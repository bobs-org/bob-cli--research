# Acknowledge bank transactions: first-day guide + kd end-to-end test

Research for `bob-cli-kd` (Bank — acknowledge every transaction daily, prove it
weekly). Status as observed 2026-11-11: **daily ritual is ready to start
tomorrow**; weekly import, balance proof, and Obsidian cards are still in
progress. Verified against the live CLI (`bob 0.5.0`), the real vault
(`~/bob`), the epic plan (`plan:202611/bank_daily_acknowledgment.md`), and
`docs/bank.md`, plus a scratch-vault probe of every shipped command.

## Where things stand (read this first)

| Piece | State | Evidence |
|---|---|---|
| Vault ritual (`bank.md`, `bank/2026-11.md`, daily PRE chore, retired `^daily-bank-records-again`) | Done (`bob-cli-kd.1` closed) | `~/bob/bank.md` + `bank/2026-11.md` exist; `gtd_daily.md:12` chore scheduled 2026-11-12, repeats daily |
| `bob bank check/list/report/ensure/ack` + `docs/bank.md` | Done (`bob-cli-kd.2`, `.3` closed) | `bob bank --help` lists all five; `bob bank check -b ~/bob` → 0 errors, 0 warnings |
| `bob bank import` (QFX/CSV, journal, matching) | In progress (`.4.1.1` parsers/journal closed; guarded command pending) | No `import` subcommand in CLI yet |
| Balance proof (`balanced`/`gap`/`delta`/`stale`) | In progress (phase `.5` open) | All accounts report `unverified` today |
| Obsidian month/queue cards, row styling, daily chip | In progress (`.6.1.1` data service closed; views pending; `bob plugins sync` blocked on a pre-existing `git check-ignore` failure) | No cards in vault yet |
| Guide + full e2e (`bob-cli-kd.7`) | This research feeds it | Target: `docs/guides/acknowledge-bank-transactions.md` |

Rule of thumb for tomorrow: **everything in sections 1–4 below works now.**
Anything saying `import`, `✓ balanced`, or pointing at a rendered card is
marked **coming** — do not try it yet.

## 1. What was already set up for you

- `bank.md`: hub note under `cash`, `accounts: checking` (WF Checking,
  `start: 2026-11-11`), 14 starter categories, one `VENMO → transfer` rule.
- `bank/2026-11.md`: this month's note with a `view: month` fence and one
  empty `## Wed Nov 11` heading.
- Daily PRE chore `^acknowledge-bank` in `gtd_daily.md`, scheduled from
  **2026-11-12**, repeating `every day when done`. Completing it *is* the
  record — on a no-posting day, write nothing and just complete the chore.
- Until import ships, every total and the waiting queue come from rows you
  type. Nothing else is required before tomorrow morning.

## 2. The two-minute daily ritual (starts tomorrow, Nov 12)

1. Open the Wells Fargo app, look at **posted** transactions only (pending
   ones never count — they aren't in QFX either, so typing them early only
   creates twins later).
2. Open this month's note. Shortcut that also creates a missing heading:
   `bob bank ensure -D today` (prints the file and the line where the next
   row goes). Or open `bank/2026-11.md` directly.
3. Under today's `##` heading, type one row per posting, **already ticked**
   (typed rows start acknowledged — the tick *is* the acknowledgment):
   `- [x] $13.71 Smashburger [cat:: dining]`
4. Tick any waiting `[ ]` rows from earlier days — in the note, or with
   `bob bank ack -D 2026-11-10` (one day) / `bob bank ack <id>…` (IDs are
   the `^bank-…` suffixes; already-ticked rows are a harmless no-op).
5. Complete the `Acknowledge bank` PRE chore. Optional sanity look:
   `bob bank` (waiting queue) and `bob bank check` (should be quiet).

Row cheat-sheet (full grammar in `docs/bank.md`):

```text
- [x] $13.71 Smashburger [cat:: dining]        # out, acknowledged
- [ ] $61.20 ShopRite [cat:: groceries]        # out, waiting
- [ ] +$1,250.00 Payroll [cat:: income]        # money IN needs +
- [x] $63.50 ATM withdrawal [cat:: cash] !! fee again?
- [x] $4.25 7-Eleven -- coffee on the walk     # -- is a note, like —
- [x] $13.71 Smashburger [[eat/smashburger|🍽️]] # links welcome, any order in tail
```

Remember: `$` is required (a bare number is ignored as a plain checklist
line); `+` means money in; `⚑`/`!!` flags a row to look into; categories
are optional and learned from your edits — only `transfer`, `income`,
`refund`, `cash` change the math; `[cat:: transfer]` rows and `cash`-kind
accounts never count as spending (an ATM withdrawal *does*: `cash` category
= "cash out, destination unknown"); never put `#task` on a row.

## 3. Checking your work from the terminal

- `bob bank` — the waiting queue, oldest first (this is also the bare
  default). Real probe on a scratch vault with 2 waiting rows:
  ```text
  🏦 Bank · 2 to acknowledge  WF Checking · unverified · Nov 11
  Thu Nov 12  out $61.20 · in +$1,250.00
    ☐       $61.20  ShopRite  🛒 Groceries
    ☐   +$1,250.00  Payroll   💵 Income
  Tick them in bank/2026-11.md, or: bob bank ack -D 2026-11-12
  ```
  After `bob bank ack -D 2026-11-12` → `✓ Acknowledged 2 rows`, the queue
  reads `nothing to acknowledge` and already teaches the coming import
  command. Observed, not invented.
- `bob bank report [-m 2026-11] [-w 2026-W46] [-y 2026] [-D 2026-11-12]` —
  exact-cent totals with category bars and a heat strip; at most one period,
  default this month. `Out` excludes transfers; `In` counts only
  `income`/`refund` (a bare `+` credit is *not* income — `check` nudges
  with `bank_inflow_category`).
- `bob bank check` — lint grouped by note then day; exit 1 on any error, 0
  for warnings/info/clean. Observed: a `[?]` box is `bank_row_status` error,
  a doubled day heading is `bank_day_duplicate` warning, a `$`-less line is
  silently not-a-row, and every `⚑` row is listed as `bank_flagged` info.
- `bob bank ensure [-D today|yesterday|tomorrow|YYYY-MM-DD] [-o]` —
  idempotent; creates folder/note/heading in date order; `-o` opens in
  Obsidian. `ack` (`-d` dry-run, `-f json`) and `ensure` are guarded writes
  with no commit — vault-sync carries them. Every long option has a short
  alias; `-b DIR` targets a vault; `BOB_NOW` overrides today (useful for
  backfilling). All amounts in `-f json` are signed integer `*_cents`,
  `schema_version: 1`.

## 4. Catching up after a lapse (until import ships: the manual version)

Type the missed days' rows under their day headings (create old headings by
hand or `bob bank ensure -D 2026-11-09`), ticked or waiting — your call.
One sitting clears a missed week; there is no retyping spiral because each
row is one line and `bob bank ack -D <day>` ticks a whole day at once.
Empty day? Leave the heading empty ("I looked; nothing posted") or skip it.

## 5. Monday import (coming — what it will be)

When `bob-cli-kd.4` lands: download the last ~14 days as Quicken (QFX) from
Wells Fargo, run `bob bank import ~/Downloads/*.qfx`. It writes only what
you missed as unchecked rows (typed rows it recognizes get their `^bank-…`
ID appended, staying ticked), matches within 1 day before–3 days after
posting on same account + same cents, and refuses the whole batch (exit 2,
nothing written) on a malformed file. The weekly PRE chore
(`download → import → tick → one "what surprised me?" line`) rides Monday's
weekly review, not a separate Sunday ritual. A same-QFX-twice run writes
nothing. Privacy: no account numbers stored or printed, journal keeps only
sha256 hashes plus masked descriptions, raw files never enter the vault,
fixtures stay synthetic.

## 6. Adding an account or a rule (later; safe to defer)

Edit `bank.md`: new entry under `bank.accounts` (`label`, `kind: checking |
savings | credit | cash`, `start: YYYY-MM-DD`; first account is the default
for rows without `[acct::]`), or a `{match, cat}` entry under `bank.rules`
(first match wins, applies to import-written rows only). `bob bank check`
validates with file:line:key-path diagnostics. Out of v1: budgets,
envelopes, splits, multi-currency, investments, net worth, pending
transactions, cloud categorization.

## 7. What the statuses mean

`unverified` (everywhere today: "no import yet") → after balance ships:
`balanced` ✓ · `delta` (shows `Δ $N` + suspects; a deleted row stays
deleted until deliberate `import -F`) · `gap` ("download a longer window")
· `stale` (older than `stale_after`, default 10 days) · `untracked` (cash
accounts only). The queue never claims "all caught up" while any account is
stale, gapped, or delta'd. `✓ balanced` also retires the 30-day
`cash.md ^balance` snapshot chore to optional.

## 8. End-to-end test for the kd bead (for `bob-cli-kd.7`)

Run in a temp vault so the real vault is untouched:
`export BOB_DIR=$(mktemp -d) BOB_NOW=2026-11-12`. Steps 1–4, 7(partly),
9–10 run today; the rest gate on their phases.

1. `bank.md` (contract template) + `bob bank ensure` → note + today's
   heading; rerun is a no-op. ✅ observed.
2. Type rows incl. a stub (`- [ ] $`), a `!!` flag, a `--` note, a
   cash-account row → `check` quiet except `bank_flagged` info; stub yields
   no finding. ✅ observed.
3. `list` / `report` month + week + day; verify Out/In/Net, transfer
   separation, credit≠income, integer cents. ✅ observed (day report).
4. `ack` by IDs and by day; unknown ID → exit 2, nothing changes. ✅
   observed (day ack); ID-unknown path per contract, unobserved.
5. Import synthetic QFX twice → second run writes nothing, review state
   unchanged. ⏳ needs `.4` command.
6. Typed twin gets ID appended, stays ticked; $20-typed/$24-posted pair
   written waiting + listed as possible twins; equidistant tie written new,
   never guessed. ⏳ needs `.4` + `.5` twins.
7. Delete an imported row → `Δ` + `bank_row_missing`; `import -F` restores
   deliberately, never duplicates. ⏳ needs `.5`.
8. Skip a week → `gap`, no unqualified "caught up". ⏳ needs `.5`.
9. Two accounts + card payment netting out; transfers excluded from Out/In.
   ⏳ needs `.4` `-a` resolution (config part works today).
10. Malformed file → whole batch refused, exit 2, zero writes. ⏳ needs `.4`.
11. Obsidian: month card (bars, heat strip, prev/next nav), queue card
    (per-row ack = only drawn IDs; per-day ack), daily chip, Enter
    continues `- [x] $`, task gestures can't corrupt rows, `$` never renders
    as math. ⏳ needs `.6`.
12. Docs audit (`docs/bank.md`, guide, vault-format, json-outputs,
    vault-git-sync, CLI reference, plugin page) + `just docs-check`; real
    vault `check`/`list`/`report` pasted with amounts redacted to counts;
    memory: only `glossary:bank-month-note` + `glossary:bank-row` authorized
    (bank-rows-not-records decision explicitly declined); follow-ups filed:
    subscriptions album (depends on `bob-cli-k3`, discretionary scope),
    later views after 2–4 week trial, feed spike only if download is the
    friction.

## 9. Notes and risks for the lead

- Small doc wrinkle: post-ack `bob bank` already teaches
  `bob bank import ~/Downloads/*.qfx`, which doesn't exist yet — correct
  anticipation, but a first-day user who follows it gets `unknown subcommand`.
  Consider hiding that hint until `.4` ships, or landing import help early.
- `docs/bank.md` correctly says "`check`, `list`, `report`, `ensure`, and
  `ack` ship now; `import` ships in a later phase" — the guide above mirrors
  that split; the wrapup guide must keep it until import lands.
- Real vault is clean (`check`: 2 notes, 0 errors, 0 warnings) with the
  `Wed Nov 11` heading awaiting its first rows.
- Trial targets (product goals, not findings): median daily session ~3 min,
  one-sitting weekly catch-up, `✓ balanced` Mondays, one observation/week.
  If typing dominates → feed spike earlier; if categorizing dominates → drop
  categories from the chore.
