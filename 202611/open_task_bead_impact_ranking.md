# Open Task Beads: The 5 Most Impactful To Work Right Now

**Date:** 2026-11-11 · **Project:** bob-cli · **Author:** Claude (SASE research turn)

## Scope and method

`sase bead list` (statuses open/ready/snoozed/in_progress/claimed, type task) returned
**218 open task beads**; `sase bead ready` reports **210 with no active blockers**.
Excluded from consideration: the 7 snoozed revisit beads (bob-cli-6q, -aa, -ah, -cp,
-e3, -i8, -jd — each is time-gated by design), the one dependency-blocked bead
(bob-cli-hh), and bob-cli-hp (see "Free win" below — it is already fixed on master and
only needs verification and close).

Fourteen candidates were read in full (audited `sase bead read`): bob-cli-h7, -h9, -jx,
-f8, -hp, -jr, -jz, -jy, -k8, -jh, -dq, -gy, -9x, -e0. Candidates were selected by
corroboration count (+N), task type (CI failures and bugs first), recency of evidence,
and title severity. Ranking criteria, in order of weight:

1. **Gate blockage** — does the defect keep a CI or verification gate red that other
   work depends on?
2. **Breadth and frequency** — how many agents/landings keep paying for it (the +N
   corroboration count is a direct proxy: every +1 is an independent reproduction and a
   triage session someone already paid for)?
3. **User-facing or data damage** — crashes Bryan hits, or silent vault corruption that
   accrues.
4. **Impact per unit effort** — declared size, and whether the bead already contains a
   verified root cause and fix sketch.
5. **Freshness** — is the failure confirmed on current master, or possibly stale?

Prior work: the 2026-11-04 two-host audit
(`research:202611/task_bead_top10_with_two_host_agent_audit`) ranked gy, h7, and the
then-current CI reds highly. The landscape has shifted materially since: gy's vault-side
mitigation is verified (its note #1), h7's four named root causes are three-quarters
resolved (its note #2) with the macOS failure cluster now owned by newer beads, and hp
was fixed in passing by a Gmail epic. This report reflects the post-shift state,
re-verified against evidence recorded as recently as today (2026-11-11).

## Landscape summary

The open-bead population splits roughly into: ~60 feature beads (✦), ~45
memory/decision-recording beads (▤), ~35 bugs (⨯), ~20 CI failures (⚙), ~20 flaky tests
(≈), and the remainder decisions/process items. The dominant *cost center* right now is
not any single feature gap — it is three red verification gates (macOS CI, bob-cli
`just docs-check`, bob-plugins full `npm test`) that every epic landing keeps
re-triaging. The corroboration counts make the recurring tax visible: h9 has collected
**14** independent reproductions in 7 days, f8 has **12**, h7 has **12**. Each of those
is a landing agent that had to stop, diagnose a pre-existing failure, search for the
owning bead, and record evidence before it could close its own work.

A note on CI-vs-release exposure: bob-cli's release train gates on
`.github/workflows/ci.yml`, which deliberately excludes docs-check ("the deploy repo's
publish pipeline already gates the docs"), so the docs failures below do not stop the
daily release train — their cost is agent churn and gated docs publishing. The
bob-mac-capture failures, by contrast, block that repo's *only* verification gate.

---

## Ranked top 5

### 1. bob-cli-jx — Mac tip-anchoring tests fail on every macOS CI run (⚙ ci, L, +2)

**Three `CaptureAliasTipPanelTests` time out on every bob-mac-capture macOS CI run
since aafed83, keeping master's Test step red.**

This is the single most leveraged bead in the store. GitHub Actions is the **only**
gate for the macOS-only targets (Linux hosts cannot run these tests at all), and a red
Test step skips Bundle, Launch smoke, and Install/reinstall on every run — so **every
Mac change currently ships unverified**, and the green exact-SHA gate that every
bob-mac-capture push is required to watch (`scripts/dev/macos-ci-check`,
`/sase_monitor`) can never pass. The failure is deterministic: the same three tests
(`testFilteringKeepsTheShownTipAnchoredToTheSigil`, `testOptionTypedHashOpensTheHashTip`,
`testTypingQueryBeforeTheRouteListOpensKeepsTheTip`) fail with identical `waitUntil`
timeouts on at least ten runs across unrelated SHAs, re-corroborated today. Fixing it
likely also resolves or explains the sibling intermittents in the same suite
(bob-cli-jk, and the two flaky tests named in jx's own description), and it narrows
h7's one remaining open item (the intermittent 15-minute watchdog hang) by removing
noise. Until this lands, every macOS landing triage (a dozen in the evidence trail over
the past week) pays again.

*Why not h7 instead?* h7 (+12) is the older tracker, but its note #2 and jx's evidence
show the h7 12-test baseline cluster has since gone green on master (run 42906549245:
"4695 tests with 7 failures, all in this suite" — the alias-tip suite). The live
blocker is jx; h7's remainder (the watchdog hang) is real but intermittent and
undiagnosable until the deterministic reds are gone.

**Companion:** bob-cli-jy (⚙ ci, S) — `just typecheck-tests` fails on clean
bob-mac-capture master (two `@MainActor` test classes mutate state from nonisolated
`tearDown`). Same repo, same cause-area (closed epic j9), small and fully diagnosed.
Doing it alongside jx restores both the local pre-push type gate and the remote CI
gate in one effort.

### 2. bob-cli-h9 — mounted protocol.md over the 6000-word docs budget (⚙ ci, S, +14), with sibling bob-cli-jz (⚙ ci, M, +4)

**bob-cli `just docs-check` is red on clean master because
`docs/reference/mac-capture/protocol.md` (6149 words, cap 6000) is over budget; jz
tracks four more pages (mac-capture capture-panel 6036, capture-previews 6177, keyboard
6060; plugins bob-navigation-hotkeys 6186).**

h9 carries the highest corroboration count in the entire bead store: **14 independent
+1s in seven days**, including one recorded *today* on clean bob-cli 7eb82440 (the
current master HEAD). That number is the impact: every landing agent in every epic runs
`just docs-check`, sees a red lint, and must prove the failure is pre-existing before
closing — a tax now paid well over a dozen times and growing daily. The page has
hovered within ~15 words of the cap for weeks and has been pushed over repeatedly
(6003 → 6048 → 6149 → 6217 → 6149), so without a real trim *any* protocol addition
re-trips it. The work is bounded and small-to-medium: trim or split five source pages
(four in bob-mac-capture, one in bob-plugins) without dropping contract facts, then run
docs-check in each repo with siblings mounted. One coordinated pass clears the entire
failure class, un-reds the local gate for every future landing, and unblocks the docs
publish pipeline that gates on these checks. h9 and jz are deliberately linked sibling
beads ("tracked separately") — work them as one unit.

### 3. bob-cli-f8 — task-wikilink snapshot/ranking CPU budgets fail repeatedly on athena (⚙ ci, L, +12)

**Two CPU-timed performance gates in bob-plugins
(`test-block-id-prompt-task-wikilink-index-performance.cjs`) fail repeatedly — warm
snapshot/order ~75-128 ms against 50 ms, keystroke rank ~12-23 ms against 12 ms —
blocking a clean full `npm test` on athena.**

Twelve +1s over ten days, from virtually every bob-plugins epic landing in that window,
plus a fresh control on 2026-11-09 (59/62 pass, same two nodes red). The failures
reproduce **in isolation**, not just under suite load, and have also appeared on apollo
— so this is a genuine performance (or measurement) regression in the block-id-prompt
wikilink index, not a load flake to wave off. The bead is explicit and right that the
answer is not "raise the budgets": these gates exist to catch real typing-latency
regressions in Obsidian capture, a surface Bryan feels directly. Until it is
root-caused, every bob-plugins verification is muddied (agents cannot distinguish "the
known f8 miss" from a fresh regression they caused — exactly the ambiguity that already
generated a dozen triage sessions), and a real slowdown may be hiding under the
noise. Large size is honest — it needs investigation, reproducible host measurements,
and a defensible budget or production fix — but it is the most-paid-for unresolved
question in the plugins repo.

### 4. bob-cli-jr — `bob stats show worked` panics "RefCell already borrowed" (⨯ bug, S)

**Any single-metric `bob stats show` request whose range includes today crashes with
exit 101 (`homes.rs:412`), on the live vault at current HEAD.**

This is the highest-value *small* bug: a user-facing crash on the primary stats
surface, with the root cause already read out of the code to the line (a
`RefCell` double-borrow: `HomesEngine::finish` holds `resolver.borrow_mut()` while
`remember → ensure_root` borrows it again for a not-yet-seen `root_parent`), a concrete
two-option fix sketch, and a regression-test recipe sitting in the bead. Impact is
sharper than it first looks: any client that asks for `worked` alone over a range
touching today — scripts, the period/day-strip tooling direction the open jv/jw/cp
beads are building toward, or ad-hoc queries — gets *no data at all*. The crash is
range- and metric-dependent, which makes it a reliability landmine: it works in a demo,
then fails on the range that matters. Small size, fully diagnosed, zero design risk —
this is an afternoon fix that removes a live-vault panic.

### 5. bob-cli-k8 — `created:` stamps label New York wall time as +0000 on UTC-clock hosts (⨯ bug, S, +1)

**Every notebook, project note, and ref created from apollo (or any UTC-clock host)
gets a `created:` instant that is wrong by the Eastern offset — silent, accumulating
vault data corruption.**

`format_created_timestamp` resolves the configured-timezone wall clock (America/New_York
since bob-cli-2q) but labels it with `chrono::Local`'s offset, so on apollo a note
created at 08:01 New York time is stamped `08:01:12+0000` — five hours early (four in
EDT). Reproduced independently today via both `bob notebooks create` and the capture
path. Unlike every other bug in the backlog, this one *compounds*: each day it stays
open, more notes get permanently wrong instants, and anything that reads `created:` as
an instant (Dataview, sorting, recency) silently shifts; notes created after 19:00
local land on the previous UTC day. The fix is small and already shaped — pass
`env::configured_timezone()` into the shared helper, exactly as `records/plan.rs`
already does (including the DST-gap fallback) — plus a `TZ=Etc/UTC` regression test.
Fixing it now caps the backfill cost; waiting grows it. The bead also flags a checkable
side-question (RFC 3339 `BOB_NOW` with explicit offset is ignored) to settle while in
the file.

---

## Free win (not ranked)

**bob-cli-hp** (⚙ ci, S, +7) — the duplicate `bob clipboard` registration that failed
two lib tests — **no longer reproduces**. Gmail compose commit 2a37f8ce removed both
duplicate registrations; two independent landings (notes #2 and #3) confirmed
`just check` green end to end, and note #3 says "Ready for the owner to close." Verify
once on current master and close it; it costs minutes and retires a +7 bead that
agents otherwise keep checking.

## Near-misses and why they ranked below

- **bob-cli-jy** (⚙ S) — folded into #1 as a companion; same repo and neighborhood,
  small, deterministic.
- **bob-cli-dq** (⨯ M) and **bob-cli-ht** (⨯ L) — the `PomodoroBlockTracker` guard
  family: debug-build panics, and release builds silently drop the `pomodoro_blocks`
  preview (Mac previews lose the Pomodoro block). Real, reproduced, shared root cause
  noted across the two beads — a strong #6 candidate, outranked only because writes
  remain correct and the top-5 gates/crashes bite harder.
- **bob-cli-jh** (⨯ S) — capture dependency promotion can rewrite a *closed* (even
  archived `done/`) prerequisite to `[*]`/`[/]` in place, against the documented
  contract. Silent vault corruption with a precise code-path diagnosis, but the trigger
  (an explicit `&` dependency on a closed prerequisite from a Next/In-Progress
  dependent) is uncommon and it has not yet been reproduced end to end.
- **bob-cli-9x** (✦ L, +1) — cross-host alerting when vault-sync halts. The strongest
  *feature* candidate: a halt on headless athena/apollo is currently invisible, and the
  delivery route is now proven end to end (Prometheus → Alertmanager → Postfix/Mailjet
  → Gmail, confirmed 2026-11-05 with model rules to copy). Ranked out only because the
  halt breaker itself is already safe (no data loss while halted) and the top 5 are
  active, daily-cost defects.
- **bob-cli-e0 / -ei / -gy** — the SASE handoff/stranding class (plan-propose turns
  losing uncommitted edits; plan archives leaking into the vault). Severe class with an
  impressive loss inventory, but recovery paths exist and have been exercised, gy's
  vault-side mitigation is verified, and the prevention fix lives in the sase project's
  codebase, which a bob-cli task-bead launch is poorly placed to land.
- **bob-cli-h7** (⚙ L, +12) — see #1: keep open as the watchdog-hang tracker, but the
  deterministic work moved to jx.
- The **flake family** (ej +6, fz +6, f2/g8/gd/io/hf/hr/ju, hu/hv/jb/jk/jm) — each is
  real churn, but each is a narrower slice of the same "verification noise" problem
  that #1-#3 attack at the trunk. fz (headless Chromium hangs on apollo, +6) is the
  best of these if a #6 is wanted.

## Suggested order of attack

1. jx (+jy in the same session) — restores the Mac ship gate end to end.
2. h9 (+jz in the same session) — one docs trim pass, retires the loudest recurring tax.
3. jr, then k8 — two small, fully diagnosed fixes; k8's cost grows with delay.
4. f8 — schedule as a real investigation (it is large; resist budget-bumping).
5. Close hp on sight.

Each is `ready` with no blockers; launching any of them is `sase bead work <id>` from
the owner's TaskTriage gate.
