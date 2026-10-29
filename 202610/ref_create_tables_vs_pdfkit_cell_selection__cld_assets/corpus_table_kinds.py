import glob, os, re, statistics, collections
src_root = os.path.expanduser("~/bob/.bob/ref-sources")
def cells_of(line): return [c.strip() for c in line.strip().strip("|").split("|")]
def words(c): return len(re.sub(r"[`*_\[\]()]", " ", c).split())
tables = []
for p in glob.glob(src_root + "/*/*/source.md"):
    cur = None; infence = False
    lines = open(p, encoding="utf-8").read().splitlines()
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"): infence = not infence
        is_row = (not infence) and re.match(r"^\s*\|.*\|\s*$", line)
        if is_row:
            if cur is None: cur = {"src": p, "rows": []}
            if not re.match(r"^\s*\|[\s:|-]+\|\s*$", line): cur["rows"].append(cells_of(line))
        else:
            if cur and len(cur["rows"]) >= 2: tables.append(cur)
            cur = None
    if cur and len(cur["rows"]) >= 2: tables.append(cur)
kinds = collections.Counter(); chars = collections.Counter(); ncols = collections.Counter()
for t in tables:
    body = t["rows"][1:]
    nc = max(len(r) for r in t["rows"]); ncols[min(nc, 6)] += 1
    rest = [c for r in body for c in r[1:]] or [c for r in body for c in r]
    mx = max((words(c) for c in rest), default=0)
    avg = statistics.mean([words(c) for c in rest]) if rest else 0
    k = "prose (some cell >= 12 words)" if mx >= 12 else ("mixed (max 6-11 words)" if mx >= 6 else "data (all cells <= 5 words)")
    kinds[k] += 1
    chars[k] += sum(len(c) for r in body for c in r)
n = len(tables); tc = sum(chars.values())
print(f"tables: {n}")
for k, v in kinds.most_common(): print(f"  {k}: {v} ({v/n:.0%}) — {chars[k]/tc:.0%} of table text")
print("columns:", dict(sorted(ncols.items())))
