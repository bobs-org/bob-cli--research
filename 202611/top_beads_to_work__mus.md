# Top task beads to work next (researcher mus)

Date: 2026-11-04. Scope: bob-cli ready task beads (169 ready, 21 in progress, 0 open
tasks at read time). Method: `sase bead stats`, full `sase bead list --status ready`,
`sase bead blocked`, `sase bead list --status in_progress`, audited
`sase bead read` on ~20 high-signal candidates, `sase agent list -j` locally, and
`ssh athena sase agent list` for the other machine. Bead memory rules consulted via
`sase memory read sase_beads.md` and `tailnet.md`.

## Running-agent conflicts (checked before ranking)

Local (this machine): the 5-researcher swarm itself (research.3a/3b × cdx/cld/grk/mus/
gem, RUNNING), `bob-cli-h2.4` (RUNNING), `bob-cli-h0.8` (QUEUED), `bob-cli-h2.land`,
`bob-cli-h2.5`, `bob-cli-h2.6`, `bob-cli-h0.land` (WAITING), `cd--code` (RUNNING).

Athena: `185--3` (RUNNING, codex session 185, snippet unavailable — scope unknown),
`bob-cli-h4.1`, `bob-cli-h4.2`, `bob-cli-h4.3` (all RUNNING), `bob-cli-h4.4/4.5/4.6` and
`bob-cli-h4.land` (WAITING), plus sase-project agents unrelated to bob-cli.

Active epics and what they own (do NOT pick fights inside these areas):

- **bob-cli-h4 Transfer previews** (athena, 3 phases RUNNING): bob-side landing blocks
  for transfers, merge/move record enrichment and copy, Mac transfer/landing/pending/
  refusal cards. Its blocked chain (h4.4 blocked by h4.2; h4.5 by h4.1+h4.4; h4.6 by
  h4.3+h4.5) means the whole transfer surface is live construction.
- **bob-cli-h2 Record past Pomodoros with x=** (local, h2.4 RUNNING): whole-stack
  overlap guard, `!` edge repair, x= docs/help, Mac Record-past-work card. The entire
  `x=` capture grammar and pomodoro-record path is owned.
- **bob-cli-h0 Move choice (`- ^^`)** (local, h0.8 QUEUED): move-card submit flow,
  chaining, refusals, preview hints. The move-consequence path is owned.
- **Session 185 on athena** (RUNNING, scope unreadable from here): treat any bead in
  an area it might touch with extra care; I could not determine its epic.

Consequences applied to the ranking: no bead whose fix lands primarily in the
capture-move/transfer grammar, the x= record path, or the Mac transfer/move cards is
recommended below, even where the bead is otherwise attractive (e.g. bob-cli-8a
capture swallows unknown flags, bob-cli-7j successor-offer destination grammar,
bob-cli-fi third bullet level, bob-cli-gk multi-note-marker refusals, bob-cli-g4's
`bob capture x` half — see #6 for why g4 still makes the list). Blocked bob-cli-fg
(blocked by bob-cli-f3) is excluded: fix f3 instead. bob-cli-fp is excluded: its note
records that bob-mac-capture 2884ea2 already fixed the two Build errors (ViewBuilder
loop, keep-moving type-check) with a green Build on run 41435470545 — it needs a
verify-and-close, not work.

## Ranked list: the 10 beads to work

### 1. bob-cli-f3 — 7 pre-existing Mac XCTests fail on master (CI, large, +4)
Master macOS CI has no green Test step, so Bundle / plist-verify / Launch smoke /
Install steps never run: every Mac change ships unverified. Seven deterministic
assertion failures (line-case undo selection, three `+` separator-toggle tests, two
task-type hosted tests, task-type retype), identical across three SHAs, four
independent corroborations. Recommended solution: fix each root cause separately in
bob-mac-capture (`+` toggle undo/footer logic, line-case undo selection restore,
task-type retype strings, t:-menu hosting/visibility) — do not weaken assertions or
delete tests. Unblocks #2's siblings and bob-cli-fg.

### 2. bob-cli-fu — 14 more hosted Mac XCTests fail on master (CI, large, +2)
The other half of the same red Test step: 11 ClipPreview hosted tests plus 2
command-accept-submit tests plus the keep-moving opaque-key order test, unmasked once
2884ea2 restored the Build. Recommended solution: rerun once to confirm (single-run
evidence so far), then bisect the red-Build window rather than assuming one culprit;
fix product where the test reflects the accepted contract (clip polling/retention,
submit-on-accept, pull-in offer order) and cite the contract change where the test is
stale. Together #1+#2 restore the entire Mac gate.

### 3. bob-cli-fj — Mac CI Build opaque-return error in eventWarningBanner (CI, small, +1)
The third Build error from the same CI runs (missing `return` after inline-Markdown
setup, CapturePanelView.swift:4688). Small, mechanical, and Build must be green before
any Test signal exists. Recommended solution: add the explicit return / restructure
the opaque-return path the way 2884ea2 did for the sibling errors, verify with a
precommit `Scripts/macos-ci-check` snapshot. Pair with verifying-and-closing fp.

### 4. bob-cli-eh — ledger-tools startup tests fail since 1295e52 (CI, small, +24)
The highest-corroborated bead in the store (+24): note-ready and relation-index
harnesses break because test fakes keep one `onLayoutReady` slot that
`setupGcalEvents` overwrites — cause already localized to the second registration
introduced by bob-cli-ea.8 commit 1295e52. Recommended solution: update the affected
harnesses to register/expect both slots (or scope the fake per harness), rerun the
full ledger-tools suite. Small fix, enormous unblock for every ledger-tools change.

### 5. bob-cli-et — ledger-tools date-bomb tests fail since 2026-10-31 (CI, small, +17)
gcal-events and freshness-namespace tests read the real date and fail on every run
since the calendar passed 2026-10-30 (+17 corroborations). Recommended solution: pin
the clock in those tests (fake timers / injected date, matching whatever convention
the repo's other date-sensitive tests use) so they pass on any date. Genuinely small;
do it in the same session as #4 while the ledger harness is open.

### 6. bob-cli-dq — capture status rewrites trip PomodoroBlockTracker guard (bug, medium)
Any status-changing capture of a task inside today's `## Pomodoros` section panics
debug builds (`pomodoro entry vanished without a ref`) and silently drops
`pomodoro_blocks` in release — data loss on a routine gesture (reproduced on master
03493169). Recommended solution: teach `PomodoroBlockTracker` to follow the rewritten
entry by ref across status rewrites instead of treating it as vanished (keep the
debug assert as the invariant once the tracker follows correctly). Conflict note: this
touches the capture/pomodoro path next to live h2/h4 work — coordinate with those
owners (read-only check of h2.4/h4.2 scope first), but severity (crash + silent data
loss) means sequence it, not shelve it.

### 7. bob-cli-gt — periods brief credits every linked task the whole Pomodoro (bug, medium)
Every linked task row shows the full session while root rows split it, so tasks
outrank their own roots in every week checked (e.g. W41 root 1h33m vs its own task
1h40m) — the numbers in the new weekly-Review pipeline are visibly nonsensical, with
corroboration from most bob-cli-gr phase agents. Recommended solution: divide session
minutes across linked rows (or attribute only the root split) in
`src/native/periods/brief.rs linked_minutes / week_time` so task rows sum to ≤ their
root, and add a regression test with the W41 shape.

### 8. bob-cli-gs — periods brief ignores done/ archive paths (bug, medium)
Archived tasks lose linked minutes and print dead source-note links (W27–W43 all
affected) — the same broken Reviews pipeline as #7, from the other direction: real
work vanishes. Recommended solution: resolve `done/` archive paths when computing
`linked_minutes`/`linked_for`/`task_link` in `brief.rs`, with a fixture covering an
archived completion. Do #7+#8 as one brief-correctness pass.

### 9. bob-cli-gu — periods brief Still-open section uses today's vault for closed periods (bug, large)
Past-period briefs report today's blocked/kept/zero-minute state as though it
described the period (corroborated by every W39–W27 phase). For a review-drafting tool
this is a correctness defect, not polish: it writes false history. Recommended
solution: snapshot (or recompute from period-dated inputs) the still-open inputs in
`still_open_section` instead of reading live lane state. Larger, but completes the
brief-correctness pass with #7+#8.

### 10. bob-cli-e0 — plan-propose handoff loses the lander's dirty edits (bug, large)
Five consecutive backlog-batch landers lost their plan `status: done` edits (and any
same-turn landing fixes) because `sase plan propose` as a final action submits no
final declaration — the tooling silently discards landing work on a repeated,
predictable path. Recommended solution: make the propose handoff commit (or carry
forward) the proposer's dirty plan-sidecar edits before submitting — or refuse to
propose dirty — so successor-rule landers cannot lose state. Infra-level blast radius
across every future landing; pairs with bob-cli-ei (stranded multi-repo landing
commits) as follow-up.

## Deliberately excluded / next-up

- Next-up: bob-cli-fy (plugins-sync dirty-deploy refusals — daily friction across
  epics), bob-cli-ei (stranded landing commits), bob-cli-fo (docs-check red, blocks
  the docs gate, small — good quick win), bob-cli-f8 (athena perf budgets, +6),
  bob-cli-8r (athena hostile-CPU alert — real security gap, but feature-sized and
  lower leverage than green CI), bob-cli-9x (vault-sync-halt alert, same reasoning),
  bob-cli-gw/gx (rest of the periods-brief cluster once #7–#9 land).
- Do not work now: anything owned by h0/h2/h4 (capture/move/transfer grammar and
  cards), blocked bob-cli-fg (fix f3 first), already-fixed bob-cli-fp
  (verify-and-close), and the ~60 decision/glossary record beads (valuable but
  documentation, strictly lower leverage than red CI and wrong numbers).
