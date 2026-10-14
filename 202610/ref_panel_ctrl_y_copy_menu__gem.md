# Design and Architecture of the `<ctrl+y>` Clipboard Copy Palette for Bob Refs

- **Date:** 2026-10-14
- **Researcher:** `research.16.gem` (Swarm Member)
- **Target Component:** `bob-mac-capture` (`RefsPanel`, `RefsKeyRouter`, `RefsCore`) & `bob-cli` (`bob ref list`, `bob ref show`)
- **Status:** Complete Research Proposal & Design Specification

---

## 1. Executive Summary

This report evaluates and designs a dedicated **`<ctrl+y>` clipboard copy menu** (the **"Yank Palette"**) for the Bob Refs panel inside `bob-mac-capture`.

### The Core Problem
The Refs panel is extraordinarily fast at *retrieving* and *opening* references in Highlights, Obsidian, and Finder (`↵`, `⌘↵`, `⌥↵`). However, copying reference data out of the panel into active writing contexts (Obsidian daily notes, canvas files, code files, terminal commands, or Slack) remains high-friction. The existing `⌘K` actions menu carries only two basic clipboard actions (`Copy Wiki Link` and `Copy PDF Path`), requires navigating a traditional macOS context menu with arrow keys or mouse tracking, and omits the rich metadata, excerpts, marker IDs, citations, and task lines that constitute a reference in Bob's ecosystem.

### Key Conclusions
1. **The concept is outstanding and should be built**, but as a **lightweight, in-panel SwiftUI glass HUD ("Yank Palette")**, NOT as a traditional AppKit `NSMenu`. An `NSMenu` intercepts the runloop, disrupts the panel's glass aesthetics, and handles single-keypress selection poorly on macOS.
2. **`<ctrl+y>` is an excellent ergonomic choice** for power users (grounded in the Unix/Vim "yank" tradition and harmonized with the panel's existing control chords `⌃D`, `⌃U`, `⌃P`, `⌃N`). However, to avoid trapping standard Mac users, `⌘C` (when the search field has no text selected) should act as a direct alias for the primary copy action (`Wiki Link`), while `⌃Y` invokes the full palette.
3. **The palette must feature single-key mnemonics with live previews.** A user pressing `⌃Y` sees a HUD where pressing `w` copies the wiki link, `m` copies the marker ID, `p` copies the PDF path, `t` copies the reading task, `s` copies the summary, and `q` copies the latest quote—each displaying the exact string to be copied before the key is struck.
4. **Minor additive backend changes to `bob-cli` are required:** `RefRow.id` (the marker/frontmatter ID) is currently suppressed with `#[serde(skip_serializing)]` in `src/native/ref_library/row.rs`. Serializing this field allows Bob Mac Capture to expose marker IDs cleanly without violating the thin-client architecture.

---

## 2. Critique of the Proposal

### 2.1 Is `<ctrl+y>` a Good Idea?

The proposal calls for binding `<ctrl+y>` in the Refs panel to open a single-keypress copy menu.

#### The Arguments in Favor
- **Strong Mnemonic ("Yank"):** In Vim, kakoune, tmux, and developer tooling, `y` is the universal verb for "yank" (copy). Given that Bryan uses Vim-style keybindings across his system (e.g., `]s`/`[s` GTD walks, `Ctrl+O` jumps, `j`/`k` navigation in Refs), `y` is intuitively recognized as copy.
- **Architectural Symmetry with `RefsKeyRouter`:** The Refs panel already segments its key space by modifier role:
  - **Unmodified keys:** Printable text falls through to the search field; `↵`, `Tab`, arrows, `PageUp`/`PageDown`, `Home`/`End` navigate and open.
  - **`⌘` (Command):** Top-level system operations (`⌘↵` open note, `⌘K` show actions, `⌘R` refresh, `⌘S` scan, `⌘1–5` switch scopes).
  - **`⌥` (Option):** Alternate opens (`⌥↵` reveal in Finder, `⌥↑`/`⌥↓` jump sections).
  - **`⌃` (Control):** Inspection and non-destructive in-panel navigation (`⌃P`/`⌃N`/`⌃J`/`⌃K` list movement, `⌃D`/`⌃U` inspector note scrolling, `⌃[` escape).
  Placing clipboard extraction on `⌃Y` aligns perfectly with this established tier: it is an inspection/extraction chord that operates strictly within the panel.

#### Potential Pitfalls & Nuances
1. **Cocoa Readline Emacs Conflict:**
   In standard macOS text fields (`NSTextField` / `NSTextView`), `Ctrl+Y` is bound by default to Cocoa's `yank:` selector (pasting text previously killed with `Ctrl+K` or `Ctrl+W`).
   *Resolution in Refs:* `RefsKeyRouter` has *already* broken Cocoa's default line-editing bindings. It remapped `Ctrl+D` (Cocoa "delete forward") to `.scrollInspector(.down)`, `Ctrl+K` (Cocoa "kill line") to `.move(.previous)`, and `Ctrl+U` (Unix "kill line backward") to `.scrollInspector(.up)`. Since the search bar is a single-line filter field where users type short keywords rather than editing long paragraphs, repurposing `Ctrl+Y` introduces zero friction for typical users and fits the existing precedent.
2. **Footer Real Estate:**
   `RefsFooter.swift` currently renders:
   ```
   ↵ Open in Highlights  ⌘↵ Note  ⌥↵ Reveal  ⌘K Actions  ⌘S Scan  ⌘1–5 Scope  esc Close
   ```
   This is already crowded on narrower displays (such as MacBook 13/14" screens with high UI scaling). Adding `⌃Y Copy` verbatim would truncate status indicators on the right.
   *Resolution:* The footer must be slightly compressed. `⌘1–5 Scope` can become `⌘1–5` or move to the search bar placeholder, freeing space for `⌃Y Copy`.

### 2.2 Why Not Just Use `⌘K` Actions Menu?

`RefsActionsMenu.swift` already has `⌘K` which pops up an AppKit `NSMenu` containing:
- Open in Highlights (`↵`)
- Open Note (`⌘↵`)
- Reveal in Finder (`⌥↵`)
- Copy Wiki Link (no shortcut)
- Copy PDF Path (no shortcut)
- Open Source URL
- Open Narration
- Open in Default App
- Refresh Library (`⌘R`)
- Scan for New References (`⌘S`)

Why create a separate `<ctrl+y>` menu instead of putting shortcuts into `⌘K`?
1. **Menu Velocity:** `⌘K` is an *actions* menu that includes heavy dispatch operations (launching apps, running scans). Navigating it requires arrowing down 4 times or using the mouse.
2. **Single-Keypress vs. Modifier Shortcuts:** In an `NSMenu`, assigning a single unadorned letter like `w` or `p` as a key equivalent is deeply problematic in macOS. The system menu manager treats single un-modified keystrokes as "type-ahead search" across menu item titles rather than immediate trigger keys.
3. **Modal Focus:** When Bryan is actively drafting a note or task, he wants to hit `[hotkey] -> [type 2 chars] -> ⌃Y -> w`, and instantly have `[[ref/notes.md|Title]]` in his clipboard, with the panel dismissed or ready for the next action. That requires a zero-friction, dedicated Yank HUD.

---

## 3. Interaction & Visual Design: The Glass "Yank Palette"

To satisfy the requirement that this feature be **intuitive, reliable, and beautiful**, we reject the use of a standard AppKit `NSMenu` for the `<ctrl+y>` gesture and instead design a native SwiftUI Glass HUD overlay.

### 3.1 Visual Anatomy of the Yank Palette

When `<ctrl+y>` is pressed, a compact modal card fades and scales in (`0.08s easeOut`), centered over the boundary between the list and inspector or anchored below the selected row.

```
┌────────────────────────────────────────────────────────────────────────┐
│  YANK TO CLIPBOARD                                      [esc] Cancel   │
├────────────────────────────────────────────────────────────────────────┤
│  [ W ]  Wiki Link              [[20261014_ref_panel|Bob Refs Panel]]   │
│  [ M ]  Marker ID              ref_panel_quick_open                    │
│  [ T ]  Reading Task           - [ ] [[20261014_ref_panel]] #task #ref │
│  [ P ]  PDF Path (Absolute)    ~/bob/lib/chat/20261014_ref_panel.pdf   │
│  [ R ]  PDF Path (Relative)    lib/chat/20261014_ref_panel.pdf         │
│  [ U ]  Source URL             https://arxiv.org/abs/2610.12345        │
│  [ S ]  Summary / Abstract     "Examines the feasibility of adding..." │
│  [ Q ]  Latest Highlight Quote "The panel must open in under 50ms..."  │
│  [ C ]  Citation (Markdown)    Bryan (2026). Bob Refs Panel.           │
│  [ B ]  BibTeX Entry           @article{bryan2026refs, ...}            │
└────────────────────────────────────────────────────────────────────────┘
```

#### Visual Tokens & Styling
- **Background Material:** `.regularMaterial` matching `CapturePickerView` and `RefsPanelView.well`.
- **Corner Radius:** `12 pt` (`RefsVisualTokens.wellRadius`), bordered by a `0.5 pt` stroke of `Color.primary.opacity(0.10)`.
- **Shadow:** Deep elevation shadow (`radius: 20, y: 10, opacity: 0.25`), creating a clear visual hierarchy above the listing.
- **Keycap Badges (`[ K ]`):**
  - Rendered in a small rounded rectangle (`cornerRadius: 5`) with a subtle gradient background (`.quaternary`), monospaced bold font (`.font(.system(.caption, design: .monospaced).weight(.bold))`), and an active accent color.
- **Preview Column:**
  - On the trailing side of each row, a monospaced tertiary text preview displays the *actual text* that will land on the clipboard, truncated with middle or tail ellipsis.
  - **Why this is critical:** Users hate copying "blindly". Showing `[[ref/notes.md|Title]]` next to `Wiki Link` provides immediate confirmation of the format before committing the keypress.

### 3.2 The Dual-Input Ergonomic Model

To make the menu both blistering fast for muscle memory and discoverable for casual use:

1. **Direct Single Keystroke (Fast Path):**
   - Pressing `w`, `m`, `t`, `p`, `u`, `s`, `q`, etc. immediately:
     1. Copies the corresponding string to `NSPasteboard.general`.
     2. Posts an accessibility announcement (`"Copied Wiki Link"`).
     3. Dismisses the Yank Palette instantly.
     4. Displays a 1.5-second toast confirmation in the panel footer: `Copied Wiki Link`.
     5. Keeps the Refs panel open with focus returned to the search field (or optionally dismisses the panel if configured; see §6).
2. **Arrow + Return Navigation (Exploratory Path):**
   - Users who do not have the keys memorized can use `↓`/`↑` or `⌃N`/`⌃P` to highlight rows in the palette, then hit `Return` or `Tab` to copy the selected item.
3. **Cancellation:**
   - Hitting `Escape`, `⌃[`, or pressing `⌃Y` a second time dismisses the palette with no clipboard mutation, leaving the selected row and search query intact.

---

## 4. Comprehensive Catalog of Copy Options

What properties of a reference note / PDF file might a user want on their clipboard?
Below is a structured taxonomy of properties, categorized by use case, assigned ergonomic single-character mnemonics, and analyzed for availability.

### 4.1 Knowledge Graph & Vault Integration

| Key | Property | Output Format / Example | Why Bryan Needs This |
| :--- | :--- | :--- | :--- |
| **`w`** | **Wiki Link (Aliased)** | `[[ref/chat/20261014_topic.md\|Refined Display Title]]` | Primary gesture for linking references inside Obsidian notes and research reports. |
| **`W`** | **Wiki Link (Bare Stem)** | `[[20261014_topic]]` | Cleaner link style when note titles are auto-resolved by Obsidian plugins or frontmatter aliases. |
| **`m`** | **Marker / Note ID** | `20261014_topic` or `xprompt_role_binding` | The semantic identifier stored in the PDF's page-1 marker note and frontmatter `id:`. Used in capture syntax and `bob ref find <id>`. |
| **`t`** | **Reading Task Line** | `- [ ] [[ref/chat/20261014_topic.md]] #task #ref` | Instantly creates a v2 reading task ready to be pasted into an Area or Project note. |
| **`o`** | **Obsidian URI** | `obsidian://open?vault=bob&file=ref%2Fchat%2F20261014_topic.md` | Deep link for pasting into macOS Calendar, Reminders, Slack, or GitHub issues. |
| **`h`** | **Highlights Deep Link** | `highlights://Users/bryan/bob/lib/chat/20261014_topic.pdf#page=1` | Direct URI opening Highlights to page 1 of the specific document. |

### 4.2 File System & Terminal Paths

| Key | Property | Output Format / Example | Why Bryan Needs This |
| :--- | :--- | :--- | :--- |
| **`p`** | **Absolute PDF Path** | `/Users/bryan/bob/lib/chat/20261014_topic.pdf` | Essential for shell scripting, CLI tools (`pdftotext`, `mutool`, `rclone`), and terminal pipelines. |
| **`r`** | **Relative PDF Path** | `lib/chat/20261014_topic.pdf` | Standard path used in Bob's internal configurations and task lines. |
| **`n`** | **Relative Note Path** | `ref/chat/20261014_topic.md` | Path used in `bob ref show`, git commands, and vault metadata. |
| **`N`** | **Absolute Note Path** | `/Users/bryan/bob/ref/chat/20261014_topic.md` | For opening in external text editors (VS Code, Neovim, Sublime). |

### 4.3 Web & Research Metadata

| Key | Property | Output Format / Example | Why Bryan Needs This |
| :--- | :--- | :--- | :--- |
| **`u`** | **Source Web URL** | `https://arxiv.org/abs/1706.03762` | For sharing the paper or article with colleagues, pasting in chat, or opening in a browser. |
| **`d`** | **Identifier (DOI / arXiv)** | `arXiv:1706.03762` or `10.1145/3290605.3300267` | Exact canonical identifier for research papers and literature reviews. |
| **`c`** | **Formatted Citation** | `Vaswani et al. (2017). Attention Is All You Need. arXiv:1706.03762` | Markdown/text citation ready for inclusion in academic or blog drafts. |
| **`b`** | **BibTeX Entry** | `@article{vaswani2017attention, title={...}, ...}` | Generated on-the-fly for LaTeX / Overleaf documents. |

### 4.4 Excerpts & Annotations (Content Extraction)

| Key | Property | Output Format / Example | Why Bryan Needs This |
| :--- | :--- | :--- | :--- |
| **`s`** | **Summary / Abstract** | *"The dominant sequence transduction models are based on complex recurrent or convolutional neural networks..."* | The executive summary or abstract text extracted by `RefsSummaryExtractor`. |
| **`q`** | **Latest Highlight Quote** | `> "Self-attention, sometimes called intra-attention..." (p. 2)` | The most recently added quote from the user's Highlights annotations. |
| **`k`** | **Latest User Note / Comment** | *"Key concept: eliminates recurrence entirely."* | The user's personal thought or annotation comment on the document. |
| **`a`** | **All Notes & Highlights (MD)** | `### Highlights\n- > "Quote 1" (p. 1)\n  - My comment\n...` | A formatted Markdown block of all highlights, ready to embed in a synthesis note. |

### 4.5 Dynamic Adaptation & Palette Prioritization

A reference note for a short chat report will not have an arXiv ID, DOI, or BibTeX citation. Showing dead or disabled rows clutters the visual field.

**Policy: Dynamic Contextual Visibility**
- **Core Rows (Always Present):**
  - `[ W ]` Wiki Link
  - `[ M ]` Marker / Note ID
  - `[ T ]` Reading Task
  - `[ P ]` PDF Path (Absolute)
  - `[ N ]` Note Path
- **Conditional Rows (Appended when data exists):**
  - `[ U ]` Source URL *(only if `!item.urls.isEmpty`)*
  - `[ D ]` DOI / arXiv ID *(only if `item.doi != nil || item.arxivID != nil`)*
  - `[ C ]` Citation *(only for Papers / Articles with authors & published date)*
  - `[ S ]` Summary / Abstract *(only if `inspectorLoader.content?.summary != nil`)*
  - `[ Q ]` Latest Highlight Quote *(only if `item.annotationCount > 0`)*
  - `[ K ]` Latest User Comment *(only if `item.commentCount > 0`)*

---

## 5. Architectural & Technical Implementation

Following the strict rule from SASE memory:
> **Bob Mac Capture Is A Thin Client Of bob:** bob-cli is the only implementation of capture grammar, completion data, preview, and vault mutation. Bob Mac Capture owns presentation, process orchestration, the global hotkey, settings, launch at login, and packaging.

### 5.1 Backend Requirements in `bob-cli`

Currently, `bob ref list -R all -A -f json` produces `RefRecord` objects.
In `src/native/ref_library/row.rs`:
```rust
pub(crate) struct RefRow {
    pub path: String,
    pub link: String,
    pub title: String,
    ...
    /// Frontmatter `id`, kept out of JSON; only query resolution reads it.
    #[serde(skip_serializing)]
    pub id: Option<String>,
    ...
}
```
Notice that `pub id: Option<String>` is explicitly annotated with `#[serde(skip_serializing)]`!
This is why the Swift client currently cannot read the marker note ID.

#### Required `bob-cli` Change
1. Remove `#[serde(skip_serializing)]` from `pub id: Option<String>` in `src/native/ref_library/row.rs`.
2. Add `#[serde(skip_serializing_if = "Option::is_none")]` so notes without an explicit `id:` simply omit the field or serialize it cleanly.
3. This is a 100% additive change that preserves schema compatibility while giving the Mac client direct access to the note's marker ID.

### 5.2 Frontend Data Models in `RefsCore`

In `bob-mac-capture/Sources/RefsCore/RefsDecoding.swift`:
```swift
public struct RefRecord: Codable, Equatable, Sendable {
    ...
    public let idField: String? // Decoded from "id"
    ...
}
```

In `bob-mac-capture/Sources/RefsCore/RefsModel.swift`:
```swift
public struct RefItem: Identifiable, Equatable, Sendable {
    public let id: String       // Note path (unique key)
    public let markerID: String? // Semantic marker/frontmatter ID
    ...
}
```

### 5.3 Copy Action Modeling: `RefsCopyAction`

```swift
public enum RefsCopyTarget: Equatable, Sendable {
    case wikiLink
    case markerID
    case readingTask
    case pdfPathAbsolute
    case pdfPathRelative
    case notePathRelative
    case sourceURL(URL)
    case identifier(String)
    case citation
    case summary
    case latestQuote
    case latestComment
    case allAnnotations
}

public struct RefsCopyOption: Identifiable, Equatable, Sendable {
    public let id: String
    public let target: RefsCopyTarget
    public let keyChar: Character
    public let title: String
    public let preview: String

    public init(target: RefsCopyTarget, keyChar: Character, title: String, preview: String) {
        self.id = String(keyChar)
        self.target = target
        self.keyChar = keyChar
        self.title = title
        self.preview = preview
    }
}
```

### 5.4 Key Routing & State Machine in `RefsKeyRouter`

In `RefsKeyRouter.swift`, we add `KeyCode.y = 16` and a new command `.showCopyMenu`:

```swift
case KeyCode.y:
    if flags == .control {
        return .showCopyMenu
    }
    return nil
```

#### Palette Active State Machine
When `RefsPanelModel.isCopyMenuPresented` is true:
- Key events do **not** route through standard panel commands.
- The local monitor in `RefsPanelController` passes the key event to `RefsCopyKeyRouter`.
- Printable characters match against `RefsCopyOption.keyChar` (case-insensitive).
- Matching key -> executes `model.copyProperty(target)`, dismisses palette, shows toast, consumes event.
- `Escape` or `⌃[` -> dismisses palette, consumes event.
- Arrows `↑`/`↓` -> adjusts highlighted index in palette.
- `Return` -> executes copy for highlighted index.
- Unmatched keys -> system beep (`NSSound.beep()`) to give audio feedback without dropping characters into the search field.

---

## 6. Detailed Plan of Record & Recommendations

### 6.1 Requirements Adjustments Summary

| # | Proposal Requirement | Recommended Adjustment | Justification |
| :--- | :--- | :--- | :--- |
| **A1** | Add `<ctrl+y>` keymap to ref panel | **Adopt `<ctrl+y>`, and also wire `⌘C` (when query has no selected text)** | Power users get the Vim yank chord (`⌃Y`); standard Mac users get zero-friction default copy (`⌘C`). |
| **A2** | Open a "new menu" for single keypress | **Implement as a SwiftUI Glass HUD ("Yank Palette"), NOT an AppKit `NSMenu`** | AppKit menus cannot cleanly bind single unadorned letters (`w`, `p`, `m`), pause animations, and break the panel's modern visual design. |
| **A3** | Options to put in menu | **Curated 2-tier catalog: 5 Universal Core items + dynamic contextual items (URL, DOI, Quote, Summary)** | Prevents clutter on chat reports while providing academic depth on papers and articles. |
| **A4** | Visual Presentation | **Display Keycap Badge + Action Title + Monospaced Live Output Preview** | Seeing the exact text preview before pressing the key eliminates clipboard mistakes. |
| **A5** | Post-Copy Behavior | **Copy to pasteboard, show 1.5s toast, keep panel open by default; `Shift+<key>` copies and closes panel** | Often Bryan copies a link to reference while continuing to browse, but if he wants to copy and immediately resume writing, `Shift` gives him the one-shot exit. |

### 6.2 The Recommended Yank Palette Catalog

```
[ W ]  Wiki Link              [[ref/chat/20261014_ref.md|Bob Refs]]
[ M ]  Marker ID              20261014_ref_panel
[ T ]  Reading Task           - [ ] [[ref/chat/20261014_ref.md]] #task #ref
[ P ]  PDF Path (Absolute)    /Users/bryan/bob/lib/chat/20261014_ref.pdf
[ R ]  PDF Path (Relative)    lib/chat/20261014_ref.pdf
[ N ]  Note Path              ref/chat/20261014_ref.md
--- Contextual (rendered when available) ---
[ U ]  Source URL             https://arxiv.org/abs/...
[ D ]  DOI / arXiv ID         10.1145/3290605
[ S ]  Summary / Abstract     "Examines the feasibility of..."
[ Q ]  Latest Quote           > "The panel must open under 50ms..."
[ K ]  Latest Comment         "Crucial performance target."
[ C ]  Citation (Markdown)    Bryan (2026). Bob Refs.
```

### 6.3 Phased Implementation Roadmap

#### Phase 1: `bob-cli` Schema & `RefsCore` Serialization
- **Task 1.1:** In `bob-cli/src/native/ref_library/row.rs`, un-suppress `pub id: Option<String>` so it serializes into the `bob ref list` and `bob ref show` JSON envelopes.
- **Task 1.2:** In `bob-mac-capture/Sources/RefsCore/RefsDecoding.swift`, decode `id` into `RefRecord`.
- **Task 1.3:** In `RefsCore/RefsModel.swift`, expose `markerID: String?` on `RefItem`.
- **Task 1.4:** Add Linux unit tests verifying snapshot parsing retains `markerID`.

#### Phase 2: Copy Engine & Key Routing
- **Task 2.1:** Implement `RefsCopyFormatter` in `RefsCore`: pure functions that generate strings for each `RefsCopyTarget`.
- **Task 2.2:** Add `KeyCode.y = 16` and `.showCopyMenu` to `RefsKeyRouter.swift`.
- **Task 2.3:** Implement `RefsCopyKeyRouter` to handle single-keystroke selection, arrows, return, and dismissal.
- **Task 2.4:** Unit test key routing on Linux (`swift test`).

#### Phase 3: SwiftUI Yank Palette HUD & Panel Polish
- **Task 3.1:** Build `RefsCopyHUDView.swift`: glass card, keycap badges, semantic labels, trailing live text previews.
- **Task 3.2:** Mount `RefsCopyHUDView` in `RefsPanelView.swift`, transitioning smoothly with spring animations.
- **Task 3.3:** Integrate with `RefsPanelModel.showToast(_:)` for transient visual feedback.
- **Task 3.4:** Update `RefsFooter.swift` to reflect `⌃Y Copy`.

#### Phase 4: Verification & Fixtures
- **Task 4.1:** Generate deterministic SwiftUI preview snapshots using `ImageRenderer` for visual regression testing.
- **Task 4.2:** Test edge cases: references missing PDFs, references with long titles, empty highlight sets, and Asian/IME composing states.
- **Task 4.3:** Verify keyboard responsiveness on macOS CI and live host.

---

## 7. Sources and References

1. **`bob-mac-capture` Codebase:**
   - `Sources/BobMacCapture/Refs/RefsKeyRouter.swift`: Keyboard event routing and modifier handling.
   - `Sources/BobMacCapture/Refs/RefsActionsMenu.swift`: Existing `⌘K` action definitions and `RefsPasteboardWriting`.
   - `Sources/BobMacCapture/Refs/RefsPanelModel.swift`: Panel state, selection, commands, and toast notifications.
   - `Sources/BobMacCapture/Refs/RefsPanelView.swift` & `RefsVisualTokens.swift`: Layout geometry, glass effects, and visual styling.
   - `Sources/RefsCore/RefsInspector.swift`: Annotation decoding (`RefsShowAnnotation`), summaries, and reading times.
2. **`bob-cli` Codebase:**
   - `src/native/ref_library/row.rs`: `RefRow` definition and field serialization.
   - `src/native/ref_library/show.rs`: Annotation and task resolution for exact references.
   - `src/native/highlights_ref/marker.rs`: PDF page-1 marker parsing and `FIELD_ID` management.
3. **Prior SASE Research:**
   - `sase/repos/research/202610/highlights_quick_open_refs_panel/highlights_quick_open_refs_panel__final.md`: Canonical architectural foundation of the Bob Refs panel.
   - SASE Memory: `decisions:mac-capture-is-a-thin-client`.
