const fs = require("node:fs");
const [tpl, data, out] = process.argv.slice(2);
const cases = [
  { shot: "after-W45-both", id: "2026-W45", title: "2026-W45 · both charts (the default view)", view: "both" },
  { shot: "after-W45-hover", id: "2026-W45", title: "2026-W45 · hovering Thu 5: one band and one tooltip span both charts", view: "both", hoverCol: 3 },
  { shot: "after-W45-roots", id: "2026-W45", title: "2026-W45 · roots only", view: "roots" },
  { shot: "after-W45-types", id: "2026-W45", title: "2026-W45 · types only · hovering the BUILD legend item", view: "themes", highlight: { lane: "types", key: "BUILD" } },
  { shot: "after-Q4-both", id: "2026-Q4", title: "2026-Q4 · both charts · current quarter", view: "both", meta: "so far · W40–W46 · 10:06" },
  { shot: "after-Q3-both", id: "2026-Q3", title: "2026-Q3 · both charts · closed quarter (the screenshot's note)", view: "both" },
  { shot: "after-2026-both", id: "2026", title: "2026 · both charts · 53 week columns", view: "both", meta: "so far · W01–W46 · 10:06" },
];
const j = (v) => JSON.stringify(v).replace(/</g, "\\u003c");
fs.writeFileSync(out, fs.readFileSync(tpl, "utf8").replace("__DATA__", () => j(JSON.parse(fs.readFileSync(data, "utf8")))).replace("__CASES__", () => j(cases)));
console.log("wrote", out);
