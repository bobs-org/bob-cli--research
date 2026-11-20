# Jump after closing: successor navigation in Obsidian and Capture

Independent research by **cdx**, 2026-11-20. This report investigates the requested Ctrl+J interaction; it does not implement it. No other report or findings from this swarm were consulted.

**Recommendation in brief.** This is a good feature. Add one optional **Jump after** marker to the existing successor card, independent of Leave / Pull in / Done / Cancel. Ctrl+J toggles it on the highlighted task without moving focus or committing anything. On successful completion of the enclosing operation, reveal that exact task in its final note and focus the editor there. The explicit jump wins over Capture's submit-and-open behavior and Obsidian's automatic review navigation. The important work is the selection and navigation contract, not drawing another icon.

**1. Why the idea is sound—and where it could go wrong**

The request separates two decisions that currently share a surface: “What belongs in my plan?” and “What do I want to inspect next?” That distinction is useful. A successor can need prioritization or rewriting without belonging in today's Pomodoro plan. Pulling it in solely to make it reachable would give navigation an unintended planning consequence. Conversely, adding a task to the plan does not mean its wording is ready.

I would retain the requested single destination. Multiple pull-ins are useful, but opening several successor tasks would recreate the navigation noise this feature should remove. I would also retain Done and Cancel compatibility: inspecting a just-resolved task's notes or cancellation reason is legitimate. “Jump” must never mean “start,” “reopen,” “stamp fresh,” or “raise to Next.”

The main costs are one more visible state and one more contextual shortcut. Ctrl+J is not universally “jump” in this product: Capture already uses it for a bullet newline in its editor and next-row movement in ordinary pickers. It is acceptable here because the successor card is a distinct, modal decision surface, but the shortcut must be clearly advertised and tightly scoped. A hidden shortcut without a visible marker would be a poor implementation.

I would not replace this with immediate opening on Ctrl+J. Leaving the card before the parent operation finishes creates unresolved writes and makes it unclear whether edits in Obsidian affect the pending choice. Nor would I build an embedded priority/reword editor into this card. That expands a small decision surface into a second task editor. A deferred jump solves both stated use cases with less duplication.

**2. What the current code establishes**

The source audit used these revisions:

| Repository | Revision |
|---|---|
| bob-cli | `620270d116a0d0c8fb0f546959dc230eff06d488` |
| bob-plugins | `a68e29be2b0bb50aee47a19d65a3485c207b59bb` |
| bob-mac-capture | `6d54cb0f42ef19cd6679a5e493671748274f28cd` |

The following findings materially affect the design; source identifiers are expanded near the end.

- **Enter has an implicit pull-in fallback in both clients.** With no explicit marks or close verdicts, it selects the highlighted offer. The Obsidian modal implements this in both `prospectiveKeys()` and `applySelection()`. The Mac implements it in both its card state and portable outcome model. Adding only `jumpKey` would therefore make “leave this task open and jump there” accidentally pull it in. All selection, footer, button-enablement, and submission calculations must agree. [R1, R3]
- **The picker already supports independent close verdicts.** Obsidian's successors API is currently version 4. Picks and Done/Cancel verdicts exclude each other, and cancellation has an inline reason editor. Jump must be a separate field, not another member of that exclusive outcome enum. `settle()` and `normalizeSuccessorChoices()` rebuild result objects, so adding the field only to the UI would silently lose it. [R1, R2]
- **Capture remembers submit-and-open through intermediate choices.** `CapturePullInChoiceState.openAfterCapture` and the submit context carry the earlier modifier. The final success handler builds `CaptureOpenPlan`, optionally opens `bob-open-notes`, then dismisses the panel. An explicit jump needs to reach this final branch, including inbox-route, move-choice, stale-choice, and retry paths. [R4]
- **A useful task navigation implementation already exists.** The Mac constructs `obsidian://bob-goto-task` with a path, one-based line, optional line digest, and optional block ID. The Obsidian handler reads current content, attempts to refind the task, uses `focusTaskAnchor(... ensureEditing: true)`, and records a Vim jump context. Reuse this machinery. [R5]
- **Its current fallback is too weak for this promise.** If the digest and block lookup fail, `refindGoToTaskLine()` clamps the old line number into the note. The handler warns that it landed near the old line. That is explicitly approximate navigation, not proof that the selected successor is focused. The new feature needs an exact-target mode; do not silently inherit the fallback. [R5]
- **Preview identity is not final location.** Rust offer keys are retained across later transformations; output comments explicitly distinguish offer-time identities from the final `note_path` and settled ordinals for tasks without IDs. Done/Cancel rows have separate `offer_closes[]` receipts. A UI cannot safely derive the final target by parsing the offer key, using list position, or looking only among surviving open offers. [R6]
- **The clients do not share identical transaction boundaries.** Rust plans a capture batch and commits before reporting success. In the Obsidian completion path inspected, the predecessor has already been written Done before `finalizeClosedTasks()` runs; successor recovery/linking is best effort and later reference retirement still follows. Closing the picker is not equivalent to an atomic rollback there. [R7, R8]
- **Review continuation is another navigation owner.** Completion records an answer and calls `advanceReviewWalkAfterAnswer()`, which lands on a review row. An early jump from inside the successor picker can be overwritten afterward. [R8, R9]

These are source findings, not measurements of the live Mac or Obsidian UI.

**3. The interaction contract**

Keep three concepts separate: keyboard highlight, task disposition, and the optional jump destination.

```text
per offer:  Leave | Pull in | Done | Cancel(reason)
per card:   jumpKey: OfferKey?       // zero or one, across every group
            explicitJumpChoice: Bool
```

`jumpKey` is transient state of this enclosing gesture. It is not a task property, vault field, preference, or durable queue. No destination is marked when a new card opens. A same-gesture refresh may retain it when identity can be proven.

| Interaction | Recommended result |
|---|---|
| Ctrl+J on task A | Mark A as Jump after; keep highlight and disposition unchanged |
| Ctrl+J on A again | Clear the marker |
| Ctrl+J on B while A is marked | Transfer the marker to B; A and B retain their dispositions |
| Space/Tab or a disposition action | Change disposition as today; preserve the jump marker |
| Done/Cancel on the marked task | Keep the marker; jump to the resolved task after success |
| Filter or collapse a group | Retain the marker; show its task in the persistent summary |
| Enter with a jump and no explicit pull-ins | Finish with zero pull-ins, then jump |
| Enter with marks/verdicts and a jump | Apply those decisions, then jump |
| Capture submit-and-open plus a jump | Open only the jump target automatically |
| Actual card abandonment | Discard the jump intent; do not navigate |

For an offer that remains open, “Leave” means no additional chosen disposition. The predecessor's normal recovery can still unblock it or update its recovery metadata. Jump itself adds no mutation beyond those existing effects.

**Enter must stop implying a pull-in after the user explicitly chooses navigation.** Set `explicitJumpChoice` when Ctrl+J is first used, and suppress the highlighted-row fallback for the remainder of that card interaction—even if the jump is later cleared. Otherwise toggling the marker off can invisibly reinstate an unintended pull-in. Actual marks and verdicts continue to work. A jump-only card is committable; after clearing its jump, an ordinary close-triggered card can finish with no successor actions, equivalent to an explicit “none.” Preserve the legacy Enter fallback on untouched cards.

This is a deliberate, small change to existing behavior. It needs its own regression test and accurate footer copy. Do not solve it by silently auto-marking the jump target for pull-in.

Scope Ctrl+J to the successor card's list or filter. It should work while typing a filter, acting on the highlighted task. Consume it without action on a header, expansion control, empty result set, repeat event, or while submitting. Treat Control alone as Control: Command-J, Control-Shift-J, and other variants retain their meanings. Ignore composition events. In the inline cancellation reason field, do not repurpose the chord to toggle a different row; consume it as a no-op in this card, so it also cannot fall through to Capture's bullet-newline behavior. Leave that field through its normal confirm/back interaction first.

Preserve the existing layered Esc behavior, including q and Ctrl+[ aliases. The Mac normally backs out to the draft, while Obsidian's plain dismissal means no successor picks in an already-started close flow. An inner reason-editor back action must not erase a jump. Clearing staged verdicts in an intermediate Esc step need not erase it either. Only actual card abandonment clears it. Do not introduce a new discard-confirmation dialog solely for a navigation marker. Where Capture offers Shift-Return for explicit zero pull-ins, retain its close verdicts **and** the jump marker.

**4. A restrained visual design**

Use the existing card, spacing, type scale, group headers, selection treatment, and semantic colors. Add a compact trailing **Jump after** badge with an arrow-to-location icon. Use the same icon meaning in Obsidian and SF Symbols on the Mac; avoid emoji as the only indicator. Reserve room so toggling it does not shift task titles or Pomodoro destination labels.

A structural sketch—not a new visual theme:

```text
Successor tasks
After “Finish migration”

Hand-offs
  ○  Prioritize rollback checks       infra.md      ↪ Jump after
  ✓  Update the runbook               infra.md      → WORK
  ⊘  Replace obsolete dashboard       ops.md        Cancel

Pull in 1 · Cancel 1
Jump after: Prioritize rollback checks · infra.md       Clear

⌃J Jump after     Tab Toggle & move     ↵ Apply & jump
```

Here the jump target is explicitly left open. The row's focus outline still shows keyboard position; the state well still shows disposition; the compact badge shows deferred navigation. Do not tint the entire row to mean jump, because that would compete with highlight and Done/Cancel treatment. A resolved row can dim or strike its task text while its Jump after badge remains legible.

The pinned summary matters more than a decorative icon. Filtering should never hide the fact that a different, offscreen task will receive focus. Show “Jump after: [task] · [note]” and a Clear action. Clicking the summary may reveal that row inside the card; it must not open Obsidian early. Keep a restrained marker transition, honor reduced motion, and avoid rearranging groups when marking a task.

Make the primary action describe the pending operation: **Finish & jump** for jump-only closing, **Apply & jump** when picks or verdicts are also staged. Preserve existing labels when no jump is staged. Explain once in contextual help: “Choose one task to open after this completes. Its other choices stay the same.” Use “Jump after” rather than “Next” or “Start,” which would confuse task lanes and timer actions.

Provide a pointer equivalent and an accessibility action named “Jump here after completing”; change it to “Clear jump destination” when selected. On macOS, avoid nesting a new Button inside the existing row Button: use a sibling action or existing context-menu/accessibility-action surface. In Obsidian, preserve keyboard focus during rerender and make the separate toggle's pressed state explicit. Announce the marked task and the fact that its disposition has not changed. Color alone is insufficient.

W3C's keyboard guidance distinguishes focus from selection and emphasizes predictable, persistent focus. That supports keeping these indicators separate; it does not prescribe this particular feature or its shortcut. [W1]

**5. Ownership and the implementation seam I recommend**

Keep UI navigation intent in the clients, task identity and final-location calculation in the mutation authority, and editor navigation in Bob Navigation Hotkeys. Do not give Swift a new Markdown parser or ask it to mint block IDs. This follows the existing thin-client decision. [M1]

I recommend a small explicit request/receipt extension rather than a UI-only patch:

```json
{
  "picks": [],
  "closes": [],
  "jump": { "key": "opaque-offer-key" }
}
```

That is an illustrative Obsidian picker result. Preserve it through settlement, normalization, close finalization, and the caller's final navigation decision. Add an explicit capability on both the picker and caller so an older caller cannot display a control whose result it will drop. An API version increment alone is insufficient if a new picker is called by an old mutation owner.

For capture, an optional scalar `--jump-offer KEY` request is a reasonable parallel to `--complete-offer` and `--cancel-offer`; it requests a validated destination receipt and does **not** launch Obsidian from bob. If public, give it a short alias (`-j` appears unallocated in the inspected capture CLI; recheck before implementation), alphabetical help placement, and tests under the project's CLI rules. Alternatively keep it explicitly internal to the subprocess protocol. Send it only after positive capability advertisement from the same bob binary and draft preview. This is important here: current Mac code warns that old bob binaries can interpret unknown flags as capture text. [R4, M3]

A proposed additive response shape:

```json
{
  "pull_in": {
    "jump": {
      "supported": true,
      "key": "opaque-offer-key",
      "target": {
        "path": "/vault/projects/infra.md",
        "line": 42,
        "ref": "42:deadbeef",
        "block_id": "rollback-checks"
      }
    }
  }
}
```

Names are proposals, not existing fields. A capable response with no jump has no target. `block_id` is optional; do not create one merely to navigate. The existing `OpenNoteJson`/Go To location shape is a suitable reusable type. Dry-run may describe the planned destination, but only real successful submission authorizes navigation.

Why an explicit request? It gives the backend one selected identity to validate, handles jump-only offers that do not appear among picked tasks, and keeps a just-closed target addressable after it leaves the survivor list. An alternative is to add final navigation locators to every offer and close receipt and let the client select one. That is viable if another feature needs such locators, but it exposes a wider output guarantee and leaves more reconciliation to the clients. I favor the singular request for this feature.

Resolve the request against the original offer identity, then carry it through all transformations. After the complete batch is planned—including routing, moves, status/freshness changes, log insertion, and ID creation caused by actual pull-ins—construct the location from final staged text, much as `build_open_notes()` already does. Include unchanged jump-target notes in the read validation needed to protect the request. Use the final source task, not its Pomodoro link. Do not choose a duplicate ID-less task by nearest text or ordinal after the population has changed. The planner's identity mapping is the authority. [R6, R7]

For Obsidian, return an equivalent location only after the writer has settled the relevant task changes and reference updates. Propagate partial failures honestly: this path currently cannot promise whole-gesture rollback. A failed chosen disposition should not be presented as fully successful merely because the predecessor closed. Keep the failure visible and offer a navigation-only action when appropriate, rather than blindly jumping away from the error. The intended happy path still performs one automatic jump after success. [R8]

**6. Navigation order and exactness**

Use one final navigation arbiter per gesture:

```text
explicit successor jump
    otherwise Capture's original submit-and-open plan
    otherwise the caller's existing navigation / review continuation
```

The ordering is behavioral, not “run all three with the jump last.” Open the chosen task once. Avoid opening ordinary capture notes first and then jumping, which would create extra tabs, history entries, and focus races. Without a jump, preserve the original submit modifier. Clearing a jump restores that modifier's ordinary behavior at completion; it does not forget how the draft was submitted.

Reuse the existing Bob task-navigation resolver and editor-focus primitives, with an exact mode that:

1. Resolves the selected final task identity in current content, preferring its block identity when available and validating task shape.
2. Accepts the planned line only with matching identity evidence; otherwise uses an unambiguous identity/digest relocation.
3. Refuses ambiguous or missing targets instead of focusing a clamped line as though it were the task.
4. Reveals folded content, scrolls the task into a comfortable viewport position, focuses its editor line, and retains a jump-back entry. Do not select the whole line or start Vim insert mode; the next key should not accidentally overwrite the task.

A same-transaction move should follow the returned final path. A later external move or deletion is a separate race: if exact resolution cannot prove the destination, report it and offer Retry jump / Open note, without guessing. No generic vault-wide fuzzy search is needed for the first version.

Native Obsidian URIs can address existing blocks when encoded correctly, but they do not supply Bob's ID-less identity validation and editor-focus behavior. They are a fallback for an explicit Open note action, not a replacement for the existing Bob route. [W2]

Exact-mode compatibility must be real. Passing an extra query parameter to an old handler that ignores it would still permit approximate landing. Use an explicitly versioned/capability-gated exact route, deploy the Obsidian support before enabling the Mac control, and test mixed versions. A dedicated exact handler is safer than a flag silently ignored by old handlers. `NSWorkspace` accepting a URL proves dispatch, not task focus. Obsidian should report resolution failure itself; if the product needs the Mac to display verified “Jumped” success, add a request-ID acknowledgment. Do not claim that guarantee from the current Boolean opener callback. This research did not establish an existing cross-app acknowledgment protocol. [R4, R5]

**Review walk adjustment.** When the predecessor close is a review answer and an explicit jump is selected, record the answer but park the walk at its continuation point instead of physically landing on the next review row. Then navigate to the chosen successor. The next ]s/[s resumes from the parked review context; merely focusing an offered task does not stamp, consume, or manufacture a review landing for it. If the jumped task also happens to be due, it remains eligible until normally answered. This is an intentional exception to answer-auto-advance, supported conceptually by the existing task-move parking behavior, but it needs explicit documentation and tests. Without it, the user's navigation request is unreliable. [M2, R9]

**7. Failure, refresh, and lifetime rules**

| Situation | Required behavior |
|---|---|
| Capture mutation refuses or fails | No navigation; retain draft and explain the failure. Restore same-gesture choices where valid. |
| Selected identity is stale before an atomic capture commit | Refuse/reopen with refreshed offers; do not silently substitute the highlighted row. |
| Refresh retains the same proven identity | Preserve jump across filtering/reordering, along with marks and verdicts. |
| Refresh loses that identity | Explain “Jump destination changed”; require an explicit new target or continuation without it. Keep the implicit pull-in fallback suppressed. |
| Success returns a final Done/Cancelled task | Navigate to that closed row; do not reopen it. |
| Commit succeeds but app launch or exact landing fails | Keep the successful close. Report “Completed; couldn't jump”; retry navigation only. Never resubmit the capture. |
| Duplicate Enter or delayed async callback | One mutation and at most one automatic navigation, tied to the gesture/request ID. |
| New draft, changed bob executable, new card, or abandoned gesture | Invalidate the old jump intent; never carry it into another close. |

Store the intent in the request/gesture context, not a process-global “next task” variable. Capture already uses request IDs, draft snapshots, client identity, and analysis generations; extend those guards. Carry it through intermediate choice contexts and clear it on completion. A retry destination is session-local navigation state, not a durable successor tray.

**8. Explicit requirement adjustments**

These are recommendations beyond the literal request:

1. **Zero or one**, never a mandatory/default destination; repeating Ctrl+J clears it.
2. **No implied planning effect.** Jump adds no pull-in, lane change, freshness stamp, block ID, timer start, or reopening. Normal predecessor recovery still happens.
3. **Suppress implicit Enter pull-in once jump selection has been touched.** This is necessary for safe jump-only use and remains in effect after clearing the marker.
4. **Explicit navigation also overrides review auto-advance.** Park/resume the walk; do not let it steal focus afterward.
5. **Exact focus is required for automatic success.** A nearby line is not a successful jump. Navigation failure does not undo or replay a completed close.
6. **“Any state” means any disposition of an offered task.** Do not broaden the candidate set into a browser of all previously closed/cancelled tasks or hidden aggregate rows. This keeps scope bounded while satisfying the stated combinations.
7. **Keep the chord local.** Preserve existing Ctrl+J behavior outside the successor card and make the action available by pointer and accessibility APIs.

The shared component can support promotion/new-project successor cards when their callers adopt the same finalization contract. Do not expose an inert marker in those paths or casually extend unrelated note-pull flows. Audit every caller; either wire the complete behavior or withhold the capability there.

**9. Verification and delivery implications**

I ran the existing Obsidian successor-picker, successor-verdict, and Go To URI test files together with Node's test runner; they passed. This validates the inspected baseline under its test harness, not the proposed feature. No product files changed, and no Swift compilation or live Obsidian/macOS visual testing was performed.

The implementation should add behavioral tests concentrated at the existing seams:

| Test area | Essential cases |
|---|---|
| State model | Toggle/replace/clear a single jump; all four dispositions; changing disposition preserves jump; zero pull-ins after jump-only and after jump-clear. |
| Interaction | List/filter focus, empty results, hidden selected task, collapsed groups, reason editor, exact modifier matching, repeats, composition, mouse and accessibility action parity. |
| Submission | Plain Return and original Command/Control-Return; Shift-Return; route/move intermediate cards; stale refusals; new draft; client change; repeated confirmation. |
| Final target | ID-bearing and ID-less tasks; duplicate descriptions; same-batch moves; earlier line insertions; closed/cancelled target; Unicode/plus/hash paths; source task versus daily link. |
| Post-commit navigation | Exactly one dispatch; no ordinary note opening alongside it; no jump on failed mutation; navigation failure never repeats the close; exact resolver refuses ambiguity. |
| Review integration | Done from an existing landing records once, parks without an intermediate landing, jumps once, and resumes ]s/[s without skipping or falsely consuming the jump target. |
| Compatibility | New/old bob, caller/picker version mismatches, missing or old navigation handler; new flags never sent without positive support. |
| Visual/accessibility | Light/dark themes, narrow card, long task/note names, Done/Cancel plus jump, high contrast, VoiceOver, reduced motion, folded destination. |

Use the existing Rust offer/verdict integration tests, portable `CaptureCore` state tests, Mac key-router/model/view tests, and plugin modal/URI harnesses. For Swift changes, compile the affected Mac targets and run the repository's macOS gate; portable tests alone cannot validate AppKit/SwiftUI. Plugin edits must change source fragments and rebuild generated entrypoints, then deploy with `bob plugins sync` under the repository's rules. This report is research, so no build, deployment, or implementation approval is implied.

The likely work spans three repositories and is more than a shortcut patch, but it should not require a daemon, database, new persistent task field, a global navigation framework, or a new task editor. The exact-location contract and final navigation ownership are the work worth paying for.

**10. Evidence index and limits**

Repository paths below refer to the pinned revisions above; line numbers are orientation points, not claims about future heads.

| ID | Primary source | What it establishes |
|---|---|---|
| R1 | bob-plugins `plugins/bob-navigation-hotkeys/src/206-successor-picker-modal.js`, especially lines 300–375, 490–535, 689–782; `206c-successor-picker-verdicts.js`, lines 490–610 | Key handling, implicit pick, result settlement, API v4, reason/escape behavior |
| R2 | bob-plugins `plugins/task-status-cycler/src/089g-successor-offer-close.js:45`; `137a-successor-offer-close-integration.js:249`; `137-plugin-successor-project.js:433` | Choice normalization, caller capabilities, revalidation, final close result |
| R3 | bob-mac-capture `Sources/BobMacCapture/CapturePullInChoice.swift:559`, `:648`; `Sources/CaptureCore/CapturePullInOutcomes.swift:165`, `:368` | Per-card state, fallback/canCommit calculations, refresh behavior |
| R4 | bob-mac-capture `Sources/BobMacCapture/CapturePanelModel.swift:4165`, `:5139`, `:17926`; `CaptureKeyCommandRouter.swift:655`, `:837`, `:1414` | Submit context, modifier inheritance, final success branch, failure restoration, key conflicts |
| R5 | bob-mac-capture `Sources/CaptureCore/ObsidianOpenURL.swift:19`; bob-plugins `plugins/bob-navigation-hotkeys/src/675-plugin-goto-task-uri.js:155`, `:511` | Existing URI encoding, identity relocation, approximate fallback, editor focus |
| R6 | bob-cli `src/native/capture/output.rs:1450–1643`; `src/native/capture/offer_verdicts.rs`; `src/native/task_complete/offer_close.rs` | Offer identity, final-home comments, ID-less ordinal caveat, separate close receipts |
| R7 | bob-cli `src/native/capture/mod.rs:411`; `src/native/capture/open_notes.rs:1–145` | Planned batch, success-after-commit boundary, backend-built locations, moved-task landing |
| R8 | bob-plugins `plugins/task-status-cycler/src/160-plugin-completion.js:325–377`; `130-plugin-references.js:52`; `137-plugin-successor-project.js:885–987` | Predecessor closes before finalization, best-effort successor pass, later retirement and partial failures |
| R9 | bob-plugins `plugins/bob-navigation-hotkeys/src/536-plugin-review-advance.js:490–555`, `:624`; `537-plugin-review-move-park.js` | Review answer bookkeeping, automatic landing, existing park/resume mechanisms |
| M1 | Audited memory `decisions:unblocked-tasks-are-offered`, `decisions:mac-capture-is-a-thin-client` | Explicit pull-in decisions, automatic recovery, bob owns capture semantics |
| M2 | Audited memory `decisions:answering-advances-the-walk`, `decisions:task-move-never-advances-the-walk`, `decisions:q-and-ctrl-bracket-mirror-esc` | Existing navigation and dismissal policies; proposed exception made explicit |
| M3 | Audited memory `cli_rules.md`; linked-repository `AGENTS.md` files | CLI aliases/help conventions and required source/build/macOS validation practices |

[W1] [W3C APG: Developing a Keyboard Interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/), accessed 2026-11-20. Primary guidance for distinguishable focus/selection and predictable keyboard behavior. The Jump after design is my application of that guidance, not a W3C recommendation.

[W2] [Obsidian Help: Obsidian URI](https://help.obsidian.md/uri), accessed 2026-11-20. Documents note/block URI navigation and encoding. Bob-specific exactness and editor focus are established by the local code, not by the generic URI documentation.

Remaining uncertainty is concentrated in live behavior: window activation on cold Obsidian startup, folded-task visibility, accessibility presentation of the combined row controls, and the best minimal capability/acknowledgment transport for exact cross-app navigation. These should be resolved during implementation with a real Mac and Obsidian. The report does not assert that a launched URL proves a successful landing, or that Obsidian's existing best-effort close path has capture's atomicity.

**Recommended solution.** Implement **Ctrl+J → Jump after** as a transient, single destination on the existing successor card. Keep task disposition independent; make Enter reliably support jump-only completion; produce a verified final task location through the mutation owner; and perform one exact Obsidian editor jump after the enclosing operation settles. Give this explicit choice priority over Capture's ordinary open plan and review auto-advance, with a parked review continuation and navigation-only recovery on failure. Ship the modest badge, persistent destination summary, and accessible toggle together with that contract. This preserves the feature's useful simplicity while making its promise trustworthy.
