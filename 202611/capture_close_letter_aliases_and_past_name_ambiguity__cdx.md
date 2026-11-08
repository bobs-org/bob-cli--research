# Close-letter shortcuts in Bob Capture: useful, with explicit name boundaries

Independent research by **cdx**, 2026-11-08. No other report or researcher findings from this swarm were consulted. This is research and a proposed behavioral contract; no product code was changed.

**Recommendation:** add lowercase `x` → `!` and `s` → `*` through Bob's existing editor rewrite interface. Preserve the requested `xx` → `x!` and `x=1s` → `x=1=*`, but explicitly reserve the latter numeric-prefix spelling and protect ordinary session names. Broadly replacing letters wherever a substituted command would parse would break normal names. Treat fast typing and Return as acceptance criteria, not later polish.

## What exists today

I inspected bob-cli at `51d572d59075cc1b9363051ec453b4d3ee3e1ed4` and bob-mac-capture at `0583f37aef3241ffc872e11325f8afaec1c5cbcc`. Local, read-only probes used the installed `bob 0.4.0`, whose parse responses reported grammar 16. I did not establish that installed binary's exact build SHA; source inspection and runtime observations are separate evidence. No capture execution or vault mutation was performed, and no Swift compilation or Mac interaction was performed.

**The architectural path already exists.** `capture_language::rewrite_draft` produces a canonical draft, byte edits, cursor, rule, and summary. `bob capture-rewrite` exposes that result. The app records a native key gesture, asks Bob, checks the response against the current draft and caret, and applies a native text replacement. Grammar belongs in Rust; Swift owns the interaction. Existing aliases are typing assistance, not alternate input accepted by `bob capture` or `capture-parse`. This matches the audited `decisions:mac-capture-is-a-thin-client` and `decisions:relation-equals-alias-and-flips` records. [Rust rewrite implementation](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/src/native/capture_language/rewrite.rs#L78), [Mac key handling](https://github.com/bobs-org/bob-mac-capture/blob/0583f37aef3241ffc872e11325f8afaec1c5cbcc/Sources/BobMacCapture/CapturePanelController.swift#L1108).

**The canonical meanings must remain distinct.** Whole-item `x!` closes with completion of the remaining eligible numbered Task Links; `x*` closes with parking. Numeric lists select explicit tasks. In `x=E[s][!][=X]`, the first portion describes past-session timing/name, a pre-close `!` permits closed-edge repair, and the second `=` begins task outcomes. The `s` in this documentation schematic is a metavariable for a segment suffix such as `~2`, not an existing literal `s` operator. Consequently `x=1x` must expand to `x=1=!`, never `x=1!`: the latter requests history repair. Existing Event Task and selection rules still govern what a wildcard actually affects. [Close contract](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/docs/capture.md#L4943), [past-session contract](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/docs/capture.md#L5380).

**The important collision is real, not hypothetical.** These were observed with `bob capture-parse --format json -- '<input>'`:

| Input today | Observed interpretation |
| --- | --- |
| `xx`, `xs` | Ordinary task text |
| `x=1s` | Past session named `S`, one block/five minutes |
| `x=s` | Past session named `S`, five blocks/25 minutes |
| `x=fix` | Past session named `FIX` |
| `x=fix2s` | Past session named `FIX2S`, default duration |
| `x=2sync`, `x=2xmas` | Named past sessions, two blocks |
| `x=1x` | Error teaching the literal name spelling `x=1#x` |
| `x=1=*` | Past session with `park_all: true` |
| `x=1=!` | Past session with `complete_all: true`, no repair |
| `x=1!=!` | Past session with repair and complete-all |
| `x=1=x`, `x=1=s` | Invalid close task lists |
| `x=sync1` | Past session named `SYNC`, one block |
| `x=1#sync` | Retired redundant-hash spelling; suggests `x=1sync` |
| `x=1#"S"` | Valid exact name `S`, one block |
| `@dev:foo=xs` | Link with session name `xs`, not a close |

`bob capture-rewrite --cursor 4 --format json -- 'x=1s'` currently returns `changed:false`, as expected. These probes corroborate the shared bare-name and past-token lexers. [Bare names](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/src/native/capture_language/bare_name.rs#L28), [past-token splitting](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/src/native/capture_language/past.rs#L45).

A test that merely replaces the last character and accepts a valid result is insufficient. Typing the final `x` of `x=fix` would produce the equally valid `x=fi=!`; typing the final `s` of `x=bugs` would produce `x=bug=*`. Even detecting a preceding digit is insufficient: `x=fix2s` is an existing valid name.

## Is this a good idea?

For an expert user's frequent close operations, yes. `xx` is easy to repeat, and both letters avoid a shifted punctuation key on common US keyboard layouts. `s` can stand for “star,” though it is less mnemonic for the actual park action. The benefit is ergonomic more than a dramatic reduction in character count: `xx` and `x!` each use two characters, whereas `x=1s` also saves the second `=`.

Letters are substantially more invasive than punctuation aliases. They occur in names and prose; aliases for wildcard completion and parking also have greater consequences than opening a picker. Visible canonical expansion, the existing preview, ordinary explicit submission, and reliable Undo are sufficient safeguards here. I would not add a confirmation dialog to every use, a timing-dependent double-tap language, or another modal shortcut card.

There is an unavoidable tradeoff in the exact requirement: at the moment `s` arrives in `x=1s`, the editor cannot know whether the user intends the shortcut or is beginning `x=1sync`. Immediate expansion and completely unrestricted count-first names cannot both be preserved. Waiting for Space/Return changes the requested interaction; waiting for a typing pause makes the result depend on typing speed. The product must choose a reservation rule and document it.

## Proposed requirements, including adjustments

**A1 — Typed-only, lowercase, reversible.** Trigger only on a single physical/editor typing gesture for lowercase `x` or `s` in the main capture editor, with a collapsed selection and no active marked-text composition. Do not normalize pasted text, draft restoration, completion insertion, programmatic edits, Undo/Redo, or all CLI input. Do not add uppercase aliases. Do not treat key-repeat as a second deliberate alias gesture. Canonical punctuation remains available everywhere it works today.

The typed-versus-pasted distinction is intentional: a pasted `x=1s` retains its current name meaning. Explain this in shortcut documentation rather than silently changing the parser to hide the distinction. Native Undo should restore the literal post-key draft once, without immediately triggering the alias again. Backspace can retain ordinary editor behavior; it need not act as a special expansion undo.

**A2 — Start with whole-item close commands and whole-item past commands.** Include standalone items, supported bulk-item positions, and contiguous session chains recognized by Bob. Exclude task titles, route/block IDs, wikilinks, template content, modal fields, and Work Log text. Do not infer eligibility from the entire draft's top-level mode: the caret must belong to the actual operator token.

**Scope adjustment:** do not initially expand inside link suffixes such as `@dev:foo=xs`, or after log text merely because rewriting a trailing word could create another operator. Those forms need their own explicit interaction decision. Link suffixes currently accept names such as `xs` and `xx`; this is not a harmless extension of the whole-item rule.

**A3 — Normal close selections use punctuation only.** Inside an eligible `x` close token, replace the typed character with `!` or `*`. Support later groups as well as the first group: `x1s` → `x1*`, and `x!1s` → `x!1*`. Existing task lists, zero, selection conflicts, and wildcard behavior remain authoritative.

Do not require the substituted token to be executable at every keystroke. For example, typing `xsx2` should pass through `x*`, then `x*!`, then `x*!2`. The middle spelling has competing wildcard groups until the task number arrives; Bob should show its ordinary diagnostic. A context helper should recognize an allowable next operator, including this recoverable editing state. It should not repair a dangling comma (`x1,s`) or silently reinterpret an already malformed list. Duplicate operators can remain literal/errors rather than introducing another group.

**A4 — Insert the second `=` only at selected past-session boundaries.** Before the second `=`, expand to `=!` / `=*` when the prefix is:

- A valid, positive, **unnamed numeric duration**, such as `x=1`.
- A valid past expression ended by an explicit segment suffix, such as `x=fix~2` or `x=2~~`.
- A valid past expression ended by its repair `!`, such as `x=fix!`.
- A valid past expression ended by a closed exact-name quote, such as `x=1#"FIX"`.

Do not expand immediately after bare `x=` or while extending an unquoted name, including after a trailing count attached to that name. Thus `x=s`, `x=xmas`, `x=fix`, `x=bugs`, `x=fix2s`, and unquoted `#name` content stay literal. A repair `!` must stay before the inserted second `=`.

**Material requirement adjustment:** this intentionally narrows “where `x=` is supported.” It preserves the requested `x=1s` example while avoiding broad name corruption. It still reserves lowercase `x` and `s` as the first letter after a bare numeric duration during typing. For a count-first name such as `x=2sync`, type name-first `x=sync2`, or an exact quoted name such as `x=2#"SYNC"`. Plain `x=2#sync` is not a valid general escape under today's grammar. Undo is also available.

For a bare named session, keep the explicit second equals: type `x=fix=s` or `x=fix=x`. This adds one deliberate boundary and protects every letter of the name. Do not try to infer that a name is finished from a catalog match: unknown names are valid, known names can be prefixes of longer names, and catalog-dependent rewriting would be unpredictable.

**A5 — Once the second `=` exists, never insert another.** In the past close-selection portion, the aliases are again just `!` and `*`. This is a small, justified extension for consistency and supplies the safe named-session spelling above. For example, `x=1=s` → `x=1=*`, and `x=fix=x` → `x=fix=!`.

| Gesture/input at the typing point | Proposed visible result |
| --- | --- |
| `xx` | `x!` |
| `xs` | `x*` |
| `x1s` | `x1*` |
| `x!1s` | `x!1*` |
| `xsx2`, typed as a sequence | `x*!2` |
| `x=1x` | `x=1=!` |
| `x=1s` | `x=1=*` |
| `x=1!x` | `x=1!=!` |
| `x=2~1s` | `x=2~1=*` |
| `x=1#"FIX"s` | `x=1#"FIX"=*` |
| `x=fix=x` | `x=fix=!` |
| `x=fix`, `x=bugs`, `x=fix2s` | Unchanged name text |
| `x=s`, `x=xmas` | Unchanged name text |
| `x=0s`, `x1,s` | No alias; existing diagnostic behavior |
| `@dev:foo=xs`, log text containing `xs` | Unchanged |

**A6 — Timing must not alter meaning.** `xx1`, `xs1`, `xsx2`, and `x=1s2` typed quickly must have the same canonical results as slow typing. Return immediately after an alias must wait for the rewrite and analysis/preview of its result. A rewrite timeout/error must cancel that queued Return, leaving the draft visible for recovery; it must not submit the unintended literal draft. Ordinary unrelated edits, caret movement, Undo, paste, panel dismissal, or a Bob executable change invalidate the pending gesture safely.

## Implementation assessment

**Rust: extend the existing lexical rewrite lane.** A dedicated close-letter helper under `capture_language/rewrite.rs` is appropriate. Reuse `split_past_token`, `validate_past_e`, `classify_whole_item_close`, the close-selection lexer, exact-name handling, and Bob's item/chain model. Factor a small shared “can append this close group here” predicate if needed for recoverable states; do not build an unrelated regex grammar in Rust or Swift.

Determine the pre-trigger token's ownership and name state before trying a canonical candidate. For `xx`, inspect the prefix `x`; the raw `xx` currently parses as prose. For past expressions, split timing/name/repair from close selection and enforce A4. Reparse the candidate sufficiently to verify operator ownership and source ranges, but do not demand that every other unfinished item in the draft be valid. Same-line chains require attention because the unreplaced alias can temporarily prevent the original draft from splitting into session items. Work Log text must not become a new command solely because the candidate is valid.

Return the existing `expand_sigil_alias` rule, with one byte-range replacement. For `x=1s` at UTF-8 cursor 4, the edit is `[3,4)` → `=*`, the result is `x=1=*`, and cursor is 5. The existing `finish_sigil_alias` takes a `char` and preserves cursor length; do not use it unchanged for this two-character insertion. Generalize its replacement/cursor calculation or use a separate constructor. One-byte-to-two-byte rewrites already have precedent in comma continuation handling. Preserve idempotence and the existing no-cursor behavior. [Rewrite helpers](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/src/native/capture_language/rewrite.rs#L745), [close lexer](https://github.com/bobs-org/bob-cli/blob/51d572d59075cc1b9363051ec453b4d3ee3e1ed4/src/native/capture_language/close_selection.rs#L106).

**Mac: two trigger allowlists and the asynchronous interaction need work.** Both `CapturePanelController.noteSeparatorToggleIntentIfEligible` and `CapturePanelModel.noteSeparatorToggleIntent` currently enumerate punctuation triggers; add the new letters in both places. Keep semantic eligibility in Bob. Existing `CaptureRewriteResponse.coveringEdit`, UTF-8/UTF-16 conversion, and `applyNativeSingleEditRewrite` can apply variable-length edits without a new response shape. The controller already breaks undo coalescing and inserts the returned replacement through the native editor. Apple's text-input API distinguishes marked composition from committed insertion; preserving the existing marked-text guard is appropriate here. [Model trigger recording](https://github.com/bobs-org/bob-mac-capture/blob/0583f37aef3241ffc872e11325f8afaec1c5cbcc/Sources/BobMacCapture/CapturePanelModel.swift#L2617), [native replacement](https://github.com/bobs-org/bob-mac-capture/blob/0583f37aef3241ffc872e11325f8afaec1c5cbcc/Sources/BobMacCapture/CapturePanelController.swift#L1202), [Apple NSTextInputClient](https://developer.apple.com/documentation/appkit/nstextinputclient).

The harder work is preserving an alias gesture across subsequent typing. Current `applyCaptureRewrite` checks exact input/draft/generation and rejects a response after a newer edit. That is correct stale-response protection, but merely adding letters to the allowlists can lose a shortcut when a digit arrives first. The existing deferred submission path is specifically armed for a past-segment dash; it is not a generic guarantee for these letters. [Response guards](https://github.com/bobs-org/bob-mac-capture/blob/0583f37aef3241ffc872e11325f8afaec1c5cbcc/Sources/BobMacCapture/CapturePanelModel.swift#L16301), [rewrite launch](https://github.com/bobs-org/bob-mac-capture/blob/0583f37aef3241ffc872e11325f8afaec1c5cbcc/Sources/BobMacCapture/CapturePanelModel.swift#L15846), [deferred Return](https://github.com/bobs-org/bob-mac-capture/blob/0583f37aef3241ffc872e11325f8afaec1c5cbcc/Sources/BobMacCapture/CapturePanelModel.swift#L3181).

I recommend a small ordered pending-gesture mechanism: retain the exact trigger snapshot and record subsequent contiguous insertions. Resolve Bob's decision for that snapshot; if the only subsequent edits are those recorded insertions after the trigger, carry the returned edit forward with verified ranges and replay subsequent gestures in order. This is editor bookkeeping, not Swift grammar. A second alias must be resolved against the canonical result of the first. Cancel on any unrecognized edit instead of removing the existing stale-response checks. Generalize the pending-Return path to this mechanism. The exact integration needs native tests; this research does not claim that appending characters to an old returned string is sufficient.

Letters also generate more potential rewrite calls than punctuation. Begin with the existing process lane and measure on the Mac. Do not add Swift name recognition as a performance shortcut. If the additional calls are materially expensive, expose Bob-authored eligibility information for a matching draft/caret, or combine parsing and rewrite discovery in Bob. Avoid a daemon or general editor-protocol redesign for this feature without measurements.

**Compatibility and rollout:** the existing edit response can represent the entire change; a breaking schema/grammar revision is not intrinsically needed for the rewrite itself. Release Bob support before advertising the app feature. Older apps will not send letter-trigger requests. A new app with an older Bob will receive no rewrite, and those literals can mean ordinary text or a named session. Establish support during Bob resolution, using additive capability metadata or a harmless lexical probe such as `capture-rewrite` on `xx`; expose shortcut availability accordingly. Do not silently treat an unsupported backend as proof that the requested alias was applied. No version bump, release file edit, or push is part of this research task.

## Verification that would make this implementation reviewable

1. **Rust rewrite tests:** all rows in the proposed table; no cursor; invalid and mid-codepoint cursors; multiple items and same-line chains; Unicode and CRLF before the edited token; quoted names including internal `=`/`!`; unquoted names; raw `xx`/`xs` parser compatibility; template and Work Log exclusion; recoverable `x*!` progression; unchanged results on a second rewrite.
2. **CLI JSON tests:** exact edit `[3,4)` → `=*`, cursor 5, existing rule string, and parse of canonical output. Prove `x=1x` sets close completion without setting `repair`; prove `x=1!x` preserves repair. Verify ordinary `capture-parse` still treats literal `x=1s` as a name.
3. **Mac integration tests with delayed fake Bob:** immediate and delayed replies for `xx1`, `xs1`, `xsx2`, `x=1s2`; several response orders; fast Return exactly once after canonical analysis; timeout/error; no-change on an ordinary word; edits/caret move while pending; no lost suffix or caret jump; Undo/Redo without retrigger; paste/restore/IME/modal/selection exclusions; unavailable backend support. Test typing the prefixes of `x=sync2`, `x=xmas2`, `x=fix`, and `x=bugs`, not merely loading their final strings.
4. **Native validation:** reuse the existing separator-toggle and response fixtures, run portable checks where supported, and compile/type-check changed macOS targets as the linked repository requires. Its macOS CI must pass for the exact implementation SHA before landing. This report has not run those implementation checks.

The relevant existing suites are `src/native/capture_language/tests/rewrite.rs`, `src/native/capture_rewrite.rs`'s JSON tests, `Tests/BobMacCaptureTests/CaptureSeparatorToggleTests.swift`, and `Tests/CaptureCoreTests/CaptureRewriteResponseTests.swift`. No new end-to-end vault-mutation suite is necessary merely to retest unchanged close semantics; the meaningful new coverage concerns rewrite eligibility, canonical output, and event ordering.

## Alternatives and final recommendation

| Approach | Assessment |
| --- | --- |
| Replace any final `x`/`s` after `x=` when the replacement parses | Reject: corrupts ordinary `fix`, `bugs`, and digit-containing names. |
| Accept letters directly in execution grammar | Reject for this request: changes scripts, pasted input, and existing names; departs from existing editor-only aliases. |
| Delay until Space/Return | Viable if preserving every count-first name matters more than immediate expansion; changes the requested interaction and still needs a decision for literal `x=1s`. |
| Only allow aliases after an explicit second `=` | Safest simplified alternative: `x=1=s` → `x=1=*`; gives up the user's exact `x=1s` example. |
| Keep punctuation only or add modifier chords | Lowest grammar complexity, but loses the requested ergonomic benefit. |
| Immediate, narrowly scoped aliases with explicit name boundaries | Best fit for the request, provided the numeric-prefix reservation and timing work are accepted. |

**Recommended solution:** implement A1–A6 as a Bob-owned editor rewrite plus coordinated Mac gesture handling. Keep `xx`/`xs`, reserve `x=<positive-number>x/s` during typing, preserve unquoted names, and offer explicit `=x`/`=s` after a named past session. Reuse the existing rewrite JSON and native Undo path, and make fast typing and Return deterministic before shipping. If reserving count-first names is unacceptable, choose the explicit-second-equals alternative instead; do not disguise the ambiguity with timing or a permissive replacement regex.
