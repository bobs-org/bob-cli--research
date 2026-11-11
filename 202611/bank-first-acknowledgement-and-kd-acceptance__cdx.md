# First bank acknowledgement and bob-cli-kd acceptance

Independent research by **cdx**, 2026-11-11, evidence collected through 20:34 UTC. No other report or researcher findings from this swarm were consulted. All monetary examples below are synthetic.

**Recommendation:** publish a short daily walkthrough first, followed by a clearly gated weekly reconciliation procedure and a separate tester checklist. Bryan can start the habit on **Thursday, November 12, 2026**, even if import and Obsidian work are unfinished. An empty waiting queue is acknowledgement evidence; it is not proof that every bank transaction is present.

## What is actually ready

| Evidence | Observed state |
| --- | --- |
| Epic `bob-cli-kd` | In progress. Phases .1–.3 closed; .4–.7 in progress when read. Import and Obsidian work have child epics. |
| Restart, reported by `bob-cli-kd.1` | `bank.md`, `bank_month.md`, and `bank/2026-11.md` created. Checking only; account `start: 2026-11-11`. Daily PRE chore `gtd_daily#^acknowledge-bank` scheduled for November 12. Old `cash#^daily-bank-records-again` canceled as superseded. `bob#^bank-records` remains open. |
| CLI source inspected | Commit `8134d17310869db7afddde27e0f5df099d593c46`: `check`, `list`, `report`, `ensure`, `ack` exposed. Import parser/journal foundations exist; no import command. Account status is still an explicit `unverified` stub. |
| Executable tested on this host | `/home/bryan/.cargo/bin/bob`, version `0.5.0`; same five commands. `bob bank import --help` rejects `import`. The version number alone is not a readiness check. |
| Plugin source inspected | `bob-plugins` commit `3423ba6515ca006c9d010e8c4efd9a0f419a63a9` has bank decoding, source, and data-service fragments. Full bank cards, editing gestures, and deployment were not established by this snapshot. |

The restart facts above come from the phase's recorded rollout, not a fresh inspection of Bryan's live vault. I did not change the real vault, install software, import real transactions, or declare the epic complete.

## Suggested concise user guide

### Tomorrow: look, write, acknowledge

1. **Open your usual Bob vault and Wells Fargo checking activity.** Find the PRE chore **Acknowledge bank**. Review **posted** transactions and deposits; leave pending items until they post. Use the bank's posting date for each row. The seeded start date is **November 11**, so include anything posted since November 11 on this first pass. There is no historical backfill obligation before that date.

2. **Open the month note.** If the completed plugin is available, run **Bank: open today** from Obsidian's command palette. It has no default hotkey in the approved design. The CLI route is:

   ```sh
   bob bank ensure -D 2026-11-12 -o
   ```

   Expect `bank/2026-11.md` and `## Thu Nov 12`. Repeating the command is safe. Without the bank CLI/plugin, open that note directly and add the heading by hand. Put November 11 postings under `## Wed Nov 11`, even when reviewing them tomorrow. After the first day, use `-D today`.

3. **Type one checked row for each posting you have reviewed.** These examples show the syntax; substitute your own transactions:

   ```markdown
   - [x] $13.71 Smashburger [cat:: dining]
   - [x] +$1,250.00 Payroll [cat:: income]
   - [x] +$10.00 Returned item [cat:: refund]
   - [x] $100.00 Card payment [cat:: transfer]
   - [x] $20.00 ATM withdrawal [cat:: cash] !! check fee
   ```

   `[x]` means “I acknowledged this.” An unsigned `$` amount is money out; `+$` is money in. Categories are optional, but `income`, `refund`, `transfer`, and `cash` affect totals. A transfer is excluded from spending; an uncategorized deposit is not automatically income. `[acct::]` is unnecessary for the sole default checking account. Add `— a note` or `!! follow up` when useful. Never add `#task`, invent a bank ID, or type totals into the note. A real follow-up task belongs in the bank hub, separate from the transaction row.

4. **Read any waiting rows before ticking them.** `bob bank` lists waiting rows across all months; `bob bank list -a` includes rows you already acknowledged. Imported rows will start `[ ]`. Tick individual rows in the note, use the queue card once shipped, or acknowledge a reviewed day:

   ```sh
   bob bank ack -d -D 2026-11-12
   bob bank ack -D 2026-11-12
   ```

   The first command previews. The second ticks every currently waiting row on that date, including rows without IDs. For a smaller selection, pass actual IDs from the rows, for example `bob bank ack bank-aabbccdd`. Already checked rows are unchanged. Do not use the all-day command to clear rows you have not read.

5. **Check and finish the chore.**

   ```sh
   bob bank check
   bob bank report -D 2026-11-12
   bob bank
   ```

   Resolve syntax/configuration errors. A deliberate flag can remain. The daily total includes both checked and waiting rows: acknowledgement changes review state, not spending. If nothing posted, leave the heading empty and complete **Acknowledge bank**; do not create a `$0.00` transaction. Before import is available, `unverified` is expected.

**Tomorrow's success:** you looked at checking, recorded the postings since the configured start, read/ticked the waiting rows you recognized, and completed the chore. Checking-only coverage does not claim visibility into purchases made on an unconfigured credit card or into how withdrawn cash was later spent.

### First reconciliation, then Mondays

This procedure requires the completed import and proof phases. First check on the machine where you will run it:

```sh
bob bank --help
bob bank import --help
```

If `import` is absent, keep using the daily routine and treat weekly proof as pending. Update to a build containing the completed epic through the normal installation procedure; `just install` is the documented source-checkout route. For Obsidian, deploy the matching plugins with `bob plugins sync` on that desktop, then reload Obsidian. Do not force an overwrite when sync reports another deployment.

1. In Wells Fargo Online, download checking activity as **Quicken Web Connect/QFX**. Wells Fargo documents account-activity downloads and selectable dates; Quicken identifies Web Connect files as `.qfx`. Save the file outside the vault. Use a date range starting on or before **November 11**, ending at the latest available posted activity. The precise signed-in menu was not tested. [Wells Fargo account activity](https://www.wellsfargo.com/help/online-banking/activity-faqs/), [Quicken Web Connect](https://www.quicken.com/support/how-activate-web-connect-account/).
2. Preview the actual file, then import it. Replace the example filename with the one downloaded:

   ```sh
   bob bank import -a checking -d "$HOME/Downloads/checking-2026-11-12.qfx"
   bob bank import -a checking "$HOME/Downloads/checking-2026-11-12.qfx"
   bob bank check
   bob bank
   ```

   Inspect the matched rows as well as additions. A typed match should retain its text and tick and gain an ID; only missed transactions should appear as new waiting rows. Review those rows, correct payees/categories if useful, and acknowledge them. Prefer an explicit filename to a Downloads-wide glob for the first test.
3. Import the **same file again**. Expect no duplicate rows, no changed acknowledgements, and no new commit for a true no-op. This tests repeatability, not a second independent balance observation.
4. Obtain a **later export with a later balance observation** and an overlapping date window. The first balanced QFX establishes an opening anchor; the later observation tests it. Confirm contiguous coverage, present rows, matching amounts, and a current account status. Compare the bank's **ledger/posted balance at the reported as-of time**, not the live available balance, which can include pending adjustments. [Wells Fargo explains this difference](https://www.wellsfargo.com/help/online-banking/activity-faqs/).
5. Continue at the Monday review—first Monday is **November 16**—normally downloading the last 14 days, importing, acknowledging, and writing one line in last week's note: “What surprised me?” If a lapse exceeds that window, download back to the last covered date; do not repeatedly import only the latest 14 days and leave a hole. Import from one host at a time.

| Status or finding | What to do |
| --- | --- |
| `unverified` | No usable QFX balance proof yet; CSV alone cannot establish it. |
| `gap` | Download the missing date range, including the configured start when necessary. |
| `stale` | Refresh the export/import; default threshold is older than 10 days. |
| `delta` / edited amount | Inspect the named rows and the bank's posting. Do not invent an adjusting row. |
| `bank_row_missing` | Ordinary reimport preserves deletion. If deletion was accidental, preview `import -d -F` and deliberately restore with `import -F`. |
| Possible twins | Inspect both. If they are the same posting, preserve the ID-bearing row and transfer useful notes before removing the duplicate typed row. |
| `balanced` | The configured account's coverage, presence, amounts, and balance checks pass and the import is current. Also finish reading the waiting queue. |

The preservation advice for twins is a practical inference from the journal's presence check. A flag or acknowledgement records review; it does not settle a dispute or certify that a charge is legitimate.

## End-to-end acceptance: keep it separate from the daily chore

Run destructive and synthetic cases in a **disposable vault**, with an explicit `BOB_DIR` (or `-b`) and controlled `BOB_NOW`. Never add test transactions to Bryan's real bank notes. Record the CLI commit/build, plugin commit/deploy, counts, exit codes, and expected versus observed results. Full `kd` completion needs CLI, import/proof, UI, and wrap-up evidence; “queue empty” alone cannot close it.

| Test | Expected outcome | Evidence here |
| --- | --- | --- |
| Create configured hub; `ensure` twice | One month note/day heading; second run no change | Passed on installed CLI |
| Typed row, note, flag, empty `$` stub | Rows parse; stub ignored; flag informational | Passed |
| `list`, `list -a`, day/week/month reports | Waiting filter correct; exact cents and period totals | Passed |
| Read commands and `ack -d` | File bytes unchanged | Passed; Git index/HEAD not tested in this fixture |
| `ack` by ID, repeat, by date; valid+unknown IDs | Tick only selected rows; repeat no-op; unknown batch exit 2 and no write | Passed |
| First QFX, repeat, overlapping exports | Match typed rows once; missing rows wait; repeated import preserves bytes/review state | Pending import CLI |
| Later QFX balance snapshot | Anchor remains consistent; coverage and presence hold | Pending proof phase |
| Same amount twice, distinct FITIDs | Both real purchases survive; overlap never duplicates either | Pending |
| Exact typed twin; $20 typed/$24 posted; equidistant tie | Exact match keeps user text/tick; changed amount or ambiguity stays visible for review, not silently merged | Pending |
| Delete imported row; regular import; forced restore | Missing/delta reported; regular import leaves deletion; `-F` restores deliberately | Pending; disposable vault only |
| Edit imported amount | `bank_amount_edited`/proof problem; user edit preserved | Pending |
| Coverage hole; old last import | Named `gap`/`stale`; no unqualified caught-up result | Pending |
| Two accounts, transfer pair, income/refund, cash account | Explicit account choice when ambiguous; transfer excluded from Out/In; cash tracing avoids double counting | Partial: checking-side totals passed; multi-account import/cash tracing pending |
| Malformed transaction mixed with valid file | Whole batch exit 2; rows, journal, and Git state unchanged | Pending |
| QFX SGML and XML, CSV fallback, before-start row | Both QFX forms accepted; CSV unverified; no new pre-start row | Parser source inspected, not executed here |
| Task isolation | Bank rows absent from task planning/reconcile/archive; no task metadata added by gestures | Shared scanner unit test inspected; end-to-end tools/UI pending |
| Obsidian month/queue/day chip | Values agree with CLI; links navigate; warnings remain visible with empty queue | Pending actual desktop test |
| Enter, categories, completion, both display modes | Checked `$` continuation; empty stub clears; suggestions work; checkbox stays binary; `$` never becomes math | Pending actual desktop test |
| Queue painted, then a new waiting row arrives | “Acknowledge day” ticks only the IDs originally displayed; new row waits | Pending; CLI `-D` deliberately has broader current-day scope |
| Wrap-up | Docs match shipped behavior; read-only real-vault checks reported as counts; requested memory/follow-ups handled by epic owner | Pending .7 |

Additional UI checks: month navigation must not create missing months, the daily chip must open its own date, row syntax must return under the cursor, edits/acks must refresh visible totals without writing total lines, and an unavailable CLI must show an error rather than stale success. Test in Live Preview and Reading view. Plugin source existing in Git is not evidence of deployment on Bryan's Mac.

For the real export, first validate the actual Wells Fargo format with a dry run against a temporary vault copy. Report only counts and finding codes. Keep raw bank exports, credentials, identifiers, and personal amounts out of research artifacts. Then perform the real first import only as the user-directed operational step.

## What I executed

An isolated synthetic vault used `BOB_NOW=2026-11-12T12:00:00-05:00`, checking start November 11, and nine rows: dining −$13.71, waiting groceries −$61.20, income +$1,250, refund +$10, transfer −$100, flagged cash withdrawal −$20, unclassified credit +$9, and unclassified outflows −$0.10/−$0.20. A final empty checked `$` stub was ignored.

Eighteen JSON-mode invocations completed successfully, including the deliberately expected exit 2. The sequence was:

```text
check (empty vault)
ensure -D 2026-11-12
ensure -D 2026-11-12
[type the nine synthetic rows and stub]
check
list
list -a
report -m 2026-11
report -w 2026-W46
report -D 2026-11-12
ack aabbccdd -d
ack aabbccdd deadbeef       -> exit 2, no write
ack aabbccdd
list                      -> waiting 0
ack aabbccdd              -> changed false
report -D 2026-11-12      -> same totals
[append one unchecked, ID-less synthetic $1 row]
ack -D 2026-11-12
list                      -> waiting 0
check                     -> errors 0; bank_flagged info
```

Before the additional $1 row, all three periods returned **Out $95.21, In $1,260.00, Net $1,164.79**, transfer out $100, cash out $20, unclassified in $9, and unclassified out $0.30. The waiting row already contributed to Out. The file-hash snapshot matched before/after the read commands, acknowledgement preview, and unknown-ID refusal. These results verify the installed daily CLI only; they are not a full epic test or a real-bank reconciliation.

## Issues the final guide must resolve before calling the epic done

- **Start-date mismatch:** the approved plan/template examples use November 12, but the recorded real seed uses November 11. Teach the actual configured date; do not silently change it to make coverage pass.
- **Install versus capability:** `bob 0.5.0` here lacks import. Recheck help and executable resolution on Bryan's desktop after landing; do not promise readiness from a version string or a closed phase alone.
- **First anchor versus later proof:** importing identical bytes twice tests deduplication. A later balance-bearing snapshot is required for the independent reconciliation check.
- **Optional category does not mean meaningless category:** `+$` without `income`/`refund` stays outside In; transfer payments disappear from spending even when the destination card is outside the checking-only scope.
- **Matching is not merchant verification:** the approved matcher uses account, exact signed amount, and date proximity (typed date from one day before through three days after posting). Review matches in the preview, especially repeated equal amounts.
- **No need to add another chore:** confirm the recorded daily chore and the import phase's Monday chore have arrived through sync. Avoid creating duplicates. The subscriptions album and later statistical views are follow-ups, not prerequisites for tomorrow.

## Evidence trail

Internal records were read through audited SASE commands:

- `sase bead read bob-cli-kd bob-cli-kd.1 bob-cli-kd.3 bob-cli-kd.4 bob-cli-kd.5 bob-cli-kd.6 bob-cli-kd.7 -r "…"` (performed in batches): scope, decisions, rollout, phase evidence.
- `sase artifact read plan:202611/bank_daily_acknowledgment.md "…"`: accepted grammar, import/proof/UI contracts, acceptance table, and wrap-up obligations. This is the approved plan, not any current swarm report.
- [Bank contract at inspected CLI commit](https://github.com/bobs-org/bob-cli/blob/8134d17310869db7afddde27e0f5df099d593c46/docs/bank.md), [CLI reference](https://github.com/bobs-org/bob-cli/blob/8134d17310869db7afddde27e0f5df099d593c46/docs/reference/cli/bank.md).
- [CLI dispatch](https://github.com/bobs-org/bob-cli/blob/8134d17310869db7afddde27e0f5df099d593c46/src/native/bank/cli.rs), [status stub](https://github.com/bobs-org/bob-cli/blob/8134d17310869db7afddde27e0f5df099d593c46/src/native/bank/status.rs), [bank tests](https://github.com/bobs-org/bob-cli/blob/8134d17310869db7afddde27e0f5df099d593c46/src/native/bank/tests.rs), [source parser](https://github.com/bobs-org/bob-cli/blob/8134d17310869db7afddde27e0f5df099d593c46/src/native/bank/source.rs).
- [Plugin fragment manifest at inspected plugin commit](https://github.com/bobs-org/bob-plugins/blob/3423ba6515ca006c9d010e8c4efd9a0f419a63a9/plugins/bob-ledger-tools/src/fragments.json), accessed through the `sase repo open bob-plugins` checkout.
- [Installation](https://github.com/bobs-org/bob-cli/blob/8134d17310869db7afddde27e0f5df099d593c46/docs/start/install.md) and [desktop deployment/resolution](https://github.com/bobs-org/bob-cli/blob/8134d17310869db7afddde27e0f5df099d593c46/docs/guides/run-bob-from-obsidian.md).

No account authentication or financial connection service is needed by this proposed workflow: the user downloads activity and Bob reads the local export. The signed-in Wells Fargo flow, real export compatibility, Mac deployment, and later-phase behavior remain explicit verification items.
