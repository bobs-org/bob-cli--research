# Wells Fargo checking balance in period notes — research (`__mus`)

> **Request:** show the total balance of the Wells Fargo checking account at the end
> of a given period in the corresponding period note (not daily notes). Example:
> balance on 2026-11-15 visible in `~/bob/2026/2026-W46.md`.
> Goal: a design that is intuitive, reliable, and beautiful, plus a critique and a
> recommended implementation.

## Bottom line

**Build it — as one quiet, read-only balance line in the existing bank family on
period notes, never as bytes written into the note.** The idea is good: the weekly
review already happens on the period note, the Monday QFX import lands beside it,
and flows (In/Out) without stock (balance) leave the review asking "so where do I
stand?" But the request as literally written has three bugs, each needing a
called-out adjustment before implementation:

1. **There is no "balance on Nov 15".** The latest bank evidence for W46
   (Nov 9–15) is a QFX `LEDGERBAL` as of **Nov 13**; imports run weekly and the
   report says `imported through Nov 13`. Claiming a Nov-15 balance invents two
   days of bank truth. The honest label is **"Balance Nov 13 · $7,760.04"** with
   the as-of date always shown (§Adjustments A1).
2. **"Total balance" must mean one account's ledger balance, not a sum.**
   `bob bank` supports many accounts of different kinds (checking, savings,
   credit, cash). Summing them is meaningless (a credit balance offsets
   checking). Ship **WF Checking only**, explicitly labeled, with per-account
   data so later accounts add lines instead of corrupting a sum (§A2).
3. **Nothing may be written into the period note.** Period-note ownership is
   settled: scaffolds are create-only, strips and parts render live, numbers are
   never written into Markdown (`docs/periods.md`, `docs/stats.md` engine
   principle, `docs/bank.md` totals contract). A written-in balance would go
   stale on the next import, fight vault sync, and leak into agent briefs. The
   balance must be a **live rendering from `bob bank report -p <id>`**, like the
   badge and charts panel (§A3).

With those fixes, the recommended v1 is small: add an additive `balances[]`
array to `bob bank report -p`, and render one muted line in the Bank Period
Charts panel (gated by the existing `stats.bank_period` key): `Balance Nov 13 ·
$7,760.04 · WF Checking ✓`. No scaffold change, no new fence, no Stats fact,
no brief change, no Mac surface, no daily-note change.

## Is this a good idea?

**Yes, with scope discipline.** Four researchers' prior work converges on the
same verdict for money on period notes: the badge gives each period one flow
line, the charts panel gives shape, and neither answers "what did I have?" The
balance completes stock-vs-flow at exactly the grain the review uses (week,
quarter, year, all time). The data model is ready (journaled `LEDGERBAL`
balances, `start` dates, import windows), the ritual exists (weekly Monday QFX
import + Category-card walk beside the week note), and the marginal cost is one
JSON array on a call the plugin already makes.

**Why it earns its place.**

- The review question is real: Out $469.70 in W46 means something different
  with $7,760 in checking than with $400.
- The plumbing is already period-aware: `bob bank report -p 2026-W46` resolves
  the ISO week, and `-p 2026-Q4` / `-p 2026` / `-p all` already cover quarters,
  ISO years, and bank-history all-time. No new calendar code is needed.
- The family already solved the hard problems this feature inherits: partial
  coverage captions, waiting-aware hide rules, whole-dollar rounding, green-only
  for In, never-red, tooltips with exact cents, read-only activation.

**Risks, and how the design answers them.**

- **False precision.** Weekly imports + 6-day-old evidence make most period-end
  dates unbacked. *Answer:* every rendering names its as-of date; forward
  derivation past `imported_through` is labeled provisional; pre-tracking and
  future periods render nothing, never $0.
- **Judgment creep.** Balances invite red/green health coloring, net-worth
  math, and typical-comparisons. *Answer:* balance uses neutral body ink
  always; only In keeps green; stale/gap/delta use the existing warning/error
  language; no typicals, no budgets, no scores (stays behind the `ku` trial
  gate).
- **Flow/stock confusion.** In/Out (period sums) next to Balance (point in
  time) can misread as "In − Out = Balance". *Answer:* separate copy
  ("Balance" vs "Out/In"), separate line, tooltip explains the anchor method;
  never net refunds or exclude transfers in the balance path.
- **Privacy.** Balances are the most sensitive bank number. *Answer:* live
  plugin rendering only; nothing in note bytes, `bob periods brief`, Stats,
  or Mac surfaces (honors the standing `ku` privacy rule).
- **Clutter.** Period notes already hold strip + badge + charts + parts +
  prose. *Answer:* one quiet line, hidden whenever it has nothing honest to
  say; cold load renders nothing; mobile renders nothing (no `bob` spawn).

**Would I take a different approach?** Not a different goal, but I would not
write it into notes, make it a Stats fact, or build a balance-trend chart in
v1. Three rejected alternatives with reasons are in §Alternatives; the
deferred balance-history chart is explicitly v2 after two months of rows.

## What exists today (verified in this session)

| Fact | Evidence |
| --- | --- |
| One checking account: alias `checking`, label `WF Checking`, kind `checking`, `start: 2026-11-11` | `bob bank config show -f json`: `alias checking, label WF Checking, start 2026-11-11, status balanced, balance_cents 776004, balance_asof 2026-11-13, hint Ledger balance matches through 2026-11-13` |
| Latest balance $7,760.04 as of Nov 13, `balanced`, `delta_cents 0`, `last_import 2026-11-16` | Same `config show` output, corroborated by `bob bank report -p 2026-W46 -f json` `accounts[]`: identical `balance_cents 776004, balance_asof 2026-11-13, status balanced` |
| W46 is Nov 9–15, closed; Q4 is Sep 28, 2026 – Jan 3, 2027; report coverage `tracked_since 2026-11-11, imported_through 2026-11-13, complete false` | `bob bank report -p 2026-W46 -f json`: `period {start 2026-11-09, end 2026-11-15}` + `coverage {tracked_since 2026-11-11, imported_through 2026-11-13}`; `bob bank report -p 2026-Q4 -f json` shows the same coverage with `start 2026-09-28` |
| W46 flows: Out $469.70, In $0.00, 11 rows on Nov 12–13 only; Nov 9–10 and Nov 14–15 have no rows | `bob bank report -p 2026-W46` human output: `Out $469.70 · In $0.00 · Net $469.70`; JSON `days[]` confirms empty Nov 9/10/11/14/15 and 7 + 4 rows on Nov 12/13 |
| `report -p` already speaks the strip's calendar: day, ISO week, quarter, ISO week-year, all time (`-p 2026` = ISO year; `-y` stays calendar) | `bob bank report --help` + `src/native/bank/report.rs: resolve_stats_strip_period` via `PeriodId::resolve` |
| Balances come only from QFX `LEDGERBAL` (`BALAMT`/`DTASOF`); never `available` balance; CSV carries no balance or account kind | `docs/bank.md` Import + `src/native/bank/import_plan.rs` ledger-balance parsing |
| Account proof today is latest-only: earliest-balance anchor minus journaled txns from `start`, checked against latest balance + current ledger rows; states `balanced/delta/gap/stale/unverified/untracked` | `src/native/bank/status.rs: proof_for`, `latest_balance`, `coverage_gap`, `status_hint` |
| Totals exclude `transfer` and cash-account rows; In counts only `income`/`refund`; balance derivation must NOT apply those filters (a transfer out of checking still moves checking's balance) | `docs/bank.md` Totals + `src/native/bank/report.rs: is_counted_money` vs `status.rs: ledger_transaction_sum` (sums by account + journal ID, no category filter) |
| Period-note contract: scaffold written once (incl. `bob-stats-strip` fence); strip + parts render live; numbers never written; Review via `bob periods draft` only; Intentions/Outcomes/Theme/Reflection belong to Bryan | `docs/periods.md` Note anatomy and ownership + `src/native/periods/scaffold.rs` fence strings |
| Bank Badge follows the strip; Bank Period Charts panel follows the badge on week/quarter/ISO-year/all-time (never daily, never embeds); both read `bob bank report -p <id> -s [-c]`, never write | `docs/bank.md` Bank badge + Bank period charts + prior consolidated research `bank_badge_strip_family.md`, `bank_period_charts.md` |
| Money never becomes a Stats fact or typical; agent briefs carry no bank data (standing `ku` rule) | `docs/stats.md` + `bank_period_charts.md` §Verified (`bob-cli-ku` snoozed to 2026-12-14) |
| CLI/docs gates: alphabetical options, short alias for every public long option, colored output where it helps, never hard-rename, additive JSON; docs via `just docs-gen` + `just docs-check` | `sase/memory/cli_rules.md`, `sase/memory/docs.md` |

## How the balance at "end of period" must actually be computed

The current proof answers "does the latest QFX balance agree with the
ledger?" For a period end `D`, v1 needs "what was the bank's balance at `D`?"
with the same honesty. The correct derivation reuses the existing anchor
machinery per account, not the flow-totals path:

1. **Anchor.** Earliest QFX import with `balance_cents` + `balance_asof >=
   start`: `opening = anchor_balance − Σ journaled txns posted in [start,
   anchor_asof]`. (Already in `status.rs`.)
2. **Historical point.** For period end `D`: `balance(D) = opening +
   Σ journaled txns posted in [start, min(D, latest_asof)]`, where the sum is
   over **all journaled cents for that account** (no `transfer`/cash/category
   filter; transfers and ATM withdrawals move real balances). Typed rows
   without journal IDs never enter the sum: Bryan's guesses must not move the
   claimed bank balance. Ledger edits do not move it either — divergence
   surfaces as the existing `delta` finding, and the displayed number stays
   the bank's number with its warning.
3. **After the latest evidence.** If `D > latest_asof`, derive forward
   (`latest_balance + Σ journaled txns in (latest_asof, D]`) and mark the line
   provisional (`awaiting import` / `so far` on open periods). With weekly
   Monday imports, a Sunday week-end is routinely 2 days past evidence — the
   W46 ask ("Nov 15") is exactly this case, so the line must read Nov 13.
4. **States propagate.** `gap` (QFX window break from `start` through `D`),
   `stale` (`today − latest_asof > stale_after`), `delta` (bank vs ledger
   mismatch), `unverified` (no QFX balance yet, incl. CSV-only), `untracked`
   (cash), pre-tracking (`D < start` or period entirely before `start`), and
   `future` (`period.start > today`) each have a rendering (§Design). A state
   never zeroes money: buckets keep their rows; the balance line explains
   itself in words.
5. **Multi-day periods use one point.** Week/quarter/year show `balance(end)`,
   not a sum or average. All-time shows the latest balance (same as the hub).
   Open periods (`so_far`) show the latest balance labeled `as of`, not the
   future Sunday.

This keeps one accounting path (`compute_totals` for flows stays untouched;
balance has its own journaled-sums path mirroring `ledger_transaction_sum`
minus the ledger-row join), and `Σ children == totals` invariants are
unaffected because balances are points, not additive.

## Design (intuitive, reliable, beautiful)

**Scope.** Week, quarter, ISO week-year, and all-time period notes only.
Daily notes excluded per the request (daily keeps the badge; the balance would
double the badge's job and crowd `bob-plan`). Month notes excluded (months are
a Stats grouping, not a note level). Pre-tracking, future, and teaching-empty
periods render nothing.

**Account.** WF Checking (`alias checking`) only in v1, always labeled
(`WF Checking` + `✓`/`Δ`/warning per account status). The JSON carries an
array so a second account later adds a second quiet line; v1 never sums
accounts. Copy says **Balance**, never "Total" (which collides with flow
totals and net-worth readings).

**Placement (recommended).** One muted line at the foot of the Bank Period
Charts panel (inside the existing `bob-stats-strip` fence, third-host
sibling after the badge — the host split `bob-cli-lh.3` already built). Rationale:
the badge owns flows + waiting + coverage for the strip's exact period; the
charts panel owns the period's money shape; the balance is a point-in-time
coda to that shape, not a second badge. One new host or a badge second line
would add a spawn or tangle two concepts (flows vs stock) in one line. Panel
footer reuses the panel's `bob bank report -p <id> -s -c` call (add balances
to the same payload — no new spawn), its coverage caption, and its hide rules.

Fallback if the panel host proves awkward in implementation: append the same
copy as a quiet suffix line to the badge (`BANK · out $X · in +$Y · Balance
Nov 13 $7,760.04`). Same JSON, same states, same gate discussion — but keep
it out of the badge tooltip-only alternative (a balance that hides behind
hover fails the "glanceable in review" goal).

**Copy.** `Balance Nov 13 · $7,760.04 · WF Checking ✓` (closed W46 example;
`✓` mirrors `account_chips` balanced language). Open week: `Balance Nov 13 ·
$7,760.04 · WF Checking · so far`. Provisional: `Balance Nov 13 · $7,760.04 ·
awaiting import`. Gap/stale/delta append their existing words
(`coverage gap Oct 3–5`, `stale — import a current statement`, `differs by
−$12.40`). Pre-tracking: `Balance · not tracked yet` only when the whole
period predates `start`; partial periods keep the balance plus the panel's
`since Nov 11` caption. Never `Balance $0.00` for unverified/CSV-only —
render `Balance · unverified — import a QFX statement`.

**Format.** Follow the badge contract verbatim: exact cents on week panels,
whole dollars from quarter up (sub-$1 keeps cents), exact cents always in the
tooltip. Tabular figures, `+` never on balances (plus means inflow), no
thousands ambiguity ($7,760.04). Tooltip: exact cents, as-of date, account
status + hint, coverage (`tracked since / imported through`), and the
one-line derivation note ("from QFX ledger balances + posted transactions;
typed rows excluded").

**Color.** Balance amount in normal body ink, never green/red. Green stays
reserved for In; warning amber only for waiting/stale; errors carry text
(`differs by …`, `coverage gap …`), never color alone. Chrome stays neutral;
no net-based tint from the balance (a low balance is timing, not failure).
This extends the settled badge/panel palette without a new hue.

**Activation.** Click/Enter/Space opens the bank month note at the as-of day
heading when one month holds the as-of date, else `bank.md` — read-only, never
creates a note (same rule as badge/quarter activation in `docs/bank.md`).
Category rows and the balance line itself are otherwise inert.

**Gates and hosts.** Reuse `stats.bank_period` (default true) — no new config
key in v1, so one kill-switch covers the panel and its coda, and a broken
balance never takes the badge down. Honor `stats.bank_badge` off (badge hides;
panel + balance follow panel rules, including the waiting-only quiet line).
Hidden on mobile, embeds, and hover popovers (no `bob` spawn there — same as
badge/charts). Cold load renders nothing until the report resolves; failure
renders the existing muted `Bank charts unavailable` line, never a clean zero;
period mismatch is a failure, never a number.

## Adjustments to the requirements

_Explicit call-outs._

| # | Requested / implied | Shipped as | Why |
| --- | --- | --- | --- |
| A1 | "Balance on 2026-11-15" (period-end date) | **"Balance as of latest evidence"** with the as-of date always shown (W46: Nov 13, not Nov 15) | Imports land weekly; claiming the Sunday invents bank truth. The as-of date is the reliability feature. |
| A2 | "Total balance" (singular sum) | **One labeled account line (WF Checking)**; JSON is per-account `balances[]`, never a cross-account sum | Credit/cash/savings sums are meaningless; later accounts add lines. |
| A3 | "In the period note … somewhere" | **Live rendering in the charts panel footer**, zero bytes written to the note | Ownership + engine principle: numbers render live; written balances go stale and leak into briefs/sync. |
| A4 | *(implied: every period incl. daily)* | Week/quarter/ISO-year/all-time only; **daily excluded** per the request; pre-tracking/future/empty render nothing | Daily keeps the badge; months are not a note level; false zeros are worse than absence. |
| A5 | *(unsaid: which cents)* | Badge rounding reused (cents on week, whole dollars above, exact in tooltip) | One money-format rule instead of two; noise down on year/all-time. |
| A6 | *(tempting: red/green balance health)* | Neutral body ink for the balance; green only for In; warnings in words | Spending/low balances are not errors; color never carries meaning alone. |
| A7 | *(unsaid: CSV / typed rows)* | CSV-only and no-QFX states show `unverified`, never $0; typed rows never move the balance | CSV carries no balance; guesses must not move bank truth. |
| A8 | *(unsaid: open periods)* | Open periods show latest balance + `so far` / `awaiting import`, not the future Sunday | The future has no ledger. |
| A9 | *(implied: new config + docs)* | Reuse `stats.bank_period` gate; additive `balances` on `schema_version: 1`; `docs/bank.md` + JSON-outputs docs + `just docs-gen`/`docs-check` | No config sprawl; no breaking change; follows CLI/docs memory rules. |
| A10 | "Beautiful" | Family resemblance: strip typography, badge inks, same child axis, same ghost/coverage language, tabular numerals | Copying the existing chart language *is* the beauty. |

## Alternatives considered (and why not v1)

- **Write the balance into note bytes** (frontmatter `balance::` or a
  `## Money` section). Rejected: violates create-only scaffolds, stale-on-next-import,
  sync conflicts across athena/apollo/Mac, freshness/status-hook surface, and the
  `ku` privacy rule (bytes leak into briefs). The engine derives every number at
  read time for exactly this reason.
- **A sixth Stats fact / typical line for balance.** Rejected: typicals are
  medians over prior same-kind periods — noise over 6-day-old bursty money —
  and Stats feeds `bob periods brief`, which must stay bank-free.
- **Badge-embedded balance as the primary home.** Viable fallback (§Design),
  but second choice: it tangles flows and stock in one line and either adds a
  second spawn or overloads the badge's exact-period waiting/coverage contract.
- **Balance-trend chart / net-worth line.** Deferred to v2: needs two months
  of rows (the `ku` trial gate), a per-bucket historical-balance series
  (multiply the honesty-state work by 53 buckets), and a Bryan decision that
  comparisons belong on money notes. V1 ships the point; v2 draws the line.
- **`dash_bank.md` explorer or hub-queue balance.** Useful, but review happens
  on the period note beside Intentions/Outcomes; the hub already shows account
  chips (`account_chips` in `output.rs`). No new page in v1.
- **Summing all accounts ("total").** Rejected per A2. If Bryan later wants a
  liquid-total, it needs an explicit account set + credit-sign rules + its own
  design — not an unlabeled sum.
- **CLI-only (`report` human line, no plugin).** Insufficient: the review
  happens in Obsidian; terminal-only misses the goal. (Still worth adding the
  human `Balance …` line to `report` output for parity — cheap and consistent.)

## Recommended implementation (v1, in order)

1. **CLI: `bob bank report -p` gains additive `balances[]`.** Per importable
   account: `{alias, label, balance_cents, asof, status, provisional}` where
   `provisional = asof < period.end` (or period open). Derivation per §How;
   reuse `proof_for` anchor + journal sums; no `transfer`/category filter;
   typed rows excluded; gap/stale/delta/unverified propagate from `status.rs`.
   Human output adds one `Balance …` line under coverage (same copy). Clap:
   no new flag (rides existing `-p/-s/-c`); keep options alphabetical; help
   text via `just docs-gen`. JSON stays `schema_version: 1` additive.
2. **Plugin: panel footer line** in the existing period host (same `-p -s -c`
   payload; no new spawn). Copy/format/color/activation/tooltip per §Design.
   Gate: existing `stats.bank_period`. No scaffold/migration (create-only
   preserved). Mobile/embeds/popovers: hidden (no spawn).
3. **Docs:** `docs/bank.md` (balance semantics + states + placement), JSON
   outputs reference, badge/panel cross-links. `just docs-check` green.
4. **Tests:** report golden vectors for W46 (balance Nov 13 $7,760.04,
   provisional past Nov 13), Q4 partial (`since Nov 11`), pre-tracking quarter
   (nothing), CSV-only account (`unverified`), cash account (no line), gap and
   delta states, open vs closed, all-time latest. Plugin: hide/show matrix from
   the badge/charts family plus the new line.
5. **After `lh.4` docs close; re-scope `ku`** against whatever ships (trial +
   two-months rule still gates typicals/trends/Mac/briefs — unchanged).

## Open questions for Bryan (v1 defaults in parentheses)

1. Account scope: WF Checking only, or also show a second line if a savings
   account appears later? (Default: per-account lines, checking first.)
2. Quarter/year rounding: whole dollars like the badge, or always cents for
   balances? (Default: follow the badge; exact cents in tooltip.)
3. Gate: reuse `stats.bank_period`, or a separate `stats.bank_balance`
   kill-switch? (Default: reuse — less sprawl.)

## Sources and method

- Live vault via `bob query` skill + `bob bank config show`, `bob bank report
  -p 2026-W46[-s -c]`, `bob bank report -p 2026-Q4`, `bob periods show 2026-W46`
  (installed `bob 0.5.0`, today 2026-11-16): balance $7,760.04 asof Nov 13
  corroborated by both config and report; W46 Out $469.70 / In $0.00;
  coverage tracked-since Nov 11 / imported-through Nov 13.
- Code: `src/native/bank/report.rs` (periods, totals, coverage, charts),
  `src/native/bank/status.rs` (anchor/proof/states), `src/native/bank/journal.rs`,
  `src/native/bank/import_plan.rs` (LEDGERBAL, CSV limits),
  `src/native/bank/output.rs` (`account_chips`), `src/native/periods/scaffold.rs`,
  `docs/bank.md`, `docs/periods.md`, `docs/stats.md`.
- Prior consolidated research: `bank_badge_strip_family.md`,
  `bank_period_charts.md`, `period_note_tree_and_stats_strips.md`
  (verified-current-state, placement, palette, and honesty-state resolutions
  adopted here); memory strands `glossary:bank-badge`, `glossary:stats-strip`,
  `glossary:bank-month-note`, `glossary:bank-row`, `glossary:period-note`.
- Deliberately did not seek or open this swarm's peer `__cdx/__cld/__grk/__gem`
  reports; convergences cited above are with prior, unrelated research only.
