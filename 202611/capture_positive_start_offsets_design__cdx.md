# Positive start offsets in Capture: a compact shift, with explicit boundaries

Independent research by **cdx**, 2026-11-07. No other swarm researcher's report, findings, or transcript was consulted. This is design research, not an implementation or an approval request.

**Recommendation:** add a terminal `+[N]` modifier to whole-item starts and task/link starts. Read it as **“perform this start, then move its session N five-minute blocks later, preserving its duration.”** Default N to 1. Resolve the ordinary start first, including its selection, swap, and calendar behavior, then shift that same session inside the existing transaction and present one final result. Do not add positive offsets to `x=` in this release.

This is a useful shortcut, particularly for link-and-start captures. It is also a real grammar change: `+` already belongs to names, and some requested spellings currently mean something else. The quality of the feature depends more on resolving those collisions and preserving start semantics than on the addition itself.

## 1. Evidence and method

I inspected these source revisions locally through the authorized repository workflow:

| Repository | Revision | Relevant evidence |
| --- | --- | --- |
| bob-cli | `b73ac383c239a1f058742050f84b70c94e6c5732` | Capture grammar, lexer, completion, planner, timeline, documentation, tests |
| bob-mac-capture | `c2b7db24f188285085babb13570ae11f825ae197` | JSON decoding and start-preview presentation |
| bob-plugins | `2563c7898644d1f784c13f3eefa698285ae4a381` | Existing `se<X>` snippet grammar and calendar parity |

I also ran read-only `capture-parse` probes and isolated `capture --dry-run` probes against temporary fixture vaults under the workspace. The available executable reported **bob 0.4.0, capture grammar 16**; the source checkout's Cargo version is 0.5.0. Thus runtime results corroborate existing behavior but are not a claim that I built or tested the exact source revision. All temporary fixture directories were removed. No personal vault writes or source changes were made.

The design rationale also uses Nielsen's primary account of usability heuristics: consistent meanings, visible feedback, error prevention, and concise contextual help. These support exposing the resolved time and preserving established behavior; they do not empirically establish that this particular syntax is best. That judgment remains an inference from Bob's grammar and the user's requested workflow. [Nielsen Norman Group](https://www.nngroup.com/articles/ten-usability-heuristics/)

## 2. What the current system actually does

### Starts and shifts are different operations

The existing start timing has unsigned duration units and unsigned **backward** offset units. A unit is five minutes. Ordinary explicit timing computes:

```text
base_start = ceil((local_hour_and_minute − 5 × backward_units) / 5) × 5
base_end   = base_start + 5 × duration_units
```

The calculation uses the hour and minute; seconds do not change an exact five-minute boundary. Missing duration defaults to five units. Old spellings accept zero and leading zeros. The final HHMM representation wraps modulo 24 hours. This logic lives in `parse_pomodoro_start_suffix`, `start_block_minute`, and `compute_pomodoro_start_range`. [Parser](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/src/native/capture_language/tokens.rs#L1609), [clock calculation](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/src/native/capture/meet_event_run.rs#L199), [range rendering](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/src/native/capture/pomodoro_start.rs#L16)

Standalone `+N` changes duration; `++N` shifts both endpoints and preserves duration. The latter finds an open timed entry, including one whose start is in the future, and preserves its clock metadata. A positive suffix should therefore mean **shift later**, not “add duration,” “shorten from the front,” “schedule a callback,” or “create a break entry.” [Shift planner](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/src/native/capture/pomodoro_adjust.rs#L505)

### A bare named start does not always mean 25 minutes from now

When another session is running, `=fix` swaps FIX into that session's existing span. Adding an explicit duration, such as `=5fix`, instead supplies fresh timing. A named start that names the already-running session without timing currently refuses. Separately, an empty-timing MEET start can take its event run's calendar span; unnamed starts can select a MEET overlapping the base start block. These distinctions currently depend in part on `spec.raw.is_empty()`. [Swap implementation](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/src/native/capture/pomodoro_start.rs#L1504), [calendar rule](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/src/native/capture/meet_event_run.rs#L690), [start contract](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/docs/capture.md#starting-the-next-pomodoro)

At a controlled 09:42 clock, the current two-operation forms produced:

| Fixture and input | Final session |
| --- | --- |
| FIX placeholder; `=fix2 ++` | FIX 09:50–10:00, 10 minutes |
| Existing FIX task; `@foo:bar=` then blank line then `++3` | FIX 10:00–10:25, 25 minutes |
| BUILD running 09:00–09:50; `=fix ++` | FIX 09:05–09:55, 50 minutes; BUILD demoted |
| Same running BUILD; `=5fix ++` | FIX 09:50–10:15, 25 minutes; BUILD demoted |
| FIX placeholder; `=fix2-1 ++3` | FIX 09:55–10:05, 10 minutes |

These are strong reasons to define the new feature against the resolved ordinary start, rather than unconditionally calculate `ceil(now/5)*5 + 5N`.

### The link example needs a small correction

**Today, `@foo:bar= ++3` is not a same-line link/start-and-shift chain.** Same-line chaining is for session operator tokens, and excludes task/link forms. The editor parsed that example as `pomodoro_task`, with `++3` as task text. Against an existing `^bar` fixture, execution refused because the block ID already existed. The blank-line form parsed and executed as a link/start followed by a shift:

```text
@foo:bar=

++3
```

Therefore `@foo:bar=+3` should deliver the *intended* equivalence to that two-item draft. Expanding general link/task chaining is a different feature and is unnecessary here. This also makes the compact suffix more valuable than a mere one-character saving. [Chain contract](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/docs/capture.md#chaining-session-operators-on-one-line)

### Plus already belongs to names

The selector character set includes `+`, and bare-name parsing removes trailing digits only after scanning the name. Current `capture-parse` observations:

| Input | Current interpretation |
| --- | --- |
| `=fix2+` | Name `fix2+`, default duration |
| `=fix2+3` | Name `fix2+`, duration 3 units |
| `=fix+3` | Name `fix+`, duration 3 units |
| `=+3` | Ordinary task text |
| `=fix+read2` | Composite name `fix+read`, duration 2 units |
| `=c++` | Name `c++`, default duration |
| `=c++2` | Name `c++`, duration 2 units |
| `x=fix2+` | Past-session name `FIX2+`, default duration |

Thus extending only the numeric parser cannot implement the request. The name lexer consumes the crucial bytes first. There is even a documentation discrepancy: the chain section calls `=bugs+2` a start of the name `BUGS+2`, whereas the inspected trailing-digit lexer and installed editor parser treat its final `2` as duration. Implementation should fix that example while documenting the new rule, rather than use it as evidence that the old grammar was unambiguous. [Selector bytes](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/src/native/capture_language/tokens.rs#L559), [bare-name lexer](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/src/native/capture_language/bare_name.rs), [existing C++ coverage](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/src/native/capture_language/tests/editor_modes.rs#L1118)

## 3. Proposed user contract

### One terminal modifier, applied to a complete start

Teach this sentence:

> Append `+` to move the session five minutes later. Append `+3` for fifteen minutes. Its duration stays the same.

Conceptually, the grammar is:

```text
start-with-shift = existing-start-core [ + positive-ASCII-integer? ] [ ~drop-list ]
```

The optional `~drop-list` remains restricted to whole-item starts and remains last. “Existing start core” includes its existing name and timing spellings. Parse quotes before recognizing operators. Whitespace still separates capture items/operators according to the existing rules.

Recommended spellings:

| Input | Interpretation |
| --- | --- |
| `=+` | Resolve `=`, then shift its session +5 minutes |
| `=+3` | Resolve `=`, then shift +15 minutes |
| `=fix2+` | Resolve `=fix2`, then shift +5 minutes |
| `=fix2+3` | Resolve `=fix2`, then shift +15 minutes |
| `=2fix+3` | Same duration/name and shift as the previous row |
| `=fix+` | Resolve `=fix`, including a kept-span swap, then shift +5 minutes |
| `@foo:bar=+3` | Link/start using existing rules, then shift that session +15 minutes |
| `@foo:bar=fix2+` | The existing named link start plus a +5-minute shift |
| `Do work @foo:bar=2+` | Existing new-task-and-start behavior, with the start shifted +5 minutes |
| `^foo:bar=+3` | Same modifier through the already-supported active-task spelling |
| `=2#"DEEP WORK"+3` | Exact named start for 10 minutes, shifted +15 minutes |
| `=#"C++"+3` | Exact C++ start, shifted +15 minutes |
| `=fix2+3~2,4` | Start FIX without links 2 and 4, shifted +15 minutes |
| `=fix2-1+3` | Existing 5-minute backdate, then +15-minute shift; net +10 minutes |

**Placement decision:** the new modifier terminates the complete start core, before the existing drop list. It is not another duration slot. In particular, prefer `=2fix+3` and `=2#"DEEP WORK"+3`; do not introduce `=2+3fix` or `=2+3#"DEEP WORK"` as alternative spellings in v1. Give a reorder hint if those are typed. This makes “append plus” true for both existing leading-duration and trailing-duration spellings, including exact names.

The exact-name suffix is a deliberate extension: duration still goes before a hash/exact name, while this new shift goes after the complete start. The distinction is structural, not a special case for quote characters.

Allow an existing backward offset followed by one new positive modifier. This follows the user's “add to the start” requirement and provides a direct equivalence oracle. Do not allow a general arithmetic expression, repeated shift suffixes, decimals, units such as `m`, or an extra sign in N.

N must be a positive ASCII integer. Bare `+` means 1; `+03` means 3; `+0` and `+000` are errors. Preserve old zero-duration and backward-zero behavior rather than changing it incidentally. Check parsing, multiplication by five, and time addition for overflow before any write. No new arbitrary product cap is needed for this shortcut.

### Define equivalence precisely

For a valid ordinary base start B resolving to target P and span `[S,E)`:

```text
B+[N] resolves to the same P and [S + 5N, E + 5N)
```

Equivalence means the final session, links, task effects, duration, clock kind, and ledger placement agree with B followed by the existing standalone `++N`, from the same snapshot and clock. The compact version produces **one result**, with its final time, rather than two result cards. Warnings should describe the final operation and should not duplicate intermediate preview messages.

An attached suffix does not change target selection, convert a failed base start into success, or silently reset an inherited duration. Thus `=fix+` still refuses if `=fix` names the already-running FIX. Use standalone `++`, or an explicit restart such as `=5fix+`, for those different intentions. A link/start keeps its current refusal to overwrite an existing running session.

For calendar-derived MEET starts, resolve the same base event run first and then shift its span. Preserve event-task times and the clock classification; the modifier changes the Pomodoro record only. After a manual shift, the displayed span must not be represented as an untouched calendar span. Keep calendar provenance as context, with the explicit shift clearly identified. An unnamed `=+3` must not silently select a different MEET by moving the selection window first.

For ordinary explicit durations, this reduces to the familiar arithmetic:

```text
S = ceil((minute_of_day − 5 × backward_units) / 5) × 5 + 5 × N
E = S + 5 × duration_units
```

At 09:42, `=fix2+` produces 09:50–10:00. Avoid saying it starts “in five minutes”: rounding means the actual wait is eight minutes in this example.

### Resolve name ambiguity deterministically

Reserve **one terminal, isolated `+` followed only by optional ASCII digits** outside quotes as the new modifier. Peel it before the bare-name lexer removes duration digits. An isolated plus means it is not part of a contiguous `++` or longer plus run.

Consequences:

- `=fix+3` becomes FIX shifted +15 minutes. This is an intentional compatibility change.
- `=fix+read2` retains its existing composite-name meaning: the internal plus is followed by a name component, not a terminal numeric shift.
- `=c++` and `=c++2` retain their existing meanings. Never take the last plus of `++` as the new modifier.
- `=c++2+3` has an isolated final plus, so it means a 10-minute C++ start shifted +15 minutes.
- Quotes protect every inner character: `=#"FIX2+"` and `=#"FIX+3"` remain exact names. Completion must emit such literals for names that the new grammar would otherwise reinterpret.
- A hash without quotes is not an escape from the modifier: `=#deep-work+3` means shifted DEEP-WORK. Use `=#"DEEP-WORK+3"` for that exact name.
- Reject repeated numeric shift tails such as `=fix2+1+2`, with a hint to combine them as `=fix2+3` or quote an intended literal name. Do not repeatedly strip and sum arbitrary tails.

A double-plus ending after a bare name remains name content for compatibility; `=fix2++` is **not** a two-unit shift. This is a cost of preserving existing plus-bearing names. Do not advertise it as timing. If this exception is judged too costly, the coherent alternative is to reserve *all* trailing plus runs and require literals for C++; that is a materially larger break, and I do not recommend it for this request.

Never choose between “name” and “shift” by checking whether a matching session currently exists. The same draft must retain its interpretation when the catalog, vault, or running session changes.

## 4. Why `x=` should stay out

`x=` records a closed past interval, ordinarily ending at the current rounded boundary T. Positive translation changes `[T−D,T)` into `[T−D+5N,T+5N)`, which records a closed session beyond that boundary. Keeping the old endpoint instead would shorten the duration and violate the proposed meaning. Clamping would introduce yet another meaning.

Past captures also have their own anchored timeline language. In `x=2~1+`, the plus selects a segment's **end edge**; it is not a five-minute offset. Consecutive `x=` items form stacks with one pin and bounded overlap/repair behavior. The current past parser explicitly excludes numeric offsets. Adding shifted past stacks would require decisions about which member moves, whether gaps are allowed, how anchors combine, what gets trimmed, and how the now limit behaves. [Past syntax and examples](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/docs/capture.md#recording-past-pomodoros), [past parser](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/src/native/capture_language/past.rs), [timeline planner](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/src/native/capture/pomodoro_past.rs)

Nor does `x=3 ++3` provide a valid implementation shortcut. In the isolated fixture it failed after recording the staged past item because no open timed Pomodoro remained to shift; the transaction refused. Where another open timed session exists, `++3` targets that open session, not the newly recorded past one.

**Scope decision:** leave the entire `x=` grammar unchanged, including its existing plus-bearing names and `~n+` anchors. Do not accidentally change it through shared bare-name helpers. If past offsets later become a genuine need, design them as timeline placement relative to an explicit historical anchor and keep the no-future-record rule. They are not a prerequisite for shipping this feature.

## 5. Implementation architecture

### Parse once; keep the base operation explicit

Introduce a small start-specific representation of the positive suffix, with its magnitude and original byte range. Keep the existing base start representation intact beneath it, conceptually:

```text
StartIntent {
    base: existing start selection + existing timing + existing drops,
    shift_later: optional { units, source_range }
}
```

This is a design sketch, not a requirement to create that exact Rust type. The important point is that **base timing presence remains distinct from shift presence**. Feeding raw `+3` into today's `spec.raw.is_empty()` decisions would accidentally turn kept-span swaps and calendar-derived starts into fresh 25-minute starts.

Locate the modifier in a quote-aware lexer before ordinary name/timing extraction, with the drop list already structurally separated. Both editor and execution consume the same parse result. A global regex replacement over the draft would corrupt names, literal text, item ownership, source ranges, and potentially past captures.

The primary seams are:

| Concern | Existing code to inspect/change |
| --- | --- |
| Recognizing the complete start token and its parts | `capture_language/item.rs::session_equals_token`, `start_timing_len`, start error builders |
| Shared standalone/link behavior | `capture_language/tokens.rs::parse_link_start_suffix`, `parse_pomodoro_start_suffix` |
| Name-versus-timing boundaries | `capture_language/bare_name.rs`; changes must be context-specific so past parsing does not drift |
| Editor spans and diagnostics | `capture_language/editor_pomodoro.rs`, `editor_classify.rs`, `editor_model.rs` |
| Name replacement and cursor preservation | `capture_language/completion.rs`, `capture_complete/pomodoros.rs::apply_bare_start_name_replacements` |
| Execution and summaries | `capture/pomodoro_start.rs`, `pomodoro_link.rs`, `pomodoro_adjust.rs`, `batch.rs` |
| Calendar selection, explicit timing, conflict hints | `capture/meet_event_run.rs` and event-conflict rendering |
| Public parse revision and formatting | `capture_language/mod.rs`, `capture_parse.rs` |

Current completion already moves trailing duration before `#` when accepting a name that cannot be bare. Extending only execution would leave acceptance of a completion capable of dropping, swallowing, or relocating the new suffix incorrectly. [Completion replacement logic](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/src/native/capture_complete/pomodoros.rs#L893)

### Plan against the same transaction

Reuse the start planner to resolve and stage the base operation. Reuse a factored shift primitive to move the exact resolved entry, rather than reselecting “whatever is running” from a public command invocation. The primitive should accept a resolved target/span, preserve `[t::]` versus `[off::]`, and return the shifted span and any relevant metadata.

Do not implement this by launching two CLI processes, sleeping, or submitting a second capture after the first succeeds. Do not expose synthetic extra capture items in JSON merely to reuse the code. The existing snapshot planner should continue to guarantee all-or-nothing writes across both the day note and task notes.

Update the compact result's start/end, canonical line, duration, placement, block tracking, override details, and calendar context together. Event-conflict checks and any suggested fit token must describe the final span, not the intermediate one. Preserve applicable existing warnings; avoid duplicate base/shift notices. Scope equivalence tests to durable results and relevant warning meaning, not equality of a two-item response envelope.

### Preserve the existing JSON field's meaning

`PomodoroStartSpec.offset_units` and the start summary's `offset_units` are unsigned backward-offset magnitudes today. Do not silently make them signed or invert their sign convention.

Prefer an additive optional `shift_later_units` field, omitted when absent and decoded as zero by new clients. The public raw timing can retain the new typed suffix, while the internal base object retains its old raw timing for base-selection decisions. Include explicit shift information in the resolved start summary so a client can present it without parsing raw text. The final authoritative `start`, `end`, and `duration_minutes` remain the primary display data.

Advance the capture grammar revision from the current 16 to the next revision available when implementation lands. A schema-version bump is not automatically necessary for additive fields, but accepted-text reinterpretations are still a CLI contract break and should be identified as such in the release commit. Existing app decoding uses defaults for omitted fields and renders Bob's resolved preview rather than computing times itself. [Rust model](https://github.com/bobs-org/bob-cli/blob/b73ac383c239a1f058742050f84b70c94e6c5732/src/native/capture_language/model.rs#L438), [Mac decoder](https://github.com/bobs-org/bob-mac-capture/blob/c2b7db24f188285085babb13570ae11f825ae197/Sources/CaptureCore/CaptureModels.swift#L1508), [Mac presentation](https://github.com/bobs-org/bob-mac-capture/blob/c2b7db24f188285085babb13570ae11f825ae197/Sources/CaptureCore/CapturePomodoroStartPresentation.swift)

Keep parsing, completion, time calculation, and preview truth in bob-cli. Extend the Mac's decoding, presentation, and fixture tests only as needed. Verify new-bob/old-app and old-bob/new-app combinations; a new client must not display support that its backend does not have.

### Scope the Obsidian relationship honestly

The current snippet lexer is `^se(\d*)(?:-(\d*))?$`; it does not accept positive offsets. Existing documentation says capture timing mirrors `se<X>`. [Snippet constant](https://github.com/bobs-org/bob-plugins/blob/2563c7898644d1f784c13f3eefa698285ae4a381/plugins/bob-ledger-tools/src/010-load-and-constants.js#L289), [snippet parsing](https://github.com/bobs-org/bob-plugins/blob/2563c7898644d1f784c13f3eefa698285ae4a381/plugins/bob-ledger-tools/src/020-time-and-pomodoro.js)

For this request, describe the existing numeric **base timing** as mirroring `se<X>`, and the new terminal modifier as Capture's compact shift. Do not claim `se2+3` works or automatically expand the request into a second writer's grammar change. A separately authorized snippet extension could share numeric fixtures later. The Mac frontend, in contrast, is a Capture client and should support the feature in the coordinated delivery.

## 6. Make the interaction feel finished

The preview is what makes the punctuation understandable. At 09:42, an illustrative single result could read:

```text
Start FIX
09:50–10:00 · 10 min · shifted 5 min later
```

A kept-span swap should show its actual inherited duration and the existing swap explanation. A calendar-derived start should identify the event context and the manual shift. Use the existing timing styling on the suffix and keep name styling on the name. No new mode, confirmation dialog, spinner, or permanent tutorial is warranted.

`=fix2+` is already complete, because the omitted number means 1. Adding `3` updates the preview to +15 minutes. Do not mark the bare plus as incomplete, launch a parent-task picker, or wait for extra punctuation. Name completion must preserve the suffix once, including when accepting an exact multiword name. The result of accepting DEEP WORK into `=de2+3` should be a valid spelling such as `=2#"DEEP WORK"+3`.

Examples of targeted error copy:

| Input/problem | Suggested response |
| --- | --- |
| `=fix2+0` | “Use a positive number after `+`; remove `+0` for no shift.” |
| `=fix2+1+2` | “Use one shift suffix: `=fix2+3`. Quote a literal name containing these characters.” |
| `=2+3fix` | “Put the shift at the end: `=2fix+3`.” |
| `=fix2~1+3` | “Put the shift before the drop list: `=fix2+3~1`.” |
| Count or arithmetic overflow | “That shift is too large; use fewer five-minute blocks.” |

Preserve the current literal/prose protections outside start contexts. For example, prose mentioning `C++`, generic `+query` parent completion, and `x=2~1+` should not acquire new behavior.

## 7. Validation and delivery criteria

This deserves semantic tests, not merely acceptance tests for a new character.

1. **Parser/editor agreement.** Assert equivalent names, durations, backward offsets, positive shifts, and original UTF-8 byte ranges for all accepted forms above. Cover CRLF, multi-item drafts, exact literals, incomplete quotes, and errors after a valid prefix. Invalid claimed starts must not silently become task captures.
2. **Completion round trips.** Accept a bare name, a hyphenated name, a digit-ending name, an exact multiword name, and plus-bearing names while keeping duration, shift, and drops. Check caret positions inside the name, on `+`, and inside the shift digits.
3. **Differential execution.** For each supported base start B, compare compact B+N with B followed by a separate `++N` item using the same `BOB_NOW` and initial fixture. Compare final note bytes and resolved target, not the response's number of items. Include ordinary placeholders, creation, restarts, kept/fresh swaps, calendar MEET runs, unnamed meeting selection, dropped tasks, new-task starts, active-task starts, and off-clock rows.
4. **Guards and transactions.** Test missing day/section, multiple open timed rows, a running-session link-start refusal, bad or missing task IDs, overflow, and a later failed item after a valid shifted start. Verify every touched file remains unchanged after a failed draft.
5. **Compatibility matrix.** Freeze `=c++`, `=c++2`, composite names, exact literals, prose, `x=fix2+`, and `x=2~1+`. Explicitly assert the intended new interpretation of `=fix2+`, `=fix+3`, and `=+3`.
6. **Clocks and boundaries.** Test 09:42, an exact boundary with nonzero seconds, 23:55, midnight-crossing endpoints, old zero durations, leading zeros, and the checked arithmetic limits. Preserve the existing modulo-day ledger convention; do not accidentally move a note to tomorrow or change all timing policy in this feature.
7. **Presentation.** Verify the single result contains the final shifted line/range, correct duration and clock key, final conflict context, and a coherent override/calendar explanation. Test decoding when the new optional field is absent.

The existing date-free HHMM ledger model deserves an explicit limit in expectations: large shifts can wrap the displayed clock, and a future-start session is still an open timed session today. This feature is not a future-day scheduler and does not resolve that broader model. Preserve current `++N` behavior for equivalence, keep the resolved clock prominent, and treat any new multi-day policy as a separate design decision.

Implementation should run the relevant Rust grammar/completion/capture tests, the repository's required checks, and affected documentation checks. If Mac Swift changes are made, run portable checks and the required macOS compile/CI gate; do not treat a Linux-only pass as validation of macOS targets. Follow the daily release train and use a breaking-change marker for the intentionally reinterpreted capture text; do not manually edit the version or changelog.

## 8. Critique and alternatives

| Approach | Benefit | Cost | Judgment |
| --- | --- | --- | --- |
| Keep only existing separate `++N` | No new ambiguity; already works | Awkward for links, two items and two result stories | Keep as the general operation, but add the shortcut |
| Terminal `+N` as a modifier of the resolved start | Satisfies examples; preserves duration and contextual behavior; one result | Requires explicit name precedence and completion work | **Recommended** |
| Change numeric timing to one signed offset | Attractive arithmetic model | Does not alone solve names; changes calendar/swap interpretation; risks old JSON meaning | Do not use as the product model for this request |
| Attach `++N` instead | Visually resembles standalone shifting | More punctuation; collides directly with C++; still needs lexing rules | Inferior to the requested single-plus spelling |
| Add `in 15m`, `start:1000`, or a new scheduling sigil | More descriptive for new users or arbitrary dates | Broadens the language and the feature considerably | Consider only for a separate scheduling need |
| Add the same modifier to `x=` | Superficial symmetry | Conflicts with historical endpoints, stacks, and existing `~n+` meaning | Exclude |

The feature is a good idea when it expresses one frequent intention: “start this, just a little later.” It is less compelling if it becomes an excuse to create a general timing expression language. The disciplined version retains one terminal modifier, one visible result, one existing transaction, and a documented literal escape for ambiguous names.

The principal tradeoff is compatibility. There is no honest way to make `=fix2+` both retain its current name meaning and perform the requested shift without adding a disambiguation rule. Treat this as an intentional grammar revision, ensure completion generates safe names, and explain it through a few concrete examples. Do not conceal the break behind vault-dependent guessing.

## 9. Explicit requirement adjustments

- **Clarify that both endpoints move.** Duration stays unchanged; the feature does not merely change the start boundary.
- **Correct the link equivalence.** The existing equivalent is link/start plus a blank-line-separated `++N`, because task/link forms do not currently join same-line session chains.
- **Define suffix placement.** Append after the complete start core and before a drop list, including after an exact name. Do not add redundant placements inside leading timing in v1.
- **Preserve contextual base semantics.** A suffix-only named start can keep an inherited running span or a calendar span. Request fresh default timing explicitly with a duration when desired.
- **Reserve the terminal single-plus pattern.** This reinterprets some currently valid names; exact literals are the escape. Preserve existing `++` name runs and internal composite-name pluses.
- **Exclude `x=` for this release.** Its anchors, past boundary, and stack semantics remain intact.
- **Keep the request within Capture.** Coordinate Bob Mac Capture's contract/rendering; do not imply Obsidian `se` gains the new suffix automatically.

## 10. Recommended solution

**Ship a start-specific terminal `+[N]` modifier for all existing Capture start entry points, defaulting N to 1 and preserving the resolved session's duration.** Parse it once, outside quotes and before name/timing decomposition, then apply it to the exact session selected by the ordinary start inside the current atomic planner. Produce one accurate preview/result, preserve existing backward offsets and JSON meanings, protect plus-bearing names through deterministic precedence and exact literals, and test against the existing start-then-shift behavior.

**Leave `x=` unchanged.** The result is a compact, useful feature with a clear mental model: choose and start the session as usual; the final `+` moves that session later.
