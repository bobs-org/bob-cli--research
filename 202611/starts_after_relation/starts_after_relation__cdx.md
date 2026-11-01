# Starts-after relations: an explicit handoff cue for successor offers

Independent research by **cdx**, 2026-11-01.

**Recommendation:** implement `starts after` as a built-in, nonblocking relation that offers its source task when its target is explicitly **parked** or **completed** through a managed gesture. Render its inverse as `starts before`. Reuse the existing successor choice and write path, but give every offer a precise, visible reason. Do not derive this behavior from the Pending checkbox, turn it into an ordinary dependency, or introduce a background watcher.

This is a good feature for the stated workflow: preparing a second agent prompt often becomes useful once the first prompt has been dispatched, well before the first task finishes. The strongest design treats that moment as an opportunity to choose work. It does not claim to know when an agent actually starts running.

## Scope and evidence

I independently inspected the current contracts and implementations in these checkouts:

| Repository | Inspected revision |
| --- | --- |
| bob-cli | `96155ed5a81959c2414652fb50965ec658a4f050` |
| bob-plugins | `7dbbb6debde93028654342eedeed4ae1deefc71b` |
| bob-mac-capture | `01c753b0e6e045a0cc69b3d3f51302b8423b7e55` |

I also read the audited SASE glossary and decisions concerning successor offers, sticky lanes, relation preferences and renames, and the Mac thin-client boundary. I did not consult any other researcher's report, transcript, or findings. This is source and contract research; I did not exercise a live vault, run application tests, or measure performance. Proposed behavior below is explicitly a design recommendation, not an assertion that it already exists.

## What the current system actually does

**`x*` parks work; it does not move the task out of the daily note.** Parking preserves normal work history in the closed session, applies the normal In Progress effects, and suppresses carrying that Task Link into the next placeholder. The task itself remains in its owning note. An existing link elsewhere in today's open Pomodoros can still keep it in Today. Both continuing and parked outcomes can set `[/]`; a task can already be `[/]` before it is parked. Parking is explicit planner metadata, not a durable Markdown marker. This makes a status transition or a file move the wrong trigger. [Capture close contract][capture]

The syntax is also broader than bare `x*`: explicit `x*1`, wildcard `x*`, mixed `x1*2!3~4`, and supported `=x*…` link suffixes use the same close outcomes. Trigger on the resolved outcome, not a substring in the capture draft. Event-task clock classification also affects effective outcomes, so an ineligible future event must not trigger merely because a wildcard was typed. [Capture contract][capture]

**Successors already have an appropriate interaction model.** Managed Done gestures calculate offers before applying the gesture. They use stable keys, one picker, explicit selection, destination routing, and a re-plan before writing. Capture itself never prompts: the Mac presents the choice and submits it; bare CLI capture reports offers without selecting any. Selection can link and promote a Ready task to Next and stamp freshness. Unselected dependent tasks still recover automatically. Cancellation, raw checkbox clicks, reconcile, and `x*` parking currently do not produce offers. Thus adding parking is a deliberate contract extension. [Successor contract, §§12.1–12.5 and 12.13][successors]

**Relations currently have one authored direction.** `S starts after T` belongs on **S's LINKS line**. T is the trigger task; S is the task to offer. LINKED FROM is derived and is never authoritative input. Stored mirror entries retain the source's label; chips and the Linked-from picker display an inverse phrase. Adding `starts after → starts before` to the named inverse mappings fits this architecture directly. [Relation contract, §§1, 5, 10][relations]; [Rust inverse mapping][inverse]

**This is a new kind of active relation.** Existing configured complete/cancel labels act when someone commits the relation. The proposed label instead arms a later response to an event on its target. It must not be implemented as another `CloseEffect`, and merely writing or renaming the relation must not complete or park either task. The relation contract currently says relations do not produce successor offers except through complete-label commits; that contract needs an explicit, narrow exception. [Relations, §§2, 17–18][relations]; [close-effect configuration][config]

## Critique: useful, but “starts” overpromises without explanation

The motivation is sound. A hard finish dependency unnecessarily serializes work whose preparation can overlap. There is an established distinction between finish-to-start and start-to-start dependencies: Microsoft Project's start-to-start relation constrains the successor until the predecessor starts. That analogy explains the user's intent, but Bob's proposed relation would be an advisory prompt, not a scheduling constraint. [Microsoft's scheduling documentation](https://support.microsoft.com/en-us/project/how-project-schedules-tasks-behind-the-scenes)

Three ambiguities deserve explicit product decisions:

1. **“Started” could mean active work, dispatch, or a status symbol.** In this workflow the useful signal is the user's explicit park gesture. Ordinary continued work should not interrupt with these prompts. Keep the requested label, but explain it at authoring time: **“Offers this task when the linked task is parked or completed. Does not block it.”**
2. **“Starts after” sounds like enforcement.** The task remains available before the target is parked. If Bryan instead wants it hidden or Blocked until dispatch, that is a materially different feature requiring persistent milestone state and dependency semantics. Do not silently build half of that system.
3. **Several targets might imply an AND condition.** For this advisory version, each edge independently offers the source when its target is parked or completed. Two matching events merge into one row with two reasons. Requiring every target to have been parked would need a durable record that Pending alone cannot provide.

A different approach is preferable when these distinctions matter: split “Send prompt A” from “Review result A,” and make “Prepare prompt B” an ordinary dependent of the first task. That uses current completion successors and accurately models a hard prerequisite. Its cost is another task for each dispatch. For frequent agent handoffs, the lightweight relation is the better default; for safety-critical or genuinely gated workflows, the explicit milestone task is clearer.

| Approach | Strength | Cost or mismatch | Decision |
| --- | --- | --- | --- |
| Generic Pending transition watcher | Appears automatic | Fires during continued work; misses already-Pending parks; reacts to edits/sync; cannot identify dispatch | Reject |
| Ordinary Depends-On edge | Existing blocking and recovery | Waits for completion; does not express the desired overlap | Use only for finish prerequisites |
| Explicit dispatch task plus dependency | Precise milestone and hard gate | More task management | Offer as an alternative |
| Explicit park/Done event plus relation offer | Matches the gesture, preserves choice, reuses UI | Advisory semantics need clear copy; two engines need parity | Recommend |
| Configurable relation-trigger framework | Broad future flexibility | Expands a focused feature into an automation language | Defer |

## Proposed behavioral contract

Let **B** be “Prepare evaluation prompt” and **A** be “Send implementation prompt.” Author:

```markdown
- [ ] #task Prepare evaluation prompt ^evaluate
  - 🪢 **LINKS:** starts after [[agents#^implement]]
```

On A, the existing generated Markdown representation remains:

```markdown
- 🪢 **LINKED FROM:** [[agents#^evaluate]] (starts after)
```

The rendered view on A reads **“starts before [Prepare evaluation prompt]”**. In raw source, the parenthesized label still describes B's relation to A, as existing mirrors do. This is an intentional clarification of “rendered”: storing the inverse only for this label would break the current uniform convention. If literal raw Markdown must say `starts before`, treat that as a separate mirror-format contract change, not a formatter shortcut. [Mirror format and display rules][relations]

Use existing normalized, case-insensitive label identity, including whitespace collapse and trailing-colon normalization. Recognize the exact normalized key `starts after`; do not match synonyms, substrings, or arbitrary “after” phrases. Keep `starts before` a display inverse in v1. An authored label of that spelling must not silently reverse the edge or gain semantics. Give it the same kind of inverse hint that closing labels already have: **“To offer the other task, use Linked from with ‘starts after’.”** Add no new sigil or capture grammar. [Label rules and inverse hints][relations]

| Event affecting A | Offer B? | Explanation |
| --- | --- | --- |
| Effective explicit park outcome from any supported close form | Yes, if B is eligible | A was deliberately worked and not carried forward |
| Park A while A was already Pending | Yes | Parking, not a checkbox change, is the event |
| Managed open → Done transition, including tree or complete-label completion | Yes, if B is eligible | Completion is the fallback trigger |
| Plain continued-work close or manual transition to Pending | No | No explicit park occurred |
| Drop, defer, unlink, release, or move | No | None asserts the requested handoff |
| Cancel | No | Preserve the existing distinction between cancellation and Done |
| Raw checkbox edit, reconcile, startup, sync | No | No interactive gesture to own the offer |
| Add/relabel a relation to a target already Pending or Done | No immediate offer | Authoring arms future events; it does not replay history |
| Reopen then complete A again | Yes, if B is still eligible | A new managed completion is a new opportunity |
| Select B in the offer picker | No recursive offer | Linking B is neither parking nor completing B |

“Closed” should mean **Done**, not every terminal status. That matches normal successor behavior. The relation survives all events and selections as useful context; it is not consumed.

For v1, inherit normal eligibility: an open source task outside `done/`, not hidden, not `^prj`, with no outstanding real dependencies, no future schedule, and no project blocking. Ready, Next, and Pending sources can qualify, following the existing open-task rule; choosing a Pending source never demotes it. Check actual blocking inputs rather than trusting a stale checkbox. Do not forcibly recover a relation source, delete its prerequisites, remove `#hide`, retire schedules, or stamp `[unblocked::]` merely because the target was parked.

Suppress tasks already planned before the gesture, and honor later explicit link, close, drop, block, hide, or relation-removal operations in a capture batch. A source blocked by a real dependency on A remains blocked when A is parked; it can become an ordinary dependency successor when A is completed. That coexistence must work without duplicate rows.

No new “already prompted” journal is needed. Deduplicate within the gesture and use existing planned-task suppression. Skipping a park offer does not permanently dismiss it: completing A later can offer B again. If B was selected earlier but is now unplanned and still open, it can also reappear. This is explicit **per-gesture behavior**, not a promise of one prompt per relation lifetime. Repeated annoyance would justify a later dismissal feature with an intentional reset model.

If A still has another live link today, a valid park of its current-session link still triggers. Requiring A to disappear from all of Today would make behavior depend on unrelated planning elsewhere and would not match the explicit-gesture model.

## Make the reason unmistakable and the interface quiet

Use the current Pull-In card/modal. One gesture gets one choice even when it parks some tasks, completes others, and produces several kinds of successors. Present a shared title such as **“What comes next?”** and a distinct **“Starts after”** group, alongside the existing dependency and project groups.

A compact design sketch, shown before committing the close:

```text
What comes next?                              3 offers
After parking “Send implementation prompt”

STARTS AFTER
□ Prepare evaluation prompt                  → AGENTS
  Starts after “Send implementation prompt” · on park

DEPENDENCIES CLEARED
□ Validate the migration                     → DATABASE
  Unblocked by completing “Apply schema change”

[Continue without adding]                     [Pull in 1]
```

For completion, use **“After completing ‘Send implementation prompt’.”** In a mixed batch, use a short summary (“2 parked · 1 completed”) and retain the exact reason on each row. After successful commit, change tense: **“Pulled in ‘Prepare evaluation prompt’ after parking ‘Send implementation prompt’.”** Do not claim an agent is running or a task was unblocked when Bob only observed a park.

This recommendation applies recognition-over-recall by keeping the triggering task beside the suggested work, and visibility of system status by distinguishing the planned consequence from a committed result. The layout and wording are my proposed application of those principles, not a validated usability finding. [NN/G on recognition](https://www.nngroup.com/articles/recognition-and-recall/), [NN/G on status visibility](https://www.nngroup.com/articles/visibility-system-status/)

Reuse the existing two-line row, neutral relation styling, status colors, destination capsule, keyboard controls, and fixed panel height during filtering. Put the task and destination on the first line and the causal sentence on the second; move incidental paths to existing detail/hover affordances. Screen-reader labels must announce the cause and destination. Do not encode the distinction only through a new color or icon.

Keep nothing marked initially and retain established keyboard selection semantics. The current Mac implementation treats the focused row as the effective selection when no rows are marked, so the action label must continue to state exactly what Return will pull in. Keep a visible “Continue without adding” action; follow each surface's existing Escape behavior rather than inventing a new global meaning. A disabled candidate can say “Still blocked by …” or “Scheduled for …”; do not show a modal if there are no selectable offers, though the preview/result can explain suppressed candidates.

The Mac currently builds generic context such as **“Unblocked by …”** and sometimes exposes `trigger: …` metadata. Simply sending a new enum would produce misleading or technical copy. Update the row, group, context, preview, accessibility, and completion-notice presentations together. [Mac choice model][mac-choice]; [shared presentation][mac-presentation]

## Implementation direction and traps

### 1. Separate trigger facts from status recovery

Keep completed tasks as the existing `completed` input; add a distinct parked-event input. A parked task must never be inserted into the completed set as a shortcut: that would unblock finish dependencies and could trigger project-finished logic incorrectly.

Build events from resolved close summary outcomes and staged task identity, after clock rules and selection resolution. Preserve the triggering task identity and its pre-gesture ledger anchor. The current `plan_close_successors` derives predecessors only from actual completed embedded/subtask rows and can return early before invoking the planner. Both that gate and the shared planner need the new route. [Close integration][close-code]; [planner types][planner]

Conceptually:

```text
events = completed_tasks + effectively_parked_tasks
incoming = canonical authored LINKS whose label key is starts after
candidates = sources of incoming edges whose target is in events
eligible = candidates filtered against final task/blocking/planning state
all_offers = merge(existing successor offers, eligible relation offers)
chosen = existing user selection over stable offer keys
writes = original gesture + chosen links, applied through existing write flow
```

The `completed_tasks` set remains responsible for dependency recovery. A relation-only unselected offer causes no source-task write. Existing-task picks stamp freshness and promote Ready to Next under the current rules; same-capture-created tasks retain the no-creation-stamp rule.

### 2. Discover incoming relations from authoritative data

Use resolved `(note path, block id)` identities and the shared LINKS parser, not `[id::]`, descriptions, line numbers, or stored LINKED FROM text. This must work with generated mirrors disabled, missing, or stale.

The existing dependency snapshot and `[id::]` shortcut cannot supply this candidate set: a perfectly valid relation-only task can carry no dependency fields at either end. Rust needs a batch-scoped reverse relation lookup, with staged text overlaid for captures. Obsidian already has a live relation index, but its snapshot must be paired with fresh authoritative text during re-plan. Missing plugin capability must produce a clear unavailable result, not silently masquerade as an empty relation graph.

Do not use the relation-label vocabulary cache as execution authority. It stores label counts and has a 60-second snapshot TTL, not the required current edge graph. It is useful for suggestions only. [Vocabulary scan][label-scan]; [live relation index contract][relations]

Start with one relation scan per relevant batch, reuse parsing and the note catalog, and benchmark realistic vaults before introducing a durable index. A cheap optimization may skip work only if it proves no matching edges; absence of `[id::]` or a stored mirror proves nothing. Measure ordinary closes with no match, one parked target, and wide fan-out. No performance numbers were measured in this research.

### 3. Keep offer identity independent of its reasons

Use the existing stable task key. Merge all reasons for the same task, including different predecessors and event types. I recommend priority **direct dependency → starts-after relation → project → project-finished → keep-moving** for the single displayed row, while retaining every applicable cause. This preserves the established precedence of true dependency handoffs and prevents a relation explanation from disappearing behind generic project copy.

Add structured causal metadata, for example:

```json
{
  "offer": {
    "key": "agents.md#^evaluate",
    "group": "starts_after",
    "reasons": [{
      "kind": "starts_after",
      "event": "parked",
      "predecessor": {
        "note_path": "agents.md",
        "block_id": "implement",
        "text": "Send implementation prompt"
      }
    }]
  }
}
```

This is an illustrative additive shape, not a finalized endpoint schema. A source offered through a relation belongs in a neutral collection such as `relation_successors[]`, not falsely in `unblocked[]`. Internally share a generic offer-row type. Existing dependency rows keep their fields and can gain `offer.reasons` when deduplicated with a relation cause. Update all row iterators, selection numbering, budget calculation, summaries, and net-batch filtering; do not add the array only to serialization. `keep_moving[]` is already a precedent for separating non-recovery offers. [Reporting contract][successors]; [pull-in machinery][pull-in]; [batch post-pass][net-pass]

### 4. Preserve placement and explicit choice

On a park close, selected successors use the existing closing destination and task-type routing; create a continuation only when a chosen row actually needs one. On an ordinary task completion, use its slot or existing implicit destination rules. Do not insert successor bullets into closed work history or create an empty continuation merely to display an offer. Respect current destination overrides and refusal behavior.

Remain within plan → choose → re-plan → apply. In a batch, a relation must exist when its triggering item is evaluated: a later relation addition must not retroactively fire for an earlier park. Conversely, a later removal/relabel or source close/drop must invalidate an earlier offer. Two triggering items for the same source should produce one draft-level key and one link, with merged reasons. Define this explicitly in shared vectors rather than relying on array order.

### 5. Revalidate the explanation as well as the write

Re-read the target event, source task, authored relation, blocking prerequisites, and destination at final application. A still-existing task key is insufficient if its `starts after` edge disappeared after preview. If the selected key or its justification changes, refresh the choice and require renewed selection rather than silently substituting another task or reason.

Capture has disk-preimage checks and rollback, but its source explicitly notes that these are not cross-process locking or a fully serialized transaction. Extend checks to relation/blocking read dependencies needed for the selected offer and reuse the existing transaction boundary; do not claim globally exactly-once effects across hosts. On uncertain scans, suppress unsafe candidates and expose “Could not check starts-after offers.” A plain CLI close without requested picks can retain the current fail-soft reporting pattern; a requested pick whose basis cannot be verified must fail without being replaced. [Commit preimage guard][commit]

### 6. Treat built-in label lifecycle and rollout as part of the feature

Seed `starts after` in label suggestions even with zero authored uses, show its effect description, and include its inverse in the existing catalog. Hiding the label only hides suggestions; it must not disable existing edges. Unlinking or renaming away from the canonical key disarms future events. Renaming into it arms future events, with a preview warning, but never fires immediately. Preserve existing transactional rename/history semantics.

Prevent the key from simultaneously being configured as a complete or cancel label. Detect and explain the conflict; do not silently choose one behavior. Existing label uses should be disclosed in rollout preview: this spelling becomes behavioral on future managed gestures. Do not rewrite old relations or replay old parks on upgrade.

Ship Rust behavior, the Obsidian completion path, mirror rendering, and Mac presentation as a coordinated feature. Keep JSON fields additive and decode new collections with an empty default, but do not assume this alone guarantees old-client UX: an old Mac may see an increased offer count without understanding the new row collection. Feature-detect support, provide an explicit compatibility message where necessary, and test old/new pairings. Reuse the existing global successor-offer switch if its documented scope is broadened; mirror visibility and label hiding must never serve as execution switches.

The main code surfaces are:

| Surface | Work |
| --- | --- |
| `src/native/task_relations/inverse.rs` and JS `145a-relation-inverse-phrase.js` | Named inverse and parity vectors |
| Relation catalog/completion and close-label policy | Seeded special label, explanation, inverse hint, conflict handling |
| `capture/pomodoro_close.rs`, `capture/task_complete.rs` | Collect real events, bypass dependency-only gates, wire shared candidates |
| `task_complete/successors.rs` and capture output/pull-in/batch helpers | Candidate merge, neutral reasons, filtering, placement, serialization |
| Plugin task-status-cycler successor planner/runtime and nav successor modal | Managed Done parity, fresh relation reads, one causal picker |
| Mac `CapturePullInChoice` and `CaptureSuccessorPresentation` families | Decode, label, group, explain, select, announce, summarize |
| `docs/task-relations.md`, `docs/task-dependencies.md`, `docs/capture.md` | Normative semantics and shared acceptance vectors |

This research does not propose editing durable SASE memory. Any eventual memory update must follow its separate write workflow.

## Acceptance evidence worth requiring

Use shared behavioral fixtures across Rust and JavaScript, then Swift decoder/presentation tests. The high-value cases are:

1. Correct B→A direction, normalized label match, rendered inverse, and mirrors disabled or stale.
2. `x*`, `x*1`, mixed park/complete/drop, and link suffixes; wildcard expansion uses effective outcomes, including event-clock exclusions.
3. Already-Pending A parks successfully and offers B; ordinary continued work, raw edits, cancel, reconcile, and moves never offer it.
4. Managed Done parity across capture `!`, Pomodoro embeds, task-line completion, status-cycle Done, tree children, and complete-label gestures.
5. Both tasks lack `[id::]`; relation-only B is still discovered and gets no synthetic dependency fields.
6. Real dependencies, future schedule, project blocking, hidden/done/project tasks, duplicate IDs, ambiguous/broken links, and an incomplete scan all receive deliberate outcomes.
7. Two relation targets, relation plus dependency/project causes, repeated sightings, and mixed trigger types produce one selectable row with complete reasons.
8. A later batch item closes, links, drops, hides, blocks, unlinks, or relabels B; selected-but-invalidated keys are refused. A relation added only after the event does not retroactively trigger.
9. Preview changes nothing; no selection leaves B unchanged; selection promotes/stamps appropriately and preserves the relation and closed-session history.
10. No selected rows means no new placeholder; selected rows use closing/type/override destinations exactly once.
11. Concurrent relation deletion, target change, dependency change, destination closure, and write failure refresh/refuse safely and preserve rollback behavior.
12. Skip at park then offer at completion; source already planned is suppressed; later eligible re-offering matches the documented per-gesture policy.
13. Mixed-cause UI, long titles, narrow panel, keyboard-only selection, screen-reader text, and old/new client combinations retain truthful copy.

Before landing Mac application changes, compile/type-check the affected macOS targets as required by that repository; portable model tests alone are insufficient. For plugin implementation, edit source fragments, rebuild generated entrypoints, run focused successor/relation suites and build checks, then deploy through the repository's required `bob plugins sync` workflow. Follow the normal bob-cli release train rather than changing its version manually.

## Requirement adjustments called out

- Interpret “moved out of the daily file” as **not carried from the closed session**, not moving/deleting the task or its historical link.
- Define “starts” as an **explicit park event**, including already-Pending tasks and equivalent close syntax; keep ordinary In Progress changes silent.
- Interpret “closed” as **managed Done**, excluding Cancelled and raw edits.
- Make this an **advisory, per-edge offer**, not a blocking constraint or an all-predecessors-started gate.
- Render `starts before` through the existing inverse mechanism; retain the normal raw mirror representation.
- Do not fire when the relation is written, renamed, reconciled, or discovered on startup. Skipped offers can return on a later qualifying gesture.
- Preserve one picker and explicit choice; distinguish relation reasons from actual unblocking in both data and copy.

The unresolved product preference is whether Bryan ultimately wants a reminder opportunity or a hard start prerequisite. The prompt asks for a successor prompt, so the advisory interpretation is the appropriate implementation default. No additional user decision is needed to research or specify that default.

## Source links

The code links below are pinned to the revisions inspected. External sources were checked on 2026-11-01. SASE policies were read through `sase memory read`, not inferred from unrelated research.

[relations]: https://github.com/bobs-org/bob-cli/blob/96155ed5a81959c2414652fb50965ec658a4f050/docs/task-relations.md
[capture]: https://github.com/bobs-org/bob-cli/blob/96155ed5a81959c2414652fb50965ec658a4f050/docs/capture.md
[successors]: https://github.com/bobs-org/bob-cli/blob/96155ed5a81959c2414652fb50965ec658a4f050/docs/task-dependencies.md#12-successor-offers
[inverse]: https://github.com/bobs-org/bob-cli/blob/96155ed5a81959c2414652fb50965ec658a4f050/src/native/task_relations/inverse.rs
[config]: https://github.com/bobs-org/bob-cli/blob/96155ed5a81959c2414652fb50965ec658a4f050/src/native/config/relations.rs
[close-code]: https://github.com/bobs-org/bob-cli/blob/96155ed5a81959c2414652fb50965ec658a4f050/src/native/capture/pomodoro_close.rs#L631
[planner]: https://github.com/bobs-org/bob-cli/blob/96155ed5a81959c2414652fb50965ec658a4f050/src/native/task_complete/successors.rs
[label-scan]: https://github.com/bobs-org/bob-cli/blob/96155ed5a81959c2414652fb50965ec658a4f050/src/native/relation_labels/scan.rs
[pull-in]: https://github.com/bobs-org/bob-cli/blob/96155ed5a81959c2414652fb50965ec658a4f050/src/native/capture/pull_in.rs
[net-pass]: https://github.com/bobs-org/bob-cli/blob/96155ed5a81959c2414652fb50965ec658a4f050/src/native/capture/task_complete.rs#L1112
[commit]: https://github.com/bobs-org/bob-cli/blob/96155ed5a81959c2414652fb50965ec658a4f050/src/native/capture/commit.rs#L163
[mac-choice]: https://github.com/bobs-org/bob-mac-capture/blob/01c753b0e6e045a0cc69b3d3f51302b8423b7e55/Sources/BobMacCapture/CapturePullInChoice.swift
[mac-presentation]: https://github.com/bobs-org/bob-mac-capture/blob/01c753b0e6e045a0cc69b3d3f51302b8423b7e55/Sources/CaptureCore/CaptureSuccessorPresentation.swift

## Recommended solution

Build **one narrowly defined special relation**: **B starts after A** offers B when a managed gesture explicitly parks or completes A. Render **A starts before B**, preserve authored relation history, keep real blocking rules intact, and let Bryan choose through the existing successor picker. Explain the exact predecessor and event on every offer, with additive structured reasons shared across clients. Implement relation discovery independently of dependency IDs, then reuse stable keys, destination routing, revalidation, and the existing write path.

This delivers the useful handoff moment without adding another status, a durable trigger journal, or a general automation engine. If the desired behavior later becomes “B must remain unavailable until every A has really started,” use explicit dispatch milestones or design a true start dependency as a separate feature.
