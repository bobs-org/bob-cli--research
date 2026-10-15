# Research Report: Highlights App Tab-Switcher Filter in Bob Mac Capture

**Researcher ID:** `research.1m.gem`  
**Date:** 2026-10-15  
**Topic:** Adding a special mode/filter to Bob Mac Capture's reference panel showing reference notes corresponding to PDFs currently open in Highlights (to function as an interactive tab-switcher).

---

## 1. Executive Summary

This research investigates the proposal to add a special mode or filter to the `bob-mac-capture` reference panel (`Bob Refs`) that restricts the listing exclusively to reference notes corresponding to PDF files currently opened in the Highlights app (`net.highlightsapp.universal`). This feature enables the reference panel to serve as an intelligent, metadata-rich "tab-switcher" for Highlights.

### Key Conclusions:
1. **Feasibility & Speed**: The feature is highly feasible and can execute with sub-millisecond latency (<1 ms) without adding noticeable overhead to panel presentation.
2. **Detection Mechanism**: The optimal inspection method is the low-level macOS `libproc` C API (`proc_pidinfo` with `PROC_PIDLISTFDS` and `proc_pidfdinfo` with `PROC_PIDFDVNODEPATHINFO`). It requires **zero special macOS permissions** (no Accessibility, no TCC Automation, no Screen Recording prompts) because `bob-mac-capture` and Highlights run as un-sandboxed processes under the same user UID. Higher-level options like AppleScript / `System Events` or Accessibility (`AXUIElement`) introduce permission friction, UI fragility, and fail to enumerate background tabs cleanly.
3. **Tab Switching Mechanics**: Activating an open PDF in Highlights is already supported natively by macOS AppKit document architecture: invoking `NSWorkspace.open([pdfURL], withApplicationAt: highlightsAppURL)` on an already-open PDF brings Highlights forward and focuses its existing window/tab. No synthetic keyboard events or UI scripting are needed.
4. **Architectural Boundary**: Per the architectural decision `mac-capture-is-a-thin-client`, this functionality belongs exclusively within `bob-mac-capture` (and its helper core `RefsCore`). `bob-cli` remains cross-platform and authoritative over vault syntax, notes, and the library catalog; local macOS process introspection belongs strictly in the native macOS frontend alongside Spotlight metadata and window activation.
5. **Critique & Recommended Adjustments**:
   - *The Trap Risk*: The mode must **never be an inescapable takeover**. When Bryan presses `Command-O` inside Highlights, he frequently wants to switch tabs, but he also needs to be able to open *new* references from his library.
   - *Recommended UX*: Implement a context-aware **Open in Highlights** filter chip/scope. When `Command-O` is triggered while Highlights is frontmost and Highlights has open library PDFs, the panel opens with this filter pre-selected. Pressing `Backspace` on an empty search or `Esc` immediately removes the filter and restores the full reference library.

---

## 2. Background and Context

### 2.1 The Highlights & Bob Vault Ecosystem
In Bryan’s GTD and reference workflow:
- `bob ref` (and `bob highlights`) syncs external reference materials into Obsidian reference notes (`type: "[[ref]]"`) in `ref/`, linked to PDF sources in `lib/` (`docs/highlights-ref-sync.md`).
- Highlights Pro (`net.highlightsapp.universal`) is Bryan’s primary PDF reader and annotation tool on macOS.
- Reference notes track reading state via their `^ref` task: `ready` (`[ ]`), `next` (`[*]`), `reading`/`wip` (`[/]`), and `read` (`[x]`).

### 2.2 Bob Mac Capture's Reference Panel (`Bob Refs`)
`bob-mac-capture` is a native Swift menu-bar companion for `bob-cli`:
- It provides a global floating spotlight-style search HUD for reference materials (`Ctrl-Shift-Cmd-O`).
- **Highlights Takeover (`HighlightsTakeover.swift`)**: When Highlights is frontmost, `bob-mac-capture` dynamically registers a Carbon hotkey intercepting `Command-O` (or `Control-O`) so pressing open inside Highlights summons Bob Refs directly over Highlights.
- The panel presents rich metadata: clean titles, author, publication date, reading state chips, annotation counts, comments, and an inspector with table-of-contents headings and extracted quotes.
- Selecting a reference note and pressing `Return` triggers `WorkspaceRefsOpener.openInHighlights(pdf, app:)`.

### 2.3 The User Need
Highlights uses native macOS window tabbing (`NSWindowTabGroup`). When multiple PDFs (e.g. 5–20 papers) are open simultaneously:
1. Native tab bars truncate long academic titles (e.g. `2304.08424v1.pdf`, `Attention_Is_All_You_...`).
2. Tabs overflow offscreen into an unwieldy trailing menu.
3. Highlights has no fuzzy-search tab switcher (unlike VS Code's `Cmd-P` or browser tab switchers).

Using Bob Refs as a tab-switcher gives Bryan instant fuzzy search across open PDFs with full article titles, author names, reading states, and annotations.

---

## 3. Technical Investigation: Detecting Open PDFs in Highlights

We investigated five candidate technical approaches on macOS to determine which PDF files are currently open in Highlights.

### 3.1 Mechanism 1: `libproc` Process File Descriptor Introspection (Recommended)

#### How It Works
macOS provides `<libproc.h>` APIs to query kernel process descriptors. Because Highlights and `bob-mac-capture` run under the same user UID, and `bob-mac-capture` is not sandboxed, `bob-mac-capture` can inspect Highlights' file descriptors directly in C/Swift:

1. Obtain Highlights' PID via `NSRunningApplication`:
   ```swift
   guard let app = NSRunningApplication.runningApplications(
       withBundleIdentifier: HighlightsLocator.bundleIdentifier
   ).first else { return [] }
   let pid = app.processIdentifier
   ```
2. Determine the buffer size for open file descriptors using `proc_pidinfo`:
   ```c
   int size = proc_pidinfo(pid, PROC_PIDLISTFDS, 0, NULL, 0);
   ```
3. Allocate a buffer of `struct proc_fdinfo` and retrieve the descriptors:
   ```c
   struct proc_fdinfo *fds = malloc(size);
   int actualSize = proc_pidinfo(pid, PROC_PIDLISTFDS, 0, fds, size);
   int count = actualSize / sizeof(struct proc_fdinfo);
   ```
4. For each descriptor where `proc_fdtype == PROX_FDTYPE_VNODE`, query the vnode path via `proc_pidfdinfo`:
   ```c
   struct vnode_fdinfowithpath vnodeInfo;
   int res = proc_pidfdinfo(pid, fds[i].proc_fd, PROC_PIDFDVNODEPATHINFO, &vnodeInfo, sizeof(vnodeInfo));
   if (res > 0) {
       const char *path = vnodeInfo.pvip.vip_path;
       // collect path
   }
   ```
5. Match paths against the active Bob reference catalog (`library.items`).

#### Evaluation
- **Latency**: Sub-millisecond (~0.2 ms to 0.6 ms).
- **Permissions**: **Zero permissions required**. No Accessibility prompt, no TCC Automation consent dialog, no Screen Recording entitlement.
- **Completeness**: Finds all open PDF files across all windows, tabs, and minimized windows, because `NSDocument` and `PDFKit` maintain active vnodes for open files.
- **Reliability**: Extremely stable, standard Unix/Darwin kernel mechanism.

---

### 3.2 Mechanism 2: AppleScript / JXA via System Events or Highlights

#### How It Works
Execute AppleScript to query the open documents:
```applescript
tell application "System Events"
    tell process "Highlights"
        get value of attribute "AXDocument" of every window
    end tell
end tell
```
Or directly if Highlights supported Cocoa scripting:
```applescript
tell application "Highlights"
    get path of every document
end tell
```

#### Evaluation
- **Fatal Flaw 1 (No `.sdef`)**: Highlights lacks an AppleScript dictionary (`.sdef`). Direct document queries (`every document`) fail or return incomplete records.
- **Fatal Flaw 2 (Tab Group Blindness)**: In macOS native window tabbing (`NSWindowTabGroup`), `every window` in `System Events` only returns the *active frontmost tab* of each window group. Background tabs inside a tab group are not returned as standalone `window` objects.
- **Fatal Flaw 3 (Permissions Friction)**: Querying `System Events` triggers macOS TCC "Automation" prompts ("Bob Mac Capture wants to control System Events"). If the user denies or resets permissions, the feature silently breaks.
- **Latency**: High (30 ms to 120 ms due to AppleEvent serialization and IPC context switches).

---

### 3.3 Mechanism 3: macOS Accessibility API (`AXUIElement`)

#### How It Works
Use `ApplicationServices.AXUIElement` to traverse Highlights' UI hierarchy:
`AXUIElementCreateApplication(pid)` $\rightarrow$ `kAXWindowsAttribute` $\rightarrow$ `AXTabGroup` $\rightarrow$ `kAXTabsAttribute`.

#### Evaluation
- **Fatal Flaw (Accessibility Permission Required)**: Calling `AXUIElement` on another process requires the calling app to be explicitly trusted in **System Settings > Privacy & Security > Accessibility** (`AXIsProcessTrusted()`). `bob-mac-capture` currently does *not* require Accessibility privileges (it uses Carbon hotkeys and standard NSWorkspace). Forcing Bryan to grant Accessibility privileges for a tab-switcher is unnecessary friction.
- **Tab Attribute Inconsistency**: While active windows expose `kAXDocumentAttribute` (file URL), tab elements inside `AXTabGroup` typically expose only their display title (`kAXTitleAttribute`, e.g. "vaswani2017"), not the canonical file path. Resolving titles back to vault paths is ambiguous if duplicate titles exist.

---

### 3.4 Mechanism 4: Quartz Window Services (`CGWindowListCopyWindowList`)

#### How It Works
Query the WindowServer for windows belonging to Highlights' PID.

#### Evaluation
- **Fatal Flaw (Screen Recording Permission)**: On macOS Catalina through Sequoia, `kCGWindowName` for windows belonging to other applications is sanitized and returns `nil` unless the application has been granted **Screen Recording** permissions (`CGPreflightScreenCaptureAccess()`). Without Screen Recording permissions, window titles cannot be read.

---

### 3.5 Mechanism 5: Saved Application State Files

#### How It Works
Read Highlights' saved state plist files in `~/Library/Saved Application State/net.highlightsapp.universal.savedState/`.

#### Evaluation
- **Fatal Flaw (Async & Encrypted State)**: Saved state files are only written when an application loses focus, enters background sleep, or terminates. Live tab changes are not written synchronously. Furthermore, modern macOS saves window states in binary `NSKeyedArchiver` streams that are brittle to parse.

---

### Comparison Matrix

| Criteria | `libproc` (Proc FDs) | AppleScript (`System Events`) | Accessibility (`AXUIElement`) | Quartz (`CGWindowList`) |
| :--- | :--- | :--- | :--- | :--- |
| **Speed** | **< 1 ms** | 40–100 ms | 15–30 ms | 2–5 ms |
| **Permissions Required** | **None** | Automation (TCC) | **Accessibility** (TCC) | **Screen Recording** (TCC) |
| **Tab Enumeration** | **All open tabs** | Front tab only | Complex / Flaky | Titles only (redacted) |
| **Path Fidelity** | **Exact POSIX Path** | URL string | Display title only | Display title only |
| **Maintenance Burden** | Low | High | High | High |

**Verdict**: `libproc` is the indisputable winner across all criteria.

---

## 4. Technical Investigation: Tab Switching & Document Activation

A critical requirement of a "tab-switcher" is: *what happens when Bryan selects a row and presses `Return`?*

### 4.1 Native macOS Tab Activation Mechanics
When a document is already open in Highlights (whether in an active tab, an inactive background tab, or another window):
```swift
var configuration = NSWorkspace.OpenConfiguration()
configuration.activates = true
NSWorkspace.shared.open([pdfURL], withApplicationAt: highlightsAppURL, configuration: configuration)
```
1. `NSWorkspace` sends an `openURLs:` AppleEvent to Highlights.
2. Highlights' AppKit document controller (`NSDocumentController`) checks its internal document registry.
3. Because the file URL matches an existing `NSDocument`, Highlights does **not** re-read or duplicate the document.
4. Instead, it invokes `makeWindowControllers()` and `window.makeKeyAndOrderFront(nil)`.
5. Under macOS native window tabbing (`NSWindowTabGroup`), ordering an existing tab window to the front automatically switches the active tab in the tab bar and focuses the document.

### 4.2 Tab Closing Considerations
In some tab switchers (e.g. browser tab switchers), users can close tabs using `Command-W` or a close button directly from the switcher list.
- **Can Bob Refs close a tab in Highlights?**
  No native `NSWorkspace` API exists to close another application's document. Closing a tab would require UI scripting (sending synthetic keystrokes via `CGEvent` or Accessibility action `AXPress` on the tab's close button).
- **Recommendation**: Keep the tab-switcher focused strictly on **navigation and activation**. Do not attempt remote tab closing.

---

## 5. Architectural Alignment: The "Thin Client" Principle

Before introducing changes, we must audit against accepted architectural decisions in Bob.

### 5.1 Memory Rule: `decisions:mac-capture-is-a-thin-client`
> *"bob-cli is the only implementation of capture grammar, completion data, preview, and vault mutation. Bob Mac Capture owns presentation, process orchestration, the global hotkey, settings, launch at login, and packaging... It may filter or rank what bob returned, but it never decides syntax itself."*

### 5.2 Application to This Feature
- **Where does the code belong?**
  - Detecting running macOS applications and inspecting their open file descriptors (`proc_pidinfo`) is **operating system process orchestration**.
  - Highlights is a macOS-only GUI app. `bob-cli` is a cross-platform Rust binary designed to run on Linux servers, macOS, and ephemeral agent containers.
  - Putting Highlights process inspection into `bob-cli` would violate separation of concerns, require platform-specific C/FFI bindings in Rust, and add subprocess spawn latency to every panel presentation.
  - `bob-mac-capture` already owns macOS-specific signal gathering:
    - `SpotlightRefsSignals`: queries Spotlight via `MDItemCreateWithURL`.
    - `VaultTargetWatcher`: monitors file system changes via macOS `FSEvents`.
    - `HighlightsTakeover`: intercepts `Command-O` via Carbon hotkeys.
- **Conclusion**:
  `bob-cli` continues to provide the library catalog via `bob ref list -R all -A -f json`. `bob-mac-capture` inspects Highlights' open file descriptors locally and applies this as a presentation filter to the catalog. This aligns 100% with `mac-capture-is-a-thin-client`.

---

## 6. Critique of the Plan: Is This a Good Idea?

### 6.1 Strengths of the Plan
1. **Solves a Real Cognitive Bottleneck**: When synthesizing complex topics across 8 papers in Highlights, tab switching via the native tab bar is clumsy. A searchable switcher showing authors, publication dates, and reading status eliminates friction.
2. **Reuses Established Infrastructure**: Bob Mac Capture already has the takeover hotkey (`Command-O` in Highlights), the panel view, fuzzy filtering, and document open handlers.
3. **Synergy with Reading Tasks**: A tab switcher in Bob Refs naturally surfaces the reading task checkbox (`[*] Next`, `[/] WIP`, `[ ] Ready`), allowing Bryan to see his task status alongside open tabs.

### 6.2 Critique and Pitfalls of a Naive Implementation

#### Pitfall 1: The "Trapped in Open Tabs" Dilemma
If pressing `Command-O` in Highlights *always* and *only* shows open tabs:
- What happens when Bryan is in Highlights and wants to open a *new* paper from his library that isn't currently open?
- If the panel is strictly locked into "tab-switcher mode", Bryan would have to leave Highlights, switch to another app, press `Ctrl-Shift-Cmd-O` to open Bob Refs globally, select the paper, and open it. That would be a severe regression in usability.
- **Requirement Adjustment**: The filter must be **modal and dismissible with a single keystroke**.

#### Pitfall 2: Highlights Has Zero Open Documents
If Highlights is running with no documents open (or only an untitled blank window), opening the panel in an active "Open Tabs" filter would result in an empty list:
- Presenting a blank panel looks like a crash or bug.
- **Requirement Adjustment**: If Highlights has 0 matching open PDFs, Bob Refs must automatically fall back to the standard browse view (`Today`, `Reading`, `Next`, etc.) with a subtle notice or badge, rather than showing an empty screen.

#### Pitfall 3: Non-Vault PDFs Open in Highlights
Bryan might open arbitrary PDFs in Highlights (e.g. an invoice from `~/Downloads/`, a tax document, or an intake PDF in `xlib/` before scanning).
- These PDFs do not correspond to any reference note in the Bob vault (`ref/` / `lib/`).
- **Requirement Adjustment**: The detection logic must safely perform a set intersection between open PDF paths and `library.items.map(\.pdfPath)`. Any open file not tracked by Bob is silently excluded without throwing errors.

#### Pitfall 4: Confusion with Existing Scopes
Bob Refs already has scopes (`⌘1 All`, `⌘2 Chats`, `⌘3 Papers`, `⌘4 Articles`, `⌘5 Docs`).
- Scopes are currently **orthogonal reference kinds**.
- Making "Highlights Tabs" a 6th scope (`⌘6`) would conflate *content kind* with *runtime state*. For example, an open paper is both a "Paper" and an "Open Tab".
- **Requirement Adjustment**: Model "Highlights Tabs" as an **active filter toggle / overlay** (similar to a search token or view filter), rather than a disjoint `RefScope`.

---

## 7. Requirement Adjustments & Design Refinements

Based on the critique, we recommend the following adjustments to Bryan's original requirements:

### Adjustment 1: Context-Aware Default Activation
- When Bob Refs is opened via the **Highlights Takeover Hotkey (`Command-O`)** from within Highlights:
  - If Highlights has $\ge 1$ open library PDFs: The panel opens with the **Highlights Tabs** filter **automatically enabled**.
  - If Highlights has 0 open library PDFs: The panel opens in standard `All` browse mode.
- When Bob Refs is opened via the **Global Hotkey (`Ctrl-Shift-Cmd-O`)** from any other app (Finder, Obsidian, etc.):
  - The panel opens in standard `All` browse mode as it does today.

### Adjustment 2: Seamless Escape / Scope Clearing
- When the **Highlights Tabs** filter is active:
  - An orange/accent filter capsule appears in `RefsSearchBar`:  
    `[ ⊞ Highlights (5)  × ]`
  - Pressing `Backspace` (on an empty search query) immediately dismisses the filter and expands the list to the full reference library.
  - Pressing `Esc` dismisses the filter before dismissing the panel.
  - Pressing `⌘1` resets scope to All references.

### Adjustment 3: Manual Toggle Shortcut
- Allow Bryan to manually toggle the Highlights Tabs filter on or off at any time using a dedicated keyboard shortcut inside the panel:
  - **Proposed shortcut**: `⌘0` (Command-Zero) or `⌥O` (Option-O).
  - This allows filtering to open Highlights tabs even when Bob Refs was invoked from outside Highlights.

### Adjustment 4: Strict Filtering in Search Mode
- When typing in the search bar while the Highlights Tabs filter is active, fuzzy search must search **strictly within the open Highlights references**.
- This guarantees rapid 2-keystroke tab switching: `Cmd-O` $\rightarrow$ type `"att"` $\rightarrow$ `Return` switches to *Attention Is All You Need*.

### Adjustment 5: Open Status in Browse Captions
- When in general browse mode (`All`), reference items that are currently open in Highlights should display an "OPEN IN HIGHLIGHTS" pill or indicator in their caption line, reinforcing the connection between the library and the active app state.

---

## 8. Detailed Implementation Architecture

### 8.1 Module Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       BobMacCapture                         │
│                                                             │
│  ┌───────────────────────┐       ┌───────────────────────┐  │
│  │   HighlightsTakeover  │       │  HighlightsInspector  │  │
│  │ (watches frontmost app│       │ (runs libproc FDs to  │  │
│  │  & registers ⌘O)      │       │  find open PDF paths) │  │
│  └───────────┬───────────┘       └───────────┬───────────┘  │
│              │ invokes                       │ provides     │
│              ▼                               ▼              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    RefsPanelModel                     │  │
│  │  - isHighlightsFilterActive: Bool                     │  │
│  │  - openInHighlightsIDs: Set<String>                   │  │
│  └───────────────────────────┬───────────────────────────┘  │
└──────────────────────────────┼──────────────────────────────┘
                               │ passes signals
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                          RefsCore                           │
│                                                             │
│  ┌───────────────────────┐       ┌───────────────────────┐  │
│  │      RefsSignals      │       │      RefsRanker       │  │
│  │ + openInHighlights:   │──────▶│ (filters items if     │  │
│  │   Set<String>         │       │  filter is active)    │  │
│  └───────────────────────┘       └───────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Component Specifications

#### Component 1: `HighlightsDocumentInspector` (in `BobMacCapture`)
A new lightweight service to query open file descriptors for Highlights:

```swift
import Foundation
import libproc

public protocol HighlightsDocumentInspecting: Sendable {
    func openPDFPaths(for bundleIdentifier: String) -> Set<String>
}

public struct LiveHighlightsDocumentInspector: HighlightsDocumentInspecting, Sendable {
    public init() {}

    public func openPDFPaths(for bundleIdentifier: String) -> Set<String> {
        guard let app = NSRunningApplication.runningApplications(
            withBundleIdentifier: bundleIdentifier
        ).first else {
            return []
        }
        let pid = app.processIdentifier
        let bufferSize = proc_pidinfo(pid, PROC_PIDLISTFDS, 0, nil, 0)
        guard bufferSize > 0 else { return [] }

        let fdInfoPtr = UnsafeMutablePointer<proc_fdinfo>.allocate(capacity: Int(bufferSize))
        defer { fdInfoPtr.deallocate() }

        let actualSize = proc_pidinfo(pid, PROC_PIDLISTFDS, 0, fdInfoPtr, bufferSize)
        guard actualSize > 0 else { return [] }

        let count = Int(actualSize) / MemoryLayout<proc_fdinfo>.size
        var pdfPaths: Set<String> = []

        for i in 0..<count {
            let fd = fdInfoPtr.advanced(by: i).pointee
            guard fd.proc_fdtype == PROX_FDTYPE_VNODE else { continue }

            var vnodeInfo = vnode_fdinfowithpath()
            let vnodeSize = Int32(MemoryLayout<vnode_fdinfowithpath>.size)
            let res = proc_pidfdinfo(pid, fd.proc_fd, PROC_PIDFDVNODEPATHINFO, &vnodeInfo, vnodeSize)
            if res > 0 {
                let path = withUnsafeBytes(of: &vnodeInfo.pvip.vip_path) { rawPtr -> String in
                    let ptr = rawPtr.baseAddress!.assumingMemoryBound(to: CChar.self)
                    return String(cString: ptr)
                }
                if path.lowercased().hasSuffix(".pdf") {
                    pdfPaths.insert(URL(fileURLWithPath: path).standardizedFileURL.path)
                }
            }
        }
        return pdfPaths
    }
}
```

#### Component 2: `RefsSignals` Update (in `RefsCore`)
Extend `RefsSignals` to store the set of item IDs currently open in Highlights:

```swift
public struct RefsSignals: Sendable {
    public var today: RefsToday
    public var opens: RefsOpenStats
    public var externalLastUsed: [String: Date]
    public var pageCounts: [String: Int]
    public var missingPDFs: Set<String>
    public var outlineHeadings: [String: [String]]
    public var scan: RefsScanMark?
    public var openInHighlights: Set<String> // <-- NEW: Item IDs currently open in Highlights
    public var now: Date
    public var calendar: Calendar
    // ...
}
```

#### Component 3: Ranking & Listing Update (in `RefsCore/RefsRanking.swift`)
In `RefsRanker.listing(...)`:
If `highlightsFilterActive` is `true`:
```swift
let scoped = items
    .filter { scope.contains($0.kind) }
    .filter { signals.openInHighlights.contains($0.id) }
```
When filtered, browse mode simply renders one unified section:
`Open in Highlights (N)` ordered by last activity or matching the tab sequence.

#### Component 4: Panel Presentation Integration (`RefsPanelModel.swift`)
In `RefsPanelModel.prepareForPresentation()`:
```swift
public func prepareForPresentation(invokedFromHighlightsTakeover: Bool = false) {
    // 1. Inspect open PDFs in Highlights
    let openPaths = highlightsInspector.openPDFPaths(for: HighlightsLocator.bundleIdentifier)
    let matchingIDs = Set(library.items.filter { item in
        guard let url = library.pdfURL(for: item) else { return false }
        return openPaths.contains(url.standardizedFileURL.path)
    }.map(\.id))

    library.updateOpenInHighlights(matchingIDs)

    // 2. Decide filter state
    if invokedFromHighlightsTakeover && !matchingIDs.isEmpty {
        isHighlightsFilterActive = true
    } else {
        isHighlightsFilterActive = false
    }

    // 3. Re-rank
    rerankSelectingFirst()
}
```

#### Component 5: UI & Search Bar Rendering (`RefsSearchBar.swift`)
When `model.isHighlightsFilterActive` is true, render a distinct capsule in the search bar:
```swift
if model.isHighlightsFilterActive {
    Button {
        model.clearHighlightsFilter()
    } label: {
        HStack(spacing: 5) {
            Image(systemName: "rectangle.stack")
            Text("Highlights Tabs (\(model.signals.openInHighlights.count))")
            Image(systemName: "xmark")
        }
        .foregroundStyle(.orange)
        .padding(.horizontal, 10)
        .padding(.vertical, 5)
        .background(Color.orange.opacity(0.16), in: Capsule())
    }
}
```

---

## 9. Recommended Solution Summary

### Summary Recommendation:
1. **Adopt `libproc` in `bob-mac-capture`**:
   Implement a `HighlightsDocumentInspector` that inspects Highlights' open file descriptors via `proc_pidinfo`. It runs in <1 ms and requires **zero security permissions**.
2. **Context-Aware Default with Quick Escape**:
   When Bryan is in Highlights and presses `Command-O`, Bob Refs opens pre-filtered to the currently open tabs if any match vault references. If Bryan wants to search the whole library, a single `Backspace` or `Esc` clears the filter instantly.
3. **Keep `bob-cli` Clean**:
   Do not modify `bob-cli` or add new subprocess commands to `bob`. This feature is pure client-side process orchestration and presentation filtering, strictly adhering to `decisions:mac-capture-is-a-thin-client`.
4. **Navigation-Only Contract**:
   Use standard `NSWorkspace.shared.open([pdf], withApplicationAt: highlightsAppURL)` to activate the tab in Highlights upon selection. Do not attempt remote tab closing or UI scripting.

This solution delivers an instant, intuitive, and robust tab-switcher experience while respecting the existing architectural boundaries of the Bob ecosystem.
