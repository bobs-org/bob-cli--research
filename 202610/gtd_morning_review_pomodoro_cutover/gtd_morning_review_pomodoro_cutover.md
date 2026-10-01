# Morning GTD and Pomodoro practice after the 2026-09-30 cutover: what's wrong and what to change

## Bottom line

**The design is mostly right. The way you run it is what's failing.** All five reports agree, and so do I.
These parts are good and should stay (see [what is working](#what-is-working-and-should-stay)):

- `#now` is retired;
- Today is read from open Pomodoro Task Links;
- Next and Pending are sticky lanes, and only release (Alt+N) lowers them;
- a day is GTD plus at most 3 themes and 10 links;
- the freshness lease replaces scanning READY.

Here is what you're getting wrong, most important first:

1. **The new process changes the tool, but the tool isn't what broke.**
   ([Finding 1](#the-routine-died-over-sequencing-and-the-new-process-does-not-address-it))
   - Morning GTD stopped when the first block of the day became agent operations.
   - From 08-28 to 09-10, GTD was the first block on 11 of 14 days. From 09-11 to 09-30 it was first on 2 of
     20 days. It was missing on 7 of those days, and ops took the first block on 11.
   - Nothing in the new process changes which block comes first.
2. **The trial starts in a failed state.**
   ([Finding 2](#the-lanes-start-the-trial-already-over-their-caps-and-your-close-habit-refills-them))
   - Lanes are at **PENDING 50/10** and **NEXT 29/15**. Those are mostly the 09-29 carry pile plus finished
     work you haven't closed.
   - The one-time triage the design assumes hasn't happened.
   - Your habit of closing blocks with a bare `=x` keeps refilling Pending.
3. **The "≈10 min" morning review is upside down and has no stopping rule.**
   ([Finding 3](#the-morning-review-is-upside-down-and-has-no-stopping-rule))
   - It puts maintenance (the freshness walk) before planning.
   - It has no STALE budget. About **39–55 review decisions arrive each morning from Friday to next Thursday**.
   - The first two mornings are made up entirely of **unclarified Google Keep notes**.
4. **There is no clarify step.** ([Finding 4](#you-collect-but-you-do-not-clarify))
   - The 65 Keep notes count as Ready work.
   - The seed marked them "fresh" even though nobody has looked at them.
5. **Building the system is crowding out running it.** ([Finding 5](#building-the-system-is-crowding-out-running-it))
   - The morning chore had three versions in about 30 hours.
   - About 23% of September's logged time went to GTD and bob tooling.
   - Today's highlight is more GTD tooling.
6. **The life tasks that matter are invisible.**
   ([Finding 6](#the-life-tasks-that-matter-are-the-ones-the-system-lets-slide))
   - The job search has been blocked since June behind one vague task.
   - The five most-rescheduled open tasks are all in `cash.md` or `job.md`.

The fix is mostly about order and limits, not new features:

- triage once;
- protect the first block;
- plan before maintaining;
- set a daily limit on review;
- change how you close Pomodoros;
- stop changing the system for two weeks.

[Ranked list below.](#ranked-recommendations)

![Infographic summarizing the review: keep the ledger-based foundations; GTD lost the first block (11 of 14 days fell to 2 of 20); the lanes start over their caps (Pending 50 vs 10, Next 29 vs 15); the freshness review needs a daily limit (about 300 decisions a week); a better morning sequence with an exit gate; the ten ranked improvements; and the 14-day test](gtd_morning_review_pomodoro_cutover_infographic.png)

## What changed

For reference, these are the changes under review:

| Change | Where |
| --- | --- |
| `#now` retired. Next `[*]` and Pending `[/]` are sticky; only release (Alt+N) lowers them. Today = dedicated Task Links under today's **open** Pomodoros. | `decisions:task-lanes-are-sticky`, `decisions:today-is-read-from-the-ledger`, epic `bob-cli-2y` |
| Caps: 3 themes, 10 links, NEXT 15, PENDING 10. GTD is exempt. The highlight is the first non-exempt entry. | `docs/plan.md`, `~/.config/bob/config.yml` `plan:` |
| Task freshness: `[fresh::]` stamps, the REVIEW queue (`freshness.md`), `]s`/`[s`, Alt+F/Alt+Shift+F. The cutover seed stamped 390 tasks. | epic `bob-cli-31`, `docs/freshness.md` |
| The morning chore became: **"Morning review (≈10 min): REVIEW until 0 new …, then clear what's due; PENDING → NEXT; link today's work, release the rest with Alt+N; ≤3 themes, highlight first."** The weekly prune gained release-to-caps, leftover REVIEW, and "projects with no Next or Ready." | `gtd_daily.md` (vault `83254268`, `0701c271`) |
| Today's ledger was written at 00:07: GTD, then ★BOB, READ, MEMORY. Now 3/3 themes, **5/10 links**, TODAY 6. | `2026/20261001.md`, `bob plan` |

## What is working and should stay

- **Today's plan is the best in weeks.**
  - It has GTD first, 3 themes, and 5 links.
  - Two days earlier, the 09-29 note had 20 open placeholders and 73 link lines.
- **The model is sound.**
  - Each task is in exactly one lane.
  - Release is a deliberate gesture, with a Work Log "why."
  - Today can't go stale, because it's computed from the ledger.
  - The 09-29 leftovers no longer count as Today.
- **Freshness is a better primitive than reading READY.**
  - It has one key per outcome.
  - Its uncapped NEW tier is a real safety net.
- **The volume of work is healthy.**
  - September had 222 closed sessions and 146.7 h, with a session on every day of the month.
  - Selection and closure are the problem, not effort.

## What you are getting wrong

The [ranked recommendations](#ranked-recommendations) cite these findings by number.

### The routine died over sequencing and the new process does not address it

**Finding 1.** I re-parsed the daily ledgers and confirmed cld's finding exactly:

| Period | Days | GTD was the first closed block | No GTD block at all | First block was ops (SHIT, RELAUNCH, RESTARTS, CLEANUP, ATHENA, SASE AGENTS) |
| --- | ---: | ---: | ---: | ---: |
| 08-28 → 09-10 | 14 | **11** | 0 | 2 (with GTD second) |
| 09-11 → 09-30 | 20 | **2** | **7** | **11** |

- **The `^gtd` task.** It was completed on most days through 09-09. From 09-10 to 09-30 it was **cancelled every
  day (21 of 21)**.
- **Late GTD.** When GTD did run in the second period, it ran in the afternoon (13:50, 14:40, 15:25, 17:25). By
  then it was catch-up.
- **GTD without a finish line.** GTD sessions without a clear end turned into ordinary work. On 09-13 there were
  six "GTD" blocks of SASE fixes.
- **Yesterday.** The GTD slot at 06:20 became a 95-minute CLEANUP block (`re-launch-failed`,
  `clean-prompt-history`).

The new process makes the review longer and puts it in the same slot that agents already take over. No dash
chip changes who gets the first block.

### The lanes start the trial already over their caps and your close habit refills them

**Finding 2.**

- **Live `bob plan`:**
  - **PENDING 50/10** and **NEXT 29/15**.
  - NEXT was 28 at 00:30. It reached 29 when `^web-refs` was captured straight into Next and into today's BOB
    block at 00:37.
- **Where they came from:**
  - 40 of the 50 Pending tasks live in `sase.md`, and 39 of those 40 were created in September.
  - The 09-29 note still holds **20 open placeholders**: BOB, GOALS, SASE ×2, DECKS, READ, MISC, FINAL,
    RENAME, CLEANUP, REMOTE, SERVICE, NEW FEATURES, SUDO, FAST TESTS, QUEUE, SCHEDULE, AUDIT MEMORY, GATES,
    LATER.
  - Sticky lanes froze that pile.
- **Inflation is real.** I spot-checked two of gem's "already done" Pending tasks. `sase -p/--print-command`
  and `sase screenshot` both exist, so `^better-sbd-alias` and `^tui-screenshot` are finished but still `[/]`.
- **The decision record already says this.**
  - It warns: "no automatic forgetting … about 2–3 tasks a day of lane growth … a daily review with release and
    a weekly prune are required … about 80 legacy statuses need one-time triage."
  - None of that has run yet.
  - The [keep rule](#how-to-judge-the-next-14-days) (caps green on 10 of 14 days) therefore fails on day 0 by
    construction.
- **The mechanism nobody planned for is your Pomodoro close** (`docs/capture.md`, the outcome table):
  - A bare `=x` gives every plain link the ledger default: "in progress → started `[/]`, carried."
  - On 09-30 you averaged about 2.3 links per block, so each bare close adds roughly two sticky Pending tasks.
  - Even `~K` ("dropped") keeps the task's lane.
  - Only Alt+N lowers it.

### The morning review is upside down and has no stopping rule

**Finding 3.**

**How the queue works** (`docs/freshness.md` §4):

- Freshness only covers visible, non-recurring **Ready** tasks.
- It never sees the 79 Next and Pending tasks, so the step the chore starts with can't touch the lanes that
  are over cap.

**Forecast.** I ran `bob freshness list` with `BOB_NOW` set to each future date. I added deferrals that come back
from Blocked (that command can't see them until the hooks flip them to Ready).

| Morning | Seeded Ready going STALE | Deferrals returning (RESURFACED) | Due that morning (if you clear it daily) |
| --- | ---: | ---: | ---: |
| Fri 10-02 | 26 (all `gkeep_inbox.md`) | 13 | **39** |
| Sat 10-03 | 26 (all `gkeep_inbox.md`) | 19 | **45** |
| Sun 10-04 | 26 (all `sase.md`) | 20 | **46** |
| Mon 10-05 | 15 | 23 | **38**, plus the first weekly prune |
| Tue 10-06 | 20 | 10 | 30 |
| Wed 10-07 | 38 | 9 | 47 |
| Thu 10-08 | 47 | 8 | 55 |

- That is about **300 decisions in a week**, not counting new captures (September averaged about 14 a day).
- **After that** the pool keeps cycling: 198 Ready tasks at a 7-day interval is about 28 a day, plus deferrals
  coming back.
- **Ten minutes doesn't cover it.** It allows 11–20 seconds per item. That isn't enough to check wording,
  project, priority, and schedule, which is what a freshness confirmation is supposed to mean.
- **Leftovers pile up.** If a morning is skipped, the queue grows: with no review, all 198 are due by 10-08.

Three things are wrong with the chore as written:

1. **Maintenance comes before planning.** When the walk runs long, picking the highlight is what gets squeezed.
   That is the one step that matters most.
2. **"Clear what's due" has no limit.** `freshness.stale_daily_budget` is unset, and `bob freshness list`
   reports `budget: null`. Note that "REVIEW until 0 new" is cheap: NEW is 0 after the seed. The unbounded part
   is DUE.
3. **The wording is ambiguous.**
   - "PENDING → NEXT" reads like a promotion, but the model has none.
   - Read literally, "release the rest" turns NEXT into TODAY every morning. That brings back derived Next by
     hand.
   - Read loosely, nothing ever gets released.
   - The intent is "release what you won't touch **this week**."
   - The order of steps also matters: release before linking, or you release what you just planned.

### You collect but you do not clarify

**Finding 4.**

- **65 open tasks sit in `gkeep_inbox.md`.**
  - None have been closed.
  - They are a third of all in-scope Ready tasks.
  - They're unprocessed Keep notes such as "Roadmap," "Glossary changes:," and "Machine Gods podcast."
- **The seed stamped them fresh** (09-25, 09-26, and 09-29), so they will **never show as NEW**. Instead they
  make up all of Friday's and Saturday's STALE waves.
- **That's the wrong question to ask of them.**
  - Freshness asks "is this still needed as written?" That is the wrong question for an unprocessed note.
  - GTD's clarify step asks: what is it, is it actionable, what's the next action, and where does it belong?
  - Pressing Alt+Shift+F on these items is how the queue becomes a rubber stamp. As the freshness research
    put it: "Refresh is not clarification."
- **The routine never says to empty the inbox.** It says "import from Keep," and import is not the same as
  clarify.

### Building the system is crowding out running it

**Finding 5.**

- **The morning chore changed four times in two days.**
  - 09-29: "Pick today … NOW."
  - 09-30 evening: "≤5 min: PENDING → NEXT → READY."
  - 09-30 late: "≈10 min: REVIEW until 0 new …"
- **`#now` was shipped, bulk-applied, stripped, and retired** within about a day. Two decision records were
  superseded on the day they were accepted.
- **Freshness was researched, built, seeded, and written into the chore in one evening.** No morning has yet
  been run with the lanes it was designed to complement.
- **Your time went to the system** (cld's attribution; I didn't recompute it):
  - About 23% of September's logged time went to the system itself: 14.9 h of GTD sessions plus 18.6 h building
    bob.
  - On 09-30, BOB blocks took 3 h 25 m of 7 h 35 m.
- **Today's ★BOB highlight is more GTD tooling.** Its links are `^auto-decay-priorities` (epic `bob-cli-34`),
  `bob_gtd#^diagnostics`, and `^web-refs`.
- **Those diagnostics would fire constantly.**
  - They alarm when a file has ≥5 Ready tasks, so they would be red on `gkeep_inbox.md` (65) and `sase.md` (59)
    every day.
  - Their R and S thresholds are still undefined.
- **Every trial needs 10–14 stable days, and none has had them.**
  - This applies to the `#now` trial, the lanes trial, and the freshness trial.
  - Each change resets the baseline.
  - Agents make building nearly free. Your attention to run a change and judge it is now the scarce resource.

### The life tasks that matter are the ones the system lets slide

**Finding 6.**

- **The job chain is invisible.**
  - "Reply to job emails!" and "Apply to open OpenAI and Anthropic roles!" carry
    `[dependsOn:: job__update-goog-end-date]` and `scheduled:: 2026-06-30`.
  - They have been blocked by that dependency for three months.
  - Dependency-blocked tasks never appear in READY, NEXT, or the freshness queue.
- **The task they wait on is really a project.**
  - "Update LinkedIn, CV, and GitHub profile …" has 11 Schedule Log entries and has three deliverables.
  - Rescheduling over and over with "🤷 no reason given" is the classic sign of a task with no clear next
    physical action.
- **The five most-rescheduled open tasks** (I recounted them) all live in `cash.md` or `job.md`, with 15, 14, 12,
  11, and 10 Schedule Log entries.
- **The decay ladder points the same way** (`bob-cli-34`, P1 → P2 → P3 → P4 → cancel).
  - Pressing Ctrl+Enter on these tasks sends them into 31–90 and 91–365-day windows.
  - After about 6–8 rolls with no reason given, it cancels them.
  - The cancel is months away. The real near-term harm is avoided life tasks disappearing into P3/P4.
  - Per the plan, **any typed reason or explicit priority pick resets the streak**. That is your lever.
- **Nothing reviews old blockers.**
  - 266 tasks are Blocked, most of them future deferrals.
  - No step looks at old dependency blockers or overdue waiting-for items.
  - "Has Ray Lyles emailed you back yet?!" is a waiting-for item that sits in Ready.

### Two GTD clocks with habits mixed into the review

**Finding 7.**

- **Clock one: the daily wrapper.**
  - The template creates `- [*] #task [[gtd_daily]] ^gtd` in each daily note. It starts out as a sticky Next
    and is counted in TODAY.
  - It has been cancelled 21 days in a row.
- **Clock two: the recurring chores in `gtd_daily.md`.**
  - These are separate `repeat:: every day when done` tasks.
  - They are stuck at `scheduled:: 2026-09-29` (weather, teeth, pills, calendar, email, Keep) and 2026-09-30
    (the morning review).
  - Finishing the wrapper doesn't advance them, and cancelling it hides whether they happened.
- **Habits share the trusted action list.** Teeth, fish oil, and stretches sit in the same task system as next
  actions. They get checked off in batches days later, which adds recurrence noise and no signal.
- **Some steps are open-ended.** "Read Email" has no limit, so it can become an inbox session in the middle of
  the review.

### Pomodoros have become a time log and planning happens at midnight

**Finding 8.**

- **September session lengths:**
  - median 32.5 min, mean 39.6 min;
  - 75 sessions of exactly 25 min;
  - **41 sessions over 50 min**, 10 of 90 min or more, and the longest 195 min;
  - two overlapping entries on 09-30.
- **Breaks and outcomes.** No breaks are recorded, and links are not closed with outcomes. A 95–195-minute
  "Pomodoro" gives you no chance to stop, rest, and re-plan.
- **Today was planned at midnight.**
  - The last block on 09-30 ran 23:40–00:00.
  - Today's ledger was filled to 3/3 themes at 00:07.
  - An idea was captured straight into Today at 00:37.
- **A full plan leaves the morning nothing to pick.** It also leaves no room for anything unexpected.
- **Themes:** themes per day are a smaller problem than the reports suggest.
  - Counting non-GTD names, September averaged **3.1 themes a day** and went over 3 on **11 of 30 days**. cdx's
    3.87 and 17 days counted the exempt GTD entries.
  - The cap is supported, but links per block and leftover placeholders cause more sprawl than the number of
    themes does.

### Day-1 metrics are distorted by the cutover

**Finding 9.**

- **"✓ 390 today" is an artifact.** That count comes from the seed; no human has reviewed anything yet.
- **The seed used apollo's UTC clock (bead `bob-cli-2q`, still open).**
  - The seed ran at 21:45 EDT on 09-30 but used 10-01 as "today."
  - **23 deferrals scheduled for 10-01 were stamped `fresh 10-01`.** Under the rule "fresh == scheduled → not
    resurfaced," they **skip their review today** and won't show up until 10-08.
  - One of them is the high-priority cash task "Find number you need to call to get real-id going!"
- **Config leftovers:**
  - `plan.max_now: 15` is still in `config.yml`;
  - `max_next` and `max_pending` aren't set, so the defaults apply;
  - there is no `freshness:` block at all;
  - `bob_gtd.md` still lists the obsolete requirement "WIP and Next sections should not show `#now` tasks!"

## Ranked recommendations

The ranking reflects how much each change affects whether the practice survives the next two weeks, weighted by
how solid the evidence is and by cost.

### Run a one-time cutover sweep before the first review on Friday

**Rank 1.** Use 2–4 blocks named CUTOVER, not GTD.

- **Pending: from 50 down to ≤10.**
  - Mark done what's done, such as `^better-sbd-alias` and `^tui-screenshot`.
  - Release anything you won't touch this week. Press Esc on the Work Log prompt.
  - Keep only tasks with a live agent or work for this week.
- **Next: from 29 down to ≤15.**
- **The Keep inbox: clarify all 65.**
  - Route each one (Ctrl+Shift+M), cancel it, or rewrite it as a next action.
  - These items *are* Friday's and Saturday's queue.
- **Clean up 09-29:** cancel its 20 open placeholders.
- **Look at today's 23 silently skipped deferrals.** Find them with a `scheduled 2026-10-01` query.
- **Closing the past month:**
  - Close outcome tasks that are truly finished, using their real completion dates.
  - Skip or cancel routine instances that didn't happen.
  - Don't backfill habits.
- **Thin out `sase.md` while you're in it.** Move next actions to the sub-projects that own them. A note with 40
  Pending tasks can't meet a cap of 10.
- **Start the 14-day trial clock** only once both chips are green.
- **Why:** findings [2](#the-lanes-start-the-trial-already-over-their-caps-and-your-close-habit-refills-them),
  [3](#the-morning-review-is-upside-down-and-has-no-stopping-rule), and
  [4](#you-collect-but-you-do-not-clarify). The lane decision itself names this triage as a cost. Monday 10-05
  already carries 38 reviews plus the prune.

### Make GTD the first block before agents as a fixed if-then rule

**Rank 2.**

- **The rule:** "When I sit down in the morning, I start the GTD timer before opening tmux, the SASE TUI, or agent
  notifications."
- **Agent triage** becomes one step inside GTD, capped at 5 minutes: batch-relaunch failures. Anything bigger
  becomes a Task Link in a later block.
- **Why:** [finding 1](#the-routine-died-over-sequencing-and-the-new-process-does-not-address-it).
  Implementation intentions (if-then plans) have a medium-to-large effect on follow-through: d ≈ 0.65 across 94
  studies (Gollwitzer & Sheeran 2006).
- **Cost:** none.

### Rebuild the morning review to plan first and maintain later

**Rank 3.** Give the review a timebox and an exit gate.

- Use [the script below](#the-morning-script) in place of the current one-line chore.
- **Config:** set `freshness.stale_daily_budget: 15`. Set `task_refresh: 14` on `sase.md`, or try a 14-day
  default interval and keep 7 days only for fast-changing notes.
- **The governing equation:** daily review capacity ≥ Ready pool ÷ interval + deferrals returning + new
  captures.
- **Adjust the interval from evidence:**
  - Track the share of REVIEW items that get an outcome other than "still right."
  - If it's under about 10%, lengthen the interval (Taskwarrior's rule).
- **Fix the wording:**
  - "release what you won't touch this week";
  - "pull today's work Pending first";
  - release before linking;
  - clarify NEW, never just refresh it.
- **Why:** [finding 3](#the-morning-review-is-upside-down-and-has-no-stopping-rule).

### Change how you close Pomodoros so they stop refilling Pending

**Rank 4.**

- **One primary 🍅 Task Link per block.**
- **Close with explicit outcomes:**
  - `=x1` keeps one in progress and defers the rest;
  - `=x!1` completes it;
  - `=x0` keeps none in progress;
  - avoid a bare `=x` on multi-link blocks.
- **Length:**
  - 25–35 minutes by default, with a **50-minute hard ceiling** and a real break;
  - if you're still on the same theme, close the block and reopen it;
  - no overlapping times;
  - if you deliberately want a long flow block, give it a different label.
- **Why:** findings [2](#the-lanes-start-the-trial-already-over-their-caps-and-your-close-habit-refills-them) and
  [8](#pomodoros-have-become-a-time-log-and-planning-happens-at-midnight). This is the main way Pending grows by
  itself.

### Freeze GTD and bob process changes for 14 days

**Rank 5.** Start with today's highlight.

- **During the freeze:**
  - no new GTD or bob features;
  - no research swarms about the system;
  - no rewrites of the chores.
- **Capture ideas** in `bob_gtd.md` and decide on **at most one** process change a week, at the prune.
- **Today's work:**
  - Let `bob-cli-34` finish in the background.
  - Hold `^diagnostics` until the caps are green.
  - **Swap today's ★BOB for a non-tooling outcome.**
- **New captures** land as Ready in their project. They go into Today only if they replace something already
  planned there.
- **Why:** [finding 5](#building-the-system-is-crowding-out-running-it). Note that this report is itself the
  eleventh research report about this system in four days.

### Give life admin a protected daily slot and unblock the job chain this week

**Rank 6.**

- **Slot:** make the second block of each weekday a LIFE theme drawn from cash, job, love, or body.
- **Job chain:**
  - Remove `dependsOn` from "Reply to job emails!" and "Apply to … roles!".
  - Rewrite the LinkedIn/CV/GitHub task as a project whose first action takes 5 minutes, such as "set the Google
    end date on LinkedIn."
- **When you defer a life-area task, type a reason.** That resets the decay streak. After three rolls with no
  reason, clarify the task or do it instead.
- **Why:** [finding 6](#the-life-tasks-that-matter-are-the-ones-the-system-lets-slide). Blocked work is invisible
  to every surface you now review.

### Use one GTD clock and take habits out of the review

**Rank 7.**

- **Keep `^gtd` as the only daily GTD clock.**
  - It means "the exit gate holds."
  - Close the GTD block with `=x!1` to complete it, rather than cancelling it the next day.
- **Turn the recurring "Morning review" chore into checklist text** that the wrapper links to.
- **Habits:** take teeth, pills, weather, and stretches out of `#task`, or put them in a separate habit list.
- **Email:** time-box it to "capture or do two-minute replies."
- **Why:** [finding 7](#two-gtd-clocks-with-habits-mixed-into-the-review).

### End the day at a fixed hour and plan tomorrow then

**Rank 8.**

- **The shutdown** happens at a fixed hour, for example 21:00, not 00:07:
  1. Close the last block.
  2. Leave **no open non-GTD placeholders**.
  3. Write tomorrow: GTD, then a ★ highlight phrased as **an outcome with a finish condition and one primary
     link**, then at most 1–2 more themes.
- **Leave slack below the caps.** Plan for your historical capacity of about 6–8 sessions, not for 10 links.
- **Why:** findings [8](#pomodoros-have-become-a-time-log-and-planning-happens-at-midnight) and
  [2](#the-lanes-start-the-trial-already-over-their-caps-and-your-close-habit-refills-them). Open inventory
  labels such as LATER and MISC are Ready lists in disguise.

### Keep the Monday prune small and make sure it happens

**Rank 9.**

- **Size:** at most two Pomodoros. Your own 2024 rule in `gtd.md` was "at most 4."
- **Steps:**
  - bring lanes to their caps;
  - deal with leftover STALE, or lengthen that note's `task_refresh`;
  - **review aging Blocked and waiting-for items**, including old dependency blockers and Blocked tasks whose
    scheduled date has passed;
  - check each life area for a Ready next action;
  - compare created vs closed and hours vs the 🍅 log;
  - make the one allowed process change for the week.
- **Why it matters:** with sticky lanes, the prune is the only *scheduled* way work leaves Next and Pending.
- **Why:** findings [2](#the-lanes-start-the-trial-already-over-their-caps-and-your-close-habit-refills-them) and
  [6](#the-life-tasks-that-matter-are-the-ones-the-system-lets-slide).

### Fix the instruments and start a clean measurement period

**Rank 10.**

- **Distrusted signals:**
  - ignore "✓ today" for 10-01;
  - fix `bob-cli-2q` (apollo's time zone) before trusting any evening `bob` run by an agent.
- **Config:**
  - delete `max_now`;
  - set `max_next` and `max_pending` explicitly;
  - add the `freshness:` block.
- **Leftovers:** delete the obsolete `#now` requirement from `bob_gtd.md`.
- **Measurement:**
  - Declare the day the sweep finishes as day 0.
  - Judge the trial on [the signals below](#how-to-judge-the-next-14-days), not on September.

## The morning script

Take ≤25 minutes, in this order:

1. **Start the GTD timer first**, before tmux or SASE.
2. **Calendar** for today and tomorrow.
3. **Email:** do it if it takes 2 minutes; otherwise capture it. Stop after 5 minutes.
4. **Inbox:**
   - Run `bob gkeep pull`.
   - Clear **NEW to 0 by clarifying**: route it, cancel it, or rewrite it as a next action and then press Alt+F.
5. **Agents:** at most 5 minutes of batch relaunching.
6. **Lanes:**
   - Glance at PENDING, then NEXT.
   - **Release anything you won't touch this week.**
   - Confirm the highlight, today's one LIFE action, and their links.
   - Make sure `bob plan` is clean on themes and links.
7. **Exit gate:**
   - NEW = 0;
   - the highlight is linked;
   - PENDING ≤10 and NEXT ≤15 (or a written exception).
   - When all three hold, close with `=x!1` and start the highlight.

**STALE review** gets one 25-minute block *after* the highlight, or as the last block of the day. Stop when the
budget meter turns green. Leftovers wait for tomorrow, and the weekly prune catches whatever keeps coming
back.

## How to judge the next 14 days

| Signal | Source | Keep rule |
| --- | --- | --- |
| GTD is the first closed block and closes within 30 min | the ledger | ≥10 of 14 days |
| `^gtd` completed, not cancelled | the daily note | ≥10 of 14 days |
| PENDING ≤10 and NEXT ≤15 | `bob plan` | ≥10 of 14 days |
| NEW = 0 when GTD ends; STALE leftovers handled weekly | `bob freshness list` | ≥12 of 14 days |
| Share of REVIEW items with an outcome other than "still right" | your count | under ~10% → lengthen the interval |
| A life-area action done or clarified | cash/job/love/body logs | ≥5 of 7 days |
| Open non-GTD placeholders at midnight | the ledger | 0 |

Interpreting the result:

- **If the routine is still being cancelled,** change the ritual (shorter, on a smaller list), not the lanes.
- **If the routine runs and the lanes still grow past their caps,** then reopen the design. That is when age-based
  Next decay would be on the table.

## Where the reports disagreed and how I resolved it

| Question | Reports said | Resolution (verified) |
| --- | --- | --- |
| Lane and link counts | cdx, cld, grk: NEXT 28, 4 links. gem: NEXT 29, 5 links. | Both are right, at different times. The 00:37 `^web-refs` capture went straight into Next and Today. Live is **29 / 5 links / TODAY 6**. |
| Freshness load | gem: all 390 stamps expire as a "cliff" on 10-08. cld: STALE 26/26/23/13/13/19/19. cdx: 26/26/26/15/20/38/47. | **cdx is right.** Only in-scope Ready tasks (198) can be due, and the seed staggered them. Non-Ready stamps only matter when a task returns to Ready. cld undercounted 10-04 to 10-08. gem's instinct is right in one sense: skip the review and all 198 are due by 10-08. |
| Is "REVIEW until 0 new" unbounded? (mus) | mus: yes. | No. NEW is 0 after the seed. The unbounded part is "then clear what's due." |
| Theme spread | cdx: 3.87 a day, over 3 on 17 days. | 3.07 non-GTD themes a day, over 3 on 11 days. The cap is supported, but modestly. |
| Session length | grk: 25–35 min. cdx, cld: cap at 50. | Both: **25–35 by default, 50 as a hard ceiling**, and take the break. |
| Keep-inbox `task_refresh` | gem: 2–3 days (force it). grk: 90 (hide it). | Neither. Clarify the inbox; an interval can't replace clarifying. If the sweep slips, treat Friday's and Saturday's STALE items as **clarify** work, not Alt+Shift+F. |
| Planning the night before | cld: the right instinct. grk: a night-time bet that blocks the morning pick. mus: link late. | Plan at a **fixed shutdown hour**, not at midnight. Plan the highlight plus at most 2 themes, with one primary link each, and leave slack. Pre-linking isn't the harm. Never releasing is. |
| Pending target | gem: ≤5 now. cdx: test 5 after cleanup. Others: the cap of 10. | Get to 10/15 first. Test a Pending cap of 5 only after two clean weeks. |
| The `^gtd` wrapper | gem: remove it and link the recurring chore. grk, cdx: split habits from the review. | Keep **one clock**. Keep `^gtd`: it is already templated and has the R9 carve-out. Make it mean "the exit gate holds," and move habits out. See [recommendation 7](#use-one-gtd-clock-and-take-habits-out-of-the-review). |
| What comes first | Four reports: triage. cld: GTD before agents. | Both, in that order. Triage is urgent. Protecting the first block stops the next lapse. |

## Scope and limitations

- **Lead synthesis** of five independent reports (`__cdx`, `__cld`, `__grk`, `__mus`, `__gem` in this
  directory), plus my own verification against the live vault and tools.
- **Snapshot:** 2026-10-01, about 00:30–01:00 EDT. This is before the first morning that runs the new
  process.
- **Question:** You changed your morning GTD and Pomodoro practice on 2026-09-30. What are you getting wrong,
  and what should you change next?
- **Bias you flagged (old data):** you skipped morning GTD for about a month and still have finished tasks to
  close. The month-long gap inflates the lane and Ready counts. So I rely on counts only where that inflation
  can't flip the conclusion:
  - lane sizes are upper bounds;
  - Pomodoro timings and ledger order are reliable;
  - the freshness forecast reads the future dates already in the vault.

  The sequencing, churn, and forecast findings don't depend on that inflation.
- **The forecast is approximate:**
  - The STALE numbers come from `bob freshness list` run under `BOB_NOW`.
  - The deferral counts come from a line-level scan: open, non-recurring, scheduled tasks, excluding `#hide`.
  - Neither counts new captures. Treat the totals as ±10%.
- **Unverified figures.** Time attribution (the 23% figure) and the per-area reschedule means are cld's numbers;
  I didn't recompute them.
- **No live Obsidian session.** Keystroke cost per review item is assumed, not measured.

## Sources

- **Researcher reports** (this directory): [cdx](gtd_morning_review_pomodoro_cutover__cdx.md),
  [cld](gtd_morning_review_pomodoro_cutover__cld.md), [grk](gtd_morning_review_pomodoro_cutover__grk.md),
  [mus](gtd_morning_review_pomodoro_cutover__mus.md), [gem](gtd_morning_review_pomodoro_cutover__gem.md).
- **Vault:**
  - `~/bob/2026/202608*.md`, `202609*.md`, `20261001.md`;
  - `gtd_daily.md`, `gkeep_inbox.md`, `sase.md`, `job.md`, `cash.md`, `bob.md`, `bob_gtd.md`,
    `_templates/daily.md`;
  - vault commits `61b0921e` (seed), `83254268`, `0701c271`, `86c8621d`, `475022a6`.
- **Tools (2026-10-01):**
  - `bob plan`;
  - `bob freshness list -f json` with `BOB_NOW` set to dates from 10-02 to 10-22;
  - `sase --help`;
  - `sase bead read bob-cli-2q`.
- **bob-cli docs:** `docs/freshness.md` §4–6, `docs/capture.md` (the `=x` outcome table), `docs/plan.md`.
- **Plans and decisions:**
  - `plan:202609/priority_roll_decay.md` (the ladder and the streak rules);
  - `decisions:task-lanes-are-sticky`;
  - `decisions:today-is-read-from-the-ledger`.
- **External** (cited by the researchers):
  - [GTD podcast #7: the weekly review](https://gettingthingsdone.com/2015/07/podcast-07-guided-gtd-weekly-review/)
  - [GTD & Procrastination](https://gettingthingsdone.com/2018/01/gtd-procrastination/)
  - [Taskwarrior review](https://taskwarrior.org/docs/review/)
  - [Gollwitzer & Sheeran 2006](https://www.socmot.uni-konstanz.de/publications/implementation-intentions-and-goal-achievement-meta-analysis-effects-and-processes)
  - [Pomodoro Technique](https://en.wikipedia.org/wiki/Pomodoro_Technique)
