const fs = require("node:fs"); const path = require("node:path");
const [pluginRoot, dataDir] = process.argv.slice(2);
const src = fs.readFileSync(path.join(pluginRoot, "main.js"), "utf8");
const mo = { exports: {} };
const modules = { obsidian: { Plugin: class {}, MarkdownRenderChild: class {}, MarkdownView: class {}, Notice: class {}, Platform: { isDesktopApp: false }, normalizePath: (v) => v, parseYaml: () => ({}) },
  "@codemirror/state": { Prec: { highest: (v) => v } }, "@codemirror/view": { EditorView: { updateListener: { of: (l) => ({ l }) } }, keymap: { of: (v) => v } } };
new Function("require", "module", "exports", "process", src)((n) => modules[n] || {}, mo, mo.exports, { env: { HOME: "/" } });
const h = mo.exports.helpers;
for (const id of ["2026-W45", "2026-W46", "2026-Q3", "2026-Q4", "2026"]) {
  const r = JSON.parse(fs.readFileSync(path.join(dataDir, id + ".json"), "utf8"));
  const m = h.periodStripModel(r, r.period.id, { laneView: "both", fetchedAt: r.generated_at });
  console.log(id.padEnd(9), "roots:", m.roots.segments.map((s) => s.label + "=" + s.hue).join(" "));
  console.log(" ".repeat(9), "types:", m.themes.segments.map((s) => s.label + "=" + s.hue + (s.shade ? "/" + s.shade : "")).join(" "));
  console.log(" ".repeat(9), "lanes.shown:", JSON.stringify(m.lanes.shown), "legend shown roots:", m.roots.legend.slice(0, 3).map((x) => x.label).join(","), "types:", m.themes.legend.slice(0, 3).map((x) => x.label).join(","));
}
