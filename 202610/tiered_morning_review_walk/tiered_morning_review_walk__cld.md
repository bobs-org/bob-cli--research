# A tiered `]s` review walk with lane and scheduled refresh intervals: critique and recommendation

- **Researcher:** cld (one of five independent reports in this swarm).
- **Snapshot:** Thu 2026-10-01, afternoon EDT. This is the live vault on athena (`~/bob`, HEAD `03023bbd`),
  bob-cli `5d24c98`, and bob-plugins `4744607` (ledger-tools 1.14.1, nav-hotkeys 1.49.0).
- **Question:** Should `[s` / `]s` and Ctrl+Alt+J/K walk NEW → PENDING → NEXT → due scheduled → READY with a
  new sort order? Should lane and scheduled tasks get configurable refresh intervals that default to 1 day? And
  should the artificial values from the cutover seed be removed? How would I build it, and would I do it
  differently?

## Bottom line

**Most of this is a good idea, but two of the four parts need changing before you build them.**

1. **The new walk order is a clear win. Build it.**
   - It makes `]s` walk the dash in its own order (NEW → PENDING → NEXT), then the review page (RETURNED →
     ROTTEN).
   - Planning comes before maintenance. The 2026-10-01 morning-review research recommended exactly that.
   - It closes a real gap: the freshness walk can't see the 80 Next/Pending tasks today, and those are the
     lanes that are over their caps.
   - **Make the tiers explicit; don't let them fall out of the interval sort.** "New, pending, next, due
     scheduled, other ready" only comes out right while every lane and scheduled interval is shorter than every
     Ready interval. One `[refresh:: 1]` task or one config change would scramble it.
2. **Daily lane intervals (`pending_interval: 1`, `next_interval: 1`) are a good mechanism. Build them.**
   - They turn the sticky-lanes decision's required "daily review with release" into a walk with a ✓ for each
     task.
   - Every outcome already stamps the task: keep (Alt+F), link today (Ctrl+Shift+Enter), and release (Alt+N).
   - The cost is load. With lanes at 50/30, that's **80 lane decisions every morning**. At the 10/15 caps it's
     25.
3. **The scheduled interval, as you wrote it, doesn't do what you described. I recommend changing it.**
   - Your intent was that a scheduled task is reviewed "on the day it is due". The current RESURFACED rule
     already does that.
   - `interval = 1` for "any task that has a `scheduled` property" means something else. Every Ready task
     sitting past its scheduled date would come back **every morning** until you roll it, clear it, or finish
     it.
   - That adds **59 tasks on the first morning**. If you answer them with Alt+F ("still right"), the daily
     re-review set **grows from 59 to about 200 in two weeks** (forecast in §5).
   - My recommendation: give due-day scheduled tasks their own tier (RETURNED), and make the "every day while
     overdue" behavior an opt-in `scheduled_interval` that is off by default.
4. **There are no artificial `refresh` properties to remove. The artificial values are the seeded `fresh`
   dates, and you should leave them alone.**
   - The vault has **zero** `[refresh:: N]` fields and zero `task_refresh` frontmatter.
   - The cutover seed only staggered `[fresh::]` dates.
   - Stripping them makes about **153 tasks NEW on the next morning**. NEW is the uncapped tier.
   - Flattening them to one date makes a **140–199-task ROTTEN cliff on 10-08**, in the middle of the trial,
     and it **comes back every 7 days**, because tasks you confirm together come due together.
   - The stagger stops mattering by itself by 10-08, so doing nothing is the right move.

The sort rule you asked for is fine. Today it only uses the `fresh` → `created` part, because every Ready task
is on the default 7-day interval. Recommended design: [§8](#8-recommended-solution).

## 1. What exists today (verified)

**The keymaps are one command.**

- The vault's `obsidian_vimrc.md` maps `]s` / `[s` to `bob-navigation-hotkeys:jump-to-next-due-task` /
  `jump-to-prev-due-task`.
- Ctrl+Alt+J/K are the same two commands.
- nav-hotkeys has **no ordering logic of its own**.
  - `planReviewJump` (nav `main.js` around line 24255) walks whatever `api.freshness.queue()` returns, in
    order.
  - It wraps at the end.
  - After an Alt+Shift+F stamp, it continues from the remembered rank, because the Tasks cache lags.
- So the walk order is decided in two places:
  - `freshnessQueue` in bob-ledger-tools (`main.js` around line 4699);
  - its Rust mirror `queue()` in `src/native/freshness/state.rs`.
- Both run the shared vectors in `docs/freshness.md` §10.

**Current queue.**

- NEW by (path, line), then DUE by (due_on, path, line).
- DUE mixes RESURFACED and ROTTEN, ordered by due date.
  - This contradicts the documented ritual (§6: "RETURNED first, then age-expired ROTTEN").
  - Vector S14 actually puts the ROTTEN `a.md:2` ahead of the RESURFACED `a.md:4` on the same due date.
  - The new tiers fix this as a side effect.

**Scope.**

- Only `[ ]` Ready tasks are in scope (`in_scope` in `docs/freshness.md` §4). They must also be:
  - lane-visible;
  - non-recurring;
  - outside daily notes;
  - not linked today.
- `[*]` and `[/]` are explicitly out of scope (S13), and the marks show them as `resting · Not in the review
  queue: Next` (M9).

**Interval chain.** The task's `[refresh:: N]`, then the note's `task_refresh`, then `freshness.interval`, then
7.

- Lanes and `scheduled` have no interval of their own.
- `scheduled` only matters through RESURFACED: `fresh < scheduled ≤ today`, which is due on the scheduled day
  whatever the interval.

**Live vault** (regex scan, cross-checked against `bob freshness list`, which reports `1 new · 199 fresh · ✓ 393
today`):

| Population | Count |
| --- | ---: |
| Ready `[ ]`, visible, non-recurring, outside daily notes | 200 |
| …with `scheduled` today or earlier | **59** (23 today, 34 in September, 2 in August) |
| …with a `priority` (P-level) | 39 |
| PENDING `[/]` | **50** (cap 10) |
| NEXT `[*]` outside daily notes | **30** (cap 15) |
| Blocked `[?]` by a future date, so it will come back | 253 (14, 20, 21, 23, 10, 9, 8 returning 10-02 … 10-08) |
| `[refresh:: N]` fields on any task | **0** |
| Notes with `task_refresh` frontmatter | **0** |

**Ready `fresh` dates.** These are the seed's buckets, from commit `61b0921e`, "46 files", 2026-10-01 01:45 UTC:

| Date | Tasks |
| --- | ---: |
| 09-25 | 26 |
| 09-26 | 26 |
| 09-27 | 26 |
| 09-28 | 15 |
| 09-29 | 20 |
| 09-30 | 38 |
| 10-01 | 48 (seed bucket 7 plus real confirmations) |
| none | 1 |

The vault git log since 09-20 has no commit that adds or removes `refresh::`.

**Config.** `~/.config/bob/config.yml` has no `freshness:` block, so the interval is 7 and the budget is off.
The `plan:` block sets `max_pending: 10` and `max_next: 15`.

## 2. How I read the request (and what was ambiguous)

| You wrote | I read it as | Why |
| --- | --- | --- |
| "…then (if they have the same `refresh` property value) based on which was created later" | The same **`fresh`** date. | The tie-break follows "refreshed earlier". With equal intervals, an equal `fresh` date means an equal due date. |
| "…review a task with a 7d interval that is 3d overdue before **that one**" | "That one" is the 7d task that is 1 day overdue, not the 1d task. | Your rule puts the interval first. If you meant that a 7d task 3 days overdue should beat a 1d task due today, that's a scoring rule, not a lexicographic one (see alternative A3). |
| "remove all of the artificial `refresh` properties" | The seeded **`fresh`** dates. | No `refresh` property exists anywhere in the vault (§1). |
| "any task that has a `scheduled` property … default 1 … refreshed on the day they are due" | Your **intent** is review on the due day. | The literal rule differs; see §4.2. |

Your examples, written as a vector (today 10-08):

| Task | Interval | `fresh` | `created` | Days overdue |
| --- | --- | --- | --- | ---: |
| a | 1d | 10-07 | — | 0 |
| b | 7d | 09-30 | — | 1 |
| c | 7d | 09-28 | 09-01 | 3 |
| d | 7d | 09-28 | 09-04 | 3 |

The required order is **a, d, c, b**.

## 3. What's good about the plan

- **It makes `]s` mean "walk my dash".**
  - The dash sections are TODAY → NEW → PENDING → NEXT → READY.
  - The review page is RETURNED → ROTTEN.
  - The new walk is that list with TODAY and READY removed, and only items not yet confirmed today.
  - One mental model, one key.
- **It puts planning before maintenance.**
  - The current chore reads NEW → ROTTEN → PENDING → NEXT. The 10-01 morning-review research said that order
    is upside down, because the open-ended ROTTEN walk crowds out picking the highlight.
  - Your order lets you stop after NEXT, start the highlight, and do RETURNED/ROTTEN later in the day.
- **It finally puts the over-cap lanes in front of you.**
  - The sticky-lanes decision says its own cost is "no automatic forgetting … a daily review with release …
    required".
  - Today nothing walks you through that review.
  - Daily lane intervals do, and the stamps leave a visible ✓ on each lane task you've handled.
- **It reuses the existing gestures and stamps.**
  - Keep is Alt+F / Alt+Shift+F.
  - Do today is Ctrl+Shift+Enter: it stamps, and the task becomes Today, which takes it out of scope.
  - Release is Alt+N: it stamps and returns the task to Ready as FRESH.
  - Close or cancel works as today.
  - No new keys and no new write paths.
- **The sort rule is sensible.**
  - Short intervals are the ones you chose to see often, so reviewing them first works as a stand-in for
    importance.
  - Within an interval, the most overdue task comes first.
  - Newest first breaks ties, which favors items whose context you still remember.

## 4. Problems and risks

### 4.1 Removing the seeded stamps would bring back the overwhelm you're trying to avoid

There is nothing named `refresh` to remove, so "remove the artificial values" can only mean one of two things
for the `fresh` stamps:

- **Strip them.** About 153 tasks with pre-10-01 seeded stamps go back to having no stamp, which makes them NEW.
  - NEW is first in the walk.
  - It is "never capped, never skipped".
  - It is gated out of READY.
  - The next morning's walk starts with about 219 items (forecast C1). READY on the dash empties until you clear
    them.
- **Flatten them to one real date.**
  - All of them come due together: 140 on 10-08 even with the scheduled ones resolved, and 199 under the
    resurface-only rule.
  - That's the middle of the 10-05 → 10-18 trial. Its keep rule (red on no more than 3 mornings, about 30
    confirmed tasks on most mornings) would fail by construction.
  - **The cliff repeats every 7 days.** A group of tasks confirmed on the same day stays together (C2: 140 on
    10-08 *and* 140 on 10-15). The seed's stagger is exactly what prevents that.

Better ordering does not replace the stagger, because READY is freshness-gated:

- Under the accepted gating decision, a ROTTEN task is hidden from READY until you review it.
- So a pile of ROTTEN tasks is not just a long, sorted queue you can stop partway through. It is also an empty
  READY section, and a red chip.

The stagger is temporary anyway:

- By 10-08 every seeded date is at least 7 days old.
- So every seeded task will have come due once.
- From then on, each one carries either a real confirmation or a truthful "overdue".

**Recommendation: do nothing.**

### 4.2 "Scheduled interval = 1" gives you a daily reminder, not a review on the due day

How the rule plays out for a task with `scheduled 10-05`:

1. On 10-05 it is due. That's the existing RESURFACED rule, and it's the behavior you described.
2. You confirm it with Alt+F, and it gets `fresh 10-05`.
3. With interval 1 it's due again on 10-06, then 10-07, and so on. That continues until you:
   - roll it to a future date (Ctrl+Enter), which makes it Blocked and takes it out of scope;
   - clear `scheduled` (Ctrl+Shift+P → Ctrl+D);
   - or finish it.

Two consequences:

- **The day-one burst.** All 59 Ready tasks already past their scheduled date are due on 10-02, before any
  ordinary ROTTEN task.
- **Growth.** Every deferral that returns and gets "still right" joins the daily set. P-level rolls write
  `scheduled` on everything you defer. So the set grows by about 4–23 a day (forecast B: 59 → 201 by 10-15).

There is a real case for the strict version:

- `fresh` means "confirmed as written, including its schedule".
- A past `scheduled` date on a task you're keeping is stale metadata.
- The randomize doc calls such tasks "overdue P1–P4 tasks that bury the P0 work".
- A daily reminder pushes each one into the decay ladder (roll, then decay, then cancel), which already exists
  for this.
- If you always roll or clear rather than confirm, the load is fine (forecast B2).

But it changes what Alt+F means on those lines: it becomes "remind me tomorrow", not "keep". It also contradicts
what you said you wanted. So I recommend it only as an opt-in (§6, A4).

### 4.3 The lane load is front-loaded and may turn into reflexive stamping

- At today's 50/30 lanes, a daily interval means 80 lane decisions every morning before you reach RETURNED.
  - On day one that's useful. Walking PENDING with Alt+N *is* the one-time triage that the decision and the
    10-01 research both say is overdue.
  - Kept up daily at 80, it isn't sustainable.
- At the caps it's 25 a day: roughly 2–4 minutes of Alt+Shift+F and Alt+N.
- The quieter risk is that confirming the same 25 tasks every day becomes automatic, and the stamps stop meaning
  anything.
  - Use the 10-01 research's own rule: if more than about 90% of lane reviews end in "keep", lengthen
    `next_interval` to 2–3.
  - Leave Pending at 1. Pending is the "pull this first" lane.

### 4.4 The order you asked for only comes out right with the current defaults

Your model sorts every tier by interval. The order NEW, PENDING, NEXT, due scheduled, other ready only comes out
because every lane and scheduled interval happens to be 1 and every Ready interval happens to be at least 7.
It breaks in three easy ways:

- Set `[refresh:: 1]` on a Ready task, and it lands among the scheduled tasks.
- Set `next_interval: 3`, and NEXT mixes with 3-day Ready tasks.
- Lanes and scheduled tasks all at 1 can't be ordered among themselves by interval at all.

**Make the tiers structural**, and apply the sort only within a tier.

### 4.5 Sorting by interval first changes nothing today, and the long tail it delays is bounded

- With zero `refresh` fields and no `task_refresh`, every Ready interval is 7.
- So today the ROTTEN order is just `fresh` ascending, then `created` descending.
- The interval key starts to matter once you use the refresh row's presets (2, 3, 7, 14, 30, 90, 180, 365).
- A long-interval task can then wait behind every 7-day task on mornings when you stop at the budget.
- That's acceptable:
  - you chose to see those tasks less often;
  - the weekly prune already says "clear any leftover ROTTEN", so the wait is bounded at about a week.

### 4.6 Lane stamps would fill up the budget meter

- `refreshed_today` counts stamps on tasks of any status.
- Once lanes are in the walk, 25 lane confirmations turn a 15-task `rotten_daily_budget` green before you've
  touched a single ROTTEN task.
- The budget should count Ready-pool confirmations only. That's the same "confirmed FRESH" number the trial
  tally already has to track separately.

### 4.7 Effects on the contracts (things that break if done naively)

- **The dash-gating contract must not move.**
  - `rotten.md` filters on `not done` plus `bucket === "rotten"`, with **no status filter**.
  - If lane tasks got the `rotten` bucket, they would show up on the review page and in the ROTTEN chip.
  - Keep `state` and `bucket` exactly as they are for lanes (null), and add a separate **tier** evaluation.
  - That also leaves READY, NEW, and ROTTEN, and so the trial's measurements, unchanged.
- **Recurring lane tasks would stay due forever.** `stampLine` refuses recurring tasks, so the lane tiers have
  to exclude them, just as Ready does.
- **The interval logic is duplicated in nav.**
  - `describeRefreshInterval` in nav-hotkeys reimplements the precedence for the Ctrl+Shift+P refresh row.
  - Without a change it would show `every 7 d (config)` on a Next task that is actually reviewed daily.
  - Have it call an api `intervalFor` instead.
- **Marks.**
  - M9, M10, and M14 now say lane tasks are "Not in the review queue".
  - Lane tasks that are due need the `due` tone (⟳), and their tooltip needs the lane outcomes.
- **Version bumps.**
  - JSON `tier` changes from `new|due` to five values, so it becomes schema 3.
  - ledger-tools' freshness namespace becomes v4.
  - nav keeps working against v3, because it only follows the queue order.
- **Memory records.**
  - The ritual order in `decisions/ready-is-freshness-gated` ("NEW … then rotten.md … then PENDING → NEXT")
    and the interval chain in the `glossary:freshness` strand both change.
  - That needs a new decision record plus a strand update, done through `/sase_memory_write`, not edits in
    place.

### 4.8 Timing

- The 14-day trial starts **2026-10-05**. If this lands before then, the trial measures the ritual you'll
  actually keep.
- Lane tiers don't touch the gated quantities, so landing them before the start is safe.
- Landing them in the middle would mix two different rituals in one tally.
- The 10-01 research also recommended a 14-day freeze on process changes. If you want to honor that, this is a
  defensible choice for the single change. It directly implements that report's "plan first, maintain later".

## 5. Forecast: review decisions per morning

How the forecast works:

- I wrote a small simulation over the live vault.
- Every due item is reviewed each day.
- Ready outcomes are "still right" (restamp).
- Date-blocked `[?]` tasks without `dependsOn` come back as RESURFACED on their date.
- New captures (about 14 a day in September) are **not** included.

Scenario A reproduces the 10-01 research's independent forecast: seeded tasks 26/26/26/15/20/38/47, and
deferrals coming back 13/19/20/23/10/9/8.

| Scenario | Fri 10-02 | Mon 10-05 | Thu 10-08 | Thu 10-15 | 14-day peak |
| --- | ---: | ---: | ---: | ---: | ---: |
| **A** Today's rules (lanes not walked) | 41 | 38 | 56 | 60 | 60 |
| **B** Literal request: lanes 1d with 80 live, scheduled 1d, scheduled items confirmed with Alt+F | 180 | 230 | 264 | **305** | 305 |
| **B2** Literal request: lanes at caps (25), scheduled 1d, every scheduled item rolled or cleared | 125 | 62 | 53 | 49 | 125 |
| **R** Recommended: lanes 1d at caps (25), RETURNED tier, `scheduled_interval` off | 66 | 63 | 81 | 85 | 85 |
| **C1** = B2, plus seeded `fresh` stripped | **219** (153 NEW) | 49 | 53 | 49 | 219 |
| **C2** = B2, plus seeded `fresh` flattened to 10-01 | 99 | 49 | **173** | **169** | 173 |
| **C2r** = R, plus seeded `fresh` flattened to 10-01 | 40 | 48 | **232** | **236** | 236 |

How to read the table:

- **B vs B2.** The literal scheduled rule is only manageable if "still right" is never your answer to a
  past-scheduled task.
- **C1, C2, and C2r.** Removing the stagger either floods NEW once (stripping) or creates a weekly cliff that
  keeps coming back (flattening).
- **R vs A.** The recommendation adds exactly the lane review (+25 a day at the caps) and nothing else.
  - R's 14-day total is higher than B2's only because B2 assumes every scheduled task leaves the pool.
- **Beyond any of these scenarios:** the steady state of about 45–60 Ready decisions a day (200 ÷ 7 plus
  returning deferrals) is the underlying load problem. That calls for longer intervals on low-churn notes and a
  `rotten_daily_budget`, not for reordering.

## 6. Adjustments to your requirements (called out)

| # | You asked for | I recommend instead | Why |
| --- | --- | --- | --- |
| **A1** | Order NEW → PENDING → NEXT → due scheduled → READY, with the scheduled/ready split coming out of interval sorting | **Explicit tiers**: NEW → PENDING → NEXT → RETURNED → ROTTEN, sorted only within each tier | It's always true, whatever the config (§4.4). It reuses existing vocabulary: the review page already calls due-day scheduled tasks RETURNED. |
| **A2** | Ready order: interval ascending, then "refreshed earlier", then created later | **As asked**, with "refreshed earlier" written as due date ascending (the same thing at equal intervals). Then path, then line. A missing `created` sorts last. | It matches your examples (a, d, c, b). Using the due date lets one comparator serve every tier. |
| **A3** | No order given inside NEW, PENDING, or NEXT | NEW keeps (path, line), so the inbox is processed in note order. PENDING, NEXT, and RETURNED use most overdue first (never-stamped first), then newest `created`, then path, then line. | One rule to remember: "most overdue, then newest". NEW stays in note order so a Keep inbox is processed top to bottom. |
| **A4** | Tasks with `scheduled` get a configurable interval, default 1 ("refreshed on the day they are due") | Due-day review is **always on**: it's the RETURNED tier, today's RESURFACED rule. An **opt-in** `scheduled_interval` (default **off**) controls re-review while a Ready task stays past its date. | Your stated intent is the due-day review. The literal default adds 59 tasks on day one and grows without bound if you answer with Alt+F (§4.2, B). It also changes READY gating during the trial. |
| **A5** | `pending_interval` and `next_interval`, default 1 | **As asked.** Also, `null` means "don't walk this lane" (today's behavior, and a one-line rollback). Lane intervals **override** a task's `refresh` and the note's `task_refresh` while the task is in the lane. | A lane is a short-lived commitment check, while `refresh` sets how often a backlog item comes back. A Next task carrying `[refresh:: 30]` from its Ready days should still be checked daily. |
| **A6** | (implicit) | Lane and scheduled stamps do **not** count toward `rotten_daily_budget`. Add a Ready-only `confirmed_ready_today` count. | Otherwise the meter is meaningless (§4.6), and the trial needs that count anyway. |
| **A7** | Remove the artificial `refresh` properties | **Do nothing.** No `refresh` properties exist, and the seeded `fresh` dates expire by themselves by 10-08. | Stripping floods NEW; flattening creates weekly cliffs (§4.1, C1, C2). |
| **A8** | (implicit) | Recurring tasks, daily-note tasks (the R9 carve-out), and Today-linked tasks stay out of every tier. | Recurring lines can't be stamped. Daily-note lanes clear by themselves. Today has already been decided. |

## 7. Alternatives considered

- **Alt-1: a session walker, with no lane stamps.** Build a snapshot list at the first `]s` and remember what
  you've seen in memory.
  - *Rejected.* It forgets across devices and restarts, loses the ✓ marks, and duplicates state that stamps
    already store.
  - Stamps are the persistent "I looked at this today" record. Lanes are already stamped by every lane
    gesture.
- **Alt-2: lane review through chips only.** Leave lanes out of the walk and rely on the PENDING/NEXT section
  chips and the caps.
  - *Rejected.* That's the status quo, and it's the step that didn't happen.
  - The walk gives a concrete next item and a "done" signal.
- **Alt-3: a score instead of a lexicographic sort** (for example, days overdue ÷ interval).
  - *Rejected for now.* Your examples rule it out (a must beat b), and its order is harder to predict when
    stepping through.
  - Revisit it only if long-interval tasks starve past the weekly prune.
- **Alt-4: one interval-sorted queue with no tiers** (the literal model). *Rejected:* §4.4.
- **Alt-5: deterministic interval jitter.** Add ±1 day, keyed on a hash of the block ID, to break up groups of
  tasks that come due together.
  - *Not now.* The seed's stagger already does that.
  - Keep it in reserve in case a large bulk confirmation (for example, a weekly prune that stamps 60 tasks)
    starts producing weekly spikes.
  - The price is that "due in exactly N days" stops being predictable.

## 8. Recommended solution

### 8.1 Model

**Tiers, walked in this order.** Each tier holds only tasks that are due and have not been stamped today.

| # | Tier | Members | Due when | Order within the tier |
| --- | --- | --- | --- | --- |
| 1 | **NEW** | Ready `[ ]` in scope (today's rule) with no valid `fresh` | always | path, line |
| 2 | **PENDING** | `[/]`: lane-visible, non-recurring, outside daily notes, not Today | no `fresh`, or today ≥ `fresh` + `pending_interval` | due date ↑ (never-stamped first), `created` ↓ (missing last), path, line |
| 3 | **NEXT** | `[*]`, with the same filters | no `fresh`, or today ≥ `fresh` + `next_interval` | the same as PENDING |
| 4 | **RETURNED** | Ready, in scope, with `fresh < scheduled ≤ today` (today's RESURFACED). With `scheduled_interval` set, also Ready tasks past their `scheduled` date whose `fresh` + `scheduled_interval` ≤ today | as stated | due date ↑ (the oldest `scheduled` first), `created` ↓, path, line |
| 5 | **ROTTEN** | Ready, in scope, with today ≥ `fresh` + interval | today's rule | **interval ↑, due date ↑, `created` ↓**, path, line |

**Config** (in the existing `freshness:` block; flat keys, valid values 1–365 or `null`):

```yaml
freshness:
  interval: 7               # Ready backlog (unchanged)
  pending_interval: 1       # [/] PENDING lane review cadence; null = not walked
  next_interval: 1          # [*] NEXT lane review cadence; null = not walked
  scheduled_interval: null  # opt-in: re-review cadence while a Ready task sits past its scheduled date
  rotten_daily_budget: 15   # counts Ready-pool confirmations only
```

**Interval precedence:**

| Task | Interval |
| --- | --- |
| In a lane tier | the lane's interval (overrides `refresh` and `task_refresh`) |
| Ready | task `refresh` → `scheduled_interval` (if set and `scheduled` < today) → note `task_refresh` → `interval` → 7 |

**Unchanged:**

- `state()` and `bucket()` for every task, so lanes stay `null`.
- The READY, NEW, and ROTTEN gating.
- The `rotten.md` filters.
- The dash chips.
- Stamping rules.
- "Freshness never changes a lane, Today, schedule, or priority."

### 8.2 Changes by repository

**bob-cli (Rust): the contract owner.**

- `docs/freshness.md`:
  - §2: config keys and the precedence table.
  - §4: the tier evaluation beside the unchanged state/bucket rules.
  - §6: the new ritual, plus a "for a past-scheduled task, roll or clear rather than Alt+F" line.
  - §7: JSON schema 3, with `tier ∈ new|pending|next|returned|rotten` and counts gaining `pending`, `next`,
    `confirmed_ready_today`.
  - §10: vectors.
  - §12: lane marks.
- `src/native/config/freshness.rs`: the three keys, validated like `interval`. An invalid value is a config
  error with exit 2, the same as today.
- `src/native/freshness/state.rs`:
  - a `Tier` enum and a `tier_for(row)` function;
  - lane evaluation reads `row.status` and `row.created`, both already filled in and currently marked
    `dead_code`;
  - `queue()` sorts by (tier, the tier's comparator);
  - `counts()` adds the lane counts, and `budget_met` uses Ready-only confirmations.
- `src/native/freshness/scan.rs`: already builds rows for every status with `created` and `is_today`. Check
  that lane rows get the same `lane_visible`.
- `src/native/freshness/cli.rs`: human sections NEW / PENDING / NEXT / RETURNED / ROTTEN, and the
  `--help` text that describes the order.

**bob-plugins / bob-ledger-tools (the JS mirror, namespace v4).**

- `coerceFreshnessConfig` gets the three keys.
- `freshnessRowFromTask` adds `statusSymbol` and `created`.
- `freshnessEvaluate` / `freshnessQueue` use the tiers and comparators.
- `freshnessTierForState` gives `"1 · NEW"` … `"5 · ROTTEN"`, so `rotten.md`'s `sort by … rank` follows
  automatically.
- `freshnessCounts` and `reviewModel` get lane counts, and the budget becomes Ready-only.
- The status bar shows, for example, `REVIEW 2 new · 9 pending · 12 next · 13 returned · 26 rotten`.
- The mark model gets a `due` tone on lane-due tasks. The tooltip reads, for example, `Daily NEXT review · Alt+F
  keep · Alt+N release · Ctrl+Shift+Enter today`.
- Expose `intervalFor(task)` with its source (`task|note|config|default|pending|next|scheduled`).

**bob-plugins / bob-navigation-hotkeys (small).**

- No ordering code.
- The jump notice names the tier, for example `NEXT · 14/62`.
- Show **one tier-boundary notice** when Alt+Shift+F or `]s` leaves NEXT: `Planning tiers done — 39
  RETURNED/ROTTEN left`. This puts the 10-01 research's "exit gate, then the highlight" into the tool.
- `describeRefreshInterval` reads the api's `intervalFor`, so the refresh row shows `every 1 d (next lane)`.
- While there, the fallback counts still use the pre-migration `stale` key. Rename it to `rotten`.

**Vault and config.**

- Add the `freshness:` block above to `~/.config/bob/config.yml`. The repo's config template comment should
  match it.
- Rewrite the `gtd_daily.md` "Morning review" chore: "`]s` through NEW (clarify) → PENDING → NEXT (link
  today / keep / release with Alt+N); start the highlight; later, RETURNED → ROTTEN until 0 or budget."
- Optionally switch `rotten.md`'s RETURNED/ROTTEN split to the tier rather than the state, so that the opt-in
  `scheduled_interval` re-reviews land under RETURNED.

**Memory** (through `/sase_memory_write` during implementation):

- A new decision record, for example "the review walk is tiered: NEW → PENDING → NEXT → RETURNED → ROTTEN;
  lanes are reviewed daily by stamp". It partly supersedes the ritual-order clause of
  `decisions/ready-is-freshness-gated`.
- An update to the `glossary:freshness` strand's interval chain and scope sentence.

### 8.3 Conformance vectors to add (both languages)

- **Q1 (your example).** Today 10-08, Ready:
  - a: `[refresh:: 1]`, fresh 10-07;
  - b: fresh 09-30;
  - c: fresh 09-28, created 09-01;
  - d: fresh 09-28, created 09-04.
  - ROTTEN order: **a, d, c, b**.
- **Q2 (tier order).** One task each of NEW, PENDING (fresh 10-07), NEXT (no fresh), RETURNED, and ROTTEN, in
  reverse path order. The queue still comes out in tier order.
- **L1.** A `[*]` stamped 10-08 is not in the queue. A `[*]` stamped 10-07 is tier `next`, due 10-08,
  `days_overdue` 0. Its `state` and `bucket` stay null.
- **L2.** A `[/]` with `[refresh:: 30]`, fresh 10-07, `pending_interval: 1` → due (the lane overrides).
- **L3.** A recurring `[*]` and a `[*]` linked today → not in any tier.
- **L4.** `next_interval: null` → `[*]` tasks are never queued (today's behavior).
- **R1.** RETURNED is ordered before a ROTTEN task with an earlier due date (this replaces S14's interleaving).
- **R2.** `scheduled_interval: 1`, Ready, scheduled 10-05, fresh 10-07 → tier `returned`, state `rotten`,
  bucket `rotten`.
  - With `scheduled_interval: null`, the same task is FRESH until 10-14.
- **B1.** 20 lane stamps and 5 Ready stamps today with budget 15 → `budget_met: false`.
- **Updates.** S13 (lanes are out of *state* scope but in *tier* scope), S14, and the M9, M10, and M14
  tooltips.

### 8.4 Rollout

1. **Land before Mon 10-05.** Rust and the contract first, then ledger-tools and nav, then the vault chore and
   config, then the memory records.
   - That's a medium epic of about 4 phases. Most of the work is mirrored code plus vectors.
2. **Use the first walk as the lane triage.**
   - The first morning will put all 80 lane tasks in front of you.
   - Release with Alt+N until the chips read at most 10 and at most 15.
   - After that it's about 25 a day.
3. **Leave the seeded `fresh` dates alone.**
   - On 10-08, `bob freshness list` should show no seeded stamp that hasn't already come due once.
   - Any 09-25 … 09-30 stamp still on a Ready task after that is a task you skipped, and it is already
     truthfully overdue.
4. **Keep `scheduled_interval` off during the trial.**
   - Turn it on afterwards if you want the daily reminder for overdue scheduled tasks.
   - If you do, train "roll or clear, not Alt+F" for past-scheduled tasks. B2 shows that keeps the load
     flat.
5. **Signals to watch** (on top of the trial's keep rule):
   - the share of lane reviews that end in "keep": above 90% means lengthen `next_interval`;
   - minutes from the first `]s` to the tier-boundary notice: about 10 or less once the lanes are at their caps;
   - whether ROTTEN leftovers reach the weekly prune. If they regularly do, apply the 10-01 research's advice:
     lengthen `task_refresh` on low-churn notes such as `sase.md`, rather than reordering.

## Sources

- **bob-cli:**
  - `docs/freshness.md` (§§2, 4, 6, 7, 10, 12, 13);
  - `src/native/freshness/state.rs` (`evaluate`, `interval_for`, `queue`, `counts`, and `FreshnessRow`'s
    unused `status` and `created`);
  - `src/native/freshness/scan.rs`;
  - `src/native/config/freshness.rs`;
  - `docs/randomize.md`.
- **bob-plugins `4744607`:**
  - `plugins/bob-ledger-tools/main.js`: `freshnessIntervalFor` (around line 4516), `freshnessEvaluate` (around
    4555), `freshnessQueue` (around 4699), `freshnessRowFromTask` (around 5647), `planLaneVisible` (around
    2947);
  - `plugins/bob-navigation-hotkeys/main.js`: `describeRefreshInterval`, `reviewQueueEntryKey`,
    `planReviewJump` (around 24000–24340), `readFreshnessCounts` (around 27074);
  - `README.md`, the plugin table.
- **Vault `~/bob` at `03023bbd`:**
  - `obsidian_vimrc.md` (the `]s` / `[s` mappings);
  - `dash.md` (the NEW / PENDING / NEXT / READY queries);
  - `rotten.md` (the RETURNED/ROTTEN filters, with no status filter);
  - `gtd_daily.md` (the current morning chore);
  - the seed commit `61b0921e`;
  - a regex census of task lines and `[fresh::]` dates;
  - `~/.config/bob/config.yml`.
- **Live `bob freshness list`** (human and JSON), 2026-10-01.
- **Memory:**
  - `decisions:ready-is-freshness-gated`;
  - `decisions:task-lanes-are-sticky`;
  - `decisions:today-is-read-from-the-ledger`;
  - `decisions:task-status-is-derived`;
  - `glossary:freshness`, `glossary:task-link`, `glossary:pomodoro`.
- **Prior unrelated research:**
  `research:202610/gtd_morning_review_pomodoro_cutover/gtd_morning_review_pomodoro_cutover__final.md`. I used
  it for the freshness forecast (which scenario A reproduces), the "plan first, maintain later" ritual, the
  lane-cap triage, and the 14-day freeze.
- **The forecast simulation** (my own, not committed): a regex scan of the vault plus a day-by-day replay of
  the §4 evaluation rules, under the assumptions stated in §5.
