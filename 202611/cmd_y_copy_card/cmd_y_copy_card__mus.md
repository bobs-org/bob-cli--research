# `<cmd+y>` copy-path panel redesign (`bob-navigation-hotkeys`)

Research report by `mus` — November 2026. Question: how to improve the
`Copy active file path` panel (Mod+Y), per the five requested changes.
Short answer at the top: **yes, do it, with four adjustments** (stable
accelerators instead of positional digits, keep palette commands for the
removed rows, cursor-line task scope for the block-ID row, and a
`yank.custom` list in `bob/config.yml` with fail-soft per-row rendering).
The rest of this note is the evidence and the concrete spec.

## 1. What the panel is today

- Entry point: `copy-active-file-path` command, default hotkey `Mod+Y`,
  in `plugins/bob-navigation-hotkeys/src/490-plugin-lifecycle.js`
  (around line 452: `callback: () => this.openYankPathPicker()`).
- Row source: `YANK_PATH_COMMANDS` (6 entries) in
  `src/010-requires-and-config.js` (~line 213): `absolute-tilde`,
  `absolute`, `basename`, `basename-no-extension`, `parent-directory`,
  `relative`. Titles in `YANK_PATH_PICKER_TITLES` (~line 255) and notice
  labels in `YANK_PATH_NOTICE_LABELS` (~line 246).
- Picker: `YankPathPickerModal extends FilteredPickerModal` in
  `src/200-filtered-picker-modals.js` (~line 910). Title
  `Copy active file path`, filter input `Filter path formats`, per-row
  icon + title + preview + `Copy` pill + `↵` affordance, footer hints
  (`KEYBOARD_HINTS` in `src/180-editor-transactions.js` ~line 816:
  Navigate / Move / Open / Dismiss). Key handling today is only
  Up/Down, Ctrl+N/P, Enter, Esc (`handleKeydown`, same file ~line 191).
- Value computation: `getYankPathText(kind, relativePath, basePath, homePath)`
  in `src/100-yank-and-paths.js` (~line 18); per-file result via
  `getActiveFileYankPath` / `yankActiveFilePath` /
  `createYankPathPickerItem` in `src/640-plugin-notes-and-task-move.js`
  and `src/100-yank-and-paths.js` (~line 50). Clipboard via
  `writeTextToClipboard` (~line 113 of the 640 file).
- The same `YANK_PATH_COMMANDS` list also registers six palette commands
  (`490-plugin-lifecycle.js` ~line 458, `YANK_PATH_COMMANDS.forEach`).
  Panel rows and palette commands are currently 1:1 but need not stay so.
- Docs: generated command table in `docs/bob-navigation-hotkeys.md`
  (~lines 32, 82–87). The `docs/` tree is generated — `npm run docs:check`
  must pass after changes (per that repo's `AGENTS.md`).
- No plugin settings UI exists: no `loadData`/`saveData` in this plugin.
  Shared file-backed config precedent is `bob/config.yml`
  (`BULLET_PROPERTY_CONFIG_RELATIVE_PATH = "bob/config.yml"`,
  `getBulletPropertyConfigPath` in `src/010-requires-and-config.js`
  ~line 534; parsed with `parseYaml` plus an mtime/size stat-key cache —
  see `loadBlocksLinesEnabled` in `src/020-config-load-and-tasks.js`).
  Unknown keys are tolerated (config comments note older/newer bob builds
  ignore unknown `capture:`/`stats:` keys), so a new `yank:` top-level key
  is safe for the Rust CLI.

Screenshot `~/tmp/screenshots/20261111_092732.png` (6 rows for `bob.md`,
first row selected): `Absolute path with tilde` (`~/bob/bob.md`),
`Absolute path` (`/Users/bbugyi/bob/bob.md`), `Basename` (`bob.md`),
`Basename without extension` (`bob`), `Parent directory`
(`(empty string)` — the file sits at the vault root, so this row copies
nothing useful), `Relative path` (`bob.md` — identical to Basename here).
Two readings fall out: at the vault root, Parent is actively
embarrassing (empty string) and Relative is a duplicate of Basename.

## 2. Requirement-by-requirement analysis

### 2a. Remove "Parent directory" and "Relative path"

Agree, with one scoping adjustment. Parent directory should go from the
panel unconditionally: it is the only row whose value is routinely the
empty string (any vault-root file), and a row that previews
`(empty string)` next to a `Copy` pill teaches users the panel cannot be
trusted. Relative path is weaker rather than broken: for nested files
(`projects/foo.md`) it carries folder context that Basename drops, and
unlike the absolute forms it never leaks the home directory when pasted
into shared text. Removing both is still the right call for a 4-row
panel that fits without scrolling, but **keep both palette commands**
(`yank-parent-directory`, `yank-relative-path`) registered. Panel
membership and palette registration are already two loops over one
array; split them (panel list vs. command list) so nobody's muscle
memory or automation breaks while the panel gets calmer.

### 2b. Every remaining option selectable via a single keypress; Enter keeps defaulting to absolute-tilde

This is the heart of the request and the one place the naive
implementation breaks. The panel's filter `<input>` owns focus, so bare
letters (`t`, `a`, `b`, `e`) would go into the filter box instead of
copying — stealing them (the `~`-flip precedent in
`src/450-picker-keydown.js` ~line 95 proves interception is possible)
would destroy filtering, since every title contains those letters.
Digits do not have this problem: nobody filters path formats with `1`.
So:

- Give every row a **stable per-kind accelerator**, not a positional
  number: e.g. `t` → absolute-tilde, `a` → absolute, `b` → basename,
  `e` → basename-no-extension, `i` (or `^`) → block ID, `1..9` →
  custom rows in config order. Stable-by-kind matters because the
  block-ID row is conditional (see 2c): positional `1..4` would renumber
  the path rows whenever the cursor sits on a block-ID task. Fixed keys
  never shift.
- Handle the keys in `handleKeydown` before the input consumes them,
  guarded exactly like the existing `~` interception (skip when
  `isComposing` / `keyCode === 229`, skip with Ctrl/Meta/Alt held), and
  **only when the filter is empty** for letter keys; digits may fire
  even with a non-empty filter since they never collide with real
  queries. This preserves "type to filter, Enter to copy the match"
  while making "Mod+Y then `b`" copy the basename instantly.
- Keep `selectedIndex` pinned to absolute-tilde on open regardless of
  row order, so Enter always means what it means today. Render the
  accelerator as a `<kbd>` chip in each row (right-aligned, ahead of the
  `Copy` pill) plus one footer hint (`t a b e … Copy`, `↵ Default`,
  existing Navigate/Move/Dismiss hints unchanged). Show `↵` only on the
  default row; every row keeps click-to-copy.
- Reliability notes: ignore `event.repeat` (the Task Card key model in
  `src/314-task-card-key-model.js` already suppresses repeated action
  keys — copy that guard); close-before-copy to avoid double-fire via
  the existing `opening` flag in `openItemAtIndex`.

Alternatives considered and rejected: Alt+letter (violates the
single-keypress requirement and collides with Option-key Vim mappings);
removing the filter box (kills discoverability of custom rows); first-
letter-of-title mnemonics (`a` for two "Absolute…" rows — ambiguous).

### 2c. New block-ID row when a task with a block ID is selected

Good idea; tighten the trigger wording. "Selected" should mean **the
cursor (main cursor) sits on an open task line whose text ends in a
trailing block ID**, detected with the existing
`getTrailingBlockIdSpan(line)` (`src/020-config-load-and-tasks.js`
~line 258, `BULLET_PROPERTY_TRAILING_BLOCK_ID_RE`). That helper is the
 codebase's single definition of "trailing block ID" (used by task-move,
 project-schedules, dependency stage), so reuse it rather than a new
 regex. Concretely: on `openYankPathPicker`, resolve the active
 Markdown view + editor (`getActiveMarkdownView`, same pattern as
 `openTaskMoveOrPomodoroBulletPicker` in the 640 file ~line 472),
 read the cursor line via `getEditorLine`/`getEditorCursor`
 (`src/170-open-task-jump.js` ~line 814), require it to match an open
 task line (`OBS...` statuses / project task line), extract the span,
 and offer kind `block-id`, title `Block ID`, preview `^foo-bar-baz`
 **with the caret** (matches the request's `^foo-bar-baz` example and is
 what pastes correctly after `#` in `[[note#^id]]`).
 Copy path goes through the existing `yankActiveFilePath(kind, file)`
 flow with a block-ID branch (needs the editor line, not just the
 file — thread it through the picker item at construction).

Scoping decisions (recommended): hide the row entirely when there is no
 block ID under the cursor (a permanently visible but `Unavailable` row
 would punish the common case); Reading-mode / no-editor / cursor on a
 non-task line all hide it; visual selections are ignored in v1 (a
 selection that merely contains `^id` somewhere is too fuzzy — cursor
 line is predictable and matches how Ctrl+Shift+P/B/L already resolve
 "the task under the cursor"). Palette command `yank-block-id`
 registered for parity, refusing with a Notice when absent.

### 2d. Configurable custom rows with `{variable}` templates (chezmoi)

Right home, right file. This plugin has no settings tab and
`bob/config.yml` (chezmoi-managed at
`home/dot_config/bob/config.yml`) is already the shared knob board the
 plugin reads (bullet properties, relations kill-switches, plan caps).
 A new top-level `yank:` key fits the file's conventions and is ignored
 by bob-cli builds that do not know it yet. Proposed schema:

```yaml
yank:
  custom:
    - name: "Task ref"
      template: "the ^{task_id} task in the {abs_file_with_tilde}"
```

- Variables are exactly the non-custom panel values, snake_case:
  `{abs_file_with_tilde}`, `{abs_file}`, `{basename}`,
  `{basename_no_ext}`, plus `{block_id}` (alias `{task_id}`, bare id
  without caret — templates write the `^` themselves, as in the user's
  example) and —
  recommend keeping — `{relative}` and `{parent}` even though the rows
  leave the panel, so templates can still use them. That satisfies
  "support injected variables containing the appropriate values of the
  other (non-custom) options on that panel" without resurrecting rows.
  The user's example then reads naturally; note the literal `^` before
  `{task_id}`/`{block_id}` is intentional in the example and must be
  documented (the variable itself should NOT include the caret, or
  `^{block_id}` double-counts — pick one; I recommend the variable
  carries the bare id and templates write the `^`, exactly as the
  user's example does).
- Rendering: single-pass `{name}` substitution over a frozen context
  object built per panel-open (same values the rows preview). Escape
  hatch `{{` → `{`, `}}` → `}`. Unknown variable → row renders
  `Unavailable` with a console warning and a Notice on attempt; never
  silently empty (silent empties are how `Parent directory` lost trust).
  A template referencing `{block_id}` with no block ID under the
  cursor behaves like the block-ID row: hidden in v1 (recommended) or
  `Unavailable` — either way never a half-rendered string.
- Validation at load (fail-soft per row, panel still opens): custom must
  be a list, each entry needs non-empty `name` (unique, ≤ 40 chars) and
  `template` (≤ 500 chars); cap the list at 5 so the panel plus block
  ID still fits without scrolling. Violations drop that row with one
  Notice, not a dead panel. Reload per gesture through the existing
  stat-key cache pattern (`020-config-load-and-tasks.js`), so a chezmoi
  apply + `bob plugins sync` takes effect on the next Mod+Y with no
  Obsidian restart.
- Configure Bryan's example in the chezmoi repo as the first entry
  (name it `Task ref`), proving the feature on day one.

## 3. Critique — is this a good idea, and what would I change?

Yes, with the adjustments above it is a clean, high-leverage change:
 the panel today has a dead-feeling row (empty Parent) and a duplicate
 (Relative at root), no keyboard path beyond Up/Down+Enter, and no way
 to express the very common "which task in which file" reference this
 request's template captures. The plan's instincts — fewer rows, faster
 keys, stable default, contextual block ID, user templates — all point
 the same direction: a panel that answers in one keypress what today
 takes arrow keys plus judgment.

 Changes I would insist on (beyond §2): (1) keep removed rows' palette
 commands; (2) stable per-kind accelerators, not positional digits, so
 the conditional block-ID row never renumbers paths; (3) cursor-line
 task scope for block ID (not arbitrary selection text); (4) fail-soft
 per-row template errors; (5) pin `selectedIndex` to absolute-tilde on
 every open. One deliberate non-change: do NOT reorder rows so the
 default sits anywhere but first — Enter-default and first-row are the
 same muscle memory; keep them together.

## 4. Recommended solution (build spec)

- Rows (panel order): `Absolute path with tilde` (`t`, default, Enter),
  `Absolute path` (`a`), `Basename` (`b`),
  `Basename without extension` (`e`), conditional `Block ID` (`i`),
  then custom rows in config order (`1..5`). Footer gains a
  `t a b e i 1–5 Copy` hint; each row shows its `<kbd>`.
- Config: `yank.custom` in `bob/config.yml` as in §2d; ship Bryan's
  `the ^{task_id} task in the {abs_file_with_tilde}` example as entry 1
  via the chezmoi repo.
- Code: split `YANK_PATH_COMMANDS` into panel list vs. palette list
  (`010`); extend `getYankPathText` + `getActiveFileYankPath` with
  `block-id` and `custom:<n>` kinds (`100`, `640`); add cursor-line
  block-ID resolution at picker construction (`640`, reusing
  `getTrailingBlockIdSpan` + `getEditorLine`); key interception in
  `YankPathPickerModal.handleKeydown` / `FilteredPickerModal`
  (`200`, modeled on the `~` precedent in `450`); template renderer +
  validator with stat-key caching (`020`-adjacent new fragment);
  styles for `<kbd>` chips (`styles.css`); regenerate docs
  (`npm run docs:check`, `npm run build:check` per repo `AGENTS.md`).
- Tests (repo currently has none for yank — add them): unit tests for
  `getYankPathText` all kinds, template renderer (escape, unknown var,
  block-ID-absent hiding, 5-row cap, per-row fail-soft), block-ID span
  detection on task vs. non-task lines, and key-dispatch (letter fires
  only with empty filter, digit fires anytime, repeat ignored, Enter
  still default). Drive through the existing harness pattern
  (`scripts/navigation-hotkeys-harness.cjs`, `scripts/modal-harness.cjs`).
- Rollout: implement in `bob-plugins`, `bob plugins sync` to the vault,
  verify Mod+Y on a root file (no empty row), a nested file, a
  block-ID task line, and a non-task line; confirm Enter, each
  accelerator, click, and filter-then-Enter all copy correctly.

## 5. Sources checked

`src/010-requires-and-config.js` (commands, titles, config-path
 helpers), `src/100-yank-and-paths.js` (value computation, picker items),
 `src/200-filtered-picker-modals.js` (picker + base key handling),
 `src/450-picker-keydown.js` (`~` interception precedent),
 `src/314-task-card-key-model.js` (bare-key + repeat-suppression
 precedent), `src/640-plugin-notes-and-task-move.js` (picker open/copy
 flow), `src/490-plugin-lifecycle.js` (Mod+Y registration),
 `src/170-open-task-jump.js` (cursor/line helpers),
 `src/020-config-load-and-tasks.js` (block-ID span, stat-key config
 caching), `docs/bob-navigation-hotkeys.md` (generated command table),
 `home/dot_config/bob/config.yml` (chezmoi config to extend),
 screenshot `~/tmp/screenshots/20261111_092732.png` (viewed: 6 rows,
 empty-string Parent, Relative==Basename at root).
