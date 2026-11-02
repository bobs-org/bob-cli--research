# Unified Task Decay & Freshness Lifecycle Architecture

> **Author**: researcher `gem` (Independent Research Report)  
> **Date**: 2026-11-02  
> **Scope**: `bob-cli`, `bob-plugins` (`bob-navigation-hotkeys`, `bob-ledger-tools`), `chezmoi` (`bob/config.yml`), and Bob Vault Policy.  
> **Artifact ID**: `research:202611/unified_task_decay_and_freshness_lifecycle__gem.md`

---

## 1. Executive Summary & Problem Formulation

### 1.1 The Vision
Task management systems suffer from an inevitable law of entropy: tasks are captured and scheduled with optimistic intentions, but over time stalled and neglected tasks accumulate across active lanes. Today, Bob addresses this with two separate, disconnected decay mechanisms:
1. **Priority / Roll Decay (`Ctrl+Enter` on `scheduled`)**: If a task with a configured priority (`[priority:: high]`) and date (`[scheduled:: YYYY-MM-DD]`) is repeatedly rolled at the same priority level, its Schedule Log streak builds up until reaching a roll limit, at which point it decays down the priority ladder ($P1 \to P2 \to P3 \to P4$) and past $P4$ is cancelled (`Drop`).
2. **Freshness / Ready Task Decay (`Alt+F` / `Ctrl+Alt+F` on Ready tasks)**: If a Ready backlog task (`[ ]`) is confirmed 3 times without progress (`[keeps:: 3]`), the next review opens a `FreshnessDecayCardModal` offering options to defer into the priority ladder (P0 entry), review less often, reword, drop, or keep anyway.

Meanwhile, **Work-in-Progress (WIP, `[/]`)** and **Next (`[*]`)** tasks have been completely exempt from keep-streak counting and decay. Because lanes are sticky (under `decisions:task-lanes-are-sticky`), tasks in WIP and Next linger indefinitely unless manually released via `Alt+N` or completed. During morning review (`]s`), pressing `<alt+f>` on a WIP task prompts for a Work Log summary ("What did you get done?"), while Next tasks prompt for an optional reason that is discarded if left blank.

### 1.2 The Proposed Unification
The proposed enhancement unifies task decay across the entire task lifecycle into a single, cohesive, entropy-fighting funnel:

```
[ Active Work ]
      |
      v
  WIP ([/])       -- (exceeds keep limit) -->  Decays to Next ([*])
      |
      v
  Next ([*])      -- (exceeds keep limit) -->  Decays to Ready ([ ])
      |
      v
  Ready ([ ])     -- (exceeds keep limit) -->  Decays to Priority Ladder (P1 entry)
      |
      v
  P1 -> P2 -> P3 -> P4  -- (exceeds roll limit) -->  Decays to Cancelled (Drop)
```

At every decay boundary, the user is presented with a consistent, beautiful decay modal where:
- **`Enter` (Default / Recommended)**: Accepts the graceful degradation to the next lower stage.
- **`Alt+F` (Keep in Status)**: Allows keeping the task in its current status, prompting for why, logging a dated entry in the `🥀 **ROTTEN LOG**`, and **resetting the keep streak** so the user is granted a fresh cycle before being prompted again.
- **`E` (Reword)**: Edits task text and resets the keep streak.
- **`D` (Drop)**: Cancels the task with a Cancel Log entry.
- **`Esc`**: Dismisses without changes.

---

## 2. Root Cause Analysis: The Ready Task Decay Bug

### 2.1 Bug Symptom
In `~/tmp/screenshots/20261102_134505.png`, an exact due Ready task at 3 keeps opened the decay card, displaying:
- **Title**: `Kept 3 reviews in a row`
- **Option `Enter`**: `Not now` — **`no priority ladder is configured`** (disabled / unavailable).
- **Default Focus**: Fell back to `Alt+F Keep` instead of the recommended `Enter Not now`.

The user noted:
> *"Namely, it says that no priority ladder is configured (I think we should just always use P1, right?). We should fix this issue as a part of this change."*

### 2.2 Deep Code Investigation
Bryan's `~/.config/bob/config.yml` in `chezmoi` **does** configure a full priority ladder:
```yaml
properties:
  - name: scheduled
    values: date
  - name: priority
    values: priority
    schedules: scheduled
    levels:
      - label: P1
        value: high
        min_days: 3
        max_days: 8
      - label: P2
        value: medium
        min_days: 9
        max_days: 31
      - label: P3
        value: low
        min_days: 32
        max_days: 100
      - label: P4
        value: lowest
        min_days: 101
        max_days: 365
```

Why did Bob report `"no priority ladder is configured"`? Investigation reveals **two distinct defects**: one critical implementation bug in `bob-navigation-hotkeys`, and one subtle policy flaw in the P0 entry resolution algorithm.

#### Defect 1: `this.config` is `undefined` on `BobNavigationHotkeysPlugin`
In `plugins/bob-navigation-hotkeys/src/530-plugin-freshness-refresh-and-decay.js`:
```javascript
// Line 157 in buildFreshnessDecayCardCtx:
const property = findFreshnessDecayPriorityProperty(this.config);

// Line 365 in revalidateFreshnessDecayCardInputs:
const property = findFreshnessDecayPriorityProperty(this.config);

// Line 558 in resolveFreshnessDecayCardLevel:
const property = findFreshnessDecayPriorityProperty(this.config);

// Line 589 in applyFreshnessDecayCardDeferral:
const property = findFreshnessDecayPriorityProperty(this.config);
```
In JavaScript, `this` in these methods refers to the plugin instance `BobNavigationHotkeysPlugin`.
Across the entire plugin lifecycle (`490-plugin-lifecycle.js`), **`this.config` is never set or loaded**. The property `this.config` only exists on modal instances like `BulletPropertyPickerModal` (which sets `this.config = config` in its own constructor).

When `buildFreshnessDecayCardCtx` runs:
1. `this.config` is `undefined`.
2. `findFreshnessDecayPriorityProperty(undefined)` executes:
   ```javascript
   function findFreshnessDecayPriorityProperty(config) {
     try {
       const properties = config && Array.isArray(config.properties) ? config.properties : [];
       return properties.find(c => c && c.values === "priority") || null;
     } catch (e) { return null; }
   }
   ```
3. It returns `null`.
4. In `050-decay-planner.js` (line 153 & 198):
   ```javascript
   const hasPriorityLadder = Boolean(property && property.values === "priority");
   ...
   } else if (!hasPriorityLadder) {
     notNow = unavailable("no priority ladder is configured");
   }
   ```
5. `hasPriorityLadder` evaluates to `false`, immediately hard-disabling the `Enter Not now` row with the exact string `"no priority ladder is configured"`.

**The Fix for Defect 1**:
`BobNavigationHotkeysPlugin` must properly load and cache the bullet property configuration using `loadBulletPropertyConfig()`, exactly as `500-plugin-transclusion-and-link-picker.js` and `550-plugin-cancel-and-counted-property.js` do:
```javascript
const config = this.bulletPropertyConfig || loadBulletPropertyConfig({ showNotice: () => {} });
const property = findFreshnessDecayPriorityProperty(config);
```

#### Defect 2: Flawed Fallback in `resolveFreshnessDecayP0EntryLevel`
Even after fixing `this.config`, inspecting `resolveFreshnessDecayP0EntryLevel` in `plugins/bob-navigation-hotkeys/src/040-priority-roll.js` reveals an algorithmic bug:
```javascript
function resolveFreshnessDecayP0EntryLevel(property, intervalDays, enterLabel) {
  const levels = property && Array.isArray(property.levels) ? property.levels : [];
  if (levels.length === 0) return { unavailable: true, reason: "no configured priority levels" };
  const enterResolved = resolveFreshnessDecayEnterLevel(property, enterLabel);
  if (enterResolved) return { level: enterResolved };

  const interval = Math.floor(numericOrDefault(intervalDays, NaN));
  const entry = levels.find(
    (level) =>
      level && Number.isInteger(level.minDays) && Number.isInteger(level.maxDays) &&
      level.minDays <= level.maxDays &&
      level.minDays > interval, // <--- THE FLAW
  );
  if (!entry) return { unavailable: true, reason: `no level stays out longer than every ${interval} days` };
  return { level: entry };
}
```
Notice what happens when `enterLabel` is not configured in `freshness.decay.enter`:
- Bryan's `freshness.interval` is `3`.
- Level `P1` has `min_days: 3`, `max_days: 8`.
- The condition `level.minDays > interval` checks `3 > 3`, which is **`false`**!
- As a result, the scan **skips P1 entirely** and jumps to `P2` (`min_days: 9 > 3`). If `interval` were `9` or higher, it would skip `P2` as well, or fail with `"no level stays out longer than every 9 days"`.

Bryan's intuition is entirely right:
> *"(I think we should just always use P1, right?)"*

A Ready task has no priority tag, representing implicit P0. When it decays into the priority ladder, it should step down to the **first tier of the ladder (P1)**, rolling a date within P1's window (3–8 days). Skipping P1 directly into P2 violates the priority ladder's progression.

**The Fix for Defect 2**:
1. In `chezmoi`'s `bob/config.yml`, explicitly set `freshness.decay.enter: P1`.
2. In `resolveFreshnessDecayP0EntryLevel`, if `enterLabel` is absent or `minDays > interval` finds nothing, fallback to `levels[0]` (the first configured level, P1) rather than failing.

---

## 3. Comprehensive Feature Critique & Architectural Analysis

### 3.1 Critique: Is Generalized Task Decay a Good Idea?
**Verdict: Strongly Yes, with disciplined guardrails.**

#### Why it is a compelling idea:
1. **Solves the "Sticky Lane Stagnation" Problem**:
   In `decisions:task-lanes-are-sticky`, Next and Pending were made sticky to prevent tasks from prematurely falling back to Ready on unlinking. While this protected active context, it created a severe blind spot: **tasks enter WIP or Next and never leave**. When an agent or human gets distracted, tasks stay in `[/]` or `[*]` indefinitely. Over weeks, the user develops "review blindness," reflexively pressing `Alt+F` to advance past stale WIP/Next rows.
2. **Restores Kanban WIP & Next Lane Caps**:
   Bob configures lane soft caps:
   - `plan.max_pending: 8`
   - `plan.max_next: 13`
   - `plan.max_ready: 21`
   When abandoned tasks clog WIP and Next, the user cannot pull real work without breaching caps or seeing warnings. Decaying stalled tasks naturally frees WIP capacity for active work and pushes stale commitments back down to the backlog.
3. **Respects User Agency**:
   Decay is never a silent background reaper. It occurs **only on an explicit review gesture** (`<alt+f>` or `<ctrl+alt+f>`) when the keep limit has been exhausted. The user can always override the decay with one keypress (`Alt+F Keep`), resetting the counter.

#### Potential Pitfalls & How to Avoid Them:
1. **Review Ritual Friction (Prompt Fatigue)**:
   If marking a task fresh prompts for text every morning, review slows to a crawl.
   *Mitigation*: Hitting `Enter` on a blank input must immediately accept the default reason and proceed without friction.
2. **Accidental Premature Demotion**:
   A keep limit of 2 means that on day 3 of review without progress, the task is prompted for decay. For tasks waiting on external PR review or third-party responses, 2 days might feel fast.
   *Mitigation*:
   - Choosing `Alt+F Keep` at the decay prompt resets the keep count to 0, giving another 2 full reviews.
   - External dependencies should be tracked using Bob's `[dependsOn::]` or `#waiting` mechanism (which derives Blocked status `[?]`, exempt from decay).

---

## 4. Detailed Component Design

### 4.1 State Machine & Decay Rules

| Current Status | Review Action | Keep Count | Resulting Action | Next Status | Keep Count After |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **WIP (`[/]`)** | `Alt+F` | $0 \to 1$ | Prompt Rotten Log (optional) | WIP (`[/]`) | $1$ |
| **WIP (`[/]`)** | `Alt+F` | $1 \to 2$ | Prompt Rotten Log (optional) | WIP (`[/]`) | $2$ (Limit reached) |
| **WIP (`[/]`)** | `Alt+F` | $2$ (at limit) | **WIP Decay Card** | | |
| | $\to$ `Enter` (Default) | | Decay to Next | **Next (`[*]`)** | **$0$ (cleared)** |
| | $\to$ `Alt+F` (Keep) | | Keep in WIP (asks why) | **WIP (`[/]`)** | **$0$ (reset)** |
| | $\to$ `D` (Drop) | | Cancel task | Cancelled (`[-]`) | N/A |
| **Next (`[*]`)** | `Alt+F` | $0 \to 1$ | Prompt Rotten Log (optional) | Next (`[*]`) | $1$ |
| **Next (`[*]`)** | `Alt+F` | $1 \to 2$ | Prompt Rotten Log (optional) | Next (`[*]`) | $2$ (Limit reached) |
| **Next (`[*]`)** | `Alt+F` | $2$ (at limit) | **Next Decay Card** | | |
| | $\to$ `Enter` (Default) | | Decay to Ready | **Ready (`[ ]`)** | **$0$ (cleared)** |
| | $\to$ `Alt+F` (Keep) | | Keep in Next (asks why) | **Next (`[*]`)** | **$0$ (reset)** |
| | $\to$ `D` (Drop) | | Cancel task | Cancelled (`[-]`) | N/A |
| **Ready (`[ ]`)** | `Alt+F` | $0 \to 1$ | Prompt Rotten Log (optional) | Ready (`[ ]`) | $1$ |
| **Ready (`[ ]`)** | `Alt+F` | $1 \to 2$ | Prompt Rotten Log (optional) | Ready (`[ ]`) | $2$ (Limit reached) |
| **Ready (`[ ]`)** | `Alt+F` | $2$ (at limit) | **Ready Decay Card** | | |
| | $\to$ `Enter` (Default) | | Decay to P1 Scheduled Roll | **Ready + `[priority:: high]`** | **$0$ (cleared)** |
| | $\to$ `Alt+F` (Keep) | | Keep in Ready (asks why) | **Ready (`[ ]`)** | **$0$ (reset)** |
| | $\to$ `L` (Less Often) | | Adjust `[refresh:: N]` | Ready (`[ ]`) | $0$ (reset) |
| | $\to$ `D` (Drop) | | Cancel task | Cancelled (`[-]`) | N/A |
| **Scheduled Priority** | `Ctrl+Enter` | Rolls $< 2$ | Same-level roll | Same P-level | Rolls $+ 1$ |
| **Scheduled Priority** | `Ctrl+Enter` | Rolls $= 2$ | **Priority Decay** | Next P-level ($P_i \to P_{i+1}$) | Rolls $= 0$ |
| **Scheduled $P4$** | `Ctrl+Enter` | Rolls $= 2$ | **Terminal Decay** | Cancelled (`[-]`) | Cancel Log |

### 4.2 Rotten Log Grammar & Unification
Currently, Rotten Log entries for Ready tasks use:
```markdown
- 🥀 **ROTTEN LOG**
	- *2026-11-02* — 🤷 no reason given · kept 1×
	- *2026-11-01* — waiting on upstream PR · kept 2×
```
While Next tasks currently use:
```markdown
- 🥀 **ROTTEN LOG**
	- *2026-11-02* — blocked on design review · kept in Next
```
(Notice: no keep count, and blank reasons were completely omitted).

#### Unified Standard Grammar:
Every keep confirmation writes a structured entry. If the user hits `Enter` without typing a reason, the default reason `🤷 no reason given` is recorded alongside the status and keep count.

1. **Keep Entries**:
   - **WIP**: `*YYYY-MM-DD* — <reason> · kept in WIP (<N>×)`  
     *Default*: `*YYYY-MM-DD* — 🤷 no reason given · kept in WIP (<N>×)`
   - **Next**: `*YYYY-MM-DD* — <reason> · kept in Next (<N>×)`  
     *Default*: `*YYYY-MM-DD* — 🤷 no reason given · kept in Next (<N>×)`
   - **Ready**: `*YYYY-MM-DD* — <reason> · kept in Ready (<N>×)`  
     *Default*: `*YYYY-MM-DD* — 🤷 no reason given · kept in Ready (<N>×)`
   - **Keep at Decay Limit (Streak Reset)**:  
     `*YYYY-MM-DD* — <reason> · kept in <Status> (streak reset)`

2. **Decay Transition Entries**:
   When a task decays, an entry is added to document why the transition occurred:
   - **WIP $\to$ Next**: `*YYYY-MM-DD* — decayed WIP → Next after 2 keeps`
   - **Next $\to$ Ready**: `*YYYY-MM-DD* — decayed Next → Ready after 2 keeps`
   - **Ready $\to$ Priority (P1)**: Recorded in `🗓️ **SCHEDULE LOG**`:  
     `🎲 P0 → P1 decay · in **5** (3–8) days · kept 2×`  
     *(Optionally mirrored in Rotten Log for unified auditability).*

### 4.3 Why Deprecating Work Log on WIP `<alt+f>` is Superior
Under current behavior, `<alt+f>` on a WIP task asks for a Work Log summary (`WORK LOG`), writing timestamped entries like `*2026-11-02 09:30* — fixed auth bug`.
Replacing this with the Rotten Log prompt during `<alt+f>` is justified because:
1. **Semantic Alignment**: `<alt+f>` is the **freshness review key**. Pressing it on a morning review row signifies: *"I am reviewing this task, but I am not closing it or progressing it today."* That is precisely what "Rotten" means: work that is aging without resolution.
2. **Separation of Concerns**: True work completed belongs in Pomodoro ledger closes (`=x`), capture bullets, or explicit Work Log entries via the Task Card.
3. **Consistency**: The user experiences a uniform review interaction: `<alt+f>` consistently manages freshness and Rotten Log across every tier of the review queue.

---

## 5. UI/UX Design: Intuitive, Reliable, and Beautiful

### 5.1 The Decay Modal Progression
We leverage the existing, beautifully styled `FreshnessDecayCardModal` (`.bob-decay-card-modal`) across all statuses, adapting the title, subtitle, and rows dynamically based on the decaying task's current status:

````carousel
```markdown
### WIP Task Decay Modal (Triggered on 3rd review of WIP task)
╭─────────────────────────────────────────────────────────────────╮
│ 🌿 Kept 2 reviews in WIP                                        │
│ Fix memory leak in buffer pool · memory.md · captured 5d ago    │
│ 🥀 2 keeps logged · last Nov 1 — 🤷 no reason given             │
├─────────────────────────────────────────────────────────────────┤
│ [Enter]   Decay to Next                                         │
│           [/] → [*] · move back to Next lane                    │
│                                                                 │
│ [Alt+F]   Keep in WIP                                           │
│           say why · logs 🥀 · resets keep streak                │
│                                                                 │
│ [  E  ]   Reword                                                │
│           edit the task · start the count over                  │
│                                                                 │
│ [  D  ]   Drop                                                  │
│           cancel · dropped after 2 keeps                        │
├─────────────────────────────────────────────────────────────────┤
│ Esc changes nothing · Enter decays to Next · Alt+F keeps in WIP │
╰─────────────────────────────────────────────────────────────────╯
```
<!-- slide -->
```markdown
### Next Task Decay Modal (Triggered on 3rd review of Next task)
╭─────────────────────────────────────────────────────────────────╮
│ 🌿 Kept 2 reviews in Next                                       │
│ Refactor config parser · config.md · captured 12d ago           │
│ 🥀 2 keeps logged · last Nov 1 — waiting on RFC                 │
├─────────────────────────────────────────────────────────────────┤
│ [Enter]   Decay to Ready                                        │
│           [*] → [ ] · return to backlog                         │
│                                                                 │
│ [Alt+F]   Keep in Next                                          │
│           say why · logs 🥀 · resets keep streak                │
│                                                                 │
│ [  E  ]   Reword                                                │
│           edit the task · start the count over                  │
│                                                                 │
│ [  D  ]   Drop                                                  │
│           cancel · dropped after 2 keeps                        │
├─────────────────────────────────────────────────────────────────┤
│ Esc changes nothing · Enter decays to Ready · Alt+F keeps       │
╰─────────────────────────────────────────────────────────────────╯
```
<!-- slide -->
```markdown
### Ready Task Decay Modal (Triggered on 3rd review of Ready task)
╭─────────────────────────────────────────────────────────────────╮
│ 🌿 Kept 2 reviews in a row                                      │
│ Explore sqlite backend · storage.md · captured 18d ago          │
│ 🥀 2 keeps logged · last Nov 1 — 🤷 no reason given             │
├─────────────────────────────────────────────────────────────────┤
│ [Enter]   Not now                                               │
│           P0 → P1 · back in 5 days (3–8)                        │
│                                                                 │
│ [  L  ]   Less often                                            │
│           review every 7 days instead of 3                      │
│                                                                 │
│ [  E  ]   Reword                                                │
│           edit the task · start the count over                  │
│                                                                 │
│ [  D  ]   Drop                                                  │
│           cancel · dropped after 2 keeps                        │
│                                                                 │
│ [Alt+F]   Keep                                                  │
│           say why · logs 🥀 · resets keep streak                │
├─────────────────────────────────────────────────────────────────┤
│ Esc changes nothing · D / X drops · 1–4 pick a P-level instead  │
╰─────────────────────────────────────────────────────────────────╯
```
````

### 5.2 Micro-Interactions & Keyboard Ergonomics
1. **Immediate Focus on Recommended Action**:
   In all modals, the `Enter` action is marked `recommended: true` and receives autofocus. The user can simply tap `Enter` to approve the natural decay step and move on with their morning review.
2. **In-Card Reason Stage on `Alt+F`**:
   Selecting `Alt+F Keep` swaps the modal rows for an inline text input (`RottenKeepReasonStage`) asking *"Why keep in <Status>?"*. The user can type a reason and press `Enter` to commit the keep and streak reset, or press `Enter` on empty text to log `🤷 no reason given`.
3. **Walk Auto-Advance Integration (`Ctrl+Alt+F`)**:
   Under `decisions:answering-advances-the-walk`, if the decay modal was triggered by `Ctrl+Alt+F`, committing either the decay transition (`Enter`) or the keep (`Alt+F`) advances the review walk to the next item automatically.

---

## 6. Configuration Schema & Chezmoi Updates

### 6.1 Unified Configuration Design
To make this feature flexible and maintainable, we introduce structured decay configuration under `freshness:` and explicitly configure priority decay under `properties:`.

#### Structure in `~/.config/bob/config.yml`:
```yaml
properties:
  - name: scheduled
    values: date
  - name: dependsOn
    values: local_task_id
  - name: priority
    values: priority
    schedules: scheduled
    # Ctrl+Enter on `scheduled` takes the recommended roll. Each level allows `rolls`
    # same-level rolls (read from the task's Schedule Log); the next recommended roll
    # decays the task one level (P2 → P3), and past the last level it cancels it.
    decay:
      rolls: 2 # allow 2 same-level rolls before decaying to next priority level
    levels:
      - label: P1
        value: high
        min_days: 3
        max_days: 8
      - label: P2
        value: medium
        min_days: 9
        max_days: 31
      - label: P3
        value: low
        min_days: 32
        max_days: 100
      - label: P4
        value: lowest
        min_days: 101
        max_days: 365

freshness:
  interval: 3 # Ready backlog review cadence
  pending_interval: 1 # [/] lane daily review; false = not walked
  next_interval: 1 # [*] lane daily review; false = not walked
  project_interval: 1 # Bryan's ^prj review cadence

  # Task Decay policy: unified entropy control across WIP, Next, and Ready.
  # A task kept without progress reaching its limit defaults to decaying to the next
  # lower status (WIP -> Next -> Ready -> P1 scheduled roll).
  decay:
    enabled: true # master switch for decay prompts (false keeps counting only)
    keeps: 2 # default keep limit across all statuses (2 keeps before decay prompt)
    # Optional status-specific overrides (default to `keeps` above):
    wip_keeps: 2 # allowed keeps in WIP [/] before decaying to Next [*]
    next_keeps: 2 # allowed keeps in Next [*] before decaying to Ready [ ]
    ready_keeps: 2 # allowed keeps in Ready [ ] before decaying to P1 scheduled roll
    enter: P1 # priority level entered when a Ready task decays (always P1)
```

### 6.2 Backward Compatibility
- If `wip_keeps`, `next_keeps`, or `ready_keeps` are omitted, they gracefully fall back to `decay.keeps`.
- If `decay.keeps` is omitted, it defaults to `2` (updated from legacy `3`).
- If `enter` is omitted, it defaults to `P1` (the first configured priority level).
- Old configurations specifying only `freshness.decay.keeps: 3` remain valid syntax.

---

## 7. New Glossary Term Proposal: `Task Decay`

In accordance with SASE conventions, the following markdown strand should be added to `sase/memory/glossary/task-decay.md`:

```markdown
# Task Decay

*Requested · project*

aka status decay, priority decay, lane decay

The automated, entropy-fighting degradation policy that prevents unprogressed or
neglected tasks from stagnating indefinitely across Bob's active lanes and backlog.
When an open task is repeatedly reviewed and kept without progress or completion,
reaching the configured keep limit (default 2 keeps) triggers an explicit decay
decision card down the task lifecycle hierarchy:

1. **WIP Decay**: Stalled in-progress tasks (`[/]`) decay by default to Next (`[*]`),
   releasing capacity in the active WIP lane (`plan.max_pending`).
2. **Next Decay**: Stalled next-up tasks (`[*]`) decay by default to Ready (`[ ]`),
   returning unstarted commitments to the general backlog (`plan.max_next`).
3. **Ready Decay**: Stalled backlog tasks (`[ ]`) decay by default into the scheduled
   priority ladder, entering at P1 with a rolled scheduled date window, clearing the
   daily Ready backlog until due.
4. **Priority Decay**: Scheduled tasks repeatedly rolled at the same priority level
   without execution decay down the priority ladder ($P1 \to P2 \to P3 \to P4$), and
   past P4 decay to cancellation (Drop).

Decay is never a silent background action: reaching a limit prompts an explicit
consent modal during review. The user can accept the default decay transition (`Enter`),
reword the task (`E`), drop it (`D`), or choose to keep it in its current status
(`Alt+F`), which logs a dated reason in the task's `🥀 **ROTTEN LOG**` and resets the
keep streak to zero.

See [[decisions/task-lanes-are-sticky]], [[decisions/rotten-keeps-use-priority-decay]],
[[glossary:keep-streak]], and [[glossary:task-freshness]].
```

---

## 8. Implementation Blueprint & Execution Plan

### 8.1 Repository Changes Summary

```
bob-plugins/
├── plugins/bob-navigation-hotkeys/
│   ├── src/010-requires-and-config.js               # Parse wip_keeps, next_keeps, ready_keeps
│   ├── src/040-priority-roll.js                      # Fix resolveFreshnessDecayP0EntryLevel fallback to P1
│   ├── src/050-decay-planner.js                      # Multi-status decay planner (WIP, Next, Ready)
│   ├── src/060-decay-card-modal.js                   # Status-aware rows and recommended actions
│   ├── src/195-rotten-keep.js                        # Unified Rotten Log formatting (WIP/Next/Ready)
│   ├── src/220-property-targets.js                   # Classify WIP & Next decay targets
│   ├── src/520-plugin-lane-links-and-review.js       # Route WIP & Next <alt+f> to Rotten Log & decay
│   ├── src/530-plugin-freshness-refresh-and-decay.js # Fix this.config bug via loadBulletPropertyConfig()
│   └── src/540-plugin-decay-picker-and-cancel.js     # Apply lane transitions (WIP->Next, Next->Ready)
├── plugins/bob-ledger-tools/
│   ├── src/080-freshness-placement.js                # Allow keepLine counting for WIP & Next
│   └── src/230-plugin-freshness-api.js               # Expose wip/next keep counts & decay flags
bob-cli/
├── src/native/config/freshness.rs                   # Parse wip_keeps, next_keeps, ready_keeps
├── src/native/freshness/state.rs                    # Update decide_for to evaluate WIP & Next lanes
├── docs/freshness.md                                # Document generalized task decay policy
chezmoi/
└── home/dot_config/bob/config.yml                   # Set rolls: 2, keeps: 2, enter: P1 with comments
```

### 8.2 Detailed Step-by-Step Implementation Guide

#### Step 1: Fix the Priority Ladder Lookup Bug in `bob-navigation-hotkeys`
In `plugins/bob-navigation-hotkeys/src/530-plugin-freshness-refresh-and-decay.js`:
- Replace all 4 instances of `findFreshnessDecayPriorityProperty(this.config)` with:
  ```javascript
  const config = loadBulletPropertyConfig({ showNotice: () => {} });
  const property = findFreshnessDecayPriorityProperty(config);
  ```
- In `plugins/bob-navigation-hotkeys/src/040-priority-roll.js`:
  In `resolveFreshnessDecayP0EntryLevel`:
  ```javascript
  // If enterLabel not found or scan misses, default to levels[0] (P1)
  if (!entry && levels.length > 0) {
    return { level: levels[0] };
  }
  ```

#### Step 2: Extend Config Parsers for Lane Keeps
- In `src/native/config/freshness.rs` (Rust) and `010-requires-and-config.js` (JS):
  Add parsing for:
  - `wip_keeps: Option<u16>`
  - `next_keeps: Option<u16>`
  - `ready_keeps: Option<u16>`
  - Update default `keeps` from `3` to `2`.

#### Step 3: Enable Keep Streaks and Decay Evaluation on WIP and Next
- In `bob-ledger-tools/src/080-freshness-placement.js`:
  Update `freshnessKeepLine` so `status === "/"` and `status === "*"` are allowed to increment `[keeps::]` when `counted: true`.
- In `bob-navigation-hotkeys/src/195-rotten-keep.js`:
  Update `classifyRottenKeepTarget` to authorize counting for `lane in ['pending', 'next', 'ready']`.
- In `bob-navigation-hotkeys/src/050-decay-planner.js`:
  Generalize `planFreshnessDecayCard` to support `lane: "pending"` (WIP) and `lane: "next"`.
  When `lane === "pending"`:
  - `Enter`: Decay to Next (`[/] → [*]`).
  - `Alt+F`: Keep in WIP (`[/]`, resets keep streak).
  When `lane === "next"`:
  - `Enter`: Decay to Ready (`[*] → [ ]`).
  - `Alt+F`: Keep in Next (`[*]`, resets keep streak).

#### Step 4: Route WIP `<alt+f>` from Work Log to Rotten Log
- In `bob-navigation-hotkeys/src/520-plugin-lane-links-and-review.js`:
  Remove `isPendingWorkLogTargetRawLine` from `eligibleTargets` (Work Log prompt).
  Include WIP targets in `rottenTargets` alongside Next and Ready.
- In `195-rotten-keep.js`:
  Ensure empty reason strings on Next and WIP fallback to `formatRottenLogEntryText` with `🤷 no reason given · kept in <Status> (<N>×)`.

#### Step 5: Update `chezmoi`'s `bob/config.yml`
Apply the updated configuration:
- Uncomment `properties.priority.decay.rolls: 2`.
- Add `freshness.decay` with `keeps: 2` and `enter: P1`.

---

## 9. Recommended Decisions & Conclusion

### Summary of Recommendations:
1. **Unify Task Decay into a 4-Tier Cascade**:
   Adopt the full cascade: $WIP \to Next \to Ready \to Priority \to Cancel$. This transforms task decay from an ad-hoc cleanup hack into an elegant, structural Kanban workflow engine.
2. **Standardize on 2 Keeps Across All Tiers**:
   2 keeps (allowing 2 consecutive reviews before prompting for decay on the 3rd) provides optimal balance between leniency and active backlog hygiene.
3. **Always Default P0 Decay to P1**:
   Fix the bug in `resolveFreshnessDecayP0EntryLevel` so tasks decaying from Ready always enter at P1, and explicitly configure `enter: P1`.
4. **Enforce 100% Rotten Log Auditability**:
   Eliminate silent keeps for Next tasks and deprecate Work Log prompts for WIP review. Every `<alt+f>` press records a dated Rotten Log entry—either with user rationale or the explicit default `🤷 no reason given · kept in <Status> (<N>×)`.
5. **Reset Streak on "Keep in Status"**:
   Choosing Keep at the decay limit resets `[keeps::]` to 0, granting a clean 2-review grace period and preventing annoying recurring modal interruptions.

This design is reliable, architecturally sound, thoroughly backward-compatible, and beautifully intuitive.
