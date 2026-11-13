# Bank, weekly: Ctrl+Enter files each row with one key, then lands on the next

Researcher: `cld` (one of five in the swarm). Date: 2026-11-13.

Scope. This report covers the five asks:

- auto-advance after a Ctrl+Enter close;
- a Wells Fargo link on the bank chore;
- moving the chore from daily to weekly;
- a personal category list;
- a one-key category prompt when a row closes.

It also critiques the plan and ends with a recommended solution.

Privacy. The category work used the import journal on the vault
(`.bob/bank/*.jsonl`): 850 transactions, May 1 – Nov 12. This report gives only
category names, coarse frequency bands, and aggregate rates. It names no merchants,
amounts, people, places, or account digits.

---

## TL;DR

1. **Good idea, with one prerequisite.** A weekly import followed by fast keyboard
   filing is the right shape for this habit. But a category prompt on every close only
   stays cheap if bob usually has a good guess ready. **Today it almost never does.**
   - Wells Fargo QFX descriptions carry a `PURCHASE MM/DD … CARD dddd` tail.
   - Payee cleaning misses this tail on **87%** of rows.
   - So every imported payee keeps the purchase date and the card's last four digits,
     like `Corner Cafe Purchase 11/10 Anytown St Card ####` (synthetic).
   - Because the date is in the merchant key, the "learned" tier would recognize a
     repeat merchant on only **~13%** of rows.
   - Fixing that tail, plus processor order codes, raises the rate to **~77–85%**. Most
     rows would then arrive pre-categorized, and filing becomes `Ctrl+Enter`, `Enter`.
   - **Fix this first.** Without it, the prompt is pure toil. The epic's own trial rule
     says: "if it goes mostly to categorizing, drop categories."
2. **Merge the two chores; don't just re-cadence one.** `gtd_daily.md` already has two
   bank chores:
   - a daily `Acknowledge bank` (type rows by hand from the WF app);
   - a Monday `Bank import` (QFX).

   Retire the daily one. Make the Monday one the single weekly **Bank** chore, carrying
   the Wells Fargo link and the new filing steps.
3. **The Category card.** Ctrl+Enter on a waiting row opens a compact keycap card from
   the same family as the Cmd+Y Copy card:
   - one letter files the row;
   - `↵` (or a second `Ctrl+Enter`) accepts bob's highlighted suggestion;
   - `␣` acknowledges with no category;
   - `Esc` changes nothing.

   The tick and the `[cat:: key]` are written in **one editor transaction**, so one undo
   reverts both. The cursor then lands on the next waiting row.
4. **Hotkeys are bob's to assign.** Each category may declare a `key:` in `bank.md`.
   Otherwise bob derives one. Either way, bob reports it in the JSON that every
   `bob bank` command already prints, so the plugin only renders it. Keys never change
   meaning, and retired categories are **hidden, never deleted**. This mirrors the theme
   hue and hide decisions.
5. **Your category list:**
   - 12 everyday categories on mnemonic letters;
   - 8 bills on digits ("letters for what you decide, digits for what bob already
     knows");
   - the 4 built-ins on `i r t a`.

   It is listed in §5.2 and ready to paste.
6. **The bank-feed spike (`bob-cli-kv`) has hit its trigger.** That task was conditional
   on "the weekly QFX download is the friction", and you have now said exactly that. Move
   its snooze earlier. A feed removes the toil outright. A weekly cadence only rations it.

---

## 1. What exists today

| Piece | Where | State |
| --- | --- | --- |
| Categories in config | `bank.md` → `bank.categories` (an ordered map of `key: "<emoji> Label"`), plus built-ins `income`, `refund`, `transfer`, `cash` | ✅ Exists. Your hub declares 14 starters. |
| Row grammar | `[cat:: key]` anywhere in the row tail. bob's canonical spot is right after the payee (`src/native/bank/grammar.rs` `render_row`, `parse_row_tail`). | ✅ |
| Import naming tiers | Four tiers: a rule, then a learned name (the most recent **acknowledged** row with the same merchant key), then WF built-ins (ATM → `cash`, fees, transfers), then the cleaned description (`src/native/bank/naming.rs`) | ⚠️ Learning rarely fires on real WF QFX data (§2). |
| Category typing helper | Typing `[cat:: ` in a month note suggests keys (ledger-tools `241k-plugin-bank-actions.js`, `setupBankCategorySuggest`) | ✅ But it is slow: typing the field, then searching a fuzzy list. |
| Ctrl+Enter on a bank row | task-status-cycler `192-bank-row-guard.js` → `cyclerBankLocalFlip`. It flips `[ ]`↔`[x]` as plain bytes and runs no walk or successor logic. It is called from both the Vim and command paths (`140-plugin-vim.js`, `160-plugin-completion.js`). | ✅ Flip only. No category, no advance. |
| Row marks | ledger-tools `241o/241p` render `[cat::]` as an emoji+label chip | ✅ A filed row already looks good. |
| Report and cards | Out by category, Unclassified always shown, month card bars | ✅ |
| Chores | `gtd_daily.md`: a daily `Acknowledge bank` PRE and a Monday `Bank import` PRE | Two chores |

So yes: categories are **mostly built**. What is missing is the cheap moment at which to
choose one, plus guesses good enough that choosing is usually just confirming.

The 7 rows you imported this morning (Nov 12 postings) are all ticked, and none has a
category. Renaming them is free right now: no category history exists yet.

## 2. What the data says (aggregate only)

| Measure | Value | Design consequence |
| --- | --- | --- |
| Volume | ~31 rows/week (weekly min 6, median 30, max 38) | One weekly session is ~30 decisions. At two beats a row, that is about 1–2 minutes once suggestions work. |
| Share with WF's card tail (`… PURCHASE MM/DD <place> <ST> CARD dddd`) | **87%** | Cleaning was built from the CSV shape (`PURCHASE AUTHORIZED ON …`, `S<digits> CARD dddd`), so it misses the QFX shape. |
| Learned-tier hit rate today (merchant key includes the date) | **~13%** | The learned tier is effectively off. |
| …after stripping the card tail | ~64% | |
| …plus processor order codes (`*AB1C2`) | ~77% | |
| …plus ATM and P2P tails | ~85% | Most rows arrive pre-filed. The card mostly confirms. |
| Concentration | The top 10 merchants cover 57% of rows; the top 40 cover 85% | The cold start is about 40 one-time decisions spread over 2–3 weeks. No rule-writing marathon is needed. |
| Rows vs dollars | A few small, frequent kinds of purchase dominate the **row count**, while two fixed monthly obligations dominate the **dollars** | Categories are worth having: the frequent small spends are where awareness pays, and they are invisible in dollar totals. |
| Posting days | Mon–Fri only, and Monday is the heaviest (weekend purchases) | A Monday-morning download covers through Friday's postings. Weekend spending shows up the following week. That is harmless (14-day overlapping windows), but worth knowing for "what surprised me?". |

Privacy side-finding. Uncleaned payees put the **card's last four digits** into vault
text, which is git-synced. ACH rows also carry reference numbers and the account
holder's name. The journal masks digit runs, but rows written to the vault do not.
`docs/bank.md` promises that untrusted descriptions "cannot inject" grammar. It does not
promise redaction, but this leak is clearly unintended. The cleaning fix closes it.

## 3. Critique: is this a good idea?

**Yes. This is the right correction to the epic.** The epic bet on "acknowledge daily,
prove weekly", with you typing rows by hand from the app. The evidence:

- You actually ran a QFX import on each of the last two mornings. The daily ritual had
  already turned into a daily download.
- That download is the toil. Typing ~4–5 rows a day by hand would be worse.

A weekly import plus a fast filing pass keeps the epic's guarantees: balance proof,
nothing missed, every total drawn at read time. It drops the daily cost.

What I would change or add:

1. **The prompt must not become the new toil.** A keypress per row is only a joy when
   the right answer is usually pre-selected. That depends on the cleaning and learning
   fix (§5.5). Ship that first or alongside.
2. **Don't let auto-acceptance train bad habits.** It is tempting to skip the card when a
   row already has a category, making Ctrl+Enter one beat. I recommend **always showing
   the card**. You asked to be prompted, and the uniform two-beat rhythm is predictable.
   It also keeps learning honest: categories learned from rubber-stamped guesses
   reinforce their own errors. Accepting is a single `↵`, so the cost is one key.
3. **Weekly loses "daily awareness". That is fine, but say so.** The epic's ADJ-4
   ("a daily chance to look") goes away. The WF app's own notifications cover day-level
   surprises. The weekly pass covers patterns.
4. **Categories are about what you bought, not how you pay.** Your current
   `subscriptions` category describes a payment cadence. The planned subscriptions album
   (`bob-cli-kt`) already tracks recurrence. Split that bucket by meaning instead:
   `tech` (AI, cloud, dev tools) and `media` (streaming, news, audio).
5. **The feed spike should move up.** See TL;DR 6. Until it lands, the weekly cadence
   is the right compromise.
6. **Scope discipline.** No splits, budgets, or cloud categorization, consistent with the
   epic's ADJ-8. Bulk "Bank: acknowledge this day" stays as an escape hatch: it
   acknowledges with no category, and Unclassified stays visible in every total.

## 4. Requirement adjustments (called out)

| # | Your requirement | Adjusted to | Why |
| --- | --- | --- | --- |
| **A1** | "Change this [daily] task so it recurs weekly" | **Retire** the daily `Acknowledge bank` chore. Fold its steps into the existing Monday `Bank import` chore and rename that one **Bank**. | Two weekly bank chores would be redundant. The import already writes every row you'd have typed. |
| **A2** | Prompt for a category on close | The prompt is the **Category card**. It always opens, with bob's suggestion pre-highlighted. `↵` or a second `Ctrl+Enter` accepts it, a letter overrides it, and `␣` means "no category". | One keypress is preserved in every case. Confirmation keeps learning clean. |
| **A3** | (implicit) Categories need keys | **bob assigns hotkeys:** an explicit `key:` in config, otherwise derived. They ship in the `categories[]` JSON. Retired categories take `hidden: true` and are never deleted. | One source of truth for every client (Obsidian now, possibly Mac later). Old rows never become `bank_category_unknown`. |
| **A4** | "Jump to the next unticked row" | Search **forward in the same month note, then wrap**. Never auto-switch files. If the note is clear, a notice names other months that still have waiting rows. The jump is recorded for Ctrl+O. | Notes run oldest-first, so forward is chronological. Switching files on a keypress would be surprising. |
| **A5** | (new) | **Reopening** (Ctrl+Enter on `[x]`) keeps the category and opens no card. It does not advance. | Reopen is a correction, not a filing. |
| **A6** | (new, prerequisite) | **Fix WF QFX payee cleaning and the merchant key.** Clean learned payees too (§5.5). | Without this, the card asks a real question on ~87% of rows, and payees leak card digits into the vault. |
| **A7** | "A good link to the WF URL" | Use a **verified** link. I could not confirm a public, stable deep link to *Download Account Activity* (§5.1), so the link comes from a 1-minute test, with the menu path in the link text as a fallback. Optionally store it as `bank.accounts.<alias>.download_url` so bob's stale hint and the queue card can show it too. | A broken deep link is worse than a sign-on link with a clear path. |
| **A8** | (new) | **Move the `bob-cli-kv` feed spike earlier.** | Its trigger condition is now met. |

## 5. Design

### 5.1 The weekly Bank chore (vault only, no code)

Replace the two bank lines in `gtd_daily.md` with one chore. Write it with
`bob capture`, as the epic did. Do not edit it by hand. Suggested text:

```markdown
- [ ] #task #gtd #pre #browser **Bank**: [Wells Fargo › Download Account Activity](<VERIFIED-URL>) · Checking · last 14 days · Quicken (QFX) · `bob bank import ~/Downloads/*.qfx`, then trash the .qfx · in this month's [[bank]] note, `Ctrl+Enter` each waiting row and press its category key · ✓ balanced? · one line in last week's note: what surprised me?  [repeat:: every week on Monday when done]
```

Then cancel the daily `Acknowledge bank` occurrence; don't delete it. Its history and
the `^acknowledge-bank` LINKED FROM line stay intact.

**Getting a good link.** Download Account Activity lives behind sign-on. Public sources
describe only the path (Accounts › Download Account Activity › pick account, date range,
Quicken format) and the sign-on host `connect.secure.wellsfargo.com`. None of them gives
a deep link that survives sign-on. To get one:

1. On the Mac, sign in, open **Download Account Activity**, and copy the address-bar URL.
2. Check that the URL contains **no account number or account index**. The vault is
   git-synced.
3. Sign out, then paste the URL into a new tab.
   - If sign-on returns you to the download page, that is the good link.
   - If not, use the sign-on URL. The link text already names the path.

**Why trash the QFX?** The file contains the full account number, and the
`~/Downloads/*.qfx` glob re-reads every old file each week. Import is idempotent, so
this is harmless, but it is noise. A later `bob bank import` flag could offer this.
Before proposing it, check it against the CLI rules memory.

**Day choice.** Keep Monday. It rides the weekly review, as the epic decided. Tuesday
would include weekend postings (§2) but would separate the bank from the review. The
14-day window overlaps the previous import, so a skipped week heals itself, and
`stale_after: 10` flags a second skipped week.

### 5.2 Your categories (paste-ready)

Derived from the 6.5-month journal. Bands are coarse on purpose. A handful of rare
purchase kinds (<1% of rows) fold into the nearest broader bucket instead of getting
their own key.

| Key | Category | Band | Notes |
| --- | --- | --- | --- |
| **Everyday: letters** | | | |
| `c` | ☕ Coffee | several/week | The single most frequent kind of row |
| `v` | 🏪 Convenience | near-daily | Convenience-store and gas-station runs |
| `s` | 🛍️ Shopping | several/week | Mostly online orders. Mixed baskets go to the dominant item. |
| `d` | 🛵 Delivery | ~weekly | Food-delivery apps. Kept apart from eating out because it is a distinct, frequent habit. |
| `e` | 🍽️ Eating out | ~weekly | Restaurants and sit-down meals (key `dining` kept) |
| `g` | 🛒 Groceries | ~weekly | Includes bulk stores |
| `p` | 🌿 Personal | ~weekly | A recurring specialty-shop cluster, named neutrally here. Rename it to what you'd say out loud. |
| `h` | 💊 Health | ~weekly | Pharmacy, medical, insurance premium |
| `o` | 🐶 Dog | occasional | Pet supplies and care |
| `f` | 🎟️ Fun | occasional | Outings and trip activities |
| `n` | 🚆 Transit | ~weekly | Fares, parking, tolls |
| `k` | 🚗 Car | monthly | Insurance and fuel |
| **Bills: digits (usually pre-filled)** | | | |
| `1` | 🏠 Housing | monthly | Housing payments and municipal services (key `home` kept) |
| `2` | 💡 Utilities | monthly | Phone, gas/electric |
| `3` | 💻 Tech & AI | monthly+ | AI subscriptions, cloud, domains, dev tools. More rows than media. |
| `4` | 📺 Media | monthly | Streaming, news, audio (replaces `subscriptions`) |
| `5` | 🎓 Loans | monthly | |
| `6` | 🤝 Household | monthly | Person-to-person payments that are really shared household costs. Count them as spending, **not** `transfer`. `transfer` is for money that stays yours. |
| `7` | 🏛️ Taxes | rare | |
| `8` | 🧾 Fees | ~weekly | Out-of-network ATM fees recur: the epic's predicted first "observation" is real |
| **Money moves: built-ins** | | | |
| `i` | 💵 Income | | Pay and deposits |
| `r` | ↩️ Refund | | Purchase returns |
| `t` | ↔️ Transfer | | Own-account moves, card payments |
| `a` | 🏧 Cash out | | ATM ("destination unknown") |

Changes from today's hub:

- add `convenience`, `delivery`, `personal`, `loans`, `taxes`, `household`;
- split `subscriptions` into `tech` and `media`;
- keep `kids` only if you expect to use it, since nothing in the sample needs it (hide it
  otherwise).

Every rename is free today because no row carries a category yet.

```yaml
bank:
  categories:
    coffee:      { label: ☕ Coffee,       key: c, group: Everyday }
    convenience: { label: 🏪 Convenience,  key: v, group: Everyday }
    shopping:    { label: 🛍️ Shopping,     key: s, group: Everyday }
    delivery:    { label: 🛵 Delivery,     key: d, group: Everyday }
    dining:      { label: 🍽️ Eating out,   key: e, group: Everyday }
    groceries:   { label: 🛒 Groceries,    key: g, group: Everyday }
    personal:    { label: 🌿 Personal,     key: p, group: Everyday }
    health:      { label: 💊 Health,       key: h, group: Everyday }
    dog:         { label: 🐶 Dog,          key: o, group: Everyday }
    fun:         { label: 🎟️ Fun,          key: f, group: Everyday }
    transit:     { label: 🚆 Transit,      key: n, group: Everyday }
    car:         { label: 🚗 Car,          key: k, group: Everyday }
    home:        { label: 🏠 Housing,      key: "1", group: Bills }
    utilities:   { label: 💡 Utilities,    key: "2", group: Bills }
    tech:        { label: 💻 Tech & AI,    key: "3", group: Bills }
    media:       { label: 📺 Media,        key: "4", group: Bills }
    loans:       { label: 🎓 Loans,        key: "5", group: Bills }
    household:   { label: 🤝 Household,    key: "6", group: Bills }
    taxes:       { label: 🏛️ Taxes,        key: "7", group: Bills }
    fees:        { label: 🧾 Fees,         key: "8", group: Bills }
    kids:        { label: 🧸 Kids,         hidden: true }
```

Config contract (bob-cli):

- The scalar form `coffee: ☕ Coffee` stays valid, so this is backward compatible.
- The mapping form adds four keys:
  - `label` (required);
  - `key` (one lowercase letter or digit);
  - `group` (free text; the card's section heading);
  - `hidden` (stays valid on rows, never offered).
- Built-ins keep fixed defaults `i r t a`, and declaring one may override its key.
- Reserved keys are `q`, Space, and Enter. `q` closes the card, as on the Copy card.
- **Derivation when `key:` is absent.** Scan declared categories in order. Take the
  first letter of the category key that isn't reserved or taken, then the remaining
  letters of the key, then the label's letters, then `1`–`9`.
- Conflicts or reserved keys raise `bank_config_invalid` with file, line, and key path,
  like every other config error.
- JSON `categories[]` gains `hotkey`, `group`, and `hidden`. This is additive, so
  `schema_version` stays 1.
- `[cat::]` suggestions skip hidden categories. `check` still accepts them on rows.

### 5.3 The Category card (Ctrl+Enter on a waiting row)

```text
╭──────────────────────────────────────────────────────────────────╮
│  $6.45    Corner Cafe                             Thu Nov 12     │
│  waiting · 3 of 31   ▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱             │
├──────────────────────────────────────────────────────────────────┤
│  EVERYDAY                                                        │
│  ┏━━━━━━━━━━━━━━━━━━━┓                                           │
│  ┃ C  ☕ Coffee   ↵   ┃  V  🏪 Convenience    S  🛍️ Shopping      │
│  ┗━━━━━━━━━━━━━━━━━━━┛                                           │
│    D  🛵 Delivery        E  🍽️ Eating out     G  🛒 Groceries     │
│    P  🌿 Personal        H  💊 Health         O  🐶 Dog           │
│    F  🎟️ Fun             N  🚆 Transit        K  🚗 Car           │
│  BILLS                                                           │
│    1  🏠 Housing   2  💡 Utilities   3  💻 Tech & AI   4  📺 Media │
│    5  🎓 Loans     6  🤝 Household   7  🏛️ Taxes       8  🧾 Fees  │
│  MONEY MOVES                                                     │
│    I  💵 Income    R  ↩️ Refund      T  ↔️ Transfer    A  🏧 Cash  │
├──────────────────────────────────────────────────────────────────┤
│  ↵ ☕ Coffee · learned      ␣ no category      esc cancel        │
╰──────────────────────────────────────────────────────────────────╯
```

**Keys** (the same family as the Copy card: a key never changes meaning):

| Key | Effect |
| --- | --- |
| category key | Writes `[x]` and `[cat:: key]` in one transaction, closes the card, and advances |
| `↵` or a second `Ctrl+Enter` | Accepts the highlighted suggestion. With no suggestion it does nothing and the footer says "pick a category". |
| `␣` Space | Acknowledges with no category (counts as Unclassified) and advances |
| `↑ ↓ ← →`, `Ctrl+N` / `Ctrl+P` | Move the highlight within the grid |
| `Esc`, `q`, `Ctrl+[` | Close with **no write**. The cursor stays. |
| other keys | Ignored. A dimmed key nudges and announces why, as on the Copy card. |

**The suggestion** is whatever the row already carries (an import rule or a learned
category). The footer names where it came from (`learned`, `rule`, `bank`) so you know
how much to trust it. On a typed row with no category there is no highlight.

**Sign-aware layout.** For an inflow (`+$`), MONEY MOVES moves to the top and spending
groups dim. They stay selectable, but `check` will still give `bank_inflow_category`.
Keys never move, so muscle memory holds.

**Beauty:**

- Amounts use tabular numerals. Outflows are neutral and inflows green: the report rule
  "spending is not an error" applies here too.
- Keycaps are monospace, with the suggestion in an accent ring.
- The progress meter reads "3 of 31 waiting", the count of waiting rows in this note.
- Section headings use quiet small caps.
- On a pick, the card closes instantly (the write is local), the row's existing category
  chip appears, the filed row gets a brief settle flash (the yank-flash idiom), and the
  landing row gets a soft focus flash. `prefers-reduced-motion` turns both off.
- **Accessibility:** `role="listbox"` with `aria-keyshortcuts` on each option, and a
  live region that announces "Filed $6.45 as Coffee · next $12.90 waiting". State is
  never carried by color alone.

**The end of the run.** Once the last waiting row in the note is filed, a toast closes
the loop with bob's numbers. Bob owns every total, so the toast data comes from
`bob bank report -w … -f json` and `list`:

> 🏦 November filed · WF Checking ✓ balanced through Nov 12 · 2 waiting in October →

That is the moment to write "what surprised me?".

### 5.4 Advancing to the next waiting row

- **Target.** The next top-level row with `[ ]` after the filed row, in document order.
  It skips ticked rows, stubs, invalid rows, and child bullets. If none is below, the
  search wraps to the first waiting row above. The search only runs after a successful
  card write: Esc, reopen, and refused writes never advance.
- **Cursor.** It lands at the start of the **payee**, so a Vim `cw` renames it at once.
  The landing scrolls into view if it is off-screen and pushes a Ctrl+O jump, matching
  the review walk's landing rule.
- **Double-press safety.** A short gesture lock (about 300 ms) swallows a repeated
  Ctrl+Enter that would otherwise open the card on the row you just reached. Same idea as
  the walk's "short gesture lock".
- **Nothing left in this note.** Show the toast above. If the `bob bank list` cache shows
  waiting rows in other months, the toast offers to open the queue. It never switches
  files on its own.

### 5.5 Making the suggestion right (the prerequisite)

All of this is in bob-cli, `src/native/bank/naming.rs` and `identity.rs`:

1. **Strip WF's QFX card tail** in `clean_description`: `␠PURCHASE[ RETURN]
   [AUTHORIZED ON ]MM/DD … [CARD dddd]` and `␠RECURRING PAYMENT [AUTHORIZED ON ]MM/DD …`.
   Classify built-ins **before** cleaning, as now, so `RETURN` can still mean refund.
2. **Strip processor order codes.** Remove a `*` followed by a short token containing a
   digit, which is an order code. Keep a `*` followed by words, which is a real
   sub-merchant name such as a restaurant behind a delivery app.
3. **Mask long digit runs and drop the account-holder name tail** from ACH and P2P
   payees.
4. **`merchant_key` inherits all of this automatically**, because it calls
   `clean_description`. `learn()` already recomputes keys from the masked journal `desc`,
   so **no migration is needed**: history becomes comparable immediately.
5. **Clean learned payees too.** Your 7 existing acknowledged rows still carry the
   uncleaned payee. After the fix they would *teach* it, stale date included, to every
   future row of that merchant. Run the same cleaner over a learned payee before
   reusing it. It is idempotent on names you have edited.
6. **Optional tidy-up.** Stop writing `[acct:: checking]` when the account is the
   default. It is noise on every imported row.
7. **Tests.** Add synthetic fixtures in the real QFX shape. Never use real data.
   Required cases:
   - the same merchant on different days gets one key;
   - delivery sub-merchants stay distinct;
   - order codes collapse;
   - card digits never appear in a written row.

### 5.6 Who owns what

```text
Ctrl+Enter ─► task-status-cycler bank guard (192)
               │  ledger-tools api.bank v1 present?
               ├─ yes ─► api.bank.claimClose(editor, file, line)
               │          → Category card (ledger-tools) → one editor transaction
               │          → advance cursor → toast at end of run
               └─ no  ─► today's plain [ ]↔[x] flip (graceful fallback)
```

- **bob-cli** owns the categories, their hotkeys, groups, and hidden flags, the
  suggestion (written into the row at import), cleaning, learning, the totals, and the
  final toast's numbers. It adds **no new subcommand**: the plugin reads `categories[]`
  from the `bob bank list|report -f json` it already fetches.
- **bob-ledger-tools** owns the card, the write, the advance, the toast, and a
  **Bank: set category** command (no default hotkey). That command opens the same card
  on any row, ticked or not, without changing the box. Use it to recategorize.
- **task-status-cycler** keeps its guard and gains one delegation hook, the same pattern
  it already uses for the nav review-walk APIs. If ledger-tools is disabled, behavior is
  exactly today's.
- **The ownership contract is unchanged.** The category is written in your editor as
  your edit, so `docs/bank.md` § Ownership still holds: bob's only row edits remain
  `ack` and the ID append. A `bob bank ack ID -c KEY` for terminal parity is optional and
  would need that contract amended. Leave it for later.

### 5.7 Reliability rules

- **Re-verify before writing.** The card captures the row's line text and `^bank-` ID
  when it opens. On a pick, re-read the line, and relocate it by ID if lines shifted, for
  example after a sync merge. Refuse with a notice if the row changed. The successor
  offer card uses the same rule.
- **One transaction.** The status byte and the category span are written together.
  `[cat::]` is inserted at bob's canonical spot (after the payee), or its value is
  replaced in place if one exists. Other bytes stay identical.
- **Only declared categories.** Keys come from bob JSON, with a stale-while-revalidate
  cache. On a cold cache the card shows a brief loading state. If bob is unreachable,
  the card offers only `␣ tick without category` and `Esc`. Acknowledging is never
  blocked.
- **Guards stay.** No `#task` and no freshness, status, or completion metadata ever
  reaches a bank row.
- **Tests.** Extend `scripts/test-task-status-cycler-bank-guard.cjs` (delegation and
  fallback), add ledger-tools unit tests (card model, key routing, advance target,
  write splice), and add one `obsidian-bank-ui-e2e` scenario: import fixture, then
  Ctrl+Enter, `c`, landing, Ctrl+Enter, `↵`, Esc, and finally the end toast.

## 6. Alternatives considered

| Option | Verdict |
| --- | --- |
| **A "filing run":** the card stays open and re-targets the next row, one key per row | It is faster (1 beat vs 2), but more modal. It hides the note, so you can't fix a payee or add a `— note` or `⚑` between rows. **Later, if the trial shows you pressing Ctrl+Enter, ↵ on most rows.** |
| Skip the card when a row is pre-categorized (Ctrl+Enter = accept what you see) | It is one beat for most rows, but the behavior varies by row state, and it lets learned errors reinforce themselves. **Rejected** in favor of the always-on card. |
| Obsidian's `EditorSuggest` or a fuzzy picker | It needs typing, and it is not one key. **Rejected.** The existing `[cat:: ` suggest stays for hand-typed rows. |
| Positional hotkeys `1`–`9`, `a`–`z` by order | Not mnemonic, and inserting a category reshuffles them. **Rejected.** Use explicit or derived stable keys. |
| bob writes the category (`bob bank ack -c`) | It changes the ownership contract, races the open editor buffer, and loses Vim undo. **Rejected for v1.** |
| A "bulk file the week" table | Encourages rubber-stamping. **Rejected.** |
| Keep the daily chore as well | Two bank chores and double the toil. **Rejected** (A1). |
| Backfill the 843 journaled pre-start transactions as rows for six months of history | It would need a deliberate backfill path (journaled `before_start` items count as "seen"), and it is a ~20-minute one-off. **Not now.** Revisit with `bob-cli-ku`, which wants two months of history. |

## 7. Open questions for you

1. Should **🤝 Household** count as spending? I recommend yes. The other choice is
   `transfer`.
2. Should the **🌿 Personal** name stay neutral, or would you prefer a plainer label?
3. **Kids**: keep it visible, or hide it?
4. Is the **Monday** chore OK, or do you want **Tuesday** so each pass covers complete
   Mon–Sun postings?
5. When should the **feed spike** run: soon, or after the planned trial date?

## 8. Recommended solution

Ship it as one small epic in four steps. Order matters: make the guesses good before
asking you to confirm them.

1. **Vault, today, no code.**
   - Capture the merged weekly **Bank** chore with the verified Wells Fargo link (§5.1).
   - Cancel the daily `Acknowledge bank` recurrence.
   - Paste the scalar form of the §5.2 categories into `bank.md`. Keys follow in step 2.
   - Rename this week's 7 payees by hand.
   - Move `bob-cli-kv`'s snooze earlier.
2. **bob-cli: guesses and hotkeys.**
   - WF QFX cleaning for payees and the merchant key, plus learned-payee cleaning (§5.5).
   - The category mapping form (`label`, `key`, `group`, `hidden`), hotkey derivation
     and validation, and the additive JSON fields (§5.2).
   - Optionally, stop writing default `[acct::]`.
   - Docs: `docs/bank.md`, the guide rewritten from daily to weekly, and `bob bank`
     next-step hints that point at the month note.
3. **bob-plugins: the gesture.**
   - ledger-tools `api.bank v1`, with the Category card, the one-transaction write, the
     next-row advance with jump and gesture lock, the end-of-run toast, and the
     **Bank: set category** command.
   - The task-status-cycler delegation hook with fallback.
   - Docs and tests, then `bob plugins sync`.
4. **Memory and docs wrap-up.**
   - Update `glossary:bank-row` (filed on close; categories carry hotkeys).
   - Propose a decision record, for example `bank-close-files-a-category`: "Ctrl+Enter
     on a waiting bank row always asks for one category with one key, then lands on the
     next waiting row. bob assigns stable hotkeys. Categories are hidden, never
     deleted." This needs `/sase_memory_write` authorization.

**Expected experience after step 3.** Monday morning:

1. One click on the chore's link, download the QFX, and run one command.
2. Open the month note and press Ctrl+Enter on the first waiting row.
3. Then it is `↵`, Ctrl+Enter, `↵`, Ctrl+Enter, `c`… About 30 rows. Once learning warms
   up (2–3 weeks), roughly four of every five are a plain `↵`.
4. The run ends on "✓ balanced" and a prompt to write what surprised you.

About 2 minutes a week instead of a daily download.

---

### Sources

- Wells Fargo Web Connect help (the Download Account Activity flow):
  [wellsfargo.com/online-banking/software/web-connect](https://wellsfargo.com/online-banking/software/web-connect).
  This URL returned 404 when fetched today; the search snippet described the flow.
- Wells Fargo Account Activity (download depth, extended time frame):
  [wellsfargo.com/biz/online-banking/deposit-details](https://www.wellsfargo.com/biz/online-banking/deposit-details/)
- Wells Fargo Account Activity FAQs:
  [wellsfargo.com/help/online-banking/activity-faqs](https://www.wellsfargo.com/help/online-banking/activity-faqs/)
- Quicken Community, manual Wells Fargo QFX download and history limits:
  [community.quicken.com/discussion/comment/20233730](https://community.quicken.com/discussion/comment/20233730),
  [community.quicken.com/discussion/comment/20141152](https://community.quicken.com/discussion/comment/20141152/)
- Sign-on host guidance (go to `connect.secure.wellsfargo.com` directly):
  [onlinebankinghelp.com — Wells Fargo login guide](https://www.onlinebankinghelp.com/banks/wells-fargo/wells-fargo-login-guide/)
- Local evidence:
  - `docs/bank.md`, `docs/guides/acknowledge-bank-transactions.md`, and
    `src/native/bank/{naming,identity,grammar,config}.rs` (bob-cli);
  - bob-plugins `task-status-cycler/src/192-bank-row-guard.js`, `140-plugin-vim.js`,
    `160-plugin-completion.js`, `bob-ledger-tools/src/241k-plugin-bank-actions.js`,
    `241o-plugin-bank-marks-model.js`, and `docs/copy-card.md`;
  - the epic plan `plan:202611/bank_daily_acknowledgment.md` (trial rule, ADJ-4/5/8,
    follow-ups) and the beads `bob-cli-kd`, `bob-cli-kt`, `bob-cli-ku`, `bob-cli-kv`;
  - aggregate-only analysis of the vault's bank import journal.
