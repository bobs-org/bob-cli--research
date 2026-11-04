# Which bob-cli Task Beads to Work Next: Ten Picks Checked Against Live Agents on apollo and athena

*Consolidated report · 2026-11-04 · merges five independent reports (`cdx`, `cld`, `grk`, `mus`,
`gem`) with fresh checks run at about 20:40 UTC. Trees: bob-cli `399b5222`, bob-plugins `b9f47f3`,
bob-mac-capture `5960b31` (last finished CI run).*

## Bottom line

Ten work items are worth starting. Seven can start right now; one of them (#6) needs to coordinate
with a queued Mac agent. The other three wait on something specific:

- #3 waits for #1 and a one-line policy call from you.
- #9 can record its decision now, but its code must wait for epics `h2` and `h4` to land.
- #10 waits for #7, which edits the same module.

Several items bundle beads that share one file, one test command, or one root cause. One worker
should take each bundle.

| # | Work item | Beads | Size | Start |
|---|---|---|---|---|
| 1 | Make bob-plugins `npm test` green | `eh`, `et`, `ff`, `f7`, `f1` | S | Now |
| 2 | Let committed agent deploys through `bob plugins sync` | `fy` (+ live instance `e4`) | L | Now |
| 3 | Stop Obsidian Ctrl+Enter deleting a closed timed Pomodoro | `g4` | S | After #1, plus your one-line policy call |
| 4 | Fix `bob periods brief` before Monday's Review | `gs`, then `gt` (`gu`–`gx` follow) | M | Now |
| 5 | Stop vault edits leaking SASE plans into `~/bob` | `gy` (+ `8n`) | S mitigation | Now |
| 6 | Turn bob-mac-capture master green again | **`h7` (new)** + `1x` | L | Now, coordinate with the `185` chain |
| 7 | Fix the unowned bob-cli master test failures | **`h6` (new)** | L | Now |
| 8 | Alert on hostile activity on athena | `8r` | L | Now (infra repo) |
| 9 | Make link consumption keep notes and unrelated entries | `7q` | L | Decision now; code after `h2` and `h4` land |
| 10 | Render emoji in generic ref PDFs | `e9` | M | After #7 (same module) |

Items 6 and 7 are beads I filed during this review: `bob-cli-h7` and `bob-cli-h6`. Both master
breakages were confirmed by two researchers and by my own checks, and neither had a bead or a
running owner.

Six Mac CI beads and one plugin-test bead are already fixed and should be closed rather than worked
(see [Close or narrow](#close-or-narrow-before-anyone-works-them)).

## 1. What is running now, and what it rules out

All five researchers checked both hosts between about 20:10 and 20:25 UTC. I re-checked at 20:40 UTC
with `sase agent list -j` on apollo and `ssh athena sase agent list -j`. Three things changed in
between: `h2.4` landed as `399b5222`, `h4.3` landed as `3ad23a73`, and athena's `185--3` finished.
The `185` chain then gained a second queued follow-up.

| Host | Live work | What it owns | Beads that must wait |
|---|---|---|---|
| apollo | Epic **`h2`**, "Record past Pomodoros with `x=`". `h2.5` (docs) is running; `h2.6` (Mac card) and `h2.land` are waiting. | `capture_language/editor_pomodoro.rs`, `past.rs`, `capture/pomodoro_start.rs`, `capture/pomodoro_blocks.rs` (changed twice today), the `!` close path, and `__complete` tests | `h1`, `gc`, `dq`, `gd`/`f2`/`g8` |
| apollo | Epic **`h0`**, "`- ^^` move choice". `h0.8` (Move card submit flow, docs) is running; `h0.land` is waiting. | Capture planner, `-m/--move-in`, capture-parse spans, the Mac Move card | `8a`, `gk`, `ge`, `h5` (see below) |
| athena | Epic **`h4`**, "Transfer previews". `h4.1` and `h4.2` are running; `h4.4`–`h4.6` and `h4.land` are waiting. | Landing blocks, merge and move records, and the Mac transfer, landing, and refusal cards | `dq`, `2u`, Mac capture-panel UI beads |
| athena | Non-bead **`185` chain**. `185.f0` is running. `185.f0.f1` (`,` types `+`) and `185.f0.f2` (`\` types `#`, with double `\` typing a real backslash) are both queued as `#plan %m:@xlarge`. | The Mac capture editor's typing aliases, including backslash handling | `6g`, `9n`, and the backslash half of `h7` (coordinate) |
| both | SASE-project epics `1qz`, `1r8`, `1r2`, `1n6.11`, and agents `18a`, `18b`, `ce`, `cd--code` | SASE runtime, finalizers, publication, and release | Route `e0`, `ei`, and the SASE side of `gy` to the sase project |

Ten older bob-cli epics (`28`, `3j`, `5w`, `66`, `87`, `8b`, `9k`, `9k.8`, `bj`, `d2`) are still
`in_progress`, but no agent is running for any of them. They create no file conflict today. Their
ready follow-ons (for example `68`/`69`/`6a`, `83`/`8h`/`8i`, `7j`/`fm`) should still wait for those
epics to be landed or closed.

**`h5` belongs to `h0`.** `bob-cli-h5` was filed at 20:23 UTC for the master failure
`capture::note_pull::np_move_groups_follow_requested_sources_in_cli_fixtures`. The CI diff differs
only in a new `moved_tasks[].via = "bullet"` field, which arrived in h0 commit `458b53b9` ("execute
move_choice picks with mint, splice, offers and via"). I added a `DISCOVERED ISSUE` note to
`bob-cli-h0` so its lander refreshes the fixture and closes `h5`.

None of the ten picks edits a file that a running agent owns. Refresh both rosters immediately before
launching workers, because this changes hourly.

## 2. Where the five reports disagreed, and what is actually true

| Question | Reports said | Verified today | Effect on the ranking |
|---|---|---|---|
| Are `f3`/`fu` (Mac XCTests) still red? | `mus` ranked them #1–#2. `grk` said wait for `h4`. `cdx` and `cld` said they are fixed. | **Fixed.** Run 41888215951 at `4906d94` passed every step. Master went red again only with three later Go To commits, a different set of failures. | Close `f3`, `fu`, `dz`, `eo`, `fj`, and `fp`. Work the new failures as `h7`. |
| Is `e4` (stuck dirty plugin deploys) resolved? | `gem` said resolved. `cld` said it is live. | **Live.** `bob plugins list` shows `bob-ledger-tools` 1.98.0 and `bob-navigation-hotkeys` 2.73.3 in `drift`, deployed from an uncommitted build at `1dc272a` (07:13 UTC). A dry-run sync refuses both. | `fy` is #2. Keep `e4` open as `fy`'s acceptance case. |
| Does `et`'s gcal half still fail? | `gem`/`grk` said yes (from source). `cdx`/`cld` said it passes. | **It passes**: 25/25 under both UTC and America/New_York. Only freshness-namespace fails (8 pass, 1 fail). | Narrow `et` to the freshness test. |
| Is `dq` data loss? | `gem`/`mus` said yes and ranked it. | **No.** The bead says release "writes are still correct"; only the Mac `pomodoro_blocks` preview is dropped. `pomodoro_blocks.rs` was changed twice today by `h2`. | Runner-up. Start after `h2` and `h4` land. |
| How big is `gy`? | `gem`: large. `cld`: small vault edit. | The leak is open: `~/bob/AGENTS.md` still says to commit with `/sase_git_commit`, and `.gitignore:34` (`!*.md`) re-includes `sdd/plans/*.md`. | The vault mitigation is small. The SASE-side root fix belongs in the sase project. |
| `8r`/`9x` alerting | `cdx` ranked them #4 and #5. The others listed them as runners-up. | `cdx` queried athena's live Prometheus: only `athena.apt` and `athena.disk-space` rules exist. | `8r` is in (a real compromise happened on 10-17). `9x` is a runner-up (no halt has gone unnoticed yet). |
| `f8` (athena CPU budgets) | `grk`/`gem` ranked it #8. | Passes on apollo; fails only on athena. Fixing it properly needs profiling. | Runner-up. |
| Are there master failures with no bead? | Only `cld` found them and left them unfiled to avoid five duplicate beads. | Confirmed in CI runs 41900846465 (bob-cli) and 41900858873 (Mac). No duplicate bead exists. | Filed as `h6` and `h7`. |

My test re-run of bob-plugins `b9f47f3` on apollo (UTC unless noted):

| Test file | Result | Bead |
|---|---|---|
| `test-ledger-tools-note-ready.cjs` | 40 pass / 1 fail (`1 !== 2` scans) | `eh` |
| `test-ledger-tools-relation-index.cjs` | 11 pass / 1 fail | `eh` |
| `test-ledger-tools-freshness-namespace.cjs` | 8 pass / 1 fail | `et` |
| `test-ledger-tools-gcal-events.cjs` | 25 pass (UTC and New York) | `et`, already fixed |
| `test-navigation-hotkeys-schedule-work-log.cjs` | 16 pass / 1 fail | `ff` |
| `test-command-mode-sheet-sequence-dom.cjs` | 0 pass / 1 fail ("Could not find Chromium") | `f1` |
| `test-ledger-tools-keep-inbox.cjs` | 33 pass (UTC); 32 pass / 1 fail under `TZ=America/New_York` | `f7` |
| `test-ledger-tools-lane-walk.cjs` | 10 pass | `dx`, already fixed |

## 3. The ranked list

Ranking order: harm to your own data or daily workflow first, then the tax on every agent's gate,
then how fresh the evidence is, then whether a running agent conflicts, then cost.

### 1. Make bob-plugins `npm test` green: [`eh`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-eh/README.md), [`et`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-et/README.md), [`ff`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-ff/README.md), [`f7`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-f7/README.md), [`f1`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-f1/README.md)

**Why.** These five beads carry 66 independent +1s, more than half of all corroboration on ready task
beads. Since 2026-10-30, every lander that touches bob-plugins has re-proved that these failures came
before its change. All five reports rank this cluster at or near the top. All six failing assertions
reproduce today. Every one is a test-harness defect, not a product bug. A green suite also makes the
verification for #2, #3, and #9 meaningful.

**Recommended solution.** One worker, one bob-plugins checkout, test-only edits:

- **`eh`:** change the `onLayoutReady` fakes in `test-ledger-tools-note-ready.cjs` and
  `test-ledger-tools-relation-index.cjs` from one slot to an ordered callback list, and fire each
  callback once. That matches Obsidian, where `setupGcalEvents` registers a second callback. Look for
  other copies of the single-slot fake. Do not remove the production registration.
- **`et`:** narrow the bead to the freshness test. Run the initial memo and the later refresh on one
  injected clock. Today the test starts on October 8 but refreshes against the real date, when an
  October 1 stamp with a 30-day interval is already due. Do not just move fixture dates forward.
- **`ff`:** derive the "future" schedule date from the harness clock (for example now + 7 days), or
  freeze the clock. Keep the Pending→Blocked and Work Log assertions.
- **`f7`:** build the expected notice text with the same local-time formatter that production uses.
  Run the test under both `TZ=UTC` and `TZ=America/New_York`.
- **`f1`:** skip with a clear reason when no Chromium is found. Fail hard when `CHROMIUM_PATH` is set
  but invalid, or when `CI` is set.
- Run the full `npm test` under America/New_York, then close each bead on its own evidence. Optionally
  fold in `ej` (the 5 s Live Preview wall-clock gate, +4).

**Conflicts:** none; no running agent edits bob-plugins tests. **Do not** launch five agents into the
same repository.

### 2. Let committed agent deploys through `bob plugins sync`: [`fy`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-fy/README.md), with [`e4`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-e4/README.md) as the live instance

**Why.** Your Obsidian is running stale plugin code right now. Agents run `bob plugins sync` before
SASE commits their edits, so the stamp says `dirty` and every later sync from master refuses that
plugin. This has happened at least five times (`e4` twice, `fd.2`, `ey.6`, `fl.6.1`) and is live again
today. I compared the vault's deployed files with git history. **Every managed file in both drifted
plugins is byte-identical to commit `f392c88`**, which was committed two minutes after the dirty
deploy and is an ancestor of HEAD. The vault is therefore missing `b9f47f3`, yet sync still refuses.
This is the exact case `fy` must accept, and it gives a ready-made acceptance fixture.

**Recommended solution.** In `src/native/plugins/deploy.rs` (untouched since 11-02, and owned by no
running epic):

1. When a sync meets a `dirty` stamp, look for a single commit reachable from the incoming clean HEAD
   whose `plugins/<id>/` tree contains every managed file (`manifest.json`, `main.js`, and
   `styles.css` when present) with exactly the stamped hashes. Use `git rev-list HEAD --
   plugins/<id>`. If one exists, treat the deploy as included and overwrite without `--force`.
2. Never accept "each blob appears somewhere in history". Hashes drawn from different commits can
   describe a bundle that never existed. Keep `cu`'s refusal for genuinely uncommitted, divergent, or
   unverifiable deploys.
3. Optionally, also restamp provenance after SASE's post-turn commit, so the dirty window closes
   sooner.
4. Tests: dirty deploy → same content committed → later commit → sync from a second checkout
   succeeds. A modified or uncommitted build still refuses. Update the plugin-sync help text.

**Immediate operational step (needs your OK):** because the content matches `f392c88`, a targeted
force-sync of `bob-ledger-tools` and `bob-navigation-hotkeys` from the clean master checkout is safe
today. After `fy` lands, a normal sync should clear the drift; close `e4` then.

### 3. Stop Obsidian Ctrl+Enter deleting a closed timed Pomodoro: [`g4`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-g4/README.md)

**Why.** This is silent loss of recorded time. When a close defers every kept link (for example, the
only link is a not-started Event Task), task-status-cycler deletes the closed `(**0800-0900**
[t:: 60m])` row, while `bob capture x` keeps it. Your Stats therefore depend on which surface closed
the session. That contradicts `decisions:off-clock-pomodoros-count-apart`, under which recorded
session time survives. The `deferredOnlyClose` branch is still at `060-pomodoro.js:847–973`, and
`cdx` reproduced the deletion with the shared vector.

**Recommended solution.** Confirm option 1 in one line: the plugin keeps the closed timed row,
matching bob. Then, in bob-plugins only:

- Remove the `deferredOnlyClose`/`deletedClosedEntry` special case, but keep the deferral of the link
  to the new placeholder.
- Keep deleting genuinely empty, *untimed* entries, per the existing emptied-Pomodoro rule.
- Make the vector harness assert the full `expected_day` for `close-defers-not-started-off-clock`,
  covering worked and off-clock rows.
- Update `docs/task-status-cycler.md` and the `pomodoro_clock` fixture README.

Bob's behavior and vector stay unchanged, so this does not touch `h2`'s close or record engine. Run it
after #1, so the suite can verify it. Its retention rule also sets the baseline for #9.

### 4. Fix `bob periods brief` before Monday's Review: [`gs`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-gs/README.md), then [`gt`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-gt/README.md); `gu`, `gv`, `gw`, `gx` follow

**Why.** The `gr` epic drafted 17 weekly Reviews (W27–W43) from this command and hit the same defects
every week:

- **`gs`:** archived `done/` tasks lose their linked minutes and get dead links. Current
  `linked_minutes` matches only `source_path`.
- **`gt`:** every linked task is credited the whole Pomodoro, so tasks outrank their own roots. For
  example, in W41 a root shows 1h33m while its own task shows 1h40m.

The next weekly Review is Monday 2026-11-09, and the planned automation `gp` would copy the defects
every week. All six beads live in `src/native/periods/brief.rs`, which no running agent touches.

**Recommended solution.** One worker and one short plan, fixing the beads in this order and never in
parallel checkouts:

1. **`gs`:** resolve original and archive paths to one canonical task identity, keyed by full
   vault-relative path plus block id. Count each session and task match once. Render `archive_path`
   in links when it is set. Share this resolver among attribution, ranking, and link output.
2. **`gt`:** split a multi-link Pomodoro's minutes across its links by reusing the stats
   `root_parent` splitter, so task rows sum to no more than their root. Add a W41-shaped regression
   test.
3. **`gv`, `gw`, `gx`:** small, already localized fixes (the "+N more" counts; dedup and ordering of
   "Bryan's words"; Markdown glitches).
4. **`gu`** needs your call on semantics. Recommended:
   - Rebuild "Kept 3+" and "No linked minutes" as of the span end, from dated ROTTEN LOG entries and
     `[created::]`.
   - Omit "Blocked projects" for past periods, with a one-line note.

If time is short, land `gs` and `gt` before Monday and leave the rest for the following week.

### 5. Stop vault edits leaking SASE plans into `~/bob`: [`gy`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-gy/README.md), with `8n`

**Why.** `~/bob/AGENTS.md` (line 11) still tells agents to commit vault edits with
`/sase_git_commit`. Two `gr` phases did that, and each committed a tale-plan archive into
`~/bob/sdd/plans/`. The vault's `.gitignore` does not stop a repeat: its `!*.md` rule (line 34)
re-includes `sdd/plans/*.md`. Any agent that edits the vault, including the planned Monday Review
automation, can leak again. Line 5 of the same file still says the vault "is actively synced by
Obsidian Sync" (`8n`); git vault-sync replaced that.

**Recommended solution.**

1. **Vault commit (small).**
   - Change the commit instruction: let `bob vault-sync` commit (it committed 15 of 17 Review notes
     within seconds). When an explicit commit is needed, run `git add <your files> && git commit`,
     never `/sase_git_commit`.
   - Replace the Obsidian Sync sentence with git vault-sync and a pointer to `bob vault-sync status
     --json`.
   - Add an anchored `/sdd/` ignore *after* the `!*.md` re-include, then check with `git check-ignore
     -v sdd/plans/x.md`.
2. **Root cause (sase project).** SASE should never archive a plan into a repository that is not that
   plan's home. File it through `/sase_new_task` in the sase project rather than patching it from Bob.

The stored size (`large`) reflects the SASE-side fix. The vault mitigation removes the risk today.

### 6. Turn bob-mac-capture master green again: [`h7`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-h7/README.md) (new), with [`1x`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-1x/README.md)

**Why.** Mac master was fully green at `4906d94`. Three Go To commits then landed without a lander
(`fde8211`, `70c0839`, `5960b31`), and every finished run since has failed:

- `CaptureBackslashGotoTests.testInsertHelperDeclinesWhileComposingSubmittingOrLocked` leaves `\` in
  the draft.
- `CaptureTaskGotoPanelTests.testDelayedChipRefetchCannotReplaceReopenedSnapshot` times out.
- `testFailureOnChipRefetchRetainsRowsAndReportsError` now receives a `bob command failed (exit 7):
  …` prefix where it expects the bare error text.
- `swift test` also hits the 15-minute hang guard.

While the Test step is red, Bundle, Launch smoke, and Install never run. That matters right now:
`h4.4`–`h4.6`, `h2.6`, and the `185` chain are all about to push Mac code into that red gate. `1x` (+4)
is the process gap that let this happen: Linux hosts push Mac code without watching macOS CI.

**Recommended solution.**

1. Fix each failure at its root. Decide whether the panel should show the prefixed error text (then
   update the test) or strip the prefix (then fix the product). Repair the delayed-refetch race; the
   uploaded xctest samples point to the hang. Do not delete or weaken tests.
2. **Coordinate the backslash test with `185.f0.f2`**, which will change backslash handling in the
   same editor. Either land `h7` before `185.f0.f2` starts (it is queued behind `185.f0`), or give the
   backslash half to that agent.
3. Then land `1x` through `/sase_memory_write`. Any push to bob-mac-capture from a Linux host must run
   `scripts/dev/macos-ci-check` or watch the exact-SHA macOS run to green, using `/sase_monitor`.

### 7. Fix the unowned bob-cli master test failures: [`h6`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-h6/README.md) (new)

**Why.** bob-cli master CI is red for four reasons:

- **h2's own code:** a `cargo fmt` diff and 8 clippy errors.
- **h0's fixture:** `h5`, now noted on `h0`.
- **Two unowned tests:**
  `highlights::overwrite_local::local_pdf_overwrite_replaces_in_place_without_archive` (line 655,
  "replacement keeps the stem id and refreshes captured") and
  `overwrite_same_stem_source_selects_named_member` (line 1658, "v2 keeps its stamp after the named
  overwrite").

The two unowned failures started with `5c9b6e42`, a standalone tale from athena agent `181` that
stamps a minute-precision `captured` time and also edited that test file. The epic landers will
clear their own red; nobody will clear this. The Release train has not shipped since `v0.4.0`
(10-27). Your hosts track master, so this mainly affects crates.io users and release-gated beads such
as `g3`, but it also means every lander re-triages these failures.

**Recommended solution.** Decide the intended contract first: should an overwrite refresh `captured`
to a minute stamp, or keep the original? Then fix `highlights_ref/{create,duplicate}.rs` or the
assertions to match, and document the rule in `docs/highlights-ref-sync.md`. Run `cargo test --test
cli highlights::overwrite_local` and confirm on the next master CI. No running epic touches
`highlights_ref/`.

### 8. Alert on hostile activity on athena: [`8r`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-8r/README.md)

**Why.** On 2026-10-17 a miner ran on athena at load ~70 for about five hours before anyone noticed
(`research:202610/athena_plex_compromise_incident_report.md`). athena runs most of your agent fleet.
`cdx` queried its live Prometheus: only the `athena.apt` (8) and `athena.disk-space` (5) rule groups
exist. There is no service-account CPU, writable-directory execution, or mining-egress rule.

**Recommended solution.** This work lives in the tailnet infrastructure source, not bob-cli code.

- Add per-user/process CPU telemetry (process-exporter or a textfile collector), an "exec from
  `/tmp`, `/var/tmp`, `/dev/shm`, or a deleted binary" check, and nft egress counters for common
  mining ports as a secondary signal.
- Tune the rules against legitimate Plex transcoding and agent build load; host load alone is not
  enough.
- Alert when the collector itself goes stale.
- Reuse the working Alertmanager → Postfix/Mailjet → Gmail route (the `8v.land` note). Do not build a
  second delivery stack.
- Acceptance: synthetic inputs fire and resolve through that route, and the rules survive a restart.

Pair `9x` (vault-sync halt alerts) onto the same route afterwards.

### 9. Make link consumption keep notes and unrelated entries: [`7q`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-7q/README.md)

**Why.** Capture already keeps authored notes, deletes only the entries it emptied, and matches links
by identity (PDL8–PDL10). Three other paths still use the older behavior:

- `bob task reconcile` blocked-link consumption removes whole subtrees.
- `task_complete` retirement (`retirement.rs:168`) runs unrestricted `plan_empty_pomodoro_removals`,
  deleting untouched placeholder entries.
- Plugin Depends-On consumption removes whole subtrees.

So the same blocked task's link loses your notes, or an unrelated planned slot vanishes, depending on
which surface consumed it. This is a quieter version of #3's problem. Only `cdx` ranked it, but the
source evidence is direct.

**Recommended solution.**

1. Record the retention decision now, through `/sase_memory_write` into the `decisions` web, and keep
   it consistent with #3's timed-row rule.
2. Implement the three paths only after `h2` and `h4` land, then rebase.
3. Add cross-writer parity vectors in `docs/task-dependencies.md` §13.14: nested notes, aliased links
   that resolve to one task, untouched empty placeholders, and timed rows. Show that a second reconcile
   is a no-op.
4. Keep the accepted policy that capture drops prerequisites while plugin gestures retain consumption.

### 10. Render emoji in generic ref PDFs: [`e9`](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-e9/README.md)

**Why.** `render_temp_pdf_from` (`highlights_ref/create.rs:5890`) sets DejaVu fonts with no fallback.
MuPDF text extraction of all 498 `lib/chat/*.pdf` found U+FFFD in 193 of them (39%, 2,547
occurrences). Emoji such as 🍅, ✅, and ⚠️ print as tofu and extract as garbage, which hurts both
reading and the annotation and code catalogs. Note snapshots already solved this with
`NotoEmoji-Regular.ttf` and a glyph-table Lua filter.

**Recommended solution.** Route the generic pandoc → XeLaTeX path through the snapshot template's
fallback, or add a fontspec fallback family. Add a golden test that renders 🍅 and checks the
extracted text. A previewed re-render backfill of the affected PDFs can follow as a separate step,
gated on Highlights coordination. Start after #7, because both edit `highlights_ref/create.rs`.

## 4. Launch plan

| Order | Launch | Same time as | Must finish first |
|---|---|---|---|
| A | #1 plugin tests (one worker) | #2, #4, #5, #7, #8 | nothing |
| A | #2 `fy` (plan first; L) | #1, #4, #5, #7, #8 | nothing; force-sync `e4` now if you approve |
| A | #4 periods brief (`gs`→`gt`) | everything in A | nothing; target before Monday 11-09 |
| A | #5 vault `AGENTS.md`/`.gitignore` | everything in A | nothing |
| A | #7 `h6` | everything in A | nothing |
| A | #8 `8r` | everything in A | nothing |
| A | #6 `h7` | everything in A | coordinate the backslash test with `185.f0.f2` |
| B | #3 `g4` | B items | #1 landed; your option-1 call |
| B | #9 `7q` decision record | B items | #3's retention rule |
| C | #9 `7q` implementation | — | `h2.land` and `h4.land` finished |
| C | #10 `e9` | — | #7 landed |

Ready task beads still go through TaskTriage and then `sase bead work <id>`.

## 5. Runners-up, and beads that wait for a running epic

| Bead(s) | Why not in the ten | When to pick it up |
|---|---|---|
| `gd`, `f2`, `g8` (+`bo`, `gz`) | `__complete` tests built on `bob_command()` run on the 150 ms production deadline and flake under load. This is a real agent tax, but `h2` is adding completion tests now. | After `h2.land`. Route every `__complete` through `bob_completion_command()` and add a grep lint. |
| `9x` | Vault-sync halt alerts. Valuable, but no unnoticed halt has happened yet. | After #8, on the same alert route. |
| `f8` | Athena-only CPU budgets; passes on apollo. | Profile on athena; do not just raise budgets. |
| `fz`, `ej` | Chromium screenshot hangs (unbounded CDP calls); a 5 s wall-clock flake. | `ej` can ride with #1; give `fz` its own worker. |
| `dq` | Release drops only the Mac preview; vault writes are correct. `pomodoro_blocks.rs` is in active `h2` churn. | After `h2` and `h4` land. |
| `h1`, `gc` | Midnight wrap of `=-N` starts; capture `!` latency (95–220 ms against a 70 ms budget). Both sit in `h2`'s code. | After `h2.land`. Align `h1` with `h2`'s midnight refusal. |
| `gu`, `gv`, `gw`, `gx` | The rest of the brief cluster. | In #4's worker, after `gs` and `gt`. |
| `e0`, `ei` | SASE handoff and landing commit-loss bugs. | Route to the sase project. |
| `30`, `5g` | The Mac crontab cannot be installed over ssh. | One Mac Terminal session by you. |
| ~25 "record decision X" memory beads | Each is cheap but needs your acceptance. | One batched review session. |

## Close or narrow before anyone works them

| Bead(s) | Action | Evidence |
|---|---|---|
| `f3`, `fu`, `dz`, `eo`, `fj`, `fp` | Close as done | bob-mac-capture `933091b` and `2884ea2`; run 41888215951 at `4906d94` passed Build, Test, Bundle, Launch smoke, and Install. |
| `dx` | Close | `test-ledger-tools-lane-walk.cjs` passes 10/10 at `b9f47f3`. |
| `fh` | Close | Its own note says it no longer reproduces; today's clippy errors are in `h2`'s files. |
| `et` | Narrow to the freshness test | The gcal-events half passes 25/25. |
| `e4` | **Keep open** | The drift is live today. Close it after `fy` lands, or after an approved force-sync. |
| `8a` | Narrow | Long flags are refused now; re-check short flags after `h0` lands. |
| `ge` | Re-scope | After `933091b`, only the grammar-3/4 fixture JSONs remain to audit. |
| `h5` | Leave for `h0.land` | Caused by `h0`'s `via` field; noted on `bob-cli-h0`. |

## Method and limits

- **Inputs.** Five independent reports, now in this folder as `__cdx`, `__cld`, `__grk`, `__mus`, and
  `__gem`. Each researcher screened all 169–170 ready task beads and checked both hosts.
- **My checks.**
  - The bead store via `sase bead list -s ready -s snoozed -t task` (170 ready, 5 snoozed), plus
    audited reads of `gy`, `g4`, `fy`, `e4`, `8r`, `9x`, `7q`, `dq`, `e9`, and `h5`.
  - Agent rosters on both hosts, including the `185` chain's raw prompts.
  - `gh run list` and `gh run view` for bob-cli and bob-mac-capture.
  - A dry-run `bob plugins sync` and a blob-hash comparison of the vault's deployed plugin files
    against bob-plugins history.
  - bob-plugins `node --test` runs of the eight disputed files.
  - The vault's `AGENTS.md` and `.gitignore`.
  - Git history for each pick's files.
- **Beads written.** I filed `bob-cli-h6` and `bob-cli-h7` (type `ci`, size `large`, ready, with
  related links to `h5`, `1x`, and `f3`), and appended one `DISCOVERED ISSUE` note to `bob-cli-h0`. I
  changed no other bead state, deployed no plugins, and did not edit the vault.
- **Not done.**
  - I did not run `cargo test` or `just check` locally; bob-cli status comes from CI.
  - I did not reproduce `g4` or `7q` end to end; `cdx` did for `g4`, and `7q` rests on source reading.
  - The Mac run for `3cf0c6d` was still in progress at writing time, so a 185-chain push may or may
    not change the Go To picture.
  - I dropped a planned ordering figure because it could not render legibly at PDF width; the launch
    plan table carries the same constraints.
- **Snapshot warning.** Agent rosters and CI states change hourly. Re-check both hosts before each
  launch.
