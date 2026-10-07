# Round-trip local links in `bob ref create` PDFs

> **Research query:** How should `bob ref create` render Markdown PDFs so a reader can follow
> a local link to another part of the document and then jump back to where they were? The
> proposal: find every local link, work out its target, add a unique alphanumeric ID to the
> rendered link text, and add a link at the target, labeled with the same ID, that returns
> to the original link. Lead the design so it is intuitive, reliable, and beautiful;
> critique the plan; adjust requirements where justified; end with a recommended solution.
>
> Researcher: cld (one of five in the swarm). Date: 2026-10-07.

## Bottom line

1. **Build it.** The idea is sound and well grounded in the data. 40% of the 291 rendered
   chat/research PDFs in `~/bob/lib/chat` contain working body links, 1,181 in total. 37%
   of their targets are linked from more than one place, up to 7 times
   ([survey](#how-local-links-are-used-today)). Highlights for Mac already has Back and
   Forward buttons. An in-document return still adds three things the viewer can't: it
   works on any device and survives detours, and it shows *who links here*
   ([critique](#critique-of-the-plan)).
2. **Use page labels, not IDs, as the return label (my biggest adjustment).**
   - Each target heading gets one right-aligned **return rail**: `↩ p.2 p.3 p.5`. Each pill
     jumps back to the exact link on that page.
   - Link text is **not** changed. Readers rarely remember an arbitrary ID at the moment
     they need it. They do know, or can see, the page they came from.
   - 95% of real back-references are uniquely identified by their page
     ([R1](#requirement-adjustments)).
3. **One rail per target, not one backlink per link.** Multi-inbound targets are common,
   so the rail aggregates every inbound link in reading order ([R2](#requirement-adjustments)).
4. **Return marks must not be text.** Apple PDFKit, which Highlights is built on, ignores
   `/ActualText` (verified on macOS 26.5). Text chips would therefore leak into Highlights
   quotes, `bob ref show`, and `--listen` narration ("The idea is sound 1 , and").
   Prototype pills and arrows are drawn as vector glyph outlines. All three extractors I
   tested (PDFKit, poppler, MuPDF) see nothing ([R5](#requirement-adjustments)).
5. **Fix resolution while we are here.** The filter resolves anchors the way authors
   meant them:
   - GitHub-style and Obsidian-style anchors, and raw `<a id>` anchors;
   - it reports any it still can't resolve.
   Today such links die **silently**: three links in this repo's own
   `docs/capture.md` are dead in the PDF, and the prototype rescued all three
   ([R3](#requirement-adjustments)).
6. **Get the details right:**
   - the return lands about two lines above the link, so the lead-in stays visible;
   - rail pills are 26×16 pt tap targets, not the 4–9 pt default;
   - a section that runs past a page also ends with a quiet end-of-section rail;
   - nothing leaks into the TOC or bookmarks;
   - layout never depends on page numbers, so references converge.
7. **It is cheap and contained.**
   - One pandoc Lua pass plus about 60 lines of LaTeX macros and ~10 KB of glyph data, all
     inside the existing Markdown route.
   - A 19-page report renders in ≈6.0 s instead of 5.3 s.
   - In the final variant, 32 corpus documents rendered with 0 failures, 0 page-count
     changes, and 0 stale references ([evidence](#prototype-evidence)).

The rest of this report backs these claims. It ends with the
[recommended solution](#recommended-solution).

## What exists today

### The Markdown route

`create_markdown_route` (`src/native/highlights_ref/create.rs`) runs pandoc once:

- XeLaTeX engine, `--toc --toc-depth=3 --number-sections`, `colorlinks=true`, DejaVu fonts,
  0.85 in margins;
- one embedded Lua filter (`PANDOC_CODE_BREAK_FILTER`: inline-code breaking plus the listen
  card) and one `header-includes` string (`PANDOC_HEADER_INCLUDES`: `fvextra` wrapping plus
  the listen-card macros), both written to the `0700` scratch directory;
- then `stamp_and_install` embeds the page-1 Highlights marker with lopdf and installs the
  file atomically.

Facts that shape the design:

- **Local links already work, partly.** Pandoc writes `[text](#id)` as `\hyperref[id]{text}`,
  and hyperref turns it into a GoTo link to the heading's named destination. There is no way
  back except the viewer's history.
- **Unresolvable links vanish silently.**
  - An unknown fragment becomes plain text, and LaTeX emits "Hyper reference … undefined".
  - bob discards pandoc's stderr when the render succeeds, so nobody sees the warning.
  - The common trap is GitHub-style slugs. `## 1. Summary` gets the pandoc id `summary`, but
    the GitHub slug is `1-summary`. In `docs/capture.md`, `[Picking any open task with
    ':'](#picking-any-open-task-with-)` is dead because pandoc's smart quotes change the
    heading text.
- **The default internal-link color is pandoc's `Maroon` (#800000)**: the template sets
  `linkcolor=Maroon` and loads xcolor with `svgnames` (I sampled #800000 in the renders).
  External URLs are blue. The listen card uses a separate blue (#3B6EA8).
- **bob already cleans PDF text for quotes.** `text.rs` (`clean_pdf_text_artifacts`) exists
  because Highlights quotes come straight from the PDF's text layer. Anything we add to that
  layer shows up in Bryan's annotations.
- **The research hook feeds this route.**
  `bob ref create --include-id <report>.md` renders every final research report. Changes
  here reach every future report automatically.

### How local links are used today

I scanned all 291 PDFs in `~/bob/lib/chat` with MuPDF. TOC links were excluded by skipping
as many leading internal links as the outline has entries, and line-wrapped fragments of one
link were merged:

| Measure | Value |
| --- | --- |
| PDFs with ≥1 body-local link | 115 of 291 (40%) |
| PDFs with ≥5 / ≥20 | 54 / 28 |
| Body-local links (logical) | 1,181 |
| Distinct targets | 735 |
| Targets linked from more than one place | 273 (37%) |
| Max inbound links on one target | 7 |
| Docs whose busiest target has 1/2/3/4/5/6/7 inbound | 66/9/15/17/3/2/3 |
| Max body-local links on one page | 25 (a reading list) |
| Links to footnotes, figures, tables, spans | 0 (every target is a heading) |

Recent final reports link heavily and correctly. `review_walk_answer_auto_advance.md` has 33
local links to 15 targets, and `#a4-details` is linked 7 times. Its links point at
pandoc-compatible ids. Most of them sit in tables ("A4 details below the table") or in
parentheses after a claim.

Reading and annotation are real. Of 292 chat ref notes, 272 are `finished`. 53 carry
Highlights annotations: 169 annotations and 95 comments.

### Viewers

- **Highlights for Mac** has had "back and forward buttons" since version 1.5 (15 Mar 2016)
  and a Go menu since 2020.3. Its changelog fixed internal-link navigation as recently as
  2025.1.2/2025.1.4.
- **Highlights for iPad/iPhone:** I could not confirm a Back button. The 2025.1 iPad entry
  only says navigation "now resemble[s] the macOS version in even more ways"
  ([open question 1](#open-questions-for-bryan)).
- **The PDF `GoBack` named action** works in Acrobat, Preview, and Skim, but not in PDFPen
  or browser viewers. That is a 2016 Prince forum test; Prince calls it "non-standard". It
  also depends on the viewer's history, which is exactly what may be missing.
- **PDFKit (verified on Kelly's MacBook, macOS 26.5):**
  - it resolves named destinations, including ones bob adds, through lopdf stamping;
  - `page.string` and `selection(for:)` **ignore `/ActualText`**;
  - it does not see vector-drawn marks at all.

## Critique of the plan

### Is it a good idea?

Yes, with a reframing. The value is not only "jump back".

1. **History-independent return.** Viewer Back is per-session and per-jump. It is gone
   after a reopen, and muddled after you scroll, annotate, or follow a second link. A
   printed-in return works on any viewer and device. It also works days later.
2. **Reverse navigation, which no viewer offers.** A rail tells you, at the target, that
   this section is referenced from pages 2, 3, 5, 7, 16, and 17. You can visit any of
   them, not just the one you came from. This is the PDF version of Obsidian's backlinks,
   or LaTeX `backref`'s "Cited on pages …".
3. **It costs the reader nothing when unused.** Done right, it adds no clutter to body
   text and no change to page count or text layer.

It is **not** a reason to drop the viewer's Back button. The two complement each other.

### Where the literal plan breaks

| Literal plan | Problem | Evidence |
| --- | --- | --- |
| Put a unique ID in the rendered link text | Every link gets visual noise (25 links on one page). Numbers collide with numeric link labels: reading lists link `#3`, `#10`, so you'd see `#3 ⁽¹⁷⁾`. | Survey; rendered prototype |
| Match return to source by ID | When a reader lands on `↩ 11 14 17 23 25 29 32`, they must remember which number they clicked. They usually didn't notice it. | `#a4-details` has 7 inbound |
| ID text in the PDF | IDs enter the text layer: Highlights quotes, `bob ref show`, and `--listen` narration. `/ActualText` does not help on PDFKit. | PDFKit `page.string`: "The idea is sound 1 , and" |
| One new link per original link at the target | Seven separate backlinks scattered at a heading. They need one aggregated place. | 37% of targets multi-inbound |
| "Search the Markdown for local links" | Text search misses reference-style links, and misreads code spans and fenced code. Pandoc, not bob, decides heading ids. | Pandoc AST is the source of truth |
| Silent on what it can't resolve | Dead links stay invisible, as today. | 3 dead links in `docs/capture.md` |
| Return "to the original link" | `\hypertarget` lands with the link line at the very top edge. In xdvipdfmx, hyperref links are glyph-sized: a 4×8 pt tap target. | PDFKit link rects measured |

The **pairing intuition behind IDs is right**. The reader needs to see which return belongs
to them. Page labels deliver that pairing with information the reader already has.

## Requirement adjustments

Each row is a deliberate change to the request. **R1** is the one that most changes what
you asked for.

| # | You asked | I recommend | Why |
| --- | --- | --- | --- |
| R1 | A unique alphanumeric ID in each link's text, repeated at the target | **Label returns by source page** (`p.5`). Leave link text unchanged. When a page holds several links to the same target, the pill returns to the first one. | The page is a coordinate the reader already has (page indicator, thumbnails, and `bob ref show` groups by page). An ID is a coordinate they must memorize. 241 of 253 real back-references (95%) are unique by page. The rest land on the right page. |
| R2 | One backlink per link, placed at the target | **One return rail per target**, listing every inbound link in reading order, right-aligned on the heading line | Multi-inbound targets are common (37%, max 7). One rail reads as an index, and scattered links read as noise. |
| R3 | "Figure out which part of the document they link to" | **Resolve like the author meant**: pandoc id first, then the GitHub slug, then heading text (Obsidian `#Heading%20Text`), plus raw `<a id>`/`<a name>` anchors. Report what's left. | Today dead links are silent. Aliasing rescued 3 of 3 dead links in `docs/capture.md`. |
| R4 | Return to "where they were originally" | Return lands **≈2 lines above** the link (`/XYZ null y null`), so the lead-in sentence is visible and horizontal scroll is kept | A dest at the link's baseline puts the line under the top edge. |
| R5 | IDs as "rendered link text" | **Return marks are vector art, never text** | PDFKit ignores `/ActualText`. Text marks pollute quotes and narration. |
| R6 | — | **Tap targets ≥ 26×16 pt** via explicit link rectangles | xdvipdfmx sizes hyperref links to drawn glyphs: 9×8 pt measured for a 2-digit chip, 4×8 pt for 1 digit. |
| R7 | Backlink at the target | Also an **end-of-section rail** for leaf sections that cross a page | People return when they *finish* the target section, which may be pages after the heading. |
| R8 | All local links | **Scope:** headings first (100% of today's targets); spans and divs get an inline or block rail. Exclude links inside headings (TOC and bookmark safety), the TOC itself, cross-file and external links. | Survey; TOC and bookmarks must stay clean. |
| R9 | — | **Per-document opt-out** `bob-backlinks: false` in frontmatter, and **no new CLI flag** | Keeps `ref create`'s surface unchanged (CLI rules). An escape hatch for odd documents. |
| R10 | — | **Don't use viewer `GoBack` actions** | Non-standard, and only works where the viewer already has a Back button. |

## Design

### What the reader sees

The source side is unchanged: the link is maroon text, exactly as today.

```text
  …the shipped D3 rule exists because one habitual extra Ctrl+Enter would close a real
  task (see A4 details below the table).
```

At the target heading, a quiet rail sits flush right on the heading's line:

```text
1.3.2   A4 details                                  ↩ [p.2] [p.3] [p.5] [p.7] [p.16] [p.17]
  • Ctrl+Enter never auto-advances across the checklist ↔ non-checklist boundary: …
```

If that section runs onto a later page, its end carries the same rail behind a short hairline.
It reads as a section terminator rather than as a heading's rail:

```text
  …last line of the section.
                                         ────  ↩ [p.2] [p.3] [p.5] [p.7] [p.16] [p.17]
1.3.3   A5 exclusions                                                     ↩ [p.2] [p.5]
```

Tapping `[p.5]` lands with the original link two lines below the top of the screen.

### Visual specification

- **Arrow:** `↩` (U+21A9), DejaVu Sans outline, 10 pt, ink #800000 (the internal-link color,
  so returns read as part of the same link family).
- **Pills:** `p.N` in DejaVu Sans outlines at 7.2 pt. Ink #800000 on a pale maroon tint
  (≈#F5E6E3), 1.6 pt corner radius. A fixed minimum width (fits `p.00`) keeps pills uniform
  and layout stable. Pills are 4 pt apart.
- **Placement:** the TeXbook "signed" glue (`\hfil\penalty50\hskip1em\null\nobreak\hfil`).
  The rail sits flush right on the heading's last line, or drops to its own flush-right line
  when the heading is long. It never squeezes the heading.
- **End rail:** drawn in a zero-height box in the space above the next heading, behind a
  2.2 em hairline in a lighter tint. It only appears when the section's end is on a
  different page than its heading. It adds no vertical space.
- **Spans and divs** (rare): an inline `↩ p.N` after the span, or a flush-right line at the
  top of the div.
- **Nothing changes in body text, the TOC, PDF bookmarks, page count, or the text layer.**

### How it works

One new pandoc Lua pass runs **before** the existing Meta/Code/Div passes. It works on the
AST, so pandoc's own id rules, reference-style links, and code spans are handled for free.

1. **Anchors.** Raw HTML `<a id="x"></a>` / `<a name="x">` become empty Spans with that id.
   The LaTeX writer would otherwise drop them.
2. **Index.** Register every canonical id first (headers, divs, spans, figures, tables, code
   blocks, images). Then add aliases: the GitHub slug (Unicode-aware: drops ASCII
   punctuation, smart quotes, dashes, arrows, and emoji; numbers duplicates `-1`, `-2` like
   GitHub) and the lowercased heading text. Aliases never shadow a real id.
3. **Rewrite.** For each `Link` whose target starts with `#`, outside headings:
   - percent-decode it and resolve it;
   - if resolved, number it n in reading order (footnote contents included);
   - rewrite the target to the canonical id;
   - prepend `\BobLinkSrc{n}`, a raised named destination `bob-src-n` plus `\label{bob-src-n}`;
   - if unresolved, keep the text and drop the link (today's behavior), and record it.

   Links inside headings are canonicalized but get no anchor or rail.
4. **Rails.** Append `\BobBacklinks{…}` to each target header (and the span/div forms).
   The argument lists `\BobBackChip{n}` for each inbound n.
5. **End rails.** Walk the top-level blocks. For a target header, insert
   `\BobEndRail{id}{…}` before the next heading **only if that heading's level is ≤ the
   target's**. A parent section continues into its children, so ending it there would stack
   two rails.
6. **Report.** Write JSON counts (links, resolved, aliased, unresolved fragments with their
   text) to the path in metadata `bob-link-report`. bob prints a summary line.

On the LaTeX side, each `\BobBackChip{n}` reads `\getpagerefnumber{bob-src-n}` (refcount).
It skips a page already listed in this rail, and draws the pill from glyph outlines:

- **Outlines:** the glyph outlines (digits, `p`, `.`, `↩`) are precomputed from DejaVu Sans
  with fontTools. They are stored as TeX macros holding PDF path operators.
- **Drawing:** a pill is assembled with `\fpeval` into one `\special{pdf:content …}`.
  That gives no glyphs and no text layer, and the box has zero height, so leading is
  unaffected.
- **Tap target:** each pill emits its own
  `\special{pdf:ann width … height 12pt depth 5pt << /Subtype /Link /A << /S /GoTo /D (bob-src-n) >> >>}`
  padded 2 pt on each side.
- **TOC and bookmarks:** `\pdfstringdefDisableCommands` and a wrapped `\tableofcontents`
  gobble the rail, so bookmarks and the TOC stay clean.

### Reliability rules

- **Layout never depends on page numbers.** Pills have a fixed minimum width, and end rails
  have zero height. Without this, 5 of 32 corpus documents finished pandoc's capped LaTeX
  reruns with "Label(s) may have changed", meaning their page labels could be stale. With
  it: 0 of 32.
- **The source text never changes.** Only a zero-size destination is inserted before the
  link.
- **Every return is a plain GoTo to a named destination.** That is the same mechanism every
  existing TOC and body link already uses in Bryan's library. PDFKit resolved them in the
  stamped file.
- **What the filter can't resolve, it says.** The success output gains
  `links: 33 return rails · 3 anchors rescued · 1 unresolved`, plus one
  `warning: unresolved local link #does-not-exist ("nowhere")` line per dead link.
- **The PDFKit iOS/macOS 27 beta write bug doesn't apply.** That forum thread is about
  PDFKit *writing* link destinations it created at runtime; destinations already in the
  file survive. bob's destinations are written by xdvipdfmx.

## Alternatives considered

| Option | Verdict | Why |
| --- | --- | --- |
| **A. ID chips (your plan)**: numbered pill after each link, matching numbered pills at the target | Viable fallback ([below](#if-you-prefer-id-chips)) | Exact pairing and a "you are here" mark on return. But it adds clutter, numeric collisions, and an ID the reader must remember. |
| Text chips with `/ActualText` to hide them | Rejected | PDFKit ignores ActualText. Quotes and narration get the digits. |
| Chips via TikZ `svg.path` outlines | Rejected | Correct but slow: 10.6 s vs 5.3 s. |
| Viewer `GoBack` button at each target | Rejected | Non-standard, viewer-dependent, and history-bound. |
| Post-process the PDF in Rust with lopdf (add link annotations and appearance streams) | Rejected | Can't typeset into the layout. Highlights treats annotations as user data. More code than a filter. |
| Margin notes (`\marginpar`) for rails | Rejected | The 0.85 in margin is too tight for 6–7 pills. It fails in tables and footnotes. It is tiny on a phone. |
| Forward page hints at the source (`see A4, p. 7`) | Not now | The classic print convention, but it adds the source clutter R1 avoids. The tap already gets you there. |
| Render via HTML and Chromium (like web clips) | Rejected | A rewrite of a route that works. |

### If you prefer ID chips

If you value exact pairing and the "you are here" mark over clean link text, the prototype
supports a precise ID variant at the same quality bar:

- after each link text, a small raised pill with the link's number in reading order
  (5.9 pt, vector, not text);
- at the target, `↩ 11 14 17 23 25 29 32`, each pill a 19×16 pt tap target;
- the Lua filter draws pills as raw PDF paths, so IDs are known at filter time. Layout is
  page-independent, so it converges like today.

It rendered the 19-page report in 6.1 s, with clean text in PDFKit, poppler, and MuPDF. The
one wart: xdvipdfmx doesn't extend the link's tap area over a vector chip. Each chip would
need its own small link annotation to the same destination.

## Prototype evidence

Everything below ran on athena (pandoc 3.1.11.1, XeTeX/TeX Live 2025) with bob's exact pandoc
flags and existing filter. PDFKit checks ran on `mac` (macOS 26.5) with a Swift probe.

| Variant | Reader sees | Render, 19-page report | Text layer (PDFKit) | Converges |
| --- | --- | --- | --- | --- |
| Baseline (today) | — | 5.3 s | — | yes |
| ID chips, TikZ pills, text digits | chips + numbered rail | 7.4 s | digits leak, with or without ActualText | yes |
| ID chips, TikZ SVG outlines | same | 10.6 s | clean | yes |
| ID chips, raw PDF outlines from Lua | same | 6.1 s | clean | yes |
| **Page-label rails, raw PDF outlines (recommended)** | rails only | **≈6.0 s** | **clean; link text untouched** | **yes**, after the layout-invariance rule |

More checks:

- **Corpus:** 32 Markdown files: 22 `docs/*.md`, the 3 most recent final research reports,
  6 older numbered-heading reports, and 1 synthetic edge-case file. Final variant results:
  - 0 render failures and 0 page-count changes against baseline;
  - 0 "Label(s) may have changed" warnings;
  - all 253 real local links resolved (3 via GitHub-slug aliases).
- **Edge file:** GitHub-style `#2-current-state`, Obsidian `#4.%20Open%20questions`, a span
  target, a div target, a raw `<a id>` anchor, a link inside a table, a link in a footnote, a
  link inside a heading, and a dead link. Results:
  - every live link round-trips;
  - the heading link is canonicalized with no rail;
  - the dead link is reported;
  - the TOC and bookmarks contain no rail text.
- **End-to-end through the real `bob ref create`.** A `BOB_PANDOC_COMMAND` wrapper swapped in
  the prototype filter (ID-chip build, same `pdf:dest`/`pdf:ann` mechanism). The lopdf-stamped
  intake PDF kept all 65 local links. PDFKit resolved each return to the right page and
  position. bob's success output dropped the filter's stderr summary, which is why the
  report must go through a file.
- **Tap targets (PDFKit link bounds):**
  - hyperref default: 9×8 pt (4×8 pt for one digit);
  - explicit annotation: 26×16 pt per page pill.
- **Landing:** each return destination is raised 2.2 baselines, with left = null. PDFKit
  reports the destination point above the link line, as intended.
- **Same-page duplicates:** across the real corpus, 241 of 253 back-references are on a page
  no other link to the same target shares. 9 rails have a duplicate.

## Implementation plan

**Files** (all inside the Markdown route):

- Move the filter and header out of the Rust raw strings into
  `src/native/highlights_ref/pandoc/`, loaded with `include_str!`:
  - `bob.lua`: today's Meta/Code/Div passes, unchanged;
  - `backlinks.lua`: the new pass, run first;
  - `backlinks.tex`: the ~60 lines of macros;
  - `glyphs.tex`: generated outlines for 0–9, `p`, `.`, `↩`, ≈7 KB, with a header naming
    the generator.
- Add `scripts/pdf_glyphs.py`, a one-shot fontTools generator, run by hand only if the font
  ever changes.
- `create.rs`:
  - concatenate the filters in order, and append `backlinks.tex` + `glyphs.tex` to
    `PANDOC_HEADER_INCLUDES`;
  - pass `-M bob-link-report=<scratch>/links.json`;
  - after render, read the report and print the `links:` line plus one `warning:` per
    unresolved fragment;
  - if pandoc's stderr still contains "Label(s) may have changed", print one warning.

**Order of work:**

1. Resolution and reporting first: aliases, anchors, the JSON report, and warnings. This
   alone fixes the silent dead links.
2. Return anchors and heading rails.
3. End rails and the span/div forms.
4. The opt-out (`bob-backlinks: false` read in `Meta`) and docs.

**Tests** (pandoc-gated and xelatex-gated, like the existing listen-card tests):

- `-t latex` output: `\BobLinkSrc{1}` before a resolved link, `\BobBacklinks{` on its
  target, no rail on a heading that contains a link;
- alias resolution: GitHub numbered heading, smart-quoted heading, Obsidian `%20`, raw
  `<a id>`; exact id beats alias;
- report JSON counts and unresolved fragments;
- PDF via lopdf:
  - a `bob-src-1` named destination exists;
  - a GoTo to it exists with a rect ≥ 20 pt wide;
  - outline titles contain no `↩`/`p.`;
  - text extraction of the heading page contains no rail text;
- no "Label(s) may have changed" in stderr for a ≥10-page fixture with end rails.

**Docs:**

- a new "Local links" section in `docs/highlights-create.md`: behavior, aliasing, the report
  line, the opt-out, and the rail anatomy;
- one sentence in `bob ref create -h` "Output:" (currently "Pandoc renders TOC/bookmarks…").

**Effort:** about a day for the Lua and TeX (the prototype exists), half a day for Rust
plumbing, tests, and docs.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| A future layout tweak makes rails page-dependent again, so labels go stale | The convergence test. bob warns when pandoc's last run still says "Label(s) may have changed". |
| 100+ page documents widen pills past `p.00` | Rare (chat PDFs are 2–72 pages). At worst one extra rerun; the warning covers it. |
| TeX features: `refcount`, `\fpeval` (LaTeX ≥ 2022-06), xdvipdfmx `pdf:` specials | All present in TeX Live on athena. The engine is already hard-wired to XeLaTeX. Specials live in three macros. |
| Pandoc Lua API drift | Uses only `walk`, `pandoc.Blocks/Inlines`, `pandoc.text`, `utf8` (pandoc ≥ 2.17; athena has 3.1.11). |
| Manual-TOC documents (`docs/capture.md`) get a rail on every heading | That's a feature: each section's `↩` returns to its contents entry. |
| Highlights on iPad behaves differently from PDFKit on macOS | Same framework. Verify with one document before rollout ([open question 1](#open-questions-for-bryan)). |

## Adjacent findings

These are not part of this feature, but they are on the same "beautiful PDF" path.

- **Heading numbering is off in most rendered reports.**
  - 239 of 291 PDFs number every section `1.x`: the H1 title becomes section 1, and the same
    title also appears in the title block.
  - 147 of 291 are double-numbered, as in `1.2 1. Evidence`: manual numbers plus
    `--number-sections`.
  - Possible fix: `--shift-heading-level-by=-1` when the document's only H1 is its title,
    and skip `--number-sections` when headings are already numbered.
  - This deserves its own change. The R3 aliasing makes GitHub-style anchors to manually
    numbered headings work either way.
- **Pandoc warnings are discarded on success.** The link report covers links. Other
  warnings stay invisible, such as missing glyphs: emoji in DejaVu fonts render as blanks.
  They could get a one-line "pandoc: N warnings (BOB_HIGHLIGHTS_KEEP_WORKDIR=1 to inspect)"
  summary.

## Open questions for Bryan

1. On your iPad, does Highlights show a Back button after you tap an internal link? This
   doesn't change the design, but it tells us how much the rails matter there.
2. **R1:** are you happy with page labels instead of IDs? If not, the
   [ID-chip variant](#if-you-prefer-id-chips) is ready at the same quality bar.
3. Same-page duplicates: is one pill per page enough, or do you want `p.17a`/`p.17b` pills
   that return exactly to each of the 5% of links that share a page?

## Recommended solution

Ship **page-labeled return rails** in the Markdown route of `bob ref create`, as one new pandoc
Lua pass plus LaTeX macros:

1. **Resolve every local link the way its author meant it.**
   - Resolve pandoc ids, then GitHub slugs, then heading text, plus raw `<a id>`/`<a name>`
     anchors.
   - Rewrite links to canonical ids.
   - Report the rest. Dead links stay plain text and print a `warning:` line; the success
     output gains `links: N return rails · M anchors rescued · K unresolved`.
2. **Leave link text alone.** Before each resolved link, plant a raised (≈2 lines), zero-size
   named destination with horizontal scroll kept.
3. **Give every linked heading one flush-right return rail.**
   - The rail reads `↩ p.2 p.3 p.5`, in reading order, one pill per source page.
   - Each pill is a 26×16 pt tap target that returns to the exact link.
   - Everything is drawn as DejaVu Sans vector outlines in the internal-link maroon, so
     nothing enters the text layer, Highlights quotes, `bob ref show`, or narration.
4. **End a leaf section that ran past a page with the same rail**, behind a hairline, in zero
   vertical space.
5. **Keep everything else unchanged and stable.**
   - Exclude links inside headings, the TOC, bookmarks, and external and cross-file links.
   - Keep layout independent of page numbers so references converge.
   - Allow `bob-backlinks: false` in frontmatter as the only opt-out. Add no CLI flag.
6. **Test and document it.**
   - Test with pandoc/xelatex-gated unit tests and lopdf PDF assertions, including a
     convergence check.
   - Document it in `docs/highlights-create.md` and the `ref create` help text.

It keeps your core idea: a visible, matching return at the target that jumps back to the
exact link. It swaps the memorized ID for the page the reader already knows. It fixes
today's silent dead links along the way. On the measured corpus it changed no page counts,
no text, and no TOC entries, and cost about 0.7 s per render.
