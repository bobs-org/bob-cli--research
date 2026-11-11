# First bank ack tomorrow, and an end-to-end test of `bob-cli-kd`

> **Research query.** Write a concise user guide that walks Bryan through
> acknowledging bank transactions for the first time tomorrow and end-to-end
> testing epic `bob-cli-kd`.
>
> **Researcher.** `grk` (independent swarm report).
> **Date.** 2026-11-11 (ritual day is **Thu 2026-11-12**).
> **Scope.** Research only. This file is the deliverable. No vault, bob-cli,
> plugin, or memory files were changed.

**Primary evidence.** Bead `bob-cli-kd` and children; plan
`plan:202611/bank_daily_acknowledgment.md`; `docs/bank.md`; generated CLI
help; live `bob 0.5.0` against `~/bob`; a throwaway-vault CLI walk (output
below); `BOB_NOW=2026-11-12 bob freshness`; vault notes `bank.md`,
`bank/2026-11.md`, `gtd_daily.md ^acknowledge-bank`.

---

## Bottom line

Tomorrow morning the habit is already in the PRE walk. Open the Wells Fargo
app, ensure Thursday's heading, type every posted checking row since
**2026-11-11** as a ticked line in `bank/2026-11.md`, then complete the chore.
That is the first acknowledgment.

`bob bank import` is **not** on PATH yet (`unrecognized subcommand 'import'`
on `bob 0.5.0`). Obsidian cards, the daily chip, Enter continuation, and
row guards are still in `bob-cli-kd.6.1.2–5`. Type in the month note; use
the shipped CLI (`list` / `report` / `ensure` / `ack` / `check`) to prove
the row.

A full epic e2e is two sessions: the live ritual tomorrow (phases 1–3),
then wrap-up's ten-step throwaway vault once import and the plugin land.

---

# User guide

## What is ready on the machine (checked 2026-11-11 evening)

| Piece | State |
| --- | --- |
| `bob` | `0.5.0` at `~/.cargo/bin/bob` |
| Hub | `bank.md` — checking only (`WF Checking`), `start: 2026-11-11`, 14 starter categories, VENMO → transfer |
| Month note | `bank/2026-11.md` — fence + `## Wed Nov 11`, **zero rows** |
| CLI | `bob bank` → `nothing to acknowledge`; `check` → `✓ 2 notes — 0 errors, 0 warnings` |
| PRE chore | `gtd_daily.md:12` `^acknowledge-bank`, `[scheduled:: 2026-11-12]`, `[repeat:: every day when done]` |
| Walk (simulated tomorrow) | PRE 7 of 9, after init → terminal → browser → sync, before brush teeth |
| `bob bank import` | missing from `--help` |
| Plugin cards / chip / Enter / guards | not deployed (`bob-cli-kd.6.1` still in progress; `bob plugins sync` also failed on 0.5.0 `check-ignore`) |
| Origin task | `bob.md ^bank-records` stays open (PENDING tomorrow). Keep it. Completing PRE does not close it. |

Account coverage is **checking only**. Credit-card spend waits until you add
an account.

## 0. Thirty-second morning check

```bash
bob --version          # expect 0.5.0, or a newer train build
bob bank --help        # look for `import`; tomorrow it should still be absent
bob bank check         # expect ✓ 2 notes
```

If `import` appears, still **type** tomorrow. Import is the Monday net, not
the first-day gesture.

## 1. Land on the chore

Start the morning walk with `]s` (or `Ctrl+Alt+J`). PRE order is
`init → terminal → periods → browser → sync`, then unstaged chores.

1. Complete `#init Run task reconcile` first. That is what lifts
   `^acknowledge-bank` out of the date-blocked `[?]` state.
2. Work the staged PRE rows as usual.
3. Land on **Acknowledge bank**. The row text is the ritual:

   > open the Wells Fargo app · type each new posted row under its day in
   > this month's [[bank]] note (ticked) · tick any waiting rows · nothing
   > new? completing this is the record

Do the bank work **before** `Ctrl+Enter` on that row.

## 2. Open the month note on today's heading

In a terminal, or from Obsidian Command Mode (`:` then `bank ensure`):

```bash
bob bank ensure -D today -o
```

On a vault that already has November, expect:

```text
Created heading Thu Nov 12 in bank/2026-11.md
bank/2026-11.md:16
```

The printed `path:line` is where the next row goes (blank line under the
heading, or after that day's last row). `-o` opens the note in Obsidian.
The command is idempotent: a second run only reprints the line.

Command Mode names: `bank-ensure` (runs), `bank-ack` (preview-first),
`bank-list` / `bank-report` / `bank-check` (reports).

If `$13.71` turns into an equation in Live Preview, type in source mode.
Row math-guards are still in `bob-cli-kd.6.1.4`.

## 3. Type posted checking rows

Open the Wells Fargo **app**. Type every **posted** checking transaction
and deposit from **Wed Nov 11** and **Thu Nov 12**. Pending charges wait
until they post. Empty day: type nothing; completing the chore is the
record. Never write a `$0.00` row.

Put each row under its own day heading. `ensure` created Thursday;
Wednesday already exists. A first session that only fills Thursday leaves
Wednesday's posted activity waiting for next week's import.

Typed rows start **ticked**. One line:

```markdown
## Thu Nov 12

- [x] $13.71 Smashburger [cat:: dining]
- [x] $4.25 7-Eleven [cat:: coffee] — coffee on the walk
- [x] +$1,250.00 Payroll [cat:: income]
- [x] $63.50 ATM withdrawal [cat:: cash] !! fee again?
- [x] $40.00 Venmo [cat:: transfer] — rent split
```

| Bit | How to type it |
| --- | --- |
| Out | `$61.20` (no sign) |
| In | `+$1,250.00` |
| Category | `[cat:: dining]` — optional except `income`, `refund`, `transfer`, `cash` |
| Account | omit; checking is the default |
| Note | `— …` or `-- …` |
| Flag | `⚑` or `!!` |
| Restaurant | `[[eat/smashburger\|🍽️]]` when you already know the record |
| Stub | leave `- [x] $` unfinished; `check` ignores it |
| Next row | type `- [x] $` yourself (Enter continuation is still unshipped) |

Starter category keys, in declared order: `groceries`, `dining`, `coffee`,
`transit`, `car`, `home`, `utilities`, `dog`, `kids`, `health`, `shopping`,
`subscriptions`, `fun`, `fees`. Built-ins you do not have to declare:
`income`, `refund`, `transfer`, `cash`.

Skip a category when unsure. Guessing a spending cat on an inflow makes
`check` emit `bank_inflow_category` (info: use `refund` or `income`).

Rows stay free of `#task`. They are invisible to `bob plan`, freshness, and
the Tasks filter on purpose. Do not run the task-status cycler on a bank
row until `bob-cli-kd.6.1.2` deploys the guard.

`ensure` and `ack` are guarded writes with no git commit; vault-sync
carries them. Hand-typed rows are ordinary vault edits; vault-sync carries
those too. Keep the QFX, if you download one, in `~/Downloads`.

## 4. Tick waiting rows, then look

On day one there are no imported waiting rows. If you typed a row as
`[ ]` by mistake:

```bash
bob bank ack -d -D today     # preview
bob bank ack -D today        # tick every waiting row of that day
```

`ack` by day ticks typed waiting rows (no `^bank-` id required). `ack` by
id needs `^bank-<hex>` and will exist once import writes IDs. Unknown ids
exit 2 and change nothing.

Then:

```bash
bob bank              # waiting queue; day one should be "nothing to acknowledge"
bob bank list -a      # every row, ☑ and ☐
bob bank report       # month so far, bars, heat strip
bob bank report -D today
bob bank check        # ⚑ rows show as info; errors fail the run
```

Verified throwaway output (same grammar, `BOB_NOW=2026-11-12`): one waiting
ShopRite row listed as `☐ $61.20`, ATM `!!` rendered as `⚑`, payroll as
`+$1,250.00` 💵, cash-out share labelled "destination unknown", heat-strip
cell `12☐` while waiting. After `ack -D today`: `nothing to acknowledge`
plus the import hint (the hint is a stub until the command ships).

`check` on a flagged ATM row:

```text
bank/2026-11.md:20: [bank_flagged/info] flagged row ATM withdrawal
✓ 2 notes — 0 errors, 0 warnings
```

A clean first day is `✓` with 0 waiting. `WF Checking · unverified` is
expected until the first real import.

## 5. Complete the chore

Back on `^acknowledge-bank`, `Ctrl+Enter`. PRE completion stays in PRE
(`docs/guides/run-morning-review.md`). Nothing posted still completes.

Leave `bob.md ^bank-records` open. It will sit in PENDING tomorrow; keep
it until wrap-up asks you about it.

---

# End-to-end test of `bob-cli-kd`

Treat "e2e the epic" as a scorecard, not a single command. Phases 1–3 are
closed and live. 4–7 are in progress.

```text
✓ kd.1  bank-restart   vault + PRE chore     ← tomorrow's ritual
✓ kd.2  bank-grammar   check + parse
✓ kd.3  bank-cli       list/report/ensure/ack
◐ kd.4  bank-import    4.1.1 closed; 4.1.2–4 in progress; no CLI yet
◐ kd.5  bank-balance   blocked on import
◐ kd.6  bank-obsidian  6.1.1 closed (JSON); 6.1.2–5 in progress; sync broken
◐ kd.7  bank-wrapup    blocked on 5 and 6; owns the published guide
```

## Track A — live vault, tomorrow (phases 1–3)

Pass when all of these hold:

1. `BOB_NOW` unset, `]s` lands on **Acknowledge bank** during PRE.
2. `bob bank ensure -D today` inserts `## Thu Nov 12` and prints `path:line`.
3. You type at least one real posted row as `- [x] $…` (or complete with
   zero rows because nothing posted).
4. `bob bank check` is 0 errors. Info-only flags are fine.
5. `bob bank` is `nothing to acknowledge` after you tick what you meant to
   tick.
6. `bob bank report -D today` Out/In match the rows you typed, with
   transfers kept off Out/In and ATM `[cat:: cash]` in Cash out.
7. `Ctrl+Enter` completes `^acknowledge-bank`.
8. No `#task` on any bank row; `bob plan` still ignores them.

Amounts in any bead note, commit, or chat stay as **counts**, never live
payees or dollars.

## Track B — throwaway vault, any time (shipped CLI)

This is wrap-up steps 1–4. It does not touch `~/bob`. Verified on this
host with `bob 0.5.0`.

```bash
TMP=$(mktemp -d /tmp/bob-kd-e2e-XXXXXX)
export BOB_DIR="$TMP" BOB_NOW=2026-11-12

cat > "$TMP/bank.md" <<'EOF'
---
parent: "[[cash]]"
type: "[[area]]"
bank:
  accounts:
    checking:
      label: WF Checking
      kind: checking
      start: 2026-11-11
  categories:
    groceries: 🛒 Groceries
    dining: 🍽️ Dining
    coffee: ☕ Coffee
---
# 🏦 Bank
EOF

bob bank check                    # teaching? no — hub exists, 0 errors
bob bank ensure -D today          # Created bank/2026-11.md / :16
bob bank ensure -D today          # idempotent, reprints :16
# append sample rows under ## Thu Nov 12, including a [ ] row, a ⚑, a +$, a stub
bob bank check                    # info flag only
bob bank                          # 1 to acknowledge
bob bank list -a
bob bank report
bob bank report -w 2026-W46
bob bank report -D today
bob bank ack -d -D today          # Dry run — nothing written
bob bank ack -D today             # ✓ Acknowledged 1 row
bob bank                          # nothing to acknowledge
bob bank ack deadbeef; echo $?    # unknown id, exit 2, no writes
```

Empty-vault teaching state (also verified): `No bank.md yet.` plus a
paste-ready `bank:` block; `list` and `check` both exit 0.

Developer regression of the same surface, from a bob-cli checkout:

```bash
cargo test --lib native::bank
```

Phase `bank-cli` recorded 31 lib tests plus the CLI integration suite.
Workspace `src/native/bank/` already contains `source.rs` / `journal.rs` /
`identity.rs` behind `dead_code` — parsers exist, the `import` subcommand
does not.

## Track C — wrap-up's remaining ten steps (after 4–6 land)

Do this in a **new** `$TMP` with synthetic fixtures from the import
phase. Never point it at `~/bob`. Never commit a real QFX.

From `plan:202611/bank_daily_acknowledgment.md` § bank-wrapup:

5. Import a synthetic QFX twice (second run writes nothing).
6. Typed twin, $20 typed vs $24 posted, ambiguous equidistant pair.
7. Delete a row → `Δ` / `bank_row_missing` → `import -F` restores it.
8. Skip a week → `gap`; stale hint if last import is older than 10 days.
9. Two accounts plus a card payment that nets out of Out/In.
10. A malformed file refuses the whole batch (exit 2, nothing written).

Plugin proof (once `bob plugins sync` copies ledger-tools): month card on
`bank/2026-11.md`, queue card on `bank.md`, daily chip on the daily note,
Enter continues with `- [x] $`, a complete gesture on a row only toggles
`[ ]`↔`[x]`, `$` is not inline math. `kd.6.1.5` is the fixture walkthrough
that should produce that evidence.

When `bob bank import` is on PATH, the Monday PRE chore (installed by
`kd.4.1.4`) is:

> download the last 14 days as Quicken (QFX) from Wells Fargo · run
> `bob bank import ~/Downloads/*.qfx` · tick what it wrote (`bob bank`) ·
> write one line in last week's note: what surprised me?

Download that file from **wellsfargo.com** (browser), not the app:
account → **Download Account Activity** → date range covering `start`
(2026-11-11) → **Quicken Web Connect (QFX)** → `~/Downloads`. Default
window is 90 days. CSV is the fallback (`Date, Amount, *, (blank),
Description`, no header) and leaves the account `unverified`.

Next Monday is **2026-11-16**. Thursday is for typing.

---

## If something looks wrong

| Symptom | What to do |
| --- | --- |
| Chore still `[?]` under Blocked | Finish `#init` reconcile, or wait for hooks; `BOB_NOW=2026-11-12 bob freshness` already lists it as due PRE |
| `ensure` exit 2 | Invalid `-D` or broken `bank:` — `bob bank check` names file:line:key |
| `ack` exit 2 | Unknown id; nothing was written |
| Amounts become equations | Source mode until 6.1.4 |
| Checkbox becomes `[?]` / `[/]` / `#task` | Undo; `check` will flag `bank_row_status` or `bank_row_task` |
| `unverified` after typing | Expected. Status flips after import + balance |
| Import hint on an empty queue | Stub copy; the subcommand is still missing |
| Want to try a real QFX early | `bob bank import -d FILE` against a **copy** of the vault, counts only, once the command exists |

---

## Sources

- Bead `bob-cli-kd` (in progress) and closed phases `.1` `.2` `.3`; child
  epics `.4.1` (import) and `.6.1` (Obsidian).
- `plan:202611/bank_daily_acknowledgment.md` — ritual, grammar, wrap-up
  walk, reviewer decisions (`accounts = checking`).
- `plan:202611/bank_import.md` — Monday PRE chore; command still unshipped.
- `docs/bank.md`, `docs/reference/cli/bank.md`,
  `docs/reference/vault-format.md` (Bank notes),
  `docs/guides/run-morning-review.md`.
- Live vault 2026-11-11: `bank.md`, `bank/2026-11.md`,
  `gtd_daily.md:12 ^acknowledge-bank`, cancelled
  `cash.md ^daily-bank-records-again`, open `bob.md ^bank-records`.
- Live CLI: `bob 0.5.0`; `bob bank`, `check`, `report`;
  `BOB_NOW=2026-11-12 bob freshness` (PRE 9, Acknowledge bank unstaged).
- Throwaway vault `/tmp/bob-bank-e2e-*` on this host: ensure, type, check,
  list, report, ack dry-run, ack, unknown-id exit 2, teaching empty state.
- Wells Fargo download path: wellsfargo.com → Download Account Activity →
  Quicken Web Connect; 90-day default (third-party 2026 write-ups of WF
  online banking; confirm the labels on the real screen).
- Catalog: `bank-check`, `bank-list`, `bank-report`, `bank-ensure`,
  `bank-ack` in `src/native/catalog/table.rs`.
