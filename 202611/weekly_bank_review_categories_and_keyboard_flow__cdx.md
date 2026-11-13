# Weekly bank review: categories, keyboard flow, and a quieter ritual

Independent research by **cdx**, 2026-11-13. Research and design only; no application code, bank configuration, transaction rows, or recurring tasks were changed.

## Recommendation in brief

Adopt **one Monday import-and-review ritual**, replacing the daily manual-entry obligation and consolidating the existing Monday import reminder. Extend the categories already configured in `bank.md`. On an unchecked bank row, **Ctrl+Enter → one category key → one atomic category-and-checkbox edit → next waiting row**. Use a compact, keyboard-first card with stable shortcuts, cancellation, explicit Unclassified, and a guarded undo.

This is a good idea if the feature reduces effort spent reviewing real transactions. It becomes a poor trade if every transaction demands a classification guess or if category selection accidentally hides spending. Acknowledgement, categorization, and reconciliation must remain three separate facts.

## Evidence and scope

I independently read `bob-cli-kd`, its approved plan, the bank contract and guide, Rust implementation, plugin implementations and relevant tests. I inspected the vault through a brokered repository checkout. I did not consult this swarm's other reports or agents.

The private import journal establishes two distinct observations: a historical Mac import on **November 12**, then a small new-row import on **November 13**. Thus “imported yesterday” does not describe all of the current ledger. The historical import contains several months of transactions marked `before_start`; these were journaled but deliberately not rendered as bank rows. The newer imported rows in the inspected snapshot were already acknowledged and lacked categories. I used the historical merchant families to assess taxonomy coverage, and the current rows to understand the interaction gap. I did not reopen those rows, change the account start date, or restore historical transactions.

This report contains no real transaction examples, amounts, balances, merchant lists, locations, people, identifiers, or category-by-category personal activity counts. Suggested categories are menu choices, not claims about particular purchases. Merchant descriptions cannot establish the purpose of mixed retail purchases, reimbursements, payment-platform transactions, or cash withdrawals.

The synced checkout was the evidence source, not a live inspection of the Mac's Downloads folder or authenticated Wells Fargo session. Unpushed Mac changes could differ. Public Wells Fargo links were checked independently; no private transaction text was sent to web search.

Source snapshots:

- bob-cli: `c994cfbd1d0d0a8271b5b27c3db5b6d6d73b0795`.
- bob-plugins: `2ee64e603c3b1dc5eab0d15c6b8ec4aebc7b8c4a`.
- Vault: `962024aea3cc75ffb6b15a097958e872be76b8c7`.
- Audited context: `bead:bob-cli-kd`, `plan:202611/bank_daily_acknowledgment.md`, and the Bank Row, Bank Month Note, and recurring-occurrence memories.

## What already exists

| Capability | Observed implementation | Consequence |
| --- | --- | --- |
| User categories | `bank.categories` is an ordered map in `bank.md`; the live configuration already has a substantial starter list | This is an extension and better discovery, not a new category system |
| Special categories | `income`, `refund`, `transfer`, `cash` always exist; labels may be overridden | Their IDs have accounting meaning and must remain stable |
| Categorized Markdown | `[cat:: key]`; category chips, completion after `[cat:: `, and report breakdowns | Keep the existing representation |
| Import suggestions | Explicit rule → latest acknowledged matching merchant → bank heuristics → cleaned name | Manual category choices can help later imports without introducing a new learning database |
| Ctrl+Enter | `task-status-cycler` recognizes bank rows and flips one checkbox byte | It currently neither prompts nor advances |
| Batch acknowledgement | CLI `ack`, day commands, and rendered-card ID snapshots | Preserve these explicit bulk operations; do not force a modal into scripts |
| Review queue | `bob bank list` is waiting rows across months, oldest first | Reuse its ordering and the existing bank service |
| Weekly reminder | A Monday QFX import chore already lives in `gtd_daily.md` beside the daily acknowledgement chore | Merely changing daily recurrence would leave duplicate chores |
| Reconciliation | Independent coverage, presence, immutable imported amounts, balance and staleness checks | A tick must never imply balanced, current, or correctly categorized |

The existing contract says Bob writes rows once, then only ticks them or appends a matched ID. Category selection deliberately expands this narrow ownership: **an explicit user gesture may update the selected row's category**. Imports still must not rewrite categories on existing rows. Bank rows remain ordinary checkboxes without `#task`, freshness, completion dates, dependency effects, or task-review-walk advancement.

Primary implementation evidence: bob-cli `src/native/bank/{config,naming,model,ack,list,grammar,scan}.rs`; bob-plugins `plugins/task-status-cycler/src/160-plugin-completion.js` and `192-bank-row-guard.js`; `plugins/bob-ledger-tools/src/241j-plugin-bank-data.js`, `241k-plugin-bank-actions.js`, and `241m-plugin-bank-cards.js`.

## Weekly ritual and the Wells Fargo link

### Consolidate, rather than multiply, reminders

Keep one active **Bank review** chore in `gtd_daily.md`, using the existing Monday recurrence:

```text
[repeat:: every week on Monday when done]
```

The filename does not require every contained chore to recur daily. Preserve the weekly chore's current schedule and identity where present. Update that chore, retire only the active daily successor as superseded, and retain completed historical occurrences and their links. The inspected completed daily occurrence has a block ID that the active successor does not; migration must not mistake that historical ID for the active task.

Suggested user-facing task content:

```markdown
- [?] #task #gtd #pre **Bank review**: [Download Wells Fargo activity](https://connect.secure.wellsfargo.com/auth/login/present?LOB=CONS&loginMode=jukePassword&origin=cob&serviceType=accountActivityDownload) · import QFX · review [[bank|waiting transactions]] [repeat:: every week on Monday when done]
  - Download posted activity with overlap; normally the last 14 days.
  - Import the selected QFX file, then review and categorize waiting rows.
  - Check coverage and balance; record any unresolved issue before completing.
```

This is proposed wording, not a complete migration row: retain or deliberately set its real scheduled date and required task metadata through the established task tooling. Verify that a not-yet-due occurrence does not enter PRE and that an overdue occurrence remains visible. Do not add freshness stamps to recurring chores.

Prefer an explicit freshly downloaded filename over instructing the user to repeatedly import every historical `~/Downloads/*.qfx`. Replay is idempotent, but a wildcard can include unrelated accounts and obsolete files. The software already accepts overlapping exports. Normally 14 days covers a weekly cadence with margin; after a lapse, choose a range that overlaps the last verified coverage, not blindly the last 14 days. Keep `stale_after: 10` initially: seven days plus a small grace interval is consistent with weekly review. Do not loosen it merely to make status look healthy.

The routine's completion means the import was reviewed and any outstanding issue was consciously handled. Zero new transactions is valid. An unresolved discrepancy must remain visible and can receive a separate follow-up task; do not invent a $0 row or tick transactions automatically when the chore is completed. Optional manual entry remains available without a daily obligation.

### Link evidence

Wells Fargo's official [Account Services page](https://www.wellsfargo.com/help/online-banking/services/) publishes a **Download Account Activity** quick link to the exact sign-on URL used above. It is a better task link than a generic homepage or an account-specific URL copied from a logged-in session. Its [Account Activity FAQ](https://www.wellsfargo.com/help/online-banking/activity-faqs/) documents downloads and Quicken Web Connect support.

The public link resolves to sign-on. I did not verify the post-login destination with Bryan's account. Keep the Account Services page as the documented fallback if the bank changes its routing. Choose **Quicken/QFX**, preserving the balance and coverage evidence Bob already uses; do not substitute a PDF statement or silently change the import format.

## Category design grounded in the private sample

### Keep a modest, purpose-based vocabulary

The sample supports retaining distinctions already present in the starter taxonomy, including everyday purchases, transport, household bills, discretionary digital services, and fees. It also motivates two neutral additions: **Personal** and **Debt payments**. These avoid forcing legitimate outflows into an unrelated category or treating every repayment as a transfer. This is a menu recommendation, not a classification of anyone's individual transactions.

Do not introduce merchant-specific, sensitive, or diagnosis-specific categories. Do not split categories solely because a merchant description contains an interesting word. For a mixed basket, choose its main purpose or explicitly leave it unclassified; split transactions are outside this change.

The following is a concrete complete shortcut proposal. It preserves existing category IDs and adds only `personal` and `debt`. Existing optional categories remain available without asserting that the inspected sample establishes a need for each one.

| Key | Stored category | Display label | Boundary |
| --- | --- | --- | --- |
| G | `groceries` | 🛒 Groceries | Food for home; not every mixed-store purchase |
| D | `dining` | 🍽️ Dining | Meals and prepared food, including delivery |
| C | `coffee` | ☕ Coffee | Keep the existing distinction; user may merge later |
| T | `transit` | 🚆 Transit | Public transport and similar fares |
| A | `car` | 🚗 Car | Vehicle costs; purpose overrides payment method |
| H | `home` | 🏠 Home | Housing and household costs |
| U | `utilities` | 💡 Utilities | Essential recurring household services |
| P | `dog` | 🐶 Pets | Label-only broadening; preserve the existing key |
| K | `kids` | 🧸 Kids | Retained optional household distinction |
| M | `health` | 💊 Health | Broad, nonspecific health costs |
| S | `shopping` | 🛍️ Shopping | General goods when a better purpose is unknown |
| B | `subscriptions` | 🔁 Subscriptions | Discretionary subscriptions; not all recurring debits |
| E | `fun` | 🎟️ Leisure | Entertainment and recreation |
| F | `fees` | 🧾 Fees | Bank or payment fees |
| N | `personal` | 🧴 Personal | Neutral personal purchases and services |
| L | `debt` | 🧮 Debt payments | Cash-flow payment bucket; no principal/interest split |
| I | `income` | 💵 Income | Identified income, never inferred from positive sign alone |
| R | `refund` | ↩️ Refund | Recognized refunds |
| X | `transfer` | ↔️ Transfer | Recognized movements whose exclusion is intentional |
| W | `cash` | 🏧 Cash out | Cash withdrawal, not its later use |
| 0 | **no category** | Unclassified | Explicit action, not a new stored category |

The mnemonic key is printed beside every choice. It is a shortcut, not a new transaction field. The more marginal labels can be refined after actual use; do not spend the implementation budget building category hierarchies or a category-management application.

### Extend the current configuration additively

Keep existing scalar values legal and add an optional richer value:

```yaml
bank:
  categories:
    groceries: { label: "🛒 Groceries", shortcut: g }
    dining: { label: "🍽️ Dining", shortcut: d }
    coffee: "☕ Coffee"  # existing string form remains valid
    personal: { label: "🧴 Personal", shortcut: n }
    debt: { label: "🧮 Debt payments", shortcut: l }
```

At rollout, populate explicit shortcuts for the complete configured menu above, including built-ins if desired. Rust resolves labels, builtin meanings and shortcuts into the existing JSON `categories` catalog. Add `shortcut` as an optional field; update plugin decoding to retain it. Do not change existing `key`, `emoji`, `label`, or `builtin` meanings, and do not change schema version solely for an optional additive field.

Validate case-insensitive duplicate shortcuts, reserved actions, unknown object fields, blank labels, and invalid category IDs. `0`, Enter, Escape, Tab and `/` belong to actions/navigation. Strings without a shortcut remain selectable by focus/search; do not assign them changing letters based on recent usage or array position. For arbitrary larger custom catalogs, explicit unique shortcuts are required for the one-key guarantee. The supplied starter menu fits without numeric pages or changing mappings.

Renaming a display label is safe. Renaming a stored category key changes historical meaning and requires a separate previewed migration; deleting a category still used in rows must be surfaced by validation, not silently rewritten. No journal schema changes are needed.

### Be conservative about inference

The live configuration contains a payment-platform-wide transfer rule. Review and remove or narrow that rule during implementation: a payment rail is not a purpose. The importer also treats broad payment/bill-pay signals as transfers in `naming.rs`; those suggestions must remain visibly reviewable. This is a semantic risk identified by source inspection, not a claim that a particular private transaction was misclassified.

Explicit rules outrank learned categories. Correcting a row will therefore not fix a conflicting broad rule for the next import. Explain that precedence and avoid promoting a one-off choice into an unconditional new rule.

Preserve existing merchant learning for new imports, but never silently acknowledge a suggested row. The current import does not recategorize previously written waiting rows, so do not promise that categorizing one row updates the rest of the current batch. A later, separate improvement could offer a visible suggestion based on an earlier choice in the same review session; it is unnecessary for the first release.

Subscriptions is a purpose bucket here. It does not create a subscription registry, infer renewal contracts, or change the separately tracked subscriptions follow-up.

## Interaction: quick, legible, and safe

### The card

On an unchecked, valid bank row, Ctrl+Enter opens **Review transaction**. The row remains unchecked until a choice commits. Keep the card at a stable position and size; use the vault's established bank accent, restrained separators, tabular amount digits, and a clear focus ring. Use one emoji per category and textual labels throughout.

Illustrative layout, using entirely synthetic data:

```text
┌ Review transaction ────────────────────────────────┐
│ Example Market                             $12.34 │
│ Thu Nov 12 · Checking · 6 waiting                  │
│                                                   │
│ [G] Groceries           [D] Dining                 │
│ [C] Coffee              [T] Transit                │
│ [A] Car                 [H] Home                   │
│ [U] Utilities           [P] Pets                   │
│ [K] Kids                [M] Health                 │
│ [S] Shopping            [B] Subscriptions          │
│ [E] Leisure             [F] Fees                   │
│ [N] Personal            [L] Debt payments          │
│ [I] Income              [R] Refund                 │
│ [X] Transfer            [W] Cash out               │
│                                                   │
│ [0] Unclassified   [/] Search   [Esc] Cancel        │
│ Choose once to acknowledge and move to the next.   │
└───────────────────────────────────────────────────┘
```

Mark a currently valid category and make **Enter** explicitly confirm it. If no category exists, Enter must not silently choose the first category. An invalid/removed category is shown as needing correction and cannot become the implicit Enter choice. Keep all shortcuts in fixed places; a current category can be highlighted without reordering the grid.

Letter keys commit immediately; no second confirmation. Arrow keys and Tab move focus, Enter activates, and pointer selection follows exactly the same path. `/` opens search mode, where typing filters rather than triggers shortcuts. Escape from search first returns to the category grid; Escape from the grid cancels with no mutation and restores editor focus. Handle key-repeat and composition events, and scope the shortcuts to the focused card so they cannot leak into Vim/editor bindings.

Do not reopen the card automatically after advancing. The user looks at the next row and invokes Ctrl+Enter again. This retains the requested gesture and avoids an endless modal loop. A lightweight queue header can show the remaining count; the modal needs no charts, budgets, celebratory animations, or per-row success toast.

### State and edge behavior

| Situation | Required result |
| --- | --- |
| Unchecked row, category key | Replace/insert exactly one category and tick in one transaction, then navigate |
| Unchecked row, `0` | Remove an existing category if present, acknowledge explicitly as unclassified, then navigate |
| Cancel | No text, checkbox, or cursor-position change |
| Checked row, Ctrl+Enter | Reopen in place, retain category, no automatic jump |
| Checked row needs category correction | Explicit **Bank: edit category** opens the same card; preserves acknowledgement and stays in place |
| Row has a flag | Preserve it; acknowledgement does not resolve the flag |
| Invalid row, duplicate category fields, ambiguous identity | Refuse with a specific local message; do not repair silently |
| Busy double press / held category key | One gesture, one edit, one navigation |
| Different note or focus after async work | Never apply to the new cursor or steal focus back |
| Service/configuration unavailable | Keep the bank guard; show an actionable error, with no fallback into ordinary task completion |
| Write succeeded, next-row lookup failed | Keep the successful edit; stay and offer navigation retry; do not replay the write |

The explicit edit-category command is important because current imported rows may already be ticked. Users should not have to reopen and re-acknowledge them merely to improve their reports. Do not retroactively require a classification for every historical acknowledged row.

### Define “next” precisely

Use valid waiting bank rows, not arbitrary unchecked Markdown checkboxes. Skip stubs, code fences, indented notes, ordinary checklists, malformed amounts and rows outside valid day headings. Use the canonical queue order: date, note path, then physical row order within the day.

After a successful acknowledgement, find the next still-waiting row after the origin. Start from fresh data and overlay unsaved bank-editor buffers, so the newly ticked origin is not returned from stale CLI output. Continue across existing month notes when necessary; make the date/month transition visible, unfold the destination, and reveal the actual row. Never create a month note merely to navigate.

Do not silently wrap to earlier rows. At the end, say either **All waiting transactions reviewed** or **No later waiting rows · N earlier remain**, with an explicit **Review oldest** action. Report unavailable data as unavailable, not empty. Keep account balance, stale coverage, unclassified rows and flagged rows separate from this acknowledgement count.

Resolve destinations by unique bank ID where available, rechecking the live row. For ID-less rows, use the captured path, day and exact source text with uniqueness checks; a stale line number alone is never authority. New imports may join the refreshed queue, but no row is acknowledged until it is shown and the user acts on it.

This navigation is a bank-specific flow. It does not advance or rewrite the task `]s` walker. Preserve a jump-back location so the user can return to the acknowledged row.

## Recommended implementation boundary

### Extend the existing services; avoid a parallel review engine

1. **Rust remains the category/configuration/report authority.** Extend `config.rs`, every bank JSON category serializer, and contract fixtures. Keep integer-cent totals and the existing four special category meanings unchanged. No second category catalog in plugin settings.
2. **Bob Ledger Tools owns the review card and pure row-edit planner.** Add a small bank-review fragment and register it in `src/fragments.json`; the existing actions fragment is already large and fragments must stay within the repository's size cap. Reuse the bank source scanner, category catalog, invalidation service and guarded navigation.
3. **Task Status Cycler routes only recognized bank gestures.** Its existing bank branch delegates to a feature-detected bank review API. Keep its standalone guard when Ledger Tools is absent. Never fall through to task completion, successor handling, freshness or recurring-task logic. Advertise the enhanced API capability/version and coordinate compatible deployment.
4. **Editor gestures write through one native editor transaction.** The transaction contains category insertion/replacement/removal and the checkbox change. Do not first call disk-writing `bob bank ack` and then edit the buffer; that creates partial success, autosave races and broken undo. CLI `ack` remains acknowledgement-only in this release.
5. **Route individual card acknowledgement through the same review service.** The default GUI “review this row” action should behave consistently. Preserve existing explicitly named day/batch acknowledgement as a deliberate category-free operation, labeled accordingly; do not surprise a batch user with dozens of dialogs.

A new `bob bank review` command or a new persistent review journal is not necessary for this version. Existing plugins already perform guarded local bank edits and contain a source recognizer. Keep the new local transformation pure and test its output against Rust's grammar; do not duplicate totals or import identity algorithms in JavaScript.

### Guard the edit, not just the modal

Capture origin editor/file, category-catalog generation, day, bank ID when present, exact row text and relevant source context. At commit, re-resolve the origin in the same document and recheck that it is still the same waiting transaction. An unrelated insertion above the row can be tolerated if identity and source still agree; a changed amount, payee, category, date, ID or checkbox must refuse and refresh. An ID duplicated elsewhere is ambiguous, even if one copy remains at the old line.

Validate the chosen category against the current catalog, particularly after `bank.md` changes. A config-generation change should refresh the card and require a new choice rather than reinterpret a keystroke. Preserve all non-owned bytes: money, account, payee, notes, links, flags, children, block IDs and newline style. Insert the field before the trailing note/comment/ID region, not by reparsing and re-rendering the entire row. Refuse multiple `[cat::]` occurrences rather than choosing one silently.

After the editor transaction, invalidate bank views. Read-only CLI reports should refresh after the expected vault save; navigation inside the current note can use the live buffer. For cross-note movement, retain and verify the origin save through the normal editor lifecycle. A save or navigation timeout must not trigger a second acknowledgement.

Within a note, normal undo must restore category and checkbox together. Cross-note navigation changes the active undo stack, so provide an **Undo last review** action that targets the originating document and applies the inverse only if the owned spans and identity still match the successful after-image. If later edits conflict, refuse the inverse with a clear message. Never solve this by restoring a stale whole-file snapshot.

## Critique and explicit adjustments to the request

| Adjustment | Why it improves the proposal |
| --- | --- |
| Merge daily acknowledgement and Monday import into one weekly chore | Both already exist; changing only recurrence duplicates work |
| Keep acknowledgement distinct from classification | Recognition can be complete even when a category is uncertain |
| Offer an explicit Unclassified action | Forced guesses harm reports and train future imports incorrectly |
| Confirm an existing category with Enter | Keeps repeated merchants fast while preserving a review gesture |
| Keep closed-row reopening and category editing separate | Prevents accidental navigation and avoids backfill churn |
| Advance only after successful atomic mutation | Cancel/error cannot lose the user's place or create partial review |
| Cross month boundaries, but do not silently wrap | Handles real imported batches while preserving predictable direction |
| Retain explicit batch acknowledgement outside the guided flow | Maintains existing scripting and catch-up behavior |
| Review broad transfer rules as part of rollout | Categories affect totals, not just appearance |
| Retain weekly staleness checks and independent reconciliation | An empty waiting queue is not proof of current bank coverage |

A weekly cadence is a reasonable response to manual download friction. The original approved plan itself says to reduce categorization if it dominates effort and to reconsider feeds if manual ingestion remains the bottleneck. Try this simpler workflow before expanding into bank-login automation or an aggregator integration.

One accounting limitation deserves prominence: this is currently a **checking-account view**, not a complete household spending model. Card payments classified as transfers can exclude underlying purchases that are not imported anywhere else. Label account coverage honestly. Do not silently add accounts, treat all positive amounts as income, or redefine `transfer` to make a dashboard more attractive. `debt` in the proposed menu is a pragmatic cash-flow bucket, not principal/interest accounting. Choosing a category must not change imported amounts or balance proof.

Automatic categorization is useful as a suggestion. Automatic acknowledgement is contrary to the point of this ritual. Sensitive and ambiguous merchants should remain neutral; no cloud classification, raw export retention in research artifacts, or invented merchant-confidence percentages are needed.

## Verification and rollout

This research did not run the full test suite or a real Obsidian UI session. The following are implementation acceptance checks, not claimed passing tests.

- **Configuration:** old scalar YAML still parses; mixed scalar/object values work; built-in overrides preserve semantics; duplicate/reserved shortcuts and unknown fields produce precise diagnostics; JSON round-trips the optional shortcut.
- **Editing:** selection, cancellation, Unclassified, recategorizing checked rows, reopening, CRLF/BOM, Unicode, links, children, flags, trailing notes/IDs, existing/duplicate category fields, and unchanged amounts/accounts. One undo restores one review.
- **Concurrency:** row inserted above; target moved or deleted; duplicate bank ID; second window changes category/amount/status; config changes while card is open; save timeout; retry after committed write; navigation failure after successful review.
- **Navigation:** checked siblings; ordinary checklists; fenced and indented lookalikes; ID-less rows; invalid day context; final row; earlier waiting rows; month boundary; incoming import; unavailable catalog/queue. Verify one advance per committed review.
- **Integration:** cycler has no task side effects; plugin disabled/outdated states refuse safely; source/Live Preview and individual queue-card actions agree; keyboard shortcuts work with Vim mode, focus, composition, held keys and mouse input; cross-note Undo cannot undo an unrelated row.
- **Financial semantics:** acknowledge alone does not change money totals; category changes alter only their documented report classification; transfer/refund/cash tests remain valid; balances and journal identity remain unchanged; replay of the same QFX preserves reviewed rows.
- **Migration:** exactly one active weekly chore; old completed occurrences unchanged; correct future Monday scheduling; link sign-on and post-login destination manually checked on the Mac; current uncategorized closed rows can be categorized without reopening them.

Extend the existing `test-task-status-cycler-bank-guard.cjs`, bank-actions/source/data/decode/card tests and `test-obsidian-bank-ui-e2e.cjs`, plus Rust bank configuration/grammar/report tests. Use synthetic transactions only. Build fragments and run the repositories' required checks; changes to plugin sources require the normal `bob plugins sync` deployment. Confirm actual GUI behavior on the Mac after deployment, not merely Node harness success.

Deliver in three cohesive increments: **(1)** catalog shortcuts plus the guarded edit/card, **(2)** navigation, recovery and unified GUI routing, **(3)** private configuration and chore migration with updated bank contract/guide and a Mac walkthrough. Ship the matching CLI before plugins depend on its shortcut field. A two-to-four-week trial should assess elapsed review time, forced-Unclassified frequency, correction frequency, and whether weekly coverage remains continuous. These are proposed product measures, not statistics inferred from the private data; no merchant telemetry is needed.

## Recommended solution

Implement **one Monday Bank review task**, linking directly to Wells Fargo's published download sign-on and to Bob's waiting queue. Keep the existing category IDs and bank grammar, add neutral Personal and Debt payments choices, and give the configured menu stable one-key shortcuts. Route Ctrl+Enter through a compact card that commits the category and acknowledgement atomically, then moves once to the next valid waiting row. Make cancellation, Unclassified, reopening, category correction and undo explicit. Preserve independent reconciliation and carefully review transfer suggestions. This addresses the actual toil while keeping the bank record understandable, recoverable, and pleasant to review.
