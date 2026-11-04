# Which bob-cli Task Beads To Work Next: A Conflict-Checked Top 10

*Researcher `cld` · 2026-11-04 (about 15:15–15:45 EST) · bob-cli at `87eecb1a`, bob-plugins at
`b9f47f3`, bob-mac-capture at `5960b31`*

## Summary

The bob-cli task-bead backlog holds **174 task beads**: 169 `ready` and 5 `snoozed`. By
type that is 81 feature, 35 memory, 31 bug, 19 ci, 7 flake, and 1 untyped. I read every
bead, checked the agents running on apollo and athena, and re-ran the most-cited
failures on today's trees. Ten work items are clearly worth doing now. Several bundle
beads that one worker should fix together because they share a file or a root cause.

The three highest-leverage items:

1. **Make bob-plugins `npm test` green.** Five beads carry 66 independent +1s between
   them. I re-ran the tests today and six assertions still fail. Every lander that
   touches bob-plugins pays this tax again.
2. **Fix dirty plugin deploys (`bob-cli-fy`).** Right now Bryan's vault runs
   `bob-ledger-tools` and `bob-navigation-hotkeys` from an *uncommitted* agent build.
   Every later sync from master refuses to replace it.
3. **Fix the `bob periods brief` defects (`gs`–`gx`).** These six bugs, all in one
   file, corrupt every weekly Review draft. The next weekly Review falls on Monday
   2026-11-09, so they need to land before then.

Four broader findings shape the list:

- **Six Mac CI beads are already fixed.** `f3`, `fu`, `dz`, `eo`, `fj`, and `fp` were
  resolved by bob-mac-capture `933091b` and `2884ea2`, and master went fully green in
  run 41888215951. All six should be closed, not worked.
- **bob-mac-capture master is red again, and no bead tracks it.** Today's Go To tales
  broke `CaptureTaskGotoPanelTests` and `CaptureBackslashGotoTests`, and the Test step
  also hit the 15-minute hang guard.
- **The bob-cli release train has not shipped since `v0.4.0` (2026-10-27).** Every
  Release run since 2026-10-28 has failed or been cancelled. Some of today's red
  belongs to the running epics `h0` and `h2`. Two `highlights::overwrite_local` test
  failures from today's captured-time change (`5c9b6e42`) have no owner.
- **Four running epics claim the capture engine and the Mac capture panel for the next
  few hours:** `h0` and `h2` on apollo, `h4` and the `185` chain on athena. Capture
  bugs such as `h1`, `8a`, `gk`, `dq`, and `gc` should wait until those land.

## 1. What Is Running Right Now

### apollo (`sase agent list -j`, 15:13–15:20 EST)

| Agent(s) | Status | What it owns |
| --- | --- | --- |
| `bob-cli-h0.8`, `bob-cli-h0.land` | QUEUED / WAITING | Epic **bob-cli-h0** "Choose parent tasks to move in with a `- ^^` capture bullet". Phases 1–7 closed; h0.8 is the Move card submit flow and docs. It touches the capture planner, the `-m/--move-in` CLI flag, capture-parse spans, the grammar version, and the Mac Move card. |
| `bob-cli-h2.4` (running), `h2.5`, `h2.6`, `h2.land` | RUNNING / WAITING | Epic **bob-cli-h2** "Record past Pomodoros with x=". h2.4 is the whole-stack overlap guard and `!` edge repair, h2.5 the docs, and h2.6 the Mac "Record past work" card. It touches `capture_language/editor_pomodoro.rs`, `past.rs`, `capture/pomodoro_start.rs`, and the Pomodoro close engine. |
| `research.3b.*` | RUNNING | This research swarm. |
| `research.3a.*`, `cd--code` | RUNNING / WAITING | sase project only, so no bob-cli conflict. |

### athena (`ssh athena sase agent list -j`)

| Agent(s) | Status | What it owns |
| --- | --- | --- |
| `bob-cli-h4.1`–`h4.6`, `bob-cli-h4.land` | RUNNING / WAITING | Epic **bob-cli-h4** "Transfer previews — see every `>` move and merge before it lands". It covers bob landing blocks, merge and move records, and dry-run descriptions, plus Mac transfer, landing, pending, and refusal cards (`CapturePanelView`, notifications, VoiceOver). |
| `185--3` (running), `185.f0`, `185.f0.f1` | RUNNING / WAITING | Non-bead plan chain. In the Mac capture editor it makes `.` type `^`, `;` type `:`, and `,` type `+` after `@route`, including at bullet starts in `@foo[:^]bar@` captures. It is currently running `just test` plus the bob-mac-capture `portable-check`. It touches the Mac separator toggle and editor, and possibly bob completion. |
| `sase-1qz*`, `sase-1r8*`, `sase-1r2*`, `sase-1n6*`, `18a`, `18b` | various | sase project: agent hijack, publication, and release work. None of them owns the SASE handoff commit-loss bugs filed here (`e0`, `ei`). |

### Ten idle epics

Ten older epics have **every phase closed but the epic still `in_progress`/`open`**, and
no agent is running for any of them: `bob-cli-28`, `3j`, `5w`, `66`, `87`, `8b`, `9k`,
`9k.8`, `bj`, `d2`, and `ex` (`open`, 4/4 phases closed). They create no live
conflict. Their landings were never finalized, though, and some beads still name them
as owners. For example, `3j` "owns" the completion engine referenced by `f2` and `gd`.
Re-running `sase bead work <epic>` or closing them would clear that up.

### Conflict map used for ranking

| Area | Claimed by | Beads that should wait |
| --- | --- | --- |
| Capture grammar, capture-parse editor, `capture/cli.rs` flags | h0, h2, h4, 185 | `gk`, `8a` (the short-flag remainder; h0 just added `-m`), `ge` |
| `capture/pomodoro_start.rs`, Pomodoro close and record | h2 | `h1` (midnight wrap of `=-N` starts; h2's plan already adds the A7 midnight refusal for `x=`) |
| Capture preview blocks (`pomodoro_blocks`, landing blocks) | h4 | `dq` (ranked, but start it after h4 lands), `2u` |
| Mac capture panel, editor, and cards | h0.8, h2.6, h4.4–h4.6, 185 | `7g`, `fa`, `73`, `76`, `ds`, `83`, `6a`, `68`, `69`, `a9`, `e5` |
| Capture `!` close path | h2.4 (`!` edge repair) | `gc` |

My top-10 picks avoid these areas, or are explicitly sequenced after the owning epic
lands.

## 2. What I Verified Today

### bob-plugins `npm test` is red on master `b9f47f3`

I ran `node --test` on the relevant files:

| File | Result | Bead |
| --- | --- | --- |
| `test-ledger-tools-note-ready.cjs` | 40 pass / **1 fail** ("the startup storm is linear") | `eh` |
| `test-ledger-tools-relation-index.cjs` | 11 pass / **1 fail** (layout-ready scan never finishes) | `eh` |
| `test-ledger-tools-freshness-namespace.cjs` | 8 pass / **1 fail** (reload event `[]`) | `et` |
| `test-ledger-tools-gcal-events.cjs` | 25 / 25 **pass**, so `et`'s gcal half is now fixed | `et` |
| `test-navigation-hotkeys-schedule-work-log.cjs` | 16 pass / **1 fail** (hard-coded 2026-11-02 is no longer in the future) | `ff` |
| `test-command-mode-sheet-sequence-dom.cjs` | 0 pass / **1 fail** ("Could not find Chromium") | `f1` |
| `test-ledger-tools-keep-inbox.cjs` | passes under UTC; under `TZ=America/New_York`, 32 pass / **1 fail** | `f7` |
| `test-ledger-tools-lane-walk.cjs` | 10 / 10 **pass** | `dx` (stale, close it) |
| `test-block-id-prompt-task-wikilink-index-performance.cjs` | 5 / 5 pass on apollo | `f8` (athena-only CPU budget) |

### The vault runs uncommitted plugin builds

`bob plugins list` on apollo reports 6 plugins synced and 2 in `drift`. Both
`bob-ledger-tools` (1.98.0) and `bob-navigation-hotkeys` (2.73.3) were "deployed from
uncommitted build" in another agent workspace's bob-plugins checkout (`1dc272a`,
2026-11-04T07:13Z). This is `bob-cli-fy`/`bob-cli-e4` happening live, for the fourth
time.

### bob-mac-capture CI

- **Green at `78df1c9` and `4906d94`.** Run 41888215951 passed every step: Build, Test,
  Bundle, Launch smoke, and Install. Commit `933091b` ("restore green macOS CI for the
  grammar-5 gate", 2026-11-03) fixed the separator-toggle, line-case undo, task-type,
  clip-preview, keep-moving, and grammar-fixture failures. `2884ea2` fixed the build.
  So **`f3`, `fu`, `dz`, `eo`, `fj`, and `fp` are resolved**. `ge` is partly resolved:
  the inline grammar-3 bodies were bumped and the generator floor is enforced, but 65
  fixture JSONs still declare grammar 3 or 4, and some of those may be deliberate.
- **Red again since `fde8211` (backslash Go To), `70c0839`, and `5960b31` (Command-X
  completed-only).** These all came from today's Go To tales, which have no landers.
  The failing tests are `CaptureBackslashGotoTests.testInsertHelperDeclinesWhileComposingSubmittingOrLocked`
  and `CaptureTaskGotoPanelTests.testDelayedChipRefetchCannotReplaceReopenedSnapshot` /
  `testFailureOnChipRefetchRetainsRowsAndReportsError`. Run 41900858873 also tripped
  "swift test ran longer than 15 minutes". **No bead tracks this.**

### bob-cli CI and the release train

- The last tag is `v0.4.0` (2026-10-27). All 15 Release workflow runs since 2026-10-28
  failed or were cancelled. The off-clock commit `8a9ec685` is in no release, so `g3`
  is still blocked. Per `decisions:bob-cli-releases-ride-a-daily-train`, Bryan's hosts
  track master, so this mainly affects crates.io users and release-gated beads.
- Master CI run 41900846465 on `87eecb1a` fails on:
  - `cargo fmt`: a diff at `capture/task_theme.rs:1009`. Earlier diffs in h2's x= files
    are already recorded as a DISCOVERED ISSUE on `bob-cli-h2`.
  - macOS clippy: 8 deny errors in `capture_language/editor_pomodoro.rs` and `past.rs`,
    which is h2's code.
  - `capture::note_pull::np_move_groups_follow_requested_sources_in_cli_fixtures`: the
    output now carries `move_choice`, so this is likely h0's fixture drift.
  - **`highlights::overwrite_local::local_pdf_overwrite_replaces_in_place_without_archive`
    and `overwrite_same_stem_source_selects_named_member`.** These panic on "replacement
    keeps the stem id and refreshes captured". The only recent change in that area is
    `5c9b6e42` "stamp minute-precision captured time in every ref create marker", a tale
    that landed today with no lander. **No bead tracks this.**

### Small bugs re-checked in source on `87eecb1a`

| Bead | Where | Status |
| --- | --- | --- |
| `ev` | `gcal/doctor.rs:88` | still formats `"v{version}"` |
| `fr` | `stats/render.rs:604` | `warning_lines` still re-appends metric warnings |
| `h1` | `pomodoro_start.rs:28` | still wraps `% 1440` |
| `gk` | `capture_language/editor_*` | still emits no `multi_note_marker` |
| `fh` | — | its own note says it no longer reproduces on Linux (stale) |

## 3. The Ranked List

Ranking criteria, in order:

- impact on Bryan's daily data and workflow, or on every agent's gate;
- strength and freshness of the evidence;
- no conflict with running epics;
- cost.

"Size" uses the bead's own size, or my estimate for a bundle.

### #1 — Make bob-plugins `npm test` green: `bob-cli-eh`, `bob-cli-et`, `bob-cli-ff`, `bob-cli-f7`, `bob-cli-f1`

- **Why.** Together these beads carry 66 independent +1s, almost all from land agents
  that had to prove the failures pre-existed before closing their own epics. Since
  2026-10-30, every bob-plugins lander has spent time re-verifying the same six
  assertions. A red baseline can also hide real regressions in the same files. All six
  failures reproduce today (Section 2), and all are test-harness or fixture defects, not
  product bugs.
- **Recommended solution.** One small worker, test-only changes, in one commit:
  - `eh`: change the `onLayoutReady` fakes in `test-ledger-tools-note-ready.cjs` and
    `test-ledger-tools-relation-index.cjs` from a single slot to a callback list. Fire
    them all, which matches Obsidian, where `setupGcalSyncOnCreate` adds a second
    callback.
  - `et`: the gcal half already passes. Pin the clock (an injected `now`, or a `Date`
    preload) for "the reload event fires only when the due key set changes" in
    `test-ledger-tools-freshness-namespace.cjs`.
  - `ff`: compute the "future" scheduled date from the harness's `now` (now + 7 days)
    instead of the literal `2026-11-02`, or freeze the harness clock.
  - `f7`: build the expected notice with the same local-time formatter production uses,
    for example `new Date("2026-10-31T16:30:00Z").toLocaleTimeString(...)`. Run under
    both `TZ=UTC` and `TZ=America/New_York`.
  - `f1`: when no Chromium is found, `t.skip("Chromium not installed")`. Keep it a hard
    failure when `CHROMIUM_PATH` is set but invalid, or when `CI` is set.
  - Then run the full `npm test` under `TZ=America/New_York` and close all five beads.
    `ej` (5 s Live Preview wall-clock gate) and `fz` (Chromium screenshot hangs) can
    ride along if time allows, but they are flakes, not deterministic failures.
- **Size:** S overall. **Conflicts:** none; no running agent edits bob-plugins tests.

### #2 — Dirty plugin deploys never clear: `bob-cli-fy`, with `bob-cli-e4` as the live instance

- **Why.** This is the only item where Bryan's own Obsidian is wrong right now. Two
  plugins run an uncommitted agent build, and every later `bob plugins sync` from master
  refuses to replace them. Each refusal so far has needed a land agent to prove
  inclusion by hand and force-sync: `e4` (twice), `fd.2`, `ey.6`, `fl.6.1.4/.5`, and
  now `bob-cli_23`. As long as agents run `bob plugins sync` before SASE commits their
  edits, every plugin-touching epic recreates the problem.
- **Recommended solution.**
  1. At deploy time, `.bob-deploy.json` should also record a content fingerprint of
     the plugin's source subtree. One way is `git hash-object` per managed source file,
     or the tree hash of `plugins/<name>` built from the working tree. It should also
     keep the built-artifact hashes it already implies.
  2. When a later sync meets a `dirty` deploy, it treats the deploy as included, and
     overwrites without `--force`, if either:
     - the current `HEAD`'s `plugins/<name>` tree, or any tree for that path in
       `git rev-list HEAD -- plugins/<name>`, equals the recorded fingerprint; or
     - the clean build of `HEAD` reproduces the deployed artifact bytes.
  3. Otherwise keep `bob-cli-cu`'s refusal, so a genuinely uncommitted build is never
     overwritten. Add a CLI test that deploys dirty, commits the same content, and then
     syncs clean.
  4. Separately, as an operational step that needs Bryan's approval: verify the two
     drifted plugins' content against master and force-sync them, then close `e4`.
- **Size:** L (this needs a short plan first). **Conflicts:** none. This is `bob plugins`
  code, which no running epic touches.

### #3 — `bob periods brief` correctness: `bob-cli-gs`, `gt`, `gu`, `gv`, `gw`, `gx`

- **Why.** The bob-cli-gr epic drafted 17 weekly Reviews (W27–W43) from
  `bob periods brief`, and each phase hit the same defects:
  - archived (`done/`) tasks get 0 minutes and dead links (`gs`);
  - each task is credited the whole Pomodoro, so tasks outrank their roots (`gt`);
  - "Still open" reports today's vault for past periods (`gu`);
  - there is no `+N more` count (`gv`);
  - "Bryan's words" duplicates lines, truncates later days, misorders entries, and
    mangles links (`gw`);
  - cosmetic Markdown glitches (`gx`).

  Weekly Review is a recurring ritual, and the next one is Monday 2026-11-09. The
  planned Monday automation (`gp`) depends on all six fixes. Every root cause is already
  localized in `src/native/periods/brief.rs`.
- **Recommended solution.** One worker, one plan:
  - `gs`: match Pomodoro link targets against both `source_path` and `archive_path` in
    `linked_minutes` and `linked_for`/`task_key`. Render `archive_path` in `task_link`
    when it is set.
  - `gt`: split a multi-link Pomodoro's `counted_minutes()` across its links, exactly as
    the stats `root_parent` lanes do. Reuse that splitter instead of duplicating it.
  - `gv`: emit `total` and `more = total − shown` for Finished and Dropped before
    `truncate(finish_cap)`, in both the Markdown and JSON output.
  - `gw`: dedup by (date, normalized text), preferring the block-anchored daily-note
    link. Sort by (date, time-of-day) rather than link text. Trim only a real checkbox
    prefix. Skip children that are only a wikilink. Escape wikilinks inside alias text.
    Report a per-day cap instead of a global `truncate(40)`.
  - `gx`: drop the empty dates segment, and use `task_link` in "No linked minutes".
  - `gu` needs a semantics call (ask Bryan through the plan). I recommend:
    - For "Kept 3+" and "No linked minutes", rebuild state as of the span end. Keeps
      can be rebuilt from dated ROTTEN LOG entries and creation from `[created::]`, and
      tasks created after the span should be excluded.
    - For "Blocked projects", which cannot be reconstructed, omit the list when the
      period ended before today, and say so in one line.
    - Keep the "as of today" heading only for the current period.
- **Size:** M–L combined. **Conflicts:** none. No running epic touches `periods/`.

### #4 — Emoji print as missing glyphs in generic Markdown ref PDFs: `bob-cli-e9`

- **Why.** This hits the reading surface Bryan uses most. The +1 impact scan found
  U+FFFD in **193 of 498** `lib/chat/*.pdf`, which is 39% of research PDFs. Emoji such
  as 🍅, ✅, and ⚠️ render as tofu, and their text layer extracts as garbage. This hurts
  both reading and the code and annotation catalog. Note snapshots already solved this,
  with `NotoEmoji-Regular.ttf` and the `note.lua` glyph table.
- **Recommended solution.** Route the generic pandoc → XeLaTeX path (`render_temp_pdf_from`
  in `highlights_ref/create.rs`) through the same fallback the snapshot template uses.
  Either reuse `\BobFallbackFont` and the glyph-table Lua filter, or add a fontspec
  `FallbackFontFamily`-style fallback. Make sure uncovered code points both render and
  extract correctly, which matters for the text-layer rule in decision record
  `annotated-pdfs-render-on-xelatex` (proposed in `8p`). Add a golden test that renders
  🍅 and checks the PyMuPDF text. Optionally, add a previewed `--force` re-render
  backfill for the affected chat PDFs, as a follow-up gated on Highlights coordination
  (`ay`/`b0`).
- **Size:** M. **Conflicts:** none. This is not the code behind today's
  `overwrite_local` failures, but whoever fixes those (see #8) should rebase on it.

### #5 — Obsidian Ctrl+Enter deletes a closed timed Pomodoro and its minutes: `bob-cli-g4`

- **Why.** This is silent ledger data loss. When a close defers every link (for example,
  a not-started Event Task deferred to MEET), task-status-cycler deletes the closed
  `(**0800-0900** [t:: 60m])` row, while `bob capture x` keeps it. The two engines
  disagree, so Stats depend on which surface closed the session. That contradicts
  `decisions:off-clock-pomodoros-count-apart`, under which recorded session time
  survives.
- **Recommended solution.** Get Bryan's one-line confirmation of option 1: keep the
  closed timed row, matching bob. Then:
  - delete the `deferredOnlyClose` / `deletedClosedEntry` special case in
    task-status-cycler;
  - update `docs/task-status-cycler.md` and the pomodoro_clock README;
  - make the vector harness assert the full `expected_day` for
    `close-defers-not-started-off-clock`;
  - keep deleting *untimed* emptied entries, per the existing emptied-Pomodoro decision
    in `8d`.
- **Size:** S. **Conflicts:** the fix is plugin-only. h2 changes bob's close and record
  engine but not the cycler, so there is no overlap.

### #6 — Load-proof the bob-cli test gates: `bob-cli-gd`, `bob-cli-f2`, `bob-cli-g8` (optionally `bo`, `gz`)

- **Why.** `just check` and full-suite runs keep failing for completion tests that run on
  the 150 ms production `COMPLETE_DEADLINE_MS` because they are built on `bob_command()`
  instead of `bob_completion_command()`. `gd`'s sweep lists `stats.rs`,
  `stats_clock.rs`, `complete_task_complete.rs`, `complete_wikilink_task.rs`,
  `complete_relationship_owner.rs`, `task_goto.rs`, and `help.rs`; `f2` adds
  `articles.rs` and `g8` adds `complete_themes.rs`. The same thing happened to the
  wall-clock perf gates `bo` (500 ms, which recurred after its fix) and `gz` (250 ms).
  Each failure costs a phase agent a rerun and a triage note.
- **Recommended solution.**
  - Route every `__complete` invocation in `tests/cli/**` through
    `bob_completion_command()`. Add a small test or `just` lint that greps for
    `"__complete"` built on `bob_command()` and fails, so the class cannot come back.
  - For `bo` and `gz`, follow the precedent the beads cite: assert bounded *work*
    (read counts, candidate counts) instead of elapsed time, or a paired big-vs-tiny
    minimum. Leave the production deadlines unchanged.
- **Size:** S. **Conflicts:** h2 is adding completion tests (`h2.2`). Start after
  `bob-cli-h2.land` finishes, or rebase onto it. The diff touches only test helpers.

### #7 — Fix the vault's agent instructions: `bob-cli-gy`, `bob-cli-8n`

- **Why.** `~/bob/AGENTS.md` tells agents to commit vault edits with `/sase_git_commit`.
  From the vault, that archives SASE tale plans into `~/bob/sdd/plans/`, which already
  happened twice in the gr epic (`ec8ae84c5`, `7d84dcb46`). The planned Monday Review
  automation (`gp`) would leak a plan every week. The same file also still says the
  vault "is actively synced by Obsidian Sync" (`8n`), although git vault-sync has
  replaced Obsidian Sync.
- **Recommended solution.** Make one vault commit to `~/bob/AGENTS.md`:
  - Replace the commit instruction with: let `bob vault-sync` commit (it committed 15 of
    17 Review notes within seconds). If an explicit commit is needed, use plain
    `git add <your files> && git commit`, never `/sase_git_commit`.
  - Replace the Obsidian Sync sentence with git vault-sync, pointing at
    `bob vault-sync status --json`.
  - Add `sdd/` to the vault's `.gitignore` as a belt-and-braces guard.

  The SASE-side fix, never archiving plans into a repo that is not the plan's home, is
  worth a sase bead, but it does not block this.
- **Size:** S. **Conflicts:** none.

### #8 — Get bob-cli master gates green and keep them green: `bob-cli-de`, `bob-cli-b6`, `bob-cli-fo`, plus a new bead for `overwrite_local`

- **Why.** Fifteen consecutive Release runs have failed or been cancelled, so there has
  been no release since 2026-10-27. Today's causes are mostly in-flight epic work (h2's
  fmt and clippy, h0's fixture), which their landers should fix. Three beads, however,
  are gates that **break again every time a feature lands**, and each has a fresh +1
  from today:
  - `de`: the catalog CLI test asserts an exact entry count. It has broken at least
    twice (expected 54 but got 55; expected 67 but got 69), and it now hard-codes 71.
  - `b6`: `docs/develop/decisions.md` is not regenerated when a decision strand is
    added.
  - `fo`: new capture tokens ship without `search_smoke.yml` literal queries.

  The two `highlights::overwrite_local` failures after `5c9b6e42` have no owner at all.
- **Recommended solution.** After `bob-cli-h0.land` and `bob-cli-h2.land` finish:
  - `overwrite_local`: file and fix the two failures. Most likely the test or fixture
    expects the old date-only `captured` value. Decide whether the overwrite path
    should refresh it to minute precision, and assert that.
  - `de`: replace the hard-coded count with structural invariants. Every entry has an
    id and a path, ids are unique, and named sentinel entries exist. Alternatively,
    compare against a generated snapshot that `just` regenerates, so adding a command
    cannot break it.
  - `b6`: have `sase memory` publication, or a `just check` pre-stage, run `just docs-gen`
    for `docs/develop/decisions.md`. At minimum, make the docs-check failure message
    name the exact command. Then regenerate the page.
  - `fo`: make the capture-token coverage test report the missing YAML stanza
    verbatim, and add the current missing literals.
  - Re-run `just check` and `just docs-check`, then confirm the next scheduled Release
    run.
- **Size:** S–M. **Conflicts:** wait for the h0 and h2 landers, because they are
  fixing their own red on the same gate.

### #9 — Status rewrites in today's `## Pomodoros` crash the preview tracker: `bob-cli-dq`

- **Why.** Any status-changing capture on a task line inside today's `## Pomodoros` trips
  `debug_assert!(false, "pomodoro entry vanished without a ref")`
  (`capture/pomodoro_blocks.rs:859`). Examples include cancel-label `~…|"duplicate of"`
  and toggles of day tasks. Debug builds panic with exit 101. Release builds silently
  drop `pomodoro_blocks`, so Bob Mac Capture loses its Pomodoro preview for a common
  gesture. A clear repro script is in the bead.
- **Recommended solution.** Give in-place task-line status rewrites an explicit block ref
  in the tracker, keyed by line identity. Do not carve them out of the guard, so the
  guard keeps catching genuine vanishes. Add the bead's scratch-vault case as a CLI
  test, in both debug and `--dry-run` JSON.
- **Size:** M. **Conflicts:** **start after `bob-cli-h4` lands.** h4.1 is changing what
  the capture preview emits (landing blocks).

### #10 — Keep bob-mac-capture master green: `bob-cli-1x`, plus a new bead for today's Go To failures

- **Why.** Mac CI went red again within hours of being restored. Three of today's Go To
  tales (`fde8211`, `70c0839`, `5960b31`) landed without a lander. Two Go To test
  classes now fail, and the Test step hits the 15-minute hang guard. `1x` already has
  four +1s for exactly this pattern: pushes to bob-mac-capture without watching macOS
  CI, which Linux hosts cannot run. A packaged gate now exists for it
  (`scripts/dev/macos-ci-check`, from the 2026-10-27 +1).
- **Recommended solution.**
  - Fix the Go To tests. The panel test expects the bare error string, but the code now
    prefixes "bob command failed (exit 7)…". The delayed-refetch test times out, and
    the backslash insert helper leaves `\` in the draft. Find the hang with the uploaded
    xctest samples.
  - Then land `1x` through `/sase_memory_write`. A short rule in `sase.md` / the agent
    instructions should say: any push to bob-mac-capture from a Linux host must run
    `scripts/dev/macos-ci-check`, or watch the exact-SHA macOS run, before declaring
    done.
- **Size:** S–M. **Conflicts:** h4.4–h4.6, h2.6, and the 185 chain all push Mac code
  today. Coordinate by letting their landers see the red first, and take only the Go To
  tests, which none of them own.

### Runners-up (next in line)

- **`bob-cli-9x` — cross-host alert when vault-sync halts (L).** The new halt breaker
  stops safely, but a halt on headless athena or apollo is invisible. This is valuable
  data-safety work and conflict-free. It falls just outside the top 10 because no
  unnoticed halt has been observed yet.
- **`bob-cli-8r` — athena hostile-CPU / `/tmp` exec / mining-egress alerts (L).** A real
  miner ran at load around 70 for about five hours on 2026-10-17. This is security
  hardening and lives in the tailnet repo, not bob code.
- **`bob-cli-e1` + `bob-cli-g2` — Markdown link titles leaking into minted IDs and
  breaking Ctrl+L Keep badges (L each).** These need coordinated SB vectors across
  engines, so they are better run as one planned change than as two tasks.
- **`bob-cli-6g` — ordinary `@route` capture ignores `project_name_aliases` and creates a
  stray note (L).** Wait until the capture epics land.
- **`bob-cli-gc` — capture `!` close takes about 95–220 ms against a 70 ms budget (L).**
  Wait until h2 lands.

## 4. Do Not Work These; Close Or Re-Scope Them

| Bead(s) | Recommendation | Evidence |
| --- | --- | --- |
| `f3`, `fu`, `dz`, `eo`, `fj`, `fp` | **Close as done** | bob-mac-capture `933091b` / `2884ea2`; master run 41888215951 passed every step |
| `dx` | **Close** | `test-ledger-tools-lane-walk.cjs` passes 10/10 on bob-plugins `b9f47f3` |
| `fh` | **Close** | its own note says it no longer reproduces; today's macOS clippy errors are in h2-owned files |
| `et` | **Narrow** | to the freshness-namespace half; the gcal-events half passes 25/25 |
| `8a` | **Narrow** | long flags are now refused, short flags are not; re-check after h0 lands (h0 added `-m`) |
| `ge` | **Re-scope** | after `933091b`, only the 65 grammar-3/4 fixture JSONs remain to audit |
| `b6`, `fo`, `de` | **Keep, but fix structurally (#8)** | each was "fixed" once and recurred today |
| `e0`, `ei` | **Route to the sase project** | these are SASE finalizer/handoff commit-loss bugs; `sase-1ph` only recovered losses, and none of the running sase epics covers prevention |
| `h1` | **Wait for h2, then align** | h2's plan adds the A7 midnight refusal for `x=`; apply the same rule to `=-N` starts in `compute_pomodoro_start_range` |
| `gk` | **Wait for h0/h2/h4** | the capture-parse editor is under active change |

## 5. Needs Bryan's Hands, Not An Agent

- **A batch for one Mac Terminal session:**
  - `30`: reconcile the crontab and install it locally, since `crontab -` over ssh is
    denied.
  - `5g`: add `bob ref jobs run -q` to the same crontab.
  - `ay`: run `scripts/dev/highlights_coordination_acceptance`, then flip the default.
  - `cx`: link-copy acceptance.
  - `20`: a UX copy pass.
- **Owner decisions that block design:** `1q` (vault PDF tracking policy), `72` (ADJ-8
  date propagation), `4a`/`4b` (JSON option and noun policy), `b0` (status in the PDF
  marker), `g4` (see #5), and `gu` (see #3).
- **Time-gated (snoozed or waiting on the train):**
  - `aa`: Zensical 0.1.x, wakes 11-06.
  - `cp`: Day strip reassessment, wakes 11-16.
  - `e3`: theme replay, wakes 11-12.
  - `6q`: Daily Stats revisit, past its wake date.
  - `ah`: crates.io publish.
  - `g3`: needs the first release after `8a9ec685`.
  - `ec`: probably actionable now, since the master-built `bob` on apollo already
    serves `bob types list`.

## 6. The Memory Backlog

About 25 of the 35 memory beads are "record decision X" follow-ups that epics skipped
under an auto-decision of `decision_record = no` (`4d`, `4t`, `51`, `5d`, `5u`, `6d`,
`7t`, `82`, `8c`, `8d`, `8h`, `8m`, `8p`, `90`, `9e`, `9l`, `9t`, `a3`, `br`, `bs`,
`ed`, `eu`, `f0`, and others). Each is cheap, but each needs Bryan's acceptance under
`/sase_memory_write`. None ranks individually against the items above. I recommend one
batched session in which Bryan reviews the proposed records together. The mechanical
glossary fixes `ar`, `ga`, `fq`, `2x`, `4o`, `7a`, and `bu` can ride along. The
exception is `1x`, which is folded into #10.

## 7. Method And Limits

- **Beads.** I listed every task bead with `sase bead list -t task -f json`. For the 82
  beads whose details live in typed fields, I used `sase bead read … -f json`. Each bead
  was assessed on +1 evidence, notes, links, and size.
- **Agents.** I ran `sase agent list -j` locally and over `ssh athena`, then read
  `raw_prompt.md` for the non-bead plan chains (athena `180`–`188`). Epic scope came from
  `sase bead read` on h0, h2, and h4 and from their plan files.
- **Re-checks.** I ran bob-plugins `node --test` on master `b9f47f3`, under both UTC and
  America/New_York. I took GitHub Actions job and step results for bob-cli and
  bob-mac-capture from `gh run list` / `gh run view`, ran `bob plugins list`, and grepped
  bob-cli source at `87eecb1a`.
- **Not done.** I did not run `cargo test` or `just check`: apollo's load average was
  about 26 on 16 cores, and the workspace had no build cache. bob-cli test status
  therefore comes from CI run 41900846465, not a local run. `f8` (CPU budgets) is
  athena-specific and passed on apollo. I did not file beads for the two untracked
  breakages (`overwrite_local`, Mac Go To CI), to avoid duplicates from five parallel
  researchers. I recommend the lead or the next worker file them through
  `/sase_new_task`.
