// Minimal CDP screenshot helper: node cdp.cjs <html> <outdir> <selector-prefix> <width> [theme]
const fs = require("node:fs"); const os = require("node:os"); const path = require("node:path");
const { spawn } = require("node:child_process"); const { pathToFileURL } = require("node:url");
function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }
function findChromium() {
  const cache = path.join(os.homedir(), ".cache/ms-playwright");
  for (const d of fs.readdirSync(cache).sort().reverse()) {
    if (!d.startsWith("chromium-")) continue;
    for (const p of ["chrome-linux64", "chrome-linux"]) { const e = path.join(cache, d, p, "chrome"); if (fs.existsSync(e)) return e; }
  }
  throw new Error("no chromium");
}
class Cdp {
  constructor(s) { this.s = s; this.id = 1; this.p = new Map(); s.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && this.p.has(m.id)) { const x = this.p.get(m.id); this.p.delete(m.id); m.error ? x.rej(new Error(JSON.stringify(m.error))) : x.res(m.result || {}); } }); }
  call(method, params = {}) { const id = this.id++; return new Promise((res, rej) => { this.p.set(id, { res, rej }); this.s.send(JSON.stringify({ id, method, params })); }); }
  async ev(expr) { const r = await this.call("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 800)); return r.result && r.result.value; }
}
(async () => {
  const [html, outdir, width, theme] = process.argv.slice(2);
  fs.mkdirSync(outdir, { recursive: true });
  const profile = fs.mkdtempSync("/tmp/cld-ps-chrome-");
  const child = spawn(findChromium(), ["--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore", env: { ...process.env, TMPDIR: "/tmp" } });
  try {
    const f = path.join(profile, "DevToolsActivePort");
    for (let i = 0; i < 300 && !fs.existsSync(f); i++) await sleep(100);
    const port = fs.readFileSync(f, "utf8").split(/\s+/)[0];
    let page = null;
    for (let i = 0; i < 40 && !page; i++) { const pages = await fetch(`http://127.0.0.1:${port}/json/list`).then((r) => r.json()); page = pages.find((p) => p.type === "page"); if (!page) await sleep(100); }
    const ws = new WebSocket(page.webSocketDebuggerUrl); await new Promise((r, j) => { ws.addEventListener("open", r, { once: true }); ws.addEventListener("error", j, { once: true }); });
    const c = new Cdp(ws);
    await c.call("Page.enable"); await c.call("Runtime.enable");
    await c.call("Emulation.setDeviceMetricsOverride", { width: Number(width), height: 1400, deviceScaleFactor: 2, mobile: false });
    await c.call("Page.navigate", { url: pathToFileURL(path.resolve(html)).href + (theme ? "#" + theme : "") });
    await sleep(1500);
    const err = await c.ev("window.__err || ''"); if (err) console.error("PAGE ERROR:", err);
    const boxes = await c.ev(`Array.from(document.querySelectorAll('[data-shot]')).map(e => { const r = e.getBoundingClientRect(); return { name: e.getAttribute('data-shot'), x: r.x + window.scrollX, y: r.y + window.scrollY, w: r.width, h: r.height }; })`);
    for (const b of boxes) {
      const shot = await c.call("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: b.x, y: b.y, width: b.w, height: b.h, scale: 1 } });
      fs.writeFileSync(path.join(outdir, b.name + ".png"), Buffer.from(shot.data, "base64"));
      console.log("wrote", b.name, Math.round(b.w) + "x" + Math.round(b.h));
    }
    ws.close();
  } finally { child.kill(); }
})().catch((e) => { console.error(e); process.exit(1); });
