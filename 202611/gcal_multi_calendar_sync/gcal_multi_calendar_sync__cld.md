# Multi-calendar `bob gcal sync`, starting with Birthdays (cld)

*Research for: "make `bob gcal sync` support multiple calendars from the same account,
starting with Birthdays; always make it clear which calendar each Event Task came from;
verify with `bob gcal sync -D yesterday` (Ava's birthday as an all-day bullet)."*

## TL;DR

1. **Bob can already sync more than one calendar.** `gcal.calendars` has been in the
   config schema since `bob gcal sync` first shipped. The snapshot fetches each configured
   calendar, the journal keys rows by `(calendar_id, event_id)`, and per-calendar
   `root:` works. I ran a dry run on athena with a temporary config that added the
   Birthdays calendar. The current binary already plans exactly the row you asked for:

   ```diff
    *↻ synced Sun 2026-11-15 11:11 · [<account>](…/r/day/2026/11/14?…)*
   +- **all day** Ava's Birthday [📅](https://www.google.com/calendar/event?eid=MHJvbzlw…)
    - [x] #task **0900-0915** Swings! [📅](…) [root:: abby] [type:: MEET] …
   ```

2. **The missing piece is identity, not syncing.** The row above does not say which
   calendar it came from. In code, `SnapshotEvent.calendar_name` is
   `#[allow(dead_code)]`, the `bob gcal list` table has no calendar column, and the sync
   JSON rows carry no calendar. So the real feature is "make the calendar visible", plus
   a few hardening fixes that only matter once there is more than one calendar.
3. **Recommendation: a per-calendar *mark*.** Each non-primary calendar gets a short
   glyph that Bob writes as the first token of every row's title from that calendar:
   `- **all day** 🎂 Ava's Birthday [📅](…)`. The mark is set in config
   (`mark: 🎂`), required for non-primary calendars, validated at load, and checked for
   uniqueness. Primary-calendar rows stay unmarked, so no mark means your own calendar.
   The mark rides inside the existing Google-owned title span, so the row grammar,
   the `📅` identity badge, the stamp, the Ledger Tools plugin, and the Mac app all stay
   unchanged. The planner's three-way span merge handles migration with no new code.
4. **Requirement adjustments** (details in [§3](#3-critique-of-the-plan-and-my-adjustments)):
   - Primary rows stay unmarked.
   - Calendars are chosen by **id, never by name**. Your sidebar shows two "Birthdays".
   - Verify with `-D 2026-11-14`, not `-D yesterday`.
   - Run the verification on a host with the Calendar grant (the Mac or athena).
     **apollo has none.**
   - The config change goes through chezmoi.

## 1. What I verified

| Fact | Evidence |
| --- | --- |
| Ava's Birthday is on a **user-created** calendar "Birthdays", id `kjs04hafl3btrilujllivid3s8@group.calendar.google.com`, colour `#7bd148`, owner role | Screenshot ("Created by: Bryan Bugyi", lime dot); `bob gcal calendars -f json` on athena; Calendar connector `list_calendars` |
| The event is `eventType: default`, all-day `2026-11-14 → 2026-11-15`, `transparency: transparent`, annual series `0roo9pdfmor2uhp72o0h5u8k31`, organizer = the Birthdays calendar (`self: true`), no attendees | Calendar connector `list_events` on that calendar for Nov 8–16. Dad's Birthday on Nov 9 is the same shape |
| The **other** "Birthdays" in the sidebar (darker green, listed first) is not in the calendar list API. It is Google's contacts-birthday view: `eventType: birthday` events on the primary calendar. None fall in Nov 8–16 | API calendar list has one Birthdays; `list_events eventType=BIRTHDAY` on primary returned nothing |
| Bob omits every `eventType` other than `default`/`fromGmail`, so contacts birthdays would never appear even on primary | `src/native/gcal/classify.rs` `classify()` |
| All-day events with a Yes answer (own or no guests) are **context rows**: `- **all day** title [📅](…)`, no checkbox, no `[root::]`, no MEET link | `classify.rs`; `render.rs::render_context_row`; `docs/reference/vault-format.md` § Events section |
| Multi-calendar fetch exists: one gog call per configured calendar per contiguous day run, all-or-nothing | `snapshot.rs::FetchContext::fetch_days` |
| Journal keys use the **configured** id string (`"primary"`, not the email) | `.bob/gcal/*.jsonl` (`"key":{"calendar_id":"primary",…}`) |
| Calendar name is computed but never rendered | `snapshot.rs` `SnapshotEvent.calendar_name` (`#[allow(dead_code)]`); `list.rs` headers `TIME EVENT RSVP ROOT VAULT` |
| Duplicate calendar entries are not rejected (`- primary` plus `- <your email>` would fetch the same calendar twice) | `config/gcal.rs::parse_calendars`; `gcal/config.rs::from_settings` |
| A journaled row whose calendar was **removed** from config goes through a per-row gog lookup. If the event is still on that day it is left alone. Day 2+ of a multi-day all-day event, however, fails `starts != day` and gets **`Moved` → an untouched context row is removed** with a false "Moved to …" reason | `sync.rs::resolve_absent` / `lookup_verdict` |
| A shared event (same iCalUID) visible on two configured calendars would produce **two rows**. iCalUID is journaled but never used for dedupe | `grep ical_uid src/native/gcal` |
| `📅` is a parse key in bob-cli and in two plugins | `lifecycle.rs::split_row_spans` (`" [📅]("`); `plan.rs` adoption; `replaced.rs`; `capture_pomodoros_agenda.rs` (`calendar_url`); bob-plugins `291-plugin-gcal-events.js` (badge list `["📅","📹","📍"]`) and `015-prompt-block-id-naming.js` |
| The stamp grammar is closed: any text after the account link makes the stamp malformed | `stamp.rs::parse` (`if !rest.is_empty() { return None }`) |
| **Host access:** apollo has no `bob-gcal` client (`no_client`). athena is logged in. The Mac (the writer, host label `kellys-macbook-pro-local`) answered SSH today. `gcal.writer` is unset everywhere | `bob gcal calendars` on apollo and athena; `ssh mac hostname`; journal host labels |

### The current binary already handles the Birthdays row

On athena I wrote a temporary `BOB_CONFIG_FILE` with
`calendars: [primary, kjs04…@group.calendar.google.com]` and ran two read-only commands.
`bob gcal list -D 2026-11-14 -a` showed:

```text
Google Calendar · Sat 2026-11-14 · <account>, Birthdays · synced 6 d ago on athena
TIME         EVENT                        RSVP   ROOT    VAULT
all day      Ava's Birthday               ✓ own  —       context
09:00-09:15  Swings!                      ✓ own  ● abby  task · MEET · off-clock via love
19:00-20:00  Some of "Brave" w/ Abby ≡ 1  ✓ own  ● abby  task · MEET · off-clock via love
```

`bob gcal sync -D 2026-11-14 -d` planned only the stamp refresh plus the one added
context row shown in the TL;DR. Its JSON row was
`{"kind":"context","action":"added","title":"Ava's Birthday","time":"all day","root":null,…}`.
That row has no calendar field.

## 2. Is this a good idea?

**Yes.** It fits Bob's model cleanly:

- **One pane per day.** The daily note is where you already review the day. A 🎂 row at
  the top of `## Events` is the cheapest possible "call/text Ava" nudge. The `#pre`
  checklist line "Review Calendar for today and tomorrow" becomes partly automatic.
- **A place for what happened.** Context rows accept your child bullets, and Bob never
  touches them. `- texted Ava 🎉 · she starts the new job Monday` under the birthday row
  is durable, searchable history. Searching `🎂` in Obsidian lists every birthday across
  years.
- **No new Google surface.** Same account, same read-only grant
  (`calendar.readonly` already covers every calendar), same gog transport. This keeps
  `decisions:bob-gcal-is-read-only-and-proposes-once` intact.
- **Low noise.** Birthdays are sparse, all-day, and become context rows. They never
  create MEET links, never affect Pomodoros or the plan budget, never get `#unacked`, and
  never get cancelled as "worked" tasks.

What I would **not** do:

- **Make birthdays tasks.** A same-day checkbox you must tick on every birthday is
  ceremony. Event Task grammar also requires a timed `**HHMM-HHMM**` span, so all-day
  Event Tasks would be a large grammar change. Capture a real task when there is one
  ("buy Ava a gift").
- **Read birthdays from Google Contacts** (People API). That needs a new scope and grant,
  and you track birthdays in a calendar on purpose.
- **Rely on the daily note for lead time.** A same-day row cannot remind you to buy a
  gift. That is Google's notification's job, or a later "upcoming" view (see
  [§7](#7-follow-ups-and-non-goals)).

## 3. Critique of the plan and my adjustments

The plan reads as "build multi-calendar sync". It already exists, so the work is
different from what the request implies. My adjustments:

| # | Adjustment | Why |
| --- | --- | --- |
| A1 | **Reframe:** the feature is *calendar identity plus multi-calendar hardening*, not a new sync path. Enabling Birthdays is a one-line config change | Proven by the dry run above |
| A2 | **"Always clear which calendar" means:** every row from a **non-primary** calendar starts with that calendar's mark. Primary rows stay unmarked, so no mark means your own calendar. A primary mark is opt-in (`mark:` on the `primary` entry) | Marking primary would rewrite every existing meeting row on its next untouched sync and add a glyph to most rows for no information. Absence is unambiguous once every non-primary calendar is guaranteed a mark |
| A3 | **Select calendars by id only, never by display name** | Your sidebar shows two calendars named "Birthdays". Names are user-editable in Google and silently retarget. Ids are stable. `bob gcal calendars` already prints ids to copy |
| A4 | **Verify with `bob gcal sync -D 2026-11-14`**, preceded by `-d` | `yesterday` is Nov 14 only until midnight. If the implementation lands on Nov 16, `-D yesterday` targets Nov 15, which has no birthday, and the check passes vacuously. Use the explicit date (you can mention `-D yesterday` in the report) |
| A5 | **Run the verification on the Mac (the writer) or athena, never apollo** | apollo has no `bob-gcal` OAuth client (`no_client`). The Mac is the documented single writer; athena has a grant and has synced before |
| A6 | **Change config in the chezmoi source**, then `chezmoi apply` on the writer | `~/.config/bob/config.yml` is chezmoi-managed (Bob's own error hint says so). athena's copy is already behind apollo's (`root:` still commented), so drift is real |
| A7 | **Add three small hardening fixes in the same change:** reject duplicate calendar entries; leave rows from a de-configured calendar alone without a lookup; fail clearly when a configured calendar id is not in the account | Multi-calendar makes these reachable; see [§5.5](#55-multi-calendar-hardening) |

## 4. Options for showing which calendar a row came from

The row grammar today is
`prefix **time** title [· *qualifier*] badges [suffix]`. Google owns time, title, and
badges, which are hash-tracked in the journal. You own the checkbox, `[root::]`,
children, and the row itself.

| Option | Example | Intuitive | Reliable | Beautiful | Cost / risk |
| --- | --- | --- | --- | --- | --- |
| **A. Mark at the start of the title** (recommended) | `- **all day** 🎂 Ava's Birthday [📅](…)` | High: a glyph you chose, read before the title, like Google's coloured dot | **High:** no grammar change; rides the existing title span and three-way merge; nothing else parses titles | **High** | Small: config, render, validation, list/JSON |
| B. Replace the `📅` glyph per calendar | `- **all day** Ava's Birthday [🎂](…)` | High | **Low:** `📅` is a parse and adoption key in about 6 places across bob-cli and bob-plugins; loses the universal "📅 opens Google" affordance | High | Cross-repo contract change; version-skew hazards |
| C. Qualifier chip | `- **all day** Ava's Birthday · *🎂 Birthdays* [📅](…)` | Very explicit | Medium: the qualifier slot holds one chip on context rows only (`split_qualifier`), and Ledger Tools only paints `maybe/free/day N of M` | Medium; wordy on timed rows | Grammar plus plugin change |
| D. Obsidian tag | `… [📅](…) #cal/birthdays` | Medium; clickable, searchable | Medium: becomes a task tag on Event Tasks; Tasks plugin and Bob tag semantics; noisy | Low–medium | Grammar change in the badge run |
| E. Inline field | `… [📅](…) [cal:: Birthdays]` | Medium; Dataview-queryable | Medium | Low (Ledger Tools already hides `[buffer::]`-style fields; hiding defeats "always clear") | Grammar plus plugin change |
| F. `### Birthdays` sub-sections | separate groups under `## Events` | Medium | Low: breaks time-ordered insertion, the replaced-section logic, and plugin section scans | Medium | Large |
| G. Plugin-only paint (decode the calendar from the `eid` in the URL) | colour chip at render time | Medium | Medium | High in Obsidian, **invisible in raw Markdown, git diffs, Mac, CLI** | Fails "always clear" |
| H. Stamp legend | `*↻ synced 11:11 · [<account>](…) · 🎂 Birthdays*` | Helps decode the marks | **Low right now:** the stamp parser rejects trailing text, so mixed-version hosts would flip-flop the line; the plugin also parses it | Medium | Cross-repo grammar change. Good later as a complement to A, not a replacement |

**A wins on all three of your criteria.** The mark is plain text in the vault, so it
reads the same in raw Markdown, Live Preview, Reading view, git diffs, `bob gcal list`,
and the Mac agenda (which already displays Event Task titles). The two strongest
alternatives fail differently: B is beautiful but breaks a cross-repo parse contract,
and C is explicit but changes grammar in two repos. The decision record should name
them as rejected.

## 5. Recommended design

### 5.1 Config

```yaml
gcal:
  root: meet_inbox
  calendars:
    - id: primary # your own calendar; unmarked rows
    - id: kjs04hafl3btrilujllivid3s8@group.calendar.google.com # Birthdays
      mark: 🎂
      # root: love # optional; only matters for timed events on this calendar
```

Rules, validated when config loads (setup error, exit 2, naming the key, consistent with
`gcal.colors` and `description_lines`):

- **`mark` is required on every non-primary entry.** Example message:
  `gcal.calendars[1] (kjs04…@group.calendar.google.com) needs a mark so its rows show
  which calendar they came from; add e.g. "mark: 🎂"`. A bare id string is still
  accepted for `primary`, and for non-primary entries only once they have a mark (so
  they must use the map form).
- `mark` is optional on `primary`. Default: none.
- **Mark shape:** one short non-ASCII token (emoji or symbol) of at most 8 Unicode
  scalars, which leaves room for ZWJ and variation selectors (`🧑‍🤝‍🧑`, flags). No
  whitespace and no ASCII. Reject reserved glyphs:
  - Tasks-plugin signifiers: `📅 ⏳ 🛫 ✅ ➕ ❌ 🔁 ⏫ 🔼 🔽 ⏬ 🔺 🆔 ⛔ 🏁`.
  - Bob's own glyphs: `📹 📍 🍅 ✎ ↤ ↦ ↻ ⚠ ⚑ ≡ 🥀`.

  This rejects, for example, `🔁` for your "Recurring Events" calendar with a clear
  reason.
- **Marks are unique** across configured calendars.
- **Calendar entries are unique.** Duplicate ids are rejected, and so are `primary` and
  the primary's literal id together (the second is detected at fetch time, when gog
  reports which calendar is `primary`).

Precedent and contract: `feat(gcal)!:` because a bare non-primary id that used to be
accepted now needs a mark. Nobody has one configured today (every host has
`calendars:` commented out), so the break is nominal, but per
`decisions:bob-cli-releases-ride-a-daily-train` it is still marked.

> Considered and rejected for the default: deriving a mark from the Google calendar
> colour (🟢 for `#7bd148`). It looks faithful to the screenshot's dot, but the lossy
> mapping from 24 colours to 9 emoji collides: Birthdays `#7bd148` and Holidays
> `#42d692` both become 🟢. It also depends on runtime Google data, and the
> rows churn when you recolour a calendar. A required, human-chosen glyph is clearer and
> deterministic.

### 5.2 Row rendering and ownership

- `render_task_row` and `render_context_row` write `"{mark} {escaped title}"` when the
  row's calendar has a mark. The **planner's fresh title text** (`plan.rs`,
  `("title", escape_title(&occurrence.title))`) uses the same marked string, so the
  three-way merge does the rest:
  - **New rows** are born marked.
  - **Untouched existing rows** (current title hash = journaled hash) pick up an added or
    changed mark in place on the next sync. This is how a mark edit in config
    propagates.
  - **Rows whose title you edited** keep your text, and the existing once-only
    `kept_edit` notice applies. Deleting the 🎂 by hand is your call. The journal and the
    `📅` URL's `eid` still record the calendar.
- **Block IDs are minted from the bare Google title**, never the marked one. The same
  goes for the `[type:: MEET]` probe (`needs_meet_type`), similar-task probes, and the
  `@route` stripping. All of these already run on `occurrence.title`; tests must pin it.
- Context rows keep their qualifier after the title:
  `- **all day** 🎂 Ava's Birthday · *day 2 of 3* [📅](…)`.
- Add a row to the "Who owns each part of a row" table in `docs/gcal.md`:
  *Calendar mark — your config — part of the Google-owned title span; follows config
  while the title is untouched.*

What Nov 14 will look like:

```markdown
## Events

*↻ synced Sun 2026-11-15 11:40 · [<account>](https://calendar.google.com/calendar/r/day/2026/11/14?authuser=…)*
- **all day** 🎂 Ava's Birthday [📅](https://www.google.com/calendar/event?eid=MHJvbzlwZGZtb3IydWhwNzJvMGg1dThrMzFfMjAyNjExMTQga2pzMDRoYWZsM2J0cmlsdWpsbGl2aWQzczhAZw)
- [x] #task **0900-0915** Swings! [📅](…) [root:: abby] [type:: MEET] [fresh:: 2026-11-14]  [completion:: 2026-11-14] ^swings
- [x] #task **1900-2000** Some of "Brave" w/ Abby [📅](…) [root:: abby] [type:: MEET]  [completion:: 2026-11-14] ^grocery-store-w
	- She didn't like it...
```

All-day rows sort at local midnight, so new birthday rows land directly under the stamp.
Existing lines are never reordered.

### 5.3 CLI surfaces (all additive)

- **`bob gcal calendars`:** add a `MARK` column (`—` when none) and `"mark"` in JSON.
  The Birthdays row then reads `… #7bd148  🎂  yes  meet_inbox`.
- **`bob gcal list`:**
  - The EVENT cell shows the mark before the title, exactly as the note will
    (`🎂 Ava's Birthday`).
  - The header names synced calendars with their marks:
    `Google Calendar · Sat 2026-11-14 · <account> + 🎂 Birthdays · …`.
  - JSON events gain `"calendar": {"id", "name", "mark"}` next to the existing
    `calendar_id`, and `title` stays bare.
- **`bob gcal sync`:** human row lines show the mark. JSON `rows[]` gain `calendar_id`
  and `calendar: {id, name, mark}`. Update `docs/reference/json-outputs.md` and
  `docs/_meta/contracts.yml` if they enumerate row fields. Additive, so the same
  `schema_version` stays.
- **`bob gcal doctor`:** add a "calendars" check: every configured id is present in the
  account's calendar list, marks are valid and unique, and the summary is
  `2 synced: primary, 🎂 Birthdays`.
- **No new flags.** In particular, **do not add `bob gcal sync -C ID`**. A
  single-calendar snapshot would make every other calendar's journaled rows look
  "absent" and drive cancellations or removals. If one is ever wanted, absence detection
  must be scoped to the selected calendars first.

### 5.4 What deliberately does not change

- The `📅` identity badge, the badge order, `split_row_spans`, adoption by URL or block
  ID, and the stamp line.
- **bob-plugins needs no change.** Ledger Tools keys on `**all day**`/`**HHMM-HHMM**`
  and the badge glyphs; the mark is title text.
- **Bob Mac Capture needs no change.** Its idle agenda shows Event Task titles, and
  all-day context rows are filtered out (`AllDayContext` is unreachable there).
- Context-row semantics: no checkbox, no root, no MEET link, never `#unacked`.
- All-or-nothing snapshots. One failing calendar still fails the run, so nothing
  partial is ever written. See 5.5 for making that failure legible.

### 5.5 Multi-calendar hardening

1. **Duplicate entries** are a setup error. Today `- primary` plus `- <primary email>`
   would fetch the same events twice under two keys.
2. **De-configured calendar.** In `resolve_absent`, a journaled key whose `calendar_id`
   is no longer in `gcal.calendars` gets a new verdict, `LeftAlone("calendar no longer
   synced")`, **without a gog lookup**, reported once. This fixes the
   multi-day-all-day "Moved" misverdict for removed calendars and saves one API call per
   orphaned row. Removing Birthdays from config should freeze its rows, never remove
   them.
3. **Missing or inaccessible calendar.** Before fetching, check each configured id
   against the already-fetched calendar list (`FetchContext.calendars`). If one is
   missing, fail with a named setup error:
   `gcal.calendars[1] kjs04… is not in <account>'s calendar list · bob gcal calendars`.
   This replaces an opaque gog 404 for a deleted or unshared calendar. Keep the run
   all-or-nothing: a partial snapshot would misjudge absent rows. Per-calendar fault
   isolation (`required: false`) is not worth its complexity yet.
4. **Cross-calendar duplicates (same iCalUID on two calendars):** a **follow-up, not
   v1.** Birthdays events are unique to their calendar, so v1 cannot hit this. It
   becomes real once a calendar you invite to meetings (Health, Time Blocks) is synced.
   The rule should be: one row per `(iCalUID, original start)` per day; an
   already-journaled copy wins, otherwise config order wins; the loser is reported as a
   `duplicate` skip. File it as a task bead when this lands.

### 5.6 Docs and memory

- `docs/gcal.md`:
  - Configuration: the `mark` key, its rules, and the example.
  - Calendars: the MARK column.
  - List: the EVENT mark and header.
  - Events: the anatomy and the ownership-table row.
  - Root selection: unchanged.
  - Known limits: cross-calendar duplicates.
- `docs/reference/vault-format.md` § Events: "a row from a non-primary calendar begins
  its title with that calendar's mark".
- `docs/reference/configuration.md#gcal`, `docs/reference/json-outputs.md`, and
  `docs/guides/connect-google-calendar.md` (the "add another calendar" step).
- **New decision record** (via `/sase_memory_write`), e.g.
  `decisions:non-primary-calendars-wear-a-mark`:
  - **Claim:** calendars are selected by id; every non-primary calendar's rows begin
    their title with that calendar's configured, unique mark; primary rows are
    unmarked.
  - **Rejected:** badge swap (B), chip (C), tag (D), field (E), sections (F),
    plugin-only paint (G), selection by name, and colour-derived default marks.
  - **Reopens when:** marks need machine parsing, or a stamp legend lands.
- Glossary: the Event Task strand could mention the mark in one clause. Optional.

### 5.7 Tests (fake gog, `BOB_GCAL_GOG`)

- Two-calendar fixture with an all-day context row: born marked, sorted under the stamp,
  idempotent rerun, and JSON `calendar` fields.
- Changing the mark in config migrates an untouched row. A hand-edited title is kept
  and reported once. Removing the mark from config un-marks untouched rows.
- A timed event on a marked calendar: Event Task title marked, block ID minted from the
  bare title, MEET filing unchanged.
- Config errors: missing mark on a non-primary entry, reserved glyph, ASCII mark,
  duplicate mark, duplicate id. `primary` with no mark is fine.
- A de-configured calendar's journaled rows, including a multi-day all-day day-2 row:
  left alone, no lookup, one report.
- A configured calendar id missing from the account fails with the named setup error
  and writes nothing.
- `bob gcal calendars` / `list` table and JSON snapshots.

**Size:** one medium PR in bob-cli only, roughly 500–800 lines including tests and docs.
No plugin, Mac, or vault-format grammar change.

## 6. Rollout and verification

1. Land the bob-cli change with the fake-gog tests.
2. Add the calendar entry with `mark: 🎂` in the **chezmoi source** for
   `~/.config/bob/config.yml`, then `chezmoi apply` on the writer host.
3. Install the updated `bob` on the host that will run the check (the Mac preferred,
   athena acceptable). Confirm with `bob gcal doctor` and
   `bob gcal calendars` (Birthdays shows `🎂 yes`).
4. `bob gcal sync -D 2026-11-14 -d`. Expect exactly two changes: the stamp refresh and
   `+- **all day** 🎂 Ava's Birthday [📅](…eid=MHJvbzlw…)` directly under the stamp.
   Nothing else may change. Swings! and the "Brave" row must be byte-identical.
5. `bob gcal sync -D 2026-11-14` for real. Then rerun it: the row must be reported
   in sync, and only the stamp minute may move.
6. Optional: `bob gcal sync -D 2026-11-09 -d` should show `🎂 Dad's Birthday` the same
   way. Confirm the Nov 14 note looks right in Obsidian (Live Preview context-row
   styling) after vault-sync.

Mixed versions: hosts that run an older `bob` ignore `mark:` (unknown keys are ignored)
and would re-render untouched titles without it if they synced. Keep the Mac as the only
syncing host. Pinning `gcal.writer` is worth considering, but the Mac's host label has
already changed once (`kellys-mbp` → `kellys-macbook-pro-local` in the journals), so
check `bob gcal doctor`'s label before pinning.

## 7. Follow-ups and non-goals

- **More calendars, as config only:**
  - Surf: `🏄`. All-day "good surf day" markers fit context rows perfectly.
  - Holidays in United States: `🇺🇸` or `🎉`. Reader role, no attendees, all-day.
  - Health: `🩺`, with `root: body`.
  - **Time Blocks and Bloomberg** would turn into MEET Event Tasks, which is probably
    wrong for focus blocks. That calls for a per-calendar row policy (`rows: context`,
    or a `type:` other than MEET) before you enable them.
- **Cross-calendar iCalUID dedupe** (see 5.5 item 4).
- **Contacts birthdays** (`eventType: birthday` on primary, the other "Birthdays"):
  could be an opt-in (`gcal.birthdays: 🎂`) that admits that event type as context rows
  with the same mark. Not needed while you keep birthdays in your own calendar.
- **Stamp legend** (option H) once both parsers accept trailing segments. It would also
  prove "🎂 Birthdays was consulted, so no birthday today".
- **Ledger Tools polish:** a tooltip naming the calendar on the mark, or tinting all-day
  rows with the calendar's Google colour. Needs a vault-side calendar catalog; nice, not
  necessary.
- **Mac agenda:** an all-day banner (`🎂 Ava's Birthday`) above Now/Next. Lands in
  bob-cli JSON first per `decisions:mac-capture-is-a-thin-client`.
- **Lead time** ("birthday in 3 days"): out of scope for daily-note residence.

## 8. Risks

| Risk | Mitigation |
| --- | --- |
| The mark leaks into places that key on title text (block IDs, theme probes, route stripping) | Compute all of them from `occurrence.title`; pin with tests (5.7) |
| You edit a marked title and the mark is lost | Your edit wins (existing ownership rule); calendar identity survives in the journal and the `eid` |
| An emoji mark renders differently across platforms | Marks are user-chosen; reserved-glyph and shape validation keep them parse-safe |
| One broken calendar blocks all syncing | Named setup error plus a doctor check; remove the entry to recover |
| A config change applied on one host only | chezmoi plus a single writer; verify on the writer |

## 9. Recommendation

**Ship "calendar marks" as a bob-cli-only change, then turn Birthdays on by config.**

1. Add `mark` to `gcal.calendars` entries: required and unique for non-primary
   calendars, optional for `primary`, restricted to a short non-ASCII glyph, with
   reserved glyphs rejected.
2. Render the mark as the first token of the Google-owned title span on every row from
   that calendar, Event Tasks and context rows alike. Use the existing three-way span
   merge so untouched rows migrate in place and hand edits win. Leave the `📅` badge,
   the stamp, plugins, and the Mac app untouched.
3. Surface the calendar everywhere Bob reports events: `calendars` MARK column, `list`
   EVENT cell and header, sync and list JSON `calendar: {id, name, mark}`, and a doctor
   calendars check.
4. Harden multi-calendar behaviour in the same PR: reject duplicate entries; freeze rows
   from de-configured calendars without lookups; fail clearly on a configured calendar
   missing from the account. File iCalUID dedupe as a follow-up bead.
5. Record the decision (`non-primary-calendars-wear-a-mark`) with the rejected options
   from §4, and update `gcal.md`, `vault-format.md`, `configuration.md`, and
   `json-outputs.md`.
6. Enable `- id: kjs04hafl3btrilujllivid3s8@group.calendar.google.com`, `mark: 🎂` in
   chezmoi. Verify on the Mac (or athena) with `bob gcal sync -D 2026-11-14 -d`, then a
   real run, then an idempotent rerun. Expected result:
   `- **all day** 🎂 Ava's Birthday [📅](…)` under the stamp, and nothing else changed.
