# Task theme defaults that explain themselves and remember deliberate choices

Independent research by **cdx**, 2026-10-28.

**Recommendation:** build this feature using deterministic defaults, visible provenance, and task-local exceptions. The crucial adjustment is to distinguish **a task's preferred theme** from **the Pomodoro chosen for this occasion**. They often agree, but treating them as identical would create surprising permanent overrides.

## Scope and evidence

This is research, not an implementation. No product code, vault notes, configuration, or theme journals were changed. No peer report, peer transcript, or peer findings were consulted.

I inspected these local repository snapshots:

| Repository | Inspected commit |
| --- | --- |
| bob-cli | `50f6c91bc03029dc8cf0e449d8380c107d2183ff` |
| bob-plugins | `8baf76398048612cc0ed1c7b7b03537c87056b3b` |
| bob-mac-capture | `88757e97c4d761e4fbbf4829c1ed6badb7db36af` |

I read applicable SASE glossary/decisions through audited memory reads, checked the seed notes with read-only `bob query`, and consulted primary Obsidian/Dataview documentation and Nielsen Norman Group guidance. Sources appear before the final recommendation. Current behavior below is based on source inspection; proposed behavior is a recommendation. I did not compile the clients, run their product tests, benchmark performance, or validate a visual prototype inside Obsidian.

The seed query confirmed:

| Exact vault path | Current type | Current parent | Existing theme | Proposed value |
| --- | --- | --- | --- | --- |
| `dev.md` | area | `[[area]]` | absent | `BUILD` |
| `love.md` | area | `[[area]]` | absent | `CHORE` |
| `job.md` | area | `[[area]]` | absent | `WRITE` |
| `sase_blog.md` | project | `[[sase]]` | absent | `WRITE` |

Generated tag pages also share some of these basenames. Seed by **exact vault-relative path**, verifying type before writing. The query emitted unrelated ambiguous-link warnings; none changed these four returned rows. I did not audit the complete parent chain of `sase.md` or measure how well each proposed theme fits its task population.

## Assessment: worthwhile, with boundaries

The proposal replaces repeated classification with a few understandable rules. BUILD, CHORE, WRITE, and READ describe modes of work, while the hierarchy describes where work belongs. A reading task can belong to dev but suggest READ; a writing project can override a broader BUILD area.

This needs no training period, embeddings, confidence score, or task-text classifier. A person can explain every result by inspecting a task and its note ancestry. I would not introduce semantic task-text inference in v1.

The main risks are behavioral:

- Putting a writing task into today's running BUILD session can be a scheduling convenience, not a permanent preference.
- A suggested WRITE choice might create a new planned Pomodoro. The selected row must say that before Enter.
- Copying defaults into every task freezes inheritance and hides provenance.
- `BUILD + WRITE` is a Pomodoro name containing two themes, not one valid scalar task theme.
- Reference follow-up tasks are not necessarily reading tasks; legacy reading tasks may lack modern tags.
- Preferences must never rewrite historic Pomodoros, time accounting, or Stats. The ledger remains the record of what happened.

The four seeds are reasonable starting defaults, not proof that every job task is writing or every love task is a chore. If exceptions become frequent, revisit the note's default instead of compensating with a complicated classifier.

## Findings in the existing implementation

**Existing theme semantics are a good foundation.** A theme is one `+`-separated component keyed by `normalize_component`. History comes from canonical daily notes; hiding affects Recent only. Hue resolves from pin, exemption, matching top-level area, then hash. Pills use a tinted background and normal text; dense rows use rounded square swatches, distinct from area dots. Reuse these rules. [C1]

**The menus have separate adapters.** Rust's `capture_complete/theme_menu.rs` composes Today, Recent, create, substring, and utility rows. `pomodoro_candidates` currently receives query/start/literal flags, without task identity. `capture_complete/engine.rs` has parsed item context that can supply it. Obsidian's Link to today picker lives in `block-id-prompt`, consuming Ledger Tools' `api.themes`; its request currently supplies task display text/status rather than resolved theme context. [C2, C3]

**The keymap example needs correction, not rebinding.** Current documentation binds Link to today to **Ctrl+Shift+Enter**. Ctrl+Enter completes tasks/Pomodoros and can trigger successor offers. Cover task-link gestures, including explicit per-task successor destination selection, without changing those bindings. [C3, C4]

**Obsidian persistence is the most important implementation trap.** Rust's existing-task link wrapper uses `CaptureBatchPlanner` and `commit_capture_batch`. Obsidian's `applyPomodoroTaskLink` reads live editor text and checks snapshots, but its separate-note branch applies the task first and the daily note second. It explicitly reports partial failure if the second write fails. Adding a theme field to the first write can therefore remember a choice whose link never succeeded. [C5]

**Reference recognition must be deliberate.** `note_tasks::is_ref_task_kind` recognizes the global task filter immediately followed by `#ref`. The reference subsystem also has `RefTaskIndex`, v2 selection, and legacy tracker handling. A new check for a filename under `ref/`, any link to a reference, or merely a `^ref-` prefix would be insufficient. Reading tasks normally reside in area/project notes, and their block IDs can survive reference renames. [C6]

**Parent traversal is reusable, but its predicates are not universal.** `project_dependencies/tree.rs` provides source-relative link resolution, cycle guards, and a depth bound of 16. Its project-only ancestor helper stops at a non-project. Theme inheritance needs areas too; reuse mechanics without copying that stopping rule. [C7]

**Dataview exposes page fields on tasks.** A truthy `task.theme` in a query result is not proof that the task has an authored inline override. Read the physical task line for explicit metadata and frontmatter separately for defaults. Dataview documents this inheritance behavior. [E2]

**Rename currently stops at ledger names.** Its scope explicitly excludes task text. Defaults and task fields require an intentional extension to that contract; otherwise renamed themes will reappear through suggestions. [C8]

## Recommended data model and precedence

Use the requested property names with complete syntax:

```yaml
---
type: "[[project]]"
parent: "[[dev]]"
theme: WRITE
---
```

```markdown
- [ ] #task Draft the announcement [theme:: WRITE] ^announcement
```

Normalize the prompt's `[theme::<theme]` to **`[theme:: WRITE]`**. YAML uses a scalar Text property; tasks use a bracketed Dataview field. Obsidian and Dataview support these basic representations. There is no need for theme notes, a tag, a nested YAML object, or another preference store. [E1, E2]

Each declaration holds **one nonempty theme component**. Reject composites, lists, maps, booleans, and malformed bracket syntax as declarations. Reuse existing single-theme validation and normalization, additionally rejecting delimiters that cannot round-trip through a bracketed field. Compare normalized keys, not selector slugs. Reuse the catalog spelling for known names and existing Bob name canonicalization for new values.

In v1, missing/null/blank note values mean inherit; a missing task field means use the default. Do not introduce special `false`, `none`, or `-` values to stop inheritance. A subtree-level opt-out can follow evidence of need.

A note's field applies to its resident tasks, including `^prj`, and descendants without a nearer declaration. Sub-areas participate. No separate local-only/sub-project-only mode is needed initially. Task indentation introduces no additional inheritance: an inline override on a parent task applies to that task alone.

| Priority | Rule | Visible reason |
| --- | --- | --- |
| 1 | Explicit valid inline field on the task | Saved for this task |
| 2 | Recognized source reading task | Reading task |
| 3 | Theme on its resident area/project | From sase_blog |
| 4 | Theme on the nearest ancestor area/project | From dev · via sase |
| 5 | No inferred theme | Existing current/next destination behavior |

The reference fallback is **READ**. An explicit task override beats READ: the user asked for a reading default and an explicit override, not a mandatory reading category. A task involving implementation of a book's exercises might legitimately prefer BUILD.

Use the task's actual residence, not the active pane, a daily-note Task Link, reference embed, filesystem directory, or vaguely matching basename. For an inbox task being filed during the same gesture, resolve against its proposed final residence. The current route/picker sequencing needs attention: either choose the route first or visibly recompute and reconfirm before writing. Never persist a comparison against an obsolete inbox default.

Traverse resolved scalar `parent` links through typed areas/projects only. Stop at a missing/ambiguous parent, a non-area/project note, the ontology boundary, a cycle, or the depth limit. Track canonical paths. A valid nearer declaration already found remains valid even if a higher link is broken.

Invalid declarations should not silently win. Completion should show one compact diagnostic, retain a usable destination fallback, and suppress automatic remembering for the unresolved case. Conflicting duplicate inline fields need repair rather than accidental first/last-match semantics. An explicit repair operation may replace the invalid field.

| Example | Result |
| --- | --- |
| Ordinary task in dev | BUILD, from dev; no field written |
| Task in a dev-descended project without a theme | BUILD, with ancestor provenance |
| Task in sase_blog | WRITE, from sase_blog |
| Reading task in dev | READ |
| Reading task with `[theme:: BUILD]` | BUILD, saved for this task |
| Ordinary annotation follow-up in dev | BUILD; reference origin alone does not imply READ |
| Task moved from BUILD area to WRITE project, no override | WRITE at next lookup |
| Same move with saved CHORE | CHORE remains |
| Saved WRITE later equals its project's new default | Preserve explicit field until Use default |

Do not backfill inherited values into tasks. Note changes should take effect at the next lookup, without a mass rewrite. Rollover must preserve existing task identity/fields, never stamp the carried Pomodoro's name onto the task.

## Menu and visual design

### Separate the recommendation from the executable destination

A recommendation says **WRITE, from sase_blog**. A candidate says **link into today's WRITE Pomodoro** or **create a planned WRITE Pomodoro**. Both are needed; a colored theme label alone does not describe the action.

For an empty-query task-specific menu, present one compact Suggested row and preselect it. Promote an existing matching candidate when possible, removing its duplicate from Today/Recent. Keep remaining Today rows in ledger order and existing Recent ranking intact. Do not invent historical usage for a theme merely mentioned in frontmatter.

Conceptual layout, rendered with the existing pills/swatches:

```text
Link to today
Draft the release announcement

Suggested
› ■ WRITE                         New Pomodoro
  From sase_blog

Today
  ■ BUILD                         Running · 09:20–09:45
  ■ CHORE                         Planned · 2 tasks

Recent
  ■ READ                          Oct 27 · 4 days

Enter: link and create WRITE                 Esc: cancel
```

If WRITE exists, show its real state/time/task count. For a reading task use Reading task; for an override use Saved for this task. A detail affordance can show the full inheritance chain and jump to its source, but the basic reason must be visible without hover.

Map the recommendation to a destination in this order:

1. Eligible open **single-theme** entry with the same normalized key: running match first, otherwise first matching entry in ledger order.
2. Otherwise, eligible open **composite containing** that component: running match first, otherwise ledger order. Show its full name and Includes WRITE, not a misleading WRITE-only label.
3. Otherwise, create a planned singleton using existing placement rules. A completed-only name uses existing “again” behavior.
4. Retain all eligibility and budget checks. If unavailable, show the reason and select a valid existing fallback. Do not bypass a cap/blockage or learn from that fallback.

This favors reuse over fragmentation. If composite reuse proves undesirable, swapping steps 2 and 3 is a small policy adjustment with no storage redesign.

Only task-aware menus get this default. Bare start/name menus retain current behavior. Existing no-name CLI capture and `bob ref today` keep documented current/next semantics; UI acceptance supplies an explicit chosen destination. Do not silently change what existing command strings mean. The current Ref Today response already distinguishes implicit default targeting from explicit name or stale-safe row targeting. [C9]

### Query intent and stable selection

Once the query is nonempty, typing wins. Do not pin a nonmatching suggestion or fill the input with the inferred name. Matching rows may retain their reasons while respecting explicit exact matches and normal filtering.

Preserve selection by candidate identity after navigation/typing. The Obsidian picker currently rebuilds its selected index during `updateQuery`; another asynchronous result must not move the highlighted action just before Enter. Use stable entry identities or normalized create-row keys, generation-tag responses, and discard stale requests. Material changes to the selected task/default require a visible refresh and another acceptance, not silent retargeting.

Reuse Bob's lossless exact-name replacements: suggesting BUILD must not accidentally prefix-select BUILD TOOLS. The current completion layer already handles literal replacements when slugs cannot faithfully identify the displayed name. [C2]

### Concise authored metadata

Render `[theme:: WRITE]` as a small **WRITE** pill: existing 4 px corners, 16% light/24% dark tint, normal text, no border, and the same hue as the ledger theme. Avoid an area dot, novelty emoji, or independent hue calculation. The text carries meaning even with color disabled. [C1]

Keep the pill at the authored field location; managed insertion belongs consistently before the terminal block ID without reformatting the task. Reveal editable syntax when the Live Preview selection enters the field; Source mode always shows the actual Markdown. Reading view, embeds, task cards, and query results should share the presentation when the physical override can be identified safely. Avoid double-decorating Dataview output.

Use Ledger Tools' existing CodeMirror/Markdown postprocessor patterns and check popout documents. Skip fences, code spans, escaped examples, and unrelated prose. Do not globally hide all inline `theme` text with CSS: that would obscure malformed values and hurt editing. [C10]

Accessible label: `Task theme: WRITE. Saved override.` A task-card Theme row shows the effective theme and provenance even when no inline field exists, with **Choose theme** and **Use default — BUILD from dev** actions. Ordinary task rows show authored overrides only; adding an inherited pill to every task would create clutter and blur stored versus computed state.

## Automatic remembering without accidental permanent decisions

Honor the convenience: deliberately selecting a different **single theme** while linking remembers it by default, without a second confirmation dialog. Before accepting, show a compact control in the existing picker:

```text
Theme for this task: CHORE       [✓ Remember for this task]
Next time: CHORE · suggested BUILD came from dev
```

Unchecking Remember means only this time. Use a visible control rather than a hidden modifier. In particular, Shift+Enter is already assigned to a new-name creation intent in this picker. [C3]

After success, show `Linked to CHORE · remembered for this task` with **Undo theme change**. That action restores the exact previous field state and leaves the link in place; its name avoids promising a full link rollback. A separate full-gesture undo can be added if the transaction layer supports it. Permanent reset remains in the task card. Visible feedback and reversibility follow established usability guidance; this exact interface has not been user-tested. [E3, E4]

| Event | Preference effect |
| --- | --- |
| Accept the effective suggestion | No write; preserve any explicit override |
| Deliberately choose another singleton, Remember on | Set/replace exactly one task field |
| Same selection, Remember off | Leave prior field state unchanged |
| Choose Use default | Remove the override and preview the resulting default |
| Browse/filter/highlight/cancel/dry-run | No write |
| Implicitly accept current/next with no inferred suggestion | No automatic override |
| No suggestion, but deliberately choose a singleton | Offer Remember on, explaining the new preference |
| Composite containing the effective theme | Do not infer an override from its other components |
| Composite without the effective theme | Link once; optionally choose which component to remember |
| Unnamed destination | No new override; preserve existing preference |
| Rollover/reconciliation/cleanup/inherited successor placement | No learning |
| Guarded or failed action that does not link this task | No preference write |

For a nonmatching composite, the control may offer BUILD, WRITE, or Only this time, with the latter selected initially. Never choose the first component arbitrarily or store `BUILD + WRITE` as a scalar theme.

If a saved override differs from the inherited default and the user chooses the inherited value, normal Remember may explicitly pin that value. **Use default** is the unambiguous way to resume inheritance. Never delete a manually authored override just because it happens to equal the current default.

An accepted choice needs a structured record: stable task identity, chosen component, mode (`remember`, `once`, `use_default`), and preview snapshots. Destination text alone cannot distinguish deliberate preference intent from inferred or inherited placement.

For multiple tasks, do not majority-vote a theme or stamp a global destination onto every task. A shared recommendation is appropriate only if all resolved tasks agree; otherwise show Mixed and retain the batch's existing placement flow. Persistence requires per-task selection or an explicit bulk Remember action. Existing successor offers stay opt-in; this feature must not preselect successor tasks.

## Implementation shape and reliability

### One semantic contract with adapters for existing clients

Add a small Rust `task_themes` domain module: parse local fields, resolve a recommendation from supplied snapshots, map it to candidate destinations, and plan minimal edits from accepted choices. Keep scanning, UI, and mutation separate from those pure functions.

An illustrative **proposed**, additive response shape:

```json
{
  "theme_suggestion": {
    "key": "write",
    "name": "WRITE",
    "source": {
      "kind": "ancestor",
      "path": "sase_blog.md",
      "chain": ["article_project.md", "sase_blog.md"]
    },
    "base": { "key": "write", "name": "WRITE" }
  },
  "initial_candidate_id": "existing:41:0b1c2d3e"
}
```

For a saved override, source kind becomes `task_override`; base still identifies what clearing the field would reveal. Carry existing ThemeRef/hue data rather than inventing color logic. Candidates can carry a short explanation and proposed field effect.

Do not overload `origin: history`, which describes catalog provenance, or existing `default`/`next_up` fields used for no-name semantics. Keep schema-1 changes additive, unknown optional fields harmless, and write-intent support capability-gated.

Capture can derive context from the parsed item at the cursor, its final route, and selected task identity. New-task drafts can resolve their destination note's default before creation. Unfinished/ambiguous task selection must not borrow an arbitrary candidate's theme. A global field spanning disagreeing items has no single task recommendation.

Pass accepted preference intent as structured **per-item metadata** to the existing capture/write protocol and include it in dry-run preview. The exact option spelling belongs in normal CLI design review; do not invent another `capture-*` sibling or nest a subcommand beneath free-text `bob capture`. Replacement text alone cannot represent both one-time and remembered acceptance of the same destination.

Mac Capture remains a thin client: extend models, completion presentation, and the Refs Today card; send choice intent to Bob. Swift must not parse frontmatter or traverse parents. When the installed Bob cannot persist a preference, disable Remember with a concise explanation rather than claiming it was saved. [C11]

Obsidian needs unsaved editor state. Its existing theme subsystem already uses pure mirrors and shared vectors; a similarly bounded resolver/field-edit mirror in Ledger Tools is a practical fit. Expose one versioned API for Block ID Prompt, navigation, and task cards. Rust owns the specification; a byte-identical fixture corpus checks Rust and JS against identical inputs/results. Do not build one interpretation per plugin. If using a Bob subprocess instead, supply editor snapshots; disk-only resolution is not equivalent.

### Treat link and preference as one operation

In Rust, stage the field and link in the same capture batch. Revalidate task identity, relevant source/default snapshots, destination, and final route before commit. Failed items or budget checks must leave neither half written. Dry-run runs the same planner; repeating a request must not append another field.

In Obsidian, extend the planner/coordinator rather than attaching a detached post-modal callback. Same-note changes should be one editor transaction. Separate-note writes need staged preimage checks and conditional rollback of this gesture's writes, or a transaction service that preserves live buffers. Re-read before rollback and never overwrite an intervening human edit. If rollback is unsafe, report partial failure and never show a false remembered-success notice.

This is a release requirement for auto-persistence. Recommendation-only behavior can ship as an explicit intermediate stage while the coordinator is built; it is not the complete requested feature. Writing the task field first and hoping the link succeeds is insufficient.

Compare against the suggestion in the confirmed preview, not a different one recomputed after an asynchronous hierarchy change. Refresh and obtain another acceptance when inputs materially change. Use stable task identity plus snapshots, not stale line numbers. Preserve block IDs, other fields, comments, indentation, and line endings.

### Performance and cache correctness

Do not build a vault-wide `RefTaskIndex` on every keystroke. Reuse indexed reference identity and bounded parent traversal. Cache parsed metadata by revision/fingerprint and track every ancestor dependency. Invalidate on task edits/moves, note theme/type/parent changes, rename/delete, reference identity changes, and fallback configuration changes. Open edited buffers take precedence over Obsidian's metadata cache.

The existing theme contract targets no more than +5 ms warm p95 completion overhead on apollo. Measure the resolver and end-to-end menu against a baseline; the target is not evidence this implementation will meet it. Default resolution must work without catalog history or a network connection, and history failure should leave the menu usable. [C1]

### Lifecycle completeness: rename, hide, moves, and READ

A configured but never-used BUILD is valid. Resolve its identity/hue through the existing machinery while keeping it out of usage totals until the ledger records it. A hidden default remains valid under Suggested: hide suppresses Recent only. Never unhide automatically.

Extend `bob themes rename` to rewrite exact theme values in recognized area/project frontmatter and task inline fields, including archived tasks that can reopen, alongside its existing ledger/template scope. This is a deliberate contract change, limited to parsed managed fields; prose, code samples, and preserved reference sources remain untouched. Preview session/default/override counts separately. Preserve unrelated YAML bytes/comments. Field-only declarations should count as known references for rename without becoming historical catalog usage.

Renaming READ reveals another trap: a hardcoded reading fallback would recreate the old name immediately. I recommend one small setting, **`task_themes.reference`, default READ**, with rename's existing configuration-reference guard extended to cover its effective value, including the built-in default. A READ rename must explain that this setting needs to point to the destination first. This is one knob, not a general rules language. If it is deferred, rename READ must refuse explicitly instead of knowingly resurrecting the name.

Moves and reference-task regeneration must preserve overrides. Reading-task rewrites are an essential round-trip test: managed reconstruction must not drop user-authored theme metadata. Defaults themselves never reclassify old ledger entries; historical rewriting remains exclusive to the explicit global rename command.

## Alternatives and adjustments to the request

| Alternative | Judgment |
| --- | --- |
| Materialize defaults on all tasks | Reject: noisy diffs, frozen inheritance, lost provenance. |
| Infer from the last linked session | Reject as primary rule: mixes deliberate preferences, one-time placement, rollover, and composites. |
| Put task preferences in the theme journal | Reject: adds an identity/location join where a local field already fits; retain that journal for global hide/color preferences. |
| Rename YAML to default_theme | Defensible but unnecessary. Keep requested theme and label it Default theme in UI. |
| Task-text embeddings/LLM classifier | Defer: greater uncertainty and cost without improving the specified deterministic cases. |
| Always ask whether to remember | Reject as default UX: visible default-on Remember plus reset/undo gives control without another modal. |
| Treat any destination as a preference | Reject: unnamed/composite and inherited placements do not identify one deliberate theme choice. |

Explicit adjustments/clarifications:

1. Use complete `[theme:: WRITE]` syntax and existing Ctrl+Shift+Enter linking, without rebinding.
2. Task override beats READ; READ beats all note defaults.
3. Inherit from the nearest typed area/project through parent links, including sub-areas; never from directory or task indentation.
4. Remember deliberate singleton alternatives by default with a visible one-time escape and Use default reset. Never learn from implicit placement, rollover, or unchosen successor destinations.
5. Require component choice for composite persistence; unnamed destinations do not invent a preference.
6. Change menu selection, preserving backend no-name command semantics through explicit accepted targets.
7. Include transaction safety, managed-field rename, and reading-task round trips in the definition of done.
8. Add a configurable reading fallback/rename guard to prevent READ resurrection.
9. Apply the four seed edits at rollout; do not mass-stamp tasks or create fake theme history.

## Validation and delivery boundaries

A sensible sequence is shared resolver/mutation fixtures, recommendation UI, reliable remembered-choice transactions, lifecycle/rename coverage, then four seed edits. Intermediate work can be reviewed independently; the finished feature includes persistence and rendering.

| Area | Minimum meaningful cases |
| --- | --- |
| Precedence | Override beats READ; READ beats project; project beats area; sub-area/deep inheritance; no default. |
| Reference identity | Modern/legacy tasks, rereads, stable block IDs after rename; follow-ups stay ordinary tasks. |
| Invalid metadata | Null/blank, wrong types, duplicates, malformed fields, ambiguous parents, cycles, depth limit, code examples. |
| Destination | Singleton, composite, completed-only, multiple matches, unnamed, unavailable create, prefix-shadowed names. |
| Persistence | Same choice no-op; alternate singleton once; one-time preserves prior override; reset; undo; implicit fallback does not learn. |
| Failure/retry | Cancel, preview, stale task/ancestor/destination, second-file failure, inbox-move failure, repeat request, concurrent edit during rollback. |
| Survival | Rollover, move, archive/reopen, reading-task rewrite, rename, unused default, hidden default. |
| Presentation | Keyboard selection survives refresh; typing wins; visible reason; light/dark/no-color; source editing; embeds, query results, task cards, popouts, accessibility. |
| Compatibility | Old/new client combinations; optional fields; unavailable persistence disabled; no Swift resolver. |
| Performance | Cold/warm and p95 timings on a live-size vault, with bounded chain reads and indexed reference lookup. |

Use fault injection for two-file writes: a happy-path test cannot establish atomicity. Follow each repository's normal validation and fragment build checks. Mac changes require portable checks plus macOS-target compile/test evidence; this research supplies neither. Seed through the approved vault workflow using exact-path frontmatter edits and a four-file diff.

After rollout, assess whether common cases need only Enter, whether the source explanation is understood, whether one-time exceptions are easy, and whether saved preferences are frequently reset. These are proposed evaluation questions, not collected measurements; no new telemetry service is necessary.

## Sources

Repository links identify files inspected locally at the pinned snapshots; repository source was not fetched through the web. The report intentionally avoids ephemeral workspace paths.

- **C1 — Theme contract:** [docs/pomodoro-themes.md](https://github.com/bobs-org/bob-cli/blob/50f6c91bc03029dc8cf0e449d8380c107d2183ff/docs/pomodoro-themes.md), PT1–PT10: identity, history, performance budget, visual language, menus, hide, rename.
- **C2 — Rust completion:** [theme_menu.rs](https://github.com/bobs-org/bob-cli/blob/50f6c91bc03029dc8cf0e449d8380c107d2183ff/src/native/capture_complete/theme_menu.rs), [pomodoros.rs](https://github.com/bobs-org/bob-cli/blob/50f6c91bc03029dc8cf0e449d8380c107d2183ff/src/native/capture_complete/pomodoros.rs), [engine.rs](https://github.com/bobs-org/bob-cli/blob/50f6c91bc03029dc8cf0e449d8380c107d2183ff/src/native/capture_complete/engine.rs), [model.rs](https://github.com/bobs-org/bob-cli/blob/50f6c91bc03029dc8cf0e449d8380c107d2183ff/src/native/capture_complete/model.rs).
- **C3 — Obsidian linking:** [block-id-prompt documentation](https://github.com/bobs-org/bob-plugins/blob/8baf76398048612cc0ed1c7b7b03537c87056b3b/docs/block-id-prompt.md), [076 theme picker](https://github.com/bobs-org/bob-plugins/blob/8baf76398048612cc0ed1c7b7b03537c87056b3b/plugins/block-id-prompt/src/076-pomodoro-theme-picker.js), [085 modal](https://github.com/bobs-org/bob-plugins/blob/8baf76398048612cc0ed1c7b7b03537c87056b3b/plugins/block-id-prompt/src/085-pomodoro-link-picker-modal.js), [122 picker request](https://github.com/bobs-org/bob-plugins/blob/8baf76398048612cc0ed1c7b7b03537c87056b3b/plugins/block-id-prompt/src/122-plugin-pomodoro-link-picker.js), [126 API](https://github.com/bobs-org/bob-plugins/blob/8baf76398048612cc0ed1c7b7b03537c87056b3b/plugins/block-id-prompt/src/126-plugin-pomodoro-link-picker-api.js).
- **C4 — Completion/successor behavior:** [task-status-cycler documentation](https://github.com/bobs-org/bob-plugins/blob/8baf76398048612cc0ed1c7b7b03537c87056b3b/docs/task-status-cycler.md); audited `decisions:unblocked-tasks-are-offered`.
- **C5 — Write paths:** [Rust existing_task_link.rs](https://github.com/bobs-org/bob-cli/blob/50f6c91bc03029dc8cf0e449d8380c107d2183ff/src/native/capture/existing_task_link.rs) and [Obsidian 120-plugin-pomodoro-links.js](https://github.com/bobs-org/bob-plugins/blob/8baf76398048612cc0ed1c7b7b03537c87056b3b/plugins/block-id-prompt/src/120-plugin-pomodoro-links.js), especially `applyPomodoroTaskLink` around line 654.
- **C6 — Task/reference identity:** [note_tasks.rs](https://github.com/bobs-org/bob-cli/blob/50f6c91bc03029dc8cf0e449d8380c107d2183ff/src/native/note_tasks.rs), [ref_tasks/line.rs](https://github.com/bobs-org/bob-cli/blob/50f6c91bc03029dc8cf0e449d8380c107d2183ff/src/native/ref_tasks/line.rs), [ref_tasks/walk.rs](https://github.com/bobs-org/bob-cli/blob/50f6c91bc03029dc8cf0e449d8380c107d2183ff/src/native/ref_tasks/walk.rs); audited reference-task glossary.
- **C7 — Parent traversal:** [project_dependencies/tree.rs](https://github.com/bobs-org/bob-cli/blob/50f6c91bc03029dc8cf0e449d8380c107d2183ff/src/native/project_dependencies/tree.rs).
- **C8 — Rename:** [pomodoro_themes/rename.rs](https://github.com/bobs-org/bob-cli/blob/50f6c91bc03029dc8cf0e449d8380c107d2183ff/src/native/pomodoro_themes/rename.rs), plus C1 PT10.
- **C9 — Ref Today:** [docs/ref.md](https://github.com/bobs-org/bob-cli/blob/50f6c91bc03029dc8cf0e449d8380c107d2183ff/docs/ref.md#bob-ref-today).
- **C10 — Obsidian rendering/mirrors:** [279-theme-chips](https://github.com/bobs-org/bob-plugins/blob/8baf76398048612cc0ed1c7b7b03537c87056b3b/plugins/bob-ledger-tools/src/279-plugin-pomodoro-theme-chips.js), [279-themes API](https://github.com/bobs-org/bob-plugins/blob/8baf76398048612cc0ed1c7b7b03537c87056b3b/plugins/bob-ledger-tools/src/279-plugin-pomodoro-themes.js), [279-theme-mirrors](https://github.com/bobs-org/bob-plugins/blob/8baf76398048612cc0ed1c7b7b03537c87056b3b/plugins/bob-ledger-tools/src/279-plugin-pomodoro-theme-mirrors.js), [266-popout mark gates](https://github.com/bobs-org/bob-plugins/blob/8baf76398048612cc0ed1c7b7b03537c87056b3b/plugins/bob-ledger-tools/src/266-plugin-mark-gate-mirror.js).
- **C11 — Mac client:** [CaptureModels.swift](https://github.com/bobs-org/bob-mac-capture/blob/88757e97c4d761e4fbbf4829c1ed6badb7db36af/Sources/CaptureCore/CaptureModels.swift), [CapturePanelModel.swift](https://github.com/bobs-org/bob-mac-capture/blob/88757e97c4d761e4fbbf4829c1ed6badb7db36af/Sources/BobMacCapture/CapturePanelModel.swift), [RefsTodayLinkPresentation.swift](https://github.com/bobs-org/bob-mac-capture/blob/88757e97c4d761e4fbbf4829c1ed6badb7db36af/Sources/RefsCore/RefsTodayLinkPresentation.swift); audited thin-client decision.
- **E1 — Obsidian Properties:** [Official documentation](https://obsidian.md/help/properties), accessed 2026-10-28. Supports scalar frontmatter; Bob's inheritance policy is our design.
- **E2 — Dataview:** [Metadata on Tasks and Lists](https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-tasks/) and [Adding Metadata](https://blacksmithgu.github.io/obsidian-dataview/data-annotation/), accessed 2026-10-28. Supports bracketed task fields and page-field inheritance.
- **E3 — Visibility of system status:** [Nielsen Norman Group](https://www.nngroup.com/articles/visibility-system-status/), Aurora Harley, 2018-06-03. Supports visible explanation and pending-change feedback.
- **E4 — User control and freedom:** [Nielsen Norman Group](https://www.nngroup.com/articles/user-control-and-freedom/), Maria Rosala, 2020-11-29. Supports cancel/reset/undo; it does not validate this feature's particular default-on remembering policy.

## Recommended solution

Ship **explicit task override → reading-task READ → nearest area/project theme → existing destination fallback**, with no task-text inference and no mass materialization of defaults. Seed `dev: BUILD`, `love: CHORE`, `job: WRITE`, and `sase_blog: WRITE` when the complete behavior is ready.

Make the initial task-aware completion choice an executable, deduplicated Suggested row with a visible reason and destination effect. Reuse Bob's theme pills for explicit task fields, and show the effective default plus Use default in the task card. Remember deliberate alternative single themes automatically with a visible one-time escape; require a component choice for composites and never learn from automatic placement or rollover.

Treat safe link-plus-preference writes, live-editor correctness, reference-task preservation, and managed-field rename as core functionality. This version saves repeated decisions while keeping the vault understandable and the interface calm.
