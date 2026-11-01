# Supplemental Pomodoros: preserve the time, protect the work totals

Independent research and design recommendation by **cdx** · 2026-11-01

**Recommendation:** adopt the idea, using **Supplemental Pomodoro** as the product term and `[u:: Nm]` as its ledger representation. Keep `[t:: Nm]` for regular time. Offer **Regular / Supplemental / All** in the time section of Stats, while preserving existing work metrics. Determine classification from participating Task Links when writing a session; preserve that classification once the session closes.

The most important adjustment is to qualify “iff all its task links”: require a **nonempty, fully resolved set of participating Task Links, evaluated at the committed write**. Future calendar tasks waiting in the same MEET queue are not participation in the current session. Later tag edits must not silently rewrite past accounting.

This is a research proposal, not an implementation or accepted decision. It includes a proposed glossary entry; no canonical memory or product code was changed. I did not consult any other report, transcript, or finding from this swarm.

## 1. What exists, and why this is a good change

The approved `bob-cli-f6` epic is still in progress. At inspection, phases 1, 2, 3, 5, and 7 were closed; phases 4, 6, and 8 were in progress. Its chosen `untracked_counts = exclude` branch explicitly removes untracked sessions from both time and session counts. The implementation retains clock spans but omits `[t::]`. Its accepted decision preserves a useful separation: task tags are inputs to writers, while the ledger is the record consumed by readers. [S1–S3]

This leaves a gap between two valid questions:

- **How much regular work did I record?** Lunch, appointments, and other excluded activities should not inflate that number.
- **What occupied my recorded day?** Those same activities provide context for capacity, scheduling, and understanding a week.

A second accounting class answers both without treating a dentist visit as work or erasing its duration. The benefit is context, not a new productivity score. Supplemental time should have a neutral trend: more is neither automatically better nor worse.

There is precedent for recording duration independently of inclusion in a primary total. Clockify reports time entries with a billable/non-billable distinction; Toggl supports filtering by billable status. This is a structural analogy, not a recommendation to introduce billing concepts into Bob. [Clockify Summary report](https://clockify.me/help/reports/summary-report), [Toggl report filters](https://support.toggl.com/en-us/article/using-filters-in-toggl-track-reports-18575d8/).

### Findings that affect the design

| Finding | Evidence | Implication |
| --- | --- | --- |
| Timed rows with `[t::]` or a legacy stopwatch are tracked; absence means untracked. | `SessionTracking` and `duration_from_range_text`. [S4] | Add explicit supplemental duration; do not restore span fallback for regular totals. |
| Stats skips untracked sessions before metric evaluation; session facts give them zero minutes. | `stats/metrics.rs`, `stats/session_facts.rs`. [S5] | A toggle alone cannot recover correct totals; parsing, attribution, and report facts need changes. |
| Start classification is MEET-specific and uses an event run, not every queued task. | `capture/meet_event_run.rs`. [S6] | Generalizing to ordinary tasks is substantive behavior work. |
| Closed calendar imports can create overlapping regular and untracked MEET rows. | Approved plan and `gcal/plan.rs::cluster_past`. [S1, S7] | All recorded duration is not necessarily unique elapsed time. |
| Stats already distinguishes missing/not-yet-tracked data from zero and treats today provisionally. | `docs/stats.md`. [S8] | New history needs quality and coverage rules. |
| Obsidian fetches `bob stats show -a -f json`, caches by argv, and renders server facts. | Stats data/block fragments. [S9] | One report can provide all three views for immediate local switching. |
| The inspected plugin writer emits `[t::]` and preserves other metadata. | `020-time-and-pomodoro.js::durationMetadata`. [S10] | Old writers could create stale or dual fields; additive JSON alone does not make vault writes safe. |
| Mac models already decode `tracked`, `untracked_count`, and event `untracked`. | `CaptureAgendaModels.swift`. [S11] | Preserve legacy meanings and add facts; Swift must not classify tasks. |

These are snapshot findings. The plugin finding is a compatibility risk in an actively changing epic, not a claim that its unfinished phase has failed.

## 2. Names and proposed glossary entry

Use **Supplemental Pomodoro**, with **supplemental time** for its duration. Call existing `[t::]` time **regular time** and the combined measure **recorded time**.

“Untracked” becomes misleading once duration is deliberately recorded. “Personal,” “leisure,” and “non-work” assume why something was excluded. “Background” suggests concurrency or reduced attention. “Off-budget” collides with existing plan-budget concepts. “Supplemental” describes the accounting relationship without claiming the activity is less valuable.

Keep `#untracked` as the existing input spelling and `u::` as the compact storage spelling. Render the friendly term with discoverable help: **“Supplemental — recorded separately; excluded from regular work totals. Set with #untracked.”** Avoid introducing a second tag in this release: equivalent tags create unnecessary sync and removal rules.

### Proposed glossary: Supplemental Pomodoro

> A **Supplemental Pomodoro** is a Pomodoro whose duration is recorded separately from regular work time. Bob assigns this class when the session has at least one participating Task Link and every participating link resolves to a task carrying the standalone `#untracked` tag. Any task type or session name can qualify. An open session's class is provisional; closing records its duration as `[u:: Nm]` instead of `[t:: Nm]` and freezes the class. Supplemental sessions appear in Supplemental and All time views, but do not contribute to regular work minutes or counts. Future queued tasks and incidental mentions are not participating Task Links, and later task-tag edits do not reclassify closed history.

Discovery aliases: **untracked Pomodoro**, **untracked session**, **supplemental session**. Canonical memory should link the Pomodoro and Task Link terms. The lifecycle qualification belongs in the definition.

Adopt this entry with implementation. The Event Task glossary and `untracked-sessions-omit-t-field` decision also need explicit updates/supersession: their “off the clock” and zero-minute claims would no longer describe the new behavior. Preserve the accepted decision's original rationale and mark it superseded rather than rewriting the rationale. This report proposes those changes; it does not publish them as current truth.

## 3. Classification: make the rule precise

Let `L` be the distinct participating Task Links in the session being committed:

```text
supplemental(L) = L is nonempty
                 AND every link resolves uniquely to a task
                 AND every resolved task has the standalone #untracked tag
```

Classification is a session-level choice. It does not divide mixed-session minutes according to the number of tagged tasks.

| Participants | Automatic class | Reason |
| --- | --- | --- |
| One tagged ordinary task | Supplemental | Calendar residence and MEET are irrelevant. |
| Several tagged tasks | Supplemental | All participants opt out of regular totals. |
| Tagged and untagged tasks | Regular | Mixed sessions follow the requested all-links rule. |
| No Task Links | Regular | Empty-set universal truth must not exclude unlinked work. |
| Tagged task plus unresolved/ambiguous link | Regular, with diagnostic | Failure to resolve is not evidence that all tasks opted out. |
| Duplicate links | Same as one link per task | Deduplicate by resolved identity. |
| Incidental mention, dependency/relation link, fenced example | No effect | Reuse the canonical Task Link grammar. |
| Linked done or archived task | Its tag still participates | Completion does not erase its participation. |
| `#untracked/foo`, code text, or link text mentioning the tag | Does not qualify | Match a standalone token, not a substring or inherited tag. |

Extract the existing token exclusions and case-insensitive recognition from `event_task::line_has_untracked_tag` into a shared task-level helper. Reuse canonical link resolution, including same-note links, supported aliases, archives, and ambiguity diagnostics. Do not invent a separate wikilink scanner for stats. [S12]

A single untagged participant makes a long mixed session regular. This is simple and auditable but does not establish minute-by-minute activity. Explain it in session detail: **“Regular · includes 1 task without #untracked.”** If distinct accounting is wanted, close one session and start another. Do not fabricate a 50/50 split from two links.

### Queue membership is not participation

The existing MEET lineup can contain an untracked lunch followed by a regular meeting. Applying the literal predicate to every link under that open MEET would make lunch regular before it starts. The current event-run design avoids that. [S1, S6]

Preserve the distinction:

1. At start, ordinary sessions use assigned Task Links; calendar-aware starts use the active event run plus any other participating non-event links. Deferred future events do not determine the current class.
2. While open, supported link and tag changes refresh provisional classification. Timing-only operations preserve duration and its correct field.
3. On close, finish event selection, parking, drops, and deferrals first. Classify the links that remain as session history using the transaction's staged task snapshots. A worked link also carried to a later session still participates in this session.
4. Atomically write `t::` or `u::` with the finalized history. A future event must not remain a false participant merely because it shares a MEET queue.

The close planner already distinguishes Worked, Mentioned, Deferred, Dropped, Struck, and Embedded roles and removes deferred/dropped rows from closed history. Use those roles and the existing session-link contract; “carried” does not mean “not worked.” [S13]

Do not add a second open MEET with the same name just to classify time: the approved plan explicitly avoids that duplicate-name problem. If the existing planner cannot identify participants reliably, resolve that before enabling the generalized rule.

### Preserve closed history

Readers use the recorded field, not current tags. Moving, archiving, deleting, or retagging a task next month must not change last month's class or duration. Home attribution can retain its existing behavior; this proposal freezes time classification, not every dimension Bob derives.

A deliberate edit of the closed ledger field is a historical correction. A later task-tag edit is not. A managed reclassification action should preview the change and preserve recorded duration; normal reconciliation should not rewrite closed rows. Explicit reopening returns the session to provisional classification, with a visible preview.

For raw Markdown edits, refresh the proposed class in the display and reconcile at the next supported transaction/close. Avoid background rewrites on each keystroke. The strict iff invariant is therefore guaranteed at managed writes, not at every intermediate state of a manually edited file. This is a deliberate reliability adjustment.

## 4. Representation: accept `u::`, model one duration internally

```markdown
- [x] (**0900-0930** [t:: 30m]) — BOB
  - 🍅 [[bob#^fix-sync]]

- [x] (**1200-1300** [u:: 60m]) — MEET
  - 🍅 [[#^lunch]]

- [x] (**1700-1745** [u:: 45m]) — BODY
  - 🍅 [[body#^gym]]
```

`u::` belongs on the Pomodoro headline, not the linked task. It records this occurrence's duration, not a lifetime accumulation on the task. The tag is the classification input.

| Alternative | Assessment |
| --- | --- |
| Keep omitting duration and infer clock spans | Cheap, but conflates recorded values with estimates and makes omission carry two meanings. |
| Put every duration in `t::` plus a class field | Normalized from scratch, but existing readers would count supplemental time as work unless all migrated. |
| Mutually exclusive `t::` / `u::` | Best fit: readable, preserves regular totals for existing `t::` readers, and records class locally. |
| Derive class from current task tags during reporting | Rewrites history and expands resolution requirements across readers. Reject. |
| Encode it as a theme/name | Confuses accounting with subject matter and conflicts with composition and attribution. |

Use a typed internal model, conceptually:

```text
SessionTime = Placeholder
            | Recorded { class: Regular | Supplemental, minutes }
            | LegacySupplemental { span_minutes }
            | Invalid { reason }
```

Avoid independent optional `t_minutes` and `u_minutes` that downstream code might sum. Both classes use the same parsing, arithmetic, split rounding, and formatting machinery.

### Parsing and writer invariants

- A new timed row has exactly one valid duration field; placeholders have neither. Preserve existing regular zero-duration behavior. Zero must not become missing or an invented 24-hour session.
- Valid `t::` means regular, valid `u::` supplemental; the legacy stopwatch remains regular. Conflicting class encodings, duplicate canonical fields, and malformed values need diagnostics. Preserve explicitly documented precedence for preexisting legacy encodings until a separately tested migration changes it.
- In particular, `t::` plus `u::` is invalid. Reports identify the row and mark affected totals incomplete; managed edits refuse until corrected rather than choosing one or summing both.
- Generalize metadata removal so an adjustment cannot retain stale `[u:: 45m]` while adding `[t:: 50m]`.
- Changing class moves the **recorded number**. A 60-minute span with 45 recorded minutes must remain 45. The current `set_ledger_tracking` can restore duration from the span, so it is not the appropriate conversion implementation. [S4]
- Shift-only operations preserve duration and class; extend/shorten/close use existing timing rules with the correct field. Splits conserve recorded minutes with deterministic remainders. Swaps preserve kept duration while resolving destination participants.
- Non-MEET and unnamed sessions can qualify. All-day calendar context without a timed Pomodoro does not invent supplemental minutes.

A targeted source search found no existing `u::` support in the inspected duration/stats paths. That does not prove the live vault has no user-authored `u::`. Before rollout, inventory existing uses and conflicts read-only.

## 5. Stats: three views, stable metrics

The selector changes **the time view**, not every metric on the page. Created, Done, review answers, habits, and task flow do not become “untracked tasks” when viewing supplemental time.

| Metric | Meaning | Direction |
| --- | --- | --- |
| `worked` | Existing regular minutes | Existing setting |
| `sessions` | Existing regular session count | Existing setting |
| `supplemental_time` | Supplemental recorded minutes | Neutral |
| `supplemental_sessions` | Supplemental closed sessions | Neutral |
| `recorded_time` | Regular plus supplemental recorded minutes | Neutral |
| `recorded_sessions` | Regular plus supplemental closed sessions | Neutral |

Implement these using the existing `kind: pomodoro` machinery with a parameter such as `time_class: regular|supplemental|all`, defaulting to regular. This spelling is proposed, not an existing API. Custom metrics can explicitly select a class. Existing formulas keep their meanings: a formula referencing `worked` does not change because the UI control moved.

Compute requested classes from one vault snapshot. The dashboard can continue requesting all visible metrics and locally select the corresponding time metric and server-computed panels. No new process is needed per click. Explicitly requested metrics should remain available even when hidden from the normal metric list.

### CLI proposal

```sh
bob stats                         # existing regular view
bob stats --time supplemental      # supplemental time view
bob stats --time all               # all recorded time view
bob stats -t supplemental -r 7d
bob stats show supplemental_time supplemental_sessions
bob stats show recorded_time -c -f json
```

Add `--time/-t` to the overview/bare view. The alias is unused in the inspected CLI. Keep help alphabetical. Do not overload `--all/-a`: `stats show -a` already means all visible metrics.

Detailed `show` should use stable metric IDs. Do not let `show worked --time supplemental` reinterpret Worked: either omit this overview-only option from `show` or issue a targeted error naming `supplemental_time`.

Terminal headings say **“Supplemental time · 7 days”** or **“Recorded time · all classes.”** Combined output gives a breakdown: **“7h 15m recorded · 5h regular + 2h 15m supplemental.”** CSV keeps the distinct metric IDs, including when exporting an overview selected by `--time`.

### Attribution and invariants

Reuse home/root/project and theme attribution, including deterministic rounding. Supplemental time needs actual shares instead of the current zero-minute `homes` values. Do not create a home called “Untracked”: this class cuts across homes and themes.

For valid, complete data with identical filters:

```text
recorded minutes = regular minutes + supplemental minutes
recorded sessions = regular sessions + supplemental sessions
sum(home parts) = selected metric total
sum(theme parts) = selected metric total
```

Check daily, grouped, prior-comparison, and summary values. Preserve the exclusion of open sessions from actual metrics and the separate provisional-today point. A planned 60-minute session is not 60 minutes already spent. A fully observed day with no matches is zero; absent data is not.

### JSON compatibility

Add new facts without redefining old ones:

- New metrics and their `time_class` parameters are additive.
- Session facts gain `time_class`, `recorded_minutes`, and duration source/quality. Keep the old session `minutes` regular-only during migration so an unaware Day strip does not add supplemental time.
- Supply supplemental attribution separately or in an opt-in versioned accounting object. Do not silently replace old untracked `homes.parts[].minutes = 0` with 60 for unaware consumers.
- Preserve legacy `tracked: false` as “excluded from regular totals.” Add a class fact rather than flipping it to true because duration is now recorded.
- Keep `completed_summary.minutes/count` regular; add supplemental and combined totals.
- Expose a capability signal. Old backends should show an update requirement, not a convincing zero supplemental chart.

Schema 1 can remain if additions preserve semantics. If old fields are replaced, version the contract and coordinate clients. A semantic change is not compatible merely because new keys were added elsewhere.

## 6. A quiet, coherent dashboard

Put a three-part segmented radio control beside the time heading. A binary “include untracked” toggle cannot express supplemental-only.

```text
TIME                                  Last 4 weeks    ‹   ›
[ Regular ] [ Supplemental ] [ All • ]

Recorded time
        7h 15m
5h regular  ·  2h 15m supplemental

[ daily bars: solid regular + patterned supplemental ]

Where the time went                   By root ▾
JOB        ███████████                       3h 30m
BOB        █████                             1h 30m
BODY       ▧▧▧                               1h 15m
LOVE       ▧▧                                  1h

Selected day: Thu 29
12:00–13:00  MEET   Supplemental   1h       LOVE
17:00–17:45  BODY   Supplemental   45m      BODY
```

This is an illustrative layout, not measured user data. Bob supplies totals, displays, proportions, and attribution; the client paints them.

- Start on **Regular**. Remember selection for the Stats view during the app session, without changing CLI defaults, unrelated dashboards, budgets, or goals.
- Scope only the time section. Non-time tiles remain unchanged; fixed custom metrics keep explicit labels rather than pretending to follow the selector.
- Preserve date range, grouping, pinned date, and home navigation. If a selected day has no matches, keep it selected and show an honest empty state.
- Preserve root/theme hues. Use **solid versus outlined/patterned treatment plus text** for class. Reuse the existing dashed calendar language but replace timer-off imagery and text that imply duration is absent.
- All uses stacked daily bars with a regular/supplemental legend and exact hover/focus values. Single-class charts stay simple. Home panels follow the chosen metric; details can expose class components without adding six competing headline cards.
- Supplemental/All comparisons are neutral: “45m more than the previous period,” not a success arrow.
- Regular can have a subtle **“+2h 15m supplemental”** link beside its total to make the feature discoverable.
- Ledger and agenda labels say **“60m · Supplemental”**, with **“Recorded separately from regular work totals”** in the tooltip. Avoid zero-minute home chips.

Use a labeled radio group, visible keyboard focus, standard arrow/Space behavior, and accessible class text. Do not rely solely on color. Respect reduced motion and avoid layout shifts. These choices follow the [WAI radio-group pattern](https://www.w3.org/WAI/ARIA/apg/patterns/radio/) and [WCAG use-of-color guidance](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html).

Visual acceptance should cover narrow/wide, light/dark, increased contrast, reduced motion, keyboard use, no history, all-supplemental days, mixed days, and partial data.

## 7. Two accounting traps

### Overlap: recorded duration is not unique occupied time

The importer deliberately permits closed MEET clusters with different classes to overlap. Consider regular 12:00–13:00 and supplemental 12:30–13:30:

| Quantity | Minutes |
| --- | ---: |
| Regular recorded time | 60 |
| Supplemental recorded time | 60 |
| All recorded time | 120 |
| Union of clock spans | 90 |

For the first release, retain additive ledger accounting and call it **recorded time**. Add a report-level overlap diagnostic with row drill-down. Do not call All “hours occupied,” free time, or a percentage of a 24-hour day.

Do not silently subtract 30 minutes from either class: that invents precedence and breaks the additive invariant. Even span overlap is not necessarily the exact overcount when recorded duration differs from the clock window. A future occupied-time metric needs its own interval-union, class precedence, time-zone, and attribution rules.

Calendar imports also record scheduled spans under the existing contract; these are not independent proof of attendance. Adding `u::` does not make calendar data stopwatch-measured. If provenance matters, add it separately from accounting class.

### History: missing duration is not automatically a measured hour

The prior plan reports zero bare timed closed rows among 1,226 sessions in its pre-change vault scan. I did not repeat that private-vault scan; the active rollout may already have created such rows. [S1, S2]

Read bare legacy timed rows as a distinct legacy supplemental state. Supplemental/All may show span-derived minutes as **estimated**, with partial quality and an explanation; Regular stays unchanged. A malformed duration field is invalid, not a legacy estimate. Stats must not write `u::` as a side effect.

Offer an optional reviewed backfill listing candidate rows and proposed durations, skipping conflicts and allowing reversal. If inferred durations are materialized, retain provenance rather than silently upgrading them to measured certainty. Explicit user correction can accept a number as the record.

Define supplemental coverage through a documented adoption date or metric `since` setting, accounting for known legacy rows. A complete note after coverage begins with no supplemental entries means zero. Earlier dates mean unknown/not tracked. All history with known regular time and unknown supplemental coverage is a regular subtotal with partial coverage, not an authoritative all-time total. The first positive supplemental entry does not prove earlier days were zero.

Clock spans cannot resolve every DST ambiguity. Retain the existing local-day/midnight conventions, prefer explicit duration, and label fallback values estimates. This feature should not quietly invent a different temporal model.

## 8. Implementation boundaries and rollout

Follow the current epic's settled baseline, or amend it explicitly before more writers land. Avoid simultaneous implementations disagreeing about whether absence or `u::` is canonical.

| Area | Required work |
| --- | --- |
| bob-cli time model | Typed regular/supplemental/legacy/invalid parsing; exclusive field writes; duration-preserving conversion. |
| Task/session resolution | General tag predicate; nonempty participant classifier; staged snapshots; unresolved-link diagnostics. |
| Writers | Calendar import, start/restart/swap/link-start, adjustment/shift, close, split/move, affected tag/link-edit paths. |
| Stats/homes | New metrics, real supplemental attribution, coverage/quality, frozen-class reads, overlap diagnostics. |
| Obsidian | Duration writers/snippets, close/link gestures, ledger chips, selector/charts, capability handling. |
| Mac Capture | Additive models and updated labels/summary presentation; Bob remains semantic authority. |
| Contracts/docs | Shared vectors, CLI help, vault format, stats/capture/calendar/homes docs, glossary, decision supersession. |

Recommended sequence:

1. **Pin semantics and shared vectors.** Include bare legacy rows, mixed sessions, future MEET queue items, and recorded duration versus clock union.
2. **Ship readers before new writers.** Add parsing, metrics, additive facts, and defensive decoding; regular defaults remain stable.
3. **Update every active writer.** Especially Obsidian metadata removal. An old writer can append `t::` beside `u::`; compatible readers do not prevent that. Unsupported writers should refuse the affected edit with an update message, not corrupt it.
4. **Enable `u::` writes and generalized classification.** Verify dry-run/commit parity and rollback on concurrent edits. Enable the selector when capabilities exist.
5. **Review/backfill history separately.** Do not require a vault-wide rewrite for ordinary use.

Share Rust/JavaScript vectors for parsing, classification, and writes. Swift consumes results instead of duplicating the predicate. Use the normal plugin build/tests and `bob plugins sync`; changed Mac targets require portable checks and compilation/type-checking under that repository's instructions. Bob CLI keeps its daily release train. This proposal does not require bypassing those workflows.

## 9. Acceptance examples

| Scenario | Required result |
| --- | --- |
| Close a 45-minute BODY session linked only to a tagged ordinary task | `u:: 45m`; regular unchanged; supplemental/all +45. |
| Add an untagged participant while open | Regular preview with explanation; close writes only `t::`. |
| Remove the last participant | Regular unlinked session, not supplemental by empty-set logic. |
| Tagged task plus a broken link | Regular fallback and diagnostic; broken link is not silently discarded. |
| Lunch then a regular event in the same MEET queue | Lunch supplemental; future event deferred rather than treated as participation. |
| Worked tagged task carried on close | Participates now and may participate next; carry does not erase history. |
| Retag task after closing | Recorded class and duration unchanged. |
| Change class on a 60-minute span with 45 recorded minutes | New class still records 45. |
| Extend/shift/split/swap/close through Rust and JS | Matching class/field results, conservation, unrelated metadata preserved. |
| Both `t::` and `u::` | Invalid with location; no double count or falsely complete total. |
| Bare legacy timed row | Never regular; any supplemental estimate explicitly identified. |
| Complete day after coverage begins has no supplemental entries | Zero; absent/pre-coverage days stay distinct. |
| Overlapping classes | Additive recorded total with overlap diagnostic. |
| Scope switch while a fetch resolves | Correct selected labels/data; no stale view or lost pinned date. |
| Old/new backend-client combinations | Honest capability limitation, never invented supplemental zeros. |
| Failed batch or concurrent edit | No partial class/duration/link write; retry from fresh snapshots. |

Also verify grouped/prior sums, home/theme conservation, JSON/CSV meaning, zero duration, midnight, archived/moved tasks, and raw edits before managed close. Tests should assert user-visible outcomes, not mirror helpers.

I inspected source and existing fixtures but did not implement this design or run product suites. Numerical examples are constructed cases, not empirical measurements or passing-test claims.

## 10. Explicit adjustments to the request

1. **Rename the concept, preserve input syntax.** Supplemental Pomodoro in the product; `#untracked` and `u::` remain practical spellings.
2. **Require nonempty resolved participation.** Empty sessions stay regular, unresolved links matter, future queue items do not participate.
3. **Qualify iff by lifecycle.** Derive at open/managed writes and freeze at close; raw intermediate edits and deliberate history corrections are explicit exceptions.
4. **Keep mixed sessions whole.** Any regular participant makes the session regular; no invented fractional split.
5. **Protect metric identities/defaults.** Select separate time metrics; do not reinterpret Worked, task counts, goals, or formulas.
6. **Define All as recorded duration.** Diagnose overlaps without claiming unique elapsed hours.
7. **Represent uncertain history honestly.** Estimates and coverage boundaries remain visible; backfill is reviewed separately.
8. **Include writers and attribution in scope.** Stats alone cannot make the feature reliable across the CLI, Obsidian, and Mac.

## Evidence and limits

Sources were inspected in authorized local checkouts. The links below pin source snapshots so subsequent epic progress does not change the evidence. Proposed identifiers elsewhere in this report are recommendations, not existing commands.

- **S1 — Approved baseline/progress:** audited `sase bead read bob-cli-f6` and `sase artifact read plan:202611/untracked_calendar_events.md`, 2026-11-01. [Epic page](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-f6/README.md). The plan supplies reviewer selections, visual baseline, and the earlier 0/1,226 scan; the live bead may advance.
- **S2 — Accepted decision:** audited `sase memory read decisions:untracked-sessions-omit-t-field`. It records writer-time classification and identifies counting untracked sessions as grounds to reopen.
- **S3 — Vocabulary/contracts:** audited glossary reads for Pomodoro, Task Link, Event Task, and Stats Dash; memory reads for CLI rules, Mac semantic ownership, and theme hues.
- **S4 — Parser/writer:** bob-cli `ab32d58aac5a838edf405eb0a34dfb1955041d1f`, [pomodoro_adjust.rs](https://github.com/bobs-org/bob-cli/blob/ab32d58aac5a838edf405eb0a34dfb1955041d1f/src/native/capture/pomodoro_adjust.rs), especially `session_tracking`, `duration_from_range_text`, `set_ledger_tracking`.
- **S5 — Stats mechanics:** same commit, [metrics.rs](https://github.com/bobs-org/bob-cli/blob/ab32d58aac5a838edf405eb0a34dfb1955041d1f/src/native/stats/metrics.rs), [index.rs](https://github.com/bobs-org/bob-cli/blob/ab32d58aac5a838edf405eb0a34dfb1955041d1f/src/native/stats/index.rs), [session_facts.rs](https://github.com/bobs-org/bob-cli/blob/ab32d58aac5a838edf405eb0a34dfb1955041d1f/src/native/stats/session_facts.rs), [report.rs](https://github.com/bobs-org/bob-cli/blob/ab32d58aac5a838edf405eb0a34dfb1955041d1f/src/native/stats/report.rs).
- **S6 — Event-run behavior:** same commit, [meet_event_run.rs](https://github.com/bobs-org/bob-cli/blob/ab32d58aac5a838edf405eb0a34dfb1955041d1f/src/native/capture/meet_event_run.rs), plus `tests/fixtures/meet_event_run/vectors.json`.
- **S7 — Calendar clustering:** same commit, [gcal/plan.rs](https://github.com/bobs-org/bob-cli/blob/ab32d58aac5a838edf405eb0a34dfb1955041d1f/src/native/gcal/plan.rs), `plan_meet_pomodoros`, `cluster_past`, `format_meet_span`; existing cases in `tests/gcal_sync.rs` and `tests/gcal_lifecycle.rs`.
- **S8 — Report contracts:** same commit, [stats.md](https://github.com/bobs-org/bob-cli/blob/ab32d58aac5a838edf405eb0a34dfb1955041d1f/docs/stats.md), [stats/cli.rs](https://github.com/bobs-org/bob-cli/blob/ab32d58aac5a838edf405eb0a34dfb1955041d1f/src/native/stats/cli.rs), [pomodoro_homes/session.rs](https://github.com/bobs-org/bob-cli/blob/ab32d58aac5a838edf405eb0a34dfb1955041d1f/src/native/pomodoro_homes/session.rs).
- **S9 — Dashboard:** bob-plugins `74ad5556c79d5a80910e25131014c00b32a28806`, [236-plugin-stats-data.js](https://github.com/bobs-org/bob-plugins/blob/74ad5556c79d5a80910e25131014c00b32a28806/plugins/bob-ledger-tools/src/236-plugin-stats-data.js), [238-plugin-stats-block.js](https://github.com/bobs-org/bob-plugins/blob/74ad5556c79d5a80910e25131014c00b32a28806/plugins/bob-ledger-tools/src/238-plugin-stats-block.js).
- **S10 — Writer compatibility:** same plugin commit, [020-time-and-pomodoro.js](https://github.com/bobs-org/bob-plugins/blob/74ad5556c79d5a80910e25131014c00b32a28806/plugins/bob-ledger-tools/src/020-time-and-pomodoro.js), `durationMetadata`, `removeDurationMetadata`, `changePomodoroLineUnits`.
- **S11 — Mac models:** bob-mac-capture `01c753b0e6e045a0cc69b3d3f51302b8423b7e55`, [CaptureAgendaModels.swift](https://github.com/bobs-org/bob-mac-capture/blob/01c753b0e6e045a0cc69b3d3f51302b8423b7e55/Sources/CaptureCore/CaptureAgendaModels.swift), plus `CaptureAgendaPresentation.swift`.
- **S12 — Tag semantics:** bob-cli snapshot above, [event_task.rs](https://github.com/bobs-org/bob-cli/blob/ab32d58aac5a838edf405eb0a34dfb1955041d1f/src/native/event_task.rs), `line_has_untracked_tag` and tests.
- **S13 — Close participation:** same commit, [capture_pomodoro_close/ledger.rs](https://github.com/bobs-org/bob-cli/blob/ab32d58aac5a838edf405eb0a34dfb1955041d1f/src/native/capture_pomodoro_close/ledger.rs), `LedgerLinkRole` and `plan_ledger_close_with_parked`.

External primary documentation was checked on 2026-11-01. Product analogies support separating duration from reporting eligibility; they do not establish this exact design for Bob. WAI sources support accessibility details. Naming, lifecycle, and rollout recommendations are independent design judgments grounded in the local contracts.

## Recommended solution

**Implement Supplemental Pomodoros with mutually exclusive `t::` and `u::` durations, shared writer-time classification, and frozen closed-session accounting. Add supplemental and combined metrics, then expose them through Regular / Supplemental / All and `bob stats --time`. Keep existing work totals, formulas, and defaults stable.**

Adopt the nonempty participating-link rule, exclude future queue items, preserve recorded minutes during class changes, and expose legacy estimates and overlapping spans. Ship compatible readers and every active writer before enabling the field. This provides a fuller account of the day without making ordinary work stats less trustworthy.
