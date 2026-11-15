# Multi-Calendar `bob gcal sync` & Birthdays Design Research

**Author:** Researcher (`gem`)  
**Date:** 2026-11-15  
**Scope:** Independent architecture research, product critique, and end-to-end design for multi-calendar Google Calendar sync (`bob-cli`, `bob-plugins`, `bob-mac-capture`, and the Bob vault), evaluated against Bryan's `"Birthdays"` starter use case.

---

## 1. Executive Summary

The headline surprise from inspecting `bob-cli` is that **most multi-calendar infrastructure already exists**, yet the feature fails at both the **first-mile (`Birthdays`)** and the **last-mile (provenance, disambiguation, and aesthetics)**:

1. **Multi-calendar plumbing is already built:** `gcal.calendars` (`{ id, root? }`), `FetchContext::fetch_days`, `OccurrenceKey { calendar_id, event_id }`, per-calendar journal records (`gcal.row`, `gcal.link`, `gcal.note`, `gcal.ack`, `gcal.series_root`), `bob gcal calendars`, and `-C/--calendar` flags in `bob gcal note` / `bob gcal ack` are already implemented.
2. **Immediate showstopper for `Ava's Birthday`:** In [`classify.rs`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/classify.rs#L134-L136), `bob gcal` omits every event whose Google `eventType` is not `"default"` or `"fromGmail"`. In Bryan's screenshot (`~/tmp/screenshots/20261115_105604.png`), `Ava's Birthday` displays Google Calendar's dedicated birthday-cake illustration banner — a visual signature of `eventType: "birthday"` (also listed by `~/bin/gog calendar events --help`). Without updating `classify`, enabling the `"Birthdays"` calendar will **silently skip `Ava's Birthday` as `event type: birthday`**.
3. **Zero calendar provenance across every user-facing surface:** `SnapshotEvent.calendar_name` is explicitly marked `#[allow(dead_code)]` in [`snapshot.rs`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/snapshot.rs#L37-L38). Today's Markdown rows (`[📅](url)`), `bob gcal list` tables, `bob gcal sync` output and JSON (`ReportRow`), `bob gcal doctor`, and `bob capture-pomodoros --tasks` (Mac Capture Agenda) give no indication of which calendar an Event Task or all-day context row came from.
4. **Duplicate-name trap in Bryan's real account:** Bryan's `My calendars` sidebar contains **two separate calendars both named `Birthdays`** — a teal-green built-in Google Contacts calendar and an olive-green user-created calendar (`Created by: Bryan Bugyi`) containing `Ava's Birthday` and `Dad's Birt...`. Relying on raw Google calendar names without explicit aliases and duplicate disambiguation would collide immediately.

**Recommended direction:** Keep Google Calendar (`Birthdays`) as the source of truth synced into `## Events` as lightweight all-day context rows, fix the `eventType: "birthday"` omission and secondary-calendar semantics (`mode: context`, `label`, `color`, `ack`), and render provenance **inside the existing Google Calendar badge link as `[📅 <label>](<url>)`** on every non-primary calendar (keeping `primary` as compact `[📅](<url>)` by default, with opt-in `label:` if desired), paired with 8-hue Obsidian badge pills, Pomodoro link tooltips, Mac Capture Agenda metadata, and `list`/`sync`/`calendars` CLI+JSON upgrades.

---

## 2. Ground-Truth Audit

### 2.1 Screenshot & Google Calendar Account Evidence

Inspecting `/home/bryan/tmp/screenshots/20261115_105604.png` (Google Calendar week view for Nov 8–14, 2026, `GMT-5`) reveals:

- **9 checked calendars under `My calendars`:**
  1. `Bryan Bugyi` (blue — primary; contains `Swings!`, `Haircut`, `Hercules and Pizza!`, `Some of "Brave" w/ Abby`)
  2. `Birthdays` (teal-green — Google's built-in Contacts-synced `addressbook#contacts@group.v.calendar.google.com` layer)
  3. `Birthdays` (olive-green — custom calendar; holds `Ava's Birthday` on `Saturday, November 14` and `Dad's Birt...` on `Monday, November 9`)
  4. `Bloomberg` (brown)
  5. `Health` (maroon)
  6. `Recurring Events` (gold)
  7. `Surf` (orange)
  8. `Tasks` (blue — Google Tasks special calendar)
  9. `Time Blocks` (indigo)
- **Target event (`Ava's Birthday`) details from popup:**
  - Title: `Ava's Birthday`
  - Schedule: `Saturday, November 14`, `Annually on November 14` (all-day recurring event)
  - Calendar: `Birthdays` (olive-green color dot), `Created by: Bryan Bugyi`
  - Visual header: Google Calendar's pink/yellow/purple birthday cake and balloon illustration — assigned to `eventType: "birthday"` events.

### 2.2 Google Calendar API & `gog` Transport Reality

- `~/bin/gog` on this host (`v0.44.0`) already supports `--event-types` (`default, birthday, focus-time, from-gmail, out-of-office, working-location`).
- [`Gog::events`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/gog.rs#L85-L111) does **not** filter `--event-types`, and requests `eventType,colorId,attendees(self,responseStatus),organizer(self,displayName,email)` in `FIELDS`. Google Calendar's API returns `eventType: "birthday"` events by default when `eventTypes` is unrestricted, with `start.date` / `end.date` all-day bounds (`YYYY-MM-DD`) and `RRULE:FREQ=YEARLY` instances expanded across `--from`/`--to`.
- [`GogCalendar`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/gog.rs#L18-L31) already fetches `id`, `summary`, `primary`, `accessRole`, `backgroundColor`, and `colorId` via `gog calendar calendars --all`.

### 2.3 Local Config, Host Environment & Live Vault State

- [`~/.config/bob/config.yml`](file:///home/bryan/.config/bob/config.yml#L92-L103) currently defines only `gog: ~/bin/gog` and `root: meet_inbox`; `account`, `writer`, `calendars`, `colors`, `tentative`, and `timeout_secs` are all commented out.
- Running `bob gcal calendars -f json` on this Linux host (`athena`) fails with `no_client`: `athena` holds no `bob-gcal` OAuth token. The `.bob/gcal/` journals (`athena.jsonl`, `kellys-macbook-pro-local.jsonl`, `kellys-mbp.jsonl`) contain 148 keyed records, **all** with `key.calendar_id == "primary"`, written almost exclusively by Bryan's Mac.
- Sample daily notes in `~/bob`:
  - [`2026/20261106.md`](file:///home/bryan/bob/2026/20261106.md#L27): `- **all day** Wedding Anniversary  [📅](https://www.google.com/calendar/event?eid=...)` — clean all-day context bullet (from `primary`, no calendar label).
  - [`2026/20261114.md`](file:///home/bryan/bob/2026/20261114.md#L21-L26): synced `Sun 2026-11-15 06:02`, contains two timed Event Tasks (`Swings!`, `Some of "Brave" w/ Abby`) and no `Ava's Birthday`.
  - Existing birthday/family structures in the vault: [`love.md`](file:///home/bryan/bob/love.md#L22) (`offclock: true`, `offclock_types: [MEET]`), [`family.md`](file:///home/bryan/bob/family.md#L1-L7) (`"Extended family beyond Kelly and Abby: keeping in touch, visits, birthdays, and gifts."`), [`tick_month_05.md`](file:///home/bryan/bob/tick_month_05.md#L17) (legacy zorg task for Kelly's birthday cake), and [`recur.md`](file:///home/bryan/bob/recur.md#L1-L16) (`[repeat:: every ...]` area tasks).

### 2.4 Existing Multi-Calendar Capability Matrix in `bob-cli`

| Capability | Current Status | Observed Implementation / Gap |
| --- | --- | --- |
| Multi-calendar config | Partial | [`GcalCalendarSettings`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/config/gcal.rs#L22-L27) has `{ id, root? }` only; no `label`, `color`, `mode`, or `ack`. |
| Multi-calendar fetch & key | Built | [`FetchContext::fetch_days`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/snapshot.rs#L92-L116) loops configured calendars; [`OccurrenceKey`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/model.rs) keys journal records cleanly — **except** config does not deduplicate `"primary"` vs real primary email ID if both are listed. |
| `eventType: "birthday"` | **Broken** | [`classify`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/classify.rs#L134-L136) and [`note::is_eligible`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/note.rs#L552-L555) reject all `event_type` values except `"default" \| "fromGmail"`. |
| Calendar provenance in Markdown | Missing | [`render_task_row`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/render.rs#L51-L71) and [`render_context_row`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/render.rs#L152-L164) emit identical `[📅](url)` badges for every calendar. |
| Secondary calendar tie-breaking | Unintuitive | [`compare_events`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/snapshot.rs#L379-L393) tie-breaks same-day all-day/same-start rows by raw lexicographical `calendar_id` (`c_...` sorts before `"primary"`). |
| Secondary calendar ownership (`ack`) | Fragile | [`is_external`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/model.rs#L166-L168) checks `!self.organizer_is_self`, which on secondary owned calendars often triggers `#unacked` because Google sets `organizer.email` to `@group.calendar.google.com`. |
| CLI & JSON provenance | Incomplete | `bob gcal list` JSON has `calendar_id` only on events; `list` table has no `CAL` column; [`ReportRow`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/sync.rs#L145-L171) omits calendar fields entirely; [`doctor`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/doctor.rs#L214-L224) prints raw opaque hash IDs; `-C/--calendar` only matches raw IDs. `gcal note` already exposes `calendar_name`. |
| Mac Capture & Obsidian UI | Partial | `GcalNoteModels.swift` decodes `calendarName`; [`AgendaAllDayContext`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/capture_pomodoros_agenda.rs#L179-L198) and `AgendaEventRow` have no `calendar` field; Obsidian CSS/JS only highlights plain `[📅]`, `📍`, `📹`. |

---

## 3. Plan Critique & Alternatives Analysis

### 3.1 Is Syncing Multiple Calendars — Starting With `Birthdays` — a Good Idea?

**Yes for multi-calendar infrastructure and ambient birthday awareness, with important caveats on *how* birthdays and non-primary calendars behave inside Bob.**

What works well in Bryan's plan:
- **Single source of truth for dates:** Keeping extended-family birthdays in Google Calendar avoids maintaining duplicate dates in Markdown (`tick_month_*.md`, `family.md`).
- **Clean fit with `- **all day**` context bullets:** Syncing birthdays as context rows (rather than `#task` items) gives day-of visibility right above timed meetings in `## Events` and in Mac Capture's `all_day` strip (`CaptureAgendaView.quietLineView`) with **zero WIP/Next/Pending/ROTTEN inflation** and zero fake `MEET` Pomodoros.
- **Unlocks the rest of Bryan's sidebar safely:** Once provenance and per-calendar modes exist, `Health`, `Surf`, `Recurring Events`, or `Bloomberg` can each be opted in intentionally.

Where the naive version of the plan breaks down:

1. **Zero lead time for preparation:** `bob gcal sync` normally runs via `bob-ledger-tools` when today's daily note is created (morning of the birthday). Remembering *on November 14* that it is Ava's birthday works for a text/call, **too late** if you needed to buy a card, ship a gift, or order an ice cream cake (see [`tick_month_05.md`](file:///home/bryan/bob/tick_month_05.md#L17)).
2. **Context rows are non-actionable:** `- **all day** Ava's Birthday` has no checkbox (`[ ]`) and never rolls forward. If sync didn't run on a given day (e.g., traveling without opening the Mac, or working on `athena`), a birthday is silently missed.
3. **Treating all 9 sidebar calendars symmetrically would hurt the vault:**
   - Syncing Google's **`Tasks`** calendar or **`Time Blocks`** calendar would fight Bob's `#task` system and `## Pomodoros` (`MEET` auto-filing).
   - Syncing Google's teal **`Birthdays` (Contacts)** calendar alongside Bryan's olive **`Birthdays`** calendar would create duplicate entries (`Ava's Birthday` twice) or noisy entries for casual contacts.
   - Syncing an informational calendar (`Birthdays`, `Bloomberg` holidays/shared schedule) without a `context`-only guard means any timed event accidentally added there spawns a `#task`, an `#unacked` warning, and an open `MEET` Pomodoro slot.

### 3.2 Alternative Approaches Compared

| Approach | How It Works | Strengths | Weaknesses | Verdict |
| --- | --- | --- | --- | --- |
| **A. Pure GCal All-Day Sync** | Sync `Birthdays` calendar into `## Events` `- **all day**` bullets only | Zero duplicate data entry; clean daily-note & Mac Capture surface; historical archive | Day-of-only (no gift lead time); no completion checkbox | Strong core for day-of awareness |
| **B. Pure Bob Recurring Tasks** | `[repeat:: every year]` tasks in `family.md`, `kelly.md`, `abby.md` | Supports lead-time `[scheduled::]` (e.g. `-7d`), WIP tracking, checkboxes | Manual duplication against GCal; floods task backlog for 30+ extended contacts | Best *only* for VIP/gift birthdays |
| **C. Lookahead Command (`bob gcal list --days 14`)** | Render upcoming non-primary / birthday milestones during review without cluttering daily notes early | Gives multi-day warning without touching daily note template semantics | Doesn't leave a durable daily-note record or show in idle Mac Capture | Useful future companion, not a substitute |
| **D. Hybrid (Recommended)** | Sync curated `Birthdays` calendar -> `## Events` (`mode: context`, `[📅 Birthdays]`), **plus** keep gift/party prep as `[repeat:: every year]` tasks in `family.md` / `kelly.md` / `abby.md` | Combines ambient coverage for *all* calendar birthdays with actionable lead-time tasks for VIPs; keeps `Time Blocks` / `Tasks` / Contacts `Birthdays` out of `gcal.calendars` | Requires choosing once which VIP birthdays merit prep tasks | **Best overall workflow fit** |

---

## 4. Justified Adjustments to Requirements

| # | Original Requirement | Adjusted Requirement | Justification |
| --- | --- | --- | --- |
| 1 | *"clear which **event task** came from which Google Calendar"* + *"`Ava's birthday` as an **all-day bullet**"* | Provenance MUST appear clearly on **both Event Tasks (`#task`) and context rows (`- **all day**`, `*free*`, `*maybe*`)**, plus `bob gcal list`, `sync`, and `capture-pomodoros`. | In Bob's format ([`vault-format.md`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/docs/reference/vault-format.md#L594-L595)), all-day bullets are context rows, not Event Tasks. Labeling only `#task` lines leaves `Ava's Birthday` unlabeled; labeling only context rows leaves timed secondary calendars (`Health`, `Surf`) ambiguous. |
| 2 | Explicit calendar clarity on every event | **Implicit Primary, Explicit Secondary (with opt-in `primary` label):** Non-primary calendars *always* show `[📅 <label>](url)` on daily-note rows; `primary` defaults to compact `[📅](url)` unless `label:` is set in config, while JSON/CLI/`list`/tooltips always report all calendars explicitly. | Putting `[📅 Bryan Bugyi]` on 5–10 primary rows per day adds 14+ chars of repetitive noise to already dense task lines and invalidates untouched primary row hashes unnecessarily. Leaving `primary` unmarked and marking every secondary calendar makes non-primary events pop visually (just like Gmail/GCal badges), while allowing 1-line opt-in (`label: Personal`). |
| 3 | Sync `"Birthdays"` calendar via `bob gcal sync` | **Unstated prerequisite:** Update [`classify.rs`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/classify.rs#L134) (and docs) to include `eventType == "birthday"` as `Inclusion::Context`. | `Ava's Birthday` carries Google's birthday cake header (`eventType: "birthday"`). Current code drops everything outside `"default" \| "fromGmail"`. Birthdays should *always* become context bullets, never Event Tasks or `#unacked`. |
| 4 | Identify calendar by name `"Birthdays"` | Key config by stable Google Calendar **`id`**, add optional `label:` / `mode:` / `color:` / `ack:`, and auto-disambiguate duplicate names in UI/CLI/doctor. | Bryan's own sidebar has **two** calendars literally named `Birthdays`. Matching or labeling solely by Google `summary` is ambiguous. |
| 5 | Same sync behavior across multiple calendars | Support per-calendar **`mode: all \| context`** and smart owned-secondary `ack` handling (`ack: inherit \| external \| off`). | Secondary awareness calendars (`Birthdays`, `Bloomberg`) should never spawn accidental `#task` / `MEET` Pomodoros; owned secondary calendars (`accessRole == "owner"`) shouldn't falsely trigger `#unacked` solely because Google sets `organizer.email` to `@group.calendar.google.com`. |
| 6 | *"run `bob gcal sync -D yesterday` ... (`Ava's Birthday` added)"* | Keep offline fake-`gog` integration tests as the CI/repo proof, then verify live **on the `writer` Mac** using explicit `-D 2026-11-14` once the olive `Birthdays` ID is added to `~/.config/bob/config.yml`. | (a) This swarm run is research-only; (b) `athena` (Linux) has `no_client` (`bob-gcal` grant lives on Mac) and `calendars:` is still commented out in `config.yml`; (c) `-D yesterday` shifts daily, so any implementation test run after Nov 15 needs `-D 2026-11-14`. |

---

## 5. Recommended Design

### 5.1 Configuration & Onboarding UX

Extend [`GcalCalendarSettings`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/config/gcal.rs#L22-L27) backward-compatibly (string items and `{id, root}` maps keep working untouched):

```yaml
gcal:
  root: meet_inbox
  calendars:
    - id: primary
      # label: Personal   # optional; omit to keep compact `[📅](url)` on primary
    - id: <olive-birthdays-calendar-id>@group.calendar.google.com
      label: Birthdays    # short display label (rendered in `[📅 Birthdays](url)`)
      mode: context       # `all` (default) | `context` (never mint Event Tasks / MEETs)
      color: green        # optional Bob hue: blue|orange|aqua|yellow|magenta|green|violet|red
      # ack: off          # optional: `inherit` (default) | `external` | `off`
    # - id: <health-calendar-id>@group.calendar.google.com
    #   label: Health
    #   root: body
    #   color: red
    #   ack: off
```

Key config & onboarding rules:
- **Duplicate-primary prevention:** In `FetchContext` / `GcalConfig`, resolve `"primary"` against the fetched `GogCalendar::primary` entry's real ID and reject/collapse duplicate configured calendars resolving to the same Google calendar ID (preventing double-synced rows if someone configures both `primary` and `bryanbugyi34@gmail.com`).
- **Deterministic label resolution:**
  - If `calendars.len() == 1` and `primary` has no explicit `label:`: emit `None` for Markdown badge label (`[📅](url)`), while CLI/JSON still know `calendar_name` (`Bryan Bugyi`).
  - If `calendars.len() > 1`:
    - Primary calendar: `label` is `configured.label.as_deref()` (i.e., compact `[📅](url)` unless Bryan explicitly opts into `label: Personal` or similar).
    - Non-primary calendar: `label` is `configured.label` -> `gog_calendar.name()` -> trimmed ID fallback.
  - **Duplicate resolved label guard:** If two synced calendars resolve to the exact same display label (e.g., syncing both `Birthdays` calendars without setting `label:`), disambiguate deterministically: tag `addressbook#contacts@group.v.calendar.google.com` as `Birthdays (Contacts)` or append a short numeric/hash suffix (`Birthdays (2)`), and emit a yellow warning in `bob gcal doctor` and `calendars`.
- **Upgraded `bob gcal calendars` (Setup Delight):**
  - Show a colored `●` dot next to each calendar's name (mapped to ANSI/Bob 8-hue palette), surface a subtle `[contacts]` / `[primary]` / `[duplicate name]` tag when names collide, display `LABEL` and `MODE` columns alongside `SYNC` and `ROOT`, and add `-y` / `--yaml` to print ready-to-paste `gcal.calendars` YAML snippets (respecting [`cli_rules.md`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/AGENTS.md) short aliases).
  - Update [`doctor.rs`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/doctor.rs#L214-L224) so the `calendars` check reports friendly names (`Bryan Bugyi (primary), Birthdays`) rather than raw `@group.calendar.google.com` hashes.
  - Extend `-C/--calendar` across `note` / `ack` (and optional `--calendar` filter on `list`!) to accept configured `label`, unique Google `summary`, or exact `id`, erroring cleanly with candidates when ambiguous (such as `"Birthdays"` matching two IDs).

### 5.2 Markdown Representation in `## Events` (Decision Matrix)

How should calendar provenance appear in the daily note itself?

| Option | Example Rendered Rows | Compatibility & Aesthetics Assessment |
| --- | --- | --- |
| **1. Label Inside `📅` Link (`[📅 Label](url)`)** *(Recommended)* | `- **all day** Ava's Birthday [📅 Birthdays](https://...)`<br>`- [*] #task **1800-1900** Dentist [📅 Health](https://...) [root:: body] ^dentist`<br>`- [*] #task **0900-0915** Swings! [📅](https://...) [root:: abby] ^swings` | **Minimal noise:** reuses the badge every row already has. One clickable, Hue-tinted pill in Obsidian; title-free Markdown link (`Ctrl+L` Jump-to-link keeps working); [`clean_event_title`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/event_task.rs#L1063-L1087) already strips it; stays cleanly inside Google-owned `spans.badges`! |
| **2. Dataview Field (`[cal:: Birthdays]`)** | `- **all day** Ava's Birthday [cal:: Birthdays] [📅](...)`<br>`- [*] #task **1800-1900** Dentist [📅](...) [cal:: Health] [root:: body] ^dentist` | Verbose raw text (`16+` extra chars); pollutes Dataview task/note fields with `cal` metadata; placing unknown inline fields in trailing position risks Obsidian Tasks right-to-left parser truncation (noted in [`config.yml`](file:///home/bryan/.config/bob/config.yml#L17-L22)). |
| **3. Italic Qualifier (`· *Birthdays*`)** | `- **all day** Ava's Birthday · *Birthdays* [📅](...)`<br>`- [*] #task **1800-1900** Dentist · *Health* [📅](...) ^dentist` | Breaks Event Tasks: [`split_qualifier`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/lifecycle.rs#L336-L353) ignores `task == true` rows, [`event_qualifier`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/capture_pomodoros_agenda.rs#L1059-L1063) takes only the first `· *...*`, and mixes provenance with availability (`*free*`, `*maybe*`, `*day N of M*`). |
| **4. Subheadings (`### Birthdays`)** | `## Events` -> `### Bryan Bugyi` / `### Birthdays` | Destroys chronological daily ordering (`insert_slot` sorts flatly by `(all_day, start_min)`); breaks section parsers across `bob-cli` and `bob-ledger-tools`. |
| **5. Title Prefix (`[Birthdays] Ava's Birthday`)** | `- **all day** [Birthdays] Ava's Birthday [📅](...)` | Corrupts title text, `span_hash("title")`, minted `^block-id` slugs, and Mac Capture/list title matching. |

**Why `[📅 Label](url)` is the cleanest design:**
- **Visual economy:** Instead of inventing a second indicator next to `[📅](url)`, it turns the generic `[📅]` icon into a semantic pill (`[📅 Birthdays]`, `[📅 Health]`) when non-primary, while `primary` keeps compact `[📅]` by default.
- **Google-owned lifecycle integrity:** Inside [`split_row_spans`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/lifecycle.rs#L207-L215), updating `middle.find(" [📅](")` to find `" [📅"` up to `"]("` keeps the entire `[📅 Label](url)` inside `spans.badges`. Consequently, renaming a calendar's `label` in config automatically updates existing untouched rows via [`apply_span_updates`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/plan.rs#L1198-L1329) without clobbering user edits!
- **Sanitization & Dataview safety guard:** Escape/strip `[`, `]`, `*`, `#`, `::`, `^`, newlines, and collapse spaces inside the rendered label; and if a label starts with `YYYY-MM-DD`, insert `\u{200b}` after `📅` (matching [`escape_title`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/render.rs#L483)) so [`dataview/tasks/task.rs`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/dataview/tasks/task.rs#L47) never mistakes `📅 2026-...` for an Obsidian Tasks due date.

### 5.3 Classification, Sorting, Ownership & `eventType: "birthday"` Rules

1. **Allow `eventType: "birthday"` in [`classify.rs`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/classify.rs#L134-L158):**
   - Permit `"birthday"` alongside `"default" | "fromGmail"`.
   - Always classify `"birthday"` events as `Inclusion::Context` (when their `[start, end)` covers `window.day`), never as `Inclusion::Task`, and leave `qualifier: None` (avoiding redundant `"Ava's Birthday · *birthday*"` noise).
   - Keep `note::is_eligible` unchanged (or document explicitly that birthdays are non-task context items, so private task notes and `ack` remain scoped to timed Event Tasks).
2. **Per-calendar `mode: context`:**
   - Any event from a `mode: context` calendar classifies as `Inclusion::Context` (`"free"` / `"maybe"` / `"multi-day"` or `None` qualifier as appropriate for timed context rows `- **1400-1500** ... [📅 Health](url)`), never minting Event Tasks, `#unacked`, or `MEET` Pomodoros.
3. **Fix secondary owned-calendar `ack` check:**
   - When `ack == GcalCalendarAck::Off`, treat `is_external()` as `false` for that calendar.
   - When `ack == Inherit` (default), don't treat an event as external solely because `organizer.email == calendar_id` on an `"owner"` secondary calendar with no third-party attendees (`organizer_or_no_guests` / empty attendee list). Genuine third-party invites (`fromGmail` or external organizers) still trigger `bob gcal ack` (`#unacked`).
4. **Config-order tie-breaking in [`compare_events`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/snapshot.rs#L379-L393):**
   - Change tie-breaking from raw `left.event.key.calendar_id.cmp(&right.event.key.calendar_id)` to:
     `calendar_config_index` (so `primary` comes before `Birthdays` if listed first!) -> `title` (case-insensitive) -> `calendar_id` -> `event_id`.
   - In [`insert_slot`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/plan.rs#L2568-L2595), preserving snapshot order on fresh inserts means `2026/20261114.md` cleanly places `- **all day** Ava's Birthday [📅 Birthdays](...)` above timed Event Tasks without hopping around based on opaque `@group.calendar.google.com` hashes.

### 5.4 Aesthetics Across Obsidian, Pomodoro Links, Mac Capture & Terminal

**"Beautiful"** in Bob means matching the cohesive 8-hue visual language already built into `bob-ledger-tools`, `pomodoro_homes`, and `bob-mac-capture`:

1. **Google Color -> Bob 8-Hue Mapping:**
   - Map Google's calendar `colorId` / `backgroundColor` automatically to Bob's 8 harmonious hues (`blue`, `orange`, `aqua`, `yellow`, `magenta`, `green`, `violet`, `red` — e.g., Bryan's olive-green `Birthdays` -> `green`, maroon `Health` -> `red`, gold `Recurring Events` -> `yellow`, orange `Surf` -> `orange`, blue `Bryan Bugyi` -> `blue`), overridable via `color:` in `config.yml`.
2. **Obsidian Live Preview & Reading View ([`291-plugin-gcal-events.js`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/sase/repos/linked/bob-plugins/plugins/bob-ledger-tools/src/291-plugin-gcal-events.js#L262-L266) & [`styles.css`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/sase/repos/linked/bob-plugins/plugins/bob-ledger-tools/styles.css#L5921-L5944)):**
   - Extend Live Preview badge regex/scanner to detect `[📅 <label>](url)` in full (Reading View's `/[📅📹📍]/.test(link.textContent)` already adds `.bob-calendar-event-badge` to `<a>`!).
   - Style labeled calendar badges (`a.bob-calendar-event-badge[data-calendar-label]`) as subtle, crisp rounded micro-pills tinted via `--bob-hue-<hue>` (`12%` background mix, `28%` border mix, subtle ink), keeping `📅` + `Birthdays` unified in one clickable pill (`title="Birthdays · Open in Google Calendar"`), while unlabeled primary `[📅]` stays minimal as today.
   - **Important distinction:** Do *not* override the **time pill** hue (which belongs to `MEET` / running Pomodoro phase + `root` / off-clock dashed outline); keep calendar color on the **source pill** so time, work home, and calendar provenance never fight each other!
   - **Pomodoro Task Link tooltips ([`291d-event-link-times.js`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/sase/repos/linked/bob-plugins/plugins/bob-ledger-tools/src/291d-event-link-times.js#L165-L178)):** Read the extracted `calendarLabel` from the linked `## Events` row and append `· Health` in `eventLinkTimeTooltip`, letting Bryan see which calendar an Event Task came from even while looking inside `## Pomodoros`!
3. **Bob Mac Capture Agenda ([`capture_pomodoros_agenda.rs`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/capture_pomodoros_agenda.rs#L867-L958), [`CaptureAgendaModels.swift`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/sase/repos/linked/bob-mac-capture/Sources/CaptureCore/CaptureAgendaModels.swift#L815-L963), [`CaptureAgendaView.swift`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/sase/repos/linked/bob-mac-capture/Sources/BobMacCapture/CaptureAgendaView.swift#L1294-L1370)):**
   - **Parser fix required first:** Update [`markdown_link_target`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/capture_pomodoros_agenda.rs#L1077-L1083) from `format!("[{icon}](")` to prefix-match `[<icon>` (plus optional space+label before `](`), and add a helper `calendar_badge_label(line)` so `calendar_url` doesn't break when `[📅 Birthdays](url)` is present! Similarly update [`CaptureAgendaInlineText.iconLinkEnd`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/sase/repos/linked/bob-mac-capture/Sources/CaptureCore/CaptureAgendaInlineText.swift#L338-L346) if labeled links ever appear in non-event agenda inline text.
   - **Additive JSON `calendar` object** on both `AgendaAllDayContext` and `AgendaEventRow` (when a calendar label is present on the row, plus optional `hue` resolved from config/label): `{ "label": "Birthdays", "hue": "green" }`.
   - **Mac Capture SwiftUI rendering:**
     - Timed rows (`calendarRowView`): render a small secondary capsule badge (`Health`) right next to title / off-clock chips when `data.calendar?.label` is non-empty.
     - All-day strip ([`makeCalendarAllDayRow`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/sase/repos/linked/bob-mac-capture/Sources/CaptureCore/CaptureAgendaPresentation.swift#L2119-L2136)): format labeled items cleanly (`Birthdays: Ava's Birthday`, or tinted mini-dot + label), while `bob capture-pomodoros` CLI prints dim `(Birthdays)`.
4. **CLI (`list`, `sync`) & JSON Contracts (Additive, `schema_version: 1` Safe):**
   - **`bob gcal list`:** Add `calendar_name`, `calendar_label`, `calendar_primary`, `event_type` to `events[]` JSON and `label`, `color`, `hue`, `primary`, `mode` to `calendars[]` JSON; add a `CAL` column to the human table **only when `calendars.len() > 1`** (using subtle color-coded labels, dimming `Primary` so secondary calendars stand out).
   - **`bob gcal sync`:** Add `calendar_id`, `calendar_name`, `calendar_label`, `calendar_primary` to [`ReportRow`](file:///home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_18/src/native/gcal/sync.rs#L145-L171) / `report_json` and `SkippedEvent::json`; in human output append colored calendar tag on non-primary rows (e.g., `+ context  all day  Ava's Birthday  Birthdays`).

---

## 6. Cross-Repo Impact & Verification Plan

### 6.1 Files & Consumers Requiring Coordinated Updates

| Repo | Component / File | Change Summary |
| --- | --- | --- |
| `bob-cli` | `src/native/config/gcal.rs`, `src/native/gcal/config.rs` | Extend `GcalCalendarSettings` (`label`, `mode`, `color`, `ack`); resolve hues & duplicate-ID deduplication |
| `bob-cli` | `src/native/gcal/classify.rs`, `src/native/gcal/model.rs`, `src/native/gcal/snapshot.rs` | Allow `eventType: "birthday"` as Context; apply `mode: context`; owned-secondary `ack` guard; config-order tie-breaking; expose `calendar_label` / `calendar_hue` |
| `bob-cli` | `src/native/gcal/render.rs`, `src/native/gcal/lifecycle.rs`, `src/native/gcal/plan.rs` | Render `[📅 <label>](<url>)` when labeled; generalize `split_row_spans` for `" [📅..."`; thread label through `PlannedOccurrence` & `apply_span_updates` |
| `bob-cli` | `src/native/gcal/{calendars,list,sync,skip,doctor,note,ack}.rs` | JSON/CLI calendar fields; `--yaml` & duplicate warnings in `calendars`; `CAL` column in `list`; friendly `doctor` summary; `-C` label matching |
| `bob-cli` | `src/native/capture_pomodoros_agenda.rs`, `src/native/capture_pomodoros.rs` | Fix `markdown_link_target` for `[📅 <label>](url)`; parse & emit additive `calendar` metadata on `AgendaAllDayContext` and `AgendaEventRow` |
| `bob-cli` | `docs/gcal.md`, `docs/reference/vault-format.md` | Document multi-calendar options, `[📅 <label>](url)` badge, `birthday` event inclusion |
| `bob-plugins` | `plugins/bob-ledger-tools/src/291-plugin-gcal-events.js`, `291d-event-link-times.js`, `styles.css` | Capture `[📅 <label>]` link span in Live Preview; paint subtle calendar source pills; show `· <label>` in Pomodoro link tooltip |
| `bob-mac-capture` | `CaptureAgendaModels.swift`, `CaptureAgendaPresentation.swift`, `CaptureAgendaView.swift`, `CaptureAgendaInlineText.swift` | Decode optional `calendar` on `CaptureAgendaAllDayContext` & `CaptureAgendaEventRow`; render compact calendar tag on timed/all-day rows; generalize `iconLinkEnd` if needed |

### 6.2 Concrete Expected Result for `Ava's Birthday` (`2026-11-14`)

Once implemented, configured with Bryan's olive `Birthdays` calendar ID in `~/.config/bob/config.yml` (via chezmoi), and executed on his `writer` Mac with `bob gcal sync -D 2026-11-14`:

```text
bob gcal sync · 2026/20261114.md
  + context  all day  Ava's Birthday  Birthdays
✓ Events updated (+1 context) · Pomodoros unchanged · 2 in sync
```

And [`2026/20261114.md`](file:///home/bryan/bob/2026/20261114.md#L21-L26) cleanly gains an all-day bullet sorted above the day's Event Tasks:

```markdown
## Events

*↻ synced Sun 2026-11-15 11:15 · [bryanbugyi34@gmail.com](https://calendar.google.com/calendar/r/day/2026/11/14?authuser=bryanbugyi34%40gmail.com)*
- **all day** Ava's Birthday [📅 Birthdays](https://www.google.com/calendar/event?eid=...)
- [x] #task **0900-0915** Swings! [📅](...) [root:: abby] [type:: MEET] [fresh:: 2026-11-14]  [completion:: 2026-11-14] ^swings
- [x] #task **1900-2000** Some of "Brave" w/ Abby [📅](...) [root:: abby] [type:: MEET]  [completion:: 2026-11-14] ^grocery-store-w
```

### 6.3 Recommended Delivery Phases

1. **Phase 1 (`bob-cli` Core Multi-Calendar & `Birthdays`):** `classify.rs` (`"birthday"`), `config.rs` (`label`, `mode`, `color`, `ack`, duplicate-ID dedup), `render.rs` + `lifecycle.rs` (`[📅 Label](url)` + hash preservation), `snapshot.rs` sorting, `capture_pomodoros_agenda.rs` (`markdown_link_target` fix + `calendar` payload), CLI/JSON improvements (`calendars`, `list`, `sync`, `doctor`), and fake-`gog` tests in `tests/gcal_sync.rs`.
2. **Phase 2 (`bob-plugins` Visual Polish):** Obsidian pill styling for `[📅 Label](url)` + `291d-event-link-times.js` hover tooltip + `bob plugins sync`.
3. **Phase 3 (`bob-mac-capture` + Live Mac Rollout):** Mac Capture `CaptureAgenda` badges, chezmoi `~/.config/bob/config.yml` update using `bob gcal calendars --yaml`, and live Mac verification with `bob gcal sync -D 2026-11-14` plus `scripts/dev/macos-ci-check`.
