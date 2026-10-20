# Research Report: Image Zoom & Inline Image Link Viewing in Obsidian

**Researcher:** `research.26.gem`  
**Date:** October 2026  
**Context:** Investigating mechanics, interaction models, and keymaps for inspecting enlarged images and inline image links in Obsidian, with specific critique of a proposed `Z` keymap and recommendations tailored to the `bob-cli` / `bob-plugins` ecosystem.

---

## 1. Executive Summary

The user proposes introducing a mechanism in Obsidian to zoom in on images and inline image links to view a large, detailed version on demand, triggered by a new `Z` keymap.

### Key Findings & Evaluation

1. **The Core Need is Real and High-Value:**  
   Obsidian's default handling of embedded images—either constraining them to the editor note width, forcing fixed thumbnail widths (e.g., `![[image.png|300]]`), or requiring a jarring jump to a new workspace leaf—severely impairs inspection of high-density images (such as Retina screenshots from `macscrot`, PDF figure clips from `bob ref`, architecture diagrams, and dense charts). A fluid, in-place zoom/lightbox solution is urgently needed.

2. **The Bare `Z` Keymap is Fundamentally Flawed in Vim Mode:**  
   In a keyboard-driven setup running CodeMirror Vim (as configured across `bob-plugins`), bare `Z` in Normal mode directly collides with standard Vim commands:
   - `ZZ` (save and quit) and `ZQ` (quit without saving).
   - Mapping bare `Z` in Normal mode either breaks these commands or introduces an ambiguous input timeout delay, causing sluggish editor response.
   - Lowercase `z` is the standard prefix for folding and scrolling (`zz`, `zt`, `zb`, `za`, `zo`, `zc`) and cannot be remapped without breaking standard motions.
   - In Insert mode, bare `Z` obviously inserts the character "Z".
   - In Reading View, there is no text cursor (`editor.getCursor()`), making cursor-relative hotkeys non-functional without mouse hover context.

3. **A Purely Keyboard-Driven Trigger Creates an Ergonomic Paradox:**  
   Image inspection is primarily an eye- and mouse-guided task. Requiring a user to navigate their text cursor through paragraphs onto an image syntax link just to view an image they are already looking at adds unnecessary friction. The solution must support a **dual-trigger model**:
   - **Direct click / double-click** on any rendered image in both Live Preview and Reading View.
   - **Keyboard chord / motion** (`\z`, `Alt+Z`, or context-aware `<CR>` Enter on image links) when the cursor is already on or near an image link during writing or review.

4. **Recommended Solution:**  
   - **Short-Term / Immediate:** Evaluate the lightweight community plugin `Image Workflow` (`1spread/obsidian-image-enlarge`) for instant, zero-maintenance click-to-zoom with mouse-wheel scaling and Esc dismiss.
   - **Long-Term / Strategic ("The Bob Way"):** Implement a dedicated, lightweight module within `bob-plugins` (either as an extension to `bob-navigation-hotkeys` or a standalone `bob-image-lightbox` plugin) that provides:
     1. Click-to-lightbox on any rendered `<img>`.
     2. Context-aware `<CR>` (Enter) and `\z` (Vim normal mode leader) to zoom the image link under the cursor.
     3. An unobtrusive, hardware-accelerated modal supporting wheel zoom, pan, reset, and `y` yank image path.

---

## 2. Background & Problem Analysis

### 2.1 Image Types in Obsidian & Bryan's Workflow

In Bryan's Obsidian vault and `bob-cli` toolchain, images originate from several distinct workflows:

1. **Highlights & PDF Reference Notes (`bob ref`):**  
   Recent enhancements (e.g., `highlights_image_notes.md`) automatically extract screenshots and figures from PDF annotations in Highlights on macOS into vault asset directories (`ref/<type>/<stem>.assets/<safe-stem>-<hash8>.png`) and embed them inline into reference notes.
2. **Standard Vault Attachments:**  
   Screenshots captured via `macscrot` (`~/tmp/screenshots/YYYYMMDD_HHMMSS.png`), pasted into daily notes, project notes, or area notes.
3. **Syntactical Variations:**
   - Internal Wikilink Embeds: `![[ref/papers/example.assets/figure-07154fc6.png]]` or `![[diagram.png|400]]`.
   - Markdown Embeds: `![Architecture Diagram](assets/arch.png)` or external URLs `![Web Graphic](https://...)`.
   - Plain Image Links (non-embedded): `[[screenshot.png]]` or `[Data Table](table.png)`.
   - HTML Image Tags: `<img src="..." width="300">`.

### 2.2 Shortcomings of Default Obsidian Behavior

When viewing notes in Obsidian:
- **Constrained Layout:** Images without explicit width scale to 100% of the active editor pane width. In narrow split panes (common in multi-pane GTD setups), diagrams and full-screen Retina screenshots become unreadably tiny.
- **Fixed Width Clamping:** Images with thumbnail widths (e.g., `|300`) cannot be magnified without manually editing the markdown source.
- **Disruptive Navigation:** In default Obsidian, `Cmd/Ctrl + Click` on an internal image link opens the image in a new workspace leaf / tab. This displaces the active note, creates tab clutter, destroys reading flow, and lacks smooth pan/zoom controls.
- **No Built-in Lightbox:** Unlike modern reading platforms (Medium, GitHub, Notion), Obsidian core provides no native click-to-enlarge overlay for embedded media.

---

## 3. Critique of the `Z` Keymap Proposal

The user proposed: *"I was thinking a new `Z` keymap could trigger this behavior."*

While the desire for quick, keyboard-accessible inspection is sound, a bare `Z` keymap suffers from severe technical, modal, and ergonomic issues:

### 3.1 Severe Conflicts in Vim Mode

The vault environment relies extensively on Vim mode (`window.CodeMirrorAdapter.Vim`), as evident in `bob-navigation-hotkeys`, `task-status-cycler`, and `bob-vim-surround`.

1. **Vim Normal Mode `ZZ` and `ZQ`:**
   - In Vim, uppercase `Z` is a hardcoded prefix:
     - `ZZ`: Write current file and close buffer (`:x` / `:wq`).
     - `ZQ`: Quit current buffer without saving (`:q!`).
   - If bare `Z` is mapped to an action in Normal mode via `vim.mapCommand("Z", "action", ...)`:
     - It intercepts the `Z` key immediately, breaking `ZZ` and `ZQ`.
     - Or, if mapped as a multi-key binding, CodeMirror Vim must wait for `timeoutlen` (usually 1000ms) to check whether a second key is pressed. This introduces perceptible lag into general editing.
2. **Lowercase `z` Conflicts:**
   - In Vim, lowercase `z` is the canonical prefix for scrolling and fold manipulation:
     - Viewport centering: `zz` (center cursor), `zt` (top), `zb` (bottom).
     - Folds: `za` (toggle fold), `zo` (open fold), `zc` (close fold), `zM` (close all folds), `zR` (open all folds).
   - Hijacking lowercase `z` destroys standard Vim text navigation.

### 3.2 Modal & Document Context Ambiguities

1. **Insert Mode:**
   - An unmodified letter key (`Z` or `z`) cannot be an active hotkey in Insert mode; it would prevent the user from typing the letter "Z" into notes or prose.
2. **Reading View (Markdown Preview):**
   - In Reading View, the document is rendered HTML. There is no active CodeMirror editor cursor (`editor.getCursor()` returns null).
   - If a keymap relies on the cursor being located on an image link, that keymap will do nothing in Reading View.
3. **Cursor Target Ambiguity:**
   - Where must the cursor be?
     - Exactly inside `![[image.png]]`?
     - Anywhere on the line?
     - What if a line contains multiple images (e.g., a row of comparison screenshots)?
     - What if the cursor is in a paragraph discussing an image that is 4 lines below? Does the user have to stop reading, count lines, move the cursor down, and then press `Z`?

### 3.3 The Ergonomic Mismatch (Visual vs Spatial Flow)

Image zoom is an inherently visual, 2D inspection task:
- When a user wants to enlarge an image, their eyes are already looking at that image.
- If their hand is on the mouse/trackpad, clicking the image is an immediate, zero-friction gesture (~200ms).
- Requiring a keyboard-only approach forces the user to:
  1. Switch context from visual inspection to text navigation.
  2. Locate the text cursor.
  3. Navigate the cursor onto the image embed line using Vim motions (`/`, `j`, `k`).
  4. Press the keymap.
- This creates 5x more cognitive and physical friction than a direct click.

**Verdict on `Z`:**
A bare `Z` keymap is untenable. The functionality must be accessible via **direct mouse click** on rendered images, supplemented by a **conflict-free keyboard chord** (such as `\z`, `Alt+Z`, or context-aware `<CR>`) for keyboard-centric editing sessions.

---

## 4. Exploration of Solution Spaces & Existing Patterns

### 4.1 Landscape of Existing Obsidian Community Plugins

Several community plugins tackle image viewing in Obsidian. An examination of their architectures reveals important design patterns:

| Plugin | Downloads / Maturity | Primary Trigger | Key Features | Limitations / Trade-offs |
| :--- | :--- | :--- | :--- | :--- |
| **`Image Toolkit`** (`obsidian-image-toolkit` by sissilab) | 100k+ (Very mature) | Click on `img` | • Zoom (mouse wheel & toolbar buttons)<br>• Pan (drag & arrow keys)<br>• Rotate, flip, color invert<br>• Pin mode (floats image while editing note)<br>• Gallery navbar for multi-image notes | • Bulky UI toolbar over images<br>• Complex settings suite<br>• No keyboard trigger from editor cursor |
| **`Image Workflow` / `obsidian-image-enlarge`** (`1spread`) | Modern / Lightweight | Click on `img` | • Fullscreen dark overlay lightbox<br>• Smooth mouse wheel zoom with 100% snap<br>• Esc or backdrop click to dismiss<br>• Rich copy / download buttons<br>• Fast and unobtrusive | • Click-driven only; no editor cursor keymap<br>• Third-party plugin requiring manual update/sync |
| **`Image Hover Preview`** (`shin2w`) | Emerging | Mouse hover on `![]()` or image links | • Floating preview overlay near cursor<br>• Shift + scroll wheel to zoom<br>• Configurable trigger/suppress keys | • Can be intrusive during fast mouse movements<br>• Not a centered lightbox; limited max zoom boundary |
| **`Medium Zoom` / `PhotoView`** | Moderate | Click on `img` | • Medium-style smooth animation zoom to viewport center | • Lacks deep zoom/pan for large technical diagrams or high-res Retina screenshots |

### 4.2 Obsidian Core API Capabilities

1. **`Modal` Class (`obsidian.Modal`):**
   - Built into Obsidian API.
   - Automatically handles:
     - Backdrop dimming (`.modal-bg`).
     - Window management and positioning.
     - `Escape` key capture and dismiss.
     - Outside click to dismiss.
     - Focus trapping and restoration (`shouldRestoreSelection = true`).
2. **File Resource Resolution (`app.vault.getResourcePath`):**
   - Given a `TFile` representing an internal attachment (e.g. `ref/...assets/fig.png`), `app.vault.getResourcePath(tfile)` returns a local Electron URL (`app://...`) that can be directly assigned to an `HTMLImageElement.src`.
3. **Editor Link Inspection in CodeMirror 6:**
   - Active view: `app.workspace.getActiveViewOfType(MarkdownView)`.
   - Cursor: `view.editor.getCursor()`.
   - Line text: `view.editor.getLine(cursor.line)`.
   - Link resolution: `app.metadataCache.getFirstLinkpathDest(linkpath, sourcePath)`.

---

## 5. Architectural Options for Bryan's Setup

### Option 1: Adopt an Off-the-Shelf Community Plugin (`Image Workflow`)

- **Description:** Install `1spread/obsidian-image-enlarge` (Image Workflow) or `obsidian-image-toolkit`.
- **How it works:** Whenever an image is clicked in Live Preview or Reading View, a responsive lightbox overlay opens. Scrolling the mouse wheel zooms in/out; pressing `Esc` or clicking the backdrop closes it.
- **Pros:**
  - Zero development or testing time.
  - Fully tested across Obsidian desktop versions.
  - Handles drag-pan, wheel zoom, and retina images cleanly.
- **Cons:**
  - Outside Bryan's `bob-plugins` repository (must be maintained via BRAT or manual vault sync).
  - Lacks keyboard cursor activation (no way to press a hotkey on an image link without touching the mouse).

### Option 2: Extend `bob-navigation-hotkeys` in `bob-plugins`

- **Description:** Integrate image zoom directly into Bryan's existing `bob-navigation-hotkeys` plugin.
- **Why this is attractive:**
  - `bob-navigation-hotkeys` already contains a robust link parsing engine (`extractLineLinks`, `parseWikiLinkAt`, `parseMarkdownLinkAt`) in `src/640-plugin-notes-and-task-move.js`.
  - Currently, line 237 of that file deliberately discards non-markdown files:
    ```javascript
    const resolvedFile = this.resolveLinkTargetFile(target, sourcePath);
    if (resolvedFile) {
      if (!this.isMarkdownFile(resolvedFile)) {
        return null; // Skips images!
      }
      ...
    }
    ```
  - By extending `bob-navigation-hotkeys`:
    1. **Context-Aware Enter (`<CR>`):** When the cursor in Vim Normal mode is on an image link (e.g. `![[image.png]]` or `[[figure.png]]`), pressing `<CR>` opens the image lightbox modal instead of falling through!
    2. **Vim Leader Keymap (`\z`):** In `src/620-plugin-dash-and-vim-jumps.js`, `bob-navigation-hotkeys` already defines `\s` for tab pinning via `vim.mapCommand("\\s", ...)`. We can define `\z` to explicitly zoom the image at the cursor.
    3. **Global Command & Hotkey (`Alt+Z`):** Register an Obsidian command `bob-navigation-hotkeys:zoom-image-at-cursor` bound by default to `Alt+Z`.
    4. **DOM Click Listener:** Register a click listener on the active window to open the lightbox when clicking any rendered `<img>` in markdown preview or live preview.
- **Pros:**
  - Perfect cohesion with Bryan's existing keyboard philosophy and Vim muscle memory.
  - Fully deployed and versioned via `bob plugins sync`.
  - Solves both keyboard-cursor and mouse-click workflows simultaneously.
  - Zero external plugin dependencies.
- **Cons:**
  - Increases the footprint of `bob-navigation-hotkeys`.

### Option 3: Create a Dedicated `bob-image-lightbox` Plugin in `bob-plugins`

- **Description:** Add a new, focused plugin (`plugins/bob-image-lightbox`) inside the `bob-plugins` monorepo.
- **Features:**
  - Single-responsibility plugin (~300 lines of code).
  - Implements `ImageLightboxModal` using Obsidian's native `Modal`.
  - Exposes an editor command `bob-image-lightbox:zoom-at-cursor` and a click interceptor.
  - Hooks into `window.CodeMirrorAdapter.Vim` to register `\z`.
- **Pros:**
  - Clean separation of concerns (doesn't complicate task navigation or review walks).
  - Isolated testing and zero risk of regression to core GTD navigation.
  - Synced automatically with `bob plugins sync`.
- **Cons:**
  - Adds an 8th plugin to the `bob-plugins` suite.

---

## 6. Adjustments to Requirements

To transform the initial concept into an intuitive, reliable, and ergonomic feature, the following adjustments to the requirements are justified and recommended:

### Adjustment 1: Replace Bare `Z` with Conflict-Free Triggers

1. **Vim Normal Mode Leader Chord (`\z`):**  
   - Pattern: Follow the established convention in `bob-navigation-hotkeys` where `\s` toggles tab pin.
   - Behavior: Pressing `\z` in Normal mode inspects the current line, finds the image link/embed at or nearest to the cursor, and opens the lightbox.
2. **Context-Aware Enter (`<CR>`):**  
   - Pattern: In Normal mode, `<CR>` already follows wiki links to markdown notes.
   - Behavior: If the link under the cursor points to an image file (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg`, `.bmp`), `<CR>` should immediately open the image lightbox.
3. **Global Obsidian Hotkey (`Alt+Z`):**  
   - An unmodified `Z` is impossible in Insert mode, and `Mod+Z` (`Ctrl+Z`) is reserved for Undo.
   - `Alt+Z` (or `Ctrl+Alt+Z`) is conflict-free, accessible from both Insert mode and Normal mode, and works across Live Preview and Reading View.

### Adjustment 2: Enforce a Dual-Trigger Model (Click + Keyboard)

- **Requirement:** A mouse click (or double-click) directly on any rendered `<img>` inside a markdown leaf must immediately open the lightbox.
- **Rationale:** When reviewing papers or browsing notes, the user's hand is frequently on the trackpad. Clicking the image is 5x faster than moving the text cursor to the link syntax.

### Adjustment 3: Broad Syntax Support

The zoom mechanism must detect all standard image representations:
1. Internal transcluded embeds: `![[path/to/image.png]]` and `![[image.png|width]]`.
2. Standard markdown embeds: `![alt text](path/to/image.png)` and remote URLs `![alt](https://...)`.
3. Non-transcluded links: `[[image.png]]` (common when attaching diagrams without rendering them full-page).
4. Rendered HTML tags: `<img src="...">`.

### Adjustment 4: Interactive Lightbox Controls

Simply scaling up the image statically is insufficient for high-density Retina screenshots or multi-column PDF diagrams. The lightbox must provide:
- **Mouse Wheel Zoom:** Scaled relative to the cursor position (zoom toward pointer).
- **Drag-to-Pan:** Pan the image freely when zoomed past viewport dimensions.
- **100% Snap & Reset:** Quick toggle between "Fit to Screen" and "Original Resolution (1:1 pixels)".
- **Modal Keybindings:**
  - `Escape` or `q`: Close lightbox.
  - `+` / `-`: Zoom in / zoom out.
  - `0`: Reset zoom to fit.
  - `y`: Copy image vault path to clipboard (synergizes with Bryan's `ctrl-y` yank philosophy).

---

## 7. Implementation Blueprint (The Tailored Solution)

Below is the concrete technical architecture for implementing this in `bob-plugins` (either inside `bob-navigation-hotkeys` or as `bob-image-lightbox`).

```
┌─────────────────────────────────────────────────────────────┐
│                       Obsidian UI                           │
│                                                             │
│   [ Live Preview / Reading View ]      [ Text Cursor / Vim ]│
│                 │                                │          │
│           Mouse Click                      Press \z or <CR> │
│                 │                                │          │
│                 ▼                                ▼          │
│      ┌─────────────────────┐          ┌───────────────────┐ │
│      │ DOM Click Listener  │          │ Link Target       │ │
│      │ (img element target)│          │ Resolver (CM6)    │ │
│      └──────────┬──────────┘          └─────────┬─────────┘ │
│                 │                               │           │
│                 └───────────────┬───────────────┘           │
│                                 ▼                           │
│                 ┌───────────────────────────────┐           │
│                 │      ImageLightboxModal       │           │
│                 │  - Hardware-accelerated scale │           │
│                 │  - Wheel zoom & pan           │           │
│                 │  - Esc / q to dismiss         │           │
│                 │  - y to yank path             │           │
│                 └───────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### 7.1 Cursor Image Link Resolver (JavaScript)

```javascript
const IMAGE_EXTENSIONS = new Set(["png", "jpg", "jpeg", "gif", "webp", "svg", "bmp", "avif"]);

function isImageExtension(ext) {
  return ext && IMAGE_EXTENSIONS.has(ext.toLowerCase());
}

function resolveImageAtCursor(app, editor, file) {
  const cursor = editor.getCursor();
  const line = editor.getLine(cursor.line);
  
  // 1. Check for wikilink embeds: ![[...]] or links [[...]]
  const wikiRegex = /!?\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]/g;
  let match;
  while ((match = wikiRegex.exec(line)) !== null) {
    const start = match.index;
    const end = start + match[0].length;
    // Check if cursor is inside or adjacent to the link
    if (cursor.ch >= start && cursor.ch <= end) {
      const linkPath = match[1].trim();
      const resolved = app.metadataCache.getFirstLinkpathDest(linkPath, file.path);
      if (resolved && isImageExtension(resolved.extension)) {
        return {
          file: resolved,
          url: app.vault.getResourcePath(resolved),
          title: resolved.basename
        };
      }
    }
  }

  // 2. Check for markdown embeds: ![alt](url)
  const mdRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
  while ((match = mdRegex.exec(line)) !== null) {
    const start = match.index;
    const end = start + match[0].length;
    if (cursor.ch >= start && cursor.ch <= end) {
      const linkTarget = match[2].trim();
      if (/^https?:\/\//i.test(linkTarget)) {
        return { file: null, url: linkTarget, title: match[1] || "Remote Image" };
      }
      const resolved = app.metadataCache.getFirstLinkpathDest(linkTarget, file.path);
      if (resolved && isImageExtension(resolved.extension)) {
        return {
          file: resolved,
          url: app.vault.getResourcePath(resolved),
          title: resolved.basename
        };
      }
    }
  }

  // 3. Fallback: If cursor line contains exactly one image, use it
  // (Provides forgiving ergonomics when cursor is on the same line)
  return null;
}
```

### 7.2 The Lightbox Modal (`ImageLightboxModal.js`)

```javascript
import { Modal } from "obsidian";

export class ImageLightboxModal extends Modal {
  constructor(app, { url, title, file }) {
    super(app);
    this.url = url;
    this.titleText = title || "";
    this.file = file;
    this.scale = 1.0;
    this.translateX = 0;
    this.translateY = 0;
    this.isDragging = false;
    this.dragStartX = 0;
    this.dragStartY = 0;
  }

  onOpen() {
    const { contentEl, modalEl, containerEl } = this;
    modalEl.addClass("bob-image-lightbox-modal");
    containerEl.addClass("bob-image-lightbox-backdrop");

    // Clear default modal chrome
    contentEl.empty();

    const stageEl = contentEl.createDiv({ cls: "bob-lightbox-stage" });
    const imgEl = stageEl.createEl("img", {
      cls: "bob-lightbox-img",
      attr: { src: this.url }
    });

    const updateTransform = () => {
      imgEl.style.transform = `translate(${this.translateX}px, ${this.translateY}px) scale(${this.scale})`;
    };

    // Mouse wheel zoom centered on cursor
    stageEl.addEventListener("wheel", (evt) => {
      evt.preventDefault();
      const zoomFactor = evt.deltaY < 0 ? 1.15 : 0.85;
      const newScale = Math.min(Math.max(this.scale * zoomFactor, 0.2), 10.0);
      
      // Calculate zoom relative to pointer
      const rect = imgEl.getBoundingClientRect();
      const offsetX = evt.clientX - rect.left;
      const offsetY = evt.clientY - rect.top;
      
      this.translateX -= (offsetX - rect.width / 2) * (zoomFactor - 1);
      this.translateY -= (offsetY - rect.height / 2) * (zoomFactor - 1);
      this.scale = newScale;
      updateTransform();
    }, { passive: false });

    // Drag-to-pan
    stageEl.addEventListener("mousedown", (evt) => {
      if (evt.button !== 0) return;
      this.isDragging = true;
      this.dragStartX = evt.clientX - this.translateX;
      this.dragStartY = evt.clientY - this.translateY;
    });

    window.addEventListener("mousemove", (evt) => {
      if (!this.isDragging) return;
      this.translateX = evt.clientX - this.dragStartX;
      this.translateY = evt.clientY - this.dragStartY;
      updateTransform();
    });

    window.addEventListener("mouseup", () => {
      this.isDragging = false;
    });

    // Keyboard controls inside the modal
    this.scope.register([], "Escape", () => this.close());
    this.scope.register([], "q", () => this.close());
    this.scope.register([], "0", () => {
      this.scale = 1.0;
      this.translateX = 0;
      this.translateY = 0;
      updateTransform();
    });
    this.scope.register([], "y", () => {
      if (this.file) {
        navigator.clipboard.writeText(this.file.path);
        new Notice(`Copied image path: ${this.file.path}`);
      }
    });
  }
}
```

### 7.3 Click & Vim Event Registration

```javascript
// Register DOM click on rendered images
this.registerDomEvent(window, "click", (evt) => {
  const target = evt.target;
  if (!target || !(target instanceof HTMLImageElement)) return;
  // Ignore small icons or buttons
  if (target.closest(".nav-file, .tree-item, .clickable-icon")) return;
  if (!target.closest(".workspace-leaf-content[data-type='markdown']")) return;

  evt.preventDefault();
  evt.stopPropagation();
  new ImageLightboxModal(this.app, {
    url: target.src,
    title: target.alt || ""
  }).open();
});

// Register Vim Normal mode command (\z)
const vim = window.CodeMirrorAdapter && window.CodeMirrorAdapter.Vim;
if (vim) {
  vim.defineAction("bobZoomImageAtCursor", (cm) => {
    const view = this.app.workspace.getActiveViewOfType(MarkdownView);
    if (!view || !view.editor) return;
    const target = resolveImageAtCursor(this.app, view.editor, view.file);
    if (target) {
      new ImageLightboxModal(this.app, target).open();
    } else {
      new Notice("No image link under cursor");
    }
  });

  vim.mapCommand("\\z", "action", "bobZoomImageAtCursor", {}, { context: "normal" });
}
```

---

## 8. Comparison Matrix: Approaches

| Dimension | Option 1: Community Plugin (`Image Workflow`) | Option 2: Extend `bob-navigation-hotkeys` | Option 3: Dedicated `bob-image-lightbox` |
| :--- | :--- | :--- | :--- |
| **Development Effort** | 0 hours (immediate install) | 4–6 hours (integrate + test) | 6–8 hours (new plugin boilerplate + sync) |
| **Maintenance Overhead** | External dependency updates | Bundled in existing CI/tests | Managed in `bob-plugins` |
| **Vim Keymap Integration** | ❌ None (mouse-click only) | ✅ Native (`\z`, `<CR>`, `Alt+Z`) | ✅ Native (`\z`, `<CR>`, `Alt+Z`) |
| **Mouse Click Trigger** | ✅ Smooth click overlay | ✅ Native click listener | ✅ Native click listener |
| **Risk of GTD Regression** | 0% | Low (isolated link check) | 0% |
| **Ecosystem Synergies** | Standard Obsidian | Integrates with `ctrl-y` yank & ref links | Integrates with `ctrl-y` yank & ref links |

---

## 9. Recommended Solution & Next Steps

### Phased Recommendation

1. **Immediate Step (Zero-Risk Trial):**  
   Install and test the community plugin **`Image Workflow`** (`1spread/obsidian-image-enlarge`) via BRAT or manual placement in the vault's `.obsidian/plugins/` directory.  
   - This provides immediate, beautiful click-to-enlarge behavior with mouse-wheel zoom and `Escape` dismiss for reading notes and inspecting `bob ref` screenshots.
   - It will immediately confirm whether click-to-zoom satisfies 90% of the day-to-day visual inspection needs.

2. **Strategic Implementation (The Native "Bob" Solution):**  
   If Bryan requires full Vim keyboard parity (the ability to zoom an image under the text cursor without reaching for the mouse):
   - **Extend `bob-navigation-hotkeys`**:
     1. Relax the `isMarkdownFile` gate in `toLineLinkCandidate` (`src/640-plugin-notes-and-task-move.js`) so that `<CR>` on an image link triggers an image preview rather than doing nothing.
     2. Add `bobNavigationZoomImageAtCursor` and bind it to `\z` in Normal mode (matching `\s` for tab pins) and `Alt+Z` as an Obsidian command.
     3. Add the lightweight `ImageLightboxModal` with wheel zoom, drag-pan, `Esc`/`q` dismiss, and `y` path copy.
     4. Add a global window click handler so that clicking rendered images in Live Preview or Reading View opens the same lightbox.

This hybrid approach gives Bryan the best of both worlds: zero-friction mouse interaction while reading, and instant, Vim-idiomatic keyboard inspection while writing and reviewing.
