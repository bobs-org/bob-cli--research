# Wells Fargo checking balances in period notes: a trustworthy close, quietly presented

Independent research by **cdx**, 2026-11-16. Scope: design and implementation guidance, not implementation.

**Recommendation: add a small closing-balance summary to the existing bank area of each non-daily period note.** Compute it in bob from imported bank evidence for that period's actual ending date, and render it live through bob-ledger-tools. Keep the amount, account name, date, and evidence state together. Do not insert periodically updated dollar amounts into note Markdown or substitute the newest imported account balance for an old period's close.

This is a good feature for financial reflection. It supplies a useful stock of money alongside the existing flows of money. Its value depends much more on the meaning of the number than on another chart. I would make one reliable, attractive number the first release.

I researched bob-cli at `0510aaf0e997ca97c10919ec21214b362a1b8c12` and bob-plugins at `91e909791a86fa30bba0b8b11c712e03a80e4dd4`, plus Wells Fargo's account-activity documentation and the official OFX specification. I did not read any other swarm research, inspect Bryan's actual financial records, or change the vault or application code. All dollar amounts below are invented examples.

**The requirement needs a more precise definition.** “Total balance” should mean the checking account's **posted ledger balance at the end of the period**, reconstructed from the best imported evidence currently available. It should not mean available-to-spend money, the period's net income, all accounts combined, or what Bob happened to know on that date.

Wells Fargo distinguishes its posted balance from available funds: the latter adjusts for holds and pending transactions. Its FAQ describes posted balance in relation to the previous business day's posting, and explains that business-day cutoffs affect deposits. Consequently a Sunday period close is a legitimate historical posted-balance question, even though weekend spending may still be pending. We should use the bank's posting-date semantics, not invent a Sunday transaction or adjust the balance for pending purchases. [Wells Fargo: Account Activity Questions](https://www.wellsfargo.com/help/online-banking/activity-faqs/)

Here are my explicit adjustments to the request:

| Requirement | Recommended interpretation or adjustment |
| --- | --- |
| “Total balance” | One named account's USD posted ledger balance. Label it “Closing balance,” with “Posted balance” explained in details. |
| “At the end” | Use the canonical period end from Bob's calendar. The example is Sunday, 2026-11-15, for 2026-W46. |
| “In the corresponding note” | Visible in the note's live bank summary. The underlying evidence remains durable in the bank journal; dollar amounts are not written into the note. |
| Current periods | Show “Posted balance · as of <actual date>”; never call an unfinished week's value its closing balance. |
| Future periods | No balance display or bank fetch for this feature. |
| All time | Show the latest supported posted balance with its date. There is no final all-time close, and balances must never be summed across periods. |
| Insufficient evidence | Show “Closing balance unavailable” with a specific next action; never silently substitute a last-known value or zero. |
| Historical revisions | Allow later bank evidence to correct a historical value, retaining provenance. This answers the best-known historical balance, not an immutable record of the website as it looked then. |
| Initial scope | Weeks, Bob quarters, and ISO week-years, plus the qualified all-time view. No daily balance UI, new monthly period notes, feeds, budgets, net-worth dashboard, or balance trend chart in v1. |

The live-rendering interpretation deserves explicit acceptance during implementation planning: a plain Markdown editor will not show the number. That follows the existing period-note contract and avoids a second copy of the financial truth. If portable Markdown/PDF snapshots are essential, make an explicit export a subsequent feature, with its evidence date attached.

**The existing system already supplies much of the foundation.**

The current bank importer accepts QFX/OFX and a specific Wells Fargo CSV shape. QFX contributes ledger-balance observations and transaction windows; CSV contributes transactions but no balance anchor. Per-host `.bob/bank/<host>.jsonl` journals preserve import observations, signed integer cents, source hashes, bank transaction identities after hashing, and bank posting dates. Repeated imports are deduplicated; conflicting transaction evidence is recorded as a problem. Bank-note rows are the editable acknowledgement and categorization surface. [R1, R2]

Period reports already resolve the requested dates, and the plugin already attaches a Bank Badge and Bank Period Charts after `bob-stats-strip`. The charts use `bob bank report -p <id> -s -c -f json`. A new query layer, vault-wide scan, nightly writer, or new note fence is unnecessary. Existing period notes gain the display through the plugin update. [R3, R5]

There are several traps in reusing today's code:

- `accounts[].balance_cents` and `balance_asof` are **current account evidence**, even inside a historical period report. `status::latest_balance` selects the latest bank observation; it does not resolve the requested period's end. Reusing this field directly would make every old week show a later balance. [R2, R4]
- `coverage.complete` is a coarse report-coverage summary. Its current implementation compares tracked start and latest import end; it does not prove an unbroken, account-specific reconstruction interval. It cannot certify a closing balance. [R4]
- Existing account status is evaluated against today. A historical close does not become invalid just because no new QFX has been imported for a month. Separate historical evidence sufficiency from current import freshness. [R2]
- Existing cashflow totals exclude transfers and handle unclassified inflows separately. Those totals cannot be used to reconstruct checking balances. Checking transfers, ATM withdrawals, fees, refunds, and every other posted movement affect the account regardless of category or acknowledgement. [R4]
- Both badge and chart visibility currently depend on money movement or waiting rows. A balance is meaningful even when no money moved, and a real zero balance is meaningful too. Its visibility must have its own condition. [R5]
- Bob's “quarters” are groups of ISO weeks. The 2026 ISO year and Q4 end on **2027-01-03**, not December 31. Reuse the calendar resolver and print the actual end date. [R3]

**The main research finding is that closing-date precision needs work before the UI can promise an exact close.**

OFX has separate transaction-window dates and a balance timestamp. The specification defines response `DTEND` as exclusive, and permits timestamps with offsets. Bank-statement downloads provide the current ledger balance and its own date. It also describes late-added transactions and explicit replacement/deletion corrections. These are distinct concepts; selecting an export date range does not by itself establish that its ledger balance belongs to that range's end. [OFX Banking 2.3, §§3.2.7–3.2.8, 11.4.2, 11.4.4.1](https://financialdataexchange.org/wp-content/uploads/2025/12/OFX-Banking-Specification-v2.3.pdf)

Bob currently reduces OFX dates to their first eight date digits, stores `balance_asof` as `NaiveDate`, and unions date windows inclusively. No explicit correction-tag handling was found in the inspected source parser. These are concrete limitations of the evidence available to a new resolver; they are not proof that Bryan's existing imports or amounts are wrong. [R2]

For example, an export that stops at Monday 00:00 cannot establish all of Monday's postings. Two balances observed on the same date may also represent different times. Picking the last-imported amount and calling it that day's closing balance would discard the distinction we need.

I would make a small, focused import-evidence improvement a prerequisite:

1. Preserve the original precision and normalized meaning of balance and coverage timestamps, including offsets when present. Keep existing bank posting calendar dates intact; do not shift transactions to the importing machine's timezone.
2. Normalize coverage endpoints once in the Rust bank domain, recording whether an endpoint is exclusive and which complete posting days it supports.
3. Establish the actual Wells Fargo QFX behavior with sanitized, paired exports and a bank-displayed closing balance. Test an ordinary weekday, a weekend boundary, and two exports on the same day. An explicit bank-specific rule should be supported by those fixtures, not inferred from a label containing “WF.”
4. Keep old date-only evidence readable, but mark its precision honestly. Reimport can append richer evidence for an existing file without rewriting old events or multiplying transactions. Include evidence-format/profile revision in the deduplication decision so identical file bytes can enrich a legacy import.
5. Detect unsupported correction records and refuse an exact reconstructed result based on them; ideally reject such an import before installing it until replacement/deletion handling exists. Silent ordinary-transaction treatment is unsafe.

This is bounded work, not a request for a general banking platform. The useful fallback is a clearly dated bank observation while precise reconstruction remains unavailable. Legacy records must never be silently promoted to stronger evidence merely because the new code understands a more precise format.

The remaining uncertainty is specific: I have not examined a real Wells Fargo export from Bryan, so I cannot establish its exact intraday/end-of-day conventions or promise that the existing journal alone can answer November 15. That is the first implementation validation, not a reason to fabricate a number now.

**The core model should be a pure historical balance resolver.**

Add a Rust bank-domain function conceptually equivalent to:

`balance_at(account, target_posting_day, bank_evidence) -> BalanceResult`

Its inputs are account identity, normalized observations, covered intervals, deduplicated bank transactions, and evidence integrity findings. Its output distinguishes requested date, resolved date, amount, basis, confidence, and problems. Frontend code formats the result; it never adds transactions or selects anchors.

For **validated whole-day anchors**, the arithmetic is:

```text
Earlier anchor A:
  close(D) = balance(A) + sum(posted movements on dates A < date <= D)

Later anchor A:
  close(D) = balance(A) - sum(posted movements on dates D < date <= A)
```

The second direction is important: the normal Monday import should be able to explain the preceding Sunday's close. Both formulas require complete evidence for their adjustment interval and an anchor whose timing agrees with that interval. They must not be applied to an arbitrary intraday observation by truncating its timestamp.

An invented example: a validated November 18 close is $13,045.67. Posted movements after November 15 through that anchor are +$1,000.00 and −$300.00. November 15's reconstructed close is $12,345.67. A $90 pending card authorization is outside this ledger-balance calculation.

Recommended resolution rules:

- Prefer a direct observation proven to represent the requested day's close. Otherwise use a nearby eligible anchor with continuous coverage through the target. Prefer the shortest sufficient interval; use a stable ordering for equivalent evidence.
- When other eligible anchors provide an independent check, reconcile the predicted values in exact cents. A disagreement yields `conflict`, not an average or whichever import arrived last.
- A single anchor plus a complete interval supports “Reconstructed.” Do not call this independently verified just because deriving an opening balance from the same anchor reproduces that anchor.
- Require coverage only for the interval actually needed to establish the close. A reliable November 15 anchor can establish the W46 close even if tracking began on November 12 and the week's spending summary is incomplete.
- Initially respect the configured account start as the supported-history boundary. Permit a period whose start predates tracking when its end is supported. Do not automatically expand tracking or create old bank rows as a side effect.
- Use deduplicated **bank transaction evidence** for balance arithmetic. Categories, labels, waiting checkboxes, hand-entered unmatched rows, and deletion of a presentation row must not rewrite what the bank reported. Surface note/journal discrepancies separately; a missing note row is a ledger-maintenance problem, not evidence that the bank's balance changed.
- Treat unreadable or malformed evidence as a loss of confidence. Scope contradictions to the relevant account/interval when safely attributable; uncertainty about missing evidence must not become an empty successful history.
- Never infer a zero-movement interval from the absence of transactions. An empty exported interval can supply evidence; an interval never imported cannot.
- Revalidate later imports against affected historical intervals. Overlapping downloads and reconciliation help find late postings, but no imported window promises that the bank can never correct history.

Keep two different dimensions in the result: **how the bank amount was established**, and **whether the editable bank ledger agrees**. Otherwise a typo in a payee's row could erase a perfectly good directly reported closing balance, or a “balanced” current account could falsely certify a poorly covered historical week.

Use checked integer-cent arithmetic. Include all signed movements on the selected checking account exactly once. Do not use cashflow net, floats, absolute values, or sums of child-period closing balances.

**The visual design should be quiet and precise.**

Place the new summary inside the existing bank region below the Stats Strip, adjacent to the current In/Out badge and above the charts. Keep it outside the charts' collapsible body. The typography should make the amount easy to find without competing with the period title or turning the note into a dashboard.

A closed week could read as follows. This is a layout sketch, not a screenshot of existing functionality:

```text
Wells Fargo checking                         $12,345.67
Closing balance · Sun Nov 15, 2026            Reconstructed  ⓘ

[ existing In / Out summary and bank charts ]
```

The exact relative position of the existing badge can remain unchanged in the first implementation: adding the balance between that badge and the chart header preserves today's navigation and styling. Visually group these elements with spacing rather than introducing another large bordered card.

- Account label in secondary text; amount in normal high-contrast text, semibold, with tabular numerals and **exact cents at every period size**. Do not abbreviate $12,345.67 to $12k.
- Date and meaning are always visible. The amount's evidence state is short text, not a color-only dot. Use neutral color for positive balances and a signed amount for overdrafts; do not equate more checking money with personal success.
- One compact row on wide panes, two rows on narrow panes, matching the existing strip's spacing, radius, and theme variables. Preserve readable wrapping at 200% zoom.
- Information activation by click, Enter, or Space opens a small detail disclosure. It explains “Posted balance; pending transactions excluded,” the target date, anchor date, import date, calculation basis, and any relevant discrepancy. Include a read-only “Open bank” action.
- Use the configured account display label, optionally expanded to “Wells Fargo checking.” Do not show account-number tails, source-file paths, raw bank identifiers, or cryptographic hashes in routine UI.
- The balance remains visible when charts are collapsed or empty, when all rows are acknowledged, and when its amount is exactly $0.00.
- No sparkline in v1. It adds historical reconstruction, gap encoding, scale choices, and possible confusion with the existing cashflow charts before the main question has been answered.

The primary states should have deliberate copy:

| State | Visible treatment |
| --- | --- |
| Direct supported close | Amount, “Closing balance · <end>,” and “Bank reported.” |
| Reconstructed close | Amount, same closing date, and “Reconstructed”; disclose the anchor and adjustment. An independent match can be noted in details. |
| Closed period, missing interval | “Closing balance unavailable · <end>”; “Import activity covering <missing range>.” No large fallback amount. |
| Only an older bank observation | Same unavailable close; optional secondary “Last reported $… on <date>,” always earlier than or equal to the target and clearly separated. |
| Conflicting evidence | “Closing balance needs review”; show the conflicting dates and reconciliation difference in details, with an actionable bank-check link. |
| Current period | “Posted balance · as of <supported date>”; any stale-import message refers to current freshness. Never display a future closing date beside a current amount. |
| All time | “Latest posted balance · as of <date>.” |
| No balance anchor / CSV-only | “No bank balance imported”; explain that a QFX import supplies the anchor. |
| No configured bank or explicitly disabled | Hide without empty space. A configured account with missing data gets an explanation rather than disappearing. |
| Refresh failure with a cached value | Keep the last result only for the same account and period, visibly marked “Could not refresh”; never present cached data as freshly checked. |

For a closed period the main number is either its supported close or absent. There is no “close, approximately as of a different date” hybrid. This makes the feature intuitive even when the bank data is awkward.

No daily note, daily strip, parts-table row, embed, or hover popover should gain a balance from a generic badge change. For v1, retain the existing desktop-only bank-period host support. Mobile needs a separate plan for obtaining Bob's report; acknowledge that limitation rather than silently treating a cached desktop number as current.

**The implementation can stay close to today's architecture.**

Pin the intended account explicitly by a small vault-level setting such as `bank.period_balance_account: checking`. This is a proposed new key, not a current command/config contract. Do not derive the historical account from map ordering, “the first checking account,” or a label substring. The engine can return account-scoped results while the first UI presents only the selected account.

Extend `bob bank report` with an additive, versioned `balances` object, available independently of chart generation. Preserve the meaning of existing `accounts`, `totals`, and `coverage`. A sketch of the useful shape is:

```json
{
  "balances": {
    "version": 1,
    "selected_account": "checking",
    "requested_end": "2026-11-15",
    "period_state": "closed",
    "accounts": [
      {
        "account": "checking",
        "currency": "USD",
        "amount_cents": 1234567,
        "effective_date": "2026-11-15",
        "status": "reconstructed",
        "basis": "posted_ledger",
        "anchor_date": "2026-11-18",
        "independently_reconciled": false,
        "issues": []
      }
    ]
  }
}
```

This example assumes validated complete-day evidence. The final contract also needs structured coverage gaps, source precision, evidence references/fingerprint, and import timestamps. Those belong in the report/domain model, not in the headline display. Unknown amounts use JSON null, never 0. The engine's `status` should not be overloaded with cache freshness.

Reuse the existing period host and `-s -c` request when charts are enabled. Decode `balances` independently of `charts`, so a missing or undecodable chart does not remove a valid balance. Change the panel's money-empty rule to allow a balance-only summary; chart collapse affects charts only. Continue to honor `stats.bank_period` for the whole period bank section, and document that behavior. The account-selection setting supplies intentional scope without adding several new toggles.

Older Bob reports without `balances` should keep their existing charts and omit the new line. Rust computes date ranges and money; JavaScript validates safe integers and renders. The existing plugin bank service already revalidates on focus, file-open, and visibility because hidden journal changes are not reliably delivered as vault events. Test this specifically for **balance-only imports with no new bank rows** and ensure there is an accessible refresh path. [R5]

Keep source observations durable in the journal and rederive period values. A cache is disposable and must include account, period, evidence revision, and resolver version in its validity criteria. No new nightly job is necessary. No automatic retrospective writes to period reviews or reflections are appropriate.

Because the source files are transient and the existing workflow can delete downloaded QFX after import, retain enough normalized evidence to explain the result later. Raw bank exports need not be copied into a period note or research artifact. Evidence hashes and immutable journal records can provide provenance; the details UI can present their human meaning without exposing internal machinery.

**Alternatives have meaningful tradeoffs.**

| Approach | Benefit | Why I would or would not choose it |
| --- | --- | --- |
| Reuse latest `accounts[].balance_cents` | Very small UI change | Reject for historical closes; it answers a different date. |
| Store a manual amount in each period note | Simple, visible in plain Markdown | Reasonable one-off workaround, but repeated entry and corrections create competing truths. Not the default design. |
| Automatically write a balance field nightly | Produces standalone note text | Adds a writer, sync conflicts, ownership rules, and late-import repair. Conflicts with today's live-number period design. |
| Sum bank rows from an assumed zero opening balance | Easy arithmetic | Reject: missing anchor, transfers/category semantics, mutable rows, and incomplete history make it wrong. |
| New financial-service connection | Could reduce import effort | Adds authentication and operating complexity to an already supported import workflow. Not needed for this request. |
| Live close from journal evidence | Fits current notes, backfills when evidence arrives, no note rewrites | Recommended, provided date precision, coverage, and failure states are explicit. |
| Balance trend and change since last close | Useful later context | Defer until point values are trusted. A change in checking balance includes transfers and is not “savings” or the existing net-income metric. |

A checking balance is also an incomplete measure of financial health: payroll timing, transfers to savings, and credit-card payment timing can move it without any comparable change in wealth. That is a reason to keep the display descriptive and neutral, not a reason to reject it. The existing cashflow views already offer complementary context. I would not broaden this request into net worth or make money a new productivity score.

**Acceptance should focus on whether the displayed claim is true.**

The following cases are worth testing before shipment:

1. The exact example: W46 resolves to November 9–15 and displays the November 15 close in `2026/2026-W46.md`, while a daily note has no balance UI.
2. A later validated anchor reconstructs the Sunday close, including transfers and unclassified credits, with pending activity excluded.
3. A direct supported close remains usable when the beginning of the period is outside tracked history; the separate cashflow summary still reports its partial coverage.
4. An unimported no-transaction interval produces unavailable, while a covered empty interval can carry a balance forward.
5. Date-only legacy evidence, exclusive midnight `DTEND`, non-midnight timestamps, different offsets, and two observations on the same date never receive unjustified closing-day precision.
6. Repeated/overlapping exports and two-host replay do not multiply movements. Conflicting anchors and corrected transactions cannot be resolved by import-order accident.
7. A zero balance is visible; negative balances preserve their sign; overflow and unsupported currency fail explicitly.
8. Categorizing, acknowledging, renaming, or deleting a presentation row does not change the bank-evidence amount. Relevant note discrepancies remain inspectable.
9. A historically established close does not age into “stale” when today advances. New contradictory evidence does invalidate or revise it with provenance.
10. Week/quarter/year boundaries include the 2026 W53 case; current and all-time views show actual as-of dates; future notes do not fetch a closing balance.
11. A balance-only import refreshes a visible note even when no bank Markdown row changed. Failed refreshes, old CLI payloads, malformed JSON, and wrong-period cached responses are handled separately.
12. The summary survives empty/collapsed charts; keyboard and screen-reader users can inspect all evidence; light/dark themes, narrow panes, long account labels, and large amounts remain readable.
13. Reading the note/report writes no vault file. Updating the plugin adds the balance to existing periods without scaffold migration.

I checked the calendar example and illustrative arithmetic with a small Python calculation. This report does not claim an implemented resolver, passing application tests, or validation against a real account.

Implementation should proceed in three reviewable pieces: first validate and preserve source evidence; then add the pure resolver and versioned report result with the financial edge cases above; finally add the compact plugin presentation and visual/interaction fixtures. Avoid estimating this as a one-field UI change. The UI is small; the date and evidence semantics are the substantive work.

The local evidence map below makes the research reproducible without depending on this ephemeral workspace path. Paths are relative to the named repository at the revisions recorded above:

| Ref | Source locations and observed facts |
| --- | --- |
| R1 | bob-cli: `docs/bank.md`, especially Sources, Journal, Account status, Bank Badge, Bank period charts; `docs/guides/acknowledge-bank-transactions.md` for the current QFX workflow. |
| R2 | bob-cli: `src/native/bank/source.rs` (`parse_ofx`, `parse_ledger_balance`, `parse_ofx_date`, account resolution); `journal.rs` (`ImportEvent`, `TxnEvent`, `JournalSnapshot`); `status.rs` (`proof_for`, `latest_balance`, `coverage_gap`). |
| R3 | bob-cli: `docs/periods.md`, Calendar and identity / Note anatomy and ownership; `src/native/periods/calendar.rs` and `scaffold.rs` identify the existing calendar/scaffold integration points. The documented ownership contract says rendered numbers are not written to Markdown. |
| R4 | bob-cli: `src/native/bank/cli.rs` report path passes current account statuses to `report::build`; `report.rs` (`BankReport`, `coverage_for`, `build`); `model.rs` (`compute_totals`) documents cashflow exclusions. |
| R5 | bob-plugins: `plugins/bob-ledger-tools/src/241nb-plugin-bank-badge-hosts.js`, `241nc-plugin-bank-period-model.js`, `241ne-plugin-bank-period-hosts.js`, and `241j-plugin-bank-data.js`. These establish sibling hosts, zero-activity hiding, period gating, cache/fetch separation, and hidden-journal revalidation. Existing `scripts/test-ledger-tools-bank-period-*.cjs` and `scripts/preview-bank-period.cjs` are suitable validation surfaces. |

**Recommended solution:** implement one live, exact-cent **Wells Fargo checking closing balance** in the existing non-daily period bank section, with the period's real ending date and a plain-language evidence state. Build it on a Rust historical resolver over the import journal, with source-time normalization and account-specific coverage. Let the regular QFX workflow populate past closes when sufficient evidence arrives; show an honest unavailable state when it cannot. Ship the compact summary first, keep it visible in quiet weeks, and defer charts, snapshots, and broader financial metrics until this number has earned trust.
