# Task Relation Equals Alias and Direction Toggle Design

## Executive Summary

This report investigates improvements to task relation handling (`~foo:bar` / `~~foo:bar`) in `bob-mac-capture` and `bob-cli`, specifically focusing on:
1. Retiring the fragile `-` alias for `~` and making `=` the sole alias for opening the Links To relation picker.
2. Enabling typing `~` or `=` immediately after a relation link (`~foo:bar` / `~~foo:bar`) to toggle its direction between Links To (`~`) and Linked From (`~~`).
3. Providing an escape mechanism where typing `==` quickly escapes the alias to insert a literal `=` and cancel picker invocation.
4. Enabling typing `~` or `=` in the Task Relation Label Panel to toggle relation direction in place without abandoning the label query or restarting capture.

We evaluate the UX implications, critique the requirements, identify edge cases (notably multi-relation capture and Obsidian highlight collisions), specify the architecture across `bob-cli` (rewrite engine) and `bob-mac-capture` (UI event routing and state management), and provide a concrete implementation plan.

---

## 1. Context and Current Architecture

### 1.1 Bob Task Relations Syntax
Bob captures task relationships using directional tilde prefixes:
- `~note:id`: **Links To** (`relation_to`). The draft task links to `note:id`.
- `~~note:id`: **Linked From** (`relation_from`). `note:id` links to the draft task.
- `~note:id|label`: Annotated relation with a canonical label from the relation catalog.
- `~note:id||label`: One-off relation label (hidden from future suggestions).

In the capture editor, relation pickers are triggered when a relation sigil is typed after whitespace in an eligible task position.

### 1.2 Recent Commits and Existing Limitations
Two recent commits introduced keyboard shortcuts for relations:
1. **Commit `591e4ed` (Mac) / `060d97ed` (CLI) — Relation Dash Aliases**:
   - Aimed to avoid holding `Shift` for `~` by allowing unshifted `-` after whitespace to expand to `~` (`expand_relation_dash_alias`).
   - **Problem**: In prose, `-` is heavily overloaded (hyphenated compounds, spaced hyphens/en-dashes `foo - bar`, subtraction/math `x - y`, bullet sub-items, CLI flags `--flag`).
   - To counteract accidental triggers, `CaptureRelationDashArm` was added so that `Space`, `-`, or `Escape` on an empty filter restores `- `, `--`, or `-`. This causes UI flashing, unnecessary subprocess IPC to `bob capture-rewrite`, and typing friction.
2. **Commit `3ba25d6` (Mac) / `7c71241f` (CLI) — Relation Direction Flip with `=`**:
   - Enabled typing `=` anywhere in an open relation picker filter to toggle direction between `~` (Links To) and `~~` (Linked From).
   - In rewrite, enabled `~=` and `-=` to rewrite to `~~` (`expand_relation_flip_alias`).
   - **Problem**: Typing `=` alone in task prose does *not* alias `~` yet. Furthermore, `=` does not toggle completed relation links, and the relation label panel does not handle `=` or `~` to toggle direction.

---

## 2. Critique and Detailed Analysis of Requirements

### 2.1 Requirement 1: Make `=` the Sole Alias for `~` (Retiring `-`)

#### The Proposal
Retire `-` as an alias for `~` and instead treat `=` typed after whitespace in a task body as the sole alias that expands to `~` (opening the Links To picker).

#### Grammar Audit: Is `=` Ever Used in the Same Context?
We audited `docs/capture.md` and the grammar in `src/native/capture_language/` for all occurrences of `=`:
1. **Pomodoro Session Operations**:
   - `=bugs`, `=/`, `=*`, `=3`, `=-2`, `=`: Line/item-initial or bullet-initial tokens.
2. **Glued Task Links**:
   - `^task=`, `@task=bugs`, `^task=x`: Glued directly to the task identifier with no preceding whitespace.
3. **Past Pomodoro Segments**:
   - `x=3!`, `x=~2`: Must start with `x=`.
4. **Mid-Body Tokens**:
   - `docs/capture.md` explicitly notes: *"mid-body tokens (`Plan =bugs` stays prose...)"*. A standalone `=` preceded by whitespace in a task body is **never** valid Bob capture syntax.

#### Critique & Assessment
- **Verdict**: **Strongly Recommended.**
- Replacing `-` with `=` is a substantial ergonomic improvement. Both `-` and `=` are unshifted keys adjacent to each other on standard US keyboards, but `=` appears orders of magnitude less frequently in task prose than `-`.
- Retiring `-` eliminates false-positive relation triggers on spaced hyphens, ranges, and flags, allowing the removal of the cumbersome `CaptureRelationDashArm` restore logic.

---

### 2.2 Requirement 2: Type `~` or `=` After `~foo:bar` to Toggle Direction

#### The Proposal
Typing `~` or `=` after an existing `~foo:bar` style link should automatically transform it into `~~foo:bar`, and conversely typing `~` or `=` after `~~foo:bar` should transform it into `~foo:bar`.

#### Precedent: `switch_block_id_separator`
In `bob-cli` (`src/native/capture_language/rewrite.rs`), Bob already implements a similar toggle mechanism:
> *"Block-ID separator toggle: typing `^` immediately after a completed `@file:id` toggles the separator to `@file^id`, or typing `:` after `@file^id` toggles to `@file:id`."*

The trigger key (`^` or `:`) is typed at the end of the identifier, consumed by the rewrite engine, and the leading separator is swapped in place while keeping the caret at the end of the identifier.

#### Critical Design Consideration: Glued vs. Spaced Suffix
What happens if there is whitespace after `~foo:bar`?
- **Glued (`~foo:bar=` or `~foo:bar~`)**:
  - Unambiguous. Block IDs and note stems never end with `=` or `~`.
  - The rewrite engine can safely match a completed relation token ending at `cursor - 1` with trigger `=` or `~`.
- **Spaced (`~foo:bar =` or `~foo:bar ~`)**:
  - **Conflict with Multiple Relations**: A single task can legally have multiple relationships:
    ```markdown
    Refactor auth ~backend:api ~db:schema
    ```
    If `=` after a space was treated as a toggle of the *previous* relation, a user typing `Refactor auth ~backend:api =` would toggle `~backend:api` to `~~backend:api` instead of starting a second relation!
  - **Relation Picker Auto-Space**: When a relation picker row is accepted at the end of a draft, `CapturePanelModel.swift` appends a trailing space:
    ```swift
    insertionText = insertion.hasSuffix(" ") ? insertion : insertion + " "
    ```
    If a user immediately hits `=` after accepting, the buffer contains `~note:id =`.

#### Adjustment & Recommendation
1. **The rewrite rule `switch_relation_direction` MUST be strictly glued**:
   - `~note:id=` and `~note:id~` -> `~~note:id`
   - `~~note:id=` and `~~note:id~` -> `~note:id`
   - Glued labelled relations: `~note:id|label=` -> `~~note:id|label`
2. **To flip a just-accepted relation from the draft editor**:
   - The user presses `Backspace` once to delete the auto-appended space, then presses `=` or `~`.
   - Better yet: Requirement 4 allows toggling direction *directly in the picker or relation label panel before or during label selection*, making editor-level flipping an auxiliary shortcut rather than the primary workflow.

---

### 2.3 Requirement 3: Escaping the `=` Sign with `==` Fast Enough

#### The Proposal
Allow escaping the `=` sign anywhere it is used as an alias for `~` by pressing `==` fast enough.

#### What Text Should Escape Produce?
When someone escapes the alias by double-tapping `=`:
- In `bob-mac-capture`, the established convention for alias escaping is:
  - `\\` escapes the `#` alias to insert a **single** `\`.
  - Bare `/` Go To: a second `\` right after the alias types a **single** `\`.
- If the user types `let x = 10`, they type space, `=`, `=`.
- If `==` resulted in literal `==`, the draft would contain `let x == 10`, requiring a Backspace to remove the extra `=`.
- Therefore, double-tapping `==` fast enough should escape to a **single literal `=`** (`let x = `) and close/dismiss any relation completion or picker.
- If the user genuinely wants `==` (e.g. an equality operator `x == y` or an Obsidian highlight `==text==`), typing a third `=` (`===`) immediately appends the second `=`, yielding `==`.

#### Dual-Race Architecture
Subprocess calls to `bob capture-rewrite` are asynchronous. When a user double-taps `==`, two timing cases must be handled:
1. **Case A (Fast double-tap before Bob answers)**:
   - Keystroke 1 (`=`): `CapturePanelController` records a pending rewrite intent.
   - Keystroke 2 (`=`): Arrives before Bob's JSON response for Keystroke 1.
   - `CaptureKeyCommandRouter` recognizes the pending alias and records an `EqualsAliasProbe`.
   - When Bob's response arrives proposing `~`, the probe suppresses the rewrite, replaces the draft with a single literal `=`, and dismisses completion.
2. **Case B (Second tap after Bob answers)**:
   - Keystroke 1 (`=`): Bob's response arrives and rewrites `=` to `~`, opening the Links To picker.
   - Keystroke 2 (`=`): Arrives while the relation picker is open.
   - Normally, in the relation picker, `=` is routed as `.flipRelationDirection`.
   - However, if the picker was just opened by the `=` alias and has an empty filter, an armed `equalsAliasLiteralArm` intercepts the `=` key, restores the literal `=`, closes the picker, and focuses the editor!

---

### 2.4 Requirement 4: Direction Toggle in the Task Relation Label Panel

#### The Proposal
When `~` or `=` is pressed in the Task Relation Label Panel, toggle between "link to" and "linked from".

#### User Problem
When picking a relation label (e.g. "blocks", "child of", "depends on"), the user is presented with the relation sentence:
- Links To: `“This task” [blocks] “Target task”`
- Linked From: `“Target task” [blocks] “This task”`

Users frequently realize at this moment that the relationship was created in reverse. Currently, fixing this requires:
1. Escaping out of the label card.
2. Deleting the relation token in the draft.
3. Re-triggering the relation picker with `~~`.
4. Re-searching and re-selecting the target task.
5. Re-opening the label card with Shift-Return.

#### Mechanics of the Toggle
In `CaptureRelationLabelPromptState`:
- `direction`: `DependencyPickerDirection` (`.linksTo` vs `.linkedFrom`).
- `tokenRange`: CaptureRange covering `~target` or `~~target`.
- `labelRange`: CaptureRange covering the trailing label.
- `draftSnapshot`: The current draft text containing `~target`.

When `~` or `=` is pressed:
1. `direction` flips between `.linksTo` and `.linkedFrom`.
2. In `plainDraft` and `prompt.draftSnapshot`:
   - If flipping `.linksTo` -> `.linkedFrom`: insert `~` at `tokenRange.start` (turning `~` into `~~`). All subsequent byte offsets shift by `+1`.
   - If flipping `.linkedFrom` -> `.linksTo`: remove one `~` at `tokenRange.start` (turning `~~` into `~`). All subsequent byte offsets shift by `-1`.
3. The live sentence preview (`relationLabelSentenceSource` and `relationLabelSentenceTarget`) instantly flips the subject and object in the UI.
4. The label query input and focus remain completely undisturbed. (Note: `~` is already in `FORBIDDEN_CHARS` for relation labels in Bob, so intercepting `~` never conflicts with valid label typing).
5. If rename mode is active (`prompt.rename != nil`), the key is passed through to native editing and does *not* flip relation direction.

---

## 3. Recommended Architecture & Implementation Plan

### 3.1 Backend: `bob-cli`

#### 1. Update `src/native/capture_language/rewrite.rs`
- **Retire Dash Alias**:
  - Remove `expand_relation_dash_alias` and references to relation dash from `expand_sigil_alias`. (Retain `expand_past_segment_dash_alias` for `x=` tokens where `-` remains valid).
- **Add `=` -> `~` Alias**:
  - In `expand_sigil_alias`, when `alias == "="`:
    - If `start > 0` and previous char is `~` -> expand `~=` to `~~` (existing `expand_relation_flip_alias`).
    - If preceded by whitespace and eligible for `CompletionContext::RelationTo` -> expand `=` to `~` (new `expand_relation_equals_alias`).
- **Add Glued Direction Toggle Rule (`switch_relation_direction`)**:
  - When `alias == "="` or `alias == "~"`:
    - Tokenize draft and inspect token ending at `cursor`.
    - If token ends in `~` or `=` and preceding portion is a valid `RelationTo` or `RelationFrom` token (`~note:id` or `~~note:id`, with or without `|label`):
      - If prefix was `~`, replace prefix with `~~` and strip trailing trigger.
      - If prefix was `~~`, replace prefix with `~` and strip trailing trigger.
      - Cursor lands at the end of the relation target / label.
      - Rule name: `switch_relation_direction`.

#### 2. Documentation and Test Updates
- Update `docs/capture.md` and `docs/reference/cli/capture-rewrite.md`.
- Add unit tests in `src/native/capture_language/rewrite.rs` and CLI integration tests in `tests/cli/capture/rewrite.rs`.

---

### 3.2 Frontend: `bob-mac-capture`

#### 1. Key Routing in `CaptureKeyCommandRouter.swift`
- Remove `relationDashRestoreCommand` and `.restoreRelationDashLiteral`.
- In `relationLabelPromptCommand`:
  ```swift
  if event.characters == "~" || event.characters == "=",
     modifiers.intersection([.command, .option, .control]).isEmpty,
     !renameActive
  {
      if event.isARepeat || context.keyIsRepeat {
          return .consumeKey
      }
      return .flipRelationLabelPromptDirection
  }
  ```
- In `pickerCommand`:
  - Retain `event.characters == "~" || event.characters == "="` -> `.flipRelationDirection`.
  - Add armed escape check for `=`: if `context.equalsAliasLiteralArmed`, return `.typeLiteralForEqualsAlias`.

#### 2. Model & State in `CapturePanelModel.swift`
- **Retire Dash Restore Arm**:
  - Delete `relationDashLiteralArm`, `takeRelationDashLiteralArm()`, and `restoreRelationDashLiteral()`.
- **Add Equals Alias Escape Arm**:
  - Add `equalsAliasLiteralArm: CaptureEqualsAliasArm?`.
  - When Bob rewrites `=` to `~`, arm `equalsAliasLiteralArm`.
  - If a second `=` is pressed while armed, `replaceEqualsAliasWithLiteralKey()` replaces `~` with `=`, closes the picker, and focuses the editor.
- **Implement `flipRelationLabelPromptDirection()`**:
  ```swift
  func flipRelationLabelPromptDirection() {
      guard var prompt = relationLabelPrompt,
            !prompt.isSaving,
            prompt.rename == nil
      else { return }
      
      let wasLinkedFrom = prompt.direction == .linkedFrom
      let newDirection: DependencyPickerDirection = wasLinkedFrom ? .linksTo : .linkedFrom
      let tokenStart = prompt.tokenRange.start
      
      var draft = prompt.draftSnapshot
      guard let startIdx = stringRange(in: draft, start: tokenStart, end: tokenStart + 1) else { return }
      
      let delta: Int
      if wasLinkedFrom {
          // Remove one tilde: ~~ -> ~
          draft.removeSubrange(startIdx)
          delta = -1
      } else {
          // Insert one tilde: ~ -> ~~
          draft.insert("~", at: startIdx.lowerBound)
          delta = 1
      }
      
      let newTokenRange = CaptureRange(start: prompt.tokenRange.start, end: prompt.tokenRange.end + delta)
      let newLabelRange = CaptureRange(start: prompt.labelRange.start + delta, end: prompt.labelRange.end + delta)
      let newRestoreCursor = prompt.restoreCursor + delta
      
      prompt.direction = newDirection
      prompt.draftSnapshot = draft
      prompt.tokenRange = newTokenRange
      prompt.labelRange = newLabelRange
      prompt.restoreCursor = newRestoreCursor
      if var returnPicker = prompt.returnPicker {
          returnPicker.source = wasLinkedFrom ? .linksTo : .linkedFrom
          returnPicker.draftSnapshot = draft
          prompt.returnPicker = returnPicker
      }
      
      relationLabelPrompt = prompt
      setPlainDraft(draft, cursorUTF8Offset: newRestoreCursor, suppressSelectionCallbacks: true)
  }
  ```

#### 3. Controller in `CapturePanelController.swift`
- In `noteSeparatorToggleIntentIfEligible`:
  - Remove `-` from eligible trigger characters.
  - Allow `=` when preceded by whitespace, preceded by `~`, or preceded by a relation token.
  - Allow `~` when preceded by a relation token.
- Route `.flipRelationLabelPromptDirection` to `model.flipRelationLabelPromptDirection()`.

---

## 4. Summary Table of Gestures and Behaviors

| Context | Typed Gesture | Resulting Action | Draft Result |
| :--- | :--- | :--- | :--- |
| Task body prose | `foo =` | Expands `=` to `~`, opens Links To picker | `foo ~` |
| Task body prose | `foo ==` (fast) | Escapes alias, cancels picker | `foo =` |
| Open relation picker | `~` or `=` | Flips direction Links To ↔ Linked From in place | `~` ↔ `~~` |
| Relation label panel | `~` or `=` | Flips direction in place, live-updates sentence | `~note:id` ↔ `~~note:id` |
| Editor draft | `~note:id=` | Rewrites relation to Linked From | `~~note:id` |
| Editor draft | `~~note:id=` | Rewrites relation to Links To | `~note:id` |
| Editor draft | `~note:id~` | Rewrites relation to Linked From | `~~note:id` |
| Editor draft | `~~note:id~` | Rewrites relation to Links To | `~note:id` |

---

## 5. Conclusion

The proposed improvements create a uniform, cohesive relation management workflow:
1. `=` becomes the single, unshifted relation alias across all capture modes.
2. Fragile dash restores and accidental hyphen triggers are completely eliminated.
3. Relations can be toggled symmetrically at every stage of capture:
   - *Before picking*: typing `=` in prose (`=`) or after `~` (`~=`).
   - *While picking*: typing `=` or `~` in the relation picker.
   - *While labelling*: typing `=` or `~` in the relation label panel.
   - *After capture in editor*: typing glued `=` or `~` after `~note:id`.
4. Escape via fast `==` ensures zero interference with programming assignments, math expressions, or Obsidian highlight syntax.
