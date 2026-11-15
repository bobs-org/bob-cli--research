# Vertical split windows via `<C-w>` — research (`mus`)

## TL;DR

Yes, do this. The proposal is a good idea and the cheapest correct
implementation is almost entirely configuration, not code: Obsidian's
bundled Vim already treats `<C-w>` as a window-leader, Obsidian core
already ships `editor:focus-left` / `editor:focus-right`, and the
community-standard wiring is `exmap … obcommand …` plus one vimrc line
per key. Bob only needs to write **new plugin code for the move-window
commands** (`H`/`L` — Obsidian has no native "move tab to adjacent
group" command) and **the `<C-w>` hint**. Recommended scope for v1:
`h l H L w q v` (+ `j k` for free through core focus commands),
normal-mode only, main-area splits only, floating hint card plus a
destination-group flash on every jump/move.

## 1. What the screenshot shows

`~/tmp/screenshots/20261115_171818.png` shows the Bob vault with two
side-by-side **vertical tab groups** in the main area:

- Left group: tabs `20261115`, `dash`, `sase_blog` (active tab renders
  the `sase_blog` tasks view: READY pills, Next & In Progress, Blocked).
- Right group: single tab `sase_blog_contents` (a long `##`-headed doc,
  lines 13–42 visible).

This is exactly the working state the feature targets: source material
on one side, the thing being written/checked on the other, with the
keyboard never leaving Vim normal mode. No horizontal splits, no popout
windows, no sidebars involved.

## 2. How Obsidian splits actually work (API facts)

From the pinned `obsidian-api` checkout
(`sase/repos/external/gh/obsidianmd/obsidian-api/obsidian.d.ts`):

- Layout is a tree: `WorkspaceRoot` → `WorkspaceSplit` (lays children
  out along a `vertical` | `horizontal` direction) → `WorkspaceTabs`
  (one visible child = one tab) → `WorkspaceLeaf` (one open view).
  `SplitDirection` is `'vertical' | 'horizontal'`
  (`obsidian.d.ts:9480`). The root split defaults to vertical, i.e.
  side-by-side columns.
- `workspace.getLeaf('split', 'vertical')` creates a new leaf adjacent
  to the active leaf (`obsidian.d.ts:10821`). This is the sanctioned
  "create a split" primitive (`splitActiveLeaf` is deprecated in favor
  of it).
- `workspace.createLeafInParent(parent: WorkspaceSplit, index: number)`
  (`obsidian.d.ts:10769`) creates a leaf inside a *specific existing*
  group — the primitive a move command needs.
- `workspace.setActiveLeaf(leaf, { focus: true })` + `workspace.revealLeaf(leaf)`
  is the focus primitive. Bob already wraps both with deferred-leaf
  handling in `activateWorkspaceLeaf`
  (`plugins/bob-navigation-hotkeys/src/620-plugin-dash-and-vim-jumps.js`).
- `leaf.detach()` removes a leaf; empty tab groups collapse on their
  own (the tab-shifter plugin, below, relies on exactly this).
- `leaf.getViewState()` / `leaf.setViewState(state)` clones scroll,
  cursor, and mode. Bob's `duplicateCurrentTab` already implements the
  clone-with-fallback pattern: try `setViewState`, fall back to
  `openFile` (`620-plugin-dash-and-vim-jumps.js:134`).

Core commands that already exist (no Bob code needed):

- `editor:focus-left` / `editor:focus-right` — focus the tab group to
  the left/right. Attested by three independent sources: Bauer's notes
  (`exmap focusRight obcommand editor:focus-right`), the
  `j4ckofalltrades/obsideck` vanilla-command list, and the
  `xpgcrx/dotfiles` Vim table (`<C-w>h` → `editor:focus-left`,
  `<C-w>l` → `editor:focus-right`).
- `workspace:split-vertical` / `workspace:split-horizontal` — attested
  in Bauer's notes (`exmap splitVertical obcommand
  workspace:split-vertical`). Symmetric `editor:focus-top` /
  `editor:focus-bottom` are expected but **not yet verified** — confirm
  in-app before binding `j`/`k`.

## 3. What Bob already has (and what is missing)

- **Vim entry point.** `obsidian_vimrc.md` (vault root) is owned by
  `obsidian-vimrc-support` and already maps a large `]x` / `[x` family
  (`]s` review, `]w` lanes, `]n` links, `]b` bank, `]]` repeat).
  `bob-command-mode` owns `:`; the file header documents the critical
  rule: mappings that replay `:` **must be `nnoremap`**, or they recurse
  into command mode. Any `<C-w>` mapping **must be `nnoremap`** too.
- **Leaf/tab operations.** `bob-navigation-hotkeys` already owns
  `moveActiveTab(±1)` (reorder within a group),
  `duplicateCurrentTab()` (clone incl. view state),
  `closeSiblingTabs()`, and the `open-alternate-file` / `move-tab-*` /
  `duplicate-current-tab` / `close-tabs-*` commands
  (`630-plugin-vim-link-and-leaves.js:361`,
  `620-plugin-dash-and-vim-jumps.js:134`,
  `490-plugin-lifecycle.js:445–499`). The move-window feature is a
  natural sibling living in the same mixin.
- **Hint/status infrastructure.** The `[[ s w n b ]]` bracket-repeat
  status indicator (`547a-bracket-mode-view.js`,
  `547-bracket-mode-indicator.js`) and the Highlights status chip + line
  rail (`677d-highlights-hints.js`) are the in-house patterns for
  "show state beautifully without a modal." The yank-flash plugin
  (`bob-vim-yank-flash`) is the precedent for a brief visual flash as
  confirmation.
- **Vim-state detection.** `getCurrentVimMode(cm)` reads
  `cm.state.vim` with fallback to
  `vimrc-support.currentVimStatus`
  (`610-plugin-jumps-and-counted-keys.js:900+`). A `<C-w>`-hint trigger
  can reuse this to fire only in normal mode.
- **Missing:** no `<C-w>` bindings anywhere in the vimrc, no
  move-tab-to-adjacent-group command, no pending-prefix hint.

## 4. Key precedent: `<C-w>` works natively — after one conflict is cleared

1. Since Obsidian 0.14.0, the bundled `vim.js` supports `<C-w>` leader
   sequences natively (Bauer's notes: "licat modified the included
   `vim.js` so `C-w` leader shortcuts are supported natively").
2. The price: **the core "Close active tab/pane" hotkey on `Ctrl+W`
   must be removed**, or the keystroke never reaches Vim. Bryan's vault
   `hotkeys.json` does not rebind it, so the default is live — the
   feature's setup step #1 is deleting that binding, and the plugin
   should detect the conflict and say so (see §7).
3. Wiring is two vimrc lines per key, e.g. the attested pattern:
   `exmap focusRight obcommand editor:focus-right` +
   `nnoremap <C-w>l :focusRight<CR>`.
4. Caution from `obsidian-tab-shifter` (opened as external repo): it
   moves tabs by trusting that `getLeavesOfType` order matches visual
   group order, and its README admits this "might behave weirdly if you
   have a ton of splits" — plus it leans on unofficial `parent`/`id`
   fields (`src/typesUnofficial.ts`) and marks itself DesktopOnly for
   exactly that reason. Bob should **not** copy the ordering shortcut:
   resolve adjacency by walking the public `WorkspaceSplit` tree
   (parent chains), not by leaf enumeration order.

## 5. Critique of the proposal as stated

**It is a good idea.** It matches Vim muscle memory Bryan already has,
it composes with the existing `]x` walk family instead of competing
with it, and ~half the feature is free via core commands. Adjustments
I would make (all explicit):

1. **Define `h`/`l` for >2 groups.** "The other split" is only
   unambiguous with exactly two groups. Specify: focus the nearest
   group strictly in that direction in the split tree; if none, no-op
   with a hint flash (never wrap, never create — navigation must not
   mutate layout, matching Vim).
2. **`H`/`L` deviate slightly from Vim — keep the deviation, document
   it.** In Vim, `<C-w>H` moves the window to the far edge; the
   proposal moves it to the *adjacent* split, creating one if needed.
   Adjacent is right for a 2-column workflow (far-edge ≡ adjacent when
   there are two groups), but the vimrc comment/vim docs should say so
   in one line to avoid a future "this isn't vim behavior" bug report.
3. **Include `j`/`k` navigation from day one.** Vertical-only bindings
   with dead `j`/`k` will feel broken the first time a horizontal split
   or stacked group exists. Cost is two vimrc lines on already-existing
   core commands (after verifying the `focus-top`/`focus-bottom` ids).
   Scope `J`/`K` (horizontal move) as a stated follow-up, not v1.
4. **Add three tiny keys to the table: `w`, `q`, `v`.** `w` = cycle
   groups (Vim's `<C-w>w`; implement as focus-next-group, needed anyway
   once `h`/`l` hit a dead end with 3+ groups), `q` = close current tab
   (`workspace:close` — but note this *replaces* the freed `Ctrl+W`
   close, so it must be a deliberate second keystroke, which is safer),
   `v` = `workspace:split-vertical` on the current tab. All three are
   config-only. Do **not** bind `s`/`o`/`=`/`x` in v1: horizontal
   creation, close-others, equalize, and exchange each need design of
   their own.
5. **Normal mode only.** `<C-w>` in insert/visual mode must keep doing
   whatever it does today (in practice: nothing / word-delete habits).
   Gate the hint and all mappings on normal mode.
6. **Main area only.** Sidebars, drawers, popouts, and mobile: refuse
   with a one-line Notice. Precedent: tab-shifter went DesktopOnly
   rather than reason about these; Bob's plugin is not desktop-only, so
   an explicit guard + notice is the honest version.
7. **"Destroy a split" needs one verification, not new code.**
   Detaching the last leaf of a group should collapse the group
   (tab-shifter depends on it), but if an empty `WorkspaceTabs` lingers
   in this Obsidian version, explicitly detach it. Test, don't assume.

## 6. Recommended v1 key table

| Keys | Action | Implementation |
|---|---|---|
| `<C-w>h` / `<C-w>l` | Focus group left / right; no-op + hint when none | vimrc → `editor:focus-left/right` |
| `<C-w>j` / `<C-w>k` | Focus group below / above (verify ids first) | vimrc → core focus commands |
| `<C-w>H` / `<C-w>L` | Move current tab to adjacent left/right group, creating it if needed; collapses the source group when emptied | **new Bob commands** (see §7) |
| `<C-w>w` | Cycle to next group | new Bob command (trivial: ordered main-area groups) |
| `<C-w>q` | Close current tab | vimrc → `workspace:close` |
| `<C-w>v` | Split current tab right | vimrc → `workspace:split-vertical` |

## 7. Hint design (the "beautiful" requirement)

Vim shows nothing while `<C-w>` is pending; the proposal rightly wants
better. Constraints: the pending state lives inside CodeMirror's Vim,
which exposes no "prefix pending" event, so detect it with a
capture-phase `keydown` listener for `Ctrl+W` that (a) checks normal
mode via `getCurrentVimMode`, (b) shows the hint, (c) hides it on the
next keydown, `Escape`, focus loss, or a ~1.2 s timeout.

Recommended presentation — a small floating card, bottom-center above
the status bar, in the Task Card visual language:

```text
 WIN  h ← · l → · H move · L move · w cycle · q close · v split
```

- `kbd`-styled keys, one line, auto-dismiss; never steals focus, never
  writes.
- Pair it with a **destination flash**: on every `h`/`l`/`H`/`L`/`w`,
  briefly outline the newly focused group (300 ms fade), reusing the
  yank-flash idea from `bob-vim-yank-flash`. The flash is what makes
  jumps *legible* in a 2-column layout where both sides look alike.
- Alternative considered and rejected: a persistent status-bar `[[W]]`
  segment (bracket-indicator style). It is cheaper but invisible at the
  moment of need — the transient card plus flash teaches the keys
  exactly when the fingers are asking.

## 8. Implementation sketch (for the implementing agent)

1. **New commands** in `bob-navigation-hotkeys` (`490-plugin-lifecycle.js`
   + operations in `630-plugin-vim-link-and-leaves.js`, following the
   existing mixin pattern):
   `move-current-tab-to-split-left` / `...-right` /
   `focus-next-tab-group`. Move algorithm: resolve target group by
   walking the split tree from `activeLeaf.parent`; if none in that
   direction, `getLeaf('split', 'vertical')` (left = `before: true`
   via `createLeafBySplit` — verify arg order in-app); else
   `createLeafInParent(target, target.children.length)`; transfer via
   cloned view state (copy `duplicateCurrentTab`'s
   `setViewState`-with-`openFile`-fallback); `detach()` source;
   `setActiveLeaf(newLeaf, {focus:true})`; refuse pinned leaves,
   non-markdown? No — support all view types via state clone; refuse
   sidebar/drawer/popout leaves with a Notice.
2. **vimrc additions** (`obsidian_vimrc.md`): one `exmap` per Bob
   command + `nnoremap <C-w><key> :<name><CR>` lines. Keep the
   `nnoremap` rule from the file header.
3. **Conflict detection** at startup/layout-ready: if any command still
   binds `Ctrl+W` (notably the core close command), show a one-time
   Notice pointing at Settings → Hotkeys. (Hotkey introspection:
   `app.hotkeyManager`.)
4. **Hint card + flash**: new fragment (e.g. `632-plugin-ctrl-w-hints.js`;
   keep fragments ≤1000 lines per `AGENTS.md`, register in
   `fragments.json` source order, `npm run build` + `npm run
   build:check`, then `bob plugins sync`).
5. **Tests**: pure-function unit tests in the existing
   `scripts/test-navigation-*` (`node:test` + in-memory app harness)
   for group resolution and move planning (2-group, 3-group, dead-end,
   pinned, sidebar, last-tab-collapses); manual vault checklist for the
   flash/hint timing and the `Ctrl+W` conflict notice.
6. **Docs**: one page under `docs/` + the two vimrc-adjacent help lines
   (per `sase/memory/docs.md`, read it before touching docs).

## 9. Risks / open verifications

- `editor:focus-top` / `editor:focus-bottom` ids (expected, unverified).
- Whether `editor:focus-*` can land in a sidebar (acceptable if yes;
  document it).
- Empty-group collapse after last-leaf `detach()` in the current
  Obsidian version.
- `createLeafBySplit(leaf, 'vertical', before)` argument order for
  left-placement.
- Electron/macOS swallowing `Ctrl+W` before it reaches the editor even
  with the hotkey unbound (test on the Mac; the 0.14-era fix suggests
  it works, but re-verify on current builds).

## 10. Recommended solution

Ship v1 as: **core-command vimrc bindings for all navigation
(`h j k l`), two new Bob move commands (`H` `L`) with tree-based
adjacency, config-only `w q v`, a transient `<C-w>` hint card, and a
destination-group flash.** Total new plugin surface is two commands plus
one UI fragment; everything else is vimrc + docs. Explicitly deferred:
`J`/`K` horizontal moves, `s`/`o`/`=`/`x`, sidebar/popout/mobile
support, and any change to what single-group `h`/`l` do (no-op forever —
navigation never creates layout).
