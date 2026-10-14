# Ref Panel `<ctrl+y>` Quick-Copy Palette: Design, Taxonomy, Critique, and Implementation Specification

- **Author**: `research.19.gem`
- **Date**: 2026-10-14
- **Project**: `bob-mac-capture` / `bob-cli`
- **Scope**: Reference Panel Keyboard Interactions, Clipboard Data Model, and Visual Design
- **Status**: Research & Design Proposal

---

## 1. Executive Summary & Core Recommendations

This report evaluates and designs a dedicated `<ctrl+y>` quick-copy feature for the Reference Panel in `bob-mac-capture`. In the current architecture, copying information about a reference item (e.g., its Obsidian wiki link or local PDF file path) requires either summoning the full ⌘K Actions menu and navigating through mixed action categories, or opening the note in Obsidian/Highlights to manually select and copy text. 

A rapid, keyboard-driven workflow requires an instantaneous mechanism to extract identifiers, citations, file paths, and reading notes directly to the macOS system pasteboard.

### Key Conclusions & Strategic Decisions

1. **Adopt `<ctrl+y>` as a First-Class Modal Trigger**:
   - In Vim terminology, `y` signifies **Yank** (copy). Because `bob-mac-capture`'s Ref Panel already incorporates a Vim/Readline navigation grammar (`ctrl+j`/`ctrl+k` for vertical movement, `ctrl+d`/`ctrl+u` for inspector half-page scrolling, and `ctrl+[` for escape), `<ctrl+y>` aligns with the app's established keyboard philosophy.
   - While macOS Readline text bindings traditionally associate `ctrl+y` with `yank:` (pasting from the kill-ring), `RefsKeyRouter` already rebinds `ctrl+k` from `kill-line` to `move(.previous)`. Thus, Cocoa kill-ring semantics are already superseded in this interface.

2. **Reject AppKit `NSMenu` in Favor of a Declarative SwiftUI Glass HUD Palette**:
   - The existing ⌘K menu uses `NSMenu.popUp(...)`. While suitable for occasional command discovery, `NSMenu` fails the single-keypress copy requirement: AppKit menus hijack the runloop, intercept bare alphanumeric keystrokes for type-ahead list filtering rather than instant execution, and impose rigid system styling that breaks the panel's bespoke liquid-glass aesthetic.
   - We recommend a transient **SwiftUI Glass HUD Palette** anchored concentric with the panel well. It presents categorized copy targets with vintage keycap badges (`[W]`, `[P]`, `[I]`, `[1]`), displays a truncated live preview of the text to be copied, and immediately dispatches upon a single unmodified keypress.

3. **Incorporate a "Zero-Selection `⌘C`" Smart Default**:
   - To satisfy native macOS muscle memory while preserving `<ctrl+y>` for multi-property selection, we propose a hybrid:
     - If text is selected in the search field, `⌘C` performs standard text copying.
     - If **no** text is selected in the search field, `⌘C` copies the default representation (the Obsidian Wiki Link `item.link`) directly, displaying a 1.5 s toast.
     - `<ctrl+y>` opens the full **Quick-Copy Palette**, allowing instant single-key access to all 12+ item properties.

4. **Strict Adherence to SASE Architecture (`decisions:mac-capture-is-a-thin-client`)**:
   - The palette requires zero new command-line parser additions or grammar mutations. All necessary metadata is already surfaced by `bob ref list` snapshot records (`RefItem`) and `bob ref show <path> -c -f json` (`RefsShowResponse` / `RefsInspectorContent`).

---

## 2. Critique of the Proposed Plan

### 2.1 The Keymap: Why `<ctrl+y>`? Strengths, Friction, and Alternatives

| Shortcut | Mnemonic / Domain | Pros | Cons / Conflicts | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **`<ctrl+y>`** | Vim "Yank" / CLI | Cohesive with `ctrl+j/k/d/u/[`. Does not type into focused search bar. | Unfamiliar to pure Mac GUI users; historic Cocoa `yank:` conflict (minor here). | **Primary Palette Trigger** |
| **`⌘C`** (bare) | Standard macOS Copy | Universal muscle memory. | Triggers text copy when search query is highlighted. | **Adopt for zero-selection default (Wiki link)** |
| **`⌘⇧C`** | Developer / Inspector Copy | Common in IDEs (Copy Relative Path, Copy Reference). | Requires two hands / three fingers. | Viable secondary alias |
| **`⌘Y`** | macOS Quick Look | Standard macOS shortcut. | Conficts with user expectation of document Quick Look preview. | Reject |
| **`⌥C`** | Option-Chord | Distinct modifier. | Types special characters (`ç`) into text fields if unintercepted. | Reject |

#### Detailed Ergonomic Analysis
- **The Text-Field Focus Paradox**: Because `RefsSearchBar` holds first-responder focus by default, any bare printable character (like typing `c` or `y`) immediately appends to the search filter. Therefore, invoking an action palette *must* employ a modifier key (`control` or `command`).
- **The Terminal/Vim Alignment**: Bob users heavily utilize terminal-driven workflows (Git, CLI, Neovim, Tmux). In `RefsKeyRouter.swift`, we find:
  - `KeyCode.k` with `.control` $\rightarrow$ `move(.previous)`
  - `KeyCode.j` with `.control` $\rightarrow$ `move(.next)`
  - `KeyCode.d` with `.control` $\rightarrow$ `scrollInspector(.down)`
  - `KeyCode.u` with `.control` $\rightarrow$ `scrollInspector(.up)`
  - `KeyCode.leftBracket` with `.control` $\rightarrow$ `escape`
  Introducing `<ctrl+y>` as "Yank" fits into this exact register of control-key navigation.
- **The Readline Kill-Ring Non-Issue**: In Emacs/Readline, `ctrl+k` cuts to end of line and `ctrl+y` yanks it back. However, `RefsKeyRouter` lines 129–136 explicitly swallows `ctrl+k` for navigation. Because users cannot `ctrl+k` kill text in the search bar, expecting `ctrl+y` to restore text is a non-existent mental model in this application.

### 2.2 Mechanism Critique: AppKit `NSMenu` vs. SwiftUI Glass HUD

The user prompt requests: *"This keymap should open a new menu that allows the user to select (with a single keypress) what they want to copy... intuitive, reliable, and (last but not least) beautiful!"*

#### Why AppKit's `NSMenu` is Structurally Flawed for this Task
1. **Modal Runloop Interception**: `menu.popUp(...)` executes a synchronous AppKit event-tracking loop. This halts SwiftUI view updates, freezes toast animations, and makes automated testing awkward because synthetic key events cannot be routed cleanly through `RefsKeyRouter`.
2. **Type-Ahead Conflict with Unmodified Keys**: In standard macOS menus, pressing an unmodified letter key (such as `p` or `w`) triggers "type-to-select" (jumping through menu items starting with that character), rather than firing the item's action. Forcing an `NSMenuItem` to fire on bare keypresses without `command` modifiers requires complex custom key equivalent hacking.
3. **Aesthetic Disharmony**: `bob-mac-capture` features a gorgeous glass aesthetic (`NSGlassEffectView`, concentric 12 pt well radiuses, 0.5 pt subtle boundary strokes, accent-tinted capsules). A standard rectangular AppKit context menu looks dated and disconnected from the surrounding visual hierarchy.

#### Why a Custom SwiftUI Glass HUD Palette Excels
1. **Pure State-Machine Integration**: The menu is simply a state enum on `RefsPanelModel` (`isCopyPalettePresented: Bool`). When active, `RefsKeyRouter` handles single keycodes (`w`, `p`, `i`, etc.) as pure enum commands (`.executeCopy(.wikiLink)`).
2. **Live Value Previews**: In an `NSMenu`, you only see "Copy Wiki Link". In a custom HUD palette, you see:
   ```text
   [ W ]  Wiki Link      [[ref/papers/vaswani2017|Attention Is All You Need]]
   [ P ]  PDF Path       ~/bob/lib/papers/vaswani2017.pdf
   [ I ]  Marker ID      vaswani2017
   ```
   Seeing the exact payload before copying prevents errors and builds immediate confidence.
3. **Deterministic Testability**: 100% of the router transitions, key mappings, clipboard payloads, and dismissal states can be verified via headless `XCTest` unit tests in `RefsKeyRouterTests` and `RefsPanelModelTests`.

---

## 3. Creative Inventory of Copy Targets

When working with reference literature, technical papers, AI chat transcripts, and documentation, the user's pasteboard requirements vary drastically depending on the destination app (Obsidian, Terminal, GitHub PR, Slack, BibTeX file, or LLM chat).

Below is the comprehensive taxonomy of properties available from `RefItem` and `RefsShowResponse`, categorized by workflow domain:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    REFERENCE COPY TAXONOMY & TARGET CATALOG                  │
├────────────────────────┬─────────────────────────┬───────────────────────────┤
│ Category               │ Target Property         │ Mnemonic & Payload Format │
├────────────────────────┼─────────────────────────┼───────────────────────────┤
│ Identifiers & Links    │ Obsidian Wiki Link      │ [ W ] [[path|Title]]      │
│                        │ Marker Note ID (Slug)   │ [ I ] stem / slug         │
│                        │ Standard Markdown Link  │ [ M ] [Title](URL)        │
│                        │ Obsidian URI Deep Link  │ [ O ] obsidian://open?... │
├────────────────────────┼─────────────────────────┼───────────────────────────┤
│ Files & Terminal Paths │ Absolute POSIX PDF Path │ [ P ] /Users/.../doc.pdf  │
│                        │ Shell-Escaped PDF Path  │ [ S ] '/Users/.../doc.pdf'│
│                        │ Vault Note Path         │ [ N ] ref/papers/doc.md   │
├────────────────────────┼─────────────────────────┼───────────────────────────┤
│ Citations & Metadata   │ Clean Display Title     │ [ T ] Plain text title    │
│                        │ Formatted Citation      │ [ C ] Author (Yr) "Title" │
│                        │ Primary Source URL      │ [ U ] https://arxiv...    │
│                        │ DOI / arXiv Identifier  │ [ D ] 1706.03762 / 10.... │
├────────────────────────┼─────────────────────────┼───────────────────────────┤
│ Excerpts & Intelligence│ Note/Highlight 1        │ [ 1 ] > "quote" + comment │
│ (Context-Aware)        │ Note/Highlight 2        │ [ 2 ] > "quote" + comment │
│                        │ Note/Highlight 3        │ [ 3 ] > "quote" + comment │
│                        │ All Notes Digest        │ [ A ] Full markdown notes │
│                        │ Executive Summary / TLDR│ [ B ] Abstract or Summary │
│                        │ GTD Reading Task Line   │ [ K ] - [ ] #task ...     │
└────────────────────────┴─────────────────────────┴───────────────────────────┘
```

### Detailed Breakdown of Copy Targets

#### 1. Identifiers & Links
- **`[ W ]` Obsidian Wiki Link**:
  - *Source*: `item.link`.
  - *Payload*: `[[ref/papers/vaswani2017|Attention Is All You Need]]` or `[[ref/chat/today_report]]`.
  - *Utility*: Pasting into Obsidian daily notes, project plans, or GTD inbox files.
- **`[ I ]` Marker Note ID (Slug)**:
  - *Source*: `item.stem` (which matches the page-1 marker note `- id: <slug>`).
  - *Payload*: `vaswani2017` or `ea_graph`.
  - *Utility*: SASE commands, `bob ref show <slug>`, agent prompts ("Focus on reference `ea_graph`"), and scripts.
- **`[ M ]` Standard Markdown Link**:
  - *Source*: Formatted from `item.title.text` and `item.urls.first ?? pdfURL.absoluteString`.
  - *Payload*: `[Attention Is All You Need](https://arxiv.org/abs/1706.03762)`.
  - *Utility*: GitHub pull request descriptions, GitLab issues, Slack, Google Docs, or Markdown apps where double-bracket wiki links are not supported.
- **`[ O ]` Obsidian URI (Deep Link)**:
  - *Source*: `ObsidianOpenURL.url(forAbsolutePath: noteURL.path)`.
  - *Payload*: `obsidian://open?vault=bob&file=ref%2Fpapers%2Fvaswani2017.md`.
  - *Utility*: External task managers (Things, Omnifocus, Reminders), browser bookmarks, or calendar invites to jump straight to the reference note in Obsidian.

#### 2. Files & Terminal Paths
- **`[ P ]` Absolute PDF Path**:
  - *Source*: `library.pdfURL(for: item)?.path`.
  - *Payload*: `/Users/bryan/bob/lib/papers/vaswani2017.pdf`.
  - *Utility*: Running CLI tools (`pdftotext`, `pdfimages`, `exiftool`, `lp`), Python scripts, or opening in alternative viewers.
- **`[ S ]` Shell-Escaped POSIX Path**:
  - *Source*: Single-quoted or backslash-escaped path.
  - *Payload*: `'/Users/bryan/bob/lib/papers/Attention Is All You Need.pdf'`.
  - *Utility*: Direct pasting into bash/zsh command line without syntax errors caused by unescaped spaces or brackets.
- **`[ N ]` Vault Note Path**:
  - *Source*: `item.id`.
  - *Payload*: `ref/papers/vaswani2017.md`.
  - *Utility*: SASE instructions, Git operations, and file inspection.

#### 3. Citations & Academic Metadata
- **`[ T ]` Clean Title**:
  - *Source*: `item.title.text`.
  - *Payload*: `Attention Is All You Need`.
  - *Utility*: Pasting cleanly without tags, wikilink delimiters, or formatting artifact characters.
- **`[ C ]` Formatted Academic Citation**:
  - *Source*: Composed from `item.author`, `item.published`, `item.title.text`, and `item.arxivID`/`doi`.
  - *Payload*: `Vaswani et al. (2017). "Attention Is All You Need". arXiv:1706.03762`.
  - *Utility*: Academic bibliographies, reading lists, research memos.
- **`[ U ]` Primary Source URL**:
  - *Source*: `item.urls.first`.
  - *Payload*: `https://arxiv.org/abs/1706.03762`.
  - *Utility*: Instant web sharing, opening in external browsers, verifying references.
- **`[ D ]` DOI / arXiv ID**:
  - *Source*: `item.doi ?? item.arxivID`.
  - *Payload*: `1706.03762` or `10.1145/3292500.3330964`.
  - *Utility*: Querying citation APIs, Semantic Scholar, CrossRef, or BibTeX generators.

#### 4. Reading Intelligence & Excerpts (Context-Aware)
- **`[ 1 ]`, `[ 2 ]`, `[ 3 ]` Specific Highlight & Note**:
  - *Source*: `RefsShowRow.commentedHighlights[index]`.
  - *Payload*:
    ```markdown
    > "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks..." (Page 1)
    
    This is where the transformer architecture departs from traditional RNNs.
    ```
  - *Utility*: Pulling exact quotes and reflections into agent prompts, research reports, or emails.
- **`[ A ]` All Notes & Highlights Digest**:
  - *Source*: Concatenation of all `commentedHighlights` into a structured Markdown block.
  - *Payload*: Multi-quote summary of the entire reading session.
  - *Utility*: Incorporating literature review findings directly into project documentation.
- **`[ B ]` Bottom-Line / Abstract**:
  - *Source*: `RefsInspectorContent.summary` (parsed by `RefsSummaryExtractor`).
  - *Payload*:
    ```markdown
    **Summary:**
    • We propose the Transformer, a model architecture eschewing recurrence and relying entirely on attention.
    • Experiments show superior quality while being more parallelizable.
    ```
  - *Utility*: Sharing TL;DRs with collaborators or summarizing background research.
- **`[ K ]` GTD Reading Task Line**:
  - *Source*: `item.task`.
  - *Payload*: `- [ ] #task Read [[ref/papers/vaswani2017|Attention Is All You Need]] ^ref-vaswani2017`.
  - *Utility*: Manually moving or cloning the reading task into another note.

---

## 4. Visual & Interaction Design Specification

To meet the requirement that the feature be **intuitive, reliable, and beautiful**, the interface must avoid generic menus and adopt a bespoke, translucent glass design that feels like a native HUD in macOS.

### 4.1 Layout & Spatial Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔍 Search references                                           All  142 refs│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────┐ ┌─────────────────────────────────────────────┐  │
│  │ READING               │ │                                             │  │
│  │ Attention Is All You  │ │   ┌─────────────────────────────────────┐   │  │
│  │                       │ │   │ 📋 COPY TO CLIPBOARD                │   │  │
│  │ READY                 │ │   │ Press single key to copy and close  │   │  │
│  │ FlashAttention-2      │ │   ├─────────────────────────────────────┤   │  │
│  │ LoRA: Low-Rank Adapt  │ │   │ IDENTIFIERS & LINKS                 │   │  │
│  │ DeepSeek-R1 Technical │ │   │ [ W ] Wiki Link   [[ref/papers/...  │   │  │
│  │                       │ │   │ [ I ] Marker ID   vaswani2017       │   │  │
│  │                       │ │   │ [ M ] Markdown    [Attention...     │   │  │
│  │                       │ │   │ [ O ] Obsidian URI obsidian://open  │   │  │
│  │                       │ │   ├─────────────────────────────────────┤   │  │
│  │                       │ │   │ PATHS & METADATA                    │   │  │
│  │                       │ │   │ [ P ] PDF Path    ~/bob/lib/pape... │   │  │
│  │                       │ │   │ [ C ] Citation    Vaswani (2017)    │   │  │
│  │                       │ │   │ [ U ] Source URL  https://arxiv...  │   │  │
│  │                       │ │   ├─────────────────────────────────────┤   │  │
│  │                       │ │   │ HIGHLIGHTS & NOTES                  │   │  │
│  │                       │ │   │ [ 1 ] Note 1 (p.1) "The dominant... │   │  │
│  │                       │ │   │ [ 2 ] Note 2 (p.3) "Self-attenti... │   │  │
│  │                       │ │   │ [ A ] All Notes   (2 highlights)    │   │  │
│  │                       │ │   ├─────────────────────────────────────┤   │  │
│  │                       │ │   │ esc Cancel         ↵ Default (Wiki) │   │  │
│  │                       │ │   └─────────────────────────────────────┘   │  │
│  │                       │ │                                             │  │
│  └───────────────────────┘ └─────────────────────────────────────────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ ↵ Open in Highlights  ⌘↵ Note  ⌥↵ Reveal  ^Y Copy  ⌘K Actions  esc Close    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Visual Tokens & Styling Specs

1. **Card Geometry**:
   - **Width**: `360 pt` fixed width.
   - **Corner Radius**: `12 pt` (concentric with the well radius).
   - **Background**: `.regularMaterial` with a subtle dark backdrop dimming overlay (`Color.black.opacity(0.18)`).
   - **Border**: `RoundedRectangle(cornerRadius: 12).stroke(Color.primary.opacity(0.10), lineWidth: 0.5)`.
   - **Shadow**: `shadow(color: .black.opacity(0.24), radius: 24, x: 0, y: 12)`.
2. **Keycap Badge (`RefsKeycapView`)**:
   - Resembles a physical mechanical keyboard keycap:
     - Dimensions: `24 pt` width $\times$ `20 pt` height.
     - Background: `.background.opacity(0.85)` with a subtle inner shadow.
     - Border: `0.5 pt` solid `.primary.opacity(0.18)`.
     - Corner Radius: `4.5 pt`.
     - Font: `.system(size: 11, weight: .bold, design: .monospaced)`.
     - Foreground: `Color.accentColor` or `.primary`.
3. **Live Value Previews**:
   - Right-aligned next to the option title.
   - Font: `.caption.monospaced()`.
   - Foreground: `.secondary` or `.tertiary`.
   - Truncation: Middle-truncated (`.truncationMode(.middle)`), max width `140 pt`.
4. **Motion & Feedback**:
   - **Entrance**: Scale from `0.96` to `1.0` with opacity `0` to `1` over `0.12 s` (`.easeOut`). Degrades to immediate paint if `accessibilityReduceMotion` is active.
   - **Selection**: Instant copy, soundless, card dismisses immediately (`0.08 s`), and `RefsFooter` displays the toast:
     `Copied Wiki Link` or `Copied Marker ID`.
   - **Escape**: Pressing `Esc`, `<ctrl+[>`, or `<ctrl+y>` again animates the card away and restores immediate search typing.

---

## 5. Technical Architecture & Implementation Blueprint

### 5.1 Modifications to `RefsKeyRouter.swift`

We expand `RefsKeyRouter` and `RefsKeyContext` to track palette presentation and map bare keys when the palette is active:

```swift
// In Sources/BobMacCapture/Refs/RefsKeyRouter.swift

public struct RefsKeyContext: Equatable, Sendable {
    public var queryIsEmpty: Bool
    public var scopeIsAll: Bool
    public var markedTextPresent: Bool
    public var listModeIsBrowse: Bool
    /// New: tracks whether the quick-copy palette is currently presented.
    public var copyPaletteVisible: Bool

    public init(
        queryIsEmpty: Bool = true,
        scopeIsAll: Bool = true,
        markedTextPresent: Bool = false,
        listModeIsBrowse: Bool = true,
        copyPaletteVisible: Bool = false
    ) {
        self.queryIsEmpty = queryIsEmpty
        self.scopeIsAll = scopeIsAll
        self.markedTextPresent = markedTextPresent
        self.listModeIsBrowse = listModeIsBrowse
        self.copyPaletteVisible = copyPaletteVisible
    }
}

public enum RefsCommand: Equatable, Sendable {
    // Existing commands...
    case open(RefsOpenTarget)
    case move(RefsMove)
    // ...
    
    // New Copy Palette Commands:
    case toggleCopyPalette
    case dismissCopyPalette
    case executeCopy(RefsCopyTarget)
}

public enum RefsCopyTarget: Equatable, Sendable {
    case wikiLink
    case markerID
    case markdownLink
    case obsidianURI
    case pdfPath
    case shellEscapedPath
    case notePath
    case title
    case citation
    case sourceURL
    case identifier
    case note(Int)
    case allNotes
    case summary
}
```

#### Routing Logic Inside `RefsKeyRouter.command`:

```swift
public static func command(
    keyCode: UInt16,
    modifiers: NSEvent.ModifierFlags,
    context: RefsKeyContext
) -> RefsCommand? {
    let flags = modifiers.intersection(.deviceIndependentFlagsMask)

    // 1. If Copy Palette is currently active, intercept bare keys:
    if context.copyPaletteVisible {
        switch keyCode {
        case KeyCode.escape:
            return .dismissCopyPalette
        case KeyCode.leftBracket where flags == .control:
            return .dismissCopyPalette
        case KeyCode.y where flags == .control:
            return .dismissCopyPalette
        case KeyCode.return, KeyCode.keypadEnter:
            return .executeCopy(.wikiLink) // Default return action
        // Bare mnemonic keys (no modifiers):
        case KeyCode.w where flags.isEmpty:
            return .executeCopy(.wikiLink)
        case KeyCode.i where flags.isEmpty:
            return .executeCopy(.markerID)
        case KeyCode.m where flags.isEmpty:
            return .executeCopy(.markdownLink)
        case KeyCode.o where flags.isEmpty:
            return .executeCopy(.obsidianURI)
        case KeyCode.p where flags.isEmpty:
            return .executeCopy(.pdfPath)
        case KeyCode.s where flags.isEmpty:
            return .executeCopy(.shellEscapedPath)
        case KeyCode.n where flags.isEmpty:
            return .executeCopy(.notePath)
        case KeyCode.t where flags.isEmpty:
            return .executeCopy(.title)
        case KeyCode.c where flags.isEmpty:
            return .executeCopy(.citation)
        case KeyCode.u where flags.isEmpty:
            return .executeCopy(.sourceURL)
        case KeyCode.d where flags.isEmpty:
            return .executeCopy(.identifier)
        case KeyCode.a where flags.isEmpty:
            return .executeCopy(.allNotes)
        case KeyCode.b where flags.isEmpty:
            return .executeCopy(.summary)
        case KeyCode.one where flags.isEmpty:
            return .executeCopy(.note(0))
        case KeyCode.two where flags.isEmpty:
            return .executeCopy(.note(1))
        case KeyCode.three where flags.isEmpty:
            return .executeCopy(.note(2))
        default:
            // Consume all other keys while palette is up so they don't leak into search!
            return .consume
        }
    }

    // 2. Normal Mode Key Router:
    switch keyCode {
    case KeyCode.y:
        // ^Y opens the copy palette if an item is selected
        if flags == .control {
            return .toggleCopyPalette
        }
        return nil
    case KeyCode.c:
        // Optional smart default: ⌘C when search bar has no selection
        if flags == .command && context.queryIsEmpty {
            return .executeCopy(.wikiLink)
        }
        return nil
    // ... rest of normal keyboard table
    }
}
```

### 5.2 State Machine in `RefsPanelModel.swift`

```swift
@MainActor
public final class RefsPanelModel: ObservableObject {
    @Published public private(set) var isCopyPalettePresented: Bool = false
    
    public func perform(_ command: RefsCommand) -> Bool {
        switch command {
        case .toggleCopyPalette:
            guard selectedItem != nil else { return false }
            isCopyPalettePresented.toggle()
            return true

        case .dismissCopyPalette:
            guard isCopyPalettePresented else { return false }
            isCopyPalettePresented = false
            return true

        case .executeCopy(let target):
            isCopyPalettePresented = false
            return executeCopyTarget(target)
            
        // existing commands...
        }
    }

    private func executeCopyTarget(_ target: RefsCopyTarget) -> Bool {
        guard let item = selectedItem else { return false }
        switch target {
        case .wikiLink:
            pasteboard.copy(item.link)
            showToast("Copied wiki link")
        case .markerID:
            pasteboard.copy(item.stem)
            showToast("Copied marker ID (\(item.stem))")
        case .markdownLink:
            let url = item.urls.first ?? library.pdfURL(for: item)?.absoluteString ?? ""
            pasteboard.copy("[\(item.title.text)](\(url))")
            showToast("Copied markdown link")
        case .obsidianURI:
            if let noteURL = library.noteURL(for: item),
               let deep = ObsidianOpenURL.url(forAbsolutePath: noteURL.path) {
                pasteboard.copy(deep.absoluteString)
                showToast("Copied Obsidian URL")
            }
        case .pdfPath:
            if let pdf = library.pdfURL(for: item) {
                pasteboard.copy(pdf.path)
                showToast("Copied PDF path")
            }
        case .shellEscapedPath:
            if let pdf = library.pdfURL(for: item) {
                let escaped = "'" + pdf.path.replacingOccurrences(of: "'", with: "'\\''") + "'"
                pasteboard.copy(escaped)
                showToast("Copied shell path")
            }
        case .notePath:
            pasteboard.copy(item.id)
            showToast("Copied note path")
        case .title:
            pasteboard.copy(item.title.text)
            showToast("Copied title")
        case .citation:
            let citation = formatCitation(for: item)
            pasteboard.copy(citation)
            showToast("Copied citation")
        case .sourceURL:
            if let url = item.urls.first {
                pasteboard.copy(url)
                showToast("Copied source URL")
            }
        case .identifier:
            let id = item.doi ?? item.arxivID ?? item.stem
            pasteboard.copy(id)
            showToast("Copied identifier")
        case .note(let index):
            guard let notes = currentInspector?.notes, notes.indices.contains(index) else {
                return false
            }
            let note = notes[index]
            var text = ""
            if let quote = note.quote { text += "> \"\(quote)\"\n\n" }
            if let comment = note.comment { text += comment }
            pasteboard.copy(text)
            showToast("Copied note #\(index + 1)")
        case .allNotes:
            guard let notes = currentInspector?.notes, !notes.isEmpty else { return false }
            let all = notes.compactMap { n -> String? in
                var s = ""
                if let q = n.quote { s += "> \"\(q)\"\n" }
                if let c = n.comment { s += "\(c)\n" }
                return s.isEmpty ? nil : s
            }.joined(separator: "\n---\n\n")
            pasteboard.copy(all)
            showToast("Copied all notes")
        case .summary:
            if let summary = currentInspector?.summary {
                var text = summary.label + ":\n"
                if let p = summary.paragraph { text += p + "\n" }
                for b in summary.bullets { text += "• \(b)\n" }
                pasteboard.copy(text)
                showToast("Copied summary")
            }
        }
        return true
    }
}
```

### 5.3 Escape Ladder & Resign Integration
In `RefsPanelModel.swift`, the Esc key operates via an established hierarchical ladder:
1. Dismiss active error/warning banner.
2. **Dismiss active Copy Palette** (New).
3. If query is non-empty, clear query.
4. If scope is not `.all`, reset scope to `.all`.
5. Close panel.

This ensures pressing `Esc` while the palette is open cleanly closes *only* the palette, without dismissing the entire Refs panel.

---

## 6. Comparison of Implementation Approaches

| Dimension | Approach A: Direct `NSMenu` (Naive) | Approach B: Expanded ⌘K Menu | Approach C: SwiftUI Glass HUD (Recommended) |
| :--- | :--- | :--- | :--- |
| **Trigger** | `<ctrl+y>` $\rightarrow$ pops `NSMenu` | ⌘K $\rightarrow$ 15+ menu items | `<ctrl+y>` $\rightarrow$ reveals HUD Card |
| **Selection Speed** | Multi-key (type-ahead / arrows + enter) | Slow (arrows through mixed actions) | **Instantaneous (single unmodified key)** |
| **Visual Aesthetics** | Gray OS-native menu | Gray OS-native menu | **Liquid glass, custom keycaps, concentric** |
| **Payload Previews** | None (only titles) | None (only titles) | **Live middle-truncated text preview** |
| **Runloop Impact** | Blocks thread in `menu.popUp` | Blocks thread in `menu.popUp` | **Zero blocking; pure SwiftUI state** |
| **Testability** | Hard (requires UI / event synthesis) | Hard | **100% headless unit testable** |
| **Thin-Client Safety** | High | High | **High (consumes existing models)** |

---

## 7. Verification & Testing Strategy

To adhere to the rigorous engineering standards set in `bob-mac-capture`:

1. **Key Router Unit Tests (`RefsKeyRouterTests.swift`)**:
   - Verify `<ctrl+y>` routes to `.toggleCopyPalette`.
   - Verify that when `context.copyPaletteVisible == true`:
     - Bare letters `w`, `p`, `i`, `1`, etc. return `.executeCopy(...)`.
     - `escape`, `<ctrl+[>`, and `<ctrl+y>` return `.dismissCopyPalette`.
     - Unassigned letters return `.consume` (ensuring no characters leak into the search filter).
2. **Model Unit Tests (`RefsPanelModelTests.swift`)**:
   - Verify `executeCopyTarget` correctly invokes `pasteboard.copy(...)` with the exact string formatting for each target.
   - Verify `model.toast` is updated with the corresponding confirmation message.
   - Verify the Esc ladder: pressing Esc with palette open dismisses only the palette.
3. **Design Snapshot Tests (`RefsPanelDesignTests.swift`)**:
   - Render static preview fixtures with `isCopyPalettePresented = true` in both Light and Dark mode, as well as with `accessibilityReduceTransparency` enabled.

---

## 8. Summary of Recommended Solution

1. **Trigger**: Map `<ctrl+y>` in `RefsKeyRouter` to `.toggleCopyPalette`.
2. **Interface**: Render a centered, concentric SwiftUI HUD Card (`RefsCopyPaletteView`) overlaying the well content with a subtle backdrop blur.
3. **Interaction**: Single bare keypress triggers the copy action, copies to `pasteboard`, triggers a 1.5 s toast in `RefsFooter`, and immediately dismisses the card.
4. **Key Taxonomy**:
   - `[ W ]` Wiki Link
   - `[ I ]` Marker Note ID
   - `[ M ]` Markdown Link
   - `[ O ]` Obsidian URI
   - `[ P ]` PDF Path
   - `[ S ]` Shell Path
   - `[ T ]` Title
   - `[ C ]` Citation
   - `[ U ]` Source URL
   - `[ 1..3 ]` Notes / Highlights
   - `[ A ]` All Notes
   - `[ B ]` Bottom-line / Summary
5. **Escape Ladder**: `Esc` or `<ctrl+y>` dismisses the palette harmlessly.
6. **Smart ⌘C**: Allow `⌘C` when no search text is selected to copy the default Wiki Link, harmonizing native macOS habits with power-user ergonomics.
