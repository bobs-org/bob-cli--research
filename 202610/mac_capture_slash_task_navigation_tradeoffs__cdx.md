# Slash task navigation in Bob Mac Capture: reuse the picker, separate the action

Researcher: **cdx**. Date: **2026-10-13**. Independent research for the five-researcher swarm; no peer reports or findings were consulted. This report proposes a design; it does not implement the feature.

## Decision in brief

The idea is useful: the existing global capture panel can also be a quick entry point to a task's full context. Keep `/` as a shortcut from an empty editor, use the same task catalog and search presentation as `:`, and make acceptance an **Open in Obsidian** action. Do not insert a link or run capture as an intermediate step.

My preferred first release uses **Obsidian's built-in block navigation URI**, plus `:`'s existing explicit Add block ID prompt for tasks without IDs. Add a small read-only Bob resolver to validate the selected task and return its current filesystem target. A custom Obsidian protocol handler is justified only if a Mac proof shows that the native URI cannot satisfy the agreed focus behavior, or if opening ID-less tasks without any vault write becomes a requirement.

The distinction matters: searching is almost entirely reusable; reliable task identity, the acceptance action, and the exact meaning of “focus” need decisions.

## Evidence and limits

I inspected these checkouts, opened through `sase repo open`:

| Repository | Inspected revision | Purpose |
| --- | --- | --- |
| bob-cli | `1de9e036918de01098339ee5b07378231e6df465` | Capture grammar, task catalog, task refs, ID assignment, target paths |
| bob-mac-capture | `eed300d33e5296336f5b24fb56a762f283aa9048` | Picker state, acceptance, process orchestration, key routing, URI helper |
| bob-plugins | `4f0cc94231556c5058030187da02b827a9ba8b93` | Existing Obsidian navigation and possible bridge host |
| obsidianmd/obsidian-api | `9abd9605ce081383674aae1ed111c456edde0688` | Public protocol, editor, and workspace APIs |

I also read the thin-client decision, vault conventions, CLI rules, artifact rules, and definitions of Area Note, Project Note, and Task Link through audited SASE memory reads. The thin-client rule keeps grammar, task discovery, and vault mutation in Bob; Swift owns presentation, process orchestration, and keyboard interactions.

I ran read-only completion calls and capture dry runs against a temporary synthetic vault using the installed `bob 0.1.0`. That binary's commit provenance was not established; the probes corroborate the inspected source rather than proving it is built from that exact revision. No real vault task was modified. I could not run AppKit/Obsidian on this Linux host, so viewport, editor focus, folded sections, cold launch, and Vim behavior remain Mac verification items.

## What `:` actually does today

### Catalog and scope

`:` searches **linkable open tasks**, including Ready `[ ]`, Blocked `[?]`, Next `[*]`, and In Progress `[/]`, from the capture-target catalog. That means the inbox, routable root area notes, and non-terminal root project notes. It excludes nested notes, reference notes, completed/cancelled tasks, terminal projects, and ordinary untyped root notes. The selected task's owning file is its residence; a Pomodoro grouping does not make the daily note its navigation destination. These constraints are explicit in [the capture contract](https://github.com/bobs-org/bob-cli/blob/1de9e036918de01098339ee5b07378231e6df465/docs/capture.md#L978-L1045) and [the catalog scanner](https://github.com/bobs-org/bob-cli/blob/1de9e036918de01098339ee5b07378231e6df465/src/native/capture_targets.rs#L205-L230).

This is narrower than the phrase “Obsidian task search” might suggest. For this feature I would preserve it: it matches the requested `:` behavior and avoids quietly building a second task catalog. If vault-wide search including references or nested projects is wanted later, make that a separate explicit scope decision.

The default grouping is queued tasks in today's ledger order, then unqueued In Progress, then Next, then tasks grouped by owning note. The app presents a full Bob snapshot and locally fuzzy-matches text, note, ID, section, and Pomodoro fields. Filtering is presentation work already allowed by the architecture. [TaskLinkPickerIndex](https://github.com/bobs-org/bob-mac-capture/blob/eed300d33e5296336f5b24fb56a762f283aa9048/Sources/CaptureCore/TaskLinkPickerPresentation.swift#L9-L120) keys rows by `route|ref`, so several ID-less rows survive even though their replacement strings are empty.

### Acceptance is capture-specific

Return, Tab, or clicking an identified `:` row inserts Bob's `@route:block-id` replacement into the draft. Command-Return can then submit it. Shift-Return adds `=` to start the session when captured. An ID-less row opens an explicit naming prompt; Bob assigns the ID before the app inserts the link. [The acceptance branch](https://github.com/bobs-org/bob-mac-capture/blob/eed300d33e5296336f5b24fb56a762f283aa9048/Sources/BobMacCapture/CapturePanelModel.swift#L3286-L3400) and [panel tests](https://github.com/bobs-org/bob-mac-capture/blob/eed300d33e5296336f5b24fb56a762f283aa9048/Tests/BobMacCaptureTests/CaptureTaskLinkPanelTests.swift#L45-L84) demonstrate this behavior.

Therefore `/` should reuse the selection experience, **not call the existing link-insertion routine and change what happens afterward**. That would retain capture continuations, ID-prompt continuations, and success handling that have unrelated side effects.

The row action text also needs a navigation variant. Today it says “inserts …” or “adds … then inserts,” and future-scheduled rows can say linking pulls the task forward. `/` must instead say “Open in Obsidian” or “Add block ID, then open.” Keep the scheduled date as context but omit the pull-forward promise: opening a task should not retire its schedule. [Those strings are authored here](https://github.com/bobs-org/bob-mac-capture/blob/eed300d33e5296336f5b24fb56a762f283aa9048/Sources/CaptureCore/TaskLinkPickerPresentation.swift#L304-L325).

### Probe results

The synthetic vault contained a root area, root project, inbox, nested area, queued identified task, unnamed task, scheduled blocked task, and completed task.

| Probe | Observed result |
| --- | --- |
| `capture-complete --cursor 1 -- ':'` | `task_link`; queued identified task first, ID-less tasks included, scheduled blocked task included |
| Same catalog, completed/nested tasks | Excluded |
| Completion on `/`, `/fix`, `/tmp/file` | No completion context or candidates |
| Completion on `:fix` | Matching identified task, with a range covering the entire query |
| Completion on `: fix` | No task-link context |
| `capture --dry-run -- '/fix'` | Successful ordinary capture preview targeting `mac_inbox.md` |
| `capture --dry-run -- ':fix'` | Exit 2 with a teaching error directing the user to select a task |

The last two results expose a real implementation hazard: if `/` becomes draft syntax but only Swift understands it, a preview or submit can turn an unresolved search into an inbox item. An app-owned keyboard mode avoids that issue because its trigger/query never becomes capture text. If the implementation chooses `/query` as actual capture-language syntax, Bob must classify it, provide completion, and reject unresolved execution before the app ships. [The existing colon classification](https://github.com/bobs-org/bob-cli/blob/1de9e036918de01098339ee5b07378231e6df465/src/native/capture_language/editor_parse.rs#L667-L705) is a useful precedent for that alternate design.

## Is this a good idea?

Yes, as a small task-navigation shortcut. It lets Bryan locate a task while working outside Obsidian, then land in the area/project context where he can edit or act on it. Reusing `:`'s established layout and ranking makes the behavior learnable. `/` is a recognizable search gesture, especially for a Vim user.

The main costs are mode clarity, literal slash input, and ID-less task friction. A panel named Capture now performs navigation too; the header and action labels must make the current action obvious. A first typed slash is also how an absolute path begins. And many tasks may lack anchors: forcing a naming ceremony just to inspect a task can be annoying.

I would not create a separate launcher window or general slash-command menu for this request. Those expand scope without improving the requested task jump. An alternate modifier action on `:` (for example Option-Return to open) could preserve one trigger and work while editing a draft, but it is less discoverable and competes with an already dense picker keymap. It could be a later convenience using the same opener; I would keep the requested dedicated `/` gesture initially.

The possible objection I take most seriously is “navigation should never write.” The requested parity with `:` already admits an explicit Add block ID step. Keeping that step is a reasonable low-cost first release, provided it clearly says the ID will be added. If that exception is unacceptable, the architecture changes: use a navigation bridge with a validated line identity instead of silently adding IDs or hiding unnamed tasks.

## Requirements I would clarify or adjust

These are proposed decisions, not claims that the original prompt already specified them.

1. **Trigger scope: exactly an empty editor.** `/` typed into the capture editor with an empty draft and caret at zero opens navigation. It does not activate merely because a slash is at the start of a later batch item, inside text, or in a restored nonempty draft. This tightens `:` parity to the user's “first key in the input box” wording and protects unsent drafts.
2. **Make `/` an app keyboard command, not a new capture spelling.** Enter navigation mode immediately, put subsequent keystrokes in its existing filter field, and ask Bob for the existing full `:` task snapshot. The synthetic `:` request is a deliberate discovery call; do not rewrite user drafts from `/` to `:`. This is UI orchestration, not a Swift grammar implementation. If pasted `/query` should also be recognized as a persistent draft, choose the Bob-language alternative instead and implement its rejection semantics there.
3. **Define focus before coding the transport.** Obsidian must become frontmost, open the owning note, reveal the task row, and, in an editing view, leave the caret on that row so the next action operates there. Opening the note at its old scroll position is insufficient. Do not open the Task Card, complete the task, or advance a review walk. Centering and an optional transient highlight are useful but not required for the first release.
4. **Read-only opening, with one explicit exception.** Searching, selecting an already identified task, and opening must not modify task status, lane, schedule, freshness, dependencies, or the Pomodoro ledger. An ID-less row may reuse the explicit Add block ID prompt. No silent ID assignment. The prompt says “Add ID and open”; cancelling restores the picker and filter.
5. **Parity applies to searching, not capture actions.** Return, Tab, and click open the chosen row. Command-Return should also open, with no capture; consume Shift-Return in this mode rather than start a session. Retain the same navigation/filter keys. Keep the two-stage Escape convention: first clear a nonempty filter, then leave search.
6. **Provide a literal-slash escape.** Leaving an empty-filter `/` picker should return to the empty editor with its automatic trigger suppressed for the next slash entry; `/tmp/file` can then be typed literally. Pasted paths bypass a keyboard-only trigger. Make this behavior visible in a compact hint. This is a necessary accommodation for reserving the first slash.
7. **Fail without losing state.** No candidate, stale target, invalid URI, or OS dispatch failure keeps the picker/query available with an actionable error. Successfully handing the URL to Obsidian hides the panel and clears navigation-only state. A cancelled lookup or an older Bob response never falls through to capture submission.
8. **Call the scope “Open tasks,” not universal search.** Include the inbox because `:` does; do not exclude it just because the prompt mentions area/project notes. Preserve the current eligibility set until scope is deliberately expanded.

These refinements keep the feature bounded while making accidental writes and ambiguous focus behavior reviewable.

## Opening and focusing: the transport choices

### A. Built-in Obsidian block URI — preferred first

Current official documentation explicitly supports encoded heading/block navigation in the `file` parameter. It also says the absolute `path` parameter selects a containing vault and passes the remaining path as `file`. That makes native block opening a credible first approach; older discussions recommending Advanced URI are insufficient evidence that it is still required. [Obsidian URI documentation](https://help.obsidian.md/uri).

The app already owns [ObsidianOpenURL](https://github.com/bobs-org/bob-mac-capture/blob/eed300d33e5296336f5b24fb56a762f283aa9048/Sources/CaptureCore/ObsidianOpenURL.swift#L3-L16), which constructs `obsidian://open?path=...` from a Bob-returned absolute target. Extend it with a distinct task overload accepting a validated target and block ID. Build the entire query value with `URLComponents`/`URLQueryItem`, never a shell command or manually concatenated encoded URL.

Illustrative values before query encoding:

```text
path = /Users/bryan/bob/dev.md#^fix-sync
```

The `#^fix-sync` belongs inside the query value; it must not become the URI's outer fragment. A documented alternative is `file=dev.md#^fix-sync` with a known vault identity. Prefer the existing absolute-path strategy to guessing a vault name or hardcoding a Mac home directory.

**Evidence boundary:** heading/block support via `file` is documented; extending absolute `path` with the block subpath is an inference from its documented translation to `file`. Prove that exact form on Bryan's installed Obsidian. The docs do not establish the required editing caret, fold, or Vim behavior. Those are acceptance tests, not guaranteed properties of this report.

Advantages: no new plugin dependency, no local server, no Accessibility automation, and block IDs tolerate edits above the row. Costs: unnamed tasks need an explicit anchor; deletion/movement to another note invalidates the old location; OS URL dispatch does not prove that Obsidian landed on the expected task.

### B. Advanced URI — viable if already a chosen dependency

Advanced URI supports a file with block, or one-based line and column. That can open tasks without IDs after a fresh resolver returns a line, and offers more navigation controls. [Maintainer navigation documentation](https://publish.obsidian.md/advanced-uri-doc/Actions/Navigation).

However, its presence/version on Bryan's Mac was not established in this investigation. Do not assume it is installed just because old forum answers mention it. Adding a third-party dependency solely for identified task jumps looks unnecessary given the current native URI contract. A line remains a location, not a durable identity, and can change between Bob validation and plugin handling. If Advanced URI is already an intentional installed dependency and its mode/cursor behavior passes the Mac checks, it can replace a custom bridge for the stronger read-only-unnamed requirement.

### C. Small custom handler in bob-navigation-hotkeys — strongest control, higher cost

No `registerObsidianProtocolHandler` usage was found in the inspected custom plugin source. A new `bob-open-task` action would be additive work, not reuse of an existing external endpoint. The public API supports registering handlers and opening files; the Editor abstraction supports cursor placement, focus, and scrolling. [Official API definitions](https://github.com/obsidianmd/obsidian-api/blob/9abd9605ce081383674aae1ed111c456edde0688/obsidian.d.ts#L7300-L7308), [editor methods](https://github.com/obsidianmd/obsidian-api/blob/9abd9605ce081383674aae1ed111c456edde0688/obsidian.d.ts#L3754-L3795), and [editor guidance](https://docs.obsidian.md/Plugins/Editor/Editor).

`bob-navigation-hotkeys` is the appropriate host because it already owns file/leaf navigation, cursor placement, and Vim history. Its [openMarkdownFileWithLeafReuse helper](https://github.com/bobs-org/bob-plugins/blob/4f0cc94231556c5058030187da02b827a9ba8b93/plugins/bob-navigation-hotkeys/src/480-review-jump-and-nav-api.js#L862-L887) can reuse an existing note leaf. Factor a neutral navigation helper rather than invoking task-move or review-answer methods with their unrelated bookkeeping.

For unnamed tasks, the handler should validate the selected snapshot against the current editor content, not trust a numeric line. Pass an exact note path plus block ID where present; otherwise pass a line hint and a raw-line digest or equivalent Bob-owned identity. Inspect an open editor first so unsaved edits are authoritative. Revalidate after asynchronous opening, account for folds/view readiness, and focus the final row without modifying it. Bob's existing `ref` is an eight-hex line digest, not a globally stable task ID; any cross-language digest handling must have explicit shared fixtures.

This approach can meet a strict “read-only, unnamed tasks, focused editing caret, reuse existing leaf, return jump history” requirement. It adds a third-repository deployment and compatibility surface. If programmatic success acknowledgment is required, design a callback contract too: successful dispatch of a custom URI does not establish that its handler ran. Do not introduce an HTTP listener or shell-evaluation endpoint for this small feature.

### D. Other approaches

| Approach | Assessment |
| --- | --- |
| Obsidian `search` URI | Opens search results; it does not directly fulfill selected-task focus |
| File open only | Loses the task position; insufficient |
| AppleScript/UI keystroke automation | Timing, permissions, and layout dependence make it inferior to URIs/API |
| Capture, then open its result | Performs the wrong action and can mutate ledger/status/schedule |
| Hide every unnamed task | Violates `:` catalog parity and makes common tasks undiscoverable |
| Silently add an ID on selection | Surprising navigation write; preserve the explicit prompt instead |

## Recommended implementation shape

### Keep the picker catalog separate from its purpose

The task snapshot and fuzzy index should be shared. The session needs an explicit purpose such as `insertTaskLink` versus `openTask`; the implementation can represent this as a purpose value or a dedicated source using the same index. Do not scatter checks against whether a draft string begins with `/` throughout `CapturePanelModel`.

Parameterize task-specific action labels, missing-ID continuation, schedule messaging, and acceptance. Retain the `route|ref` row keys and shared grouping/ranking. Do not copy `TaskLinkPickerIndex` into a second fuzzy implementation. Its `FuzzyQuery` currently strips `:`; the new mode should provide an already-normalized filter or a parameterized display sigil so `/` is not searched as part of the text.

Enter the mode synchronously on the key so typing during the Bob fetch is buffered in the filter. Show loading/error states in the same card. Guard the trigger by the editor first responder, actual produced `/` character, empty document/caret, no active picker/prompt, and no marked-text composition. Use the produced character rather than a US-layout hardware key code. Subsequent `/` characters in the filter are ordinary search text.

Request `capture-complete --cursor 1 --format json -- ':'` to obtain Bob's full catalog and filter locally. [BobProcessClient.captureComplete](https://github.com/bobs-org/bob-mac-capture/blob/eed300d33e5296336f5b24fb56a762f283aa9048/Sources/CaptureCore/BobProcessClient.swift#L151-L169) already supplies that contract, but uses the shared `completion` process lane. Give navigation fetching/resolution its own lane and generation token, or deliberately cancel/suspend draft analysis while navigation owns the panel. A late response after Escape, settings change, or reopening must never launch Obsidian.

This design honors the thin-client rule: Swift treats `/` as a keyboard shortcut to an app mode; Bob still authors every task candidate and validates every vault operation. It does not declare `/query` to be a new capture language.

### Validate at acceptance, not once at list fetch

The existing JSON has `route`, `ref`, optional `block_id`, and one-based `line`, but the task-link candidate does not include an absolute filesystem target. The target catalog separately provides `bob_dir` and `relative_path`; these are adequate for a prototype. Do not derive the destination from the displayed note name, Pomodoro ownership, or a parsed `@route:id` replacement. [Candidate contract](https://github.com/bobs-org/bob-cli/blob/1de9e036918de01098339ee5b07378231e6df465/src/native/capture_complete/model.rs#L144-L172), [target contract](https://github.com/bobs-org/bob-mac-capture/blob/eed300d33e5296336f5b24fb56a762f283aa9048/Sources/CaptureCore/CaptureModels.swift#L4036-L4100).

For the shipping feature I favor one small read-only protocol sibling, provisionally:

```text
bob capture-task-location --route dev --task-ref 5:e27f9f8d \
    --block-id fix-sync --format json
```

The name and schema above are proposals, not existing commands. Return schema version 1 with the validated absolute `target`, exact `relative_target`, current `ref`, one-based `line`, and nullable `block_id`. Reuse Bob's route resolution, Tasks settings, scanner, and lookup errors; do not run status hooks or write any note. Keep public option short aliases and help ordering consistent with the CLI rules. This read-only command belongs at top level among protocol siblings, not under `bob task`, whose local membership rule is vault-wide task-line mutation.

For an identified task, resolve the supplied block ID in the supplied owning note and reject duplicates/non-task anchors/missing targets. The physical line digest may change through ordinary edits without changing this anchor identity. For an unnamed row, use `NoteTaskScan.by_ref`: matching line+digest first, then a unique digest elsewhere in the same note. A changed or ambiguous unnamed row requires refreshing and reselecting. [Lookup semantics](https://github.com/bobs-org/bob-cli/blob/1de9e036918de01098339ee5b07378231e6df465/src/native/note_tasks.rs#L148-L183). The digest is SHA-256 of the physical line after trimming trailing whitespace, truncated to eight hex characters; it is stale detection, not a durable identifier. [Digest implementation](https://github.com/bobs-org/bob-cli/blob/1de9e036918de01098339ee5b07378231e6df465/src/native/note_tasks.rs#L367-L369).

Keep the first-release eligibility policy consistent with the snapshot: if it has closed or left the catalog, refresh rather than guessing its new destination. Do not chase a block ID across the entire vault: IDs are scoped to their note, and cross-note moves need a deliberate identity design. A task can still change between filesystem validation and Obsidian opening; the core-URI option cannot eliminate that race, especially with unsaved editor content. If those races are materially disruptive, that is evidence for the bridge option.

### Preserve explicit ID naming, change its continuation

An unnamed selection enters the existing ID prompt with Bob's suggestions. The prompt uses `capture-task-id`, which already revalidates the line and rejects stale/ambiguous selection, duplicate IDs, and tasks that are no longer open. [Existing writer guards](https://github.com/bobs-org/bob-cli/blob/1de9e036918de01098339ee5b07378231e6df465/src/native/capture_task_id.rs#L450-L490).

Its success continuation must now resolve/open the returned task, not splice `@route:id` or submit. Use the returned ID, ref, and `relative_target`, not the pre-prompt snapshot. If opening fails after the ID was successfully added, tell the user that the ID was added and keep the open action retryable; do not pretend the whole operation was rolled back or remove the authored ID.

### Treat dispatch as a distinct operation

The app's current `targetOpener: (URL) -> Void` discards the `NSWorkspace.open` outcome and is used after successful capture. Introduce an injectable task-opening operation with a dispatch result/error. Keep its success handling separate from `completeSubmit`: no capture success notification, no clearing an unrelated draft, and no opening today's daily note.

Disable duplicate acceptance while resolution, ID assignment, or dispatch is running. Dismiss the panel only after dispatch is accepted, with navigation state invalidated so a delayed callback cannot restore the Capture focus. A dispatch result is still not an Obsidian task-landing acknowledgment; user-visible wording and tests should not overstate it.

## Proof and verification before shipping

The first step should be a small Mac proof with a fixture note and a block ID: use the exact encoded native URI through the app opener and inspect actual task landing. This settles the transport risk before doing picker refactoring.

| Area | Meaningful cases |
| --- | --- |
| Trigger | Empty editor; retained draft; second batch item; slash within text; non-US keyboard; IME/marked text; pasted absolute path; literal-slash escape |
| Search parity | Identical candidates/order to `:`; multiword fuzzy filter; inbox/area/project groups; unnamed rows; queued task opens its owning note |
| Acceptance | Return/Tab/click open once; Command-Return opens without submit; Shift-Return never starts; empty result does nothing |
| ID prompt | Explicit add-and-open wording; cancel preserves filter; stale/ambiguous ref; duplicate anchor; success uses returned identity; open failure after successful ID write |
| Resolver | No vault-byte changes; row moved within note; task changed/closed; missing/renamed note; duplicate task/non-task anchor; unsupported Bob contract |
| URI | Spaces, Unicode and reserved characters in vault path; encoded `#^id` in query; no outer fragment; correct vault among multiple vaults |
| Obsidian landing | Cold/warm app; another note active; target already open; reading/source/live preview; folded task ancestors; caret on selected row; Vim next action applies there |
| Lifecycle | Escape during fetch; settings/vault change; panel reopened; double Return; OS opener failure; stale callback does not steal focus |
| Mutation boundary | Identified open leaves task and day files byte-identical; explicit ID assignment changes only its intended note through Bob |

Use Bob unit/contract tests for the resolver, CaptureCore tests for purpose-specific rendering and URL encoding, and AppKit model/router tests for lifecycle and acceptance. Run the Mac repository's normal formatting/build/test checks on macOS. Manual target-focus checks remain necessary: neither a mock opener nor a JSON test establishes actual Obsidian cursor behavior. No feature tests were added or full suites run in this research-only turn.

## Recommended solution

**Implement `/` as an empty-editor navigation shortcut using `:`'s Bob-authored catalog and shared fuzzy picker, with an explicit open purpose. Add a small read-only Bob task-location resolver, retain the explicit Add block ID prompt for unnamed tasks, and dispatch a correctly encoded native Obsidian block URI.** Opening must not insert capture syntax, link a Pomodoro, start a session, alter schedules/status, or advance the review walk; the only permitted write is the user's explicit ID assignment.

First prove native absolute-path block navigation and the required editing caret on Bryan's Mac. If that proof fails, add a narrow `bob-open-task` handler to `bob-navigation-hotkeys` using its neutral file/leaf navigation helpers. If Bryan instead requires navigation to be completely read-only even for unnamed tasks, select that bridge design up front. I would not add Advanced URI, a daemon, or UI scripting by default. This delivers the requested gesture with the existing architecture and keeps the stronger navigation machinery contingent on an observed need.
