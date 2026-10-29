# `bob ref create` tables in PDF: highlightability + readability

Researcher: **mus** · 2026-10-29 · swarm report (`__mus`)

Question: how should `bob ref create` render Markdown tables in PDFs so that
(1) annotations made in the Highlights app work better — today highlighting
cell contents is awkward, as if the app wants to select the whole cell — and
(2) tables get easier to read, or at minimum not harder to read.

**Bottom line up front.** Do not re-architect table rendering. Ship a
header-only cosmetics pass that cannot change the PDF text layer (so it cannot
make highlighting worse), then measure and reproduce before doing anything
structural. Keep visual booktabs tables as the default; offer a linear,
prose-form rendering only as an opt-in per-document fallback; spike Tagged PDF
separately. Details in [Recommended solution](#recommended-solution).

## 1. What `bob ref create` does with tables today

There are two Markdown-to-PDF routes, and tables flow through both untouched
as pandoc `Table` AST nodes:

- **Generic Markdown route** (`report.md`-style input):
  `src/native/highlights_ref/create.rs` runs pandoc with
  reader `markdown+autolink_bare_uris`
  (`MARKDOWN_PANDOC_READER` in `src/native/highlights_ref/code_catalog.rs`),
  `--pdf-engine=xelatex`, `geometry:margin=0.85in`, `fontsize=10pt`,
  `linestretch=1.08`, DejaVu fonts, plus stacked Lua filters
  (`code_catalog` → diagrams swap → `code_break` → `return_links` →
  `code_catalog_report`) and `PANDOC_HEADER_INCLUDES`
  (`src/native/highlights_ref/create.rs:61`). No filter rewrites `Table`
  nodes: `code_catalog.lua:362` only walks *into* cells (code/link
  extraction), and `return_links.lua` classifies table head/foot/caption as
  return-pill-ineligible while body cells stay eligible.
- **Vault-note snapshot route:** `render_note_pdf`
  (`src/native/highlights_ref/note_snapshot/profile.rs`) runs pandoc with
  reader `commonmark_x-tex_math_dollars-emoji+autolink_bare_uris` to LaTeX,
  then xelatex, with `note.tex` as the print profile and `note.lua` as the
  contract filter. `note.lua:536` passes `Table`/`Figure` through unchanged.
  (I verified `commonmark_x…` still emits `longtable` for pipe tables on the
  repo's pandoc 3.1.3 — tables are not silently dropped on this route.)
- **Web-article route** is different: `scripts/web_clip/` re-typesets via a
  Chromium print template (HTML `<table>`), so its text layer comes from the
  browser, not pandoc/LaTeX. Any fix here should target the two pandoc routes
  and leave the article engine alone unless repro shows it has the same
  problem.

In both pandoc routes the LaTeX writer emits the same thing it always has:
a `longtable` with `booktabs` rules (`\toprule`, `\midrule`, `\bottomrule`),
`array` column specs, and `calc`-width `p{…}` columns with `minipage`
wrappers once cells wrap. I confirmed this end to end on this host: a
three-column pipe table renders to
`\begin{longtable}[]{@{}lll@{}}` for narrow content and to weighted
`>{\raggedright\arraybackslash}p{(\columnwidth - …) * \real{…}}` columns
with per-header-cell `minipage`s for wide content. The loaded package set
already declares `longtable`, `booktabs`, `array` (`calc`, `etoolbox`,
`footnote` via the pandoc template) in
`src/native/highlights_ref/render_tex.rs` (`RENDER_TEX_PACKAGES`, checked by
`bob ref doctor`).

## 2. What the PDF text layer actually looks like (measured)

I rendered a probe table with bob-equivalent pandoc flags and dumped the text
layer with `mutool draw -F txt/-F stext` (no `pdftotext` on this host):

- Every cell is its own stext `line` element at the correct y/x: header
  `Name | Value | Note` on one baseline, `alpha | 1 | first cell…` and
  `beta | 2 | second cell…` each on their own baselines. Character quads are
  clean and in the right places. **There is no column-major scrambling and
  no merged-cell garbage in the text layer.**
- Header and body live in *separate* stext blocks, and each data row is a
  separate set of lines. A highlight spanning header+body or two rows
  therefore crosses block boundaries — fine for PDF viewers, but a plausible
  reason a tap-and-drag heuristic "snaps" to a cell/row instead of following
  the drag.
- Wrapped cells split into one line per visual line with no continuation
  marker (e.g. `a very long cell value that wraps over multiple lines in` /
  `the pdf`). A highlight of a wrapped cell is inherently multi-line, and
  whatever the app does at line joins is where partial/odd selections come
  from.

Honest limit: I did **not** reproduce the Highlights-app behavior itself —
no macOS/Highlights on this Linux host. The text-layer evidence says the PDF
is well-formed, which points at app-side selection heuristics (tap targets,
block snapping, line-join handling) rather than a corrupt text layer. Any
structural fix built without a Mac-side repro risks fixing the wrong thing.
Section 6 prescribes the repro protocol.

## 3. Readability today, and what "don't decrease it" rules out

Current readability is already good by print-table standards: pandoc emits
real booktabs (heavy top rule, light header rule, heavy bottom rule, no
vertical rules, no boxed grid), left/center/right alignment follows the
Markdown colons, and captions/TOC/bookmarks work through the normal pandoc
machinery. The booktabs/Tufte literature is near-unanimous on the core
rules — three horizontal rules, never verticals, whitespace (not gridlines
or zebra) separates columns, `\arraystretch` 1.2–1.3 for air. That
constrains the design space:

- **No vertical rules, no boxed grids, no zebra striping by default.**
  All three would make tap targets more visible but make the tables
  objectively worse to read, violating the stated constraint. They also
  fight the existing `note.tex` aesthetic (rules in `BobRule`, airy type).
- **No smaller type for tables.** Shrinking to `\small`/`\footnotesize` to
  fit wide tables would make cell text harder to tap-highlight on iPad and
  harder to read. Wrapping + page-breaking `longtable` is the right call;
  it already breaks across pages with a repeated header (`\endhead`).
- **Genuine readability gaps I found:** (a) default `\arraystretch` is 1.0 —
  rows are cramped, which hurts *both* reading and tap targeting;
  (b) `\tabcolsep` is the LaTeX default (6pt) with `@{}` edge trim, so
  columns sit close together and a slightly wide drag crosses into the
  neighbor; (c) header rows get no visual distinction beyond position
  (pandoc emits no bold/letterspaced header — weight comes only from the
  rule below it); (d) wrapped `p`-column text is fully justified-ish inside
  minipages with no extra leading, so dense cells look heavy.

All four are fixable with header-only TeX (lengths, not packages), which is
why Phase 0 below is pure win.

## 4. Options evaluated

| Option | Highlight effect | Readability effect | Cost / risk |
|---|---|---|---|
| **A. Header-only cosmetics** (`\arraystretch` ~1.35, wider `\tabcolsep`, booktabs rule spacing, header distinction, caption spacing) | Neutral-to-positive: larger tap targets, fewer accidental neighbor grabs; text layer byte-identical | Positive, stays booktabs | Tiny; no new packages; both routes; `doctor` list unchanged |
| **B. Light header-row shading** (`colortbl`/`xcolor[table]`) | Slightly easier row tracking | Mildly positive if very light; risks yellow-highlight-on-grey contrast | New package + `doctor`/CI updates; tint must be ~3–5% grey |
| **C. Auto-linearize tables to prose lists** (Lua filter: each row becomes headed `Para`s / definition list) | Best raw highlightability (plain paragraphs) | **Negative**: destroys scanability; violates "don't decrease readability" as a default | Medium; filter-order hazards (below) |
| **D. Dual render: visual table + linear appendix** | Good: app users highlight the appendix copy | Neutral if appendix is clearly marked "same data, highlight-friendly" | Page bloat; TOC/bookmark noise; needs anchor/pill decisions |
| **E. Swap `longtable`→`tabularray` (`longtblr`)** | Unknown, probably neutral | Neutral-to-positive styling | **High, not recommended**: pandoc cannot emit it — needs a `Table`→`RawBlock` filter that bypasses `code_catalog`/`return_links` cell handling (link anchors, return pills inside cells silently lost unless reimplemented); new heavy dependency; full `doctor`/TinyTeX rollout |
| **F. Tagged PDF** (`\DocumentMetadata{tagging=on}` + latex-lab table module) | Potentially the *correct* structural fix (real `<Table>/<TR>/<TH>/<TD>` structure for smart apps/AT) | Neutral | Spike-sized but version-sensitive: needs current LaTeX, xelatex tagging still maturing, `\DocumentMetadata` must precede `\documentclass` (pandoc template interplay), pagination/log churn; verify Highlights even consumes tags |
| **G. Render tables as images** | Catastrophic (no text at all) | Negative | Rejected outright |
| **H. Table catalog like the code catalog** (record cell text + page anchors at render time, serve via `bob ref …`, cf. `decisions:code-copy-reads-render-time-catalog`) | Sidesteps the app entirely for *copy* (bytes come from the catalog, PDF is only a locator) | Neutral | Real project, not a table tweak: new JSON contract + Mac client work per `decisions:mac-capture-is-a-thin-client`; does not fix in-app highlighting itself |
| **I. Unify Markdown routes onto the Chromium print engine** | Would inherit browser table selection | Unknown, huge visual change | Rejected: abandons the snapshot print profile, fonts, callouts, and catalog pipeline for a hunch |

Key structural insight behind the ranking: **anything that rewrites the
`Table` AST node into raw TeX (E, and naive forms of C/D) breaks two
existing contracts.** `code_catalog.lua` walks into `Table` cells to anchor
code blocks and URI links, and `return_links.lua` deliberately treats head/
foot/caption as pill-ineligible while keeping body cells eligible. A filter
that stringifies tables to `RawBlock` runs outside both walkers (depending
on filter order it either hides cells from them or carries already-placed
raw TeX into new blocks). Preserving those behaviors through a rewrite is
the bulk of the work in C/D/E — the TeX itself is the easy part. Option A
has no such hazard: it changes lengths and rules, never the AST, so the
text layer, anchors, pills, and catalog are provably untouched.

## 5. Critique of the plan ("improve table rendering somehow")

The goal is worth pursuing — tables are reference-dense content and the
complaint (can't cleanly highlight a cell) is exactly the kind of papercut
that decides whether Bryan annotates in Highlights or avoids tables — but
the plan as stated has four weaknesses, with adjustments:

1. **"Somehow" is doing too much work; reproduce first.** The failure mode
   ("app tries to select the cell") is a hypothesis about a closed-source
   app's gesture handling, and my text-layer probe says the PDF is clean.
   Without a Mac-side repro (fixed probe document × three gestures),
   we could ship a rework that changes nothing the app cares about.
   *Adjustment: gate every structural phase on the repro in §6.*
2. **Prevalence is unknown; size the fix to the evidence.** The repo has
   hard data on code blocks (449/538 reports, per
   `decisions:reference-sources-are-preserved-write-once`) but I found no
   equivalent table census. If 5% of references contain tables, Phase 0 +
   opt-in is the whole project; if 50% do, Phase 2/3 earn their keep.
   *Adjustment: add a corpus count (pipe/grid tables in `lib` sources and
   snapshot projected Markdown) as the Phase 1 exit gate.*
3. **The readability constraint should be load-bearing, not aspirational.**
   "Don't decrease readability" rules out the two most obvious
   highlightability wins (gridlines/zebra, linearization-by-default).
   *Adjustment: state it as a veto — any proposal that adds vertical rules,
   shrinks table type, or replaces tables by default fails review — and
   judge options against booktabs, not against tap-target size alone.*
4. **Don't touch the contract surface.** A new CLI flag (e.g.
   `--tables=linear`) would invoke `cli_rules.md` obligations (short alias,
   sorted help, excellent `-h` text) and a `docs.md` contract update for a
   preference that belongs in the document, not the command line.
   *Adjustment: no new flag. If an opt-in is needed, spell it in-document
   (fenced Div class or frontmatter key, defaulting to current rendering),
   so old documents render byte-identically and the choice travels with the
   source per `decisions:reference-sources-are-preserved-write-once`.*

One more scoping note: old PDFs must **not** be re-rendered for this. Sources
are preserved write-once and annotated PDFs carry coordinated-write
guarantees (`decisions:open-pdf-writes-are-coordinated`); bulk re-rendering
would churn digests, markers, and Highlights tabs for zero annotation gain
(the old highlights already exist). New renders get the new styling; history
stays byte-stable.

## 6. Recommended solution (phased)

**Phase 0 — ship unconditionally (header-only cosmetics, both pandoc
routes).** Add to `PANDOC_HEADER_INCLUDES` (`create.rs:61`) and to
`note.tex` (snapshot profile) the same small block:
`\renewcommand{\arraystretch}{1.35}`, a wider `\tabcolsep`, booktabs
separation (`\aboverulesep`/`\belowrulesep` breathing room), caption spacing
(`\abovecaptionskip`), and a header-row distinction that needs no new
package (e.g. slightly stronger header via the existing `\Bob…` sans/ink
treatment or letterspaced small-caps — not vertical rules, not shading, not
smaller type). No new `.sty`, so `RENDER_TEX_PACKAGES` and `bob ref doctor`
are untouched. Acceptance: `mutool draw -F txt/-F stext` on a table corpus
is byte-identical before/after (text layer provably unchanged), plus
eyeball review of one narrow, one wide/wrapped, and one multi-page table.
Verification: `just check` (fmt + clippy + workspace tests) and the
highlight/create CLI tests; per the daily-train decision
(`decisions:bob-cli-releases-ride-a-daily-train`) this rides the normal
train — no version/CHANGELOG edits by hand, no release PR.

**Phase 1 — measure and reproduce (gates everything else).**
(a) Corpus count of tables in reference sources; (b) Mac-side repro with a
fixed probe PDF (narrow table, wrapped-cell table, multi-page table ×
gestures: highlight one cell, one row, one column; record sidecar text for
each); (c) `mutool stext` block/line map of the same PDF to separate
app-heuristic failures from text-layer failures. If the repro shows
Highlights handles Phase-0 PDFs fine, stop — the project is done.

**Phase 2 — conditional opt-in linear fallback (only if Phase 1 shows a
real app-side failure).** A Lua filter that rewrites `Table`→headed
prose blocks **only** inside an explicit opt-in scope (e.g. a
`::: highlight-friendly` Div or a `tables: linear` frontmatter key;
default = today's visual table), running in the documented filter position
with `code_catalog`/`return_links` cell handling preserved or explicitly
re-decided (pills/anchors inside linearized cells must have a specified
home — likely: keep visual table's pill policy for the visual copy, plain
no-pill prose for the linear copy). Prefer **dual** (visual table first,
collapsed linear copy after, clearly labeled) over replacement, so
readability never regresses for non-annotating readers. Docs touch:
`docs/highlights-create.md` contract + guide steps, via `just docs-check`.

**Phase 3 — separate spikes, not part of this fix.** (i) Tagged-PDF spike:
`\DocumentMetadata{tagging=on}` + latex-lab table module on a branch,
checking pandoc-template interplay, TeX Live version floor (TinyTeX
rollout!), pagination churn, and — critically — whether Highlights changes
behavior on tagged tables at all. (ii) Table-catalog follow-up filed as its
own bead: extend the render-time catalog philosophy
(`decisions:code-copy-reads-render-time-catalog`) to table cells so exact
cell bytes are servable without trusting any PDF text layer.

**Explicitly not recommended:** default linearization, gridlines/zebra,
smaller table type, image tables, `tabularray` migration, article-engine
changes, new CLI flags, or backfill re-renders.

## 7. Files, risks, and verification for the implementer

- Touch: `src/native/highlights_ref/create.rs` (`PANDOC_HEADER_INCLUDES`),
  `src/native/highlights_ref/note_snapshot/note.tex` (mirror block),
  tests + fixtures for the three probe tables, `docs/highlights-create.md`
  only if Phase 2 happens (`just docs-gen`/`just docs-check` per `docs.md`).
- Do not touch: `Cargo.toml` version, `CHANGELOG.md` (train owns both),
  filter order, `Table` AST handling, `.bob` stores, marker/write paths.
- Risks: (1) `\arraystretch`/`\tabcolsep` shift pagination on dense
  documents — expected and acceptable, but snapshot overfull-warning
  thresholds (`>20pt` in `profile.rs`) should be re-checked on the corpus;
  (2) any Phase 2+ filter work must re-run the return-link pill tests
  (caption/head/foot ineligibility) and code-catalog link tests with tables
  in the fixtures; (3) Mac CI has no Swift-side impact (thin client —
  bob-first, app decodes later — but Phase 0/1 need no app change at all).
- Traceability: probe Markdown + `mutool` dumps in `/tmp` for this report
  (`/tmp/tableprobe/`); promote the corpus versions into the repo's test
  fixtures when Phase 0 lands.

