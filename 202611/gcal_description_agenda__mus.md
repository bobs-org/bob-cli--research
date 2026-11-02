# Gcal description → event-task sub-bullets: design research

Researcher: mus · 2026-11-02 · for Bryan's `bob gcal sync` proposal:
convert the Google Calendar event description (minus the special syntax
already parsed from descriptions) into sub-bullets on the created event
tasks. Intuitive, reliable, beautiful — in that order.

## TL;DR recommendation

Do it, but **not as free-form sub-bullets**. Ship a single Google-owned
**agenda block**: the non-directive remainder of the description, rendered
as nested bullets under one labeled header bullet, owned by Google under
the existing propose-once rules, capped in size, link-preserving, and
vault-escaped. Seed it on row creation, update it in place only while
untouched, and never touch anything outside the block. Details in
§Recommended solution.

## What sync does with descriptions today

Ground truth from the tree (all paths relative to the bob-cli checkout):

- `src/native/gcal/model.rs` — `GcalEvent::from_google` keeps the raw
  `description` only long enough to run `description_directives()`, then
  drops it. A *directive line* is a line whose **every** token (split on
  whitespace/commas) is a directive: `@route`, an off-clock alias
  (`#offclock`, `#off-clock`, `#untracked`), or a buffer (`-30`/`-30m`,
  `+15`/`+15m`, ASCII or typographic minus). Directives combine on one
  line or spread across lines. HTML from Google's editor is normalized
  first (`<br>`/`<p>`/`<div>`/`<li>` → line breaks, other tags stripped,
  entities decoded). **Any line containing one non-directive token is
  ignored whole** — phone numbers, 4-digit values, sentences, agendas,
  links, all of it. Numbers in titles are never buffers either.
- `src/native/gcal/sync.rs` (`build_occurrences`) folds the parsed
  directives into the row: `@route` → `[root::]` candidate, off-clock →
  ` #offclock` tag, buffer → `[buffer::]` field. The journal records only
  three span hashes per row: `time`, `title`, `badges` (badges cover the
  📅/📹/📍 links **plus** `#offclock` **plus** `[buffer::]`).
- `src/native/gcal/plan.rs` (`apply_span_updates`) does a three-way merge
  per span: still-matching-journal → replace in place; differs-from-both
  → Bryan's edit, kept and reported once (`kept_edit`); plus independent
  root rerouting (`kept_root`), off-clock flips (`kept_off_clock`), and
  time-change reslotting that moves the row **with its child block**.
- `src/native/gcal/lifecycle.rs` (`row_untouched`) decides whether a row
  is safe to auto-manage; `remove_lifecycle_context` **refuses to remove a
  context row that has any child bullets** ("kept a context row with your
  notes"). The ownership contract in `docs/gcal.md` is explicit: child
  bullets are Bryan's, sync never touches them.
- `docs/gcal.md` §JSON output: "JSON never includes tokens, descriptions,
  or attendees." Descriptions never leave the machine today except as
  parsed directives.
- Precedent for a machine-owned child block exists:
  `src/native/task_cancel/line.rs` (`edit_source_create_log`) inserts a
  first-child `  - ❌ **CANCEL LOG**` header with dated entries — indented
  two spaces under a column-0 task, i.e. exactly where agenda bullets
  would live.

Related decisions read for this review (`sase memory read`): `decisions:`
`bob-gcal-is-read-only-and-proposes-once`,
`gcal-root-follows-google-until-edited`,
`calendar-events-are-daily-note-event-tasks`,
`synced-meetings-link-by-phase`, `event-buffers-widen-the-span`, plus
`glossary:event-task`. CLI/docs conventions from `cli_rules.md` and
`docs.md`.

## Critique: is this a good idea?

**Yes — with a tighter shape than "sub-bullets".** The value is real:
the highest-signal part of most invites (agenda, doc links, call-in
details beyond the 📹 badge, address details beyond 📍) currently lives
one click away in Google Calendar, and every meeting starts with Bryan
re-typing or hunting for it. Event tasks are the natural home: they are
already a daily-note residence exception outside the review walk, so a
bounded notes block adds zero review burden. But the naive version of
this request has five problems, each fixable:

1. **Ownership collision.** Today "child bullets are yours, never
   touched" is load-bearing: context-row lifecycle refuses to delete a
   row with children, and reslot moves the whole block. Free-form
   sub-bullets erase the line between Google's text and Bryan's meeting
   notes, so the next description edit either clobbers his notes or can
   never apply. Fix: one delimited Google-owned block; everything outside
   it stays his, byte-for-byte.
2. **Boilerplate pollution.** Real descriptions are full of Meet/Zoom
   footers (duplicating the 📹 badge sync already renders),
   confidentiality disclaimers, and forwarded threads. A verbatim dump
   would make daily notes ugly and `vault-sync` diffs noisy. Fix: strip
   lines that duplicate rendered badges, collapse whitespace, cap size
   with an explicit truncation marker.
3. **Forgeable vault syntax.** Descriptions are attacker-adjacent input
   (anyone can invite Bryan). A line like `- [ ] #task pay me` or
   `[root:: job]`, `^fake-id`, `[[#^real-id]]`, `🔁`, or a `📅 2026-11-03`
   due date must render as inert text, never as a task, field, block id,
   link, or due date. The existing `escape_title` + Tasks-emoji
   neutralizer in `src/native/gcal/render.rs` is the template; bullets
   need the same treatment plus leading-marker and `[[` handling.
4. **Journal blindness.** Descriptions are unhashed today, so there is no
   record of what was written and no propose-once reporting. Any design
   must add a fourth span (or equivalent) to `RowRecord.spans`, or edits
   will flap: every sync would see "different from journal" with no
   journal to compare against.
5. **Scope creep into the row.** The temptation is to enrich the row line
   itself (badges, fields, longer titles). Don't: the row's Google-owned
   run (badges → `#offclock` → `[buffer::]` → `[root::]` → `[type::]`) is
   parsed positionally by `split_row_spans` and hashed as one `badges`
   span. Notes belong **below** the row, never in it.

What I would **not** do: two-way notes sync (rejected alongside two-way
everything in the read-only decision — no UI exists to resolve edit
conflicts); stuffing notes into `list`/JSON by default (descriptions are
deliberately excluded there; a count is enough); or writing notes on
context (Maybe/free) rows — they have no task block to hang bullets on,
and a Maybe→Yes upgrade is the right moment to render them.

## Adjustments to the requirements (called out)

1. **Only Event Task rows get notes; context rows never do.** A Maybe or
   free row is `- **time** title · *maybe*`, not a task, so sub-bullets
   have no parent. Upgrades render the block at upgrade time. (New rule,
   consistent with buffer/off-clock handling.)
2. **Directive-only and empty descriptions produce no block.** No header,
   no placeholder, no empty bullets. The note stays exactly as today.
3. **One labeled block, not loose bullets.** Loose `  - line` children
   are indistinguishable from Bryan's notes; a header bullet makes
   ownership visible and gives updates a single anchor.
4. **Sync never edits Bryan's bullets, and Bryan's bullets never block
   Google's.** His notes live as siblings after the block; the block
   updates/replaces/removes independently while untouched.
5. **Caps are part of the feature, not tuning:** at most ~12 lines /
   ~1200 characters per event, then a `… N more lines in Google Calendar`
   trailer. Without caps one forwarded thread owns the daily note.
6. **Off by config, not by flag (v1).** A `gcal:` config key (e.g.
   `agenda_notes: false`) is the escape hatch; no new `sync` flag, so no
   `cli_rules.md` short-alias/help-matrix work. Revisit a flag only if
   per-run control proves necessary.

## Options considered

| Approach | Shape | Verdict |
| --- | --- | --- |
| **A. Managed agenda block (recommended)** | One Google-owned header + nested bullets; hashed span; propose-once updates | Intuitive (labeled, scannable), reliable (owned range, journaled), beautiful (capped, link-preserving) |
| B. Seed once on creation, then Bryan owns | Same render, but frozen after first write | Simpler merge logic, but stale agendas forever; Google corrections never land; arguably worse than nothing |
| C. Link-out only (no vault write) | e.g. 📝 badge or `list -f json` gains description text | Zero note noise, but keeps the context one click away — concedes the whole point |
| D. Loose sub-bullets, synced line-by-line | Each description line its own `  - ` child, merged individually | Unreliable: reordering/duplicates flap; Bryan's interleaved notes make every update ambiguous |
| E. Two-way notes sync | Bryan's bullet edits flow back to Google | Rejected: violates the read-only grant decision; no conflict UI |

B is the honest fallback if A proves too fiddly in implementation: it is
A with the updater deleted. D is the literal reading of the request and
the one I advise against — it is the only option that cannot tell his
words from Google's a week later.

## Recommended solution

### Rendered shape

For an event whose description has non-directive remainder text, a new
Event Task row renders as:

```markdown
- [*] #task **1200-1300** Lunch with Kelly [📅](… "Open in Google Calendar") [root:: love] ^lunch-with-kelly
  - 📝 From Google
    - Bring insurance card
    - [Q3 planning doc](https://docs.google.com/…) — my notes
```

- Header bullet `  - 📝 From Google`: fixed text, two-space indent (same
  convention as the `❌ **CANCEL LOG**` first child). One header per task,
  always the **first** child block, so updates have a stable anchor and
  Bryan's own notes naturally accumulate below it as siblings.
- Nested lines at four-space indent (`    - …`), one per surviving
  description line; continuation/wrapped lines fold into their parent.
- No block at all when nothing survives (empty, directive-only, or
  entirely boilerplate descriptions). No empty headers, ever.

### Parsing pipeline (extends `model.rs`, reuses its HTML normalizer)

1. Start from the already-normalized plain text (`normalize_description_html`).
2. Extract links **before** stripping: `<a href>` → `[text](url)` Markdown
   (the tag-stripper must learn this one tag; everything else still strips).
   This is the feature's main beauty payoff — doc links survive as links.
3. Drop every directive-only line (the existing rule, unchanged), then drop
   boilerplate lines that duplicate what the row already renders: the Meet
   "Join with Google Meet" footer (📹 badge covers it), URL-only lines
   matching `join_link`/`html_link`, and blank lines. Be conservative:
   when in doubt, keep the line. Never learn "confidentiality disclaimer"
   heuristics in v1.
4. Collapse 3+ blank/newline runs, fold soft-wrapped continuations, cap at
   ~12 lines / ~1200 chars with a trailer
   `    - … N more lines in Google Calendar`.
5. Escape each line as vault-inert text: run the row's `escape_title`
   pipeline (shared escaper + Tasks-emoji neutralizer + leading-marker
   backslash), plus neutralize `[[`, `]]`, `^id` tails, and leading list
   markers (`-`, `*`, `>`, `#`, `1.`) so a hostile or accidental line can
   never become a task, tag, field, block id, embed, or due date. Control
   case in tests: a description containing `- [ ] #task pay me 📅 2026-11-03`
   must render inert (mirroring the existing
   `calendar_badges_never_parse_as_due_dates` test in `render.rs`).

### Ownership and sync semantics (extends `plan.rs` + `journal.rs`)

- The block (header through last nested line) is a **fourth Google-owned
  span** (`notes`), hashed into `RowRecord.spans` alongside
  `time`/`title`/`badges`. Same three-way rule: journal-match → replace
  the block range in place; differs-from-both → keep Bryan's version,
  report once (`kept_notes`, reusing the `push_kept_once` flag mechanism);
  Google-cleared description → remove the block while untouched.
- "Untouched" for the block means the block range still matches the
  journal hash — independent of Bryan's sibling notes below it and of the
  row spans. His edits anywhere else never block a notes update; his edits
  inside the block always win, once.
- Creation, upgrade (Maybe→Yes renders the block with the new row),
  reslot (the block is inside `child_block_end_line`, so it already
  travels with the row — verify with a test), crash-adoption (adopt the
  unjournaled block as his, same as rows), cancel (CANCEL LOG still
  prepends first; the agenda block stays beneath it), and `waiting`/
  `unchanged`/`dry-run` all follow the existing row machinery with no new
  write paths.
- `sync -f json` rows gain a small `notes: {"lines": N} | null` (count
  only — raw descriptions stay out of JSON per the existing security
  posture); human report keeps the `~ task` updated-row display. `list`
  output is unchanged in v1.

### Beauty details

- Links render as `[label](url)` with the same URL-encoding the badges use;
  bare URLs that match the 📹/📅 badges are dropped as duplicates instead.
- Headings in the description (`<h1>`–`<h3>`, ALL-CAPS single lines) render
  as `**bold**` inline text, not as `##` vault headings — a daily note
  must keep exactly its own section structure.
- List structure flattens one level: Google `<li>` items become sibling
  `    - ` bullets (nesting deeper than one level flattens; Bryan's vault
  rarely wants a third level under an event).
- The 📝 header is deliberately unobtrusive: one emoji, two small words,
  dimmed by familiarity after the first day. No per-line attribution, no
  timestamps, no "synced at" noise inside the block — the Events stamp
  already says when sync ran.

### Rollout and tests

- v1 behind `gcal.agenda_notes` (default true); setting false restores
  today's behavior byte-for-byte, which is also the downgrade path.
- Backfill: existing journaled rows gain the block on the next sync as a
  span update (same migration story as the buffer feature:
  `buffer_change_updates_untouched_row_in_place…` in
  `tests/gcal_lifecycle.rs` is the test template). Edited rows keep their
  text and report once — no surprise rewrites.
- New tests, mirroring existing ones: seed-on-create, upgrade renders
  block, Google edit updates untouched block in place, Bryan edit inside
  block wins + `kept_notes` once, Google clear removes block, hostile
  description renders inert (dataview + emoji-format parse asserts),
  caps + trailer, reslot carries the block, idempotency (`unchanged` on
  rerun, journal count stable).
- Docs: `docs/gcal.md` gains a short section (ownership-table row:
  "Agenda block — Google until you edit it"), `just docs-check` gate per
  `docs.md`; no README or help-text changes (config-only surface).

### Open questions for Bryan

1. Header wording: `📝 From Google` vs `📝 Agenda` vs no header (loose
   bullets)? I recommend the header for ownership clarity, but it is one
   line of taste.
2. Cap values (12 lines / 1200 chars) — right order of magnitude, or do
   your invites run longer/shorter?
3. Should `bob gcal list` show a hint (e.g. `+notes`) when an event
   carries description text, so you can see pre-sync what will land?
