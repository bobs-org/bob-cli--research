// Mockup generator for the Bank Period View (illustrative data only).
const fs = require("fs");
const THEMES = {
  light: { bg: "#ffffff", text: "#222222", muted: "#5c5c5c", faint: "#9a9a9a", border: "#e3e3e3",
    inInk: "#127c3c", inFill: "#2e9e58", outFill: "#858585", outFillSoft: "#b9b9b9", warn: "#b36b00", accent: "#7852ee", wash: "rgba(8,185,78,0.10)" },
  dark: { bg: "#1e1e1e", text: "#dadada", muted: "#b3b3b3", faint: "#777777", border: "#363636",
    inInk: "#80d399", inFill: "#56c27c", outFill: "#858585", outFillSoft: "#5a5a5a", warn: "#e0a94a", accent: "#8a6cf0", wash: "rgba(68,207,110,0.12)" },
};
const fmt = (c, opts = {}) => {
  const whole = opts.whole;
  const sign = opts.plus ? "+" : (c < 0 ? "−" : "");
  const a = Math.abs(c);
  if (whole && a >= 100) return sign + "$" + Math.round(a / 100).toLocaleString("en-US");
  return sign + "$" + (a / 100).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};
const short = (c) => { const d = Math.abs(c) / 100; return d >= 1000 ? "$" + (d / 1000).toFixed(d >= 10000 ? 0 : 1) + "k" : "$" + Math.round(d); };

function facts(t, f) {
  return `<div class="facts">${f.map((x) => `<div class="fact"><div class="lab">${x.label}</div><div class="val" style="color:${x.ink || t.text}">${x.value}</div><div class="sub">${x.sub}</div></div>`).join("")}</div>`;
}

function rhythm(t, m) {
  // m.cols: [{cap, out, inn, state: tracked|ghost|awaiting|future|collapsed, waiting, group}]
  const W = 568, H = m.height || 74, top = 36, capH = 30, gap = 2; const GUT = 92; m.id = String(m.id).replace(/[^a-z0-9]/gi, '');
  const slots = m.cols.map((c) => c.state === "collapsed" ? (m.collapsedSlots || 3) : 1);
  const total = slots.reduce((a, b) => a + b, 0);
  const unit = W / total;
  const maxOut = Math.max(...m.cols.filter((c) => c.state === "tracked" || c.state === "partial").map((c) => c.out), 1);
  let x = 0, svg = "";
  svg += `<line x1="0" x2="${W}" y1="${top + H}" y2="${top + H}" stroke="${t.border}" stroke-width="1"/>`;
  const labels = [];
  if (m.scaleNote) labels.push(`<text x="${W + 10}" y="${top + 6}" font-size="10.5" fill="${t.faint}">${m.scaleNote}</text>`);
  m.cols.forEach((c, i) => {
    const sw = slots[i] * unit;
    const bw = Math.min(m.barMax || 24, sw - gap * 2);
    const bx = x + (sw - bw) / 2;
    if (c.state === "tracked" || c.state === "partial") {
      const h = c.out > 0 ? Math.max(2, (c.out / maxOut) * H) : 0;
      if (h) svg += `<path d="M${bx},${top + H} v${-(h - 2)} q0,-2 2,-2 h${bw - 4} q2,0 2,2 v${h - 2} z" fill="${c.state === "partial" ? t.outFillSoft : t.outFill}"/>`;
      if (c.inn > 0) {
        const cy = 4;
        svg += `<circle cx="${bx + bw / 2}" cy="${cy + 4}" r="4" fill="${t.inFill}" stroke="${t.bg}" stroke-width="2"/>`;
        if (m.inLabels !== false) labels.push(`<text x="${bx + bw / 2 + 7}" y="${cy + 7.5}" font-size="10.5" fill="${t.inInk}" font-weight="700">+${short(c.inn)}</text>`);
      }
      if (c.label) labels.push(`<text x="${bx + bw / 2}" y="${top + H - Math.max(2, (c.out / maxOut) * H) - 4}" text-anchor="middle" font-size="10.5" fill="${t.muted}">${c.label}</text>`);
    } else if (c.state === "awaiting") {
      const h = H * 0.35;
      svg += `<rect x="${bx}" y="${top + H - h}" width="${bw}" height="${h}" rx="2" fill="url(#hatch-${m.id})" stroke="${t.faint}" stroke-dasharray="2 2" stroke-width="1"/>`;
    } else if (c.state === "ghost" || c.state === "collapsed") {
      const h = H * 0.35;
      const gx = c.state === "collapsed" ? x + 6 : bx, gw = c.state === "collapsed" ? sw - 12 : bw;
      svg += `<rect x="${gx}" y="${top + H - h}" width="${gw}" height="${h}" rx="2" fill="none" stroke="${t.faint}" stroke-dasharray="1.5 2.5" stroke-width="1.2"/>`;
      if (c.state === "collapsed") svg += `<text x="${x + sw / 2}" y="${top + H - h / 2 + 4}" text-anchor="middle" font-size="10.5" fill="${t.faint}">${c.note}</text>`;
    } else if (c.state === "future") {
      svg += `<rect x="${bx}" y="${top + H - 2}" width="${bw}" height="2" fill="${t.border}"/>`;
    }
    // caption
    const capColor = c.state === "future" || c.state === "ghost" || c.state === "collapsed" ? t.faint : t.muted;
    if (c.cap) svg += `<text x="${x + sw / 2}" y="${top + H + 14}" text-anchor="middle" font-size="${m.capSize || 11}" fill="${capColor}" ${c.focus ? 'text-decoration="underline"' : ""}>${c.cap}</text>`;
    if (c.waiting) svg += `<circle cx="${x + sw / 2}" cy="${top + H + 22}" r="2.6" fill="${t.warn}"/>`;
    if (c.focus) svg += `<rect x="${x + 1}" y="${top - 16}" width="${sw - 2}" height="${H + 44}" rx="4" fill="none" stroke="${t.accent}" stroke-width="2"/>`;
    x += sw;
  });
  // groups
  if (m.groups) {
    let gx = 0;
    m.groups.forEach((g) => {
      const gw = g.slots * unit;
      svg += `<line x1="${gx + 3}" x2="${gx + gw - 3}" y1="${top + H + capH + 2}" y2="${top + H + capH + 2}" stroke="${t.border}"/>`;
      svg += `<text x="${gx + 3}" y="${top + H + capH + 15}" font-size="10.5" fill="${t.muted}">${g.label}</text>`;
      gx += gw;
    });
  }
  const extra = m.groups ? 20 : 0;
  const defs = `<defs><pattern id="hatch-${m.id}" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="5" stroke="${t.faint}" stroke-width="1.2"/></pattern></defs>`;
  let tip = "";
  if (m.tooltip) tip = `<div class="tip" style="left:${m.tooltip.left}px;top:${m.tooltip.top}px">${m.tooltip.html}</div>`;
  return `<div class="chart"><div class="chartlab"><span class="lab">${m.title}</span><span class="legend"><i class="sw out"></i>Out <i class="dot"></i>In</span></div><div style="position:relative"><svg width="${W + GUT}" height="${top + H + capH + extra}" font-family="Lato, sans-serif">${defs}${svg}${labels.join("")}</svg>${tip}</div></div>`;
}

function running(t, m) {
  // cumulative In (green) vs Out (graphite), x across child slots; ghost region before start
  const W = 660, H = 92, top = 10, padR = 92; m.id = String(m.id).replace(/[^a-z0-9]/gi, '');
  const n = m.slots;
  const xw = (W - padR) / n;
  const maxV = Math.max(m.cumIn[m.cumIn.length - 1], m.cumOut[m.cumOut.length - 1]);
  const y = (v) => top + H - (v / maxV) * H;
  const xs = (i) => (i + 1) * xw; // end of slot i
  const s0 = m.startSlot; // first tracked slot index
  let svg = `<line x1="0" x2="${W - padR}" y1="${top + H}" y2="${top + H}" stroke="${t.border}"/>`;
  if (s0 > 0) {
    svg += `<rect x="0" y="${top}" width="${s0 * xw}" height="${H}" fill="none"/>`;
    svg += `<line x1="0" x2="${s0 * xw}" y1="${top + H - 0.5}" y2="${top + H - 0.5}" stroke="${t.faint}" stroke-dasharray="1.5 2.5"/>`;
    svg += `<text x="${(s0 * xw) / 2}" y="${top + H - 8}" text-anchor="middle" font-size="10.5" fill="${t.faint}">before bank tracking</text>`;
  }
  const pts = (arr) => arr.map((v, k) => `${xs(s0 + k)},${y(v)}`);
  const startPt = `${s0 * xw},${top + H}`;
  const inPts = [startPt, ...pts(m.cumIn)], outPts = [startPt, ...pts(m.cumOut)];
  // shaded gap where in leads
  const area = [...inPts, ...outPts.slice().reverse()].join(" ");
  svg += `<clipPath id="lead-${m.id}"><polygon points="${inPts.join(" ")} ${xs(s0 + m.cumIn.length - 1)},${top + H}"/></clipPath>`;
  svg += `<polygon points="${area}" fill="${t.wash}" clip-path="url(#lead-${m.id})"/>`;
  svg += `<polyline points="${outPts.join(" ")}" fill="none" stroke="${t.outFill}" stroke-width="2" stroke-linejoin="round"/>`;
  svg += `<polyline points="${inPts.join(" ")}" fill="none" stroke="${t.inFill}" stroke-width="2" stroke-linejoin="round"/>`;
  const lx = xs(s0 + m.cumIn.length - 1);
  if (m.awaitFrom != null) {
    svg += `<rect x="${xs(m.awaitFrom - 1)}" y="${top}" width="${xw * m.awaitSlots}" height="${H}" fill="url(#hatch2-${m.id})" opacity="0.5"/>`;
  }
  if (m.futureFrom != null) {
    svg += `<line x1="${lx}" x2="${W - padR}" y1="${top + H - 0.5}" y2="${top + H - 0.5}" stroke="${t.border}" stroke-width="2"/>`;
  }
  svg += `<circle cx="${lx}" cy="${y(m.cumIn[m.cumIn.length - 1])}" r="3.5" fill="${t.inFill}" stroke="${t.bg}" stroke-width="2"/>`;
  svg += `<circle cx="${lx}" cy="${y(m.cumOut[m.cumOut.length - 1])}" r="3.5" fill="${t.outFill}" stroke="${t.bg}" stroke-width="2"/>`;
  svg += `<text x="${lx + 8}" y="${y(m.cumIn[m.cumIn.length - 1]) + 4}" font-size="11" fill="${t.inInk}" font-weight="700">In ${m.inLabel}</text>`;
  svg += `<text x="${lx + 8}" y="${y(m.cumOut[m.cumOut.length - 1]) + 4}" font-size="11" fill="${t.text}" font-weight="700">Out ${m.outLabel}</text>`;
  const defs = `<defs><pattern id="hatch2-${m.id}" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="5" stroke="${t.faint}" stroke-width="1"/></pattern></defs>`;
  return `<div class="chart"><div class="chartlab"><span class="lab">${m.title}</span><span class="legend">${m.legend}</span></div><svg width="${W}" height="${top + H + 6}" font-family="Lato, sans-serif">${defs}${svg}</svg></div>`;
}

function where(t, m) {
  const max = Math.max(...m.rows.map((r) => r.out));
  const rows = m.rows.map((r) => `<div class="cat${r.open ? " open" : ""}${r.hatch ? " hatch" : ""}"><span class="cname">${r.icon ? `<span class="ic">${r.icon}</span>` : ""}${r.label}</span><span class="track"><span class="fill" style="width:${(r.out / max) * 100}%"></span></span><span class="amt">${fmt(r.out, { whole: m.whole })}</span><span class="share">${r.share}</span><span class="rows">${r.n}×</span></div>${r.open ? `<div class="drill">${r.open.map((o) => `<div class="drow"><span class="ddate">${o[0]}</span><span class="dpay">${o[1]}</span><span class="damt">${o[2]}</span></div>`).join("")}<div class="dmore">${r.more}</div></div>` : ""}`).join("");
  return `<div class="block"><div class="chartlab"><span class="lab">Where it went</span><span class="legend groups">${m.groups}</span></div>${rows}<div class="more">${m.more}</div></div>`;
}

function who(t, m) {
  const pay = m.payees.map((p) => `<div class="li"><span class="ic">${p[0]}</span><span class="nm">${p[1]}</span><span class="ct">${p[2]}×</span><span class="am">${p[3]}</span></div>`).join("");
  const big = m.largest.map((p) => `<div class="li"><span class="dt">${p[0]}</span><span class="nm">${p[1]}</span><span class="am">${p[2]}</span></div>`).join("");
  return `<div class="two"><div><div class="chartlab"><span class="lab">Top payees</span></div>${pay}</div><div><div class="chartlab"><span class="lab">Largest</span></div>${big}</div></div>`;
}

function footer(t, parts) {
  return `<div class="foot">${parts.join('<span class="sep"> · </span>')}</div>`;
}

function css(t) {
  return `
  .panel{background:${t.bg};color:${t.text};font-family:Lato,"DejaVu Sans",sans-serif;width:700px;padding:18px 20px 20px;box-sizing:border-box}
  .crumb{font-size:12px;color:${t.faint};margin-bottom:6px;letter-spacing:.02em}
  h2{font-size:22px;margin:4px 0 12px;font-weight:700}
  .facts{display:grid;grid-template-columns:repeat(4,1fr);margin-bottom:14px}
  .fact{padding:0 12px;border-left:1px solid ${t.border}} .fact:first-child{border-left:none;padding-left:0}
  .lab{font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;color:${t.muted};font-weight:700}
  .val{font-size:21px;font-weight:700;margin:2px 0 1px}
  .sub{font-size:11.5px;color:${t.faint}}
  .chart{margin:6px 0 10px}
  .chartlab{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px}
  .legend{font-size:11px;color:${t.muted}}
  .legend .sw{display:inline-block;width:9px;height:9px;border-radius:2px;margin:0 4px 0 10px;vertical-align:-1px}
  .legend .sw.out{background:${t.outFill}}
  .legend .dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:${t.inFill};margin:0 4px 0 10px;vertical-align:-1px}
  .legend .ln{display:inline-block;width:14px;height:2px;margin:0 4px 0 10px;vertical-align:3px}
  .block{margin:12px 0 10px}
  .cat{display:grid;grid-template-columns:150px 1fr 82px 40px 30px;align-items:center;gap:8px;font-size:13px;padding:2.5px 0;font-variant-numeric:tabular-nums}
  .cat .ic{display:inline-block;width:18px;text-align:center;margin-right:5px;color:${t.muted}}
  .track{height:7px;border-radius:999px;background:${t.border};overflow:hidden;display:block}
  .fill{display:block;height:100%;border-radius:999px;background:${t.outFill}}
  .cat.hatch .fill{background:repeating-linear-gradient(45deg,${t.outFill} 0 2px,transparent 2px 4.5px)}
  .cat.open .cname{text-decoration:underline;text-decoration-color:${t.accent};text-underline-offset:3px}
  .amt{text-align:right} .share,.rows{text-align:right;color:${t.faint};font-size:11.5px}
  .drill{margin:2px 0 6px 28px;padding-left:10px;border-left:2px solid ${t.border}}
  .drow{display:grid;grid-template-columns:62px 1fr 80px;font-size:12px;color:${t.muted};padding:1.5px 0;font-variant-numeric:tabular-nums}
  .damt{text-align:right;color:${t.text}} .dmore{font-size:11.5px;color:${t.faint};padding-top:2px}
  .more{font-size:11.5px;color:${t.muted};margin-top:3px}
  .two{display:grid;grid-template-columns:1fr 1fr;gap:28px;margin:10px 0}
  .li{display:flex;gap:8px;font-size:12.5px;padding:2.5px 0;align-items:baseline;font-variant-numeric:tabular-nums}
  .li .nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis} .li .ct,.li .dt{color:${t.faint};font-size:11.5px;min-width:42px} .li .am{text-align:right} .li .ic{color:${t.muted};width:16px;text-align:center}
  .foot{font-size:11.5px;color:${t.faint};margin-top:10px;padding-top:8px;border-top:1px solid ${t.border};line-height:1.6}
  .foot .w{color:${t.warn};font-weight:700} .foot .lk{color:${t.muted};text-decoration:underline;text-decoration-color:${t.border};text-underline-offset:2px}
  .tip{position:absolute;background:${t.bg};border:1px solid ${t.border};box-shadow:0 4px 14px rgba(0,0,0,.18);border-radius:6px;padding:7px 9px;font-size:11.5px;line-height:1.45;color:${t.text};white-space:nowrap;font-variant-numeric:tabular-nums}
  .tip b{font-weight:700} .tip .m{color:${t.muted}} .tip .g{color:${t.inInk};font-weight:700}
  `;
}
module.exports = { THEMES, fmt, short, facts, rhythm, running, where, who, footer, css };
