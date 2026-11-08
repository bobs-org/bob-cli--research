# Contextual x/s aliases for capture close outcomes

Independent research by **cdx**, 2026-11-08.

**Recommendation:** Add lowercase `x → !` and `s → *` as editor typing assists in Bob-owned close-selection positions. Implement the semantic decision in `bob capture-rewrite`, and extend the Mac app's existing native rewrite lane. Keep the execution grammar unchanged. This is a useful convenience, but it requires explicit handling of ordinary-text collisions and asynchronous typing; adding two characters to a Swift allowlist alone is insufficient.

## Scope and evidence

I independently inspected the bob-cli checkout at `51d572d59075cc1b9363051ec453b4d3ee3e1ed4` and the linked bob-mac-capture checkout at `0583f37aef3241ffc872e11325f8afaec1c5cbcc`. I did not consult another swarm researcher's report, findings, or transcript. No product source was changed, and no capture was executed against the vault.

Evidence comes from current source, its existing tests and documentation, audited project decisions, read-only local CLI probes, and Apple's text-editing guidance. The installed executable reports `bob 0.4.0` and `capture-parse` grammar **16**; the inspected checkout declares grammar **19**. Runtime observations below are therefore observations of the installed binary, corroborated where indicated by current source, not tests of a freshly built checkout. I did not compile Swift or exercise the native UI. Timing-race conclusions are source-based predictions supported by existing delayed-response tests, not measured Mac failures.

Important source references, all pinned to the inspected commits:

| Ref | Evidence |
| --- | --- |
| C1 | [Rewrite dispatch, alias eligibility and returned edits](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/src/native/capture_language/rewrite.rs) — `rewrite_draft`, `expand_sigil_alias`, `finish_sigil_alias` |
| C2 | [Shared close-selection lexer](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/src/native/capture_language/close_selection.rs) — whole-item classification, link suffixes, wildcard and malformed-list rules |
| C3 | [Past-token splitter](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/src/native/capture_language/past.rs) — quote-aware separation of name/timing, repair `!`, second `=`, and close selection |
| C4 | [Editor Pomodoro parser](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/src/native/capture_language/editor_pomodoro.rs) — `parse_editor_close_item`, `parse_editor_past_item`, semantic span ownership |
| C5 | [Completion contexts](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/src/native/capture_language/completion.rs) and [draft/item splitting](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/src/native/capture_language/draft.rs) |
| C6 | [Capture reference](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/docs/capture.md) — closing, past sessions, same-line chains, and `capture-rewrite` |
| C7 | [Rewrite unit tests](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/src/native/capture_language/tests/rewrite.rs), [bare-close compatibility tests](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/src/native/capture_language/tests/bare_close.rs), [rewrite CLI tests](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/tests/cli/capture/rewrite.rs) |
| M1 | [Mac event filtering and native edit application](https://github.com/bobs-org/bob-mac-capture/blob/0583f37aef3241ffc872e11325f8afaec1c5cbcc/Sources/BobMacCapture/CapturePanelController.swift) — `noteSeparatorToggleIntentIfEligible`, `applySeparatorToggleInEditableTextView` |
| M2 | [Rewrite orchestration and submit handling](https://github.com/bobs-org/bob-mac-capture/blob/0583f37aef3241ffc872e11325f8afaec1c5cbcc/Sources/BobMacCapture/CapturePanelModel.swift) — `noteSeparatorToggleIntent`, `editorTextDidChange`, `startCaptureRewrite`, `applyCaptureRewrite`, `submit`, `invalidateRewrite` |
| M3 | [Native rewrite tests](https://github.com/bobs-org/bob-mac-capture/blob/0583f37aef3241ffc872e11325f8afaec1c5cbcc/Tests/BobMacCaptureTests/CaptureSeparatorToggleTests.swift) — Undo, Unicode, IME, and stale response tests |
| M4 | [Existing close-list comma assist](https://github.com/bobs-org/bob-mac-capture/blob/0583f37aef3241ffc872e11325f8afaec1c5cbcc/Sources/CaptureCore/CaptureCloseTaskCommaAssist.swift) and [rewrite response validation](https://github.com/bobs-org/bob-mac-capture/blob/0583f37aef3241ffc872e11325f8afaec1c5cbcc/Sources/CaptureCore/CaptureModels.swift) |
| M5 | [Mac capture behavior documentation](https://github.com/bobs-org/bob-mac-capture/blob/0583f37aef3241ffc872e11325f8afaec1c5cbcc/docs/capture-panel.md) and [build requirements](https://github.com/bobs-org/bob-mac-capture/blob/0583f37aef3241ffc872e11325f8afaec1c5cbcc/AGENTS.md) |

Audited decisions reviewed: `decisions:mac-capture-is-a-thin-client` and `decisions:close-selections-list-explicitly`. These require Bob to own capture grammar and preserve the existing meaning of explicit numeric selections. Neither alias should alter task outcomes, wildcard behavior, event-clock exceptions, or the interpretation of unlisted tasks.

## What the request means, with explicit adjustments

The second bullet's wording says “instead of the second `=`,” but its example retains that delimiter. I recommend following the example: **replace an `x` or `s` inside the close-selection suffix after the second `=`, without inserting or removing either `=`.** `x=1=s` becomes `x=1=*`; `x=1=x` becomes `x=1=!`.

The following are deliberate clarifications or scope adjustments:

1. **Typing assist only.** Trigger on an actual lowercase single-character insertion in the main capture editor. Do not normalize pasted text, restored drafts, templates, completion insertions, Undo/Redo, or CLI input. `!` and `*` remain canonical, portable spellings.
2. **The close selection owns the alias.** Support the initial action slot and subsequent action groups, not just the exact strings `xx` and `xs`. Thus typing `x1s` produces `x1*`, and typing `x!1s` produces `x!1*`.
3. **Retain the second `=` for past sessions.** Do not make `x=1s` mean park, or `x=1x` mean repair/complete. Names and timing precede the second delimiter. The existing `!` before it authorizes trimming a closed session; it is a different operation and receives no new alias.
4. **Cover canonical link-and-close suffixes as well.** I recommend including existing-task `@route:id=x…`, active-task `^route:id=x…`, and new-task link-and-close forms wherever Bob already recognizes them. This extends the examples but follows “contexts where the x capture syntax is respected.” It also introduces a named-start collision described below, so it must be documented explicitly.
5. **Make it independent of typing speed.** No timed `xx` chord, special double-tap escape, or requirement to pause before a task number. A deliberate second `x` is the requested alias whether typed quickly or slowly.
6. **Preserve native editing.** Ignore held-key repeats as alias triggers; preserve selection replacements, modifier shortcuts, marked-text composition, modal fields, and picker query text. Undo restores the literal text before the automatic replacement. Uppercase `X`/`S` are not new aliases.

These are product requirements for the proposed feature, not claims that the feature already exists.

## What exists today

### Bob already provides the correct architectural seam

`rewrite_draft` runs lexical editor assists and returns edits, text, a UTF-8 cursor and a summary. Existing `.`, `;`, `,`, `-`, `/`, `\`, and `=` assists use `expand_sigil_alias`; many construct the canonical candidate and ask Bob's completion grammar whether it owns the location. The endpoint is read-only and requires no vault. Templates are excluded before dispatch. The app records a keystroke intent, lets native insertion happen, then sends the post-key draft to `capture-rewrite`. [C1, C6, M1, M2]

The Mac app does **not** currently forward `x` or `s` through this lane. There are allowlists in both the controller and model. Extending only the Rust helper or only one Swift allowlist would leave the feature incomplete. Returned `expand_sigil_alias` edits already use native single-edit application, so a new wire rule is unnecessary. [M1, M2]

### Close selection is not an ordinary picker context

The shared lexer supports numeric in-progress, park `*`, complete `!`, drop `~`, and explicit in-progress `@` groups. A bare `!` or `*` group is a valid wildcard action, not an unfinished field. In current source, `pomodoro_close_task` is a parser **need** for dangling selections; it is not a `CompletionContext` enum case. An implementation that waits for this need, or copies another alias's “picker must open” test, will miss the requested `xx → x!` and `xs → x*`. [C2, C4, C5]

The past-token splitter already identifies the second equals outside exact-name quotes. Use it; searching for the second `=` byte blindly fails on quoted names containing `=`. The editor parser gives the close delimiter and outcome lists their own spans, separately from past timing, names, segment suffixes, and repair. [C3, C4]

### Read-only probe results

I ran `bob capture-parse --no-ref --format json -- '<text>'` and cursor-specific `capture-rewrite` against the installed grammar-16 executable. Representative results:

| Input | Observed result |
| --- | --- |
| `xx`, `xs` | Ordinary task text; `xx` rewrite is currently a no-op |
| `x!` | `pomodoro_close`, `complete_all: true` |
| `x*` | `pomodoro_close`, `park_all: true` |
| `x1!`, `x1*` | Keep task 1 in progress and apply the wildcard to remaining eligible links |
| `x1x`, `x1s` | Close-shaped input with `invalid_pomodoro_close` diagnostics |
| `x=1=x`, `x=1=s` | Past-shaped input with invalid close-selection diagnostics |
| `x=1=!`, `x=1=*` | One-block past session with complete-all / park-all close outcomes |
| `x=s`, `x=1s` | Valid sessions named `S`, for 25 minutes / 5 minutes respectively |
| `x=1!` | Past session with `repair: true`, no complete-all selection |
| `@foo:bar=xx`, `@foo:bar=xs` | Link and start a session named `XX` / `XS` |
| `@foo:bar=x!`, `@foo:bar=x*` | Link and close with the selected wildcard |
| `x1,!` | Missing-number diagnostic; conversion must not erase it |
| `x!*` | Competing wildcard diagnostic; `x!*1` is a meaningful later continuation |
| `Plan x!` | Ordinary task text |
| `x` followed by a child bullet `- x!` | Close with literal child-log text, not another close |

Current source explicitly retains the prose classification of `xx` and documents the same name/repair distinctions. Its bare-close tests assert that `xx` is not a session-chain token. Preserve those execution tests when adding editor rewrite tests. [C2, C3, C6, C7]

For a limited performance baseline, 30 separate local processes executing the existing no-op `capture-rewrite --cursor 2 --format json -- xx` took median **6.07 ms**, nearest-rank p95 **8.14 ms**, range **5.65–9.42 ms**, including Python subprocess overhead on apollo/Linux. This is neither Mac latency nor a benchmark of the new implementation. It only suggests that the existing process boundary is worth trying before adding a daemon or FFI.

## Critique: useful, with two real costs

The benefit is straightforward: fewer shifted punctuation keystrokes for a frequent close operation, immediate feedback in the existing canonical syntax, and no additional durable syntax for other clients to learn. `x` can suggest completion; `s` is defensible as “suspend” or a shortcut to star/park. Documentation should call the actual outcome **Park**, not “schedule,” because no scheduling semantics are being added.

The first cost is **claiming ordinary letters during incremental typing**. Today `xx` and `xs` are prose. With the requested immediate gesture, typing a word beginning with `xs` can change it before the rest of the word exists. Similarly, a name beginning `xs` after `@foo:bar=` passes through the currently meaningful close prefix `=x`, so the next `s` becomes `*`. No parser can infer the user's intended future characters from that prefix.

That is an unavoidable tradeoff of the exact requested interaction, not something a clever final-string regular expression solves. Keep canonical CLI parsing unchanged; provide ordinary Undo as the literal escape, and document uppercase `X…` for whole-item prose. For a named start that collides in the editor, use an explicit exact-name literal such as `@foo:bar=#"XS"`. The accepted `#"…"` spelling protects name text. No separate persistent preference is necessary initially; reassess if these collisions occur frequently.

The second cost is **asynchronous correctness**. `x!` and `x*` can affect multiple tasks on submission. Although the editor rewrite itself only edits text, a silently skipped alias can mean an ordinary task (`xx`), a named start (`@foo:bar=xs`), or a refusal (`x=1=s`) rather than the intended close. Existing safe rejection of stale responses is essential, but by itself it does not deliver a reliable typing shortcut.

A key finding in M2/M3: ordinary subsequent typing invalidates the pending rewrite, and the response application requires the live draft and caret to match the request. There is a dedicated pending-Return path for the past-segment dash alias, but it is not automatically enabled for all aliases. Simply forwarding `x` and `s` would inherit those limits. Test the new sequence under delayed replies, rather than assuming normal subprocess speed makes the problem disappear.

Apple's guidance supports preserving the native text-input and Undo paths: input contexts distinguish text insertion from marked text and commands, and people expect system-standard reversal of editing actions. This corroborates reusing the existing AppKit path rather than directly replacing the whole editor buffer. [Apple Cocoa Text Architecture](https://developer.apple.com/library/archive/documentation/TextFonts/Conceptual/CocoaTextArchitecture/TextEditing/TextEditing.html), [Apple Undo and Redo guidance](https://developer.apple.com/design/human-interface-guidelines/undo-and-redo)

## Implementation choices

| Approach | Assessment |
| --- | --- |
| Replace `x`/`s` globally or recognize close syntax with a Swift regex | Reject. It changes prose and names and duplicates Bob's grammar. |
| Make aliases part of `bob capture` execution syntax | Reject for this request. Pasted text, scripts and non-Mac clients would acquire new meanings, including current prose and named starts. It is broader than a typing assist. |
| Extend Bob's cursor-aware rewrite plus native Mac event handling | **Preferred.** Reuses the existing contract, parser ownership, canonical outcomes, UTF offsets and Undo behavior. |
| Ask Bob to return speculative next-key edit descriptors with every parse | Plausible future optimization, but adds protocol and cache-state machinery and still needs a fallback when typing outruns parsing. Not the first implementation. |
| Add explicit keyboard shortcuts or delay conversion until a delimiter | Reasonable if the prose collision is unacceptable, but changes the requested interaction. Do not silently substitute it for immediate `xx → x!`. |

### Backend design

Add a dedicated close-outcome branch inside `expand_sigil_alias`, retaining `RewriteRule::ExpandSigilAlias` and the existing response schema. A one-byte ASCII replacement leaves the UTF-8 cursor unchanged and can use `finish_sigil_alias`.

The difficult part is an internal **grammar-owned close-selection location query**, not the mapping table. Reuse the existing draft splitter, close/link classification, past splitter and shared lexer. Determine ownership using the pre-insertion draft (the post-key draft with just the trigger removed), then examine the canonical candidate at the same location. For example, removing the second key from `xx` exposes the existing `x` close; removing `s` from `x=1=s` exposes the empty selection after the second equals. This also helps keep aliases out of new session openers, name text and logs.

Require the inserted byte to be inside, or at the end of, that existing selection token, after its opener. Do not let the alias's *candidate* create a new token boundary or promote arbitrary log prose into another session operator. This matters because canonical `x` tokens can split same-line session chains: a test such as `x log xs` must distinguish an actual pre-key close slot from arbitrary text. Use Bob's classification, not a hand-written approximation of chain splitting. Child Work Log text always remains literal.

Do not require the **entire draft** to be error-free. An unrelated item may be incomplete, and a valid editing trajectory can pass through a temporary error: `x!` plus `s` gives `x!*`, then `1` gives `x!*1`. Once the location is unequivocally a close-selection token, mapping the typed alias to its punctuation should leave the existing lexer to diagnose duplicate groups, competing wildcards, missing indices and other errors. Do not “repair” those errors, reinterpret an invalid list as a different action, or weaken canonical execution checks. The location helper must therefore expose structural ownership even when the selection itself has diagnostics. Checking only `ok`, a top-level mode, or the existence of any close span is insufficient.

For an initial implementation, require the key to be at the selection-token end in its event snapshot; insertion before existing token content can remain literal. This is a deliberate conservative boundary consistent with several existing assists, not a reason to lose later typing from the same gesture. Batches and same-line chains should work at any eligible item, not just at byte zero.

### Mac design and the typing race

Add lowercase characters to both existing intent allowlists, retaining character-based detection, normal modifier checks, a collapsed selection, main-editor focus, and the marked-text guard. Also exclude repeat events for these two triggers. Do not add a Swift implementation of close grammar. Keep Bob's returned edits, validation and native `NSTextView` application; do not set the entire draft as the primary rewrite mechanism. [M1–M4]

For fast typing, introduce a small, explicit pending-letter-rewrite transaction rather than relaxing the general stale-response guard:

- Record the exact post-key snapshot, insertion location and editor generation.
- Preserve ordinary forward insertions after that caret while the request is outstanding. Track those events; do not infer provenance merely because two arbitrary strings share a prefix.
- When Bob approves the one-byte edit, rebase only that edit through the recorded, disjoint insertions and preserve the current caret. Additional alias events must be replayed in order against the updated text through Bob, so `x1s2x3` does not depend on reply timing.
- Edits overlapping the target, caret relocation, selection changes, Undo/Redo, paste, composition, dismissal and process-client replacement cancel the transaction. Never replay into a different editing generation or a dismissed/restored buffer.
- Return during a pending alias must wait for normalization and current parse/preview, then submit at most once from the resulting visible draft. Generalize the existing dash-specific deferred-submit mechanism for this purpose. A failed request must cancel that queued submission and leave editable text; it must not silently send the unresolved alias draft.

This is more work than the mapping, but it is bounded editor event bookkeeping, not another grammar. Validate the transaction independently with fake-Bob delays and malformed replies. If the team chooses a smaller first patch that simply drops the alias when further typing arrives, document that limitation explicitly; I would not consider it a satisfactory implementation of a fast close shortcut.

Because `x` and especially `s` occur often, avoid turning every ordinary letter into a visibly stalled parse/completion interaction. Measure the rewrite lane on the Mac. Backend-owned cached context can eliminate requests when it conclusively rules out an alias; any client prefilter must remain an optimization that cannot change semantics or exclude valid chain/link contexts. Start with the existing subprocess transport; no evidence here justifies a daemon.

### Compatibility and presentation

No execution-language revision or new mandatory response field is inherently needed for the basic rewrite. Old apps will not trigger the new keys; old Bob binaries will return no change. However, do not advertise that as fully safe semantic fallback: the probe table shows that literal `xx` can become a task and `=xs` can start a named session.

If rollout must tolerate old Bob, a read-only capability probe on process resolution is inexpensive: test known alias inputs such as `xx` and `xs` with their cursor and verify the expected canonical edits. Cache by process-client identity and clear on re-resolution. This uses the existing lexical endpoint and avoids guessing from an unrelated grammar revision. Unsupported installations should clearly present aliases as unavailable and retain canonical punctuation. A supported probe does not replace request-failure handling or contextual validation.

Keep the existing preview and outcome labels. Do not add a modal confirmation just for an alias. Announce the rewrite using the normal summary channel and show `!` or `*` in the draft. Do not add hash/relation-style double-tap behavior to these keys; it would compete with the requested `xx` gesture.

## Acceptance cases and verification

These are proposed expectations for **key events**, not bulk search-and-replace instructions. Where several aliases occur, the examples describe successive key insertions with previous approved replacements applied.

| Event context / sequence | Expected behavior |
| --- | --- |
| `x` + `x` / `s` | `x!` / `x*` |
| `x1` + `x` / `s` | `x1!` / `x1*` |
| `x!1` + `s`, or `x*1` + `x` | `x!1*` / `x*1!` |
| `x=1=` + `s` / `x` | `x=1=*` / `x=1=!` |
| `x==` + `s` | `x==*` for default-duration past work |
| `x=1~2!=` + `x` | `x=1~2!=!`; repair and close outcomes stay separate |
| `x=#"DEEP WORK"=` + `s` | Name unchanged; close suffix becomes `=*` |
| `@foo:bar=x` + `x` / `s`; equivalent active/new-task forms | Canonical link-and-close suffix `=x!` / `=x*` |
| Eligible later item in a batch or session chain | Same local edit; every other byte preserved |
| `x=s`, `x=1s`, `x=fix`, `x=#"XS"` | No alias in name/timing components |
| `Plan xs`, task IDs containing `s`/`x`, `s:2`, relations, URLs, quoted names, inline code | Literal text |
| Child logs, templates, picker queries, modal fields, composition | Literal text |
| Initial `x`, uppercase `X`/`S`, Command-X / Command-S, held repeats | No new alias action |
| `x!` + `s` | `x!*` with existing competing-wildcard diagnostic; later `1` can resolve it |
| `x1,` + `x`, or an already-used group marker + its alias | Preserve canonical malformed-selection diagnostics; never silently drop a comma or duplicate group |
| No cursor supplied to rewrite, or pasted/restored `xx` | No letter-alias normalization |
| Immediate Undo after `xx → x!` | Restore `xx`; Redo restores `x!`; neither retriggers the assist |

Backend tests belong beside C7 and should assert rule, one-byte range, resulting text, cursor, idempotence, UTF-8 boundaries, CRLF, batch offsets, and no changes to canonical parser/execution behavior. Include exact-name literals containing `=` so the second-delimiter logic is proved. Check errors by location and kind, not only `ok: true`, since editor parsing can succeed while reporting diagnostic errors.

Mac tests should use a deliberately delayed fake Bob and exercise `xx1`, `xs12`, `x=1=s3`, `x1s2x3`, immediate Return and modified Return, repeated Return, failure/no-op replies, Undo/Redo, selection movement, process replacement and dismissal. Include an emoji before a later item to verify UTF-8/UTF-16 conversion. Test interaction with the existing automatic comma helper: after normalization, number entry should behave exactly as it does after directly typed `!` or `*`, including the lineup-size rule for multi-digit indices. [M3, M4]

The future implementation must compile and test the affected Swift targets. Run portable checks for portable code, the linked repo's macOS gate for AppKit changes, documentation checks for edited docs, and watch the exact pushed SHA's macOS CI as required by M5. Portable tests alone do not type-check the native panel/controller. This research did not run those implementation gates because it made no product changes.

Update `docs/capture.md`'s rewrite section and the Mac keyboard/panel documentation. Explicitly qualify the existing statement that `xx` is prose: it remains true for raw execution input, while the new typed gesture canonicalizes it in the editor. Include the past-session delimiter rule and the named-start collision, rather than showing only the happy-path examples.

## Recommended solution

Proceed with both aliases. Keep them lowercase, immediate, typing-only and restricted to Bob-recognized close selections, including canonical link-close suffixes and the portion after a past session's second `=`. Preserve `x=s`, `x=1s`, quoted names, repair `!`, logs and pasted text. Implement the semantic location query and one-byte edit in `capture-rewrite`, reuse native AppKit editing, and make fast follow-on typing and Return reliable before shipping.

The one meaningful usability concession is that typing literal `xx`/`xs` at an eligible close prefix now needs Undo or an explicit prose/name escape. Accept that openly if these are rare inputs. If preserving those prefixes without any escape is more important, choose explicit shortcuts instead; immediate automatic conversion cannot promise both behaviors. With that tradeoff stated and the asynchronous tests passing, this is a worthwhile extension of the existing capture interaction, without expanding the durable capture language.
