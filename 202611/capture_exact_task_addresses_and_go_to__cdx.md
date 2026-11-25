**Direct task addresses in Capture: an exact Go To shortcut**

Independent research by **cdx**, 2026-11-25. This report uses the supplied screenshot, local source inspection, isolated CLI probes, project memory, and primary external documentation. I did not read or request any other swarm researcher's report or findings. This is a design recommendation; no product code or real vault content was changed.

I recommend supporting a standalone `@foo^bar` as **Go To the existing task `^bar` in `foo.md`**. It is a good complement to `/`: search helps when you remember the task; an address helps when you already have its location. The panel already supports navigation, so this does not need another command surface. The important qualification is that this must be a distinct, read-only intent, with exact resolution and visible action wording. Treating it as an empty task capture with a special exception would leave too many opportunities for the parser, preview, picker, and submit button to disagree.

The conceptual rule should be: **an address alone opens; an address with task text keeps the existing creation behavior.** Whether the task exists must decide whether navigation succeeds, never whether the draft means navigation or creation.

The screenshot, `/home/bryan/tmp/screenshots/20261125_135534.png`, shows `@bob^intention-rollovers`, already highlighted as route plus block ID, above the error “task text is required; pass TEXT or pipe it on stdin.” The same error occupies two places, the footer says “Preview failed,” and the primary button still says “Capture.” This is a mismatch between a plausible user intention and the current interface. Fixing only submission would leave that mismatch visible during typing. The feature should replace the failed capture preview with a small, recognizable destination card before Return is pressed. I did not inspect the actual task or infer its contents from the ID.

The source and runtime evidence establish three important constraints.

First, `^` already has an authoring meaning. `New task @foo^bar` creates a task with an explicit block ID; `@foo^bar New task` is also supported. A bare marker is parsed as task mode, but execution rejects the empty parent body. The Rust creation path formats `TaskWithBlockId` as a new task. The Block ID Picker explicitly treats a caret marker as `intent: new`, lists used IDs, and offers unused alternatives. An existing ID is currently a collision, not a destination. This is why the change touches completion as well as execution. See [the shared grammar][C1], [empty-body rejection][C2], [creation planning][C3], and [block-ID intent selection][C4].

Second, `/` already has the desired navigation side effects: none. Its completion rows include the absolute note target, vault-relative path, line, block ID, and a line digest reference. Accepting a row dispatches `obsidian://bob-goto-task`; it does not invoke capture, mint an ID, link the task, move its schedule, or advance the review walk. The plugin focuses the task through the established editor/navigation machinery and captures a Vim jump origin. The native model guards against repeated accepts while dispatch is in flight. See [task picker behavior][M1], [the completion row contract][C5], [native dispatch][M2], and [plugin landing][P1].

Third, “open succeeded” currently means the operating system accepted the URL dispatch. The Mac callback does not acknowledge that the plugin located the requested task. The plugin can recover a moved row by block ID or digest, but ultimately falls back to a clamped line; its block-ID helper returns the first matching task. That is a useful distinction for an exact address: neither a nearby row nor an arbitrary duplicate should satisfy it. This is not a hypothetical claim about the API: it follows from `taskGotoOpener`, `refindGoToTaskLine`, and `findTaskLineByBlockId` in the inspected code. [Native dispatch][M2], [re-finding logic][P1], [block-ID search][P2].

I independently ran `bob capture-parse`, `bob capture-complete`, and `bob capture --dry-run --no-clip` against disposable fixtures, with `BOB_DIR` pointed inside this workspace's temporary fixture directory. No capture was executed against the real vault. The installed binary reported **bob 0.6.0, grammar 29**; the inspected checkout advertises **grammar 30**, so these are installed-version observations corroborated by source inspection, not a claim to have compiled the checkout.

| Probe | Observed result | Design implication |
|---|---|---|
| Parse `@foo^bar` | `mode: task`, no needs or diagnostics | The preview failure is later than lexical recognition. |
| Dry-run `@foo^bar` | Exit 2; exact missing-text error from the screenshot | A submission-only patch is insufficient. |
| Complete `@foo^bar` | `context: task_block_id`, `intent: new`, used ID `bar`, no candidates | The existing New ID composer is the wrong UI for navigation. |
| Parse `@foo^` | Incomplete; needs `block_id` | Partial address typing needs an intentional transition. |
| Dry-run `New task @foo^bar`, where `bar` exists | Existing-block-ID rejection | Text-bearing drafts must retain collision protection. |
| Dry-run `@foo^new-id`, where it does not exist | Missing-text rejection | Missing addresses must not become new tasks automatically. |
| Parse `@foo:bar` / `@foo+bar` | `pomodoro_link` / `task_toggle` | These adjacent gestures must remain separate. |
| Parse `/bar` and dry-run it | `task_goto` need; execution refuses it as navigation | The existing panel-only navigation architecture is reusable. |
| Complete `/` in an area-note fixture | A Go To row with target, line, ref, and block ID | Reuse the destination shape and landing machinery. |
| Parse `@foo^bar` followed by a blank line and another task | Two items, with the first body's text empty | Classification must consider the whole draft, not just its first item. |

The fixture's status labels were “Unknown” without the full task-status configuration; its locator fields and new-ID intent were still sufficient for these probes. I did not run the Mac app, exercise an Obsidian URL, or verify visual behavior on macOS.

The proposed shortcut has a real ergonomic benefit, but it also overloads an authoring prefix. A user can start a new task by typing its destination first, pause at `@foo^bar`, and then add text. The interface must permit that intermediate state without trapping the user in a modal picker. The address card should be presentation under the existing editor, with no mandatory confirmation and no focus transfer. Continuing with Space and task text must immediately return to the usual creation preview. A short teaching line can say “Add task text to create with this ID.” If that ID already exists, creation should then produce the existing collision error; opening or modifying the existing task instead would be a dangerous semantic change.

For this reason I would not add a `Go To` intent to the current block-ID `intent` enum as a shortcut implementation. The documentation says an unknown explicit intent falls back to a New ID composer. A new value interpreted by an old app could therefore present exactly the wrong workflow. Use a separately recognized navigation context and explicit compatibility handling. Preserve the existing `task_block_id` response for creation. [Block ID Picker contract][M1].

The recommended acceptance boundary is deliberately narrow:

| Draft or target | Recommended behavior |
|---|---|
| `@foo^bar`, with optional surrounding whitespace | Exact task navigation, as one whole draft. |
| `@foo^` | Incomplete address; calm prompt and optional note-scoped suggestions. |
| `@foo^ba` with no exact `ba` task | No implicit destination; offer suggestions without choosing one. |
| `New task @foo^bar` or `@foo^bar New task` | Existing creation semantics, including duplicate-ID refusal. |
| `@foo^bar` plus child bullets | Existing capture validation; never silently ignore the children and open. |
| Two standalone addresses, or an address plus another capture item | Refuse the aggregate before any write; navigation is one draft at a time. |
| `@foo^bar@`, `@foo#Section^bar`, `%` directives, schedule/priority/relationship modifiers | Existing meanings and validations; excluded from address navigation. |
| `@@foo` plus `@foo^bar` | Excluded from the new shorthand; do not silently absorb declarations. |
| `@foo:bar`, `^foo:bar`, `@foo+bar` | Existing link/toggle actions. No change. |
| Exact task is completed, canceled, blocked, scheduled, hidden, or a project task | Open it without changing its state; show its status as context. |
| ID identifies a paragraph or notebook note bullet | Explain that it is not a task; do not relabel generic blocks as tasks. |
| Missing note, missing ID, duplicate ID, or malformed address | Keep the draft and report a specific resolution problem. Never create or guess. |

The eligibility test must operate on the original whole draft and parsed structure, before marker stripping, template expansion, or bulk planning can make a richer draft look empty. A shared Rust predicate should own this test for parse, completion, and capture refusal. The body-bearing cases above are not “navigation with options”; they retain their established authoring contracts.

For resolution, retain Bob's current route syntax and normalization. Today `is_route_token` admits ASCII letters, digits, underscores, and hyphens, and the ordinary capture `route_label` maps a route to `<route>.md`. Do not hard-code `~/bob`: resolve relative to the configured vault. Do not add path traversal, `.md` spellings, quoted paths, root-parent aliases, or a vault-wide basename search as incidental features. In particular, reference-parent alias resolution is a different subsystem; importing it here would change what `@foo` names. The core user request is the exact root note `foo.md`. [Route syntax][C6], [route mapping][C3].

Once the file is resolved, inspect that note using Bob's existing task parser and ID handling. Require exactly one addressable task with a case-sensitive matching ID. Detect duplicate IDs in the note, including collisions with non-task blocks, rather than trusting a search row or a first-hit regex. Reuse code-fence and task recognition rules, so a task-looking code example is not a destination. Do not filter exact resolution through “linkable tasks”: `/`'s default open catalog intentionally includes only certain note/task classes, while an explicit address should not cease to work because a task is completed or its project changes status. The addressed file is the search boundary. An archived/moved task with the old address should fail and offer `/` search, not silently follow the same ID into another note. [Go To catalog scope][C7].

This makes direct lookup fast and explainable: one known file, one ID, one task. A whole-vault index, new resident service, or fuzzy-matching dependency is unnecessary. Cache suggestions for responsiveness if useful, but re-resolve at acceptance. Keep the resolved path, ID, task label, and generation associated with the exact draft and Bob client identity.

The visual proposal is a compact version of the existing Go To language. This wireframe uses an illustrative title; the actual title must come from Bob's resolved task:

```text
  @bob^intention-rollovers

  ↗ Go To · Task
  □ Intention rollovers
    bob.md › Tasks                         ^intention-rollovers

  Opens this task in Obsidian
                                           [ Go To  ↩ ]
```

Retain the current route blue and block-ID indigo instead of inventing another token palette. Show the task title as the strongest content, one quiet breadcrumb/locator row, and the normal status glyph. Use the existing panel's fixed editor eye line and downward content growth. Do not render an empty write preview, duplicate error panel, task-count budget, or “Captured” toast for this action. The primary action should say **Go To**, with the same accent treatment as other primary actions; the redundant capture-and-open footer action should disappear in this mode. A short status announcement can read “Go To: Intention rollovers, in bob.md.” Use text and accessibility labels as well as color.

This is a design inference, supported by Apple's guidance that labels communicate a button's action and the likely action receives the primary role and Return behavior. It is not evidence that Apple prescribes this particular card. [Apple Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons).

Keep keyboard behavior explicit. With a resolved exact address, Return, Command-Return, Control-Return, and the primary button all open that task; modifier variants must never fall into the capture submit path. Suppress repeat dispatch while opening. Plain Tab should complete or browse an address rather than unexpectedly launch Obsidian from a field that also participates in authoring. For a non-exact prefix, Tab or selecting a suggestion replaces the ID using Bob's byte range; a subsequent Return opens the now-exact address. Do not auto-select a fuzzy result merely because Return was pressed. Pasting a complete address should resolve to the compact card directly, without forcing a browse interaction. These completion details intentionally differ from `/`'s picker acceptance; the landing behavior and absence of writes are the same.

Suggestion rows should contain existing tasks only, with no “New ID,” “Available,” “Next free,” or “Add block ID” actions. An ID-less task cannot satisfy an exact address. Keep `/` as the way to find and open such tasks without minting an ID. Adding task text or the existing project-note seal should restore the original authoring composer. Backspace and ordinary typing should remain normal editor operations, with native undo for a suggestion insertion. Escape should follow the panel's current hide/retain behavior and clear an open suggestion interaction before closing it; an abandoned pure navigation draft should follow `/`'s discard/no-stash policy. Exclude the whole intent from similar-task suggestions and capture templates that imply a write.

Loading and failure states should remain small. While resolving, show “Finding task…” and disable Go To for the current generation. A missing ID can say “No task ^bar in foo.md” with an explicit Search Tasks action and the secondary explanation about adding text for creation. A missing note says “foo.md was not found”; duplicates say “More than one block uses ^bar in foo.md.” Do not substitute a terminal-oriented instruction about piping stdin. The Search Tasks action may explicitly replace the draft with the existing `/` search interface, preserving normal undo; it must not auto-select or navigate to an alternative. Show ordinary unresolved typing neutrally, then announce a concise error if the user submits it. A malformed ID can be marked immediately using Bob's character-rule diagnostic.

The implementation should reuse the existing protocol surfaces instead of making the native app recognize an address with a regex. Project memory's thin-client decision requires Bob to own grammar, completion, and meaning. My suggested allocation is:

1. **Shared Rust language layer:** recognize the exact whole-draft intent; expose its source ranges, route, ID, and incomplete state. Add a deliberate mode/need such as `task_address`, rather than claiming it is a normal task. The name is illustrative. The execution parser should produce a specific navigation-only refusal for `bob capture`, just as `/` does, before writing or interpreting forced flags. Do not turn the CLI into a desktop launcher.
2. **Read-only resolution and `capture-complete`:** add a dedicated context that returns explicit `incomplete`, `resolved`, `not_found`, `ambiguous`, or invalid/wrong-target states. Reuse the existing Go To destination fields and row rendering data. Return exact resolution independently of the caret's position within a recognized address; no silent downgrade when the user moves the caret left. Keep task creation's block-ID context unchanged. Where possible, share the ID/task scanners, not the link eligibility rules.
3. **Native panel:** decode the context, render the destination card, suppress the doomed capture dry run, and route every accept gesture through one navigation dispatcher. Factor that dispatcher out of the picker-only method rather than synthesizing a fake `/` draft. Recheck the current draft/generation/client before and after resolution and in the asynchronous dispatch callback, so a late result cannot clear newly typed text.
4. **Plugin landing:** reuse `focusTaskAnchor`, editing focus, fold visibility, jump history, and existing path validation. Add an explicit strict-block navigation option for this intent: resolve the supplied block ID uniquely in the live editor buffer, require a task, and fail if absent or duplicated. Strict mode must not fall back to digest-only or nearby-line navigation. It should not alter ordinary `/` recovery unless a separate change deliberately chooses that policy.
5. **Documentation and compatibility:** document the paired examples `@foo^bar` and `Task text @foo^bar`, including the type-through transition. Add Mac protocol coverage, update the grammar revision appropriately, and version-gate the new native behavior. Keep JSON schema changes additive where possible. Follow the normal release train; do not hand-edit the CLI version or changelog.

A resolved response needs no elaborate new object model. For example, its conceptual payload can carry `kind: exact_task`, `status: resolved`, `route`, `block_id`, and a destination containing `note_path`, absolute `target`, `line`, and `ref`, plus task display fields. Bob should return structured identity and data; the native client already owns URL construction. Prefix suggestions can continue using server-provided UTF-8 replacement ranges. This example is an allocation of responsibilities, not a frozen wire schema.

There is an important cross-version constraint on step 4: an old plugin may ignore an unknown URI parameter. **Sending a strict flag is not sufficient proof that strict behavior is available.** Establish a minimum plugin version or capability through a Bob-owned compatibility check before enabling exact dispatch, with an actionable update message when unsupported. Do not substitute a generic note URL automatically. This makes the fully reliable feature a coordinated change across bob-cli, Bob Mac Capture, and bob-navigation-hotkeys, even though its UI is small.

The ordinary Obsidian URI can navigate to a block with a properly encoded file-plus-anchor value, and its documentation explicitly calls out percent encoding. That makes a generic URI tempting, but the existing Bob handler already supplies editor focus and Bob jump behavior. Retain its encoder, which handles `+`, spaces, Unicode, and reserved characters, rather than concatenating a new URL. The official Obsidian block-ID character set is letters, digits, and hyphens, matching the current Bob rule. [Obsidian URI](https://obsidian.md/help/uri), [Internal links](https://obsidian.md/help/links).

A strict plugin lookup still does not create an end-to-end acknowledgment to the Mac. For the first release I would keep the existing asynchronous dispatch model: OS failure keeps the draft; a last-moment plugin failure produces a precise Obsidian notice and does not land on a different task. Do not describe this as a verified successful landing. If retaining the panel until confirmed arrival is a hard requirement, it needs a separate callback/acknowledgment protocol and timeout, which substantially expands the feature. Re-resolving immediately before dispatch plus checking the live buffer at landing gives a useful reliability improvement without that infrastructure. The residual boundary should be explicit in testing and release notes.

The main alternative is an explicit `/@foo^bar` or `/foo^bar` syntax. That would make navigation visually unambiguous and preserve the current bare-caret composer, but requires an additional sigil even when the user already has a complete address, and does not meet the demonstrated expectation in the screenshot. I would choose it only if using addresses first to author new tasks is so frequent that the transient Go To card is disruptive. Do not ship both spellings initially; two spellings obscure the small rule we are trying to teach.

Another attractive later option is accepting a pasted Obsidian task wikilink such as `[[foo#^bar]]` as a standalone address. It is portable and explicit, but bare wikilinks already participate in capture content; changing that behavior needs its own compatibility decision. It is not necessary for this request. Opening arbitrary blocks, general folder paths, following moved task IDs, or mixing capture and navigation in one batch are similarly reasonable separate features, not prerequisites.

These are the requirements I recommend adjusting or making explicit:

- **Panel navigation rather than a mutating capture:** pressing the panel's primary action opens the task, while `bob capture` remains non-navigational and refuses the standalone intent clearly. This follows `/`'s existing contract.
- **Whole-draft scope:** only one bare address navigates. Other text, bullets, declarations, and modifiers do not get ignored or partially executed.
- **Exact task identity:** no fuzzy fallback, no new task or ID, no relocation to another file, and no first-match duplicate behavior.
- **Status-independent lookup:** a direct task address can open a closed or blocked task without the search picker's open/completed toggle or mutation eligibility restrictions.
- **Explicit action presentation:** label the action Go To and replace the write preview; a bare-caret editing context stops being the New ID composer until task text or a project seal is present.
- **Stricter final lookup than current `/`:** reuse the same final focusing behavior, but refuse if the exact addressed task no longer exists. This is a deliberate reliability improvement, not a claim about today's `/` implementation.
- **Narrow first release:** root route syntax and task targets only. No universal note-address language and no end-to-end arrival acknowledgment in the initial scope.

Verification should target semantic boundaries, not just a happy-path screenshot:

| Area | Essential acceptance checks |
|---|---|
| Grammar | Lone/padded address; partial route/ID; escaped/literal forms; malformed ID; same text with body before/after; global declaration; section, seal, modifiers, child bullets, two items. |
| Resolver | Exact ID versus prefix; ID case; missing file; duplicate task/non-task IDs; fenced examples; completed/canceled/scheduled/blocked tasks; project status; non-task notebook bullet. |
| No writes | Hash fixture vault files before and after resolution and accepted navigation; no task, ledger, block-ID, freshness, dependency, or schedule changes. Read-only temp/cache activity is a different concern from vault content. |
| Identity races | Insert lines, edit task text, delete the task, duplicate its ID, or modify an open unsaved buffer after preview; exact mode follows the unique live ID or refuses. Never lands nearby. |
| Native interactions | Full paste; typing a prefix; Tab completion; Return and modifiers; double Return; ordinary Space/type-through into creation; undo; Escape; OS dispatch failure; stale parse/resolution/dispatch callbacks after an edit. |
| Compatibility | Old Bob/new app; new Bob/old app; plugin below strict capability; missing handler; unknown JSON fields. Unsupported versions show a clear failure and never reinterpret the address as a write. |
| Presentation | Compact card; no duplicate error, empty preview, or Capture label; dark mode; VoiceOver; increased contrast; long title; narrow window; fixed editor position. |
| Regression | `/`, `//`, New ID composer, `@foo:bar`, `@foo+bar`, project seals, notebook creation, and aggregate capture continue to behave as documented. |

Run focused Rust and CLI checks for the shared grammar and resolver; native model and URL tests for dispatch; and plugin tests for strict live-buffer resolution and duplicate handling. Compile the native changes and use the repository's required macOS gate, including exact-SHA CI after a push. A Linux-only parse test does not validate the Mac feature. No performance measurements were taken here; profile direct single-note resolution on the Mac before introducing an index or daemon.

For reproducibility, the source baseline was bob-cli `e6eb52a103656add99a1a49f2f0b3d791536abc4`, bob-mac-capture `3931c308b376904d063208e13f793691396e58cc`, and bob-plugins `1ff10aa40e7f0b5a1c290bbdfb1897466168fcd3`. Repository links below identify locally inspected source, not web-fetched repository content. I also read the audited project decisions `capture-sigils-say-where-what-how`, `notebook-routes-write-notes`, `mac-capture-is-a-thin-client`, and `capture-link-drops-blocking-deps`, plus the Capture and Capture Panel glossary entries. They explain why navigation must remain distinct from link gestures and why grammar belongs in Bob. No existing memory record was changed or proposed for editing.

[C1]: https://github.com/bobs-org/bob-cli/blob/e6eb52a103656add99a1a49f2f0b3d791536abc4/src/native/capture_language/mod.rs
[C2]: https://github.com/bobs-org/bob-cli/blob/e6eb52a103656add99a1a49f2f0b3d791536abc4/src/native/capture_language/item.rs#L2500
[C3]: https://github.com/bobs-org/bob-cli/blob/e6eb52a103656add99a1a49f2f0b3d791536abc4/src/native/capture/plan.rs
[C4]: https://github.com/bobs-org/bob-cli/blob/e6eb52a103656add99a1a49f2f0b3d791536abc4/src/native/capture_block_ids.rs#L145
[C5]: https://github.com/bobs-org/bob-cli/blob/e6eb52a103656add99a1a49f2f0b3d791536abc4/src/native/capture_complete/model.rs#L721
[C6]: https://github.com/bobs-org/bob-cli/blob/e6eb52a103656add99a1a49f2f0b3d791536abc4/src/native/capture_language/markers.rs#L252
[C7]: https://github.com/bobs-org/bob-cli/blob/e6eb52a103656add99a1a49f2f0b3d791536abc4/src/native/capture_complete/candidates.rs#L1638
[M1]: https://github.com/bobs-org/bob-mac-capture/blob/3931c308b376904d063208e13f793691396e58cc/docs/task-pickers.md
[M2]: https://github.com/bobs-org/bob-mac-capture/blob/3931c308b376904d063208e13f793691396e58cc/Sources/BobMacCapture/CapturePanelModel.swift#L12201
[P1]: https://github.com/bobs-org/bob-plugins/blob/1ff10aa40e7f0b5a1c290bbdfb1897466168fcd3/plugins/bob-navigation-hotkeys/src/675-plugin-goto-task-uri.js
[P2]: https://github.com/bobs-org/bob-plugins/blob/1ff10aa40e7f0b5a1c290bbdfb1897466168fcd3/plugins/bob-navigation-hotkeys/src/180-editor-transactions.js#L760

My recommended solution is to ship **one exact, standalone task-address shortcut**: Bob recognizes and resolves `@foo^bar`; the panel shows the task and an explicit **Go To** action; the existing navigation machinery focuses the unique live task without writing anything. Preserve creation whenever task text is present, preserve `/` for discovery, and require strict block matching for this exact-address gesture. The idea is sound. Its quality will come from a small, visible rule applied consistently across typing, preview, completion, and landing—not from adding more syntax.
