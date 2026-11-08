# Research Report: Ergonomic Shorthand Expansion for Pomodoro Close (`x` → `!` and `s` → `*`)

**Researcher:** `gem` (Independent Swarm Evaluation)  
**Date:** 2026-11-08  
**Repository Focus:** `bob-cli` & `bob-mac-capture`  
**Classification:** Capture Grammar, Editor Rewrite Assists, Ergonomics, Thin-Client Architecture  

---

## 1. Executive Summary

This research investigates a proposal to introduce two new editor shorthand characters in `bob-mac-capture` and `bob-cli`:
1. **`x`** auto-replaced with **`!`** (Complete All / Complete List).
2. **`s`** auto-replaced with **`*`** (Park All / Park List).

These replacements are proposed for two primary contexts:
- **Bare Close syntax (`x` syntax)**: Typing `xx` at the start of a close item rewrites to `x!`; typing `xs` rewrites to `x*`.
- **Past Pomodoro Close syntax (`x=` syntax)**: Typing `s` or `x` after the second `=` (for example, typing `x=1=s`) rewrites to `*` or `!` respectively (for example, resulting in `x=1=*`).

### Key Conclusions
1. **Strongly Recommended**: The proposal addresses a major physical keyboard ergonomic pain point. On a standard QWERTY keyboard, `!` (`Shift + 1`) and `*` (`Shift + 8`) require awkward finger reaches and Shift-key chords. In contrast, `x` and `s` are unshifted home-row / lower-row keys directly under the left hand. Because Pomodoro close operations occur multiple times daily, replacing these chorded punctuation characters with rapid left-hand keystrokes (`xx` double-tap, `xs` home-row roll) yields significant speed and comfort gains.
2. **Critical Disambiguation ("Instead of the second `=`")**: The user prompt contains a slight textual tension: it mentions replacing characters *"when used instead of the second `=` that is supported by the `x=` capture syntax"*, but then provides the concrete example *"typing `x=1=s` should result in `x=1=*`"* (which explicitly retains the second `=`). We demonstrate that the second `=` **must remain required** (`x=1=s` → `x=1=*`), and `s` is replacing `*`, not the `=`. Allowing `x=1s` without the second `=` would introduce severe collisions with Pomodoro theme names (e.g., `x=1s` is a 1-block session with theme `S`, and typing `x=1study` or `x=1sase` would be hijacked).
3. **Architectural Placement (Thin-Client Compliance)**: Under **Decision 10 (`mac-capture-is-a-thin-client`)**, the rewrite rules must be implemented canonically in `bob-cli` under `bob capture-rewrite` (`src/native/capture_language/rewrite.rs`), exactly like existing sigil aliases (`,`, `.`, `;`, `=`, `-`, `/`, `\`). `bob-mac-capture` must remain a thin client that routes the keystroke intent, calls `capture-rewrite`, and applies the single-point native edit.
4. **Typing Performance Guard**: Unlike punctuation (`.`, `,`, `;`), `s` is the 7th most frequent letter in the English language (~6.3% of all characters). `bob-mac-capture` must contextually gate recording of `s` and `x` rewrite intents so that ordinary prose typing in task titles does not trigger unnecessary rewrite subprocess calls.
5. **Immediate Submit Protection**: Rapid gestures like `xx<Return>` or `xs<Return>` occur within milliseconds. `bob-mac-capture` must ensure that hitting Return immediately after typing a close shorthand awaits the in-flight rewrite before submitting (extending the existing `deferSubmitForPastSegmentDash` pattern).

---

## 2. Background & Grammar Overview

### 2.1 The Pomodoro Close Grammar (`x` syntax)

In `bob-cli`, a draft or item beginning with a bare `x` is parsed as a Pomodoro Close operation (`EditorMode::PomodoroClose`). The close specification format is:
```text
x[<in_progress>][*<park>][!<complete>][~<drop>][@<delegate>]
```
Where:
- **Bare `x`**: Closes the active Pomodoro with default behavior (parks tasks).
- **`x!`**: Closes the Pomodoro and explicitly marks **all** linked tasks as completed (`complete_all: true`).
- **`x*`**: Closes the Pomodoro and explicitly marks **all** linked tasks as parked (`park_all: true`).
- **`x1`**: Keeps task index `1` in progress (`in_progress: [1]`).
- **`x1!`**: Keeps task index `1` in progress and marks all other tasks completed (`in_progress: [1], complete_all: true`).
- **`x1*`**: Keeps task index `1` in progress and parks all other tasks (`in_progress: [1], park_all: true`).
- **`x*2`**: Parks task index `2`.
- **`x!1,2`**: Completes task indices `1` and `2`.

In daily operation, `x!` (Complete All) and `x*` (Park All) are by far the most frequent close invocations Bryan types at the conclusion of a Pomodoro session.

### 2.2 The Past Pomodoro Grammar (`x=` syntax)

The `x=` capture syntax records a past Pomodoro session directly into the daily note ledger (`EditorMode::PomodoroPast`). Its lexical structure (`src/native/capture_language/past.rs`) consists of:
```text
x=[<E>][!][=<close_spec>]
```
- **`E` (Elapsed & Theme)**: Can specify elapsed blocks (e.g., `x=1` for 5 minutes, `x=3` for 15 minutes, default 5 blocks = 25 minutes) and/or an optional theme name (e.g., `x=fix3`, `x=3fix`, `x=1s`, `x=#deep-work`).
- **Repair `!`**: A `!` appearing *before* the second `=` (or at the end of `E` when no second `=` exists) designates a **repair session** (an unscheduled interruption or maintenance session), setting `spec.repair = true`. It does *not* mean "complete all".
- **The Second `=`**: Unambiguously terminates the `E` (elapsed / theme) section and introduces the close specification (`close_spec`).
- **`<close_spec>`**: Reuses the exact same close list grammar as bare `x`:
  - `x=1=*`: 1 block, park all tasks (`park_all: true`).
  - `x=1=!`: 1 block, complete all tasks (`complete_all: true`).
  - `x=1=*2`: 1 block, park task 2.
  - `x=1=!2`: 1 block, complete task 2.
  - `x=fix3!=*3`: 3 blocks, theme FIX, repair mode, park task 3.

Crucially, in Bob's past grammar, close lists are forbidden before the second `=`. Bob provides explicit teaching errors:
- *"to park {tasks}, put it after a second `=`: `{raw_token}` never parks, write `{rewrite}`"*
- *"write the task selection after a second `=`: `{raw_token}` selects tasks, write `{rewrite}`"*

### 2.3 Existing Sigil Aliases in Bob

Bob already supports an extensive suite of editor-time sigil aliases in `bob capture-rewrite` (`src/native/capture_language/rewrite.rs`). These aliases allow typing comfortable unshifted characters instead of chorded punctuation:
- **`.` → `^`**: Immediately following `@route`, aliases to `^` to open the Block ID picker (avoids `Shift + 6`).
- **`;` → `:`**: Immediately following `@route`, aliases to `:` to open the Pomodoro Block ID picker (avoids `Shift + ;`).
- **`,` → `+`**: After `@route`, aliases to `+` to open the Parent Task picker (avoids `Shift + =`).
- **`-` → `~`**: Inside `x=` past pomodoro tokens (e.g., `x=2-` → `x=2~`), aliases to `~` to open the segment selector (avoids `Shift + \``).
- **`=` → `~`**: After whitespace, aliases to `~` to open the Links To picker; typing `==` quickly undos the gesture and types a literal `=`.
- **`\` or `/` → `#`**: Wherever completion would open a `#` menu (task type, section, drawer, pomodoro name), aliases to `#` (avoids `Shift + 3`).

In every case, the alias is:
1. Evaluated by `bob capture-rewrite` with the exact caret offset `--cursor`.
2. Validated against the contextual grammar (it stays literal in prose or where the target sigil is illegal).
3. Applied cleanly in `bob-mac-capture` as a single-point native `NSTextView` edit.

---

## 3. Critique of the Proposed Plan

### 3.1 Ergonomic Evaluation (Is This a Good Idea?)

**Verdict: Yes, it is an outstanding idea.**

1. **Elimination of Awkward Shift Chords**:
   - `!` requires `Shift + 1`. This forces the left pinky onto Shift and a stretch of the left ring or middle finger to `1`.
   - `*` requires `Shift + 8`. This is a two-handed chord (left Shift + right middle finger on `8`), interrupting typing cadence.
   - In contrast, `x` and `s` are single unshifted keys located on the left hand home row (`s`) and lower row (`x`).
2. **Double-Tap and Rolling Gestures**:
   - For Complete All: `xx` is a crisp double-tap of the same key. The user opens capture (hotkey), taps `x` twice (`xx`), and presses Return. Total elapsed time: under 200 milliseconds.
   - For Park All: `xs` is a natural rolling motion from bottom row (`x`) to home row (`s`).
   - For Past Sessions: `x=1=s` avoids shifting for `8`. `x=1=x` avoids shifting for `1`.
3. **Consistency with Bob's Design Philosophy**:
   - Bob's capture interface is designed for minimal friction and maximum capture velocity. Just as `-` was introduced to avoid typing `~` in `x=2-`, introducing `x` and `s` avoids `!` and `*` in close lists.

---

### 3.2 Detailed Analysis of the "Instead of the Second `=`" Ambiguity

The user prompt contains an ambiguity that must be addressed with precision:
> *"Similarly, these will be repaced with `!` and `*`, respectively, when used instead of the second `=` that is supported by the `x=` capture syntax. For example, typing `x=1=s` should result in `x=1=*` in contexts where the `x=` capture syntax is supported."*

Notice the conflict:
- **Phrase**: *"used instead of the second `="* (implies typing `x=1s` without the second `=`).
- **Example**: *"typing `x=1=s` should result in `x=1=*`"* (explicitly types the second `=`, with `s` replacing `*`).

#### Why `x=1s` → `x=1=*` (Omitting the Second `=`) Must Be Rejected
If we attempted to rewrite `x=1s` to `x=1=*`:
1. **Severe Collision with Pomodoro Theme Names**:
   In `x=`, any unquoted alphabetic characters following digits in `E` represent a Pomodoro theme name:
   - `x=1s` currently parses validly as: 1 block (5 minutes), theme name `"S"`.
   - `x=3fix` parses as: 3 blocks, theme name `"FIX"`.
   - `x=1study` parses as: 1 block, theme name `"STUDY"`.
   - `x=1sase` parses as: 1 block, theme name `"SASE"`.
   If typing `s` immediately after `x=1` triggered a rewrite to `x=1=*`:
   - Anyone attempting to log a theme starting with `s` (such as `study`, `sase`, `swift`, `sql`, `search`, `security`, `sync`) would have their theme hijacked and replaced with `=*` the moment they pressed `s`.
   - Anyone logging an actual Pomodoro with single-letter theme `S` would be unable to do so.
2. **Grammar Inconsistency with Repair Mode**:
   Before the second `=`, `!` designates repair mode (`x=1!` = 1 block, repair mode, no close spec). If `x=1x` rewrote to `x=1!`, it would create confusion between repair mode and close complete-all.

#### The Correct Resolution: Rewrite *After* the Second `=`
In `x=1=s`:
- The second `=` has already been typed.
- The second `=` strictly terminates the elapsed/theme section and enters the close list.
- In the close list, letters `s` and `x` have **zero legal meaning**; in raw grammar, `x=1=s` produces an `invalid_pomodoro_past` error.
- Therefore, rewriting `x=1=s` → `x=1=*` and `x=1=x` → `x=1=!` has **zero syntactic collisions** and perfectly preserves theme naming.

**Recommendation:** Clarify this requirement explicitly. The implementation must require the second `=` (`x=1=s` → `x=1=*`, `x=1=x` → `x=1=!`), adhering strictly to the user's provided example and Bob's past grammar invariants.

---

### 3.3 Scope Analysis: Where Else in Close Syntax Should `x` and `s` Expand?

We must determine the exact scope of where `x` → `!` and `s` → `*` should operate.

#### Scenario A: Immediately After Close Opener (`xx` and `xs`)
- At start of draft or item:
  - `xx` → `x!` (Complete All)
  - `xs` → `x*` (Park All)
- After the second `=` in past pomodoros:
  - `x=1=s` → `x=1=*` (1 block, Park All)
  - `x=1=x` → `x=1=!` (1 block, Complete All)
  - `x=fix3=s` → `x=fix3=*` (Theme FIX, 3 blocks, Park All)
  - `x=fix3=x` → `x=fix3=!` (Theme FIX, 3 blocks, Complete All)
  - `x=fix3!=s` → `x=fix3!=*` (Theme FIX, repair mode, Park All)
  - `x=fix3!=x` → `x=fix3!=!` (Theme FIX, repair mode, Complete All)
  - `x==s` → `x==*` (Default 5 blocks, Park All)
  - `x==x` → `x==!` (Default 5 blocks, Complete All)

#### Scenario B: After In-Progress Task Numbers (`x1x` and `x1s`)
Suppose Bryan has active tasks in today's Pomodoro and wants to keep task 1 in progress, but complete or park all others:
- Raw grammar:
  - `x1!` = task 1 in progress, complete all others.
  - `x1*` = task 1 in progress, park all others.
- If the user types `x1x`:
  - In a close list, digits represent task indices. A letter `x` immediately following a digit is a syntax error.
  - Rewriting `x1x` → `x1!` and `x1s` → `x1*` is completely unambiguous!
  - Similarly, in past pomodoros: `x=1=1x` → `x=1=1!` and `x=1=1s` → `x=1=1*`.

#### Scenario C: Chaining with Numbers (`xs2` / `xx2` / `x=1=s2`)
- If `xs` immediately expands to `x*`, then typing `2` naturally yields `x*2` (park task 2).
- If `xx` immediately expands to `x!`, then typing `2` naturally yields `x!2` (complete task 2).
- If `x=1=s` expands to `x=1=*`, typing `2` yields `x=1=*2`.
Because the single-character expansion occurs instantaneously upon typing the alias, subsequent numbers naturally attach to the resulting `*` or `!`.

**Recommendation:** Support both Scenario A (bare close / bare past close) and Scenario B (close after in-progress digits). This provides a complete, polished, and unified mental model where `x` always means Complete All and `s` always means Park All within any close specification.

---

### 3.4 Collision Analysis with Regular Prose

Could typing `xx` or `xs` accidentally hijack ordinary prose tasks?

1. **Tasks Starting with `x`**:
   In Bob capture grammar, any draft starting with a bare `x` followed by a space is *already* claimed as a Pomodoro Close with a log message. For example, `x ray results` parses as `mode: "pomodoro_close"` with log text `"ray results"`. Users never write unadorned tasks starting with `x`; they write `#todo x ray` or `- x ray` or `@inbox x ray`.
2. **Tasks Starting with `xx` or `xs`**:
   Words starting with `xx` (e.g., "xxl") or `xs` (e.g., "xsd", "xs size") are exceedingly rare as initial words in actionable GTD tasks. Even if one were typed, standard undo (`Cmd-Z` or Backspace) restores the literal text.
3. **Mid-Draft Prose**:
   In normal tasks (e.g., `Review tax forms`), the word `tax` ends in `x`, and the word `forms` contains `s`.
   - In `Review tax forms`, the cursor when typing `s` in `forms` is preceded by `form`, which is neither a close item nor preceded by `x`. The rewrite rule strictly requires the preceding token to be a close trigger (`x` or `=`), so mid-draft prose is 100% unaffected.

---

## 4. Architectural Analysis & Options

We evaluate three potential architectural approaches for implementing this feature:

### Approach 1: Dual-Tier Architecture (`bob-cli` Canonical Rewrite + `bob-mac-capture` Thin Client Wiring) — **RECOMMENDED**

```
┌────────────────────────────────────────────────────────┐
│                   bob-mac-capture                      │
│                                                        │
│  CapturePanelController.swift                          │
│    - Intercepts key-downs for 'x' and 's'              │
│    - Fast context filter: is draft close-eligible?     │
│    - Calls noteSeparatorToggleIntent                   │
│                                                        │
│  CapturePanelModel.swift                               │
│    - AppKit native key inserts character               │
│    - editorTextDidChange consumes intent               │
│    - Dispatches async processClient.captureRewrite     │
│    - Receives response and applies native single edit  │
│    - Return key deferral guards instant submission     │
└──────────────────────────┬─────────────────────────────┘
                           │ JSON IPC (stdio)
                           ▼
┌────────────────────────────────────────────────────────┐
│                       bob-cli                          │
│                                                        │
│  src/native/capture_language/rewrite.rs                │
│    - expand_sigil_alias handles 'x' and 's'            │
│    - Inspects exact cursor offset and draft grammar    │
│    - Emits TextEdit: 'x' -> '!' or 's' -> '*'          │
│    - Pure, audited, read-only, fully tested in Rust    │
└────────────────────────────────────────────────────────┘
```

#### Why Approach 1 Wins:
1. **Adheres to Decision 10 (`mac-capture-is-a-thin-client`)**: The macOS app never parses capture grammar or invents rewrite rules locally.
2. **Full CLI Parity**: The rewrite is available via `bob capture-rewrite -c <cursor> -f json -- "<draft>"`, making it accessible to tests, scripts, and alternative frontends.
3. **Native Undo & Accessibility**: The rewrite edit is applied via AppKit's `NSTextView.insertText(_:replacementRange:)`, ensuring that `Cmd-Z` seamlessly reverts the character without custom undo stack manipulation.

---

### Approach 2: Client-Side Typing Assist in `bob-mac-capture` Only (REJECTED)

In this approach, `bob-mac-capture` would intercept `x` and `s` in Swift (similar to `CaptureCloseTaskCommaAssist`) and replace the characters immediately without invoking `bob capture-rewrite`.

#### Why Approach 2 Fails:
- **Direct Violation of Decision 10**: Re-implementing lexical close rules in Swift causes grammar drift between Bob and Mac Capture.
- **Breaks `bob capture-rewrite` CLI**: Anyone testing or using the CLI command would not see the aliases expand.
- **Unnecessary Duplication**: Bob already has the full tokenizer, parser, and rewrite infrastructure in Rust.

---

### Approach 3: Modifying Raw Parser Grammar in `bob-cli` (REJECTED)

In this approach, `capture-parse` would be modified to directly accept `xx`, `xs`, and `x=1=s` as valid raw grammar without rewriting the text in the editor.

#### Why Approach 3 Fails:
- **Pollutes Stored Vault Data**: If `xx` or `x=1=s` were stored directly into daily note ledgers, it would introduce multiple competing dialects into canonical Markdown files.
- **No Immediate Visual Feedback**: Rewriting `xx` → `x!` and `xs` → `x*` provides immediate, unambiguous confirmation to the user that Bob recognized the gesture and is preparing the exact close action intended.

---

## 5. Detailed Technical Design (Recommended Solution)

### 5.1 Changes to `bob-cli`

#### 1. File: `src/native/capture_language/rewrite.rs`
Update `expand_sigil_alias` to process `alias == "x"` and `alias == "s"`:

```rust
// Inside expand_sigil_alias(raw_text: &str, cursor: usize) -> Option<DraftRewrite>:
if alias == "x" || alias == "s" {
    return expand_pomodoro_close_alias(raw_text, start, cursor, alias);
}
```

Implement the helper function `expand_pomodoro_close_alias`:
```rust
fn expand_pomodoro_close_alias(
    raw_text: &str,
    start: usize,
    cursor: usize,
    alias: &str,
) -> Option<DraftRewrite> {
    let target_sigil = if alias == "x" { '!' } else { '*' };
    let replacement = target_sigil.to_string();

    // Context 1: Past Pomodoro close part (after second `=`)
    // Look for an x= token containing the second `=` immediately preceding start,
    // or preceding close digits ending at start.
    if let Some(rewrite) = expand_past_close_alias(raw_text, start, cursor, target_sigil, alias) {
        return Some(rewrite);
    }

    // Context 2: Bare x Pomodoro close
    // Case 2A: "xx" or "xs" at start of item/draft
    if let Some(rewrite) = expand_bare_close_alias(raw_text, start, cursor, target_sigil, alias) {
        return Some(rewrite);
    }

    // Case 2B: "x1x" or "x1s" (after in-progress task digits)
    if let Some(rewrite) = expand_close_digits_alias(raw_text, start, cursor, target_sigil, alias) {
        return Some(rewrite);
    }

    None
}
```

Validation criteria inside `expand_past_close_alias`:
- The caret must be within a past pomodoro token (`x=...`).
- The second `=` must be present in the token and strictly precede the alias character.
- The text between the second `=` and the alias character must consist solely of valid close-list digits and commas (e.g., `x=1=` or `x=1=1` or `x=fix3!=`).
- Wikilinks and quoted literals must not claim the span.

Validation criteria inside `expand_bare_close_alias`:
- The item must start with `x`.
- For `xx` / `xs`: `start` must be index `1` relative to the item line start (immediately following `x`).
- For `x<digits>x` / `x<digits>s`: the characters between `x` and `start` must be purely digits and commas (in-progress task list).

#### 2. Tests in `src/native/capture_language/tests/rewrite.rs`
Add comprehensive test coverage:
```rust
#[test]
fn rewrite_draft_expands_close_x_and_s_aliases() {
    let cases = [
        ("xx", "x!", "! for xx"),
        ("xs", "x*", "* for xs"),
        ("x1x", "x1!", "! for x1x"),
        ("x1s", "x1*", "* for x1s"),
        ("x1,2x", "x1,2!", "! for x1,2x"),
        ("x1,2s", "x1,2*", "* for x1,2s"),
        ("x=1=s", "x=1=*", "* for s after x=1="),
        ("x=1=x", "x=1=!", "! for x after x=1="),
        ("x=fix3=s", "x=fix3=*", "* for s after x=fix3="),
        ("x=fix3=x", "x=fix3=!", "! for x after x=fix3="),
        ("x=fix3!=s", "x=fix3!=*", "* for s after x=fix3!="),
        ("x=fix3!=x", "x=fix3!=!", "! for x after x=fix3!="),
        ("x==s", "x==*", "* for s after x=="),
        ("x==x", "x==!", "! for x after x=="),
        ("x=1=1s", "x=1=1*", "* for s after x=1=1"),
        ("x=1=1x", "x=1=1!", "! for x after x=1=1"),
    ];
    for (raw, expected, desc) in cases {
        let cursor = raw.len();
        let rewrite = rewrite_draft(raw, Some(cursor));
        assert_eq!(rewrite.rule, Some(RewriteRule::ExpandSigilAlias), "{desc}: {raw}");
        assert_eq!(rewrite.text, expected, "{desc}: {raw}");
        assert_eq!(rewrite.cursor, Some(cursor), "{desc}: {raw}");
    }
}

#[test]
fn rewrite_draft_close_x_and_s_stay_literal_in_prose() {
    let literal_cases = [
        ("six", 3),
        ("task", 3),
        ("fix forms", 9),
        ("x=1s", 4),        // Theme 'S', must NOT alias!
        ("x=1study", 5),    // Theme 'STUDY', must NOT alias!
        ("x=1x", 4),        // Theme 'X', must NOT alias!
        ("x=s", 3),         // Theme 'S', must NOT alias!
        ("buy xxl shirt", 7),
    ];
    for (raw, cursor) in literal_cases {
        let rewrite = rewrite_draft(raw, Some(cursor));
        assert_eq!(rewrite.rule, None, "should stay literal: {raw} at {cursor}");
        assert_eq!(rewrite.text, raw, "text unchanged: {raw} at {cursor}");
    }
}
```

---

### 5.2 Changes to `bob-mac-capture`

#### 1. File: `Sources/BobMacCapture/CapturePanelController.swift`
Update `handleKeyInDraftEditor(event:)`:
```swift
// Allow 'x' and 's' into noteSeparatorToggleIntent when in close-eligible contexts:
let isCloseAliasCandidate: Bool = {
    guard characters == "x" || characters == "s" else { return false }
    let text = textView.string
    let sel = textView.selectedRange()
    guard sel.length == 0, sel.location > 0 else { return false }
    let prefix = (text as NSString).substring(to: sel.location)
    // Quick check: ends with 'x', digits following 'x', '=', or digits following '='
    return prefix == "x"
        || prefix.hasSuffix("=")
        || (model.latestParse?.mode == "pomodoro_close")
        || (model.latestParse?.mode == "pomodoro_past" && prefix.contains("="))
}()

guard event.modifierFlags.intersection([.command, .control, .option]).isEmpty,
    characters == ":" || characters == "^" || characters == "+"
        || characters == "|" || characters == "," || characters == "."
        || characters == ";" || characters == "-" || characters == "="
        || characters == "~"
        || isCloseAliasCandidate
else {
    return
}
```

#### 2. File: `Sources/BobMacCapture/CapturePanelModel.swift`
Update `noteSeparatorToggleIntent`:
```swift
guard
    typed == ":" || typed == "^" || typed == "+" || typed == "|"
        || typed == "," || typed == "." || typed == ";" || typed == "\\"
        || typed == "/" || typed == "-" || typed == "=" || typed == "~"
        || typed == "x" || typed == "s",
    selectedRange.length == 0,
    selectedRange.location >= 0
else {
    pendingSeparatorToggleIntent = nil
    return
}
```

#### 3. Immediate Return-Key Submit Protection
In `CapturePanelModel.swift`:
```swift
// In editorTextDidChange consumption of intent:
let isCloseOrPastRewrite = (intent.typed == "x" || intent.typed == "s")
    || (intent.typed == "-" && intent.expectedDraft.contains("x="))

completionGate = startCaptureRewrite(
    draft: draft,
    cursorUTF8Offset: intent.expectedCursorUTF8,
    triggeredCharacter: intent.typed,
    triggerTimestamp: intent.timestamp,
    expectsRelationDirectionToggle: intent.expectsRelationDirectionToggle,
    deferSubmitForPastSegmentDash: isCloseOrPastRewrite
)
```
*Note:* Generalizing `deferSubmitForPastSegmentDash` ensures that if a user types `xx<Return>` or `x=1=s<Return>` in rapid succession, the submit action pauses until the rewrite task completes and submits `x!` or `x=1=*` rather than the unexpanded draft.

---

## 6. Summary Comparison Matrix

| Aspect | Current Behavior | Proposed Behavior | Impact / Benefit |
| :--- | :--- | :--- | :--- |
| **Typing `xx`** | Parsed as prose `task` `"xx"` | Rewrites instantly to `x!` | Rapid double-tap closes and completes all Pomodoro tasks without `Shift + 1`. |
| **Typing `xs`** | Parsed as prose `task` `"xs"` | Rewrites instantly to `x*` | Smooth home-row roll closes and parks all Pomodoro tasks without `Shift + 8`. |
| **Typing `x=1=s`** | Diagnostic error (`invalid_pomodoro_past`) | Rewrites instantly to `x=1=*` | Eliminates chorded `*` when recording past parked sessions. |
| **Typing `x=1=x`** | Diagnostic error (`invalid_pomodoro_past`) | Rewrites instantly to `x=1=!` | Eliminates chorded `!` when recording past completed sessions. |
| **Typing `x1x` / `x1s`** | Diagnostic error (`invalid_pomodoro_close`) | Rewrites to `x1!` / `x1*` | Keeps task 1 in progress and completes/parks all others with single unshifted keys. |
| **Typing `x=1s`** | Parsed as 1 block, theme `"S"` | **Stays literal** (`x=1s`) | Preserves Pomodoro theme names with zero hijacking. |
| **Undo (`Cmd-Z`)** | N/A | Restores typed `xx` / `xs` | AppKit native undo guarantees complete reversibility. |
| **Rapid `<Return>`** | Immediate submission | Deferred until rewrite completes | Prevents race condition where raw `xx` or `x=1=s` could be submitted before rewrite finishes. |

---

## 7. Recommended Action Plan

1. **Adopt Requirements with Disambiguation**:
   - Confirm that `x` → `!` and `s` → `*` apply to `x` close syntax (`xx` → `x!`, `xs` → `x*`, `x1x` → `x1!`, `x1s` → `x1*`).
   - Confirm that for `x=`, the expansion occurs strictly *after* the second `=` (`x=1=s` → `x=1=*`, `x=1=x` → `x=1=!`).
2. **Implement in `bob-cli` First**:
   - Add `expand_pomodoro_close_alias` to `src/native/capture_language/rewrite.rs`.
   - Add comprehensive unit tests in `src/native/capture_language/tests/rewrite.rs`.
   - Verify with `cargo test capture_language::tests::rewrite`.
3. **Wire in `bob-mac-capture`**:
   - Update `CapturePanelController.swift` to intercept `x` and `s` with the close-eligible context guard.
   - Update `CapturePanelModel.swift` to register `noteSeparatorToggleIntent` and include close rewrites in submit deferral.
   - Verify on macOS test suite (`just portable-check` or macOS CI check).
4. **Documentation**:
   - Update `docs/keyboard.md` and CLI help examples in `bob capture-rewrite` to document the new `xx`, `xs`, and `x=...=s` / `x=...=x` shortcuts.
