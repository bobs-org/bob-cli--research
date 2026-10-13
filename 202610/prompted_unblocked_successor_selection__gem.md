# Interactive Prompting for Unblocked Successor Tasks on Completion

**Author:** Researcher gem (Swarm 11)  
**Date:** 2026-10-13  
**Status:** Completed Research & Architecture Proposal  
**Topic:** Successor Task Link Prompting, Multi-Surface UX, Project Member Inclusion, and Breaker Removal

---

## 1. Executive Summary

This research investigates the proposal to replace the automatic insertion of successor task links into the Pomodoro ledger upon task completion with an interactive user prompt. We analyze the root cause of the current behavior regarding project tasks, evaluate the UX requirements across all three user surfaces (Obsidian, Bob Mac Capture, and CLI), critique the proposal's ergonomics against core GTD workflows, and present a concrete architecture and implementation plan.

### Key Findings & Answers:
1. **Root Cause Analysis (Why `sase_foo.md`'s tasks were not pulled in):**  
   Closing `^bar` in `sase.md` did not pull in tasks from `sase_foo.md` because `bob-cli`'s project close rule (PDC2 in `docs/task-dependencies.md` §13.16 and `src/native/task_complete/project_close.rs`) explicitly classifies project residents as **recover-only, never successor-linked** (`VerdictKind::Recover("project_member")`). By deliberate design, unblocking a project's `^prj` line recovers eligible residents from Blocked `[?]` to Ready `[ ]` (and stamps `[unblocked:: today]`), but strictly prevents automatic insertion of those tasks into the daily Pomodoro ledger to prevent flooding.
2. **Critique of Prompting (Is this a good idea?):**  
   Prompting is a **double-edged sword**. It provides welcome intentionality and prevents ledger pollution for complex milestones and project completions. However, **unconditional blocking prompts will severely degrade flow and velocity** during rapid workflows—most notably the **GTD Morning Review (`]s` walk)** and quick sequential task completion.  
   **Verdict:** Proceed with prompting, but with **critical guardrails and context carve-outs**:
   - **GTD Review Walk Carve-out:** Never show a modal during the morning review walk; tasks recover to Ready/Tickler silently or via a lightweight toast.
   - **Smart Defaults:** If only 1 task is unblocked, provide a frictionless single-action path (or pre-select it); if multiple tasks are unblocked, require explicit selection.
   - **Escape/Skip Velocity:** Pressing `Esc` or `Enter` on an empty selection must immediately complete the task without adding links (0-friction dismissal).
3. **Bob Mac Capture Needs a Custom Solution:**  
   **Verified.** Bob Mac Capture is a stateless AppKit popover and a strict thin client (`decisions:mac-capture-is-a-thin-client`). A blocking modal sheet after submission breaks the capture experience. Instead, Mac Capture should leverage its existing **live preview card** (`bob capture --dry-run`), allowing inline toggling of successor candidates before submission, or provide a lightweight confirmation popover.
4. **5-Successor Breaker Removal:**  
   The `MAX_SUCCESSORS_PER_GESTURE = 5` limit was a mechanical safety valve against runaway automation. With explicit user selection, this hard ceiling can and should be removed. However, to maintain ledger sanity, the UI should provide a soft warning when more than 5 tasks are selected for a single Pomodoro.
5. **Project Pull-In Alignment (§12.10):**  
   When closing the last task of a project note empties the project, the candidate `^prj` task (or parent `^prj`) should be presented in the same selection panel, unifying dependency successors and project completion pull-ins under one mental model.

---

## 2. Current Architecture & Behavioral Trace

To understand how the new design should function, we must first trace the existing pipeline across `bob-cli`, `bob-plugins`, and `bob-mac-capture`.

### 2.1 The Successor Link Pipeline Today

Successor task linking is governed by `docs/task-dependencies.md` §12. It is implemented in two mirroring engines:
- **Rust Native Capture Engine:** `src/native/task_complete/successors.rs`, `project_close.rs`, and `project_pull_in.rs`.
- **JavaScript Obsidian Engine:** `plugins/task-status-cycler/src/085-successor-plan.js`, `src/135-plugin-successors.js`, and `src/137-plugin-successor-project.js`.

When a task or pomodoro completion gesture occurs (via `bob capture`, Obsidian checkbox/hotkey, or `completeTaskAtCursor`):
1. **Predecessor Identification ($C$):** Collects all tasks moved from Open $\to$ Done.
2. **Identity Gate:** Checks if any completed task in $C$ carries an `[id::]` field. If none do (approx. 96% of tasks), the dependents lookup is skipped entirely for zero I/O overhead.
3. **Candidate Discovery:** Scans open tasks outside `done/` whose `[dependsOn::]` contains an ID matching a completed task in $C$.
4. **Classification & Verdicts:**
   - **`waits_on`:** Dependent still has remaining open prerequisites $\to$ stays `[?]` (`still_blocked`).
   - **`scheduled`:** Dependent has a future scheduled date $\to$ stays `[?]` (`still_blocked`).
   - **`project`:** Dependent lives in a project whose `^prj` is still blocked $\to$ stays `[?]` (`still_blocked`, PDC1/PDC4).
   - **`project_task`:** Dependent is a `^prj` task $\to$ recovers to Ready (`not_linked: "project_task"`).
   - **`hidden`:** Dependent carries `#hide` $\to$ recovers to Ready (`not_linked: "hidden"`).
   - **`already_planned`:** Dependent already has a Task Link in today's day file $\to$ recovers to Next (`not_linked: "already_planned"`).
   - **`not_planned_today`:** The completed predecessor was not planned under today's Pomodoros $\to$ recovers to Ready (`not_linked: "not_planned_today"`).
   - **`disabled`:** `plan.link_unblocked: false` $\to$ recovers to Ready (`not_linked: "disabled"`).
   - **`SUCCESSOR`:** All checks pass $\to$ eligible to be linked!
5. **The Breaker (`MAX_SUCCESSORS_PER_GESTURE = 5`):**
   If `linkable_successors > 5`, the circuit breaker trips. **Zero** successors are linked; all are demoted to `Recover("breaker")`.
6. **Execution & Writes:**
   - Note bodies: Status updated (`[?]`/`[ ]` $\to$ `[*]`), missing block IDs minted (`^<id>`).
   - Day file: Task Link bullets (`- [[note#^id]]`) inserted into the closing continuation or anchor slot.
   - Reporting: Generates notice card (`api.notice.showUnblocked`) or CLI JSON/human rows.

### 2.2 Why Closing `^bar` in `sase.md` Did Not Pull In `sase_foo.md`'s Tasks

The user observed:
> *"just tried this by closing the ^bar task in the ~/bob/sase.md file and it did not pull in the (non-project) tasks contained in the ~/bob/sase_foo.md project note as successors as I expected."*

Here is the exact code path and architectural rationale:

1. **The Scenario:**
   - `sase.md` has `- [ ] #task Bar [id:: bar] ^bar`.
   - `sase_foo.md` is a project note (`type: [[project]]`).
   - In `sase_foo.md`, the project task is `- [?] #task Foo Outcome [dependsOn:: bar] [id:: foo] ^prj`.
   - In `sase_foo.md`, resident tasks exist, e.g. `- [?] #task Step 1 [id:: step-1] ^step-1`.
2. **What Happened on Close:**
   - `^bar` was closed.
   - The candidate matching identified `sase_foo.md`'s `^prj` task as dependent on `bar`.
   - `^prj` had no remaining prerequisites.
   - However, in `src/native/task_complete/successors.rs` (lines 711–727):
     ```rust
     } else if task.block_id.as_deref().is_some_and(|id| is_project_task_id(Some(id))) {
         if has_prj_is_blocked_tag(&raw_task_line(&file.contents, task.line_index)) {
             VerdictKind::StillBlockedProject
         } else {
             VerdictKind::Recover("project_task")
         }
     }
     ```
     Because the block ID is `prj`, its verdict was **`Recover("project_task")`**, NOT `VerdictKind::Successor`!
   - Next, `recover_project_members` executed (`src/native/task_complete/project_close.rs:217–292`):
     ```rust
     verdicts.push(super::successors::DependentVerdict {
         file: file_index,
         task: task_index,
         preds: preds.clone(),
         anchor: None,
         kind: VerdictKind::Recover("project_member"),
         open_count,
         pull_in: false,
     });
     ```
     Every resident task in `sase_foo.md` whose own dependencies were satisfied received **`VerdictKind::Recover("project_member")`**.
   - In `successors.rs:777–786`, `successor_positions` filters strictly for `verdict.kind == VerdictKind::Successor`.
   - Neither `^prj` nor any resident was a `Successor`. Therefore:
     - **Zero task links were inserted into the day file.**
     - In `sase_foo.md`, `#prj_is_blocked` was stripped, and each resident recovered from `[?]` to `[ ]` (Ready), stamped with `[unblocked:: <today>]`.
3. **The Architectural Rationale:**
   This was not a bug; it was the intended design codified in SASE decisions:
   - **`decisions:unblocked-tasks-resurface-as-ticklers`**:
     > *"Residents recover-only, never successor-linked... Recover-only, never-linked project members kept their old `[fresh::]` and could sit FRESH, outside the walk, for up to six mornings... `[unblocked:: today]` surfaces them as TICKLER in tomorrow's morning review."*
   - **`decisions:projects-block-from-prj-line`**:
     > *"Residents recover-only (never successor-linked)... Reopens when: Bryan wants a sub-project cascade or re-linking on unblock."*
   - **Why it was designed this way:** In an automated system without user confirmation, unblocking a project with 15 open tasks could not reasonably dump all 15 tasks into today's Pomodoro ledger. It would exceed daily capacities and overwhelm the day plan.

**Key Insight:** Transitioning from *automated linking* to *interactive user selection* fundamentally changes this constraint. Because the user will explicitly select which tasks to pull in, we no longer need to fear ledger flooding. Presenting unblocked project residents in the selection panel is not only safe—it is highly desirable.

---

## 3. Critical Evaluation & Critique of the Plan

Before jumping into implementation details, we must rigorously critique the proposal: **Is prompting the user on task completion a good idea?**

```
+---------------------------------------------------------------------------------+
|                       COMPLETION WORKFLOW TRADEOFF                              |
+---------------------------------------------------------------------------------+
|                                                                                 |
|  AUTOMATIC LINKING (Status Quo)               INTERACTIVE PROMPTING (Proposed)  |
|  ------------------------------               --------------------------------  |
|  + Zero cognitive interruption                + Absolute ledger control         |
|  + Fast, fluid GTD walk                       + Zero unwanted task injections   |
|  - Injects unexpected tasks into ledger       - Modal interrupts flow           |
|  - Hard breaker (links 0 if >5)               - Prompt fatigue on frequent closes|
|  - Blocks project resident linking            - Complex headless/CLI handling   |
|                                                                                 |
+---------------------------------------------------------------------------------+
```

### 3.1 The Arguments in Favor
1. **Preserves the Sanctity of the Pomodoro Ledger:**  
   Today's Pomodoros represent Bryan's focused commitments. Automatic injection of unexpected tasks often forces manual cleanup (e.g., deleting lines, running `Alt+N` releases). Explicit selection ensures that only tasks Bryan actively intends to tackle *today* enter the ledger.
2. **Unlocks Project Member Pull-Ins:**  
   As seen in the `sase_foo.md` example, automatic linking was forced to treat project members as recover-only because it couldn't guess which task Bryan wanted next. Prompting solves this: Bryan can choose the 1 or 2 project tasks he wants to start immediately.
3. **Replaces the Arbitrary 5-Task Breaker:**  
   The current rule (if 6 tasks unblock, link 0 of them) was an awkward compromise. With user selection, Bryan can pick 1, 3, or all 6 if he genuinely plans to batch-process them.

### 3.2 The Risks & Pitfalls (The Critique)
1. **Prompt Fatigue & Flow Interruption:**  
   Task completion is a high-frequency psychological "checkpoint." Adding a modal dialog after checking off a task introduces cognitive friction. If Bryan completes 5 subtasks in 20 minutes, encountering a modal dialog on tasks that have dependents will feel disruptive unless the modal is lightning-fast and easily bypassed.
2. **Destruction of the GTD Morning Review (`]s` Walk):**  
   In the morning review walk, Bryan moves through tasks sequentially (`]s` / `[s`). Pressing `Ctrl+Enter` completes an item and auto-advances the walk (`decisions:answering-advances-the-walk`). If completing an item pops open an interactive selection modal, **it halts the review walk in its tracks**. During morning review, Bryan is clearing decks, not choosing active Pomodoro work.
3. **The Single-Successor Disappointment:**  
   In 80% of linear task dependency chains, Task B follows Task A (1-to-1). Automatically pulling in Task B was frictionless and delightful. Requiring an extra dialog to confirm the obvious single successor adds unnecessary keystrokes.
4. **Headless & Automation Breakage:**  
   If CLI commands (`bob capture "!sase:bar"`, git commit hooks, or automated scripts) assume interactive prompts, they will hang or fail in non-TTY environments.

### 3.3 Recommended Adjustments to the Plan
To capture the benefits of user selection while eliminating prompt fatigue, we recommend the following adjustments:

| Requirement / Scenario | Initial User Idea | Recommended Adjusted Specification | Rationale |
| :--- | :--- | :--- | :--- |
| **Morning Review Walk (`]s`)** | Prompt user | **Never prompt.** Recover to Ready/Tickler automatically. | Preserves review walk velocity (`answering-advances-the-walk`). |
| **Single Unblocked Successor** | Prompt user in panel | **Pre-select candidate by default.** (Press `Enter` to link, `Esc` to skip). | Single keypress to accept; zero typing required. |
| **Project Member Candidates** | Include all open tasks | **Include only unblocked open residents.** | Residents with unsatisfied internal dependencies or future dates remain blocked. |
| **Empty Selection (`Esc` / `Enter`)** | Unclear | **Instant zero-link completion.** Tasks still recover to Ready with `[unblocked:: today]`. | Zero friction to decline linking. |
| **Non-Interactive CLI** | Unclear | **Default to recover-only (no link), unless `--successors` flag is passed.** | Never hangs in scripts, CI, or agent turns. |
| **5-Successor Breaker** | Remove limit | **Remove hard limit; add soft visual indicator if >5 selected.** | Protects against accidental mass-linking while honoring user choice. |

---

## 4. Multi-Surface UX Architecture

A major challenge is ensuring the UX feels native and seamless across **Obsidian**, **Bob Mac Capture**, and the **Terminal CLI**.

```
+----------------------------------------------------------------------------------------------------+
|                                    MULTI-SURFACE UX MATRIX                                         |
+-----------------------------------+--------------------------------+-------------------------------+
| Surface                           | Primary Interaction Point      | Prompt Mechanism              |
+-----------------------------------+--------------------------------+-------------------------------+
| Obsidian (Desktop)                | Note Editor / Checklist / Walk | SuccessorPickerModal (AppKit- |
|                                   |                                | style FilteredPickerModal)    |
|                                   |                                |                               |
| Bob Mac Capture (macOS Menu Bar)  | Menubar Input Popover          | In-Preview Selection Cards    |
|                                   |                                | (or Modal Confirmation Sheet) |
|                                   |                                |                               |
| Terminal CLI (`bob capture`)      | Bash Shell / Terminal TTY      | Interactive TTY Multiselect   |
|                                   |                                | (Headless: Flags / Recover)   |
+-----------------------------------+--------------------------------+-------------------------------+
```

### 4.1 Obsidian UX (`bob-plugins`)

In Obsidian, task completion happens via `task-status-cycler` (`finalizeClosedTasks`), `bob-navigation-hotkeys` (`completeTaskAtCursor`), and `bob-ledger-tools`.

#### Proposed Component: `SuccessorPickerModal`
The modal should extend `FilteredPickerModal` (already heavily optimized in `bob-navigation-hotkeys/src/200-filtered-picker-modals.js` and used for Task Cards and link pickers).

**Visual Layout:**
```text
┌────────────────────────────────────────────────────────────────────────┐
│ 🔓 Pull In Unblocked Successors                     ✓ Fix apollo machine│
│ Filter unblocked tasks...                                              │
├────────────────────────────────────────────────────────────────────────┤
│ Direct Successors:                                                     │
│   [x] Re-launch failed agents on apollo!               sase.md  [ Next ]│
│                                                                        │
│ Unblocked Project Tasks (sase_foo.md):                                 │
│   [ ] Update agent configurations                      foo.md   [ Ready ]│
│   [ ] Verify test suite on apollo                      foo.md   [ Ready ]│
│                                                                        │
│ Destination: FIX (next up in today's Pomodoro)                         │
├────────────────────────────────────────────────────────────────────────┤
│ [Enter] Link Selected (1)    [Space] Toggle    [Esc] Skip (Recover Only) │
│ [A] Toggle All               [↑/↓] Navigate                              │
└────────────────────────────────────────────────────────────────────────┘
```

**Key Ergonomic Behaviors:**
1. **Grouping:**
   - **Direct Successors:** Tasks that directly depend on the completed task.
   - **Project Residents:** Tasks in project notes whose `^prj` line was unblocked.
   - **Emptied Projects (§12.10):** The `^prj` line of a project that was just emptied.
2. **Keyboard Mapping:**
   - `↑` / `↓`: Move selection highlight.
   - `Space`: Toggle checkbox for highlighted task.
   - `Enter`: Commit. Links all checked tasks to the Pomodoro continuation/slot; unselected tasks recover to Ready.
   - `Esc`: Dismiss immediately. Links **nothing**; all unblocked tasks recover to Ready with `[unblocked:: today]`.
   - `A`: Toggle all on/off.
3. **Carve-out Detection:**
   If the completion gesture originated from `completeTaskAtCursor` while in GTD Review Walk mode, `SuccessorPickerModal` is suppressed. The tasks recover silently, and the walk advances without interruption.

---

### 4.2 Bob Mac Capture UX (`bob-mac-capture`)

The user prompt noted:
> *(we'll probably need a custom / separate solution for the bob-mac-capture app, but you should verify this is needed).*

**Verification: A separate solution is 100% required.**

#### Why Mac Capture Cannot Use the Obsidian Approach:
1. **Thin Client Boundary (`decisions:mac-capture-is-a-thin-client`):**  
   Bob Mac Capture never touches Markdown files directly. It is a Swift AppKit frontend that communicates with `bob` exclusively via CLI commands (`capture-parse`, `capture-complete`, and `capture --dry-run`).
2. **Presentation Paradigm:**  
   In Mac Capture, the user types a command (e.g., `=x` or `!sase:bar`). The app displays a **live preview card** below the text input before the user ever presses Enter.
3. **Popover Window Lifecycle:**  
   The Mac Capture window is an ephemeral menu-bar popover. Opening a secondary floating modal or sheet upon pressing Enter disrupts the quick-capture muscle memory.

#### Recommended Mac Capture Solution: **"In-Preview Selection"**

Instead of interrupting after submission, integrate the selection directly into the **Live Preview Card**:

```text
┌────────────────────────────────────────────────────────────┐
│ !sase:fix-apollo                                           │
└────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────┐
│ ✓ Complete: Fix apollo machine!                            │
│                                                            │
│ 🔓 Successors to link (click or press ⌥1, ⌥2 to toggle):   │
│   [✓] 1. Re-launch failed agents on apollo!  → FIX         │
│   [ ] 2. Update agent configurations (sase_foo)            │
│   [ ] 3. Verify test suite on apollo (sase_foo)            │
│                                                            │
│ Press ↩ to complete and link checked tasks                │
└────────────────────────────────────────────────────────────┘
```

**How It Works Architecturally:**
1. While typing, Mac Capture runs `bob capture --dry-run -f json -- !sase:fix-apollo`.
2. The JSON response returns candidate unblocked rows in `unblocked[]`, each with a unique identifier or index.
3. The Swift AppKit view renders interactive checkboxes or pills for each candidate.
4. When the user submits (presses Enter), Mac Capture passes the selected task IDs to `bob capture` via a new flag:
   ```bash
   bob capture -f json --successors "relaunch-failed-agents" -- "!sase:fix-apollo"
   ```
5. If the user does not want any successors linked, they uncheck them (or press `⌥0`), and `bob capture` runs with `--successors none`.

*Alternative Fallback:* If interactive preview checkboxes are deemed too complex for AppKit V1, Mac Capture can display an inline confirmation sheet inside the popover upon pressing Enter when multiple successors are detected. However, In-Preview Selection is vastly superior and honors the "preview first, notification second" rule (`docs/task-dependencies.md` §12.6).

---

### 4.3 Terminal CLI UX (`bob capture`)

When running from the terminal shell:
1. **Interactive TTY (`io::stdout().is_terminal()`):**
   If interactive and multiple candidates are unblocked, render an ANSI/terminal selector (e.g., using a terminal multi-select list):
   ```text
   Completed 'Fix apollo machine!'. Select successors to pull into today's Pomodoro:
   [x] 1. Re-launch failed agents on apollo! (sase.md)
   [ ] 2. Update agent configurations (sase_foo.md)
   [ ] 3. Verify test suite on apollo (sase_foo.md)
   [Enter: confirm, Esc/q: none, a: all]
   ```
2. **Headless / Non-Interactive (Pipes, Scripts, Agent Turns):**
   - **Crucial Rule:** Never block on stdin.
   - If `--successors` is omitted and stdin is not a TTY: Default to linking **none** (`--successors none`), recovering all candidates to Ready.
   - Explicit CLI options:
     - `--successors all`: Links all eligible unblocked tasks.
     - `--successors none`: Recovers all eligible tasks without linking.
     - `--successors id1,id2`: Links only specified IDs.
     - `--no-prompt`: Disables interactive prompt even in a TTY.

---

## 5. Detailed Logic: Project Unblocking & Edge Cases

### 5.1 Project Task Unblocking (`^bar` $\to$ `sase_foo.md`)

When completing task $C$ unblocks project task `^prj` of project note $N$:

#### 1. Candidate Filtering for Project Residents:
We must distinguish between **unblocked residents** and **still-blocked residents** within project $N$:
- **Eligible Candidate Resident:**
  - Status is open (`?`, ` `, `*`, `/`).
  - Has **zero remaining open prerequisites** (both external and internal to $N$).
  - Does **not** have a strictly future `[scheduled::]` date (`scheduled <= today`).
- **Ineligible (Still-Blocked) Resident:**
  - Has an internal prerequisite within $N$ that remains open (PDC3).
  - Has a future scheduled date.
  - **Action:** These tasks MUST NOT be presented as selectable successors to pull into today's Pomodoro! They may optionally be shown in a muted "Still Blocked" section of the modal for situational awareness.

#### 2. What about the `^prj` task itself?
- If project $N$ still contains open tasks, `^prj` represents the overarching project outcome/container. In Bob's GTD model, `^prj` is not an executable task until its members are complete.
- **Rule:** If $N$ has open tasks, `^prj` is **not** offered as a successor link. Only eligible resident tasks are offered.
- If $N$ has **no open tasks** (empty project), `^prj` *is* offered as a candidate (§12.10 pull-in).

```
+-----------------------------------------------------------------------------------+
|                        PROJECT UNBLOCKING SELECTION LOGIC                         |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|   Completed Task [x]                                                              |
|          |                                                                        |
|          v                                                                        |
|   Unblocks Project Task `^prj` (sase_foo.md)                                      |
|          |                                                                        |
|          +---> Does Project have Open Tasks?                                      |
|          |            |                                                           |
|          |            +--- YES ---> Present Open Residents with open_count == 0   |
|          |            |             in the Selection Panel                        |
|          |            |             (Do NOT present `^prj`)                       |
|          |            |                                                           |
|          |            +--- NO  ---> Present `^prj` as Empty Project Pull-In       |
|          |                          in the Selection Panel                        |
|          |                                                                        |
|          +---> Unselected / Declined Tasks: Recover to Ready [ ]                  |
|                Strip `#prj_is_blocked`, Write `[unblocked:: today]`               |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

### 5.2 Empty Project Pull-In (§12.10) Integration

The user requested:
> *"This change should also apply to the project tasks / parent project tasks we pull in as successors when closing the last open task / sub-project for a project."*

Currently, under §12.10:
- When a task completion empties project $N$, $N$'s `^prj` task is automatically linked as a successor link and `#hide` is removed.
- If $N$ was a subproject of parent project $P$, completing $N$'s `^prj` can empty $P$, triggering $P$'s `^prj` pull-in.

**New Behavior:**
1. Instead of automatically writing the Task Link into the day file, candidate `^prj` (or parent `^prj`) is classified with `trigger: "project_empty"` and added to the candidate list.
2. In the selection prompt, it appears clearly labeled:
   ```text
   [x] Ship the outcome!  proj.md ^prj  · project has no open tasks
   ```
3. If selected:
   - `#hide` is removed.
   - Status updated to Next (`[*]`).
   - Task Link inserted into today's Pomodoro.
4. If unselected:
   - `#hide` is removed (surfaced).
   - Status updated to Ready (`[ ]`).
   - **No Task Link is inserted into the day file.**
   - It will surface naturally in tomorrow's morning review or in the Projects dashboard.

### 5.3 Removing the 5-Successor Breaker

Currently:
```rust
pub(crate) const MAX_SUCCESSORS_PER_GESTURE: usize = 5;
```
If 6 tasks unblock, the breaker activates and links none.

**New Specification:**
1. **Remove Hard Limit:** There is no longer a cutoff where the engine refuses to link. If the user checks 7 tasks, 7 tasks are linked.
2. **Display Scaling (Modal Performance & Scroll):**
   - If a task unblocks 20 tasks (e.g. unblocking a large project), the modal must have a scrollable results area capped at a sensible height (e.g., max 8 visible rows with scrollbar).
   - A search/filter input at the top allows instant fuzzy filtering.
3. **Safety / Guardrail Warnings:**
   - If the user selects $\ge 5$ tasks, display a subtle warning pill in the modal footer:
     `⚠️ 5 tasks selected for this Pomodoro session`
   - If `> 10` tasks unblock, items are **unchecked by default** to prevent accidental mass-linking on an errant `Enter`.

### 5.4 The "Not Planned Today" Nuance

Under existing §12.2 step 7:
If task $C$ was completed, but $C$ was *not planned today* (i.e., completed directly in a project note, outside today's Pomodoro ledger), its successors were assigned `not_linked: "not_planned_today"` and never linked to today's ledger.

**With Interactive Prompting:**
- If Bryan is working in a project note and checks off a task, does he want to pull its successor into today's Pomodoro?
- **Recommendation:**
  - Yes, provide the option!
  - In the modal header, clearly display the target Pomodoro:
    `Destination: FIX (running Pomodoro)` or `Destination: Next up Pomodoro`.
  - If no Pomodoro is open today, the modal gracefully indicates:
    `No active Pomodoro today — unblocked tasks will recover to Ready`. (Or prompt to start/append to today's day file).

---

## 6. Technical Implementation Blueprint

Here is the exact architectural blueprint across all repositories.

### 6.1 `bob-cli` Changes (Rust Native Core)

1. **Modify `SuccessorPlan` & Reporting Model (`src/native/task_complete/successors.rs`):**
   - Remove `MAX_SUCCESSORS_PER_GESTURE` breaker enforcement when in prompt/explicit mode.
   - Add candidate metadata to `UnblockedRow` or a new top-level `candidates` field in the capture JSON schema:
     ```json
     "candidates": [
       {
         "note_path": "sase.md",
         "block_id": "relaunch-failed-agents",
         "text": "Re-launch all failed agents on apollo!",
         "trigger": "dependency",
         "is_project_member": false,
         "default_selected": true
       },
       {
         "note_path": "sase_foo.md",
         "block_id": "step-1",
         "text": "Update agent configurations",
         "trigger": "project_member",
         "is_project_member": true,
         "default_selected": false
       }
     ]
     ```
2. **Update `project_close.rs` (`recovering_prj_verdict` / `recover_project_members`):**
   - When a `^prj` task recovers, collect all eligible open resident tasks.
   - Instead of marking them strictly `VerdictKind::Recover("project_member")` without an anchor, mark them as **linkable candidates** (`VerdictKind::CandidateProjectMember`).
   - If explicitly selected via `--successors`, upgrade them to `VerdictKind::Successor` so block IDs are minted and day file links are placed.
3. **Add CLI Option to `bob capture`:**
   ```bash
   bob capture [--dry-run] [--successors <id1,id2|all|none>] <expression>
   ```
   - In dry-run mode, returns all unblocked candidates.
   - In real execution, links only the subset passed in `--successors`.
   - In non-interactive mode with `--successors` omitted: defaults to `none` (recover only).

### 6.2 `bob-plugins` Changes (Obsidian JS)

1. **`plugins/task-status-cycler/src/085-successor-plan.js`:**
   - Remove `const SUCCESSOR_BREAKER_LIMIT = 5;`.
   - Update candidate collection to include unblocked project members as selectable candidates.
   - Support a `selectedIdentities: Set<string>` input to `planSuccessors`. Only items in this set produce placements in the day file; the rest produce recover edits only.
2. **`plugins/bob-navigation-hotkeys/src/` (New Component: `SuccessorPickerModal`):**
   - Create `SuccessorPickerModal extends FilteredPickerModal`.
   - Mount in `plugins/task-status-cycler/src/137-plugin-successor-project.js` (`planAndApplySuccessorsNow`):
     - Before applying day file insertions:
     - If candidates exist and NOT in review walk:
     - Await `SuccessorPickerModal.openAndSelect(candidates)`.
     - Pass the selected IDs into the placement applicator.
     - If the user pressed `Esc`, apply recoveries only and return.
3. **Configuration Kill Switch:**
   In `~/.config/bob/config.yml` (and plugin settings):
   ```yaml
   plan:
     prompt_unblocked: true      # Enable modal prompting on close
     auto_link_single: false     # When true, automatically links if exactly 1 successor
   ```

### 6.3 `bob-mac-capture` Changes (Swift AppKit)

1. **Update `CaptureModel.swift`:**
   - Decode additive `candidates` array from `bob capture --dry-run` JSON.
2. **Update Preview Cards (`CapturePomodoroCloseView.swift` & `CaptureTaskCompleteView.swift`):**
   - Render selectable checkbox rows for candidate successors in the `Unblocked` section of the card.
   - Maintain a local selection state `Set<String>` in `CaptureState`.
3. **Execution Call:**
   - When submitting draft, serialize selected candidate IDs into `--successors <id1,id2>` and pass to `bob capture`.

---

## 7. Recommended Solution & Action Plan

### Recommended Architecture: "Context-Aware Prompting with Smart Defaults"

We recommend adopting the user's plan with **three essential refinements**:
1. **Never prompt during the morning GTD review walk** (recover tasks to Ready silently to preserve walk momentum).
2. **In-Preview Selection for Bob Mac Capture** rather than a secondary modal sheet, honoring the thin-client architecture.
3. **Project residents are candidates, but unchecked by default** (to prevent accidental mass-linking of an entire project backlog).

### Phased Rollout Plan

```
Phase 1: bob-cli Core Protocol & Schema
  ├── Expose candidate unblocked tasks (including eligible project members and empty ^prj) in JSON
  ├── Add `--successors <ids|all|none>` parameter to `bob capture`
  └── Remove hard `MAX_SUCCESSORS_PER_GESTURE = 5` limit when explicit successors are specified

Phase 2: Obsidian Implementation (`bob-plugins`)
  ├── Build `SuccessorPickerModal` in `bob-navigation-hotkeys`
  ├── Wire modal into `task-status-cycler`'s `finalizeClosedTasks` pass
  ├── Implement GTD Review Walk bypass
  └── Add `plan.prompt_unblocked` configuration setting

Phase 3: Bob Mac Capture Implementation (`bob-mac-capture`)
  ├── Decode candidate successors in Swift
  ├── Render interactive selection toggles in the live preview card
  └── Pass selected IDs via `--successors` on draft execution
```

---

## 8. Conclusion

The proposed change directly addresses user frustration with unwanted Pomodoro link pollution and the arbitrary 5-successor circuit breaker. By converting unblocked project residents and empty project outcomes into selectable candidates rather than strictly recover-only tasks, we unlock a major functional improvement: closing a blocking task can now seamlessly pull the first step of a project directly into today's work.

With the addition of GTD walk carve-outs and in-preview selection for Mac Capture, the system will achieve the ideal balance of **absolute ledger intentionality** without sacrificing **rapid keyboard velocity**.
