# Relation gestures in Bob Mac Capture: equals aliases, direction changes, and literal escape

Independent research by **cdx**, 2026-11-06.

I recommend implementing the requested interaction, with explicit limits on where `=` is an alias. Keep `~` and `~~` as the canonical capture language; replace the relation-opening `-` shortcut with `=`; allow direction changes at an unlabelled relation target's end and in both relation cards; and give every relation use of `=` the same reversible, rapid-`==` escape. The difficult parts are preserving native `=` commands, making the escape independent of subprocess timing, and invalidating direction-sensitive label validation.

This is research, not an implementation. No product code, vault data, or memory was changed. I investigated independently and did not read or obtain any other swarm researcher's findings.

## Evidence and scope

The source checkouts inspected were:

| Repository | Commit inspected |
| --- | --- |
| bob-cli | `ee05db4d8ffeb6714ee90abbcf65d9d7c6215e46` |
| bob-mac-capture | `e9d3ae2fdade28d031811b458c5f18633f38e023` |

I read the audited decisions `mac-capture-is-a-thin-client` and `relation-card-tab-accepts-ctrl-d-hides`, plus the Task Relation glossary. The implementation must retain Bob's ownership of grammar and label semantics, and the card's separation between typed query and selection by canonical label key.

I also ran read-only `capture-rewrite`, `capture-parse`, and `capture-complete` probes with the installed `bob 0.4.0`. Completion probes used a disposable fixture directory in this workspace, not the real vault. These observations agree with the inspected source and tests; the installed executable was not rebuilt or proven to originate from the inspected SHA. I did not run AppKit tests or compile Swift on this Linux host. Conclusions about the app are source-based and need macOS verification during implementation.

Source references below are commit-pinned links to files inspected locally. Apple documentation was checked separately for event and text-input behavior.

## What the current implementation actually does

### 1. There are separate implementations for opening and flipping

In bob-cli, `expand_sigil_alias` dispatches `-` to a past-session helper first and then to `expand_relation_dash_alias`. The latter changes a whitespace-prefixed dash into `~` only where Bob's completion grammar selects an empty relation target. It excludes line/bullet-body starts, glued words, backticks, and wikilink contexts.

`expand_relation_flip_alias` handles only a very narrow `=` case: `~=` becomes `~~`, and eligible `-=` becomes `~~`. It intentionally leaves `~~=`, completed targets, and other equals uses alone. The test suite explicitly asserts those exclusions. [CLI rewrite implementation](https://github.com/bobs-org/bob-cli/blob/ee05db4d8ffeb6714ee90abbcf65d9d7c6215e46/src/native/capture_language/rewrite.rs), [rewrite tests](https://github.com/bobs-org/bob-cli/blob/ee05db4d8ffeb6714ee90abbcf65d9d7c6215e46/src/native/capture_language/tests/rewrite.rs).

Once the app's task relation picker is open, the behavior is broader: `pickerCommand` routes either `~` or `=` to `flipRelationDirection`. That model method inserts/removes one prefix tilde using the picker's replacement range and preserves the filter. This explains why direction changes already work in the target picker even when the CLI's corresponding editor rewrite does not. [Key router](https://github.com/bobs-org/bob-mac-capture/blob/e9d3ae2fdade28d031811b458c5f18633f38e023/Sources/BobMacCapture/CaptureKeyCommandRouter.swift), [model, `flipRelationDirection`](https://github.com/bobs-org/bob-mac-capture/blob/e9d3ae2fdade28d031811b458c5f18633f38e023/Sources/BobMacCapture/CapturePanelModel.swift#L8893).

Observed CLI examples, all at the end-of-input cursor:

| Input to `capture-rewrite` | Current output |
| --- | --- |
| `Fix it -` | `Fix it ~` |
| `Fix it =` | unchanged |
| `Fix it ~=` | `Fix it ~~` |
| `Fix it ~~=` | unchanged |
| `Fix it ~foo:bar~` | unchanged |
| `Fix it ~~foo:bar~` | unchanged |
| `Fix it ~foo:bar=` | unchanged |
| `Fix it ~~foo:bar=` | unchanged |
| `Fix it ==` | unchanged |

Appending `=` or `~` to the completed block ID currently produces an invalid ID in `capture-parse`; these are not hidden parser aliases waiting for the app to expose them.

### 2. The label panel has no direction command

`relationLabelPromptCommand` handles navigation, Tab, hide/unhide, rename, and submission, but leaves ordinary `~` and `=` to text editing. `CaptureRelationLabelPromptState` makes `direction` and `tokenRange` immutable. The panel therefore needs a state transition as well as routing changes. [Router, `relationLabelPromptCommand`](https://github.com/bobs-org/bob-mac-capture/blob/e9d3ae2fdade28d031811b458c5f18633f38e023/Sources/BobMacCapture/CaptureKeyCommandRouter.swift#L917), [prompt state](https://github.com/bobs-org/bob-mac-capture/blob/e9d3ae2fdade28d031811b458c5f18633f38e023/Sources/BobMacCapture/CapturePanelModel.swift#L280).

The panel already knows its relation's UTF-8 range, label replacement range, owner, target, direction, and return-picker snapshot. Bob's `relation_label` completion explicitly supplies the token range and direction so the client need not rediscover the token. This is enough to implement a bounded prefix edit without adding a Swift relation parser. [Completion relation contract](https://github.com/bobs-org/bob-cli/blob/ee05db4d8ffeb6714ee90abbcf65d9d7c6215e46/src/native/capture_complete/model.rs#L710).

### 3. An equals escape does not currently exist

The app has a useful precedent for `/` and `\`: a pending-rewrite probe handles the second key before Bob replies, and a literal arm handles the second key after the rewrite. Both paths restore a single literal alias character. However, those structures and router branches are specific to hash aliases; `=` is not included. The existing relation dash escape is another separate path for space, dash, or Escape. [Model, alias state and probe](https://github.com/bobs-org/bob-mac-capture/blob/e9d3ae2fdade28d031811b458c5f18633f38e023/Sources/BobMacCapture/CapturePanelModel.swift#L24), [controller key routing](https://github.com/bobs-org/bob-mac-capture/blob/e9d3ae2fdade28d031811b458c5f18633f38e023/Sources/BobMacCapture/CapturePanelController.swift#L2270).

The hash precedent is next-key based: its inspected arm/probe structures contain no timestamp or maximum interval. It is not already a general timed double-press engine. Existing equals tests expect two consecutive presses in an open picker to flip there and back; those tests must change for rapid `==`, while retaining a slower two-press case. [Equals tests](https://github.com/bobs-org/bob-mac-capture/blob/e9d3ae2fdade28d031811b458c5f18633f38e023/Tests/BobMacCaptureTests/CaptureRelationFlipAliasTests.swift).

### 4. Both proposed aliases have real competing uses

The assertion that `=` never has another meaning in a relation-capable context is too broad. A bare `=` starts a Pomodoro, while a bare `~` opens an ownerless relation picker. Replacing the former merely because the latter would complete successfully would steal a real command. `x =` is a close/start chain; glued `@work:outline=` is an existing link-and-start form. Ordinary task prose may also contain equals signs. These need deliberate exclusions, not a global character substitution. [Capture syntax](https://github.com/bobs-org/bob-cli/blob/ee05db4d8ffeb6714ee90abbcf65d9d7c6215e46/docs/reference/capture-syntax.md).

`-` also aliases `~` in a distinct past-session feature: `x=2-` rewrites to `x=2~`. Removing every dash-to-tilde rule would regress that feature. Interpret this request as removing **the relation dash alias**, preserving the unrelated past-session shortcut. [Past-session helper and tests](https://github.com/bobs-org/bob-cli/blob/ee05db4d8ffeb6714ee90abbcf65d9d7c6215e46/src/native/capture_language/tests/rewrite.rs#L1702).

Finally, `=` is a valid relation-label character; `~` is forbidden there. A probe of `Fix it ~foo:bar|a=b` preserves label `a=b`. Thus the label panel's equals escape is necessary for actual valid data, not merely an escape from a surprising menu. [Label normalization](https://github.com/bobs-org/bob-cli/blob/ee05db4d8ffeb6714ee90abbcf65d9d7c6215e46/src/native/task_relations/label.rs).

## Critique and explicit requirement adjustments

The proposal improves consistency and removes the particularly intrusive dash alias from ordinary prose. Completing the label-panel interaction is valuable: choosing a label is exactly when the source/target sentence makes a wrong direction apparent. I would keep the requested gestures rather than replace them with a modifier-only shortcut.

I would make these adjustments explicit before implementation:

| Adjustment | Reason |
| --- | --- |
| `=` is the only **relation** alias; `~`/`~~` remain canonical, and the past-session dash shortcut remains | Keeps the request scoped and preserves an unrelated workflow |
| New-relation `=` opens only in eligible task-tail positions; line/item starts and native equals operators retain their meaning | A hypothetical `~` picker alone is insufficient to establish alias eligibility |
| In the editor, a suffix flip requires the caret directly after the unlabelled target, with no intervening whitespace | A separated `~` must remain available for adding another relation |
| Do not interpret `=` inside an inline label as a direction command | Equals is valid label text; use the label card to reverse labelled relations |
| Rapid `==` means one literal `=`, restoring the state before the first alias action | Matches the existing hash-alias escape model and makes the output unambiguous |
| Direction changes preserve label spelling and selected key; they do not substitute an inverse label | Reversing the edge and inverting the phrase together could preserve the old meaning instead of correcting it |
| Disable direction commands in label **rename** mode and while an irreversible label operation is saving | Rename is a separate text-entry operation with different consequences |
| Add a visible direction control/help hint to both cards | Provides discoverability and a way to reverse without relying on double-press timing |

The whitespace boundary is a real usability tradeoff. Picker acceptance currently appends a separating space at the end of a draft. With this recommendation, pressing `~` or `=` after that space starts another relation; to reverse the accepted token directly, delete the space, or open its label card with `|` and reverse there. Shift-Return already opens the label card directly. Do not silently treat an arbitrary space as belonging to the previous relation: that would make multiple relations ambiguous. If immediate reversal after ordinary acceptance is later required, design an explicit completion-provenance rule; I would not add that hidden mode in this change. [Accept-and-open-label implementation](https://github.com/bobs-org/bob-mac-capture/blob/e9d3ae2fdade28d031811b458c5f18633f38e023/Sources/BobMacCapture/CapturePanelModel.swift#L10896), [pipe attachment rewrite](https://github.com/bobs-org/bob-cli/blob/ee05db4d8ffeb6714ee90abbcf65d9d7c6215e46/src/native/capture_language/rewrite.rs#L1286).

There is also a timing tradeoff: rapid `==` can no longer mean “flip twice.” That is acceptable because it has no lasting directional effect anyway. Slower presses, canonical `~`, and the visible direction control remain available. I suggest an initial **350 ms** key-to-key window, treated as a product choice to verify on the Mac, not a measured optimum. Keep it a named, test-injectable constant; a new settings screen is unnecessary initially.

## Proposed behavior contract

`D` below is an otherwise eligible task draft. “Fast” means two deliberate non-repeat key-downs within the escape interval, with no intervening user action. These are typing gestures, not new syntax accepted by `bob capture` or pasted text.

| Starting surface / draft | Gesture | Result |
| --- | --- | --- |
| Editor, `D ` | `=` | Canonical `D ~`; open Links To |
| Editor, `D ` | fast `==` | `D =`; restore editor and dismiss alias-created picker |
| Editor, `D ` | `-` | Literal dash; no relation menu |
| Empty item, `x `, native equals suffix | `=` | Preserve native equals behavior |
| Target picker, either direction | `~` | Reverse direction, keep filter |
| Target picker, either direction | `=` | Same reversal; arm literal escape |
| Target picker | fast `==` | Restore original direction; insert one `=` at the original filter selection |
| Editor, `D ~foo:bar` | `~` or `=` | `D ~~foo:bar`; consume the suffix trigger |
| Editor, `D ~~foo:bar` | `~` or `=` | `D ~foo:bar`; consume the suffix trigger |
| Editor, `D ~foo:bar ` | `~` or `=` | Start another relation; do not change `foo:bar` |
| Editor, completed relation target | fast `==` | Restore original direction and insert one literal `=` at the original caret |
| Label card, choose mode | `~` or `=` | Reverse relation; retain query, selection, target, hidden view, and one-off state |
| Label card, choose mode | fast `==` | Restore original direction and insert one `=` in label text at its original selection |
| Label card, rename mode | `=` | Ordinary rename text |
| Pasted draft containing `==`, or ordinary typing where `=` is not an alias | `==` | Preserve both characters |

A literal escape prevents the editor alias; it does not make invalid capture syntax valid. For example, a literal `=` glued onto a relation ID will still get Bob's ordinary invalid-ID diagnostic. Do not hide that diagnostic or invent a second backend escaping language.

The existing bare-prefix editor behavior should also become consistent in both directions: `~` followed by `=` selects `~~`, and an already established `~~` followed by `=` selects `~`. Keep normal typed `~~` as the canonical incoming relation. Test mixed rapid sequences such as `=~` across the rewrite race; the UI must not change meaning merely because the picker appeared between the keys.

## Recommended implementation design

### Keep grammar recognition in bob-cli

Extend `capture_language/rewrite.rs`, not the capture executor:

1. Replace only `expand_relation_dash_alias` and its `-=` relation path with a conservative equals-opening helper. Keep `expand_past_segment_dash_alias`.
2. Check the original editing context for native equals ownership and protected contexts. Require a real eligible task-tail position, then validate the hypothetical `~` result with the ordinary completion grammar. Reuse existing exclusions for prose-adjacent, code, wikilink, template, and bullet-start positions.
3. Add a completed-target direction rewrite for `~` and `=`. Remove the just-typed trigger in a scratch string, locate a complete selected relation using the existing relation scanner and contextual extraction, and require its target to end exactly at that cursor. Reject escaped tokens, partial targets, inline label contents, and grammar contexts where the apparent token is prose.
4. Insert/remove exactly one prefix tilde and consume the suffix trigger. Preserve the original bytes of note spelling, quotes, ID, and surrounding draft. Use UTF-8 spans, not a regex over the last whitespace-delimited word: quoted note names already exist.
5. Make the output idempotent. The returned canonical draft should not flip again when submitted to `capture-rewrite` with the returned cursor.

Give the tail operation a clear rewrite rule such as `toggle_relation_direction`. A two-edit response is sufficient: prefix insertion/deletion plus trigger deletion. No new general RPC or relation parser in Swift is needed. The app already has `CaptureRewriteResponse.coveringEdit`, which validates sorted, non-overlapping edits and combines them into one native text replacement; the native rewrite path is not actually limited to one JSON edit despite its current helper name. [Covering-edit implementation](https://github.com/bobs-org/bob-mac-capture/blob/e9d3ae2fdade28d031811b458c5f18633f38e023/Sources/CaptureCore/CaptureModels.swift#L3401).

Keep `capture-parse` and `capture` literal. Users of the CLI, paste, templates, and stored drafts should not acquire timing-dependent syntax.

### Use one relation gesture coordinator in the app

Keep the three surfaces explicit: draft editor, target filter, label chooser. They can share a small reversible equals-gesture record rather than accumulate another set of unrelated booleans. This need not become a framework for every shortcut.

Record the initiating surface, prompt/picker identity, pre-action draft and selection, original direction and relation range when known, expected post-action state, request generation, and first key timestamp. In particular, remember **where the first key originated**: the second key may arrive in a newly opened picker, but an escaped opener belongs back in the editor.

Order key handling as follows:

1. Respect locks, native shortcuts, rename mode, and IME composition.
2. Check a pending equals escape before ordinary relation direction routing.
3. If the current surface supports a relation gesture, perform/ask Bob for that gesture and record its reversible state.
4. Otherwise let AppKit insert the text normally.

In the editor, add `~` to the existing typed-intent path; it currently records `=` and `-` but not `~`. Register the new rewrite rule for native undo-aware application. In known picker/card contexts, share a prefix-splice helper operating only on Bob-supplied relation ranges and direction. That is bounded editing of an identified token, not client-side syntax recognition. [Typed-intent capture](https://github.com/bobs-org/bob-mac-capture/blob/e9d3ae2fdade28d031811b458c5f18633f38e023/Sources/BobMacCapture/CapturePanelController.swift#L1071), [rewrite application](https://github.com/bobs-org/bob-mac-capture/blob/e9d3ae2fdade28d031811b458c5f18633f38e023/Sources/BobMacCapture/CapturePanelModel.swift#L15508).

### Make escape depend on key events, not process speed

Handle both timelines:

- **First rewrite already applied:** restore its saved pre-action state, insert one literal `=` in the original field/selection, and invalidate its completion/validation results. Do not merely flip again: that would lose the literal character and could leave the wrong focus.
- **Second key arrives before the reply:** retain both native characters provisionally and use the first request, or the existing first-draft probe pattern, to establish whether that first key really was an alias. Only then collapse to one literal equals. If the first key was not an alias, preserve both. Never accept the late first reply against the second draft.

A genuine native equals command must not be classified as an alias because its second key arrived quickly. A pending `==` decision must remain valid through the expected programmatic editor-to-picker focus transition, but not through a user click, caret move, other edit, pane dismissal, paste, Undo, or replacement of the Bob process client. Treat request generation and draft revision as part of identity, even if the text happens to return to an earlier spelling.

For `=~` and other subsequent deliberate gestures, preserve event order while the first rewrite is pending. Do not guess a mixed-sigil grammar in Swift or silently lose the second gesture. A narrowly scoped queued relation gesture, released only after eligibility is known, is preferable to interpreting arbitrary pasted strings as key history.

Measure the interval using `NSEvent.timestamp`, which Apple defines relative to system startup. Use `event.characters` to recognize the intended printable character rather than assuming the US equals keycode. Ignore auto-repeat for toggling/escaping and do not intercept marked-text composition. These recommendations follow AppKit's event/text model, not any claim that Apple prescribes a 350 ms threshold. [Timestamp](https://developer.apple.com/documentation/appkit/nsevent/timestamp?changes=_1_7&language=objc), [characters](https://developer.apple.com/documentation/appkit/nsevent/characters?changes=l_2&language=objc), [repeat property](https://developer.apple.com/documentation/appkit/nsevent?changes=_3), [marked text](https://developer.apple.com/documentation/appkit/nstextinputclient/hasmarkedtext%28%29).

Preserve native Undo/Redo and the existing suppression of automatic rewrites after undo. The current `breakUndoCoalescing`/`insertText` path makes the rewrite a distinct undo step restoring the literal post-key draft. Extend that deliberately; do not replace the full editor model and assume AppKit's undo history follows. Native rewrite helpers that force focus back to the editor need a focus-preserving variant for the label card. [Native editor edit helpers](https://github.com/bobs-org/bob-mac-capture/blob/e9d3ae2fdade28d031811b458c5f18633f38e023/Sources/BobMacCapture/CapturePanelController.swift#L1150).

### Treat label reversal as a semantic state change

Make the relevant prompt fields rebasable, or replace the prompt with a new value retaining its user state. Change the actual canonical token as well as the displayed direction. Shift `tokenRange.end`, both label-range endpoints, and subsequent restore offsets by the prefix-length delta. Preserve quoted targets, the authored query, `selectedKey`, one-off hiding, the hidden section, and field selection.

Immediately swap the source/target sentence and show the direction. Keep the label phrase unchanged. For example, `A —depends on→ B` becoming `B —depends on→ A` is the reversal the user requested; automatically replacing the phrase with “is depended on by” would undermine it.

Invalidate every direction-dependent result: catalog row eligibility, typed-row validation, cancel/complete/successor consequence, pending submit, and outstanding requests for the prior semantic revision. Although vocabulary filtering is local, the catalog carries direction-dependent disabled rows. Refresh the catalog once for the new direction and revalidate the typed or selected label; ordinary navigation must remain local and must not refetch. Keep label identity selected if it still exists, showing a disabled reason if the new direction makes it ineligible.

This matters because configured labels can cancel, complete, or merge the **source** task, and `~~` changes which task that is. Existing fixtures even report that a new task cannot be born cancelled and suggest `~~` to retire the existing task instead. A selected catalog row currently can be accepted directly, so refreshing only the typed-row probe would leave a stale acceptance path. Pending Return must wait for current-direction validation or be cancelled on reversal; it must never replay an old validated action. [Label submission and validation](https://github.com/bobs-org/bob-mac-capture/blob/e9d3ae2fdade28d031811b458c5f18633f38e023/Sources/BobMacCapture/CapturePanelModel.swift#L12108), [cancel-label fixture](https://github.com/bobs-org/bob-mac-capture/blob/e9d3ae2fdade28d031811b458c5f18633f38e023/Tests/Fixtures/relation-cancel-complete-new-task-typed.json).

For Escape, recommend that an explicit direction edit remains in the draft while the uncommitted label is dismissed. If Escape returns to the target picker, rebuild/rebase its range, snapshot, direction, and candidate data from the current draft. The current `returnPicker` is a saved snapshot; blindly reinstating it after a prefix edit would resurrect stale state. Test the `|`-opened flow and the Shift-Return flow separately.

A direction change itself must not write label preferences or execute a relation effect. Those remain governed by their existing explicit actions and final capture.

### Compatibility and delivery

Keep JSON additions optional and retain existing schema conventions. A new app talking to an older Bob should leave unsupported editor rewrites literal rather than manufacture syntax. Existing picker/card range metadata supports their bounded edits; if required metadata is absent, refuse that shortcut with an update hint rather than scan the draft in Swift.

Ship Bob's lexical changes and tests before the app integration, then update the user-facing capture and picker documentation together. Document the lost relation dash shortcut, literal `==`, the glued-versus-separated boundary, and that direction toggles keep the label text. Release notes should identify the behavior change; follow the project's daily release process rather than manually editing versions or changelogs.

## Validation that would justify shipping

The high-value tests are transitions and races, not assertions that mirror helper internals.

| Area | Required cases |
| --- | --- |
| Equals eligibility | Eligible task tail and explicit owner; bare item `=`, named start, `x =`, link-and-start suffix, split/merge operators, arithmetic/prose, newline/bullet start |
| Dash regression | Relation dash stays literal; em-dash typing still works; past-session `x=-` and `x=2-` continue to rewrite |
| Target suffix | Both directions × `~`/`=`; quoted and Unicode note names; leading/trailing relation; multiple relations; adjacent label pipe; caret before following text |
| Protected/literal text | Escaped relation, completed/unclosed code, wikilink note/heading/alias, template, incomplete ID, unquoted label containing `=`; no scanning to an earlier unrelated token |
| Canonical invariants | Rewriting output again is unchanged; no `~~~`; no duplicate trigger; exact surrounding bytes retained; `capture-parse`/`capture` do not gain alias behavior |
| Escape outcomes | All alias surfaces × both original directions; one literal equals; before/after/during reply; threshold boundary; slower second equals; non-alias `==` preserved |
| Event ordering | Delayed first reply, reordered completion, `=~`, `~=`, rapid reversal twice, `==` then text, fast Return while rewrite or label validation is pending |
| Label state | Query and canonical selected key survive; one-off and hidden view survive; source sentence updates; equals inserted at field caret/selection; rename field remains ordinary text |
| Effect correctness | Cancel/complete/merge/successor examples in each direction; new owner versus existing owner; selected and typed rows; stale response cannot restore the prior source or enable stale submission |
| Return/cancel | Label card opened by `|` and Shift-Return; Escape after reversal returns to a valid current picker/editor; accept inserts label at rebased range |
| Native editing | Unicode before the token, IME, keyboard-layout characters, repeat events, nonempty selection, paste, Undo/Redo, explicit focus moves and app dismissal |
| Version skew | New app/old Bob no-op rewrite; new rule decoded and applied through native edit path; missing optional metadata handled conservatively |

Expand the existing Rust rewrite tests and CLI editor-contract tests. In the app, extend `CaptureRelationFlipAliasTests`, replace the relation-specific expectations in `CaptureRelationDashAliasTests` while keeping its past-session cases, and add chooser routing/state tests in `CaptureRelationPanelTests`. Use fake-Bob delayed responses and injected event times rather than wall-clock sleeps for the escape threshold. Existing fake-Bob tests already cover a delayed dash/equals rewrite and stale reply rejection, providing a practical starting point.

The implementation must compile Swift. Follow the Mac repository's required `just portable-check`; for AppKit changes, compile a scratch Mac copy with `bundle.sh` and `just typecheck-tests`, and run the exact-SHA macOS CI tests. `portable-check` alone cannot type-check these AppKit targets. Run documentation checks for changed docs. Any unavailable Mac validation must be reported explicitly, not described as passing.

## Recommended solution

Proceed with the four requested improvements as a coordinated bob-cli and Mac app change. Use **`=` as the sole relation alias**, preserve all native equals commands and the unrelated past-session dash alias, add **glued completed-target reversal** through Bob's rewrite API, and enable **the same reversal in the target and label cards**. Implement **one timed, reversible `==` gesture across all relation surfaces**, including the before-reply race. Preserve the label phrase and user selection while recomputing direction-dependent consequences.

Keep whitespace as the boundary for starting a new relation, leave inline label equals signs as data, and provide a visible direction control. These boundaries make the behavior predictable without introducing another capture grammar in Swift. The main shipping gate should be the delayed-reply escape tests plus label-effect revalidation; a key-routing patch alone would leave the most consequential bugs unresolved.
