#!/usr/bin/env python3
"""Spike: project a Bob area/project note into clean, engine-neutral pandoc Markdown.

Prototype only (research for bob ref create note rendering). Real code would be Rust,
reusing note_tasks / task_fields / vault_links.
"""
import datetime
import os
import re
import sys
import urllib.parse

VAULT = os.path.expanduser("~/bob")

FIELD_RE = re.compile(r"[\[(]\s*([A-Za-z][\w-]*)\s*::\s*([^\])]*?)\s*[\])]")
BLOCK_ID_RE = re.compile(r"\s+\^([A-Za-z0-9-]+)\s*$")
TASK_RE = re.compile(r"^(\s*)[-*+] \[(.)\] (.*)$")
BULLET_RE = re.compile(r"^(\s*)([-*+]|\d+[.)]) (.*)$")
WIKILINK_RE = re.compile(r"(!?)\[\[([^\]|#]*)(#[^\]|]*)?(?:\|([^\]]*))?\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
STATUS = {" ": "open", "/": "wip", "*": "next", "?": "blocked", "x": "done",
          "X": "done", "-": "canceled", ">": "deferred"}
DROP_TAGS = {"#task", "#ref", "#prj", "#hide"}
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def short_date(value):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", value.strip())
    if not m:
        return value.strip()
    return f"{MONTHS[int(m.group(2)) - 1]} {int(m.group(3))}"


def humanize(stem):
    words = stem.replace("_", " ").replace("-", " ").split()
    acronyms = {"sase": "SASE", "gtd": "GTD", "ai": "AI", "tui": "TUI", "cli": "CLI"}
    return " ".join(acronyms.get(w.lower(), w.capitalize()) for w in words)


def obsidian_uri(path):
    return "obsidian://open?vault=bob&file=" + urllib.parse.quote(path, safe="/")


def read_lines(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read().split("\n")


def split_frontmatter(lines):
    fm = {}
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                for line in lines[1:i]:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        fm[k.strip()] = v.strip().strip('"')
                return fm, lines[i + 1:]
    return fm, lines


_block_cache = {}


def block_text(note_path, block_id):
    """Find the cleaned text of the line carrying ^block_id in a vault note."""
    key = (note_path, block_id)
    if key in _block_cache:
        return _block_cache[key]
    full = os.path.join(VAULT, note_path if note_path.endswith(".md") else note_path + ".md")
    text = None
    if os.path.exists(full):
        for line in read_lines(full):
            if re.search(r"\^" + re.escape(block_id) + r"\s*$", line):
                m = TASK_RE.match(line) or BULLET_RE.match(line)
                body = m.group(3) if m else line
                text = clean_inline(body, note_path, link=False)
                break
    _block_cache[key] = text
    return text


def wikilink_sub(note, link=True):
    def repl(m):
        bang, target, frag, alias = m.groups()
        target = (target or "").strip()
        frag = (frag or "").strip()
        if bang:
            return m.group(0)  # embeds handled at block level
        if not target and frag.startswith("#^"):
            bid = frag[2:]
            txt = alias or block_text(note, bid) or bid
            return f"[{txt}](#t-{bid})" if link else txt
        if alias:
            label = alias
        elif frag.startswith("#^"):
            label = block_text(target, frag[2:]) or os.path.basename(target)
            label = f"{humanize(os.path.basename(target))} › {label}"
        else:
            label = os.path.basename(target) + (f" › {frag[1:]}" if frag else "")
        label = label.replace("¶", "").strip()
        if not link:
            return label
        return f"[{label}]({obsidian_uri(target + '.md')})"
    return repl


def clean_inline(text, note, link=True):
    text = re.sub(r"%%.*?%%", "", text)
    text = BLOCK_ID_RE.sub("", text)
    text = FIELD_RE.sub("", text)
    text = WIKILINK_RE.sub(wikilink_sub(note, link), text)
    toks = [t for t in text.split(" ") if t not in DROP_TAGS]
    text = " ".join(toks)
    # ~/paths and bare filenames are code so the break filter can wrap them.
    text = re.sub(r"(?<![`\w])(~/[^\s)]+)", r"`\1`", text)
    # bare URLs -> autolinks
    text = re.sub(r"(?<![(<\[])\b(https?://[^\s)>\]]+[^\s)>\].,!?;:])", r"<\1>", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def task_chips(body):
    fields = {k.lower(): v for k, v in FIELD_RE.findall(body)}
    chips = []
    if "priority" in fields:
        chips.append(fields["priority"].strip())
    if "scheduled" in fields and fields["scheduled"].strip():
        chips.append("sched " + short_date(fields["scheduled"]))
    if "completion" in fields:
        chips.append("done " + short_date(fields["completion"]))
    if "cancelled" in fields:
        chips.append("canceled " + short_date(fields["cancelled"]))
    elif "created" in fields:
        chips.append("added " + short_date(fields["created"]))
    return chips


def indent_width(ws):
    return len(ws.replace("\t", "    "))


def project(path, include_done=False):
    stem = os.path.splitext(os.path.basename(path))[0]
    note = os.path.relpath(os.path.abspath(path), VAULT)[:-3]
    fm, body = split_frontmatter(read_lines(path))
    kind = fm.get("type", "").strip("[]") or "note"
    parent = fm.get("parent", "").strip("[]")
    title = fm.get("title") or None
    out = []
    prj_goal = None
    prj_meta = []
    counts = {}
    omitted_done = 0

    # First pass: H1 title.
    h1_index = None
    for i, line in enumerate(body):
        m = HEADING_RE.match(line)
        if m and len(m.group(1)) == 1:
            h1_index = i
            if not title:
                title = clean_inline(m.group(2), note, link=False)
            break
    if not title:
        title = humanize(stem)
    min_level = min((len(m.group(1)) for m in map(HEADING_RE.match, body) if m and len(m.group(1)) > 1),
                    default=2)

    in_fence = False
    skip_section_level = None  # skipping Done & Canceled
    skip_child_indent = None   # skipping a log's children
    i = 0
    lines = body
    while i < len(lines):
        raw = lines[i]
        i += 1
        if raw.strip().startswith("```"):
            in_fence = not in_fence
            out.append(raw)
            continue
        if in_fence:
            out.append(raw)
            continue
        if i - 1 == h1_index:
            continue
        # multi-line %% comments
        if raw.strip().startswith("%%") and raw.count("%%") == 1:
            while i < len(lines) and "%%" not in lines[i]:
                i += 1
            i += 1
            continue
        hm = HEADING_RE.match(raw)
        if hm:
            level = len(hm.group(1))
            text = clean_inline(hm.group(2), note, link=False)
            if skip_section_level is not None and level <= skip_section_level:
                skip_section_level = None
            if not include_done and re.match(r"done\s*&\s*cancel", text, re.I):
                skip_section_level = level
                continue
            if skip_section_level is not None:
                continue
            new_level = max(1, level - min_level + 1)
            if text.lower() == "contents":
                text = "Contents (draft)"
            out.extend(["", "#" * new_level + " " + text, ""])
            continue
        if skip_section_level is not None:
            if TASK_RE.match(raw) and not raw.startswith(("\t", " ")):
                omitted_done += 1
            continue
        if raw.strip().startswith("[`") and "open`]" in raw:
            continue  # status chip row rendered by a plugin
        if re.match(r"^\s*\^[A-Za-z0-9-]+\s*$", raw):
            continue  # standalone block id
        ws = re.match(r"^(\s*)", raw).group(1)
        if skip_child_indent is not None:
            if raw.strip() and indent_width(ws) > skip_child_indent:
                continue
            skip_child_indent = None

        tm = TASK_RE.match(raw)
        if tm:
            ind, sym, tbody = tm.groups()
            status = STATUS.get(sym, "open")
            counts[status] = counts.get(status, 0) + 1
            bid_m = BLOCK_ID_RE.search(tbody)
            bid = bid_m.group(1) if bid_m else None
            text = clean_inline(tbody, note)
            chips = task_chips(tbody)
            if bid == "prj" and not ind:
                prj_goal = text
                prj_meta = chips
                # children of ^prj become masthead meta
                while i < len(lines) and lines[i].startswith(("\t", "    ")):
                    child = lines[i].strip().lstrip("-").strip()
                    i += 1
                    lab = re.match(r"^\S+\s+\*\*([^*]+?):?\*\*:?\s*(.*)$", child)
                    if lab:
                        prj_meta.append(f"{lab.group(1).strip().title()}: {clean_inline(lab.group(2), note)}")
                continue
            if "#ref" in tbody.split():
                chips.insert(0, "ref")
            anchor = f"{{#t-{bid}}}" if bid else ""
            chip_md = " ".join(f"[{c}]{{.chip}}" for c in chips)
            text_md = f"~~{text}~~" if status == "canceled" else text
            span = f"[{text_md}]{anchor}" if anchor else text_md
            out.append(f"{ind}- []{{.st .st-{status}}} {span} {chip_md}".rstrip())
            continue

        bm = BULLET_RE.match(raw)
        if bm:
            ind, marker, bbody = bm.groups()
            s = bbody.strip()
            # Bob task-child labels: 🧱 **BLOCKS:** … / 🗓️ **SCHEDULE LOG** …
            lab = re.match(r"^(\S+)\s+\*\*([A-Z][A-Z -]+?):?\*\*:?\s*(.*)$", s)
            if lab and not lab.group(1)[0].isalnum():
                name = lab.group(2).strip().upper()
                rest = lab.group(3)
                children = []
                j = i
                while j < len(lines) and lines[j].strip() and indent_width(re.match(r"^(\s*)", lines[j]).group(1)) > indent_width(ind):
                    children.append(lines[j].strip().lstrip("-").strip())
                    j += 1
                if name == "SCHEDULE LOG":
                    i = j
                    if children:
                        out.append(f"{ind}- [Rescheduled {len(children)}×]{{.label}} [latest: {clean_inline(children[0], note, link=False)}]{{.muted}}")
                    continue
                if name in ("WORK LOG", "CANCEL LOG"):
                    i = j
                    label = "Worked" if name == "WORK LOG" else "Why canceled"
                    for child in children[:2]:
                        out.append(f"{ind}- [{label}]{{.label}} {clean_inline(child, note)}")
                    if len(children) > 2:
                        out.append(f"{ind}- [+{len(children) - 2} older entries]{{.muted}}")
                    continue
                nice = {"BLOCKS": "Blocks", "DEPENDS ON": "Waits on", "SUB-PROJECTS": "Sub-projects"}.get(name, name.title())
                out.append(f"{ind}- [{nice}]{{.label}} {clean_inline(rest, note).replace(' • ', ' · ')}")
                continue
            emb = re.match(r"^!\[\[([^\]|#]+?)(#[^\]|]*)?(?:\|(\d+))?\]\]$", s)
            if emb:
                target, frag, width = emb.groups()
                ext = os.path.splitext(target)[1].lower()
                if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
                    img = os.path.join(VAULT, target)
                    w = f"{{width={min(100, int(int(width) / 6))}%}}" if width else "{width=80%}"
                    out.append(f"{ind}- ![]({img}){w}")
                    continue
                if frag and frag.startswith("#^"):
                    txt = block_text(target, frag[2:])
                    if txt:
                        out.append(f"{ind}- [Embedded]{{.label}} *{txt}*")
                        continue
                out.append(f"{ind}- {clean_inline('[[' + target + (frag or '') + ']]', note)}")
                continue
            if re.match(r"^!\[\[#\^", s):
                bid = re.match(r"^!\[\[#\^([^\]|]+)", s).group(1)
                out.append(f"{ind}- [See]{{.label}} [{block_text(note, bid) or bid}](#t-{bid})")
                continue
            out.append(f"{ind}{marker} {clean_inline(bbody, note)}")
            continue

        if raw.strip():
            out.append(clean_inline(raw, note))
        else:
            out.append("")

    # Masthead as YAML metadata the templates read.
    today = datetime.date.today().isoformat()
    total_open = counts.get("open", 0) + counts.get("next", 0) + counts.get("wip", 0)
    stats = []
    for key, label in (("open", "open"), ("next", "next"), ("wip", "in progress"),
                       ("blocked", "blocked"), ("done", "done"), ("canceled", "canceled")):
        if counts.get(key):
            stats.append(f"{counts[key]} {label}")
    if omitted_done:
        stats.append(f"{omitted_done} closed not shown")
    meta = {
        "title": title,
        "kicker": f"{kind.upper()} · {parent}" if parent else kind.upper(),
        "goal": prj_goal or "",
        "goalmeta": " · ".join(prj_meta),
        "stats": " · ".join(stats),
        "snapshot": f"Snapshot of {note}.md · {today}",
    }
    head = ["---"]
    for k, v in meta.items():
        v = v.replace('"', '\\"')
        head.append(f'{k}: "{v}"')
    head.append("---")
    text = "\n".join(head + [""] + out) + "\n"
    defined = set(re.findall(r"\{#(t-[A-Za-z0-9-]+)\}", text))
    text = re.sub(r"\[([^\[\]]+)\]\(#(t-[A-Za-z0-9-]+)\)",
                  lambda m: m.group(0) if m.group(2) in defined else m.group(1), text)
    return re.sub(r"\n{3,}", "\n\n", text)


if __name__ == "__main__":
    sys.stdout.write(project(sys.argv[1], include_done="--include-done" in sys.argv))
