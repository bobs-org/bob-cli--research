# The album `record` property: hide the row, read it in the header, edit it through bob

Consolidated report, 2026-11-12. Lead researcher merging five independent reports
(`__cdx`, `__cld`, `__grk`, `__mus`, `__gem`, in this directory) plus my own
verification against bob-cli master `4835680d`, the live vault, the
`plan:202611/album_plugin_ui.md` phase spec, and the `cli_rules` memory.

## TL;DR

Yes, this is worth doing — but not the way the request's words suggest. "Make `record`
render properly in Obsidian" cannot mean making the native Properties row pretty:
Obsidian has no widget for nested mappings and no public API to add one. All five
researchers independently converged on the same shape, and I endorse it:

1. **Keep the nested `record:` mapping exactly as stored.** No flattening, no body code
   block, no second schema home, no third-party nested-properties plugin.
2. **Hide the native `record` row on album notes only** (already specified in the
   in-flight phase `bob-cli-k3.7.1.4`). The row is not just ugly — it is a corruption
   hazard: Obsidian's unknown-type widget can write the mapping back as a string, and
   `schema.rs` already carries `recover_album_noun` because exactly that shape has
   leaked before.
3. **Render the schema as album-header chrome**: one quiet, collapsed summary line that
   expands into a chip-based schema view sharing the `[!records]` index's visual
   vocabulary (`🔖 To try` on the card is the same token as `🔖 11 to try` in the
   index).
4. **Edit through a keyboard-first Schema Card** (Task Card idiom) whose every write
   goes through a new **`bob albums update`**: JSON ops in, dry-run consequence line,
   fingerprint guard, Rust-side validation, span-preserving YAML emit, index rebuild,
   one scoped commit. The plugin draws and collects intent; it never parses or writes
   schema YAML.
5. **YAML stays first-class**: `y` jumps to the exact Source-mode line; bob's
   `issues[]` (which already carry `line`, `key_path`, `suggestions`) paint as lint
   marks. Kind changes and anything the card doesn't model happen there.
6. **Ship in two slices**: amend `k3.7.1.4` now (plugin-only, read + jump, no bob
   changes), then a follow-up phase for the writer and editable card. Slice A alone
   does not satisfy "very easy to modify" — do not let the request close on it.

## What the screenshot shows, and why (verified)

The screenshot (`~/tmp/screenshots/20261112_054646.png`) is `eat.md` with six clean
native property rows (`parent`, `type`, `summary`, `emoji`, `index_by`, `created`) and
a seventh, `record`, rendered as a truncated orange JSON string behind an unknown-type
`?` icon. The bytes on disk are healthy canonical block YAML (re-verified today with
`cat -A`): `noun`/`label`/`dated_notes`, five ordered fields with required marks,
choices, `suggest` flags, and `legacy` patterns. `podcasts.md`, `tv.md`, and
`movies.md` share the shape. Nothing is corrupt; this is pure renderer limitation.

Three stacked causes, agreed by all five reports and confirmed against primary sources:

- **Obsidian's Properties engine supports only flat scalars and string lists.** A
  mapping value gets the `unknown` fallback and a `JSON.stringify` preview. Obsidian's
  help still lists nested properties as unsupported and recommends Source mode.
- **There is no public API to fix the row.** Two researchers independently checked
  `obsidian.d.ts` (v1.14.4 and the pinned API repo): no property-widget registration
  exists. Community plugins ("Nested Properties", "Nested Frontmatter Properties",
  Metadata Menu objects) patch the undocumented `metadataTypeManager.registeredTypeWidgets`.
- **The row is a write hazard, not just an eyesore.** In Obsidian 1.9.2 clicking a
  nested object wrote `[Object object]` into the file (forum-acknowledged regression).
  Any Properties-panel save re-serializes the whole frontmatter. bob's parser requires
  a mapping (`record must be a mapping; got …`, `schema.rs:779`) and ships
  `recover_album_noun` (`schema.rs:986`) specifically to salvage a noun out of a
  stringified record — evidence this failure mode is real, not theoretical.

One correction the swarm surfaced (cld, confirmed by me at byte level): the epic plan's
risk table claims canonical block YAML makes a Properties re-serialize a no-op. Not
quite — `legacy:` is written serde_yaml-style with **unindented** sequence items, while
Obsidian writes indented ones. A Properties edit of `summary` would likely rewrite the
`record:` block's bytes (harmlessly today, since bob parses semantics and the album
service fingerprints content, but it breaks the "no-op" claim). **Fix: bob's schema
emitter should write Obsidian's YAML style, and a real-Obsidian fixture should edit
`summary` via Properties and diff the `record:` block.**

## Where the five reports agree

Every report, working independently, concluded:

- Keep the nested mapping; the storage decision from `bob-cli-k3` is right and this
  rendering cost was predicted by the epic's own research.
- Native Properties can never be the schema's render or edit surface.
- Hide the row album-scoped only (an unrelated note may legally carry a `record` key;
  the phase plan already demands that fixture), with cleanup on type change, file
  switch, and unload, and Source mode untouched.
- Present the schema from the existing shared album report service
  (`bob albums list -f json` via `241l`/`241m`) — never a second YAML parser in JS.
- `bob albums list -f json` is **lossy** and must grow additively before any editor can
  round-trip: `AlbumField.to_json` (verified in `report.rs`) emits only
  `key/label/kind/required/list/choices`, omitting `suggest`, `default`, `min`, `max`;
  the album entry omits `dated_notes` and `legacy`.
- Dangerous edits need impact counts before they happen: renaming a choice key strands
  every record using it (86 `liked` restaurants); renaming a field key orphans the
  data in all 104; making a field required silently invalidates older records; a typo
  in `values:` breaks the `@eat/` capture route.
- Rejected unanimously: flattening the schema into top-level properties (vault-wide
  property-name pollution, `fields` still an object, dozens of rows), moving it to a
  body code block (second source of truth, fights the bob-owned `[!records]` region,
  reverses an accepted migration), adopting a community nested-properties plugin
  (schema-unaware, undocumented internals, no validation or impact preview), and
  CLI-only editing (leaves the broken render and forces a terminal context switch).

## The two real disagreements, resolved

### 1. Who writes the YAML? → bob, and only bob

Three reports (cdx, cld, grk) demand a bob-side writer; two (mus, gem) propose
plugin-side writes — mus via `processFrontMatter` with a v2 Rust writer "if churn
annoys", gem via `vault.process` plus a ~400-line JavaScript model that re-implements
the Rust validation rules.

**The bob-side writer wins, and not narrowly:**

- **Validation drift is the exact disease this epic exists to cure.** Duplicating
  `schema.rs` rules in JavaScript recreates the config-vs-vault drift that motivated
  albums. One schema authority, in Rust, already exists.
- **The plugin contract already decides this.** The `plugins-albums` shared contract
  (verified in `plan:202611/album_plugin_ui.md`): "No UI code rebuilds catalog Markdown
  or parses record schemas from YAML." A JS serializer violates its spirit; so does the
  thin-client precedent (`decisions:mac-capture-is-a-thin-client`).
- **The plugins themselves refuse `processFrontMatter`.** `211-parent-frontmatter-plan.js`
  exists because whole-frontmatter re-serialization rewrites other keys (unquoted
  wikilinks). An object-based API preserves neither bytes nor style.
- **Impact counts and migrations need the vault scan bob already has.** "86 records
  still use `liked`" requires `records check` machinery; a future rename/merge needs
  the span-preserving record-update planner, the maintenance lock, and one scoped
  commit covering album + records + rebuilt index. No Obsidian API provides that
  transaction.

mus's sequencing instinct survives even though its writer doesn't: ship the read-only
surface first, writer second.

### 2. Where does the schema render? → hidden row + header, one quiet line

cld and gem want an in-row replacement (a "schema strip" / "smart pill" painted inside
the Properties row); cdx, grk, and mus want the planned hide-plus-header-card.

**Hide + header wins for v1.** The in-row strip is the more "honest" render (the panel
still shows seven properties) but requires injecting DOM into Obsidian's Properties
panel and re-applying it through a MutationObserver on every re-render — strictly more
fragile than a CSS hide, for marginal gain. The header is bob-owned chrome with an
established dual-view lifecycle (notebook header `241e`–`241g`), which is where the
phase plan already puts it. Revisit the strip only if the hidden row's absence ever
feels dishonest in practice.

**But take cld's vertical-bulk critique seriously** — it is the best UX observation in
the swarm. A permanently expanded schema table pushes the `[!records]` index (the
page's actual job) down ~8 lines on every open, for information needed a few times a
year. So amend the phase's "read-only schema card" to be **collapsed by default**:

```text
Body › Restaurants                                ＋ restaurant   ⊞ Schema

▸ Restaurant · 5 fields · dated notes · grouped by Status, sub-grouped by Location

Restaurants Kelly and I have tried, liked, or want to try. …

## Records
104 restaurants · 🔖 11 to try · 💚 86 liked · 🚫 7 not liked
```

Expanding the disclosure (or clicking ⊞ Schema) shows the chip view — one row per
field in declaration order, human labels leading, kind as muted suffix text
(`date`, `url`, `text · suggest`, `number 1888–2100`), required as a quiet `*`, choice
chips with their emojis, `legacy` as muted trailing chips. Grouping/`index_by` is
displayed here because it explains the index below (gem and mus both caught that the
phase spec omits it). Empty schema teaches ("No fields yet — add one so `Name @eat/`
can collect facts"); invalid schema stays visibly broken and never impersonates a
healthy empty card; the `＋ restaurant` copy affordance disables with the same reason.
Collapse state lives in view state, never frontmatter.

## Requirement adjustments (called out explicitly)

1. **"Render properly" → "render as a schema."** The deliverable is a schema-aware
   header surface in Reading view and Live Preview, not a fixed Properties row. Success
   is "Bryan never needs to look at the raw row", not "the raw row looks good".
2. **"Very easy to modify" → "very easy to modify *correctly*."** The edits that
   actually happen (add a choice, relabel, add a field, toggle required) become
   one-gesture operations; the edits that strand data (key renames, used removals,
   noun changes) are deliberately *not* easy in v1 — they are refused with a taught
   alternative, pending a migration flow. An editor that makes `liked → loved` one
   keystroke without migrating 86 records would be worse than the orange blob.
3. **The in-flight plan's "read-only schema card" becomes a collapsed summary +
   expandable chip view + editable card (in slice B).** Read-only-forever was the
   original epic's explicit compromise ("edit in Source mode"); this request is the
   evidence that compromise was too timid.
4. **Correct the plan's "re-serialize is a no-op" claim** and make it true: emit
   Obsidian-style YAML (indented sequences), verify with a real-Obsidian round-trip
   fixture.
5. **`record.noun` is immutable in the editor (v1)** — renaming the noun renames the
   kind across capture routes, folders, and Bases filters and deserves its own guided
   flow. Field *kind* changes are YAML-only in v1.
6. **YAML editing stays first-class, not grudging.** Bryan is fastest in vim; `y`
   jumps to the exact line, lint marks carry bob's diagnostics, and a "Done" affordance
   refuses to leave Source mode while the schema has errors.

## Recommended solution

### Render (slice A — amend `bob-cli-k3.7.1.4`, plugin-only)

- View-scoped CSS hide of `.metadata-property[data-property-key="record"]` on album
  surfaces only, exactly per the existing phase spec (restore on type change, file
  switch, unload, non-album notes; never delete or rewrite the property; Source mode
  untouched). Failure mode if the selector ever misses: the raw row is merely visible —
  never corruption.
- The collapsed header summary line and expandable chip view described above, drawn
  from the shared album report service. Owner-hue accent, notebook-header typography
  (`8px` radius, `2px` hue start border), light/dark via Obsidian theme variables,
  wraps at ~375 px, keyboard-operable, one header per source surface.
- **`⊞ Schema` opens the Schema Card read-only** (layout below, no write gestures
  yet), plus the `y` YAML jump and lint marks — `issues[]` already ships `line`,
  `key_path`, `message`, `suggestions` (verified in `report.rs`), so this needs no bob
  change.
- Drop the always-open schema table the phase currently specifies.

### Edit (slice B — new phase `album-schema-editor` + bob writer)

**The Schema Card**, a keyboard-first modal in the Task Card idiom, opened from the
header, the command palette (**Edit album schema** — resolves to the owning album even
when invoked from a record note, which is where you most often want a new choice), and
Command Mode:

```text
╭─ 🍽️ Restaurant · Body › Restaurants ───────────────────────────────╮
│  104 restaurants · dated notes · grouped by Status                  │
│  ▸ Status *     🔖 To try 11   💚 Liked 86   🚫 Not liked 7   ＋    │
│    Category *   text · suggest                                      │
│    Location *   text · suggest · sub-groups the index               │
│    Visited      date · set on 2 of 104                              │
│    Url          url · set on 31 of 104                              │
│    ＋ Add field                                                     │
│  adds 🔁 Regular after 💚 Liked · no record changes                 │ ← consequence
│  ⏎ edit  a add field  c add choice  ! required  s suggest           │
│  ⌥J/⌥K move  ⌃D remove  y YAML  u undo  esc close                   │
╰─────────────────────────────────────────────────────────────────────╯
```

- Live usage counts on choice chips (tabular numerals); labels lead, stored keys shown
  dim in monospace only where they matter (add, rename stages).
- **Every gesture dry-runs first and shows a consequence line before Enter**
  ("12 restaurants have no category · they'll show in bob records check";
  refused: "7 restaurants are 🚫 Not liked").
- Safe ops commit on Enter, one gesture = one scoped commit, with an Undo toast backed
  by bob-returned inverse ops; the card stays open and repaints from the refreshed
  report (schema edits come in bursts — deliberate break from the Task Card's
  write-closes-card rule).
- **v1 ops:** label/plural/dated_notes, add optional field (key derived from label,
  shown before creation), add/relabel/re-emoji/reorder choices, reorder fields (with
  the index-grouping consequence previewed), required/suggest toggles, defaults and
  numeric bounds (typed, never stringified; no default for `status`; distinguish "no
  default" from empty/false/zero).
- **v1 refusals, teaching the path:** rename field/choice keys, merge, remove a used
  field or choice, change noun or kind — refused with the count and "edit in YAML (`y`)
  or wait for the migration flow". cld's full migration op table
  (`field.rename`, `choice.merge` with span-preserving record rewrites in one
  transaction) is the right v2 spec, deferred so v1 ships.

**The writer: `bob albums update STEM [-d] [-f human|json] [-i FILE]`.** Named for
symmetry with the existing `bob records update` (verified: resolve by stem, edit only
supplied value spans, `--dry-run` prints without writing). Follows `cli_rules`:
nested under the `albums` noun, alphabetical options, short aliases, additive JSON.
Human-ergonomic flags can mirror the common gestures; `-i` takes the card's JSON ops
envelope (`schema_version`, `expect` fingerprint, ordered `ops[]`) on stdin — argv is
never built from labels or YAML.

Writer guarantees (the correctness contract cdx rightly insists is part of the
feature, not polish):

1. Open/view/preview/cancel: zero vault writes. A no-op save is byte-identical, no
   commit, no sync.
2. Post-image validated by the same Rust validator capture uses; refusal, never an
   invalid write. Dependent references (`index_by`, `index_facets`, group field)
   updated or refused, never dangling. Cross-album storage-shape clashes
   (`year` is a number in movies) refused by name.
3. Span-preserving emit of the `record:` block only, in Obsidian's YAML style; every
   other byte preserved. Anchors/aliases/duplicate keys the span editor can't preserve
   → typed refusal + source fallback, never a regex guess.
4. `expect` fingerprint guard: an edit made on another host or in Source mode between
   card open and Enter refuses with the stale-note error. Before apply, flush the open
   editor buffer via a supported save path and verify revisions; the race test
   (two panes, delayed save) runs in real Obsidian — shell tests cannot prove it.
5. One transaction under the maintenance lock: album frontmatter + rebuilt
   `[!records]` index (when grouping/choices/labels change) in one scoped commit
   (`albums: update eat.md (status +regular)`); owner `## Albums` bytes untouched
   (counts are drawn). If the index can't be safely rebuilt, the save refuses and the
   draft survives with the reason.
6. Dry run returns the diff, impact counts from a complete record scan (never the
   visible rows), derived keys, and the consequence text; takes no locks.
7. Result includes `inverse_ops`; `u` replays them as a normal edit, keeping git
   history linear. "Saved locally; sync failed" retries sync only, never the mutation.

**Report additions (additive, schema version 1)** so the card can paint and round-trip
the whole contract: per-field `suggest`, `default`, `min`, `max`, `line`, `filled`;
per-choice `count`; per-album `dated_notes`, `legacy`, `schema_fingerprint`. Mirror in
`bob records show -f json` so the two surfaces stay one model. Measured latency
(cld, apollo): `albums list -f json` ≈ 0.4 s, fine for card-open and per-gesture dry
runs after a typing pause; debounce, never per-keystroke.

### What stays out

No second schema file, no Bases-as-schema-editor (`eat.base` remains the records
table), no capture grammar for schema, no generic nested-properties framework, no
per-record value editor (noted by cld as the higher-frequency follow-up — it should
not grow this task), no mobile guided writes without an explicit backend strategy
(the strip degrades to read-only + "Edit YAML" there, or is skipped if Bryan never
uses mobile — open question).

## Sequencing and acceptance

1. **Slice A — amend `k3.7.1.4` now** (in progress, no header code exists yet, so the
   reshape is cheap; coordinate with the phase owner rather than compete). Plugin-only:
   hide, collapsed summary, chip view, read-only Schema Card, `y` jump + lint marks.
   Existing phase fixtures stand: Properties isolation, unrelated `record` key,
   type change, empty schema, ordered choices, unload.
2. **Slice B — new phase after k3 lands:** report JSON additions + emitter style fix
   (small/medium), `bob albums update` with ops/dry-run/impact/transaction/inverse ops
   (large), editable card gestures + consequence lines + Undo + record-note entry
   (medium/large), real-Obsidian e2e.
3. **Acceptance spine** (merged from cdx's checklist and cld's §5.8): the
   Properties-`summary` round-trip fixture; no gesture writes without a dry run;
   stale-`expect` refusal; rename/merge (v2) rewrites exactly the counted records in
   one commit and `u` restores; broken schema shows the red state and lint line, and
   "Done" won't leave Source mode while errors stand; label edits leave stored tokens
   and record files untouched; cancelled/no-op edits byte-identical; light/dark,
   375 px, keyboard-only, screen-reader labels; plugin disable restores the native
   row.
4. **Candidate decision record** (needs Bryan + the memory-write flow): "Album schemas
   are edited through bob" — plugin presents, bob writes, YAML stays first-class;
   reopens if Obsidian ships a public property-widget API or native nested-property
   editing.

## Open questions for Bryan

1. **Mobile:** do you use Obsidian on mobile at all? If not, the read-only mobile
   fallback disappears from scope.
2. **Chord:** should `Ctrl+Shift+P` (Task Card) open the Schema Card on album notes,
   where it is otherwise idle? Nice rule ("edits the properties of what I'm on"), but
   only if you want the chord overloaded.
3. **Commit granularity:** one commit per gesture (recommended: revertable, honest)
   vs. a batched draft-and-save session. If burst-of-five-commits noise would bother
   you, say so before slice B is planned.

## Provenance

- Five independent reports in this directory (`__cdx`, `__cld`, `__grk`, `__mus`,
  `__gem`); grk's rendered figures accompany its report.
- My verification this turn: `bob-cli-k3` epic bead (audited read);
  `plan:202611/album_plugin_ui.md` (audited read — shared contract and `album-header`
  phase text quoted above); `src/native/records/schema.rs` (mapping requirement,
  `recover_album_noun`, key allowlists); `src/native/albums/report.rs` (`AlbumField`
  JSON lossiness, `AlbumIssue` line/key_path/suggestions); `src/native/records/cli.rs`
  (`bob records update` span-edit + dry-run precedent); `~/bob/eat.md` bytes via
  `cat -A` (healthy nested YAML; serde-style unindented `legacy` sequence);
  `sase/memory/cli_rules.md` (audited read — subcommand naming and option rules);
  screenshot `~/tmp/screenshots/20261112_054646.png`.
- Key external claims carried from the reports (not re-fetched): Obsidian help on
  unsupported nested properties; the 1.9.2 `[Object object]` forum regression; absent
  property-widget API in `obsidian.d.ts`; community nested-property plugins patching
  undocumented internals; Obsidian 1.10.3's "Bases List view supports nested
  properties" concerns Bases display, not Properties editing (cdx).
