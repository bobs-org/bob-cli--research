// Build before.html: the production period strip painted from real `bob periods show` reports.
const fs = require("node:fs"); const path = require("node:path");
const [pluginRoot, dataDir, outFile] = process.argv.slice(2);
const main = fs.readFileSync(path.join(pluginRoot, "main.js"), "utf8");
const css = fs.readFileSync(path.join(pluginRoot, "styles.css"), "utf8");
const tpl = fs.readFileSync(path.join(pluginRoot, "../../scripts/preview-period-strip.template.html"), "utf8");
const themeCss = tpl.slice(tpl.indexOf("<style>") + 7, tpl.indexOf("</style>"));
const ids = ["2026-W45", "2026-Q3", "2026-Q4", "2026", "all"];
const reports = Object.fromEntries(ids.map((id) => [id, JSON.parse(fs.readFileSync(path.join(dataDir, id + ".json"), "utf8"))]));
const j = (v) => JSON.stringify(v).replace(/</g, "\\u003c");
const html = `<!doctype html><html><head><meta charset="utf-8"><style>${themeCss}
.preview-note{width:760px;margin:10px auto} h2{font:600 12px system-ui;color:#6f6c65;margin:0 0 4px}</style>
<style>:root { --input-height: 30px; } button{display:inline-flex;height:var(--input-height)}</style>
<style>${css}</style></head><body class="theme-light"><main id="root"></main>
<script>
try {
  if (location.hash === "#dark") document.body.className = "theme-dark";
  const pluginSource = ${j(main)}; const reports = ${j(reports)};
  const mo = { exports: {} };
  const modules = { obsidian: { Plugin: class {}, MarkdownRenderChild: class {}, MarkdownView: class {}, Notice: class {}, Platform: { isDesktopApp: false }, normalizePath: (v) => v, parseYaml: () => ({}) },
    "@codemirror/state": { Prec: { highest: (v) => v } }, "@codemirror/view": { EditorView: { updateListener: { of: (l) => ({ l }) } }, keymap: { of: (v) => v } } };
  new Function("require", "module", "exports", "process", pluginSource)((n) => modules[n] || {}, mo, mo.exports, { env: { HOME: "/" } });
  const h = mo.exports.helpers;
  for (const id of ${j(ids)}) {
    const wrap = document.createElement("div"); wrap.className = "preview-note"; wrap.setAttribute("data-shot", "before-" + id + (location.hash === "#dark" ? "-dark" : ""));
    const t = document.createElement("h2"); t.textContent = "Today · " + id; wrap.appendChild(t);
    const host = document.createElement("div"); wrap.appendChild(host); document.getElementById("root").appendChild(wrap);
    const r = reports[id];
    const model = h.periodStripModel(r, r.period.id, { laneView: "both", fetchedAt: r.generated_at });
    h.paintPeriodStrip(host, model, {});
  }
} catch (e) { window.__err = String(e && e.stack || e); }
</script></body></html>`;
fs.writeFileSync(outFile, html);
console.log("wrote", outFile, html.length);
