# The Obsidian ⌘Y panel as a keyed Copy card

*Research report · researcher `cld` · 2026-11-11*

**Question.** How should the `⌘Y` ("Copy active file path") panel in Obsidian be
reworked so that every option takes one keypress, the tilde path stays the `↵`
default, a task's block ID can be copied, and user-defined template rows can
reuse the panel's values? Is the plan sound, and what would I change?

**Short answer.** The plan is sound. Its core problem is the filter field, not
the row list. My recommendation is to replace the filtered picker with a
**keyed Copy card**, a small modal with no text input. Every row gets a fixed
mnemonic keycap, so muscle memory never shifts. The card should use the same
grammar as Bob Mac Capture's existing `⌘Y` Copy card, which uses letters for
fixed rows and digits for lists. Templates go in `~/.config/bob/config.yml` under a
new `copy.templates` key and use a tiny `{variable}` language. I recommend a
few adjustments to the request, listed in
[§3](#3-adjustments-to-the-requirements-called-out). The two that matter most:
the variable is `{block_id}`, not `{task_id}`, and two rows are renamed to stop
calling `bob.md` a "basename".

---

## 1. What exists today

### 1.1 The screenshot

What the screenshot `~/tmp/screenshots/20261111_092732.png` shows (macOS,
`bob.md` at the vault root):

| Observation | Consequence |
| --- | --- |
| A focused **"Filter path formats"** search field | Every letter goes into the filter, which is why single-key selection is impossible today. A filter on a list of six items costs more than it saves. |
| Six two-line rows, each with a copy icon **and** a "Copy" pill | The icon and pill repeat on every row, so they add noise without information. The `↵` glyph already marks the default. |
| `Parent directory` → `(empty string)`; `Relative path` → `bob.md` | At the vault root, one row is empty and the other duplicates `Basename`. You were right to remove both. |
| `Basename` = `bob.md`, `Basename without extension` = `bob` | Obsidian's own API uses `basename` to mean `bob` (`TFile.basename`) and `name` to mean `bob.md`. The labels contradict the platform's vocabulary. |
| About 45% of the modal is empty white space | The modal has a fixed `height: min(82vh, 840px)` (`styles.css:5-14`). The Task Card already overrides this with `height: auto` (`styles.css:2129-2134`). |
| Footer: `↵ Open` | Wrong verb. The panel copies. The hints are the shared `KEYBOARD_HINTS` (`src/180-editor-transactions.js:816-821`). |
| Notice after copying: `Copied absolute path` (for both the `~` and the absolute row) | The confirmation doesn't say *what* was copied (`YANK_PATH_NOTICE_LABELS`, `src/010-requires-and-config.js:246-253`). |

### 1.2 Where the code lives

All of it is in `bob-plugins/plugins/bob-navigation-hotkeys`, which uses the
fragment build (edit `src/`, then run `npm run build`; never hand-edit `main.js`):

| Piece | Location |
| --- | --- |
| Command `copy-active-file-path`, `Mod+Y` | `src/490-plugin-lifecycle.js:451-456` |
| Six standalone `yank-*` commands (no hotkeys) | `src/490-plugin-lifecycle.js:458-464`, table in `src/010-requires-and-config.js:212-244` |
| Row titles | `YANK_PATH_PICKER_TITLES`, `src/010-requires-and-config.js:255-262` |
| Path computation | `getYankPathText` / `createYankPathPickerItem`, `src/100-yank-and-paths.js:18-60` |
| Modal | `YankPathPickerModal extends FilteredPickerModal`, `src/200-filtered-picker-modals.js:910-959` |
| Base picker (input-focused, keys handled on the `<input>`) | `src/200-filtered-picker-modals.js:1-443`, `handleKeydown` at `:191-211` |
| Open, copy, clipboard, Notice | `src/640-plugin-notes-and-task-move.js:3-10, 47-129` |
| Tests | **None.** No `scripts/test-*.cjs` file covers the yank picker. |

### 1.3 Building blocks already in the repo

These make the redesign cheap and keep it consistent with the rest of Bob:

* **The key-card design tokens.** `.bob-key-card-key`, `.bob-key-card-row`,
  `.bob-key-card-footer`, and an `.is-alias` dashed keycap
  (`styles.css:2073-2125`). The decay card and the Task Card already use them.
* **A pure key resolver with real-world guards.** `resolveTaskCardKey`
  (`src/314-task-card-key-model.js`) ignores IME composition (`isComposing` /
  `keyCode 229`), text-input targets, and auto-repeated action keys
  (`event.repeat`). Its row-to-shortcut table is `TASK_CARD_ROW_SHORTCUTS`.
* **A catch-all modal scope.** `DeleteFileConfirmModal` registers
  `scope.register(null, null, fn)` and returns `false`, so the card owns every
  key while it is open (`src/672-delete-confirm-modal.js:126`). Obsidian's
  `Scope.register` documents a `null` key as matching every key.
* **Opening-chord protection.** The decay card records the keys held when it
  opened and ignores them until they are released
  (`src/060-decay-card-modal.js`, `openingChordKeys`).
* **Owning-task resolution.** `findOwningTaskLine(lines, line)` returns the
  cursor line if it is a `#task`, else the nearest ancestor list item that is
  one (`src/070-recommended-roll-batch.js:442-465`). Relations, dependencies,
  and the Blocks API already use it. `isObsidianTaskLine` requires the `#task`
  tag (`src/130-fences-and-status.js:86-94`), so Pomodoro rows and plain
  bullets are never "tasks".
* **Block-ID parsing.** `getTrailingBlockId(line)` returns the bare id
  (`src/020-config-load-and-tasks.js:434-442`, regex
  `/[ \t]+\^([A-Za-z0-9-]+)[ \t]*$/` at `src/010-requires-and-config.js:433-434`).
  `cleanTaskDisplayText(line)` returns the task's human title.
* **A config loader pattern.** The plugin already reads
  `~/.config/bob/config.yml` (`properties`, `relations`, `types`, `priority`),
  with an mtime+size cache so edits apply on the next gesture without a reload
  (`src/020-config-load-and-tasks.js:1-45`).

### 1.4 The sibling design: Bob Mac Capture's `⌘Y` Copy card

Bob Mac Capture already has a `⌘Y` **Copy card** for references
(`bob-cli/docs/reference/mac-capture/keyboard.md:37-52`;
`bob-mac-capture/Sources/RefsCore/RefsCopy.swift:19-86`). Its grammar:

* There is **no filter field**.
* Each fixed row has a **fixed letter glyph**: `I` Marker ID, `T` Title,
  `W` Wiki link, `N` Note path, `P` PDF path, `O` Obsidian link.
* **Digits `1–9`** are reserved for *lists* (notes, highlights, links).
* `Return` copies the selected row. One row is the default.
* Rows that don't apply are absent (an arXiv row only appears when there is an
  arXiv id).
* `Option` flips a row to its alternate payload, as native macOS menus do.

So `⌘Y` already means "Copy card, letters pick rows" in Bob. The Obsidian
panel should feel like the same object.

---

## 2. Is this a good idea?

Yes, with a sharper framing. **This is not "a path picker with more rows". It
is Obsidian's Copy card.**

* **The frequency is high and the menu is small.** For four to seven stable
  options, keyboard accelerators beat searching (see Hick–Hyman law). Today
  only the default is fast (`⌘Y ↵`). Every other row costs arrows plus `↵`, or
  typing into the filter. With keycaps, every row is `⌘Y` plus one key.
* **The block-ID row is the most valuable addition.** It turns `⌘Y` into a
  "reference this thing" gesture, the way JetBrains' "Copy Path/Reference…"
  menu offers references alongside paths. Your
  template example (`the ^… task in ~/bob/…`) shows the real use: handing a
  precise task pointer to an agent prompt.
* **Templates are worth it if the language stays tiny.** Use `{name}` and
  `{{`/`}}` only. Conditionals, filters, shell quoting, and JS eval would turn a
  copy menu into a templating engine you then have to debug.
* **Removing `Parent directory` and `Relative path` is right.** The screenshot
  shows why: one is empty and the other duplicates `Basename`.

What I would **not** do:

* **Keep the filter and add digit shortcuts.** This is the minimal-diff option,
  since digits rarely appear in filter text. But positions shift as the
  conditional block-ID row and the templates come and go, and the
  useless filter stays.
* **Collapse rows into `⌥` alternates** (Path ⇄ Absolute, File ⇄ Note name), as
  the Mac card does. This makes the card smaller, but it breaks your "one
  keypress" requirement and hides options.
* **Reorder by recency or context** (for example, putting block ID first when
  on a task). Stable positions are worth more than adaptive ones in a gesture
  you use dozens of times a day. The `↵` default stays fixed on the path.
* **Mint a block ID from the copy gesture.** A copy should never write to the
  vault. When the task has no ID, the card *teaches* `⌃6` (the existing
  "Rename selected block ID" prompt, which also names a block that has none)
  instead of writing.

---

## 3. Adjustments to the requirements (called out)

| # | Your requirement | My adjustment | Why |
| --- | --- | --- | --- |
| A1 | "Selected via a single keypress" | **Remove the filter field.** Fixed rows get **mnemonic letters**. Template rows get a configured letter or, by default, digits `1–9` in config order. | Letters don't move when rows appear or disappear. This matches the Mac Copy card (letters for things, digits for lists). |
| A2 | Keep "Basename" / "Basename without extension" | Rename them **"File name"** (`bob.md`) and **"Note name"** (`bob`). | Obsidian's `TFile.basename` is `bob`. "Note name" is what you type inside `[[…]]`. |
| A3 | "Absolute path with tilde" | Label it **"Path"**. It is the default and the canonical Bob form (the Mac card abbreviates to `~` too). Keep **"Absolute path"** for tools that don't expand `~`. | The default row deserves the shortest name. The value is printed right beside the label, so nothing is hidden. |
| A4 | New option when "a task that has a block ID [is] selected" | Use the cursor's **owning task**: the cursor line if it is a `#task`, else its nearest `#task` ancestor (`findOwningTaskLine`). Show a **"Task" caption with the task's title** above the row. | It matches how relations and dependencies already find "the task", so `⌘Y` on a note under the task still works. The caption shows *which* task's ID you're about to copy. |
| A5 | Copy `^foo-bar-baz` | The row copies **`^foo-bar-baz`**, but the template **variable `{block_id}` is bare** (`foo-bar-baz`). You write `^{block_id}`, exactly as in your example. | Bob and Obsidian treat the block ID as the bare token (`getTrailingBlockId`, `BlockCache.id`, `[[note#^id]]`). It composes in both prose (`^{block_id}`) and links (`#^{block_id}`). |
| A6 | Variable named `{task_id}` | Name it **`{block_id}`**. Don't support `task_id` as an alias. An unknown-variable error suggests the right name instead. | Bob tasks carry *two* ids: `[id:: bob__bank-records] ^bank-records` (`~/bob/bob.md:26`). "task_id" would be ambiguous. |
| A7 | Variable `{abs_file_with_tilde}` | **Variable name = row label in snake_case**: `{path}`, `{absolute_path}`, `{file_name}`, `{note_name}`, `{block_id}`. | One guessable rule, with no list to memorize. |
| A8 | (unstated) what happens when a template needs `{block_id}` and there is none | No owning task: the row is **hidden**. Owning task without an ID: the row is **dimmed** and reads "needs a block ID · ⌃6 names one". | Path-copying (the common case) stays clean. When you're on a task, the card explains the gap instead of silently dropping a row you expected. |
| A9 | (unstated) config location | **`~/.config/bob/config.yml` → `copy.templates`** (chezmoi: `home/dot_config/bob/config.yml`). | The plugin already reads this file. bob-cli ignores unknown top-level keys (`bob-cli/docs/reference/configuration.md:352-353`), and no Rust config uses `deny_unknown_fields`. It is chezmoi-managed, as you asked. |
| A10 | (unstated) feedback | The Notice shows the copied value: `Copied ~/bob/bob.md`. | It is more trustworthy than `Copied absolute path`, which today is printed for two different payloads. |

---

## 4. Design decisions and alternatives

### 4.1 Keymap

| Key | Row | Copies (example) | Template variable |
| --- | --- | --- | --- |
| `P` · **↵** | Path | `~/bob/bob.md` | `{path}` |
| `A` | Absolute path | `/Users/bbugyi/bob/bob.md` | `{absolute_path}` |
| `F` | File name | `bob.md` | `{file_name}` |
| `N` | Note name | `bob` | `{note_name}` |
| `I` | Block ID *(owning task has one)* | `^bank-records` | `{block_id}` → `bank-records` |
| `T` (configured) / `1–9` (default) | Your templates | `the ^bank-records task in ~/bob/bob.md` | — |

Other keys:

* `↵` copies the highlighted row. The highlight starts on Path.
* `↑` `↓` / `⌃N` `⌃P` move the highlight.
* `esc` closes the card.

Rules:

* Keys are **case-insensitive**. Shift-letter is reserved for future
  alternates.
* `P A F N I` are **reserved**. A template that claims one, or a duplicate key,
  is shown with a red reason and gets no key. It is never silently dropped and
  never steals a built-in key.
* **Auto-repeat events are ignored** (`event.repeat`), so holding `⌘Y` can
  never fire a row.
* **Optional delight:** pressing `⌘Y` again (a fresh press, not a repeat)
  copies the highlighted row. That makes `⌘Y ⌘Y` copy the path, so you never
  have to leave the chord. It is safe because the card's catch-all scope
  consumes the keystroke before any global hotkey.

Considered and rejected:

* **Positional digits for everything.** Simple, but the numbers move when the
  task rows appear.
* **A `^` alias for `I`.** It is cute, since `^` is the first character copied,
  but it is a Shift chord. Accept it as an undocumented alias at most.
* **Chord-through** (`⌘` held + letter). macOS key equivalents such as
  `⌘Q`/`⌘W`/`⌘H`/`⌘C` would be swallowed by the OS/app menu for some
  letters. That is an inconsistent rule, so leave it out.

### 4.2 Block-ID detection (reliability core)

1. Take the **active editor's live buffer**, not `metadataCache`, which lags
   behind edits. In Reading view with no editor, show no task group.
2. **Single cursor only**, as `⌃6` requires (`hasSingleCursor`). Use the
   selection head's line. Lines inside fences or frontmatter don't count (that
   is built into `isObsidianTaskAtLine`).
3. `owner = findOwningTaskLine(lines, head.line)`, then
   `id = getTrailingBlockId(lines[owner])` and
   `title = cleanTaskDisplayText(lines[owner])`.
4. **Same-file invariant:** every value in the card describes the *active
   file*. A `[[other#^id]]` link under the cursor is **never** used as the
   block ID. Otherwise a template would print another file's ID next to this
   file's path, which is a silently wrong pointer. (Pomodoro Task Links are
   safe: Pomodoro rows aren't `#task` lines, so they have no owning task.)
5. Take a **snapshot at open**. Copy from the snapshot, so an edit that races
   the keypress can't change the payload.

This works for `^prj` project tasks (`the ^prj task in ~/bob/prj/foo.md`) and
`^ref-…` reading tasks without special cases.

### 4.3 Template language

* `{name}` substitutes a variable. `{{` and `}}` produce literal braces (the
  `str.format` convention). That's the whole language.
* **Single pass.** Substituted values are never re-scanned, so a path that
  contains `{` can't inject anything.
* The `{placeholder}` style already appears in the same config file
  (`highlights.listen_command: … {target} … {audio}`).
* **Errors render in the card, never on the clipboard.** An unknown variable,
  an unbalanced brace, or an empty template shows a red reason on that row and
  disables its key. Known misspellings get a hint, for example
  `{task_id}` → "did you mean `{block_id}`?" and `{basename}` → `{file_name}`.
* **YAML trap, handled explicitly.** An unquoted `template: {path}` parses as a
  YAML *mapping*, and `… #task` starts a comment. If the loader sees a
  non-string template, its reason reads "quote the template — YAML read it as a
  mapping". The documented examples always use double quotes.

Rejected: Handlebars/Templater/JS expressions, per-variable filters
(`{path|sh}`), and conditionals. Revisit only if a concrete template needs one.

### 4.4 Config shape

```yaml
# Obsidian ⌘Y Copy card (bob-navigation-hotkeys): extra rows after the built-in
# Path (P), Absolute path (A), File name (F), Note name (N), and Block ID (I).
# Variables: {path} (~/…), {absolute_path}, {file_name}, {note_name}, and
# {block_id} (no caret — write ^{block_id}). {{ and }} are literal braces.
# A row that uses {block_id} appears only when the cursor's task has one.
# Always double-quote templates. `key` is one letter or digit; omit it to get
# 1–9 in list order. Edits apply on the next ⌘Y.
copy:
  templates:
    - key: t
      label: Task for an agent
      template: "the ^{block_id} task in {path}"
```

* It is a **list** (order is meaningful) of `{template, label?, key?}`.
* `label` defaults to the template text.
* The section is surface-neutral (`copy:`), so the Mac Copy card could adopt
  `copy.*` later without renaming.
* On mobile, where there is no `fs`, templates are absent and the card still
  works.
* I dropped "in **the** {path}" from your phrasing. Read aloud,
  "in ~/bob/bob.md" is cleaner than "in the ~/bob/bob.md". Either works, and
  the wording is yours to pick.

---

## 5. Visual design

The card is compact and content-sized (`height: auto`, `width: min(560px, 92vw)`).
It has no search field. Values sit in one aligned monospace column.

**On a task with a block ID** (cursor anywhere in its block):

```
╭────────────────────────────────────────────────────────────────╮
│  ⧉  Copy                                                bob.md │
│                                                                │
│ ▌[P]  Path            ~/bob/bob.md                           ↵ │
│  [A]  Absolute path   /Users/bbugyi/bob/bob.md                 │
│  [F]  File name       bob.md                                   │
│  [N]  Note name       bob                                      │
│  ───────────────────────────────────────────────────────────── │
│  TASK  Use records to start tracking bank transactions again!  │
│  [I]  Block ID        ^bank-records                            │
│  [T]  Task for an …   the ^bank-records task in ~/bob/bob.md   │
│                                                                │
│  ↵ copy path   ↑↓ select   esc close                           │
╰────────────────────────────────────────────────────────────────╯
```

**On a task with no block ID:**

```
│  ───────────────────────────────────────────────────────────── │
│  TASK  Add event note to 2026-11-12 recruiter Google Event!    │
│  [I]  Block ID        none · ⌃6 names one                (dim) │
│  [T]  Task for an …   the ^‹block_id› task in ~/bob/…    (dim) │
```

**Not on a task** (the common path-copy case): the four file rows only, with
the divider and task group omitted entirely.

Styling notes. Reuse the existing tokens. Don't invent a new look.

* **Keycaps.** Use a compact variant of `.bob-key-card-key`: 22×22 px, monospace
  uppercase glyph, 2 px bottom border for a hint of key depth. On the
  highlighted row the border takes `--interactive-accent` and the glyph
  `--text-accent`. A template whose key is a digit renders the same way.
* **Columns.** The label column is fixed-width (≈ 120 px, `--text-muted`, 0.9em).
  The value column uses `--font-monospace`, `--text-normal`, single line, with
  middle truncation done in JS so the file name stays visible. The full value
  goes in `title`.
* **Selection.** Keep the current accent tint and left bar (visible in today's
  screenshot). Show `↵` only on the highlighted row. Drop the per-row copy icon
  and the "Copy" pill.
* **Task caption.** Small caps `TASK` in `--text-faint`, then the task title in
  normal case with a tail ellipsis. This is the reliability affordance that
  confirms which task the ID belongs to.
* **Dim rows.** Opacity ≈ 0.55. A missing variable renders as a dashed-outline
  chip `‹block_id›`, and the reason sits right-aligned in small text.
* **Footer.** One hairline-separated line whose `↵` hint names the highlighted
  row (`↵ copy path`, `↵ copy block ID`).
* **Header.** Title "Copy", with the vault-relative path on the right as quiet
  context. The command palette name becomes "Copy path, block ID, or template".
  Keep the command **ID** `copy-active-file-path` so existing hotkey bindings
  survive.
* **Motion.** Close immediately on copy. The Notice (`Copied ~/bob/bob.md`) is
  the confirmation. Row hover and selection transitions sit behind
  `prefers-reduced-motion: no-preference`, like `.bob-key-card-row`.
* **Accessibility.** The list is `role="listbox"` with `aria-activedescendant`.
  Each row is `role="option"` with `aria-keyshortcuts="P"` and so on, and
  `aria-disabled` on dim rows.

---

## 6. Reliability checklist

| Failure mode | Guard |
| --- | --- |
| Holding `⌘Y` fires a row through auto-repeat | Ignore `event.repeat` (pattern from `resolveTaskCardKey`). |
| IME composition / dead keys | Ignore `isComposing` / `keyCode 229`. |
| A global hotkey fires while the card is open | `scope.register(null, null, …)` returns `false` and consumes every key. Escape is handled explicitly. |
| Block ID from the wrong task or file | Owning-task rule, same-file invariant, and a title caption (§4.2). |
| Stale ID after a fast edit | Read the live editor buffer and snapshot it at open. |
| Template typo copies `{task_id}` literally | Unknown variable → red row, key disabled, "did you mean" hint. |
| YAML parses `{path}` as a mapping | Detect a non-string template and say "quote the template". |
| Template key collides with a built-in or another template | Red reason, no key, never silently reassigned onto a built-in. |
| Config edited while Obsidian runs | mtime+size cache (the existing loader pattern), reloaded on each `⌘Y`. |
| Clipboard write fails | Keep the card open, show the reason, and fire the Notice (today's `writeTextToClipboard` already returns `false`). |
| No absolute base path (mobile) | Path/Absolute rows are unavailable. The highlight starts on the first available row. |
| Multi-cursor | No task group, same rule as `⌃6`. |

---

## 7. Implementation sketch

One focused bob-plugins change plus one chezmoi commit.

**bob-plugins (`plugins/bob-navigation-hotkeys`)**

1. **`src/101-copy-card-model.js`** (new, pure, no Obsidian):
   * `COPY_CARD_BUILTIN_ROWS`: `{id, key, label, variable, needs}`.
   * `parseCopyTemplate(text)` → tokens or error.
   * `renderCopyTemplate(tokens, vars)` → text or a missing-variable list.
   * `buildCopyCardModel({file values, task: {title, blockId}|null, templates, config errors})`
     → ordered rows with `key`, `available`, `preview`, `reason`, `payload`, plus
     `defaultRowId`.
   * `resolveCopyCardKey(model, event)` → `copy-row` | `move` | `close` | null.
   * Built-ins are just templates (`"{path}"`, `"^{block_id}"`, …), so there is
     one row pipeline.
2. **`src/102-copy-card-config.js`** (new): loads `copy.templates` with the
   mtime cache. Validates the shape, keys, reserved letters, and duplicates, and
   emits per-row reasons.
3. **`src/215-copy-card-modal.js`** (new): `CopyCardModal extends Modal`, with
   no input, a catch-all scope, rendering on the key-card tokens, and
   snapshot-at-open.
4. **`src/640-plugin-notes-and-task-move.js`**: `openYankPathPicker()` builds the
   context (active file plus the editor's owning task) and opens
   `CopyCardModal`. `writeTextToClipboard` gets a value-bearing Notice.
5. **`src/010-requires-and-config.js` / `src/490-plugin-lifecycle.js`**:
   * Retitle the command and keep its ID.
   * Keep the six palette-only `yank-*` commands unchanged, since removing them
     could break someone's binding.
   * Add `yank-block-id`.
   * Retire `YankPathPickerModal` and `YANK_PATH_PICKER_TITLES`.
6. **`styles.css`**: a `.bob-copy-card*` block plus the compact keycap variant,
   with `height: auto`.
7. **Tests**: `scripts/test-navigation-copy-card.cjs` (added to `npm test`)
   should cover:
   * the template grammar: escapes, unknown variables, single pass, YAML
     mapping;
   * owning-task resolution: child bullet, Pomodoro Task Link, fence, no
     `#task`;
   * key resolution: repeat, IME, reserved and duplicate keys, digits;
   * row availability in all three task states;
   * a FakeNode render smoke test, modelled on
     `test-navigation-task-card-view.cjs`.
8. **Docs**:
   * Add a "Copy card (`⌘Y`)" section in `docs/bob-navigation-hotkeys.md` with
     the keymap, variables, and config example.
   * Regenerate the command inventory and run `npm run docs:check`.
   * Check whether bob-cli's mirrored
     `docs/reference/plugins/bob-navigation-hotkeys.md` needs regenerating.
9. Run `npm run build`, `npm test`, then **`bob plugins sync`**.

**chezmoi.** Add the `copy:` block from §4.4 to
`home/dot_config/bob/config.yml`, commit, then run `chezmoi update -a --force`.
The order is free in both directions: old plugins and bob-cli both ignore the
unknown key.

**Size.** About 400–500 lines of new JS across three fragments (each well under
the 1000-line fragment cap), about 120 lines of CSS, and about 300 lines of
tests. It fits in one PR. A one-paragraph decision record ("Copy cards key
fixed rows by letter, lists by digit; `⌘Y` never writes") would be a reasonable
`decisions` web entry once you accept the design. Write it through
`/sase_memory_write`.

---

## 8. Open questions for Bryan

1. **Letters.** Are `P A F N I` right for you? The main alternative is `T` for
   the tilde path, but then `T` can't be your task template.
2. **Renames.** OK with "Path / Absolute path / File name / Note name"?
3. **`⌘Y ⌘Y`** to copy the highlighted row: keep it as a delight, or skip it
   for rule minimalism?
4. **Template wording.** `the ^{block_id} task in {path}` or your original
   `… in the {path}`?
5. **Future variables** I deliberately left out: `{vault_path}` (for
   `[[{vault_path}#^{block_id}]]` links) and `{task}` (the task title). Each is
   a cheap later addition if a real template needs it.

---

## 9. Recommended solution

Replace the `⌘Y` filtered picker with a **keyed Copy card**, the Obsidian twin
of Bob Mac Capture's `⌘Y` Copy card:

1. **No filter field.** Built-in rows have fixed letter keys:
   * `P` Path `~/bob/bob.md`, which is also **`↵`**, the default;
   * `A` Absolute path;
   * `F` File name `bob.md`;
   * `N` Note name `bob`;
   * `I` Block ID `^id`.

   Parent directory and Relative path are removed. Every row is one keypress;
   `↑↓`/`⌃N⌃P` + `↵` still work, and `esc` closes.
2. **Block ID** comes from the cursor's **owning `#task`** in the active editor's
   live buffer (`findOwningTaskLine` + `getTrailingBlockId`). It is shown under a
   `TASK <title>` caption, never taken from a linked task in another file, and
   snapshotted at open. A task without an ID shows a dim "none · ⌃6 names one".
   The copy gesture never writes to the vault.
3. **Templates** live in `~/.config/bob/config.yml` → `copy.templates` (chezmoi
   `home/dot_config/bob/config.yml`), as an ordered list of
   `{template, label?, key?}`.
   * The language is `{variable}` plus `{{ }}`, single pass. Variables are the
     row labels in snake_case: `{path}`, `{absolute_path}`, `{file_name}`,
     `{note_name}`, and `{block_id}` (bare, so write `^{block_id}`).
   * Keys default to `1–9`.
   * Errors and collisions render as red reasons in the card, never as
     clipboard text.
   * Ship your entry as `- {key: t, label: Task for an agent, template: "the ^{block_id} task in {path}"}`.
4. **Look.** A content-sized card (no dead space) with compact keycaps, one
   aligned monospace value column, no per-row copy icons or pills, the `↵`
   glyph on the highlighted row, a footer that says "copy" instead of "open",
   and a Notice that shows the copied value.
5. **Reliability guards.** Ignore auto-repeat and IME keys, consume every key
   through a catch-all modal scope, keep the command ID so bindings survive,
   and add a test file for the template grammar, task resolution, key
   resolution, and rendering. Then `npm run build && npm test`,
   `bob plugins sync`, and commit plus `chezmoi update -a --force` for the
   config.

---

### Sources

**Code read for this report:**

* bob-plugins `plugins/bob-navigation-hotkeys/src/{010,020,060,070,100,130,180,200,314,320,330,490,640,672}-*.js` and `styles.css`
* bob-plugins `docs/bob-navigation-hotkeys.md` and `docs/block-id-prompt.md`
* bob-plugins `plugins/block-id-prompt/main.js` (`openSelectedBlockIdPrompt`)
* bob-mac-capture `Sources/RefsCore/RefsCopy.swift`
* bob-cli `docs/reference/mac-capture/keyboard.md`, `docs/reference/mac-capture/refs-inspector.md`, and `docs/reference/configuration.md`
* chezmoi `home/dot_config/bob/config.yml`
* vault `~/bob/bob.md:26` (dual `[id::]` / `^id` example)
* Screenshot `~/tmp/screenshots/20261111_092732.png`

**Web:**

* Obsidian API, `Scope.register`: https://docs.obsidian.md/Reference/TypeScript+API/Scope/register
* Obsidian API, `Scope`: https://docs.obsidian.md/Reference/TypeScript+API/Scope
* Obsidian forum, modal-scope key handling: https://forum.obsidian.md/t/suggestmodal-select-w-modifier-key/97652
* JetBrains copy/paste help (Copy Path/Reference): https://www.jetbrains.com/help/phpstorm/2017.3/cutting-copying-and-pasting.html
* JetBrains support thread on the Copy Path popup: https://intellij-support.jetbrains.com/hc/en-us/community/posts/360008218899/comments/360001673339
