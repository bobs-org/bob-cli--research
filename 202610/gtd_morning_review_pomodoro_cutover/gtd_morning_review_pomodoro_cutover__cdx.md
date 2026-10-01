# Review of the new morning GTD and Pomodoro process

**Researcher:** cdx  
**Snapshot:** 2026-10-01 00:40 EDT  
**Scope:** Bryan's current Bob vault, the new daily/weekly review tasks, today's
Pomodoro ledger, and the preceding 30 days of ledger data.

## Bottom line

The redesign is directionally very good. The strongest changes are the retirement of
`#now`, making the daily ledger the source of truth for Today, limiting a day to GTD
plus three themes, introducing a freshness queue instead of rereading all Ready work,
and explicitly pruning the sticky Next and Pending lanes. Today's draft plan is much
more coherent than the recent baseline: it has exactly three non-GTD themes, four
non-GTD task links, and five Today tasks, with no unresolved links or ledger cleanup
needed.

What is wrong is mainly the operating capacity around that design. The normal morning
ritual assumes it can repair a month of drift and then sustain a large task system in
about ten minutes. It cannot. At the snapshot, the visible commitment lanes contain 28
Next tasks and 50 Pending tasks against caps of 15 and 10. The capture inboxes contain
66 open tasks. The freshness cutover has also scheduled a large first-week review
wave. Unless recovery and steady-state review are separated, the new routine will
either take far longer than advertised or encourage superficial confirmations that
make the system look clean without making it trustworthy.

The Pomodoro data tells a similar story. Work volume is high; focus boundaries are
not. September contains 222 completed timed sessions over 30 active days, but 55
different theme names, more than three themes on 17 days, and many very long sessions.
The three-theme rule is therefore addressing a real problem. It now needs an equally
clear rule for session length, breaks, and what counts as an outcome.

## Evidence and limitations

I used read-only Bob interfaces (`bob query`, `bob plan`, `bob freshness`,
`bob capture-pomodoros`, `bob task-status-hooks --dry-run`, and
`bob randomize --dry-run`). The vault's last sync had succeeded at 00:38 EDT, two
minutes before the snapshot. No other swarm researcher's report or transcript was
consulted.

The user's warning about incomplete historical marking is important. I do **not**
treat open-task counts, September closure counts, or old recurring chores as exact
measures of work performed. Timed ledger entries are more useful for describing work
rhythm, while current lane sizes and future review dates are useful for forecasting
the load the new process will actually present.

Because the snapshot was taken just after midnight, today's open placeholders and the
still-open GTD task are plans, not evidence that the morning routine failed. The
relevant evidence is the state the morning routine will encounter.

## What the redesign gets right

### 1. Today is now concrete

Today's ledger contains an exempt GTD entry followed by BOB, READ, and MEMORY. Those
three themes hold four non-exempt links; the GTD wrapper makes five Today tasks in all.
This is inside the 3-theme and 10-link budgets. The first non-exempt entry, BOB, is the
highlight. This is a substantial improvement over September 29, whose ledger retained
20 open placeholders after eight completed sessions.

The important conceptual improvement is that Today means a real task link under an
open Pomodoro, not a tag or vague intention. That makes the plan observable and makes
unplanning distinct from changing a task's longer-lived lane.

### 2. The daily/weekly split is sensible

The new morning review focuses on new and due freshness items, then Pending, Next, and
today's plan. The weekly prune handles deeper lane cleanup, Ready promotion, deferral,
throughput, and projects without an actionable task. That is the right separation:
daily review should restore situational control; weekly review should restore system
trust.

### 3. Freshness is a better review primitive than scanning Ready

The new mechanism asks whether each task is still correctly worded, prioritized,
routed, scheduled, and dependent. It also supports different refresh intervals. This
is better than repeatedly reading a large undifferentiated list.

Today's freshness state—0 new, 0 due, and 198 in-scope fresh tasks—looks clean. The
date pattern strongly indicates the documented one-time seed: Ready work was staggered
across seven freshness dates, while other open non-recurring lanes were stamped today.
That is a useful cutover, but it is initialization, not evidence that 390 tasks were
manually reconfirmed today.

### 4. The theme cap addresses observed context spread

Across September there were 222 completed timed sessions totaling 8,800 minutes:
about 7.4 sessions and 293 logged minutes per active day. The same month used 55
distinct theme labels, averaged 3.87 themes per active day, and exceeded three themes
on 17 of 30 days. A hard daily theme budget is therefore supported by the data rather
than being arbitrary.

## What is still wrong

### 1. The steady-state review does not fit in ten minutes

The seeded Ready pool is scheduled to become stale in the following pattern:

| Date | Ready tasks due for freshness review | Already future-scheduled tasks returning | Combined decisions |
| --- | ---: | ---: | ---: |
| Oct 2 | 26 | 13 | 39 |
| Oct 3 | 26 | 19 | 45 |
| Oct 4 | 26 | 21 | 47 |
| Oct 5 | 15 | 24 | 39 |
| Oct 6 | 20 | 10 | 30 |
| Oct 7 | 38 | 9 | 47 |
| Oct 8 | 47 | 8 | 55 |

These sets are disjoint in the current snapshot: the first is visible Ready work and
the second is future-scheduled work. New captures will add more. Ten minutes permits
only 11–20 seconds per decision at those volumes, which is not enough to inspect
wording, priority, project, schedule, and dependencies—the very meaning of a freshness
confirmation.

The configuration currently has a seven-day default interval and no stale daily
budget. With 198 Ready tasks, even the long-run base load is about 28 reviews per day
before arrivals and resurfacing. The routine's promise to “clear what's due” therefore
has no bounded stopping rule.

A plausible starting experiment is a 14-day default interval plus a 20-item daily
budget, keeping seven days only for volatile notes and using 30/90 days for stable
ones. The exact numbers should be measured, but the governing equation must hold:

`daily capacity >= Ready pool / average interval + new arrivals + resurfaced tasks`.

### 2. Sticky lanes have not yet been migrated into their intended meaning

The current plan reports 28 Next tasks and 50 Pending tasks, versus caps of 15 and 10.
That means 53 explicit releases are required merely to reach the configured limits.
Concentration makes the problem clearer:

- `sase.md` contains 40 of the 50 visible Pending tasks and 20 of the 28 visible Next
  tasks.
- The oldest visible Pending item was created August 9; the oldest Next item was
  created August 18.
- Only two Pending tasks are actually linked into today's plan.

This is not a reason to reverse the sticky-lane decision. It is evidence that Pending
is currently functioning as “has been touched sometime” rather than “work I am
actively carrying.” A 50-item In Progress lane cannot guide action. The process must
make explicit release a non-negotiable exit condition, particularly after a lapse.

The existing cap of 10 may itself be generous for genuine concurrent work. After the
one-time cleanup, it would be worth testing a Pending cap of five while retaining a
larger Next cap.

### 3. Recovery work is mixed into the normal ritual

The system has several distinct recovery inventories:

- 65 open tasks in `gkeep_inbox.md` and one in `mac_inbox.md`;
- 53 excess visible Next/Pending commitments relative to the current caps;
- 82 open tasks scheduled on or before today;
- a `bob randomize --dry-run` plan that can reroll 38 P1/P2 tasks but deliberately
  leaves 42 P0 tasks due (and skips one Next and one In Progress task).

These sets overlap, so they should not be summed. They do show that normal operation
has not resumed yet. Importing Google Keep is not the same as clarifying its 65 open
items, and a clean freshness meter after seeding is not the same as a trusted backlog.

Trying to absorb this into a ten-minute daily review risks two bad outcomes: either
the morning ritual becomes an hour-long avoidance target, or tasks are stamped/released
without real decisions. A dedicated recovery sweep should establish the initial state;
only then can the recurring ritual be evaluated.

### 4. The morning checklist mixes habits, collection, review, and planning

`gtd_daily.md` currently has separate recurring tasks for weather, teeth, supplements,
calendar/event notes, email, Google Keep import, stretching, and the dense morning
review. Today's daily note adds another wrapper task linking to `gtd_daily.md`.

This produces ambiguous completion semantics. The wrapper can be completed while its
component tasks remain open, and the components can be completed without proving the
review's lane and plan invariants. Basic habits also create task-history and recurrence
noise in the same system used for trusted next actions.

Separate these layers:

- a lightweight morning habit checklist for teeth, supplements, weather, and
  stretching;
- collection steps for calendar, email, and Google Keep;
- one GTD review workflow with explicit, inspectable exit criteria.

“Read Email” is also too passive and unbounded. A better instruction is to capture or
clarify actionable email for a fixed time, leaving communication work in the task
system rather than doing an indefinite inbox session during review.

### 5. Inbox collection is present, but inbox clarification is implicit

The routine says to import Google Keep and review freshness. It never plainly says
“empty or intentionally defer each inbox.” The result is observable: 65 open tasks
remain in the Google Keep inbox. Freshness can eventually surface them, but after a
seed it deliberately spreads them across days, so an unprocessed inbox can appear
fresh.

The process needs separate definitions:

- **collected:** the item is safely in Bob;
- **clarified:** it is actionable, trashed, reference, someday/maybe, or waiting;
- **organized:** an actionable item has a project/context, priority or deferral, and a
  useful next action.

Daily review should either drive capture inboxes to zero or record an explicit count
and deadline for a recovery queue. “Imported” should never be the success condition.

### 6. The weekly review omits aging Blocked/Waiting work

There are 266 tasks bearing the Blocked status. Of those, 253 are legitimately hidden
by future schedules and 13 are dependency-blocked. Ten dependency-blocked tasks also
carry overdue schedule dates, including several from June. The new weekly prune checks
projects with no Next or Ready action, but it does not explicitly review old blockers,
waiting-for follow-ups, or dependencies whose promised date has passed.

Add an aging review: oldest dependency blockers, Blocked tasks whose schedule is in the
past, and projects whose only action is blocked. This should be weekly, not part of the
morning scan.

### 7. The Pomodoro ledger is partly a focus tool and partly retrospective timekeeping

September's median session was 35 minutes and the mean was 39.6. Forty-one of 222
sessions exceeded 50 minutes, eight exceeded 90 minutes, and the longest was 195
minutes. There were also two overlapping adjacent entries. Flexible focus blocks are
not inherently a problem, but a 95–195 minute “Pomodoro” no longer provides frequent
stop, break, and re-plan points. It behaves more like a time log.

Choose which role the ledger is meant to play. If it is a focus feedback loop, close
and reopen the same named theme after at most 50 minutes, take a real break, and log a
one-line result or Work Log summary. If long uninterrupted flow is intentional, label
that as a different block type rather than allowing one measure to mean both focused
iterations and retrospective elapsed time.

The historical capacity of roughly seven sessions per active day is also a better
planning prior than the ten-link ceiling. Ten is a safety cap, not a daily target.

### 8. Current metrics are too contaminated to optimize from

September contains 542 tasks with September creation dates, 251 with September
completion dates, and 49 cancellations. There are also 284 open tasks created before
September and 227 open tasks with no creation date. Those numbers look like backlog
growth, but recurrence, newly added metadata, and missing retrospective completions
make that conclusion unsafe.

Do not “repair” the month by marking every old routine as completed. Mark genuinely
completed outcome tasks with the best available actual completion date; cancel or skip
routine instances that were not performed; and leave uncertain tasks for an explicit
clarify/release decision. After the recovery sweep, declare a clean baseline date and
measure forward for two weeks.

## Ranked recommended improvements

1. **Run a one-time recovery/migration sweep before judging the new routine.** In
   dedicated Pomodoros, process the 66 capture-inbox tasks, release at least the 53
   excess Next/Pending commitments, and explicitly decide the 42 P0 tasks that
   `bob randomize` will not defer. Do not squeeze this into the recurring ten-minute
   review.

2. **Make the freshness workload mathematically sustainable.** Pilot a 14-day default
   interval and a 20-item stale daily budget, retaining 7-day intervals only where
   change is rapid and using 30/90-day overrides for stable notes. Record review time
   and decisions per minute for two weeks, then adjust using observed throughput.

3. **Turn lane caps into morning exit gates.** End the review with `bob plan`; do not
   call it complete while Next exceeds 15 or Pending exceeds 10 unless an intentional
   exception is recorded. After cleanup, test whether a Pending cap of five better
   matches genuinely active work.

4. **Separate the habit checklist, capture, clarification, and GTD planning.** Keep
   teeth/weather/supplements/stretching out of the trusted action inventory, timebox
   email/calendar collection, and make capture-inbox clarification explicit. Use one
   GTD workflow whose completion means its invariants actually hold.

5. **Add a weekly Blocked/Waiting aging review.** Inspect overdue dependency-blocked
   tasks, old waiting items, and projects whose only next action is blocked. This fills
   the largest omission in the current weekly prune without burdening every morning.

6. **Plan from one must-win outcome plus at most two supporting themes.** Keep the
   three-theme cap, but treat broad names such as BOB, READ, and MEMORY as containers;
   make the first linked task the concrete daily win. Plan roughly six to eight focus
   sessions from the historical capacity and leave slack below the ten-link ceiling.

7. **Restore a real feedback boundary to Pomodoros.** Cap ordinary focus sessions at
   50 minutes, close/reopen when continuing the same theme, take a break, and record a
   short result. Use a distinct label or convention for intentionally long flow/time
   tracking blocks.

8. **Start a clean measurement epoch instead of backfilling ambiguous history.** From
   the post-recovery date, track review minutes, new/due items processed, inbox count,
   lane counts, aging blockers, planned-versus-completed links, and session duration.
   Revisit the process after two weeks; do not automate further from the biased
   September baseline.
