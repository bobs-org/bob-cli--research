# Wispr Flow Meeting Notes → Ref Notes Linked to Event Tasks

Researcher: `mus` (independent swarm report, suffix `__mus`)
Date: 2026-11-24
Question: how to make it as easy as possible to create excellent ref notes from
AI meeting transcripts (first case: Wispr Flow transcript) that land in the
correct area/project and link to the correct Event Task.

First use-case inputs (as stated in the request):

- Transcript: `~/tmp/bryan_derrick_meet_notes.txt` (Wispr Flow output for the
  Yogi intro call).
- Event Task: `^bryan-bugyi-derrick` in `~/bob/2026/20261123.md`
  (`1500-1530 Bryan Bugyi and Derrick Blakely`, `[root:: job]`,
  `[type:: MEET]`).

## TL;DR recommendation

Yes, this is a good idea, with adjustments. Build it as a thin extension of
the existing reference pipeline, not as a new top-level command or a new note
kind:

1. Reuse `bob ref create` (Markdown route, default `ref_type: chat`) plus one
   new option, e.g. `-E/--event EVENT`, that resolves an Event Task and does
   the two things Bryan currently does by hand: (a) default the reading-task
   parent from the event's `[root::]`, and (b) write the reading task's
   `LINKS:` entry pointing at the event's block link.
2. Convert the Wispr `.txt` to `.md` before ingest (one documented `cp`/rename
   step, or accept `.txt` as Markdown — see §5). Do not teach `bob ref create`
   a new transcript target type in v1.
3. Keep v1 verbatim: the transcript becomes the saved `source_markdown`
   (write-once) and the rendered PDF body; add a fixed `## NOTES` scaffold and
   a `## Tasks` section for Bryan's own follow-ups. No AI summary/rewrite in
   the filed note in v1.
4. Ship the same JSON the Mac needs (Mac Capture is a thin client of `bob`):
   event resolution, parent, title/name derivation, dry-run preview, and link
   write must all be in the `bob` JSON response so the Mac picker is only a
   renderer.
5. For the first use-case, the command is approximately:

```bash
cp ~/tmp/bryan_derrick_meet_notes.txt ./bryan_derrick_meet_notes.md
bob ref create ./bryan_derrick_meet_notes.md \
  -P job \
  -T "Bryan Bugyi and Derrick Blakely — Yogi intro (2026-11-23, 15:00 ET)" \
  -E '20261123#^bryan-bugyi-derrick' -d
bob ref create ./bryan_derrick_meet_notes.md \
  -P job \
  -T "Bryan Bugyi and Derrick Blakely — Yogi intro (2026-11-23, 15:00 ET)" \
  -E '20261123#^bryan-bugyi-derrick'
```

The rest of this report justifies each line of that recommendation, critiques
the request, and lists the adjustments.

## 1. What the inputs actually look like

### 1.1 The transcript

`~/tmp/bryan_derrick_meet_notes.txt` is ~3.2 KB of plain-text Wispr Flow
output. It is already sectioned (Yogi and the Role, Background, Yogi Agents
Feature, Google Experience, AI Development Practices, Potential Work/Roadmap,
Interview Process, Next Steps). It is clean prose, not timestamped diarized
utterances. Two consequences:

- There is no speaker-attribution or timestamp repair problem in this
  instance. A generic meeting-notes importer must still handle those (Wispr
  can emit them), but the first use-case does not need diarization cleanup.
- The file is a `.txt`, not a `.md`. This matters because `bob ref create`
  today only accepts (a) vault notes, (b) other Markdown files (`.md`), (c)
  local PDFs, (d) PDF/ArXiv URLs, (e) Spotify episodes, (f) web articles. The
  target classifier keys off the `.md` extension (`src/native/highlights_ref/target.rs`:
  `extension.eq_ignore_ascii_case("md")`, else the `TARGET must be a Markdown
  file (.md), a PDF file, or an http(s) URL` refusal). A `.txt` transcript is
  refused today. The fix is trivial (treat `.txt` as Markdown, or document the
  `cp` step), but the request as written ("create a ref note from the `.txt`
  file") does not work without it.

### 1.2 The event task

From `~/bob/2026/20261123.md`, `## Events`:

```markdown
- [x] #task **1500-1530** Bryan Bugyi and Derrick Blakely [📅](...) [📹](...)
  [📍](...) [buffer:: -15m] [root:: job] [type:: MEET]
  [completion:: 2026-11-23] ^bryan-bugyi-derrick
  - 🪢 **LINKS:** [[job#^ref-yogi-senior-swe-product-intro-call-prep]]
  - 🪢 **LINKED FROM:** [[job#^whisperflow-meeting]] (💬 mentions)
  ...
```

Key facts: residence is the daily note (the mandated Event Task residence —
daily-note exception beside `^gtd`; see `docs/gcal.md` § Sync and the
`calendar-events-are-daily-note-event-tasks` decision). Attribution is
`[root:: job]`. The row is closed `[x]` because the meeting ended before sync
observed it (the `ended-synced-meetings-are-born-done` rule: past meetings are
born `[x]` with a struck 🍅 link under a closed MEET). It already carries a
`LINKS:` entry to a prep ref task and a generated `LINKED FROM:` mention from
the `^whisperflow-meeting` task. The Pomodoro ledger shows a closed
`1445-1530 MEET` entry with a struck link to this row.

### 1.3 The surrounding task graph (why this request exists)

- `job#^whisperflow-meeting`: `[?] #task Review WhisperFlow meeting notes on
  [[20261123#^bryan-bugyi-derrick]]!` — Blocked on
  `[[bob#^wispr-flow-meet-notes]]`.
- `bob#^wispr-flow-meet-notes`: `[/] #task Integrate bob with Wispr Flow
  meeting notes!` — blocks the job task above.
- `job#^send-yogi-follow-up`: depends on `^whisperflow-meeting`.

So Bryan has already staged the dependency chain: tooling → review notes →
follow-up email. The missing piece is exactly the tooling plus the ref note.

### 1.4 The existing manual pattern (three precedents)

`~/bob/job.md` already contains three `#task #ref` reading tasks that link to
this same event:

- `^ref-yogi-senior-swe-product-intro-call-prep` (`[*]`, prep material)
- `^ref-yogi-derrick-question-playbook` (`[x]`, closing questions)
- `^ref-why-leave-google-*` (related prep, also linked)

Each is a v2 reading task (open `#task #ref` line in `job.md`, i.e. in the
area/project parent) whose note lives under `ref/chat/` with frontmatter
`parent: "[[job]]"`, `type: "[[ref]]"`, `ref_type: chat`, plus a managed embed
`![[job#^<block-id>]]` one blank line below the H1. Each carries
`🪢 LINKS: [[20261123#^bryan-bugyi-derrick]]` on the task line. This is the
pattern the feature must automate: it is already the convention, it already
renders correctly in the Reading Board (`bob ref list -P job`), and it already
survives `bob ref rename` (reading-task block ID is stable across renames).

## 2. Is this a good idea?

Yes. Three reasons it fits Bob's model rather than fighting it:

1. **A meeting transcript is reference material.** The reference-library
   concept (`docs/concepts/reference-library.md`) defines the three-way split:
   source (the material) / reference note (what was learned, under `ref/`) /
   reading task (the handle that Today, lanes, and review operate on). A Wispr
   transcript is exactly a source. Filing it as a ref note gives Bryan the
   reading-task handle for free: the review task walks in RECURRING/TICKLER/
   ROTTEN like any other reading, it can be pulled into Today with
   `bob ref today`, it respects Blocked overlays, and it shows up in
   `bob ref list -P job`.
2. **The event link is a relation, and relations are the right join.** A
   `LINKS:` entry from the reading task to the Event Task is inert (never
   blocks, never reschedules, never counts as a Pomodoro Task Link — see the
   `task-relation` glossary strand and `docs/task-relations.md`). That is the
   correct semantics: the note is *about* the meeting, it does not depend on
   it. The existing three precedents already use this join, so automation
   converges on convention instead of inventing one.
3. **Area/project association falls out of the event.** The event already
   carries `[root:: job]`. Deriving the default parent from the event root
   removes the hardest UX step (picking where the reading task lives) and
   matches the `root-parent` derivation rule (nearest area/project on the
   walk, explicit `[root::]` wins).

### Critiques and risks

1. **The Highlights pipeline is heavy for a 3 KB transcript.** `bob ref
   create` on a Markdown file runs pandoc/XeLaTeX, stamps a PDF into
   `lib/chat/`, writes a write-once `source.md` store under
   `.bob/ref-sources/`, files the note, creates the reading task, and commits
   — under `bob_sync.lock` + `scan.lock` + `ingest.lock` ordering. That is the
   right durability story for papers and articles, and it buys `bob ref code` /
   `bob ref links` / Highlights annotation sync for free. But for a short
   transcript it is a lot of machinery per meeting. The alternative (a plain
   `meet/` notebook note with no PDF, no reading task) is cheaper but loses
   the reading-task handle, the Reading Board, `bob ref today`, and the
   rename/identity guarantees. I judge the ref route worth it because Bryan
   explicitly wants "excellent ref notes" and the review workflow, not just a
   file dump. If meeting volume ever reaches dozens per week, revisit with a
   lighter `meet` type; do not pre-build it.
2. **Do not conflate this with private event notes.** `bob gcal note`
   (`docs/gcal-notes.md`) writes Bob-only description grammar (`@route`,
   `#off`, buffers, prose bullets) keyed by Google event identity, layered
   over the Google description. It is for *pre-meeting* directives and prose
   that should render as Event Task bullets. A post-meeting transcript is not
   description grammar and must not be stuffed into a private note: it would
   blow the `description_lines` cap, pollute every future sync diff, and
   confuse the ownership rule (note, then Google, until you edit it).
   Transcript → ref note; directives → private note. Keep the two.
3. **Do not file the transcript in the daily note.** Daily notes hold Event
   Tasks as a residence exception; pasting a 3 KB transcript under the event
   row breaks the Events-section contract (`docs/reference/vault-format.md` §
   Events section and Event Tasks), pollutes `gcal sync` reconciliation (it
   must preserve unknown bullets while reordering/tombstoning rows), and
   drags the transcript into the `]s` walk. The daily note should keep at
   most a one-line pointer (the relation already provides it).
4. **AI summarization is the main quality risk.** The request asks for
   "excellent ref notes". The temptation is to have the importer rewrite or
   summarize the transcript. Do not do that in v1. The filed note must be
   verbatim transcript plus scaffold; Bryan's own notes and the follow-up
   tasks live in `## NOTES` / `## Tasks` outside the managed Highlights
   region. An AI pass can *propose* bullets/tasks in the dry-run preview or as
   a separate draft, but writing model output into the write-once source store
   poisons provenance (`source_markdown` digest, `code.json` catalog) and
   makes `attach-source` verification meaningless. Phase AI assistance as a
   preview, not as the filed bytes.
5. **Privacy is fine but must be stated.** Transcripts contain names,
   employers, and interview details. They already live in the vault git repo
   (vault-sync commits them), same as mail notes and prep refs. No new
   exfiltration as long as the importer does not call a cloud model inline.
   If a future AI-cleanup step calls one, it must be explicit and off by
   default.

## 3. UX options considered

| Option | What it is | Verdict |
|---|---|---|
| A. Manual today | `bob ref create transcript.md -P job`, then hand-add `LINKS:` to event | Works now; 3 precedents prove it; too many steps to be "as easy as possible" |
| B. `bob ref create -E/--event` (recommended) | One flag on the existing create path resolves the event, defaults parent from `[root::]`, writes the relation | Smallest change that removes all hand steps; reuses `-f`/`-d`/JSON contracts |
| C. New `bob meet notes` noun | Dedicated meeting importer | Rejected for v1: new noun needs a membership rule, duplicates create's intake/lock/commit logic, violates "smallest correct fix" |
| D. `bob gcal note --ref` | Grow private notes to also file refs | Rejected: conflates pre-meeting directives with post-meeting sources; different keying (Google identity vs file stem) and different ownership |
| E. `meet/` notebook note | Cheap Markdown note under `meet.md`, no PDF/task | Rejected as the primary: loses reading handle, board, rename guarantees; fine as a pointer target, not as the artifact |
| F. Mac Capture card only | Picker in Bob Mac Capture | Required as a *client* but not as the implementation: Mac is a thin client of `bob` (`mac-capture-is-a-thin-client`), so the JSON contract in B comes first and the Mac card renders it |

## 4. Recommended solution (detailed)

### 4.1 Command shape

Extend `bob ref create` (it already owns Markdown→PDF→note→task→commit),
not a new noun. Sketch (final flag names/slots per `cli_rules.md`:
alphabetical options, every long option gets a short alias, excellent
`-h` text, hidden aliases for any rename — no new `bob capture` subcommand,
which is forbidden):

```text
bob ref create <TRANSCRIPT.md> -E|--event EVENT [-P|--parent NOTE]
    [-N|--name NAME] [-T|--title TITLE] [-t|--ref-type DIR]
    [-s|--status STATUS] [-d|--dry-run] [-f|--force[=MODE]]
```

- `-E/--event EVENT` accepts what `bob gcal note` already accepts, because
  users already know that picker: an event query (`derrick`, `bryan
  derrick`), a pasted Google Calendar URL with `?eid=`, `-i/--event-id` with
  `-C/--calendar`, and `-D/--day` to scope the lookup (default: search the
  event's day first, then ± surrounding days for the block link; Event Tasks
  are looked up by block link in the vault, not only via Google, so already-
  synced past events resolve even when the Google window has moved on).
- Zero matches → exit 2 with candidates/hint (same style as `ref show`
  `ambiguous_reference` / `no reference note matches`). Multiple matches →
  numbered TTY picker; off-TTY → exit 2 with candidates (same contract as
  `gcal note` and `ref show`).
- Default parent: the event row's resolved `[root::]` (here `job`). Explicit
  `-P` wins. Unresolvable root → require `-P` (same refusal style as vault-
  note create with no eligible ancestor).
- Default title: `"<Event title> — <counterparty/context> (<Day YYYY-MM-DD,
  HH:MM–HH:MM ET)"`, overridable with `-T`. For the first use-case the event
  title alone ("Bryan Bugyi and Derrick Blakely") is a poor ref title; the
  three precedents all add context (`Yogi Senior Software Engineer, Product:
  Intro Call Prep (Mon 2026-11-23, 15:00–15:30 ET)`). The importer should
  propose that shape and let `-T` override.
- Default name/title derivation, collision handling (`<stem>_2`), `id`
  follows stem (`reference-ids-follow-file-stems`), and `-f` reread/overwrite
  semantics are inherited unchanged from `bob ref create`. A second import of
  the same transcript for the same event must print the existing
  `already captured` + `hint: -f read it again as <stem>__vN` path, never a
  duplicate note.
- Relation write: after the reading task is filed in the parent, append (or
  create) its `🪢 LINKS:` line with `[[<day-note>#^<event-block-id>]]`
  (here `[[20261123#^bryan-bugyi-derrick]]`). If the task already links there,
  report `already_current` and change nothing. Never write the mirror
  `LINKED FROM:` line by hand — reconcile generates it. Never use a Task
  Mention (`(💬 mentions)`) for this; it must be a real relation entry.
- The event row itself is not modified (no new bullets, no `[root::]`
  change). If Bryan later re-roots the event, the parent stays where filed
  (same as all ref tasks today); `parent_mismatch` diagnostics already cover
  drift.

### 4.2 Why `ref_type: chat`, not a new `meet` type

`lib/` today holds `blogs chat docs notes papers podcasts` — no `meet`. The
Markdown route defaults to `chat`, and all three Yogi precedents are `chat`.
A new `meet` type would require a `refs.base` category entry, pipeline
routing, Mac Refs-panel support, and a migration story for the existing
interview refs. Reuse `chat` in v1. If Bryan later files dozens of meeting
refs per month and wants a separate Reading Board lane, add the type then
with a recatalog, not now.

### 4.3 The `.txt` adjustment (required, tiny)

Either (i) document `cp transcript.txt transcript.md` as step zero, or (ii)
accept `.txt` as Markdown input on the Markdown route (one-line classifier
change plus a test). I recommend (ii) because Wispr exports `.txt` and every
extra shell step is a papercut in the "as easy as possible" story — but it is
explicitly a *packaging* fix, not a new transcript pipeline. The report's
example commands use the `cp` form so they work on today's binary.

### 4.4 What "excellent" means for the filed note (v1 scope)

Filed note frontmatter (same as precedents):

```yaml
status: next        # or -s ready; default next so it surfaces for review
parent: "[[job]]"   # from event root unless -P overrides
type: "[[ref]]"
ref_type: chat
title: "<event-contextual title>"
```

Body:

```markdown
# <title>

![[<parent>#^<reading-task-block-id>]]

## NOTES
<!-- Bryan's own notes; importer leaves empty with one prompt line -->

## Transcript
<verbatim Wispr text, fenced as prose — the pandoc source>

## Highlights
<!-- highlights:begin -->
<!-- highlights:end -->

## Tasks
<!-- follow-ups; importer seeds none in v1 -->
```

Do not put the transcript inside the managed Highlights region (it is source,
not annotations). Do not invent `## Summary` content. A future AI pass may
offer suggested `## NOTES` bullets and candidate tasks in the `-d` preview
for Bryan to accept; it must not silently file them.

### 4.5 Reliability contract (what makes this trustworthy)

- **Dry-run first.** `-d` prints: resolved event (day, time, root, block
  link), derived parent/title/name, link to be written, and `writes: none`.
  Same JSON envelope pattern as `ref create -d` and `gcal note -d`.
- **Idempotent.** Same transcript + same event → `already captured` /
  `already_current`, exit 0, no new commit. `-f` reuse gives reread
  (`__vN`) vs `overwrite` (in place, preserves task) with today's semantics.
- **Locks and commits.** Reuse create's order (`ingest.lock` → `bob_sync.lock`
  → `scan.lock`), atomic note/PDF/task write, one `bob ref create`-subject
  commit that vault-sync picks up. Never take the vault lock the way capture's
  staged-file path does; this is an intake write.
- **Guards inherited.** Missing daily note / Templater-unrendered day /
  missing Pomodoros section → the event lookup still resolves (read-only), but
  the relation write goes to the *parent* note (here `job.md`), which is
  unaffected by the daily-note guards. Cancelled/declined/not-found events
  warn like `gcal doctor` orphans instead of linking.
- **JSON for the Mac.** Every new field (`event`, `parent`, `link`) appears
  in `-f json` with the same `schema_version: 1` envelope style as `ref
  create`/`ref today`, so the Mac picker (thin client) and a future Obsidian
  command can render without parsing human output.

### 4.6 Beauty (what makes it feel excellent, not just correct)

- Human output on success should read like the existing wins, e.g.
  `✓ filed <display> → ref/chat/<stem>.md · linked 📖 <title> → [[20261123#^bryan-bugyi-derrick]]`,
  with the Reading Board row visible immediately in `bob ref list -P job`.
- The Mac surface is a single "File meeting notes" card: event picker
  (same matching as `gcal note -l -a`), transcript picker, title field
  prefilled, parent chip prefilled from event root, Preview → File. No
  grammar to memorize, no vault paths typed.
- The Obsidian side needs nothing new on day one: the `![[job#^…]]` embed,
  `LINKS:` pill, and Reading Board already render the result beautifully.
  That is a feature — the design converges on existing surfaces.

## 5. Adjustments to the request (explicit list)

1. **Transcript format:** request says `.txt` → adjust to `.md` at the
   boundary (copy step today, `.txt`-as-Markdown acceptance as the tiny code
   change). Without this the command refuses.
2. **Ref type:** do not create a `meet` ref type in v1; file as `chat` like
   the three existing Yogi refs.
3. **No AI rewrite in v1:** request says "excellent ref notes" — interpret as
   verbatim transcript + scaffold + correct parent/link in v1; AI summary and
   task extraction become preview suggestions, not filed bytes.
4. **No new command noun:** request invites "the best UX" — deliver it as
   `bob ref create -E`, not `bob meet …`, to respect CLI nesting rules and
   reuse intake reliability.
5. **Link direction:** the request says "linked to the corresponding event
   task" — implement as relation on the *reading task* (`LINKS:
   [[day#^event]]`), not as a bullet on the event row and not as a Pomodoro
   Task Link. The event row stays untouched.
6. **Parent default:** "associated with the correct area/project" — default
   from the event's `[root::]` (`job` here), overridable with `-P`. Do not
   infer the parent from transcript content.

## 6. First use-case walkthrough (expected end state)

After the recommended command:

- `ref/chat/bryan_derrick_yogi_intro_261123.md` (exact stem per collision
  rules) with `parent: [[job]]`, verbatim transcript, empty `## NOTES`.
- `job.md` gains one reading task, e.g.
  `- [*] #task #ref [[ref/chat/bryan_derrick_yogi_intro_261123|<title>]] …`
  with `🪢 LINKS: [[20261123#^bryan-bugyi-derrick]]`.
- `job#^whisperflow-meeting` becomes unblocked once
  `bob#^wispr-flow-meet-notes` closes (existing dependency chain), and
  `^send-yogi-follow-up` follows.
- `bob ref list -P job` shows the new row; `bob ref today <stem>` can pull it
  into today's Pomodoro; no daily-note Events surgery was needed.

## 7. What I verified and what I did not

Verified from the working tree and vault: transcript bytes
(`~/tmp/bryan_derrick_meet_notes.txt`), event row and ledger
(`~/bob/2026/20261123.md`), the three precedent ref tasks in `~/bob/job.md`,
precedent ref notes under `~/bob/ref/chat/`, `meet.md` / `meet_inbox.md`
roles, `bob ref create --help` target/type/parent semantics, the `.md`-only
classifier refusal for `.txt`, `gcal note` event-matching semantics,
relation-vs-mention and mirror-line rules, reference-id-follows-stem and
reading-task-stability-across-rename guarantees, CLI nesting/alias rules, and
the Mac-thin-client decision. Quoted command outputs and file excerpts above
are from those reads.

Not verified by execution: I did not run `bob ref create` against the live
vault (a write), did not run pandoc/XeLaTeX rendering, and did not test
`gcal` event lookup against Google — this is a design research report, and
those verifications belong to the implementing plan's dry-run phase
(`bob ref create … -d`, `just check`).

## 8. Open questions for Bryan

1. Should the importer also seed `## Tasks` from the transcript's "Next
   Steps" section (here: "Derrick emails next steps") as *proposed* tasks in
   the dry-run preview, or stay strictly empty in v1?
2. Should recurring 1:1s with the same person file one ref per occurrence
   (recommended — matches per-event identity) or roll up into a series note?
3. Is narrating the transcript with `-L/--listen` (commute playback) desired,
   or out of scope for meetings?
