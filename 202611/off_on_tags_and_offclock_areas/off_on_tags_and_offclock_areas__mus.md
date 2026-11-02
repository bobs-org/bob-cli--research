# `#off` tag, deprecated aliases, `offclock:` frontmatter, and `#on` override

Research report (swarm member `mus`). Question: how should bob-cli adopt `#off`
as the canonical off-clock tag (keeping `#offclock`/`#untracked` as deprecated
read-only aliases with a `bob gcal sync` warning), migrate past event tasks to
`#off`, and add a recursive `offclock: true|false` area/project frontmatter
field with a per-task `#on` escape hatch (first use: `offclock: true` in
`~/bob/love.md`)?

## Recommendation (TL;DR)

Good plan, worth doing, with six adjustments (marked **[ADJUSTMENT]** below).
The short version:

1. Add `#off` as a fourth recognized spelling everywhere, then flip the
   **written** canonical form from `#offclock` to `#off` in one commit.
   Keep `#offclock`, `#off-clock`, `#untracked` as read-only aliases forever
   (matching the repo's permanent-hidden-alias philosophy for renames).
2. Emit the deprecation notice through the existing `SyncReport.warnings`
   vector (human + JSON), one line per Google event that used a deprecated
   spelling — in `bob gcal sync` only, not `list`.
3. Implement `offclock: true|false` as an inherited note attribute resolved
   over the existing `parent: [[...]]` chain, consulted at **write time**
   (sync classification, close-time clock verdict, settle) — never by stats
   readers, which keep reading `[off::]`/`[t::]` history.
4. Precedence (explicit beats inherited): task-level `#on` (force on-clock)
   > task-level `#off` (force off-clock) > Google token / area default
   (OR'd) > worked default.
5. Do the vault migration as a one-shot pass, not as sync behavior. Evidence
   suggests it is tiny (possibly zero live rows).
6. Do **not** invent new subcommands, flags, or JSON fields. No CLI-rule or
   JSON-contract issues arise.

## Current-state inventory (verified in source)

The off-clock alias triple is copy-pasted as literals in four implementation
files (no shared constant exists):

| Site | File | What it does |
|---|---|---|
| Google title strip | `src/native/gcal/model.rs:425-446` (`strip_off_clock_tokens`) | removes alias, sets `off_clock=true` |
| Google description directives | `src/native/gcal/model.rs:296-297` (`is_off_clock_token`, `:415`) | `@route`-style directive lines |
| Vault row re-parse | `src/native/gcal/lifecycle.rs:210-224` (`strip_trailing_off_clock_token`) | splits Google-owned badge run |
| Vault classification | `src/native/event_task.rs:941-966` (`line_has_off_clock_tag`) | code-span/link-masked, boundary-checked |
| Second vault strip | `src/native/event_task.rs:1069-1088` (`strip_trailing_off_clock`) | title cleanup |
| Writer | `src/native/gcal/render.rs:56-58` | always writes canonical ` #offclock` |

Downstream consumers of the boolean (not the spelling): `sync.rs`
(`off_clock`/`untracked` row fields), `plan.rs` (`kept_off_clock` logic,
`format_meet_span`), `capture_pomodoro_close/linked_tasks.rs:1275`
(session verdict), `task_status_hooks/settle.rs:85` (settle gate),
`capture/event_conflict.rs` + `capture/meet_event_run.rs` (JSON `off_clock`
+ deprecated `untracked`), `capture_pomodoros_agenda.rs:923-924`
(agenda `off_clock` + deprecated `untracked`). Deprecation-in-JSON already
has precedent: `untracked`/`tracked: false` are kept as deprecated doubles
of `off_clock` everywhere (`docs/reference/json-outputs.md:82,86`,
`stats/report.rs:351`, `pomodoro_homes/json.rs:50`).

Warnings infrastructure already exists: `SyncReport.warnings: Vec<String>`
(`sync.rs:99`), populated from journal + `plan.warnings` + `kept_*` details
(`sync.rs:330-332`), rendered in human and JSON output. No new plumbing is
needed — only new warning strings.

Area/project notes already parse frontmatter with `parent: [[...]]`
wikilinks (`src/native/projects/scan.rs`; `TypedNote { stem, parent,
ready_cap_raw, ... }` at `:730-743`, walked by `walk_typed_notes`). There is
no boolean frontmatter flag yet, but `ready_cap` handling (`:805-807`) is
the exact template for parsing a new scalar. Note the YAML-scalar gotcha in
the same file (`is_yaml_non_string_scalar`, `:702-713`): bare `on`/`off`
parse as booleans — the proposal's key name `offclock` avoids this, but the
value parser must accept `true/false` (and ideally `yes/no/1/0`)
case-insensitively.

Vault evidence on migration size: a bounded scan of `~/bob` found **zero**
live `#offclock`/`#off-clock`/`#untracked` event-task rows in daily notes —
the only hits were task *text about this very rename* (`bob.md:99`,
`[id:: bob__off-tag]`) and `.bob/` internals. So "update all past event
tasks" is likely a near-no-op; the implementer must re-scan at build time,
but should not build heavy migration machinery for it.

No `#on` or `#off` standalone-tag usage exists in `src` today (verified by
grep), so neither spelling collides with an existing tag. The stats CLI
already has hidden `on`/`off` aliases for the worked/off-clock clocks
(`stats/clock.rs:54-58`) — a different namespace (CLI arg vs. vault tag),
no conflict, and mildly supporting the choice of `#off`.

## Critique and adjustments

### 1. The `#off` rename: yes, but watch the prefix trap

`#off` is a strict prefix of `#offclock`. Every matcher must therefore test
longer spellings first or use exact-token comparison. Good news: all four
sites already do the safe thing — `model.rs` compares whole whitespace-split
tokens, `lifecycle.rs` compares the whole trailing token, and
`event_task.rs` requires a non-word right boundary (`#off` inside `#offclock`
is followed by `c`, which fails `right_ok`). The implementer must preserve
these properties and extend the existing tests (`model.rs:582-603`,
`event_task.rs:1246-1272`) with `#off` cases **including adversarial ones**
(`#offclock` must still match as off-clock, `#office`/`#offer` must not).

**[ADJUSTMENT 1]** Flip the *written* canonical to `#off` in the same change
(render.rs, lifecycle rebuild paths). A rename that still writes the old
spelling never converges. Deprecated spellings become read-only: recognized
on input, never emitted.

### 2. Deprecation warnings: yes, but sync-only and per-event

The request already scopes the warning to `bob gcal sync` — keep it that
way. `bob gcal list` is a glanceable read path; warning there would noise
every listing until Google-side titles are edited (which Bryan may never do
for old recurring events). One warning line per event occurrence that
contained a deprecated spelling (title or description), worded actionably,
e.g. `Lunch: Google title uses #untracked; replace with #off`. Emit it
whenever the deprecated spelling is *observed*, regardless of whether the
row changed — otherwise already-synced events go silent and Bryan never
learns which Google titles to fix. Dedupe identical lines within a run.

**[ADJUSTMENT 2]** Do not add a JSON field or flag for this. A `warnings[]`
string entry (existing contract) is sufficient and follows the `kept_*`
precedent. Do not print any deprecation output for the *vault-side*
deprecated tags during migration — the migration itself is the fix.

No sunset: keep the aliases readable permanently. They cost three string
comparisons, and the repo's own CLI-rules memory already establishes
"never hard-remove a spelling" as house philosophy.

### 3. `offclock:` frontmatter: the best part of the proposal, with a scoping fix

A whole-area default fills a real gap — today off-clock-ness is purely
per-task-tag, so "everything about love is personal time" cannot be
expressed. The `parent: [[...]]` chain gives inheritance almost for free,
and `offclock: false` as an explicit opt-out (vs. absent = inherit) is the
right three-state design (`None` inherit / `Some(true)` / `Some(false)`),
with cycle protection on the walk.

**[ADJUSTMENT 3]** Define exactly which tasks a note's flag covers, because
"tasks belonging to that area/project" is ambiguous across the two task
homes in this vault:
- *Resident tasks* (task lines physically in `love.md` or a descendant
  note): covered by walking the residence note's parent chain.
- *Event tasks* (rows in daily notes): covered by resolving their `[root::]`
  target to a note and walking *that* note's chain. Event tasks with no
  resolvable root stay on today's behavior.
- "Child areas/projects, recursively" = the `parent:` wikilink chain, not
  file proximity. `walk_typed_notes` already returns every `(stem, parent)`
  pair needed to build the map; cache it once per command run (sync touches
  every event; per-event file reads would be the only perf risk).

Consumers to consult the resolved default, in this order of implementation:
(a) `bob gcal sync` classification (`model.rs` occurrence → needs the
resolved `[root::]` *before* classification, so this wires through
`choose_event_root` output); (b) close-time clock verdict
(`linked_tasks.rs` `LinkFact` resolution, both `:1231` and `:1260` sites);
(c) settle (`settle.rs:85`, via the same shared helper). Stats readers,
`--worked` filters, and JSON `off_clock` history fields must **not** consult
frontmatter: a session's clock is history once `[off::]`/`[t::]` is written
(glossary: "a closed row's key is history, and later tag edits are reported,
never applied"). Frontmatter edits are therefore explicitly non-retroactive
— call this out in docs, or Bryan will expect flipping `love.md` to rewrite
past stats.

### 4. `#on`: necessary, and symmetric `#off` comes free

With an area default, a per-task escape hatch is mandatory, and `#on` (force
on-clock) is the right name — it mirrors the stats CLI's hidden `on` alias.
But the proposal only names one direction. Since `#off` becomes the canonical
*task tag* anyway, the symmetric rule falls out naturally: an explicit `#off`
on the task forces off-clock even under an `offclock: false` (or default
on-clock) ancestor.

**[ADJUSTMENT 4]** Adopt the full precedence, task-tag-beats-inheritance:
`#on` > `#off` > (Google off-token OR inherited `offclock: true`) >
worked default. For Google events specifically: `#on` in the Google title
or description forces on-clock even when the area default says off (this is
the requested "sync looks for `#on`" behavior); Google `#off*` and area
default OR together. Document that `#on`/`#off` on the *vault row* likewise
override for non-event tasks at close/settle time.

### 5. Migration: one-shot pass, mind today's journal

**[ADJUSTMENT 5]** Do not make sync rewrite old tags opportunistically —
that would dirty badge spans on every sync and spam diffs. Do a single
vault-wide rewrite of `#offclock`/`#off-clock`/`#untracked` → `#off` on
event-task rows (only where `line_has_off_clock_tag` semantics confirm a
real tag, preserving code spans/links), then rely on read-compatible aliases
for anything missed. Two cautions for the implementer:
- The gcal journal (`gcal/journal.rs`, keyed by occurrence+day) stores span
  hashes of what sync wrote. Rewriting *today's or future open* rows changes
  the badge span text, so the next sync may report them as user-edited
  (`kept_off_clock` path, `plan.rs:542-577`). Migrate when no open sync
  window exists, or accept and hand-clear at most one round of warnings.
  Past (settled/closed) rows are never re-synced and are hash-safe.
- `bob.md:99` (`Rename #untracked to #off!`, `^off-tag`) is ordinary task
  text, not an event row — exclude non-event-task lines; a regex limited to
  `#task **HHMM-HHMM**` rows is the safe selector.

### 6. First use-case (`love.md`): approve, with one expectation set

Setting `offclock: true` in `~/bob/love.md` (frontmatter already has
`parent`/`type`, so the new key slots in cleanly) will move every
love-rooted session — including `[root:: love]` MEETs — to `[off::]`,
shrinking Worked and growing Off-clock in stats and the Day Strip. That is
the stated intent and the semantics are coherent (family time is off-clock).
Just make sure Bryan expects the Worked dip, and note the interaction with
`subprojects-inherit-project-blocking`-style chains: `love.md`'s own parent
is `[[area]]`, so the walk must terminate cleanly at notes without the key.

## Recommended implementation shape

1. **Centralize**: introduce one shared `OFF_CLOCK_TAGS` ordered list
   (`#off`, `#offclock`, `#off-clock`, `#untracked`) plus
   `is_off_clock_token` / strip helpers in `event_task.rs`, and rewire the
   four literal sites to it. This is the highest-value refactor in the whole
   change; it prevents the next rename from repeating today's archaeology.
2. **Token layer**: add `#off` (exact-token, boundary-checked) + `#on`
   detection (`line_has_on_clock_tag`, same masking rules) in `event_task.rs`;
   extend `model.rs` title/directive parsing with both; extend
   `lifecycle.rs` trailing-token strip with `#off` (keep `#on` *out* of the
   Google-owned badge run — `#on` is Bryan-side intent, and echoing it into
   the badge run would corrupt span hashing; record it as a vault-side tag
   after the badge run instead).
3. **Frontmatter**: parse `offclock` scalar in `projects/scan.rs`
   (three-state), build stem→flag map with parent-chain resolution + cycle
   guard, cache per run; add `effective_off_clock(line, root_note)` helper
   used by sync classification, close verdict, and settle.
4. **Warnings**: per-event deprecated-spelling lines in `SyncReport.warnings`.
5. **Migration + love.md flag** as above.
6. **Tests**: extend `model.rs`, `event_task.rs`, `render.rs:381-384`,
   `plan.rs` kept-off-clock, settle, and close-verdict suites; add
   inheritance unit tests (absent/false/true × three depths + cycle).
7. **Docs + memory**: update `docs/gcal.md` (§off-clock-events, directive
   table), `docs/reference/vault-format.md:371-389`,
   `docs/reference/glossary.md` off-clock-pomodoro entry (authorized strand),
   `docs/task-status-hooks.md` settle section, and `docs/reference/cli/*`
   via `just docs-gen` if help text changes; run `just docs-check`. Note the
   epic's auto-decisions authorize memory edits only for
   `glossary:off-clock-pomodoro`, `glossary:pomodoro`, `glossary:event-task`,
   and two decision records — a brand-new decision record for the area
   default (recommended: it is a durable policy choice) needs Bryan's
   explicit nod first.

## Open questions for Bryan

1. Should `#on` also exist as an Obsidian-side task tag with the same
   force-on-clock meaning at close/settle time (recommended yes — §4
   assumes it), or Google-events-only?
2. For event tasks, when Google says off-clock but the resolved area says
   `offclock: false`, which wins? (Recommended: explicit task/area-false is
   still inherited-level, so Google token wins unless `#on` is present —
   but this is a genuine judgment call.)
3. May the migration touch today's open event rows (risking one round of
   `kept_off_clock` warnings), or should it skip them and let aliases cover
   today?

## Sources

All claims verified against the checkout at
`sase/repos` workspace root: `src/native/gcal/model.rs`,
`src/native/gcal/lifecycle.rs`, `src/native/gcal/render.rs`,
`src/native/gcal/plan.rs`, `src/native/gcal/sync.rs`,
`src/native/gcal/journal.rs`, `src/native/gcal/root.rs`,
`src/native/event_task.rs`, `src/native/task_status_hooks/settle.rs`,
`src/native/capture_pomodoro_close/linked_tasks.rs`,
`src/native/capture/event_conflict.rs`,
`src/native/capture/meet_event_run.rs`,
`src/native/capture_pomodoros_agenda.rs`, `src/native/stats/clock.rs`,
`src/native/stats/report.rs`, `src/native/projects/scan.rs`,
`src/native/task_text_escape.rs`, `docs/gcal.md`,
`docs/reference/vault-format.md`, `docs/reference/glossary.md`,
`docs/task-status-hooks.md`, `docs/stats.md`,
`docs/reference/json-outputs.md`, `sase/memory/cli_rules.md`,
`sase/memory/docs.md`, epic bead `bob-cli-fl` (read 2026-11-02), and a
bounded scan of `~/bob` (`love.md` frontmatter, daily notes, `bob.md:99`).
