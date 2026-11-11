# Bank Transactions First Acknowledgment & E2E Testing Guide (`bob-cli-kd`)

**Author:** Researcher `gem`  
**Date:** 2026-11-11  
**Target Date (Tomorrow):** 2026-11-12 (Thursday)  
**Epic Bead:** `bob-cli-kd` (Bank — acknowledge every transaction daily, prove it weekly)  
**Scope:** Actionable user guide for tomorrow's first live bank acknowledgment ritual, paired with a comprehensive protocol for end-to-end testing the entire `bob-cli-kd` epic.

---

## Executive Summary

The `bob-cli-kd` epic re-establishes Bryan's daily bank awareness habit while eliminating historical failure modes:
1. **The habit is decoupled from code:** Phase 1 (`bob-cli-kd.1`) already established `bank.md`, `bank/2026-11.md`, and scheduled the daily `#gtd #pre` chore `^acknowledge-bank` for tomorrow (`2026-11-12`).
2. **Typing acknowledges immediately:** Hand-typed rows start ticked (`- [x] $...`), taking roughly two minutes during morning review.
3. **Weekly safety net:** Weekly QFX import (`bob bank import`) fills in missed rows without duplicating typed ones, proving 100% coverage via balance checks (`bob bank check`).
4. **Totals are drawn, never stored:** Math is computed dynamically at query time (`bob bank report`), ensuring zero out-of-sync state.
5. **Obsidian integration:** Obsidian `bob-ledger-tools` renders dynamic month and queue cards (`view: month`, `view: queue`) and daily note chips without treating bank rows as tasks.

---

# Part 1: First-Time Bank Acknowledgment Guide (Tomorrow, Nov 12)

Tomorrow morning (2026-11-12) marks the restart of your daily bank acknowledgment ritual. Here is exactly what you need to do.

### 1.1 The Ritual at a Glance
- **When:** During your morning review (`gtd_daily.md` `#gtd #pre` checklist).
- **Time Required:** ~2 minutes.
- **Where:** `bank/2026-11.md` under heading `## Thu Nov 12`.
- **Primary Tool:** Obsidian or terminal (`bob bank`).

---

### 1.2 Step-by-Step Morning Walkthrough

#### Step 1: Open the Daily Chore
In your morning review walk or `gtd_daily.md`, locate the pre-scheduled chore:
```markdown
- [?] #task #gtd #pre **Acknowledge bank**: open the Wells Fargo app · type each new posted row under its day in this month's [[bank]] note (ticked) · tick any waiting rows · nothing new? completing this is the record [repeat:: every day when done] [created::2026-11-11] [scheduled::2026-11-12] ^acknowledge-bank
```

#### Step 2: Navigate to Today's Bank Section
Choose whichever path fits your workflow:
- **Via CLI:** Run:
  ```bash
  bob bank ensure -D today -o
  ```
  This creates the `## Thu Nov 12` heading if missing, opens the note in Obsidian, and reports the exact insertion line.
- **Via Obsidian Command Palette:** Trigger `Bank: open today`.
- **Via Daily Note:** Click the quiet bank chip (`out $0.00 · in +$0.00`) mounted inside today's `bob-plan` block.
- **Direct Navigation:** Open `bank/2026-11.md` in Obsidian and scroll to `## Thu Nov 12`.

#### Step 3: Check Wells Fargo
Open the Wells Fargo app or web portal on your phone or browser:
- Focus **only on posted transactions and deposits** since yesterday (Nov 11).
- **Ignore pending transactions.** Pending amounts fluctuate and may drop or post differently; only posted items count.

#### Step 4: Type Each Posted Item
Under `## Thu Nov 12`, enter each posted transaction as a top-level checkbox list item.

> **Key Rule: Typed rows start ticked (`- [x]`)!**  
> Typing the row is your conscious act of acknowledgment. You do not need to acknowledge it a second time.

**Syntax Reference & Examples:**

1. **Standard Expense (Outflow):**
   ```markdown
   - [x] $13.71 Smashburger [cat:: dining]
   - [x] $64.12 ShopRite [cat:: groceries]
   ```
2. **Deposit / Income (Inflow):**
   Use an explicit `+$`:
   ```markdown
   - [x] +$1,250.00 Payroll [cat:: income]
   - [x] +$25.00 Venmo Cashout [cat:: transfer]
   ```
   *(Note: Credits alone do not count as income; always use `[cat:: income]`, `[cat:: refund]`, or `[cat:: transfer]`.)*
3. **With Notes & Linked Records:**
   Use `—` (or `--`) for inline notes, and standard wikilinks for context:
   ```markdown
   - [x] $42.50 Target [cat:: shopping] [[area/home]] — cleaning supplies
   - [x] $18.20 Taqueria [cat:: dining] [[eat/taqueria|🌮]] — lunch with Kelly
   ```
4. **Flagging Items to Inspect:**
   Use `⚑` or `!!` to flag suspicious or unrecognized charges for later investigation:
   ```markdown
   - [x] $89.00 Unknown Merchant ⚑ — check receipt / possible dispute
   ```
5. **Cash Withdrawals (ATM):**
   Categorize as `cash` (represents untraced cash outflow):
   ```markdown
   - [x] $40.00 ATM Withdrawal [cat:: cash]
   ```
6. **Card Payments & Transfers:**
   Categorize as `transfer` so they net out and never inflate Outflow/Inflow totals:
   ```markdown
   - [x] $450.00 WF Credit Card Payment [cat:: transfer]
   ```

#### Step 5: What if Nothing Posted Today?
If no new transactions posted:
- **Do NOT create placeholder or dummy rows.**
- An empty `## Thu Nov 12` section is completely valid.
- Simply checking off the PRE chore is your durable record that you looked and verified.

#### Step 6: Complete the Chore
Return to `gtd_daily.md` (or your review walk) and mark `^acknowledge-bank` done (`[x]`). Because it carries `[repeat:: every day when done]`, it will automatically reschedule for Friday (`2026-11-13`).

---

### 1.3 Quick Verification Commands

Immediately after typing your rows tomorrow, verify everything from your terminal:

```bash
# 1. Check for grammar or syntax errors (should exit 0 with 0 errors, 0 warnings)
bob bank check

# 2. Check the waiting queue (should show "nothing to acknowledge" if all typed rows were ticked)
bob bank

# 3. View today's clean summary report
bob bank report -D today

# 4. View the month-to-date report with category breakdown and heat strip
bob bank report
```

### 1.4 Do's and Don'ts

| Do | Don't | Why |
|---|---|---|
| Use `[cat:: key]` matching `bank.md` | Don't invent arbitrary unconfigured tags | Keeps reporting categories clean and structured |
| Use `[x]` for typed rows | Don't leave them `[ ]` | Typed rows are acknowledged at birth |
| Use `+$` for deposits / refunds | Don't omit the `+` on money in | Unsigned amounts are parsed as spending |
| Leave empty days blank | Don't add "None" or fake `$0.00` lines | Empty day headings represent zero activity cleanly |
| Keep `#task` off bank rows | **NEVER add `#task` to a bank row** | Triggers `bank_row_task` error; bank rows are not GTD tasks |

---

# Part 2: End-to-End Testing Protocol for Epic `bob-cli-kd`

This section details how to verify the entire system across all 7 epic phases:
- **Phase 1 (`bob-cli-kd.1`):** Vault habit restart (`bank.md`, `bank/2026-11.md`, PRE chore).
- **Phase 2 (`bob-cli-kd.2`):** Row grammar, YAML config, and `bob bank check` linting.
- **Phase 3 (`bob-cli-kd.3`):** Read commands (`list`, `report`, `ensure`, `ack`).
- **Phase 4 (`bob-cli-kd.4` / `4.1`):** Weekly QFX/CSV import, deduplication, and journal `.bob/bank/`.
- **Phase 5 (`bob-cli-kd.5`):** Balance proofs, anchor derivation, presence, and `import -F`.
- **Phase 6 (`bob-cli-kd.6` / `6.1`):** Obsidian UI cards, daily note chips, and safe editor gestures.
- **Phase 7 (`bob-cli-kd.7`):** Final wrap-up, documentation audit, and durable SASE memory strands.

---

### 2.1 Test Environment Setup

Always execute full end-to-end integration tests in an isolated temporary vault to protect production data:

```bash
# Set up isolated scratch vault
export TEST_VAULT=$(mktemp -d /tmp/bob_bank_e2e_XXXXXX)
export BOB_DIR="$TEST_VAULT"
export BOB_NOW="2026-11-12T09:00:00-05:00"

echo "Running E2E tests in: $BOB_DIR (Simulated date: $BOB_NOW)"
```

---

### 2.2 Phase-by-Phase Walkthrough Test Cases

#### Test Case 1: Initial Vault Hub & Ensure (Phases 1 & 3)
1. **Verify Empty Teaching State:**
   ```bash
   bob bank check
   ```
   *Expected:* Exits 0, prints teaching empty state explaining `bank.md` configuration.
2. **Initialize `bank.md`:**
   ```bash
   cat << 'EOF' > "$BOB_DIR/bank.md"
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
    shopping: 🛍️ Shopping
    subscriptions: 🔁 Subscriptions
  rules:
    - match: VENMO
      cat: transfer
---
# 🏦 Bank
EOF
   ```
3. **Execute `ensure`:**
   ```bash
   bob bank ensure -D 2026-11-12
   ```
   *Expected:* Creates `bank/` directory, initializes `bank/2026-11.md` with canonical frontmatter and `## Thu Nov 12` heading. Prints next insertion line. Idempotent on second run.

---

#### Test Case 2: Row Grammar, Edge Cases & Linting (Phase 2)
1. **Append Test Rows into `bank/2026-11.md`:**
   ```bash
   cat << 'EOF' >> "$BOB_DIR/bank/2026-11.md"

- [x] $13.71 Smashburger [cat:: dining]
- [ ] $61.20 ShopRite [cat:: groceries]
- [x] +$1,250.00 Payroll [cat:: income]
- [x] $40.00 ATM Withdrawal [cat:: cash]
- [x] $25.00 Target ⚑ — check warranty
- [x] $
EOF
   ```
2. **Execute `check`:**
   ```bash
   bob bank check -f json
   ```
   *Expected:*
   - `ok: true`.
   - `issues.errors: 0`, `issues.warnings: 0`.
   - Stubs (`- [x] $`) ignored without findings.
   - Flags recorded under findings as `info` (`bank_flagged`).
3. **Negative Syntax Checks:**
   - Add a row with `#task`: `- [x] $10.00 Lunch #task` -> `bob bank check` reports error `bank_row_task`.
   - Add an unknown category `[cat:: space_travel]` -> reports error `bank_category_unknown` with suggestions.
   - Add invalid box `[-] $10.00` -> reports error `bank_row_status`.
   *(Revert invalid rows after verifying failure).*

---

#### Test Case 3: Read, Report & Acknowledgment Workflows (Phase 3)
1. **Waiting Queue Inspection:**
   ```bash
   bob bank
   ```
   *Expected:* Shows 1 waiting row: `$61.20 ShopRite` under `Thu Nov 12`.
2. **Period Reports & Arithmetic Integrity:**
   ```bash
   bob bank report -m 2026-11 -f json
   ```
   *Expected:*
   - Integer cents representation:
     - `out_cents: 11491` ($13.71 + $61.20 + $40.00).
     - `in_cents: 125000` (Payroll).
     - `net_cents: 113509` ($1,250.00 - $114.91).
     - `cash_out_cents: 4000` (ATM).
   - Category breakdowns match exact cent totals and shares.
3. **Acknowledge Waiting Row:**
   ```bash
   # Dry-run preview
   bob bank ack -d -D 2026-11-12
   # Real execution
   bob bank ack -D 2026-11-12
   ```
   *Expected:* Modifies line in `bank/2026-11.md` from `- [ ] $61.20` to `- [x] $61.20`. Rerunning `bob bank` now displays `nothing to acknowledge`.

---

#### Test Case 4: QFX Import & Journal Deduplication (Phase 4)
1. **Generate Synthetic QFX Statement (`sample.qfx`):**
   Simulate a Wells Fargo QFX statement covering Nov 11–12 containing:
   - Smashburger ($13.71) — matches the typed twin!
   - Trader Joe's ($34.80) — new transaction missed by manual typing.
2. **Run Import:**
   ```bash
   bob bank import sample.qfx
   ```
   *Expected:*
   - **Twin Matching:** Matches `$13.71 Smashburger`. Appends `^bank-<hex>` to the existing typed row; preserves Bryan's category and note; does NOT duplicate the row.
   - **New Insertion:** Inserts `- [ ] $34.80 Trader Joe's [cat:: groceries] ^bank-<hex2>` under `## Thu Nov 12` in waiting status (`[ ]`).
   - **Journal Record:** Creates/appends to `.bob/bank/<host>.jsonl` with hashed transaction IDs.
3. **Idempotency Test (Importing Twice):**
   ```bash
   bob bank import sample.qfx
   ```
   *Expected:* 0 new rows written; 0 modifications; exits cleanly.

---

#### Test Case 5: Balance Proving, Drift & Restoration (Phase 5)
1. **Balance Check Verification:**
   ```bash
   bob bank check
   ```
   *Expected:* Shows `✓ balanced` (LEDGERBAL from QFX matches sum of posted transactions + anchor).
2. **Detecting Manually Deleted Row:**
   - Manually delete the Trader Joe's row from `bank/2026-11.md`.
   - Run `bob bank check`:
     *Expected:* Reports warning/error `bank_balance_delta` and `bank_row_missing` naming the missing transaction ID.
3. **Force Restoration (`import -F`):**
   ```bash
   bob bank import -F
   ```
   *Expected:* Re-inserts the deleted Trader Joe's transaction into `bank/2026-11.md` under `## Thu Nov 12` without duplicating any existing rows. `bob bank check` returns to `✓ balanced`.
4. **Coverage Gap & Stale Account Verification:**
   - Advance `BOB_NOW` by 14 days without importing:
     `bob bank check` reports `bank_account_stale` (exceeds default `stale_after: 10`).

---

#### Test Case 6: Obsidian Plugin Verification (Phase 6 / `bob-ledger-tools`)
Verify in `bob-plugins` test harness or test vault:
1. **Codeblock Rendering:**
   - In `bank/2026-11.md`: ````bob-bank view: month```` renders interactive month card with heatmap, category bars, and period totals.
   - In `bank.md`: ````bob-bank view: queue```` renders waiting queue with clickable acknowledge buttons.
2. **Daily Note Chip:**
   - In `daily/2026-11-12.md`: renders quiet chip `out $114.91 · in +$1,250.00`. Clicking jumps to `bank/2026-11.md#Thu Nov 12`.
3. **Editor Typing Helpers:**
   - Pressing `Enter` at the end of a bank row automatically inserts `- [x] $`.
   - Pressing `Enter` on an empty stub `- [x] $` clears the line.
4. **Math Protection:**
   - Ensure consecutive rows like `$13.71` and `$61.20` do not trigger Obsidian MathJax inline LaTeX rendering (`$...$`).
5. **Task Cycler Guard:**
   - Using Obsidian hotkeys (Ctrl+Enter, Alt+N, task status cycling) on a bank row does NOT attach `#task` or cycle into task statuses.

---

#### Test Case 7: Durable Memory Strands & Docs Audit (Phase 7 Wrap-up)
1. **SASE Memory Strands:**
   - Verified that only authorized strands are added via `/sase_memory_write`:
     - `glossary:bank-month-note` (defines `bank/YYYY-MM.md`).
     - `glossary:bank-row` (defines row syntax and acknowledgment semantics).
   - Rejected decision `decisions:bank-rows-not-records` must **NOT** be created (adhering to reviewer DECISIONS block).
2. **Documentation Audit:**
   - Verify `docs/bank.md`, `docs/reference/cli/bank.md`, and `docs/guides/acknowledge-bank-transactions.md` reflect shipped behavior.
   - Run `just docs-gen` and `just docs-check` to confirm all CLI snapshots and word budgets pass.

---

## Conclusion & Readiness Checklist

Bryan is 100% prepared to execute tomorrow's ritual:
- [x] Vault structure initialized (`bank.md` and `bank/2026-11.md` exist and are valid).
- [x] Morning PRE chore in place (`gtd_daily.md ^acknowledge-bank`).
- [x] Syntax and rules clear (typed rows start ticked `[x]`, no `#task`, `+$` for deposits).
- [x] Core CLI commands ready (`bob bank check`, `bob bank`, `bob bank report`, `bob bank ensure`).
- [x] Full E2E testing protocol mapped out for closing epic `bob-cli-kd`.
