# Task transfer, merge, and bullet extraction: a design that preserves meaning

Independent research by **cdx**, 2026-11-03.

**Recommendation:** build this. Moving, consolidating, and extracting work belong together, and Bob already has much of the necessary machinery. Keep the proposed `>` syntax, but make it a small, typed transformation language with explicit previews. Treat merge as a new operation that preserves history and transfers obligations, rather than as a cancel label with a content-copy side effect. Make bullet extraction the simplest interaction: select bullets, preview new tasks, commit, leave readable links.

This report is research and a design recommendation, not an implementation or an approved change to existing policy. I independently reviewed the local code, relevant durable decisions, the requested multi-target capture plan, and primary Obsidian documentation. I did not read or solicit any peer research from this swarm. No vault content was changed and no product tests were run.

## 1. What exists, and what it means for this feature

The inspected snapshots were:

| Repository | Commit |
| --- | --- |
| bob-cli | `c673d14439212e79443d231c81dc11204d10a25c` |
| bob-plugins | `d1737ea7ca1b216960a908904358f91ed1c2a17a` |
| bob-mac-capture | `6c103800c9ca93831e0ff79fb7320b5b92f67dfd` |

The code moves quickly. Recommendations below describe these snapshots and should be rebased onto the eventual multi-target implementation.

**Task move is already a serious structural operation.** `bob task move` selects multiple open task roots from one source note, preserves their subtrees, repairs links throughout the vault, and repairs derived dependency identities. It understands relative/pathless links, embeds, aliases, descendant anchors, collisions, and type-driven ledger relocation. Its snapshot-only planner is reusable; do not implement `>` by deleting and recreating task text. The command uses a maintenance lock, a guarded full read-set, ordered writes, and partial-apply reporting. It expressly does not promise a filesystem-wide atomic transaction. [B1, B2]

**Capture already has a staged composition model.** The ordinary capture writer checks preimages, stages files, and attempts rollback on failure. Its own comment says the checks are neither cross-process locking nor fully serialized transactions. The stronger task-move writer and the ordinary capture writer are related foundations, not interchangeable guarantees. [B3]

**Relations already support effects, but a merge effect does not exist.** Explicit additions or relabels into configured cancel/complete labels trigger source status changes. Hand edits, reconciliation, config edits, rename, unlink, and unchanged re-adds do not trigger them. The source normally remains in place. Existing cancel behavior prunes today's live source links and recovers dependents; it does **not** transfer dependencies. The docs even show `merged into` as a commented-out possible cancel label. Rust and plugin display tables already know the inverse phrase `merged from`, so the vocabulary is partly present, not the operation. [B4, B5, P1]

**Drawers and note headings are distinct.** A task drawer is a direct ALL-CAPS child bullet. `@c+cid#requirements` resolves that drawer; `@c#Requirements` routes to a note heading. Managed Depends-On, LINKS, LINKED FROM, logs, and TASKS are not user drawers. Existing matching, reserved-name, near-duplicate, and explicit-literal rules should apply rather than a new lowercase-and-append helper. [B6; memory `glossary:task-drawer`]

**The backlink requirement has a direction trap.** If old task S contains `[[new#^n]]`, N receives `[[S]] (💬 mentions)` on its LINKED FROM line. S does not receive that entry. To give S the requested mentions, N must also contain a link to S. Mentions are already derived, distinguish nested task ownership, skip managed relation/dependency lines and code, and defer to relations/dependencies on the same pair. [B4 §19]

**Obsidian edits must respect open buffers.** The existing move implementation reads open editors, writes them with editor transactions, uses preimage-checked `vault.process` for other files, writes the destination before source removal, and rolls back only while postimages still match. Existing relation follow-ups are weaker: some mirrors, ledger pruning, and recovery are best effort after the primary write. Content transfer cannot safely inherit that weaker contract. [P2, P3]

**Mac Capture is a thin client.** It consumes Bob's parse/completion/preview results. Its model has string-valued modes and additive decoding patterns, but that does not prove an unfamiliar structural preview will display correctly. The new operation needs explicit Mac presentation tests and capability handling, while Rust remains the capture grammar and mutation authority. [M1; memory `decisions:mac-capture-is-a-thin-client`]

## 2. Is this a good idea?

Yes. Notes naturally alternate between context and actionable work. A bullet becomes a task when it deserves independent attention; several tasks become one when they represent the same outcome; a task becomes context when it no longer deserves an independent commitment. Supporting those transitions reduces copy/paste, stale duplicates, and orphaned context.

There is a familiar interaction precedent: Obsidian's core Note composer can extract selected text and replace it with a link. That supports the proposed extraction experience. Its merge deletes the source note and rewrites links, however, so it is the wrong lifecycle model for Bob's task history. [Obsidian Note composer](https://obsidian.md/help/plugins/note-composer)

The main risk is making a pleasant syntax conceal materially different operations. Moving retains an actionable identity; merging retires identities into another actionable identity; filing as notes retires work into non-actionable context; extraction creates new identities without finishing the parent. These should share parsing and planning machinery while remaining visibly distinct in the UI and result JSON.

I would not build a general-purpose Markdown refactoring framework, arbitrary relation scripting, or natural-language merging. Deterministic transformations with readable previews are sufficient. Do not summarize away source details, deduplicate bullets by approximate wording, or interpret identical titles as identity.

## 3. Proposed syntax and explicit requirement adjustments

Use these meanings:

| Capture | Named action | Result |
| --- | --- | --- |
| `@a+aid @b+bid > @c` | Move 2 tasks | Relocate intact task blocks into c's task intake; repair identity references |
| `@a+aid @b+bid > @c#research` | File 2 tasks as notes | Append contextual bullet groups under c's RESEARCH heading; retire source tasks with provenance |
| `@a+aid @b+bid > @c+cid` | Merge 2 tasks | Add contextual content under cid; preserve and cancel source task records; add source → destination merge relations |
| `@a+aid @b+bid > @c+cid#requirements` | Merge 2 tasks into REQUIREMENTS | The same merge, with copied content placed inside the destination task's drawer |

Create a missing destination heading or drawer only when the commit has nonempty content to put there. Use the existing resolver and creation controls; show `Create REQUIREMENTS` in preview. Destination note/task identities must already exist in the first version. Do not create an entire note because of a misspelled route.

The adjustments are deliberate:

1. **LHS entries name tasks, not whole notes.** Require `@route+id` on every source. A bare `@a` must not unexpectedly select every task in a note. There may be any number of explicitly selected source tasks, subject to practical validation and performance limits.
2. **`@c#drawer` remains a note heading.** In UI copy call it a section, preserving the existing grammar. A task drawer requires `@c+cid#drawer`. There is no invisible task that owns an area note's drawer.
3. **Filing as notes preserves cancelled source records.** I recommend extending the source-history protection requested for merge to task-to-note conversion. Removing the source checkbox/identity would make historical task links and dependency/relation targets stop resolving as tasks. The destination contains plain contextual notes; the source stays as history. This is a change from a literal destructive interpretation of “converted and moved.”
4. **Merge transfers active dependency obligations.** Merely invoking today's cancel effect is insufficient; details follow below.
5. **Extraction includes a backlink in each new task.** This satisfies the requested LINKED FROM mentions on the old task as well as the useful mentions on the new tasks.
6. **Special lifecycle objects are excluded initially.** Recurring roots, calendar-owned Event Tasks, `^prj`, archived/closed roots, and subtrees containing live nested `#task` records need dedicated semantics. Refuse with a useful reason instead of silently stripping their lifecycle or duplicating tasks. Ordinary authored child bullets and arbitrarily deep non-task content remain supported.

None of these adjustments requires a permission round during routine use. The operation's normal preview is where the user sees what will happen. Exceptional semantic conflicts may require a choice before commit.

### Parsing alongside the in-progress multi-target work

I read `plan:202611/capture_multi_target.md` through the audited artifact reader. It introduces adjacent task targets as a run, fans them into ordinary capture items, preserves typed order, rejects duplicate resolved tasks, and exposes additive `targets[]`/`fanout` data. It also contains both candidate `split_edges` decisions; the eventual selected behavior must be checked rather than inferred. At the inspected bob-cli commit, `GRAMMAR_REVISION` is 7 and multi-target support was not visible in the searched capture paths. [A1, B7]

A transfer is **not** a fan-out of ordinary `@task` captures. Otherwise the sources can receive notes or Ensure Next effects before the destination is considered. Recognize the entire transfer form before ordinary target-run expansion:

```text
transfer := source (space source)* space ">" space destination
source   := complete @route+id
```

Recommended first-version rules:

- The transfer occupies its entire parent line: no leading/trailing prose, extra destination, chained `>`, or child capture bullets.
- `>` is a standalone token in this exact position, outside quotes/code. Ordinary prose and Markdown blockquotes remain ordinary text.
- Once the source-run plus `>` prefix is recognized, incomplete or malformed RHS text is an incomplete transfer/error, never a note to capture.
- Reject LHS drawers, `!`, dependency/relation modifiers, scheduling/type markers, clipboard directives, and Pomodoro actions. They can be added later with explicit semantics. The sources already contain the data being transferred.
- Respect forced-literal destination behavior from existing capture rather than interpreting marker-like prose behind the user's back.
- Reuse target lexing, route resolution, task resolution, byte ranges, and duplicate detection from the multi-target work. Report source spans and one destination span in a dedicated transfer node; do not mislabel source tasks as fan-out recipients.
- Deduplicate by **refusing** repeated resolved `(note path, block ID)` pairs, including aliases, consistent with the target-run plan.
- Across notes, preserve typed source order. Within one explicit list, preserve that list order even if it differs from physical source order; document this distinction from existing `task move` selectors.
- Reject self-merge, ancestor/descendant overlap, and a source that is also the target. Allow distinct tasks in the same note for merge. Keep same-note ordinary move refusal/no-op explicit rather than pretending it changed location.
- Completion before `>` offers source tasks; after it offers valid destinations; after `+` tasks; after `#` the correct section/drawer catalog. Filter sources out of merge targets and show disabled reasons where useful.

This changes interpretation of some previously literal drafts. Allocate a grammar revision after the other in-flight changes land; do not hard-code “8” here. Parse, completion, rewrite, dry-run, execution, docs, and old-client behavior must agree. [A1, B7]

## 4. Exact merge semantics

### Preserve history; copy actionable context

A source task stays in its original note with its original ID, title, fields, logs, and authored notes. The merge records a source-to-destination relation and cancels it through the composed merge operation. Historical ledger links and ordinary mentions continue to point to the source, rather than being globally redirected to a different task.

The destination receives one provenance group per source in selection order:

```markdown
- [ ] #task Make capture reliable [created:: 2026-11-01] ^reliable
  - REQUIREMENTS
    - [[a#^retry|Handle request retries]]
      - Retry only when the first request did not commit.
      - Include the response identifier in diagnostics.
    - [[b#^timeout|Explain timeout failures]]
      - Keep the draft visible after a timeout.
```

The source becomes, schematically:

```markdown
- [-] #task Handle request retries [created:: 2026-10-28] [cancelled:: 2026-11-03] ^retry
  - 🪢 **LINKS:** merged into [[c#^reliable]]
  - Retry only when the first request did not commit.
  - Include the response identifier in diagnostics.
```

Generated mirrors are omitted from these examples for readability. The source title supplies the group label even when it has no authored children, so title-only tasks still contribute meaning. A link is short, navigable, and provides hover access to the original history. The copied text is an editable snapshot, never a continuously synchronized second copy.

Copy authored contextual content. Do not copy a root checkbox, `#task`, status fields, dependency IDs, fresh/keep state, managed edge lines, generated mirrors, or Work/Schedule/Rotten/Cancel logs into the destination as live metadata. Those remain accessible on the source. Show the distinction in the preview: `2 sources · 5 notes added · history retained`.

Keep existing destination content in place and append source groups at the normal content anchor or selected drawer. Preserve nested structure; do not flatten identically named source drawers together by guessed meaning. Inside a provenance group, a copied ALL-CAPS child is ordinary nested context rather than a new destination-level drawer. Explicit destination `#requirements` controls where the group goes.

Rebase links using their original file context. Copying `[[#^other]]` into another note without rebasing changes its target. Preserve source anchors; remint copied descendant anchors where needed, remap internal links within the copied subtree, and expose the mapping in the plan. External inbound links stay attached to original source anchors. Obsidian's documented block-link syntax and alias support make the proposed visible provenance compatible with ordinary notes. [B2; Obsidian internal links](https://obsidian.md/help/links)

### Dependencies: merge is a contraction of outstanding work

Suppose D depends on source A, and A is merged into C. Plain cancellation makes D eligible before C is done. That defeats “this work now lives in C.” Today's cancel-label behavior really has this recovery effect. [B4 §17]

Recommended rule for eligible ordinary tasks:

- Replace references to merged sources in **open dependents' authored Depends-On lines** with the surviving destination, deduplicating edges.
- Give the destination the union of its existing prerequisites and the sources' explicit external prerequisites.
- Remove edges internal to the merged set from the surviving graph. When the destination depended directly on a source, that internal edge disappears as part of the merge.
- Keep closed source records' historical prerequisites. Do not rewrite closed dependents or old ledger history.
- Validate the complete resulting graph for self-dependency and cycles, including project relationships. A cycle aborts the entire operation with the shortest useful explanation.
- Project/ancestor blockers are contextual, not ordinary authored task edges. If merging across projects would discard an inherited blocker, refuse and explain it in the initial version. Do not materialize project dependencies onto tasks as a shortcut; existing policy explicitly rejects that model.
- Only after the new active graph is planned should cancellation and final-state recovery run. Never briefly recover dependents against the pre-transfer graph.

Write the authoritative Depends-On links, then project the derived `[id::]`/`[dependsOn::]` fields through existing engines. Rewriting fields alone would fight reconciliation. [B8; memory `decisions:task-deps-are-depends-on-links`, `decisions:projects-block-from-prj-line`]

This can over-block a dependent: D may need only A's piece, whereas C also includes B. That is a real cost of merging distinct commitments. Show `2 dependents will now wait for C` in the preview. If that is undesirable, keep separate tasks and relate them rather than merging their completion criteria. A “content-only copy” is a different operation and should not silently masquerade as merge.

### Destination fields, schedules, and today's ledger

The destination owns its title, type, clock, priority, and history. Do not select the “strongest” lane or earliest deadline by a universal merge heuristic. Show conflicting source fields in a compact optional details section; their originals remain intact.

A future source scheduled date is a blocking constraint, not merely historical decoration. If the destination would become actionable earlier than that gate, require one explicit resolution: keep the destination's schedule or carry the latest source gate. The default is a conflict result, not silent relaxation. Similar inherited project blocking conflicts are refused initially. Priority and due-date differences are visible warnings, without automatic escalation.

Prune source links from today's **open** Pomodoros using the current cancellation rules. Leave closed sessions and historical time untouched. Do not automatically link C to every source session or manufacture multiple live commitments. Keep C's existing placement unless final blocking requires removal; offer an explicit optional placement if the user wants C planned today. No preselected successor links. A structural move still follows its existing relocation semantics; a merge is not an excuse to change that policy. [B1, B4; memories `task-lanes-are-sticky`, `off-clock-follows-tag-then-note-default`, `unblocked-tasks-are-offered`]

### The relation effect

Add a dedicated `merge` effect alongside cancel, complete, and successor. Do not put `merged into` in both a merge list and cancel list. Merge owns copying, graph rewrites, source cancellation, ledger pruning, and the relation write as one plan.

A conservative configuration shape fits the existing system:

```yaml
relations:
  merge_labels:
    - merged into
```

Recommend shipping the capability with an empty built-in effect list, matching existing effect opt-in conventions, and enabling this label in Bryan's managed configuration as part of the authorized implementation. An explicit `>`/CLI merge is always a merge command; configuration governs whether a relation gesture launches that command. All explicit merge commands record the canonical `merged into` provenance label. Additional configured aliases may trigger the same action; aliases do not create arbitrary executable callbacks.

Validate collisions across all effect lists with the existing fail-toward-no-effect rule. Existing users who configured `merged into` as cancel-only must not silently acquire copying on upgrade. Surface the policy conflict and migrate that configuration deliberately. Hide/unhide remains suggestion-only, and changing the config does not replay history.

In Ctrl+Shift+L, choosing the merge label changes the relation card into the same merge preview. Choosing an optional destination drawer is operation input, not a new fragment appended to a task relation link. The stored edge still points to the task root. The operation receipt records actual placement. A normal relation `S merged into T` without a drawer appends source groups under T's ordinary content anchor.

Apply the effect only on a new explicit add or relabel into the label. Never on reconciliation, mirror refresh, hand edit, config change, rename, unlink, or unchanged re-add. Unlinking does not unmerge or reopen a task. An inverse “merged from” display must still run the action in the correct stored source → target direction. Closed sources receive no new content-transfer operation in v1; a recognized already-applied operation returns unchanged rather than copying again. [B4, B5, P1]

## 5. Filing tasks as ordinary notes

For `@a+aid > @c#research`, use the same provenance group but place it under a note H2 section rather than under a task. Retain the original task as a cancelled record and add a readable note such as:

```markdown
- Filed as notes in [[c#^filed-retry|Research]].
```

The destination group receives its own plain-bullet anchor so the provenance link can be precise. Do not author a `merged into` **task relation** to a heading or a non-task bullet: the current relation contract requires task endpoints. Do not create a fake destination task solely to make a mirror work.

Initial eligibility should require no active dependency obligations involving the source. If open work depends on it, or its own blocked work still has outstanding prerequisites, explain that filing as context would retire those obligations and offer merge-into-task instead. A future advanced “abandon obligation and file context” action could make this explicit, but it is not needed for the first coherent feature.

This is the proposal's least necessary subfeature. If delivery needs staging, ship it after move, merge, and extraction. The heading-vs-drawer distinction and historical identity behavior should be settled before enabling the syntax, not discovered after users have demoted tasks.

## 6. Ctrl+Shift+T: extract bullets into tasks

Name the command **Create tasks from bullets…**; use the requested Ctrl+Shift+T binding in Bryan's setup and expose a normal command-palette action. A source search found no explicit competing registration in the inspected navigation sources, but that is not a live vault hotkey audit. Check configured/core conflicts during integration; do not assume global availability.

### Selection and interaction

- With the cursor in an authored direct-child bullet, select that complete subtree. With the cursor in a deeper ordinary child, resolve its eligible top-level ancestor and show the selected range.
- A full-bullet editor selection selects all included sibling subtrees. Partial text selections expand visibly to whole bullets in preview; crossing task owners is refused in the first version.
- From a task root, show its eligible direct children as a compact checklist. Start with none checked rather than promoting the whole task accidentally.
- Managed dependency/relation lines, logs, generated mirrors, and structural project children are not candidates. Explain exclusions when invoked there.
- A selected authored drawer can become **one** new task with that drawer's title and all its children. The card states the count explicitly. For convenience, allow opening the drawer in the chooser and selecting its immediate child notes individually; do not interpret the drawer title as a task merely because it is ALL-CAPS.
- Default to one new task per selected bullet. A secondary “Combine into one task” mode may be offered, but one-per-bullet should be the first release's default and can be its only mode.
- Default destination is the source note's task intake when eligible, or the established inbox route when it is not. The card always names the destination. Changing it previews inherited type, clock, and project blocking.

A compact card could read:

```text
Create 2 tasks                            product → product

✓ Test the retry path                     2 child notes
✓ Document timeout behavior               1 child note

Parent keeps links to the new tasks
New tasks link back to “Make capture reliable”

Esc Cancel                       Enter Create 2 tasks
```

Use the same keyboard selection and focus conventions as existing pickers. Show actual task text, destination, counts, and effect, rather than implementation metadata. Use color as an additional cue, with explicit verbs and accessible labels. First Enter commits a reviewed operation; do not add repetitive confirmation dialogs after the card.

### Exact Markdown outcome and mention direction

Before:

```markdown
- [ ] #task Make capture reliable ^reliable
  - Test the retry path
    - Include a response-lost-after-commit case.
  - Document timeout behavior
    - Explain that the draft is retained.
```

After, schematically:

```markdown
- [ ] #task Make capture reliable ^reliable
  - Split out: [[product#^test-retry|Test the retry path]] · [[product#^document-timeouts|Document timeout behavior]].

- [ ] #task Test the retry path [created:: 2026-11-03] ^test-retry
  - From [[product#^reliable|Make capture reliable]].
  - Include a response-lost-after-commit case.

- [ ] #task Document timeout behavior [created:: 2026-11-03] ^document-timeouts
  - From [[product#^reliable|Make capture reliable]].
  - Explain that the draft is retained.
```

The parent's inline links generate mentions on each new task. Each `From` link generates a mention on the parent. Use ordinary prose, not a managed `split from` relation: relation precedence would replace the requested mention on that direction of the pair. The existing inverse vocabulary for `split from` is useful if a separate relation feature is ever desired, but is unnecessary here. Respect `linked_from_mentions: false`; never override the user's mention setting. [B4 §19, B5]

Replace one **contiguous selected run** with one compact `Split out:` bullet in its original position. For noncontiguous selections, leave a stub at each original position so intervening context is preserved. If original selected bullets have externally referenced anchors, keep those anchors on individual stubs rather than compressing them into an invalid multi-anchor line. Cap visual density by using one stub per bullet for large runs; do not discard links to make the notice shorter.

New task titles come from the selected bullet roots. Preserve emphasis and semantic links while removing only the list marker and any moved block anchor. Use the existing block-ID naming/prompt conventions and require unique destination identities. Body subtrees move with their structure, fences, blank lines, code, and relative links intact. Creating tasks should not run those bytes back through capture grammar: a literal `@`, `>`, `%c`, or `#` in an existing bullet is existing content.

New tasks receive fresh IDs and today's creation date; no inherited `fresh`, `keeps`, cancellation, lane, or work-history fields. They start under ordinary creation rules, including destination project blocking, and are never automatically Next/Today-linked. Do not copy the parent's priority, deadline, or dependencies wholesale. Explicit task-like scheduling/status metadata already on a selected plain bullet must be surfaced for resolution rather than silently becoming a new task's active state.

The parent remains open with its status and metadata intact. Extraction is not a Done gesture and does not advance the review walk. Leave focus at the first replacement stub, with an easy “Open first task” action. Existing Ctrl+Shift+M must retain its follow-and-park behavior. A merge that closes a current review landing follows the existing resolving-relation answer policy, and any new multi-source behavior must advance at most once. [P2; memory `decisions:task-move-never-advances-the-walk`]

## 7. Architecture, failure behavior, and undo

Use one operation model with explicit variants:

```text
MoveTasks(sources, note)
FileTasksAsNotes(sources, section)
MergeTasks(sources, targetTask, optionalDrawer)
ExtractBullets(owner, selections, destination)
```

Resolve all references and selections first. Build a pure plan from snapshots containing edits, identity mappings, graph changes, side effects, landing positions, and user-visible consequences. Adapt that plan to capture, CLI, and Obsidian writers. Do not implement merge as “call relation writer; then call cancel; then append notes.”

For Rust, compose the existing move/link-repair, drawer, relation, dependency, cancellation, and capture staging modules. For Obsidian, keep buffer-aware editor writing. The present architecture already has Rust and JS planners pinned by shared vectors. Reusing that pattern is more practical than forcing disk-based `bob capture` through unsaved editors. A Rust plan-only snapshot RPC could be considered later, but should not become a prerequisite for this feature. Swift continues to render Bob's verdicts and content.

The required contract is stronger than the current best-effort relation follow-up:

1. **Plan all primary effects before any write.** This includes destination payloads, source retirement/stubs, dependency transfers, relevant ledger changes, and required ID allocation.
2. **Validate all inputs used for decisions.** Include graph/read-set membership and open-buffer content, not just files that happen to be written. A source line number is not an identity.
3. **Persist a recoverable operation record before structural writes.** Extend the existing guarded writer/recovery facilities with operation ID, ordered paths, pre/post hashes, generated IDs, and progress. Do not invent a new general transaction platform. Treat record contents and recovery directories as implementation details, not front-page UI.
4. **Write destination content before retiring/removing source content.** Group all edits to one file into one postimage. For dependency-bearing merges, keep recovery disabled until the final graph is present; prevent cooperative hooks from observing an intermediate graph as a finished operation.
5. **Guard rollback against concurrent edits.** Restore a before-image only if the file/buffer still equals this operation's postimage. Otherwise retain recovery material and report precisely which paths need repair. Prefer recoverable duplicates to lost source content.
6. **Distinguish outcomes.** Return `planned`, `applied`, `unchanged`, `stale`, or `partial` with applied/deferred paths and a recovery reference. A lost subprocess response is not proof that the write failed.
7. **Make retries idempotent.** A repeated operation ID returns its stored result. An existing unchanged merge relation does not copy again. A hand-authored relation alone is not evidence that content was transferred. If the destination was written but source retirement failed, recover from the receipt rather than replaying the command blindly.

Ordinary Markdown files cannot provide a single crash-atomic multi-file transaction. The existing implementations explicitly demonstrate that limitation. The promise should be “validated as one operation, with guarded writes and recoverable partial failure,” not “atomic” without qualification. [B1, B3, P2]

Obsidian's own developer guidance recommends the Editor interface for active content and `Vault.process` for background changes, consistent with Bob's current approach. This is a sound reason to preserve a buffer-aware writer. [Obsidian plugin self-critique checklist](https://docs.obsidian.md/oo/plugin)

**Undo needs an explicit contract.** Same-note extraction can be one native editor transaction and one Ctrl+Z. A multi-file merge/extraction requires an operation-aware undo action that restores all affected files only while recorded postimages still match. Show `Undo merge`/`Undo extraction` in the completion notice and expose a command for the latest operation. A scoped CLI Git commit is valuable additional recovery, but does not make editor Ctrl+Z cross-file-safe. Do not advertise one-key global undo until it is implemented and failure-tested. Do not implement unmerge by deleting the relation.

## 8. Command-line and JSON support

Keep existing `bob task move SOURCE DEST -b ID ...` behavior and selectors intact. A small additional surface can cover multi-note sources without overloading those positional arguments:

```bash
# Existing command remains available.
bob task move inbox product -b retry --dry-run

# Proposed structured equivalents of the four > forms.
bob task transfer -d -f json -t '@c' '@a+aid' '@b+bid'
bob task transfer -t '@c#research' '@a+aid'
bob task transfer -t '@c+cid#requirements' '@a+aid' '@b+bid'

# Same operation through capture; quote > so the shell cannot redirect it.
bob capture --dry-run -- '@a+aid @b+bid > @c+cid#requirements'

# Proposed discovery and extraction interface.
bob task-bullets -f json '@product+reliable'
bob task extract -d -f json -t product -b '<selection-token-1>' -b '<selection-token-2>' '@product+reliable'
```

These names and flags are a proposed contract, not commands verified to exist. `task transfer` reports its resolved action as move/file/merge. I prefer it to adding separate public move-many, merge, demote, and copy commands. `task extract` is a distinct verb because its sources are bullet subtrees. A read-only `task-bullets` report stays top-level under the project's CLI membership rule; do not create a new read-only `task list-bullets` member. [memory `cli_rules.md`]

A bullet selection token should bind owner identity, snapshot hash, source range, and subtree fingerprint. It is opaque to callers and stale after relevant edits. Ordinals may be UI conveniences, but bare line numbers or bullet text alone cannot authorize removing content. If desired, a machine-only JSON request can carry the same stable plan/selection data; avoid a second bespoke selector language in capture.

All mutating commands should provide `-d/--dry-run`, `-f/--format`, and the existing appropriate lock/offline/retry conventions. Give every public long option a short alias, alphabetize help, use stderr for progress, stdout for a single JSON result, and meaningful nonzero exits for refusals/partial failures. Dry-run must not mint IDs on disk, create drawers, write recovery state, read a clipboard, or mutate config. Reserve candidate IDs in the plan and revalidate them at commit.

JSON should expose:

- Resolved action, source and target identities, effective destination kind and section/drawer.
- Preview blocks and primary content counts; exact proposed identity mappings.
- Sources retained/cancelled, new tasks created, dependencies replaced/added, ledger links pruned, field conflicts and warnings.
- Selection/plan identity, staleness/conflict codes, resulting focus location.
- Applied/deferred files, recovery/undo identifiers, and commit/sync outcome where applicable.

Capture can add a dedicated `transfer` result and parse mode, preserving unrelated legacy fields and not pretending there was a new task capture. Extend `capture-parse`, `capture-complete`, and `capture-rewrite` together. The Mac must show the correct verbs and consequences before Return; generic JSON decoding alone is not acceptance. Older Bob clients should report unsupported capability rather than capturing the draft literally.

## 9. Validation and delivery boundaries

The first milestone should be byte-level examples and conformance vectors covering the transformation semantics, followed by the common planner and writer. Add capture and CLI adapters, then the Obsidian relation/extraction cards and Mac rendering. Filing as note sections can follow once its retirement semantics are accepted. This is a delivery sequence, not a proposal to ship several independent implementations.

Essential acceptance cases:

| Area | Required evidence |
| --- | --- |
| Grammar | Single/multiple sources; partial RHS; quoted drawers; prose/code `>`; duplicate aliases; no accidental fan-out or Ensure Next; no mixed-action fallthrough |
| Move | Existing task-move conformance retained; cross-file and pathless links; root/descendant collisions; co-moved references; inherited type and ledger relocation |
| Merge payload | Title-only task; nested drawers; fences/tables/blank lines; pathless links rebased; no managed log/edge leakage; no duplicated live nested tasks |
| Dependencies | External prerequisites union; incoming edges retargeted; internal edges removed; cycles refused; no transient unblock; inherited blocker refusal; future schedule conflict |
| Relations | Forward and reverse picker entry; configured aliases; effect collisions; hidden labels; unchanged re-add; hand edit/reconcile/rename/unlink never replay a merge |
| Extraction | Cursor/root/selection flows; drawer vs drawer children; noncontiguous stubs; anchored bullets; duplicate titles; nested task rejection; origin mentions in both directions |
| State | New task creation fields; parent lane unchanged; no automatic Today links; source historical sessions preserved; target blocked-state and clock/type behavior |
| Concurrency | Source/target/graph changes after preview; competing open views; destination collision; no stale selector fallback to similar text |
| Failure | Fail after each file write; process exit before response; receipt replay; rollback blocked by a concurrent edit; partial result accurately reported |
| Undo | Same-note Ctrl+Z; multi-file operation undo; refuse undo after unrelated edits without erasing them; relation deletion does not unmerge |
| Clients | Shared Rust/JS transformation vectors; exact CLI JSON fixtures; Mac previews and older-capability paths; keyboard/focus/VoiceOver checks |

Use synthetic vaults. Include a realistic mixed-note performance fixture and measure parse/completion/preview latency on the Mac; do not invent a universal time threshold before measurement. Reuse indexes instead of scanning the entire vault on every cursor move. The current move implementation's broader scan is appropriate at commit planning, not necessarily in keystroke completion.

Follow each repo's actual verification rules when implementing: bob-cli format/lint/tests/docs checks, bob-plugins source build/conformance tests, and compiled Swift plus Mac-specific checks for changed app code. A Linux-only model check does not validate the macOS UI. Preserve the release-train/version policy and mark grammar contract changes appropriately.

## 10. Alternatives and remaining tradeoffs

**Only add `merged into` to cancel labels:** cheapest, but does not merge content and can release dependents too early. Reject.

**Delete sources and redirect every inbound link:** superficially tidy, but historical references now claim another task owned the original work. Reject for Bob's history model.

**Merge by moving all source children away:** reduces duplication, but makes source records poor history and turns every task log into a transfer problem. Prefer retained originals and copied authored context, with the visible destination treated as the current working copy.

**Keep all dependency edges unchanged:** preserves text, but changes the meaning of open work when cancellation resolves source prerequisites. Reject as the default.

**Automatically union all metadata:** arbitrary priority/date/lane choices can make a destination unexpectedly urgent or planned. Preserve destination ownership, handle gates explicitly, and retain originals.

**Run the CLI mutation from Obsidian:** would centralize some code but bypass unsaved buffers and native undo. Prefer the existing pure-planner/shared-vector approach unless a genuine snapshot RPC is designed.

**Turn every extraction into parent → children dependencies:** useful for decomposition in some cases, but prevents the requested inert mentions because dependency precedence suppresses them, and changes completion semantics without instruction. Keep extraction structural; let the existing dependency UI make that additional commitment explicitly.

**Restrict extraction to direct task children forever:** easy to explain but awkward for the very drawers Bob now encourages. Ship direct children first if necessary, but design the chooser to expose drawer children without adding a new capture sigil.

The two highest-cost pieces are dependency-preserving merge and multi-file recovery/undo. They are worth doing for a reliable feature; they should be named in scope rather than hidden behind “reuse cancel.” If scope must shrink, support dependency-free merges first with a clear refusal, while keeping the final graph-transfer semantics specified. Do not ship incorrect dependency behavior under a broad “merge” label.

## Evidence index

Repository paths below refer to the commits listed at the start. Code was read through local authorized checkouts; links are review conveniences. Memory was read through `sase memory read`, and the plan through `sase artifact read`.

- **B1:** [bob-cli `docs/task-move.md`](https://github.com/bobs-org/bob-cli/blob/c673d14439212e79443d231c81dc11204d10a25c/docs/task-move.md): eligibility, placement, link repair, write ordering, scoped Git commits, and partial outcomes.
- **B2:** [bob-cli `src/native/task_move/plan.rs`](https://github.com/bobs-org/bob-cli/blob/c673d14439212e79443d231c81dc11204d10a25c/src/native/task_move/plan.rs), `task_move/command.rs`: snapshot planner, selectors, destination enumeration, and guarded writer adapter.
- **B3:** [bob-cli `src/native/capture/commit.rs`](https://github.com/bobs-org/bob-cli/blob/c673d14439212e79443d231c81dc11204d10a25c/src/native/capture/commit.rs), especially `validate_disk_preimages` and `write_staged_files`: staged writes and limited optimistic concurrency guarantee.
- **B4:** [bob-cli `docs/task-relations.md`](https://github.com/bobs-org/bob-cli/blob/c673d14439212e79443d231c81dc11204d10a25c/docs/task-relations.md), §§8, 17–20: explicit effect triggers, follow-up guarantees, cancellations, mentions, and successor labels.
- **B5:** [bob-cli `src/native/config/relations.rs`](https://github.com/bobs-org/bob-cli/blob/c673d14439212e79443d231c81dc11204d10a25c/src/native/config/relations.rs), `src/native/task_relations/inverse.rs`: current effect enum/config defaults and existing merge/split inverse phrases.
- **B6:** [bob-cli `src/native/capture_drawers.rs`](https://github.com/bobs-org/bob-cli/blob/c673d14439212e79443d231c81dc11204d10a25c/src/native/capture_drawers.rs), `docs/capture.md`: task drawers, project H2 handling, reserved keys, completion, and capture grammar.
- **B7:** [bob-cli `src/native/capture_language/mod.rs`](https://github.com/bobs-org/bob-cli/blob/c673d14439212e79443d231c81dc11204d10a25c/src/native/capture_language/mod.rs): inspected grammar revision; `src/native/capture_parse.rs` and `src/native/capture/plan.rs` are important integration points.
- **B8:** bob-cli `src/native/capture/dependencies.rs`; audited decisions `task-deps-are-depends-on-links`, `projects-block-from-prj-line`, `task-lanes-are-sticky`, `off-clock-follows-tag-then-note-default`, `unblocked-tasks-are-offered`. The decision bodies include supersession notes; use those rather than interpreting older clauses in isolation.
- **P1:** [bob-plugins relation cancel composition](https://github.com/bobs-org/bob-plugins/blob/d1737ea7ca1b216960a908904358f91ed1c2a17a/plugins/bob-navigation-hotkeys/src/596-relation-cancel-compose.js): preview consequence comparison and composed source cancellation; adjacent `303a-relation-inverse-phrase.js` contains the existing merge inverse.
- **P2:** [bob-plugins shared task move writer](https://github.com/bobs-org/bob-plugins/blob/d1737ea7ca1b216960a908904358f91ed1c2a17a/plugins/bob-navigation-hotkeys/src/655-plugin-inbox-route.js), plus `650-plugin-move-commit.js`: snapshots, destination-first ordering, rollback, and move focus behavior.
- **P3:** [bob-plugins `640-plugin-notes-and-task-move.js`](https://github.com/bobs-org/bob-plugins/blob/d1737ea7ca1b216960a908904358f91ed1c2a17a/plugins/bob-navigation-hotkeys/src/640-plugin-notes-and-task-move.js), `writeTaskMoveChange` / `rollbackTaskMoveChanges`: editor vs `vault.process`, preimage/postimage checks.
- **M1:** [bob-mac-capture `CaptureModels.swift`](https://github.com/bobs-org/bob-mac-capture/blob/6c103800c9ca93831e0ff79fb7320b5b92f67dfd/Sources/CaptureCore/CaptureModels.swift), `BobProcessClient.swift`: additive transport models, string modes, subprocess schema handling.
- **A1:** `plan:202611/capture_multi_target.md`, audited read during this research: intended target-run semantics, fan-out, grammar coordination, shared outputs, and unresolved split-edge alternatives in the stored text.
- **External primary sources:** [Obsidian Note composer](https://obsidian.md/help/plugins/note-composer), [Obsidian internal links](https://obsidian.md/help/links), [Obsidian plugin self-critique checklist](https://docs.obsidian.md/oo/plugin), accessed 2026-11-03. These support interaction and API precedents, not Bob-specific lifecycle conclusions.

## Recommended solution

Build a shared, deterministic task transformation planner and expose it through the proposed `>` capture form, a structured CLI, and focused Obsidian cards. Keep ordinary moves identity-preserving. Make merge retain and cancel sources, copy only authored context with visible provenance, and preserve active dependency obligations before recovery runs. Keep heading destinations distinct from task drawers, and retain source records when filing content as notes.

For Ctrl+Shift+T, make one selected bullet subtree become one new task by default; replace selected content with concise inline links and add a short origin link in every new task. This gives the requested backlink behavior while keeping the parent open and new tasks uncommitted to Today. Build stale-preview refusal, operation receipts, guarded recovery, and honest undo guarantees into the first structural writer. The quality of this feature will come from predictable outcomes and readable notes, not from adding more syntax.
