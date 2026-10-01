# Ready Tasks Freshness: Architectural Critique and Implementation Plan for NEW, READY, and ROTTEN Task Separation

- **Research date:** 2026-10-01
- **Author:** Researcher `gem` (5-researcher swarm)
- **Question:** How should we implement the removal of new and rotten tasks from the "READY tasks" section of `~/bob/dash.md`, the addition of a "NEW tasks" section on `dash.md`, and the relocation of rotten tasks to `~/bob/rotten.md` (linked via a "ROTTEN" badge)? Is Bryan's proposal to preprocess rotten tasks using `bob task-status-hooks` with a `#rotten` tag a good idea, or is there a better approach?
- **Evidence examined:**
  - `docs/freshness.md` (canonical contract for task freshness in `bob-cli`)
  - `docs/task-status-hooks.md` and `src/native/task_status_hooks/` (vault reconciler rules and implementation)
  - `src/native/freshness/` (`placement.rs`, `state.rs`, `cli.rs`)
  - `plugins/bob-ledger-tools/main.js` (api v3 `freshness` namespace, `readyBadge`, and `planBudget`)
  - `scripts/test-ledger-tools-freshness.cjs` and `scripts/test-ledger-tools-ready-badge.cjs`
  - Canonical vault files in `gh:bobs-org/bob`: `dash.md` and `freshness.md`
  - SASE decision records: `decisions:now-tag-is-user-owned`, `decisions:task-status-is-derived`, `decisions:task-lanes-are-sticky`, `decisions:today-is-read-from-the-ledger`
  - Prior research report: `research:202609/bob_cli_31_task_freshness_epic.md`

---

## 1. Executive Summary & Verdict

> **The conceptual separation of NEW, READY, and ROTTEN tasks is an excellent, high-leverage GTD enhancement, but preprocessing via `bob task-status-hooks` to write a `#rotten` tag is an architectural trap.**
>
> 1. **The Idea Is Fundamentally Sound:** Separating the backlog restores trust in the `### READY Tasks` section. In an uncurated ~180-task READY backlog, unprocessed captures ("pick up milk") and neglected 6-month-old decaying tasks drown out genuinely actionable work. Triaging NEW tasks directly on the dashboard, keeping READY as a high-confidence pull queue of fresh tasks, and relegating decaying tasks to a dedicated `rotten.md` review file creates a clear Kanban operational hierarchy.
> 2. **Tag Preprocessing via `task-status-hooks` Must Be Avoided:** Adding a `#rotten` tag to note files via automated cron violates core Bob architecture (`decisions:now-tag-is-user-owned`, `docs/freshness.md` §4 "Computed at read time, never stored"). It causes continuous git churn across dozens of notes, creates synchronization race conditions on multi-device Obsidian (desktop/mobile), requires complex stripping logic in every stamping tool (`bob capture`, hotkeys, cycler, Vim), and introduces a 15-minute feedback delay when refreshing tasks.
> 3. **The Recommended Implementation (Pure Read-Time Evaluation):** Obsidian Tasks queries natively support `filter by function`. Bob's existing plugin `bob-ledger-tools` already computes memoized freshness states in sub-millisecond time. By exposing lightweight helper predicates (`api.freshness.isNew(task)`, `api.freshness.isRotten(task)`, `api.freshness.isReady(task)`), `dash.md` and `rotten.md` can filter tasks instantly at render time without modifying a single markdown file on disk.
> 4. **Key Requirement Adjustments:**
>    - **Incorporate `RESURFACED` tasks:** Tasks unblocked from a deferral today are not fresh; they belong in `rotten.md` alongside stale tasks so they are not orphaned.
>    - **Consolidate `freshness.md` into `rotten.md`:** Rather than having two competing review files, `freshness.md` should be transitioned to `rotten.md`.
>    - **Synchronize the `READY` chip budget:** The `READY` badge count in `bob-ledger-tools` must be updated to count only fresh ready tasks to avoid a glaring visual contradiction with the section below it.
>    - **Adopt "rotten" cleanly:** Transition user-facing labels, headings, and file paths to "rotten", while retaining `stale` as an internal API alias to avoid breaking existing CLI outputs or downstream tools.

---

## 2. Background: How Freshness and Dashboard Currently Operate

### 2.1 The Freshness Contract (`docs/freshness.md`)
Implemented in `bob-cli-31`, task freshness tracks when a human last reviewed a Ready task:
- **Field:** `[fresh:: YYYY-MM-DD]` placed immediately before the trailing Tasks suffix (protecting trailing Tasks metadata like `scheduled`, `priority`, and block IDs).
- **Scope:** Active, non-recurring `[ ]` (TODO) tasks outside canonical daily notes, `#hide`, and Today.
- **Evaluation States (Pure & Read-Time):**
  - **`NEW`**: No valid `fresh` property.
  - **`RESURFACED`**: `fresh` < `scheduled` <= today (a deferred task whose date has arrived).
  - **`STALE`** (to become **`ROTTEN`**): `today >= fresh + interval` (default interval: 7 days).
  - **`FRESH`**: Confirmed within interval and not resurfaced.
- **Review Queue Tiers:**
  - **Tier 1 (`NEW`)**: Unreviewed captures. Morning rule: walk to 0 new.
  - **Tier 2 (`DUE`)**: `RESURFACED` + `STALE` (rotten). Walk until 0 due or daily budget met.
- **Bedrock Invariants:**
  - Section 4: *"Computed at read time, never stored."*
  - Section 5: *"Automation: — (hooks never stamp)."* Freshness is stamped exclusively by human gestures (`Alt+F`, `Alt+N`, picker edits, cycler reopens).

### 2.2 The Current `dash.md` Structure
`~/bob/dash.md` acts as the primary operational cockpit in Obsidian. It contains:
1. **Count Widget (DataviewJS):**
   - Renders chips: `PENDING`, `NEXT`, `READY` (via shared `renderReadyBadge`), `BLOCKED`, `REVIEW`, `TODAY`.
   - `REVIEW` chip points to `freshness.md` and displays `${fresh.due} · ${fresh.new} new · ✓ ${fresh.refreshedToday}`.
2. **Tasks Query Sections:**
   ```tasks
   ### TODAY Tasks       --> filter by isToday(task) === true
   ### PENDING Tasks     --> status.type is IN_PROGRESS (excluding Today)
   ### NEXT Tasks        --> status.name includes Next (excluding Today)
   ### READY Tasks       --> status.type is TODO (excluding Today)
   ```
Currently, `### READY Tasks` displays **all** `[ ]` tasks in the vault (~180 tasks). Unchecked Keep captures, neglected year-old chores, and freshly validated items sit in a single undivided list.

---

## 3. In-Depth Critique of Bryan's Proposal

### 3.1 Is Separating NEW, READY, and ROTTEN a Good Idea?
**Verdict: Yes, it is an outstanding productivity and cognitive design decision.**

In GTD and Kanban methodology, mixing unreviewed inbox inputs, active work candidates, and decaying backlog tasks into a single bucket creates three major failure modes:
1. **Backlog Numbness:** When scanning 180 tasks to decide what to pull into NEXT or TODAY, Bryan must re-evaluate whether each task is still valid, already obsolete, or needs clarification. After seeing the same rotten task 20 times, scanning becomes skimming, and tasks are skipped.
2. **Inbox Invisibility:** New captures from Google Keep (`bob gkeep pull`) or mobile quick-capture arrive without `[fresh:: ...]`. When dumped directly into the 180-task READY pool, they are easily lost unless Bryan explicitly visits the separate `freshness.md` review note.
3. **Loss of Pull Confidence:** A true "READY" backlog in Kanban should mean: *Ready to be pulled immediately.* If a task might have expired context, missing dependencies, or obsolete scope, it is NOT ready.

By dividing them into:
- **`NEW` (Inbox/Triage):** Unprocessed, unconfirmed captures. Requires a triage gesture (`Alt+F` to accept, `Ctrl+Shift+P` to schedule/drop, or edit).
- **`READY` (Actionable Backlog):** Strictly fresh, confirmed tasks within their review lease (e.g. 7 days). High trust.
- **`ROTTEN` (Maintenance Queue):** Expired tasks moved out of sight into `rotten.md`. Addressed during the dedicated morning review or weekly prune.

The dashboard transforms from a cluttered warehouse into a sharp, trustworthy operational instrument.

---

### 3.2 Critique of Preprocessing with `bob task-status-hooks` to Add `#rotten` Tag
**Verdict: Strongly advised against. This is an anti-pattern that reintroduces retired failure modes.**

Bryan asked: *"We may need to preprocess these rotten tasks somehow in order to make this work. My first thought was that we could use the `bob task-status-hooks` command to add a `#rotten` tag to rotten tasks, but you should think hard about the best way to implement this."*

Here is why this approach is fundamentally flawed:

#### 1. Direct Repetition of the `#now` Tag Failure
Bob's vault history contains explicit evidence against automated tag injection:
- In `decisions:now-tag-is-user-owned` and `research:202609/retire_now_sticky_lanes_ledger_today`, automated tagging by cron was trialed and decisively rejected.
- When automation writes tags into user markdown files, git working trees are constantly dirtied without human interaction. A unattended cron job touching 20–40 files every morning creates massive git log pollution and makes `git diff` useless for tracking human edits.

#### 2. The Deletion Lifecycle Problem (Lag and Multi-Writer Burden)
If `task-status-hooks` adds `#rotten`:
- **When does `#rotten` get removed?**
  Suppose Bryan opens `rotten.md`, sees a task, and presses `Alt+F` to confirm it (stamping `[fresh:: 2026-10-01]`).
  If `Alt+F` does not know how to parse and delete `#rotten`, the task STILL carries `#rotten`! It will remain stuck in `rotten.md` until `bob task-status-hooks` runs up to 15 minutes later on cron!
  This destroys the immediate tactile feedback of the morning review ritual (`]s` / `Alt+Shift+F`).
- **Surface Explosion:** To fix that lag, every single tool that touches tasks would have to be taught to strip `#rotten`:
  - `bob-navigation-hotkeys` (`Alt+F`, `Alt+Shift+F`, `Ctrl+Shift+P`, `Ctrl+Shift+M`)
  - `task-status-cycler` (`Alt+[`, `Alt+]`, `Ctrl+Enter`)
  - `block-id-prompt` (`Ctrl+Shift+Enter`, `^^`)
  - `bob capture` (Rust CLI)
  - Vim mappings and manual editing
  This spreads fragile text-manipulation logic across multiple repositories (`bob-cli`, `bob-plugins`).

#### 3. Synchronization Race Conditions and Mobile Failure
- `task-status-hooks` runs via cron on Bryan's desktop/Mac. It **does not run on iOS or iPadOS**.
- On mobile Obsidian, tasks would never be marked `#rotten` as they age, causing inconsistent views between desktop and mobile.
- If Bryan is actively editing a note on desktop or mobile while `task-status-hooks` runs unattended in the background, file rewriting causes Obsidian file reload flickers, cursor jumps, or merge conflicts.

#### 4. Scope Creep for `task-status-hooks`
As codified in `docs/task-status-hooks.md`, `task-status-hooks` is strictly a *Pomodoro-driven status reconciler*:
- It promotes tasks linked under today's open Pomodoros to `[*]`.
- It reconciles `[?]` Blocked markers based on open Dataview dependencies and future schedules.
- It cleans the Pomodoro ledger.
It has *never* injected tags into task bodies. Making it a general-purpose tag preprocessor violates single-responsibility boundaries.

#### 5. Preprocessing Is Entirely Unnecessary
The premise that "preprocessing is required" stems from the belief that Obsidian Tasks queries can only filter by raw text or tags (`tag includes #rotten`).
However, **Obsidian Tasks natively supports `filter by function <expression>`**, and `bob-ledger-tools` is already loaded in Obsidian and already computes memoized freshness states!
`freshness.md` in the live vault already uses:
```tasks
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.isDue?.(task) === true
```
Evaluating freshness at read-time inside Obsidian is instantaneous, produces zero disk writes, requires zero git commits, and updates the UI the exact millisecond `Alt+F` is pressed.

---

### 3.3 The Missing Piece: What About `RESURFACED` Tasks?
In Bryan's prompt:
*"A new task or a rotten task (let's start using the term "rotten" instead of "stale") should not be shown in the "READY tasks" section of the ~/bob/dash.md file."*

Notice what is missing: **`RESURFACED` tasks.**
Under `docs/freshness.md` §4:
- When a task is deferred to a future date with `[scheduled:: YYYY-MM-DD]`, it is stamped and marked Blocked `[?]`.
- When that scheduled date arrives (`scheduled <= today`), `task-status-hooks` unblocks it back to `[ ]` (TODO).
- Its freshness state is now **`RESURFACED`** (`fresh < scheduled <= today`).
- In the freshness review model, RESURFACED tasks are part of the `DUE` review queue because Bryan has not reviewed them since their deferral ended.

If Bryan's new rule is implemented as:
- Exclude `NEW` from READY.
- Exclude `ROTTEN` (stale) from READY.
- Put `NEW` in `dash.md`.
- Put `ROTTEN` in `rotten.md`.

**What happens to RESURFACED tasks?**
- If READY only shows fresh tasks, RESURFACED is excluded from READY.
- If `rotten.md` only filters by `state === "stale"` (rotten), RESURFACED is excluded from `rotten.md`.
- RESURFACED tasks would become **completely invisible orphans**—absent from NEW, absent from READY, and absent from ROTTEN!

**Resolution:** `rotten.md` (or the review view) must capture **all** review-due tasks that are not NEW—specifically `ROTTEN` + `RESURFACED`.

---

### 3.4 Consolidation of `freshness.md` vs. `rotten.md`
Phase 31.9 of epic `bob-cli-31` recently deployed `~/bob/freshness.md`.
If we create `~/bob/rotten.md`:
- `freshness.md` currently lists NEW and DUE (resurfaced + stale).
- If NEW is moved directly to `dash.md`, `freshness.md` and `rotten.md` would be doing almost the exact same thing.
- Keeping both files in the vault creates clutter and ambiguity: which file should Bryan open? Which one do hotkeys (`]s`) jump through? Which one does the status bar open on click?

**Resolution:**
Rather than maintaining two parallel review notes, **`freshness.md` should be transitioned/renamed to `rotten.md`** (maintaining an alias `aliases: [Freshness review, Review]` so existing bookmarks and hotkeys continue to work seamlessly).

---

### 3.5 Synchronization of the READY Badge and Budget
In `dash.md`, the `READY` chip currently invokes `ledgerApi?.renderReadyBadge(parent, ...)`.
In `bob-ledger-tools/main.js`, `readyCountFromTasks()` counts all `[ ]` tasks that are visible and unblocked (~177 tasks).
If `dash.md`'s `### READY Tasks` section is filtered to show only fresh tasks, but the `READY` chip at the top of the page continues to say:
`READY 177/100 (over limit)`
The dashboard will be self-contradictory: the chip screams red and claims 177 tasks, while the list below it displays only ~35 fresh tasks!

**Resolution:**
The counting logic in `bob-ledger-tools` (`readyCountFromTasks` and `readyBudgetFromTasks`) must be updated in lockstep: a task only counts toward the READY backlog budget if it is truly ready (i.e. fresh).

---

## 4. Architectural Alternatives Compared

| Criterion | Option A: `#rotten` Tag via `task-status-hooks` | Option B: Pure Read-Time Function Filter (Recommended) | Option C: Pure DataviewJS Task Rendering |
| :--- | :--- | :--- | :--- |
| **Storage Model** | Stored tag written to markdown files on disk | Computed in memory at render time | Computed in memory at render time |
| **Git Churn** | **Severe:** 10–30 notes modified by cron weekly | **Zero:** No files touched on disk | **Zero:** No files touched on disk |
| **Update Latency** | **Slow:** Up to 15-min lag after pressing `Alt+F` | **Instantaneous:** UI updates on keystroke | **Instantaneous:** UI updates on keystroke |
| **Mobile Compatibility** | **Broken:** Cron does not run on iOS/iPadOS | **Full:** Runs identically in mobile Obsidian | **Full:** Runs identically in mobile Obsidian |
| **Tag Stripping Logic** | **Complex:** Must update cycler, hotkeys, capture, vim | **None needed:** State is derived from date math | **None needed:** State is derived from date math |
| **Interactive UX** | Standard Tasks checkboxes and modals | Standard Tasks checkboxes and modals | Degraded (DataviewJS checkboxes lack Tasks hotkey/cycling hooks) |
| **SASE Precedent Alignment** | Violates `decisions:now-tag-is-user-owned` and `docs/freshness.md` | Perfectly aligns with `decisions:today-is-read-from-the-ledger` | Aligns with decisions, but worse UI ergonomics |

**Conclusion:** Option B (Pure Read-Time Function Filtering) is unambiguously superior across every architectural, operational, and user-experience dimension.

---

## 5. Adjustments to Bryan's Requirements

Based on this analysis, the following 6 adjustments to Bryan's requirements are recommended:

1. **Adjustment 1 (Implementation Mechanism):**
   *Requirement:* Preprocess rotten tasks with `bob task-status-hooks` to add `#rotten`.
   *Adjusted:* **Do not use `task-status-hooks` or `#rotten` tags.** Implement read-time filtering using `filter by function` via lightweight helper predicates in `bob-ledger-tools`.
   *Justification:* Eliminates git churn, eliminates sync conflicts, works on mobile, and guarantees instant UI reactivity when refreshing tasks.

2. **Adjustment 2 (Handling Resurfaced Tasks):**
   *Requirement:* Only mentions new and rotten tasks.
   *Adjusted:* **Explicitly include `RESURFACED` tasks in `rotten.md`** and exclude them from `### READY Tasks`.
   *Justification:* Resurfaced tasks (newly unblocked from past deferrals) must be re-verified before entering the fresh READY backlog; otherwise they become invisible orphans.

3. **Adjustment 3 (Note Consolidation):**
   *Requirement:* Create a new `~/bob/rotten.md` file while `~/bob/freshness.md` exists.
   *Adjusted:* **Rename `freshness.md` to `rotten.md`** (keeping aliases `[Freshness review, Review]`), updating its query to focus on rotten + resurfaced tasks.
   *Justification:* Prevents note redundancy and unifies the review surface.

4. **Adjustment 4 (Synchronizing Dashboard Chips and READY Budget):**
   *Requirement:* Change the task sections on `dash.md`.
   *Adjusted:* **Update `bob-ledger-tools` READY budget counting** to count only fresh ready tasks, and update the dashboard chip widget to replace/relabel `REVIEW` with `ROTTEN`.
   *Justification:* Prevents visual and numerical contradictions between the `READY` chip (cap/count) and the `### READY Tasks` section.

5. **Adjustment 5 (Section Hierarchy on `dash.md`):**
   *Requirement:* Show `### NEW Tasks` above "WIP tasks" (PENDING).
   *Adjusted:* **Place `### NEW Tasks` directly between `### TODAY Tasks` and `### PENDING Tasks`.**
   *Justification:* The canonical flow becomes:
   `TODAY` (today's committed execution) $\rightarrow$ `NEW` (unprocessed capture inbox) $\rightarrow$ `PENDING` (work in progress) $\rightarrow$ `NEXT` (pull candidates) $\rightarrow$ `READY` (curated fresh backlog).

6. **Adjustment 6 (Vocabulary Migration):**
   *Requirement:* Use "rotten" instead of "stale".
   *Adjusted:* **Adopt "rotten" across all user-facing surfaces** (`rotten.md`, `ROTTEN` chip, docs, headings), while retaining `"stale"` as an accepted internal API value and alias in `bob-cli` and `bob-ledger-tools` to ensure backward compatibility.

---

## 6. Recommended Technical Implementation Blueprint

Here is the exact, concrete implementation plan across `bob-plugins`, `dash.md`, and the vault.

### 6.1 Changes to `bob-plugins` (`plugins/bob-ledger-tools/main.js`)

In `bob-ledger-tools`, enhance the `freshness` namespace and `readyBudget`:

#### 1. Add Helper Predicates to `api.freshness`
Expose clean, self-documenting predicates on `api.freshness`:

```javascript
// In bob-ledger-tools/main.js under api.freshness:
isNew: (task) => {
  try {
    return self.apiFreshnessState(task) === "new";
  } catch { return false; }
},
isRotten: (task) => {
  try {
    const s = self.apiFreshnessState(task);
    return s === "stale" || s === "resurfaced";
  } catch { return false; }
},
isFresh: (task) => {
  try {
    return self.apiFreshnessState(task) === "fresh";
  } catch { return false; }
},
isReady: (task) => {
  try {
    // A task is Ready if it is TODO, not in Today, and FRESH
    if (task?.status?.type !== "TODO") return false;
    if (self.isToday(task)) return false;
    return self.apiFreshnessState(task) === "fresh";
  } catch { return false; }
}
```

#### 2. Update `freshnessCounts`
Expose `rotten` in the count object alongside `stale`:
```javascript
// In freshnessCounts:
return {
  due,
  new: freshNew,
  resurfaced,
  stale,
  rotten: stale, // alias for "rotten"
  fresh,
  refreshedToday,
  budget,
  budgetMet,
};
```

#### 3. Update `readyCountFromTasks` to Count Fresh Ready Tasks
Update `readyCountFromTasks` in `main.js`:
```javascript
function readyCountFromTasks(tasks, today, isToday, freshnessApi) {
  const list = Array.isArray(tasks) ? tasks : [];
  const todayDay = planDayNumber(today === undefined ? new Date() : today);
  const isTodayPredicate = typeof isToday === "function" ? isToday : () => false;
  let count = 0;
  for (const task of list) {
    if (!readyTaskVisible(task, todayDay)) continue;
    if (planTaskIsBlocked(task, list)) continue;
    if (isTodayPredicate(task)) continue;
    
    // Only count fresh tasks toward the READY backlog cap
    if (freshnessApi && typeof freshnessApi.state === "function") {
      const state = freshnessApi.state(task);
      if (state !== "fresh") continue;
    }
    count += 1;
  }
  return count;
}
```

---

### 6.2 Changes to `~/bob/dash.md`

#### 1. Tasks Sections in `dash.md`
Update lines 413–444 of `dash.md` to:

````markdown
### TODAY Tasks

```tasks
not done
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) === true
sort by function (globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.todayRank?.(task) ?? 0)
```

### NEW Tasks

```tasks
status.type is TODO
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.isNew?.(task) === true
sort by created reverse
```

### PENDING Tasks

```tasks
status.type is IN_PROGRESS
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true
sort by created
```

### NEXT Tasks

```tasks
status.name includes Next
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true
sort by priority
```

### READY Tasks

```tasks
status.type is TODO
filter by function (globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.isReady?.(task) ?? (globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true))
```
````

*Note on Fallback:* If `bob-ledger-tools` is ever disabled, the nullish coalescing `??` safely falls back to standard `isToday(task) !== true`.

#### 2. Chips Widget in `dash.md`
In the DataviewJS block:
1. Update `chipsAfterReady`:
   ```javascript
   const chipsAfterReady = [
     { key: "blocked", target: "blocked", label: "BLOCKED", external: true },
     { key: "rotten", target: "rotten", label: "ROTTEN", external: true, over: rottenOver, destination: "Rotten review" },
     { key: "plan", target: todayDailyPath, label: "TODAY", href: `${todayDailyPath}.md`, over: planOver, destination: "today's daily note" },
   ];
   ```
2. Compute `counts.rotten`:
   ```javascript
   let rottenOver = false;
   try {
     const fresh = ledgerApi?.freshness?.counts?.();
     if (fresh && typeof fresh.stale === "number") {
       const rottenCount = fresh.stale + (fresh.resurfaced || 0);
       counts.rotten = `${rottenCount} · ✓ ${fresh.refreshedToday}`;
       rottenOver = rottenCount > 0;
     }
   } catch {
     // keep placeholder
   }
   ```
3. Add CSS accent styling for `.task-count-rotten`:
   ```css
   .task-count-widget .task-count-rotten {
     --task-count-accent: var(--color-orange, var(--interactive-accent));
   }
   ```

---

### 6.3 Creation of `~/bob/rotten.md` (Transformed from `freshness.md`)

Create `~/bob/rotten.md` (replacing or aliasing `freshness.md`):

````markdown
---
parent: "[[gtd]]"
aliases:
  - Rotten
  - Rotten tasks
  - Freshness review
  - Review
---

# Rotten tasks

```dataviewjs
const api = app.plugins.plugins["bob-ledger-tools"]?.api;
let text = "–";
try {
  const c = api?.freshness?.counts?.();
  if (c && typeof c.stale === "number") {
    const rottenTotal = c.stale + (c.resurfaced || 0);
    text = `${rottenTotal} rotten (${c.stale} stale, ${c.resurfaced} resurfaced) · ✓ ${c.refreshedToday} refreshed today`;
  }
} catch {}
dv.paragraph(text);
```

Review rotten and resurfaced tasks. One key per outcome:

| Decision | Key |
| :--- | :--- |
| still right, keep fresh | `Alt+Shift+F` (or `Alt+F`) |
| keep, but see less often | `Ctrl+Shift+P` → refresh → 14 / 30 / 90 |
| not now (defer) | `Ctrl+Shift+P` priority (rolls a P-level `scheduled`) |
| do today / commit | `Ctrl+Shift+Enter` / `Alt+N` |
| route to a project | `Ctrl+Shift+M` |
| drop / cancel | `Ctrl+Shift+P` cancel |
| wording is wrong | edit, then `Alt+F` |

```tasks
not done
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.isRotten?.(task) === true
sort by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.rank?.(task) ?? 0
group by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.freshness?.tier?.(task) ?? "?"
short mode
hide toolbar
```
````

---

### 6.4 The Revised Morning Review Ritual

With this architecture in place, Bryan's morning ritual becomes remarkably streamlined and frictionless:

1. **`bob gkeep pull`** (pulls thoughts captured on phone).
2. **Open `dash.md`**:
   - Look at `### NEW Tasks` directly on the dashboard.
   - For each new task, tap `Alt+Shift+F` to confirm, or route/schedule it.
   - **`### NEW Tasks` becomes empty within 2 minutes.**
3. **Check `ROTTEN` Badge on `dash.md`**:
   - If rotten count is high or budget unreached, click the `ROTTEN` badge to open `rotten.md`.
   - Walk `]s` / `Alt+Shift+F` to review rotten tasks until the daily goal is met.
   - As each task is refreshed, it **instantly vanishes from `rotten.md`** and moves into `### READY Tasks` on `dash.md`.
4. **Plan Today**:
   - Scan `### PENDING Tasks` and `### NEXT Tasks`.
   - Pull from `### READY Tasks` (now guaranteed to contain only fresh, high-confidence work).

---

## 7. Migration & Rollout Plan

1. **Phase 1: Update `bob-plugins` (`bob-ledger-tools`)**
   - Implement `isNew`, `isRotten`, `isFresh`, and `isReady` on `api.freshness`.
   - Update `readyCountFromTasks` to count only fresh ready tasks.
   - Add unit tests in `bob-plugins/scripts/test-ledger-tools-freshness.cjs` verifying all 4 predicates against vectors S1–S15.
   - Run `bob plugins sync` to deploy to `~/bob/.obsidian/plugins/bob-ledger-tools/`.
2. **Phase 2: Update Vault Notes (`dash.md` & `rotten.md`)**
   - Create `~/bob/rotten.md` with aliases pointing to old `freshness.md`.
   - Edit `~/bob/dash.md`: add `### NEW Tasks`, update `### READY Tasks` query, update `ROTTEN` chip.
   - Test in Obsidian: confirm that stamping a task with `Alt+F` immediately moves it from `NEW`/`ROTTEN` into `READY` in real time.
3. **Phase 3: Documentation & CLI Aliasing**
   - In `docs/freshness.md`: Document the term "rotten" as the canonical name for expired review tasks, noting `stale` as the protocol-level value.
   - In `bob freshness list`: Add an optional `--rotten` alias or update human output headers to say `rotten` if desired.

---

## 8. Summary Checklist of Recommendations

- [x] **Reject `#rotten` tag preprocessing via `task-status-hooks`:** Avoids git noise, tag-stripping bugs, and sync lag.
- [x] **Implement via Read-Time Function Filters:** Expose `api.freshness.isNew`, `isRotten`, and `isReady` in `bob-ledger-tools`.
- [x] **Add `### NEW Tasks` to `dash.md`:** Place between `### TODAY Tasks` and `### PENDING Tasks`.
- [x] **Filter `### READY Tasks` in `dash.md`:** Show only tasks where `isReady(task) === true`.
- [x] **Create `rotten.md` with Resurfaced Coverage:** Ensure `RESURFACED` tasks accompany rotten tasks in review.
- [x] **Synchronize the `READY` Badge Budget:** Update `readyCountFromTasks` to match the fresh-only section definition.
- [x] **Adopt "Rotten" Terminology:** Transition UI and markdown surfaces to "rotten" while keeping `stale` as an internal alias.
