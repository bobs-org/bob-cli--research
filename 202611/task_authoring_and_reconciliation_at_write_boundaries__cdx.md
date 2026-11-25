# Task-aware insertion and reconciliation at write boundaries

Independent research by **cdx**, 2026-11-25, for `bob.md#^better-o` and `bob.md#^all-ops-reconcile-tasks`.

## Judgment

Both tasks address a real problem. Bob should preserve task ownership while editing and should finish the structural work caused by its own operations. The most valuable change is **shared, scoped planning before a managed write commits**, rather than running the whole `bob task reconcile` command after every keypress.

There are two distinct objectives hiding in the request:

1. **Task-block correctness:** new tasks, requirements, notes, drawers, links, and logs land under the right owner and in the right insertion zone. This is primarily the `task_block_layout` / `bob task tidy` domain.
2. **Consistency after an operation:** lane changes, generated task groups and badges, dependency projections, and affected ledger entries agree when an operation finishes. This is part of the `bob task reconcile` domain.

Fix the insertion behavior first. Then close the gaps in managed writers in small, measurable groups. Keep explicit tidy and periodic reconciliation: raw Markdown editing, external changes, ambiguous links, and the passage of time still require repair.

The research found three reproducible editor insertion defects and a separate capture-to-reconcile gap. It also found substantial existing machinery worth reusing. This does not need a new task AST, a daemon, a new on-disk format, or a wholesale rewrite of the plugins.

## 1. What the tasks actually ask for

I read the task blocks through read-only `bob query`, filtering `bob.md` by `blockId` and task text. No vault content was changed.

`^better-o` asks for:

- Better `o` and Ctrl+Shift+O in Obsidian.
- `o` on a task headline to create a new task below the current task.
- Both commands to respect child ordering: links, requirements, drawers, logs.
- Notes on a task with requirements to live in its explicit notes drawer.
- Coordination with `bob-cli-on`, `bob-cli-pq`, and the active drawer work in `bob-cli-ph`.

`^all-ops-reconcile-tasks` asks for all Obsidian keymaps and capture-panel operations to respect the structure maintained by `bob task reconcile`, so that a subsequent reconciliation, including after morning review, needs to change fewer files. Its relation says it starts after `^better-o`.

The prerequisites have advanced since the note was written. At this observation:

| Reference | Observed state | Consequence |
| --- | --- | --- |
| `^micro-tasks` | Done in `bob.md` | Its speculative `TASK:`/`ALSO:` and hash-glyph ideas are historical, not the implementation contract. |
| `bob-cli-on` | Closed | Requirements, layout helpers, NOTES routing, and Rust/JS vectors already exist. |
| `bob-cli-pq` | Closed | The requirement diamond is already implemented; this research is about authoring and writes, not another rendering redesign. |
| `bob-cli-ph` | In progress | True-case bold drawers are the active destination. Readers have landed; several writer, UI, migration, and cutover phases are still listed in progress. |

The approved true-case drawer plan says identity remains `NOTES`, while newly created titles become `Notes` with whole-bold headers after writer rollout. Existing spellings are reused. Therefore, the new insertion code must call the drawer resolver/writer rather than hard-code either `- NOTES` or `- **Notes**`. Source: audited `sase bead read` of the three epics and `sase artifact read plan:202611/true_case_drawers.md`.

## 2. Verified current behavior

### 2.1 `o` is line-aware, not task-aware

The cycler maps normal-mode `o` to `handleVimOpenLineBelow`. That handler reads only the cursor line, obtains `getOpenLineBelowPrefix`, and inserts immediately after that line. The prefix helper returns `- [ ] ` for any checkbox line; it does not distinguish a real task from a requirement and does not include the configured task filter.

I invoked the actual bundled plugin through its existing Node test harness. Given:

```markdown
- [ ] #task Parent ^parent
    - [ ] Criterion
    - NOTES
        - Evidence
- [ ] #task Next ^next
```

`o` on the parent produced this shape, with the original tab indentation preserved in the actual reproduction:

```markdown
- [ ] #task Parent ^parent
- [ ] 
    - [ ] Criterion
    - NOTES
        - Evidence
- [ ] #task Next ^next
```

Two consequences matter:

- The new row is not a Bob task because it lacks `#task`.
- The original descendants now follow the new sibling row. Their structural ownership has changed even though the user only asked to add a task.

Adding `#task` to the prefix alone would fix only the first defect. It would still transfer the original children to the newly inserted task.

Evidence: [`010-core.js`](https://github.com/bobs-org/bob-plugins/blob/876782fed9878db3a1f3db5f0c33bb8ed4d6ab7d/plugins/task-status-cycler/src/010-core.js), `getOpenLineBelowPrefix`; [`140-plugin-vim.js`](https://github.com/bobs-org/bob-plugins/blob/876782fed9878db3a1f3db5f0c33bb8ed4d6ab7d/plugins/task-status-cycler/src/140-plugin-vim.js), `handleVimOpenLineBelow` around line 766.

### 2.2 Requirement continuation can transfer child notes too

With a requirement containing a nested evidence note, `o` on the requirement inserts its sibling immediately after the requirement headline, before its subtree:

```markdown
- [ ] #task Parent ^parent
    - [ ] Criterion
    - [ ] 
        - Evidence
    - [ ] Second
```

The evidence is now under the new requirement. Existing continuation tests check an open checkbox and indentation, but their example requirement has no descendants. All **15 tests** in `scripts/test-task-status-cycler-req-typing.cjs` passed unchanged during this research. That is evidence of a coverage gap, not evidence that the insertion behavior is correct for complete blocks.

This strengthens the case for treating task and requirement boundaries structurally, rather than making a one-line special case for `#task`.

### 2.3 Ctrl+Shift+O bypasses the notes home

The physical Ctrl+Shift+O handler and command path reach `handleVimOpenChildBulletLineBelow`. It inserts one tab-indented plain bullet directly after the cursor line. On a task containing Depends-On, requirements, NOTES, and a Work Log, it creates:

```markdown
- [ ] #task Parent ^parent
    - 
    - ⛓️ **DEPENDS ON:** [[#^dep]]
    - [ ] Criterion
    - NOTES
        - Evidence
    - 🛠️ **WORK LOG**
        - history
```

Once text is typed, this is a loose task note before the managed links, outside the existing notes drawer. The key handlers do not call the layout twin. They also always use the configured child-bullet indent constant rather than the task layout's existing-child/dominant-indent rule.

The physical dispatch already prevents duplicate handling of the same event through window and document capture listeners. Preserve that behavior. Both dispatch routes must call the same replacement planner.

Evidence: [`150-plugin-commands.js`](https://github.com/bobs-org/bob-plugins/blob/876782fed9878db3a1f3db5f0c33bb8ed4d6ab7d/plugins/task-status-cycler/src/150-plugin-commands.js), `handleOpenChildBulletLineCommand`, `dispatchChildBulletEvent`, and `getChildBulletKeydownDirection`; `140-plugin-vim.js`, `handleVimOpenChildBulletLineBelow`.

### 2.4 Capture leaves a measurable reconciliation delta even with correct insertion

I used installed **bob 0.6.0** against a temporary fixture vault, with the clock pinned to `2026-11-25 10:00:00 UTC`. This was separate from the real vault.

1. Create an area note with one Next task under `## Tasks`, a minimal daily note, and compatible Tasks settings.
2. Reconcile it once, creating the generated group and badge row.
3. Verify a second dry-run has no grouped sections or other repairs.
4. Run `bob capture -- '@work New item'`.
5. Run `bob task reconcile --dry-run --format json`.

Capture correctly added a Ready task to the intake. However, the stored badge still said `0 open`. The next reconcile reported:

```json
{
  "path": "work.md",
  "open": 1,
  "next_and_in_progress": 1,
  "moved_block_count": 0,
  "moved_blocks": []
}
```

This is pure generated-metadata debt: there was no task to move, but another file write was still needed. Counting only moved tasks would miss it. In a dry-run, `applied_files` is empty even when a repair is planned, so that field alone is also an inadequate success metric.

The checked-out source agrees with this observation. `task_status_groups::transform` is called by reconciliation, reroll, and archive planning; the searched capture paths do not call it. The contract explicitly describes badge counts as written snapshots that capture can leave stale. See [`docs/task-status-hooks.md`](https://github.com/bobs-org/bob-cli/blob/5ab392a1ba087c6f87d8685035979498082079ed/docs/task-status-hooks.md), “Status grouping,” and [`randomize_plan.rs`](https://github.com/bobs-org/bob-cli/blob/5ab392a1ba087c6f87d8685035979498082079ed/src/native/randomize_plan.rs) around line 552 for an existing writer that already composes grouping into its write.

### 2.5 The relevant abstraction already exists

`src/native/task_block_layout.rs` provides task extents, child classification, insertion slots, notes-home selection, first-requirement filing, and explicit tidy planning. The cycler and navigation plugins have byte-for-byte JS twins, tested against Rust-owned RQ/RL/RW fixtures.

The actual canonical order is more complete than the shorthand in the task:

1. Cancel Log.
2. Managed links.
3. Requirements, each with its subtree.
4. Authored children, including nested real tasks.
5. Drawers, with the notes drawer first for requirement-owning tasks.
6. Schedule, Work, and Rotten Logs, preserving their existing relative order.

Further rules are important:

- Zero-requirement tasks keep loose notes at the existing tail slot before managed logs; their loose notes and drawers need not be globally sorted.
- Notes inside a requirement belong to that requirement and do not get moved into the task's notes drawer.
- A nested real task starts a new ownership boundary.
- A project `^prj` task's notes home is the note's `## Notes` section, not a child drawer.
- Existing hand-edited order is not invalid merely because it differs from canonical insertion order. Explicit `bob task tidy` repairs it; routine writers should not silently sort everything.

These rules are already documented in [`docs/task-requirements.md §3`](https://github.com/bobs-org/bob-cli/blob/5ab392a1ba087c6f87d8685035979498082079ed/docs/task-requirements.md) and implemented in [`task_block_layout.rs`](https://github.com/bobs-org/bob-cli/blob/5ab392a1ba087c6f87d8685035979498082079ed/src/native/task_block_layout.rs). Reuse them.

## 3. Adjustments I recommend making to the requirements

These are explicit interpretations or changes to the original brief, not claims that it already specifies them.

| ID | Recommended adjustment | Reason |
| --- | --- | --- |
| R1 | Define “below current task” as **after its entire task block**, at the same nesting level. | Immediate physical-line insertion transfers descendants. |
| R2 | A new sibling is a fresh Ready task using the configured filter and normal creation metadata; it inherits no ID, dependencies, dates, lane, freshness, priority, completion, or log history. | Copying the current task's state would manufacture intent and duplicate identity. The source task can be Done, Blocked, or Next. |
| R3 | Extend subtree-safe sibling insertion to requirements, and preserve the corresponding `O` task/requirement prefix behavior. | The same ownership defect occurs below requirement headlines. `O` already shares the prefix helper, so an `o` fix must not leave task creation asymmetric accidentally. |
| R4 | Replace the four-item ordering shorthand with the existing six-zone contract and its zero-requirement and project-root exceptions. | Otherwise the new feature would disagree with accepted behavior for Cancel Logs, nested tasks, and `^prj`. |
| R5 | “All operations” means **all Bob-managed mutations**, with an explicit inventory and postconditions. Navigation, painting, and arbitrary free typing do not trigger a global formatter. | Automatic whole-vault cleanup would surprise the user, disturb undo, and expand each gesture's failure surface. |
| R6 | Measure operation-caused repair deltas on a fixed clock and known baseline, not an unconditional promise that reconcile is always a no-op. | Unrelated raw edits, time-driven event settlement, and external changes legitimately produce later repairs. |
| R7 | Distinguish an interactive empty draft from a committed note/task. A generated empty Notes shell must be removed if that draft is abandoned unchanged. | `o` opens an editing session, while capture commits complete text. The first-note rule cannot be implemented correctly by treating a bare empty bullet as a finished note. |
| R8 | Start with task-block placement and affected-container grouping/badges; add dependency and ledger postconditions through their existing planners. | “Run everything everywhere” is an unbounded project. The first two scopes have direct evidence and reusable pure code. |
| R9 | Preserve existing manual-layout drift unless the gesture explicitly owns the transformation, such as adding the first requirement and filing loose notes. | The established contract says order is a writer rule, not a validity rule or permission to silently tidy hand edits. |

R5 does not mean abandoning comprehensive coverage. It makes coverage finite: every managed mutation must either maintain each applicable invariant or identify the precise deferred effect and why it cannot safely own it.

I would not make new tasks inherit the current generated status group. A new task should start Ready even if the cursor is on a Next or Done task. That creates an interaction between “below” and later physical grouping, addressed below.

## 4. Proposed editor behavior

Use a pure context-sensitive insertion planner, fed the current editor buffer, selection, Tasks settings, and the chosen action. Do not resolve the active row from a disk snapshot or metadata cache when the editor already has newer text.

| Cursor context | `o` | Ctrl+Shift+O |
| --- | --- | --- |
| Real task headline | New Ready sibling after the whole block, at the same indent, with the configured task filter. | A note in that task's resolved notes home. |
| Requirement headline | New Pending requirement after its whole subtree, same indent, without task fields or `#task`. | A plain child note belonging to that requirement; existing child order stays intact. |
| Task's ordinary note | Sibling note after that note's subtree; when it is a loose direct note on a requirement-owning task, use the task's notes home. | Child note under that note. |
| Note inside a named drawer | Sibling note inside the same drawer, after its subtree. | Child note inside that explicit location. |
| Drawer header | Treat opening a note as entry into that named container, using the same child-note placement as Ctrl+Shift+O. | Plain note inside that drawer. |
| Project `^prj` headline | Ordinary task-sibling creation only in a valid task container; do not manufacture another `^prj` or a second project-root row. | Route to the project `## Notes` section. |
| Managed link/log header | Never duplicate its machine-owned prefix or invent a second managed row. Route a general task-note action through the owner; specialized log/relation editing retains its existing commands. | Same owner-aware note rule, except an explicitly supported log-entry command remains separate. |
| Fence, quote, prose, unrelated checklist, unsupported selection | Preserve ordinary editor behavior outside recognized Bob structure; never infer a remote target from a transclusion or a task mention. | Preserve the existing plain-child behavior only where it is unambiguous; otherwise decline the structured action without partial edits. |

The drawer-header rule is a **proposed UX choice**, beyond the explicit headline request: a drawer is a container, so entering it is more useful than accidentally creating another drawer-level note. Coordinate this with `bob-cli-ph.7`'s Smart Enter and drawer typing. If keeping that change out of the first increment, keep drawer headers on a documented fallback and do not claim complete insertion coverage yet.

For `^prj`, resolve the actual task container from the note. If the root lives outside one, refuse sibling-task creation with a short explanation or use an existing explicit “add task” route; do not silently insert a peer project root. The common task and requirement cases should not need prompts.

A task such as this:

```markdown
- [*] #task Implement parser ^parser
    - ⛓️ **DEPENDS ON:** [[#^spec]]
    - [ ] Handles empty input
    - **Notes**
        - Confirm the error wording.
    - 🛠️ **WORK LOG**
        - *2026-11-25* — prototype
```

should keep its bytes and ownership when `o` starts the next task below its entire block. Ctrl+Shift+O should enter the existing notes drawer, preserving its spelling. The bold form here illustrates the active drawer plan's target; rollout-sensitive serialization still belongs to the shared drawer writer.

### The editing-session boundary matters

`o` does not submit a complete task. It opens a draft that the user may type, indent, undo, or abandon. Do not run grouping while the caret is inside that unfinished row.

Recommended lifecycle:

1. Plan the insertion and resulting selection from one buffer snapshot.
2. Apply one editor transaction, preserving folded subtrees and revealing the new caret.
3. Keep a small in-memory receipt for any generated draft shell, mapped through subsequent edits. This is editor state, not new vault metadata.
4. On completion of that managed authoring session, finalize its local invariants. If a generated empty note/drawer is abandoned untouched, remove only that owned shell. Never delete a pre-existing empty drawer.
5. Revalidate ownership before cleanup or grouping; if the user restructured the region, drop the receipt and preserve their edits rather than guessing.

For normal-mode `o`, leaving insert mode is a natural completion boundary. Focus changes, undo, and closing the note need explicit handling too. Prove this in a real Obsidian prototype before spreading it to more gestures.

A new Ready task drafted below a Next task may initially appear inside the Next section. On completion, group it into the correct Ready intake and keep the caret on that task. This is a **visible tradeoff**: permanent physical adjacency and canonical status grouping cannot both hold across different lanes. Prefer adjacency while authoring and correct grouping after completion; never silently give the task the wrong lane to preserve its location.

## 5. Architecture: finish affected structure inside the write

### 5.1 Share semantics; retain appropriate adapters

Build on `task_block_layout`, `task_children`, the existing requirement writers, and `task_status_groups`. Add only the missing pure editor insertion decisions and corresponding shared fixtures.

The planner should produce explicit edits, a resulting selection, affected task identities/containers, and named refusals. Offsets must be explicit: Rust uses UTF-8 byte positions while the JS layout twin documents UTF-16 positions. Test emoji and non-ASCII text rather than passing numeric offsets between languages unchanged.

Rust remains the semantic authority and owns cross-language vectors. The cycler/nav twins are already checked for byte equality by `scripts/test-task-reqs-twin-copies.cjs`. Extend that arrangement. Do not build a separate regex-only miniature parser for the hotkeys.

The UI adapter owns focus, Vim mode, selection mapping, undo, and the editing-session receipt. These are not reasons to move all task semantics into JS or to call a subprocess on each keystroke.

### 5.2 Add scoped postconditions to existing planners

Think of a mutation as:

```text
current snapshots + explicit user action
    -> semantic changes
    -> affected child placement / grouping / ledger agreement
    -> validate identities and every consulted input
    -> commit the composed result
    -> refresh presentation and finish navigation
```

This is a composition boundary, not a second pass that writes after the first pass has already succeeded.

For capture, `CaptureBatchPlanner` already tracks originals, staged contents, and read guards. Apply affected-container grouping to the **final overlay**, after the draft's items have been planned and before committing. Derive final preview/report locations from those same postimages; otherwise line numbers and preview text describe the intermediate layout. Preserve capture's one-draft transaction and failure behavior.

For Obsidian, plan against open editor buffers and apply through editor transactions. For closed notes, retain the existing guarded vault-write paths. The official [Obsidian Vault API documentation](https://docs.obsidian.md/Plugins/Vault) recommends `Vault.process()` for read-modify-write operations and revalidating the input when asynchronous work intervenes. That guarantee is per file, not an atomic multi-file transaction; keep existing guarded rollback/undo mechanisms for batches.

A CodeMirror transaction can contain several changes and an explicit resulting selection; original-document change positions and new-document selection positions have different meanings. Use those facilities deliberately instead of multiple uncoordinated replacements. See the [CodeMirror reference](https://codemirror.net/docs/ref/#state.TransactionSpec). The actual Obsidian Vim adapter and undo grouping still require integration tests.

### 5.3 Do not hide repair scope in a generic `normalize()` call

Useful effect categories include:

| Mutation family | Required local effects | Wider effects to audit |
| --- | --- | --- |
| Add task/note/requirement/drawer | Correct owner, insertion zone, first-req filing, drawer identity, no borrowed fields | Counts/group placement when task membership changes |
| Complete/reopen/cancel; lane or schedule change | Final task fields, affected generated groups/badges | Dependency/project recovery, successor offers, affected live links |
| Link/unlink/start/close/type change | Affected ledger structure and entry-name agreement | Dependency promotion, blocked-link handling, markers and task grouping |
| Edit dependencies/relations | Correct managed-zone placement and projections | Reverse links, dependent status and affected containers |
| Move/merge/split/promote/demote | Whole-subtree preservation and both source/destination structure | Identity/link repair, grouping, ledger references |
| Add Work/Schedule/Rotten/Cancel log | Contract-correct log slot and preserved authored order | Any associated lane/schedule effects |

The dependency closure can be larger than the directly edited note. “Scoped” means the semantic dependency closure, not simply “whatever files happened to be written already.” Include inputs that influenced the decision in the validation set even when they are not outputs.

Preserve existing ownership constraints: reconciliation must not retype task fields to fix entry names; removing a link must not silently lower sticky lanes; successor linking requires explicit selection; requirements are not completed by writing `[x]` into their children. Those accepted contracts were read through the decisions memory web for this research.

### 5.4 Preserve repair boundaries

A full `bob task reconcile` run also scans dependencies, recovers Blocked tasks, repairs reverse relations, cleans ledger references, settles ended off-clock events, coalesces eligible sessions, and groups notes. It uses snapshots, recovery copies, a two-second structural quiet period, and bounded retries that default to 120 seconds.

That makes it a useful repair command and a poor universal hotkey callback. It would couple typing to unrelated scans and failures, add a separate write/undo boundary, and potentially move content the gesture never touched.

Likewise, automatically calling `plan_tidy` on every touched task is too broad. Use insertion slots and the specific first-req transformation for ordinary authoring. Explicit tidy remains the tool for previously hand-authored disorder. Order is not a reason to reject all work on a pre-existing noncanonical block.

## 6. How I would narrow and sequence the work

Treat these as implementation increments with separate evidence, rather than one giant “all operations” refactor.

**First: repair insertion.** Implement the pure sibling/notes-home planner; wire both command and physical-key paths; test full task and req subtrees, nested tasks, Notes reuse, `^prj`, cancellation, selection mapping, and undo. Coordinate only the drawer-writing seam with the active drawer epic. There is no need to reopen the diamond work.

**Second: stop avoidable grouping and badge debt.** Start with capture creation and managed review/lane/close operations. Reuse the existing Rust grouping transformation and add a JS twin backed by shared grouping fixtures if no suitable plugin implementation exists. The source search found no existing grouping transformer in the inspected cycler/nav/block-id fragments, so this is real work rather than a one-line hook. Reroll's existing composition is a useful reference.

**Third: audit operation families.** Maintain a checked-in matrix of public gesture/capture route, semantic writer, applicable postconditions, fixtures, and intentionally deferred global effects. Audit the common commit paths before patching individual call sites. Expand through dependency/relation edits, link changes, moves/splits, and logs. Read-only operations are marked not applicable.

**Finally: measure real maintenance residue.** Once isolated fixtures are clean, compare reconciliation repair categories after representative morning-review sessions on controlled copies or approved observations. Use the measurements to select remaining writers. Do not infer that the largest code module is the largest source of user-visible churn.

Do not add a new public CLI command just to enable the editor. Start with internal pure functions and the current APIs. A later stateless Rust planning endpoint could reduce duplication for complex cross-file operations, but introducing it now brings buffer-overlay, offset, latency, and version-negotiation work that does not solve the basic insertion bug faster.

## 7. Acceptance criteria that actually prove the improvement

### Insertion and preservation

- `o` on a task keeps every original descendant under that original task and creates one real sibling after the full block.
- `o` on a req keeps its notes and nested reqs attached and creates a fresh Pending req.
- No new row inherits a source block ID, lane, completion date, schedule, dependency, or history.
- Ctrl+Shift+O reuses the correct notes home; no duplicate Notes drawer, no empty persistent shell from cancellation, and no task-level NOTES drawer on a `^prj` owner.
- Explicit named-drawer and requirement-note contexts retain their specific owner.
- Tabs, spaces, CRLF, EOF without newline, blank separators, fences, quotes, multiline children, and folded blocks survive.
- A duplicate physical event inserts once. Unsupported/multiple selections have an explicit, tested policy.
- Undo/redo restores exact bytes and ownership. Tests must cover the insertion gesture and the following typed text/finalization, not just the prefix string.

### Postcondition tests

For each migrated operation, begin from a fixture that is already tidy and reconciled at a fixed clock. Apply the operation through its public path, then verify both relevant task-block invariants and reconciliation output.

The strongest clean-fixture assertion is that a subsequent repair plan makes **no byte changes**. Report arrays are useful diagnostics, but neither `applied_files` on a dry-run nor `moved_block_count` alone proves this. Include badge-only rewrites, projection changes, and ledger changes.

On deliberately dirty fixtures, assert that the operation introduces no new violations and leaves unrelated authored bytes alone. Baseline debt and operation-caused debt need separate expectations. Add explicit expected exceptions for time changes and ambiguous external inputs.

Run equivalence checks across the Rust and JS pure planners, plus public-path tests so correct helpers cannot be bypassed accidentally. Capture dry-run and commit must describe the same final placement. A stale buffer, changed referenced note, disappearing target, or failed multi-file write must not leave a half-finalized result.

### Performance and UX

Record warm and cold operation latency on a representative note/vault, editor main-thread duration, files read/written, and repair bytes left behind. The local insertion path should involve no vault scan, network call, or subprocess. Set a numeric latency budget after measuring the existing path; this research does not provide a credible benchmark for the real UI.

Test in real Obsidian with Vim, Live Preview, folded children, undo, and concurrent note changes before declaring the keyboard work complete. A headless harness does not establish rendered cursor behavior or actual editor history semantics.

## 8. Alternatives and critique

| Approach | Benefit | Main problem | Assessment |
| --- | --- | --- | --- |
| Run full reconcile after every operation | Simple wiring, uses current authority | Broad reads/writes, repeated scans, separate failure/undo boundary, unrelated cleanup | Reject as the default. |
| Debounced global formatter on editor changes | Eventually catches many edits | Cursor movement, undo surprises, races, silent rewriting of authored structure | Reject; conflicts with the explicit tidy boundary. |
| Hand-patch each keymap | Fast initial fixes | Repeated parsing and placement rules drift again | Only acceptable when every patch delegates to shared helpers. |
| Rust-only RPC for all editor edits | One semantic implementation | Needs unsaved-buffer transport, offsets, capability handling, and acceptable interactive latency | Possible later for complex operations, unnecessary for the first repair. |
| Shared pure rules plus scoped write finalization | Correct at source, testable, local undo, incremental adoption | Requires honest coverage inventory and cross-language parity discipline | Recommended. |
| Remove physical status grouping and render it only | Could remove a major source of maintenance writes | Changes vault/raw-Markdown behavior and the existing grouping contract | A separate product decision, not required for these tasks. |

The idea is good if the target is **less repair debt caused by Bob itself**. It becomes a bad idea if the target is “every keystroke instantly makes the whole vault canonical.” That target is incompatible with freeform Markdown editing and encourages hidden global work.

The most subtle risk is moving tasks during active editing. The implementation must define an authoring completion boundary and restore the caret by identity/range mapping. The second is scope creep: the keyboard defect is small, while universal dependency/ledger convergence is a large cross-surface audit. Delivering the small fix should not depend on completing that audit.

## 9. Evidence, provenance, and limits

Code examined:

- bob-cli commit `5ab392a1ba087c6f87d8685035979498082079ed`.
- bob-plugins commit `876782fed9878db3a1f3db5f0c33bb8ed4d6ab7d`.
- Installed CLI behavior: `bob 0.6.0`; the temporary-vault result is identified separately from checkout-only inspection.

Additional useful implementation entry points:

- `src/native/task_children.rs`, `task_reqs.rs`, `task_block_layout/{writers,tidy,edit}.rs`.
- `src/native/capture/{batch,plan,sub_bullet}.rs` and `capture_drawers.rs`.
- `src/native/task_status_hooks/{sync,compose}.rs`, `task_status_hooks_write/{model,preflight,apply}.rs`.
- `src/native/randomize_plan.rs` and `collect_done/plan.rs` for existing compose-before-write grouping.
- `tests/fixtures/task_reqs/{vectors,layout,writes}.json` and `tests/fixtures/task_status_groups/`.
- Cycler `196-task-block-layout-twin.js`, `197-task-block-tidy-twin.js`, `198-task-reqs-writers-twin.js`; corresponding navigation twins.
- `scripts/test-task-reqs-twin-copies.cjs`, `scripts/task-status-cycler-harness.cjs`, and `scripts/test-task-status-cycler-req-typing.cjs`.

Performed: read-only task query; audited epic/plan/memory reads; source tracing; three actual-handler insertion reproductions; the 15-test requirement-typing suite; isolated CLI capture/reconcile reproduction with a clean baseline. No implementation changes, task closures, live-vault repairs, or deployments were made.

Not performed: full writer coverage audit, live Obsidian UI verification, Mac client code audit, benchmark on the production vault, or exhaustive Rust test suite. The Mac should continue to submit capture through bob; any changed preview or protocol output will need coordinated client testing during implementation. The active drawer epic can advance after these pinned observations.

This report was researched independently. No report, chat transcript, summary, or findings from the other researchers in this swarm were consulted.

## Recommended solution

Implement **task-aware `o`/Ctrl+Shift+O through the existing shared layout model**, with whole-subtree sibling insertion, fresh task identity, correct notes-home routing, and a tested interactive draft/undo boundary. Then make **managed writers finalize their affected structures before committing**, starting with capture and review operations' task groups and badges. Extend that coverage through a finite operation matrix and shared postcondition fixtures. Keep `bob task tidy` explicit and `bob task reconcile` as the authoritative repair path for external, historical, ambiguous, and time-driven changes. This addresses the demonstrated failures, reduces unnecessary maintenance writes, and preserves the user's control over authored Markdown.
