# Record albums: rooting record collections in the area network

Researcher: mus · 2026-11-10 · swarm report (`__mus`)

## Question

Bryan's proposal: give record-note collections ("albums") a root parent in the
area/project note network, move each record type's schema from `config.yml`
into the album note's frontmatter, dezorg the album notes (as was done for
`job.md`), render a record summary in each album note plus a new H2 section in
the parent area/project note, rename `podcast.md` to `podcasts.md`, add an
`album` value for the `type` frontmatter field, and add glossary terms for
"album note" and "record note". Is this a good idea, what should change, and
what is the recommended implementation?

## Bottom line

- **Yes, this is a good idea, with three adjustments.** Rooting collections
  under areas, dezorging the album notes, and rendering summaries are all
  sound and mostly low-risk. But (1) the concept should be called a
  **collection note**, not an "album note"; (2) `podcast.md` must **not** be
  renamed to `podcasts.md` (that file already exists — the proposal conflates
  the type note with the collection note); and (3) the config-to-frontmatter
  schema migration should land **last**, behind a transition period, not first.
- **The type-note / collection-note distinction is the load-bearing
  clarification.** Today every record type is already three vault pieces
  (`src/native/records/init.rs`: type note `<type>.md`, collection note
  `<dir>.md`, starter `<dir>.base`). The proposal's "album" is the middle
  piece. Once that is explicit, every other clause falls into place.
- **Parents are cheap and safe; rendering follows existing precedent; schema
  migration is where all the risk lives.** Phase it in that order and each
  phase is independently shippable.

## Status quo (verified 2026-11-10)

### The four configured types

`~/.config/bob/config.yml` declares `records:` with four types; `bob records`
confirms live counts:

| Type id | Folder | Collection note | Type note | Notes |
|---|---|---|---|---|
| `restaurant` | `eat/` | `eat.md` | `restaurant.md` | 104 |
| `podcast` | `podcasts/` | `podcasts.md` | `podcast.md` | 15 |
| `show` | `tv/` | `tv.md` | `show.md` | 23 |
| `movie` | `movies/` | `movies.md` | `movie.md` | 10 |

`bob records show <type>` prints schema, choice labels, and common values.
`docs/records.md` is the contract: schema loading, value validation, filename
planning, capture creation (`Title @dir/`), and `bob records check/new/update`.

### What each piece looks like today

- **Record notes** (`eat/30_burger.md`, `podcasts/talk_python.md`) carry
  `parent: "[[eat]]"` / `parent: "[[podcasts]]"`, `type: "[[restaurant]]"` /
  `type: "[[podcast]]"`, `title`, schema fields in schema order, `created`,
  and an always-present `## Notes`. Parents point at the **collection**, not
  the area. Verified across `eat/`, `podcasts/`, `tv/`, `movies/`.
- **Type notes** (`restaurant.md`, `podcast.md`, `movie.md`, `show.md`) carry
  `parent: "[[type]]"`, no `type` field, one paragraph of prose, and a
  `Schema: bob records show <type>` pointer. They are schema documentation,
  not collections.
- **Collection notes** are inconsistent — this is the dezorg gradient:
  - `movies.md` (`parent: "[[fun]]"`) and `podcasts.md`
    (`parent: "[[mind]]"`): hand-maintained, short prose, `![[movies.base]]` /
    `![[podcasts.base]]` embed, plus hand lists. **This is already the target
    shape.**
  - `tv.md` (`parent: "[[fun.md|fun]]"`): nearly empty, one bullet, no base
    embed despite `tv.base` existing and `tv/` holding 23 notes.
  - `eat.md`: still fully zorg-generated — `generated_from_zorg: true`,
    `parent: [[h2_role]]` (a dead zorg-era link), a ~200-row restaurant table,
    no `.base` embed despite `eat.base` existing with five grouped views
    (All, Favorites, To Try, By Town, Recently Tried). **This is the big
    dezorg job.** `eat/` records were already extracted (104 notes with
    `source_*` provenance anchors) and `maybe_eat.md` notes it was migrated to
    `to_try` records on 2026-11-08 — but the source table was never retired.
- **Area notes** (`body.md`, `dev.md`, `fun.md`, `job.md`) render `## Tasks`
  (status-grouped) and a machine-owned `## Notebooks` catalog
  (`bob notebooks sync` owns content, Bryan owns position — see the
  `notebook` glossary strand). There is no records section anywhere yet.
- **Glossary** (`sase/memory/glossary/`) has `area-note`, `root-parent`,
  `notebook`, `project-note`, etc. There is **no `record-note` term**, even
  though the `notebook` strand already writes "Not a … a record note" — a
  dangling forward reference this proposal would fix.

## Critique, clause by clause

### 1. "Give each record a root parent" — yes, and it is nearly free

The mechanism already exists: record → collection → area is a `parent` chain,
and the root-parent walk derives the area at read time (see `root-parent`
strand). Adding `parent: "[[body]]"` to `eat.md` roots all 104 restaurant
records at `body` with **zero per-record edits**. Nothing task-related changes:
record notes hold no `#task`s, so Ready lanes, the review walk, the per-note
Ready cap, and Pomodoro homes are untouched.

One implementation caveat to verify, not a blocker: the root-parent walk must
**pass through** collection notes the way it passes through notebooks (the
`notebook` strand documents pass-through for notebooks explicitly). If the
walker only recognizes area/project/notebook links, album notes need the same
one-line pass-through treatment. File it as an acceptance criterion, not a
redesign.

### 2. Parents: accept `eat → body`, reject `podcasts → dev`

- `eat.md` → `[[body]]`: accept. Its current parent `[[h2_role]]` is a dead
  zorg link; anything is an upgrade. (Restaurants are also shared life with
  Kelly — arguably `love` — but `body` is the sane primary; backlinks and
  `Related:` lines can name the rest.)
- `podcasts.md` → `[[dev]]`: **reject**. The collection is heterogeneous
  (Python, comedy, productivity, TED). Its current parent `[[mind]]` is
  correct; `dev` would misfile every non-programming show. Keep `[[mind]]`.
- `tv.md`, `movies.md` → keep `[[fun]]`. No change needed.

### 3. "Album" is the wrong name — call it a collection note

Three reasons, strongest first:

1. **The codebase already named it.** `PieceKind::Collection` in
   `src/native/records/init.rs`, "collection note" throughout `docs/records.md`
   and `bob records init` help. Renaming the concept to "album" forks the
   vocabulary between code/docs and vault for no gain.
2. **`album` already means something.** It reads as a music LP. A future
   `listened` record type for music albums would then be absurd ("the album
   record under the album note"). `collection` has no such collision.
3. **Obsidian users already say "collection note"** for exactly this
   index-over-a-folder pattern.

If Bryan loves the word, keep `album` as a glossary alias, the way `prj note`
aliases `project-note`. But the canonical term, the `type` link, and any new
code should say `collection`. The rest of this report uses "collection
(album)" where the proposal's wording matters.

### 4. Do not rename `podcast.md` to `podcasts.md` — it collides

`podcasts.md` **already exists** (the collection note, parent `[[mind]]`,
with subscribed/unsubscribed lists and the base embed). `podcast.md` is the
**type note** (`Use this type for one-note-per-show records…`, `bob records
show podcast` pointer). The proposal conflates the two pieces. There is
nothing to rename; the collection note for podcasts is done and needs only a
parent it already has.

The real question underneath: should the type note and collection note
**merge** (one file per record type instead of two)? I recommend **no**:
record notes link `type: "[[podcast]]"`, and folding that identity into
`podcasts.md` would churn 15+ notes' frontmatter per type for zero reader
benefit. The two-note split mirrors `area.md` (the type) vs `body.md` (an
area) and should stay. Note also that `eat` is the odd one out in naming
(folder `eat/` ≠ plural of `restaurant`); that is fine and needs no action —
`init.rs` already treats `dir` and type id as independent.

### 5. `type: "[[collection]]"` on collection notes — yes, with one addition

Collection notes currently have **no `type`** at all. Giving them
`type: "[[collection]]"` (proposal says `[[album]]`; see §3) makes them
queryable (`bob query`, Bases, `type.md` children listing) and gives
`bob records check` something to lint (every `<dir>.md` for a configured type
must exist, carry the collection type, and name a valid parent). Add a
`collection.md` type note under `[[type]]` mirroring `restaurant.md`'s shape,
and update `bob records init` to stamp the new type note's markdown and the
collection markdown accordingly.

### 6. Schema migration (config → frontmatter) — yes, but last and transitional

This is the highest-value and highest-risk clause. Weighed honestly:

**For frontmatter-as-source-of-truth:** schema lives with the collection it
describes, visible and editable in Obsidian on any host (including the Mac,
which never sees `~/.config/bob` except via chezmoi); per-type evolution
without touching global config; the collection note becomes genuinely
self-describing, which is the aesthetic heart of this proposal.

**Against / caution:** YAML-in-YAML quoting and Obsidian Properties noise
(solved: nest everything under one `schema:` mapping key — Obsidian tolerates
nested objects, and `.base` files already set precedent for config-shaped
bodies); vault-sync merge conflicts landing mid-schema on another host
(requires the same failure isolation `docs/records.md` demands of config:
a bad album schema disables only that type, with a typed diagnostic naming
note + field); every `bob` invocation now reads vault files for schema
(cache it; four small files, negligible); capture completion and the Mac
client consume schema through `bob`'s JSON, so they are unaffected as long as
bob remains the parser; and the vault-global property-kind invariant
("shared property names must share storage shape") must be enforced across
album notes at load, which bob can do since it loads all types anyway.

**Recommended path:** transitional dual-read. (a) `bob` reads schema from the
album note's `schema:` frontmatter when present, else falls back to
`config.yml` — so migration is per-type, reversible, one PR per type.
(b) `bob records check` gains schema validation (unknown keys, bad kinds,
property-kind conflicts across types) with typed diagnostics. (c) Migrate
`movie` first (10 notes, simplest consumer), then the rest. (d) Only when all
four are migrated and clean does `config.yml`'s `records:` slim down to a
registry (or retire). Never two sources of truth without a stated precedence:
**frontmatter wins when present, config is the fallback, and `check` reports
which source each type resolves from.**

### 7. Dezorg — `eat.md` is the project; the others are polish

"Dezorged appropriately" has a concrete meaning from the `job.md` precedent
(verified: zorg table → prose + `## Notebooks` with a `legacy_job` notebook
holding the moved notes, Tasks intact): extract the data into typed notes
(done), replace the generated table with a hand-owned note, park anything of
historical value in a `legacy_*` notebook, drop the `generated_from_zorg` keys.

Applied per collection:

- **`eat.md`**: replace the ~200-row table with prose ("what this list is",
  verdict semantics), `Related: [[drink]] [[maybe_eat]]`, the
  `![[eat.base]]` embed (five views already exist and are good), and small
  hand-curated H2s (see §8). Convert `maybe_eat.md` (already migrated to
  `to_try` records) into a `legacy` notebook or archive it; keep the LID
  provenance (records carry `source_*` anchors — nothing is lost).
- **`tv.md`**: one bullet + no embed despite 23 records — give it the
  `movies.md` treatment (prose + `![[tv.base]]` + watching/to-watch H2s).
- **`podcasts.md`, `movies.md`**: essentially done; add the summary H2 (§8)
  and the `type`/`schema` frontmatter when §6 lands.

### 8. Album summary rendering — live embeds first, hand lists second

The summary must never be a second source of truth that rots. Order of
preference:

1. **The `.base` embed** (`![[eat.base]]`) — already live, grouped, counted.
   This is the summary; everything else is commentary. `eat.md` getting its
   embed is the single highest-value rendering change in the proposal.
2. **Two or three hand-curated H2s** for what Bases do poorly: editorial picks
   ("Favorites worth the drive", "To-try shortlist", "Recently loved").
   Hand-owned, a handful of links each, allowed to go stale gracefully
   because they are taste, not inventory.
3. **A compact generated census** (counts by status) only if `bob` owns it —
   e.g. `bob records sync` refreshing a bounded `## Records` block the way
   `bob notebooks sync` owns `## Notebooks`. Do not hand-maintain counts.

### 9. Area-note H2 section — one machine-owned `## Records` catalog

Follow the `## Notebooks` precedent exactly: a machine-owned catalog section
whose **content is bob's and whose position is Bryan's**. Proposed shape per
child collection: album link, one-line description, live counts by status
(`💚 87 liked · 🔖 12 to try`), and one "spotlight" line the album note
declares (e.g. eat → to-try shortlist; podcasts → subscribed count). Owned by
a new `bob records sync` (or folded into nightly), never hand-edited, so it
cannot fight the `## Tasks` writer. Start hand-written on `body.md` to prove
the shape, automate once the shape survives a month.

### 10. Glossary — draft both terms now (with the naming fix)

`record-note.md` fills a dangling reference (`notebook.md` already excludes
"a record note" without defining it). Drafts:

- **Record Note** (`record-note.md`, aliases: `record`): a vault note holding
  one durable thing (a restaurant, show, recipient, session cluster) with
  `parent` naming its collection, `type` naming its record type, `title`,
  schema fields in schema order, `created`, and an always-present `## Notes`.
  Lives in the type's folder; created by capture (`Title @dir/`) or
  `bob records new`; linted by `bob records check`. Not a task residence, not
  a notebook, not a reference note.
- **Collection Note** (`collection-note.md`, alias: `album note`): the
  `<dir>.md` index over one record folder — prose, related links, the
  `.base` embed, curated H2s. Carries `type: "[[collection]]"`, a `parent`
  naming its area (or project), and eventually the `schema:` source of truth.
  Distinct from the `<type>.md` type note under `[[type]]`.

## Recommended solution (phased)

1. **Phase 0 — language.** Record a decision: canonical term `collection
   note`, `album` kept as alias only; no `podcast.md` rename; `podcasts`
   stays under `[[mind]]`. Write both glossary strands.
2. **Phase 1 — parents + types (manual, one sitting).** Set
   `eat.md → [[body]]` (+ `type: [[collection]]`), stamp `type` on the other
   three collections, add `collection.md` under `[[type]]`, extend `bob
   records check` to lint the new invariants, extend the root-parent walk
   pass-through if needed. Independently shippable; immediately improves
   graph/backlinks/queries.
3. **Phase 2 — dezorg + rendering.** Rewrite `eat.md` (prose + base embed +
   curated H2s), retire/park `maybe_eat.md`, treat `tv.md`, hand-write
   `## Records` on `body.md` to prove the area-section shape.
4. **Phase 3 — automation.** `bob records sync` (or nightly job) owns the
   area `## Records` catalogs; `init` scaffolds the new frontmatter shape.
5. **Phase 4 — schema migration.** Dual-read → `check` validates →
   per-type migration starting with `movie` → config slims to registry.
   The only phase allowed to break `bob`, and structured so it cannot break
   anything else.

## Verdict

Build it, with the adjustments above: **collection, not album; no podcast
rename; mind, not dev; parents and rendering before schema migration.** The
intuition is right — everything Bryan tracks deserves a home in the area
network — and the proposal's best property is that phases 1–2 deliver nearly
all the felt value (navigation, recall, beauty) before the riskiest work
begins.
