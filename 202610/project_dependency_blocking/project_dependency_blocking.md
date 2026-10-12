# Project dependencies: `depends_on` frontmatter, project-inherited Blocked, and blocked-link removal

> **Research query:** How should Bob give project (`#prj`) tasks full task-dep-link
> support: store a project's dependencies in a `depends_on` frontmatter field instead of
> a "Depends On" sub-bullet, block every task that lives in a blocked project, and
> remove blocked tasks' Task Links (plus any Pomodoro left empty)? This includes updating
> the Ctrl+Shift+P and Cmd+Ctrl+Shift+N keymaps, `bob task reconcile` (which should
> auto-fix notes like `job_apply_to_databricks.md`), and the "task dep links" glossary
> term. Is this plan a good idea, which requirements should change, and what
> implementation is recommended?

![Infographic summarizing the recommendation: a project blocked by an open prerequisite or a future project date blocks all its resident tasks; one dependency model with a depends_on frontmatter home for projects; consuming blocked links by promoting prerequisites, removing links, and deleting empty Pomodoros; scope boundaries; and the five-phase rollout](project_dependency_blocking_infographic.png)

## Bottom line

- **Build it. The core rule is right.** In GTD terms, a project that waits on
  something has no next actions. Its tasks should be Blocked `[?]` and out of today's
  Pomodoros. All five researchers agree. The
  [demonstrated bug](#the-example-and-vault-changes-since-the-swarm-ran) comes mostly
  from missing **inheritance**, not from where the dependency is stored. `^prj`
  correctly became `[?]`, but its two tasks stayed Next `[*]` and stayed linked in
  today's JOB Pomodoro, because nothing in bob-cli or the plugins knows that a project
  can be blocked.
- **`depends_on` frontmatter is the right home**, provided it is *the `^prj` task's
  Depends-On line moved into YAML*. That means the same link grammar, the same identity
  rules, and the same R-rule reconciliation, with a derived `[dependsOn::]` kept on
  `^prj` (see the [data model](#data-model)). That keeps one dependency model with two
  storage spots. It also follows the existing precedent: project `scheduled` already
  lives in frontmatter.
- **Derive inheritance when the vault is read. Never copy it.** The
  [effective Blocked rule](#one-effective-blocking-rule-in-every-engine) becomes: own
  open prerequisite, OR own future schedule, OR the task lives in a blocked project.
  Copying project ids into member fields would collide with R1 (drop) and R2 (adopt).
- **Removing links from Blocked tasks is right, with two consequences to choose on
  purpose:**
  1. It retires the documented "link a blocked dependent to promote its prerequisites"
     behavior. I recommend keeping that behavior's effect by treating removal as
     **consumption**: promote the prerequisites, then remove the link (see
     [D7 reasoning](#d7-reasoning)).
  2. Members of an unblocked project come back as Ready, not Next. The accepted
     sticky-lanes decision already says "lanes don't survive Blocked". That cost now
     covers a whole project at once (see [D8 reasoning](#d8-reasoning)).
- **The request undercounts the blast radius. Three gaps are confirmed:**
  - `blocked.md` would list inherited members as **STRANDED**, a section meant only for
    broken state ([Visibility](#visibility)).
  - About ten immediate code paths (recovery, successor links, schedule edits, capture
    link toggles) unblock tasks without knowing about projects
    ([Other writers and immediate paths](#other-writers-and-immediate-paths)).
  - The [project-conversion command](#converting-between-task-and-project) currently
    turns a Depends-On child into a fake task.
- **Ship order matters.** bob-cli must ship first
  ([rollout](#rollout-phases-and-acceptance)). An old reconcile that finds a
  frontmatter-only `^prj` (field present, no line) would adopt a new Depends-On line
  (R2) and recreate today's layout.

## What is actually broken

Everything in this section was verified.

### The example and vault changes since the swarm ran

`~/bob/job_apply_to_databricks.md` (frontmatter `parent: "[[job]]"`; `job.md` is an
**area**, so this example raises no sub-project question):

```markdown
- [?] #task #prj Apply to DataBricks NYC role(s)! … #hide [dependsOn:: job__update-linkedin] ^prj
	- ⛓️ **DEPENDS ON:** [[job#^update-linkedin]]
## Tasks
### Next & In Progress
- [*] #task #ref [[…databricks_nyc_cv_and_role_pitches|…]] … ^ref-databricks-nyc-cv-and-role-pitches
- [*] #task #ref [[…databricks_nyc_cv_and_role_pitches_v2|…]] … ^ref-databricks-nyc-cv-and-role-pitches-v2
```

Two changes since the swarm ran affect the acceptance checks. The reports did not see
either one.

| Vault commit | Change | Consequence |
| --- | --- | --- |
| `e6a48cce` 06:57 | Both Databricks links were removed **by hand** from the open `0645-0710 — JOB` Pomodoro | Bryan already enforces the "Blocked tasks have no links" rule manually. The live auto-fix no longer needs to remove links (see [rollout and acceptance](#rollout-phases-and-acceptance)) |
| `c48ecd09` 07:05 | "Change LinkedIn NOW!" now depends on `[[job_update_cv#^prj]]`, a **task waiting on a whole project** | The first task→`^prj` edge in the vault (cld counted zero earlier). The chain is Databricks → LinkedIn → Update CV project |
| `f5b85e20` 07:06 | The LinkedIn link was removed by hand from the same Pomodoro | The same manual rule again |
| (current state) | `job_update_cv.md`'s `^prj` is `[/]` In Progress | A dependent raised a lifecycle row into the PENDING lane. See [ADJ-11](#requirement-adjustments) |

### Code facts the design depends on

| Fact | Evidence |
| --- | --- |
| Blocked is decided per task, from an open `dependsOn` id or a future inline `scheduled`. Nothing about projects. | bob-cli `src/native/task_status_hooks/sync.rs:527-529`. The help text says project `scheduled` "is ignored by this rule" (`task_status_hooks/mod.rs:107`) |
| A `[?]` with no surviving reason recovers. A desired or recent-activity rank wins; otherwise the task goes to Ready. "Recent activity" includes the **previous daily's** links. | `sync.rs:455-476`, `task_transition` `:746-772` |
| Reconcile's order is: structural ledger cleanup → empty-Pomodoro removal → R1–R10 → ranks → Blocked. Nothing removes links to Blocked tasks, and removed roots "stop contributing" promotion in the same run. | `sync.rs:362-477`; `docs/task-status-hooks.md` §Empty Pomodoros, around line 222 |
| Empty-Pomodoro removal deletes **any** childless top-level entry, including a running timed one | `task_status_hooks/pomodoro.rs:282-305` |
| Successor and recovery logic finds dependents only through their `[dependsOn::]` field. A `^prj` dependent recovers but is never linked (rule 3). More than 5 successors in one gesture links none. | `docs/task-dependencies.md` §12.2 |
| A Depends-On line belongs in first-child position. `projects sync` inserts the machine-owned Sub-projects line directly after `^prj`. Readers tolerate a non-first position, but the two writers' position rules conflict. | `docs/task-dependencies.md` §2.1–2.2; `src/native/projects/edits.rs:483-495` |
| The capture link toggle flips `[?]`→`[*]`, which Sticky Lanes claim 1 allows. For a dependency-blocked task, the hooks block it again. | `src/native/capture_task_toggle/task_update.rs:150-153`; `decisions:task-lanes-are-sticky` |
| Capture writes `^prj` as `[?]` when a project is scheduled. Reconcile ignores project `scheduled` and will recover it. | `src/native/capture_project_note.rs:282` and the line above |
| Frontmatter helpers: `frontmatter_value` reads only same-line scalars. The `project_name_aliases` reader is quote-aware for flow and block lists and can be reused. | `src/native/projects/scan.rs:372`, `:406-528` (`split_flow_items` respects quotes) |
| nav: `kind: "project-frontmatter"` means `scheduled` at about 12 call sites. Conversion refuses `[?]` sources. The building blocks for the prune already exist. | bob-plugins `bob-navigation-hotkeys/src/010-requires-and-config.js:85,253`; `220`, `260`, `360`, `450` fragments; `160-pomodoro-reorder.js:542` (`planDeferredPomodoroLinkCleanup`); `150-pomodoro-capture.js:28` (`removePomodoroBulletRanges`); `140-scheduled-recovery.js:608` (`collectPomodoroEntries`) |
| Converting a task with a Depends-On child seeds a fake `- [ ] #task ⛓️ **DEPENDS ON:** …` row and reports the conversion as lossless | cdx reproduced this with the exported planners; grk and cld confirmed it from source (`110-project-seed.js`, `100-yank-and-paths.js`) |
| `blocked.md` puts `[?]` tasks that are neither `is blocked` nor future-scheduled in **STRANDED** ("Should be empty — if it is not, run `bob task-status-hooks`") | `~/bob/blocked.md` final section |
| Tasks 8.4.0 is installed, and `task.file.property()` / `hasProperty()` are available to query filters | `.obsidian/plugins/obsidian-tasks-plugin` |
| Hotkeys: `create-project-note-from-task` = **Alt+Ctrl+Shift+N** (Option on a Mac, not Cmd); `set-bullet-property` = Ctrl+Shift+P | `~/bob/.obsidian/hotkeys.json` |
| Project statuses in the vault: 34 `wip`, 45 `done`, 5 `canceled`, 0 `waiting` | vault census |

## Is this a good idea

**Yes. Inheritance is the heart of it; the storage move is the smaller half.**

- **Inheritance.** A project is an outcome container. If the outcome cannot start, none
  of its actions can. Bryan already relies on project-wide blocking for schedules: a
  future project `scheduled` blocks every member, through propagated `[scheduled::]`.
  Dependencies are the missing second reason. The rule is also cheap: a task's project
  is the note it lives in, so every engine can decide it from that one note's text.
- **Frontmatter storage.** Arguments for it:
  - it matches `scheduled`, `parent`, and `status`;
  - it frees the `^prj` child area, which is already contested by Sub-projects,
    Schedule/Cancel/Work Logs, and the first-child position rule;
  - Dataview, Bases, and Properties can query it;
  - it gives conversion a clean mapping (line ↔ property).

  The accepted decision rejected "fields only with a virtual line" because hand edits had
  nowhere to land. That objection does not apply: Properties is a real, editable surface.
  The real cost is a fifth reader and writer in each engine, and losing live chips unless
  they are re-hosted on the `^prj` line.
- **The cheaper alternative (cld's option A):** keep the line under `^prj` and add only
  inheritance and link removal. It delivers most of the value. It is the right
  fallback if the storage work slips. It fixes neither the Sub-projects position
  conflict nor the conversion mapping, and it does not meet Bryan's explicit storage
  requirement.
- **What I would not do:**
  - copy project dependencies onto member lines or fields;
  - make members depend on their own `^prj` (that means waiting for project
    *completion*, not for the project to be *unblocked*);
  - treat `status: waiting` as a blocking signal;
  - make Blocked an overlay in this change. It is the endgame if losing lanes hurts,
    but it changes policy for every Blocked reason.

## Requirement adjustments

Each adjustment to the request is explicitly called out below. The D-numbers refer to
[the resolved disagreements](#how-disagreements-between-the-reports-were-resolved).

| # | As requested | Adjusted to | Why |
| --- | --- | --- | --- |
| **ADJ-1** | `depends_on` frontmatter instead of the sub-bullet | A YAML block list of **quoted task block links**, in canonical form and in authored order (appended, never re-sorted), with the key omitted when empty. `^prj` keeps a **derived** `[dependsOn::]`. `^prj` never has a Depends-On child | One model, two storage spots. Existing field consumers keep working (D1, D2) |
| **ADJ-2** | "Whenever a project is blocked" | **Project blocked** = active (non-terminal) project with exactly one open `^prj`, AND (an open `depends_on` target OR `scheduled` later than the anchor date). The `^prj` row inherits these reasons too. `status: waiting` and a cached `[?]` are not reasons | One rule every engine can compute (D4, D5) |
| **ADJ-3** | "Any task that lives in a blocked project" | Every **recognized open task physically in the project note** except `^prj`: nested tasks and `#ref` tasks included; fenced, blockquoted, and custom-status lines excluded. **No cascade through `parent`** in v1 | Matches the glossary's residence meaning and the `scheduled` precedent (D6) |
| **ADJ-4** | (implicit) | Inheritance is **derived at read time**. Nothing is written onto members except the `[?]` checkbox | Copied fields would trigger R1/R2 and leak when a task moves out |
| **ADJ-5** | Remove Task Links of blocked tasks, plus empty Pomodoros | Applies to **every effectively Blocked task**, not only project members. Scope: live (unstruck) links under **today's open** Pomodoros only. Closed entries, `🍅` history, other days, and dependency links are untouched. A link-only bullet goes with its subtree; otherwise only the link is removed. Then the existing empty-Pomodoro pass runs, and that pass can delete a running timed entry | Same semantics as the existing cancel and defer removals. History is never rewritten |
| **ADJ-6** | (conflicts with a documented feature) | Removal is **consumption**: the link's open prerequisites (its own plus inherited ones) are promoted to Next first. The "final state" test applies: a link whose target's last blocker closes in the same run is kept | Keeps the feature's effect ([D7](#d7-reasoning)). Requires partly superseding two decision records ([Memory and docs](#memory-and-docs)) |
| **ADJ-7** | (unstated) | **Accept lane loss.** Members recover to Ready, or to Next when linked or recently active. No automatic re-linking in v1. Adding a project dependency moves the strongest member lane onto the prerequisites | Sticky-lanes policy; size-independent behavior ([D8](#d8-reasoning)) |
| **ADJ-8** | (unstated) | Refuse **same-note** targets for `^prj` in the picker. Hand-authored internal targets are ignored with a warning. R7 cycle detection includes the implicit member→project edge | Otherwise the project deadlocks (D10) |
| **ADJ-9** | Update the Cmd+Ctrl+Shift+N keymap | Update the **command** `create-project-note-from-task` (bound to Alt/Option+Ctrl+Shift+N) in **both** directions. Accept `[?]` sources and `[?]` `^prj` | Both directions currently lose or corrupt dependency data |
| **ADJ-10** | (unstated) | `blocked.md` gains a PROJECT section and STRANDED excludes it | Otherwise valid inherited blocks look like broken state (D9) |
| **ADJ-11** | (unstated) | Dependency promotion **never raises a `^prj` target** into a lane | A lifecycle row is not work. The vault already has `job_update_cv`'s `^prj` at `[/]` because of its dependent |
| **ADJ-12** | Update the glossary term | Also write a **new decision record** that partly supersedes `task-deps-are-depends-on-links` (storage exception, consumption) and `task-lanes-are-sticky` claim 1 (linking raises a *dependency- or project-blocked* task to Next). Update glossary **Project Task**. Use `/sase_memory_write` when implementing | Decision records are immutable rules. Changing behavior without one would contradict them |
| **ADJ-13** | (unstated) | **Rollout order:** install bob-cli (where the hooks run, the MacBook) before the plugins | Old R2 would add a Depends-On line back under a frontmatter-only `^prj` |

## How disagreements between the reports were resolved

| # | Topic | Positions | Resolution and why |
| --- | --- | --- | --- |
| D1 | What goes in the YAML list | Quoted wikilinks: cdx, cld, grk, gem. Dependency ids: mus | **Quoted task block links.** Same grammar as the line, so R3 healing works unchanged. Obsidian indexes property links (backlinks, rename updates, clickable in Properties). Ids are already derived on `^prj` |
| D2 | Keep `[dependsOn::]` on `^prj`? | Keep: cdx, cld, grk. Strip: gem, mus | **Keep it, as a derived projection.** §12.2 successor and recovery logic, `task_dependency_states`, and Tasks' `is blocked` all find dependents through the field. Stripping it would leave `^prj` unrecovered at close time until the next hooks run, and would need a new reader in every engine |
| D3 | A `^prj` with only a field, no line and no property | Adopt into YAML: cld, grk. A missing property means empty: cdx | **A missing property means empty for `^prj`; drop the field ids and warn.** Deleting the property in the Properties pane is a deliberate in-app gesture that nav cannot intercept, so re-adopting it would bring a deleted dependency back. The census found no field-only `^prj` cases. A *line* under `^prj` is still hoisted ([Task reconcile](#task-reconcile)) |
| D4 | What makes a project blocked | An open dependency or a future schedule: cdx, cld, grk, mus. gem adds `status: waiting/blocked` and "`^prj` is `[?]`" | **An open `depends_on` target, or a future project `scheduled`.** `status` is user-owned lifecycle data and no note uses `waiting`. A `^prj` `[?]` is an *output* of these reasons, not an input; treating it as an input would let a stale manual `[?]` block every member permanently |
| D5 | `^prj` itself under a future project schedule | `[?]`: cld, cdx. `#hide` only: grk | **`[?]` (plus the existing `#hide`).** This fixes the verified flip where capture writes `[?]` and reconcile recovers it |
| D6 | Blocking sub-projects through `parent` | No: cdx, cld, grk, gem. Transitive: mus | **No in v1. Residence only**, the same as `scheduled`, which also does not cascade. 29 `wip` sub-projects sit under `wip` parents, so one dependency on `sase` would freeze most of the vault. [Open question Q2](#open-questions-for-bryan) |
| D7 | Removing links vs the promote-on-link feature | Consume (promote, then remove): cld. Just remove: cdx, grk, mus | **Consume.** See [D7 reasoning](#d7-reasoning) below the table |
| D8 | Re-linking members when the project unblocks | Into the predecessor's slot: cld. Recover only: cdx, grk, mus, gem | **Recover only in v1.** See [D8 reasoning](#d8-reasoning) below the table. [Open question Q3](#open-questions-for-bryan) |
| D9 | `blocked.md` | Mislabeled as STRANDED: cdx. Invisible: cld, grk. No change needed: gem, mus | **cdx is right (verified).** Add a PROJECT section and exclude it from STRANDED ([Visibility](#visibility)). grk's fix, `(is blocked) OR status Blocked` in DEPENDENT, would break the page's "exactly one section" rule |
| D10 | A project that depends on its own member | Refuse; on hand edits, ignore and warn: cld. Refuse; keep as a cycle: cdx | **Refuse in the picker.** On a hand edit, keep the link in YAML, **do not project it**, and warn `project_internal_dependency`. By construction it is a guaranteed deadlock, reconcile runs unattended, and an ignored edge is better than a silent freeze. Longer cycles that pass through inherited edges follow R7 (keep and warn) |
| D11 | Counted Ctrl+Shift+P sessions that mix `^prj` with ordinary tasks | Refuse: grk, mus. Route each target: cld | **Refuse in v1** with a one-line notice. Mixed storage in one edit has unclear meaning |
| D12 | The keymap name | "cmd ≡ option": mus | **Wrong.** The binding is Alt/Option+Ctrl+Shift+N. Change the command's behavior; leave the binding alone |

### D7 reasoning

The glossary, the `task-deps-are-depends-on-links` decision, and the
test `task_status_hooks_promotes_prerequisite_through_depends_on_line` all promise that
linking a blocked dependent raises its prerequisites to Next. Linking expresses "I want X
today". Adding a dependency already turns that intent into sticky Next on the
prerequisites (`getDependencyPromotionStatus`). Consumption applies the same conversion
when a link is removed. The cost is one extra root set, recorded in the output. It
differs from canceled-link removal (whose roots correctly stop promoting): a canceled task
is no longer wanted, while a blocked one still is.

### D8 reasoning

- Membership is not an authored successor edge.
- The 5-link breaker makes the outcome depend on project size: a 6-task project gets
  none.
- §12.2 rule 3 already makes project rows recover-only.
- Moving lane commitment to the prerequisite when the dependency is added
  ([Editing project dependencies from the keymap](#editing-project-dependencies-from-the-keymap))
  is the mitigation.

## Recommended solution

### Data model

```yaml
---
type: "[[project]]"
status: wip
depends_on:
  - "[[job#^update-linkedin]]"
  - "[[job_update_cv#^prj]]"
---
- [?] #task #prj Apply to DataBricks NYC role(s)! … #hide [dependsOn:: job__update-linkedin, job_update_cv__prj] ^prj
```

- **Writer form:**
  - a block list of double-quoted plain links (no alias, embed, or strike);
  - the shortest unambiguous form per contract §3, with an explicit `done/` path for
    archive targets;
  - the same-note form never appears (ADJ-8);
  - new links are appended;
  - an empty list deletes the key.

  In Rust and JS, edit the YAML as a text splice limited to that key's span, without
  reformatting unrelated YAML. This follows the `updateProjectScheduledFrontmatter`
  precedent, so the edit stays inside one editor transaction. `processFrontMatter` would
  not.
- **Reader tolerance:** flow lists, one quoted scalar, aliased or `!` links
  (canonicalized away), and null or empty values (meaning none). A bare
  project link `[[other_project]]` canonicalizes to `[[other_project#^prj]]`.
  Malformed shapes or duplicate keys get a per-project warning; destructive
  migration is skipped; they never count as safely empty.
- **Derived values:** `[dependsOn::]` on `^prj`, in list order, and `[id::]` on
  targets, both as today.
- **The key name** stays snake_case, like `project_name_aliases` and `task_count`.

### One effective-blocking rule in every engine

```text
project(T)       = the project note T lives in (type project, non-terminal status,
                   exactly one open ^prj)
project_reasons  = { open depends_on targets } ∪ { scheduled > anchor }
T is Blocked     = T has an open prerequisite                 (unchanged)
                OR T.scheduled > anchor                       (unchanged)
                OR project(T) exists AND project_reasons ≠ ∅  (new; applies to ^prj too)
edges(T)         = T's own dep links ∪ (T is a member ? ^prj's depends_on : ∅)
                   -- used for promotion, recovery rank, and R7 cycle detection
```

- **Recovery:** a member recovers only when *every* reason is gone, its own included. It
  goes to the existing derived rank. No previous status is stored.
- **Reasons are reported, not stored.** Report `local_dependency`, `local_schedule`,
  `project_dependency`, and `project_schedule`, with the project path and the open target
  ids, in reconcile JSON and in nav/cycler notices.
- **JS shortcut:** an immediate JS path may treat "this note's `^prj` is `[?]`" as the
  project test. It is accurate because every bob writer that changes the inputs also
  updates `^prj` in the same transaction. Hand edits are fixed by the next reconcile.
- Reconcile reads project `scheduled` directly, so results do not depend on whether
  `bob projects sync` ran first. Sync still stamps member dates as today.

### Task reconcile

These are the changes to `bob task reconcile`.

**Pipeline.** Blocked does not depend on Pomodoro links, so compute it before cleaning up
the ledger. No fixpoint loop is needed.

1. Scan the vault, today's ledger, and the previous daily (as today).
2. **R0 hoist (migration).** For each valid project whose `^prj` has a well-formed
   Depends-On line:
   - merge its links into `depends_on` (dedupe by path and block id; property entries
     first, line entries appended);
   - delete the line.

   Special cases:
   - a property that disagrees with the line: union them and report both sources (in
     practice only the Databricks note exists);
   - a malformed line: leave it and warn (R10 parity).

   This is a documented exception to "hooks never move lines".
3. **`^prj` R-rules.** The property plays the role of the line:
   - R1 projects the field from it and stamps target `[id::]` values;
   - R3 heals within the property;
   - R4 keeps breadcrumbs;
   - R9 deletes the key;
   - the **R2 exception** applies: never adopt the field into a line or into the property
     (D3).

   Ordinary tasks, including those inside project notes (40 vault lines), keep R1–R10
   unchanged.
4. Compute dependency states, the project reasons, and the **final Blocked set**. This
   includes the `project_internal_dependency` warning and R7 with the implicit edge.
5. Plan the ledger structure in this order:
   1. dedupe;
   2. remove canceled links;
   3. **consume blocked links** (record their promotion seeds first, then remove them);
   4. retire completed links and repair markers;
   5. remove empty Pomodoros.

   Pass the Blocked set into `plan_structural_changes`; `task_complete` passes an empty
   set.
6. **Ranks.** The promotion roots are the surviving links plus the consumed seeds (which
   seed only their prerequisites). Edges come from `edges(T)`. A `^prj` target is never
   promoted (ADJ-11).
7. Then transitions, grouping (the new marker-free groups), and the guarded write, as
   today. Keep the existing guard against multiple open timed entries as it is.

If reordering R1–R10 ahead of the structural plan proves invasive, a second rewrite pass
after step 7 also works, but the two empty-Pomodoro reports must then be merged. Either
way, the requirements are the same: dry-run output equals the live write, and a second
run changes nothing.

**Output (additive):** `hoisted_project_dependency_lines`, `project_dependency_updates`,
`consumed_blocked_references` (`{path, line, task, reason, promoted[]}`), the new reason
kinds on `marked_blocked`/`still_blocked`, and the new warning kinds. Update the
`--help` text in `task_status_hooks/mod.rs`.

### Editing project dependencies from the keymap

Ctrl+Shift+P → `b` on `^prj`, in bob-navigation-hotkeys.

- **New target descriptor** `kind: "project-dependencies"` beside `scheduled`. Add an
  explicit branch at every route that currently assumes `project-frontmatter` means
  `scheduled`. CURRENT rows read `depends_on`, overlaid with the open buffer.
- **Entry points:**
  - the cursor on `^prj`;
  - a Task Link to `^prj`;
  - a leftover Depends-On line under `^prj` (it edits the property; the line is folded in
    on commit);
  - the `edit-task-dependencies` palette command.

  Refuse mixed counted sessions (D11) and same-note targets (ADJ-8). The cycle guard
  includes implicit edges.
- **One editor transaction in the project note:**
  1. splice the property;
  2. write the `^prj` field;
  3. set `^prj` and **every open member** to `[?]`;
  4. fold in any old line;
  5. stamp `[fresh::]`;
  6. regroup `## Tasks`.

  Cross-note target `[id::]` preparation happens first, as today.
- **Commitment transfer:** raise each open target to at least the strongest lane among
  `^prj` and the members, which extends `getDependencyPromotionStatus`. Never raise a
  `^prj` target (ADJ-11). This mitigates lane loss.
- **Removing links from today's ledger:** run `planDeferredPomodoroLinkCleanup` over
  `^prj` and the members, then **delete Pomodoros left empty**. That deletion is new for
  nav: compose `collectPomodoroEntries` with `removePomodoroBulletRanges`. A failure
  reports the existing "Pomodoro links not removed" chip and is not rolled back;
  reconcile repairs it.
- **Removal:** when the last reason clears, recover `^prj` and every member that has no
  reason of its own. Ctrl+D on the property row clears the key, mirroring
  `deleteProjectNoteScheduledValue`.
- **Notice:** `⛓ Project waits on "Change LinkedIn NOW!" · 2 tasks Blocked · removed 2
  Pomodoro links`.
- New code goes in new fragments, because the 080/250/570/580/590 fragments are near the
  1000-line cap. Edit fragment sources and regenerate `main.js`.

### Converting between task and project

This covers the `create-project-note-from-task` command, bound to Alt+Ctrl+Shift+N.

- **Forward:**
  1. Accept `[?]` sources.
  2. Extract the source's Depends-On line, plus R8 legacy children, into `depends_on`.
     Rebase same-note links to the source note: `[[#^a]]` → `[[job#^a]]`.
  3. Never seed that line as a `## Tasks` row. This fixes the fake-task bug.
  4. Strip `[dependsOn::]` from the description; it is re-derived.
  5. **Keep `[id::]` on `^prj`.** Existing dependents are rewritten to
     `[[project#^prj]]` and still match.
  6. If the source had open prerequisites, start `^prj` and the seeded members as `[?]`,
     and do not expand today's link into per-member links.
  7. Refuse, or drop with a notice, any prerequisite that becomes a member (ADJ-8).
- **Reverse:**
  1. Accept a `[?]` `^prj`.
  2. Turn `depends_on` into a **first-child** Depends-On line on the restored task, with
     links re-formed relative to the destination (`[[job#^x]]` → `[[#^x]]` when restored
     into `job.md`).
  3. Skip the machine-owned `🧩 **Sub-projects:**` child, which is copied today
     (pre-existing bug).
  4. Restored subtasks lose inherited blocking and recover by the normal rules. The
     notice says so.
- Leave the hotkey binding as it is.

### Other writers and immediate paths

Without these changes, the 15-minute hooks window shows flicker: tasks unblock wrongly
until the next run re-blocks them. Paths are from cld and cdx, and the files were
spot-checked:

- **bob-cli:**
  - `task_complete/recovery.rs` and `task_complete/successors.rs`: when a recovered
    dependent is a `^prj`, also recover its members that have no other reason. Never
    unblock a member while its project is blocked. The successor rule-3 analog for
    members is recover-only.
  - The capture link toggle (`capture_task_toggle/task_update.rs`): keep the schedule
    pull-forward, which removes a reason. For dependency- or project-blocked targets,
    apply consumption at gesture time: do not link; raise the open prerequisites to Next;
    report it.
  - Capture of a new task into a blocked project lands `[?]` and unlinked.
  - Capture `&` aimed at an existing `^prj` writes the property.
  - `randomize_plan.rs`: respect the project reason.
- **task-status-cycler:**
  - `recoverBlockedDependents` gets the same member recovery.
  - Alt+[ on a project-blocked member refuses, with a pointer to the project.
- **nav:**
  - Teach the dependency-removal recovery and every `reconcileBlockedScheduledTaskLine`
    caller (schedule due or deleted) the project rule. Otherwise making a project
    schedule due would unblock the members of a dependency-blocked project.
  - Ctrl+Shift+M **into** a blocked project blocks the task and removes its links in the
    move transaction.
- **block-id-prompt:** apply the same gesture-time consumption on `forceNext` link
  creation to a dependency- or project-blocked target.
- **Bob Mac Capture:** nothing, unless a new response field needs display. It is a thin
  client (`decisions:mac-capture-is-a-thin-client`).

### Visibility

- **`blocked.md`:** add a section before STRANDED:

  ```tasks
  is not blocked
  status.name includes Blocked
  NOT (scheduled after today)
  filter by function (task.file.property('depends_on') ?? []).length > 0 || (task.file.property('scheduled') && moment(task.file.property('scheduled')).isAfter(moment(), 'day'))
  group by path
  ```

  - Add the negated filter to STRANDED.
  - Update the page's intro, which lists only dependency and schedule reasons.
  - `^prj` stays filtered out by `#hide`. Members show up grouped under the project's
    path.
  - The query approximates "blocked project"; reconcile output stays the authority.
- **Chips:** v1 relies on the Properties pane plus the stage's CURRENT rows. v2 renders
  chips on the `^prj` line from YAML. `dependencyChipModel` is pure, but ×/＋ need
  frontmatter-aware api members; `api.version` stays 3.
- **Optional:** a `⛓️` marker for dependency-blocked children on a parent's Sub-projects
  line (the `🗓️` analog), and a `waits on N` column in `bob projects list`.

### Memory and docs

- **Contract:** a new `docs/task-dependencies.md` §13 "Project dependencies" with
  grammar, R0, the `^prj` R-rules, inheritance, consumption, guards, and **PD vectors**.
  Rust, nav, cycler, and ledger-tools copy the tables they need, as with DP/DW/DR. The
  vectors:

  | Group | Vectors |
  | --- | --- |
  | Migration and projection | hoist; property → field; field-only dropped; empty key |
  | Guards | internal target ignored; inherited cycle |
  | Blocking | members blocked; recovery needs every reason gone; terminal project; sub-project not blocked; bare project link → `#^prj`; multiple `^prj`; future project schedule → `^prj` `[?]` |
  | Ledger | consumption with promotion and empty-Pomodoro delete; link kept when the block clears in the same run |

  Also update `docs/task-status-hooks.md` (Derived Blocked, Empty Pomodoros, the new
  consumption section) and `docs/projects.md` (property table, Task Card, conversion,
  and the `dependsOn`-is-not-a-project-property sentence).
- **New decision record** (through `/sase_memory_write`), for example
  `project-deps-block-resident-tasks`. Claim:

  > "A project's prerequisites live in its note's `depends_on` property; while the
  > project has an open prerequisite or a future schedule, every open task in its note
  > is Blocked; links to Blocked tasks under today's open Pomodoros are consumed."

  It partly supersedes `task-deps-are-depends-on-links` (the `^prj` storage exception;
  consumption replaces "linking the dependent raises its prerequisites") and Sticky
  Lanes claim 1 for dependency- or project-blocked tasks. It also cross-links the
  Sticky Lanes cost "lanes don't survive Blocked", which is now project-wide.
- **Glossary `task-dependency-link`** (the requested update), proposed text:

  > A plain (never transcluded) [[task-link]] to a prerequisite of another Obsidian task.
  > An ordinary task's dep links sit on its Depends-On line, its first direct child:
  > `⛓️ **DEPENDS ON:** [[#^a]] • [[note#^b]]`. A [[project-task]]'s dep links instead
  > live in its [[project-note]]'s `depends_on` property, a list of quoted links; `^prj`
  > never gets a Depends-On line. That line or property is the source of truth: Bob
  > derives the task's `[dependsOn::]` field and each target's `[id::]` from it, and the
  > task stays Blocked `[?]` while any target is open. While a project has an open
  > prerequisite or a future `scheduled` date, every open task in its note is Blocked
  > too. Blocked tasks keep no Task Links under today's open Pomodoros: linking one
  > raises its open prerequisites to Next instead, and `bob task reconcile` removes such
  > links and any Pomodoro left empty. Add or remove dep links with Ctrl+Shift+P →
  > Depends on (on `^prj` it edits the property) or by editing the line or property. A
  > dep link is a prerequisite, not a sub-task: closing the dependent never closes its
  > targets, and dep links never count as Pomodoro Task Links. See
  > [[decisions/project-deps-block-resident-tasks]] and
  > [[decisions/task-deps-are-depends-on-links]]; syntax lives in
  > `docs/task-dependencies.md`.

- Add one sentence to **Project Task** (it owns `depends_on`; while it is blocked, the
  note's tasks are blocked). Optionally add one to **Task Link** (consumed when its
  target is Blocked).

### Rollout phases and acceptance

| Phase | Repo | Content | Gate |
| --- | --- | --- | --- |
| P0 | bob-cli docs and memory | §13 contract, PD vectors, decision record, glossary | Bryan answers the [open questions](#open-questions-for-bryan) |
| P1 | bob-cli | Frontmatter I/O, R0 hoist, `^prj` R-rules with the R2 exception, effective-blocking reasons (including project `scheduled`), internal-target warning and inherited R7, blocked-link consumption, `^prj` never promoted, outputs | `--dry-run` on the live vault matches the expected diff below. A second run changes nothing. **Install on the MacBook (the hooks host) before P3** |
| P2 | bob-cli | Close and recovery paths, capture link toggle consumption, capture into a blocked project, capture `&` on `^prj` | SL and PD vectors pass |
| P3 | bob-plugins (nav, cycler, block-id-prompt) | Descriptor and stage on `^prj`, member blocking, link removal plus empty-Pomodoro delete, schedule-path mirrors, conversion both ways, member recovery, Alt+[ refusal, Ctrl+Shift+M | `npm test` / `npm run validate`, then `bob plugins sync` |
| P4 | ledger-tools and vault | `blocked.md` PROJECT section, optional chips from YAML, optional Sub-projects marker | Visual check |

P1 alone fixes the reported bug vault-wide. Its "15-minute window" is the same one that
exists today, and the editor-side changes close it.

**Expected live auto-fix after P1 (current vault):**

- `job_apply_to_databricks.md`:
  - gains `depends_on: ["[[job#^update-linkedin]]"]` (written as a block list);
  - loses the Depends-On child;
  - keeps `[dependsOn:: job__update-linkedin]` on `^prj`, which stays `[?]`;
  - both `#ref` tasks go from `[*]` to `[?]` and move to `### Blocked`, and the badge
    updates.
- **No ledger change:** Bryan already removed the links by hand.
- `job.md`'s LinkedIn task stays `[?]` because of its own dependency on
  `job_update_cv#^prj`.
- `job_update_cv`'s `^prj` stays `[/]` (sticky). ADJ-11 only stops future promotions;
  releasing the existing one is Bryan's Alt+N.

**Fixture to test with:** use the pre-06:57 state, with both Databricks links in the
open timed JOB entry. Expect:
- exactly those two links consumed;
- LinkedIn (the prerequisite) promoted, and already `[/]`;
- the JOB entry kept, because other children remain;
- a second fixture where the blocked link is the last child, so the entry is deleted;
- closed entries byte-identical.

**Other checks:**
- Convert a sequenced task to a project and back: YAML appears; no fake row; the
  restored line is re-formed relative to the destination.
- Ctrl+Shift+P removal recovers members to Ready and removes the key.
- An old-format line under `^prj` is hoisted, not duplicated.
- Deleting the property in the Properties pane is honored (D3).

## Open questions for Bryan

Each question has a recommendation.

1. **Consumption (ADJ-6).** Should linking a blocked task, or a stale link to one, raise
   its prerequisites to Next before the link goes away? **Recommended: yes.** The
   alternative is to drop that behavior and rely on adding dependencies to transfer
   commitment. See [D7 reasoning](#d7-reasoning).
2. **Sub-project cascade (ADJ-3).** **Recommended: no in v1.** If you want it later, it is
   one extra reason, "parent project blocked", using a cycle-safe walk.
3. **Lane loss (ADJ-7).** Is "members recover to Ready" acceptable, or should closing the
   last project prerequisite link the members back into its slot (cld's proposal; the
   5-link breaker applies)? **Recommended: Ready in v1.** Revisit, or reopen Sticky Lanes
   toward a Blocked overlay, if re-pulling Databricks-style tasks feels wrong in the
   first week. See [D8 reasoning](#d8-reasoning).
4. **Planned link bullets with authored child notes** under an open Pomodoro.
   **Recommended:** remove the whole subtree, matching cancel and defer, and document it.
   The alternative is to move the children into the task's Work Log first.
5. **Future project schedule makes `^prj` `[?]` (ADJ-2).** **Recommended: yes.** It
   matches what capture already writes.

## Incidental pre-existing findings

- Capture writes `[?]` on a scheduled `^prj`, and reconcile recovers it, because it
  ignores project `scheduled`. Fixed by ADJ-2.
- Dependency promotion raises `^prj` targets into lanes. Live example: `job_update_cv`'s
  `^prj` is `[/]`. Fixed by ADJ-11.
- Conversion turns a Depends-On child into a fake task and keeps `[dependsOn::]` in the
  `^prj` description. It refuses `[?]` sources. Reverse conversion copies the
  machine-owned Sub-projects line.
- `projects sync` inserts Sub-projects directly after `^prj`, which conflicts with the
  Depends-On writer's first-child position. Moving project dependencies to frontmatter
  removes this conflict.
- `blocked.md` STRANDED still names the legacy `bob task-status-hooks` command.

## Scope and snapshots

_Lead researcher consolidation · 2026-10-12 · merges the five swarm reports `__cdx`, `__cld`,
`__grk`, `__mus`, `__gem` in this directory, plus my own verification_

Snapshots: bob-cli `2eb2581` (the swarm used `a55a22e`; the only commit between them
is the marker-free task-status-groups change), bob-plugins `4193a19`, and the Bob
vault as of `f5b85e20` (07:06 today). Research only. No code, vault note, keymap, or
memory file was changed.

## Sources

- **Swarm reports** (this directory): `__cdx` (pipeline-order analysis, STRANDED finding,
  migration table, a probe reproducing the conversion bug); `__cld` (git history of the
  example, census, consumption, list of code paths that need the project rule, PD
  vectors); `__grk` (`scheduled` analog, Sub-projects slot conflict, commitment transfer,
  census); `__mus` (minority positions on ids and transitivity, rejected here); `__gem`
  (prune boundary, walkthrough, `status: waiting` position, rejected here).
- **bob-cli `2eb2581`:**
  - docs: `docs/task-dependencies.md` §§2, 4, 5, 12; `docs/task-status-hooks.md` (Empty
    Pomodoros, Derived Blocked); `docs/projects.md` (sync rules, schedule propagation,
    Sub-projects); `docs/capture.md`;
  - `task_status_hooks/`: `sync.rs`, `pomodoro.rs`, `mod.rs`;
  - `projects/`: `scan.rs`, `edits.rs`;
  - `capture_project_note.rs`, `capture_task_toggle/task_update.rs`,
    `capture_language/dependencies.rs`;
  - `tests/cli/task_status_hooks/dependency_lines.rs:78`.
- **bob-plugins `4193a19`:** `bob-navigation-hotkeys/src/` fragments 010, 100, 110, 140,
  150, 160, 220, 260, 360, 450.
- **Vault (read-only):** `job_apply_to_databricks.md`, `job.md`, `job_update_cv.md`,
  `2026/20261012.md` and its commits `e6a48cce` / `f5b85e20`, `blocked.md`,
  `.obsidian/hotkeys.json`, and the Tasks plugin manifest (8.4.0).
- **Memory (audited reads):** `glossary:task-dependency-link`, `glossary:project-task`,
  `decisions:task-deps-are-depends-on-links`, `decisions:task-lanes-are-sticky`.
- **External:** [Obsidian Properties](https://obsidian.md/help/properties) (quoted links
  in list properties) and [Tasks query filters](https://publish.obsidian.md/tasks/Queries/Filters),
  both as cited by cdx.
