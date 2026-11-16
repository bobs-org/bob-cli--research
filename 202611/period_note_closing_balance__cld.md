# Closing balance on period notes (WF Checking) — research · cld

**Request.** Show the total balance of the Wells Fargo checking account at the end of
each period in that period's note (weekly, quarterly, yearly, all-time), but not in
daily notes. Example: the 2026-11-15 balance should be visible in `2026/2026-W46.md`.
Design it to be intuitive, reliable, and beautiful. Critique the idea, adjust the
requirements where that's justified, and recommend a solution.

**Short answer.** Yes, build it. Almost all of the hard part already exists. bob
already journals every QFX ledger balance and every posted transaction, and it proves
they agree. On your vault the chain reconciles to the cent across all four later bank
balances. Three changes make it work well:

1. **Name the number exactly.** It is the *posted* balance at the end of the period's
   last day, which is always a Sunday. It is not the "available" balance the Wells
   Fargo app shows, and it is not a statement ending balance.
2. **Draw it at read time.** Never write it into the note. Show it as one more part of
   the period **Bank Badge**, with a quiet change since the previous close. Add a thin
   **balance lane** to Bank Period Charts on the same child axis.
3. **Show it only when bob can prove it.** Otherwise show "as of <date>" or "unverified",
   never a guess. Add a weekend rule so a Sunday close counts as settled as soon as
   Friday's postings are imported.

The full recommendation is in [§9](#9-recommended-solution).

> Numbers in mockups are illustrative. No real balance appears in this report.

---

## 1. What already exists

| Piece | Where | What it gives us |
| --- | --- | --- |
| QFX ledger balance on every import | `docs/bank.md` § Sources, § Journal; `.bob/bank/<host>.jsonl` `bank.import {balance_cents, balance_asof}` | The bank's own posted balance (OFX `LEDGERBAL`, never `AVAILBAL`) with its as-of date, append-only and git-synced. |
| Every posted transaction, immutable | `bank.txn {account, posted, cents, outcome…}`, including `before_start` | Signed cents by posted date, even for transactions before the account `start`. |
| Balance proof | `src/native/bank/status.rs` (`proof_for`, `transaction_sum`, `coverage_gap`) | Opening anchor = first ledger balance at/after `start` minus the journaled sum. Status values are `balanced`, `delta`, `gap`, `stale`, and `unverified`. Today this exists only as an account *status*, not as a per-date series. |
| Bank Badge on every Stats Strip | `bob-ledger-tools` `241n-plugin-bank-badge-model.js`, `241nb-…-hosts.js` | A read-only one-liner per period: `BANK · in +$… · out $… · N waiting · since … · to …`. Hidden when all three are zero. |
| Bank Period Charts on period notes only | `241nc/241nd/241ne-plugin-bank-period-*.js`; `bob bank report -p <id> -s -c` | In/Out on the child-period axis, Out by category, a roving readout, and a table twin. Never shown on daily notes or mobile. |
| Period notes | `YYYY/YYYY-Www.md`, `YYYY/YYYY-Qn.md`, `YYYY.md`, `all_time.md` with an empty `bob-stats-strip` fence | The strip, then the badge, then the charts all mount inside that one fence. Scaffolds are create-only. |
| House rules | `docs/bank.md`: "Totals are drawn when they are shown and never written into notes"; "No … balance is stored" (in config) | Read-time rendering is the established contract. |

The badge, the charts, and the journal already exist. The feature is mostly one new
bob computation, *balance on date D*, plus two small paint changes.

## 2. What your vault's data says

I ran a read-only script against `.bob/bank/*.jsonl` and `cash.md`. It printed only
deltas and counts, never balances.

1. **The chain is exact.** Take the first ledger balance (as of Nov 10) and add the
   journaled transactions. The result matches each of the four later bank balances
   (Nov 12, then Nov 13 three times) with a **$0.00** delta. Computing a balance on any
   date D from the journal is already proven to work on this data.
2. **No weekend postings.** Of 854 journaled transactions (May 1 – Nov 13), **0** have a
   Saturday or Sunday posted date. The breakdown is Mon 308, Tue 178, Wed 124, Thu 124,
   Fri 120. **Every period note ends on a Sunday**, because periods are whole ISO
   weeks. So a period's closing balance always equals the balance after the last
   weekday posting.
3. **Imports end at the last finished posting day.** A Friday-morning import reported
   coverage through Thursday. Sunday's and Monday's imports both reported coverage
   through Friday Nov 13. As a result, **today's W46 badge already reads "… · to Nov 13"**
   and calls the week partly covered, even though nothing can post on Nov 14–15. A
   balance feature would hit the same issue: without a weekend rule, the W46 close
   would read "as of Fri 13" until Tuesday's import.
4. **The history is already there.** The first QFX import covered **May 1 – Nov 10 in one
   continuous window** (843 `before_start` transactions plus a ledger balance). Closing
   balances are therefore provable for **29 weekly notes (W18–W46)**, the close of
   2026-Q2, and both ends of 2026-Q3. That works today, with no new imports.
5. **Your manual snapshots are a different number.** `cash.md ^balance` holds 18
   hand-recorded snapshots since Jan 2025, roughly monthly, with a gap from Mar to Jun 2026.
   The four that fall inside the evidence window come in **about $660–$2,400 below** the
   derived posted balance for the previous day. That pattern fits Wells Fargo's
   *available* balance: posted balance minus pending holds. Wells Fargo defines
   available balance as starting from the posted balance and adjusting for holds and
   pending transactions it knows about ([WF activity FAQ][wf]). The new feature can't
   reproduce the old habit's number, and it shouldn't try to (see ADJ-1).
6. **ISO periods are not calendar periods.** 2026-Q4 runs **Sep 28, 2026 – Jan 3, 2027**,
   because 2026 has 53 ISO weeks. Its closing balance is the Jan 3 balance, not the
   Dec 31 balance or any statement's ending balance.

## 3. Critique: is this a good idea?

**Yes, as long as it is framed correctly.**

Why it's worth doing:

- **It automates a habit you already keep.** The `^balance` snapshots show you want this
  number periodically. You've kept the habit for almost two years, with gaps and an
  irregular cadence. The period notes give it a fixed cadence (every Sunday) and a
  fixed home. They also give it bank-proven precision.
- **It costs little and carries little risk.** The evidence already exists, and the
  arithmetic is already proven in production code (`status.rs`). Nothing new is
  written to the vault.
- **Period notes are the right place.** They are where you look back. A stock (the
  balance) next to the flows (In/Out) answers "where did I end up?" next to "what
  happened?"

Where it could go wrong, and what handles each risk:

| Risk | Why it matters | Mitigation in this design |
| --- | --- | --- |
| **Wrong number type.** Posted vs available. | You'll compare it with the app and with your old snapshots, and they won't match. | Label it "posted" in the tooltip, with one line explaining available balance. Never call it "available". |
| **"It doesn't add up."** The change in balance ≠ In − Out. | The badge's In/Out exclude transfers, cash-account rows, and unclassified inflows. A $1,200 move to savings drops the balance but isn't spending. | The tooltip shows a **bridge**: in + out + transfers + other (+ untracked) = change. bob guarantees it sums exactly. |
| **False precision.** | A close shown before the period's postings are imported looks final when it isn't. | Finality states (§6.3). An "as of Fri 13" suffix appears whenever proof stops before the period end. Contradictions show "unverified", never a number. |
| **Privacy.** | A balance at the top of every weekly note is visible when screen-sharing, and the review agent reads period notes. | It's drawn at read time, so it's never in note bytes and agents reading the Markdown never see it. `stats.bank_balance: false` turns it off. A masked mode is an optional follow-up. |
| **Fixation.** | A weekly balance with no target can turn into a mood indicator. | Neutral ink. A drop is never red, matching the existing badge rule that spending isn't an error. The headline is the close plus its change, not a grade. |
| **A lone number has no context.** | "$4,312.43" means little without where it came from. | Show the change since the previous close, and a balance lane on the charts' child axis. |
| **No mobile.** | Strips, badges, and charts never render on mobile, because `bob` can't spawn there. | Accept it, consistent with every other strip value. If mobile matters later, the fix is family-wide, not balance-specific. |

**Would I take a different approach?** I'd keep your goal but change the framing. Don't
"write the balance into the note". Instead, "show where each period closed and how it
got there, drawn from bank-proven evidence". The concrete differences are in §4.

## 4. Requirement adjustments

I'm calling each change out so you can veto it.

| ID | Your requirement | Adjusted to | Why |
| --- | --- | --- | --- |
| **ADJ-1** | "total balance" | The **posted (ledger) balance**: what the bank has posted, excluding pending holds. | It's the only number that can be reconstructed for a past date and proven against the bank. QFX only carries `AVAILBAL` for the download moment, and bob already deliberately parses `LEDGERBAL` only. Your old snapshots look like available balances, so the two won't match, and the UI says so. |
| **ADJ-2** | "at the end of a given period" | The **end of the period's last day (Sunday, local time)**, meaning the balance after the last posting dated on or before that day. | It needs an exact definition to be testable. The tooltip names the last posting day ("last posting Fri Nov 13"). |
| **ADJ-3** | (implicit) Settles once imported through the end | A **weekend rule**: a Sunday close counts as settled once proof reaches the Friday before it, and Sat/Sun count as non-posting days. A `bob bank check` finding turns the rule off for an account if a weekend-dated posting ever appears. | Your data: 0 of 854 weekend postings, and imports report through Friday on Sat/Sun/Mon mornings. Without the rule, every week's close reads "as of Fri" until Tuesday. *Optional sibling fix:* apply the same rule to the existing badge's "to Nov 13" coverage caption. |
| **ADJ-4** | Wells Fargo checking only | **Every importable account with QFX balance evidence**, each as its own value in config order. Accounts are **never summed**. Today that is just `checking` ("WF Checking"). | `bank.accounts` is already a multi-account map. Summing checking and a credit card is meaningless, and net worth is out of scope. Cash and CSV-only accounts have no balance evidence, so they show nothing. |
| **ADJ-5** | (new) | Show the **change since the previous period's close**, and a **balance lane** in Bank Period Charts. | A level without a trend is hard to read. The chart's child axis already exists: daily closes for a week, weekly closes for a quarter or year, and quarterly closes for all time. |
| **ADJ-6** | (implicit) Starts with the bank tracking `start` | Balances are provable for **any date inside continuous QFX coverage that connects to a ledger balance**, even before `start`. | Balance is bank evidence, not row bookkeeping. You get 29 weeks of history (W18–W46) for free. Weeks before `start` show the balance with no In/Out, and the tooltip explains why. |
| **ADJ-7** | "see it in the file" | **Visible when the note is rendered** (Live Preview or Reading view, on desktop). It is **never written into the note's bytes.** | This matches the house rule "drawn, never written". It avoids stale-number and ownership problems, and keeps the balance out of agent-read Markdown (§5.2). |
| **ADJ-8** | No daily files | **Agreed, and enforced in the plugin only.** bob's day report may still carry the balance, so `bob bank report -D 2026-11-15` answers "what was it on the 15th?" in the terminal. | Your example question is a single-day lookup. The CLI should answer it even though the daily note stays clean. In the vault, the week note's balance-lane hover shows each day's close. |

## 5. Design options considered

### 5.1 Where it appears

| Option | Verdict | Reasoning |
| --- | --- | --- |
| **A. A part of the period Bank Badge** (`… · WF Checking $4,312.43 ▼ $512.52`) | ✅ **Headline** | The badge is already the money one-liner, already period-exact, gated, accessible, and read-only. It stays visible when the charts are collapsed. It needs no new host, fence, or scaffold migration. |
| **B. A balance lane in Bank Period Charts** (step line on the shared child axis) | ✅ **History** | It reuses the axis, readout, roving focus, and table twin. A drop that coincides with a large Out bar becomes visible. It is a separate small plot, not a second y-axis, so it isn't a dual-axis chart. |
| C. A sixth Stats Strip fact (`BALANCE`) | ❌ | Stats facts are bob-stats time/work metrics with "typical" medians. The glossary keeps the badge explicitly "not a Stats metric". |
| D. A new standalone balance line or tile host | ❌ (close second) | It would look good, but it adds a fourth stacked element and a fourth gate, and it duplicates the charts' axis as a sparkline. |
| E. A hand-placed `bob-bank-balance` fence or a `## Money` section | ❌ | Scaffolds are create-only, so 29+ existing notes would need migration. Prior research rejected the same idea for the charts. |

### 5.2 Persistence: read-time vs written

| Option | Verdict | Reasoning |
| --- | --- | --- |
| **Read-time from the journal** | ✅ | It follows the existing contract ("drawn, never written"). The journal is append-only and git-tracked, so values are reproducible. Late imports simply refine the value, with no ownership conflict. It also keeps money out of note bytes that agents read while drafting `## Review`. |
| Written once when settled (frontmatter `closing_balance:` or an inline field) | ❌ | Upside: mobile, grep, and Dataview. Downside: it contradicts "drawn, never written". It needs a settle protocol, a rewrite protocol for late Friday imports, and a "Bryan edited it" rule. It puts your balance into every agent's context. Prior research already rejected hand-maintained `closing_balance` fields for the same reason. |
| Into the agent-drafted Review via `bob periods brief` | ❌ | That writes money into prose. Prior research explicitly deferred "agent-brief money". |

### 5.3 Source of truth: journal vs rows

Use **journal amounts only**, which are the bank's immutable posted cents. Rows can be
edited, and typed rows may not be posted yet. A balance must equal what the bank would
say. `bob bank check` already reports edited amounts and missing rows separately, so
nothing is lost. Rows are used only to look up a transaction's **category** for the
bridge.

## 6. Recommended design

### 6.1 Definition

> **Closing balance of period P for account A** is the posted (ledger) balance of A at
> the end of P's last day E (local time), in signed integer cents: the bank's
> balance after every posting dated ≤ E.

### 6.2 Computation (bob)

1. **Evidence per account.** Use every OFX import window (`start..end`, not clipped
   to `start`), every ledger observation (`balance_cents @ balance_asof`), and every
   journaled transaction of any outcome, deduped by key as today.
2. **Spans.** Merge OFX windows into maximal continuous spans. A span is *anchored*
   when it holds at least one observation.
3. **Value on day D** inside an anchored span (D may also be the day before the span
   starts): take the nearest observation O and compute `O ± Σ cents posted between D
   (exclusive) and O.asof (inclusive)`, adding in the forward direction and subtracting
   in the backward one.
4. **Consistency.** Every observation in a span must chain to every other one with
   delta 0 (the existing `bank_balance_delta` logic, generalized). If any pair
   disagrees, the whole span is **unverified**: no number is shown, only the reason.
   This is deliberately conservative.
5. **After the last covered day L.** If `D > L`, the value is the balance at L.
   - The close is **settled** if every day in `(L, D]` is a Saturday or Sunday and the
     weekend rule is on for the account.
   - Otherwise the close is **as of L**.
6. **Journal health.** Malformed or unreadable journal lines put the account in the
   **unverified** state, mirroring `proof_for`.

Weekend-rule self-check: if a transaction with a Sat/Sun posted date ever appears for an
account, `bob bank check` emits an info finding (`bank_weekend_posting`), and that
account falls back to the strict rule.

### 6.3 Finality states

`close.state` takes one of these values:

| State | Rule | Badge text |
| --- | --- | --- |
| `settled` | Proof reaches E, or reaches the Friday before E under the weekend rule | `WF Checking $4,312.43` |
| `as_of` | The period is closed but proof stops at L < E (not weekend-only) | `WF Checking $4,312.43 as of Wed 11` |
| `so_far` | The period contains today | `WF Checking $4,312.43 as of Fri 13` (the badge already reads "so far" in its tooltip) |
| `stale` | `as_of` or `so_far` with L older than `bank.stale_after` days before today | Same text, with the date in warning ink |
| `unverified` | The span is inconsistent, or the journal is unreadable | `WF Checking unverified` (warning ink; the tooltip says to run `bob bank check`) |
| `none` | E is outside every anchored span (before the evidence starts or after a gap), CSV-only, or a cash account | Part omitted. The tooltip says why when there's room. |

### 6.4 JSON contract (additive, `schema_version: 1`)

`bob bank report` gains a `balance` object for every period kind:

```json
"balance": {
  "version": 1,
  "accounts": [{
    "alias": "checking", "label": "WF Checking", "kind": "checking", "default": true,
    "close":  { "date": "2026-11-15", "cents": 431243, "asof": "2026-11-13", "state": "settled" },
    "open":   { "date": "2026-11-08", "cents": 482495, "asof": "2026-11-06", "state": "settled" },
    "change_cents": -51252,
    "bridge": { "in_cents": 250000, "out_cents": -182012, "transfer_cents": -120000,
                "other_cents": 760, "untracked_cents": 0 },
    "low": { "date": "2026-11-10", "cents": 81210 },
    "evidence": { "since": "2026-04-30", "through": "2026-11-13", "observations": 5 },
    "reason": null
  }]
}
```

- `open` is the previous period's close. `change_cents = close − open` and is `null`
  unless both are numeric.
- **Invariant:** the bridge parts sum exactly to `change_cents`. `in` and `out` use the
  Totals rules on journal transactions joined to row categories. `transfer` is the net of
  transfers. `other` covers unclassified inflows. `untracked` covers transactions with
  no row, such as those before `start`.
- With `-c`, each `charts.buckets[]` gains `balances[] {alias, close_cents, asof, state}`.
  **Invariant:** the last bucket's close equals `balance.close`.
- Human `report` output gains one line:
  `WF Checking closed $4,312.43 · Sun Nov 15 (last posting Fri 13) · ▼ $512.52 since Nov 8`.
  With `-D 2026-11-15` the same line answers your example directly.

No new subcommand is needed. `report` already has every period selector, including
`-D`. If you later want a balance history table in the terminal, a read-only
`bob bank balance [-a ALIAS] [-D DAY] [-f human|json] [-p PERIOD]` could sit
alphabetically between `ack` and `check`. Treat that as an optional follow-up.

### 6.5 Display: badge part (period notes only)

The W46 note, as it renders on Monday morning (Nov 16), with the weekend rule on:

```
┃ BANK · in +$2,500.00 · out $1,820.12 · since Nov 11 · WF Checking $4,312.43 ▼ $512.52
```

A quiet week with no flows and no waiting rows still shows the balance. Today that
badge would be hidden:

```
┃ BANK · WF Checking $4,312.43 = unchanged
```

An open period (W47, viewed Wednesday):

```
┃ BANK · out $96.40 · 2 waiting · WF Checking $4,215.03 ▼ $97.40 as of Tue 17
```

Quarter, year, and all-time (whole dollars, per the badge's existing rounding rule):

```
┃ BANK · in +$9,850 · out $7,402 · since Nov 11 · WF Checking $4,312 ▲ $1,205       (2026-Q4, so far)
┃ BANK · in +$9,850 · out $7,402 · since Nov 11, 2026 · WF Checking $4,312 as of Fri 13   (all_time)
```

Paint rules, extending the existing badge contract:

- The part order is: flows (in, out, waiting), then coverage, then **balance last**. It
  reads like a statement summary ending in "ending balance", and it keeps the flows'
  coverage words ("since …") from appearing to qualify the balance.
- The part's word is the **account label** ("WF Checking"), which scales to two or three
  accounts as separate parts. The amount is in `--text-normal` at semibold, the one
  slightly heavier figure in an otherwise muted badge, using tabular numerals.
- The change uses `▲` in `--bob-bank-in-ink` (green) or `▼` in body ink, and `=` when
  unchanged. It is **never red.** Glyph plus words carry the meaning (aria: "down
  $512.52 since November 8"). It is omitted when `open` is unknown.
- The `as of Wed 11` suffix is faint ink, like the coverage words. It is warning ink
  when `stale`.
- **Tone is unchanged.** Chrome color stays driven by In vs Out only, and the balance
  never tints the badge.
- **Visibility:** on period notes, a balance part keeps the badge visible even when
  in, out, and waiting are all 0. Day badges never request or show it.

Tooltip, added after the existing lines:

```
WF Checking · posted balance
Closed $4,312.43 Sun Nov 15 (last posting Fri Nov 13)
Opened $4,824.95 Sun Nov 8 · ▼ $512.52
  in +$2,500.00 · out −$1,820.12 · transfers −$1,200.00 · other +$7.60
Low $812.10 Tue Nov 10
✓ Agrees with 5 Wells Fargo balances · latest Fri Nov 13
Posted balance excludes pending holds; the app's available balance may be lower.
```

Activation is unchanged: it opens the oldest waiting row, the first money day, the
month note, or `bank.md`. A balance-only badge opens the bank month note at the last
posting day's heading, or `bank.md` when there is none. Activation stays read-only.

### 6.6 Display: balance lane in Bank Period Charts

```
 ▾ BANK CHARTS   ◐                         Tue 10 · out $312.40 · close $812.10
  WF Checking ─┐                    ┌──────┐                                 ●  $4,312.43
  ○            └────────┐   ┌───────┘      └──────────────────────────────── 
                        └───┘                                                      ← balance lane (≈28 px)
  ─────────────────────────────────────────────────────────────────────────── 0
   ▮        ▮▮     ▮     ▮▮▮      ▮                                               ← In / Out (existing)
   Mon 9    Tue 10  Wed 11  Thu 12  Fri 13  Sat 14  Sun 15
```

- It is a **separate small plot** above the In/Out chart on the **same columns**. One
  y-scale per plot, never dual-axis. It rides with the In/Out view: Both shows it, and
  so does In/Out-only. Categories-only hides it.
- **Mark:** a 2 px **step-after** line in muted text ink. A balance is flat between
  postings, so a step is the honest shape. A hollow ring sits at the left edge for the
  opening balance, and a filled ≥ 8 px dot at the close carries the **only direct
  label** (the closing amount). Following the dataviz anti-patterns guidance, there are
  no per-point numbers.
- **Y-domain:** fitted to the min and max of the visible closes with ~10% padding
  (a line, unlike a bar, needs no zero baseline). If the range crosses $0, a faint zero
  rule is drawn and the overdraft segment uses warning ink. That is the one state that
  earns color.
- **States on the line:** a gap with no line for `none`. A dashed segment for `as_of`
  or `so_far` days past the last proof, which is never interpolated. Future buckets are
  empty.
- **Readout and focus:** the existing roving readout gains `close $…` for the focused
  column. The table twin gains a **Close** column. No new tab stops.
- **Single series:** no legend. The lane's tiny label ("WF Checking") names it. With
  several accounts, show one lane per account, stacked, each with its own name label.

### 6.7 Config

`stats.bank_balance` in `~/.config/bob/config.yml` defaults to `true`. It hides both the
badge part and the balance lane, and is independent of `stats.bank_badge` and
`stats.bank_period`. When `stats.bank_badge` is false, the whole badge is gone,
including the balance, and the lane still follows `stats.bank_period`.

Optional, not v1: `stats.bank_balance: masked`, which shows `$•,•••.••` until hover or
focus, for screen-sharing.

## 7. Implementation plan

**Sequencing.** Ship bob first. The JSON is additive, and older plugins ignore it. The
plugin ships second and tolerates a missing `balance` (older bob means no part, with no
warning noise).

**bob-cli** (`src/native/bank/`)

1. Add `balance.rs` (new): evidence spans, `close_on(alias, D)`, consistency check,
   weekend rule, bridge, and low. Refactor `status.rs` to reuse the shared span and sum
   helpers so the status and the series never disagree.
2. Add the `balance` object and the `charts.buckets[].balances[]` field in `report.rs`
   and `charts.rs`, plus the human line in `output.rs`.
3. Add the `bank_weekend_posting` info finding in `check.rs`.
4. Tests, using synthetic QFX fixtures only:
   - an anchor after the period, before it, and inside it;
   - a coverage gap;
   - a chain delta, which must yield `unverified`;
   - weekend settle;
   - a Friday-holiday week (e.g. W52 2026, where Dec 25 is a Friday), which must yield
     `as_of`;
   - an open period, and all-time;
   - `before_start` history;
   - a CSV-only account, which must yield `none`;
   - two accounts;
   - bridge-sum and last-bucket invariants as property tests.
5. Docs: a "Closing balance" section in `docs/bank.md`, the JSON outputs reference, and
   one sentence in `docs/stats.md` for the gate. Don't edit `CHANGELOG.md` or the version,
   because the release train owns them.

**bob-plugins** (`plugins/bob-ledger-tools/src/`)

1. In `241n-…-bank-badge-model.js`, add the balance part for period kinds, the
   visibility exception, the tooltip and aria lines, and the activation fallback. Keep
   each fragment ≤ 1000 lines. Then run `npm run build`, `npm test`, and
   `bob plugins sync`.
2. In `241nc/241nd-…-bank-period-*.js`, add the lane model, the step-path paint, the
   readout field, and the table-twin column.
3. In `styles.css`, add `.bob-bank-badge-part-balance`, the delta inks, and the lane
   styles, including forced-colors and the light and dark themes.
4. Extend the host tests and e2e (`scripts/test-ledger-tools-bank-*.cjs`,
   `obsidian-bank-ui-e2e.cjs`).

**Memory and decisions** (after you accept, via `/sase_memory_write`)

- Update the glossary Bank Badge strand: it may end with a closing-balance part on
  period notes.
- Possibly add a decisions record: "Period closing balances are posted balances drawn
  from bank evidence at read time, never written into notes."

**Estimated size:** about one medium bob bead plus one medium plugin bead.

## 8. Open questions for you

1. **Posted vs available.** Are you comfortable that this number won't match the app's
   headline "available balance"? I recommend yes. The posted balance is the only
   provable, historical one.
2. **History before `start`.** Should W18–W45 show balances, with no In/Out? I recommend
   yes. It's free and accurate.
3. **Weekend rule for the existing coverage caption.** Should the same rule also drop
   the "to Nov 13" on closed weeks' flow badges? I recommend yes, as a separate small
   change.
4. **Masked mode.** Do you screen-share period notes? If so, add `masked` in the same
   change.
5. **Retire `cash.md ^balance`?** Once this ships, the manual snapshot task is
   redundant. You could keep the old snapshots as history, and optionally plot them as
   hollow "manual (available)" points on all-time later.

## 9. Recommended solution

**Build "Closing balance" as a read-time, bank-proven, period-only extension of the
existing bank layer.**

1. **Definition.** For each importable account with QFX evidence (today: WF Checking),
   the closing balance is the **posted (ledger) balance at the end of the period's last
   day**, always a Sunday. It is never the available balance, and accounts are never
   summed.
2. **bob computes it** from the import journal alone: QFX ledger balances plus immutable
   posted transactions, across continuous coverage spans (including before `start`).
   Every observation in a span must chain with a $0 delta. A **weekend rule** settles a
   Sunday close once Friday's postings are in, and a check finding guards that rule.
   bob adds an additive `balance` object to `bob bank report` with close, open, change,
   an exactly-summing bridge, the low, finality state, and per-bucket closes under `-c`.
   `bob bank report -D 2026-11-15` answers your example in the terminal.
3. **The plugin paints it in two existing places on period notes only:**
   - a final **`WF Checking $4,312.43 ▼ $512.52`** part on the Bank Badge, with an
     "as of …" suffix when proof stops short and "unverified" when it can't be proven;
   - a slim **step-line balance lane** above In/Out in Bank Period Charts, on the same
     child axis, with the close as its only direct label and a Close column in the
     table twin.
   Daily notes never show it. `stats.bank_balance` turns it off.
4. **Nothing is written to any note.** The value is reproducible from the git-tracked
   journal, stays out of the Markdown that agents read, and refines itself when late
   imports land.

On your vault this would light up `2026-W46` immediately with a settled Sun Nov 15 close
(proof through Fri Nov 13, weekend rule). It would also backfill 28 earlier weekly notes
(W18–W45) from evidence you've already imported.

---

### Sources

- Wells Fargo, *Online banking activity FAQs* (available vs posted balance): [wellsfargo.com/help/online-banking/activity-faqs][wf]
- TD Bank, *Available balance vs posted balance*: <https://www.td.com/us/en/personal-banking/learning/money-management/available-balance-vs-posted-balance>
- OFX 2.1.1 schema, `LEDGERBAL` (BALAMT + DTASOF required): <https://schemas.liquid-technologies.com/OFX/2.1.1/ledgerbal.html>
- Tryton forum, OFX balance date can differ from statement end: <https://discuss.tryton.org/t/statement-import-in-ofx-format-final-balance-required/8828>
- In-repo: `docs/bank.md` (Sources, Journal, Account status, Bank badge, Bank period charts); `src/native/bank/status.rs`, `report.rs`; `bob-plugins/plugins/bob-ledger-tools/src/241n*-plugin-bank-*.js`, `239-plugin-period-strip-fence.js`, `styles.css`; glossary strands `bank-badge`, `period-note`, `stats-strip`; prior research `202611/bank_period_charts/…__final.md`, `202611/bank_daily_acknowledgment/…__final.md`.
- Vault evidence (read-only, amounts never printed): `~/bob/.bob/bank/*.jsonl`, `~/bob/bank.md`, `~/bob/cash.md ^balance`, `~/bob/2026/2026-W46.md`, `~/bob/2026/2026-Q4.md`, `bob bank report -p 2026-W46`.

[wf]: https://wellsfargo.com/help/online-banking/activity-faqs
