# Daily Habit / Stats Tracking for Bob: Research & Recommendation (`mus`)

Researcher: `mus` · Date: 2026-10-11 · Scope: design research for per-day integer
habit/stats tracking in the Bob vault plus `bob-cli`, with a recommended v1.

## 0. TL;DR (read this and skip the rest if busy)

**Yes, build it — but build it backwards from what was asked.** Every metric Bryan
listed is already recorded in the vault as a side effect of normal work. Nothing needs
to be captured, هیچ new daily file needs to be written, and no new capture UX is
needed. The entire v1 is a **read-time derivation layer** (`bob stats` JSON engine) +
one **dashboard note** (`stats.md`) rendered by the existing `bob-ledger-tools`
plugin as SVG charts with period controls. History backfills itself to mid-2026 on
day one. Total new-write surface: zero bytes per day.

The one-sentence design: **metrics are pure functions over data Bryan already
produces; the dashboard is a thin, beautiful view over those functions; adding a
metric is a one-function registration, never a migration.**

Key adjustments to the request (all justified below):

1. **Do not store per-day stat values anywhere.** Derive them at read time.
   (Storing them creates a sync/staleness problem the codebase has already rejected
   twice — the `#today` tag and the written In-Progress mark.)
2. **"Review tasks processed via `]s`" must be redefined** as "tasks stamped that
   day" (`fresh::`/`completion::` date == D). Stamps carry no provenance, so "via
   `]s`" is unmeasurable retroactively — but stamping is what every `]s` answer
   does, so the proxy is exact in practice.
3. **Pomodoro minutes should come from the ledger parser, not the Dataview inline
   query.** The inline `durationformat(...)` expression in each daily note is display
   logic; the Rust `plan_budget` ledger parser is the tested source of truth and
   already handles time ranges, `[t::]`, exempt entries, and subheadings.
4. **Defer manual habits** (meds, workouts, teeth — the legacy `HABITS TO TRACK`
   list). Manual tracking has been tried in this vault (zorg `habit.md` files died
   out by early 2026) and has a different data model. v1 = zero-friction automatic
   metrics only.
5. **Don't install Tracker/Charts community plugins for v1.** Hand-rolled SVG in
   the existing first-party plugin is prettier, offline, versioned with the repo,
   and avoids a second source of truth.

---

## 1. What I verified (evidence, not assumptions)

All claims below were observed this session against the live vault and `bob-cli`.

### 1.1 The four requested metrics already exist as vault data

| Requested metric | Where it lives today | Coverage observed |
|---|---|---|
| Pomodoro hours/minutes per day | `## Pomodoros` ledger in `YYYY/YYYYMMDD.md`: time ranges + `[t:: Nm]`; daily note already sums completed ones with an inline Dataview expression | Universal for days with a ledger; Rust parser (`src/native/plan_budget/`) is the tested reader |
| Tasks completed per day | `[completion:: YYYY-MM-DD]` inline field on `#task` lines; exposed by `bob query --tasks` JSON as `done` (`{'raw','valid','value'}`) | 2205/2218 DONE tasks carry a valid done-date (~99.4%) |
| Tasks created per day | `[created:: YYYY-MM-DD]` inline field; exposed as `created` in Tasks JSON | 2476/2781 tasks (~89%); gap is mostly old/legacy lines |
| `]s` morning-review tasks processed per day | Every walk answer stamps: keep → `[fresh:: D]`, close → `[completion:: D]`, plus reschedule/route variants (§6 of `docs/freshness.md`); `bob freshness list -f json` already computes `refreshed_today` + `upkeep_today` for today | 56 lines vault-wide carry `fresh:: 2026-10-10` (yesterday) — the signal is dense and fresh |

### 1.2 Archives don't break history

`bob task archive` moves done/canceled lines into `done/*_done.md` but preserves
the full line text including `[fresh::]`, `[created::]`, `[completion::]`, and
`[scheduled::]` (verified in `done/cash_done.md`). The native Tasks query is
vault-wide and returns `done/` paths. **Therefore per-day series survive
archiving** — provided the stats engine scans the whole vault (including `done/`,
excluding `_templates/` and `_conflicts/`, mirroring the dashboard visibility
predicate in `docs/plan.md`). Any design that only scans daily notes or only
open tasks would silently lose history; this is a hard requirement.

### 1.3 The daily template and dashboard already set the pattern to follow

- New daily notes (`_templates/daily.md`) contain an empty ````bob-plan```` fenced
  block rendered live by `bob-ledger-tools` (v1.43.0), plus the Pomodoros inline
  Dataview sum. Precedent: **CLI computes, fenced block declares, first-party
  plugin renders.** A ````bob-stats```` block is the natural sibling — no new
  plugin, no new distribution channel.
- `bob plan -f json` (schema v2) and `bob freshness list -f json` (schema v13)
  establish the JSON contract conventions to copy: `schema_version`, `date`,
  `counts`, `warnings`. A `bob stats -f json` with `schema_version: 1` slots
  straight into scripts, smoke tests, and the plugin's versioned API namespace
  pattern (`api.dashboardCollections` is namespace v1 under top-level api v3).

### 1.4 One anomaly to resolve before building

My probe of `bob query --format json --tasks ''` found 0 occurrences of the
substring `[fresh::` in `originalMarkdown` while ripgrep finds hundreds in the
vault (including in `done/` files whose paths *are* returned). Possible causes:
field normalization in the serializer, or the dash origin's global filter
interacting with archived lines. **Recommendation:** the stats engine must not
depend on Tasks-JSON `originalMarkdown` for stamp fields — it should reuse the
repo's own line scanner (the `task_status_hooks`/`freshness` parsers already
tokenize `[fresh::]`, `[created::]`, `[completion::]` with tested edge cases in
`docs/freshness.md` §7 vectors). A 10-line coverage audit
(`rg -c` per field per month) should gate the build.

---

## 2. Critique of the plan as stated

### 2.1 Is this a good idea? Yes — with the friction at zero

The failure mode of habit tracking is well-represented in Bryan's own vault
history: the zorg-era `*_habit.md` per-day files (e.g. `2026/20260101_habit.md`)
stopped being maintained, and the `HABITS TO TRACK` list in `gtd.md` (meds, water,
workouts, teeth, CLs) is legacy text, not a living system. Manual per-day capture
dies; derived metrics survive because they cost nothing on days motivation is low —
which are exactly the days the data matters most. The request's instinct ("each stat
boils down to a single integer per day") is right, but the integers should be
*discovered*, not *recorded*.

### 2.2 The Goodhart risk is real but bounded

Tasks-closed-per-day is gameable (splitting tasks, closing trivia). Mitigations
in the design: (a) lead with *input* metrics (review done? pomodoro minutes) over
*output* metrics (tasks closed); (b) show created-vs-closed *together* so gaming
is visible as inflated creation; (c) frame the dashboard as "review mirror, not
scoreboard" — no streaks, no goals, no red/green judgment colors in v1. (The
dashboard badge palette in `docs/dashboard.md` is carefully informational; stats
should inherit that restraint, not add gamification.)

### 2.3 "Easy to visualize over an adjustable period" is the actual hard part

Computing integers is trivial; the UX risks are (a) period controls that require
editing queries, (b) charts that need network (CDN Chart.js) or a new plugin, and
(c) a dashboard that rots when metrics are added. The recommendation in §5
addresses all three: rendered block with clickable presets (7/30/90/365 + trailing
anchor), offline hand-rolled SVG, auto-discovery of registered metrics.

### 2.4 What the request gets wrong (kindly)

- *"The total number of morning GTD review tasks I completed each day (by iterating
  over and processing each one using the `]s` keymap)"* — conflates three things:
  review *answers* (stamps), review *closes*, and the *session* (morning review
  done or not). These want two metrics, not one (§4.1: `review_stamped`,
  `review_done`), because a day with 40 keeps and a day with 3 closes + skipped
  review look identical under a single number.
- *"Pomodoro hours and minutes ... I already show this via an inline query"* — the
  inline query is per-note display code duplicated into every daily file. Stats
  should not scrape rendered Dataview output; they should read the ledger with the
  Rust parser. (Longer-term, the inline expression could itself be replaced by the
  rendered block — out of scope for v1, noted as follow-up.)
- *"Easy to start tracking new daily metrics"* — under-specified. "Easy" must mean:
  no migration, no backfill job, history available immediately IF the underlying
  signal already exists, and honest "no history before today" labeling when it
  doesn't (e.g. a brand-new manual habit). §6 makes this a registry contract.

---

## 3. Recommended v1 metric set

### 3.1 The four requested (with corrected definitions)

1. **`pomodoro_minutes`** — sum of `[t::]` over *completed* (`[x]`) entries in day
   D's `## Pomodoros` ledger, via the `plan_budget` parser. Display as `h'h' m'm'`
   (same format string as the daily note). Open entries excluded (they're plans,
   not work). Subheading-split sections follow the existing `subheading_in_pomodoros`
   semantics.
2. **`review_stamped`** — count of task lines vault-wide with `fresh:: == D` OR
   (`completion:: == D` AND the line was due for review — practically: any
   `completion:: == D`). This is the "`]s` processed" proxy. Caveat documented in
   §0(2): occasional non-walk stamps (Ctrl+Shift+P `f` elsewhere, Task Card
   commits) are included; in practice these *are* review processing, so this is a
   feature, not contamination.
3. **`tasks_closed`** — lines with `completion:: == D` (any status type DONE; also
   count `cancelled == D` separately as `tasks_canceled` — canceled work is signal,
   especially pruning days, and conflating it with closes hides that).
4. **`tasks_created`** — lines with `created:: == D`. Pair with closed as
   **`net_backlog = created − closed`** (signed, the most motivating number on the
   dashboard).

### 3.2 Additional v1 metrics worth including (all free — same scan)

5. **`review_done`** (binary 0/1) — the `#gtd #post` "Morning review" recurring
   task in `gtd_daily.md` has `completion:: == D`. This is the keystone habit
   metric: did the session happen at all. Deserves the top slot on the dashboard.
6. **`pomodoro_count`** — number of completed ledger entries (complements minutes;
   distinguishes "one 3h slog" from "six focused 25s").
7. **`today_planned`** — `bob plan`'s Today-link count for day D (from that day's
   ledger; for past days, reparse the archived daily file — ledgers are immutable
   history). Planned-vs-done ratio is the planning-accuracy mirror.
8. **Lane pressure snapshot** (`next_size`, `pending_size`, `ready_size`) — state,
   not event: must be sampled, not derived (see §7 risk). For v1, record only
   *today-forward* via nightly sampling; show as "since <date>" with an honest
   start boundary. Alternatively defer to v2. I recommend including the sampler
   (cheap) but labeling the series start date prominently.

### 3.3 Explicitly deferred (with reasons)

- **Manual habits** (meds, water, workouts, teeth, the `gtd.md` legacy list):
  different data model (affirmation, not derivation), needs capture UX + reminder
  integration; do it as v2 on top of the same dashboard shell once v1 proves the
  viewing pattern. Note the old habit files as a warning, not a template.
- **Per-theme/per-project pomodoro breakdowns**: tempting, high cardinality,
  unclear question. Defer until Bryan asks a question that needs it.
- **Streaks, goals, targets, red/green judgments**: Goodhart accelerants. The
  dashboard shows trajectories; Bryan's weekly review supplies the judgment.
- **GTD-session duration** (how long the morning review took): derivable from the
  GTD ledger entry's time range, but GTD entries are exempt and often left open;
  data quality too poor for v1.

---

## 4. Architecture: three options, one winner

### Option A — Derive at read time (RECOMMENDED)

A new `bob stats` command scans the vault (reusing the existing scanners) and
emits per-day integer series as JSON; a ````bob-stats```` fenced block in
`stats.md` is rendered by `bob-ledger-tools` into SVG charts with period
controls. No vault writes, ever.

| Attribute | Assessment |
|---|---|
| Backfill | Free: full history to oldest stamped line (~June 2026 for created/completion) |
| Reliability | No sync clocks, no stale caches, no merge conflicts; archive-safe by construction |
| Testability | Pure functions + golden JSON vectors, same harness style as freshness §7 vectors |
| Cost | One vault scan per dashboard open (~3k tasks today; the freshness scan already does this every walk) |

### Option B — Materialize per-day values (nightly write-back into daily frontmatter)

`bob nightly` (or a hook) writes `stats: {pomodoro_minutes: …}` into each daily
note's frontmatter; Tracker/Dataview read the frontmatter.

Rejected for v1: duplicates derived data (every past write is a lie waiting for a
re-parse to expose it — e.g. late task closes with backdated `completion::`
would require rewriting past frontmatter); adds vault churn to every nightly;
makes `bob task archive` a stats-invalidation event; and frontmatter edits on
daily notes risk Templater/Dataview cache churn. The codebase's own history
supports this verdict: the `#today` tag (written Today state) was retired in
favor of read-time computation, and the In-Progress ledger mark was deliberately
*rendered, never written* for the same churn/race reasons (`docs/plan.md`).

### Option C — Adopt Tracker / Obsidian Charts community plugins

Rejected for v1 (not forever): adds an unmanaged dependency to the carefully
versioned plugin set, needs materialized data (so it inherits Option B's
problems), requires learning Tracker YAML DSL for every new metric (worse
extensibility than a Rust registry + auto-render), and its aesthetics can't match
a purpose-built SVG that inherits the vault's badge palette. Revisit only if v1's
hand-rolled charts prove insufficient (e.g. Bryan wants correlation scatterplots).

---

## 5. UX design: `stats.md` + ````bob-stats```` block

Precedent is the `dash.md` badge system and the `bob-plan` block: calm,
informational, keyboard-friendly, exact counts with honest unavailability (`–`,
never synthetic zero).

- **One dashboard note** (`stats.md`, aliased "Stats", linked from `dash.md` nav):
  one section per metric, each with a trailing-N-day SVG bar strip + current value
  + period-anchored delta (e.g. "last 7d avg"). Heatmap-calendar strip (GitHub
  style, 12 weeks) for `review_done` and `pomodoro_minutes` — the two glanceable
  "did I show up" views.
- **Period control without editing queries**: the rendered block owns preset chips
  `7 · 30 · 90 · 365` + prev/next window arrows, persisted per-note (in-memory +
  `localStorage`, never written to the vault — same "rendered, never written"
  principle). Default 30. Custom range = v2.
- **Beauty specifics**: bars reusing the vault's existing count-to-limit hue ramp (blue→green→yellow→orange,
  defined in `docs/dashboard.md`) for intensity, grey for zero, never red for
  judgment; tabular numerals; every chart labeled with data-start boundary
  ("created history since 2026-06-18; lane sizes since <sampling start>"); missing
  days shown as gaps, never interpolated zeros (a day with no daily note ≠ a day
  with zero pomodoros — though for pomodoros the distinction rarely matters,
  honesty in the renderer is cheaper than explaining it later).
- **CLI surface**: `bob stats --from YYYY-MM-DD --to YYYY-MM-DD --metric
  <key>... --format human|json` for scripts and debugging; `--metric all` default.
  Human format = sparkline-per-metric terminal view (mirrors `bob plan` human
  output conventions).

---

## 6. Extensibility: the metric registry contract

New metric in v1 design = **one pure function + one registry row**, no migration,
no backfill job, no dashboard edit:

```rust
// sketch: src/native/stats/metric.rs
struct Metric {
    key: &'static str,        // "pomodoro_minutes"
    title: &'static str,      // "Pomodoro time"
    unit: Unit,               // Minutes | Count | Binary | Signed
    history_floor: Option<NaiveDate>, // None = full vault history
    compute: fn(&VaultIndex, NaiveDate) -> Option<i64>, // None = no data
}
```

Rules: (1) `compute` may only read the shared `VaultIndex` (one scan, all
metrics — keeps dashboard opens O(1 scans)); (2) `None` renders as a gap/`–`,
never 0; (3) the dashboard enumerates the registry, so CLI and plugin stay in
sync by construction; (4) a metric whose signal starts today (new manual habit
in v2) declares `history_floor = today` and the UI labels the series start —
honest partial history beats fake zeros. A `bob stats --list-metrics` documents
the live catalog (mirroring `sase bead task-type list` convention from project
memory).

---

## 7. Risks, unknowns, and what to verify first

1. **Stamp-field coverage audit** (gate the build): month-by-month `rg -c` counts
   for `created::`, `completion::`, `fresh::` + the §1.4 `originalMarkdown`
   anomaly. If `created::` coverage pre-June-2026 is thin, set per-metric
   `history_floor`s accordingly.
2. **"`]s`-processed" has no provenance.** Accept the stamp proxy consciously;
   do NOT add provenance writes (a `reviewed_via:: ]s` field would be written
   state with all of Option B's diseases, on the hottest path in the vault).
3. **`today_planned` for past days** reparses old ledgers — verify old daily
   files' Pomodoros sections parse under the current parser (spot-check 5).
4. **Lane sizes are state, not events** — the only metric needing a sampler. Keep
   the sampler append-only (one JSONL line per day in state dir, not in the
   vault) or defer. Never derive "pending size on Oct 3" from today's vault.
5. **Performance**: full-vault scan per dashboard open is today's freshness cost
   and fine at 3k tasks; add a scan budget + `unavailable` fallback if the vault
   10x's.
6. **Mobile/offline**: hand-rolled SVG has no network dependency — verify the
   rendered block doesn't import remote fonts/scripts (vault is offline-first).

---

## 8. Recommended solution (phased)

- **Phase 0 (half day):** coverage audit (§7.1) + 5-file ledger reparse check
  (§7.3). Go/no-go on per-metric history floors.
- **Phase 1 (the v1):** `bob stats` JSON engine (registry + VaultIndex + 8
  metrics from §3.1–§3.2 minus lane snapshots) with golden-vector tests;
  `stats.md` + ````bob-stats```` renderer in `bob-ledger-tools` (bar strips +
  heatmaps + preset chips); dash nav link; docs page (`docs/stats.md`) defining
  each metric exactly (the way `docs/plan.md` defines Today — future arguments
  about "what does review_stamped mean" end by citing it).
- **Phase 2:** nightly lane-size sampler (JSONL in state dir, `bob stats` merges
  it); planned-vs-done ratio view; weekly-review footer line ("this week: 5/7
  reviews, 11h20m, +12/−31").
- **Phase 3 (only if v1 sticks):** manual-habit capture UX reusing the same
  dashboard shell (checkbox-state-per-day lines in one `habits.md`, registry
  entries with `history_floor`), plus reminder integration via the existing
  `bob_notify`/tmux surfaces.

The through-line: **Bryan already does the work; the vault already records it;
v1 just holds up the mirror.** Build the mirror, not another ledger.

---

## 9. Sources consulted

Live vault: `2026/20261010.md`, `2026/20261011.md`, `gtd_daily.md`,
`gtd.md` (HABITS TO TRACK), `_templates/daily.md`, `dash.md`, `2026/20260101.md`,
`2026/20260101_habit.md`, `2026/20260101_poms.md`, `done/cash_done.md`;
`~/.config/bob/config.yml` (plan/freshness caps); `bob-ledger-tools`
manifest/description; `bob-cli` docs (`plan.md`, `freshness.md`, `dataview.md`,
`dashboard.md`); CLI behavior observed: `bob plan -f json` (schema v2),
`bob freshness list -f json` (schema v13), `bob query --tasks` JSON task records
(`created`/`done` date objects, vault-wide incl. `done/`).
