# Personal calendar details, before the daily note exists

Independent design research by **cdx** · 2026-11-09

**Recommendation:** give every Google event a small **My details** editor in Bob. Save root attribution and before/after buffers, including their reasons, in a vault-owned record attached to the event's identity. Let normal calendar sync project those details into the Event Task later. Keep the Google connection read-only.

This solves a real ownership mismatch: the organizer controls the meeting; Bryan controls what attending means for his own time and areas. A personal layer is a good idea. A second calendar, a copied invitation, or prematurely created daily-note tasks would introduce much more machinery than this problem needs.

This report is independent. I did not consult the other swarm researchers' reports, transcripts, summaries, or findings. I inspected bob-cli at `b97d8d4c3b214d1f73f0627f868a108ff6755a66`, Bob Mac Capture at `a65fb6a06d6d50d88ab263cf58914108e2be73f4`, audited project decisions, and the Google documentation linked below. This is a researched design, not an implemented or live-account-tested feature.

## 1. The actual job to solve

After responding to an invitation, Bryan should be able to select that event, type familiar metadata such as:

```text
@body
-30 I need to walk home from the park
```

and know that Bob will remember it when the event arrives—even if its daily note does not exist, the organizer changes its title, or the meeting moves to another day.

The interaction should answer three questions immediately:

1. **Which event am I changing?** Show date, meeting time, calendar, and title.
2. **What will this do?** Show attribution and the occupied time around the unchanged meeting.
3. **Where is it saved?** Say “Only in Bob,” with a separate status for whether today's note has been updated.

There are two important semantic corrections to make explicit:

- `-30` means **30 minutes before this meeting**. If walking home happens after the selected park event, the input should be `+30`. The software must not reinterpret the sign from prose. A preview makes the distinction obvious.
- A Bob buffer reserves time in **Bob's planning and ledger views**. It does not add Google busy time, stop an outside booking system, or notify other attendees. If blocking availability in Google is the real objective, that is a separate calendar-writing feature.

## 2. What exists today, and what is missing

Bob already has most of the projection machinery:

| Existing behavior | Design implication |
| --- | --- |
| `bob gcal list -D DATE -a` can inspect a future day, including omitted events. | Event selection need not depend on a daily note or an accepted RSVP. |
| Sync requires an existing, rendered daily note with Pomodoros. | Saving personal metadata must be independent of sync and daily-note creation. |
| Roots come from learned series edits, event directives, colors, calendar configuration, or the default. | Add personal intent as an explicit source, with visible provenance. |
| The normalizer preserves event ID, calendar ID, iCalUID, recurring-event ID, and original start. | Stable attachment does not require title matching or a new external service. |
| Buffers drive occupied-time calculations and MEET placement without replacing the meeting's bold time span. | Reuse the same buffer type and calculations. |
| Imported description bullets, including Google buffer reasons, are tracked as one block. | Personal reasons cannot simply be concatenated into that block without changing ownership. |
| The Mac is the calendar-sync writer; changes are protected by a vault lock and preimage checks. | Keep note projection on that writer and reuse its transaction path. |
| Mac Capture already displays a Calendar band, root hues, buffer capsules, and buffer wings on its time rail. | Extend the existing visual language instead of creating an unrelated calendar application. |

Sources: [calendar behavior and limitations](https://github.com/bobs-org/bob-cli/blob/b97d8d4c3b214d1f73f0627f868a108ff6755a66/docs/gcal.md), [normalized event data](https://github.com/bobs-org/bob-cli/blob/b97d8d4c3b214d1f73f0627f868a108ff6755a66/src/native/gcal/model.rs#L21), [snapshot acquisition](https://github.com/bobs-org/bob-cli/blob/b97d8d4c3b214d1f73f0627f868a108ff6755a66/src/native/gcal/snapshot.rs#L61), and [Mac Calendar band](https://github.com/bobs-org/bob-mac-capture/blob/a65fb6a06d6d50d88ab263cf58914108e2be73f4/docs/idle-agenda.md).

A hand-added `[buffer::]` or `[root::]` is a useful emergency workaround once a task exists. It is not a complete solution: it depends on that day's note, supplies no advance-event picker, and participates in the existing manual-edit protections. Creating future notes just to obtain a place to put metadata also exposes them to existing future-day status and templating behavior.

## 3. Google offers a real alternative—but it is not the best default here

Google supports `extendedProperties.private` on an attendee's local event copy. These properties are scoped to the calendar/event pair. They can be set with event mutation requests; a property value is limited to 1,024 characters. This is a genuine alternative to an external database, not an organizer-only capability. [Google: extended properties](https://developers.google.com/workspace/calendar/api/guides/extended-properties).

Google distinguishes organizer-owned shared information from attendee-specific properties such as reminders, color, and private extended properties. Its documentation also says attendee-side changes to shared fields can be overwritten by organizer changes. Thus even where an API can alter a local description, using it as durable personal metadata would be a weak contract. [Google: event copies and propagation](https://developers.google.com/workspace/calendar/api/concepts/inviting-attendees-to-events).

However, writing private properties requires an event-writing OAuth scope; the existing read-only grant is insufficient. The published scopes do not offer a general “write only my Bob metadata” permission. Do not confuse owning a calendar with organizing an event: some write scopes concern calendars the user owns, which can contain invitations from others. Exact behavior on a read-only shared calendar still needs a targeted proof if this option is ever selected. [Google: patch authorization](https://developers.google.com/workspace/calendar/api/v3/reference/events/patch), [scope definitions](https://developers.google.com/workspace/calendar/api/auth).

### Alternatives compared

| Approach | What it does well | Main cost or failure | Judgment |
| --- | --- | --- | --- |
| **Vault-owned personal event details** | Works before task creation; keeps existing Google grant; survives organizer edits independently; uses Bob's sync and backup model | Requires reliable identity, a picker, and explicit projection ownership | **Best fit** |
| Google private extended properties | Stores data with the attendee's calendar copy; could support a Calendar-side editor | Requires write consent and another client surface; permission and recurrence behavior need testing | Credible later option if editing directly inside Google becomes essential |
| Change the attendee copy's description/title | Familiar location for directives when possible | Permissions vary; organizer changes can erase local shared-field edits | Reject as durable storage |
| Personal event colors mapped to roots | Existing Bob feature; may solve a root-only case with little work | Cannot express minutes or reasons; a visual palette is a poor general metadata store | Useful interim shortcut |
| Edit future Event Tasks | Reuses Markdown | Requires future-note materialization and creates two places to maintain intent | Reject as primary workflow |
| Duplicate event or personal shadow calendar | Ownable descriptions; separately created busy blocks can affect Google availability | Duplicates, cancellation/move tracking, recurrence coupling, and possible double-counting | Only for a separately requested availability feature |
| Title/organizer matching rules in configuration | Fast for predictable repetitive meetings | False matches; title changes; unsafe attachment of personal intent | Avoid in initial release |
| Workspace add-on or browser extension | Can put the action beside the invitation | Another distribution/security/runtime surface; vault delivery remains unsolved | Treat as an entry point, not the storage architecture |

A Google Workspace add-on can react when an event is opened and receive calendar/event identity. That makes a future “Open My details in Bob” bridge plausible without scraping title text. It does not by itself create a connection to the local vault, and it is not evidence of an automatic, atomic RSVP-plus-Bob transaction. [Google: Calendar add-on manifest](https://developers.google.com/workspace/add-ons/reference/rpc/google.apps.script.type/calendar), [event objects](https://developers.google.com/workspace/add-ons/concepts/event-objects).

## 4. The proposed experience

### Find the event at RSVP time

Add a clearly named **Calendar → My details…** action to Mac Capture's menu and an equivalent action on today's Calendar-band rows. The menu opens an event picker covering upcoming events, with search and an explicit date jump. A 30-day initial browse window is reasonable; it must be an initial query bound, never a limit on how far ahead metadata can be saved.

Rows show title, date/time, calendar name, RSVP state, and a small “My details” indicator when settings exist. Distinguish two events with the same title. Searching filters candidates; it never authorizes a write until a specific event is selected.

Include unanswered and tentative invitations in this editor even when ordinary sync excludes them. A saved annotation must not accept an invitation or override inclusion rules. If an invite is not yet present in the account, say “Not in Calendar yet—respond or add it in Google, then refresh.” Google documents that invitation settings can delay insertion until a response. [Google: invitation visibility](https://developers.google.com/workspace/calendar/api/concepts/inviting-attendees-to-events).

For all-day, free, and other context-only events, explain that Bob will not create an Event Task under current inclusion rules. Disable buffer editing where there is no supported timed meeting span; storing attribution must not silently promote a context row.

Paste-an-event-link is useful as an accelerator, provided Bob resolves and validates supported URL forms to API identity. Keep search/date selection as the reliable fallback; do not assume every Google link encodes the attendee's actual event copy.

### A small, calm editor

Conceptual wireframe; these are proposed controls, not an existing interface:

```text
My details                                  Only in Bob

Call with Sam
Wed 18 Nov · 14:00–15:00 · Personal · Going

Attribute to     ● body                   My choice
Before           30 min
                 I need to walk home from the park
After            Follow Calendar · none

                 13:30       14:00                 15:00
                 ░░░░░░░░░░░████████████████████████
                 Before     Call with Sam

                 Occupied in Bob 13:30–15:00
                 Meeting 14:00–15:00

Applies to       This event

Reset to inherited details                    Save
```

Use the current root hue for attribution and buffer wings, with text labels that work without color. The meeting stays visually solid; the reserved wings are lighter/hatched, matching the existing Calendar band. Keep the event identity fixed at the top and Save/Reset visible when the reason wraps. Announce meeting time, before/after minutes, occupied range, and scope to VoiceOver. Respect Reduce Motion. Do not use a color change as the only indication that a field is overridden.

Provide an optional **Paste directives** field for familiar input. The two lines from the request populate the structured root/before controls and the preview. This is one editor state with two input methods, not two independently stored versions. Parsing and validation belong to bob-cli; Swift only renders the result.

For personal input, reject contradictory repeated settings with a precise inline explanation. The forgiving “first value wins; the rest stays prose” rule makes sense for imported organizer descriptions, but silently ignoring a value in an intentional settings editor does not. Unrecognized text must not vanish. Initial scope is routing and buffer reasons, not a general-purpose task-capture grammar.

### Show the difference between saved and applied

- Future event without a note: **“Saved for 18 Nov. Bob will use these details when the event syncs.”**
- Today's writable, untouched row: **“Saved and applied to today's event.”**
- Note not ready, network unavailable, or sync failure: **“Saved in Bob. Today's note still needs an update.”** Offer Retry.
- A conflicting note edit: show the saved intent and the current note value; do not claim the new value is applied.

The metadata save must succeed independently of Google fetching or note projection once event identity is established. A cached event can be edited offline with a visible “Calendar last checked…” timestamp; fetching a completely unknown event requires connectivity. Retry projection without duplicating the saved operation.

The editor must not hide while an unsuccessful save has left the draft unsaved. Escape returns to the picker and preserves the draft during that interaction; successful save offers Undo.

### The phone question

The request says when Bryan normally RSVPs, not which device he uses. A Mac hotkey immediately after RSVP meets a desktop workflow. It does **not** complete a phone-first workflow. I recommend the existing Mac client first, but mobile entry is a release criterion if phone RSVP is common. A future share action or Calendar bridge should invoke the same identity-based backend; a text inbox that guesses the event later is not an acceptable substitute.

## 5. A precise data and precedence model

### Separate personal intent from materialized daily rows

Use a dedicated vault namespace, for example:

```text
.bob/gcal-personal/<host>.jsonl
```

This is proposed storage. Existing `.bob/gcal/<host>.jsonl` records what sync wrote, row deletions, resets, and learned roots. Personal intent has a different lifetime: it can precede the row and must survive rebuilding that row. Keeping it separate also avoids making a day reset or existing malformed-record handling accidentally discard the settings.

Reuse the shared preference-journal infrastructure, but add the durability and validation this feature needs. The current helper provides append writes and deterministic fold ordering; its general reader can skip unreadable files or malformed lines. A calendar planner must not silently interpret missing personal settings as permission to remove someone's reserved travel time. Fail projection closed on an incomplete personal-state read, with a visible diagnostic. [Existing journal mechanics](https://github.com/bobs-org/bob-cli/blob/b97d8d4c3b214d1f73f0627f868a108ff6755a66/src/native/pref_journal/mod.rs), [calendar projection journal](https://github.com/bobs-org/bob-cli/blob/b97d8d4c3b214d1f73f0627f868a108ff6755a66/src/native/gcal/journal.rs).

For the first release, accept writes on the configured `gcal.writer` host only. This is an explicit scope choice: the Mac UI is the writer; other hosts can read synced metadata. It avoids introducing concurrent remote authors merely because the storage format can contain multiple host files. Future multi-host editing needs field-level conflict semantics, not a claim that timestamp ordering prevents lost intent.

Each record should include a schema version, operation ID, host/time, account namespace, canonical calendar ID, event selector, changed fields, and the revision the editor observed. Serialize local writers, check the observed revision, append and flush durably before acknowledging Save. Retry with the same operation ID is idempotent. Undo and reset append new operations.

Store typed values, not a fake Google description. Minimal illustrative payload:

```json
{
  "selector": {
    "account": "you@example.com",
    "calendar_id": "resolved-calendar-id",
    "event_id": "selected-event-id"
  },
  "scope": "occurrence",
  "fields": {
    "root": {"mode": "set", "value": "body"},
    "before": {
      "mode": "set",
      "minutes": 30,
      "reason": "I need to walk home from the park"
    }
  }
}
```

This omits the envelope and concurrency fields for readability. Resolve `primary` to the actual calendar ID. The current event model keys by calendar/event while account is held on the snapshot; personal storage must bind the account too, so changing logins cannot retarget an annotation.

### Identity

For a single event, use **account + calendar ID + event ID**. Never key by title, current date, daily-note filename, or block ID.

For a recurring occurrence, retain the concrete instance ID and **series ID + originalStartTime** in the same account/calendar namespace. Preserve all-day dates as dates and timed anchors as instants; do not convert an all-day identity through UTC midnight. Google defines originalStartTime as the occurrence identifier that stays meaningful when the instance is moved. Recurring instances have distinct IDs while sharing an iCalUID, so iCalUID alone is insufficient. [Google: recurring instances](https://developers.google.com/workspace/calendar/api/guides/recurringevents), [event resource identity](https://developers.google.com/workspace/calendar/api/v3/reference/events).

These keys survive ordinary time/title changes and movement between daily notes. An organizer replacement, series split, or move to a different calendar can create a new identity. Preserve the old annotation as unresolved/inactive and offer an explicit transfer after inspecting the new event. Similar titles and matching iCalUIDs may help explain candidates; they must not silently transfer personal intent.

### Resolve each field independently

For new or still-managed projection, the order is:

1. Explicit personal occurrence value.
2. Explicit personal series value, when that scope is supported.
3. Existing Bob defaults for that field.

“Existing defaults” means the current root ladder, including its learned-series behavior for new rows, or the parsed Google value for a buffer side. Existing note edits remain a separate protection layer during projection.

Each buffer side is an atomic **minutes + optional reason** value. A local before-buffer overrides only before; it must not erase an inherited after-buffer. When a local value replaces a Google value, do not accidentally carry over the organizer's reason. A local 30-minute buffer with no reason should not display Google's explanation for a different trip.

Distinguish these states in storage and UI:

| State | Meaning |
| --- | --- |
| Inherit | Remove this scope's choice and use the next source. |
| Set 0 minutes | Explicitly reserve no time on this side, even if Google or the series specifies a buffer. |
| Set N minutes, optional reason | Use this exact personal value. |
| Follow Calendar, bypass personal series | Needed when series settings exist and one occurrence should follow its external/default inputs instead. |

The last state should be introduced with series support; it is unnecessary complexity for occurrence-only v1. An absent field in a partial API update means “leave my current choice alone,” not “reset it.”

Validate roots using the existing resolver and buffer minutes using the existing limits. Bob currently supports 0–720 minutes per side, clamps pre-buffers at midnight, and keeps the occupied span under 24 hours. Show any clipping in preview; do not silently promise a full 30-minute reservation when only ten minutes fit before midnight. [Buffer implementation](https://github.com/bobs-org/bob-cli/blob/b97d8d4c3b214d1f73f0627f868a108ff6755a66/src/native/event_task.rs#L23).

If a previously valid root stops resolving, retain the authored value and show it as unresolved. Require correction before applying that field; silently falling back while labeling it “My choice” would be misleading.

## 6. Projection ownership is the difficult part

### One resolver shared by all consumers

Build an effective-event layer between provider normalization and root/clock/planning/rendering:

```text
Google event + personal record
          ↓
effective root, before/after values, reasons, and provenance
          ↓
picker preview / gcal list / sync plan
          ↓
daily Event Task → existing agenda and event-time calculations
```

Do not mutate a provider description string and feed it back through the parser. That loses source ownership and turns override precedence into a token-order accident. Keep the raw normalized provider event and personal state distinguishable.

List and preview should report both the chosen effective metadata and any existing note value retained by manual-edit protection. Otherwise the editor can say `body` while the actual task remains `job`. Root changes can also change inherited on/off-clock attribution; the preview should show that consequence even though v1 does not add a new clock-setting feature.

The existing Mac agenda is derived from daily-note rows. It will naturally reflect a successfully projected `[buffer::]`; it should not paint unsynced personal intent as if the note already contained it. Add an event reference to agenda JSON where the sync journal can map the row reliably. An ordinary hand-written Event Task has no Google identity and should not receive the Google-personal-details action. [Agenda construction](https://github.com/bobs-org/bob-cli/blob/b97d8d4c3b214d1f73f0627f868a108ff6755a66/src/native/capture_pomodoros_agenda.rs#L836).

### Give personal reasons their own visible ownership

Render personal reasons in a compact **My details** subtree under the event, after existing managed logs and before imported description prose:

```markdown
- [*] #task **1400-1500** Call with Sam … [buffer:: -30m] [root:: body] …
  - **My details**
    - ↤ *30m before* · I need to walk home from the park
  - Organizer's agenda…
```

Omit the subtree when there are no personal reasons; attribution already lives on the task row. Keep `↤`/`↦` and duration labels consistent with existing reason bullets. Personal text still uses safe rendering, so it cannot accidentally mint tasks, tags, managed logs, or executable Markdown.

Track this subtree independently from the Google description block. Personal changes must not overwrite organizer bullets; edited organizer bullets must not freeze personal changes. Do not allow two indistinguishable managed windows: record separate hashes/lengths and require an unambiguous structural match. A user-created “My details” heading is not automatically Bob-owned.

For untouched imported blocks, suppress the Google reason for a side overridden by a personal buffer, while preserving unrelated prose and the other side's reason. If that block has been manually edited, keep it and show a one-time conflict rather than deleting the stale reason silently.

Direct edits or deletion of the personal subtree become a note-level override, just as other managed content can become user-owned. The editor then offers a concrete preview to restore the saved projection or keep the note. No automatic resurrection of a deleted block.

This deliberately departs from **Buffer Reasons Ride The Description Bullets**, which rejected a second block to avoid two ownership rules. That tradeoff was sensible when both numbers and reasons came from Google. Here there are two authors and two lifetimes. Keeping them in one hash would make the new feature unreliable. The added journal state and small visual label are justified.

Also, `gcal.description: off` should continue disabling imported Google prose and Google reasons. It should not hide explicitly authored My details. That is a proposed, clearly scoped behavior change.

### Avoid broad replacement of existing rows

Personal setters should not hand-edit a task row and rely on the next sync to discover what happened. They should write intent, then invoke the shared projection planner, which records the resulting baseline.

Preserve manual changes to unrelated fields. If a requested root or buffer conflicts with a note edit, show both values before choosing “Apply my saved value”; replacing one chosen field must not reset title, links, children, or checkbox.

There is a concrete implementation trap in the current code: buffer and clock tags share the badge span, and `apply_span_updates` only rebuilds the span group when its `edited` list is empty. Simply substituting a new buffer before rendering can therefore be blocked by another protected span. Personal fields need their own semantic merge/baseline, or a deliberate planner extension that applies only the requested fields. Do not assume three-way merge is already fully independent per field. [Current merge and refile trigger](https://github.com/bobs-org/bob-cli/blob/b97d8d4c3b214d1f73f0627f868a108ff6755a66/src/native/gcal/plan.rs#L950).

A changed effective buffer should trigger the same guarded MEET refile logic as a Google buffer change. Running or edited sessions retain their history and existing kept-filing diagnostics. Do not broaden this into rewriting recorded time. For v1, personal editing of already-worked occurrences should be read-only with an explanation; historical correction is a separate workflow.

Finally, `bob gcal sync -F` must reset the day's projection, not delete personal intent. Its new fresh render should include current personal settings while retaining existing history safeguards. Make the reset preview state that. This extends the current reset contract, which presently rebuilds from Google's chosen values.

## 7. Recurrence without surprises

Ship occurrence-only editing first if needed, but store recurrence identity from the start. Label the scope **This event**, not an ambiguous “Save.”

The next useful scope is **This and future occurrences**, with a start occurrence shown explicitly. Store a series rule plus an immutable original-start boundary; do not enumerate or write hundreds of event copies. An occurrence setting outranks the series. For multiple dated rules, the latest applicable start boundary wins per field; edits at the same boundary use a checked revision. Show the boundary and scope when reopening the editor.

A rescheduled instance keeps its original position for scope membership, even if its displayed date crosses the boundary. Explain that in the scope detail. A split/recreated series is a new identity and needs explicit transfer. Past worked history is not rewritten when a future-series rule changes.

Do not let saving a one-occurrence root through My details teach the existing implicit series-root learner. Record the projection as authored by the personal layer so it is not mistaken for a raw manual `[root::]` edit. Preserve legacy direct-Markdown series learning initially; expose that inherited source when relevant instead of silently migrating or deleting it. [Existing series learning](https://github.com/bobs-org/bob-cli/blob/b97d8d4c3b214d1f73f0627f868a108ff6755a66/src/native/gcal/plan.rs#L1303).

## 8. Reliability cases that should decide whether it ships

| Scenario | Required result |
| --- | --- |
| RSVP today for an event six months away; future daily note absent | Save metadata now; create no note/task; eventual projection uses it. |
| Google renames or reschedules the event, including a different day | Details follow verified identity; no title/date rematching. |
| Two calendars contain events with the same title/time | Only the selected account/calendar event changes. |
| `primary` is later configured by its actual ID, or account changes | Canonical identity prevents loss or cross-account application. |
| Recurring instance moves across DST or to another day | Original occurrence identity is retained; current local preview updates. |
| One side is explicitly zero; the other inherits | The override does not disappear just because the rendered zero field is omitted. |
| Google changes title/description after personal save | Organizer changes still arrive where managed; personal values remain. |
| Organizer's reason exists and Bryan overrides that side | No misleading inherited reason; edited prose is preserved with a conflict. |
| A local title/badge edit exists | Personal root/buffer application does not require resetting unrelated text. |
| Invitation is unanswered, tentative, declined, or cancelled | Metadata can remain stored; ordinary inclusion and cancellation policy controls tasks. |
| Event disappears during a failed or partial query | No deletion, orphan conclusion, or destructive projection from incomplete evidence. |
| Actual 404/410, removed access, or replacement event | Retain metadata; distinguish inaccessible from deleted when evidence permits; offer repair. |
| Daily row deleted by Bryan | Saving or syncing metadata does not automatically recreate it; existing reset semantics apply. |
| Forced day reset | Personal records survive and are included in the rebuilt effective event. |
| Process dies after save but before note projection | Next reconciliation applies once; Save is not falsely reported as lost. |
| Two editor windows save from the same revision | Second stale edit receives a conflict, not a silent overwrite. |
| Metadata file is unreadable, truncated, or a newer unsupported schema | Hold projection and explain; do not fall back to an empty metadata set. |
| Root change affects off-clock attribution | Preview shows the consequence; recorded sessions are protected. |
| Midnight clipping or a very long buffer | Preview shows actual supported occupancy, not the requested duration alone. |
| Older bob/client combination | Capability detection hides unsupported editing; existing agenda still works. |

Implement these as resolver/identity fixtures, fake-Google integration tests, projection crash/retry tests, and shared JSON fixtures for the Mac client. Verify the UI with long reasons, duplicate titles, dark/light appearances, keyboard-only use, VoiceOver, and narrow panels. No live Calendar writes are needed for testing the recommended architecture.

Compatibility deserves particular attention: an old bob binary does not know the personal namespace. A cleanly rendered row might look Google-owned to it. Before rollout, prove that an older writer cannot erase personal projections; use a managed-state version/capability guard or an explicit minimum writer version if necessary. Additive client JSON alone does not solve backward compatibility of a vault writer.

## 9. Implementation boundaries and requirement adjustments

The backend should offer explicit event discovery, detail inspection, preview, save, reset, and revision/conflict results under `bob gcal`. Exact command spelling should be settled with the CLI conventions, including short aliases for public long flags. These are new APIs; the report does not imply such commands already exist.

Keep raw event IDs out of normal UI but return an opaque stable event reference to clients. Ordinary list JSON need not start exposing organizer descriptions or attendee lists. The personal editor may return the user's own reason text in its explicit detail response; diagnostics should use counts/identifiers rather than logging that text.

The implementation centers on:

| Area | Work needed |
| --- | --- |
| `gcal/model.rs`, `gog.rs`, `snapshot.rs` | Canonical identity and bounded event discovery independent of task inclusion; effective-event resolution. |
| New personal-state module using `pref_journal` | Typed patches, strict reads, revision checks, idempotent durable saves, reset/undo. |
| `root.rs`, `plan.rs`, `journal.rs` | Explicit personal provenance, semantic field ownership, prevention of accidental series learning. |
| `description/bullets.rs`, `bullet_block.rs` | Separate personal subtree and correctly filtered effective reasons. |
| `refile.rs`, `sync.rs`, `reset.rs` | Personal buffer changes use existing safe placement, locking, reset, and recovery paths. |
| `list.rs`, capture agenda JSON, Mac Capture | Consistent preview/applied-state reporting; picker, editor, and familiar buffer visuals. |

Mac Capture must remain a thin client: no Swift parsing of `@body`, no second override resolver, and no direct vault writes. Its source compilation and exact-SHA macOS CI remain required for implementation; this research did not change Swift.

**Adjustments I recommend making explicit in the requirements:**

1. **Attach metadata to the calendar event before an Event Task exists.** The daily row is a projection, not the durable anchor.
2. **Support owned and invited events with the same editor.** Personal travel details should not depend on who organized the meeting.
3. **Keep v1 deliberately narrow:** root, before/after duration, optional per-side reason, occurrence scope. Defer general notes, tags, clock controls, matching rules, and automatic travel-time estimates.
4. **Preserve RSVP semantics.** Annotation is available before acceptance where the event is visible, but does not RSVP or force an event into the task list.
5. **Provide a Mac-first writer explicitly.** Phone-first capture and concurrent host authorship require additional work; do not claim they are solved by vault syncing alone.
6. **Separate personal reasons from imported prose.** This revises the earlier one-block tradeoff because authorship now differs.
7. **Keep external availability out of this feature.** Bob occupancy and Google free/busy are different promises.
8. **Make saved/applied/conflicted states visible.** No success message should hide a projection failure or a retained note edit.
9. **Preserve history and recoverability.** Save ahead of time, support explicit transfer/reset, and avoid automatically rewriting worked occurrences.

No source code or accepted decision record was changed for this research. The above are proposed requirements and design departures for review.

## 10. Final recommendation

**Build vault-owned My details with a compact Mac event picker and editor, backed by bob-cli's existing calendar model.** Save typed personal root and buffer settings immediately, independently of daily-note creation, and resolve them before ordinary list/sync planning. Keep Google read-only.

Start with one occurrence, robust identity, reset/undo, strict persistence, and clear saved-versus-applied feedback. Treat independent field ownership, personal-reason rendering, and protection against old writers as release requirements, not cleanup work. Add explicit future-series scope once the single-event path is dependable.

This is worth implementing. It gives Bryan a natural place to say what an invitation means for his own day without fighting the organizer or maintaining a duplicate calendar. The quality of the feature will come from a small editor that always identifies the right event, shows the actual occupied time, and keeps its promises when the event changes.
