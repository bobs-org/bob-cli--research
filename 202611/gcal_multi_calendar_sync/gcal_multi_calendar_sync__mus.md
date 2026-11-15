# Gcal multi-calendar sync, starting with Birthdays — research (`mus`)

Date: 2026-11-15. Request: teach `bob gcal sync` to sync multiple Google
Calendars under the same `bryanbugyi34@gmail.com` account, starting with the
"Birthdays" calendar, so that Ava's Birthday (Sat Nov 14, all-day, annually
recurring — see `~/tmp/screenshots/20261115_105604.png`) lands in the daily
note, with the source calendar always visible.

## TL;DR

Most of the multi-calendar plumbing **already exists**: `gcal.calendars`
config, per-calendar fetch, per-calendar roots, and journal keys scoped by
`(account, calendar_id, event_id)`. Two small gaps block the request, both in
classification, not transport:

1. `classify()` in `src/native/gcal/classify.rs` omits every event whose
   Google `eventType` is not `default`/`fromGmail`. Google birthday events
   carry `eventType: "birthday"` (special all-day events with annual
   recurrence, per the [Calendar API event-types guide](https://developers.google.com/workspace/calendar/api/guides/event-types)),
   so adding the Birthdays calendar to config today would fetch Ava's
   birthday and then drop it as `omitted — event type: birthday`
   (`event_type` skip code, `src/native/gcal/skip.rs`).
2. All-day events are `Context`, never `Task` (`classify.rs`, restated in
   `is_eligible` in `src/native/gcal/note.rs`: "Declined, cancelled,
   all-day, multi-day, and free events can never become Event Tasks").
   So "Ava's birthday as an all-day bullet" means a **context row**
   (`- **all day** Ava's Birthday [📅](…)`), not an Event Task checkbox.
   That is the right landing spot (see recommendation).

Provenance ("always clear which calendar it came from") is the genuine
design gap: vault rows carry no calendar name today. Attribution flows only
through `[root::]` (routable away from the calendar by token/colour/note
overrides), the opaque `📅` htmlLink, and JSON-only `calendar_id`.

## What I verified in the tree

- **Fetch already fans out per configured calendar.**
  `FetchContext::fetch_days` (`src/native/gcal/snapshot.rs`) loops over
  `config.calendars()` for each contiguous day-run and tags every raw event
  with its calendar id. Any single calendar failing fails the whole snapshot
  (no partial writes). Journal identity is
  `(account, calendar_id, event_id)` (`model.rs` `OccurrenceKey`,
  `plan.rs` occurrences carry `calendar_id` everywhere), so the same event
  id on two calendars cannot collide.
- **Config already supports N calendars.**
  `src/native/config/gcal.rs` parses `gcal.calendars` as ids or
  `{id, root?}` maps; default is `[primary]`. `GcalConfig::syncs`,
  `root_for`, and `calendar_root` (`src/native/gcal/config.rs`) all
  key off the configured list, and `bob gcal calendars`
  (`src/native/gcal/calendars.rs`) prints id, name, role, colour, sync
  membership, and mapped root — the command that yields the id to paste
  into config.
- **Roots already understand calendars.**
  `choose_event_root` (`src/native/gcal/root.rs`) accepts a per-calendar
  `root:` override (`RootSourceKind::Calendar`, source label
  `"calendar <name>"`), ordered below note/learned/token/colour sources.
  So routing Birthdays somewhere distinct (e.g. `family`) needs no code.
- **RSVP is not a blocker.** Birthday events have no attendees; `my_answer`
  (`src/native/gcal/model.rs`) returns `Yes` when there is no self attendee
  or no organizer, so a birthday passes the answer gate.
- **The human `list` table has no calendar column.**
  Columns are `TIME EVENT RSVP ROOT VAULT` (`src/native/gcal/list.rs`);
  only the header names the synced calendars and JSON carries per-event
  `calendar_id` (top-level `calendars` maps id→name). Two calendars can
  share one display name and `list` would show nothing to tell them apart.
- **`note`/`ack` also exclude birthdays today.** `fetch_candidates`
  (`src/native/gcal/note.rs`) reuses task-eligibility, and `ack.rs`
  skips all-day rows outright. Notes keyed by
  `(account, calendar_id, event_id)` would work mechanically, but context
  rows never render description bullets (`plan.rs`: `None` for context
  rows), so private-note value on a birthday is near zero. Defer.
- **Sync never creates daily notes.** `bob gcal sync -D yesterday` writes
  nothing (exit 0, `waiting …`) when yesterday's note is missing, lacks
  `## Pomodoros`, or still holds Templater tags (`docs/gcal.md` § Sync).
  The requested verification step has this precondition — check the note
  exists before judging the run.

## Screenshot details that matter

- The calendar list shows **two distinct calendars both named "Birthdays"**
  (plus primary, Bloomberg, Health, etc.). Name alone cannot disambiguate;
  the implementation and the docs must speak in **calendar id**
  (via `bob gcal calendars`), never display name.
- Ava's Birthday is all-day, annual (`eventType: birthday`,
  `transparency: transparent`, date-valued start/end) — i.e. exactly the
  two gates in §TL;DR. It should also confirm recurring-instance expansion:
  `gog calendar events --from/--to` must return the 2026-11-14 instance of
  the yearly rule. I did not observe a live `gog` call in this session;
  the implementer should confirm with
  `bob gcal list -D 2026-11-14 -a -f json` (expect the birthday present
  with `inclusion: context`, not `omitted`) before touching sync.

## Critique: is this a good idea?

Yes, with the scope below. Birthdays are the ideal first second-calendar:
read-only, Google-owned, no attendees, no RSVP churn, no buffers, no ack
workflow — they exercise multi-calendar fetch + provenance with almost no
lifecycle surface (no MEET filing, no close semantics, no reroute
reporting). The rejected alternative — promoting birthdays to Event Task
checkboxes with Pomodoro links — would drag in MEET phase filing, past-day
born-done handling, ack tagging, and review-walk/freshness interactions
for rows nobody works sessions against. A birthday is a reminder, not a
meeting; a context bullet is the honest shape, and it matches the request's
own "all-day bullet" wording.

Two cautions:

1. **Provenance-by-root is a trap.** Mapping Birthdays→`[root:: family]`
   looks like attribution but isn't: tokens, colours, and private notes
   outrank the calendar source
   (decisions `gcal-root-follows-google-until-edited`,
   `private-event-notes-beat-google-per-field`), so the root can silently
   stop naming the calendar. Provenance must be its own marker, not a root.
2. **Don't generalize all-day→task.** Lifting the all-day ban globally
   would sweep holidays, travel days, and multi-day spans into Event Tasks
   and MEET filing. If anyone later wants checkbox birthdays, gate it as an
   explicit per-calendar opt-in (e.g. `task: true` on the calendar entry),
   never as a change to the all-day rule.

## Requirement adjustments (called out)

1. **"Event task" → context bullet.** The request says both "added as an
   all-day bullet" and "which event task came from which calendar". I
   recommend the bullet wins: Ava's birthday lands as an all-day **context**
   row, consistent with the standing contract that all-day events can never
   become Event Tasks
   (decisions `calendar-events-are-daily-note-event-tasks` residence,
   `synced-meetings-link-by-phase` filing — neither covers all-day rows).
   If Bryan wants a checkbox, say so explicitly; cost is MEET filing +
   close/ack semantics for a new task class.
2. **"Always clear" needs a definition.** I define it as: (a) the vault row
   itself names the calendar for any non-primary calendar; (b) the human
   `list` table gains a calendar column; (c) JSON already has
   `calendar_id` — add `calendar_name` beside it. Primary-calendar rows
   stay byte-identical (zero churn for today's single-calendar users).
3. **Verification precondition.** `bob gcal sync -D yesterday` only proves
   something if yesterday's daily note already exists with a rendered
   `## Pomodoros` section; otherwise a silent `waiting` exit looks like
   failure. State that in the plan.

## Recommended solution

1. **Config (no code):** `bob gcal calendars` → add the Birthdays calendar
   **id** (not its display name — two calendars share it) to
   `gcal.calendars`, e.g.
   `calendars: [{id: primary}, {id: <birthdays-id>, root: family}]`.
   The `root:` is routing, not provenance; Bryan picks the value
   (`family` reads naturally; any area/project works). Default stays
   `[primary]`, so existing users see zero change.
2. **Classify (small code):** in `classify.rs`, accept
   `eventType: "birthday"` alongside `default`/`fromGmail` **only down the
   all-day path** → `Context("all-day")` / `Context("all-day · day N of M")`.
   Timed `birthday` events (shouldn't exist, but be safe) keep today's
   omit. Mirror the allowlist in `skip.rs` vocabulary so the reason reads
   deliberately, and document the `event_type` code change in
   `docs/gcal.md` § Skipped events. Leave `is_eligible` (tasks) untouched.
3. **Provenance marker (the design work):** for rows whose calendar is not
   the primary one, render the calendar's short name in a fixed slot:
   - context rows reuse the qualifier position:
     `- **all day** Ava's Birthday · *Birthdays* [📅](…)`
     (italic qualifier styling already exists in Obsidian; no qualifier
     competes on single-day all-day rows);
   - Event Task rows (future non-primary timed calendars) put the same
     short name at the end of the Google-owned badge run, so
     `split_row_spans` (`src/native/gcal/lifecycle.rs`) keeps it
     Google-owned and Bryan's edits still win;
   - the marker is **name, never id**, in the vault; ids live in JSON and
     in `-C` flags. Open edge, flagged for the implementer: the two
     same-named "Birthdays" calendars — recommend documenting "first
     configured id wins the display name; disambiguate by id in config"
     or suffixing on collision. Either is fine; pick one and write it
     down.
   - `list` human table: add a calendar column (or trailing dim name);
     JSON: add per-event `calendar_name`.
   - Journal the marker text in the row's span hashes like time/title so
     renames reconcile instead of duplicating (follow the existing
     `spans: BTreeMap<String, String>` pattern in `plan.rs`).
4. **Docs:** `docs/gcal.md` (Configuration, Calendars, List, Sync,
   Skipped events, "Who owns each part of a row" gains a provenance row),
   `docs/reference/configuration.md#gcal`, and the
   `bob gcal calendars`/`list` help strings. No version bump, no
   CHANGELOG (release train owns those —
   decisions `bob-cli-releases-ride-a-daily-train`); additive JSON fields
   don't break the `!` contract rule, but call it out in the plan.
5. **Tests & verification:**
   - unit: `classify` birthday all-day → context; birthday timed → omit;
     `syncs`/`root_for` with two same-named calendars (id-keyed, not
     name-keyed);
   - fixture-level: snapshot/plan test with a fabricated
     `eventType: birthday` payload asserting the exact context-row bytes
     including the marker;
   - live: `bob gcal list -D 2026-11-14 -a -f json` (birthday present as
     context), then `bob gcal sync -D yesterday` with the real binary and
     confirm Ava's row in yesterday's `## Events` — after confirming that
     note exists and is Templater-rendered.

## Open questions for the implementer (not blockers)

- Does `gog calendar events --from/--to` expand yearly recurrences into
  instances by default, or is a flag needed? One live query answers it.
- Which of the two "Birthdays" ids owns Ava's event, and is the other one
  a regular calendar (whose `default`-type events would already sync once
  configured)?
- Exact qualifier-slot wiring for all-day context rows in `plan.rs`
  `build_occurrences` — I traced the types, not every assignment; confirm
  no qualifier competes on single-day all-day rows before using the slot.
