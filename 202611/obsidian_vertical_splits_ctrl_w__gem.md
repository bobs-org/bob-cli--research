# Vertical Split Window Management & `<ctrl+w>` Prefix Design for Obsidian

> **Bottom line:** Add a native **`<ctrl+w>` Window Prefix Mode, geometric split engine, and live context-aware HUD** inside **`bob-navigation-hotkeys`** (`bob-plugins`)—do **not** implement this in `obsidian_vimrc.md` (`obsidian-vimrc-support`) and do **not** adopt clone-and-detach plugins like `obsidian-tab-shifter`. Intercept `<ctrl+w>` at the active window's capture phase **only when outside Vim Insert/Replace mode and editable form inputs**, push a transient Obsidian `Scope`, and move live `WorkspaceLeaf` instances across splits in place. Pair the shortcut with a two-tier hint (`0ms` status-bar pill + `180ms`-delayed bottom-docked HUD) and subtle active-split focus chrome so side-by-side splits become immediately legible.

---

## 1. Grounded Diagnosis of the Current Workspace

Inspecting `~/tmp/screenshots/20261115_171818.png` alongside the vault configuration (`gh:bobs-org/bob`) and `bob-plugins` clarifies both the target workflow and why existing tools fall short:

- **Active visual environment (`20261115_171818.png`, `.obsidian/appearance.json`):**
  - Obsidian on **macOS** using Obsidian's **Default Light** theme (`.obsidian/appearance.json` enables 4 CSS snippets—`task-statuses`, `dataview-properties`, `inline-code`, `ref-highlights`—and no community theme).
  - **Left vertical split (`WorkspaceTabs`):** Two pinned tabs (`20261115`, `dash`) plus an active unpinned tab (`sase_blog`) holding keyboard focus (purple Vim Normal-mode block cursor at line 34, relative line numbers).
  - **Right vertical split (`WorkspaceTabs`):** One active unpinned tab (`sase_blog_contents`), also styled with a white active tab header (`is-active` local to its `WorkspaceTabs`) and identical breadcrumb chrome.
  - **Status bar:** Bottom-right includes the `bob-navigation-hotkeys` bracket-mode widget (`[[ s w n b ]]`).
- **Two structural gaps exposed by the screenshot:**
  1. **Zero keyboard split navigation or cross-split tab movement:** Neither `obsidian_vimrc.md` nor `.obsidian/hotkeys.json` binds any split focus or `<ctrl+w>` commands. `bob-navigation-hotkeys` currently provides only intra-group tab actions (`move-tab-left`, `move-tab-right`, `duplicate-current-tab`, `toggle-current-tab-pin`, `close-tabs-left`, `close-tabs-right`, `close-other-tabs` in `plugins/bob-navigation-hotkeys/src/490-plugin-lifecycle.js:463-501`). Moving `sase_blog_contents` into the left group (`^split-tabs`) or jumping focus left/right requires the trackpad.
  2. **Near-invisible active-split distinction:** In Obsidian's Default Light theme, the left split's active tab (`sase_blog`) and the right split's active tab (`sase_blog_contents`) look nearly identical. Only the small editor cursor indicates which split owns focus—and on Reading view, Empty tabs (`+`), PDFs, Canvas, or scrolled notes, even that cue disappears.

---

## 2. Critique of the Plan & Implementation Approaches

### 2.1 Is the overall plan a good idea?

**Yes—high-value and well-motivated**, especially for Bryan's side-by-side writing and task-review workflow (`bob#^ctrl-w-keymaps` blocking `bob#^split-tabs` in `bob.md:65, 115-116`). However, implementing `<ctrl+w>` naively via `.obsidian.vimrc` or file-reopening plugins would introduce severe reliability bugs.

### 2.2 Comparing the Three Implementation Paths

| Approach | How It Intercepts `<ctrl+w>` | How It Moves Tabs / Splits | Verdict |
| :--- | :--- | :--- | :--- |
| **A. `obsidian_vimrc.md` (`obsidian-vimrc-support`)** | CodeMirror 6 Vim `nmap <C-w>...` inside `MarkdownView` editors | Calls Obsidian commands (`obcommand`) or JS snippets (`supportJsCommands` is currently `false`) | **Reject** — broken by default in CodeMirror Vim, dead in non-editor views, poor hint UI |
| **B. Community Plugins (`obsidian-tab-shifter`, `pane-relief`) or New Standalone Plugin** | Obsidian `HotkeyManager` (single-key chords only; cannot do two-key `<ctrl+w><key>` prefixes) | `tab-shifter`: opens new leaf via `activeLeaf.view.file` + `detach()`. `pane-relief`: `children.splice` DOM/tree reparenting | **Reject as standalone; borrow techniques** — `tab-shifter` loses state/non-file views; standalone plugin fragments shared Bob utilities |
| **C. Extend `bob-navigation-hotkeys` (`bob-plugins`)** | Window capture-phase listener (guarded for Insert/input modes) + `app.keymap.pushScope()` prefix state machine | Spatial `getBoundingClientRect()` navigation + in-place `WorkspaceLeaf` reparenting (`removeChild` / `insertChild` / `splitLeaf`) with safe fallback | **Recommended** — works everywhere, preserves state, zero plugin sprawl, native Bob HUD & E2E test harness |

### 2.3 Why `obsidian_vimrc.md` (`obsidian-vimrc-support`) Fails Here

Inspecting `replit/codemirror-vim` and `esm7/obsidian-vimrc-support` reveals three fatal flaws if `<ctrl+w>` lives in `obsidian_vimrc.md`:

1. **CodeMirror Vim swallows `<C-w>` before `nmap <C-w>...` can match unless explicitly unmapped:**
   In `replit/codemirror-vim/packages/codemirror-vim-core/vim.js:200`, `defaultKeymap` defines `{ keys: '<C-w>', type: 'idle', context: 'normal' }`. Even after `nmap <C-w>h ...` calls `defaultKeymap.unshift(command)` (`vim.js:6720-6721`), `commandMatches()` (`vim.js:3621-3641`) scans the entire `keyMap` collecting both `partial` and `full` matches, and `matchCommand()` (`vim.js:1602-1613`) returns `matches.full[0]` before checking `matches.partial.length`. Without `nunmap <C-w>`, `<C-w>` hits the built-in `idle` full match immediately; and when handled, `packages/codemirror-vim/src/index.ts:248-252` calls `e.preventDefault()` and `e.stopPropagation()`.
2. **Non-editor splits become dead-end traps:**
   `obsidian-vimrc-support` binds keys only onto a `MarkdownView`'s CodeMirror instance (`main.ts:276-316`). If `<ctrl+w>v` / `<ctrl+w>n` focuses an **Empty tab** (`+`), or the right split holds **Reading view**, a **PDF**, **Canvas**, **Graph**, **Search**, or **Sidebar** (`File Explorer`, `Backlinks`), Vim mode is inactive—pressing `<ctrl+w>h` to move back or `<ctrl+w>q` to close that split does nothing on macOS (or closes the tab via `Mod+W` on Linux!).
3. **No rich hint UI:**
   `obsidian-vimrc-support`'s `displayChord` (`main.ts:618-663`, enabled in Bryan's `.obsidian/plugins/obsidian-vimrc-support/data.json`) only renders raw accumulated keys like `" <C-w>-"` in a plain left status-bar span inside CM6 editors. It cannot show available actions, dynamic split context, or work outside Markdown Edit mode.

### 2.4 Why `obsidian-tab-shifter` Pattern Is Insufficient (and What to Borrow from `pane-relief`)

- **`jsrozner/obsidian-tab-shifter` (`src/plugins/TabShifterPlugin.ts:39-112`)** moves a tab by checking `activeLeaf.view.file`, creating a brand-new leaf via `workspace.getLeaf('split', 'vertical')` or `workspace.createLeafInParent(targetGroup, index)`, calling `activeLeaf.detach()`, and running `await newLeaf.openFile(activeFile)`. That breaks on Empty tabs, Graph, and non-file views; destroys editor undo/scroll/cursor/folds/Vim state/`LeafHistory`; loses `leaf.pinned`; leaves an explicit `// todo support initial split left` gap; and wraps blindly by leaf discovery order (`getParentsForEachLeaf`) rather than screen geometry.
- **`pjeby/pane-relief`** demonstrates much stronger Obsidian workspace techniques we should borrow:
  - Direct parent `children` splicing + DOM synchronization + `recomputeChildrenDimensions()` + `onLayoutChange()` + `setActiveLeaf()` (`src/pane-relief.ts:220-236`—the exact pattern `bob-navigation-hotkeys`'s own `moveActiveTab` already uses in `630-plugin-vim-link-and-leaves.js:361-436`).
  - Non-destructive CSS zoom toggling via `.should-maximize` / `.has-maximized` / `.is-maximized` (`src/maximizing.ts:100-170`).
  - Multi-window (`WorkspaceFloating` / popout) awareness via `PerWindowComponent` / `getContainer()`.

### 2.5 Why `bob-navigation-hotkeys` Is the Right Home

`bob-navigation-hotkeys` (`v2.82.0`) already owns:
1. All tab-manipulation commands (`move-tab-left`, `move-tab-right`, `duplicate-current-tab`, `toggle-current-tab-pin`, `close-tabs-*`).
2. Battle-tested Vim-mode detection (`resolveVimCodeMirror`, `getCurrentVimMode`, `isVimNormalModeEditor` in `610-plugin-jumps-and-counted-keys.js:886-937`) and `Ctrl+[` / `Escape` dismissal helpers (`814-832`).
3. Established card/HUD CSS tokens (`.bob-key-card-*`, `.bob-copy-card-*`, `.bob-bracket-mode-*` in `styles.css`) and Node/Obsidian Electron E2E test infrastructure (`scripts/test-obsidian-*.cjs`).

---

## 3. Called-Out Adjustments to Requirements

To make `<ctrl+w>` both predictable in complex layouts and safe alongside Vim and Obsidian defaults, I recommend **five explicit requirement adjustments**:

### Adjustment 1 — Clarify "Window" Means Active Tab (`WorkspaceLeaf`), While Keeping Column Swap Separate
- **Prompt wording:** *"move the current window to a split on the left or right... moving the last window from a split to the other side."*
- **Adjustment:** In Obsidian's tabbed splits (`20261115_171818.png` has 3 tabs left, 1 tab right), `<ctrl+w>H` and `<ctrl+w>L` should move **only the active tab (`WorkspaceLeaf`)**, not the entire tab group (`WorkspaceTabs`) and not OS popout windows. When that tab was the last leaf in its origin `WorkspaceTabs`, moving it collapses/destroys the empty origin split.
- **Why:** If `<ctrl+w>L` moved all 3 left tabs when focused on `sase_blog`, it would drag pinned `20261115` and `dash` across splits. Adding `<ctrl+w>x` ("Swap split column with neighbor") covers the whole-column swap case cleanly without merging tabs.

### Adjustment 2 — Make `<ctrl+w>h` / `<ctrl+w>l` Strictly Directional (No Wrap) and Add `<ctrl+w><ctrl+w>` / `<ctrl+w>w` for Toggling
- **Prompt wording:** *"`<ctrl+w>h` and `<ctrl+w>l` keymaps should navigate to the other (i.e. not currently focused) split when a vertical split is active."*
- **Adjustment:** Make `h` / `l` (and `j` / `k`) **strictly spatial and clamped at edges** (always left / right / down / up), and make **`<ctrl+w><ctrl+w>`** (quick double-tap!) and **`<ctrl+w>w`** cycle / toggle to the **other** split (wrapping across splits).
- **Why:** If `h`/`l` wrapped around even in a 2-split layout, hitting `<ctrl+w>l` while *already* on the right split would jump you *left*, breaking spatial muscle memory ("`h` always puts me left; `l` always puts me right") and failing completely with 3+ splits. Double-tap `<ctrl+w><ctrl+w>` gives an even faster zero-hand-shift toggle between two splits. *(If Bryan strictly wants 2-split wrap on `h`/`l`, expose a single boolean option `wrapDirectionalFocus`, defaulting to `false`.)*

### Adjustment 3 — Explicit 4-State Behavior for `<ctrl+w>H` and `<ctrl+w>L` (Preventing Phantom / Empty Splits)
The requirement asks `<ctrl+w>H`/`<ctrl+w>L` to both create splits, move across splits, and destroy emptied splits. Spelling out all edge cases prevents surprising behavior:

| Starting State | Action | Result |
| :--- | :--- | :--- |
| **1. Single pane, `>= 2` tabs** (e.g., `dash`, `sase_blog*`) | `<ctrl+w>L` (or `H`) | Moves `sase_blog` into a **new right (or left) vertical split**, keeping `dash` on the other side |
| **2. Single pane, `1` tab only** | `<ctrl+w>H` or `L` | **Safe no-op** + subtle hint (`"Only 1 tab open — press v to split"`). Moving the sole tab cannot create a split without leaving a phantom empty/duplicate pane |
| **3. Multi-split, target neighbor split exists, source split has `>= 2` tabs** | `<ctrl+w>L` (from left split) or `H` (from right split) | Moves active tab into adjacent split's `WorkspaceTabs` (after its pinned tabs, focused); source split stays open on its previous active tab |
| **4. Multi-split, target neighbor split exists, source split has `1` tab** (e.g. `sase_blog_contents` in screenshot) | `<ctrl+w>H` (right → left) | Moves `sase_blog_contents` into left split's `WorkspaceTabs` **and destroys/collapses the emptied right split** |
| **5. Multi-split, already at outermost split, `>= 2` tabs in current split** | `<ctrl+w>H` on leftmost / `<ctrl+w>L` on rightmost | Splits active tab out into a **new outermost vertical split** on that side (supports `2 → 3` columns cleanly) |
| **6. Multi-split, already at outermost split, `1` tab in current split** | `<ctrl+w>H` on leftmost / `<ctrl+w>L` on rightmost | **Safe no-op** + subtle hint (`"Already leftmost/rightmost split"`). Prevents pointless empty-column churn |

*(Pinned-tab nuance: When moving a pinned tab like `20261115` into an existing `WorkspaceTabs`, preserve `leaf.pinned = true` and insert it at the end of the target group's pinned prefix; when moving an unpinned tab, insert at the end of the target group or immediately after its active tab—never ahead of existing pinned tabs!)*

### Adjustment 4 — Strictly Yield `<ctrl+w>` in Vim Insert/Replace Mode & Editable Inputs (Plus Linux `Mod+W` Note)
- **Evidence:** Bryan's own `bob/lit/practical_vim_notes.md:27` notes `<C-w>` deletes the last word in Insert mode, matching `vim.js:198` (`context: 'insert'`). Search bars, File Explorer inline renames, modals, and `bob-command-mode` also have `<input>`/`<textarea>` elements where `<C-w>` must edit text.
- **Adjustment:** `<ctrl+w>` enters Window Prefix Mode **only when**:
  1. No modal / prompt (`modal-container`) is capturing input (or only when active modal is not a text input),
  2. `document.activeElement` is not a non-CM editable field (`INPUT`, `TEXTAREA`, `SELECT`, or non-Obsidian-CM `[contenteditable="true"]`), and
  3. If focus is inside an active CodeMirror editor, `getCurrentVimMode(cm)` is **not** `'insert'` and **not** `'replace'`.
- **Platform note (macOS vs. Linux):** On macOS (`20261115_171818.png`), Obsidian binds `workspace:close` to `Cmd+W` (`Mod+W`), leaving `Ctrl+W` free. If Bryan ever opens Obsidian on **Linux or Windows**, `Mod+W` *is* `Ctrl+W` and Obsidian >= 1.14's built-in `Keymap` window-capture listener runs before plugins load (`610-plugin-jumps-and-counted-keys.js:576-579`), so `workspace:close` would close the tab unless `workspace:close` is rebound in `hotkeys.json` (e.g., to `Mod+Shift+W` / `Alt+W`) or another prefix is used on Linux.

### Adjustment 5 — Curated Keymap Vocabulary (Replace Destructive `<C-w>o` with Non-Destructive Zoom `z`)
Vim's `<C-w>o` ("close all *other* windows") is unforgiving on a tabbed Obsidian workspace with pinned notes. I recommend replacing one-key "close all other splits" with **non-destructive Split Zoom (`<ctrl+w>z`)**, plus a compact, Vim-idiomatic set of `<key>` actions:

| Category | Key(s) | Action |
| :--- | :--- | :--- |
| **Focus** | `h` / `l` *(or `←` / `→`)* | Focus split to the left / right (spatial) |
| | `k` / `j` *(or `↑` / `↓`)* | Focus split above / below (when horizontal splits exist) |
| | `w` or **`<ctrl+w>`** | Cycle / toggle to the next / other split (fast double-tap!) |
| | `p` | Jump to previously focused split |
| **Move** | **`H`** / **`L`** | Move active tab to left / right split (create if outer `>=2` tabs; collapse split if last tab) |
| | `K` / `J` | Move active tab to top / bottom split (horizontal symmetry) |
| | `x` | Swap current split column (`WorkspaceTabs`) with its adjacent vertical split |
| **Split & Size** | `v` | Split vertically right (duplicate current leaf—like Vim `<C-w>v` & Obsidian Split right) |
| | `n` | New empty tab in vertical right split (like `v` + blank `+` tab for quick capture/lookup) |
| | `s` | Split horizontally down (duplicate current leaf—like Vim `<C-w>s`) |
| | `=` | Equalize split widths/heights (reset custom drag sizes to 50/50) |
| | `<` / `>` | Narrow / widen active split by step (supports counts, e.g., `2>`) |
| **Zoom & Close** | `z` | Toggle non-destructive zoom/maximize on active split (`pane-relief` CSS style) |
| | `q` / `c` | Close active tab (auto-collapses split if last tab; warns/protects if `leaf.pinned`) |
| **Cancel** | `Esc`, `Ctrl+[`, `Ctrl+G` | Cancel prefix mode without modifying workspace or leaking keys |

---

## 4. Technical Architecture (Inside `bob-navigation-hotkeys`)

### 4.1 Input Capture & Prefix State Machine (`Keymap` `Scope`)

1. **Entering `<ctrl+w>` Prefix Mode:**
   - Attach a **capture-phase `keydown` listener** on each workspace `Window` (`window` main + any popouts via `workspace.on("window-open", ...)`), mirroring `610-plugin-jumps-and-counted-keys.js:585-605`.
   - Match exact `Ctrl+W` (`event.ctrlKey && !event.metaKey && !event.altKey && !event.shiftKey && (event.code === "KeyW" || event.key === "w" || event.key === "W")`), ignoring `event.repeat`.
   - Run the **Mode Guard**:
     - If already in Window Prefix Mode → do not re-enter here; let the active `Scope` handle second `<ctrl+w>` as **toggle to other split**!
     - If a modal (`.modal-container`) is open, or focus is inside a regular text input (`INPUT`, `TEXTAREA`, `[contenteditable]` outside CM6, CM6 search panel `.cm-panels`), or an active Markdown editor is in Vim `insert` / `replace` mode (checked via existing `getCurrentVimMode(cm)` in `610-plugin-jumps-and-counted-keys.js:912-937`) → **return immediately without `preventDefault()`** so Vim `i_<C-w>` deletes word backward normally.
     - Otherwise: call `event.preventDefault(); event.stopPropagation();` (so CodeMirror's normal-mode `idle` `<C-w>` never runs), reset any pending Vim count (`resetPendingVimInputState`, capturing optional numeric count `N` e.g. `2<ctrl+w>l` or `2<ctrl+w>>`!), and activate Window Prefix Mode.
2. **While in Window Prefix Mode (`app.keymap.pushScope(windowChordScope)`):**
   - Push a fresh Obsidian `Scope` (`new Scope(this.app.scope)` or standalone `new Scope()`): register a catch-all `scope.register(null, null, (event, ctx) => ...)` handler (plus a `window` `blur` + `pointerdown` auto-cancel listener so the user can **never** get stuck in prefix mode).
   - Map `Escape` and `Ctrl+[` (`isClearSearchHighlightEscapeKeydown` pattern in `610-plugin-jumps-and-counted-keys.js:814-832`) to exit cleanly.
   - Allow optional digit keys (`1`–`9`, `0` after first digit) to accumulate a repeat count (`×N` for resize `<`/`>` or multi-column jumps) while keeping the HUD open.
   - Map `<ctrl+w>` (with `event.ctrlKey`) to execute `"toggle-other-split"` and exit.
   - Dispatch mapped lowercase/uppercase keys (`h`, `l`, `H`, `L`, etc. checking `event.key` and `event.shiftKey` carefully), always returning `false` from `Scope` to swallow the event, and exit prefix mode cleanly via `app.keymap.popScope(windowChordScope)`.
   - On any **unmapped key**, exit prefix mode cleanly and swallow the key (never replay an unexpected `d` or `x` into Vim Normal mode!).

### 4.2 Geometric Navigation Engine (Reliable Multi-Split Targeting)

- **Why not `workspace.getAdjacentLeafInDirection`?** Even `obsidian-typings` flags `Workspace.getAdjacentLeafInDirection` with `@remark Potentially does not work` (`Workspace.d.ts:485-492`). And flat leaf-iteration (`tab-shifter`) fails as soon as horizontal + vertical splits mix or tabs are closed/reopened.
- **Use visible `WorkspaceTabs` bounding-box geometry within the active container:**
  1. Resolve `container = activeLeaf?.getContainer() || workspace.rootSplit` (handling popout `WorkspaceWindow`s seamlessly; if focus is in a collapsed/sidebar leaf `isInSidebar(activeLeaf)`, allow jumping out of sidebar or resolve `getMostRecentLeaf(workspace.rootSplit)`).
  2. Collect all candidate `WorkspaceTabs` inside `container` whose `containerEl` has `rect.width > 0 && rect.height > 0` (`getBoundingClientRect()`).
  3. To navigate in direction `dir ∈ {left, right, up, down}` from `sourceRect`:
     - Filter candidates strictly on the target side (e.g., for `right`: `candRect.left >= sourceRect.right - 8` or `candCenterX > sourceCenterX` with minimal overlap ambiguity).
     - Rank candidates by: **(a) orthogonal overlap first** (for `left`/`right`, shared vertical band overlap with `sourceRect`; breaks ties when a tall left column faces a horizontally split right column by preferring the sub-pane aligned with the active cursor/center!), **(b) closest edge distance along primary axis**, **(c) smallest center offset on secondary axis**.
     - Focus the winning `WorkspaceTabs`'s currently selected leaf (`tabs.children[tabs.currentTab]` or active visible leaf) via `workspace.setActiveLeaf(targetLeaf, { focus: true })`, and explicitly ensure focus lands inside `.cm-content` if Edit mode or `view.containerEl` if Reading/Empty/Canvas so subsequent keyboard events immediately belong to that pane.
  4. Track `lastActiveLeafByContainer` so `<ctrl+w>p` and `<ctrl+w><ctrl+w>` always jump back to the exact previous split in 2+ pane setups.

### 4.3 In-Place `WorkspaceLeaf` Reparenting (No State Loss)

Because Obsidian's main area is a tree of `WorkspaceSplit(direction: "vertical" | "horizontal")` → `WorkspaceTabs` → `WorkspaceLeaf[]`, **in-place reparenting** avoids reloading files or losing cursor/scroll/history/empty/PDF/Canvas views:

- **Core primitives verified in `obsidian-api` / `obsidian-typings` (1.15.1):**
  - `workspace.createLeafBySplit(anchorLeaf, 'vertical', before)` (public since 0.9.7; `before = true` creates a split to the **left**, `before = false` to the **right**!).
  - `workspace.splitLeaf(anchorLeaf, leaf, 'vertical', before)` (`Workspace.d.ts:1597`, unofficial: splits using an existing `leaf`!).
  - `WorkspaceParent.insertChild(index, child)`, `removeChild(child)`, `recomputeChildrenDimensions()`, `WorkspaceTabs.selectTab(leaf)`, `WorkspaceItem.setDimension(null | n)`, `Workspace.onLayoutChange()`, `Workspace.requestSaveLayout()`.
- **Implementation sequence (and mandatory E2E verification):**
  1. **Target existing `WorkspaceTabs` (`targetTabs`):**
     - Compute safe insertion index respecting pinned tabs: if `!leaf.pinned`, insert at `Math.max(pinnedCount(targetTabs), targetTabs.children.length)` (end of group, after pins); if `leaf.pinned`, insert at `pinnedCount(targetTabs)` (end of pinned cluster).
     - Reparent `leaf` into `targetTabs` (`sourceTabs.removeChild(leaf)` → `targetTabs.insertChild(insertIdx, leaf)` → `targetTabs.selectTab(leaf)` → `recomputeChildrenDimensions` → `onLayoutChange()` → `setActiveLeaf(leaf, { focus: true })`).
     - **If `sourceTabs` now has `0` leaves:** verify whether `removeChild` auto-collapses `sourceTabs` cleanly (or detach emptied `sourceTabs` via `sourceTabs.detach()` + `workspace.onLayoutChange()` + `requestSaveLayout()`), and flatten any redundant single-child intermediate `WorkspaceSplit` (`allowSingleChild: false`).
  2. **Creating a new split on `<ctrl+w>H` / `<ctrl+w>L`:**
     - Choose an anchor leaf: if splitting the whole active group vertically, split around `sourceTabs`'s active sibling or `workspace.splitLeaf(anchorLeaf, leaf, 'vertical', before)`. If `sourceTabs` has `>= 2` tabs and becomes its own left/right split (`<ctrl+w>H` from a single pane), select a surviving tab in `sourceTabs` as `anchorLeaf`, move `leaf` out via `splitLeaf(anchorLeaf, leaf, 'vertical', isLeft)` (or create a sibling `WorkspaceTabs` inside a `WorkspaceSplit('vertical')` and move `leaf` into it!).
  3. **Safe Fallback + Verification Gate:**
     - Because `splitLeaf` / `removeChild` / `insertChild` / `DeferredView` (`leaf.isDeferred()` / `loadIfDeferred()` in `obsidian-typings` `WorkspaceLeaf.d.ts`) are Obsidian internals across versions `1.8.7–1.15.x`, keep a clean fallback helper (`createLeaf` + `setViewState(leaf.getViewState())` + `setPinned(wasPinned)` + `leaf.detach()`) ONLY if in-place reparenting throws, **and test every transition (single→split, split→merge/destroy, 3-column, pinned tabs, Empty tab, Reading view, Vim Normal editor preservation) inside `bob-plugins`' real Electron Obsidian E2E runner (`scripts/test-obsidian-*.cjs`)**!

---

## 5. Beautiful, Intuitive UX & Visual Design

### 5.1 Two-Tier `<ctrl+w>` Hint: Zero Flicker for Speed, Rich Clarity When Paused

Bad leader-key UIs either flash an intrusive centered dialog on every fast chord or hide tiny cryptic text in a corner. A **two-tier progressive reveal** solves both:

1. **Tier 1 (`0ms` — Instant Micro-Pill in Status Bar):**
   - Immediately upon pressing `<ctrl+w>`, light up a crisp compact pill right beside `[[ s w n b ]]`: e.g. `⌃W …` (styled identically to `.bob-bracket-mode-thumb` using `color-mix(in srgb, var(--interactive-accent) 20%, transparent)` and a `1px` `--interactive-accent` border).
   - If Bryan types `<ctrl+w>l` in `60ms` from muscle memory, Tier 1 clears immediately and **Tier 2 never even paints** — zero flicker!
2. **Tier 2 (`180ms` Delay — Floating Context-Aware Window HUD):**
   - After `180ms` (configurable `120–250ms`) with `<ctrl+w>` still waiting, smoothly appear as a **bottom-center floating dock** just above the status bar—**without dimming or blocking the vertical splits above it** so Bryan can keep reading `sase_blog` and `sase_blog_contents` while glancing down.
   - Styled with `bob-navigation-hotkeys`' native Obsidian tokens (`styles.css:2096-2258`):
     - Surface: `var(--background-primary)` at ~`94%` opacity with `backdrop-filter: blur(10px)`, `1px solid var(--background-modifier-border)`, `border-radius: var(--radius-l, 12px)`, `box-shadow: var(--shadow-l)`.
     - Keycaps: `.bob-key-card-key` badges (`var(--font-monospace)`, `var(--background-secondary)`, `1px solid var(--background-modifier-border)`, `border-radius: 6px`), accent highlight for primary contextual actions (`--interactive-accent`), warm coral border (`color-mix(in srgb, var(--color-red) 45%, transparent)`) on `q` close, muted `opacity: 0.42` for unavailable directions.
   - **Live Spatial Minimap & Dynamic Context Labels (what makes it *intuitive*):**
     - The header includes a tiny proportional **live layout schematic** (`[ █ | ░ ]` vs `[ ░ | █ ]` vs `[ █ ]`) showing at a glance which split is focused, plus `"Left split (3 tabs · sase_blog)"`.
     - Key descriptions dynamically reflect **exact consequences** before you press the key:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│  [ █ | ░ ]  Window (⌃W) · Left split · 3 tabs            [count: —]        │
├───────────────────────────┬──────────────────────────┬─────────────────────┤
│  FOCUS                    │  MOVE & SIZE             │  SPLIT & CLOSE      │
│  [h]  — at left edge      │  [H]  Split left (move)  │  [v]  Split right   │
│  [l]  Focus right →       │  [L]  Move tab → right   │  [n]  New blank →   │
│       sase_blog_contents  │  [x]  Swap splits        │  [s]  Split down    │
│  [j/k] — no row split     │  [=]  Equalize (50/50)   │  [z]  Zoom toggle   │
│  [⌃W] / [w] Other split   │  [<] / [>] Resize step   │  [q]  Close tab     │
├───────────────────────────┴──────────────────────────┴─────────────────────┤
│  Esc / ⌃[ cancel · click any action or press key                           │
└────────────────────────────────────────────────────────────────────────────┘
```

*(Example when focused in the **right** single-tab split of `20261115_171818.png`: `[ ░ | █ ]`, `h` reads `Focus left → sase_blog`, **`H` lights up with `Merge ← left (destroys this split)`**, `L` dims cleanly with `Sole tab on right edge`, `q` reads `Close tab (closes split)`!)*

### 5.2 Solving the Screenshot's Focus Blind Spot (Persistent Split Polish)

Alongside `<ctrl+w>`, add lightweight CSS (applied **only** when `> 1` split exists inside `.workspace-split.mod-root`) to fix the visual ambiguity seen in `20261115_171818.png`:
- **Focused split indicator:** A clean `2px` `--interactive-accent` top bar along `.workspace-tabs.mod-active .workspace-tab-header-container` (subtle, architectural, native to Default Light & Dark modes).
- **Quiet inactive chrome:** Softly lower opacity (`~0.72`–`0.82`) on unfocused `.workspace-tabs:not(.mod-active)` **tab headers & view header breadcrumbs only**—never dimming the note content itself so side-by-side comparison stays 100% high-contrast.
- **Arrival pulse:** A `240ms` crisp border/inset accent pulse (`prefers-reduced-motion` guarded!) on the destination `.workspace-tabs` whenever `<ctrl+w>` jumps focus or moves a tab across splits, guiding the eye immediately across wide monitors.

---

## 6. Recommended Solution & Implementation Roadmap

1. **Home:** Implement in **`bob-plugins/plugins/bob-navigation-hotkeys`** as dedicated cohesive fragments (following `AGENTS.md`: `src/fragments.json`, mixin registration in `690-install-plugin-mixins.js`, and `styles.css` under `.bob-win-*` / `.bob-key-card-*` tokens), with matching Palette commands (`bob-navigation-hotkeys:window-focus-left`, `window-move-tab-right`, etc.) documented in `docs/bob-navigation-hotkeys.md`.
2. **Recommended Phased Rollout:**
   - **Phase 1 — Split Topology, Geometry Navigation & In-Place Move Engine + Obsidian E2E Tests:**
     - Implement geometric `left`/`right`/`up`/`down` target resolution + last-split history (`w`, `p`, `<C-w><C-w>`).
     - Implement `<ctrl+w>H`/`L` 4-state split/move/collapse + pinned-tab index ordering + `v`/`n`/`s`/`=`/`<`/`>`/`x`/`z`/`q`.
     - Verify in-place reparenting vs. empty-split cleanup, `DeferredView` safety, cursor/scroll retention, Empty tabs, and Reading view via a new headless Electron E2E test (`scripts/test-obsidian-vertical-splits-e2e.cjs`).
   - **Phase 2 — `<ctrl+w>` Prefix Interceptor, `Scope` Machine, HUD & Active-Split CSS:**
     - Install per-window capture listener (`Window` + popouts) yielding cleanly to Vim Insert/Replace mode and editable DOM fields.
     - Add the `0ms` status pill + `180ms`-delayed context-aware Window HUD + multi-split active-pane indicator CSS.
   - **Phase 3 — Sync & Documentation:**
     - Document the macOS `Ctrl+W` vs. Linux `Mod+W` (`workspace:close`) note, run `npm run build`, `npm run validate`, `npm run docs:gen`, `npm run docs:check`, and deploy via `bob plugins sync`.
