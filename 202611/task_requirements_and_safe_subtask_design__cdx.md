# Bob task requirements: a safer design than miniature tasks

Independent research by **cdx**, 2026-11-21.

**Recommendation:** build one level of **task requirements**, with an explicit marker, a quiet `##` presentation, and a review before the parent closes. Keep independently actionable work as ordinary Bob tasks. Do not resume `bob-cli-of` unchanged: its recursive checkbox model, close-before-review behavior, and defaults for older clients conflict with the revised intent.

The largest departure I recommend is **not storing requirements as native Markdown checkboxes**. An item that cannot be checked off independently should not be represented by an independently toggleable control. Keep the requested fast typing gesture as an editor shortcut, but have it produce a semantic requirement marker. This is a design recommendation, not an already approved contract.

## 1. Evidence and scope

I independently read the requested vault tasks through read-only `bob query`, the original epic through audited `sase bead read`, and its plan through `sase artifact read`. I inspected bob-cli and opened the client repositories through `sase repo open`. I did not consult other reports, transcripts, or findings from this research swarm.

| Repository | Inspected commit |
| --- | --- |
| bob-cli | `ce0dcc54cec50104991b4ad943de0566e7eba2b6` |
| bob-plugins | `983076e6882c744f36e6fa513e9c2853bd160c36` |
| bob-mac-capture | `109c30db300df4a9a161ee2152e3b4676decdeaf` |

This is design and source research. I did not modify the vault, implement the feature, run a user study, or validate a prototype on macOS. The old plan's earlier vault-scan claims are historical claims, not measurements independently repeated here. The bead still reports `IN_PROGRESS`; that does not override Bryan's explicit statement that he canceled the agent, nor establish that its phases landed.

### The task graph

At read time, `bob.md#^micro-tasks` had no Depends-On line. Its Blocks line pointed to four tasks. I followed those links and the next level rather than assuming the prompt established dependency direction:

```text
micro-tasks
  ├─ blocks better-o
  ├─ blocks micro-tasks-cleanup
  ├─ blocks no-all-caps-for-drawers
  └─ blocks tasks-parent-projects
               └─ blocks task-to-project
```

`^task-to-project` is titled “Add support for converting any project note to a task!”, despite its ID suggesting the reverse. `^better-micro-task-name` was merged into cleanup. Cleanup explicitly references `^ctrl-j-successor-jump`; I read that task and the accepted jump decision.

| Source in `bob.md` | Design intent |
| --- | --- |
| `^micro-tasks` | Explicit child commitments; successor presentation with a default closed outcome; hash marks; notes should not become tasks during project promotion. |
| `^micro-tasks-cleanup` | Better name, possibly “task requirement”; links → requirements → drawers → logs; NOTES when requirements exist; no independent completion; optional cancellation reason; hide checkbox; replace `..` with bracket-space expansion and reversible Backspace; one level; Ctrl+J. |
| `^better-o` | `o` on a task headline inserts a sibling after its block; insertion respects structural ordering. |
| `^no-all-caps-for-drawers` | Drawer identity should eventually be explicit instead of inferred from capitalization. |
| `^tasks-parent-projects` → `^task-to-project` | Future task/project containment and project-to-task conversion. The notes do not specify complete identity, blocking, or lifecycle rules. |

The cleanup is a semantic revision: “steps I can tick while working” became “requirements that close with their parent.” It should replace the old plan's foundation, not be implemented afterward as cosmetic cleanup.

## 2. Is this a good idea?

**Yes, if it separates scope, notes, and independently executable work.** Bob already has substantial task machinery: lanes, freshness, dependencies, Task Links, completion, and promotion. Replicating that machinery on every little bullet would make review noisier and create another project hierarchy.

| Concept | Question it answers | Example | Own lifecycle? |
| --- | --- | --- | --- |
| Note | What should I remember? | “The old exporter truncates accented names.” | No |
| Requirement | What am I committing this task to deliver? | “Accented names survive export.” | Resolved with the owner, or explicitly removed from scope |
| Task | What work should I choose, schedule, or complete independently? | “Investigate the export library's encoding.” | Yes, through existing Bob behavior |

An imperative requirement such as “Add regression coverage” is acceptable. This is a personal work tool, not a formal specification language. The boundary is independent management, not grammatical purity.

“Micro task” is a poor name because size says nothing about behavior. “Subtask” normally suggests independent completion. **Requirement** fits the cleanup's rule; use the full word in UI labels, with “req” as informal shorthand. Keep “subtask” for genuine nested or embedded Bob tasks already discussed in Bob's contracts.

There is a real cost: requirements do not show partial execution progress. Someone wanting to tick five packing steps will find them less satisfying than a checklist. If that is the principal use case, choose a conventional checklist and relax the no-independent-completion rule. My recommendation follows the cleanup's more specific intent.

### External precedents

Things distinguishes small goals with checklists from larger goals with project tasks, and supports conversion from checklist items into project to-dos. This supports a cheap escape from local detail into independent tasks. It does **not** validate non-checkable requirements: Things explicitly allows ticking checklist items while working. [Things support](https://culturedcode.com/things/support/articles/8491676/)

OmniFocus's documented action groups can complete manually or with their last action. This illustrates that containment and completion policy require an explicit contract, not that Bob needs a configurable recursive hierarchy. The inspected manual is version 4.3.3, not a claim about the newest release. [OmniFocus manual](https://support.omnigroup.com/documentation/omnifocus/universal/4.3.3/en/print/)

Todoist's recurring-subtask documentation describes explicit reset behavior, including a limit and different treatment of deeper descendants. Recurrence introduces template, occurrence, and child-state decisions; it is not simply “reset the boxes.” [Todoist reset documentation](https://www.todoist.com/help/todoist/features/reset-a-sub-task-in-todoist-V6SRBGPw0)

These are product precedents, not controlled evidence that one approach improves productivity. The proposed fit should be tested on Bryan's own tasks.

## 3. Critique of the original epic

Retain the old plan's explicit distinction between notes and commitments, reuse of split/promotion, shared fixtures, and Mac thin-client architecture. Change these foundations:

1. **Review must precede closing.** The plan says the Obsidian owner is already closed when its card opens. Escape leaves child bytes untouched, but readers infer they resolved with the owner. On Mac, Escape leaves the draft unchanged. Similar cards therefore have different cancellation semantics.
2. **State does not require a checkbox.** The old plan explicitly makes that inference. The cleanup's non-checkable requirement is better expressed directly.
3. **One level invalidates recursive merge.** The original merge turns a source title into a micro task and carries its children another level down. Rendering everything as `##` would hide, not solve, that contradiction.
4. **Title hashes are poor choice identities.** A title hash plus duplicate ordinal cannot reliably preserve the intended staged choice after duplicate rows move. A preimage permits safe refusal, not stable identity.
5. **Older clients must not silently accept new obligations.** The original client fallback applies Done defaults. Unsupported clients should preserve content and require a supported review path.
6. **Unfinished, waived, and extracted are different outcomes.** Intentionally removing scope is not failed work. Turning work into another task is not completing it. Labels and receipts should describe the actual outcome.

The following are explicit changes or qualifications, not claims that Bryan already approved them:

| Requirement or old-plan choice | Recommendation | Reason |
| --- | --- | --- |
| Rename micro tasks | **Keep:** requirements | Matches cleanup semantics. |
| One level, `##`, no visible checkbox | **Keep** | Compact, predictable outline. |
| No completion before parent | **Keep for managed gestures** | Scope acceptance belongs to the owner; raw Markdown stays editable. |
| Native checkbox storage | **Change:** explicit plain-bullet marker | Avoid generic checkbox controls and pasted-checklist ambiguity. |
| `- [ ` expansion and Backspace | **Keep gesture; change canonical bytes** | Fast entry without persistent checkbox semantics. |
| Default Done at closing | **Qualify:** stage Satisfied in a visible precommit review | Finish accepts displayed defaults; opening or dismissing writes nothing. |
| NOTES with requirements | **Keep on authored writes** | Stable ordering without background vault churn. |
| Every merge creates micro tasks | **Defer automatic conversion** | Cannot preserve every task tree in a one-level model. |
| Any project can become a task | **Defer; validate representability later** | Dependencies and independent histories cannot always become requirements. |
| Tasks can parent projects | **Separate design** | Affects root traversal, blocking, relocation, and lifecycle. |
| Heuristic migration of imperative prose | **Replace with opt-in conversion** | Wording alone is not proof of a commitment. |

## 4. Representation

### Recommended canonical form

Prototype a dedicated inline field on a **plain bullet**:

```markdown
- [ ] #task Ship CSV export ^csv-export
    - ⛓️ **DEPENDS ON:** [[#^pick-format]]
    - [req:: active] Accented names survive export ^req-utf8
        - Include composed and decomposed accents in the examples.
    - [req:: active] Empty results produce a valid file ^req-empty
    - NOTES
        - The old endpoint returned JSON.
    - 🛠️ **WORK LOG**
        - Investigated the current endpoint.
```

`[req:: active]` is proposed syntax, not existing Bob syntax. It is deliberately explicit in source and quiet in the rendered view. Parse it only at the start of a plain direct-child bullet under an eligible Bob task, outside code, quotes, drawers, and managed lines. The same text elsewhere must not acquire requirement semantics.

Requirements can have ordinary explanatory child bullets, but no requirement children. Nested markers produce a diagnostic; never flatten, promote, or discard text automatically. Existing real `#task` children retain their current semantics.

New requirements get stable note-local block IDs using existing collision checks. These are addresses for editing and provenance, not task identities: no dependency `[id::]`, no Task Links. For an ID-less handwritten requirement, use a snapshot-bound locator and mint an ID only during a confirmed write. Duplicate IDs refuse writes; duplicate titles are allowed.

### Alternatives and tradeoffs

| Representation | Strength | Cost | Verdict |
| --- | --- | --- | --- |
| Native `[ ]` without `#task` | Familiar Markdown, compact source | Independently toggleable; generic task readers may see it; ambiguous pasted checklists | Appropriate for actual checklists |
| Explicit field on plain bullet | Unambiguous opt-in, no native checkbox, explicit state | Custom parser and decoration; noisier source | **Recommended for requirements** |
| Stored literal `##` | Resembles desired visual | Heading ambiguity and coupling presentation to grammar | Avoid |
| Every child a real `#task` | Existing lifecycle machinery | Review overhead and unwanted independence | Use when independence is intended |

Obsidian documents that task-list checkboxes can be toggled in Reading view and that non-space status characters count as completed in its basic Markdown rendering. Hiding a checkbox does not remove its control semantics. [Obsidian syntax](https://obsidian.md/help/syntax)

Bob also has concrete exceptions to ordinary tag filtering: `complete_task_tree` clears the global filter for lookup, and `finish_close_node` changes the checkbox before checking whether to add completion metadata. Thus “no `#task`, so no writer can touch it” is false as a universal assumption. This is a compatibility hazard to audit, not a claim that every direct child currently closes. [Tree completion source](https://github.com/bobs-org/bob-cli/blob/ce0dcc54cec50104991b4ad943de0566e7eba2b6/src/native/task_complete/tree.rs#L770)

An explicit marker does not make older Bob safe automatically: old promotion can still treat a plain child as a task. Capability gates are needed under either representation.

If Bryan strongly prefers native checkbox source, retain it only with an explicit requirement discriminator and a comprehensive writer audit. Document that non-completion is a Bob UI rule, not a guarantee about generic editors. Do not introduce an automatic fixer that fights external edits.

### Authoring

In an eligible task-child position, `- [ ` invokes a Bob-authored rewrite to the canonical requirement marker and renders immediately as `- ## `. Backspace immediately after expansion removes the entire inserted marker and returns to `- `; Undo restores the literal input. Source mode exposes the field. **This intentionally changes cleanup's literal expansion to `- [ ] ` and needs explicit design review.**

Keep `..` literal. Do not trigger on paste, input composition, a code fence, a drawer, or a notebook. Pasted checklists stay checklists until an explicit Convert to requirements action. Route-less capture can preview a provisional task, but final validation uses its resolved destination.

The Mac receives semantic spans and edits from Bob, never independently decides grammar in Swift. Canonical syntax works headlessly. A visual typing shortcut must not change the meaning of every `[ ]` bullet in capture.

## 5. Lifecycle and finishing

| State | Meaning | Transition policy |
| --- | --- | --- |
| `active` | Included in the owner's commitment | Edit, waive, extract; satisfy only with managed owner completion |
| `satisfied` | Accepted when the owner completed | Explicit owner reopen reactivates those satisfied by that close |
| `waived` | Deliberately removed from scope | Optional dated reason; restore explicitly |
| `carried` | Converted into a real task | Preserve forward link and provenance |
| `canceled` | Owner abandoned this remaining scope | Never display as satisfied; explicit owner reopen may restore it |

Record causes in the operation receipt and owner-local managed log entries keyed to requirement IDs. Bullet state remains authoritative; a separate state table would introduce competing truth. A hand-edited terminal state without provenance is not blindly reversed by reopening.

Requirements have no independent lane, review date, schedule, priority, freshness, dependency graph, or completion metric. Report “3 requirements accepted” separately from “1 task completed.” Avoid a 2/5 progress bar because the feature deliberately does not track independent progress.

### One review before mutations

When a managed Done action would close an eligible owner with active requirements:

1. Plan the normal close and compute every affected owner.
2. Show requirements first, grouped by owner, in the existing successor-card shell.
3. Stage **Satisfied** by default; write nothing yet.
4. Offer **Make task**, **Drop requirement** with optional reason, and **Back to task**.
5. Apply owner completion, dispositions, extracted tasks, normal recovery, and selected Task Links in one validated operation.
6. Navigate after the committed receipt identifies the final target.

Make task explicitly removes that requirement from the closing owner's scope. It is not satisfaction. The parent can close because the person approved that scope change, and the receipt says so. Back to task aborts the close.

```text
Finish “Ship CSV export”

REQUIREMENTS                              3 to resolve
## Accented names survive export         Satisfied
## Empty results produce a valid file    Satisfied
## Add a migration guide                 Make task  →  Next   ↪

SUGGESTED NEXT TASKS
   Publish the release note              [not selected]

2 satisfied · 1 made into a task · 1 pull-in
[Back to task]                    [Finish & Jump]
```

This is a wireframe, not a validated prototype. Use the owner's existing hue for the small hash glyphs, stable text/consequence columns, and wrapping instead of truncating decisive content. Historical dispositions collapse below active rows. Show consequences before striking text; keep the active choice unmistakable.

Do not use color alone. Accessible text should announce “Requirement, will become a task,” not “unchecked checkbox.” WAI's checkbox pattern expects state-changing Space interaction; a non-checkable requirement should not pretend to be that control. Use labeled outcome buttons or a choice group. [WAI checkbox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/)

### Keys and Ctrl+J

Avoid the old plan's reversal where Ctrl+X means Keep open on a micro row but Done on an ordinary offer. Ctrl+X can select Satisfied; extraction gets a labeled Make task action. Choose its shortcut only after auditing the existing key map. Space/Tab can retain explicit pull-in: on a requirement, it stages Make task plus pull-in, with both consequences displayed.

**Ctrl+J stays navigation only.** It must not create a task or select a pull-in implicitly. Enable it after Make task is staged, then map the temporary row key to the created task in the receipt. Changing back to Satisfied or Drop clears the invalid pin with visible feedback. One pin per card; one landing after success. A close from a `]s` landing parks the walk according to the accepted jump decision.

Escape cancels the staged close on both clients. Preserve existing Escape aliases and staged-change warnings. The first Escape in a reason editor may return to the card, but must not persist anything. One Finish action is sufficient to accept clearly displayed defaults; an extra routine confirmation adds little.

### Prevent bypasses

A successor-card close on another requirement-owning task must expand its review within the same operation or refuse with Open to finish. No silent defaults and no recursive pop-up rounds.

For v1, reject requirement creation on recurring or externally auto-completed owners such as synced Event Tasks. Those workflows need occurrence-specific rules. Existing flows continue normally; unsupported markers get a visible diagnostic rather than half-supported behavior.

A headless close with active requirements returns structured choices unless the caller supplies reviewed dispositions or an explicit accept-all policy. Ordinary closes without requirements keep their behavior. Old clients lacking the capability cannot complete requirement-owning tasks through the managed path.

Raw file edits stay possible. A manually closed owner with active requirements is **closed, requirements unresolved**, not implicitly satisfied. Show that discrepancy and offer repair review. Never silently reopen the parent or certify its requirements. Archive should hold unresolved blocks so unfinished scope does not disappear.

## 6. Notes, ordering, and conversions

Use one semantic classification for all writers:

```text
managed links and dependencies
requirements, in authored order
notes and drawers, in authored order
managed logs, using their established ordering
```

This is a stable partition of whole subtrees, not a line sort. Preserve subtree text, relative indentation, anchors, and attached detail. Unknown constructs stay intact and cause destructive normalization to refuse.

On a managed edit adding the first requirement, preview moving loose authored notes into NOTES and commit it together. Subsequent note capture reuses that drawer; explicit drawer routes still win. Do not remove NOTES when the last requirement disappears, which would make formatting oscillate. Do not recursively normalize the vault. A requirement's explanatory children remain attached to it; tasks without requirements can retain loose notes.

The new `o` behavior can ship separately: task headline → sibling after the entire block; requirements band → another requirement; notes/drawers → another note. Counted operations and selections use the same insertion-slot logic.

### Promotion fixes a real existing ambiguity

The current promotion code handles managed logs and drawers specially, then calls `buildProjectTaskLineFromChildBullet` for other direct children. That is the implementation seam to change. [Project seed source](https://github.com/bobs-org/bob-plugins/blob/983076e6882c744f36e6fa513e9c2853bd160c36/plugins/bob-navigation-hotkeys/src/110-project-seed.js#L153)

| Source content | Project result |
| --- | --- |
| Active requirement | Ordinary task; explanatory children stay its notes |
| Loose notes and NOTES | One `## Notes` section, order preserved |
| Other drawer | Corresponding section |
| Waived/canceled requirement | Scope history in Notes, not active work |
| Carried requirement | Existing task link/provenance, not duplicate work |
| Existing real task child | Preserve its identity and task semantics |

Do not casually promote a closed owner. Historical state needs a separate validated flow. New tasks follow existing creation/split behavior, not copied freshness or completion fields.

Reuse `task_split` placement and link repair for extraction. It already has a `LINE:DIGEST` preimage selector and explicit anchor reuse; retain those guarantees and add stable requirement IDs for choices. [Split contract](https://github.com/bobs-org/bob-cli/blob/ce0dcc54cec50104991b4ad943de0566e7eba2b6/docs/task-split.md), [stale-reference check](https://github.com/bobs-org/bob-cli/blob/ce0dcc54cec50104991b4ad943de0566e7eba2b6/src/native/task_split/plan.rs#L1015)

Extraction while the owner stays open needs two explicit meanings: **Extract as prerequisite** adds the normal dependency from parent to new task; **Remove from scope and make task** does not. Do not infer a dependency from indentation. At parent completion, Make task explicitly means the latter. Requirements themselves are never dependency nodes.

### Universal round trips are not a reasonable v1 promise

An arbitrary project can contain independently completed tasks, schedules, dependencies, recurring tasks, nested projects, and external inbound links. A requirement cannot represent all that without becoming a task again.

Later project-to-task conversion must prove representability, preview preservation, and refuse otherwise. Tasks with independent history should remain real tasks or links, not be rewritten as if they were accepted with their new owner. “Lossless” must cover identities, workflow, links, and history, not just text.

Task-owned projects need separate design. Prefer ordinary project relationships or task dependencies to `^prj` when those express the need. Do not generalize note `parent` pointers to task blocks in this epic.

Initially preserve documented merge behavior. A later previewed Merge as requirement operation can support representable sources. A source with its own requirements needs an explicit flattening decision or refusal; never invent grouping or drop a level. The current refusal for sources with open real nested tasks is a useful conservative precedent. [Merge validation](https://github.com/bobs-org/bob-cli/blob/ce0dcc54cec50104991b4ad943de0566e7eba2b6/src/native/task_merge/payload.rs#L71)

## 7. Reliability architecture

Use a small typed task-body model instead of independent regex additions:

```text
TaskBody
  managed_links
  requirements: Requirement[id, state, title, child_notes]
  authored_notes_and_drawers
  managed_logs
  diagnostics
```

Preserve byte spans and unknown text alongside semantic nodes. The classifier drives capture, preview, insertion, rendering descriptors, promotion, extraction, and closing. This does not require an unrelated whole-repository parser rewrite.

**Rust owns operation planning.** The Mac decodes rows and submits choices, consistent with the accepted thin-client decision. Obsidian should call the same planner for new requirement mutations. Immediate JS rendering can remain local, read-only, and covered by shared vectors; it must not invent completion semantics.

Bind previews to the full owner block, affected file digests, destination, and capability version. A line digest alone misses changed child notes, ownership, or destination. Refresh retains a choice only if stable ID and relevant preimage match; changed rows require review. Never substitute a similarly titled row.

**Unsaved Obsidian content is part of correctness.** A CLI reading disk is not authoritative over dirty buffers. The adapter must submit editor snapshots and use guarded editor transactions, or flush affected buffers and verify their versions before commit. If neither is safe, refuse. Never overwrite a live buffer with stale disk content.

Validate all preimages and paths before the first mutation. Use a recoverable operation journal for writes spanning owner, extracted-task destination, and ledger. Individual file renames are not multi-file crash atomicity; journaled recovery is needed for logical all-or-nothing behavior. Recovery must not overwrite later edits.

Retries carry an operation ID and return the original receipt rather than creating another task. Undo is preimage-guarded and cannot erase work added since extraction. No jump or walk advance occurs before a committed receipt.

Gate recognition, review, and mutation with a named capability such as `task_requirements_v1`. Unknown semantic rows cannot fall back to implicit success or accidental task creation. Deploy recognizers/preservation first; enable writers only after participating surfaces agree. Existing Mac jump state is reusable, but remapping a newly created task is new work. [Mac choice state](https://github.com/bobs-org/bob-mac-capture/blob/109c30db300df4a9a161ee2152e3b4676decdeaf/Sources/CaptureCore/CapturePullInOutcomes.swift)

## 8. Delivery and acceptance evidence

Replace the original thirteen-phase scope with a smaller sequence. This is a research recommendation, not an executable SASE plan or authorization to change memory.

1. **Freeze semantics with examples.** Resolve marker, reopen/cancel policy, and extraction meanings; establish semantic fixtures.
2. **Read, preserve, and author.** Add explicit classification, one-level validation, note layout, capture rewrite, and hash rendering. Requirements stay absent from task queues/counts.
3. **Finish safely.** Implement precommit review, extraction, dispositions, recovery, headless choices, and Ctrl+J on both clients. Do not enable ordinary requirement authoring before the end-to-end close path works.
4. **Promote and polish.** Fix promotion mapping and refine insertion/presentation with real examples. Ordinary notes must not turn into tasks merely because their owner becomes a project.

Drawer syntax, unrestricted demotion, task-owned projects, recurrence, and merge flattening remain separate. They can consume the classifier later without blocking a coherent first release.

| Scenario | Required acceptance evidence |
| --- | --- |
| Same-titled requirements reorder/edit while a card is open | No choice applies to the wrong row; stale preimages refuse or require review. |
| Escape after extraction choice or reason entry | Parent, requirement, ledger, destination stay byte-identical. |
| Failure between extraction and parent close | Recover to one consistent result; no duplicate work or lost scope. |
| Dirty buffer differs from disk | No silent overwrite or stale completion. |
| Ctrl+J on an extracted requirement | One landing after commit, no implicit pull-in, correct walk parking. |
| Root close includes an embedded requirement-owning task | Review covers every affected eligible owner. |
| Successor-card close targets another such owner | Review expands or shortcut refuses; no bypass. |
| Raw parent edit, unsupported client, unknown state | Preserve and diagnose; no inferred satisfaction or archive disappearance. |
| Mixed notes, drawers, code, real child tasks, requirement detail | No text loss or reclassification of pasted checklists. |
| Bracket-space, Backspace, paste, IME, Undo, route change | Correct eligibility, one undoable edit, client agreement. |
| Extraction/promotion with inbound links or duplicate anchors | Repair identities correctly; refuse duplicate anchors. |
| Reopen after satisfaction, waiver, extraction | Restore only recorded parent-close effects; never duplicate extracted work. |
| Review, Ready caps, Today, completion statistics | Only actual Bob tasks contribute. |
| Plugin disabled or Source mode | Readable content and intact markers; no false checkbox affordance. |

Test the design on five real cases: a small implementation task, mostly reference notes, an acceptance-criteria task, extraction during close, and promotion to a project. The strongest success signal is predicting where each bullet goes and what Finish/Escape does without documentation. Repeated requests to tick requirements early would justify reconsidering the semantics, not adding hidden exceptions.

Implementation validation must include normal repository checks, shared Rust/JS vectors where applicable, and exact-commit macOS CI for Swift changes. This research changed no product code and did not run those implementation gates.

## 9. Source trail

Internal context read through the required audited interfaces:

- `bead:bob-cli-of`: thirteen-phase epic and selected plan branches.
- `plan:202611/explicit_micro_tasks.md`, especially sections 1–7: classification, state inheritance, rendering, authoring, close ordering, compatibility, merge, promotion. Its earlier research report was not needed for this independent evaluation.
- Vault query locators: `bob.md#^micro-tasks`, `^micro-tasks-cleanup`, `^better-o`, `^no-all-caps-for-drawers`, `^tasks-parent-projects`, `^task-to-project`, `^better-micro-task-name`, `^ctrl-j-successor-jump`. Approximate DQL line positions at read time: 95–163, 197–200, 493–518; block IDs are durable locators.
- `decisions:capture-bullets-mirror-the-task-block`, `decisions:unblocked-tasks-are-offered`, `decisions:successor-jump-parks-the-walk`, `decisions:mac-capture-is-a-thin-client`; glossary strands for capture, drawers, task links, dependency links, split, merge, and successor offers.
- Additional inspected code/contracts: `src/native/task_complete/tests/tree_tests.rs`, `src/native/collect_done/transform.rs`, `docs/capture.md` completion execution, and `docs/task-dependencies.md` successor verdicts.

External primary sources are linked beside their supporting claims. They inform particular comparisons; the recommendation is my inference from the cleanup requirements and implementation constraints.

## 10. Recommended solution

**Implement task requirements, not a second task hierarchy.** Give them one level, explicit opt-in identity, a `##` visual marker, no independent scheduling or completion, and ordinary explanatory notes. Use NOTES to distinguish context from committed scope. Offer split and project promotion as escape routes into real tasks.

Use a non-checkbox marker unless native checkbox source matters more to Bryan than the no-independent-completion rule. Preserve bracket-space authoring while explicitly acknowledging the canonical-syntax change. Show a precommit review when the parent finishes, accept displayed defaults with one action, preserve Escape, and apply scope changes, extraction, ledger updates, and navigation through one guarded operation.

**The best first release solves three things well: knowing what a task includes, finishing it honestly, and promoting detail into independent work without losing context.** Drawer renaming, arbitrary task/project nesting, and universal round trips should not determine its architecture or delay that useful core.
