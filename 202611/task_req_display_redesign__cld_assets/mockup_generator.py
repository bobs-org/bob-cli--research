import urllib.parse, os, sys
OUT = sys.argv[1]
def uri(svg):
    return 'url("data:image/svg+xml,' + urllib.parse.quote(svg, safe="=:/ ',") + '")'
S = "xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'"
D = "M8 1.7 14.3 8 8 14.3 1.7 8Z"
G = {
 'hollow': f"<svg {S} fill='none' stroke='black' stroke-width='1.75' stroke-linejoin='round'><path d='{D}'/></svg>",
 'met': f"<svg {S}><path d='{D}' fill='black' stroke='black' stroke-width='1.75' stroke-linejoin='round'/></svg>",
 'dropped': f"<svg {S} fill='none' stroke='black' stroke-width='1.75' stroke-linejoin='round' stroke-linecap='round'><path d='{D}'/><path d='M4.4 11.6 11.6 4.4'/></svg>",
 'carried': f"<svg {S} fill='none' stroke='black' stroke-width='1.75' stroke-linejoin='round' stroke-linecap='round'><path d='M2.4 8h10.4M9.2 4.3 12.9 8 9.2 11.7'/></svg>",
 'ring': f"<svg {S} fill='none' stroke='black' stroke-width='1.9'><circle cx='8' cy='8' r='6.05'/></svg>",
 'ringdone': f"<svg {S}><defs><mask id='m'><rect width='16' height='16' fill='white'/><path d='M5 8.3 7.1 10.4 11 6.1' fill='none' stroke='black' stroke-width='1.9' stroke-linecap='round' stroke-linejoin='round'/></mask></defs><circle cx='8' cy='8' r='7' fill='black' mask='url(#m)'/></svg>",
 'ringcancel': f"<svg {S} fill='none' stroke='black' stroke-width='1.9' stroke-linecap='round'><circle cx='8' cy='8' r='6.05'/><path d='M5.3 10.7 10.7 5.3'/></svg>",
 'ringnext': f"<svg {S}><circle cx='8' cy='8' r='6.05' fill='none' stroke='black' stroke-width='1.9'/><circle cx='8' cy='8' r='2.35' fill='black'/></svg>",
 'hash': f"<svg {S} fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round'><path d='M6.5 3 5.5 13M10.5 3 9.5 13M3.5 6.25h9M3.5 9.75h9'/></svg>",
 'run': "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 16' fill='none' stroke='black' stroke-width='1.45' stroke-linecap='round'><path d='M2.5 2 1.5 14M5.5 2 4.5 14M.5 6h7M.5 10h7M10.5 2 9.5 14M13.5 2 12.5 14M8.5 6h7M8.5 10h7M18.5 2 17.5 14M21.5 2 20.5 14M16.5 6h7M16.5 10h7M26.5 2 25.5 14M29.5 2 28.5 14M24.5 6h7M24.5 10h7'/></svg>",
 'circ': f"<svg {S} fill='none' stroke='black' stroke-width='1.6'><circle cx='8' cy='8' r='4.9'/></svg>",
 'ghost': f"<svg {S} fill='none' stroke='black' stroke-width='1.4' stroke-dasharray='2.1 1.7'><rect x='2.6' y='2.6' width='10.8' height='10.8' rx='2.4'/></svg>",
 'cbx': f"<svg {S}><defs><mask id='m'><rect width='16' height='16' fill='white'/><path d='M4.6 8.3 7 10.6 11.6 5.6' fill='none' stroke='black' stroke-width='1.9' stroke-linecap='round' stroke-linejoin='round'/></mask></defs><rect x='1' y='1' width='14' height='14' rx='3.2' fill='black' mask='url(#m)'/></svg>",
}
css_vars = "\n".join(f"  --g-{k}: {uri(v)};" for k, v in G.items())
CSS = """
:root {
%s
}
* { box-sizing: border-box; }
body { margin: 0; font-family: 'DejaVu Sans', sans-serif; font-size: 15px; background: #fff; }
.theme-light { --bg:#ffffff; --panel:#f7f7f8; --text:#1f1f1f; --muted:#6e6e6e; --faint:#a9a9a9; --guide:#e4e4e4; --link:#6f4fd8; --teal:#0a9391; --yellow:#c69026; --green:#3f8f5f; --red:#c65367; --grey:#8a8a8a; --orange:#c9731c; --border:#e3e3e6; --chip:#f0f0f2; --type-fix:#b5527d; }
.theme-dark { --bg:#1e1e1e; --panel:#262628; --text:#dcddde; --muted:#9a9a9a; --faint:#666; --guide:#343434; --link:#a88bfa; --teal:#79dedc; --yellow:#d9a441; --green:#62b882; --red:#e07a8c; --grey:#8a8a8a; --orange:#e3954a; --border:#3a3a3d; --chip:#2e2e31; --type-fix:#e48fb5; }
.pane { background: var(--bg); color: var(--text); padding: 18px 22px 20px; border-radius: 10px; border: 1px solid var(--border); }
.cap { font-size: 12.5px; color: var(--muted); letter-spacing: .02em; margin: 0 0 10px; font-weight: bold; text-transform: uppercase; }
.sub { font-size: 12px; color: var(--muted); margin: -6px 0 10px; }
.ln { position: relative; display: flex; align-items: center; min-height: 1.75em; line-height: 1.5; padding-left: calc(var(--d,0) * 1.55em); border-radius: 4px; white-space: nowrap; }
.ln::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: calc(var(--d,0) * 1.55em); background-image: repeating-linear-gradient(to right, transparent 0 .62em, var(--guide) .62em calc(.62em + 1px), transparent calc(.62em + 1px) 1.55em); }
.ln.inprog { background: linear-gradient(to right, var(--yellow) 0 2px, color-mix(in srgb, var(--yellow) 13%%, transparent) 2px 100%%); }
.ln.next { background: linear-gradient(to right, var(--green) 0 2px, color-mix(in srgb, var(--green) 13%%, transparent) 2px 100%%); }
.slot { display: inline-flex; justify-content: center; align-items: center; width: 1.3em; flex: 0 0 1.3em; margin-right: .3em; height: 1.5em; }
.dot { display: inline-block; width: .33em; height: .33em; border-radius: 50%%; background: var(--text); opacity: .75; }
.cb { width: .95em; height: .95em; border-radius: .2em; border: 1.5px solid var(--faint); display: inline-flex; align-items: center; justify-content: center; font-size: .7em; font-weight: bold; color: #fff; }
.cb.inprog { background: var(--yellow); border-color: var(--yellow); }
.cb.next { background: var(--green); border-color: var(--green); }
.cb.done { background: var(--muted); border-color: var(--muted); }
.cb.cancel { background: var(--grey); border-color: var(--grey); }
.m { display: inline-block; background-color: var(--ink, var(--teal)); -webkit-mask-repeat: no-repeat; -webkit-mask-position: center; -webkit-mask-size: contain; }
.hash { width: 1.0em; height: 1.0em; -webkit-mask-image: var(--g-hash); margin-right: .32em; opacity: .9; }
.g { width: .92em; height: .92em; }
.g.hollow { -webkit-mask-image: var(--g-hollow); }
.g.met { -webkit-mask-image: var(--g-met); opacity: .62; }
.g.dropped { -webkit-mask-image: var(--g-dropped); opacity: .55; }
.g.carried { -webkit-mask-image: var(--g-carried); }
.g.faded { -webkit-mask-image: var(--g-hollow); opacity: .42; }
.g.flag { -webkit-mask-image: var(--g-hollow); --ink: var(--orange); }
.g.circ { -webkit-mask-image: var(--g-circ); }
.g.ghost { -webkit-mask-image: var(--g-ghost); }
.g.onehash { -webkit-mask-image: var(--g-hash); width: .8em; height: .8em; }
.ring { width: .86em; height: .86em; -webkit-mask-image: var(--g-ring); margin-right: .24em; }
.ring.next { -webkit-mask-image: var(--g-ringnext); --ink: var(--green); }
.ring.done { -webkit-mask-image: var(--g-ringdone); --ink: var(--muted); opacity: .8; }
.ring.cancel { -webkit-mask-image: var(--g-ringcancel); --ink: var(--grey); opacity: .8; }
.run { height: 1em; -webkit-mask-image: var(--g-run); -webkit-mask-size: 2em 1em; -webkit-mask-position: left center; margin-right: .24em; }
.run.n2 { width: 1em; } .run.n3 { width: 1.5em; } .run.n4 { width: 2em; }
.runwrap { display:inline-flex; align-items:center; margin-left: .18em; margin-right: .06em; }
.txt.muted { color: var(--muted); }
.txt.strike { text-decoration: line-through; text-decoration-color: color-mix(in srgb, var(--muted) 70%%, transparent); }
.txt.done { color: var(--muted); text-decoration: line-through; }
.link { color: var(--link); text-decoration: underline; text-decoration-color: color-mix(in srgb, var(--link) 45%%, transparent); text-underline-offset: 2px; }
.lbl { font-weight: bold; font-size: .82em; letter-spacing: .02em; color: var(--muted); margin-right: .45em; }
.loglbl { font-weight: bold; font-size: .82em; letter-spacing: .02em; color: var(--muted); }
.chips { margin-left: .9em; font-size: .8em; color: var(--faint); }
.anno { margin-left: auto; padding-left: 1.2em; font-size: 11.5px; color: var(--muted); font-style: italic; }
.row { display: flex; gap: 18px; align-items: stretch; }
.col { flex: 1; }
.wrap { padding: 16px; background: #fafafa; }
.title { font-size: 15px; font-weight: bold; margin: 0 0 12px; color: #222; }
.tag { display:inline-block; font-size: 10.5px; padding: 1px 6px; border-radius: 999px; background: var(--chip); color: var(--muted); margin-left: 6px; vertical-align: middle; }
.typefix { color: var(--type-fix); font-weight: bold; font-size: .9em; margin-right: .32em; }
""" % css_vars

def page(body, theme_wrap=True, width=1180):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body><div class='wrap' style='width:{width}px'>{body}</div></body></html>"

def L(d, slot, text, cls="", tail="", txtcls="", extra=""):
    return f"<div class='ln {cls}' style='--d:{d}'>{slot}<span class='txt {txtcls}'>{text}</span>{tail}{extra}</div>"

def slot(inner): return f"<span class='slot'>{inner}</span>"
DOT = slot("<span class='dot'></span>")
def CB(kind="", sym=""): return slot(f"<span class='cb {kind}'>{sym}</span>")
HASH = "<span class='m hash'></span>"
def G1(cls, ink=None):
    st = f" style='--ink:{ink}'" if ink else ""
    return slot(f"<span class='m g {cls}'{st}></span>")
def RUN(n): return f"<span class='runwrap'><span class='m run n{n}'></span></span>"

def block(req, owner_cls="inprog", owner_cb=("inprog","/"), owner_txt="Ship the exporter", depth_run=False, state_mode="open"):
    """req(depth, state) -> slot html"""
    out = []
    out.append(L(0, CB(*owner_cb), HASH + owner_txt, cls=owner_cls, tail="<span class='chips'>▮▮▮ &nbsp;+ Dec 4</span>"))
    out.append(L(1, DOT, "<span class='lbl'>DEPENDS ON:</span><span class='m ring'></span><span class='link'>parser › Parse every dialect</span>"))
    rows = [
      (1, "pending", "Handles supported inputs"),
      (2, "pending", "Handles Windows files"),
      (3, "pending", "Preserves CRLF"),
      (3, "note", "Fixture: windows.csv"),
      (2, "pending", "Handles empty input"),
      (1, "dropped", "Benchmarks within 5% of v1"),
      (2, "log", "CANCEL LOG"),
      (3, "note", "<i>2026-11-21</i> — v1 is gone"),
      (1, "carried", "Docs cover every flag"),
      (1, "drawer", "NOTES"),
      (2, "note", "Morgan reported the original issue."),
      (1, "log", "WORK LOG"),
    ]
    for d, st, t in rows:
        if st == "note": out.append(L(d, DOT, t)); continue
        if st == "drawer": out.append(L(d, DOT, t)); continue
        if st == "log": out.append(L(d, DOT, f"<span class='loglbl'>{t}</span>")); continue
        out.append(req(d, st, t))
    return "".join(out)

def req_current(d, st, t):
    n = 2 if d == 1 else 3 if d == 2 else 4
    if st == "pending": return L(d, "", t, extra="").replace("<span class='txt '>", RUN(n) + "<span class='txt '>", 1)
    if st == "dropped": return L(d, "", t, txtcls="muted strike").replace("<span class='txt muted strike'>", RUN(n).replace("class='m run", "style='opacity:.58' class='m run") + "<span class='txt muted strike'>", 1)
    if st == "carried": return L(d, "", "<span class='m ring next'></span><span class='link'>Docs cover every flag</span> <span style='color:var(--faint);font-size:.8em'>→</span>").replace("<span class='txt '>", RUN(n) + "<span class='txt '>", 1)

def req_new(d, st, t):
    if st == "pending": return L(d, G1("hollow"), t)
    if st == "dropped": return L(d, G1("dropped"), t, txtcls="muted strike")
    if st == "carried": return L(d, G1("carried"), "<span class='m ring next'></span><span class='link'>Docs cover every flag</span>")

# FIG 1: current vs proposed
f1 = f"""<div class='title'>Same task block, same bytes: shipped today (left) vs proposed (right) · Obsidian Live Preview mockup, light theme</div>
<div class='row'>
 <div class='col pane theme-light'><div class='cap'>Today · depth-coded hash runs (##, ###, ####)</div><div class='sub'>run width 1em → 1.5em → 2em; text column shifts per level</div>{block(req_current)}</div>
 <div class='col pane theme-light'><div class='cap'>Proposed · criterion diamond</div><div class='sub'>one glyph at every depth; the outline carries depth; shape carries state</div>{block(req_new)}</div>
</div>"""
open(os.path.join(OUT, "fig1.html"), "w").write(page(f1))

# FIG 2: state sheet light + dark
def states_pane(theme):
    rows = []
    rows.append(L(0, CB("inprog","/"), HASH + "Ship the exporter", cls="inprog", extra="<span class='anno'>owner open</span>"))
    rows.append(L(1, G1("hollow"), "Handles supported inputs", extra="<span class='anno'>Pending · ◇ hollow, owner ink</span>"))
    rows.append(L(1, G1("met"), "Legacy hand-ticked row", txtcls="muted", extra="<span class='anno'>Met by hand [x] · ◆ filled</span>"))
    rows.append(L(1, G1("dropped"), "Benchmarks within 5% of v1", txtcls="muted strike", extra="<span class='anno'>Dropped [-] · slashed, struck</span>"))
    rows.append(L(2, G1("faded"), "Under the dropped branch", txtcls="muted", extra="<span class='anno'>Excluded · faded hollow, not struck</span>"))
    rows.append(L(1, G1("carried"), "<span class='m ring next'></span><span class='link'>Docs cover every flag</span>", extra="<span class='anno'>Carried [>] · arrow, then the link's live ring</span>"))
    rows.append(L(1, G1("flag"), "Row with an unknown mark [?]", extra="<span class='anno'>Flagged · repair ink, no lane tint</span>"))
    rows.append("<div style='height:8px'></div>")
    rows.append(L(0, CB("done","✓"), HASH + "Ship the importer", txtcls="done", extra="<span class='anno'>owner done</span>"))
    rows.append(L(1, G1("met"), "Handles supported inputs", txtcls="muted", extra="<span class='anno'>Met (derived) · same ◆ as a hand tick</span>"))
    rows.append(L(1, G1("dropped"), "Benchmarks within 5% of v1", txtcls="muted strike", extra="<span class='anno'>Dropped stays readable in done/</span>"))
    rows.append("<div style='height:8px'></div>")
    rows.append(L(0, CB("cancel","–"), HASH + "Ship the old exporter", txtcls="done", extra="<span class='anno'>owner cancelled</span>"))
    rows.append(L(1, G1("faded"), "Handles supported inputs", txtcls="muted", extra="<span class='anno'>Moot (derived) · faded hollow</span>"))
    return f"<div class='col pane theme-{theme}'><div class='cap'>{theme} theme</div>{''.join(rows)}</div>"
f2 = f"<div class='title'>Proposed state set · identity by shape (◇ = requirement), state by fill, the rule Bob's task-link rings already follow</div><div class='row'>{states_pane('light')}{states_pane('dark')}</div>"
open(os.path.join(OUT, "fig2.html"), "w").write(page(f2, width=1380))

# FIG 3: alternatives
def mini(title, verdict, mk, good=False):
    rows = [L(0, CB("next","✱"), HASH + "Fix the export", cls="next")]
    for d, t in [(1, "Handles CRLF"), (2, "Windows line endings"), (3, "Mixed files")]:
        rows.append(mk(d, t))
    rows.append(L(2, DOT, "seen in the March import"))
    rows.append(L(1, DOT, "see the ticket"))
    border = "border:2px solid var(--teal);" if good else ""
    return f"<div class='col pane theme-light' style='{border}'><div class='cap'>{title}</div>{''.join(rows)}<div style='font-size:12px;color:var(--muted);margin-top:10px;white-space:normal;line-height:1.4'>{verdict}</div></div>"
def mk_run(d, t):
    n = 2 if d == 1 else 3 if d == 2 else 4
    return L(d, "", t).replace("<span class='txt '>", RUN(n) + "<span class='txt '>", 1)
alts = [
 mini("A · today: ## run", "Reads as Markdown ## headings and tags; deepest row is loudest; depth coded twice; ragged text column.", mk_run),
 mini("B · one small #", "Cheapest edit, but it is the task identity glyph: a req looks like a task missing its checkbox.", lambda d,t: L(d, G1("onehash"), t)),
 mini("C · ring ○", "Taken: Bob's rings mean “link to a task” (task-link marks), and rings are the tick target in Reminders and Microsoft To Do.", lambda d,t: L(d, G1("circ"), t)),
 mini("D · ghost checkbox", "Still a checkbox: invites the click Bob refuses; dashes turn to mush at 10 px.", lambda d,t: L(d, G1("ghost"), t)),
 mini("E · scope rail", "Pretty in a static mock, fragile live: collides with Obsidian's indent guides, breaks where notes interleave, still needs a per-row state mark.", lambda d,t: L(d, slot("<span style='display:inline-block;width:2px;height:1.75em;background:var(--teal);opacity:.8'></span><span style='display:inline-block;width:.45em;height:2px;background:var(--teal);opacity:.8'></span>"), t)),
 mini("F · criterion diamond ◇", "Unused anywhere in Bob; milestone/criterion meaning; never a checkbox; one fill rule for met, the same as rings.", lambda d,t: L(d, G1("hollow"), t), good=True),
]
f3 = "<div class='title'>Six candidate req marks on one block (owner, reqs at depths 1–3, a req note, a task note)</div><div class='row'>" + "".join(alts[:3]) + "</div><div style='height:14px'></div><div class='row'>" + "".join(alts[3:]) + "</div>"
open(os.path.join(OUT, "fig3.html"), "w").write(page(f3, width=1180))

# FIG 4: shape grammar
def gcell(kind, label, ink="var(--teal)", extra_cls=""):
    if kind == "cb": inner = f"<span class='cb {extra_cls}' style='width:1.1em;height:1.1em'>{label}</span>"
    elif kind == "dot": inner = "<span class='dot' style='width:.38em;height:.38em'></span>"
    else: inner = f"<span class='m {kind}' style='--ink:{ink};width:1.15em;height:1.15em'></span>"
    return f"<td style='text-align:center;padding:10px 14px'>{inner}</td>"
f4 = f"""<div class='title'>One shape per kind of line, one fill rule per state</div>
<div class='pane theme-light' style='width:1000px'>
<table style='border-collapse:collapse;font-size:13.5px;color:var(--text)'>
<tr style='color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.03em'><td style='padding:6px 14px'>shape</td><td style='padding:6px 14px'>means</td><td style='padding:6px 14px;text-align:center'>open</td><td style='padding:6px 14px;text-align:center'>done / met</td><td style='padding:6px 14px;text-align:center'>cancelled / dropped</td><td style='padding:6px 14px;text-align:center'>moved out</td></tr>
<tr style='border-top:1px solid var(--border)'><td style='padding:10px 14px'><b>square</b></td><td style='padding:10px 14px'>a <b>task</b> — you act on it</td>{gcell('cb','')}{gcell('cb','✓','', 'done')}{gcell('cb','–','','cancel')}<td style='text-align:center;color:var(--faint)'>—</td></tr>
<tr style='border-top:1px solid var(--border)'><td style='padding:10px 14px'><b>ring</b></td><td style='padding:10px 14px'>a <b>link to a task</b> — status at a glance</td>{gcell('ring','')}{gcell('ring done','', 'var(--muted)')}{gcell('ring cancel','', 'var(--grey)')}<td style='text-align:center;color:var(--faint)'>—</td></tr>
<tr style='border-top:1px solid var(--border);background:color-mix(in srgb, var(--teal) 7%, transparent)'><td style='padding:10px 14px'><b>diamond</b></td><td style='padding:10px 14px'>a <b>requirement</b> — met when its task closes</td>{gcell('g hollow','')}{gcell('g met','', 'var(--teal)')}{gcell('g dropped','')}{gcell('g carried','')}</tr>
<tr style='border-top:1px solid var(--border)'><td style='padding:10px 14px'><b>dot</b></td><td style='padding:10px 14px'>a <b>note</b> — you read it</td>{gcell('dot','')}<td style='text-align:center;color:var(--faint)'>—</td><td style='text-align:center;color:var(--faint)'>—</td><td style='text-align:center;color:var(--faint)'>—</td></tr>
</table></div>"""
open(os.path.join(OUT, "fig4.html"), "w").write(page(f4, width=1060))

# FIG 5: Mac capture draft
MAC_CSS = """
.mac { background:#232325; border-radius:14px; padding:16px 18px; width: 520px; border:1px solid #3a3a3c; box-shadow: 0 10px 30px rgba(0,0,0,.25);}
.mac .hdr { color:#8e8e93; font-size:11.5px; margin-bottom:8px; font-family:'DejaVu Sans'; letter-spacing:.02em; text-transform:uppercase; font-weight:bold }
.ed { position:relative; font-family:'DejaVu Sans Mono', monospace; font-size:13px; line-height:20px; color:#e5e5ea; white-space:pre; }
.ed .c { display:inline-block; width:1ch; text-align:center; }
.ed .hid { color: transparent; position: relative; }
.ed .ov { position:absolute; display:flex; align-items:center; justify-content:center; height:20px; }
.ed .route { color:#bf9cff } .ed .dash { color:#8e8e93 }
"""
def mac_line(indent, marker, text, mode):
    # returns html for one monospace line
    pre = " " * indent + "<span class='dash'>-</span> "
    if marker is None:
        return pre + text
    depth = marker
    if mode == "raw":
        return pre + "<span style='color:#8e8e93'>[ ]</span> " + text
    if mode == "today":
        n = min(depth, 3) + 1
        run = "⌗" * n
        return pre + f"<span style='position:relative;display:inline-block;width:4ch'><span style='color:transparent'>[ ] </span><span style='position:absolute;left:0;top:0;width:4ch;height:20px;display:flex;justify-content:center;align-items:center;gap:0'>{''.join("<span class='m' style='width:9px;height:11px;-webkit-mask-image:var(--g-hash);--ink:#8e8e93'></span>" for _ in range(n))}</span></span>" + text
    if mode == "new":
        return pre + f"<span style='position:relative;display:inline-block;width:4ch'><span style='color:transparent'>[ ] </span><span class='m' style='position:absolute;left:calc(1.5ch - 6.5px);top:3.5px;width:13px;height:13px;-webkit-mask-image:var(--g-hollow);--ink:#5fd4d2'></span></span>" + text
def mac(mode, hdr):
    lines = ["Fix the export <span class='route'>@work</span>",
             mac_line(0, 1, "Handles CRLF", mode),
             mac_line(2, 2, "Windows line endings", mode),
             mac_line(4, 3, "Mixed files", mode),
             mac_line(6, None, "seen in the March import", mode),
             mac_line(0, None, "see the ticket", mode)]
    return f"<div class='mac'><div class='hdr'>{hdr}</div><div class='ed'>" + "\n".join(lines) + "</div></div>"
f5 = f"<style>{MAC_CSS}</style><div class='title'>Bob Mac Capture draft (mockup): raw bytes, today's overlay, proposed overlay</div><div class='row' style='gap:14px'>{mac('raw','bytes (caret on the marker)')}{mac('today','today · ## run over [ ] (neutral ink)')}{mac('new','proposed · ◇ over [ ] ')}</div>"
open(os.path.join(OUT, "fig5.html"), "w").write(page(f5, width=1660))

# FIG 6: close card group
CARD_CSS = """
.card { width: 860px; background: var(--bg); border:1px solid var(--border); border-radius: 12px; padding: 18px 20px 14px; color: var(--text); box-shadow: 0 8px 28px rgba(0,0,0,.10); }
.card h2 { font-size: 17px; margin: 0 0 2px; }
.card .why { font-size: 12.5px; color: var(--muted); margin-bottom: 12px; }
.grp { font-size: 14px; font-weight: bold; margin: 6px 0 2px; display:flex; align-items:center; gap: 8px; }
.grp .cnt { font-weight: normal; color: var(--muted); font-size: 12.5px; }
.cap2 { font-size: 12px; color: var(--muted); margin: 0 0 8px; }
.crow { display:flex; align-items:center; padding: 6px 8px; border-radius: 7px; padding-left: calc(8px + var(--d) * 1.35em); min-height: 30px; }
.crow.sel { background: color-mix(in srgb, var(--link) 9%, transparent); box-shadow: inset 3px 0 0 var(--link); }
.crow .t { flex: 1; }
.v { font-size: 12px; padding: 2px 8px; border-radius: 999px; white-space: nowrap; }
.v.met { color: var(--muted); }
.v.drop { color: var(--red); background: color-mix(in srgb, var(--red) 10%, transparent); }
.v.carry { color: var(--link); background: color-mix(in srgb, var(--link) 10%, transparent); }
.fold { font-size: 12px; color: var(--muted); padding: 2px 8px 2px calc(8px + var(--d) * 1.35em + 1.6em); }
.foot { margin-top: 12px; border-top: 1px solid var(--border); padding-top: 10px; font-size: 12px; color: var(--muted); display:flex; gap: 14px; flex-wrap: wrap; }
.k { display:inline-block; border:1px solid var(--border); border-radius:5px; padding:0 5px; margin-right:4px; color: var(--text); background: var(--chip); }
"""
def crow(d, g, text, verdict, vcls, sel=False, tcls=""):
    return f"<div class='crow{' sel' if sel else ''}' style='--d:{d}'>{G1(g)}<span class='t {tcls}'>{text}</span><span class='v {vcls}'>{verdict}</span></div>"
f6 = f"""<style>{CARD_CSS}</style><div class='title'>Successor card · requirements group (mockup, proposed glyph; layout per the shipped contract §7)</div>
<div class='card theme-light'>
<h2>Close “Ship the exporter”</h2><div class='why'>1 owner · 4 reqs in 2 branches · 2 offers</div>
<div class='grp'><span class='m' style='width:1em;height:1em;-webkit-mask-image:var(--g-hollow);--ink:var(--teal)'></span>Requirements · “Ship the exporter” <span class='cnt'>4 reqs in 2 branches</span></div>
<div class='cap2'>Met when it closes, unless you say otherwise</div>
{crow(0,'hollow','Handles supported inputs','✓ met','met')}
{crow(1,'hollow','Handles Windows files','→ own task · pulled in','carry', sel=True)}
<div class='fold' style='--d:1'>· 1 nested goes with it</div>
{crow(1,'hollow','Handles empty input','✓ met','met')}
{crow(0,'dropped','Benchmarks within 5% of v1','⊘ drop · “v1 is gone”','drop', tcls='txt muted strike')}
<div class='fold' style='--d:0'>· 1 carried earlier</div>
<div class='grp' style='margin-top:12px'>Hand-offs <span class='cnt'>2 offers</span></div>
<div class='crow' style='--d:0'>{CB('','')}<span class='t'>Write the release notes</span><span class='v met' style='font-size:11.5px'>bob · Blocked → Ready</span></div>
<div class='foot'><span><span class='k'>⌃X</span>met</span><span><span class='k'>⌃⇧X</span>drop</span><span><span class='k'>⌃⇧T</span>own task</span><span><span class='k'>space</span>pull in</span><span><span class='k'>⌃J</span>jump</span><span style='margin-left:auto;color:var(--text)'>reqs <span class='m' style='width:.8em;height:.8em;-webkit-mask-image:var(--g-met);--ink:var(--muted);vertical-align:-1px'></span>2 ⊘1 →1</span></div>
</div>"""
open(os.path.join(OUT, "fig6.html"), "w").write(page(f6, width=920))
print("ok")
