# Bank as a daily acknowledgment album

Independent research by **cdx**, 2026-11-11. Scope: deciding what to build after `bob-cli-k3`, not implementing it or changing the live vault. No other report, conversation, or findings from this research swarm were consulted. All financial examples below are invented.

**Recommendation:** build a modest `bank` album under `cash`, centered on a short daily acknowledgment session. Use one record per account transaction, exact monetary values, stable identity, and an explicit distinction between **recorded**, **acknowledged**, and **reconciled**. Start with current activity and one real export format; add bank connectivity only if the habit survives a trial and acquisition is the bottleneck. An ordinary album schema is enough for a prototype, but not enough for trustworthy importing or financial totals.

The strongest alternative is Actual Budget with a Bob reminder and links. Choose that instead if the real goal expands to comprehensive budgeting, debt management, or maintaining many connected accounts. Do not build two independently editable transaction ledgers.

## What the local evidence says

I inspected the current epic through `sase bead read bob-cli-k3`, its approved plan through `sase artifact read plan:202611/album_and_record_notes.md`, the bob-cli checkout at `ba3f51bad3bd491d66e739a895ce4de99149329f`, and an audited checkout of the Bob vault at `52b647aea37116e874c4838110f016ddafb21a88`. The vault checkout is a repository snapshot, not proof of the latest unsynced bytes in `~/bob`. Implementation must recheck the live state.

The request has a clear lineage:

- `bob.md ^bank-records` says to use records to track bank transactions again, and links its start to `^record-h2-sections`.
- `cash.md ^daily-bank-records-again` asks to go through bank records every day again and links to that Bob task. This is principally a review habit, not a request for another budgeting system.
- `cash.md` is already an area and already links to `[[bank]]`. Neither `bank.md` nor `bank/` exists in the inspected snapshot. The proposed name therefore fits an existing navigation intention; check for a collision again before creation.
- A narrowly scoped scan of `2024`, `2025`, and `2026` immediate `*_habit.md` files found **494 exact `## @BANK` sections**, from 2024-04-10 through 2025-12-27. They contain 2,996 nonempty lines, including 487 lines labeled `total:` and 603 lines containing `[[eat` links. These are section/line counts, **not a verified transaction count or complete inventory of historical banking data**. Some sections contain only a total. The sample includes merchant links, recurring-expense references, shorthand descriptions, and daily aggregates.

That history matters: a successful successor should preserve the feeling of deliberately looking at money, the ability to connect purchases to places, and a meaningful completion state on days with no new activity. It should remove the need to maintain handwritten totals. It should not assume that the old entries are a bank-grade ledger.

Local evidence: [origin task](https://github.com/bobs-org/bob/blob/52b647aea37116e874c4838110f016ddafb21a88/bob.md#L26), [cash area and habit task](https://github.com/bobs-org/bob/blob/52b647aea37116e874c4838110f016ddafb21a88/cash.md#L80), and `bead:bob-cli-k3` / `plan:202611/album_and_record_notes.md`.

At inspection, the epic remained **in progress**. Phases 1–3 were closed; record routing, indexes, owner catalogs, clients, cutover, ledger mining, and wrap-up remained in progress. Treat its approved end state as a dependency, not as shipped capability.

## Is the idea good?

Yes, provided acknowledgment is the product and bookkeeping serves it. A transaction is a reasonable durable record: it has identity, dates, an amount, a counterparty, and sometimes a useful story. Bob adds a benefit an ordinary bank list lacks: a payment can link to a restaurant, project, purchase decision, or follow-up task in the surrounding vault.

The behavioral evidence supports monitoring in general, with limits. Harkin and colleagues' meta-analysis covered 138 randomized studies and 19,951 participants; progress-monitoring interventions improved goal attainment on average, with an effect size of about 0.40. This does **not** establish that daily bank review beats weekly review, that retyping transactions is necessary, or that an album will improve Bryan's finances. It supports testing a lightweight, deliberate review loop. [Harkin et al., 2016](https://pubmed.ncbi.nlm.nih.gov/26479070/)

The CFPB's spending-tracker guidance also separates collecting information from reflecting on surprising expenses and unused services, and suggests a trial lasting at least two weeks or a month. My design inference is to pair daily recognition with a brief weekly reflection; accumulating rows alone is an incomplete feedback loop. [CFPB spending-tracker guidance](https://www.consumerfinance.gov/archive/blog/track-your-spending-with-this-easy-tool/)

The main objections are practical:

1. **Manual transcription can displace attention.** A polished form with twelve required inputs may make the habit harder than opening the bank website. Automate trustworthy facts; reserve human effort for recognition and interpretation.
2. **“Every bank transaction” may not reveal spending.** A checking-account payment to a credit card does not explain the purchases on that card. All relevant purchase accounts must be included before claiming comprehensive spending insight.
3. **A green screen can conceal missing data.** An empty queue after a failed import is different from a successful check with no new transactions.
4. **The album abstraction has costs at volume.** Restaurants recur as one entity; transactions create new records every day. The current folder scan and generated index need realistic scale testing.
5. **Perfection can make restarting expensive.** Requiring months of backfill, perfect categories, or a flawless daily streak would reproduce the burden that a restart should remove. The cause of the previous lapse is unknown; I would not infer it from the notes.

A useful product promise is: **“See and acknowledge every new transaction available from the accounts you track; know what remains uncertain.”** That is both more useful and more honest than “track all spending in real time.”

## Requirement adjustments I recommend

These are proposed changes to the request, not previously accepted requirements.

| Adjustment | Reason and consequence |
| --- | --- |
| Daily means a daily review opportunity, with acknowledgment when transactions become available. | Bank posting and aggregation can lag. Do not manufacture an overdue failure for a transaction Bob has not received. |
| Review posted transactions by default; keep pending activity separate. | Final amounts and identities can differ. A pending authorization is not final spending. |
| Include spending credit cards as well as checking accounts when claiming spending coverage. | Otherwise the album mainly sees card repayments and hides purchase detail. Account scope must be explicit. |
| Separate acknowledgment, categorization, and reconciliation. | “I saw this” must not silently mean “the category is correct” or “the account balances.” |
| Importing never acknowledges. | The motivation requires a human gesture. Rules may suggest a merchant or category, but cannot mark a row reviewed. |
| Categories and prose are optional during acknowledgment. | “Uncategorized” is useful information. Making classification mandatory increases friction. Financial kind must remain distinguishable from category. |
| Start at a chosen date, with no historical review debt. | Old data can be imported later into an explicitly historical state; it must not claim to have been acknowledged. |
| Keep the first release focused on awareness and accurate account activity. | No net-worth model, investment tax lots, budgeting envelopes, receipt OCR, or autonomous anomaly judgments. |
| Make completeness and freshness visible. | A stale or missing account must prevent an unqualified “all caught up” claim. |
| Add weekly reconciliation and reflection. | Daily acknowledgment catches recognition problems; weekly checks catch missing/duplicated data and turn observations into decisions. |

## Alternatives and acquisition choices

| Approach | Fit for this request | Main cost | Decision |
| --- | --- | --- | --- |
| Bank website plus a recurring Bob task | Excellent way to restart immediately; authoritative transaction display | No unified structured history or contextual links | Use while waiting for the album epic if desired; no setup is required by this report |
| Daily note or notebook with transaction bullets | Familiar to the old habit | Weak identity, awkward filtering, manual totals and duplicate handling | Keep as historical evidence, not the new canonical model |
| Generic album only | Good low-cost prototype for capture and browsing | Cannot enforce monetary arithmetic, deduplication, review revisions, or account coverage | Suitable for a short pilot with explicit limitations |
| Bank album plus a narrow Bob banking module | Best combination of Bob integration and a deliberate review experience | Requires a small domain model and careful import/review engineering | Recommended, with restricted initial scope |
| Actual Budget plus Bob links/reminder | Already offers financial-file import, reconciliation, transfers, and optional bank connections | A second application; a mirrored album adds synchronization design | Preferred if financial management becomes the primary goal |
| Plain-text accounting with hledger | Strong fit for someone who wants an accounting journal and reports | Posting rules and a separate accounting workflow | Credible alternative, but more accounting than this request requires |

Actual supports CSV, QIF, OFX, QFX, and CAMT imports. Its documentation recommends OFX/QFX where available because transaction identifiers help avoid duplicates; it also attempts matching by date, amount, and payee. Its reconciliation workflow compares records with the bank and exposes a balance difference. These are useful existing capabilities, not evidence that arbitrary imports are infallible. [Actual import documentation](https://actualbudget.org/docs/transactions/importing/), [Actual reconciliation](https://actualbudget.org/docs/accounts/reconciliation/)

hledger explicitly documents assumptions behind its incremental CSV import, including stable dates and same-date ordering. This illustrates why “just hash a CSV row” or “just skip everything before the latest date” is not a universal ingestion solution. [hledger import behavior](https://hledger.org/1.52/hledger.html)

For Bob, choose acquisition in this order:

1. **A short manual or pasted pilot.** Review the real bank display and enter only the facts needed to test the interaction. Do not confuse this incomplete prototype with an authoritative account ledger.
2. **One supported bank export.** Prefer OFX/QFX with stable IDs if Bryan's bank actually provides it; otherwise support its real CSV layout with an explicit date/sign/column profile. Preview the mapping and totals before saving. Do not promise every bank format in v1.
3. **Optional read-only connectivity.** Evaluate only after identifying the institution, country, and account coverage. SimpleFIN is a plausible North American candidate; it is not a verified match for Bryan's accounts. Its protocol exposes account-scoped transaction IDs, signed decimal-string amounts, pending state, and balance timestamps. [SimpleFIN v1 protocol](https://www.simplefin.org/protocol-v1.html)

At research time SimpleFIN Bridge advertises $1.50 plus tax monthly or $15 plus tax annually. Recheck pricing and real institution support before adoption. The small subscription cost is likely less important than connection reliability and token handling. [SimpleFIN Bridge](https://bridge.simplefin.org/)

Directly integrating Plaid is not my first choice for a personal restart. Its transaction API is useful evidence of the complexity a connector must handle: changes are additions, modifications, and removals, and a failed multi-page update may require restarting the pagination loop. The future adapter should stage a complete update before advancing its cursor. [Plaid Transactions API](https://plaid.com/docs/api/products/transactions/)

If Actual becomes the canonical system, keep it canonical: Bob may own acknowledgment metadata and contextual links keyed to Actual transaction IDs, but must not independently edit imported amounts or balances. An integration bridge itself is work; a simple reminder with a link may be the better solution.

## The daily experience

The album should open on the next useful action. A wall of YAML, a large chart, or a lifetime list is the wrong first screen.

Illustrative layout; amounts, merchants, counts, and timing are synthetic:

```text
Cash › Bank                                      Add · Import · All activity
A moment with your money.

Checking checked 09:10 · Card checked 09:11
6 new to acknowledge · 1 needs attention · 2 pending

REVIEW NEXT
Nov 10   North Street Café       Card          −$18.40
         Food & drink · linked place
         Recognize this transaction?

         [Acknowledge]   [Needs attention]   [Later]
         Optional note…                           Undo

THIS MONTH · USD · POSTED · TRACKED ACCOUNTS ONLY
Purchases $812.20    Refunds $34.00    Net spending $778.20
Income $2,500.00     Transfers excluded

Views: Needs review | Needs attention | All activity | By category
```

Use the existing `cash` area hue as a quiet accent. Right-align tabular amounts. Keep the sign and currency explicit. Use text plus shape/icons for status, not color alone; an expense should not automatically look like an error. On a narrow pane, place account and category below the merchant. Hide technical identifiers and import details behind an inspect action.

The review sequence is deliberately small:

1. Open Bank and check whether each included account has usable data.
2. Show the oldest available unacknowledged posted transaction. Show the bank's description beside a friendlier title when needed; never conceal unfamiliar source text behind an auto-cleaned merchant name.
3. **Acknowledge** records explicit recognition of the displayed financial facts. A suggested category can stay blank. Save first, then advance. A failed write leaves the row and focus in place.
4. **Needs attention** records that the row was seen but has an unresolved question. It remains in a separate visible queue. “Create follow-up” can explicitly create a task in `cash` linking back to this transaction; it never inserts a task into the record.
5. **Later** leaves the transaction unacknowledged and moves within this session. No silent completion, no automatic next-day postponement, and no hidden backlog reset.
6. End with either “All available transactions acknowledged” plus source timestamps, or a qualified message such as “Available queue clear; Card could not be checked.”

Provide keyboard navigation, labeled actions, a visible undo, and a focus treatment that remains clear in light and dark themes. Opening a record, scrolling past it, or editing its category must not count as acknowledgment. Bulk acknowledgment should require an explicit selection of visible rows; exclude a one-click “approve everything unseen” default.

A successful check with zero new transactions records a **review-session event**, not a fake $0 transaction. The session can say which accounts were checked and when. If one account failed, that failure stays visible. A returning user sees the outstanding queue and can resume without a guilt-inducing broken streak.

The weekly experience adds two questions: “Does this match the account evidence?” and “What surprised me?” Link an intentional follow-up to `cash` only when there is something to do. Avoid mandatory daily essays or a useful/useless verdict on every purchase.

YNAB provides a relevant interaction precedent: imported transactions can wait for explicit approval, while pending items have a separate section. Bob should preserve its own stricter requirement that acquisition alone never acknowledges a changed financial fact. [YNAB linked-account workflow](https://support.ynab.com/en_us/linked-accounts-in-ynab-B1991f2Cc?mobile-help=true), [YNAB pending transactions](https://support.ynab.com/en_us/pending-transactions-an-overview-Bk0WoOcA5)

## Data model: one transaction is one account movement

Use `bank.md` as the album, `parent: "[[cash]]"`, and `record.noun: bank_transaction`. Keep its records in **flat `bank/*.md`**, matching the current album membership contract. One purchase and its subsequent refund are separate records. A transfer between two tracked accounts has two account movements linked as one transfer. Neither side disappears merely to make totals work.

A record has three independent concerns:

| Concern | Meaning | Authority |
| --- | --- | --- |
| Financial facts | Account, signed amount, currency, posting date, bank description, pending/posted/void state | Bank/export evidence, or clearly labeled manual entry |
| Interpretation | Friendly title, optional category, contextual links, notes, transfer/refund relationship | Bryan; suggestions never overwrite his decision silently |
| Review | Whether Bryan acknowledged the current facts; questions that remain | Explicit user gestures bound to a facts revision |

Suggested frontmatter for an acknowledged example:

```yaml
---
parent: "[[bank]]"
type: "[[record]]"
title: "North Street Café · 10 Nov"
status: acknowledged
bank_id: "tx-7e4af54a-1fd8-4e36-b5af-9193b311aa29"
bank_account: "everyday-card"
bank_date: 2026-11-10
bank_amount: "-18.40"
bank_currency: "USD"
bank_posting: posted
bank_kind: expense
bank_category: "Food & drink"
bank_source: "file:card-export-v1"
bank_source_key: "opaque-account-scoped-source-key"
bank_ack_revision: "semantic-facts-hash"
bank_ack_at: "2026-11-11T09:12:00-05:00"
created: 2026-11-11T09:11:00-0500
---

# North Street Café · 10 Nov

## Notes

- Breakfast before the appointment.
```

The filename is `bank/tx-7e4af54a-1fd8-4e36-b5af-9193b311aa29.md`: stable and unrelated to mutable date, merchant, or amount. `bank_id` matches it. A display title can change without breaking inbound links. A full UUID is illustrative; the invariant is collision-resistant identity, not this particular encoding.

A **schema excerpt**, using only existing record field kinds, could be:

```yaml
parent: "[[cash]]"
type: "[[album]]"
summary: Acknowledge account activity and notice where money goes.
emoji: 🏦
index_by: bank_account
index_facets:
  - bank_date
  - bank_amount
  - bank_currency
record:
  noun: bank_transaction
  label: Transaction
  plural: transactions
  fields:
    status:
      required: true
      values:
        new: "○ To acknowledge"
        attention: "? Needs attention"
        acknowledged: "✓ Acknowledged"
        historical: "· Historical"
    bank_id:
      required: true
    bank_account:
      required: true
      suggest: true
    bank_date:
      values: date
    bank_amount:
      required: true
    bank_currency:
      required: true
    bank_posting:
      required: true
      values:
        posted: Posted
        pending: Pending
        void: Void
    bank_kind:
      required: true
      values:
        unclassified: Unclassified
        expense: Expense
        income: Income
        transfer: Transfer
        refund: Refund
        adjustment: Adjustment
    bank_category:
      suggest: true
```

This is an excerpt, not a complete ready-to-install schema: declare the source/review fields from the example and any optional relationship fields before use. There is intentionally **no default for `status`**; the existing schema forbids one. Bank commands supply `new` explicitly, or record acknowledgment only after the associated gesture. Ordinary capture remains available for prototype entry, but full bank semantics need the bank validator.

The generic schema leaves `bank_date` optional so a pending item can lack a posting date; the bank validator requires it for every posted record. This conditional rule is another reason the schema alone is insufficient.

Most names use `bank_` because Obsidian properties have shared storage shapes across record kinds. `status` remains a string choice so the album's existing actionable-group ordering works. The bank view must compute effective status from current facts; a stale serialized `acknowledged` value alone cannot prove that the current amount was seen. Audit/check repairs or reports a stale projection.

### Exact money, dates, and identity

**Store canonical amounts as decimal strings and parse them into exact, checked arithmetic in Bob.** For example, `"-18.40"` becomes −1840 minor units for USD. Do not use the generic `number` field as the financial authority: the inspected implementation uses `RecordScalar::Number(f64)` and parses with `parse::<f64>()`. This is reasonable for generic numeric properties, but it is the wrong arithmetic contract for reconciliation. [Current schema implementation](https://github.com/bobs-org/bob-cli/blob/ba3f51bad3bd491d66e739a895ce4de99149329f/src/native/records/schema.rs#L435)

A bank validator must check decimal syntax, the configured currency exponent, integral minor units, and overflow. Reject unsupported currency/precision rather than silently rounding. Account setup supplies currency; do not infer USD merely from a dollar sign. V1 can explicitly support one verified currency. Separate currencies in every total and defer exchange-rate reporting.

A consequence of using strings is that native Base numeric summaries are **not the authoritative financial totals**. The bank read model calculates exact totals and renders formatted strings. Bases remain excellent for sorting, filtering, inspection, and links. Do not add a formula that converts money to floating point and then call its result reconciled. Obsidian documents per-file rows, views, filters, and summaries; it does not give this application a banking correctness contract. [Bases introduction](https://help.obsidian.md/bases), [table summaries](https://help.obsidian.md/bases/views/table)

Normalize sign at the adapter boundary: money entering the modeled account is positive; money leaving is negative. For cards, represent debt balances as negative, so purchases decrease the balance and payments increase it. Verify this with real export fixtures. Sign conventions are not universal: Plaid's transaction amounts use positive for outflow, whereas SimpleFIN uses positive for inflow. [Plaid amount semantics](https://plaid.com/docs/api/products/transactions/), [SimpleFIN transaction schema](https://www.simplefin.org/protocol-v1.html)

Keep `created` as record creation time. `bank_date` is the source posting date used for default reports; preserve an optional purchase/authorization date separately. A late import must not look like a purchase made today. Preserve date-only source values as dates rather than passing them through UTC midnight conversions.

Provider IDs are aliases, not the record's identity. An external key includes provider/connection namespace, account identity, and transaction ID. Manual records get a Bob ID immediately; when a later import matches, attach the source alias to that same record after a safe match. A mutable merchant/date/amount hash cannot serve as durable transaction identity.

### Recognition survives only the facts actually recognized

Compute a revision over the material financial facts: account, amount, currency, source description, relevant dates, and posting state. Acknowledgment stores that revision and a timestamp. If those facts change, present the old/new difference and require acknowledgment again. Changes to a friendly title, annotation, or suggested category need not reopen recognition.

Store provider facts separately from any explicit user correction: a refresh may update source facts, but must preserve the correction and surface a conflict rather than silently overwrite it. Friendly titles, categories, and notes remain user-owned.

Keep a small recoverable audit history of source changes and review actions, with independent event IDs. The immutable evidence log and current record projection must have one documented relationship; a disposable local index may accelerate queries but is not a second authority. Manual frontmatter edits to financial facts must invalidate the effective acknowledgment on the next read, even if the old status text remains.

For the initial release, review posted activity only. Pending can be omitted or displayed separately without an acknowledgment obligation. If later supported, follow provider linkage when available and preserve one Bob identity across a pending-to-posted replacement. Never infer a guaranteed match from merchant and amount alone. Plaid documents that posting may replace the transaction ID, change the amount or name, or remove a hold entirely; posted records can also be modified. [Plaid transaction lifecycle](https://plaid.com/docs/transactions/transactions-data/)

## Importing and financial correctness

A dependable importer needs explicit rules even for one bank:

- **Stable ID first.** Reimporting the same external transaction updates its existing record or is a no-op. Reimporting identical file bytes is a no-op by file hash as well.
- **CSV without IDs is ambiguous.** Date, amount, and normalized description produce a candidate match, not proof. Two identical café purchases on the same day may both be real. Preserve multiplicity; show uncertain matches and permit “same transaction” or “both are real.” A whole-file hash does not solve overlap between different exports.
- **Preview before commit.** Show new, unchanged, changed, possible-duplicate, and rejected counts; account, currency, date interval, inflow/outflow totals, and representative parsed rows. Ambiguous dates or signs block that import profile.
- **No silent partial success.** Malformed rows block the batch by default. A future explicit “import valid rows” option must retain a visible incomplete-coverage state. Never drop rows unnoticed.
- **Write records and index together.** Stage the batch once, rebuild the album index once, check that inputs have not changed, then commit through Bob's guarded transaction machinery. A failure cannot advance the durable import checkpoint.
- **Deletion is evidence-sensitive.** Absence from a later date-filtered export is not deletion. An explicit provider removal creates a retained void/tombstone state and audit event, not a disappearing record or broken link.
- **Account relinking needs an explicit mapping.** A new connection ID must not create a second copy of the same account's history. Preserve old source aliases when migration is intentional.

Define the first report totals precisely:

- **Gross outflow/inflow:** signed account activity, including transfers, labeled as account movement.
- **Gross spending:** posted expense movements, including fees; exclude transfers, historical opening anchors, and adjustments.
- **Refunds:** separately displayed credits classified as refunds; link the original purchase when known.
- **Net spending:** gross spending less refunds in the displayed posting-date period. A later-month refund belongs to that later period; it does not rewrite the earlier month's bank history.
- **Income:** classified income, not every positive transaction.
- **Unclassified:** visible count and amount, with totals explicitly labeled incomplete until resolved.

For example, a $120 card purchase plus a $120 checking-to-card payment represents **$120 spending**, not $240. The two repayment legs are a transfer. A later $20 refund makes net spending $100 in a period containing both purchase and refund. Actual's explicit transfer relationship is a useful precedent for preventing double counting. [Actual transfers](https://actualbudget.org/docs/transactions/transfers/)

A withdrawal to cash is an account outflow. If cash purchases are not tracked, label it “cash withdrawn; destination spending unknown,” rather than pretending to know the purchase categories. Similarly, a payment to an untracked card is not evidence of its underlying purchases. Shared-account ownership, reimbursements, and split purchases need explicit policies before any “my personal spending” metric. V1 may use one optional category and defer splits; retain the source amount and free-form explanation.

Weekly reconciliation is per account and currency, against a particular statement or verified posted-balance cutoff:

```text
expected closing balance = verified opening balance + included posted movements
unexplained difference   = bank closing balance − expected closing balance
```

Do not compare a posted ledger with an available balance that includes holds. Do not display an authoritative current balance without an opening anchor and known coverage. Check row coverage as well as the balance: offsetting omissions can sum to zero. Never create an unexplained adjustment automatically to make the result green. A reconciliation snapshot records its cutoff, evidence, included facts revision, and remaining difference; a later correction makes it stale. Acknowledgment remains independent.

## Fit with the album epic, and the engineering boundary

Use the epic's native affordances: owner catalog, breadcrumb, record note, schema card, ordinary `[!records]` index, and `bank.base`. Keep banking behavior in bob-cli. Obsidian renders Bob's versioned read/review output; Mac Capture renders Bob's parsing and preview decisions. This follows `decisions:mac-capture-is-a-thin-client`.

The following gaps are verified in the inspected contract/code and need deliberate handling:

| Existing behavior | Consequence for Bank |
| --- | --- |
| Title-derived filenames; collisions refused | Repeated merchants need generated stable IDs, not hand-chosen unique titles. |
| Catalog indexes only immediate Markdown files | Do not introduce `bank/2026/11/` partitioning without changing the album contract. |
| `number` uses `f64` | Exact bank arithmetic needs a domain parser and representation. |
| `status` cannot have a default | The writer must explicitly set a review state. |
| `index_by` affects large-group peeks/order | It is not a month-bucketing or financial-reporting engine. |
| Album freshness is based on record `created` | It cannot stand for “last account refresh” or “last acknowledged.” Show those separately. |
| Albums and records hold no tasks | Follow-ups and a recurring review reminder belong in `cash`, linking records as context. |
| Each write plans an album index update | Batch imports and realistic volume tests are necessary. |

Sources: [records contract](https://github.com/bobs-org/bob-cli/blob/ba3f51bad3bd491d66e739a895ce4de99149329f/docs/records.md), [record catalog](https://github.com/bobs-org/bob-cli/blob/ba3f51bad3bd491d66e739a895ce4de99149329f/src/native/records/catalog.rs#L1), [filename planning](https://github.com/bobs-org/bob-cli/blob/ba3f51bad3bd491d66e739a895ce4de99149329f/src/native/records/plan.rs#L211), [grouping and freshness](https://github.com/bobs-org/bob-cli/blob/ba3f51bad3bd491d66e739a895ce4de99149329f/src/native/albums/grouping.rs#L57), and the approved album epic plan.

Keep the canonical transaction files in the vault. Use a rebuildable host-local index for fast queries if measurement warrants it. Keep raw statements and credentials out of the ordinary synced vault by default; normalized records carry provenance identifiers sufficient to locate protected import evidence. Do not retain a mutable SQLite database as a second synchronized transaction authority.

A future `bob bank` group is reasonable because it has a clear membership rule: it operates on Bank transaction records and their import, review, and reconciliation metadata. A bare invocation should be a read-only overview. Proposed verbs include `list`, `import`, `acknowledge`, `check`, and `reconcile`; these **do not exist as part of this research**. Final option spellings should follow `cli_rules.md`, including short aliases and alphabetical help. Do not add a subcommand under `bob capture`.

For ordinary record entry, `@bank/` can reuse capture, and the existing `@bank/^explicit-id` form can support a prototype. A bank entry action should eventually supply its stable ID and reduce repeated account/currency typing. That behavior belongs in Bob's planner, with the same generated ID retained from preview to commit; Swift must not implement a second grammar. Avoid inventing compact money sigils before observing actual typing friction.

Scale is an open question, not a benchmark result. Five new transactions a day produces about 1,825 records per year; twenty produces about 7,300. Test 1k, 10k, and 50k synthetic records for capture preview, opening the album, import/index rebuild, sync churn, and mobile browsing. The epic's folded groups still contain their rows. If the full generated index becomes too large, design an explicit generic bounded-index extension after the epic, with complete counts and a link to the full Base. Do not quietly truncate records or change membership to hide the problem.

Git synchronization is not a distributed transaction lock. A conservative v1 has one ingestion writer, records the writing device, and uses the vault's existing guarded writes. All hosts may browse; initially perform bank mutations on the chosen writer. If cross-device review is needed, add immutable per-host review events with deterministic folding and test concurrent changes before advertising it. Same-record conflicts must remain visible; they cannot silently combine one source amount with an acknowledgment of another.

## Privacy, recovery, and operational boundaries

Transaction history is sensitive even without account numbers. The current vault sync model distributes Git history across machines. Before importing live financial data, verify the vault remote's visibility, device access, backup policy, and acceptable retention. Do not infer that a private-looking repository name or a hidden `.bob` directory encrypts anything.

Use account aliases in visible records. Keep credentials, connection tokens, full account/routing numbers, and raw export files out of Markdown, Git commits, debug logs, screenshots, and research artifacts. Ordinary source IDs are not necessarily credentials, but minimize them when an opaque local mapping suffices. Do not feed transaction descriptions to a cloud model for categorization in v1; deterministic suggestions are sufficient and preserve a clear data boundary.

Actual's documentation makes a relevant distinction: bank-sync credentials stored on its server are not protected by its budget end-to-end encryption. Adopting a mature app therefore still requires understanding where connection secrets live. [Actual bank-sync security boundary](https://actualbudget.org/docs/advanced/bank-sync/)

Recovery should be ordinary: rebuild the local index from records and audit metadata; replay an interrupted import without duplicates; restore a mistakenly changed annotation; show source changes rather than deleting acknowledged history. Test backup restoration. All product screenshots and automated fixtures should use synthetic financial data.

## A restrained rollout and its acceptance criteria

**Before the epic finishes:** decide account scope and inspect an export format, if supplied later. Do not create or migrate the live album while the album contract and ledger-mining phase are moving. This research does not change either origin task or its schedule.

**After the epic finishes:** recheck all relevant hosts and the shipped contracts, then make a schema-only pilot in a temporary vault and verify creation, update, links, and presentation. Run the pilot on current activity for roughly two weeks, extending to four if the interaction is useful. Its purpose is to validate the daily routine, not claim automatic completeness. A schema-only prototype should not publish authoritative computed balances.

**First dependable release:** add stable IDs, exact-money validation, one source adapter, conservative import matching, revision-bound acknowledgment, the review UI, and weekly statement reconciliation. Keep the ordinary album and Base as the readable substrate. Export parsing and UI work must not race ahead of the identity and money rules.

**Only then:** consider a read-only connector, additional bank formats, split allocations, advanced charts, or historical import. Prioritize the measured source of friction. If daily file acquisition is unpleasant, test a compatible connector or Actual instead of adding more manual UI.

Suggested trial measures are product targets, not literature-derived thresholds: a median daily session near two minutes, most review days completed without dread, no silent duplicates or data loss, a visible source freshness state, and at least one useful weekly observation. A missed day should be easy to recover from. If the trial becomes mostly transcription, change acquisition; if it becomes mostly categorization, make classification less demanding.

Minimum correctness examples for implementation:

| Case | Required outcome |
| --- | --- |
| Import the same file twice | Second import changes no records or review state. |
| Overlapping exports; two truly identical same-day purchases | Both purchases survive; overlap does not double them. Uncertainty is surfaced. |
| Manual entry later matched to an imported transaction | One Bob identity and preserved notes; conflicting financial facts request review. |
| Pending $20 becomes posted $24; or a hold disappears | No double spending; material changes are visible; removed holds do not vanish from audit history. |
| Salary, transfer, refund, and card repayment all arrive as credits | Financial kind controls summaries; “credit” alone never means income. |
| $0.10 + $0.20, negative amounts, unusual currency precision | Exact totals or explicit unsupported-currency errors, never a rounded reconciliation illusion. |
| Late-posted transaction or corrected historical date | Correct posting-date report; any affected acknowledgment/reconciliation becomes stale. |
| Import failure, offline account, or partial coverage | Queue does not claim complete coverage. |
| Successful check with no new transactions | Review session completes without a fake transaction note. |
| Crash between staged writes; concurrent source change | Recoverable all-or-nothing result; checkpoint does not skip data. |
| Rename merchant or add restaurant link | Stable transaction path and acknowledgment survive annotation-only edits. |
| Hand-edit amount but leave `status: acknowledged` | Read model notices the revision mismatch and asks for acknowledgment. |
| Reconciliation has a nonzero difference | Visible discrepancy, no automatic balancing fiction. |
| Historic `@BANK` total line | Never imported as an individual expense. |

History should remain intact initially. The epic is already rewriting legacy restaurant links, so wait for its completion before any parser touches the old ledger. An optional later migration must preserve source-note anchors, identify daily aggregates and shorthand, report unparseable rows, and mark imported history as historical rather than pretending it was newly acknowledged. A new album should not require reconstructing all of 2024–2025.

## Decisions still needed before implementation

The evidence does not identify the financial institutions, supported export formats, tracked account list, currencies, typical daily volume, use of cash, shared-account policy, or tolerance for third-party aggregation. It also does not explain why the prior habit stopped. These are the inputs that can materially change scope. A small sanitized export sample and a short account inventory are more valuable next inputs than a detailed feature wish list.

The largest decision is whether the desired outcome is **awareness inside Bob** or **a comprehensive personal-finance system**. This report recommends the former based on the task wording and historical practice. If that inference is wrong, choose Actual or another mature financial tool and let Bob host the reminder and contextual follow-ups.

## Recommended solution

Proceed with **Bank under Cash after `bob-cli-k3` completes**, using one stable record per account transaction and a calm, explicit daily acknowledgment queue. Start fresh; preserve old notes; review posted activity; include deposits and transfers while keeping their financial meaning separate. Make categories optional, represent money exactly, and show source freshness as prominently as completion.

Use the existing album system for ownership, record storage, links, and browsing. Add a narrowly scoped Bob banking layer for identity, imports, material-change review, and reconciliation. Begin with one real export format and a short habit trial, not a broad bank-integration platform. Keep Actual Budget as the deliberate fallback if acquisition or accounting requirements grow beyond that scope.

The test of success is simple: Bryan can look at each available movement, recognize it or raise a question, finish with an honest sense of coverage, and occasionally make a better decision because of what he noticed.
