# Morning GTD + Pomodoro Changes Review (2026-09-30 → 2026-10-01)

Researcher: mus. Vault + repo evidence read 2026-10-01 (~08:00 EDT assumed for
`bob plan`; `BOB_NOW=2026-10-01T08:00-04:00`).
Scope: what changed in Bryan's morning GTD and pomodoro practice, what is wrong
with it, and a ranked list of recommended improvements. The author notes he has
not done morning GTD for roughly a month, so counts and freshness data are
biased (many tasks still need to be marked complete/cancelled).

## Sources inspected (not exhaustive)

- `~/bob/gtd_daily.md`, `~/bob/bob_gtd.md`, `~/bob/gtd.md`,
  `~/bob/freshness.md`, `~/bob/dash.md`
- `~/bob/2026/20260929.md`, `~/bob/2026/20260930.md`, `~/bob/2026/20261001.md`
- `~/bob/bob.md` (`^auto-decay-priorities`, `^submitted-status`)
- `bob plan -f json` for 2026-10-01; `docs/plan.md` ("Today", "Lanes");
  SASE decisions `task-lanes-are-sticky`, `today-is-read-from-the-ledger`;
  glossary `pomodoro`, `task-link`, `work-log`

## What changed

### 1. Morning routine rewritten (in `gtd_daily.md`, 2026-09-30)

Two old tasks cancelled 2026-09-30:

- "Pick today: ≤3 themes from yesterday + NOW (highlight first)"
  (created 09-29, cancelled 09-30)
- "Weekly review: re-tag NOW to ≤15, promote from READY, defer with P-levels,
  check hours and created vs closed" (weekly Monday, cancelled 09-30)

Two new tasks created 2026-09-30:

- "Morning review (≈10 min): REVIEW until 0 new (]s, Alt+Shift+F), then clear
  what's due; PENDING → NEXT; link today's work, release the rest with Alt+N;
  ≤3 themes, highlight first" (daily when-done, scheduled 09-30)
- "Weekly prune: release NEXT to ≤15 and PENDING to ≤10 with Alt+N, promote
  from READY, defer with P-levels, check hours and created vs closed; clear
  leftover REVIEW or lengthen that note's task_refresh; look for projects with
  no Next or Ready task" (weekly Monday when-done, scheduled 10-05)

So the vocabulary moved NOW → TODAY/PENDING/NEXT/READY/REVIEW/PLAN, re-tagging
became Alt+N releasing, and freshness review (`freshness.md`: walk `]s` /
Alt+Shift+F until 0 new, one key per outcome) became the gated first step.

### 2. Today redefined as ledger-derived (repo + vault, Sep 30–Oct 1)

Per `today-is-read-from-the-ledger` and `docs/plan.md`: Today = open tasks with
a dedicated Task Link (exact single block link as a direct child bullet) under
today's **open** Pomodoros, computed at read time. `#now` grammar, pickers,
rows, and docs removed (`bob-cli-2y.6`); dash TODAY/PENDING/NEXT/READY sections
made exclusive; `bob plan` reports budget + lanes. The old file-path filter
("tasks living in the daily note") and any tag-based Today are gone.

### 3. Lanes made sticky; only release demotes (same epic)

Per `task-lanes-are-sticky`: linking under today's open Pomodoros raises Ready
(or Blocked) to Next; `=x` sets In Progress (Pending); **removing a link never
demotes** — only Alt+N release (or the lane-row control) returns Next/Pending
to Ready. Blocked stays derived and overrides. Canonical-daily-note tasks
(`^gtd`) keep a derived-clearing carve-out (R9).

### 4. Pomodoro planning style changed (visible in daily notes)

- 09-29: ledger mixes 8 closed timed pomodoros with ~15 open `()` placeholder
  entries used as a standing inventory/queue (BOB, GOALS, SASE, DECKS, …).
- 09-30: 12 closed timed pomodoros (≈435 min), no placeholders left open.
- 10-01 (today, pre-work): 4 open `()` placeholders, no timespans yet —
  GTD (links `[[#^gtd]]`), BOB (2 links), READ (1 link), MEMORY (1 link).

That is: from inventory-style placeholder backlog to a lean pre-declared
themed plan. `bob plan` for today: themes 3/3 (BOB/READ/MEMORY; GTD exempt),
links 4/10, Today count 5, highlight BOB. Disciplined on paper — but themes
are already exactly at cap before a single minute is logged.

### 5. Supporting apparatus landed with it

- `=x` close writes typed Work Log entries (`🛠️ **WORK LOG**` newest-first);
  `=x1,2!4`-style syntax work continues (`bob.md`).
- `[fresh::]` stamps on rewritten tasks; `freshness.md` review queue with
  rank/tier sorting.
- Proposed Submitted/Waiting status cancelled ("WIP status should fill this
  role"); `bob_gtd.md` project "Improve GTD morning review process!" tracks
  diagnostics (thresholds `>=5 ready`, `>=R total ready`, `>=S scheduled` —
  R and S undefined) and a keymap for jumping through stale items (done).
- Old daily `^gtd` lines on 09-29/09-30 were cancelled (`[-]`), not completed;
  today's `^gtd` is a fresh `[*]` (created 10-01).

## What is wrong

Findings are ordered by importance; the bias note applies throughout: every
count below reflects a month of no morning GTD, i.e. absence, not workload.

1. **The lanes are already blown out, and the new routine cannot absorb that.**
   `bob plan` reports NEXT 28/15 and PENDING 50/10 — 13 + 40 = ~53 releases
   needed to reach cap. Sticky lanes plus a month of no releases is the cause;
   the decision record itself predicts 2–3 tasks/day of lane growth at
   September rates with no automatic forgetting. A "≈10 min" morning review
   cannot also be a 53-release triage session, and the weekly prune faces 40
   Pending releases in one sitting. Until a catch-up pass happens, every
   cap, chip, and "release the rest" instruction is fiction.
2. **"REVIEW until 0 new" is an unbounded gate on a stale vault.** With a
   month of un-reviewed tasks, the freshness-new backlog is large; gating the
   whole morning behind draining it to zero makes the routine's duration
   unbounded on exactly the mornings when time matters most. The weekly task
   already contains the escape hatch ("clear leftover REVIEW or lengthen that
   note's task_refresh") — the daily gate needs the same kind of bound.
3. **The morning-review line packs ~6 operations into one sentence with no
   order.** REVIEW → clear due → PENDING→NEXT → link → release rest → themes →
   highlight. There is no step order (release must come *before* linking, or
   just-linked work gets released), no checkboxes, and the easiest step to
   skip under time pressure is the release — which is precisely the step the
   sticky-lane system depends on. Old routine had the same density problem
   ("re-tag… promote… defer… check hours and created vs closed"), so this is
   inherited, not new — but the new system punishes skipped releases
   permanently (lanes never decay).
4. **Pre-linking at plan time inflates the very lanes you must then prune.**
   Linking promotes Ready→Next and nothing but Alt+N reverses it. Today's
   ledger pre-links 4 tasks (one self-link: the GTD entry links `[[#^gtd]]`,
   i.e. the review task links itself into Today). Every planned-but-unworked
   link is a Next/Pending task that now requires an explicit release. The
   09-29 inventory style was worse, but "link today's work" at plan time,
   before starting, still commits lanes speculatively.
5. **No catch-up step exists in the routine despite the known backlog.** The
   author knows "a lot of tasks I need to go back and mark as complete";
   neither the daily nor the weekly task says so. The freshness queue and lane
   caps will mislead (everything looks over-budget) until a one-time triage
   pass (complete/cancel the month's done work, bulk-release to caps) is done
   — and the routine should name it so it actually happens.
6. **Stale scheduled/repeat hygiene sits outside the routine.** The daily
   habits (weather, teeth, fish oil, calendar, email, Keep import) still carry
   `scheduled:: 2026-09-29` and sit open; the morning review itself is
   `scheduled:: 2026-09-30`, i.e. already a day overdue on the morning it
   should run. `repeat:: every day when done` means no pile-up, but each
   stale item must be individually completed to roll forward — slow, and
   nothing in the routine addresses it.
7. **Themes are at cap (3/3) with zero minutes logged.** BOB/READ/MEMORY
   exactly fills the budget; any emergent work has nowhere to go except over
   cap or via mid-day re-plan. Planning to the cap the night before (or by
   template) leaves no slack. Highlight (= first non-exempt entry, BOB) is
   correct by construction today, but only because entry order happened to
   match priority — the routine says "highlight first" without saying how to
   choose what is first.
8. **Diagnostics and thresholds are undefined.** `bob_gtd.md^diagnostics`
   wants alerts at "≥5 ready per project/area, total ready ≥R, total scheduled
   ≥S" with R and S never defined; the weekly prune's "look for projects with
   no Next or Ready task" is the orphan check the diagnostics should feed, but
   the two are not connected. As written this is a wish, not a control.
9. **Minor semantic traps for a tired morning brain.** "PENDING → NEXT" in
   the daily line reads as a promotion direction, but the lane model has no
   such promotion (Pending and Next are both sticky; the pull order
   Pending→Next→Ready is about *working* order, and the weekly prune only
   releases downward). "Clear what's due" vs "REVIEW until 0 new" (due vs new
   are different freshness tiers) is easy to conflate at 7am. The `[?]`
   morning-stretches task scheduled 10-04 is invisible to the dash until then
   (scheduled-after-today is filtered) — fine, but it means the routine's own
   list is not what the dash shows, inviting "I thought I did everything"
   misses.
10. **What is actually good and should be kept.** Ledger-derived Today removes
    a whole class of staleness (no tag to forget); the exclusive dash sections
    plus `bob plan` give one authoritative count; the freshness one-key table
    is a genuine speedup over re-tagging; cancelling Submitted rather than
    adding a status was right; the GTD exemption keeps the review itself out
    of the theme budget. The critique above is about calibration and
    catch-up, not direction.

## Ranked recommendations

1. **Run a one-time catch-up triage before trusting any count (this week,
   timeboxed, not part of the daily).** Complete/cancel the month's done
   work, then bulk-release NEXT→15 and PENDING→10 with Alt+N. Until then,
   treat all chips, caps, and freshness counts as biased. Add one line to the
   weekly prune ("if returning from a gap, do the catch-up pass first") so
   the next lapse self-heals.
2. **Bound the freshness gate.** E.g. "REVIEW until 0 new *or 5 minutes /
   20 items*, then stop; leftovers roll to the weekly prune (lengthen
   `task_refresh` if they recur)." An unbounded gate on a stale vault
   guarantees skipped mornings — the exact failure mode being recovered from.
3. **Split the morning line into an ordered checklist with release before
   link.** Suggested order: (a) bounded REVIEW, (b) clear due, (c) release
   anything not today (Alt+N) *first*, (d) link today's work, (e) set ≤3
   themes with highlight = most important deliberately placed first. Order
   matters: link-then-release destroys the plan; release-then-link protects
   it.
4. **Link late, not early.** Keep placeholders link-free at plan time; add
   the task link when the pomodoro starts (or keep at most the highlight
   linked). Pre-linking 4 tasks before any work is speculative lane promotion
   under a system with no decay.
5. **Reset the stale scheduled dates as part of the triage.** Complete (or
   re-schedule) the 09-29/09-30-dated daily habits so repeats roll; confirm
   the morning review rolls daily. Consider whether overdue daily habits
   should show as overdue or silently ride — either is fine, but pick one.
6. **Plan 2 themes, keep 1 in reserve.** Nights/templates should leave slack
   for emergent work; hitting 3/3 before logging a minute means the first
   interruption breaks the budget. The reserve is also where "link today's
   work" overflow goes without guilt.
7. **Define R and S and wire the diagnostics.** Pick numbers (e.g. total
   ready ≥ 40, scheduled ≥ 20 — calibrate after triage), implement the
   `bob_gtd#^diagnostics` alerts against `bob plan` output, and point the
   weekly orphan-check at the same query. An unwired alert is clutter.
8. **Calibrate "≈10 min" against reality.** Log a week of actual
   review durations (a pomodoro with timespan, or start/end times) and adjust
   the claim or the scope. With lanes over cap it is 30+ min; say so until
   triage lands, or mornings get skipped again.
9. **Clarify the daily line's wording.** Replace "PENDING → NEXT" with what
   to actually do (e.g. "pull today's work Pending-first"), and separate
   "clear due" (act on due items) from "REVIEW to 0 new" (re-stamp
   freshness). Morning brains should not have to interpret arrows.
10. **Keep the direction; schedule the re-check.** The sticky-lane + ledger
    design is sound but explicitly experimental (two-week trial with a keep
    rule per the decision record). Put a dated note in the weekly prune to
    judge: are lanes near cap without heroics? If yes, keep; if the prune
    stays a 40-release ordeal, revisit decay or a smaller Next cap before
    concluding the trial failed — the current overflow is backlog, not steady
    state, and must not be counted against the trial.
