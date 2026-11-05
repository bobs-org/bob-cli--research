# Review order and period preparation for the morning GTD walk

Independent research by **cdx** · 2026-11-05

## Recommendation in brief

Add three small PRE reminders for preparing the weekly, quarterly, and yearly reviews. Give PRE and POST an optional **Review order**, separate from ordinary task priority: smaller numbers walk earlier, and equal numbers retain the existing file/line order. Use 10–12 for period preparation, 20 for SASE cleanup, 30 for the three browser tasks, and leave other PRE tasks unnumbered.

This is a good improvement: launching drafts first buys time while Bryan does the rest of the review, and keeping browser chores together removes unnecessary switching. The main risks are recurrence drift, launching the wrong period, and making the morning review into an agent-management session. Keep the feature small, explicit, and visible.

Two findings materially affect implementation: **quarterly and yearly review currently lack `#post`**, and **Bob's ordinary P-levels are scheduling/deferral controls**, not a suitable encoding of checklist sequence. A third finding affects correctness: a new custom field placed after Tasks metadata can hide the task's scheduled date and recurrence from the parser.

No vault, application, or plugin changes were made in this research. No peer reports or peer findings were consulted.

## Evidence and current behavior

I inspected the primary bob-cli checkout, opened bob-plugins and upstream Obsidian Tasks through the audited repository workflow, read the relevant SASE decisions, and queried the live vault through the read-only `bob_query` workflow. Code revisions and source pointers appear below. The installed query executable reports `bob 0.4.0`; the source inspection is pinned separately and should not be confused with proof of the installed binary's exact commit.

### The live checklist

The live query found eight PRE tasks, two POST tasks, and two period-review tasks carrying `#gtd` without either phase tag. All twelve open rows were currently `[?]`, with future scheduled dates. This is a snapshot after today's work, not evidence that the tasks are missing from the morning walk.

| Existing task | Phase tags | Recurrence | Next scheduled occurrence in snapshot |
| --- | --- | --- | --- |
| Morning review | `#gtd #post` | `every day when done` | 2026-11-06 |
| Weekly review | `#gtd #post` | `every week on Monday when done` | 2026-11-09 |
| Quarterly review | `#gtd` only | `every 3 months on the 1st Monday` | 2027-01-04 |
| Yearly review | `#gtd` only | `every January on the 2nd Monday` | 2027-01-11 |

The existing PRE source order is Calendar → Weather → Brush teeth → Email → SASE cleanup → Reconcile/sync/pull → Supplements → Stretches. Thus the browser tasks are currently split, and SASE cleanup comes after them. The first seven are next scheduled for November 6; stretches is scheduled for November 11. Preserve that deliberate future schedule during migration. All twelve rows have normal native Tasks priority; none needs an ordinary priority migration. [S1]

Exact membership matters. `#gtd #pre` creates PRE; `#gtd #post` without `#pre` creates POST. `#gtd` alone creates neither. Quarterly/yearly may enter the ordinary RECURRING tier once their status/date permit, but they cannot provide the intended POST checklist behavior in their current form. [S2]

### One shared queue, two implementations

The queue is PRE → NEW → PROJECTS → PENDING → NEXT → RECURRING → TICKLER → ROTTEN → POST. Both the Rust evaluator and bob-ledger-tools' JavaScript evaluator currently sort PRE and POST by **path, then line**. NEW uses the same comparator branch today; an implementation must split PRE/POST out rather than accidentally changing NEW. Navigation and footer ranks consume this shared order. [S2–S4]

Eligibility happens before ordering. PRE/POST admit the supported open statuses, including `[?]`, but exclude future-scheduled, hidden, dependency-blocked, and template/conflict rows. Recurrence and Today membership do not exclude a checklist member. A high order must never make tomorrow's reminder appear today. The checklist gate specifically uses `scheduled`; use that field for the new reminders rather than substituting a due-only date. [S2, S3]

Completion stays with Tasks so it creates the next occurrence. The walk never freshness-stamps PRE/POST. Existing answer/advance rules, including the Ctrl+Enter boundary between checklist and other tiers, should remain intact. The navigation implementation already records neighbors in queue order and resolves identities after line movement; it should receive the changed queue, not gain another private sort. [S2, S5]

### Period notes are not calendar-month notes

Bob has week, quarter, year, and all-time notes. Weeks are ISO Monday–Sunday weeks; quarters partition ISO weeks into W01–13, W14–26, W27–39, and W40–52/53. Monthly notes are retired, and all-time has no Review to draft. Add **three** reminders, not monthly or all-time reminders. [S6]

A review appointment need not be the first day after its period ends. For example, 2026-Q3 ends September 27, while its existing calendar-quarter first-Monday appointment is October 5. 2026-Q4 ends January 3, 2027; its appointment is January 4. The yearly appointment remains January 11. I independently checked these dates with Python's ISO-calendar functions. Preserve these appointments; changing to ISO-boundary review dates would be a separate requirement change.

## Alternatives and tradeoffs

| Approach | Advantages | Costs and verdict |
| --- | --- | --- |
| Reorder the source rows, optionally under clear headings | No new queue code or syntax; already controls this file's walk | Good immediate workaround. Physical placement also serves status organization and recurrence insertion, and cannot express priority across files. A lasting feature should not rely exclusively on it. |
| Reuse `[priority:: highest/high/medium]` | Native field, existing picker and decorations, small comparator change | Reject. Bob treats absence as implicit P0, while native Tasks puts normal below medium. Bob's picker also rolls scheduled dates for P1–P4. Sequence would acquire unrelated scheduling meaning. |
| Add `[review_order:: N]` only for PRE/POST | Local, explicit, travels with recurrence, independent of task importance, supports ties | Recommended. Requires a parser/placement contract, a small editor affordance, and Rust/JS conformance tests. |
| Use `#gtd/order/10` tags | Avoids the custom-field suffix hazard; tags are copied into recurrences | Technically viable fallback, but adds numeric tag taxonomy and a second interpretation of tags alongside phase membership. Less natural than a typed order property here. |
| Store a configuration list of task titles or block IDs | Clean task lines | Reject. Titles change; Tasks clears block links and dependency IDs on new recurrences. A config list needs durable series identity and synchronization. |
| Infer browser tasks from URLs or wording | No manual labels | Reject. Email/calendar need not contain URLs, and unrelated tasks may contain them. Assignment should be explicit. |
| Add dependency links or new walk tiers | Can express hard prerequisite order | Reject for this scope. Dependencies affect visibility and recur poorly; new tiers would spread a local sequencing preference into the global review ritual. |
| Generate reminders dynamically from due POST rows | Could enforce a single schedule source | Stronger synchronization, but needs series identity, generation/reconciliation, and occurrence completion bookkeeping. Reserve for a later request for automatic lockstep. |

The difference between Bob and native Tasks priority is not cosmetic. Bob's documented picker maps P1–P4 to `high`, `medium`, `low`, and `lowest`, and writes a future scheduled date when selected. Native Tasks sorts highest → high → medium → normal → low → lowest. Merely applying that native comparator would invert part of Bob's P0 meaning. [S7; official [Tasks sorting](https://publish.obsidian.md/tasks/Queries/Sorting)]

## Proposed user experience and data contract

Call the property **Review order**, with the explanation “Earlier in PRE or POST.” Avoid calling it P1/P2 or drawing it with the existing priority bars.

| PRE task or group | Stored order |
| --- | --- |
| Prepare weekly review | 10 |
| Prepare quarterly review | 11 |
| Prepare yearly review | 12 |
| Clean up SASE agents | 20 |
| Calendar, weather, email | 30 each |
| Every other PRE task | Absent |

The gaps permit later insertion. The three browser rows stay contiguous among this checklist's tasks; ties preserve their current Calendar → Weather → Email order. There is no need to force a new ordering inside that cluster. If a specific browser sequence later matters, it can use 30, 31, 32 without changing the model.

Proposed semantics:

- Scope: exact PRE/POST members only. An order on an ordinary task is inert, and should produce an informational diagnostic rather than change another tier.
- Value: decimal integer 1–999. Lower means earlier. Missing means “Default,” after all valid explicit values. Do not write a magic default number into every row.
- Comparison: existing tier first; within PRE or POST, explicit order ascending with absent last, then existing path/line comparison. All other tier comparators remain byte-for-byte equivalent in behavior.
- Ties intentionally form a group. A value is an ordering preference, not a unique identity, progress count, task priority, deadline, or dependency.
- Invalid/duplicate fields: keep the task visible according to its real dates/status, use Default, and emit a diagnostic. Do not pick a surprising winner from contradictory values. A managed edit replaces all occurrences with one canonical field.
- Parse real task metadata, excluding quoted/code examples and child prose. Accept bracket and parenthesis inline-field forms if following the existing metadata conventions; writers emit square brackets.
- Read-time queue construction never rewrites or physically sorts the note.

Canonical example, deliberately placing custom metadata **before** the Tasks suffix:

```markdown
- [?] #task #gtd #pre Prepare weekly review [review_order:: 10] [repeat:: every week on Monday when done] [scheduled:: 2026-11-09]
```

The migration should write through a shared placement helper. An order edit must preserve status, recurrence, scheduled/start/due dates, ordinary priority, task links, child blocks, and line-ending conventions.

### A small, quiet visual treatment

Use the existing PRE/POST identity mark and add a subdued adjacent `10` when explicit order exists. On hover or keyboard focus: “Review order 10 · earlier values first · PRE only.” Default rows show no extra mark. Keep text readable without color, and preserve raw metadata in source mode.

Expose one contextual **Review order…** action for PRE/POST tasks: numeric entry, a short explanation, and “Default” to remove it. Reuse the existing task-editing surface if possible; do not add another keyboard shortcut or repurpose Alt+P. The editor affordance is valuable because it prevents users from appending the field in an unsafe position.

A schematic presentation, not a proposed new dashboard:

```text
PRE
  10  Prepare weekly review
  20  Clean up SASE agents
  30  Review next week in Google Calendar
  30  Check weather
  30  Read email
      Brush teeth
      Reconcile / sync / pull
      …
```

The footer should continue showing its existing PRE/POST counts and ranks. Order values do not become extra chips, counters, progress bars, or global tiers. A tooltip or expanded queue explanation can identify the order when someone asks why a row came first. Use one styling system across Live Preview and Reading view, with keyboard access and light/dark checks. Beauty here comes from a legible sequence and restrained metadata.

### The placement hazard is a release blocker

In a temporary isolated vault, I ran the installed native Tasks query against two otherwise identical future reminders:

| Position of `[review_order:: 10]` | Observed `isRecurring` | Observed `scheduled` |
| --- | --- | --- |
| Before `[repeat:: …] [scheduled:: …]` | true | 2026-11-09 |
| After `[repeat:: …] [scheduled:: …]` | false | null |

The temporary vault was removed after the experiment. This was a parser experiment, not a test of an implemented review-order feature.

The Rust Tasks parser reads trailing fields until it encounters an unknown field. Existing freshness placement code explicitly documents this constraint. Upstream Tasks' Dataview support likewise does not promise arbitrary field placement. [S8, S9]

Therefore, a comparator-only patch is insufficient. Add canonical insertion, preservation through Tasks completion, and clear linting for a misplaced field. For the read path, ensure order extraction cannot accidentally promote a future task whose Tasks suffix was masked: a defensive raw-line reparse/normalization for eligibility is preferable to treating missing parsed dates as genuinely absent. Do not claim that an arbitrary field at the end is safe. Repair placement through an explicit managed edit before any completion operation relying on the affected Tasks object. Verify this with the installed Tasks plugin, not just the Rust mirror. If that integration cannot be made sound, the numeric-tag alternative is safer than shipping a field that silently loses dates.

## The new recurring reminders

Create one companion PRE task per period. Copy the counterpart's actual recurrence and current scheduled date at migration time; the dates below are evidence from this snapshot, not hardcoded constants for a later implementation.

| Reminder title | Initial recurrence | Initial scheduled date | First target note |
| --- | --- | --- | --- |
| Prepare weekly review | `every week on Monday when done` | 2026-11-09 | `2026/2026-W45.md` |
| Prepare quarterly review | `every 3 months on the 1st Monday` | 2027-01-04 | `2026/2026-Q4.md` |
| Prepare yearly review | `every January on the 2nd Monday` | 2027-01-11 | `2026.md` |

Suggested short task text:

> **Prepare weekly review:** identify the week for this review occurrence; if its Review is missing, launch an agent to draft it before POST. If a draft or agent already exists, use it.

Use equivalent quarterly/yearly wording. Put the fuller prompt and completion rule in child notes, keeping the navigated line short. The task text should describe identifying the target; do **not** embed `2026-W45` into an endlessly recurring description that Tasks will copy forever.

At launch, resolve a concrete target ID and include it in the agent prompt. Use the latest fully closed period of the relevant kind **as of this occurrence's scheduled review date**, not the wall clock when a delayed agent finally starts. That prevents an overdue weekly reminder from silently changing its subject after another Monday. A weekly task completed after several missed weeks also needs an explicit catch-up decision; recurrence alone does not recover skipped history.

The agent should read the target's versioned instructions and `bob periods brief <ID>`, then save only through `bob periods draft <ID>`. It must not overwrite Intentions, Outcomes, Theme, or Reflection, and should not use `--force` by default. Existing `edited`/`reflected` states are reasons to preserve Bryan's work, not to redraft it. `all_time` is excluded. [S6]

The PRE reminder means **preparation is accounted for**: a usable draft already exists, the relevant human-edited/reflected note needs no draft, or a real launch was accepted and its target recorded. A failed launch does not count. Completion does not mean the agent finished, and it does not mean the human reviewed the period. POST remains the explicit human review, correction, reflection, and planning action.

Update POST prose to remove the normal “launch an agent now” step, while retaining a recovery path if PRE was skipped or the draft failed. “Review prepared draft; if missing, retry preparation” makes the happy path clear without concealing failures.

### Shared days and parent/child synthesis

On January 4, weekly and quarterly preparation will overlap under the current schedules. A single coordinating agent may satisfy both reminders: draft the due week first, then refresh the quarter's brief and draft the quarter. Alternatively, use separate agents with explicit sequencing. Do not require a new agent-management subsystem in the review queue.

The reason to sequence related drafting is evidence freshness: a quarter brief contains weekly Headlines and Reflection leads; a year brief contains the quarters' corresponding summaries. However, an agent cannot manufacture the Reflection Bryan has not written yet. Parent drafts prepared before POST must acknowledge missing child reflection/review coverage. If the human changes a child materially, refresh an untouched parent draft when useful, subject to the normal ownership guard. Do not block the entire morning walk waiting for every historical period to be reviewed. [S6]

Cleanup follows launches as requested, but its wording should distinguish yesterday's settled agents from today's new work. Avoid accidentally dismissing or restarting the just-launched preparation agents. If the launch itself needs a repair, perform that necessary repair at the launch step; no ordering system can make broken infrastructure productive.

## Recurrence synchronization: the important limit

**Matching recurrence text and the first date does not create a transactionally linked pair.** Tasks advances each recurring row independently. `when done` calculates from its completion date; ordinary recurrence calculates from the occurrence's reference date. New occurrences copy the description but clear block links and dependency IDs. [S9]

Example: both weekly tasks are scheduled November 9. PRE is completed November 9, so its successor is November 16. POST is not completed until November 17, so its `when done` successor is November 23. On November 16 the new PRE can appear while the old POST is still open. Even fixed-date recurrence does not make two unfinished series share the same current occurrence after one has advanced and the other has not.

For the first implementation I recommend a precise, modest contract: **same nominal review calendar and same initial occurrence date; independently completed obligations may be overdue independently.** Edit both schedules intentionally when changing the review appointment. Do not silently reschedule the other row when one is completed or snoozed. This is a requirement clarification, not a claim that the original strongest reading has been implemented.

Preserve the three existing recurrence rules initially. Do not append `when done` everywhere just to silence a lint: `every 3 months … when done` can shift the quarter sequence if completion slips into another month. Conversely, replacing weekly `when done` with fixed recurrence creates catch-up occurrences that Bryan may not want.

Adding `#post` to quarterly/yearly will expose the existing `checklist_repeat_not_when_done` warning, because those rules are calendar-anchored. Review the lint's guidance as part of implementation: calendar review appointments are a legitimate reason to retain fixed cadence. Do not weaken all recurrence validation or silently change the dates to accommodate the warning. The warning should explain catch-up behavior and distinguish it from malformed recurrence. [S2, S3]

If the requirement is **strict automatic pair synchronization despite delayed completion, snoozes, and missed periods**, defer the two independent series design. That stronger feature needs one calendar/series authority and period-keyed preparation/review state, with target identity surviving recurrence. A derived PRE preparation row or explicit series reconciliation could then be designed. It is meaningfully larger than adding three reminders and a comparator. I would choose it only after the simpler workflow demonstrates that drift is a real recurring problem.

## Adjustments to the requirements

These are explicit design recommendations, not changes already applied:

1. **Use Review order instead of ordinary priority.** This keeps sequence independent of P-level deferral, decay, and schedule rolls.
2. **Repair quarterly/yearly POST membership.** Add exact `#post` to those existing rows, so all three period reviews belong to the intended group.
3. **Keep existing review appointments.** ISO period boundaries determine which note to draft; they do not silently redefine the review day.
4. **Define “same day” as a shared nominal schedule for the initial version.** Strict synchronization after divergent completion is a separate, larger design. This is the main deliberate narrowing of the request.
5. **Make PRE about launching or accounting for a draft, not waiting.** POST checks readiness and remains unfinished if meaningful human review is still outstanding.
6. **Put the final Morning review closeout last within POST.** Give Weekly, Quarterly, Yearly POST orders 10, 20, 30 respectively, and leave Morning review at Default. This uses the requested POST capability and makes “closeout” true on review days. Ordinary days still show only the daily closeout. Preserve Ctrl+Enter's boundary behavior.
7. **Do not add agent auto-launching or hard task dependencies.** The request is for reminders. A human still chooses and starts agents; the queue should not own their lifecycle.

## Critique of the ritual

The idea is sound if PRE stays preparatory. The latency benefit is straightforward but unmeasured: early drafting can finish during the intervening work; it is not a guarantee that a long quarter/year job will be ready at POST.

Browser batching is reasonable, but “Read email” can expand without bound. I would suggest **Triage email** if Bryan means clearing the input channel before planning: identify actionable items, capture them, and leave substantial replies for scheduled work. This is an optional wording change, not a necessary part of the feature.

SASE cleanup similarly combines failure repair, dismissals, inbox review, and updating software on every machine. Keep the stated ordering, but consider a short operating limit and capture substantial maintenance as separate work. Otherwise an effort to make planning smoother may make morning entry more expensive.

Three reminders are preferable to one generic daily “Update any period notes?” row: they disappear on days when irrelevant and state exactly which period kind needs preparation. Conversely, three prompts should not imply three mandatory agents. On overlap days, one coordinated launch can cover the requested targets.

Avoid building a scheduling framework to solve a three-group ordering preference. An optional number, deterministic tie behavior, and short labels are sufficient. Revisit automatic schedule coupling only with evidence of repeated pair drift.

## Implementation surface and acceptance criteria

This is a research design, not an implementation performed in this turn.

The core changes belong in Rust freshness parsing/placement, `FreshnessRow`/`QueueEntry`, the PRE/POST comparator, and CLI JSON/explanations; and in the corresponding bob-ledger-tools placement/evaluation/queue/API fragments. Navigation consumes the resulting queue; the editor action and lightweight mark must preserve that single authority. Existing CLI schema is 15 and the inspected plugin freshness namespace is v13; version exposed contract changes deliberately and document the new field. Do not infer a Mac Capture change unless its actual consumers require one. [S3, S4]

Deployment order matters: ship matching evaluator support and editor behavior before annotating the live rows. Keep normal bob-cli release policy and plugin build/deploy workflow. A mixed old/new evaluator can show different order between terminal and Obsidian, so include a compatibility check or visible capability diagnostic. Do not edit generated plugin `main.js` by hand.

Focused acceptance cases:

| Area | Required proof |
| --- | --- |
| Defaults | With no new fields, all queue rows and ranks match the old behavior. |
| PRE and POST | Explicit orders sort before Default; ties retain existing path/line order; PRE cannot overtake its tier boundary. |
| Scope | NEW and every other tier remain unchanged, including ordinary task priority and freshness decisions. |
| Visibility | Tomorrow's preparation remains absent even at order 1; due `[?]` checklist behavior remains intact; hidden/dependency-blocked rows remain excluded. |
| Metadata | Bracket/paren, duplicates, invalid numbers, wrong placement, code examples, and non-checklist use have deterministic outcomes and diagnostics. |
| Parser preservation | Changing order preserves every Tasks suffix field. Specifically reproduce the misplaced-field experiment and prove there is no false early eligibility or completion against an unparsed recurrence. |
| Recurrence | Real Tasks completion copies order to the new occurrence, advances its date, and retains correct behavior with insertion above or below the completed row. |
| Walk continuation | Finish the highest-order task when it is physically below the next task; auto-advance follows queue order. Verify `[s`, `]S`, undo, stale-cache line shifts, and the last PRE/POST boundary. |
| Calendar | November 9 weekly only; January 4 weekly + quarterly; January 11 weekly + yearly; 53-week years; future dates; overdue target resolution. |
| Drift | Demonstrate the November 9/17 split explicitly. The UI and documentation must not promise synchronized current dates. |
| Agent outcomes | Already drafted, edited/reflected, duplicate launch, failed launch, missing note, open-period refusal, and parent/child overlap. |
| Presentation | Source fallback, keyboard access, light/dark contrast, and the existing footer's ranks/counts remain clear. |

Use the existing Rust freshness state/placement suites and bob-plugins' freshness queue/placement/footer and checklist navigation suites. A small real-Obsidian scratch-vault test is justified for recurrence preservation and line-shifting advancement; a comparator unit test cannot establish those facts. No implementation tests were run because no implementation was made.

## Sources and reproducibility

**S1 — live vault snapshot.** Read-only query on 2026-11-05, using `bob query --format json --tasks-file -` with:

```text
path regex matches /^gtd_daily[.]md$/
not done
```

A separate native Dataview TASK query corroborated the task descriptions/tags. Tasks JSON supplied original Markdown, recurrence, scheduled dates, and native priority. Line numbers are transient and zero-based in this query; the evidence above uses titles and fields rather than treating line numbers as identities.

**S2 — established review contract.** Audited reads of `decisions:review-walk-is-tiered`, `decisions:recurring-occurrences-walk-when-due`, `decisions:answering-advances-the-walk`, and the period-note/footer glossary. Current contract: [bob-cli `docs/freshness.md`](https://github.com/bobs-org/bob-cli/blob/6e816775f0252b6bd68af2900699e6bd537168fb/docs/freshness.md), especially §§4, 6, 7 and CL/RC examples.

**S3 — Rust implementation.** bob-cli commit `6e816775f0252b6bd68af2900699e6bd537168fb`: `src/native/freshness/state.rs` (`queue`, `QueueEntry`), `scan.rs` (`checklist_candidate_visible`, `checklist_lints`), `placement.rs`, and `cli.rs`. [Queue comparator](https://github.com/bobs-org/bob-cli/blob/6e816775f0252b6bd68af2900699e6bd537168fb/src/native/freshness/state.rs#L890).

**S4 — JavaScript queue and presentation.** bob-plugins commit `7b7c52f10f42f1b38553e991a0750852d2a46761`: `plugins/bob-ledger-tools/src/110-freshness-queue.js`, `080-freshness-placement.js`, `230-plugin-freshness-api.js`, `120-freshness-footer.js`, `138-checklist-task-marks.js`, and `135-priority-marks.js`. [Shared queue](https://github.com/bobs-org/bob-plugins/blob/7b7c52f10f42f1b38553e991a0750852d2a46761/plugins/bob-ledger-tools/src/110-freshness-queue.js).

**S5 — navigation identity and advancement.** Same bob-plugins revision: `plugins/bob-navigation-hotkeys/src/538-review-walk-identity.js`, `539-plugin-review-walk-return.js`, and `scripts/test-navigation-checklist-ctrl-enter.cjs`; existing tests cover recurrence insertion above/below and stale queues. [Anchor implementation](https://github.com/bobs-org/bob-plugins/blob/7b7c52f10f42f1b38553e991a0750852d2a46761/plugins/bob-navigation-hotkeys/src/538-review-walk-identity.js).

**S6 — period calendar and ownership.** Same bob-cli revision: [docs/periods.md](https://github.com/bobs-org/bob-cli/blob/6e816775f0252b6bd68af2900699e6bd537168fb/docs/periods.md), `src/native/periods/calendar.rs`, `cli.rs`, and `instructions.rs`. These establish ISO identities, draft refusal rules, Review ownership, and parent-summary inputs.

**S7 — ordinary priority has scheduling semantics.** [bob-cli docs/projects.md, Priority property and scheduled rolls](https://github.com/bobs-org/bob-cli/blob/6e816775f0252b6bd68af2900699e6bd537168fb/docs/projects.md#priority-property-and-scheduled-rolls); bob-plugins `040-priority-roll.js`; official [Tasks priority sorting](https://publish.obsidian.md/tasks/Queries/Sorting). The recommendation to keep review sequence separate is an inference from these contracts.

**S8 — custom-field parser constraint.** Same bob-cli revision: `src/native/dataview/tasks/task.rs` (`try_take_dataview_field`) and `src/native/freshness/placement.rs`. Independently reproduced with the installed binary in a disposable scratch vault, as described above.

**S9 — upstream recurrence and Dataview behavior.** Obsidian Tasks checkout at `7e3ba597d9a65ee9b21f6040c9d703d44c4c7b1f`: [Recurring Tasks documentation](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/7e3ba597d9a65ee9b21f6040c9d703d44c4c7b1f/docs/Getting%20Started/Recurring%20Tasks.md), [Dataview Format documentation](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/7e3ba597d9a65ee9b21f6040c9d703d44c4c7b1f/docs/Reference/Task%20Formats/Dataview%20Format.md), `src/Task/Recurrence.ts`, and `src/Task/Task.ts#createNextOccurrence`. Read from the audited local checkout, not web-fetched repository files. Upstream source supports the design analysis; installed-plugin conformance still needs verification during implementation.

## Recommended solution

Implement a PRE/POST-only **Review order** field with explicit values before Default and stable file/line ties. Add weekly, quarterly, and yearly preparation reminders at 10, 11, and 12; put SASE cleanup at 20 and calendar/weather/email at 30. Preserve the other PRE schedules and behaviors. Add `#post` to quarterly/yearly, order the period reviews before the daily closeout, and keep completion delegated to Tasks.

Mirror the existing review calendars and initial occurrence dates, resolve the exact period before launching, and treat PRE completion as “draft exists or launch accepted.” Keep human reflection in POST. Ship only after field placement, recurrence preservation, and queue advancement have been verified together. Accept independent overdue occurrences explicitly; if automatic lockstep is essential, design a shared period-series authority before creating two independent recurring series.
