# Bank tracking, second pass: weekly rhythm, jump-to-next, and one-keypress categories

Research by `research.4i.mus` (independent swarm member; report suffix `__mus`).
Date: 2026-11-13. Epic context: `bob-cli-kd` (closed 2026-11-12, all 7 phases landed).

## Question asked

Bryan wants five changes to how he tracks bank transactions:

1. `Ctrl+Enter` on a bank row should jump to the next unticked bank row.
2. The daily bank task in `~/bob/gtd_daily.md` should link to the right Wells Fargo URL.
3. That task should recur weekly instead of daily (QFX-download toil doesn't justify daily).
4. Support a user-configured category list (partial support exists today).
5. On `Ctrl+Enter`-close, prompt for a category selectable with a single keypress.

Plus: lead the design (intuitive, reliable, beautiful), critique the plan, adjust
requirements where justified, end with a recommended solution.

## What I verified (evidence, not assumption)

- **Epic state.** `sase bead read bob-cli-kd` shows the epic CLOSED with all 7 phases
  closed; follow-ups went to `bob-cli-kt` (subscriptions album), `bob-cli-ku`/`bob-cli-kv`
  (later views, feed spike). `docs/bank.md` is the shipped contract; `bob bank
  {list,report,ensure,ack,import,check}` all ship with `schema_version: 1` JSON.
- **Categories already exist.** `bank.md` holds `bank.categories` (ordered map
  `key: "<emoji> Label"`), four built-ins (`income`, `refund`, `transfer`, `cash`) that
  always exist, and `bank.rules` (`match`/`cat`) used at import time. `docs/bank.md`
  says "Categories are optional; only `transfer`, `income`, `refund`, and `cash`
  change totals." So "partial support" = declared + validated (`bank_category_unknown`
  finding) + used in totals/breakdown/report JSON, but **no way to set one after import
  except typing `[cat:: key]` by hand**, no prompt, no picker, no `ack --cat`.
- **`bob bank ack` only ticks.** `src/native/bank/ack.rs` plans `[ ]`→`[x]` flips and
  nothing else. There is no CLI path that writes or changes `[cat::]`.
- **What `Ctrl+Enter` does on a bank row today.** The shipped plugins in
  `~/.obsidian/plugins` confirm the kd.6.1 design: `task-status-cycler`'s
  `192-bank-row-guard.js` classifies the line and, for bank rows, allows only
  space↔x flips as a local editor write ("Bank row · not a task status" otherwise) —
  no freshness stamp, no task recovery, no cursor move, no prompt. `bob-ledger-tools`
  owns `bank-open-today`, `bank-ack-day`, queue-card checkboxes (wired to
  `bob bank ack <IDs>`), `[cat:: ` EditorSuggest completions in declared order, and
  Enter-continues-`- [x] $`. No modal/picker exists in either bank plugin today
  (the only Modal precedent is the freshness decay card in `bob-navigation-hotkeys`,
  `060-decay-card-modal.js`).
- **The live ritual.** `~/bob/gtd_daily.md` has two bank PRE chores: **Acknowledge bank**
  (`[repeat:: every day when done]`, "open the Wells Fargo app · type each new posted
  row under its day in this month's `[[bank]]` note (ticked) · tick any waiting rows")
  and **Bank import** (`[repeat:: every week on Monday when done]`, "download the last
  14 days as Quicken (QFX) … run `bob bank import …` · tick what it wrote · write one
  line in last week's note: what surprised me?"). The weekly-repeat syntax the request
  wants already exists and is proven — the import chore uses it.
- **Yesterday's import (Nov 13, host `kellys-macbook-pro-local`).** Journal
  `.bob/bank/kellys-macbook-pro-local.jsonl`: one `bank.import` event, window
  2026-11-12→2026-11-12, 7 new waiting rows, 0 matched/ambiguous. All 7 now ticked in
  `bank/2026-11.md` under `## Thu Nov 12`, none carrying `[cat::]` (all land in
  Unclassified). Stated generically, per the no-personal-details constraint: the batch
  is 7 small outflows — one recurring web-services charge, three coffee-shop visits,
  one convenience-store stop, one transit-adjacent small purchase pattern, and one
  large fixed student-loan payment. Full card numbers and raw QFX descriptors are in
  the note rows (the journal masks digit runs; the notes do not — see privacy note).
- **Wells Fargo download path.** Public sources agree: sign on to Wells Fargo Online,
  open the account, choose **Download Account Activity**, select **Quicken Web Connect
  (QFX)**. I fetched `https://www.wellsfargo.com/online-banking/` (200 OK; redirects to
  the Mobile & Online Banking hub) and confirmed the stable Sign On entry it links:
  `https://connect.secure.wellsfargo.com/auth/login/present?origin=cob`. No
  unauthenticated deep link can land directly on Download Account Activity.

## Requirement-by-requirement critique

### 1. Jump to next unticked on `Ctrl+Enter` — yes, with a defined scope

Good idea: acknowledging is a serial walk (oldest waiting → newest), and today the
cursor stays put, so every tick costs a manual hunt. The cycler guard is exactly the
right hook: after a successful space→x flip on a bank row, advance the cursor.

Adjustments needed (the request under-specifies "next"):

- **Scope order:** next unticked row under the same day heading → later day headings
  in the same month note → stop with a notice at the last waiting row ("Bank · nothing
  left waiting in November" + offer `Bank: open today`/queue card). Do **not** silently
  cross into another month note; month files are separate editor leaves and auto-opening
  files from a toggle is surprising.
- **Skip correctly:** acknowledged rows, plain checklist lines, prose, empty stubs
  (`- [x] $`), flagged rows stay (flag ≠ waiting; `⚑` rows that are `[ ]` are still
  waiting and should be landed on — flagging means "look into", not "skip").
- **Only on tick, not untick.** x→space is an undo; don't yank the cursor away from the
  row the user just re-opened.
- **Queue-card checkboxes** (rendered, moused) can't move a source cursor usefully;
  there, "jump" = re-render and move focus/highlight to the next waiting queue row.
- **Vim-mode safety:** the advance must go through the same guarded editor API (verify
  exact line bytes before moving; if the buffer changed under us, don't move).

### 2. Wells Fargo link in the daily task — yes, link Sign On, not a deep page

Recommend the task text link the Sign On entry
`https://connect.secure.wellsfargo.com/auth/login/present?origin=cob`
(post-login: account → Download Account Activity → Quicken Web Connect), because no
stable unauthenticated URL reaches the download screen and WF redesigns deep pages
regularly. Vault precedent supports inline markdown links in chore text (e.g. the
`[weather](https://google.com/search?q=weather)` chore). One line in the guide
(`docs/guides/acknowledge-bank-transactions.md` §2) should name the three clicks, since
a bare sign-on link doesn't teach the path. Cheap, durable, no code.

### 3. Daily → weekly — the request misdiagnoses the toil; merge, don't just reschedule

Critique: the daily chore's toil is **not** the QFX download — it says "open the Wells
Fargo app · type each new posted row". The QFX download already lives in the separate
weekly import chore. If we merely flip the daily chore to `[repeat:: every week …]`,
we get two overlapping weekly chores (acknowledge + import) that both say "tick what
posted", and we kill the only intraday path (typing rows as they post, which is also
what makes import's `matched` tier valuable — typed rows matching imports is the
proof-you-were-there loop).

What actually happened: weekly QFX import made daily transcription redundant — import
writes the rows, so the remaining work is triage (tick + categorize), which batches
naturally. So the justified adjustment:

- **Replace both chores with one weekly "Bank session" PRE chore** (Monday, after the
  import chore's slot): download QFX → `bob bank import` → walk the waiting queue
  (tick + one-keypress category each) → one surprise-line in last week's note. Delete
  the daily acknowledge chore; keep the daily chip (it still routes to today on demand).
- **Consequence to accept:** waiting rows pile up for up to 7 days; `bob bank`'s "nothing
  to acknowledge" stays noisy mid-week and `stale_after` (10d) still holds with a Monday
  cadence. The guide must say: mid-week, typing a row at purchase time is still allowed
  (import will `match` it); the weekly session is the backstop, not the only door.
- Keep `[repeat:: every week on Monday when done]` — the proven syntax — so the
  scheduler needs no code change. This is a vault edit + guide edit, zero CLI/plugin
  code.

### 4–5. User-configured categories + one-keypress prompt on close — yes, and this is the core feature

The current state (declared list, validated, totals-aware, but unsettable except by
hand-typing) is exactly "partial". Yesterday's batch proves the gap: 7/7 imported rows
uncategorized, all in Unclassified, because naming tier 4 (cleaned description) never
assigns spending categories and tiers 1–2 (rules, learned payees) had nothing to learn
from. Every import without a category step permanently degrades `report` breakdowns.

**What the 7-row sample says about the category list** (generic shapes only, no
merchants/amounts): the existing 14 user keys (`groceries dining coffee transit car
home utilities dog kids health shopping subscriptions fun fees`) cover 6 of 7 rows
(recurring web charge → `subscriptions`; coffee ×3 → `coffee`; convenience → `groceries`
or `shopping`). The gap is exactly one: the fixed student-loan payment has no honest
home — `subscriptions` is wrong for it (per the `subscriptions_scope=discretionary`
decision, obligations are not keep-or-cancel choices, and the kt album must not absorb
them). So: **add one obligation category** (recommend `debt`: `💸 Debt` — covers loan
payments; mortgage/rent later) and optionally a `transport`-adjacent top-up only if
future batches ask for it. Do not bulk-add speculative categories; each unused key
weakens the one-keypress mapping below. Also from the sample: payee cleaning leaves
`"PURCHASE … CARD NNNN"` noise in note rows — a separate small fix (extend the
cleaner), and note rows carry full card numbers while the journal masks them — worth a
privacy pass (mask in rows too, or document the exposure).

**Design for the prompt (intuitive, reliable, beautiful):**

- **Trigger:** only when a `Ctrl+Enter` tick lands on a row with **no** `[cat::]`.
  Already-categorized rows tick silently (plus jump-to-next). No prompt on untick, no
  prompt on bulk `ack -D`/ack-day (bulk uses per-row fallback: leave uncategorized;
  the queue card is where bulk categorization happens — see below). This bounds prompt
  fatigue to exactly the rows that need it.
- **UI:** a small card-modal (visual precedent: the decay card; styling precedent: the
  `bob-bank` cards — 2px accent start border, 14% accent background, emoji + label,
  native focus, declared order). Contents: the row's amount + payee (so the choice is
  grounded), categories in `bank:` declared order with **single-key hints**
  (`1–9, 0, then a–z` in order — 18 slots cover today's 14+4 without codes to memorize),
  type-to-filter narrowing, `Enter` = accept highlighted / skip-without-category,
  `Esc` = skip. One keypress categorizes; two at most with filter.
- **Write path (reliable):** editor-local guarded write, not a new CLI round-trip for
  the source-note flow: verify exact preimage bytes of the row, then insert
  `[cat:: key]` in canonical tail position (before links? after payee — follow the
  grammar's tail order; reuse the canonical renderer, don't string-hack) or replace an
  existing key. Preserve undo (single editor transaction combining tick + category so
  one undo undoes both). Refuse-and-refresh on moved/ambiguous bytes, same as the
  existing ID-less-row discipline. Validate the key against live `bank:` config
  (unknown → `bank_category_unknown` behavior, never write it).
- **Queue-card / bulk flow:** queue checkboxes call `bob bank ack <IDs>`, which cannot
  set categories today. Two options: (a) extend `ack` with additive `--cat KEY`
  applied to exactly the acked IDs (validated, refused on unknown — exit 2 like other
  ack refusals; JSON reports per-row `category`); the card then offers the same
  one-keypress card after bulk-ack for the still-uncategorized subset, applied via one
  `ack --cat` per distinct key. (b) Defer bulk categorization to source-note walks.
  Recommend (a): small, additive, no schema break (`categories`/`accounts` already in
  every envelope), and it makes the Monday session (bulk import → bulk ack → bulk
  categorize) actually work.
- **Learning (explicitly phase 2, not now):** choosing a category could offer "always
  categorize this payee as X" → appends a `bank.rules` entry. That needs a CLI writer
  (`bob bank rule --from-row` or similar) plus hub-config guarded write + commit
  policy — real scope. Ship prompt-first, log payee→category pairs, and let the logged
  data justify the rules-writer later. Do not auto-create rules from single choices
  (one coffee shop is not a policy).
- **Beautiful details:** group hints — digits for the first 10 (most-used order =
  declared order, and tell Bryan to put his top-10 first in `bank.md`), letters after;
  show each category's month-to-date share next to it (from cached report JSON — the
  data service already holds it) so the picker doubles as a spending glance; dim
  built-ins that don't apply to outflows. Keep it one glance, no scrolling for ≤18.

## Out-of-scope / deliberately not recommended

- **No auto-categorization heuristics** beyond existing tiers. The sample shows why:
  with 7 rows and no history, any guesser would misfile. Rules + learned payees +
  one-keypress human triage is the whole system; ML is toil in a trench coat.
- **No per-row due dates, budgets, or pending-transaction support** — all listed as
  current limits in `docs/bank.md`; this proposal doesn't reopen them.
- **No new top-level `bob bank` subcommand for the modal** — the source-note flow
  needs no CLI change at all; only `ack --cat` (additive flag) for the bulk flow.

## Recommended solution (phased)

1. **Vault + docs (no code, immediate):** merge the two PRE chores into one weekly
   "Bank session" chore with the WF Sign On link; delete the daily chore; teach the
   3-click download path in the guide. Add `debt: 💸 Debt` to `bank.categories`.
2. **Plugin (the feature):** `Ctrl+Enter` tick → jump to next waiting row (same-day →
   later-day, stop-with-notice at end); if the ticked row lacks `[cat::]`, open the
   one-keypress category card (declared order, `1–9/0/a–z` hints, filter, Enter/Esc);
   guarded single-transaction write; categorized rows tick silently.
3. **CLI (additive):** `bob bank ack --cat KEY` for the queue-card/bulk flow; same
   validation and exit codes as existing ack refusals.
4. **Later (data-justified):** payee→category log → `bank.rules` writer; payee-cleaner
   extension for `PURCHASE … CARD NNNN` noise; card-number masking in note rows.

Success looks like: Monday session = download, import, walk 7 rows with ~7 keypresses,
write the surprise line, done; `report` breakdowns stop bleeding into Unclassified;
mid-week purchases still typeable by hand; nothing new to memorize (declared order is
the shortcut order).
