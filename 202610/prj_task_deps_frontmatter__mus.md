# Project-task dependency links: frontmatter `depends_on`, blocked-project inheritance, and link pruning

Research report — researcher `mus`. Independent conclusions; peer reports not consulted.

## 0. TL;DR

The request is sound and worth building, with adjustments. The core diagnosis is correct:
today a `^prj` task can own a `⛓️ DEPENDS ON:` child line (the example
`~/bob/job_apply_to_databricks.md` proves the parser already accepts it), but nothing else
treats the *project* as blocked — so the `^prj` line reads `[?]` while its resident tasks
stay `[*]`, the dash still counts "2 next/wip / 0 blocked", and the dependency lives in a
contested child slot under a machine-managed lifecycle task. Moving the project-level edge
set into frontmatter and deriving blocked-ness downward is the right fix, and it has a
direct precedent: project `scheduled` already lives in frontmatter and propagates inward.
The main risks are (1) splitting the "one managed line is the source of truth" contract
across two stores, (2) four-parser sync (Rust, nav-hotkeys, ledger-tools, cycler), and
(3) getting unblock-recovery and link-pruning semantics exactly right. My recommended
solution keeps the Depends-On line as the source of truth for *ordinary* tasks, adds a
frontmatter `depends_on` list as the source of truth for *projects*, migrates existing
`^prj` lines in `bob task reconcile`, and makes blocked-project inheritance a derived
`[?]` reason alongside open deps and future schedules.

## 1. What I read

- `docs/task-dependencies.md` (contract §§1–6), `docs/projects.md` (sync rules, Task Card,
  defer-prune, project-note creation), `docs/task-status-hooks.md` (ledger, duplicate and
  canceled cleanup, empty-Pomodoro removal, dependency edges, derived Blocked).
- `src/native/task_dependencies/` (parser/formatter/link-form/legacy), `src/native/task_status_hooks/reconcile.rs`
  + `reconcile/apply.rs` + `reconcile/fields.rs` + `sync.rs` (`task_transition`, `task_dependency_states`,
  `has_derived_block`), `src/native/projects/` (`scan.rs`, `sync.rs`, `edits.rs`, `model.rs`).
- `~/bob/job_apply_to_databricks.md` and `~/bob/job.md` (live example).
- Memory (via `sase memory read`): `decisions:task-deps-are-depends-on-links`,
  `decisions:task-lanes-are-sticky`, `decisions:today-is-read-from-the-ledger`, full
  `glossary` web (Task Dependency Link, Project Task, Project Note, Task Link).
- Linked `bob-plugins` checkout (via `sase repo open bob-plugins`):
  `bob-navigation-hotkeys/src/660-plugin-project-notes.js`,
  `src/100-yank-and-paths.js` (`parseProjectSourceTaskLine`),
  `src/110-project-seed.js` (`buildProjectContentFromTask`,
  `applyProjectCreationFrontmatter`), `src/590-plugin-dependency-stage.js`,
  `src/600-plugin-dependency-mirror.js`, `src/220-property-targets.js`.

## 2. Current state

### 2.1 Ordinary-task deps: one managed line, fields derived

A task's prerequisites are plain, never-transcluded task links on one managed
first-child `⛓️ **DEPENDS ON:**` line. That line is the source of truth; `bob task
reconcile` (still accepting `bob task-status-hooks`) projects it into `[dependsOn::]` /
`[id::]` through R1–R10 (adopt R2, heal R3, canonicalise, R4 breadcrumbs, R5–R7 warnings,
R8 legacy children, R9 empty-line deletion, R10 malformed no-touch). Only open dependents
(Todo / In-Progress / On-Hold incl. `[?]`) are reconciled; closed tasks are never touched.
Blocked is `[?]` while any prerequisite is open (AND, finish-to-start) or `scheduled` is
future. Linking the dependent under today's open Pomodoros promotes open prerequisites to
Next; closing a dependent never closes prerequisites; closed prerequisites stay as muted
history. Decision `task-deps-are-depends-on-links` and `docs/task-dependencies.md` own
this; four parsers must stay in sync (Rust, nav-hotkeys grammar, ledger-tools chips,
cycler/block-id-prompt recognisers).

### 2.2 `^prj` tasks: the line is accepted but the project is not blocked

Nothing in `task_status_hooks` excludes `^prj` lines — the reconcile projection applies to
any open `#task`, and `reconcile/fields.rs` even has a `^prj` stamp-placement test. So
adding a dep via `Ctrl+Shift+P` today writes a Depends-On child under `^prj` plus
`[dependsOn::]` on the `^prj` line and marks `^prj` itself `[?]`. That is exactly what the
example shows:

```markdown
- [?] #task #prj Apply to DataBricks NYC role(s)! [fresh:: 2026-10-12] [created::2026-10-12] #hide [dependsOn:: job__update-linkedin] ^prj
    - ⛓️ **DEPENDS ON:** [[job#^update-linkedin]]
```

Meanwhile the project's two resident `[*]` tasks are untouched, and the status-group badge
reads `2 next/wip · 0 blocked`. Three things are unintuitive about this, in increasing
order of importance:

1. **Storage slot.** The `^prj` child slot is contested: `bob projects sync` owns the
   generated `🧩 Sub-projects:` line directly under `^prj`, plus managed schedule/work
   logs that the project-note keymap explicitly preserves and moves. A Depends-On line
   wedged in as first child fights that ownership and reads as a "sub-subullet" of the
   completion-criteria task rather than a property of the project.
2. **Surfacing.** `^prj` uses `#hide`, not checkbox state, as its dash-surfacing
   mechanism, and `projects list` `SHOWN` already excludes `[?]` so blocked tasks "do not
   accidentally surface the lifecycle task". A `[?]`-with-`#hide` `^prj` is therefore
   doubly hidden: the blocked signal is invisible, and residents still look actionable.
3. **No inheritance.** `task_dependency_states` + `has_derived_block` know only per-task
   open-dep ids and per-task future `scheduled`. No code path reads "my note is a project
   whose `^prj`/project is blocked". There is no `frontmatter` or `project` concept in
   `task_status_hooks` at all (grep finds only a doc comment about `[[project]]`
   frontmatter for daily-note detection). Schedule propagation is the only project→task
   inheritance that exists, and it lives in `bob projects sync` (stamping `[scheduled:: P]`
   onto ordinary tasks), with `reconcile` merely deriving `[?]` from the stamped date.

### 2.3 The `scheduled` precedent — the model to copy

Project `scheduled: YYYY-MM-DD` frontmatter is the sole project schedule; `sync` stamps
ordinary tasks and forces `#hide` on future-dated `^prj`; `reconcile` derives `[?]`.
Ownership is clean: `sync` writes dates, `reconcile` owns `[?]`, dash needs no query
change. Project deps should follow the same split: **project command writes the edge set,
`reconcile` derives `[?]`**. The request's frontmatter proposal is therefore architecturally
consistent, not a new pattern.

### 2.4 Keymaps today

- **`Ctrl+Shift+P` (Task Card → `b` / Depends-on stage).** Vault-wide fuzzy search over
  open tasks, writes the Depends-On line + `[dependsOn::]` in one transaction, sets `[?]`
  when the target is open, promotes prerequisites, recovers immediately on last-removal.
  It does not special-case `^prj`: cursor on a `^prj` line writes the child line described
  above. The defer path (`scheduled`) already does Pomodoro-link pruning in the same
  transaction (dedicated-bullet removed with subtree, otherwise token-only) — the exact
  semantics the request wants for blocking.
- **`Ctrl+Shift+Option+N` (create project note from task).** Note the name drift: the
  request says `<cmd+ctrl+shift+n>`; docs and code say `<ctrl+shift+option+n>` (same
  physical chord on macOS: `option` = `alt`, `cmd` shown in some cheatsheets). Functionally:
  `parseProjectSourceTaskLine` extracts description/priority/schedule/blockId and
  **drops dependency state entirely** (no `dependsOn` in the returned struct);
  `buildProjectSeedFromChildBullets` converts qualifying child bullets to tasks/sections/logs
  with no Depends-On awareness; `applyProjectCreationFrontmatter` writes only
  `parent/type/status/scheduled`. So a source task's Depends-On line today is either
  converted to ordinary tasks (wrong), carried as managed logs (wrong), or lost. The
  reverse direction (`convertProjectNoteToTask` → `buildTaskBlockFromProjectNote`) has the
  symmetric gap: there is no frontmatter-dep slot to restore from.
- No `depends_on`/`dependsOn` frontmatter key exists anywhere in `src/`, `docs/`, or memory.
  Dataview inline parsing (`dataview/tasks/task.rs`) knows `[dependsOn::]`; project
  `scan.rs` knows `status/parent/scheduled/aliases/ready_cap` — deps would be a new
  frontmatter reader in both Rust and JS.

### 2.5 Link pruning today

`reconcile` removes cross-Pomodoro duplicate lines, canceled-reference subtrees, completed
references (retire/relocate + `🍅` repair), then empty Pomodoros — but **never removes a
live link because its task became `[?]`**. By the time it runs, the nav defer-prune has
usually already removed the deferred task's links, so "a deferred task's dependency chain
never got the chance to seed a promotion". Blocked-via-deps has no equivalent prune: a
newly `[?]` task keeps its ledger links, keeps seeding Next-promotion for its subtree,
and keeps a Today presence that contradicts "blocked means not today". The request's
prune rule closes a real gap, and the empty-Pomodoro pass already handles the "section
becomes empty" half for free.

## 3. Critique: is this a good idea?

**Yes — with five adjustments (marked [A1]–[A5]).** Blocking the residents of a blocked
project is clearly right: showing `[*]` "next up" work inside a project whose completion
criteria are themselves waiting on an unmet prerequisite is the exact false-affordance in
the example, and per-residence blocking matches how future-scheduled projects already
behave. Frontmatter storage is the right call over keeping the child line, for the
`scheduled` symmetry and child-slot ownership reasons above.

Alternative I considered and rejected: keep the `^prj` Depends-On line and merely
propagate `^prj`-is-`[?]` downward. It is a smaller diff (no migration, no new
frontmatter grammar, no decision-record amendment) and would fix the example's badge. But
it preserves the contested-slot problem, keeps project state split between a hidden
lifecycle task and note metadata, and leaves the create-project/convert-back keymaps
lossy. The frontmatter move costs a migration but pays it back in queryability
(Dataview/Tasks can index a list field; a child line under a hidden task cannot) and in
keymap clarity. Take the larger change.

Caveats that force the adjustments:

- **[A1] `depends_on` vs `dependsOn`.** The request names the frontmatter key
  `depends_on`. Keep that spelling: YAML frontmatter keys in this vault are snake_case
  (`task_count`, `project_name_aliases`, `ready_cap`), while `dependsOn` is the Tasks-inline
  camelCase field. New key `depends_on`, YAML list of strings. Value form needs a decision
  (see §5.1): I recommend canonical dependency **ids** (`job__update-linkedin`) as the
  stored form with wikilink targets resolved at write time — ids are what `task_dependency_states`
  actually joins on, they survive renames of link brevity, and they match `[dependsOn::]`
  values so the same resolver/warnings apply. Writers accept wikilinks from the picker and
  persist ids; readers never parse wikilink syntax out of YAML.
- **[A2] "Whenever a project is blocked" is too broad as stated.** Projects can be
  not-actionable for several reasons: unmet `depends_on`, future `scheduled`, `status:
  waiting`, terminal `done/canceled`. Only the first two should propagate `[?]` to
  residents — and they already partially do via different mechanisms (`scheduled` via
  stamped dates, `waiting` deliberately does *not* block today). Terminal projects must
  never block residents (closed `^prj` + archived tasks), and `waiting` needs an explicit
  non-goal statement or someone will "fix" it later. Define **blocked project** narrowly:
  *active* (`status` non-terminal, `^prj` open) AND (`depends_on` has ≥1 open target OR
  `scheduled` is future). Everything else is out of scope.
- **[A3] Do not blocked-propagate into `done/`, daily notes, or through `^prj` itself
  carrying a line.** `reconcile` skips the previous-daily snapshot and never touches closed
  dependents; project inheritance must respect both. And the migration must be one-way and
  total: after it, a Depends-On line or `[dependsOn::]` on a `^prj` line is malformed input
  to be adopted into frontmatter (R2-style), never a second live store. Two stores that can
  disagree will disagree.
- **[A4] Link pruning needs a recovery story.** Removing live ledger links on block is
  correct (blocked means not-Today; cf. `today-is-read-from-the-ledger`), and sticky lanes
  already state removal never changes the lane while Blocked overrides every lane — so the
  unblocked task recovers to Ready (or Next only via fresh promotion/recent-activity), not
  to its pre-block lane. That matches deferral precedent, but it is a behavior change for
  dep-blocks specifically: today a dep-blocked task keeps its links and its lane claim.
  State it explicitly in the decision record and the reconcile output, or the first
 /prune will read as data loss. Prune scope: live links under *open* Pomodoros in the
  current daily note only (same scope as canceled/duplicate cleanup); never closed
  `🍅` history, never other days.
- **[A5] `#ref` residents and sub-project transitivity need explicit rulings.**
  The example project contains two `#ref` follow-up tasks. "Any task that lives in a
  blocked project" by residence includes them — I recommend yes, block by residence
  regardless of `#task` subtype (`#ref` follow-ups are ordinary work items; the `^ref`
  lifecycle task itself lives on reference notes, not project notes, so highlights-sync is
  unaffected — but say so). Sub-projects: block transitively (parent blocked ⇒ child
  project blocked ⇒ child residents blocked), with cycle warnings mirroring R7. Without
  transitivity the first real vault hierarchy will re-create the example bug one level down.

A further minor correction: the request's `<cmd+ctrl+shift+n>` should read
`<ctrl+shift+option+n>` (docs `projects.md` "Create project note from task"; macOS
`option`≡`alt`). Also `bob task reconcile` is the current name (`task-status-hooks` still
accepted) — the request already uses the right one.

## 4. Requirement-by-requirement assessment

| Requested item | Verdict | Notes |
|---|---|---|
| Dep on `^prj` → `depends_on` frontmatter, not child line | Adopt with [A1], [A3] | Needs grammar (§5.1), R2-style adoption, writer/reader updates in 4 parsers. |
| Update project-note keymap for correct conversion | Adopt | Both directions: task→project seeds frontmatter; project→task restores a Depends-On line. Currently lossy — the highest-risk JS work. |
| Residents of blocked projects are `[?]` (any blocked reason) | Narrow per [A2], transitive per [A5] | Active + (open dep OR future schedule) only; transitive through `parent` chains; terminal/`waiting` excluded. |
| `Ctrl+Shift+P` on `^prj` writes frontmatter + derives state automatically | Adopt | Must also prune the dependent-project's residents' ledger links in the same transaction (defer-prune semantics). |
| Blocked tasks lose task links (+ empty Pomodoro cleanup) | Adopt with [A4] | Scope to open-Pomodoro live links; empty-Pomodoro pass already exists; recovery rank becomes Ready. |
| `reconcile` checks block-worthy tasks + removes links | Adopt | New derived-block reason + link-prune pass before promotion; report counts. |
| Update "task dep links" glossary term | Adopt | Plus amend `decisions:task-deps-are-depends-on-links` (new record, not in-place edit) and `docs/task-dependencies.md` §§1/4/5. |

## 5. Recommended solution

### 5.1 Data model: `depends_on` frontmatter list of dependency ids

```yaml
depends_on:
  - job__update-linkedin
```

- Key `depends_on` (snake_case, per [A1]); absent/empty = no project deps. Flow form
  (`depends_on: [a, b]`) accepted on read, block list canonical on write — same tolerance
  pattern as `project_name_aliases`.
- Values are canonical dependency ids (the `[id::]`/dependency_id space), not wikilinks:
  stable under link-shortening, directly joinable in `task_dependency_states`, healable via
  existing R3 logic. The picker resolves chosen tasks to ids at commit; hand-edited unknown
  ids warn (`unadoptable_dependency_id` analogue, e.g. `unresolvable_project_dependency`)
  and never block — mirroring R4's "unresolved never blocks".
- `^prj` lines must not carry a Depends-On child or `[dependsOn::]` after migration; if
  found, `reconcile` adopts them into frontmatter (new **R11**: `^prj`-line adoption —
  resolve line+legacy children to ids, append to `depends_on` deduped, delete line,
  strip field, report `adopted_project_dependencies`). Malformed `^prj` lines warn and are
  left alone (R10 analogue). This auto-fixes the example file.
- `docs/task-dependencies.md` gains a §7 (project deps); the glossary `Task Dependency
  Link` term gains a project paragraph ("a `^prj` task's prerequisites live in its note's
  `depends_on` frontmatter; a Depends-On line on `^prj` is legacy input adopted on
  reconcile"); decision record gets a *new* superseding-amendment record, not an in-place
  edit (decisions are immutable).

### 5.2 Derived state: project-blocked as a third `has_derived_block` reason

In `task_status_hooks/sync.rs`, extend the existing

```rust
has_derived_block = !open_dep_ids.is_empty() || future_scheduled.is_some()
```

with `|| resident_of_blocked_project`. Computation order per run:

1. Parse frontmatter `depends_on` for all project notes (reuse `projects::scan`
   frontmatter helpers) + resolve ids to open/closed via the same identity map
   `task_dependency_states` uses (archive/`done/` ids = closed history, never blocking).
2. Compute blocked-project set: active projects with ≥1 open dep id (transitive closure
   through `parent` links; cycles warn R7-style, all members stay blocked). Future
   `scheduled` already blocks via stamped dates — keep that path, do not double-implement;
   but *include* dep-blocked parents' children even when the child has no stamped date.
3. Every open non-`^prj` task residing in a blocked project gets `MarkBlocked`; `^prj`
   itself derives `[?]` from its own note's `depends_on` (keeps the example's `[?]`
   meaningful, now as derived state rather than line state). Closed tasks untouched;
   previous-daily snapshot untouched.
4. Recovery (`Unblock`) uses the existing `recovery_desired` path unchanged — which, per
   [A4], yields Ready absent fresh promotion. Document it.

`bob projects list` `SHOWN` already excludes `[?]`; no dash query change needed (same claim
`projects.md` makes for schedule-blocks). `blocked.md` likewise needs no change.

### 5.3 Link pruning (both writers)

- **Authoritative batch (`reconcile`).** After Blocked planning and before promotion
  mapping, delete live block-link occurrences of newly-`MarkBlocked` tasks under open
  Pomodoros in the current daily note (dedicated-bullet/token semantics copied from the
  nav defer-prune and the canceled-reference pass), then run the existing empty-Pomodoro
  removal in the same invocation so emptied sections disappear. Report
  `blocked_link_removals` + `removed_empty_pomodoros` (existing counter). Dry-run prints
  without writing, per existing guarded-write behavior (notes modified <2s ago deferred).
- **Interactive (`Ctrl+Shift+P`).** When the Depends-on stage commits an open-target dep
  onto a `^prj` (or any commit that newly blocks a project), the same transaction writes
  frontmatter, sets `^prj` `[?]`, marks residents `[?]` in their notes, and prunes those
  residents' live links from today's open Pomodoros. Reuse the defer-prune code path, not a
  copy. Unblock path (last dep removed / prereq closed): recover residents immediately to
  derived rank (mirrors "Removing a dependency recovers immediately" §5), links stay gone.
- Promotion interplay: pruned tasks stop seeding Next-promotion that same run (the existing
  "rewritten Pomodoro section is scanned again" rule already guarantees this ordering).

### 5.4 Keymap details (`bob-navigation-hotkeys`, coordinated with `bob-cli`)

1. **Depends-on stage**: detect `^prj` dependent (cursor on `^prj` line, its Depends-On
   line, or a chip/link naming `^prj`) → commit to frontmatter `depends_on` (append,
   dedupe, canonical block-list form, preserve line endings/final newline) instead of a
   child line; refuse prose/multi-task scopes as today; keep `N<Ctrl+Shift+P>` counted
   behavior for ordinary tasks but refuse counted scope spanning `^prj` + non-`^prj` with a
   short reason (mixed stores). Cycle-guard uses frontmatter ids + line ids jointly.
2. **Create-project (`Ctrl+Shift+Option+N`)**: `parseProjectSourceTaskLine` must additionally
   capture the source block's Depends-On line + `[dependsOn::]` + R8 legacy children (needs
   block Range, not just the line — extend the source-block capture); seed them into the new
   note's `depends_on` frontmatter via `applyProjectCreationFrontmatter`; do not emit them
   as child tasks/sections/logs. Reverse (`buildTaskBlockFromProjectNote`): restore
   `depends_on` ids as a canonical Depends-On line + `[dependsOn::]` on the restored task.
3. **Ledger-tools chips + cycler recognisers**: chips render project deps from frontmatter
   (muted when closed, `＋`/`×` edit frontmatter, not the line); `is Depends-On line`
   recognisers must *reject* any child line under `^prj` as a live edge source post-migration
   (it is R11 input, not state) to avoid double-counting during the migration window.

### 5.5 `reconcile` migration for the example file

On `~/bob/job_apply_to_databricks.md`: R11 reads `[[job#^update-linkedin]]` + field
`job__update-linkedin`, writes `depends_on: [job__update-linkedin]` (block list),
deletes the child line, strips `[dependsOn:: …]` from `^prj`, leaves `^prj` `[?]` (now
derived), marks both `[*]` residents `[?]` (new reason), prunes any of their live ledger
links, and reports all of it. `job.md`'s `^update-linkedin` (`[/]`, open) keeps blocking;
closing it unblocks the project and residents recover to Ready. No `job.md` write needed.

### 5.6 Tests and rollout

- Rust vectors: R11 adoption table (well-formed `^prj` line, field-only `^prj`, legacy
  child under `^prj`, malformed left alone, archive target never blocks, cycle across two
  projects, sub-project transitivity, terminal project exempt); blocked-project
  `task_transition` matrix (resident `[*]`/`[/]`/`[ ]` → `[?]`; closed untouched;
  unblock → Ready); prune tests (dedicated bullet vs token, empty-Pomodoro collapse,
  closed-Pomodoro history preserved); idempotence (second run no-op).
- JS: nav stage `^prj` commit (frontmatter written, no child line), create-project seed +
  reverse-restore round-trip, chip render/edit against frontmatter.
- Docs in the same change (contract-first rule): `docs/task-dependencies.md` §7,
  `docs/projects.md` (frontmatter field + sync/reconcile ownership line),
  `docs/task-status-hooks.md` (third block reason + prune pass), glossary term, new
  decision record superseding-amending `task-deps-are-depends-on-links` for the `^prj`
  scope only.
- Order: contract + Rust (`reconcile` R11, derivation, prune) first with the example file
  as fixture; nav keymaps second against the shipped CLI; ledger-tools/cycler third; vault
  migration is just "run `bob projects sync` then `bob task reconcile`" — no separate
  migration script needed since R11 is the migration.

## 6. Open questions for the lead (not blockers)

1. Should `status: waiting` projects opt into propagation later? I say no for v1 ([A2]).
2. Should closing the last open project prereq *re-link* residents into their prior
   Pomodoro slots (§12-style "unblocked successor links")? I say no — links stay gone,
   matching deferral; re-linking would resurrect stale Today claims.
3. Frontmatter flow-vs-block canonical form and `depends_on` key order within frontmatter
   (`status` adjacency?) — trivial, pick one and pin it in tests.

## 7. Sources consulted

Contract, project, and hooks docs named in §1; the two vault notes; the four decision/
glossary memories named in §1; `task_status_hooks` (`sync.rs` transitions,
`reconcile*.rs`, `references.rs`, `compose.rs`, `pomodoro.rs`) and `projects`
(`scan/sync/edits/model`) sources; nav-hotkeys sources named in §1. No peer `__cdx/__cld/
__grk/__gem` reports, transcripts, or summaries were sought or read; shared inputs above
are the only overlap.
