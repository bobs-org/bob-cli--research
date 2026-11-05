# Resolve tasks where successors are offered

Independent design research by **cdx**, 2026-11-05.

**Recommendation:** add staged **Complete task** and **Cancel task** actions to the existing successor card in Obsidian and Bob Mac Capture. Let people resolve several rows before applying their choices. Keep pull-in selection, task resolution, and dismissal visibly distinct. Preserve each client's existing commit boundary; do not launch independent task writes from a picker shortcut.

This is a worthwhile feature. The successor card is already a moment of informed review: the predecessor just changed, related work is visible, and its relevance is unusually easy to judge. Deferring an obvious completion or cancellation creates unnecessary review work. The risk is turning a small planning choice into an ambiguous bulk editor. The design below keeps that expansion bounded.

## Evidence and limits

I inspected the current source and contracts independently. I did not consult the other researchers' reports, transcripts, summaries, or findings. The report contains design recommendations, not implementation or usability-test results. I did not run either graphical client, measure latency, or execute repository test suites. Existing tests cited below were read as evidence of intended behavior.

| Repository | Inspected commit |
| --- | --- |
| bob-cli | `58e98558fb2c85c438ab866d992123531a90ed53` |
| bob-plugins | `7b7c52f10f42f1b38553e991a0750852d2a46761` |
| bob-mac-capture | `9714a56d0d64aa3be2b2bcaf89977a349062604c` |

I also read the audited SASE glossary entries for Successor Offer, Task Successor, Task Link, and Task Dependency Link; the decisions `unblocked-tasks-are-offered`, `mac-capture-is-a-thin-client`, and `answering-advances-the-walk`; and the CLI and artifact rules. External design references are primary Apple and W3C guidance, linked where used. Those references guide interaction design; they do not establish Bob's product semantics.

## What the implementation implies

### “Successor” covers different relationships

The card can contain direct hand-offs, recovered project residents, project-finished offers, keep-moving candidates, capture-created project tasks, relation successors, and note-pull residents. Some rows are dependents; others are simply useful next work. Some need a block ID, some are folded, and some are shown muted because they remain blocked. The meaning of completing a row cannot be inferred from its group. Eligibility and consequences must come from the task engine. [Offer contract][offer-contract]

The accepted rule is recovery without automatic scheduling: unpicked tasks can unblock without receiving a Task Link; explicit picks receive links and the associated lane/freshness effects. This feature should not turn completion or cancellation into an implicit pull-in.

### The clients have different transaction boundaries

| Behavior | Obsidian | Bob Mac Capture |
| --- | --- | --- |
| When the card opens | In the managed Done path inspected, the predecessor is already closed. The successor pass then plans, asks, re-reads, and applies. | The draft has been previewed; the real capture has not committed. |
| Escape today | Chooses no successors; the earlier completion remains. | Returns to the draft without the real capture write. |
| Return without marks | Pulls in the highlighted selectable offer. | Same highlighted-row fallback. |
| Existing multi-selection | Marks mean pull-in. Tab toggles and moves; Ctrl/Cmd+A marks the highlighted group. | Marks mean pull-in. Space toggles; Cmd+A marks all offers. |
| Failure boundary | Successor linking is best effort; it does not roll back the original close. | Bob stages the whole capture and checks preimages, with rollback on ordinary commit failures. |

These are not cosmetic differences. Obsidian's completion code calls the task write **before** `finalizeClosedTasks`; the successor mixin explicitly says linking failure never rolls back the close. Mac stores the original draft and submits it with chosen keys only after confirmation. [Obsidian completion][obs-complete], [successor writer][obs-writer], [Mac submission][mac-submit], [Mac Escape test][mac-test]

The Rust writer explicitly says its optimistic guards are **not cross-process locking or a fully serialized transaction**. “One capture batch” is the right implementation boundary, but it is not a promise of database-grade crash atomicity. [Capture commit guard][capture-commit]

### Complete and Cancel are domain operations

Completion can affect ledger links, dependents, project state, and further offers. Cancellation writes cancelled state/date, manages optional cancellation history, prunes applicable open ledger links, and recovers dependents. **Cancellation currently does not offer successors.** Cancelling a project outcome does not mean cancelling all project residents. [Close semantics][relation-contract], [cancel engine][cancel-engine], [cancel recovery][cancel-recovery]

There is an important scope difference: capture's `!note:id` and complete-label path can close embedded task trees, while some Obsidian link gestures are explicitly root-only. Reusing a convenient public completion entry point could close tasks the successor card never showed. [Completion tree][complete-tree], [completion adapter][complete-adapter], [relation contract, CP4][relation-contract]

### Existing keys matter

Ctrl+Enter means Pull In & Open in Mac's card. Ctrl+Shift+Enter retargets successors in Obsidian. Ctrl+X has other **contextual** meanings elsewhere: closing a Highlights tab in Mac Capture and merging Pomodoros in an Obsidian picker. Those uses do not prohibit a successor-specific action, but rule out installing a global Ctrl+X handler. [Mac router][mac-router], [Obsidian picker][obs-picker], [Obsidian Pomodoro keys][obs-keys], [Mac keyboard documentation][mac-keys]

## Critique and alternatives

The capability is good; “two new keys that immediately write task status” is not a sufficient design.

| Approach | Benefit | Cost / verdict |
| --- | --- | --- |
| Open the normal Task Card or source note | Reuses rich editing | Loses successor context and interrupts a quick decision. Keep as an escape hatch. |
| Immediately complete/cancel on a shortcut | Fast and superficially simple | Breaks Mac's write-free Back, demands cross-file undo, and can trigger nested pickers. Reject. |
| Stage actions in the card, then Apply | Reviewable and reversible before commit; fits Mac capture | Needs a richer decision model and an Obsidian planning adapter. **Recommend.** |
| Make the card a full task manager | Broad functionality | More controls and harder-to-predict scope. Defer scheduling, priority, rewording, merge, and bulk cancellation. |
| Add a cleanup-later tray | Preserves the picker | Recreates the postponed work motivating the request. Reject for this need. |

The feature should answer “Which should I work on next?” and “Which no longer need doing?” without creating a new general review mode.

The largest cost is not drawing two icons. It is composing actions across the Rust and JavaScript engines, retaining identity during replanning, and reporting the truth when Obsidian has already written part of the gesture. Budget this as a coordinated change across three repositories, not a keyboard tweak.

## Adjusted requirements

These changes to the initial request are deliberate:

1. **Use explicit verbs:** “Complete task” and “Cancel task,” not “Close.” Completion means already done; cancellation means no longer intended. Dismissal is “Back” or “Continue without pulling in.”
2. **Stage the action:** Ctrl+X / Ctrl+Shift+X prepare a change; Apply commits it. Several tasks can be resolved without several writes or confirmations.
3. **Target the focused row initially:** existing marks remain pull-in choices. Do not reinterpret marked rows as cancellation targets. Resolve several tasks by repeating a row action. Defer a distinct bulk-resolution mode until it is demonstrably needed.
4. **Resolve the displayed task only:** add an explicit single-task completion scope instead of inheriting capture's embedded-tree close. Children, embedded tasks, and prerequisites are not implicitly resolved. Reuse normal status, date, ledger, and recovery primitives around that scope.
5. **Keep exclusions explicit:** initially refuse recurring tasks, unsupported/custom statuses, ambiguous identities, and tasks newly created by the uncommitted capture. Explain why and provide an appropriate editing route.
6. **Preserve cancellation semantics:** cancellation recovers dependents but does not become a new offer trigger. Completion-generated offers may appear in the same card.
7. **Preserve each client's Escape boundary:** Escape does not restore the original Obsidian predecessor. Mac's original draft remains unwritten.
8. **Provide visible actions as well as keys:** a shortcut-only feature is difficult to discover and cannot adequately explain its scope.

The single-task scope and focused-row choice are product decisions, not established shared behavior. They deserve explicit acceptance when this research becomes an implementation proposal. They substantially reduce surprising side effects.

## Interaction design

### A small addition to the card

Keep existing group explanations, destinations, plan meter, filter, and row rhythm. Add one compact action area for the focused task. Avoid a row of bright destructive icons on every offer.

Illustrative layout; this is proposed wording, not a screenshot:

```text
Keep ‹Release› moving
Review next work                         Filter tasks…

  ☑  Write rollout notes                         → FIX
     release.md · Ready
  ·  Update the old dashboard             ✓ Will complete
     release.md · This task only
  ·  Renew the retired service            ⊘ Will cancel
     ops.md · Reason: No longer needed

Focused: Update the old dashboard
[Complete task  ⌃X] [Cancel task  ⌃⇧X] [Clear action]

1 to pull in · 1 to complete · 1 to cancel       [Apply changes ↵]
Nothing else will be pulled in unless marked.
```

Use a dedicated state glyph for pending resolution so it cannot be mistaken for the pull-in checkbox.

- Keep text readable and rows in place while decisions are pending. Do not strike through a task before it has actually closed; Bob's relation-close design already makes this distinction.
- Use `✓ Will complete` and `⊘ Will cancel`, with words and established Done/Cancelled tints. Reserve red for errors and amber for caveats, consistent with the relation design. [Relation-close presentation][relation-contract]
- Replace the destination capsule on a resolving row with the pending-action capsule. A row cannot promise both a link and a close.
- Expose the focused task's full title and note in a detail area. Show “This task only; 2 embedded tasks stay open” or “Project outcome; 4 project tasks stay open” when applicable.
- Keep counts and Apply fixed during filtering. If a staged action is filtered out, say “1 change outside this filter” and offer “Show changes.”
- Avoid reordering and focus jumps during preview. Honor reduced motion.

Beauty comes from stable geometry, restrained color, strong typography, and unambiguous consequences. A pending badge is more useful than a celebratory animation for a write that has not happened.

### Exact state model

Each offer has one local disposition:

| Disposition | What Apply does |
| --- | --- |
| Leave | No explicit row action; ordinary recovery from the originating gesture may still occur. |
| Pull in | Link and apply existing lane/freshness behavior, using any explicitly chosen destination. |
| Complete | Complete this task only, with normal managed consequences. No pull-in for the same task. |
| Cancel | Cancel this task only, with normal cancel consequences. No pull-in for the same task. |

Initially all dispositions are Leave. Existing marks map to Pull in. Focus is separate from disposition.

Ctrl+X sets the focused eligible row to Complete; Ctrl+Shift+X sets it to Cancel. Switching actions replaces the previous disposition. The same key on the same pending action is a no-op, not a toggle; repeats never advance to another task. Preserve previous state in local undo history, including the pull-in destination.

Space or the existing mark gesture can deliberately replace a pending resolution with Pull in. The summary changes immediately. “Clear action” returns the row to Leave; Undo restores its actual previous disposition. Name these distinct operations accurately.

Keep focus on the acted-on row. Down moves to the next when desired. That navigation press avoids a held key or delayed event resolving several tasks.

### Keyboard scope

The suggested Ctrl+X / Ctrl+Shift+X pair is reasonable **as a local list shortcut**, with qualifications:

- On Windows/Linux Ctrl+X is Cut. In a filter, reason field, or other editable text, preserve normal editing. On macOS preserve Cmd+X everywhere it normally cuts. Apple cautions against repurposing standard shortcuts. [Apple keyboard guidance](https://developer.apple.com/design/human-interface-guidelines/keyboards/)
- Require an eligible focused offer and ownership by this card. In Obsidian this needs a real list-focus contract; a highlighted index while the filter owns editing focus is insufficient. List navigation should move focus into the list; typing can return to filtering without losing decisions. Test the existing Tab-to-mark interaction and provide an accessible route to the action area.

Do not take Ctrl+Enter or Ctrl+Shift+Enter away from their existing meanings. Keep action buttons available when a shortcut is unavailable. Show contextual hints only where applicable. Ignore composition and repeat events; retain protection against the Enter that opened the card also applying it.

Consider a platform-specific override if testing exposes an unavoidable collision. A general keybinding system is unnecessary for this feature.

### Return, Skip, and Escape

The highlighted-row fallback is the easiest serious mistake to introduce. After completing A, Return must not unexpectedly link B.

| Situation | Return / Apply |
| --- | --- |
| No staged Complete/Cancel | Preserve today's pull-in behavior: marks, otherwise highlighted offer. |
| Any staged Complete/Cancel | Apply those actions and **explicitly marked** pull-ins only. Disable highlighted-row fallback. |
| Every offer staged Complete/Cancel; zero pull-ins | Apply remains enabled. |
| Replanning or invalid action needs attention | Apply waits or is disabled with a visible reason. |

With resolutions staged, rename “Pull In” to “Apply changes,” with the three counts adjacent. A completion-only batch must not display a disabled “Pull In 0” button.

Mac's Shift+Return Skip currently submits with no pull-ins. While terminal actions are staged, disable that shortcut/control with “Apply or clear task changes first”; provide **Clear changes** to restore the normal Skip path. This avoids silently discarding resolutions or treating “Skip” as permission to cancel tasks.

Escape discards the card's staged decisions. In Mac it returns to the draft; in the inspected Obsidian Done flow the original close remains, with recovery/continuation following existing behavior. Explain this in contextual copy rather than adding confirmation dialogs. During a write, Escape must not imply cancellation of a transaction already in progress.

### Cancel reason and undo

Show a collapsed optional “Add reason…” field for pending cancellation. Do not require a reason or open another modal per task. Blank reason must preserve Task Card rules: no invented “obsolete” reason, no new empty log, and the established fallback when an existing Cancel Log requires an entry. The Rust helper's current relation-oriented input is not itself a complete implementation of that UI policy; extract or parameterize the appropriate adapter and test parity. [Task Card cancel stage][obs-cancel-stage], [cancel line helpers][cancel-line]

Provide local **Undo task choice** and **Clear action** before Apply. Standard Undo in a text field still edits text. Apple recommends predictable, specifically named undo operations; follow that guidance without implying a cross-file undo mechanism already exists. [Apple undo guidance](https://developer.apple.com/design/human-interface-guidelines/undo-and-redo)

After Apply, use existing reopen/edit facilities and truthful receipts. Do not ship “Undo everything” unless a guarded inverse operation restores intended task, ledger, and dependency effects without overwriting later edits. Staging is the first release's cheap, reliable correction path.

## Further successors: one card, explicit decisions

Completing offered task B may reveal C. Hiding C until later review partly defeats this feature. Recursively opening another picker is worse.

Re-plan against pending decisions and append new offers inside the **same** card, under “Newly available,” with “After completing B” explaining the cause. They start unmarked. Preserve existing row order and focus; never jump into the new section. Retain group distinctions within it.

1. A is the original completion; B is offered.
2. Stage Complete on B. The preview includes C, unselected.
3. Leave C, explicitly pull C in, or explicitly resolve C too.
4. Apply the acknowledged decisions once.

Every new close requires human action. Never auto-complete a graph, preselect newly revealed work, or impose a hidden offer-count cap. Deduplicate by task identity while retaining multiple causes. Use visited identities and ordinary planner resource limits to prevent computation loops; visibly refuse if preview cannot finish.

Undoing B may invalidate a dependent decision on C. Mark that decision invalid and explain why; do not silently execute, remap, or discard it while committing the rest. Require acknowledgement of the refreshed preview.

Cancel B retains recovery-only behavior. Do not generate a pull-in group solely from cancellation. Offers with another valid cause may survive. Pin this distinction in shared fixtures instead of client heuristics. [Cancel recovery][cancel-recovery]

## Implementation direction

### Shared contract and capabilities

Extend the protocol with per-row capabilities, action scope, explanatory consequences, and opaque identity/preconditions. Complete might be disabled with “Repeating task—complete in Obsidian” while Pull in remains available. Model muted, blocked, unsupported, and newly created rows independently of styling.

Start with existing actionable offers. Do not make every folded or muted row closable merely because it appears in a backing array. Cleanup of blocked/hidden inventories is a separate expansion.

Proposed request shape—not finalized CLI spelling:

```json
{
  "preview_id": "opaque",
  "actions": [
    {"key": "release.md#^notes", "kind": "pull_in"},
    {"key": "release.md#^dashboard", "kind": "complete", "scope": "task"},
    {"key": "ops.md#^service", "kind": "cancel", "reason": "No longer needed"}
  ]
}
```

Absence means Leave. Reject conflicting actions for an identity; array order must not determine whether a task gets cancelled or linked. Responses need refreshed offers, consequences, and per-action outcomes, not only `picked_count`.

Preserve legacy `--pull-in`. Prefer an additive structured internal subprocess argument on `bob capture`, rather than generating capture prose, overloading numbers, or adding a subcommand under `capture`. Final naming belongs in the implementation proposal and must follow CLI rules. Mac passes arguments directly, never shell commands.

Use capability detection and the next appropriate Obsidian successor API version. Both picker **and writer/caller** must support resolution before controls appear. New Mac with old bob remains a normal pull-in card. Old clients retain behavior. Never discard unsupported resolutions and report success. [Picker API][offer-contract], [Mac process client][mac-process]

### Identity and planning order

Current offer keys use path/block ID when available; id-less rows use description digests and occurrence ordinals. These are useful selection handles, not sufficient identity proof after duplicate insertion or edits. [Offer key construction][offer-engine]

For id-less targets, bind actions to original note/task preimages and a preview revision. Conservative refusal after relevant change is preferable to resolving a similar neighbor. Mint no block IDs on preview, Escape, or merely to simplify UI state. Committed pull-ins can continue to mint as today.

Conceptual planner order:

1. Plan the originating gesture without successor links.
2. Establish offer identities authorizing row actions.
3. Apply explicit resolutions to the shared in-memory overlay using single-task scope and existing domain primitives.
4. Recover state and derive resulting offers; retain authorization/history for resolved rows although they are no longer open offers.
5. Validate pull-ins against final open state and retain only explicit valid choices.
6. Produce the effect summary; revalidate identity, source bytes, date/config, and destination anchors before writing.

Step 4 matters: the current net pass removes offers closed by later capture items. A naive implementation followed by existing unknown-pick validation could reject its own correctly resolved tasks. Validate resolutions against authorized preview identities, not only final open offers. [Capture selection][capture-pull], [net planning][capture-plan]

Use generation guards so old preview replies cannot replace newer decisions. Materially changed consequences require a fresh visible preview and new Apply; a dry run is not permission to mutate whatever later occupies the same row.

### Rust and Mac

Mac remains presentation and subprocess orchestration. It does not parse Markdown, generate cancellation fields, walk dependencies, or invent eligibility. Extend `CapturePullInChoiceState` from marks/highlight fallback to dispositions and local history. Update submission, footer, rows, key routing, Codable models, and the process client together. [Mac state][mac-state], [Mac view][mac-view], [Mac submission][mac-submit]

Bob composes original draft, resolutions, and surviving links into one capture batch. Refactor completion/cancellation helpers to accept the scope and reason policy. Do not launch bob once per row or append guessed `!` syntax. The structured path also supports existing offered tasks without block IDs.

Single-task completion is new work: `RootPolicy::Explicit` still walks embedded children and must not substitute for the proposed scope. [Tree implementation][complete-tree]

A refused batch retains the draft and choices, identifies the changed target, and offers refresh. After a transport timeout with unknown outcome, read state before retrying; do not replay a capture that may already have created a project or appended content. Distinguish refusal from unknown outcome using the process client's conventions.

### Obsidian

The navigation picker returns decisions without writing. Its cycler/nav owner prepares and validates domain effects. Reuse editor-buffer-first reads and guarded writers; an unsaved editor is authoritative over disk. Do not invoke bob-cli behind the open editor to bypass those paths.

Expose pure planning beneath completion/cancellation finalization so previews derive offers **without another UI-opening gesture**. Recursively calling `finalizeClosedTasks` while a picker is open risks nested dialogs or lost offers through the one-picker guard.

Prepare all edits before the first secondary write. Group same-note edits into one editor transaction. Preserve cross-note preimage checks and per-task failure reporting. The existing best-effort infrastructure does not become globally atomic merely because actions share a card.

After partial failure, keep a receipt in the card/notice: “Completed B; could not cancel D—note changed.” Disable applied actions; do not retry them automatically. Recompute links whose eligibility depended on failed resolutions. The predecessor remains closed. A partial failure must never resemble a successful Apply.

Hold the existing review-walk gesture lock through the card. The initiating landing advances once when the gesture settles, retaining established dismissal behavior; secondary resolutions do not each advance it. Reopening the predecessor must not undo deliberate successor resolutions. Existing reopen receipts restore only matching untouched successor state; retain that ownership boundary. [Successor application][obs-project-writer], [reopen receipts][obs-receipts]

## Acceptance scenarios

These are requirements for implementation, not tests executed for this report.

| Scenario | Required result |
| --- | --- |
| Complete B, cancel C, mark D, Apply | Only B/C resolve; only D is linked; three outcomes distinguished. |
| Resolve one row with other rows marked | Only focused row changes disposition; other marks stay pull-ins. |
| Complete all offers, zero marks | Apply enabled; no implicit link. |
| Stage resolution, Return over another row | No highlighted-row fallback. |
| Escape in Mac / Obsidian | Mac writes no capture; Obsidian discards secondary choices, keeps predecessor. |
| Blank reason, existing Cancel Log, authored reason | Task Card log/date semantics match in Rust and JS. |
| Embedded child or project residents exist | Only displayed task closes; retained work is described. |
| Recurring/custom/new task | Disabled/refused with reason; no recurrence corruption. |
| Duplicate id-less descriptions; mid-card edits | Refuse stale/ambiguous target; never resolve its neighbor. |
| Complete B reveals C; undo B | Dependent action on C becomes invalid; Apply needs a new decision. |
| Cancel B recovers C | No cancellation-generated offer. |
| Multiple causes or conflicting actions | One identity/disposition; malformed requests rejected. |
| Destination moves/closes; task blocks; date/config changes | Replan/refuse with visible consequences. |
| Key repeat, IME, Return carried from opener | No extra action or accidental Apply. |
| Filter/reason editing; Cut or Undo | Normal text editing preserved. |
| Filter/collapse hides staged actions | Counts visible; changes remain inspectable. |
| Old bob or old picker/writer | Legacy pull-in works; unsupported resolutions cannot submit. |
| Obsidian cross-note partial failure | Per-action receipt; no unconditional success or invalid dependent links. |
| Reopen original predecessor later | Deliberately resolved successors stay resolved. |
| Timeout after possible Mac commit | Refresh before retry; no blind duplicate capture. |

For Obsidian, use an accessible grouped choice list with a separate action toolbar, rather than burying buttons inside `role=option`. W3C distinguishes focus from selection and explains why listbox options are unsuitable containers for interactive descendants. Review the existing focus/mark semantics when adding another state. [W3C listbox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/listbox/)

Expose action scope to assistive technology. Announce pending state, results, and refusals without reading the entire card. Test actual VoiceOver and keyboard behavior, not labels alone. W3C's toolbar example illustrates scoped shortcuts and deliberate focus management, and calls for assistive-technology testing before production use. [W3C listbox with action toolbar](https://www.w3.org/WAI/ARIA/apg/patterns/listbox/examples/listbox-rearrangeable/)

Add shared Rust/JS vectors for scope, cancellation, identity, chains, and failures. Extend Mac choice/model/router tests for zero-link Apply and stale generations. Verify light/dark appearance, high contrast, reduced motion, long titles, and large groups. Swift changes need compilation and exact-SHA macOS CI under repository rules; portable checks cannot validate native targets. Deploy plugin changes from bob-plugins through `bob plugins sync`.

## Delivery judgment

Ship the engine/contract and capability negotiation first, followed by both clients against shared fixtures. A useful first vertical slice is an ordinary existing task, staged Complete/Cancel, correct Apply/Escape, and zero-link submission. Expand that tested path to project outcomes, id-less offers, and completion-generated offers before declaring the supported scope complete. This is implementation research, not permission to stop at that first slice.

Keep bulk resolution, recurring-task handling, a general task manager, and global cross-file undo outside the first release. If same-card replanning is prohibitively expensive, the defensible fallback is staged resolution with an explicit result describing recovered work—not immediate writes concealed behind the old picker. Dropping completion-generated offers is a stated product compromise because it weakens the managed-Done contract.

The main uncertainty is usability. Test five short tasks with Bryan: complete one offer; cancel without a reason; pull one in while completing another; undo a pending choice; escape. Watch whether marks are mistaken for closure targets, whether the clients' existing Escape difference surprises him, and whether list-focus scoping makes Ctrl+X discoverable enough. Those observations should guide any later bulk mode or key change.

## Source index

Repository links are pinned to inspected commits; function names in the text are search anchors. Files were read from SASE-opened local checkouts, not web-fetched repository contents.

[offer-contract]: https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/docs/task-dependencies.md
[relation-contract]: https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/docs/task-relations.md
[complete-tree]: https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/task_complete/tree.rs
[complete-adapter]: https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/capture/task_complete.rs
[cancel-engine]: https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/task_cancel/mod.rs
[cancel-recovery]: https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/task_cancel/recovery.rs
[cancel-line]: https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/task_cancel/line.rs
[capture-commit]: https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/capture/commit.rs
[capture-pull]: https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/capture/pull_in.rs
[capture-plan]: https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/capture/plan.rs
[offer-engine]: https://github.com/bobs-org/bob-cli/blob/58e98558fb2c85c438ab866d992123531a90ed53/src/native/task_complete/successors.rs
[obs-picker]: https://github.com/bobs-org/bob-plugins/blob/7b7c52f10f42f1b38553e991a0750852d2a46761/plugins/bob-navigation-hotkeys/src/206-successor-picker-modal.js
[obs-complete]: https://github.com/bobs-org/bob-plugins/blob/7b7c52f10f42f1b38553e991a0750852d2a46761/plugins/task-status-cycler/src/160-plugin-completion.js
[obs-writer]: https://github.com/bobs-org/bob-plugins/blob/7b7c52f10f42f1b38553e991a0750852d2a46761/plugins/task-status-cycler/src/135-plugin-successors.js
[obs-project-writer]: https://github.com/bobs-org/bob-plugins/blob/7b7c52f10f42f1b38553e991a0750852d2a46761/plugins/task-status-cycler/src/137-plugin-successor-project.js
[obs-receipts]: https://github.com/bobs-org/bob-plugins/blob/7b7c52f10f42f1b38553e991a0750852d2a46761/plugins/task-status-cycler/src/136-plugin-successor-receipt.js
[obs-cancel-stage]: https://github.com/bobs-org/bob-plugins/blob/7b7c52f10f42f1b38553e991a0750852d2a46761/plugins/bob-navigation-hotkeys/src/380-picker-cancel-and-lane.js
[obs-keys]: https://github.com/bobs-org/bob-plugins/blob/7b7c52f10f42f1b38553e991a0750852d2a46761/docs/bob-navigation-hotkeys.md
[mac-state]: https://github.com/bobs-org/bob-mac-capture/blob/9714a56d0d64aa3be2b2bcaf89977a349062604c/Sources/BobMacCapture/CapturePullInChoice.swift
[mac-view]: https://github.com/bobs-org/bob-mac-capture/blob/9714a56d0d64aa3be2b2bcaf89977a349062604c/Sources/BobMacCapture/CapturePullInChoiceView.swift
[mac-submit]: https://github.com/bobs-org/bob-mac-capture/blob/9714a56d0d64aa3be2b2bcaf89977a349062604c/Sources/BobMacCapture/CapturePanelModel.swift
[mac-router]: https://github.com/bobs-org/bob-mac-capture/blob/9714a56d0d64aa3be2b2bcaf89977a349062604c/Sources/BobMacCapture/CaptureKeyCommandRouter.swift
[mac-process]: https://github.com/bobs-org/bob-mac-capture/blob/9714a56d0d64aa3be2b2bcaf89977a349062604c/Sources/CaptureCore/BobProcessClient.swift
[mac-test]: https://github.com/bobs-org/bob-mac-capture/blob/9714a56d0d64aa3be2b2bcaf89977a349062604c/Tests/BobMacCaptureTests/CapturePullInChoiceModelTests.swift
[mac-keys]: https://github.com/bobs-org/bob-mac-capture/blob/9714a56d0d64aa3be2b2bcaf89977a349062604c/docs/keyboard.md

## Recommended solution

Build a small, staged resolution extension to the existing successor card: **Complete task** and **Cancel task** on the focused row, optionally using **Ctrl+X** and **Ctrl+Shift+X** when the list owns focus. Keep marks dedicated to pulling work in, provide pending badges and local undo, and use one explicit **Apply changes** action with no implicit highlighted-row pull-in once resolutions are staged.

Use single-task scope, preserve normal recovery and ledger effects, keep cancellation recovery-only, and show completion-generated offers in the same card without preselection. Mac submits one bob-owned capture batch; Obsidian uses editor-aware guarded writers and reports partial outcomes honestly. Preserve each client's current Escape boundary. This delivers the useful decision when the user can make it, while keeping the interface calm and the write semantics reviewable.
