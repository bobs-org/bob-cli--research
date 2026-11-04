# A submit-time parent-task chooser for `^^`

Independent research by **cdx**, 2026-11-04. Scope: design and implementation advice, not a product implementation. No other research.37 report, transcript, or findings were consulted.

## Judgment

**Build it, as an explicit request for help choosing moves—not as another kind of move.** `^^` is a useful bridge between writing a project outcome and remembering which existing tasks belong in it. The direct `^id` / `:id` syntax remains best when the user knows the tasks; the chooser is better for recognizing several tasks in their original context.

The feature needs more care than “reuse the successor dialog with a third checkbox state.” Moving changes residence and repairs links; linking changes today's plan and can change task status or prerequisites. These are stronger effects than highlighting a candidate. My recommendation is a compact in-panel **Bring tasks into this project** card with a mutually exclusive action per task: **Leave**, **Move `^`**, **Move & link `:`**. Everything starts at Leave. The first Submit opens the card; the final confirmation commits the whole capture together.

The main implementation decision is to resolve the chooser in bob-cli, lower the answers into the same planned move operations as explicit bullets, and retain the existing transaction engine. Do not implement expansion, task eligibility, or writes in Swift.

## Evidence and limits

I inspected the audited `bob-cli-gl` bead and its accepted plan, the current capture/move implementation and conformance documentation, and Bob Mac Capture's actual successor state and submission code. I also checked primary accessibility guidance for the proposed control. The linked repositories were opened through `sase repo open`; the plan was read through `sase artifact read`.

Reviewed checkout identities:

| Repository | Commit |
| --- | --- |
| bob-cli | `b9fe9d0c1208ca4a4670c6e886060621116b6286` |
| bob-mac-capture | `2940666a76e65545bb3416bced36dd4f1f5c9b67` |
| bob-plugins | `f392c88f9acd919da15c2e6de8e269e3d9a44588` — opened for context; recommendation does not require plugin edits |

The local installed `bob 0.4.0` was available, but no checkout-built `target/debug/bob` was present. A read-only `capture-parse -f json` probe classified `Finish @cash^x@\n- ^^` as `project_note`, with the literal `^^` in `sub_bullets`, no needs, and no diagnostics. Its lone-`^` behavior predates the new move picker, so this is **compatibility evidence about the installed binary**, not an execution test of current master. Source inspection independently confirms that today's move lexer does not claim `^^`. I did not run the full test suite, compile Swift, mutate the vault, or measure UI latency. Performance targets and usability recommendations below are proposed acceptance criteria, not measured outcomes.

Important primary references:

- **[S1] Accepted scope:** `bead:bob-cli-gl`, closed with seven phases and land verification; `plan:202611/capture_move_bullets.md`, read through the audited artifact command. The bead records moves, ID-less picker support, draft-order placement, and destination-before-source writes.
- **[S2] Current contract:** [capture: Moving parent tasks in](https://github.com/bobs-org/bob-cli/blob/b9fe9d0c1208ca4a4670c6e886060621116b6286/docs/capture.md#L5425) and the adjacent “Offer a new project's tasks” section. Includes MV1–MV17 and MC1–MC5.
- **[S3] Grammar authority:** [move_bullet.rs](https://github.com/bobs-org/bob-cli/blob/b9fe9d0c1208ca4a4670c6e886060621116b6286/src/native/capture_language/move_bullet.rs), especially `scan_move_bullet`, and [grammar revision](https://github.com/bobs-org/bob-cli/blob/b9fe9d0c1208ca4a4670c6e886060621116b6286/src/native/capture_language/mod.rs#L45).
- **[S4] Candidate authority:** [capture_complete/candidates.rs](https://github.com/bobs-org/bob-cli/blob/b9fe9d0c1208ca4a4670c6e886060621116b6286/src/native/capture_complete/candidates.rs#L191), `project_task_move_candidates`; [task_move/plan.rs](https://github.com/bobs-org/bob-cli/blob/b9fe9d0c1208ca4a4670c6e886060621116b6286/src/native/task_move/plan.rs#L247), `movable_roots` and `resolve_movable`.
- **[S5] Planning and writes:** [capture/project_note.rs](https://github.com/bobs-org/bob-cli/blob/b9fe9d0c1208ca4a4670c6e886060621116b6286/src/native/capture/project_note.rs), [batch_move.rs](https://github.com/bobs-org/bob-cli/blob/b9fe9d0c1208ca4a4670c6e886060621116b6286/src/native/capture/batch_move.rs), [commit.rs](https://github.com/bobs-org/bob-cli/blob/b9fe9d0c1208ca4a4670c6e886060621116b6286/src/native/capture/commit.rs), and [pull_in.rs](https://github.com/bobs-org/bob-cli/blob/b9fe9d0c1208ca4a4670c6e886060621116b6286/src/native/capture/pull_in.rs).
- **[S6] Existing Mac choice behavior:** [CapturePullInChoice.swift](https://github.com/bobs-org/bob-mac-capture/blob/2940666a76e65545bb3416bced36dd4f1f5c9b67/Sources/BobMacCapture/CapturePullInChoice.swift#L511), [CapturePanelModel.swift](https://github.com/bobs-org/bob-mac-capture/blob/2940666a76e65545bb3416bced36dd4f1f5c9b67/Sources/BobMacCapture/CapturePanelModel.swift#L3173), and [CaptureKeyCommandRouter.swift](https://github.com/bobs-org/bob-mac-capture/blob/2940666a76e65545bb3416bced36dd4f1f5c9b67/Sources/BobMacCapture/CaptureKeyCommandRouter.swift#L437).
- **[S7] Identity and ID assignment:** [note_tasks.rs](https://github.com/bobs-org/bob-cli/blob/b9fe9d0c1208ca4a4670c6e886060621116b6286/src/native/note_tasks.rs#L437) and [capture_task_id.rs](https://github.com/bobs-org/bob-cli/blob/b9fe9d0c1208ca4a4670c6e886060621116b6286/src/native/capture_task_id.rs#L70).
- **[S8] Audited decisions:** `decisions:mac-capture-is-a-thin-client`, `decisions:unblocked-tasks-are-offered`, `decisions:capture-bullets-mirror-the-task-block`, and `decisions:capture-link-drops-blocking-deps`.
- **[S9] Control semantics:** [W3C checkbox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/) and [W3C radio-group pattern](https://www.w3.org/WAI/ARIA/apg/patterns/radio/).

## What the existing system already provides

### This moves task blocks, not merely their links

The shipped syntax is restricted to first-level bullets in sealed project-note items:

```text
Finish the exit packet @cash^goog-exit@#admin
- Draft the resignation memo :draft-memo
- ^equity-docs
- :call-ms
- Book the lawyer
```

`^equity-docs` moves that task's entire block from `cash.md` into the new project's task section at that bullet's position. `:call-ms` additionally invokes the existing-task linking behavior. Moved IDs and children survive; inbound links and relevant dependency references are repaired; moved roots receive freshness stamps. An existing live link follows a move, and the link path avoids creating a duplicate. [S1–S2, S5]

The parent may be an area or project. Eligible sources are open top-level task roots in that immediate note, excluding the project lifecycle task and other ineligible roots. This is not an ancestor search and not a recursive pull from descendant project notes. ID-less and hidden tasks are part of the existing picker design. Some candidates are displayed disabled with reasons rather than silently omitted. [S2, S4]

### Move and link are distinct actions

Three details should influence every label and preview:

1. **`^` does not mean “not Today.”** A moved task already linked under WORK retains that link after path repair. Moving is also an explicit freshness event. Calling this action “Later” would be incorrect.
2. **`:` is more than adding a link.** The current capture policy may remove a task's own open prerequisites when its blocking reasons meet the dependency-drop gates, then perform the link gesture. Scheduling and project blocking can also affect the outcome. A row must explain this before confirmation. [S2 MV16, S8]
3. **The parent's `:` is another choice dimension.** `@cash:goog-exit@` offers the new project's tasks through the successor protocol. Eligible moved `^id` rows join those offers; `:id` rows and already-planned moves do not. Naively adding a move chooser before the existing successor chooser would ask twice about the same tasks. [S5, `frozen_offers` and `moved_eligible_indices`]

### Reuse the successor card's strengths, not all its behavior

The current Mac successor card has grouped rows, filtering, status/destination context, keyboard movement, accessibility announcements, a draft snapshot, process identity, generation checks, and a preserved priority-roll seed. Esc returns to the editor; explicit “none” is separate from cancellation. These are strong foundations. [S6]

However, `CapturePullInChoiceState.effectiveSelectionKeys` returns the highlighted row when there are no valid marks. `openPullInChoice` initially highlights the first offer. Thus **nothing marked does not mean nothing will be applied on Return**. This is an intentional shortcut in the existing implementation, but it must not become the new chooser's default. The user explicitly requested not selected by default, and moving a task is too consequential to infer from focus. This observation is not a request to redesign all existing successor interactions.

Also, `capture-task-id` is a real vault write. Reusing the inline ID prompt by calling that command during the submit-time chooser would leave edits behind after Cancel. The presentation can be reused; the write boundary must change. [S7]

## Proposed language contract

```text
Finish the exit packet @cash^goog-exit@
- Draft the resignation memo
- ^^
- Book the lawyer
```

The marker means: **At this slot, ask which existing tasks to move from `cash.md`.** It does not mean move all, move the current task, search all parents, or link everything.

| Shape | Proposed meaning |
| --- | --- |
| First-level bullet whose trimmed raw body is exactly `^^`, inside either sealed project-note form | Deferred parent-task choice |
| First-level `- ^^` plus surrounding whitespace | Same choice |
| `* ^^` or `+ ^^` in the same position | Same, matching supported bullet markers |
| Escaped `\^^` or inline-code `^^` | Literal text, following protected-markup precedence |
| `^^` embedded in ordinary prose, or outside this scoped position | Existing behavior; no new global operator |
| Checkbox-prefixed `- [ ] ^^` | Teaching error in a sealed project item; a chooser has no authored checkbox |
| Children beneath a recognized chooser bullet | Teaching error; selected tasks already carry their own blocks |
| Two chooser bullets in the same item | Teaching error naming the first marker |
| One chooser in each of several items | Supported, processed in draft order |

Claim the raw marker before trailing-ID or item-wide modifier processing. Do not strip arbitrary suffixes and then accidentally recognize a marker. Exact-match semantics mean `- ^^ commentary` does not trigger this feature; document that the marker must be alone. Bare `^^` outside the scoped construct must retain its current meaning, including any unrelated Obsidian keymap behavior.

One marker per item is a deliberate v1 restriction. Two identical markers have the same source but different insertion positions and unclear ownership of tasks. Explicit `^id` bullets already provide precise multi-slot placement. Supporting multiple capture items is more useful and avoids an unnecessary global limitation.

The selected rows replace the marker's slot in **parent document order**, regardless of search ranking, clicking order, or action choice. Leave expands to no bullet; Move expands semantically to `^id`; Move & link expands to `:id`. Authored bullets before and after the marker retain their positions. Existing direct move bullets remain valid alongside it; their tasks are unavailable for duplicate selection.

Defer checks that depend on the answers. In particular, a caret-sealed item with `#admin` and only `^^` may acquire a valid colon move, so do not reject its name as unused before the chooser. After expansion, apply the ordinary name rule: if the final draft has no operation that uses `#admin`, explain that the user must remove the name or select an appropriate link action. Never silently discard it. If zero moves leave the project without authored tasks, use the existing empty-project/placeholder behavior; the marker itself must never become a task.

“Expansion” is a backend intermediate representation, not a requirement to overwrite the editor's text. Keep the user's original draft while the card is open. Bob may return an expanded-draft view for inspection, but Swift should not concatenate syntax or manufacture identifiers. A later “Apply choices to draft” command could be useful; it is not required to ship the feature.

## The interaction

### Before Submit

Typing `^^` should settle the lone-`^` inline completion and leave the editor usable. It should not immediately open a modal. The parse result identifies a valid item with a **pending choice**, not an unfinished ID selector that disables Submit.

The preview shows a quiet placeholder at the insertion slot:

> Choose tasks from Cash after Submit · 12 available

The available count comes from Bob. A missing source or invalid project seal is an error, not zero available tasks. While this choice is unresolved, the preview must not claim that it has shown the final project contents or all downstream effects. Existing `^id` / `:id` previews remain concrete.

### On Submit

Use the existing capture panel, preserving the editor's place behind the card. The header names both endpoints. The action verb is **Move**, not generic “Select” or “Pull in,” because “pull in” already means linking to today's plan elsewhere.

Illustrative state after two explicit choices; all rows initially use Leave:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ Bring tasks into Exit packet                                               │
│ From Cash  →  cash_goog_exit.md                                             │
│ Existing task blocks and their links move together.                         │
│                                                                            │
│ ⌕ Filter tasks…                                              12 available  │
│                                                                            │
│ Equity                                                                     │
│   Collect equity documents           [ Leave | Move ^ ● | Move & link : ] │
│   Ready · 3 notes · ^equity-docs                                            │
│                                                                            │
│   Call Morgan Stanley                [ Leave | Move ^   | Move & link :●] │
│   Ready → Next · links under ADMIN                                         │
│                                                                            │
│   Review old statement               [ Leave●| Move ^   | Move & link : ] │
│   Already planned under WORK · its WORK link follows if moved               │
│                                                                            │
│ 2 tasks will move · 1 new link under ADMIN                                  │
│ Back                 Continue without moves                Create project │
└────────────────────────────────────────────────────────────────────────────┘
```

This is a layout sketch, not a recommendation to reproduce the ASCII density. In the native panel, use consistent spacing, restrained separators, readable titles, aligned controls, and a quieter second line. The semantic hierarchy is project → task title → action → consequences. Keep the footer fixed while the list scrolls. Do not put a modal over another modal or animate rows into a new sort order after selection.

On narrower panels, put the action control on the second line for every row rather than shrinking titles or exposing only mysterious glyphs. Use a subtle move accent and a distinct link accent, with selected text and shape as well as color. Long task text should wrap enough to distinguish similar tasks; an expanded detail region can show more. Preserve section headings from the source note. Show `#hide` as muted metadata, not an invisible eligibility filter.

### Why three choices, not a mixed checkbox

Leave, Move, and Move & link are mutually exclusive actions. A checkbox's mixed state normally communicates a partially checked collection, not a different operation on the same object. A radio group expresses exclusive alternatives directly. This supports a native segmented/radio-style control with real accessible labels, not unchecked → checked → mixed cycling. The W3C patterns are evidence for these semantics, not a mandate to implement web ARIA in Swift. [Checkbox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/), [radio-group pattern](https://www.w3.org/WAI/ARIA/apg/patterns/radio/).

The state model should be an enum keyed by task identity, not two booleans whose combinations can mean “link without moving.” All rows start at Leave. Focusing, filtering, hovering, or pressing Return must never select a task implicitly.

### Keyboard and accessibility

Use the successor card's familiar Up/Down and Ctrl+N/P row navigation. On the task-list navigation surface, direct shortcuts `0`, `1`, `2` set Leave, Move, Move & link. Display these in the footer when that surface is focused. They set a state idempotently; holding a key cannot cycle into a stronger action. If `^` and `:` aliases are added, they are conveniences, not the only keyboard route, since keyboard layouts differ.

A native per-row control must retain its expected focus/activation behavior when directly focused; do not intercept its arrow keys as row movement. The filter remains an ordinary text field: digits, caret, colon, spaces, selection shortcuts, and input-method composition work normally there. Escape returns to the original draft and writes nothing. Return activates the visible primary action using only explicit choices. With zero choices, the primary action says **Continue without moves**; do not silently pick the first row or require an awkward alternate shortcut for zero.

Avoid a global Select all in v1. Source notes can be large, hidden, or heterogeneous. If bulk actions are later needed, make them explicit commands such as “Move visible tasks,” include the count, and never let filtering silently clear choices. Show “3 chosen outside this filter” when relevant.

VoiceOver should announce task title, chosen action, status, destination, and any reason an action is unavailable. Announce changed counts and errors without narrating every repaint. Disabled actions keep their explanation reachable. Tests must cover keyboard-only use, VoiceOver, light/dark appearance, long labels, and increased text sizes; visual polish is incomplete without those paths.

### Consequences must come from the final planner

Reuse the visual row ingredients from existing pickers, but do not assume `project_move_consequence` is sufficiently precise: its current string builder chooses largely from sigil, status, name, and existing link. It is not a complete simulation of dependency drops, inherited blocking, or the final combined batch. [S4]

Examples of truthful row details:

| Situation | Detail |
| --- | --- |
| Ordinary Move | `Moves to Exit packet · status stays Ready` |
| Move already linked under WORK | `Moves to Exit packet · keeps its WORK link` |
| Ordinary Move & link | `Moves to Exit packet · Ready → Next · links under ADMIN` |
| Link drops own prerequisites | `Removes 2 prerequisite links · Next · links under ADMIN`, with expandable task names |
| ID-less selected task | `Adds ^collect-equity-documents when saved` |
| Task cannot enter a future project | `Project starts Friday; this Ready task cannot move yet` |
| Task can move but cannot link because of project blocking | Move stays available; link action disabled with the precise reason |

Disabling an impossible link action is an intentional chooser restriction, not a change to handwritten `:id` behavior. The existing direct syntax can sometimes move a task while reporting that its link is held. The chooser should make the achievable operation clear and offer Move instead of promising an unavailable link. Final validation remains authoritative even for enabled actions.

Do not call the footer's total “2 new tasks”: these are existing tasks. Distinguish tasks moved, **new** links, and preserved links. The plan-budget delta counts actual new links, not the number of colon choices. Preserve the current nonblocking budget warning behavior.

## Coexisting with the successor prompt

A two-stage workflow is acceptable when it answers two genuinely different questions; asking twice about the same task is not.

For `@cash^exit@`, choose parent moves and finish, unless other items in the draft independently need a choice. For `@cash:exit@`, resolve parent moves first, then run the ordinary successor planning for the expanded draft. The second stage should contain only still-undecided tasks, such as newly authored project tasks or unrelated completion successors.

A chosen Move means do not add a new link through the later successor choice; a chosen Move & link already requests its link. **Both rows are resolved for the interaction.** Preserve their provenance so the client can suppress them from the remaining-choice list or show them in a collapsed “Already decided” summary. Do not remove them from the underlying canonical offer model merely to simplify the UI.

This can retain literal semantics: an expanded `^id` under a colon seal still has its ordinary offer, but the final explicit successor key set omits it. An expanded `:id` already links through the move path. Equivalent manual input is therefore the explicit bullets **plus the explicit successor selection**, not bullets alone. Do not send `--pull-in all` to implement this combined UI: that could upgrade a prior Move choice. Conflicting programmatic answers should be diagnosed or explicitly revised, never silently overridden.

If no undecided offers remain, skip the second screen and submit an explicit none choice as necessary. If more remain, the first primary action is **Continue**, with a concise “Next: choose tasks for today's plan” cue. Back preserves choices and does not write. Keep one in-panel flow, not a stack of dialogs.

For multiple project items, process source-dependent groups in draft order. Independent groups can share the card, clearly labeled by destination. If an earlier choice changes the staged parent of a later group, invalidate and rebuild that later group's choices. Correct staged semantics are more valuable than forcing every possible group into a single initial response.

## Backend design

### A typed pending choice, then ordinary move planning

Add an explicit chooser node beside concrete move bullets, with its capture item identity and source range. Do not represent it as a malformed block ID or a special task title. Both execution and editor parsing must use the same recognition helper.

A read-only preflight runs the capture planner up to actionable choices. Candidate construction reads the **staged source note** at that point, not only the disk file. This matters because an earlier capture item can create or modify the parent of a later item. The existing completion entry point reads its target directly from disk; extract reusable candidate/eligibility logic instead of repeatedly calling that public command from Swift. [S4–S5]

The answer has three-state intent per candidate, but can serialize only the two selected actions; an explicit empty array acknowledges choosing none. Sketch, with protocol spelling illustrative:

```json
{
  "version": 1,
  "draft_digest": "…",
  "groups": [{
    "key": "opaque marker identity from Bob",
    "snapshot": "opaque source-and-context revision",
    "picks": [
      {"task_key": "opaque source identity", "action": "move"},
      {"task_key": "another identity", "action": "move_and_link"}
    ]
  }]
}
```

A missing group answer is different from `picks: []`. Unknown groups, duplicate task picks, unknown actions, stale identities, and choices incompatible with another explicit move fail before writing. The backend returns source/destination labels, display metadata, action availability and reasons, preview consequences, and provenance linking expanded moves to the chooser.

Keep this a separate typed selection from successor `--pull-in`. A boolean successor pick cannot represent a move-only action and source/slot ownership. An internal structured argument such as `--project-move-choices` could fit the existing subprocess interface; final naming should follow the CLI rules. Do not add a subcommand beneath `bob capture`, whose positional text grammar makes that inappropriate. Existing explicit bullets remain the simple public scripting route.

### ID-less tasks are a first-class path

The picker should include them from the start. Requiring the user to assign IDs beforehand would exclude precisely the loose tasks they are trying to organize.

At confirmation, validate the selected source root against its preflight snapshot, allocate its ID using Bob's existing suggestion/uniqueness helpers, stage that assignment in memory, and run the normal move plan. The source note, destination, repaired links, and any ID assignment join one commit attempt. Merely opening or canceling the chooser never calls the writing `capture-task-id` command.

Use the current `^id` identity where present, plus an opaque source fingerprint. For ID-less tasks, include a stable presentation key and a source-bound locator. The existing text digest/duplicate ordinal key is useful for rendering but **is not sufficient proof of unchanged intent**: identical task titles can be reordered or their child blocks edited. Bind answers to a source revision and the complete block, not just visible text or a line number. A conservative whole-source snapshot check is a reasonable first implementation; unrelated concurrent edits may require refresh, which is safer than moving an unintended block.

ID allocation must consider existing destination anchors, authored tasks, all imported descendants, and other selected ID-less roots. Preserve the current refusal policy for collisions rather than renaming existing IDs silently. On an unselected task, mint nothing and stamp nothing.

### Revalidation and failure behavior

At final confirmation, reconstruct the whole plan against current snapshots and validate the draft digest, source identities, permissions, eligibility, schedules, destinations, reference repairs, and all dependent choices. A changed preview must return to review rather than silently accepting stronger consequences. The same ID with changed title, children, prerequisites, or planned placement may represent changed user intent.

Reuse `apply_batch_move`, snapshot postimages, freshness helpers, link handling, and the capture transaction writer. Preserve destination-before-source replacement order and the current preimage checks. These supply error rollback and a no-source-first-loss ordering; they are **not a promise of database-style all-file crash atomicity**. A hard interruption can leave duplicates, as the original epic explicitly acknowledges. Do not claim this feature introduces a stronger crash guarantee. [S1, S5]

Double Submit and key repeat need an in-flight guard and request identity. If the child process outcome is uncertain, retain the draft and report uncertainty; do not blindly retry a potentially completed capture. The existing “destination already exists” refusal helps, but does not replace deliberate handling of uncertain completion.

If selection becomes stale, show which choice needs review, refresh the rows, preserve only choices that can be safely revalidated, and require another explicit confirmation. Never drop a rejected choice and commit the remainder unnoticed.

### CLI behavior

`bob capture` remains noninteractive. A write-capable invocation containing unresolved `^^` should return a structured `project_move_choice_required` response and write nothing, **even without an optional require-choice flag**. Otherwise an older client that does not know the feature could unknowingly create the project while dropping the requested interaction.

A dry run should return a usable pending-choice object and partial preview without side effects. It must not falsely mark that preview as final. An explicit empty answer removes the marker and continues normal planning. If no tasks are available, show a short empty state with Continue without moves and Back; an invalid or unreadable source is an error, not an empty state.

Before final choices, deterministic seeds and the unchanged draft keep repeated previews stable. A selected dry run and the actual commit should agree on the expanded operations and outputs except for existing dry-run distinctions. A final capture should report the same `moved_tasks`, repairs, status, freshness, and link effects that the equivalent direct moves produce, plus additive chooser provenance if needed.

## Compatibility and scope

This consumes text previously treated as prose in a narrow position, so it is a capture grammar change. The reviewed source reports grammar **10**, while the move-bullet documentation still mentions **9**; implementation must bump from the actual current constant, not copy an old number. Mark the grammar change as breaking under the release rules. No manual Cargo version or changelog edits.

The current Mac `CaptureGrammarGate.minimumRevision` is 5 and only checks a lower bound. A named capability helps new clients identify this feature, but **capability absence alone cannot stop an old Bob from saving literal `^^`**, as the installed-binary probe demonstrates. The reliable thin-client rollout is:

1. Bob ships parsing, pending-choice reporting, structured answers, and unconditional no-write refusal for unresolved markers.
2. Mac ships the card and requires a Bob grammar revision that includes the feature before allowing captures. This is an explicit minimum-version increase for the new app.
3. Old app + new Bob fails safely on unresolved `^^`; new app + old Bob asks for an update before capture. Never silently degrade to a literal task or ignore the marker.

A more permissive feature-specific gate would need semantic support from the old backend or a deliberately approved client-side detector. I would not add a second grammar implementation just to avoid the minimum-version increase. Test all four old/new combinations, not just the happy pair.

No bob-plugins changes are inherently required: the requested interaction is capture's, and the Mac already owns the submit-time UI. Do not couple this delivery to rewriting the Obsidian successor API or changing its existing `^^` gesture. Use the successor card as presentation inspiration and reuse appropriate primitives, rather than expanding one boolean model to govern every future choice.

## Requirements I would adjust explicitly

| Original or implicit requirement | Recommended adjustment and reason |
| --- | --- |
| Prompt “after they submit” | After the first Submit, **before any vault writes**. Final confirmation commits one whole capture. Post-commit selection would break cancellation and atomic planning. |
| Select “one or more” | Allow **zero or more**. Zero is an explicit, useful answer; Escape means return to draft, not choose zero and commit. |
| Parent project | Use the **immediate declared parent note**, including existing supported area parents. Do not recurse through project descendants or ancestors. |
| A successor-like prompt | Reuse its layout, filtering, and orchestration, but use an exclusive action enum and no highlighted-row fallback. |
| `^^` anywhere a bullet exists | Only the raw whole first-level body in a sealed project-note item; one marker per item for v1. |
| Selected tasks become bullets | Lower to equivalent backend operations with provenance; do not require visible editor rewrites or early ID writes. |
| `:` always selectable | Expose it when its link action is meaningful; show precise disabled reasons otherwise. Handwritten `:id` retains its current semantics. |
| Exact equivalence with direct syntax | Preserve final write semantics, including explicit successor choices. The guided UI does not ask again about already-decided moved tasks. |
| Older clients may ignore additive fields | Unresolved markers must always fail closed on write; the updated Mac needs a feature-capable Bob minimum. |

These changes preserve the useful idea while removing ambiguous consent, duplicate questioning, and hidden partial writes. They do not authorize automatic selection, silent changes to task status policy, or new rules for handwritten moves.

## Alternatives and critique

| Approach | Strength | Problem / decision |
| --- | --- | --- |
| Existing inline `^`/`:` picker with Shift-Return chaining | Already shipped; no new protocol; best for one or two known tasks | Less convenient when composing first and choosing a mixed batch later. Keep it as a complementary workflow. |
| Upgrade the inline picker to a batch chooser, without `^^` | Could deliver much of the benefit with fewer language forms | Changes an established completion interaction and interrupts drafting. Consider a future shared chooser entry point; the explicit deferred marker is still useful. |
| Post-save move dialog | Superficially simple: project already exists | Failed or canceled moves leave a partial capture; undo and stale state become harder. Reject. |
| Automatically choose all parent tasks | Fast when every task belongs | Surprising relocation, hidden tasks, and plan inflation. Reject. |
| A cycling three-state checkbox | Compact | Mixed-state meaning is misleading; accidental extra presses select stronger actions; discoverability suffers. Reject. |
| Two independent “Move” and “Link” checkboxes | Familiar individual controls | Creates an invalid link-without-move state and requires coupled toggling. Less clear than one action enum. |
| Default all selected tasks to `:` | Fewer decisions | Conflates project organization with daily commitment. Reject. |
| Client-generated `^id` text plus early ID commands | Reuses current CLI with little Rust work | Splits authority, loses source-snapshot binding, and writes before cancellation is resolved. Reject for the robust version. |
| Generic choice framework across all capture operations | Future flexibility | Too much abstraction before this two-action use case is proven. Extract a small submission coordinator and common view primitives only where needed. |

The idea is good, but it adds another symbol to an already rich capture language. Make the preview teach its meaning, and keep it opt-in: no marker means no new parent-task prompt. Avoid expanding this change into cross-note search, recursive project collection, drag ordering, arbitrary destinations, or `::` / `^^query` variants. Those would weaken the meaning of “these tasks, from this parent, at this slot.”

The main product risk is ceremony: two prompts after a quick capture can feel like an unexpected wizard. The remedy is to ask only for unresolved choices, skip empty stages, label the next action accurately, and leave direct bullets fast. The main engineering risk is treating preflight output as a command that remains valid indefinitely. Snapshot binding and complete revalidation are release requirements.

## Implementation priorities and proof of completion

First define grammar, response shapes, state transitions, and conformance examples across both repositories. Then implement Bob's pending-choice resolution and atomic ID-less selection using the existing move engine. Finally add the Mac presentation and submission coordination against generated real-Bob fixtures. Do not start with a beautiful card backed by a fake or lossy expansion path.

The essential acceptance matrix is:

| Area | Required cases |
| --- | --- |
| Recognition | Both seals; `-`/`*`/`+`; whitespace; escaped and protected forms; nonproject and nested contexts; raw `^^` with suffix text; checkbox/children refusal; duplicate marker refusal; parser/executor agreement |
| Defaults | First row focused, Return pressed, zero task actions: no task moves; changing filter or focus never changes action; empty project uses existing placeholder behavior |
| Equivalence | Compare selected `^^` output and final vault bytes to explicit move bullets plus the same successor selection; cover both seals, mixed actions, explicit bullets, and inherited links |
| Placement | Tasks land at the marker in original source order, between authored neighbors; filtered selection order cannot reorder them |
| Identity | ID-less rows; duplicate titles; preexisting IDs; ID collisions with authored/moved descendants; no mutation during preview or cancellation |
| Staleness | Source moves/deletes/reorders; changed title or child block; changed dependencies or status; destination created; day link changes; draft/process changes |
| Planning | Dependency drop shown before confirmation; existing link retained; hidden row; future project; inherited block; deferred unused-`#name` check; actual new-link count and budget |
| Batch | Same task selected twice; direct move overlap; multiple independent projects; later source created or changed by an earlier item; later failure rolls back all writes |
| Transaction | Existing preimage rejection and injected rename failure; preserve destination-before-source ordering; duplicate Submit; unknown completion outcome |
| Successor coexistence | Move-only row never implicitly upgraded; moved rows not asked twice; new authored tasks still offered; explicit none; Back retains answers; unrelated successor groups remain intact |
| Compatibility | New/new works; old app/new Bob refuses safely; new app/old Bob blocks with upgrade guidance; old/old unchanged |
| UI | Empty/error/refresh states; long titles; large sources; filtered-out selections; disabled reason accessibility; keyboard and VoiceOver; light/dark and larger text |

Keep the existing MV/MC tests as regression evidence and add interaction tests that assert outcomes, not implementation details. Share real-Bob JSON fixtures with the Mac tests. A Rust pass alone cannot establish that the app target compiles or that the keyboard card works: follow bob-mac-capture's compilation and CI requirements, including an actual macOS app build and tests as appropriate.

For perceived responsiveness, measure time to the first useful card and selection-to-preview latency on the Mac with small and large source notes. A sensible initial target is an immediately visible loading shell and ordinary candidate presentation within a few hundred milliseconds; treat this as a target to validate, not a promised number. Full link-repair scans can cost more than source enumeration. Cache only by the relevant snapshot/draft identity, cancel obsolete preview work, and never perform the expensive vault scan for every navigation keystroke. Do not truncate the selectable task set to meet a timing target.

Before shipping, walk through three short usability tasks: move three tasks without linking any; mix two moves and one link; cancel after selecting an ID-less task. The user should predict the resulting residence and today's links from the card alone. This is a more meaningful beauty/reliability check than whether the screen resembles the successor prompt.

## Recommended solution

**Add `^^` as one explicit, deferred parent-task chooser slot per sealed project-note item.** Show it after Submit and before writes. Use a polished in-panel action list with **Leave / Move `^` / Move & link `:`**, default every row to Leave, separate focus from consent, and explain real planning effects. Expand selected tasks in source order through bob-cli's existing move machinery, including staged ID assignment and source-snapshot validation. Preserve direct syntax and task policy; pass explicit successor selections so already-decided moves are not asked about or upgraded again. Commit the entire capture only after all choices are resolved.

This is worth implementing because it makes project creation a deliberate act of organizing existing work. Its quality will come from clear consequences and reliable cancellation as much as from appearance. Ship the narrow version with atomic planning and compatibility gates; retain the inline picker for fast known-task entry and postpone generalized bulk-move features until this interaction proves useful.
