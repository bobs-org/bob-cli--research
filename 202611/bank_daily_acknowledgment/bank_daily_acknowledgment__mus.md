# Bank album: should daily transactions become an album, and if so what shape?

- Researcher: mus (`__mus` report in 5-researcher swarm)
- Date: 2026-11-11
- Question: Bryan wants to track bank transactions daily again and proposes a new
  `bank` album. Lead the design so it is intuitive, reliable, and beautiful.
  Critique the plan, adjust requirements where justified, and recommend a solution.
- Context read for this report:
  - `sase bead read bob-cli-k3` (epic), `bob-cli-k3.2/.4/.5/.10` phases, and
    `plan:202611/album_and_record_notes.md` via `sase artifact read`
  - `docs/records.md` (album + record contract, schema kinds, capture, filename rule)
  - Vault via `bob query`: `cash.md` (area), `bob.md ^bank-records` and
    `cash.md ^daily-bank-records-again`, one `@BANK` sample
    (`2024/20241226_habit.md ## @BANK`)
  - `research:202611/album_and_record_notes/album_and_record_notes.md` (lead research)
- Status constraint: the k3 epic is `IN_PROGRESS` (album-model closed, album-records /
  album-index / album-catalog / mac / cutover / ledger-mining still open). Any new
  `bank` album must wait for that epic. Do not create it now.

## Bottom line

Build a `bank` album — but **not** as one-record-per-transaction. That literal reading
of "acknowledge every transaction" is the wrong schema for the album machinery Bryan
just approved, and it would make the daily habit harder, not easier.

Recommended shape:

1. **`bank.md` under `[[cash]]` is a payee album** (one record per merchant / source,
   eat-style), not a transaction ledger. Stem `bank`, folder `bank/`, noun `payee`
   (or `merchant` — see §5). Transactions stay where they already work: one-line
   `## @BANK` entries in the daily habit note, plus dated notes under the payee.
2. **Daily acknowledgment stays a review habit, not a capture-every-field chore.**
   Keep the existing `^daily-bank-records-again` scheduled task and the `@BANK` line
   format. Add one Base (`bank.base`) filtered by month/payee for the "structured
   view", and let the album index answer "where does money go?" while the daily note
   answers "what happened today?".
3. **Only graduate to transaction records if/when CSV import exists.** Manual
   per-transaction records at 5–10 lines/day (~2,000–3,000 files/year) break every
   property that makes albums beautiful: titles, filenames, index grouping, capture
   friction, and git noise. If Bryan later wants queryable amounts, build import first,
   then revisit — do not hand-type a ledger into `bank/`.

If Bryan insists that "structured view of this data" must mean queryable amounts from
day one, the fallback is a **monthly-statement album** (one record per account-month),
not a transaction album. Details and why in §6.

## 1. What Bryan actually asked for

From `bob.md ^bank-records` and `cash.md ^daily-bank-records-again`:

- `bob.md:26`: "Use records to start tracking bank transactions again!"
  (`starts after [[#^record-h2-sections]]`, linked from `cash#^daily-bank-records-again`).
- `cash.md:80`: "Go through bank records every day again!" (Keep link, currently
  scheduled 2026-12-01, P2 decay lane). This is a lapsed habit being revived, not a new
  habit being invented.
- Motivation in the prompt: acknowledge every transaction/deposit, stay aware of
  spending, and get an "excellent, structured view" via an album.

So there are two jobs tangled together: (a) a **daily review ritual** (look at the bank,
acknowledge each line), and (b) a **durable catalog** (structured, beautiful,
browsable). An album is excellent at (b) and mediocre at (a). The design must serve
both without making (a) pay (b)'s data-entry tax every day.

## 2. What exists today

### 2.1 The `@BANK` event log already works

Sample (`2024/20241226_habit.md`, lines 38–47):

```markdown
## @BANK
- 241226#1T 13.00  ([[eat#sworld]]) ^z-241226-1t
- 241226#1U 13.00  ([[eat#sworld]]) ^z-241226-1u
- 241226#1V 13.99  ([[old_recur#^z-241128-0n|recur_youtube]]) ^z-241226-1v
- 241226#1W 200.00 (xmas cash for %nikki and %trisa) ^z-241226-1w
- 241226#1X 18.27  (711) ^z-241226-1x
- 241226#1Y 63.50  (w) ^z-241226-1y
- 241226#1Z 3.00   (w) ^z-241226-1z

- 241226#1a total: 324.76 / 1198.76 ^z-241226-1a
```

Properties: one line per transaction, amount first, payee as link or parenthetical,
dated block IDs, daily total line. The lead album research found **694 more
`[[eat#<lid>]]` links, 657 of them dated spending lines in 323 daily `_habit.md` notes
(2024-02 to 2025-12), 653 mappable to a restaurant record** — i.e. Bryan already ran a
daily spending ledger for ~2 years inside habit notes. Phase `bob-cli-k3.10` mines that
ledger once to backfill restaurant `visited` dates. That mining is explicitly one-shot:
the research says "Event series (meals, listens, spending) would need their own model.
The ledger finding is the only event data here, and Phase 4 mines it once instead of
building one."

A transaction album would reverse that settled scope and build the event-series model
the epic deliberately deferred.

### 2.2 The album machinery being built (k3)

- Album note: vault-root `bank.md`, `type: "[[album]]"`, `parent: "[[cash]]"`, top-level
  facts + one nested `record:` schema. Stem = folder = capture route (`bank/` and
  `@bank/`). No nested albums, owner must be an area/project (`cash` is an area —
  good).
- Record note: `type: "[[record]]"`, `parent: "[[bank]]"`, lives in `bank/`. Invalid
  records stay visible; broken album refuses only its own route.
- Index: generated grouped `[!records]` callout, pure function of frontmatter through
  closing `---`. Group field is `status` choices when present, else first choices
  field, else flat list. Sub-groups via `index_by` only when a group has >12 rows and
  ≥2 distinct values. Facets capped at 3. Empty album shows a teaching line.
- Catalog: one stable `[!albums]` row per album in the owner's `## Albums`, placed
  after `## Notebooks`. Counts/backlog/freshness drawn by the plugin, never written.
- Capture: `Name @bank/` creates, `@bank/stem` updates, first-level `key:: value`
  bullets set fields, other bullets become notes. Bare `Blaze @bank` is a teaching
  refusal. `dated_notes: true` dates each first-level note bullet.
- Registry: vault-aware, album-wins over config, per-album isolation, file+line+keypath
  diagnostics. `bob albums list|check`, `bob albums sync` + nightly step (planned).
- Field kinds available: text (default), choices mapping, `date`, `link`, `url`,
  `number` (with `min`/`max`), lists, `required`/`suggest`/defaults. Reserved field
  names: `parent`, `type`, `title`, `created`.
- Filename rule: NFKD → `&`→`and` → drop apostrophes → non-alnum runs to `_` →
  lowercase. Collisions refused, never suffixed. Explicit `-S/--stem` only for empty
  stems or curated names.

Current scale for calibration: eat 104, podcasts 15, tv 23, movies 10. `bob records
check` is green today (0 errors). `bob albums list` reports no albums yet (pre-cutover).

## 3. Is a bank album a good idea?

Yes — with the payee reading. Ranked reasons:

1. **Every collection should reach an area.** Nothing in `cash.md` says a transaction
   log exists. A `bank` album under `[[cash]]` with a `## Albums` row fixes that the
   same way `eat → body` does. This is the epic's core win and it applies cleanly.
2. **Schema/data co-versioning.** If Bryan formalizes payees (category, default
   account, links to subscriptions), that schema belongs in `bank.md`, not chezmoi.
   Same drift argument as `companions`: one vault commit, one `bob albums check`.
3. **The lookup moment is real.** "That charge from Clark — what was it?" is the same
   question as "that place in Clark." A grouped payee index plus a month-filtered Base
   answers it. The prior "record notes data unlock" finding applies.
4. **It preserves the daily ritual instead of replacing it.** A payee album does not
   ask Bryan to type five fields per coffee. The `@BANK` line stays one line; the
   payee's dated note is appended by the same capture that creates/updates the payee.

Limits built into the recommendation (mirroring the lead research's limits):

- **A payee is not a transaction.** One file per merchant, many dated notes per file.
  Amounts inside notes are not queryable frontmatter — accepted deliberately for v1.
- **An album is not a Root Parent, Ready lane, review item, or task home.** Bank
  records hold no tasks. `Blaze @bank` refuses and teaches `@cash`, exactly like eat.
- **Ownership is one dimension.** A payee (e.g. Amazon) spans categories. One canonical
  payee record under cash; categories, links, and relations express the rest. Never
  duplicate a payee per category.
- **No bank credentials in the vault.** The album stores what Bryan typed, never
  scraped balances, tokens, or full account numbers. See §8 privacy.

## 4. Why one-record-per-transaction fails the beautiful/reliable/intuitive bar

This is the plan's biggest risk, so it gets its own section. Suppose `bank/` held one
file per transaction with `noun: transaction`:

| Album property | What transactions do to it |
| --- | --- |
| Titles | Meaningless. `Wawa 2026-11-11 3.50` vs `Wawa 2026-11-11 18.27` — the title is a synthetic key, not a name. The index becomes a phone bill. |
| Filenames | Collision-adjacent. The filename rule refuses duplicates instead of suffixing. Two same-payee same-day amounts need curated stems (`-S`) every time or a timestamp-in-title hack. Daily capture turns into stem bookkeeping. |
| Volume | ~5–10/day → 2,000–3,000 files/year. Largest album today is 104. Ten years of transactions is 20k+ files in one folder; every `bob albums sync`, Base render, git status, and phone sync pays it. |
| Index grouping | Wrong tool. Group field is `status` choices (or first choices). Time series want grouping by month, sorting by date+amount — neither exists. A flat 2,000-row bullet list with `index_by: payee` sub-groups (>12 rows) is not skimmable and rewrites on every capture. |
| Capture friction | Today's `@BANK` line is ~15 keystrokes plus amount. A transaction record needs `date`, `amount`, `payee`, `category`, `account` (+ `status` for review) — five `key:: value` bullets or five `-s` flags. At 8 transactions/day the ritual dies within a week. Bulk `%t` templates help little because each row still needs categorization. |
| Reliability | Amounts hand-typed with no reconciliation. No balance check, no duplicate detection across `@BANK` lines vs records, sign-convention risk (is a refund negative or a separate status?). One typo is a wrong ledger with no bank truth to diff against. |
| Git noise | Every coffee is a commit-sized file creation plus an index rewrite plus a catalog freshness change. `vault-sync` and mobile sync carry thousands of tiny files. |
| Privacy | Amounts in plaintext git history forever, synced to every host. Payee names alone are less sensitive than dated amounts. Either is committed, but transaction amounts are the more scrapeable half. |

None of this means queryable amounts are never wanted. It means the album is the wrong
first vehicle: **import (bank CSV) must precede transaction records, not follow them.**
Hand-typing a ledger to earn a structured view inverts the economics — the view should
come from data Bryan already has (the CSV he downloads to "go through bank records"),
not from retyping it.

### Approaches rejected (and why)

| Alternative | Verdict |
| --- | --- |
| Transaction-per-record from day one | Rejected for v1 (§4 table). Revisit only with CSV import + monthly archiving + amount/date index support. |
| Statement-per-record as v1 | Viable fallback (§6), but awkward: transactions become unstructured bullets again, just under a different parent. Only choose if Bryan demands frontmatter amounts without per-transaction files. |
| Keep schema in chezmoi `records:` | Rejected by the whole epic. Any new kind must be an album from birth; no new `records:` blocks. |
| Make `bank.md` a sub-area or notebook | Rejected. Sub-area drags in Tasks/Ready/Stats; notebook members are bullets with no schema. Payee validation, capture routes, and counts all need album semantics. |
| Nested albums (`bank` per account) | Rejected for v1. No nested albums in the contract; owner must be `cash` directly. Multi-account is a `account` choices field, not a folder tree. |
| Bases/Dataview only, no album | Keeps the ritual but repeats the pre-k3 sprawl (config-less collection with no schema home, no capture route, invisible to git/agents/mobile the way hand lists are). The payee album costs one note and buys the schema home. |

## 5. Recommended design: `bank` payee album under `cash`

### 5.1 Identity

- Album note: `bank.md` at vault root. `parent: "[[cash]]"`, `type: "[[album]]"`.
- Folder + route: `bank/` and `@bank/`, by stem. No `dir:` key (derived).
- Noun: `payee` (preferred) — "one payee", CLI/JSON `"type": "payee"`, capture
  `Name @bank/`. Alternative `merchant` is warmer but excludes income sources,
  transfers, and people (`%nikki` Christmas cash, `w` withdrawals). If Bryan wants
  person-to-person transfers first-class, `payee` covers both; `merchant` does not.
  **Adjustment: do not use noun `transaction`, `bank`, or `entry` — all collide with
  the folder stem, reserved ids, or plain language ("bank" is the album, not the row).**
- Owner chain: `bank → cash → area`. Cash is already an area, so no `mind.md`-style
  blocker like podcasts had.
- Emoji: `🏦` (album row, capture-targets, Record Card). Distinct from `💰` noise.

### 5.2 Schema draft (minimal v1, `bob albums create`-shaped)

```markdown
---
parent: "[[cash]]"
type: "[[album]]"
summary: People and places money goes to or comes from.
emoji: 🏦
index_by: category
record:
  noun: payee
  label: Payee
  dated_notes: true
  fields:
    status:
      required: true
      values:
        active: 🟢 Active
        inactive: ⚪ Inactive
    category:
      required: true
      suggest: true
    account:
      suggest: true
    url:
      values: url
---

# Bank

Places and people money goes to or comes from. Add one with `Name @bank/`.
Browse and sort in [[bank.base]].

## Records

> [!records] No payees yet
>
> Add one with `Name @bank/`.
```

Why this shape:

- `status` (choices, required) gives the index its actionable-first grouping for free:
  `🟢 Active` leads, `⚪ Inactive` trails — same grammar as eat's `🔖 To try` first.
  No `needs_review` group is needed because review lives in the daily habit, not the
  catalog.
- `category` (required, suggest) is the `index_by`. Groups >12 rows sub-group by
  category display text (`Groceries`, `[[nj_towns…]]`-style links fold like eat
  locations). Small groups stay flat with category as facet.
- `account` (optional suggest, e.g. `Chase checking`, `Amex`) records the default
  instrument without forcing per-transaction bookkeeping. A choices mapping is
  premature — Bryan's accounts change; `suggest: true` learns them.
- No `amount`, no `date`, no `balance` fields on the payee. Amounts live in dated
  notes (`- 2026-11-11: $13.00 coffee`), exactly like eat's `- 2026-11-08: Spicy tuna…`
  notes. This is the deliberate v1 ceiling that keeps record count at payee scale.
- `dated_notes: true` is required — it is what makes `@bank/wawa` updates append
  `- YYYY-MM-DD: …` notes.
- `index_facets` omitted in v1 (default: other choices + suggest fields, capped at 3).
  With this schema the default facet is `account` — one glance wide. Add explicit
  `index_facets: [account]` only if a second suggest field ever appears.

What v1 does NOT include (and why): `visited`-style last-paid date (derivable from
notes; backfill only if ledger mining proves worth it), `amount` totals (needs
structured notes — deferred to import), `companions`-style list fields (the exact
field just deleted across 137 records — do not reintroduce list-link defaults).

### 5.3 Capture UX (intuitive = one line stays one line)

Create: `Wawa @bank/` + `- category:: Groceries` (+ optional `- account:: …`, note
bullet `oatmeal`). Update (the daily path): `Wawa @bank/wawa` with parent text as the
dated note (`13.00 coffee`) — same updater semantics as `@eat/ramen_nagi`. The `@BANK`
habit line and the payee note are written by the same draft where convenient, but
neither requires the other: a cash-only transfer (`w` withdrawal) needs no payee.

Bare `Wawa @bank` (no trailing slash) refuses with `album_holds_no_tasks` and teaches
`@bank/` vs `@cash` — same contract as eat. This matters more here than for restaurants
because `@bank` will be typed constantly during review; the refusal is the guardrail
that keeps tasks out of the catalog.

Bulk path for seeding: `%t` template over the existing `@BANK` payee strings
(`w`, `711`, top 20 merchants from the 2024–2025 ledger) to create the first ~30
payees in one reviewed batch, then categorize over the first week of use. Do not
pre-create hundreds — `suggest` learns faster than Bryan can type a taxonomy.

### 5.4 Rendered index (beautiful = eat grammar, cash hue)

```markdown
## Records

> [!records] 47 payees · 🟢 41 active · ⚪ 6 inactive
>
> - **🟢 Active** · 41
>   - **Groceries** · 8
>     - [[bank/wawa|Wawa]] — Amex
>     - …
>   - **Dining** · 14
>     - [[bank/ani_ramen_house|Ani Ramen House]] — Chase checking
>     - …
>   - …
> - **⚪ Inactive** · 6
>   - [[bank/old_gym|Old gym]] — Chase checking
```

Same reader questions as eat: how big (47 payees), what needs attention (active set),
find one thing (category sub-groups, title-sorted rows), what did we think (one click
to the payee's dated notes). The `.base` stays as the sort/filter tool, linked from the
intro — index for glancing, Base for slicing by month.

### 5.5 Owner catalog row in `cash.md`

One stable row under `## Albums` (engine-placed after `## Notebooks`):

```markdown
## Albums

> [!albums]
>
> - 🏦 **[[bank|Bank]]** — People and places money goes to or comes from.
```

Counts (`47`), lead-group peek (`🟢 41 active`), and freshness (`last added 2d`) are
plugin-drawn chips, never written — same split as notebooks. No amounts, no dates, no
balances are ever written into `cash.md`.

## 6. Fallback if Bryan demands queryable amounts in v1

If "structured view" must mean `amount` as a number field from day one, choose a
**monthly-statement album**, not transactions:

- Noun `statement`, one record per account-month (`title: "2026-11 Chase checking"`,
  explicit `-S 2026-11-chase-checking` stems to dodge the filename normalizer).
- Fields: `account` (choices), `month` (date, first-of-month), `status`
  (`open`/`reconciled`), `opening`/`closing` (number, optional), notes carry the
  transaction lines.
- Pros: 12–36 records/year, natural reconcile unit, balances have a home.
- Cons: transactions still unstructured; month stems are synthetic; index groups by
  `status`, not time, so history browsing still needs the Base. It is a better ledger
  than transaction-per-record but a worse catalog than payees.

Do not ship both albums in v1. Two bank albums (payees + statements) double the
taxonomy before either is proven. Pick payees; add statements only after one quarter
of payee use shows reconciliation needs a home.

## 7. Implementation order (waits for k3)

1. **Gate: k3 cutover + `records:` retirement.** New album must be born album-native
   (`type: [[record]]`, `record.noun: payee`). No chezmoi block, no type stub
   (`payee.md` must never exist as a sibling — the A3 lesson).
2. `bob albums create bank --parent cash` (or hand-write `bank.md` per §5.2), then
   `bob albums check`, `bob albums sync`; verify `cash.md ## Albums` row, `bank.base`
   filter (`file.inFolder("bank")`, `note.type == link("record")`), capture
   create/update, bare-route refusal, broken-schema isolation.
3. Seed top payees from the 2024–2025 `@BANK` lines in one reviewed commit (bulk
   template, §5.3). Backfill nothing else — no `visited` mining for payees unless
   k3.10's restaurant backfill proves the script reusable.
4. Plugin + Mac follow the existing k3 phases: `[!records]` card styling, count/peek/
   freshness chips from `bob albums list -f json`, debounced sync; Mac shows album
   title/owner/summary in capture-targets and names the payee in previews.
5. Docs: `docs/records.md` contract already covers albums; add the bank worked example
   only (no new contract), plus `cash.md` catalog screenshot if the docs gate wants it.
   Run `just docs-check`.

## 8. Risks and open questions

- **Privacy.** Amounts + payees + dates in plaintext git, synced to three hosts and
  (via vault-sync) potentially remotes. Payee names alone already leak lifestyle; dated
  amounts complete the picture. Mitigations: never store account numbers, never store
  CSV balances verbatim, keep the vault's existing git-sync exclusions audited, and
  decide explicitly whether `bank/` is excluded from any shared/public export before
  seeding. Flag, do not solve, in this research.
- **Reconciliation has no home in v1.** Deliberate. If Bryan finds month-end drifting,
  that is the trigger for the statement album (§6), not a reason to bloat payees.
- **Sign convention.** `@BANK` lines today mix spending (`13.00`), totals, and cash
  (`200.00 xmas cash`). If amounts ever become frontmatter, decide once: positive =
  outflow, negative = inflow (or separate `direction` choices?) and document it in the
  schema card. Undecided for v1 because amounts are notes text.
- **Noun bikeshed.** `payee` vs `merchant` vs `counterparty`. `payee` recommended
  (§5.1) because it covers people and refunds. If Bryan hates it, `merchant` is the
  only alternative that survives pluralization (`merchants`); `counterparty` is precise
  but cold.
- **Volume tripwire.** If `bank/` exceeds ~300 payees, the category taxonomy failed
  (duplicates, one-off cash lines promoted too eagerly). Fix by merging, not by
  sharding — no second bank album, no per-year folders.
- **What "acknowledged" means.** Define done for the daily task: every `@BANK` line has
  a payee link or explicit `(cash)` marker + the daily total line exists. That keeps
  `^daily-bank-records-again` checkable without per-transaction records.

## 9. Requirement adjustments (explicit)

- **A: new album approved in principle, payee-shaped** — not transaction-shaped. The
  prompt's "bank album" survives; its grain changes from ledger rows to counterparties.
- **B: no new `records:` config, no type stub.** Born album-native post-k3 (§7.1).
- **C: owner is `cash`, stem `bank`, noun `payee`, emoji `🏦`.** Multi-account via
  `account` suggest field, not folders or nested albums.
- **D: daily ritual unchanged in v1.** `@BANK` lines + scheduled review task stay the
  acknowledgment path; album capture is for payee creation/update, not per-transaction
  filing.
- **E: no amount/date/balance frontmatter in v1.** Amounts live in dated notes text.
  Queryable amounts wait for CSV import (new work, not scoped here).
- **F: index/catalog follow existing contracts exactly.** No new grouping, sorting, or
  chip semantics for bank — grouped-by-status index, plugin-drawn chips, Base for
  time slices.
- **G: fallback on record.** If structured amounts are required immediately, build the
  statement album (§6) instead of transactions — recorded here so a later plan has the
  branch without re-researching.

## 10. Recommended solution (restated for the lead)

Wait for `bob-cli-k3` to land. Then create **`bank.md` under `[[cash]]` as a payee
album** per §5 (noun `payee`, `status` + `category` + `account` + `url`,
`dated_notes: true`, `index_by: category`), seed from the historical `@BANK` payees,
keep the daily `@BANK` + review-task ritual, browse via the generated `[!records]`
index plus a month-filtered `bank.base`, and defer queryable amounts until a CSV import
path exists. If amounts-in-frontmatter cannot wait, build the statement album instead —
never the transaction album.
