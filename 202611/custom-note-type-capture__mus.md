# Generalized capture support for custom note types

Research report (swarm member `mus`). Independent investigation; no peer
reports were consulted.

## Verdict up front

Yes, build this — but narrower than asked, in two phases, with the type
registry living in the vault (not in `config.yml`), and with TV shows and
movies explicitly **out** of scope for per-note types. The recommended
end state:

1. **Phase 1 — registry + `bob note create`.** Each custom note type is
   declared by a machine-readable schema in its existing `type` note
   (`restaurant.md`, `podcast.md`, …). A new `bob note create --type …`
   command validates required frontmatter, picks the directory and slug,
   renders the note, and reports dry-run bytes. No capture-grammar change.
2. **Phase 2 — capture sugar.** Generalize the existing project-note seal
   (`@route^id@`) to `@parent^slug@`: when the parent is a registered
   custom-type directory index, Bob creates a typed note instead of a
   project note, with required fields supplied as `key=value` pairs (plus
   an eat-style positional shorthand) and completed through a new
   `capture-complete` field context. Bob Mac Capture renders that context
   as a form sheet without parsing anything itself.

Everything below justifies that shape: what the vault looks like today,
why the idea is good, where the request overreaches, the candidate-type
audit, the syntax trade-offs, and the concrete schema and rollout.

## How custom-typed notes work today (observed, not assumed)

### The `eat/` pattern

- `eat.md` (vault root) is the human index: grouped `TABLE` sections of
  one-line rows such as
  `- 250828 240410#7o 30 Burger | Burgers + Dogs | Linden | LID::30burger …`.
  It carries a `generated_from_zorg` header — it is a converted artifact,
  not hand-maintained going forward.
- `eat/` holds one note per restaurant (92 files), e.g.
  `eat/30_burger.md`, `eat/a_cozy_corner.md`,
  `eat/pardon_my_cheesesteak.md`. Frontmatter observed across samples:

  ```yaml
  parent: "[[eat]]"
  type: "[[restaurant]]"
  title: "30 Burger"
  status: liked            # liked | not_liked observed (null category/lid possible)
  category: "Burgers + Dogs"
  location: "Linden"       # plain text OR wikilink [[nj_towns#…|cranford]]
  source_group: union_county
  lid: "30burger"          # null observed when unknown
  companions:
    - "[[kelly]]"
  source_note: "[[eat]]"   # lineage back to the index row
  source_anchors: [z-…]
  source_dates: ["250828", …]
  source_lines: [75]
  ```

  Body shape is `# Title / ## Notes / ## Source` with a fenced copy of the
  index row. `eat.base` renders the dashboard purely from notes
  (`file.inFolder("eat")`, `note.type == link("restaurant")`), so the
  hand-edited `eat.md` table is already redundant for browsing.

- There is **no capture path** for a new restaurant today. Capture routes
  (`src/native/capture_targets.rs`, `routable_route_for_root_file`) only
  cover **root-level** `*.md` files — `nested/child.md` is explicitly
  skipped — so `@eat…` cannot address `eat/` at all, and no grammar token
  creates a standalone note except the project-note seal
  (`@route^block-id@`, `src/native/capture/project_note.rs`), which
  hardcodes `type: [[project]]`, `status: wip`, and the
  `<route>_<block-id>.md` path shape.

### The `podcasts/` pattern (same architecture, smaller)

- `podcasts.md` index + `podcasts/*.md` (15 files) + `podcasts.base`
  dashboard (`note.type == link("podcast")`). Per-show frontmatter:

  ```yaml
  parent: "[[podcasts]]"
  type: "[[podcast]]"
  title: "Talk Python to Me"
  status: subscribed       # subscribed | unsubscribed observed
  category: python
  url: https://talkpython.fm
  zorg_id: talk_python
  ```

  Same lineage fields (`source_note`, `source_anchors`, …), same missing
  capture path.

### The `type` notes already exist — as prose

`type.md` (`parent: [[org]]`) collects the convention: children
`restaurant.md`, `podcast.md`, `article.md`, `project.md`, `area.md`,
`ref.md`, `day.md`, `mail.md`, `done.md` each document one
`type: "[[…]]"` value in prose (e.g. `restaurant.md`: "one-note-per-
restaurant records under [[eat]]"). No schema is machine-readable today;
nothing validates `status` enums, required keys, or directory placement.
This is the natural registry anchor (more in the recommendation).

### Capture grammar density (the constraint every syntax must respect)

- `docs/reference/capture-syntax.md` + `docs/capture.md`: `@` says where,
  `#` names a place or a task type, `%` says how. Grammar is at version 19
  (`capture-complete` JSON `grammar: 19`); every marker composes with
  scheduling (`s:<N>`), priority (`$<N>`), clipboard (`%c`), relations
  (`~`), dependencies (`&`), and blockers (`*`).
- `#` at an item edge is already claimed by **task** types (ALL-CAPS
  Pomodoro themes; unknown names refuse with `type_not_configured`).
  Lowercase `#restaurant` currently refuses — usable namespace, but easily
  confused with task typing.
- `capture-complete` is the beauty engine: every picker (`task_type`,
  `directive`, drawers, Pomodoro names, …) is a JSON context the thin
  clients render. Per the mac-capture thin-client decision, Bob Mac
  Capture never parses or previews locally — any new syntax **must** come
  with `capture-complete` rows, `capture-parse` preview, and
  `--dry-run` bytes, or the menu-bar client cannot offer it.

## Critique of the plan

**It is a good idea.** The two existing libraries prove the pattern twice
independently (same frontmatter shape, same index+notes+`.base` triple,
same lineage fields). A third hand-rolled instance would cement a
maintenance burden: today adding a restaurant means hand-editing YAML with
no validation, no slug-uniqueness check, and no atomicity (capture's
plan-then-write guarantee in `src/native/capture/plan.rs` does not cover
hand edits). Generalizing once is cheaper than documenting the manual
ritual a third time.

**But four adjustments are warranted** (each called out as requested):

1. **Registry belongs in the vault, not in `config.yml`.** The request
   says "each custom type should be able to define which frontmatter
   fields must be defined" without saying where. Host config
   (`~/.config/bob/config.yml`, cf. `docs/reference/configuration.md`)
   does not sync; type definitions are Bryan's data and must ride the
   vault like relation-label journals (`.bob/…/*.jsonl`) and theme prefs
   do. The `type` notes are the obvious home: they already are the
   human-readable contract, one file per type, synced and linkable.
2. **Directory ↔ type is many-to-one with a default, not 1:1.** The
   request assumes one directory per type. Keep `directory` as the
   default home plus an allow-list, so e.g. a future `places/` directory
   could host both `restaurant` and `cafe` types, and `maybe_eat`
   candidates can be `status: want_to_try` rows of type `restaurant`
   rather than a second type.
3. **Optional fields must be supported.** The request leaves this open;
   I decide yes. Required-only would force junk values (`category: null`
   is already observed in the wild — better to omit an optional key than
   to bless `null`). Capture offers optional fields after required ones
   are satisfied and omits unfilled ones.
4. **`source_*` lineage fields must be machine-written, never user input.**
   `source_note/anchors/dates/lines` made sense for the zorg conversion
   backfill. For fresh captures they are either auto-filled (parent index
   row, if the user appends one) or omitted. The capture form should never
   ask for them. Related: **do not append rows to `eat.md`/`podcasts.md`
   tables on capture.** The `.base` dashboards already render from notes;
   keeping a hand-edited table in sync doubles every write and its
   alignment (`vim_utils/align_tables.vim`) cannot run inside Bob's
   atomic commit. Record the index note as `parent`, skip the table edit,
   and let the bases be the index.

## Candidate types audit (thinking hard, as asked)

| Candidate | Files today | Per-note type? | Reasoning |
| --- | --- | --- | --- |
| Restaurants (`eat/`) | 92 notes, rich schema, revisited often | **Yes — first** | The motivating case. Revisit-heavy (notes accumulate visits), clear required set (title, status, category, location), big win. |
| Podcasts (`podcasts/`) | 15 notes, stable schema | **Yes — second** | Same lifecycle as restaurants (subscribe → many episodes). Small schema delta proves generality. |
| `maybe_eat` candidates | Rows in `maybe_eat.md`, no per-place notes | **No — use `status`** | A want-to-try place is a `restaurant` with `status: want_to_try`, promotable to `liked` in place. A separate type would fork every restaurant field. |
| Drinks (`drink.md`) | One note, liquor-store list | **No** | Two sections, no per-venue notes, no `.base`. Fold into a future `place` type if venue notes ever appear. |
| TV shows / movies (`tv.md`, `chad_movie.md`) | One bullet + one prompt note; **no** `type` note, no directory, no `.base` | **No — recommend against** | Consumption is watch-once, not revisit-and-accumulate like restaurants/shows. Volume does not justify a library (observed: a single bullet). A per-title note per watched film would create hundreds of near-empty notes. Better: a `watchlist` of **tasks** (`#task` + `s:`/`$` scheduling already exist) with links, or `ref` notes for the few titles with real notes. Revisit only if viewing notes become a habit. |
| Books / papers | Covered by `ref/` + `bob ref create` | **No** | Already has a full ingest pipeline (`docs/ref.md`); do not duplicate. |
| Music (`music.md`) | Mixed bullets (piano, links) | **No** | No per-item schema evident; tasks + refs suffice. |

Net: ship with exactly two registered types (`restaurant`, `podcast`).
Design the registry for N types; do not pre-create speculative ones. The
request's instinct ("I might be wrong about this") is right for
TV/movies — the winning move is tasks, not notes.

## Required-field inventories (proposed, derived from observed notes)

`restaurant` (directory `eat/`, parent `[[eat]]`):

- required: `title` (text), `status` (`liked | not_liked | want_to_try |
  retry`), `category` (text, free — values observed range from "Sushi" to
  `[[eat#^z-…|breakfast]]` links), `location` (text-or-wikilink).
- optional: `url`, `companions` (default `["[[kelly]]"]`), `notes`.
- machine: `parent`, `type`, `lid` (slug, see below), `source_*` (only
  when appending to an index row — which v1 does not).

`podcast` (directory `podcasts/`, parent `[[podcasts]]`):

- required: `title`, `status` (`subscribed | unsubscribed`), `category`
  (free text today: `python`, `ai`, …).
- optional: `url`, `notes`.
- machine: `parent`, `type`, `zorg_id`/slug.

Note the slug mess worth cleaning: restaurants use `lid`, podcasts use
`zorg_id`, both hand-picked (`30burger`, `talk_python`). The registry
should declare one `slug_from: title` rule (lowercase, spaces → `_`,
strip punctuation, case-insensitive uniqueness like `bob ref create` ids)
and treat `lid`/`zorg_id` as legacy aliases of the slug, not separate
concepts. Do not ask the user for a slug except on collision.

## Capture syntax: options weighed

Constraints from the codebase: must not collide with the 19-grammar
token space; must be expressible through `capture-complete` /
`capture-parse` / `--dry-run` JSON for the thin Mac client; must keep
the atomic plan-then-write guarantee; must keep working when typed blind
(no picker) as well as interactively.

**Option A — generalized seal (recommended): `@parent^slug@`.**
Today `@route^block-id@` creates `<route>_<block-id>.md` as a project
note. Generalize: if `parent` resolves to a registered custom-type
directory index, the seal creates `<dir>/<slug>.md` with that type's
template instead. Type is inferred from the directory default; an
explicit override appends the type (`@eat^titos@restaurant` is accepted
but redundant while `eat/` hosts one type). Fields follow as pairs:

```bash
bob capture '@eat^titos_burritos@ Titos Burritos | Burritos | Cranford'
bob capture '@eat^new@ status=want_to_try La Colina | Mexican | Cranford'
bob capture '@podcasts^talk_python@ Talk Python to Me https://talkpython.fm category=python status=subscribed'
```

The `|`-positional form mirrors the existing `eat.md` table idiom
(name | category | location) and is the "beautiful" fast path; named
`key=value` pairs cover everything else. Pros: zero new sigils; `@`
keeps meaning "where"; the seal already means "create a note, not a
task"; back-compatible (non-typed parents keep today's project behavior).
Cons: requires teaching the `@`-router subdirectories (it currently only
routes root files) — but that work is needed regardless.

**Option B — `%note` directive.** `bob capture '%note restaurant …'`.
Pros: no router change. Cons: a fourth meaning for `%` (clipboard,
Pomodoro note, template, …), verbose for the common case, and it splits
"destination" across two markers (`%note` + directory), violating the
`@`-says-where rule.

**Option C — `bob note create` only, no capture syntax.** A full CLI
(`--type`, `--title`, `--set key=value`, `--dry-run`) without any
one-line capture spelling. Pros: simplest, most discoverable via
`--help`. Cons: misses the request's core ask — fast capture from the
menu-bar box. Keep it as Phase 1 (it is also the testable engine Phase 2
delegates to), not the end state.

**Option D — piggyback `#`.** `@eat Titos #restaurant …`. Rejected:
`#` at the edge already means task type; overloading note types onto it
guarantees confusion between `#READ` the task and `#restaurant` the note,
and completion rows would mix Pomodoro themes with note schemas.

**Interactive filling (the "as easy as possible" requirement).** Whichever
spelling, `capture-complete` gains a `note_field` context: with the seal
typed, each missing required field is a row (`category=` with recent
values from the type's existing notes — the eat cuisine list is the
suggestion source, like Recent themes today); accepting inserts `key=`
and advances to the next gap. `capture-parse` reports
`missing_required_fields`; `bob capture` refuses until they are filled,
exactly like today's incomplete-picker refusals (`capture-parse` needs
`task_link`, etc.). Mac Capture renders the rows as a form sheet; it
never validates locally. Optional fields appear once required ones are
satisfied. This is the same picker-then-refuse loop the grammar already
uses for `:`, `/`, `+`, `&`, `*`, `~`, `!` — no new interaction model.

## Reliability notes

- **Atomicity and preview**: plan-then-write must cover the new note plus
  any index/daily-note touch (none in v1), with `duplicate_slug`
  detection pre-write, case-insensitive, vault-wide within the type's
  directories — mirroring `duplicate_capture_target` and `ref create` id
  rules. `--dry-run` prints the full rendered note bytes.
- **Validation**: unknown field → refuse with `unknown_field` +
  did-you-mean (like `type_not_configured`); bad enum → refuse with the
  allowed set; bad wikilink/url → refuse before writing. Never write a
  note that fails its own schema.
- **Grammar version**: bump to 20 with the seal generalization and field
  pairs; keep JSON additive (`note_type` object beside existing kinds).
- **Back-compat**: `@route^id@` with a non-typed parent keeps today's
  project-note behavior byte-for-byte; existing `eat/*` notes without a
  registry entry keep rendering (registry absence never invalidates
  notes).

## Recommended solution (end state)

1. **Registry in the vault.** Each `type` note gains a fenced
   machine-readable schema block (frontmatter `schema:` mapping or a
   designated code fence — pick frontmatter; Dataview already reads it):
   `directory`, `parent`, `required[]` (name + kind: text/enum/wikilink/
   url + values), `optional[]`, `defaults`, `slug_from`, and an eat-style
   `capture_order` for the positional `|` form. `bob note types` (or
   `bob capture-targets -v`) lists and lints the registry.
2. **Phase 1: `bob note create --type restaurant --title … --set …`.**
   Full validation, slug derivation, dry-run bytes, JSON envelope. No
   grammar change; Mac Capture can already shell it.
3. **Phase 2: seal sugar + `note_field` completion.** Generalize the seal
   per Option A; sub-directory routing; positional `|` shorthand per
   type's `capture_order`. Mac Capture gets a field sheet for free via
   `capture-complete`.
4. **Seed with two types only**: `restaurant`, `podcast`. TV/movies stay
   tasks; `maybe_eat` becomes a status; `drink` waits for a real venue
   habit. Add a type only with its `type` note + ≥5 real notes waiting.
5. **Docs**: extend `docs/reference/capture-syntax.md` (new seal rows),
   `docs/capture.md` (field-filling walkthrough), and each type note's
   prose; `bob capture --help` gains three examples, not the full schema.

## Open questions for Bryan

- Is `want_to_try` the right third restaurant status, or should
  `maybe_eat` stay a separate list forever?
- Slug readability vs stability: okay to derive `la_colina` from title
  and treat `lid`/`zorg_id` as legacy, or do those ids carry meaning worth
  preserving verbatim?
- Should a fresh restaurant capture also offer to file a first-visit
  `#task` (e.g. "try La Colina") linked from the note — or is the note
  alone the right unit?

## Sources consulted

Vault: `eat.md`, `eat.base`, `eat/30_burger.md`,
`eat/a_cozy_corner.md`, `eat/pardon_my_cheesesteak.md`,
`eat/riverside_cafe.md`, `maybe_eat.md`, `drink.md`, `podcasts.md`,
`podcasts.base`, `podcasts/talk_python.md`,
`podcasts/ai_daily_brief.md`, `podcasts/gtd_podcast.md`, `tv.md`,
`chad_movie.md`, `music.md`, `type.md`, `restaurant.md`, `podcast.md`,
`article.md`, `project.md`, `area.md`, `ref.md`, `books.md`.
Repo: `docs/capture.md`, `docs/reference/capture-syntax.md`,
`docs/reference/cli/capture.md`,
`docs/reference/cli/capture-complete.md`, `docs/task-types.md`,
`docs/ref.md`, `docs/reference/configuration.md`,
`src/native/capture/project_note.rs`,
`src/native/capture_targets.rs` (`routable_route_for_root_file`),
`src/native/capture_language/type_marker.rs`,
`src/native/capture_complete/cli.rs`,
`src/native/ref_library/frontmatter.rs`.
