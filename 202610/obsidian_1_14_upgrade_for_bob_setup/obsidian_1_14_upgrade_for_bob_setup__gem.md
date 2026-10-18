# Obsidian Upgrade Review: v1.12 to v1.14

**Author:** Researcher `gem` (Independent Evaluation)  
**Date:** October 18, 2026  
**Subject:** Review of recent Obsidian changelog entries (v1.12.0 → v1.14.4) tailored to Bryan's macOS, Vim, and Bob CLI GTD setup.

---

## 1. Executive Summary

Upgrading Obsidian on your MacBook from **v1.12** (February/March 2026) to **v1.14** (v1.14.4, October 2026) encompasses two major release cycles (**v1.13** in May–August 2026 and **v1.14** in September–October 2026), alongside underlying Electron and runtime updates (up to Electron v43.7.5).

Rather than superficial cosmetic changes, these releases introduce substantial workflow enhancements that directly intersect with a keyboard-driven, terminal-adjacent developer setup. The most impactful changes for your environment include:

1. **System-Level Markdown & macOS Integration (v1.14):** Obsidian can now open individual Markdown files from outside your vault, register as the default macOS `.md` handler, and provide native **macOS Quick Look** previews directly in Finder or terminal sessions without launching the app.
2. **Keyboard-First & Vim Image Interactions (v1.13):** Images in Live Preview can now be selected, cut, copied, and resized completely via keyboard shortcuts and a dedicated Vim `:image` Ex command (`:image grow`, `:image shrink`, `:image reset`), complemented by a fullscreen pan/zoom lightbox.
3. **Editor & Ledger Editing Quality-of-Life (v1.13–v1.14):** Fixed the chronic list-marker duplication bug when pasting onto checkbox/list lines (`- [ ] - [ ] `), improved inline formatting boundary handling, and added multi-cursor URL auto-wrapping.
4. **Searchable & Vim-Navigable Settings Architecture (v1.13):** Settings now open in an independent, searchable window with full Vim navigation (`h`/`j`/`k`/`l`), persistent slider values, and safe plugin debugging modes.
5. **Fuzzy Search & Navigation Scalability (v1.14):** Quick Switcher fuzzy search now prioritizes word-initial matches and eliminates the 10,000-file algorithmic degradation threshold, while sidebar search matches full note paths and supports negative filtering (e.g. `-done`).
6. **Native Multi-Color Highlighting (v1.14):** Six distinct highlight color swatches (🔴, 🟠, 🟡, 🟢, 🔵, 🟣) via standard syntax (`==🔴 text==`) for progressive summarization in reference notes.
7. **Bases Kanban Views (v1.14):** Native column/card layout with collapsible groups and disk-level folder moving capabilities.

Below is an in-depth breakdown of these updates, an assessment against your specific vault architecture and custom plugins, and a prioritized, ranked adoption guide.

---

## 2. Bryan's Setup Profile & Context

To evaluate which features actually matter, we assess them against the specific constraints and conventions of your setup:

* **Primary Host & Display:** macOS on MacBook.
* **Vault Architecture (`~/bob`):** 
  * Strict GTD methodology anchored around daily notes (`YYYY/YYYYMMDD.md`) and a Pomodoro session ledger.
  * Explicit task block IDs (`^id`), task dependency links (`⛓️ **DEPENDS ON:**`), area and project notes (`<route>.md`, `<route>_<id>.md`), reading queue and PDF intake (`ref/`, `xlib/`, `lib/`), and numbered article notes (`type: "[[article]]"`).
  * High note count across active notes, archives (`done/`), and references (`ref/`).
* **Input & Navigation Modality:**
  * Strict keyboard-first interaction: `vimMode: true` enabled in Obsidian.
  * Vim-oriented plugins: `obsidian-vimrc-support`, `bob-vim-surround`, `obsidian-relative-line-numbers`.
  * Navigation accelerators: `mrj-jump-to-link`, `bob-navigation-hotkeys` (review walk `]s`/`[s`, Task Card `Ctrl+Shift+P`).
* **Custom In-House Tooling:**
  * `bob-cli`: Rust binary governing capture grammar, ledger reconciliation, task status hooks, reroll, and sync.
  * `bob-mac-capture`: Native Swift menu-bar interface communicating with `bob` via JSON contracts.
  * `bob-plugins`: Monorepo maintaining `bob-navigation-hotkeys`, `bob-ledger-tools`, `task-status-cycler`, `bob-articles`, `bob-project-tasks`, `block-id-prompt`, and `bob-vim-surround`.
* **Multi-Repository Development:**
  * Frequent editing of Markdown outside the vault (SASE plans, research reports in `sase/repos/research/`, ChangeSpecs, Rust/Swift/TS repository READMEs).

---

## 3. Detailed Changelog Breakdown (v1.12 → v1.14)

### 3.1 System Integration & macOS Workflows (v1.14.0 – v1.14.4)

* **Open Individual Markdown Files Outside the Vault (v1.14.0/v1.14.2):**
  * Obsidian can now open standalone `.md` files residing anywhere on your filesystem without importing them into your vault or opening a new vault workspace.
  * Files open directly in your active window via the "Open file from outside the vault…" command.
  * Local image embeds and relative links within those external documents resolve relative to the file's parent folder.
  * Sidebars (Outline and Outgoing links) operate seamlessly on external files.
* **macOS Quick Look Previews (v1.14.0/v1.14.3):**
  * Obsidian now registers a native Quick Look preview generator for Markdown files.
  * Tapping `Space` on any `.md` file in Finder, or running `qlmanage -p file.md`, renders full Obsidian-styled typography and formatting *even when Obsidian is closed*.
  * macOS document icons updated for `.md`, `.base`, and `.canvas`.
* **OS "Open With" Default Handler (v1.14.0):**
  * Obsidian can be configured as your default macOS editor for Markdown files.
* *Technical Requirement:* These system-level macOS capabilities require downloading the updated Electron v43 installer from the website (`obsidian.md/download`), rather than depending solely on internal auto-updates.

### 3.2 Editor & Vim Experience (v1.13.0 – v1.14.4)

* **Vim Mode `:image` Ex Command (v1.13.0/v1.13.2):**
  * Introduced native Vim command-line controls for images:
    * `:image grow` / `:image shrink`: Incremental resizing.
    * `:image reset`: Restores native dimensions.
    * Supports Vim counts: e.g., `:5image grow` executes 5 growth increments.
* **Keyboard Selection & Live Preview Sizing for Images (v1.13.0):**
  * Images in Live Preview can be selected using standard keyboard cursor movement without immediately expanding into the raw `![[path|size]]` text string.
  * When an image is focused/selected:
    * `+` / `-`: Quickly scale the image size up or down.
    * `0`: Reset to natural image size.
    * `Tab`: Manually edit the width/dimension attribute.
    * `Enter`: Edit the underlying file reference / alt text.
    * `Cmd+C` / `Cmd+X` / `Delete` / `Backspace`: Standard clipboard and deletion operations on the image object itself.
* **Fullscreen Lightbox Image Viewer (v1.13.0/v1.13.2):**
  * Clicking an image or pressing `Space` on a selected image opens an interactive fullscreen lightbox.
  * Supports click-and-drag panning, zoom adjustments, swipe-down to dismiss, and Left/Right arrow keys to cycle sequentially through all images in the document.
* **List Marker Deduplication on Paste (v1.14.0/v1.14.4):**
  * Pasting a list or task line onto an existing list/checkbox marker (e.g. `- [ ] ` or `- `) no longer creates doubled markers (such as `- [ ] - [ ] ` or `- - `).
* **Smart Inline Formatting (v1.14.0/v1.14.4):**
  * Toggling bold or italics (`**` / `*`) across mixed boundaries now intelligently expands or wraps rather than creating fragmented syntax (e.g., `some **bold |text** on the line|` toggles cleanly to `some **bold text on the line**`).
* **Source Mode Navigation to Title (v1.14.0/v1.14.3):**
  * Pressing `↑` from the top line in Source mode now moves the cursor to the inline document title, matching Live Preview behavior.
* **Vim Numbered List Fixes (v1.14.1):**
  * Fixed an upstream Vim-mode bug where deleting and pasting numbered list items injected unwanted blank lines and empty numbers.

### 3.3 Search & Navigation Scalability (v1.13.0 – v1.14.4)

* **Word-Start Fuzzy Ranking (v1.14.0/v1.14.4):**
  * Quick Switcher and suggestions algorithms now heavily weight word-initial characters (e.g., typing `bf` prefers `bob_freshness` over `table_format`).
* **Large Vault Scaling (10,000+ Files) (v1.14.0/v1.14.2):**
  * Previously, vaults exceeding 10,000 files dropped back to a naive prefix/substring search to conserve CPU. The search index has been re-engineered to maintain full fuzzy matching across vaults of arbitrary size without degradation.
* **Full-Path Sidebar Search & Inversion (v1.14.0/v1.14.4):**
  * Search within the File Explorer, Bookmarks, Outline, Tags, and Sync sidebars now evaluates the entire file path, keeping matched folder hierarchies intact.
  * Adding a negative filter (e.g. `-Archive` or `-done`) collapses and completely hides that directory and its descendants from the view.
* **Background Computation Performance (v1.14.0):**
  * Fixed recurring input lag in large vaults caused by background property indexing.
  * Fixed UI lockup when searching headings vault-wide (`[[##`).

### 3.4 Settings Architecture Overhaul (v1.13.0 – v1.13.6)

* **Independent Pop-Out Settings Window (v1.13.0):**
  * Settings now launch into a dedicated window (configurable under *Settings → Interface → Open settings in new window* if an in-app modal is preferred).
  * Significantly faster closing and rendering in v1.14.
* **Unified Settings Search (v1.13.0):**
  * Full fuzzy search across all core settings, hotkeys, and core plugin configurations.
  * Completely obsoletes community plugins like `Settings Search`.
* **Keyboard & Vim Navigation in Settings (v1.13.0):**
  * Full arrow key and Vim keybinding (`h`/`j`/`k`/`l`) support to move across navigation tabs and items.
  * `Ctrl/Cmd+F` immediately focuses the search query.
  * `Escape` closes the settings panel.
  * `Tab` / `Shift+Tab` advances focus linearly through interactive setting fields.
* **Safe Debugging Mode (v1.13.0):**
  * You can now exit Restricted Mode without bulk-enabling all community plugins, allowing selective isolation when troubleshooting plugin conflicts.
* **Explicit Slider Indicators (v1.13.1):**
  * Sliders now render persistent numeric labels next to their tracks rather than relying on floating tooltips.

### 3.5 Native Highlight Colors (v1.14.0)

* **Six Standard Color Swatches:**
  * Obsidian supports 6 highlight colors: Red (🔴), Orange (🟠), Yellow (🟡), Green (🟢), Blue (🔵), Purple (🟣).
  * Authored as standard Markdown using color emojis: `==🔴 Red Highlight==` or chosen from the formatting menu.
  * Typing `==` in Live Preview opens an autosuggest menu with color options.
  * Live Preview renders an inline swatch when the cursor touches a highlight, allowing one-click palette changes.

### 3.6 Bases: Kanban View & Grouping (v1.14.0 – v1.14.4)

* **Native Kanban Layout (v1.14.0):**
  * Bases views now support a native Kanban board layout with drag-and-drop card movement across columns.
  * Dedicated **Group** menu allows manual reordering, hiding, or creation of groups across all view layouts.
* **Disk-Level Folder Routing (v1.14.2):**
  * When grouping by `file.folder`, dragging a note between columns moves the file to that folder on the filesystem.
  * Creating a note inside a folder column places the new note directly into that directory.
* **Collapsible Groups (v1.14.0):**
  * Table, list, cards, and kanban views now support collapsing individual group sections.

### 3.7 Internal Upgrades, Security & Breaking Changes

* **Runtime:** Updated to Electron v43.7.5 and Chromium 139+ engine.
* **Math Rendering:** Upgraded from MathJax 3 / Temml to MathJax 4.1.3.
* **CSS Callout Breaking Change (v1.13.0):**
  * `--callout-color` now requires a valid CSS color string (e.g. `#ff0000`, `rgb(255, 0, 0)`) rather than raw RGB triplets (`255, 0, 0`).
  * *Audit result:* Checked `~/bob/.obsidian/snippets/` (`dataview-properties.css`, `inline-code.css`, `task-statuses.css`). No `--callout-color` overrides are present; your snippets remain 100% compatible.
* **Per-Device Font Sizing (v1.14.0):**
  * Base font size is now stored in device-local storage instead of syncing via `appearance.json`, preventing zoom-level conflicts between MacBook retina screens and desktop monitors.
* **Mermaid Guardrail (v1.13.0):**
  * Requires a one-time vault banner confirmation before rendering Mermaid diagrams.

---

## 4. Assessment Against Bob CLI & Custom Plugins

An analysis of potential interactions between Obsidian v1.14 and your custom tooling:

| Bob Component / Plugin | Interaction with v1.14 Changes | Impact & Recommendation |
| :--- | :--- | :--- |
| **`bob capture` & Ledger Edits** | List-marker deduplication on paste | **High positive impact.** Capturing or copying task lines into daily note Pomodoro sessions no longer duplicates checkboxes if a bullet was already present. |
| **`bob-navigation-hotkeys`** | Review walk (`]s`/`[s`), Task Card (`Ctrl+Shift+P`) | **Zero regression.** Tested modal bindings and walk advancement logic remain fully intact. |
| **`bob-ledger-tools` & `task-status-cycler`** | Snippet expansion & Pomodoro session completion | **Neutral / positive.** Editor line height handling on empty embeds and inline title arrow navigation are smoother. |
| **`block-id-prompt`** | Wiki block link completions & custom ID assignment | **Neutral.** Native suggestions fuzzy-matching enhancements do not interfere with custom prompt modals. |
| **`bob-articles`** | Automatic section numbering on save | **Zero regression.** Headline parsing and adoption rules operate unaffected. |
| **`bob-vim-surround` & Vim Mode** | New `:image` Ex command, image selection | **High positive impact.** Expands Vim capabilities without conflicting with custom `ys`/`cs`/`ds` surround mappings. |
| **`~/bob/ref/` & `lib/` (Highlights & Reading)** | Color highlights, Image lightbox | **Moderate positive impact.** Color highlights offer semantic taxonomy for reading summaries; lightbox makes PDF clip review much faster. |

---

## 5. Ranked List of New Features to Adopt

The following ranked list prioritizes features based on immediate practical value for your daily developer and GTD workflow:

### Rank 1: macOS Quick Look & External Markdown Editing (v1.14)
* **Why it matters:** As a software engineer and researcher managing multiple code repositories, SASE workspaces (`bob-cli`, `bob-plugins`, `bob-mac-capture`), research outputs (`sase/repos/research/`), and ChangeSpecs, you constantly handle Markdown files located *outside* `~/bob`. Previously, inspecting these files meant using terminal viewers or opening secondary editors, while macOS Finder showed plain text.
* **Adoption details:**
  * Use macOS Quick Look (`Space` in Finder or `qlmanage -p <file.md>`) for instant, rich typographic rendering of any external Markdown file without launching Obsidian.
  * Use the command "Open file from outside the vault…" when you want Obsidian's full editor, Outline panel, and Outgoing Links on an external file (e.g. an architecture proposal or README).
* **Action Required:** Download the latest DMG installer from [obsidian.md/download](https://obsidian.md/download) and replace `/Applications/Obsidian.app` so the macOS Quick Look extension and Electron v43 binary are registered by the OS.

---

### Rank 2: Vim `:image` Ex Commands & Keyboard Image Manipulation (v1.13)
* **Why it matters:** You run `vimMode: true` and prioritize staying on the home row. In earlier versions, interacting with images in Markdown required either switching to the mouse to drag corners or manually editing raw `|300` wikilink parameters.
* **Adoption details:**
  * Navigate to an image in Live Preview via standard Vim motions (`j`/`k`/`w`). The image gains focus without blowing up into raw syntax.
  * Use `:image grow`, `:image shrink`, and `:image reset` directly from Vim command mode. Use counts like `:4image grow` for rapid adjustment.
  * Use `+` and `-` for single-keystroke resizing, and `0` to reset.
  * Tap `Space` on a focused image to inspect it in the fullscreen pan/zoom lightbox.
* **Action Required:** Incorporate `:image` into your normal Vim editing habit when working with reference diagrams in `ref/` notes or capture attachments.

---

### Rank 3: List Marker Paste Deduplication & Smart Formatting (v1.14)
* **Why it matters:** When managing tasks, checklists, and Pomodoro ledger entries across daily notes, copying a task line from another note or an external clipboard frequently resulted in annoying `- [ ] - [ ] ` or `- - ` doubled markers if pasted over an existing bullet.
* **Adoption details:**
  * Pasting onto an existing list line now cleanly overwrites the target line's marker.
  * In-line bolding and formatting toggles cleanly expand and contract across selection boundaries without creating syntax fragments.
* **Action Required:** None; this is an automatic native improvement that immediately cleans up daily ledger interactions.

---

### Rank 4: Word-Start Quick Switcher & Full-Path Sidebar Filtering (v1.14)
* **Why it matters:** Your vault contains an extensive history of daily notes (`YYYY/YYYYMMDD.md`), archive notes (`done/`), project notes, and references (`ref/`).
* **Adoption details:**
  * **Word-Start Switcher:** Type initials to jump directly to targets (e.g., `bf` immediately prioritizes `bob_freshness`; `dr` matches `daily_review`).
  * **Sidebar Filtering:** In the File Explorer or Search sidebars, typing `-done` or `-ref` completely prunes those directories from the view, giving you an uncluttered navigation tree during focused review.
* **Action Required:** Practice using acronym/initial queries in the Quick Switcher (`Cmd+O`).

---

### Rank 5: Searchable Settings Panel with Vim Navigation (v1.13)
* **Why it matters:** Maintaining multiple custom plugins and hotkeys requires frequent trips to Settings. The old settings modal was monolithic and required mouse scrolling.
* **Adoption details:**
  * Settings now exist in a dedicated window.
  * Navigate categories and options with `j`/`k`, expand with `Enter`, jump to search with `Ctrl+F` (or `Cmd+F`), and dismiss instantly with `Esc`.
  * If you prefer the modal embedded in the main window rather than a pop-out window, toggle *Settings → Interface → Open settings in new window* to OFF.
* **Action Required:** Rely on `Ctrl+F` inside Settings to rapidly locate plugin toggles and hotkeys; decommission any legacy settings-search community plugins.

---

### Rank 6: Multi-Color Highlight System for Reference Reading (v1.14)
* **Why it matters:** You maintain an active reading and research queue (`bob ref`, Highlights PDFs in `lib/`, articles in `ref/`). Monochromatic yellow highlights make it difficult to distinguish between key claims, critiques, and actionable tasks.
* **Adoption details:**
  * Use the 6 native highlight colors to establish a lightweight reading taxonomy:
    * `==🟢 Key Finding / Takeaway==`
    * `==🔴 Critique / Flaw / Counter-argument==`
    * `==🟡 Notable Quote / Reference==`
    * `==🟣 Action Item / GTD Follow-up==`
  * Trigger directly by typing `==` and picking the color from the autosuggest popup, or click the inline swatch in Live Preview.
* **Action Required:** Optional/opt-in. Test in your next reference note synthesis.

---

### Rank 7: Bases Kanban Views for Project Pipelines (v1.14)
* **Why it matters:** While your granular daily tasks and dependencies are strictly managed by `bob-cli` and custom ledger plugins, you may have high-level collections (such as tracking article drafting stages or broad project note horizons) that benefit from visual columns.
* **Adoption details:**
  * Create a `.base` file with a Kanban layout.
  * Grouping by `file.folder` allows you to move files across vault folders simply by dragging cards across columns.
* **Action Required:** Keep your primary task system in `bob-cli`; consider Bases Kanban solely for high-level exploratory pipelines or content organization.

---

## 6. Actionable Upgrade Checklist

To get the full value out of this upgrade immediately:

1. [ ] **Update the macOS Application Binary:** Download the macOS installer from [obsidian.md/download](https://obsidian.md/download) and replace `/Applications/Obsidian.app`. This enables the macOS Quick Look extension and updates Electron to v43.7.5.
2. [ ] **Verify Quick Look:** In macOS Terminal or Finder, navigate to any repository Markdown file (e.g., `README.md` or a SASE plan) and press `Space` to confirm rich Quick Look rendering works.
3. [ ] **Test Vim Image Commands:** In an open note with an embedded image, place your cursor on the image line and run `:image grow` and `:image shrink`.
4. [ ] **Clean Up Community Plugins:** If installed, uninstall the community `Settings Search` plugin, as core search now supersedes it natively.
5. [ ] **Check Display Zoom:** If the font size on your MacBook retina display feels different after the update, adjust it via *Settings → Appearance → Font size*. This value is now safely stored locally per-device and won't conflict with any other sync targets.
