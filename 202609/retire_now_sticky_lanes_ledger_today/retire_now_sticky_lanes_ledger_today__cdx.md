# Replacing `#now` with Today / Pending / Next

**Researcher:** cdx  
**Date:** 2026-09-30  
**Scope:** independent review of the proposed Bob workflow; no peer-swarm reports were consulted

## Executive conclusion

The proposed workflow is directionally better than the new `#now` design, but I would not implement it exactly as stated.

The strong idea is to separate the daily plan from durable task state:

- **Today** should mean “this open task has a live, dedicated Task Link somewhere under a recognized Pomodoro in today’s daily note.” It should be derived at query/render time from the ledger, not written onto the task.
- **Pending** should be the durable `[/]` lane for work that has started or needs a later review, whether or not it remains on today’s ledger.
- **Next** should be the durable `[*]` lane for committed, actionable work that has not yet started.
- **Ready** should remain `[ ]` and continue to be the reservoir used only after Pending and Next have been reviewed.

This makes `#now` redundant. It also matches the proposed morning review better than the present system, where the ledger, Next, WIP, and NOW partially encode overlapping ideas.

My main adjustment is important: **do not implement Today with either a Tasks file-path filter or a machine-managed `#today` tag.** A file-path filter selects tasks physically stored in the daily note, not tasks targeted by links from that note. A managed tag would work, but would duplicate ledger state into many task files and preserve the background-write/sync failure mode that motivated the concern about `#now` automation. Instead, compute a canonical set of `(target note path, block ID)` identities from today’s ledger and partition the dashboard in one pass. A small versioned dashboard component in Bob Ledger Tools is the best long-term home.

I also recommend changing more than `bob task-status-hooks`: several capture and Obsidian unlink gestures currently demote a task immediately. If those are left alone, Pending will still be wiped before the hook ever runs.

## What the live system says today

I inspected the current bob-cli implementation, the Bob Ledger Tools and Navigation Hotkeys sources, and the live vault through read-only `bob query`, `bob plan`, and `bob task-status-hooks --dry-run` calls.

The dashboard currently returns:

| Section | Visible tasks |
| --- | ---: |
| NOW | 0 |
| WIP | 53 |
| NEXT | 27 |
| READY | 186 |

The current plan has four open Pomodoros and six budgeted Task Links. The status hook reports seven direct open-Pomodoro references because the exempt GTD Pomodoro also has a Task Link. It also sees 74 references in the preceding daily note and 82 recent-activity references across its rolling window. That large historical root set explains why status and day membership are not interchangeable.

There are no current `#now` tasks. This makes removal cheap in terms of user data, although the feature has already spread through capture grammar, completion, plan budgeting, plugin toggles, documentation, and tests.

The empirical file-path test is decisive:

```text
bob query --tasks 'path includes 2026/20260930'
```

returns exactly one task: the `^gtd` task physically stored in `2026/20260930.md`. It misses the six cross-note tasks linked from the open plan. This agrees with the Tasks documentation: `task.file.path` is the path of the file containing the task, not the path of a file linking to it. See the official [Tasks filter documentation](https://publish.obsidian.md/tasks/Queries/Filters).

The accepted project decisions explain how the overlap arose:

- `#now` is a user-owned weekly bet, deliberately independent of status and links.
- Next and In Progress are currently derived from the ledger and rolling recent activity.
- The `#now` decision is explicitly a two-week trial and says to reopen the decision if NOW is ignored.

The observed count of zero is not enough, by itself, to prove a failed trial on its first day. It is enough to show that there is no migration burden and that the proposed simpler model is worth testing now.

## Critique of the proposal

### What is good

1. **The daily file is already the best source of truth for Today.** Adding a Task Link is an explicit selection gesture, the ledger shows capacity, and removing the link has an obvious meaning. A second hand-maintained tag adds no information.

2. **Durable Pending solves a real failure mode.** A task delegated to an agent swarm may need review hours later without occupying a current Pomodoro. Removing its link should not erase the fact that it is underway or awaiting attention.

3. **The morning review becomes legible.** Review Pending obligations, review the Next commitment pool, add selected work to Today, then draw from Ready if capacity remains.

4. **A single checkbox lane is easier to act on than a checkbox plus a weekly tag.** If Next becomes user-owned, `#now` is largely a second representation of the same commitment decision.

### What needs correction

#### 1. Today, status, and blockedness are three different dimensions

The proposal still risks treating one checkbox character as if it can encode all three:

| Dimension | Question | Recommended owner |
| --- | --- | --- |
| Daily selection | Is this on today’s ledger? | Derived from today’s Task Links |
| Workflow lane | Is it Ready, Next, or Pending? | User gestures, except obvious capture transitions |
| Actionability | Is a dependency open or is the schedule in the future? | Derived from dependency/schedule facts |

Today must be orthogonal to status. A Today task may be Next or Pending. During a transient inconsistency it may even still be Ready; the dashboard should show it rather than silently lose a ledger selection.

Blockedness is the harder edge. The current hook overwrites `[ ]`, `[*]`, or `[/]` with `[?]` and stores no previous status. When the block clears, it reconstructs a lane from current/recent ledger reachability. Once Next and Pending become durable authored lanes, that recovery rule can destroy authored state.

I recommend this explicit policy adjustment for the first implementation:

- Link removal alone never changes Next or Pending.
- Derived schedule/dependency blocking may continue to override a lane during the transition, but recovery to Ready is an intentional re-triage, not restoration.
- Document that a future schedule means “leave the active commitment lanes”; do not promise that a scheduled task will automatically regain Next or Pending.
- If preserving a lane across blocking later proves necessary, treat blockedness as a separate overlay rather than adding another hidden tag/property. One checkbox cannot losslessly encode both lane and blocker state.

This is a narrower guarantee than “the hook never wipes Pending,” but it addresses the stated agent-swarm case: unlinking a still-Pending task does not demote it. It also avoids inventing fragile `previousStatus` metadata before actual use demonstrates a need.

#### 2. “Every Task Link is Next or Pending” needs terminal and conflict exceptions

Historical completed/struck links, canceled tasks, unresolved targets, and dependency-blocked targets exist. The useful invariant is:

> Creating a live link to an actionable Ready task promotes it to Next; linking an existing Next or Pending task preserves its lane; starting work promotes Next to Pending; unlinking preserves the lane.

That is more precise than requiring every link occurrence to correspond to one of two statuses.

#### 3. Persistent Pending and Next can become the new pile

The current hooks clear stale Next and some stale In Progress tasks. Removing those clear operations solves unwanted demotion but also removes garbage collection. The morning review must become an actual lifecycle owner.

I would keep a cap for the total actionable Next lane, renamed from `max_now` to `max_next`, and add a non-blocking stale-Pending warning later if the review does not keep up. Count the entire Next lane, including tasks also shown under Today, because Today is only a display partition and should not make commitments disappear from the cap.

#### 4. Existing statuses cannot simply be frozen at cutover

The live dashboard has 80 WIP/Next tasks. Those values were produced under the old derived and rolling-recent rules. Treating all 80 as deliberate authored choices would turn an implementation artifact into a permanent queue.

The cutover needs a one-time review report. There is no safe fully automatic migration beyond:

- map any surviving `#now` task to Next (currently none);
- preserve the lanes of today’s live linked tasks;
- list all other WIP/Next tasks for explicit keep/demote decisions.

## Evaluating the Today implementation options

### Option A: a Tasks file-path filter — reject

This cannot answer the question. Tasks path filters operate on the task’s owner file. They do not perform a reverse block-link join. The current live test found one local daily task and missed the six cross-note targets.

Dataview’s `file.inlinks` does not repair this cleanly. It is page-level metadata: it can tell that the daily file links somewhere into a note, but selecting that note’s tasks would include unrelated tasks in the same note. It does not by itself express “this exact task block was the target.” Dataview documents `file.inlinks` as incoming page links and separately exposes task/list `path`, `outlinks`, and `blockId`; see [page metadata](https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-pages/) and [task/list metadata](https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-tasks/).

### Option B: a hook-managed `#today` tag — feasible fallback, not preferred

This is the smallest way to retain ordinary Tasks code blocks:

```text
TODAY:   not done; tags include #today
PENDING: status.type is IN_PROGRESS; tags do not include #today
NEXT:    status.name includes Next; tags do not include #today
READY:   status.type is TODO; tags do not include #today
```

The sections are easy to make mutually exclusive. The cost is architectural:

- the tag is a materialized cache of facts already present in the daily ledger;
- every add/remove/day rollover rewrites target task files;
- missed runs or partial failures leave stale membership;
- open-editor and multi-machine sync conflicts remain possible;
- the hook must scan and remove stale tags vault-wide, including terminal tasks and renamed/moved targets;
- debugging now requires asking whether the ledger or the cache is wrong.

If implementation time rules out a dynamic dashboard, this is acceptable as an explicitly machine-owned, reserved tag. It should never be a user gesture and should be reconciled from scratch after structural cleanup. But I would regard it as an interim cache, not the model.

### Option C: a dynamic canonical-identity partition — recommend

Build the Today set from the daily note and then partition all visible tasks once. The canonical key is the same one already used by `task-status-hooks`: normalized vault-relative target path plus block ID.

Recommended Today membership:

- the selected current daily note only;
- recognized Pomodoro entries, both completed and open;
- a live, dedicated Task Link whose list-item body is the link (allowing the normal marker decoration), not an arbitrary block link mentioned in prose;
- exclude struck, dropped, completed, and canceled targets from the open-task result;
- de-duplicate repeated work sessions by canonical identity;
- resolve explicit paths first and unique case-insensitive basenames second, warning rather than guessing on ambiguity;
- include same-note links such as the GTD task;
- if a linked task is derived-blocked, keep it visible in Today with a warning/style rather than silently violating “all selected work.” Future-schedule gestures normally prune the link anyway.

Then apply this precedence:

```text
Today   = visible open tasks whose canonical identity is in today_ids
Pending = visible IN_PROGRESS tasks not in Today
Next    = visible Next-status tasks not in Today or Pending
Ready   = visible TODO tasks not in Today, Pending, or Next
```

Use the dashboard’s existing visibility defaults for the last three lanes (`#hide`, templates/conflicts, future schedules, dependency blocking). Today should be slightly stricter about identity but slightly more permissive about displaying a conflict, since the ledger itself is an explicit user selection.

A one-pass partition is superior to four independent queries because mutual exclusivity becomes a property of the algorithm rather than a convention repeated in query text.

Dataview can render interactive source tasks using `dv.taskList`, and its JavaScript API is intended for complex views and plugin interoperation; see the official [Dataview code-block API](https://blacksmithgu.github.io/obsidian-dataview/api/code-reference/). However, I would not leave substantial ad hoc JavaScript in `dash.md`.

## Recommended implementation shape

### 1. Add a versioned dashboard component to Bob Ledger Tools

Bob Ledger Tools already:

- reads today’s daily note;
- obtains all Tasks plugin task objects;
- subscribes to daily-note metadata and Tasks-cache updates;
- exposes a versioned API;
- renders the live `bob-plan` block.

Extend it with a `bob-dashboard` block and an API such as `dashboardModel()` or `taskLanes()`. The component should compute canonical Today identities, partition the task cache, and render Today / Pending / Next / Ready together. Using the Dataview plugin’s public API for interactive task rendering is reasonable; if Dataview is unavailable, render a clear degraded-state message rather than stale data.

Keep the daily note declarative:

````markdown
```bob-dashboard
```
````

Do not embed the resolver and partition logic directly in the vault note.

### 2. Share the semantic contract with bob-cli

The Rust hook already has the mature parser/resolver for Pomodoros, block links, archive exceptions, ambiguity, cancellation, and normalized identities. Refactor enough of it into a read-only library surface and expose a diagnostic JSON command (for example `bob today --format json` or a dashboard mode under `bob query`). This gives shell/tests a canonical oracle even if Obsidian rendering remains JavaScript.

The plugin and CLI cannot literally share code, so use shared conformance fixtures. The existing plan-budget implementation already accepts a Rust/JavaScript mirror; Today identity needs the same discipline.

### 3. Make Next and Pending authored lanes

Change `bob task-status-hooks` so ordinary ledger reachability no longer:

- promotes Ready to Next;
- propagates Next/In Progress down task-link dependency transclusions;
- clears unreachable Next;
- clears unlinked area/project In Progress via rolling recent activity.

Keep its structural ledger cleanup, completed/canceled reference retirement, marker repair, task-section grouping, and derived Blocked behavior during the first migration.

Keep obvious event-driven transitions in the commands that know user intent:

- linking an actionable Ready task: Ready → Next;
- linking Next or Pending: preserve;
- starting/working a task: Next → Pending;
- completing/canceling: terminal status;
- dropping or merely unlinking: preserve Next/Pending;
- explicit demotion: a separate deliberate gesture.

The distinction between “unlink” and “demote” should be visible in command names, help, and Notices.

### 4. Fix every unlink path, not only the hook

Current behavior is distributed. In particular, Navigation Hotkeys / Block ID Prompt documents Ctrl+Shift+Enter on a selected Task Link as deleting the link **and setting the target Open**; the explicit `@route+id!` toggle also couples link removal to Next → Ready. Pomodoro `~K` drop relies on the next hook to demote.

Under the new model:

- `~K` becomes naturally status-preserving once hook clearing is removed;
- selected-Task-Link unlink should preserve status by default;
- an explicit “remove from Next/Pending” operation should remain available, but it must be a distinct, clearly authored transition;
- work-summary capture may still accompany a Pending → Ready demotion when the user explicitly chooses that action.

This is necessary to satisfy the agent-swarm example.

### 5. Replace NOW budgeting deliberately

After the new dashboard and lane semantics are proven:

- remove `#now` capture grammar and completion candidate;
- remove Alt+N and the pinned `#now` property row;
- replace the NOW chip/cap with a NEXT chip/cap if the cap remains useful;
- count all actionable Next tasks, including those displayed under Today;
- remove the NOW query from `dash.md`;
- supersede, rather than edit, the accepted `#now` and derived-active-status decision records.

The status registry can keep the name “In Progress” initially while the dashboard heading says “Pending.” Renaming the Tasks status to Pending touches more integrations and can be a later cosmetic migration after the behavior is stable.

## Rollout plan

1. **Instrument first.** Add read-only Today identity output and a temporary dashboard preview. Compare it with the ledger by hand for same-note links, completed/open Pomodoros, aliases, embeds, duplicates, struck links, canceled tasks, and ambiguous targets.
2. **Land the one-pass dashboard.** Keep existing NOW/WIP/NEXT blocks beside it briefly as a comparison, but do not add `#today`.
3. **Generate a cutover inventory.** Snapshot the 53 WIP and 27 Next visible tasks and classify current-day identities separately. Do not automatically freeze or demote the remaining tasks.
4. **Change unlink semantics and hooks together.** There must not be a window where the hook preserves Pending but the interactive unlink gesture still demotes it.
5. **Run the authored-lane trial.** For at least several working days, use Today / Pending / Next / Ready and record whether Pending/Next accumulate or whether blocked recovery loses needed commitments.
6. **Remove `#now` surfaces.** The current count is zero, so no tag migration is needed if that remains true. Replace the decision record with a superseding one that documents the new ownership model.

## Acceptance criteria and tests

- Every visible open task appears in at most one of Today, Pending, Next, Ready.
- Every resolvable, nonterminal dedicated live Task Link in today’s recognized Pomodoros appears in Today exactly once.
- Repeated links across completed/open Pomodoros do not duplicate a task.
- Struck, dropped, completed, canceled, ambiguous, and missing targets follow explicit tested rules.
- Same-note daily links resolve correctly.
- Removing a link from a Pending or Next task leaves the checkbox unchanged after both the immediate gesture and a subsequent hook run.
- Explicit demotion still changes the lane and is not conflated with unlinking.
- A Ready task linked into today becomes Next and immediately appears only in Today.
- Starting it makes it Pending without duplicating it in the Pending section while it remains Today.
- Removing its last Today link moves it from Today to Pending without any task-file mutation at unlink time except the intended ledger edit.
- Future schedule and dependency blocking behavior is tested separately from link removal and documented as re-triage, not hidden restoration.
- Rust and JavaScript Today-identity fixtures stay byte-for-byte/conceptually conformant.
- The dashboard updates on both daily-note and Tasks-cache changes and has an explicit degraded state if either Tasks or Dataview is unavailable.

## Recommended solution

Adopt Today / Pending / Next / Ready and retire `#now`, but implement **Today as a read-only canonical projection of today’s Pomodoro Task Links**. Render all four lanes from one versioned Bob Ledger Tools dashboard component so exclusivity is guaranteed by one partition function. Make Next and Pending durable authored lanes; remove ledger-driven promotion/clearing from `task-status-hooks`; and change every unlink gesture to preserve those lanes unless the user explicitly asks to demote.

Do not use a file-path filter—it answers the wrong question. Avoid `#today` unless a short-lived fallback is required. Before cutover, manually triage the existing derived WIP/Next population, and explicitly accept that dependency/future-schedule blocking re-triages to Ready unless and until blockedness is redesigned as a separate overlay.

This gives the simplest durable mental model:

> The ledger says what is on Today. The checkbox says where the task lives in the workflow. Dependencies and schedules say whether it is actionable.

