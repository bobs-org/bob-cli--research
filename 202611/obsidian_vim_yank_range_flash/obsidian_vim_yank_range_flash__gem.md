# Research: Vim Normal-Mode Yank Highlighting in Obsidian

**Author:** Researcher gem (`research.46.gem`)  
**Date:** 2026-11-11  
**Target Repositories:** `bob-plugins`, `gh:sase-org/sase`, `gh:replit/codemirror-vim`  
**Output Artifact:** `research:202611/obsidian_vim_yank_highlight__gem.md`

---

## 1. Executive Summary

This research investigates implementing transient visual highlighting for Vim normal-mode yank motions (e.g., `yy`, `yw`, `yip`, `y$`) in Obsidian, modeled after the UX in the SASE project's prompt input widget (`PromptTextArea` in `sase-org/sase`).

### Key Findings
1. **The Plan is Strongly Recommended:** "Blind yanking" is one of the most persistent usability pain points in modal editing. In normal mode, yanks produce zero visual confirmation, leaving users uncertain about whether trailing whitespaces, newlines, or outer blocks were captured until pasting. Neovim's `vim.highlight.on_yank` solved this in the terminal; replicating it in Obsidian brings identical ergonomic relief.
2. **Prior Art Has Critical Flaws:** Existing community plugins illustrate what *not* to do:
   - `aleksey-rowan/obsidian-vim-yank-highlight` waits until `vim-command-done` when the cursor has already collapsed, attempting to recover the yanked span via fuzzy string searching (`longestCommonSubstring`). This is brittle, slow, and causes phantom highlights across duplicate words and lines.
   - `kometenstaub/obsidian-vim-yank-highlight` hooks the correct Vim state (`pushText`), but uses an unmaintainable 2000 ms duration, mutates decorations without dispatching proper CodeMirror 6 (CM6) transactions/effects (leading to paint glitches), and unnecessarily flashes in visual mode.
3. **Recommended Implementation Architecture:** Implement as a focused module within Bryan's existing `bob-plugins` monorepo (either as a standalone plugin `bob-vim-yank-highlight` or integrated into `bob-vim-surround`). The mechanism should:
   - Hook `window.CodeMirrorAdapter.Vim.getRegisterController().pushText` using `monkey-around` or safe function wrapping.
   - Synchronously inspect the editor's active selection during `pushText` *before* the Vim command dispatcher collapses the selection to the cursor anchor.
   - Gate activation to `operator === "yank"` and `!cm.state.vim.visualMode` (normal-mode motions only).
   - Dispatch a CM6 `StateEffect` to a dedicated `StateField<DecorationSet>` with a **200 ms** flash duration and a smooth CSS fade-out transition using Obsidian theme accent CSS variables.

---

## 2. Analysis of the Reference Implementation (`sase` Prompt Input Widget)

The SASE TUI prompt widget (`PromptTextArea` in `src/sase/ace/tui/widgets/`) provides a clean, well-tested reference model for modal yank feedback.

### 2.1 The Architecture in SASE
In SASE's Textual implementation, yank highlighting is factored into `YankHighlightMixin` (`src/sase/ace/tui/widgets/_yank_highlight.py`) and wired directly into normal-mode operator execution (`_vim_normal_operator_exec.py`).

1. **Explicit Operator Trigger:**
   In `VimNormalOperatorExecutionMixin`, when operator `op == "y"` executes:
   - For **charwise motions** (`y{motion}`):
     ```python
     self._store_vim_register(text, "charwise")
     if text:
         schedule_copy_delivery(...)
         self._flash_yank(start, end)
     self.cursor_location = start
     ```
   - For **linewise motions** (`yy`, `Y`, `y{linewise motion}`):
     ```python
     if text:
         self._flash_yank((first_row, 0), (last_row, len(lines[-1])))
     ```
2. **Visual Mode Omission:**
   In `_vim_visual_ops.py`, `_store_visual_register` does **not** call `_flash_yank`. Because the user has already visually selected the range in visual mode (`v`, `V`), flashing again upon pressing `y` produces an annoying visual double-take. SASE deliberately reserves the flash for normal-mode blind motions.
3. **Flash Mechanics & Lifespan:**
   - **Duration:** Fixed at `_YANK_FLASH_SECONDS = 0.2` (200 milliseconds).
   - **Generation Counter:** `self._yank_flash_generation += 1` increments on each flash. The scheduled timer closure captures this generation; if a subsequent yank occurs before the timer fires, the old timer callback safely no-ops.
   - **Overlay Theme:** It dynamically injects a syntax style `"yank.flash"` into `TextAreaTheme` using `app_theme.foreground`, `bgcolor=app_theme.success`, and `bold=True`.

---

## 3. Obsidian & CodeMirror 6 Architecture Breakdown

Obsidian (v0.13+ through current v1.8+) is built on **CodeMirror 6 (CM6)**. However, Obsidian's Vim mode runs on `@replit/codemirror-vim`, an adapter layer that emulates CodeMirror 5's modal API on top of CM6. Understanding the interaction between these layers is critical.

### 3.1 The CodeMirror Adapter Layer
- **`window.CodeMirrorAdapter.Vim`**: The global Vim API entry point. Exposes `getRegisterController()`, `defineOperator()`, `defineMotion()`, `mapCommand()`, and `handleKey()`.
- **`cm` (The Adapter Instance)**: Each editor pane has a `CodeMirrorAdapter` instance (`view.editMode.editor.cm.cm`). It holds `cm.cm6` (the underlying CM6 `EditorView`) and `cm.state.vim` (the current modal state, e.g., `visualMode`, `insertMode`).

### 3.2 The Vim Operator Execution Lifecycle
When a user presses a normal-mode motion command like `yy` or `yw`:
1. `commandDispatcher.evalInput(cm, vim)` matches the command key sequence.
2. It calculates the target motion range `[curStart, curEnd]`. If linewise, it expands to line boundaries via `expandSelectionToLine(cm, curStart, curEnd)`.
3. **Crucial Step:** It sets the CM6 selection to the motion target:
   ```javascript
   cm.setSelections(cmSel.ranges, cmSel.primary);
   ```
4. It invokes the operator function:
   ```javascript
   var operatorMoveTo = operators[operator](cm, operatorArgs, cmSel.ranges, oldAnchor, newHead);
   ```
5. Inside `operators.yank`:
   ```javascript
   yank: function(cm, args, ranges, oldAnchor) {
     var vim = cm.state.vim;
     var text = cm.getSelection();
     var endPos = vim.visualMode
       ? cursorMin(vim.sel.anchor, vim.sel.head, ranges[0].head, ranges[0].anchor)
       : oldAnchor;
     vimGlobalState.registerController.pushText(
         args.registerName, 'yank', text, args.linewise, vim.visualBlock);
     ...
     return endPos;
   }
   ```
6. **Selection Collapse:** Immediately after `operators[operator]` returns `operatorMoveTo`, the dispatcher calls:
   ```javascript
   if (operatorMoveTo) {
     cm.setCursor(operatorMoveTo);
   }
   ```
   This collapses the selection back to a single cursor position.

**Key Insight:** During the synchronous execution of `pushText`, `cm.setSelections` is still active on `cm.cm6`! The exact start and end offsets are present in `cm.cm6.state.selection.ranges`. Once `operators.yank` returns, that selection is destroyed.

---

## 4. Evaluation of Existing Prior Art

Two community plugins exist in this space. Examining them explains why standard community installations feel brittle or unmaintained.

### 4.1 `aleksey-rowan/obsidian-vim-yank-highlight`
- **Approach:** Hooks `cm.on("vim-keypress")` and `cm.on("vim-command-done")`. When `"y"` or `"Y"` is encountered, it reads `registerController.getRegister("yank").keyBuffer[0]`.
- **Severe Flaws:**
  1. *Lost Coordinates:* By the time `vim-command-done` fires, the editor selection has already collapsed to the cursor anchor. The plugin has no range information.
  2. *Fuzzy String Matching:* To recreate the range, it executes `longestCommonSubstring(visibleText, yankText)` and `indexOf` starting near `cursorHead`. This fails catastrophically when:
     - The yanked text is a common word (e.g., `the`, `return`, `id`) that occurs earlier on the line.
     - Linewise yanks contain newlines or indentation matching nearby blank lines.
     - Document has folded regions.
  3. *Key Snooping False Positives:* Searching for `"y"` in `vimCommand` triggers on search input (`/yearly`) or replace keys.
  4. *Performance:* String diffing in JavaScript on large visible viewports on every keypress causes typing latency.

### 4.2 `kometenstaub/obsidian-vim-yank-highlight`
- **Approach:** Monkey-patches `window.CodeMirrorAdapter.Vim.getRegisterController().pushText`. When `args[1] === "yank"`, it retrieves the active view and calls `makeYankDeco()`.
- **Flaws & Deficiencies:**
  1. *Broken CM6 Reactive Loop:* Directly assigns `this.decorations = Decoration.set(deco)` on a CM6 `ViewPlugin` without dispatching a `StateEffect` or transaction. CM6 does not reliably re-render until an unrelated DOM or scroll event occurs.
  2. *Excessive Duration:* Hardcoded to `2000 ms` (2 full seconds). This distracts the user, feels like a selection freeze, and interferes with reading.
  3. *No Mode Filtering:* Flashes on visual-mode yanks, producing an annoying double-flash after the user already highlighted the text.
  4. *Single Bounding Box:* Uses `editor.getCursor('from')` and `'to'`, collapsing multi-cursor or visual-block yanks into a single contiguous rectangle.

---

## 5. Critique & Adjusted Requirements

### 5.1 Is this a good idea?
**Yes, unequivocally.** Yank highlighting is considered indispensable by modern modal editors.
- In Vim/Neovim, `y` does not change document text. Without visual feedback, the user cannot verify if `yap` took the trailing newline, if `yi"` excluded the quotes, or if `3yw` included the space.
- It brings behavioral parity with the SASE terminal prompt widget and Neovim (`vim.highlight.on_yank`).

### 5.2 Required Adjustments to Requirements

To achieve production-grade quality in Obsidian, the original idea needs the following refinements:

| Original Plan / Baseline Idea | Recommended Adjustment | Justification |
| :--- | :--- | :--- |
| Flash all yanks | **Suppress on Visual Mode (`!vim.visualMode`)** | In `v` / `V` / `<C-v>`, the user already sees the selection highlighted. Re-flashing is redundant visual noise. |
| Fixed long timeout (e.g., 500ms–2000ms) | **Fast transient flash: 180 ms – 200 ms** | Matches SASE (`0.2s`) and Neovim (`150ms`). Must be an unobtrusive confirmation, not a persistent highlight. |
| Hardcoded CSS background color | **Theme CSS variable (`var(--color-accent-subtle)`) with fade-out** | Supports light/dark themes and Obsidian custom themes cleanly. CSS transition provides a smooth visual exit. |
| String-matching / regex on text | **Zero text-searching: capture CM6 ranges at `pushText`** | Guarantees 100% mathematical precision for multi-cursor, identical words, folded headers, and indentation. |
| Standalone third-party community plugin | **Incorporate into `bob-plugins`** | Bryan already maintains `bob-plugins` (with `bob-vim-surround` and Node test suites). Third-party plugins in this niche are abandoned or buggy. |

---

## 6. Technical Implementation Approaches

Three potential architectural approaches exist within the Obsidian/CodeMirror environment:

```
+------------------------------------------------------------------------------------+
|                                    VIM KEYMAP                                      |
|                                    (e.g., "yy")                                    |
+------------------------------------------------------------------------------------+
                                          |
                                          v
+------------------------------------------------------------------------------------+
|                           CodeMirrorAdapter Dispatcher                             |
|                           cm.setSelections(range)                                  |
|                           operators["yank"](cm, args, ranges)                      |
+------------------------------------------------------------------------------------+
                                          |
                   +----------------------+----------------------+
                   |                                             |
                   v                                             v
       [APPROACH A: RECOMMENDED]                     [APPROACH B: REJECTED]
       Hook pushText on registerController           Override Vim.defineOperator("yank")
       (Captures live CM6 ranges before collapse)    (Requires rewriting private Vim internals)
                   |
                   v
+------------------------------------------------------------------------------------+
|                         CodeMirror 6 Decoration Pipeline                           |
|       Dispatch StateEffect.add -> StateField updates Decoration.mark               |
|       setTimeout(200ms) -> Dispatch StateEffect.remove                             |
+------------------------------------------------------------------------------------+
```

### Approach Comparison

| Metric | Approach A: Hook `pushText` + CM6 `StateField` | Approach B: Custom `defineOperator` | Approach C: Keypress + `vim-command-done` |
| :--- | :--- | :--- | :--- |
| **Range Accuracy** | **100% Exact** (reads active CM6 selection) | **100% Exact** | **Low / Flawed** (heuristic substring matching) |
| **Code Mirror 6 Safety** | **High** (standard `StateEffect` transaction) | **High** | **Medium** |
| **Maintenance Burden** | **Low** (wraps 1 stable method) | **High** (re-implements register routing & messages) | **High** (edge cases with syntax & folds) |
| **Visual Mode Isolation**| **Trivial** (`!cm.state.vim.visualMode`) | **Trivial** | **Difficult** |
| **Multi-selection Support**| **Native** (maps over all selection ranges) | **Native** | **Unsupported** |

---

## 7. Recommended Solution & Concrete Design

### 7.1 Location in the Ecosystem
Incorporate this directly into `bob-plugins` as a dedicated plugin: `plugins/bob-vim-yank-highlight/` (or as a submodule inside `bob-vim-surround`).
A dedicated plugin `bob-vim-yank-highlight` is preferred to maintain clean separation of concerns and allow independent toggling and testing.

### 7.2 Implementation Code Structure

#### 1. CodeMirror 6 StateField & Effects (`yankField.ts`)
```typescript
import { StateEffect, StateField } from "@codemirror/state";
import { Decoration, DecorationSet, EditorView } from "@codemirror/view";

export interface YankRange {
  from: number;
  to: number;
}

export const addYankHighlight = StateEffect.define<YankRange[]>();
export const clearYankHighlight = StateEffect.define<void>();

const yankMark = Decoration.mark({ class: "bob-vim-yank-flash" });

export const yankHighlightField = StateField.define<DecorationSet>({
  create() {
    return Decoration.none;
  },
  update(decorations, tr) {
    // Map existing decorations across document changes
    decorations = decorations.map(tr.changes);

    for (const effect of tr.effects) {
      if (effect.is(addYankHighlight)) {
        const marks = effect.value
          .filter((r) => r.to > r.from)
          .map((r) => yankMark.range(r.from, r.to));
        decorations = Decoration.set(marks, true);
      } else if (effect.is(clearYankHighlight)) {
        decorations = Decoration.none;
      }
    }
    return decorations;
  },
  provide: (field) => EditorView.decorations.from(field),
});
```

#### 2. The Hook & Trigger Logic (`main.ts`)
```typescript
import { MarkdownView, Plugin } from "obsidian";
import { around } from "monkey-around";
import { yankHighlightField, addYankHighlight, clearYankHighlight, YankRange } from "./yankField";

const YANK_FLASH_DURATION_MS = 200;

export default class BobVimYankHighlightPlugin extends Plugin {
  private unhookPushText: (() => void) | null = null;
  private flashTimer: number | null = null;
  private flashGeneration = 0;

  async onload() {
    this.registerEditorExtension([yankHighlightField]);
    this.setupVimHook();
  }

  private setupVimHook() {
    const codeMirrorAdapter = (window as any).CodeMirrorAdapter;
    const vim = codeMirrorAdapter?.Vim;
    if (!vim) {
      // Retry when Vim adapter initializes
      this.registerEvent(
        this.app.workspace.on("active-leaf-change", () => {
          if (!this.unhookPushText) this.setupVimHook();
        })
      );
      return;
    }

    const registerController = vim.getRegisterController();
    if (!registerController || this.unhookPushText) return;

    const self = this;
    this.unhookPushText = around(registerController, {
      pushText(oldMethod: Function) {
        return function (registerName: string, operator: string, text: string, linewise?: boolean, blockwise?: boolean) {
          if (operator === "yank") {
            self.handleYankCapture();
          }
          return oldMethod.apply(this, arguments);
        };
      },
    });
  }

  private handleYankCapture() {
    const activeView = this.app.workspace.getActiveViewOfType(MarkdownView);
    if (!activeView) return;

    const editorCm = (activeView as any).editMode?.editor?.cm;
    const adapter = editorCm?.cm;
    const cm6View = editorCm; // EditorView

    if (!adapter || !cm6View) return;

    // Requirement: Normal-mode motions only (e.g. yy, yw, yip)
    // Suppress if in visual mode
    if (adapter.state?.vim?.visualMode) {
      return;
    }

    // While inside pushText, cm.setSelections has the exact yanked ranges
    const cm6Ranges: YankRange[] = cm6View.state.selection.ranges.map((r: any) => ({
      from: r.from,
      to: r.to,
    }));

    if (cm6Ranges.length === 0 || cm6Ranges.every((r) => r.from === r.to)) {
      return;
    }

    // Dispatch highlight effect into CM6
    cm6View.dispatch({
      effects: [addYankHighlight.of(cm6Ranges)],
    });

    // Schedule transient clear with generation protection
    this.flashGeneration += 1;
    const generation = this.flashGeneration;

    if (this.flashTimer) {
      window.clearTimeout(this.flashTimer);
    }

    this.flashTimer = window.setTimeout(() => {
      if (this.flashGeneration === generation && !cm6View.isDestroyed) {
        cm6View.dispatch({
          effects: [clearYankHighlight.of()],
        });
      }
    }, YANK_FLASH_DURATION_MS);
  }

  onunload() {
    if (this.unhookPushText) {
      this.unhookPushText();
      this.unhookPushText = null;
    }
    if (this.flashTimer) {
      window.clearTimeout(this.flashTimer);
    }
  }
}
```

#### 3. Styling & Smooth Fade-Out (`styles.css`)
```css
.bob-vim-yank-flash {
  background-color: var(--color-accent-subtle, rgba(var(--color-accent-rgb), 0.28)) !important;
  border-radius: 2px;
  transition: background-color 200ms ease-out;
}
```

---

## 8. Verification & Test Plan

Following the testing patterns in `bob-plugins/scripts/test-vim-surround.cjs`:
1. **Unit Test Harness:**
   - Create `scripts/test-vim-yank-highlight.cjs` running under `node --test`.
   - Mock `CodeMirrorAdapter.Vim.getRegisterController()`.
   - Test that `pushText(..., 'yank', ...)` fires `addYankHighlight` with exact ranges.
   - Test that `pushText(..., 'delete', ...)` and `pushText(..., 'change', ...)` do **not** trigger yank highlights.
   - Test that `visualMode === true` does **not** trigger yank highlights.
   - Test that linewise yanks (`yy`) cover the entire line from column 0 to line length + 1.
2. **Interactive Vault Verification:**
   - Deploy via `bob plugins sync`.
   - Verify `yy` on single lines, `3yy`, `yw`, `yip` (inner paragraph), and `y$` (tail of line).
   - Verify smooth 200 ms flash without screen flicker or residual artifacts.

---

## 9. Conclusion

Implementing normal-mode yank highlighting in Obsidian is a high-value ergonomic upgrade that aligns Obsidian with the SASE prompt widget and Neovim standards. By capturing CM6 ranges directly during the `registerController.pushText` lifecycle and routing them to a CM6 `StateField`, the implementation avoids all the pitfalls of third-party community plugins and provides a robust, zero-heuristic, 200 ms flash.
