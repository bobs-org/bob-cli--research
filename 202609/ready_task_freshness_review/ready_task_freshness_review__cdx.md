# Task freshness: a rolling review lease for Bob tasks

**Researcher:** cdx  
**Date:** 2026-09-30  
**Scope:** independent analysis for the `bob-cli-2y` GTD redesign; no peer-swarm
reports were consulted.

## Executive conclusion

The core idea is good. It replaces “look at every Ready task every morning” with a
rolling, explicit assertion that a human has recently looked at each task. That is a
large improvement over using the Ready lane itself as a review queue.

I would not implement the requirements literally, though. Four changes are important:

1. A missing freshness date must be valid and mean **never reviewed / due now**. New
   captures must not be stamped fresh merely because software created them.
2. Only a human action may advance the freshness date. An automated Blocked → Ready
   transition must invalidate freshness, not falsely claim that a human reviewed the
   task.
3. Newly captured/unreviewed tasks and periodically stale tasks should be distinct
   queues. The former is the daily safety guarantee and should not be hidden by a
   daily cap; the latter can be capped and caught up weekly.
4. Freshness should get its own review note or review mode. It should not become a new
   checkbox status or a fifth overlapping section in `dash.md`; the newly accepted
   TODAY/PENDING/NEXT/READY lane model should remain mutually exclusive.

The recommended representation is:

```markdown
- [ ] #task Pick up our daughter [fresh:: 2026-09-30] [refreshDays:: 7] ^pickup
```

with the containing note optionally declaring:

```yaml
---
task_refresh_days: 30
---
```

The interval precedence should be task `[refreshDays:: N]`, containing-note
`task_refresh_days`, global `freshness.default_days`, then a built-in seven-day
fallback. The due date is derived, never stored: a task refreshed on September 30 with
a seven-day interval becomes due on October 7.

The live vault makes per-note overrides important. There are currently 186 Ready tasks,
176 after excluding recurring tasks. A literal seven-day cadence would mature about
25 non-recurring tasks per day. The design is still viable, but only if large,
low-volatility backlogs such as `gkeep_inbox.md` and `sase.md` use longer intervals and
the daily UI separates new work from review debt.

## What I examined

### Project design and implementation surfaces

I read the active `bob-cli-2y` epic and its plan, plus the accepted decisions
`task-lanes-are-sticky` and `today-is-read-from-the-ledger`. The relevant constraints
are now unusually clear:

- TODAY is read from Task Links under today's open Pomodoros.
- PENDING (`[/]`) and NEXT (`[*]`) are sticky lanes.
- READY (`[ ]`) is a lane, not an inbox marker or review status.
- BLOCKED (`[?]`) is derived from dependencies and future schedules.
- The dashboard's TODAY/PENDING/NEXT/READY sections are intentionally disjoint.

I also inspected the current source-of-truth plugins. `bob-ledger-tools` already owns a
versioned synchronous API over the Tasks cache, live query refresh, Today, and lane
counts. `bob-navigation-hotkeys` already has guarded task-line mutation, cross-note Task
Link resolution, Dataview-property upserts, counted operations, and task navigation.
`task-status-cycler` and `block-id-prompt` own other supported human task transitions.
Those are the natural integration points; a brand-new plugin would duplicate too much
of this machinery.

### Live-vault measurement

I ran the existing `dash.md` Tasks blocks read-only through `bob query`, then queried
the READY block's native JSON on 2026-09-30. The snapshot was:

| Measurement | Count |
| --- | ---: |
| Ready tasks shown by `dash.md` | 186 |
| Ready recurring tasks | 10 |
| Ready non-recurring tasks | 176 |
| Ready tasks in `gkeep_inbox.md` | 65 |
| Ready tasks in `sase.md` | 48 |
| Ready tasks in `sase_remote.md` | 11 |
| Ready tasks with missing/invalid `created` | 2 |
| Created today | 1 |
| Created yesterday | 1 |
| Created 2–6 days ago | 20 |
| Created 7–29 days ago | 134 |
| Created 30–89 days ago | 27 |
| Created at least 90 days ago | 1 |

The seven-day steady-state estimate is therefore:

```text
176 eligible Ready tasks / 7 days = 25.1 periodic reviews per day
```

That is far better than scanning 186 tasks every day, but it is not free. For
illustration, giving the 65-item Keep inbox a 30-day interval, the 48-item `sase.md`
backlog a 14-day interval, and the remaining 63 tasks the default seven days reduces
the simple steady-state estimate to about 14.6 tasks per day. Normal task edits and
lane movement would reduce it further.

The measurement also shows why a single undifferentiated “stale” queue is dangerous.
At rollout every legacy task lacks a freshness date, so 176 tasks would become due at
once. The UI needs an explicit bootstrap/legacy-debt state and must order recent
captures ahead of it.

## Is the proposal a good idea?

### What it gets right

The proposal fixes the actual failure mode. The pickup example is not fundamentally a
prioritization problem; it is an **acknowledgement latency** problem. A captured task is
useful only after it has entered a trusted review surface. Treating absence of `fresh`
as “never acknowledged” gives that surface a durable, queryable invariant.

It also decouples two jobs that the old Ready review conflated:

- READY answers “is this actionable but not committed?”
- freshness answers “when did I last verify that this record is still trustworthy?”

That separation matches the new lane architecture. Freshness can change without
changing Today, lane, priority, schedule, or dependencies.

Finally, a rolling cadence is a sensible way to distribute review work. The official
[GTD Weekly Review checklist](https://gettingthingsdone.com/wp-content/uploads/2016/04/GTD-WeeklyReview.pdf)
requires getting inboxes clear, reviewing next-action lists, and evaluating projects
one by one. Freshness turns part of that burst into small daily slices while retaining
a visible debt count.

### What it does not solve

Freshness is not a replacement for inbox clarification. Looking at “Pick up our
daughter” and pressing Refresh without deciding whether it belongs Today, needs a due
date, or is already obsolete is a failed review even though the metadata looks green.
The workflow must define Refresh as a confirmation, not a dismiss button.

It also cannot replace the whole GTD Weekly Review. It does not examine calendars,
Waiting For items, project support material, project outcomes with no next action,
checklists, or Someday/Maybe. A small weekly system review should remain even if the
large Ready scan disappears. The existing weekly lane prune is a good home for that
minimal check.

There is also a risk of false precision. Seven days is a service-level objective, not a
fact about a task's natural decay. A volatile family/logistics task and a low-value
software idea do not deserve the same revisit rate. The default is reasonable, but the
overrides are essential rather than ornamental.

## Required adjustments

These are deliberate changes to the stated requirements.

| Original direction | Recommended adjustment | Why |
| --- | --- | --- |
| Every Ready task has a `fresh` date. | `fresh` is optional; absence is a first-class `unreviewed` state and is due now. | Otherwise creation/import must invent a human review that never occurred. |
| Making any task Ready updates freshness. | A **human** gesture ending in Ready advances `fresh`; an automated unblock clears/invalidates it. | `fresh` is defined as human confirmation, so automation cannot truthfully advance it. |
| All Ready tasks participate. | Exclude recurring tasks by default. | Their recurrence/schedule already controls resurfacing, and Tasks may copy arbitrary inline fields into the next occurrence. Freshness would be redundant or inherited incorrectly. |
| One out-of-date queue, possibly capped at N. | Split `NEW/UNREVIEWED` from `STALE/EXPIRED`; a cap applies to expired and legacy debt, never silently to newly captured work. | The pickup guarantee must survive a large old backlog. |
| Put freshness into the dashboard review. | Add a dashboard chip linking to a separate freshness review note/mode. | A freshness queue overlaps READY and would break the accepted mutually exclusive lane sections. |
| Any edit makes a task fresh. | Touch freshness only for supported human mutations whose final state is Ready. Do not infer manual edits or file modification time. | File mtime is note-wide, sync can change it, and machine edits are not human confirmation. |
| Seven days is the operative cadence. | Keep seven days as the default, but ship project/note overrides and an initial daily budget at the same time. | The current non-recurring Ready population implies about 25 reviews/day at seven days. |
| Freshness can eliminate a weekly review. | Retain a short weekly lane/project/system review. | Freshness reviews records; GTD's weekly review also checks system completeness and project coverage. |

## Proposed semantics

### Glossary definition

The glossary strand should define the concept approximately as follows:

> **Task Freshness** (freshness) is the validity period of a human confirmation
> attached to an actionable Ready task. `[fresh:: YYYY-MM-DD]` records the most recent
> local calendar date on which a human reviewed the task and confirmed that it still
> belongs, remains actionable, and has correct wording, priority, project placement,
> schedule, and dependencies. The freshness deadline is that date plus the effective
> refresh interval. Missing, invalid, future-dated, invalidated, or expired freshness
> is due for review. Freshness is orthogonal to Today, task lane, and Blocked state and
> never changes them by itself.

The strand should also say explicitly that a review is expected to end in one of:

- refresh as-is;
- edit, move, reprioritize, schedule/defer, or change dependencies and then refresh;
- commit/link it to current work;
- complete or cancel it.

### Stored fields

Use ISO local dates and integer day counts:

```markdown
[fresh:: 2026-09-30]
[refreshDays:: 14]
```

and note frontmatter:

```yaml
task_refresh_days: 30
```

Why integer days rather than Dataview duration strings:

- the only needed unit is a calendar day;
- Rust, JavaScript, YAML, Dataview, and Tasks can validate an integer identically;
- it avoids disagreements about `1 month`, daylight-saving boundaries, abbreviations,
  and malformed duration text;
- the unit is visible in the field name.

`refreshDays` should accept only integers in a documented range such as 1–3650.
Invalid values produce a lint and fall back to the next precedence level. Do not add a
`never` sentinel in v1; forgotten Ready tasks are exactly what this feature is meant to
prevent.

The effective interval is:

```text
task [refreshDays:: N]
    > containing note task_refresh_days: N
    > config freshness.default_days
    > built-in 7
```

“Project override” should mean the project note that physically contains the task.
Following arbitrary parent/project links would introduce ambiguity, cycles, and a much
larger resolver. Since Dataview makes page fields available to tasks, containing-note
inheritance is also the native data model: see
[Dataview task metadata](https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-tasks/)
and [adding metadata](https://blacksmithgu.github.io/obsidian-dataview/annotation/add-metadata/).

### Eligibility and state

A v1 task is freshness-eligible when all of the following are true:

- it is a real `#task`;
- its status is Ready (`[ ]` / Tasks type `TODO`);
- it passes the same visibility rules as the current READY dashboard block (`#hide`,
  templates, conflicts, and future schedules remain excluded);
- it is not Today during the brief interval before link-driven promotion catches up;
- it is not recurring.

The evaluator returns one of:

| State | Meaning | In due queue? |
| --- | --- | --- |
| `unreviewed` | no valid `fresh` field | yes |
| `invalid` | duplicate, malformed, or future `fresh`; invalid override is also linted | yes |
| `stale` | `today >= fresh + effectiveDays` | yes |
| `fresh` | confirmation remains inside its interval | no |
| `ineligible` | not a visible non-recurring Ready task | no |

The due boundary should be inclusive. With `[fresh:: 2026-09-30]` and seven days, the
task is fresh through October 6 and due October 7. All calculations use the vault's
local calendar day, not UTC timestamps.

Dataview already parses ISO dates and supports task-level inline fields; the
[metadata type documentation](https://blacksmithgu.github.io/obsidian-dataview/annotation/types-of-metadata/)
supports this representation. The Tasks plugin does not need to understand `fresh` as
a native date: custom functions can read `task.originalMarkdown`, and Tasks documents
custom filtering/sorting over task objects in its
[filter](https://publish.obsidian.md/tasks/Queries/Filters) and
[sorting](https://publish.obsidian.md/tasks/Queries/Sorting) references.

### Ordering

Use deterministic priority buckets:

1. unreviewed tasks created/captured since the last daily review, newest first;
2. other unreviewed tasks, newest first during migration so yesterday's captures cannot
   hide behind a legacy backlog;
3. stale tasks, earliest freshness deadline first (most overdue first);
4. within a tie, higher task priority, then path and source line.

For Google Keep, retain the rule that a new imported task has no `fresh` field. If
Keep's source creation date can differ materially from the import date, add a separate
`[captured:: YYYY-MM-DD]`/import date in `bob gkeep pull` and use that for bucket 1.
Do not overload `fresh` with the import date.

## The review experience

### Keep the lane dashboard intact

Do not add a `FRESHNESS Tasks` section beside TODAY/PENDING/NEXT/READY. The same Ready
task would then appear in two sections, undoing the exclusivity work in `bob-cli-2y`.

Instead:

- add a dashboard chip such as `REVIEW 17 · TODAY 6` linking to a dedicated
  `freshness.md` review note;
- show a richer header in that note, for example
  `NEW 2 · STALE 15 · LEGACY 41 · REFRESHED TODAY 6`;
- display the ordered due queue in one Tasks block, optionally limited after the new
  items;
- expose oldest lateness and invalid-field warnings in the chip tooltip or block.

Tasks query limiting retains the total match count (for example “15 of 57 tasks”), so a
limited review list need not hide the backlog; see the
[Tasks limiting documentation](https://publish.obsidian.md/tasks/Queries/Limiting).

`REFRESHED TODAY` should count unique active tasks whose valid `fresh` date is today,
even if a refresh was followed by moving the task to NEXT or PENDING. Otherwise the
counter falls when the review succeeds. It is a task count, not an event count; pressing
Refresh twice on one task still counts once.

### Commands and keymaps

Add commands to Bob Navigation Hotkeys rather than a new plugin:

- **Open freshness review**: open the review note and initialize/rebuild the queue.
- **Next due task** and **Previous due task**: traverse the ordered queue across notes,
  opening the source task and centering it.
- **Refresh current task**: guarded-upsert `[fresh:: today]` and make no semantic change
  to the task. After success it should advance to the next due task by default; provide
  a command variant that stays in place if that proves useful.

A sensible provisional mapping is `Alt+Shift+J/K` for next/previous (mirroring the
existing J/K direction convention) and `Alt+R` for refresh-and-next. The implementation
phase should audit the live Obsidian hotkey map before fixing these defaults. As with
the existing Alt+N and Ctrl+Shift+J/K paths, Vim-normal capture handling may be needed
so Obsidian and CodeMirror do not double-dispatch or swallow the chord.

The command must work from a source task and from a dedicated Task Link by reusing the
existing cross-note resolver. A refresh is idempotent on the same local day. Duplicate
`fresh` fields are a refusal/lint, not something silently normalized.

### Daily and weekly routine

Recommended morning sequence:

1. Pull Google Keep.
2. Clear **NEW/UNREVIEWED since the prior review**. These items are never suppressed by
   the stale-review budget.
3. Review up to `freshness.daily_limit` expired or legacy items (start with 10–15).
4. Continue the current PENDING → NEXT → READY planning flow and link today's work.

Recommended weekly sequence:

1. Clear all remaining freshness debt or deliberately raise a task/note interval.
2. Prune PENDING/NEXT to their caps.
3. Check project outcomes with no current next action, Waiting For, calendar, and
   Someday/Maybe—the portions freshness cannot cover.

The daily limit is a workload valve, not a correctness definition. The counts must
remain visible when the limit is reached.

## Automatic update policy

The following matrix preserves the meaning “last human confirmation.”

| Event | Freshness behavior |
| --- | --- |
| New task from `bob capture`, Bob Mac Capture, or `bob gkeep pull` | leave `fresh` absent |
| Explicit Refresh command | set `fresh` to today |
| Supported property/keymap edit that ends with the task Ready | set `fresh` to today in the same guarded transaction |
| Alt+N release from NEXT/PENDING to Ready | set `fresh` to today; the human just made the keep/release decision |
| Human removal of schedule/dependency that immediately recovers Ready | set `fresh` to today |
| Move a Ready task to another note/project via the supported keymap | set `fresh` to today after the move; the new note's interval then applies |
| Automated `task-status-hooks` Blocked → Ready | remove/invalidate `fresh`, so the newly actionable task is due |
| Automated Ready → Blocked or Ready → Next promotion | preserve the field but exclude the task while ineligible |
| Manual Markdown edit outside supported commands | no automatic change, as requested |
| Done/cancelled task | preserve historical metadata; exclude it |
| Recurring occurrence | exclude recurring tasks in v1 rather than risk inheriting the prior occurrence's date |

The automated-unblock rule is the most important departure from the prompt. Stamping
today there would make the data internally contradictory: it would assert a human
confirmation that did not happen. Removing the field loses the old confirmation date,
but correctly records that there is no longer a valid confirmation for the current
actionable state. If preservation of that history becomes valuable later, add a
separate invalidation date; do not make `fresh` lie.

## Implementation architecture

### 1. Define one contract first

Add `docs/freshness.md` in bob-cli with:

- the glossary semantics above;
- eligibility and precedence;
- local-date and inclusive-boundary rules;
- ordering;
- transition matrix;
- JSON conformance vectors covering missing, malformed, duplicate, future, boundary,
  task override, note override, global fallback, recurrence, Today, and status changes.

Use the same pattern as the recently implemented Today contract. The JavaScript and
Rust surfaces are deployed separately, so executable shared code is unrealistic;
shared vectors are the practical defense against semantic drift.

### 2. Make `bob-ledger-tools` the read-side owner

Bump its API from v2 to v3 and add synchronous methods along these lines:

```javascript
freshness(task, now?)
isFreshnessDue(task, now?)
freshnessRank(task, now?)
freshnessBudget(now?)
freshnessQueue(now?)
```

The plugin already obtains the Tasks cache, computes lane budgets, reads metadata, and
triggers `obsidian-tasks-plugin:reload-open-search-results`. The evaluator can parse
`task.originalMarkdown`, look up `task.file.path` in Obsidian's metadata cache for
`task_refresh_days`, and read the global fallback config. A full-vault pass over the
current few hundred tasks is cheap enough to compute on demand; premature persistent
caching would create more invalidation bugs than value.

Extend the existing local-midnight timer so the Tasks query refresh event fires when a
new calendar day changes freshness eligibility even if no file changed. Re-render the
freshness header/chip on Tasks cache updates, relevant metadata changes, config reload,
and midnight rollover.

### 3. Use `bob-navigation-hotkeys` for the write side

Reuse its existing:

- `upsertBulletProperty` placement before a trailing block ID;
- raw-line/preimage guards;
- cross-note Task Link resolution;
- cursor centering and open-note navigation;
- counted/batch transaction patterns where appropriate.

For background cross-file writes, use Obsidian's guarded `Vault.process()` API rather
than an unguarded read/modify pair. Obsidian's
[Vault developer documentation](https://docs.obsidian.md/Plugins/Vault) specifically
recommends `process()` to avoid losing concurrent changes. On any path/line/raw-text
mismatch, rebuild the queue and show a refusal; never write to a guessed line.

The navigation session should store stable `(path, blockId if present, line,
originalMarkdown)` identities. Block IDs are preferable, but many current Ready tasks
do not have one, so v1 cannot require them. A missing/moved line simply causes a guarded
re-resolution or skip.

### 4. Touch the other human writers narrowly

Add a small, byte-compatible `fresh` upsert helper (with shared vector tests) to:

- `task-status-cycler` for human status changes that end Ready;
- `block-id-prompt` for a human transition that ends Ready, if any remain after the
  sticky-lane work;
- the property/move/release paths in `bob-navigation-hotkeys`.

Do not make every writer depend on the runtime presence of Ledger Tools to preserve a
write. The read policy belongs in its API, but a supported task mutation should still
be able to stamp the simple ISO field if Ledger Tools is temporarily unavailable.

### 5. Change `task-status-hooks` only for machine invalidation

When a derived Blocked task automatically returns to Ready, remove/invalidate a valid
`fresh` field on that task line in the same planned mutation. Dry-run JSON should report
the invalidations so the behavior is auditable. Do not alter freshness for unrelated
idempotent passes.

This is the only required bob-cli mutation for v1. A new public CLI is not necessary to
prove the workflow; `bob query` plus plugin tests can inspect it. A later read-only
`bob freshness` command would be useful if headless agents need the ordered queue, but
it should be justified by a real consumer rather than added speculatively.

### 6. Add config and vault surfaces together

Suggested global config:

```yaml
freshness:
  default_days: 7
  daily_limit: 12
```

Suggested initial note overrides, to be tuned from actual use rather than treated as
permanent policy:

```yaml
# gkeep_inbox.md and low-volatility idea backlogs
task_refresh_days: 30

# active but large project/backlog notes such as sase.md
task_refresh_days: 14
```

Create the dedicated review note, add its chip to `dash.md`, and update the morning
GTD chore to name the new/unreviewed pass explicitly after Keep import. Keep the
existing PENDING/NEXT/READY flow; freshness is an input-quality pass before planning,
not a replacement for lane selection.

The existing bullet-property config can expose `fresh` as a date and `refreshDays` as
a small scalar choice list (for example 1, 3, 7, 14, 30, 90) in Ctrl+Shift+P, while the
dedicated refresh key remains the fast path.

## Migration and rollout

### Do not bulk-mark legacy tasks fresh

A migration that writes today's date to every existing task would make rollout look
clean while destroying the field's meaning. It would also create a large, needless Git
diff and make all tasks mature on the same day seven days later.

Instead:

1. Install the evaluator with all missing fields classified as `unreviewed`.
2. Label pre-rollout missing fields as **LEGACY** in the UI; they remain due but are
   budgeted separately.
3. Sort newly captured/yesterday items above legacy debt.
4. Work the legacy queue in daily slices and clear it at the first weekly review.
5. As tasks are edited, moved, released to Ready, completed, cancelled, or refreshed,
   the debt naturally drains and due dates spread across days.

If an explicit migration epoch is needed to distinguish NEW from LEGACY, store it in
configuration, not on every task. For Keep imports whose source `created` date is not a
reliable arrival date, add the separate capture/import date described earlier.

### Two-week trial

Instrument only data the system already has. After 14 days evaluate:

- Were all tasks newly captured before the morning review acknowledged that day?
- Did `NEW` return to zero on at least 10 of 14 days?
- Is freshness debt flat or falling after excluding the bootstrap cohort?
- What are the median and 90th-percentile daily review counts?
- Does the full morning sequence stay within five minutes on at least 10 of 14 days?
- Which notes dominate due volume, and should their note interval be lengthened?
- Were there any duplicate/malformed fields, write conflicts, or Tasks refresh misses?
- Did freshness ever change a lane, schedule, priority, or Task Link unexpectedly? The
  answer must be no.

Tune interval overrides before adding more automation. If the queue is still too large,
raise intervals for low-volatility notes and reduce the expired-task budget while
keeping NEW uncapped. Do not silently age tasks out of the system.

## Tests and acceptance criteria

At minimum, automated tests should cover:

- missing `fresh` is due and new capture/import leaves it missing;
- a seven-day interval is due exactly on day 7;
- local-day behavior around midnight and daylight-saving changes;
- invalid, duplicate, and future dates are visible due/lints;
- precedence of task, note, config, and built-in intervals;
- note override changes immediately when a task is moved;
- recurring tasks are excluded;
- TODAY/NEXT/PENDING/BLOCKED/done/cancelled tasks are ineligible;
- a supported Ready edit writes one canonical field before the block ID;
- same-day refresh is idempotent;
- automated unblock invalidates rather than advances freshness;
- an automated hook rerun is idempotent;
- queue ordering puts recent unreviewed tasks before legacy and stale tasks;
- refresh count remains after the task moves to another active lane;
- midnight and cache changes reload open Tasks queries only when needed;
- cross-note navigation survives absent block IDs and safely refuses stale preimages;
- limiting shows N rows while the full due count remains visible;
- all prior Today/lane conformance vectors remain unchanged.

Manual acceptance should include the exact motivating scenario: create a Keep task the
previous evening, pull it the next morning, verify it appears in NEW before old review
debt, open it with the next-task keymap, refresh or schedule/link it, and confirm that
the counters and queue update immediately.

## Risks and mitigations

### Review becomes a mechanical “snooze” action

This is the largest product risk. Put the confirmation checklist in the glossary and
review-note help text, show alternative actions in the property picker, and make the
button say **Refresh** rather than “Dismiss.” Measure churn and cancellations, not just
the number of refresh presses.

### Metadata churn and sync conflicts

Inline metadata produces daily note edits, possibly across multiple machines. A
central freshness ledger would reduce churn, but it would require stable identities
that many existing tasks lack and would break when tasks move. Inline metadata is the
right v1 tradeoff because it travels with the task and is inspectable. Mitigate churn
with one date per task per day, guarded `Vault.process()` writes, file-local batching
when refreshing several tasks, and the existing vault-sync discipline.

### Query/API drift

Tasks does not natively model the custom field. Keep the query expression tiny and put
parsing in the versioned Ledger Tools API. Pin `task.originalMarkdown`, `task.file.path`,
line number, and reload-event behavior in tests, just as the Today implementation pins
its internal Tasks event.

### False confidence from “fresh” projects

A set of individually fresh tasks can still omit a next action for a project. Keep the
weekly project/outcome check. Freshness is record validity, not project completeness.

### Backlog starvation under a daily cap

Never apply the cap before sorting or to the NEW bucket. Show total counts and oldest
lateness even when only N stale rows are rendered. The weekly pass is the backstop for
old debt.

### Project-level override ambiguity

Define it as the containing note's frontmatter. Do not traverse `parent` links in v1.
If tasks later become routinely stored away from their project notes, revisit that
definition with explicit identity and cycle rules.

## Alternatives considered

### Review only yesterday's captures

This is the smallest fix for the pickup scenario and should effectively exist as the
NEW bucket. By itself it does not detect a once-valid task whose wording, priority, or
project placement has become stale. The hybrid NEW + periodic freshness design retains
the guarantee without giving up longer-term trust.

### Keep reducing every project's Ready list to five daily

This repeatedly rereads stable tasks and couples review burden to project grouping. It
also pressures the user to manipulate lanes just to make the dashboard smaller.
Freshness is a more direct control variable.

### Randomly sample N tasks per day

Tasks itself documents a random-backlog example, and random sampling is useful for
serendipity. It cannot guarantee timely review of yesterday's capture and gives no
per-task service-level bound. Random order could be an optional tie-breaker after NEW,
not the core policy.

### Infer freshness from file modification time or Git history

File mtime is note-wide, sync rewrites it, and neither a modification nor a commit
proves the task was read. This would be cheap but semantically wrong.

### Store freshness in a central ledger

This avoids task-line churn and can preserve event history. It also needs stable task
IDs, reconciliation for moved/deleted tasks, another state store, and UI to explain
disagreements. Since many live tasks lack block IDs, inline metadata is substantially
safer for v1.

### Make freshness a checkbox status or lane

This would collide with the accepted status model and make a task choose between
“Ready” and “stale,” even though staleness is an orthogonal quality. Reject it.

## Sources

- Project evidence: epic `bob-cli-2y`; artifact
  `plan:202609/retire_now_sticky_lanes.md`; accepted decisions
  `task-lanes-are-sticky` and `today-is-read-from-the-ledger`; bob-cli
  `docs/plan.md`; bob-plugins `plugins/bob-ledger-tools/main.js`,
  `plugins/bob-navigation-hotkeys/main.js`, `plugins/task-status-cycler/main.js`,
  and `plugins/block-id-prompt/main.js`.
- Live-vault evidence: read-only `bob query --tasks-note dash.md --format markdown`
  and native JSON queries with `--origin dash.md`, captured on 2026-09-30.
- [GTD Weekly Review checklist](https://gettingthingsdone.com/wp-content/uploads/2016/04/GTD-WeeklyReview.pdf).
- [Dataview: metadata on tasks and lists](https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-tasks/).
- [Dataview: adding metadata](https://blacksmithgu.github.io/obsidian-dataview/annotation/add-metadata/).
- [Dataview: metadata types](https://blacksmithgu.github.io/obsidian-dataview/annotation/types-of-metadata/).
- [Tasks: filters and custom functions](https://publish.obsidian.md/tasks/Queries/Filters).
- [Tasks: custom sorting](https://publish.obsidian.md/tasks/Queries/Sorting).
- [Tasks: limiting and total counts](https://publish.obsidian.md/tasks/Queries/Limiting).
- [Obsidian developer docs: guarded vault writes](https://docs.obsidian.md/Plugins/Vault).

## Recommended solution

Implement **Task Freshness as a review lease on visible, non-recurring Ready tasks**, not
as a status. Store a human-confirmed local date in optional `[fresh:: YYYY-MM-DD]`
metadata; treat absence as unreviewed and due now. Derive the deadline from
`[refreshDays:: N]` → containing-note `task_refresh_days` → global default → seven
days. Keep invalid/future dates visible as due lints.

Put the policy and conformance vectors in bob-cli, make `bob-ledger-tools` API v3 the
read-side evaluator and counter, and use `bob-navigation-hotkeys` for cross-vault
next/previous/refresh commands with guarded writes. Narrowly update the other supported
human task writers so a human edit ending in Ready stamps today. Make automated
Blocked → Ready transitions invalidate freshness; never let software claim a human
review. Leave creation and Keep import unstamped.

Preserve the exclusive TODAY/PENDING/NEXT/READY dashboard. Add only a `REVIEW due ·
today` chip there, linking to a dedicated freshness review note with separate NEW,
STALE, and LEGACY counts. Every morning, clear NEW after `bob gkeep pull`, then review
up to 10–15 expired/legacy tasks. Never let that budget hide new captures. Keep a short
weekly pass for residual freshness debt, lane pruning, Waiting For, calendars, and
projects without next actions.

Roll out without bulk-stamping legacy tasks. Start with seven days globally, 30 days
for the Keep/low-volatility backlog and roughly 14 days for large active backlogs, then
tune from a two-week trial. Success means yesterday's captures are always acknowledged,
the due debt is flat or falling, the morning routine remains under five minutes, and
freshness never changes a task's execution state by itself.
