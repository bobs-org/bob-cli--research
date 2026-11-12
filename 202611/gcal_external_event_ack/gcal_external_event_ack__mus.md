# Soft-requiring ack for external Google Calendar events — research report

Researcher: mus · 2026-11-12 · scope: `bob gcal` ack triage + unacked warnings in sync

**Verdict:** Yes, build it — but not as stated. Build `bob gcal ack`
(not `bob gmail ack`), covering only events that would become Event Tasks,
with ack state in the existing per-host gcal journal, note-as-ack preserved,
and sync rendering an ownership-safe, journaled `⚠ UNACKED` marker plus an
actionable hint. The weekly `gtd_daily.md` reminder should replace — not
duplicate — the existing daily "Review next week" row, or the two will fight.
Details and seven requirement adjustments in §7–§8.

## 1. What was asked

1. Soft-require ack for all external (not owned by Bryan) Google Calendar
   events before they become event tasks.
2. "Acked" = explicit no-op ack **or** a private note (e.g. via
   `bob gcal note`).
3. Add a new `bob gmail ack` command with `-n|--next-n-days`; iterate every
   unacked external event in the window (always including today); prompt with
   single-keypress choice: **Ack** (no-op) or **Note** (same argument form as
   `bob gcal note` TEXT).
4. `bob gcal sync` still creates event tasks for unacked externals, but renders
   a hard-to-miss warning in those rows.
5. Add a weekly recurring task to `~/bob/gtd_daily.md` reminding Bryan to run
   `bob gcal ack -n 7`.
6. Lead the design: intuitive, reliable, beautiful.

Two literal readings of the request are wrong and §§7–8 change them: the noun
(`gmail` → `gcal`) and the `-n` direction (see §2.5).

## 2. How it works today (grounded)

### 2.1 Command tree

`src/native/gcal/cli.rs::build_cli` owns the tree; `src/native/gcal/mod.rs::run`
dispatches. Subcommands: `calendars`, `doctor`, `list`, `login`, `logout`,
`note`, `sync`. Bare `bob gcal` runs `list`. There is **no** `ack` anywhere
under `gcal`, and `src/native/gmail/cli.rs::build_cli` (subcommands `attach`,
`draft`, `link`, `list`, `login`, `logout`, `new`, `peek`, `reply`, `save`,
`search`, `send`, `sync`) has no `ack` either. The requested name
`bob gmail ack` therefore cannot be an extension of an existing ack flow —
it is a naming slip. The feature belongs under `bob gcal`.

### 2.2 What "external" can mean in code

`src/native/gcal/model.rs` carries two different ownership signals:

- `organizer_is_self: bool` — true only when the Google `organizer` object has
  `is_self`. This is the correct "owned by me" test.
- `organizer_or_no_guests: bool` — true when I organize **or** when there are
  no guests at all (`my_answer()` returns `(Yes, true)` when the organizer is
  self, when `attendees` is missing, or when it is empty). It is also false for
  the "no self attendee found" path, which yields `MyAnswer::NoReply`.

So "external" must be defined as `!organizer_is_self` (optionally further
requiring guests exist). Using `!organizer_or_no_guests` would wrongly sweep
in odd guest-less edge cases and wrongly exclude nothing useful. Note the
existing consumer: `src/native/gcal/list.rs:572` already uses
`!event.event.organizer_or_no_guests` for the ⚑ fragile-directives hint; an
ack feature should use the stricter `!organizer_is_self` and say so in help.

### 2.3 Which events become Event Tasks

`src/native/gcal/classify.rs::classify` returns
`Inclusion::Task | Context(String) | Omitted(String)`:

- Non-`default`/`fromGmail` types, `cancelled`, `declined` (answer No), and
  **unanswered invites** (`MyAnswer::NoReply` → `Omitted("reply in Calendar")`)
  never become tasks.
- `Yes`/`Maybe` timed events become `Task`, with short/busy nuances;
  all-day, free, transparent, and multi-day spans mostly become `Context`.

Consequence: "every external event in the window" is far too broad. Most of
that set (declined, cancelled, focusTime/outOfOffice, unanswered, all-day,
free) never produces a row, so prompting over it would be pure noise. The ack
loop must default to **future Task-inclusion externals with answer Yes/Maybe**,
which is also the only set for which the sync warning (§2.6) can ever render.

### 2.4 Notes already exist and already count as triage

`docs/gcal-notes.md` + `src/native/gcal/note.rs` + `src/native/gcal/journal.rs`
define the private event note: Bob-only description text keyed by Google
identity (`{calendar_id, event_id}` for scope `event`,
`{calendar_id, series}` for scope `series`), stored as `gcal.note` records in
`.bob/gcal/<host>.jsonl` (union-merged, last-writer-wins on
`(ts, host, path, line)`; `text: ""` is a deliberate clear; 2048-byte cap
`MAX_NOTE_BYTES`; account-guarded; notes survive `sync -F`). `GcalEvent::apply_notes`
layers occurrence → series → Google field-by-field (root, clock, buffers,
reasons, prose). Ownership is unchanged: the row follows while untouched,
Bryan's edit wins and is reported once (`kept_root`, `kept_edit`,
`kept_description`). `sync -d` diffs are the only place note text appears in
sync output; `list`/`sync` JSON carry only summaries (`scope`, `fields`,
`bullet_lines`), never text.

So half the requested "acked" definition already exists. An explicit ack must
be a **second, cheaper journal record**, not a second kind of note — otherwise
every no-op ack pollutes the note namespace, `doctor` orphan counts, and the
`fragile_directives` logic.

### 2.5 Window flags point in opposite directions

`src/native/gcal/cli.rs::last_n_days_arg`: sync's `-n/--last-n-days N` means
"the last N days ending today (2 = today and yesterday; combines with `-D`)".
The request's `-n|--next-n-days` means the **next** N days including today.
Same short flag, opposite arrows, sibling subcommands. That is learnable only
if both help strings say the direction in the first seven words (sync's
already does). The long name `--next-n-days` is symmetric with
`--last-n-days` and therefore worth keeping despite its clunkiness; do **not**
shorten to `--next` alone. Keep `-n` for muscle memory (fresh arg namespace per
subcommand, so no parser conflict) but document the mirror explicitly.

### 2.6 Sync rendering and ownership constraints

`src/native/gcal/render.rs::render_task_row` renders
`- [status] #task **HHMM-HHMM** title badges [#off/#on] [buffer::] [root::] [type::] ^id`.
Ownership (`docs/gcal.md` § Who owns each part of a row, plus decisions
`bob-gcal-is-read-only-and-proposes-once`,
`gcal-root-follows-google-until-edited`,
`private-event-notes-beat-google-per-field`, `buffer-reasons-ride-description-bullets`):
Google owns spans/time/title/badges; the vault owns the checkbox, `[root::]`,
children, and the row itself; description bullets follow while untouched, edits
win once-reported. A warning that lives inside the Google-owned run (e.g.
prepending ⚠ to the title) will fight the three-way merge and produce
`kept_edit` noise. A warning that lives outside any managed span (e.g. text
after `^id`) breaks block-id parsing. The warning must therefore be a
**sync-managed, journaled token in the vault-adjacent position** (before
`[root::]`, after badges/clock/buffer) that sync adds and removes itself and
that users are told never to hand-edit — same pattern as the stamp
(`src/native/gcal/stamp.rs`) and link ordering (`src/native/gcal/link_order.rs`).
Precedent for the glyph language already exists: ⚑ for fragile directives
(`list.rs:766`, JSON `fragile_directives`), `kept_*` once-only notices, and the
`past_open` 7-day footer in `list`.

### 2.7 Recurring-task syntax for the reminder

`~/bob/gtd_daily.md` (read 2026-11-12) already holds a daily
`#browser Review next week in Google Calendar` row and a daily `#sync Run
gcal sync + gkeep pull + gmail sync` row, both
`[repeat:: every day when done]`. The weekly form the request wants exists in
the same file: `[repeat:: every week on Monday when done]` (e.g. the Bank
import and Weekly review rows). `docs/date-marks.md` specifies the
`[repeat:: …]` grammar; PRE/POST checklist rows need `when done`. So the
reminder is one line, but its interaction with the existing daily review row
is the actual design question (§6.5).

### 2.8 Test and doc gates

`tests/` holds `gcal_sync.rs` (4634 lines), `gcal_lifecycle.rs` (2257),
`gcal_notes.rs` (1374), `gcal_note_cli.rs` (3386), `gcal_list.rs`,
`gcal_cli.rs`, `gcal_auth.rs`, `gcal_diagnostics.rs`. Note TTY flows are
simulated with `BOB_GCAL_ASSUME_TTY=1` (see `note` after-help). Doc gates per
`sase/memory/docs.md`: `just docs-gen` + `just docs-check`; behavior changes
update the contract/reference plus only the guide steps made incorrect; the
repo README stays a front door. Per `sase/memory/cli_rules.md`: keep options
alphabetical, every public long option gets a short alias, never rename
without a permanent hidden alias, add only under the `gcal` noun (already the
right noun).

## 3. Critique — is this a good idea?

**Yes, with the scope narrowed.** The underlying pain is real: invites Bryan
does not own arrive with no `@route`, no `#off/#on`, and no buffer reasons, so
first sync files them under a default root with wrong clock/buffers, and the
row then looks "handled" when it was never triaged. An RSVP-time triage loop
is exactly the hole the private-note design left open: notes can be written
weeks early, but nothing prompts Bryan to do so. A weekly lookahead that asks
"do you know what this is and where it goes?" closes that hole at the cheapest
possible moment.

But five parts of the plan as stated would backfire:

1. **"All external events" is the wrong set.** Prompting over declined,
   cancelled, unanswered, all-day, and free events trains Bryan to mash "ack"
   blindly — the opposite of triage. Gate on `Inclusion::Task` + answer
   Yes/Maybe + `!organizer_is_self`. Offer `--all` for Context/Omitted, never
   default to it.
2. **"Soft require" is a misnomer — and that is fine.** Sync must keep
   creating rows (a gate that drops meetings violates propose-once and loses
   attendance evidence; cf. `ended-synced-meetings-are-born-done`). Call it
   what it is: **lookahead triage with a persistent visual debt marker**. The
   marker must clear itself the moment the ack or note lands (next sync), or
   it becomes permanent clutter.
3. **A no-op ack with no expiry rots.** An ack recorded in October for a
   December instance claims triage that predates the final invite update
   (time/title/attendees all change). Ack records should carry the `seen`
   identity the note path already carries (title/start/ical_uid) and `list`
   should flag `ack_stale` when Google's current snapshot disagrees — warn,
   do not auto-clear, so the row is never silently un-triaged.
4. **Single-keypress is right for the loop, wrong as the only interface.**
   Require: TTY loop with `a`/`n`/`s`/`q` (+`?` help, `e` edit); non-TTY
   refuses with exit 2 and prints candidates (the `note` command's established
   contract); `-f json` plans the queue without prompting; `-d` previews
   journal appends. Anything less breaks scripts, the Mac thin client
   (decision `mac-capture-is-a-thin-client` — the Mac can only call versioned
   `bob` subprocess/JSON), and tests.
5. **The Note option must reuse the note write path byte-for-byte.**
   `note` TEXT has genuinely tricky grammar (directive-first canonicalization,
   `rewrite_gcal_argv` argv surgery, `-d` preview, `-e` editor, `-A` adopt,
   `-c` clear, `-s` scope for recurring). A second implementation of "accepts
   the same argument form" will drift within one release. The ack loop's Note
   branch must call into the same constructor/validator/persister as
   `note::run`, with the event pre-selected so the user types only TEXT (or
   `-e`/`-A` flags forwarded before TEXT).

## 4. Options considered

| Option | Ack store | Sync warning | Verdict |
|---|---|---|---|
| A. Journaled `gcal.ack` + note-as-ack (recommended, §5) | New `gcal.ack` record, same keying/fold/clear semantics as `gcal.note`; live non-cleared note also counts | Sync-managed `⚠ UNACKED` token before `[root::]`, journaled per row, auto-removed on ack; JSON `acked`/`ack_source` | Reliable, multi-host, testable; one new record kind, no second ownership rule |
| B. Note-as-ack only (empty note = ack) | No new record; empty-text note means acked | Same marker, driven by note presence | Cheapest, but overloads clear-vs-ack (today `text: ""` is a deliberate clear), pollutes `doctor` orphans and `bullet_lines`, and cannot distinguish "looked, nothing to add" from "never looked" |
| C. Vault-side marker field (`[acked:: date]`) | Row field Bryan could hand-edit | The field itself is the warning | Breaks the derived-status rule (decisions: `today-is-read-from-the-ledger`, freshness): hand-editable state that review never stamps; merge conflicts across hosts; sync would have to adopt/ignore it — a second ownership rule |
| D. No new command; extend `gcal note -a` with an ack column | Reuses note list | Same marker | Least code, but `note -a` is a 90-day browser, not a bounded triage queue; no forward-window loop, no single-keypress flow, no JSON plan for the Mac client |

## 5. Recommended solution

### 5.1 Command: `bob gcal ack` (not `gmail`)

```
bob gcal ack [-n N|--next-n-days N] [-D DAY ...] [-a|--all] [-d|--dry-run]
             [-f|--format human|json] [-q|--quiet]
             [-s|--scope event|series] [-i|--event-id ID] [-C|--calendar ID]
```

- Window: next N local days **including today** (`-n 7` on a Monday covers
  Mon–Sun). Default when neither `-n` nor `-D` is given: `-n 7` (matches the
  requested weekly habit; document it loudly). `-D` repeats like sync's and
  combines with `-n`; dates merge ascending. N in 1–366 (same bound as sync).
- Queue: future `Inclusion::Task` events with `!organizer_is_self` and answer
  Yes/Maybe, unacked, in time order. `-a` adds Context/Omitted externals with
  their reason shown (never the default). Already-synced rows are included —
  ack is about triage, not about row existence.
- Acked = **live explicit `gcal.ack`** (event or series scope, account
  matches, not cleared) **OR live private note** (same scopes). Cleared
  either side does not count. Series ack covers every instance; series note
  already does.
- Recurring instances: default scope `event` (one instance); prompt offers
  `A` (this + series choice like `note`'s This/All picker) or accept `-s`
  non-interactively — same contract as `note -s` (TTY asks, off-TTY requires
  `-s`, exit 2 otherwise).
- Storage: `gcal.ack` in `.bob/gcal/<host>.jsonl`:
  `{v, ts, host, kind: "gcal.ack", account, key: {calendar_id, event_id} |
  {calendar_id, series}, scope, seen: {title, start, ical_uid,
  original_start}}`. Fold last-writer-wins exactly like notes; `cleared: true`
  tombstone via `bob gcal ack -c`. Notes survive `sync -F`; acks must too.
  `load_state` skips `gcal.ack` for occurrence folding (as it does notes);
  `doctor` gains an ack section (counts, orphans, malformed, stale-`seen`
  warnings) mirroring the notes check.
- JSON (`-f json`): `{schema_version, window, events: [{day, time, title,
  calendar_id, event_id, series, answer, inclusion, organizer, root, acked,
  ack_source: "ack"|"note"|null, ack_stale: bool, fragile_directives}]}`.
  Never note/ack text — same redaction rule as notes.
- TTY loop per event (beautiful + fast): header line
  `Wed 11-19 · 10:00–11:00 · Deerwood breakfast · from <organizer> · ● family`,
  second line `root → <proposed root> · clock → <on/off> · no note yet`; then
  ` [a]ck · [n]ote · [e]dit note · [A]dopt Google lines · [s]kip · [q]uit · [?]help`.
  Single keypress, no Enter. `n` reads one TEXT line with the full note
  grammar (`@route`, `#off/#on`, `-30 reason`, prose; `--` verbatim); empty
  line cancels back to the prompt (it must NOT save an empty note — that is
  `clear`). `e` opens `$VISUAL/$EDITOR/vi`; `A` forwards to the adopt path.
  After save, immediately advance. `q` exits 0 having saved prior decisions
  (journal appends are per-event, after each write — never batch at the end).
- Off-TTY: print the queue (human table or JSON) and exit 2 when prompting
  would be needed — byte-identical contract to the `note` numbered picker.
- Help/discovery: `bob gcal` top help gains one line
  (`bob gcal ack -n 7  Triage next week's external invites`); `ack --help`
  states the gmail-name correction once ("for Gmail threads see `bob gmail`")
  so the slip does not recur.

### 5.2 Sync warning: managed `⚠ UNACKED`, not title graffiti

- On row create (and on row update while still unacked), sync inserts
  `⚠ UNACKED` immediately before `[root::]` (after badges/clock/buffer) for
  Task-inclusion externals with no live ack/note. The token is sync-managed:
  journaled in `gcal.row` alongside `note: {hash, fields}` (add
  `ack: {state}` or extend provenance), re-applied while unacked, removed on
  the first sync after an ack/note lands — including past-day closes and
  born-done rows. A hand-removed token is re-added while unacked (like the
  stamp), with no `kept_*` warning (it is debt, not a user edit to respect).
- Human output: `sync` human rows render the token in yellow + a trailing hint
  on first appearance per run:
  `hint: 2 unacked external events · bob gcal ack -n 7`. JSON rows add
  `acked: false, ack_source: null`. `list` shows the same token/fields so the
  warning is visible before sync writes anything.
- Why this position: it never touches Google-owned spans (no `kept_edit`
  fights), never crosses the `^id`, parses with the existing span splitter
  (`lifecycle::split_row_spans` — the token must be added to the
  vault-adjacent grammar and its tests), and survives all-day/context
  exclusion because it only ever renders on Task rows.
- "Hard to miss" without fatigue: the token is per-row (visible in the daily
  note, which is where Bryan lives) plus ONE summary hint per run — never a
  per-row stderr scream. Color via the existing `Styler` (yellow, dim
  non-TTY).

### 5.3 `list` changes (preview before write)

`bob gcal list` gains the same `acked`/`ack_source`/`ack_stale` columns
(human: `⚠` + dim `unacked`; JSON fields) and the ⚑ fragile hint stays. This
matters because Bryan triages with `list`/`ack` before `sync` ever runs.

### 5.4 Stale acks

When Google's current `seen` (title/start/ical_uid) differs from the ack's
recorded `seen`, `list`/`ack` print `ack stale · moved/renamed?` and JSON sets
`ack_stale: true`. Sync keeps the row marked unacked-warning but does NOT
auto-clear the ack (attendance evidence must never vanish silently). Re-acking
refreshes `seen`. `doctor` counts stale acks.

### 5.5 The weekly reminder (vault, not repo)

One line in `~/bob/gtd_daily.md`, placed with the other Monday-weekly rows
(Bank import / Weekly review group), and **replacing** the daily
`#browser Review next week in Google Calendar` row (delete that row in the
same edit, or the two reminders permanently duplicate):

```md
- [?] #task #gtd #pre #browser **Triage next week's external invites**: Run `bob gcal ack -n 7` · ack or note each ⚠ row · nothing new? completing this is the record  [repeat:: every week on Monday when done]  [created:: 2026-11-12]  [scheduled:: 2026-11-19]
```

Rationale: Monday + `-n 7` covers the full coming week including today; `when
done` matches every other checklist row; `#pre #browser` matches the row it
replaces so walk behavior is unchanged; the ⚠ ties the task text to the exact
marker sync renders. If Bryan prefers keeping a daily glance, downgrade the
daily row to non-checklist prose instead — never two checklist rows for one
job.

## 6. Requirement adjustments (explicit — do not implement as literally stated)

1. **Rename to `bob gcal ack`.** The request says `bob gmail ack`; Gmail
   has no ack concept and the queue is Calendar events. Ship `gcal ack`;
   mention `bob gmail` once in help to close the loop.
2. **Default the queue to Task-inclusion externals (Yes/Maybe,
   `!organizer_is_self`).** "Every external event" would include declined,
   cancelled, unanswered (`Omitted("reply in Calendar")`), all-day, and free
   events. Gate the default; put the rest behind `-a/--all` with reasons.
3. **Keep `-n` but document the mirror.** Sync `-n` looks backward, ack `-n`
   looks forward. Keep `-n|--next-n-days` for symmetry with
   `--last-n-days`, default `-n 7`, bound 1–366, combines with `-D`. Help
   must say "next … including today" in the first words.
4. **Note-as-ack stays, but empty text never counts.** A live note in either
   scope counts; a cleared note and an empty TEXT line do not. The ack loop's
   Note branch reuses the `note` write path (grammar, `-d`, `-e`, `-A`,
   `-c`, `-s`, `BOB_GCAL_ASSUME_TTY`) rather than reimplementing it.
5. **Single-keypress loop AND scriptable planning.** TTY: `a/n/e/A/s/q/?`
   with no Enter. Non-TTY: print queue, exit 2 when a choice is needed.
   `-f json` and `-d` never prompt. The Mac client consumes JSON only.
6. **Sync still creates the rows; the warning is a managed token, not title
   graffiti.** Position: after badges/clock/buffer, before `[root::]`;
   journaled; auto-removed on ack; one summary hint per run. No per-row
   stderr, no title edits, nothing after `^id`.
7. **Weekly Monday reminder replaces the daily review row.** Ship the exact
   line in §5.5 and delete/retire
   `#browser Review next week in Google Calendar` in the same vault edit.
   A daily glance + a weekly triage queue for the same job guarantees one of
   them is always stale.

## 7. Implementation sketch (for the implementer, not this report's job)

- `src/native/gcal/cli.rs`: `ack_command()` + `AckArgs` (alphabetical args,
  every long has a short; `-n/--next-n-days`, `-D/--day` repeatable,
  `-a/--all`, `-d/--dry-run`, `-f/--format`, `-q/--quiet`, `-s/--scope`,
  `-i/--event-id`, `-C/--calendar`, `-c/--clear`); top help + `ack` after-help
  with the sync-mirror note and the gmail-pointer line. Add `ack` to
  `mod.rs::run` dispatch; preferred: no trailing TEXT on ack itself — Note
  reads it interactively or via `--` passthrough to the shared writer.
- `src/native/gcal/journal.rs`: `gcal.ack` record, fold, clears, orphans;
  `NoteBook`-parallel `AckBook`; `load_state` skips acks for occurrence
  folding; malformed counting mirrors notes.
- New `src/native/gcal/ack.rs`: window resolution (next-N incl. today +
  `-D`), queue build on `classify` + `!organizer_is_self` + ack/note lookup +
  `ack_stale` compare, TTY loop (single-keypress reader with `?` help),
  JSON/human planners, per-event journal appends.
- `src/native/gcal/list.rs`, `sync.rs`, `plan.rs`, `render.rs`,
  `lifecycle.rs`: `acked`/`ack_source`/`ack_stale` plumbing; UNACKED
  tokenize/render/journal; `past_open`-style summary hint; born-done and
  past-day-close carry the token until acked.
- `src/native/gcal/doctor.rs`: ack section (counts, orphans, malformed,
  stale, foreign-account).
- Docs: `docs/gcal.md` (Sync + ownership table + JSON fields), extended
  `docs/gcal-notes.md` § ack vs note, `just docs-gen`, `just docs-check`.
  Decision record for the UNACKED token + `gcal.ack` keying (it constrains
  `mac-capture-is-a-thin-client` consumers to JSON).
- Tests: new `tests/gcal_ack.rs` (queue gating, note-counts-as-ack, clears,
  series scope, stale-seen, non-TTY exit 2, `-d` no-write, `-f json`
  redaction); extend `gcal_sync.rs` (token add/remove round-trip, born-done,
  `-F` keeps acks) and `gcal_list.rs` (columns/JSON). TTY paths under
  `BOB_GCAL_ASSUME_TTY=1`. Gate: repo's `just check`.
- Vault edit (separate from the release train — `bob-cli` ships via the daily
  train, at most one version per New York day, never hand-editing
  `Cargo.toml`/CHANGELOG): apply the §5.5 line swap in `~/bob/gtd_daily.md`.

## 8. Open questions for Bryan

1. Should a **series ack** cover all future instances, or should high-stakes
   series force per-instance ack? (Recommend: series covers all;
   per-instance always available via default scope.)
2. Should unanswered invites (`Omitted("reply in Calendar")`) appear in
   `ack -a`, or stay invisible until answered? (Recommend: `-a` only.)
3. Keep or kill the daily "Review next week" row when the Monday triage lands?
   (Recommend: kill it per §5.5.)
4. Should `ack_stale` ever auto-clear (e.g. time-only change under 15 min), or
   always require re-ack? (Recommend: never auto-clear; warn only.)

## 9. Sources consulted

Code: `src/native/gcal/cli.rs` (`build_cli`, `note_command`, `sync_command`,
`last_n_days_arg`, `rewrite_gcal_argv`), `src/native/gcal/mod.rs` (`run`),
`src/native/gcal/model.rs` (`organizer_is_self`, `organizer_or_no_guests`,
`my_answer`, `apply_notes`), `src/native/gcal/classify.rs` (`classify`,
`Inclusion`), `src/native/gcal/journal.rs` (`NAMESPACE`, `NoteBook`,
`FoldedNote`, `MAX_NOTE_BYTES`), `src/native/gcal/note.rs`,
`src/native/gcal/render.rs` (`render_task_row`), `src/native/gcal/list.rs`
(fragile ⚑ hint, `past_open`), `src/native/gcal/sync.rs`, `stamp.rs`,
`ui.rs`, `src/native/gmail/cli.rs` (no ack today). Docs: `docs/gcal.md`
(Sync, ownership table, JSON), `docs/gcal-notes.md` (Model/Grammar/Precedence/
Storage/Ownership/Reliability/Command), `docs/date-marks.md` (`repeat::`
grammar), `docs/command-catalog.md` (checked, no ack entry). Memory:
`cli_rules.md`, `docs.md`, `obsidian.md` (all via `sase memory read`);
decisions `bob-gcal-is-read-only-and-proposes-once`,
`calendar-events-are-daily-note-event-tasks`,
`ended-synced-meetings-are-born-done`, `gcal-root-follows-google-until-edited`,
`private-event-notes-beat-google-per-field`, `sync-sorts-event-task-links`,
`meet-filing-follows-google-until-edited`, `mac-capture-is-a-thin-client`;
glossary `event-task`. Vault: `~/bob/gtd_daily.md` (current PRE/POST + weekly
rows, read 2026-11-12). Peer swarm reports: not located, opened, or read, per
the swarm instruction (only filenames listed to avoid overwrite).
job.
