# Section annotations for ref notes (`# <name>` + `@<name>`): research & recommendation

Researcher: mus. Scope: how `bob ref` turns Highlights PDF annotations into
Obsidian ref notes today, what the proposed "section annotation" feature would
touch, what's good and risky about the proposal as stated, and a recommended
design. All code citations are against the local `bob-cli` checkout
(`src/native/highlights_ref/`); the linked `bob-mac-capture` repo was not
inspected (no cross-repo tool available in this session), so claims about the
Refs panel below are grounded in `bob-cli`'s own docs and JSON contracts, and
the one point that needs Mac-side confirmation is flagged explicitly.

## TL;DR

- The feature is a good idea and fits an established pattern: `bob ref` already
  does **stateless, render-time grouping** twice (continuation `<` groups,
  underline-emphasis folds). Section grouping should be the third fold, reusing
  the same machinery and invariants.
- The proposal as stated has one real collision (`@<name>` vs the existing
  `@route` task-routing suffix), one pleasant surprise (a bare `# <name>`
  sticky note is **currently dropped** by the sidecar parser, so section
  definitions need no migration for the common case), and one hard rendering
  constraint (member blocks must stay byte-identical callouts with column-0
  `^h-…` IDs, which rules out a wrapper-callout design).
- Recommended: **heading-based sections rendered at the definition's position**
  (`### <Name>` + optional description + unchanged member blocks), derived
  fresh from the sidecar on every scan, members keep their block IDs, `@tag`
  stripped from rendered comments, dangling tags left visible, route suffix
  wins on `#task` lines, section anchors as stable `^h-section-…` IDs,
  `Removed highlights` stubs only for defs that were previously visible,
  additive scan-JSON fields, and a small CSS snippet for beauty. Details in
  §6.

## 1. How ref-note rendering works today

`bob ref sync` / `bob ref scan` rewrite **only the managed region** of the ref
note (between the Highlights begin/end markers; `note.rs:managed_region`,
`replace_managed_region`). Everything outside is preserved; user edits *inside*
the region may be overwritten. This is the single most important constraint:
anything the feature persists must be re-derivable from the sidecar on every
scan, because the region is regenerated, not patched.

The render pipeline (`sidecar_render.rs:render_sidecar_highlights`):

1. Parse the Highlights TextBundle/Markdown sidecar into `SidecarAnnotation`s
   (`sidecar.rs:parse_sidecar_markdown`), each a `Highlight`, `Image`, or
   `StandaloneNote` (`model.rs`), ordered by sidecar (sidebar) order.
2. Compute **folds**: `plan_annotation_folds` produces an `UnderlinePlan` plus
   a `ContinuationPlan` (`underline.rs`, `continuation.rs`).
3. Render in sidecar order under `### <page>` headings (`push_page_heading`):
   highlights as `> [!quote]` callouts, highlight/image comments nested as
   `> > [!note] Comment`, standalone notes as `> [!note]`, one trailing
   column-0 `^h-…` block ID per block (`render_annotation_block`,
   `render_highlight_group_block`).
4. Append `### Removed highlights` tombstones for previously published blocks
   that disappeared or were absorbed (`[!warning] Removed highlight`,
   `[!info] Grouped highlight`, `[!info] Merged emphasis` redirect stubs).

Block IDs are content-addressed and deliberately comment-insensitive:
`stable_base_block_id` hashes `source_pdf + kind + page_label + normalized
text`, where `identity_quote_key` strips return-link glyphs, beautifies,
removes `**`, and collapses whitespace — and `identity_comment_key` exists
only as a duplicate tiebreaker, so **comment edits alone never change the
block ID** (`sidecar_render.rs:841-937`). The continuation precedent adds the
group invariant: *the head `^h-` ID is unchanged with or without followers,
and the follower ID is the same grouped and ungrouped*, so existing
`[[#^h-…]]` links and task 🔖 links survive grouping via redirect stubs.

## 2. The two existing grouping precedents (follow these)

**Continuation `<` groups** (`continuation.rs`, documented in
`docs/highlights-ref-sync.md#continuation-highlights--`): a note starting with
`<` on a *later* text highlight folds it into the nearest earlier text
highlight. Grammar notes worth copying: first-nonempty-line scan, one optional
list prefix stripped, token must be followed by whitespace/EOL, `\`-escape,
`<…`/`<...` spellings, dangling markers stay visible verbatim, and the marker
is stripped from the rendered comment. Groups render at the head's position as
nested `[!quote|<page>]` callouts with a CSS snippet drawing the dashed seam
and page caption. Scan JSON reports `continuations` /
`continuations_dangling` (omitted when zero, `schema_version` stays 1), and
dry-run prints `continuations:` lines.

**Underline folds** (`underline.rs`): a `**…**`-wrapped underline merges into
its host quote as a `**` run when its cleaned text occurs exactly once in
exactly one same-page highlight; otherwise it stays standalone with a
dry-run reason (`no highlight around it`, `inside N highlights`, `text
repeats inside its highlight`). Absorbed underlines are never tombstoned; a
`Merged emphasis` stub appears only if the old ID was published *and* is
still linked or already tombstoned.

Both precedents agree on the architecture section grouping should copy:
**parse → plan (pure function of sidecar + existing note) → render**, no PDF
or sidecar writes, no state beyond what the next scan recomputes.

## 3. Critique of the proposal as stated

**3.1. `@<name>` collides with `@route` task routing — the one real problem.**
`annotation_tasks.rs:strict_annotation_task_route_name` already gives meaning
to a trailing `@token`: on a `#task` line, `@name` routes the task to the
root note `name.md`, and `route_name_to_note_path` **hard-errors the whole
PDF's sync** if that note doesn't exist. So `- #task Fix it @methods` today
means "route to `methods.md`", and would fail if that file is missing. If
`@methods` simultaneously means "member of section Methods", one line has two
meanings and one of them errors. Mitigation (recommended in §6): membership is
recognized on non-task lines/lines without `#task`; on `#task` lines the
route wins; members that need both put the `@section` on its own comment
line — which is safe because the task parser only fires on list-item lines
*containing* `#task` (`annotation_task_source_from_item`), so a bare
`- @methods` line is ignored by the task pipeline entirely. Multi-word
section names (e.g. `@causal inference`) can *never* collide since route
tokens are single `alnum+(_|-)` tokens — a further reason to encourage
display-style names.

**3.2. Pleasant surprise: `# <name>` defs are nearly free.** `parse_sidecar_chunk`
(`sidecar.rs:295-304`) drops chunks whose lines are *all* Markdown headings,
and strips heading lines from mixed chunks. So a sticky note containing only
`# Methods` **currently vanishes** (renders nothing, mints no block ID —
nothing to tombstone later), and `# Methods\n\n<description>` currently
renders as a plain `[!note]` of the description text. The proposed def form
therefore needs no migration for the pure case; only description-carrying defs
change rendering (old `[!note]` block → new section heading, which needs a
redirect stub — the machinery already exists).

**3.3. Persistence must be derived, not stored.** The request says "think hard
about the best way to persist and render this grouping." Given the managed
region is regenerated wholesale, the only sane persistence *is the sidecar
itself*: the `# <name>` def notes and `@<name>` tags re-derive the grouping
every scan, exactly like `<` markers. No frontmatter, no sidecar writes, no
`source_id`-style hidden state. Deleting the def or the tag dissolves the
group — matching the `<` mental model ("deleting the `<` removes the group").

**3.4. Rendering must not wrap members in a parent callout.** I checked
`region.rs:region_block_id`: block IDs are found via `line.trim()` +
`^`-prefix, and — critically — a member `^h-` nested as `> ^h-…` inside a
section callout would no longer parse as that member's trailing ID, while a
column-0 `^h-` after nested content would attach to the whole section block,
corrupting per-member identity, `generated_block_ids`, tombstoning, and every
task 🔖 link. The continuation design already solved this by keeping pieces
as *sibling* callouts with one shared column-0 ID; sections have multiple
independent members each needing their own ID, so the correct shape is
**headings, not wrappers**: `### <Name>` + description + member blocks
rendered byte-identical to today. Beauty then comes from the heading treatment
plus CSS, which degrades gracefully everywhere (see §6.5).

**3.5. Page headings need a decision.** Members of one section will often span
pages, but `push_page_heading` emits `### <page>` per page today. Sections and
page headings are both `###` by default — fine (siblings under `## Highlights`),
but the interaction needs a rule: when a section is open, suppress per-member
page headings and show the page on each member some other way (the
`[!quote|<page>]` labelled-callout style from continuation groups already
exists for exactly this), or re-emit page headings inside sections. Recommend
the former: quieter, and it reuses the labelled-quote convention readers
already know.

**3.6. The `@tag` must be stripped from rendered output, and dangling tags
must stay visible.** Copy the `<` contract: consumed markers disappear from
rendered comments (otherwise every member advertises its plumbing); tags with
no matching def render verbatim so a typo is discoverable, with a dry-run
diagnostic (`section_dangling: @name (<page>)`). Never silently drop.

**3.7. One section per annotation.** Allowing an annotation in N sections
multiplies render/identity/stub complexity for a case nobody needs. First
defined-name match in document order wins; extra tags stay literal (visible,
honest). Call this out in docs.

**3.8. Forward references should resolve.** Unlike `<` (positional — "the
nearest earlier highlight"), `@name` is a global key. Resolve membership
against *all* defs in the sidecar regardless of order, so `@methods` works
even if the `# Methods` sticky sits later in sidebar order. Positional
sensitivity here would be pure footgun.

**3.9. Duplicate defs and empty sections need rules, not errors.** Two `# Foo`
stickies (easy when annotating a long PDF on two days): merge members, first
description wins, dry-run warning. A def with no members: still render the
heading + description (it's an explicit gesture, cheap to delete) and count it
in dry-run. Failing a whole PDF over section bookkeeping would violate the
pipeline's "per-PDF failures never stop unrelated PDFs, and trivia never
fails a PDF" ethos.

## 4. Options considered

| Approach | Shape in the note | Verdict |
|---|---|---|
| **A. Heading-based sections** (`### Name` + unchanged member blocks) | Siblings under `## Highlights`; member callouts + column-0 `^h-` IDs byte-identical | **Recommend.** Zero risk to identity/stub/task-link machinery; portable Markdown; CSS beautifies. |
| B. Wrapper callout (`> [!example]+ Name` containing members) | Members nested one depth deeper; IDs must nest or re-anchor | Reject: breaks `region_block_id` parsing and per-member link targets (§3.4); deep nesting reads poorly on mobile. |
| C. Persist grouping in frontmatter/sidecar writes | Stable section IDs stored on the note or PDF | Reject: fights the regenerate-the-region architecture; sidecar writes risk Highlights sync conflicts; state to migrate forever. |
| D. Obsidian tags/properties (`#section/methods`, `section:` frontmatter) | Query-based grouping via Dataview/boards | Reject as the mechanism (fragile, Obsidian-only, invisible in Mac app and `cat`), though a `sections:` note-level index could be a later additive extra. |
| E. Reuse page-heading level per section with members under `####` pages | Inverts the current hierarchy | Reject: churns every existing note's heading structure; `### Page` headings are load-bearing for readers and possibly the Mac panel. |

## 5. Granularity answers (member kinds, nesting, scope)

- **Member kinds:** highlight notes/comments, underline notes (via their host —
  an absorbed underline follows its host; a standalone underline joins on its
  own tag), standalone notes, and image-selection captions all join by the
  same `@tag` scan over their effective comment/task-source text. Continuation
  followers keep working: `<`-groups join a section as a unit (tag on any
  piece, preferably the head's comment), rendering exactly as today.
- **Section defs themselves** (`# Name` stickies) are absorbed, never members;
  a def's `@other` tag is ignored (no nesting of sections — flat, like
  continuation groups are flat).
- **Scope** is per-PDF/note: defs and tags resolve within one sidecar only.
  Cross-note sections would need vault-wide registries and break the
  per-PDF stateless model; explicitly out of scope.
- **Name matching:** case-insensitive, whitespace-collapsed; display form from
  the def. Allow spaces and punctuation in names (they can't collide with
  routes); match tags greedily per line (`@causal inference` = whole rest of
  the line's token run, or require exact def-name substring match per line).
  Recommend: a line contains a membership tag if it contains `@` + a defined
  name (case-insensitive); the tag text stripped at render is exactly the
  matched `@name` span.

## 6. Recommended solution

**Architecture:** a third fold, `SectionPlan`, computed in
`plan_annotation_folds` alongside `UnderlinePlan`/`ContinuationPlan`, from
(sidecar, existing-note) only. No PDF/sidecar writes, no new state files.

**6.1 Grammar.**

- *Definition:* a `StandaloneNote` whose first non-blank line matches
  `^#{1,6}\s+<name>\s*$` (single-line name, any heading level — Highlights
  users won't be precise) and which contains no quote/image content.
  Everything after the first blank line is the optional description
  (beautified at render; task lines in a description still import as tasks —
  don't suppress the task pipeline inside descriptions, just don't treat the
  def as a member).
- *Membership:* any highlight comment/task-source, standalone-note text, or
  image-caption text containing `@<defined-name>` (case-insensitive,
  whitespace-collapsed match). Strip every matched `@name` span (plus one
  adjacent whitespace run, mirroring `strip_return_link_glyphs` spacing care)
  from the rendered comment; if stripping empties the comment, drop the
  Comment card (like bare `<` adds no comment).
- *Precedence on `#task` lines:* `@route` wins — a trailing route-shaped
  token on a task line routes (existing behavior, existing error). Document:
  put `@section` on its own line when a task also routes. Bare `- @section`
  lines are task-pipeline-inert (no `#task` token) and therefore safe.

**6.2 Planning.**

1. Collect defs in sidecar order; duplicates merge (first description wins +
   dry-run warning `section_duplicate: <name>`).
2. Assign each annotation to the first defined name it references
   (document order of *defs* breaks ties); record dangling tags
   (`section_dangling` with page label, verbatim render).
3. Order sections by def position; members keep sidecar-relative order.
   Untagged annotations render in place as today.

**6.3 Rendering (at the def's position in sidecar order).**

```md
### Methods

A short description from the def's body, if any.

> [!quote|Page 4] …member quote…
>
> > [!note] Comment …(`@methods` stripped)…

^h-aaa…

> [!quote|Page 7] …second member…

^h-bbb…
```

Rules: section heading `### <display name>` (same level as page headings —
siblings, no hierarchy churn); description as a plain paragraph; members
rendered byte-identical to their ungrouped form except page headings are
suppressed inside the section and each member quote uses the labelled
`[!quote|<page>]` style readers already know from continuation groups;
member `^h-` IDs unchanged (identity inputs untouched — comment-key
tiebreaker sees the *stripped* comment, matching the `<`-follower
convention where the marker isn't identity). The def emits no block of its
own, so pure `# Name` defs need no tombstone; a def that previously rendered
as `[!note]<description>` leaves a `> [!info]` redirect stub pointing at the
section heading (existing stub machinery, new alias "the Methods section").
Section heading carries a stable anchor `^h-section-<12hex of
sha256(source_pdf + normalized name)>` on its own line so sections are
linkable (`[[#^h-section-…]]`) without disturbing member IDs; anchors are
derived, never stored.

**6.4 Observability (copy existing conventions).**

- Dry-run: `sections: Name (N)` per section, `section_dangling: @x (<page>)`,
  `section_duplicate: <name>` warnings.
- Concise scan: `N sections` / `N dangling section tags` after continuation
  details. JSON: `notes[].sections`, `notes[].sections_dangling` (omitted
  when zero, `schema_version` stays 1 — the established additive pattern).
- `highlights_count` counts members, not sections (groups count once today;
  sections aren't annotations at all).

**6.5 Beauty on all three surfaces.**

- *Obsidian:* heading + description + familiar callout cards reads well with
  zero CSS. Ship a `ref-sections` CSS snippet alongside `ref-highlights`:
  section headings get a small-caps eyebrow treatment with a gold left rule
  and comfortable spacing; members keep the existing quote/comment styling.
  Graceful without the snippet by construction (plain `###` + paragraph +
  callouts). Optionally use folded callouts for descriptions, not members.
- *bob-mac-capture Refs panel:* not inspected in this session (linked repo
  unread — **confirm before build** whether the inspector renders raw note
  Markdown or parses callouts/blocks). The heading-based design is the safe
  choice either way: any Markdown renderer shows headings, paragraphs, and
  blockquotes sensibly, whereas a wrapper-callout or HTML-`<details>` design
  could render as soup. Concrete asks for the Mac side: render `###` section
  headings distinctly, hide the `^h-section-` anchor line, keep per-member
  cards as today. No JSON contract change needed for v1 (sections are
  presentation inside the existing body); add `sections[]` to the scan
  envelope only if the panel wants a section outline (cheap later addition).
- *Terminal/`cat`/diffs:* headings + unchanged member blocks diff minimally
  when tags are added/removed — verify with golden tests (below).

**6.6 Edge cases & invariants.**

- Removing a def/tag dissolves the group with zero residue (members re-render
  exactly as before; section anchor vanishes without a tombstone — anchors
  were never member identity, same as page headings today).
- Member edits (quote/comment) keep today's ID stability (comment-only edits
  never re-ID).
- Tasks: `🔖`/processed-ID linkage unchanged (members keep IDs); redirect
  stubs for absorbed description-defs preserve old `[[#^h-…]]` links.
- Marker mirrors, preamble, and tombstone handling untouched.

**6.7 Tests (mirror `highlights_ref/tests/` conventions).**

- Golden render: multi-page section with description, stripped tags,
  labelled quotes, stable member IDs, section anchor.
- Dangling tag stays verbatim + dry-run diagnostic; escaped `\#`/`\@`
  (`\@methods` renders literally — add the backslash escape for symmetry
  with `\<`); route-wins-on-task-line; bare `- @section` doesn't route.
- Duplicate defs merge + warn; empty def renders heading-only; def-order
  rendering with untagged annotations undisturbed in place.
- Idempotency: scan → scan with no sidecar change is byte-identical
  (the pipeline's core property).
- Forward reference (`@tag` before its def) resolves; case/whitespace
  variants match.

## 7. Adjustments to the requirements (explicit)

1. **Membership sigil keeps `@`, but scoped:** non-task lines join sections;
   on `#task` lines the existing route meaning wins (§6.1). *Why:* avoids
   redefining shipped `@route` behavior and its error contract.
2. **Multi-word names encouraged** (`# Causal Inference` / `@causal
   inference`): they cannot collide with routes and read better as headings.
3. **Sections are flat and per-note** (no nested sections, no cross-note
   sections) — §5. *Why:* keeps the stateless per-PDF model; nesting can be
   revisited with usage evidence.
4. **One section per annotation; render at def position; empty defs render.**
   Judgment calls where the request was silent; each has a stated reason
   above and is cheap to revisit.
5. **Beauty via headings + CSS, not wrapper callouts** (§3.4, §6.5) — the
   largest visual deviation from a naive reading of "rendered under a nice
   section", forced by the block-ID machinery.

## 8. Open questions for Bryan

1. Should the `@tag` also be recognized in the *quote text* of highlights, or
   comments/notes only? (Recommend comments/notes only — quote text is PDF
   truth; Muster: never rewrite quotes.)
2. Is a linkable section anchor (`^h-section-…`) worth the extra block-ID
   namespace, or should sections be unaddressable headings in v1?
3. Confirm the Mac inspector's rendering path (raw Markdown vs parsed
   callouts) so the CSS/panel asks in §6.5 land correctly.
