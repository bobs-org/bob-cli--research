# READY task capacity: a calm, consistent review aid for Bob

Researcher: **cdx**  
Date: **2026-10-01**  
Scope: independent design research; no feature implementation or vault mutation.

**Recommendation:** add a configurable, warning-only **READY limit per area/project note**, defaulting to **5**. Build it as a grouped view of Bob's existing freshness-gated READY model. Show one compact dashboard summary, an actionable list of crowded notes, matching CLI output, and contextual feedback after supported Bob commands increase an over-limit count. Keep all tasks accessible. Treat a crowded note as a review prompt, not proof that its work needs another project.

## 1. Research method and confidence

I inspected bob-cli and the authoritative bob-plugins source checkout, read the relevant audited SASE memories and architecture decisions, and consulted primary GTD, Kanban, Obsidian, and accessibility sources. I did not locate or consult any report, transcript, summary, or findings from this swarm's other researchers.

The inspected source revisions were:

- bob-cli: `eba9cbc940393a2c733c68a0ed198ec08b3f84b2`.
- bob-plugins: `d4197f7c0fe89186047cb7ec3bb5434a79cedd88`.

The existing JavaScript READY badge, dashboard parity, and navigation freshness suites passed: **67 tests**, using:

~~~sh
node --test --test-reporter=dot \
  scripts/test-ledger-tools-ready-badge.cjs \
  scripts/test-ledger-tools-dashboard-parity.cjs \
  scripts/test-navigation-freshness.cjs
~~~

That verifies useful existing foundations. It does not verify the proposed feature, Obsidian's actual rendering, or new native/plugin parity. I did not inspect live vault tasks or measure Bryan's current distribution; every UI example below is illustrative.

## 2. What the current system already provides

| Finding | Consequence for this feature | Evidence |
| --- | --- | --- |
| READY is a visible TODO pool with NEW and ROTTEN review buckets removed, while retaining freshness-exempt tasks. | Counting `[ ]` or counting only freshness state FRESH would both be wrong. | [READY contract](https://github.com/bobs-org/bob-cli/blob/eba9cbc940393a2c733c68a0ed198ec08b3f84b2/docs/plan.md#ready-backlog-dashboard-and-daily-badge), [freshness evaluation](https://github.com/bobs-org/bob-cli/blob/eba9cbc940393a2c733c68a0ed198ec08b3f84b2/docs/freshness.md#4-evaluation). |
| The global soft READY cap already defaults to 100; NEXT and PENDING have separate caps. | Add a per-note cap alongside the existing caps. Do not repurpose `max_ready` or let this change the plan's theme/link status. | [Plan configuration](https://github.com/bobs-org/bob-cli/blob/eba9cbc940393a2c733c68a0ed198ec08b3f84b2/docs/plan.md#config). |
| `bob-ledger-tools` owns READY predicates, freshness evaluation, live badges, Today membership, and cache invalidation. | Extend this plugin instead of creating a seventh Bob plugin or independent Dataview expressions. | [Ledger tools implementation](https://github.com/bobs-org/bob-plugins/blob/d4197f7c0fe89186047cb7ec3bb5434a79cedd88/plugins/bob-ledger-tools/main.js), especially `readyTaskVisible`, `readyCountFromTasks`, `readyBudget`, and `freshnessEnsureMemo`. |
| Moving tasks already uses planned before/after contents, concurrency guards, destination-first writes, and rollback. It stamps each moved open task line, including nested lines. | A move's capacity effect must use the actual resulting task tree, not the number of selected root tasks. | [Navigation implementation](https://github.com/bobs-org/bob-plugins/blob/d4197f7c0fe89186047cb7ec3bb5434a79cedd88/plugins/bob-navigation-hotkeys/main.js), `planTaskMoveAcrossFiles` and `commitTaskMoveSession`. |
| Alt+N and the property picker's lane row release NEXT/PENDING to Ready; unlinking alone preserves those lanes. | Lane release can increase READY. An ordinary unlink of a sticky Next task usually cannot. Inspect the resulting state. | [Lane contract](https://github.com/bobs-org/bob-cli/blob/eba9cbc940393a2c733c68a0ed198ec08b3f84b2/docs/plan.md#lanes-next-and-pending), navigation `toggleTaskLaneOnTasks`. |
| Freshness confirmation and several line-editing gestures stamp tasks; creation does not. | Alt+F, Alt+Shift+F, and `]s` are central capacity-increasing operations. Capturing a NEW task normally does not immediately consume READY capacity. | [Who stamps](https://github.com/bobs-org/bob-cli/blob/eba9cbc940393a2c733c68a0ed198ec08b3f84b2/docs/freshness.md#5-who-stamps). |
| Native `bob plan` currently has no READY count. `bob freshness` already gathers rich tasks, Today membership, per-note refresh settings, and freshness warnings. | The CLI needs a new native grouped report, but can reuse existing machinery. This is not an already available CLI switch. | [Plan command](https://github.com/bobs-org/bob-cli/blob/eba9cbc940393a2c733c68a0ed198ec08b3f84b2/src/native/plan_budget/cli.rs), [freshness scan](https://github.com/bobs-org/bob-cli/blob/eba9cbc940393a2c733c68a0ed198ec08b3f84b2/src/native/freshness/scan.rs). |
| Native project classification recognizes exact scalar type links; navigation also recognizes lists of type values. Capture targets scan only routable top-level notes. | Define and test classification explicitly. Neither `bob capture-targets` nor project OPEN/SHOWN counters is a correct capacity report. | [Project scanner](https://github.com/bobs-org/bob-cli/blob/eba9cbc940393a2c733c68a0ed198ec08b3f84b2/src/native/projects/scan.rs), [capture targets](https://github.com/bobs-org/bob-cli/blob/eba9cbc940393a2c733c68a0ed198ec08b3f84b2/src/native/capture_targets.rs), navigation `isAreaType`, `isProjectType`, and `getChildNoteInfo`. |

The accepted freshness decision explicitly identifies a required plugin-free surface as a reason to revisit gating coverage. This CLI requirement is such a surface. Extend the documented contract deliberately; do not quietly turn a headless `bob query` result into a purported freshness-gated READY count.

## 3. Is this a good idea?

**Yes, as a concentration diagnostic. Five is a useful starting policy, not a universal productivity rule.**

A small per-note menu can make morning review easier and expose mixed work that needs clarification. The limit is concrete, inspectable, and reversible. It also addresses something the global READY cap misses: one note holding a disproportionate share of the available backlog.

### 3.1 A crowded note is evidence to investigate, not an instruction to split

Official GTD guidance defines projects by achievable outcomes requiring multiple actions. It permits parallel next actions and keeps dependent future actions with project plans until actionable. A count threshold alone does not establish a project boundary. Use the warning to investigate distinct outcomes, missing dependencies, or work that is no longer a current commitment. Creating “Project 2” merely to clear a badge increases organizational work without reducing the load. [David Allen Company: managing projects](https://gettingthingsdone.com/2017/05/managing-projects-with-gtd/).

An area such as home maintenance can legitimately contain many unrelated actions. A narrow project can legitimately expose six parallel actions. A uniform default is worthwhile if exceptions are explicit and inexpensive.

### 3.2 This measures the available menu, not all commitments

Kanban defines work in progress relative to a workflow's started and finished points. Bob's READY list is a backlog surface; it should not be advertised as a WIP limit. Existing NEXT/PENDING and daily plan budgets remain measures of committed work. This distinction is an inference from the Kanban definition and Bob's lane contracts. [The Kanban Guide](https://kanbanguides.org/the-kanban-guide/).

Bryan could “fix” a crowded READY note by committing tasks to NEXT, increasing commitment while turning this warning green. The UI should offer review, move, defer, or clarify actions; it should not offer “promote until under the limit” as a repair strategy.

Splitting 12 tasks into three projects gives each four READY tasks but leaves 12 available actions. Keep the global READY cap visible. Leave hierarchical rollups for a separate future decision.

### 3.3 Freshness creates an incentive problem

Seven READY tasks can become zero READY tasks as confirmations expire. Nothing was completed or deprioritized. Conversely, carefully confirming NEW/ROTTEN work can make a note exceed the limit.

The diagnostic must never teach “stop reviewing because the count is red.” Show NEW and ROTTEN context beside READY. Clear NEW first, finish the existing review ritual, then address crowded notes. Do not cap review or auto-defer the sixth confirmation. Bob's existing procedure deliberately clears NEW before reviewing ROTTEN and lanes. [Review ritual](https://github.com/bobs-org/bob-cli/blob/eba9cbc940393a2c733c68a0ed198ec08b3f84b2/docs/freshness.md#6-review-ritual).

### 3.4 Scheduling should express an honest decision

Ctrl+Shift+P supports priority-driven scheduling, so it is a practical resolution path. Lowering a priority label by itself need not remove a task from READY. Its resulting schedule/visibility/state determines the count.

Use a real revisit date when “not now” means “review after this date.” Possible actions without a real date belong in a regularly reviewed incubation workflow. Official GTD guidance supports reviewed Someday/Maybe storage for actions and projects. This report does not propose a new task lane or status for incubation. [David Allen Company: Someday/Maybe](https://gettingthingsdone.com/2010/10/what-goes-on-a-someday-maybe-list/).

## 4. Explicit adjustments to the requirements

| Requested direction | Recommended adjustment | Reason |
| --- | --- | --- |
| No note should contain more than N READY tasks. | A **soft review limit**: N is allowed; N+1 is flagged. Never reject a valid edit, move, release, or confirmation. | Correct routing and release must remain possible when a note is crowded. |
| Create projects or deprioritize crowded notes. | Diagnose: move a coherent outcome, establish real dependencies, defer honestly, cancel obsolete work, or intentionally raise a note's limit. | A counter is a cue, not enough evidence for restructuring. |
| Notify anytime a keymap violates the constraint. | Notify after every successful supported Bob command that **increases** an already over-limit count or crosses into excess. Coalesce each command's batch into one message. | Warn about worsening load without warning on unrelated edits or improvements. |
| “Any keymap.” | Apply policy to Bob command handlers regardless of key binding or command-palette invocation. Manual edits, other plugins, CLI writes, and sync refresh diagnostics without per-keystroke toasts. | Keystrokes are not a reliable mutation boundary. This narrows the literal requirement and should be accepted explicitly. |
| Configurable default N=5. | One global setting plus an optional numeric note override. No `parent` inheritance, exemption tags, path globs, or per-task limit fields in v1. | Areas vary in breadth; a small model stays understandable. |
| Dashboard and/or note badges. | Dashboard summary and full diagnostics are mandatory; reuse a current-note widget in templates and optionally the active-note status bar. | Immediate coverage without generated counts in every note. |
| Show READY load. | Show READY, NEW, and ROTTEN separately. Only READY is thresholded. | Consistent meaning with unreviewed pressure visible. |
| Beautiful presentation. | Reuse Bob's theme-native chips, exact counts, labels, focus states, and source links. | Consistency and legibility beat another graph. |

These adjustments preserve the requested outcome: identify every violating area/project quickly and get relevant feedback when Bob gestures worsen one.

## 5. Counting contract

Define this once in a command/design contract, then implement Rust and JavaScript against shared fixtures.

Let `B(t)` be the dashboard's **visible TODO pool**, with existing visibility, blocked, schedule, and Today rules applied. Let `bucket(t)` be its freshness bucket.

~~~text
ready(t) =
  B(t)
  AND bucket(t) != new
  AND bucket(t) != rotten

ready_count(note) =
  number of source task rows t where ready(t) and source_path(t) == note.path

effective_limit(note) =
  valid note.ready_limit, otherwise plan.max_ready_per_note, otherwise 5

excess(note) = max(0, ready_count(note) - effective_limit(note))
over(note)   = excess(note) > 0

over_notes   = number of eligible notes where over(note)
excess_tasks = sum(excess(note)) over eligible notes
~~~

`bucket == null` is insufficient by itself: it also describes out-of-scope tasks. `state == fresh` is too narrow: recurring and other freshness-exempt Ready tasks remain in READY.

### 5.1 Eligibility and ownership

- Recognize area/project notes through the canonical `type` links, including quoted scalars and navigation's list form. Cover legacy bare `type: [[project]]` explicitly; ordinary YAML parsing can interpret it as a nested sequence instead of a wikilink string.
- Traverse eligible notes throughout the vault, including nested directories. Do not restrict to capture routes or require a working `^prj` completion task.
- Use existing system/template/archive exclusions, plus conflicts and `dash.md`. Document precise path rules alongside dashboard rules, rather than inventing another ad hoc list.
- Include recognized project notes even if lifecycle metadata says terminal but visible READY tasks remain; display lifecycle as context. Move destinations retain existing open-project restrictions. Diagnostics should reveal inconsistent leftover work.
- Count by the file **physically owning the task**, not a heading, `parent`, dashboard row, embed, or backlink.
- Count all eligible task rows, including nested rows: those are distinct tasks in the current dashboard. Plain subtasks without task recognition do not count.
- Embedded work contributes once in its source note. Dependency links and project index rows do not create more READY tasks. Genuine physical copies are additional task rows.
- Do not deduplicate rows merely by description or block ID. Identical descriptions can be legitimate; duplicate IDs need diagnostics rather than silently lost capacity.
- Hidden `^prj` tasks remain excluded through the existing hide predicate. Do not add a general block-ID exemption.
- A file typed as both area and project appears once, using the existing classifier's deterministic precedence, pinned by a fixture.

Eligible-note totals need not equal the global READY badge: inboxes, daily notes, and other sources can contribute to global READY.

### 5.2 Visibility must remain exact

Reuse TODO **type**, including custom TODO symbols; recognition/global-filter settings; the full dependency graph; future schedule exclusion; existing case-insensitive `#hide` substring behavior; template/conflict exclusions; and ledger-derived Today membership.

Do not infer task visibility directly from a note's `scheduled`, `priority`, or `parent` field. Use actual task inputs after existing project scheduling machinery has applied them.

A temporarily linked TODO task is excluded by Today even before its checkbox reconciles. Releasing Next work consumes READY only when the result is visible and no longer Today.

The native READY query is an **ungated candidate pool**, not the final result. Add Today and freshness gating before grouping. [Native task contracts](https://github.com/bobs-org/bob-cli/blob/eba9cbc940393a2c733c68a0ed198ec08b3f84b2/src/native/dataview/tasks/mod.rs).

### 5.3 Unknown remains unknown

Cold Tasks data, unready Today data, unsupported task format, failed freshness evaluation, unreadable notes, and unsupported APIs must never appear as `0/5` or “within limits.”

Return availability and warnings. Use `–/5 · updating` temporarily; show actionable unavailable/default-policy states for configuration problems. If partial scans are supported, say “at least 2 over; 1 note unavailable.” A simpler native v1 can fail the full report rather than emit an incomplete table silently.

The existing READY implementation can fall back to an ungated legacy count when its freshness gate fails. Do not present that as an authoritative new capacity result. Factor a validated shared snapshot and label compatibility fallback as non-authoritative. Do not change READY's definition because a plugin is absent. [Existing fallback](https://github.com/bobs-org/bob-plugins/blob/d4197f7c0fe89186047cb7ec3bb5434a79cedd88/plugins/bob-ledger-tools/main.js).

## 6. Configuration

Recommended global setting, preserving the existing global cap:

~~~yaml
plan:
  max_ready: 100
  max_ready_per_note: 5
~~~

Optional local frontmatter:

~~~yaml
type: "[[area]]"
ready_limit: 8
~~~

`ready_limit` applies only to this file. It does not inherit through `parent`, change status, or exempt tasks from the global cap.

Mirror existing cap validation: integer 1 through the supported unsigned-32-bit maximum; absence/null means inherit; zero, negative, fractional, or string values are invalid. Invalid note overrides emit `ready_limit_invalid` and fall through to the global setting. The CLI treats invalid relevant global config as a usage error; keymaps continue with the existing documented default fallback and announce it once.

Expose effective value and provenance in tooltip/detail/JSON: “Limit 8 from this note” or “Limit 5 from Bob config.” Ignore unknown fields without breaking unrelated commands.

**Cross-device caveat:** current global config lives outside the vault. Mobile already falls back when it cannot read it. Do not introduce an independent Obsidian setting that can drift from the CLI. V1 should show “using default limit 5” when applicable and honor vault-local note overrides everywhere. Identical customized global policy on mobile needs an explicit shared-policy decision; another slider does not solve it. [Plan config behavior](https://github.com/bobs-org/bob-cli/blob/eba9cbc940393a2c733c68a0ed198ec08b3f84b2/docs/plan.md#config), [mobile freshness caveat](https://github.com/bobs-org/bob-cli/blob/eba9cbc940393a2c733c68a0ed198ec08b3f84b2/docs/freshness.md#2-fields-overrides-and-config).

Avoid “dismiss forever.” A deliberate local limit is a clear exception; a hidden dismissal becomes another state to distrust.

## 7. Obsidian experience

### 7.1 Dashboard: one summary, then drill down

Keep the established task sections and lane-chip order. Add an ancillary **Ready load** summary near the review/budget strip rather than another task-status chip.

Illustrative compact state:

~~~text
READY 34                         READY LOAD 3 notes over · +7

▾ Ready load
  Note                         READY       Excess   Review waiting
  Research                     9 / 5       +4       2 new · 3 rotten
  Home                         7 / 5       +2       1 new
  Bob capture                  6 / 5       +1       —
~~~

The summary counts violating **notes**; excess counts tasks. An accessible label includes “3 area/project notes exceed their READY limit; 7 READY tasks above the combined limits.”

Clicking reveals diagnostics and focuses the first actionable row. Names open source notes, with READY detail/navigation to the first eligible task. For many violations, show an initial group and “Show all 17”; never silently truncate.

Sort violations by excess descending, READY count descending, then deterministic path. Include paths for colliding basenames. An “All notes” disclosure includes compliant and zero-count notes, with type/lifecycle details.

With zero violations, keep a quiet “Ready load · within limits” summary that still opens all counts. Do not celebrate merely because freshness expiry lowered READY.

### 7.2 Current note: small, source-local feedback

Reuse a `bob-ready` code block:

~~~text
Dashboard block:
  scope: vault
  show: over

Area/project block:
  scope: note
~~~

These are proposed parameters, not current syntax. A note block uses the processor's source path; rename/move must not leave a stale hard-coded path.

Illustrative note widget:

~~~text
READY 7/5   +2 over
Review waiting: 1 NEW · 3 ROTTEN
~~~

Below limit, show `READY 3/5`; exactly at limit, `READY 5/5 · at limit` without over styling. Use a compact widget, not a large error banner.

Put the block in appropriate templates and optionally provide an active-note status-bar badge for existing notes. Dashboard coverage must not require blocks everywhere. Avoid mass insertion or rewriting frontmatter with computed counts.

Detail uses source-resolving links or an existing task renderer, not duplicate editable checkboxes. Tasks without block IDs must still be navigable; display should not assign IDs merely for links.

### 7.3 Move picker: inform before choosing

Add a compact indicator to each destination:

~~~text
Bob capture        project       4/5 READY
Home               area          7/5 READY · +2 over
~~~

On the highlighted destination, show a trustworthy projection:

~~~text
Moving this task tree adds 3 READY tasks: 4/5 → 7/5.
~~~

“Adds 3” can differ from “moves 1 root.” Evaluate nested rows, stamping, destination refresh overrides, dependencies, schedules, and Today links.

Do not disable/hide crowded destinations or disturb fuzzy-search ranking. Use cached counts for rows; project only the highlighted choice, then revalidate at commit. Avoid generating a full vault mutation plan for every destination on every keystroke.

### 7.4 Visual and accessibility direction

Reuse rounded ledger-tools chips, two-part label/value spans, tabular numbers, theme variables, and focus treatment. Preserve the existing red over-cap convention; use subdued blue/neutral below limit. Avoid an “almost over” warning state: N is valid.

Five small capacity marks with a separate `+4` can supplement the fraction. Numbers and text remain primary. A saturated bar alone cannot distinguish 6/5 from 25/5. Variable local limits must not create sprawling marks.

Use keyboard-operable links/buttons, visible focus, descriptive accessible labels, and contrast in light/dark themes. Combine color with text/icon. Announce operation feedback without moving focus; verify Notice behavior and add a polite live-region mechanism if necessary. These choices follow W3C guidance on [color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) and [status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).

On narrow/mobile layouts, stack review context beneath the name. Keep motion restrained and honor reduced-motion preferences.

## 8. Notifications: precise operation feedback

For each eligible note `p`, warn when:

~~~text
operation succeeded
AND after.ready[p] > after.limit[p]
AND after.ready[p] > before.ready[p]
~~~

`5 → 6` warns; `7 → 8` warns; `7 → 6` does not; rewriting wording at unchanged `7` does not. Persistent diagnostics still show existing violations. Lowering a policy limit refreshes diagnostics and can show a configuration-result message; it is not a task mutation.

### 8.1 Cover relevant Bob command paths

| Operation family | Why READY can grow | Owner |
| --- | --- | --- |
| Ctrl+Shift+M moves, counted roots and descendants | Residence changes; open lines are confirmed; refresh policy can differ. | Navigation move planner/success handler. |
| Alt+F, Alt+Shift+F, `]s`, counted/Task Link review | Confirmation moves NEW/ROTTEN into READY. | Navigation freshness handlers and `finishFreshStamp`. |
| Alt+N or property-picker lane release, including cross-note targets | Next/Pending becomes TODO and Today links are removed. | Navigation lane transactions. |
| Property-picker schedule, priority, refresh, dependency edits or deletion | Tasks can become visible, unblocked, or fresh. | Navigation single/counted/Task Link/project handlers. |
| Alt+[ / Alt+] cycles and Ctrl+Enter reopen | An open TODO result can become confirmed READY. | `task-status-cycler`. |
| Completion/cancellation or dependency toggling | Other source tasks can become unblocked. | Status-cycler and graph-aware recovery paths. |
| Ctrl+Shift+Enter and Task Link changes | Typical linking reduces READY; removing temporary TODO Today membership can increase it. | `block-id-prompt`; use actual membership. |
| Project creation/promotion/demotion and task-to-project conversion | Work acquires new ownership or visible descendants. | Navigation project transformations. |

Normal unconfirmed creation is NEW, so no READY warning unless the same operation changes other READY membership. Keep NEW visible. Completion that only reduces counts needs no capacity toast.

This catalog follows the human-gesture/stamp contract and requires a final command-path inventory during implementation. [Mutation families](https://github.com/bobs-org/bob-cli/blob/eba9cbc940393a2c733c68a0ed198ec08b3f84b2/docs/freshness.md#5-who-stamps).

### 8.2 Compose into the existing result message

~~~text
Moved 2 tasks to Home · READY 5 → 7/5 · 2 over
Review Home

Confirmed task · Research READY 6/5 · 1 over
Review Research

Released 3 tasks · 2 notes now over their READY limits
Home 7/5 (+2) · Bob 6/5 (+1)
Review ready load
~~~

One command produces one consolidated capacity result, preferably within its success Notice. A “Review…” action opens source/diagnostics without rewriting work. No approval modal.

Deduplicate by operation identity and note, not “already warned today.” Later `7 → 8` must still give feedback. Many affected notes get one summary and drill-down. Sequential confirmations can update a visible message instead of stacking, while reflecting every successful increase.

Do not emit success before a multi-file move finishes, after rollback, or after cancellation. For partial application, evaluate actual applied contents and compose with existing error feedback; never claim the intended count landed.

### 8.3 Cache lag is a core correctness problem

`finishFreshStamp` already compensates for lagging Tasks cache data. Reading `readyBudget()` immediately after a write can return the old count. A timer or `before + selected roots` is insufficient. [Freshness feedback implementation](https://github.com/bobs-org/bob-plugins/blob/d4197f7c0fe89186047cb7ec3bb5434a79cedd88/plugins/bob-navigation-hotkeys/main.js).

Prefer an operation envelope containing actual before/after texts, updated daily ledger when relevant, affected paths, and snapshot generation. Evaluate their overlay through the shared task/freshness model, including dependency consequences. Publish only after success; reconcile with the next validated Tasks snapshot and discard the overlay after convergence.

If JavaScript parsing cannot reliably reconstruct a projected graph, do not label an estimate exact. Mark picker projection unavailable and use a pending operation receipt against the first post-write cache generation reflecting affected files. Serialize overlapping receipts, or merge affected paths and explicit outcomes, so intervening edits are not attributed to the wrong command. This is accurate deferred delivery, not guessing after 500 ms.

Manual edits, CLI writes, sync, time changes, and policy edits refresh persistent diagnostics. Avoid startup toasts for each existing violation or repeated notifications from cache refresh itself.

## 9. Architecture

**Classification/aggregation belongs in ledger-tools and native task/freshness modules. Command attribution belongs in existing mutation plugins.**

~~~mermaid
flowchart TD
    T[Task graph and note metadata] --> M[Validated READY model]
    L[Today's Pomodoro ledger] --> M
    F[Freshness rules and effective limits] --> M
    M --> G[Group source tasks by note]
    G --> D[Dashboard summary and diagnostics]
    G --> N[Note widget and picker counts]
    O[Operation before/after contents] --> P[Shared projected READY evaluation]
    M --> P
    P --> S[Successful operation receipt]
    S --> C[One contextual Notice]
    R[Native Tasks and freshness engine] --> J[Versioned per-note report]
    J --> CLI[bob ready human or JSON]
    V[Shared conformance fixtures] -.-> M
    V -.-> R
~~~

### 9.1 One model, several views

Add a capability such as `api.readyLoad` with its own namespace version. Proposed members:

~~~text
readyLoad.snapshot()
readyLoad.forNote(path)
readyLoad.preview(operation)
readyLoad.recordResult(operation, outcome)
readyLoad.renderSummary(parent, options)
readyLoad.renderNote(parent, options)
readyLoad.renderDiagnostics(parent, options)
~~~

Renderers use the same rows. Other plugins discover the API through `app.plugins.plugins["bob-ledger-tools"].api`; they must not import each other's `main.js`, matching freshness placement.

Expose immutable plain data with:

- Availability, local date, generation, policy validity/source, and warnings.
- Note path/name/type/lifecycle, effective limit, and limit provenance.
- READY, NEW, returned, and age-expired ROTTEN counts; excess and over flag.
- READY detail identities: path, one-based line, optional block ID, description.
- Summary evaluated notes, violating notes, and excess READY tasks.

The UI can combine returned/expired under ROTTEN; machine data should retain the distinction. Zero is valid; unknown has null counts/status rather than a false all-clear.

Version CLI JSON independently. Preserve `bob plan` compatibility unless intentionally adding a documented field. A new `ready_note_cap_exceeded` diagnostic does not change theme/link plan status or `plan.strict`.

### 9.2 Efficient invalidation

Build groups once per validated Tasks/Today/freshness/policy/metadata generation; `forNote(path)` is then an O(1) map lookup. Reuse the freshness memo and cache generation, which already detects updates reusing the same array object.

Invalidate on task-cache updates, relevant frontmatter edits, create/delete/rename, Today changes, local day rollover, and config changes. Reuse minute-tick recovery and UI debounce. Do not parse YAML or scan the vault independently for every row.

Use registered lifecycle events and render-component ownership to clean up listeners/widgets/timers. Reopening a note must not accumulate them. [Obsidian lifecycle guidance](https://docs.obsidian.md/plugins/guides/lifecycle-management).

### 9.3 Native foundation and consistency

Reuse `RichTask`, Tasks settings/dependency evaluation, freshness buckets, and `today_tasks`. Refactor enough scan access to use one index and one date anchor. The current freshness scan invokes several task scans; adding another full scan per group is wasteful and can mix generations.

Pin the note classifier and READY predicate with cross-language fixtures. Cover scalar/list/legacy bare types before claiming parity. Project OPEN/SHOWN are not READY.

Use the full graph even for a one-note report: dependencies may live elsewhere.

`Vault.process()` guards a per-file update; it is not a cross-file transaction or cross-device invariant. Keep existing snapshot guards and recovery. Remain advisory and reconcile after sync rather than pretending a preflight can enforce an absolute rule. [Obsidian Vault API](https://docs.obsidian.md/Plugins/Vault).

## 10. CLI design

Use a dedicated read-only **`bob ready`** command. `bob projects ready` understates area coverage; overloading `bob plan` obscures this file-level review diagnostic.

Proposed interface, following Bob format/root conventions and short aliases:

~~~sh
bob ready
bob ready --over
bob ready --note home.md --tasks
bob ready --format json
bob ready --bob-dir /path/to/vault --check
~~~

| Option | Alias | Behavior |
| --- | --- | --- |
| `--bob-dir DIR` | `-b` | Existing vault-root/environment convention. |
| `--check` | `-c` | Opt-in nonzero exit for a violation. |
| `--format human|json` | `-f` | Existing output-format convention. |
| `--help` | `-h` | Clear, alphabetically ordered help. |
| `--note PATH` | `-n` | Select an exact vault-relative eligible note. |
| `--over` | `-o` | Display violations only. |
| `--tasks` | `-t` | Include source READY tasks in human/JSON output. |

Use exact paths initially rather than ambiguous basenames. If extension omission is allowed, document it and reject ambiguous matches. Unknown/ineligible `--note` is an error, not a successful empty report.

Default output lists every eligible note, including zero-count notes. Show violations first, then the rest. Retain full-vault summary under display filtering; JSON exposes full and displayed totals.

Illustrative output:

~~~text
Ready load — 3 notes over · 7 READY tasks above limits
Default limit 5 · freshness-gated · 2026-10-01

  NOTE             KIND       READY    EXCESS   REVIEW WAITING
  Research         project     9/5      +4       2 new · 3 rotten
  Home             area        7/5      +2       1 new
  Bob capture      project     6/5      +1       —
  Reading          area        3/5       —       4 rotten
  Garden           project     0/5       —       —

  Review each crowded note; move an outcome or choose what can wait.
~~~

Use existing terminal-aware `Styler`: cyan names, subdued headers, red excess counts, display-width-aware alignment, meaningful plain labels. Honor `NO_COLOR`, omit ANSI when piped, and preserve full note identity. Wrap detail on narrow terminals. Unicode is optional; meaning survives plain output.

Illustrative JSON:

~~~json
{
  "ok": true,
  "schema_version": 1,
  "date": "2026-10-01",
  "definition": "dashboard_ready",
  "default_limit": 5,
  "summary": {
    "evaluated_notes": 1,
    "over_notes": 1,
    "excess_ready_tasks": 2
  },
  "rows": [
    {
      "path": "home.md",
      "kind": "area",
      "limit": 5,
      "limit_source": "config",
      "counts": {"ready": 7, "new": 1, "returned": 0, "rotten": 0},
      "excess": 2,
      "over": true
    }
  ],
  "warnings": []
}
~~~

Define optional task arrays and filter metadata in the actual schema.

Exit 0 for a successful informational report even if over; 1 for read/runtime failure; 2 for usage/global-config error; proposed 3 only when `--check` requests a violation exit. `--check --note` checks that selected note; without a note it checks the full set. `--over` is display-only. Keep structured errors valid JSON; distinguish command failure from a valid over-limit report.

Require no Obsidian process. CLI sees persisted files; editor projection may include unsaved text. Parity means identical inputs yield identical results, not that different snapshots always match.

## 11. Delivery and acceptance

### 11.1 Three bounded stages

1. **Contract and model:** define classification, READY membership, configuration, availability, schema, and shared fixtures. Implement native CLI and ledger-tools grouping.
2. **Review surfaces and feedback:** dashboard summary/table, picker capacity, note widget, and operation integration across the mutation families. These notifications are required scope, not discretionary follow-up.
3. **Polish/deploy:** adapt dashboard/templates, exercise actual Obsidian edit/reading/narrow layouts, update help/docs/plugin versions, and deploy changed plugin sources with `bob plugins sync`.

Update documentation currently stating native READY reporting is absent. Do not mutate reference memory as a display side effect. No automatic task-status, schedule, tag, block-ID, or freshness migration is needed.

### 11.2 Meaningful conformance tests

| Case | Expected |
| --- | --- |
| Limit 5, READY 0/4/5/6 | Only 6 violates; excess 1. |
| Confirm NEW in a note at 5 | 6 READY; confirmation succeeds; one warning. |
| READY task becomes ROTTEN | READY decreases, review count grows; no celebration. |
| Recurring TODO without fresh stamp | Count when part of existing exempt READY pool. |
| Configured custom TODO symbol | Same policy by TODO type. |
| `#hide`, `#Hide`, `#hide/x` | Match dashboard exclusions. |
| Future/dependency-blocked task with recent stamp | Excluded. |
| Temporary TODO Today member | Excluded until actual Today membership ends. |
| Release Next/Pending and unlink successfully | Evaluate result; warn only for growth beyond limit. |
| Ordinary sticky Next unlink | Lane preserved; no added READY. |
| One moved parent and three eligible child tasks | Count eligible source rows, not selected roots. |
| Move rewrites Today links/dependency IDs | Ownership, Today, graph remain consistent. |
| Complete dependency in another note | Evaluate newly unblocked dependent notes. |
| Priority-only edit of existing READY | No warning if count unchanged. |
| Repeated `7 → 8 → 9` | Each increase reflected; no daily suppression. |
| Failed/stale/cancelled/rolled-back operation | No false capacity-success message. |
| Editor/cache lag | Exact overlay or validated receipt; no fixed-delay guess. |
| Quoted/scalar/list/legacy types; nested paths | Native/plugin scope agrees. |
| Same basenames, duplicate IDs, identical wording | No silent merging/wrong ownership. |
| Override, bad override/global config, mobile defaults | Policy/provenance visible. |
| Missing daily note | Model establishes known empty Today; counts can remain available. |
| Cold cache/parser failure/unreadability | Unknown/incomplete, never zero/all-clear. |
| Rename/type edit/config edit/midnight/date rollover | Refresh without reload. |
| Reopen widgets repeatedly | No duplicate listeners/timers/badges. |
| Pipes/NO_COLOR/JSON errors/narrow terminal/check exit | Stable human/machine contract. |

Use shared vault/task vectors for Rust and JavaScript; separate handwritten expectations are insufficient parity evidence. Existing dashboard tests use stubs, so also test actual Tasks/Obsidian cache lag, unsaved editors, link resolution, and command-result Notices.

Suggested performance goals, **not measured claims**: warm O(1) note lookup; no per-row vault scan; coalesced paint within roughly a second of relevant cache updates; existing minute-tick recovery for time/config. Measure real-vault latency before adding a service or more caches.

## 12. Alternatives

| Approach | Strength | Limitation | Verdict |
| --- | --- | --- | --- |
| Dataview-only badge | Fast visual sketch. | Cannot own reliable command feedback; divergence on freshness/dependencies/CLI. | Prototype only. |
| Raw headless Tasks query by filename | Reuses query command. | Ungated NEW/ROTTEN, missing policy/ownership contract. | Incorrect final feature. |
| Hard cap/refused move or confirmation | Enforces some known operations. | Blocks valid review/routing; still loses to sync/manual edits. | Reject. |
| Automatic deferral/project creation | Removes warnings quickly. | Makes Bryan's priority/outcome decisions; can conceal work. | Reject. |
| Display first five tasks | Clean-looking list. | Hides the work needing review. | Reject. |
| Parent-area rollups including descendants | Aggregate pressure view. | Different ownership, cycles, double counts, penalizes project organization. | Separate future decision. |
| New plugin or persisted count frontmatter | Isolated ownership/easy queries. | Duplicates ledger/freshness; sync churn and staleness. | Extend ledger-tools. |
| Cap NEXT+PENDING instead | Addresses commitments directly. | Already exists; misses per-note READY concentration. | Keep alongside this feature. |

## 13. Trial and remaining uncertainty

Run a two-week observation period. Start at five, use numeric note overrides sparingly, and do not optimize for green badges.

Success means:

- Every violating note is discoverable and openable in one or two actions.
- Operation feedback matches final counts for the same snapshot.
- Review becomes easier/shorter without skipping NEW/ROTTEN.
- Resolutions clarify outcomes, commitments, or dependencies; cosmetic splitting and arbitrary deferrals are uncommon.
- Notification volume is tolerable; batching still reflects each over-limit increase.
- Native/plugin fixtures agree; unavailable data never becomes success.

Do not add persistent telemetry in v1. A few human observations during review can determine whether the policy helps.

Questions for a real-vault trial or implementation spike:

1. Is five appropriate for broad areas? No inspected evidence establishes a universal optimum.
2. Would many overrides indicate separate area/project defaults or another policy?
3. Can current JavaScript parsing afford exact graph-aware overlays? If not, validate receipt attribution/latency.
4. How do Notice actions work with keyboard/screen readers and rapid confirmations in the actual Obsidian build?
5. Is identical customized global policy needed on mobile? Current external config does not provide it automatically.

This research establishes a concrete direction, not runtime fidelity from source inspection alone.

## 14. Source index

Primary external sources:

- [David Allen Company, Managing projects with GTD](https://gettingthingsdone.com/2017/05/managing-projects-with-gtd/): outcomes, parallel next actions, dependent future actions.
- [David Allen Company, Someday Maybe](https://gettingthingsdone.com/2010/10/what-goes-on-a-someday-maybe-list/): reviewed incubation for actions/projects.
- [The Kanban Guide, May 2025](https://kanbanguides.org/the-kanban-guide/): start/finish boundaries and WIP.
- [Obsidian Vault](https://docs.obsidian.md/Plugins/Vault): Notice example, enumeration, per-file update guards.
- [Obsidian lifecycle management](https://docs.obsidian.md/plugins/guides/lifecycle-management): events/interval cleanup.
- [W3C use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html): supplementary text/shape.
- [W3C status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html): announced feedback without taking focus.

Repository evidence was read from authorized local checkouts. Pinned links identify inspected revisions; they do not imply repository content was fetched through the web.

Audited memory informed this design: `obsidian.md`, `cli_rules.md`, `sase_artifacts.md`, sticky-lanes/freshness-gated-READY/ledger-Today decisions, and the glossary. This report does not alter them.

## 15. Recommended solution

Implement **Ready load** as a soft, source-file-based limit of **5 freshness-gated READY tasks per area/project**, configurable globally through `plan.max_ready_per_note` and locally through optional `ready_limit`.

Extend **bob-ledger-tools** with one validated grouped READY model for the `dash.md` summary/diagnostics, current-note widgets, and destination-picker counts. Add native **`bob ready`** with readable colored output and versioned JSON. Warn once per successful Bob operation when an affected note's READY count grows beyond its limit, using actual resulting membership and accounting for freshness, Today, nested tasks, dependencies, and cache lag.

Keep global READY and existing NEXT/PENDING budgets visible. Preserve tasks and valid user gestures. The purpose is to make a crowded choice set easy to notice and thoughtfully review; the sixth task should never become an obstacle or a reason to stop confirming work.
