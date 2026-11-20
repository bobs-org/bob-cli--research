# Design Research: `<ctrl+j>` Jump Successor in Obsidian & Bob Mac Capture

> **Decision Question:** How should Bob support `<ctrl+j>` inside the successor panel (Obsidian `SuccessorOfferPickerModal` and Mac Capture `CapturePullInChoiceCard`) to mark a single task—regardless of whether it is Left Open, Pulled In, Done, or Cancelled—to open and focus in Obsidian after the close completes (overriding `<cmd+enter>` in Capture)?

---

## 1. Executive Summary

- **Verdict on the Idea:** **Strong approve.** Today Bob couples *"leave unlinked"* with *"stay on the predecessor / advance the `]s` walk"*, and couples *"pull into Today"* with *"manually navigate to the successor's canonical note afterward."* Adding an orthogonal, single-slot **`jumpKey` (`↗ Jump`)** inside the successor panel cleanly bridges that gap without polluting Today's Pomodoro ledger when you just want to edit, schedule, or reprioritize a successor.
- **Top Recommended Design:**
  1. **Model `<ctrl+j>` as a single-slot orthogonal navigation flag (`jumpKey`)** alongside the four per-offer outcomes (*Leave*, *Pull In*, *Done*, *Cancel*), toggling on the same row and seamlessly transferring when pressed on another row.
  2. **Fix Commit Semantics for Jump-Only (`0` pull-ins, `0` closes, `1` jump):** When `jumpKey` is set, **suppress `Enter`/`Return` highlight-fallback** (mirroring how §12.22 verdicts already suppress fallback), allow `{ picks: [], closes: [], jumpKey }` to commit cleanly rather than abort or pull in the highlighted row, and keep `Esc`/`Ctrl+[` single-press when no destructive verdicts are staged.
  3. **Make `bob capture` Authoritative on Mac Capture (`-j / --jump-offer <N|KEY>`):** Rather than reconstructing vault coordinates in Swift from preview state, pass the chosen offer key to `bob capture` so Bob resolves post-write coordinates *after* `^block-id` minting, `Cancel Log` line shifts, and `--inbox-route` moves—emitting a single-target `open_notes` entry (overriding `Cmd+Return` / `Ctrl+Return` targets, carrying fresh `<line>:<digest>` `ref`, `block_id`, and coherent `NotificationService` click targets).
  4. **Park (Never Auto-Advance) the Obsidian `]s` Review Walk:** Reuse `parkReviewWalkAfterMove` + `focusTaskAnchor` (with Vim `<C-o>` history) + `flashBobOpenNotesLandingLine` (`.bob-landing-flash`) in Obsidian so the cursor stays on the jump successor instead of getting yanked away by `advanceReviewWalkAfterAnswer`.
  5. **Polish the UI for Instant Clarity:** Dedicated indigo/accent `↗ Jump` pill + 2px left rail accent distinct from green Pull-In / emerald Done / crimson Cancel, dynamic primary button labels (`"Leave Open & Jump ↩"` vs `"Pull In 1 & Jump ↩"`), off-filter safety hint if the marked row is filtered out, and accessible status messaging.

---

## 2. Critique of the Plan & Alternative Approaches

### 2.1 Is This a Good Idea?

Yes. Comparing existing navigation gestures against real daily triage workflows shows an exact missing primitive:

- In Obsidian, `Ctrl+Shift+M` follows a moved task (`focusTaskAnchor` + `parkReviewWalkAfterMove`), while closing a task from `]s` or `Ctrl+Enter` offers successors in `SuccessorOfferPickerModal` and leaves you behind on the predecessor (or immediately advances `]s` to the next review card).
- In Mac Capture, submitting a task completion can surface `CapturePullInChoiceCard`, and `Cmd+Return` / `Ctrl+Return` opens `open_notes` (the captured/routed day/note targets), **not** an un-pulled or newly edited successor residing in a project or area note.
- Both use cases Bryan highlighted are poorly served today:
  1. **Leave Open + Edit / Prioritize:** You close *Task A*; *Task B* unblocks; you do *not* want *Task B* in today's Pomodoro, yet you want to inspect its subtasks, raise its priority, or reschedule it right away. Today, pressing `Enter` accidentally pulls it into Today; pressing `Esc` loses it in your vault unless you search for it manually.
  2. **Pull In + Refine:** You pull *Task B* into Today *and* want to edit its text or inspect its project notes immediately in its canonical file.

### 2.2 Alternative Approaches Evaluated

| Alternative | How It Would Work | Why `<ctrl+j>` Orthogonal Mark Wins |
| :--- | :--- | :--- |
| **A. Immediate-Execute Hotkey (`Ctrl+J` commits immediately)** | Pressing `Ctrl+J` skips `Enter` and immediately submits `{ pull highlighted or skip }` + jumps to highlighted row. | **Fails multi-offer composition.** Cannot combine *"Cancel stale B (`Ctrl+Shift+X`), Pull In A (`Space`), and Jump to A (or un-pulled C)"* without ordering pitfalls. Also collides conceptually with `Ctrl+Return` (`Confirm & Open`) in Mac Capture. |
| **B. 5th Mutually Exclusive Row State** | Row state becomes `Leave \| Pull In \| Done \| Cancel \| Jump`. | **Breaks "Pull In + Jump" and "Done/Cancel + Jump".** Users would still have to pull a task in and then search for it manually when it needs edits. |
| **C. Inline Task Editor Inside the Picker Modal** | Add quick priority/schedule editing directly inside the successor panel. | **Overbuilt and fights the environment.** Obsidian already gives full Vim motions, `bob-ledger-tools` property cards, dependency editors, and full project context—jumping directly to the canonical line leverages all of it cleanly. |

**Conclusion:** An **orthogonal single-slot flag (`jumpKey`)** toggled via `<ctrl+j>` is minimal, composable, reversible before commit, and cleanly separates *vault plan mutations* (`Leave / Pull In / Done / Cancel`) from *post-commit cursor destination*.

---

## 3. Codebase Findings Across All Three Repositories

### 3.1 Obsidian (`bob-plugins`)

1. **Picker Modal (`plugins/bob-navigation-hotkeys/src/206-successor-picker-modal.js`, `206a`, `206c`, `206d`):**
   - `SuccessorOfferPickerModal` extends `FilteredPickerModal` (`200-filtered-picker-modals.js`) and tracks `markedKeys` (`Set`), `verdicts` (`Map`), `destinationOverrides` (`Map`), `reasonEditKey`, and `escArmed`.
   - Every offer row from `task-status-cycler/src/085b-successor-offers.js` (`buildSuccessorPickerTaskContext`) already carries `row.task = { path, line (1-based), text, displayText, status, preimage }` (`normalizeSuccessorPickerTaskContext` in `206a-successor-picker-model.js`).
   - **Critical constraint found in `206-successor-picker-modal.js`:**
     - `handleKeydown` / `applySelection` falls back to picking the **highlighted row** whenever `markedKeys.size === 0` and `verdicts.size === 0`.
     - `createSuccessorPickerApi(plugin)` (`version: 4`, `pick(model)`) rejects any settlement where `picks.length === 0 && closes.length === 0`, returning `null` (aborting the close/link flow).
   - **Styling (`plugins/bob-navigation-hotkeys/styles.css`):**
     - `styles.css:3375–3720` styles `.bob-successor-*` rows, badges, and `.bob-successor-verdict-actions` hover action buttons.
     - `styles.css:129–150` defines `.cm-line.bob-landing-flash` (`1.2s ease-out both`, `--interactive-accent` wash + `inset 2px 0 0 var(--interactive-accent)` left rail, respecting `@media (prefers-reduced-motion: reduce)`).
2. **All Callers of `pickSuccessorOffers`:**
   - `task-status-cycler/src/137-plugin-successor-project.js` (`planAndApplySuccessorsNow`) and `139-plugin-successor-parked.js` (`offerParkedSuccessors`) — task closes, Pomodoro closes, and unlinks.
   - `bob-navigation-hotkeys/src/667-plugin-project-promotion.js` (`buildPromotionSuccessorModel` in `122-project-promotion-successors.js`) — project promotion successor picker. Its `modelRows` currently contain `key`, `text`, `notePath`, `status`, `selectable` (plus `planPromotionSuccessorRows` has `line`, `rawLine`, `blockId`), though `buildPromotionSuccessorModel` drops `line`/`rawLine`/`blockId` when mapping `modelRows`.
   - `bob-navigation-hotkeys/src/429a-relation-merge-commit.js` (`taskMergeOfferPickerModel`) — all rows represent **Pomodoro link hand-off slots** pointing to the *same* `targetTitle`/`targetPath` without per-row line anchors.
3. **Obsidian Navigation, Landing Flash & Review Walk (`480`, `536`, `537`, `650`, `670`, `675`, `676`, `140`):**
   - `focusTaskAnchor(file, anchor, { vimJumpContext, failureNotice, ensureEditing })` (`650-plugin-move-commit.js:530`) opens the target via `openMarkdownFileWithLeafReuse`, ensures an editable Markdown view, uses `jumpOrDeferTaskMoveDestination`, focuses the editor, and records Vim `<C-o>` history—**but is not yet exposed on `createDependencyNavApi` (`480-review-jump-and-nav-api.js`, `version: 3`)**.
   - `obsidian://bob-open-notes` (`676-plugin-open-notes-uri.js`) already combines `waitForBobOpenNotesFreshness` (up to `2000ms` at `50ms` polls checking `<line>:<digest>` `ref` and `block_id`), `focusTaskAnchor`, and `flashBobOpenNotesLandingLine` (`.bob-landing-flash`).
   - **Review Walk (`]s`) Collision:** In `task-status-cycler/src/140-plugin-vim.js:261–292`, closing a row on a `]s` walk landing captures `reviewOrigin`, awaits `finalizeClosedTasks`, and calls `settleReviewOrigin` -> `continueReviewWalkAfter` -> `advanceReviewWalkAfterAnswer`, which moves the cursor to the next review item. Meanwhile `trackOpenedFile` (`670-plugin-project-files.js:521`) clears `this.reviewLanding` on file switch. By contrast, `Ctrl+Shift+M` calls `parkReviewWalkAfterMove(origin, handledRefs)` (`537-plugin-review-move-park.js:200`) *before* focusing the destination (`650-plugin-move-commit.js:445`), clearing `this.reviewLanding`, computing the next `this.reviewAnchor`, and releasing the walk lock without jumping away.

### 3.2 Bob Mac Capture (`bob-mac-capture`) & CLI (`bob-cli`)

1. **Pull-In State & UI (`CapturePullInOutcomes.swift`, `CapturePullInChoice.swift`, `CapturePullInChoiceView.swift`):**
   - `CapturePullInOutcomes` holds `rows`, `highlightedKey`, `marks: Set<String>`, `verdicts: [String: Verdict]`, and `isEscArmed`. Non-selectable (`still_blocked` / future-scheduled) rows are skipped in keyboard navigation (`visibleSelectableKeys`).
   - `CapturePullInChoiceState` manages `openAfterCapture: Bool`, `outcomes`, `canCommit`, `activeReasonKey`, `consequenceMessage`, and `verdictRefusalMessage`.
   - `CapturePullInChoiceFooter` renders the primary action (`Pull In … ↩` / `Apply … ↩`) and `Skip ⇧↩` buttons, displaying trailing `arrow.up.forward` icons when `openAfterCapture == true`.
2. **Keyboard Routing (`CaptureKeyCommandRouter.swift`, `CapturePanelController.swift`):**
   - `pullInChoiceCommand(...)` (`CaptureKeyCommandRouter.swift:837–933`):
     - `Return` -> `.confirmPullInChoice`
     - `Ctrl+Return` -> `.confirmPullInChoiceAndOpen`
     - `Shift+Return` -> `.chooseNoPullInOffers`
     - `Esc` / `Ctrl+[` -> `.cancelPullInChoice`
     - `Space` / `Tab` / `Cmd+A` -> marks; `Ctrl+X` / `Ctrl+Shift+X` -> verdicts.
     - **`KeyCode.j` with `.control` is currently completely unbound (`nil`) inside `pullInChoiceCommand`!** (In the main draft editor at line 696, `Ctrl+J` triggers `.insertBulletNewline`, and `RefsKeyRouter.swift` binds `KeyCode.j` separately; neither conflicts inside the Pull-In sheet.)
   - `CapturePanelController.swift:3226–3239` already passes `pullInChoiceVisible`, `pullInFilterFocused`, `pullInFilterIsEmpty`, and `pullInReasonFocused` in `CaptureKeyRoutingContext`.
   - Note also: in the main draft editor (`CaptureKeyCommandRouter.swift:675–686`), **both `Cmd+Return` and `Ctrl+Return`** set `.submitAndOpen` (`openAfterCapture: true`), and inside `CapturePullInChoice` itself `Ctrl+Return` arms `openAfterCapture` while `Cmd+Return` is ignored.
3. **Submission Continuation, Refusal Recovery, `open_notes`, and Notifications (`CapturePanelModel.swift`, `CaptureOpenPlan.swift`, `NotificationService.swift`, `bob-cli/src/native/capture/`):**
   - `dispatchCapture` packages `CaptureInboxRouteSubmitContext` holding `openAfterCapture`, `pullInSelection`, `offerVerdicts`, and `pullInChoiceForBack`. If `bob capture` subsequently opens `InboxRouteChoice`, answering it calls `processClient.capture(...)` *again* with `pullInSelection`, `offerVerdicts`, and `inboxRouteAnswers`, which can move a task from `inbox.md` into another note!
   - If a commit fails on offer validation/staleness, `reopenPullInChoiceAfterOfferRefusal` refreshes offers via `choice.refresh(offers:)` preserving surviving marks, verdicts, reasons, and highlight.
   - `bob capture` constructs `open_notes: [OpenNoteJson]` (`src/native/capture/open_notes.rs`) on **staged final post-write text** (`path`, `relative_path`, `role`, `label`, `line`, `ref`, `block_id`), which `CaptureOpenPlan(openNotes:captures:)` turns into `obsidian://bob-open-notes?...` URLs—and `NotificationService.successContent` stores `openPlanKey` in notification `userInfo` so clicking the macOS notification opens the exact same destination (`targetURLs`).
   - In `src/native/capture/cli.rs`, **`-j` is currently unused** among short options (`-X, -c, -x, -b, -d, -E, -f, -h, -i, -m, -n, -R, -p, -r, -s, -t, -D` are taken), and `sase/memory/cli_rules.md` requires every public long option to have a short alias and options to be kept alphabetically sorted.

---

## 4. Justified Requirement Adjustments & Edge Cases

Implementing the literal spec without addressing the 6 interactions below would create silent pull-ins, lost focus, or stale line jumps. Each adjustment below is strongly recommended and should be approved alongside the feature:

| # | Area | Literal Spec Gap / Friction | Recommended Adjustment |
| :-: | :--- | :--- | :--- |
| **1** | **Empty Pull-In + Jump Commit (`0` picks, `0` closes, `1` jump)** | Today `Enter` with `0` marks & `0` verdicts **pulls in the highlighted row**, and `createSuccessorPickerApi` returns `null` (abort) for empty `{ picks: [], closes: [] }`. | **Suppress highlight-fallback whenever `jumpKey != nil`** (mirroring §12.22 verdicts). Allow `{ picks: [], closes: [], jumpKey }` as a valid first-class commit meaning *"apply close, pull in nothing, jump to target"*. Show clear CTA copy (`"Leave Open & Jump ↩"`) so the user knows nothing will be pulled in. |
| **2** | **Capture Submit Shortcuts (`Cmd+Return`, `Ctrl+Return`, `Return`, `Shift+Return`)** | Prompt mentions overriding `<cmd+enter>` if used. Today **both `Cmd+Return` and `Ctrl+Return`** in the draft set `openAfterCapture = true`, `Ctrl+Return` inside the Pull-In card also sets it, and plain `Return` normally does **not** open Obsidian. | **Any `jumpKey != nil` implies opening Obsidian on commit**—even on plain `Return`! Furthermore, when `jumpKey != nil` and `openAfterCapture == true` (via draft `Cmd+Return` *or* draft/card `Ctrl+Return`), **override `open_notes` cleanly to focus only the jump successor**. Reserve `Shift+Return` (`Skip`) for *"discard pull-ins/verdicts and do not jump"* (or keep `Skip` clean while plain `Return` commits `"Leave Open & Jump"`). |
| **3** | **Obsidian `]s` Review Walk Collision** | Completing a task from a `]s` walk landing triggers `settleReviewOrigin` -> `advanceReviewWalkAfterAnswer`, which immediately moves the cursor to the *next* review row—fighting the jump and risking stale `reviewLanding` via `trackOpenedFile`. | **Follow `decisions:task-move-never-advances-the-walk`:** When a jump occurs on a walk landing, call **`parkReviewWalkAfterMove` before focusing** the jump target, suppress `advanceReviewWalkAfterAnswer`, and enqueue Vim **`<C-o>`** on the completed task so `]s` resumes cleanly later and `<C-o>` steps back immediately. |
| **4** | **Caller Scope & Non-Selectable (`muted`) Rows** | Prompt refers to "the successor panel." Obsidian actually has 4 callers (`cycler`, `parked`, `project-promotion`, `relation-merge`), and pickers contain muted (`still_blocked` / future-scheduled) rows skipped by keyboard nav. | **Enable `<ctrl+j>` on all selectable offer rows** across task closes, parked unlinks, and project promotion (after forwarding `line`/`rawLine`/`blockId` in `buildPromotionSuccessorModel`). **Disable `<ctrl+j>` (`allowJump: false`) in Relation Merge** (`429a`), where rows are Pomodoro hand-off slots for one shared task. Keep muted rows unselectable in V1 to match `Space`/`Ctrl+X`/`Ctrl+Shift+X` nav. |
| **5** | **Destructive-Esc Guard (`isEscArmed` / `escArmed`)** | Verdicts (`Ctrl+X`/`Ctrl+Shift+X`) arm a two-step `Esc` confirmation because they mutate unrelated vault tasks on commit. | **Do NOT arm 2-step `Esc` for `jumpKey` alone.** Choosing a jump target makes zero extra vault writes; pressing `Esc` / `Ctrl+[` with only `jumpKey` (and 0 verdicts) should immediately cancel and discard `jumpKey` in one stroke. Wait until actual verdicts exist to arm `Esc`. |
| **6** | **Focus & Input Guards for `Ctrl+J`** | Both modals contain an inline filter input and an inline Cancel Reason editor (`reasonEditKey` / `pullInReasonFocused`). | **`Ctrl+J` MUST toggle the highlighted row even when the filter input has focus** (call `event.preventDefault()` in Obsidian so Chromium/macOS text-input defaults don't eat `Ctrl+J`), **and MUST be suppressed when `reasonEditKey` / `pullInReasonFocused` is active** so typing a Cancel reason is never interrupted. Preserve `jumpKey` in `CapturePullInOutcomes.refresh(offers:)` across offer refusals and `Back` from Inbox Route. |

---

## 5. Recommended Architecture & Cross-Repo Design

### 5.1 Architectural Choice for Mac Capture: Why Bob Must Resolve the Jump Target (`--jump-offer`)

We evaluated two ways to translate a Mac Capture `jumpKey` into an Obsidian jump:

- **Rejected — Client-Side Swift Synthesis from Preview Offers:** Constructing `CaptureOpenPlan` in Swift directly from `TaskCompleteUnblocked` fields stored before commit fails in four real scenarios:
  1. **Stale line numbers:** Pulling in or closing another offer in the same note injects `^block-id`, `[p:: ...]`, completion dates, or `- Cancel Log` sub-bullets, shifting subsequent lines.
  2. **`--inbox-route` relocation:** Answering `InboxRouteChoice` *after* `CapturePullInChoice` can move a task out of `inbox.md` into a project note; preview-time `notePath` points to the wrong file.
  3. **Missing `^block-id`:** Newly minted block IDs do not exist at preview time.
  4. **Missing `ref` digest:** `obsidian://bob-open-notes` uses `ref1` (`<line>:<digest>`) in `waitForBobOpenNotesFreshness` to wait (up to 2s) until Obsidian's file index reflects Bob's write on disk; without `ref`, Obsidian risks focusing pre-write line numbers.
- **Recommended — Bob-Authoritative `-j / --jump-offer <N|KEY>` Flag (Honors `decisions:mac-capture-is-a-thin-client`):**
  Passing `--jump-offer <KEY>` to `bob capture` delegates all post-write resolution, relocation, `^block-id` lookup, and digest computation to Bob's existing `open_notes` pipeline.

### 5.2 Contract & Data Flow Per Repository

#### Layer 1: `bob-cli` (`src/native/capture/`)

1. **`cli.rs`:**
   - Add `jump_offer_arg()` alphabetically between `inbox_route_arg` and `move_in_arg`:
     - `.long("jump-offer").short('j').value_name("N|KEY")` (single value, repeatable not needed — reject multiple with clap default single-arg error, matching `sase/memory/cli_rules.md` `-j` rule since `-j` is free).
     - Help: `"Mark one successor offer to open in Obsidian (overrides default open-notes); accepts row number or key"`.
   - Wire `jump_offer: Option<String>` onto `CaptureRequest` (only populated on commit runs, or ignored cleanly on dry-run previews).
2. **`pull_in.rs` & `offer_verdicts.rs`:**
   - Resolve `jump_offer` using the same probe-key / row-number resolver built in `offer_verdicts.rs` (`resolve_verdict_probes` / `probe_key`) against the active selectable offers (`plan_with_pull_in` / `plan_with_offer_verdicts`).
   - Crucially, **allow `--jump-offer` to target ANY active offer**—even if it is omitted from `--pull-in`, included in `--pull-in`, listed in `--complete-offer`, or listed in `--cancel-offer`! Do **not** reject `--jump-offer` as conflicting with `-p`, `-x`, `-X`, or `--pull-in none`.
   - Still validate staleness: if `jump_offer` does not match any live selectable offer (or that offer's preimage fails on write), refuse cleanly with structured offer failure (`offers[]`) so Mac Capture's `reopenPullInChoiceAfterOfferRefusal` refreshes seamlessly.
   - Note subtle UX detail: allow `--pull-in none` + `--jump-offer <KEY>` without erroring (represents *"Leave Open + Jump"*).
3. **`open_notes.rs`:**
   - After all staged note edits, `pull_in` mutations, offer closes, and `--inbox-route` moves finish on the final staged file map (`staged_files`):
   - If `jump_offer` resolved to `(path, post_write_text, final_block_id, final_line_text)`:
     - Look up final `line` by `block_id` -> post-write `line_text` -> fallback clamped line on the **final** `path` (automatically accounting for `--inbox-route` relocation if an inbox route moved that task!).
     - Compute `TaskRef` (`<line>:<digest>`) via `open_notes.rs`'s existing ref builder.
     - Replace `open_notes` with the single entry `[OpenNoteJson { path, relative_path, role: "jump_successor", label, line, ref, block_id }]`!
   - Also emit a clean batch/summary field or keep `open_notes` singular—because `CaptureOpenPlan(openNotes:captures:)` already reads `success.openNotes` as authoritative (and `NotificationService` reads `openPlan`), Mac Capture needs **zero custom URL assembly**.

#### Layer 2: `bob-mac-capture` (`Sources/`)

1. **`CaptureCore/CapturePullInOutcomes.swift`:**
   - Add `public var jumpKey: String? = nil` on `CapturePullInOutcomes`.
   - Add mutators:
     - `mutating func toggleJump(key: String)` — sets `jumpKey = (jumpKey == key) ? nil : key`.
     - `mutating func clearJump()` — clears `jumpKey = nil`.
     - Update `mutating func refresh(offers:)` — drop `jumpKey` if its key no longer exists in refreshed selectable rows (and fold into lost-selection feedback if dropped).
2. **`BobMacCapture/CapturePullInChoice.swift` (`CapturePullInChoiceState`):**
   - Update `effectiveSelectionKeys` & `canCommit`:
     - When `jumpKey != nil` and `marks.isEmpty && verdicts.isEmpty`, **`highlightedKey` fallback is suppressed** (just like when `!verdicts.isEmpty`)! Instead, effective pull-in selection becomes **empty (`[]` -> `.none`)** while `canCommit` stays `true` (so pressing `Return` commits `"Leave Open & Jump"` without pulling in the highlighted row!).
     - Even if `isOnlyNotePull == true` and `closeCount == 0` (where `.none` / `Skip` is normally blocked), allow `Return` when `jumpKey != nil` so the user can still jump to inspect a destination task without pulling it in.
   - Expose computed helper properties for view & router clarity:
     - `var jumpTargetRow: CapturePullInOfferRow?`
     - `var isHiddenJumpByFilter: Bool` (true when `jumpKey != nil` and not present in `visibleRows`)
     - `var effectiveWillOpenObsidian: Bool { openAfterCapture || outcomes.jumpKey != nil }`
3. **`BobMacCapture/CaptureKeyCommandRouter.swift` & `CapturePanelController.swift`:**
   - Add enum command `.togglePullInJump`.
   - In `pullInChoiceCommand(...)` (`CaptureKeyCommandRouter.swift:837`), add handler before `default`:
     - Match `event.keyCode == KeyCode.j` with `modifiers == [.control]` (reject `.command`, `.option`, `.shift`) when `context.pullInChoiceVisible && !context.pullInReasonFocused`.
     - Keep `Shift+Return` mapped to `.chooseNoPullInOffers` (*"Skip offers — leave open, no pull-in, no jump"*): if the user staged only `Ctrl+J`, primary `Return` already executes **`Leave Open & Jump ↩`**, keeping `Shift+Return` unambiguous as a fast one-key exit that skips both pull-ins and any staged jump.
4. **`CaptureCore/BobProcessClient.swift` & `BobMacCapture/CapturePanelModel.swift`:**
   - Add `jumpOfferKey: String?` parameter to `BobProcessClient.capture(...)` -> passes `["--jump-offer", key]` when non-nil.
   - Add `jumpOfferKey: String?` to `CapturePullInSelection` or directly alongside `offerVerdicts` in `CaptureInboxRouteSubmitContext` and `dispatchCapture(...)` (preserving it cleanly across `InboxRouteChoice` pause & `reopenPullInChoiceAfter*`!).
   - In `confirmPullInChoice(openAfterCapture:)`:
     - If `marks.isEmpty && verdicts.isEmpty && outcomes.jumpKey != nil`, call `commitPullInChoice(..., selection: .none, jumpOfferKey: outcomes.jumpKey, openAfterCapture: true)`.
     - Otherwise pass `selection` + `verdicts` + `jumpOfferKey: outcomes.jumpKey` and compute final `effectiveOpen = openAfterCapture || outcomes.jumpKey != nil`.
   - In `completeSubmit(...)`:
     - When `success.openNotes` arrives from Bob for a `--jump-offer` submission, `CaptureOpenPlan(openNotes: success.openNotes, captures: captures)` automatically builds the single jump-target `obsidian://bob-open-notes?...` URL for both immediate Obsidian activation and `NotificationService`!

#### Layer 3: `bob-plugins` (`bob-navigation-hotkeys` + `task-status-cycler`)

1. **`bob-navigation-hotkeys/src/206-successor-picker-modal.js`, `206a`, `206c`, `206d`:**
   - **State:** Add `this.jumpKey = null` on `SuccessorOfferPickerModal`. (Reset on modal init; allow options `{ allowJump: model.allowJump !== false && options.allowJump !== false }` so Relation Merge passes `{ allowJump: false }`.)
   - **Action (`toggleJumpForKey(key)`):** Sets `this.jumpKey = (this.jumpKey === key) ? null : key`, re-renders list badges + consequence status line + footer without altering `markedKeys` or `verdicts`. Does **not** set `this.escArmed`.
   - **Keyboard (`handleKeydown`):**
     - Guard: `!event.isComposing`, `event.ctrlKey && !event.metaKey && !event.altKey && !event.shiftKey && String(event.key || "").toLowerCase() === "j"`.
     - If `this.reasonEditKey != null`: return / ignore while typing Cancel reason.
     - Always call `event.preventDefault(); event.stopPropagation();` so macOS/Chromium `<input>` defaults never capture `Ctrl+J`.
     - Target row: highlighted `this.visibleItems[this.selectedIndex]` (require `allowJump && item && item.selectable`).
   - **Apply Selection (`applySelection`):**
     - Highlight fallback rule: ONLY fall back to highlighted row when `markedKeys.size === 0 && !successorModalHasVerdicts(this) && !this.jumpKey`.
     - Settle with `{ picks, closes, ...(this.jumpKey ? { jumpKey: this.jumpKey } : {}) }`.
   - **Picker API (`createSuccessorPickerApi`):**
     - Bump to `version: 5` (backward-compatible additive fields).
     - Accept settlement whenever `picks.length > 0 || closes.length > 0 || Boolean(result.jumpKey)`! Return `{ picks, closes, ...(result.jumpKey ? { jumpKey: result.jumpKey } : {}) }` instead of coercing empty `picks + closes` to `null`.
     - Ensure `Esc` / `Ctrl+[` still resolves `null` (and discards `this.jumpKey`).
2. **`bob-navigation-hotkeys/src/480-review-jump-and-nav-api.js`:**
   - Expose a clean navigation method on `createDependencyNavApi` (e.g., `focusTaskTarget(target)` alongside existing `reviewWalk`/`notice`):
     - Resolves `TFile` from `target.path`.
     - If `target.parkWalk && target.reviewOrigin`, calls `plugin.parkReviewWalkAfterMove(target.reviewOrigin, target.handledRefs)` **before** opening the destination file so `trackOpenedFile` does not corrupt review walk state.
     - Captures `vimJumpContext` (`captureGoToTaskJumpContext`) before switching files so `<C-o>` hops straight back to the closed predecessor task!
     - Calls `plugin.focusTaskAnchor(file, { line: target.line, text: target.text, blockId: target.blockId }, { vimJumpContext, ensureEditing: true })`, then invokes `plugin.flashBobOpenNotesLandingLine(editor, resolvedLine)` to pulse `.bob-landing-flash` on the focused line.
3. **`bob-navigation-hotkeys/src/122-project-promotion-successors.js` & `667-plugin-project-promotion.js` + `429a-relation-merge-commit.js`:**
   - In `buildPromotionSuccessorModel`: include `task: { path: row.notePath, line: row.line + 1, text: row.rawLine, status: row.status, blockId: row.blockId }` on each model row, and in `667-plugin-project-promotion.js`, if `result.jumpKey` is present, resolve its post-write line in `projectContent` (since promotion edits project content / mints block IDs) and call `this.focusTaskAnchor` + `this.flashBobOpenNotesLandingLine`.
   - In `429a-relation-merge-commit.js`: call `pickSuccessorOffers(model, { retarget: false, allowJump: false })` so Relation Merge does not show `Ctrl+J`.
4. **`task-status-cycler` (`135`, `136`, `137`, `139`, `140`, `160`):**
   - In `137-plugin-successor-project.js` (`planAndApplySuccessorsNow`):
     - Accept `jumpKey` from `pickSuccessorOfferChoices` (even when `selectedKeys` and `closeChoices` are both empty!).
     - Note subtle guard in `planAndApplySuccessorsNow` / `139-plugin-successor-parked.js`: ensure early-return checks when `picks.length === 0 && closes.length === 0` do **not** bail out before handling `jumpKey`!
     - Record `jumpKey` target snapshot before edits (`offer.notePath`, `offer.line`, `offer.blockId`, `offer.rawLine`), then **after** `applySuccessorNoteEdits`, `applySuccessorDailyInsertions`, `applySuccessorOfferCloseChoices`, and `rememberSuccessorPass` finish:
       - Read the authoritative final text for `targetPath` (via open editor buffer or vault read / post-write `noteTexts`).
       - Locate the final line using **`blockId` -> post-write updated `rawLine` (e.g. `[x]` or `[-]` line returned by `applySuccessorOfferCloseChoices` / minted ID line returned by `applySuccessorNoteEdits`) -> fallback line**, resolving via `resolveTaskMoveDestinationLine`-style matching.
       - Return `jumpTarget: { path, line, blockId, text, status }` on the successor pass result (plus concise notice text reflecting the jump!).
   - In `140-plugin-vim.js` / `160-plugin-completion.js` (`finalizeClosedTasks`):
     - When `jumpTarget` is returned:
       - If invoked inside a `reviewOrigin` walk landing (`Ctrl+Enter` on `]s`), instruct `navApi.focusTaskTarget` to **park the walk** (`parkReviewWalkAfterMove`) and **skip `advanceReviewWalkAfterAnswer`** in `settleReviewOrigin`!
       - Show ONE merged notice (`"Left open · ↗ Focused “…”"` or `"Pulled 1 into Lunch · ↗ Focused “…”"`), suppress conflicting walk notices, and focus + `.bob-landing-flash` the target line!

---

## 6. Visual & Interaction Design ("Intuitive, Reliable, and Beautiful")

### 6.1 Coexistence Matrix Across All 4 Per-Offer States

Because `<ctrl+j>` is orthogonal to *Leave / Pull In / Done / Cancel*, the row layout must keep **task-state iconography** on the left and **jump destination indicator** on the right/trailing slot so no two badges fight visually:

| Row State + Jump | Left Glyph | Destination / Verdict Pill | Jump Indicator | Row Border / Surface |
| :--- | :--- | :--- | :--- | :--- |
| **Leave Open + Jump** | `□` (unlinked) | *(none / muted reason)* | `↗ Jump` (accent capsule) | Subtle 2px accent left bar + faint accent tint |
| **Pull In + Jump** | `☑` (checked) | `→ Lunch` (green capsule) | `↗ Jump` (accent capsule) | Green check + accent jump capsule + 2px left rail |
| **Done + Jump** | `✓` | `Done` (emerald pill) | `↗ Jump` (accent capsule) | Subtle dim text + crisp accent jump capsule |
| **Cancel + Jump** | `⊘` | `Cancel` (crimson pill + optional reason) | `↗ Jump` (accent capsule) | Crimson verdict + crisp accent jump capsule |

### 6.2 Platform-Native Execution Details

- **Obsidian (`206d-successor-picker-verdict-render.js` + `styles.css`):**
  - Iconography: Lucide `arrow-up-right` inside `<span class="bob-successor-jump-badge">` (`↗ Jump`) placed before or beside the row's destination pill, plus an unobtrusive hover-revealed button (`data-action="jump"`, title `"Jump after closing (Ctrl+J)"`) inside `.bob-successor-verdict-actions` (next to `✓` and `⊘`, always highlighted when active).
  - Color tokens: Drive `--interactive-accent` + `color-mix(in srgb, var(--interactive-accent) 14%, transparent)` (reusing the exact theme-adaptive approach of `.cm-line.bob-landing-flash`), cleanly harmonizing with light and dark Obsidian themes.
  - Micro-detail: Changing `jumpKey` from Row A to Row B immediately updates without scrolling or resetting filter text; toggling off removes the accent rail smoothly.
- **Bob Mac Capture (`CapturePullInChoiceView.swift`):**
  - Badge: Compact SwiftUI `Label("Jump", systemImage: "arrow.up.forward")` (or `↗ Jump` pill matching `CapturePullInChoiceFooter`'s existing `arrow.up.forward` metaphor) tinted with `.accentColor` + subtle accent capsule fill and a 2pt leading `.accentColor` bar on the jumped row.
  - Pointer parity: Context menu / hover quick-action pill (`"Jump After  ⌃J"`) matching existing row actions so mouse and keyboard remain equally discoverable.
- **Footer Hints & Self-Documenting Commit Button:**
  - **Footer keycaps:** Add `Ctrl+J` `jump` (Obsidian) / `⌃J Jump` (Mac Capture).
  - **Consequence strip above footer:**
    - When `jumpKey != nil` and **hidden by active filter**: `"↗ Jump to “<task>” (hidden by filter) · Enter keeps jump"` — prevents accidental jumps if the user typed a search filter and forgot Row A was marked!
    - When `jumpKey != nil` and `openAfterCapture` was armed (`Cmd+Return`): `"↗ Jump overrides Cmd+Return · will focus “<task>”"`.
  - **Dynamic Primary Button Label (Mac Capture):**
    - `0` marks, `0` verdicts, `jumpKey != nil`: **`Leave Open & Jump ↩`** (with lit `arrow.up.forward`)
    - `1+` marks or verdicts, `jumpKey != nil`: **`Pull In 1 & Jump ↩`** / **`Apply & Jump ↩`** (with lit `arrow.up.forward`, even if `openAfterCapture` was `false`).
    - When `marks.isEmpty && verdicts.isEmpty && jumpKey != nil`, hide or grey/clarify `Skip ⇧↩` vs `Leave Open & Jump ↩` (`Shift+Return` remains *"Skip (no pull-in, no jump)"*, giving users an instant one-key abort of their jump mark too!).
- **Accessibility & Post-Jump Wayfinding:**
  - Append `", jump target"` to row `aria-label` (Obsidian) and VoiceOver `accessibilityLabel` (Mac Capture).
  - Announce state toggles live (`"Jump set to <task>"` / `"Jump cleared"`).
  - On landing in Obsidian, fire `.bob-landing-flash` (`1200ms` fade, or `600ms` static wash when reduced motion is active) on the exact task line and position cursor cleanly in edit mode (`ensureEditing: true`).

---

## 7. Implementation & Verification Plan

### 7.1 Recommended Rollout Order

1. **Step 1 — `bob-cli` (`bob capture -j / --jump-offer`):**
   - Implement flag parsing (`cli.rs`), probe-key resolution across `Leave / Pull In / Done / Cancel` (`pull_in.rs`, `offer_verdicts.rs`), and post-write `open_notes` override (`open_notes.rs`).
   - Can ship independently and be verified purely through CLI unit + integration tests before UI changes land.
2. **Step 2 — `bob-plugins` (`bob-navigation-hotkeys` + `task-status-cycler`):**
   - Upgrade `SuccessorOfferPickerModal` + `createSuccessorPickerApi` (`v5`), add `navApi.focusTaskTarget` (`focusTaskAnchor` + `flashBobOpenNotesLandingLine` + `parkReviewWalkAfterMove`), wire post-write target resolution in `task-status-cycler` (`135`–`140`, `160`), enrich `project-promotion` (`122`/`667`), and opt out `relation-merge` (`429a`).
3. **Step 3 — `bob-mac-capture` (with versioned Bob feature check or synchronized Bob release):**
   - Add `jumpKey` on `CapturePullInOutcomes`, update `CapturePullInChoiceState` commit rules & dynamic footer, wire `Ctrl+J` in `CaptureKeyCommandRouter`, send `--jump-offer` through `BobProcessClient` / `CapturePanelModel` (including `InboxRouteSubmitContext` and `reopenPullInChoiceAfter*`), and cover with Swift unit & UI tests.

### 7.2 High-Value Test Matrix

| Layer | Essential Test Cases to Include |
| :--- | :--- |
| **`bob-cli` (Rust tests)** | 1. `-p none -j 1` (Leave Open + Jump): zero Today links written; `open_notes` has 1 item at post-write line + `ref` + `block_id`.<br>2. `-p 1 -j 1` (Pull In + Jump) on task with `needs_block_id`: newly minted `^id` reflected in `open_notes.block_id` and `ref`.<br>3. `-x 1 -j 1` and `-X 1=reason -j 1`: Done/Cancel write succeeds AND `open_notes` resolves updated `[x]` / `[-]` line.<br>4. `-j` + `--inbox-route` relocation: `open_notes.path` and `line` follow the moved task to its destination note.<br>5. Stale `-j` key refuses without mutating vault and emits structured `offers[]`. |
| **`bob-plugins` (Node + Obsidian CDP E2E)** | 1. Modal `Ctrl+J` toggles on/off, moves single-slot cleanly on another row, works while filter focused, does NOT fire inside `reasonEditKey`, prevents highlight-fallback, and returns `{ picks: [], closes: [], jumpKey }` (while `Esc` returns `null` without 2-step arm when no verdicts exist).<br>2. All 4 states (`Leave`, `Pull In`, `Done`, `Cancel`) resolve exact post-write lines even when sibling edits shift lines above the target.<br>3. On a `]s` review walk landing, jumping parks the walk (`parkReviewWalkAfterMove`), skips `advanceReviewWalkAfterAnswer`, leaves `<C-o>` jump history pointing back to the closed task, and fires `.bob-landing-flash`.<br>4. Project promotion picker supports `Ctrl+J`; Relation Merge picker disables it. |
| **`bob-mac-capture` (Swift + UI tests)** | 1. `CaptureKeyCommandRouter` maps `Ctrl+J` -> `.togglePullInJump` when Pull-In visible (even if filter focused), ignores when `pullInReasonFocused` or `Shift`/`Cmd`/`Opt` held, keeps main-editor `Ctrl+J` unchanged.<br>2. Draft `Cmd+Return` + `Ctrl+J` overrides `open_notes` with the jump target; plain `Return` + `Ctrl+J` still triggers Obsidian open; `Return` with `0` marks + `jumpKey` commits `.none` without pulling highlighted row.<br>3. `jumpKey` survives `refresh(offers:)` after offer refusal if present, drops cleanly if gone, and flows through `InboxRouteChoice` context + `NotificationService` `openPlan`. |
