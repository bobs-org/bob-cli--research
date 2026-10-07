# PDF backlinks for `bob ref create` markdown renders — research (`__mus`)

## TL;DR

The proposed feature is worth building, but not exactly as specified. Pandoc
already renders every `#anchor` markdown link as a working forward hyperlink in
the PDF (`\hyperref`, verified below) — so the only missing half is the way
back. I verified with a prototype Lua filter that a true position-accurate
"jump back" is achievable with AST-only changes and **no LaTeX preamble work**:
wrap each outbound internal link in an identified `Span` (pandoc emits
`\phantomsection\label{…}` around it — a genuine return anchor), tag the link
text with a small marker, and append matching return links at the destination.
Recommend building exactly that, inside the existing
`PANDOC_CODE_BREAK_FILTER`, with the adjustments in §5. The raw-alphanumeric-ID-
in-body-text part of the proposal should not ship as described — §4 explains
why, and §6 gives the beautiful version.

## 1. What the pipeline does today (verified, not assumed)

All claims below were verified against the actual code and toolchain in this
workspace on 2026-10-07 (pandoc 3.1.11.1, xelatex present).

- Markdown route: `src/native/highlights_ref/create.rs`, `render_temp_pdf()`
  shells out to pandoc with `--standalone --toc --toc-depth=3
  --number-sections --pdf-engine=xelatex -V colorlinks=true`, plus one
  `--lua-filter` (`PANDOC_CODE_BREAK_FILTER`, embedded string at the top of
  `create.rs`) and the `header-includes` preamble (`fvextra`, listen-card
  macros). Any backlink work slots into this exact invocation.
- There is already a Lua-filter precedent that rewrites links for PDF: the
  `Div` handler **deletes relative-file links** (`is_relative_target`) from
  listen cards, trimming the `·` separator so the output still reads cleanly.
  A backlink filter follows the same pattern and can live in the same file.
- Internal-link behavior today (verified by rendering a probe document):

  | Markdown | LaTeX pandoc emits | PDF result |
  |---|---|---|
  | `[text](#heading)` | `\hyperref[heading]{text}` | Working forward jump, free |
  | `[text](#missing)` | `\hyperref[missing]{text}` | Dangling: target does not exist |
  | `[text](other.md)` | `\href{other.md}{text}` | Dead file link in a standalone PDF |
  | `[text](https://…)` | `\href{https://…}{text}` | Works, untouched by this feature |
  | TOC entries | generated at render, not AST `Link`s | Unaffected by any AST filter — good |

- Prototype result 1: a `Link → { Span(el, {id=…}) }` rewrite emits
  `\phantomsection\label{ref-bl001}{\hyperref[b]{go}}` — i.e. wrapping an
  outbound link in an identified Span creates a **real return anchor at the
  exact link site**, with zero preamble changes.
- Prototype result 2: a two-pass filter (tag outbound `#links`, then append
  return-link paragraphs at matching `Header` identifiers) produces working
  bidirectional markup. It also surfaced every edge case in §4 — including
  one outright bug in my first draft (return links `#ref-…` emitted before I
  had created the anchors), which is why the recommended design below does
  anchor creation and link tagging in a single pass.

## 2. Is this a good idea?

Yes, with the adjustments in §5. The motivation is sound: these PDFs are
*annotated* in the Highlights app, and annotation-focused PDF readers are
exactly where "forward link works, now I'm stranded" hurts most — desktop
Acrobat-style history-back either doesn't exist or isn't discoverable there,
and on paper-equivalent reading flows there is no back button at all. The
forward half of the problem is already solved by pandoc, so the feature is
small, additive, and low-risk: worst case (filter bug) degrades to today's
behavior, never to an unrenderable PDF, provided the filter is written
defensively (nil-check every target, never fail the render — log and skip).

## 3. Approaches considered

1. **Do nothing; rely on viewer history-back.** Rejected: the target readers
   (Highlights macOS/iOS) are the weakest viewers for history navigation, and
   printed copies get nothing. Zero implementation cost, zero benefit where
   it matters.
2. **Regex preprocessing of the markdown source.** Rejected: fragile against
   code spans/blocks, reference-style links, headings containing formatting,
   and duplicate heading slugs. Pandoc's AST already resolves all of these
   (including `auto_identifiers` slugging and explicit `{#id}` attributes) —
   matching that resolution with regexes reimplements pandoc badly.
3. **Pure LaTeX-side solution (`backref`-style, `zref`, custom
   `\hyperlink`/`\hypertarget` preamble).** Rejected as primary mechanism:
   it fights pandoc's generated `\hyperref`/`\label` scheme instead of riding
   it, needs preamble surgery, and still can't enumerate "which links point
   here" without AST knowledge. Keep the preamble untouched.
4. **Footnote/endnote "link index"** (collect all internal links into an
   appendix). Rejected: it answers "where can I go" rather than "how do I get
   back," adds pages, and duplicates the TOC's job.
5. **AST Lua filter: per-link return anchors + destination return links
   (recommended).** It operates where the information lives (pandoc knows
   every link target and every header identifier), reuses the existing filter
   file and its test pattern (`--to=latex` assertions, cf. the `code_break`
   and `listen-card` tests in `create.rs`), and degrades gracefully.

## 4. Critique of the proposal as written

- **Raw alphanumeric IDs as visible link text are ugly and hurt readability.**
  `see the method [a1b2]` burdens every reader with machinery that serves
  only the few who follow that link. IDs should be present but visually
  subordinate: a small superscript marker in the link color, not a body-size
  token. The ID's job is disambiguation (several links can share one target),
  and a 2–3 character superscript does that job.
- **"Figuring out which part of the document they link to" needs a precise
  definition.** Pandoc targets resolve to: (a) a `Header` identifier
  (auto-slugged or explicit `{#id}`), (b) a `Span`/`Div` identifier anywhere
  in the body, or (c) nothing (dangling). "The destination" is therefore
  *the identified block*, not "the section" — return links must attach to
  whatever block owns the identifier, with headers merely the common case.
- **The return anchor must be created, not assumed.** The proposal says the
  destination gets "a new local link … that links back to the original link"
  — but the original link site is not itself a link target until the filter
  makes it one. This is the load-bearing step (§1, prototype result 1): wrap
  each outbound link in `Span{id="bob-ref-<n>"}`. Without it there is no way
  back to the reader's position, only back to the enclosing section.
- **Placement matters more than the proposal suggests.** A return-link
  paragraph inserted *between a heading and its first paragraph* (what the
  naive implementation does) reads as layout damage. Return links belong
  either trailing the destination block's content or floated right on the
  heading line.
- **Unbounded backlink lists.** A heavily-linked-to section ("see §Method"
  × 12) would grow a 12-item return cluster. Cap the visible cluster with a
  deliberate overflow rule.
- **Dangling targets must not get markers.** Tagging `[x](#nope)` with an ID
  promises a round trip that doesn't exist. Dangling links should render
  unchanged (or with a build warning listing them) and receive no marker and
  no return entry.
- **Scope: only `#fragment` links.** Relative-file links (`other.md`) are
  dead in a standalone PDF and the existing filter already strips some; bare
  `#` (self-link) and bare URLs are out of scope. TOC entries are
  auto-generated and self-excluded.

## 5. Adjustments to the requirements (explicit)

1. **Visible marker, not visible ID.** Outbound marker: superscript
   `↩n` (U+21A9 + small sequential number, link-colored, e.g.
   `the method`^`↩1`). Return marker at destination: matching superscript
   `↩n` hyperlinked to `#bob-ref-n`. Sequential per-document numbers are
   prettier and shorter than random alphanumerics; uniqueness scope is one
   document, so randomness buys nothing. (If stable-across-edits IDs are ever
   needed for external cross-references, revisit — not this feature.)
2. **Return anchor = wrapped outbound link.** Each tagged outbound link is
   wrapped in `Span{id="bob-ref-<n>"}` in the same pass that tags it, so
   anchor and marker can never disagree.
3. **Destination = owning block, placement = trailing.** Return cluster goes
   at the end of the destination block's content (for headers: end of the
   section's last block before the next header — implement as: append to the
   section by inserting after the final block belonging to that header's
   span, or pragmatically, immediately after the header in a right-aligned
   small line if section-end insertion proves fiddly; prototype both and pick
   the prettier). Style: `\small`, link color, right-aligned or trailing,
   prefixed with a hairline or `·` separators.
4. **Overflow rule.** Show at most 5 return markers per destination; beyond
   that render `↩1 ↩2 … ↩5 ⁺³` where `⁺³` links to the *first* return site
   (documented behavior, not silent truncation).
5. **Dangling-link policy.** Links whose fragment matches no identifier in
   the document: no marker, no return entry, plus a pandoc `io.stderr` warning
   naming target and source line context so authors can fix them. Never fail
   the render for this.
6. **Exclusions.** TOC (automatic), links inside headings (tagging there
   would put markers in the TOC/bookmarks — skip outbound links that occur
   inside a `Header`'s own inlines), `listen` Div cards (existing dead-link
   stripping runs first and wins on conflict), code spans (not `Link`s anyway).
7. **No preamble or CLI changes.** No new flags, no new dependencies, no
   `header-includes` edits. The whole feature is ~60 lines of Lua in the
   existing filter string plus tests. If a future beauty pass wants custom
   LaTeX styling of the cluster, *then* add one `\newcommand`, not before.

## 6. Recommended solution (beauty spec included)

Extend `PANDOC_CODE_BREAK_FILTER` in `src/native/highlights_ref/create.rs`
with a backlink pass (single filter file, ordering: dead-link stripping
first, backlinks second, code-break/listen rendering unchanged):

- **Pass A (walk all `Link` inlines with targets starting `#`, length > 1,
  outside `Header` inlines and outside `listen` Divs):** assign `n = ++counter`;
  wrap in `Span{id="bob-ref-n"}`; append `Superscript{Str("↩n")}` to the link
  content; record `fragment → [n…]`.
- **Pass B (walk top-level blocks; resolve each recorded fragment to the
  block owning that identifier — `Header`, `Div`, or `Span`-bearing block):**
  append a trailing return cluster `↩n₁ · ↩n₂ …` where each marker links to
  `#bob-ref-nᵢ`, capped per §5.4. Unresolvable fragments: stderr warning,
  link left as pandoc rendered it (strip the marker if Pass A already added
  one — hence do resolution *before* mutation, or two full walks with a
  resolve-first pass).
- **Visual design:** markers inherit the surrounding link color (`colorlinks`
  already paints internal links Maroon); superscript sizing keeps the body
  copy clean; the destination cluster is `\small`, right-aligned, and reads
  as a quiet marginal note — e.g. a right-aligned line `↩1 · ↩2` tucked
  against the end of the destination section. Nothing in body size, nothing
  alphanumeric, nothing that survives as noise for readers who never click.
- **Verification:** (1) unit tests in the existing style — render probe docs
  with `--to=latex` and assert `\label{bob-ref-1}`, matching superscript
  markers, return-link presence, dangling-link silence, TOC cleanliness, and
  the >5 overflow form; (2) one real XeLaTeX PDF build of a multi-link
  document, opened in a viewer, clicking forward and back; (3) confirm the
  lopdf stamp round-trip (`stamp_pdf_to_scratch` verifies page count, not
  annotations — spot-check that GoTo annotations survive stamping, since a
  stamp that ate internal links would silently void this feature).
- **Known residual risks:** Highlights' iOS renderer is the least
  predictable link consumer — test one output PDF there before declaring
  victory; duplicate auto-generated header slugs (`method`, `method-1`) are
  handled by pandoc's identifier assignment, but authors should prefer
  explicit `{#id}`s on frequently-linked headings (worth one line in the docs).

## 7. Suggested implementation order

1. Resolve-first two-walk Lua pass in the existing filter string (no CLI,
   no preamble changes).
2. `--to=latex` assertion tests mirroring the current filter tests.
3. Beauty pass on the cluster placement (trailing-vs-heading-line prototype
   comparison on a real PDF).
4. Highlights macOS + iOS spot-check, stamp round-trip check.
5. One-paragraph addition to `docs/highlights-create.md` documenting marker
   meaning and the dangling-link warning.

*Report: independent research by mus; methods and conclusions my own. Evidence:
repo source (`src/native/highlights_ref/create.rs`, `docs/highlights-create.md`)
plus live pandoc 3.1.11.1 rendering probes run during this session.*
