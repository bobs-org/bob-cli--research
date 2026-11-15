# Subscriptions under Bank: evidence, matching, and a design that earns trust

Independent research by **cdx**, 2026-11-15. Context: `bead:bob-cli-kt` and `plan:202611/bank_daily_acknowledgment.md`.

**Recommendation:** build the album. Model one discretionary recurring service or contract per record, use the existing bank journal to prepare a reviewed seed, and match future charges through explicit, exact merchant aliases stored on those records. Keep transaction rows and subscription records separate. A small, accessible `🔁` link is the right row treatment. Do not make historical merchant learning the subscription identity mechanism, or assume every recurring charge has one fixed monthly/yearly price.

This is research, not implementation. I did not create subscriptions, change bank rows, change the tracking start, migrate the legacy note, or close the feature bead. No other report or researcher’s findings from this swarm were consulted. The bead should close after the implemented feature and migration satisfy the acceptance criteria below, not merely after this report is written.

## 1. What is already known, and what needed correcting

The bead is a large feature in `ready` state. Its album dependency, `bob-cli-k3`, is now closed; the description’s statement that albums are still in progress is stale. Its accepted scope is **discretionary keep-or-cancel charges**. Mortgage, loans, insurance, utilities, and household salary payments remain bank categories/rules. The original plan contains both scope alternatives as decision blocks; the bead records the selected one. I retain that selection.

The existing architecture is a good fit:

- An album lives at the vault root. Thus this is `subscriptions.md`, parent `[[bank]]`, with records under `subscriptions/`, not a nested `bank/subscriptions/` folder. Its noun is `subscription` and capture route is `@subscriptions/`.
- A record is one durable thing. A subscription qualifies; each charge does not.
- Bank rows already accept ordinary wikilinks. Import already supports explicit rule links, learned links, and restaurant links. There is no reason to introduce a new inline-field grammar just to relate a charge to its subscription.
- Albums already have ordered status groups, generated indexes, Base files, owner catalogs, schema editing, and keyboard navigation. Reuse these rather than build a separate subscription application.
- The bank importer is a guarded, previewable transaction. Existing rows are user-owned: import writes new rows, but only appends an ID when matching a typed row. Reimport does not enrich existing rows.

The current naming implementation copies only the first learned link from the latest acknowledged row with the same normalized journal merchant. It does not identify a subscription contract, distinguish multiple services sold by one merchant, or constrain learning by amount or cadence. “Link one old row and let learning do everything” is therefore insufficient for this feature. [Code: naming](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/bank/naming.rs), [import planner](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/bank/import_plan.rs).

## 2. There really are six months of usable bank evidence

I inspected the current bank commands, then opened the vault’s repository through `sase repo open gh:bobs-org/bob` to read only the relevant masked bank journal. The snapshot matched the live vault-sync status SHA.

| Evidence | Verified result |
| --- | --- |
| Live bank rows | 11 rows on November 12–13, all acknowledged |
| Configured account | One account, Wells Fargo checking; tracking starts November 11 |
| Journal | 857 events: 3 import events and 854 unique transaction events |
| Transaction date range | May 1–November 13, 2026 |
| Transaction signs | 846 outflows, 8 inflows |
| Journal outcomes | 843 `before_start`; 11 `written` |
| Import windows | May 1–November 10; November 12; August 18–November 13 |
| Explicit `RECURRING PAYMENT` descriptions | 95 transactions, including obligations that do not belong in this album |
| Existing albums | Five; no subscriptions album |

**The hidden history is the key implementation finding.** A `before_start` event retains date, signed cents, account, hashed identity, and masked description, even though it has no bank row. `bob bank list -a` only shows rows, so using it alone would miss 843 transactions. The overlapping export is already deduplicated by the journal. Do not lower `bank.accounts.checking.start`, restore those events into bank month notes, or generate hundreds of waiting checkboxes to perform this review.

The three statement windows collectively span the observed range, but this is coverage of the configured checking account, not proof of every household account, every subscription, or a full annual cycle. Bills paid through another card, Apple/Google intermediaries, another person, or a renewal outside this window may be absent. Six months is sufficient for many monthly patterns; annual contracts still need the legacy list, receipts, or older exports.

There is a second subtlety: **many old journal `merchant` values still contain the purchase date and card wrapper.** Grouping that stored field directly splits a monthly service into many one-off merchants. The current Rust code correctly recomputes `merchant_key(event.desc)` for old events. Subscription discovery must do the same; do not migrate or rewrite the append-only journal.

For a reproducible normalization probe, I built a temporary scratch vault with a minimal bank hub, emitted a synthetic Wells Fargo CSV from the already-masked 854 journal descriptions, and ran installed `bob 0.5.0` with `bank import -d -a checking -b <scratch> -f json`. It successfully planned 854 rows. This exercised the actual current cleaner without touching the real vault, publishing a bank export, or manufacturing real transaction identities. Counts and amounts below come from original journal events; the scratch output supplied cleaned merchant labels. It is a probe of current naming behavior, not a test of the proposed matching feature.

## 3. A concrete seed review

These are observed charges and proposed interpretations, not vendor list prices or declarations that a subscription is currently active. Amounts are USD charges as posted. Full transaction dumps, balances, account identifiers, and unrelated household payments are intentionally absent from this report.

### Strong repeat evidence

| Proposed record | Observed evidence | Proposed initial treatment |
| --- | --- | --- |
| Claude | 7 charges, May–November, all $200; two merchant spellings | Monthly candidate; replace the legacy $100 expectation only after review |
| ChatGPT | 7 charges; May $122.86, June–November $200 | Monthly candidate; May may be a partial period or plan change, which the bank alone cannot explain |
| Audible | 7 monthly charges at $17.05; two Google merchant spellings | Monthly candidate; preserve both observed aliases |
| Google One | 6 monthly charges at $19.99, May–October | **Legacy says yearly; observed series is monthly** |
| YouTube Premium | 6 monthly charges at $15.99, May–October; two spellings | Update the old “YouTube Red” display name and review its $13.99 expectation |
| Spotify | 6 monthly charges at $13.85 | Review the old $11.72 expectation |
| reMarkable Connect | 7 monthly charges at $3.99 | Review the old $3.19 expectation |
| Medium | 6 monthly charges at $5 | Straightforward candidate from both sources |
| Disney+ | 5 charges at $21.31, then October 22 at $23.45 | Show the observed $2.14 difference; do not assert its cause or silently accept it |
| DigitalOcean | 7 charges: $6, $62.43, $62.50, $62.50, $62.50, $338.97, $342.50 | Recurring service with variable or changed billing; inspect invoices before defining a fixed baseline |
| NYTimes | 7 charges at $6, **exactly 28 days apart** from May 26 to November 10 | New candidate absent from the legacy list; `four_weekly`, not monthly |
| Grok | 5 charges in August–October: $30, $66.65, $174.69, then $300 in September and October | New candidate; likely a recurring service with adjustments, but verify the contract and current tier |

The visible November rows only expose Claude and GoDaddy. Relying on those alone would miss most of this list.

### Single charges and ambiguous services worth asking about

| Candidate | Observed evidence | What is still unknown |
| --- | --- | --- |
| No-IP | November 10, $29.99; legacy lists $59.98 yearly | Which plan or domain, and whether the old amount bundled services |
| GoDaddy | May 7, $89.99; November 12, $46.38; legacy lists $44.34 yearly | These may be different domain renewals. Do not collapse them into one fixed-price contract without review |
| Surfline | September 1, $149.99; legacy lists that annual amount | Strong cross-source candidate; annual renewal still needs confirmation |
| Readwise | June 29, $119.88; bank marks it recurring | Candidate with unknown cadence until confirmed; not in legacy list |
| Plex Remote | October 26, $31.98; descriptor contains `REMOTE YEA` and recurring marker | Annual is plausible, not proved by one charge |
| DashPass | September 25, $96; distinct `DD *DOORDASHDASHPA` descriptor | Candidate; keep separate from ordinary DoorDash orders |
| MetaPay | September 21 and October 21, both $50; one marked recurring | Two repeats suggest a bill, but the actual purchased service is not identifiable from “MetaPay” |
| Twilio | July 30, $10.76, marked recurring | Contract versus usage/top-up; do not invent a fixed monthly price |
| Dynalist | June 1, $50.12 | Possible service renewal, one observation only |
| Google Cloud | October 5, $20 | Could be usage or credit purchase; do not equate it with Google One |

Apple.com/bill and AliCloud also appear once. They belong in the review’s uncertain evidence, not automatically in the album. Generic processor or platform descriptors are not service identities.

### Legacy-only candidates

`old_recur.md` has 28 rows in its active section and one inactive Trade Coffee row. Nineteen of those active rows appear to fit the discretionary scope. Thirteen of those nineteen have plausible supporting transactions in this window. The following six had **no obvious matching descriptor** in my review: XMind, Private Internet Access, The Farmer’s Dog, Copilot, Reuters, and Wispr Flow.

Keep them in a “Needs review” draft set with their legacy provenance. Absence from this checking account is not cancellation. In particular, the legacy Wispr entry says `$144 / 1m`; verify that cadence instead of silently treating it as an annual price. Keep inactive Trade Coffee historical; do not reactivate it during migration.

Exclude mortgage, both student-loan entries, gas, car insurance, Verizon, sanitation, ordinary train tickets, and household salary payments from this discretionary album. Their recurrence is real but they serve a different review purpose. Insurance and daily coffee transactions in the journal provide useful negative examples for the detector.

## 4. Explicit changes I recommend to the bead

| Original requirement | Recommended adjustment and reason |
| --- | --- |
| Seed from active legacy rows | Reconcile legacy rows **and** journal evidence, including `before_start`. Neither source alone is current and complete |
| Amount required | Make expected amount optional until confirmed, and distinguish fixed from variable billing. Unknown is not zero |
| Monthly/yearly only | Add `four_weekly`, `weekly`, `fortnightly`, `quarterly`, `irregular`, and `unknown`. NYTimes demonstrates the immediate need for four-weekly |
| Active/to-cancel/cancelled only | Add `needs_review`, placed first. A generated proposal must not assert active status |
| One suggestible `payee` | Use an optional list of exact bank merchant aliases, selected from observed evidence. Keep friendly title separate |
| Required matching strings | Require an unambiguous match only **to enable automatic linking**, not to create a record. Some annual or aggregator-billed services cannot safely match yet |
| Learned links drive future imports | Use explicit record matchers as authority. Learned subscription links can suggest a mapping, but cannot bypass it |
| Compare every linked amount with current amount | Compare recent comparable charges against a reviewed, date-effective expectation. Otherwise every old price becomes a permanent alert |
| Three annual charges to detect recurrence | Two annual occurrences support a recurring pattern; one plus explicit legacy/receipt evidence can support a review proposal. Three annual charges would demand two years of history |
| Rewrite existing links as part of normal import | Keep import ownership intact. Backfill only through an explicit previewed migration or row-edit gesture |
| De-zorg immediately | Retain and link the legacy source until accepted records and inbound-link checks are complete; then perform the existing bead’s migration as a separate step |

Also narrow the album summary to **“Discretionary services we pay for repeatedly, and whether they still earn their keep.”** “Everything that charges us on repeat” contradicts the selected scope.

## 5. Record design: small facts, explicit uncertainty

Use one record per independently cancellable service or contract. Two domains with different renewal schedules can deserve two records even when both charge through GoDaddy. A usage-based cloud account can be one record without pretending it has a fixed price.

A proposed schema, using existing album field kinds:

```yaml
parent: "[[bank]]"
type: "[[album]]"
emoji: 🔁
summary: Discretionary services we pay for repeatedly, and whether they still earn their keep.
index_facets: [amount, cadence, category]
record:
  noun: subscription
  label: Subscription
  plural: subscriptions
  dated_notes: true
  fields:
    status:
      required: true
      values:
        needs_review: 🔎 Needs review
        to_cancel: ✂️ To cancel
        active: 💚 Active
        cancelled: 🚫 Cancelled
    amount:
      label: Expected charge (USD)
      values: number
      min: 0
    cadence:
      required: true
      values:
        unknown: ❓ Unknown
        weekly: Weekly
        fortnightly: Every 2 weeks
        four_weekly: Every 4 weeks
        monthly: Monthly
        quarterly: Quarterly
        yearly: Yearly
        irregular: Irregular
    billing:
      values:
        fixed: Fixed
        variable: Variable
        unknown: Unknown
    amount_since:
      label: Price effective from
      values: date
    bank_matches:
      label: Bank merchant aliases
      list: true
    bank_accounts:
      label: Match only these bank accounts
      list: true
    category:
      suggest: true
    renews:
      values: date
    cancelled_on:
      values: date
    url:
      values: url
```

No new generic album field type is needed. No `status` default: the seeding action explicitly chooses `needs_review`; the user chooses active/to-cancel/cancelled. Unknown billing and price remain honestly unknown. `amount_since` scopes comparisons, and `cancelled_on` permits an intelligible “charged after cancellation” finding. These dates are not inferred from missing transactions.

`category` uses existing bank category keys such as `tech`, `media`, or `dog`, not a blanket `subscriptions` spending category. Recurrence is a relationship, orthogonal to what the money bought. Do not silently change bank category selection because a subscription matched; validate the record’s category and offer it during review.

`renews` means an explicitly known next renewal date. An inferred next posting window is derived display data and must be labelled estimated. Do not perpetually advance an authored `renews` field behind the user’s back.

The bank-specific reader validates these conventional fields in the album resolved by noun `subscription`, not a hard-coded directory. It must report duplicate/invalid noun resolution and wrong field shapes. Generic album validation still handles normal record facts. `amount` is a generic number, so bank consumption must additionally reject fractional cents and convert checked decimal values to integer cents; money comparisons and totals never use floating-point arithmetic. Current USD-only support is retained.

Put source links and dated observations in `## Notes`: legacy block, reviewed date, and concise evidence. Do not copy every charge into the record or maintain a mutable “last charge” frontmatter cache. Derive last charge, observed spend, and linked history from bank data. Pre-start evidence has no row target; present a dated journal-evidence reference in the bank report rather than inventing a `bank/YYYY-MM` link.

## 6. Matching: exact aliases, one shared resolver, no hidden guess

### Recommended v1 semantics

`bank_matches` is a list of **literal merchant identities**, not arbitrary substring patterns. Normalize each entry and each source description with one documented function based on the existing conservative `merchant_key`. OR the aliases within one record; apply optional account restrictions as an AND. Reject empty normalized values. A literal `*` is literal, not a wildcard. No regex language, fuzzy matching, dollar thresholds, or inferred recurrence in import’s automatic identity path.

Examples from the normalization probe:

```yaml
# A reviewed Claude record
bank_matches:
  - "Anthropic* Claude"
  - "Claude.ai Subscrip"

# A reviewed Audible record
bank_matches:
  - "Google *audible Au"
  - "Google Audible Aud"
```

These are example observed aliases, not a seed patch to apply blindly. The implementation must show their exact current matches before acceptance. Google One and YouTube have their own distinct observed aliases. Never suggest a broad `GOOGLE`, `APPLE`, `AMAZON`, or `PAYPAL` substring as a safe contract identifier.

Use the **masked description consistently** at import and at read time. Recompute historical merchant identities from descriptions rather than trusting legacy stored `merchant`. Keep word-bearing submerchant distinctions. The normalization version and catalogue fingerprint should accompany preview evidence so a cleaner change forces an explicit re-evaluation. Do not preserve raw bank identifiers to improve matching.

For each eligible posted outflow:

1. Resolve any explicit `bank.rules.link` as today. A rule that deliberately targets a subscription wins and its result is explainable; a non-subscription link is independent.
2. Otherwise evaluate reviewed record aliases. `needs_review` records do not auto-link. Active, to-cancel, and cancelled records can identify charges: cancelled does not erase identity.
3. Exactly one matching record produces one subscription link. Multiple matching records produce a bounded ambiguity diagnostic and no inferred subscription link. Zero produces none.
4. Learned links targeting subscription records are not an alternative authority. They can prefill an alias proposal but must pass the same current resolver before reuse. Regular restaurant or authored unrelated links keep their existing behavior.
5. Transfers, income, zero-value rows, and refunds do not infer subscription expense links in v1. An explicitly authored link remains allowed. Refund association can come later as a separate, signed relation rather than a negative “price”.

Do not use expected amount as a normal matching condition. The same service must still match when its price changes. If two subscriptions have an indistinguishable bank descriptor and account, **the data cannot identify which one charged**. Require a user-selected relation for that row; do not settle the tie by record order, price, or the last acknowledged purchase. Date-limited contracts and richer rules can be added when a demonstrated case needs them.

### Integrating without breaking current behavior

Today `NameResolution` carries one optional link even though bank rows carry a link vector. Split subscription resolution from generic name/category selection and combine results with target-based deduplication. Preserve one existing rule/learned/restaurant link where applicable and append at most one subscription link. An explicit subscription rule and an automatic match must never generate two subscription targets. A conflict is visible, not silently resolved by whichever vector entry happened to be first.

Use the same resolver for import, historical preview, candidate review, and check. Return structured provenance: target, source (`rule` or record alias), matched alias/account, and ambiguity candidates. Additive JSON data lets the plugin render the result without independently implementing bank matching.

Follow the existing restaurant loader’s guarded-read pattern: album declaration, relevant record bytes, folder membership, and registry membership all participate in the import preconditions. An unreadable or changing catalogue is not an empty catalogue. Refuse unsafe snapshots before mutation. Readable invalid records/matchers should be diagnosed by `bank check`; do not silently let an invalid competitor disappear and make another candidate “unique”. The implementation should withhold inferred links for affected identities; unreadable membership requires refusal because affected identities cannot be bounded.

Newly created rows get the link at birth, including deliberate restoration from masked journal evidence. Seen rows stay byte-identical. Matching an existing typed row still appends only its bank ID. A separate link-edit action or reviewed migration must handle existing rows. Do not opportunistically teach aliases by acknowledging a charge, and do not create subscription records during ordinary import.

## 7. Discovery and price review should be useful, not noisy

The original three-charge idea is a sensible signal, not a definition of subscription. This dataset contains 99 coffee charges and 28 identical ATM fees. Frequency and equal price alone are not enough. Conversely, annual renewals and new subscriptions can be useful candidates after one observed charge.

Build a pure review service over journal identities plus current rows:

- Deduplicate imported observations by hashed transaction key. Attach current row text/links by unambiguous bank ID when present. Typed ID-less rows remain separately labelled evidence; do not guess that they are duplicates and inflate confidence.
- Group with current normalized identities and **reviewed** alias groups. Plausible cross-alias merges such as Claude’s two names can be proposed with both series shown, not silently learned as fact.
- Show account, date range, coverage, count, charge amounts, gaps, recurring marker, existing links, and the reason for each proposal.
- Distinguish calendar-month cadence from fixed-day cadence. NYTimes is every 28 days; monthly series vary with month length, weekends, and posting delays. Proposed tolerances must be fixture-backed, not unexplained percentages presented as confidence.
- Three monthly cycles are strong evidence; two are an early candidate. Annual singletons stay reviewable and “cadence unconfirmed”; two annual occurrences support an annual hypothesis. Missing cycles can lower confidence but never auto-cancel.
- Recurring bank wording strengthens a proposal but does not override discretionary scope. Suppress known obligations, transfers, fees, and previously dismissed merchant candidates.

A small persistent dismiss/ignore facility is needed before unattended candidate findings become part of routine checking. Store explicit suppression decisions in bank-owned configuration or a minimal established journal namespace, not by creating fake cancelled subscription records. Keep the first release’s discovery an explicit review so it can prove its quality before becoming persistent background noise.

Price findings should say **“charge differs from expected”**, not “vendor increased its price”. A difference can be tax, usage, proration, currency conversion outside current support, multiple services, or an identity error. Compare only unambiguously associated outflows for fixed billing, at/after `amount_since`, and summarize the latest unresolved discrepancy per record. Updating a reviewed expectation must stop old history from becoming an endless warning. Variable billing shows observed amounts/trend; a distinct threshold alert is optional future work.

Keep `bank check` read-only. Candidate/price findings should normally be info/warnings, preserving successful exit status for otherwise healthy bank data. Malformed subscription configuration is a separate actionable diagnostic. A charge after `cancelled_on` is especially useful, but always shows the cancellation and posted dates so settlement lag can be judged.

For a product precedent, Plaid recommends at least 180 days for recurring analysis and distinguishes early streams from mature streams, with three occurrences normally and two for annual streams. That supports a review lifecycle and longer history; it does not justify adding Plaid or a cloud classifier to Bob. [Plaid Transactions API](https://plaid.com/docs/api/products/transactions/).

## 8. Presentation: quiet in the statement, informative on focus

Canonical Markdown remains concise:

```markdown
- [ ] $200.00 Anthropic* Claude [cat:: tech] [[subscriptions/claude|🔁]] ^bank-…
```

Rendered statement sketch:

```text
☐  $200.00  Anthropic* Claude     Tech & AI   [🔁]
☐   $23.45  Disney Plus          Media       [🔁]
```

The subscription chip should use the same height, radius, spacing, and subdued border as existing bank chips. It should be a real note link, have a visible focus ring and a practical padded hit area, and preserve modifier-click, hover preview, and source-edit behavior. Give it an accessible name such as **“Open Claude subscription”**. A tooltip/focus popover can show `Claude · Active · $200/month · latest charge Nov 13`; money is not duplicated on the row itself. Hover is an enhancement, not the only way to learn its purpose. Descriptive context and names follow W3C’s link-purpose guidance. [W3C WCAG 2.2, Link Purpose](https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context.html).

Do not style every subscription warning-yellow. Normal charges stay quiet. A genuine unresolved difference may add a small amber marker with textual explanation in detail. Cancelled records retain the relation; an unexpected new charge can be flagged separately. Source mode always retains the standard wikilink. Plugin-disabled rendering still yields a usable link with neighboring payee context.

The linked plugin currently decodes `row.links`, and its bank marks tokenizer retains link spans, but the queue card’s row renderer only draws money, payee, category, and a line jump. Therefore “write the link” is not enough: implement the relation in **Reading view, Live Preview, and the queue card**. Preserve line cursor reveal and do not interfere with Category-card acknowledgment. The current bank mark files and `bankCardRenderQueueRow` are concrete extension points.

The album should retain its existing generated records index and actionable status order. Add a small optional read-time summary above it, not a replacement dashboard:

```text
🔁 Subscriptions
Needs review 4   ·   To cancel 1   ·   Active 12
Confirmed fixed commitments: $…/month equivalent
3 variable or unknown charges excluded · evidence through Nov 13
```

Counts above are illustrative. Never present illustrative totals as measurements. Monthly equivalent is only for confirmed fixed records; yearly divides by 12, quarterly by 3, and four-weekly uses 13 charges/year divided by 12 under the chosen 52-week convention. Label this an estimate of commitments, not actual bank spend. Keep cancelled/review records and unknown/variable amounts outside that subtotal and show the exclusion count. Actual spend remains the bank’s observed money, with its own coverage and transfer rules.

The schema’s amount facet is currently a plain number. Add currency/cadence formatting at the bank-aware presentation layer, so users see `$13.85 / month`, not an unexplained `13.85`. Preserve ordinary Markdown/Base access and the generated index’s ownership.

The review interaction should be simpler than the schema. Present one candidate with a small charge timeline, proposed title/aliases/cadence, evidence source, and **Create**, **Link existing**, **Not a subscription**, **Later**. Preview the exact record and affected rows before apply. Do not make users edit matching YAML before they have seen which charges it selects.

## 9. Alternatives and why I would not choose them

| Approach | Benefit | Cost / decision |
| --- | --- | --- |
| Album plus existing `bank.rules.link` only | Very small implementation; rules already work | Acceptable bootstrap for a few precise descriptors. Poor record-centred review and no ambiguity/coverage story |
| Learned subscription link from latest acknowledged row | Almost no new matching code | Too implicit; same merchant can sell several contracts, learning can be cross-account, and unlinking behavior is surprising. Reject as authority |
| Required substring list on every record | Easy to explain initially | Broad strings overmatch; annual/unknown records need fabricated rules. Prefer optional exact aliases selected from evidence |
| Structured regex/condition language in records | Can handle complex billing descriptors | Duplicates bank rules, overwhelms capture and schema UI, and still cannot distinguish identical descriptors. Defer |
| Runtime fuzzy/LLM subscription classifier | Can recognize messy service names | Irreproducible attribution and hard-to-explain false positives; unnecessary for this small private collection. Use judgement during reviewed seeding only |
| Album of all recurring obligations | More comprehensive cash-flow view | Dilutes the accepted keep-or-cancel purpose. A later recurring-bills report can cover obligations without changing this album |
| Journal-only computed relations, no written link | Easy to recalculate | User requested durable navigable row links; computed matching changes could silently change historical attribution. Use stored links for actual rows and labelled computed evidence for pre-start history |

Actual Budget usefully separates the original imported payee from edited display identity and exposes editable rules. Borrow that separation and an explicit “use this mapping next time” gesture, not its rule-priority semantics wholesale: Bob should leave an ambiguous subscription unlinked. [Actual rules](https://actualbudget.org/docs/budgeting/rules/), [payees](https://actualbudget.org/docs/transactions/payees/).

## 10. Implementation boundaries and completion criteria

A practical delivery sequence is:

1. **Evidence and schema:** expose a read-only bank subscription review over existing journal data, load the subscription album through the registry, and implement alias validation/provenance. One possible public command is `bob bank subscriptions` with `-f/--format`, `-b/--bob-dir`, and `-a/--account`; it is a bank report over charges and subscription relations, not another generic record editor. Final flag choices must follow the CLI rules and generated help.
2. **Reviewed seed:** create the album with `bob albums create bank subscriptions -n subscription -e 🔁 -t Subscriptions -s '<summary>'`; use existing schema/record writers for accepted facts. Assemble the proposed records before asking Bryan to decide uncertain contracts. Store undecided evidence as review candidates, not active commitments. Do not infer URLs, cancellation instructions, or renewal dates from merchant text.
3. **Linking and findings:** use one resolver in import, restore, preview, historical association, and `bank check`. Add a targeted, previewable link migration for selected existing rows; preserve all other row bytes and child notes. The seed transaction or migration needs exact preimages and no-overwrite destinations, with a dry-run/apply fingerprint and idempotent rerun behavior.
4. **Presentation:** reuse album cards and bank marks, add the subscription chip across all three bank surfaces, and render price/cadence/coverage honestly. Cache derived summaries with invalidation for album/record changes, bank month/journal changes, and relevant date rollover.
5. **Legacy cutover:** keep block IDs and resolve every inbound link before converting `old_recur.md` to the requested `legacy_recur` notebook under `cash`. If preserving its path temporarily is safer, make that an explicit migration adjustment. Update `cash.md#^audit-monthly-subscriptions` to the album without changing the task’s review/status semantics. Synthetic fixtures, not private transactions, belong in source tests.

Critical implementation files in bob-cli are `src/native/bank/{journal,identity,naming,import_plan,import_run,check,model}.rs`, with the existing `records` context/catalog/schema and album transaction planners. Reuse the guarded restaurant registry loader as precedent rather than adding an unguarded directory scan. Plugin work belongs in `bob-plugins`, then deployment through `bob plugins sync` after verification. The Mac capture client needs no new bank-matching logic; existing album/capture contracts suffice unless their JSON contract actually changes.

Tests should establish behavior, not merely mirror helper functions:

- Journal events before account start contribute review evidence but never create rows, affect tracked totals, or change acknowledgment counts.
- Old dirty `merchant` values are recomputed from masked descriptions; import, restore, and historical review resolve the same aliases.
- Aliases for two Google services remain distinct; literal asterisks, casing, whitespace, masked digits, and merchant renames have explicit fixtures.
- Multiple records matching one identity withhold linking; amount changes still match; generic processor descriptors remain uncertain.
- Learned subscription links cannot override record ambiguity or account restrictions; explicit rule links and unrelated restaurant links retain defined behavior.
- Reimport/overlap/retry remain idempotent; typed-row matching still edits only its ID; one-off backfill changes only selected link spans.
- Catalogue edits and new records between preview and apply cause stale refusal; unreadable inputs cannot become false uniqueness; rollback preserves external edits.
- The NYTimes fixture fits four-weekly cadence; variable cloud charges do not emit repeated fixed-price errors; annual singleton evidence never claims a proven annual pattern.
- Updating a price expectation does not re-alert on all old charges; cancellation does not auto-unlink or auto-reactivate a record; unknown coverage never implies cancellation.
- UI checks cover Reading, Live Preview, queue card, keyboard navigation, focus/accessible name, narrow panes, light/dark themes, plugin-disabled fallback, and unchanged source bytes after rendering.

Close `bob-cli-kt` only after the actual album and reviewed seed exist, new imports link safely, useful candidate/price findings work, historical linking is explicitly applied where selected, the audit task points at the album, legacy migration preserves identity/links, and the relevant CLI/plugin checks pass. If implementation intentionally narrows the original migration or finding scope, record the agreed change before closing. This research does not itself meet those criteria.

## 11. Evidence and reproducibility

Primary observations were made on 2026-11-15:

- bob-cli checkout: `9c2c240480998e1b9ecd82a5c70aefbe963b8c58`; installed binary: `bob 0.5.0`.
- bob-plugins checkout: `f72bd4e96403a7e6a3f287c8f191ec70fa3e5c4a`.
- Vault checkout and reported live synced SHA: `22dd8c80ccfc486088c2bc0986f2d029ccdd726d`.
- Audited context: `sase bead read bob-cli-kt`; `sase artifact read plan:202611/bank_daily_acknowledgment.md`; relevant glossary, artifact, vault, and CLI memory.
- Read-only live reports: `bob bank list -a -f json`, `bob albums list -f json`, and `bob vault-sync status --json`.
- Legacy source via `bob query`: `TABLE WITHOUT ID L.line AS Line, L.section AS Section, L.text AS Text FROM "old_recur.md" FLATTEN file.lists AS L`. A focused query also confirmed `cash.md#^audit-monthly-subscriptions`. The native query emitted unrelated ambiguous-link warnings; it returned the requested source rows. Broad empty-root DQL was not used as evidence of absence; the album registry supplied that evidence.
- Historical source: the sole `.bob/bank/*.jsonl` file in the opened vault snapshot. Group unique `bank.txn` by `key`; report import windows separately; inspect `desc`, `posted`, `cents`, and `outcome`. Repeated export imports did not multiply transaction events.
- Normalization probe: temporary minimal scratch vault and synthetic CSV from masked journal descriptions; `bob bank import -d` planned all 854 rows successfully. Temporary files were removed after the probe. No live import or financial write was performed.

Repository contracts and implementation references:

- [Bank contract](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/docs/bank.md): ownership, row grammar, naming, journal, import transactions.
- [Records contract](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/docs/records.md): root-level albums, schema kinds, indexes, required-field semantics, and record writers.
- [Journal reader](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/bank/journal.rs), [identity normalization](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/bank/identity.rs), [guarded import loader](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/bank/import_run.rs).
- [Album presentation contract](https://github.com/bobs-org/bob-plugins/blob/f72bd4e96403a7e6a3f287c8f191ec70fa3e5c4a/docs/albums.md); plugin bank fragments `241h-plugin-bank-decode.js`, `241m-plugin-bank-cards.js`, `241o-plugin-bank-marks-model.js`, `241p-plugin-bank-marks.js`, and `241q-plugin-bank-marks-reading.js` were inspected locally.

External sources were limited to official Plaid, Actual Budget, and W3C documentation, linked beside the claims they support. No private transaction text was sent to external research services. Proposed heuristics, schema, interaction, and implementation boundaries are my recommendations, not claims that the present product already implements them.

## Recommended solution

**Proceed with a discretionary subscriptions album, seeded through a review of the existing six-month journal plus the legacy list. Store explicit exact merchant aliases on reviewed records; let a shared deterministic resolver add one compact, accessible subscription link to new bank rows. Preserve written history, treat ambiguity as a reason to ask rather than guess, and keep observed charges separate from confirmed contract terms.**

Start with the verified repeat series, then review annual/ambiguous/legacy-only candidates. Include four-week billing and variable prices from the first release because the actual data requires them. Reuse the existing album and bank UI, put uncertainty and exceptions in the review detail, and reserve normal statement space for a quiet `🔁`. This achieves the user’s intended convenience and beauty while making every automated link understandable and correctable.
