# Daily stats as a derived Pulse, not a habit app

Researcher: `grk`. Independent design research for tracking daily integer stats (GTD review, Pomodoro time, tasks created/completed, and whatever comes next) with a period-adjustable visualization. Peer swarm reports were not consulted.

## Verdict

Do it. Ship a **Pulse**: a catalog of daily integers that Bob derives from the vault, with a thin nightly latch only for numbers the vault forgets, rendered as a contribution grid on a new Dashboard child. Do not ship a habit tracker.

The request is right about the shape of the data (one integer per day, easy to add series later, range-adjustable view). It is wrong about the product. Bryan already tried a dedicated `@HABIT` daily log in Zorg (2024-05-22 through 2024-06-27) and abandoned it. The chores that log used to hold now complete as `#gtd #pre` / `#gtd #post` tasks. Pomodoro minutes already live on the ledger as `[t:: Nm]`. Completions and created dates already live on task lines. A second daily artifact that wants to be filled in by hand will die the same death, and it will steal the first block to do it.

The feature earns its keep if opening Pulse answers, in one glance, "how has this week gone?" for a metric Bob already knows. It fails if Bryan has to log a number the vault already holds, if a streak counter becomes the goal, or if "walk items processed" becomes a high score.

## Bottom line

1. **Pulse is a read view of facts Bob already has.** `bob pulse` (CLI) and a `bob-pulse` code block (Obsidian, sibling of `bob-plan`) share one catalog. The plugin never computes the series; it renders JSON Bob returns, the same thin-client rule as Mac Capture.
2. **Derive what the vault still knows; latch only what it overwrites.** Pomodoro minutes, `#gtd` checklist completions, `[completion::]`, and `[created::]` are reconstructable forever, including from `done/`. Freshness stamps are not: `[fresh::]` is last-reviewed, so yesterday's walk count vanishes the next morning. Nightly (and POST closeout) snapshot those ephemeral counts into `_generated/bob-pulse.json`.
3. **The home is `pulse.md`, not the daily note.** Daily notes stay today's ledger. The Pomodoro heading query stays as the in-day glance. Pulse is the cross-day view, with period chips (7 / 14 / 30 / 90 / year / custom) and metric chips. A Dashboard Browse badge opens it. Monday's weekly prune already asks to "check hours and created vs closed"; that sentence is the spec for the default view.
4. **Headline a contribution grid and a rate, never a streak.** One pale cell in a month of work is a miss. A streak counter that resets to zero is a quit. Loop Habit Tracker, GitHub's contribution graph, and the 2026 habit-tracker literature all agree on this; Bob's own date-marks already teach "quiet by default, louder only when it matters."

---

## 1. Is this a good idea?

Yes, with a rename and a narrower job.

Bob already produces the four requested series. What is missing is a *range* view that is as calm as the dashboard chips and as trustworthy as `bob plan`. The weekly prune in `gtd_daily.md` already tells Bryan to look at hours and created-vs-closed, and the freshness decision's reopen clause already cares whether more than about 90% of NEXT reviews end in keep. Those are stats the system promised itself and never instrumented.

Three properties of the current vault make Pulse the right shape:

- **The ledger is already a daily integer store for time.** Every closed Pomodoro carries `[t:: Nm]` under `## Pomodoros`. The daily template already sums it in the heading with an inline Dataview query. Last week that sum was 175, 300, 250, 375, 260, 250, 0 minutes (Sun still open).
- **Task dates are already a daily integer store for inventory.** `[created::]` and `[completion::]` survive `bob task archive` into `done/`. Native `bob query --tasks` already groups them. Last week non-GTD creates ran 7 / 18 / 22 / 28 / 26 / 28 / 3; non-GTD completions ran 7 / 87 / 25 / 33 / 18 / 38.
- **The `#gtd` checklist is already a habit tracker.** Six PRE chores complete every day. The POST "Morning review" closeout completed on Oct 6, 8, 9, 10 and was missed on Oct 5 and 7. That 0/1 is the ritual. Counting "walk items processed" on top of it would measure throughput, which the tiered-walk decision already flagged as rubber-stamp risk.

The idea is a good idea if it is a *mirror*. It is a bad idea if it is a *second practice*.

---

## 2. Critique of the original plan

The request asks for: one integer per day for GTD-review completions via `]s`, Pomodoro hours/minutes, tasks completed, tasks created; easy new metrics later; a visualization over an adjustable period; lead the design so it is intuitive, reliable, and beautiful.

### What to keep

- **One integer per day as the v1 atom.** Durations store as minutes, booleans as 0/1, rates as basis points (0–10000). Display is a separate formatter (`4h 10m`, `85%`, `yes`). The catalog stays boring on purpose.
- **Easy new series.** This is a catalog problem, not a UI problem. One extractor plus one catalog row must light up CLI, JSON, and the grid without a new plugin screen.
- **Adjustable period.** 7 / 14 / 30 / 90 / year / `from`–`to`. Default the grid to 30 days and the CLI sparkline to 14. The weekly prune is a 7-day question; a year grid is the "how has this been going" question.
- **Lead with beauty.** Bob already has a visual language (date marks, work-badge tones, `bob-plan` chips, freshness footer). Pulse must speak it, not import GitHub-green or a spreadsheet.

### What to change

These are explicit requirement adjustments.

**A1. This is Pulse, not a habit tracker. (rename)**

"Habits/stats" mixes two products. Habits (fish oil, brush teeth, morning review) are already tasks on `gtd_daily.md`, completed through the `]s` walk. Stats are aggregates over work already recorded. Rebuilding a habit app on top of those tasks would duplicate PRE/POST and invite a streak UX that the 2024 `@HABIT` log already proved unsustainable.

Call the feature **Pulse**. Put it next to `bob plan` and `bob freshness` in Daily workflow. The word "habit" stays in the GTD checklist, where it belongs.

**A2. Split "morning GTD review tasks I completed via `]s`" into three series. (definition)**

The request treats one number as if the walk were a list of completable chores. The walk is not that. PRE/POST `#gtd` rows resolve by completion; NEW / PROJECTS / PENDING / NEXT / TICKLER / ROTTEN resolve by stamp, release, link, or close, and the stamp overwrites. The footer already warns that `r/N` is a queue position, not a completed-task count.

v1 series:

| id | What it actually measures | Kind |
| --- | --- | --- |
| `gtd_pre` | `#gtd #pre` completions that day (the chores; currently 6) | derived |
| `review_closed` | POST "Morning review" completed that day (0/1) | derived |
| `walk_answered` | `refreshed_today` at latch time (stamps that day) | latched |

`review_closed` is the ritual. `gtd_pre` is the chore strip. `walk_answered` is a diagnostic, never a goal. Making walk volume a target would reward rubber-stamping, which is exactly the cost the tiered-walk decision named.

**A3. Exclude GTD recurrence and `#ref` swarm closeouts from created/done. (definition)**

Raw "tasks completed" last week is dominated by things that are not "I finished work":

- GTD PRE/POST recurrence is a flat 6–7 every day.
- Oct 6's 94 completions include 32 `done/sase_done.md`, 18 `done/gkeep_inbox_done.md`, and 25 `#ref` (research-chat) tasks.
- Each daily note also creates a `^gtd` Task Link with `[created:: today]`.

Without exclusions, created-vs-closed is a chart of research swarms and inbox dumps. Default `tasks_created` / `tasks_done` to `#task` lines excluding `#gtd` recurrence, excluding `#ref`, excluding the daily `^gtd` link. Keep `ref_created` / `ref_done` as optional catalog rows so reading-queue throughput is still visible. `net_tasks = tasks_created - tasks_done` is the weekly-prune number.

**A4. Split Pomodoro minutes into all vs work. (definition)**

The 2024 habit log already tracked `all` and `work` separately. Last week GTD ate the day more than once: Oct 6 was 215 GTD minutes vs 85 work; Oct 8 was 65 GTD vs 310 work. The heading query sums everything, which is the right in-day total. Pulse's default series is `pomodoro_work_min` (closed `[t::]` whose name is not GTD). `pomodoro_min` stays available. Store minutes; display `h'h' m'm'` with the same `durationformat` the heading already uses.

**A5. Do not write derived integers back onto daily notes. (storage)**

Decision `today-is-read-from-the-ledger` rejected a `#today` tag because it was a second copy of the ledger, rewritten on a timer, with churn and staleness. Putting `completed: 12` in daily frontmatter is the same mistake for a different field. Completions already have `[completion::]`. Closed sessions already have `[t::]`. The only numbers that must be stored are the ones the vault forgets: freshness-day counts.

Latch file: `_generated/bob-pulse.json`, git-tracked, vault-synced, one object keyed by `YYYY-MM-DD` holding only latched fields. Nightly writes yesterday if missing. Completing POST "Morning review" may write today's latched snapshot early. No per-stamp write during `]s` (do not slow the walk).

**A6. The visualization lives on `pulse.md`, not on every daily note. (UX home)**

A chart on each daily note is the 2024 `@HABIT` file with a prettier coat: a second daily artifact to open, a template change, linter churn, and a view that can only see one day. Daily notes keep the existing heading query and the `bob-plan` block. Pulse is a Dashboard Browse child, the way Projects and References already are. The weekly prune's "check hours and created vs closed" becomes "open Pulse." Optional later: a month-scoped `bob-pulse` fence on the empty monthly template.

**A7. Zero extra daily work. (reliability)**

Prior GTD-cutover research found that building the system crowded out running it (~23% of September's logged time went to GTD and bob tooling) and that morning GTD died when the first block became operations. Pulse must add no checkbox, no capture grammar, no end-of-day form. If a future metric does not already live in the vault, it goes through `pulse.extra.<id>` on the daily note (a typed integer Bryan logs only when he wants a new series). v1 ships the slot and does not use it.

**A8. Do not headline streaks. (UX)**

Streaks measure consecutive days and punish a single miss out of proportion to the record (a 28/30 month becomes a streak of 3). Loop Habit Tracker's score exists specifically because "don't break the chain" destroys progress on a sick day. GitHub-style contribution grids show trend, not status: a miss is one pale cell. v1 shows (a) the grid, (b) `N of D days` in the period, (c) period sum / median / delta vs the previous period. A streak may appear in a tooltip. It is never the big number.

**A9. Walk volume is not a success metric. (Goodhart)**

If `walk_answered` is on the home row, the walk becomes a high score. The reopen condition in `review-walk-is-tiered` is keep rate and PRE skip rate, not throughput. Show `walk_answered` and `upkeep_today` in a Review group, behind the ritual chips. If keep-rate latching is cheap (count keep vs non-keep answers in the existing stamp path into the same JSON), ship `next_keep_bps` in v1 because the weekly prune already depends on it; otherwise it is the first follow-up, not a reason to delay Pulse.

---

## 3. What already exists (do not rebuild)

### Daily glance

The daily template (`_templates/daily.md`) already renders closed-session time in the Pomodoro heading:

```markdown
## Pomodoros (`= durationformat(default(sum(nonnull(map(filter(this.file.tasks, (task) => task.completed AND startswith(meta(task.section).subpath, "Pomodoros")), (task) => task.t))), dur("0m")), "h'h' m'm'")`)
```

Keep this. It is the right in-day number. Pulse is the range view of the same `[t::]` field.

The `bob-plan` fence already paints TODAY / PENDING / NEXT / READY as live chips with the work-badge tone scale (grey / blue / green / yellow / orange / red). Pulse chips reuse that chrome. They do **not** reuse that scale for "more minutes is more pressure." Achievement series use a depth scale (grey → blue → green). Pressure series (inbox remaining, net-positive backlog, NEW remaining) use the existing work-badge scale.

### Ritual

`gtd_daily.md` already *is* the habit list. PRE chores and POST closeout carry `[repeat:: every day when done]` and `[completion:: YYYY-MM-DD]`. They archive into `done/gtd_daily_done.md`. Last week PRE was 6/6 every day; POST was the actual missable habit.

The morning GTD review footer already shows due / commitments / `✓ upkeep/budget today`. Those are *today's queue*, not history. Pulse does not replace the footer.

### Inventory dates

Date marks already render `created` and `completion` as `+ Aug 31` and `✓ Sep 3`. The fields are the source of truth. Pulse counts them; it does not restyle them.

`bob query --tasks 'done on or after 2026-10-05'` and `created on or after …` already return the rows. That is a stopgap, not a product: no period chips, no exclusions, no grid, no comparison to the previous window.

### 2024 `@HABIT` tracker (negative evidence)

From 2024-05-22 to 2024-06-27 Bryan kept a per-day `@HABIT Tracker` note (`2024/20240522_habit.md` and siblings) with manual integers: meds, run miles, time of first Pomodoro, work-from-office, CL mailed/submitted, AM/PM routine, pomodoros `all` / `work`, and a bank spend log with running totals. It required a second daily file, mixed habits with accounting, and stopped. The AM/PM routine migrated into GTD PRE tasks; Pomodoros migrated into the ledger; the bank log has no successor on purpose. Pulse must not resurrect this file.

### Plugin set

The vault's community plugins are a closed, curated list. There is no Tracker, Heatmap Calendar, Obsidian Charts, or Calendar plugin. Adding one would be a third rendering stack next to Tasks and bob-ledger-tools. Rejected.

### Nightly

`bob nightly` is vault-sync → task archive → vault-sync. Latch fits as a fourth step, after archive, writing **yesterday** if `BOB_NOW` has rolled (a 00:05 cron must not latch an empty today). Completing POST "Morning review" may latch today early so a missed nightly still has the ritual snapshot.

---

## 4. Recommended architecture

```text
                    vault facts
         ┌──────────────┼──────────────────┐
         │              │                  │
    daily [t::]   [created::]/[completion::]   [fresh::] (overwrites)
         │              │                  │
         │         derived extractors      │ live today only
         │              │                  │
         │              │           nightly / POST latch
         │              │                  │
         │              │         _generated/bob-pulse.json
         │              │                  │
         └──────────────┴────────┬─────────┘
                                 │
                          bob pulse catalog
                          (id, unit, kind, palette, extract)
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              bob pulse CLI              ```bob-pulse
              (Daily workflow)           pulse.md + monthly
                    │                         │
              colored sparkline          contribution grid
              JSON for any client        period + metric chips
```

**Bob owns every fact.** Roles, exclusions, Pomodoro name parsing, GTD tag membership, date validity, and "yesterday" vs "today" live in Rust (`src/native/pulse/`), next to `plan_budget` and `freshness`. bob-ledger-tools grows a `pulse` namespace that decodes the JSON and paints. Mac Capture stays out of it.

**CLI placement.** Top-level `bob pulse` in Daily workflow, alphabetically between `pomodoro` and `ready`. Bare `bob pulse` defaults to read-only `show` (CLI rule: a bare group may default only to a flag-only, read-only member). Help, JSON, and a short alias on every public long option.

```text
bob pulse                 Today's headline row + 14-day sparkline
bob pulse -m pomodoro_work_min -r 30d
bob pulse -f 2026-09-01 -t 2026-10-11
bob pulse catalog         List series (id, unit, kind, palette)
bob pulse latch           Write missing latched days (also nightly)
bob pulse log <id> <n>    Extra series (v1 slot, unused by defaults)
```

**Fence.** Sibling of `bob-plan`:

````markdown
```bob-pulse
metric: pomodoro_work_min
range: 30d
```
````

Empty fence → last-used (or default) metric and 30d. Chips rewrite the fence body so the view is git-visible, or hold session view state and only persist on an explicit pin. Prefer rewriting the fence: the note is then a real saved view, and Monday's prune can keep `range: 7d` without a hidden cookie.

**Catalog row (the extension point).**

```text
id:        pomodoro_work_min
label:     WORK
unit:      minutes          # minutes | count | flag | bps
kind:      derived          # derived | latched | extra
palette:   depth            # depth | pressure | flag
exclude:   [gtd_named]      # optional extractor flags
description: Closed ledger minutes whose session name is not GTD
```

Adding a series is one Rust extractor + one catalog row. `bob pulse catalog --json` is the plugin's schema. No new React, no new DataviewJS, no new community plugin.

**Latch document.**

```json
{
  "schema": 1,
  "days": {
    "2026-10-10": {
      "walk_answered": 41,
      "upkeep_today": 12,
      "budget_met": 0,
      "new_remaining": 0
    }
  }
}
```

Derived series are absent on purpose. Recomputing them from the vault is the reliability story: archive, sync, and a rebuilt laptop must not depend on a snapshot of numbers the Markdown still holds.

---

## 5. v1 metric catalog

Grouped the way the Pulse page is grouped. Headline row is Ritual + Output. Review is one click behind. Extra is a documented empty slot.

### Ritual

| id | Unit | Kind | Why |
| --- | --- | --- | --- |
| `gtd_pre` | count | derived | PRE chores completed. Flat 6 last week; a dip is a real miss. |
| `review_closed` | flag | derived | POST Morning review completed. Missed Oct 5 and Oct 7 last week. This is the habit. |
| `gtd_leads` | flag | derived | First timed ledger session that day is named GTD. True every day 10-05..10-11. The cutover research's "protect the first block" becomes a visible series. |

### Output

| id | Unit | Kind | Why |
| --- | --- | --- | --- |
| `pomodoro_work_min` | minutes | derived | Default time series. Closed `[t::]` excluding GTD-named sessions. |
| `pomodoro_min` | minutes | derived | Same as the daily heading query, over a range. |
| `pomodoro_sessions` | count | derived | Closed session count (8 / 10 / 7 / 15 / 8 / 7 last week). |
| `tasks_done` | count | derived | `#task` completions that day, minus GTD recurrence, `#ref`, daily `^gtd`. |
| `tasks_created` | count | derived | Same exclusions on `[created::]`. |
| `net_tasks` | count | derived | `tasks_created - tasks_done`. The weekly prune's question. Palette is pressure: positive net (backlog grew) trends yellow/red; negative net is green. |

### Review (not a goal)

| id | Unit | Kind | Why |
| --- | --- | --- | --- |
| `walk_answered` | count | latched | `refreshed_today` at latch. Diagnostic. |
| `upkeep_today` | count | latched | Already in freshness JSON. |
| `new_cleared` | flag | latched | `new == 0` at latch. The walk's actual commitment gate. |

### Optional in v1 if cheap

| id | Unit | Kind | Why |
| --- | --- | --- | --- |
| `first_pomodoro_min` | count | derived | Minutes from local midnight to the first timed session. The 2024 log tracked `time_of_1st_pomodoro`. Display as `HH:MM`. |
| `ref_done` / `ref_created` | count | derived | Reading-queue throughput, split out so it does not pollute Output. |
| `next_keep_bps` | bps | latched | Share of NEXT answers that were keep. The weekly prune's 90% clause. Only if the stamp path can increment a pair of counters without a second walk implementation. |

### Out of v1

- Meds, floss, rubber bands, miles, spend: those either already live as PRE tasks or were in the abandoned 2024 log on purpose.
- Mood / energy extras: the `pulse.extra` slot exists; do not invent a series Bryan did not ask for.
- Keep-streak as a daily integer: `[keeps:: N]` is per-task, not per-day.
- Mac menu-bar heatmap, capture-panel heatmap, tmux heatmap: Pulse is an Obsidian + CLI read view.
- A second daily note.

---

## 6. UX: intuitive, reliable, beautiful

### Pulse page

`pulse.md`, `parent: "[[dash]]"`, Browse row badge `PULSE` to the right of REFERENCES, informational accent (same family as PROJECTS / REFERENCES / BLOCKED: a collection, not a cap). Tooltip: `Open Pulse. Hours, created vs closed, review closeout.`

Layout, top to bottom, above the fold on a 14-inch frame:

1. **Metric chips** in three labeled groups (Ritual / Output / Review), `bob-plan` chrome, small-caps labels, tabular values for "today."
2. **Period chips** `7d 14d 30d 90d 1y` plus a from/to pair. Selected chip uses the metric's accent.
3. **Hero row** for the selected series: big tabular number, unit, delta vs the previous window of the same length (`+40m vs prior 30d`), and `N/D days` for flags.
4. **Contribution grid**: 7 rows (Mon–Sun, matching the daily-note weekday aliases), columns = weeks in the period. Cell size ~12px, 3px gap, 3px radius. Depth palette for achievement; pressure palette for net/backlog; two-state fill for flags. Missing day (no daily note and no events) is a hollow cell, which is distinct from a recorded zero.
5. **Sparkline** under the grid, same series, same window, 2px stroke, no fill, hover a day to highlight the matching cell.
6. **Quiet table** folded by default: date, value, vs period median. For people who want numbers.

Hover on a cell: `Fri, Oct 9 · 3h 10m · 20m above 30d median`, then a click opens that daily note. Keyboard: `h`/`l` period, `j`/`k` metric, Enter opens the day. Vimrc users should be able to drive this without a mouse.

Empty state: a 30-day hollow grid and one sentence, `No closed sessions in this window`, never a spinner that collapses the page.

### Daily note

Unchanged, with one optional later capsule on the `bob-plan` row: `PULSE ↗` that opens `pulse.md`. No sparkline on the daily note in v1. Today's number is already in the Pomodoro heading.

### CLI

Color, tabular numbers, Unicode sparkline (`▁▂▃▅▇`), the same groups. `NO_COLOR` and non-tty drop to plain text. JSON is the plugin contract.

```text
Pulse  2026-10-10  ·  14d

Ritual   PRE 6  ·  review ✓  ·  GTD first ✓
Output   2h 30m work   ▁▂▃▅▇▅▃▂▃▅▄▃▂▁   14d median 2h 55m
         done 18  created 26  net +8
Review   walk 41  ·  upkeep 12  ·  NEW cleared
```

### Visual language (do not invent a third one)

Reuse, in this order:

- Interface font, small-caps labels, tabular numbers, 2px accent start-border, 14% accent wash (`bob-plan` chips).
- Work-badge tones for pressure series, documented in `docs/dashboard.md`.
- A **depth** scale for achievement: grey (0), blue (below median), green (at/above median). Never red for "you worked a lot." Red on an achievement grid would teach the wrong lesson.
- Date-mark grammar for hover copy (`Fri, Oct 9 · 2 days ago`).
- Freshness-footer density: drop groups, then detail, then the meter as space runs out.

Theme-native in light and dark. No GitHub greens, no heatmap-calendar oranges, no sparkline library with its own tooltip chrome.

### Intuition

Three questions, three places:

| Question | Place |
| --- | --- |
| What am I doing *now*? | Capture idle agenda, `bob pomodoro`, ledger |
| What is due *this morning*? | `]s`, freshness footer, dash Review chips |
| How has *this week* gone? | Pulse |

If Pulse tries to answer the first two, it will be another dashboard. It answers only the third.

---

## 7. Reliability

- **One scanner.** Pulse extractors walk the native Tasks index and the daily-note ledger once per request (or once per nightly latch), the same engines as `bob query --tasks` and `bob plan`. No DataviewJS on `dash.md` (that file is already a compatibility thicket). No live Obsidian engine.
- **Exclusions are named and tested.** Conformance vectors for GTD recurrence, `#ref`, daily `^gtd`, `done/` archives, cancelled `[-]`, template/conflict paths, and Pomodoro lines that are not `#task`.
- **Latch is idempotent.** Re-running nightly overwrites a day only with a greater-or-equal snapshot taken the same local date, or with an explicit `--force`. A missing day is computed from `fresh == that date` *if* those stamps have not yet been overwritten; otherwise it stays missing (hollow cell), never a silent zero. Hollow vs zero is a reliability feature.
- **Today is live; history is derived + latched.** Opening Pulse at 16:00 shows today's live `gtd_pre` / closed minutes / created / done, and yesterday's latched walk counts. No 15-minute hook rewrite.
- **Headless.** `bob pulse -f json` works on Athena without Obsidian, matching `bob plan` and `bob freshness`.
- **Archive-safe.** Completions moved to `done/` remain in `tasks_done`. Tests must include an archived PRE row and an archived non-GTD `#task`.
- **Do not slow `]s`.** No extra vault write on stamp. Latch at POST closeout and nightly only.

---

## 8. Alternatives rejected

| Alternative | Why not |
| --- | --- |
| Community Tracker / Heatmap Calendar / Obsidian Charts | Third stack, foreign visual language, not in the curated plugin list. |
| More DataviewJS on `dash.md` | Dash already has a guarded inline fallback novel. Bob should own facts; the plugin should paint. |
| Daily `@HABIT` note, resurrected | Tried 2024-05-22..06-27; died. Duplicate of PRE/POST and the ledger. |
| Frontmatter copies of derived counts | The `#today` tag lesson. Drift, linter churn, false history. |
| SQLite / CSV sidecar outside the vault | Breaks `bob vault-sync` as the source of truth. |
| Counting every `]s` landing as "review completed" | Conflates chores, stamps, and closeout; Goodharts the walk. |
| Streak-first UX (Streaks, Don't Break the Chain) | One miss zeros a month. Loop's score and contribution grids exist because this fails. |
| Chart on every daily note | Second daily artifact; cannot show a range. |
| Mac Capture heatmap | Wrong surface (now-and-next, not history); thin-client rule still requires Bob JSON first. |
| Manual end-of-day form | Extra work. The cutover research's failure mode. |
| `bob query` stopgap as the product | It already runs; it is not beautiful, not exclusive, not period-interactive, and not a catalog. |

---

## 9. Literature and prior art (short)

- **Goodhart's law.** When a measure becomes a target, it ceases to be a good measure. Walk volume, raw completions, and streaks are the three easiest Pulse numbers to Goodhart. That is why `review_closed`, `pomodoro_work_min`, and `net_tasks` are the headlines, and why `#ref` swarm closeouts are excluded from done/created.
- **Contribution grid vs streaks.** GitHub's graph, and 2026 write-ups of the same pattern for habits, show trend rather than status. A miss is a pale cell. A streak counter is a status that lies after one sick day.
- **Loop Habit Tracker.** Score (an exponential strength that survives a few misses) plus a calendar, not a chain. Bob does not need Loop's score in v1; the grid plus `N/D days` plus median is enough. If a score appears later, it belongs on `review_closed` and `gtd_pre`, not on `walk_answered`.
- **James Clear / Atomic Habits.** Measurement is useful as feedback in a larger picture. Measuring hours of GTD tooling is how September lost the first block. Pulse must not become that tooling.

---

## 10. Implementation sketch (so a plan can start)

Phased so each slice is usable alone.

**Phase 1 — `bob pulse` derived catalog.** Rust module, CLI `show`/`catalog`, JSON, human sparkline. Series: `gtd_pre`, `review_closed`, `gtd_leads`, `pomodoro_min`, `pomodoro_work_min`, `pomodoro_sessions`, `tasks_done`, `tasks_created`, `net_tasks`. Docs in `docs/pulse.md`. Goldens from last week's real shape (PRE=6, POST misses on 10-05 and 10-07, Oct 6 GTD-heavy minutes, Oct 6 `#ref`/inbox spike excluded).

**Phase 2 — `pulse.md` + `bob-pulse` block.** bob-ledger-tools namespace `pulse` v1, contribution grid, period/metric chips, Dashboard Browse badge. Fence body is the view state. Click a cell → that daily note.

**Phase 3 — latch.** `_generated/bob-pulse.json`, `bob pulse latch`, nightly step, POST-closeout snapshot of `walk_answered` / `upkeep_today` / `new_cleared`. Hollow cells for days that were never latched.

**Phase 4 — extras only if still hungry.** `first_pomodoro_min`, `ref_*`, `next_keep_bps`, `pulse.extra.*` logging, a month-scoped fence on the monthly template. Not a reason to delay 1–3.

CLI rules checklist: `-h` excellent; options alphabetical; every long option has a short alias; colored output; `pulse` is a new noun with a membership rule ("read-only daily integer series and their latch"); no `bob task pulse` (it does not rewrite task lines).

---

## 11. Recommended solution

Build **Pulse**: a derived-first daily-integer catalog with a contribution-grid home on `pulse.md` and a matching `bob pulse` command.

v1 headlines: `review_closed`, `gtd_pre`, `gtd_leads`, `pomodoro_work_min`, `tasks_done`, `tasks_created`, `net_tasks`. v1 diagnostics, latched: `walk_answered`, `upkeep_today`, `new_cleared`. v1 storage: none for derived series; `_generated/bob-pulse.json` for latched series. v1 UX: `bob-pulse` fence, period chips, depth/pressure palettes borrowed from chips that already exist, no streak as the big number, no new daily note, no new community plugin, no extra gesture during the walk.

The original request, restated after the adjustments above: *I want to see how a handful of daily integers have moved over a window I can change, without creating a second practice, and I want adding the next integer to be a catalog row.* That is a good idea. The 2024 habit log was the other idea. Do not do that one again.
