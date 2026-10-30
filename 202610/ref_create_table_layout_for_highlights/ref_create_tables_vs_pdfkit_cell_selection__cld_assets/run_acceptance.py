#!/usr/bin/env python3
"""Render and compare table-heavy chat sources without writing to the vault."""
from __future__ import annotations

import argparse
import collections
import html.parser
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

SOURCE_STEMS = [
    "sase_goals_epic_roadmap--02b074ea97f6",
    "sase_core_maintainability_audit--1a427a25239b",
    "memory_built_instruction_migration_epics--3757396f06fc",
    "bob_daily_stats--f813bef5bc1f",
    "agents_tab_inbox_and_history_views--9ccdccc71f16",
    "now_tag_vs_in_progress_status--65b53a678f17",
]


def run(argv: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, check=True)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def canonical_text(text: str) -> str:
    """Normalize line wrapping and typographic punctuation from PDF output."""
    # bob adds raised return-link markers and "↩ p. N" pills to linked source
    # text. They are navigation chrome, not authored cell wording. 🍅 is the one
    # known missing-glyph case called out as out of scope in the study.
    text = re.sub(r"↩\s*p\.\s*\d+\s*[⁰¹²³⁴⁵⁶⁷⁸⁹ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻ]*", " ", text)
    text = text.translate(str.maketrans("", "", "⁰¹²³⁴⁵⁶⁷⁸⁹ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻ"))
    text = re.sub(r"</?br\s*/?>", "", text, flags=re.IGNORECASE)
    text = text.translate(str.maketrans("", "", "🍅✗✓✅❌🟢🟡⚪⚫⌖\ufffd"))
    text = unicodedata.normalize("NFKC", text)
    # XeTeX/MuPDF can insert a line-wrap space immediately beside an underscore
    # inside inline code identifiers. It is not a source word boundary.
    text = re.sub(r"(?<=\w)_\s+|\s+_(?=\w)", "_", text)
    text = re.sub(r"(?<=\w)-\s+(?=\w)", "-", text)
    text = re.sub(r"(?<!\w)-\s+(?=[A-Za-z])", "-", text)
    return norm(text).translate(str.maketrans({
        "“": '"', "”": '"', "‘": "'", "’": "'",
        "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
        "…": "...", "\u00a0": " ",
    }))


def fidelity_pattern(needle: str) -> re.Pattern[str]:
    """Match a cell while allowing PDF line-wrap spaces inside code-like tokens."""
    tokens = needle.split()
    pieces: list[str] = []
    for token in tokens:
        code_like = (any(char in token for char in "_/.:%") or
                     re.search(r"[a-z][A-Z]", token) is not None)
        if code_like:
            pieces.append(r"\s*".join(re.escape(char) for char in token))
        else:
            pieces.append(re.escape(token))
    left = r"(?<![A-Za-z0-9])" if needle and needle[0].isalnum() else ""
    right = r"(?![A-Za-z0-9])" if needle and needle[-1].isalnum() else ""
    return re.compile(left + r"\s+".join(pieces) + right)


def non_table_text(value: object) -> str:
    """Collect document text while omitting table cells, which are checked separately."""
    if isinstance(value, list):
        return " ".join(part for item in value if (part := non_table_text(item)))
    if not isinstance(value, dict):
        return ""
    kind, content = value.get("t"), value.get("c")
    if kind == "Table":
        return ""
    if kind in {"Plain", "Para"}:
        return inline_text(content)
    if kind == "Header":
        return inline_text(content[2])
    if kind == "CodeBlock":
        return str(content[1] or "")
    if kind == "RawBlock":
        return str(content[1] or "")
    if kind in {"BulletList", "OrderedList"}:
        items = content if kind == "BulletList" else content[1]
        return " ".join(non_table_text(item) for item in items)
    if kind in {"Str", "Space", "SoftBreak", "LineBreak", "Code", "Math",
                "RawInline", "Link", "Image", "Cite", "Note", "Emph",
                "Strong", "Underline", "Strikeout", "Superscript", "Subscript",
                "SmallCaps", "Quoted"}:
        return inline_text(value)
    return non_table_text(content)


def inline_text(node: object) -> str:
    if isinstance(node, list):
        return "".join(inline_text(item) for item in node)
    if not isinstance(node, dict):
        return ""
    kind, content = node.get("t"), node.get("c")
    if kind == "Str":
        return str(content or "")
    if kind in {"Space", "SoftBreak", "LineBreak"}:
        return " "
    if kind == "Code":
        return str(content[1] or "")
    if kind == "Math":
        return str(content[1] or "")
    if kind == "RawInline":
        return str(content[1] or "")
    if kind in {"Link", "Image"}:
        return inline_text(content[1])
    if kind == "Cite":
        return inline_text(content[1])
    if kind == "Note":
        return blocks_text(content)
    if kind in {"Emph", "Strong", "Underline", "Strikeout", "Superscript",
                "Subscript", "SmallCaps", "Quoted"}:
        if kind == "Quoted":
            quote_type = content[0]
            if isinstance(quote_type, dict):
                quote_type = quote_type.get("t")
            opening, closing = (("“", "”") if quote_type == "DoubleQuote"
                                else ("‘", "’"))
            return opening + inline_text(content[1]) + closing
        return inline_text(content)
    return ""


def blocks_text(blocks: object) -> str:
    if not isinstance(blocks, list):
        return ""
    pieces: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        kind, content = block.get("t"), block.get("c")
        if kind in {"Plain", "Para", "Header"}:
            pieces.append(inline_text(content if kind != "Header" else content[2]))
        elif kind == "CodeBlock":
            pieces.append(str(content[1] or ""))
        elif kind in {"BulletList", "OrderedList"}:
            items = content if kind == "BulletList" else content[1]
            pieces.extend(blocks_text(item) for item in items)
        elif kind == "BlockQuote":
            pieces.append(blocks_text(content))
        elif kind == "Table":
            pieces.append(" ".join(table_cells(content)))
        else:
            pieces.append(blocks_text(content))
    return " ".join(piece for piece in pieces if piece)


def table_cells(content: list[object]) -> list[str]:
    out: list[str] = []
    for body in content[4]:
        rows = body[3]
        for row in rows:
            for cell in row[1]:
                text = norm(blocks_text(cell[4]))
                if text:
                    out.append(text)
    return out


def markdown_data(path: Path) -> tuple[int, list[str], str, str | None]:
    ast = json.loads(run(["pandoc", str(path), "-t", "json"]).stdout)
    cells: list[str] = []
    table_count = 0

    def walk(value: object) -> None:
        nonlocal table_count
        if isinstance(value, dict):
            if value.get("t") == "Table":
                table_count += 1
                cells.extend(table_cells(value["c"]))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(ast)
    source_text = non_table_text(ast.get("blocks", []))
    first_heading = next((inline_text(block["c"][2]) for block in ast.get("blocks", [])
                          if isinstance(block, dict) and block.get("t") == "Header"), None)
    return table_count, cells, norm(source_text), first_heading


class TableHTMLParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.table_depth = 0
        self.thead_depth = 0
        self.cell: list[str] | None = None
        self.cells: list[str] = []
        self.tables = 0
        self.table_cells: list[list[str]] = []
        self.current_table_cells: list[str] | None = None
        self.all_text: list[str] = []
        self.outside_table_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.table_depth += 1
            self.tables += 1
            if self.table_depth == 1:
                self.current_table_cells = []
        elif tag == "thead":
            self.thead_depth += 1
        elif tag == "td" and self.table_depth and not self.thead_depth:
            self.cell = []
        elif tag in {"br", "p", "li"} and self.cell is not None:
            self.cell.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.cell is not None:
            text = norm("".join(self.cell))
            if text:
                self.cells.append(text)
                if self.current_table_cells is not None:
                    self.current_table_cells.append(text)
            self.cell = None
        elif tag == "thead" and self.thead_depth:
            self.thead_depth -= 1
        elif tag == "table" and self.table_depth:
            if self.table_depth == 1 and self.current_table_cells is not None:
                self.table_cells.append(self.current_table_cells)
                self.current_table_cells = None
            self.table_depth -= 1

    def handle_data(self, data: str) -> None:
        self.all_text.append(data)
        if self.table_depth == 0:
            self.outside_table_text.append(data)
        if self.cell is not None:
            self.cell.append(data)


def html_data(path: Path) -> tuple[int, list[str], str, None]:
    parser = TableHTMLParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.tables, parser.cells, norm(" ".join(parser.outside_table_text)), None



def first_markdown_table_cells(path: Path) -> list[str]:
    ast = json.loads(run(["pandoc", str(path), "-t", "json"]).stdout)
    found: list[str] = []

    def walk(value: object) -> None:
        if found:
            return
        if isinstance(value, dict):
            if value.get("t") == "Table":
                found.extend(table_cells(value["c"]))
                return
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(ast)
    return found


def probe_targets(cells: list[str]) -> list[dict[str, str]]:
    candidate = max(cells, key=len)
    words = candidate.split()
    phrase = " ".join(words[:min(8, len(words))])
    return [{"kind": "cell", "text": candidate}, {"kind": "phrase", "text": phrase}]


def page_count(path: Path) -> int:
    if shutil.which("pdfinfo"):
        result = run(["pdfinfo", str(path)]).stdout
        match = re.search(r"^Pages:\s+(\d+)", result, re.MULTILINE)
    else:
        result = run(["mutool", "info", "-M", str(path)]).stdout
        match = re.search(r"^Pages:\s+(\d+)", result, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not read page count from {path}")
    return int(match.group(1))


def parse_summary(log: str, tables: int) -> tuple[int, int, str | None]:
    match = re.search(r"tables:\s+(\d+)\s+records?\s+·\s+(\d+)\s+grids?", log)
    if match:
        return int(match.group(1)), int(match.group(2)), match.group(0)
    # The pre-filter baseline rendered all source tables as grids and had no summary.
    return 0, tables, None


def fidelity(source_text: str, cells: list[str], pdf_text: str,
             body_anchor: str | None = None) -> dict[str, object]:
    output = canonical_text(pdf_text)
    source = canonical_text(source_text)
    if body_anchor:
        anchor = canonical_text(body_anchor)
        anchor_matches = list(re.finditer(re.escape(anchor), output))
        if len(anchor_matches) >= 2:
            # Pandoc's generated TOC repeats headings before the printed body.
            # Start at the second occurrence of the first source heading.
            output = output[anchor_matches[1].start():]
        elif anchor_matches:
            output = output[anchor_matches[0].start():]
    counts = collections.Counter(cells)
    issues: list[str] = []
    for cell, cell_count in counts.items():
        needle = canonical_text(cell)
        if not needle:
            continue
        pattern = fidelity_pattern(needle)
        expected = len(pattern.findall(source)) + cell_count
        actual = len(pattern.findall(output))
        # Short values (for example "No", "12", and "—") also occur in prose,
        # labels, and page furniture, so their total PDF occurrence count cannot
        # distinguish a duplicated cell from unrelated text. Their ordered
        # presence is still checked below.
        if len(needle.split()) >= 4 and len(needle) >= 24 and actual != expected:
            issues.append(f"occurrences {actual}/{expected}: {cell[:72]}")
    cursor = 0
    ordered = 0
    for cell in cells:
        needle = canonical_text(cell)
        if not needle:
            continue
        match = fidelity_pattern(needle).search(output, cursor)
        if match is None:
            issues.append(f"out of order or missing: {cell[:72]}")
            continue
        ordered += 1
        cursor = match.end()
    return {
        "body_cells": len(cells),
        "text_cells_checked": sum(bool(canonical_text(cell)) for cell in cells),
        "ordered_text_cells": ordered,
        "ignored_symbol_cells": sum(not canonical_text(cell) for cell in cells),
        "occurrence_issues": issues,
        "pass": not issues and ordered == sum(bool(canonical_text(cell)) for cell in cells),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument("--source-root", type=Path,
                        default=Path.home() / "bob/.bob/ref-sources/chat")
    parser.add_argument("--markdown-fixture", required=True, type=Path)
    parser.add_argument("--html-fixture", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.baseline = args.baseline.resolve()
    args.current = args.current.resolve()
    args.source_root = args.source_root.resolve()
    args.markdown_fixture = args.markdown_fixture.resolve()
    args.html_fixture = args.html_fixture.resolve()
    args.out = args.out.resolve()

    args.out.mkdir(parents=True, exist_ok=True)
    inputs = args.out / "inputs"
    inputs.mkdir(exist_ok=True)
    renders = args.out / "renders"
    vault = Path.home() / "bob"
    before = run(["git", "-C", str(vault), "status", "--porcelain"]).stdout

    sources: list[tuple[str, Path, str]] = []
    for stem in SOURCE_STEMS:
        original = args.source_root / stem / "source.md"
        if not original.is_file():
            raise FileNotFoundError(f"Required preserved chat source is missing: {stem}")
        copy = inputs / f"{stem}.md"
        shutil.copy2(original, copy)
        sources.append((stem, copy, "markdown"))
    md_copy = inputs / "table-layout-fixture.md"
    shutil.copy2(args.markdown_fixture, md_copy)
    sources.append(("table-layout-fixture", md_copy, "markdown"))
    html_copy = inputs / "tables.html"
    shutil.copy2(args.html_fixture, html_copy)
    sources.append(("web-tables-fixture", html_copy, "html"))

    md_targets = probe_targets(first_markdown_table_cells(md_copy))
    html_parser = TableHTMLParser()
    html_parser.feed(html_copy.read_text(encoding="utf-8"))
    if not html_parser.table_cells or not html_parser.table_cells[0]:
        raise RuntimeError("The web fixture has no body cells in its first table")
    web_targets = probe_targets(html_parser.table_cells[0])
    (args.out / "probe_targets_markdown.json").write_text(
        json.dumps(md_targets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.out / "probe_targets_web.json").write_text(
        json.dumps(web_targets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    docs: list[dict[str, object]] = []
    for label, source, kind in sources:
        if kind == "markdown":
            table_total, cells, source_text, body_anchor = markdown_data(source)
        else:
            table_total, cells, source_text, body_anchor = html_data(source)
        doc: dict[str, object] = {
            "name": label,
            "source_kind": kind,
            "tables_in_source": table_total,
            "body_cells_in_source": len(cells),
            "variants": {},
        }
        for variant, binary in (("baseline", args.baseline), ("current", args.current)):
            variant_dir = renders / variant
            variant_dir.mkdir(parents=True, exist_ok=True)
            pdf = variant_dir / f"{label}.pdf"
            log_path = variant_dir / f"{label}.log"
            # bob refuses to overwrite an existing explicit output path. Keep the
            # acceptance runner repeatable by clearing only its generated outputs.
            pdf.unlink(missing_ok=True)
            log_path.unlink(missing_ok=True)
            if kind == "markdown":
                cmd = [str(binary), "ref", "create", str(source), "--output", str(pdf),
                       "--no-audio", "--parent", "sase"]
            else:
                cmd = [str(binary), "ref", "create", "https://example.invalid/table-layout-acceptance",
                       "--html", str(source), "--output", str(pdf), "--no-audio", "--parent", "sase"]
            result = run(cmd, cwd=args.out)
            log_path.write_text(result.stdout, encoding="utf-8")
            pdf_text = run(["mutool", "draw", "-F", "txt", str(pdf)]).stdout
            records, grids, summary_line = parse_summary(result.stdout, table_total)
            doc["variants"][variant] = {
                "pages": page_count(pdf),
                "records": records,
                "grids": grids,
                "tables_summary": summary_line,
                "kept_grid_warnings": [line for line in result.stdout.splitlines()
                                       if "kept" in line.lower() and "grid" in line.lower()],
                "fidelity": fidelity(source_text, cells, pdf_text, body_anchor),
                "pdf": str(pdf),
                "log": str(log_path),
            }
        base = doc["variants"]["baseline"]
        current = doc["variants"]["current"]
        doc["page_count_not_increased"] = current["pages"] <= base["pages"]
        doc["current_fidelity_pass"] = current["fidelity"]["pass"]
        docs.append(doc)

    after = run(["git", "-C", str(vault), "status", "--porcelain"]).stdout
    report = {
        "baseline_binary": str(args.baseline.resolve()),
        "current_binary": str(args.current.resolve()),
        "baseline_current_vault_status_identical": before == after,
        "vault_status_before": before.splitlines(),
        "vault_status_after": after.splitlines(),
        "documents": docs,
        "page_counts_pass": all(doc["page_count_not_increased"] for doc in docs),
        "fidelity_pass": all(doc["current_fidelity_pass"] for doc in docs),
    }
    result_file = args.out / "results.json"
    result_file.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "results": str(result_file),
        "probe_targets_markdown": str(args.out / "probe_targets_markdown.json"),
        "probe_targets_web": str(args.out / "probe_targets_web.json"),
        "vault_status_identical": report["baseline_current_vault_status_identical"],
        "page_counts_pass": report["page_counts_pass"],
        "fidelity_pass": report["fidelity_pass"],
        "documents": [{
            "name": d["name"],
            "tables": d["tables_in_source"],
            "baseline_pages": d["variants"]["baseline"]["pages"],
            "current_pages": d["variants"]["current"]["pages"],
            "current_records": d["variants"]["current"]["records"],
            "current_grids": d["variants"]["current"]["grids"],
            "fidelity": d["current_fidelity_pass"],
        } for d in docs],
    }, indent=2, ensure_ascii=False))
    return 0 if report["baseline_current_vault_status_identical"] and report["page_counts_pass"] and report["fidelity_pass"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout, file=sys.stderr, end="" if exc.stdout.endswith("\n") else "\n")
        print(f"acceptance failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(2)
    except Exception as exc:
        print(f"acceptance failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(2)
