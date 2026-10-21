# Quiet GTD phase marks and readable recurrence

Independent design research by **cdx** · 2026-10-21

**Recommendation:** implement this as an Obsidian display feature in `bob-ledger-tools`. Collapse each valid GTD tag pair into one quiet, monochrome **icon + PRE/POST label**, and render familiar recurrence fields as a **repeat icon + short, readable rule**. Preserve `when done` visibly. Keep the original Markdown, task semantics, completion gestures, and recurrence generation unchanged.

This is a good idea. The main adjustment I recommend is resisting maximal compression: a beautiful task line should be easy to understand without hovering, remembering an icon legend, or discovering that two identical-looking recurrence marks behave differently. Removing the metadata syntax yields most of the benefit without removing its meaning.

## 1. Evidence and scope

I independently inspected Bob's current task-mark implementation and review classifier, queried the vault read-only through `bob query`, examined upstream Tasks source through an audited external checkout, and consulted official Obsidian, Lucide, and W3C documentation. I did not consult any other report, transcript, or findings from this research swarm.

Repository baselines:

- `bob-cli`: `c13016217b448ef21c4c490ea58aa448d4f0cd20`.
- `bob-plugins`: `ee16031f6944628f3099571f5fbd51d01de95f6d`.
- Upstream Tasks: `fa04fc18ab5643bba01767a824449406c871ec8d`, described by Git as `8.6.0-9-gfa04fc18a`. I also checked the `8.4.0` tag for the recurrence parser, API, and rendered recurrence component, because Bob's existing display contracts document that version. This does **not** establish which Tasks version is installed in the running Obsidian app.

This is design research, not an implementation or live UI verification. No vault content, plugin source, settings, or task metadata was changed. Source evidence establishes feasibility; actual visual quality, screen-reader behavior, and mobile interaction still require in-app verification.

### What the vault actually contains

The focused census selected task status symbols space, `?`, `*`, and `/`, excluded `_templates/` and `_conflicts/` for the recurrence count, and grouped by the parsed `repeat` field. It found **14 active recurrence rows with six distinct rules**:

| Stored repeat value | Active rows | Suggested compact rendering |
| --- | ---: | --- |
| `every day when done` | 9 | repeat icon · `daily when done` |
| `every week on Monday when done` | 1 | repeat icon · `weekly Mon when done` |
| `every week on Sunday` | 1 | repeat icon · `weekly Sun` |
| `every 30 days when done` | 1 | repeat icon · `every 30 days when done` |
| `every month on the 1st` | 1 | repeat icon · `monthly on the 1st` |
| `every 28 days` | 1 | repeat icon · `every 28 days` |

A separate active-status checklist query found **8 PRE rows and 2 POST rows**. All ten have recurrence: all eight PRE rows and one POST row use `every day when done`; the other POST row uses `every week on Monday when done`. These are membership counts, not today's eligible walk queue. They do not apply future-date, blocking, or other due-queue exclusions. The query produced unrelated ambiguous-link warnings but completed successfully; these counts use task fields and tags, not link resolution.

The census supports a small formatter rather than a general recurrence-language project. It also shows why POST must not imply evening: one POST item closes the **morning review**, and another is the weekly prune.

Reproducible recurrence query:

```dataview
TABLE WITHOUT ID rule AS "Repeat rule", length(rows) AS "Active rows"
FLATTEN file.tasks AS t
WHERE contains(list(" ", "?", "*", "/"), t.status)
  AND t.repeat
  AND !contains(file.path, "_templates/")
  AND !contains(file.path, "_conflicts/")
GROUP BY t.repeat AS rule
SORT length(rows) DESC
```

Checklist query:

```dataview
TABLE WITHOUT ID phase AS "Phase", length(rows) AS "Tasks", rows.t.repeat AS "Repeat rules"
FLATTEN file.tasks AS t
WHERE contains(list(" ", "?", "*", "/"), t.status)
  AND contains(t.tags, "#gtd")
  AND (contains(t.tags, "#pre") OR contains(t.tags, "#post"))
GROUP BY choice(contains(t.tags, "#pre"), "PRE", "POST") AS phase
```

These census queries target the current lowercase tags; the implementation must also handle the classifier's case-insensitive forms.

## 2. Critique: the valuable change and its limits

The valuable change is reducing repeated visual scaffolding. `#gtd #pre` communicates one useful classification using two prominent tag pills. `[repeat:: every day when done]` mixes a useful rule with storage syntax. Both deserve a more restrained presentation.

The risk is replacing readable information with a private pictographic language. An icon can indicate a category effectively, but no universally understood icon means “opening tier of Bryan's morning review.” Likewise, a loop alone cannot tell daily recurrence from monthly recurrence or date-based recurrence from completion-based recurrence. Hover-only explanations would be particularly weak on mobile and in exported notes.

A second risk is implementation scope. Obsidian has multiple rendering paths, and Tasks query results are not ordinary rendered Markdown. Treating this as one CSS rule would be deceptively simple. Treating it as a new recurrence editor would be unnecessarily large. The appropriate middle is a narrow presentation layer that extends the existing marks architecture.

Finally, ten GTD rows do not justify a general-purpose configurable icon engine. Solve these two concrete representations, preserve readable fallbacks, and leave additional metadata types for separate decisions.

## 3. Proposed appearance

### Phase marks: a small icon with PRE or POST

Use **Lucide `list-start` for PRE and `list-end` for POST**, with a short visible label. The paired icons depict the beginning and end of a list, which is closer to the actual semantics than a time-of-day metaphor. The icon pages themselves describe their queue/top/start and queue/bottom/end associations. This is my design interpretation, not evidence that users can identify them without text. [Lucide list-start](https://lucide.dev/icons/list-start), [Lucide list-end](https://lucide.dev/icons/list-end).

| Source | Resting display | Accessible meaning |
| --- | --- | --- |
| `#gtd #pre` | `list-start` icon + **PRE** | PRE: opening checklist for the morning review |
| `#gtd #post` | `list-end` icon + **POST** | POST: closing checklist for the morning review |
| `#gtd` alone | Native tag | No phase was specified |
| `#pre` or `#post` alone | Native tag | Incomplete GTD membership; do not imply a valid phase |

These are **one combined mark per pair**, not one icon per tag. Keep the current `#task` identity mark separate in the first implementation. Task identity and review phase are different dimensions; preserving their existing ownership avoids special cases involving `#task #ref`, Today marks, and nonadjacent tags. Although merging the entire `#task #gtd #pre` cluster could save another icon, it would widen the change without solving the main clutter.

Use the existing teal identity ink for both phase marks, subject to contrast checks. Shape and text distinguish PRE from POST; they do not need different colors. Their tone must not change when a task becomes eligible for today's walk: the mark says **belongs to this group**, not **due now**. Closed rows may follow the existing subdued treatment while remaining identifiable.

At normal note size, target an approximately `1em` square icon and `0.82–0.9em` label, with a small consistent gap. These are starting values to inspect at 100% zoom, not a finalized pixel specification. Match the stroke weight, baseline, and line height of the existing task/date marks. Avoid filled pills, borders at rest, animation, a second accent palette, or extra row height. Use the existing quiet hover/focus treatment.

### Why not the obvious alternatives?

| Option | Assessment |
| --- | --- |
| Sunrise / sunset | Attractive pair, but sunset suggests an evening ritual. POST closes the morning review. Reject for this workflow. |
| Play / stop, checkmark, or checked circle | Suggest execution, stopping, or completion. POST membership is not completion. Reject. |
| Flag / finish flag | Legible, but flags suggest priority; a finish flag also overlaps Tasks' on-completion vocabulary. Reject here. |
| Log-in / log-out | Coherent entry/exit pair, but strongly associated with accounts and actions. Less appropriate than list position. |
| Pure PRE / POST text | Strong fallback and a credible simpler implementation, but lacks the icon cue the user requested. |
| Icon only | Smallest, but depends on learning and hover. Revisit only if the labeled version feels too wide after real use. |
| Icon + PRE / POST | Recommended: compact, recognizable without hover, consistent with the established review labels. |

The tiny words are intentional. I would not add an icon-only preference menu in the first release; a raw-mark toggle is enough. If a week of actual use establishes that the words are redundant, removing them can be a separate, small decision.

### Repeat marks: show the cadence, not the wrapper

Use a monochrome **Lucide `repeat`** icon followed by a readable value. Its two-arrow loop is distinguishable from the circular freshness/refresh symbol and uses the familiar recurrence metaphor. Do not animate it. [Lucide repeat](https://lucide.dev/icons/repeat).

Schematic examples, with bracketed icon names standing in for the actual SVGs:

```text
Source:
[ ] #task #gtd #pre Brush teeth [repeat:: every day when done]

Display:
[ ] [task] [list-start] PRE  Brush teeth  [repeat] daily when done

Source:
[ ] #task #gtd #post Weekly prune [repeat:: every week on Monday when done]

Display:
[ ] [task] [list-end] POST  Weekly prune  [repeat] weekly Mon when done
```

The repeat mark stays where the repeat field was, among the task's other metadata. Do not relocate it into a new gutter or combine it with the phase icon. A non-GTD task with the same recurrence receives the same recurrence rendering.

The smallest useful first formatter is:

- `every day` → `daily`.
- `every week` → `weekly`.
- `every month` → `monthly`.
- `every year` → `yearly`.
- `every week on <one weekday>` → `weekly <weekday abbreviation>`.
- `every month on the 1st` → `monthly on the 1st`.
- `every N days` → retain `every N days`; removing the wrapper still helps.
- Preserve an optional terminal **`when done`** visibly and verbatim in every supported form.

Only apply these transformations on a whole-value match to the supported grammar. Unknown forms retain their native rendering. Do not perform broad text substitutions or drop unrecognized tails. A complex rule can be longer because its meaning is more complex.

For the most common field, `[repeat:: every day when done]` contains 30 source characters. The readable label `daily when done` contains 15, plus one icon and spacing. That is a useful reduction without an opaque code such as `1d✓`. It is not a claim about measured pixel savings.

### `when done` is behavior, not decoration

Tasks distinguishes recurrence based on the original reference date from recurrence based on completion. The parser stores the distinction, and its date calculation has separate paths. Consequently `daily` and `daily when done` must remain visually different. Monthly rules also have date-specific behavior; do not simplify 28 or 30 days to “monthly,” or “monthly on the 31st” to “monthly.” [Tasks recurrence implementation](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/fa04fc18ab5643bba01767a824449406c871ec8d/src/Task/Recurrence.ts), [Tasks recurrence guide](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/fa04fc18ab5643bba01767a824449406c871ec8d/docs/Getting%20Started/Recurring%20Tasks.md).

Do not replace `when done` with a checkmark: that can look like the task is already completed. Do not calculate a “next occurrence” date for this feature. That would need to reproduce Tasks' recurrence semantics and settings, while adding another date to a task line already containing date marks.

A repeat mark means **recurrence is configured**; it is not a promise that a new occurrence will appear without the user's completion gesture.

## 4. Semantics that rendering must preserve

### Match group membership, not literal typography

Bob's `freshnessChecklistForTags` lowercases whole tag tokens, requires `#gtd`, chooses PRE when `#pre` exists, otherwise chooses POST when `#post` exists. It does not require adjacency or a particular order. Therefore the renderer must not silently define a narrower membership rule around the exact string `#gtd #pre`. [Bob checklist classifier](https://github.com/bobs-org/bob-plugins/blob/ee16031f6944628f3099571f5fbd51d01de95f6d/plugins/bob-ledger-tools/src/100-freshness-evaluate.js#L45).

Required behavior:

- Accept case variants and reversed or separated tags when their exact token identities establish membership on the same task row.
- Do not match `#gtd/sub`, `#prepare`, `#postponed`, links merely containing those characters, or substrings in words.
- Do not decorate tag examples inside inline/fenced code, headings, or plain prose. Do not borrow a tag from a child task or neighboring list item.
- Do not require a task to be due, currently in the walk, or currently open merely to show its group identity. Keep group identity stable in completed history as well.
- Require a real task row and Bob's tracked-task context. If a row is outside that context, leave native tags instead of implying that the review engine tracks it.
- If both PRE and POST occur, leave the phase tags raw. The evaluator still gives PRE precedence; the rendering layer must not conceal the conflict behind a reassuring clean badge. Bob already has a `checklist_tag_conflict` lint. Repeated/ambiguous pair tokens should likewise fall back to raw rather than guess which anchors to consume.

Bob also has an incomplete-tag lint and a checklist recurrence lint for missing `when done`. The display feature must preserve these diagnostics and must not “repair” metadata while rendering. [Existing checklist lints](https://github.com/bobs-org/bob-cli/blob/c13016217b448ef21c4c490ea58aa448d4f0cd20/docs/freshness.md#L529).

For adjacent tags, one replacement range can cover the pair and its internal whitespace. For nonadjacent tags, use separate ranges: render the mark at the phase token and suppress only the corresponding `#gtd` token. Never replace the entire span between them: it can contain task text or another tag. Retaining an extra separator in an unusual layout is preferable to swallowing text. This needs a pair-level reveal rule so editing either tag restores both.

### Be more conservative with repeat than with ordinary decoration

A pleasant recurrence mark can falsely imply that Tasks recognizes a field. Therefore compact only a single canonical `repeat` field in a confirmed task-metadata suffix, outside code, with a completely recognized value. Support square and round Dataview wrappers if their structural handling is verified; otherwise leave a supported-but-unhandled wrapper native until that adapter exists.

Do not decorate duplicate fields, incomplete input, mismatched delimiters, uppercase keys, a field embedded in task prose, or unsupported grammar. Do not label every unformatted value invalid: a valid complex recurrence may simply be outside this formatter's scope. Native display is the safe fallback, not an error state.

Tasks' Dataview serializer extracts fields from the end of the task and uses `repeat::` specifically. Bob's existing `freshnessTasksSuffixStart` is a useful placement helper, but it accepts more surrounding syntax than a recurrence validator; it is not sufficient proof by itself. Add fixtures comparing the supported suffix cases with Tasks rather than treating a broad inline-field regex as authority. [Tasks Dataview serializer](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/fa04fc18ab5643bba01767a824449406c871ec8d/src/TaskSerializer/DataviewTaskSerializer.ts), [Bob suffix helper](https://github.com/bobs-org/bob-plugins/blob/ee16031f6944628f3099571f5fbd51d01de95f6d/plugins/bob-ledger-tools/src/080-freshness-placement.js#L369).

There is no need to import Tasks' private recurrence object or add another full recurrence library. Its documented public API offers task editing and completion operations, not a general recurrence-parser service. Keep the formatter finite and fail visibly back to text. [Tasks public API](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/fa04fc18ab5643bba01767a824449406c871ec8d/src/Api/TasksApiV1.ts).

## 5. Interaction and accessibility

**Live Preview:** follow the existing Bob marks contract. Moving a caret into a replaced source range, selecting across it, or clicking it reveals the raw source. A phase mark reveals both participating tags. A recurrence mark reveals its own field only. Clicking never changes the task, completes it, edits its schedule, or advances the review walk. Source mode always shows literal Markdown. A vertical Vim move onto the same line should not reveal unrelated metadata and shift the entire line. Existing task marks already use selection-sensitive replacement widgets for this purpose. [Bob task-mark contract](https://github.com/bobs-org/bob-cli/blob/c13016217b448ef21c4c490ea58aa448d4f0cd20/docs/task-tag-marks.md#L178).

**Reading view:** retain the phase tag's native anchor and its native search action. Annotate `#pre` or `#post`; visually suppress the partner `#gtd` only after the pair is established. The raw toggle restores both native tags, including the broader `#gtd` search affordance. Do not turn the mark into a review-navigation button. Recurrence text is informational; use the existing source/edit affordance rather than introducing a new recurrence modal.

**Accessible names:** the phase anchor should retain its link role and receive a meaningful label such as “PRE — opening morning-review checklist; search #pre.” A noninteractive editor widget can expose the corresponding text meaning without pretending to be a button. The recurrence mark's accessible name should contain the full original value, for example “Repeats every day when done.” Do not let decorative SVGs announce their path or icon names, and avoid duplicate announcements from both hidden original content and the replacement.

**Hover and focus:** offer the full original recurrence wording and an explanation of the phase, but make this supplemental. Keep `when done` and PRE/POST visible, so touch users need no hover to understand essential information. If using custom tooltips, check keyboard access, dismissal, hoverability, and persistence; `title` alone is not the interaction design. [W3C content on hover or focus](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html).

**Contrast and export:** test meaningful icons at at least 3:1 against their actual backgrounds, and small readable labels at the normal-text contrast target of 4.5:1. Do not rely on PRE/POST colors alone. Check the actual Blocked/Next/Pending tints, dark and light themes, forced colors, and closed rows. Retain a usable textual fallback when masks fail or on print/export. Matching the current mark family's appearance does not establish accessibility automatically. [W3C non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html), [W3C use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html), [W3C text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

Editor clipboard operations must continue to copy the original Markdown. For reading-view copy, explicitly test the chosen hiding technique: keeping an anchor in the DOM does **not** prove that browser clipboard text includes it. At minimum, visible copied text must not contain duplicate labels or broken task titles; source mode remains the exact-source copy route.

## 6. Implementation architecture and surface coverage

Put both features in **`bob-plugins/plugins/bob-ledger-tools`**, alongside the current task, date, priority, and freshness marks. Use small pure model functions plus host-specific adapters. Do not build a separate plugin, mutate vault source, change the global Tasks filter, or add a runtime CLI subprocess for rendering.

The existing source is fragmented and generates `main.js`. New implementation belongs in `src/` fragments and `styles.css`, with registration through `src/fragments.json`, lifecycle/install files, and the normal build. Do not hand-edit generated entrypoints. After implementation, repository instructions require `bob plugins sync` for deployment.

Useful seams:

| Existing source in bob-ledger-tools | Role in the proposed change |
| --- | --- |
| `100-freshness-evaluate.js` | Reuse checklist classification semantics; do not create a separate phase definition. |
| `138-task-tag-marks.js`, `264-plugin-task-tag-marks.js` | Pair recognition, widget interaction, native anchor annotation, toggling. Prefer separate small phase fragments if these files would exceed the repository's size limit. |
| `136-date-marks.js`, `266-plugin-date-marks.js` | Model/widget split, selection reveal, whitespace handling, rendered text scanning. |
| `267-plugin-date-marks-tasks.js` | Bounded query-result adaptation and preservation of Tasks-owned DOM. |
| `styles.css` | Shared icon definitions, typography, theme variables, focus, print fallback, and toggle gating. |

Use existing task-tag marks toggling for the phase marks and a separate session-only repeat-marks toggle. Both should restore native rendering immediately and clean up on unload. Do not add persistent configuration or a new public API namespace without a consumer.

### Live Preview

Use a viewport-bounded CodeMirror `ViewPlugin` with inline `Decoration.replace` widgets. This is the established Obsidian mechanism for replacing displayed content, and a view plugin is appropriate when the decorations can be derived from visible content without structural changes. [Obsidian decorations documentation](https://docs.obsidian.md/Plugins/Editor/Decorations).

Rebuild on document, selection, viewport, mode/file, and explicit toggle changes. Use full line context for a partially visible line, UTF-16 offsets, syntax-tree code exclusions, and sorted disjoint ranges. Ensure the phase and repeat ranges do not overlap task identity, Today, priority, date, or freshness decorations. Let raw input remain visible while incomplete or selected. Model equality should include the source rule and label, not just the icon.

### Reading view, embeds, and Dataview task output

Use idempotent Markdown post-processing, with the same ordering conventions as the existing marks. Inspect a task row's own content; do not scan descendants in a way that mixes parent and child tags. Preserve native anchors and skip `code`, `pre`, existing widgets, and already-processed inline fields.

One specific Bob pitfall matters: Dataview re-scans `innerHTML`. Existing mark builders deliberately keep the literal `::` sequence out of tooltips. A new tooltip containing `[repeat:: every day]` can reintroduce inline-field parsing. Use “Repeat: every day” plus the full value instead, and audit serialized attributes as well as visible text. [Existing date-mark warning](https://github.com/bobs-org/bob-plugins/blob/ee16031f6944628f3099571f5fbd51d01de95f6d/plugins/bob-ledger-tools/src/136-date-marks.js#L390).

If a fragment does not provide enough context to establish task ownership, pair membership, or suffix validity, leave it native. Do not assemble a recurrence rule across arbitrary DOM fragments merely to achieve visual uniformity.

### Tasks query results

Treat this as a distinct adapter. Upstream gives recurrence its own `.task-recurring` component; in full mode its inner text contains the recurrence icon and rule, while short mode contains only the icon. It does **not** attach a recurrence-rule data attribute. An implementation that reads `data-task-recurrence` would be invented. These observations are supported by the field renderer and full/short-mode fixtures, with the class also present in Tasks 8.4.0. [Tasks field renderer](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/fa04fc18ab5643bba01767a824449406c871ec8d/src/Renderer/TaskFieldRenderer.ts#L184), [Full-mode fixture](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/fa04fc18ab5643bba01767a824449406c871ec8d/tests/Renderer/TaskLineRenderer.test.Visualise_HTML_Full_task_-_full_mode.approved.html), [Short-mode fixture](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/fa04fc18ab5643bba01767a824449406c871ec8d/tests/Renderer/TaskLineRenderer.test.Visualise_HTML_Full_task_-_short_mode.approved.html).

For full mode, reuse the narrow scheduling pattern from Bob's Tasks date adapter: wait for a complete row, validate the expected component shape, append a listener-free mark, and visually hide the native child only after replacement succeeds. Preserve the host and any upstream listeners. Avoid a document-wide MutationObserver or rewriting `innerHTML`.

For phase tags, scope membership to direct content in the row's `.task-description`, not a broad `li:has(...)` selector that could count a nested child's tags. Exact attribute/text checks and case folding should agree with the model. The existing CSS-only `#task` treatment is a useful precedent but does not by itself solve paired-tag semantics and accessibility.

Respect user query layout:

- `hide tags`: do not recreate phase marks.
- `hide recurrence rule`: do not recreate recurrence marks.
- `short mode`: retain the native icon-only recurrence presentation or restyle only the glyph; do not invent a missing cadence or reverse an explicit request for compact output.
- Changed/unrecognized DOM or unsupported full-mode rule: retain native rendering.

Tasks already offers these layout controls. They are a useful alternative for individual dashboards, but do not address source-note Live Preview and would hide more information than this proposal by default. [Tasks layout documentation](https://publish.obsidian.md/tasks/Queries/Layout).

## 7. Acceptance evidence required before shipping

Model tests should cover semantics and range safety, not just snapshots of the chosen implementation.

| Case | Required outcome |
| --- | --- |
| Normal PRE / POST pairs, mixed case, reversed order, extra spaces | Same group, one mark, no source edits. |
| Nonadjacent tags with text or another tag between | Preserve every intervening character; reveal both participating tags together. |
| Only one tag, nested tags, prefix matches, duplicates, both phases | Native fallback; no misleading membership badge. Existing PRE precedence and lints remain unchanged. |
| Inline/fenced code; plain bullet; parent/child task combinations; callouts; numbered tasks | Only the correct real task tokens are decorated. |
| Future-scheduled, blocked, completed, and currently due members | Group identity remains stable; no claim of current eligibility. |
| The six observed recurrence values | Expected readable labels, with `when done` preserved. |
| Unfamiliar recurrence, multi-weekday/monthly qualifiers, malformed or duplicate repeat fields | Native readable fallback, never lossy abbreviation. |
| Field in prose versus confirmed suffix; brackets versus parentheses | Do not decorate an apparent field that Tasks would not interpret as recurrence. |
| Selection on either edge, multicursor, emoji before a field, Vim motions, IME composition | Correct UTF-16 ranges and source reveal; no swallowed text, caret traps, or writes. |
| Existing marks immediately adjacent | Disjoint decoration ranges and consistent spacing. |
| Full/short/hidden Tasks layouts, late row attachment, re-render | Respect layout, avoid duplicate marks, preserve upstream interactions. |
| Dataview reprocessing, embeds, hover previews | No re-parsed tooltip fields or duplicate annotation. |
| Toggle off/on and plugin unload | Native rendering restored across existing views, with no orphan attributes or listeners. |
| Source copy, reading copy, print, mobile, keyboard/screen reader | Usable text alternatives, correct names, no duplicate copy output. |

Before deployment, run the affected mark tests, build checks, repository-required validation, and documentation checks. Then perform a focused live Obsidian pass in light/dark themes and iOS. In a disposable fixture vault, complete one calendar-based recurrence and one `when done` recurrence with marks enabled and disabled; the resulting Markdown and next occurrence must be identical. Rendering and toggling alone must write **zero bytes** to task files.

Visual acceptance should use an actual mixed task list at 100% zoom and a narrow pane, with existing priority/date/freshness/Today marks present. Check whether PRE and POST remain distinguishable when viewed quickly and whether `daily when done` reads as secondary metadata without becoming faint. The icon choice is a reasoned starting point, not a substitute for this inspection.

## 8. Explicit requirement adjustments

1. **Use icon + PRE/POST, rather than icon-only, by default.** This costs a few letters and avoids an unexplained symbol language. It still removes two tag pills in favor of one compact mark.
2. **Replace each tag pair as one semantic unit.** Do not assign separate unrelated icons to `#gtd` and `#pre`/`#post`.
3. **Treat phase marks as group identity, not live queue status.** This prevents rendering from implying that a blocked or future task is due for review now.
4. **Compact repeat syntax and familiar wording, not recurrence meaning.** Keep cadence and `when done` visible; leave complex rules native.
5. **Adopt conservative fallback as a feature.** Uncertain parsing, conflicting tags, unsupported rules, and changed upstream DOM retain readable source/native presentation.
6. **Keep storage and workflow unchanged.** No tag migration, new inline property, recurrence engine, task-card redesign, or changes to completion/navigation gestures.
7. **Scope the work to existing Obsidian note and task-rendering surfaces.** CLI/TUI, Mac Capture, global search/backlinks, pickers, and tag-pane redesign are outside this first change. Short-mode and hide directives retain their explicit meaning.

These are design recommendations, not changes already made to project policy or behavior.

## 9. Recommended solution

**Proceed with two small extensions to `bob-ledger-tools`: labeled phase marks using `list-start` / `list-end`, and conservative recurrence marks using `repeat` plus a readable rule.** Use the current marks' visual language, source-reveal interaction, toggles, and cleanup lifecycle. Preserve source Markdown and delegate recurrence behavior entirely to Tasks.

Start with the six recurrence forms observed in the active vault and the simple base-unit variants, preserving `when done` explicitly. Keep unusual values readable through native fallback. Support Live Preview, reading/embedded/Dataview task views, and Tasks full-mode output through separate adapters, while respecting short mode and hide options.

I would choose this over pure icons, sunrise/sunset, or globally hiding recurrence. It delivers a calmer task line immediately, keeps the morning-review meaning clear, and limits the maintenance burden to a presentation feature rather than a second task system.
