# Capture `<`: merge existing tasks into a new task

Independent research and design recommendation — researcher **cdx**, 2026-11-05.

## Decision in brief

**Yes: this is a good addition, provided `<` means a real task merge, not merely a relation write.** It gives a compact expression to a useful act: writing a better formulation of several existing tasks and bringing their context into it. The arrow points toward the surviving task, which makes the requested example readable:

```text
Some great new task! @foo^great < @foo+f @bar+b
```

Create `foo#^great`; merge `foo#^f`, then `bar#^b`, into it. The new task survives. The two originals become cancelled tombstones whose LINKS entries point to the survivor. Their descriptions and authored notes move beneath it; its generated LINKED FROM entries show the inverse, “merged from.”

Implement this as **a new-task modifier backed by the existing explicit merge engine**, with a target-first preview headed **Create task · Merge 2 tasks**. Do not implement it by rewriting the draft into `~~…|"merged into"`: that form has different configuration and closed-source behavior.

The feature is mostly grammar, integration, and presentation work. The challenging parts already have an engine, but they must not be bypassed. The most consequential risks are mistaken parsing, invisible source retirement, accidental partial creation, and old clients accepting syntax they misunderstand.

## Scope and evidence

I independently inspected bob-cli at commit `58e98558fb2c85c438ab866d992123531a90ed53` and bob-mac-capture at `6e09f2c7fabfdda0e337da63a6bb48b28c32747f`, opened through `sase repo open`. I consulted the audited Capture, Task Merge, Task Relation, and Task Link glossary entries and the capture/thin-client decisions. I did not consult the other swarm researchers or their reports.

I also ran read-only parser probes and three `capture --dry-run` probes in a temporary fixture vault inside this workspace. The installed executable identified itself as `bob 0.4.0` and reported grammar **12**; the checked-out source reports grammar **13**. These runtime results establish what that installed binary does, not that it is built from the inspected commit. The temporary fixture files were byte-for-byte unchanged after each dry run. No product code or real vault files were changed, and I did not compile or run the Mac app.

Repository evidence is cited below with pinned source links. Proposed behavior is explicitly described as a recommendation. External UI guidance informs the accessibility and confirmation discussion; it does not establish Bob's current behavior.

## What exists already

### A real merge is much more than a labelled link

Bob's task-merge contract and pure planner already define the operation:

- Each source description becomes a plain title bullet under the target. Authored body content is cut beneath that bullet, preserving structure; descendant anchors and affected inbound links are repaired.
- Sources become Cancelled, retain their IDs and history, and record the merge relation. They are not deleted or marked Done.
- Open dependents are redirected to the target, with deduplication and cycle checks. A dependent lacking an addressable ID can refuse the operation.
- A source's own prerequisites are **not inherited**. They remain on the tombstone and are reported. `starts after` relations pointing at the source are also not redirected and are reported.
- Sources' live Task Links under today's open Pomodoros are pruned. Closed sessions and other-day history remain intact. The target may be offered once as a replacement, and linking requires an explicit choice.
- The target owns its status, schedule, priority, type, and freshness. Merge does not synthesize these from the sources; existing cancellation recovery can still affect a target that depended on a source.
- Recurring sources, `^prj` sources, sources with open nested tasks, overlaps, invalid destinations, and dependency cycles are refused. Same-note merges and eligible nested sources are supported. [C1, C5, C6]

This is the right semantic foundation. A link-only implementation would leave duplicate active work and fail to gather the notes that motivated consolidation. Conversely, calling the preview only “Add links” would conceal substantial mutations.

### Incoming merge already exists through relations

This currently works when `merged into` is a configured merge label:

```text
New target @target^new ~~source:src|"merged into"
```

There is a CLI integration test specifically for merging a picked existing task into a newly created capture task. The capture planner stages the new task, locates it as a relation owner, then invokes the shared merge engine against the staged snapshot. [C3, C4, C10]

However, the relation path runs with `MergeGesture::Label`. A closed source can yield `already_closed` and only add the relation. Explicit `>` uses `MergeGesture::Explicit`, which refuses an already-closed source unless the operation is the engine's same-target unchanged replay. Explicit merge also works when `merge_labels` is empty. [C4–C6]

The fixture probe confirmed the distinction:

| Fixture policy / source | Result of the incoming `~~` draft |
| --- | --- |
| `merge_labels: [merged into]`, open source | `merged`, one authored note moved in the preview |
| `merge_labels: []`, open source | Relation added; no merge record |
| `merge_labels: [merged into]`, completed source | `already_closed`, zero moved notes |

Therefore `<` is useful even though it overlaps an existing capability: it names an explicit operation without requiring users to know a configurable effect-bearing label.

### Existing transfer machinery is reusable, but not unchanged

The `>` scanner is shared by execution and editor parsing and claims transfers before ordinary target-run expansion. Its source list is ordered. Explicit merge passes the whole source vector into one merge request. `load_staged_snapshot` overlays prior staged edits and guards both note contents and the scanned file membership; `stage_merge_plan` preserves write ordering. Those are the correct building blocks. [C2, C4, C6, C7]

An easy-to-miss completion issue: the existing `>` source filter accepts **movable OR mergeable** tasks because `>` can move into a bare note. `<` can only merge. It needs a merge-only source role, otherwise it will suggest tasks the operation subsequently refuses, including some tasks with open children. Eligible nested source tasks should remain discoverable. [C9]

### The Mac already has useful merge presentation pieces

`CaptureTransferPresentation` consumes source and target descriptors, before/after statuses, moved-note counts, Bob-authored consequence sentences, repair summaries, and offers. `CaptureTransferCardView` already uses the merge symbol, a restrained purple accent, source status transitions, and an accessibility summary. Reuse these visual components. [M1, M2]

There are two integration traps:

1. The transfer presenter currently requires result kind `task_move` or `task_merge`. Adding `merges[]` to an ordinary `task` result alone will not activate that card.
2. `MergeRecord.target.created` describes a created **drawer or section** in the existing contract. It is not a reliable statement that the target task was born in this capture. Do not overload it to get a NEW badge. [C1, M1]

### Old parsing is actively unsafe for this spelling

The installed parser accepted the user's exact example with no diagnostics:

```json
{
  "grammar": 12,
  "mode": "sub_bullet",
  "body": "Some great new task! @foo^great <",
  "route": "foo",
  "block_id": "f",
  "targets": ["@foo+f", "@bar+b"],
  "diagnostics": []
}
```

The `targets` above is a shortened rendering of the actual structured array. It treated the source selectors as an ordinary target run. `Some great new task! @foo^great <` alone parsed as an ordinary task whose body still contained the marker text. Thus an old binary does not reliably reject this syntax; it can interpret a different operation. The checked-out language revision and the existing Mac minimum-revision gate provide the place to address this. [C11, M3]

## Critique and explicit requirement adjustments

The idea is sound. Its best use is **consolidation into a freshly written outcome**, not arbitrary graph editing. Retain that focus. Do not turn this release into reversible arrow notation for every transfer mode, a general merge wizard, or automatic deduplication.

I recommend the following clarifications and adjustments:

| Requested or ambiguous requirement | Recommended decision and reason |
| --- | --- |
| “Merged … by linking … using the label” | **Clarification:** run the full existing task merge, including moved content, dependency repair, and source cancellation. The label is provenance, not the whole operation. |
| “Only … a context that would create a new task” | **Tighten:** the left side must resolve to exactly one newly created, open, ordinary task. Merely having text before `<` is insufficient. Existing-task updates, note bullets, drawers, references, project-note creation, and pure session operations are refused. |
| Multiple source tasks | Preserve typed order; validate every source; submit one merge request and one capture transaction. Reject duplicate identities, including aliases. Never silently skip a bad source or deduplicate it invisibly. |
| Relation label literally `merged into` | **Small consistency adjustment:** use the same first-configured-merge-label-or-`merged into` rule as `>`. Empty label configuration must not disable `<`. If a fixed literal label is essential, make that an explicit exception to the shared explicit-merge policy; I prefer consistency. |
| Source can already be closed | **Clarification:** explicit-merge refusal, not relation-only success. This avoids a half-effective consolidation. |
| New task inherits old tasks' metadata | **Do not add this behavior.** Keep current merge rules. Warn specifically about prerequisites left behind. Automatically combining schedules, priority, types, or prerequisite sets would be a separate product decision. |
| Automatic transfer of today's plan | Keep existing explicit Pull-In selection. A default new task is not silently put into today's ledger. |
| Works anywhere in the draft | Make `< sources…` a **terminal clause on the item's parent line**. Task modifiers belong before `<`; authored children follow on later lines. This is simpler to teach and parse. |
| New task + a simultaneous start/close | For the first release, refuse combined session-start/close actions. Ordinary creation with an explicitly requested Task Link can be supported when the existing planner proves it creates one task; never infer a new task from a link-only gesture. This is a deliberate scope boundary. |

A missing requirement deserves promotion to an acceptance criterion: **a failed merge must not leave the new task behind.** It is one user action. Also, do not advertise a fresh-created capture as generally idempotent simply because merging two already-existing identities can be idempotent.

The main cost is another punctuation operator in an already rich capture language. A consistent arrow direction, one terminal clause, and a visible “Merge from…” label in completion keep that cost reasonable. A verbose keyword would be more discoverable but would interrupt established marker syntax; the current `~~` relation spelling is considerably harder to remember and quote. I would keep both explicit arrows and retain `~~` for general relations.

## Proposed language contract

### Shape and ownership

```text
<ordinary-new-task-capture> < <source> [<source> ...]
source := @route+block-id
```

The first and last angle-bracket pairs above are grammar placeholders; the middle `<` is the literal operator. In actual drafts:

```text
Some great new task! @foo^great < @foo+f @bar+b

A better combined outcome @foo < @foo+f
- My new acceptance criteria
  - Keep this authored structure
```

No new destination notation is needed. Default inbox routing, normal route inheritance, and the existing `@route^id` creation form should continue to work. If no target ID is supplied, use the normal new-task ID allocation machinery because merge provenance needs a stable target. Dry run must not persist an ID or create a note.

A task-list row can use the clause **where the current list grammar already creates one ordinary task**. Its inherited destination belongs to the left side; the selectors after `<` are always sources. This does not authorize transfers inside project-note sealed bodies or change list routing rules. Retain existing literal behavior for forced-destination modes that intentionally treat `@` markers as text.

The new task's authored notes stay first; source groups append afterward at the established plain-child insertion anchor, in source order. Do not flatten matching drawer names, copy source managed logs, or add synthetic “MERGED TASKS” drawers. The existing content model already preserves provenance without clutter. [C1]

### Claim early; preserve ordinary prose

Use one span-aware scanner shared by execution, parsing, completion, and rewrite support. Claim the incoming clause **before source selectors can become a target run**, but leave the prefix to the normal task parser. Mask/remove only the clause while preserving original offsets; do not reconstruct the entire draft as a new string with changed coordinates.

Recognition rules:

- A standalone `<` followed by `@`, a complete `@route+id`, or an accepted source-picker placeholder claims an incoming merge.
- A terminal standalone `<` after a candidate task prefix is an incomplete merge. Do not capture it as prose on Submit.
- Glued operator forms such as `<@foo+f` receive a spacing diagnostic when they clearly intend this syntax.
- Once claimed, missing IDs, invalid selectors, a second `<`, extra prose, or another `>` refuse the clause. They do not fall back to task text.
- Preserve mathematical comparisons such as `Latency < 50ms`, `<=`, ordinary `<<`, HTML/autolinks, inline code, fenced code, and existing protected markup. Parent-line detection must not interpret operators in authored children.
- Offer `\<` as an escape at a would-be incoming-merge position. A literal escape must suppress the **whole clause interpretation**, so its `@` text cannot subsequently fan out. Specify and test this explicitly.

The left side is validated semantically after normal capture parsing: “one newly created ordinary task” is a planner fact, not a string heuristic. Check before ordinary task side effects can escape staging. A supplied ID already belonging to an existing task fails normal creation rules; it must never silently turn `<` into an existing-target merge.

### Validity and incomplete states

| Draft | Proposed response |
| --- | --- |
| `New outcome @foo^great < @foo+f @bar+b` | Create one task and merge two sources. |
| `New outcome < @foo+f` | Create in the normal destination; allocate target ID through existing machinery. |
| `New outcome @foo^great <` | Pending: “Choose a task to merge into ‘New outcome’.” No write. |
| `New outcome < @foo+` | Task-ID completion for a merge source; no write. |
| `New outcome < @foo+f @bar+` | Keep the first resolved source visible while completing the second; no write. |
| `@foo+existing < @bar+b` | Refuse: “`<` needs a new task. To merge into this task, use `@bar+b > @foo+existing`.” |
| `Notes @foo+existing < @bar+b` | Refuse: the left side appends a child, not a new task. |
| `New outcome < @foo` | Incomplete source selector; require a task ID. A note is never a source. |
| `New outcome < @foo^f` or `@foo:f` on the right | Teach `@foo+f`; do not interpret creation or ledger actions as sources. |
| `New outcome < @foo+f#drawer` or `@foo+f!` | Refuse source suffixes. Only whole source tasks are accepted. |
| `New outcome < @foo+f @foo+f` | Duplicate-source diagnostic on the second occurrence. |
| `New outcome < @foo+f s:3` | Refuse trailing modifier; teach placing target modifiers before `<`. |
| `Latency < 50ms @foo^fast` | Ordinary capture, unchanged. |

Use existing engine refusal codes for semantic errors, plus a small family for the new clause: spacing, incomplete source, source marker, extra text, and new-task-required. Exact code names should be settled with the grammar change. Include the item number, offending source, and UTF-8 byte span whenever possible; do not return only “invalid capture.”

### Composition rules

Allow normal target title, route, ID, task type, schedule, priority, clipboard content, and authored children, subject to their existing rules. Ordinary dependencies and inert relations on the new target can also compose when the final graph is valid. The merge engine must see the fully staged target, including those writes.

Reject an item that simultaneously modifies or completes a selected source through another marker. Conflicting close/merge intents should enter the existing batch close-intent registry, even though this clause is not implemented as a label effect. Do not emit duplicate relation writes by both the clause adapter and the relation-effects path.

Do not add a convenience “reopen closed sources” mode or silently clear their prerequisites to make a merge possible. Missing or ambiguous source identity, a dependency cycle, or a conflicting target is a whole-action failure.

## Preview and completion design

### One calm card, centered on the new task

The following is a schematic; source titles and counts are illustrative, not facts about the user's vault:

```text
⊞ Create task                                      foo › Tasks
Some great new task!                               NEW · ^great

⤵ Merge 2 tasks into this task
  First existing task                    foo · ^f   Ready → Cancelled
  Second existing task                   bar · ^b   Next  → Cancelled
  Moves 3 notes · 2 dependents now wait on this task

[Create & merge]                                           ⌘↩
```

In the actual UI, use the existing merge symbol and restrained accent. Keep the destination/title in a fixed top position as the user adds sources. Preserve the standard task type, schedule, and destination treatment. Source rows are smaller than the target but legible; “Cancelled” is visible text, not just tint or strikethrough. Prefer task titles, with note/ID as secondary disambiguation.

The action title is **Create & merge**. The resolved sources make the consequence concrete; there is no reason to repeat “Are you sure?” on every ordinary submission. Nevertheless, this recommendation rests on an explicit destructive preview and recoverable provenance, not on pretending Bob has an easy Undo button. Apple advises context-sensitive confirmation and avoiding needless repeated alerts; its undo guidance also distinguishes an easy reversal from mere theoretical recoverability. Do not claim that reopening a source reverses its moved notes and repaired links. [U1, U2]

For one to three sources, show all rows. For more, show three plus a keyboard-accessible “Show all N sources” disclosure, with the full list in the accessibility summary. Never hide a blocking error, the aggregate cancellation count, or a warning that changes the meaning of the operation. Expanded details can show the final task block and per-source content groups using existing task-block previews; a large Markdown dump should not be the default card.

### Make exceptional consequences visible

Concise preview must not mean incomplete consent. Show Bob-authored consequences, aggregated by stable task identity rather than blindly summing per-source counts:

```text
⚠ 2 prerequisites stay on the originals; this task will not wait on them.
⚠ “Follow up with Sam” still starts after a task being merged.
```

A single dependent that referenced both sources should appear/count once. For small cases, name the affected task directly. Make exact prerequisite/successor details available without displacing the new task title. Use the engine's final target status rather than assuming every new task remains Ready.

When sources lose live ledger links, retain the existing Pull-In offer and selected state. For example, “Link this task in place of 2 merged tasks in PLAN.” Do not auto-select it. If the target already has an explicitly requested link, do not offer a duplicate. This retains the current policy and avoids silently altering today's plan. [C1, C6]

### Pending and failure states

After `<`, retain the new-task portion of the card and replace the merge rows with “Choose a task to merge.” After one resolved source and one partial selector, retain the resolved row and show a neutral pending row. Do not flash a destructive red error while ordinary typing is incomplete.

A source that resolves but cannot merge gets a concrete message such as “Has 2 open subtasks; merge or close them first.” Submission remains unavailable for the entire item. A source that disappears or changes between preview and commit is revalidated by Bob; failure leaves the draft and diagnosis visible.

Never show an earlier successful preview as current while its draft revision is obsolete. Associate responses with the draft and executable identity, cancel/discard stale responses, and suppress submit until the current draft has a valid plan. Continue using Bob's existing subprocess/debounce machinery. Measure multi-source preview latency on a representative vault before deciding whether caching needs work; this research did not benchmark it.

### Completion should teach “merge from”

At `< @route+`, complete only mergeable tasks. At `< +query`, I recommend supporting the established vault-wide task-picker idiom, scoped to merge sources, with acceptance inserting canonical `@route+id`. This is an additive usability improvement, not required to commit an already-written source list.

Exclude sources already selected, canonical aliases of them, and the target identity. List titles, location, and current status; use a short “Merge into new task” context line. Accepting a source edits the draft only. Return and Tab retain the app's established completion behavior and never submit a partially resolved clause unexpectedly.

Use Bob's replacement ranges and semantic spans for both `@route+id` and the picker form. The Mac must not split the string or infer merge eligibility. The existing `>` union of movable/mergeable sources needs a dedicated merge-only variant. [C8, C9]

Provide accessible text for status transitions and announce settled result-count/error changes without shifting keyboard focus. Do not announce every keystroke. Text and symbols must carry meaning independently of color. These are native accessibility recommendations informed by W3C's status-message and use-of-color guidance, not a claim that a SwiftUI screen is a WCAG-certified website. [U3, U4]

## Recommended implementation architecture

### 1. Model a modifier, not another content grammar

Add a typed incoming-merge clause to the parsed item, containing the operator span and ordered source selectors. Keep normal new-task creation parsing, routing, body normalization, and child handling intact. A separate small scanner module can share task-selector primitives with `transfer.rs`; do not duplicate the entire `>` recognizer with the arrow reversed.

Wire it through both `draft.rs` and `editor_parse.rs` before target-run recognition. Extend the editor model, completion-role dispatch, and rewrite/format logic. New spans must be nonoverlapping, point into the original input, and respect Unicode boundaries. Grammar parse remains read-only and does not inspect task eligibility.

Keep editor mode as the ordinary task-creation mode with additive incoming-merge metadata where practical. Incomplete source selectors have a named need. Reusing `task_merge` as an editor mode indiscriminately would risk routing the prefix through transfer-only rewrite behavior.

### 2. Create and merge inside one staged batch

Recommended sequence:

1. Recognize the clause and validate that the prefix denotes one supported new-task operation.
2. Resolve source identities against the current staged snapshot and reject lexical duplicates/aliases and obvious conflicts.
3. Stage ordinary target creation and its authored children/metadata, obtaining its actual target identity. Nothing has been written to disk.
4. Load the staged merge snapshot, including the newly created target. Build one `MergeRequest` with all sources in typed order, `MergeContainer::Task(new_target)`, the explicit-merge label policy, and `MergeGesture::Explicit`.
5. Invoke `plan_task_merge` once. Reuse `stage_merge_plan`, read guards, repaired-file reporting, close-intent bookkeeping, and Pull-In handling. Refresh final target/source task-block references after merge and any later draft items.
6. Commit through the existing aggregate capture path only after the entire draft succeeds.

Do not spawn one `bob task merge` process per source. Do not first commit a new task and then merge into it. Both approaches weaken atomicity and make retry/recovery harder.

The snapshot/guard and destination-before-source infrastructure already exists. Preserve its rollback and recovery behavior rather than inventing another transaction system. “All or nothing” here means the existing capture guarantee for validation, planning, and guarded-write failures; it should not be expanded into an unproven claim of filesystem-wide crash atomicity. On catastrophic interruption, retaining an intact source is preferable to losing its content. [C1, C4, C6]

Same-note target/source cases require special attention: plan against post-creation offsets, resolve by stable identity, and apply one final postimage per file. The merge engine already supports multiple sources; a serial relation-based adapter would miss the opportunity to validate overlapping sources and aggregate offers as one operation.

### 3. Extend result metadata deliberately

Reuse the existing `merges[]`, consequence, repaired-file, Pull-In, and final task-block structures. Add a small explicit new-target descriptor, for example `merge_creation: { target: ..., created: true }`, plus Bob-authored summary/action text if the current presentation contract needs it. Proposed names are illustrative, not an existing schema.

**Recommended compatibility shape:** keep creation as the internal base operation and expose the composite success as the already-understood `kind: "task_merge"`, with the existing merge records and additive creation metadata. A new Mac renders a target-first Create & merge variant; an older compatible Mac can still render its known merge card, showing all retired sources and the surviving target. It may omit the NEW badge, but it must not hide the merge consequences. Preserve ordinary creation/budget fields and verify all consumers that branch on `kind`.

This is preferable to simply emitting `kind: "task"` plus a new optional field, because the inspected Mac transfer presenter ignores that combination. Keep `schema_version: 1` if the result changes remain additive, but bump the language revision. Do not overload the existing target-container `created` flag. [M1, C11]

For partial drafts, add a structured pending payload analogous to `transfer_pending`: item number, draft spans, pending source index, resolved source descriptors, target creation summary when available, and source-specific errors. Human output should remain useful and concise. New task creation is still a preview; do not imply that it has happened before submit.

### 4. Version the feature across both repositories

Use the next available grammar revision—**14 at the inspected source revision**, subject to rebase. Require that revision in the updated Mac before submission. A conservative global minimum-version gate is simpler and safer than adding a second partial parser in Swift to recognize `<` for older Bob. It temporarily requires upgrading Bob to use the updated app; that is an explicit rollout cost.

| App / CLI combination | Required behavior |
| --- | --- |
| New app / new Bob | Full target-first preview, completion, and composite commit. |
| New app / old or unidentified Bob | Submission blocked with an update message; never submit the draft as interpreted by the old parser. |
| Old app / new Bob | Known `task_merge` result renders sources, cancellation, destination, and offers. Test with the existing decoder/presenter before claiming support. NEW badge may be absent. |
| Old app / old Bob | No new feature. Document the syntax as requiring the new release; an old system cannot retroactively recognize it. |

Retain executable-identity-aware capability invalidation. Check the release against the actual Mac app on the user's upgrade path; do not assume “optional JSON field” guarantees semantic compatibility. If the old presenter fails the composite fixture, treat that combination as unsupported and require a coordinated app update before exposing the syntax. Do not conceal destructive consequences merely to preserve compatibility. [M1, M3, M4]

CLI examples must quote the entire draft: unquoted `<` is shell input redirection. Prefer stdin for multiline examples. Bob cannot generally recover an input-redirection operator consumed by the shell, so do not promise a symmetric version of the existing `>` special-case diagnostic.

### 5. Keep retries honest

A capture that creates a new target is not the same operation as merging into a target that already exists. An explicit `^great` collision must fail creation, even when a merge-only replay might otherwise be unchanged. With an auto-ID, a repeat draft normally encounters retired sources and must refuse without leaving a second target behind.

For a lost submit response, retain the draft and surface the actual outcome/recovery information; do not automatically resend a create-and-merge operation. General idempotency tokens or a new undo subsystem may be worthwhile elsewhere, but neither should be smuggled into this small feature as an assumed existing guarantee.

## Validation that determines whether this is ready

These are acceptance tests for implementation, not tests claimed to have run during this research.

| Area | Essential evidence |
| --- | --- |
| Grammar ownership | Exact user example produces one new owner plus two sources; sources never become ordinary target-run recipients. |
| Literal preservation | Comparisons, `<=`, `<<`, HTML/autolinks, code, authored children, and forced-literal modes retain their existing meanings. Escaped incoming syntax cannot subsequently fan out. |
| Incomplete input | `<`, `< @`, `< @foo+`, partial second source, and `< +query` produce useful pending states and cannot commit. Unicode and multiline source spans remain correct. |
| Context rule | Existing-task toggles, sub-bullets, drawers, project creation, bare URLs, and session-only forms refuse; default/routed/explicit-ID new tasks and eligible list rows work. |
| Merge fidelity | Titles and authored content move in typed order; tombstones, labels, mirrors, dependent rewrites, anchors, logs, and final status match the existing engine. |
| Source safety | Closed, recurring, `^prj`, open-subtask, duplicate/alias, overlapping, missing, and ambiguous sources refuse the whole capture. |
| Target identity | Explicit-ID collision, ID allocation without persistent dry-run writes, same-note creation/merge, and same-note descendant-anchor collisions are covered. |
| Graph and ledger | Shared dependent counts deduplicate; cycles refuse; unmet prerequisites are warned about; source links are pruned; target offered once and never auto-picked. Existing explicit target link produces no duplicate offer. |
| Composition | Target metadata, children, dependencies, and allowed inert relations survive; conflicting source actions fail; later bulk items see the merged snapshot. |
| Atomicity | A bad second source or later draft item leaves no new target and no retired source. Inject guarded-write failure; verify rollback/recovery behavior. Test concurrent changes to read-only dependency notes and vault membership. |
| Preview parity | Dry run and commit produce the same semantic effects under a fixed clock/snapshot; no clipboard access without its directive; no dry-run vault writes. |
| Mac presentation | One/two/many sources, long/duplicate titles, no authored notes, warnings, zero/one/many dependents, blocked target, pending second source, stale responses, and mixed bulk drafts. Test light/dark, narrow width, keyboard disclosure, and VoiceOver. |
| Compatibility | New app refuses grammar 12/13; existing app decoder/presenter renders the composite `task_merge` fixture and displays source cancellation. No unknown-field disappearance of consequences. |
| Retry | Repeating an explicit-ID draft refuses safely; repeating an auto-ID draft with retired sources does not create another target. Lost response does not trigger an automatic replay. |

Use the existing transfer and relation-merge fixtures as starting points, including the genuine incoming-new-task test. Prefer a few semantic end-to-end cases over tests that merely duplicate enum shapes.

For implementation validation, run the repository's required Rust checks and relevant capture/merge tests. Mac changes must compile: follow its AGENTS instructions, including portable checks, macOS build/type-check coverage, and the required macOS CI gate; watch the exact pushed SHA to green. Do not substitute a Linux-only check for macOS validation. Documentation and grammar-contract changes must pass their docs checks. This report itself changes no Swift or Rust code.

## Evidence index

All repository links refer to sources read locally through the approved checkout paths; web fetching was not used to inspect repository files.

- **C1 — Merge semantics and output contract:** [docs/task-merge.md](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/docs/task-merge.md), especially §§1–8 and the JSON record contract.
- **C2 — Existing transfer grammar:** [docs/capture.md, moving and merging with `>`](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/docs/capture.md#L6346).
- **C3 — Incoming new-task relation test:** [tests/cli/capture/relations_merge.rs](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/tests/cli/capture/relations_merge.rs#L107).
- **C4 — Relation merge adapter and guarded overlays:** [src/native/capture/relations_merge.rs](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/capture/relations_merge.rs), `plan_relation_merges`, `load_staged_snapshot`, and `stage_merge_plan`.
- **C5 — Shared planner and strict gesture distinction:** [src/native/task_merge/plan.rs](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/task_merge/plan.rs#L45) and [payload.rs](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/task_merge/payload.rs#L45).
- **C6 — Explicit capture adapter:** [src/native/capture/transfer.rs](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/capture/transfer.rs#L632).
- **C7 — Shared transfer recognition:** [src/native/capture_language/transfer.rs](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/capture_language/transfer.rs).
- **C8 — Completion role dispatch:** [src/native/capture_language/completion.rs](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/capture_language/completion.rs#L1486).
- **C9 — Movable-or-mergeable source filter:** [src/native/capture_complete/transfer_assist.rs](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/capture_complete/transfer_assist.rs#L80).
- **C10 — Staged new owner and relation results:** [src/native/capture/plan.rs](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/capture/plan.rs#L3323), [batch guards](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/capture/batch.rs#L1), and [task-block tracking](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/capture/task_blocks.rs#L17).
- **C11 — Language version and compatibility:** [capture_language/mod.rs](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/capture_language/mod.rs#L46) and [docs/reference/compatibility.md](https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/docs/reference/compatibility.md#L68).
- **M1 — Merge result decoder/presenter:** [CaptureTransferPresentation.swift](https://github.com/bobs-org/bob-mac-capture/blob/6e09f2c7fabfdda0e337da63a6bb48b28c32747f/Sources/CaptureCore/CaptureTransferPresentation.swift#L304).
- **M2 — Existing transfer card:** [CaptureTransferCardView.swift](https://github.com/bobs-org/bob-mac-capture/blob/6e09f2c7fabfdda0e337da63a6bb48b28c32747f/Sources/BobMacCapture/CaptureTransferCardView.swift#L1) and [panel dispatch](https://github.com/bobs-org/bob-mac-capture/blob/6e09f2c7fabfdda0e337da63a6bb48b28c32747f/Sources/BobMacCapture/CapturePanelView.swift#L3988).
- **M3 — Existing grammar gate:** [CaptureGrammarGate.swift](https://github.com/bobs-org/bob-mac-capture/blob/6e09f2c7fabfdda0e337da63a6bb48b28c32747f/Sources/CaptureCore/CaptureGrammarGate.swift).
- **M4 — Capability-aware subprocess submission:** [BobProcessClient.swift](https://github.com/bobs-org/bob-mac-capture/blob/6e09f2c7fabfdda0e337da63a6bb48b28c32747f/Sources/CaptureCore/BobProcessClient.swift#L817).
- **U1 — Confirmation tradeoffs:** [Apple Human Interface Guidelines: Alerts](https://developer.apple.com/design/human-interface-guidelines/alerts). The search-indexed primary-source excerpt was available; the page's Markdown fetch was unavailable in this environment.
- **U2 — Reversibility:** [Apple Human Interface Guidelines: Undo and redo](https://developer.apple.com/design/human-interface-guidelines/undo-and-redo). Consulted through the primary-source search excerpt.
- **U3 — Noninterrupting accessible status:** [W3C: Understanding Status Messages](https://www.w3.org/WAI/WCAG21/Understanding/status-messages).
- **U4 — Meaning beyond color:** [W3C: Understanding Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html).

## Recommended solution

Ship **`New task < @source+id …` as explicit “merge from” syntax for one newly created task**. Keep the requested spelling and arrow direction. Give it a small typed clause in the authoritative Rust grammar, claim it before target-run parsing, create the target only in the staged batch, and invoke the existing explicit multi-source merge planner once. Preserve existing merge semantics and require every source to pass validation.

Present one compact **Create & merge** card with the new task at the top, ordered source titles and visible Cancelled transitions beneath it, and only meaningful consequences expanded by default. Reuse the existing merge records and Mac visual components, add explicit target-creation metadata, and test old-client rendering and the new grammar gate as release requirements.

This gives the user a concise way to replace scattered work with a better task while retaining its context and history. The justified departures are strict explicit-merge behavior, one unambiguous new-task owner, a terminal source clause, no metadata inheritance or automatic ledger replacement, and a conservative version gate. Those constraints make the feature predictable without making it feel heavy.
