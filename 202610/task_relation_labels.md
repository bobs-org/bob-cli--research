# How to create a task relation with a label

Research date: 2026-10-20. Context: epic `bob-cli-a2` (task relations: `🪢 LINKS`,
the generated `🪢 LINKED FROM` mirror, and `~` / `~~` capture). All 15 phases are
closed. The capture examples below were run against the installed `bob` in a
throwaway vault.

## Short answer

Add `|label` after the relation token. Quote any label that contains a space:

```bash
bob capture 'Fix flaky retries ~sase:retry-design|see'              # one word
bob capture 'Fix flaky retries ~sase:retry-design|"follow-up of"'   # several words, quoted
```

Result on disk (verified):

```markdown
<!-- mac_inbox.md: the source task. The label is stored here. -->
- [ ] #task Fix flaky retries [created::2026-10-20] ^fix-flaky-retries
	- 🪢 **LINKS:** follow-up of [[sase#^retry-design]]

<!-- sase.md: the target task. Bob generates this line. -->
- [ ] #task Design a retry policy ^retry-design
	- 🪢 **LINKED FROM:** [[mac_inbox#^fix-flaky-retries]] (follow-up of)
```

The label reads as a sentence from the **source's** side: "S ‹label› T".

## The four ways to add a labelled relation

| Where | How |
| --- | --- |
| **`bob capture` (CLI)** | `~note:id\|label` means the new task links to `note:id`. `~~note:id\|label` means `note:id` links to the new task. `@route+id ~note:id\|label` relates two tasks that already exist, without creating a task. |
| **Bob Mac Capture** | Type `~` to open the task picker; type a second `~` to switch direction. Press `⇧↩` on a row, or type `\|` after an accepted token. This opens the **Relation card**: a text field with label suggestions, a live `S — label → T` sentence, and `↩` to insert. |
| **Obsidian Task Card** | `Ctrl+Shift+P`, then `l` (**Links to…**), or `Ctrl+Shift+L` directly. Select a task, then press `⇧↵` to open the **relation field**: type a label (suggestion chips are offered) and press `↵`. Plain `↵` links without a label. `⇧L` (**Linked from…**) works the same way in the reverse direction. |
| **Hand edit** | Add a direct child line under the source task: `- 🪢 **LINKS:** merged into [[sase#^retry-design]]`. Separate entries with ` • `. The next `bob task reconcile` writes the target's `LINKED FROM` line (verified). |

Examples of each capture form (verified with `--dry-run`):

```text
Fix flaky retries ~sase:retry-design|"follow-up of"        → 🪢 would link to "Design a retry policy" · follow-up of
Write the migration note ~~sase:retry-design|"migration note for"
                                                           → 🪢 "Write the migration note" would now link here · migration note for
@bob+fix-retries ~sase:retry-design|see                    → 🪢 would link to "Design a retry policy" · see
```

In `~~`, the named task is the **source**, so read the label from its side:
"retry-design — migration note for → Write the migration note".

## Label rules

- 1–40 characters. Bob trims the label, collapses runs of whitespace, and
  strips one trailing `:`. Case is preserved.
- A label may not contain `[ ] ( ) " \ | • * ~` or control characters. It may
  not start with `·` or `,`. For example, `|"has (parens)"` is rejected with
  `invalid_relation`.
- A trailing `|` with no label is incomplete (`relation_label`); the pickers
  show suggestions at that point.
- **Relabel:** link the same target again with a different label. Bob replaces
  the label in place and capture prints `🪢 relabeled`. In the Links stage,
  `⇧↵` on a CURRENT row relabels it.
- The target needs a `^block-id`. The pickers offer to create one (`＋ id`).
- **Built-in inverse wording (display only):** on the target's `LINKED FROM`
  chip, five known labels are shown reversed. The stored text stays
  `(follow-up of)`.

  | Stored label | Shown as |
  | --- | --- |
  | `merged into` | `merged from` |
  | `duplicate of` | `duplicated by` |
  | `follow-up of` | `followed up by` |
  | `superseded by` | `supersedes` |
  | `split from` | `split into` |

Relations are inert. They never block a task, change its status, lane, or
schedule, or count as Pomodoro Task Links. If one task must finish before
another, use `&` (depends on) or `*` (blocks) instead.

## Gotcha: one shipped guide example is wrong

`docs/guides/link-related-tasks.md` shows unquoted multi-word labels:

```bash
bob capture 'Investigate retry handling ~service:retry-loop|follow-up of'   # WRONG
bob capture '@bob+retry-investigation ~service:retry-loop|related to'       # WRONG
```

`bob capture-parse` shows that neither creates a relation. A relation token is
only recognised when it is in the trailing run of modifiers, and the extra word
(`of`, `to`) breaks that run. The first draft becomes plain task text containing
`~service:…|follow-up of`. The second is parsed as a sub-bullet whose body is
`to`. Use `|"follow-up of"` and `|"related to"`.

Also, the `bob capture-parse --help` text (`src/native/capture_parse.rs:366`)
still says that `bob capture` "currently refuses any item with relations". That
is out of date: execution shipped in `8755ffc8` and works.

## Sources

- `docs/guides/link-related-tasks.md`, `docs/capture.md#linking-tasks`,
  `docs/reference/capture-syntax.md#tilde-link`
- `docs/task-relations.md` §3.2 (labels), §4 (relabel), §10 (inverse phrases)
- `docs/reference/plugins/task-relations.md` (Links stage and relation field)
- `plan:202610/task_relations.md` (Mac Capture relation card, phase `mac-preview`)
- Live checks: `bob capture-parse`, `bob capture -d`, `bob capture`, and
  `bob task reconcile` in a temporary vault
