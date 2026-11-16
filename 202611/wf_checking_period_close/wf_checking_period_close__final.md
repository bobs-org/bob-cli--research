# WF Checking closing balance on period notes — consolidated design

> **Request:** show the Wells Fargo checking balance at the end of a period in the
> corresponding period note (never daily files); e.g. the 2026-11-15 balance visible in
> `~/bob/2026/2026-W46.md`. Lead the design (intuitive, reliable, beautiful), critique
> the plan, call out justified requirement adjustments, and recommend a solution.

**Lead researcher consolidation** (2026-11-16) of five independent reports — `__cdx`,
`__cld`, `__grk`, `__mus`, `__gem` in this directory — plus the lead's own verification
of every disputed data and code claim against bob-cli `0510aaf0`, bob-plugins
`origin/master`, and the live vault.

## Verdict

**Build it.** All five researchers independently reached the same core, and the lead's
verification confirms it:

1. **The number is the posted (ledger) balance at the end of the period's last day** —
   not the "available" balance the Wells Fargo app headlines, not a sum of accounts,
   and not the latest import's balance pasted onto an old week.
2. **It is drawn live at read time and never written into note bytes.** Period notes
   are create-only scaffolds; `docs/bank.md`'s contract is "totals are drawn when they
   are shown and never written into notes." A written balance goes stale on the next
   import, churns vault sync, and leaks into agent briefs.
3. **bob computes every cent from the import journal; the plugin only formats.**
   `.bob/bank/<host>.jsonl` already holds every QFX `LEDGERBAL` anchor and every posted
   transaction, append-only. On the live vault the chain reconciles **to the cent**
   against all five imported anchors (verified independently by cld, gem, and the lead).
4. **The home is the existing period-only bank area inside the `bob-stats-strip`
   fence** — which already mounts on week/quarter/ISO-year/all-time notes and
   structurally never on daily notes, embeds, popovers, or mobile. The "not for daily
   files" requirement is satisfied by the host, not by a filter.

Recommended v1 (detail below): bob gains a pure historical balance resolver and an
additive `balances[]` array on `bob bank report`; the plugin paints one calm,
exact-cents closing readout in the **Bank Period Charts header** (`▾ BANK CHARTS
$7,760.04 as of Fri 13`), with honest as-of labeling that quietly settles into a plain
Sunday close when later evidence proves the weekend empty. Roughly one medium bob-cli
bead plus one small-to-medium bob-plugins bead.

## Verified ground truth

The lead re-ran the critical checks rather than trusting any single report. All of the
following is confirmed:

| Fact | Verified how |
| --- | --- |
| W46 = Nov 9–15 2026, closed (`so_far: false`); Q4 2026 = Sep 28 2026 – **Jan 3 2027** (2026 has 53 ISO weeks) | `bob bank report -p 2026-W46 -f json`; period calendar |
| One account: alias `checking`, label `WF Checking`, kind `checking`, `start: 2026-11-11`; status `balanced`, `delta_cents 0`, balance **$7,760.04 as of 2026-11-13**, `last_import 2026-11-16`, coverage `imported_through 2026-11-13`, `complete: false` | report JSON + journal |
| Journal: 5 `bank.import` events (all `source: ofx`), 854 unique `bank.txn` (843 `before_start`, 11 `written`), posted span **2026-05-01 → 2026-11-13**, largest internal posted-date gap 4 days | direct read of `.bob/bank/kellys-macbook-pro-local.jsonl` |
| **Zero weekend postings**: weekday distribution Mon 308 / Tue 178 / Wed 124 / Thu 124 / Fri 120 / Sat 0 / Sun 0 | same |
| **The chain reconciles exactly**: latest anchor minus/plus journaled postings matches every other anchor (Nov 10 $8,229.74, Nov 12 $7,979.97, Nov 13 $7,760.04 ×3) with $0.00 delta | lead's independent recomputation |
| Reconstructed closes available **today** from existing evidence: Q2 end (Jun 28) $73,916.86 · Q3 end (Sep 27) $32,164.40 · W43 $18,403.73 · W44 $17,312.12 · W45 $8,960.31 · Nov 13 $7,760.04 | same (matches gem's table exactly) |
| Wells Fargo QFX sets `DTEND` and `LEDGERBAL/DTASOF` to the **last posted transaction date**, not the download date: Monday Nov 16's import still ends Nov 13 | import table above |
| OFX txn identity is the bank's `FITID`; CSV rows get synthetic `csv:<date>:<cents>:<n>` keys in the same map — a CSV import overlapping QFX coverage **would double-count** in a naive journal sum (none exist today) | `src/native/bank/source.rs:448,571` |
| `status.rs` `proof_for` is latest-only (earliest anchor ≥ `start` → opening; checked against the latest balance) and **excludes `before_start`** txns; its delta check sums *vault-row* cents, not journal cents | `src/native/bank/status.rs` |
| The charts host mounts only for kind ∈ {week, quarter, year, all/all_time}; its header renders `▾ BANK CHARTS` plus an **empty right-aligned `.bob-bank-period-readout`** slot (tabular-ready, ellipsis overflow) that fills only on bucket hover | `bob-plugins 241ne-…-hosts.js:92`, `241nd-…-paint.js:41–91` |
| Bryan already keeps this number by hand: a 30-day recurring chore `Update [[cash#^balance]]` in `recur.md`, 18 snapshots in `cash.md` since Jan 2025. The four inside the evidence window run **~$660–$2,400 below** the derived posted balance — the signature of WF's *available* balance (posted minus pending holds) | gem + cld, consistent with the WF activity FAQ |

Two implications worth stating plainly:

- **The example date needs honesty.** Nothing posts on weekends and WF's anchors stop
  at the last posted day, so today the honest W46 number is **$7,760.04 as of Fri
  Nov 13**. The next import whose window spans past Nov 15 proves Sat–Sun empty inside
  a covered range, at which point the same dollar amount becomes a plain, settled
  Sunday close. The amount never changes — only the claim strengthens.
- **Backfill is real and already paid for.** The 843 `before_start` transactions plus
  the anchor chain make closing balances provable for ~29 weekly notes (W18–W46), the
  Q2 and Q3 closes, and W44/W45 — with no new imports.

## Is this a good idea? (critique)

**Yes — it automates a two-year manual habit and completes the stock/flow picture.**

- The `cash.md ^balance` chore proves the want: Bryan has hand-recorded this number
  roughly monthly since January 2025, with gaps and drifting dates. This feature gives
  the same number a fixed cadence (every period close), a fixed home (the note where
  review happens), bank-proven precision, and zero toil.
- The bank family currently answers only *flow*. In/Out deliberately exclude transfers
  and unclassified inflows, so W46 reads "Out $469.70" while checking actually fell
  **$1,200.27** from W45. A card payment or savings transfer drops the balance and
  leaves the badge untouched. Stock next to flow prevents exactly this misreading.
- The marginal cost is small: the evidence, calendar, period host, fetch path, and
  design language (tabular numerals, never-red, coverage captions, read-only
  activation) all exist.

Risks, each with its answer in the design:

| Risk | Answer |
| --- | --- |
| **Wrong number type.** It won't match the app's "available" headline or the old `cash.md` snapshots (~$660–2,400 lower). | Label it posted/closing balance; tooltip explains available vs posted once. Never call it "available". |
| **False precision.** A Friday anchor dressed up as a Sunday close. | The as-of date is part of the claim; promotion to a plain close requires covered-empty evidence through period end. Unknowns render words, never $0.00. |
| **"It doesn't add up."** In − Out ≠ balance change. | Tooltip shows the signed period change (transfers included) and names the distinction. cld's exact bridge is a good v1.1. |
| **Judgment creep.** A weekly balance becomes a mood grade. | Body ink always; a falling balance is never red; no typicals, budgets, or scores. Overdraft (sign flip) is the one state earning warning ink. |
| **Privacy.** The most sensitive number in the vault, on every period note. | Drawn at read time: never in note bytes, `bob periods brief`, `bob stats`, or Mac surfaces (standing `ku` privacy rule). Optional masked mode later. |
| **Mobile absence.** Strips never render where `bob` can't spawn. | Accepted, consistent with the whole family; `bob bank report` answers in the terminal. A fix would be family-wide, not balance-specific. |

**Would we take a different approach?** Same goal, reframed: not "write the balance
into the note" but "show where each period closed, drawn live from bank-proven
evidence." No researcher recommended writing bytes, a new fence, a Stats fact, an
agent-brief change, or waiting for a bank feed (SimpleFIN/Teller) — and the lead
concurs on all five.

## Requirement adjustments (explicit)

| # | Requested | Shipped as | Why |
| --- | --- | --- | --- |
| **A1** | "total balance" | One account's **posted (ledger) balance**, labeled; accounts never summed | Only number provable for a past date; QFX carries `LEDGERBAL` only; credit/cash sums are meaningless. |
| **A2** | "on 2026-11-15" | Balance at `min(period end, last covered day)` with the **as-of date visible** whenever short of period end; auto-promotes when coverage reaches the end | WF anchors stop at the last posted weekday; claiming Sunday from Friday evidence invents bank truth. |
| **A3** | "in the file" | **Rendered on the note, never written into it** | Create-only scaffolds; "drawn, never written"; sync, staleness, and brief-leak hazards. Plain-Markdown/mobile readers won't see it — accepted tradeoff; the CLI answers there. |
| **A4** | not in daily files | Enforced **structurally** (charts host mounts on period kinds only); the CLI still answers single-day queries (`bob bank report -D 2026-11-15`) | The example question is a day lookup; the terminal should answer it even though daily notes stay clean. |
| **A5** | Wells Fargo checking | **Hero = first `kind: checking` account** (today: WF Checking); per-account data model so future accounts add lines, never a sum | Matches the live hub; avoids hardcoding a label. |
| **A6** | *(implied week-only)* | **Every period note**: week, quarter, ISO week-year, all-time (latest as-of) | Same host, same calendar, same question; a quarter close is at least as valuable. |
| **A7** | *(unsaid)* | **Backfill before `start`**: closes computed across all merged OFX coverage, including `before_start` history → ~29 weeks + Q2/Q3 light up immediately | Verified to the cent on the live journal; balance is bank evidence, not row bookkeeping. |
| **A8** | *(unsaid)* | **Exact cents at every period size** (week through all-time), tabular numerals | A balance is a reconcilable statement figure; the badge's whole-dollar rule exists for summed flows, which this is not. (Deviates from cld/mus/grk's badge-rounding position; adopted from cdx/gem.) |
| **A9** | *(unsaid)* | Quiet weeks still show it: **header-only render when In/Out/waiting are all zero** but a close exists | Transfer-only and no-spend weeks are exactly when stock matters and flow hides (live W45 is the proof case). |

## Resolved disagreements

The five reports agreed on the core but split on five points. Resolutions, with
reasoning:

| Question | Positions | Resolution |
| --- | --- | --- |
| **Where it renders** | badge part + chart lane (cld) · charts-header resting readout (grk) · panel footer line (mus) · balance band + sparkline above charts (gem) · row between badge and charts (cdx) | **Charts-header resting readout** (grk). The slot exists and is empty at rest, costs zero height, stays visible when charts collapse, and the host is structurally period-only. The badge is rejected as the home because it also mounts on daily Day strips and its semantics are flow. gem's hero band + sparkline and cld's step-line lane are the **v2 blueprint**, not v1. |
| **Weekend/Sunday settling** | weekend rule settles Sunday once Friday is proven, guarded by a check finding (cld) · strict as-of until coverage reaches the end (cdx, grk, mus, gem) | **Strict as-of by default; no heuristic.** The displayed dollar is identical either way — only the label differs — and the next import's window retroactively proves the weekend empty, so a Sunday close settles itself within days. cld's rule (with its `bank_weekend_posting` guard) stays on the table as an opt-in if the suffix annoys Bryan in practice. |
| **History before `start`** | include `before_start` (cld, gem) · clip to `start` (grk, mus, cdx) | **Include it.** The cautious position assumed the chain might not hold; the lead verified it holds exactly, and the per-span anchor-consistency check is the safety net (any mismatch → `unverified`, no number). 29 weeks of free backfill is the difference between a feature and a demo. |
| **Rounding on quarter/year** | badge-style whole dollars (cld, mus, grk) · exact cents everywhere (cdx, gem) | **Exact cents everywhere** (A8): stock ≠ flow; reconcilability wins. Called out as a deliberate deviation from the badge contract. |
| **Config gate** | reuse `stats.bank_period` (mus, grk) · new `stats.bank_balance` (cld, gem) · account-selection key (cdx) | **Reuse `stats.bank_period` in v1** — the close lives inside that host, one kill-switch, no sprawl. An independent `stats.bank_balance` (and a masked screen-share mode) are easy follow-ups if ever wanted. No account-selection key until a second account exists. |

Also resolved: cdx alone wanted OFX timestamp-precision work (exclusive `DTEND`,
intraday offsets, correction tags) as a prerequisite. The live evidence largely defuses
this for Wells Fargo — anchors are date-stamped at the last posted day and the chain
reconciles exactly across overlapping re-imports — so v1 does not block on it. Two of
cdx's cautions survive as design requirements: the per-span **anchor cross-check**
(which would catch a silent bank-side correction as a mismatch → `unverified` +
check finding) and **never inferring zero movement outside an imported window**.

## The design

### Definition

> **Closing balance of period P for account A:** the posted (ledger) balance of A at
> the end of P's last day, in signed integer cents — the bank's balance after every
> transaction posted on or before that day. Suggested glossary term: **Bank Closing**.

### Computation (bob, one pure module)

New `src/native/bank/balance.rs`, reusing the journal/window/proof machinery; the
plugin never adds cents.

1. **Spans.** Merge each account's OFX import windows (`start..end`, unclipped) into
   maximal contiguous components. Days inside a window with no transactions are
   proven-empty; days outside every window are unknown.
2. **Anchors.** Within a span, every `bank.import` with `balance_cents` +
   `balance_asof` is an anchor; the canonical one is `max_by_key(balance_asof, ts)`.
3. **B(d).** For a date `d` inside (or one day before) an anchored span:
   `anchor ∓ Σ journal cents posted between d and the anchor's as-of` (subtract
   backward, add forward). Journal cents only — **never vault-row cents, never
   category/transfer filters** (a transfer out of checking moves checking).
   `before_start` txns count. CSV-keyed txns (`csv:` prefix) are excluded from balance
   arithmetic; a CSV window overlapping an OFX span marks it `unverified` until a
   `source` tag lands on new txn events (gem's guard — moot today, cheap to honor).
4. **Consistency.** Every other anchor in the span must reproduce from the canonical
   one with a $0.00 delta; any disagreement makes the whole span `unverified` (no
   number, a reason, and a `bank_balance_anchor_mismatch` finding in `bob bank
   check`). Deliberately conservative; it passes on today's data.
5. **Period resolution.** Wanted date = period end (clipped to today while open). As-of
   = last covered day ≤ wanted. Never extrapolate across unimported gaps; never show a
   value for a date before coverage begins.
6. **Invariants (each a test):** when as-of equals the latest anchor date and
   `delta_cents == 0`, the close equals `accounts[].balance_cents`;
   `B(d) − B(d−1) = Σ cents posted on d` for covered days; a past period never
   inherits the *latest* balance just because it is latest; as-of never exceeds period
   end, coverage, or today.

### States and copy

| State | Rule | Readout |
| --- | --- | --- |
| **settled** | coverage reaches period end | `$7,760.04` |
| **as_of** | closed period, coverage stops earlier | `$7,760.04 as of Fri 13` (suffix in faint ink) |
| **so_far** | period contains today (and all-time) | `$7,760.04 as of Fri 13` + existing so-far language in tooltip |
| **stale** | as-of older than `bank.stale_after` | same, date in warning ink |
| **delta** | bank vs vault rows disagree | number renders + `Δ $X` chip naming the disagreement (the number is still the bank's claim) |
| **unverified / gap** | anchor chain broken, journal unreadable, CSV-only, or window hole | short muted words (`unverified — import a QFX statement`), **never $0.00** |
| **untracked / pre-coverage / future** | cash account, period before evidence, future period | nothing renders |

A true $0.00 balance renders; negative balances keep their sign and may use warning
ink (the one state that earns color). Tooltip: account label, "posted balance" with
the one-line available-balance caveat, exact cents, as-of + wanted dates, previous
close and signed period change (transfers included), anchor agreement (`✓ matches 5
Wells Fargo balances`), coverage, and the click action. Aria spells all of it;
activation (click/Enter/Space) opens the as-of day's heading in the bank month note,
else `bank.md` — read-only, like every bank surface.

### Rendering

The W46 header on Monday morning, today: `▾ BANK CHARTS      $7,760.04 as of Fri 13` —
tabular numerals in the existing right-aligned readout slot, body ink, account label
in the tooltip while there is one hero (visible — `WF Checking $…` — if a second
importable account ever appears). Bucket hover still borrows the readout for In/Out;
mouse-leave and Escape restore the close. Collapsed charts keep the number
(`▸ BANK CHARTS $7,760.04 …`), which is what makes collapse livable. Quiet periods
(W45: no flows, no waiting) render the header line only — today they render nothing,
which is precisely the gap. Zero new vertical height on active periods; forced-colors
and reduced-motion follow the family rules.

### JSON and CLI (additive, `schema_version: 1` unchanged)

`bob bank report` (all period selectors, same payload the plugin already fetches with
`-p <id> -s -c`) gains a top-level `balances[]`:

```json
"balances": [{
  "alias": "checking", "label": "WF Checking", "kind": "checking", "hero": true,
  "cents": 776004, "as_of": "2026-11-13", "wanted": "2026-11-15",
  "state": "as_of", "status": "balanced", "delta_cents": 0,
  "open_cents": 896031, "open_date": "2026-11-08", "change_cents": -120027,
  "coverage": { "since": "2026-05-01", "through": "2026-11-13" },
  "target": { "path": "bank/2026-11.md", "line": 26 }
}]
```

Unknown amounts are `null`, never 0; absent array on old binaries means the plugin
paints nothing (no warning noise). Human output gains one line under the summary —
`WF Checking $7,760.04 as of Fri 13 · ✓ balanced` — and `bob bank report -D
2026-11-15` answers the literal example in the terminal. No new subcommand, no new
flag, no `!` contract break. Per-bucket closing series (`charts.balances[]`) ships
with the v2 lane, not now.

### Explicitly out of scope (v1)

Daily notes and `bob-day-stats`; writing cents anywhere (notes, frontmatter, Review,
briefs, Stats, Mac — the `ku` privacy rule stands); net worth, budgets, typicals,
available balance, pending transactions; the balance sparkline/lane; bank feeds
(`bob-cli-kv`); new config keys; month notes (retired as a note level).

## Implementation plan

Ship bob first; the plugin tolerates a missing `balances[]`, so sequencing is safe.

1. **bob-cli (medium bead):** `balance.rs` resolver (spans, anchors, B(d), consistency,
   period resolution) refactored to share span/sum helpers with `status.rs` so status
   and closes can never disagree; `balances[]` in `report.rs` + human line in
   `output.rs`; `bank_balance_anchor_mismatch` in `check.rs`. Tests: the invariant
   suite above plus anchor-before/inside/after-period, gap isolation, `before_start`
   reconstruction, CSV-only → `unverified`, open/all-time, W53 boundary (Q4 ends
   2027-01-03), zero and negative balances, overflow. Docs: `docs/bank.md` "Closing
   balance" section + JSON outputs reference; `just docs-gen` / `docs-check`. No
   version/CHANGELOG edits (release train owns them).
2. **bob-plugins (small-medium bead, depends on the shipped JSON):** decode
   `balances[]` via the safe-cents path; resting readout + restore-on-leave;
   header-only visibility when flows are empty; states, tooltip, aria, activation;
   styles incl. forced-colors. Golden tests: settled / as_of / delta / unverified /
   quiet-week / old-bob-omission / collapse persistence / daily-note exclusion. Then
   `npm run build && npm test && bob plugins sync`.
3. **Vocabulary (after acceptance, via `/sase_memory_write`):** glossary **Bank
   Closing** strand; one-line cross-references from Bank Badge / Period Note /
   Bank Period Charts; optionally a decisions record ("period closing balances are
   posted balances drawn from bank evidence at read time, never written into notes").
4. **Vault follow-up (Bryan's call):** once W45/W46/Q3 render correctly, retire the
   30-day `Update [[cash#^balance]]` chore; keep `cash.md` as pre-2026 history.

## Open questions for Bryan (recommended defaults)

1. **As-of suffix tolerance.** Each Sunday close reads `as of Fri …` for a few days
   until the next import proves the weekend empty. Live with that (recommended), or
   add cld's guarded weekend rule so Sundays settle Monday morning?
2. **Backfill.** Show closes for W18–W45 and Q2/Q3, where flows/In-Out stay empty
   (pre-`start`)? Recommended yes — verified exact, and it makes the feature useful on
   day one.
3. **Cents on quarter/year.** Exact cents everywhere (recommended) vs the badge's
   whole-dollar rule?
4. **Retire the manual chore** after verification? Recommended yes.
5. **Masked mode** (`$•,•••.••` until hover) if period notes get screen-shared —
   follow-up, not v1?

## Report provenance

- `wf_checking_period_close__cdx.md` — failure-state taxonomy, OFX date-precision
  caution, resolver purity and acceptance tests.
- `wf_checking_period_close__cld.md` — vault forensics (weekend distribution, chain
  proof, `cash.md` available-balance diagnosis), weekend rule, badge-part design,
  bridge invariant, balance-lane spec.
- `wf_checking_period_close__grk.md` — live honesty framing, charts-header readout
  placement (adopted), `closings[]` shape, figures (`fig-*__grk.svg`).
- `wf_checking_period_close__mus.md` — state machine and copy, panel-footer variant,
  scope discipline, config-gate minimalism.
- `wf_checking_period_close__gem.md` — journal import table, backfill reconstruction
  (independently re-verified exactly), CSV double-count guard, `recur.md` chore
  discovery, band/sparkline v2 blueprint.
