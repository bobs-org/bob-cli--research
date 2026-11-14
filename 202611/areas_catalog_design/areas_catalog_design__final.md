# A generated `## Areas` catalog: consolidated design

- **Date:** 2026-11-14 · **Lead:** consolidation of five independent reports
  (`__cdx`, `__cld`, `__grk`, `__mus`, `__gem` in this directory) plus lead verification
  against bob-cli `master` (`9574e618`), the audited glossary, and the prior
  sub-projects catalog research.
- **Question:** Bob already renders a generated H2 `## Projects` catalog in area/project
  notes that parent project notes. Should it render a sibling `## Areas` section for
  child area notes — hosted only on area notes and `~/bob/area.md` — and how should that
  section be designed so it is intuitive, reliable, and beautiful?
- **Verdict:** **Build it. All five researchers independently said yes**, and the
  consolidated design below is cheaper and safer than any existing catalog because area
  rows carry no lifecycle and feed no task state. The one real design fork — flat direct
  children versus a nested descendant forest — is resolved in favor of **nesting**, for
  reasons laid out in §3.1.

## 1. Decision in brief

Add a fourth member to the shared host-catalog family: a bob-owned `> [!areas]` callout
under an authored `## Areas` heading, written by a new `bob areas list | check | sync`
command and a nightly step. Hosts are area notes with child areas plus the root note
that `[[area]]` resolves to (today `area.md`). Each host lists its **descendant area
forest, nested**, as `> - **[[stem]]**[ — summary]` rows — no lifecycle glyphs, no
Closed group, no counts in Markdown. `## Areas` sits **above** `## Projects`, enforced
by a one-variant placement change to the Projects spec so the order cannot invert.
All visual polish (hue dots, `● today`, project counts, fold toggles, health chrome)
lives in a bob-ledger-tools card that never writes the vault.

What makes this worth doing (unanimous across reports):

1. **A real, compounding gap.** Children point up through `parent:`; nothing points
   down. `area.md` is a dead end that names one area in prose. `love.md` has five child
   areas and renders none of them. `cash.md`'s hand-written `Related:` line is already
   stale (`[[old_recur]]` instead of `[[recur]]`), and `inbox.md` lists its trays in
   prose that will drift. Backlinks bury child areas under hundreds of task links.
2. **The engine already exists.** Notebooks, Albums, and Projects share
   `src/native/host_catalog` (`RegionSpec`, byte-span owned regions, damage handling,
   guarded transactions, nightly, capture protection, plugin card family). Areas is one
   more `RegionSpec`, a small pure planner, and one CLI noun.
3. **It turns a convention into a checked invariant.** "Areas can only be children of
   areas or `area.md`" is enforced nowhere today; a typo'd `parent:` fails silently even
   though inbox-file classification and root-parent walks depend on it. Rendering the
   catalog requires resolving and validating every area parent for the first time.
4. **Smallest blast radius of any catalog.** Projects rows are load-bearing (SUBOPEN →
   `#hide` surfacing → blocking cascade). Areas never close (glossary *Area Note*: no
   `^prj`, no done/canceled lifecycle), so this catalog is pure navigation: nothing in
   surface, reconcile, freshness, Ready caps, or home walks changes.

## 2. The ground truth (verified)

### 2.1 The live vault (cld/grk/gem/mus audits, consistent with each other)

19 area notes, all at the vault root, max depth 3, every parent valid today:

```text
area.md          root type note (parent: [[type]], NO type: field) — hosts Areas
├── body         color: green
├── cash         color: magenta        — hosts Areas
│   ├── bank     H1 "🏦 Bank"
│   └── recur
├── dev          color: blue
├── gtd          color: grey           — hosts Areas
│   ├── gtd_daily
│   └── inbox    H1 "Inbox"            — hosts Areas
│       ├── gkeep_inbox
│       ├── gmail_inbox  H1 "Gmail inbox"
│       └── mac_inbox    H1 "Mac Inbox"
├── job          color: aqua
├── love         color: yellow         — hosts Areas
│   ├── abby
│   ├── family   parent: "[[love.md|love]]"
│   ├── fun
│   ├── kelly
│   └── vacation parent: "[[love.md|love]]"
└── meet         color: violet
```

Five hosts gain a section; fifteen leaves are untouched. **0/19 areas have `summary:`**;
4/19 have an H1 title. Areas change rarely (newest: `bank` 2026-11-11, `family`
2026-11-02). Aliased parents (`[[love.md|love]]`) already resolve through the shared
resolver. Mixed children are the norm under areas (`dev` parents projects, notebooks,
albums, and a ref), so membership must filter by `frontmatter_is_area`.

### 2.2 The code (lead-verified at `9574e618`)

- `src/native/host_catalog/region.rs` — `RegionSpec` with `NOTEBOOKS`
  (`BeforeFirstTasks`, legacy markers), `ALBUMS` (`AfterSectionThenTasks("Notebooks")`,
  strict), `PROJECTS` (`BeforeFirstH2`, strict); `GENERATED_CATALOGS = &[NOTEBOOKS,
  ALBUMS, PROJECTS]`. The engine preserves BOM/CRLF, skips frontmatter and fences,
  self-heals duplicate well-formed regions, treats malformed strict openers as damage,
  and drops an emptied heading only when its section is then blank.
- `src/native/projects/catalog.rs` — pure planner; membership from scalar `parent:`
  through `NoteIndex` (exact path, then unique case-insensitive basename, alias/heading
  forms stripped). `src/native/notebooks/catalog.rs::push_forest` — the nested-forest
  renderer Areas can reuse. `src/native/notebooks/scan.rs::derive_title` — H1 → first
  alias → humanized stem.
- `src/native/capture/sections.rs::reject_generated_catalog_selector` — a **hardcoded**
  three-entry table (`notebooks_section_generated`, `albums_section_generated`,
  `projects_section_generated`) that must gain an `areas` row; the drawer and merge
  guards follow `GENERATED_CATALOGS` automatically.
- `src/native/nightly.rs` — steps: vault-sync, task archive, articles, period notes,
  **projects, notebooks, albums**, vault-sync.
- **Snapshot hazard (cdx, lead-verified):** `src/native/notebooks/snapshot.rs` retains
  note bodies only for `LiteKind::{Notebook, Album, Area, Project}`. The real `area.md`
  is untyped (`parent: "[[type]]"`, no `type:`), so a reused snapshot would have
  `contents: None` for the one host the request names. Retention must be extended for
  the resolved root (and for ineligible notes carrying a leftover `[!areas]` region, so
  cleanup can run).
- `walk_typed_notes` skips notes that are neither area nor project, so no existing
  pipeline ever sees the real `area.md` (gem). Many tests write a synthetic `area.md`
  *with* `type: [[area]]`; the host rule below handles both spellings.

### 2.3 Precedent inside the catalog family

The prior sub-projects research (`202611/subprojects_catalog_section/`) decided **D7**
for Projects — *direct children only; a grandchild change must rewrite one parent, not
every ancestor* — and **D8** — *catalogs read goal → parts → knowledge → work*. D7 is
research precedent for the **lifecycle** catalog, not an accepted decision record. The
two **navigation** catalogs already go the other way: Notebooks renders a nested forest
down to the next root parent, and each area/project lists its **descendant** albums
(glossary *Area Note*). So the family's real rule is: lifecycle catalogs stay flat,
navigation catalogs show the subtree.

## 3. Resolved disagreements (the lead calls)

### 3.1 Nested descendant forest, not direct children only — **nested** (grk, gem over cdx, cld, mus)

The one substantive fork. The direct-only camp (cdx, cld, mus) argued D7's write-locality
rule, the clean "every area appears in exactly one catalog" invariant, and exact reuse of
the Projects row parser; depth would live in plugin `▸ N` expanders. The nested camp
(grk, gem) argued the tree is tiny and stable, and that flat rows gut the feature where
it matters most.

**Resolution: nested, by the navigation-catalog precedent and by where the value is.**

- The whole justification for stored bytes over a Dataview/Bases query — unanimous in
  all five reports — is the readers Obsidian plugins can't reach: git diffs, agents,
  grep, mobile, and Highlights PDFs. Direct-only gives those readers one level;
  `area.md` would show seven names and still hide where `bank`, `inbox`, or `abby`
  live. The 19-line atlas on `area.md` is the headline "beautiful" outcome in raw
  Markdown, and plugin expanders cannot substitute for it off-desktop.
- D7's rationale is scale (projects number in the dozens per host, with closed
  archives); it does not transfer to 19 permanent notes, depth 3, and near-zero churn.
  Nesting here *follows* the family rule (Notebooks/Albums nest or roll up; Projects
  stays flat) rather than overriding D7.
- The write-amplification cost is real but bounded and honest: adding or reparenting a
  leaf rewrites its ancestor chain (≤ 3 notes today) in one commit, a few times a
  month at most. Among the four area hosts, nested differs from direct-only on exactly
  one note (`gtd.md`, 2 → 5 rows); the decision is effectively about `area.md`.
- Duplication across hosts is the point of a local map: `mac_inbox` belongs on
  `inbox.md`, nested on `gtd.md`, and nested on `area.md`. Each note answers "what
  hangs from here?"

**Documented fallback:** if the tree ever grows past a few dozen areas or meaningfully
deeper, switch to direct-only (a contract change worth its own decision record). This
choice — nesting for a navigation catalog, diverging from Projects — is exactly the
kind of trade-off that should be captured as a decision record when accepted.

### 3.2 Root host identity — **resolve `[[area]]`, don't hard-code the filename** (cld, grk over cdx, mus, gem)

The live `area.md` is the type-definition note: `parent: "[[type]]"`, **no `type:`
field**, so a naive `frontmatter_is_area` host predicate would skip the one note the
request names. Rule: a host is (a) an area note (`frontmatter_is_area`) with at least
one eligible descendant or an existing `[!areas]` region, or (b) **the note the bare
`[[area]]` wikilink resolves to through `NoteIndex`** (today `area.md`), outside `done/`
and excluded directories, with no frontmatter requirement. Resolution beats an exact
filename because a rename of the type note moves every `type: "[[area]]"` field with it;
it also transparently covers test fixtures that write `area.md` *with* area frontmatter.
The root is never a child row and is a terminal sentinel: its own `parent:` is never
followed. If nothing resolves, report `areas_root_missing` and host nothing — never
manufacture the file. Keep the root out of `walk_typed_notes`, capture targets, and
Pomodoro-home resolution (it is a catalog container, not a routable home), and do **not**
generalize to "type notes list their instances" (`project.md` would list ~100 projects).
`type.md` keeps its Bases embeds; it gets no catalog.

### 3.3 Invalid parents — **findings, not rows** (cdx, grk, mus over cld)

cld proposed routing every orphan (missing/unresolved/ambiguous/list-form/self/cyclic/
wrong-kind parent) into `area.md` as a `⚠️ **[[stem]]** — reason` row so the root map
stays complete. It is a thoughtful option, but it writes bob-authored prose into stored
rows, depends on direct-only's "exactly one catalog" bookkeeping (which nesting retires),
and has no precedent in the other navigation catalogs. **v1: no row anywhere + a typed
finding** (`area_parent_missing | _unresolved | _ambiguous | _list | _self`,
`area_cycle`, `area_parent_kind`), surfaced by `bob areas list`/`check`, nightly output,
and the card's health line. Wrong parents are check findings, never catalogs on project
or notebook notes. The vault has zero violations today, so findings-only is
proportionate; cld's ⚠️-row alternative stays on the table if silent findings prove too
quiet (open question 2).

### 3.4 Row links — **bare stems; titles live in the card** (cdx, cld, mus, gem over grk)

grk proposed Notebooks-style title aliasing (`[[bank|🏦 Bank]]` from H1/alias/stem).
Rejected for v1: bare `**[[stem]]**` matches the Projects grammar (so row parsing
reuses), matches Bryan's capture vocabulary (`@bank`, `@mac_inbox`), and — decisively —
avoids a new churn source where editing a child's H1 rewrites every ancestor catalog
(amplified by nesting). The JSON report carries `title` (H1 → first alias → humanized
stem, via `derive_title`) so the card and tooltips can show `🏦 Bank` without storing
it. Ambiguous stems disambiguate as `path-without-md|stem`, exactly like Projects.

### 3.5 Everything else (near-unanimous)

- **Placement:** `AREAS` gets `Placement::BeforeFirstH2`; `PROJECTS` changes to a new
  `Placement::AfterSectionThenFirstH2("Areas")` (after an existing `## Areas` section,
  else the current before-first-H2, modeled on `AfterSectionThenTasks`). All five flagged
  the same bug: two `BeforeFirstH2` specs make section order depend on creation history —
  a host that gains its first project after its first sub-area would hoist `## Projects`
  above `## Areas`. The fix is a placement rule, never nightly step order. First-write
  outline: **Areas → Projects → Notebooks → Albums → Tasks** (extends D8: spheres →
  outcomes → knowledge → records → work). After first write the position is Bryan's.
  If a single authored `## Areas` heading already exists, install the callout into it
  without duplicating the heading (engine behavior; test it).
- **Summaries:** recognize an optional one-line `summary:` on area notes in v1
  (rendered ` — summary`, inert-escaped via the existing notebooks helper). Absence is
  **never** a finding (0/19 today; 19 day-one warnings would be noise); never scrape
  body prose ("Money Money Mooooney!" is not a catalog line). Soft findings
  `area_summary_long` (>140 chars) / `area_summary_multiline`. The cld report carries a
  ready-to-edit draft summary table for all 19 areas.
- **CLI:** new noun `bob areas`, Vault section of `bob --help`, never folded into
  `bob projects sync` (areas have no lifecycle; `cli_rules.md` nests only under a noun
  with a stated membership rule). Shape per the family:
  `bob areas [list] [-b DIR] [-f human|json]` (bare = read-only list, colored tree with
  hue dots and a repair footer), `bob areas check`, `bob areas sync [-d]`. JSON is a
  versioned `schema_version: 1` envelope with `root`, `areas[]` (path, stem, title,
  summary, parent, depth, hue/hue_source, children, issues, direct/subtree rollups),
  `catalogs[]` (`current | missing | stale | damaged`), `findings[]`, `counts`.
  Missing/stale warn (exit 0); damaged errors (exit 1). Sync: shared vault lock,
  pre-sync, plan from one snapshot, preimage-guarded install through
  `host_catalog::txn`, one scoped commit `areas: sync catalogs (N notes)`, post-sync;
  dry-run writes nothing; no-op commits nothing; damaged hosts are skipped while healthy
  hosts apply. Guard read dependencies too (parent/type/summary facts *and* the
  note-path namespace — a new same-stem file can flip ambiguity, per cdx).
- **Nightly:** an `areas` step immediately **before** `projects`, matching on-page
  order (cld, gem; grk's after-projects works too once the placement fix lands, but
  before-projects reads better and is self-consistent on first paint). Update
  `docs/vault-git-sync.md` and the nightly help.
- **Capture & structure protection:** add `AREAS` to `GENERATED_CATALOGS` (drawer and
  merge guards follow automatically) **and** add the `areas_section_generated` row to
  the hardcoded selector-refusal table in the same commit as the writer, so
  `@love#areas` refuses instead of writing into the callout.
- **Highlights:** project `[!areas]` as `kind="areas"` beside `kind="projects"` so PDF
  note snapshots keep the rows instead of a generic callout.
- **No creation surface in v1:** no `bob areas create`, no capture sigil, no `＋ area`
  card button (it would be a false promise — bob has no area-creation flow). Hand-made
  areas converge at the next nightly or on-demand sync; if capture ever grows an
  area-create form it should update ancestor catalogs in the same transaction, as
  `@route^id@` already does for `## Projects`.
- **Rejected approaches (unanimous):** Dataview/Bases as the writer (invisible to git,
  agents, mobile, PDFs; another parent-semantics implementation), plugin-only overlay
  (dies with the plugin, breaks the bytes contract), folding areas into `## Projects`
  (lifecycle glyphs/Closed/SUBOPEN would be meaningless or wrong — PARA's whole test is
  the project/area split), a stored Mermaid graph (brittle, no real links), and a
  cloned Closed-group/glyph grammar (areas never close; a status ring would paint every
  area "open ready" forever).

## 4. Recommended contract

### 4.1 Region

```rust
pub(crate) const AREAS: RegionSpec<'static> = RegionSpec {
    callout: "areas",
    heading: "Areas",
    head_title: None,
    placement: Placement::BeforeFirstH2,
    legacy: None,          // nothing to migrate
    strict_bare: true,     // malformed `> [!areas` opener = damage, host untouched
};
// GENERATED_CATALOGS = &[AREAS, NOTEBOOKS, ALBUMS, PROJECTS];
// PROJECTS.placement = Placement::AfterSectionThenFirstH2("Areas");
```

Bob owns exactly the `> [!areas]` callout bytes. Bryan owns `## Areas` and its position
after the first write, and every other byte. Duplicate well-formed regions self-heal
(keep first). An empty host loses the callout; the heading goes only when its section is
then blank. A leftover `[!areas]` on any ineligible, non-excluded note (retyped area,
project, newly leaf host) is stale and is removed — cleanup, not permission to catalog
project notes.

### 4.2 Membership and rows

- **Children:** notes with `frontmatter_is_area`, outside `done/` and excluded
  directories, whose scalar `parent:` resolves (exact path → unique case-insensitive
  basename; alias and heading forms stripped) to an eligible host or to another area in
  the host's subtree. List-form, duplicate-key, missing, ambiguous, self, cyclic, and
  wrong-kind parents produce no row and a finding; cycles are detected on the resolved
  graph with the existing walk-depth cap, and a bad ancestor never suppresses valid
  edges beneath it.
- **Rows:** `> {indent}- **[[stem]]**[ — summary]`, two spaces per depth, nested by
  resolved parent (reuse the `push_forest` pattern). Each sibling level sorts A–Z by
  stem, case-insensitive, path tie-break. No glyphs, no Closed group, no counts, no
  dates, no emoji, no hue names.

### 4.3 First-sync preview on today's vault

`area.md` (no H2 today, so heading + callout land at EOF after the type prose):

```markdown
## Areas

> [!areas]
>
> - **[[body]]**
> - **[[cash]]**
>   - **[[bank]]**
>   - **[[recur]]**
> - **[[dev]]**
> - **[[gtd]]**
>   - **[[gtd_daily]]**
>   - **[[inbox]]**
>     - **[[gkeep_inbox]]**
>     - **[[gmail_inbox]]**
>     - **[[mac_inbox]]**
> - **[[job]]**
> - **[[love]]**
>   - **[[abby]]**
>   - **[[family]]**
>   - **[[fun]]**
>   - **[[kelly]]**
>   - **[[vacation]]**
> - **[[meet]]**
```

`gtd.md`: `gtd_daily` + `inbox` with its three trays nested, inserted above the existing
`## Projects`. `love.md`: five flat children above `## Notebooks`. `cash.md`: `bank`,
`recur` (the stale authored `Related: [[old_recur]]` line stays until Bryan prunes it).
`inbox.md`: the three trays. Fifteen leaf notes unchanged. Once summaries exist, rows
grow ` — …` tails; until then the atlas is already more useful than today's nothing.

### 4.4 The Obsidian card (the beauty layer, shipped in the same wave)

A raw `[!areas]` callout looks like a generic note callout; grk is right that *a writer
without the card CSS is not "beautiful"* — ship the bob-ledger-tools card with (or
immediately after) the writer. It is display-only: it styles the stored rows, reads
`bob areas list -f json`, and never edits catalog text or re-resolves parents in JS.

- **Family chrome:** same card shell as `[!projects]`/`[!notebooks]` (hue wash,
  border, radius, container queries, nested-list rail). Icon `lucide-layers` (grk,
  gem; cld's `lucide-orbit` is the runner-up) — distinct from puzzle, notebook-tabs,
  and album.
- **The marker means something** (cld's best idea): Projects rows carry a **ring**
  because a project can finish; Areas rows carry a **solid dot** because an area never
  does. Each dot paints in that child's resolved hue through the shared home-color
  resolver — `area.md` keeps a neutral card whose rows carry a rainbow (green, magenta,
  blue, grey, aqua, yellow, violet); `love.md`'s children inherit a softer yellow tint.
- **Calm chips, at most a few per row, all drawn never stored:** `● today` when the
  branch has a live Task Link today (ledger-derived), a muted `N projects` count,
  `▸/▾` branch folds with per-pane memory. Task counts live in the dot's tooltip, not
  the row — this is a map, not a to-do list. gem's config pills (`PLAN`, `offclock`,
  `no cap`) are optional later polish.
- **Health chrome:** `stale catalog · ↻ sync` (runs `bob areas sync`), Retry on a
  failed report keeping last-good rows, damage explained with the offending line —
  never auto-writing a damaged host. A quiet **add summary** affordance on rows without
  one (Notebooks code path). No `＋ area` button.
- **Fallbacks:** on mobile or without bob, the callout is ordinary readable Markdown —
  no permanent failure banners, no phantom cards on non-host notes.

### 4.5 Docs, memory, and decision record

- New contract page `docs/areas.md` (hosts, membership, nesting, row grammar, order,
  placement, ownership, damage, states, CLI, JSON, nightly); `docs/reference/
  vault-format.md` § Area notes gains `summary:`, the catalog, and the root-note host
  rule; capture reference gains `areas_section_generated`; `docs/projects.md` notes the
  placement change; bob-plugins docs gain the card section; `just docs-gen` for the CLI
  reference. Mind the `docs.md` memory gate before touching docs.
- Glossary *Area Note* strand should mention the catalog (a memory change — route
  through the memory-write flow, not this research).
- **One decision record** when accepted, because §3.1 deliberately diverges from the
  Projects precedent: claim ≈ *"Area catalogs nest the descendant forest; lifecycle
  catalogs stay flat"*, covering the root-note host rule and counts-are-drawn; rejected
  alternatives: direct-only rows, Dataview/Bases, merging into Projects, ⚠️ orphan
  rows. Reopens if the tree outgrows a screen or areas gain a lifecycle.

## 5. Reliability checklist (what the tests must prove)

1. **Placement, both orders:** sub-area first then first project, and the reverse —
   `## Areas` ends above `## Projects` in both; manually moved catalogs stay put;
   authored intro/H1 stay above; an existing authored `## Areas` heading is reused, not
   duplicated.
2. **Root host:** real-shape fixture (`area.md` with `parent: [[type]]`, no `type:`)
   hosts; `type.md` does not; synthetic typed `area.md` fixtures keep passing; no root →
   `areas_root_missing`, healthy area hosts still sync; nested `dir/area.md` and a
   project named `area` stay distinct from the root.
3. **Snapshot retention:** untyped root body retained; ineligible notes with leftover
   `[!areas]` regions retained for cleanup; a partial scan refuses removals (unreadable
   children are never "deleted").
4. **Parents:** aliased (`[[love.md|love]]`), path, and heading forms resolve; missing/
   ambiguous/list/self/cycle/wrong-kind each yield the right finding and no row; a
   two-node cycle and the 16-hop depth cap; valid children below a broken ancestor
   still render.
5. **Ownership:** BOM/CRLF byte-identical outside the callout; fenced `[!areas]`
   examples ignored; duplicate regions self-heal; malformed opener → damaged, host
   untouched, exit 1, other hosts apply.
6. **Nesting & cleanup:** golden bytes for today's five hosts; reparent `kelly` →
   `family` updates every affected host in one commit; last child removed deletes the
   callout and drops the heading only when the section is blank; retyped area and
   project notes shed stray regions.
7. **Idempotence:** second sync is byte-identical, no commit; dry-run writes nothing.
8. **Protection:** `bob capture '@love#areas' …` refuses with
   `areas_section_generated`; drawer/merge loops extended to the fourth heading.
9. **Concurrency:** host edited after planning → refuse/replan; a new same-stem file
   flips ambiguity → read-dependency guard fires.
10. **Readers:** Highlights projects `kind="areas"`; summaries inert-escape `[[x]]`,
    `#tag`, `**`, newlines.

## 6. Rollout

1. **bob-cli (one PR):** `AREAS` spec + `AfterSectionThenFirstH2` + `PROJECTS`
   placement change; `src/native/areas/` planner (scan, catalog, sync, output) reusing
   `push_forest`, `derive_title`, `host_catalog::txn`; snapshot retention extension;
   `bob areas list|check|sync`; nightly step; capture refusal; Highlights projection;
   docs; the test matrix above. Additive CLI — rides the daily release train, no `!`.
2. **Vault:** run `bob areas sync -d`, eyeball the five diffs, sync. Optionally add
   `summary:` lines (cld's drafts) and prune the now-redundant prose in `inbox.md`,
   `cash.md`, and `area.md` (Bryan's call; bob never edits authored text).
3. **bob-plugins:** the `[!areas]` card (CSS + report service + Reading/Live Preview
   decorators), then `bob plugins sync`. A card without live chips is acceptable for
   the first paint; a writer with no CSS is not.
4. **Follow-ups:** decision record + glossary strand; optional capture-targets summary
   surfacing for Mac Capture route completions; optional config pills.

## 7. Open questions for Bryan

1. **Nesting (the one real fork):** the nested atlas (recommended, §3.1) trades
   bounded multi-host rewrites for a complete raw-Markdown map; direct-only (cdx/cld/
   mus) keeps D7's one-change-one-parent locality and leans on plugin expanders. If you
   value write-locality over the stored atlas, everything else here still stands.
2. **Orphan visibility:** findings-only (recommended) or cld's ⚠️ rows in the root
   catalog so modeling mistakes are impossible to miss?
3. **Summaries:** happy to adopt `summary:` on area notes? The cld report has drafts
   for all 19.
4. **Card icon & density:** `lucide-layers` vs `lucide-orbit`; project-count chip on
   rows or tooltip-only?

## 8. Source reports

| Suffix | Emphasis / unique contributions |
| --- | --- |
| `__cdx` | Restraint principles; snapshot-retention hazard; read-dependency and namespace-ambiguity guards; cleanup/cycle semantics; accessibility/reflow targets; don't reuse `HomeResolver`. |
| `__cld` | Live-vault audit; D7/D8 lineage; ⚠️ orphan-routing alternative; draft summaries for all 19 areas; dot-vs-ring card semantics; full JSON sketch; acceptance-test table. |
| `__grk` | Nested-forest case; resolve-`[[area]]` root rule; placement-inversion analysis; "writer without CSS is not beautiful"; title derivation; Highlights `kind="areas"`. |
| `__mus` | Code-level verification (specs, planner, row grammar, capture table); smallest-blast-radius argument; synthetic-fixture compatibility; link-only row discipline. |
| `__gem` | Per-note vault inventory (H1s, colors, config keys); union host predicate; subtree-vs-direct delta ("differs on one file"); card mockups, config pills, fingerprint watcher. |
