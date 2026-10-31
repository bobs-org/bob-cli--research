# Pick the project for one Google Calendar event in `bob gcal sync`

Research date: 2026-10-31. Evidence comes from the bob-cli source at commit `061824f8`
(`src/native/gcal/`), the bob-cli docs (`docs/gcal.md`, `docs/pomodoro-homes.md`,
`docs/projects.md`), and read-only checks of `bob capture-targets` and note frontmatter
in `~/bob`. Nothing was changed.

## TL;DR

- **End the event's title in Google Calendar with `@<project>`.** For example, rename
  the event to `Planning sync @bob`. The next `bob gcal sync` writes the Event Task with
  `[root:: bob]` and removes `@bob` from the title it shows:

  ```markdown
  - [*] #task **1400-1430** Planning sync [📅](…) [root:: bob] ^planning-sync
  ```

- **Or put `@<project>` alone on one line of the event description.** The title stays
  as it is. If the title also ends in an `@token`, the title wins.
- **Pick a project that is its own root parent.** A top-level project (its `parent:` is
  an area), or a project with `root: true`, works. A sub-project such as `@sase_art` is
  rejected because it groups under `sase`. Bob then falls back to colour, calendar, or
  the default root (`meet`) and prints a warning.
- **Set the route before the first sync writes the row.** Sync writes `[root::]` once
  and never rewrites it. If the Event Task already exists, edit `[root:: …]` on the
  daily-note line. For a recurring event, that edit also sets the root for its future
  occurrences.
- **Check before you sync:** `bob gcal list` (or `bob gcal sync -d`). The root column
  shows the chosen root and its source, such as `@bob`, and warns about each rejected
  candidate.

## What "the project" means here

Synced Event Tasks always go in the daily note's `## Events` section. Bob never files
them into a project note. The "project" is the task's `[root::]` field. That field
records which area or project the meeting's time counts toward. It affects Pomodoro home
chips, `bob plan`, the capture agenda, and `bob stats` (see bob-cli
`docs/pomodoro-homes.md` §R11). It does not
change the task's location, blocking, or review state. This rule comes from decision
`calendar-events-are-daily-note-event-tasks`: synced events live in the daily note, are
attributed to a root, and get one MEET link.

So "use project X for this event" means "make sync write `[root:: X]`".

## Root precedence

`choose_event_root` (`src/native/gcal/root.rs:41`) tries these sources in order. It
writes the first one that passes validation (`docs/gcal.md` §Root selection):

| # | Source | How you set it | Reported as |
| --- | --- | --- | --- |
| 1 | Series memory | Edit `[root::]` on one occurrence of a recurring event in the vault | `learned from your 2026-10-29 edit` |
| 2 | **Event route token** | Title ends in `@route`, or a description line is only `@route` | `@bob` |
| 3 | Event colour | `gcal.colors: {tomato: job}` in `~/.config/bob/config.yml` | `colour tomato` |
| 4 | Calendar | `gcal.calendars: [{id: …, root: body}]` | `calendar Health` |
| 5 | Default | `gcal.root` (default `meet`) | `default` |

When a source is invalid, Bob warns, names the reason and the fix, and tries the next
source. Only the route token (#2) is set on a single event in Google Calendar. Colour
(#3) is per event too, but it maps a colour to a root, so it fits only when one colour
always means one area or project.

## Route token rules (from the code)

Parsing lives in `src/native/gcal/model.rs:113` and `:240-257`. Resolution lives in
`src/native/gcal/root.rs:73-116` and `src/native/parent_notes.rs:192`.

1. **Title form.** Bob reads only the last whitespace-separated word of the title. It
   must start with `@` and have at least one character after the `@`.
   `Dentist @body` works. `@body Dentist` does not, and neither does `Dentist @body.`
   (Bob would look for a route named `body.`).
2. **Description form.** Bob reads the first description line that, once trimmed, is a
   single `@word`. Other lines can hold anything. Bob ignores a line such as
   `@bob and more`.
3. **The title wins, even when its token is wrong.** The code reads
   `title_route_hint.or(route_hint)`. A title whose last word starts with `@` hides the
   description token, even if that word resolves to nothing. For example, with
   `Coffee with @alice` and a description line `@job`, Bob looks only for `alice`. It
   then warns `route_unknown` and goes on to colour, calendar, and default. It never
   checks `@job`.
4. **Name matching.** The route matches like `bob ref create -P` or a capture `@route`.
   Case does not matter. The `.md` suffix and `[[…]]` wrapping are allowed. `-` and `_`
   count as different characters. A note's `project_name_aliases` also match, so
   `@bob-cli` resolves to `bob`. Bob writes the canonical stem (`[root:: bob]`), but the
   source column shows what you typed (`@bob-cli`). Bob never fuzzy-matches. A near miss
   gives a hint, not a match.
5. **Which notes match.** Only notes that `bob capture-targets` lists: vault-root area
   notes and vault-root project notes that are not done or canceled. A closed project
   fails with `route_unknown` (`project 'x' is done`).
6. **Root validation.** The resolved note must pass `validate_root_candidate`
   (`root.rs:210`). It must be an area at any depth, or a project that is its own root
   parent. Otherwise Bob rejects it with `root_field_not_root`, for example
   `sase_art groups under sase; write [root:: sase] or set root: true on sase_art`.
7. **Title stripping.** Bob removes the `@token` from the title only when the title
   token resolved and passed validation (`strip_title_route`, `root.rs:192`). A title
   that is only `@bob` becomes `(untitled event)`. A rejected or unknown token stays in
   the title, so the mistake shows in the note.

## Which of Bryan's projects work today

From `bob capture-targets` and the frontmatter in `~/bob` on 2026-10-31:

| Token | Note | Result |
| --- | --- | --- |
| `@bob` or `@bob-cli` | `bob.md`, project, `parent: [[dev]]` (area) | Works, so `[root:: bob]` |
| `@job_2026` | `job_2026.md`, project, `parent: [[job]]` (area) | Works, so `[root:: job_2026]` |
| `@sase` | `sase.md`, top-level project | Works |
| `@sase_blog` | `sase_blog.md`, `root: true` | Works |
| `@job`, `@body`, `@dev`, … | Area notes | Works |
| `@sase_art` | `parent: [[sase]]`, no `root: true` | Rejected (`root_field_not_root`). Falls back |
| `@job_2026_apply_29` | `parent: [[job_2026]]`, no `root: true` | Rejected (`root_field_not_root`). Falls back |

To attribute meetings to a sub-project, choose one:

- use its root project (`@sase` instead of `@sase_art`); or
- add `root: true` to the sub-project's frontmatter. `root: true` is reporting-only. It
  makes the note its own root parent for Stats and Pomodoro grouping and changes nothing
  else (`docs/projects.md`, `docs/pomodoro-homes.md` §R2).

## Gotchas

- **An existing row's root never changes.** On every run, sync updates the time, title,
  and badge spans of an untouched row. It never rewrites the checkbox, `[root::]`,
  `[type::]`, or block ID (`apply_span_updates`, `src/native/gcal/plan.rs:466-472`). If
  you add `@bob` to the title after the row exists, the next sync drops `@bob` from the
  displayed title (if you haven't edited the title span) but keeps the old root. To fix
  that row, edit its `[root:: …]` in the daily note.
- **For recurring events, series memory beats the title token.** If you edited
  `[root::]` on any occurrence, that learned root is source #1. It wins over an `@route`
  you add to the series later (`root.rs:52-70`, `learn_series_root` at
  `plan.rs:614`). Edit `[root::]` on another occurrence to teach the series again.
  Changing the token alone does nothing. Because Bob returns before it reads the
  token, the `@bob` also stays in the displayed title.
- **Recurring events are easier to fix in the vault.** One `[root::]` edit on any
  occurrence sets the root for every new occurrence in that series. No Google edit is
  needed.
- **Rich-text descriptions (not verified).** Bob splits the description on newline
  characters and strips no HTML. Google Calendar's web editor may store a multi-line
  description as HTML (`Agenda<br>@bob`). Then `@bob` is not on its own line and Bob
  would miss it. A description that is only `@bob` is safe. The title token avoids the
  question entirely. Check with `bob gcal list` before you rely on a description token.
- **Only Event Tasks get a root.** Context rows (all-day, multi-day, free, or Maybe
  unless `gcal.tentative: task`) have no root.
- **Google Calendar stays unchanged.** Bob is read-only on Google (decision
  `bob-gcal-is-read-only-and-proposes-once`). The `@bob` token stays in the Google
  event. Bob strips it only from the vault row.

## How to check it

```bash
bob gcal list                 # root column: chosen root and its source (e.g. @bob)
bob gcal list -f json         # events[].root.value / .source / .warnings
bob gcal sync -d              # exact diff, including the [root:: …] it would write
bob capture-targets           # every name an @route can resolve to
```

A rejected candidate shows up as a warning that gives the reason and the fix, for
example: `@sase_art rejected (root_field_not_root): …; fix: … set root: true on
sase_art`.

## Bulk alternatives (not per event)

- **Calendar to root:** `gcal.calendars: [{id: <calendar id>, root: job}]` sends every
  event on that calendar to `job` unless a token or colour says otherwise.
- **Colour to root:** `gcal.colors: {tomato: job, sage: body}` lets you choose a root by
  colour in Google Calendar without renaming the event.

Bryan's `~/.config/bob/config.yml` currently has its `gcal:` block commented out, so
the defaults apply (root `meet`, calendar `primary`, no colour map). On this host, the
`@route` token and series memory are the only per-event controls until that block is
enabled.

## Evidence

- `src/native/gcal/model.rs:113-129`: title token from the last word; description token
  from `description_route`.
- `src/native/gcal/model.rs:240-257`: `parse_route_token` and `description_route`.
- `src/native/gcal/root.rs:41-170`: `choose_event_root` precedence (series memory, then
  token, colour, calendar, default), with `title_route_hint.or(route_hint)` at `:73-76`.
- `src/native/gcal/root.rs:192-209`: `strip_title_route`.
- `src/native/gcal/root.rs:210-277`: `validate_root_candidate`, including
  `root_field_not_root`.
- `src/native/parent_notes.rs:186-262`: `resolve_parent` (stem, alias, terminal, no
  fuzzy matching).
- `src/native/gcal/snapshot.rs:86-109`: Bob chooses a root only for events that
  classify as Event Tasks, and replaces the event title with the stripped title before
  planning.
- `src/native/gcal/plan.rs:466-472`, `:609-660`: roots are never rewritten, and series
  learning.
- Unit test `route_token_precedes_color_calendar_and_default` (`root.rs`): `Dentist
  @body` with description `@job`, colour tomato→job, and calendar root `health` gives
  root `body`, source `@body`, title `Dentist`.
- Integration test `tests/gcal_sync.rs:126` and `:585`: the synced row omits `@body`,
  and its JSON source is `@body`.
- Docs: `docs/gcal.md` §Root selection (line 541), §Who owns each part of a row (448),
  §Reconciling Google-side changes (471); `docs/pomodoro-homes.md` §R2 (43) and §R11
  (279).
