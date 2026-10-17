# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.62.0"]
# ///
"""Lead-researcher spike: batch-render Mermaid fences to fitted PDFs.

argv: mermaid_js font_ttf out_dir diagram.mmd [diagram.mmd ...]
"""
import base64
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

mermaid_js, font_ttf, out_dir, *sources = sys.argv[1:]
os.makedirs(out_dir, exist_ok=True)
font_b64 = base64.b64encode(open(font_ttf, "rb").read()).decode()
css = (
    "@font-face{font-family:'BobDiagram';"
    f"src:url(data:font/ttf;base64,{font_b64}) format('truetype');}}"
    "html,body{margin:0;padding:0;background:white}"
)
t0 = time.monotonic()
requests = []
results = []
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path="/opt/google/chrome/chrome")
    context = browser.new_context()

    def _abort(route):
        requests.append(route.request.url[:60])
        route.abort()

    context.route("**/*", _abort)
    page = context.new_page()
    page.goto("about:blank")
    page.add_style_tag(content=css)
    page.add_script_tag(content=open(mermaid_js, encoding="utf-8").read())
    page.evaluate(
        """() => mermaid.initialize({startOnLoad:false, securityLevel:'strict',
            theme:'neutral', fontFamily:'BobDiagram', themeVariables:{dropShadow:'none'}, themeCSS:'* { filter: none !important; }',
            flowchart:{useMaxWidth:false}, sequence:{useMaxWidth:false},
            state:{useMaxWidth:false}})"""
    )
    page.evaluate("() => document.fonts.load('16px BobDiagram')")
    for i, src_path in enumerate(sources):
        text = open(src_path, encoding="utf-8").read()
        t = time.monotonic()
        try:
            box = page.evaluate(
                """async ([id, text]) => {
                    document.body.innerHTML = '';
                    const {svg} = await mermaid.render(id, text);
                    const host = document.createElement('div');
                    host.style.display = 'inline-block';
                    host.innerHTML = svg;
                    document.body.appendChild(host);
                    await document.fonts.ready;
                    const r = host.getBoundingClientRect();
                    return {w: Math.ceil(r.width), h: Math.ceil(r.height)};
                }""",
                [f"d{i}", text],
            )
            out = os.path.join(out_dir, f"d{i}.pdf")
            page.pdf(path=out, width=f"{box['w']}px", height=f"{box['h'] + 1}px",
                     print_background=True, page_ranges="1")
            results.append({"src": src_path, "ok": True, "pdf": out, **box,
                            "ms": round((time.monotonic() - t) * 1000)})
        except Exception as exc:  # noqa: BLE001
            results.append({"src": src_path, "ok": False,
                            "error": str(exc).splitlines()[0][:160]})
    browser.close()
print(json.dumps({"total_s": round(time.monotonic() - t0, 2),
                  "blocked_requests": requests, "results": results}, indent=1))
