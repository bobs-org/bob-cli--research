# Highlighting vim yank ranges in Obsidian (SASE-style flash)

Researcher: `mus` (independent swarm report, `__mus` suffix).
Question: how best to highlight the text that vim normal-mode motions copy in
Obsidian (e.g. `yy`), the way the sase project's prompt input widget does.

## TL;DR recommendation

Build it in-house as a small, exact-range flash owned by Bryan's own plugins —
do not install either community yank-highlight plugin as the long-term answer.
Wrap the yank at the point where the exact range is still known, paint it with
one short-lived CodeMirror 6 `Decoration.mark` per yanked range, clear it after
~250 ms (configurable, default-on with a disable toggle), and restyle it with
theme-native CSS variables. Port sase's semantics (exact range, reyank
restarts the timer, stale timers never clear a newer flash), not sase's
Textual code.

Concretely: add one focused unit to the bob-plugins monorepo — preferably a new
tiny plugin (e.g. `bob-yank-highlight`), or, if Bryan wants zero new plugin
entries, a single ≤1000-line fragment in `bob-navigation-hotkeys` reusing the
`bob-ledger-tools` mark-extension patterns by copy. Trigger by wrapping
`RegisterController.pushText` (kometenstaub's interception point) **plus**
capturing the exact yank range from the vim layer (which neither community
plugin does), instead of fuzzy text search (aleksey's approach).

## What sase actually does (the reference behavior)

Source (external checkout via `/sase_repo`, read-only):

- `src/sase/ace/tui/widgets/_yank_highlight.py` — `YankHighlightMixin`.
  - `_YANK_FLASH_SECONDS = 0.2` (200 ms).
  - `_flash_yank(start, end)` converts `(row, col)` to absolute offsets,
    stores `_yank_flash_span`, bumps `_yank_flash_generation`, stops the prior
    timer, rebuilds the overlay, and arms `set_timer(0.2, clear)`.
  - `_clear_yank_flash(generation)` ignores stale callbacks
    (`generation != self._yank_flash_generation` returns early), so a rapid
    reyank is never erased by the previous yank's timer.
  - `_build_highlight_map` appends one span,
    `self._append_highlight_span(*span, "yank.flash")`, guarded by
    `_MAX_OVERLAY_BYTES` / `_MAX_OVERLAY_LINES` from `_jinja_highlight.py`
    (large-buffer escape hatch).
  - `_register_yank_text_area_theme` derives the style from the active theme:
    `Style(color=foreground, bgcolor=success, bold=True)`.
- `src/sase/ace/tui/widgets/_vim_normal_operator_exec.py`
  - `_execute_charwise_operator`: on `op == "y"` it stores the vim register,
    calls `schedule_copy_delivery(...)` ("yanked text"), calls
    `self._flash_yank(start, end)`, parks the cursor at `start`, and returns
    without recording a mutation.
  - `_execute_linewise_operator`: on `op == "y"` it flashes
    `((first_row, 0), (last_row, len(last_line)))` — full lines, no trailing
    newline guessing.
  - Deletes/changes also copy to the clipboard path but never flash. Yank-only
    is a deliberate scope line.
- `src/sase/ace/tui/widgets/vim_text_area.py:421` — `_flash_yank` no-op
  default so mixins compose safely.
- `src/sase/ace/tui/widgets/prompt_text_area.py` — `PromptTextArea` mixes in
  `YankHighlightMixin` alongside search/jinja/todo/bullet highlight mixins.
- `tests/ace/tui/widgets/test_prompt_yank_highlight.py` — the contract worth
  copying: charwise `yw`/`yiw`/`yf)` flash the exact copied span; linewise
  `yy`/`2Y`/`Vjy` flash full lines; visual `vhy` flashes the selection;
  expiry clears only the overlay (text and register survive); rapid reyank
  replaces the flash and the stale timer is ignored; the yank overlay coexists
  with search and jinja highlights.

Takeaway: sase can do this cleanly because it owns the operator layer — the
flash call sites sit exactly where `start`/`end` are known. Obsidian cannot
hook that layer without monkey-patching, which is the whole design problem.

## Obsidian / CodeMirror platform facts

- Obsidian's editor is CodeMirror 6. Vim emulation comes from
  `replit/codemirror-vim` (`packages/codemirror-vim-core/vim.js` in that
  checkout, `packages/codemirror-vim/src/{index.ts,cm_adapter.ts}` for the
  CM6 adapter). Obsidian exposes it undocumented as
  `window.CodeMirrorAdapter.Vim`.
- Yank execution path in `vim.js`:
  - Operator table maps `y`/`Y` to the `yank` operator; `Y` is
    `operatorMotion yank / expandToLine linewise`.
  - `actions.yank(cm, args, ranges, oldAnchor)`: reads `cm.getSelection()`,
    calls `vimGlobalState.registerController.pushText(registerName, 'yank',
    text, args.linewise, vim.visualBlock)`, shows `"<N> lines yanked"`, and
    returns the cursor position. `ranges` here is the exact yank range — the
    single best interception point, but it lives inside the vim.js closure and
    is not a public API.
  - `RegisterController.pushText(registerName, operator, text, linewise,
    blockwise)`: black-hole register `_` returns early; linewise text gets a
    trailing `\n` appended if missing; no-register/unnamed yanks populate the
    `0` register and the unnamed register; `+` writes `navigator.clipboard`.
    Signature: `(registerName, operator, text, linewise, blockwise)`.
  - Observable signals: `CodeMirror.signal(cm, 'vim-keypress', key)` and
    `'vim-command-done'` (see `index.ts:248` and `vim.js:1367`), plus
    `'vim-mode-change'`. These carry keys/reasons, never ranges.
- Obsidian plugin APIs used by any implementation:
  - `this.registerEditorExtension([viewPlugin])` — applies to every markdown
    CM6 editor (Live Preview and Source mode share CM6 now; Reading view has no
    editor and is out of scope).
  - `require("@codemirror/view")` → `ViewPlugin`, `Decoration`;
    `require("@codemirror/state")` → `RangeSetBuilder`, `StateEffect`;
    `require("obsidian")` → `editorInfoField`, `editorViewField`,
    `editorLivePreviewField`. The bob-plugins convention (e.g.
    `plugins/bob-ledger-tools/src/010-load-and-constants.js`) loads each with
    defensive `try/catch` nulls so a missing export degrades to "feature off,
    never throw".
  - Editor handles: the CM5-compat adapter at
    `activeView.editMode.editor.cm.cm` (what both community plugins use) versus
    the raw CM6 `EditorView` at `leaf.view.editor.cm`. Cursor/offset mapping
    goes through `editor.posToOffset(editor.getCursor('from'/'to'))` on the
    adapter or `view.state.doc` offsets on the CM6 view.
  - `app.vault.getConfig('vimMode')` gates everything; when vim mode is off
    there are no yank operators to highlight.
  - Vault vimrc (`~/bob/obsidian_vimrc.md`): `set clipboard=unnamedplus` (every
    yank also hits the system clipboard), `:` remapped to bob command mode,
    bracket walks (`]s`, `]w`, `]]`, …) dispatched as `obcommand`s. A yank
    flash must not fire for command-mode or picker `y` keys (e.g. image-zoom
    modal's `y` copies a path through plain clipboard, not a vim operator).

## Prior art: the two community plugins

Both were read in full as external checkouts. Neither should be adopted
verbatim, but together they map the solution space.

### A. `aleksey-rowan/obsidian-vim-yank-highlight` — keypress snoop + fuzzy match

- `src/main.ts`: listens to `vim-keypress` / `vim-command-done` on
  `activeView.editMode.editor.cm.cm`, accumulates a `vimCommand` key buffer,
  and when `vimCommandDone` is set, checks `vimCommand.contains("y")`. Any
  command containing the letter `y` triggers `highlightYank()`.
- `highlightYank()` reads the yank register
  (`getRegisterController().getRegister("yank").keyBuffer[0]`), hands the raw
  text to a per-view `MarkViewPlugin`, and clears after a hardcoded 500 ms.
- `src/markViewPlugin.ts`: decorates via `RangeSetBuilder` + one
  `Decoration.mark({class: "ovy-highlight"})`. Because the true range is
  unknown, it slices the viewport text (`view.state.sliceDoc(viewport.from,
  viewport.to) + "\n"` — the appended newline is a hack for linewise yanks on
  the last line), computes `longestCommonSubstring(visibleText, yankText)`
  (`src/util.ts`, O(n·m) dynamic programming), and picks the occurrence
  nearest the cursor (`getSubstringPosition`).
- `src/types.ts` documents the event contract (`vim-keypress`,
  `vim-command-done`) and the `window.CodeMirrorAdapter` backdoor.
- `styles.css`: `yankedHighlight` keyframes with a candid comment block about
  the multi-line gap problem (line contents are inline elements; background
  doesn't cover the inter-line gap; the shipped fix is approximate vertical
  padding that "jumps a little" and "might not work for all fonts").
- TODOs in the source admit the gaps: no visual-block support ("requires
  multiple disjoint highlights"), highlight duration/color hardcoded, visual
  mode behavior unsuppressed.

Failure modes that matter for Bryan: (1) any mapping containing `y` (including
a typed `y` in an ex command or a `Z`-style custom key) can false-trigger;
(2) fuzzy matching highlights the wrong occurrence whenever the yanked text
(`the`, `- [ ]`, `TODO`) appears more than once — the common case in task
notes; (3) O(n·m) substring on every yank with no size guard; (4) only the
active view is wired (`active-leaf-change` + single `codeMirror` handle), so
yanks in a second pane or right after startup can miss; (5) per the author's
own README, this exists because upstream
`replit/codemirror-vim#121` ("highlight yanked text") is unlikely to land.

### B. `kometenstaub/obsidian-vim-yank-highlight` — `pushText` wrap + cursor range

- `src/main.ts` (representative): with `monkey-around`'s `around()`, wraps
  `window.CodeMirrorAdapter.Vim.getRegisterController()`'s `pushText`. When
  `args.at(1) === 'yank'`, it grabs the active `MarkdownView`'s CM6 view and
  calls `cm6Editor.plugin(viewPlugin).makeYankDeco()` **before** the original
  `pushText` runs, then delegates.
- `makeYankDeco()`: builds a single `Decoration.mark({class: "yank-deco"})`
  from `editor.posToOffset(editor.getCursor('from'))` to `...getCursor('to')`
  via `view.state.field(editorViewField)`, stores it in a per-view
  `ViewPlugin`, and clears with `setTimeout(..., this.plugin.settings.timeout)`
  (default 2000 ms, user-configurable in a settings tab).
- Strengths over A: interception is semantic (only real yank-operator register
  writes trigger it — deletes/changes pass `operator !== 'yank'` and are
  correctly ignored), and there is no O(n·m) search and no key-buffer
  heuristics.

Correctness gap to know before copying it: the cursor range is only the yank
range for **visual-mode** yanks (selection still active when the wrapper runs).
For normal-mode `yy`/`yw`/`y$`/`yi(`/`yip`/counts there is no selection — the
cursor is a point — so `from == to` and the decoration is empty or a caret.
That is presumably why the plugin's audience reports it "works" for selections
but is vague on `yy`. An exact-range implementation must not reuse the cursor
as the range for normal-mode yanks; it must recover the range another way (see
recommendation).

Also note: the wrapper reads `app.workspace.getActiveViewOfType(MarkdownView)`
at yank time. That is usually but not always the yanked editor (pane races,
same-note split panes). The robust target is the editor that owns the yank,
not "the active view at timeout time".

### Upstream and adjacent options

- `replit/codemirror-vim#121` (native yank highlight): no native support; treat
  as unavailable. Do not block on it.
- `esm7/obsidian-vimrc-support`: owns the vimrc layer (`set
  clipboard=unnamedplus`, `exmap`/`obcommand`, `defineAction` patterns in
  `utils/vimApi.ts`). No yank-highlight feature; its value here is as the
  compatibility surface (vimrc reload replaces the Vim adapter object — see
  `plugins/bob-navigation-hotkeys/src/620-plugin-dash-and-vim-jumps.js`
  comments about reinstalling hooks after reload).
- Neovim `vim.highlight.on_yank()` (`TextYankPost`): the UX gold standard —
  exact range, short timeout (~150–300 ms depending on config), theme highlight
  group, reyank restarts the timer. Sase's 200 ms `success`-background flash is
  the same idea in Textual. Recommend matching that timing family, not the
  community plugins' 500 ms / 2000 ms.
- `nilsgke/obsidian-better-vim` (also opened in this workspace): broader vim
  overhaul, out of scope as a dependency for one flash effect.

## Options compared

| Option | Trigger | Range | Verdict |
|---|---|---|---|
| Install aleksey-rowan as-is | keypress buffer + `contains("y")` | fuzzy LCS near cursor | No. Wrong-occurrence and false-trigger risks are highest exactly in Bryan's dense task notes. |
| Install kometenstaub as-is | `pushText` wrap, `operator === 'yank'` | cursor `from`/`to` | Closest existing behavior, and settings UI exists. But normal-mode `yy`/`yw` ranges are wrong/empty; active-view-only; 2 s default feels sticky. Adopt the interception point, not the range logic. |
| In-house exact-range flash (recommended) | `pushText` wrap + range recovery at yank time | exact CM6 offsets, incl. linewise + blockwise | Yes. ~150–250 lines following existing bob mark patterns. Only option that makes `yy` right. |
| Upstream fix in codemirror-vim / Obsidian native | n/a | exact | No as a plan (unavailable); yes as a watch item. |
| Toast-only ("3 lines yanked") | reuse vim.js `showConfirm` text via Notice | no range | Weak substitute. vim.js already computes the line count; surfacing it as a Notice is cheap but answers "how much" while the ask is "where". Could ship as a complement, not the solution. |

## Critique: is this a good idea, and what would I change?

Yes, with a narrowed scope. The case for: yanks are invisible by design (no
doc change, cursor often stays put), and with `clipboard=unnamedplus` every
`yy` silently leaves Obsidian for the system clipboard — a flash is the only
confirmation of *what* left. Neovim, VSCodeVim, and now sase all treat this as
standard, expected feedback. Cost is a small, well-isolated decoration plus one
monkey-patch that Bryan already pays variants of elsewhere (Vim adapter
wiring, `handleEx("nohlsearch")`, vimrc-reload reinstalls).

Adjustments I would make to the request as stated (explicit requirement
changes):

1. **Yank only — not delete, change, or paste.** Sase deliberately flashes
   only `y`; both community plugins agree. Do not highlight `d`/`c`/`p` even
   though they also route through `pushText`/`showConfirm`.
2. **Exact ranges, never text search.** Drop the LCS approach entirely. The
   duplicate-text failure is disqualifying in a vault full of `- [ ]` rows.
3. **Default ~250 ms, configurable, default-on with an off switch.** Do not
   copy 500 ms or 2000 ms verbatim. Sase's 200 ms is right for a terminal
   prompt; Obsidian's denser, variable-height lines (headers, embeds, wrapped
   task rows) deserve slightly longer, but anything past ~500 ms reads as a
   stuck selection. Ship a duration setting plus a command-palette toggle,
   mirroring the `bob-ledger-tools` mark-gate/toggle pattern
   (`setupTaskTagMarks` → `toggleTaskTagMarks`, `registerMarkGatePopoutSync`).
4. **Per-leaf ViewPlugins, not one active-view handle.** Register one editor
   extension globally; each `EditorView` owns its flash state. The trigger
   resolves the *yanked* view (the one whose adapter called `pushText`), with
   active-view as fallback, never as the only path.
5. **Gate on vim mode and markdown editors.** No flash when
   `vault.getConfig('vimMode')` is false, in Reading view, canvas, or non-
   markdown panes. No flash for the black-hole register (`"_yy`) or for
   non-operator clipboard writes (image-zoom `y`, command-mode copies).
6. **Linewise means full lines; blockwise means disjoint ranges.**
   `yy`/`Y`/`2yy` highlight whole lines (sase parity:
   `(first_row, 0)`–`(last_row, len)`), not the register text's trailing-`\n`
   artifact. Visual-block (`Ctrl-V`) yanks highlight each block row, the case
   aleksey explicitly punts on.
7. **Reyank restarts; stale timers never clear.** Copy sase's generation
   counter, not the community plugins' bare `setTimeout`/`clearTimeout`. Rapid
   `yy` `yw` must move the flash, never blink it out early.
8. **Theme-native styling, no hardcoded background.** Sase can use Textual's
   `success` token; Obsidian must use CSS variables (e.g. a translucent
   `color-mix(in srgb, var(--interactive-accent) …, transparent)` or the
   existing search-highlight token) so light/dark and community themes survive.
   Expect the aleksey inter-line-gap quirk on multi-line flashes; accept
   approximate padding and avoid `!important` reaches into theme CSS.
9. **Size and failure discipline.** Never throw from the decoration path
   (bob mark convention: `try/catch`, return `Decoration.none`). Skip or clamp
   absurdly large yanks (mirror sase's byte/line guards). Reinstall cleanly on
   vimrc reload (the adapter object identity changes) and fully unwrap on
   unload.
10. **No new dependency.** `monkey-around` is already the community standard
    for this exact wrap and is tiny, but in-house code can do the same
    save/restore in ~10 lines; either is fine, but do not pull a plugin to get
    a library.

What I would *not* do: a separate "yank highlight" community-plugin install
(dueling settings, unowned CSS class names in Bryan's vault, active-view-only
bugs Bryan will feel daily); a keypress-sniffing design (fragile against
Bryan's own `:`→command-mode remap and `Z`/`]s`-style mappings); highlighting
deletes (noise — every `dd`/`cc` would flash); or a Reading-view/post-
processor component (no vim operators exist there).

## Recommended solution (build plan for the implementer)

Place it in the bob-plugins monorepo (source of truth; deploys via
`bob plugins sync`). Prefer a **new micro-plugin** over bolting onto an
existing one — it mirrors sase's single-purpose `YankHighlightMixin`, keeps the
toggle/instructions discoverable, and avoids weighting `bob-navigation-hotkeys`
(whose manifest description is already enormous) or `bob-ledger-tools` with
vim-lifecycle code. If Bryan is averse to a new plugin id, second choice is one
fragment in `bob-navigation-hotkeys/src/` (it already owns Vim-adapter
lifecycle: `620-plugin-dash-and-vim-jumps.js`, `handleEx("nohlsearch")`, vimrc-
reload reinstall), abiding by the repo's `src/fragments.json` + ≤1000-lines-
per-fragment + `npm run build:check` rules in that repo's `AGENTS.md`.

Implementation sketch (all patterns already exist in-repo):

1. **State:** one `StateEffect` (`setYankFlash`) + `StateField` holding
   `{ranges: {from,to}[], generation}` per `EditorView`, plus a `ViewPlugin`
   rendering `Decoration.mark({class: "bob-yank-flash"})` per range. Follow
   `264-plugin-task-tag-marks.js` (`createTaskTagMarkExtension`,
   `Prec.highest(ViewPlugin.fromClass(...))`, `buildXDecorations`,
   `taskTagMarkShouldRebuild`) and the defensive loader in
   `010-load-and-constants.js`.
2. **Trigger:** on load (and on vimrc reload / layout ready), resolve
   `window.CodeMirrorAdapter.Vim.getRegisterController()` and wrap
   `pushText(registerName, operator, text, linewise, blockwise)`. Proceed only
   when `operator === "yank"` and `registerName !== "_"` and vim mode is on.
   Resolve the target CM6 view from the *yanking* editor (adapter → view), not
   solely `getActiveViewOfType`.
3. **Range recovery (the part neither plugin gets right):** at wrap time the
   CM6 selection is trustworthy only for visual yanks. For normal-mode yanks,
   derive the range without searching text:
   - visual (charwise/linewise/blockwise): current selection ranges
     (blockwise → one decoration per row slice);
   - `yy`/`Y`/count-linewise: cursor row ± count−1, full lines
     (`(row,0)`–`(row+n−1, len))`, clamping to `doc.lineCount`;
   - charwise motions (`w`/`e`/`$`/`f`/`i`/`a`/paragraph): prefer wrapping one
     level up — the vim `yank` operator's `ranges` argument — over inferring
     from `text.length` (backward motions like `yb` and exclusive/inclusive
     edges make length-anchoring wrong). If operator-wrapping proves too
     brittle against the bundled vim.js version, fall back to: anchor at the
     post-yank cursor with direction recovered from the pre-yank cursor saved
     on `vim-keypress`, and verify `doc.sliceString(from,to) === text`
     (sans linewise trailing newline) before painting; on mismatch, paint
     nothing rather than something wrong.
   - registers (`"ayy`), counts (`2yy`, `y3w`), and `clipboard=unnamedplus`
     change destination, never geometry — no special-casing.
4. **Timing:** dispatch `setYankFlash`, `setTimeout(clear, duration)` with a
   generation counter per view (sase parity). Default 250 ms; setting range
   ~100–1000 ms; clearing must survive doc edits (flash is time-based, not
   edit-based — do not clear on `docChanged` the way search highlights do).
5. **Style:** `.bob-yank-flash` in the plugin's `styles.css`, namespaced like
   `bob-cnp-*`, built on theme vars, short fade keyframes (aleksey's
   `yankedHighlight` shape at 250 ms, without its line-gap padding unless
   multi-line testing shows the gap). Check light/dark, default + one community
   theme, headers/embeds/wrapped rows.
6. **Lifecycle:** unwrap the `pushText` patch on unload; re-resolve the
   adapter on vimrc reload; no-ops (never throws) when the adapter, fields, or
   vim mode are absent.

Verification: unit tests in the repo's `scripts/test-*.cjs` harness for range
math (linewise clamp, backward-motion anchor, blockwise split, generation
guard, size guard, `_`-register and non-yank-operator silence); then a manual
matrix the author must actually run in the vault — `yy`, `Y`, `2yy`, `yw`,
`y$`, `yb`, `yi(`/`ya"`, `yip`, `Vj y`, `Ctrl-V` block, `"ayy`, `"_yy`,
folded lines, Live Preview vs Source mode, two panes, light/dark, vimMode off
— confirming `yy` highlights exactly the yanked line(s) and nothing else, with
no console errors on reload/unload.

## Open questions for Bryan

- New micro-plugin vs. fragment in `bob-navigation-hotkeys` — preference?
- Default duration (proposing 250 ms) and should deletes ever flash, or stay
  yank-only forever?
- Should the flash also surface the existing `"<N> lines yanked"` confirm as a
  subtle Notice, or is the highlight alone the right feedback?

## Sources inspected

- `gh:sase-org/sase`: `src/sase/ace/tui/widgets/_yank_highlight.py`,
  `src/sase/ace/tui/widgets/_vim_normal_operator_exec.py`,
  `src/sase/ace/tui/widgets/vim_text_area.py`,
  `src/sase/ace/tui/widgets/prompt_text_area.py`,
  `tests/ace/tui/widgets/test_prompt_yank_highlight.py`.
- `gh:aleksey-rowan/obsidian-vim-yank-highlight`: `src/main.ts`,
  `src/markViewPlugin.ts`, `src/util.ts`, `src/types.ts`, `styles.css`,
  `README.md`.
- `gh:kometenstaub/obsidian-vim-yank-highlight`: `src/main.ts` (+ settings
  tab), `styles.css` where present.
- `gh:replit/codemirror-vim`: `packages/codemirror-vim-core/vim.js`
  (`defineOperator`, `actions.yank`, `RegisterController.pushText`,
  `getRegisterController`, `vim-keypress`/`vim-command-done` signals),
  `packages/codemirror-vim/src/{index.ts,cm_adapter.ts}`.
- `gh:esm7/obsidian-vimrc-support`: vimrc contract (`set
  clipboard=unnamedplus`, `exmap`/`obcommand`), `utils/vimApi.ts`.
- Linked `bob-plugins`: `AGENTS.md`, `plugins/bob-ledger-tools/src/
  {010-load-and-constants.js,264-plugin-task-tag-marks.js,
  300-plugin-vim-and-snippets.js}`, `plugins/bob-navigation-hotkeys/src/
  {100-yank-and-paths.js,620-plugin-dash-and-vim-jumps.js}`,
  `plugins/bob-navigation-hotkeys/styles.css`.
- Vault: `~/bob/obsidian_vimrc.md` (clipboard, `:`→command-mode, bracket-walk
  mappings).
