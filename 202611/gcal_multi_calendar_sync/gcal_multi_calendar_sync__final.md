# Multi-calendar `bob gcal sync`, starting with Birthdays — consolidated research

Lead researcher consolidation · 2026-11-15

**Inputs.** Five independent researcher reports (`__cdx`, `__cld`, `__grk`, `__mus`,
`__gem`, all in this directory), plus the lead's own verification: a fresh live read of
the Birthdays calendar through the Calendar connector, the screenshot
(`~/tmp/screenshots/20261115_105604.png`), and line-level checks of every load-bearing
code claim in the bob-cli checkout (`classify.rs`, `snapshot.rs`, `lifecycle.rs`,
`stamp.rs`, `config/gcal.rs`, `sync.rs`).

## Decision in brief

**Yes, do this — and the work is smaller and different than the request implies.**
Multi-calendar sync already exists in bob-cli: `gcal.calendars` accepts several
calendars, the snapshot fetches each one, and the journal keys every row by
`(calendar_id, event_id)`. A config-only change already makes Ava's birthday appear as
an all-day context bullet with the **current** binary (verified by a live dry run). The
real feature is **calendar identity**: no vault row, list cell, or sync JSON row says
which calendar it came from today. Build that as per-calendar **marks** — a short,
user-chosen glyph (`🎂`) rendered at the front of every row title from a non-primary
calendar — plus three multi-calendar hardening fixes, then enable the Birthdays
calendar by ID through chezmoi and verify on a host that holds the OAuth grant.

Recommended end state for `2026/20261114.md`:

```markdown
## Events

*↻ synced Sun 2026-11-15 11:40 · [<account>](https://calendar.google.com/calendar/r/day/2026/11/14?authuser=…)*
- **all day** 🎂 Ava's Birthday [📅](https://www.google.com/calendar/event?eid=MHJvbzlw…)
- [x] #task **0900-0915** Swings! [📅](…) [root:: abby] [type:: MEET] [fresh:: 2026-11-14]  [completion:: 2026-11-14] ^swings
- [x] #task **1900-2000** Some of "Brave" w/ Abby [📅](…) [root:: abby] [type:: MEET]  [completion:: 2026-11-14] ^grocery-store-w
```

No checkbox, no MEET, no root on the birthday row: it is context, not a task.

## Verified ground truth

### The event and the calendar

Three independent live reads (cdx via the Mac's gog adapter over SSH, cld via the
Calendar connector and a temporary config on athena, and the lead's own connector read
on 2026-11-15) agree exactly:

| Property | Value |
| --- | --- |
| Calendar | `Birthdays`, id `kjs04hafl3btrilujllivid3s8@group.calendar.google.com` |
| Calendar role / colour | `owner` · `#7bd148`, not primary, currently **not** in Bob's sync set |
| Event | `Ava's Birthday`, occurrence id `0roo9pdfmor2uhp72o0h5u8k31_20261114` |
| `eventType` | **`default`** (not `birthday`) |
| Shape | All-day `2026-11-14 → 2026-11-15` (exclusive end), `transparency: transparent`, annual series, no attendees, organizer is the calendar itself (`self: true`) |

The screenshot's second sidebar "Birthdays" (the darker green, listed first) is
Google's contacts-birthday layer. It does not appear in the CalendarList API at all,
and a `BIRTHDAY`-typed query on primary for Nov 8–16 returns nothing. Ava lives only on
the user-created calendar.

### The current binary already produces the row

cld ran the existing binary on athena with a temporary `BOB_CONFIG_FILE` naming
`[primary, kjs04…@group.calendar.google.com]`:

- `bob gcal list -D 2026-11-14 -a` showed `all day · Ava's Birthday · ✓ own · context`
  alongside the day's two existing Event Tasks.
- `bob gcal sync -D 2026-11-14 -d` planned exactly two changes: the stamp refresh and
  `+- **all day** Ava's Birthday [📅](…)`.

So enabling the calendar is one config row. Everything else in this report is about
making the result trustworthy and legible.

### Code facts (re-verified by the lead at the cited lines)

| Fact | Where |
| --- | --- |
| Event-type allowlist is `default \| fromGmail`; everything else is omitted | `src/native/gcal/classify.rs:134` |
| All-day events classify as context rows, never Event Tasks; ack skips all-day rows | `classify.rs`, `note.rs::is_eligible`, `ack.rs` |
| Snapshot fetches each configured calendar per day-run; one failure fails the whole snapshot | `snapshot.rs::fetch_days` |
| `SnapshotEvent.calendar_name` is computed but `#[allow(dead_code)]` — never rendered | `snapshot.rs:37` |
| Journal key is `calendar_id + \u{1f} + event_id`, using the **configured** spelling (`"primary"`) | `journal.rs`, confirmed in `sync.rs::resolve_absent` |
| `" [📅]("` is a literal parse key for the Google-owned badge span | `lifecycle.rs:207`; also `capture_pomodoros_agenda.rs` (`calendar_url`), bob-plugins `291-plugin-gcal-events.js` |
| The stamp parser rejects any trailing text (`if !rest.is_empty() { return None }`) | `stamp.rs:141` |
| `parse_calendars` accepts duplicates — `primary` plus the primary's email would double-fetch | `config/gcal.rs:443` |
| A journaled row whose calendar left the config still gets a per-row gog lookup; day 2+ of a multi-day all-day event then fails `starts != day` → false `Moved` removal, and a 404 → `Deleted` | `sync.rs::resolve_absent`, `lookup_verdict` (~1191–1315) |
| `bob gcal sync` writes nothing when the target daily note is missing, lacks `## Pomodoros`, or still holds Templater tags | `docs/gcal.md` § Sync |

### Hosts

| Host | bob-gcal client | Role |
| --- | --- | --- |
| apollo (this machine) | **none** (`no_client`, re-verified) | Cannot verify live |
| athena | logged in; ran the read-only dry run | Acceptable for verification |
| Mac (`kellys-macbook-pro-local`) | logged in; author of nearly all journal records | The de facto writer; preferred for the acceptance run. `gcal.writer` is unset — note its host label already changed once before pinning |

`~/.config/bob/config.yml` is chezmoi-managed and currently has `gcal.calendars`
commented out everywhere, so production syncs only `primary`.

## How the researcher disagreements resolved

1. **`eventType` (the big one).** grk, mus, and gem inferred from Google's birthday
   cover art in the screenshot that Ava is `eventType: birthday` and made a
   `classify.rs` allowlist change the centrepiece of their designs. Live API reads by
   cdx, cld, and the lead all show **`eventType: default`** — Google decorates the
   popup with birthday chrome regardless. **No classifier change is needed for v1.**
   Accepting `eventType: birthday` remains a reasonable, separate opt-in if the
   contacts-birthday layer is ever wanted (see Follow-ups).
2. **Provenance mechanism.** Four distinct proposals; resolution in
   [Design](#recommended-design-calendar-marks) and
   [Alternative](#the-main-alternative-a-named-badge). The qualifier-chip option
   (`· *Birthdays*`, grk/mus) is eliminated outright: gem showed `split_qualifier`
   ignores task rows and the Ledger Tools painter only recognises
   `maybe|free|day N of M`, so it would mix "why context" with "which calendar" and
   not work on Event Tasks.
3. **Host labels.** gem reported its Linux host as "athena" with no client; the host
   was actually apollo (re-verified: `hostname` → apollo, `no_client`). cld's host
   matrix stands.

## Is this a good idea?

Yes. Birthdays are the ideal first secondary calendar: sparse, all-day, read-only,
no attendees, no RSVP churn — they exercise multi-calendar fetch and provenance with
almost zero lifecycle surface. The daily note is where the day is already reviewed; an
all-day bullet at the top of `## Events` is the cheapest possible "call Ava" nudge, and
child bullets under it (`- texted Ava 🎉`) become durable, searchable history that Bob
never touches. The read-only contract
(`decisions:bob-gcal-is-read-only-and-proposes-once`) is untouched: same account, same
`calendar.readonly` grant, same gog transport.

What this feature should **not** do (unanimous across reports):

- **Make birthdays Event Tasks.** Event Task grammar requires a timed span; a checkbox
  would drag in MEET filing, past-day close, ack, and stats for rows nobody works
  against. A real obligation ("buy Ava a gift") is a separately captured task.
- **Sync every visible calendar.** Sidebar visibility is not consent. Time Blocks,
  Tasks, and Recurring Events would flood or fight the note. Explicit opt-in per
  calendar is the product.
- **Select calendars by display name.** Two sidebar entries are both named
  "Birthdays"; names are user-editable and silently retarget. IDs only.
- **Dedupe across calendars by title or iCalUID in v1.** Silent drops lose provenance;
  birthdays can't hit this case anyway. File as a follow-up bead when the feature
  lands.
- **Teach bob to write its own config.** chezmoi owns `~/.config/bob/config.yml`.

One honest limitation to accept (gem): a same-day bullet gives zero gift lead time.
That is Google-notification or future-lookahead territory, not a daily-note concern;
VIP birthday prep can stay as recurring vault tasks.

## Requirement adjustments (explicitly called out)

1. **Reframe the work.** Not "build multi-calendar sync" but *expose calendar identity,
   harden the multi-calendar paths that become reachable, and enable Birthdays by
   config*. Proven by the dry run.
2. **"Event task" → all-day context bullet.** The request's own "all-day bullet"
   wording wins over its "event task" wording. Birthdays never become tasks.
3. **"Always clear which calendar" is defined as:** every row from a **non-primary**
   calendar carries that calendar's mark in the row text itself (visible in raw
   Markdown, Obsidian, `list`, sync output, git diffs); primary rows stay unmarked, so
   absence unambiguously means "my calendar" and existing rows see zero churn. JSON
   gains explicit calendar fields everywhere rows are reported.
4. **Identify by calendar ID, never name.**
5. **No classifier change in v1** (adjusted *against* three of five reports, on live
   evidence). The contacts-birthday layer stays out of scope.
6. **Verification is date-pinned and host-aware.** `-D yesterday` targets Ava only
   while today is 2026-11-15; after that, use `-D 2026-11-14`. Run on the Mac
   (preferred) or athena — never apollo. Precondition: the target daily note must
   exist and be Templater-rendered, or sync silently waits. Dry-run first; never `-F`;
   rerun to prove idempotence.
7. **Config lands in the chezmoi source**, then `chezmoi apply` on the syncing host
   (athena's copy is already drifting behind apollo's).

## Recommended design: calendar marks

The row grammar is `prefix **time** title [· *qualifier*] badges [suffix]`; Google owns
time, title, and badges via journaled span hashes. The mark rides **inside the
Google-owned title span**, so no parse contract anywhere changes, and the existing
three-way span merge does all migration work.

### Config

```yaml
gcal:
  root: meet_inbox
  calendars:
    - id: primary                 # unmarked rows
    - id: kjs04hafl3btrilujllivid3s8@group.calendar.google.com
      mark: 🎂                    # Birthdays
      # root: love                # optional; only affects timed events on this calendar
```

Validated at config load (setup error, exit 2, naming the key):

- **`mark` is required on every non-primary entry**, optional on `primary`. Error text
  suggests a fix: `gcal.calendars[1] (kjs04…) needs a mark … add e.g. "mark: 🎂"`.
- **Mark shape:** one short non-ASCII token (≤ 8 Unicode scalars, allowing ZWJ
  sequences and flags), no whitespace, no ASCII. Reject reserved glyphs: Tasks-plugin
  signifiers (`📅 ⏳ 🛫 ✅ ➕ ❌ 🔁 ⏫ 🔼 🔽 ⏬ 🔺 🆔 ⛔ 🏁`) and Bob's own
  (`📹 📍 🍅 ✎ ↤ ↦ ↻ ⚠ ⚑ ≡ 🥀`).
- **Marks unique** across configured calendars; **calendar entries unique** — duplicate
  IDs rejected at load, `primary` + the primary's literal email detected at fetch time
  when gog reports which calendar is primary. Marks are presentation only: they never
  select calendars, affect roots, recurrence, task type, time accounting, or identity.
- A bare string entry stays valid for `primary` only; non-primary entries need the map
  form (they need a mark). This is nominally breaking (`feat(gcal)!` per
  `decisions:bob-cli-releases-ride-a-daily-train`) though nobody has a multi-calendar
  config today.

Rejected default: deriving marks from Google calendar colours — the 24→9 emoji mapping
collides (`#7bd148` and `#42d692` both → 🟢) and churns rows on recolour. A
human-chosen glyph is deterministic and clearer.

### Rendering and ownership

- `render_task_row` / `render_context_row` emit `"{mark} {escaped_title}"` when the
  row's calendar has a mark; the planner's fresh title span uses the same string, so:
  new rows are born marked; **untouched** rows pick up an added/changed/removed mark in
  place on the next sync; hand-edited titles keep the user's text with the existing
  once-only `kept_edit` notice. Calendar identity survives edits in the journal and the
  `📅` URL.
- **Block IDs, the `[type:: MEET]` probe, similar-task probes, and `@route` stripping
  all compute from the bare `occurrence.title`** — they already do; pin with tests.
- Context qualifiers keep their slot: `- **all day** 🎂 Ava's Birthday · *day 2 of 3* [📅](…)`.
- All-day rows keep sorting at local midnight, directly under the stamp.
- **Unchanged on purpose:** the `📅` badge and its URL, `split_row_spans`, adoption by
  URL/block ID, the stamp line, context-row semantics, all-or-nothing snapshots.
  **bob-plugins and Bob Mac Capture need no changes** — the mark is title text, which
  every surface already displays (this is the key reliability win).

### CLI surfaces (all additive; `schema_version` unchanged)

- `bob gcal calendars`: `MARK` column (`—` when none) + `"mark"` in JSON; put the
  human name and sync status before the long ID and keep the full ID copyable.
- `bob gcal list`: EVENT cell shows the mark exactly as the note will; header names
  the sync set (`<account> + 🎂 Birthdays`); JSON events gain
  `calendar: {id, name, mark}` (keep `calendar_id`; `title` stays bare).
- `bob gcal sync`: human rows show the mark; JSON `rows[]` gain `calendar_id` and
  `calendar: {id, name, mark}`. Update `docs/reference/json-outputs.md` /
  `docs/_meta/contracts.yml`.
- `bob gcal doctor`: a calendars check — every configured ID exists in the account,
  marks valid and unique, friendly summary (`2 synced: primary, 🎂 Birthdays`).
- **No new sync flags.** In particular no `bob gcal sync -C ID`: a single-calendar
  snapshot would make every other calendar's journaled rows look absent and drive
  cancellations.

### Multi-calendar hardening (same PR — these paths become reachable)

1. **Duplicate entries are a setup error**, including the `primary`/email alias pair
   (verified gap at `config/gcal.rs:443`).
2. **De-configured calendar: freeze, don't lookup.** In `resolve_absent`, a journaled
   key whose calendar is no longer configured gets `LeftAlone("calendar no longer
   synced")` with **no** gog lookup, reported once. This fixes the verified false-`Moved`
   removal for day-2 multi-day all-day rows and the `Deleted` verdict a 404 would
   produce after a calendar is unshared or deleted. Removing a calendar from config
   means "stop managing this source" — prior rows and journals stay; re-adding resumes
   the same identities.
3. **Configured-but-missing calendar fails pre-fetch** with a named setup error
   (`gcal.calendars[1] kjs04… is not in <account>'s calendar list · bob gcal calendars`)
   instead of an opaque gog 404. Runs stay all-or-nothing; per-calendar fault isolation
   is not worth its complexity yet.

### Docs and memory

- `docs/gcal.md` (Configuration incl. `mark` rules, Calendars/List columns, Events
  anatomy, "Who owns each part of a row" gains: *Calendar mark — your config — part of
  the Google-owned title span; follows config while the title is untouched*, Known
  limits: cross-calendar duplicates), `docs/reference/vault-format.md` § Events,
  `docs/reference/configuration.md#gcal`, `docs/reference/json-outputs.md`,
  `docs/guides/connect-google-calendar.md` ("add another calendar" step). Read
  `sase/memory/docs.md` and `sase/memory/cli_rules.md` before these changes.
- **New decision record** (via `/sase_memory_write`), e.g.
  `decisions:non-primary-calendars-wear-a-mark`: calendars are selected by id; every
  non-primary calendar's rows begin their title with that calendar's configured, unique
  mark; primary rows are unmarked. Rejected: named badge, qualifier chip, Obsidian tag,
  inline field, per-calendar sections, plugin-only paint, stamp-only legend, selection
  by name, colour-derived marks. Reopens when marks need machine parsing or a stamp
  legend lands.
- No manual version bump or CHANGELOG edit; the release train owns both.

### Tests (fake gog)

Extend `tests/gcal_support/fake_gog.py` to serve and fail event lists **by calendar
ID** and single-event lookups by `(calendar_id, event_id)` — today it serves one
fixture regardless of calendar, so multi-calendar tests would be vacuous. Then:

- Two-calendar fixture: all-day context row born marked, sorted under the stamp,
  idempotent rerun, JSON `calendar` fields; existing timed tasks byte-identical.
- Mark migration: config mark change updates an untouched row; hand-edited title kept
  and reported once; mark removal un-marks untouched rows.
- Timed event on a marked calendar: marked Event Task title, block ID minted from the
  bare title, MEET filing unchanged.
- Config errors: missing mark, reserved glyph, ASCII mark, duplicate mark, duplicate
  ID, `primary`+email alias; `primary` with no mark is fine.
- Same event ID on two calendars → separate rows, independent lifecycle state.
- De-configured calendar rows (incl. a day-2 multi-day all-day row): left alone, no
  lookup, one report. Configured-but-missing calendar: named error, nothing written.
- Later-page / second-calendar fetch failure → no writes (test a failure *after* a
  successful first page, not only first-call failure).
- All-day recurrence: exclusive end, next-year occurrence distinct, leap-day fixture;
  trust Google's instance dates — no local recurrence engine.
- `calendars`/`list` table and JSON snapshots.

**Size:** one medium bob-cli-only PR, roughly 500–800 lines including tests and docs.

## The main alternative: a named badge

`[📅 Birthdays](url)` — the calendar's name inside the existing badge (cdx and gem's
choice) — is the strongest rejected option and worth recording properly. It is more
self-documenting than a glyph. It lost on reliability and blast radius: `" [📅]("` is a
literal parse key in `lifecycle.rs` (span splitting), `capture_pomodoros_agenda.rs`
(`calendar_url` extraction), bob-plugins Live Preview badge detection, and Mac Capture's
`iconLinkEnd` — four parse sites across three repos, each a version-skew hazard, and
the label still wouldn't reach title-only surfaces (Mac agenda, `list` EVENT cell)
without extra JSON plumbing that the mark gets for free. gem's report contains the
complete compatibility checklist should this ever be revisited; a stamp legend
(`… · 🎂 Birthdays`) is the natural later complement once the stamp parser accepts
trailing segments. gem's further extensions (`mode: context`, per-calendar `ack:`,
Google-colour→hue mapping) are deliberately deferred: birthdays are already context by
the all-day rule, ack already skips all-day rows, and none are needed to land Ava.

## Rollout and acceptance

1. Land the bob-cli change with the fake-gog tests; run the repo's verification gate.
2. Add `- id: kjs04hafl3btrilujllivid3s8@group.calendar.google.com` with `mark: 🎂`
   in the **chezmoi source** for `~/.config/bob/config.yml`; `chezmoi apply` on the
   verification host.
3. On the Mac (preferred; athena acceptable; apollo impossible), with the **updated**
   binary: `bob gcal doctor`, then `bob gcal calendars` (Birthdays shows `🎂 yes`),
   then `bob gcal list -D 2026-11-14 -a` (Ava present as `context`).
4. `bob gcal sync -D 2026-11-14 -d`: expect exactly the stamp refresh plus
   `+- **all day** 🎂 Ava's Birthday [📅](…eid=MHJvbzlw…)` under the stamp; Swings! and
   the "Brave" row byte-identical. (Past-day sync may also legitimately settle older
   eligible meetings — inspect the whole diff rather than assuming Ava is the only
   possible change.)
5. `bob gcal sync -D 2026-11-14` for real — this satisfies the requested
   `-D yesterday` while today is still 2026-11-15; afterwards the explicit date is the
   honest form. Then **rerun**: no duplicate row, only the stamp minute may move.
6. Inspect `2026/20261114.md` in Obsidian (Reading and Live Preview): one Ava bullet,
   visible 🎂, working 📅 link, no checkbox/`#task`/MEET/root. Optional:
   `bob gcal sync -D 2026-11-09 -d` should show `🎂 Dad's Birthday` the same way.
7. If the note were missing or its Events section held, report that state — it is not
   a passing run. Never `-F` to make the test pass.

## Follow-ups and non-goals (config rows or beads, not v1)

- **More calendars:** Surf `🏄`, Holidays `🎉`, Health `🩺` + `root: body`. Time
  Blocks/Bloomberg need a per-calendar row policy first (their timed events would
  become MEET Event Tasks, probably wrongly).
- **Cross-calendar iCalUID dedupe** — file a task bead when this feature lands.
- **Contacts birthdays**: an explicit opt-in admitting `eventType: birthday` as
  context; not needed while birthdays live in the user-created calendar.
- **Stamp legend** once both stamp parsers accept trailing segments (also proves "🎂
  was consulted; no birthday today").
- **Ledger Tools polish** (tooltip naming the calendar, colour tint) and a **Mac
  all-day banner** — bob-cli JSON first, per `decisions:mac-capture-is-a-thin-client`.
- **Lead time** ("birthday in 3 days") is out of scope for daily-note residence; VIP
  gift prep stays as recurring vault tasks.
- Consider pinning `gcal.writer` — but the Mac's host label changed once already
  (`kellys-mbp` → `kellys-macbook-pro-local`); check `bob gcal doctor`'s label first.

## Report provenance

- **cld** contributed the decisive current-binary dry run, the marks design, the
  reserved-glyph/validation rules, the host matrix, and the de-configured-calendar bug;
  its design is adopted nearly whole.
- **cdx** independently verified the event's true `eventType` via the Mac's gog
  adapter, contributed the identity/alias hardening (primary-vs-email journal keys,
  CalendarList completeness, label-never-identity), the ownership-preserving migration
  rules, and the honest acceptance protocol.
- **gem** contributed the deepest cross-repo compatibility audit (lifecycle, capture
  agenda, plugins, Mac) that both sized the named-badge alternative and justified
  rejecting it, plus the hybrid insight that gift prep stays in recurring tasks.
- **grk** and **mus** contributed the two-Birthdays disambiguation framing, the
  "provenance-by-root is a trap" warning, the sync-precondition (missing/unrendered
  note waits silently), and the qualifier-slot analysis — though both (with gem) built
  on the `eventType: birthday` premise that live evidence refuted; their classifier
  change is recorded here as a deferred opt-in, not a v1 requirement.
