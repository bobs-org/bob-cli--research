# Bank badge: hide-empty parts, color by in/out, and period-strip badges

Research report — researcher `mus` (independent, 5-researcher swarm).
Question: how best to implement the proposed "bank badge" upgrade —
glossary term, conditional in/out parts, color, and badges on every stats strip.

## TL;DR recommendation

Do it, with five adjustments. Keep the badge as a **separate chip row under
the strip** (not a sixth Stats fact), hide zero parts and hide the whole badge
only when there is genuinely nothing to show, color **amounts not chrome**
(in green, out neutral, waiting in warning color), and ship in phases so the
week/month/year period badge (no CLI change) lands before the quarter/all-time
badge (needs a `bob bank report` period extension). The one hard requirement
the plan must add: the hide rule must also account for **unclassified inflows**
and waiting rows, or the badge will hide exactly the money that needs
attention.

---

## 1. What exists today

There is no "bank badge" string anywhere yet. What the prompt calls the bank
badge is the **bank daily chip** in canonical daily-note `bob-plan` blocks,
owned by `bob-ledger-tools` (render) + `bob bank report -D` (data).

### 1.1 Daily chip: render

- Mixin: `BobLedgerToolsBankDailyChipMixin` in
  `plugins/bob-ledger-tools/src/241n-plugin-bank-daily-chip.js`
  (`setupBankDailyChip`, `bankDailyChipConfigEnabled`,
  `bankDailyChipEnabled`, `bankSyncPlanHost`, `bankDailyChipPaint`,
  `bankRefreshPlanHosts`, `bankReleasePlanHost`, `teardownBankDailyChip`).
- Enablement: persistent `stats.bank_chip` preference, read and cached at
  setup / on the 60 s config poll, never from a Markdown paint callback
  (`bankDailyChipConfigEnabled` returns `statsReadConfigValue("bank_chip") !== false`).
- Visibility gates in `bankSyncPlanHost` (all must pass or the host is
  released): the note has a parseable day (`dayStripDayFor(view.sourcePath)`),
  the day is not in the future (`day > today`), the preference is on, `bank.md`
  exists (`bankDailyHubExists`), and the bank data service is active.
- Placement: NOT inside the five-facts row. `bankSyncPlanHost` inserts a
  `div.bob-bank-daily-plan-host` immediately **after** the day-strip host
  inside the `bob-plan` block (`stripHost.nextSibling` logic in
  `239-plugin-day-strip-plan-host.js`, `bankPlanHostForRepaint`). Visually it
  reads as part of the day-strip area, which is why the prompt describes it as
  "shown in the day strip", but structurally it is a sibling row. This matters
  for the period design (see §6): keep this sibling-row pattern.
- Subscription: one `apiBankSubscribe({ command: "report", date: day })`
  per plan-block view, keyed by `bankCacheKey(bankBuildArgs(...))`; repaint on
  state arrival (`bankDailyChipPaint`).
- Current text (always both parts, always when data exists):

```js
const out = bankCardDisplayCents(Math.abs(model.outCents));
const incoming = bankCardDisplayCents(Math.abs(model.inCents), true);
const text = `BANK · out ${out} · in ${incoming}${model.waitingAll === null ? "" : ` · ${model.waitingAll} waiting`}`;
```

  `waitingAll` is appended only when `date === today` (see model below), and
  the chip is a `<button>` opening that day in the bank month note
  (`bankApi().ensureOpenDay(record.day)`), with `aria-label` carrying
  out/in/waiting and `title` noting staleness.
- States today: `Bank unavailable` (report error), `Bank · loading`
  (no result yet), `Bank · unavailable` (model `day-unavailable`),
  nothing at all when `report.teaching_empty === true` (no `bank.md`), plus
  `Refresh failed; values may be stale` + dashed `data-stale="true"` border
  when the result is stale.

### 1.2 Daily chip: model

- `bankCardDailyChipModel(report, date, today)` in
  `plugins/bob-ledger-tools/src/241l-plugin-bank-cards-model.js` (lines ~275–293):

```js
const day = report.days.find((entry) => entry && entry.date === date);
// requires Number.isSafeInteger(day.out_cents) && Number.isSafeInteger(day.in_cents)
return { kind: "day", date, outCents: day.out_cents, inCents: day.in_cents,
         waitingAll: date === today && report.waiting && Number.isInteger(report.waiting.all)
           ? report.waiting.all : null };
```

  Kinds: `teaching-empty`, `invalid-report`, `day-unavailable`, `day`.
- Formatting: `bankCardDisplayCents(cents, explicitPlus)` in
  `241m-plugin-bank-cards.js` strips the `+` unless `explicitPlus`; the chip
  passes `explicitPlus=true` only for the in-part. So today `BANK · out $12.50 · in +$1,250.00`
  (in-part keeps its `+`; out-part never shows a sign).

### 1.3 Daily chip: style

`plugins/bob-ledger-tools/styles.css` (~lines 8886–8898):

- Base: `.bob-bank-daily-chip` — `font-size: 0.72em`, muted text
  (`color: var(--text-muted)`), tabular numerals, `border-inline-start: 2px`
  accent bar + 14% accent wash background.
- Accent is **bank identity, not value semantics**: `--bob-bank-accent`
  defaults to `--bob-area-magenta` and follows `data-root-hue` from
  `bank.md`'s root hue (`bankCardRootHue("bank.md")`). There is currently
  **no value-based coloring at all** — a $5 coffee and a $5,000 payroll look
  identical.
- Stale: `data-stale="true"` → dashed border. Focus-visible outline exists.
  The refresh-error span is faint (`bob-bank-chip-refresh-error`).

### 1.4 Data contract: `bob bank report`

`src/native/bank/report.rs` (`build`, `Period`, `PeriodKind`, `ReportDay`),
`src/native/bank/cli.rs` (report args), `docs/bank.md` (§Commands, §Totals, §JSON):

- Periods today: **day / week / month / year only**
  (`-D/--day`, `-w/--week`, `-m/--month`, `-y/--year`; `resolve_period`
  refuses more than one). **No quarter, no all-time.** Week boundaries are
  ISO Monday-first. `report -D` yields one day and "is the daily chip's data"
  (`docs/bank.md`).
- Day out/in keep-apart rules (`report.rs`, day loop): cash-kind accounts,
  `[cat:: transfer]` rows, and `$0.00` rows **never land in day out/in**.
  `cents < 0` → `out_cents += -cents`; `cents > 0` **only if**
  `category == income|refund` → `in_cents += cents`. Anything else positive
  (uncategorized inflow, inflow with a spending category such as a `dining`
  refund) contributes **nothing** to either number. Acknowledgement is
  irrelevant to the amounts (waiting rows still count); `waiting` counts
  unacknowledged rows separately.
- Period totals (`compute_totals`, `docs/bank.md` §Totals): `Out` excludes
  transfers + cash-account rows (includes `cash` ATM + uncategorized
  outflows); `In` = `income` + `refund` only; `Net = In − Out`; plus
  `refund_cents`, `transfer_*`, `cash_out_cents`, `cash_traced_cents`,
  `unclassified_out_cents`, `unclassified_in_cents`. JSON `days[]` carry
  `{date, heading, path, line, out_cents, in_cents, rows, waiting, flagged}`
  for **every day of the period including empty ones** — but **no per-day
  unclassified_in_cents**. `waiting {period, all, oldest}` + `flagged`.
- Human-output doctrine (`docs/bank.md`): "inflows are green and outflows are
  neutral, because spending is not an error. State is always carried by text
  and shape, never by color alone." Month card agrees:
  `.bob-bank-metric-in strong { color: var(--color-green) }`; category modal
  `.bob-bank-category-amount.is-inflow` is green; queue rows are uncolored.
  This doctrine directly constrains §3.

### 1.5 Stats strips (where the badge must now also live)

- Glossary (via `sase memory read`): `glossary:day-strip` — the day member of
  the stats strip, five LABEL-value facts each over a quiet `typical` line
  (median of the 7 days before, ▲/▼/= once finished), then root-parent and
  task-type lanes; `glossary:stats-strip` — every member shares the same
  tiers: five facts (Worked, Reviewed, Done, Created, Review closed) totalled
  over the period + `so far` while open, each with a `typical` line (median of
  same-kind prior periods, marked only once closed); on periods a root-parent
  chart + task-type chart on one child-period axis; period-only Both/Roots/Types
  switch. "Worked counts closed on-clock pomodoros; off-clock time stays a
  quiet separate hint." The day strip "keeps its two lanes, has no parts row,
  and mounts itself in `bob-plan`".
- Plugin models: `239-plugin-day-strip-model.js`
  (`DAY_STRIP_METRIC_IDS`, `dayStripBuildFact`, `dayStripAriaLabel`,
  skeleton/future/hidden/unavailable states), `239-plugin-period-strip-model.js`
  (`PERIOD_STRIP_METRIC_IDS`, `periodStripBuildFact`, `periodStripTypical`,
  week columns, children rows, groups), renders in
  `239-plugin-day-strip-render.js` / `239-plugin-period-strip-render.js` +
  charts. Facts open the stats dash with the period pinned; strips never write
  the note; `bob owns every value`.
- Period notes (`glossary:period-note`): week files, 13-week quarters
  (Q4 takes W53), ISO week-years, `all_time` singleton; each opens with a
  stats strip + live parts table. Monthly notes are retired as a note level —
  bank's `bank/YYYY-MM.md` month notes are a **separate, still-current**
  hierarchy (`glossary:bank-month-note`), so "month" means different things in
  the two systems; a month-period badge must say "month" in the bank sense.
- Work-badge color precedent (`docs/dashboard.md`): TODAY/PENDING/NEXT/READY
  use count-to-limit bands (grey→blue→green→yellow→orange→magenta→red, with
  magenta reserved for exactly-at-cap); NEW/ROTTEN/CROWDED are grey-when-zero,
  red-when-positive; BLOCKED is informational. Magenta already means both
  "bank identity" and "lane exactly full" — overloading it further with
  in/out semantics would be a mistake.

---

## 2. Requirement-by-requirement analysis

### R1 — new glossary term for "bank badge"

Straightforward and worth doing. Gaps to close while writing it: the term
does not exist in `docs/reference/glossary.md` (generated from the web) or
`sase/memory/glossary/`; the closest existing strands are `bank-row`,
`bank-month-note`, `day-strip`, `stats-strip`, `period-note`. Proposed strand
(§6.5) uses keyword `Bank Badge`, aliases `bank chip` + `daily chip`, and
normatively separates the badge from the five Stats facts, the parts table,
the month/queue cards, and the review footer. Cost: one strand file + generated
glossary rebuild + a docs link. No behavior risk.

### R2 — show each in/out part only when it is >$0.00; hide the badge when both are $0.00

Directionally right (a perennial `BANK · out $0.00 · in $0.00` row is pure
noise on ~most days), but the rule as stated has a **reliability hole** that
must be fixed before it ships (§4.1): with the current JSON, a day holding
only an **uncategorized +$50 inflow** reports `out_cents = 0, in_cents = 0`
and would vanish — hiding the one row that most needs filing. Likewise a day
of only transfers / cash-account rows / `$0.00` rows reports 0/0. The shipped
rule must be: hide the in/out **parts** at exactly `$0.00` (integer-cents
comparison, never float or string compare — `bank_row_zero` already warns on
`$0.00` rows), but hide the **whole badge** only when `out == 0 && in == 0
&& unclassified_in == 0 && waiting == 0` (day), and the period analog with
`waiting_period`. That keeps "nothing to show" truly empty while never
swallowing actionable money. The waiting carve-out matters mostly for today
(the only day whose chip shows `waitingAll`); a future-dated or
teaching-empty day already shows nothing, which must stay visually distinct
from "genuine zero" (see §4.3).

A second subtlety: with partial hiding the text grammar needs a rule. `BANK ·
out $X` / `BANK · in +$Y` / `BANK · out $X · in +$Y` covers it; keep the `+`
on the in-part (current `explicitPlus` behavior) so polarity survives without
color. When only the waiting segment remains (pathological $0 day with
waiting rows), render `BANK · N waiting` rather than an empty label.

### R3 — color the badge by in/out values

The most design-sensitive requirement, and the one where "intuitive and
beautiful" is won or lost. Full analysis in §3; headline: color the
**amounts**, not the chrome; green in-part, neutral out-part, warning-colored
waiting segment; never red for spending; never color alone (labels stay).
This extends the existing `docs/bank.md` doctrine instead of inventing a new
one, and it avoids colliding with magenta (bank identity / at-cap), red
(errors/ROTTEN/over-cap), and orange (Worked/near-cap).

### R4 — badge on all period notes (every stats strip), aggregated

Valuable — a week/quarter/year review without money context is missing a leg —
but it is the largest scope item because of two gaps:

1. **CLI gap**: `bob bank report` cannot express quarters or all-time
   (§1.4). Period notes come in week / quarter / year / all_time flavors, so
   "every stats strip" needs either a report extension (`-q/--quarter`,
   and a decision on all-time: `--all-time`? or reuse the year-range
   machinery with unbounded start) or client-side aggregation of month
   reports. The extension is cleaner (one code path, one JSON shape,
   `so_far`/`label` semantics for free); client-side summation would
   re-split rounded totals and duplicate `by_date` logic. Week/month/year
   badges need **no** CLI change and should ship first.
2. **Placement/semantics gap**: the five strip facts are Stats metrics with
   `typical` medians, `so far`, quality states, and dash deep-links. Bank
   totals are none of those (money is bursty; a "typical payday" median
   would mislead; bank rows open the bank month note, not the stats dash).
   So the period badge must be the **same sibling-row component as the daily
   chip**, fed by `totals.out_cents / totals.in_cents` (+
   `unclassified_in_cents` per §4.1), placed directly under the strip and
   above the parts table — not a sixth fact, not a chart series, not a parts
   column.

`so far` should be honored (open week/quarter/year aggregates get the marker,
mirroring the strip convention); `typical` must **not** be added for money.
Waiting on period badges: omit it (the queue card owns the waiting queue; a
period waiting count would double-report and confuse `waiting_all`-vs-`waiting_period`
semantics). The daily chip keeps its today-only `N waiting` segment.

---

## 3. Color design (think hard)

### 3.1 Doctrines that bind

- `docs/bank.md`: inflows green, outflows neutral — "spending is not an
  error". Any red-outflow scheme contradicts the contract and would need a
  decision record to overturn; I recommend against.
- `docs/bank.md`: "State is always carried by text and shape, never by color
  alone." Labels (`out`/`in`/`waiting`), signs (`+` on in), and order carry
  the meaning; color is redundant emphasis.
- `docs/dashboard.md`: red = positive NEW/ROTTEN/CROWDED counts and
  over-cap lanes; magenta = exactly-full lanes AND bank accent. A red or
  magenta value encoding would actively misread against both systems.
- Stats palette (`docs/stats.md`): orange = Worked, violet = reviewed,
  green = done, blue = created, gray = net/dropped. Green already means
  "good/complete/inflow" everywhere; reuse it for money-in.

### 3.2 Recommended scheme

| Case | Chrome (border + wash) | out amount | in amount | waiting segment |
| --- | --- | --- | --- | --- |
| out only (spending day) | unchanged bank accent (magenta/root hue), muted | normal text | — (hidden) | warning color when present |
| in only (payday/refund) | unchanged bank accent | — (hidden) | **green** (`var(--color-green, var(--text-success))`, same token as month-card inflow) | warning color when present |
| both (mixed day) | unchanged bank accent | normal text | **green** | warning color when present |
| neither (hidden) | badge not rendered | — | — | — (badge hidden unless waiting/unclassified force it visible) |
| loading / error / stale | current treatment | — | — | — |

Why this shape:

- **Amounts, not chrome.** The accent bar stays bank-magenta in all states,
  preserving bank identity and the existing `data-root-hue` machinery. Only
  the in-amount (and waiting count) change color. This is the smallest visual
  delta that still answers "did money come in?" at a glance, and it matches
  the month card (`.bob-bank-metric-in strong` green) and the terminal report
  (green inflows) pixel-for-token.
- **Out stays neutral, always.** Spending is routine; alarming it would cry
  wolf on groceries and train Bryan to ignore real red (deltas, errors,
  ROTTEN). Net-negative mixed days stay neutral chrome too — the numbers and
  their signs say what happened; a "you spent more than you earned" judgment
  color would editorialize the ledger and invite disputes about refunds,
  reimbursements, and transfers (all of which distort naive net).
- **Waiting gets the warning color**, not green/red: `N waiting` is the only
  actionable segment (unfiled rows), and the heat-grid waiting dot already
  uses `var(--text-warning)`. Scoping the warning tint to that segment keeps
  the badge calm while making the queue visible.
- Alternatives rejected: whole-badge green on payday (too loud next to the
  muted strip; fights the `done` green facts); red/orange for outflows
  (contradicts the no-alarm doctrine; orange collides with Worked);
  net-based coloring (refunds + transfers + uncategorized inflows make naive
  net judgmental and often wrong); heat-intensity background by out size
  (the month card already owns heat; duplicating it in a 0.72em chip is
  illegible).

### 3.3 Accessibility and theme-safety

- Text+sign redundancy: `in +$1,250.00` vs `out $61.20` reads unambiguously
  with color removed; `aria-label` already spells out out/in/waiting and must
  be extended to the partial-part grammar (`Open bank rows for 2026-11-14;
  in +$1,250.00; 3 waiting across all months`).
- Tokens, not hex: reuse `--color-green`/`--text-success`,
  `--text-warning`, `--text-muted` so dark/light themes and existing
  high-contrast handling follow for free. Respect `NO_COLOR` where the
  terminal report path is involved (plugin CSS has no NO_COLOR concept, but
  the text redundancy covers it).
- Color-vision safety: the only hue distinction is green-vs-default-text for
  the in-amount plus an explicit `+` sign — safe under deuteranopia because
  the sign, label, and position disambiguate. Never encode anything in
  red/green opposition.
- Stale stays dashed-border + note (shape, not color). Loading/error strings
  stay faint/error tones as today.

---

## 4. Critique: is this a good idea, and what must change

**Yes — with the adjustments below.** Money context in the daily and period
review surfaces is genuinely useful (the morning walk already points at the
waiting queue; the strip is where "what happened" is summarized), the hide
rule removes far more noise than the period badge adds, and the color proposal
above stays inside existing doctrine. The risks are all in the details, and
they are all fixable. I would not take a different approach (e.g. folding bank
into Stats metrics, or a separate bank section in period notes): Stats metrics
are productivity values with `typical` baselines and dash links, and a bank
section would duplicate the month/queue cards. The sibling-chip-row approach
reuses one component, one JSON contract, and one doctrine.

### Required adjustments (call-outs against the prompt)

1. **Hide rule must include unclassified inflows (and waiting).** As specified
   ("both $0.00 → hide"), a day with only an uncategorized +$50 inflow, only
   transfers, only cash-account rows, or only `$0.00` rows would vanish. The
   uncategorized-inflow case is the dangerous one: it hides money needing a
   category. Fix: add per-day `unclassified_in_cents` to report JSON
   (`days[]` entries; totals already carry it) and hide the badge only when
   `out == 0 && in == 0 && unclassified_in == 0 && waiting == 0`. Show an
   `unclassified` marker segment (existing "Unclassified: $X out · $Y in"
   vocabulary from the month card extras) whenever it forces visibility.
2. **Do not color outflows red (or orange/magenta).** The prompt says "think
   hard about which colors" — the answer is constrained: green in, neutral
   out, warning waiting (§3). Anything else contradicts `docs/bank.md` or
   collides with lane/magenta semantics. If Bryan wants net-aware coloring,
   that needs its own decision record; do not smuggle it into this change.
3. **Period badge needs a CLI extension for quarters (+ all-time decision).**
   "Every stats strip" cannot ship on the current `report` periods. Add
   `-q/--quarter YYYY-Qn` (free short flag; `-D/-m/-w/-y` taken; verify `-q`
   conflicts in `cli.rs` first) reusing `periods/calendar.rs`
   quarter parsing/range helpers, and decide all-time explicitly: either a
   `--all-time` report period (bounded start = earliest bank row / account
   start) or a documented "no badge on all_time" carve-out. My recommendation:
   implement quarter + all-time together so "every stats strip" is literally
   true; all-time aggregates over the whole journal with `so_far: true`.
4. **Do not make the badge a Stats fact or give money a `typical` line.**
   Tempting for visual uniformity, but medians over bursty money mislead
   (payday spikes, rent cliffs) and the five-fact contract (dash links,
   quality states, `typical` medians) does not fit money. Sibling row with
   `so far`, no `typical`.
5. **Keep period badges waiting-free; keep the daily waiting segment
   today-only.** Cross-period waiting counts would double-report the queue
   card and mix `waiting_period` with `waiting_all`. Current daily semantics
   (today → `waiting_all`, else nothing) are already subtly odd; do not
   propagate them — document them in the glossary instead.
6. **Keep the bank accent (magenta/root-hue) as identity in all value states.**
   Do not re-tint the border/wash by value; it would destroy the bank-card
   family resemblance (month/queue/category all share the accent) and fight
   the lane-cap magenta.

### Non-blocking nits worth taking

- Grammar: `BANK · out $61.20`, `BANK · in +$1,250.00`,
  `BANK · out $61.20 · in +$1,250.00`, optional `· N waiting` tail. Keep the
  `BANK ·` prefix (namespace in a chip-dense block) and the `+` on in.
- Numbers: integer-cents `> 0` checks; display via existing
  `bankCardDisplayCents` / `bankFormatCents` (commas, 2dp). Zero-part hiding
  is exact (`=== 0`), so `$0.004`-style dust cannot occur (cents are integers).
- Future/teaching/loading/error states keep current behavior; genuine-zero
  must render as *absence*, which reads differently from the explicit
  `Bank · loading` / `Bank unavailable` strings. Good as-is.
- The `stats.bank_chip` preference gates the daily chip; decide whether it
  also gates period badges (recommendation: yes, one preference, documented —
  a user hiding bank from the day strip almost surely wants it hidden from
  period strips too; per-kind toggles are over-engineering).

---

## 5. Recommended solution

### Phase 0 — glossary + docs (no behavior)

- New strand `sase/memory/glossary/bank-badge.md` (keyword `Bank Badge`):

```markdown
---
keyword: Bank Badge
aliases:
  - "bank chip"
  - "daily chip"
---

The read-only money summary chip drawn from `bob bank report`: on a daily
note, `BANK · out $X · in +$Y` (plus `N waiting` on today) in its own row
right under the [[day-strip]] inside the `bob-plan` block; on a [[period-note]],
the same row under the [[stats-strip]] with that period's aggregated totals
and a `so far` marker while the period is open. Each in/out part shows only
when it is greater than $0.00; the badge hides when there is nothing to show
(no in, no out, no unclassified inflow, nothing waiting). The in amount is
green and the out amount is neutral — spending is not an error — with a
warning-tinted waiting count; labels and signs carry the meaning so color is
never load-bearing. It opens the day's rows in the [[bank-month-note]], never
the [[stats-dash]]. Not a Stats fact (it has no `typical` line), not the
month/queue bank cards, not the [[morning-gtd-review-footer]].
```

- Rebuild `docs/reference/glossary.md`, link the badge from `docs/bank.md`
  (§Commands `report -D` paragraph) and `docs/stats.md` (day-strip + period
  sections), via `just docs-gen` / `just docs-check` per `docs.md` memory.

### Phase 1 — daily chip: partial-hide + color (plugin only, no CLI change)

- `241l-plugin-bank-cards-model.js`: extend `bankCardDailyChipModel` to pass
  through `waiting` (day) and new `unclassifiedInCents` (after the JSON
  addition in Phase 1b, or land the model defensively with `?? 0`).
- `241n-plugin-bank-daily-chip.js` `bankDailyChipPaint`: build parts
  conditionally (`outCents > 0`, `inCents > 0`), hide host when the §4.1 rule
  says empty, wrap amounts in spans (`.bob-bank-chip-out`,
  `.bob-bank-chip-in`, `.bob-bank-chip-waiting`), extend `aria-label`/tooltip
  grammar.
- `styles.css`: `.bob-bank-chip-in { color: var(--color-green,
  var(--text-success)); font-weight: 600 }`-ish (match month-card inflow
  weight), `.bob-bank-chip-waiting { color: var(--text-warning) }`, out
  inherits muted. No chrome change.
- Tests: extend the `241l` model tests + chip paint tests with
  out-only / in-only / mixed / all-zero / unclassified-only / waiting-only
  vectors; plugin fixture `bank/report-month.json`-style day fixtures.

### Phase 1b — report JSON: per-day unclassified inflow (bob-cli, additive)

- `src/native/bank/report.rs`: add `unclassified_in_cents` (and, for
  symmetry/cheapness, `waiting` already exists) to `ReportDay` + JSON
  `days[]`; compute with the same keep-apart rules as `compute_totals`.
  Additive field: no breaking change to `schema_version: 1` shape beyond the
  new key (document in `docs/bank.md` §JSON + `docs/reference/json-outputs.md`).
- `src/native/bank/tests.rs`: day vectors — uncategorized inflow day,
  transfer-only day, cash-account-only day, `$0.00`-row day, mixed day.

### Phase 2 — period badges for week/month/year (plugin only)

- New period-strip bank host (mirror `bankSyncPlanHost`): for a period note,
  subscribe `apiBankSubscribe({ command: "report", <period args> })` matching
  the strip's period id (week → `-w`, month → `-m` in the bank sense — note
  the month vocabulary clash and label accordingly, year → `-y`), render the
  same chip component with `totals.out_cents / totals.in_cents /
  totals.unclassified_in_cents`, `so_far` marker from `period.so_far`, no
  waiting segment, same hide rule with `waiting_period`.
- Placement: directly under the `bob-stats-strip` fence output, above the
  parts table; `Both/Roots/Types` switch does not affect it; gated by the
  same `stats.bank_chip` preference.
- Tests: period-model mapping tests (week/month/year ids → report args;
  hide/show matrix; `so_far` propagation).

### Phase 3 — quarter + all-time report periods (bob-cli + plugin)

- `src/native/bank/cli.rs`: add `quarter_arg()` (`--quarter/-q`,
  `YYYY-Qn`, alphabetical order per `cli_rules.md`) and decide all-time
  (`--all-time`, no short or `-A` if free — check collisions; every public
  long option needs a short alias). `resolve_period` gains the new kinds;
  reuse `periods/calendar.rs` quarter ranges; all-time start = min(account
  starts, earliest row) with `so_far: true`.
- Plugin maps quarter/all_time strip ids to the new args. Docs + JSON
  reference updates. This is the only phase touching CLI help (keep
  `bob --help` section order, alphabetical subcommands/options per
  `cli_rules.md`).

### Verification

- `bob bank report -D/-w/-m/-y` (+ `-q`/`--all-time` after Phase 3) JSON
  vectors incl. the §4.1 trap days; `just check` / repo gates per project
  config; Obsidian checks: daily note with payday / spending-only /
  transfer-only / uncategorized-inflow / no-bank days, plus week + quarter +
  year + all_time period notes, light + dark theme, narrow width (chip wraps
  via existing flex host), screen-reader label spot-checks.

---

## 6. Evidence index (selected)

- Daily chip: `plugins/bob-ledger-tools/src/241n-plugin-bank-daily-chip.js`
  (paint text line ~207–215; gates ~107–120; teaching-empty ~201).
- Model: `plugins/bob-ledger-tools/src/241l-plugin-bank-cards-model.js`
  (`bankCardDailyChipModel` ~275–293; heat buckets ~72–94 for contrast).
- Cards/format: `241m-plugin-bank-cards.js` (`bankCardDisplayCents` ~38–41;
  month extras `Unclassified: … out · … in` ~413; heat title `Out …` ~431).
- Style: `styles.css` `8886–8898` (chip base + `data-root-hue` accents),
  `8832` (inflow green), `8852` (cash-note warning), heat `8860–8866`.
- Plan host surgery: `239-plugin-day-strip-plan-host.js` (~280 bank sync,
  ~735–808 bank-host preservation across repaints).
- CLI/contract: `src/native/bank/cli.rs` (report ~102–115; arg builders
  ~213–254), `src/native/bank/report.rs` (periods ~88–168; day loop ~216–256;
  JSON ~405–448), `src/native/bank/model.rs` (`compute_totals`,
  `breakdown_for`), `src/native/bank/output.rs` (`day_out_in` ~128–145,
  `print_list`), `docs/bank.md` (§Totals, §Commands, §JSON), `docs/stats.md`
  (metric colors, strip/typical/`so_far` semantics), `docs/dashboard.md`
  (badge color bands), `src/native/periods/calendar.rs` (quarter ranges for
  Phase 3), `sase/memory/glossary/{day-strip,stats-strip,period-note,
  bank-row,bank-month-note}.md`.

## 7. Open questions for Bryan

1. Should the `stats.bank_chip` preference gate period badges too (my
   recommendation: yes), or do you want separate day/period toggles?
2. All-time badge: full-journal aggregate, or an explicit "no badge on
   `all_time`" carve-out?
3. Period badge on `waiting_period > 0` but zero money: show `N waiting in
   period`, or stay hidden (my recommendation: hidden — the queue card owns it)?
