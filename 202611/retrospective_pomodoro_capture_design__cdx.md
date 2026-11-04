# Retrospective Pomodoro capture: a predictable shortcut with explicit repair

Independent research by **cdx**, 2026-11-04. This report was researched without consulting the other swarm researchers, their reports, or their conversations. Scope: design and implementation advice; no product code was changed.

**Recommendation:** add `x=` as a first-class retrospective capture operation. The idea is good: it makes recording work after the fact almost as easy as starting a timer. Keep the requested examples, use one time anchor for a same-line group, and reuse Bob's existing task-close effects. Change the placement of overlap permission when a close selection is present, and initially allow only repairs that leave each older session as one nonempty interval. Do not implement this as a textual substitution into ordinary start and close commands.

The most important distinction is between **recording a session that already happened** and **controlling the session running now**. Bob already has substantial behavior attached to ordinary start and close. The new command should share their vocabulary without accidentally inheriting their timer control, calendar selection, or reset behavior.

**What I checked.** I inspected bob-cli at `d216f7eb3bdefeaa233b5d0ed288b4c653f2df1a` and the linked Bob Mac Capture checkout at `2940666a76e65545bb3416bced36dd4f1f5c9b67`. I read the capture contract, parser, planner, close-selection and ledger engines, staged writer, relevant tests, and Mac decoding and preview code. I also read the accepted decisions concerning event clocks, sticky lanes, off-clock accounting, successor offers, the thin Mac client, and releases through audited SASE memory reads. Source links below identify the inspected revisions.

I ran eight isolated, read-only capture probes using the installed `bob 0.4.0`, a synthetic vault, `BOB_NOW=2026-11-04 09:21:00`, UTC, an absent configuration file, isolated XDG directories, disabled reference-job kicking, and `--dry-run`. Every original fixture file remained unchanged. The executable's exact build SHA was not established; these are observations of that installed binary, corroborated where noted by the inspected source, not a claim that I built or tested the checkout.

| Probe | Observed result | Design implication |
| --- | --- | --- |
| `=3-3 x` | Closed BUILD at 0910–0925, 15 minutes | Confirms the requested arithmetic in the simple case. |
| `=2-5#build x =3-3#fix x` | BUILD 0900–0910; FIX 0910–0925 | Confirms the two-session target example can be expressed with existing primitives. |
| `=2-2#fix x*3 apollo agent` | FIX 0915–0925; resolved Work Log entry for task 3 | Existing parking and logging are reusable. |
| `=3-3 x`, with closed OLD 0855–0920 | Succeeded with the overlapping new range | The shortcut needs a new conflict check. |
| `=3-3 x`, with CURRENT running 0900–0930 | Restarted CURRENT at 0910–0925, then closed it | A textual macro would operate on the wrong session. |
| `x=3` | Parsed as an ordinary task | Shipping `x=` changes an existing prose interpretation. |
| `=3-3 x0` | Reset BUILD to `()` | Blindly reusing all close behavior can erase the new session. |
| `=3-3 x!` | Accepted the close's complete-all wildcard | A trailing `!` cannot be reserved for repair without resolving an actual grammar conflict. |

The source confirms ordinary unnamed starts can restart the running session or prefer a MEET occupying the start block; named starts can swap the current session; close timing and event classification receive the current clock. The close planner also stamps Work Logs to minute precision. These are reasons to extract reusable primitives, not to call the existing public start/close orchestration unchanged. [Start dispatch](https://github.com/bobs-org/bob-cli/blob/d216f7eb3bdefeaa233b5d0ed288b4c653f2df1a/src/native/capture/pomodoro_start.rs#L877), [close planning](https://github.com/bobs-org/bob-cli/blob/d216f7eb3bdefeaa233b5d0ed288b4c653f2df1a/src/native/capture_pomodoro_close/linked_tasks.rs#L974), [timestamp formatting](https://github.com/bobs-org/bob-cli/blob/d216f7eb3bdefeaa233b5d0ed288b4c653f2df1a/src/native/capture_work_log.rs#L41).

**The product idea is worthwhile, with a narrower promise.** Teach it as “record the last N blocks,” not as “start a timer in the past and then stop it.” The first wording explains the backward arithmetic and makes a running timer irrelevant to target selection. It also avoids suggesting that the operation should replay every historical side effect of a real timer start.

There are two costs worth accepting deliberately. First, appending a later `x=` shifts every earlier session in that line; the preview must display the whole group, not just the current token. Second, `x=` creates history and changes task state together. The default close works queued tasks, so an implicit target is convenient but deserves a visible name and numbered lineup before submission. This remains a good expert capture language; it is not a good place to add automatic guesses about which time or tasks the person meant.

The simple alternative is documenting `=N-N x`, but that retains arithmetic, running-session hazards, and absent overlap checks. An explicit clock-range syntax would be useful for arbitrary gaps and old dates, but it is a larger feature and less convenient for “I just did this.” I would ship the bounded shortcut now, reserving any future explicit-range form rather than inventing another operator in this change.

**Define the grammar so the two meanings of `!` never compete.** I recommend:

```text
x=<E>[!][=<X>] [work-log text]
```

`<E>` may be empty. It contains a positive block count, a Pomodoro selector, or both; omitted count means five blocks. Retain `x=3`, `x=build`, `x=3#build`, `x=build@3`, and exact quoted names such as `x=#"DEEP WORK"@3`. Recognize separators only outside quoted names. The second `=` introduces the existing close-selection body, without its leading `x`. Both omitting that part and spelling an empty part mean a plain close.

**The repair `!` belongs to `<E>`, immediately before the optional second `=`.** Everything after the second `=` belongs to the ordinary close lexer. This is a requirement adjustment, but it preserves every example in the request and preserves all existing close wildcards.

| Input | Meaning |
| --- | --- |
| `x=3!` | Record three blocks and trim overlapping old history if needed. |
| `x==1!2` | Default five blocks; work task 1 and complete task 2; no repair permission. |
| `x==!` | Default five blocks; complete the eligible remaining tasks; no repair permission. |
| `x=3!=1!2` | Three blocks; permit repair; work task 1 and complete task 2. |
| `x=build@3!=!` | BUILD, three blocks, repair permitted, complete-all close selection. |
| `x=!=!` | Default target and duration, repair permitted, complete-all close selection. |
| `x=3=1!` | Work task 1 and complete the other eligible tasks; the final `!` is the close wildcard. |

The original `x=<E>=<X>[!]` cannot preserve every `<X>` meaning: `x=3=!` would mean both complete-all and a plain close with overlap permission. “Peel a final bang off” is therefore unsafe. Doubling it only moves the ambiguity and produces hard-to-read forms. An alternative is keeping `!` exclusively for completion and choosing a new repair symbol, but placing it on the start half is the smallest change with a clear mnemonic: **before the divider, time; after the divider, tasks**. The existing close lexer explicitly accepts empty `!` and `*` wildcard groups. [Close selection lexer](https://github.com/bobs-org/bob-cli/blob/d216f7eb3bdefeaa233b5d0ed288b4c653f2df1a/src/native/capture_language/close_selection.rs#L224).

I would initially exclude numeric offset forms throughout `<E>`: `-N`, `N-M`, and dangling numeric `N-`, including their `@` versions. Named hyphens still work: `x=deep-work` is a selector, not timing. Accept leading zeroes for positive counts consistently with starts, but reject zero duration and overflow. Split/merge operators are not session-start arguments for this feature.

I would also omit start-side `~K` in the first version. Start drops number direct children and delete their subtrees; closes number eligible links at any depth and preserve historical notes differently. Combining both creates two numbering stages inside one tiny token. Close-side `~K` remains supported, with its existing semantics; it is not a byte-identical replacement for start-drop. If start drops are later required, specify both lineups explicitly before adding them. [Start lineup](https://github.com/bobs-org/bob-cli/blob/d216f7eb3bdefeaa233b5d0ed288b4c653f2df1a/src/native/capture_pomodoro_start.rs#L100), [selection contract](https://github.com/bobs-org/bob-cli/blob/d216f7eb3bdefeaa233b5d0ed288b4c653f2df1a/docs/capture.md#L4709).

**Use one anchor and solve the whole line before writing.** Capture `now` once. Match Bob's existing minute precision: discard seconds, then round the minute upward to the five-minute boundary. Thus 09:21 becomes 09:25, and 09:20:59 remains 09:20 under today's implementation. This subtlety must be tested and documented rather than silently changing other session operators. The endpoint is a recorded block boundary, so “past” does not mean every represented minute has already elapsed. [Existing rounding](https://github.com/bobs-org/bob-cli/blob/d216f7eb3bdefeaa233b5d0ed288b4c653f2df1a/src/native/capture/meet_event_run.rs#L200).

For a same-line group with durations `d1 … dn` in minutes and anchor `A`:

```text
end(i)   = A - sum(dj for j > i)
start(i) = end(i) - di
```

Compute intervals right to left; resolve sources and apply task outcomes left to right. These are different passes. Reversing execution would reverse completion effects, continuation selection, task numbering, and Work Log order.

At 09:21, with `A=09:25`:

| Requested input | Resolved result |
| --- | --- |
| `x=build` | BUILD 0900–0925, 25m. |
| `x=build@2 x=fix@3` | BUILD 0900–0910, FIX 0910–0925. |
| `x=2#fix=*3 apollo agent` | Same as `x=fix@2=*3 apollo agent`; FIX 0915–0925, task 3 parked, one Work Log entry. |
| `x==1!2` | First planned source 0900–0925; task 1 in progress and carried, task 2 completed. |
| `x=3!`, with OLD 0855–0920 | New 0910–0925; OLD becomes 0855–0910, 15m. |

In the parking example, “dismiss from the daily file” should mean **remove its live/planned link**, not erase its worked historical link. Existing `*3` records the work, leaves the task In Progress, keeps its historical link under the closed session, and does not carry it. Deleting that historical link would contradict the close behavior the request asks to reuse.

Make one group the consecutive retrospective operators on one physical parent line. Work Log text owned by a retrospective operator does not break its group. Ordinary operators delimit groups; a blank line starts a separate group with its own intervals anchored to the same captured `now`. Consequently, two separate `x=3` lines can overlap and should fail; same-line and blank-line forms are intentionally not equivalent here. Do not silently reach backward across unrelated capture items. Permit a useful trailing normal start, such as `x=build@2 x=fix@3 =admin`, after the group finishes. Reject any resulting overlap with a later group rather than letting repair rewrite a session created by the same capture.

For the first release, retain today's single-inline-Work-Log ownership rule per parent line and attach child bullets to the last retrospective close when there is no inline owner. Do not silently distribute one text fragment across multiple sessions. Multiple separately owned inline logs on one line can be added later with an explicit grammar; a precise error is preferable now. [Existing chain ownership](https://github.com/bobs-org/bob-cli/blob/d216f7eb3bdefeaa233b5d0ed288b4c653f2df1a/src/native/capture_language/draft.rs#L412).

**Select planned sources explicitly, preserving close semantics.** For an unnamed `x=`, choose the first open untimed placeholder in staged document order. Do not restart a running session and do not apply the current-start MEET preference. For a named operation, reuse existing selector normalization, exact literal matching, ambiguity errors, and near-match warnings. Use a matching planned placeholder; otherwise create a new session with the selected canonical name. A completed match supplies its name, not a copy of old task links or old Work Logs. A selector resolving to the running session should refuse with a precise explanation rather than swap it or silently create a duplicate current name.

A matched placeholder becomes the new historical session and goes through normal continuation behavior. Sources resolve left to right against staged state. Therefore `x=2 x=3` may work the same named queue twice when the first close creates a continuation at the top. This is consistent with ordinary sequential start/close behavior, but the preview must show it. If two different sources are intended, naming them is the clear spelling. Do not reserve all initial placeholders up front; that would make continuation and task-state effects depend on an unseen alternate queue.

The duration is explicit or 25 minutes even for MEET. A retrospective MEET must not unexpectedly expand to its calendar run. Calendar tasks can still participate in ordinary close classification; only automatic target selection and duration substitution are bypassed.

Reuse numbered progress, park, complete, drop, wildcard handling, name narrowing, continuation naming, dependency recovery, Work Logs, and explicit successor offers. Normal task effects occur at submission against current task state; this is not historical reconstruction of the vault. Never resurrect a currently completed task to recreate an imagined old state. Successors remain offers, never automatic links, and those offers must participate in the same aggregate transaction.

Reject a reset-only close selection (`0` or `@0` with no other outcomes) in retrospective mode, regardless of whether a note would make ordinary `x0` bypass its reset shortcut. Teach “this operation records a session; remove `=0`, or use `x0` on the running session to reset it.” Keep meaningful combinations such as `0*` and `0*2` using existing selection rules. This explicitly narrows “same arguments as close” to avoid a command whose stated purpose vanishes when executed.

Pass an explicit target and fixed interval into the close engine. Also distinguish the historical effective close time from submission time. For group member `i`, use `Ci=min(real_now, end(i))` for event classification and the historical Work Log timestamp; keep `recorded_at=real_now` in the result. Earlier members close at their earlier endpoint. The final member closes at 09:21 even if its rounded ledger endpoint is 09:25, so a meeting ending at 09:24 is not prematurely completed. This preserves the existing distinction between the clock used for event outcomes and the rounded ledger span. A report of an earlier event ending after that member's endpoint must not be classified using the later submission clock. Keep these inputs separate rather than globally replacing `BOB_NOW`.

**Overlap repair needs a complete interval policy.** Treat spans as half-open `[start,end)`, so adjacent sessions do not conflict. Two nonempty intervals overlap when `max(start1,start2) < min(end1,end2)`. This is a conventional scheduling representation: iCalendar gives events an inclusive start and non-inclusive end, and PostgreSQL's range model explicitly represents inclusive/exclusive boundaries and disjoint multiranges. These references support the interval representation, not a proposal to add either technology to Bob. [RFC 5545 §3.6.1](https://www.rfc-editor.org/rfc/rfc5545#section-3.6.1), [PostgreSQL range types](https://www.postgresql.org/docs/current/rangetypes.html).

Check every timed closed session intersecting the requested windows, including named, unnamed, on-clock, off-clock, and legacy unstamped history. Check timed open sessions too, but never steal time from them, even with `!`. An active interval ending exactly where a new one begins is adjacent; otherwise refusal should show both ranges. Planned untimed placeholders occupy no clock interval. Existing old-old conflicts outside the requested window are not repaired as a side effect.

Without the start-half `!`, any old-history intersection is an error and the whole capture writes nothing. With it, each applicable token must actually overlap eligible pre-existing history; otherwise return an unnecessary-permission error. Validate this against the stable pre-group history before applying any trims, so an earlier token's repair cannot make a later required `!` appear unused.

Calculate each old session's residual as `old_interval minus union(new_intervals)`. Then apply this policy:

| Residual of an old session | First-release behavior |
| --- | --- |
| Same old interval | No edit; a token that needs no repairs must not carry `!`. |
| One nonempty interval | Permit with `!` on every new token that overlaps it; update old endpoints and duration once. |
| Two nonempty intervals | Refuse even with `!`: this would split one historical session. |
| Empty | Refuse even with `!`: this would erase all of that session's time. |
| Cannot determine interval reliably | Refuse rather than skip an unknown conflict. |

For example, new 0910–0925 trims OLD 0855–0920 to 0855–0910. A prefix trim is also valid when it leaves one positive remainder. If OLD is 0900–0930, however, removing 0910–0925 leaves 0900–0910 and 0925–0930. Keeping only one loses real recorded time; joining them misrepresents the clock; cloning the row risks duplicating child history and session counts. Fully replacing an old row has the same ownership problem. These cases merit a separate history-editing design, not a clever fallback in a capture suffix.

This restriction is the largest proposed scope adjustment. It is preferable to silently deleting rows, manufacturing zero-minute remnants, or duplicating task histories. If arbitrary stealing is a hard requirement, the implementation must first specify stable session identity, split-session statistics, ownership of notes and links across fragments, and full-coverage archival. Merely adjusting two HHMM fields is insufficient.

A successful trim changes only the old row's range and its corresponding duration metadata. Preserve its existing clock classification, name, checkbox, block ID, children, and note bytes. Do not re-close it, rerun completion effects, duplicate Work Logs, recompute its clock from today's tags, or transfer its tasks into the new session. For old `[t::]` or `[off::]`, update the same key. Legacy unstamped history should retain its representation while its span changes. Refuse internally inconsistent timing metadata until it is repaired explicitly.

Use actual minute intervals, not five-minute rounding of old history: old calendar spans need not be block-aligned. Trims must conserve old minutes: retained minutes plus intersection minutes equals the original duration. The new interval gets its own normal clock classification from its retained task links. Moving minutes between worked and off-clock sessions can therefore change the worked total while leaving total occupied time consistent. It must be visible in the preview. Existing total statistics can double-count overlap, which makes checking both clocks essential.

For the first version, constrain the whole group to today's representable local day: `0 <= start < end <= 1440`. An endpoint of 1440 may render as 0000 only with the canonical date and duration preserving its meaning. A group beginning yesterday must refuse with a clear date-boundary error. Never perform collision arithmetic on modulo-1440 HHMM values. Ambiguous or nonexistent local times around a daylight-saving transition also need an explicit refusal until the ledger can represent the relevant distinction. An arbitrary-day backfill feature should be designed separately.

**The preview should make this feel like recording work, not editing syntax.** Show one “Record past work” card per group with chronological rows, exact times, durations, and each resolved source name. Avoid separate “Started” and “Closed” cards for a session that never became the current timer.

```text
Record past work                                  25m

09:00 ───── BUILD · 10m ───── 09:10 ───── FIX · 15m ───── 09:25

BUILD    09:00–09:10    10m
FIX      09:10–09:25    15m
         3  Apollo agent task    Parked · +1 Work Log

Recorded through the 09:25 block
```

The timeline is explanatory, not an additional editable time control. Text rows remain authoritative and accessible. On a narrow panel, collapse the timeline first and retain names and ranges. Use existing theme hues; reserve amber for an authorized time trim and red for a refusal. Do not communicate permission only through color.

When repair is needed, the refusal should already describe the proposed change:

```text
0910–0925 overlaps OLD by 10m.
Add ! before the selection divider to keep OLD at 0855–0910.
```

After `!`:

```text
OLD    08:55–09:20 → 08:55–09:10    10m reassigned
NEW    09:10–09:25                  15m recorded
```

If the requested repair is unsupported, show that fact rather than recommending a suffix that cannot succeed. An unnecessary `!` should say which token has no overlapping time. The suffix itself supplies explicit repair intent; an extra modal confirmation for every valid trim would undermine capture. Return should submit one atomic capture after any existing successor/inbox choices are resolved.

Completion must show the retrospective target's lineup, not the running session's lineup. `x=#` and incomplete literal names should behave as calm picker states. After the second `=`, reuse the close selector UI, including wildcards, parking, completion, drop, and log targets. Add a distinct semantic span for repair permission so its visual role cannot be confused with `!2`.

Bob must compute the intervals, target mapping, error ranges, repairs, and task outcomes. Swift should only decode and present them. The current client already renders Bob's resolved start/close objects and has dedicated semantic categories and picker needs, so this is a real client feature, not a claim that new JSON automatically yields a good preview. [Mac models](https://github.com/bobs-org/bob-mac-capture/blob/2940666a76e65545bb3416bced36dd4f1f5c9b67/Sources/CaptureCore/CaptureModels.swift#L1453), [preview rendering](https://github.com/bobs-org/bob-mac-capture/blob/2940666a76e65545bb3416bced36dd4f1f5c9b67/Sources/BobMacCapture/CapturePanelView.swift#L4365), [span mapping](https://github.com/bobs-org/bob-mac-capture/blob/2940666a76e65545bb3416bced36dd4f1f5c9b67/Sources/CaptureCore/CompletionRowContent.swift#L145).

**Implement one planned operation with reusable close internals.** Add a typed retrospective spec and a shared lexer rather than constructing strings that imitate commands. It should preserve raw input ranges, duration, selector, repair intent, existing close selection, and Work Log entries. Recognize `x=` before prose fallback and before ordinary close near-miss handling. Share parsing between execution, `capture-parse`, completion, and rewrite, including quoted-name masking and UTF-8 byte ranges.

Retain group identity through draft splitting. Today's splitter creates independent items for chained tokens; a later summation pass needs to know which retrospective tokens share a physical-line group. Compute checked cumulative durations before per-item planning. One logical result per `x=` can remain compatible with batch presentation, with an additive group identifier and one group summary.

A useful internal shape, offered as architecture rather than a finalized wire schema, is:

```text
RetrospectiveSpec { selector, duration_blocks, repair, close_selection, log, source_range }
RetrospectiveGroup { members, anchor, intervals }
CloseContext { target_handle, fixed_interval, effective_close_at, recorded_at,
               allow_reset: false, continuation_policy }
HistoryTrim { target_handle, before_interval, after_interval, removed_minutes, clock }
```

Refactor the close core to accept an explicit entry and close context. Keep the existing `find_running_pomodoro` wrapper for ordinary `x`. Avoid a fake in-memory running row that causes global “find current” calls to select or conflict with the actual running session. The current low-level ledger planner already accepts a `RunningPomodoro` entry descriptor, but the higher-level close planner finds it globally; that is the practical seam to improve. Preserve and use block tracking so inserting a historical row cannot make a later line number identify the wrong source.

Plan group intervals and collision residuals before staging any of that group's history repairs. Resolve and apply source/task effects left to right against the shared staged vault. Place new historical blocks chronologically, preserve unrelated block order, and keep active and planned rows in their proper ledger slots. Normal task completion may still update links according to its existing contract; the prohibition is against commandeering the active session's identity or timing.

Run all task notes, daily-row trims, new history, continuations, and selected successors through `CaptureBatchPlanner` and the existing shared writer. Any invalid index, bad name, unresolved required task, unsupported overlap, failed log target, or failed write aborts the aggregate capture. Existing warning-only task-resolution behavior should remain consistent where normal close already permits it; do not accidentally turn every unresolved historical mention into a new hard error.

The existing writer validates planning preimages, stages replacements, and rolls back failures, but its own comment explicitly says it is not cross-process locking or full serialization. Do not claim database-style atomicity or crash durability. Retain its guards and extend guarded reads to every fact that determines a destructive trim or target selection. For cooperating capture processes, reuse an applicable vault write lock if available; verify its scope before adding another one. Concurrent Obsidian edits still require stale-preimage detection and a clean retry. [Batch snapshots](https://github.com/bobs-org/bob-cli/blob/d216f7eb3bdefeaa233b5d0ed288b4c653f2df1a/src/native/capture/batch.rs#L5), [writer and explicit race limitation](https://github.com/bobs-org/bob-cli/blob/d216f7eb3bdefeaa233b5d0ed288b4c653f2df1a/src/native/capture/commit.rs#L167).

A preview is a separate process from submission. Replanning at the next five-minute boundary could shift all ranges or steal different time. The Mac should refresh when the anchor changes and submit a Bob-issued fingerprint covering the displayed intervals, source identities, lineup identities, selections, and history edits. Bob recomputes and refuses a materially changed plan with a structured stale-preview result; the panel refreshes without writing. This requires a deliberately designed request contract, not Swift-side clock math. A direct CLI call can capture its anchor once at execution without requiring an interactive preview. Do not treat `!` as a durable authorization to repair whatever happens to exist later.

Expose additive result data for `pomodoro_past` (or an equally explicit name): anchor, effective close time, recorded-at time, resolved interval, source, normal close outcome, and history trims with before/after block references. Use structured errors such as `past_overlap`, `past_repair_unused`, `past_repair_would_split`, `past_repair_would_erase`, `past_overlaps_running`, `past_crosses_day`, and `past_reset_not_supported`, each ranged to the relevant token. These names are proposals. Preserve existing JSON fields and test older-client behavior; tolerant decoding alone does not make a new operation semantically understood.

Because `x=3` is currently prose, treat claiming the prefix as a capture-language compatibility change. Keep mid-body text such as `Discuss x=3` and a documented capitalized escape as prose. Malformed leading `x=` should produce a useful error rather than unexpectedly writing a task. Ship bob-cli and its capture docs first, then the capable Mac presentation; follow the daily release train and mark the breaking CLI contract as required. No manual version or changelog edits are needed.

**Verification should target observable invariants.** I checked a small independent model of the proposed arithmetic: 2,000 valid three-session groups and 301 interval intersection/subtraction cases satisfied adjacency, anchor, duration, and minute-conservation assertions. This validates the design algebra only. The feature is unimplemented and no checkout test suite or Swift build was run for this research.

The implementation needs the following acceptance coverage:

| Area | Essential cases |
| --- | --- |
| Requested behavior | All five user examples; both FIX spellings produce equivalent plans and task effects. |
| Grammar | Bare/default, named/count aliases, exact quoted and Unicode names, empty second part, wildcard `!`, repaired `!=!`, repeated bangs, dangling selectors, unsupported offsets, zero/overflow, ordinary prose escapes. |
| Time | Every minute in a five-minute bucket; seconds at boundary minutes; three or more sessions; appended member shifts earlier members; midnight terminal endpoint, crossing yesterday, DST ambiguity. |
| Grouping | Single and multiple members; ordinary trailing start; separate lines overlap; inline owner and child bullets; errors identify the correct member and preserve UTF-8 ranges. |
| Targets | Empty ledger, missing day/section, multiple running entries, active nonconflict, active conflict, same-name running refusal, exact/prefix ambiguity, named-again without copied historical tasks, repeated unnamed continuation. |
| Task effects | Progress, park, complete, drop, wildcard, deferred/embedded/nested links, completion of already-done tasks, reset-only refusal, one Work Log only, name narrowing, successor offers, no unwanted lane lowering. |
| Event clocks | Earlier group member classified at its endpoint, final member at real now, not-yet-ended meeting inside rounded final block, explicit picks overriding defaults. |
| Collision geometry | Disjoint, endpoint-touching, tail/prefix trims, containment, exact coverage, multiple old rows, group union fully covering a row, unused `!`, no repair of newly created same-capture history. |
| Accounting | Existing `[t::]`, `[off::]`, legacy unstamped spans, odd-minute endpoints, mixed clocks, unchanged old children/statuses/logs, recomputed old duration and downstream stats. |
| Transaction and client | Dry-run/submit equality at fixed time, late member failure leaves every file unchanged, changed preimage refusal, injected rename failure, preview boundary refresh, stale fingerprint refusal, stable block refs, unsupported client/server combinations. |

For unchanged ordinary operations, retain the current start/close and shared event fixtures as regression tests. Compare complete affected file contents, not just headline strings. Use one shared set of retrospective contract vectors for parser, planner, and Swift decoding/presentation. The eventual Mac changes must be compiled and checked according to that repository's instructions; Linux-only validation is insufficient for macOS UI targets.

**The requirement adjustments are deliberate.** Keep the requested one-operation behavior, all supplied examples, backward packing, no-overlap default, repair warning, and unnecessary-repair error. Adjust or constrain the following:

1. Put repair permission before the second `=`, preserving the full close-selection grammar.
2. Define `<E>` as duration and selector initially; exclude numeric offsets, split/merge, and start-side drop lists.
3. Make sources planned placeholders or new named sessions; bypass running-session override and implicit calendar selection/duration.
4. Reject zero duration and reset-only close selections.
5. Permit only trims leaving one nonempty old interval; refuse split and full erasure even with `!`.
6. Protect timed open sessions and same-capture new history from repair; check both clocks.
7. Bound the first version to one local day, explicit group boundaries, and today's single-inline-log ownership rules.
8. Define retrospective event/log time separately from the rounded ledger endpoint and real submission time.

**Recommended solution:** ship `x=<E>[!][=<X>]` as a dedicated, previewable “record past work” operation, with fixed same-line intervals computed from one rounded anchor and task effects applied left to right through the existing close engine. Deliver exact ranges, resolved task outcomes, and before/after history trims in Bob's JSON, then render a compact chronological card in Mac Capture. Preserve every requested example, constrain repair to nonempty contiguous remnants, and make unsupported history surgery explicit. That delivers the convenience of the proposed shortcut while keeping its timing, task effects, and corrections understandable enough to trust.
