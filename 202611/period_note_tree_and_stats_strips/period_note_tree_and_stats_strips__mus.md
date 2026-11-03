# Weekly → Quarterly → Yearly → All-Time: periodic parents with stats strips

*Research report (mus) · 2026-11-03 · question: should daily notes link to weekly
parents, chained up through quarterly, yearly, `all_time.md`, and `org.md`, each
with a stats strip, unit breakdowns, and LLM-enrichment scaffolding?*

## TL;DR and recommended solution

**Yes, build it — but in three phases, with two adjustments to the plan as stated.**

1. **Phase 1 — Weekly parents + weekly stats strip (the actual win).** Daily notes
   (`YYYY/YYYYMMDD.md`) gain weekly parents; weekly notes carry the first true
   "stats strip" (a week-range generalization of the day strip). Add the weekly
   review task to `gtd_daily.md` and the `stats strip` glossary term now.
2. **Phase 2 — Quarterly and yearly parents + strips.** Quarterly notes break down
   by month (3 rows, native to the stats engine) with a week table underneath;
   yearly notes break down by quarter (4 rows) with a month table underneath.
3. **Phase 3 — `all_time.md` and the `org.md` link.** A hand-curated capstone, not
   another stats dashboard. Link it under `org.md` last, after the lower levels
   have proven themselves.

**Adjustments to the stated requirements (justified in §5):**

- **A1 — Keep month arithmetic, even though month *files* go away.** The stats
  engine groups natively by day/week/month (weeks start Monday, months are
  calendar months; quarters are not a native bucket). Quarterly breakdowns should
  therefore lead with a 3-month table and only secondarily list ~13 weeks.
  Do not invent a quarter bucket in the engine.
- **A2 — Make `all_time.md` mostly narrative, not statistical.** A lifetime
  aggregate of worked minutes is a vanity number that gets slower and less
  meaningful every year; lifetime *review* (per-year table + curated narrative)
  is the durable value. Cap its stats strip at a small fixed metric set and a
  per-year breakdown, and say so in its template instructions.
- **A3 (migration) — Apply the new parent chain going forward; do not rewrite
  history by default.** Existing daily notes keep their current `parent:
  "[[day]]"` (or monthly) links. New dailies point at their weekly note.
  Provide a one-shot backfill command but leave old notes untouched unless Bryan
  asks — the same "never rewrite history" instinct behind append-only journals.

Why phased: weekly review is the highest-leverage GTD ritual Bryan doesn't yet
have a note for, and it exercises every new mechanism (parent chain, range
stats, embed fences, LLM instructions) at the smallest scope. Quarterly/yearly
reuse the same machinery. `all_time.md` is the riskiest piece socially (a
file that claims to summarize a life) and the cheapest to defer.

## 1. Current state (evidence)

### 1.1 Daily notes and parents

- Canonical daily path is `<bob-dir>/YYYY/YYYYMMDD.md`, selected by `BOB_DAY_FILE`,
  else `BOB_DIR` + `BOB_NOW`/local date (`docs/capture.md`, `docs/plan.md`,
  `docs/reference/vault-format.md`).
- The ledger is the `## Pomodoros…` section; column-0 checkboxes are Pomodoro
  entries; dedicated Task Links under open entries define Today at read time.
  Nothing about Today is stored (`docs/plan.md` §Today; decision
  `today-is-read-from-the-ledger`).
- New daily notes carry `parent: "[[day]]"` frontmatter (vault `day.md`;
  `docs/reference/vault-format.md` §Day notes). The prompt reports dailies
  currently link to a monthly file with no template — either way, the parent
  today is a *calendar container*, not a review note, and there is no weekly,
  quarterly, yearly, or all-time layer.
- Area/project notes use scalar `parent: "[[…]]"` wikilinks; residence,
  parent-project, and prerequisite are three composed answers
  (`docs/concepts/projects-and-dependencies.md`). The periodic chain reuses
  exactly this mechanism — no new link type is needed.

### 1.2 The day strip (the thing to generalize)

- The day strip is the read-only Stats summary at the top of the `bob-plan`
  block in canonical daily notes: five facts (`worked`, `reviewed`, `done`,
  `created`, `review_closed`) each with a quiet `typical` line (median of the
  prior 7 days, ▲/▼/= once the day is finished), plus a root-parent lane and a
  task-type lane (`glossary:day-strip`; `docs/stats.md` §Day strip).
- Three load-bearing properties to preserve in any generalization:
  1. **Bob owns every value.** Labels, displays, shares, hues, typical
     sentences all come from `bob stats` JSON; the plugin orders, colors, and
     lays out, and never sums or formats itself.
  2. **Derived at read time, never written.** The strip writes no note bytes
     and appends no journal events (`docs/stats.md` §Day strip, "Controls").
  3. **`typical` is day-only.** Typical-day objects appear only on day-grouped
     `count`/`minutes` points with ≥4 usable days; week/month points never
     carry them (`docs/stats.md` §Typical day). A week strip therefore needs a
     different comparison line (prior-period delta), not a typical line.
- The embedding primitive **already exists**: a `bob-day-stats` fence renders
  one day's strip in any note with `day: YYYY-MM-DD` in its body, and "such as
  a weekly note" is the documented example (`docs/stats.md` §Day strip). So a
  weekly note can *today* embed seven day strips with zero new code. Whatever
  we build should keep this fence working and add a range-strip fence beside
  it, not replace it.

### 1.3 The stats engine (what range aggregation already gives us)

- `bob stats` is read-only and deterministic for a fixed clock (`BOB_NOW`); one
  vault pass feeds all metrics (`docs/stats.md` §Engine principle).
- Ranges, grouping: `auto` picks day through 91 complete days, week through
  371, month beyond; **weeks start Monday (ISO, year boundaries included)** and
  months are calendar months; edge-clipped buckets carry `partial: true`
  (`docs/stats.md` §Ranges). There is no quarter grouping — confirmed by the
  absence of any `quarter` group in `docs/stats.md` and the CLI (`week|month`
  only in `bob stats overview -g`).
- Points carry `parts`/`parts_display` by dimension (`root_parent`, `theme`,
  `area`, …), `daily_points` for the display window, clock breakdowns, and
  per-day `quality`. The Stats-page "Where the time went" bar and the day
  strip's lanes already consume these — a range strip reuses the same JSON.
- `dash_stats.md` (aliases Stats/Dashboard Stats) is the full-report surface;
  every day-strip fact links to Stats with the day pinned
  (`docs/dashboard.md` §Child pages). Range strips should do the same: facts
  link to Stats with the *range* pinned.

### 1.4 Review rituals and `gtd_daily.md`

- `gtd_daily.md` is an area/sub-area note whose `^gtd` rows carry
  `[root:: gtd_daily]` so morning-review time attributes there
  (`docs/pomodoro-homes.md`, `docs/reference/vault-format.md`). Built-in metric
  `review_time` is `in: [gtd_daily]`.
- The morning walk is PRE → NEW → PROJECTS → PENDING → NEXT → RECURRING →
  TICKLER → ROTTEN → POST with a status-bar footer and POST closeout
  (`docs/guides/run-morning-review.md`, `docs/freshness.md`). There is **no
  weekly/quarterly/yearly review task today** — the "weekly review" hits in the
  repo are hints, trials, and test fixtures, not a ritual. This proposal fills
  a real gap, not a cosmetic one.
- The review journal (`.bob/stats/review/YYYY-MM.<host>.jsonl`) records only
  answers, never metric values (`docs/stats.md` §Review journal). Periodic
  review *completion* (weekly/quarterly/yearly closeouts) is the natural
  extension point if Bryan later wants "did I do my weekly review" as a
  metric — but do not add it in phase 1; a checklist row completed in the
  weekly note is enough signal to start.

## 2. Critique: is this a good idea?

**Yes — with the scope discipline in §5.** The core insight is sound: daily
notes are a ledger, and ledgers need rollups. A weekly note is where the
question "what did this week *mean*?" gets answered, and Bryan's system
already computes everything such a note needs except the note itself.

Strengths of the plan:

- **Fills the missing GTD review layers.** Daily (morning walk) exists;
    weekly/quarterly/yearly reviews are standard GTD horizons and currently
    have no home. The weekly review in particular converts lane growth (the
    known cost of sticky lanes: ~2–3 tasks/day needing a weekly prune;
    decision `task-lanes-are-sticky`) from background anxiety into a ritual.
- **Reuses proven machinery.** Parent frontmatter, read-time derivation,
  `bob stats` ranges, the fence-embed pattern, and the day strip's visual
  language all exist. Nothing here requires a new database, a new sync
  protocol, or a stored aggregate.
- **The chain daily → weekly → quarterly → yearly → all-time → org reads
  naturally** and gives every note exactly one parent, which keeps the
  existing "walk the parent chain" code (root parents, homes, capture
  routing) working unchanged.

Risks and costs (each addressed in the design):

1. **Six levels is a deep chain.** Every level is maintenance surface
   (templates, generation, rendering) and a click-distance cost. Mitigation:
   phases; and weekly notes link *down* to days (the direction people actually
   browse) while the `parent` field only points *up* one hop.
2. **Quarterly files group 13 weeks; the engine doesn't do quarters.**
   Naive "quarterly strip = 13 week strips" is slow and ugly. Mitigation (A1):
   quarter strips aggregate the quarter range once and break down by month.
3. **LLM enrichment can rot.** An agent asked to "update" a note with no
   guardrails will rewrite stats, invent facts, or reformat the template into
   oblivion. Mitigation: template instructions that are *prohibitions first*
   (§4), idempotency rules, and "prose only below this line" sections.
4. **Stats double counting across levels.** If weekly notes stored aggregates,
   quarters summing weeks would drift from quarters computed from days.
   Mitigation: **store no aggregates anywhere** — every strip is read-time
   from the vault, exactly like the day strip. Duplicated numbers are then
   always consistent because they share one computation.
5. **Boundary ambiguity.** Weeks (ISO Monday-start vs. Sunday-start?), quarters
   (calendar Q1–Q4?), years (calendar vs. rolling?). Mitigation: match the
   engine — ISO weeks starting Monday, calendar quarters (Jan–Mar, …),
   calendar years. State this in the template so humans and agents agree.
6. **`all_time.md` scope creep.** A file that is the parent of all years and
   child of `org.md` invites "life dashboard" maximalism. Mitigation (A2):
   define it as narrative + per-year table, explicitly not a stats page.

What I would *not* do: monthly files. The prompt already proposes replacing
them with weeklies, and I agree — monthly granularity serves neither the
weekly ritual nor the quarterly arc, and the engine's month *grouping* covers
the "show me October" need without month *notes*. Retire month notes (leave
existing files in place; stop generating/linking them), but keep month as a
display bucket.

## 3. Design

### 3.1 File identity and naming

Constraints: daily notes live at `YYYY/YYYYMMDD.md` (directory per year at the
vault root); a new `2026.md`-style file at the root would collide visually
with the `2026/` directory but not technically (file vs. directory with an
extension differ). Periodic Notes plugin conventions (the ecosystem default,
and the external `gh:liamcain/obsidian-periodic-notes` repo is already in
this project's inventory) use `YYYY-[W]WW`, `YYYY-[Q]Q`, `YYYY` formats.

Proposed (vault-root-relative; all with `parent` frontmatter pointing one hop
up):

| Level | Path pattern | Example | `parent` |
| --- | --- | --- | --- |
| Daily (changed) | `YYYY/YYYYMMDD.md` (unchanged) | `2026/20261103.md` | `[[2026-W44]]` (was `[[day]]`/monthly) |
| Weekly | `periodic/2026-W44.md` | week 44 of 2026, Mon 2026-10-26 – Sun 2026-11-01 | `[[2026-Q4]]` |
| Quarterly | `periodic/2026-Q4.md` | Oct–Dec 2026 | `[[2026]]` |
| Yearly | `periodic/2026.md` | calendar 2026 | `[[all_time]]` |
| All-time | `all_time.md` (vault root) | singleton | `[[org]]` |

Notes:

- A `periodic/` folder keeps 200+ future week files out of the vault root and
  out of the `YYYY/` day folders (which dataview/task queries may assume hold
  only daily notes). Daily notes stay where they are — moving them would break
  every existing query, and the plan doesn't ask for it.
- Weekly file stems use **ISO week-year**, not calendar year: the week
  containing 2026-01-01 is `2025-W53` or `2026-W01` per ISO; the template
  states the resolved Monday–Sunday range in its title line so humans never
  guess. The generator (not the human) picks the stem.
- Quarterly stems are calendar quarters: Q1 Jan–Mar, Q2 Apr–Jun, Q3 Jul–Sep,
  Q4 Oct–Dec. Yearly stems are calendar years.
- `org.md` is taken as given (Bryan's index note). Verify it exists before
  phase 3; if it doesn't, phase 3 creates the link target first. Do not invent
  a second root.

### 3.2 The stats strip (glossary proposal in §6)

A **stats strip** is the range-generalized day strip: a read-only,
read-time-rendered summary at the top of a periodic note, owned entirely by
`bob stats` JSON, consisting of (a) a fact row, (b) one or two distribution
lanes reusing the day strip's visual grammar (hollow-ring roots, tinted type
pills, hatch for unattributed), and (c) deep links into `dash_stats.md` with
the range pinned. The day strip is the daily specialization (5 facts +
`typical` lines); every other strip shows **prior-period deltas instead of
typical lines** (because `typical` doesn't exist off day grouping) and a
`partial` marker when the range includes today or an edge-clipped bucket.

Per-level strip content (metrics are the existing built-in ids; no new metric
kinds in phase 1):

- **Weekly strip** (range Mon–Sun; `partial` while the week is open):
  facts `worked`, `reviewed`, `done`, `created`, `net`, `review_time`,
  `sessions`, each with `vs last week` delta words from the engine's prior
  window. Lanes: roots + types over the week's worked minutes. Below the
  strip, an auto-rendered 7-row day table (day, worked, done, review mark) —
  each day linking to its daily note — then the agent's prose sections.
- **Quarterly strip** (range calendar quarter): facts `worked` (total + weekly
  average), `done`, `created`, `net`, `review_time`; delta vs. prior quarter.
  Lanes: roots + types over the quarter. Breakdown: 3 month rows (native
  month grouping) + a 13-week table (week link, worked, done). The month rows
  are the "units that make up the whole"; the week table is the drill path.
- **Yearly strip** (range calendar year): facts `worked`, `done`, `created`,
  `net`, `review_time`; delta vs. prior year. Lanes: roots + types. Breakdown:
  4 quarter rows + 12 month table.
- **All-time strip** (bounded by A2): facts `worked` (total), `done`
  (total), years-covered count — no deltas (prior period is meaningless), no
  lanes (a lifetime root bar is soup). Breakdown: one row per year. Everything
  else in the file is narrative.

Rendering strategy: extend the existing day-strip renderer with a
range-strip mode (new fence, e.g. `bob-stats-strip` with `range:` /
`period: 2026-W44` body), reusing lane markup, hue rules, fitter, and
accessibility patterns verbatim. Facts reuse the Stats-page formatters so
numbers match everywhere. Beauty comes from *sameness*: same hairlines, same
tabular numerals, same hollow/filled ring semantics, same `so far` + clock
meta on open periods ("so far · HH:MM" already exists for today; generalize
to "Week 44 so far · HH:MM" / "Q4 so far").

### 3.3 Unit breakdowns ("the parts that make up the whole")

Rule: **breakdowns are links, not copies.** Each periodic note lists its
children as a table (child link, 2–4 headline numbers) rendered read-time
from the same report the strip uses — never hand-maintained lists, which rot
within a month. Concretely:

- Weekly: 7 day rows (auto from daily points).
- Quarterly: 3 month rows (auto from month grouping) + 13 week rows (auto).
- Yearly: 4 quarter rows (computed as 3-month ranges; 4 small range fetches,
  cached) + 12 month rows (auto).
- All-time: N year rows.

Each row links to the child note. Missing child notes (future weeks) render
as plain text, not broken links — the generator creates notes lazily, and the
renderer must never demand a file that doesn't exist yet.

### 3.4 LLM/agent enrichment scaffolding

Every generated periodic note ships with an HTML-comment instruction block
(invisible in reading view, visible in source/live-preview source) plus a
visible one-line pointer ("Agent: read the instructions in source mode before
editing"). Rationale: instructions must survive normal reading (hence hidden)
yet be discoverable (hence the pointer), and must never render as note
content.

The instruction block follows one shape at all levels, with level-specific
sections:

1. **Identity** (1 line): "You are editing the weekly note for ISO week 44
   (Mon 2026-10-26 – Sun 2026-11-01). Today is <generated-date>."
2. **Prohibitions first** (the most important part): never edit the stats
   strip, the breakdown tables, frontmatter `parent`, or any `bob-*` fence;
   never restate numbers from the strip in prose (link, don't copy); never
   reformat headings; never touch other weeks' notes; never invent tasks,
   events, or numbers — every claim must trace to a linked note or the vault,
   and uncertain claims get a `?` marker.
3. **Where to write**: exactly the named prose sections for that level (see
   below); append-only bullets under dated subheadings; idempotency ("running
   twice with no new vault activity adds nothing").
4. **Empty-state behavior**: if the period is future or has no Pomodoros, write
   nothing except the planned-focus section; never pad.
5. **Closeout rule**: only mark the period's review task complete when the
   prose sections are non-empty (prevents box-ticking an empty review).

Per-level prose sections (kept small on purpose — an agent fills what exists):

- **Weekly**: `## Highlights` (what moved), `## Friction` (what dragged, with
  links to the task/area), `## Open loops` (carried into next week — each a
  task link, not prose), `## Next week` (3–5 intended outcomes). ~15 lines is
  a complete weekly.
- **Quarterly**: `## Arc` (the quarter's narrative in 3–5 sentences),
  `## By month` (one line per month, agent-written, *above* the auto month
  table — interpretation, not duplication), `## Open loops`, `## Next
  quarter`.
- **Yearly**: `## Arc`, `## By quarter` (one paragraph each), `## Themes`
  (which root parents grew/shrank and what that says), `## Next year`.
- **All-time**: `## Through-line` (curated, human-first — the agent proposes,
  Bryan disposes), `## By year` (one line each, above the auto table). The
  template explicitly says: this file is allowed to be short; do not
  manufacture profundity.

### 3.5 Review tasks in `gtd_daily.md`

Add three rows (PRE/POST placement follows the existing morning-review
convention — POST closeout stays last; weekly review is a weekend ritual, not
a morning one, so schedule-gate it):

- `Weekly review` — recurring row due each Sunday (or Bryan's chosen review
  day): open this week's note, confirm the strip rendered, fill Highlights /
  Friction / Open loops / Next week, complete. Links the weekly note.
- `Quarterly review` — due the first weekend of Jan/Apr/Jul/Oct: same shape
  one level up, plus confirm the 3 month rows.
- `Yearly review` — due the first weekend of January: same shape, plus the
  Themes section.

Each row's completion is the closeout signal (§3.4.5); the journal extension
for periodic-review completion stays a phase-2 option, not a phase-1
requirement.

### 3.6 Generation (no hand-made week files)

A new read-mostly command (e.g. `bob periodic init [--backfill]`) creates
missing notes for a range from templates: weekly/quarterly/yearly shells with
frontmatter, parent links, fences, breakdown placeholders, and the
instruction comment. Daily-note creation retargets new dailies' `parent` to
the current weekly note. Backfill generates shells for past periods without
prose (agents enrich on demand, never bulk-generate narrative for 200 past
weeks — that's cost without value). If a full CLI command is too much for
phase 1, a `just`-wrapped script plus checked-in templates is an acceptable
stand-in, but the template source of truth must live in the repo either way.

## 4. Alternatives considered

- **Monthly notes instead of weekly.** Rejected: months serve neither the
  weekly GTD ritual nor quarterly arcs; keep month as a stats bucket only.
- **Obsidian Periodic Notes plugin as the owner.** The plugin can create
  day/week/month/quarter/year notes, and it's already adjacent to this
  ecosystem. But it owns *file creation*, not stats strips, parent chains, or
  Bob semantics — use it (or not) as a dumb template expander if convenient,
  never as the design authority. Bob's generator stays canonical so `parent`
  links and fences are always correct.
- **Dashboard queries instead of files.** Dataview/Bases could show "this
  week's days" without week files. Rejected as the *primary* surface: queries
  can't hold agent prose, can't be linked as review-closeout targets, and
  don't participate in the parent chain. Keep queries as a secondary index.
- **Storing aggregates in the periodic notes.** Rejected (§2.4): write-time
  aggregates drift; read-time derivation is the established engine principle.
- **Weekly-only (no quarterly/yearly/all-time).** This is the fallback if
  phases 2–3 stall — and it would still be worth shipping. But the marginal
  cost of quarterly/yearly given the weekly machinery is small, so plan for
  them now and sequence them later.

## 5. Adjustments to the requirements (explicit)

- **A1 — Quarterly breakdowns lead with months, not weeks.** The request says
  "quarterly files should ideally show some kind of breakdown of each week."
  Keep the week table, but make the 3-month breakdown primary: it's native to
  the engine (one grouped fetch), matches calendar intuition, and renders 3
  rows instead of ~13. Reason: no quarter bucket exists in `bob stats`
  grouping; week tables are drill-down, not the headline.
- **A2 — `all_time.md` is narrative-first, stats-minimal.** The request asks
  for a stats strip at every level. Grant it, but bound it: lifetime totals +
  per-year table only. Reason: lifetime aggregates degrade (slow queries,
  vanity numbers, meaningless deltas); the file's job is continuity, and its
  template says so explicitly.
- **A3 — Going-forward migration, backfill optional.** The request doesn't
  state what happens to existing daily→monthly links. Decide: leave them;
  retarget new dailies; offer (don't run) a backfill. Reason: rewriting
  hundreds of daily frontmatters churns sync history for zero ritual value,
  and vault-sync conflicts are the most expensive failure mode in this system.

## 6. Proposed glossary term: stats strip

> **Stats strip** — the read-only, read-time Stats summary rendered at the top
> of a periodic note (weekly, quarterly, yearly, all-time), consisting of a
> fact row with prior-period deltas, optional worked-minutes distribution
> lanes, and deep links into Stats with the period pinned. Bob owns every
> value; the note stores none. The **day strip** is the daily specialization
> of the stats strip: the five-fact (`worked`, `reviewed`, `done`, `created`,
> `review_closed`) summary atop the `bob-plan` block in canonical daily notes
> (`YYYY/YYYYMMDD.md`), distinguished by its `typical`-day comparison lines
> (day grouping only) and its automatic rendering. Non-daily stats strips show
> `vs prior period` deltas instead of `typical` lines and a `partial` marker
> while their period is open. Related: `dash_stats` (the full report a strip
> links into), `root parent` and `task type` (the two lane dimensions),
> `typical` semantics in `docs/stats.md` (day-only by construction).

Placement: new `glossary/stats-strip.md` strand; append `day strip`'s "Not the
morning GTD review footer" style cross-link in both directions; `docs/stats.md`
gains a "Stats strips" parent section with "Day strip" as its first child.
`day-strip.md` itself stays authoritative for daily behavior — the new term
references it rather than restating it.

## 7. Open questions for Bryan (before implementation)

1. Review day: is Sunday (ISO week end) the weekly review day, or another day?
   (Template scheduling and the "week so far" semantics hinge on it.)
2. Confirm `org.md` exists and may gain `all_time.md` as a child — or name the
   true index note if different.
3. Weekly note folder: `periodic/` proposed — any vault-organization objection,
   or an existing folder convention to reuse?
4. Backfill appetite: generate shells for all past weeks/quarters/years, only
   2026, or nothing until asked? (Recommendation: current year only.)
5. Agent enrichment trigger: on-demand ("update my weekly note") vs. automatic
   (a scheduled job filling sections)? On-demand first; automation only after
   the instruction block proves itself.

## 8. Verification notes (what this report checked)

- Read via audited `sase memory read`: `obsidian.md`, `tailnet.md`,
  `cli_rules.md`, `docs.md`, `sase_beads.md`, `sase_artifacts.md`;
  `glossary:day-strip`, `stats-dash`, `pomodoro`, `work-log`,
  `morning-gtd-review-footer`, `root-parent`;
  `decisions:today-is-read-from-the-ledger`, `task-lanes-are-sticky`,
  `ready-is-freshness-gated`.
- Read in-repo: `docs/plan.md` (ledger, Today, roots), `docs/stats.md`
  (engine, grouping, typical-day, day-strip contract incl. the `bob-day-stats`
  weekly-note example), `docs/dashboard.md` (child pages),
  `docs/reference/vault-format.md` (note types, parent frontmatter, day
  notes), `docs/guides/run-morning-review.md`, `docs/freshness.md`,
  `vault/day.md`; `bob-plugins` ledger-tools day-strip fence + registry
  sources (confirming the embed primitive exists and its opt-outs).
- Deliberately *not* verified (flagged above instead): live `~/bob` contents
  (`org.md`, `gtd_daily.md` rows, existing monthly files) — this workspace has
  no vault checkout, so file-level claims about Bryan's vault are
  requirements-text, not observations. The design avoids depending on any of
  them except `org.md`'s existence (Q2).

*End of report.*
