# Morning GTD and pomodoro practice review (2026-10-01)

Researcher: `grk`. Independent vault-and-ledger review of the GTD / pomodoro changes Bryan made on 2026-09-30 through 2026-10-01 (local night of 30 Sep → 1 Oct). Other swarm reports were not consulted.

## Bottom line

The new machinery (sticky Next/Pending, ledger Today, freshness review, `]s` jumps, REVIEW chip) is coherent. The practice that is supposed to feed it is not. Sticky lanes froze the pre-cutover WIP pile at **PENDING 50/10** and **NEXT 28/15**. The morning review was rewritten four times in two days, grew from "≤5 min" to "≈10 min", and still starts with a freshness queue that is **empty tonight** and becomes a **~26-task stale wave tomorrow**. Meanwhile the daily `^gtd` wrapper has been **cancelled 21 of the last 22 days** (2026-09-10 through 2026-09-30, with 8–9 Sep as the last completions). Execution of named pomodoros is strong (~5 hours every September day). Control of the lists is not.

The ranked list at the end is the action. The rest of this note is the evidence.

## Bias, as requested

Bryan has not been doing morning GTD for about three weeks, and says many tasks still need to be marked complete. That bias is real and it cuts in a specific direction:

- **Open ≠ still to do.** PENDING 50 and NEXT 28 are upper bounds. Some of those rows are finished work that was never closed. The *shape* of the failure (one file, sticky lanes, no daily release) is still true even if a close-the-done pass halves the counts.
- **Cancelled `^gtd` ≠ skipped teeth / email / Keep in real life.** The wrapper in each daily note is what got cancelled. Habit recurrences in `gtd_daily.md` last show completions on 2026-09-28. Treat the checkboxes as a stale system of record, not a biography.
- **Freshness counts tonight are post-seed.** `bob freshness list` reports `due 0`, `new 0`, `fresh 198`, `refreshed_today 390`. The REVIEW step of the new morning ritual is a no-op until tomorrow.
- **September pomodoro minutes are trustworthy.** Closed 🍅 lines with `[t::]` were written throughout the month, including on days the GTD wrapper was cancelled.

## What changed in the last 36 hours

Observed in the vault (`~/bob`) and in `bob plan` / `bob freshness list` on 2026-10-01 ~00:30 EDT.

1. **`#now` retired; Next and Pending are sticky; Today is read from open Pomodoro Task Links.** Decision records `task-lanes-are-sticky` and `today-is-read-from-the-ledger`. Caps: NEXT 15, PENDING 10, themes 3, links 10. GTD is exempt. Release is Alt+N. Unlinking never demotes.
2. **`freshness.md` created** as the review surface: counts, a one-key-per-outcome table, and a Tasks query grouped by freshness tier. Dash gained a **REVIEW chip**. `obsidian_vimrc.md` bound `]s` / `[s` to jump-to-next/prev due task. The keymap task `bob_gtd.md#^keymaps` was closed 2026-10-01.
3. **Morning review rewritten (third time in 48 hours):**
   - 2026-09-29: cancelled the old "Review READY" and "Review WIP+NEXT and plan Pomodoros" recurrences (they had been scheduled since 2026-09-09 and were never completed).
   - Same day: "Pick today: ≤3 themes from yesterday + NOW". Cancelled 2026-09-30 when `#now` died.
   - 2026-09-30 22:13 UTC: "Morning review (≤5 min): PENDING → NEXT → READY; link today's work, release the rest with Alt+N".
   - 2026-10-01 02:41 UTC: **"Morning review (≈10 min): REVIEW until 0 new (`]s`, Alt+Shift+F), then clear what's due; PENDING → NEXT; link today's work, release the rest; ≤3 themes, highlight first"**. READY dropped off the daily path. Weekly prune gained leftover REVIEW, per-note `task_refresh`, and "projects with no Next or Ready task".
4. **Freshness seed ran.** 390 tasks stamped today; Ready stamps are spread 2026-09-25 → 2026-10-01 (26 / 26 / 26 / 15 / 20 / 38 / 47). Interval is 7 days. `stale_daily_budget` is unset.
5. **`bob_gtd` project created 2026-09-30** ("Improve GTD morning review process"). Today's BOB pomodoro already links `bob_gtd#^diagnostics` (ready-count alarms) and `bob#^auto-decay-priorities`.
6. **Today's ledger** (`2026/20261001.md`, created 00:07): open placeholders `GTD` (exempt) + `BOB` + `READ` + `MEMORY`. `bob plan`: **3/3 themes, 4/10 links, TODAY 5, PENDING 50/10, NEXT 28/15**. Highlight is BOB. No 🍅 has been started.

## What the ledger actually shows

### Pomodoro execution is the healthy part

| Window | Days with a closed 🍅 | Closed 🍅 | Minutes | Median length | `^gtd` completed | `^gtd` cancelled |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Jun 2026 | 30/30 | 223 | 7530 | 25m | 12 | 1 |
| Jul 2026 | 31/31 | 188 | 7105 | 25m | 19 | 12 |
| Aug 2026 | 30/31 | 250 | 9540 | 30m | 25 | 6 |
| Sep 2026 | 30/30 | 222 | 8800 | 32m | 7 | 23 |
| Sep 24–30 | 7/7 | 55 | 2340 | 35m | 0 | 7 |
| 2026-10-01 | 0/1 | 0 | 0 | — | open `[*]` | — |

September work happened. Named themes happened (GTD, BOB, SASE, REMOTE, GOALS, …). The GTD *wrapper* did not. Last `^gtd` completions: 2026-09-01–05, 08–09. From 2026-09-10 through 2026-09-30 the daily `[[gtd_daily]]` task is cancelled, usually the next calendar morning (`[cancelled::]` is the following date). That is a close-the-loop-by-cancelling habit, not a forgotten checkbox.

September still logged **51 closed GTD-named pomodoro components**. Those sessions were system-building (dash, freshness, `bob_gtd`, capture), not the morning checklist. GTD time is going to GTD tooling.

### The one day that explains the lane overflow

2026-09-29 closed 8 pomodoros, then left **20 open named placeholders** with **19 open themes and 73 open links**: BOB, GOALS, SASE, DECKS, READ, MISC, FINAL, RENAME, CLEANUP, REMOTE, SERVICE, NEW FEATURES, SUDO, FAST TESTS, QUEUE, SCHEDULE, AUDIT MEMORY, GATES, LATER. The LATER bucket alone holds on the order of twenty Task Links.

That is the whole Next+Pending inventory poured into one daily ledger. `plan.inventory_labels` already names `LATER`, `MISC`, `NEW FEATURES`, `SASE` as storage labels. They still count as themes when left open. The 3-theme / 10-link budget exists to stop this. 2026-09-29 is the only September day over those caps — and it is the day sticky lanes would have promoted nearly every linked task.

2026-09-30 then ran 12 closed pomodoros / 455 minutes (CLEANUP, RESEARCH, BOB ×7, BETS, MEMORY) with `^gtd` cancelled and no leftover opens. The 2026-09-29 placeholders are still open on that historical note. They no longer count as Today. The tasks they promoted are still Next or Pending, because nothing releases them.

`bob plan` tonight: **PENDING 50, NEXT 28**. The 2026-09-30 sticky-lanes research predicted ~48 `[/]` and ~25 `[*]` at cutover. The live counts are those piles plus two days of work.

### Where the 78 sticky-lane tasks live

Lane-visible (not `#hide`, not `_templates`/`_conflicts`, not future-scheduled, not dependency-blocked):

| Lane | Count | Cap | Median age (created) | Dominant file |
| --- | ---: | ---: | ---: | --- |
| PENDING `[/]` | 50 | 10 | 9d | `sase.md` 40 |
| NEXT `[*]` | 28 | 15 | 10d | `sase.md` 20 |
| READY `[ ]` | 209 | none | 19d | `gkeep_inbox.md` 65, `sase.md` 59 |
| Blocked `[?]` (visible) | 266 | — | — | mostly P-level `scheduled` |

50 PENDING: 2 created in the last day, 18 in 2–7d, 14 in 8–14d, 13 in 15–30d, 3 older (max 53d, `bob.md#^better-roadmaps`). 49 of 50 have no `scheduled` date. Almost all are Normal priority. They are not "today's work"; they are last month's working set, frozen.

`sase.md` badges: 59 Ready, 60 Next/WIP, 137 Blocked, 8 done/canceled. `bob projects list`: 257 open / 119 shown on that one project, plus 41 active projects of which many have **0 shown** tasks and a still-open `^prj`.

`gkeep_inbox.md`: **65 Ready, 0 done**. Pull writes them as TODO. They have been Ready since capture (created 2026-09-09 through 2026-09-29). Freshness stamps on that file cluster on 2026-09-25, which is tomorrow's first stale wave.

Whole vault: **797** open `#task` lines (including hidden and blocked).

### Recurring GTD source of truth is stalled

`gtd_daily.md` recurrences, `repeat:: every day when done`, still scheduled in the past:

- 2026-09-29: weather, teeth, pills, calendar, email, Keep import.
- 2026-09-30: the new ≈10 min morning review.
- 2026-10-04: morning stretches (Blocked).
- 2026-10-05: weekly prune (Blocked).

Completing or cancelling the daily note's `^gtd` wrapper does not tick these rows. The wrapper and the checklist are two clocks. The template stamps the wrapper `[*]` (Next) every morning, so GTD starts the day already in a sticky lane.

### Freshness will not save the morning

In-scope Ready stamps (198 visible non-recurring Ready):

| `fresh` date | n | First due (interval 7) |
| --- | ---: | --- |
| 2026-09-25 | 26 | 2026-10-02 |
| 2026-09-26 | 26 | 2026-10-03 |
| 2026-09-27 | 26 | 2026-10-04 |
| 2026-09-28 | 15 | 2026-10-05 |
| 2026-09-29 | 20 | 2026-10-06 |
| 2026-09-30 | 38 | 2026-10-07 |
| 2026-10-01 | 47 | 2026-10-08 |

Tonight: 0 new, 0 due. Tomorrow: ~26 stale Ready, many of them unclarified Keep captures. The morning text says "REVIEW until 0 new, then clear what's due" with no stale budget. Freshness, by design, **never looks at Next or Pending**. The 78 tasks that blow the caps are invisible to the step the review now leads with.

The freshness research (`research:202609/ready_task_freshness_review`) already named the load: ~25 stale/day from a ~176 Ready pool at 7 days, plus returning deferrals, and it told you to set a STALE goal meter. `freshness.stale_daily_budget` is still `null`.

### Today's plan is already full, before GTD

At 00:07 the new daily note was created with four open named pomodoros and four non-GTD links. That is the theme cap. A morning review that is supposed to *pick* today's work from PENDING/NEXT has nowhere to put a fifth theme and only six link slots left. The highlight is BOB (`auto-decay-priorities` + `diagnostics`), so the first non-exempt session is more GTD-tooling and capture work.

The daily note was created at midnight after a 2340–0000 BOB session on 2026-09-30. "Morning" GTD is being attempted at the end of the previous day's energy.

## What is going wrong

### 1. Sticky lanes without a release habit freeze last month's WIP

The design is correct: unlinking must not forget. The cost, stated in `decisions/task-lanes-are-sticky`, is 2–3 tasks/day of lane growth unless caps, chips, a daily release, and a weekly prune actually run. They have not. Alt+N is the whole forgetting mechanism, and the only daily instruction that uses it sits on a recurrence last scheduled 2026-09-30 and never completed.

### 2. The daily ledger was used as a roadmap

2026-09-29's 20 open names / 73 links is the anti-pattern the budget was written to catch. LATER/MISC/SASE as open pomodoros are a second Ready list with a worse query. The migrate-unfinished-from-yesterday recurrence was cancelled the same day, so leftovers stay on the historical note and the tasks stay sticky.

### 3. Morning GTD is skipped by cancelling the wrapper, then rebuilt

Four review texts in two days, all cancelled or unstarted. The list of steps got longer each time. A 10-minute review over 50 Pending + 28 Next + a freshness wave is not 10 minutes. When the ritual is heavier than the skip cost (one `[-]` on `^gtd` the next morning), skip wins.

### 4. Review order matches the new toy, not the fire

Freshness is a good Ready-lease. It is the wrong first step while PENDING is 5× its cap and the freshness queue is empty. Starting at REVIEW also invites rubber-stamping: Alt+Shift+F until 0 new, on an inbox that has not been clarified, produces 65 "fresh" unprocessed captures and a dead signal.

### 5. Collect is working; Clarify is not

Keep import is a daily recurrence. 65 Ready tasks sit in `gkeep_inbox.md` with 0 completions. Pulling inbox items into Ready makes them show up on the dash, in freshness, and in any "project/area ≥5 Ready" diagnostic. That diagnostic (`bob_gtd#^diagnostics`) will be red on `gkeep_inbox.md` (65) and `sase.md` (59) every day until those files are treated as inboxes/portfolios rather than Next lists.

### 6. `sase.md` is a portfolio pretending to be a project

40 of 50 Pending and 20 of 28 Next live in one note, which already has 31 listed sub-projects. Sub-projects with 0 shown tasks and an open `^prj` mean next actions never left the parent. No morning ritual can make a 119-shown-task file feel like a 10-item Pending cap.

### 7. Two GTD clocks, plus habits in the same wrapper

Body/admin recurrences (weather, teeth, pills, calendar, email, Keep) share `gtd_daily.md` and the daily `^gtd` wrapper with the work review. Cancelling the wrapper hides whether the habits were done. Leaving the source rows on 2026-09-29 means the real checklist never advances. The wrapper is born `[*]`, so it is a sticky Next before anyone has reviewed anything.

### 8. Meta-work is winning the GTD pomodoro

Keymaps shipped. Diagnostics are already in today's highlight. `bob_gtd.md` still lists the obsolete requirement "WIP and Next sections should not show `#now` tasks!". Building alarms that will scream at `sase.md` and `gkeep_inbox.md` is easier than releasing 40 Pending rows. That is the same pattern as 51 GTD-named pomodoros in a month of cancelled morning reviews.

### 9. Pomodoro length is drifting at the tail

September median 32m is fine. 41 sessions over 50m (max 195m) and 12 closed pomodoros / 7.5h on 2026-09-30 make the 🍅 a time-log, not a focus box. Repeating BOB through the day is a valid single theme. A 195-minute "one pomodoro" is not.

### 10. The 10-minute budget is being asked to do the cutover

Lane triage, inbox clarify, close-the-done, and the first freshness wave are one-time (or weekly) work. They are currently packed into a daily recurrence timed at 10 minutes, scheduled to wait for Monday for the prune (2026-10-05) while caps are already blown.

## What is going right (keep these)

- **Named pomodoros and the 3-theme cap, on a normal day.** After 2026-09-29, 2026-09-30 closed its sessions and left 0 opens. Today is 3/3 with 4 links. That is the budget working.
- **GTD exempt, highlight = first non-exempt.** The model (review is free, the bet is BOB/READ/MEMORY) is right. Fill it after the review.
- **Today from open Task Links.** The 2026-09-29 leftovers do not haunt today's Today set. Closed 🍅 lines are history.
- **Freshness seed was staggered by note, Ready only.** Blocked/Next/Pending got today, so returning deferrals arrive as STALE. That matches the cutover spec.
- **One key per review outcome** on `freshness.md` is the right UX. `]s` / Alt+Shift+F in the source note beats a dash walk.
- **Weekly prune text** (release to caps, promote from Ready, P-levels, hours vs created/closed, leftover REVIEW, orphan projects) is the right weekly. It needs a cutover *today*, then Mondays.
- **Work volume.** ~5h/day, every day, through the month GTD was skipped. The problem is selection and closure, not effort.

## Ranked recommended improvements

Do these in order. Later items assume the earlier ones landed. Times are honest for the current pile, including the close-the-done bias.

1. **Catch-up pass on PENDING/NEXT before any new ritual (45–90 min, today).** Walk PENDING then NEXT. For each row: mark complete if it is done (Bryan already knows many are), Alt+N release if it is not this week's work, P-level defer if it should sleep, leave it only if it would survive a 10+15 cap. Stop at PENDING ≤10 and NEXT ≤15. Do not wait for Monday. Soft caps with no release are decoration. After this pass, `bob plan` should be quiet on `pending_cap_exceeded` / `next_cap_exceeded`.

2. **Do the work review after sleep, on an empty-enough ledger.** Create the daily note with the GTD placeholder (and at most yesterday's highlight). Fill BOB/READ/MEMORY *after* the review. Midnight 🍅 belong on yesterday's note (as 2340–0000 already did). A 3/3 plan at 00:07 is a night bet, and it blocks the morning pick.

3. **Split the wrapper.** Body/admin recurrences (weather, teeth, pills, calendar, email, Keep) stay as their own daily ticks. The work review is one short task: release overflow, pick ≤3 themes, link ≤10, start the highlight. Completing `^gtd` currently claims a bundle that has not been true for weeks. A cancelled wrapper then erases the evidence.

4. **End every day with zero non-GTD open placeholders.** Cancel leftover open 🍅 names at close. 2026-09-29's 20 opens are still sitting on that file. Open inventory labels (LATER, MISC, NEW FEATURES, SASE) are Ready in disguise; put that work on the task line (Next, P-level, or a sub-project) and keep the ledger as today's bet. Optionally turn `plan.strict` on so a fourth theme has to be a conscious override.

5. **Clarify `gkeep_inbox.md` out of Ready before tomorrow's freshness wave.** 65 unprocessed captures should not be dash-Ready and should not be in the 7-day lease. File to a project, P-level, cancel, or keep in a true inbox that freshness ignores (`task_refresh: 90` on that note is the immediate lever; moving off Ready is the real fix). Tomorrow's ~26 due Ready are heavily 2026-09-25 stamps from this file. Alt+F on them is how the queue goes dead.

6. **Put STALE on a budget; keep NEW uncapped.** Set `freshness.stale_daily_budget: 15` (the config example). Morning REVIEW: clear NEW to 0, then at most 15 STALE (or stop when the 10-minute work-review budget is gone). Leftover STALE is the weekly prune's job, which the new text already says. Without this, 2026-10-02 through 2026-10-08 are 15–47 stale Ready/day on top of lane work.

7. **Lead the daily work review with lanes, then freshness.** Order: PENDING (close / release / keep) → NEXT (pick today's links) → write ≤3 themes → then `]s` for NEW plus the STALE budget. Freshness does not see the 78 sticky-lane tasks. Leading with it tonight is a no-op; leading with it tomorrow is a 26-item Ready walk while PENDING is still 50.

8. **Hold `bob_gtd#^diagnostics` until the caps are green.** Alarms for "file ≥5 Ready", "Ready ≥ R", "scheduled ≥ S" will fire on `gkeep_inbox.md` and `sase.md` every day and teach you to ignore chips. The REVIEW chip is already enough signal. Spend the GTD pomodoro on recommendation 1, not on building the dashboard for a pile you have not cut.

9. **Move next actions off `sase.md` onto the sub-project that owns them.** 40 Pending in one note cannot meet a cap of 10. The parent keeps the `^prj` bet and a handful of Next; the rest live on `sase_pager`, `sase_remote`, `sase_memory`, … Weekly prune already asks for projects with no Next or Ready — use that to either park a 0-shown `^prj` as waiting or give it a single next action.

10. **Keep the 🍅 as a 25–35 minute box; split long work into another named session.** Median is already there. Close at ~30–40m even if the theme continues (2026-09-30's seven BOB sessions are the right shape; a 195m close is not). The time total on the heading stays honest, and Today/links stay a session bet rather than a half-day bag.

11. **Sweep process residue this week.** Drop the `#now` requirement on `bob_gtd.md`. Archive the cancelled NOW / old READY-walk rows out of `gtd_daily.md` (they already have `done_tasks: [[done/gtd_daily_done]]`). Remove or ignore `plan.max_now` in `~/.config/bob/config.yml`. Cancel the still-open placeholders on `2026/20260929.md` so historical open counts stop looking like a live plan.

12. **Make Monday prune a maintain step, with a created-vs-closed and hours check.** After the cutover in (1), the weekly is: NEXT ≤15, PENDING ≤10, one Next or Ready per active project, leftover STALE or longer `task_refresh`, and "did I close as many as I created, and did hours match the 🍅 log?" That last check is how the close-the-done bias gets caught next time instead of silently inflating Pending.

## Trial keep-rule (two weeks, through 2026-10-13)

The sticky-lanes trial window is 2026-09-30 → 2026-10-13. A fair test needs the release habit in place, otherwise the keep-rule is "lanes grew because nobody released them".

- **Keep** if, by 2026-10-13: PENDING ≤10 and NEXT ≤15 on at least 5 weekdays; `^gtd` work-review completed (not cancelled) on those days; open non-GTD placeholders at midnight = 0; freshness NEW = 0 each morning; STALE leftover is weekly, not daily.
- **Revisit the design** if those are true and the lanes still grow past cap, or if Blocked recovery to Ready is eating committed work.
- **Revisit the ritual** (not the lanes) if the work-review is still being cancelled. Four rewrites in two days already failed; a shorter review on a smaller list is the next experiment, not another chip.

## Commands used

```text
bob plan -f json          # 2026-10-01: 3/3 themes, 4/10 links, TODAY 5, PENDING 50/10, NEXT 28/15
bob freshness list -f json
bob query --format json --tasks 'not done'
bob projects list
```

Vault git on `gtd_daily.md`, `dash.md`, `freshness.md`, `bob_gtd.md`, `2026/20260929.md`, `2026/20260930.md`, `2026/20261001.md`. Daily-note pomodoro parse for 2026-01-01..2026-10-01. Decision records `task-lanes-are-sticky`, `today-is-read-from-the-ledger`. `docs/plan.md`, `docs/freshness.md`. `~/.config/bob/config.yml` `plan:` and `freshness:` (budget unset).
