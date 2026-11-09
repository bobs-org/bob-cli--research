# Giving unowned Google Calendar events local metadata (routes, buffers, reasons)

**Swarm report (`mus`). Question: how should Bryan attach metadata like
`@body` or `-30 walk home from the park` to event tasks whose Google
Calendar events he does not own, ahead of time (at RSVP time, not on the
day)? Includes a critique of the idea, alternatives considered, and a
recommended solution.**

## 1. Problem restatement

Bryan wants per-event logistics on synced Event Tasks — a root/route
(`@love`, `@body`), a clock tag (`#off`), a travel/prep buffer (`-30` /
`+15`), and a human reason (`Drive to Kelly's`) — for events organized by
someone else. Two facts block the current grammar:

1. **The description is read-only to him.** Buffers, routes, clock tags,
   and bullet copy are all parsed from the Google description
   (`docs/gcal.md` § Off-clock events, § Buffers, § Root selection). An
   organizer-owned description he cannot edit cannot take a Google-owned
   buffer: a hand-added `[buffer::]` is currently treated as his edit and
   reported once (`Known limits`).
2. **He wants to set it at RSVP time.** The row only materializes when
   `bob gcal sync` runs for that day's note, and `awaiting_reply` events
   are omitted entirely until he RSVPs Yes. Even after RSVP, the daily
   note for a future day may not exist yet, so there is nowhere to put a
   vault edit. Post-sync vault edits work for today but not for
   "I RSVP'd to a dentist appointment three weeks out and already know
   parking takes 20 minutes."

So the ask is really: **a Bob-owned, pre-day, per-event override layer
that merges at sync time and survives Google-owned overwrites.**

## 2. What the current system already does (ground truth)

Read the code and `docs/gcal.md` before proposing anything; the ownership
model is precise and the proposal must extend it, not fork it.

- **Read-only grant.** `gog` fetches with `calendar.readonly`; event
  fetching requests only
  `attendees(self,responseStatus),organizer(self)` plus timing/title/
  description/badges (`src/native/gcal/gog.rs`). The accepted decision
  `decisions:bob-gcal-is-read-only-and-proposes-once` (partly superseded
  but the read-only half stands) says Bob writes each row and link once
  and never writes back to Google.
- **Four Google-owned spans.** Time, title, badges (join/location links),
  explicit `#off`/`#on`, and `[buffer::]` form the badge run; sync
  three-ways each span against the journal hash and keeps Bryan's edit,
  reported once as `kept_edit` / `kept_off_clock`
  (`src/native/gcal/plan.rs` `apply_span_updates`,
  `src/native/gcal/lifecycle.rs`). `[root::]` follows Google's chosen
  root until edited (`decisions:gcal-root-follows-google-until-edited`);
  description bullets follow Google until edited
  (`src/native/gcal/plan.rs` `apply_description_update`,
  `src/native/gcal/bullet_block.rs`).
- **Buffers come only from the description.** `-30` / `+15` directive
  lines and `-30 Reason` reason lines both parse in
  `src/native/gcal/description.rs`; the first value per side wins, and a
  reason attaches only when its line sets or repeats that value
  (`decisions:buffer-reasons-ride-description-bullets`). Someone else's
  prose can already false-trigger this (`+1 to that` reads as a 1-minute
  after-buffer — documented in Known limits).
- **RSVP gating.** `my_answer()` returns Yes only for organizer-self,
  no-guest, or explicit accept; NoReply (no `self` attendee or blank
  status) classifies as Omitted `awaiting_reply`
  (`src/native/gcal/model.rs`, `src/native/gcal/classify.rs`). `list -a`
  shows the reason; `sync -f json` lists it under `skipped`.
- **Phase filing.** New rows file under a MEET by buffered phase at sync
  time; Google time/buffer moves re-file only Bob-owned placeholder or
  Bob-shaped closed filing
  (`decisions:meet-filing-follows-google-until-edited`).
- **Identity gap.** Neither `list -f json` nor `sync -f json` currently
  emits `calendar_id`/`event_id` per row (checked
  `src/native/gcal/list.rs` `print_json`, `src/native/gcal/sync.rs`
  `print_json`). Time+title matching is therefore the only selector today
  — ambiguous for duplicate titles and unstable across moves. Any
  annotate flow must fix this first.
- **Journal shape.** One `gcal.row` record per (occurrence key, day) with
  span hashes, root, source, and `DescriptionState::{Absent, Tracked,
  HandsOff}` (`src/native/gcal/journal.rs`). The store is append-only
  per-host JSONL under vault-synced `.bob/gcal/` and folds across hosts,
  with the Mac as the single sync writer.

## 3. Critique: is this a good idea?

**Yes, with a narrowed scope.** The request is justified: travel/prep
buffers and roots are inherently attendee-local knowledge ("I need 30
minutes to walk home from the park") that the organizer will never put in
their description, and RSVP time is exactly when Bryan knows it. Forgetting
it until the day-of defeats the purpose of buffers (agenda gaps,
conflicts, `refresh_at`, MEET clustering all read the buffered span).

Adjustments I would make to the requirements as stated:

1. **Do not pursue Google write-back.** Requesting a writer scope and
   PATCHing the organizer's description would violate the read-only
   decision, need a re-consent and a new `gcal.writer`-style permission
   story, fight the organizer's later edits with no conflict UI, and
   silently fail for the common case (guests usually lack "modify event"
   rights). It also leaks Bryan's logistics into someone else's invite.
   Keep Google read-only; store overrides in Bob.
2. **Do not allow overriding time, title, badges, or join links.**
   Those are organizer facts; letting local overrides rewrite them
   breaks the span-hash reconciliation, the `kept_edit` signal, and the
   "tap 📅 to open the real invite" trust. Scope overrides to exactly the
   attendee-local fields: **root, clock tag, buffer sides, buffer
   reasons.** Everything else stays Google-owned as today.
3. **Do not put freeform prose in the override store.** Sibling notes and
   child bullets below the description block are already vault-owned and
   never touched by sync. The override store only needs the four fields
   above; prose has a home already.
4. **Do allow annotating `awaiting_reply` events.** The natural moment is
   "I just RSVP'd Yes and, while I'm here, add the buffer" — or even
   "stage it before I RSVP so I don't forget." An override keyed to a
   future day must wait for the Yes and then apply, not force the event
   into the note early.
5. **Do not auto-promote Maybe/NoReply to tasks.** Overrides must never
   change inclusion. An override on an omitted event waits; it does not
   summon a row, change RSVP, or bypass `gcal.tentative`.

The failure mode to avoid is a second ownership rule. The codebase just
paid down exactly this risk by folding buffer reasons into the one
Google-owned description block (see the rejected "separate tracked reason
block" in `decisions:buffer-reasons-ride-description-bullets`). The
override layer must read as "Bryan edited these fields at birth," reusing
the existing kept/edit-wins machinery, not as a parallel block with its
own journal schema and find logic.

## 4. Options considered

| Option | How it works | Verdict |
| --- | --- | --- |
| **A. Vault edit after sync (status quo)** | RSVP, wait for the day's sync, hand-edit `[buffer::]` / `[root::]` / bullets; series edits teach the series. | Keep as the day-of path, but it cannot satisfy "ahead of time": no row exists yet, and `awaiting_reply` rows don't exist at all. Also relies on memory weeks later. |
| **B. Journal-backed per-event overrides + `gcal annotate` CLI (recommended, §5)** | New `gcal.override` journal records keyed by stable Google identity; sync merges them as pre-touched fields; `list` exposes IDs for selection. | Meets all three goals. Small schema addition, reuses kept/edit-wins reporting, works pre-day and pre-RSVP, survives organizer edits. Costs one new subcommand and ID plumbing in `list`/`sync` JSON. |
| **C. Google write-back (PATCH description)** | Request writer scope; append `-30 reason` / `@route` to the organizer's description where `guestsCanModify` allows. | Reject: scope escalation, usually forbidden by the organizer, organizer prose can clobber it, leaks logistics, needs conflict UI. Directly reopens the rejected two-way-sync alternative. |
| **D. Config-file overrides (`gcal.overrides:` in `config.yml`)** | Hand-edited YAML keyed by `calendar_id/event_id` with root/buffer fields. | Reject as primary: opaque IDs in a home config file are un-discoverable, unvalidated, host-local (not vault-synced), and painful for recurring instances. Could serve as a power-user import format, not the interface. |
| **E. Markdown override note (`gcal_overrides.md`)** | A vault note with one section per event that sync parses. | Reject: fragile free-text parsing, no atomic validation, competes with the journal as second source of truth, still needs an ID picker. Worse version of B with a prettier face. |
| **F. Companion task + relation link** | Create a separate task ("Walk home 30m") and `~`/`starts after` link it to the Event Task. | Useful as a complement for complex logistics, but it does not widen the occupied span, so agenda gaps, conflict detection, MEET clustering, and `refresh_at` all stay wrong. Does not substitute for a real buffer. |

## 5. Recommended solution: pre-touched overrides that merge at sync time

### 5.1 Mental model (one sentence for the docs)

> **An override is a vault-recorded edit to fields Google owns, made
> before the row exists; sync treats overridden fields as already
> Bryan-edited from birth.**

That sentence does all the heavy lifting: no new ownership column in the
"Who owns each part of a row" table, no new block-finding rule. The merge
order per field becomes: **override > vault edit > Google**, with the
first two both reporting through the existing `kept_*` once-only
warnings when Google later disagrees.

### 5.2 Data: `gcal.override` journal records

- New record kind `gcal.override` in the existing `.bob/gcal/<host>.jsonl`
  namespace, folded by `journal.rs` alongside `gcal.row`. Fields:
  `calendar_id`, `event_id`, `ical_uid`, `series_id` (when present),
  `scope` (`instance` | `series`), the override payload
  (`root`, `clock` (`off`/`on`/null), `before_minutes`,
  `after_minutes`, `before_reason`, `after_reason`), `updated_ts`,
  `updated_host`, and optional `note` (why, for `list` display only —
  never synced to the row).
- **Keying.** Default scope is `instance`, keyed by
  `(calendar_id, event_id)` with `ical_uid` as a cross-check and move
  heuristic. Recurring instances carry stable Google instance IDs
  (`<series>_<timestamp>Z`), so instance scope works for the common
  "this dentist appointment" case. Opt-in `--series` scope keys by
  `(calendar_id, series_id)` and behaves like series-root teaching: it
  applies to future occurrences until an instance override or a vault
  edit narrows it. When an event moves days, the override follows the
  `event_id` (day is a hint at write time, never part of the key).
- **Precedence inside the store.** Last writer wins per
  (scope key, field group), consistent with theme/relation journals;
  instance beats series; an explicit `--clear` tombstones a field group
  rather than deleting history. A row-created vault edit and an override
  that disagree resolve vault-wins (the note in front of Bryan wins over
  the record he forgot), reported once as `kept_override` so the stale
  override gets noticed and cleared.
- **Lifecycle.** Cancelled/declined/moved-away occurrences keep their
  overrides inert: a tombstoned row never resurrects from an override,
  and an override never blocks a cancel. Overrides do not create rows,
  links, MEET entries, or journal `gcal.row` records on their own.

### 5.3 Write path: one new subcommand

Per `cli_rules.md`, subcommands stay alphabetical with short-aliased long
options and excellent `-h` text. Sketch (names bikesheddable, shape not):

```text
bob gcal annotate -D 2026-12-03 --event <id> --root @love --before 30
    --before-reason "walk home from the park" [--after 15 ...]
    [--clock off] [--series] [--clear before|after|root|clock|all] [-d]
```

- **Selection must be beautiful.** `bob gcal list -D <day>` gains a
  stable short selector per row (e.g. `#3`, alongside the new
  `calendar_id`/`event_id` in `-f json`). `annotate --event` accepts the
  short index (resolved against that day's snapshot), a
  `calendar_id/event_id` pair, or an `ical_uid`. Never require pasting a
  raw Google event ID by hand from the Calendar UI.
- **Validate everything at write time.** Unknown root (same R11 rules as
  sync), bad minutes (1–720, integer, first-value-wins documented),
  reason without its side's minutes, and reason grammar violations (the
  `-30Drive` / `+1 555-1212` traps from § Buffer reasons) all fail fast
  with the same messages sync uses — not weeks later at sync time.
- **Preview.** `-d` prints the exact row sync would render (badges,
  `[buffer::]`, reason bullets, root, MEET phase) without writing the
  journal, mirroring `sync -d`.
- **Read path parity.** `list` (human + JSON) shows pending overrides per
  event (`◈ override: −30m reason…`, `root @love`), including on
  `awaiting_reply` rows, so Bryan can see at RSVP time what will apply.

### 5.4 Sync merge (exact order)

For each planned Task occurrence with a matching override:

1. Compute Google's render exactly as today (directives, clock, buffer,
   bullets, root choice).
2. Apply the override as a pre-touch: replaced fields are marked
   edited-from-birth. Concretely this means the fresh span hashes for
   `badges`/`[buffer::]`, the chosen root, and the rendered reason
   bullets are replaced by the override's values **before** the
   `apply_span_updates` / `apply_description_update` three-ways run, so
   those functions see "journaled ≠ fresh, current == journaled" turn
   into "already edited" with zero new branches.
3. Reason bullets render through the existing `render_reason` path
   (`↤ *Nm before* · …` / `↦ *Nm after* · …`), sharing the block's
   ownership, cap exemption, and `description_lines` count as today.
4. Conflicts report once through existing channels: Google changed a
   field Bryan overrode → `kept_buffer` / `kept_root` / `kept_description`
   family (one new code at most, `kept_override`, if the family split
   gets noisy). Vault hand-edit vs. override → vault wins +
   `kept_override` naming the stale record and its `--clear` fix.
5. `sync -F` (day reset) intentionally drops the pre-touch for that day's
   rows and re-applies pure Google, exactly like it drops vault edits —
   but the override records themselves survive (they are not day state),
   so the next normal sync re-merges them. Document this; it is the one
   genuinely surprising interaction.

### 5.5 What stays unchanged

- Grant stays `calendar.readonly`; no new Google fields except the IDs
  `list` needs for selection (already fetched: `id`, `iCalUID`,
  `recurringEventId` are in the snapshot — only the display/JSON
  plumbing is new).
- Inclusion is untouched: overrides never promote Maybe/NoReply/Free/
  multi-day to tasks.
- Post-sync vault editing keeps working exactly as today, including
  series-root teaching. Overrides are the pre-day complement, not a
  replacement.
- Single writer rule holds: any host may append `gcal.override` records
  (they fold across hosts via vault git sync), but only `gcal.writer`
  applies them during sync.

## 6. Reliability notes (for the implementer)

- **Identity hazards.** Recurring-series splits arrive as cancel+insert
  with new instance IDs; carry instance overrides forward only on exact
  `ical_uid` + `originalStartTime` match, otherwise leave them orphaned
  and surface an `override_orphaned` warning in `list`/`doctor` rather
  than guessing. Moved single events keep their `event_id` — follow it.
- **Incomplete snapshots write nothing** (existing invariant): overrides
  must not let a partial fetch create half-annotated rows.
- **Idempotency.** Re-running sync with the same override set is a no-op
  (`in_sync: true`); the override fold must be a pure function of
  (snapshot, override records, journal) with no wall-clock input except
  phase classification.
- **Tests to add** (mirror `tests/gcal_sync.rs` / `tests/gcal_list.rs` +
  `tests/fixtures/gcal/events.json` + fake `gog` in
  `tests/gcal_support/fake_gog.py`): instance override applies at birth;
  series override teaches future instances; instance beats series; vault
  edit beats override with one warning; override on `awaiting_reply`
  waits then applies on Yes; moved event carries its override; cancelled
  event ignores its override; `sync -F` resets the day but keeps records;
  malformed/unknown-root override rejected at `annotate` time.
- **Observability.** `doctor` gains an override count + orphan check;
  `sync -f json` rows gain an `override: {applied: [...], kept: [...]}`-
  shaped detail (exact keys TBD at plan time) so Bob Mac Capture and
  ledger tools can render "this row carries your pre-set buffer" without
  parsing prose.

## 7. Open questions for Bryan (answering these is the plan phase)

1. Should `--series` scope exist in v1, or is instance-only enough until
   someone feels the recurring pain? (Lean: instance-only v1; series
   teaching already covers roots via vault edits.)
2. Should overrides be visible/editable in Obsidian anywhere, or is the
   terminal `list` → `annotate` loop plus JSON for future Mac Capture
   affordances sufficient?
3. Reason-length and character policy: reuse the description-line grammar
   verbatim (recommended — one rule), or relax it for the override path
   since forgery-from-title is impossible there?

## 8. Recommendation

**Build Option B, instance-scope first: a `gcal.override` journal +
`bob gcal annotate` write path + ID selectors in `list`, merged at sync
time as pre-touched fields, with Google write-back explicitly out of
scope.** It is the only option that is intuitive (annotate the event you
see in `list` at RSVP time), reliable (reuses the kept/edit-wins
three-ways, the journal fold, and the single-writer rule; never writes
to Google; never promotes omitted events), and beautiful (one command,
validated inputs, dry-run preview, override badges in `list`). Keep the
day-of vault edit path exactly as is — the two compose as
override-then-edit, vault wins, warned once.
