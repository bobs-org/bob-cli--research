# Tables in `bob ref create` PDFs vs. Highlights selection

Researcher: cld · 2026-10-29 · Highlights 2026.1.2 on macOS 26.5 (25F71)

## Bottom line

**The cause is not bob's table styling.** macOS 26 PDFKit runs a private "document analysis" pass on every page shown in a `PDFView`. It is on by default, and Highlights inherits it. The pass detects tables **visually**. Once it has run, a drag inside a detected table no longer makes a text selection. It makes a private whole-cell "table-cell selection" (`-[PDFSelection isTableCellSelection]`), or nothing. That selection has no usable geometry: its bounds and per-line rects are infinite. Highlights then writes a highlight with all-zero QuadPoints, or no highlight at all. This matches "Highlights tries to select the table cell."

Evidence from Bryan's own session today (`lib/blogs/the_ai_native_sdlc_playbook.pdf`, page 6):

- Bryan worked on that page's table between 04:51 and 05:30 UTC.
- The PDF holds **5 real highlights** on that table and **20 Highlight/Underline annotations with all-zero QuadPoints and a zero rect**.
- Their quad counts (4, 3, 1) match the line counts of table cells.
- The first four attempts worked; from 04:59 on, almost all failed.

No styling of a grid escapes detection. I tested booktabs (today's output), content-aware widths, extra row spacing, hairline row rules, a full grid, Chrome's bordered and zebra-striped `reader.css` table (a tagged PDF), and a CSS-grid "table" with no `<table>` tags. **PDFKit treated all of them as tables.** Only a linear "record" layout (one row becomes a lead-in line followed by its cells as paragraphs or items) reliably gets normal text selection: 22/22 cells and every phrase test in the probe.

**Recommendation:** add a render-time table-layout policy to bob:

- **Prose tables** (any body cell outside the first column with 12 or more words; 68% of Bryan's tables and 89% of all table text) print as **row records**.
- **Data tables** keep a grid, improved with content-aware column widths and hairline row rules. That is a clear readability gain over today, and it saves pages.
- Add a frontmatter or per-table override and a global default, so the policy can be reverted when Apple changes PDFKit.
- Separately, report the PDFKit behavior to the Highlights developer and to Apple. Only they can fix tables in PDFs bob doesn't render, such as arXiv papers.

## 1. How bob renders tables today

| Route | Engine | Table output |
| --- | --- | --- |
| Markdown file (`chat`, default) and `-M` | pandoc → XeLaTeX (`render_temp_pdf_from`, `create.rs`) | pandoc's default `longtable` + `booktabs`: top, mid, and bottom rules only, no row separation. For long rows, column widths come from the dash counts in the pipe-table separator, so `\|---\|---\|` means equal widths. |
| Vault-note snapshot | pandoc → XeLaTeX with `note.tex` / `note.lua` | Same pandoc longtable; `note.lua` passes `Table` through untouched. |
| Web article / collection | Chrome print of reader HTML (`web_clip_render.py`, `template/reader.css`) | Full 0.5pt borders, zebra rows, Inter 8.5pt, `width: 100%`. |

The default widths waste space in Bryan's typical tables. In `athena_root_nvme_wear_and_replacement`, the `Item | Value` table gives "Item" half the width, so values wrap to seven lines. Rows also run together because the inter-row gap equals the line gap. Both are visible in `compare_current.png` in the assets.

## 2. How much this matters (Bryan's corpus)

- **Sources:** 199 of 273 preserved chat sources (73%) contain tables, and tables hold 13.4% of their non-space text.
- **Table kinds:** 996 tables across all preserved sources, classified with `corpus_table_kinds.py`:
  - **Prose tables** (some cell of 12+ words): 673 (68%), holding 89% of table text.
  - **Mixed** (6–11 words): 190 (19%), 8% of table text.
  - **Data tables** (5 words or fewer): 133 (13%), 3% of table text.
  - Most tables have 3 columns (391), then 2 (259), then 4 (204).
- **Annotations:** the 455 XeLaTeX-rendered library PDFs carry 229 highlight-type annotations, 205 of them in PDFs that also contain tables. After hand-checking every geometric "hit," **none** sits in a LaTeX table cell: all were numbered lists that happened to sit between two tables' rules. Bryan annotates "open question" lists heavily (highlight the lead-in, answer in the comment), but effectively never annotates tables. Absence alone doesn't prove difficulty, but it is consistent with the complaint, and the blog page above shows the difficulty directly.
- **Chrome route:** blog PDFs do have successful table highlights (the five above). Section 3 explains why some attempts work.

## 3. What I measured on the Mac

All probes ran on the MacBook (macOS 26.5). Highlights 2026.1.2 links `PDFKit.framework` and calls `selectionFromPoint:toPoint:`, `selectionsByLine`, `characterIndexAtPoint:`, and `selectionFromPage:atCharacterIndex:…`. It also has a manual rectangle tool (`PDFSquareSelectionMode`, `addImageSelectionWithStartPoint:endPoint:`). Its binary contains **no** reference to `documentAnalysis`, `formDetection`, or `tableCell`, so it runs with PDFKit's defaults.

### 3.1 Page-level API without a PDFView: tables are fine

Calling `PDFPage.selection(from:to:)` on bob's current PDF, from the first glyph of each cell to its last glyph, returns exactly that cell's text. With ±8pt pointer jitter, 90% of cell drags are clean (prose: 100%). The misses come from tight row spacing: a drag that ends slightly low catches the next row. Chrome (93%) and the stacked layout (91%) behave about the same. **This is not what Bryan experiences**, because no document analysis runs here.

### 3.2 Inside a real PDFView, PDFKit's private table detection takes over

A background probe app (`cells_probe.swift` in the assets) loads each PDF into an invisible PDFView and waits about 8 s for analysis. It then sends synthesized drags to its own window. PDFKit 26.5 exposes, privately:

- `-[PDFView isDocumentAnalysisEnabled]` (**default YES**) and `isFormDetectionEnabled` (default NO)
- `-[PDFPage tableSelectionFromPoint:toPoint:]`, `selectionForTableRect:`, `detectedForm`, `didPerformFormDetection`
- `-[PDFSelection isTableCellSelection]`, `tableCellSelectionRect`

Results, per variant:

- **Cell drags:** first glyph to last glyph of each whole cell.
- **Phrase drags:** across 3–5 words inside a cell.
- Each cell is counted as text selection / table-cell selection / nothing.

| Rendering | Cell drags: text / table-cell / nothing | Phrase drags |
| --- | --- | --- |
| Today's LaTeX (booktabs) | 0 / 16 / 6 | 0 text (3 cell, 2 nothing) |
| LaTeX + content-aware widths | 5 / 13 / 2 | — |
| LaTeX + widths + row spacing | 3 / 16 / 1 | — |
| LaTeX + widths + hairline rows | 3 / 13 / 4 | — |
| LaTeX full grid | 0 / 18 / 2 | — |
| Chrome, bob `reader.css` (tagged PDF) | 2 / 19 / 1 | 0 text (6 cell) |
| Chrome, CSS-grid divs (no `<table>`) | 1 / 13 / 5 | 0 text (5 cell, 1 nothing) |
| LaTeX hanging-indent key/value | 10 / 5 / 4 | 5 text, 1 cell |
| **LaTeX row records (stacked)** | **22 / 0 / 0** | **7/7 text** |
| Today's LaTeX, analysis **disabled** | 22 / 0 / 0 | 5/5 text |
| Real library PDF (`athena_root_nvme…`) | 3 / 25 / 11 | — |
| Prose controls (all variants) | all text | all text |

Further findings:

- **Whole cells only.** A table-cell selection always covers the entire cell. You cannot select a phrase inside a cell.
- **No geometry.** `bounds(for:)` and every `selectionsByLine()` rect are `{inf, inf, 0, 0}`. A highlight built from them has no geometry, which matches the 20 zero-quad annotations in Bryan's PDF.
- **First column often fails entirely.** Many first-column cells produce nothing at all.
- **Corrupted cell text.** The cell selection's string can also drop characters at line ends (for example "applicable window**retain**", "entir**provider**"), so any text exported from it would be wrong.
- **Public API is hijacked too.** Once analysis has run, the public `PDFPage.selection(from:to:)` and `PDFDocument.selection(from:at:to:at:with:)` return **nil** for 20 of 22 table cells (prose stays clean). An app can't route around this with public API.
- **No workaround in the app.** Option-, Shift-, Command-, and Control-drags don't restore text selection, and neither does the public `isInMarkupMode = true`.
- **Tags are irrelevant.** Detection is visual: Chrome's tagged PDF is detected, and so is the version with no table tags at all.

**Interpretation:** analysis is asynchronous per page, so a table can be selectable for a short while after a page first appears, and not afterwards. That fits Bryan's timeline above, and it fits "it can be hard," rather than "always impossible." The same behavior shows up in the long-running Apple Community thread ["macOS 26 preview does not allow highlighting on much of text"](https://discussions.apple.com/thread/256139925) (463 "me too" votes). Users there report blue boxes, highlighting failures concentrated in tables, Skim affected too, and no fix through 26.5.

**Limits of the harness:** synthesized events in an offscreen PDFView are not Highlights. An earlier, noisier harness gave misleading "clean" scores, because a whole-cell selection's string equals the cell text. I discarded it in favor of the probe above, which records `isTableCellSelection` directly. The zero-quad annotations Bryan created today independently confirm the conclusion.

## 4. Critique of the plan

**Is it a good idea?** Yes: tables carry about 13% of Bryan's reading text, mostly in prose-heavy decision and comparison tables, and they are effectively unannotatable on macOS 26. The premise needs one correction, though. The obvious move is to restyle tables (rules, padding, zebra, a different engine), and **that cannot fix highlighting.** PDFKit classifies anything that looks like a grid as a table. Restyling only helps readability.

**Adjusted requirements** (my changes, called out):

1. **R1, reframed.** Not "render tables so Highlights can select cells," but "render the tables Bryan would annotate in a layout PDFKit won't classify as a table, and keep grids where scanning matters more than annotating."
2. **R2, made testable.** "Don't decrease readability" becomes: no more pages than today, no cramped columns, and rows visually separated. Measured with bob's flags on five real reports, the hybrid is never longer than today: 15→15, 11→11, 12→10, 4→4, 23→22 pages. The improved grid alone is 15/10/10/4/19.
3. **R3, explicit scope.** The generic Markdown route and vault-note snapshots come first; the web-article route is phase 2. Third-party PDFs (arXiv, local PDFs) **cannot** be fixed by bob, so the reader-side report is part of the plan, not optional.
4. **R4, reversible.** Apple may fix or change this in 26.x or 27, so the policy needs a global default plus per-document and per-table overrides. Changing the default must not touch any stored note.
5. **R5, source fidelity.** The preserved `source.md`, Obsidian views, narration, and the code catalog keep the original Markdown table. Only the print changes. The new filter runs **first**, so the render-time code catalog and return-link pairing describe the printed layout (see the `code-copy-reads-render-time-catalog` decision).
6. **R6, no promise of whole-cell highlights in grids.** Under macOS 26, grid cells are not reliably highlightable in any PDF. For the rare data-table annotation, Highlights' rectangle (image) tool is the stopgap.

**Would I take a different approach?** Mostly the same direction, with three emphases:

- Fix the representation, not the style.
- Keep grids for data.
- Pursue the reader-side fix in parallel, because only it covers papers.

A complementary, upstream nudge: SASE research prompts could prefer numbered lists over prose tables for open questions and decisions. Bryan already annotates those lists heavily. That is outside bob, though.

## 5. Options considered

| Option | Highlightable (macOS 26) | Readability | Cost / risk | Verdict |
| --- | --- | --- | --- | --- |
| A. Restyle grids (widths, rules, zebra, full grid) | ✗ (detected as table) | ↑ | Low | Do it for data tables only |
| B. Records for every table | ✓ | ↓ for numeric/data tables | Low | Too blunt |
| **C. Hybrid: records for prose tables, improved grid for data** | ✓ where it matters | ≈ or ↑ (page counts equal or lower) | Medium (one Lua filter plus tests) | **Recommended** |
| D. Hanging-indent key/value (label gutter, value paragraph) | Partial: still classified as a table on some pages | ↑ for 2-column tables | Medium | Rejected (unreliable) |
| E. Switch engine (Chrome/Typst) | ✗ (the Chrome table was detected) | n/a | High | Rejected: detection is visual, not engine-specific |
| F. Tagged PDF or table semantics | ✗ (tagged Chrome PDF still detected) | n/a | High | Rejected |
| G. Table as image | ✗ (no text) | ↓ | Low | Rejected |
| H. Reader-side: Highlights turns off document analysis | ✓ for every PDF | n/a | Outside Bryan's control; private API | Report it; don't block on it |

## 6. Recommended solution

**1. Add a `table_layout.lua` filter**, embedded the same way as `return_links.lua` and `code_catalog.lua`, and run it first in both pandoc→XeLaTeX chains: `render_temp_pdf_from` and `note_snapshot/profile.rs`.

- **Classification:** a table is "prose" when any body cell outside the first column has 12 or more words. The default sits at the observed corpus split; make it a constant or config value. All other tables are "grid."
- **Records layout for prose tables:**
  - The first cell becomes a bold run-in lead line, kept with what follows via `\needspace`.
  - In 2-column tables, the value follows as a plain paragraph with a small indent.
  - In 3+ column tables, each remaining cell becomes its own line, `Header: value`, with the header in muted semibold sans.
  - About 4pt between records; the table's caption or id, if any, goes on a wrapper `Div` so return links still resolve.
  - No side-by-side label column: the hanging variant was still detected.
- **Grid layout for data tables:**
  - Content-aware widths: CSS-auto style, minimum = longest word, maximum = longest cell. Natural `l` columns when everything fits.
  - Hairline row rules: `\noalign{\vskip3pt{\color{BobRule}\hrule height .4pt}\vskip3pt}`, keeping the booktabs top, mid, and bottom rules.
  - Gotcha: once a table is emitted as a `RawBlock`, pandoc stops loading `longtable` and `booktabs`. Add `\usepackage{longtable,booktabs,array,calc}` to bob's header includes; all four are already in `RENDER_TEX_PACKAGES` via `tools` and `booktabs`. Alternatively, keep the `Table` AST and only adjust `colspecs`.
- **Overrides:**
  - Frontmatter `bob-tables: auto|records|grid`, mirroring `bob-return-links: false`.
  - Per table, a fenced div `::: {.bob-grid}` or `::: {.bob-records}`.
  - A global `highlights.tables` default, passed as metadata.
  - Document all of these in create's `--help` and the highlights docs.

**2. Tests**, following the existing pandoc/xelatex/pdftotext-gated pattern in `create.rs`:

- A prose table produces no `longtable` in the TeX, and its record labels appear in `pdftotext`.
- A data table keeps a `longtable` with the computed widths.
- Both overrides work.
- Code spans inside cells still reach the code catalog, and the existing return-link pill test still passes.

**3. Mac acceptance:** re-run `cells_probe.swift` on new renders and expect **0** table-cell selections on prose-table content, then do one real Highlights session.

**4. Phase 2, web route:** in `web_clip_render.py`, apply the same classification to article `<table>`s. Restack prose tables with CSS (`display:block` rows and `td::before { content: attr(data-label) }`). Verify with the probe; I expect the visual detector to ignore stacked tables, but I did not test it.

**5. Reader side, now:**

- Send the Highlights developer the specifics: `PDFView.documentAnalysisEnabled` defaults to YES on macOS 26; drags in detected tables yield `isTableCellSelection` selections with infinite bounds; Highlights writes zero-QuadPoint annotations from them; turning analysis off restores text selection. Ask for a preference.
- File the same with Apple Feedback.
- Until then: use the rectangle tool for tables in papers.

**Optional cleanup:** existing PDFs contain zero-geometry ghost annotations (20 on the SDLC page). They are filtered out of the sidecar and the note, so they are harmless. A later `bob ref doctor` warning could count them.

## 7. Side findings

- **Emoji in generic Markdown PDFs print as missing glyphs.** For example, 🍅 becomes `\x00` in `lib/chat/now_tag_vs_in_progress_status.pdf`. The DejaVu fonts lack emoji, and that route has no fallback, unlike note snapshots, which ship Noto Emoji. Unrelated to tables.
- **`PDFPage.characterIndex(at:)` is unreliable on these PDFs.** It returns NSNotFound for most glyph centers, on Chrome PDFs too, so it is not a useful signal for any bob tooling.

## Sources

- bob-cli: `src/native/highlights_ref/create.rs` (pandoc flags, header includes), `render_tex.rs`, `code_catalog.lua`, `return_links.lua`, `note_snapshot/note.lua`, `scripts/web_clip/template/reader.css`
- Vault: `~/bob/.bob/ref-sources/*/*/source.md` (corpus), `~/bob/lib/**.pdf` (annotations), `ref/blogs/the_ai_native_sdlc_playbook.md`
- Mac probes: `cells_probe.swift` (assets); macOS SDK 26.5 `PDFKit.framework` headers and Objective-C runtime method lists
- [Apple Community thread 256139925](https://discussions.apple.com/thread/256139925): macOS 26 Preview highlighting failures in tables
- [Cocoa-dev 2010: PDFKit column-aware selection](https://lists.apple.com/archives/Cocoa-dev/2010/Jan/msg01358.html) (background)
- [Highlights on the App Store](https://apps.apple.com/us/app/highlights-extract-pdf-notes/id1498912833)
