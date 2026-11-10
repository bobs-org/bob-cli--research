"""Fold real bob reports into the proposed chart contract (top-N roots, vocabulary types)."""
import json, sys
from collections import defaultdict
D = sys.argv[1]
TOP = 5
VOCAB = {"BUILD", "CHORE", "FIX", "MEET", "PLAN", "READ", "WRITE"}
PALETTE = ["blue", "orange", "aqua", "yellow", "magenta", "green", "violet", "red"]

def load(n): return json.load(open(f"{D}/{n}.json"))

def worked_points(stats):
    m = [x for x in stats["metrics"] if x["id"] == "worked"][0]
    return {p["date"]: p for p in m["points"]}

def fmt(m):
    m = int(round(m)); h, r = divmod(m, 60)
    return f"{h}h {r:02d}m" if h else f"{r}m"

def short(m):
    m = int(round(m)); h = m // 60
    return f"{h}h" if h >= 10 else fmt(m)

def root_series(rep):
    homes = rep["homes"]; total = sum(r["minutes"] for r in rep["lanes"]["root_parent"])
    rows = [r for r in rep["lanes"]["root_parent"] if r["minutes"] > 0]
    real = [r for r in rows if not r["key"].startswith("@")]
    buckets = [r for r in rows if r["key"].startswith("@")]
    top = real[:TOP]; rest = real[TOP:]
    # Stable hue: explicit/area hue; collisions resolved by key order, never by minutes.
    claimed, hue = set(), {}
    fixed = {"bob.md": "blue", "sase.md": "violet", "sase_blog.md": "aqua", "dev.md": "orange", "gtd.md": "gray",
             "love.md": "yellow", "cash.md": "magenta", "body.md": "green", "job_2026.md": "green", "job.md": "aqua"}
    for r in top:
        if r["key"] in fixed: hue[r["key"]] = fixed[r["key"]]
    for r in sorted(top, key=lambda r: r["key"]):
        if r["key"] in hue: continue
        h = homes.get(r["key"], {}); pref = h.get("hue"); src = h.get("hue_source")
        if src == "muted" or not pref: hue[r["key"]] = "gray"; continue
        if pref not in claimed: hue[r["key"]] = pref; claimed.add(pref); continue
        i = PALETTE.index(pref)
        for k in range(1, 9):
            c = PALETTE[(i + k) % 8]
            if c not in claimed and c != "red": hue[r["key"]] = c; claimed.add(c); break
    series = [dict(key=r["key"], label=r["label"], kind="root", hue=hue[r["key"]], minutes=r["minutes"]) for r in top]
    if rest:
        series.append(dict(key="other", label=f"{len(rest)} more", kind="other", hue="other", minutes=sum(r["minutes"] for r in rest),
                           members=[f'{r["label"]} {fmt(r["minutes"])}' for r in rest]))
    if buckets:
        series.append(dict(key="@none", label="unlinked" if len(buckets) == 1 and buckets[0]["key"] == "@unlinked" else "no root",
                           kind="unattributed", hue="hatch", minutes=sum(b["minutes"] for b in buckets),
                           members=[f'{b["label"]} {fmt(b["minutes"])}' for b in buckets]))
    for s in series: s["display"] = fmt(s["minutes"]); s["short"] = short(s["minutes"]); s["share"] = f'{round(100*s["minutes"]/total)}%' if total else "0%"
    return series, {r["key"] for r in top}

def fold_root_stack(stack, topkeys):
    out = defaultdict(int)
    for e in stack:
        k = e["key"]
        out[k if k in topkeys else ("@none" if k.startswith("@") else "other")] += e["minutes"]
    return dict(out)

def type_key(k, hues):
    if k.strip() == "" or k.lower() == "(unnamed)": return "untyped"
    e = hues.get(k.strip().lower().replace(" ", "_")) or hues.get(k.strip().lower())
    return k if k.upper() in VOCAB else "other"

def type_series(rep, points_by_col):
    hues = rep["theme_hues"]; tot = defaultdict(int)
    for stack in points_by_col.values():
        for k, v in stack.items(): tot[k] += v
    total = sum(tot.values())
    if rep["period"]["kind"] != "week":
        for k in [k for k in tot if k not in ("other", "untyped") and tot[k] * 100 < total * 2]:
            tot["other"] = tot.get("other", 0) + tot.pop(k)
            for st in points_by_col.values():
                if k in st: st["other"] = st.get("other", 0) + st.pop(k)
    named = sorted([k for k in tot if k not in ("other", "untyped")], key=lambda k: -tot[k])
    series = []
    for k in named:
        e = hues.get(k.lower(), {})
        h = e.get("hue") if e.get("hue_source") in ("config", "pin") and e.get("hue") else "gray"
        series.append(dict(key=k, label=e.get("name", k), kind="type", hue=h, minutes=tot[k]))
    if tot.get("other"):
        series.append(dict(key="other", label="other types", kind="other", hue="other", minutes=tot["other"]))
    if tot.get("untyped"):
        series.append(dict(key="untyped", label="untyped", kind="unattributed", hue="hatch", minutes=tot["untyped"]))
    for s in series: s["display"] = fmt(s["minutes"]); s["short"] = short(s["minutes"]); s["share"] = f'{round(100*s["minutes"]/total)}%' if total else "0%"
    return series

def build(pid, stats_name):
    rep = load(pid)
    pts = worked_points(load(stats_name)) if stats_name else {}
    hues = rep["theme_hues"]
    rseries, topkeys = root_series(rep)
    cols, type_by_col = [], {}
    for c in rep["columns"]:
        start = c.get("start") or c.get("id")
        p = pts.get(start)
        tstack = defaultdict(int)
        if p and p.get("parts", {}).get("theme"):
            for k, v in p["parts"]["theme"].items(): tstack[type_key(k, hues)] += v
        type_by_col[c["id"]] = dict(tstack)
        w = c.get("worked") or {}
        cols.append(dict(id=c["id"], caption=c.get("caption", ""), label=c.get("label", ""), state=c.get("state"), mark=c.get("mark"),
                         tick=c.get("tick"), group=c.get("group"), worked=w.get("value"), display=w.get("display"),
                         short=short(w["value"]) if isinstance(w.get("value"), int) and w.get("value") else (w.get("display") or ""),
                         quality=w.get("quality"), roots=fold_root_stack(c.get("stack", []), topkeys), types=dict(tstack)))
    tseries = type_series(rep, type_by_col)
    for c in cols: c["types"] = type_by_col[c["id"]]
    return dict(id=pid, kind=rep["period"]["kind"], title=rep["period"].get("title"), state=rep["period"]["state"],
                facts=rep["facts"], groups=rep.get("groups", []), columns=cols, roots=rseries, types=tseries,
                meta=(rep["period"].get("coverage") or {}).get("display", ""))

out = {k: build(k, s) for k, s in [("2026-W45", "st-W45"), ("2026-Q4", "st-Q4"), ("2026-Q3", "st-Q3"), ("2026", "st-2026")]}
json.dump(out, open(f"{D}/mock.json", "w"))
for k, v in out.items():
    print(k, "roots:", [(s["label"], s["hue"], s["share"]) for s in v["roots"]])
    print("   types:", [(s["label"], s["hue"], s["share"]) for s in v["types"]])
    print("   col0:", v["columns"][0]["roots"], v["columns"][0]["types"])
