const fs = require("fs");
const M = require("./mock.js");
const { THEMES, fmt, facts, rhythm, running, where, who, footer, css } = M;
const mono = (ch) => `<span style="display:inline-flex;width:15px;height:15px;border-radius:4px;align-items:center;justify-content:center;font-size:9.5px;font-weight:700;background:rgba(127,127,127,.18)">${ch}</span>`;

function week(t) {
  const cols = [
    { cap: "Mon 23", out: 2340, inn: 0, state: "tracked" },
    { cap: "Tue 24", out: 14580, inn: 0, state: "tracked" },
    { cap: "Wed 25", out: 18635, inn: 0, state: "tracked" },
    { cap: "Thu 26", out: 6420, inn: 0, state: "tracked", waiting: true },
    { cap: "Fri 27", out: 41288, inn: 248615, state: "tracked", focus: true, label: "$412.88" },
    { cap: "Sat 28", state: "awaiting" },
    { cap: "Sun 29", state: "awaiting" },
  ];
  return `<div class="panel"><div class="crumb">2026-W48 · Nov 23 – 29 · Money section (closed week, Monday before import)</div><h2>Money</h2>` +
    facts(t, [
      { label: "In", value: "+$2,486.15", sub: "1 income row", ink: t.inInk },
      { label: "Out", value: "$832.63", sub: "12 rows · 7 payees" },
      { label: "Net", value: "+$1,653.52", sub: "kept 67% of in", ink: t.inInk },
      { label: "Out / day", value: "$166.53", sub: "over 5 imported days" },
    ]) +
    rhythm(t, { id: "w", title: "Out per day", cols, height: 70, barMax: 30,
      scaleNote: "", tooltip: { left: 40, top: 0, html: `<b>Fri Nov 27</b><br><span class="g">In +$2,486.15</span> <span class="m">· Income</span><br>Out $412.88 <span class="m">· 3 rows</span><br><span class="m">Shopping $310.00 · Delivery $94.24</span><br><span class="m">Click: open Nov 27 in bank/2026-11.md</span>` } }) +
    where(t, { whole: false, groups: "Everyday $695.47 · Bills $137.16", more: "＋ 1 more · Coffee $34.56",
      rows: [
        { icon: mono("S"), label: "Shopping", out: 31000, share: "37%", n: 1 },
        { icon: mono("G"), label: "Groceries", out: 15686, share: "19%", n: 2, open: [["Wed 25", "Corner Market", "$142.10"], ["Mon 23", "Corner Market", "$14.76"]], more: "Click a row to open it in bank/2026-11.md" },
        { icon: mono("L"), label: "Loans", out: 13716, share: "16%", n: 1 },
        { icon: mono("D"), label: "Delivery", out: 9424, share: "11%", n: 1 },
        { icon: mono("E"), label: "Eating out", out: 6420, share: "8%", n: 2 },
        { icon: mono("C"), label: "Convenience", out: 3561, share: "4%", n: 1 },
      ] }) +
    who(t, { payees: [[mono("G"), "Corner Market", 2, "$156.86"], [mono("C"), "Track Coffee", 4, "$34.56"], [mono("S"), "Outdoor Outfitters", 1, "$310.00"], [mono("L"), "Student Loan Svc", 1, "$137.16"]].sort((a,b)=>parseFloat(b[3].slice(1))-parseFloat(a[3].slice(1))),
      largest: [["Fri 27", "Outdoor Outfitters", "$310.00"], ["Wed 25", "Corner Market", "$142.10"], ["Tue 24", "Student Loan Svc", "$137.16"], ["Fri 27", "QuickEats", "$94.24"]] }) +
    footer(t, [`<span class="w">● 2 waiting</span> <span class="lk">file them</span>`, "Sat–Sun not imported yet (imported through Fri Nov 27)", "Not counted: ↔ transfers $500.00"]) + `</div>`;
}

function quarter(t, label) {
  const outs = [61200, 43800, 70100, 39500, 221000, 52000, 48900, 97600];
  const ins = [248615, 0, 248615, 0, 252833, 0, 248615, 0];
  const cols = outs.map((o, i) => ({ cap: `W${String(i + 1).padStart(2, "0")}`, out: o, inn: ins[i], state: "tracked", label: i === 4 ? "$2,210" : "" }));
  cols.push({ cap: "W09", state: "awaiting" });
  for (let i = 10; i <= 13; i += 1) cols.push({ cap: `W${i}`, state: "future" });
  let ci = 0, co = 0; const cumIn = [], cumOut = [];
  outs.forEach((o, i) => { ci += ins[i]; co += o; cumIn.push(ci); cumOut.push(co); });
  return `<div class="panel"><div class="crumb">2027-Q1 · W01–W13 · Jan 4 – Apr 4, 2027 · ${label}</div><h2>Money</h2>` +
    facts(t, [
      { label: "In", value: "+$9,987", sub: "4 income · 1 refund", ink: t.inInk },
      { label: "Out", value: "$6,341", sub: "214 rows · 61 payees" },
      { label: "Net", value: "+$3,646", sub: "kept 37% of in", ink: t.inInk },
      { label: "Out / day", value: "$113", sub: "so far · 56 imported days" },
    ]) +
    running(t, { id: "q" + label.length, title: "Running totals", slots: 13, startSlot: 0, cumIn, cumOut, inLabel: "$9,987", outLabel: "$6,341", futureFrom: 9, awaitFrom: 8, awaitSlots: 1,
      legend: `<i class="ln" style="background:${t.inFill}"></i>In <i class="ln" style="background:${t.outFill}"></i>Out <i class="sw" style="background:${t.wash};border:1px solid ${t.border}"></i>kept` }) +
    rhythm(t, { id: "q" + label, title: "Out per week", cols, height: 52, barMax: 26, capSize: 10.5 }) +
    where(t, { whole: true, groups: "Everyday $3,729 · Bills $2,612", more: "＋ 9 more · $1,174",
      rows: [
        { icon: mono("H"), label: "Housing", out: 165000, share: "26%", n: 1 },
        { icon: mono("G"), label: "Groceries", out: 112400, share: "18%", n: 14 },
        { icon: mono("E"), label: "Eating out", out: 70200, share: "11%", n: 19 },
        { icon: mono("C"), label: "Car", out: 64000, share: "10%", n: 1 },
        { icon: mono("L"), label: "Loans", out: 54864, share: "9%", n: 4 },
        { icon: mono("?"), label: "Unclassified", out: 21300, share: "3%", n: 6, hatch: true },
      ] }) +
    who(t, { payees: [[mono("H"), "Rent Co", 1, "$1,650"], [mono("G"), "Corner Market", 14, "$1,018"], [mono("A"), "Midas", 1, "$640"], [mono("L"), "Student Loan Svc", 4, "$549"], [mono("C"), "Track Coffee", 31, "$268"]],
      largest: [["Feb 1", "Rent Co", "$1,650"], ["Feb 24", "Midas", "$640"], ["Jan 15", "Outdoor Outfitters", "$215"], ["Feb 12", "Trattoria", "$148"], ["Jan 9", "Corner Market", "$141"]] }) +
    footer(t, ["W09 not imported yet (imported through Feb 28)", "Not counted: ↔ transfers $2,000 · cash out $120 · unclassified in +$35", "WF Checking · balanced"]) + `</div>`;
}

function yearSparse(t) {
  const cols = [
    { cap: "W01 – W45", state: "collapsed", note: "before bank tracking" },
    { cap: "W46", out: 24977, inn: 0, state: "partial" },
    { cap: "W47", out: 61040, inn: 248615, state: "tracked" },
    { cap: "W48", state: "awaiting" },
    ...[49, 50, 51, 52, 53].map((w) => ({ cap: `W${w}`, state: "future" })),
  ];
  return `<div class="panel"><div class="crumb">2026 · ISO year · Dec 29, 2025 – Jan 3, 2027 · sparse truth today</div><h2>Money</h2>` +
    facts(t, [
      { label: "In", value: "+$2,486", sub: "1 income row", ink: t.inInk },
      { label: "Out", value: "$860", sub: "19 rows · 11 payees" },
      { label: "Net", value: "+$1,626", sub: "kept 65% of in", ink: t.inInk },
      { label: "Out / day", value: "$72", sub: "so far · 12 imported days" },
    ]) +
    rhythm(t, { id: "y", title: "Out per week", cols, height: 52, barMax: 22, collapsedSlots: 4, capSize: 10.5 }) +
    `<div class="more" style="margin:-2px 0 8px">Running totals appear once two full weeks are imported.</div>` +
    where(t, { whole: true, groups: "Everyday $511 · Bills $349", more: "＋ 4 more · $96",
      rows: [
        { icon: mono("L"), label: "Loans", out: 27432, share: "32%", n: 2 },
        { icon: mono("G"), label: "Groceries", out: 18850, share: "22%", n: 3 },
        { icon: mono("T"), label: "Tech & AI", out: 9276, share: "11%", n: 2 },
      ] }) +
    footer(t, ["Tracked since Nov 11, 2026", "imported through Nov 22", "W48 not imported yet"]) + `</div>`;
}

const page = (body, t) => `<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:${t.bg}} ${css(t)}</style></head><body>${body}</body></html>`;
fs.writeFileSync("/tmp/bankviz_cld/week.html", page(week(THEMES.light), THEMES.light));
fs.writeFileSync("/tmp/bankviz_cld/quarter_light.html", page(quarter(THEMES.light, "so far, light"), THEMES.light));
fs.writeFileSync("/tmp/bankviz_cld/quarter_dark.html", page(quarter(THEMES.dark, "so far, dark"), THEMES.dark));
fs.writeFileSync("/tmp/bankviz_cld/year_sparse.html", page(yearSparse(THEMES.light), THEMES.light));
console.log("written");
