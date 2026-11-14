# Bank Badge Redesign Across Every Stats Strip

**Date**: 2026-11-14
**Status**: Research & Design Proposal
**Scope**: `bob-cli` (`src/native/bank/`, `src/native/periods/`), `bob-plugins` (`bob-ledger-tools`), `sase/memory/glossary/` & `docs/`

---

## Executive Summary

Extending and redesigning the bank badge across every Stats Strip is a **strong, high-leverage idea**, provided four structural gaps in the current implementation are resolved first:

1. **The current chip is not inside the Day Strip**: `BobLedgerToolsBankDailyChipMixin` mounts `.bob-bank-daily-plan-host` inside canonical daily `bob-plan` blocks (`241n-plugin-bank-daily-chip.js`), so standalone `bob-day-stats` fences and daily `bob-stats-strip` fences do not show it at all, and period notes have no bank integration.
2. **`bob bank report` cannot align with Period Notes today**: `PeriodKind` (`src/native/bank/report.rs`) only supports `Day | Week | Month | Year`, lacks `Quarter` and `AllTime`, and defines `-y YYYY` as calendar Jan 1–Dec 31—whereas `bob periods show` defines `Year` as an ISO week-year (`Mon W01 – Sun W52/W53`, e.g., `2026` spans `2025-12-29 .. 2027-01-03`).
3. **Literal `$0.00` hiding clashes with `waiting` rows and uncategorized deposits**: In `bob bank report`, uncategorized deposits sit in `unclassified_in_cents` (not `in_cents`), so an imported uncategorized paycheck has `out_cents == 0` and `in_cents == 0`. Hiding the badge whenever `out == $0.00 && in == $0.00` would silently hide both uncategorized same-period money and `N waiting` reminders.
4. **Color needs a non-punitive cashflow grammar**: Coloring outflows bright red collides directly with Bob's own rule in `docs/bank.md` (*"spending is not an error"*) and Bob's UI invariant (*red = Blocked / Over Cap / Missed Closeout*), while today's `.bob-bank-daily-chip` defaults `--bob-bank-accent` to `--bob-area-magenta`, violating `styles.css`'s rule reserving magenta for exact-limit work badges.

**Recommended Solution (Summary)**:
- **Backend**: Extend `bob bank report` with `-p / --period <PERIOD_ID>` (reusing `PeriodId::parse` so `YYYY-Www`, `YYYY-Qn`, `YYYY` [ISO week-year], and `all` match `bob periods show` day-for-day) plus `--summary` (skipping heavy per-day arrays and adding a lightweight period navigation hint), rather than coupling `src/native/periods` directly to `src/native/bank`.
- **Frontend & UI**: Retire `.bob-bank-daily-plan-host` and integrate `.bob-stats-bank-badge` cleanly into the **sub-facts rule band** of both `paintDayStrip` and `paintPeriodStrip` (including standalone `bob-day-stats` and `bob-stats-strip`, excluding `bob-period-parts` tables and future periods), using `span[role="button"]` typography without `all-small-caps` distortion on currency digits.
- **Visibility & Coloring**: Show `out` only when `out_cents > 0`, `in` only when `in_cents > 0`; keep a quiet amber waiting pill if `waiting_period > 0` even when both totals are `$0.00`, otherwise omit completely with zero cold-load skeleton shift. Encode flow with **Restrained Cashflow Polarity**: emerald green for net surplus (`in > out` / `in`-only), neutral warm-stone for routine outflow-only (`out > 0, in == 0`) or breakeven (`in == out`), muted warm terracotta/amber for net deficit (`out > in > 0`)—and never error-red or magenta.
- **Glossary**: Add canonical `bank-badge` strand (`sase/memory/glossary/bank-badge.md` → `docs/reference/glossary.md`).

---

## 1. Current State Audit (What Exists in the Codebase)

Inspecting `bob-cli` and `bob-plugins` reveals why the current chip feels ad-hoc and where the data contracts diverge:

| Layer | Current Reality | Evidence |
| --- | --- | --- |
| **DOM placement** | Mounted as `<div class="bob-bank-daily-plan-host">` inside `.bob-plan` *after* `.bob-day-strip-plan-host`, *before* `TODAY`/`PENDING`/`NEXT`/`READY`. | `241n-plugin-bank-daily-chip.js:107-178`, `239-plugin-day-strip-plan-host.js:280` |
| **Fence coverage** | Shown **only** in canonical daily `bob-plan` blocks. Absent from standalone `bob-day-stats`, daily `bob-stats-strip`, and all Period Note `bob-stats-strip` blocks. | `239-plugin-day-strip-fence.js`, `239-plugin-period-strip-fence.js:374-533` |
| **Text & hiding** | Renders ``BANK · out ${out} · in ${incoming}${waitingAll...}`` even when `$0.00`. Shows `waiting.all` only on `today`; hides only when `teaching_empty === true`, `!bank.md`, future date, or `stats.bank_chip: false`. | `241n-plugin-bank-daily-chip.js:117,201,209`, `241l-plugin-bank-cards-model.js:275-293` |
| **Typography & color** | Inherits `.bob-plan-chip` (`all-small-caps`, `letter-spacing: 0.045em`) overridden to `color: var(--text-muted); font-size: 0.72em`. `bankCardRootHue("bank.md")` checks `[path, "bank.md"]` without walking `parent: "[[cash]]"`, falling back to `"magenta"` (`--bob-area-magenta`). | `styles.css:22-38,8886-8899`, `241m-plugin-bank-cards.js:279-293` |
| **Rule conflict** | `styles.css` states: *"Magenta marks a count exactly at its limit, and no other Bob chip uses that hue."* Yet the bank chip uses magenta by default. | `styles.css:110-116` |
| **Calendar mismatch** | `bob bank report` supports `-D` (day), `-m` (month), `-w` (ISO week), `-y` (calendar `Jan 1–Dec 31`). `bob periods show` supports `Week`, `Quarter` (13/14 ISO weeks), `Year` (ISO week-year `W01 Mon–W52/53 Sun`), and `AllTime`. | `src/native/bank/report.rs:21-26,139-149`, `src/native/bank/dates.rs:92-97`, `src/native/periods/calendar.rs:150-188` |
| **Flow semantics** | `out_cents` sums non-cash, non-`transfer` outflows (`cents < 0`); `in_cents` sums **only** inflows tagged `[cat:: income]` or `[cat:: refund]`. Uncategorized inflows go to `unclassified_in_cents`. | `src/native/bank/report.rs:224-236`, `src/native/bank/model.rs:160-201`, `docs/bank.md:477-483` |

---

## 2. General Critique of the Plan & Justified Adjustments

Overall, turning the ad-hoc daily `bob-plan` chip into a genuine, color-coded **Bank Badge** rendered by **every Stats Strip** is the right direction. It gives Bob a unified peripheral telemetry system across daily notes and period rollups while eliminating stale `$0.00` visual noise.

However, implementing the five requirements *literally without adjustment* would create subtle UX regressions and data bugs. Below are **five justified adjustments** to the requirements:

| # | Original Requirement | Critique / Hidden Failure Mode | Proposed Adjustment |
| --- | --- | --- | --- |
| **A1** | *"if both are `$0.00`, do not show the badge"* | Uncategorized deposits leave `in_cents == 0` (`report.rs:235`), and imported unacked rows in a quiet day/period leave `out_cents == 0 && in_cents == 0`. Hiding unconditionally swallows real same-period uncategorized transactions! Meanwhile, today's legacy `waiting.all` counter (all months) would vanish on no-spend days OR nag on quiet days. | **Hide `$0.00` sides strictly, and hide when no money flowed — *unless* `waiting_period > 0`**: if unacknowledged `[ ]` rows exist *inside that exact day/period*, render a quiet `BANK · N waiting` attention badge so posted uncategorized transactions are never silently invisible. Keep prior-day `waiting_all` off `$0` days (or surface `· M waiting` only when today's badge is already visible / inside `bob-bank`). |
| **A2** | *"start coloring based on in/out values"* (naive green/red intuition) | Most days only have outflows (`$15` lunch). Turning any `out > 0` badge bright red triggers ~90% daily alert noise, violates `docs/bank.md` (*"spending is not an error"*), and collides with red `Blocked` / `Over Plan` / `missed closeout` badges. Furthermore, ~99% of Period Notes have *both* `in > 0` and `out > 0`, so coloring only "in vs out vs both" makes every Period Note look identical. | **Color by Net Direction + Part Semantics, never Error-Red**: Keep `out` digits neutral high-contrast ink (`--text-normal`) and `in` digits green (`--color-green` mix); drive the badge accent/tint by `(in_cents, out_cents)` balance (`in`-only -> emerald green; `in > out` -> mint/green; `in == out` -> neutral slate; `out`-only -> calm warm-stone/muted slate; `out > in > 0` -> muted warm terracotta/amber). Drop `--bob-area-magenta` completely. |
| **A3** | *"rendered by every stats strip"* (placement & loading state) | Mounting a full-row `"Bank · loading"` skeleton inside strips whose `$0.00` post-load rule will *remove* the row causes a jarring 24–28px vertical layout shift 80ms after opening any `$0` day note. Also `bob-period-parts` shares `renderPeriodStripFence` (`surface: "table"`) and is *not* a Stats Strip. | **Zero-flash cold load & strict Strip-only scope**: Paint synchronously from cache (`BankDataMixin` + optional persisted LRU); on a cold miss, occupy `0px` until resolved and fade in cleanly if visible. Exclude `bob-period-parts` (`surface === "table"`) and future periods (`state === "future"`). Integrate the badge into the strip's **sub-facts rule band** rather than `.bob-plan`. |
| **A4** | *"aggregated transactions for that period"* (implicit use of `bob bank report`) | `bob bank report -y 2026` uses calendar year (`Jan 1–Dec 31`), disagreeing with `2026.md` (`2025-12-29 .. 2027-01-03`), and has no Quarter or All-time mode. Also calling `bob bank report` naively across years serializes thousands of empty `days[]` entries. | **Add `-p / --period <PERIOD_ID>` and `--summary` to `bob bank report`**: Leave `-y YYYY` calendar-scoped for CLI backwards-compatibility, and introduce `-p` backed by `PeriodId::parse` so Period Strip bank figures always match `bob periods show` week boundaries to the day. |
| **A5** | *Implicit click behavior* | Daily chip runs `ensureOpenDay(day)`. Week, Quarter, Year, and All-time span 1–12+ months (`bank/YYYY-MM.md` notes) and cannot call `ensureOpenDay`. | **Smart multi-horizon navigation**: Day badges call `ensureOpenDay(day)`. Period badges jump to: (1) the oldest waiting row inside the period (`path:line`), else (2) the single active month note if contained in one month, else (3) `bank.md` hub (`view: queue`). Support Ctrl/Cmd/middle-click for `newLeaf`. |

---

## 3. Deep Design Analysis

### 3.1 Placement & Layout Grammar Across Day and Period Strips

Currently, Day Strips and Period Strips obey two closely related visual grammars (`docs/stats.md`, `styles.css:6777-6792,7575-7725,7913-7943`):

- **Period Strip (`paintPeriodStrip` in `239-plugin-period-strip-charts-render.js:600-656`)** already has three tiers:
  1. `.bob-period-strip-facts`: 5-column metric grid (`WORKED`, `REVIEWED`, `DONE`, `CREATED`, `REVIEW CLOSED`)
  2. `.bob-period-strip-rule-row`: `[ ──────── hairline ──────── ]  [metaText]  [stale]  [●■ chartSwitch]`
  3. `.bob-period-strip-charts`: Roots & Types stacked column charts
- **Day Strip (`paintDayStrip` in `239-plugin-day-strip-render.js:638-736`)** has:
  1. `.bob-day-strip-facts`: 5 metric columns
  2. `.bob-day-strip-mix-row` + `.bob-day-strip-bar`: Roots legend + bar (`metaText` + `●■` switch on the first lane row)
  3. Second `.bob-day-strip-mix-row` + `.bob-day-strip-bar`: Types legend + bar (acts as visual divider before `.bob-plan`'s `TODAY` / `PENDING` / `NEXT` / `READY` badges)

#### Where should the Bank Badge sit inside every strip?

Compare the two serious architectural slots:

1. **Bottom-of-strip Footer Row** (after bars on Day Strip, after charts on Period Strip):
   - *Drawbacks*: On Period Strips (`260–370px` tall), bank activity gets pushed below two stacked charts and x-axis legends. On Day Strips inside `bob-plan`, the bottom 4px bar is explicitly designed as the divider above work badges (`styles.css:6777`); putting a chip below or interrupting that boundary recreates today's clutter right next to `TODAY` / `PENDING` / `NEXT` / `READY`.
2. **Unified Sub-Facts Band (Recommended)** — anchored directly beneath `.bob-*-strip-facts`:
   - **On Period Strips**: Place `.bob-stats-bank-slot` at the leading edge of `.bob-period-strip-rule-row` (ahead of the flex `1` hairline `.bob-period-strip-rule`, `metaText`, and `chartSwitch`).
     - *Desktop (`>= 480px`)*: **Zero vertical height added!** The badge nests into the horizontal rule band (`[Bank badge] ─────── so far · W40–W46 ●■`), staying strictly within `docs/stats.md`'s 260–282 px height budget.
     - *Narrow (`< 460px`)*: `flex-wrap: wrap` lets the bank pill sit cleanly on its own sub-line above `so far · W40–W46 ●■` (suppressing the rule dash when wrapped cleanly via flex-basis or `min-width`).
   - **On Day Strips**: When the badge is visible (`out > 0 || in > 0 || waiting_period > 0`), render a slim `.bob-day-strip-bank-row` directly between `.bob-day-strip-facts` and the first lane row, sharing the exact same hairline rule pattern (`[Bank badge] ───────────`), OR simply left-aligned with quiet `0.35em` breathing room. When hidden (`$0` day), this element is omitted (`display: none` / not mounted), leaving **zero pixel difference** on empty days and preserving `<= 132px` height budget (`docs/stats.md:1659`).
   - **Canonical `bob-plan` blocks**: Because the Day Strip (`bob-day-strip-plan-host`) now owns the Bank Badge across canonical daily notes, standalone `bob-day-stats` fences, AND daily `bob-stats-strip` fences, `.bob-bank-daily-plan-host` in `241n-plugin-bank-daily-chip.js` is retired cleanly with no duplicate rendering.
   - **Edge case — `stats.day_strip: false` on a daily note**: Just as `docs/bob-ledger-tools.md:73` already states *"The chip follows the Day strip"*, disabling `day_strip` hides the strip (and its badge) automatically while explicit `bob-day-stats` fences still show it; disabling `stats.bank_chip: false` hides the bank badge inside *all* strips (Day and Period) while leaving Pomodoro stats intact.

```text
Period Strip (desktop >= 500px — 0px added height):
WORKED       REVIEWED   DONE   CREATED   REVIEW CLOSED
18h 30m      5 of 7     24     9         ✓ done
[ BANK · out $412.80 · in +$2,150.00 ] ─────────── so far · W46  ●■
ROOTS  ● Cash 12h   ● Dev 6h 30m
[ ... stacked bars ... ]

Day Strip (active bank day inside bob-plan):
WORKED   REVIEWED   DONE   CREATED   CLOSEOUT
3h 20m   2 of 3     4      2         ◐
[ BANK · out $13.71 ] ───────────────────────────────────────────
● Dev 2h 30m   ● Cash 50m                        so far · 14:15  ●■
█████████████████████████████░░░░░░░░░░░
■ WORK 2h 10m  ■ OPS 1h 10m
██████████████████████░░░░░░░░░░░░░░░░░░
[TODAY 4/8]  [PENDING 2/10]  [NEXT 5/15]  [READY 11/20]
```

---

### 3.2 Visibility Rules, Edge Cases & Anti-Flicker Lifecycle

Let `out = report.totals.out_cents`, `in = report.totals.in_cents`, `waitPeriod = report.waiting.period`, `waitAll = report.waiting.all`.

1. **Zero-Part Filtering (`>$0.00`)**:
   - Integer cents eliminate float rounding issues: strictly `out > 0` (`>= 1` cent) and `in > 0` (`>= 1` cent).
   - `out > 0 && in == 0`: render only the `out` segment (`BANK  out $13.71`). Never print `in $0.00`.
   - `in > 0 && out == 0`: render only the `in` segment (`BANK  in +$2,500.00`). Never print `out $0.00`.
   - `out > 0 && in > 0`: render both (`BANK  out $13.71  in +$2,500.00`).
2. **When Both `out == 0` and `in == 0`**:
   - **Recommended Rule**:
     - If `teaching_empty === true`, `!bankHubExists`, `state === "future"`, or `stats.bank_chip === false`: **do not show** (and do not spawn `bob bank` on future periods or missing `bank.md`).
     - If `out === 0 && in === 0`:
       - If **`waitPeriod > 0`** (unacknowledged row(s) exist inside *this* day or period—including uncategorized deposits whose `cents > 0` only counted toward `unclassified_in_cents`, or uncategorized outflows): **show `BANK  N waiting`** in quiet warning amber so no transaction inside the period silently vanishes.
       - Otherwise (`out === 0 && in === 0 && waitPeriod === 0`): **do not show the badge**.
     - *Transfers & Cash Account note*: `[cat:: transfer]` and `[cat:: cash]` rows intentionally stay out of `out_cents` and `in_cents` (`docs/bank.md:477-483`), preventing an internal savings-to-checking move from inflating spending/income badges.
3. **`waiting` Display When Badge IS Visible**:
   - Notice the bug-prone asymmetry in today's model (`241l-plugin-bank-cards-model.js:275-293`): `waitingAll` is shown on `today`, whereas periods have `waiting.period`.
   - On **Period Strips** (and past Day Strips): append `· ${waitPeriod} waiting` **only when `waitPeriod > 0`**. (Most closed periods have `waitPeriod === 0`, keeping the badge ultra-clean!).
   - On **Today (`day === today`)**: if `waitPeriod > 0`, show `${waitPeriod} waiting` (or if `waitPeriod === 0 && waitAll > 0`, optionally surface `· ${waitAll} queue` in tooltip/text so cross-month backlog stays discoverable without cluttering `$0` days). Keeping **`waitPeriod`** across *all* strips (with `waitAll` in the `title` tooltip on today!) makes Day and Period behavior 100% consistent.
4. **Loading, Stale, and Error States Without Vertical Layout Jump (CLS)**:
   - On **cold initial load** (`report === null`): **render nothing (`0px`)** instead of inserting a `"Bank · loading"` row that vanishes 80ms later on `$0` days.
   - If an already-rendered badge transitions to **stale** during background refresh (`result.stale === true`): dim opacity softly (`opacity: 0.72`) and keep `border-style: dashed` on the start bar with `title="Updating · last good values shown"`.
   - If `bob bank` **fails**:
     - With cached report: keep cached badge visible in stale ink + quiet tooltip/status indicator (`title="Bank refresh failed; cached totals shown"`).
     - Without cached report: **only** emit a quiet non-blocking console/diagnostic warning (or inline mute link *only* when user hovers/triggers retry via palette, or on explicit command), rather than injecting an ugly `"Bank unavailable"` box on every daily/period note when the user intentionally skips bank setup or hasn't upgraded `bob`. (*Wait*: if `bank.md` exists and `bob bank` exits non-zero unexpectedly, a tiny discrete `BANK · unavailable` muted retry link inside the strip's meta/rule band—where `refresh failed` already lives—is low-noise and aids debugging!)

---

### 3.3 Color System ("Think Hard About Which Colors Are Appropriate When")

#### Why Color Choice Here Is Non-Trivial
Three constraints collide if we pick colors carelessly:
1. **Bob Bank's Explicit Color Contract (`docs/bank.md:450-452`)**:
   > *"inflows are green and outflows are neutral, because spending is not an error. State is always carried by text and shape, never by color alone."*
2. **Bob Work Badge Token Reservation (`styles.css:110-149`)**:
   - **Red** (`--task-status-blocked`, `--color-red`): Over-cap, Blocked, Missed Closeout, Sync Error.
   - **Magenta**: Reserved exclusively for exact-at-limit counts (*"and no other Bob chip uses that hue"*).
   - **Orange** (`--color-orange`): `PENDING`, `ROTTEN` escalation warnings.
3. **Asymmetric Base Rates Between Day and Period**:
   - On **Daily Notes**, ~85–90% of active days are `out > 0, in == 0`. Painting every grocery/coffee day red (or orange) floods daily notes with false urgency right beside `WORKED`/`DONE`/`TODAY` and blurs into `PENDING`/`Over Plan`.
   - On **Period Notes**, ~95%+ of Weeks, Quarters, Years, and All-time spans have **both `out > 0` and `in > 0`**. If mixed states share one static hue (say blue or purple), then a `+$8,000` surplus quarter and a `-$4,000` drawdown quarter look visually indistinguishable!

#### Recommended Two-Layer Semantic Palette

Split color responsibility cleanly across **Token Ink (inside the badge)** and **Flow Balance Accent (the pill's border & wash)**:

**Layer 1 — Per-Part Ink (Unambiguous, Literal)**
- **`in` (`+$…`)**: Semantic Green — `color-mix(in srgb, var(--color-green, var(--text-success, #3f8f5f)) 82%, var(--text-normal))`. Vivid, crisp `>= 4.5:1` contrast in both Obsidian `.theme-light` and `.theme-dark`, matching `.bob-bank-metric-in` (`styles.css:8832`) and `bob bank list` terminal output (`src/native/bank/output.rs:164`).
- **`out` (`$…`)**: Crisp Primary Ink (`--text-normal`) for the dollar digits, paired with muted label/direction (`out` in `--text-muted` or soft warm accent when net negative). Spending numerals stay effortless to read and never look like errors.
- **`BANK` label & `out`/`in` prepositions**: Muted structural ink (`--text-muted`), uppercase `BANK` + lowercase `out`/`in` (see Typography §3.4).

**Layer 2 — Badge Chrome (`--bob-bank-accent` driving `2px` inline-start bar, `1px` hairline border, and subtle `8%–11%` tinted surface)**

| Condition | Financial Meaning | Accent Token (`--bob-bank-accent`) | Background Wash | Rationale & Visual Effect |
| --- | --- | --- | --- | --- |
| **1. `in > 0 && out == 0`** | Pure inflow day / surplus period | `--color-green, var(--bob-area-green, #008300)` | `11%` green | Instant, calm celebration of paydays/refunds; 100% aligned with Bob's `inflows = green`. |
| **2. `in > 0 && out > 0 && in > out`** | Active period/day, **Net Positive** | `color-mix(in srgb, var(--color-green, #008300) 78%, var(--bob-area-aqua, #1baf7a))` | `9%` teal-green | Signals positive net savings cleanly on Period Notes while visibly nodding to mixed activity (cool mint/emerald vs pure green). |
| **3. `in > 0 && out > 0 && in == out`** | **Breakeven** (`net == $0.00`) | `--bob-area-blue, #2a78d6` (or neutral `--text-muted`) | `7%` cool slate-blue | Calm, exact balance (e.g., reimbursed expense). Distinct from both deficit and zero-activity grey. |
| **4. `out > 0 && in == 0`** | **Routine Outflow-Only** (most weekdays) | `color-mix(in srgb, var(--color-orange, #d9822b) 35%, var(--text-muted))` (Neutral Warm Stone) | `6%` subtle stone (or `var(--background-secondary)`) | **Crucial win**: Clearly reads as active ledger telemetry (not disabled grey `0` and NOT angry red/orange!), respecting `docs/bank.md` *"spending is not an error"*. |
| **5. `out > 0 && in > 0 && out > in`** | **Net Negative / Drawdown** (e.g., spend > income in a period) | `color-mix(in srgb, var(--color-red, #c65367) 62%, var(--color-orange, #d9822b))` (Restrained Terracotta / Muted Coral) | `9%` soft coral | Signals "net outflow exceeded inflows" unmistakably on Period/Day strips via warm terracotta/rose—noticeably warmer than neutral stone, yet visually restrained compared to harsh crimson error-red (`--task-status-blocked`). |
| **6. `out == 0 && in == 0 && waitPeriod > 0`** | Uncategorized / unacked rows only | `--text-warning, var(--color-yellow, #c98500)` | `9%` soft amber | Matches `.bob-bank-heat-waiting` warning dot (`styles.css:8865`); prompts triage without pretending dollar amounts are `$0.00`. |

**Why this palette works in every context**:
- **Accessibility & `forced-colors`**: State never depends on color alone (`docs/bank.md:452`): `out` vs `in +$` always carries explicit words and `+` sign, plus directional polarity arrows or crisp separation (`·`). Under `@media (forced-colors: active)`, use `border: 1px solid CanvasText` and `LinkText` for interactive affordance, matching `.bob-day-strip` (`docs/stats.md:1449`).
- **Light & Dark Theme Parity**: Because every wash uses `color-mix(in srgb, var(--bob-bank-accent) 9%, transparent)` over Obsidian's native background and mixes accent ink with `--text-normal`, contrast stays crisp in default Obsidian Light, Dark, and community themes.
- **Alternative Considered & Rejected (Strict Out-Red / In-Green Dichotomy)**: Rejected because making every `out > 0, in == 0` weekday badge coral/red makes daily notes visually noisy for no actionable reason (`$4.50` coffee is normal life, not a cashflow warning). Treating **pure outflow-only days** calmly as neutral warm stone while reserving **terracotta/coral** for **net-deficit periods/mixed days (`out > in > 0`)**—or optionally allowing an opt-in warm rose accent if magnitude sensitivity is ever added—gives the highest signal-to-noise ratio. *(If Bryan prefers `out > 0, in == 0` to also carry soft coral rather than warm stone so single-direction outflow and inflow mirror each other visually at a glance, State 4 simply shares State 5's restrained terracotta accent at lighter `6%` opacity rather than neutral stone; this is a single CSS variable swap.)*

---

### 3.4 Visual Craft, Typography & Micro-Interaction

#### Fixing Current Typographic Issues
Currently `.bob-bank-daily-chip` inherits `.bob-plan-chip`:
```css
font-variant-caps: all-small-caps;
font-weight: 650;
letter-spacing: 0.045em;
color: var(--text-muted);
```
Rendering lowercase `out`, `$13.71`, and `waiting` inside `all-small-caps` compresses vertical rhythm and flattens visual hierarchy between label and number.

#### Proposed Component Anatomy & CSS Spec

Use a `<span role="button" tabindex="0" class="bob-stats-bank-badge" data-flow="...">` (avoiding `<button>`, consistent with `.bob-day-strip`'s "no `<button>` elements inside strip" rule in `docs/stats.md:1652` and preventing theme button chrome collisions; calling `e.preventDefault()` on `mousedown` so Obsidian Vim normal-mode selection is never interrupted).

**Markup structure**:
```html
<div class="bob-stats-bank-slot" data-flow="net-negative">
  <span class="bob-stats-bank-badge" role="button" tabindex="0"
        aria-label="..." title="...">
    <span class="bob-stats-bank-label">BANK</span>
    <span class="bob-stats-bank-part is-out">
      <span class="bob-stats-bank-dir">out</span>
      <span class="bob-stats-bank-val">$1,420.50</span>
    </span>
    <span class="bob-stats-bank-sep" aria-hidden="true">·</span>
    <span class="bob-stats-bank-part is-in">
      <span class="bob-stats-bank-dir">in</span>
      <span class="bob-stats-bank-val">+$2,150.00</span>
    </span>
    <!-- omitted when waitingPeriod === 0 -->
    <span class="bob-stats-bank-sep" aria-hidden="true">·</span>
    <span class="bob-stats-bank-waiting">2 waiting</span>
  </span>
</div>
```

**Typography & Polish**:
- `.bob-stats-bank-badge`: `display: inline-flex; flex-wrap: wrap; align-items: baseline; gap: 0.35em; padding: 0.2em 0.6em 0.22em 0.55em; border-radius: 6px; border: 1px solid color-mix(in srgb, var(--bob-bank-accent) 26%, var(--background-modifier-border)); border-inline-start: 2.5px solid var(--bob-bank-accent); background: color-mix(in srgb, var(--bob-bank-accent) 9%, transparent); font-family: var(--font-interface); font-size: 0.8em; line-height: 1.3; cursor: pointer; font-variant-numeric: tabular-nums lining-nums;`
- `.bob-stats-bank-label`: `color: var(--text-muted); font-size: 0.85em; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase;` (no `all-small-caps` bleed into currency!)
- `.bob-stats-bank-dir`: `color: var(--text-muted); font-size: 0.9em; font-weight: 500; margin-inline-end: 0.22em;`
- `.bob-stats-bank-val`: `font-weight: 650; letter-spacing: -0.01em; color: var(--text-normal);` (with `.is-in .bob-stats-bank-val` tinted semantic green!)
- Hover / focus: border intensifies cleanly to `48%`, gentle background lift (`14%`), `outline: 2px solid var(--interactive-accent)` on `:focus-visible`.
- **Rich Hover Tooltip (`title`) & `aria-label`**:
  On hover over any badge, show complete ledger context without crowding inline text:
  - Day: `2026-11-14 · Out $42.50 · In +$0.00 · Net -$42.50 · Open bank/2026-11.md`
  - Period: `2026-Q4 (Sep 28 – Jan 3) · Out $18,412.10 · In +$24,100.00 · Net +$5,687.90 (transfers $1,200.00 · unclassified in +$150.00 excluded) · 2 waiting`
  Notice how putting **Net**, **Transfers**, **Unclassified**, and **Cash traced** in the tooltip makes the compact `out` / `in` badge deeply informative without cluttering the strip!

---

## 4. Backend & Frontend Architecture

### 4.1 Architecture Comparison: Separate `bob bank report -p` vs. Embedding in `bob periods show`

| Criterion | **Option A: `bob bank report -p <PERIOD_ID> --summary` via `BankDataMixin` (Recommended)** | Option B: Embed `bank` summary inside `bob periods show` JSON |
| --- | --- | --- |
| **Vault Invalidation Cost** | Editing `bank/2026-11.md` refreshes only lightweight bank files (`scan::scan_bank`, milliseconds). Does **not** re-scan years of Pomodoro daily notes! | Editing `bank/2026-11.md` invalidates `periodStripCache`, forcing `bob periods show all` to re-parse the entire Pomodoro/task vault just to update a dollar figure. |
| **Domain Coupling** | `src/native/periods/` and `src/native/stats/` keep zero dependency on `src/native/bank/` (matching today's clean separation). | Couples Stats & Periods schema and execution to Bank config (`bank.md` errors could leak into `bob periods show`). |
| **Progressive Rendering** | Period Strip charts & facts render immediately from `bob periods show` cache; bank badge hydrates independently without blocking charts. | Slower `bob periods show` waits on both scanners; day notes still need `bob bank report -D` separately anyway. |
| **Date Parity** | Solved cleanly by reusing `crate::native::periods::calendar::PeriodId::parse` inside `bob bank report -p`! | Automatic, since both use the same `PeriodId`. |
| **Subprocess Count** | Two lightweight calls on initial Period Note load (`bob periods show` + `bob bank report -p ... --summary`); skipped entirely if `!bankHubExists()`. | One call on Period Note load. |

**Conclusion**: **Option A wins decisively** on cache independence, edit responsiveness, module boundaries, and unified sharing between Day Strips and Period Strips.

---

### 4.2 Exact Changes Needed in `bob-cli` (Rust)

1. **Extend `src/native/bank/cli.rs` & `report.rs`**:
   - Add `-p, --period <ID>` (mutually exclusive with `-D`, `-m`, `-w`, `-y`) using `crate::native::periods::calendar::PeriodId::parse(&raw)`:
     - `PeriodId::Week` -> ISO `Mon..Sun` (`PeriodKind::Week`)
     - `PeriodId::Quarter` -> ISO 13/14-week span (`PeriodKind::Quarter`)
     - `PeriodId::Year` -> **ISO week-year** `W01 Mon..last_week Sun` (`PeriodKind::PeriodYear` or `"iso_year"` / `"year"` — note existing `-y YYYY` stays calendar Jan 1–Dec 31 for CLI compatibility!)
     - `PeriodId::AllTime` -> Earliest bank transaction date (or `accounts.*.start` / `today` fallback if empty) through `today` (`PeriodKind::AllTime`, key `"all"`). Notice: `period.start` for `AllTime` MUST derive from actual bank rows / account starts cleanly rather than scanning all daily notes!
   - Add `--summary` flag to `bob bank report`:
     - When set, skip building per-day `days[]` entries while **retaining `"days": []` as an empty array** (critical because `241h-plugin-bank-decode.js:438` validates `Array.isArray(body.days)`) and optionally emit `breakdown: []`. Why critical: on `2026` (371 days) or `all` (multi-year, 1,000+ days), building and serializing 1,000 zero-filled day JSON objects is pure waste when the badge only needs `totals`, `waiting`, `flagged`, and navigation targets.
   - Add additive navigation metadata in `report` JSON (when rows/months exist):
     - `waiting_target`: `{ "path": "bank/2026-10.md", "line": 42, "date": "2026-10-29" }` for the **oldest waiting row inside the requested period** (distinct from global `waiting.oldest`), so clicking a Period Bank Badge with `N waiting` jumps straight to that exact row in Obsidian!
     - `single_month`: `"bank/2026-11.md"` when every transaction in the period falls inside one `YYYY-MM` (else `null`, letting click fall back to `bank.md`).
2. **Documentation & Glossary Updates (`bob-cli`)**:
   - Follow `/sase_memory_write` to create `sase/memory/glossary/bank-badge.md`, run `sase memory init`, and run `just docs-gen` to regenerate `docs/reference/glossary.md` (and `AGENTS.md`).
   - Update `docs/bank.md` (`-p / --period`, `--summary`, updated badge color policy reflecting cashflow states while keeping *"spending is not an error"* & never error-red).
   - Update `docs/stats.md` & `docs/periods.md` documenting the Bank Badge tier inside every Stats Strip (`stats.bank_chip`, excluding `bob-period-parts` and future states).

---

### 4.3 Exact Changes Needed in `bob-plugins` (`bob-ledger-tools`)

1. **`241h-plugin-bank-decode.js`**:
   - Extend `bankBuildArgs(options)` to support:
     - `period`: pushes `["-p", String(options.period)]`
     - `summary: true`: pushes `["--summary"]`
   - Keep `days` validation gracefully accepting empty `days: []` when `summary: true` (verify `bankDecodeReport` allows empty `days` array).
2. **`241l-plugin-bank-cards-model.js`**:
   - Replace/generalize `bankCardDailyChipModel` into `bankStripBadgeModel(report, context)` (`{ kind: "day" | "week" | "quarter" | "year" | "all", dateOrPeriod, today }`):
     - Reads `outCents = report.totals.out_cents` (for period) or `day.out_cents` (for day), `inCents`, `waitingPeriod` (`day.waiting` on days; `report.waiting.period` on periods), `waitingAll`, transfers/unclassified/cash metadata for tooltips, and `waitingTarget` / `singleMonth`.
     - Computes `showOut = outCents > 0`, `showIn = inCents > 0`, `visible = showOut || showIn || waitingPeriod > 0`.
     - Computes semantic `flow`: `"in-only" | "net-positive" | "balanced" | "out-only" | "net-negative" | "waiting-only"`.
3. **`241j-plugin-bank-data.js`**:
   - Key period subscriptions cleanly (`report:period:${periodId}:summary`). Already invalidates all `"report:"` keys when `bank.md` or `bank/*.md` changes (`bankHandleFileEvent`), deduplicates concurrent requests across panes, and cancels stale generations cleanly.
4. **Retire `241n-plugin-bank-daily-chip.js`'s `.bob-plan` injection; unify into Strip Bank Controller**:
   - Register every mounted Day Strip (`dayStripViews` / standalone `bob-day-stats` / `periodStripPaintDay`) and every non-future Period Strip (`periodStripViews` with `surface !== "table"`).
   - Inject/update `.bob-stats-bank-slot` in the **sub-facts band** of `.bob-day-strip` and `.bob-period-strip`:
     - **Important repaint invariant**: Preserve the bank slot across Stats-only repaints (`paintDayStrip` / `paintPeriodStrip` reads latest cached `bankBadgeModel` if available so `replaceChildren()` never blanks the badge), AND allow bank-only updates to patch just `.bob-stats-bank-slot` without rebuilding Charts/SVG/Legend fitters!
   - Guard all mounts with: `statsReadConfigValue("bank_chip") !== false`, `vault.getAbstractFileByPath("bank.md")`, non-future period/date, and desktop spawn availability.
5. **`styles.css`**:
   - Add `.bob-stats-bank-slot`, `.bob-stats-bank-badge`, `[data-flow="..."]` CSS rules using `--bob-bank-accent` in both `.theme-light` and `.theme-dark` plus `@media (forced-colors: active)`.
   - Remove `--bob-area-magenta` default from `.bob-bank-daily-chip` / `.bob-bank-daily-plan-host` once retired (keeping `bob-bank` month/queue cards' root hue untouched, though fixing `bankCardRootHue` to walk `parent: "[[cash]]"` is a nice bonus cleanup!).

---

## 5. Proposed Glossary Term (`bank-badge`)

For `sase/memory/glossary/bank-badge.md` (regenerated into `docs/reference/glossary.md` via `sase memory init` + `just docs-gen`):

> ### Bank Badge {#bank-badge}
>
> *Aliases: bank chip, daily bank chip.*
>
> The read-only financial flow indicator rendered inside every non-future [Stats Strip](#stats-strip)—on canonical daily notes and `bob-day-stats` fences for that day, and on [Period Note](#period-note) `bob-stats-strip` blocks for that ISO week, quarter, ISO year, or all time. Driven live from `bob bank report` (`-D` for days, `-p` for periods) without modifying note bytes, it shows only positive `out` and `in` totals (`> $0.00`), omits zero sides, and hides itself when neither exceeds `$0.00` unless unacknowledged [Bank Row](#bank-row)s fall inside that period (`N waiting`). Cash-account entries and `[cat:: transfer]` rows stay out of `out` and `in`, while `[cat:: income]` and `[cat:: refund]` count toward `in`; badge color reflects flow direction and net balance (emerald for net surplus, warm neutral for routine outflows or even balance, muted coral/terracotta for net drawdown, amber for waiting-only triage—never error-red for ordinary spending and never `bob-plan` exact-limit magenta) while always carrying text labels and `+` signs. Controlled by `stats.bank_chip` (default on) and `bank.md` presence. Clicking opens that day's heading in its [Bank Month Note](#bank-month-note), a period's oldest waiting row, or `bank.md`. Not a [Bank Row](#bank-row), a `bob-bank` card, a `bob-plan` work badge, or part of `bob-period-parts`. See `docs/bank.md`.

*(Implementation note: `sase/memory/glossary/bank-badge.md` must use wiki links such as `[[stats-strip]]`, `[[period-note]]`, `[[bank-row]]`, and `[[bank-month-note]]` and follow `/sase_memory_write` approval rules before running `sase memory init` and `just docs-gen`.)*

---

## 6. Verification & Rollout Plan

1. **Rust Unit & Golden Tests (`bob-cli`)**:
   - Test `bob bank report -p <YYYY-Www|YYYY-Qn|YYYY|all> --summary -f json` across ISO week-year boundaries (`2025-12-29` included in `2026` and `2026-Q1`, `2026-W53` in `2026-Q4`), `waiting_target` selection, `unclassified_in` exclusion, and `teaching_empty`.
2. **Plugin Unit Tests (`bob-plugins`)**:
   - Test `bankStripBadgeModel` across all 6 `flow` states, `$0.00` / `$0.01` boundary (`out_cents: 0, 1`, `in_cents: 0, 1`), `waitingPeriod > 0` fallback when both cents are `0`, `bob-period-parts` exclusion, future-date suppression, and repaint preservation across Stats-only vs Bank-only cache invalidation.
3. **Visual Matrix Check**:
   - Inspect light and dark Obsidian themes at narrow (`320–410px`) and wide (`700px+`) pane widths on daily, weekly, quarterly, yearly, and `all_time` notes to confirm contrast (`>= 4.5:1`), zero cold-load layout shift on `$0` days, and single-line rule-row harmony on Period Strips.
