# Untracked time, tracked honestly: design for off-clock Pomodoros in `bob stats` and the Stats dash

Research report — `mus` (independent swarm member, no peer reports consulted).
Date: 2026-11-01. Workspace: `bob-cli` epic `bob-cli-f6`.

Question: after `bob-cli-f6` made an `#untracked` Google Calendar event land as an
`#untracked` Event Task linked under a MEET Pomodoro that is "on the ledger, off the
clock", should we start tracking those Pomodoros as a separate "untracked" group of
stats? The prompt proposes (a) a `u::` task property to keep the duration, (b) a Stats
dash + `bob stats` toggle for just-untracked and all-time views, (c) a generalized /
renamed concept, (d) a new glossary term, and (e) a rule that a Pomodoro is untracked
iff all its task links carry `#untracked`.

Short answer: yes, expose untracked time — but do not add `u::`, do not rename the
stored concept, and do not derive trackedness from links at read time.

## Recommended solution (TL;DR)

1. Keep absence of `[t::]` as the single stored fact. A timed ledger row with `[t:: Nm]`
   (or legacy stopwatch) is tracked; a timed row without either is untracked; `()` is a
   placeholder. This is
   [`decisions:untracked-sessions-omit-t-field`], `docs/reference/vault-format.md:322-328`,
   and `src/native/capture/pomodoro_adjust.rs:759-777` (`SessionTracking`). Do not add
   `[u:: Nm]`. The span (`**HHMM-HHMM**`) already stores the duration — see
   `src/native/stats/index.rs:597-601` (`range_minutes`) — and every reader already
   skips untracked rows' minutes and counts. The work is to surface that span as a
   parallel aggregate, not to write a new field.
2. Add a display-time scope, default tracked. `bob stats` / `bob stats show` gain one
   enum flag (for example `--time-scope tracked|untracked|all`, short `-T`), default
   `tracked` so current output is byte-identical. The engine always computes both
   aggregates in one vault pass and the JSON always carries both (additive
   `untracked_minutes` / `untracked_sessions` beside existing `minutes` / `sessions`);
   the flag only selects what human/CSV rendering shows. `dash_stats.md` (`bob-stats`
   block, `docs/stats.md:977-1071`) gains a matching three-way segmented control
   (Tracked | Untracked | All) that re-renders the already-loaded report without
   refetching. Day strip stays tracked-only; window bars stay tracked-only.
3. Keep the name `untracked session` as canonical, add `off-clock` as the display alias.
   New glossary strand `glossary:untracked-session` (aliases: off-clock session, calendar
   hold): "a closed timed ledger row without `[t::]`, on the ledger and off the clock;
   its span still records how long it lasted, but default minutes, counts, homes, Day
   strip, `bob pomodoro --worked`, and agenda `completed_summary` exclude it." This keeps
   the `decisions:untracked-sessions-omit-t-field` record, `docs/gcal.md`,
   `docs/stats.md:128-132`, and the plan's naming-collision guard intact while giving the
   UI honest copy ("off the clock, still timed").
4. Do not define untrackedness as "iff all task links carry `#untracked`". Keep
   writer-decides / reader-looks-at-the-row. Writers already implement the write-time
   equivalent (sync splits past clusters by trackedness, MEET starts follow the event
   run — `src/native/gcal/plan.rs`, `docs/capture.md:3090-3101`). Add a lint that warns
   when a row's stored trackedness disagrees with its links instead of re-deriving it in
   every reader.
5. Ship in this order: engine dual aggregates → CLI flag + `bob pomodoro --worked`
   flag → dash toggle + Day-strip copy → vectors/goldens/docs/decision update → glossary
   strand. Every JSON change additive with `decodeIfPresent` fallbacks, per the
   `bob-cli-f6` cross-repo rule (`sase/repos/plans/202611/untracked_calendar_events.md:513-575`).

The rest of this report gives the evidence, the critique of each sub-proposal, the
concrete CLI/JSON/UI contract, and what to explicitly reject.

## 1. Where untracked stands today (evidence, not assumption)

The `bob-cli-f6` epic is mid-flight (epic `IN_PROGRESS`, phases `.1`–`.5` and `.7`
closed, `.6`/`.8` open — `sase bead read bob-cli-f6`). Its chosen representation is
minimal and already landed:

- Stored fact: `src/native/capture/pomodoro_adjust.rs:769-777` —
  `session_tracking(ledger_line)` returns `Tracked { minutes }` when
  `duration_from_range_text` finds `[t:: Nm]` or the legacy stopwatch, `Untracked` when
  the line is timed but has neither, `Placeholder` for `()`. `src/native/pomodoro.rs:16`
  re-exports it for every reader.
- Writers preserve absence: `format_adjusted_range` callers in
  `capture/pomodoro_adjust.rs` (adjust/shift) and `capture_pomodoro_close/ledger.rs`
  keep an untracked row as `(**HHMM-HHMM**)` with other metadata intact; closes keep it
  untracked (`src/native/capture_pomodoro_close/tests.rs:235` pins this).
- Event-task input: `src/native/event_task.rs:567` (`line_has_untracked_tag`) plus
  `events_in_note`, `first_event_start_crossed`, `cluster_by_trackedness`. Google sync
  strips `#untracked` from the displayed title, renders it at the end of the badge run
  before `[root::]` (`src/native/gcal/render.rs:40-69`), splits past MEET clusters by
  trackedness, and makes a running MEET untracked only when every current event is
  (`src/native/gcal/plan.rs:510-519`). `docs/gcal.md:481-510` and
  `docs/reference/vault-format.md:356-385` own the contract.
- Readers exclude: `src/native/stats/metrics.rs:216-218` (`continue` on
  `session.untracked` for both `minutes` and `count`, per the `untracked_counts =
  exclude` reviewer decision); `src/native/stats/session_facts.rs:18-25` maps untracked
  to `(Some(0), Ok)`; `src/native/stats/homes.rs:202-206` skips minutes and bumps
  `health.homes.untracked_sessions`; `src/native/capture_pomodoros.rs:479-514`
  (`completed_summary_for`) counts `untracked_count` separately so `bob pomodoro
  --worked` (`src/native/pomodoro.rs:99-110`) and the agenda `completed_summary`
  (`src/native/capture_pomodoros_agenda.rs:245-250`) stay tracked-only;
  `src/native/stats/index.rs:586-612` stores `untracked`, `recorded_minutes: None`,
  `range_minutes: Some(span)`. `src/native/pomodoro_homes/session.rs:95-101` attributes
  0-minute parts with `untracked: true` (`src/native/pomodoro_homes/json.rs:49`).
- UI word is already "dashed means off the clock": Obsidian Event time pill, home chips,
  and the Mac Calendar band/rail all use a dashed outline for untracked
  (`sase/repos/plans/202611/untracked_calendar_events.md:197-223,480-560`).
- Docs already guard the name collision the prompt worries about: `bob stats` calls days
  without data "untracked points" (`src/native/stats/compute.rs`,
  `docs/stats.md:310-343`), so code uses `SessionTracking::{Tracked, Untracked}` and
  docs say "untracked session" (`untracked_calendar_events.md:252-255`).

In short: duration is not lost today. Every closed untracked row still carries its span,
and `range_minutes` is indexed. What is missing is a counted view of it.

## 2. Is this a good idea? Critique of the plan in general

Yes — with two guardrails.

Why it is worth doing: Bryan already asked for lunch/school-pickup/gym to be "on the
calendar and off the clock." Right now off-the-clock is invisible in the only place he
reviews time (`bob stats`, dash, Day strip, `--worked`). That creates three real costs:
(1) the day looks shorter than it felt, so capacity planning misfires; (2) calendar
holds cannot be audited ("how much of Tuesday was holds?"); (3) the honest ledger ("I
was in lunch 1200-1300") has no honest total. A separate, opt-in untracked group fixes
all three without touching the default headline numbers that the `exclude` decision
protects.

Why it needs guardrails:

- The default must stay tracked-only. `untracked_counts = exclude` was an explicit
  reviewer decision ("Should an untracked session also drop out of Pomodoro counts, not
  just minutes?" → exclude). Flipping the default would rewrite history, inflate `worked`
  / `sessions` / Day strip / homes, and break every golden that pins the current
  behavior (`src/native/stats/metrics.rs:1969`,
  `src/native/stats/compute.rs:1182-1186`). The toggle must be opt-in, and human output
  with no flag must stay byte-identical.
- Do not relitigate representation. The epic already rejected `[t:: 0m]` (reads like a
  bug, still counts a Pomodoro), `#untracked` on the Pomodoro line (new grammar in Rust,
  JS, and Swift parsers), and read-time link derivation (opaque, needs resolution
  everywhere, no per-session override) — `untracked_calendar_events.md:257-262` and
  `decisions:untracked-sessions-omit-t-field`. Any new proposal that reopens one of
  those needs to beat the cited evidence (0-of-1226 vault scan, three-parser cost), not
  just restate the wish.

## 3. `u::` — do not add it

Proposal: write untracked duration as a `u::` task property (for example
`(**1200-1300** [u:: 60m])`) so the minutes survive somewhere explicit.

Recommendation: reject. It solves a problem that does not exist and reopens a settled
representation question.

- The duration already survives. An untracked row keeps its span, and the index keeps
  `range_minutes` (`src/native/stats/index.rs:597-601`). `range_minutes` is exactly "the
  duration of each untracked Pomodoro somehow." No new field is needed to answer "how
  long was lunch?" — `1300-1200` is the answer, in both the note and the index.
- A new inline field is the most expensive possible change. `[t::]` is parsed by Rust
  (`duration_field_value` in `pomodoro_adjust.rs:793-801`), by the JS clock parser and
  the Obsidian Event painter (`split_row_spans`), and by Swift in Bob Mac Capture. The
  plan deliberately put `#untracked` at the end of the badge run so "every existing
  parser still finds span, title, and `^id`" (`untracked_calendar_events.md:171-178`).
  A `[u::]` on the ledger line would need the same three-parser update plus Tasks
  plugin (`Dataview` format) compatibility work, new escaping rules, and golden updates
  — for information the span already carries.
- It confuses the two clocks. Today `[t:: Nm]` means "counted minutes" and the span
  means "wall span"; they can differ (late-join clamp, early-start truthfulness,
  close-before-start clamp — plan `meet-event-run` §6-8). Adding `[u:: Nm]` invites a
  third semantics: is it wall span (redundant) or counted-but-excluded minutes (then why
  not just count it)? The plan rejected `[t:: 0m]` because it "reads like a bug"; `[u::
  60m]` reads like a second bug next to the span.
- It breaks the writer-decides invariant. Writers today decide trackedness by omitting
  or keeping `[t::]`; readers only look at the row
  (`decisions:untracked-sessions-omit-t-field`). A `[u::]` field would need writers to
  keep span and `u::` in sync on every adjust/shift/close/retime path that currently
  just preserves absence — doubling the round-trip tests in `capture_pomodoro_close`
  and `pomodoro_adjust` for no new capability.

What to do instead: in the stats engine, treat `range_minutes` as the untracked
duration. Add parallel aggregates (`untracked_minutes`, `untracked_sessions`) computed
from `range_minutes` for `session.untracked == true`, and surface them in JSON. No
ledger change, no parser change, no vault rewrite. If a future case genuinely needs an
explicit override (for example a partially-attended hold where wall span overstates the
hold), handle it as a hand edit that adds `[t::]`-style explicitness then — but do not
pre-build the field now.

Minor adjustment to the requirement, clearly called out: drop the `u::` line item. The
goal "still track the duration somehow" is already met by the span; the feature work is
display, not storage.

## 4. Toggle design — one enum, always dual-computed, additive JSON

Requirement: Stats dash and `bob stats` need a way to toggle to untracked time,
preferably "just untracked" and "all time, including untracked."

Recommendation: one `--time-scope` enum on `bob stats` / `bob stats show`, plus a
matching dash segmented control. Do not ship two booleans (`--include-untracked` +
`--only-untracked`): they combine into four states for three meanings and invite
`--only` without `--include` bug reports. A single enum has three spellings for three
meanings and a clean default.

CLI contract (follows `sase/memory/cli_rules.md`: alphabetical options, every public
long has a short, excellent help):

- `bob stats [--time-scope tracked|untracked|all] [-T ...]` and the same on
  `bob stats show`. Default `tracked`. Short `-T` is free (`src/native/stats/cli.rs`
  uses `a,b,c,f,g,h,o,r`; `t` is unused and alphabetically adjacent to `range`/`offset`
  help). Help line: "Which sessions to count: tracked (default), untracked, or all".
  `bob stats metrics` needs no flag (it lists definitions, not points).
- `bob pomodoro --worked` gains `--include-untracked` (short `-U`? check `pomodoro.rs`
  shorts `-w/--worked`, `-v/--verbose`; pick the next free letter and keep help
  alphabetical) that prints `WORKED 1h 15m + 1h off-clock` style, or a second line when
  color helps. Default stays tracked-only so tmux/menu-bar consumers do not move.
- Engine: extend `StatsRequest` (`src/native/stats/request.rs:27-44`) with
  `time_scope: Tracked | Untracked | All` (default `Tracked`). Evaluate pomodoro-kind
  metrics twice in the same vault pass — once over `!untracked`, once over `untracked`
  using `range_minutes` — and keep both in the report. Human/CSV render selects by
  scope; JSON always carries both. This keeps `bob` the single owner of metric meanings
  (`docs/stats.md:114-120`) and keeps the Mac/Obsidian clients thin
  (`decisions:mac-capture-is-a-thin-client`): the dash toggles views without refetching.
- JSON (additive, `decodeIfPresent`-safe): on each pomodoro-kind `SeriesPoint` add
  `untracked_minutes` / `untracked_sessions` (omitted when zero, mirroring
  `CompletedSummary.untracked_count` in `capture_pomodoros_agenda.rs:245-250`); on the
  report add `health.homes.untracked_minutes` beside `untracked_sessions`
  (`src/native/stats/report.rs:320-337`); on `sessions[]` facts keep the existing
  `minutes: 0` for untracked in tracked scope but add `range_minutes` / `untracked:
  true` so the dash can list holds without a second fetch. Document in
  `docs/reference/json-outputs.md` and `docs/stats.md`; regenerate with `just docs-gen`
  and gate with `just docs-check`.
- Human rendering (`src/native/stats/render.rs:41-59`): tracked scope is byte-identical
  to today. `untracked` scope swaps the headline `worked`/`sessions` to the untracked
  aggregates and tints them muted/dashed (see §7 for the visual language). `all` scope
  shows `worked 3h 05m · includes 1h off-clock` and stacks the bar (solid tracked +
  hatched/dashed untracked) rather than mixing the numbers silently. CSV gains the same
  two columns so spreadsheets do not need a second run.
- Dash (`docs/stats.md:977-1071`, `dash_stats.md` `bob-stats` fence): a small segmented
  control above the focus chart — Tracked | Untracked | All — that re-renders the
  already-loaded report. Default Tracked. Untracked view reuses the "Where the time
  went" grouping (root parent, then types) fed by the untracked parts; tiles show the
  untracked total with the dashed off-clock pill. All view shows tracked bars with a
  dashed untracked overlay and a footer line "includes X off-clock". Keyboard: `t` cycles
  the three ( Obsidian-safe, documented in `docs/stats.md` controls section). No new
  fetch, no new fence parameter — view-only state like range chips and Table toggle.
- Day strip (`glossary:day-strip`, `docs/stats.md:1335-1404`): stays tracked-only. It
  answers "did the day move work forward" in five facts; adding holds there would dilute
  the only glanceable work signal. Holds get their own glanceable surface (the dash
  toggle + agenda Calendar band), not a sixth Day-strip fact.
- Reliability: the `not_tracked` quality (`DataQuality::NotTracked` in
  `render.rs:188`, `docs/stats.md:310-343`) means "before tracking began / missing
  journal", not "an untracked session". Keep the words apart in help and tooltips:
  never label an untracked session "not tracked". The plan's collision guard already
  requires this; the toggle copy must obey it too.

## 5. Generalize and name it — keep `untracked session`, add `off-clock` as display

Requirement: generalize "untracked pomodoro" since the time will technically still be
tracked, and add an excellent glossary term.

Recommendation: do not rename the stored concept. Generalize the docs sentence, not the
ledger word.

- Why not rename: `untracked session` is already the canonical phrase in the accepted
  decision (`decisions:untracked-sessions-omit-t-field`), the vault contract
  (`docs/reference/vault-format.md:322-328`), stats (`docs/stats.md:128-132`), gcal
  (`docs/gcal.md:481-510`), and homes (`docs/pomodoro-homes.md:150-151`). Renaming to
  "excluded", "shadow", "hold", or "private" would orphan that record, churn every doc,
  and collide elsewhere (`excluded_themes`, `exclude_in`, "private" notes). The
  "technically still tracked" worry dissolves once the definition says the span is
  still recorded but excluded from default aggregates — which is exactly what "off the
  clock" already means in the plan ("on the calendar and off the clock").
- What to generalize: today the docs tie untracked sessions to calendar Event Tasks
  ("An `#untracked` tag keeps the session that links it off the clock"). Loosen that one
  sentence to cover hand-made holds too: any timed row without `[t::]` is untracked,
  however it got that way (calendar run, hand-deleted `[t::]`, future manual hold). The
  tag stays the common input; the row stays the record. That is the generalization —
  no new kind needed.
- Display alias: use `off-clock` in UI copy (dash toggle, `--worked` suffix, tooltips,
  dashed pill) while keeping `untracked` in stored/JSON/CLI-value copy. Both words are
  already in the repo ("off the clock" in the plan and vault-format; `untracked` in code
  and JSON), so no new vocabulary has to be taught — just a consistent mapping: stored
  `untracked`, shown `off-clock`.

Proposed glossary strand (new file `sase/memory/glossary/untracked-session.md`,
type requested, aliases `off-clock session, calendar hold`):

> # Untracked Session
> A closed timed ledger row without `[t::]` (or legacy stopwatch) — on the ledger, off
> the clock. Its span still records how long it lasted, but default minutes, counts,
> homes, Day strip, `bob pomodoro --worked`, and agenda `completed_summary` exclude it;
> use the untracked / all scope to see it. Writers decide trackedness when they write
> the span (sync splits past clusters by trackedness; MEET starts follow the event run);
> readers only look at the row. An `#untracked` Event Task is the common input, not the
> definition: any timed row without `[t::]` qualifies, however it lost the field. Not a
> `not_tracked` quality point, not `[t:: 0m]`, not a placeholder `()`. See
> `decisions:untracked-sessions-omit-t-field`, `glossary:event-task`,
> `glossary:pomodoro`, `glossary:stats-dash`.

This satisfies "excellent new term" without a rename migration: one strand, two
aliases, four links, and a definition that already matches the code.

## 6. "Untracked iff all links carry `#untracked`" — do not adopt as a read rule

Proposal: a Pomodoro is untracked iff every task link in it points at a task with the
`#untracked` tag.

Recommendation: reject as a read-time rule; keep it as a write-time heuristic plus a
lint. It is already half-true at write time and fully wrong at read time.

- It contradicts the accepted invariant. `decisions:untracked-sessions-omit-t-field`
  says "writers decide … readers only look at the row" precisely because "deriving
  trackedness at read time from links would be opaque, need link resolution in every
  reader, and cannot be overridden per session." Adopting iff-at-read would reintroduce
  all three costs the epic paid to remove.
- Link resolution is expensive and ambiguous. Every stats/homes/agenda/`--worked`
  reader would need vault link resolution (basename, parent-ancestry, `[root::]`
  reporting-only walks — `glossary:root-parent`) just to classify a row. Mixed lineups
  (one `#untracked` lunch + one tracked standup under one MEET) have no honest iff
  answer; unlinked sessions have no links at all; hand-added `[t::]` overrides ("count
  this hold just today") would become unrepresentable; and the three parsers (Rust, JS,
  Swift) would need to agree on tag scoping (code spans, Markdown links, `#untracked`
  inside `LINKS:` vs task body) that today lives in one helper
  (`line_has_untracked_tag`).
- The write-time version already exists and is enough. Sync splits past clusters by
  trackedness and makes a running MEET untracked only when every current event is
  (`src/native/gcal/plan.rs:510-519`); MEET starts follow the run's trackedness
  (`docs/capture.md:3090-3101`). That is "iff all linked events are untracked" applied
  once, where the lineup is known — not re-derived on every stats run.
- What to do instead: add a `kept_untracked`-style lint (the sync already reports
  `kept_edit` / `kept_untracked` once) that warns when a closed row's stored
  trackedness disagrees with its current links ("tracked row links only `#untracked`
  tasks — remove `[t::]`?"). Warn, do not reclassify. This catches the drift the iff
  rule worries about without making stats depend on task tags.

Adjustment to the requirement, clearly called out: change "should be untracked iff …"
to "writers set untracked when the run is all-`#untracked`; readers never re-derive; a
lint reports drift."

## 7. Beautiful, intuitive, reliable — the details that decide it

- Intuitive default: tracked-only everywhere until the user asks. The toggle is an
  explicit scope, not a quiet inclusion. `all` never silently sums two qualities into
  one number — it always labels the off-clock part ("3h 05m · includes 1h off-clock").
- Beautiful: extend the existing dashed language, do not invent a second one. Untracked
  rows, pills, home-hue dots, rail capsules, and dash bars all stay dashed-outline +
  muted ink (already spec'd for Obsidian, Mac band, and rail). In `bob stats` human
  output use the styler's muted/dim path (`src/native/stats/cli.rs:16`,
  `render::overview`) for untracked numbers, never a new hue that fights theme colors
  (`glossary:task-type` hue precedence stays untouched).
- Reliable: one vault pass computes both aggregates; repeated runs with fixed `BOB_NOW`
  stay byte-identical (`docs/stats.md:114-120`). No ledger migration (0-of-1226 scan
  already proved safety). No `capture` grammar change (plan §"No new capture grammar").
  No `bob task <verb>` nesting (read-only reports stay top-level per `cli_rules.md`).
  Full `just check` + `just docs-check` + copied-vector lockstep (`pomodoro_homes`,
  `meet_event_run`) as in the epic's verification §.

## 8. Recommended build (phased, additive, no migration)

1. Engine: `StatsRequest.time_scope`; pomodoro-kind metrics compute tracked
   (`recorded_minutes`) and untracked (`range_minutes` where `untracked`) in one pass;
   `SessionFact` keeps `minutes: 0` for untracked in tracked scope but always carries
   `range_minutes`/`untracked`; `HomesHealthReport` gains `untracked_minutes`. Unit +
   golden tests extend `metrics.rs:1969` and `compute.rs:1182-1186` with a mixed day
   (tracked BOB + untracked lunch) asserting tracked default unchanged and both scopes
   correct.
2. CLI: `--time-scope` on overview/show (`just docs-gen` + `docs/reference/cli/stats.md`
   + `docs/stats.md` catalog); `--include-untracked` on `pomodoro --worked`. Help sorted
   alphabetically with shorts; no renames (old spellings stay hidden aliases per
   `cli_rules.md` — here there are none, so nothing to alias).
3. Dash + Day strip: segmented Tracked | Untracked | All on `bob-stats` (view-only,
   no fence-param change); window bars and Day strip stay tracked-only; tooltips never
   say "not tracked" for untracked sessions.
4. Lint + vectors: trackedness-vs-links drift lint; new stats vectors pinning
   `untracked_minutes`/`untracked_sessions`; copy `pomodoro_homes`/`meet_event_run`
   vectors byte-for-byte to `bob-plugins` per the epic lockstep rule.
5. Memory + docs: one new `decisions` note only if scope semantics change the
   `untracked-sessions-omit-t-field` cost section ("untracked sessions are excludable,
   not invisible"); one new `glossary:untracked-session` strand above; `docs/gcal.md`,
   `docs/stats.md`, `docs/reference/vault-format.md`, `docs/capture.md` updates for the
   scope flag only. Run `sase memory init` to republish.

Explicitly rejected: `[u:: Nm]` ledger field; `[t:: 0m]` for holds; `#untracked` on the
Pomodoro line; read-time iff-from-links; two-boolean CLI flags; default-all or
default-include; Day-strip sixth fact; new hue for untracked; `bob task`-nested stats;
`capture`-grammar change.

## Appendix — key sources checked

- Plan + epic: `sase/repos/plans/202611/untracked_calendar_events.md` (esp. one-page
  design, decisions `untracked_counts = exclude`, naming guard, verification);
  `sase bead read bob-cli-f6` / `bob-cli-f6.1`.
- Decisions/glossary (via `sase memory read`): `decisions:untracked-sessions-omit-t-field`,
  `decisions:synced-meetings-link-by-phase`, `decisions:today-is-read-from-the-ledger`,
  `decisions:mac-capture-is-a-thin-client`, `glossary:pomodoro`, `glossary:task-link`,
  `glossary:event-task`, `glossary:stats-dash`, `glossary:day-strip`,
  `glossary:task-type`, `glossary:root-parent`; flat notes `cli_rules.md`, `docs.md`.
- Ledger + index: `src/native/capture/pomodoro_adjust.rs:759-801`,
  `src/native/pomodoro.rs:16,99-110`, `src/native/stats/index.rs:86-91,586-612`,
  `src/native/event_task.rs:350-567`, `src/native/gcal/render.rs:27-69`,
  `src/native/gcal/plan.rs:68-70,388-424,510-519`, `src/native/gcal/lifecycle.rs:137-194`.
- Stats: `src/native/stats/request.rs:9-44`, `src/native/stats/cli.rs:278-417`,
  `src/native/stats/metrics.rs:200-300,1969-1993`, `src/native/stats/session_facts.rs:11-40`,
  `src/native/stats/homes.rs:82-206`, `src/native/stats/report.rs:309-337`,
  `src/native/stats/render.rs:21-59,188`, `src/native/stats/compute.rs:589-670,1182-1186`,
  `src/native/pomodoro_homes/session.rs:81-112`, `src/native/pomodoro_homes/json.rs:49`,
  `src/native/capture_pomodoros.rs:470-514`, `src/native/capture_pomodoros_agenda.rs:239-250`.
- Docs/UI: `docs/stats.md:122-200,310-343,977-1090,1335-1404`, `docs/gcal.md:373-510`,
  `docs/capture.md:3090-3138,3530-3720,7521-7566`, `docs/reference/vault-format.md:302-399`,
  `docs/reference/json-outputs.md:82,193`, `docs/pomodoro-homes.md:150-151,273,390`,
  `docs/dashboard.md:79-82`.

Swarm note: this report was written independently; no `__cdx` / `__cld` / `__grk` /
`__gem` peer report was located, opened, or consulted. Shared sources above were used
directly.
