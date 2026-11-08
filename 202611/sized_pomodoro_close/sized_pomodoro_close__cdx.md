# A duration before `x`: designing an exact-length Pomodoro close

Independent research by **cdx**, 2026-11-08.

**Recommendation:** add `[B]x…`, where the optional positive integer `B` means a final recorded duration of `5 × B` minutes. Keep the session start fixed; set its end and recorded duration together; then apply the existing close selection and Work Log behavior. An explicit duration must bypass automatic shortening. Teach it as **“Duration before `x`; tasks after `x`”**, with the more precise inline hint **“Before `x`: 5-minute blocks · after `x`: task numbers.”**

This is a worthwhile shortcut for someone who already thinks in Bob's five-minute blocks. The important refinement is to make it an exact-duration close, not a textual expansion into a relative resize followed by today's automatic close. Those operations are observably different. The report identifies that requirement change explicitly below.

## Evidence and limits

I independently inspected bob-cli at `59ba11a6ab09cd7dba5b8a753f51d456348ed288` and bob-mac-capture at `0583f37aef3241ffc872e11325f8afaec1c5cbcc`. No other swarm research report, transcript, summary, or findings were consulted.

The evidence comprises current Rust and Swift source, existing tests and documentation, audited SASE decision-memory reads, and small read-only executable probes. The installed executable reports **bob 0.4.0, capture grammar 16**; the inspected source reports **grammar 19**. Accordingly, executable observations below corroborate the timing and lexical findings but are not represented as tests of the checkout's newest grammar. I did not build the checkout, run its full suite, implement this feature, or compile Swift. Dry-run execution used disposable fixture vaults inside the workspace; fixture contents were checked unchanged and removed afterward.

Source references `[S1]`–`[S12]` below identify the inspected files and functions. External UX guidance informs the presentation recommendations, not the project's behavior contract.

## What the existing implementation actually does

The current language separates relative resizing (`+N` / `-N`), shifting the entire span (`++N` / `--N`), starting (`=`), closing (`x`), and recording past work (`x=…`). Duration and offset counts already use five-minute units. Numbers after `x` select task links; they are not durations. `x!2` completes task 2 and, under the current explicit-selection decision, defers unlisted ordinary task links. `[S1, S2, S3]`

A close already has significant behavior worth preserving:

- It finds exactly one open timed entry in the selected daily note. A timed future calendar entry can meet this implementation's definition of “running”; it does not necessarily mean that its start is in the past. `[S4]`
- It automatically removes whole five-minute increments from the end when at least five minutes remain. It does not extend an overrun. The calculation is based on the existing end and remaining minutes, so a non-five-minute original duration retains its remainder. `[S5]`
- Numeric keep, park, complete, and drop lists control task scope. Wildcards and unlisted Event Tasks retain their existing specialized rules. A duration prefix must not itself count as a numeric task selection. `[S2, S6]`
- A note-free plain `x0` is a reset: it returns the entry to a placeholder rather than retaining a closed timed session. A stand-alone note or an explicit modifier prevents that reset. `[S7]`
- Inline entries and child bullets write Work Logs. Chains and blank-line batches use staged snapshots; errors abort the whole capture. `[S8]`
- Calendar outcomes use the actual close clock supplied as `now`, independently of the ledger's automatically adjusted end. This distinction matters when introducing an exact recorded duration. `[S6]`

### The equivalence in the request needs a clock condition

The following observations used a `09:00–09:25` session with two ordinary task links, and `bob capture --dry-run -f json`. The fixture harness supplied `BOB_NOW` and `BOB_DAY_FILE` explicitly.

| Draft | Submission time | Duration after resize | Duration finally recorded |
| --- | --- | --- | --- |
| `-3 x!2` | 09:03 | 10m | **5m** |
| `-3 x!2` | 09:09 | 10m | **10m** |
| `-3 x!2` | 09:12 | 10m | **10m** |
| `+3 x!2` | 09:27 | 40m | **30m** |

The current `close_timing` implementation explains these results: the ordinary close can shorten the newly resized span again. `[S5]`

Therefore, “`2x!2` is equivalent to `-3 x!2`” is only conditionally true if the intended result is ten minutes. Under the recommendation, it is true in the second and third rows, but intentionally false in the first. At 09:03, `2x!2` would record exactly ten minutes, clearly showing that its recorded end is seven minutes after now.

There is a second reason not to generate a signed count: an existing 23-minute session needs a **13-minute** reduction to reach ten minutes. No integer five-minute delta can express that. A probe of `-3 x!2` on `09:00–09:23` at 09:09 recorded eight minutes. Directly assigning the requested duration works without rounding or assumptions about the current length. `[S3, S5]`

## Is the idea good?

Yes, within Bob's existing expert language. It removes the need to inspect the current planned duration, subtract the desired duration, choose a sign, and enter a separate resize. The desired result can stay the same even if the planned session changes while the draft is open. It also removes a space and operator: `2x!2` is shorter than `-3 x!2`.

It does not remove all arithmetic: someone thinking “ten minutes” still converts ten to two blocks. Its value is strongest for the user who already uses `=2`, `+2`, and five-minute sessions. I would keep these units consistent rather than introduce a minutes-only exception before `x`.

The main costs are syntax density and prose collisions. `2x2` places two different kinds of numbers next to one another. It can mean “ten minutes, keep task 2,” but looks like multiplication or repetition to an unfamiliar reader. Worse, **`2x4 lumber` currently is ordinary task text and would become a close with a Work Log entry** if all current close features compose. Narrow token recognition cannot eliminate that exact collision. This is a real grammar compatibility change, not merely an additive JSON field.

The UI should make the two axes visible: the timing line explains the prefix, and the existing numbered task rows explain the suffix. Jakob Nielsen's guidance on visible state, recognition, and consistency supports this approach; it does not constitute a usability study of this particular syntax. My inference is that visible minutes and unchanged task rows will reduce the ambiguity more effectively than another permanent control. [Nielsen's usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/).

## Proposed user contract

Use `B` for duration blocks in documentation and `K/P/M/D` for task lists, instead of reusing `<N>` for both duration and task identity:

```text
[B]x[K][*P][!M][~D][@K]
```

This is a schematic form: the existing modifier ordering, wildcard rules, mutually exclusive lists, and typed-last `@K` alias remain exactly as today. The only new component is an optional digit run immediately before the close's `x`.

| Capture | Meaning |
| --- | --- |
| `x!2` | Existing automatic-duration close; complete task 2 |
| `2x!2` | Record exactly 10m; complete task 2; defer other ordinary links |
| `2x` | Record exactly 10m; retain the ordinary default close selection |
| `2x1,3!2` | Record 10m; keep 1 and 3 in progress; complete 2 |
| `2x*!2` | Record 10m; complete 2; park the remaining eligible links |
| `2x~2` | Record 10m; drop 2; defer other ordinary links |
| `2x!2@1` | Record 10m; complete 2; keep 1 in progress |
| `8x!2` | Record 40m, including extension if necessary; complete 2 |
| `2x!2 shipped the patch` | Same close with the existing inline log on task 2 |
| `2x!2 =` | Close at 10m, then run the existing start operation |
| `--1 2x!2` | Shift the running span five minutes earlier, then record 10m and close |
| `@work:task=2x!2` | Link the task first, then apply this close to the resulting lineup |

The equivalent new-task target suffix and caret-linked forms should work too. Shared close syntax should not stop working merely because it is attached to a task. Do not add duration prefixes inside the separate `x=…` past-recording grammar: it already has its own duration. `[S1, S2, S8]`

### Timing and validation

For a valid selected session with original start `S`, original duration `D`, and requested block count `B`:

```text
requested_minutes = checked(B × 5)
closed_start       = S
closed_duration    = requested_minutes
closed_end         = S + requested_minutes
resize_delta       = requested_minutes − D
```

Keep extended minutes or an anchored datetime until validation is finished; wrap only for the displayed `HHMM` end. The original start remains fixed, including when it falls off a five-minute boundary. A session starting at 09:02 closes at 09:12 for `2x`, not at 09:10.

The explicit branch skips auto-shortening completely. The absence of a prefix follows the current timing code unchanged. If `D` already equals the request, there is no resize, but the session still closes. Do not create an invalid `+0` or `-0` intermediate command.

Validate before staging any mutation:

- Accept ASCII decimal positive integers. Preserve the raw spelling; accept leading zeros as decimal (`02x` means 10m), without rewriting the draft while typing. Reject `0x` with a useful message.
- Use checked parsing, multiplication, addition, and signed conversions. Never saturate an absolute target to zero, truncate digits, or wrap integer overflow.
- As a bounded initial contract, accept **1–287 blocks**: five minutes through 23h55m. Reject a full day or more rather than silently representing multiple days with an undated `HHMM–HHMM` span. This is a proposed new limit, not an existing global Bob restriction. Normal midnight crossings remain valid; no arbitrary 60- or 120-minute ceiling is needed.
- Require exactly one selected open timed entry, a parseable start/range, and usable duration metadata when needed. Ordinary `x` can preserve some unparseable ranges with a warning; an explicit target cannot promise a precise result from an unusable range. Reject ambiguous or malformed timing instead of guessing.
- Require that the selected session has actually started. A future timed calendar entry should get “This session starts at 10:00; start it first or use `x0` to reset it.” This feature is for a running session, not a new way to record future work from an unstarted placeholder.
- Preserve the existing daily-note selection policy. Do not silently scan or mutate yesterday's note to find a convenient target. Wrapped end times should work whenever the existing selection mechanism finds the intended session.

Allow an explicitly requested end after now once the session has started. It is an authored duration, so silently shrinking it would violate the feature. Show the resulting clock range and a factual “ends 7m after now” caption. Likewise allow shortening below elapsed time: the user may be correcting the amount they want recorded. Neither case needs an extra confirmation dialog.

Do not reuse the current shortest-distance, half-day clock arithmetic to interpret a long explicit duration. Calculate explicit span lengths from the request and start, preserving the day offset. Keep the existing `remaining_minutes` meaning for old clients; add a separate resolved comparison if needed for the new caption. Long-duration and midnight tests should catch accidental ±12-hour reinterpretation. `[S3, S5]`

### `x0`, selections, and calendar tasks

**A duration prefix means this is a close, so `2x0` records ten minutes and defers ordinary task links; it never resets the session.** Plain `x0` retains its existing conditional reset behavior. This follows the existing precedent that an explicit close modifier prevents reset, and avoids an explicit positive duration disappearing into `()`. Preserve the resulting closed timed row even when it has no remaining links. `[S7]`

Do not feed `B` into `close_selection_is_explicit`. `2x` has exactly the task selection of `x`; `2x!2` has exactly the task selection of `x!2`. A prefix changes the duration, not which tasks were worked.

Keep **actual submission time** as the Event Task close clock and as the timestamp for dated effects. Do not fake `now = S + requested_minutes` just to suppress decrementing. The current event rules classify unlisted events against the real close clock; changing that could complete a future event or defer one that has already ended. The requested duration describes recorded session time. Explicit task numbers continue to override individual event outcomes, and wildcard exclusions remain intact. `[S6]`

### Lexical boundaries and compatibility

Recognize the new prefix only at an existing close position, tightly glued to `x`. Retain the current lowercase-only whole-item rule and the existing case-insensitive attached close suffix rule; do not widen capitalization behavior incidentally.

| Input | Recommended behavior |
| --- | --- |
| `2x!2` | Valid exact-duration close |
| `0x!2`, an overflowing digit run followed by `x!2` | Claimed close error; never silently capture as a task |
| `2x!`, `2x*` | Valid existing wildcard forms |
| `2x~`, `2x@`, `2x1,` | Existing incomplete selection state at the correct byte range |
| `2 x!2` | No prefix; ordinary prose under the existing language, not an inferred close |
| `2xylophone`, `2xx`, `2x-ray` | Ordinary prose; do not claim arbitrary words containing `x` |
| `2X4 lumber`, `Buy 2x4 lumber` | Ordinary prose under the whole-item lowercase rule |
| `2x4 lumber` | Close at 10m, keep task 4, log “lumber”; document this newly reserved shape |
| `2.5x`, `２x` | No supported duration prefix; keep outside the recognized ASCII-integer grammar |
| `2x=3` | Claimed near-miss error: use `2x =3` to close then start, or the existing `x=3` to record past work |
| standalone `=2x!2` | Teaching error pointing to `2x!2`, consistent with retired standalone `=x…` |
| `@work:task=2x!2` | Valid attached close; its separator `=` remains necessary |

Do not search-and-replace `digits+x` across the draft. It would steal text inside logs, task prose, quoted names, links, or past-session expressions. Existing rewrite/completion operations must preserve the prefix and edit only the appropriate selection or target span.

Treat release communication as part of this feature: increment the grammar revision, document the newly reserved prose shapes and uppercase/mid-sentence alternatives, and assess it as a grammar contract break for the release-train `!` convention. Do not hand-edit the package version or changelog. Optional JSON fields alone are additive; the text language change is not wholly additive.

## Make it readable without making it larger

Use the existing close card, with a dominant final duration and ordinary task rows:

```text
Close BUILD · 10 min
09:00–09:25 → 09:00–09:10 · −15 min

2  Complete   Ship the patch
1  Deferred   Review the notes
```

For an unchanged duration, omit the redundant arrow. For extension, show `+15 min` with the same visual weight as subtraction. The prefix should share the existing timing color, and task numbers should retain their existing action colors. Text and accessible labels must carry the distinction without relying on color.

On first recognition of the prefix, the compact explanation can be “2 blocks = 10 min.” If a general teaching hint is needed, use “Before x: 5-minute blocks · after x: tasks.” Do not continually rewrite the input into expanded syntax or make the person approve a separate resize card.

Errors should identify the field and provide one repair, for example: “Duration before `x` must be at least 1 block (5 minutes). Use `x0` to reset.” Do not silently correct a mistaken number. Visible changes, useful examples, and actionable errors follow the original [Command Line Interface Guidelines](https://clig.dev/#ease-of-discovery); these are design principles, not evidence that a particular label has been user-tested.

There is a concrete Mac integration requirement: `CapturePomodoroClosePresentation` currently decides whether timing changed using `decrementedMinutes > 0`. Otherwise it renders the **planned** range and duration. An exact extension with zero decrement would consequently display the old duration. Update presentation to compare the before/after timing values and use the resolved closed values. The terminal renderer also uses decrement-only logic for showing its arrow. `[S9, S10]`

## Implementation shape

Implement one semantic close operation carrying an optional duration, not two generated capture items or two subprocess calls.

1. **Shared parsing.** Extend `PomodoroCloseSpec` with optional `duration_units`. Add a shared close-head lexer returning the duration, selection body, and absolute ranges. Route whole-item, linked-task, new-task, chain, inline-log, editor, and completion/rewrite paths through it. Existing selection lexing should continue to own `K/*P/!M/~D/@K`; prefix parsing should not duplicate that grammar. `[S2, S8, S11]`
2. **Separate timing policy from task selection and continuation policy.** Introduce an internal timing choice such as `Automatic` versus `ExactDuration { minutes }`. The existing `LedgerClosePolicy::Ordinary/Record` controls continuation placement and should not acquire unrelated combinations merely to express duration. An exact duration must also disqualify the reset path in both the capture adapter and shared planner. `[S5, S6, S7]`
3. **Resolve against staged state.** Find the running entry after earlier items and after a same-item link insertion. Compute exact timing once, retain its original before-image, and pass it to the shared close machinery before duration-dependent accounting runs. Never patch the ledger only after task effects and summary construction. Keep all writes in `CaptureBatchPlanner`, so invalid selections, conflicting files, and later batch errors roll back timing and tasks together. `[S3, S6, S8]`
4. **Preserve clock handling.** Use the existing timing formatter and close-time clock resolver. Keep `[t::]` / `[off::]` and other metadata under current policy; do not blindly inject `[t::]`. The final metadata must agree with the final span. Preserve all logs, name settlement, carry behavior, and successor offers. `[S3, S6]`
5. **Expose intent and result additively.** Keep `kind: "pomodoro_close"` and the existing nested result in task/link closes. Add `duration_units` when present and an optional signed `duration_delta_minutes`. Keep `planned` as the original staged span before this close; `closed` is the final span. Keep `closed_at` as the actual submission clock. Retain `decremented_minutes` for automatic shortening, with zero for the explicit branch; do not encode extension as a negative unsigned decrement. Old unprefixed results should remain byte-compatible where tests currently require that. `[S9, S11]`
6. **Coordinate the thin client.** Decode new fields optionally in Swift; the Mac renders Rust's interpretation and never parses `2x` itself. Preserve schema version 1 for additive fields, bump grammar revision from the current value, and ensure unknown semantic spans remain tolerable. Ship the compatible presentation update before or with the Rust feature. An older Bob interprets `2x!2` as task text, so a new client must not advertise it until its normal parser response demonstrates support. Capability messaging should follow Bob's grammar metadata, not a second Swift regex. `[S10, S11]`

The affected source is dispersed enough that this is a modest language feature, not a regex-only patch. Most complexity is integration and compatibility, not computing `5 × B`.

### Verification that earns confidence

| Area | Required evidence |
| --- | --- |
| Exact timing | 25→10, 25→40, 10→10, and 23→10; start preserved; exact results independent of submission time once started |
| Ordinary close | Existing unprefixed auto-decrement, overrun, selection, and reset fixtures unchanged |
| Selection orthogonality | `2x` versus `x` has identical task outcomes at the same real clock; `2x!2` versus `x!2` likewise |
| Reset | Note-free and note-bearing `2x0` both close with ten minutes; ordinary `x0` keeps current behavior |
| Accounting | Recorded time, off-clock fields, task Work Logs, completion dates, names, and carried links agree with the final close plan |
| Event boundaries | Actual-now event classification unchanged when the requested ledger end lies before or after now; explicit numbered picks and wildcard exclusions preserved |
| Grammar | Standalone/link/new-task forms, every modifier, leading zeros, uppercase policy, prose collisions, incomplete tails, and overflow |
| Editor | UTF-8 range offsets with non-ASCII text before a close, caret immediately before/after `x`, highlighting, preview, and prefix-preserving rewrite |
| Composition | `--1 2x!2`, `2x!2 =`, logs plus chains, and selection after staged task insertion; relative resize followed by exact close uses the final absolute target |
| Failure atomicity | Invalid task number or later failing item leaves every source byte unchanged; dry-run writes nothing; snapshot drift is refused |
| Boundaries | Minimum, 287, rejected 288, huge integers, malformed timing, future-start session, missing/multiple running sessions, non-grid start, midnight wrap |
| Presentation | Shorten, extend, unchanged, future recorded end, off-clock session, older payload without new fields, and full accessible timing sentence |

Prefer table-driven cases through the existing Rust selection/timing suites and CLI fixtures, plus focused Swift decode/presentation tests. No new end-to-end testing framework is needed. For actual Swift implementation, follow that repo's required portable checks and exact-SHA macOS CI; source inspection in this research is not a substitute for compiling it.

## Alternatives and requirement changes

| Approach | Assessment |
| --- | --- |
| Literal absolute resize, then ordinary `x` | Closest to the wording “before being closed,” but can record less than requested and weakens the main benefit. Acceptable only if documented as a pre-close target, not final duration. I do not recommend it. |
| Generate `±delta x…` text | Wrong for non-grid original durations; encourages duplicate planning and obscures original intent. Reject. |
| Exact `[B]x…` | Best fit for the existing five-minute language, provided final duration is visible and prose collisions are acknowledged. Recommended. |
| Explicit minute form such as `10mx!2` | Removes block conversion and reduces `2x4` collisions. Strong alternative if minutes are how Bryan naturally thinks, but introduces a new unit vocabulary. Do not ship as a parallel alias in the first release. |
| `x=2` for duration | Already means recording a past Pomodoro. Reject. |
| Change `x2` to mean duration | Breaks task selection and learned behavior. Reject. |
| Separate absolute-resize operator | Useful only if resizing without closing becomes a frequent need; adds a broader language feature for this narrow problem. Defer. |

The proposed adjustments to the request are:

1. **Final duration is authoritative.** A prefixed close bypasses automatic shortening. Thus the supplied equivalence is conditional, not universal. This is the central design change.
2. **Explicit duration suppresses reset.** `2x0` retains ten recorded minutes; `x0` keeps its existing semantics.
3. **Bound and validate the operation.** The initial supported range is 1–287 blocks, and the selected session must have started and have usable timing. These limits address the current daily ledger representation rather than imposing an arbitrary Pomodoro length.
4. **Compose across existing close entry points.** Support attached task/link closes as well as standalone closes, while leaving past recording separate.
5. **Treat newly claimed prose as a compatibility change.** Document `2x4 lumber`, offer `2X4 lumber` or a leading prose word, and coordinate client rollout.

No change to task-selection policy, calendar close clocks, user preferences, persistent vault schema, or new confirmation gesture is required.

## Sources

Paths below are relative to the named repository at the inspected commit. Function names and line anchors identify the evidence even if a later checkout shifts line numbers.

- **[S1]** bob-cli `docs/reference/capture-syntax.md`, “Overloaded markers,” “Incomplete input versus executable syntax,” and “Recording past Pomodoros”; `docs/capture.md`, closing syntax and JSON contract. `src/native/capture/pomodoro_start.rs:16`, `compute_pomodoro_start_range`.
- **[S2]** bob-cli `src/native/capture_language/close_selection.rs:74–182`, `close_after_eq_parts`, `classify_whole_item_close`, retired spellings; `model.rs:260`, `PomodoroCloseSpec`; `capture_pomodoro_close/selection.rs`, explicit-mode logic.
- **[S3]** bob-cli `src/native/capture/pomodoro_adjust.rs:264`, `plan_pomodoro_adjust_item`; the same file's `adjustment_duration_for_range` and `format_adjusted_range`. `tests/cli/capture/pomodoro_adjust.rs` covers clamping and midnight wrap.
- **[S4]** bob-cli `src/native/capture_pomodoro_close/ledger.rs:143`, `find_running_pomodoro`; `src/native/capture/pomodoro_adjust.rs:127`, `select_running_session`.
- **[S5]** bob-cli `src/native/capture_pomodoro_close/ledger.rs:187`, `close_timing`; `:276`, `LedgerClosePolicy`. `tests/cli/capture/pomodoro_close.rs:113` verifies the ordinary close's before/after timing result.
- **[S6]** bob-cli `src/native/capture_pomodoro_close/linked_tasks.rs:1027`, `plan_pomodoro_close_for_entry`; `:1574`, `close_clock_for_entry`. Audited memories: `decisions:close-selections-list-explicitly`, `decisions:event-task-links-close-by-the-clock`, `decisions:consumption-keeps-notes-and-recorded-time`.
- **[S7]** bob-cli `src/native/capture_pomodoro_close/reset.rs:31–83`, `is_reset_selection`, `is_reset_spec`, `reset_if_eligible`.
- **[S8]** bob-cli `src/native/capture_language/draft.rs:497`, chain and inline-close splitting; `item.rs:3693`, `session_equals_token`, and `:3967`, `is_session_chain_token`; `src/native/capture/batch.rs`, staged snapshots; `tests/cli/capture/pomodoro_chain.rs`, equivalence, dry-run, and rollback tests.
- **[S9]** bob-cli `src/native/capture/pomodoro_close.rs:281`, `build_close_summary_json`; `src/native/capture/output.rs:4439`, human timing display and decrement-only arrow.
- **[S10]** bob-mac-capture `Sources/CaptureCore/CapturePomodoroClosePresentation.swift:248–278`, timing presentation; `CaptureModels.swift:790`, parsed close spec; `:3163`, close summary and optional decoding. Audited memory: `decisions:mac-capture-is-a-thin-client`.
- **[S11]** bob-cli `src/native/capture_parse.rs:33–36`, schema compatibility; `src/native/capture_language/mod.rs:48`, grammar revision 19; `editor_pomodoro.rs`, close spans; `bare_name.rs`, close-shaped name exclusions; `rewrite.rs`, close rewrite integration.
- **[S12]** Read-only local probes described above: installed bob 0.4.0 / grammar 16. Lexical probes classified `2x`, `2x!2`, `2x4 lumber`, and `2 x!2` as tasks, `x!2` as a close, and `x=2` as past recording. Timing probes used isolated fixtures and confirmed unchanged source bytes. Current-source inspection, not these older-binary probes, is authoritative for grammar 19 behavior.

## Recommended solution

Implement **exact-duration `[B]x…`** as a first-class option on the existing close operation. Keep the start, compute `B × 5` once, bypass auto-shortening, preserve the actual close clock, and let the shared planner carry out the established task and log effects atomically. Show the resulting minutes and clock range in the existing preview, including extensions. Ship the matching Mac presentation update and grammar documentation together.

This preserves the user's compact `2x!2` idea while making its strongest promise easy to understand: **the duration typed before `x` is the duration that will be recorded.**
