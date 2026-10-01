# Morning GTD and Pomodoro practice: review of the 2026-09-30 changes

- **Researcher:** cld (one of five independent researchers)
- **Written:** 2026-10-01, about 00:30–02:00 EDT, before the first morning that uses the new process
- **Question:** You made several big changes to your morning GTD and Pomodoro practice on 2026-09-30. What are
  you getting wrong, and what should you improve next?
- **Inputs:**
  - the vault (`~/bob`): daily notes July–October, `gtd_daily.md`, `dash.md`, `freshness.md`, `bob_gtd.md`, the
    area notes, `done/gtd_daily_done.md`, and vault git history;
  - live read-only tool output: `bob plan`, `bob freshness list`, `bob query`;
  - bob-cli docs (`plan.md`, `freshness.md`, `capture.md`, `randomize.md`) and git history;
  - bead `bob-cli-34`, with its plan `plan:202609/priority_roll_decay.md`;
  - two earlier research reports:
    - `research:202609/retire_now_sticky_lanes_ledger_today/retire_now_sticky_lanes_ledger_today.md`
    - `research:202609/ready_task_freshness_review/ready_task_freshness_review.md`
  - a few external sources, listed at the end.
- **Caveat you raised:** you haven't done the morning GTD for about a month, so task counts are inflated by
  finished work you haven't closed. I rely on that data mainly for *when and how* the routine runs or fails. I
  rely on counts only where inflation can't change the conclusion, and I say so when it might.

## Bottom line

1. **The redesign fixes the tool, but the tool isn't what broke.**
   - Your morning GTD did not stop because the dash was confusing or the lanes decayed. It stopped when **the
     first block of the day became agent operations**: relaunching failed agents, cleanup, restarts.
   - **Before (08-28 → 09-10):** GTD was the first Pomodoro on 11 of 14 days, and the daily chores were checked
     off almost every day.
   - **After (09-11 → 09-30):** GTD came first on 2 of 20 days and didn't happen at all on 7. On 11 of those
     20 days, the day opened with an ops block.
   - **On 09-30 itself:** you started the GTD Pomodoro at 06:20 and filled it with `re-launch-failed` and
     `clean-prompt-history`. It became a 95-minute CLEANUP block, and `^gtd` was cancelled at midnight.
   - Nothing in the new process changes that order.
2. **You are changing the process faster than you can run it.**
   - The morning-review chore had three versions in about 30 hours.
   - `#now` was shipped, bulk-applied, stripped and retired within about a day. Its decision record was
     superseded on the day it was accepted, and its two-week trial ended on day one.
   - Freshness was researched, built, seeded and written into the morning chore in one evening.
   - Ten research reports about the bob/GTD system were written in four days (09-28 → 10-01, this one included).
   - In September, about **23% of your logged Pomodoro time went to the system itself**: 14.9 h in GTD sessions
     plus 18.6 h building bob. Job, cash, love and body together got **0.3%**.
3. **The new lanes start the trial already failing.**
   - PENDING is **50/10** and NEXT **28/15**.
   - These are the **73 carried links from the 20 placeholder Pomodoros on 09-29**, under a new name.
   - The research behind sticky lanes made a one-time cutover triage a precondition. It hasn't happened yet.
4. **The "≈10 min" morning review won't take 10 minutes next week.**
   - From the vault as it stands, I forecast **39, 45, 43 and 36 tasks due for review** Friday through Monday.
     Two waves overlap: the freshness seed going stale, and the 222 tasks that `bob randomize` re-rolled on 09-28
     coming back.
   - On top of that: the 78-item lane triage, and your first weekly prune on Monday.
   - Overloading the morning is the pattern that has already killed this routine once.
5. **The system is excellent at moving SASE ideas around and bad at the few life tasks that matter.**
   - Your most-rescheduled tasks are in `cash.md` and `job.md`. They average 5.6 and 11.5 Schedule Log entries
     each; `sase*` tasks average 3.3.
   - Your job-search actions have been blocked by a dependency since June. They wait on "Update LinkedIn, CV, and
     GitHub profile", which has been re-scheduled 11 times.
   - Tomorrow's highlight, bob-cli-34 (priority roll decay), turns the one-key Ctrl+Enter path into
     P1 → P2 → P3 → P4 → **cancel**, with no exemption for these tasks.
6. **What to do, in short:**
   - GTD comes before agents.
   - Freeze the process for the trial.
   - Triage the lanes once.
   - Cut the daily ritual to a fixed minimum, and put a daily budget on STALE.
   - Give life admin a protected daily slot.

   The [ranked list](#7-ranked-recommendations) is at the end.

## 1. What changed on 2026-09-30

| Change | Where it shows up |
|---|---|
| `#now` retired. Next `[*]` and Pending `[/]` are now **sticky** lanes; only Alt+N releases them. | bob-cli epic `bob-cli-2y`; decision records `task-lanes-are-sticky` and `today-is-read-from-the-ledger` |
| **Today** is read from the ledger: dedicated Task Links under today's open Pomodoros | `docs/plan.md`; `bob plan`; `bob-ledger-tools` api `isToday` |
| `dash.md` rebuilt into exclusive TODAY / PENDING / NEXT / READY sections. Chips added: PENDING n/10, NEXT n/15, REVIEW, PLAN. | `dash.md` (vault commits `a0d6635c`, `5997e77f`) |
| **Task freshness** added: `[fresh::]` stamps, the REVIEW queue (`freshness.md`), `]s`/`[s`, Alt+F/Alt+Shift+F, a status bar. The cutover seed was stamped on the live vault around 21:45 EDT. | epic `bob-cli-31`; vault `61b0921e`, `2fa64905`, `0701c271` |
| `gtd_daily.md`: "Pick today … NOW" and "Weekly review: re-tag NOW" (created 09-29) were cancelled. "Morning review (≤5 min)" was created, then rewritten as **"Morning review (≈10 min): REVIEW until 0 new …, then clear what's due; PENDING → NEXT; link today's work, release the rest with Alt+N; ≤3 themes, highlight first"**. "Weekly prune" gained freshness and "projects with no Next" steps. | vault `83254268`, `0701c271` |
| `=x` closes and Alt+N releases write Work Log entries | bob-cli `0ce41b9`, `15c6341`, `473cca3` |
| New project `bob_gtd.md`, "Improve GTD morning review process!": the keymaps task is done; the diagnostics task is next | `bob_gtd.md` |
| Tomorrow's ledger was written at 00:07: **GTD first, then 3 themes and 4 links** (BOB★, READ, MEMORY) | `2026/20261001.md`; `bob plan` reports `3/3 themes · 4/10 links` |
| Epic `bob-cli-34` (priority roll decay) launched at 23:56. It is tomorrow's highlight (★ BOB). | `sase bead read bob-cli-34` |

## 2. What the data shows

### 2.1 The morning review died when mornings became agent operations

**Chore completions** (`done/gtd_daily_done.md`):

- From 07-15 to 09-09, you completed about 9 daily chores almost every day.
- After 09-09, chores were completed on only 6 of 21 days: 09-13 (4), 09-14 (1), 09-16 (1), 09-20 (6), 09-25 (6)
  and 09-28 (7).
- The `^gtd` task in each daily note was completed on 12 of the 14 days from 08-27 to 09-09. From 09-10 to 09-30
  it was cancelled every day (21 of 21).

**First Pomodoro of each day** (parsed from the daily ledgers):

| Period | Days | GTD was the first block | GTD missing | First block was ops (SHIT, RELAUNCH, RESTARTS, CLEANUP, ATHENA, SASE AGENTS) |
|---|---:|---:|---:|---:|
| 08-28 → 09-10 | 14 | **11** | 0 | 2 (RELAUNCH, with GTD second) |
| 09-11 → 09-30 | 20 | **2** | **7** | **11** |

**Late GTD.** When GTD did run in the second period, it usually ran in the afternoon:

| Day | GTD start | Its place in the day |
|---|---|---|
| 09-29 | 13:50 | 6th block |
| 09-20 | 14:40 | 5th block |
| 09-25 | 15:25 | 5th block |
| 09-28 | 17:25 | 9th block |

By then it was a catch-up, not a morning review.

**No finish line.** A GTD session that didn't end turned into ordinary work:

- **09-10:** 220 minutes of "GTD" blocks: "Thought of a bunch of BOB ideas and 'started' 🍅 `sase#^tool`", then an
  epic launched.
- **09-13:** six GTD blocks (240 minutes) full of SASE fixes.
- **09-22:** three "GTD" blocks with no `^gtd` link at all (`clean-core`, `dot-separators`).

GTD stopped meaning "review" and started meaning "whatever I do first". That made it expensive, so it got skipped.

**Yesterday (09-30)**, in vault commits:

- At 06:33, the template's GTD placeholder became `0620-0710 — GTD` holding `[[sase#^re-launch-failed]]` and
  `[[sase#^clean-prompt-history]]`. It ended as a 95-minute CLEANUP block.
- The second GTD placeholder stayed open all day. It was deleted at 00:05, and `^gtd` was cancelled.
- **BOB-themed blocks spent building the GTD system took 3 h 25 m: 45% of the day's 7 h 35 m.**

The new design is still a chore that competes with relaunching agents. It's just a longer one.

### 2.2 Process churn is faster than evaluation

**In about 36 hours (09-29 → 09-30):**

- **The morning-review chore had three versions:**
  - 09-29: "Pick today: ≤3 themes from yesterday + NOW";
  - 09-30, evening: "≤5 min: PENDING → NEXT → READY";
  - 09-30, late: "≈10 min: REVIEW until 0 new … PENDING → NEXT …".
- **`#now` lived and died:**
  - the capture token shipped around midnight on 09-29/30;
  - 73 tasks were bulk-tagged and then stripped;
  - it was retired the same evening.
- **Two decision records were superseded the day they were accepted.** `now-tag-is-user-owned` and
  `task-status-is-derived` (in part) were accepted on 09-30, when the decisions web launched, and superseded later
  that day.
- **A declared two-week `#now` trial (09-30 → 10-13) ended on day 1.**
- **Freshness was researched, built, seeded and written into the morning chore in one evening.** That was before
  a single morning had been run with the sticky lanes it was designed to complement.

**Overall output:**

- bob-cli landed **97 commits from 09-28 to 09-30** (138 in September).
- There were **ten research reports about the bob/GTD system in four days**:
  - gkeep drain, randomize, `#now` automation, `#now` vs In Progress, decisions web, `bob-cli-2o` explained;
  - retire-`#now`, the freshness epic, the freshness review, and this report.

**Why it matters:**

- Every trial rule you've written needs 10–14 days of stable data:
  - the `#now` trial;
  - the lanes trial ("NEXT ≤15, PENDING ≤10 on 10 of 14 days");
  - the freshness trial.
- None of them has had one, because each change resets the baseline.
- Agents now make building almost free, so the scarce resource is **your attention to run and judge a change**,
  not implementation.
- Building is also the comfortable part of GTD. In David Allen's terms, "get creative" about the system has
  crowded out "get current" with it. He calls the weekly review the critical success factor because an unreviewed
  list stops being trustworthy ([GTD podcast #7](https://gettingthingsdone.com/2015/07/podcast-07-guided-gtd-weekly-review/)).

### 2.3 Where September's Pomodoro time went

| Bucket (minutes split evenly across the distinct note families linked in a block) | Hours | Share |
|---|---:|---:|
| SASE (`sase*.md`) | 100.4 | 68.4% |
| bob tooling (`bob.md`, `bob_gtd.md`) | 18.6 | 12.7% |
| GTD sessions (`[[#^gtd]]`) | 14.9 | 10.1% |
| No Task Link | 12.4 | 8.5% |
| job | 0.3 | 0.2% |
| body | 0.1 | 0.1% |
| cash, love | 0 | 0% |
| **Total logged** | **146.7** | |

**Block sizes.** 222 closed blocks:

- median 35 minutes;
- 34% exactly 25 minutes;
- 37% were 45 minutes or longer.

On 09-30 one "Pomodoro" ran 95 minutes, and two overlapped (0620–0755 and 0750–0815).

### 2.4 The new lanes are the old carry pile, renamed

**`bob plan` now:**

```
PLAN  3/3 themes - 4/10 links      TODAY 5 - PENDING 50/10 - NEXT 28/15
warning NEXT has 28/15 tasks; release some with Alt+N  next_cap_exceeded
warning PENDING has 50/10 tasks; release some with Alt+N  pending_cap_exceeded
```

**Where they came from:**

- 48 of the 50 Pending tasks and 25 of the 28 Next tasks were last linked on **09-29**. That day's note held
  **20 open placeholder Pomodoros with 73 link lines**: BOB, GOALS, SASE ×2, DECKS, READ, MISC, FINAL, RENAME,
  CLEANUP, REMOTE, SERVICE, NEW FEATURES, SUDO, FAST TESTS, QUEUE, SCHEDULE, AUDIT MEMORY, GATES, LATER.
- 40 of the 50 Pending tasks live in `sase.md`.
- The research you adopted said: "About 80 current `[/]` and `[*]` tasks came from the old derivation rules.
  Freezing them turns an accident of implementation into a permanent queue. Triage them once, at cutover."

**Why it matters:**

- Its trial keeps the design only if NEXT ≤15 and PENDING ≤10 on 10 of 14 days. As things stand, that fails on
  day 0 by construction.
- The new chore's "PENDING → NEXT" step is a 78-item walk.

**Your Pomodoro habit keeps refilling Pending.**

- A plain `=x` close applies the ledger default, "in progress", to every link. Each linked task becomes `[/]`,
  gets a 🍅, and is carried forward (`docs/capture.md` outcome table).
- On 09-30 you averaged **2.3 links per block**, so each plain close adds about two sticky Pending tasks.
- The old hooks let those decay. Now only Alt+N removes them, with a Work Log prompt each time.

The good news: the MacBook's `bob` was rebuilt at 23:37. The first hooks pass against `20261001.md` reported
"0 cleared, 0 cleared in progress", so the overnight demotion the research warned about did not happen. The lanes
are intact; they just need triage.

### 2.5 The real load of the new morning review

`bob freshness list` reports 0 due today: by design, nothing is due on cutover day.

**Forecast.** From tomorrow, I computed the load from the vault's `[fresh::]` stamps and its future `scheduled`
dates (non-recurring, open, not `#hide`):

| Day | Deferrals returning (RESURFACED) | Seeded Ready going STALE | Due that morning |
|---|---:|---:|---:|
| Fri 10-02 | 13 | 26 | **39** |
| Sat 10-03 | 19 | 26 | **45** |
| Sun 10-04 | 20 | 23 | **43** |
| Mon 10-05 | 23 | 13 | **36**, plus the first weekly prune |
| Tue 10-06 | 10 | 13 | 23 |
| Wed 10-07 | 9 | 19 | 28 |
| Thu 10-08 | 8 | 19 | 27 |

**Not counted in the table:**

- NEW captures (September averaged 13.7 created tasks a day, per the freshness report's V2);
- the lanes;
- **re-staling.** With 198 Ready tasks at 7 days, about 28 a day keep coming due for as long as the pool stays
  that size.

**Where the bulge comes from.** The return wave is self-inflicted: on 09-28, `bob randomize` re-rolled 222 tasks
into 2–7 and 8–30 day windows, and they are landing now.

**Three things are wrong with "≈10 min" as written:**

1. **The order is upside down.**
   - The chore puts the freshness walk *before* choosing the day.
   - When the walk runs long, the step that gets squeezed is the valuable one: picking the highlight.
   - Maintenance should follow planning, not precede it.
2. **The default outcome is the cheapest one.**
   - With 40 items, Alt+Shift+F ("still right") becomes a rubber stamp.
   - The freshness research warned: "Refresh is not clarification."
   - Taskwarrior's review docs say the same: if you make no changes, review less often
     ([Taskwarrior review](https://taskwarrior.org/docs/review/)).
3. **"Release the rest with Alt+N" is ambiguous.**
   - Read literally ("everything not linked today"), it reduces NEXT to TODAY every morning. That brings back
     derived Next by hand.
   - Read loosely, nothing is ever released.
   - The intended rule is "release what you won't touch *this week*".

### 2.6 Measurement artifacts from the cutover (don't trust day 1)

- **The seed used apollo's clock.** The seed ran on apollo, whose system time zone is **Etc/UTC**, at 01:45 UTC
  on 10-01 (21:45 EDT on 09-30). It used **2026-10-01 as "today"**:
  - every non-Ready open task got `[fresh:: 2026-10-01]`;
  - Ready buckets run 09-25 → 10-01;
  - tasks you created on 09-30 (`bob_gtd.md` `^keymaps`, `^diagnostics`) were stamped 09-29, before they
    existed.
- **The ✓ counter is meaningless on 10-01.** `bob freshness list` now says **"✓ 390 today"** although no human
  has reviewed anything. It becomes meaningful from 10-02.
- **This is a known bug.** The root cause is tracked in bead **`bob-cli-2q`**: "bob picks tomorrow's daily note
  after 8pm EDT on apollo". I added a `+1` with this evidence. The same off-by-one hits any `bob capture`,
  `bob plan` or hooks run by an agent on apollo between 20:00 and midnight EDT.
- **The seed hid the inbox.** It also marked the 64 Keep notes pulled on 09-28 as fresh, so they will never show
  as NEW, even though nobody has clarified them.
- **Config cruft:**
  - `~/.config/bob/config.yml` still says `max_now: 15`. `max_next` and `max_pending` aren't set, so they fall back
    to the defaults (15 and 10).
  - The Requirements line in `bob_gtd.md` ("WIP and Next sections should not show `#now` tasks!") is now
    obsolete.

### 2.7 The inbox is counted as Ready work

**65 of the 198 Ready tasks (33%) sit in `gkeep_inbox.md`.**

- They are a month of Keep notes, pulled on 09-28 and never clarified. Examples: "Roadmap", "108:14 hard fork",
  "Glossary changes:", "Machine Gods podcast", "Pirate T25", "Buy more headphone chargers!".
- GTD's **clarify** step is missing from the new morning review. Clarify asks: what is it? Is it actionable? What
  is the next action? Where does it belong?
- Freshness asks a different question: "is this still needed as written?" That's the wrong question for an
  unprocessed note.
- The cost:
  - these items dilute READY as a pull list;
  - they add about 9 tasks a day to the freshness walk;
  - the seed made them look reviewed.

### 2.8 The life tasks that matter are the ones the system lets slide

| Area | Open tasks (non-recurring) | With a Schedule Log | ≥5 reschedules | Mean reschedules (logged tasks) |
|---|---:|---:|---:|---:|
| `sase*` | 409 | 223 | 50 | 3.3 |
| cash | 25 | 17 | 8 | **5.6** |
| job | 5 | 2 | 2 | **11.5** |
| love | 12 | 12 | 3 | 3.0 |
| body | 4 | 3 | 1 | 3.0 |

**The most-rescheduled tasks in the vault:**

| Task | Schedule Log entries | What happened |
|---|---:|---|
| "Apply to jobs that Bharath Kumar recommended you for!" | 15 | Marked "Do this today!" on 08-24, then re-scheduled 11 days running with "🤷 no reason given", then P-level rolls to 10-05 |
| "Call about unemployment to verify real ID!" | 14 | |
| "EMAIL: Jack Routledge back!" | 12 | |
| "Update LinkedIn, CV, and GitHub profile to reflect that I'm not at Google anymore!" | 11 | |
| "Did enrolling for unemployment work!" | 10 | |

**The job-search chain:**

- "Reply to job emails!" and "Apply to open OpenAI and Anthropic roles!" carry
  `[dependsOn:: job__update-goog-end-date]` and `scheduled 2026-06-30`. They have been **Blocked for three
  months** behind the LinkedIn/CV/GitHub task.
- Blocked tasks are invisible by design: they never appear in READY, NEXT or the freshness review.
- Right now most life-area tasks are Blocked (deferred): cash 20 of 26 open, love 10 of 12, body 4 of 4, job 4 of 5.

**Why this is a GTD failure, not a time failure:**

- Repeated rescheduling with no reason is the classic sign of a task with **no clear next physical action**.
- "Update LinkedIn, CV, and GitHub profile" is a three-deliverable project, not an action.
- Allen's own remedy for procrastination is to clarify the outcome and define the next action
  ([GTD & Procrastination](https://gettingthingsdone.com/2018/01/gtd-procrastination/)).

**What bob-cli-34 would do to these tasks:**

- Its Ctrl+Enter recommended roll follows **P1 → P2 → P3 → P4 → cancel**, with `rolls: 1` by default and no
  exemption by area or priority (`plan:202609/priority_roll_decay.md`, "The ladder").
- For stale SASE ideas, that's exactly right.
- For these tasks, the one-key path ends by cancelling the ones you're avoiding, logged as
  "🍂 decayed past P4".

I only know what the vault says about your situation. But by its own record, the job search has been waiting on
one vague task since June, while over 99% of linked Pomodoro time went to SASE and the system around it.

### 2.9 What's working (keep it)

- **Tomorrow's ledger is the best plan in weeks.**
  - It has GTD first, 3 themes and 4 links. Two days earlier, the note had 20 placeholders and 73 links.
  - Writing it the night before (00:07) is the right instinct.
- **The model is sound.**
  - Today is derived from the ledger.
  - Each task sits in exactly one lane.
  - Release is a first-class gesture, and Pending has a Work Log "why".
  - The sticky-lanes research was right about these.
- **Freshness's uncapped NEW tier** is a real safety net for captures that skip the inbox.
- **The GTD placeholder is pre-seeded first** in the daily template, which makes "GTD first" the default.

## 3. Diagnosis: what you're getting wrong

1. **You're treating a sequencing problem as a tooling problem.** The review fails when agents get the first
   block. No dash, lane or stamp changes who gets the first block.
2. **You're changing the system faster than you can run it.** Building process is your comfortable mode. It
   produces visible progress, while the boring step, actually reviewing, slips.
3. **You started the trials in a failed state.** The cutover triage the lanes depend on was skipped, so the caps,
   chips and keep rules measure the old carry pile, not the new design.
4. **You made the daily ritual heavier just when it needs to be lightest.** You also put maintenance (STALE)
   before planning (the highlight).
5. **There is no clarify step.** Inbox notes count as Ready. Vague tasks are rolled instead of being given a next
   action, and the deferral tools (`randomize`, P-level rolls, and soon decay-to-cancel) automate the avoidance.
6. **Non-SASE areas have no protected time.** The dash, the lanes and freshness all exclude Blocked work, which is
   where your life admin lives.
7. **Pomodoro habits are feeding the lanes and wearing you down:**
   - several 🍅 links per block, closed with a plain `=x`;
   - 45–95-minute "Pomodoros" with no recorded breaks, and overlapping times;
   - a block from 23:40 to 00:00, then planning at 00:07, before a review meant to start around 06:00.
8. **You're at risk of reading day-1 metrics** that the cutover distorted (✓ 390, PENDING 50).

## 4. A concrete morning script (≤25 minutes, in this order)

**The night before (you already do this):** write tomorrow's ledger: GTD, then the highlight, then at most two
themes; at most 10 links. Make the highlight an outcome with a finish condition, not a project name.

1. **Start the GTD Pomodoro before opening tmux, the SASE TUI or agent notifications.** Hard 25-minute timer.
2. **Calendar** for today and tomorrow. **Email:** act if it takes two minutes, otherwise capture.
3. **`bob gkeep pull`, then clear NEW to 0 by clarifying:** route (Ctrl+Shift+M), cancel, or rewrite as a next
   action (then Alt+F). Never refresh an unclarified note.
4. **Agents, at most 5 minutes:** batch-relaunch failures. Anything bigger becomes a Task Link in a later block,
   not now.
5. **Confirm the highlight and today's one life-admin action, and link both.** Release any Next or Pending task
   you notice you won't touch this week. Don't walk the whole lane.
6. **Close GTD with `=x`, then start the highlight.**

**STALE review:** one 25-minute REVIEW block *after* the highlight (or as the day's last block). Stop when the
`freshness.stale_daily_budget` meter goes green; it's a goal meter, not a filter. Whatever is left waits until
tomorrow.

## 5. How to judge the trial (no new tooling needed)

Track these over a 14-day window that starts the day both caps are green:

| Signal | Source | Keep rule |
|---|---|---|
| GTD is the first closed block of the day and closes within 30 minutes | the ledger | ≥10 of 14 days |
| PENDING ≤10 and NEXT ≤15 | `bob plan` | ≥10 of 14 days |
| NEW = 0 by the end of GTD | `bob freshness list` | ≥12 of 14 days |
| Share of REVIEW items that got a non-refresh outcome | your count, or the Notices | Below ~10% → lengthen intervals (Taskwarrior's rule) |
| A life-area action done or clarified | `cash`/`job`/`love`/`body` Schedule and Work Logs | ≥5 of 7 days |

## 6. Ranked recommendations

Ranked by expected impact on whether the routine survives the next two weeks, weighted by confidence in the
evidence and by cost.

1. **Make GTD the first block, before agents, as a fixed if-then rule.**
   - **The rule:** "When I sit down in the morning, I start the GTD timer before opening tmux or SASE."
   - Agent triage becomes a capped step *inside* GTD (step 4 above).
   - **Evidence:** GTD-first fell from 11 of 14 days to 2 of 20 when ops took the first block (§2.1), and on
     09-30 the GTD slot itself was taken over.
   - Implementation intentions (if-then plans) have a medium-to-large effect on follow-through: d ≈ 0.65 across
     94 studies ([Gollwitzer & Sheeran 2006](https://www.socmot.uni-konstanz.de/publications/implementation-intentions-and-goal-achievement-meta-analysis-effects-and-processes)).
   - **Cost:** none.
2. **Freeze the process for 14 days.**
   - No new GTD or bob features, no research swarms about the system, and no rewrites of the chores.
   - Capture ideas in `bob_gtd.md` and decide on them at the weekly prune, at most **one** process change a week.
   - Let `bob-cli-34` finish in the background, but **swap tomorrow's highlight** (★ BOB, i.e. more GTD tooling)
     for a non-tooling outcome.
   - **Evidence:** §2.2 and §2.3. About 23% of September went to the system, and none of its trials has produced
     data.
3. **Do the one-time lane triage before the trial clock starts.** Do it tomorrow, in one or two blocks named
   CUTOVER.
   - Cut PENDING from 50 to ≤10: keep only tasks with a live agent or work you'll touch this week, and press Esc on
     the Work Log prompt for the rest.
   - Cut NEXT from 28 to ≤15.
   - Start counting the trial only once both chips are green.
   - **Evidence:** §2.4. The lanes are the 09-29 carry pile, and the adopted research made this triage a
     precondition.
4. **Shrink the daily ritual, reorder it, and budget STALE.** Plan first, maintain second (§4).
   - **Config changes:**
     - set `freshness.stale_daily_budget: 15` in `config.yml`;
     - set `task_refresh: 14` in `sase.md`'s frontmatter. That halves its share of the load, and the freshness
       research already modelled this option.
   - **Chore rewrite:** replace the `gtd_daily.md` morning chore with the §4 order, and replace "release the rest"
     with "release what you won't touch this week".
   - **Evidence:** §2.5 forecasts 36–45 tasks due Friday through Monday, plus the lanes. The routine collapsed
     before when GTD sessions sprawled (§2.1).
5. **Give life admin a protected daily slot, and unstick the job chain this week.**
   - Make the second block of each weekday (or a fixed time) a LIFE theme drawn from cash, job, love and body.
   - Remove the `dependsOn` from "Reply to job emails!" and "Apply to open OpenAI and Anthropic roles!".
   - Rewrite "Update LinkedIn, CV, and GitHub profile" as a project whose first action takes five minutes, such as
     "Set the Google end date on LinkedIn".
   - Until `bob-cli-34` has an area or priority exemption, **never press Ctrl+Enter on cash/job/love/body tasks.**
     After three rolls with no reason, clarify the task or do it instead. File the exemption as a feature *after*
     the freeze.
   - **Evidence:** §2.8.
6. **Clarify the Keep inbox once (about two blocks), then keep it at zero daily.**
   - Route SASE ideas to `sase.md` (or cancel them), route personal items to their areas, and turn vague notes into
     next actions or delete them.
   - After that, inbox processing is the NEW step of GTD; an inbox item never sits in READY overnight.
   - **Evidence:** §2.7.
7. **Fix the Pomodoro habits that inflate the lanes:**
   - one primary 🍅 Task Link per block (Cirillo: one task per Pomodoro, and a Pomodoro is indivisible —
     [summary](https://en.wikipedia.org/wiki/Pomodoro_Technique));
   - close with explicit outcomes (`=x!N` complete, `~K` drop) instead of a plain `=x`;
   - cap blocks at 50 minutes and take the break;
   - no overlapping times.
   - **Evidence:** §2.3, §2.4.
8. **Formalize an evening shutdown at a fixed hour** (for example 21:00, not 00:07).
   - Close the last block, write tomorrow's ledger, run a quick lane check, and say "shutdown complete".
   - This protects tomorrow's first block. It's Newport's shutdown ritual, and you already do half of it
     ([summary](https://habitbox.app/blog/shutdown-ritual)).
   - **Evidence:** on 09-30 the last block ended at 00:00 and planning happened at 00:07.
9. **Keep the Monday weekly prune small, and make it happen.**
   - Cap it at two Pomodoros; your own 2024 rule was "weekly review should take at MOST 4 pomodoros" (`gtd.md`).
   - With lanes that never decay, the prune is now the only *scheduled* way work leaves NEXT and PENDING. If you
     skip it, the design fails.
   - Do the cutover triage *before* Monday 10-05, because Monday already carries 36 reviews.
   - Add "Is any life area without a Ready next action?" to its checklist. Freshness can't see missing actions.
10. **Clean up the instruments:**
    - ignore the "✓ today" count on 10-01;
    - get `bob-cli-2q` fixed (set apollo's time zone or give bob a vault time zone) before trusting agent-run `bob`
      commands in the evening;
    - in `config.yml`, delete `max_now` and set `max_next` and `max_pending` explicitly;
    - delete the obsolete `#now` requirement from `bob_gtd.md`;
    - consider moving body habits (brushing teeth, fish oil) out of `#task`. They get checked off in batches days
      later, so they add no signal and sit in READY.

## 7. Limitations

- **Old data.** The month-long GTD gap inflates lane and Ready counts. The timing and sequencing findings (§2.1)
  and the churn timeline (§2.2) don't depend on those counts.
- **Rough forecast.** The load forecast (§2.5) approximates the queue rules from line text. It ignores dependency
  blocking and `#hide` children, and does not count NEW captures, so treat it as ±20%.
- **Coarse time attribution.** Time is split evenly across the note families linked in a block. Unlinked time
  (8.5%) is unattributed.
- **No live Obsidian session.** I didn't observe the status bar, the plugins' runtime behavior or the actual
  keystroke cost per review item. The ≈10-minute estimate's 5 seconds per item is the freshness report's
  assumption, not a measurement.
- **The lead synthesizes.** I'm one of five researchers. Read the lead's synthesis rather than all five reports;
  that is part of recommendation 2.

## Sources

- Vault evidence: `~/bob/2026/2026{0715..1001}.md`, `gtd_daily.md`, `done/gtd_daily_done.md`, `dash.md`,
  `freshness.md`, `bob_gtd.md`, `cash.md`, `job.md`, `gkeep_inbox.md`, `gtd.md`; vault commits `0a339bb5`,
  `10ed27a8`, `61b0921e`, `83254268`, `0701c271`, `d7c3343c` (randomize: 222 tasks), `4adadb89`.
- Tool output (2026-10-01): `bob plan`, `bob freshness list -f json`,
  `bob query --tasks … --origin dash.md -f json`, MacBook hooks log tail.
- bob-cli: `docs/plan.md`, `docs/freshness.md` §7, `docs/capture.md` (`=x` outcome table), `docs/randomize.md`;
  bead `bob-cli-34`; `plan:202609/priority_roll_decay.md`; bead `bob-cli-2q` (`+1` added).
- Earlier research: `research:202609/retire_now_sticky_lanes_ledger_today/retire_now_sticky_lanes_ledger_today.md`;
  `research:202609/ready_task_freshness_review/ready_task_freshness_review.md`.
- Decision records: `decisions:task-lanes-are-sticky`, `decisions:today-is-read-from-the-ledger`,
  `decisions:now-tag-is-user-owned` (superseded).
- External:
  - [GTD podcast #7: Guided Weekly Review](https://gettingthingsdone.com/2015/07/podcast-07-guided-gtd-weekly-review/)
  - [GTD & Procrastination](https://gettingthingsdone.com/2018/01/gtd-procrastination/)
  - [Pomodoro Technique (rules summary)](https://en.wikipedia.org/wiki/Pomodoro_Technique)
  - [Gollwitzer & Sheeran 2006, implementation intentions meta-analysis](https://www.socmot.uni-konstanz.de/publications/implementation-intentions-and-goal-achievement-meta-analysis-effects-and-processes)
  - [Newport's shutdown ritual (summary)](https://habitbox.app/blog/shutdown-ritual)
  - [Taskwarrior review](https://taskwarrior.org/docs/review/)
