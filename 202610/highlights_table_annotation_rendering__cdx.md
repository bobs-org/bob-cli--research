# Making Bob’s PDF tables easier to annotate in Highlights

Independent research by **cdx**, 2026-10-29. Repository inspected: `bobs-org/bob-cli` at `48253b7f225620f2cde10c856f458c31cd6f58d3`. No other swarm researcher’s report, transcript, or findings were consulted.

Improving this is worthwhile, but the implementation should separate two problems: **making table text easier to select** and **making the information easier to read**. My recommendation is a small, measured extension to the existing Pandoc/XeLaTeX renderer: retain tables for comparisons, tune their typography, and offer an explicit single-column rendering for prose-heavy tables. Do not switch PDF engines or flatten all tables by default. Establish which alternative actually improves Highlights selection before changing the default.

This report includes source inspection, official documentation, and three generated PDF samples. It does **not** reproduce Bryan’s failure in Highlights: no problematic PDF or Apple runtime was available in this Linux workspace. The selection diagnosis below is therefore a set of testable hypotheses, not a confirmed root cause.

**Bob has several rendering paths, and the fix needs a defined scope.**

| Input path | Current behavior | Implication |
| --- | --- | --- |
| Ordinary Markdown, including research reports | Pandoc with `markdown+autolink_bare_uris`, XeLaTeX, DejaVu fonts, 10 pt body, 1.08 line stretch, 0.85-inch margins; Lua passes for code catalogs, code wrapping, links, and reports | This is the best first target. Table layout largely comes from Pandoc’s LaTeX writer. |
| Vault-note snapshot | Separate Pandoc-to-TeX/XeLaTeX profile, `commonmark_x` reader, bundled fonts, 10.75 pt body, narrower text area | Share the table transformation, but verify this profile separately. Reader dialect and available width differ. |
| Web article/collection | Chromium print pipeline, `tagged=True`; CSS currently uses full-width tables, 8.5 pt text, borders and alternate row shading | A LaTeX change will not affect this path. Its typography and PDF text need a separate comparison. |
| Existing PDF | Imported/stamped rather than laid out from Markdown | Changing the renderer cannot repair an already-created publisher PDF. |

These are implementation observations from [the generic render invocation](https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/src/native/highlights_ref/create.rs#L5782), [the snapshot profile](https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/src/native/highlights_ref/note_snapshot/profile.rs#L181), [snapshot typography](https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/src/native/highlights_ref/note_snapshot/note.tex#L27), [web table CSS](https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/scripts/web_clip/template/reader.css#L321), [browser PDF options](https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/scripts/web_clip/web_clip_render.py#L1041), and [creation routes](https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/docs/highlights-create.md#L406).

The generic profile already disables common ligatures and hyphenation and uses ragged-right text. “Disable ligatures,” “make the PDF searchable,” or “remove vertical rules” are consequently poor first answers for this path. My baseline fixture has real text and horizontal booktabs rules, with no vertical grid. Bob’s documentation also records that the snapshot engine was chosen following PDFKit measurements that found extracted-word problems with Chromium/Skia and variable fonts. A wholesale browser migration would reopen an already-investigated tradeoff. That historical finding is reported by the project documentation, not independently remeasured here. [Existing text-layer contract](https://github.com/bobs-org/bob-cli/blob/48253b7f225620f2cde10c856f458c31cd6f58d3/docs/highlights-create.md#L121).

**“Highlights selects the cell” is plausible as a symptom, but its cause remains open.**

Highlights’ documented ordinary interaction is to drag over text and then apply highlighting. Its documented table-recognition workflow instead begins with an **image selection**, followed by table recognition and optional CSV copying. A configured Power Tool can trigger that recognition automatically for an image annotation of a particular color. Check the active tool and that setting during reproduction, but do not assume the user has selected the wrong tool. These documents do not establish that ordinary text dragging should select whole cells. [Text markup](https://highlightsapp.net/how-to/mac/markup-pdf/), [table extraction](https://highlightsapp.net/how-to/mac/extract-pdf-table-to-excel/), [Power Tools](https://highlightsapp.net/how-to/mac/power-tools/).

A PDF’s visible table, its logical structure, and the reader’s selection behavior are different things. The three XeLaTeX samples generated here have no `/StructTreeRoot`; they do not contain tagged `Table`/`TR`/`TD` structures for Highlights to select. This **does not rule out visual table recognition by the reader**. Apple exposes document analysis capable of recognizing table structure, and PDFKit supports automatic interpretation of image text and forms. Neither source proves what Highlights does in Bryan’s case. [Apple document recognition](https://developer.apple.com/videos/play/wwdc2025/272/), [PDFKit Live Text and forms](https://developer.apple.com/videos/play/wwdc2022/10089/?time=414).

The strongest initial layout hypothesis is that adjacent wrapped text creates ambiguous selection boundaries. Apple’s public PDFKit APIs include point-to-point, rectangular, word, line, and character-range selections; the point-based API describes geometric ordering of the endpoints. It does not promise that a drag remains within a visual table cell. This is relevant mechanism evidence, not proof that Highlights uses a particular API or that its current implementation behaves identically. [PDFPage point selection](https://developer.apple.com/documentation/pdfkit/pdfpage/selection%28from%3Ato%3A%29), [PDFSelection](https://developer.apple.com/documentation/pdfkit/pdfselection).

The useful differential diagnosis is:

| Observation to reproduce | Hypothesis it would strengthen | Implementation consequence |
| --- | --- | --- |
| Selecting a phrase across wrapped lines includes neighboring cells | Geometric reading-order/column ambiguity | Compare wider text cells with a single-column prose layout. |
| Even a word on one line cannot be selected cleanly | Font mapping, character boxes, overlay, or active tool | Inspect character bounds and tool state before changing table composition. |
| An image-style rectangular annotation appears | Image selection or recognition workflow | Check Highlights settings; rendering may be unrelated. |
| The same PDF fails in Highlights and another Apple reader, but succeeds elsewhere | Shared platform behavior or differing PDF-layout heuristics | Retain the cross-reader reproducer; source layout changes may be a workaround. |
| Only web captures fail | Browser/font/CSS path | A generic Markdown filter would miss the reported problem. |
| Text selection is correct but the saved quotation is wrong | Annotation extraction or synchronization | Inspect saved annotation and exported note separately. |

There is no evidence here for a PDF metadata switch that reliably tells Highlights “never select table cells.” Removing tags would also discard useful semantics and would not address the untagged baseline.

**A small rendering experiment exposed a concrete readability issue.**

Pandoc’s Markdown reader can derive relative widths from the header separator’s dash counts when a pipe table requires wrapping; otherwise it can size columns to their contents. Thus an innocent-looking `--- | --- | ---` can give a short identifier column the same width as a paragraph column. The current fixture’s generated TeX confirms three `0.3333` fractions. Pandoc normally uses `longtable`, which supports tables spanning pages. Treat source column widths as potentially intentional; a new renderer should not blindly overwrite every supplied width. [Pandoc table rules](https://pandoc.org/MANUAL.html#extension-pipe_tables).

I generated the same short document three ways, using Bob’s generic render flags, extracted preamble and existing Lua filters. The fixture contains a two-row prose comparison, a numeric table, and a mixed text/code/link table. The samples bypass Bob’s vault installation, metadata stamping, and source-store publication. They isolate rendering rather than testing the complete create command.

| Variant | Deliberate change | Observed result |
| --- | --- | --- |
| Baseline | Current generic profile | First benefit cell wraps to five lines; a large portion of the label column is empty. |
| Widths and spacing | Prose columns set to 16% / 42% / 42%; `tabcolsep=9pt`, `arraystretch=1.18` applied to longtables | First benefit cell wraps to four lines; comparison remains aligned. These constants are trial values, not calibrated defaults. |
| Linear prose | Only the marked prose table becomes ordinary paragraphs with repeated bold field labels; other tables remain tables | First benefit becomes two lines in a single text column; the original comparison grid is lost. |

All three rendered successfully, remained two Letter pages, and retained all 18 body-cell strings in whitespace-insensitive MuPDF text checks. The reported external link catalog was the same in all three, but that link is in an **unchanged** table; this is not a transformed-link regression test. All samples remained untagged. Visual inspection found the narrower label column useful and the linear version easier to read as individual passages. The table header/body region measured about 134 pt high in the baseline and 125 pt with adjusted widths/spacing; the comparable labeled-paragraph region was about 164 pt. This small example illustrates the space tradeoff, not a general page-count forecast.

MuPDF emitted cell text in contiguous cell sequences even for the baseline. Therefore “LaTeX necessarily writes this table’s words in broken row order” is not supported by this experiment. Successful MuPDF extraction likewise does not demonstrate successful PDFKit or Highlights selection. The combined width/spacing trial also does not isolate which individual parameter affects interaction.

The reproducible bundle is [highlights_table_annotation_trials__cdx.zip](highlights_table_annotation_trials__cdx.zip), durable snapshot `file:explicit:4320f9bffae68eeb3edfab19`. It contains all three PDFs, generated TeX, source, a rendering script, line geometry, and checks. Run the script against the inspected Bob revision with Pandoc 3.1.3, XeTeX/TeX Live 2026, and MuPDF 1.23.10 for comparable output. The prototype intentionally handles only this simple fixture; its linear version retains caption wording but drops the automatic “Table 1” prefix. It is evidence for evaluation, not production-ready code.

**The goal is good; a universal table replacement would be a poor requirement.**

There is no detailed implementation plan to critique yet. The main risk in the proposed direction is treating an uncertain interaction failure as a mandate to redesign every table. Tables make numerical comparison, rankings, schedules, and compatibility matrices much easier to scan. Conversely, a table whose cells contain paragraphs is often functioning as several essays squeezed alongside each other. Those two uses deserve different treatments.

A cosmetic change alone may produce a prettier PDF without changing selection behavior. A renderer replacement is much more expensive than the symptom currently justifies. An automatic prose-versus-data classifier can silently damage meaningful comparisons, and character-count thresholds do not understand what the reader is trying to compare. A small explicit presentation choice is a better initial contract.

I would make these **requirement adjustments** explicit:

1. **Define the outcome as precise text annotation.** A reader must be able to highlight a word, a phrase, and a wrapped passage within one cell, without unrelated text, and obtain the same intended quotation after saving and synchronization. CSV extraction and image snapshots are different workflows.
2. **Make readability task-specific.** Preserve matrix scanning for comparison tables; improve passage reading for prose tables. Require Bryan to assess both at his normal window width and zoom. A single global “easier to read” score is insufficient.
3. **Scope the first implementation to newly rendered Markdown PDFs.** Include the snapshot profile in integration tests. Evaluate web captures separately if a failing example comes from that path; exclude imported publisher PDFs from layout guarantees.
4. **Keep content fidelity and normal text as invariants.** Preserve wording, order, empty cells, labels, links, code, emphasis, captions, and identifiers. Do not rewrite prose to fit or silently shrink it to tiny text.
5. **Require an explicit fallback and preserve existing annotated PDFs.** Rendering preferences affect new output. Existing annotations refer to positions on existing pages; do not bulk regenerate the library as a “format upgrade.”

**The implementation options have different costs and failure modes.**

| Option | Annotation prospect | Readability/cost | Assessment |
| --- | --- | --- | --- |
| Modest spacing and better width allocation | May reduce ambiguous wraps; cannot guarantee cell isolation | Preserves comparison; low implementation cost, though wider gutters consume text width | First candidate for a conservative default after validation. |
| Explicit stacked field paragraphs for prose tables | Removes adjacent columns from the target passage | Easier passage reading; repeated labels and more vertical space; worse column comparison | Recommended selective alternative. |
| Convert every table to records automatically | Same potential interaction benefit | Destroys useful matrices and creates heuristic surprises | Reject as the initial default. |
| Tagged PDF through a supported LaTeX tagging route | Better logical semantics for consumers that use them | Engine/template/package compatibility work; unclear effect on Highlights dragging | Valuable separate experiment if the small layout change fails. |
| Replace XeLaTeX with Chromium, Typst, or another engine | Unknown until measured on the same failing PDFs | Broad typography, pagination, font, link, and catalog changes | Too broad for the current evidence. |
| Rasterize tables or convert glyphs to outlines | Loses the direct text-selection target | Adds OCR dependence and makes search/copy less reliable | Reject for this goal. |
| Add invisible duplicate text or whole-cell `ActualText` | Reader-dependent; could change extraction without improving geometry | Risks duplicate or mismatched text and excessively coarse selection | No evidence to justify as a first fix. |
| Keep table plus duplicate prose appendix | Provides a second annotation surface | More navigation, repeated search results and ambiguous quote locations | Reserve for rare documents that truly require both forms. |
| Use Highlights image selection/table extraction | Works for capturing a region or table data | Does not provide precise phrase highlighting | Useful fallback, not acceptance of the requested fix. |

Tagged PDF deserves particular care. W3C explains how tags establish logical reading order for accessibility, but that is not a guarantee about mouse selection in every reader. Current LaTeX tagging guidance supports pdfLaTeX and recommends LuaLaTeX for new documents; it also requires identifying table headers. Enabling it in Bob would therefore be a deliberate engine/template integration, not simply adding a CSS attribute to the current XeLaTeX command. Tags should remain correct where emitted, including the existing browser path. [W3C reading-order guidance](https://www.w3.org/TR/WCAG20-TECHS/PDF3.html), [current LaTeX tagging instructions](https://tagging-project.latex-project.org/documentation/usage-instructions).

**A bounded Pandoc transformation fits Bob’s architecture.**

Use a dedicated table-layout Lua filter operating on Pandoc `Table` nodes. Do not regex-rewrite Markdown or postprocess the emitted TeX strings to discover cell boundaries. Pandoc exposes captions, column specifications, head/body/foot groups, cell contents, and spans, so the renderer can retain the actual parsed structure. [Pandoc Lua table API](https://pandoc.org/lua-filters.html#type-table).

Keep matrix rendering as the default presentation. For a first prose alternative, support an explicit fenced Div around a table, for example a proposed `.bob-table-prose` class. This wrapper is practical on the locally installed Pandoc 3.1.3; do not assume newer table-caption attribute syntax works on every deployed version. The exact public spelling should be settled during implementation. No global CLI switch is necessary to prove the feature.

Limit the initial conversion to a rectangular table with one plain-text header row, no spans, no intermediate header groups, and no footer. Retain every body cell’s AST content in row order under its header label. Use regular full-width paragraphs or a definition-style layout that remains a single text column. Labels should remain attached to their values, and row boundaries should remain visible through spacing or a restrained rule. Do not put each entire record in an unbreakable box: a long row must be able to continue on the next page.

Complex tables should stay tables, with a clear diagnostic when an explicit prose request cannot be honored. In particular, do not flatten merged headers by guessing their labels. Avoid duplicating rich header content with links, footnotes, or anchors until that behavior has a defined contract. Keep caption numbering, table destinations, and cross-references meaningful; the experimental filter’s caption-number omission is one reason it must not be shipped unchanged.

For table-preserving typography, retain meaningful alignment, repeat headers on continued pages, retain readable body-sized text, and use measured column allocation with width bounds. Preserve explicit author widths where possible. A universal 16/42/42 rule would be wrong outside this three-column example. Implement generous row separation locally to the table; do not globally increase every paragraph’s leading or shrink tables to force a page fit. Verify the effect of `arraystretch` on tall paragraph cells rather than assuming it changes every wrapped line’s leading.

The natural wiring points are `RenderFilters` and `write_render_filters` in `create.rs`, the generic render invocation, and `note_snapshot/profile.rs`. The code-catalog capture must still see original code bytes before transformations that alter presentation; the report pass must still observe final headings and anchors. A candidate order is catalog capture, diagram replacement, table layout, then existing typography/return-link passes and catalog reporting. This order needs fixtures: moving header content into paragraphs can alter return-link eligibility, and duplicating captured nodes could duplicate anchors. Keep links, footnotes, and code as AST nodes rather than flattening them with `stringify`.

This design preserves the accepted source-store and render-time-catalog policies: layout is a rendering operation, the saved source remains the actual input, and changed PDFs receive matching newly derived catalogs. Re-render from preserved source through existing lifecycle paths when explicitly requested; do not retrofit annotations onto shifted coordinates. File coordination protects writes, but does not make an old annotation’s page coordinates valid after layout changes. Relevant audited memory reads were `decisions:reference-sources-are-preserved-write-once`, `decisions:code-copy-reads-render-time-catalog`, and `decisions:open-pdf-writes-are-coordinated`.

**The decisive test is short and should precede a default change.**

Use one actual PDF that Bryan finds difficult, plus the bundled samples. Record the input route, Highlights version, macOS version, window size, zoom, active tool and relevant Power Tool setting. First establish the existing failure, with a paragraph outside the table as a control. Then compare baseline, width-only, spacing-only, and stacked prose variants of the same content; the present bundle combines widths and spacing, so separate them in the acceptance trial.

For each variant, select a single word, part of a line, a phrase spanning two or more lines, and the whole text of one cell. Include a middle column, first/last rows, and a cell adjacent to much taller text. Record whether it succeeds on the first drag, what extra adjustment is needed, and the exact exported quotation. Save, close, reopen, and confirm that the highlight stays on its intended words. Inspect the Highlights note and Bob’s imported annotation in a disposable test reference. Compare the troublesome PDF in another reader to help locate the failure layer.

Readability acceptance should include finding one fact, comparing a value across rows, and identifying which row/column an excerpt belongs to. Proposed acceptance: all representative cell-selection tasks succeed without neighboring-cell contamination; extracted quotations match the intended text after ordinary whitespace normalization; Bryan finds prose reading improved and numerical comparison no worse. Do not claim production readiness from a passing text-extraction unit test alone.

Automated coverage should complement that interaction check:

- Rendering fixtures for short/numeric tables, verbose/wide tables, long unbreakable tokens, page-spanning tables, empty cells, Unicode, links, inline code, and supported block content.
- A conservative fallback fixture for spans, complex headers, and footers; unsupported content must remain intact.
- Checks for omitted/duplicated text, clipping, unreasonable font reduction, captions/IDs, link targets, and catalog destination/page associations.
- Both generic Markdown and note-snapshot profiles, with their actual readers and text widths. Add browser fixtures only when that route is changed.

If table-preserving changes pass, ship those and keep the prose alternative available. If only stacked prose passes, make it the supported explicit choice for prose tables and consider a broader opt-in policy only after evaluating real reports. If even ordinary single-column passages fail, stop tuning table geometry and investigate the font/reader/extraction issue. An engine or tagged-PDF experiment then has a concrete failing case against which to justify its cost.

**Recommended solution:** retain Pandoc/XeLaTeX and introduce a shared, conservative table-layout layer. Validate modest width/spacing improvements as the possible new default; add an explicit, semantics-preserving single-column prose-table presentation while keeping comparison matrices intact. Gate the default on a real Highlights selection-and-export trial, apply changes to newly generated PDFs, and preserve existing annotated files. This is a good improvement when defined around successful annotation and task-specific readability; a global flattening rule or renderer migration is not justified by the evidence available today.
