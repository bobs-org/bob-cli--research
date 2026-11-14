# Bank transaction visualizations for period notes — research

*Researcher `mus` · 2026-11-14 · swarm report (suffix `__mus`)*

**Request:** improve on the bank-badge work (epic `bob-cli-lh`) with an excellent set of
new bank transaction visualizations on every period note (week, quarter, year, all time;
daily notes excluded). Design for intuitive, reliable, beautiful. Critique the idea,
adjust requirements with call-outs, end with a recommended solution.

**Method:** independent. I verified load-bearing claims against this checkout by running
`bob bank report` (human + JSON), `bob periods show 2026-W46 -f json`, and reading the
live week note (`~/bob/2026/2026-W46.md`) and bank month note (`~/bob/bank/2026-11.md`),
plus `docs/bank.md`, `docs/periods.md`, the `bob-cli-lh` epic bead and its plan
(`sase/repos/plans/202611/bank_badge_strip_family.md`), and the `bob-cli-ku` follow-up
bead. I did not open any peer swarm report.

## Bottom line

**Yes, build it — but build one panel, not a set of fences.** A single read-only
`bob-bank-period` fence with three blocks (summary header, category breakdown, child
columns) covers everything Bryan can act on during review, reuses the month card's
already-proven bar grammar, and adds exactly one bounded CLI addition on top of what
`bob-cli-lh` already ships. Most ways to make this "excellent" (typical comparisons,
run-rates, inflow lenses, a Mac line, a Stats metric) are explicitly gated behind the
bank trial (`bob-cli-ku`, snoozed to 2026-12-14, needs two months of rows) or behind a
privacy decision Bryan has not made — so they belong in a gated V2, not in this build.
The adjustments below are the difference between a panel Bryan trusts and wall
decoration he learns to ignore.

## Is this a good idea? Critique

**The core is a good idea.** Period review is where spending questions actually get
asked ("where did it go this week/quarter?"), the week note is where the Monday
Category-card walk already happens, and the badge alone is too thin at quarter/year
scale: `BANK · out $1,418` on a year note explains nothing. A breakdown + per-child
shape turns the badge's number into an answer.

**Three risks make the naive version a bad idea**, and each has a concrete fix:

1. **History does not exist yet.** The live vault has one bank month (`bank/2026-11.md`),
   tracking started 2026-11-11, and the only counted day so far holds 7 rows. Any
   typical-relative mark, trend arrow, or "usual" comparison computed today is noise —
   the bank epic deliberately excluded typicals from v1 for this reason, and `ku`
   re-gates them on two months of rows. *Fix:* V1 shows absolute money only, no
   typicals, no trends (adjustment A1).
2. **Bank data must not leak into agent surfaces.** The standing privacy rule (per the
   `ku` bead) is that v1 adds no bank data to agent-facing outputs: period briefs,
   Stats, the Mac app. A panel rendered live by the plugin from `bob bank` JSON honors
   this; anything that writes money into note bytes or the brief breaks it. *Fix:*
   read-only fence, values never written, brief untouched (A2).
3. **Two reports must never be joined by hand in the client.** The parts table comes
   from `bob periods show` (time), money from `bob bank report` (money). If the plugin
   sums one and hand-folds the other, boundary bugs are guaranteed (the badge research
   already proved the calendar-year vs ISO-week-year trap). *Fix:* one additive
   `buckets` array in the bank report keyed to strip columns, so parent == sum of
   children by construction (A3).

**Would I take a different approach?** Two alternatives I considered and rejected:

- *A money lane inside the existing Roots/Types strip charts.* Rejected: minutes and
  cents share no scale, and the strip's `typical` median machinery is meaningless over
  bursty money (paydays, rent cliffs). Money gets its own panel with its own grammar.
- *A sixth Stats fact ("Spent") with a typical line.* Rejected for the same reason, and
  Stats facts feed the brief — violating the privacy rule. Money is never a Stats fact.

## What exists today (verified this session)

| Fact | Evidence |
| --- | --- |
| Period notes render `bob-stats-strip` + `bob-period-parts`, own no numbers, hold no task rows | `~/bob/2026/2026-W46.md` scaffold; `docs/periods.md` §Note anatomy |
| `bob periods show` JSON exposes join keys: `columns[]` (strip axis) and `children[]` (parts rows), each with `id`/`start`/`end` | live `bob periods show 2026-W46 -f json` (columns `Mon 9…`, children days) |
| `bob bank report` JSON already carries `totals`, `breakdown[]` (emoji/key/label/out_cents/rows/share), `days[]`, `waiting{period,all,oldest}`, `accounts[]` with `start`/status | live `bob bank report -w 2026-W46 -f json` |
| Human month report already paints the reusable grammar: `Out/In/Net`, category bars with shares, calendar heat strip | live `bob bank report -f human` (☕/🛍️/💻/📆 bars, `░/▒/▓` strip) |
| `-p/--period`, `-s/--summary`, `coverage`, navigation metadata do **not** exist yet — they are `bob-cli-lh` phases 1–2 (in progress) | `bob bank report --help` shows only `-D/-m/-w/-y`; live JSON has no `coverage` key |
| Period briefs carry no bank numbers today (only bank task titles) | `bob periods brief 2026-W46 -f md` grep: no money section |
| Later views (typicals, year card, Stats metric, Mac line, week fence) are gated on the trial + 2 months of rows | `bob-cli-ku` bead, snoozed to 2026-12-14 |
| Color/accounting contracts: inflows green, outflows neutral ("spending is not an error"), state never by color alone; transfers/cash rows kept apart; `in` counts only `income`/`refund` | `docs/bank.md` §Totals, §Commands; live totals confirm `in_cents: 0` with 7 acked outflows |

## Recommended solution: one `bob-bank-period` fence, three blocks

**V1 ships a single opt-in fence**, placed by Bryan in the `## Days` / `## Weeks` /
`## Quarters` / `## Years` section after the `bob-period-parts` fence (explicit fence,
not scaffold surgery: period scaffolds are bob-owned, and a fence avoids migrating
every existing note). One fence, three blocks, all painted from one
`bob bank report -p <period> -f json` fetch:

**Block 1 — Summary header.** One line reusing the badge's exact copy contract:
`BANK · in +$Y · out $X · N waiting · since Nov 11` (parts only above $0.00 in integer
cents; whole dollars from quarter up with sub-$1 amounts keeping cents; coverage from
`lh`'s `coverage`; waiting period-scoped with today's all-months count in the tooltip).
This makes badge == panel header by construction — the numbers above the panel always
match the badge above the strip.

**Block 2 — Category breakdown.** The month card's bar grammar, period-scoped: one row
per counted category in declared order (then `cash`, then unclassified), each with
emoji, label, amount, and share-of-Out bar; an `In` section appears only when inflows
exist (payday lens can wait for V2, but the rows must render the day a paycheck lands).
Unclassified out/in always shown, never hidden — they are the "file me" signal next to
waiting. Cap at ~8 rows with an `N more` fold on quarters/years; full list lives one
click away in `bob bank report`.

**Block 3 — Child columns.** One mini-column per strip column, reusing the strip's own
`columns[]` ids as keys: days for a week (7), weeks for a quarter (13–14) and year
(52–53), quarters for all time (plus a year-grouped variant — see open question 3).
Each column shows out as a vertical bar and in as a marker/dot when present; waiting
days get the amber tick; columns with no coverage are hatched/quiet, never zero-height
lies. Clicking a column opens that day's heading (day/week panels) or the single
containing month note (quarter+), reusing the badge's read-only navigation targets.

**Interaction (inherits the badge contract):** read-only throughout — clicks open rows,
never write; `span[role=link]`, Enter/Space, `mousedown` preventDefault, Ctrl/Cmd-click
new tab; tooltip carries net, top-3 outflows, not-counted money, waiting oldest date,
coverage; stale = dashed edge + note; failure = muted `Bank unavailable`, never a
clean zero; nothing renders until data settles (no loading flash); hidden on future
periods, mobile, embeds, and when the period has no money and no waiting.

**V2 (gated, not this build):** typical comparisons once two months of rows exist (per
`ku`: median of same-kind priors, closed periods only, `▲/▼/=` marks); a run-rate line
("pace" vs elapsed-days fraction); an inflow/paycheck lens; subscriptions tie-in by
*linking* to the subscriptions album (`bob-cli-kt`), never duplicating it; and only
with an explicit Bryan decision — a `bank` Stats metric, a Mac idle-agenda line, or
brief inclusion (all three break the current privacy rule).

**Explicitly out of scope:** budgets, targets, forecasts, and alerts (needs history +
a policy Bryan hasn't set); pending-transaction tracking (the import contract covers
posted only); multi-currency; writing anything into notes.

## Data contract (bob-cli, additive, `schema_version` stays 1)

Everything in `lh` (`-p/--period` resolved through the periods calendar,
`-s/--summary`, `coverage`, `waiting_target`/`single_month` navigation) is a
prerequisite — this design assumes it lands first. V1 needs **one** further addition:

- `buckets[]`: one entry per strip column for the requested period — `{id, start, end,
  label, in_cents, out_cents, waiting, path, line}` — computed through the same shared
  `compute_totals` path as the header totals, so `sum(buckets) == totals` is a tested
  invariant, not a client fold. Bounded by construction (≤ 53 entries even for a 53-week
  year; all-time uses quarters, ≤ ~40 for any realistic history). This obsoletes
  client-side grouping of `days[]` and keeps `-s` payloads small.

Options stay alphabetical with short aliases (`cli_rules`); `-p` stays mutually
exclusive with `-D/-m/-w/-y`; `-y` keeps its calendar-year meaning for statements.
Plugin side: extend the bank data-service subscription key with `period`, reuse the
badge's shared model/painter (one `bankBadgeModel` → one `bankPeriodModel`), bump
`BANK_CACHE_SIZE` if a year note plus children approaches eviction, never hand-edit
`main.js`, deploy via `bob plugins sync`.

## Adjustments to the requirements (explicit call-outs)

| # | Requested / implied | Shipped as | Why |
| --- | --- | --- | --- |
| A1 | Rich visualizations now | Absolute-money V1 now; typicals/trends gated on the trial + 2 months of rows (`ku`) | Medians over 3 days of rows are noise; the epic excluded them deliberately |
| A2 | Visualizations on period notes | Live plugin fence; nothing written to notes, brief, Stats, or Mac surfaces | Standing privacy rule; `ku` requires an explicit decision to break it |
| A3 | Aggregated per-child views | Server-computed `buckets[]` keyed to strip `columns[]` | Client-side folds across two reports re-create the calendar/ISO boundary bug |
| A4 | (implied) money joins the strip | Money stays out of the strip and parts table; separate fence after parts | Different units, different data source, different `typical` semantics; strips forbid new facts |
| A5 | (implied) daily files too | Dailies excluded, as requested — badge + month card already cover them | A panel per day is clutter; the Monday walk lives on the week note |
| A6 | Coverage handling | Coverage line + hatched no-coverage columns are required, not polish | One week of rows on a year note otherwise reads as a frugal year |
| A7 | Waiting display | Waiting shown period-scoped in header; unclassified rows always listed in breakdown | An acked-but-uncategorized inflow is invisible to both `in_cents` and `waiting` — the breakdown is its only surface |
| A8 | Config surface | New `stats.bank_period` key (default on), `stats.bank_badge` stays the badge's key; one key gates the fence everywhere | Independent kill-switch; a broken panel must never take the badge down |

## Reliability notes (what "reliable" concretely means here)

- Integer-cents comparisons only; invalid/missing/unsafe cents are refusals, never `$0.00`.
- Period resolution goes through `PeriodId` (ISO weeks, 13/14-week quarters, ISO
  week-years, bank-universe all-time) — never `-y` for year strips.
- `so_far` marks open periods; closed periods with partial coverage say `to <date>`.
- Transfer-only and cash-only periods still hide the header (the accounting contract
  working), and the docs say so.
- Property test: header totals == sum of buckets == badge values on a fixed snapshot.

## Beauty notes (what "beautiful" concretely means here)

- Reuse the month card's bar grammar verbatim (emoji · label · bar · amount · share) —
  the vault already teaches this language; a second visual language is a cost, not a feature.
- Token inks from the badge decision: In = accessible green mix, Out = body ink,
  waiting = amber; chrome tints green only when In > Out; never red, never magenta,
  never color alone; tabular numerals; wrap between parts only.
- Narrow-friendly: bars shrink, amounts never ellipsize; forced-colors degrade to words
  and signs.

## Implementation order

1. **bob-cli `lh` first** (in progress): `-p`, `-s`, `coverage`, navigation. This
   design starts here.
2. **bob-cli:** `buckets[]` on the report + `compute_totals` routing + span-parity
   tests (W01, W53, Q4-2026, ISO 2026, all-time; `sum(buckets)==totals` property).
3. **bob-plugins:** shared `bankPeriodModel` + painter + `bob-bank-period` fence
   adapter; model-vector tests; light/dark/narrow fixtures; vault-bytes-unchanged
   click test; `BANK_CACHE_SIZE` review.
4. **Docs + memory:** `docs/bank.md` (fence, `-p`/`buckets`), `docs/periods.md`
   (placement), glossary cross-link from Bank Badge; no version/CHANGELOG edits
   (release-train rule).
5. **Gated later (`ku` re-scope):** typicals, run-rate, inflow lens, and any Stats/Mac/
   brief surface with Bryan's explicit privacy decision.

## Open questions for Bryan

1. **Placement:** panel after the parts fence (my recommendation — sits beside the
   children it breaks down) vs. directly under the badge (more visible, pushes
   Intentions down)? Fence placement makes this freely reversible.
2. **All-time columns:** quarters (bounded, my recommendation) vs. years (coarser,
   matches the `## Years` parts table)? Quarters reuse the year-panel code path.
3. **Waiting on closed periods:** show the amber tick on old waiting columns (my
   recommendation — leftover rows hide exactly there) or restrict waiting display to
   open periods?

## Sources and method

Verified live this session: `bob bank report` human output (Nov 2026: Out $249.77, 5
categories, heat strip) and `-w 2026-W46 -f json` (`totals`, 5-entry `breakdown`,
`days[]`, `waiting`, no `coverage` key pre-`lh`); `bob periods show 2026-W46 -f json`
(`columns[]`/`children[]` join keys, `period.coverage` on the time side);
`~/bob/2026/2026-W46.md` scaffold; `~/bob/bank/2026-11.md` rows. Read fully:
`docs/bank.md` (contract, totals, commands), `docs/periods.md` (anatomy, reports),
`bob-cli-lh` bead + `plan:202611/bank_badge_strip_family.md`,
`bob-cli-ku` bead (trial gate + privacy rule). Code refs:
`src/native/bank/report.rs`, `src/native/bank/model.rs` (`compute_totals`),
`src/native/periods/calendar.rs` (`PeriodId`), `src/native/periods/report.rs`
(strip/parts payload). No peer swarm report was located, opened, or consulted.
