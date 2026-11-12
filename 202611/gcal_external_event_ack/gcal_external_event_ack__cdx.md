**Calendar acknowledgment as a small review inbox — independent research by cdx**

Research date: 2026-11-12. Code inspected: bob-cli commit `4f7ab37f6180a84309e5f06e674a0f3afce5c135`.

**Recommendation.** Build `bob gcal ack` as a short, resumable review of external meetings. Save acknowledgment in Bob's existing Calendar journal, let successfully saved private notes count automatically, and put one conspicuous `⚠ UNACKED` marker on unacknowledged Event Tasks. Keep synchronization and attendance accounting working regardless of review state. This is a good idea if the gesture means “I have processed this commitment for Bob”; it becomes burdensome if it requires repeatedly approving invitations, occurrences with standing instructions, or incidental Google updates.

This is research, not implementation. I inspected local source, contracts, tests, audited project memory, and Google's API documentation. I did not consult any other swarm researcher's report or findings. I did not change executable behavior or the live `~/bob/gtd_daily.md`. The reminder below is a proposed implementation change: installing a reminder for a nonexistent command would be premature. I did not access live Calendar data or inspect the live vault, so meeting volume, actual shared-calendar configuration, and checklist placement remain unverified. No full test suite was run for this research-only change.

**Is this a good idea?**

Yes, particularly for catching missing preparation, travel buffers, project attribution, and off-clock classification. Keep three decisions independent:

| Decision | Authority | Meaning |
| --- | --- | --- |
| RSVP | Google Calendar | Whether you plan to attend |
| Acknowledgment | Bob's journal | Whether you reviewed the event for your Bob workflow |
| Task lifecycle | Existing sync, task, and ledger rules | Whether a task exists, is active, or is complete |

Someone can accept an invitation without considering logistics, add a private note before answering, or attend before reviewing. None should prevent Bob from showing commitments or recording meetings.

“Required before becoming an event task” conflicts with the explicit requirement that sync still create the task. Describe the feature as **“external meetings need review; unreviewed tasks stay visible with a warning.”** It is a soft review obligation, not a creation gate.

The main cost is another inbox. A weekly review also misses invitations received just afterward; the daily-row warning provides the second opportunity without another recurring task or notification service. Do not count RSVP, opening an event, editing its task title, completing the task, or sync importing organizer-authored prose as acknowledgment. Explicit `bob gcal note -A` adoption does count because it saves a private note through a user action.

**Requirement adjustments I recommend.**

| Original wording or gap | Proposed resolution | Reason / cost |
| --- | --- | --- |
| `bob gmail ack` versus the reminder's `bob gcal ack` | Use `bob gcal ack`; no invented Gmail alias | This is a new Calendar command, not an existing command rename |
| “All external events” | Review configured calendars' task-capable events, including Maybe and unanswered invitations | Avoid reviewing holidays, free-time context, cancelled events, and declined invitations |
| “Owned by me” | Use organizer identity and organizing-calendar ownership, with an unknown state | Edit permission and `organizer.self` alone are insufficient |
| `-n 7`, including today | Seven local dates total: today through today + 6; default 7; `-n 1` means today | Consistent with the inclusive-day convention of backward-looking `sync -n` |
| Only Ack and Note | Add Skip and Quit, neither acknowledging | Users need to defer or stop without making a false decision |
| Ack is a no-op | No Google, task-status, or note-content change; write a durable local receipt | Otherwise the same event returns forever |
| Note counts as acknowledgment | A valid saved nonempty note counts even after clearing; series notes cover the series | Treat review as a completed gesture, not a demand to retain arbitrary text |
| Organizer changes unspecified | V1 acknowledgment survives edits to the same identity | Avoid review churn; do not promise approval of the latest version |
| Warning unspecified | One separate Bob-managed marker on the task line | Visible with children folded; removable even on an edited task |
| Weekly task unspecified | One dated recurring task, installed when the command ships | Undated recurring tasks do not enter the review walk |

Restricting review to task-capable events is the main scope reduction. Reviewing every calendar entry, including all-day events and shared holidays, is a broader product; I would not make it this feature's default.

**What the code already provides, and where reuse needs care.**

Private notes already use `.bob/gcal/<host>.jsonl`, account-guarded event/series identities, arbitrary-host note writes, and application by the configured writer. Notes override description fields but never RSVP, change inclusion, or pre-create future daily notes. Forced day resets preserve them. The command already supports Yes, Maybe, and unanswered task-capable events, validated route/buffer grammar, preview, an editor, and fake-Google tests. [B1–B3]

Snapshots drain all pages and reject leftover page tokens. `FetchContext::fetch_days` batches contiguous dates into one range per configured calendar. Reuse this rather than invoking the 90-day note command once per event/day. [B4]

Specific implementation traps:

- `GcalEvent` retains organizer-self and a display label, but not organizer email separately. The raw parser and gog field mask already receive email; preserve it in the normalized model. `organizer_or_no_guests` is an RSVP convenience, not ownership evidence: empty or absent attendees makes it true. [B5]
- Note selection groups recurring instances into a series candidate. Reusing that final grouping would silently skip occurrences needing individual acknowledgment. Share raw selection and note services instead. [B6]
- Existing Calendar prompts use `read_line`. Genuine single-key interaction needs terminal input work, not just new prompt text. [B6]
- Sync hashes time, title, and badges and preserves edited spans. A warning inserted into the title becomes entangled with edit protection unless separately parsed. [B7]
- Note internals print directly and can sync after each save. Extract structured results for embedding in the loop. Pass the real account into previews: today's note preview constructs `DaySnapshot.account` from `calendar_id`; new account-keyed review lookups must not inherit that assignment. [B2]
- Unknown `gcal.*` kinds count as malformed. New `gcal.ack` records require reader/doctor updates and a multi-host upgrade order. [B8]

These are source observations, not claims of live reproductions.

**Define external precisely.**

Google's organizer is the calendar containing the main event copy. `organizer.self` describes the organizer calendar's relationship to the copy being read; it is not proof that the authenticated human owns the event. A shared calendar can therefore expose `self: true` for an event Bryan does not own. [Google: Calendars and events](https://developers.google.com/workspace/calendar/api/concepts/events-calendars), [Google: Events resource](https://developers.google.com/workspace/calendar/api/v3/reference/events).

Use a pure classifier returning `owned`, `external`, or `unknown`, plus a reason:

1. Organizer email matches the resolved account or an explicitly configured identity alias: owned.
2. Organizer email identifies a fetched calendar with access role `owner`: owned, including a copy of an event organized on Bryan's own secondary calendar.
3. Organizer is self for the current calendar and that calendar's access role is `owner`: owned.
4. An identified organizer is outside those identities/calendars: external. Reader/writer access to its calendar does not exempt it.
5. Organizer or ownership evidence is missing: unknown. Include it conservatively in review, labelled “Organizer unknown.”

Google exposes calendar access roles; Bob already loads them. `writer` and `owner` must remain distinct. [Google: Events.list](https://developers.google.com/workspace/calendar/api/v3/reference/events/list), [B4]

Case-fold identity emails for comparison, but do not invent Gmail dot/plus equivalences or infer identity from display names. Creator-based exemption is also wrong for this policy: creating on another calendar and currently organizing are different. A small explicit `gcal.owned_organizers` configuration can cover verified aliases/unlisted owned calendars if necessary, never every writable calendar by default.

This interpretation exempts events organized on Bryan-owned calendars even if a collaborator created them. “Created by any other human, including on my calendars” would require creator data and a different policy. Organizing-calendar authority better matches the existing private-note motivation.

**Acknowledgment is evidence of a review gesture.**

Use private notes' account/calendar/event identity family. Source of truth belongs in the synced journal, not task tags, checkboxes, priorities, Google properties, local caches, or daily-note paths. Moving a meeting must not erase acknowledgment.

Google event IDs distinguish recurring instances; `iCalUID` is shared across their series. Preserve `recurringEventId` and `originalStartTime` for identity/diagnostics: a moved instance keeps its original occurrence identity. Never key by current start time or just `iCalUID`. [Google: Events resource](https://developers.google.com/workspace/calendar/api/v3/reference/events), [Google: Recurring events](https://developers.google.com/workspace/calendar/api/guides/recurringevents).

Proposed semantics:

```text
review_evidence(event) =
    an explicit receipt for this account + calendar + event
    OR a valid persisted nonempty event-note record for that identity
    OR a valid persisted nonempty series-note record for its series

needs_review(event) = task_capable(event)
                     AND ownership(event) != owned
                     AND NOT review_evidence(event)
```

Explicit Ack applies to **this occurrence only**. Do not add bulk “ack all” or “ack every future recurrence” in V1. Deliberate all-events notes already offer a stronger series workflow. The scope UI should say that an all-events note also acknowledges the series; never choose that scope silently.

I recommend acknowledgment remain after clearing a note. Deleting travel instructions does not undo the review. Avoid fragile double writes: while reading valid journal records, accumulate acknowledgment evidence from all nonempty `gcal.note` records separately from the existing last-writer-wins fold of current note text. An empty clear contributes no new evidence and erases none. Existing notes therefore qualify on upgrade without rewriting them. A note still counts when it produces no visible bullet or its route later becomes unavailable.

The consequence is deliberate: a series that has ever received a valid series note remains acknowledged after clearing it, including future instances. Explain this. The coherent alternative is “only a currently nonempty note counts,” where clearing reopens review. Do not let a fold implementation accidentally choose the product rule. Historical gesture semantics best match “has added a note.”

Proposed explicit receipt, not a current schema:

```json
{
  "v": 1,
  "kind": "gcal.ack",
  "ts": "2026-11-12T09:00:00-05:00",
  "host": "mac",
  "account": "you@example.com",
  "key": {"calendar_id": "primary", "event_id": "opaque-instance-id"},
  "seen": {
    "title": "Project check-in",
    "start": "2026-11-13T10:00:00-05:00",
    "original_start": "2026-11-13T10:00:00-05:00"
  }
}
```

`seen` supports display/repair, never identity transfer. Duplicate receipts across hosts are harmless: positive acknowledgment evidence merges by union, not timestamp competition. Repeated explicit Ack ordinarily appends nothing. Current note text still uses its existing fold. Do not overload `gcal.flag`, which deduplicates day-specific lifecycle notices.

Keep the existing configured-calendar key convention. Resolve `primary` and the real primary ID as equivalent only within the same account when matching legacy records; deduplicate that alias pair on fetch. Implement any identity normalization in a helper shared with notes. Do not merge arbitrary calendar copies by title or `iCalUID`.

Failed validation, a new empty note, cancelled editor, dry run, and unreadable records create no evidence. An identical successful note save already qualifies through its prior record. A saved note still qualifies when immediate task synchronization fails. A read error must be distinguishable from healthy storage containing no evidence.

**Changes after review.**

V1 acknowledgment survives renaming/rescheduling of the same identity. A replacement event or split series with a new identity needs its own evidence. This keeps the command small and avoids churn, but a meeting can move after review and still be acknowledged. Say plainly: “Ack records that you reviewed this event; it does not approve later changes.” Existing sync continues updating eligible spans.

If the actual need becomes approving current time/location, add a separate **Changed since review** state with versioned semantic snapshots of meaningful time, location, organizer, and description changes. Compare normalized content rather than transport versions. Specify series exceptions first. I would defer that approval workflow, rather than silently invalidating note-based acknowledgment in V1.

**A terminal interaction worth using weekly.**

Proposed commands:

```text
bob gcal ack                     # next 7 dates, today included
bob gcal ack -n 1                # today
bob gcal ack -n 7 -l             # read-only pending queue
bob gcal ack -n 7 -l -f json     # structured pending queue
bob gcal ack -i EVENT -C CAL      # explicitly acknowledge one occurrence
```

Include short/long pairs for `--bob-dir`, `--format`, `--help`, `--event-id`, `--calendar`, `--list`, and `--next-n-days`, following existing spellings and alphabetical help. Exact-ID mode is an explicit mutation, requiring unambiguous lookup; it also resolves old task warnings outside the review window. Reject incompatible range/selection modes instead of ignoring flags. Bare `bob gcal` remains read-only list.

Illustrative screen, using fictional data:

```text
Calendar review · Nov 12–18 · America/New_York
3 events need your attention

1 of 3  ·  Fri Nov 13  ·  10:00–10:30
Project check-in
Alex Rivera · Work calendar · RSVP Yes

● job    MEET    10:00–10:30    No travel buffer
Agenda: review the handoff checklist

[a] Ack    [n] Note    [s] Skip    [q] Quit
```

Reuse root hues, a bold title, and the existing occupied-time rail where useful. Use amber for pending review, words as well as glyphs, and a layout that survives narrow terminals and disabled color. Organizer/calendar disambiguate similar titles. Escape control characters in provider text. Truncate long descriptions explicitly and show the Calendar link instead of burying the action row under an email invitation. A normal scrollback transcript is sufficient; a full-screen dashboard is unnecessary.

- **a:** persist, show `✓ Acknowledged`, advance. No Enter and no second confirmation.
- **n:** run the existing note workflow for the selected identity. Accept the same grammar and argument tail: `@route`, `#off`, `-30 Drive there`, `--` for prose, `-e` for the editor. Never shell-evaluate input or invent a second description parser.
- **s:** defer for this run only; it appears next time.
- **q / Escape / EOF / Ctrl-C:** stop, retaining completed actions and reporting remaining work. Do not acknowledge the current item.

Note entry omits QUERY because selection is fixed. Parse the tail as the note command would, preserve preview/validation/save behavior, and explicitly resolve event versus series scope. Empty/cancelled input returns to the current item; validation errors retain the draft. In the queue, a new note normally has nothing to replace because previously noted events are already excluded.

Keep bare Return inert. Handle held keys/repeats and buffered input so holding `a` cannot sweep the queue unnoticed. Restore terminal state before editor launch and every exit. These requirements need PTY tests, not only mocked line input.

After a series-note save, recompute pending items so covered occurrences disappear. Persist each action, not at a final “Save all?” step. A summary can say:

```text
✓ 2 acknowledged · 1 with a note · 1 skipped
1 still needs review · run bob gcal ack -n 7
Today's note updated
```

Those counts are disjoint actions. Report additional series-covered occurrences separately rather than implying each was individually viewed.

**Range, completeness, and unattended behavior.**

Capture Bob's local date and timezone once, honoring its clock override. Window: `[midnight today, midnight today + N)`, positive N with checked date arithmetic. Fetch once per configured calendar, expand recurring instances, drain every page, then build the complete queue before the first mutation. Failure of one calendar or a malformed snapshot is not “nothing to review.”

Google's lower time bound filters event end and the upper bound filters start. Pages may contain fewer than the requested maximum while another page remains. Apply Bob's local-start-day ownership after fetching so an overnight event beginning yesterday does not enter today's queue solely by overlap. Verify recurring expansion in the gog adapter contract. [Google: Events.list](https://developers.google.com/workspace/calendar/api/v3/reference/events/list), [B4]

Include earlier meetings from today, because today is explicitly included and Bob can create ended tasks. Exclude prior days from the default queue; use exact identity or private notes to resolve older warnings. Never pre-create future daily notes.

Off a TTY, refuse interactive review with `-l -f json` or exact-ID guidance. Piped `a` characters must not authorize range mutation. JSON stdout must contain only structured output. Give ack its own versioned response with window, identity, ownership reason, review basis, remaining count, completion flag, and persistence/application statuses. Add only compatible review summaries to existing list/sync output; private note text stays out of those responses.

Proposed exits: 0 for successful completion, listing, or voluntary stop with explicit `complete: false`; 1 for transport/persistence failures; 2 for usage/setup/TTY problems; normal interrupt status for Ctrl-C. Skips are pending work, not operational failure. Successful `gcal sync` stays successful when it merely finds unacknowledged events.

The queue is a snapshot, not a Google transaction. Recheck local journal evidence before saving to skip concurrent reviews. Do not hold a vault lock while waiting for input/editor. A cancelled event can disappear on the next run; actions always address the displayed identity, never whichever event later occupies its time slot.

**A warning that can clear on an edited task.**

Recommended Markdown:

```markdown
- [*] #task **1000-1030** **⚠ UNACKED** Project check-in [📅](GOOGLE_URL) [root:: job] ^event-id
```

After Ack/Note, remove only the marker. Preserve checkbox, block ID, edited title/root, children, completion, and ledger links. Keep the time span first in the description for Event Task recognition.

This is stronger than a log message, visible with children folded, and readable without plugins. Avoid a large callout per task, new task status, priority changes, or `#unacked` tags leaking into queries. One CLI summary supplies the action: `⚠ 2 external events need review · bob gcal ack -n 7`.

Make the marker a **separate Bob-managed span**, parsed before Google title hashes are computed. It is derived status, not meeting prose. Changing it must not produce `kept_edit`, reset title ownership, or affect task/ledger behavior. Update render, parse/rebuild, adoption, reset, cancellation, reordering, and preview paths together. Recognize it only at its designated position on identity-backed synced rows, never remove matching prose globally.

This is an explicit small addition to ownership policy: Bob controls the marker even on an otherwise edited row. Removing just the marker does not acknowledge; next successful sync restores it. Deleting the entire row or replacing Events still follows tombstone/hold rules. Hand-written Event Tasks without Google identity get no invented ownership classification. `description: off` does not suppress review markers.

Reconcile markers on extant rows of dates being explicitly synced, including pre-feature rows and newly born closed tasks. Do not automatically sweep old daily notes just to add warnings. Closing a task and acknowledging an event remain independent. Do not duplicate warning text into ledger links; optional UI badges should derive from the source/typed status.

Unreadable acknowledgment storage means `⚠ REVIEW UNKNOWN`, with diagnostics, rather than falsely claiming reviewed or unreviewed. Respect existing malformed-private-note holds. Healthy storage with no evidence means unacknowledged.

**Reliability and rollout.**

Reuse per-host append and vault-sync tracking. Save the gesture first, apply row changes separately. On the writer host, refresh affected existing rendered days once per session or safe stopping point, rather than fetching/syncing the day for every Ack. Elsewhere say “Saved; warning clears after vault sync and Calendar sync on <writer>.” On apply failure say “Saved; row update failed,” with recovery guidance; never roll back the receipt. A crash after append recovers through normal sync.

The shared append helper currently writes without explicit `fsync`. Follow existing guarantees and do not claim power-loss-proof persistence. Stronger durability, if required, belongs in a separately tested common journal improvement. [B9]

Update `load_state`, note readers, `malformed_count`, doctor, and resets for `gcal.ack`. Receipts must not advance lifecycle `newest` or make a future date appear synced. Forced resets preserve receipts and historical note evidence. Do not silently prune old series evidence affecting future instances.

Upgrade the designated writer and other journal readers before enabling receipts across hosts. Old binaries otherwise classify the new kind as malformed and may mishandle the visual span. Existing Mac note entry should automatically acknowledge through `bob gcal note`; the Mac must not independently infer/write state. Test additive JSON with consumers; a richer Mac review UI can wait. [B1, B8]

**The weekly reminder.**

At rollout, inspect the live `~/bob/gtd_daily.md` using supported vault access, check for an equivalent reminder, and insert one task near terminal review chores, preserving local conventions. If it belongs in PRE:

```markdown
- [ ] #task #gtd #pre #terminal Review external calendar events: `bob gcal ack -n 7` [repeat:: every week when done] [scheduled:: YYYY-MM-DD]
```

Use an actual first review date, preferably deployment day. `when done` matches checklist recurrence rules and avoids accumulating missed weekly occurrences. It drifts when completed late; that is reasonable for a catch-up review. A fixed weekday can be chosen deliberately if desired, rather than assuming Monday.

Outside PRE/POST, use an ordinary dated recurring task without those checklist tags. It enters RECURRING when due; PRE members remain PRE. An undated recurrence warns `recurring_undated` and does not walk. Do not add freshness stamps, a daily task, or a cron job. [B10]

Complete the reminder manually. `ack` should not automatically close a personal checklist item: the user may have quit or skipped events, and binding a generic command to one note is brittle.

**Implementation shape and acceptance evidence.**

| Area | Work |
| --- | --- |
| `model.rs`, `gog.rs`, selection helper | Organizer identity, ownership classifier, task-capable occurrences without series collapse |
| `journal.rs` | Receipts, note-history evidence, account/alias/reset semantics, diagnostics |
| New `gcal/ack.rs`, `cli.rs`, `mod.rs` | Range/list/exact-ID modes, terminal interaction, structured results, help/completion |
| `note.rs`, `note/write.rs` | Reusable note service/argument tail, fixed identity, real account in previews, scope explanation |
| `snapshot.rs`, `sync.rs`, `plan.rs` | One review status across consumers; batched application to existing days |
| `render.rs`, `lifecycle.rs` | Independent review span and migration/adoption of pre-feature rows |
| `list.rs`, `doctor.rs`, docs/fixtures | Visible status, remediation, JSON and behavior contracts |
| Vault launch step | One dated weekly reminder after the command is deployed |

Acceptance tests should demonstrate:

1. Ownership for primary/secondary, guest, shared reader/writer with `self: true`, aliases, missing organizer, and no attendees.
2. Today-inclusive ranges, DST transitions, overnight/start-day ownership, ended-today events, recurring expansion, every page, invalid N, and zero writes on initial snapshot failure.
3. Receipt idempotency; isolation between accounts/calendars; moved-instance stability; no accidental inheritance by another occurrence.
4. Event/series notes from every entry point, adoption, pre-feature history, clearing, identical save, cancellation, empty input, invalid input, dry run, and coverage refresh inside the queue.
5. Marker-only removal on tasks with edited title/root/children/status; repeat sync byte stability; no false `kept_edit` or accounting changes.
6. Tombstones, replaced Events, Templater waits, forced resets, born-closed tasks, description-off, and malformed journals.
7. Saved gesture plus apply failure; remote-host delay; concurrent union merges; no interactive lock held.
8. Real PTY single-key input, inert Return, held/repeated key protection, editor transitions, cancellation, restored terminal state, and non-TTY refusal.
9. Deterministic JSON and previews, no private-note leakage, and preview of post-save acknowledgment without dry-run writes.
10. A unique, dated reminder in the right review tier and correct next recurrence after completion.

Use the existing fake-gog and lifecycle test families; no real Google writes are necessary. Run required code/docs checks during implementation. The highest-risk work is ownership-preserving marker reconciliation, not appending a receipt.

**Evidence map.**

Links pin the inspected revision; these are local source observations, not other research reports.

| Ref | Source |
| --- | --- |
| B1 | [Private event notes contract](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/docs/gcal-notes.md): model, storage, reliability, command, application |
| B2 | [Note write/preview implementation](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/src/native/gcal/note/write.rs): `write_one`, `append`, `apply_if_possible`, `preview` |
| B3 | [Calendar contract](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/docs/gcal.md) and [inclusion classifier](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/src/native/gcal/classify.rs#L129) |
| B4 | [gog adapter](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/src/native/gcal/gog.rs#L85) and [batched snapshots](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/src/native/gcal/snapshot.rs#L90) |
| B5 | [Event model, parser and RSVP helper](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/src/native/gcal/model.rs): `GcalEvent`, `from_google`, `my_answer`, `RawOrganizer` |
| B6 | [Note argv, eligibility, grouping and prompts](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/src/native/gcal/note.rs): `rewrite_gcal_argv`, `is_eligible`, `group_candidates` |
| B7 | [Row rendering](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/src/native/gcal/render.rs#L57), [span parsing](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/src/native/gcal/lifecycle.rs#L105), [reconciliation](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/src/native/gcal/plan.rs#L1031) |
| B8 | [Calendar journal](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/src/native/gcal/journal.rs): `load_notes`, `append_note`, `malformed_count` |
| B9 | [Shared append primitive](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/src/native/pref_journal/mod.rs#L104) |
| B10 | [Recurring review cases](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/docs/freshness.md#L1269), [recurrence/checklist constraint](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/docs/date-marks.md#L215) |
| B11 | [Note CLI tests](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/tests/gcal_note_cli.rs), [sync tests](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/tests/gcal_sync.rs), [lifecycle tests](https://github.com/bobs-org/bob-cli/blob/4f7ab37f6180a84309e5f06e674a0f3afce5c135/tests/gcal_lifecycle.rs) |

Audited memory consulted: `cli_rules.md`, `docs.md`, `sase_artifacts.md`, `obsidian.md`, `decisions:bob-gcal-is-read-only-and-proposes-once`, `decisions:private-event-notes-beat-google-per-field`, `decisions:gcal-force-resets-the-day`, `decisions:recurring-occurrences-walk-when-due`, and `glossary:Event Task`. These support the read-only Google boundary, note semantics, reset/hold behavior, and reminder design.

**Recommended solution.**

Ship `bob gcal ack -n 7` as an occurrence-by-occurrence review inbox with genuine one-key Ack/Note/Skip/Quit, existing private-note grammar, and per-action persistence. Reuse the synced Calendar journal; saved event notes acknowledge their event and deliberate series notes acknowledge their series. Keep acknowledgment after clearing notes and ordinary organizer edits, documenting that it records a review gesture rather than approval of the latest version. Classify ownership conservatively and review only task-capable events.

Continue creating otherwise eligible Event Tasks. Give unacknowledged ones one bold `⚠ UNACKED` marker with ownership independent of meeting text, clearing through normal writer-host reconciliation. Install the dated weekly reminder when the command is deployed. Defer bulk acknowledgment, automatic re-review on changes, a new GUI, and Google writes until actual use establishes a need. The first release should make pending preparation obvious and resolving it quick without turning Calendar synchronization into another approval system.
