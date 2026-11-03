# Moving parent tasks into a project created by capture

Independent research and design recommendation — **cdx** — 2026-11-03

## Recommendation at a glance

**Adopt the proposed `- ^some-id` syntax, narrowly scoped to first-level bullets in the same project-creation item. Make it an explicit move of an existing task block.** Keep `- New task ^some-id` as the existing operation that names a newly authored task. Offer a parent-scoped task picker immediately on `^`, show task titles rather than requiring remembered IDs, and make the preview say exactly what moves from where to where.

This is a good feature: creating a subproject often means discovering that several existing tasks belong together. Doing that in one draft is substantially better than creating the project, finding it again, and moving tasks individually. The important engineering work is preserving task identity and composing the move with project creation. Parsing the token is comparatively small.

Do not call the new UI action “pull in.” Bob already uses that phrase for selecting tasks to link into today's Pomodoros. Use **Move from parent**. Movement and choosing today's work must remain separate intentions.

This report proposes behavior; it does not implement it. I researched independently and did not inspect the other swarm researchers' reports, messages, or findings.

## Evidence and confidence

I inspected these checkouts, with revisions recorded so the findings remain checkable:

| Repository | Revision | Scope inspected |
| --- | --- | --- |
| bob-cli | `020a1f6da021513bc60abdcbda7a4d9ab606fb90` | Grammar, project renderer/planner, completion, move planner, capture batch writer, inbox routing, tests and docs |
| bob-mac-capture | `f8832b34e7c7a618f5f7e67626b091779fb9081f` | Completion dispatch, picker contracts, keyboard routing, project preview, compatibility gate |
| bob-plugins | `9b5b2857f02f441cd2920b1f7738522b2ddc8b57` | Existing task-move freshness and blocked-project behavior |

I also ran isolated, read-only probes with the installed `bob 0.4.0`, which reported **grammar 6**. Fixtures lived in a temporary directory inside this workspace and were removed afterward. No real vault was used or changed. The installed executable was not freshly built from the inspected commit, so runtime observations and source observations are distinguished below. No Swift build or visual usability test was performed.

Public references provide supporting conventions, not evidence of Bob behavior. Obsidian already uses `^` to discover blocks, supports readable IDs, and represents a block link with both note and block identity. That makes the suggested selector familiar, while also explaining why moving a task requires link repair. [Obsidian internal links](https://obsidian.md/help/links)

### What exists today

1. **Both project seals already exist, with different planning behavior.** `@foo^bar@` creates `foo_bar.md`; `@foo:bar@` creates it and offers eligible tasks for explicit selection into Pomodoros. Neither means “move parent tasks.” The parent may be an area or a nonterminal project. A trailing seal can be on a child line; item classification is not confined to the first line. [C1, C2]
2. **The proposed standalone token is currently a refused gap.** `ProjectTaskPass::check_child` strips a trailing task ID and rejects an empty remaining body. This permits adding the reference form without changing the meaning of valid `- Description ^id` captures. [C3]
3. **Completion currently opens the wrong kind of picker for this use.** `- ^` in a project item produces `project_task_block_id`, intent `new`, with the destination `foo_bar` and no task body. It names a new task; it does not search `foo.md`. [C4]
4. **There is a reusable move engine.** `task_move::plan_task_move` takes an in-memory vault snapshot and returns changed note contents, identity mappings, and repaired-link information. It moves complete blocks, repairs inbound and moved-fragment links, updates dependency identity, and validates ambiguous IDs. [C5]
5. **Capture already composes moves into a batch.** Inbox routing overlays staged capture content onto a vault snapshot, calls the move planner, and binds every returned postimage to the exact preimage used to compute it. Reuse this integration pattern. [C6]
6. **The app is intentionally a thin client.** Bob supplies syntax spans, candidate data, replacement ranges, and dry-run results. Swift dispatches and presents them. The app must not discover `foo` by searching the draft for `@` tokens or scan the vault itself. [M1, M2; accepted decision `mac-capture-is-a-thin-client`]

### Read-only probe results

The project body was `Deliver feature @foo^bar@`; the fixture parent contained `Write tests ^tests` with a child note.

| Draft variant | Observed result |
| --- | --- |
| `- ^` | Parse incomplete, `needs: [block_id]`; completion context `project_task_block_id`, intent `new`, no candidates; capture dry-run refuses unfinished ID |
| `- ^tests` | Parse diagnostic `invalid_project_task_id`; dry-run refuses “names a task but has no task text” |
| `- Write tests ^tests` | Valid new named task; project dry-run succeeds |
| `- ^` before a later child carrying `@foo^bar@` | Still classified in project context; current completion remains new-ID completion |
| `- ^` in a different blank-line item | No project-task completion; it remains ordinary child content in that other item |

Correct probe interfaces were `bob capture-parse --format json` with stdin, and `bob capture-complete -b FIXTURE -f json -c UTF8_OFFSET -- DRAFT` / `bob capture -b FIXTURE -f json --dry-run --no-clip -- DRAFT`. The fixture byte comparison passed after the dry runs.

## Proposed user experience

Start with:

```text
Ship the vendor integration @foo^bar@
- ^vendor-call
- Write the rollout checklist ^rollout
- ^integration-tests
- REQUIREMENTS
  - Keep the old API working during rollout
```

The result is a new `foo_bar.md`, containing the two existing task blocks and one new task under `## Tasks`, **in draft order**. The requirements section retains its existing project-capture meaning. The selected tasks disappear from `foo.md`; their descriptions, original creation dates, logs, dependencies, and descendants travel with them. Links to their old locations now target the corresponding blocks in `foo_bar.md`.

The editor remains plain text. Do not insert the task description into the draft after choosing a row: `- Call the vendor ^vendor-call` already means a new task. A decoration or preview can show the resolved title without changing the submitted bytes.

A compact picker could read:

```text
Move from foo → foo_bar
Search parent tasks…

  Call the vendor                     Next
  ^vendor-call · Tasks · 3 child notes

  Verify the integration              Ready
  ^integration-tests · Testing · 1 child note

Tab / Return  Insert reference         Esc  Cancel
```

The live result should use ordinary words:

```text
Create foo_bar
Move 2 tasks from foo · Create 1 task

↳ Call the vendor                     from foo
  Write the rollout checklist         new
↳ Verify the integration              from foo

Task notes and history move with them. Existing links will be updated.
```

Counts must come from Bob. The preview should name any substantive status or ledger consequence separately. A collapsed details row can expose affected files and link repairs; it need not dominate everyday use. Long titles truncate visually with a full accessible label. Source/destination and movement must remain understandable without color or icons. Use the existing app typography, spacing, and selection treatment rather than introducing a separate visual language.

Apple's guidance supports making search scope clear, refining results while typing, and simplifying results. The particular parent-only scope and ranking below are my design choices for an operation with a fixed source. [Apple search fields](https://developer.apple.com/design/human-interface-guidelines/search-fields)

### Completion behavior

- Trigger when the caret follows `^` at an otherwise empty first-level task bullet in a resolved project-creation **item**. The seal may be earlier or later in that item. A seal in another item must have no effect.
- Show existing eligible tasks from the resolved parent, with human-readable titles as primary text. Show IDs, source section, status, and a small descendant count as supporting information.
- Search ID and description, reusing Bob's task-ranking utilities where suitable. Prefer exact ID, then ID/title prefix, then other matches; use parent document order as a stable tie-breaker. Empty search uses document order.
- Open with no row selected for a bare `^`; arrow keys or Ctrl-N/P establish selection. A nonempty query may select the best eligible match, following the existing picker conventions. Never preselect a disabled row.
- Tab or Return on a selected row inserts only the backend's `^id` replacement. Acceptance edits the draft and performs no vault write. Plain Return used to accept must not also submit the capture. Preserve existing explicit submit shortcuts and Shift/Option-Return behavior; test them with the new picker.
- Reuse the existing picker filter input for multiword search. Do not invent whitespace-bearing committed `^task title` syntax. A typed prefix is assistance, never a fuzzy move selector at commit.
- Keep already-selected tasks visible but disabled with “Already added on line 2” when searching them; omit them from the empty-query list if that makes repeated picking easier. Bob owns the exclusion and explanation.
- Escape closes the picker according to the established lifecycle descriptor. It must not remove an already accepted reference. An unfinished `- ^` remains incomplete until removed or resolved; it must never silently become an empty new task.
- Continue using ordinary bullet insertion to add another selector. A multiselect picker or “accept and add another” shortcut is optional later polish, not required for the first implementation.

The critical empty state is actionable: “No open parent tasks with block IDs.” A wrong typed ID should say “No task `^tests` in `foo`,” not quietly search the entire vault.

## Exact semantics and requirement adjustments

These are deliberate clarifications or changes to the original request.

| Area | Recommended contract | Why |
| --- | --- | --- |
| “Somewhere in this capture” | Same parsed item, including a later valid seal; never another blank-line item | Bulk captures can create several projects with different parents |
| Parent scope | The resolved route's area or project note only | Existing project creation already supports both; recursive ancestor search makes a bare ID ambiguous |
| Movable selection | Identified, open, top-level task roots, including Ready, Next, Pending, and Blocked subject to project-state guards | Matches the existing Rust move engine's principal eligibility rules |
| Unit moved | Entire existing task block, including nested tasks, drawers, logs, and non-task context | Moving only the checkbox line loses work |
| Draft position | First-level reference bullet, with no authored text, checkbox, schedule/type/priority modifier, or new child bullets | Keeps relocation separate from authoring or editing the task |
| New task IDs | `- Text ^id` and `- Text :id` retain their current meanings | No content-dependent reinterpretation of valid captures |
| Bare colon | Do not introduce `- :id` in this feature | Move-plus-link is another behavior; the existing offer form already handles choosing work for today |
| Nested selector | Refuse as a move; do not detach a nested task by its ID | Preserves source task ownership and avoids overlapping moves |
| Block-ID collisions | Refuse with an explanation; do not silently rename imported IDs | This destination is new, so conflicts usually come from editable draft choices |
| Tasks lacking IDs | First release requires an existing ID; explain unavailable rows or the empty state | Assigning IDs while browsing would make abandoned drafts mutate the vault |
| Display terminology | “Move from parent,” separate from “Link into today's Pomodoro” | “Pull in” already means something else in Bob |

Whitespace around a selector is harmless; the accepted ID alphabet remains Bob's shared ASCII letters/digits/hyphen rule. Exact commit resolution should use the existing identity rules rather than introducing a new case-folding convention. `^prj` remains reserved. Preserve existing escapes and code/wiki-link precedence so literal or quoted content is not recognized as a move.

A line with both a selector and a trailing project seal is deliberately outside the first-release standalone form. Put the seal on the parent line or another authored line. Recognizing the seal anywhere in the item does not require allowing every marker on the move line itself.

References with extra modifiers should fail clearly. They should not become bodyless new tasks after marker stripping, and a selector with nested authored notes should not cause those notes to be silently dropped. An existing source block may contain any supported descendants: the restriction is on new notes beneath the selector in this capture, not on what travels with the selected task.

**Future extension:** ID-less tasks could be selected using a stale-safe reference and assigned an ID inside the final aggregate transaction. Existing `capture-task-id` is a separate write command [C9], so invoking it merely to preview this feature would weaken its transactional behavior. Defer this unless usage demonstrates that missing IDs make the first version impractical.

## State preservation: more than copy and delete

### Identity and link repair

The logical identity is the source note plus block ID, not the ID alone. Moving `foo#^tests` to `foo_bar#^tests` changes its address even when the ID spelling is preserved.

The required repair set includes inbound task links, embeds, aliases, supported Markdown links, same-note references inside the moved block, links between two moved blocks, links back to tasks that remain in the parent, and derived dependency identifiers. Include historical notes covered by the existing move engine's vault scan; repairing a link target must preserve the surrounding historical text. Descendant block IDs matter just as much as the selected root ID. [C5]

A new task in the draft using an imported block ID must be refused. So must an imported descendant ID colliding with an authored root or `^prj`. The existing engine can rename collisions; use an explicit preservation/refusal policy for this caller rather than globally changing ordinary `bob task move` behavior.

Validate duplicates across the entire batch. Selecting the same source task twice, including in two new-project items, should fail the whole draft with both relevant item/line locations. Do not silently deduplicate movement instructions.

### Dates, freshness, status, and inheritance

Preserve original task creation dates, schedule, priority, type overrides, recurrence text, logs, and body text. Never pass imported blocks through the new-task renderer that stamps today's creation date.

A manual move is already a freshness gesture in Bob: capture inbox routing stamps the selected root, while the plugin move implementation can stamp eligible descendant task lines too. [C6, P1] I recommend following **capture's selected-root behavior** here: stamp the explicitly selected open, nonrecurring root with the shared freshness helper; leave carried descendants' freshness unchanged. This is an explicit policy choice, not a claim that both existing adapters behave identically. Do not count the move as a keep or advance decay.

Keep Next/Pending lanes and existing Pomodoro links unless derived blocking requires a change. Mere relocation must not ensure Next, release a task, or create a new Pomodoro link. Root/type/clock defaults should be evaluated through the new note's parent chain; because the new note inherits from the source parent, defaults usually remain the same, but that should be tested rather than assumed. Preserve historical clock fields and explicit overrides.

Blocked state needs special care. A new subproject can inherit an ancestor's block, gain its own scheduled date, or acquire prerequisites through capture modifiers. Determine effects from the final staged graph, not only from the parent's current checkbox. A project cannot wait on a task inside itself or its descendants. In particular, a project-level `&foo:tests` combined with moving `^tests` into that project must be rejected after resolving the relocation.

Do not call the “link an existing task” path to implement a move: that path can intentionally drop the task's prerequisites. A move must preserve them.

The Rust move planner currently refuses non-Blocked tasks entering a blocked destination and can return `needs_reconcile`; the plugin move has additional immediate blocking, prerequisite promotion, and live-link pruning behavior. [C5, P1] Reusing the pure planner alone does not reproduce the plugin behavior. Support only effects that can be correctly staged and previewed. **For an initial implementation, a clear refusal of a newly-blocking move is preferable to shipping a successful-looking move with stale active links.** Extend the shared staged state handling before broadening those cases. Moving a Blocked task within the same inherited block should remain possible when the final guard can prove consistency.

### Interaction with the two project forms

- `@foo^bar@`: move selected tasks, create authored tasks, and preserve existing live-link addresses through repair. The old promise that this form never touches the daily note no longer holds when moved tasks already have daily links. Explicitly update that documentation.
- `@foo:bar@`: perform the same moves, then apply the existing offer mechanism to the final project tasks. Already planned tasks remain already planned; hidden/blocked tasks retain the established eligibility rules. Nothing becomes linked merely because it moved. Offers use final identities, final order, and final state.

A subtle implementation trap is that selecting an offer currently changes an authored bullet's `task_id.link` and re-renders the project. Imported tasks cannot go through that path: it would treat existing material as newly authored. Apply selected offer effects to the already assembled task blocks instead. [C2]

## Backend design

Use one semantic implementation in Rust, consumed by capture, parse, completion, shell completion, and Mac presentation.

### 1. Add a real reference node

Represent the new child as a distinct variant such as `MoveFromParent { block_id, span }`, rather than `ProjectTaskId` with an empty body. Keep the selector span and item identity. Recognize this form before the generic trailing-new-task-ID pass, using raw line shape so stripped modifiers cannot accidentally make a line qualify.

Execution and editor parsing must share the classifier. Resolve a complete project seal using existing item rules before classifying its children. A lone caret should produce a purpose-specific incomplete state; a complete selector should produce move spans even before vault resolution. No vault lookup belongs in the pure lexer.

### 2. Share candidate eligibility with commit validation

Add an unambiguous context, for example `project_parent_task`, with source route, destination note, query, backend-owned replacement range, picker descriptor, and candidates. Use shared task-move eligibility instead of assuming that every row from a generic “linkable tasks” catalog can move. A task may be linkable but nested, ambiguous, or otherwise unsuitable for movement.

Candidates should carry a stable key, note path, ID, title, section, status, and a disabled reason when relevant. Include an additive capability indicating support for this operation. `initial_selection: "none"` already exists in the app's completion contract. [M1]

Keep a full-text query in the existing picker filter. Return `^id` as canonical replacement; neither display text nor the selected row index becomes commit authority. UTF-8 ranges must replace only the selector, never the bullet, nearby Unicode, or a later seal.

### 3. Compose the new note and the moved blocks

An implementation sequence should be:

1. Parse all items and collect move intents and authored task IDs.
2. At each item's turn, resolve against the capture planner's staged overlay. Earlier item changes are visible, consistent with existing bulk capture.
3. Resolve every source root exactly; validate eligibility, subtree identities, duplicates, and anticipated destination collisions.
4. Build the new project's structure and an ordered list of task slots: newly authored task or imported block.
5. Run shared relocation/identity-repair logic against the overlay, with preserved IDs and explicit target slots.
6. Assemble the final project in draft order. Keep `## Tasks` once, and suppress the placeholder when any imported or authored task exists.
7. Validate project dependencies, inherited blocking, and any state changes against the assembled postimages. Apply only supported, previewed effects.
8. Apply the project offer/link stage to final task identities without re-rendering imported content.
9. Bind all changed files to their observed preimages, finalize counts and task references, and submit one capture batch.

The move engine currently selects tasks through a line-keyed `BTreeMap` and inserts them at the destination task intake. [C5] It therefore neither follows selector order nor interleaves imported and new tasks. Extend its reusable core with explicit placement/order support or expose relocation fragments plus identity mappings. Avoid brittle “move first, find the text again, cut it out again” logic. Also avoid running a whole-vault repair scan once per selector; group moves from the same parent and repair once per coherent staged item or batch.

### 4. Keep preview and commit structurally identical

The dry run should describe operations, not manufacture generic task creation results. A proposed additive shape is:

```json
{
  "project_note": {
    "basename": "foo_bar.md",
    "moves": [
      {
        "source": {"note_path": "foo.md", "block_id": "vendor-call"},
        "destination": {"note_path": "foo_bar.md", "block_id": "vendor-call"},
        "text": "Call the vendor",
        "descendant_count": 3,
        "draft_line": 2
      }
    ],
    "created_task_count": 1,
    "moved_task_count": 2
  }
}
```

This is a design sketch, not a frozen schema. Add repair summaries, status effects, and refusal codes using existing report conventions. Define counts as selected root tasks; nested tasks are descendants, not additional selected moves.

Revalidate at submission, and preserve the draft on any error. Between picker/preview and commit, source edits must not cause a different task to move merely because a line number shifted. Stable identity plus a reviewed block fingerprint should detect deletion/reuse or a material block change. The Mac can pass backend-issued expectation data with its aggregate capture request; Bob owns its validation. Typed CLI captures without prior preview resolve the current exact identity. Do not persist preview hashes as new vault task metadata.

## Reliability boundary and recovery

**Do not describe the current capture writer as a fully serialized or crash-atomic transaction.** Its own comments say otherwise: it compares preimages, writes temporaries and backups, rechecks, replaces files individually, and rolls back handled failures. A process death or a noncooperating external writer remains a different problem. [C7]

Ordinary `bob task move` has a stronger live adapter: maintenance locking, shared write-session/recovery machinery, and scoped commits. The pure planner provides none of those by itself. Capture inbox routing reuses the planner, not that whole command adapter. [C6, C8]

For this destructive cross-note operation, retain the staged rollback guarantees and add a durable recovery record for move-enabled batches before the first replacement. Prefer adapting the existing write-session/recovery infrastructure rather than inventing a second recovery store. Record created files and before/after identities so interrupted creation, deletion, and link rewrites can be diagnosed and recovered together. Coordinate with the shared maintenance mechanism at commit, without making live completion perform sync or Git work.

This is a justified reliability addition to the original requirements. It does not mean pretending all vault writers honor one lock. Test and document remaining race limits. Do not automatically replay an interrupted move, and do not treat an already-existing destination as successful retry: it may be unrelated content or a partial previous run.

Draft Undo should restore an accepted selector as one edit. A post-submit “Undo move” button would need a backend inverse transaction that validates current postimages before restoring all files; a Swift text undo or unconditional backup restore is insufficient. Apple's undo guidance favors predictable operation names and visible results, supporting that distinction. [Apple undo and redo](https://developer.apple.com/design/human-interface-guidelines/undo-and-redo)

I would ship durable recovery with the feature, but defer an advertised post-submit undo UI until the guarded inverse exists. Routine successful capture should not require an extra confirmation dialog: explicit selectors plus a clear preview provide the confirmation context.

## Mac integration and compatibility

The Swift changes are presentation and orchestration work:

- Decode move context, capability, candidate details, and preview summaries additively.
- Add the new parse needs/spans to completion triggering. `CapturePanelModel` uses explicit sets; adding only the Rust context will not make `^` work end to end. [M2]
- Dispatch to the established task picker with the parent's scope, the move label, and server-owned replacement/cancel ranges. Do not route it through the new-block-ID picker.
- Add movement rows and summaries to the project preview and successful-capture feedback. Keep ledger offers visually distinct.
- Bind asynchronous results to draft generation, caret, item, and resolved parent/destination. Changing `@foo` to `@other` must invalidate candidates from `foo`, even when the typed `^` query is identical.
- Preserve UTF-8/UTF-16 conversion, IME handling, selection stability, VoiceOver labels, draft Undo, and ordinary editor key bindings.

The current Rust grammar constant is **6**, while the inspected Mac minimum gate is **5**; some CLI help prose still mentions **4**. Do not copy those numbers into a new design unquestioningly. [C10, M3] Use the next current grammar/capability contract at implementation time, keep optional JSON additions compatible, and test old/new combinations explicitly. A new Mac with an older Bob should explain that parent-task moves need an updated Bob; it must not invent a Swift fallback. An older Mac may reject or fail to present the new context, so additive decoding alone is not proof of a usable or safe mixed-version experience.

Ship through the existing daily CLI release train; follow the established release convention if a contract break is introduced. No version or changelog edits belong in this research task.

## Acceptance tests that matter

| Group | Required cases |
| --- | --- |
| Grammar parity | `^` incomplete; `^id` reference; text-plus-`^id` remains new; leading/trailing/later seal; both seal forms; item isolation; invalid IDs; reserved `prj`; escapes, code and wikilinks; CRLF and Unicode |
| Selector restrictions | Modifiers/checkbox/new nested notes rejected; ordinary nested new-task-ID assistance unchanged; bare `:id` unchanged/refused |
| Completion | Parent-only candidates; title and ID search; stable order; duplicate suppression; empty state; unknown, closed, nested, ambiguous, and missing-ID rows; no preview-time mutation |
| Successful movement | Original dates, metadata, drawers, logs, nested tasks and descendant IDs preserved; imported/new tasks interleaved exactly as drafted; all-imported project has no placeholder |
| Identity repair | Links between moved tasks, back to remaining tasks, outside inbound links, embeds/aliases/Markdown links, historical references, dependency IDs; collisions in roots and descendants |
| Lifecycle | Ready/Next/Pending preservation; recurring task freshness exemption; blocked parent inheritance; own scheduled project; unsupported newly-blocking move refused; project waiting on imported task rejected; existing daily links repaired |
| Offers | `^` seal creates no new links; `:` seal offers final tasks without recreating them; already-planned and hidden behavior; picks do not duplicate ledger links |
| Batch semantics | Earlier staged changes visible; later items can refer to the new location; duplicate movement across items refused; any failed item leaves all files unchanged |
| Drift and failure | Source changed/deleted/replaced after preview; repaired note changes during planning; destination appears concurrently; late write failure; interrupted process recovery; no blind retry |
| Mac behavior | Immediate caret trigger; accept versus submit; cancellation; repeated selection; stale async response; Unicode ranges; one draft undo step; accessible movement wording; old/new Bob combinations |

Use existing Rust parser/completion fixtures and capture integration tests, including failure injection. Do not claim correctness from only happy-path text snapshots. For Swift changes, follow the linked repository's build rules: portable checks plus an actual macOS scratch build and test-target typecheck; CI still supplies XCTest execution. A screenshot review in light/dark appearance and keyboard-only walkthrough should validate the visual design, not replace compilation.

## Alternatives and critique

| Approach | Assessment |
| --- | --- |
| Standalone `- ^id` in this project item | Recommended: concise, readable, fills a currently refused shape, and has a clear existing source |
| A new movement sigil such as `- >^id` | More explicit to a newcomer, but adds syntax and another completion trigger without solving identity/transaction complexity |
| A parent-task selection dialog after every project capture | Discoverable but interrupts even captures that only author new work; useful later as an optional “Move from parent” entry point that inserts the same selectors |
| Copy tasks instead | Leaves two actionable copies and breaks the user's reorganization intent |
| Insert task links or transclusions instead | Good for reference, but the tasks still reside in the parent and retain its residence-based behavior |
| Create the project, then invoke `bob task move` separately | Reuses command-level safety but creates a failure seam and two operations; acceptable manual workaround, poor product architecture |
| Search all ancestors or the whole vault | Useful future explicit qualified syntax, but unsuitable for implicit `^id` because scope becomes uncertain |

The weakness of the proposed syntax is that a caret alone does not communicate movement: in Obsidian it usually denotes identity or a link target. The move label, parent scope, resolved-title preview, and strict context are therefore core features, not optional polish. A second weakness is manual editing: adding prose before an accepted selector changes it into a new-task instruction. Keep the New versus Move preview conspicuous and do not make completion insert prose.

This is not a tiny grammar patch. It crosses a shared parser, a renderer that assumes new content, movement/identity machinery, a write boundary, and a native editor. The feature is still a good investment because the hard mechanisms largely exist. The design should reduce scope through strict selection rules rather than by weakening preservation or recovery.

## Source map

Repository references below identify inspected files and symbols at the revisions recorded above. They are primary implementation evidence; public links are only supporting UX references. Accepted SASE decisions and glossary entries were read through the audited memory interface, not by opening canonical memory files.

- **C1:** bob-cli `docs/capture.md`, “Project notes” and “Offer a new project's tasks”; `capture_language/project_tasks.rs::child_line_seals_project_note`.
- **C2:** bob-cli `src/native/capture/project_note.rs::plan_project_note_item`, especially offer selection/re-rendering and staging; `src/native/capture_project_note.rs::render_project_note`, `RenderedTask`, `project_note_basename`.
- **C3:** bob-cli `src/native/capture_language/project_tasks.rs::ProjectTaskPass::check_child`, `empty_project_task_body_error`, `lex_project_task_id`; shared execution/editor parsing in `item.rs` and `editor_parse.rs`.
- **C4:** bob-cli `src/native/capture_language/completion.rs::project_task_completion_field`, `project_task_token_at`, `project_task_block_id_detail`; `src/native/capture_complete/{engine,render,model}.rs`.
- **C5:** bob-cli `src/native/task_move/plan.rs::plan_task_move`, `select_tasks`, `validate_movable_task`, `rename_incoming_fragments`, `repair_moved_fragment`, `insert_into_dest`; preservation tests in `src/native/task_move/tests.rs`.
- **C6:** bob-cli `src/native/capture/inbox_route.rs`, move application, root freshness stamping, `destination_snapshot`, `stage_move_postimages`; `src/native/capture/batch.rs::stage_snapshot_postimage`.
- **C7:** bob-cli `src/native/capture/commit.rs::validate_disk_preimages`, `write_staged_files`, `rollback_applied_files`; `src/native/capture/mod.rs::capture`.
- **C8:** bob-cli `src/native/task_move/command.rs`, live lock/sync/write-session/commit adapter, `plan_and_apply_with_hooks`, `build_write_plan`.
- **C9:** bob-cli `src/native/capture_task_id.rs`, command purpose and stale-safe assignment contract.
- **C10:** bob-cli `src/native/capture_language/mod.rs::GRAMMAR_REVISION`; `src/native/capture_complete/cli.rs`; `tests/cli/capture/project_note.rs`; `src/native/capture/project_deps.rs`.
- **M1:** bob-mac-capture `Sources/CaptureCore/CaptureModels.swift`, `CaptureCompletionResponse`, `CapturePickerDescriptor`, `CaptureCompletionCandidate`; `CaptureProjectNotePresentation.swift`.
- **M2:** bob-mac-capture `Sources/BobMacCapture/CapturePanelModel.swift`, completion dispatch around line 4470 and needs/span sets around line 14225; `CaptureKeyCommandRouter.swift`, Return handling around line 333; `Sources/CaptureCore/CompletionRowContent.swift`.
- **M3:** bob-mac-capture `Sources/CaptureCore/CaptureGrammarGate.swift`; linked-repository `AGENTS.md` for build requirements.
- **P1:** bob-plugins `plugins/bob-navigation-hotkeys/main.js::planTaskMoveAcrossFiles`, generated implementation around lines 38066–38364. Any implementation changes there must target source fragments, not this generated file.
- **Policy constraints:** audited decisions `mac-capture-is-a-thin-client`, `capture-bullets-mirror-the-task-block`, `capture-sigils-say-where-what-how`, `task-move-never-advances-the-walk`, `task-lanes-are-sticky`, `projects-block-from-prj-line`, `subprojects-inherit-project-blocking`, `task-deps-are-depends-on-links`, and `off-clock-follows-tag-then-note-default`.

## Recommended solution

Implement **parent-scoped task moves using standalone first-level `- ^id` bullets**, with a Bob-authored picker and an explicit “Move from foo to foo_bar” preview. Preserve complete existing task blocks and their IDs, repair links in the same staged capture, and place moved and new tasks in draft order. Keep Pomodoro offers separate, refuse ambiguous or unsupported state transitions, and include durable interrupted-move recovery. Initially require existing IDs and reject selector modifiers or newly authored children. This gives the user a short, attractive interaction while putting the complexity where it belongs: in one shared backend that can explain and validate the entire result.
