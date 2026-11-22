# Area and project property cards: consolidated research

> **Research question:** Once the `bob-cli-pf` epic bead is complete, start using
> property cards in area notes and project notes. What should the cards look like, and
> what fields should the corresponding schema editors (triggered via the `=+` keymap)
> support, so the feature is intuitive, reliable, and beautiful? Critique the plan,
> call out justified requirement adjustments, and recommend a solution.

*Lead consolidation of five independent reports —
[cdx](area_project_property_cards__cdx.md), [cld](area_project_property_cards__cld.md),
[grk](area_project_property_cards__grk.md), [mus](area_project_property_cards__mus.md),
[gem](area_project_property_cards__gem.md) — plus the lead's own verification against
bob-cli `e98c7fe9`, bob-plugins (master, 2026-11-22), the `bob-cli-pf` bead, and
`plan:202611/card_owned_frontmatter.md`. 2026-11-22.*

## Bottom line

**Yes — do it, as the first property-card epic after `bob-cli-pf` lands.** All five
researchers independently reached the same verdict: the 19 area notes and ~102 project
notes are the vault's work homes and configuration hubs, the last major typed note kinds
with no card, and the place where Bob's most consequential per-note settings (`color`,
`task_type`, `offclock`/`offclock_types`, `ready_cap`, `task_refresh`, `parent`, `root`,
`project_name_aliases`) are still hand-typed as raw YAML with silent failure modes. The
epic also closes `bob-cli-pf`'s one deliberate deferral: the bank_foot decision keeps a
duplicate drawer on `bank.md` by design "until areas get a title-block card."

The recommended shape, in one paragraph: **two new species (`area`, `project`) on the
existing title-block kit, painting compact five-line identity cards from local data; and
`=+` as the schema editor** — kind-aware typed stages, bob-owned validation, and ghost
rows showing inherited values and their sources — with `==` registered on these notes to
open that same editor on the settings group. One byte-preserving writer (`bob props
update`, extended with area/project domain validation). The `^prj` line is never hidden,
docked, or duplicated. Catalogs, `## Tasks`, and lane math stay in the body. Two
prerequisites land first: complete the `props` role table (project `status`,
`done_tasks`, `task_count`, `open_task_count` are all `loose` today) and retire the
`bob-project-tasks` `processFrontMatter` count writer, the one remaining re-serializing
second writer on exactly these notes.

Three framing corrections to the request, unanimous across reports:

1. **"Schema editor" names the job, not a new surface.** Areas and projects have no
   album-style nested `record:` map to own; their "schema" is a closed vocabulary of
   flat scalars and short lists that bob already parses, lints, and inherits. The right
   build is typed, validated, inheritance-aware stages *inside* the `=+` property
   editor, driven by a bob-owned field contract — not a per-note schema language, a
   field builder, or a second modal.
2. **A calm identity card, not a dashboard.** The body already renders the machine-owned
   `## Areas` / `## Projects` / `## Notebooks` / `## Albums` catalogs, the `## Tasks`
   status badges, and the walker footer. The card answers "what is this home, where does
   it sit, and which policies are in force" in about five lines, then gets out of the way.
3. **The `^prj` task line stays the project's control.** It is an active surface
   (close, Task Card, `]s` PROJECTS landings, Depends-On and requirements editing).
   The card projects its lifecycle; it never hides, moves, or re-renders the line.

## 1. Is this a good idea? Critique

**What it buys** (consensus, verified):

- **The only validated, inheritance-aware editor for Bob's per-note settings.** Native
  Properties cannot validate (`color: purple` silently falls back and lints only in the
  CLI), cannot show precedence ("off-clock for MEET, from `love`"), and parks
  bookkeeping keys (`task_count`, `template`, `done_tasks`) in the most valuable spot on
  the page. These settings change clock accounting, hue on every surface, Ready-lane
  pressure, review cadence, and Stats attribution — real consequences, learned today
  from doc pages and discovered through lints after the fact.
- **It fixes real, live mistakes.** Both notes that set `offclock_types: [MEET]`
  (`body.md`, `love.md`) also carry a shadowed `offclock: true`
  (`note_offclock_shadowed`) — measured independently by two researchers. Two projects
  still carry legacy `theme:`. A typed clock-policy stage makes the shadowed state
  unrepresentable going forward.
- **One grammar everywhere.** Album, record, day, period, and bank notes already open
  with a species tile, kicker word, one title, and the pf foot row; areas and projects
  still open as stacked raw chrome (inline title + 6–10 Properties rows + H1). Only
  5/19 areas and 3/102 projects even have an H1. Closing that split is cheap because pf
  pays all the hard costs: ownership primitive, foot row, drawer, `bob props`
  byte-safety, takeover gating, the e2e harness.
- **Takeover finally reaches ~121 more notes**, `bank.md` included.

**Where it goes wrong if it grows** (the guards below are load-bearing):

1. **Derived-state confusion is the top risk.** A card showing status, blocked reasons,
   and counts beside editable rows invites "edit the card to unblock the project."
   Project lifecycle is computed from `^prj`, dependencies, and dates
   (`decisions:projects-block-from-prj-line`); the card and editor must look read-only
   exactly where they are read-only, with jump-don't-edit handoffs.
2. **Dashboard bloat.** Ready tables, Today queues, progress bars, and catalog rows in
   the card would duplicate the body, go stale between paints, and (for progress bars on
   growing task lists) actively mislead. Every researcher rejected the dashboard card.
3. **Parent edits are tree surgery.** One key rewires catalogs, hue, clock/type
   inheritance, blocking, capture routes, and historical Stats grouping (root parents
   are derived from the *current* tree). This is the one row that needs a real
   consequence preview and hard refusals, not just a link stage.
4. **A second frontmatter writer breaks everything above.** See §4.2.

**Alternatives considered and rejected** (all reports agree): keep native Properties
with better templates (underuses the foundation; weak orientation); a full configurable
dashboard (duplicate truth, stale paint, false progress signals); a per-home custom
field builder (nothing in the vault or capture grammar asks for it); nesting settings
under one `bob:`/`settings:` map (breaks every existing reader and ~45 live
declarations); `=+`-everywhere with no card (correct *fallback* if card adapters slip,
but leaves the title-block inconsistency and inheritance invisible).

## 2. Lead verification of contested claims

As lead I re-verified the claims the reports disagreed on or that only some found:

- **`bob-cli-pf` is in progress, not complete** (bead read 2026-11-22): phase `.3`
  (ownership primitive) closed; `.1`, `.2`, `.4`, `.5`, `.6` in progress. Everything
  below targets the epic's *approved contract*, and must re-check the as-landed APIs
  when it closes.
- **Role-table gap confirmed** (`src/native/props/roles.rs`): `type` is locked
  identity, record/album `parent` locked, temporal `parent` derived, and the derived
  patterns cover only `*_digest`/`*_drafted`/`review_*`/`zorg_*`/`generated_from_zorg*`
  (+ reference `source_markdown`). `NoteKind::Area` and `NoteKind::Project` exist, but
  `classify()` has no arm for them — so project `status`, `done_tasks`, `task_count`,
  `open_task_count`, `template`, and leftover `scheduled` all fall through to
  `loose()` and would be hand-editable in `=+` today. The pf plan already instructs
  `props-cli` to audit writers and complete this list; these rows belong in that audit.
- **`bank.md` classifies as Bank before the area check** (`roles.rs:212`): the path
  test returns `NoteKind::Bank` before `frontmatter_is_area` runs. Any area-key
  validation keyed only on `NoteKind::Area` silently misses `bank.md`.
- **The second writer is real** (`plugins/bob-project-tasks/main.js:561,574`): two
  `app.fileManager.processFrontMatter` calls rewrite `task_count`/`open_task_count` on
  every debounced metadata change — the exact API the plugins codebase bans elsewhere
  because it re-serializes the whole YAML block. cld additionally measured that the
  plugin's counts disagree with `bob projects list` on **all 43 live projects** (the
  plugin counts only `[ ]`/`[/]`/`[*]` under `## Tasks`; bob counts every open `#task`,
  blocked `[?]` included).
- **A byte-preserving parent-change stack already exists** (bob-navigation-hotkeys
  `208-parent-note-picker-model.js`, `209-…modal.js`, `211-parent-frontmatter-plan.js`,
  `682-plugin-parent-change.js`): a picker with `parentChangeWouldCycle` /
  `parentChangeKindRefusal` guards and a span-preserving frontmatter plan whose header
  comment explicitly bans `processFrontMatter`. The `=+` parent row should *reuse* this
  machinery, not invent a hierarchy writer.
- **Chord semantics are settled by the pf plan**: "`==` opens the card editor
  (existing), `=-` toggles the drawer, `=+` opens the property editor"; the `=+` header
  kicker already names `Area` and `Project` as `note_kind` words; D8 routes card-role
  keys from `=+` to their `==` editor; `==` falls through to Vim when no species
  matches. The bank_foot decision: on `bank.md` the drawer duplicates native Properties
  "by design until areas get a title-block card" — the epic's own wording anticipates an
  area title-block card on `bank.md`.
- **Species registry** (`240f-plugin-property-card-species.js`): seven kinds today
  (album, record, day, week, quarter, year, bank); area and project are absent. The
  kit's rule is stated at the top: "Hue says where, form says what, and words say both."
- **Vault census** (two independent live measurements, consistent): 19 areas (all with
  one-line `summary:`; 5 inbox files with `ready_cap: off`; 16/19 without `created`)
  and ~102 projects (~43 live, 51 done, 8 canceled; ~97 carry leftover
  `template: "[[new_project]]"`; 1 `root: true`; 2 legacy `theme:`; 0 uses of `priority`
  or `status: waiting`; 100/102 begin with the `^prj` line as body line 1).

## 3. Disagreements between the reports, adjudicated

### 3.1 Where does the schema editor live: `==` or `=+`? → **`=+`, with `==` as an entry point**

Four reports (cdx, cld, grk, mus) put the typed stages inside `=+`; gem alone builds a
dedicated curated `==` Area/Project Card Editor with `=+` handing off to it.

**Adjudication: the majority is right, and it matches what Bryan asked for.** Area and
project settings are flat scalars and short lists — there is no owned nested map like
album `record:` or bank `bank:` that earned those species a separate editor. A second
modal for ~9 flat keys duplicates stages `=+` already has, blurs "where do I edit this,"
and creates two UI writers for the same keys. gem's strongest argument — that `==`
falling through to Vim on a carded note is jarring once these cards look like every
other card — is satisfied more cheaply by **registering `area`/`project` in the `==`
species registry to open `=+` focused on the settings group** (cld A1, grk A2). The `=`
chord family stays complete; no third modal exists; `=+`'s existing grammar, guarded
session, undo, and YAML excursion carry over unchanged. gem's curated two-section
layout, digit-jump rows, and ghost-row presentation survive as the *settings group
design inside `=+`*, not as a separate surface. On `bank.md`, `==` keeps opening the
bank card editor (registry order: bank first), unchanged.

Consequence for roles: area/project settings keys must **not** be classified
`Role::Card` with a `prop_owned` refusal (that would make `=+` refuse its own writes).
They stay writable through `bob props update` with domain validation — either as
annotated loose keys in a contract (cld) or a Card role whose owner's writer *is*
`props` (gem). Both are workable; the contract annotation is the smaller change.

### 3.2 What does the project card say under the title? → **Lifecycle state, not the criterion**

cdx, grk, and mus render the cleaned `^prj` criterion as the card's subtitle ("DONE
WHEN …"); gem omits it as blatant duplication; cld shows a derived lifecycle line and
decorates the `^prj` line instead.

**Adjudication: gem and cld win on the facts.** 100/102 projects start with the `^prj`
line as the *first body line* — directly below the card. All five reports agree that
line can never be hidden (it is an active control), so a criterion subtitle puts the
same sentence on screen twice, ~12 px apart. The card family's whole idiom is "own the
title, hide the duplicate"; here the duplicate cannot hide, so the card must not create
it. The project card's subtitle slot instead carries what no body line states: the
**derived lifecycle** — `WIP` / `SCHEDULED · starts Dec 2` / `BLOCKED — waits on
[[sase_blog]]` / `⚠ no valid ^prj` / `DONE · Jun 14` — sourced from the existing
projects report, never from raw YAML `status` alone. cld's optional polish is worth
taking: a subtle CodeMirror line decoration on the recognized `^prj` line (slightly
larger, medium weight; nothing hidden or moved) makes it read as the note's goal.
Should Bryan strongly prefer the criterion on the card anyway, cdx's treatment (a
labelled "DONE WHEN" block with a stable link to the source line) is the right form —
listed as a decision below.

### 3.3 `bank.md` → **Mount the Area card, with explicit arbitration and a spike**

Three positions: mount the area card and arbitrate (cdx, cld, gem), keep the bank card
and add an area crumb to it (grk), leave `bank.md` excluded entirely (mus).

**Adjudication: mount the Area card.** The pf plan's own bank_foot decision names the
end state — the duplicate drawer lasts "until areas get a title-block card" — and D5's
stated blocker (area keys "have no typed stages yet") is exactly what this epic
delivers. Arbitration rules, merged from cdx and gem: the Area card mounts in the title
slot, adopts `# 🏦 Bank`, and owns the note's single foot row and the frontmatter
takeover; the bank card stays in the body with its banking content, `⊞ Edit`, and
species badge, suppressing its temporary `bank_foot` while the Area owner is active
(restoring it if the Area mount fails); `==` keeps opening the bank editor and the
`bank:` map stays card-owned, while `=+` gains the area settings rows. Two verified
engineering preconditions: (a) `roles.rs` must treat `bank.md` as a hybrid — Bank kind
for the `bank:` map, area validation for its area keys — because today the Bank arm
wins outright; (b) cld's spike: confirm the bank card's anchor under the hidden H1
survives title adoption (if not, mount without title ownership — the kit's fallback —
and record grk's crumb-on-the-bank-card as the fallback design).

### 3.4 How much live data on the card? → **Authored chips always; synchronous Ready at most; report counts deferred**

grk ships authored-only chips with no live numbers; cld, mus, and gem add a quiet
derived row (Ready meter, project/today/open counts) from the already-cached reports;
cdx ships counts only if their scope is explainable and explicitly omits Today.

**Adjudication: split by data source, which is also the reliability line.**

- **Authored policy chips** (present keys only: `READY CAP N`/`READY OFF`,
  `OFF-CLOCK`/`OFF · MEET`, type chip, `ROOT`, shadowed-clock warning) ship in v1.
  They paint from confirmed source bytes, cost nothing, and are the teaching surface.
- **Ready pressure** (`2/5 ready`, room/full/crowded ink) may ship in v1 *only* because
  `api.noteReady` is a synchronous, local, no-spawn API — it respects the kit's
  paint-from-local-data rule. It reads the whole resident lane
  (`decisions:note-ready-cap-counts-the-lane`), which the chip's tooltip should say.
- **Report-backed counts** (sub-areas/projects, open, today, blocked reasons on the
  lifecycle line) join as a Frame-2 in-place patch from the *already-subscribed* cached
  `bob areas list` / `bob projects list` services the catalogs fetch — never a new
  spawn, never a new report per card, and a missing snapshot renders as absent, not
  zero. If this patch slips, the card is still complete without it (grk's position is
  the safe floor). The blocked/scheduled lifecycle line is the one report-backed element
  worth prioritizing, because it is the card's main new information.

Unanimous never-list: catalog rows, per-status lane counts (the `## Tasks` badge row
owns them), progress bars or completion percentages, Today task lists, Stats charts.

### 3.5 Untitled-note title fallback → **Decision for Bryan; default: stem verbatim**

cdx, grk, and mus follow bob's existing derivation (H1 → alias → *humanized* stem); cld
(A9) and gem argue for the stem verbatim (`sase_pre_blog`, not `sase pre blog`).
14/19 areas and ~99/102 projects will use this fallback, so it dominates the look.
Default to **stem verbatim**: it keeps one spelling across the inline title, catalogs'
`[[stem]]` links, and `@route` capture identity, and avoids corrupting acronyms and
brand casing (`bob`, `gtd`, `sase`). The alternative keeps parity with
`bob areas list`'s humanized `title` field. Either way, no new `title:` frontmatter key
in v1 (gem's optional `title:`/`emoji:` rows are rejected by the other four: unused in
the vault, a new competing naming source, and emoji would have to ship on every other
surface).

### 3.6 Smaller calls

- **Inbox variant:** inbox files (per the existing `isInboxNote` route) are **area
  cards with an `INBOX` pill** (grk), not a third species word with its own tile (cld's
  variant is fine as a pill, not a kind). The untyped `area.md` root sentinel never
  mounts; templates, `done/`, and `_conflicts/` are excluded by the existing
  classifiers.
- **No nav rail** (unanimous): homes form a tree, not a ring; the parent crumb plus
  catalogs navigate. `[n`/`]n` keep reading the body.
- **Missing `created`:** silent on areas (16/19 lack it; a nag on 84% of areas is
  noise); projects may show the faint `no created date` like album/record. This is a
  species-specific softening of the pf missing-date rule — never backfilled from file
  times.
- **Terminal projects:** keep the card with muted wash and `DONE`/`CANCELED` pill +
  close date, no meta/pulse line. A project whose `^prj` is archived keeps its terminal
  identity (no manufactured missing-task error); an *active* project with no valid
  `^prj` shows the amber warning state.
- **`status: waiting`:** zero uses in the vault and display-only in bob; retire it from
  the docs/Bases story rather than build UI for it (cld A7; gem offers a `wip ↔
  waiting` toggle as a decision — default no).

## 4. The recommended design

### 4.1 The cards

Both cards are kit title-block cards: species tile + kicker, one owned heading, at most
one subtitle line, a content-gated chip line, the pf foot row (`▸ Properties · N` + lint
chip + created stamp) and `=-` drawer with where-marks. Target ~5 lines; collapse keeps
kicker, title, (project) state line, and foot.

```text
┌──────────────────────────────────────────────────────────────┐
│ [tile]  AREA · love                                    ⊞ =+  │
│ Abby                                                         │
│ Being a good dad to Abby: outings, play, toys, music.        │
│ OFF · MEET                                 2/5 ready         │
│──────────────────────────────────────────────────────────────│
│ ▸ Properties · 5                              created Jun 29 │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ [tile]  PROJECT · dev › sase                           ⊞ =+  │
│ sase_blog   [ WIP ]   ROOT                                   │
│ aka bob-cli                     2/5 ready · 18 open          │
│──────────────────────────────────────────────────────────────│
│ ▸ Properties · 8                              created Oct 20 │
└──────────────────────────────────────────────────────────────┘
- [ ] #task #prj Publish the SASE blog as a durable public trail! #hide ^prj
```

- **Kicker:** `AREA` / `PROJECT` + parent crumb from the local `parent:` chain (real
  links; Mod-click new tab; ellipsis past ~4 ancestors; top-level areas omit the
  `· area` crumb — it teaches the wrong thing). Projects add the lifecycle pill;
  inboxes add `INBOX`.
- **Title:** one `role="heading"` node; recognized first-body H1 (hidden at render
  time, Live Preview reveal-on-touch) → first alias → stem (§3.5). Bytes never change.
- **Subtitle:** area `summary:` (all 19 have one; absent collapses — no nag);
  project lifecycle line (§3.2). The blocked line names its reason: `waits on
  [[x]]` (≤2, then `+N`) or `parent project … is blocked`
  (`decisions:subprojects-inherit-project-blocking`).
- **Chips:** authored-only policy chips + synchronous Ready readout (§3.4); clicking a
  chip opens `=+` on that key. Optional right-aligned `@route` affordance (cld) is a
  nice-to-have, not v1-gating.
- **Material:** area ~8% hue wash (an area is where hue comes from), project ~4–5%,
  terminal ~2% + muted ink. Hue = the note's effective home color under the existing
  resolver; species is carried by form and word, never hue. No new colors; amber only
  for lint; `forced-colors`, reduced motion, 4.5:1, and ~420 px stacking per pf §7.
- **Tile glyphs:** final pick belongs to the visual pass with real screenshots, but the
  strongest candidates are gem's consistency pair — `layers` for AREA (already the
  `## Areas` catalog icon) and `target` for PROJECT (matches the `#prj` mark) — with
  cdx/cld's `compass`/`flag` as the alternative. Distinct silhouettes from all seven
  existing tiles; monochrome; `aria-hidden` with the word as the accessible prefix.
- **Mount rules:** typed areas and projects only, via the existing note classifiers;
  skip `area.md`, templates, `done/`, `_conflicts/`, embeds, popovers, canvas, print,
  mobile; fail-open restores native title, H1, and Properties in the same frame.
  Painting reads the metadata cache, confirmed source bytes, and synchronous local APIs
  — zero bob spawns, zero writes; Frame-2 report patches arrive in place via the
  existing subscriptions.

### 4.2 Two prerequisites (not optional)

1. **Complete the role table** (fold into in-flight `pf.2` if still open — `=+` reaches
   these notes either way): project `status` → derived (owner `projects sync`; teaching
   line "close, cancel, or reopen `^prj`"), `done_tasks` → derived (`bob task
   archive`), `task_count`/`open_task_count` → derived while they exist, leftover
   project `scheduled` → derived/legacy (`projects sync` hoists it), `template` →
   loose-but-folded provenance. `type` stays locked (area↔project conversion is a
   lifecycle operation with `^prj` and catalog consequences, never a key edit).
2. **Retire the second writer.** `bob-project-tasks`'s `processFrontMatter` calls must
   go before any takeover of project notes: they re-serialize the whole YAML block on
   every task edit, race `bob props` fingerprints (every count change staleness-refuses
   an open `=+` draft), and the counts are wrong by bob's definition on all 43 live
   projects. Default: retire `task_count`/`open_task_count` outright and update
   `projects.base` to live data; conservative alternative: a ~40-line byte-preserving
   span writer modeled on `211-parent-frontmatter-plan.js`. Bryan decides (§6).

### 4.3 The `=+` schema editor

Keep pf's grammar, write discipline, and chassis verbatim (250 ms dry-run, fingerprint,
inverse-op undo, stale-keeps-draft, close ladder honoring
`decisions:q-and-ctrl-bracket-mirror-esc`). Add, for area/project kinds:

- **A settings group** at the top, in contract order (stable across notes), labelled
  `AREA SETTINGS` / `PROJECT SETTINGS`; then loose keys in file order; then locked
  identity/lifecycle rows; then the folded Bob-managed group. `==` lands on the first
  settings row; reorder applies to loose rows only.
- **Ghost rows** for undeclared settings, faint and italic, showing the *effective*
  value and its source, computed by bob, never stored: "5 · plan.max_ready_per_note",
  "● blue · from dev", "off-clock MEET · from love", "on-clock — nothing above declares
  a policy". Enter sets an override; Ctrl+D on a declared setting clears to inherit,
  with a teaching line naming what will then apply. Precedence language must be exact:
  `ready_cap`/`task_refresh` apply **by residence** and never inherit ("Use Bob
  setting", not "Inherit from parent"); `task_type: off` is "Stop parent defaults", not
  "untyped" (a task's own field, reading rule, or global default can still decide);
  color `grey` is a deliberate mute, distinct from Inherit.

**Field contract** (merged; validation lives in bob, §4.4):

| Field | Kind | Stage | Validation / behavior |
| --- | --- | --- | --- |
| `parent` | both | restricted link picker | Completes eligible homes only (areas: root `area` or an area; projects: an area or non-terminal project), with kind + hue pips; writes one quoted scalar `"[[stem]]"`. Refuses self, cycles, descendants, `done/`, ambiguous stems — reusing the existing 208/209/211/682 picker-model, refusal, and byte-preserving plan machinery. Dry-run preview names consequences: hue change, inheritance changes, catalogs that refresh, Stats regrouping of past time, blocking changes. After apply, run `bob areas sync` / `bob projects sync` in the same guarded session (grk) or offer them explicitly with the catalogs' own stale-sync affordance as the safety net (cld/mus) — see §6. |
| `summary` | area | one-line text | Live `N/140` counter; multiline refused per `area_summary_multiline`; >140 warns, never refuses. No project `summary` row in v1 (the `^prj` criterion is the project's one-liner; a second would drift). |
| `color` | both | hue swatches | 8 palette hues + `grey` + Inherit; letter/digit accelerators; live tint preview; shows effective swatch **and source**; top-level collision badge ("used by dev"). Free text refused with the allowed list. |
| `task_type` | both | type picker | Configured types with hue ink + `off` ("Stop parent defaults") + Inherit; valid-but-unconfigured allowed with the existing warning. On a note with legacy `theme:`, save writes `task_type` and unsets `theme` in one undoable batch. |
| `offclock` + `offclock_types` | both | **one clock-policy stage** | Four modes with exact postimages: Inherit → remove both keys; On-clock → `offclock: false`, remove list; Off-clock → `offclock: true`, remove list; Off for types… → nonempty canonical list, remove boolean. One atomic, jointly-undoable batch; opening the stage never silently "cleans" a dual-key note, but a shadowed pair shows the warning with a one-Enter cleanup preview. Empty list is refused (it is not "all on-clock" — a boolean or ancestor policy would still apply). |
| `ready_cap` | both | count-or-off | 1–999, `off`, Inherit→"Use Bob setting (5)"; reads legacy YAML `false` as off; live effect line from `noteReady` ("6 ready · cap 8 → room"). |
| `task_refresh` | both | days | 1–365; residence-only scope stated; unused today but completes the contract. |
| `project_name_aliases` | both | list | Duplicate/ambiguity/stem-shadow diagnostics from the capture-targets rules; exact stem always wins. |
| `root` | project | toggle + consequence | `true` or unset (never `root: false`). Teaching both effects: own Stats lane for past and future time, **and** the note stops being a leaf (keep-moving successor eligibility changes). Disabled-with-explanation on top-level projects ("already a root"). Areas never show it. |
| `created` | both | pf date & time | Already loose in pf; preserves precision and offset style. |
| `status`, `done_tasks`, counts, `scheduled` | project | locked | Teaching lines name the writer; Enter on `status` jumps to `^prj` (navigation, no write). |
| criterion / schedule / dependencies / priority | project | read-only handoff rows | Virtual rows showing the `^prj` criterion, inline `[scheduled::]`, and Depends-On targets; Enter opens the Task Card on `^prj`. The editor never writes a frontmatter `scheduled`, `due`, or `deadline` — dates and deps live on the line (`decisions:projects-block-from-prj-line`, `decisions:task-deps-are-depends-on-links`). |
| everything else | both | generic pf stages | `template`, `tags`, `aliases`, `cssclasses`, unknown keys: full generic access; nothing hidden because it is off-contract. |

Figure references (rendered by the researchers; same directory):
[cld's cards and editor mocks from real vault data](area_project_property_cards__cld_cards.png)
([editor](area_project_property_cards__cld_editor.png)), [grk's anatomy](area_project_property_cards__grk_anatomy.png),
[key-routing](area_project_property_cards__grk_routing.png), and
[mount-decision](area_project_property_cards__grk_mount.png) diagrams, cld's
[one-writer routing flowchart](area_project_property_cards__cld_routing.svg), and
[cdx's concept sheet](area_project_property_cards__cdx.png) (narrow layout + clock stage).

### 4.4 bob-cli changes (single writer, bob owns the rules)

Extend `bob props`, not new per-kind CLI commands (unanimous): one byte-preserving
writer, one undo protocol, one validator that `==`-routed stages, `=+` generic ops,
paste, YAML fragments, and terminal use all pass through — a blocked or invalid value
must not be writable via any other entry point.

- Validate area/project contract keys in `prop.set`/`prop.set_yaml` using bob's
  existing parsers (`NoteColor`, theme/type parsing, `parse_offclock_types`, ready-cap
  and freshness ranges, areas/projects parent kind + cycle checks, alias collision
  checks), returning the existing typed refusal shape with bob's finding codes.
- Add atomic multi-key ops for the two coordinated edits (clock policy's two keys;
  `theme`→`task_type` migration) — either cld's `setting.set`/`setting.clear` ops that
  bob expands into span ops, or plain multi-op batches the plugin composes; bob-side
  expansion keeps the precedence rules in one place and is preferred.
- Expose the contract in `bob props show -f json`: per setting, the stage kind, choices
  (hues with `used_by`, configured types with hue), declared vs **effective value with
  its source note**, and existing lint findings — so ghost rows can never drift from
  Rust's precedence rules. Gate behind one new capability flag; the editor degrades to
  plain loose rows without it.
- Optional: per-note `contract_issues[]` in `bob areas list` / `bob projects list` so
  the foot lint chip can include bob findings (`note_offclock_shadowed`,
  `area_color_invalid`, …) without a spawn.
- Docs per `cli_rules`/`docs` memory: `docs/props.md` contract section, cross-links
  from `docs/areas.md` and `docs/projects.md`, plugin reference page. Releases ride the
  daily train; plugins feature-detect (`decisions:bob-cli-releases-ride-a-daily-train`).

## 5. Phased ship plan

One follow-on epic after `bob-cli-pf` lands (phase A can start once `pf.2` settles;
never widen pf itself):

| Phase | Repo | Content | Size |
| --- | --- | --- | --- |
| **0 · One writer** | bob-plugins (+vault) | Retire (or span-rewrite) the `bob-project-tasks` count writer per Bryan's §6 decision; one-time byte-preserving key removal if retiring; `projects.base` update. Independent of everything else and worth doing even if the epic stalls. | S |
| **A · Contract** | bob-cli | Role-table rows (§4.2.1, folded into `pf.2` if open); contract validation + atomic multi-key ops + effective-value/choices JSON + capability flag; optional `contract_issues`; golden byte-preservation tests (clock postimages, theme migration, shadowed cleanup, inverse ops on dual-key legacy notes); docs. | M |
| **B · Cards** | bob-plugins | `area`/`project` species + shared home adapter: title adoption, crumb, subtitle/lifecycle, authored chips + noteReady, foot + where-marks + managed fold, collapse, optional `^prj` decoration; Frame-2 report patch; real-Obsidian screenshots (top-level area, sub-area, inbox, open/blocked/scheduled/done project, `root: true`, narrow, light/dark). Native Properties stays visible — safe half-state. | L |
| **C · Editor** | bob-plugins | Settings group, ghost rows, typed stages (parent via the 208/211 machinery, hue, type, clock policy, cap, days, aliases, root), `^prj` handoff rows, `==` registration → `=+`, degraded mode without the capability; e2e: edit/add/delete/undo, locked-row teaching, stale refusal, byte-identical untouched keys. | L |
| **D · Takeover + bank** | bob-plugins (+docs/memory) | Wire `propertyCardOwnFrontmatter` under pf.6 eligibility for both kinds; `bank.md` spike then Area-card mount with bank_foot suppression and hybrid roles fix; reroute native entry points (gem's finds: the areas-catalog "add summary" focus helper; `Mod+;`); full fail-open e2e matrix incl. `bank.md`, `area.md`, templates, `^prj` cursor integrity; glossary strand updates only via `/sase_memory_write` authorization at plan time. | M |

Acceptance for the epic: every eligible area/project opens with a ≤5-line card; `=+`
(and `==`) edit every contract setting with a fitting stage, show effective value +
source for undeclared settings, and refuse invalid values with bob's message; every
write is one byte-preserving `bob props update` with byte-exact undo; the `^prj` line
behaves exactly as today; painting and drawer/fold/resize issue zero writes and zero
spawns; native Properties is gone on eligible notes including `bank.md` and every
failure path restores it; no frontmatter writer other than bob touches these notes.

## 6. Decisions for Bryan (defaults first)

1. **Schema editor surface** — default: typed stages inside `=+`; `==` on area/project
   opens the same modal on the settings group. Alternative (gem): a separate curated
   `==` editor with `=+` handoff.
2. **Project card subtitle** — default: derived lifecycle line only; criterion stays on
   the (optionally decorated) `^prj` line. Alternative (cdx/grk/mus): render the
   cleaned criterion as a "DONE WHEN" block with a source link.
3. **`bob-project-tasks` counts** — default: retire `task_count`/`open_task_count` and
   repoint `projects.base`; alternative: byte-preserving span writer keeping today's
   (bob-divergent) numbers.
4. **Untitled-note title** — default: stem verbatim; alternative: bob's humanized
   derivation for parity with `bob areas list` titles.
5. **Parent apply → catalog sync** — default: run the existing syncs inside the same
   guarded session so both hosts update before the modal closes; alternative: key-only
   write with an explicit sync offer and the catalogs' stale-sync chip as backstop.
6. **Live counts on the card** — default: authored chips + synchronous Ready in v1,
   report-backed lifecycle/counts as the Frame-2 patch; alternative (grk): authored
   chips only, no numbers.
7. **`bank.md`** — default: Area card mounts and takeover lands (post-spike);
   fallback (grk): keep the bank card and add the area crumb/summary to its header.
8. **Smaller defaults:** inbox = area card + `INBOX` pill (yes); no `title:`/`emoji:`
   keys (yes); `status: waiting` stays retired, no toggle (yes); missing `created`
   silent on areas (yes); notebooks/references copy this adapter in a later epic (yes).

## 7. Sources

**Lead verification (this report):** bead `bob-cli-pf` (audited read; status and
decisions), `plan:202611/card_owned_frontmatter.md` (audited read; chord table, D4/D5,
D8 routing, bank_foot wording, `=+` header kinds), bob-cli `e98c7fe9`
`src/native/props/roles.rs` (classify arms, derived patterns, bank-before-area),
bob-plugins master `plugins/bob-project-tasks/main.js:561,574`,
`plugins/bob-navigation-hotkeys/src/{208,209,211,682,701}*`,
`plugins/bob-ledger-tools/src/240f-plugin-property-card-species.js`; audited glossary
reads: Property Card, Area Note, Project Note, Project Task, Record Card, Album Card,
Bank Card.

**Member reports** (each with its own full source lists, live-vault censuses, and
figures): [cdx](area_project_property_cards__cdx.md) — inheritance-control nuance
(empty clock lists, `task_type: off`, grey vs inherit), parent-mutation release gate,
accessibility targets; [cld](area_project_property_cards__cld.md) — vault census,
second-writer measurement, contract/ghost-row design, `^prj` decorate-don't-dock,
rejected alternatives; [grk](area_project_property_cards__grk.md) — species/material
split, authored-only chips, mount-matrix, `==`→`=+` registration;
[mus](area_project_property_cards__mus.md) — role routing table, option analysis
(minimal card vs dashboard vs no-card fallback), lint-code fidelity;
[gem](area_project_property_cards__gem.md) — roles.rs and bank-classification line
numbers, native entry-point reroutes, five-phase plan, tile semantics, census detail.

Relevant decisions honored throughout: `projects-block-from-prj-line`,
`task-deps-are-depends-on-links`, `note-ready-cap-counts-the-lane`,
`off-clock-note-defaults-filter-by-task-type`, `off-clock-follows-tag-then-note-default`,
`subprojects-inherit-project-blocking`, `theme-hue-is-config-pin-exempt-area-hash`,
`q-and-ctrl-bracket-mirror-esc`, `bob-cli-releases-ride-a-daily-train`.
