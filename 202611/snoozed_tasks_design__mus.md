# Snoozed tasks: design research (`mus`)

> **Request:** implement a modified version of the snoozed-task-links design —
> same-day parking of today's tasks until a clock time, with new marks on the
> task definition and on woken links, exclusion from `plan.max_links`, a snooze
> keymap, a wake notification, and a new glossary term. Event tasks are out of
> scope. Lead the design: intuitive, reliable, beautiful.
>
> **Verdict: build it, narrowed.** The feature fills a real gap — *"committed
> to today, but not actionable until HH:MM"* — that no current mechanism
> expresses. I independently agree with the prior consolidated design's core
> shape (`## Snoozed` after `## Pomodoros`, one-line `**HHMM**` rows, `bob tick`
> wakes, same-day only, no auto-carry), with five adjustments below (A1–A5),
> the largest being the requested `max_links` exclusion plus a
> projected-budget guardrail so the exclusion cannot silently blow up the day.

## 1. Is this a good idea?

Yes. The gap is the missing middle granularity:

| Mechanism | Granularity | In Today? | Resurfaces itself? |
| --- | --- | --- | --- |
| `[scheduled::]` | day | no (Blocked until date) | yes, as TICKLER |
| Task Link under open Pomodoro | day (from 06:00) | yes, all day | n/a |
| `() — LATER` placeholder | none | yes (noise all day) | no |
| Event Task span | minute | time-aware | yes (clock) |
| **Snoozed link** | **minute, today** | **not until wake** | **yes (tick)** |

The `email-Dan-after-the-3:30-meeting` case is the proof: at 09:00 the task is
a real commitment but unactionable noise in every `=`/`x` lineup; at 15:30
nothing today signals it became doable. `[scheduled::]` cannot help (it is
date-only — a datetime there is a repair-flag error — and it derives Blocked,
which reconcile consumes links over). `LATER` placeholders count as Today all
day. Event Tasks already solve this for meetings via spans and the Mac
calendar band, which is exactly why excluding them (below) is correct rather
than a loss.

**Alternatives considered and rejected:** task-line wake timestamps (breaks
sticky lanes — a timestamped line would derive Blocked and destroy `[*]`/`[/]`
— plus Dataview date parsing and the Gmail-hold stack); inline wake markers on
ledger links (every Today/budget/lineup reader must learn them); a timed
`SNOOZED` placeholder Pomodoro (is Today, mangles entry grammar); hidden JSONL
state as the membership source (violates the visible-ledger philosophy);
notification-only with no parking (doesn't fix the agenda). The daily-note
`## Snoozed` queue is the only option that is hand-editable, costs zero
task-line schema change, and degrades safely (old parsers ignore an unknown H2
rather than working the task early).

**Honest costs:** (1) wake latency is *not-before*, not *at* — 0–10 minutes
late in practice, and never while the Mac sleeps (tick is Mac-only cron every
5 minutes); (2) every new mark is new display code in three surfaces
(Obsidian Live Preview, Reading view, Mac Capture); (3) the `max_links`
exclusion you requested opens a real budget loophole — addressed in §4, not
ignored.

## 2. Event tasks are out of scope — agreed, for structural reasons

I verified the load-bearing facts: synced meetings file under `() — MEET`
with phase-of-day filing, timed closes already protect `not_started` events,
off-clock events are already `max_links`-exempt, and gcal creates `## Events`
immediately above `## Pomodoros` (`src/native/gcal/plan.rs:2313`). Routing
event rows through `## Snoozed` would cut across all of that, and you cannot
wake a 15:00 meeting *at* 15:00 — you need lead time, which a clock row cannot
express. Keep the boundary crisp: **a snooze gesture whose target resolves to
an Event Task row is refused with a teaching error** ("event tasks already
wake by their span — see the meeting row"), and a manually hand-written
snoozed row pointing at an event row is treated as a user edit that gcal
continues to own. Event-end-time *completions* for `z:` ("15:30 · after Yogi
interview") give the Dan ergonomics with zero dependency tracking — that is
the right v1 substitute for "after that meeting".

## 3. Task-definition mark: 💤 plus the wake time

**Design.** A snoozed-but-not-yet-woken task keeps its lane and wears, in
place of the 🍅 Today mark, a display-only mark on its definition line:

```text
before: - [*] #task Email Dan the Yogi updates ^email-dan-eod
after:  - [*] ⌗ 💤 15:30 Email Dan the Yogi updates ^email-dan-eod
```

Rules (mirroring `docs/today-marks.md`, which I read as the contract to
extend): the mark appears iff the task is open, is a real `#task` line with a
unique block id, the id has a live snoozed row in **today's** note, and it is
*not* in Today (a hand-woken task that is both linked and still has its row
shows 🍅 — Today wins, and the stale row is pruned as `already_linked`). The
time shown is the row's wake-at time (`min` across duplicate rows; duplicates
are otherwise normalized by the writer). A row whose time has passed but tick
has not run yet renders **amber/bold** (`💤 15:30 · due`) — this is the honest
latency signal from §1, and it must exist in all three surfaces so a missed
scheduler run reads as "due, waking" rather than silent.

Why 💤 and not a clock emoji plus time: `docs/task-tag-marks.md:602`
explicitly reserved the moon/snooze glyph for exactly this ("implies
time-based snooze"), so the vocabulary is already waiting; 🍅 stays reserved
for "workable now", 💤 means "committed, not yet". The time is mandatory, not
decorative — a bare 💤 re-creates the ambiguity this feature exists to kill.

## 4. Woken links show the WAKE time — and snoozed links are out of `max_links` with a projected guardrail

**Decision on your §3 question: show the wake time, not the snooze time.**
When you look at a ledger row at 16:00, the question you are answering is
*"when did this become workable?"* — the wake time answers it; the moment you
parked it that morning is trivia. (In the same-day design the row's `HHMM` is
the *scheduled* wake anyway, so "snooze time" would be ambiguous between the
parking moment and the scheduled time.) Recommended form, display-only, on the
ledger row for the rest of the wake day:

```text
- [[job#^email-dan-eod]]                          →  (ledger source, unchanged)
  renders:  job > ^email-dan-eod  ⏰ woke 15:32    (pill; tooltip: due 15:30)
```

**Provenance (adjustment A1 — called out).** Once the woken link moves into
the ledger, the source row is gone, so the pill needs same-day provenance. I
recommend a day-scoped sidecar written atomically by the waker (e.g.
`woken-YYYYMMDD.json` under Bob's state dir: `{block_id: {due, woke_at}}`),
read by `bob snooze list -f json` as `woken_today[]` and consumed by agenda
and plugin pills. It is pill-only state: ledger membership stays canonical,
a missing sidecar degrades to no pill (never to a wrong pill), and
yesterday's file is ignored. The alternative — writing provenance into the
ledger row (alias, suffix) — breaks the strict one-link row grammar every
lineup parser shares, so it is rejected.

**`max_links` (adjustment A2 — called out).** Implementing your requirement as
written: on-clock snoozed rows do **not** increment the `links.count` that
drives `over`. But the loophole is concrete — five tasks snoozed to 19:00
let the morning plan read `8/13` and silently explode to `over` at dinner.
So the exclusion ships with a **projected-budget guardrail**: `bob plan`
reports `8/13 · +2 💤 → 10/13`, and a lint fires when
`active + snoozed > cap` ("projected over at 19:00 — 2 💤 wake into a full
plan"). Snoozed rows never push the plan to `over` by themselves; they only
warn. Off-clock snoozed rows stay fully uncapped, matching the existing
off-clock exemption (`docs/plan.md:114`). This honors your requirement while
keeping the plan truthful about the evening it already committed to.

## 5. Snoozing from a task link: one keymap, one writer

**Recommended: `Alt+Z`** on a ledger task-link row *or* on a task definition
line. I could not fully audit bob-plugins keymaps from this checkout, so the
implementing plan must collision-check `Alt+Z` (and fallback `Ctrl+Shift+Z`)
against the hotkey registry and name the fallback in the plan — but `Alt+Z`
is the right shape: single chord, `Z` for snooze, Alt-family like its sibling
`Alt+N` (release) and `Alt+F` (keep), easy to discover beside them.

UX flow (all surfaces shell out to one writer, `bob snooze add`):

1. Press `Alt+Z` on a link row / task line → time prompt with smart default:
   next half-hour, plus `z:` completions offering today's remaining event end
   times ("15:30 · after Yogi interview").
2. `Enter` writes (or updates in place — one live row per task per day) a
   `- **HHMM** [[note#^id]]` row in `## Snoozed`, promoting Ready → Next and
   stamping `[fresh::]` exactly like Ctrl+Shift+Enter; `Esc`/`q`/`Ctrl+[`
   backs out per the panel convention.
3. Errors teach: past times ("link it now with Ctrl+Shift+Enter, or use a
   future time"), cross-midnight ("same-day only — use `[scheduled::]` for
   another day"), event targets (refused, §2).

Two companion gestures, no new chords: a plain link gesture on a snoozed task
(`@route:id` / Ctrl+Shift+Enter) acts as **early wake** (moves the link now,
prunes the row); `@route:id!` (or the unlink gesture) drops the snoozed row
and leaves the lane sticky. These fall out of the existing grammar and need
only the one documented exception for already-snoozed targets.

## 6. Wake notification: banner + sound, backed by in-app surfaces

You asked for maximum seen-probability with auto-dismiss. No single channel
does both, so the design layers them — each layer I verified exists:

1. **Desktop banner with sound (the interrupt).** Extend the existing
   best-effort transport (`src/native/desktop_notify.rs` — osascript on
   macOS, `notify-send` on Linux) with a `snooze` title and per-woken-row
   body: `"Ready: Email Dan the Yogi updates — due 15:30, woken 15:32 → WRITE"`.
   On macOS request a sound (`sound name "Glass"`); banners auto-dismiss by
   OS design, satisfying "goes away on its own". Config `snooze.notify`
   (default on) and `BOB_VAULT_SYNC_NOTIFY`-style opt-out; failures never
   affect exit codes or JSON, per the transport's contract.
2. **Mac agenda refresh (the persistent-but-quiet layer).** The Darwin
   `tick-finished` ping already refreshes the idle agenda — the woken task
   appears in its entry with the ⏰ pill from §4, so a user who missed the
   banner still meets the task in the surface they already check. No new
   daemon, no polling.
3. **Obsidian amber due-state (the pre-write layer).** From §3: a past-time
   row reads `due · waking` before tick lands the write, so the arrival is
   never a silent ledger mutation.

Why not richer: a `bob pomodoro notify`-style blocking loop would duplicate
tick's scheduler; a persistent-until-acknowledged alert violates your
auto-dismiss requirement; sound-only or banner-only halves the seen-rate
(banner missed when away, agenda missed when not looking). The three layers
fail independently, which is the reliability argument: any two can break and
the wake is still both announced and visible.

## 7. Glossary term (draft, ready to propose via the memory-write flow)

> ### Snoozed Task {#snoozed-task}
>
> *Aliases: snoozed task link.*
>
> An open, non-event task committed to **today but not actionable until a
> clock time**. It has a live one-line row (`- **HHMM** [[note#^id]]`) in
> today's daily-note `## Snoozed` section and no dedicated Task Link under an
> open Pomodoro. Until its wake time it is not [Today](#today): it wears
> 💤 HH:MM on its definition line instead of 🍅, is excluded from the `]s`
> review walk like Today-linked rows, and does not count toward
> `plan.max_links` (the plan shows it as projected load). At or after HH:MM,
> `bob tick`'s snooze step moves the link into an untimed open Pomodoro
> entry — never the running entry — where it becomes Today (🍅) and wears a
> same-day ⏰ woke-HH:MM pill. Snoozing promotes Ready → Next and stamps
> freshness like any link; waking never stamps, never touches the running
> session, and never revives released or completed tasks. Same-day only:
> unwoken rows stay in yesterday's note as history, and multi-day deferral is
> `[scheduled::]`. Not an [Event Task](#event-task) (which wakes by its
> meeting span), not a Reading-Board Snoozed row, and not a project
> frontmatter `snooze:` hold. See `docs/snooze.md`.

## 8. Core mechanics (independently verified — agreement where earned)

- **Vault form:** `## Snoozed` after `## Pomodoros`, one-line rows
  `- **HHMM** [[note#^id]]` with link-note subtrees as ordinary children. I
  verified recent daily notes end at `## Pomodoros` and `Snoozed` is absent
  from `is_structural_h2_key` (`src/native/capture_drawers.rs:606`) — the
  after-placement needs zero changes to the gcal Events anchor or the
  ledger-range rule, so it wins over a timeline-sorted between-placement.
  Register `Snoozed` in `is_structural_h2_key` either way.
- **Pre-wake semantics:** snoozed is **not Today** until wake (Today membership
  — open tasks with a dedicated link under open Pomodoros, computed at read
  time in `src/native/plan_budget/today.rs` — must not gain a fake second
  source). Snoozing promotes Ready → Next and stamps `[fresh::]` like any
  link gesture; the freshness/review scan gains one parallel exclusion ("has a
  live snoozed row today"), mirroring the existing Today-linked exclusion.
- **Wake:** a new cheap `bob tick` `snooze` step (default 5m, ordered after
  `gcal`, before `tasks`; I verified the catalog at
  `src/native/tick/catalog.rs:115` and the readiness-gate pattern) running
  `bob snooze wake`: lock-free fast no-op when nothing is due; otherwise one
  atomic snapshot-checked write through the existing guarded writer. Wake
  re-runs the link guards (done/cancelled/already-linked/Blocked → drop or
  skip with reason), never stamps freshness, never lands in the running
  entry (a plain `x` close records every unstruck plain link as worked —
  verified in `docs/capture.md` — so running-entry placement would falsely
  record untouched tasks), and retries on contention.
- **Boundaries:** same-day only, no auto-carry (yesterday's rows are history;
  the sticky Next lane resurfaces the task through normal review);
  gesture-cleanup parity in the same release as authoring (release, close,
  cancel, unlink, decay, roll, move must prune snoozed rows through one
  shared helper, or a timer revives a released task); capture `z:<when>`
  token (`s:` already means day-offset — verified in markers — so `z:` is
  free); additive `snoozed[]` in `capture-pomodoros --tasks` with
  `min(wake_at)` folded into `refresh_at`.

## 9. Adjustments to your requirements (explicit list)

| # | Adjustment | Why |
| --- | --- | --- |
| A1 | Woken-link ⏰ pill needs a day-scoped sidecar (`woken-YYYYMMDD.json`); ledger rows stay grammar-clean | Provenance is gone after the move; writing it into the row breaks every lineup parser. Pill-only state, degrades to no pill. |
| A2 | Snoozed excluded from `max_links` **but** plan shows projected load + lint when `active + snoozed > cap` | Your requirement, honored — plus a guardrail against the silent 19:00 blowout the pure exclusion creates. |
| A3 | `Alt+Z` keymap ships only after a bob-plugins hotkey collision audit (fallback `Ctrl+Shift+Z` named in the plan) | I could not audit the plugin registry from this checkout; naming an unchecked chord would be a guess. |
| A4 | Notification defaults to banner **with sound**, configurable off | Sound is the cheapest seen-rate multiplier and stays auto-dismissing; silent-by-default would reproduce the exact failure (nothing signaled at 15:30) that motivates the feature. |
| A5 | Glossary entry documents the two *other* "snoozed" meanings as not-this | `docs/ref.md` (Reading-Board Snoozed lane) and project-frontmatter `snooze:` already use the word; without the disambiguation the term will confuse within a month. |

## 10. Recommended solution

Build the same-day `## Snoozed` parking lot after the ledger, woken by a new
5-minute `bob tick` step through the existing guarded writer, with the
💤/⏰ mark pair, the `Alt+Z` gesture, banner+sound wake notification, and
capture/agenda surfaces following in phases:

1. **bob-cli core** — `snooze` module (parse/write/plan), `bob snooze`
   (`list`/`add`/`wake`/`drop`), tick step, structural-H2 registration,
   reconcile safety-net, `bob plan` projected line (`8/13 · +2 💤 → 10/13`),
   `docs/snooze.md` + `docs/tick.md` + `docs/plan.md` updates, conformance
   tests. Hand-written rows work from day one.
2. **Marks** — 💤 HH:MM task-definition mark (amber when due) in Live
   Preview + Reading view; ⏰ woke-HH:MM ledger pill from the day sidecar;
   `today-marks`/`task-link-marks` conformance vectors extended.
3. **Capture + agenda** — `z:<when>` grammar with event-end-time completions,
   early-wake/unlink interplay, additive `snoozed[]` + `refresh_at` fold,
   Rust budget projection.
4. **Gestures + notify** — `Alt+Z` (audited), cleanup-helper parity for all
   release paths, banner+sound wake notification with config, Mac agenda
   dim "💤 Later today" band.
5. **After ~2 weeks of real use** — named times, missed-day surfacing lint,
   `starts-after` interplay as its own epic. Not v1.

Key acceptance cases: snoozed-at-15:30 is absent from lineups at 15:29 and
keeps its lane; first eligible wake moves it exactly once into an untimed
matching entry and a second wake is a no-op; complete/cancel/release/unlink
before wake prunes the row and wake never revives it; a dependency added
while asleep keeps the row parked; a running-only destination yields a
visible due state, never a write into the running session; yesterday's row
never wakes; deleting the sidecar loses only pills; event sync, MEET filing,
schedules, Gmail holds, and close numbering are byte-for-byte unaffected.

## Verified ground truth (this report's load-bearing claims)

- Today = open tasks with a dedicated link under today's open Pomodoros,
  read-time computed (`src/native/plan_budget/today.rs`,
  `docs/today-marks.md`, `docs/plan.md`).
- Plain-`x` close records every unstruck plain link in the closing entry as
  worked (`docs/capture.md` close-outcomes) — hence never-wake-into-running.
- `[scheduled::]` is date-only; datetime is a repair flag; future dates
  derive Blocked which consumes links (`docs/date-marks.md`,
  `docs/task-status-hooks.md`).
- `s:<digits>` is a pure day offset; `z:` is unused
  (`src/native/capture_language/markers.rs`).
- `Snoozed` is not a structural H2; registry is `is_structural_h2_key`
  (`src/native/capture_drawers.rs:606`).
- Off-clock links are `max_links`-exempt; `over` = on-clock links > cap
  (`docs/plan.md:114`, `src/native/plan_budget/mod.rs`).
- Tick catalog order/steps/cadences (`src/native/tick/catalog.rs:115`,
  `docs/tick.md`); shared best-effort notify transport
  (`src/native/desktop_notify.rs`); Darwin `tick-finished` ping
  (`src/native/darwin_notify.rs`).
- 🍅 Today mark is display-only on definition lines (`docs/today-marks.md`);
  ledger rows wear 🍅/◐ slots, not rings (`docs/task-link-marks.md`); the
  moon glyph was reserved for time-based snooze
  (`docs/task-tag-marks.md:602`); "Snoozed" already names a Reading-Board
  lane and a project-frontmatter hold (`docs/ref.md`).
