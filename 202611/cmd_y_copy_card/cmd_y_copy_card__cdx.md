# Cmd+Y: a compact copy menu with task context and custom formats

Independent research by **cdx**, 2026-11-11. Scope: design and implementation research, not implementation or deployment. No other report, transcript, or finding from this research swarm was consulted.

The proposed feature is a good idea. It improves a frequent, small action and makes the task-plus-file phrase a useful bridge from Obsidian into an agent prompt. The strongest version is a compact action menu: keep exact value previews, remove search, give every valid action a stable single-character shortcut, and keep the home-shortened path as the initial Enter action. Custom formats should be literal text interpolation over a small documented context, not a scripting system.

The main risks are ambiguity about which task is selected, copying a different value from the preview, and silently producing incomplete custom text. These deserve more attention than the template substitution itself.

## Evidence and current behavior

I inspected the supplied screenshot, the actual plugin source, the chezmoi configuration source, and relevant primary web documentation. Source references below identify the inspected revisions so this report remains useful after code moves.

| Source | Revision / location | What it establishes |
| --- | --- | --- |
| S1 | `bob-plugins` at `87b28e1a60ee4aceca1f9f7094ffe06129b81485`; `plugins/bob-navigation-hotkeys/src/490-plugin-lifecycle.js:452` | `copy-active-file-path` opens the picker; its default hotkey is `Mod+Y`. The six standalone yank commands are registered separately from the same command array. |
| S2 | Same repo; `src/010-requires-and-config.js:212`, `src/100-yank-and-paths.js:18`, `src/090-local-task-ids.js:816` under that plugin | Six format definitions, value construction, filename handling, and home-directory shortening. |
| S3 | Same repo; `src/200-filtered-picker-modals.js:1`, `:345`, `:910`; `styles.css:5` | Shared searchable picker, selection and async opening behavior, current copy panel, and fixed modal dimensions. |
| S4 | Same repo; `src/640-plugin-notes-and-task-move.js:3`, `:47`, `:113` | Opening captures a file for previews, but activation asks for the active Markdown file again; clipboard writes are awaited and report success/failure. |
| S5 | Same repo; `src/020-config-load-and-tasks.js:258`, `:434`, `:546`, `:586`; `src/070-recommended-roll-batch.js:444` | Existing trailing-block-ID reader, distinction from Tasks IDs, and a Markdown-aware owning-task resolver. |
| S6 | Same repo; `src/010-requires-and-config.js:534`; `src/020-config-load-and-tasks.js:1`; `src/672-delete-confirm-modal.js:126` | Existing plugin config lookup, config cache precedent, and local modal-scope keyboard registration/cleanup precedent. |
| S7 | `chezmoi` at `7ab303fba1693f62d5d049c941c1a1d0ed488f91`; `home/dot_config/bob/config.yml` | Correct managed source for the proposed user setting. It is a plain YAML source file, not a `.tmpl` file. |
| S8 | `bob-cli` at `f7332f5813c2929c2cd2979a755955cc5cf86074`; `docs/reference/configuration.md` | CLI configuration and plugin settings have separate owners; the CLI does not validate plugin settings. |
| S9 | `/home/bryan/tmp/screenshots/20261111_092732.png` | Current visual presentation and a root-level `bob.md` example. |

Paths beginning `src/` in S2–S6 are relative to `plugins/bob-navigation-hotkeys/`.

The screenshot shows six rows, a search input, repeated Copy badges, and considerable unused vertical space. “Parent directory” previews an empty string for this root-level note; “Relative path” repeats its basename. The first row and actual preview are useful. The large frame is explained by shared CSS: width up to 960px and height `min(82vh, 840px)`. This is a sensible shape for a large file picker, but disproportionate to a handful of copy actions. The footer also says “Open,” although the operation is Copy. [S2, S3, S9]

The command currently works with an active Markdown file. No existing copy-menu custom setting was found in the inspected plugin sources or managed Bob configuration. This proposal therefore introduces a plugin-owned setting; it does not require a new Rust command or a clipboard subprocess. [S1, S4, S7, S8]

### A small executable check

I ran a read-only Node probe through `scripts/navigation-hotkeys-harness.cjs`, using the production plugin prototype and helpers. It confirmed:

```text
Preview basename for a.md: a.md
Change the stub active file to b.md, then call yankActiveFilePath:
Copied value: b.md
Trailing block ID from a task with a different [id:: ...]: foo-bar-baz
[id:: foo] without a trailing block ID: no block ID
Owning task for its indented child note: the parent task
Home-prefix boundary checks: passed
```

The source wires the current modal's callback to exactly that active-file lookup. This establishes a preview/copy consistency risk if the active file changes while the panel is open; it is not a claim that a normal modal keystroke switches tabs. The probe also verifies that the existing helpers already cover important pieces of the desired behavior. No product tests were added or full test suite run for this research-only deliverable. [S3–S5]

## Critique and explicit requirement adjustments

1. **Remove search from this panel.** Unmodified letters cannot simultaneously mean “type a filter” and “copy immediately” without a mode distinction. Four base actions, one contextual action, and a few custom actions do not justify that complexity. Removing search is an intentional change beyond the request.
2. **Keep removed formats available as standalone commands.** Remove Parent directory and Relative path from this menu, but preserve `yank-parent-directory` and `yank-relative-path` for existing bindings. The user requested a panel change, not removal of those capabilities. Split the menu catalog from `YANK_PATH_COMMANDS` instead of deleting array entries globally. [S1, S2]
3. **Interpret Enter as the initially selected default.** On opening, Enter copies Absolute path with tilde. After explicit arrow/Tab navigation, Enter activates the focused row, as users expect. An invariant “Enter always copies the first row even after navigation” would make the selected state misleading. A permanent `t` shortcut still reaches the tilde path from any row.
4. **Make “selected task” precise.** In version one, use a task in the active source/Live Preview editor, including its owned child notes. Do not infer a task from an old cursor in Reading view or from a link to another note. This deliberately bounds the initial context support; broader rendered-dashboard selection can follow once the source target is explicit.
5. **Copy only existing IDs.** Never mint a block ID or normalize `[id::]` just to copy. Keep completed/closed tasks eligible when they have a valid existing ID; copying is not an open-task operation.
6. **Custom actions require a label and an explicit unique key as well as a template.** This is a small addition to the requested string configuration that makes multiple options discoverable and stable. Missing context hides a contextual action; invalid configuration is diagnosed. Neither silently substitutes an empty string.
7. **Define `{task_id}` as the bare block identifier.** Add `{task_block_id}` for the literal `^foo-bar-baz` value shown in the built-in row. This avoids the doubled caret in the user's `^{task_id}` example and avoids confusing a block identifier with Bob's dependency ID.

These adjustments keep the feature small. I would not add a template editor, arbitrary scripts, filters, conditional expressions, automatic IDs, per-task saved preferences, or a generic command-palette framework in this change.

## Recommended interaction and appearance

Use the title **Copy** and a quiet subtitle identifying the active note. When task context exists, add the task's short title and block ID there. Preserve the established Bob accent, spacing, corner radii, and theme variables. Use a content-sized card around 600–680 CSS px wide, constrained to the viewport, with a maximum height around 75vh and scrolling only when needed. The exact width should be tuned in Obsidian with long real paths and the user's font size.

A schematic, not a rendered or tested screenshot:

```text
╭────────────────────────────────────────────────────────────────────╮
│ Copy                                                            ×  │
│ bob.md · Improve the copy panel · ^foo-bar-baz                        │
│                                                                    │
│ Absolute path with tilde                               [t] [Enter]  │
│ ~/bob/bob.md                                                        │
│                                                                    │
│ Absolute path                                                 [a]  │
│ /Users/bbugyi/bob/bob.md                                             │
│                                                                    │
│ Basename                                                      [b]  │
│ bob.md                                                             │
│                                                                    │
│ Basename without extension                                    [n]  │
│ bob                                                                │
│                                                                    │
│ Task block ID                                                 [i]  │
│ ^foo-bar-baz                                                        │
│ ────────────────────────────────────────────────────────────────── │
│ Task context                                                  [c]  │
│ the ^foo-bar-baz task in the ~/bob/bob.md                             │
│                                                                    │
│ Press a key to copy · ↑↓ / Ctrl+N,P move · Enter copy · Esc cancel     │
╰────────────────────────────────────────────────────────────────────╯
```

The first row has the current soft accent fill and a visible focus border. The `[Enter]` hint follows keyboard focus; it is not permanently painted on the default after the user navigates. Keycaps replace repeated “Copy” badges. A subtle divider separates user-defined formats from built-ins. Avoid an icon on every row: the values and shortcuts carry the information.

| Action | Shortcut | Availability |
| --- | --- | --- |
| Absolute path with tilde | `t`; Enter on initial focus | Desktop filesystem path available |
| Absolute path | `a` | Desktop filesystem path available |
| Basename | `b` | Active Markdown file |
| Basename without extension | `n` | Active Markdown file |
| Task block ID | `i` | Exactly one recognized task with an existing block ID |
| Task context, configured below | `c` | Every referenced variable available |

Each shortcut copies immediately and closes only after a successful clipboard write. Clicking a row does the same. Escape closes without copying or changing the note. Preserve arrows and Ctrl+N/P; use actual row buttons with accessible labels and descriptions so Tab/Shift+Tab and Space also work naturally. Focus returns to the invoking editor and its selection remains intact.

Register shortcuts in the modal's scope, active only while the action component owns focus. Normalize letter case using `event.key`; do not depend on physical US keyboard positions. Ignore Meta/Ctrl/Alt combinations other than the explicitly supported navigation controls, composition events, and repeated activation events. Prevent a single gesture from reaching both a scope listener and a DOM listener. Reuse the existing async busy guard so rapid keys cannot cause concurrent writes. Test that Cmd+Y's opening event and held-key repeats do not immediately trigger a menu action. [S3, S6]

The W3C modal pattern supports moving focus into the dialog, containing Tab navigation, Escape dismissal, and restoring focus. Its character-shortcut guidance specifically allows shortcuts scoped to a focused component; global unmodified-letter bindings are inappropriate here. This design should still be tested with VoiceOver rather than treated as accessible merely because it has ARIA attributes. [W2, W3]

Keep previews literal and selectable by assistive technology; labels use normal UI typography, paths and IDs can use a restrained monospace style. Wrap custom text, including multiline templates, and scroll when necessary. For long paths, allow wrapping instead of hiding the distinctive basename. Never truncate the stored clipboard string to match a visual abbreviation. Show an inline failure and retain the menu when copying fails. The existing clipboard method already awaits `writeText`; retain that behavior and its success notice. [S4, W4]

## Task context: exact behavior

Capture the file path, current editor buffer, cursor/selection, and resolved values **before** opening the modal. Do not read the cursor after modal focus takes over, and do not use a stale metadata-cache block list in preference to unsaved editor text.

For an empty selection, resolve the current line's owning task with the existing Markdown-aware helper. A cursor on a task's indented note therefore selects that task. For a nonempty selection, require one contiguous selection whose touched content belongs to exactly one task; respect an exclusive end at column zero so it does not accidentally include the following task. Multiple task owners, multiple cursors, non-task content, fenced examples, or ambiguous ownership mean no task context. Do not quietly pick the first match. [S5]

Extract the actual trailing ID with `getTrailingBlockId`. Obsidian documents block identifiers as Latin letters, digits, and dashes, and uses a caret before the identifier; the helper follows that convention. Use Bob's existing task recognition rather than a new regex for checkboxes. Do not use dependency identity routines that return proposed target edits or path-qualified `[id::]` values. [S5, W1]

Keep the meaning of file variables fixed: they describe the active note. Consequently, a `[[different-note#^id]]` under the cursor is not sufficient to expose that other task's ID. Combining that ID with the active file's path would create a confidently wrong custom phrase. Similarly, an embedded task or a rendered dashboard row is file-only in version one unless a future explicit source-aware contract covers it. This is a correctness boundary, not a reason to block the ordinary copy panel.

When no task is available, omit Task block ID and task-dependent custom rows. Keep keys reserved independently of visibility: `c` must not start copying a different format merely because `i` disappeared. If the cursor is on a recognized task without an ID, a small optional line such as “This task has no block ID” explains the missing task actions without adding another action.

Treat the menu as a snapshot: copy the exact string already previewed, even if the editor focus or content changes elsewhere. Reopening refreshes it. That is sufficient for a read-only clipboard operation and avoids a live-context watcher or silent retargeting. The snapshot can become old, but it cannot say one thing while copying another. Copying must not create an undo entry, change freshness, or write task fields.

## Custom configuration and interpolation contract

Add this plugin-owned section to the existing Bob configuration, implemented in `bob-navigation-hotkeys`:

```yaml
copy_menu:
  custom:
    - label: Task context
      key: c
      template: 'the ^{task_id} task in the {abs_file_with_tilde}'
```

The implementation change should place that stanza in **chezmoi's `home/dot_config/bob/config.yml`**. Its deployed destination is `~/.config/bob/config.yml`. This research does not edit the configuration before a consumer for the setting exists. The sample yields exactly:

```text
the ^foo-bar-baz task in the ~/bob/bob.md
```

Use the existing plugin configuration lookup, which honors `XDG_CONFIG_HOME` and otherwise uses the home `.config` directory. Do not claim it already supports the CLI's `BOB_CONFIG_FILE` override: the inspected plugin helper does not. Addressing that wider inconsistency is unnecessary for this feature. Read the small config on each menu opening, or use a well-tested invalidation cache; freeze the result while the menu is open. Missing file/section means no custom rows. [S6–S8]

Expose only these initial variables:

| Variable | Example value | Contract |
| --- | --- | --- |
| `{abs_file_with_tilde}` | `~/bob/bob.md` | Exactly the first built-in action's value |
| `{abs_file}` | `/Users/bbugyi/bob/bob.md` | Exactly the absolute-path action's value |
| `{basename}` | `bob.md` | Filename with final extension |
| `{basename_no_extension}` | `bob` | Filename with final extension removed |
| `{task_block_id}` | `^foo-bar-baz` | Exactly the Task block ID action's value |
| `{task_id}` | `foo-bar-baz` | Explicit convenience value without caret; never `[id::]` |

An equally valid template is `the {task_block_id} task in the {abs_file_with_tilde}`. Document both and configure the requested spelling. Removed menu formats need not become template variables in version one.

Use a tiny tokenizer and an explicit variable map, not `eval`, JavaScript template literals, a shell, or an extensible template engine. Requirements:

- Scan the template once into literal and variable tokens; insert each value literally and do not scan inserted values again. A file containing `{task_id}` in its name must remain that filename.
- Allow `{{` and `}}` for literal braces. Unknown names, unmatched braces, and unsupported expressions are configuration errors. Variable names are case-sensitive.
- Preserve whitespace and newlines in the string value; YAML `|-` can express a multiline format without a final newline. Reject empty/whitespace-only formats and NUL characters. Do not silently strip or append text.
- Missing runtime values are different from syntax errors. If `{task_id}` has no value, hide that contextual row; never emit `undefined`, an empty gap, or an unexpanded token. Likewise, a format requiring an unavailable absolute path is unavailable.
- Require nonempty single-line labels, string templates, and one explicit key from `a-z` or `0-9`. Normalize the key to lowercase. Reserve `t`, `a`, `b`, `n`, and `i`, including when their rows are unavailable. Validate against all custom entries, including currently hidden ones.
- Reject conflicting custom keys rather than silently reassigning them. Reject all entries participating in a custom-key collision; leave unrelated valid entries and built-ins usable. Invalid YAML or a malformed `custom` list disables that custom section, not the menu.
- Show a concise, accessible configuration diagnostic with the offending entry/key/variable and source path. Do not issue a notice on every keypress or silently fall back to a prior configuration.

This key domain permits at most 31 custom keys after the five built-ins. That is a transparent consequence of guaranteeing a single key for every action, not an unlimited-list promise. There is no need for an arbitrary smaller hard cap; long menus can scroll, but documentation should encourage a few frequently used formats.

Values are plain text, not shell-escaped or Markdown-escaped. The requested phrase is excellent local context, but it is not an executable shell command, an Obsidian link, or a cross-machine identifier. Home shortening applies only at a real home-directory boundary; outside the home directory, the tilde option retains the absolute path. Keep the existing path helper and test that behavior. A `~` path also depends on the receiving machine's home and vault layout. These are reasons to preview exactly what will be copied, not reasons to add URI, quoting, and link-format variants now. [S2]

## Implementation shape and validation

Prefer a small dedicated `CopyMenuModal extends Modal` that reuses Bob's visual tokens and path helpers. The existing `FilteredPickerModal` assumes a search input in focus, uses listbox semantics, and serves many unrelated panels. A separate action view is easier to reason about than hiding its input and intercepting its filter keys. Keep the command ID `copy-active-file-path` and the existing Mod+Y binding so user hotkeys survive; its user-facing name can become “Copy file or task context.” [S1, S3]

A practical separation is:

1. **Context resolver:** snapshots the active file/editor and optionally one task, producing values or explicit unavailable reasons.
2. **Format model:** creates four built-ins, the conditional block-ID row, validated custom rows, and diagnostics. Each action contains its shortcut, label, and exact output string.
3. **Menu view:** renders that immutable model and dispatches a key, click, or Enter to one copy function. It never recomputes the active target during activation.
4. **Clipboard adapter:** preserves the existing awaited write and failure handling. Standalone yank commands can keep their current immediate active-file lookup.

Suggested touch points are the source fragments in S1–S6, the fragment manifest if adding files, a scoped `bob-copy-menu-*` CSS class, focused Node tests using the existing harnesses, plugin documentation, and the single chezmoi stanza. Do not hand-edit generated `main.js`: build it from committed fragments. Keep each source fragment within the repository's 1,000-line limit; the current filtered-picker fragment is already about 960 lines. Avoid a shared-picker redesign merely to save a small amount of view code.

Tests should verify contracts rather than just repeat the implementation:

| Area | Required checks |
| --- | --- |
| Default and keys | Open → Enter copies tilde path; each direct key executes once; navigation changes Enter target; Escape never writes; hidden rows do not remap keys. |
| Preview consistency | Open on A, change the active-file stub to B, activate: clipboard still receives A's preview. Also change the original file object's path to prove the path was copied as a string. |
| Task resolution | Cursor on task and child note; closed task; missing ID; legacy `[id::]` only; selection spanning two tasks; reversed selection; exclusive line-end boundary; multiple cursors; fenced code; links/embeds; Reading view. |
| Templates | Requested example; both ID spellings; repeated variables; escaped braces; literal inserted braces and `$` characters; multiline text; Unicode paths; unknown variables; missing runtime values; malformed YAML; duplicate/reserved keys. |
| Paths | Nested paths; multiple dots; spaces; home-prefix lookalike; outside-home vault; existing Windows normalization behavior; unavailable base path. |
| Clipboard/lifecycle | Permission failure stays open; repeat/composition guards; no double dispatch; opening Cmd+Y does not activate a row; focus and cursor restore; no vault writes or undo entries. |
| Appearance | Light/dark themes, large font, narrow window, long path/template, no task, several custom rows, error diagnostic, VoiceOver/keyboard operation. |
| Compatibility | Standalone relative/parent commands still exist; existing bindings resolve; unrelated filtered pickers retain their layout and behavior. |

Desktop is the primary target. If an adapter cannot provide an absolute path, keep those rows visibly unavailable, with an explanation, rather than copying a relative substitute under an absolute label. On that runtime only, initial focus may move to the first available action. Host-local custom configuration remains unavailable where the existing filesystem loader is unavailable. Neither case justifies a fake successful default.

During implementation, run focused tests, `npm run build`, `npm run build:check`, the applicable plugin suite/validation, and documentation checks. Regenerate the command inventory if changing displayed command names. Verify the actual modal in Obsidian: the Node harness cannot establish macOS focus behavior, real clipboard permissions, VoiceOver output, or visual polish. The repository requires `bob plugins sync` after changes; coordinate deployment with its protection against overwriting another checkout. Apply the chezmoi configuration through that repository's established post-commit workflow. No Mac Capture changes or CLI release are intrinsically needed.

## Alternatives considered

| Approach | Benefit | Why I would choose differently |
| --- | --- | --- |
| Keep search; use digit accelerators | Smaller modification to the existing picker | Digits are legitimate filter input, custom rows create numbering/visibility questions, and the oversized search UI remains. |
| Search mode entered with `/` | Handles a much larger format list | Adds modes and shortcut rules to a menu whose useful size is small. Revisit only if actual usage demands it. |
| Per-action global hotkeys | Fastest for memorized actions | Uses more global combinations and loses previews/discoverability. Existing standalone commands already cover much of this. |
| Native platform menu | Familiar, compact interaction | Exact two-line previews and consistently visible immediate-action keys are central here; the existing custom-modal foundation is already available. |
| Automatic letter assignment | Less configuration | Labels, order changes, or hidden task rows can alter muscle memory. Explicit keys are a better tradeoff. |
| Full template engine | More expressive | Introduces escaping, execution, dependencies, and error cases that the requested task/file phrase does not need. |
| Follow every task link or embed immediately | Broad reach from dashboards | Risks mixing the host file's path with a linked task's ID. Requires a separate, explicit target contract. |

## External sources and limits

- **W1:** [Obsidian: Internal links](https://obsidian.md/help/links), especially block references. Supports the caret syntax, identifier alphabet, and the fact that Obsidian block links are not standard Markdown.
- **W2:** [W3C APG: Modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/). Supports focus entry/containment/return and Escape behavior.
- **W3:** [W3C: Understanding character key shortcuts](https://www.w3.org/WAI/WCAG22/Understanding/character-key-shortcuts.html). Supports the focus-scoped shortcut constraint.
- **W4:** [MDN: Clipboard.writeText](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText). Supports awaited success and rejected-write handling.

External sources were consulted on 2026-11-11. Obsidian developer-documentation URLs for Modal and Scope were not successfully readable through the browser tool; this report therefore bases its API integration recommendation on the inspected plugin's working patterns, not an unverified upstream API claim. The screenshot was visually inspected, but no interactive Obsidian session or polished prototype was tested. Dimensions and key mnemonics are design recommendations, not measured usability results.

## Recommended solution

Build a compact, search-free **Copy** menu in `bob-navigation-hotkeys`, retaining the command ID and Cmd+Y binding. Keep the four requested file formats with stable `t/a/b/n` keys, add `i` for an existing selected task's `^block-id`, and focus the tilde-path row initially so Enter preserves the current fast path. Add validated `copy_menu.custom` entries with explicit labels, unique keys, and literal variable substitution; configure `c` as “Task context” using `the ^{task_id} task in the {abs_file_with_tilde}` in chezmoi. Resolve one local task from the current editor before opening, freeze every previewed output, and copy those exact bytes. Preserve removed formats as standalone commands. This delivers the requested speed and composability with a smaller, clearer panel and a deliberately narrow reliability contract.
