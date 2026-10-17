# Mermaid diagrams in `bob ref create` PDFs

_Researcher: cld · 2026-10-17 · Scope: bob-cli `bob ref create` Markdown routes_

## TL;DR

- **Diagnosis.** The screenshot shows the plain-Markdown route (pandoc → XeLaTeX,
  `--toc --number-sections`, DejaVu fonts). Pandoc treats a ` ```mermaid ` fence as an
  ordinary `CodeBlock`, so it is typeset as highlighted source. Nothing in `src/`
  mentions Mermaid. It is a missing feature, not a regression.
- **Worth doing?** Yes. Mermaid in agent-written reports is meant as a picture: GitHub,
  Obsidian, and VS Code all render it. Printed as source, it is noise you can't usefully
  annotate in Highlights. But two of the "obvious" implementations are traps (details
  below).
- **Recommendation.** Render Mermaid with a **pinned, vendored `mermaid.min.js` running in
  Bob's existing headless-Chrome adapter** (the uv + Playwright adapter that web-article
  capture already uses). Do it in **one browser launch per document**, producing
  **fitted vector PDFs**. Swap them in with a small pandoc Lua filter shared by both
  Markdown routes. Fall back to today's code block, plus a visible note and a warning,
  whenever anything fails. **Do not** shell out to `mmdc` via pandoc-ext/diagram as the
  durable solution. **Do not** adopt the native-Rust renderer `mmdr` yet.
- I prototyped the recommended path end to end on athena (pandoc 3.1.11.1) and on the
  Mac (pandoc 3.11).

## 1. What is happening today

| Fact | Evidence |
| --- | --- |
| Plain `.md` targets go through one pandoc call with `--pdf-engine=xelatex`, two Lua filters (code-break/listen, then return links), `--highlight-style=tango` | `src/native/highlights_ref/create.rs:3224` (`render_temp_pdf`) |
| The two filters are shared with the vault-note snapshot print profile through `RenderFilters` | `create.rs:238`, `create.rs:1368`; snapshot render in `note_snapshot/profile.rs:92` |
| No filter touches fenced code blocks for diagrams; `CodeBlock` is passed through (return-links) or only FE0F-stripped (snapshot) | `return_links.lua:111`, `note_snapshot/note.lua:511` |
| SVG image embeds in vault snapshots already degrade to an "Image not printable" placeholder, because XeLaTeX can't include SVG | `note_snapshot/assets.rs:49`, `note_snapshot/serialize.rs:457`, `docs/highlights-create.md:87-91` |
| Markdown `--dry-run` is documented to return **before** pandoc/XeLaTeX run | `docs/highlights-create.md:283` |
| Bob already ships a pinned **uv + Playwright** adapter that drives Chrome, injects a **vendored JS bundle** (Defuddle) into an **offline** page (`page.route("**/*", abort)`), and prints PDFs | `scripts/web_clip/web_clip_adapter.py:936-943`, embedded via `src/scripts.rs:72-104`, invoked as `uv run --script` from `clip_adapter.rs:92` |
| That adapter has a JSON op table (`ping`, `capture`, `compose`) where a new op slots in additively | `web_clip_adapter.py:1866` |
| Bob already works around Chrome's Unix-socket path limit: `ScratchDir` ignores a `TMPDIR` longer than 40 bytes, and the adapter points `TMPDIR` at the short workdir before launching Chrome | `workdir.rs:32-46`, `web_clip_adapter.py:1327` |

### Where the demand actually is

- **Vault:** `grep` over `~/bob` finds **0** Mermaid fences. The vault-note snapshot route
  is not where the pain is today.
- **Agent reports:** the screenshot is a SASE research report: Markdown outside the vault,
  rendered with `bob ref create report.md -P sase`. These reports increasingly use
  flowcharts, sequence diagrams, and state diagrams.
- **Conclusion:** the plain-Markdown route is the priority. Since both routes share
  `RenderFilters`, covering the snapshot route costs almost nothing extra (§6, R1).

### Host toolchains (checked 2026-10-17)

| | athena (Linux) | mac (macOS 26.5) |
| --- | --- | --- |
| pandoc | 3.1.11.1 | 3.11 |
| xelatex | yes | yes (BasicTeX) |
| `mmdc` (mermaid-cli) | 11.4.2 (bundles mermaid 11.6.0), global npm | **not installed** |
| Node / npm | v22 via nvm | Homebrew |
| uv | yes | yes |
| Chrome | `/opt/google/chrome/chrome` (155) + Playwright Chromium | Google Chrome.app |
| rsvg-convert / inkscape | yes / yes | rsvg-convert only |

Every renderer option except "Bob-owned browser adapter" and "native Rust" adds a new
install step on at least one host.

## 2. Is this a good idea? (critique)

**For:**

1. Mermaid in agent output is a picture by intent. All three common preview surfaces
   render it, so the author never saw source.
2. In Highlights, the source is actively worse than nothing. It takes a page, it's
   unhighlightable in any useful sense, and `--listen` narrates it as punctuation soup.
3. Bob already owns the hard parts: browser discovery, offline isolation, the
   TMPDIR/socket workaround, process-tree kill, and a pinned Python env. The marginal
   cost is moderate (§7).

**Against / risks (none fatal, but they shape the design):**

1. **A browser enters a previously browser-free route.** The Markdown route needs only
   pandoc + XeLaTeX today. Mitigation: launch only when a Mermaid fence exists, and treat
   a missing renderer as a warning with the current output, never a failure.
2. **Wide diagrams get small.** A portrait page with 0.85in margins leaves 489.6 pt of
   text width. The screenshot's `flowchart LR` renders 1196–1460 px wide, so its text
   lands at **≈5.4–6.6 pt** against a 10 pt body. It's vector, so it zooms crisply in
   Highlights, but it's small at 100%. This is a property of the content, not the
   renderer: all engines hit it.
3. **Version drift.** GitHub, Obsidian, and Bob will each run a different Mermaid.
   Syntax newer than Bob's pinned bundle (e.g. new `*-beta` diagram types) will fail and
   fall back to source. Mermaid also shipped real security fixes in 2026 (v11.15.0: a
   gantt DoS and CSS-related CVEs, backported to 10.9.6). So the pin needs occasional
   bumps, and rendering needs a timeout.
4. **Binary size.** `mermaid.min.js` 12.2.0 is **5.5 MB** (11.6.0 was 2.7 MB). Bob is
   36 MB today. Compressed it is 1.2 MB (xz) / 1.25 MB (zstd) / 1.57 MB (gzip).
5. **Annotation semantics.** Highlights on diagram text work (the text is real, selectable
   text; see §4), but they read as fragments ("Green?", "no"). That's acceptable; it's
   still far better than source.

**Would I take a different approach than "make `bob ref create` render Mermaid"?** I
considered three:

- **Fix it upstream:** have agents emit images instead of Mermaid. Rejected. The Mermaid
  source is the right artifact for GitHub, Obsidian, and diffs.
- **Switch the whole Markdown route to HTML → Chrome print**, where Mermaid would render
  natively. Rejected. It throws away return links, numbered TOC, Bob's LaTeX macros, and
  the shared snapshot profile for one feature.
- **Fix it in bob, with small upstream nudges (my pick).** Fix in bob, and separately
  nudge report-writing prompts toward `flowchart TD` and short labels. The nudge is a
  cheap complement for the wide-diagram problem, not a substitute.

## 3. Options evaluated

| # | Option | Fidelity | New host deps | Speed (6 diagrams) | Robustness observed | Verdict |
| - | --- | --- | --- | --- | --- | --- |
| A | **pandoc-ext/diagram** Lua filter → `mmdc` per block | Reference (mermaid.js) | `mmdc` on every host (missing on mac) + its Puppeteer Chrome | ~1.8 s **per diagram** (new Chrome each) | Failed twice out of the box on athena (below) | Good 1-hour spike, poor durable design |
| B | Bob shells out to `mmdc` itself (or its Markdown batch mode) | Reference | Same as A | One launch in batch mode | Same Puppeteer/Chrome/TMPDIR fragility; version = whatever npm installed | Not recommended |
| C | **Vendored `mermaid.min.js` in Bob's Playwright adapter** | Reference, **pinned** | None beyond web-clip's (uv + Chrome) | **1.6 s** (11.6.0) / **2.5 s** (12.2.0) total | Worked; per-diagram parse errors isolated | **Recommended** |
| D | **mmdr** (`mermaid-rs-renderer` 0.3.1, pure Rust) → SVG → PDF | Approximate (reimplementation) | None (crate) | Milliseconds | Layout/semantic gaps (below) | Watch; possible future backend |
| E | Kroki / mermaid.ink web service | Reference | Network | Network-bound | Sends vault/research text to a third party | Rejected (privacy, offline) |
| F | HTML → Chrome print for whole Markdown route | Native | Browser always | n/a | Loses LaTeX features | Rejected (scope) |
| G | Leave as source / upstream-only fix | n/a | none | n/a | Status quo | Rejected as the main fix; nudge is complementary |

### Option A/B: what went wrong with `mmdc` on athena

1. `mmdc -i d.mmd -o d.pdf --pdfFit` failed: Puppeteer could not find its pinned
   **Chrome 131.0.6778.204**. Fixed only by writing a `-p puppeteer.json` with
   `executablePath`.
2. With that fixed, Chrome died: `FATAL … Socket path too long: <SASE agent TMPDIR>/…/SingletonSocket`.
   The agent TMPDIR is 76 characters; the Unix socket path limit is ~104–108 bytes.
   Fixed only with `TMPDIR=/tmp`. Bob's adapter already solves exactly this (§1). Raw
   `mmdc` and pandoc-ext/diagram's `pandoc.pipe` do not.
3. When working, ~1.8 s per diagram, because each call starts a new Chrome. The output
   was good: a vector PDF with an embedded TrueType font and extractable text.
4. pandoc-ext/diagram itself (last commit 2025-10-27) needs pandoc ≥ 3.0 and calls
   `mmdc --pdfFit --input … --output …`. Its README warns against untrusted documents,
   because document metadata can set the engine `execpath`. Bob would have to pin the
   metadata via defaults to be safe.

### Option D: mmdr fidelity, measured

Built from `1jehuang/mermaid-rs-renderer` @ `3726ccb` (2026-09-06, v0.3.1, 546 commits
since Jan 2026). Build took 40 s. The README still says "active early development…
may not yet match mermaid-cli". It claims 23 diagram types. On my five test diagrams:

- **Screenshot flowchart (LR, two disconnected chains):** mmdr lays the chains **side by
  side**, giving a 1868 × 154 pt image. mermaid.js stacks them (≈897 × 233 pt). In a
  489.6 pt column, mmdr's text would print at **≈3 pt**, which is unreadable.
- **Sequence diagram:** layout is close, but the `alt` frame swallows the trailing
  `Note over`, a semantic error.
- **Gantt:** legible but restyled; sizing differs a lot.
- **Subgraph flowchart (TD):** good.

It's attractive for a Rust CLI (no browser; it could feed the `svg2pdf` crate). But the
first diagram I tried, the one in your screenshot, came out unusable. Revisit once it
reaches 1.0, behind the same interface (§7).

## 4. Prototype of the recommended path (Option C)

Scripts are kept outside the repo (`/tmp/mmd_scripts/`). Pipeline:

1. **Collect.** `pandoc report.md -t json --lua-filter collect.lua` writes a manifest of
   `{sha1, text}` for every `CodeBlock` with class `mermaid`. The key is
   `pandoc.utils.sha1(cb.text)`. Cost: **27 ms**. Pandoc's own parse is the source of
   truth, so fences inside lists or quotes, `~~~` fences, CRLF and similar cases need no
   Rust re-parser.
2. **Render.** One `uv run --script` Playwright process launches Chrome once, sets an
   offline page, injects `mermaid.min.js` via `add_script_tag`, and calls
   `mermaid.initialize({startOnLoad:false, securityLevel:'strict', theme:'neutral',
   fontFamily:…, <diagram>.useMaxWidth:false})`. For each diagram it then runs
   `mermaid.render()`, measures the SVG box, and calls
   `page.pdf(width=w px, height=h px)`.
3. **Swap.** In the main render, a Lua filter replaces each Mermaid `CodeBlock` with
   `Para{Image("diagrams/<sha1>.pdf")}` when the file exists. Otherwise it leaves the
   block untouched.

Results:

| Check | Result |
| --- | --- |
| 5 valid diagrams + 1 broken, mermaid 11.6.0 | 5 PDFs + 1 isolated `Parse error on line 4`, **1.62 s** total including browser launch |
| Same with mermaid **12.2.0** (current npm `latest`) | Same outcome, **2.53 s**; 12.x wraps long labels by default, so the LR screenshot diagram narrows from 1460 → 1196 px |
| Full XeLaTeX render with DejaVu fonts (athena, pandoc 3.1.11.1) | Diagrams typeset as vector art; the broken diagram stays as source; `pdftotext` finds "Agent finishes its work", "enqueue PR" |
| Same filter on the **Mac** (pandoc 3.11) | **Identical sha1 keys** across hosts and pandoc versions; images emitted inside `\pandocbounded{…}` (scale-down-only bounding) |
| Font embedding: Inter woff2 (variable) or Inter OTF (CFF) | Chrome/Skia emits **Type 3** fonts |
| Font embedding: **DejaVu Sans TTF** | **CID TrueType**, Unicode-mapped, matches the route's `sansfont` |
| Run under the 76-char SASE agent TMPDIR without Bob's workaround | Chrome FATAL socket-path error, confirming that reusing Bob's adapter matters |
| Bob's real web-clip adapter under the same TMPDIR (`bob ref create https://example.com/ -d -P sase`) | Works (`capture: chrome 155 · headless`), thanks to `workdir.rs`/`TMPDIR=workdir` |

Visual notes:

- The `neutral` theme reads well next to DejaVu Serif body text and stays out of the way
  of Highlights' colored highlights. Mermaid's default theme uses lavender nodes and
  **yellow notes**, which clash with a yellow highlight.
- With 11.6.0 `neutral`, sequence-diagram notes rendered as dark gray boxes with white
  text, so override `noteBkgColor` / `noteTextColor` in `themeVariables`.

## 5. Design details for the recommended path

**Output format: vector PDF, not PNG or SVG.**

- SVG can't go through XeLaTeX without extra tooling (`svg` package + Inkscape).
- Converting SVG with `rsvg-convert` drops Mermaid's `<foreignObject>` HTML labels: the
  `mmdc` SVG of the screenshot diagram contained 32 `foreignObject` tags.
- PNG loses crisp zoom and selectable text.
- Chrome's `page.pdf` output keeps both.

**Sizing.**

- Use `useMaxWidth:false` so each PDF has its natural size, and let pandoc's template
  scale it down only (`\pandocbounded` on 3.11; `\maxwidth`/`\maxheight` on 3.1.x).
- Optional: set Mermaid `fontSize` ≈ 13.3 px (= 10 pt) so diagrams that fit match the
  body text size.
- v1 accepts that wide diagrams shrink. Consider a warning when the effective scale drops
  below ~0.5. A landscape-page policy is a v2 question.

**Fonts and theme.**

- Use a TTF so Chrome embeds the font as CID TrueType. DejaVu Sans is already a
  documented prerequisite of this route; bundle a copy if host independence matters.
- Pin `theme: neutral` plus a few `themeVariables`.
- Never read per-document Mermaid config for engine or paths. Mermaid's own `%%{init}%%`
  directives stay subject to `securityLevel:'strict'`.

**Security.**

- Offline page with every request aborted, the pattern already at
  `web_clip_adapter.py:936`.
- `securityLevel:'strict'`: HTML labels sanitized, click handlers disabled.
- No document-controlled executables.
- A per-diagram timeout (e.g. 10 s) and a total timeout, because Mermaid has had DoS
  CVEs.

**Failure policy (never fatal).**

- Per diagram: keep the source `CodeBlock`, add a one-line italic note above it
  ("Mermaid diagram not rendered: Parse error on line 4"), and print a CLI warning.
- Renderer unavailable (no uv, no browser, adapter crash): print one warning, and every
  block stays as today.
- Exit code unchanged.

**Dry run.**

- Keep the documented contract: no pandoc, no browser.
- A Rust fence scan gives an approximate count:
  `diagrams: 3 mermaid (rendered at create time; see bob ref doctor)`.

**Doctor.**

- A warning-level row, like `pandoc`/`xelatex` today:
  `mermaid: ok (bundled mermaid 12.2.0; browser chrome 155)` or
  `mermaid: warn (no browser; diagrams will print as source)`.

**Interplay with existing features.**

- **Return links:** Image/Figure targets are already "untagged" (`docs/highlights-create.md:337`). No
  change.
- **Code-break filter:** touches only inline `Code`. No change.
- **Snapshot route:** `note.lua` reprocesses `Para` inlines (`process_inlines`), so either
  run the swap **after** `note.lua` or emit the image in a form `note.lua` passes through.
  Verify with a fixture.
- **`--listen`:** narration will now read diagram labels instead of source. That's
  better, but still noisy; tagging diagrams for listen to skip is a follow-up.
- **`BOB_HIGHLIGHTS_KEEP_WORKDIR=1`:** also keeps `diagrams/` plus the manifest for
  debugging.

**Caching.** Not needed in v1: each create runs once, and a whole document costs about
2–3 s. Content-addressed file names (`<sha1>.pdf`) make a later cache trivial.

## 6. Requirement adjustments (explicitly called out)

| # | Adjustment | Why |
| - | --- | --- |
| **R1** | Cover **both** Markdown routes (plain `.md` and vault-note snapshots, incl. `-M`), not only the screenshot's route | They share `RenderFilters`; the cost is a fixture; Obsidian users expect Mermaid to work |
| **R2** | **Degrade, never fail.** No renderer or a bad diagram means today's code block + a visible note + a warning, exit 0 | A diagram must never block importing a report; this matches the "Image not printable" convention |
| **R3** | Output **vector PDF** diagrams, not PNG/SVG | Zoom-crisp text, selectable for highlights, XeLaTeX-native |
| **R4** | **Deterministic, host-independent rendering:** a Mermaid bundle pinned in bob, a fixed TTF font, a fixed theme. Never "whatever `mmdc` is on PATH" | athena and mac would otherwise differ (one has no `mmdc`); a reproducible PDF matters for annotations |
| **R5** | The **diagram replaces the source** by default, with no source appendix and **no new CLI flag in v1**; offer an env kill switch (e.g. `BOB_HIGHLIGHTS_DIAGRAMS=off`) | Avoids flag sprawl; cli_rules would require a short alias, and `create` already uses `A C a f H i L M N n o P p S s T t` |
| **R6** | **Dry run stays browser-free** and only counts diagrams | Preserves the documented dry-run contract |
| **R7** | **Out of scope for v1:** other diagram languages (dot/PlantUML/D2), SVG image embeds, landscape pages for wide diagrams, listen-skip of diagrams | Keep v1 small; the adapter op is shaped to admit them later |

## 7. Risks and open questions

- **Bundle version policy.** Pin 12.2.0 (current npm `latest`; MIT; `dist/mermaid.min.js`
  sha256 `a8a6a6f805b074a8261a2825c86f99c8054acb3b35f50bb7e24a4f9f2c3c3b9f`), or the
  last 11.x for parity with GitHub? I lean 12.2.0, because agents write current syntax.
  Bumping is a one-file vendor update recorded in `vendor/README.md`, like Defuddle.
- **Embedding 5.5 MB.** The simplest option is raw `include_bytes!` (+15% binary). The
  alternative is xz/zstd compression with a decoder crate. I'd embed raw unless binary
  size is a stated concern.
- **Highlights selection inside an included-PDF Form XObject.** `pdftotext` extracts the
  text, and PDFKit normally selects it too. Verify on the Mac during acceptance.
- **Wide diagrams.** If 5–6 pt diagram text proves annoying in practice, the next step is
  a landscape page (`pdflscape`) for diagrams whose scale would drop below ~0.5. Those
  pages display landscape in viewers, which suits a laptop screen.
- **Renderer abstraction.** Keep a narrow internal interface ("render these
  `{id, engine, source}` items to PDFs"), so mmdr (+ `svg2pdf`) can replace the browser
  later without touching the Lua or LaTeX side.

## 8. Recommended solution

**Build Option C: vendored, pinned Mermaid rendered by Bob's existing headless-Chrome
adapter, batch-rendered once per document into vector PDFs, then swapped into the pandoc
AST by a shared Lua filter, with a graceful fallback to today's output.**

Implementation outline (v1):

1. **Vendor Mermaid.** Add `scripts/web_clip/vendor/mermaid.min.js` (12.2.0, sha256
   above, MIT license file, README entry). Embed it through `SUPPORT_ASSETS` in
   `src/scripts.rs`, next to Defuddle.
2. **Adapter op `diagrams`** (additive, protocol 1):
   - **Request:**
     `{workdir, font_path, items:[{id, engine:"mermaid", source}], timeout_s}`.
   - **Response:** `{results:[{id, ok, pdf, width_pt, height_pt, error}]}`.
   - **Behavior:** reuse `discover_browser()`, `_launch_with_fallback`, the
     `TMPDIR=workdir` trick, and the offline `route(abort)` page. Launch one browser and
     render all items with `securityLevel:'strict'`, `theme:'neutral'`, and
     `useMaxWidth:false`. Write a fitted `page.pdf` per item, with a per-item timeout.
3. **Rust `diagrams` module** in `highlights_ref`:
   - Run the collect pass (pandoc JSON + collect filter, or a walk of
     `pandoc -t json` output).
   - When at least one Mermaid block exists, call the adapter through the existing
     `clip_adapter` plumbing.
   - Write `<scratch>/diagrams/<sha1>.pdf`, print `rendering N Mermaid diagram(s)…`, and
     turn per-item failures into warnings.
   - Pass the diagram directory to pandoc as metadata, like the return-links report path.
4. **Lua swap filter** (`diagrams.lua`, `include_str!`) added to `RenderFilters`:
   - Plain route: before the code-break filter.
   - Snapshot route: placed so `note.lua` doesn't rewrite it.
   - Rendered block: `Para{Image(pdf)}`, left to pandoc's `\pandocbounded` /
     `\maxwidth` scaling.
   - Failed block: a note `Para` + the original `CodeBlock`.
5. **Dry run and doctor.**
   - Dry run: an approximate fence count line, with no browser.
   - Doctor: a warning-level `mermaid` row with the bundled version and browser
     readiness.
6. **Docs.** In `docs/highlights-create.md`: a "Diagrams" subsection, a prerequisites
   row ("Markdown with Mermaid: uv + a browser, optional; without them diagrams print as
   source"), the dry-run table, and env vars (kill switch, adapter override test seam).
7. **Tests:**
   - Lua unit tests for swap and fallback, against fake PDFs.
   - Rust tests with a stub adapter (existing override seam).
   - Adapter self-tests for the new op.
   - One gated integration test (skips without uv/Chrome/xelatex). It renders a report
     containing the screenshot diagram, asserts that `pdftotext` contains
     "Agent finishes its work" and **not** "flowchart LR", and asserts that a broken
     fence survives as source with exit 0.

Acceptance (v1):

1. The screenshot's report renders its diagrams on **both athena and the Mac**.
2. A malformed diagram prints as source with a note and a warning, and exit status is
   unchanged.
3. With no browser available, all diagrams print as source with one warning.
4. `--dry-run` launches no browser and still ends `writes: none`.
5. Text inside a rendered diagram is selectable and highlightable in Highlights (manual
   check on the Mac).

Follow-ups, each separable:

- Reuse the same adapter op to fix SVG image embeds that today print "Image not
  printable".
- A landscape policy for very wide diagrams.
- A listen-skip marker for diagrams.
- Optional dot/D2 engines.
- Re-evaluate mmdr as a browser-free backend once it reaches 1.0.
- A one-line nudge in research-report prompts to prefer `flowchart TD` and short labels.

If you want relief **today**, before any of this lands: on athena, run pandoc-ext/diagram
by hand with `mmdc`, a `-p` Puppeteer config pointing at `/opt/google/chrome/chrome`, and
`TMPDIR=/tmp`. Treat it as a stopgap, not the design.

## Sources

- Local code: bob-cli `master` @ `30bdfb8` (files and lines cited inline).
- pandoc-ext/diagram, local checkout @ `5aaf35e` (2025-10-27): README "Security" section
  and `_extensions/diagram/diagram.lua` Mermaid engine.
- mermaid-rs-renderer (mmdr), local checkout @ `3726ccb` (2026-09-06, v0.3.1): README
  and Cargo features; built and run locally.
- mermaid-cli, local checkout @ `f416ac5` (12.0.0 tagged 2026-09-24; depends on
  `mermaid ^12.0.0`, `puppeteer ^25`).
- npm registry: `npm view mermaid dist-tags` → `latest: 12.2.0`; `npm pack mermaid@12.2.0`
  (inspected `dist/mermaid.min.js`, 5,494,801 bytes).
- Mermaid security fixes (v11.15.0 gantt DoS / CSS CVEs, backported to 10.9.6):
  [newreleases.io — mermaid 10.9.6](https://newreleases.io/project/npm/mermaid/release/10.9.6).
- Zettlr's unsupported `pandoc.pipe` + `mmdc` example:
  [Zettlr docs — Mermaid](https://docs.zettlr.com/en/scientific-technical/mermaid/).
- mmdr announcement and claims:
  [Show HN: Mmdr](https://news.ycombinator.com/item?id=46885868),
  [docs.rs mermaid_rs_renderer](https://docs.rs/mermaid-rs-renderer).
- Experiments: athena and mac (via tailnet SSH), 2026-10-17; artifacts in
  `/tmp/mmd_proto/` (not committed).
