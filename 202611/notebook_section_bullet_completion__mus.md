# Notebook H2 sections in capture: bullet-start completion and per-bullet routing

Research report (`mus`). Question: how should capture support targeting
notebook `##` sections — `#`-at-bullet-start completion, project-capture
support, and `@<notebook>#` completion/creation — and is the plan as stated
the right one?

## Verdict

Good idea, but the request as written slightly misjudges what already
exists, and implementing it literally would create a third overlapping way to
do two jobs that already have one way each. Two of the three asks are
**already built**; the remaining gap is real and worth filling, but it is
narrower than the prompt suggests:

1. `@<notebook>#` completion for existing sections **plus a create-new row
   already exists** (`notebook_section_create`). Do not rebuild it; close its
   small gaps instead.
2. Section targeting on project notes **already exists twice over**:
   `@route+prj#section` (commit) with `##`-section completion on `^prj`
   targets, and ALL-CAPS bullets seeding `## Title Case` sections in new
   project/notebook creation. Do not add a parallel spelling.
3. The genuine gap is **bullet-start (`- #`) section routing inside notebook
   list drafts** (`@nb` header + bullets), which today has no section
   meaning at all. That is the feature to design, and it should be shaped as
   the notebook analog of the note-less `@route+id` drawer-bullet form, not
   as a new sigil.

Recommended solution: one new grammar branch (section-scoped list bullets
under a notebook header) + one new completion context (bullet-start section
menu) reusing the drawer-bullet interaction shape, with creation, quoting,
and near-miss rules copied verbatim from the existing `@nb#` resolver. `/`
follows for free through the existing sigil-alias allow-list. Details below.

## What already exists (do not rebuild)

All claims below were read from `docs/capture.md`, `docs/notebooks.md`,
`docs/completion.md`, and the `capture_complete` / `capture_language`
sources in this checkout.

### `@<notebook>#` completion with create-new exists

`@nb#` opens section completion backed by the same scan as
`bob capture-sections`, listing **only real H2 sections in document order**
(never the H1, H3s, or fenced headings). A nonempty query with no exact
title or whole-slug match appends one additive `kind:
"notebook_section_create"` row (`New section "Title"`); its replacement is
the bare slug, or the quoted selector when the bare slug would be a near
miss, and the response keeps exactly one `#` while preserving any `^id`
suffix. Block-ID fields on `@nb^` / `@nb#section^` carry
`destination_kind: "notebook"`. This is the exact behavior the third ask
requests. Verified in `src/native/capture_complete/candidates.rs`
(`notebook_section_candidates`, `notebook_section_replacement`).

Commit semantics to match already exist too: exact title or whole-slug
match; unquoted near-miss (prefix or edit distance two) refuses with
`notebook_section_near_miss`; quoted selectors create verbatim; other
missing selectors create a Title Case `##` at EOF (`src/native/capture/
notebook_note.rs`).

Remaining gaps in this path are small (listed under Recommendations) — e.g.
whether `capture-sections` surfaces notebook H2s for a notebook route, and
completion when the notebook is a prospective `%n` create later in the same
draft.

### Project-note section targeting exists

- `@route+id#drawer` on a `^prj` target names one of the note's eligible
  `##` sections instead of a drawer, appending after that section's last
  nonblank line and creating a missing section as `## Title Case`
  (`docs/capture.md`, "Sub-bullets under existing tasks"). Structural
  headings are excluded.
- Completion on `^prj` targets already lists the note's eligible `##`
  sections in the `task` group with `entry_count` and `Adds to ##
  Requirements`-style consequence copy.
- New project-note creation (`@route^id@`) already seeds `## Title Case`
  sections from ALL-CAPS first-level bullets with nested notes, merging
  equal-normalized titles; `TASKS` merges into `## Tasks`. Notebook creation
  (`@parent^id@ %n`) does the same seeding.
- Bullet-start drawer completion on a **new project note** already offers
  `recent` + `new` rows with `Creates ## Future Work` consequence copy.

So "good support when using the project capture syntax" is, for existing
projects, a completion-polish question, not a grammar question. The one
place project-creation drafts lack section completion is suggesting
*which* ALL-CAPS titles to type — there is no existing note to read
sections from, so any menu there must come from a cross-note catalog (see
Alternatives).

## Critique of the plan as stated

**It is a good idea.** Notebooks are the one destination where sections are
load-bearing structure (H2 = the only organization axis; no Tasks section,
no drawers, no types), yet they are the one destination with no per-bullet
section control. A five-note `@nb` list draft today forces all five notes
into one section (or five separate drafts). Per-bullet sections remove that
paper cut, and the drawer-bullet precedent proves the interaction works.

**But three adjustments are justified** (flagged explicitly per the brief):

1. **Do not add a new sigil or marker.** The `#`-at-bullet-start slot is
   the right trigger precisely because `#` already means "which place"
   there (drawer completion uses the identical slot on task drafts). The
   context system disambiguates by landing site: bullets landing under a
   task get drawers; bullets landing under a notebook section-region get
   sections. One key, two menus, zero new grammar tokens to learn.
2. **Scope the new grammar to notebook list headers only.** The prompt's
   "start of a bullet" is ambiguous across at least four bullet positions
   (list bullets under `@nb`, authored bullets under a single notebook
   note, bullets under `@nb#sec` headers, bullets in project-creation
   drafts). Only the first needs new grammar; the others already have a
   meaning (nest-under-note, header-routed, ALL-CAPS-means-section). Giving
   every bullet-start a section menu would collide with drawer completion
   and nested type completion (`  - #` still types). Saying "no" to three
   of the four positions is the design decision that keeps this reliable.
3. **Creation should follow the `@nb#` resolver byte-for-byte, not invent
   list-specific rules.** Unquoted missing → Title Case `##` at EOF;
   quoted → verbatim; near-miss → refuse with the same code and
   suggestions. Completion and commit must agree (the repo's standing rule:
   completion is backed by the same scan as commit), otherwise the menu
   promises what the write refuses.

## Recommended solution

### New grammar: section-scoped bullets under a notebook list header

Under a lone-`@nb` list header today, each first-level bullet becomes one
note in the top-level region, and a bullet-start `#` is refused
(`drawer_bullet_position`). Change that refusal, for notebook headers only,
into routing:

```text
@dev_tools
- #Ideas
  - Try mergiraf for diffs
  - jj log --revisions flag
- #Troubleshooting
  - Check which process owns a port
- Ship the notes anyway
```

- A first-level bullet of the form `#section` (slug, quoted literal, or
  bare `#`) with **nested bullets** files each nested bullet as its own
  stamped note under that `##` section (existing, or created per the
  standard resolver). The section bullet's own text is the selector, never
  a note — mirroring how `- #drawer` bullets under note-less `@route+id`
  name the drawer rather than becoming notes.
- A first-level bullet under the same header with **no** `#` prefix keeps
  today's behavior (top-level note), so old drafts are unaffected.
- A childless `- #Ideas` bullet: refuse (`empty` section scope — capture
  never creates empty drawers either, and a childless selector that names
  an existing section would be a no-op write). The error should name the
  fix the way `empty_drawer_bullet` does.
- Nested bullets under a section bullet are notes, not further scopes: a
  `  - #...` bullet two levels down keeps today's meaning (task-type menu
  in completion; literal/typed handling at commit). One level of scoping
  only — drawers made the same call (suffixes stay local; no nesting of
  scopes).
- `- #` with an empty selector is incomplete (`needs: ["section"]`), never
  "any section" — exactly like `@route+id#` today, which never means "any
  drawer."
- `@nb#Section` header + bullets keeps its existing meaning (all bullets
  under that section); a `#`-prefixed bullet beneath an already-sectioned
  header is refused as redundant scope (`list_header_marker` family),
  teaching the header form. This avoids two selectors fighting over one
  bullet.
- List-bullet trailing markers (`s:`, `$`, `&`/`*`/`~`, `%c`, ` :id` /
  ` ^id`) stay as they are on notebook lists today (IDs stay literal text;
  `%c` composes) — section scope and those markers are orthogonal, except
  that a section bullet itself takes no `^id` (it names no note; the
  `@nb#section^id` spelling already covers named section notes at header
  level). Document the one sentence: "name a note with `@nb#Section^id`,
  scope a list with `- #Section`."

Why this shape and not alternatives: it is the notebook image of two
existing forms — the note-less `@route+id` drawer-bullet list (first-level
bullets route, nested bullets are content) and the ordinary `@route#sec`
section header (bullets file under a heading). Users who learned either
one already know this one. No new sigil, no new line shape, no mode flag.

### New completion: bullet-start section menu on notebook drafts

- Trigger: `#` (and `/` via alias, below) at the start of a first-level
  bullet (`- #`, `* #`, `+ #`) **iff** that bullet's list header is a lone
  `@nb` notebook route. Everywhere else bullet-start keeps today's
  behavior (drawer menu on task-landing bullets, empty success where no
  drawer applies). The condition is computable from the draft (header
  route + notebook policy), so no vault write and no new latency class; it
  rides the existing 150 ms vault-scan budget.
- Rows reuse the `@nb#` resolver over the header notebook's H2s: existing
  sections in document order, then the additive `notebook_section_create`
  row for a nonempty non-matching query (same replacement rules: bare slug
  unless it would near-miss, then quoted). Same `refused` reasons as the
  commit path (reserved/generated, near-duplicate, ambiguous) so accepting
  a row and committing always agree — the drawer-bullet menu already sets
  this precedent with its resolver-backed `refused` field.
- Replacement inserts the selector text after `- ` (`#ideas` or `#"My
  Section"`), and when the selector ends its line with no nested bullet
  yet, appends `\n  - ` with `cursor_after` on the opened nest — copied
  from bullet-start drawer completion, which already does exactly this.
  This is the "beautiful" half of the brief: one keystroke, menu, Return,
  and the caret sits where the first note goes.
- Groups: `sections` (the notebook's H2s) + `new` (one row). Skip the
  drawer's `recent` group here — `recent` answers "which drawer does this
  task lack," a question with no notebook analog. If a cross-note section
  vocabulary is ever wanted for project-creation drafts, that is a
  separate catalog feature (see Alternatives), not a third group smuggled
  into this menu.
- The `## Notebooks` generated-catalog guard needs no notebook-side twin
  (notebook files carry no generated callout), but the menu must still
  skip fenced H2 lookalikes and honor H2-only — both already true of the
  underlying scanner.

### `/` alias: no extra work, one allow-list line

`/` → `#` already fires "wherever a `#` menu would open," decided by
running the candidate draft through `completion_field_at`
(`expand_hash_alias` in `rewrite.rs`). Adding the new bullet-start section
context to that function's allowed-context match is the entire `/` change,
and the existing guards (never at line start — `- /` is not line-start —
never glued, never after another `/`) stay correct untouched. Note for
implementers: shell completion serves one-line drafts only and never
reaches a bullet start, so this menu is editor/JSON only — same as drawer
bullet completion today. No shell adapter change.

### Commit/writer semantics

- Reuse `resolve_notebook_section` + the `notebook_note.rs` insertion path
  per scoped bullet group (append after the last note's whole block in the
  target region; first-note-in-section spacing; EOF creation with one
  heading). Batch planning sees staged sections, so two bullets creating
  `#New` in one draft merge into one heading — the same staged-snapshot
  rule project-note creation relies on for merging equal-normalized
  section titles.
- JSON: keep `kind: notebook_note` per note; add the bullet's section scope
  to the existing additive `notebook` object (`section`,
  `section_action`). Human output keeps `📓 Note → Title › Section`, one
  line per note — no new output shape, just more lines.
- `capture-parse` spans: the section selector on a list bullet gets the
  same span treatment as `@nb#section` selectors so highlighting never
  disagrees with completion (the repo's phase-grammar/tokenizer sharing
  rule).

### What explicitly stays out

- No `@@nb#sec` / `@@nb+id` forms: `@@` stays draft-wide and suffix-free
  per the accepted `notebook-routes-write-notes` decision (reopening it
  would reverse `bob-cli-ey.1.1.1`). A global notebook declaration plus
  per-bullet `#` scopes composes fine without suffixes: `@@dev_tools` +
  `- #Ideas` bullets.
- No section menu on single-note notebook items (`Note @nb#sec` +
  authored bullets nest under the note — a section choice there is
  meaningless), on `@nb+id` sub-note drafts (parent is fixed), or on
  nested bullets anywhere.
- No `recent-sections` catalog in v1. If project-creation drafts later get
  section suggestions, build it as its own catalog feature with its own
  privacy/count semantics, not as a side effect of this menu.

## Alternatives considered (and why not)

- **Per-bullet `@nb#sec` suffixes instead of bullet-start `#`.** More
  explicit, but it collides with the existing whole-item route slot (a
  second route-bearing line is `duplicate_capture_marker`) and reads
  poorly on short bullets. The header form already serves the
  one-section-per-draft case; bullet-start serves the mixed case.
- **ALL-CAPS literal section bullets in notebook lists** (mirroring
  project-note seeding). Rejected: in notebook files ALL-CAPS has no
  writer meaning (drawers don't exist there), so `- FUTURE WORK` under
  `@nb` would be genuinely ambiguous with a note whose text happens to be
  all caps. The `#` sigil removes the ambiguity — the same reason drawers
  accept `#slug` as well as the literal.
- **A `#notebook` tag or sub-area for sections.** Rejected for the same
  reasons the notebook decision record rejects neighboring proposals:
  tags can't change capture/commit behavior, and sub-areas drag in Ready
  caps, Tasks sections, and review membership.
- **Section vocabulary suggestions for brand-new project notes.**
  Tempting, but the data source (parent note? sibling projects? global
  history?) has no obviously-correct answer and the writer merges
  equal-normalized titles anyway. Recommend shipping list-scope first and
  letting real drafts reveal whether creation-time suggestions pull their
  weight.

## Edge cases the implementation must cover

1. Header notebook renamed/retyped mid-draft: classification uses the same
   preimage-guarded policy as `@nb#` so a retype aborts instead of writing
   to the wrong file (existing `NotebookRoutePolicy` sources mechanism).
2. Prospective notebooks (`@parent^id@ %n` earlier in the same draft):
   section bullets targeting the not-yet-created route should resolve
   against the staged create (disk routes win; earlier creates visible to
   later items) — same rule as `@nb` references after a create. With no
   sections yet, every scope is a create; near-miss has nothing to match.
3. `## Notebooks`-style generated headings don't exist in notebook files,
   but fenced H2s and the H1 must stay out of the menu (scanner already
   does this — keep it).
4. Empty selector, childless scope, scope-under-sectioned-header,
   scope-with-`^id`, quoted unterminated (`- #"Fu` → incomplete
   `needs: ["section"]`, mirroring `@sase#"Fu`), and `^prj`-style `+
   #`-mixups (`@nb+id#sec` is not this family — `+` takes sub-notes, `#`
   after `+id` on non-`^prj` tasks is a drawer slot, and notebooks have no
   drawers, so refuse with the teaching error pointing at `- #sec` under
   a header).
5. Multi-item batches: scopes are item-local; a `- #sec` bullet in a task
   item stays drawer behavior. The header's route decides per item.
6. Performance: one H2 scan per notebook per completion, same as `@nb#`
   today; no new synchronous reads.

## Suggested acceptance checks

- `@nb` list with three section scopes + one unscoped bullet writes each
  note to the right region in one transaction; dry-run bytes equal commit
  bytes; JSON carries per-note `section`/`section_action`.
- Near-miss scope (`- #Idea` vs `## Ideas`) refuses with
  `notebook_section_near_miss` naming the heading; quoted `-
  #"Idea"` creates verbatim.
- `- #` empty → `needs: ["section"]`; childless `- #Ideas` → named
  empty-scope refusal; `- #sec` under `@nb#sec` header → redundant-scope
  refusal teaching the header.
- `/` at the same caret expands to `#` and opens the identical menu
  (rewrite `expand_sigil_alias` + completion agree); shell one-liners
  unaffected.
- Task drafts regression: `- #` under `@route` task headers still opens
  drawers; nested `  - #` still opens types; `#` at item edge still types.
- Existing `@nb#` completion rows byte-identical before/after (new
  context adds rows only at bullet-start carets).

## Requirement adjustments (explicit, per the brief)

1. **"Trigger completion for existing sections and allow creation using
   `@<notebook>#`"** — already shipped. Change to: keep and regression-
   guard it; fix only its small gaps (prospective-create routes,
   `capture-sections` coverage for notebook routes).
2. **"Support when using the project capture syntax"** — narrowed to: no
   new project grammar; the project side of this feature is the already-
   built `^prj`-section completion plus ALL-CAPS seeding. Only add section
   suggestions to creation drafts if a follow-up justifies a catalog.
3. **"Capturing new notes to an existing project by targeting it with
   `@<notebook>`"** — reinterpreted: notes land in projects' notebooks via
   `@<notebook>` routes (notebooks hang under projects; tasks still belong
   to `@project`). The design above makes `@dev_tools` lists section-aware,
   which is the concrete form of that ask. If the intent was instead
   `@project#section` section-bullets on project notes, that path is also
   already built (ordinary section bullets, `##`-eligible).
4. **New scope added by this report:** per-bullet section scoping under
   notebook list headers, and the deliberate non-goals (no new sigil, no
   `@@` suffixes, no nested scopes, no `recent` group, single-note items
   untouched).
