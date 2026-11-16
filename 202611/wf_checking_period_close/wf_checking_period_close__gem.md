# Wells Fargo Checking Account Balances in Period Notes — Design & Critique

> **Research scope:** Architecture, reliability analysis, critique, and UX/visual design for displaying period-end Wells Fargo checking balances in Bob period notes (`YYYY-Www`, `YYYY-Qn`, `YYYY`, `all_time`), while excluding daily notes.

---

## Executive Summary & Recommended Solution

**Yes — this is a strong, high-leverage feature**, provided three core assumptions are refined before implementation. Right now, Bryan tracks checking balances manually via a recurring 30-day chore in [`recur.md`](/home/bryan/bob/recur.md) (`Update [[cash#^balance]]`) that writes irregular mid-day snapshots into [`cash.md`](/home/bryan/bob/cash.md). Meanwhile, `bob bank` already ingests Wells Fargo QFX `LEDGERBAL` anchors and every posted transaction (including 843 `before_start` transactions back to `2026-05-01`) into `.bob/bank/<host>.jsonl`.

Using that journal to reconstruct exact daily closing balances lets every period note show **stock** ("where checking landed") right alongside **flow** ("how much came in and went out").

### Recommended Architecture at a Glance

1. **Live-rendered, read-only UI inside `bob-bank-period-host` (`bob-stats-strip`), never written to Markdown:**
   - Extend `bob bank report` (`src/native/bank/report.rs` and `charts.rs`) to compute per-account historical balances (`balances[]` and `charts.balances[]`) from contiguous OFX/QFX windows and anchors in `.bob/bank/*.jsonl` (including `before_start` transactions).
   - Render a calm, period-only **Balance Header + Inline Sparkline** inside `.bob-bank-period-host` in `bob-ledger-tools` — directly above the collapsible `BANK CHARTS` body. Because `.bob-bank-period-host` already attaches **exclusively** to `week`, `quarter`, `year`, and `all_time` strips (never daily notes, `bob-period-parts`, embeds, popovers, or mobile), this satisfies *"not for daily files"* structurally with **zero Markdown edits**, **zero extra subprocess spawns**, and **retroactive support** across existing period notes (`2026-W45`, `2026-W46`, `2026-Q3`, `2026-Q4`, `2026`, `all_time`).
2. **Honest handling of Wells Fargo QFX weekend/holiday dates (`as of Fri Nov 13` → auto-promoted to `on Sun Nov 15`):**
   - Live journal inspection proves Wells Fargo QFX sets `<DTEND>` and `<LEDGERBAL><DTASOF>` to the **last posted transaction date**, not the download date. Even after Bryan imported fresh QFX files on Monday `2026-11-16`, both exports ended at `2026-11-13` ($7,760.04) because nothing posted Sat–Sun.
   - Instead of hiding `2026-W46`'s balance until the next Monday import (`2026-11-23`) or silently mislabeling Friday's balance as Sunday's, show `$7,760.04 · as of Fri Nov 13` immediately on Monday morning, and automatically promote it to verified `on Sun Nov 15` as soon as a subsequent QFX export crosses past `2026-11-15`.
3. **Account-kind scoping (`kind: checking`) rather than hardcoding "Wells Fargo checking":**
   - Compute period balances in `bob` for every non-cash account, and default the period-note UI to `kind: checking` using each account's authored `label` (`WF Checking`). This handles Bryan's single account today and prevents future `credit` or `savings` accounts from accidentally summing debt into checking cash.

---

## 1. Empirical Ground Truth: Current System & Live Vault Reality

Inspecting `bob-cli`, `bob-plugins`, and the live vault surfaced several concrete facts that shape the design:

### 1.1 Existing Vault & Workflow Context

- **Account config (`~/bob/bank.md`):**
  ```yaml
  bank:
    accounts:
      checking:
        label: WF Checking
        kind: checking
        start: 2026-11-11
  ```
- **Manual legacy snapshot chore (`~/bob/recur.md#L9` & `~/bob/cash.md#L253-L273`):**
  - `recur.md` carries `- [?] #task Update [[cash#^balance]] contains snapshots of my @BANK account balance [repeat:: every 30 days when done]`.
  - `cash.md` holds 18 manual timestamps (`250118@0000 $69,044.29` through `261101@0950 $14,918.67`) captured at arbitrary times of day and drifting month dates (missing Mar–Jun 2026).
- **Weekly QFX ritual (`~/bob/gtd_daily.md#L18,L39`):**
  - Every Monday (`PRE #browser`), Bryan downloads Wells Fargo Checking QFX (`default dates (≥ 14 days)`), runs `bob bank import ~/Downloads/*.qfx && rm ~/Downloads/*.qfx`, and files waiting rows.
- **Period notes (`docs/periods.md` & `~/bob/2026/2026-W46.md`):**
  - Period notes partition time in whole ISO weeks (`YYYY-Www`, `YYYY-Qn`, `YYYY`, `all_time`).
  - Owned strictly by `bob` (create-only deterministic scaffold, never edited later) and `bob-ledger-tools` (live `bob-stats-strip` and `bob-period-parts` fences). *"No number is ever written into Markdown."*

### 1.2 Live `.bob/bank/` Journal Findings (`kellys-macbook-pro-local.jsonl`)

Reading the live journal (`859` events: `5` `bank.import`, `854` `bank.txn`) reveals two crucial realities:

| Import # | Import `ts` (UTC) | `start` .. `end` | `balance_asof` | `balance_cents` | Counts |
|---:|---|---|---|---|---|
| 1 | `2026-11-12T11:55:24Z` | `2026-05-01` .. `2026-11-10` | `2026-11-10` | `822974` ($8,229.74) | `before_start: 843` |
| 2 | `2026-11-13T11:13:32Z` | `2026-11-12` .. `2026-11-12` | `2026-11-12` | `797997` ($7,979.97) | `new: 7` |
| 3 | `2026-11-15T11:41:20Z` | `2026-08-18` .. `2026-11-13` | `2026-11-13` | `776004` ($7,760.04) | `new: 4, seen: 392` |
| 4 | `2026-11-16T11:26:32Z` | `2026-08-19` .. `2026-11-13` | `2026-11-13` | `776004` ($7,760.04) | `seen: 389` |
| 5 | `2026-11-16T14:23:08Z` | `2026-08-19` .. `2026-11-13` | `2026-11-13` | `776004` ($7,760.04) | `seen: 389` |

Reconstructing backward from `2026-11-13` (`776004`) across `bank.txn` confirms exact penny-for-penny agreement across all three QFX anchors (`2026-11-13`, `2026-11-12`, `2026-11-10`) and unlocks continuous end-of-day checking balances back to `2026-05-01`:

| Period / Date | Span | Reconstructed End Balance | Period Change (`Δ`) | Notes |
|---|---|---:|---:|---|
| `2026-Q2` (`2026-06-28`) | Mar 30 – Jun 28 | **$73,916.86** | — | Coverage starts May 1 (`open` unknown) |
| `2026-Q3` (`2026-09-27`) | Jun 29 – Sep 27 | **$32,164.40** | −$41,752.46 (−56.5%) | `0` rows in `bank/` (all `before_start`) |
| `2026-W43` (`2026-10-25`) | Oct 19 – Oct 25 | **$18,403.73** | — | Covered by `Checking (3).qfx` |
| `2026-W44` (`2026-11-01`) | Oct 26 – Nov 1 | **$17,312.12** | −$1,091.61 (−5.9%) | Compare `cash#^balance`: `261101@0950 $14,918.67` |
| `2026-W45` (`2026-11-08`) | Nov 2 – Nov 8 | **$8,960.31** | −$8,351.81 (−48.2%) | `0` rows in `bank/` (`start: 2026-11-11`) |
| `2026-W46` (`2026-11-15`) | Nov 9 – Nov 15 | **$7,760.04** *(as of Nov 13)* | −$1,200.27 (−13.4%) | Sat 14 & Sun 15 awaiting next QFX past Nov 15 |
| `2026-Q4` / `2026` / `all_time` | Open | **$7,760.04** *(as of Nov 13)* | −$24,404.36 *(Q4 so far)* | Live current balance |

### 1.3 Why Existing `status.rs` Cannot Do This Alone

In `src/native/bank/status.rs`:
- `proof_for` (`L81-L197`) only evaluates the **single latest** QFX `balance_asof` (`accounts[].balance_cents` = `776004`) — it never computes historical balances at arbitrary dates like `2026-11-08` or `2026-09-27`.
- `transaction_sum` (`L213-L230`) and `ledger_transaction_sum` (`L232-L256`) explicitly skip `TxnOutcome::BeforeStart` and events before `account.start` (`2026-11-11`), because `status.rs` checks consistency against vault rows in `bank/*.md`.
- Therefore, historical period-end reconstruction needs a dedicated, journal-backed balance-series engine in `src/native/bank/`.

---

## 2. Critique of the Plan & Justified Requirement Adjustments

### Is This a Good Idea?
**Yes — with high confidence.** Showing checking balance in period notes solves three real problems at once:
1. **Eliminates manual toil & drift:** Retires the 30-day `Update [[cash#^balance]]` chore in `recur.md` in favor of automatic, exact end-of-day settled bank balances aligned to ISO weeks, quarters, and years.
2. **Completes the financial picture (Stock + Flow):** `bob bank report` intentionally excludes `[cat:: transfer]` and uncategorized inflows from `In`/`Out`. In `2026-W46`, for example, `Out` is `$469.70` (covering `Nov 11–13`), while checking actually dropped `−$1,200.27` from `W45` (`$8,960.31 → $7,760.04`, including `Nov 9–10` activity). Seeing both **flow** and **ending balance** prevents false impressions when large transfers, brokerage moves, or pre-start activity occur.
3. **Fits Bob's review cadence:** Period notes are already where Bryan pauses on Mondays (`Weekly review` in `gtd_daily.md`), quarterly, and yearly; excluding daily notes keeps day-to-day views uncluttered and avoids intra-day QFX pending/posted noise.

### Critical Flaws in a Naive Implementation & Explicit Requirement Adjustments

| # | Naive Assumption | What Breaks in Reality | Explicit Requirement Adjustment |
|---|---|---|---|
| **A1** | *"Put the balance somewhere in `2026-W46.md`"* by writing it into the Markdown file | Violates `docs/periods.md` ("deterministic create-only scaffold; no number is ever written into Markdown") and `docs/bank.md` ("totals are drawn when shown"). Also causes git churn on `vault-sync`, goes stale when QFX imports settle later, and requires migrating existing notes. | **Render live at read time inside `bob-stats-strip`'s `.bob-bank-period-host`** (no Markdown writes, no template migration, works retroactively on all existing period notes). *(Trade-off noted below for Mobile / raw editors.)* |
| **A2** | *"Show the balance on `2026-11-15` in `2026-W46.md`"* requiring QFX coverage `>= 2026-11-15` | Wells Fargo QFX sets `DTEND` and `DTASOF` to the **latest posted transaction date** (`2026-11-13`), not the download date (`2026-11-16`). Requiring `DTEND >= Sun` hides `2026-W46`'s balance on almost every Monday morning right when Bryan wants it for his Weekly Review! | **Distinguish `verified` (`end_asof == period.end`) from `as_of` (`period.start <= end_asof < period.end`) and `so_far` (open period).** Show `$7,760.04 · as of Fri Nov 13` immediately on Monday morning, and auto-promote to verified `on Sun Nov 15` once the next QFX import passes Sunday. |
| **A3** | Reconstruct from `account.start` (`2026-11-11`) or vault Markdown rows (`bank/*.md`) | Loses 6+ months of `before_start` QFX history already in `.bob/bank/*.jsonl`, and breaks if a user deletes/edits a vault row (`bank_amount_edited`). | **Reconstruct from immutable QFX `bank.import` `LEDGERBAL` anchors + `bank.txn` (including `before_start`) inside contiguous OFX components.** Surface vault-row `delta` as a warning indicator (`⚠ Δ`), never as a corrupted bank balance. |
| **A4** | Hardcode `"Wells Fargo checking"` or sum all `accounts[]` | Breaks if Bryan adds a `credit` card (negative debt summed with cash!) or renames `checking`'s label, or adds a second checking account. | **Compute per-account in `bob bank report`, filter UI to `kind: checking` by default** (overridable via `stats.bank_balance_accounts`), and display `account.label` (`WF Checking`). |
| **A5** | Reuse `bankBadgeModel` / `bankPeriodChartsModel` visibility (`hide when in == 0 && out == 0 && waiting == 0`) | `2026-W45`, `2026-Q3`, `2026-Q2`, and quiet no-spend weeks have `0` flow rows in `bank/` yet have known, meaningful checking balances. | **Give the Balance Band independent visibility inside `.bob-bank-period-host`:** render whenever any displayed account has non-`future`/`untracked` balance data, even when `BANK CHARTS` and `BANK` badge are hidden. |
| **A6** | Round longer periods (`quarter`, `year`, `all_time`) to whole dollars like `Bank Badge` does for flow | A checking balance (`$7,760.04` vs `$32,164.40`) is a reconcilable bank statement figure; rounding `$32,164.40` to `$32,164` obscures exact reconciliation. | **Always display exact cents (`$X,XXX.XX`) for account balances across all period levels**, paired with exact period `Δ` (`−$1,200.27`) and percentage (`−13.4%`). |
| **A7** | Assume all `bank.txn` events are OFX and all QFX anchors are settled | Future CSV imports (`source: "csv"`) generate distinct `csv:...` keys in the same `transactions` map and would double-count against OFX; mid-day same-day QFX downloads can be superseded by end-of-day postings. | **Only sum OFX-sourced transactions within contiguous OFX coverage components**, anchor backwards from each component's latest `(balance_asof, ts)`, and cross-check settled anchors in `bob bank check`. |

### Honest Trade-off: Obsidian Mobile & Plain Text Editors
Because Bob renders `bob-stats-strip`, `bob-bank-badge`, and `bob-bank-period` by spawning `bob` on desktop (`dayStripCanSpawn()`), **live balances will appear in Obsidian Desktop and via `bob bank report` in the terminal, not in Obsidian Mobile or raw Markdown (`nvim`/`cat`)**.
- *Why we still strongly prefer live rendering over writing to Markdown:* Writing mutable balances into period notes breaks Bob's strongest invariants (create-only scaffolds, zero note churn, no financial balances leaked into `bob periods brief` or git commit history). And for mobile glanceability, `bob bank report` or a future optional static snapshot command (`bob bank snapshot` into a dedicated note like `cash#^balance`) remains orthogonal without polluting period notes.

---

## 3. Architectural Comparison: Where Should Data & UI Live?

### 3.1 Data Computation Options

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **1. Write balance into period note Markdown / frontmatter on `import` & `periods ensure`** | Visible in plain text / Mobile. | Violates `periods.md` & `bank.md` ownership rules; stales across imports; creates git merge conflicts with `## Reflection`/`## Intentions`; requires migrating all existing notes. | **Reject** |
| **2. Compute inside `bob periods show`** | Single JSON payload for strip + parts. | Forces every `bob periods show` call to scan `bank/` and `.bob/bank/*.jsonl`; duplicates `bob bank` config/journal logic; violates `bob` noun boundaries (`cli_rules.md`). | **Reject** |
| **3. Extend `bob bank report` (`-p`/`-w`/all) + `charts.balances`** | Reuses exact file/journal load already paid by `bob-bank-period-hosts`; <1 ms extra CPU; single source of truth for Obsidian & terminal (`bob bank report`). | Requires desktop `bob` spawn (already standard for all strips/charts). | **Recommended** |

### 3.2 UI Placement Options in Period Notes

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **1. Inline inside existing `Bank Badge`** (`BANK · out $469.70 · checking $7,760.04`) | Zero vertical footprint. | Cramped wrapping; conflates flow vs stock; hides when `stats.bank_badge: false` or `In/Out = 0` (`2026-W45`); no room for `Δ`, open→close context, or trajectory sparkline. | **Reject** |
| **2. New Markdown code-block fence (`bob-bank-balance`)** | Explicit in note source. | Requires scaffold change + migrating every existing `2026-W*`, `2026-Q*`, `2026`, `all_time` note; causes an extra `bob` spawn per note. | **Reject** |
| **3. Balance Band + Sparkline inside existing `.bob-bank-period-host` (above collapsible `BANK CHARTS`)** | **Already excluded from daily notes, embeds, popovers, mobile, and `bob-period-parts`!** Zero note migration; zero extra spawns; stays visible when charts collapse or when `In/Out = 0`; synchronizes hover readout with `IN / OUT` columns. | Adds ~2.5 lines of clean vertical rhythm under the Bank Badge. | **Recommended** |

---

## 4. Recommended Solution: Complete Technical & Visual Design

### 4.1 Visual Design & Layout (`bob-ledger-tools`)

Following `bob-ledger-tools`'s existing design grammar (`styles.css` lines 8987–10180 & `239-plugin-period-strip-render.js` line 225: *"No cards, borders, backgrounds, shadows, or buttons; hue appears only in bars and stacks"*):

- Use the existing `.bob-bank-period` **quiet 2px left hairline** (`border-inline-start: 2px solid ...`), `0.75em` base scale, `tabular-nums`, and small-caps labels.
- Place a **Balance Band** (`.bob-bank-balance`) as the top zone of `.bob-bank-period`, **outside** the collapsible `BANK CHARTS` body so collapsing charts never hides the ending balance.

#### Mockup 1: Weekly Note with Flow + Provisional Weekend As-Of (`2026-W46.md` on Mon `2026-11-16`)

```text
▌ BANK · out $469.70 · since Nov 11 · to Nov 13

▌ WF CHECKING                                                    ╭──────────────────╮
  $7,760.04   −$1,200.27 (−13.4%)  as of Fri Nov 13              │ ●──●──●─╲        │
                                                                 │          ● · · ○ │
  ▾ BANK CHARTS  [◫]                         Fri 13 · out $219.93 · 4 rows · bal $7,760.04
  IN / OUT                                   OUT BY CATEGORY
  ──●─────●──────                            💻 Tech & AI      ███████░░  $246.38  52%
    █  █  █  ░  ░                            📆 Loans          ████░░░░░  $137.16  29%
  Mon Tue Wed Thu Fri Sat Sun                ☕ Coffee         ██░░░░░░░   $43.20   9%
                                             🛍️ Shopping       █░░░░░░░░   $27.59   6%
                                             🏪 Convenience    ▌░░░░░░░░   $12.72   3%
                                             👤 Personal       ▏░░░░░░░░    $2.65   1%
```
*(Note: Once next Monday's QFX crosses `2026-11-15`, `as of Fri Nov 13` automatically changes to `on Sun Nov 15`, and the dashed Sat–Sun tail `· · ○` fills in solid.)*

#### Mockup 2: Closed Historical Week with Zero `bank/` Rows (`2026-W45.md` on Mon `2026-11-16`)

```text
▌ WF CHECKING                                                     ╲
  $8,960.31   −$8,351.81 (−48.2%)  on Sun Nov 8                    ╲──●──●──●──●──●
```
*(No `BANK` badge and no empty `BANK CHARTS` chrome; just one serene, self-contained balance band showing exact closing cash and the Tue Nov 3 step-down.)*

#### Mockup 3: Open Quarter (`2026-Q4.md`) & Partial-Start Quarter (`2026-Q2.md`)

```text
▌ BANK · out $469.70 · since Nov 11 · to Nov 13
▌ WF CHECKING
  $7,760.04   −$24,404.36 (−75.9%)  as of Fri Nov 13 · so far    ╲──╲__╲__● · · · ○
  ▾ BANK CHARTS ...
```
And for `2026-Q2.md` (coverage starts `May 1`, so `Q1` end on `Mar 29` is unknown):
```text
▌ WF CHECKING
  $73,916.86   on Sun Jun 28 · tracked since May 1                · · · ●──╱──╲──●
```
*(No `Δ` is fabricated when `open_cents` is unknown.)*

#### Mockup 4: Anomaly / Error States (`delta` & `stale`)

- **`delta` (`ledger_delta_cents != 0`):** Subtle `--text-warning` left hairline tint + compact `⚠ ledger Δ −$13.71` chip next to the date; tooltip explains *"Bank QFX balance is $7,760.04, but vault rows in bank/2026-11.md differ by −$13.71 — run bob bank check."*
- **`stale` (open period & `today - end_asof > stale_after`):** Quiet `--text-warning` `as of Nov 13 · stale` label.
- **`gap` / `untracked` / `unverified`:** Never render `$0.00`. Hide silently for pre-tracking periods (`2025`, `2026-Q1`, `2026-W01..W17`) and future periods (`2026-W48`); show a single muted `WF Checking · unverified (import QFX for balance)` line only on active CSV-only periods.

#### Typography, Color, Accessibility & Interaction Rules

| Element | Styling & Behavior |
|---|---|
| **Balance numeral** | Exact cents (`$7,760.04`), `font-size: 1.35em` inside the `0.75em` host (`~1.01em` effective), `font-weight: 650`, `font-variant-numeric: tabular-nums`, `--text-normal`. |
| **Period delta (`Δ`)** | Signed currency + percentage (`−$1,200.27 (−13.4%)` or `+$2,450.00 (+31.2%)`). Uses `--bob-bank-in-ink` green **only** when `delta_cents > 0`; neutral `--text-muted` when `delta_cents <= 0` (consistent with `docs/bank.md`: spending/balance decline is neutral, never red). |
| **Temporal tag** | Muted (`--text-faint` / `--text-muted`): `on Sun Nov 15` (verified close), `as of Fri Nov 13` (closed period awaiting post-weekend QFX), `as of Fri Nov 13 · so far` (open period). |
| **Balance sparkline** | Crisp inline SVG (`width: 100%`, `max-width: 180px`, `height: 28px`, `preserveAspectRatio="none"` with CSS-styled stroke), Y-axis padded `[min − 15% span, max + 15% span]` (flat center line if constant). Solid path over covered buckets, subtle `8%` fill beneath, dashed muted segment over trailing `awaiting_import` / `future` buckets. |
| **Synchronized hover/focus** | Hovering/focusing bucket `i` in `IN / OUT` highlights bucket `i` on the sparkline (active circle marker) and appends `· bal $X,XXX.XX` to the `.bob-bank-period-readout` text. Hovering points on the sparkline updates the same readout and dims non-matching columns. |
| **Tooltip (`title`)** | Shows account label & proof status (`WF Checking · ✓ balanced`), exact open date & amount, exact end date & amount, exact net change & %, intra-period low–high range, QFX coverage window & `last_import` date, and click action. |
| **Click / Enter / Space** | Read-only navigation (never creates notes): opens `end_asof`'s day heading in `bank/YYYY-MM.md` if present, else opens `bank.md` (`Ctrl`/`Cmd`/middle-click opens in new leaf). |
| **Screen reader & tabular parity** | `aria-label` summarizes balance, date, and delta; visually-hidden `.bob-bank-period-sr` `<table>` carries every bucket's exact `end_cents` alongside `in`/`out`/`net`. |
| **Responsive (`@container`)** | Wide (`>= 34em`): `grid-template-columns: minmax(0, 1fr) minmax(120px, 180px)` (numeral left, sparkline right). Narrow (`< 34em`): stacks vertically, sparkline full-width below numeral. |

---

### 4.2 Backend Algorithm & Correctness Proofs (`src/native/bank/`)

Create a dedicated pure module `src/native/bank/balance.rs` invoked by `report.rs`:

1. **Contiguous OFX Component Partitioning:**
   - Filter `journal.imports` to `event.account == account.alias && event.source == SourceKind::Ofx && event.start <= event.end`.
   - Sort and merge overlapping or adjacent (`cur_end + 1 day == next_start`) intervals into maximal contiguous components $C_m = [w_{\text{start}}, w_{\text{end}}]$ (reusing `merge_windows` from `subscriptions/coverage.rs`).
2. **Canonical Component Anchor & Settled Cross-Check:**
   - Within each $C_m$, collect anchors with `balance_cents: Some(b)` and `balance_asof: Some(asof)` where `w_start <= asof <= w_end`.
   - Select the canonical anchor `A_m = anchors.max_by_key(|e| (e.balance_asof, e.ts, e.line))`. Preferring the latest `balance_asof` and latest `ts` ensures settled end-of-day balances supersede earlier mid-day downloads on the same date.
   - **CSV Safety Guard:** Add optional `"source": "ofx" | "csv"` to new `bank.txn` journal events (`journal.rs` & `import_plan.rs`). When reconstructing balances, include **only** `Ofx` transactions (including `TxnOutcome::BeforeStart`). For legacy `bank.txn` events lacking `"source"`, infer `"ofx"` if no CSV `bank.import` overlaps `[w_start, w_end]` (and mark `unverified` if an ambiguous CSV+OFX mixed overlap exists).
   - Build a `BTreeMap<NaiveDate, i64>` of daily OFX net cents (`txns_by_day`) and prefix sums over $C_m$.
   - **Consistency check:** For every earlier settled anchor $E$ in $C_m$ (where `local_date(E.ts) > E.asof` and `E.asof < A_m.asof`), verify $B(E.\text{asof}) == E.\text{balance\_cents}$. Emit `bank_balance_anchor_mismatch` warning in `bob bank check` if they ever disagree.
3. **Exact Closing-Balance Query $B(d)$ for Any Date $d$:**
   - Locate component $C_m$ where $w_{\text{start}} \le d \le A_m.\text{asof}$.
   - If found:
     $$B(d) = A_m.\text{balance\_cents} - \sum_{d < t.\text{posted} \le A_m.\text{asof}} t.\text{cents}$$
   - Otherwise `None` (never extrapolate backward before $w_{\text{start}}$ or across an unimported gap!).
4. **Period Balance Summary Resolution for `[period.start, period.end]`:**
   - `open_date = period.start.pred_opt()`; `open_cents = open_date.and_then(|d| B(d))`.
   - Evaluate target date `period.end`:
     - If `period.start > today` → `state = "future"`, `end_cents = None`.
     - Else if $B(\text{period.end})$ is `Some(c)`:
       - If `period.end < today` (or `period.end == today && latest_anchor.asof >= period.end`) → `state = "verified"`, `end_cents = Some(c)`, `end_asof = Some(period.end)`.
       - Else (`period.end >= today`, open period whose future end isn't reached yet — e.g. `2026-Q4`, `2026`, `all_time`): look up latest available $B(d)$ at $d = \min(\text{period.end}, \text{latest\_anchor.asof})$ → `state = "so_far"`.
     - Else (`B(period.end)` is `None`):
       - Check latest anchor inside `[period.start, period.end]` (the **2026-W46 Monday-morning case**!): if `max_asof_in_period` exists with NO later gap inside `[period.start, max_asof]`, return `state = "as_of"` (when `period.end < today`) or `state = "so_far"` (when `period.start <= today <= period.end`), with `end_cents = B(max_asof)`, `end_asof = Some(max_asof)`.
       - Else if `period.start <= today <= period.end` (open week/period before first transaction this week, e.g., **`2026-W47` on Monday `2026-11-16`**) and a prior QFX anchor exists before `period.start`: return `state = "so_far"`, `end_cents = latest_anchor.balance_cents`, `end_asof = latest_anchor.asof`.
       - Else if a QFX window later than `period.end` exists with a missing hole at `period.end` → `state = "gap"`.
       - Else if `period.end < earliest_ofx_start` → `state = "untracked"`.
       - Else if account has CSV imports only → `state = "unverified"`.
       - Else → `state = "awaiting_import"`.
   - `delta_cents = open_cents.zip(end_cents).map(|(o, e)| e - o)` (note: omit or flag `coverage_gap: true` if an internal OFX gap sits strictly between `open_date` and `end_asof`).
   - `min_cents` / `max_cents`: min and max of $B(d)$ across all covered days $d \in [\text{period.start}, \text{end\_asof}]$.

---

### 4.3 Additive JSON & Terminal CLI Contract (`bob bank report`)

Keeping `schema_version: 1` (purely additive fields so existing `bob-plugins` decoders stay compatible):

#### JSON additions on `bob bank report [-p PERIOD] [-w WEEK] ... -f json`

```json
{
  "balances": [
    {
      "alias": "checking",
      "label": "WF Checking",
      "kind": "checking",
      "default": true,
      "state": "as_of",
      "open_date": "2026-11-08",
      "open_cents": 896031,
      "end_asof": "2026-11-13",
      "end_cents": 776004,
      "delta_cents": -120027,
      "min_cents": 776004,
      "max_cents": 834476,
      "coverage_start": "2026-05-01",
      "coverage_through": "2026-11-13",
      "last_import": "2026-11-16",
      "status": "balanced",
      "ledger_delta_cents": 0,
      "has_internal_gap": false,
      "target": { "path": "bank/2026-11.md", "line": 26, "date": "2026-11-13" }
    }
  ]
}
```

When `-c` is also passed (`week`, `quarter`, `iso_year`, `all_time`), `charts` gains an aligned `balances[]` array matching `charts.buckets[]` by index and `id`:

```json
{
  "charts": {
    "balances": [
      {
        "alias": "checking",
        "buckets": [
          { "id": "2026-11-09", "end_cents": 834476, "as_of": "2026-11-09", "state": "verified" },
          { "id": "2026-11-10", "end_cents": 822974, "as_of": "2026-11-10", "state": "verified" },
          { "id": "2026-11-11", "end_cents": 822974, "as_of": "2026-11-11", "state": "verified" },
          { "id": "2026-11-12", "end_cents": 797997, "as_of": "2026-11-12", "state": "verified" },
          { "id": "2026-11-13", "end_cents": 776004, "as_of": "2026-11-13", "state": "verified" },
          { "id": "2026-11-14", "end_cents": null,   "as_of": null,         "state": "awaiting_import" },
          { "id": "2026-11-15", "end_cents": null,   "as_of": null,         "state": "awaiting_import" }
        ]
      }
    ]
  }
}
```

#### Human Terminal Output (`src/native/bank/output.rs`)
- In `print_report`, below the `Out · In · Net` summary line (for non-day periods where a balance exists):
  ```text
  WF Checking  $7,760.04 (as of Nov 13)  Δ -$1,200.27 (-13.4%)  Nov 8 $8,960.31 → Nov 13 $7,760.04
  ```
- In `print_bucket_table` (`-c`), add a right-aligned `Balance` column when a primary checking balance series is present (`$8,344.76`, ..., `$7,760.04`, `–`).

#### Configuration (`~/.config/bob/config.yml`)
- `stats.bank_balance`: `boolean`, defaults to `true` (controls the period-note Balance Band independently of `stats.bank_period` charts and `stats.bank_badge`).
- `stats.bank_balance_accounts`: optional list of account aliases (or `"checking"` / `"all"`, default `"checking"` = all accounts with `kind: checking`).

---

## 5. Implementation & Rollout Plan

1. **`bob-cli` (Rust):**
   - `src/native/bank/journal.rs` & `import_plan.rs`: Add additive `"source": "ofx" | "csv"` to new `bank.txn` journal entries (backwards-compatible reader fallback for existing events).
   - `src/native/bank/balance.rs` (new): Component partitioning, daily prefix sums, backward reconstruction $B(d)$, period summary resolution, bucket balance series, and settled-anchor cross-check.
   - `src/native/bank/check.rs`: Surface `bank_balance_anchor_mismatch` warning if two settled anchors inside a contiguous component disagree.
   - `src/native/bank/report.rs`, `charts.rs`, `output.rs`: Populate `balances[]`, `charts.balances[]`, and terminal `Balance` summary/column.
   - `docs/bank.md`, `docs/periods.md`, `docs/reference/json-outputs.md`: Document `balances[]`, `charts.balances[]`, and `stats.bank_balance`.
2. **`bob-plugins` (`bob-ledger-tools`):**
   - `241h-plugin-bank-decode.js` & `241ha-plugin-bank-charts-decode.js`: Strictly decode optional `balances[]` and `charts.balances[]` (missing keys stay absent so older `bob` binaries never fail decoding).
   - `241nc-plugin-bank-period-model.js` & `241nd-plugin-bank-period-paint.js` (plus `241ne-plugin-bank-period-hosts.js`):
     - Allow `.bob-bank-period` to render the Balance Band even when `in_cents == 0 && out_cents == 0 && waiting == 0` or `BANK CHARTS` is collapsed.
     - Paint `.bob-bank-balance` hero numeral, delta, temporal status (`on <date>` / `as of <date>`), SVG sparkline, hover/keyboard sync with `IN / OUT`, and accessible `<table>` twin.
   - `styles.css`: Add `.bob-bank-balance*` styles with forced-colors and `@media (prefers-reduced-motion)` support, then `npm run build && npm test && bob plugins sync`.
3. **Vault Cleanup (Optional / User Decision):**
   - Once verified across `2026-W45`, `2026-W46`, `2026-Q3`, `2026-Q4`, and `2026`, cancel the manual `Update [[cash#^balance]]` chore in `~/bob/recur.md` (and keep `cash#^balance` as historical pre-2026 archive).

### Verification Matrix
- **Unit tests (Rust):** Exact penny agreement across multi-anchor QFX components; `before_start` reconstruction; mid-day same-day anchor superseding; gap isolation (no extrapolation across unimported gaps); CSV+OFX overlap guard; weekend `DTASOF < period.end` (`as_of`) auto-promoting to `verified` once a later import spans `period.end`.
- **Unit/DOM tests (`bob-plugins`):** Independent visibility when `in_cents == 0 && out_cents == 0` (`2026-W45`), persistence when `BANK CHARTS` collapsed, daily-note exclusion, older-`bob` graceful omission, SVG sparkline flat-range & dashed-tail rendering, hover readout sync.
- **Live vault check:** Verify `bob bank report -p 2026-W45 -s -c`, `2026-W46`, `2026-Q3`, `2026-Q4`, `2026`, and `all_time` against the real `.bob/bank/kellys-macbook-pro-local.jsonl` ledger and inspect Obsidian desktop renders on `2026-W46.md` and `2026/20261115.md` (confirming nothing renders on the daily file).
