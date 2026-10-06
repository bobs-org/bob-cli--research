# GTD Morning Review: Keymap Auto-Advance Research & Architecture Plan

**Author:** Researcher `gem` (5-Researcher Swarm)  
**Date:** 2026-10-06  
**Target Repositories:** `bob-plugins` (`bob-navigation-hotkeys`, `task-status-cycler`, `block-id-prompt`, `bob-ledger-tools`), `bob-cli`  

---

## 1. Executive Summary

Bryan's GTD morning review is initiated via the `]s` Vim/Obsidian keymap (`bob-navigation-hotkeys:jump-to-next-due-task`) and proceeds sequentially through a tiered hierarchy:
$$\text{PRE} \to \text{NEW} \to \text{PROJECTS} \to \text{PENDING} \to \text{NEXT} \to \text{RETURNED} \to \text{REFERENCES} \to \text{ROTTEN} \to \text{POST}$$

Currently, the review loop suffers from an ergonomic friction point: while `Ctrl+Alt+F` ("Refresh task freshness and jump") already executes a combined **action + advance** step, most other resolution gestures—completing a task with `<ctrl+enter>`, linking it to today's Pomodoro ledger with `<ctrl+shift+enter>`, rolling or cancelling it via the Task Card (`<ctrl+shift+p>`), or releasing a lane with `Alt+N`—perform the mutation in place and leave the cursor stranded on the modified line. The user is forced into a repetitive two-step motor cadence:
$$\text{[Execute Action]} \longrightarrow \text{[Press } {]s} \text{]}$$

### Key Findings & High-Level Recommendations
1. **Verdict on Plan:** The proposal to automatically advance upon review item resolution is **an excellent, highly justified ergonomic improvement**. The morning review is primarily a triage conveyor belt; requiring an explicit `]s` after an unambiguous resolution gesture introduces unnecessary motor drag.
2. **Critical UX Safeguard ("Stay vs. Advance"):** Unlike `Ctrl+Alt+F` (which has `Alt+F` as an explicit "stamp and stay" variant), `<ctrl+enter>` and `<ctrl+shift+enter>` do not have native "stay" variants. To prevent disorientation when a user wants to edit follow-up notes on a completed task, **every auto-jump must register an entry in Vim's jump list (`vimJumpHistory`)**, allowing instant zero-friction return via `<C-o>`.
3. **Strict Landing Verification:** Auto-advance must never trigger during ordinary daytime editing. It must strictly require an active, validated `reviewLanding` matching the active file, cursor line, line text, and current date.
4. **Cross-Plugin Architecture:** Rather than having separate plugins (`task-status-cycler`, `block-id-prompt`) reinvent or duplicate queue jump logic, `bob-navigation-hotkeys` must serve as the single source of truth. It should expose a unified, versioned method:
   ```javascript
   api.advanceReviewWalkIfLanding(editor, { action, handledKey, noticePrefix })
   ```
5. **Additional Keymaps to Include:** Beyond `<ctrl+enter>`, `<ctrl+shift+enter>`, and `<ctrl+shift+p>`, we strongly recommend including **`Alt+N` (`toggle-task-lane`)** when releasing a task from Next/Pending to Ready (and when committing Ready to Next), as well as **`Ctrl+Shift+]` (`toggle-obsidian-task`)** when demoting a task to a non-task bullet. Conversely, **status cycling (`Alt+[` / `Alt+]`) should NOT auto-advance**, as cycling is an exploratory, multi-stroke operation.

---

## 2. Deep Dive: Current Review Walk Architecture

To understand how keymaps can cleanly integrate with the review walk, we must examine the runtime data structures and cross-plugin interactions.

### 2.1 The Tiered Walk Evaluator
Under Decision 8 (`review-walk-is-tiered`) and `docs/freshness.md`, the walk is evaluated across both Rust (`bob freshness list`) and JavaScript (`bob-ledger-tools` freshness API):
- **Commitment Tiers:** `PRE`, `NEW`, `PROJECTS`, `PENDING`, `NEXT`, `RETURNED`, `REFERENCES`.
- **Rotten Tier:** `ROTTEN` (tasks due for decay review under `freshness.interval`).
- **Closing Tier:** `POST` (closing checklist rows).

Crucially, **tiers are due-only**:
- A task stamped today (`[fresh:: today]`) drops out of the walk.
- Tasks that are recurring, in daily notes, hidden, dependency-blocked, future-scheduled (`scheduled > today`), or **linked to today's Pomodoro ledger** are **excluded from all tiers** (except PRE/POST checklist rows).
- A task marked completed (`[x]`) or cancelled (`[-]`) is no longer an open task and drops out of the walk.

### 2.2 Walk State Tracking in `bob-navigation-hotkeys`
`bob-navigation-hotkeys` maintains two critical pieces of state:
1. `this.reviewLanding`:
   ```javascript
   this.reviewLanding = Object.freeze({
     path,
     text: entry.originalMarkdown,
     key: reviewQueueEntryKey(entry),
     tier: reviewEntryMachineTier(entry) || null,
     day: this.laneReleaseDateText({}),
   });
   ```
   Set whenever `landOnReviewQueueEntry(plan.entry)` successfully places the cursor on a review task. It records the exact note path, line text, unique queue entry key, tier, and local calendar date.

2. `this.reviewAnchor`:
   ```javascript
   this.reviewAnchor = Object.freeze({
     keys: Object.freeze(Array.from(handled)),
     rank,
     count: handled.size,
     path: holder.path,
     line: holder.line,
     tier: reviewEntryMachineTier(holder) || null,
     day: dayText,
     afterKeys: Object.freeze(afterKeys),
     beforeKeys: Object.freeze(beforeKeys),
   });
   ```
   Because Obsidian's vault cache and the Tasks plugin metadata index update asynchronously, re-evaluating the queue immediately after an in-editor edit could erroneously re-discover the task just modified. `reviewAnchor` maintains `handledKeys` and relative successor keys (`afterKeys`). When `planReviewJump(queue, { anchor, direction: 1 })` plans the next jump, it skips all handled keys and jumps directly to the first surviving successor.

### 2.3 The Existing `<ctrl+enter>` Implementation for PRE
In `bob-navigation-hotkeys/src/535-plugin-review-checklist-walk.js` and `task-status-cycler/src/140-plugin-vim.js`, support for `<ctrl+enter>` was introduced as follows:
1. User presses `<C-Enter>` (or `<C-CR>`) in Vim normal mode.
2. `task-status-cycler`'s `handleVimTaskToggleOpenDone` intercepts the key and calls `claimReviewWalkCtrlEnter(view.editor)`.
3. This calls `bob-navigation-hotkeys`'s `api.claimReviewWalkCompletion(editor)`.
4. Hotkeys checks:
   - Does `this.reviewLanding` match the editor, file, line text, and current day?
   - Is `tier === "pre" || tier === "post"`?
5. If so, Hotkeys claims the event and executes `completeReviewChecklistRow` with `withinGroup: true`:
   - It invokes `cycler.api.completeTaskAtCursor(cm)` to toggle the task to `[x]` through Obsidian Tasks.
   - It adds the completed entry key to `handled`.
   - If another PRE row remains in `liveGroup.after`, it jumps to that successor.
   - **The Halt at Group Boundary:** When the last PRE row is completed, `liveGroup.after` is empty. Because `withinGroup: true` was set, it does **not** advance to `NEW`! Instead, it halts and renders a notice:
     ```text
     ✓ Done · PRE review complete · ]s → NEW · 12 commitments due
     ```
   - For any non-checklist tier (`NEW`, `PROJECTS`, `PENDING`, `NEXT`, `RETURNED`, `REFERENCES`, `ROTTEN`), `claimReviewWalkCtrlEnter` returns `null`. `task-status-cycler` falls back to its default handler, completing the task in place without advancing.

---

## 3. Keymap-by-Keymap Feasibility & Behavioral Analysis

### 3.1 `<ctrl+enter>`: Generalizing Task Close Across All Tiers

#### Intended Behavior
Whenever an open review item is closed (`[ ]` $\to$ `[x]`, `[/]` $\to$ `[x]`, or `[*]` $\to$ `[x]`) using `<ctrl+enter>`, the system should complete the task and immediately jump to the next due review item.

#### Technical Mechanics
1. **Remove Tier Gate:** In `bob-navigation-hotkeys/src/535-plugin-review-checklist-walk.js` (`claimReviewWalkCtrlEnter`), remove the restriction:
   ```javascript
   // Current:
   if (!entry || (tier !== "pre" && tier !== "post") || ...) return null;
   // Required:
   if (!entry || entry.path !== landing.path || entry.originalMarkdown !== landing.text) return null;
   ```
2. **Remove `withinGroup: true` Constraint:** In `claimReviewWalkCtrlEnter`, pass `withinGroup: false` (or `advanceAcrossTiers: true`). When the last item of a tier (such as PRE) is completed, `completeReviewChecklistRow` must not stall; it should execute `planReviewJump(queueBefore, { direction: 1, anchor })` and land on the first entry of the next tier (`NEW`), displaying the boundary notice:
   ```text
   ✓ Done · Habit chore
   PRE review complete · 15 commitments due
   [1/15] NEW · Projects/Alpha · Review pull request
   ```
3. **Closing vs. Reopening Guard:** In `task-status-cycler`, verify that the task status is currently an *open* status (`COMPLETE_AT_CURSOR_OPEN_SYMBOLS`: `' '`, `'/'`, `'*'`, `'?'`). If a user presses `<ctrl+enter>` on an already-completed task (`[x]`), it reopens to `[ ]`. **Reopening must NOT auto-advance**, as the item is being restored to an open state.

---

### 3.2 `<ctrl+shift+enter>`: Linking to Today's Pomodoro Ledger

#### Intended Behavior
When an open task is linked to Today's Pomodoro ledger via `<ctrl+shift+enter>` (`block-id-prompt:openPomodoroTaskLink`), it is assigned to today's active work schedule and becomes Next (`*`). Under GTD and bob-cli rules, tasks linked to today drop out of the review walk. Therefore, linking to today should immediately jump to the next review item.

#### Technical Mechanics & Challenges
1. **Decoupled Architecture:** `block-id-prompt` currently has no runtime dependency on `bob-navigation-hotkeys`. It must feature-detect `bob-navigation-hotkeys`'s API:
   ```javascript
   const navApi = this.app.plugins?.plugins?.["bob-navigation-hotkeys"]?.api;
   ```
2. **Asynchronous Transaction Pipeline:** Unlike in-memory editor toggles, `openPomodoroTaskLink` performs a multi-step operation:
   - If the task lacks a block ID, it opens `BlockIdPromptModal`. The user types or accepts a block ID.
   - It modifies the source task line (adding `#task [*]` and `^<block-id>`).
   - It modifies today's daily note (inserting the `[[note#^block-id]]` task link under the active Pomodoro section).
   - Only after both file writes succeed (`reportPomodoroLinkOutcome`) is the link complete.
3. **Trigger Point:** The auto-advance call must be placed at the very end of `applyPomodoroTaskLink`:
   ```javascript
   this.reportPomodoroLinkOutcome(plan, pomodoroPlan, isNewId);
   if (navApi && typeof navApi.advanceReviewWalkIfLanding === "function") {
     void navApi.advanceReviewWalkIfLanding(source.editor, {
       action: "today",
       handledKey: source.task.existingId,
     });
   }
   ```
4. **Linking vs. Unlinking:** Pressing `<ctrl+shift+enter>` on an already-linked task initiates an unlink (`applyPomodoroTaskUnlink`), returning the task to the backlog. In morning review, items in the walk are by definition unlinked. However, as a guard: **Unlinking must NEVER auto-advance**; only successful *linking* to today triggers advance.

---

### 3.3 `<ctrl+shift+p>`: The Task Card Modal

#### Intended Behavior
The Task Card (`bob-navigation-hotkeys:set-bullet-property`) presents a modal with actions for setting priority, scheduling dates, cancelling, and releasing lanes. Bryan notes:
> *(assuming a task card option is selected that removes the review item from the review stack)*

If and only if the chosen action removes the task from the review stack, closing the modal should automatically trigger a jump to the next review item.

#### Granular Action Matrix for Task Card
The table below evaluates every possible action inside the Task Card against review stack removal:

| Task Card Action / Stage | Modifies Task? | Removes from Review Stack? | Auto-Advance? | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Recommended Roll (`Ctrl+Enter` on card)** | Yes | **Yes** | **YES** | Rolls `scheduled` date to a future date ($> \text{today}$). Future-scheduled tasks are excluded from all review tiers. |
| **Recommended Decay / Cancel** | Yes | **Yes** | **YES** | Closes task as Cancelled (`[-]`) or rolls date forward. |
| **Cancel Task (`cancel` action)** | Yes | **Yes** | **YES** | Sets checkbox to `[-]` (Cancelled) with cancel log. Task is closed. |
| **Schedule Date $\to$ Future Date** | Yes | **Yes** | **YES** | User selects date $> \text{today}$. Excluded from review walk. |
| **Schedule Date $\to$ Today or Past** | Yes | No | **NO** | Task remains due today (or in RETURNED tier). |
| **Priority Selection with Date Roll** | Yes | **Yes** | **YES** | Applying priority (e.g., P2/P3/P4) through the priority ladder automatically rolls the `scheduled` date forward. Excluded from walk. |
| **Priority Selection without Roll** | Yes | No | **NO** | Changing priority level without rolling date leaves task due today in the current tier. |
| **Lane Release (`lane` action on Pending/Next)**| Yes | **Yes** (usually) | **YES** | Releasing from Pending (`/`) or Next (`*`) to Ready drops the task out of the daily lane review tier (unless already rotten). |
| **Edit Dependencies (`depends-on`)** | Maybe | Conditional | **NO** | Interactive sub-modal. Adding an open blocker derives Blocked status, but user is typically managing prerequisites. Do not auto-jump from sub-modal. |
| **Review Interval (`review-every`)** | Yes | No | **NO** | Adjusts `[refresh:: N]`. Does not stamp or resolve today's review. |
| **Dismiss / Cancel (`Esc`, `q`, `Ctrl+[`)** | No | No | **NO** | User aborted without writing. Must remain on task. |

#### Implementation Hook in Task Card
In `bob-navigation-hotkeys/src/350-picker-task-card.js`:
Inside `dispatchTaskCardIntent(intent)`:
```javascript
const result = await this.executeIntent(intent);
if (result === true && this.isOpen) {
  this.close();
  // Check review walk auto-advance
  if (this.removesFromReviewStack(intent) && this.plugin.isReviewWalkLanding(this.editor)) {
    void this.plugin.advanceReviewWalkIfLanding(this.editor, {
      action: intent.type,
      noticePrefix: intent.noticePrefix,
    });
  }
}
```

---

## 4. Other Candidate Keymaps & Actions

Bryan requested:
> *You should look for and propose other keymaps / actions that should trigger a jump to the next review item when in the middle of a GTD morning review.*

We surveyed the full keymap registry across `bob-plugins` and identified the following candidates:

### 4.1 HIGH RECOMMENDATION: `Alt+N` (`toggle-task-lane`)
- **Current Behavior:** Toggles between Next (`*`) and Ready (` `), or prompts for work log when releasing Pending (`/`) to Ready.
- **Workflow in Morning Review:**
  1. In `PENDING` / `NEXT` tiers: The user is performing daily lane review. The core decisions are:
     - Keep in lane $\to$ `Ctrl+Alt+F` (stamps freshness and advances).
     - Commit to Today $\to$ `Ctrl+Shift+Enter` (links to today and advances).
     - **Demote back to Ready** $\to$ `Alt+N`.
  2. In `NEW` tier: The user decides to commit a new inbox task to Next Actions $\to$ `Alt+N`.
- **Impact on Walk:** Committing to Next stamps freshness today (`stampLine: this.getFreshnessStampLine()`), which removes it from today's walk. Releasing from Next/Pending to Ready removes it from the daily lane walk.
- **Recommendation:** **Add auto-advance to `Alt+N` when on a review landing.** Releasing or committing a lane task is an unambiguous triage decision. Without auto-advance on `Alt+N`, the daily lane review workflow is lopsided: keeping advances, but releasing stalls.

### 4.2 MEDIUM RECOMMENDATION: `Ctrl+Shift+]` (`toggle-obsidian-task`)
- **Current Behavior:** In `task-status-cycler`, toggles an Obsidian task (`- [ ]`) into a plain bullet (`- `), prompting for demotion destination if configured.
- **Impact on Walk:** Once demoted to a plain bullet, it is no longer an open `#task`. It disappears from the freshness queue immediately.
- **Recommendation:** **Trigger auto-advance upon demotion.** If the user decides during review that an item is a note/reference rather than an actionable task and demotes it, the item has been triaged.

### 4.3 MEDIUM RECOMMENDATION: `Ctrl+Shift+M` (`move-tasks-to-note`)
- **Current Behavior:** Moves the task under the cursor to another project/area note.
- **Impact on Walk:** The task is cut from the current file. The cursor on the current file is now on a different line or whitespace.
- **Recommendation:** **Trigger auto-advance.** Moving a task out of the note during morning triage means the user filed it away. Continuing the review should advance to the next due item rather than leaving the cursor in limbo on the line where the task used to be.

### 4.4 STRONG ANTI-RECOMMENDATION: `Alt+[` / `Alt+]` (Task Status Cycling)
- **Current Behavior:** Cycles through task statuses (` ` $\to$ `/` $\to$ `x` $\to$ `-` $\to$ `?`).
- **Why It Should NOT Auto-Advance:** Status cycling is an interactive, sequential gesture. A user might press `Alt+]` twice in quick succession to move from ` ` to `x`, or three times to reach `-`. If the very first transition into a closed symbol (`x`) instantly yanked the editor to a different note in another folder:
  - It would cut off multi-stroke cycling.
  - It would cause severe disorientation.
- **Rule:** Status cycling should remain in-place. Terminal completion should be reserved for explicit execution keymaps (`<ctrl+enter>`, Task Card, etc.).

---

## 5. Comprehensive Critique of the Plan

### 5.1 Is This a Good Idea?
**Yes, with caveats.**

#### The Strengths
1. **Aligns with the GTD Mental Model:** The morning review is not meant to be a deep-work editing session; it is David Allen's "processing and organizing" phase. The goal is rapid, decisive triage:
   - *2-minute action?* Do it now $\to$ `<ctrl+enter>` $\to$ Next.
   - *Doing it today?* Schedule it $\to$ `<ctrl+shift+enter>` $\to$ Next.
   - *Not doing it soon?* Roll it $\to$ `Ctrl+Shift+P` $\to$ Next.
   - *Still valid backlog?* Confirm it $\to$ `Ctrl+Alt+F` $\to$ Next.
   Requiring a trailing `]s` after every single one of these actions violates the principle of least keystrokes and breaks cognitive flow.
2. **Eliminates Muscle Memory Mismatches:** Currently, `Ctrl+Alt+F` advances, `<ctrl+enter>` in PRE advances, but `<ctrl+shift+enter>` and Task Card do not. The user is constantly second-guessing: *"Did this key advance me, or do I need to press `]s` now?"* Standardizing auto-advance across all resolving gestures creates predictability.

---

### 5.2 Potential Drawbacks & Failure Modes

#### 1. "The Runaway Conveyor Belt" (Lost Editing Context)
*The Problem:* A user presses `<ctrl+enter>` to complete a task, but immediately wanted to press `o` in Vim to write a quick follow-up chore, or wanted to read the surrounding context in that file. If the system instantly navigates away to a file 5 folders away, the user is ripped out of their context.
*Contrast with `Ctrl+Alt+F`:* Why does `Ctrl+Alt+F` work so well? Because `Alt+F` exists alongside it! Bryan has `Alt+F` when he wants to confirm and stay, and `Ctrl+Alt+F` when he wants to confirm and jump.
*Does `<ctrl+enter>` have a "stay" twin?* No; `<ctrl+enter>` is a universal keymap.

#### 2. False Positives (Accidental Jumps Outside Morning Review)
*The Problem:* If the "in review" detection logic is too loose, pressing `<ctrl+enter>` or `<ctrl+shift+enter>` at 2:00 PM during deep work could suddenly jump the user to an overdue task in another folder.

#### 3. Boundary Blindness
*The Problem:* In Decision 8, transitions between tiers are semantically significant. PRE is commitment habits; NEW is fresh inbox tasks; ROTTEN is decaying backlog. If auto-advance silently jumps from the last PRE row into NEW, the user might not realize they have transitioned from checklist habits into project triage.

#### 4. Undo and Mistake Recovery Across Files
*The Problem:* In Vim/Obsidian, editor undo (`u`) is buffer-local. If you press `<ctrl+enter>` on File A, auto-jump moves you to File B. If you realize you made a mistake and press `u`, you will undo whatever was previously in File B, rather than restoring the task in File A!

---

### 5.3 Required Adjustments to Requirements

To eliminate the risks above, we propose the following concrete adjustments:

#### Adjustment 1: Vim Jump List Integration (`<C-o>` Escape Hatch)
Before executing any auto-jump from a resolving keymap, `bob-navigation-hotkeys` must push the current file and cursor position onto Vim's jump list using `recordVimJump(cm, previousPos)`.
- *Result:* If Bryan ever completes a task or rolls a date and realizes *"Wait, I wanted to stay on this note!"*, he simply presses **`<C-o>`** in Vim normal mode. The editor immediately jumps back to the exact note and line he just acted on.

#### Adjustment 2: Bulletproof Landing Validation
An action should trigger auto-advance **if and only if**:
1. `this.reviewLanding` is non-null.
2. `landing.day === this.laneReleaseDateText({})` (same calendar day).
3. `activeView.file.path === landing.path`.
4. `activeEditor.getLine(cursor.line) === landing.text` (the cursor is still on the exact task line that was landed on).
If Bryan landed on a task via `]s`, but then moved the cursor to another line or switched files to look something up, `reviewLanding` is invalidated and no auto-advance occurs.

#### Adjustment 3: Boundary Notice Visibility
When an auto-advance crosses a tier boundary (e.g. from PRE to NEW, or commitments to ROTTEN):
The notice must combine the completion outcome and the boundary announcement:
```text
✓ Done · Morning habit checklist
──────────────────────────────────────
Commitments next · 14 tasks due
[1/14] NEW · Personal/Health · Schedule dentist
```

#### Adjustment 4: Clean Review Exhaustion State
When the very last item in the entire review walk is resolved via `<ctrl+enter>` or Task Card:
Do not leave the user hanging or attempt an illegal wrap. Display the canonical review completion banner:
```text
✓ Done · Final review chore
──────────────────────────────────────
🎉 GTD Morning Review Complete — 0 tasks due
```

---

## 6. Technical Implementation Architecture

### 6.1 Unified Review Walk API in `bob-navigation-hotkeys`
All review walk state (`reviewLanding`, `reviewAnchor`, `jumpToDueTask`) lives in `bob-navigation-hotkeys`. We should expose a clean, consolidated API method on `createDependencyNavApi`:

```javascript
// In plugins/bob-navigation-hotkeys/src/480-review-jump-and-nav-api.js
return Object.freeze({
  version: 3, // Bumped from 2
  
  // Check if active editor cursor is currently sitting on the review landing
  isReviewLanding(editor) {
    return plugin.isReviewLandingActive(editor);
  },

  // Complete and advance from a resolving keymap
  async advanceReviewWalkIfLanding(editor, options = {}) {
    if (!plugin.isReviewLandingActive(editor)) {
      return false;
    }
    return await plugin.advanceReviewWalkFromAction(editor, options);
  },
  
  // Backward compatibility
  claimReviewWalkCompletion(editor) {
    return plugin.claimReviewWalkCompletion(editor);
  }
});
```

### 6.2 The Core Advance Method: `advanceReviewWalkFromAction`
In `bob-navigation-hotkeys/src/535-plugin-review-checklist-walk.js`:

```javascript
async advanceReviewWalkFromAction(editor, options = {}) {
  const landing = this.reviewLanding;
  if (!landing) return false;

  const todayText = this.laneReleaseDateText({});
  const api = this.requireFreshnessApi();
  const queueBefore = this.readFreshnessQueue(api);
  
  // 1. Build anchor marking the current task as handled
  const handledKeys = new Set(
    this.reviewAnchor && reviewAnchorIsCurrentDay(this.reviewAnchor, todayText)
      ? this.reviewAnchor.keys
      : []
  );
  handledKeys.add(landing.key);
  
  this.reviewAnchor = buildReviewAnchor(
    queueBefore,
    Array.from(handledKeys),
    landing.rank || 1,
    todayText
  );
  
  // 2. Clear landing so duplicate actions don't re-trigger
  this.reviewLanding = null;

  // 3. Register current position in Vim jump history before leaping
  this.recordVimJumpHistoryBeforeReviewAdvance(editor);

  // 4. Jump to the next due task from the new anchor
  const jumpResult = await this.jumpToDueTask(1, {
    fromStamp: this.reviewAnchor,
    actionNotice: options.notice || null,
  });

  return jumpResult;
}
```

### 6.3 Wiring Into `<ctrl+enter>` (`task-status-cycler`)
In `task-status-cycler/src/160-plugin-completion.js`:
Extend `claimReviewWalkCtrlEnter` to handle all tiers:
1. Cycler calls `api.claimReviewWalkCompletion(editor)`.
2. Hotkeys checks `isReviewLandingActive(editor)`.
3. If active, Hotkeys:
   - Calls `cycler.completeTaskAtCursor(editor)`.
   - On `{ ok: true }`, calls `advanceReviewWalkFromAction(editor, { action: "close" })`.
   - Returns `{ ok: true }` to Cycler.

### 6.4 Wiring Into `<ctrl+shift+enter>` (`block-id-prompt`)
In `block-id-prompt/src/120-plugin-pomodoro-links.js`:
In `applyPomodoroTaskLink`:
```javascript
// At the end of applyPomodoroTaskLink, after writes succeed:
this.reportPomodoroLinkOutcome(plan, pomodoroPlan, isNewId);

const navApi = this.app.plugins?.plugins?.["bob-navigation-hotkeys"]?.api;
if (navApi && Number(navApi.version) >= 3) {
  void navApi.advanceReviewWalkIfLanding(source.editor, {
    action: "pomodoro-link",
    notice: "Linked to Today's Pomodoro",
  });
}
return true;
```

### 6.5 Wiring Into Task Card (`<ctrl+shift+p>`)
In `bob-navigation-hotkeys/src/350-picker-task-card.js`:
In `dispatchTaskCardIntent(intent)`:
```javascript
// After modal action succeeds and closes:
if (result === true && this.isOpen) {
  this.close();
}

if (result === true && this.intentRemovesFromReviewStack(intent)) {
  if (this.plugin.isReviewLandingActive(this.editor)) {
    void this.plugin.advanceReviewWalkFromAction(this.editor, {
      action: intent.type,
      notice: intent.completionNotice,
    });
  }
}
```

---

## 7. Recommended Solution & Step-by-Step Implementation Plan

### Phase 1: `bob-navigation-hotkeys` Engine & API Generalization
1. **API Expansion:** Bump `createDependencyNavApi` to `version: 3`. Add `isReviewLanding(editor)` and `advanceReviewWalkIfLanding(editor, options)`.
2. **Generalize `claimReviewWalkCtrlEnter`:** Remove the `tier === "pre" || tier === "post"` gate. Allow any review landing task to be completed via `cycler.completeTaskAtCursor` and advanced.
3. **Seamless Tier Traversal:** In `completeReviewChecklistRow`, replace `withinGroup: true` with dynamic traversal: when the last PRE item is completed, advance into `NEW` with the combined boundary notice.
4. **Vim Jump History Push:** Hook into `installVimJumpHistoryMappings` so every review auto-jump pushes the source position to the jump stack, enabling instant `<C-o>` undo.

### Phase 2: Task Card (`<ctrl+shift+p>`) & `Alt+N` Auto-Advance
1. **Task Card Intent Filter:** Implement `intentRemovesFromReviewStack(intent)` in `TaskCardModal`. Wire it to `advanceReviewWalkFromAction` on modal close for:
   - Recommended Roll / Decay / Cancel (`Ctrl+Enter` on card).
   - Cancel action (`confirmCancelReason`).
   - Future schedule dates (`scheduled > today`).
   - Priority ladder rolls that advance `scheduled`.
   - Lane releases to Ready.
2. **`Alt+N` Integration:** In `toggleTaskLaneOnTasks`, if `this.reviewLanding` is active and the task was released from Next/Pending or committed to Next, trigger `advanceReviewWalkFromAction`.

### Phase 3: `block-id-prompt` (`<ctrl+shift+enter>`) Integration
1. **Cross-Plugin Hook:** In `block-id-prompt/src/120-plugin-pomodoro-links.js`, feature-detect `navApi.version >= 3`.
2. **Post-Transaction Advance:** Call `navApi.advanceReviewWalkIfLanding` immediately after `reportPomodoroLinkOutcome` verifies both note writes have settled.

---

## 8. Summary Comparison of Review Keymap Behaviors

| Keymap / Action | Context | Current Behavior | Proposed New Behavior | User Control / Escape Hatch |
| :--- | :--- | :--- | :--- | :--- |
| **`<ctrl+enter>`** | On PRE checklist item | Completes row $\to$ jumps within PRE; stops at PRE end | Completes row $\to$ jumps within PRE; **advances to NEW** at PRE end | `<C-o>` jumps back |
| **`<ctrl+enter>`** | On NEW / PENDING / NEXT / ROTTEN | Toggles checkbox in place; stays on task | **Completes task $\to$ auto-jumps to next due task** | `<C-o>` jumps back; reopen (`[x]` $\to$ `[ ]`) stays |
| **`<ctrl+shift+enter>`** | On open task | Links to Today's Pomodoro; stays on task | **Links to Today $\to$ auto-jumps to next due task** | `<C-o>` jumps back; unlinking stays |
| **`<ctrl+shift+p>` $\to$ Roll/Cancel** | On open task | Writes roll/cancel; closes card; stays on task | **Writes roll/cancel $\to$ auto-jumps to next due task** | `<C-o>` jumps back; Esc/q cancels without jump |
| **`<ctrl+shift+p>` $\to$ Inspect/No-roll** | On open task | Changes property in place; stays on task | **Stays on task** (no jump) | Unchanged |
| **`Alt+N` (toggle lane)** | On Pending/Next or Ready | Releases or commits lane; stays on task | **Releases/commits $\to$ auto-jumps to next due task** | `<C-o>` jumps back |
| **`Ctrl+Alt+F`** | On open task | Keeps task $\to$ jumps to next task | **Keeps task $\to$ jumps to next task** (Already works) | Use `Alt+F` to keep and stay |
| **`Alt+F`** | On open task | Keeps task; stays on task | **Keeps task; stays on task** (Preserved) | Canonical "stay" keymap |
| **`Alt+[` / `Alt+]`** | On open task | Cycles status in place | **Cycles status in place** (No jump) | Explorable, multi-stroke safe |

This design achieves the exact frictionless "conveyor belt" morning review Bryan envisions, while preserving full architectural integrity, multi-file transactional safety, and instant Vim jump recovery.
