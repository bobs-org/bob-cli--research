**Research: choosing successor tasks after completion — independent cdx report**

Research date: 2026-10-13. Researcher: cdx. Scope: bob-cli, Bob Obsidian plugins, and Bob Mac Capture. This report was developed independently; no reports, conversations, or findings from the other four swarm researchers were consulted. No product code or live vault notes were changed.

The inspected revisions are bob-cli `c32143ea398ac3012ae5bce9609f256958aee632`, bob-plugins `4f0cc94231556c5058030187da02b827a9ba8b93`, and bob-mac-capture `eed300d33e5296336f5b24fb56a762f283aa9048`. Repository citations below identify those snapshots. The runtime probes used the installed `/home/bryan/.cargo/bin/bob`; its build provenance was not established, so those probes corroborate the inspected source rather than certify that the binary matches that revision.

**The proposed change is a good idea, with one important separation: becoming available should remain automatic; deciding to work on it today should become explicit.** A dependency edge explains what can happen next, but says nothing about whether Bryan wants to spend this Pomodoro on it. Automatically linking every eligible dependent also promotes Ready tasks into the sticky Next lane. An optional selection step gives control over both today's agenda and the resulting lane growth.

I recommend completing the requested task or capture draft first, including dependency recovery and empty-project surfacing, then opening one searchable chooser with zero tasks selected. Selecting successors becomes a separate, revalidated write. A single panel should combine direct dependents, available tasks in newly unblocked projects, and empty project/parent-project completion tasks. The panel needs a clear **Skip** action; Escape must leave the completed task completed. Bob Mac Capture needs native selection presentation and orchestration, but should consume the same semantic contract as bob rather than implement successor discovery in Swift.

The main risk is turning every completion into an interruption. Open the chooser only when there is something actionable, combine all candidates from one gesture or aggregate draft, and make skipping fast. Keep reconciliation and background automation quiet. Those constraints make this a pull-based agenda decision rather than a compulsory second completion ritual.

**The reported project behavior is intentional in the present contract.** The Rust successor planner classifies a nonempty project's `^prj` as recovery-only, with `not_linked: project_task`. Its project recovery pass then classifies available resident tasks as `project_member`, explicitly with no successor anchor. The JS planner has matching branches. The published PDC2 vector even says that residents recover without successor links; PDC3 preserves residents' own remaining blockers. This explains the shape of the `sase.md` / `sase_foo.md` observation without requiring a malfunction. I did not inspect Bryan's live notes, so I cannot rule out additional state in that particular example. [B1] [B2] [B3] [P1]

The five-successor rule also differs from an ordinary cap: **more than five eligible direct successors links none of them**, rather than choosing the first five. Empty-project pull-ins are exempt and can still link. The limit exists independently in Rust and JS and must be removed from both. Removing it only from the UI or increasing it would leave the current semantics in place. The embedded-completion safeguards of 25 levels and 250 targets concern a different operation and should remain. [B1] [B5] [P2]

I verified these distinctions in four isolated `bob capture --dry-run --no-clip -f json` fixtures, all dated 2026-10-13. Each fixture contained its own Tasks settings, notes, and daily ledger; every file remained byte-identical after the probe, and the temporary fixtures were removed.

| Probe | Result today |
| --- | --- |
| Complete `!sase:bar`; Foo's `^prj` depends on Bar and Foo contains two blocked ordinary tasks | `^prj` becomes Ready with `project_task`; both residents become Ready with `project_member`; no links |
| Complete a planned Bar with six direct dependents | All six become Ready with `breaker`; no links |
| Complete the last ordinary task in a project | The project's `^prj` is unhidden, promoted to Next, and linked with `trigger: project_empty` |
| Complete the last open child project's `^prj`, with an otherwise empty parent | The parent's `^prj` is unhidden, promoted to Next, and linked with `trigger: project_empty` |

The focused Obsidian suites also passed: **106 tests, 106 passing**, using `node --test` with `test-task-status-cycler-successors.cjs`, `test-task-status-cycler-successor-wiring.cjs`, `test-task-status-cycler-project-pull-in.cjs`, and `test-task-status-cycler-successor-polish.cjs`. Their coverage includes the recovery-only project behavior, breaker, parent-project pull-in, anchor inheritance, and reopen behavior. I did not compile bob-cli or build/run the macOS application during this research; Mac conclusions are from source inspection, and the new UX remains untested.

**Completion has two existing semantic implementations and several entry points.** Rust's `task_complete::successors::plan_successors` serves task completion and Pomodoro-close capture paths. Obsidian's cycler funnels its supported close gestures through `finalizeClosedTasks`, which currently applies successors before retiring references, then presents an informational notice. The native Mac application delegates all capture mutations to bob. The existing division can accommodate this change without a new daemon, a general workflow engine, or a Swift graph implementation. [B1] [B6] [B7] [P3] [M1]

| Completion surface | Present behavior / recommended coverage |
| --- | --- |
| Ctrl+Enter on an ordinary task, a plain Task Link, an embedded link, or fallback link branch | Use the cycler's completion finalizer; offer selection once after the complete gesture settles |
| Ctrl+Enter on a Pomodoro | Aggregate the task identities actually completed by the gesture; offer one chooser |
| PRE/POST review-walk completion through `completeTaskAtCursor` | Include it, while preserving the existing one-advance review behavior |
| Alt+] / Alt+[ cycling into Done | Include it through the same finalizer; cycling into Cancelled remains recovery-only |
| `bob capture '!note:id'` | Return an offer after successful completion; interactive terminal use may present it |
| Capture close forms that actually complete tasks, including `=x` embeds, `=x!M`, `=!`, and linked close forms | Include them; a Pomodoro closing without task completion creates no successor offer |
| Multi-item capture drafts | One final offer for the whole successful draft, evaluated against its final state |
| JSON subprocess or noninteractive CLI execution | Return candidate/context data; never wait for human input or auto-select |
| Raw checkbox clicks, manual text edits, or third-party Tasks completion commands | Currently bypass successor handling; reconcile may recover statuses, but there is no managed successor gesture |
| Reconcile/hooks, cancellation, reopening, parks, restarts, resets, and Ctrl+Enter on a Depends-On line | Preserve current non-successor behavior; do not open a chooser |

The trigger table above follows the current documented boundary. In particular, **“any supported method” does not currently include raw checkbox clicks**. A generic vault watcher would confuse a human close with sync, reconciliation, or another writer. If raw clicks must prompt too, treat that as a separate explicit requirement: route an identifiable user action through the finalizer, with deduplication against the existing gestures. Do not infer interactive intent from every change to `[x]`. [B3] [P3]

**The requirements need the following explicit adjustments and clarifications.** These are recommendations, not changes already implemented or accepted memory updates.

1. **Completion commits independently of selection.** Closing/recovery/retirement and empty-project surfacing succeed even when the user skips, closes the panel, or cannot apply successors. This clarifies the meaning of “if any.” Selection failures should say “Completed; selected tasks were not linked,” not make the capture appear to have failed.
2. **One chooser per gesture or aggregate capture, rather than one per dependent, project, or destination.** Group rows and show where each selection will go. One gesture can legitimately produce candidates for multiple projects or slots.
3. **Remove the successor count breaker without replacing it with a hidden candidate or selection cap.** A small viewport, search, and incremental rendering are fine; a truncated backend result is not. Do not remove unrelated completion-tree safeguards.
4. **“All open tasks in an unblocked project” means all recognized open residents are accounted for, but only available tasks are selectable.** A resident with its own open prerequisite, future schedule, or remaining inherited project reason stays disabled. Show these under a collapsed explanation such as “2 still blocked.” Hidden tasks should remain excluded from the main selectable set and be accounted for separately; selecting hidden work would otherwise change the meaning of `#hide`.
5. **A nonempty project's `^prj` is a group/context row, not the default successor to offer instead of its work.** Offer its available ordinary residents. Offer `^prj` as actionable project-finishing work when the same emptiness predicate used by `projects sync` says the project is empty. Empty here means the existing effective-unhidden work/sub-project predicate, not a literal absence of every Markdown checkbox.
6. **An unplanned predecessor should still yield an offer.** Today the lack of a live predecessor Task Link prevents linking. Explicit choice makes it reasonable to offer current/next as a destination even when the predecessor was not planned. This is a deliberate widening of the existing anchor rule; display the destination and require an explicit apply. An absent daily ledger or ambiguous running entry must not cause creation or arbitrary placement merely because a chooser opened.
7. **Keep immediate project expansion scoped to the project's own note initially.** The accepted subproject decision explicitly sets `close_recovers_subprojects = no`: descendants can retain inherited blocking tags until reconcile. Direct residents satisfy the reported Foo example. Immediate recursive descendant recovery would reopen that decision and add a tree write to close paths; do not silently include such tasks as available before the recovery is authoritative.
8. **Preserve recovery and lane policy for everything not selected.** Available blocked tasks recover to their derived rank, eligible Ready recoveries retain the existing `[unblocked:: today]` tickler write, and existing Next/Pending lanes remain sticky. Selection itself does not clear schedules, stamp freshness, complete project tasks, or recursively activate downstream dependents.

Items 4 and 7 narrow a literal reading of “all open tasks” for consistency with real blocking and the accepted project-tree policy. Item 6 expands today's behavior to match the user's broader completion intent. Item 8 means a post-completion-selected task can retain an `[unblocked::]` field written during the first stage; linking should not erase a valid recovery input simply to imitate the bytes of the former one-stage operation.

Audited memory reads informing those choices included the project blocking, subproject inheritance, task-lane, ledger-Today, dependency-link, thin-client, unblock-tickler, and review-walk decisions, plus CLI rules. In particular, tickler recovery previously rejected automatically linking project residents. This proposal substitutes an explicit user choice and should document that distinction. Any accepted changes to immutable decision records should be recorded as supersession through the memory-write procedure, not by editing their original claims in place.

**Discovery should describe availability and causality, not merely recycle `unblocked[]`.** The current reporting arrays summarize writes and can omit an already-Next task when no status changed. They also contain hidden/recovery-only rows and use `trigger: dependency` for project-member recovery. A selector needs its own complete candidate model with eligibility, cause, identity, and destination. [B1] [B2] [P1] [P2]

For a gesture with completed set C, evaluate the final staged dependency/project state and form the union of:

- Open ordinary dependents whose last applicable blocking reason was removed by C, including stale checkbox states; graph truth decides availability.
- Open ordinary residents of a project whose own blocking reason was removed by C, even when those residents do not name C in their own Depends-On lines. Enumerate the affected note, rather than filtering the existing reverse index to direct edges.
- Open `^prj` finishing tasks surfaced because C removed their last effective resident or last open child project, plus an empty project's `^prj` whose final prerequisite was completed.

Then deduplicate by resolved task identity, combine multiple causes, and partition by final eligibility. A task must still be recognized, open, outside terminal/archive scope, and free of applicable own/project reasons. Preserve the pre-gesture already-planned baseline as well as the current live-link check: a task explicitly dropped by the same gesture must not reappear as a successor offer. Exclude tasks subsequently completed or reblocked by another item in the same capture. Keep “already planned” informational or omit it from the actionable list.

The existing batch post-pass verifies linked successor rows and surfaced project rows, but does not revalidate every unlinked recovery row against the final draft. A new offer needs a broader final pass. Likewise, an earlier `project_empty` observation must not offer `^prj` if a later draft item adds fresh project work. This is essential to a post-completion design; collecting every per-item row and displaying them unchanged would be incorrect. [B6]

Do not infer project expansion from `^prj`'s checkbox alone. A project can have a stale Ready marker while the dependency graph changes, and a tagged descendant can still have an ancestor reason. Conversely, not every resident will carry `[?]` at discovery time. Build the project's affected resident set from its note and apply the authoritative predicate to each task.

**The chooser should make a small, concrete agenda decision.** An example for the reported case is:

```text
Choose what to work on next
Closed Bar. Foo is now available.

Search tasks…                              0 selected

Foo · project became available
  □ Write the first section       sase_foo · → FIX
  □ Check the second section      sase_foo · → FIX
  ▸ 1 task still blocked          waits on another prerequisite

Other newly available tasks
  □ Update the tracker            admin · → NEXT

                    Skip          Link selected (0)
```

All rows start unchecked, including the single-candidate case. Show task text, note/project, a short reason, and the actual destination. Preserve selection when filtering or expanding groups. Show how many selected rows are currently outside the filter, so a user cannot unknowingly submit invisible selections. Provide explicit Select visible / Clear controls; a group checkbox, if used, should express none/some/all and affect only eligible rows in its stated scope. Avoid checking every task in a project merely by selecting its heading.

Use arrows to move focus without changing selections, Space to toggle a focused row, and an explicit button or modified Return to apply. Keep Space as text input while the search field owns focus. Provide a normal focus route from search to results, Home/End for long lists, and Escape/Skip for choosing none. Suppress the opening completion keypress and repeats so the gesture that opened the chooser cannot immediately apply it. This interaction guidance follows the W3C listbox distinction between focus and selection and its modifier-free multi-selection model; the checkbox pattern supports Space and mixed group state. [U1] [U2]

Choose an accessible implementation deliberately: a real multi-select listbox can draw checkmarks but should not contain interactive buttons or nested checkbox controls inside options. If rows have real checkboxes and task-opening buttons, use labeled checkbox groups or an appropriate interactive grid instead of inheriting `role=listbox` from an existing single-row picker. This is a reason to reuse the existing picker styling and search machinery rather than blindly reuse its entire interaction implementation. [U1]

Show one contextual panel, not a succession of modal confirmations. Apple's sheet guidance cautions against stacked sheets and requires a way to dismiss without committing. A native successor state in the existing capture panel is a suitable application of that guidance; a separate operating-system window is not required. This is a design judgment rather than evidence from user testing. [U3]

Destination defaults should preserve today's placement behavior where possible: an ordinary close uses the predecessor's original slot, and a Pomodoro close uses its same-name continuation. This is more specific than “current/next”: today's implementation does not always use the implicit running entry. Display a per-row destination chip, and allow an explicit common current/next override if Bryan wants to consolidate. For an unplanned close, use the existing implicit resolver: one running timed entry, otherwise the first open entry. [B3] [B8]

If there is no usable open destination, retain the offered tasks and show an explicit choose/create-next action. Create a placeholder only as part of applying a nonempty selection. If a former source placeholder has disappeared through retirement, offer a visibly named new continuation where it can be located safely; if its position cannot be resolved, ask for a destination instead of guessing. The panel should never silently start a timer.

**A two-stage implementation has a modest but real correctness cost.** Current successors are inserted before ledger retirement so an otherwise empty future placeholder survives. Delaying selection means that placeholder can disappear, the predecessor's subtree can move, and line numbers can shift while the user chooses. Capture the source context before retirement: day identity, predecessor identity, logical entry context, continuation hint, and proposed placement. After retirement, resolve against current content. Bare saved line numbers are unsuitable write targets. [B3] [B7] [P3] [P4]

The stages should work as follows:

1. Commit the original complete gesture or aggregate draft, with normal recovery, retirement, and empty-project `#hide` removal. Candidate discovery can use the final staged state, but no candidate status promotion, block-ID mint, successor bullet, or successor-only continuation is written here.
2. Publish an additive completion offer with a context identifier, completed identities, affected projects, candidates, proposed destinations, and discovery status. An unavailable scan is distinct from an empty candidate set; report it without invalidating completion.
3. The client holds selection in memory. Skip discards it. No persistent pending-decision fields, synthetic dependencies, or new task tags are necessary.
4. On Apply, send explicit selected candidate identities plus destination choices and the completion context. Re-read current task/project/dependency/ledger state and validate the identities, source cause, and destination before preparing writes.
5. Mint missing block IDs only for selected tasks. Use the existing deterministic readable mint and unambiguous link formatting. Change Ready to Next, preserve Next/Pending, and insert one link per task. Refuse a task that is now Blocked; never satisfy the selection by linking its prerequisites instead.
6. Commit the selected set through the existing safe staging/preimage machinery. Return applied/already-linked/unavailable outcomes and updated blocks for presentation. Repeated Apply must not duplicate links or remint IDs.

A no-block-ID resident needs a candidate key that includes its note and expected task content/context, not an empty `block_id` or a line number treated as identity. If the task moved or identical text now resolves ambiguously, refresh rather than pick one. Existing block IDs plus the expected current note/task state give a much simpler path for normal candidates. A context identifier can represent data carried by the client between subprocess calls; it does not require a resident bob process or a durable workflow queue.

For the Rust apply endpoint, prefer rejecting the new selected write as a whole when a selected task or destination changed materially, then refreshing the chooser while retaining still-valid picks. Already-linked tasks can be acknowledged as satisfied. The original completion remains committed either way. Obsidian's existing note-by-note/editor mutation path can fail partially; retain accurate per-row outcomes and retry only unresolved rows rather than pretending it has the Rust writer's transaction guarantees. [B9] [P4]

Also revalidate the graph inputs used for eligibility, not just the files being written. A prerequisite can reopen in a different note after the chooser appeared. The current Rust writer's optimistic disk-preimage checks cover planned targets and explicitly do not provide full cross-process serialization. Include read dependencies in validation where practical, keep the check close to commit, and let reconcile remain the eventual authority. Do not describe this as a perfectly atomic vault transaction. [B9]

Do not implement Apply by appending ordinary `@route:id` capture commands. Ordinary linking has freshness/schedule policy that the successor writer deliberately avoids; Ensure Next also relocates existing links. Reuse the successor's lower-level task-status and placement helpers under a specialized selection apply contract. A deliberate user selection can reasonably be given future freshness semantics, but that would be a separate requirement; retaining the current successor policy is the smaller change. [B3] [B8]

**The frontend changes are different presentations of the same choice.** In Obsidian, keep the cycler as the coordinator and semantic writer, and add a versioned chooser capability using navigation's existing modal/search styling. `notice.showUnblocked` currently presents an informational card, so it is not already a selection API. Keep a minimal chooser fallback available when navigation is absent, or at least expose candidates through a command with a clear actionable notice; missing UI must never restore automatic linking. Avoid holding `referenceMutationQueue` open while waiting for the user. Finish completion/recovery/retirement, release the queue, then enqueue the selected mutation when Apply is pressed. [P3] [P4] [P5]

Review-walk completion needs explicit sequencing. The completion must remain the one answer that advances the walk exactly once, including the PRE/POST boundary rule. Let the close settle and the walk continuation finish before presenting its offer, then restore focus to that resulting landing on Skip/Apply. Selection is an agenda action, not a second review answer. In particular, `successorNoticeTarget: return` currently suppresses notices for walk callers; it must not accidentally suppress the chooser as well. Test the nav-owned `completeTaskAtCursor` path separately from ordinary Ctrl+Enter. [P3] [P6]

Bob Mac Capture definitely needs new native state and controls. Its `CapturePickerState` tracks one `selectedRowID` and a draft replacement range; accepting a row edits a draft token. Its current `completeSubmit` clears the draft, clears picker state, notifies, optionally opens the result, and always dismisses the panel. Neither an informational successor preview nor that picker can implement the new behavior unchanged. [M1] [M2] [M3]

Add a `successorOffer` state and selected-ID set, rendered in the existing capture panel using a new multiselect view. After the first capture succeeds, clear the committed draft once and show the offer instead of dismissing. Apply calls bob's selection endpoint; it must never resubmit the original draft. On Skip, or once Apply succeeds, finish the normal dismissal/open-after-capture behavior. Defer opening another app until the offer resolves so focus is not stolen. Failures and timeouts during Apply should leave the already-committed completion visible with retryable selection. Separate request generations for submit and selection prevent a late callback from clearing a newer draft or offer.

Swift may format, filter, and render the returned candidates, but must not discover project residents, resolve blocking, choose ledger placement, mint IDs, or write the vault. The project already has two semantic engines, Rust and JS; a third in Swift would be unnecessary duplication. Do not force Obsidian onto disk-only subprocess reads as part of this project, either: its warm Tasks-cache path overlays open editor buffers. Preserve that behavior and pin the Rust and JS selection rules with common fixtures. [P4] [M1]

For terminal use, human interactive capture can run a chooser after completion when it has an appropriate controlling terminal, with an explicit skip option. JSON and noninteractive execution must return immediately with the offer; selection can be applied by an explicit subsequent request. Handle piped multiline draft input carefully: neither consuming remaining stdin as answers nor waiting on a noninteractive pipe is acceptable. Prompt eligibility and any new flags need documented TTY behavior and the CLI-rule requirements for help/aliases. Do not put a new subcommand underneath `bob capture`, whose free-text argument swallows it; any protocol additions should be additive sibling endpoints. Exact names are an implementation detail to settle in the contract phase.

**Compatibility must cover semantics as well as JSON decoding.** Keep `unblocked`, `still_blocked`, and existing result fields describing actual committed changes; introduce separate offer data. Candidate links are proposals until Apply succeeds, so do not fill an existing `link` object or mark preview block lines `unblocked` as if a bullet was written. Advertise the selection capability explicitly. Old Mac clients can ignore additive fields and still complete tasks, but will not have a chooser; they should receive a clear upgrade path, while new clients paired with an old auto-linking bob need a visible capability warning. There should be no fallback that silently auto-links the whole offer. Note that `bob capture` success/failure JSON currently has no envelope `schema_version`, unlike the versioned capture helper endpoints; version the new protocol deliberately rather than assuming every endpoint uses the same envelope. [B6] [M3] [M4]

The `plan.link_unblocked` switch needs an explicit migration rule. I recommend retaining its spelling as the enable/disable control for interactive successor offers; `false` means recover and surface, but do not prompt or link successors. Explain that `true` now offers selection. An explicit standalone user link remains a separate action. Retaining a legacy automatic mode would complicate the migration and undermine the requested change.

Existing reopen receipts remember automatically inserted links and status edits, sometimes the complete prior project line. With post-completion selection, record the new operation's before-images from the post-completion state. Reopening a predecessor can invalidate eligibility and should retain today's conditional take-back behavior only for untouched successor additions; it must not blindly restore a pre-completion project line over later work. A separate Undo selected links action should remove only this selection's untouched links and restore only lane edits it owns, preserving automatic recovery/surfacing and task work done afterward. Capture currently lacks the cycler's in-memory take-back receipt, so cross-client Undo is a deliberate addition rather than an existing guarantee. [P7]

**The credible alternatives have different costs.**

| Approach | Benefit | Cost / judgment |
| --- | --- | --- |
| Always complete first, then offer a chooser | Completion is reliable; “none” is natural; fits Obsidian's existing write-before-finalizer structure | Requires preserved placement context and a second revalidated write; recommended |
| Pre-completion chooser and one combined write | One write set; easier preservation of source slots | Cancel semantics become ambiguous, closure waits on agenda choice, and Obsidian's Tasks-owned writes need restructuring; not my first choice |
| Passive notice with a “Choose” button | Lowest interruption cost | Easier to miss, particularly in Mac capture that normally dismisses; useful if the automatic chooser proves tiring |
| Automatically link a sole candidate, ask only for several | Fast common case | Violates the requested ability to choose none, and retains automatic commitment |
| Separate panel per project/destination | Each panel is simple | Serial interruptions and fragmented selection; unnecessary |
| Always put every newly available task in Next without a link | Avoids a ledger chooser | Invents lane commitments and conflicts with the accepted pull/recovery distinction |

I would start with the automatic, immediately skippable chooser only on explicit managed completion gestures with actionable candidates. If it is routinely skipped, change presentation to a persistent local “N available · Choose” affordance rather than adding default selections or suppressing small candidate sets. No telemetry system is necessary; a short manual trial can answer whether the panel helps at the moment of completion.

**The implementation should be staged around the contract and the regression cases.** First pin candidate eligibility, project scope, destination behavior, zero-selection semantics, and capability negotiation in `docs/task-dependencies.md` and `docs/capture.md`. Replace the affected SL17/PDC2/PP automatic-link expectations with explicit-offer and selected-apply fixtures in both engines, while keeping recovery, emptiness, and inherited-blocking predicates shared with their present authorities. Then refactor discovery away from mutation in Rust/JS, remove both breakers, add the selected apply path and final aggregate-offer pass, wire the Obsidian chooser/review paths, and wire Mac decoding/panel state. Validate the mixed-version combinations before switching default behavior; deployment order alone is not a compatibility contract.

Useful acceptance cases include:

| Case | Required outcome |
| --- | --- |
| One, five, six, or twenty available dependents | Every candidate is accessible; zero selected; choosing any subset links exactly that subset |
| Skip, Escape, panel close, or lost selection request | Completion/recovery stands; no successor-only placeholder, minted ID, or Next promotion |
| Bar unblocks a nonempty Foo | All ordinary open Foo residents are accounted for; available residents selectable; no replacement `^prj` link |
| Foo has a resident with its own blocker, future date, or hidden tag | It is not linked through selection; remaining reasons are explained |
| Foo already has stale Ready/Next checkboxes | Eligibility follows the final graph, not only `[?]` transitions |
| Finish the last resident or last child project | Surface the matching project/parent `^prj`; link only if selected; do not complete it automatically |
| Parent still has another open child or own blocker | Preserve the sync emptiness/blocking result; do not offer a false finishing task |
| Project unlock has inherited-blocked descendants | Preserve deferred descendant recovery in the initial scope |
| Task is both a direct dependent and a project resident | One row, combined causes, one link |
| `=x~K` explicitly drops an otherwise available task | Drop wins; selection does not offer an automatic way to undo that drop |
| Multi-item draft later completes a candidate, adds a blocker, or adds project work | Final offer removes obsolete candidates and false empty-project rows |
| Task has no block ID, duplicate text, or a colliding basename | Mint only on selected Apply; refuse ambiguous identity; format links unambiguously |
| Another client reopens the prerequisite or closes/replans the destination while selecting | Revalidate and refresh; no blocked task link or arbitrary destination |
| Apply is double-pressed or retried | No duplicated bullets, extra block IDs, or repeated completion/log writes |
| Source queued placeholder disappeared in retirement | Resolve preserved context or request a destination; never use stale line coordinates |
| Review-walk close, including PRE/POST | Advance once with its existing boundary semantics; chooser does not answer another row |
| Selection is filtered or scrolls beyond its visible rows | Selected state persists and the total is visible; backend results are not truncated |
| JSON call, pipe, background hook, old client, or missing navigation plugin | No unattended prompt or automatic linking; capability/availability outcome is explicit |

**Source coordinates for checking the conclusions.** These are source references, not other swarm research. Memory was consumed through audited `sase memory read` commands.

[B1]: https://github.com/bobs-org/bob-cli/blob/c32143ea398ac3012ae5bce9609f256958aee632/src/native/task_complete/successors.rs#L544
[B2]: https://github.com/bobs-org/bob-cli/blob/c32143ea398ac3012ae5bce9609f256958aee632/src/native/task_complete/project_close.rs#L218
[B3]: https://github.com/bobs-org/bob-cli/blob/c32143ea398ac3012ae5bce9609f256958aee632/docs/task-dependencies.md#L775
[B5]: https://github.com/bobs-org/bob-cli/blob/c32143ea398ac3012ae5bce9609f256958aee632/src/native/task_complete/tree.rs#L27
[B6]: https://github.com/bobs-org/bob-cli/blob/c32143ea398ac3012ae5bce9609f256958aee632/src/native/capture/plan.rs#L156
[B7]: https://github.com/bobs-org/bob-cli/blob/c32143ea398ac3012ae5bce9609f256958aee632/src/native/capture/task_complete.rs#L130
[B8]: https://github.com/bobs-org/bob-cli/blob/c32143ea398ac3012ae5bce9609f256958aee632/src/native/capture_task_toggle/links.rs#L191
[B9]: https://github.com/bobs-org/bob-cli/blob/c32143ea398ac3012ae5bce9609f256958aee632/src/native/capture/commit.rs#L141
[P1]: https://github.com/bobs-org/bob-plugins/blob/4f0cc94231556c5058030187da02b827a9ba8b93/plugins/task-status-cycler/src/085-successor-plan.js#L857
[P2]: https://github.com/bobs-org/bob-plugins/blob/4f0cc94231556c5058030187da02b827a9ba8b93/plugins/task-status-cycler/src/089-successor-project.js#L797
[P3]: https://github.com/bobs-org/bob-plugins/blob/4f0cc94231556c5058030187da02b827a9ba8b93/plugins/task-status-cycler/src/130-plugin-references.js#L47
[P4]: https://github.com/bobs-org/bob-plugins/blob/4f0cc94231556c5058030187da02b827a9ba8b93/plugins/task-status-cycler/src/135-plugin-successors.js#L200
[P5]: https://github.com/bobs-org/bob-plugins/blob/4f0cc94231556c5058030187da02b827a9ba8b93/plugins/bob-navigation-hotkeys/src/200-filtered-picker-modals.js#L1
[P6]: https://github.com/bobs-org/bob-plugins/blob/4f0cc94231556c5058030187da02b827a9ba8b93/plugins/bob-navigation-hotkeys/src/535-plugin-review-checklist-walk.js#L244
[P7]: https://github.com/bobs-org/bob-plugins/blob/4f0cc94231556c5058030187da02b827a9ba8b93/plugins/task-status-cycler/src/136-plugin-successor-receipt.js#L48
[M1]: https://github.com/bobs-org/bob-mac-capture/blob/eed300d33e5296336f5b24fb56a762f283aa9048/Sources/BobMacCapture/CapturePanelModel.swift#L5213
[M2]: https://github.com/bobs-org/bob-mac-capture/blob/eed300d33e5296336f5b24fb56a762f283aa9048/Sources/BobMacCapture/CapturePickerState.swift#L1
[M3]: https://github.com/bobs-org/bob-mac-capture/blob/eed300d33e5296336f5b24fb56a762f283aa9048/Sources/CaptureCore/CaptureModels.swift#L3376
[M4]: https://github.com/bobs-org/bob-mac-capture/blob/eed300d33e5296336f5b24fb56a762f283aa9048/Sources/CaptureCore/BobProcessClient.swift#L591
[U1]: https://www.w3.org/WAI/ARIA/apg/patterns/listbox/
[U2]: https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/
[U3]: https://developer.apple.com/design/human-interface-guidelines/sheets?changes=_1

**Recommended solution: replace automatic successor commitment with one optional post-completion chooser, backed by separate candidate discovery and selected-only apply operations.** Include available direct dependents, available residents of directly unblocked project notes, and surfaced empty project/parent-project finishing tasks in that one offer. Start with none selected, remove the five-successor breaker from Rust and JS, preserve all blocking/recovery rules, and revalidate before linking only the chosen tasks. Use a native multiselect state in the existing Bob Mac Capture panel, with bob retaining semantic and write authority. Preserve quiet background behavior and the initial residence-only expansion scope; treat raw checkbox prompts and immediate descendant-tree recovery as explicit additional decisions. This gives Bryan the requested control while retaining reliable completion, recoverable unselected work, and a clear boundary between “now possible” and “chosen for today.”
