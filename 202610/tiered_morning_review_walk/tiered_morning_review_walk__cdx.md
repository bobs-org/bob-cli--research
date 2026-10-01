# Morning GTD review: queue order, daily intervals, and removing seeded freshness

Researcher: **cdx**. Date: **2026-10-01**. Independent research for the five-researcher swarm. No peer report, transcript, summary, or findings were consulted. This report proposes a design; no application code, configuration, task, or freshness field was changed.

The proposed direction is sound: review commitments before the general backlog, use one deterministic queue, and return `fresh` to meaning a real human confirmation. However, ordering cannot itself make the review small. The live workload suggests that daily review defaults need deliberate lane and schedule triage. Removing seeded dates also creates a large one-time NEW queue, and distinguishing artificial stamps from later genuine confirmations is not always possible from current text alone.

## Evidence and current behavior

Sources inspected locally:

| Reference | Source and observation |
| --- | --- |
| S1 | [bob-cli freshness contract](https://github.com/bobs-org/bob-cli/blob/5d24c98857b1d16dd1d4161da72272f272ad92bc/docs/freshness.md), especially §§2, 4, 6, 7, and 13. Interval inheritance, exclusions, queue order, seeding, review ritual, and rollout trial. |
| S2 | [Rust evaluator and queue](https://github.com/bobs-org/bob-cli/blob/5d24c98857b1d16dd1d4161da72272f272ad92bc/src/native/freshness/state.rs), plus `scan.rs`, `cli.rs`, `placement.rs`, and `seed.rs` in the same directory. |
| S3 | [Rust config loader](https://github.com/bobs-org/bob-cli/blob/5d24c98857b1d16dd1d4161da72272f272ad92bc/src/native/config/freshness.rs). Default interval 7, validation 1–365, independent config loading. |
| S4 | [bob-ledger-tools](https://github.com/bobs-org/bob-plugins/blob/4744607d7a047d114d7faa3a73e0c22048f3f374/plugins/bob-ledger-tools/main.js): `freshnessIntervalFor` around 4516, `freshnessEvaluate` 4555, `freshnessQueue` 4699, `freshnessReviewModel` 4938, task adapter 5647, memo builder 7347, public interval accessor 7776. |
| S5 | [bob-navigation-hotkeys](https://github.com/bobs-org/bob-plugins/blob/4744607d7a047d114d7faa3a73e0c22048f3f374/plugins/bob-navigation-hotkeys/main.js): freshness section 23904, duplicated interval description 24034, `planReviewJump` 24253, commands 24735, `jumpToDueTask` 27200, and post-stamp bookkeeping 27504. |
| S6 | `chezmoi:home/dot_config/bob/config.yml`, inspected at commit `c9299ff7ed2a5de5ae9173214efd38aedd50a3bf`: priority rolls write `scheduled`; configured lane caps are Pending 10 and Next 15; no freshness block currently exists in that source file. |
| S7 | Audited memory reads of Task Freshness and decisions `ready-is-freshness-gated`, `task-lanes-are-sticky`, and `today-is-read-from-the-ledger`. These govern classification and lane ownership. |

The source already has a suitable architecture: navigation reads a memoized queue from ledger-tools; it does not sort the vault itself. Ctrl+Alt+J/K call the next/previous due-task commands. The navigation source explicitly describes `]s`/`[s` as Vim aliases for those commands. The live Vim alias file was not inspected, so alias verification remains a rollout check. Alt+Shift+F uses the same queue after stamping. [S4, S5]

Today the review evaluator excludes Pending and Next entirely. It accepts visible, non-recurring Ready tasks outside canonical daily notes and outside Today. NEW sorts by path/line; the combined resurfaced/rotten queue sorts by review due date/path/line. Task `created` is present in Rust input but unused in sorting; the JavaScript freshness adapter does not yet carry creation dates. This is an eligibility and projection change as well as a comparator change. [S1, S2, S4]

### Read-only workload snapshot

`bob freshness list -f json` returned schema 2, local date 2026-10-01, default interval 7, budget off, **1 NEW, 199 FRESH, 0 RESURFACED, 0 ROTTEN**, with no warnings. Its `refreshed_today` count was **393**. That counter includes stamps on any status and seeded stamps; it does not establish that 393 human reviews occurred.

An aggregate native Tasks query through the read-only Bob query skill used the existing visibility filters, then excluded recurring tasks and canonical daily-note paths:

| Lane | Visible non-recurring tasks | With `fresh` | With task-level `refresh` | With arrived `scheduled` |
| --- | ---: | ---: | ---: | ---: |
| Pending | 50 | 50 | 0 | 1 |
| Next | 30 | 26 | 0 | 1 |
| Ready | 200 | 199 | 0 | 59 |

This aggregate includes Today membership; the current freshness queue separately excludes Today. It is a planning baseline, not an exact future morning queue. Ready stamps were distributed over September 25–October 1: 26, 26, 26, 15, 20, 38, and 48 respectively. That distribution is consistent with staggered seeding, but does not prove the provenance of individual stamps.

The relevant existing JavaScript suites passed: `node --test scripts/test-ledger-tools-freshness.cjs scripts/test-navigation-freshness.cjs scripts/test-ledger-tools-dashboard-parity.cjs` — **65 passed, 0 failed**. These validate the current implementation, not the proposed behavior. No interactive Obsidian keyboard test or Rust rebuild was performed.

## Clarifications and proposed requirement adjustments

These are explicit proposals, not assumptions silently folded into the implementation.

1. **Cleanup should target artificial `fresh` dates.** `fresh` is the confirmation date; `refresh` is an integer interval. The existing seed writes `fresh` and preserves interval overrides. No task-level `refresh` appeared in the measured visible lanes. Preserve genuine `fresh` confirmations, deliberate `refresh` overrides, and note-level `task_refresh`. [S1, S2]
2. **Navigate tasks due for review, not every open task on every press.** With one-day intervals, a task confirmed today leaves the queue until tomorrow. Otherwise refresh-and-advance can loop through already reviewed work. Keep calendar-day arithmetic, not 24-hour elapsed time.
3. **Define five explicit review groups:** NEW → PENDING → NEXT → SCHEDULED → READY. A default interval of 1 does not by itself place scheduled tasks before unscheduled tasks with interval 1. Membership and priority must be separate from interval resolution.
4. **Preserve NEW's current dashboard meaning:** an eligible Ready task without a valid confirmation. A Pending or Next task missing `fresh` is immediately due within its own lane group. This keeps the established mutually exclusive dashboard sections and avoids unexpectedly relocating lane tasks into NEW.
5. **Interpret the requested date tie-break as equal `fresh`, not equal `refresh`.** Equal intervals are already the first tie. The intended subsequent ties are older confirmation first, then newer creation first. Missing/invalid creation dates sort after known dates; path/line provide a final deterministic tie.
6. **Make contextual defaults outrank a broad note interval, while retaining a task override.** Recommended precedence is detailed below. This changes note inheritance for scheduled Ready tasks; it prevents a project-wide 30-day note setting from defeating the intended daily checks. Ordinary unscheduled Ready inheritance stays unchanged.
7. **Today should remain a dashboard placement, not suppress overdue commitment review.** Extend due-review eligibility to Pending/Next even when linked Today. For Ready tasks, I would also let an overdue task linked Today be reviewed, while retaining the dashboard's existing Today exclusion. Supported link gestures already stamp, so normal linking removes the task from today's due queue. A handwritten link should not silently prove human confirmation. This deliberately adjusts the current review exclusion, without changing ledger-derived Today or task lanes.
8. **Retain the other exclusions initially:** hidden, blocked, future-scheduled, recurring, canonical daily-note, completed/cancelled, template, and conflict tasks. Thus “any scheduled task” means any otherwise eligible task with a valid schedule. A missing/future/invalid schedule should not create a new way around the existing filters. Recurring and daily-note tasks retain their existing review mechanisms.

The morning ritual in the accepted freshness decision currently puts RETURNED/ROTTEN before Pending/Next. The requested ordering supersedes that ritual. Any accepted policy update must preserve the decision-history convention; this report does not alter memory or claim a replacement decision has been accepted.

## Recommended queue contract

Compute lane, eligibility, effective interval, confirmation state, and review group from one snapshot. Queue only tasks that need review.

| Priority | Group membership | Ordering within the group |
| ---: | --- | --- |
| 0 | Eligible Ready with no valid `fresh` | Keep path ascending, line ascending for predictable inbox processing. |
| 1 | Eligible Pending due for review | Missing confirmation first; then `fresh` ascending, `created` descending, path/line. |
| 2 | Eligible Next due for review | Same as Pending. |
| 3 | Eligible Ready with `scheduled <= today`, due for review | `scheduled` ascending, then `fresh` ascending, `created` descending, path/line; missing confirmations already belong to NEW. |
| 4 | Remaining eligible Ready due for review | Effective interval ascending, `fresh` ascending, `created` descending, path/line. |

A scheduled Pending task remains Pending, and a scheduled Next task remains Next. An unstamped scheduled Ready task remains NEW. Every task appears once. Scheduled group priority is based on a valid arrived schedule, not merely state `resurfaced`: after the first confirmation, the state may become rotten while the schedule still exists.

For the ordinary Ready group, the exact requested sort tuple is:

```text
(interval_days ASC, fresh_date ASC, created_date DESC NULLS LAST, path ASC, line ASC)
```

At equal intervals, sorting older `fresh` first is equivalent to sorting review due dates earlier or days overdue greater. It is not equivalent across different intervals, which is why interval must come first.

Example with today = October 8:

| Task | Interval | Fresh | Days overdue | Created | Result |
| --- | ---: | --- | ---: | --- | ---: |
| A | 1 | October 6 | 1 | September 1 | 1 |
| D | 7 | September 28 | 3 | September 20 | 2 |
| C | 7 | September 28 | 3 | September 1 | 3 |
| B | 7 | September 30 | 1 | September 1 | 4 |

This produces **A → D → C → B**, matching the examples in the request. A fresh, not-yet-due one-day task should not precede overdue work because it is absent from the review queue.

“Always” should describe this queue order, not force every key press to restart at NEW. Next/previous still walk forward/backward from the current task, wrap with a notice, and start at the first/last task when the cursor is outside the queue. Otherwise the previous key would cease to work sensibly.

## Interval resolution and scheduled behavior

Add three integer day settings, each validated as 1–365:

```yaml
freshness:
  interval: 7
  pending_interval: 1
  next_interval: 1
  scheduled_interval: 1
```

Use one resolver per language with this precedence:

1. Valid task-level `[refresh:: N]`.
2. Applicable contextual defaults: Pending, Next, and/or valid scheduled task. If both a lane and scheduled default apply, use the **minimum** of those two values.
3. Valid containing-note `task_refresh`.
4. `freshness.interval`, default 7.

For example, Pending 3 plus scheduled 1 gives interval 1; Next 1 plus scheduled 7 also gives 1. A deliberate task override of 14 still gives 14. Report the effective source, such as `pending`, `next`, `scheduled`, `task`, or `note`, so longer-than-daily exceptions are explainable. Tie source attribution should be deterministic.

This uses the new fields as **defaults**, not hard caps. If literal unconditional daily Pending/Next review is desired even with a task override, that is a different policy and should be explicit. I prefer preserving Bryan's deliberate task overrides.

Keep the existing returned-task trigger:

```text
scheduled > today                                  => excluded
no valid fresh                                     => needs initial confirmation
fresh < scheduled <= today                         => review immediately on return
otherwise today >= fresh + effective_interval      => review due
```

The arrived schedule triggers review immediately even if an explicit task interval is 30 days. Once confirmed on/after the scheduled date, its ordinary interval governs. Confirming today removes it for today; default interval 1 brings it back tomorrow if it remains eligible. [S1, S2]

**Important behavioral choice:** the literal request means a task with an old `scheduled` field keeps receiving the scheduled interval indefinitely. It does not mean “review exactly once on the scheduled day.” Bob's priority rolls use schedules as deferrals, so an elapsed schedule is often a tickler rather than a true deadline. [S6]

I recommend keeping the requested daily default, but offering a deliberate review outcome: **return to ordinary Ready**, which clears an elapsed schedule and stamps in the same human write, preserving any Schedule Log. The existing property-delete route may already suffice. Do not automatically clear schedules just because Alt+F was pressed. An alternative is a one-shot return policy after confirmation; that is attractive if these 59 scheduled Ready tasks are mostly old deferrals, but it contradicts the proposed persistent scheduled default and would need a separate decision.

## How to implement this without splitting the contracts

### Keep evaluation, dashboard buckets, and navigation distinct

Generalize the shared evaluator's due-review scope to the visible Ready/Pending/Next lanes, with lane information retained explicitly. Keep dashboard bucket projection restricted to its established Ready pool. A task may be due for commitment review while remaining displayed in PENDING, NEXT, or TODAY.

Changing `isTodo` to “open” and leaving `bucket(state)` unchanged would classify expired Pending/Next as ROTTEN and risk contaminating dashboard counts and filters. Likewise, the existing `reviewModel()` assumes its rotten total is resurfaced plus age-expired Ready; feeding it a generalized count silently changes chip meaning. [S2, S4]

Use the same evaluated rows to derive:

- A generalized queue, rank map, and total due count, with explicit `review_group` and lane.
- Group counts for NEW/PENDING/NEXT/SCHEDULED/READY.
- The existing Ready-only NEW/ROTTEN bucket counts and badges.
- Freshness marks and the effective interval shown in the property picker.

Keep `reviewModel()` as the Ready-bucket view if that contract is retained, and expose the generalized review summary distinctly. A status bar should show commitment-review work as well as Ready work; a Ready-only `ROTTEN 0` must not imply the whole queue is empty.

### Code surfaces

- **bob-cli:** extend `FreshnessConfig`; make interval resolution context-aware in `state.rs`; carry sort fields in queue entries; collect review inputs from the existing lane predicates instead of just `Snapshot.ready`. `scan.rs` already has richer open/all rows, so a second vault crawler is unnecessary. Update CLI help, JSON, counts, and conformance vectors. Keep unrelated config loaders isolated from invalid freshness settings.
- **bob-ledger-tools:** mirror config parsing and pure evaluation; carry lane/status and a normalized Tasks creation date through `freshnessRowFromTask`; update `freshnessQueue`, memo invalidation, rank lookup, scope projections, and marks. Keep one config/date snapshot and O(1) warm rank lookup.
- **bob-navigation-hotkeys:** consume the unified queue. Replace the separately implemented `describeRefreshInterval` inheritance with the canonical resolver, including line context needed for preview and unsaved edits. Its current task → note → global computation otherwise shows misleading intervals. Treat unresolved rendered marks neutrally when lane/schedule context cannot be established. [S4, S5]
- **Configuration and documentation:** defaults in both runtimes; source config examples in chezmoi; morning ritual and queue examples in `docs/freshness.md`; dashboard descriptions and plugin README. Deploy plugin changes from bob-plugins with `bob plugins sync`, not by editing installed files.

The native JSON contract is currently schema 2 and freshness namespace version 3. Enlarging eligibility and changing meaning of existing queue/count fields merits a documented semantic version change, conservatively JSON schema 3 and freshness namespace 4; adding new optional fields alone would not. Navigation currently checks top-level API version 3, so it must also check the relevant freshness capability/version for the new contract. Coordinate dashboard fallback checks rather than assuming all plugins reload together.

### Navigation after mutation

The existing post-stamp route remembers rank/count and suppresses just-stamped keys to tolerate Tasks cache lag. Preserve suppression, stale-line revalidation, block identity, and retry behavior. Extend tests before trusting numeric rank subtraction when removals are noncontiguous or the queue changes group/order. A removed-task sort tuple plus stable key can anchor predecessor/successor more reliably than a remembered numeric index. Verify previous as well as next after a stamp, and advancing after release, reschedule, move, or completion. [S5]

Useful acceptance cases are: the A/D/C/B vector; full group precedence; scheduled Pending/Next deduplication; initial missing stamps; equal/missing creation dates; note/task/context precedence and invalid fallthrough; future schedule exclusion and scheduled-day return; one confirmation per local day, including DST; Today visibility; preserved Ready bucket counts; delayed cache refresh; unavailable plugin/config fallbacks; and queue parity between Rust and JavaScript.

## Critique: will this reduce overwhelm?

It can reduce uncertainty and protect commitments, but the measured lane sizes are the larger issue. Under the proposed contextual defaults, approximately **80 Pending/Next + 59 scheduled Ready = 139 potential daily reviews**, plus new arrivals and reviews of the remaining 141 Ready tasks. If those remaining tasks average seven-day intervals and confirmations are distributed, their steady-state contribution is about 20/day: **roughly 159 + arrivals**. This is an estimate, not a forecast; completions, releases, schedule clearing, overrides, Today treatment, and actual note intervals change it.

At five seconds per item, 159 items is about 13 minutes; at ten seconds, about 27 minutes, before edits and scheduling. The configured lane caps are 10 Pending and 15 Next, compared with the observed 50 and 30. A one-time lane prune and reviewing whether elapsed schedules should remain are more likely to reduce effort than another sorting heuristic. Release must remain a human gesture; freshness never demotes a lane. [S6, S7]

Strict shortest-interval-first can starve 7/30/90-day Ready tasks when the protected groups consume the whole morning. Preserve the requested comparator, but reserve a small explicit ordinary-backlog allowance after the commitment pass and retain a weekly oldest-overdue sweep. If actual capacity cannot cover the daily groups, lengthen intentional task overrides or reduce commitments. Silently dropping daily commitments to satisfy a numeric goal would make the system harder to trust.

The existing daily meter counts all today-stamped tasks, including other gestures, done tasks, and seed writes. It must not authorize stopping before Pending/Next/scheduled groups are handled. Define a completion criterion using remaining queue groups, with the existing confirmation meter serving only as feedback. The initial cleanup and seeding day should be excluded from review-rate judgments.

The GTD distinction supports a modest daily commitment scan plus a broader weekly review. David Allen Company's guide recommends consulting next-action lists during the day and reviewing the broader action, waiting, and project lists weekly; it also cautions that fabricated due dates and excessive reminders weaken trust. These are reasons to preserve real dates and control review scope, rather than treat every review-due date as a deadline. [Official Microsoft To Do setup guide, p.20](https://gettingthingsdone.com/wp-content/uploads/2020/12/GTD_Microsoft_To_Do_LTR_sample.pdf)

The official weekly-review guidance includes calendar, waiting-for, project, checklist, and someday/maybe review. A task-freshness queue is useful but does not replace those checks. [GTD Best Practices: Review](https://gettingthingsdone.com/2011/11/gtd-best-practices-review-part-4-of-5/)

### Alternatives considered

| Approach | Assessment |
| --- | --- |
| Requested group order plus contextual daily defaults | Best fit, provided the active lanes and elapsed schedules are triaged. Explainable and easy to test. |
| Keep existing chronological review due-date order | Fairer to old backlog, but fails the explicit short-interval-first preference and still excludes current commitments. |
| Make every Ready task daily | Would add almost the whole 200-task pool to every morning; poor fit for the stated goal. |
| Weighted urgency or normalized overdue ratio | Adds tuning and surprises. Neither guarantees the supplied interval-first examples. Avoid initially. |
| One-shot scheduled return, then ordinary Ready cadence | My preferred fallback if persistent daily schedules prove noisy. Retains existing resurfacing semantics, but changes the requested “any scheduled task” interval policy. |
| Preserve fake dates as throttling | Keeps workload spread but preserves false confirmation history. Prefer genuine review cadence and an honest migration backlog. |

## Removing artificial dates safely

Removing all `fresh` fields indiscriminately would erase genuine confirmations since cutover. Removing only `refresh` would not undo the seed at all. The seed stores no per-task provenance field, and its report lists bucket/note counts and affected files rather than a durable old/new line manifest. Current dates alone are insufficient evidence. [S2]

Even an unchanged seeded date is ambiguous: Alt+F on a canonical line already stamped today is a no-op. A genuine same-day confirmation can therefore leave no Git text change. Vault history can reconstruct the original seed delta, but cannot always prove an unchanged stamp was never subsequently confirmed. This ambiguity should be handled openly.

Recommended migration:

1. **Ship and verify the queue and interval behavior before cleanup.** Produce a before/after eligibility preview, including the one-time NEW count and the ongoing daily-group estimate.
2. **Locate the original seed write using audited vault history or its recorded output.** Build a task-identity manifest with original/current line fingerprints and proposed field removals. Preserve subsequent confirmed changes; review ambiguous same-day cases manually, or obtain an explicit reset scope as an implementation decision. Do not infer “fake” from an old date or membership in September 25–October 1.
3. **Plan the initial backlog honestly.** If all 199 current stamped Ready tasks were reset, combined with the current one NEW, that would produce roughly 200 NEW tasks, not an already-small interval-sorted Ready queue. Genuine stamps and scope differences reduce this number. Plan a one-time triage session or several deliberate sessions, with a quick calendar/commitment check while catching up. Do not claim NEW-first navigation prevents overload by itself.
4. **Use a dedicated field-removal transformation.** Preserve every unrelated field, block ID, dependency, status, and deliberate interval. Do not use `setRefreshLine(line, null)` or `set_refresh(..., None)`: those clear an interval and stamp today, fabricating a confirmation during cleanup.
5. **Preview, back up, then apply only the approved candidate bytes.** Reuse seed-style parser invariance checks under both Rust task parsers, compare-before-write guards, and temporary-file/rename writes. Atomic replacement is per file, not a whole-vault transaction; retain a rollback record and reconcile sync safely.
6. **Verify idempotence and unchanged task semantics.** Confirm only intended artificial stamps were removed and real confirmations/intervals survived. Do not reseed after the reset.

No cleanup was performed in this research turn. The specific original seed manifest and full vault history were not examined, so this report cannot certify individual stamps as artificial.

## Recommended solution

Implement **one due-review queue ordered NEW → PENDING → NEXT → SCHEDULED → ordinary READY**, with ordinary Ready sorted by **effective interval ascending, confirmation date ascending, creation date descending**, and deterministic final ties. Add the three one-day contextual defaults, retain deliberate per-task overrides, preserve scheduled-day resurfacing, and keep dashboard buckets separate from generalized review eligibility.

Pair this with a **human lane prune and deliberate clearing/rescheduling of elapsed ticklers**, a small ordinary-backlog allowance, and the existing broad weekly review. Use daily-group completion rather than the current stamp meter as the stopping rule. Validate the cross-language contract and navigation mutation cases, then remove **only the intended artificial `fresh` stamps**, with explicit treatment of provenance ambiguity and the one-time NEW backlog. This meets the requested workflow while addressing the actual sources of overwhelm: oversized commitments, persistent old schedules, and an honest migration backlog.
