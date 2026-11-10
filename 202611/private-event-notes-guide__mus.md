# Adding Metadata to Private Event Tasks: a Small Guide

> **One-sentence rule:** a private event note is an event description only Bob reads — write the same `@route`, `#off`, and `-30 Drive there` lines you would put in Google, and they beat Google's description on that event's Event Task, field by field.

**Status:** engine (layering, precedence, provenance) is landed behind `docs/gcal-notes.md`; the `bob gcal note` CLI surface below is the `bob-cli-ji` planned shape (phases `ji.2`/`ji.4` in progress). I verified `bob gcal note --help` is still unrecognized on this checkout, so treat the commands as the guide target, not today's binary.

## When to reach for it

| Your event looks like | Example | What goes wrong without a note |
| --- | --- | --- |
| **Locked** — someone else owns it, you cannot edit it | *Deerwood. Christmas breakfast* (Kelly organizes, Dec 13, accepted, no description) | Lands as `[root:: meet]` with no buffer. You cannot fix it until the morning of. |
| **Fragile** — an external invite whose description you hand-edited | *Interview with PermitFlow* with your own `@job` / `-30 Prep!` appended | Works today, but the organizer's next update can silently drop your lines. Google warns guest edits "might be lost". |
| **Shared** — you own it, but guests can read the description | *Haircut* with `@body` / `-15 Walk…* | Works, but every guest sees your routing. |

All three take the same note. Any event qualifies: owned, locked, awaiting-reply, or Maybe. A note never RSVPs, never creates a row, and never changes inclusion.

## What a note can set

| Want | Write | Lands as |
| --- | --- | --- |
| Route the task | `@family` | `[root:: family]` via `✎ @family` |
| Clock it off/on | `#off` or `#on` | ` #off` / ` #on` tag on the row |
| Reserve time before/after | `-30` / `+15` (0–720, `-0` clears a Google side) | `[buffer:: -30m +15m]` |
| Explain the buffer | `-30 Drive to Deerwood` | `↤ *30m before* · Drive to Deerwood` bullet |
| Say anything else | `Bring the stroller` | Plain bullet under the reasons |

Grammar notes that bite:

- One line of input is **not** one directive line. `bob gcal note deerwood @family -30 Drive there` normalizes to canonical lines (`@family` / `-30 Drive there`) — the preview echoes them back.
- `-30` is *before*, `+15` is *after*. Bob never guesses the sign from your prose; the time rail (below) makes a wrong sign obvious.
- `@route`, `#off`, `#on` inside a reason are text. Keep each on its own line.
- `;` breaks a directive-started line only. `Bring snacks; and water` stays one bullet.

## The 5-minute walkthrough

**1. RSVP first, in Google.** Bob stays read-only and never RSVPs for you (v1). Then, right after the RSVP — weeks before the daily note exists:

```console
$ bob gcal note deerwood @family -30 Drive to Deerwood +15 Drive home
```

Selection: every query word must match the displayed title; exact title beats prefix beats contains beats soonest. Recurring series group into one candidate (*Little Gym · ↻ weekly*). A pasted Calendar URL (`eid=`), `-i ID`, or `-D DAY` selects exactly; `-C ID` disambiguates calendars.

**2. Read the preview — it is what sync will write.** One occurrence builder renders both, so there is no second implementation to drift:

```console
✎ Deerwood. Christmas breakfast
  Sun Dec 13 · 10:00–12:00 · from Kelly · Yes

  @family
  -30 Drive to Deerwood
  +15 Drive home

  ● family  09:30 ╱╱╱╱╱╱ 10:00 ━━━━━━━━━━━━━━━━ 12:00 ╱╱╱ 12:15

  lands as
  - [ ] #task **1000-1200** Deerwood. Christmas breakfast [📅](…)
    [buffer:: -30m +15m] [root:: family] [type:: MEET] ^deerwood-christmas-breakfast
    - ↤ *30m before* · Drive to Deerwood
    - ↦ *15m after* · Drive home

✓ Noted · only in Bob · lands in 2026/20261213.md when that day syncs
```

The rail is at most 48 columns: `╱` wings in the dim root hue, `━` meeting in the root hue, proportional widths. A midnight clip prints `(clipped at 00:00)`.

**3. Recurring event? Pick a scope.** On a TTY Bob asks; in scripts pass `-s`:

- `This event` — one occurrence (`Fri Nov 13`).
- `All events` — the whole series, keyed by Google's `recurringEventId`.

`-s series` on a one-off event is an error. There is no "this and following" in v1.

**4. Read the saved-vs-applied line.** Every write reports exactly one:

| You see | It means |
| --- | --- |
| `lands in 2026/20261213.md when that day syncs` | Noted ahead of time; sync applies it at birth. |
| `you haven't replied: lands when you say Yes` | Note waits; nothing is created. |
| `you answered Maybe: lands when you say Yes` (unless `gcal.tentative: task`) | Same wait for Maybe. |
| `↻ applied to 2026/20261109.md` | Writer host synced the affected day at once. |
| `saved · … updates on the next sync on <host>` | Saved off-writer; the writer applies it later. |

A sync failure after a save still exits 0: the note is safe, the warning names `bob gcal sync`.

## Check, edit, clear, adopt

```console
$ bob gcal note                  # 3 private notes · next 90 days
$ bob gcal note deerwood         # show: canonical lines + effective root/buffer/clock
$ bob gcal note -l -a            # every upcoming event, noted or not (the Mac picker source)
```

- **Edit:** `bob gcal note -e deerwood` opens `$VISUAL`/`$EDITOR`/`vi` on the canonical note with a scissors help block (no `#` comments — `#` starts directives). Empty text clears; validation errors offer `Edit again? [Y/n]`.
- **Clear:** `bob gcal note -c deerwood` appends a clear (`text: ""`). The row falls back to Google's values. For a series, `-c` offers only scopes that have a note.
- **Adopt fragile lines:** `bob gcal note -A -i <id>` copies directive and reason lines from a fragile Google description into a note (prose stays in Google). They then "survive the organizer's next update". Refuses if the scope already has a note — edit it with `-e` instead.
- **Dry run:** `-d` validates and previews but writes nothing.

Validation fails fast (exit 2, nothing saved, all errors at once): unknown route (with did-you-mean), two routes, `#off` + `#on`, two values for one side, minutes outside 0–720, reason with 0 minutes, text over 2048 bytes. Warnings (not errors): `#foo` becoming a bullet, prose starting like a directive, `-d`-looking tokens inside TEXT, deprecated `#offclock` canonicalized to `#off`.

## What "lands" really means

Each field takes the first layer that sets it: **✎ this event → ✎ all events → Google → your untouched-row rule**. A reason travels with its side's winning value; a note side without a reason drops Google's reason for that side.

- Google always keeps time, title, and the 📅/📹/📍 links.
- Bullet order: `↤` reason, `↦` reason, note prose (event then series), Google's copied lines (capped by `gcal.description_lines`), overflow line. Note prose and reasons never count toward the cap. `gcal.description: off` hides note bullets too — one kill switch — but directives still apply.
- Ownership after landing is the unchanged rule: the row follows the note while untouched; your `[root::]`/`[buffer::]`/bullet edit wins and is reported once (`kept_root`, `kept_description`). A note edited after the row's birth reaches the row only while time, title, and badges are all untouched (one badge hash) — exactly like a Google-side change today. Most notes land at birth, so this rarely matters.
- `sync -F` keeps notes and reapplies them. Notes are never pruned silently; `bob gcal note` hides past events by default and `bob gcal doctor` reports orphans with one-line fixes.

## Phone stopgap and privacy

- **From the phone today (no code):** set the event's Google colour at RSVP time. `gcal.colors` (e.g. `{sage: body, grape: family}`) already routes by colour. Colour cannot carry buffers or reasons — the note is the full fix.
- **Privacy:** note text appears only in `bob gcal note` output and `sync -d` diffs. `list`/`sync` JSON carry summaries (`scope`, `fields`, `bullet_lines`) plus identity fields (`calendar_id`, `event_id`, `root.kind: note/series_note`), never words. `GcalEvent`'s `Debug` redacts note text.
- **Storage:** one `gcal.note` record per save in `.bob/gcal/<host>.jsonl`, keyed by Google id (never title/date/path), last-writer-wins across hosts, only the writer applies. A foreign-account note is never applied.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `its Bob lines live in the organizer's description and may vanish` (`bob gcal list` ⚑) | Fragile directives, no note yet | `bob gcal note -A -i <id>` |
| `held …: its private note could not be read (N malformed gcal journal lines)` | Truncated note record; sync froze the row's span/root/description rather than guess | `bob gcal doctor`, repair or `-c`, re-note |
| `kept your edited description bullets; your private note changed` | Both you and the note touched the bullets | Expected: your edit stands; review the note |
| Note saved but row unchanged | Off-writer host, or row's badges edited (hash cost), or still awaiting Yes | Read the saved-vs-applied line; run `bob gcal sync` on the writer |
| `ambiguous` with candidates (exit 2, JSON `ok: false`) | Query matched several events off-TTY | Re-run with `-i`/`-C` from the candidates list |

## Sources

- Epic `bob-cli-ji` (phases `ji.2` select, `ji.4` write, `ji.6` records): `sase bead read bob-cli-ji -r '<why>'`.
- Plan `sase/repos/plans/202611/private_gcal_event_notes.md` (§§ Shared design, select, write, extras, records).
- Research `research:202611/private_notes_for_unowned_gcal_events/private_notes_for_unowned_gcal_events.md` (R1–R10, stopgap, badge-hash and pre-touch findings).
- Contract `docs/gcal-notes.md` (Model, Grammar, Precedence, Storage, Ownership, Reliability) and `docs/gcal.md` (§§ Root selection, Buffers, Buffer reasons, Description bullets, Who owns each part of a row).
