# Beautiful PDFs from Bob notes: preserve meaning before changing the renderer

Independent research by **cdx**, 2026-10-15. This report was developed from bob-cli source, the supplied PDF, official documentation, and small local experiments. No other report or findings from this research swarm were consulted. This is research and a design recommendation; no product implementation was changed.

**Decision:** Add an explicit note-reader style to `bob ref create`, using an Obsidian-aware normalization step followed by Pandoc HTML and Bob's existing Chromium reader renderer. Keep the existing Pandoc/XeLaTeX route available. The valuable work is resolving note semantics and producing a clean reading snapshot. Switching PDF engines alone will not fix the supplied example.

## What the example actually shows

The supplied `~/bob/lib/chat/sase_blog_v1.pdf` is present on athena, so Mac access was unnecessary. I inspected its metadata, extracted text, and rasterized pages 1 and 5 for visual inspection. It is six Letter pages, 77,969 bytes, created by “LaTeX via pandoc,” produced by xdvipdfmx, and untagged. Its SHA-256 is `83a4c3f9f9683aa1c01552229c9cbacf55c81aec1d79d6de8ed71c5822e69f66`.

The problems are concrete:

- The title is the internal stem `sase_blog`, with a large gap before a prominent contents list.
- Sections start at `0.1`, `0.1.1`, etc. A document with no body H1 is being numbered as though it had a missing parent section.
- Wiki links, block identifiers, `#task`, `#hide`, and fields such as `[created::…]`, `[fresh::…]`, and `[dependsOn::…]` print literally.
- Custom task statuses print as text such as `[/]` and `[?]`, while some decorative glyphs become missing-glyph boxes.
- Images such as `![[img/…png|400]]` print as syntax rather than screenshots. Some screenshot references are merely filesystem paths; an exporter should not silently turn every mentioned path into an embedded image.
- A long screenshot path visibly crosses the right edge of page 5. Path wrapping is a content-layout issue, separate from code-block wrapping.
- A `## Requirements` string appears inside extracted task content. This may reflect malformed or tightly packed source Markdown; I did not inspect the original note, so I cannot attribute that particular issue solely to the renderer.
- Several pages are dominated by operational task history before the outline and explanatory material.

This is a readable-source interpretation failure as much as a typography failure. A modern font and attractive cover would leave missing screenshots, literal links, and clutter untouched. Conversely, faithfully printing every operational detail would still be a poor article or project brief. Those are different products.

## What Bob already implements

Local code evidence is anchored to bob-cli commit `eb0dca8e2b911c2a7b030b7a68342916772e8215`.

| Evidence | Consequence for the design |
| --- | --- |
| `src/native/highlights_ref/create.rs:860`, `:1851`, `:2317` | Markdown planning, rendering, and installation already have separable seams. The renderer receives the original source path. |
| `create.rs:2317` | Markdown always uses Pandoc/XeLaTeX, automatic TOC, depth 3, numbered sections, 10pt DejaVu fonts, 1.08 line spacing, and 0.85in margins. Asset search is based on the source directory. No Obsidian wikilink reader extension is explicitly selected here. |
| `src/native/highlights_ref/render_tex.rs` | The current route already maintains checks and diagnostics for a substantial LaTeX package inventory. Improving its appearance is possible, but operational complexity already exists. |
| `src/native/highlights_ref/return_links.lua`, `return_links.tex`, `return_links.rs` | Same-document links have a significant existing contract: canonical targets, eligibility rules, duplicate/dead-target handling, raised tags, and paired `↩ p. N` links. This implementation is LaTeX-specific. |
| `scripts/web_clip/web_clip_render.py:511`, `:754`, `:805` | Web articles already use a Bob-owned HTML/CSS renderer, offline staged assets, bundled fonts, and headless Chromium. PDF generation asks for outlines and tags. |
| `scripts/web_clip/template/reader.css` and `fonts/README.md` | Bob already ships Source Serif 4, Inter, and JetBrains Mono under OFL, with a restrained reader layout, page numbers, code wrapping, tables, and captions. |
| `scripts/web_clip/web_clip_adapter.py:373`, `:1757` | Sanitization and an existing compose protocol can inform a new render-only operation. Article extraction and note rendering should remain distinct entry paths. |
| `src/native/highlights_ref/stamp.rs:701`; `docs/highlights-create.md` | PDF validation, marker stamping, collision handling, audio behavior, and atomic installation should continue to surround any renderer. |
| `src/native/task_fields.rs`, `src/native/capture_links.rs` | Shared inline-field and link-related code is worth assessing for reuse. These modules are useful building blocks, not evidence that Bob already has a complete Obsidian document parser. |

`-P/--parent` is required today and identifies the owner of the eventual reading task; it does not identify which note is being exported. Create normally installs into `xlib/`, and `bob ref scan` later moves the PDF to `lib/` and creates its reference note. The current default type for Markdown is `chat`. An explicit `-t docs` is already available for a note snapshot; a new taxonomy is unnecessary for the first release.

A title is also part of local-file collision identity. Humanizing a filename must happen consistently during planning and rendering, rather than changing only the visible masthead. Likewise, `--force` is not a general license to replace an annotated library PDF. The current documented overwrite rule is narrower and should remain intact.

## Local experiments and their limits

These were small mechanism probes, not an end-to-end export implementation or a performance comparison.

**1. Pandoc parsing.** On Pandoc 3.1.11.1, the default Markdown reader left wiki links, Obsidian callouts, custom task states, and image-embed syntax as literal text. Enabling `markdown+wikilinks_title_after_pipe` converted aliases to links and recognized an image embed. However, `![[img/screenshot.png|400]]` became an image whose alternative text and figure caption were `400`, not an image constrained to 400 pixels. Custom task states and callouts remained unnormalized. Enabling one extension is a useful first step, not an Obsidian compatibility layer. The extension itself is documented in the [Pandoc manual](https://pandoc.org/MANUAL.html#extension-wikilinks_title_after_pipe).

**2. Existing reader renderer.** With a synthetic, already-normalized HTML fixture, I called `web_clip_render.render()` directly. It produced a visually inspected one-page Letter PDF with a clear title, serif body, sans-serif headings, wrapped command, and readable table. `pdfinfo` reported `Tagged: yes`; the file was 129,466 bytes. Two observed warm render calls took about 0.51 and 0.44 seconds, excluding environment setup and the separate feature probe. These timings are merely evidence that this small local path works. They say nothing reliable about cold starts, long notes, images, or Mac performance. The existing adapter's ping reported Python 3.14.7, Playwright 1.62.0, Pillow 12.3.0, and Chrome 155.0.8059.79.

The synthetic render still needed note-specific masthead and alignment changes: it was an article renderer receiving note content. It did not exercise the source normalizer, missing assets, marker stamping, or Highlights.

**3. Printed page references in Chromium.** In the installed Chrome 155, `CSS.supports('content', 'target-counter(attr(href url), page)')` returned true. Nevertheless, a two-page printed fixture omitted the generated page-reference suffix entirely. `string-set` and `float: footnote` returned false in this environment. Parsing acceptance is therefore insufficient evidence of printed cross-reference support. Chrome's own documentation distinguishes shipped margin boxes/page counters from additional pagination features such as target cross-references and footnotes. [Chrome print-margin documentation](https://developer.chrome.com/blog/print-margins)

**4. Typst page references.** A standalone two-page fixture compiled with local Typst 0.15.1 and `--ignore-system-fonts`; extracted text correctly read “Go to detail on page 2” and “Back to page 1.” This tested native Typst locations/counters, not a Pandoc migration or Bob return-link parity. Typst's [query documentation](https://typst.app/docs/reference/introspection/query/) and [link documentation](https://typst.app/docs/reference/model/link/) describe the necessary mechanisms.

The first custom Chromium probe also hit an overly long Unix socket path under the agent's deep temporary directory; rerunning with a short temporary base succeeded. Bob's adapter already comments on this constraint. Reuse its launch/scratch handling rather than copying my minimal harness into production.

## Is the feature a good idea?

**Yes, as a personal reading and annotation snapshot.** Bob already has a PDF-centered Highlights workflow, so making the reader consume the same project context, images, and task meaning that Bryan sees in his notes has direct value. A local batch-capable command is also useful on athena without involving a running desktop app.

**It is a weaker idea as the way to turn a project workspace into a public article.** The example is planning material, task history, and an outline. Beautifully typesetting it will not produce the eventual blog post. Public-facing writing should come from a deliberately authored document or selected publishable section. Formatting must not invent prose, decide which ideas matter, or silently remove inconvenient history.

**It should not become a live PDF mirror of every area and project.** Regeneration changes pagination and can invalidate the context of existing highlights. Importing every revision into `ref/` also creates duplicate reading tasks and a loop in which the source project contains a reading task for its own exported state. That may be intentional for a particular review, but should not happen automatically.

If the actual need is just a one-off PDF matching the live Obsidian pane, first try Obsidian's native export with a small print stylesheet. It avoids implementing plugin-specific rendering. For Bob automation, depending on that application is a substantial tradeoff: the official CLI requires Obsidian to be running, and exposes developer DOM/CDP operations rather than a documented standalone PDF export command in the command list I checked. A custom desktop bridge remains possible, but it would be a different implementation with different availability guarantees. [Obsidian CLI documentation](https://help.obsidian.md/cli)

## Requirement adjustments I recommend

These changes are proposals, not claims about the current command.

| Adjustment | Reason and concrete behavior |
| --- | --- |
| Define the product as a **reading snapshot**, with an explicit supported syntax subset | A bounded promise can be tested. “Render whatever every Obsidian plugin renders” cannot be delivered by a Markdown converter alone. |
| Separate semantic cleanup from visual styling | Both HTML and Typst need correct note/link/embed handling. This work should survive a later engine change. |
| Preserve authored prose and task meaning by default | Keep task titles, meaningful tags, dependency relationships, dates needed to understand scheduling, child notes, and closed-task content. Render states as labels/icons with text, not raw checkbox characters. Do not recompute or reconcile task lanes while exporting. |
| Hide machine syntax, not information indiscriminately | Suppress structural tags, stable IDs, block-marker text, freshness machinery, and capture synchronization tokens from the reading surface. Keep anchors internally. Preserve unknown inline fields as readable metadata rather than deleting every `[key:: value]` expression. |
| Treat history reduction as an explicit later profile | Closed tasks and work/schedule/cancellation logs may be moved to a clearly labeled appendix in a future brief profile. Do not make “beautiful” mean silently excluding them. |
| Support portable static output before arbitrary live queries | Render supported static constructs. DataviewJS, plugin widgets, Bases, audio/PDF viewer embeds, and unsupported code blocks should produce a useful placeholder/diagnostic, not be executed or silently disappear. A supported Bob query can later generate a dated static result. |
| Expand collapsed callouts in the PDF | A collapsed screen control must not hide content in a static reading artifact. Obsidian documents both collapsed callouts and embeds into note sections/blocks. [Callouts](https://help.obsidian.md/callouts), [embeds](https://help.obsidian.md/embeds) |
| Use PDF bookmarks always; make the visible TOC restrained | The six-page example spends valuable space on navigation before any substance. For the first note-reader style, omit a visible TOC by default and use unnumbered headings. Retain the classic report behavior when requested. |
| Keep source and annotated snapshot distinct | No automatic refresh, source-note rewriting, reading-task creation beyond the existing scan workflow, or overwrite of an annotated library copy. A new deliberate snapshot gets a deliberate new name. |
| Scope “accessible” to evidence | Require searchable/selectable Unicode text, meaningful reading order, heading structure, and usable highlights. Tagged output is useful, but is not proof of PDF/UA compliance. Playwright exposes PDF tags and outlines; it does not certify the resulting document. [Playwright PDF API](https://playwright.dev/python/docs/api/class-page#page-pdf) |
| Explicitly relax page-number return pills **only in the new opt-in reader style** | Preserve forward links and paired return anchors, but use “Back to reference a” rather than promise `↩ p. N` in plain Chromium. Keep the existing page-number behavior in the classic renderer. This is the most material proposed tradeoff. |

For personal reading, external-to-snapshot vault links can retain readable labels and explicit local Obsidian links. They are not portable links for a reader without the vault. Links to included content should instead target internal PDF anchors. A later sharing profile should render local-only destinations as labeled references rather than claim they work everywhere. Never follow every wiki link recursively merely because it is mentioned.

If exact existing page-number pills, page-bottom footnotes, or book-style cross-references are mandatory in the new style, reject that last adjustment and favor Typst after normalization. Do not spend the first release building a custom pagination engine just to preserve a decorative part of navigation.

## Rendering options

The judgments below are specific to this repository, not a general ranking of document tools.

| Option | What it does well here | Principal cost or limitation | Assessment |
| --- | --- | --- | --- |
| Improve current Pandoc/XeLaTeX template | Smallest integration change; preserves current math, page references, and Bob return macros | Still needs the full Obsidian normalizer; font/package support and complex layouts remain LaTeX maintenance work | Credible conservative fallback; changing engines is not required to improve the example |
| **Pandoc HTML + existing Chromium reader** | Reuses Bob's current fonts, print template, runtime, asset routing, outlines, and tagging; useful HTML preview follows naturally | Needs note components, careful pagination, and an explicit return-link contract; browser version affects output | Best default direction for note reading |
| Pandoc + Bob-owned Typst template | Strong document layout, native footnotes/math and location-based page references; local compiler; potential accessible PDF export | New renderer/template stack; port every LaTeX-specific filter; handle unsupported raw HTML and bundle appropriate font formats | Best alternative when precise paginated features outrank reuse |
| HTML + WeasyPrint | Print-oriented CSS, links/bookmarks, target cross-references, and footnotes | Adds a third rendering runtime plus Pango; no JavaScript; existing CSS must be verified on that engine | Good print engine, but not enough reason to add it alongside existing Chromium and LaTeX initially |
| HTML + Paged.js | Adds pagination features to the browser approach, including target page counters | More layout transformations, dependency/version work, and another class of link/tag/pagination regressions | Revisit only after a demonstrated paginated feature requirement |
| Prince | Purpose-built commercial print rendering with extensive page-layout support | Licensing and another engine; note interpretation still needed | Hard to justify for this initial personal-note feature |
| Quarto | Established authoring/publishing system with Typst integration | Much wider product surface; does not remove the Bob-specific normalization problem | Appropriate if the scope becomes a publication or book tool, not the first step here |

Official support for the less familiar alternatives: Typst supports [PDF/UA and PDF/A targets](https://typst.app/docs/reference/pdf/), while retaining author responsibilities for semantics and alternative text. Its local [font configuration](https://typst.app/docs/reference/text/text/#parameters-font) allows controlled font paths and ignoring system fonts; plan a proper font bundle rather than assuming Bob's WOFF2 browser assets are interchangeable. WeasyPrint documents its [print features](https://doc.courtbouillon.org/weasyprint/v63.0/api_reference.html#css-generated-content-for-paged-media-module), [installation dependencies](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html), and [absence of JavaScript execution](https://doc.courtbouillon.org/weasyprint/stable/going_further.html). Paged.js documents [target-counter cross-references](https://pagedjs.org/en/documentation/-cross-references/). Prince documents its [licensing](https://www.princexml.com/purchase/) and [paged-media model](https://www.princexml.com/doc/paged/); Quarto documents [Typst output](https://quarto.org/docs/output-formats/typst.html).

No engine on this list inherently understands Bob task state or the user's intent for a project workspace. That remains the core implementation responsibility.

## An implementation shape worth pursuing

Keep the orchestration in Rust and retain the existing validation/install boundary:

```text
source note + options
        ↓
resolve note and read a consistent input snapshot
        ↓
Obsidian/Bob normalization → document structure + asset manifest + diagnostics
        ↓
Pandoc HTML → Bob note template → shared offline Chromium print service
        ↓
existing PDF validation → marker/audio handling → atomic intake installation
```

For the first version, ordinary file paths are enough. Do not add fuzzy note-name resolution, vault-wide publishing, a theme marketplace, or a generalized document framework to make this work. An additive selector such as **`-S/--style reader|classic`** would be sufficient; it is proposed syntax, not an existing option. Check its alias against the entire command, sort the help entry correctly, document source/profile behavior, and update completion/help fixtures under the repository's CLI rules. Begin opt-in. Consider automatically selecting reader for recognized area/project frontmatter only after the new contract is proven; arbitrary Markdown should retain its current route during rollout.

An illustrative future invocation is:

```bash
bob ref create ~/bob/my_project.md -P my_area -t docs \
  -S reader -T "My Project — Reading Snapshot" -N my_project_review_20261015
```

The existing `-N` makes a new deliberate snapshot name possible without weakening collision protection. `-o` still means a complete PDF destination and still conflicts with `-N`/`-t`; it should not silently become a different export-only command. A separate no-intake publishing command is worth considering only if repeated non-reference exports become a real workflow.

The normalizer needs these concrete responsibilities:

1. **Identify structure.** Parse frontmatter separately; choose a single title; normalize body heading levels without rewriting IDs; retain nested lists and code literally. Use an AST/token-aware approach. Do not regex-rewrite wiki syntax inside fenced code or examples. A practical first implementation can let Pandoc parse Markdown with appropriate extensions and use Bob/Lua processing for Bob-specific structures, with a resolver manifest supplied from Rust.
2. **Resolve note identity and anchors.** Handle aliases, same-note headings, `#^block` references, and relative paths deterministically. Resolve ambiguous basenames with an error or diagnostic instead of picking the first file found. Keep stable per-source namespaces so embedded notes cannot duplicate anchors. Preserve current duplicate/dead-link reporting semantics where applicable.
3. **Resolve actual embeds.** Support vault image embeds and explicit note/heading/block transclusions. Build a bounded inclusion graph, detect cycles, and cap depth/total included bytes. Bare links remain links. Start with a clear warning/placeholder for unsupported embedded formats; missing explicitly embedded images should fail before installing a misleadingly complete PDF.
4. **Represent tasks.** Reuse Bob's authoritative task syntax/status definitions and shared field scanners where appropriate. Render human labels for the status present in the snapshot, clean structural metadata, keep meaningful dependency labels, and never invoke reconciliation as a side effect. `#hide` is an operational tag, not evidence that the entire task should disappear from export.
5. **Represent callouts and rich content.** Render callouts as restrained semantic panels. Convert math to static supported output such as MathML, and pre-render Mermaid to safe SVG when that feature is included. Keep code highlighting static. Do not run arbitrary note JavaScript. Mermaid's [strict security mode](https://mermaid.js.org/config/schema-docs/config-properties-securitylevel.html) is relevant for a controlled diagram renderer, but does not replace process isolation or asset controls.
6. **Produce a manifest and diagnostics.** Record source/embedded-note and asset hashes, profile/template versions, and renderer version. Keep that provenance separate from task identity and from external `source_url` semantics. Do not casually add unrecognized fields to Bob's marker/ref schema; integrate any durable provenance through a reviewed supported contract. Snapshot the required bytes so concurrent edits cannot create a mixed-version document.

The HTML print service should be shared with articles, but should not run note HTML through Defuddle or live-article extraction. That could discard exactly the lists and structured task content the user wanted. Add an explicit render-only request or a narrowly extracted internal module. Share fonts, page infrastructure, and component styling; use a note-specific masthead and task/callout rules rather than pretending a note has a website publisher.

Two existing implementation details deserve adjustment before reuse:

- The article sanitizer currently strips most classes and only permits selected URI schemes. Generated note classes, anchors, local Obsidian links, MathML, and trusted diagram output require a deliberate note policy. Do not widen the web-article allowlist globally just to make generated note components work.
- The article raster policy converts images to JPEG quality 82, limits the long edge to 1600 pixels, and skips images below a small-size threshold. That may suit web photos but can blur terminal screenshots or discard small meaningful note graphics. Preserve PNG/lossless output for text screenshots and vectors for diagrams, with an explicit size budget. Retain figure/caption pairing and constrain tall images by printable height.

Use bundled fonts, a legible approximately 10.5–11pt body, modest line spacing, a restrained blue accent, real text labels for task state, and clear but compact hierarchy. Reuse the current reader as the visual baseline, then correct its note-specific alignment rather than introducing a second unrelated design. Long code, tables, and callouts must be allowed to split when they exceed a page: indiscriminate `break-inside: avoid` creates whitespace or overflow. Font readiness and image decoding must complete successfully before printing; silent font fallback should be diagnosed for the supported character set.

Render from staged local assets with scripts disabled in final HTML, deny network requests in the final print context, constrain canonical local paths to the intended vault/input assets, and impose file/depth/size limits. These are practical requirements for reproducibility and correct file selection, especially when transcluding notes; they do not call for a hosted service or a new permission workflow.

## How to decide that it is good enough

Before making reader automatic, inspect the actual example and a small representative fixture set on Linux and macOS. The acceptance check should be “the content survived and is pleasant to read,” not “the subprocess returned a PDF.”

| Check | Evidence required |
| --- | --- |
| Supplied example | Screenshots appear; aliases are readable; task statuses and dependencies are meaningful; machine fields do not dominate; no `0.x` headings, missing-glyph boxes, or clipped paths |
| Content preservation | Authored paragraphs, nested task notes, closed tasks, and callout bodies survive; any intentional omissions are reported by policy |
| Link integrity | Working internal heading/block links and paired return links; duplicate-anchor, missing-target, and cyclic-embed cases are diagnosed |
| Layout stress | Wide tables, a code block taller than a page, a tall screenshot, long URLs, and nested callouts remain readable without clipping |
| PDF usability | Text extraction agrees with visible meaning; outline works; font coverage and tags are checked; source/metadata text remains selectable |
| Existing workflow | Marker round-trip, scan/ref-note creation, audio binding, collisions, and all-or-nothing install still work; dry-run still returns before rendering |
| Real annotation round-trip | Open the final **stamped** PDF in Highlights on Mac, select body and task text, make a highlight, export/sync it, and confirm text remains clean and linked to the right reference |

Use semantic parser/manifest tests plus a few real rendered-page comparisons; do not substitute fake-Pandoc tests for visual fidelity. Pin the renderer used for CI snapshots, and treat browser/template updates as reviewed visual changes. A tagged pre-stamp PDF is not sufficient: the actual library artifact must survive stamping and the Highlights workflow.

The available sample and synthetic experiments support the diagnosis and the shared-renderer feasibility strongly. They do not establish full-note parity, annotation compatibility, multilingual font coverage, or end-to-end Mac performance. I did not change the original PDF, export a live note into the vault, or run the full application test suite for this research-only work.

## Recommended solution

**Build an opt-in `reader` style inside `bob ref create`: Obsidian/Bob normalization, Pandoc HTML, then Bob's existing offline Chromium reader renderer, followed by the existing PDF validation and installation workflow.** Ship one polished note template, correct wiki/image/block handling, readable task states, stable links, and explicit diagnostics before adding more output modes. Keep authored content by default and make each import a deliberate reading snapshot.

Keep the classic XeLaTeX path for current report behavior and exact page-number return pills. In the new reader style, explicitly choose paired return links without printed page numbers; do not present that difference as invisible compatibility. If Bryan considers precise page references or page-bottom footnotes essential in the new style, use the same normalization layer with a Bob-owned Typst template instead. That is a sound alternative, but its migration cost should buy a demonstrated requirement rather than a different engine name.

This improves the actual sample, reuses an attractive renderer Bob already maintains, and avoids turning a useful PDF export enhancement into a separate publishing platform.
