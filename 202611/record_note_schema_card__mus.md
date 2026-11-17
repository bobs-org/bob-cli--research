# Record-note schema card: render record fields as a card, hide the frontmatter

> **Research query:** Start rendering a schema card in record notes for the fields
> corresponding to the parent album note's fields — under the H1, above `## Notes`,
> hiding frontmatter, with parity to the album-note and `bank.md` schema cards
> (editable values, `==`, keyboard nav), designed to be intuitive, reliable, and
> beautiful. Critique the plan and end with a recommended solution.
>
> Screenshot: `~/tmp/screenshots/20261117_101208.png` (`bead_lifecycle` record in
> `sase_blog_zettel/` — Properties panel with `parent`, `type`, `title`, `status`,
> `claim`, `section`, `created`, then `# Bead Lifecycle` / `## Notes`).
> Related in-flight work: `plan:202611/double_equals_schema_keymap.md`
> (`==` opens the album Schema Card / Bank setup card; records decision currently
> `album_only`).
>
> This is the `mus` report for the five-researcher swarm. It was written without
> opening any peer report from this swarm.

## Bottom line

Yes — build it, but **not** as specified. The request is directionally right (one
consistent card idiom everywhere schema exists) and wrong on its broadest stroke
(**hide *all* frontmatter in record notes**). That stroke should be narrowed.

Recommended shape:

1. **Keep record storage exactly as-is.** Flat frontmatter (`parent`, `type`,
   `title`, schema fields in album order, `created`) plus `## Notes`. No new keys,
   no body block, no second schema home. The writer stays
   `bob records update` (plus capture), exactly as the thin-client precedent
   (`decisions:mac-capture-is-a-thin-client`) and the album-card precedent demand:
   the plugin draws and collects intent; only bob validates and writes.
2. **Render a Record Card as note chrome, mounted after the first H1, above
   `## Notes`** — in Reading view and Live Preview, one header per surface, same
   lifecycle as the album header (`241v`) and Bank setup header (`248c`). Do not
   render it as a body section users can type around.
3. **Hide only the schema-defined value fields from Properties — not the system
   rows — and only on record surfaces the card actually covers.** `parent`, `type`,
   `title`, `created` stay visible (they are identity, not facts; see below for
   why `title`/`created` must stay read-only in the card). Hiding everything
   removes the only mobile-safe, plugin-off, Bases-compatible edit path for
   identity fields and repeats the album-`record`-row mistake in reverse.
4. **Edit values through a keyboard-first Record Card in the Schema Card idiom,**
   with one staged gesture at a time, a `bob records update -d` consequence
   preview, and apply through the real writer. No JS YAML serializer, no
   `processFrontMatter` whole-file rewrite.
5. **Revisit the `==` decision.** The current `double_equals` plan deliberately
   leaves records on Vim's reindent (`album_only`). Once a Record Card exists,
   `==` on a record note should open the **Record Card**, not the parent album's
   Schema Card and not reindent. The parent schema stays one explicit step away
   (a button in the card), so the key keeps its "open the card on this note"
   meaning on all three note kinds.
6. **Ship in two slices:** (A) read + jump + hide-schema-rows, plugin-only, no bob
   change; (B) editable card + `records update` preview/apply. Slice A alone must
   not close the request.

The rest of this note justifies each narrowing, then specifies the card.

## What the screenshot actually shows

Verified by viewing the image (Obsidan, `bead_lifecycle` record):

- Properties panel with seven flat rows: `parent` (wikilink to `sase_blog_zettel`),
  `type` (`record` with link icon), `title`, `status` (`draft`), `claim` (sentence),
  `section` (`future`), `created` (timestamp). `+ Add property` affordance below.
- Body: `# Bead Lifecycle` (H1 duplicating `title`), then `## Notes`, currently
  empty. No record values are broken — every row renders with a native widget.

That is the opposite of the album-note problem this request cites as inspiration.
On album notes the `record:` mapping is a nested object: Obsidian renders it as a
truncated orange JSON blob behind an unknown-type `?` icon, and editing it risks
writing the mapping back as a string (the prior swarm verified this against
`screenshot 20261112_054646.png`, `schema.rs:779`, and `recover_album_noun` at
`schema.rs:986`). Hiding that row is defensive.

On record notes there is **no broken row**. Flat text / choice / date / link / URL /
number scalars are exactly what Properties handles well. The cost/benefit of hiding
is therefore inverted: on albums hiding removes a corruption hazard; on records
hiding removes a working editor. The design must earn that removal with something
materially better — validation, choices, suggest, links, required-marks, and one
keyboard flow — not just visual consistency.

## What exists today (verified in-tree)

### Record storage and writers (`docs/records.md`, 616 lines)

- Record note: `parent: "[[<album>]]"`, `type: "[[record]]"`, `title`, schema
  fields **in album declaration order**, `created`; then `# Title` + optional
  `## Notes` (dated when the album opts in). Empty optional values and legacy keys
  are omitted. Strings use typed YAML quoting.
- Field kinds: text (no `values`), choices (nonempty `values` mapping), `date`,
  `link`, `url`, `number`, each optionally `list: true`; flags `required`,
  `suggest`, `default` (never on `status`), `label`, `min`/`max` for numbers.
  Reserved field names: `parent`, `type`, `title`, `created`.
- Writers: `bob records new TYPE TITLE -s K=V -n note` and
  `bob records update TYPE STEM -s K=V -n note`, both through the same staged
  planner as capture (preimage guards, no-replace install, album `[!records]`
  index rebuilt in the same transaction, dry-run diff). Explicitly empty optional
  clears the key; empty required refuses (exit 2). No-op succeeds without rewrite.
  JSON envelopes report before/effective values, notes, warnings, and
  `album_index` when it changes.
- Readers: `bob records show TYPE` (schema + choice labels + defaults + common
  suggests), `bob records list`, `bob records check` (lint). `bob albums list -f
  json` carries the album side (fields with label/kind/flags/default/min/max,
  `schema_fingerprint`, `filled` counts, `groupingClause`); per the prior swarm,
  `suggest`/`default`/`min`/`max`/`dated_notes`/`legacy` were historically lossy
  and any card must confirm the current report shape before round-tripping.

### Album Schema Card (`bob-ledger-tools`)

- Header (`241v-plugin-album-header.js`): report-driven, Reading post-processor
  (priority 49) + Live Preview editor extension; **no Markdown or frontmatter is
  rewritten**. Collapsed summary line + expandable chip view; `⊞ Schema` opens the
  card; `y` jumps to the exact Source-mode YAML line; bob `issues[]` paint as lint.
- Card (`241y*`, `241x*`, `241xa/*`, `242c`, `242d`, `242e`): keyboard-first modal
  in the Task Card idiom. Stages **one gesture at a time**, asks bob for a dry-run
  consequence, applies only that preview. Enter is latched until a current preview
  succeeds; Escape unwinds stage → card; YAML excursion (`242e`) preserves return
  state with fingerprint + selected key. Entry point `openAlbumSchemaEntry`
  resolves album vs. record (`albumSchemaEntryKindOf`, `albumResolveSchemaTargetForFile`)
  and teaches on missing/cyclic/ambiguous/non-album parents instead of guessing.
- Model helpers (`241w`): summary text, kind text, filled text
  (`set on 2 of 104`), choice counts, grouping clause — the visual vocabulary the
  request wants reused.

### Bank setup card (`248b/248c/248i/248j/248l`, `245–247` category card)

- Same architecture: hub path (`bank.md`) header mounted **after the first H1
  exactly where the album header mounts** (comment at top of `248c`), Reading +
  Live Preview, subscription-driven refresh, palette command (`edit-bank-setup`),
  YAML excursion with Done-guard. The category card (`245–247`) is the closest
  analogue to per-field record editing: model / write / UI split, preview-then-apply.

### `==` keymap (`plan:202611/double_equals_schema_keymap.md`, 278 lines)

- Vim normal mode + Live Preview + lone pending `=` + eligible note → open the
  card on *this* note; everywhere else keep reindent. Fragile point both the plan
  and `bob-vim-surround` document: a vimrc `nnoremap ==` can never fire because
  `=` is already a complete built-in operator — hence the capture-phase `keydown`
  bridge + injected `<Esc>`.
- Current decision (`records = album_only`): records keep reindent. The `records_too`
  alternative would open the *parent album's* Schema Card from a record. Neither
  anticipates a Record Card.

## Critique: six places the request needs narrowing

### 1. Hiding all frontmatter overreaches

Record frontmatter mixes two things: **identity** (`parent`, `type`, `title`,
`created`) and **facts** (schema fields). Only facts belong to the card.

- `parent` is a relation with teaching resolvers (missing/ambiguous/cyclic all
  have messages in `242d`). Editing it re-homes the note across folders and
  capture routes. It must stay a visible wikilink row, or move only through a
  guarded re-home flow that does not exist yet.
- `type: [[record]]` is what makes the note a record at all
  (`albumSchemaEntryKindOf`). Hiding it removes the only visible signal that the
  card applies — and the recovery path when it doesn't (type changed, schema
  broken, plugin off).
- `title` duplicates the H1 and drives the filename rule (`docs/records.md`:
  Filename rule). A card that edits titles must rename files, update inbound
  links, and rebuild the album index — a move/rename transaction, not a field
  edit. Keep title display in the card, editing in place (H1/Properties rename
  flow) for v1.
- `created` is a timestamp writers stamp; closed rows stay frozen by precedent
  (`decisions:off-clock-follows-tag-then-note-default` for the analogous clock
  case). Card shows it read-only.

What *should* hide: exactly the keys the parent album declares as fields, in
declaration order, and only while (a) the note's own `type` resolves to `record`,
(b) the card successfully mounted on that surface, and (c) the view is Reading or
Live Preview. Source mode, embeds of the note elsewhere, non-record notes that
happen to carry a same-named key, and plugin-off states never hide. Failure mode
is visibility, never data loss — same rule as the album `record`-row hide.

### 2. "Parity" needs a precise scope, not a slogan

Album/Bank cards edit **schema/config**: ordered fields, choices, labels, bounds,
grouping. The Record Card edits **values** against that schema: one note's
`status`, `category`, `visited`, `url`, `rating`. The gestures rhyme (select →
stage → preview → Enter applies, Esc backs out, `y` jumps to YAML) but the writer
differs (`records update`, not `albums update`), the preview differs (before →
effective per field, not fingerprint + regrouping), and the refusal set differs
(required-missing, choice-mismatch, bounds, list-shape, stale album preimage).

Copy these exactly: modal chrome, collapsed summary vocabulary, chip rendering,
`filled`-style hints where meaningful, one-gesture staging, Enter latch, Esc
semantics, YAML excursion + Done guard, teaching Notices. Do not copy: envelope
ops (`field.add`, `choice.move`, …), fingerprint `expect`, undo `inverse_ops` —
`records update` has no such envelope today, and inventing one for v1 is scope
creep. If a later migration flow (choice rename across 86 records) needs
multi-note transactions, that is its own phase with its own `bob` writer.

### 3. Placement is right — implement it as chrome, not content

"Under the H1 but above `## Notes`" reads like body insertion. It must be header
chrome mounted after the first H1 (the `241v`/`248c` pattern), for three reasons:

- Body insertion fights the `## Notes` writer (dated appends, capture appends)
  and every tool that patches `## Records`-style owned regions.
- Chrome inherits the solved problems: one header per surface, Reading +
  Live Preview, embed scoping (`albumHeaderNodeBelongs`-style guards), refresh
  on report change, cleanup on file switch / type change / unload.
- The `## Notes` section stays the note's editable body; the card never owns a
  heading users can delete out from under it.

Acceptance detail: on a record with no `## Notes` yet, the card still mounts
after the H1 (it must not wait for a section that may not exist); on a long
record, the card does not scroll with Notes — it is header chrome, collapsed
state in view state, never frontmatter.

### 4. The `==` plan needs a third outcome

Keeping `album_only` after this ships wastes the mnemonic: on the two card
notes `==` opens the card, on the third card note it reindents. Flipping to
`records_too` as written is worse: `==` on a restaurant record would open the
*album* schema (a different note's config), surprising anyone who asked for
"the card on this note."

Proposed amendment (small, backwards-compatible): `==` opens **the card for the
note under the cursor** — album → Schema Card, `bank.md` → Bank setup card,
record → Record Card. Parent-album schema remains reachable from an explicit
Record Card button ("Album schema"), which calls the existing
`openAlbumSchemaEntry` with the record's own path so its teaching Notices
survive. Counted `N==`, register-prefixed, visual/insert/replace, Source mode,
Reading view, and non-schema notes all keep native behavior per the existing
gate table; add one gate row (`target: record`) and one integration case per
eligible/ineligible parent (missing, cyclic, ambiguous, non-album).

### 5. Values need the album schema at paint time — plan the join

A record note alone cannot validate itself: choice labels/emojis, `required`,
`list`, `suggest`, `default`, `min`/`max`, and the *order* all live on the album.
The card model is therefore a join: **record frontmatter (this note,
via `metadataCache`) + album schema entry (via the shared album report
service)**. Failure states must be explicit, following `242d`'s teaching
precedent:

- album missing from report → "not in the album report — run Sync albums",
  card read-only, `y` still jumps to the record's YAML;
- parent ambiguous/missing/cyclic/non-album → the exact `242d` message, no
  guessing, no write gestures;
- schema invalid → visibly broken card, never impersonating healthy empty;
- schema healthy but field unknown on this record (hand-added key) → shown as
  undeclared lint with "edit in YAML", never silently dropped;
- required-but-empty → inline marker, `records check` hint, apply still allowed
  for *other* fields (preview shows the refusal only for the staged field).

Subscribe to the same report the album header uses; stale/refreshing/unavailable
disables staging exactly like `schemaFresh()` does. Never parse album YAML in JS.

### 6. Beauty is the collapsed default, not the expanded table

The best observation from the prior swarm (cld's vertical-bulk critique, adopted
in the final report) applies with more force here: record values are needed
often, but not *all* values on every open. A permanently expanded value table
pushes `## Notes` — the part Bryan actually writes during a revisit — down the
viewport on every open.

Default: one quiet summary line in the header (status chip + 2–3 facets +
`updated`/`created` hint), expandable to the full value list in schema order.
Expanded rows reuse the `[!records]` index vocabulary (choice chips with emoji,
`text · suggest`, `date`, `link` display text, `number min–max`, required `*`,
empty as `—` with "set" affordance, not blank). Owner-hue accent, notebook-header
radius/typography, theme variables for light/dark, wrap at ~375px, collapse state
in view state. The expanded card and the index row for the same record should be
visually the same language — that is the parity that pays, not merely sharing a
modal class.

## Requirement adjustments (explicit)

1. **"Hide the frontmatter" → "hide the schema value rows while the card covers
   the note."** System rows stay. Hide is view-scoped CSS on record surfaces only,
   restored on type change / file switch / unload / plugin-off; Source mode
   untouched; never delete or rewrite properties. (Justification: §1.)
2. **"Parity with album/bank cards" → "same interaction idiom, different writer."**
   Reuse modal chrome, staging, Enter latch, Esc, `y`/Done excursion, teaching
   Notices; write through `bob records update -d` preview + apply, not an
   `albums update`-style envelope. No JS YAML serializer. (Justification: §2.)
3. **`title` and `created` are read-only in the card in v1.** Title rename
   (file rename + link updates + index rebuild) and timestamp edits are their own
   flows. `parent`/`type` are displayed, not edited, in v1. (Justification: §1–2.)
4. **Placement is header chrome after the first H1, not a body section.**
   It visually sits above `## Notes` without owning document bytes.
   (Justification: §3.)
5. **`==` on a record opens the Record Card** (amending the `double_equals`
   `records = album_only` decision); parent schema is an explicit button inside
   the card. (Justification: §4.)
6. **YAML stays first-class.** `y` jumps to the exact record line, lint carries
   `records check` diagnostics, and every refusal names the Source-mode fix.
   Kind changes, key renames, and multi-record migrations are YAML-only in v1.
7. **Dated `## Notes` stay out of the card in v1.** The card edits fields; notes
   append via body/capture/`records update -n` as today. A verdict/prompt loop
   (per the data-unlock research: capture → verdict → lookup) is habit design,
   not card scope.

## Recommended solution

### Slice A — read + jump + scoped hide (plugin-only, no bob change)

- New `record-card` header surface in `bob-ledger-tools` (new fragments modeled on
  `241v` + `248c`, not edits to those files): Reading post-processor + Live
  Preview widget, one per surface, after the first H1; subscribed to the album
  report; view-state collapse flag per note.
- Reads: this note's frontmatter from `metadataCache`, joined to the parent
  album's schema entry from the shared report. No new subprocess call in v1
  (`records show` JSON stays the debugging reference, not the live feed — same
  call the album header avoids making per-note).
- Renders: collapsed summary line (status choice chip first, then up to three
  `index_facets`-style values, then muted `created`/note-count hint) + expandable
  value list in schema order with kind suffixes, required marks, empty `—` states,
  and lint marks from the report/`records check` shape. Invalid schema and
  unresolvable parent render the teaching state, never a fake-empty card.
- Hides: view-scoped CSS for exactly the declared field keys on covered record
  surfaces (selector per key, e.g. `[data-property-key="<field>"]`), with the
  restore matrix from the album-row hide (type change, file switch, embed,
  unload, Source mode, non-record notes). `parent`/`type`/`title`/`created`
  never hidden.
- Entry points: header `⊞ Record` button (label TBD, see below) opens the
  read-only card; `y` jumps to the record's YAML line (reuse the excursion
  scaffold: record view-state, fingerprint of the *album* schema, return to card).
  Palette command **Edit record values** (resolves the current record; refuses
  cleanly off-record). No writes in this slice.
- Docs: `docs/albums.md`-adjacent record-card paragraph (open affordance,
  `==` reserved, YAML-first note), plus the generated facts refresh. No command
  table change (no new CLI).

Slice A closes when: the card paints on all seeded record kinds
(`eat`, media kinds, `sase_blog_zettel`-style albums), hides exactly the field
rows, survives file switch/type change/embeds, and every failure state teaches.

### Slice B — editable Record Card

- Modal in the Schema Card idiom (`AlbumSchemaCardModal` as template, new class —
  do not subclass across concerns): target list = this record's fields in schema
  order + lint targets; `j/k` + ArrowUp/Down move, `Tab`/`Shift+Tab` across inputs
  in staged form, `Enter` applies the previewed gesture (latched until
  `records update -d` returns current), `Esc` unwinds stage → card → close,
  `y` jumps to the field's YAML line, `?` or a visible hint row lists keys.
  All keyboard paths work without a mouse; all mouse paths work without the
  keyboard.
- Staging: one field per gesture. Draft input per kind: choices as radio-chip
  list (with emoji + counts where the report has them), `suggest` as filterable
  combo (existing folder values offered, free text allowed), `date` as
  `YYYY-MM-DD` with `today`/`yesterday` shortcuts, `link` as note picker
  (bare name or `[[wikilink]]`, same acceptance as the planner), `url`/`number`
  as validated text (bounds checked client-side, authoritatively by bob),
  `list` as comma/repeat-aware multi-input written as a YAML block list,
  optional-empty as explicit "clear" (writes key removal), required-empty as
  refused preview with the reason.
- Preview: run `bob records update TYPE STEM -s K=V -d` (or the service
  equivalent the album card uses for `albums update -d`) and render
  before → effective, plus index side-effects ("album index will rebuild")
  and warnings (`records check` hints). Apply only the previewed bytes through
  the same staged writer; one gesture is one commit (`records: update <stem>
  (<field>)`-scoped, following the `albums: update` commit discipline).
  Stale album/record preimage refuses with "re-open and retry", never a merge.
- Parent schema access: explicit "Album schema" button calls
  `openAlbumSchemaEntry` with the record's own path (preserving its parent
  teaching); it does not hijack `==`.
- `==` amendment ships in this slice (gated on the card existing): extend the
  `248m` gate with `target: "record"` via `albumSchemaEntryKindOf`, reusing the
  same capture-phase bridge, `<Esc>` clear, and try/catch open semantics. Update
  the three docs lines the `double_equals` plan names, flipping the default and
  recording the supersede of `records = album_only`.

### Naming and visual details (lead-design calls)

- Button: prefer **`⊞ Record`** on the record header (mirrors `⊞ Schema` on
  albums, `⊞ Edit` on Bank setup). Palette: **Edit record values**. Do not call
  it "Schema" on a record — the schema lives on the parent; the record holds
  values.
- Collapsed line leads with the group/status choice (the index's group token),
  because that is the facet Bryan scans in `[!records]` tables. Never show raw
  choice keys without labels.
- Required `*` is quiet (muted, after the label), not red, until the row is
  staged-empty — then it becomes the refusal reason. Empty optional is `—`,
  not blank, so "no value" is distinguishable from "failed to load."
- Numbers stay plain, dates ISO, links display text, lists join with `, ` —
  the exact `index_facets` formatting contract, so card ↔ index ↔ Bases agree.

### Sequencing and acceptance

1. Slice A (amend the current card/header work, plugin-only): paint, hide, jump,
   teach. Manual acceptance in a live vault on desktop: open a liked restaurant,
   a `to_try` restaurant, a record with missing required, a record with a broken
   parent link, and the `bead_lifecycle`-style `sase_blog_zettel` record from the
   screenshot. Each paints the right state; `y` lands on the right YAML line;
   switching to a daily note shows untouched Properties.
2. `==` amendment (small, with Slice B or immediately after): `==` on each of
   the above opens the Record Card with no document change and no undo entry;
   `3==`, Source mode, and daily notes keep reindent.
3. Slice B (writer): each kind staged once (choices, suggest-text, date, link,
   url, number + bounds, list, clear-optional, refuse-required-empty), preview
   matches `records update -d`, apply commits once, stale-preimage refuses.
   Mobile/Reading-view behavior: card opens read-only where the writer cannot
   run; nothing pretends to stage.
4. Non-goals for v1 (unchanged): title rename, `parent` re-home, `type`/`created`
   edits, multi-record migrations (choice rename with migration), computed or
   relational fields, `## Notes` verdict prompts, Reading-view `==`, bank-month
   or area-note `==`.

### Risks and open questions for Bryan

- **Properties-hide fragility.** The hide depends on Obsidian's
  `[data-property-key]` selector surviving re-renders. Mitigation is the same as
  for albums: CSS-only, per-surface, restore-on-everything, visible-on-miss. If
  it ever feels dishonest (hidden rows, no card — e.g. plugin off), the fallback
  is correct by construction: rows reappear.
- **Should `created` ever be editable?** This report says no for v1. If
  back-dating visits (`visited`, not `created`) covers the need, say so and keep
  it closed.
- **Do we want the card on mobile in v1?** Album/Bank cards gate editing to
  desktop Obsidian. Records are the most mobile-edited notes (at the restaurant,
  after the movie). Slice A reads everywhere; Slice B should state its mobile
  answer explicitly — even "read-only on mobile, edit on desktop" is a decision
  worth recording as a `decisions:` entry, since it reopens the desktop-only
  precedent.
- **Bases interplay.** Bases read frontmatter directly; hiding rows does not
  affect Bases, but a Bases edit while the card is open can stale the preview.
  The preimage guard already refuses that write safely — the card must surface
  the refusal as "changed under you, re-open", not as a silent overwrite.

---

*Sources checked in-session: the screenshot above; `docs/records.md` (§Albums,
§Schema, §Field kinds, §The note Bob writes, §`bob records`); `bob-ledger-tools`
`241v` (header), `241w` (model), `241x/241y` (card), `242d` (entry resolver),
`242e` (YAML excursion), `248c/248l` (Bank setup), `plan:202611/double_equals_schema_keymap.md`
(full contract + `records = album_only` decision); audited reads of
`research:202611/album_record_schema_ux/album_record_schema_ux.md` and
`research:202611/record_notes_data_unlock/record_notes_data_unlock.md`; live
`metadataCache`-join and hide-selector greps over `241*`/`248*`. No peer report
from this swarm was opened.*
