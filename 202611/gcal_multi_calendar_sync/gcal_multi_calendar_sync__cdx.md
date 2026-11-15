# Multi-calendar birthday sync: verified findings and recommended design

Researcher: **cdx** · 2026-11-15 · Independent research

## Decision in brief

**This is a good idea, and the core multi-calendar implementation already exists.** The immediate problem is configuration plus missing visible provenance, not an absent calendar-fetching engine. Ava's Birthday is an ordinary recurring all-day event in a real secondary calendar that Bob currently does not sync. Enable that calendar by its verified ID, keep birthdays as context bullets, and add a readable calendar source to every generated row.

Do not turn birthdays into tasks, rebuild synchronization, or automatically import every calendar shown in Google's sidebar. Google-native birthday events are a separate issue: Bob currently excludes them, but **that exclusion is not why Ava is missing**.

This report is research, not an implementation completion claim. No application code, Google events, production configuration, or vault content was changed. No updated binary was built and no live `bob gcal sync` was run. The requested post-implementation acceptance run is specified below.

## What I verified

### The screenshot is ambiguous; the live data is not

I inspected the supplied `20261115_105604.png`. It shows two sidebar entries named **Birthdays**, with different greens. Ava's popup says Saturday, November 14, recurring annually, and identifies Birthdays as the calendar. Neither the name nor the artwork uniquely identifies the API calendar or event type.

The connected Calendar app could search events but could not list calendars: listing returned `ACCESS_TOKEN_SCOPE_INSUFFICIENT`. The Linux host's `bob gcal calendars -f json` also could not connect because its isolated `bob-gcal` OAuth client was absent. I then used the existing Mac connection over the documented SSH alias, without changing credentials.

`ssh mac 'bob gcal calendars -f json'` confirmed:

| Property | Observed value |
| --- | --- |
| Account | `bryanbugyi34@gmail.com` |
| Calendar | `Birthdays` |
| Calendar ID | `kjs04hafl3btrilujllivid3s8@group.calendar.google.com` |
| Role | `owner` |
| Calendar background color | `#7bd148` |
| Primary | `false` |
| Selected by Bob | **`false`** |
| Primary calendar selected by Bob | **`true`** |

The connected Calendar search against that ID found Ava. A second read through the Mac's actual gog adapter confirmed the raw date-only fields:

```json
{
  "id": "0roo9pdfmor2uhp72o0h5u8k31_20261114",
  "summary": "Ava's Birthday",
  "eventType": "default",
  "status": "confirmed",
  "recurringEventId": "0roo9pdfmor2uhp72o0h5u8k31",
  "originalStartTime": {"date": "2026-11-14"},
  "start": {"date": "2026-11-14"},
  "end": {"date": "2026-11-15"}
}
```

The adapter returned one event and an empty `nextPageToken` for November 14 in America/New_York. The connected app also reported `transparency: transparent`. This is enough to identify the requested source and occurrence without guessing either from its display name.

Mac diagnostics confirmed working read-only Calendar authorization and gog v0.47.1 at `/Users/bbugyi/bin/gog`. They reported host `kellys-macbook-pro-local` and **no writer pin**. The project policy nevertheless requires the Mac to be the writer; do not treat the absent pin as permission to write from this Linux researcher host. An unrelated orphaned private-note warning was observed and left alone.

### Repository evidence

I inspected bob-cli at `9c2c240480998e1b9ecd82a5c70aefbe963b8c58`. These are observed implementation facts, not proposed functionality:

| Area | Existing behavior and implication |
| --- | --- |
| [Configuration parser](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/config/gcal.rs#L443) | `gcal.calendars` already accepts several string IDs or `{id, root}` entries. Missing configuration defaults to `primary`; an empty list is rejected. |
| [Snapshot fetching](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/gcal/snapshot.rs#L92) | Fetches each configured calendar separately for the requested date interval, using one account, then merges and classifies the results. |
| [Transport](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/gcal/gog.rs#L85) | Requests all event pages, carries `eventType`, preserves occurrence IDs, and rejects a leftover page token. No new OAuth account is necessary. |
| [Classification](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/gcal/classify.rs#L129) | Accepts `default` and `fromGmail`; all-day date ranges become context rows. Native `birthday` events are omitted before all-day classification. |
| [Rendering](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/gcal/render.rs#L152) | Already renders `- **all day** … [📅](…)`, with no task checkbox. Timed tasks and context bullets both lack a visible source name. |
| [Source metadata](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/gcal/snapshot.rs#L182) | Resolves `calendar_name`, but does not carry it through the whole write/render path. `GogCalendar::name()` uses `summary`, ignoring Google's personal `summaryOverride`. |
| [Journal identity](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/gcal/journal.rs#L618) | Combines calendar ID and occurrence event ID; state additionally distinguishes the note day. This is already substantially the right identity model. |
| [Human list](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/gcal/list.rs#L740) | Lists calendar names in its header, but has no source per row. List JSON has `calendar_id`; the similarly named `source` fields elsewhere mean root-selection provenance, not calendar identity. |
| [Absent-event handling](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/gcal/sync.rs#L1191) | Looks up journaled rows absent from the new snapshot, including rows belonging to calendars no longer selected. This needs an explicit deselection policy. |

Existing integration tests cover all-day ordering and bullets, repeated sync, lifecycle ownership, incomplete snapshots, and various past-day behaviors. I read these tests; I did not execute the Rust test suite for this research-only change. The shared fake gog currently serves one event-list fixture regardless of calendar, and its single-event fixture lookup is event-ID based. Meaningful multi-calendar tests need calendar-specific fixtures, not simply repeated reads of the existing fixture.

## Google's model and the important distinction

Google provides calendar IDs through CalendarList and lists events one calendar at a time. Display names are metadata; `summaryOverride` is a user's personal calendar name, and `selected` controls Google UI visibility. Neither is a sound identity or an implicit instruction to import into Bob. Keep Bob's selection explicit. [CalendarList resource](https://developers.google.com/workspace/calendar/api/v3/reference/calendarList), [CalendarList list](https://developers.google.com/workspace/calendar/api/v3/reference/calendarList/list).

Ava's end date is exclusive, so the occurrence covers November 14 only. Keep date-only values as dates; never convert this birthday to a midnight meeting. Google event IDs are unique within a calendar, while recurring occurrences have different event IDs but share an `iCalUID`. Therefore neither title matching nor global `iCalUID` deduplication should replace Bob's calendar-plus-occurrence identity. [Events resource](https://developers.google.com/workspace/calendar/api/v3/reference/events).

Google also has an actual `eventType: birthday`: special annually recurring all-day events. It supports reading these through ordinary event methods and returns them when no event-type filter is supplied. They may represent contact-related significant dates, not just manually entered birthdays. This is a separate mechanism from an ordinary secondary calendar named Birthdays. The screenshot alone could not distinguish them; the live response did. [Event types](https://developers.google.com/workspace/calendar/api/guides/event-types).

The event-list API supports recurrence expansion and pagination. Empty or short pages can still have a continuation token. Retain gog's expanded-occurrence behavior and Bob's all-pages completeness check; verify both in integration coverage instead of implementing a birthday recurrence engine. Do not infer deletions from an incomplete response. [Events list](https://developers.google.com/workspace/calendar/api/v3/reference/events/list).

**Scope recommendation:** enable the verified secondary calendar now. Do not silently widen primary-calendar inclusion to all native birthdays as part of that configuration change. If native birthdays are wanted too, make that an explicit inclusion decision, add fixtures, and still render them as context. No People API access, calendar writes, Contacts ingestion, or hard-coded legacy virtual-calendar ID is needed for Ava.

## Product design

### Configure a source once

This configuration is supported today and should already make Ava eligible for the existing all-day renderer:

```yaml
gcal:
  account: bryanbugyi34@gmail.com
  calendars:
    - id: primary
    - id: kjs04hafl3btrilujllivid3s8@group.calendar.google.com
```

Preserve other existing `gcal` settings. Apply any real configuration change through its managed source, opening the chezmoi repo with `sase repo open` first; do not replace the whole configuration or patch a generated copy.

For the feature, add one optional presentation property, **`label`**, while keeping existing strings and maps valid:

```yaml
gcal:
  account: bryanbugyi34@gmail.com
  calendars:
    - id: primary
      label: Personal
    - id: kjs04hafl3btrilujllivid3s8@group.calendar.google.com
      label: Birthdays
```

`label` is a proposed addition, not currently implemented. It must never select a calendar or affect roots, recurrence, task type, or time accounting. Resolve display text as explicit label → nonempty `summaryOverride` → nonempty `summary` → ID. Validate explicit labels as nonempty single-line text. Escape every displayed label independently of the event title.

For conflicting explicit labels, fail configuration with the relevant IDs and a clear correction. For duplicate Google-derived names, append a stable short ID fingerprint and explain it in `calendars`; use the same label everywhere. Do not choose the first calendar called Birthdays. Exact IDs stay visible in discovery and JSON even when shortened labels are used in normal display.

Improve the existing `bob gcal calendars` command instead of introducing a second setup command or a mutating wizard. Put the human name/label and sync status before the long ID, retain a copyable full ID, show primary and access role, and keep JSON useful. `doctor` should explain selected-but-inaccessible sources and duplicate selections. No new public CLI option is necessary for this feature.

### The note should read like a useful agenda

Recommended Markdown, with illustrative URLs:

```markdown
## Events

*↻ synced 10:32 · account/day link*
- **all day** Ava's Birthday [📅 Birthdays](https://calendar.example/ava)
- [*] #task **1000-1030** Planning [📅 Personal](https://calendar.example/planning) [root:: job] ^planning
```

Use one **named calendar link** in the existing badge position. It is readable in plain Markdown, takes no extra line, and opens the specific event. Keep it title-free: existing renderer comments document that quoted Markdown link titles break some link-opening consumers.

All-day bullets stay above the chronological timed agenda. Preserve the existing single Events section; per-calendar sections would fragment the day, complicate parser assumptions, and make simultaneous events harder to compare. Do not add a checkbox, `#task`, `#off`, `[type:: MEET]`, or a Pomodoro link to Ava's birthday. A birthday is context; any desired action such as buying a gift is a separately captured task.

Source text must be present even for a single configured calendar. A header listing sources, an emoji, a hover tooltip, or color alone cannot answer which row came from which source. Show `CALENDAR` in human `list` output and the label in sync action rows. Add `calendar_id`, `calendar_label`, and `event_id` where needed in sync JSON; preserve existing keys and the meaning of `source`.

If Google omits `htmlLink`, render a non-clickable source badge with an explicitly supported grammar. Do not manufacture a clickable event URL or drop provenance. For unchanged legacy rows lacking both URL and a stable locator, retain the existing matching safeguards and report uncertainty rather than manufacture duplicate rows.

Calendar color can accent source text in the CLI, but it is optional polish. Never feed it into existing event-color-to-root mappings: these are different concepts. Keep source text legible without color, in both Obsidian themes, and with long or Unicode labels. A screenshot review in Reading and Live Preview is more useful than adding decoration for its own sake.

### Extend visibility through existing consumers

The named-link choice has a real, bounded compatibility cost:

- `gcal/lifecycle.rs:207` recognizes the literal ` [📅](` as the start of the managed badge span. A renderer-only change would misclassify the label as title text, disrupting hashes and reconciliation.
- `capture_pomodoros_agenda.rs:1077` extracts links with an exact icon-only marker. It would lose `calendar_url` for `[📅 Birthdays](…)` unless updated.
- `event_task.rs:1061` removes trailing Markdown links generically, which is a useful existing behavior, but labels with escaped delimiters need tests against its simple link parser.
- All-day capture agenda objects currently contain line, title, and qualifier but no calendar source. Timed agenda objects also lack a display source. Add optional source fields if the “always clear” requirement includes those surfaces; the Mac must render Bob's fields, not independently parse the note.

I audited bob-plugins at `f72bd4e96403a7e6a3f287c8f191ec70fa3e5c4a`. Its [calendar fragment](https://github.com/bobs-org/bob-plugins/blob/f72bd4e96403a7e6a3f287c8f191ec70fa3e5c4a/plugins/bob-ledger-tools/src/291-plugin-gcal-events.js#L263) identifies badge icons and its Reading-mode code accepts link text containing those icons. Named calendar links appear compatible with that detection, but Live Preview decorates the icon range rather than the whole label. Its existing badge CSS also dims and shrinks links. Verify the actual result before calling it beautiful; do not assume a full chip redesign is needed.

Use one shared parser for legacy icon-only links, named source links, and the chosen URL-less representation. Keep legacy syntax readable indefinitely. Test Rust title extraction, capture URL extraction, sync row location, and Obsidian rendering together. If Mac presentation changes are included, inspect its models and renderers and test additive JSON decoding; I did not inspect the Mac source in this research turn.

## Reliability requirements that should accompany the visual change

### Identity and aliases

Keep source identity separate from presentation. Carry a resolved calendar descriptor with configured/request ID, API-resolved ID, stable journal key, display label, and optional color. A calendar rename, label edit, or color change must not create a new event or block ID.

Reject duplicate configured sources, including `primary` and the same primary email ID together. The current fetch loop would request both and use the configured spelling in event keys. Resolve aliases before fetching.

For compatibility, retain `primary` as the normal primary journal key for the existing single-account setup. When an explicit primary email is supplied, recognize it as the same source. Legacy records already using the email spelling require alias-aware lookup/adoption with conflict detection; do not blindly rewrite every journal or start a second identity. Test this separately from the normal configuration, which can keep `id: primary` unchanged.

Keep distinct calendars distinct even when they contain events with the same ID, title, times, or `iCalUID`. In the rare copied/invited-event case, show both sources and let the user decide which calendar to select. Heuristic global deduplication loses provenance and can choose the wrong copy's edits or RSVP state. Multiple accounts are outside this feature; do not imply the current row journal is already namespaced for arbitrary account switching.

### Preserve complete snapshots and selection boundaries

Retain the existing rule: a failed selected calendar, event page, parse, or required lifecycle lookup prevents the day's write. A successful empty result is different from a fetch failure. Keep bounded queries, the existing lock, preimage checks, and crash-recovery journal flow. This feature does not require incremental sync tokens, webhooks, parallel fetches, or a new scheduler.

Explicitly fix the selection boundary in `resolve_absent`: removing a calendar from configuration means **stop managing that source**, not delete its previous rows or keep fetching it indefinitely. Restrict absent-event reconciliation to selected canonical sources, preserve old rows and journals, and report the inactive source when relevant. Re-enabling resumes the same identities and respects tombstones. A retired calendar's 403 or 404 must not erase historical rows or prevent all future syncs.

Check CalendarList completeness too. The adapter uses `--all`, but currently defaults a missing `calendars` member to an empty list and does not explicitly reject leftover pagination. Validate the expected shape and complete result before relying on it for canonical identity or duplicate-label resolution. Do not confuse a hidden calendar, an unselected Google UI entry, and a source inaccessible to the account.

For the requested single-day run, preserve the existing all-or-nothing snapshot guarantee. The multi-day implementation fetches selected remote ranges before writes but processes days individually; do not advertise a new global transaction across all days without implementing and testing it.

### Upgrade without taking over the note

The provenance link belongs to the existing managed badge span. Migrate untouched icon-only badges to named links when the relevant day is synced, updating recorded hashes. Preserve time, checkbox, block ID, child notes, roots, task type, and recorded work.

A user-modified badge or row remains user-owned. Report the authoritative source in diagnostics/JSON even when the visible old badge is held; do not use `--force` to satisfy a cosmetic rule. The honest requirement is “source on every generated/managed row, with explicit diagnostics for protected edits,” not an unconditional promise to overwrite human text.

Use the existing URL or block ID to find legacy rows; never use the new display label as identity. Context rows usually rely on URL matching, and URL-less ones can rely on exact rendered text, so label migrations and rename tests need special care. Conflicting candidates should hold and explain, not guess.

Scope rewrites to days explicitly synced. No vault-wide historical badge migration is needed for the initial feature, and adding a source should not resurrect intentionally deleted rows. A held/replaced Events section remains held until the user explicitly chooses the established reset operation.

## Assessment of alternatives and adjusted requirements

| Approach | Assessment |
| --- | --- |
| Add the Birthdays ID only | Solves Ava's eligibility immediately using existing code, but fails readable per-row provenance. Useful diagnosis, incomplete feature. |
| Select the verified calendar and add named source links | **Recommended:** small, general, readable, and aligned with the existing sync model. |
| Sync every visible Google calendar | Reject: sidebar visibility is not consent to import; Time Blocks and other calendars could duplicate the day or add noise. |
| Separate section per calendar | Reject: fragments time order and widens changes to all Events consumers. |
| Source tags, `[root::]`, or colors alone | Reject: tags add taxonomy noise, roots already mean work attribution, and colors do not uniquely identify sources. |
| Birthday-specific scraper, ICS feed, or Contacts importer | Reject: live data proves the existing authenticated event endpoint already supplies Ava. |
| Automatically include all native birthdays | Defer: a separate inclusion change, potentially importing contacts the user did not request. |

The justified requirement adjustments are:

1. **Reframe the work as completing and configuring existing multi-calendar support**, not building it from scratch.
2. **Identify the source by verified ID**, not by the duplicate sidebar name.
3. **Include source labels on all synced rows**, including context bullets, and propagate source through read-only presentations where required.
4. **Keep all-day events informational.** “Event task” must not accidentally turn a birthday into an obligation or 24-hour time entry.
5. **Preserve human ownership.** Guarantee provenance for generated rows and diagnostics; do not overwrite edited rows simply to force visual uniformity.
6. **Keep native birthday inclusion separate** from Ava's ordinary secondary-calendar event.
7. **Pin validation to the intended date as well as the requested relative command.** “Yesterday” is November 14 only when the run occurs on November 15 in Bob's configured timezone.

## Verification and rollout criteria

The implementation should be considered ready only after meaningful tests cover:

| Test | Required result |
| --- | --- |
| Primary plus verified-secondary-shaped fixture | Both sources appear, one account is used, Ava is one all-day context bullet, and existing timed tasks retain their behavior. |
| Same event ID in two calendars | Separate rows and independent journal/lifecycle state. |
| Duplicate calendar ID or primary/email aliases | Clear configuration error or one canonical source; never duplicate fetch/write. |
| Empty, duplicate, renamed, Unicode, and hostile labels | Stable unambiguous display; no Markdown, task-field, tag, or link injection. |
| Old and new badge forms | Same row location, correct span hashes, intact calendar-open URLs, clean title extraction, no duplicate task or context row. |
| Legacy edited badge and URL-less context | Ownership retained; any ambiguity reported; repeated sync cannot add duplicates. |
| Later event-page failure or failed second calendar | No daily-note or event-journal writes. Test a page after a successful first page, not only first-call failure. |
| Calendar deselected or inaccessible after removal | Prior rows remain; inactive source does not enter cancellation or block active sources. |
| All-day recurrence | Date-only start and exclusive end, next-year distinct occurrence, leap-day fixture, moved/deleted occurrence, and timezone/DST boundaries. No local recurrence reimplementation. |
| Repeated sync and crash adoption | No second row, duplicate Pomodoro link, or repeated migration notice; stable IDs. A timestamp refresh alone is not duplication. |
| Native birthday fixture | Remains explicitly omitted if out of scope; becomes context only if separately enabled. Ordinary default birthdays remain included. |
| Read-only and presentation contracts | Existing JSON fields retain meaning, source fields are additive, and no Google-write call occurs. |

Extend `tests/gcal_support/fake_gog.py` to serve and fail lists by calendar ID and single-event lookups by `(calendar_id, event_id)`. Run targeted gcal, lifecycle, and capture-agenda tests, then the repository's required verification gate. If plugin or Mac changes are made, run their documented checks and deployment/CI workflow too. Ordinary release-train rules still apply; do not manually bump the version or changelog to test this feature.

### Live acceptance on the Mac, after implementation

1. Verify the actual new binary path/build and timezone. Stage the managed configuration with `primary` plus the exact secondary ID above; preserve unrelated settings. Review whether to pin the already designated Mac writer to the diagnosed host label.
2. Run `bob gcal calendars -f json` and `bob gcal list -D 2026-11-14 -a -f json`. Confirm the selected source and exact Ava occurrence ID. Inspect only the relevant results; avoid persisting unrelated calendar details in test fixtures.
3. Use the **updated** binary for `bob gcal sync -D yesterday -d` when its local date is still 2026-11-15. Inspect the complete proposed diff. Existing past-day sync can also settle eligible older meetings; do not assume the only possible change is Ava.
4. Run the requested **`bob gcal sync -D yesterday`** on the Mac when the preview is correct. Do not use `-F`, switch writers, fabricate an earlier clock, or reset the journal to make the test pass.
5. If implementation finishes on a later date, also run the date-pinned `bob gcal sync -D 2026-11-14` for Ava. The relative command then validates its actual yesterday; it no longer validates the pictured occurrence. Record the resolved date honestly.
6. Inspect `2026/20261114.md`: exactly one Ava bullet under Events, visible **Birthdays** source, correct event link, no checkbox, no `#task`, and no birthday-generated MEET/link/minutes. Check the journal's source-plus-occurrence identity and preservation of existing rows and children.
7. Run sync again and inspect both the note and report. Expect no duplicate birthday or repeated migration; permit the normal refreshed sync stamp. Review the note in Obsidian Reading and Live Preview and the relevant CLI/capture surface before declaring visual acceptance.

If the note is missing, its Events section is held, or the selected source cannot be fetched, report that actual state. These are not successful acceptance runs. Do not force the day as an incidental part of testing. Preserve the pre-write content/diff through the normal vault tooling so any unexpected past-day changes can be reviewed and recovered.

## Evidence boundaries

This work used the supplied screenshot, the checkout and tests at the SHA above, audited project decision memories, the linked plugin checkout, official Google API documentation, and narrowly scoped live reads. No other swarm research report, chat, or summary was consulted. The Calendar app could not enumerate calendars, but its event search and the Mac's Bob/gog connection independently agreed on Ava's secondary-calendar event. I did not inspect the user's managed config source, modify deployment, or run the post-implementation acceptance command.

## Recommended solution

**Ship explicit selection of the verified Birthdays calendar plus readable source links on every generated calendar row, using the existing fetch, classification, journal, and ownership machinery.** Add an optional calendar `label`, support legacy and named badges through shared parsing, reject duplicate source aliases, and keep deselected calendars outside absence reconciliation. Preserve Ava as an all-day context bullet and leave native birthday inclusion as a separate choice. Complete the change with cross-calendar regression tests and the date-aware Mac acceptance run using the updated binary. This delivers the desired experience without inventing another calendar system.
