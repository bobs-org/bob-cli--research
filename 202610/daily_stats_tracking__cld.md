# Daily stats for Bob: research, critique, and a recommended design

Researcher: `cld` (swarm member). Date: 2026-10-11. Scope: bob-cli, bob-plugins,
the Bob vault, and external research on personal tracking. Read-only; nothing in
any repo or the vault was changed.

---

## 0. TL;DR

- **Yes, build it, but derive the numbers; don't log them.** You already ran a
  manual habit log in zorg (Oct 2023 → Feb 2026). It decayed into
  `Skipping habit tracking until …` entries and died. All four metrics you listed
  can be computed from data the vault already writes, so v1 should need **zero
  daily entry**.
- **One metric breaks that rule: the `]s` review count.** Review answers leave no
  lasting trace. A `[fresh::]` stamp is overwritten at the next review. Already
  **14–30 % of each day's stamps from Oct 7–10 have been erased**. The plugins
  persist no walk history at all. Count this metric with a tiny append-only
  **review journal** written at the moment a walk answer resolves a row.
- **Architecture:** one Rust metric registry in bob-cli (`bob stats`). Metrics
  are **derived at read time** wherever the vault is durable, and **recorded**
  (per-host append-only JSONL under `.bob/stats/`) only where the vault forgets.
  Two thin renderers sit on the same JSON contract: a terminal view, and an
  Obsidian `bob-stats` code block on a new `stats.md` note.
- **Adding a metric later:** a few lines of `stats:` config, built from a small
  set of metric *kinds*. These cover Pomodoro time, task events, checklist
  habits, daily-note fields, and formulas. A derived metric arrives **with its
  full history already filled in**.
- **I changed some requirements; each change is called out in §4.** Count
  review *decisions*, not chores. Add Dropped and Net flow. Turn your existing
  `#gtd #pre` chores into the habit grid. Add Review time and Keep rate as
  companions to the review count. No streaks. Treat today as partial. Store
  numbers with types and units, not just "one integer".
- **The data already tells a story:**
  - **Sep 14 – Oct 2:** your open-task backlog grew about **+8.6 tasks a day**
    (257 created vs 93 closed).
  - **Oct 3 – Oct 10:** net flow was **−214**, after the tiered walk landed
    (this includes bulk triage and reference closes).
  - **Oct 4 – 10:** GTD-named Pomodoros took **49 %** of worked minutes, falling
    to 24 % over Oct 8–10.

  Nothing in the vault shows you any of this today. That is the case for the
  feature.

---

## 1. Evidence base

| Source | What I checked |
| --- | --- |
| Vault (`~/bob`) | Daily template and recent daily notes, `gtd_daily.md`, `done/`, zorg-era `_habit`/`_poms`/`_done` files, `.gitignore` allowlist, `.bob/`, Tasks plugin settings, git history (4,580 commits since 2026-05-30) |
| bob-cli | `README.md`, `docs/freshness.md` §§5–8, `docs/dashboard.md`, `docs/dataview.md`, `docs/vault-git-sync.md`, `src/native/{nightly,pomodoro,style}.rs`, `src/native/{freshness,dataview,config}/`, live timings |
| bob-plugins (read-only via `sase repo open`) | Review walk, `api.freshness`, code-block processors, write patterns, persistence (summary in §3.5) |
| SASE memory | Glossary; decisions `review-walk-is-tiered`, `answering-advances-the-walk`, `task-lanes-are-sticky`, `today-is-read-from-the-ledger`, `ready-is-freshness-gated`, `mac-capture-is-a-thin-client`, `idle-capture-shows-ledger-agenda`; `cli_rules.md`; `obsidian.md` |
| External | Obsidian tracking plugins, quantified-self tools, self-monitoring research, visualization guidance, storage formats (§3.6, with URLs) |

All vault numbers below came from read-only scans: Python with `-I`, plus
`git log -p`. Day boundaries are local calendar dates.

---

## 2. Is this a good idea? (critique)

### 2.1 Why it is a good idea

1. **You already do it by hand.** The weekly prune checklist says *"check hours
   and created vs closed"* (`gtd_daily.md`, `#gtd #post Weekly prune`). That is
   this feature, done by eye, once a week.
2. **Your own decisions have numeric reopen triggers that nothing measures.**
   - *review-walk-is-tiered*: "the lane keep rate stays above 90 %", "PRE rows
     are skipped with `]s` on most mornings", and "`]S` pressed at the boundary
     with zero ROTTEN done on most mornings".
   - *answering-advances-the-walk*: "`<C-o>` after an answer becomes routine".
   - *task-lanes-are-sticky*: "about 2–3 tasks a day of lane growth".
   - The weekly prune: "if more than about 90 % of NEXT reviews end in keep,
     lengthen `next_interval`".

   Every one of these is a daily number nobody can see today. This is not
   vanity tracking. It is **instrumentation for a system you actively tune**,
   and it lets those decisions reopen on evidence rather than on feel.
3. **The marginal cost is near zero.** The Tasks plugin already auto-stamps
   `created`, `completion`, and `cancelled` (`setCreatedDate`, `setDoneDate`,
   `setCancelledDate` are all `true`). Pomodoros already carry `[t:: Nm]`. Only
   the review count needs a new writer.
4. **The research supports it, with conditions.** Monitoring goal progress
   improves attainment, with a moderate effect: d+ = 0.40 across 138 RCTs. The
   effect is larger when progress is *physically recorded* and reported
   (Harkin et al. 2016). Abandonment is the norm when tracking costs effort:
   about 70 % of app users stop within 100 days (Kidman et al., JMIR 2024).
   Epstein et al.'s *lived informatics* names forgetting and upkeep burden as
   the top lapse causes. Automatic capture removes both.

### 2.2 Where it could go wrong

| Risk | Evidence | Mitigation in this design |
| --- | --- | --- |
| **Manual entry decays** | Your zorg habit log ran Oct 2023 → Feb 2026 (≈ 826 daily files). "Skipping" days appeared from Nov 2024 (2/30), grew (Apr–May 2025: 10–11 per month; Nov–Dec 2025: 10–12 per month), and every day of Jan–Feb 2026 says *Skipping*. The log has not existed since 2026-02-22. | v1 has no manual metrics. A `field` kind exists for later opt-in. |
| **Goodhart / gaming** | "Reviewed" invites rubber-stamping, which *review-walk-is-tiered* already lists as a cost. "Done" invites splitting tasks. | Pair every output metric with a counterweight: Reviewed with Keep rate and Review time; Done with Created and Net flow. No targets on counts by default. |
| **Streak anxiety** | Broken streaks reduce later engagement (Silverman & Barasch, JCR 2023). After GitHub removed its streak counter, long streaks were abandoned and token single-commit days fell (Moldon et al. 2020). | No streak counters. Optional goals are shown as **"days met in window"**, a rate that recovers after a bad week. |
| **Yet another dashboard** | You already have `dash.md`, `rotten.md`, `crowded.md`, the review footer, `bob plan`, and `bob ready`. | Put stats where you already look: the weekly prune (link it), `bob stats` in the terminal, and one `stats.md` page. Don't add a footer item. |
| **Noisy days** | Oct 6: 87 done and 47 dropped (bulk triage plus reference closes). Oct 3: 49 done. Imported tasks carry back-dated completions (Aug 20 shows 17 completions now, but git recorded none that day). | Rolling **median** overlays, breakdowns by kind and note, and "today is partial" handling. |
| **Overbuilding** | A generic metrics platform before you know which metrics matter. | Ship ~8 built-ins plus a tiny kind system. Built-ins use the same config path as user metrics, so extensibility costs almost nothing extra. Phase 1 is a CLI only. |

### 2.3 Would I take a different approach?

I considered six approaches:

| Approach | Verdict | Why |
| --- | --- | --- |
| A. Frontmatter on each daily note + Obsidian Tracker or Heatmap plugin | ✗ | Tracker has had essentially no maintenance since early 2024. Automated writes into notes you are editing add churn and sync risk. The review count still needs a writer. It is JS-only, so it can't feed the CLI. |
| B. DataviewJS dashboard computing everything live | ✗ | A second implementation of every definition. Dataview has to re-scan about 3.5 k tasks × 365 days on render. No review data. No CLI. |
| C. Bases table over daily-note properties | Later, as a view | Bases has summaries (sum/avg/median) but **no native chart view** through Obsidian 1.14.4. It also still needs a property written per daily note. |
| D. External tool (Exist.io, Grafana, SQLite + Datasette) | ✗ | Data leaves the vault. A new service to run. It doesn't fit your workflow. |
| E. Nightly snapshot of *every* metric into a ledger | ✗ as the only mechanism | New metrics start with no history. A missed nightly loses a day. A wrong definition gets frozen into history. |
| **F. Hybrid: derive what the vault keeps, record only what it forgets; one Rust engine; thin renderers** | **✓ Recommended** | One definition per metric. History comes for free. Only one small writer. It matches the established "bob owns every fact" stance (*mac-capture-is-a-thin-client*, *idle-capture-shows-ledger-agenda*). |

A valid cheaper fallback if you want to test the idea first: ship only Phase 1
(`bob stats` in the terminal, derived metrics) and use it in two weekly prunes
before you build the journal or the Obsidian view.

---

## 3. What the vault already knows (data audit)

### 3.1 Metric sources and how long they last

| Metric | Source of truth | Durable? | History available today |
| --- | --- | --- | --- |
| Pomodoro time | Closed `- [x] (**HHMM-HHMM** [t:: Nm])` lines under `## Pomodoros` in `YYYY/YYYYMMDD.md` | ✅ permanent ledger | Daily notes from **2026-06** (≈ 118–159 h per month). The zorg `_poms` format (`p::N/M`, N × 5 min) goes back to **2025-10**, adapter optional. |
| Tasks done / dropped | `[completion::]` / `[cancelled::]` on `#task` lines; `bob task archive` moves them into `done/` with the fields intact | ✅ (reopen removes a completion, which is correct) | Since vault adoption (2026-05-30). Older back-dated dates came from imports. |
| Tasks created | `[created::]` (Tasks `setCreatedDate: true`; capture and gkeep write it too) | ✅ mostly; deleted lines vanish | 2,851 of 3,497 `#task` lines carry it. Only **22 open** tasks lack it. Most gaps are generated `^ref` tasks and old done items. |
| PRE habits / review closed | Recurring `#gtd #pre` / `#gtd #post` instances in `gtd_daily.md` plus `done/gtd_daily_done.md`, each with `completion` | ✅ | Since 2026-10-04: 6 PRE rows a day, and POST closed same-day on Oct 6, 8, 9, 10. |
| Review answers (`]s`) | **Nothing durable.** `[fresh::]` keeps only the latest date. Walk state lives in plugin memory. | ❌ | Partly recoverable from vault git history, approximately. |
| Review time | Closed Pomodoros named `— GTD` | ✅ | Same as Pomodoro time. |

### 3.2 The decisive finding: review stamps evaporate

The table compares tasks still carrying `[fresh:: D]` now with distinct task
lines that gained `[fresh:: D]` in that day's vault-sync commits. The second
number is an approximation: normalized text, and edits can double-count.

| Day | Still stamped today | Stamped that day (git) | Already lost |
| --- | --- | --- | --- |
| 2026-10-07 | 33 | 47 | 30 % |
| 2026-10-08 | 62 | 72 | 14 % |
| 2026-10-09 | 41 | 51 | 20 % |
| 2026-10-10 | 56 | 65 | 14 % |

Lanes are reviewed daily (`pending_interval`/`next_interval` = 1), so a stamp
lasts about a day. **Any read-time "reviewed" metric is wrong within 24 hours.**
A stamp count is also the wrong concept:

- It counts daytime stamps such as Ctrl+Shift+Enter links and Alt+N commits.
- It misses answers that don't stamp: Ctrl+Enter closes, the Drop/cancel row,
  checklist completions.

The review count has to be recorded at the moment of the answer.

### 3.3 What the numbers already show (non-recurring tasks)

| Window | Created | Done | Dropped | Net flow |
| --- | --- | --- | --- | --- |
| Sep 14 – Oct 2 (19 d) | 257 | 63 | 30 | **+164 (+8.6/day)** |
| Oct 3 – Oct 10 (8 d) | 163 | 277 | 100 | **−214 (−26.8/day)** |

A git cross-check confirms September's low completion counts are real, not
missing data: Sep 15 has 2 now and 2 in git; Sep 23 has 10 and 10. The October
burst is the tiered walk plus bulk triage, with some reference and
`ref/chat/*` closes mixed in. That mix is why breakdowns by kind matter.

Worked time and GTD share over the same week:

| Day | Worked | GTD minutes | PRE done | POST closed same day |
| --- | --- | --- | --- | --- |
| 10-04 | 300 | 250 | 6 | – |
| 10-05 | 175 | 75 | 6 | – |
| 10-06 | 300 | 215 | 6 | ✓ |
| 10-07 | 250 | 175 | 6 | – (closed 10-08) |
| 10-08 | 375 | 65 | 6 | ✓ |
| 10-09 | 260 | 50 | 6 | ✓ |
| 10-10 | 250 | 100 | 6 | ✓ |

The morning ritual cost **930 of 1,910 worked minutes (49 %)** in its first
week, trending down to about 24 % by Oct 8–10. That is exactly the cost-side
number a "Reviewed" count needs beside it.

### 3.4 Performance constraints

Measured on apollo, a 16-core machine:

| Operation | Wall time | Notes |
| --- | --- | --- |
| `bob query --tasks 'done after …'` | **6.5–7.1 s, ~1.5 GB RSS** | Every run. Far too heavy to evaluate per metric. |
| `bob freshness list -f json` | 1.6 s | |
| `bob ready` | 1.7 s | |
| `bob plan` | 0.7 s | |
| One-pass Python scan of all 6,234 `.md` files computing every v1 metric | **0.47 s** | A Rust single pass should land well under that. |

So the stats engine needs its **own single-pass index** over task lines plus
daily-note Pomodoro sections. It must not go through the Tasks query engine.
User-defined filters should be simple fields (tags, residence, kind,
recurring), not the full Tasks DSL, until that engine can evaluate over a
shared index.

### 3.5 What bob-plugins has (and lacks)

From a read-only sweep. Paths are relative to `plugins/` in bob-plugins.

- **No persistence anywhere.** Zero `saveData`/`loadData`/`localStorage`/log
  writes. Walk state (`reviewLanding`, `reviewAnsweredKeys = {day, keys, texts}`)
  is in memory and resets on reload
  (`bob-navigation-hotkeys/src/490-plugin-lifecycle.js:327-336`).
- **Choke points where a resolved answer is known:**
  - `continueReviewWalkAfter(origin, outcome)` →
    `reviewOutcomeResolves(tier, outcome, today)` → `addReviewAnsweredKeys`
    (`536-plugin-review-advance.js:340`, `538-review-walk-identity.js:64`).
    Outcome kinds here: `complete`, `lane`, `route`, `link-today`, `card`. A
    `card` carries only before/after lines, and the resolver at 538:84-143
    already infers closed / deferred / dependency / stamped.
  - `finishFreshStamp` → `jumpToDueTask({fromAdvance})` for Alt+F /
    Ctrl+Alt+F (`530-…:228`, `520-…:621,749`).
  - `completeReviewChecklistRow` for PRE/POST rows (`535-…:181,264`).
  - `maybeAdvanceFreshnessDecayWalk(cardCtx, action)` for decision-card actions
    `notNow|level:N|lessOften|reword|drop|keep` (`530-…:705`).
  - `parkReviewWalkAfterMove` for Ctrl+Shift+M (`537-…:199`).
  - Skips (`]s` without answering) emit nothing.
- **Rendering precedent:** only two code-block processors exist, `bob-plan` and
  `bob-ready-notes`, both pure DOM with theme-variable CSS and `color-mix()`.
  There are **no charts, sparklines, SVG charts, or chart libraries**. The root
  `package.json` has no dependencies.
- **No plugin spawns `bob`** (no `child_process`). Facts are mirrored in JS
  under conformance vectors, which is the "two evaluators" cost the freshness
  decisions keep paying.
- **Day rollover:** a 60 s `registerInterval` tick plus the Tasks
  `cache-update` event (`bob-ledger-tools/src/170-…:488-546`).

### 3.6 External research (selected)

- **Obsidian tracking plugins are fragile.**
  - Tracker: last push 2024-03, 211 open issues
    ([obsidianstats](https://www.obsidianstats.com/plugins/obsidian-tracker),
    [forum "gone stale"](https://forum.obsidian.md/t/obsidian-tracker-has-gone-stale/67668)).
  - Charts and Heatmap Calendar: about 2 years without releases. Heatmap
    Tracker is the maintained successor.
  - Bases (1.10+) has summaries but no native charts
    ([syntax](https://obsidian.md/help/bases/syntax),
    [1.14.4 changelog](https://obsidian.md/changelog/2026-10-01-desktop-v1.14.4/)).
- **Exist.io's model fits well:** one value per attribute per day, typed
  values (int, minutes, scale, bool, percent), explicit `null` for missing
  days, a `manual` flag, and weekday averages
  ([object types](https://developer.exist.io/reference/object_types/),
  [averages](https://developer.exist.io/reference/averages/)).
- **Goals as pace and buffer:**
  - Beeminder shows a pace line and days of buffer; making a goal easier takes
    a one-week delay ([glossary](https://blog.beeminder.com/glossary/)).
  - Apple added ring pauses without breaking streaks and compares 90-day with
    365-day trends
    ([watchOS 11](https://apple.com/newsroom/2024/06/watchos-11-brings-powerful-health-and-fitness-insights)).
  - Toggl supports "at most" goals ([support](https://support.toggl.com/time-tracking-goals)).
- **Self-monitoring and lapses:**
  - Harkin et al. 2016 ([eprint](https://eprints.whiterose.ac.uk/91437/)).
  - Epstein et al. 2015, *lived informatics*: design for lapse and resumption,
    and offer a "clean slate"
    ([PDF](https://my.eng.utah.edu/~cs5540/au16/readings/PersonalInformatics-Epstein2015.pdf)).
  - Choe et al. 2014: "tracking too many things" is the top pitfall
    ([MSR](https://www.microsoft.com/en-us/research/publication/understanding-quantified-selfers-practices-collecting-exploring-personal-data/)).
  - Semi-automated tracking balances effort against awareness
    ([Choe 2017](https://library.selfresearch.org/research/semi-automated-tracking-a-balanced-approach-for-self-monitoring-applications/)).
- **Lead vs lag measures** (4DX, Newport's deep-work tally): show controllable
  inputs beside outcomes ([LeadX](https://leadx.org/?p=9275)).
- **Visualization:**
  - Tufte sparklines: label the last value, use a gray normal-range band
    ([Tufte](https://www.edwardtufte.com/notebook/sparkline-theory-and-practice-edward-tufte/)).
  - Position beats color for comparing magnitudes, so heatmaps are for
    spotting days, not comparing them
    ([FlowingData](https://flowingdata.com/2010/03/20/graphical-perception-learn-the-fundamentals-first)).
  - A rolling median resists spikes
    ([SAS](https://blogs.sas.com/content/iml/2021/05/26/running-median-smoother.html)).
  - Terminal block sparklines give 8 levels
    ([spark](https://linuxcommandlibrary.com/man/spark)). ratatui distinguishes
    missing from zero values (`absent_value_symbol`,
    [v0.29](https://ratatui.rs/highlights/v029/)).
- **Storage:**
  - JSONL appends diff as one line ([jsonlines.org](https://jsonlines.org/)).
  - Long, tidy `(date, metric, value)` rows make a new metric new rows instead
    of a new column ([Wickham 2014](https://jstatsoft.org/article/view/v059i10)).
  - Snapshot only what can't be recomputed (DDIA Part III;
    [Willison, git scraping](https://simonwillison.net/2020/Oct/9/git-scraping/)).

---

## 4. Requirement adjustments (called out explicitly)

| # | Your requirement | Adjustment | Why |
| --- | --- | --- | --- |
| **R1** | Each stat is a single integer per day | **One number per day with a type and unit:** count, minutes, ratio/percent, bool. Plus optional **parts** (breakdowns such as tier, outcome, Pomodoro theme, note). Missing is `null`, never 0. | Keep rate and habit completion are ratios, and review-closed is a bool. Breakdowns answer "why was Tuesday low?". The vault's existing rule is that an unavailable count shows `–` and is never zero (`docs/dashboard.md`). |
| **R2** | "Morning GTD review tasks I completed by iterating with `]s`" | Define **Reviewed** = distinct walk rows resolved by a walk answer that day, **in the decision tiers between PRE and POST**. Alt+F counts (it resolves the row without advancing); skips and moves don't count. PRE/POST rows go to the Habits and Review-closed metrics. | Counting ~6–7 constant chores a day would flatten the signal. A stamp count is wrong both ways (§3.2). |
| **R3** | Pomodoro hours and minutes | Store **minutes**, display `Hh Mm`. Name it **Worked** 🍅. It must equal the daily note's `## Pomodoros (…)` heading total (closed `[x]` Pomodoros' `t`). Add a **theme breakdown** (`— NAME`). | One truth with what you already see. Themes reveal where the time goes (GTD cost, §3.3). |
| **R4** | Tasks completed | **Done** = non-recurring `[x]` tasks with `completion` = D. Add **Dropped** (`[-]`, `cancelled` = D) as its own metric. Recurring instances are excluded and handled as Habits. | Triage that drops tasks is real GTD output (Oct 6: 47 drops). Recurring chores add 6–10 a day of noise. |
| **R5** | Tasks created | **Created** = non-recurring `#task` lines with `created` = D, shown as **neutral** (neither up nor down is "good"). Add **Net flow** = Created − Done − Dropped, where down is good. | Capturing is healthy and shouldn't be a target. Net flow is the number the weekly prune and *task-lanes-are-sticky* actually ask about. |
| **R6** | (implicit) Track habits | Use your **existing recurring `#gtd #pre` chores** as the habit grid: pills, teeth, email, calendar, weather, Keep import. | They already replaced the zorg log's `meds` and `teeth` rows, and the data is already there. |
| **R7** | (new) | **Review time** (GTD-theme minutes) and **Keep rate** (share of PENDING/NEXT answers that were keeps) ship as companions to Reviewed. | Counterweights against rubber-stamping. They also make three decision reopen triggers measurable. |
| **R8** | Visualize over an adjustable period | Default to **4 weeks**, which balances weekdays. Presets 7D / 4W / 3M / 1Y / All plus a custom `A..B`. Always compare with the **prior period of the same length**. Today is **partial**: drawn hollow and excluded from medians and deltas. | Prevents a "slump" every morning. Supports a clean slate after a lapse (Epstein). |
| **R9** | (new) | **No streak counters.** Optional goals render as a reference line and as "N of M days met". | Streak research (§2.2). |
| **R10** | (new) | Make stats part of the **weekly** ritual (the prune), not a daily scoreboard. | Avoids Goodhart pressure on daily counts. Matches where you already "check hours and created vs closed". |

---

## 5. The v1 metric catalog

### 5.1 Core (shown in the overview)

| ID | Label | Unit | Good direction | Kind | Definition | History on day 1 |
| --- | --- | --- | --- | --- | --- | --- |
| `worked` | 🍅 Worked | minutes | ↑ | pomodoro | Σ `t` of closed `[x]` Pomodoros in the day's note; parts by theme | 2026-06 → (2025-10 → with the zorg adapter) |
| `reviewed` | ⟳ Reviewed | count | ↑ (context) | journal | Distinct walk rows resolved in decision tiers; parts by tier and outcome | From ship date. Optional approximate git backfill from 2026-10-04. |
| `done` | ✓ Done | count | ↑ | tasks | Non-recurring `[x]` with `completion` = D; parts by kind (task/prj/ref) and note | 2026-05-30 → |
| `created` | ＋ Created | count | neutral | tasks | Non-recurring `#task` with `created` = D; parts by inbox vs. elsewhere | 2026-05-30 → |
| `net` | ⇅ Net flow | count | ↓ | formula | `created − done − dropped` | Same as its inputs |
| `habits` | ◉ Habits | ratio | ↑ | checklist | PRE chores completed ÷ PRE chores due on D; per-chore 0/1 grid | 2026-10-04 → |

### 5.2 Secondary (in `bob stats metrics`, detail views, and the Obsidian page)

| ID | Label | Unit | Kind | Definition |
| --- | --- | --- | --- | --- |
| `dropped` | ✕ Dropped | count | tasks | Non-recurring `[-]` with `cancelled` = D |
| `review_time` | Review time | minutes | pomodoro | `worked` restricted to theme `GTD` (configurable) |
| `keep_rate` | Keep rate | percent | journal | Keeps ÷ all answers in PENDING + NEXT, from the last answer per row per day |
| `review_closed` | Review closed | bool | checklist | `#gtd #post` *Morning review* completed on D |
| `open` | Open backlog | count | tasks (reconstructed) | Non-recurring tasks with `created ≤ D` and not closed by end of D. Approximate for deleted tasks and tasks without `created`. |
| `poms` | Pomodoros | count | pomodoro | Closed Pomodoros on D |

### 5.3 Considered for later (not v1)

| Candidate | Why later |
| --- | --- |
| Day start / end (first and last Pomodoro time) | Cheap to derive (you started between 05:15 and 09:55 over the past two weeks), but it is a sleep-schedule question. Add it when you want it, as a single config entry. |
| Plan follow-through (planned Task Links that were worked or completed) | Derivable, about 50–75 % lately, but open placeholder Pomodoros are a *lineup*, not a commitment. A naive definition punishes healthy over-planning. Needs a careful definition first. |
| Lane sizes at end of day (NEXT, PENDING, NEW, ROTTEN) and walk due at start | Needs the `snapshot` kind (Phase 4), because they are point-in-time states. The weekly prune caps (≤15 NEXT, ≤10 PENDING) make these attractive. |
| Manual metrics (sleep, weight, mood, exercise) | The zorg log showed manual entry dies. Supported through the `field` kind when *you* choose to write `weight:: 181` in a daily note. Never prompted. |

### 5.4 Rejected

| Candidate | Why rejected |
| --- | --- |
| "Stamps today" | Wrong in both directions (§3.2). |
| Commits, words, or lines written | Vanity metrics with no decision attached. |
| Streak counts | §2.2. |
| Time in Obsidian | Needs telemetry. Nothing acts on it. |

---

## 6. Architecture

### 6.1 Principle

> **Derive what the vault keeps; record only what the vault forgets; define
> every metric once, in bob.**

- **Derived metrics** (pomodoro, tasks, checklist, field, formula) are pure
  functions of the current vault. They are never stored, they are always
  consistent with the vault, and they arrive with full history. Fixing a
  definition fixes all of history consistently.
- **Recorded metrics** (journal, snapshot) are append-only facts written at
  the moment they happen. They have a `since` date, and before it they are
  `null`.

### 6.2 Engine: `src/native/stats/` in bob-cli

The engine has four layers:

- **Index** — one pass over the vault, the same exclusions as freshness
  (`_templates`, `_conflicts`, dot-directories). It produces:
  - Task events: `created` / `done` / `dropped`, plus kind, recurring flag,
    tags, residence note, and parent chain.
  - Daily-note Pomodoros: date, `t`, theme `NAME`, closed flag. This reuses
    `pomodoro.rs`: `pomodoros_section_range`, `completed_ledger_task`,
    `task_time_range`, `parse_day_file_date`.
  - Daily-note fields (frontmatter and inline `key:: value`), for the `field`
    kind.
  - Recurring `#gtd` instances (scheduled date and completion).
- **Recorded inputs** — `.bob/stats/journal/*.jsonl` and, later,
  `.bob/stats/snapshots/*.jsonl`. Every host file is merged.
- **Registry** — built-in definitions plus `stats:` config. Built-ins are
  expressed *as config entries in code*, so the config path is exercised by
  every built-in (dogfooding).
- **Series** — `Vec<(date, value | null, parts, partial)>` per metric, plus a
  summary (total, median, mean, p25/p75, prior-period median, delta, days with
  data, goal days met).

Each metric definition has these fields:

```text
id · label · glyph · unit (count|minutes|ratio|percent|bool) · direction (up|down|neutral)
kind · kind params · aggregate over buckets (sum|mean|median|last|rate) · since · version
```

`version` matters when a definition changes. The JSON reports it, so a
renderer can annotate "definition changed on …" if you ever change one.

### 6.3 Metric kinds (v1)

| Kind | Params | Notes |
| --- | --- | --- |
| `pomodoro` | `measure: minutes\|count`, `themes: [..]`, `exclude_themes` | Closed Pomodoros only, matching the heading inline query. Optional `legacy_zorg: true` adapter for `_poms` (`p::N` × 5 min). |
| `tasks` | `event: created\|done\|dropped\|closed`, `tags_any`, `tags_all`, `in: [note]` (residence, including notes whose `parent` chain reaches it), `kind: task\|prj\|ref`, `recurring: exclude\|only\|include` (default `exclude`) | Simple fields only. No Tasks DSL in v1 (§3.4). |
| `checklist` | `tags: ["#gtd","#pre"]` or `match: "Brush teeth"`, `measure: ratio\|count\|bool` | Due = instances scheduled on D. Done = completed on D. |
| `field` | `field: weight`, `source: frontmatter\|inline\|either` | Reads the day's note only. Opt-in manual metrics. |
| `formula` | `expr: "created - done - dropped"` | `+ − × ÷` and parentheses over other metric IDs. Null if any input is null. |
| `journal` | built-in event selectors | For `reviewed` and `keep_rate`. Not user-extensible in v1. |
| `snapshot` (Phase 4) | `source: freshness.counts.new`, etc. | Point-in-time values recorded daily. |

### 6.4 How you add a metric later

There are three paths, from most to least common.

**1. Config only.** No code change, and full history arrives at once:

```yaml
# ~/.config/bob/config.yml
stats:
  range: 4w
  overview: [worked, reviewed, done, created, net, habits]
  goals:
    worked: { min: 4h }          # drawn as a line; reported as "18 of 28 days"
  metrics:
    sase_worked:
      label: SASE time
      kind: pomodoro
      themes: [SASE]
    job_done:
      label: Job tasks done
      kind: tasks
      event: done
      in: [job]
    floss:
      label: Floss
      kind: checklist
      match: "Floss teeth"
      measure: bool
    close_ratio:
      label: Close ratio
      kind: formula
      expr: (done + dropped) / created
      unit: ratio
```

**2. A new kind.** A small agent-sized PR: implement one collector over the
shared index, add a golden fixture, and document it in `docs/stats.md`.

**3. A new recorded fact.** Needs a writer: a journal event in a plugin, or a
snapshot field. These are the only metrics without retroactive history, so
`bob stats metrics` shows their `since` date.

`bob stats metrics` lists every metric with its definition, source, `since`
date, and whether it is derived or recorded. That keeps the registry
self-documenting.

### 6.5 The review journal (the one new writer)

**Where:** `.bob/stats/journal/YYYY-MM.<host>.jsonl` inside the vault.

- **Per host:** each machine appends only to its own file, so git merges never
  conflict. It is a grow-only set, and readers union all hosts.
- **Monthly files** keep the file count low: roughly 10 kB a day, about 4 MB a
  year.
- **Git tracking:** add `!/.bob/stats/**/*.jsonl` to the vault `.gitignore`
  allowlist. This follows the `.bob/gkeep/imports/*.json` precedent
  (`docs/vault-git-sync.md`). Obsidian hides dot-directories, so nothing
  clutters the file explorer.

**Event (schema v1):**

```json
{"v":1,"ts":"2026-10-12T05:41:07-04:00","day":"2026-10-12","host":"kellys-mbp",
 "kind":"review.answer","tier":"next","outcome":"keep","key":"sase.md#^fix-failed-agents"}
```

- **`outcome` values:** `keep · done · drop · defer` (priority or schedule
  roll) `· sequence` (dependency) `· today` (link) `· commit · release · route ·
  reword · less_often · checklist`.
- **`key`:** the walk's row key (path plus block ID, or path plus normalized
  text).
- **Optional:** a `review.start` event `{walk_due}` on the first landing of the
  day, which gives a denominator: "answered 41 of 71 due".

**Who writes it:**

- **bob-navigation-hotkeys** emits at the choke points in §3.5 through one
  helper, for example `recordReviewAnswer(origin, outcome)`. Reuse the existing
  `card` before/after classification rather than inventing a new one.
- **bob-ledger-tools** owns the writer as `api.stats.append(event)` (new
  namespace v1):
  - a serialized append queue using `vault.adapter.append`;
  - the hostname from `os.hostname()`, as plugins already optionally require
    Node `os`;
  - a visible Notice on failure, so a broken journal never fails silently.

**Reading semantics:**

- `reviewed(D)` = |distinct `key` with a resolving answer on `day` = D|. This is
  robust to double presses, reloads, and two machines.
- `keep_rate` uses the *last* answer per key per day.

**Gap detection:** if `review_closed(D)` is true but the journal has no events
for D, `bob stats` reports `reviewed` as `null` with a warning ("journal
missing for 2026-10-12 — plugin outdated or write failed"). It never reports 0.

**Backfill (optional):** `bob stats backfill reviewed --from-git` can estimate
2026-10-04 → ship date from vault history: distinct tasks stamped per day,
plus walk-eligible closes. Values are marked `approx: true` and drawn hatched.

### 6.6 Days, partial days, and missing data

- **A day is a local calendar date** (honoring `BOB_NOW`).
  - Pomodoros belong to their daily note's date.
  - Task events use their own date fields.
  - Journal events carry the walk's `day`.
- **Today is `partial: true`.** It is drawn hollow and excluded from medians,
  deltas, and goal rates.
- **Null vs zero.** A day before a metric's `since`, a day without a daily note
  (for `worked`), or a journal gap is `null`. A tracked day with nothing
  happening is `0`.

### 6.7 Commands (following `cli_rules.md`)

`bob stats` is a read-only report, so it stays top-level and goes in the
*Daily workflow* help section, sorted alphabetically.

```text
bob stats [-b DIR] [-c|--compare] [-f|--format human|json|csv] [-g|--group day|week|month] [-r|--range 4w]
bob stats show <METRIC>... [-b DIR] [-f …] [-g …] [-r …]
bob stats metrics [-b DIR] [-f human|json]
bob stats record [-b DIR] [-d|--dry-run]                          # Phase 4 (nightly)
bob stats backfill <METRIC> [-G|--from-git] [-d|--dry-run]       # optional, hidden
```

- Bare `bob stats` is the flag-only, read-only overview, which `cli_rules.md`
  allows.
- `--range` accepts `7d|4w|90d|1y|all|YYYY-MM-DD..YYYY-MM-DD`.
- When `--group` is omitted it is chosen automatically: day up to 90 days,
  week up to a year, month beyond that.
- JSON is `schema_version: 1`. It contains `date`, `range`, a `metrics[]`
  array (each with definition, `series[]`, and `summary`), source health (last
  journal event per host), and `warnings`.

---

## 7. UX design

### 7.1 Terminal: `bob stats` (the glance)

Mockup values are illustrative, loosely based on the §3.3 data. The Reviewed
row assumes the journal ships on Oct 12.

```text
bob stats · Sun 2026-10-11 · 4 weeks · Sep 13 – Oct 10 · vs Aug 16 – Sep 12

                 Sep 13 ─────────────────── Oct 10   yesterday   median/day   vs prior
  🍅 Worked      ▅▆▃▇▆▅▂▄▆▇▅▆▄▃▅▇█▅▄▆▅▆▃▅▆▄▅▄         4h 10m      4h 50m     ▲ 6 %
  ⟳ Reviewed     ······················▆▇▅▆▇▅          41          44         since Oct 12
  ✓ Done         ▁▁▂▁▁▁▃▁▁▂▁▂▁▁▂▁▁▁▃▂▄▁█▃█▃▄▅         38          3          ▲ 9×
  ＋ Created     ▃▄▃▅▃▂▃▄▃▂▄▃▃▃▂▃▄▄▃▄▃▄▅▃▄▅▅▅         28          15         ▲ 40 %
  ⇅ Net flow     ▆▅▆▆▅▆▆▅▆▆▅▅▆▆▅▅▆▆▄▅▁▃▁▃▂▂▃▂         −17         +9         ▼ better
  ◉ Habits       ···················●●●●●●●          6/6         100 %

  today so far: 🍅 25m · ✓ 0 · ＋ 1        review: 71 due · 0 answered
```

- Each row's hue is its identity. Values stay in normal text color, and the
  arrow or label carries the meaning of a delta, so color is never the only
  signal.
- `·` marks null days. The last value is labeled (Tufte).
- `▲`/`▼` follow each metric's `direction`. Neutral metrics such as Created
  show uncolored deltas.
- Falls back to plain text under `NO_COLOR` or a non-TTY, using the existing
  `style.rs` `Styler::detect()`.

`bob stats show worked -r 90d` gives the detail view:

```text
🍅 Worked · closed Pomodoro minutes · Jul 13 – Oct 10 (13 weeks, weekly median per day)

  6h ┤                    ▆
  5h ┤ ▅     ▇ ▆    ▇ ▆  ██ ▆
  4h ┤ █ ▆ ▆ █ █ ▅  █ █  ██ █ ▅
  2h ┤ █ █ █ █ █ █  █ █  ██ █ █
     └──────────────────────────
       Jul     Aug      Sep    Oct
  median 4h 50m/day · total 412h · best Tue Sep 30 (7h 35m) · 3 days with no closed Pomodoro
  by theme  SASE ████████ 41 %  BOB ████ 22 %  JOB ███ 14 %  GTD ██ 12 %  HOME █ 6 %  other 5 %
  weekday   Mon ▆  Tue ▇  Wed ▆  Thu ▆  Fri ▅  Sat ▄  Sun ▃
```

`bob stats show reviewed` shows answers by tier and outcome, Review time, and
answers per hour, plus Keep rate with a 90 % reference line. That 90 % line is
the decision trigger.

### 7.2 Obsidian: `stats.md` with a `bob-stats` block (the beautiful one)

The new root note is `stats.md` (alias *Stats*), with `parent: "[[dash]]"` like
the other dash child pages, linked from the dash Browse row and from the
weekly prune checklist. Note: `status.md` (zorg-era) is a near-name in the
quick switcher.

````markdown
```bob-stats
view: overview            # overview | chart | flow | heatmap | habits | strip
metrics: worked, reviewed, done, created, net, habits
range: 4w                 # initial; the in-view control can change it
```
````

The layout, top to bottom:

```text
┌ Stats ───────────────────────────────── [ 7D │ 4W │ 3M │ 1Y │ All ]  ☑ vs prior ┐
│ Sep 13 – Oct 10                                                                 │
│ ┌ 🍅 WORKED ─────┐ ┌ ⟳ REVIEWED ────┐ ┌ ✓ DONE ────────┐ ┌ ＋ CREATED ─────┐     │
│ │ 4h 50m /day    │ │ 44 /day         │ │ 12 /day         │ │ 18 /day         │     │
│ │ ▲ 6 % vs prior │ │ keep 82 %       │ │ ▲ 9×            │ │ ▲ 40 %          │     │
│ │ ╱╲╱╲_╱╲╱‾╲• 4h10│ │ ‥‥‥‥‥╱╲╱‾• 41   │ │ __._/\_/\• 38   │ │ ╱╲╱╲╱╲_╱‾• 28   │     │
│ └────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘     │
│                                                                                 │
│  Focus chart (selected tile): daily bars · 7-day rolling-median line ·          │
│  p25–p75 "normal" band · optional goal line · today hollow · nulls hatched      │
│                                                                                 │
│  Flow: Created bars up (blue) │ Done + Dropped bars down (aqua, gray) │ Net line │
│                                                                                 │
│  Year heatmap for the selected metric (quantile shading per metric; weekday     │
│  rows; nulls hatched, not empty)                                                │
│                                                                                 │
│  Habits grid: PRE chores × days, ● done ○ missed · blank = not due              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Interactions:**

- Clicking a tile switches the focus chart. Hovering a mark shows a tooltip
  with the date, value, and parts (for example "SASE 2h 05m · BOB 1h 40m · GTD
  1h 05m").
- **Clicking a day opens that daily note**, which ties every number back to
  the ledger it came from.
- The range control re-queries. "vs prior" toggles a ghost series for the
  previous period.
- The chosen range is remembered in memory for the session, not written to
  the note.

**Rendering:**

- Pure DOM plus inline SVG in bob-ledger-tools. No chart library, matching
  the existing zero-dependency plugins.
- CSS uses Obsidian theme variables and `color-mix()`, like `.bob-ready-cell`.
- `prefers-reduced-motion` is respected.
- Every chart has a "table" toggle for exact values and accessibility.

**Data path — bob owns every fact:**

- The block spawns `bob stats --format json …` on desktop through
  `child_process.execFile`, with a configurable `bobPath` defaulting to
  `~/.cargo/bin/bob`, because GUI-launched Obsidian on macOS lacks the shell
  PATH.
- It caches in memory with stale-while-revalidate, mirroring the idle-agenda
  decision. It revalidates on Tasks `cache-update` (debounced around 2 s), on
  the existing minute tick for day rollover, and on range changes.
- It never shows a snapshot for the wrong day.
- If `bob` is missing, it shows an actionable error card ("bob not found at …;
  set Bob path in Bob Ledger Tools settings"), never empty charts.
- This is a **new precedent**: no plugin spawns `bob` today. It is the
  Obsidian twin of *mac-capture-is-a-thin-client* and avoids a third JS mirror
  of task semantics.
- **Fallback if spawning proves fragile:** a local, untracked
  `.bob/stats/cache.json` written by `bob stats --format json`. The vault
  `.gitignore` ignores it by default.

### 7.3 Visual system

**Hue per metric, fixed and never reassigned by rank.** Steps come from the
dataviz reference palette and were validated with its script:

| Metric | Light | Dark |
| --- | --- | --- |
| Worked | orange `#eb6834` | `#d95926` |
| Reviewed | violet `#6250d6` | `#9085e9` |
| Done | aqua `#1baf7a` | `#199e70` |
| Created | blue `#2a78d6` | `#3987e5` |
| Dropped and other context series | neutral gray (`--text-muted`) | — |
| Habits | reuses Done's aqua | — |

What validation showed:

- **Adjacent pairs** (the tile order): pass in both modes. Worst CVD ΔE is 23.1
  light and 17.3 dark.
- **All pairs:** blue ↔ violet **fails** (normal-vision ΔE ≈ 10). So
  **Reviewed and Created never share a plot**, and tiles always carry text
  labels, so identity is never color-alone. Every flow or stacked chart uses
  only blue, aqua, and gray.
- **Contrast:** light-mode aqua is 2.74:1 against the surface, so Done marks
  need direct labels or the table view.

**Status colors stay reserved.** Deltas use ▲/▼ plus text. Goal "met" uses ✓
plus a label, never a bare green.

**Marks:**

- 2 px lines, rounded bar ends anchored to the baseline, 2 px gaps.
- Recessive grid. Never dual axes: a minutes chart and a count chart are
  separate small multiples.
- Today is a hollow, outlined bar. Nulls are hatched. Approximate backfill uses
  the texture fill.

**Smoothing and context:**

- A 7-day rolling **median**, not mean, because of triage spikes.
- A gray p25–p75 band shows the normal range.
- Weekday profile and best/worst days appear in detail views.

**Lapses:** the default window is 4 weeks, so a missed week ages out quickly.
"All" is one click away.

### 7.4 Where it meets your rituals

- **Weekly prune.** Change "check hours and created vs closed" to link
  `[[stats]]`. Optionally, `bob stats -r 1w -c` prints exactly the weekly prune
  numbers: worked vs prior 4 weeks, net flow, NEXT keep rate vs 90 %.
- **POST closeout (optional, Phase 3+).** Completing *Morning review* shows a
  single toast: "Review closed · 41 decisions · 1h 40m · keep 82 %". It is read
  from the journal through ledger-tools, so the definition isn't duplicated.
- **Daily note (optional).** A one-line `view: strip` block in the daily
  template showing "yesterday vs typical". Only add it if the weekly page proves
  useful. Don't start with it.

---

## 8. Reliability plan

- **Golden fixtures.** A fixture vault with hand-computed daily values for
  every built-in, covering:
  - archived tasks in `done/`;
  - reopened tasks;
  - recurring instances;
  - tasks without `created`;
  - a daily note with no Pomodoros section (null);
  - zorg `_poms`;
  - multi-host journals with duplicate keys.
- **Oracle test for Worked.** Evaluate the daily template's own heading inline
  query with bob's native Dataview engine on the fixtures, and assert it
  equals `worked`.
- **Journal contract.** Document the event schema in `docs/stats.md` and share
  conformance vectors between nav's outcome classification and the Rust
  reader. This is the existing practice for freshness.
- **Determinism and safety.**
  - `BOB_NOW` pins dates.
  - `bob stats` is strictly read-only. Only the plugin journal and
    `bob stats record` write, and both are append-only.
  - JSON grows additively with `schema_version`, and renderers decode
    defensively (the Mac app's `decodeIfPresent` stance).
- **Health line.** `bob stats` prints the last journal event per host and any
  gap warnings. A stale plugin shows up within a day instead of silently
  undercounting.
- **Performance budget.** `bob stats` under 300 ms on the full vault, which
  gives the spawn-on-render path headroom. Measure it in CI with the fixture
  and log it on the real vault.

---

## 9. Phased plan

| Phase | Repo(s) | Deliverable | Ships value alone? |
| --- | --- | --- | --- |
| **1. Engine + CLI** | bob-cli | Single-pass index, registry + config `stats:`, kinds `pomodoro`/`tasks`/`checklist`/`formula`/`field`, built-ins `worked`, `done`, `created`, `dropped`, `net`, `habits`, `review_closed`, `review_time`, `open`, `poms`; `bob stats` overview/show/metrics in human/json/csv; `docs/stats.md`; goldens; optional zorg `_poms` adapter | ✅ Use it in the next weekly prune |
| **2. Review journal** | bob-plugins (nav + ledger-tools), vault `.gitignore`, bob-cli reader | `api.stats.append` v1; `recordReviewAnswer` at the 5 choke points; `reviewed` + `keep_rate` + tier/outcome parts; gap detection; optional `--from-git` estimate | ✅ The metric you asked for first |
| **3. Obsidian page** | bob-plugins (ledger-tools), vault (`stats.md`, dash link, prune link) | `bob-stats` block (overview, chart, flow, heatmap, habits), spawn + cache, settings `bobPath`, table view, click-to-daily-note | ✅ The "beautiful" part |
| **4. Snapshots + polish** | bob-cli (`record` in `bob nightly` STEPS), plugins | Lane sizes, NEW, walk due; POST toast; `strip` view; Bases view if Bases gains charts | Optional |

After Phase 2, consider recording a decision ("Stats derive from the vault and
record only what it forgets; bob owns every metric definition"). Write it
through `/sase_memory_write`. This report does not write memory.

---

## 10. Open questions for you

1. **Should Reviewed include PRE/POST rows?** I recommend no (R2). If you'd
   rather see the raw walk count, it is a one-line config change
   (`tiers: all`).
2. **Should Done count `^ref` reading closes?** I recommend yes, split out as
   a part, because finishing a reading is real output. Say so if you'd rather
   exclude them.
3. **Which machine(s) run the morning walk?** Per-host files handle any
   answer, but it matters for testing the journal (the Mac vs athena
   Obsidian).
4. **Goals:** do you want one for Worked (for example ≥ 4 h)? I'd start with
   none and add it after four weeks of baseline.
5. **Backfill:** is a hatched, approximate Reviewed history for Oct 4 → ship
   date worth a hidden command, or start clean?

---

## 11. Recommended solution

Build **`bob stats`**: one metric engine in bob-cli that **derives** every
metric the vault already keeps durably and **records** only the review walk's
answers, in a per-host append-only JSONL journal under `.bob/stats/`, written
by bob-navigation-hotkeys through a new `api.stats.append` in bob-ledger-tools.
Metric definitions live in one registry. Built-ins and your own metrics share
the same `stats:` config, so a new metric is a few lines of YAML and, when
derived, arrives with its full history.

Ship v1 with **Worked 🍅, Reviewed ⟳, Done ✓, Created ＋, Net flow ⇅, and
Habits ◉** as headliners, plus Dropped, Review time, Keep rate, Review closed,
Open backlog, and Pomodoros behind them. Each has a type, unit, direction,
nulls distinct from zeros, a partial today, and no streaks.

Two thin renderers sit on one JSON contract:

- a colored terminal overview and detail views (sparklines, weekly bars,
  weekday profile, theme and tier breakdowns);
- an Obsidian `stats.md` page whose `bob-stats` block spawns `bob` and draws
  themed SVG: tiles with deltas, a focus chart with a rolling median and a
  normal band, a created-vs-closed flow chart, a year heatmap, and a habit
  grid, with an adjustable range and click-through to daily notes.

Deliver it in four phases, CLI first, so it pays off at the very next weekly
prune. Hook it into that prune so the numbers get looked at weekly, where they
inform decisions, rather than daily, where they become targets.
