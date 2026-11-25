# Snoozed Task Links (`^snoozed-tasks`): consolidated research and recommendation

**Date:** 2026-11-25 · **Lead:** consolidated from five independent researcher reports
(cdx, cld, grk, mus, gem) plus the lead's own source verification.
**Task:** `~/bob/bob.md` `^snoozed-tasks` — *Add support for "snoozed" task links!*

## TL;DR

**Build it, narrowed.** All five researchers independently reached the same verdict: the
feature fills a real, currently unexpressible gap — *"committed to today, but not
actionable until HH:MM"* — and both of Bryan's notes point the right way (a `## Snoozed`
H2 in the daily note; `bob tick` wakes). All five also independently flagged the same
scope error: **Event Tasks must not be the canonical example or a v1 occupant** — their
`**HHMM-HHMM**` spans, MEET filing, clock-aware closes, and the Mac Calendar band already
snooze them, and routing them through `## Snoozed` would reopen at least four accepted
decisions.

The recommended shape, after adjudicating the researchers' disagreements:

- A `## Snoozed` section **after `## Pomodoros`**, holding one-line rows
  `- **HHMM** [[note#^id]]` with child notes as ordinary subtrees.
- Snoozing is a human planning gesture: it **promotes Ready → Next and stamps
  `[fresh::]`** exactly like Ctrl+Shift+Enter, but the row is **not Today** until it
  wakes — no 🍅, no `=`/`x` lineups, excluded from the `]s` walk like Today-linked rows.
- On-clock snoozed links **count toward `plan.max_links`** (reported as a breakdown) so
  snoozing is not a budget-evasion loophole. *(Main judgment call — see Open Questions.)*
- A new, cheap, daily-note-only **`bob snooze wake`** command run by a new **5-minute
  `bob tick` step** (after `gcal`, before `tasks`), never by the 15-minute whole-vault
  reconcile. Wake is a guarded, idempotent subtree move that re-runs the link guards and
  **never lands in a running Pomodoro**.
- Authoring via a new capture token **`z:<when>`** (`s:1530` already means *+1530 days*),
  an Obsidian gesture that shells out to `bob snooze add`, and hand-written rows that
  work from day one.
- Same-day only. No auto-carry at midnight. Multi-day deferral stays `[scheduled::]`;
  "after that meeting" ergonomics come from `z:` completions offering today's event end
  times (and, later, the separate `starts after` relation work).

## 1. The request

`~/bob/bob.md:112` (`[/]`, created 2026-11-22, work log: *2026-11-25 07:47 apollo
research*):

> Add support for "snoozed" task links!
>
> - Use new "Snoozed" H2 section in daily files for this!
> - The `bob tick` command should be responsible for waking tasks!
>
> **The Goal.** I sometimes have tasks that I know I need to do today, but that can't be
> done until after a certain time. The canonical example of this is event tasks, but
> there are plenty of other examples: email Dan on Monday with Yogi-interview updates
> (couldn't happen before the 3:30 PM meeting); tasks that can only be done at home
> (after ~7 PM).

The note names a location and an actor but specifies neither the data model nor the wake
semantics (mus enumerated ten unanswered design questions). This report pins all of them.

## 2. Verified ground truth

Every claim below was verified against source by at least one researcher; the
contested ones were re-verified by the lead on bob-cli `5ab392a1`.

| Fact | Evidence |
| --- | --- |
| **Today** is open tasks with a dedicated Task Link under today's **open** Pomodoros, computed at read time; never a tag or field. | `decisions:today-is-read-from-the-ledger`; `src/native/plan_budget/today.rs`; `bob-ledger-tools/src/060-today.js` |
| The ledger runs from `## Pomodoros` to the next `## ` heading. The same boundary rule is copied in ≥4 plugins. | `src/native/pomodoro.rs:582` (`pomodoros_section_range`); plugin copies enumerated by cld |
| Recent daily notes end at `## Pomodoros` — no H2 follows it. gcal creates `## Events` **immediately above `## Pomodoros`**. | Lead verified `2026/202611{20,24,25}.md`; `src/native/gcal/plan.rs:2313` |
| `Snoozed` is not yet a structural H2; the registry to extend is `is_structural_h2_key` (Tasks, status groups, Pomodoros, Events). | `src/native/capture_drawers.rs:594` (lead verified) |
| `s:<digits>` parses as a pure **day offset** — `s:1530` schedules ~4 years out. `z:` is unused. | `src/native/capture_language/markers.rs:10` (`parse_schedule_token`; lead verified) |
| On a plain `x` close, every unstruck plain link in the closing entry takes the ledger outcome **in progress**: started `[/]`, gets a 🍅, carried. | `docs/capture.md` close-outcomes table (lead verified) — this is why auto-wake into a running session is unsafe |
| Ctrl+Shift+Enter **stamps `[fresh::]`** when it rewrites the task line (Ready/Blocked → Next); Today-linked rows are excluded from freshness review at read time. | `docs/freshness.md:9,659` (lead verified) |
| Lanes are sticky: linking raises Ready → Next; unlink never lowers; only Alt+N releases. Daily-note-resident tasks are the exception (unlinking can clear Next there). | `decisions:task-lanes-are-sticky`; gem's "R9" trap |
| `[scheduled::]` is **date-only** (`NaiveDate`); a datetime there is a repair-flag error; a future date derives Blocked; reconcile **consumes** links to Blocked tasks. | `src/native/freshness/placement.rs`; `docs/date-marks.md`; `docs/task-status-hooks.md` § Blocked task links are consumed |
| Off-clock links are already **exempt** from `max_links`; `over` = on-clock links > cap. | `docs/plan.md:114`; `src/native/plan_budget/mod.rs` (lead verified) |
| `bob tick` is Mac-only cron `*/5`; steps gcal 60m → gmail 60m → gkeep manual → refs 15m → projects 15m → tasks (reconcile) 15m; a noninteractive run short-circuits with `already_running`; observed runs take 0–62 s. | `src/native/tick/{catalog,lock}.rs` (lead verified); `cronctl list` + `cronctl logs bob-tick` (cld) |
| Capture's existing-task placement prefers the **running** exact-type entry first, then open exact, then open containing, then a new `() — TYPE` placeholder. | `src/native/capture/task_theme.rs:1051` (`placement_for_task`) |
| The Mac agenda already does exact-minute boundary refresh (`refresh_at`) and listens for the Darwin `tick-finished` ping; it is a thin client. | `src/native/capture_pomodoros_agenda.rs`; `CaptureAgendaBoundaryRefresh.swift`; `decisions:mac-capture-is-a-thin-client` |
| Whole-note link repair (`repair_links_in_note_with`) and the task-move link rewrite scan the entire note, so snoozed links survive task moves/renames **for free**. | `src/native/collect_done/link_repair.rs`; `bob-plugins` `250-task-move.js:245` |
| One shared plugin helper, `planDeferredPomodoroLinkCleanup`, prunes links for release, close, cancel, decay, roll and Ctrl+Shift+M — but **only inside `## Pomodoros`**. | `bob-navigation-hotkeys/src/160-pomodoro-reorder.js:538` (cld) |
| "Snoozed" already means two other things: the Reading Board's date-based blocked-reference lane, and project/area frontmatter `snooze:` (a note-level `#hide` hold). A June 2026 task-line snooze property was **cancelled**. | `docs/ref.md`; grk's done-note archaeology |
| `docs/task-tag-marks.md` explicitly rejected a moon/snooze glyph for `#hide` *because* it "implies time-based snooze" — the glyph is free for this feature. | cld |
| `starts after` is a successor **relation**: it never blocks, and a managed close **offers** the next task for an explicit pick; auto-linking offers is forbidden. | `research:202611/starts_after_relation/…__final.md`; `decisions:unblocked-tasks-are-offered` |

**Evidence the pain is real (gem, cld).** `job#^email-dan-eod` is the note's own Monday
example: created 2026-11-23, linked under `() — WRITE` among ~18 open links (budget 13),
visually unactionable until 15:30, carried still-open into Tuesday, cancelled 11-25
("He already called me yesterday"). The plan gave no signal at 15:30 that it had just
become doable. Separately, Bryan has used untimed `() — LATER` inventory placeholders —
which count as Today all day — showing the demand for a "later" bucket that this feature
makes timed and self-emptying.

## 3. Critique: is this a good idea?

**Yes — unanimously, with the same narrowing.** The gap is the missing middle
granularity:

| Mechanism | Granularity | Blocks? | Today? | Resurfaces itself? |
| --- | --- | --- | --- | --- |
| `[scheduled::]` | day | yes (`[?]`, link consumed) | no | tomorrow's TICKLER |
| Task Link in open Pomodoro | day | no | yes, from 6 AM | n/a |
| `() — LATER` placeholder | none | no | yes (noise) | no |
| Event Task span | minute | no | time-aware | yes (clock) |
| **Snoozed link** | **minute, today** | **no** | **not until wake** | **yes (tick)** |

What the note gets **right** (all reports): daily-note storage preserves sticky lanes
(a task-line timestamp would derive Blocked and destroy `[*]`/`[/]`), stays
hand-editable plain Markdown, costs zero task-line schema change, degrades safely
(older parsers ignore an unknown H2 rather than working it early), and `bob tick` as the
waker reuses the existing single-writer discipline instead of a new daemon.

What the note gets **wrong** (all reports):

1. **Event Tasks are a trap, not the canonical example.** Four accepted decisions file
   future meetings under `() — MEET` in `## Pomodoros`
   (`synced-meetings-link-by-phase`, `meet-filing-follows-google-until-edited`,
   `ended-off-clock-events-settle`, `past-day-sync-closes-bob-filed-meetings`); timed
   closes already protect `not_started` events; off-clock events are already
   `max_links`-exempt; and you cannot wake a 15:00 meeting *at* 15:00 (you need lead
   time). The genuinely unserved cases are exactly the note's *other* examples.
2. **"After the meeting" is not a clock.** The interview can run long or end early. A
   15:30 snooze is an honest *approximation* the user chooses; the exact mechanism for
   "when the predecessor actually finishes" is the separate `starts after` relation
   (offers on close, never auto-links). v1 serves the Dan case with a clock plus smart
   completions; event-anchored wakes are a later, separate design.
3. **Burying wake in reconcile is too slow and too heavy** — a 15-minute whole-vault
   scan with a 10-minute ceiling for a job that needs to read one file.
4. **Unspecified semantics would bite.** Without explicit rules, snoozing would either
   leak into Today (defeating the purpose), dodge the plan budget, revive
   released/completed tasks at wake (plugin gestures only clean `## Pomodoros`), or
   dump a woken link into a running session where a plain `x` would record it as
   worked.

No researcher recommended a different fundamental approach. The alternatives were all
evaluated and rejected by multiple reports for the same reasons: task-line
timestamp/datetime `[scheduled::]` (breaks sticky lanes, Dataview date parsing, and the
Gmail-hold stack; that is `^task-props-use-time`'s separate multi-day problem); inline
wake markers on ledger links (every Today/budget/lineup reader must learn them); a
timed/`SNOOZED` placeholder Pomodoro (is Today, mangles entry grammar); hidden JSONL
state (violates the visible-ledger philosophy); read-time-only derivation with no mover
(reopens the Today definition — membership would no longer be "open Pomodoro links");
notification-only (doesn't fix the agenda).

## 4. Where the researchers disagreed, and the adjudication

This is the lead's main value-add: the five reports agree on shape but split on six
design points. Each resolution below is grounded in verified behavior, not vote-counting.

### 4.1 Section placement — **after `## Pomodoros`** (mus, gem; over cld, grk)

cld and grk placed `## Snoozed` between `## Events` and `## Pomodoros` for timeline
aesthetics. Verified facts favor the other side: daily notes currently end at
`## Pomodoros`, so an after-section gives the ledger a clean terminator with **zero**
changes to any existing anchor; gcal's "create `## Events` immediately above
`## Pomodoros`" (`gcal/plan.rs:2313`) keeps working untouched; the ledger is not pushed
down below the `bob-plan` callout; and every old binary/plugin cleanly ignores a section
past the ledger. Between-placement would require auditing the gcal insertion anchor and
anything else that assumes Events↔Pomodoros adjacency. Add `Snoozed` to
`is_structural_h2_key` either way. *(If Bryan prefers the timeline reading, the cost is
one gcal-anchor change — flagged as an open question, default: after.)*

### 4.2 Row format — **`- **HHMM** [[note#^id]]`** (grk, gem; over cld's grouped rows, mus's `[wake::]` field, cdx's RFC 3339 records)

The bold compact 24-hour time mirrors Event spans and the event-link-time pills, sorts
lexicographically, and is trivially hand-written. Child bullets under the row are the
link's notes and travel as a subtree on wake (same shape as ledger link subtrees).
mus's `[wake:: HH:MM]` inline field would put Dataview-indexed field semantics on
non-task lines in a system where a datetime in a date field is a repair flag. cdx's
full RFC 3339 timestamps, snooze IDs, and DST handling are over-engineering once scope
is same-day-only: the owning daily note *is* the date, and Bob's timezone resolution is
already centralized (`src/native/env.rs`). cld's grouped time-parent rows keep the link
line byte-identical to a ledger link (nice for parser reuse) but add a second structural
level and empty-parent cleanup for little gain — `list_queued_links`-style parsing works
on the one-line form after stripping the time prefix. Grammar rules: column-0 bullets
only; `**HHMM**` (00–23/00–59, accept `HH:MM` on hand-edits, normalize on rewrite);
exactly one unstruck block link; optional ` — NAME` destination override (gem) can ship
later; writers keep rows sorted by time; one live row per task per day — re-snoozing
updates in place; malformed rows are skipped and reported, never guessed at.

### 4.3 Pre-wake semantics — **not Today; promoted + stamped at snooze; counted in the budget**

This was the deepest three-way split:

- **Today membership:** gem argued snoozed ∈ Today (with badges) to avoid walk/dash
  duplication and the daily-note lane trap; cld/grk/mus/cdx said not-Today. Resolution:
  **not Today.** Redefining Today reopens `today-is-read-from-the-ledger` and changes
  the meaning of the central `today_tasks` reader for every consumer; cdx is right that
  execution APIs must not grow fake membership. gem's two real concerns are solved
  narrowly instead: (a) the freshness/walk scan gains one more exclusion — "has a live
  snoozed row in today's note" — exactly parallel to the existing Today-linked
  exclusion, in both the Rust scan and the ledger-tools mirror; (b) reconcile's
  daily-note exception treats a live snoozed row as "linked today" so a daily-note
  resident is not stripped back to `[ ]`.
- **Lane/freshness at snooze time:** cld/gem/cdx promote at snooze; grk promoted only at
  wake. Resolution: **promote and stamp at snooze.** Verified: Ctrl+Shift+Enter stamps
  `[fresh::]` precisely when it rewrites the task line Ready/Blocked → Next — snoozing
  is the same human commitment gesture, so it uses the same writer and gets the same
  stamp. This also makes the walk exclusion mostly redundant on day one (fresh = today),
  but the read-time exclusion is still required for hand-written rows and already-Next
  tasks with stale stamps. The background **wake writes no lane or freshness changes**
  (all five agree) except ensure-Next for a hand-written row — the same promotion any
  link gets. Wake never stamps fresh, never clears keeps, never drops dependencies,
  never writes `[unblocked::]`.
- **Plan budget:** cld/gem/cdx count on-clock snoozed links toward `max_links`;
  grk/mus exempt them. Resolution: **count them, with a visible breakdown**
  (`10/13 · 2 💤`). The loophole is concrete: five tasks snoozed to 19:00 would let the
  morning plan read `8/13` and silently explode to `over` at dinner. Off-clock snoozed
  rows stay uncapped, matching the existing off-clock exemption. This is the one
  genuine product-preference call — flagged for Bryan (§7).

### 4.4 Wake mechanism — **new cheap 5-minute tick step** (cld, grk, gem; over mus's reconcile and cdx's lock-bypassing pass)

mus's reconcile-owned wake inherits a 15-minute cadence and a whole-vault scan for a
one-file job — a 15:30 snooze waking at 15:45+ fails the use case. cdx's
run-lock-bypassing "fast wake pass" solves a problem the ops data says is small:
observed tick runs take 0–62 s on a 5-minute cadence, so the worst realistic starvation
is one missed slot. Resolution: a catalog step —

- name `snooze`, child `bob snooze wake -q -f json`, default cadence **5m**,
  `intake = false`, ceiling 1–2 m, the existing daily-note readiness gate, ordered
  **after `gcal`, before `tasks`** (fresh Events state for future event-anchored work;
  reconcile validates woken links on the same pass);
- **fast no-op path** (gem): read today's note lock-free; if no section or nothing due,
  exit without touching `bob_sync.lock` or the 2-second quiet period — near-zero cost on
  ~99 % of ticks;
- when a write is needed, apply one atomic, snapshot-checked, recovery-manifested write
  through the existing guarded writer; on contention return a deferred receipt and let
  the next tick retry;
- `bob tick -s` shows `snooze · next 19:00` via `next_due_at`.

**Latency contract (honest version, all reports):** the wake time is *not-before*, not
*at*. Wake lands 0–10 minutes late in practice and requires the Mac awake (tick is
Mac-only cron). Both stated use cases are "after X", so this is acceptable — provided
readers mark a past-time row as **due** before the write happens (amber pill in
Obsidian, `due · waking` in the Mac agenda), so a missed scheduler run is visible rather
than silent. Manual `bob snooze wake` (any host) and the Obsidian/capture early-wake
gestures cover the gap instantly when it matters.

### 4.5 Running-session placement — **never auto-wake into the running entry** (cld, grk, cdx; over gem's tail-append)

Lead-verified: on a plain `x` close, every unstruck plain link in the closing entry is
recorded **in progress** — started `[/]`, given a 🍅, carried. gem's tail-append
preserves `x1`/`x2` numbering but still plants a never-touched task into the close's
default outcome set, silently recording it as worked. Wake therefore places into the
capture type-placement chain **minus the running-first preference**: first untimed open
exact-type entry → first untimed open entry containing the type → new `() — TYPE`
placeholder at the next-up slot. An explicit *human* wake-now gesture may still join the
running session.

### 4.6 Midnight rollover — **no auto-carry** (cld, gem, mus, cdx; over grk's carry-forward)

grk's auto-carry silently re-commits yesterday's plan to a new day, which contradicts
the system-wide principle that Today is deliberately chosen (and cdx's warning against
granting old plans new commitments). Resolution: wake inspects **today's note only**.
Unwoken rows stay in yesterday's note as history. Because snoozing promoted to Next
(sticky), the task resurfaces in the normal review walk; the exclusion only applies to
*today's* snoozed rows, so suppression cannot outlive the plan day. Optional later:
cdx's explicit "missed from Monday" surfacing and a "N snoozes never woke yesterday"
lint, if stale rows prove common in practice.

### 4.7 Smaller calls

- **CLI noun:** `bob snooze` top-level (cld, gem, cdx) over grk's `bob task wake` —
  it is a daily-note queue, not a vault-wide task-line rewriter; bare `bob snooze` /
  `bob snooze list` is the read-only form per `cli_rules`; verbs `add`, `wake`, `drop`
  with the usual dry-run/format/help contract.
- **Capture token:** `z:<when>` (`z:1530`, `z:15:30`, `+45m`/`+2h` resolved to an
  absolute time at write) — unanimous among the three reports that proposed syntax;
  `s:` collision verified. Refused with teaching errors: past times ("link it now or use
  `s:1`"), cross-midnight, combination with `s:<N>` or `=` start, items without a link
  target. Existing-task items (`@route:id`) currently refuse every extra token and need
  one explicit grammar exception (grk). A plain `@route:id` on a snoozed task acts as
  **wake early**; `@route:id!` unlinks the snoozed row (lane stays, sticky).
- **Notification on wake:** ship it, configurable (cld's A5 over grk's dissent). The
  email-Dan failure mode is precisely "nothing signaled at 15:30";
  `desktop_notify.rs` already exists and the cost is a few lines. The Darwin
  `tick-finished` ping already refreshes the Mac agenda regardless.
- **The Dan example in v1:** gem's completion trick gives the ergonomics with zero
  dependency tracking — `z:` completions offer today's event **end times** ("15:30 ·
  after Yogi interview") resolved to a literal HHMM. True event-anchored wakes
  (`after [[#^event]]`, Google reschedules moving the wake) and `starts after` routing
  stay out of v1 as their own epics.
- **Naming:** reuse the word "Snoozed" (the `#hide` docs reserved the moon glyph for
  exactly this), but docs must lead with "later-today Task Links" and explicitly
  distinguish the Reading Board's date-based Snoozed lane and the project-frontmatter
  `snooze:` hold.

## 5. Requirement adjustments (explicitly called out)

These change or pin the task as written:

| # | Adjustment | Kind |
| --- | --- | --- |
| R1 | **Event Tasks are out of scope for v1.** The note's "canonical example" stays on the Events/MEET path; manually snoozing an event link is treated as a user edit gcal must respect. Event anchors are a possible v2. | Changes the stated example (unanimous) |
| R2 | **Same-day, one-shot times only.** Multi-day deferral stays `[scheduled::]`; decoupled from `^task-props-use-time`, and if that epic later adds datetimes, snooze does **not** migrate onto them (different job: Blocked vs Today-membership). | Scoping (unanimous) |
| R3 | **Snoozed is not Today until wake**, but snoozing promotes Ready → Next and stamps fresh like any link; the walk/review scan excludes tasks with a live snoozed row today; reconcile's daily-note exception treats a snoozed row as linked. | Clarification + addition |
| R4 | **On-clock snoozed links count toward `plan.max_links`** with a visible breakdown; off-clock stays uncapped. | Addition — Bryan's call (§7) |
| R5 | **Wake is mechanical and idempotent**: it re-runs the link guards (done/cancelled/already-linked/Blocked → drop or skip the row, report it), never stamps fresh, never touches the running session, preserves child-note subtrees, and retries safely on contention. | Addition |
| R6 | **`bob tick` wakes via a new cheap 5m `snooze` step**, not inside reconcile; wake time is a *not-before* bound (0–10 min late, Mac awake), and readers show **due** state before the write lands. | Refines "tick should be responsible" |
| R7 | **`## Snoozed` sits after `## Pomodoros`**, created on demand, deleted when empty, registered as a structural H2. | Pins an unspecified choice |
| R8 | **Gesture cleanup parity is mandatory in the same release as authoring**: release (Alt+N), complete, cancel, unlink, decay, roll, and Ctrl+Shift+M prune snoozed rows (one shared plugin helper covers most of this), or a released task gets revived by a timer. | Addition |
| R9 | **No auto-carry at midnight**; unwoken rows are history, lanes + review resurface the task. | Pins an unspecified choice |
| R10 | **Desktop notification on actual wake**, configurable. | Addition |

## 6. Recommended solution

**Build a same-day, link-level `## Snoozed` parking lot after the ledger, woken by a new
5-minute `bob tick` step through the existing guarded writer, with capture `z:` and
plugin/Mac surfaces following in phases.**

### Vault form

```markdown
## Pomodoros
- [ ] () — WRITE
	- [[sase_blog_drafts#^what-came-before]]

## Snoozed
- **1530** [[job#^email-dan-eod]]
- **1900** [[home#^fix-sink]]
	- grab the wrench from the garage first
```

### Wake algorithm (`bob snooze wake`, run by tick)

1. Lock-free read of today's note; exit immediately if nothing is due or prunable.
2. For every row (due or not): drop `resolved` rows (done/cancelled/struck/missing/
   ambiguous target) and `already_linked` rows (a live link under an open Pomodoro means
   the user woke it by hand) — reporting each.
3. For due rows (`HHMM ≤ now`, note-local time): skip still-Blocked targets (deps,
   project, future date, `#awaiting_reply`) — the row stays parked and retries, since
   reconcile would consume a freshly planted link to a Blocked task; otherwise ensure
   Next (hand-written rows) and move the link subtree into the first untimed open
   exact-type entry → untimed open containing-type entry → new `() — TYPE` placeholder
   at the next-up slot. Never the running entry.
4. Remove emptied rows and an empty heading; one atomic snapshot-checked write; deferred
   receipt on contention; notify per woken row; JSON reports `woken[]`, `dropped[]`
   (reasoned), `pending[]`, `next_wake_at`.

### Phases

1. **bob-cli core (useful on its own, hand-written rows work):** `src/native/snooze/`
   module (parse/write/plan), `bob snooze` CLI (`list`/`add`/`wake`/`drop`), tick
   `snooze` step, `is_structural_h2_key`, reconcile safety-net pruning + daily-note lane
   coverage, `bob plan` summary line (`💤 2 · next 15:30`), docs (`docs/snooze.md`,
   `docs/tick.md`, `docs/plan.md`, vault-format reference), conformance tests.
2. **Capture + agenda contract:** `z:<when>` grammar (spans, completions incl. event end
   times, existing-task exception, early-wake/unlink interplay), additive `snoozed[]`
   in `capture-pomodoros --tasks`, fold `min(wake_at)` into `refresh_at`, Rust budget
   breakdown.
3. **bob-plugins:** `planDeferredPomodoroLinkCleanup` learns `## Snoozed` (the single
   choke point covering release/close/cancel/decay/roll/move), link-presence "snoozed",
   walk-exclusion JS mirror with shared vectors, 💤 `15:30` task-line mark and plan
   chip, amber due-time pills, a snooze/wake gesture that shells out to
   `bob snooze add`/`wake` (one writer).
4. **Bob Mac Capture:** decode `snoozed` via `decodeIfPresent`, a dim "💤 Later today"
   band below Later folding farthest-first, `due · waking` highlight, `z:` span styling.
   macOS CI on the exact SHA per the linked-repo rule.
5. **Optional, after ~2 weeks of real use:** named times (`z:home` from
   `snooze.times`, stored resolved), event anchors or `gcal.snooze_lead_minutes`,
   missed-day surfacing/lint, `^ranked-task-links` interplay (a woken link plausibly
   ranks at the front of its destination queue).

### Key acceptance cases (distilled from cdx's fuller list)

1. A task snoozed to 15:30 is absent from `=`/`x` lineups and TODAY at 15:29, keeps its
   lane and notes, doesn't walk in `]s`, and counts in the budget breakdown.
2. First eligible wake after 15:30 moves it exactly once into an untimed matching entry;
   a second wake is a no-op; a 15:40 tick catches a 15:30 row (no minute-window loss).
3. A running-only destination, busy vault, or absent note yields a visible pending/due
   state — never a write into the running session, never a lost row.
4. Complete/cancel/release/unlink/move before wake prunes the row; wake never revives
   them; a dependency added while asleep keeps the row parked.
5. Yesterday's unwoken row never wakes into today; the task still resurfaces via lanes
   and review; deleting any cache loses nothing (Markdown is authoritative).
6. Event sync, MEET filing, schedules, Gmail holds, successor offers, and close
   numbering are byte-for-byte unaffected.

### Memory follow-through

The implementing plan should propose (via the memory-write flow, default-off unless
Bryan opts in): a glossary strand **Snoozed Task Link**, and a decision record roughly
*"Snoozed Task Links wait after the ledger and wake through tick"* — covering not-Today
semantics, the budget call, and the Event-Task exclusion, since this deliberately
*amends the surroundings of* `today-is-read-from-the-ledger` without changing Today
itself.

## 7. Open questions for Bryan

1. **Budget (R4):** count on-clock snoozed links toward `max_links`? Recommended yes
   (prevents the 19:00 blowout); grk/mus preferred exempting the parking lot.
2. **Section position (R7):** after `## Pomodoros` (recommended, zero anchor changes) or
   between Events and Pomodoros for the timeline reading (costs the gcal anchor change)?
3. **Wake of hand-written Ready rows:** promote to Next at wake (recommended — the row
   is an explicit plan) or leave Ready?
4. **Notification default** on/off, and the Obsidian snooze keymap / Task Card slot.
5. Is the `z:` completion-with-event-end-times enough for the "after the meeting" case
   for now, or should event anchors / `starts after` integration be pulled forward?

## 8. Provenance

Consolidated from five independent reports, each moved beside this file
(`snoozed_task_links__{cdx,cld,grk,mus,gem}.md`; grk's two figures travel with it):

- **cdx** — reliability/recovery depth: due-vs-placed honesty, idempotency, identity
  resolution, acceptance-test rigor; argued the planned-today union (adopted only as the
  narrow walk exclusion + budget count).
- **cld** — strongest codebase archaeology (plugin boundary copies, the single cleanup
  helper, cron run durations, `#hide` glyph reservation, `email-dan-eod` forensics);
  grouped-row format not adopted; stamp-fresh-at-snooze adopted.
- **grk** — routing clarity (Events/`starts after`/`scheduled`/snooze each keep their
  job), structural-H2 registry, existing-task grammar exception; auto-carry rollover and
  `bob task wake` naming not adopted.
- **mus** — the ten unanswered-questions framing, date-only `scheduled` evidence,
  ref-board naming caution; reconcile-owned wake not adopted (latency), lint vocabulary
  adopted.
- **gem** — `s:` collision discovery, fast no-op tick path, `refresh_at` integration,
  R9 daily-note trap, event-end-time completions, vault pain evidence; Snoozed-∈-Today
  and running-session tail-append not adopted.

Lead verification on bob-cli `5ab392a1` (this workspace): tick catalog and run-lock,
`parse_schedule_token`, plain-`x` close outcomes, freshness stamping rules,
`pomodoros_section_range`, gcal Events insertion anchor, `is_structural_h2_key`,
off-clock budget exemption, daily-note H2 structure (`~/bob/2026/202611{20,24,25}.md`),
and the live task text (`~/bob/bob.md:112`).
