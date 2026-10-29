import glob, os, re, sys, collections
root = os.path.expanduser("~/bob/.bob/ref-sources")
def cells(line): return [c.strip() for c in line.strip().strip("|").split("|")]
def words(c): return len(re.sub(r"[`*_\[\]()]", " ", c).split())
tables = []
for p in glob.glob(root + "/*/*/source.md"):
    cur=None; fence=False
    for line in open(p, encoding="utf-8").read().splitlines():
        if line.lstrip().startswith("```"): fence = not fence
        row = (not fence) and re.match(r"^\s*\|.*\|\s*$", line)
        if row:
            if cur is None: cur=[]
            if not re.match(r"^\s*\|[\s:|-]+\|\s*$", line): cur.append(cells(line))
        else:
            if cur and len(cur)>=2: tables.append(cur)
            cur=None
    if cur and len(cur)>=2: tables.append(cur)
n=len(tables)
def text(t): return sum(len(c) for r in t[1:] for c in r)
tot=sum(text(t) for t in tables)
print("tables", n)
for th in (6,8,10,12,15,20):
    rec=[t for t in tables if max((words(c) for r in t[1:] for c in r[1:]), default=0)>=th]
    print(f"threshold {th:2d}: records {len(rec)} ({len(rec)/n:.0%}), text {sum(text(t) for t in rec)/tot:.0%}")
# wide tables
wide=[t for t in tables if max(len(r) for r in t)>=4]
print("4+ cols", len(wide), f"{len(wide)/n:.0%}")
# first-column word stats: is first col a short key?
short_key=sum(1 for t in tables if max(words(r[0]) for r in t[1:])<=6)
print("first column all <=6 words:", short_key, f"{short_key/n:.0%}")
