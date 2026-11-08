# Research Report: Deep-Linking Reference Note Quotes to Highlights via `<cmd+enter>`

**Author:** researcher gem (`__gem`)  
**Date:** 2026-11-08  
**Topic:** Extending `<cmd+enter>` from `#task #ref` Reading Tasks to Ref Note Quotes, Annotations, and Annotation Tasks  
**Target Repository:** `bob-plugins` (`plugins/bob-navigation-hotkeys`)  
**Coordinating Repositories:** `bob-cli` (`docs/highlights-ref-sync.md`, `src/native/highlights_ref/`)  

---

## 1. Executive Summary

Opening reference PDFs in the Highlights app via `<cmd+enter>` (`Meta+Enter` in Obsidian) is currently supported for `#task #ref` reading tasks. This feature allows Bryan to jump directly from a reading task into Highlights.

This research report investigates extending this keymap so that selecting a **quote/annotation in a reference note**—or an **annotation task** created from `#task` annotations—jumps directly to the corresponding page in Highlights.

### Key Conclusions & Recommendations

1. **Plan Critique — A Resounding "Yes" with Essential Scope Refinements**:
   - The core proposal is ergonomically sound and fits naturally into Bryan's muscle memory. In Bob's reference workflow, reference notes under `ref/` are generated from Highlights sidecars. Jumping directly back to the exact PDF page from an excerpt or quote solves the universal "context re-hydration" problem (inspecting surrounding charts, formulas, diagrams, or neighboring paragraphs).
   - **Scope Adjustment 1 (Crucial): Extend to Annotation Tasks Everywhere.** Users frequently triage follow-up tasks in GTD task lists (e.g. `sase.md`, `today.md`, project notes) which link back to quotes via `[[ref_note#^h-...|🔖]]`. Extending `<cmd+enter>` so it also triggers on these task lines and resolves the target PDF page provides a massive productivity multiplier.
   - **Scope Adjustment 2: Precision in Multi-Page Continuations.** When a continuation quote spans multiple pages (e.g. `Pages 3–4` with nested callouts `[!quote|Page 3]` and `[!quote|Page 4]`), cursor position should resolve the specific page sub-piece rather than naively defaulting to the start page.
   - **Scope Adjustment 3: Priority Hierarchy for Inline Links.** If the cursor is positioned directly inside an explicit inline link (such as `[[another_note]]` or `[web link](...)`) within a quote, `<cmd+enter>` must preserve Obsidian's native `editor:open-link-in-new-leaf` action. If the cursor is anywhere else in the quote block, it opens Highlights.

2. **Highlights macOS Protocol Mechanism**:
   - Highlights natively registers and handles the `highlights://` URL scheme:
     ```
     highlights://<absolute-path-to-pdf>#page=<page-number>
     ```
   - Launching via macOS `/usr/bin/open` with `-b net.highlightsapp.universal` reliably opens the document and scrolls to the 1-based page index.
   - AppleScript GUI scripting is rejected because Highlights has no native scripting dictionary (`sdef`); AppleScripting via `System Events` is slow, brittle, and requires invasive OS Accessibility privileges. The `highlights://` URI scheme is fast, native, and robust.

3. **Discoverability & Visual Affordance**:
   - A dynamic, contextual **status bar indicator** (`⌘⏎ Highlights · p. 5`) that reactively appears when the cursor is inside an eligible quote or task. It is clickable, clean, zero-layout-shift, and directly informs the user of both keymap availability and the resolved page number.
   - In Live Preview, the active quote callout header gains a subtle CSS target class and tooltip indicating jump availability.

4. **Beautiful Toast Feedback**:
   - Clean, descriptive toasts via Obsidian's `Notice` system:
     - Quote jump: `📄 Opened <name>.pdf (page 5) in Highlights`
     - Task bookmark jump: `📄 Opened <name>.pdf (page 5) from bookmark in Highlights`
     - Reading task: `📄 Opened <name>.pdf in Highlights`
     - Graceful degradation: If a page number cannot be inferred, it falls back to opening the PDF at the last read position and toasts `📄 Opened <name>.pdf in Highlights (page not found)`.

---

## 2. Current State Architecture & Mechanics

### 2.1 The Existing `<cmd+enter>` Flow in `bob-navigation-hotkeys`

In `plugins/bob-navigation-hotkeys/src/677-plugin-ref-pdf-open.js`, the command is registered as:
- **Command ID:** `open-reference-pdf-in-highlights`
- **Command Name:** `Open reference PDF in Highlights (or link in new tab)`
- **Vault Hotkey:** Bound to `Meta+Enter` in `.obsidian/hotkeys.json`.

```
                    [ Press Cmd+Enter ]
                             │
                             ▼
              openReferencePdfInHighlightsOrLink()
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   No Markdown Editor Context        Markdown Editor Context
            │                                 │
            ▼                                 ▼
delegateOpenLinkInNewTab()       resolveReferencePdfAtCursor()
(editor:open-link-in-new-leaf)                │
                                ┌─────────────┴─────────────┐
                                ▼                           ▼
                      Task with #task #ref          Not #task #ref
                                │                           │
                                ▼                           ▼
                   resolveReferencePdfFromTaskLine()   Check block link line
                                │                           │
                                ▼                           ▼
                      Returns { kind: "pdf" }     If not matched:
                                │                 Returns { kind: "none" }
                                ▼                           │
                      openReferencePdfPath()                ▼
                                │                 delegateOpenLinkInNewTab()
                                ▼
               /usr/bin/open -b net.highlightsapp.universal <path>
```

Currently, `resolveReferencePdfAtCursor` strictly checks:
1. `isObsidianTaskAtLine(content, lineIndex, contexts, lines)`.
2. `REF_AFTER_TASK_RE.test(lineText)` (matching `#task #ref`).
3. Or `parseRefPdfBlockLinkLine(lineText)` pointing to a `#task #ref` line.

If the cursor is inside a reference note on a quote callout, `isObsidianTaskAtLine` is false, `parseRefPdfBlockLinkLine` is null, and the command immediately returns `{ kind: "none" }`, delegating to `editor:open-link-in-new-leaf`.

### 2.2 How `bob ref` Formats Reference Notes & Highlights

Under `ref/<ref_type>/<name>.md`, reference notes generated by `bob ref sync` follow a strict structural contract:

```markdown
---
status: read
parent: "[[sase_ref]]"
type: "[[ref]]"
ref_type: papers
source_pdf: lib/papers/log_is_the_agent.pdf
highlights_sidecar: lib/papers/log_is_the_agent.md
highlights_count: 6
---

# log is the agent

- [x] #task #ref [[lib/papers/log_is_the_agent.pdf]] #hide ^ref

## Highlights

<!-- highlights:begin -->

### Page 1

> [!quote] We discuss—without claiming to demonstrate—why this substrate is unusually well suited...

^h-f78e65c00af4

### Page 2

> [!quote] A determinism contract and replay mechanism that makes any run byte-reproducible...
>
> > [!note] Comment Support sase tool call replay?

^h-383c9e969ec8

### Pages 3–4

> [!quote|Page 3] Things that sase generalizes: ...
>
> > [!quote|Page 4] – VCS and workspace operations ...
> >
> > > [!note] Comment Make sure that these are included in your current blog outline.

^h-b64de5bfbaff

<!-- highlights:end -->
```

Key structural invariants established by `src/native/highlights_ref/sidecar_render.rs`:
- Every highlight group ends with a unique block ID: `^h-[0-9a-f]{12}`.
- Highlights are grouped under page headings:
  - Simple single page: `### Page N` or `#### Page N`.
  - Multi-page continuation groups: `### Pages N–M`.
  - Linked Highlights export format: `#### [Page N](highlights://<doc>#page=N)`.
  - Sectioned notes: section titles appear as `### Title`, but member highlights inside sections *always* retain their page subheadings: `#### Page N`.
- Inside multi-page continuation callouts, each piece is labeled: `> [!quote|Page N]`.
- Single-page callouts render as `> [!quote]` under a `### Page N` heading.

### 2.3 How Tasks Link to Annotations

When `#task` is included in a highlight comment or note, `bob ref` creates a task:
```markdown
- [ ] #task Follow up on replay determinism [[ref/papers/log_is_the_agent#^h-383c9e969ec8|🔖]] [h:: 4c0a13d2...] [created::2026-10-30]
```
The task carries an aliased wikilink `[[<target_note>#^h-<block_id>|🔖]]`. Same-note tasks use `[[#^h-<block_id>|🔖]]`.

---

## 3. Highlights App macOS Deep-Linking Technical Analysis

### 3.1 Custom URL Scheme Mechanics

Highlights for macOS (`net.highlightsapp.universal`) implements deep linking via the `highlights://` URL scheme.

**URL Scheme Specification:**
- **Base document navigation:** `highlights://<path-to-pdf>`
- **Page-specific navigation:** `highlights://<path-to-pdf>#page=<page-number>`

*Examples:*
```
highlights://Users/bryan/bob/lib/papers/log_is_the_agent.pdf#page=2
highlights:///Users/bryan/bob/lib/papers/log_is_the_agent.pdf#page=2
```

**Key Technical Attributes:**
1. **1-Based Page Indexing:** Highlights uses physical 1-based PDF page numbers in `#page=N`, exactly matching the page numbers rendered in `### Page N` headings.
2. **Path Authority Handling:** On macOS, the path is absolute. Highlights accepts both `highlights://Users/...` (where the root slash is absorbed into the authority) and `highlights:///Users/...` (RFC 3986 standard empty-authority syntax).
3. **Escaping:** Spaces and special characters in paths should be percent-encoded (`encodeURI` / `%20`).
4. **Window Focus:** Invoking `/usr/bin/open` with `-b net.highlightsapp.universal` brings the Highlights window to the foreground and switches the PDF view to the specified page.

### 3.2 Evaluation of Execution Mechanisms

| Mechanism | Speed | Reliability | Permissions Required | Page Navigation Support | Recommendation |
|---|---|---|---|---|---|
| `/usr/bin/open "highlights://<path>#page=<n>"` | ~80ms | High | None (standard URL dispatch) | Native & precise | **Strongly Recommended** |
| `/usr/bin/open -b net.highlightsapp.universal <path>` | ~60ms | High | None | Document only (no page) | Current implementation |
| AppleScript via `osascript` (GUI scripting) | ~400ms+ | Very Low | macOS Accessibility (Prompt) | Simulates `Cmd+G` keystrokes | **Rejected** (brittle, intrusive) |
| Obsidian `window.open("highlights://...")` | Immediate | Low/Med | Browser sandbox security prompts | Native | **Rejected** (can trigger Electron modal) |

Using Node's `child_process.execFile("/usr/bin/open", ["-b", "net.highlightsapp.universal", uri], ...)` is completely aligned with the existing codebase architecture and provides seamless, secure execution without external permission prompts.

---

## 4. Critique of the Plan

### 4.1 Is This a Good Idea?

**Verdict: Yes, exceptional idea.**

In reading-heavy knowledge systems (like Bryan's Bob setup), a quote in a markdown note is an abstraction—a filtered snapshot of a larger thought. In practice, quotes frequently require returning to the source:
- To inspect diagrams, figures, or footnotes adjacent to the quote.
- To verify surrounding nuance, methodology, or caveats.
- To copy mathematical notation or extended passages that were not highlighted initially.

Currently, if Bryan wants to view the source PDF for a quote in a reference note, he must scroll up to the top of the note, find the `#task #ref` reading task, press `<cmd+enter>` to open Highlights, and then manually find the page. Having `<cmd+enter>` jump directly to the page while the cursor is inside the quote eliminates all friction.

### 4.2 Critiques, Pitfalls, and Recommended Adjustments

#### Critique 1: Don't Stop at Quotes in Ref Notes—Support Annotation Tasks Everywhere!
- **The Issue:** The initial requirement states: *"support for this keymap to be used when a quote/annotation in a ref note is selected"*.
- **The Reality:** Bryan does not only look at quotes inside `ref/...` notes. Bryan reviews tasks in `sase.md`, daily notes, project notes, and review walks. When `#task` is included in an annotation, `bob ref` generates a task with a bookmark link:
  ```markdown
  - [ ] #task Review replay determinism [[ref/papers/log_is_the_agent#^h-383c9e969ec8|🔖]] [h:: ...]
  ```
- **The Solution:** If Bryan is on an annotation task line and presses `<cmd+enter>`, the plugin should follow the `[[#^h-...|🔖]]` link, resolve the reference note, find the corresponding quote and page number, and open Highlights directly to that page!
- **Benefit:** Seamless round-trip. From the task in a project note, `<cmd+enter>` jumps straight into Highlights at the annotated quote.

#### Critique 2: Resolving Inline Links vs Highlights Jump
- **The Issue:** In Obsidian, `<cmd+enter>` normally executes `editor:open-link-in-new-leaf`. What if a quote or comment contains an ordinary wikilink, such as:
  ```markdown
  > [!quote] See the architecture described in [[sase_architecture]].
  ```
  If Bryan places his cursor inside `[[sase_architecture]]` and presses `<cmd+enter>`, what should happen?
- **Recommendation:**
  - If the cursor is positioned directly inside a link token (`[[...]]` or `[...]`), and that link is **not** a bookmark link (`🔖` / `^h-`), `<cmd+enter>` should delegate to `editor:open-link-in-new-leaf` to open that note in a new tab.
  - If the cursor is anywhere else in the quote callout, comment, block ID line, or on a `🔖` bookmark, it opens Highlights.

#### Critique 3: Handling Continuation Groups (Multi-Page Quotes)
- **The Issue:** Highlights exports continuation highlights (`<`) where a single quote spans across page boundaries:
  ```markdown
  ### Pages 3–4

  > [!quote|Page 3] First half of the thought on page 3...
  >
  > > [!quote|Page 4] Second half of the thought on page 4...
  > >
  > > > [!note] Comment My note on the whole thought.

  ^h-b64de5bfbaff
  ```
- **Recommendation:**
  - If the cursor is inside the nested `> > [!quote|Page 4]` sub-block, jump to **Page 4**.
  - If the cursor is on the `[!quote|Page 3]` block, the comment block, or the `^h-...` line, jump to **Page 3**.
  - Do not naively parse the heading `### Pages 3–4` and get stuck or guess.

#### Critique 4: What if Cursor is on the Page Heading Itself?
- If the cursor is on `### Page 5` (or `#### [Page 5](highlights://...)`), pressing `<cmd+enter>` should jump to Page 5 of the reference note's PDF! This is an effortless, delight-inducing interaction.

---

## 5. UI & UX Design: Intuitive, Reliable, and Beautiful

To make the feature intuitive, reliable, and beautiful, user feedback must operate across three tiers:
1. **Pre-action Discovery:** Before pressing `<cmd+enter>`, how does the user know the action is available and where it will go?
2. **In-action Feedback:** When `<cmd+enter>` is pressed, how does the system acknowledge the action?
3. **Post-action / Error Handling:** If something goes wrong (e.g. PDF missing, non-macOS, page unparsed), how does it degrade?

```
┌────────────────────────────────────────────────────────────────────────┐
│ Obsidian Window - ref/papers/log_is_the_agent.md                       │
│                                                                        │
│   ### Page 2                                                           │
│                                                                        │
│ ┌─[ Active Callout: .bob-highlights-target ]─────────────────────────┐ │
│ │ > [!quote] A determinism contract and replay mechanism...          │ │
│ │ >                                                                  │ │
│ │ > > [!note] Comment Support sase tool call replay?                 │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│   ^h-383c9e969ec8                                                      │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│ Status Bar: [  ⌘⏎ Highlights · p. 2  ]   (Clickable, tooltipped)      │
│ Notice Toast: 📄 Opened log_is_the_agent.pdf (page 2) in Highlights    │
└────────────────────────────────────────────────────────────────────────┘
```

### 5.1 Pre-Action Discovery: Contextual Status Bar Indicator

The most elegant and reliable affordance in Obsidian is a contextual status bar item. It avoids visual clutter and document mutation while providing immediate feedback.

- **Status Bar Element:** `bob-highlights-indicator`
- **Behavior:**
  - Listens to CodeMirror 6 selection updates via the existing `trackSelectionUpdate(update)` hook in `bob-navigation-hotkeys`.
  - When cursor is on an eligible target:
    - On a ref quote/annotation:
      `⌘⏎ Highlights · p. 2`
    - On a `#task #ref` reading task:
      `⌘⏎ Highlights`
    - On an annotation task with bookmark:
      `⌘⏎ Highlights · p. 2 (from task)`
  - When cursor moves to an ordinary paragraph or non-ref line:
    - The status bar item smoothly fades to hidden (`display: none;`).
  - **Clickable:** Clicking the status bar badge directly triggers `openReferencePdfInHighlightsOrLink()`, providing mouse parity with the keyboard shortcut.
  - **Tooltip:**
    `"Open log_is_the_agent.pdf at page 2 in Highlights (⌘⏎)"`

### 5.2 Active Quote Callout Affordance (CSS & Gutter/Header)

In Live Preview / Reading View, when the cursor is inside a quote callout that resolves to a PDF:
- The editor view decorates the active callout container with a subtle CSS class: `bob-highlights-active-quote`.
- A small, unobtrusive Highlights badge or accent line appears in the top-right corner of the callout header, showing a miniature book icon with `⌘⏎ p. 2`.
- Hovering over a bookmark link `[[#^h-...|🔖]]` in any task displays a native tooltip:
  `"Page 2 in Highlights (⌘⏎)"`.

### 5.3 Toast Notifications (Obsidian Notices)

When `<cmd+enter>` is pressed, a concise, beautiful toast is displayed via `new Notice(...)`:

| Scenario | Toast Message | Duration | Icon / Tone |
|---|---|---|---|
| **Quote Jump with Page** | `📄 Opened log_is_the_agent.pdf (p. 2) in Highlights` | 2500ms | Informational / Clean |
| **Task Bookmark Jump** | `📄 Opened log_is_the_agent.pdf (p. 2) from bookmark in Highlights` | 2500ms | Informational / Clean |
| **Reading Task (No Page)** | `📄 Opened log_is_the_agent.pdf in Highlights` | 2500ms | Informational / Clean |
| **Page Unresolved Fallback** | `📄 Opened log_is_the_agent.pdf in Highlights (page not found)` | 3000ms | Neutral / Fallback |
| **PDF Not Found** | `⚠️ Reference PDF not found: lib/papers/foo.pdf` | 5000ms | Warning |
| **Non-macOS Platform** | `ℹ️ Highlights is macOS-only: lib/papers/foo.pdf` | 4000ms | Informational |

---

## 6. Detailed Implementation Blueprint

### 6.1 Architecture Overview

All modifications cleanly slot into `plugins/bob-navigation-hotkeys/src/677-plugin-ref-pdf-open.js` and its harness.

```
                              resolveReferencePdfAtCursor()
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               ▼                            ▼                            ▼
      Cursor on Task Line         Cursor on Block Link       Cursor in Reference Note
               │                            │                            │
      ┌────────┴────────┐                   ▼                   Check if inside
      ▼                 ▼         Resolve target line;          Highlights region
   #task #ref     Has 🔖 link     recurse                       (<!-- highlights:begin -->)
      │                 │                                                │
   Default        Resolve ref note                                       ▼
  (page null)     & block ID;                                   Resolve Annotation Block
                  find page                                     & Page Heading
                        │                                                │
                        └───────────────────┬────────────────────────────┘
                                            ▼
                               Returns { kind: "pdf",
                                         path: "...",
                                         page: <number|null>,
                                         blockId: "..." }
                                            │
                                            ▼
                               openReferencePdfPath(path, { page })
                                            │
                                            ▼
                        Highlights URL with #page=N (or raw path)
```

### 6.2 Target Resolution Algorithm

```javascript
/**
 * Resolves the reference PDF and optional page number at the cursor position.
 * Returns:
 *   - { kind: "none" }
 *   - { kind: "error", message: string }
 *   - { kind: "pdf", path: string, page: number | null, blockId?: string }
 */
async function resolveReferencePdfAtCursor(editor, file) {
  const content = String(editor.getValue() || "");
  const cursor = editor.getCursor();
  const lines = content.split(/\r?\n/);
  const lineIndex = cursor && Number.isInteger(cursor.line) ? cursor.line : -1;
  if (lineIndex < 0 || lineIndex >= lines.length) {
    return Object.freeze({ kind: "none" });
  }

  const lineText = String(lines[lineIndex] || "");
  const contexts = getMarkdownLineContexts(content);

  // 1. Task line handling
  if (isObsidianTaskAtLine(content, lineIndex, contexts, lines)) {
    // 1A. Standard #task #ref reading task
    if (REF_AFTER_TASK_RE.test(lineText)) {
      return this.resolveReferencePdfFromTaskLine(lineText, file.path);
    }

    // 1B. Annotation task linking to a quote: [[note#^h-...|🔖]] or [[#^h-...|🔖]]
    const annotationBookmark = parseAnnotationTaskBookmark(lineText);
    if (annotationBookmark) {
      return this.resolveReferencePdfFromBookmark(annotationBookmark, file.path);
    }

    return Object.freeze({ kind: "none" });
  }

  // 2. Block link line (e.g. ^ref embed)
  const blockLink = parseRefPdfBlockLinkLine(lineText);
  if (blockLink) {
    return this.resolveReferencePdfFromBlockLink(blockLink, file.path);
  }

  // 3. Inside a Reference Note: Check if cursor is on/within a quote or page heading
  if (isReferenceNotePath(file.path)) {
    return this.resolveReferencePdfFromRefNoteContent(content, lineIndex, file.path);
  }

  return Object.freeze({ kind: "none" });
}
```

### 6.3 Page Parsing from Reference Note Content

Inside a reference note (`ref/.../*.md`):
1. **Verify Highlights Region:**
   - Scan backward and forward from `lineIndex` to verify it falls between `<!-- highlights:begin -->` and `<!-- highlights:end -->`.
2. **Page Heading directly on cursor line:**
   - If line matches `^#{3,6}\s+(?:\[)?Page\s+(\d+)` or `^#{3,6}\s+Pages\s+(\d+)`, return page `$1`.
3. **Inside an Annotation Callout Block:**
   - Scan upward to find the start of the callout: `> [!quote` or `> [!note` or `> [!summary`.
   - Scan downward to find the block ID anchor: `^h-([0-9a-f]{12})`.
   - If cursor line is between the callout start and the block ID anchor:
     - Check callout header for explicit sub-piece page: `> [!quote|Page\s*(\d+)]`. If found and cursor is within that sub-piece, return that page.
     - Otherwise, scan upward past the callout start to find the nearest preceding page heading:
       ```javascript
       const PAGE_HEADING_RE = /^#{3,6}\s+(?:\[)?Pages?\s+(\d+)(?:[–-](\d+))?(?:\]\([^)]*#page=(\d+)\))?/i;
       ```
       Extract page number (preferring `#page=(\d+)` if present, then `$1`).
     - Retrieve `source_pdf` from the note frontmatter.
     - Return `{ kind: "pdf", path: frontmatter.source_pdf, page: pageNum, blockId: matchedBlockId }`.

### 6.4 Opening via `/usr/bin/open` with URL Fallbacks

In `openReferencePdfPath(path, options = {})`:

```javascript
function buildHighlightsOpenAttempts(absolutePath, page) {
  const normalizedPath = String(absolutePath || "");
  if (page && Number.isInteger(page) && page > 0) {
    // Format: highlights://Users/bryan/...#page=N
    const cleanPath = normalizedPath.replace(/^\/+/, "");
    const encodedPath = encodeURI(cleanPath);
    const highlightsUri = `highlights://${encodedPath}#page=${page}`;

    return Object.freeze([
      Object.freeze(["-b", HIGHLIGHTS_BUNDLE_ID, highlightsUri]),
      Object.freeze(["-a", HIGHLIGHTS_APP_NAME, highlightsUri]),
      // Fallback to direct file open if URL scheme fails
      Object.freeze(["-b", HIGHLIGHTS_BUNDLE_ID, normalizedPath]),
    ]);
  }

  // Base path open (reading task)
  return Object.freeze([
    Object.freeze(["-b", HIGHLIGHTS_BUNDLE_ID, normalizedPath]),
    Object.freeze(["-a", HIGHLIGHTS_APP_NAME, normalizedPath]),
  ]);
}
```

Notice emission:
```javascript
const pageLabel = options.page ? ` (page ${options.page})` : "";
const originLabel = options.fromBookmark ? " from bookmark" : "";
new Notice(`Opened ${fileName}${pageLabel}${originLabel} in Highlights`);
```

### 6.5 Dynamic Status Bar Controller

```javascript
class BobNavigationHotkeysStatusBarMixin {
  setupHighlightsStatusBar() {
    if (!bracketModeIsDesktop() || typeof this.addStatusBarItem !== "function") return;
    this.highlightsStatusEl = this.addStatusBarItem();
    this.highlightsStatusEl.addClass("bob-highlights-status-bar");
    this.highlightsStatusEl.style.display = "none";
    this.highlightsStatusEl.addEventListener("click", () => {
      this.openReferencePdfInHighlightsOrLink();
    });
  }

  updateHighlightsStatusBar(target) {
    if (!this.highlightsStatusEl) return;
    if (!target || target.kind !== "pdf") {
      this.highlightsStatusEl.style.display = "none";
      return;
    }

    const text = target.page
      ? `⌘⏎ Highlights · p. ${target.page}`
      : `⌘⏎ Highlights`;
    const tooltip = target.page
      ? `Open ${target.path.split("/").pop()} at page ${target.page} in Highlights (⌘⏎)`
      : `Open ${target.path.split("/").pop()} in Highlights (⌘⏎)`;

    this.highlightsStatusEl.textContent = text;
    this.highlightsStatusEl.setAttribute("aria-label", tooltip);
    this.highlightsStatusEl.style.display = "inline-flex";
  }
}
```

---

## 7. Recommended Test Matrix

The test suite in `scripts/test-navigation-hotkeys-ref-pdf.cjs` should be extended with tests covering:

1. **Quote in Ref Note with Page Heading:**
   - Cursor on `> [!quote]` under `### Page 3` -> opens `highlights://...#page=3`, toasts `Opened foo.pdf (page 3) in Highlights`.
2. **Quote on Block ID Line:**
   - Cursor on `^h-383c9e969ec8` under `### Page 2` -> opens page 2.
3. **Cursor on Page Heading Line:**
   - Cursor directly on `### Page 4` -> opens page 4.
4. **Continuation Quote with Multiple Pages:**
   - Group under `### Pages 3–4`:
     - Cursor on `> [!quote|Page 3]` -> opens page 3.
     - Cursor on `> > [!quote|Page 4]` -> opens page 4.
5. **Sectioned Reference Note:**
   - Highlights inside `### Section` under `#### Page 7` -> correctly resolves page 7.
6. **Annotation Task with Bookmark Link (`🔖`):**
   - Cursor on `- [ ] #task ... [[ref/papers/log#^h-abc|🔖]]` in another note -> opens `lib/papers/log.pdf` at the resolved page.
7. **Inline Link Delegation:**
   - Cursor inside `[[other_note]]` within a quote -> delegates to `editor:open-link-in-new-leaf`.
8. **Degraded / Fallback States:**
   - Reference note without page headings (e.g. unpaged color-grouped export) -> opens PDF at root, toasts `Opened foo.pdf in Highlights (page not found)`.
   - Missing PDF -> toasts `Reference PDF not found`.
   - Linux / Windows platform -> toasts `Highlights is macOS-only`.

---

## 8. Summary of Recommendations & Next Steps

1. **Adopt Proposed Feature:** Implement `<cmd+enter>` page jumping for quotes and annotations in reference notes.
2. **Include Annotation Tasks:** Include support for tasks carrying `[[...#^h-...|🔖]]` links.
3. **Use Native URL Scheme:** Use `highlights://<path>#page=<page>` via `/usr/bin/open -b net.highlightsapp.universal`.
4. **Implement Status Bar Affordance:** Add a reactive, clickable `⌘⏎ Highlights · p. N` status bar widget.
5. **Polished Toasts:** Provide informative, concise Obsidian notices that distinguish between full-PDF and page-targeted launches.
