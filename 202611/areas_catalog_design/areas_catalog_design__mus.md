# Areas Catalog (`## Areas`): Design Research

- **Question:** how should bob render a generated `## Areas` section listing an
  area note's direct child area notes (plus the top-level areas under
  `~/bob/area.md`), mirroring the existing generated `## Projects` catalog?
- **Verdict:** good idea, worth building. Child areas are currently invisible —
  `love.md` has five child areas (`abby`, `family`, `fun`, `kelly`,
  `vacation`) and renders no catalog for any of them; same for `cash.md`
  (`bank`, `recur`), `gtd.md` (`gtd_daily`, `inbox`), and `inbox.md` (three
  inbox areas). A generated `## Areas` catalog closes that gap with the same
  machinery as the three existing catalogs, and it is *safer* than any of them
  because area rows carry no lifecycle and affect no task state.
- **Recommended solution:** a new `AREAS` shared-region spec (`[!areas]` under
  `## Areas`, first-written before `## Projects`), a small dedicated planner,
  and a new `bob areas list|sync` command pair mirroring `bob notebooks` /
  `bob albums`. Rows are link-only (`> - **[[stem]]**`), sorted A–Z, with no
  glyphs and no Closed group. Seven requirement adjustments below (A1–A7).

All vault observations were checked against the live vault on 2026-11-14; all
code claims cite the implementation body, not just grep output.

## 1. What exists today: the three generated catalogs

Bob already maintains three bob-owned callout catalogs through one shared
engine (`src/native/host_catalog/region.rs`, `src/native/host_catalog/mod.rs`).
Each catalog owns exactly its `> [!name]` callout block; the heading, the
block's position, and every other byte belong to Bryan. Understanding the
`## Projects` catalog in particular dictates the Areas design, because Areas
is meant to mirror it.

### 1.1 `## Projects` (the template)

- **Spec** (`src/native/host_catalog/region.rs:84-94`): callout `projects`,
  heading `Projects`, first-write placement `BeforeFirstH2` (before the first
  real `##` heading after frontmatter, else EOF), `strict_bare: true`
  (a malformed `> [!projects` opener is damage, never silently duplicated).
- **Planner** (`src/native/projects/catalog.rs:156-244`): pure function of
  scanned note bytes + vault `NoteIndex` + today. Hosts are area or project
  notes outside excluded dirs and `done/`; children are project notes whose
  scalar `parent:` wikilink resolves by exact path, then unique basename
  (`resolve_project_parent` in `src/native/project_dependencies/tree.rs:28-36`;
  alias and `#heading` are stripped first, so
  `parent: "[[love.md|love]]"` — the spelling `family.md` and `vacation.md`
  actually use — resolves fine).
- **Row grammar** (`src/native/projects/catalog_rows.rs:13-44,112-142`):
  `> - [glyph ]**[[link]]**[ — criterion]`, closed rows indented under
  `> - **Closed**`. The glyph is row state (none = open ready, 🗓️ scheduled,
  ⛓️ blocked, ⚠️ unreadable lifecycle, ✅ done, ❌ canceled); readers key on
  the glyph, never group membership. Ambiguous stems link as
  `path-without-md|stem`. The criterion is the cleaned `^prj` description;
  the tail is omitted when empty, placeholder, or equal to the stem.
- **Order** (`catalog.rs:252-258` plus `sort_rows`): open rows A–Z by filename
  without `.md`, case-insensitive, path tie-break; then `**Closed**` newest
  first by closure date, undated last. Closed history is derived — every
  closed direct child appears, and a hand-deleted closed row returns.
- **Ownership/damage:** a damaged host keeps its text untouched and is never
  rewritten; legacy `🧩 **Sub-projects:**` marker lines retire into the
  catalog in the same postimage. Missing/stale hosts warn; damaged hosts
  error and exit 1. Warning children count as open so an otherwise empty
  parent keeps its `^prj` hidden.
- **Blast radius (this is what makes Projects complicated):** the catalog feeds
  `project_surface` (`src/native/projects/surface.rs`), i.e. SUBOPEN drives
  `^prj` `#hide` surfacing, close-gesture pull-in, and the blocking cascade.
  The catalog is load-bearing task state, not just navigation.
- **Commands:** `bob projects list` (read-only + health footer) and
  `bob projects sync` (lifecycle + catalog in one guarded transaction, one
  scoped commit). JSON envelopes are versioned (`schema_version: 1`).
- **Capture protection** (`src/native/capture/sections.rs:585-607`):
  `@body#projects` refuses with `projects_section_generated`; generated
  headings are also excluded from bullet-section targeting
  (`is_generated_catalog_heading`, driven by `GENERATED_CATALOGS`).

### 1.2 `## Notebooks` and `## Albums` (the precedents that matter more)

Areas resembles these two more than Projects, because neither affects task
state — both are pure navigation, which is all Areas needs to be.

- **Notebooks** (`docs/notebooks.md:204-267`): scope is the host's *subtree*
  down to the next root (with `🧩 [[project]]` group lines for sub-project
  notebooks) — complex, because notebooks nest under notebooks. Rows are
  `**[[stem|Title]]** — summary`, inert-escaped. Placement: before the first
  real `## Tasks`, else EOF. Own commands (`list|check|sync|create` in
  `src/native/notebooks/cli.rs`), own damage code
  (`notebook_catalog_damaged`, legacy-marker only).
- **Albums** (`docs/records.md`, `src/native/albums/catalog.rs`): owner
  catalogs list direct albums first, then descendant owners as
  `> - 🧩 [[project]]` groups. Rows carry emoji + summary from frontmatter
  (`> - 🍽️ **[[eat|Restaurants]]** — …`). Placement: end of the existing
  `## Notebooks` section, else before first real `## Tasks`, else EOF.
  Own `list|check|sync` commands.
- **Observed section order in real notes** (`dev.md`, `body.md`, `job.md`,
  `gtd.md`): `## Projects`, then `## Notebooks`, then `## Albums`, then
  `## Tasks`. Love/cash/inbox notes without projects go straight to
  `## Notebooks`. Any Areas placement must compose with this order and never
  reshuffle it on later writes (the engine already guarantees: later edits
  patch only the callout lines wherever the block was moved).

### 1.3 The vault's actual area tree (19 area notes)

- **Top-level** (`parent: "[[area]]"` → `area.md`): `body`, `cash`, `dev`,
  `gtd`, `job`, `love`, `meet`.
- **Second level:** `love` → `abby`, `family`, `fun`, `kelly`, `vacation`;
  `cash` → `bank`, `recur`; `gtd` → `gtd_daily`, `inbox`;
  `inbox` → `gkeep_inbox`, `gmail_inbox`, `mac_inbox`. No area is currently
  parented under a project, notebook, album, or ref — the stated invariant
  ("areas only under areas or `area.md`") holds in practice today, but
  nothing in code enforces it (there is a `notebook_child_kind` finding for
  areas misparented under notebooks in
  `src/native/notebooks/scan.rs:341`; there is no general area-parent check).

## 2. Critique: is this a good idea?

**Yes — with the adjustments in §3.** The case for:

1. **Real discoverability gap, not hypothetical.** Four notes (`love`, `cash`,
   `gtd`, `inbox`) have child areas with zero navigational affordance. Bryan
   already felt this gap for projects (hence the generated catalog); areas are
   longer-lived than projects, so the gap compounds over time.
2. **Consistency.** Three of the four child-note kinds (projects, notebooks,
   albums) already get generated catalogs. Areas are the odd one out, and the
   omission is visible exactly where the tree is deepest (`love`).
3. **Smallest blast radius of any catalog.** Projects rows carry lifecycle
   (SUBOPEN → `#hide` surfacing → blocking cascade). Notebook rows carry
   subtree scope with root-stopping rules. Areas rows need neither: areas are
   always open (no `^prj`, no done/canceled lifecycle per the glossary
   `area-note` strand), so the catalog is pure navigation. Nothing in
   `surface.rs`, the sync surfacing rules, reconcile, freshness, Ready caps,
   root-parent walks, or off-clock defaults needs to change — all of those
   derive from the note tree, not from catalogs.

The case against, and why it does not win:

- **A fourth sync command is ongoing cost** (docs, tests, nightly flow,
  staleness warnings). Mitigation: the planner is ~150 lines reusing
  `host_catalog::plan_host`, and staleness is rare — areas are created and
  reparented by hand, far less often than projects/notebooks. This is
  genuinely the cheapest of the four catalogs to own.
- **Could a Dataview query do it instead?** No. All three existing catalogs
  are generated bytes (versioned in git, readable without plugins, audited).
  A Dataview island would be inconsistent, plugin-dependent, and invisible to
  `bob`'s health reporting. Follow the generated-catalog pattern.
- **Could Areas rows fold into `## Projects`?** No. The Projects catalog has
  lifecycle semantics (glyphs, Closed group, SUBOPEN counts, `#hide`
  surfacing). Mixing always-open areas into it would either pollute those
  counts or require carve-outs in `surface.rs` — complexity for zero benefit.
  The request's instinct for a separate section is correct.

## 3. Requirement adjustments (A1–A7)

These narrow or correct the brief. Each is justified; none changes the spirit.

- **A1 — Hosts are area notes (+ `area.md`), never projects.** The brief says
  "those are the only files" (parents + `area.md`), which is right, but it is
  worth stating the negative explicitly: a project note can never host
  `## Areas`, because an area can never be its child. The planner should
  enforce this (a child area resolving under a project/notebook/album/ref is
  an *orphan finding*, listed nowhere — mirroring `notebook_child_kind`).
- **A2 — `area.md` needs an explicit special-case.** It is not an area note
  (no `type:` frontmatter; it is the type definition), so a "hosts are area
  notes" rule would leave the seven top-level areas homeless. Recommend: the
  host rule is "area notes, plus the vault-root `area.md` by exact stem",
  documented in the contract. Do not generalize to "any note with area
  children" — that would invite catalogs on type notes generally.
- **A3 — Rows are link-only in v1; no tail, no glyphs, no Closed group.**
  There is no per-area description source: no `^prj` criterion, no `summary:`
  frontmatter, and body prose shapes vary too much to parse (Related lines,
  jokes, legacy pointers). Deriving a tail from the first paragraph would be
  the single most fragile part of the feature. Recommend
  `> - **[[abby]]**` rows (with the existing `path|stem` disambiguation when
  two areas share a stem), sorted A–Z case-insensitive with path tie-break —
  the Projects open-row order minus everything lifecycle-related. Optional
  `summary:` frontmatter support (rendered `— summary`, inert-escaped like
  notebook rows) is a clean v2 if Bryan finds link-only rows too bare; do
  not invent the frontmatter convention in v1.
- **A4 — New `bob areas list|sync`, not folded into `bob projects sync`.**
  One sync per catalog is the established ownership rule (notebooks, albums,
  projects each own theirs), and `cli_rules.md` asks for nouns with stated
  membership rules — "direct child areas" qualifies. Folding Areas into
  `projects sync` would couple an isolated navigational catalog to the
  lifecycle transaction for no reason. Mirror the notebooks/albums CLI shape
  (`list` read-only + health, `sync` with `--dry-run`/`-f json`,
  `schema_version: 1` envelopes); a `check`-style read-only mode falls out of
  `list` the way it does for projects.
- **A5 — Placement: `## Areas` before `## Projects`.** First-write placement
  `BeforeFirstH2` (same spec value as `PROJECTS`), so on a note that already
  has `## Projects` the new block lands above it, yielding the hierarchy
  order Areas → Projects → Notebooks → Albums → Tasks and matching the
  existing dev/body/job ordering with Areas prepended. Later writes patch
  only the callout, wherever Bryan moves it. Both specs sharing one
  placement value is safe: each sync installs only its own callout, and when
  both are first-written together the Areas write must be sequenced first
  (define this in the sync, with a test).
- **A6 — Membership is direct children only, no rollup.** Same as Projects
  (contrast Notebooks' subtree scope with root-stopping). `root: true`
  projects still list as projection children; analogously nothing about an
  area child excludes it — every direct area child lists. Depth beyond one
  level is reached by walking down (love → abby, not love → abby's children).
- **A7 — Full generated-section citizenship.** Add `AREAS` to
  `GENERATED_CATALOGS` (auto-protects the heading from bullet targeting),
  refuse `@area#areas` selectors with a new `areas_section_generated` code
  (same table as the three existing codes in `capture/sections.rs:585-607`),
  and give the spec `strict_bare: true` like Projects/Albums.

## 4. Recommended solution (v1 spec)

**Region spec** (in `src/native/host_catalog/region.rs`, next to `PROJECTS`):

```rust
pub(crate) const AREAS: RegionSpec<'static> = RegionSpec {
    callout: "areas",
    heading: "Areas",
    head_title: None,
    placement: Placement::BeforeFirstH2,
    legacy: None,          // no legacy marker to migrate, unlike notebooks
    strict_bare: true,
};
```

**Planner** (new small module, e.g. `src/native/areas/catalog.rs`,
reusing `host_catalog::plan_host`, `canonical_callout`, `FileEdit`,
`frontmatter_is_area`, `wikilink_path_target`, and `NoteIndex.resolve`
with the exact-path-then-unique-basename rule):

- Hosts: notes with `frontmatter_is_area` outside excluded dirs and `done/`,
  plus vault-root `area.md` by stem even though it has no area frontmatter;
  a host enters the plan iff it has ≥1 direct area child or already carries
  an `[!areas]` region (so removal/repair flows work).
- Children: notes with `frontmatter_is_area` (same exclusions) whose scalar
  `parent:` resolves to a host. Self-parents, list-form parents, ambiguous
  and unresolvable parents produce no row; non-area/non-`area.md` resolutions
  produce an orphan finding (new code, e.g. `area_parent_kind`).
- Rows: `{ path, stem, link }` with Projects' disambiguation (bare stem when
  unique, else `path-without-md|stem`). No state, no criterion, no dates.
  Sort A–Z by filename-without-`.md`, case-insensitive, path tie-break.
- Render: `## Areas` + blank + `> [!areas]` + `>` + one `> - **[[link]]**`
  per row. Empty row-set with an existing region deletes the callout and
  removes the heading only when its section is then blank (same rule as
  Notebooks/Albums). Duplicate regions self-heal (keep first); malformed
  openers are `areas_catalog_damaged` and are never rewritten.
- States `missing|stale|current|damaged` and the `*_catalog_stale` /
  `*_catalog_damaged` finding shape mirror the other three catalogs.

**Commands** `bob areas list|sync` (new `src/native/areas/` module following
`src/native/albums/cli.rs` structure): `list` prints the human table plus
one repair footer and `-f json` envelope; `sync` takes the shared vault
lock, pre-syncs, installs one combined postimage per changed note, and makes
one scoped commit (`areas: sync catalogs (N notes)`). Exit codes match
projects (missing/stale warn, damaged/errors exit 1). Capture never creates
area notes, so no capture-transaction work is needed beyond the A7
selector protection.

**Docs & records:** extend `docs/projects.md`'s catalog section or add a
short `docs/areas.md` (plus one row in the vault-format contract, the
capture protection list, and a notebooks cross-ref), run `just docs-check` /
`just docs-gen` per `docs.md`; file an architecture decision record under
`decisions:` (the descriptor demands one for new behavior, and it should cite
this report); add the nightly/vault-sync flow step wherever `notebooks sync` /
`projects sync` are invoked so Areas cannot drift silently.

**Tests:** unit vectors for row parse/render (new
`tests/fixtures/area_catalog/vectors.json` mirroring the project-catalog
vectors), planner tests (alias-form parent `[[love.md|love]]`, ambiguous
stems, orphan-under-project finding, empty-subtree heading removal,
duplicate self-heal, BOM/CRLF preservation), and one temp-vault sync e2e
covering `love.md` gaining `## Areas` above `## Notebooks` and `area.md`
listing the seven top-level areas.

**Expected footprint in the real vault:** five hosts gain or maintain the
section — `area.md` (7 rows), `love.md` (5 rows: abby, family, fun, kelly,
vacation), `cash.md` (bank, recur), `gtd.md` (gtd_daily, inbox), `inbox.md`
(gkeep_inbox, gmail_inbox, mac_inbox). No other note changes. No dashboard,
walk, freshness, reconcile, Stats, or plugin-query changes are needed; the
Obsidian side needs only whatever card rendering Bryan wants (follow-up, not
v1 — Bob Mac Capture is unaffected since it never parses catalogs).

## 5. Risks and open questions

1. **`area.md` becomes a catalog host while remaining the type note.**
   Acceptable but slightly odd; the contract must say bob owns only the
   callout. If Bryan ever splits "type definition" from "area index", the
   host exception moves with the index page (one-line change).
2. **Link-only rows may feel bare** on `area.md` (seven bare links). If so,
   do the v2 `summary:` frontmatter — do not auto-derive prose tails.
3. **Orphan areas have no precedent to copy wording from**; keep the finding
   advisory (exit 0 on `list`, nonzero on `sync` only if something is
   unwritable — mirror how projects treats scan issues).
4. **Plugin rendering** (Obsidian Area cards, dataview snippets that
   enumerate areas) is out of v1 scope but should be checked after landing so
   no plugin duplicates the new section by hand.

## 6. Evidence inventory

- `src/native/host_catalog/region.rs:46-99` — `RegionSpec`, `NOTEBOOKS`,
  `ALBUMS`, `PROJECTS`, `GENERATED_CATALOGS`.
- `src/native/host_catalog/mod.rs:1-36` — shared engine + `txn` guarded
  install; `capture_drawers.rs:550`, `capture/sections.rs:567` consume
  `GENERATED_CATALOGS`.
- `src/native/projects/catalog.rs:156-260,848-868` — host planning,
  `plan_host_catalog`, `render_callout` byte shape.
- `src/native/projects/catalog_rows.rs:13-142` — row grammar, glyph states,
  `parse_catalog`/`parse_row`.
- `src/native/projects/surface.rs:1-60` — why Projects rows are load-bearing
  (SUBOPEN) and Areas rows will not be.
- `src/native/projects/scan.rs:357`, `project_dependencies/tree.rs:28-36` —
  `frontmatter_is_area`, parent resolution with alias/heading stripping.
- `src/native/capture/sections.rs:554-624` — generated-heading protection +
  the three `*_section_generated` codes to extend.
- `src/native/notebooks/cli.rs:29-121`, `src/native/albums/cli.rs:94-213` —
  CLI shape to mirror for `bob areas`.
- `docs/projects.md:282-330`, `docs/notebooks.md:204-267`, `docs/records.md`
  (Owner catalogs), `docs/reference/vault-format.md:369-376` — contracts to
  extend; `sase/memory/cli_rules.md`, `sase/memory/docs.md` — gates observed.
- Vault (2026-11-14): `area.md` (type note, no `type:`); top-level areas
  `body/cash/dev/gtd/job/love/meet`; `love.md` (5 child areas, no catalog);
  `cash.md`, `gtd.md`, `inbox.md` (ditto); `dev.md:20-26` (Projects-then-
  Notebooks-then-Albums order); `family.md`/`vacation.md` alias-form parents.

- **`area.md` is not an area note.** It has no `type:` frontmatter at all —
  it is the *type definition* note ("Area notes link to this note as their
  `type`"). Top-level areas resolve their `parent: "[[area]]"` to it, but
  under today's host rules it could never host a catalog.
- **Area frontmatter carries no description field.** Area notes have `parent`,
  `type`, `color`, `task_type`, `offclock*`, `done_tasks`, `ready_cap` — but
  no `summary:` (unlike notebooks/albums) and no `^prj` criterion task
  (unlike projects). The only "description" is free body prose, whose shape
  varies per note (`dev.md` uses a `Related:` line; `cash.md` a joke sentence;
  `abby.md` a pointer to legacy notes).
- **Mixed children are the norm.** A `parent: "[[dev]]"` child can be a
  project (`bob`, `sase`), notebook (`ai`, `vim`, …), album (`podcasts`), or
  ref (`dev_ref`). Any Areas planner must filter by `type: "[[area]]"`
  (via the existing `frontmatter_is_area` in
  `src/native/projects/scan.rs:357`), exactly as the Projects planner filters
  by `frontmatter_is_project`.
