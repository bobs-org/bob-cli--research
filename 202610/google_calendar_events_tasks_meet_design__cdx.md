# Google Calendar → Bob: event tasks without losing the calendar

Independent research by **cdx** · 2026-10-29

## Recommendation at a glance

**Build this, as a one-way, ownership-aware projection of calendar commitments into Bob.** Google Calendar should own the appointment; Bob should own attendance completion, meeting notes, task links, and reporting attribution. Do not turn Bob into another calendar editor or equate elapsed appointment time with work performed.

Keep the requested `## Events` above `## Pomodoros`, use `[root:: meet]` by default, modernize `meet.md`, and create one untimed MEET planning entry for the day's eligible events. The important qualification is that this entry is a planning queue: actual meeting time should be recorded in sessions linked only to the events attended in those sessions.

For the first implementation, I recommend a Rust reconciliation engine with a small, tested **gog transport adapter**, desktop OAuth, bounded full snapshots, and one configured writer host. The installed gog already supplies much of the difficult authentication work. Bob must still own filtering, completeness checks, identity, Markdown mutation, and recovery.

This report is independent. I did not consult the other swarm researchers, their reports, or their transcripts. It is research, not an implementation or a request to change the live vault.

## 1. What the existing system tells us

I inspected bob-cli at `d0603a5d5180ff7e1fdbc5bddbef180c89647ed5`, bob-plugins at `68db3fbefa30e13767f58fcf18c9c0b3fccd4b53`, the installed `gog v0.44.0`, and gog source at its matching commit `cf42bb7c9f67d3369090de95a7b84ee258be9b02`. Repository reads used SASE repository access; reference-memory reads were audited. Google documentation below was checked on 2026-10-29.

Read-only `bob query` established three useful facts:

- `meet.md` exists, has no `type`, and has scalar `parent: work`; `work.md` also has no area/project type. Merely adding root fields that point into the existing structure is insufficient modernization.
- The daily note uses `type: "[[day]]"` and a monthly parent. Daily creation must preserve this structure.
- The morning checklist already includes reviewing today's and tomorrow's calendar and creating event notes. This feature automates existing work rather than inventing a new habit. Calendar review should remain, for conflicts and tomorrow's preparation.

I did not read the full body of `meet.md` or the live daily template. The migration must inspect and preserve those bodies during implementation. The connected Calendar app could not list calendars because its token lacked the required scope. **No live account calendar selection, RSVP edge case, or end-to-end OAuth test was verified.** No credentials or calendar events were changed.

| Existing contract or implementation | Design consequence |
| --- | --- |
| `docs/pomodoro-homes.md`, R11; `src/native/task_root.rs` | Root overrides affect reporting and theme inheritance, not residence, blocking, freshness, Ready caps, or archive behavior. Use the existing parser, setter, and resolver. |
| Area Note glossary; `docs/concepts/today-and-the-pomodoro-ledger.md` | Normal tasks reside in area/project notes. Daily event tasks require an explicit, narrow exception alongside the daily review task. |
| `docs/plan.md`; `docs/task-status-hooks.md` | Today comes from dedicated links under open ledger entries. Create real task links, then reconcile. Do not add a Today tag or invent a parallel membership list. |
| `src/native/freshness/state.rs` | Canonical daily notes are excluded from the ordinary review walk. Missed event tasks will not automatically receive normal backlog review. |
| `docs/pomodoro-homes.md`, R5 | Closed session minutes divide evenly among distinct linked tasks. One timed MEET entry covering unequal meetings misattributes their time. |
| `src/native/collect_done/transform.rs` | Archive scanning has no general exclusion for year directories. Protect event history deliberately; do not assume daily event tasks will stay put. |
| `src/native/vault_rewrite/mod.rs`; `src/native/gkeep/pull.rs` | Bob already has maintenance locking, before-image checks, atomic writes, verification, rollback, and import evidence patterns. Reuse those principles. |
| bob-plugins `bob-navigation-hotkeys/src/010-requires-and-config.js` | Daily creation references `_templates/daily.md`; insertion must work with the existing template and its decorated Pomodoros heading. |

These are compatibility obligations, not reasons to abandon the idea.

## 2. Is making events into tasks a good idea?

Yes, for this workflow. It brings attendance commitments into the same daily view, gives meetings durable notes and block links, and attributes actual time to the appropriate responsibility. Keeping Calendar as the source also reduces manual transcription errors.

The danger is treating an appointment like discretionary backlog. A missed 09:00 appointment is not automatically a task to do tomorrow. An accepted invitation is not evidence that the meeting happened. A canceled meeting should not destroy notes. A meeting's calendar duration is not necessarily its attended duration.

I considered three shapes:

| Shape | Strength | Cost | Verdict |
| --- | --- | --- | --- |
| Read-only calendar agenda, no tasks | Smallest semantic footprint | Cannot satisfy normal Task Links, completion, or root attribution | Good fallback if the task lifecycle becomes too elaborate |
| Canonical tasks in `meet.md` or event notes, daily embeds | Fits ordinary residence rules; stable long-term home | Daily Events becomes a projection, and meeting tasks can accumulate as backlog | Credible alternative, but less direct than the requested daily experience |
| Canonical event occurrence tasks in daily Events | Matches the request; notes stay with the day | Requires provenance-aware lifecycle, archival protection, and cross-day moves | **Recommended**, with the explicit exceptions below |

Do not create one Markdown note per event by default. Most meetings do not deserve a file. A user can link a substantive meeting note beneath the task when needed. Follow-up work should become ordinary tasks in its actual area/project; the event task records attendance, not every outcome of the meeting.

## 3. Requirement adjustments I recommend

1. **Define “RSVPed” as accepted**, with an explicitly documented extension for events Bryan organizes. Declined invitations are excluded; Maybe is optional and visibly tentative. Mere presence on a calendar is insufficient.
2. **Use one untimed MEET planning entry, not one synthetic completed session.** Never populate worked minutes from the calendar automatically. Never mark attendance complete just because the clock passed the event's end.
3. **Keep only active, eligible, open event tasks linked in the live queue.** Completed, canceled, declined, or explicitly released tasks must not be continually re-linked. “All events” applies to initial eligibility and the Events view, not to overriding later user gestures.
4. **Allow managed daily event tasks as a narrow residence exception**, and retain their closed history in their daily notes. Do not change how ordinary area/project tasks are filed.
5. **Do not silently pre-create a horizon of daily files.** Default writes target today's existing daily note. Tomorrow's agenda is available read-only. A missing note is a pending import, not a reason to fabricate an incomplete template.
6. **Allow private local root overrides.** Editing a Google event description is not always possible or appropriate. The local override makes routing usable for invitations received from other people.
7. **Use one writer host initially.** Local file locks cannot prevent concurrent writes to different Git-synced vault clones.
8. **Provide “unresolved past events” review without automatic rollover.** Keep this distinct from normal task freshness and never fabricate a Done or missed-attendance outcome.

These adjustments are necessary for reliable behavior, not optional polish.

## 4. What the user should see

An illustrative daily source, after ordinary lane reconciliation:

```markdown
## Events

- [*] #task **09:30–10:00** Design review [↗](https://calendar.google.com/...) [root:: meet] [created:: 2026-10-29] ^gcal-2a68f9c71d40
  - [Join meeting](https://meet.google.com/...)
  - Notes: bring the revised diagram.
- [*] #task **14:00–15:00** Roadmap review [↗](https://calendar.google.com/...) [root:: job] [created:: 2026-10-29] ^gcal-842da36e918f

## Pomodoros

- [ ] () — MEET
  - [[2026/20261029#^gcal-2a68f9c71d40]]
  - [[2026/20261029#^gcal-842da36e918f]]
```

The URLs and IDs above are illustrative. Generated IDs must be stable, collision-checked, and unrelated to the title. Keep link bullets pure: appending time, title, or a source marker to the same bullet can stop it being a dedicated Task Link.

Design the rendered Events section as a quiet agenda: aligned time labels, title as the main visual element, restrained root attribution, and one useful join/source affordance. Use the existing root/theme colors, not a new Google-color palette competing with Bob's. Avoid attendee lists, raw event IDs, long URLs, sync timestamps that change every five minutes, and verbose imported descriptions.

Sort active rows by all-day first, then start time, then a stable identity tie-breaker. Keep notes attached when reordering. Do not reorder historical completed rows gratuitously. Flag overlaps without making them failures. Show the timezone in the section UI when it would be ambiguous, and in CLI output always. A stale badge belongs in the view/status response, not in repeatedly rewritten Markdown.

Empty-state wording must distinguish **“No accepted events”** from **“Calendar unavailable; last successful sync …”**. The importer should not create an empty MEET placeholder. A removed last event can remove an untouched, empty managed placeholder; a user-edited or timed entry stays.

The raw Markdown must remain pleasant on mobile and without Bob plugins. Plugin polish should enhance that baseline, not make the data intelligible for the first time.

## 5. A small, coherent `bob gcal` interface

`gcal` is the integration noun: its commands concern the Google Calendar account, projection, and associated local preferences. Keep subcommands and options alphabetized in help, provide short aliases for all public long options, and put the group under Integrations. Bare `bob gcal` must be read-only, in accordance with Bob's CLI rules.

| Command | Purpose |
| --- | --- |
| `bob gcal` / `bob gcal list` | Show today's agenda, source freshness, import decisions, root attribution, and the next useful action. No vault writes. |
| `bob gcal calendars` | List account calendars with stable IDs, roles, timezone, and selection. Do not select everything automatically. |
| `bob gcal doctor` | Diagnose transport/version, credentials/scopes, key store, connectivity, source completeness, roots, ownership conflicts, writer host, and daily-note structure. Never print secrets. |
| `bob gcal login` | Authenticate or repair authentication. Browser flow locally; an explicit remote mode on a server. It does not import tasks. |
| `bob gcal logout` | Disable this integration's local credential binding and scheduled activity; retain imported tasks and notes. Explain separately how to revoke Google access. |
| `bob gcal root EVENT [NOTE]` | Show routing provenance, or set a private local root override. Support a series-wide override and clearing the override. Never edit Google. |
| `bob gcal setup` | Guided first use and reconfiguration: transport, authentication, selected calendars, day timezone, writer host, root/meet migration preview, sync preview, and automation choice. |
| `bob gcal sync` | Fetch, validate, plan, and apply one bounded reconciliation; repeat safely. |

Useful initial options, scoped to the commands that need them: `-a/--account`, `-b/--bob-dir`, `-c/--calendar`, `-D/--date`, `-d/--dry-run`, `-f/--format human|json`, `-h/--help`, `-r/--remote`, and `-u/--unresolved`. For `root`, use command-local `-c/--clear` and `-s/--series`. These are proposed public spellings, not existing commands.

`list -D tomorrow` supports the current morning review. `sync -d` must use the same planner as a write and show creates, metadata updates, moves, retirements, preserved user edits, conflicts, and pending daily-note creation. Its JSON should be versioned, with per-event reason codes and an explicit snapshot-completeness state. Preview may refresh a local API cache; it must not modify vault files, durable projection receipts, or credentials.

Do not add `watch`, `push`, event CRUD, a generic query language, or a separate `preview` command in V1. `sync -d` already provides preview; `list` can show status. Offer repair through doctor diagnostics and scoped sync behavior before inventing a broad destructive `reset` command.

## 6. Authentication: easy must include the first run and the tenth week

### Reuse gog behind a strict interface

The installed gog has browser OAuth, remote/manual support, persistent token storage, read-only Calendar authorization, and paginated JSON event output. Source at the installed commit confirms PKCE S256 and offline authorization in `internal/googleauth/oauth_flow.go`; `internal/googleauth/service.go` maps Calendar read-only mode to `calendar.readonly`.

Use a Bob-owned credential namespace where practical, so logging out of Calendar cannot break Bryan's Gmail tooling. Detect an existing usable Calendar grant and offer reuse explicitly during setup rather than copying token files or assuming Gmail authentication authorizes Calendar. Never fetch or expose the token just to test it; test the requested API operation.

The adapter should invoke argv directly, with an explicit account and one calendar per process, JSON, no interactive prompts during sync, full pagination, bounded execution time, and runtime read-only enforcement. **Do not use `gog calendar events --all` as the authoritative snapshot.** In the inspected version, `listCalendarIDsEvents` reports a failing calendar on stderr and continues, potentially returning success with incomplete data. The single-calendar path returns the fetch error. This is a concrete reason Bob needs an adapter, not a shell pipeline parsing whatever gog prints.

Pin/test a supported gog version and validate the expected schema. Its event-list JSON includes full event objects, but ordinary listing uses `ShowDeleted(false)`; retirement therefore needs Bob's complete-snapshot comparison and targeted lookup for disappeared known IDs. Compatibility tests must exercise that distinction. The transport interface should permit a future native implementation without changing reconciliation or user behavior.

An embedded native OAuth/HTTP client would eliminate a runtime dependency and permit narrower scopes, but adds token storage, refresh, callback, and platform work that is already solved here. A Python official-client adapter is another viable fallback; carrying two runtimes for this feature is not my first choice. Bob's existing gkeep adapter is precedent for separating external transport from Rust vault mutation, **not** precedent for reusing Keep's cookie/master-token authentication.

### The actual login experience

On a desktop: explain the read access, open the system browser, receive a loopback callback, validate OAuth state and PKCE, store the refresh token securely, and verify Calendar access. Google's supported desktop flow uses a Desktop app OAuth client; a packaged desktop client secret is not a secret the application can protect. [Google desktop OAuth](https://developers.google.com/identity/protocols/oauth2/native-app)

On apollo: offer the adapter's supported remote flow, with the complete redirect URL entered at a hidden prompt and matched to saved, expiring state/PKCE. Prefer a localhost tunnel when available. Do not expose the callback on all interfaces, or put an authorization response in shell history. A failed browser navigation to server-local loopback needs a clear explanation. This must be tested against the exact supported adapter version.

Do not promise a device-code login for Calendar: Google's device-flow allowed scopes do not include Calendar. The old out-of-band authorization-code flow is also retired. Copying a loopback redirect URL in an appropriate remote flow is not permission to use the obsolete OOB redirect URI. [Device-flow scope list](https://developers.google.com/identity/protocols/oauth2/limited-input-device#allowedscopes), [OOB migration](https://developers.google.com/identity/protocols/oauth2/resources/oob-migration)

If Bob later owns OAuth directly, the API operations suggest `calendar.events.readonly` plus `calendar.calendarlist.readonly`; add calendar-metadata read only if the chosen discovery calls require it. The recommended gog path currently requests broader **read-only** `calendar.readonly`. State that tradeoff honestly. No event-write scope is needed for description-based routing or local overrides. [Calendar scope definitions](https://developers.google.com/workspace/calendar/api/auth)

A remaining first-use hurdle is obtaining an OAuth client. A personally configured Desktop client is practical for Bryan, especially if his existing gog setup already supplies one. A publicly distributed one-click experience requires Bob to own the OAuth project and its distribution/verification responsibilities; wrapping a CLI cannot remove that obligation.

Warn specifically about the seven-day refresh-token lifetime for external apps left in Testing. Production publishing and verification are distinct: Google's personal-use exception may avoid verification, while retaining an unverified-app warning. Workspace administrators may still block access. Setup should detect API/scopes failures and explain the exact corrective action; it should not claim to infer consent-screen publishing status from a token alone. [Refresh-token expiration](https://developers.google.com/identity/protocols/oauth2#expiration), [Verification exceptions](https://support.google.com/cloud/answer/13464323?hl=en)

Store tokens outside the vault, Git, report files, and logs. Use macOS Keychain or the established secure headless backend. Keep account identity stable independently of a friendly calendar name. A revoked refresh token should produce one actionable stale-state error, never an empty successful agenda or an endless browser prompt from the scheduler.

## 7. Which events belong in Events?

**Proposed product policy:** default to the authenticated account's primary calendar; additional accounts/calendars are explicit selections. Evaluate expanded occurrences, not a recurring-series master.

| Event condition | Default behavior |
| --- | --- |
| Bryan's attendance is accepted; ordinary event | Import |
| Bryan is the organizer of an ordinary event | Import, unless explicitly declined in an attendee record; show this policy in setup |
| Bryan is tentative | Exclude by default; optional inclusion renders “Maybe” |
| Declined or needs action | Exclude; show reason in diagnostic/list detail |
| Canceled occurrence | Retire the managed live projection, preserving notes and history |
| Missing/omitted attendance evidence on another person's calendar | Do not guess; prefer Bryan's primary copy or report uncertain eligibility |
| Birthday, working location, focus time, out-of-office | Exclude by default; these are not attendance tasks |
| Accepted all-day ordinary event | Include as “All day”; create no duration |
| Duplicate copy in a second selected calendar | Prefer an explicitly configured authoritative copy; do not duplicate the task |

Presence in Calendar does not imply acceptance: invitation settings can add invitations before a reply. Large invitations also have response-propagation limitations. That is another reason to prefer the user's own calendar copy. [Google invitation behavior](https://developers.google.com/workspace/calendar/api/concepts/inviting-attendees-to-events)

A particularly easy bug: `attendees[].self` and `organizer.self` describe the **calendar on which the copy appears**. On a shared calendar, they need not identify Bryan. Use self on the authenticated primary copy; elsewhere match the selected account's verified identity/explicit aliases. Do not equate having owner access to a shared calendar with personally organizing every event on it. [Event field definitions](https://developers.google.com/workspace/calendar/api/v3/reference/events), [Calendar sharing roles](https://developers.google.com/workspace/calendar/api/concepts/sharing)

Use an explicit IANA **vault-day timezone**, selected at setup, rather than this server's UTC setting. Construct each day's local midnight boundaries separately; a DST day is not always 24 hours. Convert timed events into that zone. All-day values are calendar dates, not UTC timestamps. Preserve a single canonical task for a multi-day occurrence; show a continuation link in subsequent days' Events and link the same open task from those days' MEET queues. Do not create independently completable copies. [Timed and all-day event model](https://developers.google.com/workspace/calendar/api/concepts/events-calendars)

Boundary tests should use interval overlap: include an event that ends after the day begins and starts before the next day begins. `timeMin` filters event **end**, and `timeMax` filters event **start**; treating both as start bounds loses overnight meetings. All-day end dates are exclusive. The API also requires walking every page, even when an intermediate page is short or empty. [Events.list](https://developers.google.com/workspace/calendar/api/v3/reference/events/list), [Event end semantics](https://developers.google.com/workspace/calendar/api/v3/reference/events)

## 8. Root selection in Calendar and Bob

Use one plain, standalone line in the Google event description:

```text
bob-root: job
```

This is easier to type on mobile than JSON, namespaced enough not to capture an unrelated “root” sentence, and stays out of the event title. Bob writes the canonical task property `[root:: job]`; the Calendar spelling is an input convention, not a second task-field syntax.

Parse the description through safe HTML-to-text normalization, then accept exactly one directive line. Normalize whitespace but do not interpret arbitrary Markdown, capture grammar, commands, paths outside the vault, or task fields from the rest of the description. Treat conflicting directives as a warning, not “last one wins.” Calendar descriptions can contain HTML. [Event description field](https://developers.google.com/workspace/calendar/api/v3/reference/events)

Resolve the value through Bob's normal note resolver and root-chain logic. Require an existing, unambiguous area/root project for the clean path. If the selected note rolls up elsewhere, show both the selected note and effective root, with the existing repair hint. A root override does not inherit project blocking, because it does not move the task into that project.

Precedence should be explicit and visible in `gcal list` detail:

1. Private occurrence override, including an intentional local edit to the task's root.
2. Private series override.
3. Valid directive on the effective Google occurrence description.
4. Selected calendar's configured default.
5. Global default `meet`.

A local root edit should become a durable override, not be overwritten on the next refresh. `root --clear` relinquishes it. Validate before materialization; a bad remote directive retains the previous valid root, or uses `meet` for a new row, and reports the problem. Do not create a new area from text supplied by an organizer. When a root note is renamed, preserve the local override through the existing link/rename machinery or report the stale reference; never silently invent a replacement.

Why not private Google extended properties? They offer private metadata bound to a calendar/event copy, but are written through event mutation APIs and are not a convenient ordinary description field. They would require a write-capable feature simply to assign reporting attribution. Shared properties are worse for a personal root. Keep private extended properties as a possible later integration hook, not the V1 user experience. [Extended properties](https://developers.google.com/workspace/calendar/api/guides/extended-properties)

Descriptions may be visible to other attendees, and received invitations may not be editable. Explain this once when teaching the convention. `bob gcal root EVENT job` is the private alternative; it changes only local preferences. Do not automatically edit Google descriptions or send event-update notifications.

### Modernizing `meet.md`

Preserve its filename, content, inbound links, and historical references. Add proper area frontmatter. Given the observed untyped `work` chain, my default migration is a top-level area:

```yaml
---
type: "[[area]]"
parent: "[[area]]"
---
```

Keep a prose link to the former work context if useful. An intentional existing modern area parent would also be valid; do not migrate the entire legacy work hierarchy as collateral work. Ensure a normal `## Tasks` section exists for meeting preparation/follow-up that belongs in meet itself. The imported occurrence tasks remain in their daily notes.

An area does not need `root: true` or a `^prj` task. Avoid pretending that `[root:: meet]` alone modernizes an untyped note. Theme MEET and root meet are separate dimensions; an event can be MEET work attributed to job or another root.

## 9. Sync architecture: small snapshot, careful reconciliation

### Start with bounded full snapshots

Poll today's window and a small adjacent-day cache, plus targeted checks for previously materialized events that disappeared or remain unresolved. Initially materialize only the requested day, defaulting to today. `list tomorrow` can read the cache or fetch without creating tomorrow's file. Keep a bounded catch-up window for already managed past days; surface older unresolved records without repeatedly rewriting all history.

For a few calendars and a few days, this is easier to reason about than a long-lived incremental store. A five-minute interval, refresh on relevant daily-note creation, and manual sync are reasonable starting defaults. Show actual staleness. Use backoff with jitter for quota/transient failures and respect response retry guidance; current quotas are project-specific, so do not hard-code an old published allowance. [Google quota handling](https://developers.google.com/workspace/calendar/api/guides/quota)

Incremental sync is a future optimization, not a requirement for correctness. A moving `timeMin`/`timeMax` query cannot simply be combined with `syncToken`. An incremental implementation must retain a compatible collection query, consume all pages, persist the final token only after durable state, and rebuild its remote cache after HTTP 410. Rebuilding a cache must never mean deleting user-authored tasks or notes. [Sync guide](https://developers.google.com/workspace/calendar/api/guides/sync), [List parameter restrictions](https://developers.google.com/workspace/calendar/api/v3/reference/events/list)

Do not begin with push notifications. They require an HTTPS receiver and channel management; notifications contain no event body, so reconciliation is still necessary. Polling fits a personal CLI and an existing always-on host much better. [Calendar push notifications](https://developers.google.com/workspace/calendar/api/guides/push)

### Stable occurrence identity

Persist the opaque account identity, actual calendar ID, API instance/event ID, and, for recurrence, series ID plus normalized `originalStartTime`. Retain `iCalUID` as supporting cross-copy evidence. Recurring instances have an original-start identity that survives rescheduling; the current displayed start must not be the key. Do not key by title, URL, position, or today's date. [Recurring instance identity](https://developers.google.com/workspace/calendar/api/guides/recurringevents)

Generate a stable Obsidian block ID from the source occurrence key and collision-check it. Keep the full key in `.bob/gcal/` provenance, not a long task-line property. For copies across calendars, reconcile only when exact UID/occurrence evidence and configured source precedence agree; an identical title and time is not enough. If a series split or delete-and-recreate produces new identities, show a replacement/conflict rather than transferring completion by a fuzzy title match.

Recommended storage separation:

| State | Location and ownership |
| --- | --- |
| OAuth credentials | Secure host credential store; never in the vault |
| Disposable API cache and retry timing | Host-local Bob state directory |
| Stable source→task mapping, last generated field values, import/release receipts, local root overrides | Versioned `.bob/gcal/` data in the vault, with schema version and one writer |
| Task completion and meeting notes | Ordinary daily Markdown |

Metadata needs enough provenance to recover after a cache loss or partial transaction. Do not store full descriptions, attendee lists, or conference secrets merely because the API returns them. Treat source identities and event URLs as private vault data too; avoid dumping payloads into default diagnostics.

### Transaction and failure behavior

1. Fetch and validate complete snapshots outside the vault-write lock. One selected calendar failing makes the reconciliation incomplete; V1 should preserve the entire previous projection and report failure rather than perform partial retirements.
2. Acquire the established maintenance lock and coordinate with vault sync. Re-read notes, settings, and provenance after syncing; recompute if their versions changed.
3. Build a pure plan from source data, last generated fields, and current Markdown. Identify rows by provenance and block ID, never by title search.
4. Compare current bytes against before-images immediately before writing. Stage daily edits, link repairs, and receipts together; use recoverable multi-file transaction records where a rename alone cannot provide atomicity.
5. Verify that every managed live link resolves once, every generated row has valid syntax/root, and unrelated bytes/user children survive. Persist successful generation receipts only with the corresponding durable writes.
6. Reconcile lanes through Bob's existing machinery, invalidate affected caches, and use the established vault commit/sync path. Distinguish “saved locally, vault sync pending” from “nothing applied.” A retry must not duplicate tasks.

Do not keep the lock while waiting on Google or an OAuth prompt. A failed page, malformed payload, 403, 404 from a lost calendar, offline state, or disabled calendar selection is **not** evidence that every event was canceled. Missing known IDs require targeted resolution or a visible “no longer visible” state, not destructive guessing.

One writer host should own scheduled sync and projection preferences. Apollo is a plausible default for this deployment, but setup should make the choice explicit. Other hosts render the synced result and may run read-only listing. Ownership transfer requires stopping the old scheduler and reconciling the vault before enabling the new writer. Deterministic IDs reduce duplicates but do not solve distributed text conflicts.

## 10. Reconciliation must preserve the user's work

Use a field-aware three-way comparison: the last generated value, the current Google value, and the current Markdown value. Do not regenerate the whole Events section from the current API list.

| Change | Recommended result |
| --- | --- |
| New accepted occurrence | Create one task, correct root, and its live planning link; record provenance |
| Title/time/location changes and local field untouched | Update only generated spans; preserve children and block ID |
| User edits title or a generated field | Preserve the edit; show a field conflict/override instead of silently winning |
| User completes or cancels task | Preserve terminal outcome; keep later sync from reopening it or re-linking it |
| User releases/removes a live link | Record suppression; ordinary refresh does not re-add it |
| Google cancellation or explicit decline | Remove managed live links; an untouched open row may become canceled with a reason; retain authored notes and historical evidence |
| Google reverses a cancellation | Reopen only a provably auto-canceled, otherwise untouched projection; never undo a human terminal outcome |
| Event moves within the same day | Update time and stable ordering without changing identity |
| Unfinished event moves to another day | Move its whole block and repair inbound links in one transaction when the destination exists; retain a small non-task cross-reference if useful |
| Destination daily note does not yet exist | Mark pending reschedule, remove old live commitment, and retain the canonical block until safe relocation; do not duplicate or invent a sparse daily file |
| Already attended event is later edited/moved | Preserve the attendance record; show source change separately rather than rewriting worked history |
| User moves task elsewhere | Locate by stable provenance/block ID; continue cautiously or mark detached, never recreate it in Events automatically |
| User deletes a previously imported row | Record a suppression/conflict and offer recovery; do not silently resurrect it |
| An event ends, but task remains open | Keep attendance unresolved; no auto-Done and no automatic next-day copy |

The implementation needs one reliable managed-entry identity for its MEET placeholder. Prefer a hidden child comment that moves with the ledger block, plus provenance, rather than a visible marker appended to `— MEET`. Test that the comment is ignored by all relevant parsers and survives ledger moves. Duplicate ownership markers are a repair error. Never adopt every user-created MEET entry merely because the theme matches.

At the end of a day, retain the daily event rows. `gcal list --unresolved` should surface recent past open occurrences for explicit completion/cancellation or creation of a separate follow-up task. They should not leak into a perpetual discretionary backlog. Implement this through explicit managed-event provenance and the existing daily visibility rules; do not assume the root override grants the behavior.

Preserving Events history requires an archive rule: ordinary archive runs should leave registered calendar occurrence rows in their canonical daily notes. If the user explicitly moves/archives one, the provenance must follow it and sync must not re-create it. Do not disable archive for the entire daily note or change unrelated task behavior.

## 11. The MEET entry is the main semantic design trap

A shared queue gives the desired Today membership with little visual duplication. However, three existing behaviors must remain visible in the design:

- The default plan budget is three themes and ten links; MEET and its links consume that budget unless exempted. Do not silently hide fixed commitments by adding MEET to `plan.exempt`. Show the pressure and let the user choose a later budget policy.
- The first open non-exempt entry is the highlight. Append the managed queue after existing planned work; a background calendar refresh must not reorder the user's highlight.
- Time attribution splits session duration equally among its linked tasks. A 30-minute appointment rooted at meet and a 60-minute appointment rooted at job, closed as one 90-minute MEET session, become 45/45. That is misleading.

Therefore, keep the daily queue untimed. For actual tracking, move the selected event's link into a separate ordinary MEET session, leaving later events in the queue. Existing task-link move gestures provide a baseline; a polished **Start this event** action can later wrap Bob's existing session operations without introducing a separate clock engine. It must not start a timer merely because an event begins in Google.

A queue plus an active MEET session also interacts with the existing duplicate-open-name lint. Recognize a positively identified calendar planning queue for this narrow lint exception; keep ordinary duplicate-entry diagnostics, theme counting, and Today semantics intact. Closed sessions and their retired links are user history and must not be “repaired” back into the queue. If the user deliberately times or closes the whole managed queue, report the attribution consequence and preserve the gesture.

This qualification is preferable to abandoning the requested single queue, inventing scheduled work as actual time, or changing all Stats attribution to duration weights.

## 12. Implementation boundaries and acceptance evidence

Build the source normalization and pure planner first, then the durable writer, then automation and UI polish. Keep the provider adapter replaceable. Bob plugins should render Bob's results and invoke its operations; they should not contain a second Calendar client or parse recurrence themselves. No Bob Mac Capture grammar change is required merely to display existing Task Links; any later new start-event protocol should remain versioned and thin-client compatible.

Likely affected surfaces:

- bob-cli: a `native/gcal` command family, transport/schema validation, projection state, daily-section planner, transaction integration, root validation, and provenance-aware archive/review handling.
- Existing contracts: daily task residence, Calendar ownership, lifecycle/visibility, and the narrow planned-entry lint exception. Update user-facing help/completion and relevant docs with the implementation.
- Vault migration: `meet.md`, the daily template's Events position, and the calendar-review checklist wording. Preserve tomorrow/conflict review and do not remove unrelated checklist work.
- bob-plugins: optional compact event presentation, status/error affordances, and eventually Start event. Source changes belong in bob-plugins and deploy through `bob plugins sync`.
- Automation/configuration: one writer service/timer, with timezone and scope explicit. Daily-note absence must be observable and retried when the note appears.

The acceptance suite should prove behavior, not merely snapshot implementation details:

| Test family | Cases that must pass |
| --- | --- |
| Identity and recurrence | Repeated sync is byte-identical; recurring exception moves retain identity; canceled occurrence; series split; duplicate calendar copy; same title/different IDs |
| Eligibility | Accepted/Maybe/declined/unanswered; organizer without attendee list; shared-calendar self trap; missing attendance; non-meeting event types |
| Dates | DST forward/back, different event/calendar/vault zones, midnight overlap, all-day exclusive end, multi-day continuation, year boundary |
| Mutation ownership | Completed/canceled task, user notes, edited title/root, removed link, moved/deleted row, changed root note, no resurrection |
| Failure and recovery | Page-two failure, empty intermediate page, malformed JSON, adapter version mismatch, token revocation, calendar ACL loss, crash between note/receipt writes, stale file, lock contention |
| Bob integration | Today links resolve; root Stats attribution; daily Next clearing; review-walk exclusion; missed-event review; archive retention; planned queue versus actual sessions; highlight and budget |
| Rendering | Decorated Pomodoros heading, CRLF, fenced fake headings, duplicate Events sections, empty agenda versus stale agenda, long/Unicode titles, safe HTML, clean source on mobile |
| Authentication | Desktop and headless login, denied consent, scope repair, noninteractive expired grant, isolated logout, no credential leakage |

Use recorded/redacted Google fixtures and an injectable adapter for almost all tests. Perform a small real-account acceptance test only after fixtures pass: one accepted event, one recurring exception, one reschedule, and a cancellation, verifying the daily note and a second no-op sync. Research here did not perform that test.

## 13. Evidence and limits

The most useful local anchors are `docs/pomodoro-homes.md` R5/R11, `docs/plan.md`, `docs/concepts/today-and-the-pomodoro-ledger.md`, `docs/task-status-hooks.md`, `src/native/task_root.rs`, `src/native/freshness/state.rs`, `src/native/collect_done/transform.rs`, `src/native/vault_rewrite/mod.rs`, and `src/native/gkeep/pull.rs`, at the bob-cli revision above. The gog adapter findings are directly checkable in `internal/cmd/calendar_list.go`, `internal/googleauth/oauth_flow.go`, and `internal/googleauth/service.go` at the installed revision above.

External claims are linked at their point of use to Google's official API/authentication documentation. Polling interval, CLI shape, root directive, data ownership, daily exception, storage model, and lifecycle rules are my design recommendations, not Google API guarantees. The exact daily-template renderer, the full meet-note content, actual selected calendars, supported account aliases, and real headless credential-store behavior still require implementation-time verification.

## Recommended solution

**Implement `bob gcal` as a read-only Google Calendar integration with a carefully managed local task projection.** Use the installed gog capabilities behind a strict per-calendar adapter; begin with accepted events on explicitly selected primary calendars, a clear organizer policy, bounded complete snapshots, and one writer host. Make setup guide OAuth, timezone, calendar selection, and a conservative `meet.md` migration.

Render one canonical task per occurrence in the daily Events section, default `[root:: meet]`, support `bob-root: NOTE` in the Google description and private occurrence/series overrides in Bob, and preserve user notes, completion, and stable identity through updates. Maintain one untimed MEET planning queue, while recording actual attendance time in appropriately linked sessions. Make missing permissions, incomplete snapshots, ambiguous roots, and unresolved past attendance visible without destroying existing data.

That retains the attractive part of the idea—a beautiful daily agenda integrated with Bob's task and time model—while avoiding duplicate tasks, fictitious meeting time, and a second system competing to own the calendar.
