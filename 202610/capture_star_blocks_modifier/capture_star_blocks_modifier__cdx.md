# Reverse capture dependencies with `*`: implementation research and critique

Researcher: **cdx**. Date: **2026-10-14**. This report was researched independently. I did not read another swarm researcher's report, transcript, summary, or findings.

**Recommendation in brief.** Add `*note:block-id` as “this newly captured task blocks that existing task.” Translate it into the existing dependency model: the selected existing task depends on the new task. Reuse the staged dependency writer after inserting the new task into staged note contents. The feature is useful, but ledger removal needs a narrower contract and better preview reporting before it is safe to reuse unchanged.

**Evidence and limits.** I inspected bob-cli at `e7e98d2e49e6c9b034e864dbbc263ffa0dbabf48` and bob-mac-capture at `060d77b41a79df7b529c9085f184b76928c0cbbb`, including their documentation, Rust/Swift implementations, and relevant test sources. I also ran the installed `bob` against disposable synthetic vaults inside the workspace. Those probes are evidence about the installed executable, whose `bob --version` is only `0.1.0`; they do not establish that it was built from the inspected commit. Source review independently corroborates the behaviors described below. No real vault was accessed or mutated. I did not implement the feature, run the full repository tests, or compile Swift.

**What the operator should mean.**

Let N be the new task, D an existing dependent, and P an existing prerequisite. The arrows below mean “depends on,” not chronological execution order:

| Input | Stored relationship | Task whose Depends-On line changes |
| --- | --- | --- |
| `N &P` | N → P | N |
| `N *D` | D → N | D |
| `N &P *D` | D → N → P | N and D |

For example:

```text
Prepare credentials @work^credentials *release:publish
```

The `release.md#^publish` task gains `[[work#^credentials]]` on its managed `⛓️ **DEPENDS ON:**` child line. Its existing prerequisites remain in their existing order. Because the new prerequisite is open, Publish becomes `[?]` Blocked. The new task gets the prerequisite identity needed for the derived field, and, when enabled, a generated `🧱 **BLOCKS:**` line listing Publish. Publish's planned links under today's open Pomodoros leave the ledger.

This is an alternate *editing direction*, not a second type of dependency. Do not store a new authoritative `blocks` field on N or treat its generated BLOCKS line as an input. Bob's accepted model reads Depends-On lines and derives `[dependsOn::]`, prerequisite `[id::]` fields, and BLOCKS mirrors. The distinction is already explicit in [the dependency contract](https://github.com/bobs-org/bob-cli/blob/e7e98d2e49e6c9b034e864dbbc263ffa0dbabf48/docs/task-dependencies.md) and the audited decisions `task-deps-are-depends-on-links` and `projects-block-from-prj-line`.

The existing model also answers what happens later: completing N recovers D if its last blocking reason clears. Under the accepted `unblocked-tasks-are-offered` decision, any successor planning link requires an explicit selection; introducing `*` should not restore automatic linking on completion.

**Why this is a useful feature, and where it can mislead.**

The common situation is discovering a prerequisite while looking at downstream work: “before I can publish, I need to obtain credentials.” Capturing that prerequisite and attaching it to Publish in one gesture avoids creating the task, finding it again, and opening the dependent's dependency editor. This is a good fit for capture.

The cost is that an ordinary capture can now change several existing notes and today's agenda. An accidental direction reversal can block work instead of waiting for it. Multiple targets amplify that effect, especially when one is a project task. The UI should therefore use concrete verbs: `Depends on` for `&`, `Blocks` for `*`, and “Publish will depend on Prepare credentials” in the preview. Calling both pickers “Choose dependency” would hide the distinction that matters.

The exact character is less important than this clarity. `*` is acceptable if the parser protects normal Markdown and existing session syntax. A wordier `blocks:` modifier would be easier to discover but slower to type and would require its own escaping and completion contract. Reusing `&` with a directional suffix would be less visually distinct. I would keep the requested `*`, with clear UI copy rather than an additional synonymous spelling.

**What can be reused, and what cannot.**

| Area | Current evidence | Consequence for implementation |
| --- | --- | --- |
| Lexical scanning | `capture_language/dependencies.rs` already has `scan_modifier_with_sigil`, shared with `!`, quoted note handling, protected spans, and leading/trailing marker extraction | Extend these primitives; do not add an unrelated regex or Swift parser |
| New-task planning | `capture/plan.rs` augments `&` task blocks before inserting them | Assign N's identity before this step, then apply reverse edges after N is staged |
| Existing dependent writes | `plan_existing_task_dependencies` resolves targets from staged contents, merges managed/legacy dependencies, checks cycles, stamps fields/status, transfers commitment, updates mirrors, and consumes links | Reuse this semantic operation with D as dependent and N as prerequisite |
| Discovery | `capture_dependency_tasks.rs` scans exact vault-relative identities, including nested notes and history | Reuse discovery and ranking, but reverse targets need different eligibility checks |
| Commit | `capture/batch.rs` composes multiple edits to one file; `capture/commit.rs` checks disk preimages and rolls back applied files on ordinary failures | Keep one capture batch across task creation, dependent edits, and daily-file edits |
| Preview | `task_blocks` reports task diffs; surviving `pomodoro_blocks` report final ledger blocks | Add explicit reporting for fully removed Pomodoros; the tracker deliberately drops them |
| Mac UI | Existing dependency picker, stale-safe ranges, block-ID prompt, and preview already exist | Reuse mechanics, while removing assumptions that every relation is `&` |

The crucial existing entry point is [plan_existing_task_dependencies](https://github.com/bobs-org/bob-cli/blob/e7e98d2e49e6c9b034e864dbbc263ffa0dbabf48/src/native/capture/dependencies.rs#L2102). It already performs the desired “make D depend on N” operation, including today's link consumption. A wrapper is preferable to reimplementing dependency merging, legacy adoption, canonical link formatting, project guards, and status derivation.

There are two reuse caveats. First, the function names its dependent using a string called `dependent_route`, whereas `*` targets can be nested, quoted, case-sensitive notes. Refactor or wrap this around a resolved note path plus block ID; do not send the selected locator through the lowercasing capture-route parser or construct a fake capture command. Second, new-task ID minting in the existing `&` path partly serves the optional BLOCKS mirror. A new task used as a prerequisite needs a block ID **even when `dependencies.blocks_lines` is false**. Reverse dependency creation must not depend on that display setting.

**Ledger removal is the main issue in the original requirements.**

The intended scope should be today's **open** Pomodoros, including the running session and future placeholders. Completed sessions, struck/`🍅` history, other days, dependency lines, and incidental references in prose should remain historical/contextual content. Remove every matching planned occurrence, rather than only the first. Resolve the task identity structurally so supported link spellings are handled correctly; raw substring matching is insufficient for aliases, local links, embeds, and code.

The existing [consume_live_links](https://github.com/bobs-org/bob-cli/blob/e7e98d2e49e6c9b034e864dbbc263ffa0dbabf48/src/native/capture/project_deps.rs#L266) invokes two broader helpers:

- [plan_link_removal](https://github.com/bobs-org/bob-cli/blob/e7e98d2e49e6c9b034e864dbbc263ffa0dbabf48/src/native/capture_task_toggle/links.rs#L160) removes a link-only bullet **with its entire child subtree**. For other lines, its lower-level remover strips matching link substrings. It is not confined to the dedicated planned Task Link shape.
- [plan_empty_pomodoro_removals](https://github.com/bobs-org/bob-cli/blob/e7e98d2e49e6c9b034e864dbbc263ffa0dbabf48/src/native/task_status_hooks/pomodoro.rs#L287) checks every scanned entry with no child. It does not require that this operation affected the entry, that it was previously nonempty, or that it is open.

I reproduced the combined behavior with an existing Next task Ship, an open prerequisite Seed, and this daily fixture:

```markdown
## Pomodoros
- [ ] () — AFFECTED
  - [[work#^ship]]
    - Preserve my notes
- [ ] () — UNRELATED
- [x] (0900-0925) — HISTORY
```

Running `bob capture '&seed:seed @work+ship'` with the synthetic vault and `BOB_DAY_FILE` pointing to the fixture succeeded. Ship became Blocked, Seed rose to Next, and the daily file became just:

```markdown
## Pomodoros
```

Thus the target's authored notes, the unrelated empty planned entry, and the unrelated empty completed entry all disappeared. The preceding dry run succeeded and left every fixture file byte-identical, but its result warned only that one live link was removed. There was no `pomodoro_blocks` array displaying the deleted entries. The source explains that omission: [PomodoroBlockRef::removed](https://github.com/bobs-org/bob-cli/blob/e7e98d2e49e6c9b034e864dbbc263ffa0dbabf48/src/native/capture/pomodoro_blocks.rs#L93) prevents a deleted entry from appearing in final block output.

This is stronger evidence than a hypothetical cleanup concern. It does not mean `*` is a bad feature; it means blindly calling the current cleanup helpers would inherit behavior broader than “delete the Pomodoro iff it becomes empty after removing that task link.”

**Explicit adjustments to the requested requirements.**

1. **Limit cleanup to live planning links in today's open sessions.** “Today's daily file” alone is too broad because it also holds completed work and context. Missing today's file should be a successful no-op for cleanup, without creating an empty day file. Existing unreadable or unwriteable required files should make submission fail, rather than silently promising a cleanup that did not happen.
2. **Delete only affected Pomodoros that become empty because of this capture.** An unrelated preexisting empty placeholder or completed entry must survive. Evaluate emptiness after all edits belonging to the capture item, including insertion of a requested link for N. A remaining note, child, or log means the session is not empty; “no remaining Task Links” alone is insufficient.
3. **Preserve authored descendants of a removed Task Link.** My preferred behavior is to replace a link-only bullet that has authored children with an ordinary text heading bullet, such as `Notes for Publish`, keeping its children unchanged. An isolated link-only bullet with no children is deleted. This is a deliberate proposed change from dependency contract §13.5's subtree deletion rule, not a claim about current behavior. If preserving notes is deferred, refuse that affected capture before writing and identify the note location; silently deleting the notes is the wrong fallback. Updating this rule for all capture dependency consumption would give `&` and `*` consistent behavior; plugin parity would be a separately coordinated change.
4. **Make N's identity mandatory but automatically allocated when absent.** The user should not have to type a block ID to use `*`. Reserve a collision-free ID in the staged batch, preserve an explicitly requested ID, and use the existing identity rules. This ID is needed independently of the BLOCKS mirror.
5. **Start with actual new-task captures.** Support ordinary tasks, explicit-ID tasks, and new Pomodoro-linked tasks, plus multiple `*` targets and mixed `&`/`*`. Reject reverse modifiers on existing-parent/sub-bullet captures, pure link/toggle actions, references, section bullets, project-note construction, and session operators with a teaching diagnostic. The request specifies a new task; accidentally applying `*` to an existing `@note+id` parent would expand the meaning. A later existing-blocker editing gesture can reuse the same internal operation without making the first release ambiguous.
6. **Keep established commitment and recovery policies.** The existing `&` writer transfers the dependent's prior Next/Pending commitment to open prerequisites. Reusing it means N may rise to Next/Pending, even without a Pomodoro link. Preserve that behavior and show it in preview. Do not automatically put N in D's vacated session, lower unrelated lanes, or auto-link D when N closes.

The first two adjustments narrow deletion to the requested cause. The third protects recorded content and explicitly revises an existing contract. The remaining adjustments settle unspecified identity, scope, and status behavior.

A running timed Pomodoro may still be deleted when it is affected and truly becomes empty. That is already accepted in dependency contract §13.5; I would retain it rather than add an exception that contradicts the requested `iff`. Show the session name and time range in the preview. Preserved notes mean it remains nonempty.

**Grammar and completion contract.**

Use the same extensionless vault-relative identity grammar as `&`: exact paths first, otherwise a unique basename; quoted note components preserve whitespace, punctuation, Unicode, and case. Reject absolute/traversing paths, missing tasks, duplicate block IDs, malformed managed dependency lines, and terminal dependent targets. Completed prerequisites are meaningful for `&`; completed tasks are not meaningful editable dependents for `*`, so the same discovery pool needs direction-specific disabled reasons.

| Draft | Recommended interpretation |
| --- | --- |
| `Prepare credentials *release:publish` | Create N; Publish depends on N |
| `Prepare credentials *release:publish *ops:deploy` | Two independent dependents share N |
| `Prepare credentials &security:approve *release:publish` | N waits for approval; Publish waits for N |
| `Prepare credentials *"Release Plan":publish` | Quoted locator uses the same identity grammar as `&` |
| `Prepare credentials *`, `Prepare credentials *rel`, `Prepare credentials *release:` | Incomplete picker state; execution refuses |
| `*release:publish` | Incomplete owner; ask for new-task text |
| `Prepare credentials \*release:publish` | Literal token; consume the escape as with `\&` |
| `Compute 2 * 3`, `*emphasis*`, `**bold**`, `a*b` | Literal Markdown/prose, not relation modifiers |
| `=x1*2`, `=x*2`, `==*` | Existing session syntax keeps its established interpretation |

Do not merely change a scanner's `&` check to “`&` or `*`.” The existing [authored-line classifier](https://github.com/bobs-org/bob-cli/blob/e7e98d2e49e6c9b034e864dbbc263ffa0dbabf48/src/native/capture_language/draft.rs#L444) recognizes `* ` as a child bullet marker, and the session grammar uses `*` to park tasks. Preserve those contexts before modifier extraction. Protect wikilinks and code as today, and keep ordinary balanced emphasis and repeated-star tokens literal. A standalone unfinished star at an item end can open the picker; a recognized Markdown child bullet must retain precedence. These are real syntax collisions: CommonMark uses `*` for both [list markers](https://spec.commonmark.org/0.31.2/#list-items) and [emphasis](https://spec.commonmark.org/0.31.2/#emphasis-and-strong-emphasis).

Shell examples should quote the whole draft: `bob capture 'Prepare credentials *release:publish'`. An unquoted `*` participates in zsh filename generation and can expand or fail before Bob receives it. This follows the [zsh expansion manual](https://zsh.sourceforge.io/Doc/Release/Expansion.html#Filename-Generation); no shell behavior belongs in the capture parser.

For internal Rust types, use an explicit relation direction and resolved task identity. Share note scanning, extraction, query decoding, replacement formatting, ranking, and graph validation. For the external JSON contract, keep existing `dependencies` entries describing `&`; do not silently place inverse relationships into a field older clients interpret as prerequisites.

One suitable additive contract is:

- Per-item `blocks` lexical entries and `blocker_target`, analogous to existing dependency entries/ownership.
- Distinct completion context/need `task_blocking`, and spans `blocking_sigil`, `blocking_note`, `blocking_block_id`.
- Backend-formatted `*...` replacements, including an additive `blocking_replacement` in `capture-task-id` responses for ID-less selected dependents.
- A `blocking_update` summary containing the resolved blocker and an array of per-dependent changes; the current singular `dependency_update` cannot describe several existing dependents.
- Structured removed-link and `removed_pomodoros` details, with original session identity and before content. Retain the existing final-state `pomodoro_blocks` contract rather than pretending a deleted session has a final headline.

These names are proposals, not current interfaces. Adding optional fields does not require changing schema version 1. Existing fields and meanings should stay stable.

**Recommended planning sequence.**

1. Parse the whole draft using the shared grammar. Resolve and deduplicate `*` targets by actual note/block identity, not typed locator text. Validate that each is an editable open task.
2. Determine N's destination and allocate/reserve its block ID before planning its `&` modifiers. This makes N a real graph identity even in a mixed-direction item.
3. Run normal new-task planning, including schedule, authored children, project guards, outgoing prerequisites, and any explicitly requested Pomodoro linking. Stage N's note block; do not write it to disk yet.
4. For each selected D, invoke the shared existing-dependent operation with a single prerequisite N. Read the latest staged contents on each pass so same-note captures, multiple dependents, ID projections, and BLOCKS mirror updates compose. Accumulate all task touches and dependency summaries rather than keeping only the last one.
5. Plan the narrowed ledger cleanup against the complete item state. Retain notes, record affected sessions, and remove only those affected open sessions that become empty. Combine this into the same staged daily file.
6. Produce preview from those same staged results. Commit through the existing writer once every item succeeds; refresh the Mac agenda after successful submission.

The shared cycle checker examines new edges, staged edges from earlier items, and implicit project relationships. Keep that behavior: `N &D *D` is a cycle and must leave the entire vault unchanged; an existing path N → … → D also forms a cycle when adding D → N. Include cycles involving project residence and descendants, not only explicit task links.

If a selected D is a recognized project's `^prj`, reuse `&`'s project-dependent policy: reject N inside that project or its descendants, block/tag the immediate residents, consume their live planning links, and transfer commitment as established. A blocker captured inside the project it blocks would otherwise deadlock itself. Current capture writers leave descendant-project cascades to reconcile; the Task Card has a broader immediate subtree pass. Preserve that distinction and report the project impact. Do not run whole-vault reconcile after every capture to conceal it.

Multi-item capture remains ordered. A later explicit link gesture can deliberately remove D's own open prerequisites under the accepted capture dependency-drop policy, including an edge added by an earlier `*` item. Do not invent a special undeletable dependency for `*`. Make the final preview/results accurately disclose the subsequent drop, and test this sequence; an earlier summary must not misleadingly claim the final task remains blocked.

The writer provides staged composition, preimage checks, temporary replacements, and rollback for ordinary failure paths. It does **not** provide cross-process serializability or crash-atomic multi-file transactions, as [its own guard documentation states](https://github.com/bobs-org/bob-cli/blob/e7e98d2e49e6c9b034e864dbbc263ffa0dbabf48/src/native/capture/commit.rs#L138). Reuse that existing guarantee rather than introducing a second write path or promising stronger atomicity. Edge deduplication is also not whole-command retry idempotency: repeating a plain new-task capture can create another blocker. No new retry protocol is required for this feature.

**Mac app work is more than decoding a field.**

Keep Bob as the only semantic authority, consistent with `mac-capture-is-a-thin-client`. Swift should render direction, spans, replacements, and mutation effects returned by Bob, then submit the aggregate draft once. It should not reverse-engineer edges or read/write vault notes.

The concrete files to extend are:

| File in bob-mac-capture | Work needed |
| --- | --- |
| `Sources/CaptureCore/CaptureModels.swift` | Decode additive lexical, completion, summary, replacement, and cleanup fields with backward-compatible defaults |
| `Sources/CaptureCore/DependencyPickerPresentation.swift` | Reuse ranking/rows with direction-specific labels, prefixes, repeated-target continuation, disabled history, and accessibility copy |
| `Sources/CaptureCore/CapturePickerPresentation.swift` | Add source/chip/keyboard routing for the new completion context |
| `Sources/BobMacCapture/CapturePickerState.swift` and `CapturePanelModel.swift` | Preserve relation direction through stale-safe completion snapshots, selection, chip reopening, ID prompts, cancellation, and follow-up submission |
| `Sources/BobMacCapture/CapturePickerView.swift` | Display `Blocks` / `Tasks blocked by this capture` rather than the prerequisite header |
| `Sources/BobMacCapture/CapturePanelView.swift` | Show all blocked tasks, status changes, removed links/sessions, preserved notes, and project impacts |
| `Sources/CaptureCore/CompletionRowContent.swift` and editor presentation | Recognize new semantic span/context names and render their meaning consistently |

The existing [picker presentation](https://github.com/bobs-org/bob-mac-capture/blob/060d77b41a79df7b529c9085f184b76928c0cbbb/Sources/CaptureCore/DependencyPickerPresentation.swift#L290) hardcodes `&` in insertion prefixes and “space adds another &” copy. The [ID-prompt acceptance path](https://github.com/bobs-org/bob-mac-capture/blob/060d77b41a79df7b529c9085f184b76928c0cbbb/Sources/BobMacCapture/CapturePanelModel.swift#L5519) specifically consumes `dependencyReplacement`. Reusing those paths unchanged would either show the wrong direction or turn an ID-less `*` selection into `&`.

Selecting/highlighting rows stays read-only. The existing explicit Add block ID prompt is a separate preparatory write; if used for a selected D, canceling the later draft may leave that explicitly assigned ID. Preserve and document this existing distinction rather than claiming every interaction before submission is side-effect-free. N's automatically allocated identity should remain purely staged until submission.

Version compatibility needs deliberate handling. My installed `bob capture-parse -f json -- 'Fix prerequisite *work:ship'` returned mode `task`, preserved the star token in `body`, and emitted no relation spans or diagnostics. Thus an older backend can accept the draft as a plain task while failing to create the intended relation. Schema version 1 alone does not prove support. Publish the feature with a compatible Bob build, preferably advertise an additive capability from Bob, and only offer the reverse picker when it is present. Show unsupported-backend guidance rather than inventing a Swift grammar. Raw manually typed `*` with an older Bob remains a compatibility limitation unless the updated app enforces a minimum backend build; hiding the picker alone cannot guarantee otherwise.

**Validation that should gate implementation.**

Existing tests provide good starting points: `tests/cli/capture/parse_dependency.rs`, `complete_dependency.rs`, `blocks.rs`, `batch.rs`, the capture commit unit tests, and the Mac dependency picker/model tests. Add behavioral coverage where the new direction or cleanup contract matters:

- Lexical parity for complete/partial/quoted/escaped markers, mixed `&`/`*`, authored child bullets, Markdown emphasis, wikilinks/code, and the existing `=x*` operators; UTF-8 replacement ranges must round-trip in Rust and Swift.
- Same-note, cross-note, nested/case-sensitive targets; several targets in one item; duplicate aliases of one target; preserved existing dependencies; malformed/duplicate managed lines; missing, duplicate-ID, terminal, and otherwise uneditable targets.
- Automatic N identity with mirrors enabled **and disabled**, explicit-ID preservation/collision, and exactly one N shared by all chosen dependents.
- Direct, transitive, cross-item, mixed-direction, same-project, and descendant-project cycles. Assert byte-identical vault contents on failure.
- Link cleanup in current and future open sessions; duplicates; a session with another task; a session with notes; descendants retained; affected empty timed/placeholder entries removed; unrelated preexisting empty and completed entries preserved; struck history, fenced code, contextual links, and other days untouched.
- N linked into D's existing session in the same item: the surviving N link keeps that session nonempty. Also test creation of N in today's file itself, because task and ledger changes then share one staged path.
- A later explicit dependency-drop gesture in the batch, and final preview accuracy for the surviving relationships and agenda.
- Dry-run leaves all notes byte-identical; live execution matches the planned semantic changes; stale preimages/write failures roll back without leaving a new task, partial edges, or partial ledger removals.
- Mac direction labels, repeated picks, ID-less targets, prompt cancel/return, stale snapshots, full removal previews, agenda refresh, and older-backend behavior.

For Mac validation, follow its repository instructions: run `just portable-check`; compile changed AppKit/SwiftUI targets in a scratch copy on the Mac using `bundle.sh` and `just typecheck-tests`, with macOS CI running XCTest. Portable checks alone cannot establish that the app targets compile. This research did not make Swift changes or perform those implementation checks.

**Recommended solution.**

Implement `*note:block-id` for new-task captures as a direction-aware front end to the existing staged Depends-On writer. Give the new task a stable identity, stage it first, then add it as a prerequisite to each selected open dependent, preserving established cycle, project, status-transfer, mirror, and recovery rules. Add distinct additive parse/completion/summary fields and extend the Mac picker with explicit `Blocks` wording and backend-formatted replacements.

Before shipping, narrow capture ledger cleanup to affected open Pomodoros, preserve authored notes, and expose fully removed sessions in dry-run/Mac preview. These adjustments address a reproduced deletion problem and make the user's `iff empty` requirement precise. Keep both task and daily-file edits in the existing single capture batch, avoid whole-vault reconciliation or a second dependency store, and keep automatic replacement planning out of scope. With that contract, this is a worthwhile capture feature with a manageable implementation path.
