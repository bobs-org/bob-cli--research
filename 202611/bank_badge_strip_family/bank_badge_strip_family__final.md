# Bank badge for the whole stats-strip family — consolidated research

**Lead researcher consolidation · 2026-11-14.**
Merged from five independent reports in this directory —
[cdx](bank_badge_strip_family__cdx.md), [cld](bank_badge_strip_family__cld.md),
[grk](bank_badge_strip_family__grk.md), [mus](bank_badge_strip_family__mus.md),
[gem](bank_badge_strip_family__gem.md) — plus my own verification of every
load-bearing code claim against bob-cli (`5b1b6d59`) and bob-plugins
(`src/native/bank/*`, `src/native/periods/calendar.rs`,
`plugins/bob-ledger-tools/src/241n-plugin-bank-daily-chip.js`, `styles.css`,
`docs/bank.md`, `docs/stats.md`, the glossary strands for Day Strip, Stats
Strip, Period Note, Bank Row, and Bank Month Note).

## Verdict

**Build it. All five researchers and I agree this is a good idea — but the
request as literally written has three real bugs, and each needs a called-out
adjustment before implementation:**

1. **Hide-when-both-zero can swallow money that needs attention.** `in_cents`
   counts only `income`/`refund` inflows (verified, `report.rs` day loop and
   `compute_totals`), so an imported-but-unfiled paycheck reports
   `in = out = $0.00`. A literal hide rule makes the day with the most
   actionable money look like nothing happened. The fix is a waiting-aware
   hide rule (§Adjustments A1–A2).
2. **Naive in/out coloring fights three existing Bob contracts.**
   `docs/bank.md:452`: inflows are green, outflows are neutral, "spending is
   not an error. State is always carried by text and shape, never by color
   alone." Red already means over-cap/blocked/missed; magenta is reserved for
   exactly-at-cap (`styles.css:114` — which today's chip already violates by
   defaulting to `--bob-area-magenta`). The palette must be chosen inside
   those contracts (§Color).
3. **Period aggregation has no honest data source today.** `bob bank report`
   supports day/week/month/calendar-year only (verified: `PeriodKind` in
   `report.rs:21`, `year_range` = Jan 1–Dec 31 in `dates.rs:92`). Period notes
   use ISO week-years: `2026.md` spans **2025-12-29 → 2027-01-03**. Wiring a
   year strip to `-y 2026` would be silently wrong at every year boundary, and
   quarters/all-time have no bank period at all. A small additive CLI change
   is required (§Data contract).

One more finding only cld caught, and it matters a lot right now: **bank
tracking began 2026-11-11** (one checking account, weekly Monday QFX import).
Without a coverage marker, `2026.md` and `all_time.md` would render one week
of transactions as if it were the whole year — "2026: in $0 · out $1,300"
reads like a frugal year instead of a one-week sample. Partial-coverage
display is a correctness feature, not polish (§Adjustments A5).

## What exists today (verified)

| Fact | Evidence |
| --- | --- |
| The "bank badge" is today the **bank daily chip**: a `<button type="button" class="bob-plan-chip bob-bank-daily-chip">` mounted in a sibling host (`.bob-bank-daily-plan-host`) right after the Day-strip host inside canonical daily `bob-plan` blocks only. No fence or period note shows it. | `241n-plugin-bank-daily-chip.js:206-221` |
| It always prints both sides — `BANK · out $X · in +$Y` — including `$0.00`, plus `N waiting` on today only, where N is `waiting.all` **across all months**, not that day's. | `241n…:209`, `241l-plugin-bank-cards-model.js` (`bankCardDailyChipModel`) |
| Its chrome is the bank hub's area hue with a **magenta fallback**; amounts are uniform `--text-muted`. No value-based color anywhere. | `styles.css:8887-8895` |
| Magenta is documented as reserved: "marks a count exactly at its limit, and no other Bob chip uses that hue." | `styles.css:114` |
| Data: `bob bank report -D <day> -f json`, `days[].out_cents/in_cents`. Day in/out follow the keep-apart rules: cash-account rows, `[cat:: transfer]` rows, and `$0.00` rows never count; `in_cents` takes only `income`/`refund`; uncategorized inflows land in `totals.unclassified_in_cents` (totals only — `days[]` has no per-day unclassified field). | `report.rs:216-256`, `report.rs:423-424` |
| Report JSON already carries `waiting: {period, all, oldest}` and per-day `waiting` — so **period-scoped waiting needs no CLI change**. | `report.rs:442-448` |
| `bob bank report` period kinds: Day, Week (ISO), Month (calendar), Year (**calendar**). No quarter, no all-time. | `report.rs:21-26`, `dates.rs:92` |
| `PeriodId::parse` already accepts `YYYY-Www`, `YYYY-Qn`, `YYYY` (ISO week-year), `all`/`all_time`/`all-time`, and vault paths — a ready-made parser to reuse. | `periods/calendar.rs:56-81` |
| Periods' existing all-time span starts at the **earliest canonical daily note's week** — wrong lower bound for money, since bank rows are independent of daily notes. | `periods/report.rs:441-444, 2227` |
| Strips forbid buttons and card chrome; interactive targets are `span[role=link/button]`; "no card, border, background, shadow, or button." The current chip breaks this (it's a `<button>` with a filled wash). | `docs/stats.md:1652,1658` |
| Click runs `bankApi().ensureOpenDay(day)` — a guarded write that can create a bank note/heading. | `241n…:219` |
| Acknowledgment is now a **weekly Monday chore** (QFX import + Category-card walk). Non-cash accounts require a `start: YYYY-MM-DD`; an import journal exists — so coverage dates are computable. | `docs/guides/acknowledge-bank-transactions.md:3,11`, `bank/config.rs:69,401`, `bank/journal.rs` |
| Error/loading states today: `Bank · loading` flash, `Bank unavailable`, stale = dashed border + note. A missing day in JSON is `day-unavailable`, never `$0.00` — that refusal must survive. | `241n…:195-205`, `241l…` |
| Config gate: `stats.bank_chip` (default on), independent of `stats.day_strip`. | `241n…`, plugin docs |

## Where the five reports disagreed, and how I resolved it

This is the heart of the consolidation; everything else was broadly shared.

### 1. Color (the big one)

| Researcher | Proposal |
| --- | --- |
| cdx | Teal In / warm-copper Out token inks, neutral shell; reject any net-based chrome |
| cld | In green ink, Out normal ink; **chrome tints green only when In > Out**, neutral otherwise; never red |
| grk | Token-only: In green, Out neutral slate, waiting amber; optional single-sided washes; never net-color |
| mus | Token-only (same inks as grk) but **keep the magenta/area-hue identity chrome** |
| gem | Token inks + a **six-state net chrome**: emerald / mint / slate-blue / warm-stone / terracotta (net deficit) / amber |

**Resolution — token inks everyone agrees on, plus cld's one-way net tint:**

- **In amount: green ink** — but *not* raw `--color-green`. cld computed (and
  I accept) that Obsidian's default light-theme green as text is **2.61:1**
  against white — a WCAG AA failure. Use
  `color-mix(in srgb, var(--color-green) 60%, var(--text-normal))`
  (≈5.2:1 light, ≈9.3:1 dark), exposed as one `--bob-bank-in-ink` token and
  reused to fix the month card's `.bob-bank-metric-in strong`, which has the
  same contrast problem today.
- **Out amount: normal body ink.** Spending is not an error — this is Bob's
  written contract, and four of five researchers independently landed on it.
- **Waiting: `--text-warning` amber** (matches the month card's waiting dot).
- **Chrome: neutral ink-tint normally; a quiet green border+wash only when
  In > Out.** This is the honest reading of Bryan's "color the badge based on
  the in/out values": paydays and surplus weeks/quarters/years glow; ordinary
  spending stays calm; there is **no punishment color** in the system. "In >
  Out" is literally true whenever shown (both numbers are visible beside it),
  it scales from a day to all-time with one rule, and it degrades safely: a
  colorblind or forced-colors reader loses only emphasis, never information,
  because labels and `+` carry the meaning.
- **Never red, never magenta, never color alone.** Retire the area-hue/magenta
  chrome on the badge (it collides with the documented at-cap reservation);
  the bank month/queue cards keep their hue — they're bank surfaces, not
  work-chip neighbors. mus's "keep magenta for family identity" loses to the
  written reservation in `styles.css:114`.

**Rejected:** gem's terracotta net-deficit state (a judgment color for what is
usually just payday timing — most periods will read "deficit" while income
arrives uncategorized; it recreates the alarm problem one step removed);
cdx's teal/copper (handsome, but it introduces two new hues against an
existing repo-wide green-inflow convention — the month card, Category card,
and `bob bank list` already green inflows); whole-badge red/green by net
(everyone rejected); magnitude heat (no common scale across day and year).

If even the one-way green tint feels too evaluative, the fallback everyone
supports is pure token ink with no net chrome at all — that's a one-line CSS
decision, and I'd ship the tint behind that understanding.

### 2. Waiting count

| Researcher | Proposal |
| --- | --- |
| cdx | Remove waiting from the badge; separate queue action on today |
| cld / gem | **Period-scoped waiting on every badge**; waiting-only badge when money is 0/0 |
| grk / mus | Keep `waiting.all` on today only; period badges never show waiting |

**Resolution — period-scoped waiting everywhere (cld/gem).** One scope rule:
*the badge describes exactly its strip's period.* Today's note shows that
day's waiting; a week note shows that week's. This fixes the real bug in
today's chip (an all-months count presented on a single day's note), keeps
the hide rule safe (an unfiled paycheck day shows `BANK · 1 waiting` instead
of vanishing), and — decisive, in my view — **matches the new weekly
acknowledgment ritual**: the Category-card walk is a Monday/week-note chore
now, so a week-scoped `N waiting` on the week strip sits exactly where that
work is done. The data is already in the JSON (`waiting.period`, per-day
`waiting`): zero CLI cost. The all-months number moves to today's tooltip,
and `bank.md`'s queue card remains the global nudge. cdx's worry (a yearly
"4 waiting" is a stale-unit nag) is answered by the fact that a closed period
with waiting rows is precisely where leftover rows hide.

Residual gap, worth documenting rather than blocking: an *acknowledged but
uncategorized* inflow is invisible to both `in_cents` and `waiting`. The
Category card ticks and files in one gesture, so this needs a deliberate
manual tick-without-category; if it ever bites, mus's per-day
`unclassified_in_cents` JSON addition is the targeted fix.

### 3. Placement

Inside the strip as a last row (grk), nested into the rule band for zero
height (gem), or a **sibling host immediately after each strip host**
(cld/mus, and today's shipped pattern)?

**Resolution — sibling host.** It keeps bank and stats lifecycles fully
decoupled (a strip repaint replaces its own children and can never blank the
badge; a bank refresh never repaints charts), it's what the daily mount
already does, and it avoids gem's repaint-invariant complexity inside two
strip painters. "Rendered by every stats strip" reads naturally as "follows
every strip": Day strip in `bob-plan` (today's slot, nothing moves),
`bob-day-stats` fences, and every `bob-stats-strip` fence on week, quarter,
year, and all-time notes. Never in `bob-period-parts` (a different surface),
never on future periods, mobile, or embeds where strips already don't render.
gem's zero-height rule-band nesting is clever but buys ~20px at the cost of
split ownership — not worth it.

### 4. CLI shape

New `bob bank summary` command (cdx) vs `bob bank report -p/--period` +
`-s/--summary` (cld/grk/gem) vs phased reuse of `-w/-m/-y` (mus)?

**Resolution — `-p/--period` + `-s/--summary` on the existing `report`.**
Three of five landed here independently; it reuses `PeriodId::parse` rather
than forking a second calendar, keeps one command surface, and `-s` (skip the
per-day `days[]` rows, keeping `"days": []` so the plugin decoder's
`Array.isArray` check still passes — gem's catch) bounds the all-time payload.
mus's phasing is partly unsound: its Phase 2 would wire year strips to `-y`,
which is the calendar/ISO mismatch all four others flagged — but mus's kernel
is right that **week badges work today with `-w`**, which gives a useful
compatibility story. `-p` is mutually exclusive with `-D/-m/-w/-y`; `-y`
keeps its calendar meaning for statements, and help text must name the
contrast (`-p 2026` = ISO week-year; `-y 2026` = calendar year). **All-time
for bank = the bank universe** (earliest account `start` / earliest row
through today), not the periods tree's earliest-daily-note week — money
predates and outlives daily notes (cdx + grk, verified against
`periods/report.rs`).

### 5. Who computes presentation

cld wants bob to emit a full `badge` object (visibility, tone, display
strings, tooltip, aria words, click target); the other four have bob emit
semantics and the plugin derive presentation.

**Resolution — bob emits semantics, the plugin derives presentation.** Bob
owns every *value*: period identity/span/so-far, exact integer cents, waiting
counts, coverage dates, and navigation metadata (gem's `waiting_target` =
oldest waiting row's path:line in the period, and `single_month` when the
period's rows live in one bank month note). The plugin derives
visibility/tone from cents by the documented rule and owns copy — exactly how
the work-badge tones already work (`075-work-badge-tone.js`), and it keeps
copy iteration out of the daily release train. Two cld details survive on
their merits: (a) **reuse `compute_totals` for the period numbers** —
`report.rs` currently computes day in/out in a second code path, and the
badge must never be able to drift from the month card; (b) **older-bob
degradation**: bob-cli ships on the daily train and plugins deploy via
`bob plugins sync`, so the plugin can reach the vault before `-p` exists —
day/week badges keep working via `-D`/`-w`, period badges on quarter/year/
all-time quietly render nothing, one `console.warn` per session.

## Adjustments to the requirements (explicit call-outs)

| # | Requested | Shipped as | Why |
| --- | --- | --- | --- |
| **A1** | Show in/out parts only when > $0.00 | Yes — compared on **integer cents** (`> 0`), never on formatted strings or floats; $0.01 shows. Invalid/missing/unsafe cents stay refusals (`day-unavailable`), never a zero-dollar success. | Totals are `i64` cents; the decoder already refuses schema mismatches. |
| **A2** | Hide the badge when both are $0.00 | Hide only when `in == 0 && out == 0` **and the period's waiting count is 0**. Otherwise render a quiet `BANK · N waiting`. | An unfiled paycheck or refund must never make the period look empty. Transfer-only and cash-only days still hide — that's the accounting contract working, and docs should say so. |
| **A3** | Color by in/out values | Token inks (In green-mix, Out normal, waiting amber) + one-way net chrome (green tint iff In > Out, neutral otherwise). Never red, never magenta, never color alone. Retire the badge's area-hue/magenta chrome. | §Color above. |
| **A4** | Badge on every stats strip, aggregated | Yes — via `bob bank report -p <PeriodId>` so the badge covers **exactly the days its strip counts** (ISO weeks, 13/14-week quarters, ISO week-years, bank-universe all-time). Never `-y` for year strips; never plugin-side month summation. | Calendar 2026 ≠ ISO 2026 (off by days at both ends); client-side folds hide accounting bugs. |
| **A5** | *(not requested)* | **Coverage marker** on partially tracked periods: `since Nov 11` when tracking starts inside the period, `to Nov 12` when a closed period isn't fully imported. From account `start` dates + the import journal. | One week of data on a year note otherwise reads as a frugal year. |
| **A6** | *(implied: keep current chrome/behavior)* | `span[role=link]` (no `<button>`), read-only navigation (no `ensureOpenDay` write; under the new visibility rule rows always exist, so plain opens suffice), no loading flash (render nothing until data settles), stale keeps the dashed marker, failure stays visibly distinct from a true zero. | Strip contract bans buttons; read surfaces shouldn't write; a `Bank · loading` chip that vanishes on $0 days is layout noise (gem's CLS point). |
| **A7** | *(not requested)* | **Waiting is period-scoped on every badge**; today's all-months count moves to the tooltip; the queue card owns the global nudge. | §Waiting above. |
| **A8** | *(not requested)* | Quarter/year/all-time display **whole dollars** (a sub-$1 nonzero amount keeps cents — never "$0"); day/week keep cents; exact cents always in the tooltip. | Cents on a year total are noise; exactness lives one hover away. |
| **A9** | *(not requested)* | Canonical config key `stats.bank_badge`; `stats.bank_chip` stays a permanent alias. One key gates all hosts. Money never gets a `typical` line and is never a sixth fact. | Never-hard-rename rule; medians over bursty money (paydays, rent cliffs) mislead. |
| **A10** | Glossary term | Yes — strand below, plus one-clause links from the Day Strip and Stats Strip strands. | Requested. |

## Design spec

### Anatomy and copy

```text
BANK · in +$2,500.00 · out $1,418.21 · 2 waiting · since Nov 11
│      │               │               │            └ coverage (faint, only when partial)
│      │               │               └ period-scoped waiting (amber), only when > 0
│      │               └ out part (normal ink), only when > 0 cents
│      └ in part (green ink, explicit +), only when > 0 cents
└ muted small-caps label; separators only between present parts
```

- **In before Out** — matches the request's own phrasing ("incoming/outgoing")
  and statement order; a deliberate, called-out flip of today's chip. Keep the
  lowercase words `in`/`out` plus the `+` sign (cld's signs-only variant is
  more compact but the words are self-teaching and are the "text and shape"
  the color contract demands).
- Tabular numerals, `0.72–0.8em`, one inline element that wraps between parts
  and never ellipsizes or truncates an amount.
- One focusable control for the whole badge: `span[role=link] tabindex=0`,
  Enter/Space, `mousedown` preventDefault (vim focus), Ctrl/Cmd/middle-click
  for a new tab — the strips' existing interaction helper.
- `aria-label` spells everything out: "Bank, week of Nov 9 to 15: in
  $2,500.00, out $1,418.21, 2 rows waiting. Open bank rows." Tooltip carries
  the breakdown: net, top out categories, "not counted: transfers $X ·
  unclassified in +$Y", waiting oldest date, coverage, and (today only) the
  all-months queue count.
- Reset inherited Obsidian button/host styles explicitly; the preview harness
  already models the global button-height hazard (cdx).

### Visibility (all comparisons on integer cents)

| Condition | Paint |
| --- | --- |
| No `bank.md`, pref off, future period, mobile/embed, teaching-empty | Nothing — and no `bob bank` spawn for future periods or a missing hub |
| in = 0, out = 0, waiting(period) = 0 | Nothing (zero height, no separator, no empty host spacing) |
| in = 0, out = 0, waiting > 0 | `BANK · N waiting` (amber, faint chrome) |
| one side > 0 | That part only; never `in $0.00` / `out $0.00` |
| both > 0 (incl. equal totals) | Both parts — a wash is activity, not nothing |
| cold load | Nothing until data settles; **no loading chip** |
| stale refresh | Last-good values, dashed start marker, tooltip note |
| failure, no cache | Muted `Bank unavailable` status (as today) — failure must never look like a clean zero |
| older bob without `-p` | Day/week badges work; quarter/year/all-time render nothing; one console warning |

### Color tokens

| Element | Token |
| --- | --- |
| In ink | `--bob-bank-in-ink: color-mix(in srgb, var(--color-green) 60%, var(--text-normal))` (shared with the month card's In metric) |
| Out ink | `--text-normal` |
| Label, coverage | `--text-muted` / `--text-faint` |
| Waiting | `--text-warning` |
| Chrome, In > Out | `--color-green` border at low alpha + ~10–12% wash |
| Chrome, otherwise | `--text-normal` at ~50% border / ~6% wash (present-but-calm; distinct from the muted grey that means "zero/unavailable") |
| Focus | 2px `--interactive-accent` outline, as the strips do |
| Forced colors | `CanvasText` amounts, no wash; words and signs carry meaning |

Verify composited contrast in default light/dark and common community themes;
small badge text needs ≥ 4.5:1 (cdx verified reference pairs; cld verified
the green-ink mix in both modes).

### Click targets (read-only, from bob's navigation metadata)

| Period | Target |
| --- | --- |
| Any, with waiting rows | Oldest waiting row in the period (`waiting_target` path:line) |
| Day / week, money only | That day's / the first counted day's heading |
| Quarter / year / all-time | The single containing month note if `single_month`, else `bank.md` (queue card) |

cdx's scoped period-detail panel is deferred: the tooltip covers explanation
at v1, and a new UI surface isn't needed to satisfy this request.

## Data contract (bob-cli, additive, schema_version 1)

```text
bob bank report [-b DIR] [-D DAY] [-f human|json] [-m MONTH] [-p PERIOD] [-s] [-w WEEK] [-y YEAR]
  -p, --period PERIOD   A stats-strip period id resolved by the periods calendar:
                        YYYY-MM-DD, GGGG-Www, GGGG-Qn, GGGG (ISO week-year, like
                        period notes), or all_time. Mutually exclusive with -D/-m/-w/-y.
                        Note: -p 2026 is the ISO year; -y 2026 is the calendar year.
  -s, --summary         Omit per-day rows (days stays []); totals, waiting, coverage,
                        and navigation only.
```

JSON additions (all additive): `period.kind` gains `quarter` / `iso_year` /
`all_time` (keep plain `year` for `-y`'s calendar span — don't overload one
kind with two calendars, grk's footgun); `coverage: {start, through,
complete}` from account starts + the import journal, clamped to the period;
`waiting_target: {path, line, date}` (oldest waiting row in the period);
`single_month` when all the period's rows live in one bank month note.
Implementation notes: route period totals through `compute_totals` (one
accounting path); options alphabetical with short aliases per `cli_rules`;
no Cargo version or CHANGELOG edits (release-train decision); document the
ISO-vs-calendar contrast in `docs/bank.md` and the JSON reference.

**Plugin side:** extend `bankBuildArgs`/decoder/subscription keys for
`period` + `summary`; generalize `bankCardDailyChipModel` into a shared
`bankBadgeModel(report, context)` → hidden | badge {inCents, outCents,
waitingPeriod, tone, coverage, target}; one painter for all hosts; adapters
for the daily plan slot (today's `bankSyncPlanHost` stays), `bob-day-stats`,
and the period-strip fence (badge host appended after the strip root).
Visibility-gate fetches with the period strip's observer; keep generation
guards and hub/month-file invalidation; watch `BANK_CACHE_SIZE = 16` (a year
note + four quarters + weeks can approach it — bump to 24 if eviction shows);
update committed fragments and regenerate `main.js`, never hand-edit it;
deploy via `bob plugins sync`.

## Glossary strand (draft — write via `/sase_memory_write` at implementation)

`sase/memory/glossary/bank-badge.md`, keyword **Bank Badge**, aliases
*bank chip*, *daily bank chip*:

> The read-only money summary that follows every [[stats-strip]] — after the
> [[day-strip]] in a daily note's `bob-plan` block, after a `bob-day-stats`
> fence, and after each [[period-note]]'s strip — for exactly that strip's
> period. From `bob bank report` totals it shows **in** (`income` and `refund`
> inflows, `+`, green ink) and **out** (outflows except transfers and
> cash-account rows, neutral ink), each only when above zero cents, plus the
> period's waiting [[bank-row]] count in warning ink; with nothing counted and
> nothing waiting it renders nothing. Its chrome tints green only when in
> exceeds out and is never red or magenta; words and signs always carry the
> meaning. It names partial coverage (`since Nov 11`). bob computes every
> value at read time from [[bank-month-note]] rows; the badge never writes a
> note, and activating it opens the rows behind it (oldest waiting row, day
> heading, or the bank hub). Gated by `stats.bank_badge` (`stats.bank_chip`
> is a permanent alias). Not a Stats fact (no `typical` line), not the
> `bob-bank` month or queue cards, not a plan-lane badge, and not part of
> `bob-period-parts`. See `docs/bank.md`.

Also: one-clause `[[bank-badge]]` links from the Day Strip and Stats Strip
strands; a decision record for the color rule (green-only-when-in-exceeds-out,
never red/magenta, text carries meaning) citing this research; docs updates in
`docs/bank.md` (badge section, `-p`/`-s`, retire "daily chip" wording),
`docs/stats.md`, `docs/periods.md`, both repos' plugin docs, and generated CLI
reference via `just docs-gen` / `just docs-check`.

## Implementation order

1. **bob-cli:** `-p/--period` via `PeriodId`, `-s/--summary`, `coverage` +
   navigation metadata, `compute_totals` reuse. Tests: bank `-p` span parity
   with `periods` for 2026-W01, 2026-W53, 2026-Q4 (Sep 28 2026 – Jan 3 2027),
   2026 (Dec 29 2025 – Jan 3 2027), all_time; leap day; current-period cutoff
   with `BOB_NOW`; all-time rows predating daily notes.
2. **bob-plugins:** shared model + painter, daily-chip migration (hide rule,
   token color, span[role=link], no loading flash), then the period hosts on
   the new report kinds. Tests: model vectors (0/0, one-cent sides, equal
   totals, waiting-only, unfiled-paycheck day, transfer-only day, stale,
   error, older-bob); update the e2e fixtures that assert the current
   `out $8.00 · in $0.00` string; preview fixtures light/dark/narrow; assert
   vault bytes unchanged after a click; sum-of-children == parent on a fixed
   snapshot (cdx's property test).
3. **Memory + docs** (glossary strand, strand links, decision record, docs).
4. **Later, explicitly out of scope:** budgets/targets, typical-relative
   marks (needs ≥4 prior periods of history), a money lane in period charts,
   cdx's period detail panel, a Mac idle-agenda bank line.

## Open questions for Bryan

1. **Net tint:** is the quiet green chrome when In > Out right, or do you
   prefer pure token ink with no net signal at all? (Both are safe; this is
   taste. Everything else — never red, never magenta — is settled by existing
   contracts.)
2. **In-first order and whole dollars on quarter+:** both are my
   recommendations and both are trivially reversible — veto freely.
3. **Waiting on period badges:** I recommend period-scoped waiting everywhere
   (it matches the weekly Category-card walk). If you'd rather keep waiting
   off week/quarter/year badges (grk/mus position), only the hide rule needs
   restating (hide when in/out are zero *and* the day is not today-with-queue).

## Recommended solution

Ship the **Bank Badge** as a bob-fed, read-only money line that follows every
stats strip:

1. **Data:** `bob bank report -p <period-id> [-s]` resolving through the
   periods calendar, with `coverage` and navigation metadata, totals through
   `compute_totals`; all-time spans the bank universe.
2. **Visibility:** parts on integer cents > 0; the badge renders when in > 0,
   out > 0, or period waiting > 0, and otherwise renders nothing — no $0.00,
   no loading chip, no empty spacing. Failure and staleness stay visibly
   distinct from a true zero.
3. **Color:** In in accessible green ink, Out in body ink, waiting in amber;
   chrome tints green only when In > Out and is otherwise neutral; never red,
   never magenta, never color alone; the badge drops the area-hue/magenta
   chrome (cards keep theirs).
4. **Form:** `BANK · in +$2,500.00 · out $1,418.21 · 2 waiting · since Nov 11`
   as a `span[role=link]` sibling row after each strip host; cents on
   day/week, whole dollars from quarter up; coverage named whenever a period
   is partially tracked; click opens the oldest waiting row, the day's
   heading, or the hub — and never writes.
5. **Vocabulary:** the Bank Badge glossary strand, strand cross-links, a
   color-rule decision record, and docs across both repos; `stats.bank_badge`
   with `stats.bank_chip` as a permanent alias.

This keeps the feature **intuitive** (one badge, one scope rule, numbers that
add up to the strip above them), **reliable** (ISO-exact periods, integer
cents, honest coverage, refusals never become zeros, read-only clicks), and
**beautiful** (Bob's own chip grammar, calm ink on ordinary days, a green
glow when more came in than went out).
