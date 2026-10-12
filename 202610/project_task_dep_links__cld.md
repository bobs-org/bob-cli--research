# Project Task Dependency Links: `depends_on` Frontmatter, Project-Inherited Blocked, and Pomodoro Link Consumption

_Researcher: cld · 2026-10-12 · bob-cli, bob-plugins, Bob vault_

## 0. TL;DR

- **The core idea is right.** In GTD terms, a project waiting on something has no next
  actions. Its tasks are not actionable, so they should read Blocked `[?]` and stay out
  of today's Pomodoros. Per-task workarounds don't scale. `N<Ctrl+Shift+P>` → `b` can add
  the same prerequisite to every task, but it misses tasks added later and clutters every
  line.
- **Most of the "unintuitive" result in `job_apply_to_databricks.md` comes from missing
  inheritance, not from where the dependency is stored.** The `^prj` task correctly
  became `[?]`. Its two tasks stayed Next `[*]` and stayed linked in today's JOB
  Pomodoro. That happens because nothing in bob-cli or the plugins knows that a project
  can be blocked.
- **`depends_on` frontmatter is a good home, with one condition.** Treat it as the `^prj`
  task's Depends-On line moved into frontmatter: same link grammar, same identity rules,
  same R1–R10 reconciliation. Keep the derived `[dependsOn::]` / `[id::]` fields on
  `^prj`. Then it is one dependency model with two storage spots, not two models. A
  cheaper alternative exists: keep the line under `^prj` and add only inheritance
  (§5, option A). It delivers most of the value.
- **"Blocked tasks should not have Task Links" conflicts with a documented feature.**
  Linking a blocked dependent under today's Pomodoros is how its prerequisites get raised
  to Next. The glossary, `docs/task-dependencies.md` §5, and a pinned CLI test all
  promise this. I recommend keeping the invariant but defining removal as
  **consumption**: reconcile first promotes the blocked task's open prerequisites (Next
  is sticky, so they stay), then removes the link, then deletes any Pomodoro left empty.
- **Do not copy dependency ids into member tasks' fields** the way project `scheduled` is
  copied. The existing R1 (drop unaccounted ids) and R2 (adopt field-only ids into a
  line) rules would either strip the copied ids or turn them into permanent per-task
  dependencies after a move or a cut-and-paste. Derive inheritance at read time instead,
  from the note itself.
- **Hidden costs to accept or address:**
  - Members lose their lanes when blocked. "Lanes don't survive Blocked" is the stated
    reopen trigger of `decisions:task-lanes-are-sticky`.
  - About ten immediate code paths would wrongly unblock members unless taught the rule.
  - `blocked.md` would show project-blocked tasks nowhere.
  - A project that depends on one of its own tasks can deadlock, and so can a cycle
    between two projects.
  - Rollout order matters: bob-cli first. An old reconcile would turn frontmatter-only
    deps back into a Depends-On line (R2 adoption).

## 1. The request and the example

### 1.1 What was asked

1. A dependency added to a `^prj` task should be stored as `depends_on` frontmatter on
   the project note, not as a `⛓️ **DEPENDS ON:**` sub-bullet.
2. Update the convert-task-to-project keymap so conversion carries dependencies
   correctly. The command is `bob-navigation-hotkeys:create-project-note-from-task`,
   bound in the vault's `.obsidian/hotkeys.json` to Alt+Ctrl+Shift+N; Bryan calls it
   `<cmd+ctrl+shift+n>`.
3. **Every task in a blocked project is Blocked**, whatever the reason the project is
   blocked.
4. `Ctrl+Shift+P` (Depends on) applies this immediately.
5. Blocked tasks have no Task Links. Remove existing ones, along with any Pomodoro left
   empty.
6. `bob task reconcile` enforces items 3 and 5 vault-wide and auto-fixes
   `job_apply_to_databricks.md`.
7. Update the glossary's "task dep link" term.

### 1.2 What actually happened in the vault (git history of `~/bob`)

| Commit | Event | Result |
| --- | --- | --- |
| `7d97d5ff` | Alt+Ctrl+Shift+N on `job.md`'s "Apply to DataBricks NYC role(s)!" | New project note. Its `^prj` is `[ ]`. The two `#ref` tasks moved in as `[*]`. Yesterday's Pomodoro links were rewritten to `job_apply_to_databricks#^…`. |
| `45a88e35` | Ctrl+Shift+P → `b` on `^prj`, target `[[job#^update-linkedin]]` | `^prj` → `[?]`, plus `[dependsOn:: job__update-linkedin]` and a `⛓️ **DEPENDS ON:**` child line. **Both members stay `[*]`.** |
| `9b9753f8` | Hooks status grouping | Members grouped under `### Next & In Progress`. The badge reads `🔵 2 next/wip · 🔴 0 blocked`. |

Today's daily note (`2026/20261012.md`) still has both member links in the open planned
`- [ ] () — JOB` Pomodoro. `job#^update-linkedin` itself is `[/]` and already linked
there.

Vault survey, read-only:

| Measure | Count |
| --- | --- |
| Project notes | 85 (34 `wip`, 45 `done`, 5 `canceled`, 1 without status) |
| `wip` sub-projects under a `wip` parent project | 29, mostly under `sase` |
| Depends-On lines in the vault | 50 |
| `^prj` tasks with a dependency | **1** (this example) |
| Depends-On links that target a `#^prj` | 0 |

The feature is new territory. There is no migration burden beyond this one note.

## 2. How the system works today (evidence)

| Fact | Where |
| --- | --- |
| Reconcile's Blocked rule is per-task only: an open `dependsOn` id or a future inline `scheduled`. Nothing about notes or projects. | `src/native/task_status_hooks/sync.rs:525-529` (`has_derived_block`), `task_transition` `:746-784` |
| Reconcile never identifies `^prj`. Project `scheduled` frontmatter is "ignored by this rule". | `task_status_hooks/mod.rs:107-108`; test `tests/cli/task_status_hooks/blocked.rs:128-156` |
| Project-wide blocking already exists for schedules, by **propagation**: `bob projects sync` and the Task Card copy `[scheduled:: P]` onto every ordinary open task. Hooks then treat it as a normal inline schedule. | `docs/projects.md:158-192`, `src/native/projects/sync.rs:518-573`, `edits.rs:101-163`; nav `250-task-move.js:611-850` |
| The Task Card already maps a `^prj` property to frontmatter, and only for `scheduled`. It writes with a plain text splice, in one editor transaction, then prunes deferred tasks from today's open Pomodoros. | nav `010-requires-and-config.js:251-256`, `250-task-move.js:774-793`, `570-plugin-link-roll-and-schedule.js:634-938`; `docs/projects.md:977-1033` |
| `kind: "project-frontmatter"` is hard-wired to mean `scheduled` throughout the picker. | nav `220-property-targets.js:42-48`, `450-picker-keydown.js:280-330, 396-435, 515-524` |
| The Depends on stage has no `^prj` special case. On `^prj` it writes a line and the field, and sets only `^prj` to `[?]`. It never prunes Pomodoros. | nav `080-dependency-identity.js:68-554`, `580-plugin-properties-and-dependency-edit.js:718-875` |
| Reconcile removes Pomodoro links only for duplicates and canceled targets. Nav prunes on future-schedule deferral and on cancel. **No path removes links to dependency-blocked tasks.** | `task_status_hooks/structure.rs:100-240`, `pomodoro.rs:282-322` |
| Linking a Blocked dependent is a **feature**: reconcile promotes its open prerequisites to Next. Capture's `@route+id!` raises Ready or Blocked to Next on link. | `docs/task-dependencies.md` §5; glossary `task-dependency-link`; `tests/cli/task_status_hooks/dependency_lines.rs:77-140`; `docs/capture.md:117`; `capture_task_toggle/task_update.rs:149-155` |
| Conversion refuses `[?]` sources ("Only open tasks…"). It turns a Depends-On child into a bogus `- [ ] #task ⛓️ **DEPENDS ON:** [[#^a]] …` task whose same-note links now point at the wrong note. `[dependsOn::]` / `[id::]` stay on `^prj`. | nav `010:85` (`PROJECT_OPEN_TASK_STATUSES = {" ", "/", "*"}`), `100-yank-and-paths.js:381-403`, `110-project-seed.js`; the bogus-task behavior was checked against the built helpers by a sub-agent |
| Reverse conversion keeps only `scheduled` and `created` from frontmatter, refuses `[?]`, and appends lifecycle children (including a Depends-On line) after the restored tasks. | nav `210-rename-and-line-context.js:766-867`, `660-plugin-project-notes.js:290-492` |
| `projects sync` inserts the `🧩 Sub-projects:` line directly after `^prj`. A Depends-On line under `^prj` is then no longer the first child. | `src/native/projects/edits.rs:483-495` |
| Capture rejects `&` prerequisites on a new project note. An explicit `@note+prj &dep` would write a line on `^prj`; there is no special case. | `capture_language/dependencies.rs:1018-1019` |
| `blocked.md`'s "DEPENDENT Tasks" section uses Tasks' `is blocked`, which reads the `dependsOn` graph. All sections filter out `#hide`. | `~/bob/blocked.md` |

## 3. Critique: is this a good idea?

### 3.1 Project-inherited Blocked: yes, and it is the heart of the request

A project is a container of next actions working toward one outcome. If the outcome
cannot start until X is done, none of its actions can either. The schedule precedent
shows Bryan already wants project-wide blocking: a future project `scheduled` blocks
every task. Dependencies are the missing second reason.

The rule is also cheap to evaluate. A task's project is the note it lives in, and that
note's `^prj` line and frontmatter are in the same file. Every writer (Rust and JS)
already holds the note text when it touches a task, so it can decide "is this task
project-blocked?" without a vault scan.

### 3.2 `depends_on` frontmatter: defensible, but only as a "relocated line"

For frontmatter:

- **Precedent.** Project-level properties already live in frontmatter: `scheduled`,
  `status`, `parent`, `project_name_aliases`. The Task Card already treats "`^prj`
  property = note property" for `scheduled`. A `^prj` dependency is a project property.
- **Queryability.** Dataview, Bases, and the Properties panel can list "projects waiting
  on X" without parsing the body.
- **Decluttering.** The `^prj` child area already holds the bob-managed Sub-projects
  line, the Schedule Log, and the Work Log. Sync's Sub-projects insert already pushes a
  Depends-On line out of first position.
- **Clean conversion.** A task's Depends-On line maps to a project's `depends_on`, and
  back.

Against, and why the condition matters:

- **A second dependency surface.** The `task-deps-are-depends-on-links` decision chose
  "one managed line" so that one grammar feeds the picker, the chips, R1–R10 healing,
  the successor links, and four synchronized parsers. Frontmatter adds a fifth reader in
  each engine.
- **Chips go away.** Chips render only from a body line. Properties shows plain,
  status-less links.
- **Every writer must route to it.** That includes capture's explicit `@note+prj &dep`.
  Otherwise the old form comes back.

The decision record's own rejection, "fields only with a virtual line … hand edits have
nowhere to land", does not apply: Properties is a real, hand-editable surface. So I
support frontmatter **if** it reuses everything:

- the same link forms (contract §3);
- the same reconciliation (R1 projects the `^prj` field from the frontmatter list, R2
  adopts into frontmatter rather than into a line, R3 heals, R9 empties);
- the same guards (self-dependency, cycles);
- the derived `[dependsOn::]` field kept on `^prj`.

Keeping that field matters. Tasks' `is blocked`, task-status-cycler's
`recoverBlockedDependents`, the successor-link gate, and Rust `task_dependency_states`
then keep working for `^prj` with no changes.

### 3.3 "Blocked tasks should not have Task Links": keep it, but redefine removal as consumption

Today a user can link a blocked dependent X under a Pomodoro to say "I want X today".
Reconcile then raises X's open prerequisites to Next. This is written into the glossary
("Linking the dependent under today's Pomodoros raises its open prerequisites to Next"),
contract §5, and test `task_status_hooks_promotes_prerequisite_through_depends_on_line`.
A rule that simply deletes links to blocked tasks would silently break it.

Removing those links before computing promotion would break it too.

The resolution is **consumption**. Within one reconcile run:

1. Seed promotion from every live link, including links to blocked tasks. Each blocked
   task's open prerequisites rise to Next as they do today, now including inherited
   project prerequisites.
2. Then remove the links whose target is Blocked **in this run's final state**.
3. Then delete Pomodoros left empty.

Because Next is sticky (`decisions:task-lanes-are-sticky`), the promotion survives the
removal. "Link a blocked task" becomes a one-shot planning gesture. Pomodoros end up
holding only actionable work, which is Bryan's intent. The pinned test changes only in
that the daily note now loses the `^dep` link.

The "final state" condition matters: a `[?]` task whose last blocker closed in the same
run keeps its link.

### 3.4 Costs the request does not mention

1. **Lane loss across a whole project.** Blocked overrides lanes and nothing stores the
   previous status. When the project unblocks, its Next and Pending tasks recover to
   Ready, and removing their links also removes the "directly recent" recovery to Next.
   With per-task deps this costs one task. With project deps it costs every member.
   `decisions:task-lanes-are-sticky` lists "Lanes must survive Blocked (then Blocked
   becomes an overlay)" as its reopen condition. The fix I recommend is in §6.6: when the
   last project prerequisite closes, successor-link the newly unblocked members back into
   the predecessor's slot, with the existing 5-link breaker. Bryan should decide whether
   that is enough or whether this reopens the decision.
2. **Mysterious `[?]`.** A member with no Depends-On line and no schedule is blocked "for
   no visible reason". The Depends on stage's BLOCKED badge, task-status-cycler's Alt+[
   hand-unblock (it would flip the task and the hooks would re-block it), the notices,
   and reconcile output all need a `project` reason.
3. **`blocked.md` gap.** Members carry no `dependsOn`, so `is blocked` is false. They have
   no schedule either, so they appear in no section. Add a "PROJECT" section that lists
   the blocked `^prj` rows (overriding `#hide`), not every member.
4. **Deadlocks.**
   - A `^prj` that depends on a task in its own note blocks that task forever: it is a
     member.
   - Project A waits on a task in project B while B waits on a task in A. Both stay
     blocked, and the cycle exists only through inheritance.
   - The picker must refuse same-note targets for `^prj`. R7 cycle detection must
     include inherited edges.
5. **Mirrors.** These immediate paths decide Blocked or recover from it without knowing
   about projects:
   - Rust: `task_complete/recovery.rs:51-134`, `task_complete/successors.rs:529-620`,
     `capture/dependencies.rs:2123-2127, 2303-2307, 2599`, the link-toggle `[?]`→`[*]`
     flip (`capture_task_toggle/task_update.rs:149-155`), and `randomize_plan.rs:399-475`.
   - task-status-cycler: `recoverBlockedDependents` (`080-dependencies.js:209-306`).
   - nav: dependency-removal recovery (`080:429-502`), and every
     `reconcileBlockedScheduledTaskLine` caller (`250:717-724`, `260:40-53, 527-585`,
     `580:188-195`). Making a project schedule due, or deleting it, **would unblock the
     tasks of a dependency-blocked project today**.
   - block-id-prompt: `planTargetTaskUpdate` forceNext (`070-daily-and-activation-plans.js:368-420`).

   Without mirrors these paths would cause flicker, which the next hooks run would fix.
   With mirrors, the 15-minute window stays truthful.
6. **Rollout hazard.** If nav starts writing `depends_on` before the MacBook's reconcile
   understands it, the old R2 rule sees "field present, no line" on `^prj` and **adopts a
   new Depends-On line**, recreating today's layout. bob-cli must ship and be installed
   first.

## 4. Requirement adjustments (explicitly called out)

| # | Requirement as stated | Adjusted to | Why |
| --- | --- | --- | --- |
| **ADJ-1** | "Blocked tasks should not have corresponding task links, so those should be removed" | **Consume, don't discard.** Reconcile promotes the open prerequisites (own plus inherited) of every blocked task linked under today's open Pomodoros, *then* removes those links. It uses the run's final Blocked state. Scope: today's open Pomodoros only; closed Pomodoros, struck links, and the previous daily note are untouched. Removal follows the existing deferral and cancel prune semantics: a link-only bullet is removed with its subtree, otherwise only the token. | Keeps the documented feature where linking a dependent promotes its prerequisites. It has precedent in the cancel and deferral prunes. |
| **ADJ-2** | "Any task that lives in a blocked project should also be blocked" | Inheritance is **derived at read time**. Project dependency ids are never copied into member fields. Members are the recognized open tasks in the project note other than `^prj`. Closed, custom-status, fenced, and blockquoted tasks are excluded. | Copied ids would collide with R1 (drop) and R2 (adopt), and would leak when a task is moved out. |
| **ADJ-3** | "Whenever a project is blocked" | Define it precisely: **a project is blocked exactly when its open `^prj` is Blocked `[?]`**. Reconcile derives that from (a) an open prerequisite in `depends_on`, and (b) **new:** a future project `scheduled`. Terminal projects, or projects with zero or several `^prj`, never block. | One local test that every engine can run on the note text. Item (b) also fixes an existing inconsistency: capture writes `[?]` on a future-scheduled `^prj` (`capture_project_note.rs:282`), but reconcile ignores project `scheduled` and would recover it. |
| **ADJ-4** | (unstated) sub-projects | **No cascade in v1.** A sub-project is its own note, and its tasks do not "live in" the parent. Show a `⛓️` marker on the parent's Sub-projects line for blocked children, like `🗓️`. | Same rule as `scheduled`, which does not cascade either. Blast radius: 29 open sub-projects sit under `wip` parents, and adding a dependency to `sase` would block most of the vault. Cascade is a one-line extension later if wanted. |
| **ADJ-5** | `depends_on` frontmatter | Make it **the `^prj` task's Depends-On line, moved into frontmatter**: same link forms, same R-rules, plus derived `[dependsOn::]` on `^prj` and `[id::]` on targets. Reader tolerance accepts a bare project link `[[other_project]]` and canonicalizes it to `[[other_project#^prj]]`. | One dependency model. Existing field consumers keep working. "Project waits on project" is natural to express. |
| **ADJ-6** | (unstated) internal targets | Refuse same-note targets for a `^prj` dependent in the picker. Reconcile warns `project_internal_dependency` and does not project the link. | Prevents the deadlock in §3.4 item 4. |
| **ADJ-7** | (unstated) `^prj` as a target | A `^prj` reached through a dependency edge is **never promoted to a lane**. Today nav raises it to Next or In Progress when the dependent is `*` or `/`. | `^prj` is a lifecycle row, not work. This matches the successor plan's "project tasks recover but never link". |
| **ADJ-8** | (unstated) other writers | Capture's explicit `@note+prj &dep` writes `depends_on`. Enabling `&` on new project-note captures is a follow-up and needs coordination with bob-mac-capture. Any hand-added Depends-On line under `^prj` is hoisted into frontmatter by reconcile, and by nav when the cursor leaves the line. | Otherwise other writers bring back the old layout. |
| **ADJ-9** | "Update the glossary term" | Also write a **new decision record**. It partly supersedes `decisions:task-deps-are-depends-on-links` (the `^prj` storage exception, and consumption replacing "linking raises prerequisites") and is cross-linked from `task-lanes-are-sticky` (lane-loss cost). Also update the glossary terms **Project Task**, **Project Note**, and **Task Link**. | Decision records are immutable and their rosters are rules to follow as written. Changing the behavior without a record would contradict them. |
| **ADJ-10** | (unstated) visibility | Add a reason `project` (naming the project and its open prerequisites) to reconcile output, the stage badge (`🔒 project waits on N`), and notices. Alt+[ on a project-blocked member refuses with a pointer to the project. Add a PROJECT section to `blocked.md`. | So a blocked member never looks unexplained. |

## 5. Options compared

| Option | Storage | Member blocking | Effort | Verdict |
| --- | --- | --- | --- | --- |
| **A. Line + inheritance** | Keep the `⛓️` line under `^prj` | Read-time inheritance + consumption | Lowest. Chips, picker, capture, and R1–R10 already work for `^prj` | Good fallback. It gives most of the value but ignores Bryan's storage requirement and keeps `^prj`'s child area crowded. |
| **B. Frontmatter as relocated line + inheritance** (recommended) | `depends_on:` list, derived `[dependsOn::]` on `^prj` | Read-time inheritance + consumption | A + roughly 30–40%: a frontmatter reader and writer in both engines, the hoist migration, a new picker descriptor, capture routing | **Recommended.** Matches the `scheduled` precedent and Bryan's requirement, with one model. |
| C. Copy ids into member fields (like `scheduled`) | Frontmatter | `[dependsOn::]` on every member | Medium | **Reject.** R1 strips the copies on nav hand edits; R2 adopts them into lines after cut/paste or move; every move path churns. |
| D. Blocked as overlay | Either | Members keep their lanes; views exclude them | High: every Tasks query, dash, lint, and plan count changes | **Reject for now.** It is the endgame if lane loss proves painful (§3.4 item 1). |
| E. Project `status: waiting` as the signal | Frontmatter `status` | Derived from status | Medium | **Reject.** Status is user-owned for active projects, and few consumers read it. It could later become a display projection. |

## 6. Recommended solution (option B)

### 6.1 Data model

```yaml
---
type: "[[project]]"
status: wip
depends_on:
  - "[[job#^update-linkedin]]"
  - "[[job_update_cv#^prj]]"
---
- [?] #task #prj Apply to DataBricks NYC role(s)! [created::2026-10-12] [dependsOn:: job__update-linkedin, job_update_cv__prj] #hide ^prj
```

- **Writer form:** a YAML block list of double-quoted wikilinks, the form Obsidian's
  Properties editor writes. Link forms follow contract §3, resolved from the project
  note's location: `[[basename#^id]]` when the basename is unique, otherwise the explicit
  path, and always the explicit path into `done/`. The same-note form never appears
  (ADJ-6). Order is preserved and new links are appended. An empty list deletes the key.
- **Reader tolerance:** flow lists (`[a, b]`), unquoted links, a single scalar, aliases
  and `!` (canonicalized away), and bare note links that resolve to a project note
  (→ `#^prj`). Reuse the flow/block list parser behind `project_name_aliases`
  (`src/native/projects/scan.rs:406-528`). Its warn-and-ignore handling of non-string
  entries is the model for R10 "malformed".
- **Derived:** `[dependsOn::]` on `^prj` (R1 order), and `[id::]` on targets, both as
  today. `^prj` derives `[?]` while any target is open.
- **Key name:** `depends_on`, snake_case like `project_name_aliases`, `task_count`, and
  `open_task_count`, and dot-free. The search results report that Obsidian skips
  rename-updating links in dotted property names; I did not test either case in this
  vault.

### 6.2 Blocked semantics (one rule, every engine)

```text
project(T)      = the project note T lives in, if it has exactly one valid ^prj and a
                  non-terminal status
project_blocked = ^prj is open AND (^prj has an open prerequisite OR project scheduled > anchor)
T is Blocked    = T has an open prerequisite                       (unchanged)
               OR T.scheduled > anchor                             (unchanged)
               OR (T is a member of a project and project_blocked) (new, T ≠ ^prj)
member          = a recognized open task (Todo/InProgress/OnHold) in the project note, other than ^prj,
                  outside fences and blockquotes; custom/unknown statuses untouched
edges(T)        = T's own Depends-On links ∪ (T is a member ? edges(^prj) : ∅)   — used for promotion,
                  recent-activity recovery rank, and R7 cycles
```

- **JS shortcut.** Immediate JS paths may test "this note's `^prj` line is `[?]`"
  instead of recomputing. It is a faithful stand-in because reconcile derives `^prj`'s
  `[?]` from the same inputs, and every writer that changes those inputs also updates
  `^prj` in the same transaction.
- **Recovery.** A member recovers only when every reason is gone, its own included, to
  the existing derived rank. No hidden previous status is stored.
- **`#ref` members.** Blocking them is status-neutral for highlights sync
  (`docs/task-status-hooks.md` §Derived Blocked), so it is safe.

### 6.3 `bob task reconcile`

**Pipeline change.** In `sync_task_statuses` (`task_status_hooks/sync.rs:192-693`), move
dependency reconciliation and Blocked inputs **before** the structural Pomodoro rewrite.
Blocked doesn't depend on Pomodoro links, so this is safe and needs no fixpoint loop.

1. Scan the vault and today's Pomodoros, as today.
2. **New R0 hoist.** For each active project's `^prj` that has a well-formed Depends-On
   line, merge its links into `depends_on` (append, dedupe by path and block id) and
   delete the line. A malformed line is left alone with a warning (R10). This is an
   explicit, documented exception to "hooks never move lines". It auto-fixes
   `job_apply_to_databricks.md`.
3. R1–R10 for every open task. For `^prj`, the source is the frontmatter list: R2 adopts
   into frontmatter, R3 heals the frontmatter link, R9 deletes the key. Add the
   `project_internal_dependency` warning, and extend R7 to inherited edges.
4. Compute `task_dependency_states` (`:701-744`) and the per-task reasons, including the
   new `project` reason. Build the final Blocked set now.
5. Dedupe, then the canceled-reference removal, then the **new blocked-reference
   consumption** (promotion seeds are recorded before removal), then completed
   retirement and markers, then empty-Pomodoro removal (`pomodoro.rs:282-322`). This
   means passing the Blocked set into `plan_structural_changes`; `task_complete` passes
   an empty set.
6. Desired ranks. Promotion roots = surviving links ∪ consumed blocked links (consumed
   roots seed only their prerequisites). The graph uses `edges(T)` from §6.2, and
   dependency edges never promote a `^prj` target (ADJ-7).
7. Transitions, grouping, guarded write, as today.

**Output.** Add a `project` reason on `marked_blocked` / `still_blocked` (project path
plus open ids), plus `hoisted_project_dependency_lines`,
`consumed_blocked_references` (`{path, line, task, reason, promoted}`), and the new
warning kinds. The second run must be a no-op.

**Option (B) from the code survey.** If moving R1–R10 earlier proves too invasive, a
second rewrite pass after step 7 also works, but the two empty-Pomodoro reports then need
merging (`pomodoro.rs:298` matches by entry index). I prefer reordering.

### 6.4 `Ctrl+Shift+P` → `b` on `^prj` (bob-navigation-hotkeys)

- **New descriptor.** Add `kind: "project-dependencies"` next to `scheduled` in
  `PROJECT_NOTE_PROPERTY_TARGETS`, and give the picker's project-frontmatter routes an
  explicit branch (they currently assume `scheduled`). CURRENT rows come from
  `depends_on`.
- **Entry points** match contract §6.1 (cursor on `^prj`, a Task Link to `^prj`, counted
  sessions that mix `^prj` with ordinary tasks). The palette command
  `edit-task-dependencies` also counts.
- **Guards:** refuse same-note targets ("a project can't wait on its own task — add the
  dependency to that task instead") and cycles that run through inherited edges.
- **One transaction in the project note:**
  1. Splice the frontmatter list; the precedent is `updateProjectScheduledFrontmatter`,
     `250:774-793`.
  2. Write `^prj`'s `[dependsOn::]` field.
  3. Set `^prj` to `[?]` and **every open member to `[?]`**.
  4. Fold any old `^prj` Depends-On line into the frontmatter (touching it migrates it).
  5. Stamp `[fresh::]` on `^prj`.
  - Cross-note target ids are prepared first, as today.
- **Prune.** Remove links to `^prj` and every member from today's open Pomodoros with
  `planDeferredPomodoroLinkCleanup` (`160:542-760`, generic `{path, blockId}` targets).
  Then **delete emptied Pomodoros**, which is new for nav: reuse `collectPomodoroEntries`
  and `removePomodoroBulletRanges`. A failure is reported as the existing "Pomodoro links
  not removed" chip and never rolled back.
- **Removal.** When no open prerequisite and no future schedule remain, `^prj` and every
  member without its own reason recover immediately.
- **Notice:** `⛓ Project now waits on "Change LinkedIn NOW!" · 2 tasks Blocked · removed 2 Pomodoro links`.
- **Mirrors.** Teach `reconcileBlockedScheduledTaskLine` callers and the
  dependency-removal recovery the §6.2 rule. These are the only nav paths that unblock in
  bulk.
- **Fragment size.** Modules 080/250/570/580/590 are each within ~150 lines of the
  AGENTS.md 1000-line fragment cap, so new code belongs in new fragments.

### 6.5 Convert task ↔ project (`create-project-note-from-task`)

**Forward** (task → project):

- Accept `[?]` sources.
- Convert the source's Depends-On line into `depends_on`. Same-note links become
  basename links to the source note, so `[[#^a]]` → `[[job#^a]]`. Never emit it as a
  `## Tasks` task; that fixes the bogus-task bug.
- The carried `[id::]` stays on `^prj`, so existing dependents, which are rewritten to
  `[[project#^prj]]`, keep matching.
- If the source had open prerequisites, `^prj` and all seeded tasks start as `[?]`. Do
  not expand today's Pomodoro link into per-member links for a blocked project; consume
  it instead.

**Reverse** (project → task):

- Accept a `[?]` `^prj`.
- Turn `depends_on` back into the restored task's **first-child** Depends-On line. Today
  lifecycle children are appended after the restored tasks.
- Re-form links relative to the destination: `[[job#^x]]` restored into `job.md` becomes
  `[[#^x]]`.
- Restored child tasks lose inherited blocking (they are subtasks now, not members). They
  recover through the normal rules, and the notice should say so.

### 6.6 Other engines

- **task-status-cycler** `recoverBlockedDependents`, and the Rust twins in
  `task_complete/recovery.rs` and capture closes: when a recovered dependent is a `^prj`,
  also recover its members that have no other reason. Do not unblock a member while its
  project is blocked.
- **Successor links (§12).** Rule 3 is today "`^prj` → recover, not linked". Extend it:
  the project's newly unblocked members become successor candidates and go through rules
  1–8, so `#hide`, already-planned, and the 5-link breaker still apply. This restores the
  plan the block consumed and mostly offsets the lane loss. Same rule in both engines,
  with new SL vectors.
- **block-id-prompt and capture link gestures** (`forceNext`, `@route+id!`, `:`) keep
  today's behavior in v1. The next reconcile consumes such a link after promoting its
  prerequisites. A follow-up could make these gestures **substitute** the open
  prerequisites at gesture time ("link X" → "link what X waits on") as one rule in two
  engines.
- **Capture `@note+prj &dep`** writes frontmatter (ADJ-8). The Mac capture preview gains
  a field naming the frontmatter destination; coordinate with `bob-mac-capture`.

### 6.7 Visibility

- Add a PROJECT section to `blocked.md`: the `#prj` rows with status `?`, ignoring
  `#hide`, grouped by path.
- `bob projects list`: add a `⛓ waits on N` column or chip. Add a `⛓️` marker on parents'
  Sub-projects lines (ADJ-4).
- Chips: v1 relies on Properties plus the stage's CURRENT rows. v2 renders a chip row
  under the `^prj` line from a Depends-On string built from frontmatter
  (`dependencyChipModel` is pure over line text). Its × and ＋ need frontmatter-aware nav
  api members (additive, `api.version` stays 3).

### 6.8 Expected auto-fix of the example

After `bob task reconcile` (dates assume 2026-10-12):

```markdown
---
parent: "[[job]]"
template: "[[new_project]]"
type: "[[project]]"
status: wip
created: 2026-10-12T06:26:32-04:00
task_count: 2
open_task_count: 2
depends_on:
  - "[[job#^update-linkedin]]"
---
- [?] #task #prj Apply to DataBricks NYC role(s)! [fresh:: 2026-10-12] [created::2026-10-12] #hide [dependsOn:: job__update-linkedin] ^prj

## Tasks
[`⚪ 0 open`](#Tasks) · [`🔵 0 next/wip`](#Tasks#Next%20&%20In%20Progress) · [`🔴 2 blocked`](#Tasks#Blocked) · [`🟢 0 done/canceled`](#Tasks#Done%20&%20Canceled)

### Next & In Progress
<!-- bob:task-status-group:v1:active -->

### Blocked
<!-- bob:task-status-group:v1:blocked -->

- [?] #task #ref [[ref/chat/databricks_nyc_cv_and_role_pitches|…]] … ^ref-databricks-nyc-cv-and-role-pitches
- [?] #task #ref [[ref/chat/databricks_nyc_cv_and_role_pitches_v2|…]] … ^ref-databricks-nyc-cv-and-role-pitches-v2

### Done & Canceled
<!-- bob:task-status-group:v1:closed -->
```

In today's daily note, the open `- [ ] () — JOB` Pomodoro loses its two
`job_apply_to_databricks#^ref-…` bullets. The Pomodoro still has other children, so it
stays. Consumption promotes `job#^update-linkedin`, which is already `[/]`, so nothing
else changes.

When "Change LinkedIn NOW!" is closed with Ctrl+Enter in its JOB slot:

- `^prj` recovers.
- Both ref tasks recover. Under §6.6 they are successor-linked back into that slot as
  Next.

### 6.9 Memory, docs, and contract

- **Contract.** Add a `docs/task-dependencies.md` §13 "Project dependencies" covering
  grammar, hoist, inheritance, consumption, and guards, with **PD vectors**:
  1. hoist a `^prj` line;
  2. frontmatter → field;
  3. field-only → adopt into frontmatter;
  4. empty list;
  5. internal target;
  6. members blocked;
  7. recovery;
  8. a member keeps its own reason;
  9. inheritance cycle;
  10. terminal project;
  11. sub-project not blocked;
  12. consume plus promote plus empty-Pomodoro delete;
  13. a link kept when the block clears this run;
  14. bare project link → `#^prj`;
  15. multiple `^prj`;
  16. future project schedule → `^prj` `[?]`.

  Rust, nav, task-status-cycler, and the ledger copy the tables they need, as with
  DP/DW/DR.
- **Docs to update:** `docs/task-status-hooks.md` (Derived Blocked, Empty Pomodoros,
  the new consumption section), `docs/projects.md` (Sync Rules, Task Card, conversion),
  and the reconcile `--help` text (`task_status_hooks/mod.rs:80-149`).
- **Memory, changed through `/sase_memory_write`.**
  - New record `decisions:project-deps-block-the-project`. Claim: "A project's
    prerequisites live in `depends_on` frontmatter; while its `^prj` is Blocked, every
    open task in the note is Blocked, and Task Links to Blocked tasks are consumed".
    Mark `task-deps-are-depends-on-links` as partly superseded, and cross-link
    `task-lanes-are-sticky`.
  - Proposed glossary text for **Task Dependency Link**:

    > A plain (never transcluded) [[task-link]] to a prerequisite of another Obsidian
    > task. An ordinary task's dep links sit on its Depends-On line, its first direct
    > child: `⛓️ **DEPENDS ON:** [[#^a]] • [[note#^b]]`. A [[project-task]]'s dep links
    > instead live in its [[project-note]]'s `depends_on` frontmatter list. Either one is
    > the source of truth: Bob derives the task's `[dependsOn::]` field and each target's
    > `[id::]` from it, and the task stays Blocked `[?]` while any target is open. While a
    > project's `^prj` task is Blocked, every open task in that note is Blocked too.
    > Blocked tasks never keep Task Links under today's open Pomodoros: `bob task
    > reconcile` raises their open prerequisites to Next, then removes the links and any
    > Pomodoro left empty. Add or remove dep links with Ctrl+Shift+P → Depends on, which
    > fuzzy-searches open tasks across the vault, or by editing the line or property. A
    > dep link is a prerequisite, not a sub-task: closing the dependent never closes its
    > targets, and dep links never count as Pomodoro Task Links. See
    > [[decisions/project-deps-block-the-project]] and
    > [[decisions/task-deps-are-depends-on-links]]; syntax lives in
    > `docs/task-dependencies.md`.

  - Add a sentence each to **Project Task** (holds `depends_on`; Blocked blocks the
    note), **Project Note**, and **Task Link** (consumed when the target is Blocked).

### 6.10 Phasing and rollout

| Phase | Repo | Content | Gate |
| --- | --- | --- | --- |
| P0 | bob-cli docs, memory | Contract §13, PD vectors, decision record, glossary | Bryan approves the open questions in §7 |
| P1 | bob-cli | Reconcile: frontmatter list I/O, R0 hoist, R1–R10 for `^prj`, inheritance, R7 extension, pipeline reorder, consumption, output | `--dry-run` on the live vault shows exactly the §6.8 diff; a second run is a no-op |
| P2 | bob-cli | Close and recovery paths (`recovery.rs`, `successors.rs`), capture `@note+prj &`, link-toggle mirror | SL and PD vectors pass |
| P3 | bob-plugins nav | Descriptor, stage on `^prj`, member blocking, prune plus empty-Pomodoro delete, schedule-path mirrors, conversion both ways | **Ships only after P1 is installed on the MacBook** (the R2 adoption hazard) |
| P4 | bob-plugins TSC, BIP, ledger + vault | Member recovery, successor expansion, badges, Alt+[ refusal, `blocked.md` PROJECT section | `bob plugins sync` |

## 7. Open questions for Bryan

1. **Consumption scope (ADJ-1).** Should it apply to every Blocked link (recommended,
   which keeps one invariant), or only project-blocked and future-scheduled links (which
   leaves today's "link a blocked dependent" behavior untouched)?
2. **Sub-project cascade (ADJ-4).** No cascade in v1 (recommended), or block a child
   project while its parent is blocked?
3. **Future project `scheduled` → `^prj` `[?]` (ADJ-3b).** Recommended yes.
4. **Lane loss (§3.4 item 1).** Is successor-relinking on unblock enough, or does
   project blocking reopen `task-lanes-are-sticky` toward a Blocked overlay?
5. **Link bullets with authored children** under an open Pomodoro. Follow the
   cancel/deferral precedent and remove the whole subtree (recommended, for parity), or
   keep the bullet and warn when it has child notes?

## 8. Incidental findings (pre-existing)

- **`^prj` status flip on scheduled captures.** `bob capture` writes `^prj` as `[?]` for a
  future-scheduled project (`capture_project_note.rs:282`). Reconcile ignores project
  `scheduled` (`task_status_hooks/mod.rs:107-108`), so the next run would recover it to
  `[ ]`. ADJ-3b fixes this.
- **Conversion bugs.** Converting a task with a Depends-On line creates a bogus
  `#task ⛓️ **DEPENDS ON:** …` task with broken same-note links. Conversion also refuses
  `[?]` sources (§6.5 fixes both).
- **`^prj` promoted by its dependents.** nav raises a `^prj` dependency target to Next or
  In Progress when its dependent is `*` or `/` (ADJ-7).
- **Sub-projects line displaces the Depends-On line.** `projects sync` inserts the
  Sub-projects line directly after `^prj`, so a Depends-On line there stops being the
  first child. Moving project deps to frontmatter (option B) removes the problem.

## Sources

- bob-cli: `docs/task-dependencies.md`, `docs/task-status-hooks.md`, `docs/projects.md`,
  `docs/plan.md`, and `src/native/{task_status_hooks,task_dependencies,projects,capture*,task_complete}`,
  as cited inline.
- bob-plugins (linked repo): `plugins/{bob-navigation-hotkeys,task-status-cycler,bob-ledger-tools,block-id-prompt}/src`,
  as cited inline.
- Memory: `glossary:{task-dependency-link,project-note,project-task,task-link,pomodoro}`,
  `decisions:{task-deps-are-depends-on-links,task-status-is-derived,task-lanes-are-sticky,today-is-read-from-the-ledger}`.
- Vault, read-only: `job_apply_to_databricks.md`, `job.md`, `2026/20261012.md`,
  `blocked.md`, `.obsidian/hotkeys.json`, and git commits `7d97d5ff`, `45a88e35`,
  `9b9753f8`.
- Obsidian frontmatter link rename behavior:
  [Property names with dots break link updating on note rename](https://forum.obsidian.md/t/property-names-with-dots-break-link-updating-on-note-rename/102860),
  [Automatic update of links to headers and blocks](https://forum.obsidian.md/t/automatic-inline-update-of-links-to-headers-and-blocks-when-they-are-modified-no-extra-dialog-window/25412/51).
