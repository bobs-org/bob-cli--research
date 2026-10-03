# Task Refresh Count Tracking and User-Approved Auto-Decay for Rotten Tasks

**Author:** researcher gem (`research.03.gem`)  
**Date:** 2026-10-03  
**Status:** Research Report  
**Target Repository:** `research:202610/task_refresh_count_and_auto_decay__gem.md`  
**System Scope:** `bob-cli`, `bob-plugins` (`bob-ledger-tools`, `bob-navigation-hotkeys`), Bob Vault Task Grammar, Obsidian Live Preview & Review Walk  

---

## 1. Executive Summary & Thesis

In a mature Getting Things Done (GTD) task management system, task review workflows face a perennial pathology: the **Rotten Review Treadmill** (or "Zombie Task Loop"). When an aging task surfaces in the review queue as rotten, users often re-confirm it (`<alt+f>`) not because of genuine, imminent intent to execute, but to alleviate immediate cognitive discomfort or defer a difficult decision. Over weeks or months, tasks are stamped fresh dozens of times without real-world progress, cluttering the morning review walk (`]s`), inflating active queues, and eroding trust in the freshness system.

The user proposes:
1. Tracking explicit refreshes via `<alt+f>` using a new `refresh_count` property.
2. Rendering this property as an appropriate icon alongside the existing `fresh` mark.
3. Enabling a user-approved auto-decay mechanism for repeatedly refreshed tasks, analogous to Bob's existing auto-decay for repeat priority rolls.
4. Designing this feature to be intuitive, reliable, and beautiful.

### Core Findings & Design Verdict

* **Tracking Repeated Refreshes is Conceptually Vital, but Requires Sparse Storage:**  
  Tracking consecutive refreshes is an essential antidote to review fatigue. However, storing a mandatory or verbose field on every task line causes markdown bloat. We recommend a **sparse inline field** (`[refresh_count:: N]`), which is **omitted entirely when count is 0**, appears only upon consecutive rotten refreshes without task progress, and automatically resets when meaningful work occurs (Pomodoro link, lane promotion, rescheduling, or manual edits).

* **Storage Naming Distinction:**  
  In the Bob vault grammar, `[refresh:: N]` **already exists** and defines the task-specific review interval in days (e.g., `[refresh:: 14]`). Naming the counter `[refresh_count:: N]` is functionally sound and avoids clashing with `[refresh:: N]`, provided that canonical placement and parsing rules strictly recognize both keys without collision.

* **UI: Folded Mark Integration Beats a Disjoint Standalone Icon:**  
  Rendering `refresh_count` as an isolated, standalone icon alongside the `fresh` mark creates a visual "Christmas tree" effect (a disjoint cluster of badges for status, text, fresh, refresh_count, priority, and scheduled). Instead, we follow the elegant precedent established in `docs/freshness.md` §11 (where `[refresh:: N]` folds directly into the freshness mark as an interval suffix). We propose an **Integrated Freshness & Decay Mark**: a single, unified widget that displays the lease ring / due capsule, accompanied by a subtle count badge/tally (e.g. `⟳ 8d · 2×`) that escalates visually only when approaching the decay threshold.

* **Decay Architecture: The Dual-Track Decay Ladder:**  
  Auto-decay must never be silent or punitive. Following the proven model of Bob's Schedule Log priority decay (`projects.md` § "Recommended roll and priority decay"):
  1. **Prioritized Tasks:** Undergo **Priority Demotion** (P1 → P2 → P3 → P4 → Cancellation), resetting the refresh count at each level step.
  2. **Unprioritized Tasks:** Undergo **Interval Backoff** (7d → 14d → 30d leash lengthening) to reduce review frequency, culminating in a recommended Cancellation or Backlog demotion.
  3. **User Approval Mechanism:** Preserves the rapid, single-keystroke cadence of morning review (`]s`). The review notice explicitly displays the recommended decay action before the user strikes the key. Striking `Alt+F` when a task has reached its refresh limit executes the recommended decay with an instant undo capability (`Ctrl+Z`), while a secondary chord (`Alt+Shift+F` or `Alt+Ctrl+F`) allows forcing a keep-fresh override.

---

## 2. Context & Current Architecture

To design this system reliably, we must ground it in Bob's existing freshness, review, and decay architecture across `bob-cli` and `bob-plugins`.

### 2.1 The Freshness Model (`docs/freshness.md`)

```
+-----------------------------------------------------------------------------------------+
|                                    TASK LINE GRAMMAR                                    |
| - [ ] Task description [fresh:: 2026-10-01] [refresh:: 7] [priority:: medium] ^blockid   |
+-----------------------------------------------------------------------------------------+
         |                       |                 |                 |
         v                       v                 v                 v
   Confirmation Date     Review Interval    Tasks Suffix       Trailing Block
     (docs/freshness)      (Overridden by   (priority, sched,       Link
                          note/config/lane)  deps, id, etc.)
```

1. **Storage Fields:**
   * `[fresh:: YYYY-MM-DD]`: The calendar date a human confirmed the task. Placement sits immediately before the trailing Tasks suffix (`created`, `priority`, `scheduled`, `id`, `dependsOn`).
   * `[refresh:: N]`: Optional integer (1–365) defining the task's custom review interval in days. Defaults to note frontmatter `task_refresh`, then config `freshness.interval` (7 days).
2. **Review Walk (`]s` / `[s`):**
   * Traverses active tiers: `NEW → PENDING → NEXT → RETURNED → ROTTEN`.
   * A task is `ROTTEN` when its age (`today - fresh`) meets or exceeds its interval.
   * `Alt+F` (normal) or `Alt+Shift+F` (advance to next due task) executes `stampTaskFreshness` via `api.freshness.stampLine`, which updates `[fresh:: <today>]`.
3. **Display (The Freshness Mark):**
   * Computed at render time in `bob-ledger-tools` via `buildFreshnessMarkElement`.
   * Displays 4 tones: `today` (`✓ today`), `aging` (draining SVG lease ring + `{N}d`), `due` (`⟳ {N}d` in an orange capsule), and `resting` (faint ring for out-of-scope/closed tasks).
   * Refresh folding: When `[refresh:: N]` immediately follows `[fresh:: ...]`, it folds into the mark as `/{N}d`.

### 2.2 The Existing Priority Roll & Decay Architecture (`docs/projects.md`)

Bob already implements a sophisticated auto-decay system for repeated priority scheduling rolls:
1. **Schedule Log Tracking:** Each randomized schedule roll via `Ctrl+Enter` logs an entry under the task's child bullet:
   ```markdown
   - [ ] Roll task [priority:: medium] [scheduled:: 2026-10-01]
       - 🗓️ **SCHEDULE LOG**
           - *2026-10-01* — 🎲 P2 roll · in **17** (8–30) days
   ```
2. **Streak Counting & Limits:**
   * `countPriorityRollStreak` scans the newest consecutive roll reasons at the current level.
   * If `streak < limit` (default `decay.rolls: 1`): Recommends another roll at the same level (`🎲 P2 roll`).
   * If `streak >= limit` and a lower level exists: Recommends **decay** to the next level (`🎲 P2 → P3 decay`).
   * If `streak >= limit` at the lowest level (P4): Recommends **cancel** (`🍂 decayed past P4 after 1 roll`, marking `[-]` and `[cancelled:: today]`).
3. **Approval at Time of Action:**
   * The user triggers `Ctrl+Enter` on the `scheduled` row. The modal/hud displays the exact action (Roll vs Decay vs Cancel). The action only executes when the user activates it.
   * A decay does *not* count as a roll at the new level; the roll streak resets to 0 upon level transition.

---

## 3. Rigorous Critique of the Initial Proposal

The user request poses fundamental questions:
> "Is this a good idea? Would you take a different approach? Make any adjustments to the requirements that you think are justified but clearly call these out."

Here is our analytical critique across the key dimensions of the proposal.

### 3.1 Critique 1: Is Tracking Repeated Manual Refreshes a Good Idea?

* **Verdict: Strongly Endorsed (Essential GTD Hygiene).**
* **The Problem It Solves:**
  In practice, the morning review walk presents cognitive friction. When a user reaches a task that has been stale for 3 weeks, deciding to execute it requires energy, while deleting/cancelling it triggers loss aversion or guilt. Pressing `Alt+F` is an effortless escape hatch: it resets the timer for 7 days, removes the task from the due queue, and provides an artificial sense of "review completion."
  Over time, a significant fraction of the backlog becomes "undead"—perpetually re-stamped without progression. Tracking repeated refreshes makes this implicit habit explicit and measurable.
* **The Risk of Goodhart's Law:**
  If decay is perceived as overly punitive or destructive, users might work around it (e.g. by editing task text or removing tags). Therefore, decay must feel like a helpful assistant pruning back overgrown branches rather than a rigid automated judge.

---

### 3.2 Critique 2: Storage Mechanism — Inline Field vs Child Log

The user proposes: *"using a new `refresh_count` property"*.

#### A. Naming Collision with `[refresh:: N]`
In Bob's Dataview grammar:
* `[refresh:: 7]` means: *"Review this task every 7 days."*
* `[refresh_count:: 3]` would mean: *"This task has been refreshed 3 times consecutively while rotten."*

While semantically different, placing `[refresh:: 7] [refresh_count:: 3]` side-by-side in raw markdown is visually verbose and can easily confuse human readers and automated query authors.

| Option | Syntax | Pros | Cons | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Option A (User's Proposal)** | `[refresh_count:: N]` | Self-documenting; distinct from `refresh`. | Slightly verbose (18-20 characters). | **Viable & Standard** |
| **Option B (Pluralized)** | `[refreshes:: N]` | Shorter (14-16 chars); natural English plural. | Could be mistaken for a list of dates. | Good alternative |
| **Option C (Fresh Count)** | `[fresh_count:: N]` | Pairs symmetrically with `[fresh:: ...]`. | Doesn't emphasize the *act* of refreshing. | Acceptable |
| **Option D (Schedule-Style Log)** | Child `REFRESH LOG` | Rich history of exact dates and notes. | **Fatal flaw:** Indented bullets explode task line height, breaking rapid review walk. | **Rejected** |

**Recommendation:** We adopt `[refresh_count:: N]` as requested, but enforce that it is **strictly sparse**:
* A freshly created task has NO `refresh_count` field.
* A task refreshed for the first time has NO `refresh_count` field (or implicitly 1, but unwritten).
* Only when a task is refreshed a **second consecutive time** without intervening progress does `[refresh_count:: 2]` appear.
* When count resets to 0, the field is **completely removed** from the task line, preventing permanent markdown clutter.

#### B. The "When Does It Reset?" Specification (Crucial Gap in Requirements)
A counter that only increments and never resets is a defect. We must formally define the reset conditions:
1. **Task Action / Progress:** If the task is linked under today's Pomodoros, or its checkbox status changes to Next (`[*]`) or In Progress (`[/]`), `refresh_count` resets to 0 (field removed).
2. **Scheduling / Re-planning:** If the user explicitly reschedules the task (changing `[scheduled:: ...]`) or rolls its priority via `Ctrl+Shift+P`, the task has received deliberate re-planning, not a rubber-stamp refresh. `refresh_count` resets to 0.
3. **Level Decay:** If the task's priority decays (e.g. P2 → P3), `refresh_count` resets to 0 at the new level (identical to priority roll streaks resetting).
4. **Task Done / Cancelled:** If closed (`[x]` or `[-]`), the field is cleaned or ignored.

---

### 3.3 Critique 3: Visual Representation — Standalone Icon vs Integrated Mark

The user proposes: *"This property should be rendered as an appropriate icon (like we do with `fresh`)."*

#### The "Christmas Tree" Trap
In Obsidian task lists, each task line can already contain:
1. Checkbox (`- [ ]`, `- [/]`, `- [*]`)
2. Task description
3. Freshness mark (`✓ today` or `⟳ 8d`)
4. Dependency chip (`Depends on #...`)
5. Priority icon / pill (`P2`)
6. Scheduled date / calendar icon (`🗓️ 2026-10-15`)
7. Block ID (`^abcd12`)

If `refresh_count` is rendered as an independent icon widget (e.g., a standalone `🔁 3` badge floating between the freshness mark and priority), it creates visual dissonance, horizontal jitter, and cognitive noise.

#### The Elegant Solution: Folded Mark Integration
In `docs/freshness.md` §11, Bob established the concept of **field folding**:
* `[refresh:: 14]` does not get its own icon; it folds into the freshness mark as `/{N}d` (`3d/14d`).
* Similarly, `[refresh_count:: N]` should **fold into the existing freshness mark widget**.

```
+-------------------------------------------------------------------------------+
|                       VISUAL MARK PROGRESSION (IN LIVE PREVIEW)               |
+-------------------------------------------------------------------------------+
| State                       | Raw Text                 | Rendered Widget      |
+-----------------------------+--------------------------+----------------------+
| 1. Fresh (Initial)          | [fresh:: 2026-10-08]     | (circle-check) today |
| 2. Aging (Mid-lease)        | [fresh:: 2026-10-04]     | (lease ring) 4d      |
| 3. Rotten (1st time due)    | [fresh:: 2026-09-28]     | [⟳ 10d]              |
| 4. Rotten (Refreshed 1x)    | [fresh:: ...] [cnt:: 1]  | [⟳ 8d · 1×]          |
| 5. Rotten (Refreshed 2x)    | [fresh:: ...] [cnt:: 2]  | [⟳ 7d · 2×]          |
| 6. Decay Ready (3x Limit)   | [fresh:: ...] [cnt:: 3]  | [⟳ 9d · 3× 🍂]       |
+-----------------------------+--------------------------+----------------------+
```

* **Visual Design:**
  * When `refresh_count` is 0 or absent: Standard freshness mark.
  * When `refresh_count` is 1 or 2: A quiet counter appended to the label: `⟳ 8d · 2×`, or a subtle tally dot.
  * When `refresh_count >= 3` (Decay Threshold): The capsule gains an amber accent border and a subtle decay indicator (`🍂` or flame/arrow icon), signaling that the next refresh will trigger auto-decay.
* **Fallback:** If a raw task line contains `[refresh_count:: N]` without a valid `[fresh:: ...]` stamp, it renders as a standalone Dataview inline field pill with a repair warning, exactly following the repair rule in `docs/freshness.md` §11.

---

## 4. Auto-Decay Paradigms: Comparative Analysis

The user writes:
> "The goal of this change is to enable some sort of (user approved--at the time of decay) auto-decay for tasks that continue to be manually refreshed, but I haven't got that part worked out yet. We already support auto-decay for repeat priority rolls but not for repeat rotten task refreshes. Think hard about the best way to do this."

What does it mean for a repeatedly refreshed task to "decay"? We analyze four distinct mechanisms.

### 4.1 Four Possible Decay Actions

```
                                  +-----------------------+
                                  | Task Rotten & Alt+F   |
                                  | refresh_count >= limit|
                                  +-----------------------+
                                              |
                   +--------------------------+--------------------------+
                   |                          |                          |
                   v                          v                          v
          [Track A: Priority]       [Track B: Interval]       [Track C: Lane/Res]
          P1 -> P2 -> P3 -> P4      7d -> 14d -> 30d -> 90d   Release Next -> Ready
                   |                          |               Move to Someday/Maybe
                   v                          v                          |
        +----------------------------------------------------------------+
        |
        v (Past Terminal Threshold)
    [Terminal: Cancellation]
    [-] [cancelled:: today]
    Cancel Log: "🍂 decayed after N refreshes"
```

#### 1. Priority Demotion Ladder (The Direct Analog to Schedule Rolls)
* **How it works:**
  * If the task has `[priority:: high]` (P1), repeated refreshes demote it to `[priority:: medium]` (P2).
  * P2 demotes to P3 (low).
  * P3 demotes to P4 (lowest).
  * Past P4: Cancellation (`[-]` with Cancel Log).
* **Pros:** Directly mirrors `docs/projects.md` § "Recommended roll and priority decay". Fits Bob's existing mental model perfectly.
* **Cons:** What about tasks that have *no* priority field? In the Bob vault, many valid tasks do not have `[priority:: ...]`. Demoting an unprioritized task directly to Cancel might feel too aggressive.

#### 2. Interval Backoff (Exponential Review Leash Lengthening)
* **How it works:**
  * If a task is refreshed repeatedly at 7 days, its review interval automatically lengthens:
    `7 days → 14 days → 30 days → 90 days`.
  * Written to `[refresh:: 14]`, then `[refresh:: 30]`, etc.
* **Pros:** Highly respectful of tasks that the user genuinely wants to keep but doesn't need to see every week. It immediately removes review walk congestion without altering priority or cancelling work.
* **Cons:** It doesn't force a real decision; tasks can still hide in 90-day hibernation loops indefinitely.

#### 3. Lane / Residence Demotion
* **How it works:**
  * If a Next (`[*]`) or Pending (`[/]`) task is refreshed repeatedly without being completed, it is released back to Ready (`[ ]`) via Alt+N mechanics.
  * If a Ready task is refreshed repeatedly, it is tagged `#someday` or moved to the project's Someday/Backlog section.
* **Pros:** Keeps the active Ready lane clean.
* **Cons:** Modifying file structure or tags during a rapid keyboard review walk can be jarring.

#### 4. Terminal Cancellation (`[-]` with Decay Reason)
* **How it works:**
  * The task checkbox flips to `[-]`, appends `[cancelled:: YYYY-MM-DD]`, and writes a Cancel Log bullet:
    `- *2026-10-08* — 🍂 decayed after 3 rotten refreshes`.
* **Pros:** Definitive closure. Prevents eternal backlog debt.
* **Cons:** Destructive if done without explicit, unambiguous user consent.

---

### 4.2 The Recommended Solution: The Unified Dual-Track Decay Ladder

We recommend a **Dual-Track Decay Architecture** configured in Bob:

1. **Track 1: Prioritized Tasks (Priority Ladder)**
   * If a task carries `[priority:: ...]`, reaching `refresh_count >= limit` triggers **Priority Decay**:
     $$\text{P1} \xrightarrow{\text{decay}} \text{P2} \xrightarrow{\text{decay}} \text{P3} \xrightarrow{\text{decay}} \text{P4} \xrightarrow{\text{decay}} \text{Cancel}$$
   * At each decay step, the priority field is updated, `refresh_count` resets to 0, and a Schedule Log entry is added:
     `- *2026-10-08* — 🍂 P2 → P3 decay after 3 refreshes`.
   * When decaying past P4, the task is cancelled with reason:
     `🍂 decayed past P4 after 3 refreshes`.

2. **Track 2: Unprioritized Tasks (Interval Backoff $\rightarrow$ Someday/Cancel)**
   * If a task has *no* priority property:
     * First decay threshold (3 refreshes): Lengthen interval from 7d to 14d (`[refresh:: 14]`), reset count.
     * Second decay threshold (3 more refreshes at 14d): Lengthen interval to 30d (`[refresh:: 30]`), reset count.
     * Third decay threshold (3 more refreshes at 30d): Recommend terminal cancellation (`[-]`) or `#someday`.

---

## 5. Interaction Design: "User-Approved at Time of Decay"

The most critical UX challenge is: **How does user approval work without destroying the speed of the morning review walk?**

During the `]s` morning walk, Bryan reviews dozens of tasks in seconds using `Alt+F` (keep) and `Alt+Shift+F` (keep and advance). If a modal dialog suddenly pops up on every decayed task requiring multiple clicks or Enter presses, review flow is destroyed. Conversely, if decay happens completely silently, tasks will change priority or disappear without Bryan realizing it.

We evaluated three interaction models:

```
[Model 1: Blocking Modal]        [Model 2: Silent Auto-Decay]      [Model 3: The Review Chords & HUD]
+-------------------------+      +--------------------------+      +---------------------------------+
| "Decay Task?"           |      | Alt+F pressed            |      | Walk Notice warns before press  |
| [Decay] [Keep] [Cancel] |      | -> Silently demotes P2->P3|      | Alt+F executes recommended decay|
+-------------------------+      +--------------------------+      | Alt+Shift+F forces plain fresh  |
   High friction (bad)             Zero visibility (bad)           | Notice shows result + Ctrl+Z    |
                                                                   +---------------------------------+
                                                                       Intuitive, fast, safe (BEST)
```

### The Recommended Interaction Model: "Notice-Guided Review Chords"

This model mirrors the exact philosophy of Bob's existing `Alt+N` and `Ctrl+Enter` interactions in `bob-navigation-hotkeys`.

#### 1. Pre-Action Signaling (Look Ahead)
When Bryan lands on a rotten task (`]s`), the review notice at the top of the editor displays the task's state.
* If `refresh_count < limit` (e.g. count is 1 of 3):
  ```
  Review 4/12 · ROTTEN (1/3 refreshes) · confirmed Sep 20
  Alt+F to confirm · Alt+Shift+F confirm & advance
  ```
* If `refresh_count >= limit` (e.g. count is 3 of 3):
  The notice switches to a **high-visibility decay recommendation**:
  ```
  Review 4/12 · ROTTEN (3/3 refreshes) · confirmed Sep 20
  ⚠️ Refresh limit reached: Alt+F will DECAY (P2 → P3)
  Alt+F decay & confirm · Alt+Shift+F force fresh (keep P2) · Ctrl+D cancel
  ```

#### 2. The Keyboard Gestures at Decay Threshold
When Bryan is on a task that has reached the decay threshold:
* **Primary Key (`Alt+F`): Execute Recommended Decay.**
  * Applies the decay: updates `[priority:: low]`, resets `[refresh_count:: 0]`, and stamps `[fresh:: today]`.
  * Logs the decay in the task's child log.
  * Shows a distinct confirmation notice:
    ```
    🍂 Decayed P2 → P3 · Fresh ✓ 1 task · 18 due (2 new) · ✓ 5 today · Press Ctrl+Z to undo
    ```
* **Override Key (`Alt+Shift+F` or `Alt+C`): Force Keep Fresh Without Decay.**
  * If Bryan genuinely needs to keep this task at P2 without decaying it, pressing `Alt+Shift+F` (or an explicit override chord) keeps the priority, stamps fresh, and resets or increments the counter according to config.
* **Terminal Decay Guard (Cancellation):**
  * When a task at P4 reaches its limit, `Alt+F` does *not* instantly delete it without a pause. The notice displays:
    `🍂 Final decay limit: Alt+F cancels task · Alt+Shift+F keep alive`.
    Pressing `Alt+F` cancels the task (`[-]`, `[cancelled:: today]`) with immediate notice and undo support.

This design achieves complete user approval:
1. The user is informed of the consequence **before** typing.
2. The default action is the recommended hygiene action (decay), requiring no extra keystrokes.
3. Overriding is a standard, familiar chord.
4. Mistakes are instantly reversible via standard editor Undo (`Ctrl+Z`).

---

## 6. Technical Architecture & Implementation Plan

Implementing this feature cleanly requires coordinating changes across `bob-cli` (Rust) and `bob-plugins` (`bob-ledger-tools` and `bob-navigation-hotkeys`).

### 6.1 Data Model & Grammar Rules

#### Canonical Field Syntax
* Field key: `refresh_count`
* Field value: Positive integer $\ge 1$ (e.g. `[refresh_count:: 2]`)
* Sparsity rule: Omitted when 0 or null. Never write `[refresh_count:: 0]`.

#### Placement Rule (Rust & TypeScript)
In `src/native/freshness/placement.rs` and `bob-ledger-tools/main.js`:
The task line is partitioned into:
$$\text{Line} = \text{Head} + \text{Freshness Group} + \text{Tasks Suffix}$$
Where:
* **Freshness Group** consists strictly of:
  `[fresh:: YYYY-MM-DD]` + optional `[refresh:: N]` + optional `[refresh_count:: N]`
* Tasks Suffix consists of:
  `priority`, `start`, `created`, `scheduled`, `due`, `completion`, `cancelled`, `repeat`, `onCompletion`, `id`, `dependsOn`, trailing tags, and trailing block ID (`^id`).

```rust
// In src/native/freshness/placement.rs:
// Both fresh, refresh, and refresh_count extend the scanned run without
// becoming part of the Tasks suffix.
if key == "fresh" || key == "refresh" || key == "refresh_count" {
    cursor = field_start;
    cursor = trim_end_to(&line[..cursor], cursor);
    continue;
}
```

```javascript
// In bob-ledger-tools (freshnessRebuildWithoutFields):
let output = head + " [fresh:: " + dateText + "]";
if (keptRefresh !== null && keptRefresh !== undefined) {
  output += " [refresh:: " + keptRefresh + "]";
}
if (keptRefreshCount !== null && keptRefreshCount > 0) {
  output += " [refresh_count:: " + keptRefreshCount + "]";
}
if (suffix !== "") {
  output += " " + suffix;
}
```

---

### 6.2 Visual Mark Rendering & Styling (`bob-ledger-tools`)

#### A. DOM Anatomy
In `buildFreshnessMarkElement(doc, model, options)`:
```html
<span class="bob-fresh-mark" data-tone="due" data-resolved="true" role="img" aria-label="...">
  <svg class="bob-fresh-mark-glyph" viewBox="0 0 16 16">
    <!-- SVG Glyph: circle check, draining lease ring, or rotate-cw arrow -->
  </svg>
  <span class="bob-fresh-mark-label">8d</span>
  <!-- Optional Interval Suffix -->
  <span class="bob-fresh-mark-interval">/14d</span>
  <!-- NEW: Refresh Count Badge -->
  <span class="bob-fresh-mark-count" data-count="3">· 3×</span>
</span>
```

#### B. CSS Styles (`bob-ledger-tools/styles.css`)
```css
/* Refresh count badge inside the freshness mark */
.bob-fresh-mark-count {
  font-size: 0.88em;
  opacity: 0.7;
  font-weight: 600;
  margin-inline-start: 0.15em;
  letter-spacing: -0.02em;
}

/* Subtle styling for initial repeat (1x, 2x) */
.bob-fresh-mark-count[data-count="1"],
.bob-fresh-mark-count[data-count="2"] {
  color: var(--text-muted);
}

/* Warning accent when reaching decay threshold (>= 3) */
.bob-fresh-mark[data-tone="due"]:has(.bob-fresh-mark-count[data-count="3"]) {
  --bob-fresh-color: var(--color-orange, #d9822b);
  box-shadow: inset 0 0 0 1.5px color-mix(in srgb, var(--color-red, #e05555) 50%, var(--color-orange));
  background-color: color-mix(in srgb, var(--color-orange) 18%, transparent);
}

.bob-fresh-mark-count[data-count="3"] {
  color: var(--color-red, #e05555);
  font-weight: 700;
}
```

#### C. Tooltip Expansion
Line 1: `Confirmed Thu, Sep 24 · 14 days ago (refreshed 2 times consecutively)`  
Line 2: `Due for review since Oct 1 · every 7 days`  
Line 3 (when due):
* If `count < limit`: `Alt+F to confirm (refresh 3/3 will trigger decay)`
* If `count >= limit`: `⚠️ Refresh limit reached: Alt+F decays priority (P2 → P3) · Alt+Shift+F force keeps`

---

### 6.3 Decay Execution & Hotkey Logic (`bob-navigation-hotkeys`)

When `Alt+F` is triggered, `refreshTaskFreshness` executes the following state machine:

```javascript
function planTaskFreshnessRefresh(lineText, dateText, config) {
  const currentRead = readFreshness(lineText, dateText);
  const currentCount = currentRead.refreshCount || 0;
  const decayLimit = config.freshnessDecayLimit || 3;
  
  // Case 1: Under limit -> plain stamp with incremented count
  if (currentCount + 1 < decayLimit) {
    const nextCount = currentCount + 1;
    const newLine = freshnessStampLineWithCount(lineText, dateText, nextCount);
    return { kind: "stamp", line: newLine, count: nextCount };
  }
  
  // Case 2: At or above limit -> plan Decay
  const priorityField = findBulletPropertyField(lineText, "priority");
  if (priorityField && priorityField.value) {
    const decayPlan = planPriorityDecayForRefresh(lineText, priorityField.value, config);
    return {
      kind: "decay-priority",
      fromLevel: decayPlan.fromLevel,
      toLevel: decayPlan.toLevel,
      line: decayPlan.newLine,
      logEntry: decayPlan.logEntry
    };
  }
  
  // Case 3: Unprioritized task -> interval backoff
  const nextInterval = calculateIntervalBackoff(currentRead.interval);
  const newLine = freshnessSetRefreshLineWithCount(lineText, nextInterval, dateText, 0);
  return {
    kind: "decay-interval",
    newInterval: nextInterval,
    line: newLine
  };
}
```

---

### 6.4 Config Schema (`config.yml` in `bob-cli`)

We extend `FreshnessConfig` in `src/native/config/freshness.rs` and the JS config validator:

```yaml
freshness:
  interval: 7
  pending_interval: 1
  next_interval: 1
  rotten_daily_budget: 15
  decay:
    enabled: true          # default true
    refreshes: 3           # default: 3 consecutive refreshes triggers decay
    action: priority       # "priority" (demote P-level) or "interval" (lengthen leash)
    terminal: cancel       # "cancel" (flip to [-]) or "someday" (tag #someday)
```

---

## 7. Edge Cases, Failure Modes & Safeguards

| Scenario / Edge Case | Risk / Problem | Mitigation Strategy |
| :--- | :--- | :--- |
| **Recurring Tasks (`repeat::`)** | Recurrence rules in Tasks copy stamps to the next instance. | In `placement.rs` and `freshnessStampLine`, recurring tasks explicitly refuse freshness stamps (`refused: "recurring"`). Decay must **never** touch recurring tasks. |
| **Dedicated Task Links** | Alt+F on a Task Link in a daily note/dashboard must update the target task in its home project note. | `refreshTaskFreshnessOnLinks` already handles cross-file transaction plans with preimage checks and rollbacks. The new decay plan seamlessly passes through this pipeline. |
| **Vim Normal Mode Event Swallowing** | CodeMirror Vim intercepts Alt keys in normal mode. | `bob-navigation-hotkeys` uses a capture-phase DOM event listener (`registerReviewRefreshInputListeners`) specifically to catch `Alt+F` before Vim eats it. The decay hotkeys use this exact mechanism. |
| **Concurrent File Changes** | Another process modifies the markdown file while review is active. | Checked by `guarded.content !== content`. If the file changes, the transaction aborts with a Notice: `"Current note changed; no tasks were updated"`. |
| **Accidental Decay** | User strikes `Alt+F` out of habit without reading notice and unintentionally decays priority. | 1. Visual pre-alert on the widget (`🍂` badge).<br>2. Full undo support via standard `Ctrl+Z`.<br>3. Schedule Log documents the transition transparently. |
| **Unprioritized Backlog Items** | A user has hundreds of tasks without P-levels; decaying shouldn't immediately delete them. | Dual-track fallback: Unprioritized tasks first undergo interval backoff (7d → 14d → 30d) before terminal cancellation is ever offered. |

---

## 8. Conformance & Test Vectors

To guarantee synchronization between Rust (`bob-cli`) and JavaScript (`bob-plugins`), the test suites must implement shared conformance vectors.

### 8.1 Placement Vectors (Extending P-vectors in `docs/freshness.md` §9)
* **P13 (First Refresh):**
  * Input: `- [ ] Buy coffee [fresh:: 2026-10-01] [priority:: medium]`
  * Action: Stamp today `2026-10-08`
  * Output: `- [ ] Buy coffee [fresh:: 2026-10-08] [refresh_count:: 1] [priority:: medium]`
* **P14 (Second Consecutive Refresh):**
  * Input: `- [ ] Buy coffee [fresh:: 2026-10-08] [refresh_count:: 1] [priority:: medium]`
  * Action: Stamp today `2026-10-15`
  * Output: `- [ ] Buy coffee [fresh:: 2026-10-15] [refresh_count:: 2] [priority:: medium]`
* **P15 (Reset on Progress/Action):**
  * Input: `- [ ] Buy coffee [fresh:: 2026-10-08] [refresh_count:: 2] [priority:: medium]`
  * Action: Promoted to Next (`[*]`) or scheduled
  * Output: `- [*] Buy coffee [fresh:: 2026-10-08] [priority:: medium]` (`refresh_count` removed).

### 8.2 Mark Conformance Vectors (Extending M-vectors in `docs/freshness.md` §12)
* **M10 (Mark with Count 1):**
  * Raw: `[fresh:: 2026-10-01] [refresh_count:: 1]` on 2026-10-08.
  * Tone: `due`, Glyph: `refresh`, Label: `7d`, Count Badge: `· 1×`.
  * Tooltip: `Confirmed Thu, Oct 1 · 7 days ago (refreshed 1 time)\nDue for review since today · every 7 days\nAlt+F to confirm`.
* **M11 (Mark at Decay Threshold):**
  * Raw: `[fresh:: 2026-10-01] [refresh_count:: 3]` on 2026-10-08.
  * Tone: `due`, Glyph: `refresh`, Label: `7d`, Count Badge: `· 3× 🍂`.
  * Tooltip includes: `⚠️ Refresh limit reached: Alt+F will decay priority (P2 → P3)`.

### 8.3 Decay Vectors (Extending D-vectors in `test-navigation-roll-decay.cjs`)
* **D1 (Priority Decay P2 → P3):**
  * Task: `- [ ] Review specs [fresh:: 2026-10-01] [refresh_count:: 3] [priority:: medium]`
  * Action: `Alt+F` on 2026-10-08
  * Result: `- [ ] Review specs [fresh:: 2026-10-08] [priority:: low]` + Schedule Log bullet:
    `- *2026-10-08* — 🍂 P2 → P3 decay after 3 refreshes`.
* **D2 (Terminal Decay Past P4):**
  * Task: `- [ ] Clean attic [fresh:: 2026-10-01] [refresh_count:: 3] [priority:: lowest]`
  * Action: `Alt+F` on 2026-10-08
  * Result: `- [-] Clean attic [cancelled:: 2026-10-08]` + Cancel Log bullet:
    `- *2026-10-08* — 🍂 decayed past P4 after 3 refreshes`.

---

## 9. Recommended Phased Implementation Roadmap

We recommend executing this work in four structured phases:

1. **Phase 1: Canonical Grammar & Parser Synchronization (Rust & JS)**
   * Update `src/native/freshness/placement.rs` in `bob-cli` to recognize and clean `[refresh_count:: N]`.
   * Update `freshnessTasksSuffixStart`, `freshnessStampLine`, and `freshnessRebuildWithoutFields` in `bob-ledger-tools`.
   * Add placement conformance tests (P13–P15) to both repositories.

2. **Phase 2: Visual Mark & Live Preview Styling**
   * Extend `freshnessMarkModel` and `buildFreshnessMarkElement` in `bob-ledger-tools` to fold the count badge into the mark.
   * Add CSS styles for `.bob-fresh-mark-count` and decay threshold accent rings.
   * Verify rendering across light and dark Obsidian themes and Tasks query codeblocks.

3. **Phase 3: Decay Planner & Review Walk Integration**
   * Implement `planTaskFreshnessRefresh` in `bob-navigation-hotkeys`.
   * Wire `Alt+F` and `Alt+Shift+F` handlers to check `refresh_count` against `config.freshness.decay.refreshes`.
   * Integrate Schedule Log and Cancel Log appenders for decayed tasks.
   * Update review walk jump notices (`buildReviewJumpNotice`) to display decay warnings.

4. **Phase 4: Headless CLI & Diagnostic Support**
   * Update `bob freshness list` and `bob freshness list -f json` in `bob-cli` to display `refresh_count` and flag decay-ready tasks.
   * Run a two-week personal trial in Bryan's vault, monitoring keep rates, decay frequency, and review walk velocity.

---

## 10. Conclusion & Final Recommendation

The user's instinct to address repeat rotten task refreshes is spot on: personal productivity systems fail not from lack of capture, but from **backlog sclerosis** caused by frictionless, guilt-driven re-deferrals.

By implementing:
1. **Sparse `[refresh_count:: N]` tracking** that resets upon active work,
2. **Folded visual integration** inside the existing freshness mark widget rather than a noisy second icon, and
3. **A Dual-Track Priority & Interval Decay Ladder** executed via intuitive **Notice-Guided Review Chords**,

Bob will gain an auto-decay system that is completely reliable, non-disruptive to morning review speed, and visually stunning.
