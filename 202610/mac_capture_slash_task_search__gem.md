# Research Report: Implementing Slash (`/`) Task Search and Obsidian Focus in Bob Mac Capture

**Researcher:** `research.4b.gem`  
**Date:** 2026-10-13  
**Target:** `bob-mac-capture`, `bob-cli`, `bob-plugins` (`bob-navigation-hotkeys`)  
**Status:** Complete  

---

## 1. Executive Summary

The proposal under evaluation introduces `/` typed as the first character in the `bob-mac-capture` input box to trigger a fuzzy task search over Obsidian tasks—matching the task catalog and candidate ranking currently surfaced when typing `:`—and, upon selecting a task, opens the enclosing area or project note in Obsidian and focuses the targeted task.

### Key Conclusions:
1. **Strong Product Concept:** The feature is an exceptional addition to Bryan's workflow. It turns `bob-mac-capture`—which is already accessible system-wide via a global macOS hotkey—into an instantaneous, zero-latency "Spotlight for Obsidian Tasks" without requiring the user to switch apps or summon Obsidian's UI first.
2. **The "Block-ID Trap" (Critical Critique):** While the candidate catalog and fuzzy search should mirror `:`, **the task selection behavior must fundamentally diverge from `:`**. In `:`, selecting an ID-less task prompts the user to create a new block ID (`presentTaskLinkIDPrompt`) because a ledger Task Link requires `[[note#^block-id]]`. For navigation (`/`), forcing a block ID prompt would mutate the user's note with an unwanted `^block-id` merely because the user wanted to *view* or *edit* a task.
3. **Obsidian Focus Limitation:** Native Obsidian URIs (`obsidian://open?path=...`) natively support jumping to block IDs (`#^block-id`) and section headings (`#Heading`), but **do not support jumping to line numbers**. If an ID-less task is opened via native `obsidian://open`, Obsidian opens the file but leaves the cursor at the top or last active position, failing to focus the task.
4. **Thin Client Architecture (Decision 3.1.6):** To maintain the core rule that `bob-cli` is the sole authority on grammar and completion (`mac-capture-is-a-thin-client`), `/` should be recognized in `bob-cli`'s `capture_language` and `capture-complete` rather than hardcoded in Swift.
5. **Recommended Navigation Mechanism:** A lightweight Obsidian protocol handler registered in the existing `bob-navigation-hotkeys` plugin (`obsidian://bob-nav?action=focus-task&path=...&line=...&block_id=...`) provides 100% reliable cursor placement and scroll centering for **both identified and ID-less tasks**, with zero file mutations, while gracefully falling back to native `obsidian://open` if the custom handler is unavailable.

---

## 2. Critique of the Plan

### 2.1 Is This a Good Idea?

**Yes.** In fact, it addresses a major ergonomic gap in the Bob desktop ecosystem.

- **System-Wide Accessibility:** Bob Mac Capture is always resident in the macOS menu bar and bound to a global hotkey. Bryan can invoke it from any application, browser, terminal, or virtual desktop.
- **Cognitive Consistency:** The `/` character is the universal standard for "search" across Vim, Slack, Discord, Linear, GitHub, and web browsers. It requires zero learning curve.
- **Symmetry with the Bob Capture Grammar:** Bob capture already features a cohesive set of single-character modal triggers:
  - `:` — Link task into today's Pomodoro ledger
  - `^` — Active / In-progress task locator
  - `!` — Complete task
  - `+` — Sub-task / parent-task selection
  - `@` — Route to note / heading
  - `=` — Pomodoro session control
  Adding `/` for **Task Navigation / Search** completes this palette, making Bob Mac Capture a unified command center for both input (capture) and retrieval (navigation).

---

### 2.2 Critical Gotchas & Flaws in the Naive Proposal

While the high-level concept is sound, treating `/` "just like `:` as far as task selection goes" exposes several design pitfalls that must be addressed:

#### Gotcha 1: The Block ID Prompt Trap
- In `bob capture`, typing `:` is a grammar operator whose end result is a ledger entry `  - [[route#^block-id]]`.
- Consequently, if the user selects an ID-less task in the `:` picker, `bob-mac-capture` invokes `presentTaskLinkIDPrompt(pending: ...)`. Accepting this prompt invokes `bob capture-task-id` to write a permanent `^id` to the task in the vault before linking.
- **For `/`, this is unacceptable.** When searching to navigate, the user's intent is read-only. Forcing a prompt to name and append a block ID to an existing note task imposes unwanted friction and pollutes the markdown file with unneeded block IDs.

#### Gotcha 2: Native Obsidian URI Cannot Focus by Line
- If `/` simply constructs an `obsidian://open` URL:
  ```text
  obsidian://open?path=/Users/bryan/bob/sase_remote.md
  ```
  Obsidian will open the note, but **it will not focus or scroll to the target task**.
- If the task has a `block_id`:
  ```text
  obsidian://open?path=/Users/bryan/bob/sase_remote.md%23%5Eupdates
  ```
  Obsidian natively jumps to `^updates`.
- But many tasks in Bryan's vault (e.g., standard tasks in `sase_remote.md` or area notes) do not have block IDs. Falling back to native `obsidian://open` for ID-less tasks results in a broken promise: the note opens, but the user must manually hunt for the task.

#### Gotcha 3: Draft Replacement vs. Panel Dismissal
- In `:`, selecting a task replaces the capture draft with `@route:block-id`, allowing the user to inspect the preview, add `=<duration>`, or press Return/Command-Return to capture.
- In `/`, task selection is a **terminal navigation gesture**. It should **not** insert text into the draft, should **not** submit to `bob capture`, and should **immediately dismiss the capture panel** while activating Obsidian.

#### Gotcha 4: Prose Collision and Escape Semantics
- In bash/zsh paths and prose, lines occasionally begin with `/` (e.g., `/bin/zsh`, `/etc/hosts`, or `/review notes`).
- Just as `:` only triggers when it is the first character of an empty draft and can be dismissed with `Escape` or `Backspace`, `/` must follow identical non-destructive typing rules:
  - If the user presses `Escape`, the picker closes and leaves `/` in the draft for normal editing/capture.
  - If the user presses `Backspace` while the filter is empty, the `/` trigger is deleted and the panel returns to its idle state.

---

## 3. Architecture & Existing Implementation Details

### 3.1 The "Thin Client of bob" Invariant (Decision 3.1.6)

Core memory decision `mac-capture-is-a-thin-client` dictates:
> *"bob-cli is the only implementation of capture grammar, completion data, preview, and vault mutation. Bob Mac Capture owns presentation, process orchestration, the global hotkey, settings, launch at login, and packaging. It spawns bob directly... and renders what comes back. It may filter or rank what bob returned, but it never decides syntax itself."*

To abide strictly by this rule, `bob-mac-capture` should not invent a separate, detached task-search subsystem in Swift. Instead:
1. `bob capture-complete` should recognize `/` (and `/<query>`) at cursor offset 1+ as a valid completion context (`task_nav` or `task_search`).
2. `bob capture-parse` should identify a draft consisting of `/<query>` and classify it cleanly (or provide an actionable teaching error if passed directly to `bob capture`).
3. `bob-mac-capture` triggers completion on typed `/`, receives the completion response from `bob`, and presents the picker.

---

### 3.2 How `:` Currently Works in `bob-cli` and `bob-mac-capture`

#### 1. In `bob-cli`:
- In `src/native/capture_language/tokens.rs` and `item.rs`:
  A single whitespace-delimited token starting with `:` is recognized as a task link query item.
- In `src/native/capture_complete/engine.rs`:
  ```rust
  CompletionContext::TaskLink => {
      task_link_candidates(bob_dir, &field.query)
  }
  ```
- `task_link_candidates` in `src/native/capture_link_tasks.rs` scans:
  - Today's open Pomodoros in the daily ledger.
  - Routable notes: Inbox, Area notes (A–Z), and active Project notes (A–Z).
  - Open tasks: Ready (`[ ]`), Next (`[*]`), In Progress (`[/]`), and Blocked (`[?]`).
- Each returned `TaskLinkCandidate` contains:
  ```json
  {
    "replacement": "@bob:e2e-prj-deps",
    "ref": "26:09409c3c",
    "route": "bob",
    "note_kind": "project",
    "block_id": "e2e-prj-deps",
    "requires_block_id": false,
    "block_id_suggestions": [],
    "status_symbol": "/",
    "status_name": "In Progress",
    "status_type": "IN_PROGRESS",
    "text": "E2E test bob project/sub-project dependencies!",
    "section": "Next & In Progress",
    "depth": 0,
    "line": 26,
    "group": "queued",
    "scheduled": null,
    "pomodoro": { "line": 41, "name": "BOB", "time_range": "0800-0815", "is_current": true }
  }
  ```

#### 2. In `bob-mac-capture`:
- `CapturePanelModel.scheduleAnalysis` spawns `bob capture-complete --all-tasks --cursor 1 --format json -- :`.
- `CapturePanelModel.handleCompletionResponse` checks `response.context`:
  For `task_link`, it constructs `TaskLinkPickerIndex(candidates: response.candidates)` and sets `picker.source = .taskLink`.
- The presentation (`TaskLinkPickerPresentation.swift`) formats grouped sections:
  - Queued Pomodoros (ordinal, name, time range).
  - In Progress (`[/]`).
  - Next (`[*]`).
  - Note sections (Area / Project notes).
- Filtering is handled locally in Swift via `FuzzyQuery(filter, leadingSigil: ":")` without re-spawning `bob` on each subsequent keystroke.

---

### 3.3 How Note Navigation Currently Works

Currently in `bob-mac-capture`:
- Note opening is encapsulated in `ObsidianOpenURL.swift`:
  ```swift
  public enum ObsidianOpenURL {
      public static func url(forAbsolutePath path: String) -> URL? {
          guard !path.isEmpty else { return nil }
          var components = URLComponents()
          components.scheme = "obsidian"
          components.host = "open"
          components.queryItems = [URLQueryItem(name: "path", value: path)]
          return components.url
      }
  }
  ```
- URLs are invoked in `CapturePanelModel.swift` via `targetOpener`:
  ```swift
  var targetOpener: (URL) -> Void = { NSWorkspace.shared.open($0) }
  ```
- This is used solely for `openAfterCapture` (e.g. after Command-Return capture), opening the modified note at the top-level file path.

---

### 3.4 Capabilities of `bob-plugins` (`bob-navigation-hotkeys`)

Bryan's vault has custom plugins installed in `~/bob/.obsidian/plugins/`, notably `bob-navigation-hotkeys` (version `2.7.2`). Inspection of `bob-plugins` shows that `bob-navigation-hotkeys` already contains all the necessary primitives for editor manipulation and leaf reuse:
1. `openMarkdownFileWithLeafReuse(plugin, file, failureNotice)`:
   - Reuses existing active workspace tabs/leaves for the note, avoiding creating duplicate editor tabs across splits.
2. `findTaskLineByBlockId(lines, blockId)`:
   - Scans note lines for `^blockId` trailing spans on task lines.
3. `setEditorCursorSafely(editor, line, ch)`:
   - Sets the cursor without crashing on clamped or changing bounds.
4. `scrollEditorLineToCenter(editor, line)`:
   - Centers the target task line vertically in Obsidian's viewport.
5. Standard Obsidian Plugin API:
   - `Plugin.registerObsidianProtocolHandler(action, handler)`:
     Obsidian natively routes `obsidian://<action>?param=val` directly to this callback.

---

## 4. Evaluation of Obsidian Focus Strategies

To focus the target task when selected from the `/` picker, four strategies were evaluated:

| Strategy | Mechanism | ID-less Tasks Focused? | Modifies Vault? | Dependency / Coupling | Recommendation |
|---|---|---|---|---|---|
| **A. Native URI Only** | `obsidian://open?path=...#^id` | ❌ No (opens file or section only) | ❌ No | None (Pure AppKit/Obsidian) | Baseline Fallback |
| **B. On-Demand Block-ID Minting** | Call `bob capture-task-id` before opening | ✅ Yes | ⚠️ Yes (mutates note) | `bob-cli` mutation | ❌ Rejected (violates read-only search) |
| **C. `bob-navigation-hotkeys` Protocol Handler** | `obsidian://bob-nav?action=focus-task&...` | ✅ Yes (exact line & centering) | ❌ No | Requires update in `bob-plugins` | **⭐️ Recommended Primary** |
| **D. Hybrid (Protocol Handler + Native Fallback)** | Try `obsidian://bob-nav`, fallback to `obsidian://open` | ✅ Yes (degrades gracefully) | ❌ No | Best resilience | **⭐️ Recommended Implementation** |

### Detailed Breakdown of Strategy C (Protocol Handler)

In `bob-navigation-hotkeys`'s `onload()` lifecycle:
```javascript
this.registerObsidianProtocolHandler("bob-focus-task", async (params) => {
    const { path, line, block_id } = params;
    if (!path) return;

    const file = this.app.vault.getAbstractFileByPath(path);
    if (!file || !this.isMarkdownFile(file)) return;

    const opened = await this.openMarkdownFileWithLeafReuse(file, null);
    if (!opened) return;

    const view = this.getActiveMarkdownView();
    if (!view || !view.editor) return;

    let targetLine = null;
    const lines = view.editor.getValue().split("\n");

    // 1. If block_id is provided, search for it first (survives line edits)
    if (block_id) {
        targetLine = findTaskLineByBlockId(lines, block_id);
    }

    // 2. Fallback to 1-based line number if block_id wasn't present or wasn't found
    if (targetLine === null && line) {
        const parsedLine = parseInt(line, 10) - 1; // 1-based to 0-based
        if (parsedLine >= 0 && parsedLine < lines.length) {
            targetLine = parsedLine;
        }
    }

    if (targetLine !== null) {
        this.setEditorCursorSafely(view.editor, targetLine, 0);
        this.scrollEditorLineToCenter(view.editor, targetLine);
        view.editor.focus();
    }
});
```

#### Why Strategy C is Superior:
1. **Handles 100% of tasks:** Whether the task has `^my-block-id` or is a plain `- [ ] Buy coffee` on line 42, Obsidian lands the cursor directly on the checkbox and centers it in view.
2. **Tab Reuse:** Uses `openMarkdownFileWithLeafReuse` so it does not proliferate dozens of redundant tabs when jumping around tasks.
3. **Zero Vault Pollution:** Keeps the user's notes clean and pristine.
4. **Resilient to External Changes:** Prioritizes `block_id` when present, falling back to line offset.

---

## 5. Adjustments to Requirements

Based on this analysis, the initial requirements should be adjusted as follows:

| Requirement Area | Initial Suggestion | Recommended Adjusted Requirement | Rationale |
|---|---|---|---|
| **Trigger Character** | Pressing `/` as the first key | Pressing `/` as the first key in an empty draft | Prevents capturing `/path/to/file` or `/review` from accidentally triggering search mid-draft. |
| **Candidate Catalog** | Just like `:` | Identical to `:` (Ready, Next, In Progress, Blocked from targets catalog) | Preserves complete mental model parity across `:` and `/`. |
| **ID-less Task Selection** | Just like `:` (which prompts for block ID) | **Diverge from `:`:** Do **not** prompt for block ID; navigate directly | Navigation is a read-only operation; it must never force vault edits. |
| **Selection Action** | Replace draft with `@route:block-id` | **Diverge from `:`:** Launch Obsidian, focus task, dismiss panel immediately | The user is navigating away from capture into Obsidian. |
| **Obsidian Focus Mechanism** | Unspecified (`open and focus`) | Custom protocol handler (`obsidian://bob-nav`) with native URI fallback | Native `obsidian://open` cannot jump to line numbers for ID-less tasks. |
| **Keyboard Modifiers** | Unspecified | `Return`: Open in Obsidian and focus<br>`Cmd+Return`: Open in Obsidian and focus<br>`Option+Return`: Open in new split / leaf | Matches standard desktop navigation ergonomics. |
| **Cancel / Escape** | Unspecified | `Escape` closes picker, preserving `/` in the draft; `Backspace` on empty filter deletes `/` | Allows user to capture literal text starting with `/` without friction. |

---

## 6. Implementation Blueprint

### 6.1 Phase 1: `bob-cli` Grammar & Completion Updates

1. **`src/native/capture_language/tokens.rs` & `item.rs`:**
   - Add recognition for single-token items starting with `/` (e.g. `/` or `/<query>`).
   - Define `CompletionContext::TaskSearch` (or `TaskNav`).
2. **`src/native/capture_complete/engine.rs`:**
   - Handle `CompletionContext::TaskSearch`:
     - Invokes `task_link_candidates(bob_dir, &field.query)` (reusing the exact scanner, ordering, and ranking as `:`).
     - Returns `context: "task_search"`.
3. **`src/native/capture/` (Parser & CLI validation):**
   - If someone runs `bob capture '/query'`, reject with a friendly teaching error:
     `` `/<query>` is a task search query in Bob Mac Capture to open that task in Obsidian; it cannot be captured directly. ``

---

### 6.2 Phase 2: `bob-plugins` Navigation Protocol Handler

1. In `plugins/bob-navigation-hotkeys/src/490-plugin-lifecycle.js`:
   - Register `bob-focus-task` protocol handler.
   - Accept parameters: `path` (relative or absolute), `line` (1-based), and `block_id` (optional).
   - Use `openMarkdownFileWithLeafReuse` -> `findTaskLineByBlockId` / `line` -> `setEditorCursorSafely` -> `scrollEditorLineToCenter` -> `editor.focus()`.
2. Sync to vault using `bob plugins sync`.

---

### 6.3 Phase 3: `bob-mac-capture` UI & Presentation

1. **`CaptureKeyCommandRouter.swift` & `CapturePanelController.swift`:**
   - Ensure `/` typed into an empty draft triggers immediate analysis and completion request.
   - Route `Return` in `.taskSearch` picker to `.acceptPickerRow`.
2. **`TaskSearchPickerIndex` / Presentation:**
   - Reuse `TaskLinkPickerIndexEntry` data structures.
   - Present status text: `"Search tasks — press Return to open in Obsidian"`.
   - Strip leading `/` when parsing `FuzzyQuery(filter, leadingSigil: "/")`.
3. **`CapturePanelModel.swift`:**
   - In `acceptPickerRow(id: String, ...)`:
     - Detect when `picker.source == .taskSearch`.
     - Extract candidate metadata: `route`, `blockID`, `line`, `text`.
     - Resolve target file relative path via `targetCacheSnapshot.targets.first(where: { $0.route == candidate.route })?.relativePath`.
     - Build URL:
       ```swift
       if let navURL = ObsidianOpenURL.focusURL(
           vaultPath: agendaStore.vaultRootPath,
           relativePath: target.relativePath,
           line: candidate.line,
           blockID: candidate.blockID
       ) {
           targetOpener(navURL)
       }
       ```
     - Dismiss the capture panel immediately: `panelDismisser()`.
     - Announce status: `"Opened \(candidate.label ?? candidate.route) in Obsidian"`.
4. **`ObsidianOpenURL.swift`:**
   - Add helper method:
     ```swift
     public static func focusURL(
         vaultPath: String,
         relativePath: String,
         line: Int?,
         blockID: String?
     ) -> URL? {
         var components = URLComponents()
         components.scheme = "obsidian"
         components.host = "bob-focus-task"
         var items = [
             URLQueryItem(name: "path", value: relativePath)
         ]
         if let line {
             items.append(URLQueryItem(name: "line", value: String(line)))
         }
         if let blockID, !blockID.isEmpty {
             items.append(URLQueryItem(name: "block_id", value: blockID))
         }
         components.queryItems = items
         return components.url
     }
     ```

---

## 7. Verification and Testing Strategy

1. **Unit Tests in `bob-cli`:**
   - Test `capture-complete -c 1 -- '/'` returns `context: "task_search"` with all linkable tasks.
   - Test `capture-complete -c 4 -- '/rem'` returns filtered tasks matching query `"rem"`.
   - Test `capture-parse` on `'/rem'` identifies mode and outputs helpful teaching diagnostics.
2. **Unit Tests in `bob-mac-capture`:**
   - Test typed `/` opens picker with `.taskSearch` source.
   - Test row selection in `.taskSearch` does NOT prompt for block ID, even when `blockID == nil`.
   - Test row selection constructs the expected `obsidian://bob-focus-task` URL.
   - Test Escape dismisses picker without clearing `/`.
3. **E2E Integration Verification in Obsidian:**
   - Trigger `/` in `bob-mac-capture`.
   - Select an identified task (`^block-id`): verify Obsidian opens note and jumps to block ID.
   - Select an ID-less task: verify Obsidian opens note, places cursor on the exact line, and centers view.
   - Select an already open note: verify leaf is reused without duplicating tabs.

---

## 8. Summary Recommendation

**Proceed with the feature, adopting the adjusted requirements.**

By coordinating across `bob-cli` (completion authority), `bob-mac-capture` (presentation & hotkey UI), and `bob-navigation-hotkeys` (Obsidian leaf reuse and exact line focusing), this feature can be delivered cleanly, robustly, and without violating either the read-only semantics of search or the architectural principles of the Bob ecosystem.
