# Project task dependencies: frontmatter, inherited blocking, and agenda repair

Researcher: **cdx**. Independent investigation for the five-researcher swarm. No peer report, transcript, summary, or findings were consulted.

Scope: implementation research and critique; no application code, vault note, keymap configuration, or canonical memory was changed.

Source snapshots: bob-cli `a55a22e83b0361ea90795dc22f1148b4f9152066`; bob-plugins `4193a190c7eaa94a17156beb9488347859dfa0f7`. Live vault examples were inspected read-only. Behavioral probes used installed `bob 0.1.0`, plus the linked plugin checkout's exported JavaScript planners. The installed binary's exact source revision was not established; the relevant behaviors were also checked against the source snapshot.

## Assessment

**The proposal is a good fit if a project dependency means “work on this entire project cannot proceed yet.”** Project properties already hold project schedules; putting project prerequisites there makes the authoring model consistent. Inheriting the project's blocking reasons addresses the demonstrated bug: the project outcome is Blocked while its work remains on today's agenda.

The important qualification is that a prerequisite for *finishing* a project is not necessarily a prerequisite for *starting every task* in it. For example, applying may require a finished LinkedIn profile, while editing application pitches could still be useful beforehand. The proposed rule intentionally forbids that parallel preparation. I would adopt the rule as requested, make that meaning clear in the picker, and put independent preparatory work outside the gated project. I would not introduce a per-task escape hatch in this change: it would weaken a simple invariant and create another inheritance policy to maintain.

The change is broader than relocating a bullet. It affects dependency parsing and projection, project/task conversion, effective blocking, ledger cleanup, immediate recovery, link creation, and blocked-task views. A correct implementation should share one effective-blocking contract across these consumers.

## What the current implementation does

### The supplied example demonstrates both missing inheritance and stale agenda links

`~/bob/job_apply_to_databricks.md` has:

```markdown
- [?] #task #prj Apply to DataBricks NYC role(s)! ... [dependsOn:: job__update-linkedin] ^prj
    - ⛓️ **DEPENDS ON:** [[job#^update-linkedin]]
```

Its two ordinary `#task #ref` rows are still `[*]`. Both also have live Task Links beneath an open JOB Pomodoro in `2026/20261012.md`. That Pomodoro contains three other Task Links, including the LinkedIn prerequisite itself.

Expected repair: migrate the project dependency into frontmatter, block both resident tasks, remove their two live agenda links, and update the task groups/badges. Keep the JOB Pomodoro because other children remain. Keep the LinkedIn prerequisite's link. Preserve `status: wip`, task identities, and project lifecycle `#hide` behavior. The example does not call for marking the project done, canceling it, or removing reference notes.

### The current dependency model has no project-frontmatter branch

`docs/task-dependencies.md` and the audited `decisions:task-deps-are-depends-on-links` record make a managed first-child Depends-On line authoritative. Reconciliation derives `[dependsOn::]` on the dependent and `[id::]` on prerequisites. This applies to an open `^prj` task just as it does to an ordinary task.

In `src/native/task_status_hooks/sync.rs`, `task_dependency_states` resolves inline dependency IDs. The main status loop combines those open targets with an inline future schedule. It has no project-blocking reason. Project `scheduled:` participates indirectly through prior `bob projects sync` propagation; the lifecycle task itself is excluded from that propagation.

The existing project frontmatter helper, `src/native/projects/scan.rs:372` (`frontmatter_value`), retrieves one property's same-line scalar. Reading `depends_on` by reusing that function alone will not correctly handle a block YAML list. The new field needs a real list-aware reader and a writer that can replace the entire property's span without rewriting unrelated YAML.

### Ctrl+Shift+P writes the ordinary task representation even for `^prj`

In bob-plugins, `plugins/bob-navigation-hotkeys/src/080-dependency-identity.js:68` (`planDependencyEdit`) is the common pure planner. It writes the inline field, a managed child line, target identity changes, and immediate dependent blocking. It does not switch storage based on project lifecycle identity, or block other tasks in that note.

The runtime entry points include the dependency stage, local writer, counted/batch writer, linked-task mode, API/chip removal, and the hand-edit mirror. Updating only one callback would leave other entry points writing the old representation.

### Conversion can manufacture a task out of dependency metadata

`buildProjectSeedFromChildBullets` in `plugins/bob-navigation-hotkeys/src/110-project-seed.js` recognizes managed logs and section bullets, but has no dependency-metadata extraction branch. A focused invocation with the example dependency child produced:

```markdown
- [ ] #task ⛓️ **DEPENDS ON:** [[job#^update-linkedin]] [created::2026-10-12]
```

It reported the conversion as lossless. This is an actual metadata-to-task conversion bug, not merely a display concern.

Forward conversion also strips schedule/priority from the source description but does not explicitly extract its dependency projection (`100-yank-and-paths.js`). Reverse conversion builds the restored task from project schedule/created metadata and lifecycle children, without handling a project dependency property (`210-rename-and-line-context.js:766`). Both directions need explicit dependency handling.

The command ID is `bob-navigation-hotkeys:create-project-note-from-task`. On the inspected machine it is bound to **Alt+Ctrl+Shift+N**, whereas the request says **Cmd+Ctrl+Shift+N**; plugin registration itself supplies no default shortcut. Implement the command behavior, and confirm the Mac binding during acceptance testing rather than silently changing this machine's binding.

### Ledger cleanup currently precedes blocking

`src/native/task_status_hooks/sync.rs:353–419` plans duplicate/canceled/completed-reference cleanup, removes empty Pomodoros, reparses the resulting daily note, and then reconciles dependencies. It subsequently calculates desired lane ranks and derives Blocked status. There is no blocked-link removal pass.

Therefore, appending project inheritance to the existing final checkbox loop cannot satisfy the agenda invariant in the same run. A soon-to-be-Blocked task can still contribute a ledger root and promote prerequisites, even if a later edit removes its link.

### Existing cleanup and recovery machinery is reusable, but incomplete for this change

Navigation's `planDeferredPomodoroLinkCleanup`, in `160-pomodoro-reorder.js:542`, already removes dedicated link bullets with their subtree and removes only matching tokens from mixed-content bullets. It preserves struck history and targets only open Pomodoros. It does **not** itself delete the newly empty Pomodoro; that composition step needs to be added/reused explicitly.

CLI reconciliation already has empty-Pomodoro cleanup, guarded input snapshots, scan-membership checks, maintenance locking, recovery manifests, retries, and final task grouping. Reuse these. Guarded multi-file replacement is not an atomic filesystem transaction: its apply implementation can report partial completion. Preserve the existing recovery behavior and make reruns converge.

Immediate recovery is narrower than full reconciliation. Rust `src/native/task_complete/recovery.rs` and the JavaScript scheduled-recovery/successor planners test direct dependency IDs and schedules. Without an inherited-project guard, closing a task's own prerequisite can wrongly recover it while its project is still blocked. Conversely, closing a project prerequisite would recover the `^prj` projection but miss resident tasks whose blocking reason is inherited.

### A checkbox-only solution would break the blocked view's explanation

The inspected `~/bob/blocked.md` uses native `is blocked` for dependencies and labels `[?]` tasks without native dependency/schedule reasons as STRANDED. Inherited tasks with no local dependency field would land there even though their blocking is valid. Its introduction also lists only local dependency and schedule reasons.

Tasks' native dependency query examines direct `id`/`dependsOn` relationships between open status types; it does not derive Bob's project containment semantics. An `ON_HOLD` checkbox by itself does not create that relationship. [Tasks' official filter documentation](https://publish.obsidian.md/tasks/Queries/Filters).

## Focused behavior checks

Four tiny fixture vaults were created temporarily inside this checkout's Git metadata directory, tested with `bob task reconcile --dry-run --format json`, and deleted. Each had compatible Tasks Blocked settings, a fixed daily anchor of 2026-10-12, one open Pomodoro link to a project resident, and an open external prerequisite. All fixture bytes remained unchanged.

| Fixture input | Observed result |
| --- | --- |
| `^prj` Depends-On line plus projection; resident Next | Only `^prj` marked Blocked; resident remained Next; ledger link remained |
| Project `depends_on` YAML list only | No blocking derived from the property |
| Future project `scheduled:` without a prior project sync | No blocking derived from that frontmatter alone |
| Ordinary linked task with an open prerequisite | Dependent marked Blocked, prerequisite promoted Next, ledger root still present in the modeled result |

Two exported JavaScript planner probes reproduced the project dependency child/field write and the conversion-to-fake-task behavior described above. `node scripts/build-plugins.mjs --check` passed for all four generated plugins, verifying that the inspected fragment sources and probed generated entrypoints agree.

These are probes of existing behavior, not passing tests of a proposed implementation. No full application test suite or live-vault reconciliation was run.

## Proposed data and behavior contract

### 1. Store project dependencies as links, with one authoring source

Canonical form:

```yaml
depends_on:
  - "[[job#^update-linkedin]]"
  - "[[another_project#^prj]]"
```

Use a list of plain task block links, not task IDs, bare project links, aliases, embeds, or separate note-level dependency entities. Preserve authored order; deduplicate by resolved note path plus block ID. Reuse existing shortest-unambiguous link formatting and target-ID rules. Accept equivalent flow lists and, for reader tolerance, a single quoted block-link scalar; write the canonical list. Treat absent, null, or empty-list values as no project prerequisites. Diagnose malformed shapes and duplicate keys.

Obsidian supports quoted internal links in list properties. Quoting is necessary for programmatic writers, and frontmatter keys must be unique. [Obsidian's official Properties documentation](https://obsidian.md/help/properties).

The project note must have project type and a valid lifecycle identity; a stray task with `^prj` in an ordinary note must not make the note a project. Dependencies remain task prerequisites, including when their target is another project's `^prj` task.

Keep a **derived** `[dependsOn::]` projection on `^prj` for existing Tasks-based consumers and prerequisite identity bookkeeping. The request forbids a Depends-On child line for project tasks, not a machine-maintained inline projection. Crucially, that projection must never become an independent authoring surface or regenerate frontmatter after a property deletion.

Ordinary tasks keep their existing managed Depends-On lines and projections. Do **not** copy project prerequisites into every resident task's managed line or field: that would erase the distinction between inherited and authored constraints, create write churn, and make dependency removal ambiguous.

### 2. Derive effective blocking from reasons, not yesterday's checkbox

For a recognized open resident task:

```text
effective blocked =
    has an open local prerequisite
    OR has a strictly future local schedule
    OR its containing project is effectively blocked
```

A project's effective blocking includes open prerequisites from its frontmatter and a strictly future project schedule. Apply the same date anchor as reconciliation. The lifecycle task gets the project's reasons, without inheriting from itself. Future additions to project blocking should feed this one reason function so residents do not need another special case.

A project is not blocked merely because `status: waiting` or an arbitrary new `status: blocked` happens to be present. Frontmatter lifecycle status and derived task blocking are separate concepts. Likewise, a stale manually authored `[?]` with no surviving input reason should recover, not infect every resident task permanently.

Recognized Done, canceled, non-task, and unknown/custom statuses keep existing preservation rules. Apply inheritance to every eligible Bob task physically resident in the project note, including nested tasks and `#ref` proxies, not just rows under `## Tasks`. A referenced task that physically lives in another note does not become a resident merely because this note links to it.

**Scope adjustment:** use immediate note residence for the first implementation. Do not silently walk `parent` links and gate every descendant project, reference note, or area. Those relationships are broader than residence, and automatic descendant gating creates additional cycles and recovery obligations. If Bryan wants transitive sub-project gating, make that a separately accepted extension with its own hierarchy semantics and tests.

Store structured blocking reasons in computed reports/API models: local dependency, local schedule, project dependency, project schedule, with the project and prerequisite identities. Do not add a persistent previous-lane field or a second stored project-block flag.

### 3. Define “remove Task Links” as removing live agenda entries

**Requirement clarification:** remove matching live links under the selected current day's open Pomodoros. Preserve completed Pomodoro history, previous-day activity, struck links, backlinks in prose outside the agenda, and dependency links themselves. These are distinct uses of task block links; deleting every occurrence across the vault would destroy history and the dependency input.

Prune links for **all effectively blocked tasks**, whether blocked by a local dependency, schedule, or project inheritance, including tasks already `[?]` whose links are stale. Include a linked `^prj` task when it is effectively blocked.

Use the same removal grammar in Rust and JavaScript:

- A dedicated blocked Task Link bullet is removed with its nested subtree, as in the existing deferral planner.
- On a mixed prose/multiple-link bullet, remove matching tokens and keep unrelated text and links. Remove an empty resulting item rather than leave a meaningless blank bullet.
- Preserve non-task and unresolved targets; do not guess a destructive match from an ambiguous basename/block ID.
- Delete a Pomodoro **entry** only when no real child list item remains after composed cleanup. Plain work-log children count as content. Keep the `## Pomodoros` heading.

The dedicated-subtree rule can remove authored annotations below a planned link; this follows current scheduling deferral behavior, but it should be documented and tested. If those annotations need preservation, move them into the task's Work Log first rather than quietly invent a new storage rule.

Other days' open entries are not automatically today's work queue. If future daily ledgers are actively used for planning, decide separately whether their links also need pruning; leave the previous-daily read-only contract intact.

### 4. Reject containment-induced deadlocks

A project depending on an open task *inside itself* creates a deadlock under the proposed semantics: the project waits for that task while the project blocks that task. Reject this in the picker and capture writer with a specific reason. Represent implicit resident-to-project gating in validation so longer cycles are caught too, for example:

```text
project P waits on external T
T waits on resident R
R inherits P's gate
```

Do not persist those implicit edges as authored `[dependsOn::]` values. Making every resident depend on its project's `^prj` would block all project work until the entire project is complete, which is a different and unusable rule.

Hand-authored invalid edges should produce cycle diagnostics and retain recoverable input; reconciliation must not silently delete a prerequisite to break a cycle. Existing open-target classification is already deterministic even when dependency graphs contain cycles. Cycle-safe traversal remains necessary for promotion and explanation.

### 5. Recovery and agenda placement are different actions

When the final blocking reason disappears, recover using existing Ready/Next/Pending rank semantics and recent-activity rules. Do not restore an arbitrary pre-block lane: accepted sticky-lane policy explicitly stores no such hidden state, and lanes do not survive Blocked. After links have been pruned, a resident with no remaining recovery rank will normally become Ready.

Dependency removal, prerequisite completion/cancellation, a reached/removed project schedule, and moving a task between project notes must all recompute effective reasons. A task whose own dependency clears remains Blocked while its project gate remains.

Retain existing authored-dependency commitment transfer for dependency gestures, subject to the target's own effective blockers. Do not derive promotions from ledger roots that cleanup has deleted, or invent automatic lane transfers from every resident task.

Existing successor behavior needs an explicit project-aware guard. Recover affected project residents when a project gate clears, but **do not automatically fan out every resident task into the completed prerequisite's Pomodoro slot**. Implicit inheritance is not an authored successor edge. Ordinary direct successors can retain their existing placement policy; every proposed placement must pass the effective-blocking check.

## Migration and reconciliation design

`bob task reconcile` should perform the example's migration automatically, as part of its ordinary guarded plan. No new public command or flag is necessary.

A suitable sequence is:

1. Snapshot the vault, status registry, selected daily ledger, and existing read-only recent-activity inputs.
2. Normalize/migrate dependencies, handling project lifecycle tasks separately from ordinary R1–R10 reconciliation. Reparse task locations after YAML or child-line edits.
3. Resolve local and project dependency targets; calculate effective blocking reasons independent of desired lane ranks.
4. Compose existing duplicate/terminal-reference cleanup with blocked-link pruning, using the post-migration task identities and planned blocking state.
5. Remove newly childless Pomodoro entries and reparse the surviving ledger.
6. Derive lane promotions and recovery ranks from the ledger that will actually be written. Apply the precomputed blockers at highest precedence.
7. Group final task sections and update counts; write through existing guarded outputs, retry/recovery paths, and report models.

The current early multiple-open-timed-Pomodoro guard should remain a deliberate invariant; do not inadvertently relax it because a later prune might erase one conflicting entry. Compose transformations against refreshed text and stable identities rather than applying old line numbers after frontmatter insertions.

Migration rules should be explicit:

| Existing state | Recommended treatment |
| --- | --- |
| No project property; one well-formed managed `^prj` dependency line | Import links into YAML, resolve/stamp targets through existing rules, remove the recognized child, derive projection and blockers |
| Property and child line agree after resolution | Keep property; remove redundant child; keep unrelated children/logs |
| Property and child line disagree | Warn with both sources and avoid destructive migration until repaired; do not silently union or discard edges |
| Property is present and empty | Treat as intentional empty source, not permission for R2 to resurrect a projected field |
| Malformed/duplicate property, malformed child, ambiguous lifecycle identity | Explain the per-project problem and skip destructive migration; never interpret malformed data as safely empty |
| Closed project task | Preserve dependency history; use the project's canonical property when reopened |

**Migration adjustment:** do not indefinitely import a field-only `^prj [dependsOn:: ...]` when no property/managed line exists. The old projection and a stale projection after a user deletes frontmatter are indistinguishable. Preflight and explicitly repair field-only legacy cases during rollout; afterward property absence is authoritative empty. Recognized child-line migration covers the supplied example. Generic R2 must be bypassed for project lifecycle tasks or it will recreate the forbidden child line.

Resolve missing/archived targets through the existing identity and archive rules. Preserve target IDs, use exact-path/unique-basename resolution, and keep warning behavior for unresolved links. Existing unresolved IDs are warnings rather than open blockers; do not silently change that global policy as part of this feature. For malformed or conflicting project inputs, avoid unsafe recovery or pruning until an authoritative reason set can be established.

Extend dry-run/JSON reporting additively: migrated project dependency properties, inherited blocking reasons, removed blocked references, empty-entry removals, and diagnostics naming the responsible project. Do not list inherited tasks as having authored dependency children.

## Changes required beyond the requested callbacks

| Component | Needed change |
| --- | --- |
| Rust dependency/reconcile model | List-aware project source, migration branch, derived lifecycle projection, reusable effective-blocking reasons |
| `task_status_hooks/sync.rs`, `compose.rs`, ledger planners | Compute blocking before live-link cleanup; derive ranks from final ledger; preserve grouping and guarded-write behavior |
| Project sync/scheduling | Keep current lifecycle and ordinary schedule propagation contracts; reconciliation also reads project scheduling directly so behavior does not depend on command order |
| Navigation dependency planners/stage/mirror | Dispatch by valid project lifecycle context; CURRENT rows read YAML; add/remove/clear/count/API/linked-task edits share that dispatch; handle unsaved YAML |
| Project conversion | Extract dependencies before ordinary child conversion; rebase outbound links; serialize YAML; reverse into an ordinary managed line/projection; preserve inbound identity/backlink rewrites |
| Navigation scheduled recovery, cycler recovery/successors, capture completion | Use effective project blockers on recovery and placement; refresh residents affected by a cleared project gate |
| Block ID prompt/direct link, capture link/toggle/move paths | Refuse/re-route adding agenda links to effectively blocked targets; still allow removing existing stale links |
| Rust capture dependency writer (`capture/dependencies.rs`) | Existing `&...:prj` writes use project storage and block/prune residents within the staged plan; no new grammar needed |
| Ledger tools and vault views | Show project-derived reasons; update dependency presentation and `blocked.md` classification; verify dashboard/Today/budget readers consume coherent post-state |
| Docs and memory | Document the project exception, migration, gates, cleanup scope, recovery, and glossary definition |

Task-to-project conversion must re-resolve same-note links relative to the *old* note and then render them for the new project, rather than copy `[[#^id]]` verbatim. Reverse conversion must render from the destination parent note's context. References to targets converted from source children need their mapped destination identities. Keep existing `[id::]` identity where applicable and regenerate dependency projections consistently with link rewrites; otherwise conversion can leave field-only IDs pointing at a removed source task.

The converter's live-link expansion into project task links also needs the effective-blocking guard. A blocked source converted to a gated project must not immediately relink all its now-blocked children.

For interactive writes, reuse editor-aware snapshots and expected-content guards. Same-note YAML, lifecycle marker, resident markers, and child removal can be one editor transaction. Target identity preparation and daily pruning are cross-note writes and cannot be promised as one global Ctrl+Z. Report cross-note failures and let reconciliation repair remaining stale links. Avoid adding a CLI subprocess dependency to every Obsidian gesture; the existing pure-planner/API approach is adequate with shared conformance vectors.

Because Mac Capture is a thin bob client, these capture changes belong in bob. Only coordinate the native client if the versioned response contract gains fields it needs to display; no duplicate project dependency parser should be introduced there.

### Views need explicit inheritance support

I recommend an additive ledger-tools effective-blocking reason API backed by its memoized task/metadata models, not repeated vault reads while rendering. Use it to add a project-blocked classification and prevent inherited tasks being counted as STRANDED. Maintain exclusive sections when a resident also has a direct dependency or a future local schedule. Provide a `[?]` fallback when the API is unavailable, rather than labeling valid inheritance a broken state.

Do not patch Tasks' upstream `is blocked` implementation or manufacture fake task dependencies solely to satisfy that filter. Native direct-dependency results and Bob's broader effective blocking should be distinguished in the view contract.

## Requirement adjustments called out

1. “Blocked project” means derived project reasons, not cached `[?]` or a new authored lifecycle status.
2. Inheritance initially follows physical note residence; transitive `parent` inheritance is an explicit future decision.
3. Link removal targets live agenda links in the selected day's open Pomodoros, with completed history and dependency inputs preserved.
4. Done/canceled/non-task/unknown statuses retain current protection; “any task” refers to recognized open Bob tasks.
5. Both conversion directions and all dependency/link/recovery entry points need coverage, beyond the two named hotkeys.
6. Keep only a derived lifecycle inline projection; do not author dependencies or inherited gates on each resident row.
7. Reject containment cycles; preserve existing unresolved-target policy rather than expanding this into a global dependency-policy rewrite.
8. Recover lanes without automatically re-adding every resident to today's agenda.
9. Fix the blocked view's inherited-reason classification; a checkbox-only implementation is incomplete.
10. Field-only legacy migration needs explicit preflight handling to avoid resurrecting deleted frontmatter. The supplied managed-line example remains automatic.
11. Resolve the actual platform shortcut by command ID; the inspected binding differs from the requested modifier spelling.

## Acceptance checks and rollout

The following are meaningful implementation tests, not additional tests written during this research:

- A fixture modeled on the Databricks note: one reconcile produces YAML, two Blocked residents, correct groups/badges, and removes exactly the two resident links while retaining LinkedIn and the nonempty JOB Pomodoro. A second run is a no-op; dry-run predicts the same output without writes.
- A blocked resident as the last Pomodoro child removes the entry; a remaining prose/log child preserves it. Closed and previous-day history stay byte-identical.
- Project dependency plus local dependency plus local/project schedule: resolving one reason cannot recover the task until all reasons clear. Include today/past/future date boundaries and project schedule without prior sync.
- Already-Blocked tasks with stale live links are pruned. New dependency hand edits and capture `&...:prj` converge to the same state.
- Same-note/external/ambiguous/archived targets, preserved IDs, flow/block lists, malformed and duplicate YAML, CRLF, and final-newline preservation.
- Empty/deleted frontmatter does not re-adopt its lifecycle projection; disagreeing legacy sources warn without silently dropping data.
- Project-to-resident and multi-project/ordinary-task cycles are refused in gestures, diagnosed in hand edits, and handled without infinite traversal.
- Forward/reverse conversion round-trips dependencies and their meanings across note contexts, never creates a metadata task, and preserves existing backlink/identity behavior.
- Counted mixed ordinary/project edits, dependency clear/remove/API/chip paths, open-buffer overrides, stale target/source guards, and cross-note failure reporting.
- Completion/cancellation/removal recovery respects an independently blocked project; clearing the project gate recovers eligible residents without successor fan-out.
- Direct link, picker, capture, conversion expansion, and successor placement cannot recreate a live link to an effectively blocked task. Unlink remains usable.
- Blocked views, Today agenda, budgets, and chips classify inherited blockers correctly and explain their project source.

Add shared project-dependency vectors to `docs/task-dependencies.md` alongside the existing Rust/JavaScript vectors. Run bob-cli `just check` and bob-plugins `npm test`/`npm run validate` after implementation. Update fragment sources and regenerate `main.js`; do not hand-edit generated plugin bundles.

Deploy compatible CLI/plugins together before live migration, run `bob plugins sync` for plugin changes, inspect `bob task reconcile --dry-run --format json`, then apply reconciliation and check its warnings and second-run idempotence. Snapshot guards and recovery manifests remain the repair path for partial writes. Research itself has not migrated the live vault.

## Memory and documentation follow-through

The user explicitly requested: “The ‘task dep links’ glossary memory web term should be updated accordingly.” The relevant canonical strand is `sase/memory/glossary/task-dependency-link.md`. Update it when the behavior lands, through the memory-write workflow, then regenerate instructions with `sase memory init`.

Suggested concise meaning: ordinary task prerequisites live on the managed Depends-On child; a Project Task's prerequisites live as quoted block links in its Project Note's `depends_on` property. Both use plain links and derived identity projections. An unmet project prerequisite blocks recognized open tasks resident in that note. Dependency links remain prerequisites, never Pomodoro agenda links or recursively completed children. Ctrl+Shift+P edits the appropriate source by context.

The accepted decision `task-deps-are-depends-on-links` currently claims every task uses a child line, and the project exception reopens part of that architecture. If accepted, add a new narrowly scoped decision and mark the earlier record superseded-in-part with a back-link, following the immutable-record policy; do not rewrite its historical rationale. An executable plan needs a memory decision for each affected canonical note. The glossary change has the explicit user request; decision-record changes should be presented with the exact claims the implementation would make false. This report proposes those changes but does not edit memory or submit an implementation plan.

Update `docs/task-dependencies.md`, `docs/task-status-hooks.md`, `docs/projects.md`, capture contract documentation where affected, and the blocked view's explanatory text. Keep command aliases and frozen capture protocol names intact.

## Evidence references

Repository paths below are relative to the named repo at the source snapshots above; line numbers are navigation aids, not a promise about future branches.

- bob-cli: `docs/task-dependencies.md` §§2–7 and §12; `docs/projects.md` lifecycle, scheduling, and conversion contracts; `docs/task-status-hooks.md` cleanup, Blocked precedence, and recovery.
- bob-cli: `src/native/task_status_hooks/sync.rs:353`, `:495`, `:680`; `task_status_hooks/reconcile.rs:45`; `task_status_hooks/compose.rs:5`; `task_status_hooks/pomodoro.rs:282`; `projects/scan.rs:261`, `:372`.
- bob-cli: `src/native/task_status_hooks_write/apply.rs:32`; `src/native/capture/dependencies.rs:1898`; `src/native/task_complete/recovery.rs:51`; capture Pomodoro-link and task-toggle planners.
- bob-plugins: `plugins/bob-navigation-hotkeys/src/080-dependency-identity.js:68`; `110-project-seed.js:1`, `:630`; `100-yank-and-paths.js:345`; `210-rename-and-line-context.js:766`; `660-plugin-project-notes.js:3`, `:290`; `490-plugin-lifecycle.js:80`.
- bob-plugins: navigation `590-plugin-dependency-stage.js`, `600-plugin-dependency-mirror.js`, `420-picker-counted-dependency.js`, `140-scheduled-recovery.js`, `160-pomodoro-reorder.js:542`; cycler `085-successor-plan.js`; block-id-prompt `030-tasks-and-dependencies.js:215`; ledger-tools `270-plugin-dependency-model.js`.
- Read-only vault inputs: `job_apply_to_databricks.md`, relevant links in `2026/20261012.md`, `blocked.md`, `dash.md`, and the two relevant `.obsidian/hotkeys.json` entries.
- Audited memory: project/task/dependency/link/Pomodoro glossary strands; `decisions:task-deps-are-depends-on-links`, `decisions:task-lanes-are-sticky`, `decisions:task-status-is-derived`, `decisions:today-is-read-from-the-ledger`; Obsidian, CLI, and artifact conventions.
- External primary documentation: [Obsidian Properties](https://obsidian.md/help/properties) and [Tasks dependency filters](https://publish.obsidian.md/tasks/Queries/Filters).

## Recommended solution

Adopt **project frontmatter as the sole authored dependency source for `^prj`, ordinary Depends-On lines for ordinary tasks, and one computed effective-blocking model that adds the containing project's reasons**. Keep a derived lifecycle projection for compatibility; do not materialize inherited dependencies on resident task lines.

Compute blockers before pruning live agenda links, derive lane ranks from the surviving ledger, and reuse existing guarded writes and empty-Pomodoro cleanup. Update both conversion directions, every dependency/link/recovery writer, and blocked-task views in the same coordinated release. Automatically migrate the Databricks managed-line example with `bob task reconcile`, validate containment cycles, preserve historical links, and recover residents without automatically flooding today's agenda. This implements the requested project gate while keeping dependency authorship, derived status, and planning history coherent.
