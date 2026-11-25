# Snoozed Task Links (`^snoozed-tasks`): research and implementation recommendation

- Researcher: mus (independent swarm report, `__mus` suffix)
- Date: 2026-11-25
- Source task: `~/bob/bob.md` line 112, `^snoozed-tasks` — "Add support for 'snoozed' task links!"
- Task text at time of research:
  - Notes: 'Use new "Snoozed" H2 section in daily files for this!' + 'The `bob tick` command should be responsible for waking tasks!'
  - Goal: tasks known to be Today work but not actionable until after a time (canonical: event tasks; examples: email Dan after 15:30 meeting, home-only tasks after ~19:00).

This report answers: is the proposal a good idea, how should it be built, what should change, and what is the recommended solution.

## 1. The problem is real and currently unexpressible

Bob has day-granularity deferral but no intra-day deferral for general tasks:

- `[scheduled:: YYYY-MM-DD]` is date-only. `src/native/freshness/placement.rs` (`first_valid_scheduled`) parses a strict calendar date; `docs/date-marks.md` says a datetime in that field is a repair-flag error ("a bad date, a word, a datetime, a duplicate..."). A separate open task, `^task-props-use-time` ("Migrate task properties that use a date value to use times instead"), confirms time-of-day support is wanted but not yet built.
- Derived Blocked follows a future `scheduled` date for the whole day. There is no "Blocked until 15:30 today" state. Once the date arrives the task resurfaces as TICKLER via `returned_on`/`returned_by` (`docs/freshness.md` §4/§10b, `decisions:unblocked-tasks-resurface-as-ticklers`), but intra-day it is either Today (linked, counts toward `plan.max_links`, shows in `bob plan` TODAY) or invisible (unlinked, risks being forgotten).
- Event Tasks (`docs/reference/vault-format.md` "Events section and Event Tasks", `docs/plan.md`, `decisions:event-buffers-widen-the-span`, `decisions:synced-meetings-link-by-phase`) already solve the canonical example for calendar-backed work: a `**HHMM-HHMM**` span in `## Events`, filed under past/running/future MEET entries by `bob gcal sync`, with buffered spans for occupancy. Ad-hoc tasks (email Dan, home chores) have no equivalent.
- Today is binary and read-time: "open tasks with a dedicated Task Link under today's open Pomodoros, computed at read time" (`docs/plan.md` §Today, `decisions:today-is-read-from-the-ledger`). There is no "later today" membership. The plan budget ledger is "the lines from a `## Pomodoros…` heading up to the next `## ` heading" (`docs/plan.md` §The ledger; identical in `docs/reference/vault-format.md`). Anything parked elsewhere in the daily note is not Today by construction.

So the user today must either clutter TODAY with not-yet-actionable links (paying link-budget and attention cost) or leave the work unlinked (paying recall risk). A "snooze until HH:MM today" fills that gap. The feature is worth building.

## 2. What the two-bullet proposal leaves unspecified

The task as written names a location (`## Snoozed` H2 in daily files) and an actor (`bob tick` wakes) but specifies neither the data model nor the wake semantics. An implementer cannot proceed without answers to all of these:

1. **Link syntax and wake time storage.** Where does "after 15:30" live? Candidates: bold span prefix on the snoozed link line (`**1530** [[...]]`), an inline field (`[snooze:: 15:30]`, `[wake:: ...]`, `[after:: ...]`), a per-entry time range on a Snoozed pseudo-Pomodoro, or a subheading (`### 15:30`). No choice is named.
2. **Section placement and ledger interaction.** Daily notes today have `## Events` then `## Pomodoros` (observed 2026-11-25: `~/bob/2026/20261125.md` has exactly those two H2s). Where does `## Snoozed` go? If placed immediately after `## Pomodoros`, it naturally terminates the ledger (ledger ends at next `## `), which is good. If placed before `## Pomodoros` or between Events and Pomodoros, writers and readers must be careful. The proposal does not say.
3. **Wake destination.** When 15:30 arrives, where does the link go? Append to the currently running entry? To a dedicated "afternoon" open entry (created if missing)? To the first open unnamed entry? What if no open entry exists, or a timed Pomodoro is already running (`bob capture =…` refuses while one runs; `duplicate_open_pomodoro_name` lints two open MEETs)? What if the target entry is exempt (PLAN)?
4. **Wake effect on lanes.** Linking Ready under open Pomodoros promotes to Next and sticks (`decisions:task-lanes-are-sticky`; `src/native/task_status_hooks/reconcile.rs` + `pomodoro.rs`). Is a pre-wake snoozed task already Next (committed, waiting for its hour) or still Ready (uncommitted until woken)? Either is defensible; the proposal does not pick. The wrong pick either double-promotes or loses commitment.
5. **Pre-wake visibility.** Is a snoozed-but-not-yet-due link Today? It must not be (it is not under `## Pomodoros`, so by definition it is not — good), but then: does it count toward NEXT/PENDING caps, does it walk in `]s` (PRE→NEW→...→TICKLER→ROTTEN→POST per `decisions:recurring-occurrences-walk-when-due`, `decisions:review-attention-follows-the-walk`), does it accrue freshness/keeps/decay (`decisions:task-decay-is-one-ladder`)? Morning review showing "email Dan" at 08:00 when it cannot be done until 15:30 defeats the purpose; hiding it entirely risks starvation if wake fails.
6. **Day rollover.** What happens to unwoken Snoozed rows at midnight? Carry to tomorrow's Snoozed? Expire to Ready/Next? Become TICKLERs via `[unblocked::]`? The existing Blocked→Ready recovery stamps `[unblocked:: today]` and resurfaces through freshness; snooze needs an equivalent "missed wake" story.
7. **Tick integration shape.** `bob tick` runs six steps in order (`src/native/tick/catalog.rs` `STEPS`: gcal → gmail → gkeep → refs → projects → tasks, defaults 60m/60m/manual/15m/15m/15m). Is wake a seventh step (new `tick.steps.snoozed`, new gate/adapter/receipt/config keys) or part of the existing `tasks` step (`task reconcile --retry-timeout 120 -f json`)? A new step needs cadence/ceiling/off/manual handling, writer-host gating (`tick.writer` defaults to `gcal.writer`), readiness gates, and JSON receipt changes. Reusing `tasks` keeps atomicity with lane promotion but couples wake cadence to reconcile's 15m default.
8. **Idempotency, races, and multi-host.** Tick "never holds the shared vault lock across steps" (`src/native/tick/mod.rs` help text) and refuses on non-writer hosts. What if the user edits the daily note on mobile while tick wakes? What if two hosts both think they are writer? What if wake fires twice? The write must be a guarded capture-style write with no commit (like `bank ack`), or go through `task_status_hooks_write` snapshot/stage/apply (`src/native/task_status_hooks_write.rs`).
9. **Display and clients.** Ledger-tools renders TODAY/PENDING/NEXT/READY badges, Today roots, In-Progress half-rings, and walk footers from `plan_budget.links` + `today_tasks` (`docs/plan.md` contract table). Mac Capture's idle agenda/TODAY badge applies the same ladder. A Snoozed section needs a rendering contract (or an explicit "invisible until woken" rule), plus `bob plan` JSON additions, or every surface silently disagrees about "what is Today at 14:00".
10. **Relation to `scheduled::`-with-times.** If `^task-props-use-time` later adds times to `scheduled`, do we end up with two parallel intra-day deferral systems (a time-aware Blocked derivation vs a Snoozed section + mover)? The proposal does not address convergence.

As specified, the idea is directionally right but not implementable. Section 4 recommends a narrowed shape that answers all ten.

## 3. Evidence: how the neighboring machinery works today

- **Ledger and Today.** `docs/plan.md` §§ Ledger/Entries/Links/Today; `docs/concepts/today-and-the-pomodoro-ledger.md`; `docs/reference/vault-format.md` §§ Ledger/Next/Events. Only dedicated Task Links (direct child bullet, body exactly one `[[target#^id]]` after stripping 🍅, under an open entry) count. `bob plan` is read-only; reconcile/capture perform writes. Blocked tasks keep no live link under open Pomodoros.
- **Sticky lanes.** `decisions:task-lanes-are-sticky`: link promotes Ready→Next; unlink never demotes; only explicit release (Alt+N) lowers Next/Pending→Ready; Blocked overrides everything and recovery recomputes (Ready unless linked today or recent activity). Any wake that links must respect this: wake = link + reconcile promotion, never a direct checkbox rewrite.
- **Freshness/decay/walk.** `docs/freshness.md` (Rust `src/native/freshness/`, JS `api.freshness`); `decisions:task-decay-is-one-ladder` (consent-based WIP→Next→Ready→P1..P4, no silent moves); `decisions:review-attention-follows-the-walk` (`s` lit iff `]s` has a landing). Snooze must not silently move lanes and must not bypass the decay card: a snoozed keep is still a keep.
- **Unblocked recovery.** `decisions:unblocked-tasks-are-offered` (managed Done offers successors via picker; unpicked rows recover without a link) + `decisions:unblocked-tasks-resurface-as-ticklers` (`[unblocked:: today]` WRITE stamp → TICKLER). Snooze wake should reuse the `[unblocked::]`/TICKLER machinery for missed wakes rather than inventing a second resurface path.
- **Tick.** `src/native/tick/{mod,run,catalog,config,schedule,gates,adapters,state,receipt}.rs`. Key facts: ordered pass gcal→gmail→gkeep→refs→projects→tasks; `tasks` step is `task reconcile`; per-step cadence (`tick.steps.<name>: 5m–7d|manual|off`), `Trigger::{Scheduled,All,Named}`, readiness gates (daily note ready), writer-host refusal, run-lock with already_running short-circuit, JSON receipt. Adding a step is not free: catalog entry, gate, adapter, config validation (`tick.steps.<name>: unknown step` otherwise), docs, and Mac CI implications.
- **Event/MEET precedent.** `decisions:synced-meetings-link-by-phase` (past/current/future filing under closed/running/placeholder MEET, link sorting via `decisions:sync-sorts-event-task-links`, born-done for ended per `decisions:ended-synced-meetings-are-born-done`); `decisions:event-buffers-widen-the-span` (buffered span = occupied, meeting span = truth). A Snoozed wake that appends links to MEET-like entries must obey the same one-running-entry and link-sort invariants.
- **Reference "Snoozed" precedent.** `bob ref list` already has a `Snoozed` kanban group with wake dates and waiting-on reasons drawn from JSON, never vault text (`docs/reference/plugins/bob-ledger-tools.md`, `docs/ref.md` "Snoozed reasons"). Task snooze should steal its vocabulary (wake date/reason, `N awake · M snoozed` header shape) for consistency, but note the direction: ref snooze is JSON-driven state rendered read-only; the task proposal is vault-text links moved by a writer. Do not copy the storage, copy the UX language.
- **No existing task snooze.** `grep -rni snooz` over `src/` + `docs/` finds only the ref-board Snoozed group, Gmail `snoozed` label constant, and task fixtures — no `[snooze::]` field, no `## Snoozed` parser, no wake logic. This is greenfield inside the daily note.

## 4. Critique: good idea, wrong layer as literally proposed

**What is good.** Ledger-local parking matches Bob's architecture (Today read from ledger, never written to tasks). A daily-note section is visible, undoable via vault Git, works offline, and needs no schema migration. Reusing tick's periodic pass matches "frequent background work" (`bob tick` help: "what cron runs") and keeps interactive paths (`bob plan`, capture) read-fast.

**What is risky.**

- A mover-based design (tick rewrites the daily note to relocate links) is the most race-prone option in the toolbox. Every other recent decision moved *away* from writers duplicating ledger state onto task lines (`decisions:today-is-read-from-the-ledger` rejected the `#today` tag for churn/races/staleness). A time-based mover reintroduces the same class: two writers (human editing Pomodoros + tick moving Snoozed links), one vault file, 15m cadence, no cross-step lock.
- The proposal duplicates rather than extends the scheduling system. Once `scheduled::` gains times, Bob would have date-deferral (Blocked derivation, freshness-gated, two-language) *and* time-deferral (section mover, Rust-only) with different semantics, different review behavior, and different JSON. Users should not need to learn which deferral to use by time granularity.
- `bob tick` is the wrong granularity anchor as stated. Wake latency wants minutes (15m default is arguably already too coarse for "after 15:30"), but tick steps are tuned for background sync (gcal 1h, tasks 15m), gated on writer host and daily-note readiness, and skippable (`manual`/`off`). A wake tied to tick inherits all of those caveats: phone-only days, non-writer hosts, and `tick.steps.tasks: off` all silently disable waking. Read-time derivation (like Today itself) degrades gracefully; a mover fails closed.

Verdict: keep the *location* (daily-note section) and the *verb* (wake), but change the *mechanism* from "tick moves links" to "reconcile derives wake + links, tick merely schedules reconcile."

## 5. Alternatives considered

| Alternative | Shape | When it wins | Why not sole choice |
|---|---|---|---|
| A. Proposed literal: `## Snoozed` + new tick step moves links | Section holds time-annotated links; new step relocates due rows under open Pomodoros | Simplest to explain in one sentence | New step/config/receipt surface; write races; inherits writer-host + cadence caveats; duplicates scheduling |
| B. Time-aware `scheduled` (extend `scheduled::` with optional `HH:MM`, derive intra-day Blocked) | No new section; `[scheduled:: 2026-11-25 15:30]` blocks until 15:30, then resurfaces | Unifies day + intra-day deferral; read-time, no mover; aligns with `^task-props-use-time` | Larger change (freshness/Blocked derivation in Rust + JS, date-marks, capture reschedule UI, vectors); no "Today but later" parking place |
| C. Event-Task generalization (allow ad-hoc `**HHMM-HHMM**` rows outside `## Events`) | Reuse MEET filing/buffer/phase machinery | Canonical example already works this way | Overloads calendar semantics; forces fake meetings for "after 19:00"; pollutes Events sync ownership |
| D. Manual parking lot (Snoozed section, no automation) | Human moves links when ready | Zero machinery; still solves recall | No wake; fails the stated goal; becomes stale like any inbox |
| E. Recommended hybrid (section + derive, reconcile owns wake) | `## Snoozed` holds wake-annotated dedicated links; wake derived at read time + materialized by existing `tasks` reconcile; tick only provides cadence | Keeps ledger-local UX; no new tick step; no second scheduler; graceful degradation | Slightly more spec writing than A; needs reconcile + plan + ledger-tools parity |

## 6. Adjustments to the requirements (explicit)

1. **Pin the time syntax.** Adopt one: bold time prefix on the snoozed link line, e.g. `- [[garden#^label-trays]] · **after 15:30**` is rejected (prose times are forgeable, cf. buffer decision). Instead require a machine field on the link line: `[wake:: 15:30]` (same-day) with optional `[wake:: tomorrow 09:00]`? No — keep scope tight: same-day `HH:MM` only, validated `00:00–23:59`, one per line, duplicates/invalid = lint + never wake. Rationale: strict, grep-able, strippable from titles, mirrors `[buffer::]` precedent.
2. **Pin section placement.** `## Snoozed` goes *after* `## Pomodoros` (and therefore terminates the ledger by the existing "up to next `## `" rule — no ledger parser change). At most one per daily note; a second is a lint and only the first wakes. `## Events` stays above `## Pomodoros`; sync never touches Snoozed (mirrors `-F` day-reset semantics: Snoozed rows are user-owned, never tombstoned by gcal).
3. **Pre-wake is not Today and not Next-promoted.** Snoozed links never count toward `plan.links`, TODAY, or lane promotion until woken. They are excluded from `]s` before their wake minute (like future-scheduled Blocked rows) and enter the walk as TICKLER-like arrivals after a missed wake. This preserves sticky-lane and decay invariants: no silent promotion, no keep-counting before due.
4. **Wake = link + reconcile, not tick rewrite.** `bob task reconcile` gains wake planning (which Snoozed rows are due at `now`) and stages the same link-append + lane-promote it already performs for ledger links. `bob tick` gets *no new step*; its existing `tasks` step carries wake with its 15m cadence. `bob tick -d/-s` surfaces wake under `tasks` detail rather than a new row. This kills the new-step config/receipt/gate cost and keeps one writer (reconcile) for all lane changes.
5. **Destination rule (single).** Due rows append as dedicated Task Links under the day's designated "wake target": the open non-exempt entry whose name or time range covers the wake minute when one exists, else the first open non-exempt entry, else create no entry and leave the row snoozed with a `wake_target_missing` lint (never auto-create Pomodoros — sync's MEET-creation rules already show why auto-creation surprises). Within an entry, wake-appends sort by wake time (mirrors `sync-sorts-event-task-links`).
6. **Missed-wake and rollover.** A Snoozed row still present and due at reconcile time wakes normally the next run (idempotent: already-linked targets are no-ops). A Snoozed row in a past daily note never wakes; the next reconcile on the current day reports `snoozed_expired` and leaves the task in its lane to resurface via existing freshness/TICKLER rules (reuses `[unblocked::]` resurface, no new stamp).
7. **No auto-demote, no silent decay.** Waking never writes `[fresh::]`, `[keeps::]`, `[scheduled::]`, or checkbox changes directly; it only links, letting reconcile's existing promotion derive the lane. Decay-card and Rotten Log behavior unchanged.
8. **Observability.** `bob plan -f json` gains `snoozed: {due, pending, next_wake_at}` alongside `today`; human meter gains `SNOOZED n (next HH:MM)`; `bob task reconcile -f json` reports `woken` rows like dependency projections. Ledger-tools mirrors `isToday`-style `isSnoozedDue` under shared vectors. Without this, Mac Capture idle agenda and walker footer cannot agree on "what is actionable at 14:00".

## 7. Recommended solution

Build **E (hybrid) in two phases**, no new tick step:

**Phase 1 — manual Snoozed + read-time visibility (no wake writes).**

- Accept `## Snoozed` after `## Pomodoros` in canonical daily notes only.
- Accept dedicated snoozed links: direct-child bullets under `## Snoozed` whose body is exactly one block link plus one valid `[wake:: HH:MM]` field (same-day). Anything else is a lint (`snoozed_not_dedicated`, `snoozed_wake_invalid`), never woken.
- `bob plan` (Rust + ledger-tools) parses and reports Snoozed counts + `next_wake_at`; snoozed-due rows appear in a read-only "due" style but are *not* Today until linked. This alone delivers recall value and validates syntax before any writer ships.
- Docs: `docs/plan.md` (ledger/Snoozed/Today interaction), `docs/reference/vault-format.md` (section order, dedicated-link rule), `docs/task-dependencies.md` §12-adjacent note (wake links vs successor offers — wake never offers, it links the named row only).

**Phase 2 — reconcile-owned wake on the existing cadence.**

- `bob task reconcile` plans wakes (Snoozed rows with `wake <= now`, target resolvable, not already linked under open Pomodoros) and stages link-appends + standard promotion via `task_status_hooks_write`. Guarded write, dry-run support, JSON `woken` list, idempotent re-runs.
- `bob tick` unchanged except `tasks` detail/hint text; wake latency = `tick.steps.tasks` cadence (default 15m) with documented "up to N minutes late" contract, plus `BOB_NOW`-pinned tests. No `tick.steps.snoozed`, no new gate/adapter/ceiling.
- Rollover/expiry, lints, and JSON as in §6. Conformance vectors shared Rust↔JS for parse/derive; Rust-only for the write (mirrors freshness split: Rust owns production increment, JS owns display).

**Why this over literal A.** Same user-visible UX (park in Snoozed, auto-appear in Today after the hour) with: one fewer tick step and its config/receipt/gate surface; one writer for lane changes (reconcile) instead of two; graceful degradation (read-time Snoozed counts work even when tick is off/wrong-host); and a clean merge path into time-aware `scheduled::` later (the `[wake:: HH:MM]` field becomes sugar over `[scheduled:: today HH:MM]` when `^task-props-use-time` lands, with the section retained as the "Today but later" view).

## 8. Open questions for the lead (not blockers for Phase 1)

- Should `[wake::]` allow `tomorrow HH:MM` or cross-midnight (`after 00:30`)? Recommendation: no — same-day only; multi-day stays with `scheduled::`.
- Should wake respect `plan.max_links` (skip + lint when over cap) or exceed it (Today over-cap already exists as `over` status)? Recommendation: link anyway and report `plan_link_cap_exceeded` — waking is a promise kept, not new planning.
- Should Mac Capture idle agenda show Snoozed-due rows pre-wake? Recommendation: counts only (`SNOOZED n · next HH:MM`), no direct answer actions until woken — mirrors ref-board Snoozed (display, not action).

## 9. Sources checked

- Task: `~/bob/bob.md` `^snoozed-tasks` + goal examples; daily `~/bob/2026/20261125.md` (Events + Pomodoros structure, `— MEET` + `— PLAN/WRITE/READ` entries).
- Docs: `docs/plan.md` (ledger/entries/links/Today/roots/status/lints), `docs/concepts/today-and-the-pomodoro-ledger.md`, `docs/concepts/tasks-and-lanes.md`, `docs/reference/vault-format.md` (ledger, Next, clock tags, Events/Event Tasks), `docs/freshness.md` (§§1–4/10b keep/decay/unblocked), `docs/date-marks.md` (datetime is repair-flag), `docs/ref.md` + `docs/reference/plugins/bob-ledger-tools.md` (ref Snoozed kanban precedent).
- Decisions (via `sase memory read`): `task-lanes-are-sticky`, `today-is-read-from-the-ledger`, `task-decay-is-one-ladder`, `unblocked-tasks-are-offered`, `unblocked-tasks-resurface-as-ticklers`, `synced-meetings-link-by-phase`, `event-buffers-widen-the-span`, `gcal-force-resets-the-day`, `review-attention-follows-the-walk`.
- Code: `src/native/tick/{mod,catalog,config,run,schedule,gates}.rs` (`STEPS`, `Trigger`, cadences, writer-host gate, no-cross-step-lock), `src/native/task_status_hooks/{mod,pomodoro,reconcile}.rs` + `src/native/task_status_hooks_write.rs` (ledger scan, guarded writes), `src/native/freshness/placement.rs` (`first_valid_scheduled` date-only), `src/native/capture_sections.rs` (section listing), `src/native/tick/config.rs` (unknown-step refusal).
- Negative evidence: no `[snooze::]`/`[wake::]` field, no `## Snoozed` parser, no wake path in `src/` or `docs/` (only ref-board Snoozed, Gmail label, fixtures).
