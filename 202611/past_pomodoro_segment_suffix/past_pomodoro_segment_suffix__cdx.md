# Past Pomodoro placement: named time slots, explicit repairs, and a trustworthy preview

Independent research by **cdx**, 2026-11-05.

This report investigates the proposed placement suffix for `x=<E>=<X>`. It is a design recommendation, not an implementation. I inspected bob-cli at `832e124645585118f9c7e42633e05814f70ec59c` and bob-mac-capture at `6c39ff8f754e9e0fb331ddbb387da2c6635c931d`, consulted the relevant SASE contracts through audited memory reads, and checked primary platform guidance. I did not consult the other swarm researchers or their reports.

## Assessment

**This is a good feature for Bob's keyboard-oriented workflow.** Recording remembered work by reference to an existing session or the gap beside it is easier than calculating clock offsets. The proposed forms cover three useful intentions: fill the latest gap, insert into an older gap, and reattribute an edge of recorded work.

The main weakness is discoverability. In `x=2~2+=!1`, the two `2`s mean duration and placement, while `!1` selects a task. Elsewhere in capture, `~` already has other meanings. This can be a good expert language if the app continuously translates it into **which session, which interval, which task, and which existing time changes**. A syntax-only release would be much less convincing.

Keep the requested spellings, including the asymmetry of `~~`. Do not add another offset notation or a separate full timeline editor to the first implementation. Invest instead in a shared interval resolver, a small context-sensitive placement list, and the existing past-work preview card.

The subtle engineering work is preserving transactional behavior and handling multiple records. The present implementation assumes every adjacent `x=` run occupies one continuous interval. Arbitrarily placed records invalidate that assumption.

## What exists today

The checked-out source provides a strong foundation:

| Concern | Existing behavior and implication |
| --- | --- |
| Duration | `x=2`, `x=2read`, and `x=read2` request two five-minute units. An omitted count requests 25 minutes. The count is **not a historical block index**. |
| Default position | `T` is the current local minute rounded up to a five-minute boundary. A single record occupies `[T − duration, T)`. At an exact boundary it stays there; seconds are discarded before rounding. |
| Multiple records | A maximal consecutive run of `x=` items is a stack. Its rightmost member ends at `T`; preceding members pack backward in typed order. Blank lines do not break a stack. |
| Close clock | Each record closes at `min(window.end, now)`. Task outcomes, event classification, and Work Log timestamps use that member's close clock. |
| Source session | The name selects the placeholder/task lineup, independently of the time window. An unnamed record takes the next eligible untimed placeholder. A named record reuses a matching placeholder or creates a new historical instance. Open timed targets are refused. |
| Existing history | `!` permits edge trimming of closed rows. It never changes open work and never permits erasing a row or splitting its remaining history into two pieces. An unnecessary `!` is an error. |
| Mutation | Capture plans against staged snapshots, checks conflicts, and applies the batch atomically. Trims preserve row identity, children, clock kind, and task links. Closing the new record goes through the existing close planner. |
| Mac contract | Rust owns grammar, rewriting, completion, interval decisions, and vault writes. Swift already renders structured past-record windows, trims, task effects, and a “Record” action. |

These findings come from the [past grammar](https://github.com/bobs-org/bob-cli/blob/832e124645585118f9c7e42633e05814f70ec59c/src/native/capture_language/past.rs), [past planner](https://github.com/bobs-org/bob-cli/blob/832e124645585118f9c7e42633e05814f70ec59c/src/native/capture/pomodoro_past.rs), [batch orchestration](https://github.com/bobs-org/bob-cli/blob/832e124645585118f9c7e42633e05814f70ec59c/src/native/capture/plan.rs#L200), and [current documented contract](https://github.com/bobs-org/bob-cli/blob/832e124645585118f9c7e42633e05814f70ec59c/docs/capture.md#L5213).

Two details are especially important:

1. `compute_preflight` currently needs only the specs and clock. The new resolver must also consume the staged daily-note snapshot. Reading the vault separately would make selection and mutation disagree.
2. `preflight_overlaps` uses the first member's start and the last member's end as the stack's continuous union. That must change before mixed historical placements are accepted. Taking a bounding interval across disjoint windows would remove time nobody requested.

### Installed software is not the inspected checkout

Read-only probes against the installed `bob 0.4.0` returned `READ2`, 25 minutes for `x=read2=!1`; this checkout's source and tests instead specify READ, 10 minutes. The installed parser also rejects `x=2~1!=!1` with a task-drop teaching error and rejects the dash form as an offset. This is evidence of source/runtime version skew, not proof of a defect in this checkout.

I did not run the repository's compiled tests or modify a live vault. The implementation should be verified against a binary built from its exact source revision. A manually checked version number alone is insufficient for coordinating the Mac rollout.

## Requirements I would clarify or adjust

These are deliberate recommendations beyond, or clarifications of, the supplied requirements:

| Decision | Recommendation | Reason |
| --- | --- | --- |
| Vocabulary | Call the indexed objects **time slots** in UI prose; call the duration count **five-minute units**. | “Block 2” currently risks meaning either ten minutes or historical slot 2. |
| Scope of a slot | Explicit placement stays inside its selected interval. Only bare `~` automatically shortens a request. Other oversize requests fail with the available duration. | Otherwise selecting a gap can unexpectedly take time from neighboring sessions. |
| Meaning of `!` | Preserve existing permission exactly: authorization to trim closed history, never authorization to overflow a selected slot. | Placement and permission answer different questions. |
| Numbering | Resolve positions chronologically, from one pre-stack snapshot. Ignore untimed placeholders and zero-length rows. Do not manufacture zero-width gaps. | File order and edits made earlier in the same stack must not renumber later selectors. |
| Unusual history | For the first release, decline suffix placement when the relevant daily timeline has overlapping timed rows or ambiguous cross-day spans. Keep existing unsuffixed behavior. | A single alternating session/gap catalog is not well-defined for concurrent history. Do not silently merge named sessions or guess ownership. |
| No usable boundary | If the boundary needed by a selector is absent, return a specific error. Never silently invent a midnight-based `~` session on an empty day. | Recording the first 25 minutes after midnight is a poor fallback for “recent work.” |
| Multiple records | A suffix positions only its own record. All unsuffixed members retain automatic packing, excluding the durations of explicitly placed members. | Avoid hidden inheritance or moving an entire stack because one member has a suffix. |
| Typing assistance | Rewrite dash aliases only in a placement field identified by Rust. Keep them an editor assist, not a general global substitution. | Names, task IDs, log text, and other operators legitimately contain `-`. |
| Preview stability | The Mac should submit a placement expectation from the preview, which Bob checks before writing. Changed history or a changed boundary refreshes the preview instead of silently selecting a different interval. | Within-execution snapshot checks do not, by themselves, bind a prior preview to a later capture invocation. |

The overlap restriction is a real limitation. Existing off-clock history can overlap, and the current clock contract explicitly acknowledges this. Supporting concurrent timelines would require a separate rule for ranking overlapping sessions and choosing which histories `!` may alter. I would not hide that policy inside the first suffix implementation. An error should identify the overlapping rows and leave the draft intact. This restriction need only affect the new placement feature; it is not a proposed normalization of existing history.

One requirement deserves a precise correction: **the absence of a suffix and `~+` would share an end anchor, but are not necessarily equivalent operations**. An unsuffixed 25-minute record ending at 09:15 begins at 08:50 even if the latest gap begins at 09:00. A bounded tail-slot operation could not do that. Continue to omit `~+`, as requested, but explain it as “use ordinary `x=` to end at the current boundary,” rather than asserting all fitting and overlap behavior is identical.

## Grammar and mental model

Use the existing duration/name grammar as the base, followed by placement, repair permission, and optional task outcomes:

```text
x=<duration-and-name>[<placement>][!][=<task-outcomes>]

placement := ~ | ~<positive-integer>[+] | ~~
```

This notation does not change the existing legal order of name and duration. `x=2read~2` and `x=read2~2` should remain equivalent. Names that need `#` or quotes retain those rules. `!` inside a quoted name is never a repair marker. Placement-looking punctuation inside a literal must remain subject to existing name validation, not be extracted as an operator.

The short teaching model is:

- Before the second `=`: **what session, how long, where in time**.
- After it: **what happened to its tasks**.
- `~`: start at the beginning of the latest gap.
- `~n`: start at the beginning of historical slot `n`.
- `~n+`: end at the end of historical slot `n`.
- `~~`: end immediately before today's first timed session.
- `!` before the second `=`: allow the previewed trim of existing history.

Make the separation concrete:

```text
x=2~1!=!1
  2       request 10 minutes
   ~1     start of the latest completed session
     !    allow trimming that session
       !1 complete task 1 from the chosen source session

x=2~2=~1
     ^ placement slot 2 before the second equals
        ^ existing task-drop selection after the second equals
```

Reject `~0`, `~+`, `~~+`, `~~2`, repeated placement suffixes, negative indices, and overflowing indices. Teach `~0` → `~`, and `~~+` → `~~`. Preserve the count, name, repair permission, and task suffix in every suggested correction. A large missing index should say how many historical slots exist, not clamp to the oldest one.

Bare `~` and `~~` are complete valid forms, not “incomplete until a number arrives.” Typing `+` after a valid `~n` changes alignment without changing slot selection. Partial name literals remain normal incomplete editor states. Replace today's misleading “move this `~` into the task-drop part” diagnostics only in the new placement position.

## Build one explicit slot catalog

Use local wall-clock minutes on the same day coordinate system as the existing planner. Internally represent intervals as half-open `[start, end)` with checked arithmetic. Preserve `1440` for the next midnight until formatting; do not reduce it to `0` during comparisons.

Read the current staged `## Pomodoros` section once for the stack. Scan all timed rows regardless of theme or clock kind. Untimed CHORE/READ/MEET placeholders do not occupy time. A timer's expected endpoint is not permission to treat an open row as completed.

For the ordinary non-overlapping case:

1. Validate relevant timed rows and sort them chronologically, retaining stable source handles and original line numbers for messages.
2. Identify the latest completed row by time, not by physical Markdown position.
3. Give that row index `1`.
4. Walk backward: include each positive gap encountered between timed rows, then each preceding completed row. Open rows are obstacles, not numbered completed slots. Never call an interval containing an open row a free gap.
5. Stop before the leading midnight interval. That interval is addressed only by `~~`; it is not another numeric slot.
6. Build the leading slot `[0, first timed start)` and the trailing slot `[last timed end, T)` when their required boundaries exist and their widths are positive. The latest timed row must be closed for the trailing shortcut to be available. An open final row, including an overdue one, should produce “close the running session first,” rather than inventing free time after its scheduled end.

The historical walk starts at the latest completed row. It does not promise to expose gaps *after* that row but *before* an open timed row; that is outside the supplied reverse-index definition. Such a future extension should be designed explicitly.

For the supplied example:

| Selector | Kind | Interval | Alignment without `+` |
| --- | --- | --- | --- |
| `~` | Latest gap | 09:00–09:15 | Start |
| `~1` | Last completed session | 08:30–09:00 | Start |
| `~2` | Previous gap | 08:00–08:30 | Start |
| `~3` | Previous completed session | 07:30–08:00 | Start |
| `~~` | Before the first timed session | 00:00–07:30 | End |

Adjacent 07:30–08:00 and 08:00–08:30 sessions yield indices 2 and 1 with no gap slot between them. Two session rows remain two slots even if their names match. Do not use odd/even arithmetic to infer whether an index means work or a gap.

### Empty days and boundary cases

| State | Proposed behavior |
| --- | --- |
| Only untimed placeholders | Numbered slots, `~`, and `~~` are unavailable; ordinary `x=` still works. Explain the missing recorded boundary. |
| One first open timed session, no completed session | Numeric slots and `~` are unavailable. `~~` can use the real interval before its start, provided the resulting record is not future work. |
| First timed session starts at midnight | No leading gap; `~~` fails. |
| Latest completed end equals `T` | No trailing gap; `~` fails instead of writing zero minutes. |
| Latest timed row is still open | `~` is unavailable; older non-overlapping historical slots can still be selected. |
| End encoded as `0000` | Treat an otherwise valid midnight-ending row as ending at minute 1440. Reject genuinely ambiguous spans crossing outside the selected day. |
| Minute-level row endpoints, such as 08:02 | Preserve those endpoints. Do not snap history to a grid. Counted duration is still in five-minute units; clipping can produce other actual durations. |
| “Completed” row far beyond `T` | Treat as inconsistent placement history, not a future target for recording past work. |

For `~~`, end alignment is the restriction. I would not add a separate ban on a mathematically valid computed start of 00:00 when an explicitly requested duration exactly fills the prefix. Existing `x=` already allows a start exactly at midnight. If “never start at midnight” was intended as a stronger ban, that would be an additional product rule, not a consequence of choosing end alignment.

DST repeated-hour ambiguity already exists in a ledger storing only HHMM and naive local times. This feature should neither claim to resolve it nor introduce an unrelated timezone migration. Use the current coordinate model and refuse ambiguous interval order where detected.

## Window arithmetic and repair rules

Let the chosen slot be `[S, E)`, its width be `W = E − S`, and the requested duration be `D = 5 × count` (25 minutes when omitted).

| Placement | Proposed result |
| --- | --- |
| No suffix | Preserve current automatic placement and overlap rules. |
| `~` | `[S, min(S + D, E))`; report a shortening when `D > W`. |
| `~n` | `[S, S + D)` if `D ≤ W`; otherwise fail. |
| `~n+` or `~~` | `[E − D, E)` if `D ≤ W`; otherwise fail. |

Every result must have positive duration and lie within today's allowed recording horizon. For the new leading-slot form, additionally reject a resulting endpoint beyond `T`; a future first timer must not make `~~` a way to record future work.

Shortening only for `~` is intentional and directly matches the request. For numbered slots and `~~`, silently reducing a typed ten-minute duration to seven minutes would weaken the meaning of the count. Even an omitted 25-minute duration can produce a useful, explicit “this slot has only 15 minutes; use `x=3~2`” message. A later product decision could make omitted durations adaptive, but it should not be accidental.

A shortened window must update **actual duration everywhere**: row duration, output summary, statistics inputs, close calculation, and preview. Keep the requested count separately. Do not leave `[t:: 25m]` or `[off:: 25m]` on a 15-minute row, and do not force a 13-minute actual span back into an integer count of five-minute units.

Retain `C = min(window.end, captured_now)` for task close effects and Work Logs. Thus the example 09:00–09:15 record closes at 09:13; a 09:00–09:10 record closes at 09:10. The slot selector does not itself select tasks from the historical victim. CHORE's task 1 still comes from CHORE's placeholder even when CHORE takes time from a different completed session.

For occupied slots, preserve the existing `!` discipline:

- Without `!`, show the precise required trim and refuse the write.
- With `!`, preserve a nonempty remainder; never erase a row or leave two disconnected fragments.
- Refuse a duration equal to the whole occupied slot even though it fits the slot geometrically. Fitting a slot does not imply permission to delete its history.
- Reject `!` on a free slot. Do not turn it into a habitually appended override.
- Preserve the old row's children, IDs, clock kind, and completion state. Do not rerun its task outcomes or rewrite its Work Log timestamps.
- Show MEET/calendar identity in a trim preview. Existing calendar trimming remains subject to the same permission; do not add a hidden rule that all MEET rows are uneditable.

The [existing trim implementation](https://github.com/bobs-org/bob-cli/blob/832e124645585118f9c7e42633e05814f70ec59c/src/native/capture/pomodoro_past.rs#L364) already preserves clock metadata and distinguishes calendar rows. The shared close planner also preserves event-task and successor-offer behavior; use it rather than building a second task-completion path.

### All six requested examples

Each row assumes a fresh copy of the example ledger, with CHORE followed by READ as untimed placeholders.

| Input | New window | Existing history changed |
| --- | --- | --- |
| `x=~=!1` | CHORE 09:00–09:15, 15m | None; requested 25m shortened to 15m |
| `x=read2~=!1` | READ 09:00–09:10, 10m | None |
| `x=2~1!=!1` | CHORE 08:30–08:40, 10m | Old 08:30–09:00 → 08:40–09:00 |
| `x=2~1+!=!1` | CHORE 08:50–09:00, 10m | Old 08:30–09:00 → 08:30–08:50 |
| `x=2~2=!1` | CHORE 08:00–08:10, 10m | None |
| `x=2~2+=!1` | CHORE 08:20–08:30, 10m | None |

I checked these six windows with an independent arithmetic script. That verifies the proposed arithmetic against the examples; it does not substitute for implementation tests of source-session choice, task completion, or writes.

## Multiple records: explicit placement opts out of automatic packing

Do not leave stacks unspecified. My preferred rule is:

1. A consecutive run of past records remains one atomic planning group.
2. Resolve every explicit slot against the same pre-stack daily snapshot, including edits already staged by earlier non-stack items such as `x`.
3. Place explicitly suffixed members independently.
4. Pack the **unsuffixed members only**, in their original relative order, backward from `T`, exactly like the existing stack algorithm.
5. Validate all new windows together. New records may touch but may not overlap one another. `!` does not authorize one new record to trim another.
6. Apply source-session/task effects in typed order, then file resulting rows chronologically using existing insertion machinery.

Example at 09:13:

```text
x=alpha2 x=beta1~2 x=gamma1

ALPHA 09:00–09:10   automatic, before GAMMA
BETA  08:00–08:05   explicit slot 2
GAMMA 09:10–09:15   automatic, last unsuffixed member
```

No explicit placement silently becomes a default for its neighbors. Two members targeting the same slot start edge generally overlap and therefore fail; the user must choose distinct intervals or opposite edges that fit. Task numbering and placeholder consumption still follow typed order, so the preview must show each record's resolved task lineup.

For old-history repair, calculate the **actual union of new intervals**, not their bounding envelope. Subtract that union from each old closed row. Zero remainder is erasure; multiple remainders are a split; one nonempty remainder can be retained. Every member that overlaps old history still requires `!`, and each changed old row is reported once. Two explicitly authorized edge takes can leave a single middle remainder; show both takes rather than pretending only one edge changed.

For example, new windows 08:00–08:10 and 08:50–09:00 do not authorize modifying any time in 08:10–08:50. This is the essential regression to guard against.

If scope must be reduced, the safe smaller release is to refuse any multi-member stack containing a suffix, while retaining all existing unsuffixed stacks. Clearly label that limitation. Do **not** approximate mixed stacks with the current continuous-union algorithm. My preferred complete implementation includes mixed placement because its behavior can be defined without adding syntax.

## Make the feature visible and calm

Extend the existing past-work card instead of creating another panel.

For a gap insertion:

```text
Record past work                                  CHORE · 10m
08:00–08:10                        Gap 2 · 08:00–08:30 · Start

Complete  1  Take out recycling
```

For a repair:

```text
Record past work                                  CHORE · 10m
08:50–09:00               Session 1 · 08:30–09:00 · End

Adjust previous session
READ      08:30–09:00  →  08:30–08:50              −10m

Complete  1  Take out recycling
```

For `x=~`, display “15m available · shortened from 25m” beside the actual range. Use the existing theme color for session identity, a lighter outlined treatment for gaps, and textual labels for “Start,” “End,” “Gap,” and “Trim.” Never make fill color the only distinction; this follows [W3C's use-of-color guidance](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html).

While the caret is in the placement suffix, show a compact list with the actual options:

```text
~     Latest gap       09:00–09:15     15m
~1    READ             08:30–09:00     30m   ! required
~2    Gap              08:00–08:30     30m
~3    BUILD            07:30–08:00     30m   ! required
~~    Before BUILD     00:00–07:30           End
```

Rows should reflect the actual names returned by Bob; the example names above are illustrative. Numbering remains derived, never hard-coded into the app. Tab accepts a placement completion; Return continues to submit a valid capture. Choosing an occupied row inserts the placement only, not `!`: selecting time and authorizing a trim should remain distinguishable acts. The ordinary diagnostic then offers the exact repair spelling.

The list should be scoped to the suffix and reuse the existing completion surface. It need not stay open after the caret enters task outcomes. The preview remains useful even for someone who never opens the list.

Do not use a day-wide proportional chart: a midnight-to-morning gap would squash the interesting ten-minute changes. A short focused strip for the selected slot can supplement exact text. For mixed placements, render each full interval or Bob-provided chronological segments. The current Mac presentation joins typed members into a single continuous string; that would misrepresent disjoint windows and must change. See [CapturePomodoroPastPresentation.swift](https://github.com/bobs-org/bob-mac-capture/blob/6c39ff8f754e9e0fb331ddbb387da2c6635c931d/Sources/CaptureCore/CapturePomodoroPastPresentation.swift#L213).

Preview change feedback belongs inline. Apple's [feedback guidance](https://developer.apple.com/design/human-interface-guidelines/feedback) supports matching interruption to the importance of the event. Routine slot selection and a permitted trim need a precise preview, not an additional modal confirmation on every capture.

### Reliable dash-to-tilde assistance

Implement this as a new Rust `capture-rewrite` rule, using the same lexer as execution and highlighting. Extend the Mac's existing rewrite-key allowlists to include `-`; Swift should send intent and apply Bob's returned edit, never decide whether a dash is syntactically a placement suffix.

Expected behavior:

| Typing | Canonical draft |
| --- | --- |
| `x=-` | `x=~` |
| `x=read2-` | `x=read2~` |
| `x=2-1+!=!1` | `x=2~1+!=!1` once the eligible typed alias is normalized |
| `x=--` or a second `-` after `x=~` | `x=~~` |
| `x=2#"DEEP WORK"-1` | `x=2#"DEEP WORK"~1` |
| `x=#deep-work`, quoted name content, task IDs, `=3-1`, standalone `--2`, log text | Unchanged |

An unquoted `#` name can legally contain dashes, so its dash bytes are not an unambiguous suffix trigger. Use a literal `~`, or quote the name before typing the dash alias. Do not infer that the end of a name has been reached simply because a keystroke paused.

Handle fast typing explicitly: `--`, `-1+`, and Return may arrive before the first subprocess reply. A stale reply must never edit a newer draft. The Mac should re-request normalization for the current eligible alias fragment and await pending normalization before submission. Preserve the captured typing intent; do not implement an unscoped “replace every dash before submission” fallback. Canonical `~` remains directly usable when assistance is unavailable. Supporting dash spellings in the CLI parser is an alternative, but I would defer that additional language surface.

Retain native selection, IME composition, and undo behavior. Do not apply assistance inside marked text or turn a stale cursor offset into an edit. Undoing the substitution must not immediately trigger the same substitution again. Apple's [text input architecture](https://developer.apple.com/library/archive/documentation/TextFonts/Conceptual/CocoaTextArchitecture/TextEditing/TextEditing.html) distinguishes inserted and marked text; its [undo guidance](https://developer.apple.com/design/human-interface-guidelines/undo-and-redo) supports reversible editing. The Mac already has generation, draft, cursor, and process-client checks plus native undoable edits; extend those mechanisms rather than replacing them.

## Implementation shape

This is a map of the change, not a request to rewrite the capture architecture.

### Rust owns interpretation and resolution

Add a typed placement value to `PomodoroPastSpec`, conceptually:

```text
RecentEnd                 existing unsuffixed behavior
TailStart                 ~
History { index, edge }   ~n / ~n+
BeforeFirstEnd            ~~
```

Separate lexical intent from resolved intervals. `capture-parse` remains text-only: it can validate syntax and emit a placement span, but it cannot know whether slot 7 exists. A shared resolver used by preview, execution, and placement completion builds the catalog from a snapshot.

Principal touchpoints:

| Area | Files / work |
| --- | --- |
| Lexical grammar | `src/native/capture_language/past.rs`, `model.rs`, `item.rs`: extract the suffix after the base name/count, before repair, without disturbing literals or the second equals. |
| Editor parity | `editor_pomodoro.rs`, editor spans, `completion.rs`: use the shared suffix parser and make name completion preserve placement, repair, and task outcomes. |
| Rewriting | `capture_language/rewrite.rs`, `capture_rewrite.rs`: an idempotent, cursor-scoped alias rule; preserve byte ranges and caret mappings. |
| Slot resolver | A focused new module beside `capture/pomodoro_past.rs`; share its interval catalog with completion rather than duplicating vault interpretation. |
| Batch orchestration | `capture/plan.rs`: read the staged day before computing resolved placement; freeze the catalog for the whole stack. |
| Overlap planning | `capture/pomodoro_past.rs`: validate pairwise new windows and subtract their true interval union from history. Preserve existing trim staging and close machinery. |
| Protocol | `capture_parse.rs`, `capture/output.rs`, completion JSON: additive intent, slot, alignment, requested/actual minutes, and preview expectation data. |
| Documentation | `docs/capture.md`, JSON references, grammar examples, help fixtures: replace offset/drop teaching errors in this position and explicitly document the two numeric meanings. |

Keep existing field meanings where possible. `blocks` remains the requested duration count; `window.minutes` remains actual duration. Introduce a nested placement object with kind, optional index, edge, chosen slot boundaries, and source identities. Keep the old `anchor` field as the existing rounded-current-time reference and add the selected placement boundary separately, rather than silently changing its meaning. Any display grouping for non-contiguous windows should be supplied by Bob.

A useful resolved shape, illustrative rather than a final schema, is:

```json
{
  "placement": {
    "kind": "history",
    "index": 1,
    "edge": "end",
    "slot": {"kind": "session", "start": "0830", "end": "0900"}
  },
  "requested_minutes": 10,
  "window": {"start": "0850", "end": "0900", "minutes": 10},
  "shortened_minutes": 0
}
```

For preview stability, return an opaque expectation identifying the day, normalized draft, selected catalog entries, resolved windows, and trim targets. Recompute and compare it on capture from the same planning snapshot used for writes. Include the rounded horizon when it affects placement, but do not invalidate a purely historical placement just because the seconds changed. On mismatch, return a typed conflict and refreshed preview; keep the draft and require a fresh submit gesture. Do not mutate part of the batch or automatically repeat a destructive submit. The ordinary direct CLI invocation without a preview expectation resolves against its own execution snapshot, as today.

This expectation is a proposed extension, not an existing capability I verified. It closes a specific risk introduced by positional historical references. Existing disk-drift detection still protects the subsequent plan-to-write boundary.

### Swift owns presentation and editing mechanics

Extend optional decoding in `CaptureModels.swift`; use Bob's windows and requested/actual durations in `CapturePomodoroPastPresentation.swift`. Update the existing card and its accessibility labels. Add the dash to both controller and model typing-intent allowlists, which currently enumerate the eligible characters separately. Exercise the fast-input path, not only the steady-state rewrite.

Keep `schema_version` stable for genuinely additive optional fields, while following the project's grammar-version conventions for newly valid syntax. Older Bob should simply leave the dash untouched and report unsupported syntax. A new app must not fabricate a successful placement preview when the installed Bob does not understand the feature. New Bob plus an older app should retain correct capture behavior through the existing window/trim fields; richer slot presentation can degrade gracefully.

Land and verify the Rust contract before enabling the richer Mac UI. Compile all changed Swift targets using the repository's required portable/macOS checks, and watch exact-SHA macOS CI after a push. This report contains no Swift changes and makes no claim that those checks ran.

## Verification that would justify shipping

Use the existing suites, especially [past grammar tests](https://github.com/bobs-org/bob-cli/blob/832e124645585118f9c7e42633e05814f70ec59c/src/native/capture_language/tests/past.rs) and [past CLI tests](https://github.com/bobs-org/bob-cli/blob/832e124645585118f9c7e42633e05814f70ec59c/tests/cli/capture/pomodoro_past.rs). Add tests for behavior and invariants, not a parallel implementation of the resolver.

1. **Required examples:** all six complete tasks and write exact expected ledger bytes, not just the right JSON interval.
2. **Parser/editor agreement:** valid suffixes, repair ordering, both count/name orders, quoted literals, dangling input, oversized indices, and task drops after the second equals. Completing a name must retain all suffixes.
3. **Catalog invariants:** sorted file disorder, consecutive sessions without gaps, no history, one row, zero-length rows, unrelated placeholders, on/off-clock entries, open obstacles, malformed times, and the explicit overlap restriction.
4. **Boundaries:** exact five-minute times, seconds just after a boundary, current-day rollover, `T=1440`, midnight-ending rows, minute-level endpoints, no zero-minute writes, and no cross-day target selection.
5. **Fit policy:** short/long/equal duration in free and occupied slots; only `~` shortens; `!` cannot erase, split, exceed a slot, or touch open work.
6. **Accounting and close effects:** actual row minutes match the interval; preserved `[off::]`/`[t::]`; historical close clocks; event-task classification; Work Logs; carried links; names; successor offers; existing placeholder behavior.
7. **Mixed stacks:** stable numbering across earlier records, unsuffixed-only packing, typed task resolution, true union subtraction, noncontiguous previews, pairwise new-window conflict, and whole-batch rollback if a later member fails.
8. **Concurrency:** preview slot renumbered before submit, clock boundary crossed, day changed, note changed during planning, and task-side write conflicts. No partial writes or silent preview retargeting.
9. **Mac mechanics:** `-`, rapid `--`, `-1+`, immediate Return, undo/redo, caret moves, selections, IME, emoji before the token, stale subprocess replies, quoted/hyphenated names, task-ID dashes, and older/newer CLI combinations.
10. **Output parity:** fixed-clock dry run and execution agree on windows, trims, actual minutes, and task effects. Error and success preview text remain accessible without color.

A particularly valuable property check is that every explicitly placed interval lies within its slot, all new intervals are pairwise disjoint, and total removed old time equals the intersection of old history with the **actual** new-window union. No minute in an untouched gap should disappear because it lies inside a bounding rectangle.

## Alternatives and why I would not choose them first

| Alternative | Advantage | Cost / conclusion |
| --- | --- | --- |
| Absolute clock syntax | Stable across catalog renumbering; exact intent | Requires remembering and typing times; expands the language beyond this request. Useful later if selecting far-back history is frequent. |
| Number only completed sessions; encode adjacent gaps separately | More predictable session indices | Needs another modifier and violates the requested walk through alternating sessions and gaps. The placement list makes the proposed numbering usable. |
| Make `~n` automatically authorize replacement | Shorter input | Removes an existing meaningful distinction between finding time and taking credited time. Keep `!`. |
| Always clamp every selected slot | Fewer errors | Silently changes explicitly requested duration and can still erase a completed session. Restrict automatic shortening to `~`. |
| Apply one suffix to the whole stack | Efficient for laying a sequence into a gap | A local suffix acquires nonlocal scope. It needs a separate deliberate grammar if desired later. |
| Timeline drag editor | Excellent visual precision | Much larger interaction surface and duplicates an existing keyboard workflow. Start with a compact list and card. |
| Swift regex substitution and time computation | Superficially quick | Conflicts with the accepted thin-client contract and creates grammar/preview disagreement. Keep one Rust authority. |
| Permit overlapping-history catalogs immediately | Covers concurrent on/off-clock history | Requires an ownership and ranking policy absent from the request. Reject with precise context initially; revisit with actual examples. |

The governing SASE contracts consulted were `decisions:mac-capture-is-a-thin-client`, `decisions:event-task-links-close-by-the-clock`, `decisions:open-pomodoro-names-follow-task-links`, and `decisions:off-clock-pomodoros-count-apart`, together with the Capture/Pomodoro/Task Link glossary and artifact rules. They constrain the integration; this report does not propose replacing them.

## Recommended solution

**Implement the proposed `~`, `~n[+]`, and `~~` forms as explicit, bounded placement selectors in Rust. Keep duration, placement, and trim permission separate.** Preserve all six examples, clip only the tail-start form, and retain the existing restrictions on editing closed history.

Resolve one chronological slot catalog per atomic stack; give explicitly placed members their own windows while automatically packing only unsuffixed members. Upgrade overlap validation to operate on the real interval union before accepting mixed placements. Preserve close clocks, task outcomes, historical identity, and clock accounting through the existing planners.

Make the experience attractive through a small placement list and an exact, readable preview of the new range and every old-range adjustment. Route contextual dash assistance through `capture-rewrite`, retain native undo and IME behavior, and prevent a stale preview from silently targeting different history. Ship the CLI contract first, then the Mac presentation with version-skew and fast-typing tests.

The syntax is worth adding. Its success will come from making the result easier to recognize than the command is to memorize.
