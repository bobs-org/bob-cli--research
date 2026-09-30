# Task Freshness and GTD Workflow Redesign: Research, Critique, and Architecture

- **Research Date:** 2026-09-30
- **Author:** Researcher `gem` (Swarm Evaluation)
- **Topic:** Task Freshness (`fresh`), Daily Inbox Triage, and Backlog Maintenance in Bob GTD
- **Context:** `bob-cli-2y` epic (Retiring `#now`, sticky Next/Pending lanes, ledger-derived Today), `bob-plugins`, `bob gkeep`, `dash.md`
- **Target File:** `sase/repos/research/202609/task_freshness_review__gem.md`

---

## 1. Executive Summary: In One Breath

> **The diagnosis:** You are attempting to solve two fundamentally different problems with a single mechanism:
> 1. **Daily In-Basket Triage:** Glancing at tasks captured in the last 24–48 hours (e.g., Google Keep voice capture of your wife asking to pick up your daughter) so urgent commitments are never dropped.
> 2. **Rolling Backlog Grooming:** Keeping 186+ project tasks from rotting in a dormant `READY` backlog because you do not do a weekly review.
>
> **The trap:** If you treat newly captured inbox tasks simply as "unfresh" tasks and pool them into a generic 7-day freshness review, you will face **~25 to 30 tasks to review every morning**. If you attempt to cope by capping that review to $N$ tasks per day (e.g., $N = 10$), **you will inevitably miss your daughter's pickup** whenever that note is sorted past item 10.
>
> **The technical landmine:** Obsidian Tasks' parser evaluates Dataview inline fields strictly from right to left using a hardcoded whitelist. Appending `[fresh:: YYYY-MM-DD]` at the end of a task line will cause the parser to abort, hiding every `[scheduled:: ...]`, `[priority:: ...]`, `[id:: ...]`, and `[dependsOn:: ...]` field to its left.
>
> **The recommended solution:** Decouple the workflow into two strict tiers:
> - **Tier 1: Daily Inbox (Zero-Tolerance, Uncapped, ~30 Seconds):** A dedicated `INBOX` section at the very top of `dash.md` isolating `gkeep_inbox.md` and unfiled captures. This guarantees you never miss a newly captured commitment.
> - **Tier 2: Rolling Task Freshness (Anti-Rot, Paced, Capped):** Implement `[fresh:: YYYY-MM-DD]` placed *immediately after the task description* (before trailing Tasks metadata), with 7-day default interval, project frontmatter and task-level overrides, automatic updates via supported keymaps (`Alt+N`, `Ctrl+Shift+P`, `Ctrl+Shift+]`, `Alt+[`/`]`), dedicated navigation/refresh keymaps (`Alt+F`), and a paced daily queue on `dash.md` (capped at 10 items) to smoothly amortize weekly review work without morning fatigue.

---

## 2. Problem Analysis & Current State

### 2.1 The Daily Capture Hazard: The "Speed-Walking" Scenario
During your daily activities, you capture quick commitments (e.g., while speed-walking with your wife, who asks you to pick up your daughter in the morning). You add this to Google Keep. The next morning, `bob gkeep pull` drains your Keep inbox into the Bob vault. 

In `src/native/gkeep/render.rs`, each Keep note is rendered as:
```markdown
- [ ] #task Pick up daughter [created::2026-09-30]
	- Source: [Google Keep](...) · 2026-09-30 07:15 %%gkeep:v1:...%%
```
This lands directly in `~/bob/gkeep_inbox.md`.

Because `gkeep_inbox.md` tasks have an unchecked checkbox (`- [ ]`) and `#task`, their status type is `TODO`. 

### 2.2 The Dash Breakdown: Why Reviewing READY Failed
In `~/bob/dash.md`, the sections are:
```tasks
### TODAY Tasks
not done
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) === true
sort by function (globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.todayRank?.(task) ?? 0)

### PENDING Tasks
status.type is IN_PROGRESS
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true
sort by created

### NEXT Tasks
status.name includes Next
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true
sort by priority

### READY Tasks
status.type is TODO
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true
```

Notice that `READY Tasks` matches **every single open `TODO` task in the vault** that is not linked in today's ledger:
- It includes all 45+ unfiled notes in `gkeep_inbox.md`.
- It includes all 140+ active project tasks across `sase.md`, `sase_usage.md`, `sase_decks.md`, `sase_remote.md`, etc.
- As observed live during research, `READY Tasks` currently contains **186 tasks**.

When you relied on reviewing the `READY` section every morning and trying to keep ready tasks per project $\le 5$, you were forced to scan through **186 backlog tasks** every single morning just to find the 1 or 2 new captures from yesterday. This created severe cognitive friction, time waste, and review fatigue, leading to the collapse of that daily habit.

### 2.3 The Absence of a Weekly Review
You noted that you do not currently perform a formal GTD weekly review. Without a weekly review, backlogs naturally accumulate "dark matter"—tasks that were once relevant but have sat untouched for weeks or months. You hope that by introducing an automated "task freshness" expiration, you can eliminate the need for a separate weekly review by amortizing backlog maintenance continuously into your morning routine.

---

## 3. Critique of the Proposed "Task Freshness" Design

Your proposed policy introduces:
1. A property `fresh: <date>` indicating the last time a human confirmed the task.
2. A default refresh interval of 7 days (overridable per task or via project frontmatter).
3. Automatic freshness timestamp updates when supported Obsidian keymaps modify the task.
4. An out-of-date task review queue in the morning, where inbox tasks are out-of-date by default.
5. Navigation hotkeys (jump next/prev out-of-date) and a touch/refresh hotkey.
6. A potential daily cap of $N$ out-of-date tasks per day to prevent morning overwhelm.

While this proposal is creative and addresses real symptoms, a rigorous analysis reveals several critical vulnerabilities that must be resolved.

### 3.1 Critique 1: The "Daily Cap Fatal Flaw" (Conflating Inbox with Backlog)
This is the single most dangerous flaw in the proposed plan.

In GTD, **Inbox Triage** and **Backlog Review** have completely different service-level objectives (SLOs):
- **Inbox Triage:** High urgency, low volume (1–5 items/day). Requires 100% review completeness every morning. Zero items can be dropped, because an inbox item might be a time-sensitive commitment for today.
- **Backlog Review:** Low urgency, high volume (180+ items). Does not require immediate same-day action; items can be reviewed on a rolling basis or deferred.

If you treat newly captured inbox tasks as simply "unfresh" tasks and lump them into the general out-of-date queue:
- In a vault of 186 tasks with a 7-day interval, approximately **25 to 30 tasks will expire every day**.
- Mixed into that list of 30 tasks will be the Keep note from yesterday ("Pick up daughter").
- If you find 30 tasks too overwhelming and implement your idea of "limiting myself to reviewing $N$ out-of-date tasks per day" (say, $N = 10$), what happens?
- If the query sorts by project path or priority or oldest created date, **"Pick up daughter" may be item #15 or #22 in the list**.
- It will be truncated by the cap. **You will not see it. You will miss picking up your daughter.**

**Verdict:** Newly captured inbox items must **never** compete in a capped rolling backlog queue. They must have their own dedicated, uncapped, instant-glance surface.

### 3.2 Critique 2: The "Morning Review Bloat" & Review Theatre
Let's examine the steady-state mathematics of a 7-day refresh interval across your current vault:
- Current `READY` tasks: $\approx 186$.
- Steady-state daily expirations: $186 / 7 \approx 26.5$ tasks expiring every day.
- Add daily Keep captures: $\approx 2$ to $5$ tasks.
- **Total morning review volume:** **$\approx 30$ tasks every morning, 7 days a week.**

Your stated goal in epic `bob-cli-2y` was:
> `Morning review (≤5 min): PENDING → NEXT → READY; link today's work, release the rest with Alt+N; ≤3 themes, highlight first`

Evaluating 30 tasks thoughtfully in 5 minutes means spending **10 seconds per task**. 
In reality, when faced with 30 tasks every morning, human nature takes over:
- You will simply press the "refresh" keymap repeatedly to clear the queue without actually reading or evaluating the tasks ("refresh theatre").
- Alternatively, you will skip the review after 3 days because 30 tasks every morning is exhausting.

### 3.3 Critique 3: Metadata Pollution and Git Worktree Noise
If 186 tasks are updated every 7 days:
- You will generate $\approx 27$ task line edits every single day.
- Over a month, that is **$\approx 800$ line modifications** across 15+ project markdown files.
- `bob vault-sync` runs Git commits across your devices. Your Git history will be dominated by commits whose sole change is bumping `[fresh::2026-09-23]` to `[fresh::2026-09-30]`.
- Task lines become cluttered with metadata tags:
  `- [ ] #task Do thing [fresh::2026-09-30] [fresh_interval::14d] [created::2026-08-12] [priority::medium] [scheduled::2026-10-15] ^id`

### 3.4 Critique 4: The Technical Hazard with Obsidian Tasks Parser
This is a critical technical blocker uncovered during codebase inspection.

In `src/native/dataview/tasks/task.rs` (which mirrors the official Obsidian Tasks plugin's parser logic):
```rust
fn try_take_dataview_field(state: &mut String, details: &mut TaskDetails) -> bool {
    let Some((start, field)) = trailing_inline_field(state) else { return false; };
    let Some((key, value)) = field.split_once("::") else { return false; };
    let recognized = match key {
        "priority" | "start" | "created" | "scheduled" | "due" | 
        "completion" | "cancelled" | "repeat" | "onCompletion" | 
        "id" | "dependsOn" => true,
        _ => false,
    };
    if recognized {
        *state = state[..start].trim().to_string();
    }
    recognized
}
```
Obsidian Tasks reads trailing inline fields **strictly from right to left** and **aborts immediately** upon encountering the first unrecognized field.

As documented in `~/.config/bob/config.yml`:
> *"Tasks-format parsers read trailing inline fields right to left and stop at the first one they do not recognize, so an invented value... would also hide every `[scheduled:: ]`, `[id:: ]`, and `[dependsOn:: ]` field to its left from Obsidian Tasks, `bob query`, and the dash."*

If a tool appends `[fresh:: 2026-09-30]` to the end of a task line:
```markdown
- [ ] #task Deploy update [scheduled:: 2026-10-05] [fresh:: 2026-09-30]
```
1. The Tasks parser reads `[fresh:: 2026-09-30]`.
2. It checks its whitelist. `fresh` is not recognized!
3. It aborts the loop!
4. `[scheduled:: 2026-10-05]` is **never parsed as a scheduled date**. It remains part of the task's text description.
5. As a result, the task is **not recognized as scheduled for the future** and immediately appears in `READY` as an unblocked task!

**Crucial Technical Constraint:** The freshness property **cannot** simply be appended at the end of the line. It must either:
- Be placed **immediately after the task description and before all Tasks metadata fields**, or
- Be integrated into the native Tasks grammar if we fork/patch it (which we cannot easily do for Obsidian's closed community plugin bundle).

---

## 4. Requirement Adjustments

Based on the critique and codebase realities, the following adjustments to your initial requirements are recommended:

| Initial Requirement | Recommended Adjustment | Rationale |
|---|---|---|
| **R1: Inbox tasks treated as unfresh tasks in the general review queue** | **Decouple into Tier 1 (Inbox) and Tier 2 (Backlog Freshness)** | Inbox items must never be buried under 25 project backlog tasks or truncated by a daily review cap. |
| **R2: Default 7-day freshness interval for all ready tasks** | **Increase default to 14 days for project tasks; 7 days for Areas; 3 days for Inbox** | A 7-day interval across 186 tasks forces ~27 tasks/day. A 14-day default halves the daily load to ~13 tasks/day, making daily review sustainable. |
| **R3: Field placement unspecified (implicit trailing field)** | **Strict Field Ordering: place `[fresh:: ...]` before trailing Tasks signifiers** | Prevents breaking Obsidian Tasks' right-to-left field parser. |
| **R4: Pacing as an optional fallback ("if it becomes a problem")** | **Pacing designed directly into the dashboard query ($N=10$ cap for Tier 2)** | Prevents review overwhelm from day one while keeping Tier 1 (Inbox) completely uncapped. |
| **R5: Cold-start unspecified** | **Cold-start seed / staggered initialization** | Prevents Day 1 from confronting you with 186 out-of-date tasks all at once. |

---

## 5. Architectural Specification & Design

### 5.1 The Two-Tier Morning Review Surface

We update `~/bob/dash.md` to cleanly separate the two tiers.

```
┌─────────────────────────────────────────────────────────────────┐
│ DASHBOARD: TASK CHIPS                                           │
│ [TODAY: 3] [PENDING: 6] [NEXT: 12] [INBOX: 2] [FRESH: 8/14]... │
└─────────────────────────────────────────────────────────────────┘
                               │
       ┌───────────────────────┴───────────────────────┐
       ▼                                               ▼
┌──────────────────────────────┐     ┌───────────────────────────────────┐
│ TIER 1: INBOX TASKS (≤ 1 min)│     │ TIER 2: FRESHNESS REVIEW (≤ 3 min)│
│ - Uncapped, top of dash      │     │ - Paced: Max 10 tasks/day         │
│ - gkeep_inbox.md & captures  │     │ - Projects & Areas past freshness │
│ - Actions: Link, Defer, File │     │ - Actions: Refresh (Alt+F), Alt+N │
└──────────────────────────────┘     └───────────────────────────────────┘
```

#### Tier 1: Dedicated `INBOX Tasks` Block
Placed immediately after `TODAY Tasks` or before `PENDING Tasks`:
```tasks
### INBOX Tasks
not done
path includes gkeep_inbox
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true
sort by created reverse
```
*Why this works:*
- Every Keep note pulled by `bob gkeep pull` appears here instantly.
- It contains only 1 to 5 items on any given morning.
- In 30 seconds, you glance at it, see "Pick up daughter", and either link it to today with `Alt+N` / `Ctrl+Shift+Enter` or file it to a project with `Ctrl+Shift+M`.
- **Zero chance of dropping urgent yesterday captures.**

#### Tier 2: `FRESHNESS REVIEW Tasks` Block
Replaces the old 186-task `READY Tasks` section:
```tasks
### FRESHNESS REVIEW Tasks
status.type is TODO
path does not include gkeep_inbox
filter by function globalThis.app?.plugins?.plugins?.["bob-ledger-tools"]?.api?.isToday?.(task) !== true
filter by function {
  const desc = task.description;
  const match = desc.match(/\[fresh::\s*(\d{4}-\d{2}-\d{2})\]/);
  const freshDate = match ? moment(match[1], "YYYY-MM-DD") : null;
  
  // Interval inheritance: Task override -> Project frontmatter -> Default (14d)
  const taskOverride = desc.match(/\[fresh_interval::\s*(\d+)d?\]/);
  let interval = taskOverride ? parseInt(taskOverride[1], 10) : null;
  if (interval === null) {
    const projProp = task.file.property("refresh_interval");
    interval = (typeof projProp === "number") ? projProp : 14;
  }
  
  if (!freshDate) return true; // never refreshed = out of date
  return moment().diff(freshDate, "days") >= interval;
}
sort by function {
  const match = task.description.match(/\[fresh::\s*(\d{4}-\d{2}-\d{2})\]/);
  return match ? match[1] : "1970-01-01";
}
limit 10
```
*Why this works:*
- It only shows tasks whose freshness deadline has expired.
- It caps the display at 10 tasks per morning.
- It sorts the oldest refreshed (or never refreshed) tasks to the top.
- Once you refresh or act on those 10 tasks, your review for the day is **complete**.

---

### 5.2 Task Syntax & Field Ordering

To guarantee compatibility with Obsidian Tasks, Dataview, and `bob-cli`'s native parser, we define the exact field placement:

```markdown
- [ ] #task <description> [fresh:: YYYY-MM-DD] [priority:: high] [created:: YYYY-MM-DD] [scheduled:: YYYY-MM-DD] ^block-id
```

#### Parsing Rules:
1. `[fresh:: YYYY-MM-DD]` is placed **immediately after the description text**, preceding any Tasks metadata (`priority`, `created`, `scheduled`, `due`, `dependsOn`, `id`).
2. When Obsidian Tasks parses right-to-left:
   - `^block-id` is stripped.
   - `[scheduled:: ...]`, `[created:: ...]`, `[priority:: ...]` are matched and stripped.
   - It hits `[fresh:: ...]`. It does not recognize `fresh`, so it stops.
   - Result: All standard Tasks fields are successfully parsed! `[fresh:: ...]` cleanly resides inside `task.description`.
3. Dataview parses the whole line regex-wise, so Dataview queries can access `task.fresh` directly.
4. Optional task-level interval override: `[fresh_interval:: 21d]`, placed adjacent to `fresh`:
   `- [ ] #task Audit logs [fresh:: 2026-09-30] [fresh_interval:: 30d] [created:: 2026-09-01]`

#### Project Note Frontmatter:
In project or area notes (e.g. `sase.md` or `finances.md`):
```yaml
---
parent: "[[gtd]]"
type: "[[project]]"
refresh_interval: 21
---
```
If omitted, defaults to:
- Projects (`type: "[[project]]"`): 14 days
- Areas (`type: "[[area]]"`): 7 days
- General backlog: 14 days

---

### 5.3 Obsidian Plugins Implementation (`bob-plugins`)

All Obsidian interactive behaviors live in the `bob-plugins` repository (specifically `plugins/bob-navigation-hotkeys` and `plugins/task-status-cycler`).

#### 1. Command: `refresh-task` (Hotkey: `Alt+F`)
Registered in `bob-navigation-hotkeys/main.js`:
- Target: Active markdown line under the editor cursor.
- Behavior:
  - If cursor is on a `#task` line:
    - If `[fresh:: YYYY-MM-DD]` exists on the line, update the date to today's date (`window.moment().format("YYYY-MM-DD")`).
    - If `[fresh:: ...]` does not exist:
      - Locate the boundary between the task description and the first trailing Tasks field (e.g. `[created::`, `[priority::`, `[scheduled::`).
      - Insert ` [fresh:: <today>]` at that exact boundary.
    - If count repeat (e.g. `3 Alt+F` via Vim count) is active: batch refresh the next $N$ tasks downward.
  - Notice feedback: Shows a subtle notice `Refreshed task freshness`.

#### 2. Commands: `jump-to-next-unfresh-task` / `jump-to-prev-unfresh-task`
Registered in `bob-navigation-hotkeys/main.js` (suggested hotkeys: `Alt+Shift+J` / `Alt+Shift+K`):
- Reads the current editor's note content and frontmatter (`refresh_interval`).
- Evaluates lines matching `isObsidianTaskAtLine`.
- For each open task, checks whether `isStale(task, noteInterval)` is true.
- Sets editor cursor to the next (or previous) matching task line and centers the view (Vim `zz` style).

#### 3. Automatic Freshness Updates on Supported Operations
We hook into the existing task-modifying actions:
- **`toggleTaskLane` (`Alt+N` in `bob-navigation-hotkeys`):**
  - When committing a task (`[ ]` → `[*]`) or releasing a task (`[*]`/`[/]` → `[ ]`), update `[fresh:: <today>]`.
- **`setBulletProperty` (`Ctrl+Shift+P` in `bob-navigation-hotkeys`):**
  - When updating `priority`, `scheduled`, or `dependsOn`, touch/update `[fresh:: <today>]`.
- **`cycle-task-status` (`Ctrl+Shift+]` in `task-status-cycler`):**
  - When converting a plain bullet to a task or cycling status, touch/update `[fresh:: <today>]`.
- **Blocked status transitions (`Alt+[` / `Alt+]` in `task-status-cycler`):**
  - When a task transitions from Blocked `[?]` to Ready `[ ]`, automatically stamp `[fresh:: <today>]`.

---

### 5.4 Dashboard Widget (`dash.md`) Integration

In `dash.md`, the DataviewJS widget at the top renders navigation chips:
`[TODAY] [PENDING] [NEXT] [READY] [BLOCKED] [PLAN]`

We enhance this widget:
1. Add an `INBOX` chip:
   - Value: count of open tasks in `gkeep_inbox.md`.
   - Accent color: purple / amber.
   - If count > 0, shows a visible dot or warning border so you immediately see that captured items await triage.
2. Replace or augment `READY` with a `FRESH` chip:
   - Computes:
     - `stale_count`: count of ready tasks past their refresh interval.
     - `refreshed_today_count`: count of ready tasks where `fresh === today`.
   - Display: `FRESH: 8 stale (4 refreshed)` or `FRESH: 8 / 14d`.
   - Target: Clicking jumps directly to `#FRESHNESS REVIEW Tasks`.

---

### 5.5 CLI & Engine Integration (`bob-cli`)

Although manual reviews happen inside Obsidian, `bob-cli` interacts with tasks via `bob query`, `bob plan`, and `bob task-status-hooks`.

1. **`src/native/dataview/tasks/task.rs`:**
   Add `"fresh"` and `"fresh_interval"` to `try_take_dataview_field` as recognized non-date attributes so headless `bob query` parses tasks without treating `[fresh:: ...]` as stray text.
2. **`bob freshness` CLI subcommand (optional diagnostic):**
   ```bash
   bob freshness status
   ```
   Outputs:
   ```
   Vault Freshness Summary:
     Total Ready Tasks: 186
     Fresh: 142
     Out of Date (Stale): 44
     Refreshed Today: 7
     Default Interval: 14 days
   Oldest Unrefreshed Tasks:
     - sase.md:42 "Implement renames..." (last fresh: never, created 2026-06-15)
     - sase_remote.md:18 "Add full support for machines..." (last fresh: 2026-09-02)
   ```

---

## 6. SASE Memory & Glossary Update

To fulfill the requirement to add this concept to the glossary memory web:

### Proposed Strand: `sase/memory/glossary/task_freshness.md`
```markdown
---
term: task freshness
aliases:
  - freshness
  - fresh
  - task refresh
---

# task freshness

The property of an open ready `#task` indicating when a human being last reviewed
and affirmed it.

A task is **fresh** if the duration since its last review date (`[fresh:: YYYY-MM-DD]`)
is strictly less than its configured refresh interval (default: 14 days for projects,
7 days for areas, overridable by `refresh_interval` frontmatter or `[fresh_interval:: Nd]`).
A task past due for review is **stale** (or out-of-date) and surfaces in the morning
freshness review queue. Newly captured tasks without a freshness date are stale by default.

Making any intentional modification to a task via supported hotkeys (`Alt+N`, `Ctrl+Shift+P`,
`Ctrl+Shift+]`, unblocking) or invoking the `refresh-task` keymap (`Alt+F`) updates the
freshness date to today.
```

---

## 7. Rollout Plan & Day 1 Cold-Start Mitigation

### The Day 1 Trap
If you deploy this tomorrow without a migration plan:
- All 186 ready tasks in your vault currently have **no `fresh` property**.
- All 186 tasks will instantly qualify as "out of date".
- Even with a daily cap of 10, you would face 19 straight days of maximum review queue backlog.

### Staggered Rollout Strategy
1. **Day 0: Deploy Tier 1 (Inbox Separation):**
   Add the `### INBOX Tasks` block to `dash.md` immediately. This instantly solves the Keep capture / speed-walking problem with zero risk and zero script churn.
2. **Day 1: Cold-Start Seeding Script:**
   Run a one-time script (`bob freshness seed` or a short python/rust script) across existing project tasks:
   - For existing tasks with a `[created:: YYYY-MM-DD]` date within the last 14 days: set `[fresh:: <created_date>]`.
   - For tasks older than 14 days: stagger their initial freshness dates evenly over the last 14 days based on a hash of their line content.
   - Result: Instead of 186 expired tasks on Day 1, you get a clean, balanced distribution of **~10 to 12 expired tasks per day**.
3. **Day 2: Deploy Plugin & Keymaps:**
   Update `bob-navigation-hotkeys` with `Alt+F` and auto-touch hooks; update `dash.md` with the `FRESH` chip and `FRESHNESS REVIEW` query.
4. **Day 3–14: Two-Week Trial:**
   Measure morning review duration:
   - Tier 1 (Inbox) should take $\le 1$ minute.
   - Tier 2 (Freshness) should take $\le 3$ minutes (reviewing $\le 10$ tasks).
   - Total morning review stays comfortably within your **$\le 5$ minute** budget.

---

## 8. Summary of Recommendations for Bryan

1. **Do not combine yesterday's Keep captures with 7-day backlog reviews.** Separate them visually and procedurally on `dash.md`:
   - Keep notes go into a dedicated, uncapped **INBOX** section at the top of the dash.
   - Project tasks go into a capped, rolling **FRESHNESS REVIEW** section.
2. **Adopt `14 days` as the default project refresh interval**, not 7 days. 7 days produces ~27 tasks/day (too many). 14 days produces ~13 tasks/day (manageable).
3. **Place `[fresh:: YYYY-MM-DD]` before trailing Tasks fields** to prevent breaking Obsidian Tasks' right-to-left whitelist parser.
4. **Cap the daily freshness review at $N=10$ tasks.** This guarantees your morning routine never spirals into fatigue.
5. **Stagger-seed existing tasks on Day 1** to avoid a 186-task avalanche.
