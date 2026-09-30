# Retiring `#now`: Architectural Analysis of a `Today / Pending / Next / Ready` Task Taxonomy

- **Author:** researcher `gem` (5-researcher swarm)
- **Date:** 2026-09-30
- **Context:** `bob-cli`, `bob-plugins`, `bob-mac-capture`, Bob Obsidian Vault (`dash.md`)
- **Status:** Research & Architectural Proposal

---

## 1. Executive Summary

Bryan's intuition that the `#now` tag was a mistake is **correct**. `#now` was introduced on 2026-09-29 as an emergency band-aid to resolve the *status-lock trap*—a trap created because `bob task-status-hooks` had monopolized the `[*]` (Next) and `[/]` (In Progress) checkbox statuses to reflect only the immediate, daily Pomodoro ledger. 

This created an inverted and confusing task taxonomy:
1. The checkbox status `[*] Next` did not mean GTD Next Action; it meant "currently linked in today's open Pomodoro".
2. The user was forced to create an orthogonal tag (`#now`) to represent what standard GTD calls "Next Actions" (the weekly commitment horizon).
3. The dashboard (`dash.md`) suffered from cognitive clutter and redundancy, displaying tasks in both `NOW` and `NEXT`/`WIP`.
4. Crucially, modern autonomous workflows—specifically delegating multi-hour work to agent swarms (like SASE)—broke down: unlinking an in-flight task from today's Pomodoro ledger caused `task-status-hooks` to aggressively wipe `[/]` and reset it back to `[ ]` Ready, burying it in the massive backlog.

Bryan proposed:
- Retiring `#now` as the weekly commitment tag.
- Reclaiming `[*]` Next as the user-owned weekly commitment pool (GTD Next Actions).
- Reclaiming `[/]` In Progress / Pending as a persistent, non-decaying in-flight status so tasks delegated to agents or awaiting review can be unlinked from today's ledger without losing state.
- Querying for tasks linked in today's ledger using either a query file-path filter or a machine-managed `#today` tag.
- Replacing the sections in `dash.md` with **mutually exclusive** `TODAY`, `PENDING`, `NEXT`, and `READY` sections.

### Primary Verdict & Recommendations
Bryan's proposed plan is **sound, elegant, and highly recommended**, subject to **three essential adjustments**:

1. **A query-based "file path filter" is technically impossible; a machine-managed `#today` tag is mandatory.**
   Because tasks live in project/area notes (`dev.md`, `sase.md`) while Pomodoro links live in daily notes (`YYYY/YYYYMMDD.md`), Obsidian Tasks queries cannot filter by incoming block links or backlinks. Tasks has no graph-traversal capability, and `bob-cli`'s native Rust Tasks engine operates in an isolated JavaScript sandbox with strict parity constraints. Therefore, `bob task-status-hooks` **must manage a `#today` tag** on the task lines themselves.
2. **Preventing Status Inflation requires explicit Caps and Lints for `NEXT` and `PENDING`.**
   Automatic decay was originally built because unmanaged statuses explode (reaching 50 `[/]` and 25 `[*]` tasks in September 2026). If `task-status-hooks` stops demoting `[*]` and `[/]`, human discipline alone will not prevent backlog rot. We must repurpose the plan budget engine:
   - Cap `NEXT` at 15 (inheriting `plan.max_now`, renamed `plan.max_next`).
   - Cap `PENDING` at 5 (WIP limit for in-flight/delegated work).
   - Display active counters on `dash.md` chips that turn red when caps are exceeded, backed by `bob plan` lints.
3. **Mutual Exclusivity on `dash.md` must be enforced via Boolean Tag/Status Query Filters.**
   Using `#today` and standard Tasks filters, the four sections become cleanly and mathematically mutually exclusive:
   - `TODAY`: `tags include #today`
   - `PENDING`: `status.type is IN_PROGRESS` AND `tags do not include #today`
   - `NEXT`: `status.name includes Next` AND `tags do not include #today`
   - `READY`: `status.type is TODO` AND `status.name does not include Next` AND `tags do not include #today`

---

## 2. Root Cause Analysis: How the Ecosystem Got Here

### 2.1 The 2026-09-29 Status-Lock Trap
To understand why `#now` was created, we must revisit the measurements documented in `now_tag_vs_in_progress_status.md` and `decisions/now-tag-is-user-owned`:
- Under `decisions/task-status-is-derived`, `bob task-status-hooks` derived `[*]` (Next) solely from open Pomodoros in today's daily note, and rolled back `[/]` (In Progress) in area and project notes once neither today's ledger nor yesterday's ledger linked it.
- When Bryan unlinked a task from today's ledger (e.g. to clean up his daily note), the next run of `task-status-hooks` immediately stripped `[*]` and demoted the task to `[ ]` Ready.
- In a vault with hundreds of Ready tasks, demoting a task to `[ ]` effectively hid it from view.
- To avoid losing track of work, Bryan was forced to keep tasks linked in today's ledger indefinitely.
- This produced the **status-lock trap**: the daily ledger accumulated 80 queued links—58% of which had gone a week or more without a single Pomodoro (`🍅`).

### 2.2 Why `#now` Was a Flawed Band-Aid
Instead of relaxing the rigid derivation rules of `task-status-hooks`, the decision was made to introduce `#now`:
- `#now` was defined as a user-owned tag representing "this week's bet".
- The checkbox statuses remained ephemeral: `task-status-hooks` continued promoting tasks to `[*]` on link and demoting them to `[ ]` on unlink.
- While this solved the immediate problem of allowing links to be dropped without forgetting the task, it introduced severe secondary problems:

| Dimension | The `#now` + Derived Status Model | Real-World Failure |
| :--- | :--- | :--- |
| **Terminology** | `Next` = Today's open Pomodoro<br>`#now` = This week's horizon | **Inverted GTD Semantics.** In GTD, "Next" is the horizon of available actions, and "Today" is today's execution. Bob inverted this completely. |
| **Dashboard UI** | `dash.md` had `NOW`, `WIP`, `NEXT`, `READY` | **Clutter & Duplication.** A task linked in today's Pomodoro appeared under `NOW Tasks` *and* `NEXT Tasks` (or `WIP Tasks`). |
| **Capture Overhead** | Must type `#now` or use Alt+N hotkey | **Friction.** Capture required syntax gymnastics: `Task text #now @route^id`. Trailing placement could trigger syntax warnings. |
| **Async Agent Swarms** | `[/]` wiped if unlinked for > 24 hours | **Broken Delegation.** When launching a 3-hour agent swarm, Bryan could not clear the task from today's focus without the task losing its `[/]` status on the next daily rollover. |

---

## 3. Technical Evaluation of Bryan's Proposed Mechanics

### 3.1 Mechanism 1: Querying Today's Tasks (File Path Filter vs. `#today` Tag)

Bryan suggested two possible ways to query for tasks in today's ledger:
1. A file path filter in the Obsidian Tasks query.
2. A machine-managed `#today` tag managed by `bob task-status-hooks`.

#### Why the File Path Filter Fails Completely
In Obsidian and `bob-cli`, task architecture is split:
- **Task definitions** live in domain notes (e.g. `sase.md`, `dev.md`, `Projects/Alpha.md`):
  ```markdown
  - [*] #task Ship parser refactor ^parser-refactor
  ```
- **Task links** live in daily notes (e.g. `2026/20260930.md`) under `## Pomodoros`:
  ```markdown
  - [ ] Implement parser (0900-0930)
    - [[dev#^parser-refactor]]
  ```

In the Obsidian Tasks plugin and `bob-cli`'s native Rust Tasks engine (`src/native/dataview/tasks/`):
- Tasks queries evaluate tasks note-by-note and line-by-line.
- The `path includes ...` filter and `filter by function task.file.path ...` only inspect the path of the file **where the task definition is located**.
- For `^parser-refactor`, `task.file.path` is `"dev.md"`, never `"2026/20260930.md"`.
- Obsidian Tasks **has no backlink or incoming-link query capability**. The `Task` JavaScript object in Tasks contains properties like `task.tags`, `task.description`, `task.status`, `task.file`, and `task.blockLink`, but has no `task.inlinks` or graph metadata.
- Furthermore, `bob query --tasks` executes in an isolated QuickJS/V8 sandbox with no access to Obsidian's runtime `metadataCache`.
- **Conclusion:** It is technically impossible for an Obsidian Tasks query to filter tasks by incoming block links from today's daily file.

#### Why the Machine-Managed `#today` Tag Succeeds
Because Obsidian Tasks only filters on intrinsic line properties, **the task line itself must carry a marker**.
A tag managed by `bob task-status-hooks` is the cleanest, least invasive mechanism:
- When a task has an active block link in today's open Pomodoros, `task-status-hooks` ensures `#today` is on the task line.
- When the link is removed, or when a new day note becomes active, `task-status-hooks` removes `#today`.
- **Write Footprint:** This does not increase vault write churn. Previously, `task-status-hooks` already opened `dev.md` and edited column 3 to change `- [ ]` to `- [*]` and back. Editing `#today` on the exact same line uses the exact same guarded write pipeline (`write_guarded`).

### 3.2 Tag Placement and Formatting Rules
To ensure zero corruption with trailing Dataview fields (`[priority:: high]`, `[created:: ...]`) and block IDs (`^id`):
- `#today` should always be placed immediately after the global filter `#task`:
  ```markdown
  - [*] #task #today Ship parser refactor [created:: 2026-09-30] ^parser-refactor
  ```
- Stripping `#today` is a deterministic replacement:
  ```rust
  // Regex: replace whole tag following #task
  let cleaned = line.replace("#task #today", "#task");
  ```
- This guarantees that trailing metadata, block IDs, and user description text remain completely untouched.

### 3.3 Checkbox Status Lifecycle Under the New Architecture

Under the new model, we establish a clean separation between **Horizon** (Checkbox Status) and **Daily Execution** (Tag):

| Dimension | Checkbox Status (`[*]`, `[/]`, `[ ]`, `[?]`) | `#today` Tag |
| :--- | :--- | :--- |
| **Meaning** | Lifecycle Horizon & Workflow State | Immediate Daily Execution Presence |
| **Ownership** | User-owned / sticky (with machine safety caps) | 100% Machine-managed by `task-status-hooks` |
| **Persistence** | Multi-day / Multi-week | Strictly 24 hours (cleared on daily rollover or link removal) |

#### The Status State Machine:
1. **`[ ]` Ready:** Backlog item. Unblocked, unscheduled, not yet committed.
2. **`[*]` Next:** The user-owned commitment pool (replacing `#now`).
   - *How it is set:* Promoted manually by Bryan during GTD review, or promoted automatically by `bob capture` / `task-status-hooks` when pulled into today's ledger.
   - *Persistence:* **Sticky.** Unlinking a task from today's ledger strips `#today`, but **leaves `[*]` intact**. It remains in `dash.md#NEXT Tasks` until Bryan starts it, finishes it, or demotes it back to Ready.
3. **`[/]` In Progress / Pending:** Active or in-flight execution.
   - *How it is set:* Set via `=x` Pomodoro session close, or set manually when work begins.
   - *Persistence:* **Sticky.** When Bryan delegates work to an agent swarm, he unlinks the task from today's Pomodoro ledger. `task-status-hooks` strips `#today`, but **leaves `[/]` intact**. The task moves immediately to `dash.md#PENDING Tasks`.
4. **`[?]` Blocked:** Derived state (unchanged). Overrides all other states if an open `dependsOn` target exists or if `[scheduled:: YYYY-MM-DD]` is strictly in the future.

---

## 4. Comprehensive Critique of Bryan's Proposal

### 4.1 What Makes This a Great Idea?

1. **Restores Natural GTD Semantics:**
   In standard GTD:
   - "Next Actions" is the inventory of next actionable steps across active projects.
   - "Daily Focus" is what you choose to execute today.
   Calling the weekly inventory `Next` (`[*]`) and today's execution `Today` (`#today`) aligns the tool with 20+ years of proven GTD cognitive ergonomics.

2. **Solves the Asynchronous Agent Swarm Dilemma:**
   Modern agent swarms (SASE) take 1 to 4 hours to execute complex tasks. 
   - Keeping the task linked under an open Pomodoro while waiting for agents clutters the active ledger and distorts Pomodoro link counts.
   - Under the old model, unlinking it demoted it to `[ ]` Ready after 24 hours.
   - Under the proposed model, unlinking it keeps it as `[/]`, placing it in `PENDING Tasks`. It remains prominent on `dash.md` for morning review without being in Bryan's face during daily Pomodoro execution.

3. **Eliminates Dashboard Duplication:**
   By enforcing strict mutual exclusivity across `TODAY`, `PENDING`, `NEXT`, and `READY`, each task appears in **exactly one section** on `dash.md`. Moving a task into today's ledger removes it from `NEXT` and places it in `TODAY`.

4. **Drastically Reduces Capture & Authoring Friction:**
   Bryan no longer has to remember to type `#now` or manage `#now` tags. Capture with `@route^id` simply creates or links a task, which automatically becomes `[*]` and receives `#today`.

### 4.2 Critical Risks and Required Adjustments

While the concept is excellent, adopting it without safeguards would recreate the exact failure that led to `#now` in the first place: **Status Inflation**.

#### Risk 1: The Return of Status Inflation (The 50 WIP Problem)
- **The Danger:** Why did `task-status-hooks` originally have aggressive decay? Because Bryan discovered that humans do not manually demote tasks. Without decay, tasks marked `[/]` or `[*]` accumulated until there were 50 in-progress tasks and 25 next tasks.
- **Adjustment 1: Strict Visual Caps on `dash.md`.**
  We must enforce explicit caps on the dashboard chips:
  - `NEXT`: Cap at 15 (e.g. `NEXT 8/15`). Turns bright red if > 15.
  - `PENDING`: Cap at 5 (e.g. `PENDING 2/5`). In-flight work should be strictly bounded. Turns bright red if > 5.
- **Adjustment 2: Lints in `bob plan`.**
  Extend `bob plan` to check whole-vault active statuses:
  - `next_cap_exceeded`: Emitted when unblocked `[*]` tasks exceed `plan.max_next` (default 15).
  - `pending_cap_exceeded`: Emitted when `[/]` tasks exceed `plan.max_pending` (default 5).

#### Risk 2: Stale Delegated Work in `PENDING`
- **The Danger:** A task delegated to an agent swarm might fail, or an external dependency might stall. If `PENDING` never decays, it could become a dumping ground.
- **Adjustment 3: Stale Age Visibility in the Morning Review.**
  In `dash.md#PENDING Tasks`, sort tasks by modification date or show relative age. During the morning GTD review, any task in `PENDING` for > 3 days must be actively triaged (reopened into `TODAY`, blocked `[?]`, or demoted to `READY`).

#### Risk 3: Transcluded Dependency Promotion
- **The Question:** If a task in today's ledger has transcluded dependencies (`![[note#^subtask]]`), how are they handled?
- **Adjustment 4: Transcluded Dependencies Inherit `#today`.**
  To work on a parent task today, its immediate blocking transclusions must also be worked on today. `bob task-status-hooks` must continue traversing transcluded dependency chains, applying `#today` (and promoting to `[*]`) so they appear in `dash.md#TODAY Tasks`.

---

## 5. The New Dashboard Architecture (`dash.md`)

### 5.1 Mutual Exclusivity Matrix
To achieve Bryan's requirement that a task appears in only one section, the query criteria must form a complete, non-overlapping partition of all non-blocked, open tasks:

| Section | Checkbox Status | `#today` Tag | Query Filter Definition |
| :--- | :--- | :--- | :--- |
| **TODAY** | `[*]` or `[/]` | **Yes** | `tags include #today` |
| **PENDING** | `[/]` (In Progress) | **No** | `status.type is IN_PROGRESS`<br>`tags do not include #today` |
| **NEXT** | `[*]` (Next) | **No** | `status.name includes Next`<br>`tags do not include #today` |
| **READY** | `[ ]` (Todo) | **No** | `status.type is TODO`<br>`status.name does not include Next`<br>`tags do not include #today` |

*Note: Blocked tasks (`[?]`) and future-scheduled tasks are excluded from all four sections by `TQ_extra_instructions` (`is not blocked`).*

### 5.2 Obsidian Tasks Query Blocks for `dash.md`

Replace lines 279–304 in `dash.md` with:

````markdown
### TODAY Tasks

```tasks
not done
tags include #today
sort by status
sort by priority
```

### PENDING Tasks

```tasks
not done
status.type is IN_PROGRESS
tags do not include #today
sort by priority
```

### NEXT Tasks

```tasks
not done
status.name includes Next
tags do not include #today
sort by priority
```

### READY Tasks

```tasks
not done
status.type is TODO
status.name does not include Next
tags do not include #today
sort by priority
```
````

### 5.3 DataviewJS Header Chips Configuration

The DataviewJS chip bar at the top of `dash.md` should be updated to reflect the new taxonomy:

```javascript
// Caps configuration
const NEXT_CAP = 15;
const PENDING_CAP = 5;

// In DataviewJS count evaluation:
const counts = { today: 0, plan: "–", pending: 0, next: 0, ready: 0, blocked: 0 };

counts.today = active.filter(t => !dependencyBlocked.has(t) && t.tags.includes("#today")).length;
counts.pending = active.filter(t => !dependencyBlocked.has(t) && t.status.type === "IN_PROGRESS" && !t.tags.includes("#today")).length;
counts.next = active.filter(t => !dependencyBlocked.has(t) && t.status.name.includes("Next") && !t.tags.includes("#today")).length;
counts.ready = active.filter(t => !dependencyBlocked.has(t) && t.status.type === "TODO" && !t.status.name.includes("Next") && !t.tags.includes("#today")).length;
counts.blocked = blocked.length;

const chips = [
  { key: "today", target: "dash#TODAY Tasks", label: "TODAY" },
  { key: "plan", target: todayDailyPath, label: "PLAN", over: planOver, destination: "today's daily note" },
  { key: "pending", target: "dash#PENDING Tasks", label: "PENDING", cap: PENDING_CAP, over: counts.pending > PENDING_CAP },
  { key: "next", target: "dash#NEXT Tasks", label: "NEXT", cap: NEXT_CAP, over: counts.next > NEXT_CAP },
  { key: "ready", target: "dash#READY Tasks", label: "READY" },
  { key: "blocked", target: "blocked", label: "BLOCKED", external: true },
];
```

---

## 6. The Day in the Life: Morning GTD Review & Execution Workflow

Here is how Bryan's daily workflow operates under this new design:

```
┌─────────────────────────────────────────────────────────────┐
│                 MORNING GTD REVIEW (dash.md)                │
└──────────────────────────────┬──────────────────────────────┘
                               │
               1. Triage PENDING Tasks (In-Flight)
               - Did overnight agent swarms complete?
               - Yes: Review and mark Done [x]
               - No: Keep in PENDING or pull to TODAY
                               │
               2. Review NEXT Tasks (Weekly Bets)
               - Select 3–5 focus tasks for today
               - Link them into today's Daily Pomodoro ledger
               - Hook immediately assigns #today -> moves to TODAY
                               │
               3. Pull from READY Tasks (Backlog)
               - Only if capacity remains under plan budget!
               - Promote to NEXT or link directly into ledger
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 DAILY POMODORO EXECUTION                     │
├─────────────────────────────────────────────────────────────┤
│ • Focus entirely on TODAY Tasks and YYYYMMDD.md ledger      │
│ • When delegating a task to an agent swarm:                │
│   1. Task status is In Progress [/]                         │
│   2. Remove link from Daily Pomodoro ledger                 │
│   3. Hook strips #today                                     │
│   4. Task drops automatically into PENDING Tasks            │
│   5. Ledger remains clean; task is safely preserved         │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Comparative Assessment of Alternative Approaches

| Feature / Criterion | Option 1: Proposed `Today/Pending/Next` (Recommended) | Option 2: Retain `#now` + Add `#pending` Tag | Option 3: Dedicated Custom Status `[P]` Pending |
| :--- | :--- | :--- | :--- |
| **User Overhead** | **Lowest.** Standard checkbox clicks; zero tag typing. | **High.** Must remember `#now` and `#pending` tags. | **Medium.** Requires cycling to a new custom status symbol. |
| **GTD Alignment** | **Perfect.** Next = Next Actions; Today = Daily focus. | **Poor.** Next = Today; Now = Week. Continues inverted vocabulary. | **Good.** Explicit status for delegated work. |
| **Agent Delegation** | **Seamless.** Simply drop link from daily file; auto-becomes Pending. | **Friction.** Must remember to add `#pending` tag before dropping link. | **Friction.** Must edit checkbox to `[P]` before dropping link. |
| **Obsidian Integration** | **Native.** Uses existing `[*]`, `[/]`, `[ ]` statuses. | **Complex.** Extra tag filtering required everywhere. | **Invasive.** Requires editing Tasks plugin `data.json` and custom CSS icons. |
| **Parity (`bob query`)** | **100% Parity.** Completely supported by existing parser. | **100% Parity.** | Requires adding new status definition across CLI and JS. |

---

## 8. Implementation & Migration Roadmap

### Phase 1: `bob-cli` Engine Updates
1. **`src/native/task_status_hooks/`:**
   - Update sync logic to manage `#today` on all tasks linked in today's open Pomodoros and their transcluded dependencies.
   - Sweep and strip `#today` from tasks no longer linked in today's open Pomodoros.
   - Modify transition rules: **Do not demote `[*]` or `[/]` when unlinked**.
   - Ensure tasks pulled from `[ ]` into today's ledger are promoted to `[*]`.
2. **`src/native/plan_budget/`:**
   - Deprecate `max_now` in favor of `max_next` (default 15).
   - Add `max_pending` (default 5).
   - Update lints: replace `now_cap_exceeded` with `next_cap_exceeded` and `pending_cap_exceeded`.

### Phase 2: `bob-plugins` Updates
1. **`bob-ledger-tools`:**
   - Update JavaScript budget calculation to report `nextBudget()` and `pendingBudget()`.
2. **`bob-navigation-hotkeys`:**
   - Repurpose the `Alt+N` toggle: instead of toggling `#now`, it toggles `[*] Next` on the current task.

### Phase 3: Vault Migration & `dash.md`
1. **One-Time Migration Script:**
   - For all open tasks with `#now`:
     - If `- [ ] #task ... #now`: convert to `- [*] #task ...` and strip `#now`.
     - If `- [*] #task ... #now` or `- [/] #task ... #now`: simply strip `#now`.
2. **`dash.md` Update:**
   - Update Tasks code blocks to the mutually exclusive queries in §5.2.
   - Update DataviewJS chip bar to the configuration in §5.3.

### Phase 4: SASE Memory & Documentation Updates
1. Supersede `decisions/now-tag-is-user-owned`: document that `#now` has been retired and replaced by user-owned Next `[*]` and machine-managed `#today`.
2. Amend `decisions/task-status-is-derived`: note that Next `[*]` and In Progress `[/]` no longer decay on ledger unlinking, while Blocked `[?]` and `#today` remain derived.
3. Update `docs/plan.md` and `docs/task-status-hooks.md`.

---

## 9. Conclusion

Bryan's plan is an outstanding structural improvement to the Bob productivity ecosystem. It eliminates the clunky `#now` tag, restores natural GTD semantics, perfectly supports asynchronous agent delegation, and cleans up the dashboard into four mutually exclusive, intuitive sections. Implementing this with a machine-managed `#today` tag and strict capacity limits provides the ultimate balance of automation, clarity, and control.
