# Flashing Vim yanks in Obsidian (Bob): research, critique, recommendation

_Researcher: cld · 2026-11-11 · Scope: bob-plugins, Obsidian 1.15.0 Vim mode, sase prompt-input parity_

## TL;DR

- **The idea is worth doing.** For yanks of one or two lines, Obsidian gives no feedback at
  all. The feature is small (about 150–200 lines of JS plus a little CSS) and the risk can
  be contained.
- **Don't install the community "Vim Yank Highlight" plugin.** It guesses which text was
  yanked by searching the viewport for it. That guess can land in the wrong place, and its
  matcher can freeze Obsidian on large yanks (details below).
- **Recommended hook:** wrap CodeMirror Vim's register controller `pushText` for
  `operator === "yank"`. At that moment the editor's live CM6 selection is exactly the
  yanked range. Draw the flash from that selection, but only after checking that the
  selected text equals the text that was pushed. If it doesn't, draw nothing. Obsidian's
  own yank code still runs. It is a patched version (more below), and overriding `yank`
  through `defineOperator` would replace it, so I keep that override only as a fallback.
- **Rendering:** draw the flash with the plugin's own CM6 `StateField` decoration for about
  200 ms (the same as sase). Linewise yanks use full-width **line** decorations; charwise
  and blockwise yanks use **mark** decorations. Background colour only (no bold), with a
  short fade.
- **Requirement changes (all called out in §6):** include visual-mode yanks, flash yanks
  only (not deletes), skip `"_`, highlight whole lines for linewise yanks (including blank
  lines), and drop sase's bold and its large-buffer cutoff.
- **Where it lives:** a new hand-edited plugin `bob-vim-yank-flash` in bob-plugins, enabled
  once in the vault.

---

## 1. What we are matching: the sase prompt-input flash

Source: `sase-org/sase`, commit `7bc4ff38f5` "feat(tui): flash yanked prompt text"
(2026-07-14), plus the later hook refactor `24cff91cd3`.

| Aspect | sase behaviour | Where |
| --- | --- | --- |
| Trigger | Only the `y` operator: charwise (`yw`, `yiw`, `yf)`, `Y`) and linewise (`yy`, `2Y`, `Vjy`) | `_vim_normal_operator_exec.py` `_execute_charwise_operator` / `_execute_linewise_operator` call `_flash_yank` |
| Visual yanks | Flash (`vhy` flashes the selection) | `test_visual_charwise_yank_flashes_selection` |
| Deletes / changes | Never flash | `test_delete_and_change_do_not_flash` |
| Region | Exact copied range; linewise = col 0 of the first row to the end of the last row's text (not the newline) | `_flash_yank((first_row, 0), (last_row, len(lines[-1])))` |
| Empty line `yy` | No flash (the range has zero width) | `test_empty_line_yank_does_not_flash` |
| Duration | `_YANK_FLASH_SECONDS = 0.2` | `_yank_highlight.py:24` |
| Re-yank | A new yank replaces the flash; a generation counter makes stale timers no-ops | `_clear_yank_flash(generation)` |
| Style | Theme foreground on the theme's `success` background, **bold** | `_register_yank_text_area_theme` |
| Large buffers | Skipped above `_MAX_OVERLAY_BYTES` / `_MAX_OVERLAY_LINES` because the whole highlight map is rebuilt | `_build_highlight_map` |
| Clipboard | Delivered asynchronously; the flash does not wait for it | `schedule_copy_delivery(...)` then `_flash_yank` |

Parity means: flash what was copied, briefly, only for yanks, and let a new yank replace
the old flash safely. The bold style and the large-buffer cutoff come from how Textual
works, not from the requirement (see §6).

## 2. What Obsidian gives us today

### 2.1 Obsidian's Vim engine (checked on the binary, not assumed)

I searched `obsidian.asar` from Obsidian **1.15.0** (snap on athena, `latest/stable`):

- It bundles `@replit/codemirror-vim` source **with an Obsidian-local patch to the yank
  operator**. Yanks only report "N lines yanked" when more than 2 lines were yanked; the
  shipped comment says *"Like Vim's default 'report' option, only report yanks of more than
  2 lines (upstream always reports)"*. The ex `:yank` command has the same patch. Upstream
  added the always-on report on 2026-02-21 (`d19062a`, "fix :'a,.y ex command (#257)").
- The bundle has **no yank-highlight feature**. Searches for `vim-yank`, `highlightYank`,
  `yankHighlight`, `flashYank` and `onYank` all returned 0.
- The operator dispatch matches upstream byte for byte. `cm.setSelections(cmSel.ranges, …)`
  runs first, then `operators[operator](cm, operatorArgs, cmSel.ranges, oldAnchor, newHead)`,
  then `cm.setCursor(operatorMoveTo)`.
- `defineOperator: defineOperator` and `getRegisterController: function` are both exported
  from `window.CodeMirrorAdapter.Vim`.
- The internal Obsidian `Editor` has undocumented `addHighlights` / `removeHighlights`
  (present in the bundle). I note it below as an alternative way to draw, not the
  recommended one.

Caveat: I checked athena's 1.15.0 snap. I did not verify Bryan's daily-driver Mac build.
The e2e smoke test in §8 guards against version drift.

### 2.2 How a yank actually executes

Upstream `packages/codemirror-vim-core/vim.js`, the same in Obsidian's bundle:

1. A keydown reaches Vim's `handleKey`. The command runs inside `cm.operation(...)`, all
   synchronously in one task.
2. `evalInput` computes the range. Linewise motions expand to `(first,0)…(last+1,0)`
   (`expandSelectionToLine`, vim.js:4009). Visual-line and visual-block build the same
   kind of ranges, with one range per row for blocks.
3. `cm.setSelections(cmSel.ranges)` (vim.js ≈2187). In the CM6 adapter this
   **dispatches the selection immediately** (`cm_adapter.ts:280`). Positions past the end
   of the document are clipped to `doc.length` (`indexFromPos`, `cm_adapter.ts:12`).
4. `operators.yank` (vim.js:2902): `text = cm.getSelection()`, which the adapter builds
   as `getSelections().join("\n")` (`cm_adapter.ts:348`). Then
   `registerController.pushText(registerName, 'yank', text, linewise, visualBlock)`, then
   the (patched) report, then it returns `endPos`.
5. After the operator returns: `exitVisualMode` if needed, then `cm.setCursor(endPos)`.
   The browser paints only after this, so the temporary "yank selection" is never visible.

So **while `pushText(…, 'yank', …)` runs, the editor's live selection is exactly the
yanked region**, including one range per row for blockwise yanks. That is the key fact
this design relies on. The `pushText(registerName, operator, text, linewise, blockwise)`
signature has not changed since 2014 (`be0ac97`). Selection-before-operator dates from
the 2012 rewrite. The ex `:yank` (vim.js:6415) calls `pushText` **without** setting a
selection.

### 2.3 Bryan's vault and plugins

- `.obsidian/app.json`: `"vimMode": true`.
- `obsidian-vimrc-support` 0.10.2 loads `obsidian_vimrc.md`, which has
  `set clipboard=unnamedplus`. vimrc-support copies the register to the system clipboard
  in `captureYankBuffer` on DOM `keyup`/`click`/`focusin`. It reads
  `getRegister('yank')`. `'yank'` is not a valid register name, so that call returns the
  **unnamed** register, which is why deletes reach the clipboard too. So the clipboard
  write is asynchronous and separate from Vim's yank. A flash therefore confirms the
  *register write*, not a successful clipboard write; sase behaves the same way.
- **bob-vim-surround** already extends Obsidian's Vim through
  `window.CodeMirrorAdapter.Vim` (`defineOperator`, `mapCommand`, `handleKey`). It
  registers after `onLayoutReady`, retrying on `active-leaf-change`. For `ys` it lets `y`
  through as a pending operator, catches the `s` keydown in the capture phase, and injects
  `<Esc><A-b>s` (`handlePhysicalSurroundTriggerKeydown`, main.js:1041). **The built-in yank
  never runs for `ys`**, so a yank hook won't flash on surround. Still worth an e2e
  assertion.
- No bob plugin or installed third-party plugin overrides `yank` or calls `pushText`.
  vimrc-support uses `register.setText`, and only bob-vim-surround and vimrc-support call
  `defineOperator`, for their own operator names.
- bob plugins already use CM6 through `require("@codemirror/state")` /
  `require("@codemirror/view")` and `registerEditorExtension`; see
  `bob-ledger-tools/src/010-load-and-constants.js`.
- `bob plugins sync` copies `manifest.json`, `main.js` and `styles.css` but **does not
  enable** a plugin. A new plugin needs a one-time enable.

## 3. Prior art

| Project | Hook | Locating the region | Verdict |
| --- | --- | --- | --- |
| **Vim Yank Highlight** (aleksey-rowan, v1.0.8, last commit 2023-12-22, community plugin, about 7k downloads) | `vim-keypress` + `vim-command-done` snooping; fires if the key list *contains* `"y"`/`"Y"` | `longestCommonSubstring(viewportText, registerText)` | **Reject.** False triggers on `fy`, `ty`, `ry`, `"yp` and `ys`. It picks the wrong spot when the text repeats, clips yanks larger than the viewport, and has no blockwise support. The LCS builds an `(n+1)×(m+1)` JS array, so a `yG` of 50k chars against a 10k-char viewport means about 5×10⁸ cells, i.e. a freeze or out-of-memory. |
| **obsidian-vim-yank-highlight** (kometenstaub, v1.1.4, 2022) | `monkey-around` wrap of `getRegisterController().pushText`, filtered on `args[1] === 'yank'` | Reads `editor.getCursor('from'/'to')` at `pushText` time | **The right hook, a buggy implementation.** It mutates `ViewPlugin.decorations` without dispatching, so the flash appears and disappears only on the next unrelated update. It handles only the main selection, has a 2000 ms default, and does no verification. |
| **Better Vim** (community) | Says its yank highlight is "inspired by" aleksey-rowan | Same family as above | Not adopted; it brings unrelated features. |
| Neovim `vim.hl.on_yank` | `TextYankPost` autocmd | Exact `'[`/`']` marks + regtype | Defaults: `IncSearch`, **150 ms**, `on_visual = true`; not fired for the black-hole register. |
| VSCodeVim `vim.highlightedyank.*` | Internal | Exact | Off by default; **200 ms**, `rgba(250, 240, 170, 0.5)`. |

The kometenstaub plugin shows the `pushText` hook has worked in Obsidian since 2022. The
aleksey-rowan README says outright that it avoided that hook only because the hook is a
monkey-patch. It paid for that with a heuristic that is wrong in common cases.

## 4. Options for detecting the yank

| # | Approach | Precision | Keeps Obsidian's patched yank | Restorable on unload | API surface relied on | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| A | Install community plugin | Poor (heuristic) | Yes | Yes | `vim-keypress`, register | See §3: misfires and can freeze on large yanks. |
| B | Home-grown key snooping + register diff | Poor | Yes | Yes | Same | Same problem: register text does not tell you *where* the yank was. |
| **C** | `Vim.defineOperator('yank', wrapper)`, re-implementing the 8-line body | Exact (`cm`, `ranges`, `args` passed in) | **No.** It replaces Obsidian's patched body, and the report patch would have to be re-created with `cm.openNotification` | **No.** The `operators` table is closure-private and has no getter, so unload can only reinstall *our copy* | `defineOperator` (public, already used by surround), `getRegisterController().pushText` | Freezes yank semantics at whatever we copy; any future Obsidian fix to yank is silently lost; last writer wins against any other plugin doing the same. |
| **D** | Wrap `getRegisterController().pushText`, read the live CM6 selection, **verify** before flashing | Exact (selection == yanked ranges, see §2.2) | **Yes** | **Yes** (restore the saved method) | `getRegisterController()` (marked "testing hook" upstream, but present since about 2013 and already relied on by vimrc-support in this vault), `pushText` signature (stable since 2014), selection-before-operator ordering (stable since 2012) | Needs the target `EditorView` (the focused editor). The check that the selection's text equals the pushed text makes a wrong view, an ex `:y`, or any internal change a quiet no-op instead of a wrong flash. |
| E | `mapCommand('y'/'Y', 'operator', 'bobYank')` + own operator | Exact | No | Partly | Same as C, plus more keymap surface | C with more moving parts (normal `Y` is an `operatorMotion`, visual `Y` needs its own entry). No advantage. |
| F | CM6 `updateListener` that spots the brief selection→cursor flip | Fragile | Yes | Yes | Adapter dispatch pattern | It can't tell a yank from any other operator (`d`, `>`, `gu`). Reject. |

**Choice: D, with C as the documented fallback.** The deciding fact is that Obsidian
patches the yank operator itself (§2.1). That fork is exactly what C would overwrite
without anyone noticing. D adds behaviour *after* Obsidian's code runs, removes itself
cleanly, and its text check turns every way it could break into "no flash" rather than "a
wrong flash".

## 5. Rendering the flash

| Approach | Verdict |
| --- | --- |
| **Own `StateField<DecorationSet>` + `StateEffect`** registered with `registerEditorExtension` | **Recommended.** It is the standard CM6 pattern and already common in bob plugins. Decorations follow edits through `tr.changes`. Clearing is safe across re-yanks by tagging each effect with an id, the CM6 version of sase's generation counter. It supports both `Decoration.line` and `Decoration.mark`. |
| `ViewPlugin` holding mutable decorations (kometenstaub) | No. Changes don't show until some unrelated update happens. |
| Obsidian internal `editor.addHighlights` / `removeHighlights` | Works today, but it is undocumented, marks only, and can't support the safe clear-by-id. |
| Briefly setting a real selection | No. It changes the cursor and Vim state, and fights visual mode. |

**Shape of the highlight** (see the adjustments in §6):

- **Linewise** (`yy`, `3yy`, `Y`, `yj`, `yap`, `Vjy`): one `Decoration.line({class})` per
  covered line. The whole line box gets a background: no gaps between lines, blank lines
  included, and the result reads as "these lines" just as `V` does. Computing the lines:
  `first = lineAt(from)`, `last = lineAt(to)`, minus one line if `to` sits at the start of
  `last` and `to > from`. An empty linewise range at the end of the document still gets
  `lineAt(from)`.
- **Charwise** (`yiw`, `yf)`, `y$`, `y}`): one `Decoration.mark` per range.
- **Blockwise** (`<C-v>…y`): one mark per selection range (one per row), which comes for
  free from the live selection.

**Style**: in `styles.css`, background only, using Obsidian's palette. sase uses the
theme's `success` colour, and Obsidian's matching variable is `--color-green-rgb` (present
in 1.15.0: `8,185,78` light, `68,207,110` dark):

```css
.bob-yank-flash,
.cm-line.bob-yank-flash-line {
  background-color: var(--bob-yank-flash-bg, rgba(var(--color-green-rgb), 0.35));
  animation: bob-yank-flash-fade 200ms ease-in forwards;
}
@keyframes bob-yank-flash-fade {
  0%, 60% { background-color: var(--bob-yank-flash-bg, rgba(var(--color-green-rgb), 0.35)); }
  100% { background-color: transparent; }
}
@media (prefers-reduced-motion: reduce) {
  .bob-yank-flash, .cm-line.bob-yank-flash-line { animation: none; }
}
```

The `--bob-yank-flash-bg` hook lets a CSS snippet change the colour without a settings
tab.

## 6. Critique of the plan, and requirement changes

### Is this a good idea?

Yes:

- **It fills a real gap.** For yanks of ≤2 lines, Obsidian's Vim says nothing; the cursor
  just jumps to the start of the range. The useful cases are text objects and searches
  (`yi(`, `yap`, `y/foo<CR>`, `yit`), where the extent isn't obvious and a wrong guess
  only shows up at paste time, often in another app.
- **It keeps habits consistent** across Neovim, the sase prompt bar and Obsidian.
- **It is cheap and isolated.** Expect one file of about 150–200 lines, a CSS file and
  tests. The plugin toggle is the kill switch.

Concerns, and how the recommendation handles them:

- **It patches Vim internals.** That is unavoidable, since Obsidian has no yank event.
  Contain it: feature-detect, wrap rather than replace, verify before drawing, restore on
  unload, and add a real-Obsidian e2e test that fails loudly when an upgrade breaks the
  hook (§8).
- **Don't treat the flash as a clipboard confirmation.** Clipboard delivery belongs to
  vimrc-support and runs asynchronously on `keyup`. If clipboard failures become a real
  problem, that's a separate fix in vimrc-support's area, not this feature.
- **Don't over-build.** No settings tab and no per-mode options. sase manages with
  constants, and so can this.

### Requirement changes (called out)

| # | Change | Why |
| --- | --- | --- |
| **R1** | **Also flash visual-mode yanks** (`v…y`, `V…y`, `<C-v>…y`, visual `Y`), not only "normal-mode motions". | sase does (`test_visual_charwise_yank_flashes_selection`), Neovim's `on_visual` defaults to true, and the hook covers it for free. In Obsidian the selection disappears on `y`, so the flash is the only confirmation of what was taken. |
| **R2** | **Yank only**: no flash for `d`, `c`, `x`, `s`, `D`, `C` even though `clipboard=unnamedplus` copies them. | Matches sase and Neovim. The text is gone, so there is nothing to flash. |
| **R3** | **Skip the black-hole register** (`"_y`). Do flash named registers (`"ay`, `"+y`). | Nothing is copied for `"_`, and Neovim's `TextYankPost` doesn't fire for it either. |
| **R4** | **Linewise yanks highlight whole lines** (full-width line background), **including blank lines**. This differs from sase, which highlights only the text and skips empty lines. | Obsidian uses proportional fonts and hides markup in Live Preview, so text-only highlights look ragged and leave the gaps between lines unpainted. A line background matches what was copied (whole lines plus newline), matches how `V` looks, and fixes sase's silent `yy` on a blank line. |
| **R5** | **Background only, no bold** (sase uses bold). | In a terminal grid bold costs nothing. In Obsidian it changes glyph widths and can re-wrap lines for 200 ms, which looks like jitter. |
| **R6** | **Drop sase's large-buffer cutoff; cap the number of line decorations instead** (for example, ≤ 500 lines per flash). | sase's cutoff exists because Textual rebuilds the whole highlight map. CM6 draws only the viewport, so a big `yG` needs at most a cheap bound on how many decorations get built. |
| **R7** | **Out of scope:** ex `:yank`, Cmd/Ctrl+C, bob's `yank-*-path` commands, Reading view, non-Vim editors. | These aren't Vim motions over buffer text. The text check skips `:y` automatically; it could be added later by wrapping `defineEx('yank')` if wanted. |
| **R8** | **One duration constant, 200 ms** (sase parity; Neovim 150, VSCodeVim 200). Hold, then fade over the last ~40%. | Parity first; tune by feel later. No setting. |

## 7. Implementation sketch

A new plugin, `plugins/bob-vim-yank-flash/`, with a hand-edited `main.js` (well under the
1,000-line fragment limit, so no `fragments.json`), `styles.css` and `manifest.json`
(`isDesktopOnly: false`, `minAppVersion` matching bob-vim-surround's `1.8.7`).

```js
const { Plugin } = require("obsidian");
const { StateEffect, StateField } = require("@codemirror/state");
const { Decoration, EditorView } = require("@codemirror/view");

const FLASH_MS = 200;
const MAX_FLASH_LINES = 500;
const lineFlash = Decoration.line({ class: "bob-yank-flash-line" });
const markFlash = Decoration.mark({ class: "bob-yank-flash" });

// {id, deco} sets a flash; {id, clear: true} clears it only if it is still the newest one.
const yankFlashEffect = StateEffect.define();
const yankFlashField = StateField.define({
  create: () => ({ id: 0, deco: Decoration.none }),
  update(value, tr) {
    let { id, deco } = value;
    deco = deco.map(tr.changes);
    for (const e of tr.effects) {
      if (!e.is(yankFlashEffect)) continue;
      if (e.value.clear) {
        if (e.value.id === id) deco = Decoration.none;
      } else {
        ({ id, deco } = e.value);
      }
    }
    return { id, deco };
  },
  provide: (f) => EditorView.decorations.from(f, (v) => v.deco),
});

// Pure helpers, unit-testable without Obsidian.
function selectionText(state) {
  return state.selection.ranges.map((r) => state.sliceDoc(r.from, r.to)).join("\n");
}

function buildYankFlash(state, linewise) {
  const doc = state.doc;
  const out = [];
  for (const r of state.selection.ranges) {
    if (linewise) {
      const first = doc.lineAt(r.from).number;
      let last = doc.lineAt(r.to).number;
      if (last > first && doc.line(last).from === r.to) last -= 1;
      const capped = Math.min(last, first + MAX_FLASH_LINES - 1);
      for (let n = first; n <= capped; n += 1) out.push(lineFlash.range(doc.line(n).from));
    } else if (!r.empty) {
      out.push(markFlash.range(r.from, r.to));
    }
  }
  return out.length ? Decoration.set(out, true) : null;
}

class BobVimYankFlashPlugin extends Plugin {
  onload() {
    this.flashSeq = 0;
    this.hookActive = false;
    this.registerEditorExtension(yankFlashField);
    this.app.workspace.onLayoutReady(() => {
      if (this.installYankHook()) return;
      const ref = this.app.workspace.on("active-leaf-change", () => {
        if (this.installYankHook()) this.app.workspace.offref(ref);
      });
      this.registerEvent(ref);
    });
  }

  installYankHook() {
    if (this.hookActive) return true;
    const vim = window.CodeMirrorAdapter && window.CodeMirrorAdapter.Vim;
    const rc = vim && typeof vim.getRegisterController === "function"
      ? vim.getRegisterController() : null;
    if (!rc || typeof rc.pushText !== "function") return false;

    const hadOwn = Object.prototype.hasOwnProperty.call(rc, "pushText");
    const original = rc.pushText;
    const plugin = this;
    const wrapped = function (registerName, operator, text, linewise) {
      const result = original.apply(this, arguments);   // Obsidian's yank semantics first
      if (plugin.hookActive && operator === "yank" && registerName !== "_") {
        try { plugin.flashFocusedYank(String(text == null ? "" : text), !!linewise); }
        catch (_e) { /* a cosmetic feature must never break a yank */ }
      }
      return result;
    };
    rc.pushText = wrapped;
    this.hookActive = true;
    this.register(() => {
      this.hookActive = false;              // inert even if someone wrapped us afterwards
      if (rc.pushText === wrapped) {
        if (hadOwn) rc.pushText = original; else delete rc.pushText;
      }
    });
    return true;
  }

  flashFocusedYank(text, linewise) {
    const doc = window.activeDocument || document;
    const el = doc.activeElement;
    const editorEl = el && typeof el.closest === "function" ? el.closest(".cm-editor") : null;
    const view = editorEl ? EditorView.findFromDOM(editorEl) : null;
    // Verify: the live selection must be exactly what Vim just pushed (§2.2).
    // Wrong view, ex :yank, or a future internal change → no flash.
    if (!view || selectionText(view.state) !== text) return;
    const deco = buildYankFlash(view.state, linewise);
    if (!deco) return;
    const id = ++this.flashSeq;
    view.dispatch({ effects: yankFlashEffect.of({ id, deco }) });
    const win = view.dom.ownerDocument.defaultView || window;   // popout-safe timer
    win.setTimeout(() => {
      if (view.dom.isConnected) view.dispatch({ effects: yankFlashEffect.of({ id, clear: true }) });
    }, FLASH_MS);
  }
}

module.exports = BobVimYankFlashPlugin;
module.exports.__test = { selectionText, buildYankFlash };
```

Notes on the sketch:

- **The dispatch happens inside the operator.** That's safe: it runs inside a keydown
  handler, not a CM6 update, and an effects-only transaction changes neither the document
  nor the selection, so the Vim adapter's update listener ignores it. The `try/catch`
  covers the unlikely case of `handleKey` being called from inside an update.
- **Text check details.** The wrapper sees `text` *before* `pushText` appends the
  linewise `"\n"`. The adapter's `getSelection()` is `getSelections().join("\n")`, so
  `selectionText()` matches it exactly, including blockwise.
- **Unload.** `registerEditorExtension` removes the field. The cleanup returns `pushText`
  to its previous state, or leaves the wrapper in place but inert if another patcher
  wrapped it after us.
- **Fallback (C)**, if a future Obsidian makes the text check fail permanently (the e2e
  test will show it): `Vim.defineOperator('yank', fn)` re-implementing the operator body
  from vim.js:2902, including Obsidian's ">2 lines" report through `cm.openNotification`.
  Flash `ranges` directly. Document that unloading can't restore Obsidian's original.

## 8. Verification plan

**Unit tests** (`node --test`, stubbing `obsidian`/`@codemirror/*` the way
`scripts/test-vim-surround.cjs` stubs `obsidian`, or with small `Text`/selection doubles):

- `buildYankFlash`: `yy` mid-document, `yy` on a blank line, `yy` on the last line with
  and without a trailing newline, `3yy` crossing a blank line, a capped `yG`, a charwise
  multi-line range, blockwise with several ranges, and an empty charwise range (no flash).
- `selectionText` against `getSelection` semantics, including the `"\n"` join for blocks.
- Effect id logic: a stale clear doesn't clear a newer flash; a flash follows edits.
- Hook install and uninstall: wrapper installed once, original restored, inert when
  someone wrapped after us, `"_` and `operator !== 'yank'` ignored, exceptions swallowed.

**Real Obsidian e2e** (the existing CDP harness pattern in
`scripts/obsidian-*-e2e*.cjs`, using a scratch vault and never the live vault). Drive keys
through `Vim.handleKey(cm, …)` and assert on `.bob-yank-flash` / `.bob-yank-flash-line` in
the DOM right away and after more than 200 ms:

- Must flash: `yy`, `yiw`, `y$`, `yap`, `Vjy`, `vey`, `<C-v>jly` (two marks), and `yy`
  on a blank line.
- Must **not** flash: `dd`, `cw<Esc>`, `"_yy`, `:y<CR>`, and `ysiw)` (the surround still
  works).
- Obsidian's own behaviour still holds: `3yy` still shows "3 lines yanked"; the
  register/clipboard text is unchanged; the cursor ends where it did without the plugin.
- Disabling the plugin restores the original `pushText` (identity check), and the next
  yank leaves no flash.
- Run it as part of the Obsidian upgrade smoke check, so a broken hook shows up as a
  failed check rather than a quietly missing flash.

## 9. Recommended solution

1. **Build `bob-vim-yank-flash`** as a new, small, hand-edited plugin in `bob-plugins`.
   Keep it out of `bob-vim-surround`: surround's docs scope it to surround editing, and a
   separate plugin gives an independent on/off toggle and keeps failures contained. Folding
   it into surround is acceptable if Bryan would rather have fewer plugins, but the
   failures would no longer be separate.
2. **Detect yanks by wrapping `Vim.getRegisterController().pushText`** for
   `operator === "yank"` (skipping `"_`), after the original method runs. Take the ranges
   from the focused `EditorView`'s live selection, and **flash only if that selection's
   text equals the pushed text**. Install after layout-ready, with an `active-leaf-change`
   retry as bob-vim-surround does; restore on unload. Keep the `defineOperator('yank')`
   override as the documented fallback only.
3. **Render with the plugin's own CM6 `StateField`**: line decorations for linewise yanks,
   mark decorations for charwise and blockwise yanks. Follow edits through `tr.changes`;
   clear with an id-tagged effect after **200 ms** on the view's own window timer. Cap
   line decorations at about 500.
4. **Style**: background only, `rgba(var(--color-green-rgb), 0.35)` (the counterpart of
   sase's success colour), a 200 ms hold-then-fade, `prefers-reduced-motion` respected,
   and `--bob-yank-flash-bg` overridable. No settings tab.
5. **Scope** as amended in §6: normal and visual yanks; never deletes or changes; no
   `"_`; named registers included; ex `:y` and non-Vim copies excluded.
6. **Ship it** with unit tests and a real-Obsidian e2e case. Then `npm run build:check`,
   `npm test`, a `docs/bob-vim-yank-flash.md` page plus `npm run docs:gen` /
   `docs:check`, and `bob plugins sync`. Finally, **enable the plugin once in the vault's
   `community-plugins.json`**, because sync does not enable plugins.

## Sources

Local checkouts (opened through `sase repo open`):

- `sase-org/sase`: `src/sase/ace/tui/widgets/_yank_highlight.py`,
  `_vim_normal_operator_exec.py`, `vim_text_area.py`,
  `tests/ace/tui/widgets/test_prompt_yank_highlight.py`; commits `7bc4ff38f5`,
  `24cff91cd3`.
- `replit/codemirror-vim` (6.4.0, HEAD `c3131c4`):
  `packages/codemirror-vim-core/vim.js` (yank operator :2902, `pushText` ≈:1474,
  operator dispatch ≈:2187–2199, ex `yank` :6415, `vimApi` :806–830, `showConfirm`
  :5302), `packages/codemirror-vim/src/cm_adapter.ts` (`indexFromPos` :12,
  `setSelections` :280, `getSelection` :348), `CHANGELOG.md`.
- `bob-plugins`: `plugins/bob-vim-surround/main.js`, `docs/bob-vim-surround.md`,
  `docs/develop/architecture.md`, `plugins/bob-ledger-tools/src/010-load-and-constants.js`,
  `scripts/test-vim-surround.cjs`, `scripts/obsidian-*-e2e*.cjs`.
- `bobs-org/bob` vault: `.obsidian/app.json`, `.obsidian/community-plugins.json`,
  `obsidian_vimrc.md`, `.obsidian/plugins/obsidian-vimrc-support/{main.js,data.json}`.
- `aleksey-rowan/obsidian-vim-yank-highlight` (`src/main.ts`, `src/markViewPlugin.ts`,
  `src/util.ts`, `styles.css`) and `kometenstaub/obsidian-vim-yank-highlight`
  (`src/main.ts`).
- bob-cli: `src/native/plugins/cli.rs` (sync copies the managed files; it does not enable
  plugins).
- Obsidian 1.15.0 snap on athena: byte-level greps of
  `/snap/obsidian/current/app/resources/obsidian.asar`, read-only.

Web:

- [Vim Yank Highlight — Obsidian community listing](https://community.obsidian.md/plugins/vim-yank-highlight)
- [Vim Yank Highlight — obsidianstats](https://obsidianstats.com/plugins/vim-yank-highlight)
- [Better Vim — Obsidian community listing](https://community.obsidian.md/plugins/better-vim)
- [Neovim `runtime/lua/vim/hl.lua` (0.11.6, Debian sources)](https://sources.debian.org/src/neovim/0.11.6-1/runtime/lua/vim/hl.lua)
- [jdhao — highlight yank region in Neovim](https://jdhao.github.io/2020/05/22/highlight_yank_region_nvim)
- [VSCodeVim README (mirror; highlightedyank defaults)](https://github.com/VSCodeVim/Vim/)
