# Research Report: Morning GTD, Task Freshness, and Pomodoro Practice Review

**Document ID:** `research:202610/morning_gtd_pomodoro_practice_review__gem`  
**Author:** Researcher `gem` (Independent Evaluation)  
**Date:** 2026-10-01  
**Project Context:** `bob-cli` / `bob` Vault / `bob-plugins`  

---

## Executive Summary

Today marked the simultaneous deployment of several foundational architectural changes to your personal task management, planning, and review systems:
1. **Retirement of `#now` in favor of Sticky Next & Pending Lanes** (`bob-cli-2y`, `plan:202609/retire_now_sticky_lanes.md`), deriving Today dynamically from open Pomodoro entries.
2. **Implementation of Rolling Task Freshness Leases** (`bob-cli-31`, `plan:202609/task_freshness_review.md`), replacing the daily 180-task READY scan with lease-based reviews (`[fresh:: YYYY-MM-DD]`).
3. **Capped Daily Plan Budgets & Pomodoro Ledger Limits** (`bob plan`, `docs/plan.md`), capping daily commitments at ≤3 open non-exempt themes and ≤10 Task Links.
4. **Automated Priority Roll Decay** (`bob-cli-34`, `priority_roll_decay.md`), streamlining schedule deferrals and task cancellations via Schedule Log streaks.
5. **Structured Work Logging on Capture Close** (`bob-cli-2z`/`32`), formalizing audit bullets upon Pomodoro completions.

These changes represent a sophisticated evolution away from manual tag curation and full-backlog visual scanning toward **bounded, tooling-assisted workflows**.

However, an examination of your live vault (`~/bob`), daily notes (`2026/20260928.md` through `2026/20261001.md`), and CLI diagnostics reveals significant structural tensions. Most critically:
- **The "Sticky Lane Ratchet" has caused a severe backlog accumulation**: Your live system currently reports **50 PENDING tasks (against a cap of 10)** and **29 NEXT tasks (against a cap of 15)**. Because task promotion is automatic and demotion is manual (`Alt+N`), your 1-month hiatus from morning GTD has created an uncurated pool of "in-progress" ghost tasks.
- **The morning review ritual is overloaded**: The new morning review chore bundles freshness review, due-task resolution, PENDING triage, NEXT curation, and daily plan formulation into an unrealistic "≈10 min" window.
- **The daily note GTD task is an anti-pattern**: In every daily note, `- [*] #task [[gtd_daily]] ^gtd` is instantiated and subsequently cancelled without completion, decoupling the daily Pomodoro ledger from the actual execution of morning routine items.
- **The daily "Highlight" lacks a concrete outcome**: The highlight currently resolves to an entire project theme (e.g. `★ BOB`) containing multiple disparate tasks, rather than a singular finished condition.
- **An impending "Freshness Cliff" looms on October 8**: The cutover seed stamped 390 tasks today with a 7-day lease; without interval adjustments or budget meters, hundreds of stale tasks will come due simultaneously in one week.

Below is a detailed analysis of what is currently breaking or misaligned, followed by a ranked, actionable roadmap of recommended improvements.

---

## 1. Systemic Review of Recent Changes

### 1.1 Sticky Next & In Progress Lanes (Superseding `#now`)
* **Old Baseline:** You relied on a manual `#now` tag to designate weekly or daily focus bets. The dashboard displayed a dedicated `#now` section. Morning review consisted of picking ≤3 themes from yesterday + `[[dash#NOW Tasks|NOW]]`.
* **New Mechanics:**
  - Linking a task raises it to **Next** (`[*]`).
  - Working a task or closing a Pomodoro with `=x` raises it to **In Progress / Pending** (`[/]`).
  - **Sticky Property:** Unlinking, stopping Pomodoros, or running automated hooks (`bob task-status-hooks`) will **never** demote a task. Only an explicit keyboard gesture (`Alt+N`) releases a Next or Pending task back to Ready (`[ ]`).
  - **Today:** Derived at read-time from open Pomodoro Task Links in today's daily note (`2026/YYYYMMDD.md`). `#now` is fully retired.

### 1.2 Rolling Task Freshness Leases
* **Old Baseline:** Every morning, you reviewed the entire `READY` section on `dash.md` (~180 open tasks), attempting to keep each project note at ≤5 ready tasks. This ensured captured ideas were never lost, but imposed heavy recurring visual overhead.
* **New Mechanics:**
  - Non-recurring Ready tasks carry `[fresh:: YYYY-MM-DD]`.
  - Tasks are due for review when **NEW** (captured without a stamp), **RESURFACED** (a scheduled date arrived after the last stamp), or **STALE** (today ≥ fresh + interval, default 7 days).
  - Status bar indicator: `⟳ N due · N new · ✓ N today`.
  - Keyboard navigation: `]s` / `[s` to jump between due tasks; `Alt+Shift+F` to confirm freshness and advance; `Alt+F` to confirm in place.
  - Review chore updated in `gtd_daily.md`: Walk `]s` / `Alt+Shift+F` until 0 new, then clear due items before planning.

### 1.3 Capped Daily Plan Budgets
* **Old Baseline:** Uncompleted Pomodoro blocks and themes accumulated across days. On September 29, 2026, your daily note carried over 12 open Pomodoro entries containing dozens of linked tasks.
* **New Mechanics:**
  - Today's open Pomodoro ledger enforces hard caps: **≤ 3 open non-exempt themes** and **≤ 10 distinct Task Links**.
  - `GTD` is configured as an exempt theme and does not consume theme or link slots.
  - The first open non-exempt theme is marked as the day's **Highlight** (`★`).

---

## 2. What Are You Getting Wrong? (Root Cause Analysis)

### 2.1 The "Sticky Lane Ratchet" (Unbounded PENDING Accumulation)
Running `bob plan -f json` on your live system today returns:
```json
{
  "pending": { "cap": 10, "count": 50, "over": true },
  "next": { "cap": 15, "count": 29, "over": true },
  "warnings": [
    { "code": "next_cap_exceeded", "message": "NEXT has 29/15 tasks; release some with Alt+N" },
    { "code": "pending_cap_exceeded", "message": "PENDING has 50/10 tasks; release some with Alt+N" }
  ]
}
```

#### The Mechanism of Failure
A sticky lane is a **one-way ratchet**:
- Entry into Pending (`[/]`) is automated and frictionless: whenever you start a task or close a Pomodoro with `=x`, `bob capture` promotes the task to `[/]`.
- Exit from Pending requires deliberate, manual intervention: either completing the task (`[x]`) or focusing the task line and pressing `Alt+N` to release it back to Ready (`[ ]`).

Because you stepped away from morning GTD over the past month, the intake valve continued operating while the exit valve remained closed. As a result, **50 tasks are marked as In Progress**, with 40 concentrated in `sase.md` alone.

#### Why This Breaks GTD and Kanban
"In Progress" (WIP) has a strict semantic purpose: *work actively underway or temporarily paused*. When 50 tasks reside in In Progress:
1. **WIP limit collapse:** Having 50 active tasks destroys cognitive focus.
2. **Ghost task contamination:** Multiple tasks in `sase.md` are already completed in reality (e.g., `^release-v18` [v0.18.0 was released], `^tui-screenshot` [command already exists in SASE], `^better-sbd-alias` [already in CLI options], `^services` [tab already renamed]).
3. **Signal erosion:** The `PENDING 50/10` warning becomes permanent background noise, training you to ignore tool warnings.

---

### 2.2 Morning Ritual Overload (The "10-Minute" Fallacy)
The revised chore in `~/bob/gtd_daily.md` reads:
> `Morning review (≈10 min): [[freshness|REVIEW]] until 0 new (]s, Alt+Shift+F), then clear what's due; [[dash#PENDING Tasks|PENDING]] → [[dash#NEXT Tasks|NEXT]]; link today's work, release the rest with Alt+N; ≤3 themes, highlight first`

Tracing what this requires in practice:
1. Walk the Freshness Queue until **0 new** (`]s`, `Alt+Shift+F`).
2. Continue through the queue until **0 due** (or budget met).
3. Inspect `dash#PENDING Tasks` (50 tasks), deciding whether to finish, promote, or `Alt+N` release each.
4. Inspect `dash#NEXT Tasks` (29 tasks), selecting items and releasing the rest down to ≤15.
5. Formulate today's daily Pomodoro ledger: pick ≤3 themes, pick ≤10 Task Links, designate the highlight.
6. Execute routine maintenance: Google Keep import (`bob gkeep pull`), calendar check, email triage.

**This cannot be completed in 10 minutes.** In a real vault, evaluating 20–30 freshness candidates and triaging 79 pending/next tasks takes 30 to 45 minutes of heavy executive function.

**The Human Consequence:** When a daily startup ritual demands 45 minutes of friction-heavy triage, the brain avoids it. Avoiding it for a few days compounds the debt, which eventually resulted in your one-month hiatus.

---

### 2.3 The Daily Note GTD Meta-Task Anti-Pattern (`[[gtd_daily]] ^gtd`)
An analysis of your daily note history shows a persistent pattern:
- **`20260928.md`:** Spent two full Pomodoros on GTD (`1725-1750` and `1805-1830`), yet `- [-] #task [[gtd_daily]] ^gtd` was marked cancelled the next day.
- **`20260929.md`:** Spent one Pomodoro on GTD (`1350-1425`), yet `- [-] #task [[gtd_daily]] ^gtd` was cancelled.
- **`20260930.md`:** `- [-] #task [[gtd_daily]] ^gtd` cancelled.
- **`20261001.md`:** Freshly instantiated as `- [*] #task [[gtd_daily]] [created::2026-10-01] ^gtd`.

#### Why This Is Dysfunctional
1. **Meta-task confusion:** `[[gtd_daily]]` is an area note containing discrete recurring habits (`Check weather`, `Brush teeth`, `Morning review`). Creating an ad-hoc meta-task `- [*] #task [[gtd_daily]]` in the daily note creates a task that never has a clean definition of done. You don't mark it complete because "GTD" isn't a single checkbox.
2. **False cancellation history:** Cancelling `[[gtd_daily]]` every morning trains your subconscious that daily routines are routinely failed or abandoned.
3. **Recurring engine stall:** In `gtd_daily.md`, `Morning review` is a recurring task with `[repeat:: every day when done]`. Because it was not checked off yesterday, Obsidian Tasks never generated today's instance. It currently sits overdue with `[scheduled:: 2026-09-30]`.
4. **Ledger pollution:** In `20261001.md`, `bob plan` reports:
   `TODAY 6` (including `2026/20261001.md#^gtd`). The meta-task inflates your daily commitment count without representing real deliverable work.

---

### 2.4 The "Highlight" as a Project Category Rather than an Outcome
In `ref/chat/pomodoro_ledger_and_daily_roadmap.md`, the expert guidance was:
> *"- The highlight line: Make it an outcome with a finish condition, not a project name. Work it first. It usually takes 2–3 blocks."*  
> (Your annotation at the time was: *"I'm not sure about this."*)

In your implementation:
- `bob plan` designates the first open non-exempt entry as the highlight:
  `★ BOB 3 links`
- In `20261001.md`, the links under `BOB` are:
  - `[[bob#^auto-decay-priorities]]` (a medium-sized epic)
  - `[[bob_gtd#^diagnostics]]` (a diagnostics feature)
  - `[[bob#^web-refs]]` (an ad-hoc capture)

#### Why This Weakens Focus
A project category (`BOB`) is not a highlight. It has no terminal condition. When you sit down to work the highlight block, you are still confronted with three distinct tasks. If you finish one, has the highlight been achieved? If you get pulled into `web-refs`, did you complete your primary objective?

A true daily highlight anchors attention to a single, non-negotiable win for the day. Categorical grouping preserves flexibility but forfeits prioritization.

---

### 2.5 Mid-Day Unfiltered Capture into Today's Ledger
At `00:37:13` EDT today (commit `475022a6`), minutes after formulating today's initial daily plan, you captured:
```markdown
+ [*] #task Turn any website into a reference note! [created::2026-10-01] ^web-refs
```
and immediately added it directly under `- [ ] () — BOB` in `20261001.md`.

#### The Process Leak
One of the core design goals in `pomodoro_ledger_and_daily_roadmap.md` was:
> *"Stop capture from filling the day... capture doesn't add to today unless you mean today."*

When an idea occurs to you during the day, capturing it directly into Next (`[*]`) and slotting it into today's open Pomodoro ledger bypasses the triage boundary. It allows immediate cognitive impulses to preempt commitments established during morning planning.

---

### 2.6 The Impending "Freshness Cliff" (October 8)
When epic `bob-cli-31` landed today, `bob freshness seed` ran across 46 vault files, stamping 390 tasks with `[fresh:: 2026-10-01]`.
Currently, `bob freshness list` reports:
`REVIEW 0 due · 0 new · 0 resurfaced · 0 stale · ✓ 390 today`

#### The Seven-Day Horizon
Because the default freshness interval is 7 days, **all 390 tasks will expire and become STALE on Thursday, October 8, 2026**.
If your backlog still contains dozens of obsolete or completed tasks from your month-long hiatus, next Thursday's morning review will greet you with a crushing queue of 50–100+ stale reviews. This will inevitably trigger rubber-stamping (`Alt+Shift+F` on everything without reading) or prompt another review breakdown.

---

### 2.7 Theme Churn vs. Instantaneous Capping
Your plan budget enforces `themes ≤ 3` on **currently open** entries.
However, reviewing your work on September 30 (`20260930.md`) reveals that you executed 12 Pomodoros across **5 distinct themes**:
- `CLEANUP` (2 sessions, 120m)
- `RESEARCH` (1 session, 50m)
- `BOB` (6 sessions, 185m)
- `BETS` (1 session, 35m)
- `MEMORY` (1 session, 45m)

While the ledger never held more than 3 *open* entries simultaneously, your actual day was fragmented across five separate problem domains. The instantaneous cap prevents visual clutter in the markdown file, but does not sufficiently protect against cognitive fragmentation across the full working day.

---

## 3. Ranked List of Recommended Improvements

The following improvements are ranked by leverage, immediate urgency, and operational impact.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                     RANKED IMPROVEMENT ROADMAP                               │
├────┬─────────────────────────────┬───────────────────────────────────────────┤
│ R1 │ Triage & Drain Sticky Lanes │ Declare PENDING bankruptcy; clear ghosts  │
│ R2 │ Decouple Morning Launch     │ Split 5m Planning from 15m Backlog Review │
│ R3 │ Eliminate Daily GTD Meta-Task│ Link concrete recurring chores directly  │
│ R4 │ Outcome-Based Highlight     │ Star a specific task, not a theme bucket  │
│ R5 │ Enforce Capture Quarantine  │ Day captures go to inbox/project as Ready │
│ R6 │ Defuse the Oct 8 Cliff      │ Note task_refresh & stale_daily_budget    │
│ R7 │ Bound Total Daily Themes    │ Limit sequential theme churn (≤3-4/day)   │
│ R8 │ Protect Weekly Pruning      │ Dedicated time for deep lane clearance    │
└────┴─────────────────────────────┴───────────────────────────────────────────┘
```

---

### Rank 1: Triage and Drain the Sticky Lanes (Declare "PENDING Bankruptcy")
* **Priority:** Critical / Immediate (Today)
* **Rationale:** You cannot evaluate your new workflows while drowning in 50 PENDING tasks and 29 NEXT tasks. The warnings in `bob plan` will continue to fire, and your mental model of WIP will remain broken.
* **Concrete Steps:**
  1. Schedule a dedicated 25-minute Pomodoro titled `CLEANUP — PENDING DRAIN`.
  2. Open `dash.md` and navigate to `## PENDING Tasks`.
  3. Walk the 50 tasks with your editor:
     - If the task is already done in reality (e.g. `^release-v18`, `^tui-screenshot`, `^better-sbd-alias`, `^services` in `sase.md`), mark it complete (`Ctrl+Enter` or swap to `[x]`).
     - If the task is not being worked on *today*, press `Alt+N` to release it back to Ready (`[ ]`).
     - If the task is no longer relevant, cancel it (`Ctrl+Shift+P` → cancel).
  4. Target bringing PENDING to ≤ 5 tasks and NEXT to ≤ 10 tasks.
  5. Run `bob plan` to verify that `pending_cap_exceeded` and `next_cap_exceeded` warnings are eliminated.

---

### Rank 2: Decouple "Daily Launch" (5 min) from "Freshness Review" (15 min)
* **Priority:** High / Process Architecture
* **Rationale:** Combining freshness traversal, PENDING triage, NEXT curation, and daily plan creation into the morning startup guarantees that morning GTD feels heavy and gets skipped.
* **Concrete Steps:**
  1. Redefine your morning startup in `gtd_daily.md` into two distinct phases:
     - **Phase 1: Morning Launch (5 min — Never Skipped)**
       1. Pull external captures: `bob gkeep pull`.
       2. Clear **NEW** freshness items only (`]s` until status bar reads `0 new`). New captures must be seen; this takes <60 seconds.
       3. Review today's calendar and daily constraints.
       4. Review `dash#NEXT Tasks` (kept small from Rank 1) and link today's 3 themes and highlight into the daily note.
     - **Phase 2: Review & Prune (15 min — Midday or Shutdown)**
       - Do not mandate clearing STALE tasks before starting work.
       - Address STALE items during a designated afternoon buffer block or during daily shutdown.
       - Use the status bar's `stale_daily_budget` (see Rank 6) to cap review effort to a fixed daily allotment.

---

### Rank 3: Eliminate the Daily Note GTD Meta-Task Anti-Pattern
* **Priority:** High / Template & Ledger Hygiene
* **Rationale:** Instantiating `- [*] #task [[gtd_daily]] ^gtd` in every daily note creates a zombie task that gets cancelled daily and clutters the Today ledger.
* **Concrete Steps:**
  1. **Update `_templates/daily.md`:**
     Remove:
     ```markdown
     - [*] #task [[gtd_daily]] [created::<% tp.file.creation_date("YYYY-MM-DD") %>] ^gtd
     ```
  2. **Direct Link in Pomodoros:**
     Under `## Pomodoros`, make the GTD entry link directly to the specific recurring morning review chore in `gtd_daily.md`:
     ```markdown
     - [ ] () — GTD
     	- [[gtd_daily#^morning-review]]
     ```
     (Give the `Morning review` line in `gtd_daily.md` a permanent block ID like `^morning-review`).
  3. **Check it off daily:** When your 5-minute morning launch finishes, mark `Morning review` complete (`[x]`). Obsidian Tasks will automatically advance the recurring task to tomorrow, keeping your schedule logs and repeat cycles completely accurate.

---

### Rank 4: Define the Daily Highlight as a Concrete Outcome
* **Priority:** Medium-High / Focus & Productivity
* **Rationale:** Labeling a project container (`BOB`) as the highlight provides no finish condition and encourages multi-tasking.
* **Concrete Steps:**
  1. Continue using your first non-exempt entry as the primary theme.
  2. In your daily note, explicitly designate the single primary deliverable under that theme with a visual indicator or outcome wording.
  3. For example, in `20261001.md`:
     ```markdown
     - [ ] () — BOB
     	- 🎯 [[bob#^auto-decay-priorities]]  <!-- Primary Highlight -->
     	- [[bob_gtd#^diagnostics]]
     ```
  4. Commit to working that specific task during your first deep-work block before context-switching to secondary tasks or routine tickets.

---

### Rank 5: Institute a "No Capture Direct to Today" Quarantine Gate
* **Priority:** Medium / Distraction Defense
* **Rationale:** Capturing an idea like `web-refs` mid-day and immediately inserting it into today's open Pomodoro ledger breaks the planning boundary and introduces reactive churn.
* **Concrete Steps:**
  1. Adopt a strict operational rule: **Any thought captured during the working day lands as Ready (`[ ]`) in its project file or inbox.**
  2. Use Bob Mac Capture or CLI capture without adding the task to today's daily note.
  3. Allow newly captured tasks to sit in the backlog for at least overnight.
  4. If a task is truly an emergency that must be done today:
     - You must explicitly remove or release an existing planned Task Link to make room under the 10-link cap.
     - Never simply append new captures to today's ledger on a whim.

---

### Rank 6: Defuse the October 8 "Freshness Cliff"
* **Priority:** Medium / System Maintenance
* **Rationale:** 390 tasks stamped on October 1 with a 7-day interval will expire on October 8. You need to distribute this review load before it arrives.
* **Concrete Steps:**
  1. **Tune Note-Level Intervals (`task_refresh`):**
     Add frontmatter to high-volume or slower-moving notes in `~/bob/`:
     - `sase.md` (119 open tasks): add `task_refresh: 21` (3-week rolling cycle).
     - Area / Someday notes: add `task_refresh: 30` or `task_refresh: 60`.
     - Fast-turnaround inboxes (`gkeep_inbox.md`): add `task_refresh: 2` or `3`.
  2. **Enable Daily Stale Budget in Config:**
     In `~/.config/bob/config.yml` (managed via chezmoi):
     ```yaml
     freshness:
       interval: 7
       stale_daily_budget: 15
     ```
     This activates the `✓ N/15` meter on your desktop status bar and dash chip. When you hit 15 reviews, the meter marks the review complete for the day (`budget_met: true`), legally authorizing you to stop reviewing and protect your focus.

---

### Rank 7: Constrain Sequential Theme Churn Across the Full Day
* **Priority:** Medium / Cognitive Ergonomics
* **Rationale:** While `bob plan` caps open themes at 3, completing Pomodoros allows an unlimited number of sequential themes across the day (e.g. 5 themes across 12 sessions on Sep 30).
* **Concrete Steps:**
  1. Treat the 3-theme rule as a **whole-day budget**, not just an instantaneous ledger constraint.
  2. Strive to restrict any single day to **at most 3 project themes + GTD**.
  3. If you complete all planned Pomodoros for your 3 themes, reinvest surplus time by doing additional Pomodoros on those same themes (deepening focus) rather than opening a 4th or 5th project domain.

---

### Rank 8: Protect the Weekly Pruning Ritual
* **Priority:** Medium / Long-term System Integrity
* **Rationale:** Under sticky lanes, the Weekly Prune is the essential garbage collector that prevents long-term lane bloat.
* **Concrete Steps:**
  1. Ensure your Monday `Weekly prune` chore is scheduled for a dedicated 30-minute calendar window.
  2. Follow the exact formula in `gtd_daily.md`:
     - Prune `dash#NEXT Tasks` down to ≤ 15 with `Alt+N`.
     - Prune `dash#PENDING Tasks` down to ≤ 10 with `Alt+N`.
     - Defer stalled items using priority roll decay (`Ctrl+Enter`).
     - Sweep notes for projects that have no active Next or Ready tasks.

---

## 4. Summary of Diagnostics & Vault Baseline Metrics

For reference and future audit, here are the baseline metrics extracted from your vault during this research session:

| Metric / Surface | Value on 2026-10-01 | Target / Cap | Health Status |
| :--- | :--- | :--- | :--- |
| **PENDING Lane (`[/]`)** | **50 tasks** | Max 10 | 🚨 **Severe Bloat** (needs Rank 1) |
| **NEXT Lane (`[*]`)** | **29 tasks** | Max 15 | ⚠️ **Over Cap** (needs Rank 1) |
| **Open Daily Themes** | 3 themes (`BOB`, `READ`, `MEMORY`) | Max 3 | ✅ **Healthy** |
| **Open Daily Links** | 5 links | Max 10 | ✅ **Healthy** |
| **Total Stamped Tasks** | 390 tasks | N/A | ⚠️ **Cliff on 2026-10-08** (needs Rank 6) |
| **Freshness Queue Today** | 0 due, 0 new | N/A | ℹ️ Artificially clean due to cutover seed |
| **Daily Routine Task** | `20261001.md#^gtd` | `[x]` | ❌ **Cancelled daily** (needs Rank 3) |

---

## 5. Conclusion

Your recent engineering work on `bob-cli` and `bob-plugins` has delivered an exceptionally powerful, idiomatic GTD environment. The transition to **sticky lanes**, **read-time Today derivation**, **plan budgets**, and **task freshness leases** correctly eliminates the friction of manual tag curation and full-backlog scanning.

What you are getting wrong is not the **architecture**, but the **operational balance**:
1. You implemented an automatic intake valve into PENDING without maintaining the daily manual drainage valve, resulting in 50 lingering "in-progress" tasks.
2. You bundled too much maintenance into the morning startup ritual, making it intimidating and leading to ritual avoidance.
3. You maintained a vestigial GTD meta-task in daily notes that breaks habit completion loops.

By declaring backlog bankruptcy on PENDING today, decoupling 5-minute morning planning from backlog freshness reviews, and adjusting note-level review intervals before October 8, you will establish a lightweight, sustainable rhythm that protects both your deep focus and your system integrity.
