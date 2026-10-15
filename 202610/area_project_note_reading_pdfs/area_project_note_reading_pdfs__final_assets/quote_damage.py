import re, subprocess, sys, pathlib, collections
VAULT = pathlib.Path.home() / "bob"
def words(s): return [w for w in re.split(r"[^a-z]+", s.lower()) if len(w) >= 2]
rows = []
for note in sorted((VAULT / "ref").rglob("*.md")):
    t = note.read_text(errors="replace")
    m = re.search(r"^source_pdf: (.+)$", t, re.M)
    c = re.search(r"^highlights_count: (\d+)", t, re.M)
    if not m or not c or int(c.group(1)) == 0: continue
    pdf = VAULT / m.group(1).strip()
    if not pdf.exists(): continue
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    creator = re.search(r"^Creator:\s*(.*)$", info, re.M)
    creator = creator.group(1) if creator else ""
    fonts = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True).stdout.splitlines()[2:]
    t3 = sum(1 for l in fonts if " Type 3 " in l); cid = sum(1 for l in fonts if "CID TrueType" in l or "CID Type 0" in l)
    vocab = set(words(subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"], capture_output=True, text=True).stdout))
    quotes = re.findall(r"^> \[!quote\] (.*)$", t, re.M)
    toks = [w for q in quotes for w in words(q)]
    bad = [w for w in toks if w not in vocab]
    kind = "chrome" if "Mozilla" in creator else ("xelatex/pandoc" if "pandoc" in creator else creator[:18] or "?")
    rows.append((kind, t3, cid, len(toks), len(bad), note.relative_to(VAULT / "ref"), bad[:8]))
agg = collections.defaultdict(lambda: [0, 0, 0])
for kind, t3, cid, n, b, name, ex in rows:
    fclass = "Type3" if t3 and t3 >= cid else ("CID" if cid else "other")
    key = f"{kind}/{fclass}"
    agg[key][0] += n; agg[key][1] += b; agg[key][2] += 1
    if kind == "chrome" or (b and "xelatex" in kind): print(f"{key:14} T3={t3:3} CID={cid:3} tok={n:4} bad={b:3} {name} {ex}")
print()
for k, (n, b, docs) in sorted(agg.items()):
    print(f"{k:24} docs={docs:3} tokens={n:6} not-in-pdf-text={b:4} rate={100*b/max(n,1):.2f}%")
