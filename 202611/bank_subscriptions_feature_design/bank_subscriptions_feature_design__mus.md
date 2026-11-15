# Bank subscriptions album: seeding, auto-link, and check design

Researcher: mus · swarm 5-researcher round · independent report (`__mus`)
Date: 2026-11-15 · workspace: `bob-cli_23`
Question: add a `bank/subscriptions` album, seed it from recent bank history,
auto-link `bob bank import` rows to their subscription record, render that link
beautifully and concisely, and have `bob bank check` propose price changes and
new candidates. Critique the plan and recommend an implementation.

TL;DR: yes, build it — but not as specified. The album idea is sound and the
`discretionary` scope decision is correct. Do not add a required
match-strings field. Instead seed from 13 months with a read-only candidate
report plus human confirmation, auto-link by generalizing the existing
`eat` registry lookup to `subscriptions` (rule link > learned link >
subscription-registry exact match), keep the row link as
`[[subscriptions/<stem>|🔁]]` for grammar consistency plus an Obsidian pill
style for beauty, and implement the two `check` findings as warnings that
propose and never create.

## Sources inspected

- Beads (audited reads): `bob-cli-kt` (subscriptions task, READY, depends on
  `bob-cli-k3`), `bob-cli-kd` (closed bank epic, 7 phases, import landed in
  `kd.4`), `bob-cli-k3` (closed albums epic; registry, `albums create`,
  cutover all landed).
- Plan: `sase/repos/plans/202611/bank_daily_acknowledgment.md`,
  `## Follow-up: the subscriptions album` (~lines 1231–1271) and settled
  requirements ADJ-1–ADJ-8 (~lines 180–210). Reviewer decision
  `subscriptions_scope = discretionary` carried into `bob-cli-kt`.
- Contract: `docs/bank.md` (row grammar ~175–204, naming tiers ~324–373,
  journal/matching/commit ~222–460, findings ~646–691, JSON ~687–770),
  `docs/records.md` (album schema ~385–435, record note shape, `records`
  commands, index facets/grouping ~60–110).
- Code: `src/native/bank/naming.rs:resolve_name` (rule > learned > builtin >
  cleaned), `src/native/bank/import_plan.rs:restaurant_link` (~832–853) and
  `RestaurantEntry::link` (~72–80), `src/native/bank/import_run.rs` (~600–745,
  registry + `eat` folder read with preimage guards),
  `src/native/bank/config.rs:RULE_KEYS` (`match,payee,cat,link`),
  `src/native/bank/suggest.rs` + `src/native/bank/identity.rs:merchant_key`,
  `src/native/bank/model.rs:BankRow`, `src/native/bank/check.rs` +
  `src/native/bank/status.rs` (twins/unmatched/balance findings),
  `src/native/albums/registry.rs` (route resolution, no vault scan in planner).
- Memory (audited): `cli_rules.md`, `docs.md`, `sase_artifacts.md`,
  `glossary:bank-row`, `glossary:bank-month-note`, `glossary:album-note`,
  `glossary:record-note`.

No peer swarm reports were opened or consulted.

## Is a subscriptions album a good idea?

Yes, with the current scope. The bank epic already settled the load-bearing
distinction (plan ADJ-1, `bob-cli-kd` notes): monthly notes hold checkbox
**rows**, not records. Transactions break all four record rules called out in
the plan — an index that rewrites every record on every write, filenames from
titles with collisions refused (`7-Eleven` × 277), `record_checkbox` as an
error, and "one durable thing." Subscriptions pass all four: Spotify is one
durable thing with a stable stem (`subscriptions/spotify.md`), a schema, and
notes. That is exactly what albums are for (`docs/records.md`: "one durable
thing, such as a restaurant"; album stem is folder + capture route).

The `discretionary` scope is also correct and should be kept. Seeding only
keep-or-cancel charges (streaming, apps, memberships, news) keeps the album a
**decision surface** ("does this still earn its keep?") rather than a second
fixed-burn ledger. Mortgage, student loans, car insurance, utilities, and
Kelly's salary stay as bank categories + rules, which is where Bryan already
handles obligations. The rejected `all_recurring + kind` alternative would
bloat the album, complicate the index grouping, and duplicate what categories
already do. If Bryan later wants the full burn view, that is a report query
over bank rows + album, not a second seeding pass.

Two cautions that shape everything below:

1. **Do not turn transactions into records.** There is deliberately no
   `decisions:bank-rows-not-records` record (kd epic decision
   `memory_bank_decision = no`), but the contract is unambiguous:
   `docs/bank.md` says bank rows "never carry `#task`," stay invisible to
   plan/ready/archive/reconcile, and totals are "drawn when shown, never
   written." The subscriptions album must link *from* rows *to* records and
   propose findings; it must never rewrite history, auto-create records from
   imports, or store totals in notes.
2. **Bank data stays out of agent outputs** (plan out-of-scope v1). Any seed
   helper must run locally against Bryan's vault, print evidence-bounded
   diagnostics (file + line + masked merchant, never raw FITIDs or account
   numbers — the same discipline as `import` JSON diagnostics), and keep
   payee strings inside the vault/terminal, not in beads, plans, or research
   artifacts.

## Seeding: review history, then let Bryan confirm

### Window: 13 months, not "a few"

"Last few months" will miss every yearly subscription — exactly the charges
most worth cancelling (Prime, Apple storage upgrades, domain renewals, annual
apps). The seeder needs **at least 13 months** of bank month notes plus the
journal, so a yearly charge appears twice and cadence can be confirmed:

- 13 months catches monthly (≈13 sightings) and yearly (≈2 sightings).
- `report -p all` already spans "the bank's own history, from the earliest
  account `start` or row date" (`docs/bank.md` commands section), so the data
  path exists; the seed helper should reuse `collect_rows` + journal union,
  not a new scanner.
- If the vault only has ~3 months of real imports (bank epic landed
  2026-11-12; `bank.md` hub + `bank/2026-11.md` are young), say so plainly and
  seed from what exists plus `old_recur.md`'s active rows, then re-run the
  candidate pass after 2–3 more imports. Do not fabricate a year of history.

### How to group: reuse `merchant_key`, not raw payees

Bank payees are noisy by design: `PURCHASE AUTHORIZED ON 11/12 ... CARD 4321`,
`SQ *`, `TST*`, `#1234` store codes, city/state spans, and long digit runs
are all stripped or masked before grouping (`naming::clean_description`,
`identity::mask_digits` masking runs of ≥4 digits, `merchant_key` =
clean → mask → lowercase → collapse). The seed pass must group by that same
`merchant_key(text)` (`src/native/bank/identity.rs:46`), or "Spotify,"
"SPOTIFY USA," and "Spotify Purchase 11/12" will look like three merchants.
That function is also what the learned index and the twins detector use, so
reusing it keeps seeding, suggestions, and `check` in agreement.

Proposed grouping (read-only, propose-never-create):

- Inputs: acknowledged + waiting rows with IDs (journal `written`/`matched`)
  plus typed rows with `merchant_key(payee)` fallback; exclude
  `[cat:: transfer]`, `cash`-kind accounts, `income`/`refund`, and
  zero-amount rows — the same exclusions `compute_totals` applies.
- Cluster by `merchant_key`; within each cluster sort by date and compute
  gaps. Monthly ≈ 27–33 days, yearly ≈ 330–400 days (wide on purpose: billing
  drifts, weekends, retries). Require **≥3 sightings for monthly, ≥2 for
  yearly** before proposing, with amount stability (exact cents, or within a
  stated tolerance only for tax-inclusive rows — default exact, Bryan widens
  per record).
- Cross out anything already linked to `subscriptions/*`, anything whose
  merchant maps to an obligation category/rule (mortgage, loans, insurance,
  utilities, salary), and singletons.
- Output one candidate per cluster with evidence: masked merchant, dates,
  amounts, cadence guess, count, and the 2–3 row locations
  (`bank/YYYY-MM.md:line`). Rank monthly-first by annualized cost so the
  keep-or-cancel review hits the big wins first.

### Human confirms; nothing auto-creates

The plan already says "`bob bank check` proposes, never creates" — extend
that to seeding. The correct shape is a **seed-assist command that prints a
paste-ready draft**, not a bulk importer:

- `bob bank subscriptions propose` (or `bob bank check` surfacing the same
  `bank_subscription_candidate` findings; see below) lists candidates with
  evidence. Bryan picks rows, then `bob records new subscription <Title>`
  with `-s amount= -s cadence= -s payee= -s category= ...` writes each record
  through the shared staged writer (index rebuild included, same transaction
  as capture/`records new`). Missing required fields already exit 2 with a
  ready-to-copy draft — reuse that path verbatim.
- Seed `old_recur.md`'s active discretionary rows the same way: one record
  per active row, keep every block ID, then de-zorg into a `legacy_recur`
  notebook under `cash` per the `eat.md` recipe (keep IDs; rewrite or report
  every inbound link). Do not bulk-convert obligations.
- Point `cash.md ^audit-monthly-subscriptions` at the album only after the
  first confirmed records exist, so the chore never points at an empty index.

This keeps the ritual intact: Bryan's explicit gesture creates each durable
thing, automation only finds and files. Fully automatic seeding would mint
records for trials, refunds, family-shared charges, and one-off annual renews
Bryan already cancelled — the exact false-positive set that would teach Bryan
to distrust the album.

## Auto-link on import: generalize the `eat` pattern, don't invent match-strings

### What already exists (and why it matters)

Import already resolves `payee / category / link` through four tiers
(`naming.rs:resolve_name`, `docs/bank.md` naming section):

1. first `bank.rules` entry whose `match` is a case-insensitive substring of
   the raw description (unspecified fields fall through);
2. most recent acknowledged ID-bearing row with the same journal merchant
   (learned; waiting rows never teach);
3. Wells Fargo built-ins (ATM → `cash`, fees, card payments/transfers);
4. cleaned, title-cased description.

Links specifically resolve as **rule link > learned link > restaurant
registry exact match** (`naming.rs:89–91`). The restaurant lookup is
deliberately narrow (`import_plan.rs:restaurant_link`): exact
case-insensitive title match against the cleaned merchant core, ambiguous
titles omitted, no fuzzy guessing, no record mutation, no full-vault scan —
the planner consumes a pre-read `Vec<RestaurantEntry>` built once in
`import_run.rs` with read guards and `DiscoveryHealth` handling. Learned
links then carry forward: once Bryan acknowledges a linked row, every future
import of that merchant inherits the link via tier 2 with zero config.

That is the machine to reuse. Three designs were considered:

| Design | How it links | Verdict |
|---|---|---|
| **A. Required `match` list field** (user's sketch: album requires list of strings to match rows) | import reads each subscription's match strings, substring-matches raw descriptions | Reject. Duplicates `bank.rules`, splits truth across two files, substring matching over vault-authored strings is fragile (`APPLE` hits hardware, App Store, and Apple TV at once), required-field forces every record to invent matchers, and it bypasses the learned tier that already solves carry-forward. |
| **B. Rules-only** (`bank.rules: [{match, link}]` per subscription) | hand-maintained rules point at `[[subscriptions/x\|🔁]]` | Works but does not scale and drifts: every new subscription needs a hand rule, renames break links, no registry to validate against. Keep as the explicit-override tier, not the system. |
| **C. Subscription registry lookup + learned carry-forward (recommended)** | import reads `subscriptions/` titles + `payee`/`aliases` fields once (same guarded pattern as `eat`), exact normalized match; tier order rule > learned > subscription registry | Adopt. One source of truth (the record), no new config surface, reuses proven guards, learned tier makes the second charge free. |
| **D. Cadence+amount-aware matcher** | match on merchant + ~30d gap + same cents at import time | Reject for v1. Elegant but brittle: trials convert, prices change, promos and family plans vary cents, yearly has one data point. Cadence belongs in `check` (which sees history), not in the single-transaction import planner. |

### Recommended link-resolution order

Keep the existing four-tier shape and slot subscriptions in as the
generalized registry tier:

1. explicit `bank.rules` `link` (highest; Bryan's manual override, preserved
   byte-identically on matched rows per Ownership rules);
2. learned link from the most recent acknowledged ID-bearing row with the same
   `merchant_key` (this is what makes the feature feel automatic after the
   first ack — no per-merchant config);
3. subscription-registry exact match (new; replaces the `eat`-only special
   case with a per-album lookup that starts with `eat` + `subscriptions`);
4. no link (lowest; never guess).

Registry matching rules (mirror `restaurant_link`, tighten slightly):

- Candidate keys per record: normalized `title` **and** normalized `payee`
  field **and** each normalized `aliases` entry (new optional list field, see
  schema). Normalize with the same pipeline as merchants
  (clean → mask → lowercase → collapse) so "Spotify USA" and "spotify" meet
  in the middle.
- Exact normalized equality only; on ambiguity (two records claim the same
  key) emit no link and surface a `check` warning naming both records.
  Never substring-match from the registry — that is what `bank.rules` is for.
- Read the `subscriptions/` folder through the same guarded path as the
  restaurant folder (`import_run.rs` pattern: snapshot folder listing before
  and after, per-record preimage deps, `DiscoveryHealth::Partial` refuses
  with `bank_import_registry`). A damaged album degrades to "no subscription
  links this run" with a bounded warning, never a refused import — imports
  must not fail because an album note has a YAML typo.
- Preserve the Ownership invariant: import writes the link only on **new**
  waiting rows; on a matched typed row it appends only `^bank-<hex>` and
  leaves checkbox, wording, fields, links, notes, and children byte-identical
  (`docs/bank.md` Ownership). A matched row never gains, loses, or rewrites a
  subscription link.

### Schema: `payee` + optional `aliases`, not a required match list

The user's instinct (the album should own its match keys) is right; making it
a **required list of match strings** is the wrong shape. Required forces every
record through a matching-theory exercise, invites overlapping substrings,
and creates a second rule engine beside `bank.rules`. Instead:

```yaml
record:
  noun: subscription
  fields:
    status: {required: true, values: {to_cancel: "✂️ To cancel", active: "💚 Active", cancelled: "🚫 Cancelled"}}
    amount: {required: true, values: number, min: 0}
    cadence: {required: true, values: {monthly: "Monthly", yearly: "Yearly", quarterly: "Quarterly", weekly: "Weekly"}}
    payee: {required: true, suggest: true}      # canonical bank-row payee
    aliases: {list: true, suggest: true}        # optional variants ("Spotify USA", "SPOTIFY")
    category: {suggest: true}
    renews: {values: date}
    url: {values: url}
```

Why this shape:

- `payee` required gives the registry exactly one canonical key per record
  with no new field kind — it is already the string import writes into rows,
  and `suggest: true` surfaces existing values in pickers (the records field
  table: `suggest` "allow existing values to be offered as suggestions").
- `aliases` optional list absorbs real-world variant spellings without
  forcing every record to have one. Empty optional list fields write nothing
  (`docs/records.md`), so simple records stay simple.
- `cadence` should include `quarterly`/`weekly` alongside monthly/yearly;
  the plan's two-value set will misfile real charges (quarterly domains,
  weekly transit-adjacent passes that are discretionary). Choices stay
  exact-key, so adding two keys costs nothing.
- Keep plan's `index_facets` under review: with `status` as the group field,
  the default facet order (other choices then suggests, capped at three)
  already yields `[cadence, category, payee]`-ish rows. The plan's explicit
  `[amount, cadence, category]` puts a high-cardinality number first, which
  reads as noise in the generated `[!records]` callout. Prefer
  `[cadence, category, amount]` or omit explicit facets and accept the
  default — numbers render plain and empty values disappear either way.

## Rendering: concise in the row, rich on hover/cards

### The row itself: keep `[[subscriptions/<stem>|🔁]]`

The bead/plan link form (`[[subscriptions/<stem>|🔁]]`) is correct for the
Markdown row and should be kept. Reasons:

- It follows the established `eat` pattern exactly
  (`- [x] $13.71 Smashburger ... [[eat/smashburger|🍽️]] ... ^bank-…`):
  payee text already names the merchant, the tail wikilink is a click target
  plus a machine-readable identity, emoji-only alias keeps the row to one
  extra token. Row grammar explicitly allows wikilinks "in any order" in the
  tail, so no grammar change is needed.
- Alternatives are worse: `[[subscriptions/spotify|Spotify]]` duplicates the
  payee and bloats every row; `[[subscriptions/spotify|🔁 Spotify]]` is
  friendlier but doubles the link width across hundreds of rows and breaks
  visual rhythm with `eat` rows; status-emoji aliases (`💚`/`✂️`) would make
  the row lie when status changes without rewriting history (and import never
  rewrites rows).
- The "every link looks identical" objection is real but misplaced at the
  row layer: `eat` rows already share 🍽️-family glyphs and read fine because
  the payee carries identity. The link's job in the row is affordance +
  identity for tooling, not a second label.

Beauty therefore belongs one layer up, not in the row bytes:

- **Obsidian style**: render `subscriptions/*` links in bank month notes as a
  pill/badge (🔁 on a tinted background, hover shows the record title +
  amount + cadence). That is the same technique as the bank month/queue cards
  and the Category card — color and shape carry the beauty, row bytes stay
  stable and greppable. No new grammar, no per-row cost, works for both
  `eat` and `subscriptions` links with different tints.
- **Terminal**: `bob bank list/report` human output already renders categories
  as `emoji + label`; render a subscription link as a trailing `🔁` marker
  (one glyph, colored when color is on, honoring `NO_COLOR`/pipes). JSON keeps
  the full `links[]` array unchanged — scripts and the Mac app need the real
  target, not the glyph.
- **Mac Capture / cards**: pass the link through in row JSON (`links`,
  `suggestion`) exactly as today; presentation (tap target, subtitle with
  record amount) lives in the client, per
  `decisions:mac-capture-is-a-thin-client`.

### What "concise" must survive

- Rows are walked with `]b`/`[b` and filed with Ctrl+Enter; trailing-clutter
  discipline matters. One `[[...|🔁]]` token preserves the walk rhythm.
- `check` and totals ignore links (only `cat`/`acct` affect money), so the
  link is inert for accounting by construction — verify with the existing
  `bank_row_*` finding suite plus a new assertion that linked vs unlinked
  twins of the same cents produce identical totals.

## `bob bank check`: two findings, both proposals, neither errors

Both findings from the plan are worth building, with narrowed triggers and
explicit severities so `✓ balanced` keeps its meaning (balance verdicts come
from the ledger-balance/journal phase; subscription findings must not flip
them to error).

### `bank_subscription_price` — linked row amount ≠ record amount

- Trigger: a bank row carrying a `subscriptions/*` link whose absolute cents
  differ from the record's `amount`. Compare exact integer cents; do not
  prorate yearly÷12 and do not net tax separately — the record's `amount` is
  "what the charge shows up as," taxes and fees included (document this on
  the album or the field help so Bryan files the posted figure).
- Severity **warning** (money disagrees with memory — worth a look, not a
  broken vault). Message names both figures and both locations, e.g.
  `Spotify $11.72 → $12.99 (bank/2026-11.md:42 vs subscriptions/spotify.md)`.
  Hint: update the record (`bob records update subscription spotify
  -s amount=12.99`) or flag if the increase was unannounced.
- Edge handling: yearly records match only yearly-amount rows (a $129.99
  yearly row must not fire against a $12.99 monthly memory); currency is
  single-currency by contract; `cancelled` records with new linked rows fire
  once as "charged after cancel" (same code, distinct message) — that is the
  highest-value alert in the set.
- Never auto-update the record. The record is Bryan's memory; the row is the
  bank's fact. `check` reconciles attention, not values.

### `bank_subscription_candidate` — 3+ unlinked charges on a cadence

- Trigger (all required): ≥3 posted charges sharing one `merchant_key`, no
  `subscriptions/*` link on any of them, gaps within monthly (27–33d) or
  yearly (330–400d) tolerance, amounts stable (exact or within a documented
  epsilon), spanning the 13-month window, and merchant not excluded by an
  obligation rule/category. Fewer than 3 (2 for yearly with a 13-month span)
  is `info` at most — two dinners at the same place are not a subscription.
- Severity **warning** for 3+ monthly / 2+ yearly with stable amounts,
  **info** for weaker patterns. Message shows the evidence that would justify
  a record: merchant, dates, amounts, cadence guess, annualized cost.
- Dedupe against existing records by registry keys before firing (a linked
  record with a renamed payee must not also fire as a candidate — that is a
  `bank_subscription_price`/alias-hint, not a candidate).
- Cap output: rank by annualized cost, bound the list (top N + "and K more"),
  and keep each finding to one line + hint. A candidate sweep that prints 40
  warnings will be ignored; one that prints the top 5 expensive unknowns will
  be acted on.

Both findings are read-only (`check`/`list`/`report` never write vault bytes,
index, or HEAD) and JSON-stable: extend the existing `findings[]` envelope
(`code, severity, path, line, message, hint`) with the two new codes and
document them in the `docs/bank.md` findings table. No new exit-code branch:
warnings keep exit 0 for warning-only runs per the current contract.

## Recommended solution (phased)

**Phase 0 — Seed assist (local, read-only).**
Build the candidate report over 13 months + journal (`merchant_key`
clustering, obligation exclusions, price-stability + cadence tolerances,
annualized-cost ranking). Ship as `bob bank check`'s
`bank_subscription_candidate` findings plus an optional
`bob bank subscriptions propose -f human|json` view for the initial bulk
pass. Bryan confirms each; `bob records new` writes them. Seed
`old_recur.md` actives the same way, then de-zorg to `legacy_recur/`.

**Phase 1 — Album.**
`bob albums create bank subscriptions -n subscription -s "Everything that
charges us on repeat, and whether it still earns its keep."` (parent `bank`,
emoji 🔁). Schema per above: `status` choices with actionable group first,
`amount` number required min 0, `cadence` choices incl. quarterly/weekly,
`payee` required suggest, `aliases` optional list suggest, `category`
suggest, `renews` date, `url`. Revisit `index_facets` to
`[cadence, category, amount]` or default. Point
`cash.md ^audit-monthly-subscriptions` at the album once seeded.

**Phase 2 — Import auto-link.**
Generalize the `eat` registry read to `subscriptions` (titles + `payee` +
`aliases`, exact normalized match, ambiguity → no link), tier order
rule > learned > subscription-registry, new-rows-only per Ownership, guarded
reads with degrade-to-no-link on damaged albums. No required match-strings
field, no new config surface. Existing learned behavior then carries every
repeat charge automatically after its first ack.

**Phase 3 — Check + presentation.**
`bank_subscription_price` (warning, exact-cents, yearly-aware,
charged-after-cancel variant) and `bank_subscription_candidate` (warning/info
per strength, top-N ranked, propose-never-create). Row bytes stay
`[[subscriptions/<stem>|🔁]]`; beauty ships as Obsidian pill styling +
terminal `🔁` marker + client tap targets. Extend `docs/bank.md` findings +
JSON docs, `docs/records.md` album example, and the guide
(`guides/acknowledge-bank-transactions.md`) chore note; run `just docs-gen`
+ `just docs-check`.

## Adjustments to the stated requirements

1. Window is **13 months minimum**, not "a few" — yearly charges are the
   point. Call this out in the bead before closing.
2. **No required match-strings field.** `payee` (required) + `aliases`
   (optional list) own matching with strictly less machinery and no second
   rule engine. If the lead prefers an explicit name, `aliases` is the name —
   not `match`, which collides with `bank.rules.match` semantics.
3. `cadence` gains `quarterly` (+`weekly`); `index_facets` should be
   `[cadence, category, amount]`, not `[amount, cadence, category]`.
4. Link form stays `[[subscriptions/<stem>|🔁]]` (grammar-consistent,
   concise); visual distinction ships via styling, not longer aliases.
5. Both `check` findings are **warnings/info that never create or update** —
   hold the plan's "proposes, never creates" line through implementation and
   keep them out of the balance verdict.

## Risks and open questions

- Thin history: with bank import only weeks old, the first candidate pass
  will be recall-poor. Mitigate with `old_recur.md` seeding + a scheduled
  re-pass after 2–3 imports.
- Variant spellings ("Spotify" vs "Spotify USA PBC") will miss exact match
  until Bryan adds an alias or acks once (learned tier covers the second
  occurrence). Acceptable: one manual ack per merchant is the existing
  learning contract, documented in tier 2.
- Price-change vs promo: trials and intro pricing will fire `price` findings
  on their first full-price charge. That is working as intended — the hint
  should say "expected if a trial converted."
- Scope pressure: yearly obligations will lobby for inclusion. Hold
  `discretionary`; if Bryan wants the full burn, build it as a report, not
  as album membership.
