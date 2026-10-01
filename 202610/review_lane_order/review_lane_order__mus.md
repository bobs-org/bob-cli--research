# Morning review lane order + lane-aware refresh intervals

Research for the proposal to (1) make the review-walk keymaps visit NEW →
pending → next → ready with interval/overdue/created ordering inside ready,
(2) add configurable refresh intervals for pending/next lanes and scheduled
tasks (all defaulting to 1), and (3) remove the seeded `fresh` dates. Ends
with a recommended solution and explicit adjustments to the requirements.

## 1. Verdict up front

The core idea is sound: the review queue today only knows Ready-lane tasks,
while the morning ritual already thinks in lanes (NEW → ROTTEN → PENDING →
NEXT). Extending the walk to cover pending and next is coherent and matches
the sticky-lanes model. But the proposal as written has three problems that
should change the requirements before anyone implements:

1. The ready-ordering example is ambiguous, and one reading of it describes an
   order no simple sort key produces. The spec needs the exact key (given
   below).
2. Default 1-day intervals for the whole pending/next lanes plus scheduled
   tasks converts freshness review from "~pool ÷ interval + arrivals" glances
   into something close to full-lane review every morning — the overwhelm the
   seed chunking was built to avoid. The defaults should fall back to the
   existing global interval, not 1.
3. The scheduled-task knob is mostly redundant (RESURFACED already guarantees
   due-on-the-day surfacing), and bulk-removing the seeded stamps floods NEW
   and destroys the chunking. Both should be narrowed or dropped.

Details and a staged recommendation follow.

## 2. How the system works today (verified in-repo)

- **Freshness scope is Ready-only.** `in_scope(t)` requires Tasks status type
  TODO (`src/native/freshness/state.rs`, `evaluate`), i.e. `[ ]`. Conformance
  S13 explicitly lists `[*]` (Next) and `[/]` (Pending / `IN_PROGRESS`) as
  out of scope (`state null`). The `READY_QUERY` Dataview filter enforces the
  same (`src/native/dataview/tasks/mod.rs`).
- **Queue order is NEW then DUE.** `queue()` in `state.rs`: NEW rows by
  `(path, line)`, then DUE (resurfaced + rotten together) by
  `(due_on, path, line)`. Queue JSON rows already carry `created`, `fresh`,
  `interval`, `due_on`, `days_overdue` (`src/native/freshness/cli.rs`).
- **Interval precedence** (`docs/freshness.md` §2, `interval_for` in
  `state.rs`): task `[refresh:: N]` → note `task_refresh` → config
  `freshness.interval` → 7. Range 1–365; invalid task/note values fall through
  with lints; an invalid `freshness:` block is a hard config error (exit 2).
- **Stamps happen in every lane.** "Who stamps" (§5) deliberately stamps Next,
  Pending, and Blocked tasks on gestures, so lane tasks may already carry
  `fresh` dates even though the evaluator ignores them. The seed likewise
  stamped every other open non-recurring task with today (the "other" bucket
  in `seed.rs`).
- **RESURFACED already covers due-day surfacing.** A task with
  `fresh < scheduled <= today` is due with `due_on = scheduled`, beating
  ROTTEN regardless of interval. Short deferrals surface on return with no
  hooks write.
- **Two implementations share conformance vectors.** Rust
  (`src/native/freshness/`) and bob-ledger-tools JS (`api.freshness`) run the
  §9/§10 vectors verbatim; the nav jump (`Ctrl+Alt+J/K` per the bob-plugins
  README) walks the JS `reviewModel()` queue, and `bob freshness list` is the
  headless equivalent. Any ordering or config change must land in both plus
  docs, or they diverge.
- **`[s` / `]s` binding unverified.** The plugin sources ship compiled, and
  nothing in-repo names `[s` / `]s`. It is presumably an Obsidian-level hotkey
  assignment pointing at the same next/previous-due commands as
  `Ctrl+Alt+J/K`. Confirm in the vault's hotkey settings before speccing; this
  report assumes both chords drive the same review-queue walk.

## 3. Requirement 1: lane-ordered walk with (interval, overdue, created) inside ready

### 3.1 The example needs disambiguation

Call the tasks A = (1d interval, just due), B = (7d, 1d overdue),
C = (7d, 3d overdue). The request says A before B, then "C before that one":

- Reading 1 ("that one" = A) demands C < A < B. No natural key produces this:
  interval-ascending gives A first; due-date-ascending gives C, B, A;
  overdue-ratio gives A, B, C. So reading 1 is unsatisfiable without a
  contrived key — treat it as a misreading, not the spec.
- Reading 2 ("that one" = B) demands A < B and C < B, i.e. interval dominates
  across intervals, overdue dominates within an interval. That is exactly the
  sort key `(interval_days ASC, fresh ASC, created DESC, path, line)`,
  since equal intervals make "more overdue" identical to "refreshed earlier"
  (`due_on = fresh + interval`).

**Adjustment A: specify the key as
`(lane_rank, interval_days ASC, fresh ASC, created DESC, path ASC, line ASC)`
and confirm the C-before-B reading with Bryan.** Note this deliberately
abandons the current DUE rule (`due_on` first): a just-due 1d task now jumps
ahead of a 5d-overdue 30d task. That is the requested semantic ("short leases
first"), but it is a behavior change worth stating plainly — chronic-but-long
lease tasks sink to the back every day.

### 3.2 Open points in the key

- **NEW ordering.** The proposal orders only ready tasks; keep NEW as
  `(path, line)` (current S14) or say otherwise. Do not silently re-sort NEW
  by `created` — many tasks lack `created` (it is only set by `gkeep pull`
  and explicit stamps), so a created-based NEW order is near-arbitrary.
- **Missing `created`.** Define null placement explicitly (recommend: missing
  `created` sorts before dated ones within the created tiebreak, or simply
  falls through to `(path, line)` — either is fine, but the vectors must pin
  one).
- **Lane rank values.** Proposed walk: NEW (any lane? see §4) → pending-due →
  next-due → ready-due, with RESURFACED placement decided (§5).

## 4. Requirement 2a: configurable pending/next intervals

This is the largest scope expansion in the proposal: two whole lanes enter
freshness evaluation. Consequences:

- **Volume.** Sticky lanes grow ~2–3 tasks/day with no automatic forgetting
  (per the sticky-lanes decision). Default 1 means every pending and next task
  is due essentially every day after its link-stamp ages out — the morning
  walk becomes full committed-lane review. That directly recreates the
  overwhelm the seed staggering was built to prevent, now with higher-stakes
  tasks.
- **Double duty.** PENDING → NEXT already has a dedicated ritual step (link
  today's work, release the rest). Daily freshness-due on the same tasks
  duplicates that step under a different key.
- **Precedence slot.** The lane default must sit somewhere in the chain.
  Recommend: task `[refresh:: N]` → note `task_refresh` → **lane default** →
  global `freshness.interval` → 7. Rationale: note overrides are deliberate
  per-project tuning ("see this less often"); lane defaults are global
  fallbacks like the existing global.

**Adjustment B: add `freshness.pending_interval` and
`freshness.next_interval` (1–365, null/absent = fall back to
`freshness.interval`), but do NOT default them to 1.** Ship them unset so
behavior is unchanged until Bryan opts in, then tune during the trial
(suggested starting points: pending 3, next 7 — committed work deserves
slower leases than the ready pool, not faster). Unknown-key tolerance,
exit-2-on-invalid, and mobile-defaults handling follow the existing config
pattern; the JS mirror needs the same fields and a namespace version bump.

A cheaper alternative worth considering: pending/next tasks are due only while
unstamped-in-lane (confirm once when entering the lane, then normal lease).
That bounds the walk without new daily load. See §7.

## 5. Requirement 2b: default interval for scheduled tasks

Mostly redundant as specified. RESURFACED already forces any task whose
`scheduled` date has arrived (with an older stamp) due with
`due_on = scheduled` — "refreshed on the day they are due" is current
behavior, no knob needed. The new knob would only change two edge behaviors,
both questionable at default 1:

- **Pre-due rot.** A task stamped 3 days before its `scheduled` date with a
  1d interval goes ROTTEN *before* the scheduled day — early surfacing that
  fights the deferral (future-scheduled tasks are out of scope / Blocked for a
  reason).
- **Post-due echo.** A task confirmed on its due day becomes due again
  tomorrow, then daily until rescheduled — noise for anything due-dated but
  not done.

**Adjustment C: drop the scheduled-interval knob.** Keep RESURFACED as the
due-day mechanism and let post-return tasks use the normal interval chain. If
a knob is still wanted, scope it narrowly: it applies only when
`fresh >= scheduled` (post-return repeat cadence), never pre-due — and even
then, default it to the global interval, not 1.

Where RESURFACED sits in the walk order still needs one decision: the current
queue mixes resurfaced with rotten by `due_on`. The proposal's "due scheduled
tasks … in that order" (before other ready) suggests promoting RESURFACED to
its own tier: NEW → pending-due → next-due → RESURFACED → ROTTEN-by-key.
Recommend that; it matches the existing ritual (RETURNED first, then
age-expired ROTTEN).

## 6. Requirement 3: remove the seeded stamps

Recommend against bulk removal.

- The seeded `[fresh::]` dates are byte-identical to honest stamps; no
  command can distinguish "fake" from "confirmed since." Any strip is either
  date-heuristic (deletes real confirmations) or whole-population (deletes
  everything).
- Whole-population removal returns every ready task to NEW simultaneously —
  one giant NEW morning, i.e. exactly the overwhelm the seed was built to
  avoid, now without the stagger.
- The seed already did its job (chunking); honest `Alt+F`/`Alt+Shift+F`
  reviews are overwriting fakes with real confirmations daily. The fake
  population decays on its own, and the decay rate is observable
  (`refreshed_today`, `budget_met`).

**Adjustment D: do not strip; let genuine reviews replace seed dates, and
measure the replacement rate via `refreshed_today` during the trial.** If a
clean break is truly wanted, the least-bad version is per-note lazy expiry
during review (restamp-on-touch, which is already the ritual), never a vault
rewrite. Note the seed also stamped non-ready lanes with today — under new
lane intervals those silently become due per the new leases, which is
acceptable and self-healing.

## 7. Alternatives considered

1. **Nav-only walk, no evaluator change.** Teach the jump commands a lane-aware
   walk (pending-due → next-due → ready queue) while leaving freshness scope
   Ready-only and lane tasks on link-stamp recency. Smaller, single-plugin
   change; but it forks the "due" definition between the jump and
   `bob freshness list`, violating the one-evaluator contract. Not
   recommended except as a prototype.
2. **Keep Ready-only freshness; lean on the existing ritual.** The current
   morning already covers PENDING → NEXT by linking/releasing. The marginal
   value of freshness-walking committed lanes may be lower than the cost. If
   the trial shows lane review is the pain point, do lane intervals then —
   with slow defaults.
3. **Confirm-on-lane-entry.** Stamp is already written on link/commit; treat
   lane entry as confirmation and start the lane lease from there. This is
   nearly free (data already exists) and bounds the walk. Recommended as part
   of the solution below.

## 8. Recommended solution

1. **Pin the spec (Adjustment A).** Walk order NEW → pending-due → next-due →
   RESURFACED → ROTTEN, ready-internal key `(interval ASC, fresh ASC, created
   DESC, path, line)`, NEW stays `(path, line)`, null-`created` handling
   pinned in vectors. Confirm the C-before-B reading and the `[s`/`]s`
   binding.
2. **Extend scope to pending/next with fallback defaults (Adjustment B).**
   `pending_interval` / `next_interval`, unset = global interval. Lane-entry
   stamps (already written) start the lease. Start conservative (pending 3,
   next 7 or unset), tune in trial.
3. **Skip the scheduled knob (Adjustment C).** RESURFACED covers due-day;
   revisit only if post-return cadence proves wrong.
4. **Keep the seeded dates (Adjustment D).** Let honest reviews overwrite;
   track `refreshed_today` / NEW-drain as the migration meter.
5. **Land it as a contract change, both sides at once:** Rust evaluator +
   queue + config, JS mirror + `reviewModel()` + api version bump, S14/S15 and
   §9/§11 vector updates, `docs/freshness.md` §§2/4/6/7, dash/rotten tier
   rendering, config lints + mobile fallback, `bob freshness list` output
   (lane column per row helps the walk make sense headlessly).
6. **Trial it like the gating trial:** two weeks, keep rule (e.g. review
   completes most mornings, no lost-needed-task case, NEW drains). Tune
   lane intervals before touching anything else.

## 9. Adjustments summary

- **A:** exact sort key + C-before-B confirmation (example as written is
  ambiguous; one reading is unsatisfiable).
- **B:** lane intervals fall back to the global interval; no default-1.
- **C:** drop the scheduled-task interval knob (RESURFACED already does the
  job); at most a post-return-only variant.
- **D:** do not bulk-remove seeded stamps; overwrite-through-review instead.
