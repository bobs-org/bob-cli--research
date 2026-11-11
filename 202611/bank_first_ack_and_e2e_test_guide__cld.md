# Bank: your first acknowledgment tomorrow, and an end-to-end test of `bob-cli-kd`

*Researcher cld · written Wed 2026-11-11, about 15:45 EST · for Thu 2026-11-12 and Mon 2026-11-16*

## Bottom line

- **Tomorrow's ritual works with no new code.** `bank.md`, `bank/2026-11.md`, and the
  `#gtd #pre` **Acknowledge bank** chore (scheduled 2026-11-12) are already in the vault.
  The installed `bob` already has `bob bank`, `check`, `report`, `ensure`, and `ack`.
- **Day one has one twist.** The account `start` is **Wed Nov 11**, not the 12th. Type
  anything that posted on Nov 11 under the `## Wed Nov 11` heading that's already there.
  Type today's rows under `## Thu Nov 12`. Never type anything dated before Nov 11.
- **Most of the epic was still landing today.** `import` (kd.4), balance proof (kd.5),
  and the Obsidian cards and guards (kd.6) are in progress. Spend two minutes checking
  what landed overnight (§1), then run only the tests whose phase has shipped (§3).
- **Test writes in a sandbox, not in your vault.** Appendix A builds a throwaway vault
  with its own Git remote, its own sync lock, and synthetic QFX files. I ran the
  sandbox and all of Step A against the installed `bob`, so those expected outputs are
  observed. The B–D expectations come from the contract.
- **One real bug is already filed.** When `ensure` adds a new day heading, it moves the
  previous day's trailing prose, checklist lines, and stubs into the new day (§5.1).
  It's recorded as a `DISCOVERED ISSUE:` on `bob-cli-kd`. Until it's fixed, keep notes
  on the row (`-- note`) or as an indented child bullet.

## 0. What exists right now

| Phase | Bead | State | What it gives you tomorrow |
| --- | --- | --- | --- |
| bank-restart | kd.1 | ✓ closed | `bank.md` (checking only, `start: 2026-11-11`), `bank/2026-11.md` with `## Wed Nov 11`, `bank_month.md`, the PRE chore `gtd_daily ^acknowledge-bank`, and `cash ^daily-bank-records-again` cancelled as "superseded by". `bob.md ^bank-records` is still open for you to close. |
| bank-grammar | kd.2 | ✓ closed | `bob bank check` |
| bank-cli | kd.3 | ✓ closed | `bob bank` (list), `report`, `ensure`, and `ack`. All are installed (`~/.cargo/bin/bob`, bob 0.5.0, built 15:27 EST). |
| bank-import | kd.4 → kd.4.1 | ◐ 1 of 4 child phases done | The parser and journal landed (`bffbf36b`). The `bob bank import` command and the Monday chore have **not** landed yet. |
| bank-balance | kd.5 | ◐ blocked on kd.4 | Every account reads `unverified`. There's no `import -F` yet. |
| bank-obsidian | kd.6 → kd.6.1 | ◐ 1 of 5 child phases done | Only the data service is deployed. `bob-bank` fences render as **plain code blocks**. There's no Enter continuation, no **Bank: open today**, no `$`-math guard, and no task-gesture guard yet. |
| bank-wrapup | kd.7 | ◐ blocked on kd.5 and kd.6 | The agent's own walkthrough in a temp vault, `docs/guides/acknowledge-bank-transactions.md`, and the glossary strands. |

## 1. First thing tomorrow (2 minutes): see what landed

Run these on the Mac, plus any host where you'll run `bob`:

```sh
sase bead show bob-cli-kd                       # which phases are ✓ now
cd <your bob-cli checkout> && just install-all  # pulls and installs bob, plugins, and Mac capture; restarts Obsidian
bob bank --help | grep -q '^  import' && echo "import: shipped"
bob bank import --help 2>/dev/null | grep -q -- '-F' && echo "balance restore (-F): shipped"
```

Then, in Obsidian, open `bank/2026-11`. A drawn month card means kd.6's cards are
deployed; a raw ```` ```bob-bank ```` block means they aren't. Also check the command
palette for **Bank: open today**.

## 2. Your first acknowledgment (Thu Nov 12, about 5 minutes the first time)

`bob freshness list` for tomorrow already shows the chore in **PRE**. It's unstaged, so
`]s` reaches it after the staged init → terminal → periods → browser → sync rows.

1. **Wells Fargo app → Checking.** Read only the **Posted** list and skip **Pending**.
   A pending amount can change: a $20 tab can post as $24 with the tip, and the two
   would then show up as twins.
2. **Open the month note.** If **Bank: open today** exists, run it. Otherwise, on the
   Mac, run `bob bank ensure -D today -o`. It adds `## Thu Nov 12` after Wednesday and
   opens the note. It doesn't place the cursor, so jump to the end yourself.
3. **Type each posted row under its *posted* day.** Use the existing `## Wed Nov 11`
   for Nov 11 postings and `## Thu Nov 12` for today's. If you skip Nov 11, Monday's
   import writes those rows unticked, which is also fine. Don't type anything before
   Nov 11: import never matches a pre-start transaction, so such a row would stay
   "unmatched" forever.
4. **Check:** `bob bank check` should exit 0 with 0 errors. `bob bank report -D yesterday`
   and `bob bank report -D today` give the day's totals.
5. **Close the chore:** press **Ctrl+Enter** on the PRE row. If nothing posted, just
   complete the chore; that is the record. Never type a `$0.00` row (`bank_row_zero`).

### The grammar on one card

| You type | It means |
| --- | --- |
| `- [x] $13.71 Smashburger` | A ticked (acknowledged) outflow. `$` is required. |
| `- [x] +$1,250.00 Payroll [cat:: income]` | Money in. Only `income` or `refund` count as **In**. |
| `[cat:: dining]` | One of your 14 keys or the built-ins `income`, `refund`, `transfer`, `cash`. `transfer` never counts as spending. |
| `!!` or `⚑` | A flag (`check` lists it as info). |
| `-- with Kelly` or `— with Kelly` | A note on the row. |
| an indented `  - …` under a row | A free note that stays with the row. |
| `- [ ] …` | Waiting, meaning imported and not yet seen. You tick it, or `bob bank ack`. |
| `**$4.10**`, `−$5`, `$1,250` | All valid input. bob writes `$4.10`. |

### Habits for tomorrow, until kd.6's guards land

- **Ticking.** Obsidian's own list continuation inserts `- [ ] `. Either change it to
  `[x]` as you type, or leave the rows unticked and run `bob bank ack -D today` at the
  end. That shortcut is safe **only before your first import**: after that, `ack -D`
  would also tick imported rows you haven't looked at.
- **Task gestures.** Don't use Ctrl+Enter or status-cycler keys *on bank rows*. If one
  slips through, `bob bank check` reports `bank_row_status` or `bank_row_task`.
- **Where notes go.** Put a note on the row or in an indented child bullet, never as an
  unindented line after a day's last row (bug §5.1).
- **Dollar signs in notes.** Avoid a second `$` inside a row's note until the
  `$`-as-math guard ships.

## 3. End-to-end test plan

**How the test is split.** All write and edge cases run in the Appendix A sandbox,
which has synthetic data, its own `master` branch and bare remote, and its own sync lock
and state, so it never touches `~/bob` or blocks the real sync. Your real vault is used
only for the UI and for the one real-file check (§3E).

**Setup.** Save Appendix A, run `bash bank-e2e-sandbox.sh /tmp/bank-e2e`, then
`source /tmp/bank-e2e/env` in a **dedicated terminal**. That env sets `BOB_DIR`, so
every `bob` command in that shell targets the sandbox. Close the terminal when you're
done, then `rm -rf /tmp/bank-e2e`.

**Variables.** `F=$BOB_DIR/bank/2026-11.md`, `Q=/tmp/bank-e2e/qfx`, and set
`export BOB_NOW=…` per step.

### A. Grammar and CLI (works today; I ran all of it on 2026-11-11)

```sh
export BOB_NOW=2026-11-12T08:00:00
bob bank ensure -D yesterday            # → "Created bank/2026-11.md" and "bank/2026-11.md:16"
cat >> "$F" <<'EOF'

- [x] $13.71 Smashburger [cat:: dining]

## Thu Nov 12

- [x] $20.00 Joe's Bar [cat:: dining] -- tab; tip not in yet
- [x] $
- [x] $5.00 Parking
- [x] **$4.10** Coffee cart [cat:: coffee] !! charged twice?
- [x] $42.00 Dog walker [acct:: wallet]

## Sat Nov 14

- [x] $5.00 Parking
EOF
bob bank ensure -D 2026-11-13   # → "Created heading Fri Nov 13", inserted between Thu and Sat
bob bank ensure                 # idempotent → prints "bank/2026-11.md:25" (after Thu's last row)
bob bank check                  # → 1 info (bank_flagged, Coffee cart), "0 errors, 0 warnings", exit 0
bob bank report -D 2026-11-12   # → Out $29.10 · Cash traced $42.00 (the wallet row is not in Out) · 1 ⚑
bob bank report -w 2026-W46     # → Out $47.81
```

| # | Do | Pass if |
| --- | --- | --- |
| A1 | The block above | The outputs match the comments. The `- [x] $` stub raises no finding. |
| A2 | Change `dining`→`dinning`, `[cat::`→`[cta::`, `$5.00`→`$5.001`, and `[x]`→`[/]` on four rows, then run `check`, then revert | Exit 1, with `bank_category_unknown` (with a hint), `bank_field_unknown` ("did you mean cat, acct?"), `bank_row_unparsed`, and `bank_row_status`. Each names `path:line`. |
| A3 | Add `- [ ] $3.00 Typed waiting` under Thu. Run `bob bank`, then `bob bank ack -d -D 2026-11-12`, then `bob bank ack -D 2026-11-12`, then `bob bank ack deadbeef` | You see "1 to acknowledge"; the dry run writes nothing; the row ticks; the unknown ID exits **2** and changes nothing; `git -C $BOB_DIR log` shows no new commit (ack doesn't commit). |
| A4 | `bob bank report -m 2026-11` and `-f json` | Exact cents, `schema_version: 1`, `accounts[].status` = `unverified` (checking) and `untracked` (wallet). |

### B. Import (needs kd.4)

| # | Do | Pass if |
| --- | --- | --- |
| B1 | `export BOB_NOW=2026-11-16T08:00:00; bob bank import -d $Q/week1.qfx` | Exact diffs print. Afterwards there are no new rows and no `.bob/bank/`. |
| B2 | `bob bank import $Q/week1.qfx` | **9 new · 1 matched · 0 seen · 1 ambiguous · 1 before start**. The last commit is `bank: import 9 rows (checking)`. The ledger balance is $2,003.79 as of Nov 16. (The pre-sync first commits your pending edits as an ordinary `vault(…)` commit; that's expected.) |
| B2a | Inspect `$F` | The Smashburger row is byte-identical, still `[x]`, plus ` ^bank-xxxxxxxx`. There are **two** `$4.25 7-Eleven` rows on Nov 11. `$24.00 Joes Bar` is waiting next to your $20 row. `ATM withdrawal [cat:: cash]`. Venmo and the Chase autopay carry `[cat:: transfer]`, the autopay under a new `## Mon Nov 16`. Payroll is `+$1,250.00` **with no category**. One waiting `$5.00` City Parking sits under Fri Nov 13 (the tie isn't guessed). Nothing on Nov 10. The ATM fee is `[cat:: fees]` if the built-in recognizes the wording; note which. |
| B2b | `grep -c 'SYN90\|0000000000' $BOB_DIR/.bob/bank/*.jsonl` | `0`: no bank IDs or account numbers are stored. |
| B3 | Run `import week1.qfx` again | 0 new, and `git log -1` doesn't change. |
| B4 | Run `bob bank`, then `bob bank ack <8-hex id of the ATM row>`, then `bob bank ack -D 2026-11-11` | Only those rows tick. |
| B5 | Rename the waiting `Joes Bar` row to `$24.00 Joe's Bar [cat:: dining]`, tick it, and delete your typed `$20.00 Joe's Bar` (twins never merge; you choose) | `check` is clean. |
| B6 | `export BOB_NOW=2026-11-23T08:00:00; bob bank import $Q/week2.qfx` | **2 new**: ShopRite on Nov 18, and the Nov 19 row arriving as `$18.00 Joe's Bar [cat:: dining]` (learned from your rename). Everything else is seen. The commit is `bank: import 2 rows (checking)`. |
| B7 | `bob bank import $Q/bad.qfx` | Exit **2**. The error names the file and the `TRNAMT` record, and `git status` and the journal are unchanged. |

### C. Balance proof (needs kd.5; continue from B6)

| # | Do | Pass if |
| --- | --- | --- |
| C1 | `bob bank`, then `bob bank check` | `WF Checking ✓ balanced · Nov 23`. `check` raises no errors. It lists `bank_row_unmatched` for Coffee cart and both typed Parking rows, `bank_twins` for the Parking pair, and nothing for the wallet row. |
| C2 | Delete the ShopRite row, then `check`, then `import week2.qfx`, then `import -F week2.qfx` | `Δ` and `bank_row_missing`. The plain import does **not** re-add the row. `-F` restores it and reports it, and the status is back to ✓. |
| C3 | Change Payroll to `+$1,200.00`, run `check`, then revert | `bank_amount_edited` |
| C4 | `BOB_NOW=2026-12-05T08:00:00 bob bank` | `⚠ … 12 days ago` stale. It never says an unqualified "nothing to acknowledge". |
| C5 | `export BOB_NOW=2026-12-07T08:00:00; bob bank import $Q/week4.qfx` | Status `gap` and `bank_coverage_gap` for Nov 24–29, even though the balance itself holds. |

### D. Obsidian (needs kd.6; real vault, your own rows)

| # | Check | Pass if |
| --- | --- | --- |
| D1 | `bank/2026-11` month card | It shows the header, status chip, Out/In/Net, category bars, and a Monday-first heat strip with today outlined. Only months that exist are links (there's no "‹ Oct" link). |
| D2 | `bank.md` queue card | `✓ nothing to acknowledge` **with** the account caveat (`unverified`). |
| D3 | Today's daily note | One quiet `🏦 out $… · in +$… · N to acknowledge` chip after the day strip. Clicking it ensures the day and jumps there. Yesterday's note has no "to acknowledge". |
| D4 | **Bank: open today**, Enter, `[cat:: ` | The cursor lands at the next-row slot. Enter after a row gives `- [x] $`, and Enter on a stub clears it. Categories are suggested in declared order. |
| D5 | Row styling | Amounts are right-aligned and tabular, inflows green with `+`, with category and ⚑ chips. Raw text shows on the cursor line. `toggle-bank-marks` turns all of it off. There's no math rendering in Reading view. |
| D6 | Guard: add `- [ ] $1.00 Guard test`, press Ctrl+Enter, try the cycler keys, then delete the line | Only `[ ]`↔`[x]` changes, with no `#task` and no `[completion::]`. `check` stays clean. |
| D7 | After Monday's import: the queue card's row checkbox and **✓ Acknowledge day** | Only the drawn rows tick, and a row that arrives after the card was drawn stays waiting. |

### E. Real vault

| # | Do | Pass if |
| --- | --- | --- |
| E1 | After tomorrow's rows: `bob freshness list \| grep -c 'bank/'` and `bob task archive -n \| grep -c 'bank/'` | Both print `0`: bank rows are invisible to task tooling. |
| E2 | **Mon Nov 16, the first real import (needs kd.4).** On wellsfargo.com (desktop), open Checking → **Download Account Activity**. Set *From* to any date on or before Nov 11 (the default range is 90 days), choose **Quicken (QFX)**, and download. Then run `bob bank import -d ~/Downloads/<file>.qfx` | The account resolves to checking and the window starts on or before Nov 11. A nonzero "before start" count is fine. The printed balance equals WF's **ledger (posted) balance, not the available balance**. |
| E3 | Run the real import **on the Mac only**, tick what it wrote, then delete the QFX from Downloads | `git -C ~/bob log -1` shows `bank: import N rows (checking)`. Grepping `.bob/bank/*.jsonl` for your account number returns 0. From the second import on: `✓ balanced`. |

E2 is the one test no agent can run for you: the plan names "the real Wells Fargo QFX
shape differs from the fixtures" as its top risk. Share counts only, never real rows.

## 4. Pass criteria, mapped to the epic's success criteria

| Success criterion (plan) | Proven by |
| --- | --- |
| You acknowledge daily via the PRE chore, in the final grammar, and the old task is retired | §2, A1–A3, E1 |
| `bob bank` shows what's waiting, and `report` gives exact cents (transfers net out, and a credit alone isn't income) | A1, A4, B2a |
| The Monday import writes only what you missed, each row exactly once | B2–B7, E2–E3 |
| `check` shows ✓ balanced from the second import on, and names gaps, staleness, deletions, and edits | C1–C5, E3 |
| Month card, queue card, and daily chip, with every number drawn rather than written | D1–D7 |
| The subscriptions album, later views, and feed spike exist as proposed follow-ups | `sase bead show bob-cli-kd.7` notes (wrap-up) |

## 5. What I found while preparing this (installed bob 0.5.0, synthetic data)

1. **Bug: `ensure` splits a day's section.** It inserts the new heading after the
   previous day's last row block (`day_end_line`, `src/native/bank/month.rs:300`),
   not at the end of that day's section. So trailing prose, a plain checklist line, or
   an empty `- [x] $` stub moves under the new day. `check` stays silent, and the
   reported next-row line points at the moved text. Ensure, the daily-chip click, and
   any import path that reuses `plan_insert_day` are all exposed. I recorded the
   reproduction as a `DISCOVERED ISSUE:` note on `bob-cli-kd`; I created no task,
   following bead policy for active epics.
2. **Net loses its minus sign.** A spending day prints `Net $116.49` while JSON says
   `net_cents: -11649`. That follows the row convention (no sign means out), but it
   reads as positive. Decide whether you want `−$116.49`.
3. **A refused `ack` still prints a check mark.** `bob bank ack <unknown>` prints
   `✓ Acknowledged 0 rows`, then the unknown list, and exits 2. That's a cosmetic
   mismatch.
4. **Some typos get no suggestion.** `[cat:: grocery]` gets no hint, while `carr` →
   "did you mean car, cash?". The suggestion distance looks too tight for a plural.
5. **The empty state teaches a command that doesn't exist yet.** It says
   `bob bank import ~/Downloads/*.qfx`, but the installed binary has no `import` until
   kd.4 lands.
6. **Human columns aren't padded.** The `list` payee and category columns, and the
   `report` breakdown rows, don't align the way the plan's samples do. Cosmetic.
7. **A small template inconsistency.** A fresh note ends right after its day heading,
   while an inserted heading gets a trailing blank line. It only matters when you
   append text with a script.

Items 2–7 are for you to accept or bead. Item 1 belongs to whoever lands next in
the bank epic.

## Appendix A: `bank-e2e-sandbox.sh`

I ran this on apollo. Before an import ships, I confirmed that `vault-sync` works against
the sandbox's bare remote with the isolated lock and state files. It creates only
synthetic data and refuses to overwrite an existing directory.

```bash
#!/usr/bin/env bash
# Throwaway bank vault + synthetic Wells Fargo-shaped QFX files. No real data.
# Usage: bash bank-e2e-sandbox.sh [DIR]   (DIR must not exist; default /tmp/bank-e2e)
set -euo pipefail
SB=${1:-/tmp/bank-e2e}
[[ -e $SB ]] && { echo "refusing: $SB exists" >&2; exit 1; }
V=$SB/vault Q=$SB/qfx
mkdir -p "$V" "$Q"
cat > "$V/bank.md" <<'EOF'
---
parent: "[[cash]]"
type: "[[area]]"
bank:
  accounts:
    checking:
      label: WF Checking
      kind: checking
      start: 2026-11-11
    wallet:
      label: Wallet
      kind: cash
  categories:
    groceries: 🛒 Groceries
    dining: 🍽️ Dining
    coffee: ☕ Coffee
    car: 🚗 Car
    fees: 🧾 Fees
  rules:
    - match: VENMO
      cat: transfer
---

# 🏦 Bank
EOF
git init -q -b master "$V"
git init -q --bare "$SB/remote.git"
git -C "$V" remote add origin "$SB/remote.git"
git -C "$V" add -A
git -C "$V" commit -qm "sandbox: bank.md"
git -C "$V" push -q -u origin master
cat > "$SB/env" <<EOF
export BOB_DIR=$V
export BOB_VAULT_SYNC_LOCK_FILE=$SB/sync.lock
export BOB_VAULT_SYNC_STATE_FILE=$SB/sync.json
export BOB_VAULT_SYNC_NOTIFY=0
EOF

# qfx FILE DTSTART DTEND BALAMT DTASOF "FITID|YYYYMMDD|AMOUNT|NAME"...
qfx() {
  local f=$1 s=$2 e=$3 bal=$4 asof=$5 t id d amt name ty; shift 5
  {
    printf 'OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nSECURITY:NONE\nENCODING:USASCII\n'
    printf 'CHARSET:1252\nCOMPRESSION:NONE\nOLDFILEUID:NONE\nNEWFILEUID:NONE\n\n'
    printf '<OFX>\n<BANKMSGSRSV1>\n<STMTTRNRS>\n<STMTRS>\n<CURDEF>USD\n<BANKACCTFROM>\n'
    printf '<BANKID>000000000\n<ACCTID>0000000000\n<ACCTTYPE>CHECKING\n</BANKACCTFROM>\n'
    printf '<BANKTRANLIST>\n<DTSTART>%s\n<DTEND>%s\n' "$s" "$e"
    for t in "$@"; do
      IFS='|' read -r id d amt name <<<"$t"
      if [[ $amt == -* ]]; then ty=DEBIT; else ty=CREDIT; fi
      printf '<STMTTRN>\n<TRNTYPE>%s\n<DTPOSTED>%s120000.000[-5:EST]\n<TRNAMT>%s\n' "$ty" "$d" "$amt"
      printf '<FITID>%s\n<NAME>%s\n</STMTTRN>\n' "$id" "$name"
    done
    printf '</BANKTRANLIST>\n<LEDGERBAL>\n<BALAMT>%s\n<DTASOF>%s\n</LEDGERBAL>\n' "$bal" "$asof"
    printf '</STMTRS>\n</STMTTRNRS>\n</BANKMSGSRSV1>\n</OFX>\n'
  } > "$f"
}
W1=(
  "SYN9001|20261110|-25.00|SHOPRITE #123"            # before start: never written
  "SYN9002|20261111|-13.71|SQ *SMASHBURGER"          # matches your typed row
  "SYN9003|20261111|-4.25|7-ELEVEN #4567"            # two identical purchases,
  "SYN9004|20261111|-4.25|7-ELEVEN #4567"            #   both must survive
  "SYN9005|20261112|-24.00|TST* JOES BAR"            # your typed $20 tab posts at $24
  "SYN9006|20261112|-63.50|ATM WITHDRAWAL"           # built-in: cash
  "SYN9007|20261112|-3.50|NON-WF ATM FEE"            # built-in: fees (if recognized)
  "SYN9008|20261113|-5.00|CITY PARKING"              # equidistant tie: ambiguous
  "SYN9009|20261113|1250.00|ACME CORP PAYROLL"       # a credit alone is never income
  "SYN9010|20261113|-8.00|VENMO PAYMENT"             # bank.rules: transfer
  "SYN9011|20261116|-120.00|CHASE CRD AUTOPAY"       # built-in: transfer
)
W2=("${W1[@]}"
  "SYN9012|20261118|-61.20|SHOPRITE #123"
  "SYN9013|20261119|-18.00|TST* JOES BAR"            # should arrive with your learned name
)
qfx "$Q/week1.qfx" 20261102 20261116 2003.79 20261116 "${W1[@]}"
qfx "$Q/week2.qfx" 20261109 20261123 1924.59 20261123 "${W2[@]}"
qfx "$Q/week4.qfx" 20261130 20261207 1914.60 20261207 "SYN9015|20261201|-9.99|SPOTIFY USA"
qfx "$Q/bad.qfx"   20261102 20261116 2003.79 20261116 "${W1[@]}" "SYN9099|20261114|-1.234|BAD AMOUNT"
echo "sandbox ready: source $SB/env"
```

The balances work out to an anchor of **$1,000.00** at the start of Nov 11.
week1's net is +$1,003.79, which gives $2,003.79. week2 adds −$79.20, giving
$1,924.59. week4 adds −$9.99, giving $1,914.60. week4 deliberately skips Nov 24–29 to
trigger `gap`. The fixture shape copies the SGML test fixture in
`src/native/bank/source.rs`. I couldn't run these files through `import` because the
command hasn't shipped. If B2 refuses one of them, run `-f json` to see the field it
names. That's a fixture bug, not necessarily an import bug.

## Sources

- **Epic and phase beads:** `bob-cli-kd`, `.1`–`.7`, `.4.1`, `.6.1`, and the closed
  child notes `.4.1.1` and `.6.1.1`, read with `sase bead read`.
- **Plans:** `plan:202611/bank_daily_acknowledgment.md` (contract, acceptance cases,
  success criteria), `plan:202611/bank_import.md`, and `plan:202611/bank_obsidian.md`.
- **Research:** `research:202611/bank_daily_acknowledgment/bank_daily_acknowledgment.md`,
  sections "The daily and weekly rhythm" and "Getting transactions in".
- **Code and docs at `8134d173`:** `docs/bank.md`, `src/native/bank/{month,source,grammar,output}.rs`,
  `src/native/host_catalog/txn.rs` (`run_locked`: vault identity, Git worktree,
  pre-sync), and `docs/guides/run-morning-review.md`.
- **Live vault (read-only):** `bank.md`, `bank/2026-11.md`, `gtd_daily.md:12`,
  `cash.md:192`, `bob.md:46`, `BOB_NOW=2026-11-12T07:00:00 bob freshness list`, and
  `bob bank` / `check` / `report`. All showed 0 rows, `unverified`, and 0 findings.
- **Wells Fargo download:**
  - [Account Activity (default 90 days, up to 18 months)](https://www.wellsfargo.com/biz/online-banking/deposit-details/)
  - [Web Connect](https://wellsfargo.com/online-banking/software/web-connect)
  - [Ledge how-to (the Download Account Activity link and date range)](https://docs.ledge.co/how-to-guides/how-to-guide-generating-wells-fargos-account-activity-report)

  The consumer menu labels may differ slightly from these business pages.
