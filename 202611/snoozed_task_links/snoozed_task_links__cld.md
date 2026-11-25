---
title: "Snoozed Task Links: a same-day, not-before deferral that bob tick wakes"
task: "bob#^snoozed-tasks"
researcher: cld
date: 2026-11-25
---

# Snoozed Task Links (`^snoozed-tasks`)

## TL;DR

- **Verdict: build it, keep it narrow.** A snoozed Task Link is
  **a deferred link gesture with a not-before time, valid for today
  only**. It fills a real gap:
  - **Today** has no time of day.
  - **`[scheduled::]`** only says which day, and it Blocks the task.
  - **Event Tasks** are time-aware, but only for calendar rows.
- **Your two notes are both right**: a `## Snoozed` H2 in the daily
  note, and `bob tick` doing the waking. Because the section sits
  *outside* the `## Pomodoros` ledger, every Today, budget, start and
  close reader ignores it without any change. All four JS boundary
  finders and the Rust `pomodoros_section_range` stop at the next `## `
  heading.
- **Seven adjustments** I recommend (details in
  [§6](#6-requirement-adjustments-called-out)):
  - **A1.** Event Tasks are **not** moved into Snoozed. They already
    snooze by their own time span. Instead, let a snooze be anchored to
    "after this meeting" (later phase).
  - **A2.** A woken link must **never** land in the running session. It
    goes into the next-up untimed placeholder.
  - **A3.** Snoozing is a commitment to today:
    - It raises Ready to Next and stamps fresh, like any link.
    - Its on-clock links count toward the plan budget.
    - It is still **not** Today until it wakes.
  - **A4.** Wake re-runs the link guards: done, cancelled, already
    linked, Blocked. Release, complete and cancel prune the snoozed row.
  - **A5.** Wake sends a desktop notification. Being reminded at the
    right moment is half the value.
  - **A6.** Same day only. Deferring across days stays
    `[scheduled::]`.
  - **A7.** We accept a wake that is 0–5 minutes late and needs the Mac
    to be awake. Readers show a row as "due" before tick moves it.
- **Phasing.** Phase 1 ships the format, a `bob snooze` CLI and a tick
  step. Hand-written rows work from day one. Later phases add:
  - the capture token `z:<when>` and the Mac "💤 Later today" fold;
  - plugin pruning, marks and the budget count;
  - event anchors and named times (`home`), if still wanted.

---

## 1. The request

From `~/bob/bob.md` (`^snoozed-tasks`, `[/]`, created 2026-11-22):

> - Use new "Snoozed" H2 section in daily files for this!
> - The `bob tick` command should be responsible for waking tasks!
> - I sometimes have tasks that I know I need to do today, but that can't be done
>   until after a certain time. The canonical example of this is event tasks, but there
>   are plenty of other examples:
>   - email Dan on Monday with updates on the Yogi interview, which couldn't happen
>     until after that meeting (after 3:30 PM);
>   - tasks that can only be done at home (after ~7 PM).

## 2. What the system does today (facts)

### 2.1 Today, the ledger, lanes

- **Today** is open tasks with a dedicated Task Link under today's
  **open** Pomodoros, computed when read. It is never a tag, a field or
  a path filter.
  - Sources: `docs/plan.md` §Today, Rust `plan_budget/today.rs:111`
    (`today_tasks`), JS `bob-ledger-tools/src/060-today.js`.
  - Decision record: `decisions:today-is-read-from-the-ledger`.
- **The ledger** runs from `## Pomodoros…` to the next `## ` heading
  (`pomodoro.rs:582` `pomodoros_section_range`). Every plugin has its
  own copy of the same boundary rule:
  - `bob-ledger-tools/src/020…:395`
  - `block-id-prompt/src/040…:115`
  - `task-status-cycler/src/060…:168`
  - `bob-navigation-hotkeys/src/140…:337`
- **Sticky lanes** (`decisions:task-lanes-are-sticky`):
  - Linking raises Ready or Blocked to Next.
  - Unlinking never lowers a lane. Only release (Alt+N) does.
  - A Blocked task keeps no Task Link under today's open Pomodoros;
    reconcile removes it ("consumes" the link).
- **`[scheduled::]` is date-only** and makes a task Blocked `[?]`.
  - The Gmail reply wait is built on it
    (`decisions:gmail-reply-wait-is-a-tagged-hold`). That record
    rejected a separate wait field and a `[w]` checkbox because they
    would split how Blocked is derived.
  - Bryan has an open task to move date fields to times
    (`^task-props-use-time`).

### 2.2 Event Tasks already have time-of-day semantics

The `**HHMM-HHMM**` span drives several things:

- Sync files each meeting by its phase: past, running or future
  (`decisions:synced-meetings-link-by-phase`).
- MEET starts follow the calendar (`docs/capture.md`
  §MEET starts follow the calendar).
- Closes classify Event Task links by the clock. A meeting that has not
  started is kept out of wildcard completion and parking
  (`decisions:event-task-links-close-by-the-clock`).
- Display: event link-time pills (`docs/event-link-times.md`), the
  plugin's future/running/past state (`291-plugin-gcal-events.js:83`),
  and the Mac agenda's event chips.

**So Event Tasks are effectively snoozed by their span already.** In
today's note, `## Pomodoros` holds `() — MEET` with both
`[[#^swings]]` (0900) and `[[#^movie-lion-king]]` (1900). Every
surface that matters knows the movie is a 19:00 thing.

### 2.3 `bob tick`

- **Step catalog.** `src/native/tick/catalog.rs` is a fixed list:
  `gcal, gmail, gkeep, refs, projects, tasks`. Each step is a child
  `bob …` command with a cadence (minimum `5m`), a readiness gate and a
  JSON adapter. Adding a step is a small, well-trodden change.
- **Live schedule** (`cronctl list`, `cronctl logs bob-tick --machine mac`):
  - `bob-tick` runs `*/5` **on the Mac only**.
  - Most runs take 0–1 s; heavier ones take 17–62 s.
  - A second run while one is still in flight exits with
    "already running".
  - The Mac skips cron while it sleeps.

### 2.4 Who writes Task Links, and where they look

**bob-cli:**

- The capture link planners check the whole daily note for duplicates:
  `pomodoro_link.rs:47` uses `original_day.contains(&block_link)`.
  That check is only for new tasks, so it is harmless here.
- Type placement for an existing-task link
  (`capture/task_theme.rs:1051 placement_for_task`) picks, in order:
  1. the **running** exact-type entry;
  2. else the first open exact-type entry;
  3. else the first open entry whose name contains the type;
  4. else a new `() — TYPE` placeholder.

**bob-plugins** (Explore survey; paths under `plugins/`):

- **Every link writer and cleanup is JS and scoped to `## Pomodoros`.**
  - Ctrl+Shift+Enter: `block-id-prompt/src/120-plugin-pomodoro-links.js`.
    Its "already linked" check (`planAllOpenPomodoroLinkCleanup`) only
    looks at Pomodoros.
  - Successor and pull-in placement: `task-status-cycler/src/087…`.
  - Release, close, cancel, decay, roll and Ctrl+Shift+M all prune
    through one shared helper: `planDeferredPomodoroLinkCleanup`
    (`bob-navigation-hotkeys/src/160-pomodoro-reorder.js:538`).
  - **Consequence:** these gestures would neither see nor prune a
    `## Snoozed` row.
- **Whole-note scanners** are harmless or helpful:
  - task-move link rewrites (`250-task-move.js:245`), so a moved task
    keeps a working snoozed link;
  - backlink indexes;
  - task-link rings (`148-task-link-marks.js:718`). These would draw
    prose-style rings on snoozed links, which is only cosmetic.
- **The only existing "snooze" is the Reading Board's 💤 lane**, which
  works by date (`243-plugin-reading-board-render.js`). Separately,
  `docs/task-tag-marks.md` §`#hide` **rejected a moon/snooze glyph
  because it "implies time-based snooze"**. That glyph is free, and
  this feature should take it.
- No plugin creates daily-note H2s. The template
  (`~/bob/_templates/daily.md`) has only the preamble, `bob-plan` and
  `## Pomodoros`. gcal adds `## Events` above Pomodoros.

### 2.5 Evidence the need is real

- **`job#^email-dan-eod` ("Email Dan by EoD!")** — this is the Monday
  example itself:
  - Created 2026-11-23, linked under `() — WRITE` among four blog
    drafts.
  - The interview it depended on ran **1500-1530**.
  - The link stayed under WRITE all Monday and was carried, still
    open, into Tuesday's `() — WRITE`.
  - It was cancelled on 2026-11-25: "He already called me yesterday."
  - I can't prove a snooze would have changed the outcome. Still, the
    plan offered no signal at 15:30 that it had just become doable.
- **`plan.inventory_labels: [LATER, MISC, NEW FEATURES]`** in
  `~/.config/bob/config.yml`, and `() — LATER` placeholders in
  September notes (e.g. `2026/20260929.md`). Bryan has used an untimed
  "later" bucket before. Snooze is the timed, self-emptying version of
  it.

## 3. Critique — is this a good idea?

**Yes, with a narrow scope.** Reasons:

1. **It is the missing middle granularity.**

   | Mechanism | Granularity | Blocks the task? | Today? | Resurfaces itself? |
   | --- | --- | --- | --- | --- |
   | `[scheduled::]` | day | yes (`[?]`) | no (Blocked links are consumed) | yes (TICKLER) |
   | Task Link in open Pomodoro | day | no | yes | n/a |
   | `() — LATER` inventory placeholder | none | no | **yes** (noise) | no |
   | Event Task span | minute | no | yes, but time-aware | yes (by clock) |
   | **Snoozed link** | **minute, today** | **no** | **not until wake** | **yes (tick)** |

2. **It isolates well.** Putting it in a separate H2 means the hard
   contracts don't change: Today, the budget, `=` start lineups, `x`
   close numbering, type agreement, reconcile. That matters in a
   codebase this size (~1.27 M Rust lines, 77 decision records).
3. **It is hand-writable markdown.** Bryan can type a row himself in
   Obsidian on any device, and the Mac wakes it. Phase 1 is useful with
   no new keymap.

**Concerns, and how to handle them:**

- **A third "today-ish" state** (Today, Next, now Snoozed) adds
  cognitive load and surfaces to keep in sync. *Handle it* by keeping
  Snoozed out of Today, out of the walk tiers and out of the lane caps.
  It is a staging area, not a lane.
- **Reliability.** Wake depends on the Mac's `*/5` cron. Waking at 19:00
  needs the Mac awake around 19:00. *Handle it* by:
  - treating the time as "not before", so a late wake is fine;
  - having readers show a row as **due** once its time has passed,
    even before tick moves it;
  - having `bob tick -s` show the next wake.
- **Another automated writer on the most-edited file**, which already
  produces `_conflicts/` copies. Wake writes only when something is
  due, a few times a day, under the same vault lock and snapshot check
  as capture. That adds little to what gcal and reconcile already do.
- **Two gaps between gestures and snoozed rows.** Plugin gestures don't
  see the rows, so release or cancel before wake could later revive a
  link. Ctrl+Shift+Enter could also create a duplicate. *Handle it* in
  two ways:
  - wake re-checks every row;
  - the one shared plugin cleanup helper learns about `## Snoozed`.
- **Scope creep** into reminders, contexts or multi-day snoozes.
  *Handle it* by deferring those (adjustments A6 and A7; §8 Phase 4).

**Would I take a different approach?** I considered five alternatives.
All are worse:

| Alternative | Why not |
| --- | --- |
| **Inline marker on the ledger link** (`- [[job#^x]] 💤1530`) | Breaks the dedicated-link shape, so it drops out of Today. But the budget still counts indented prose. Every Rust, JS and Mac reader would have to learn the marker. |
| **Timed placeholder Pomodoro** (`- [ ] (@1530) — WRITE`) | Elegant, and needs no move. But it changes the Pomodoro entry grammar parsed in ≥5 places. It must not look "running". It mixes up session timing with task deferral, and it would count as Today. |
| **A time on the task** (`[snooze:: 15:30]`, or datetime `[scheduled::]`) | Writes task lines. A time-scheduled task is Blocked, and Blocked tasks lose their Today links. Fine for **multi-day** deferral once `^task-props-use-time` lands, wrong for "today, later". |
| **Purely derived wake** (readers treat a past-time snoozed row as Today, no move) | Wakes on time with no writer. But Today would span two sections, so every Pomodoros-scoped writer (start, close, Ctrl+Shift+M, reconcile) would also need to read `## Snoozed`. Too wide a change. |
| **No new feature: a `starts after` relation to the meeting** | Already works for the Dan example: closing the MEET *offers* the email task. But it only fires on a managed close gesture, does nothing for "after 19:00", and gives no reminder. A good complement, not a replacement. |

## 4. Recommended design

### 4.1 Vault format

`## Snoozed` sits **immediately above `## Pomodoros`** (below `## Events`
when present). Writers create it on demand and remove it when it empties.
It holds column-0 **wake rows** with dedicated Task Link children, the
same parent/child shape as the ledger:

```markdown
## Events
- [x] #task **1500-1530** Bryan Bugyi and Derrick Blakely … ^bryan-bugyi-derrick

## Snoozed

- **1530** · after the Yogi interview
	- [[job#^email-dan-eod]]
- **1900** · home
	- [[home#^fix-sink]]
		- grab the wrench from the garage first

## Pomodoros
- [ ] () — WRITE
	- [[sase_blog_drafts#^what-came-before]]
```

**Rules:**

- **Wake row:** `- **HHMM**`, optionally followed by ` · <free label>`.
  - Local wall-clock time, read with the same timezone resolution as
    Event spans.
  - No checkbox, so the Tasks plugin never treats it as a task.
- **Children:** a direct child bullet whose body is exactly one
  `[[target#^id]]` (or `![[…]]`) is a snoozed link. This is the same
  test as `list_queued_links` (`capture_pomodoro_start.rs:92`), so that
  parser can be reused. A link's nested sub-bullets travel with it when
  it wakes.
- **Grouping** by wake row lets several links share a time. The label
  is display-only.
- **Placement.** Above `## Pomodoros` reads as a timeline: calendar,
  then things waiting for later, then the plan. gcal's "insert a
  missing `## Events` above Pomodoros" must learn to go above
  `## Snoozed`. This is a small check item.
- **Reserved, not implemented in Phase 1:** event anchors, where the
  label is `after [[#^event-id]]` (Phase 4).

**Why grouped and not one line per link** (`- **1530** [[job#^x]]`)?
Grouped keeps the link line byte-identical to a ledger Task Link. Wake
is then a pure subtree move with no rewrite, notes come along, and the
shape is one Bryan already reads every day.

### 4.2 Semantics

| Question | Answer |
| --- | --- |
| Is a snoozed task **Today**? | **No**, until it wakes: no 🍅 Today mark, not in TODAY on the dash, not in the `=`/`x` lineups. Plugins show a 💤 `15:30` mark instead (Phase 3). |
| Lane effect of snoozing | Same as linking: **Ready/Blocked → Next** (Blocked follows the existing link guard). Pending and Next are unchanged. |
| Freshness | Snoozing is a human gesture, so it **stamps `[fresh::]`**. A snoozed task drops out of today's walk. A snoozed RECURRING occurrence counts as answered, like "linked to Today". |
| Plan budget | On-clock snoozed links **count toward `max_links`** and are reported as an additive `links.snoozed`. Otherwise snoozing becomes a way around the budget, and the overflow lint only appears at 19:00 (Phase 2–3, since it needs both the Rust and JS engines). Phase 1: `bob plan` prints a `💤 N snoozed · next HH:MM` line. |
| Valid times | Today only, and strictly after now. A past or post-midnight time is refused, with a hint: "link it now" or "use `s:1`". |
| Unwoken rows at day end | Left as history in that day's note. The task is still Next (sticky lanes), so tomorrow's NEXT walk resurfaces it. No carry-over. Optional lint: "N snoozes never woke yesterday". |

### 4.3 Waking (`bob snooze wake`)

Wake **re-runs the existing-task link gesture**, minus the
running-session placement. For each wake row in **today's** note:

1. **Pre-checks, on every row (due or not):**
   - The task already has a live link under an open Pomodoro, meaning
     it was linked by hand: **drop the snoozed row** (`already_linked`).
     So Ctrl+Shift+Enter acts as "wake early" for free.
   - The task is done, cancelled, struck, missing or ambiguous:
     **drop the row** (`resolved`) and report it.
2. **Due rows (`wake ≤ now`), per link:**
   - **Blocked** (its prerequisites became open after the snooze): apply
     the same consumption rule as reconcile. Drop the link, promote the
     open prerequisites, report it. Rule:
     `docs/task-status-hooks.md` §Blocked task links are consumed.
   - **Otherwise:** Ensure Next, then move the link subtree into the
     destination Pomodoro (A2):
     1. the first **untimed** open entry whose name exactly matches the
        task's type;
     2. else the first untimed open entry whose name contains the type;
     3. else a new `() — TYPE` placeholder inserted at the **next-up
        slot**, right after the running entry or the last completed
        block.

     It never goes into the running timed entry. A plain `x` close
     would otherwise treat a just-woken task as worked.
3. **Cleanup:** remove emptied wake rows, then the empty `## Snoozed`
   heading.
4. **One write:** a single atomic write through the capture planner's
   snapshot check. If the note changed mid-plan, report
   `inputs_changed` and let tick retry.
5. **Notify** (A5): one best-effort desktop notification per due wake
   row, e.g. `💤→⏰ 15:30 · Email Dan by EoD! (job)`. It reuses
   `desktop_notify.rs` (osascript on macOS) and can be turned off with
   `snooze.notify: false`.
6. **Receipt:** JSON lists `woken[]`, `dropped[]` (with a reason),
   `consumed[]`, `pending[]` and `next_wake_at`. The human summary
   reads like `1 woke · next 19:00`.

### 4.4 `bob tick` step

Add `snooze` to `STEPS`:

```rust
step_with(
    "snooze",
    false,
    Cadence::Interval(5),
    2,
    &["snooze", "wake", "-q", "-f", "json"],
    tasks_gate,
    adapters::snooze,
)
```

- **Position: first.** It is cheap (well under 1 s when nothing is due)
  and latency-matters. gcal and gmail can take 10–60 s.
- **`intake = false`.** Being intake would drag a 10–17 s reconcile
  into every 5-minute tick. The wake writer already does Ensure Next
  and type agreement itself.
- **Gate:** reuse the readiness gate (today's note exists, is rendered,
  and has `## Pomodoros`).
- **Status board:** `next_due_at` shows the next wake time
  (`bob tick -s` → `snooze  ·  next 19:00`).
- **Docs:** update the `docs/tick.md` table and config block, and the
  "order is fixed" sentence. Wake is local and derived, so going first
  is a stated exception.

### 4.5 Gestures and surfaces

**CLI.** Top-level `bob snooze`, under the Daily workflow help section.
It is not under `bob task`, because it is a daily-note noun and does not
rewrite tasks vault-wide.

- `bob snooze` / `bob snooze list` (bare = read-only list, allowed by
  `cli_rules.md`): shows rows, wake times, titles, and a state of
  `waiting`, `due` (time passed, tick not yet run) or `stale`.
- `bob snooze add <route:id> -u/--until <when>`:
  - moves an existing live link, or creates one;
  - runs Ensure Next and stamps fresh;
  - takes `-n/--dry-run` and `-f/--format`.
- `bob snooze wake [<route:id>…] [-a/--all] [-n] [-q] [-f]`:
  - with no args, wakes due rows (this is what tick runs);
  - with refs, wakes those rows now;
  - `--all` wakes every row now.
- `bob snooze drop <route:id>`: removes the row and leaves the lane
  unchanged (sticky).
- `<when>` accepts `HHMM` or `H:MM` (stored as `HHMM`), `+45m` / `+2h`
  (resolved to an absolute time when written), and later configured
  names such as `home`.

**Capture (Phase 2).** A terminal token `z:<when>`. Its mnemonic is
"zzz", and it pairs with `s:<N>`: `s:` says which day, `z:` says what
time today.

- Valid on link items:
  - `@job:email-dan-eod z:1530`
  - `^job:email-dan-eod z:1530`
  - `Email Dan re Yogi @job:email-dan z:1530`
- Refused, with a teaching message:
  - with `=` start ("a snoozed task can't start now");
  - with `s:<N>`;
  - on items without a link.
- `capture-parse` reports the token span and `capture-complete` offers
  named times. The Mac stays a thin client
  (`decisions:mac-capture-is-a-thin-client`).
- The prefix `z:` is unused today. `markers.rs` only knows `s:`, `$`
  and `p:`.

**Mac agenda (Phase 2).** `capture-pomodoros --tasks` adds a `snoozed`
array (wake time, label, resolved task rows) additively. The idle
agenda gets a dim "💤 Later today" fold ordered by wake time. It could
share a time axis with upcoming meetings.

**Plugins (Phase 3):**

- `planDeferredPomodoroLinkCleanup` also prunes `## Snoozed` rows. That
  one change covers release, close, cancel, decay, roll and moves.
- `pomodoroTaskLinkPresence` treats a snoozed row as "linked (snoozed)".
- A 💤 `15:30` mark on the task line, using the glyph `#hide`
  deliberately left free.
- A `bob-plan` chip: `💤 2 · 15:30`.
- A snooze gesture on a ledger link or a task line. It should shell out
  to `bob snooze add` so there is one writer; the plugins already call
  `bob` for merge and gcal. Bryan picks the key.
- The rendering timer (`291-plugin-gcal-events.js:537` style) dims
  rows until their time and brightens them when due.

## 5. Interactions to watch

- **`^ranked-task-links`** (P-high, Next): when it lands, a woken link
  needs a rank. Natural choice: the front of its destination queue,
  since it just became doable.
- **`^task-props-use-time`:** if `[scheduled::]` gains times, "snooze
  until tomorrow 09:00" belongs there, not in `## Snoozed`. Keep the
  boundary clear: Snoozed is today only.
- **R9 carve-out:** a task that lives in a daily note (e.g. `^gtd`)
  clears Next once unlinked. Snoozing daily-note-resident tasks is
  allowed but rarely useful.
- **Vault-sync:** wake is a third automated writer of today's note.
  Keep the write minimal: a move of the subtree plus heading cleanup.

## 6. Requirement adjustments (called out)

| # | Adjustment | Kind | Why |
| --- | --- | --- | --- |
| **A1** | **Event Tasks are not routed through `## Snoozed`.** Treat their span as an implicit snooze already. Later, allow a snooze anchored "after [[#^event]]" that wakes at the event's buffered end or when the task closes, whichever comes first. | Changes the stated "canonical example" | Moving meeting links would reopen at least five accepted records (`synced-meetings-link-by-phase`, `meet-filing-follows-google-until-edited`, `sync-sorts-event-task-links`, `event-task-links-close-by-the-clock`, MEET starts follow the calendar) for little gain. The Dan example is really "after an event", and an anchor captures exactly that. |
| **A2** | Woken links never land in the **running** session. They go to the next-up untimed placeholder. | Changes reused placement | The existing rule prefers the running entry. A plain `x` would then count unworked woken work as worked. |
| **A3** | Snoozing **raises to Next, stamps fresh, and counts toward the budget**, but is **not Today** until it wakes. | Clarification + addition | It is a commitment to today, made by a human. Without the budget count, snoozing dodges `max_links`. |
| **A4** | Wake **re-runs the link guards** and drops resolved, duplicate or consumed rows. Release, complete and cancel **prune** snoozed rows (plugin cleanup helper and Rust retire paths). | Addition | Plugin writers are scoped to Pomodoros, so without this a released or done task could be revived at wake. |
| **A5** | **Notify on wake** (configurable). | Addition | Without a nudge the task quietly reappears in a long lineup, which is the `^email-dan-eod` failure mode. |
| **A6** | **Today only.** Multi-day deferral stays `[scheduled::]` (or a datetime `[scheduled::]` after `^task-props-use-time`). | Scoping | Avoids a second Blocked mechanism (`gmail-reply-wait` rejected split wait fields for the same reason). |
| **A7** | Wake may be **0–5 min late** and needs the Mac awake. Readers mark a row **due** once its time passes. | Accepted limitation | `bob-tick` runs `*/5` on the Mac only. Both use cases are "after X", not "at X". |
| A8 *(optional, Phase 4)* | **Named times** (`snooze.times: {home: "1900"}`). Written resolved as `- **1900** · home`. | Addition | Makes "when I'm home" one token. Storing the resolved time means a config change never moves existing snoozes (same principle as `reply_wait_days`). |

## 7. Open questions for Bryan

1. **Budget (A3):** should snoozed on-clock links count toward
   `max_links`? I recommend yes.
2. **Ready at wake:** should wake raise a hand-written row's Ready task
   to Next (my default), or skip it as "probably released"? Once
   plugin pruning lands (Phase 3), raising is safe.
3. **Section position:** above Pomodoros (my default), or at the bottom
   of the note?
4. **Snooze keymap** in Obsidian, and whether the Mac Capture app wants
   a dedicated snooze affordance beyond `z:`.
5. **Event anchors (A1):** worth Phase 4, or is the existing
   `starts after` relation plus MEET-close offer enough?

## 8. Recommended solution

**Build the user's plan as "deferred link gestures": a `## Snoozed` H2
above `## Pomodoros`, woken by a new first-position `bob tick` step,
delivered in four phases.**

**Phase 1 — bob-cli core (usable on its own with hand-written rows)**

- A `src/native/snooze/` module:
  - parse `## Snoozed` (wake rows plus dedicated-link children,
    reusing the `list_queued_links` rules);
  - section create and remove helpers;
  - `wake` planning through the capture planner's atomic, snapshot-
    checked write.
- The `bob snooze` CLI (`list`, `add`, `wake`, `drop`), following
  `cli_rules.md`: alphabetical options and short aliases.
- Wake semantics from §4.3:
  - guards (`already_linked`, resolved, Blocked consumption);
  - Ensure Next;
  - next-up untimed placement (A2);
  - heading cleanup;
  - desktop notification (A5).
- The tick step `snooze`: first position, `5m`, `tasks_gate`, an
  adapter with `next_wake_at`.
- A `bob plan` snoozed summary line.
- Docs: new `docs/snooze.md`; updates to `docs/reference/vault-format.md`
  (Day notes), `docs/tick.md`, and `docs/plan.md` (Snoozed is not
  Today); a gcal Events-insertion check.
- Conformance tests: parse, wake guards, placement around a running
  session, idempotence (a second `wake` is a no-op), and a time on the
  midnight boundary.

**Phase 2 — capture + Mac:**

- `z:<when>` in the capture grammar, `capture-parse` spans,
  `capture-complete`.
- The `snoozed` array in the `capture-pomodoros --tasks` payload.
- The Mac "💤 Later today" fold.
- The `links.snoozed` budget count in Rust, with conformance vectors.

**Phase 3 — bob-plugins:**

- Snoozed-row pruning in `planDeferredPomodoroLinkCleanup`, and
  "snoozed" presence in `pomodoroTaskLinkPresence`.
- The JS budget mirror.
- The 💤 task-line mark and `bob-plan` chip.
- A snooze gesture that shells out to `bob snooze add`.
- RECURRING walk: a snoozed row counts as answered.

**Phase 4 — only if still wanted after two weeks of use:**

- event anchors (`after [[#^event]]`);
- named times;
- a lint for snoozes that never woke yesterday.

**Memory.** The implementing plan should carry `decisions:` entries
for:

- a new glossary strand **Snoozed Task Link**;
- a new decision record, roughly "Snoozed Task Links wait outside the
  ledger and wake through tick".

Both are new guidance, not corrections, so per `/sase_memory_write`
they default to `false` unless Bryan asks for them. No memory was
edited in this research.

**Why this one.**

- It keeps every hard contract unchanged (Today, budget lineups, close
  numbering, type agreement, Event filing).
- It delivers value in Phase 1 with one new module and one tick step.
- It reuses existing parsers, the placement rule, the link guards and
  the notification transport.
- It turns the moment a task becomes doable, which `^email-dan-eod`
  missed, into an explicit, notified event.

## Appendix — sources consulted

**Vault:**

- `~/bob/bob.md` `^snoozed-tasks`
- `~/bob/2026/20261123.md`, `20261124.md`, `20261125.md`
- `~/bob/job.md` `^email-dan-eod`
- `~/bob/_templates/daily.md`
- `~/.config/bob/config.yml` (`plan:` block)

**bob-cli docs:**

- `docs/tick.md`
- `docs/plan.md` (§Ledger, §Links, §Today)
- `docs/reference/vault-format.md` (§Lane/freshness/Today, §Day notes,
  §Events)
- `docs/capture.md` (§Grammar at a glance, §Scheduling,
  §Linking and starting existing tasks)
- `docs/task-status-hooks.md` (§overview, §Blocked task links are
  consumed)
- `docs/event-link-times.md`
- `docs/task-tag-marks.md` (§`#hide` rejected-glyph note)

**bob-cli code:**

- `src/native/tick/catalog.rs`
- `src/native/ledger_place.rs`
- `src/native/capture/pomodoro_link.rs:47`
- `src/native/capture/task_theme.rs:1051`
- `src/native/capture_pomodoro_start.rs:92`
- `src/native/plan_budget/today.rs:111`
- `src/native/pomodoro.rs:582`
- `src/native/capture_language/markers.rs`
- `src/native/desktop_notify.rs`
- `src/native/capture_pomodoros_agenda.rs`

**SASE memory:**

- `decisions:today-is-read-from-the-ledger`
- `decisions:task-lanes-are-sticky`
- `decisions:gmail-reply-wait-is-a-tagged-hold`
- `decisions:recurring-occurrences-walk-when-due` (its "Reopens when …
  they need a snooze")
- the roster summaries of the event, MEET and successor records
- glossary: Task Link, Pomodoro, Event Task, Off-Clock Pomodoro, Task
  Freshness, Successor Offer, Walker Footer
- `crontab.md`, `cli_rules.md`

**bob-plugins** (read-only survey): the paths cited in §2.4.

**Live data:**

- `cronctl list` (`bob-tick */5`, Mac)
- `cronctl logs bob-tick --machine mac` (run durations of 0–62 s)
