# Mermaid diagrams in `bob ref create` PDFs: consolidated recommendation

- **Date:** 2026-10-17
- **Lead researcher:** consolidation of four independent reports (`__cdx`, `__cld`, `__grk`,
  `__gem` in this directory), plus new lead spikes on athena.
- **Code inspected:** bob-cli `master` @ `30bdfb8`.
- **Spike artifacts:** `ref_create_mermaid_figures__final_assets/` (render script, collect and
  swap Lua filters, page images). No production code or vault content was changed.
- **Reading of the request:** "does convert mermaid syntax well" is read as "does **not**".
  The screenshot shows `flowchart LR` printed as wrapped source, with literal `<br/>`.

## Verdict

- **Build it.** All five researchers agree that this is a good feature. It is a missing
  feature, not a regression.
  - Mermaid in agent-written reports is meant to be a picture: GitHub, Obsidian, and VS Code
    all render it.
  - Printed as source, it wastes pages, can't usefully be highlighted, and `--listen` narrates
    it as punctuation.
- **Recommended shape:**
  - Render explicit Mermaid code blocks into **fitted vector PDFs**, using a **pinned Mermaid
    bundle vendored in bob**.
  - Run the bundle inside **Bob's existing Playwright/Chrome adapter** (the one web capture
    already uses), with **one browser launch per document**.
  - Swap the PDFs into the **unchanged pandoc → XeLaTeX pipeline** with a small Lua filter
    shared by both Markdown routes.
  - When a diagram can't be rendered, keep its source and add a **visible note**, so the
    report still imports.
- **Rejected:**
  - Host `mmdc` (grk's pick).
  - The pure-Rust `mmdr` renderer (gem's pick).
  - PNG or SVG intermediates.
  - Printing the whole document through Chromium.
  - Hosted renderers such as Kroki or mermaid.ink.
- **Most important adjustments** to the request, detailed below:
  - Failures degrade visibly; they never abort the import.
  - The diagram font must be a static TTF, so Highlights text stays clean.
  - Wide diagrams scale down honestly rather than being rewritten.
  - No new CLI flag.

## What happens today

- **Generic Markdown route.** `render_temp_pdf` (`src/native/highlights_ref/create.rs:3224`)
  makes one pandoc call:
  - Flags: `--pdf-engine=xelatex --toc --number-sections`, DejaVu fonts, and the
    `code_break` then `return_links` Lua filters.
  - It uses pandoc's default Markdown reader.
  - A ` ```mermaid ` fence becomes an ordinary `CodeBlock`. The `fvextra`
    `breaklines,breakanywhere` header wraps it, which is exactly what the screenshot shows.
- **Vault-note snapshot route.** `render_note_pdf` (`note_snapshot/profile.rs:150`) differs
  in three ways:
  - It reads with `-f commonmark_x-tex_math_dollars-emoji`.
  - It adds `note.lua`.
  - It writes `.tex` with `cwd = scratch`, then runs XeLaTeX separately.
- No filter in either route knows about Mermaid. `src/` never mentions it.
- **Demand sits in research reports, not vault notes:**
  - grk counted 139 fences in 91 `sase--research` files and 44 fences in 36
    `bob-cli--research` files. I recount 38 files in this repo, including today's reports.
  - The vault has 0 fences.
  - The screenshot's report (`merge_queue_fence_reassessment_explained`) alone has 12.
- **The main caller is unattended.** `~/.config/sase/sase.yml` runs
  `bob ref create --include-id -P "$SASE_FILE_HOOK_PROJECT"` as the `research-highlights`
  file hook on every research commit. This fact decides the failure policy below.

## Is this a good idea? Critique

**For:**

- Mermaid is the right authoring language for agents and diffs.
- Bob already owns the hard parts:
  - Chrome discovery, including `BOB_CHROME`.
  - An offline page that aborts every request (`web_clip_adapter.py:936`).
  - A pinned Python environment via `uv run --script` (Playwright 1.62.0).
  - Embedded vendor assets (`src/scripts.rs`, next to Defuddle).
  - A deadline that kills the whole adapter process group (`clip_adapter.rs:172-219`).
  - The Chrome socket-path workaround: `ScratchDir` plus `TMPDIR=workdir`
    (`workdir.rs:29-46`, `web_clip_adapter.py:1327`).

**Risks (none fatal; they shape the design):**

1. **A browser enters a route that was browser-free.** Mitigation: launch it only when a
   Mermaid block exists, and degrade when it is missing.
2. **Wide diagrams get small.** The screenshot's first chart is 897 × 234 pt at natural size,
   against 489.6 pt of text width. That is a ×0.55 scale, so labels print at about 6.5 pt
   against 10 pt body text. The text is vector and zooms crisply, but it is small at 100%.
   Every engine hits this; it is a property of the content.
3. **Version drift.** GitHub, Obsidian, and Bob will each run a different Mermaid. The pin
   needs occasional bumps.
4. **Binary size.** `mermaid.min.js` 12.2.0 is 5.5 MB (1.18 MB with xz). Bob's binary is
   36 MB today.

**Would I take a different approach?** I considered three alternatives:

- **Have agents emit images instead.** Rejected: the Mermaid source is the right artifact
  for GitHub, Obsidian, and diffs.
- **Print the whole Markdown document through Chromium,** where Mermaid renders natively.
  Rejected:
  - It throws away the numbered TOC, return links, the LaTeX macros, and the shared
    snapshot profile.
  - Prior research (`area_project_note_reading_pdfs`) measured 5.4% damaged quotes in Mac
    Highlights for Chrome PDFs with Type 3 fonts. Pandoc + XeLaTeX scored 0.19%.
- **Add one cheap complement:** nudge the research-report prompts (`sase-research-artifacts`,
  a separate repo) toward `flowchart TD` and short labels. This eases the small-diagram
  problem, but it does not substitute for rendering.

## Where the reports disagreed, and how I resolved each point

| Question | cdx | cld | grk | gem | Resolution |
| --- | --- | --- | --- | --- | --- |
| Renderer | Vendored Mermaid in Playwright | Same | Host `mmdc` | `mmdr` (Rust) | **Vendored Mermaid in Playwright** |
| Output format | Vector PDF | Vector PDF | `mmdc` PDF | 2× PNG | **Vector PDF, no raster effects** |
| On failure | Abort before install | Degrade + note | Degrade | Degrade | **Degrade, visibly** |
| Finding blocks | Rust over pandoc JSON | pandoc collect + Lua swap | Rust fence rewrite | Rust text rewrite | **pandoc collect + Lua swap, Rust orchestration** |
| Opt-out | `text` fence | Env kill switch | None | `--no-mermaid` + config | **Env kill switch only** |
| Mermaid pin | Maintained release | 12.2.0 | Host version | n/a | **Newest 12.x that passes fixtures** |

### Renderer

**Rejecting `mmdc` (grk).**

- It is not installed on the Mac.
- The current `@mermaid-js/mermaid-cli` 12.0.0 needs Node ≥ 22.13.0.
- On athena, three researchers watched it fail out of the box:
  - Puppeteer wanted its own pinned Chrome 131, which was missing.
  - With system Chrome, Chrome died with `Socket path too long` under the SASE `TMPDIR`.
- It launches Chrome once per diagram, about 2 s each. For the 12-diagram screenshot report
  that is about 24 s; the adapter takes about 2–3 s per document.
- The code it saves is small. Fence collection, swapping, warnings, doctor, dry-run, and
  tests are identical either way. Only the render backend differs.

**Rejecting `mmdr` (gem).** gem called it mature but did not test its fidelity. I built
`mermaid-rs-renderer` 0.3.1 from crates.io (2 min 10 s):

- It is fast: 46–356 ms per diagram.
- It lays the screenshot's two disconnected chains **side by side**: 2491 px versus 1196 px
  from mermaid.js. That works out to labels of about **3 pt** on the page.
  - Compare `spike_mmdr_flowchart.png` with `spike_mermaidjs_flowchart.png` in the assets
    directory.
  - This independently confirms cld's measurement (1868 × 154 pt).
- cld also found a sequence-diagram `alt` frame swallowing a trailing note.
- Its README still says "active early development".
- It outputs only SVG or PNG. gem's PNG plan would remove selectable text from diagrams.

### Failure policy

cdx argued for aborting before installation. I side with the other three: **degrade, but
never silently**.

- The dominant caller is the unattended file hook. Aborting would drop an entire 17-page
  report because of one agent's typo, in a file Bryan didn't write.
- cdx's real concern is a "successful" PDF that quietly prints source. Three things meet it:
  - a visible italic note in the PDF above each failed block,
  - a stderr warning,
  - a doctor row.
- A strict mode can wait until there is demand.

### Finding blocks

grk and gem rewrite Markdown text with a Rust fence walker. That breaks on fences inside
lists and blockquotes, on `{.mermaid}` attribute syntax, and on the two routes' different
readers.

Letting pandoc do the parse avoids all of that:

- My spike collect pass took **26 ms** on pandoc 3.1.11.1, using `pandoc.utils.sha1` keys
  and `pandoc.json`.
- It correctly handled a `~~~ {.mermaid}` fence.
- The main pandoc invocation stays unchanged apart from one extra filter.
- The diagram PDFs use absolute scratch paths, so `--resource-path` is untouched.

Following cdx, Rust (not Lua) orchestrates the browser, reusing the supervised transport.

### Filter order on the snapshot route

cld worried that `note.lua` would rewrite the swapped image. I checked: `note.lua` already
centers any `Para` that holds a single `Image` (`note.lua:416-430`). It also keeps the
`Image` as pandoc AST between fixed TeX wrappers (`note.lua:343`).

Running the swap **first** in both routes therefore gives snapshot diagrams the house image
treatment for free. `return_links.lua:115` already treats images as non-targets.

### Mermaid pin

Agents write current syntax, so pin 12.x:

- 12.2.0 is npm `latest`, published about 2026-10-13. It is four days old, so the fixtures
  decide; it is not taken on faith.
- I confirmed cld's sha256 (`a8a6a6f8…c3b9f`).
- The bundle contains zero `import(` calls. It is self-contained, with no lazy chunks to
  package.
- 12.x wraps long labels by default, which narrows LR charts (cld measured 1460 → 1196 px).

## Evidence

All runs were on athena unless noted. Single runs, not benchmarks.

| Probe | Source | Result |
| --- | --- | --- |
| Plain pandoc → XeLaTeX | cdx | Mermaid source printed (reproduces the screenshot) |
| `mmdc` SVG → `rsvg-convert` | cdx, cld | Labels vanish (`foreignObject` HTML labels) |
| Host `mmdc` 11.4.2 | cld, grk, gem | Works only with a Puppeteer `executablePath` and a short `TMPDIR`; ~1.8–2.5 s per diagram (5.8 s in gem's PDF run) |
| Vendored Mermaid, one Playwright browser | cdx, cld, lead | 1.6–2.5 s for 5–6 diagrams (cld); lead: 2.2–3.2 s including `uv` and Chrome start for 4 good + 1 bad; 88–498 ms per diagram |
| Parse error | cld, lead | Isolated to its own item (`Parse error on line 4`); the other diagrams still render |
| Font: variable woff2 or CFF OTF | cld | Chrome embeds **Type 3** (bad for Highlights) |
| Font: static DejaVu Sans TTF from a `data:` URL, every request aborted | lead | **CID TrueType, Identity-H, ToUnicode**; 0 network requests attempted; curly quotes extract |
| Mermaid 12.2.0 `neutral` theme | lead | Skia rasterizes node drop shadows into 12–18 small 300-ppi image+mask patches per diagram |
| Same, with `themeCSS: '* { filter: none !important; }'` | lead | 0 rasters; flowchart PDF 87 KB → 16 KB; text unchanged |
| Neutral-theme sequence notes | cld, lead | Dark-gray boxes with white text in 11.6 and still in 12.2; override the note colors |
| Lua swap → pandoc 3.1.11.1 / XeLaTeX | cdx, cld, grk, lead | Body stays `xdvipdfmx`; every font is CID TrueType; labels extract; no implicit `Figure N` captions; a failed block falls back to note + source (`spike_xelatex_embed_page.png`) |
| Same filter on Mac pandoc 3.11 | cld | Identical sha1 keys; images bounded scale-down-only (`\pandocbounded`) |
| Snapshot two-step `.tex` → XeLaTeX | cdx | Embedded PDFs work when they live on disk until every pass finishes |
| `mmdr` 0.3.1 | cld, lead | Fast but unfaithful layout (see above); SVG/PNG output only |

## Adjusted requirements (deliberate departures from the request)

**A1. Scope is explicit Mermaid code blocks, as pandoc parses them.**

- That means ` ```mermaid `, `~~~mermaid`, and ` ``` {.mermaid} `, including fences nested
  in lists and quotes.
- Never sniff `graph` or `flowchart` inside untagged fences.
- A ` ```text ` fence remains the way to show source on purpose.

**A2. Cover both Markdown routes with one code path.**

- Cover the generic route and vault-note snapshots, including `-M/--plain`.
- The generic route is the first customer. The snapshot route costs only a fixture, since
  both share `RenderFilters`.
- PDF, PDF-URL, arXiv, and web-article imports are unchanged.

**A3. Degrade per block: never fail, never silent.**

- A failed block keeps its source, gets an italic note ("Mermaid diagram not rendered:
  Parse error on line 4"), and prints one stderr warning.
- If the renderer is unavailable (no `uv`, no browser, adapter crash or timeout), print one
  warning; every block gets the note and keeps its source.
- The exit status is unchanged. This departs from cdx's proposal to abort.

**A4. Diagrams are vector, with selectable text that is safe for Highlights.**

- Use Chrome `page.pdf` with a **static TTF**, never the adapter's variable woff2 fonts, which
  embed as Type 3.
- Disable CSS filters so nothing is rasterized.
- PNG (no text) and SVG (lost labels, and XeLaTeX can't include it) are rejected as print
  inputs.

**A5. Rendering is pinned, local, and deterministic.**

- Mermaid bundle vendored in bob, bundled font, fixed theme.
- Never host `mmdc`, a CDN, or a hosted renderer.
- No network during rendering.
- Add the renderer-owned config keys (theme, `themeCSS`, `themeVariables`, `fontFamily`) to
  Mermaid's `secure` list. That list already protects `securityLevel`, `maxTextSize`, and
  `maxEdges`. With these keys added, a diagram's `%%{init}%%` directive can't restyle or
  unfont the output.

**A6. No CLI flag in v1.**

- `cli_rules` requires a short alias for every public long option, and `create` already uses
  most letters.
- Instead, add one env kill switch (for example `BOB_HIGHLIGHTS_DIAGRAMS=off`) for debugging
  and regressions.
- gem's `--no-mermaid` and its config key are rejected.

**A7. Dry-run stays browser-free; doctor only warns.**

- `--dry-run` keeps its documented contract: no pandoc, no XeLaTeX, no browser. It prints an
  approximate fence count from the Rust pre-scan.
- `bob ref doctor` gains a warn-level `mermaid` row, never a failure.

**A8. Be honest about layout.**

- Scale down only.
- Never rewrite `LR` to `TB`, drop nodes, or paginate a graph.
- Warn when the effective scale drops below about 0.5.
- Landscape pages are a v2 question.

**A9. No backfill.** Do not re-render existing library PDFs automatically, because Bryan's
highlights are attached to those files. Re-importing an old report is a manual, per-report
choice.

**A10. Out of scope for v1:**

- Other diagram languages (PlantUML, Graphviz, D2).
- Fixing SVG image embeds that print "Image not printable".
- A listen-skip marker for diagrams.
- A persistent cache.
- Landscape pages.
- `accTitle`/`accDescr` → alt text.

## Recommended design

```text
Markdown file (generic route) | projected.md (snapshot route)
  -> Rust pre-scan: any fence opener mentioning "mermaid"?  no -> today's path, untouched
  -> pandoc <the route's own reader flags> --lua-filter collect.lua -> manifest {sha1, text}
  -> adapter op "diagrams": one browser, one offline page, N items -> scratch/diagrams/<sha1>.pdf
  -> the route's usual pandoc call, plus diagrams.lua FIRST (metadata: diagram dir + failures)
  -> XeLaTeX, stamping, listen, install: unchanged
```

**Vendored assets** (`scripts/web_clip/vendor/`, embedded through `SUPPORT_ASSETS` in
`src/scripts.rs`):

- `mermaid.min.js`, plus its MIT license and a `vendor/README.md` entry recording the version
  and sha256 (the same pattern as Defuddle).
- A static TTF: DejaVu Sans Book, 760 KB, matching the generic route's `sansfont`. Add Bold
  only if fixtures show synthesized bold looks wrong.
- The binary grows by about 6 MB. Embed raw unless size becomes a stated concern.

**Adapter op `diagrams`.** Put it in a sibling module (for example
`web_clip/diagram_render.py`) registered in the adapter's `OPS` table
(`web_clip_adapter.py:1866`). That reuses `discover_browser`, `_launch_with_fallback`, the
abort-all routing, and `TMPDIR=workdir` without growing the 118 KB adapter.

- **Request:** `{protocol: 1, op: "diagrams", workdir, items: [{id, source}], item_timeout_s}`.
- **Response:** `{ok, mermaid_version, browser, results: [{id, ok, pdf, width_pt, height_pt, error}]}`.
- **Page setup:**
  - Load the font with `@font-face` from a `data:` URL.
  - Await `document.fonts.load(...)` **before** the first render, so label boxes are measured
    with the final font.
  - Call `mermaid.initialize` with:
    - `startOnLoad: false`
    - `securityLevel: 'strict'`
    - `theme: 'neutral'`
    - `fontFamily`
    - `themeVariables` with note-color overrides
    - `themeCSS: '* { filter: none !important; }'`
    - `useMaxWidth: false` for each diagram family
    - the extended `secure` list
- **Per item:**
  1. `mermaid.render`.
  2. Measure the SVG box.
  3. `page.pdf(width, height, print_background=True)`.
  4. Assert exactly one non-empty page.
  5. Enforce the per-item timeout (about 10 s).
  6. Report a parse error as `{ok: false, error}`, not as an op failure.
- **Bounds:** Mermaid's `maxTextSize` and `maxEdges` defaults, plus an item-count cap. The
  whole call runs under the existing transport deadline.

**Rust module `highlights_ref/diagrams.rs`, shared by both routes:**

- **Pre-scan.** A cheap line scan that may over-match, never under-match. Documents without
  Mermaid pay nothing.
- **Kill switch.** The env variable from A6 skips everything.
- **Collect pass.** Run the same pandoc reader flags as the route, with `collect.lua` (see
  `spike_collect_mermaid.lua`).
- **Adapter call.** Go through `clip_adapter`'s transport (deadline, process-group kill) with
  diagram-specific hints, not "check your network".
- **Output.**
  - Print `diagrams: rendered 11 of 12 Mermaid diagram(s)` plus one warning per failure.
  - Write the PDFs under `ScratchDir` and keep them until every XeLaTeX pass finishes.
  - `BOB_HIGHLIGHTS_KEEP_WORKDIR=1` also keeps `diagrams/` and the manifest.

**`diagrams.lua`, first in `RenderFilters` for both routes** (see `spike_swap_mermaid.lua`):

- **Rendered block** → `Para{Image}` with empty alt, keeping the block's identifier.
  - An Image built by a filter never gets an implicit `Figure N` caption.
  - It scales down through pandoc's `\maxwidth` (3.1.x) or `\pandocbounded` (3.2+).
  - On the snapshot route, `note.lua` centers it.
- **Failed block** → an italic note paragraph followed by the original `CodeBlock`.

**Dry-run, doctor, docs:**

- **Dry-run** prints `diagrams: N Mermaid fence(s) (rendered at create time)` and still ends
  `writes: none`.
- **Doctor** extends the adapter `ping` op with the bundled Mermaid version, giving rows like
  `mermaid: ok (bundled 12.2.0 · chrome 155)` or
  `mermaid: warn (no browser; diagrams print as source)`.
- **Docs** (`docs/highlights-create.md`) need four edits:
  - a Prerequisites row ("Markdown with Mermaid: `uv` + a browser, optional"),
  - a Diagrams subsection,
  - the dry-run table,
  - the env-var table.

**Tests:**

- **Lua:**
  - Swap and fallback, using fake PDFs.
  - Filter order in both routes.
  - No captions.
  - The identifier is preserved.
- **Rust:**
  - Pre-scan with backtick, tilde, and `{.mermaid}` fences; fences in lists and quotes;
    nested fences; literal examples inside ` ````markdown `.
  - With a stub adapter (via `BOB_WEB_CLIP_ADAPTER`): success, partial failure, crash, and
    timeout.
  - The kill switch.
  - Dry-run spawns no subprocess.
- **Adapter self-test:** the op's request/response shape and parse-error isolation.
- **One gated live test** (skips without `uv`, Chrome, or XeLaTeX), using the screenshot
  diagram:
  - `pdftotext` contains "Agent finishes its work" and not "flowchart LR".
  - `pdffonts` shows no Type 3.
  - `pdfimages -list` is empty for the flowchart.
  - A broken fence survives as source, and the exit code is 0.
  - A long-`TMPDIR` regression case.
  - Paths with spaces and non-ASCII characters.

**Acceptance:**

1. Recreate `merge_queue_fence_reassessment_explained` (12 fences) into a scratch vault on
   athena **and** on the Mac. Every diagram renders or fails visibly, and body text is
   unchanged.
2. In Mac Highlights:
   - select and highlight label text inside a diagram,
   - copy a body-text quote cleanly (the Type 3 regression check).
3. A malformed diagram gives a note, its source, a warning, and exit 0. With no browser
   available, there is one warning and every diagram prints as source.
4. `--dry-run` launches no browser.
5. The added time is about one browser launch per document (~2–3 s), not per diagram.

## Risks and open questions

- **Small text in wide `LR` charts** (about 6.5 pt for the screenshot's first chart). It is
  zoomable vector. Mitigations: the scale warning, the prompt nudge, and landscape pages in
  v2.
- **Text selection inside an embedded PDF Form XObject in Highlights.** `pdftotext` and
  `pdffonts` look clean, but nobody has tested it on the Mac yet (acceptance 2).
- **Pin freshness.** New Mermaid syntax that the pinned bundle can't parse fails visibly,
  and the fix is a one-file vendor bump. Mermaid has shipped DoS fixes (cld cites 11.15.0);
  the timeouts bound the damage.
- **Listen.**
  - On the generic route, narration of the staged PDF will read diagram labels as fragments.
    That is better than reading source.
  - On the snapshot route, `projected.md` still contains the source. That doesn't matter
    until vault notes use Mermaid.
  - A listen-skip marker is a follow-up.

## Follow-ups (each separable)

- Route SVG image embeds ("Image not printable") through the same adapter op.
- Landscape pages for diagrams whose scale falls below 0.5.
- A listen-skip marker for diagrams.
- A prompt nudge in `sase-research-artifacts` toward `flowchart TD` and short labels.
- Re-evaluate `mmdr` once it matches fixtures. Its SVG uses real `<text>` (0
  `foreignObject`), so `mmdr` plus `svg2pdf` could become a browser-free backend behind the
  same narrow `{id, source} → pdf` interface.
- Optional Graphviz or D2 engines through the same op.

## Recommended solution

Add a shared diagram pass to both Markdown routes of `bob ref create`:

1. A cheap Rust pre-scan gates the feature, so documents without Mermaid pay nothing.
2. A 26 ms pandoc collect pass finds the exact Mermaid code blocks.
3. One supervised call to a new `diagrams` op in Bob's existing Playwright adapter renders
   them all in one offline Chrome page, using a vendored, pinned Mermaid 12.x. It applies
   `securityLevel: 'strict'`, a bundled static TTF, a fixed neutral theme with filters
   disabled, and outputs fitted vector PDFs.
4. A first-position Lua filter swaps each rendered block for a scale-down-only image. Any
   block that fails keeps its source under a visible note.

Everything else stays as it is: pandoc + XeLaTeX typesetting, return links, listen,
stamping, dry-run, and installation. This fixes the screenshot with about one browser launch
per document, keeps the diagram text selectable and Highlights-safe, works on athena and the
Mac without new installs, and never lets one bad diagram block a research report from
importing.

## Sources

- **bob-cli `master` @ `30bdfb8`:**
  - `src/native/highlights_ref/create.rs:3224`
  - `note_snapshot/profile.rs:150-207`
  - `note_snapshot/note.lua:343,416-430`
  - `return_links.lua:115`
  - `scripts/web_clip/web_clip_adapter.py:34-39,936-943,1327,1866`
  - `clip_adapter.rs:90-219`
  - `workdir.rs:29-46`
  - `src/scripts.rs:71-120`
  - `docs/highlights-create.md:206-240`
- **SASE file-hook configuration:** `~/.config/sase/sase.yml` (`research-highlights`).
- **The four researcher reports** in this directory, and their cited upstream checkouts:
  - pandoc-ext/diagram @ `5aaf35e`
  - mermaid-cli @ `f416ac5`
  - mermaid-rs-renderer @ `3726ccb`
- **Prior research:** `202610/area_project_note_reading_pdfs` (Type 3 versus CID TrueType
  quote damage, measured with Mac PDFKit).
- **npm registry, 2026-10-17:**
  - `mermaid` `latest` = 12.2.0 (MIT); `dist/mermaid.min.js` sha256 `a8a6a6f8…c3b9f`.
  - Newest 11.x = 11.17.2.
  - `@mermaid-js/mermaid-cli` `latest` = 12.0.0, `engines.node >=22.13.0`.
- **crates.io:** `mermaid-rs-renderer` 0.3.1, built and run locally.
- **Mermaid documentation:**
  - [configuration schema (`secure`)](https://mermaid.js.org/config/schema-docs/config.html#secure)
  - [security levels](https://mermaid.js.org/config/usage.html#securitylevel)
- **Lead spikes:** athena, 2026-10-17. Tools: pandoc 3.1.11.1, XeTeX (TeX Live 2025), Chrome
  155, Playwright 1.62.0, Mermaid 12.2.0. Scripts and images are in
  `ref_create_mermaid_figures__final_assets/`.
