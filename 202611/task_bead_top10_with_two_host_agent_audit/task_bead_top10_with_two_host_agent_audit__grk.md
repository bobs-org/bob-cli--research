# Highest-impact ready task beads (live-epic conflict audit)

- **Researcher:** `research.3b.grk` (Grok 4.6)
- **Date:** 2026-11-04
- **Project:** bob-cli
- **Question:** Which ready task beads should Bryan start next, after checking live SASE agents on apollo and athena for epic conflicts?

## Recommendation

Start **ten ready task beads**. The first six are a single bob-plugins `npm test` hygiene batch that currently accounts for most lander corroboration in this project. The next two repair stale vault plugin deploys. The last two are independent: a process rule that keeps shipping broken macOS CI, and a periods-brief correctness bug that already poisoned seventeen weekly Review drafts.

Launch the plugins CI cluster as **one worker** (or a two-commit stack in one checkout). Parallel agents on `bob-plugins` will collide. Launch `bob-cli-fy` and `bob-cli-e4` after that cluster, or in parallel with it, because they live in `bob-cli` deploy code and the live vault, not in plugin tests. Launch `bob-cli-1x` and `bob-cli-gs` in parallel with either batch.

Do **not** start capture, transfer, Mac Capture UI, idle-agenda, successor-offer, template-shelf, Pomodoro-homes, or relation-label task beads while `bob-cli-h0`, `bob-cli-h2`, `bob-cli-h4`, session `185`, and the assigned in-progress epics still own those files.

## Method

1. Snapshot the bob-cli bead store: 2225 beads, **169 ready tasks**, 21 in progress (13 plans + 8 phases), 3 open (1 plan + 2 phases of live epics), 5 snoozed tasks.
2. Rank ready tasks by corroboration (`plus_one_count`), type (ci / bug / flake / feature / memory), size, user-visible impact, and whether the failure is still in source.
3. List live SASE agents on **apollo** (`sase agent list -j`) and **athena** (`ssh athena sase agent list -j`).
4. Exclude ready tasks whose files or contracts overlap a live or assigned epic.
5. Spot-check bob-plugins source for the top CI beads (confirmed still present).
6. Audited `sase bead read` of the ten ranked IDs.

This report ranks **task** beads only (`sase bead ready`). In-progress epics are conflict context, not candidates.

## Backlog shape

| Status / type | Count | Notes |
|---|---|---|
| Ready tasks | 169 | 76 feature, 35 memory, 31 bug, 19 ci, 7 flake, 1 untyped |
| Plus-ones on ready tasks | 116 | **86 of 116 are on `ci` beads** |
| In-progress | 21 | 13 epic plans + 8 phases |
| Open plan | 1 | `bob-cli-ex` (project-note seals) |
| Snoozed tasks | 5 | Wake gates still in the future or already due as follow-ups |

The six highest-plus-one CI beads (`eh`, `et`, `ff`, `f1`, `f7`, `f8`) carry **72 of 116** ready-task plus-ones (62%). Independent landers keep rediscovering the same red `npm test` on bob-plugins. That is the highest-leverage work in this store.

## Live agents

### Apollo (this host)

Bob-cli work that is actually running or queued:

| Agent | Status | Clan / session | Meaning |
|---|---|---|---|
| `bob-cli-h2.4` | RUNNING | epic `bob-cli-h2` | Whole-stack overlap guard for `x=` past Pomodoros |
| `bob-cli-h2.5`, `.6`, `.land` | WAITING | epic `bob-cli-h2` | Docs and Mac "record past work" card |
| `bob-cli-h0.8` | QUEUED | epic `bob-cli-h0` | Move-card submit / chaining / docs for `- ^^` |
| `bob-cli-h0.land` | WAITING | epic `bob-cli-h0` | Land agent for parent-task move bullets |
| `research.3b.*` | RUNNING / WAITING | this swarm | Ranking reports; no product edits |

Also on apollo, outside bob-cli: `research.3a.*` and `cd--code` on `gh_sase-org__sase`. They do not own bob-cli task beads.

### Athena

Bob-cli work that is actually running or queued:

| Agent | Status | Clan / session | Meaning |
|---|---|---|---|
| `bob-cli-h4.1`, `.2`, `.3` | RUNNING | epic `bob-cli-h4` | Transfer landing blocks, merge records, dry-run description |
| `bob-cli-h4.4`, `.5`, `.6`, `.land` | WAITING | epic `bob-cli-h4` | Mac transfer / landing / refusal cards |
| `185--3` | RUNNING | session `185` (code) | Continuation after a failed `just test` + Mac `portable-check`; touching capture-language alias / `past.rs` scope |
| `185.f0`, `185.f0.f1` | WAITING | session `185` | Follow-on slots after `185` |

Athena also hosts sase-project epics (`sase-1qz`, `sase-1r8`, `sase-1r2`, `sase-1n6.11`) and agent `18b`. Those are sase work, not bob-cli task beads.

### Assigned epics with no live runner right now

These beads are still `in_progress` and still own their design space, even when no process is running:

- `bob-cli-28` — solo `@route:id` / `^route:id`
- `bob-cli-3j` — shell completion (`updated` 2026-11-03)
- `bob-cli-5w` — successor links on close (`updated` 2026-11-02)
- `bob-cli-66` — idle Pomodoro agenda
- `bob-cli-87` — beautiful note snapshots in `bob ref create`
- `bob-cli-8b` — saved capture templates
- `bob-cli-9k` / `bob-cli-9k.8` — Pomodoro homes
- `bob-cli-bj` — relation label vocabulary
- `bob-cli-d2` — saved Markdown for research refs
- `bob-cli-ex` — **open** epic, project-note seals (`@route^id@`)

Ready follow-ons of those epics wait until the epic's land agent finishes.

## Conflict exclusions (do not start now)

| Ready bead | Why it waits |
|---|---|
| `bob-cli-h1` | Past-offset Pomodoro clock vs live `bob-cli-h2` / session `185` (`past.rs`) |
| `bob-cli-8a`, `ge`, `dq`, `gk`, `gc` | Capture parser / `!` close path vs `h0`/`h2`/`h4`/`185`/`5w` |
| `bob-cli-f3`, `fu`, `dz`, `fp`, `fj` | bob-mac-capture XCTest / Build vs live `h4` Mac phases |
| `bob-cli-68`, `69`, `6a`, `fg` | Idle-agenda follow-ons of `bob-cli-66` |
| `bob-cli-9n`, `g5` | Pomodoro homes follow-ons of `9k` |
| `bob-cli-83`, `8h`, `8i` | Template shelf vs `bob-cli-8b` |
| `bob-cli-7j`, `fm` | Successor offers vs `bob-cli-5w` |
| `bob-cli-g8`, `gd`, `f2` | Shell-completion deadlines vs `bob-cli-3j` |
| `bob-cli-gp` | Monday Review automation; inherit `gs`–`gx` brief defects |
| `bob-cli-aa`, `ah`, `cp`, `e3`, `6q` | Snoozed; wake gates still apply |

`bob-cli-f3` (+4, large, macOS Test step red on master) is the highest-impact bead in that exclusion list. Pick it up the moment `bob-cli-h4` lands. `bob-cli-fu` is the rest of that same red Test step.

## Ranked list

### 1. `bob-cli-eh` — ledger-tools startup tests, single `onLayoutReady` slot

- **Type / size:** ci / small
- **Corroboration:** **+24** unique reporters (highest in the store)
- **Impact:** Two deterministic bob-plugins Node failures since `1295e52`. Every lander that runs `npm test` re-triages them.
- **Conflict:** None with live runners. Test harness only.
- **Still in source:** `scripts/test-ledger-tools-note-ready.cjs` assigns `handlers.onLayoutReady = callback` (one slot). `metadataCache.on` in the same fake already chains. `setupGcalEvents` registering a second `onLayoutReady` overwrites the first; expected scans 2, actual 1.
- **Solution:** Make the workspace fake multicast `onLayoutReady` (array of callbacks, invoke in registration order). Share that fake with `test-ledger-tools-relation-index.cjs`. Run both files isolated and under full `npm test`. Do not change production gcal/layout registration to paper over the fake.

### 2. `bob-cli-et` — gcal-events and freshness tests read the wall clock

- **Type / size:** ci / small
- **Corroboration:** **+17**
- **Impact:** Date bombs from 2026-10-31 onward. Same `npm test` as `eh`.
- **Conflict:** None. Linked to `f7` as a sibling time-fixture family; same batch, different files.
- **Still in source:** `test-ledger-tools-gcal-events.cjs` pins `now = new Date(2026, 9, 30, 9)` then later calls `todayDailyPath(new Date())`. `test-ledger-tools-freshness-namespace.cjs` uses `formatLocalDate(new Date())` in the due-key reload test.
- **Solution:** Thread the fixture `now` through create-listener and freshness reload helpers. Ban bare `new Date()` in those two files. Keep production "today" behavior. Prove with TZ=UTC and TZ=America/New_York on a clock set after 2026-10-31.

### 3. `bob-cli-ff` — schedule-work-log future date expired on 2026-11-02

- **Type / size:** ci / small
- **Corroboration:** **+10**
- **Impact:** Pending-row stays `[/]` because `2026-11-02` is no longer in the future. Same suite.
- **Conflict:** None.
- **Still in source:** `scripts/test-navigation-hotkeys-schedule-work-log.cjs:148` still opens scheduling review with `"2026-11-02"`.
- **Solution:** Drive the schedule date from a frozen harness clock (`today + 7 days`), or freeze today to a day before the fixture date. Never hard-code a civil date that expires. Assert Blocked (`[?]`) plus Work Log write.

### 4. `bob-cli-f1` — command-mode DOM test throws when Chromium is missing

- **Type / size:** ci / small
- **Corroboration:** **+9**
- **Impact:** Apollo (no Chromium on PATH) fails `npm test` in `test-command-mode-sheet-sequence-dom.cjs`. Every apollo lander rediscovers it.
- **Conflict:** None. Session `185` is on athena capture-language, not this test.
- **Still in source:** `findChromium()` throws `Could not find Chromium. Set CHROMIUM_PATH...` instead of skipping.
- **Solution:** Skip with a clear reason when no browser exists. Hard-fail when `CHROMIUM_PATH` is set but invalid, and in CI. Optional follow-up: install Chromium on apollo so the test runs there. Keep the production-DOM coverage when a browser is present.

### 5. `bob-cli-f7` — keep-inbox forced-check notice asserts UTC

- **Type / size:** ci / small
- **Corroboration:** **+6**
- **Impact:** Deterministic fail under America/New_York (`12:30` vs expected `16:30`). Passes with `TZ=UTC`. Athena landers hit it constantly.
- **Conflict:** None. Related to `et` (clock fixtures); same batch.
- **Still in source:** `test-ledger-tools-keep-inbox.cjs` fixtures `next_check_at: "2026-10-31T16:30:00Z"` and expects notice text `try after 16:30`. Production formats local time.
- **Solution:** Build the expected notice from the fixture timestamp in the test TZ (or assert a formatted local clock). Keep production local-time copy. Verify UTC and America/New_York.

**Batch note for ranks 1–5:** one bob-plugins worker, one checkout, five small commits or one commit with five file groups. Fold `bob-cli-ej` (+4 flake, 5 s Live Preview wall-clock gate) into that same worker as a sixth file if the suite is already open. Do not launch six agents.

### 6. `bob-cli-fy` — `bob plugins sync` keeps refusing committed dirty deploys

- **Type / size:** bug / large
- **Corroboration:** 0 plus-ones of its own; it is the root cause behind `e4` (+3, reopened) and repeated lander force-syncs (`fd`, `ey`, `fl.6.1`).
- **Impact:** Vault plugins stay on old builds after landed work. Bryan runs stale Obsidian plugins until a lander hand-proves ancestry and force-syncs. Every plugin epic pays that tax.
- **Conflict:** Live epics today are capture / Mac Capture / past Pomodoros. `fy` is `src/native/plugins/deploy.rs` plus the agent sync-before-commit workflow.
- **Solution:** Keep the cu protection against a *foreign dirty* deploy. Add an overwrite-ok path when the stamped tree is an ancestor of origin/master (or the host re-syncs with a clean stamp after `sase stitch create` commits). Tests: dirty workspace commit → merge to master → sync from a second checkout succeeds; a truly other-checkout dirty tree still refuses. Document the new rule in plugin-sync help.

### 7. `bob-cli-e4` — vault `bob-navigation-hotkeys` and `task-status-cycler` stuck dirty

- **Type / size:** bug / small
- **Corroboration:** **+3**, one reopen. Recurred 2026-11-02 after an Oct 30 "all synced" note.
- **Impact:** Obsidian is still running pre-theme-card / pre-complete-line-guard builds of those two plugins until someone force-syncs from a proven master checkout.
- **Conflict:** Instance of `fy`. Safe to reconcile the vault now; `fy` stops the next recurrence.
- **Solution:** From a clean bob-plugins master checkout, prove HEAD contains the stamped commits, then force-sync those two plugin ids. Confirm `bob plugins list` reports them synced. Treat any new refusal as `fy` evidence, not a third bead.

### 8. `bob-cli-f8` — task-wikilink snapshot/rank CPU budgets fail on athena

- **Type / size:** ci / large
- **Corroboration:** **+6**
- **Impact:** Isolated athena runs miss `warm snapshot plus order` (50 ms, observed ~75–83 ms) and sometimes `rank 5000 rows` (12 ms, observed ~12.2–12.9 ms). Apollo has passed the same file. Landers on athena keep classifying it.
- **Conflict:** Performance test only. After ranks 1–5, in the same bob-plugins checkout.
- **Still in source:** `scripts/test-block-id-prompt-task-wikilink-index-performance.cjs` still gates warm snapshot at 50 ms.
- **Solution:** Profile the warm snapshot on athena (Node v22). If the work is real CPU, raise the host floor with a documented athena budget *or* speed up snapshot/order (cache, less copy). Keep isolated CPU timers; do not turn this into a full-suite wall-clock flake (`ej` is that class). Record apollo vs athena numbers in the close note.

### 9. `bob-cli-1x` — document watching bob-mac-capture CI after every push

- **Type / size:** memory / small
- **Corroboration:** **+4** over a month (unwatched Mac pushes still landing)
- **Impact:** Linux `portable-check` cannot type-check `BobMacCapture*`. Agents keep pushing Mac-only breaks. `bob-cli-f3` is the current red master Test step; this bead is the process hole that lets that class of failure ship.
- **Conflict:** Documentation / agent instructions. No overlap with `h4` code. The 2026-10-27 triage already recorded a partial cover in bob-mac-capture `AGENTS.md` and `scripts/dev/macos-ci-check`; the remaining gap is an explicit "watch CI to green after every push" rule.
- **Solution:** Finish the filed `sase.md` Repositories bullet: after any push to `bobs-org/bob-mac-capture`, watch with `gh run watch --repo bobs-org/bob-mac-capture --exit-status` via `/sase_monitor` until the full macOS job is green. Point at `docs/develop/ci.md`. Keep iterating on the same SHA family until Test, bundle, launch, and install steps run.

### 10. `bob-cli-gs` — `bob periods brief` ignores `done/` archive paths

- **Type / size:** bug / medium
- **Corroboration:** 0 plus-ones (filed 2026-11-04 from the `bob-cli-gr` lander after seventeen weekly Review drafts)
- **Impact:** Weekly Reviews already drafted from the brief dropped archived-task minutes and printed dead `[[note#^id]]` links. Monday automation (`bob-cli-gp`) will copy the same defect. Sibling beads `gt`–`gx` share `brief.rs`.
- **Conflict:** No live periods epic. `gr` already closed. Do **not** parallelize `gt`/`gu`/`gw` in other checkouts; they edit the same functions.
- **Solution:** In `src/native/periods/brief.rs`, resolve task ids through `done/` homes when the live note no longer has the block. Count archived completions in `linked_minutes` / `linked_for`. Rewrite dead source-note links to the archive path. Prove with `bob periods brief 2026-W43 -f md` (bob root currently lists no tasks despite `done/bob_done#^root-parent`). Land `gs` before `gt` (split vs whole-Pomodoro minutes), then `gu` (Still open uses today's vault).

## How to run them

Ready task beads still go through TaskTriage, then `sase bead work <id>`. Suggested launch order:

1. One plugins worker covering `eh`, `et`, `ff`, `f1`, `f7` (and `ej` if the suite is open).
2. Same checkout, second commit/worker: `f8`.
3. Parallel: `fy` (bob-cli deploy.rs) and a short `e4` vault reconcile.
4. Parallel: `1x` (memory) and `gs` (periods brief).
5. After `h4` lands: `f3` then `fu` (restore a green macOS Test step).

## Honorable mentions (not in the ten)

| Bead | Why it is next-tier |
|---|---|
| `bob-cli-ej` | +4 flake in the same plugins suite; fold into the rank 1–5 worker |
| `bob-cli-f3` / `fu` | Highest Mac CI impact; wait for `h4` |
| `bob-cli-e9` | Emoji tofu in 193/498 chat PDFs; independent of live `87` (note snapshots already have Noto fallback) |
| `bob-cli-e0` | `sase plan propose` drops uncommitted lander edits; fix lives in sase, already corroborated by `sase-1ph.land` |
| `bob-cli-gy` | Vault `/sase_git_commit` leaks plan archives into `~/bob/sdd/plans/`; process + sase stitch |
| `bob-cli-30` | Mac crontab drift; needs a Mac Terminal, not SSH |
| `bob-cli-9x` / `8r` | Cross-host vault-sync halt alerts and athena miner alerts; real ops, larger than a first batch |
| `bob-cli-fz` | Chromium screenshot hangs on apollo; large flake, needs harness timeouts and process-group cleanup |
| `bob-cli-de` | Catalog CLI entry-count assertion; current tree already expects 71, so this is a recurring pin, not today's 54-vs-55 failure |
| `bob-cli-ax` | Permanently down Prometheus `clipster_server` job on athena |

## Source checks (2026-11-04)

Performed in the linked `bob-plugins` checkout opened for this run:

- `test-ledger-tools-note-ready.cjs` still uses a single-slot `onLayoutReady`.
- `test-ledger-tools-gcal-events.cjs` still calls `todayDailyPath(new Date())`.
- `test-navigation-hotkeys-schedule-work-log.cjs` still schedules `"2026-11-02"`.
- `test-command-mode-sheet-sequence-dom.cjs` `findChromium()` still throws.
- `test-ledger-tools-keep-inbox.cjs` still expects `try after 16:30` for a `Z` timestamp.
- `test-block-id-prompt-task-wikilink-index-performance.cjs` still budgets warm snapshot at 50 ms.

## Limits

- Ready-task `is_ready_to_work` is false for every ready bead in this dump; they still need TaskTriage before `sase bead work`.
- Plus-one counts measure lander tax, not Bryan's personal pain. Ranks 6, 7, and 10 exist to cover vault plugins and weekly Reviews, which plus-ones under-count.
- Session `185`'s live reply is a draft; the conflict call is from its prompt (capture-language alias / `past.rs` / note-pull fixture), which is enough to keep capture grammar beads off this list.
- This researcher did not read peer swarm reports.
