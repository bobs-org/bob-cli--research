# Private event metadata: a compact guide grounded in bob-cli-ji

Researcher: **cdx** · Investigated: **2026-11-10** · Scope: independent research and a proposed user guide, not implementation.

## Recommendation

Write one short, example-led guide at the epic's intended `docs/guides/plan-events-you-dont-own.md`. Keep the title **“Plan an event you don't own”**, and introduce **private event note** in the opening sentence. This gives readers their practical goal and the product's actual name for the feature. It also avoids implying that “private event tasks” are a new task kind or Google visibility setting.

Lead with the Mac's dedicated **Event note** mode, show one five-line recipe, and explain its result with a labeled time rail. Offer a compact terminal alternative using the same example. Finish with saving versus applying, recurring scope, and editing or clearing. Target roughly **700–900 words**, comfortably below the repository's 1,500-word guide target and 2,500-word hard cap. Keep journal storage, JSON schemas, and precedence internals in `docs/gcal-notes.md`. [S1, S3, S6]

**Publication qualification:** the workflow below is the approved destination, not a claim that the inspected builds support it today. Do not publish its command or shortcut instructions as available until the corresponding phases have landed and been verified.

## What exists, and what is still approved work

The audited epic read showed phases **ji.1** and **ji.3** closed; **ji.2, ji.4, ji.5, ji.6, and ji.7** were in progress. Its accepted choices are **automatic sync on the writer**, **⌘E from any draft state**, a decision record, and **no new glossary entry**. The research does not alter those choices. [S1]

| Area | Evidence at inspection | Consequence for the guide |
| --- | --- | --- |
| Layering and persistence | Present at bob-cli `7ff24c8241b1fefbed57906f5486367e3f86e14d`; `tests/gcal_notes.rs` covers note-created rows, layering, clears, RSVP, moves, ownership, and malformed records. | Explain these as implemented engine behavior. |
| User-facing CLI | This checkout's `src/native/gcal/cli.rs` has no `note` subcommand. | Syntax below comes from the approved plan; it was not executable here. |
| Existing note documentation | `docs/gcal-notes.md` explicitly says command write, preview, and Mac mode land later. | Treat it as the current engine contract, not a complete how-to. |
| Mac interface | Opened linked checkout at `af604c6d9e05ec6440bfce5fa15ced97e388035c`; no Event note command or page found in its source/docs. | Shortcut, scope control, save keys, and preview come from the approved Mac design. |
| Release availability | Not established by these checkout observations. | Do not invent a minimum version or say “available now.” |

## Proposed user-facing guide

*Editorial boundary: the following draft is for publication after the feature lands. “Family” and the event are illustrative; substitute an existing route and a real event. Links use the existing published documentation URLs.*

### Plan an event you don't own

Add travel time, an area or project, and reminders with a **private event note**. Bob stores it in your vault and applies it to the event's task when that day syncs—even if the organizer won't let you edit the invitation. The note is never sent to Google or the other guests.

Start with [Google Calendar connected to Bob](https://bobs-org.github.io/guides/connect-google-calendar/). RSVP in Google as usual. You can also save a note before replying or before the day's daily note exists.

#### 1. Pick the event

Open Bob Mac Capture and press **⌘E**, or choose **Event Note…** from its menu. Your capture draft stays available when you return.

Search for the event, check its **date, time, organizer, and RSVP**, then press **Return** to open it. For a recurring invitation, choose **This event** for that occurrence or **All events** for the series.

#### 2. Add what you need

For a 10:00–12:00 breakfast, enter:

```text
@family
#off
-30 Drive there
+15 Drive home
Bring the tickets
```

Use **Shift+Return** for a new line. Replace `@family` with an existing area or root-project route in your vault.

| Write | Bob uses it for |
| --- | --- |
| `@family` | Attribute the event to Family. |
| `#off` | Record the time off-clock, outside Worked totals. Use `#on` to force on-clock. |
| `-30 Drive there` | Reserve 30 minutes **before**; keep the reason under the task. |
| `+15 Drive home` | Reserve 15 minutes **after**; keep the reason under the task. |
| `Bring the tickets` | Add a reminder bullet under the task. |

Use only the lines you need. Check the signs: `-` means before and `+` means after, whatever the reason says.

#### 3. Check the preview, then save

The time rail should show:

```text
09:30      10:00                         12:00   12:15
|  BEFORE  |========== MEETING ==========| AFTER |
  Drive there                            Drive home
```

**Meeting: 10:00–12:00 · Occupied in Bob: 09:30–12:15**

The **Lands as** preview shows the resulting task and its bullets. The meeting time stays 10:00–12:00; the buffers reserve extra time in Bob without changing Google's event or availability.

Press **Return** to save, and read the result:

| Result | What it means |
| --- | --- |
| Applied to the daily note | Bob synced the affected day on the configured writer. |
| Lands when that day syncs | The note is saved; Bob will apply it when the daily note exists and sync runs. |
| Waiting for your reply / Yes | The note is saved, but the invitation is not yet eligible for an Event Task. Maybe normally waits too, unless configured as a task. |
| Saved; updates on the writer's next sync | A different machine saved it; the writer applies it after vault sync transfers the note. |

If a save reports a sync failure, the note is still saved. Retry `bob gcal sync` on the writer for today, or add `-D YYYY-MM-DD` for another existing day.

#### From a terminal or SSH

Preview a new note without saving:

```bash
bob gcal note -s event -d deerwood -- '@family #off -30 Drive there +15 Drive home; Bring the tickets'
```

Check the selected event, then run the same command without `-d` to save it:

```bash
bob gcal note -s event deerwood -- '@family #off -30 Drive there +15 Drive home; Bring the tickets'
```

Keep the note text quoted. `--` separates it from the event query. `-s event` chooses one occurrence; use `-s series` only when you intend the whole recurring series. Add `-D YYYY-MM-DD` before the query to target a particular day.

#### Check, change, or remove it

```bash
bob gcal note -s event deerwood
bob gcal note -s event -e deerwood
bob gcal note -s event -c deerwood
```

These show, edit, and clear the selected note. In the Mac editor, **⌘⌫** clears it. Clearing reveals any series note and the usual calendar rules; it does not delete the event. Use `bob gcal note` to list your notes and `bob gcal list -D YYYY-MM-DD` to inspect that day's calendar projection.

For fields you set, **This event** overrides **All events**, which overrides Google. Unset fields keep their usual values; reminder prose combines. Use `-0` or `+0` to explicitly remove an inherited buffer on that side.

If you've edited the task itself, Bob preserves those edits; a saved note may not change that part of the row. See [Private event notes](https://bobs-org.github.io/gcal-notes/) for ownership and troubleshooting.

Already put Bob directives in a guest invitation's Google description? `bob gcal note -A deerwood` copies its directives and buffer reasons into Bob; prose stays in Google. Choose the recurring scope when prompted. From a phone, a configured `gcal.colors` mapping can supply routing by recoloring the event; buffers and reminders still need a private note.

*End of guide draft.*

## Accuracy details the editor must preserve

1. **Private describes storage, not the event's Google visibility.** The note lives in the vault's existing gcal journal and shares the vault's access and sync boundaries; do not call it encrypted, device-only, or an organizer-visible RSVP comment. Google's `visibility: private` is a separate event property. Bob's read-only grant cannot mutate Calendar. [S2, S3; Google's [scope reference](https://developers.google.com/workspace/calendar/api/auth) and [event resource](https://developers.google.com/workspace/calendar/api/v3/reference/events)]
2. **“Any event” needs an eligibility qualifier.** The plan's broad promise means owned and guest events, including unanswered/Maybe invitations. Its selector explicitly targets timed, busy, under-24-hour `default`/`fromGmail` events, excluding all-day, free, cancelled, declined, and multi-day events. Avoid promising that every Google item can become a task. The note itself never RSVPs or forces inclusion. [S2, “Selecting the event”; S4, `awaiting_reply_note_waits_applies_on_yes_and_skips_declined`]
3. **Each field layers independently; prose is additive.** An occurrence containing only `-0` clears its before buffer while still inheriting the series root and after buffer. A side's reason travels with the winning numeric value; setting a bare value drops the lower layer's reason. Clearing an occurrence can reveal a series note, so “Google decides again” is too absolute. [S3; S4, `occurrence_beats_series_beats_google_per_field`; S5]
4. **Text writes replace the selected note.** A second write is not a patch to whichever fields happen to appear in its text. Teach the editor for revisions so a user does not accidentally remove an existing private route while adding a buffer. Explicit zero disables inheritance; omitting a field allows inheritance. [S2, storage fold and “Saving”]
5. **Saved and applied are separate outcomes.** On the writer, auto-sync is selected for affected existing, rendered days. Off-writer writes wait for vault transfer and writer sync. A sync failure after a successful save remains a saved note and exits successfully with a warning; exit 0 alone does not prove the daily row changed. [S1; S2, “Saved versus applied”]
6. **Manual edits have wider effects in v1.** Editing the row's time, title, or badges can prevent later private buffer/clock updates because these share a single ownership hash. A manually edited root wins independently, and edited/nested/deleted imported bullets can prevent new note prose from appearing. Keep one plain-language warning in the guide and explain the full scope in the reference. Do not recommend `sync -F` as a routine repair: it deliberately resets broader day state and does not remove private notes. [S2, “Ownership in the row”; S3; S4, `row_edited_root_is_kept_and_reported_once`, `force_reset_keeps_and_reapplies_notes`]
7. **Entry grammar is stricter than the raw engine contract.** The planned write path rejects conflicting routes, both clock tags, differing values on the same side, values outside 0–720, and canonical text over 2,048 bytes. A reason requires a positive value. Existing raw description parsing has first-value/on-wins rules; do not teach those as a workaround for invalid note input. Put directives before reasons or on separate lines because `@` and `#` inside reasons are prose. [S2, normalization/validation; S3]
8. **The shown projection needs a real fixture before publication.** The epic's illustrative CLI output uses `[ ]`, while current sync documentation creates future/current linked rows as `[*]`; type fields are conditional. Avoid copying that sample as byte-exact output. The proposed draft intentionally uses a conceptual rail, not a fabricated task screenshot. [S2, human output; S3; S5, `render_task_row`]
9. **Selection is not an unlimited title search.** The normal window is the next 90 days. `-D` selects a day; an exact event ID or suitable Google URL can reach outside the window. Repeated titles require disambiguation; recurring noninteractive calls need `-s`, and exact IDs can also require `-C` if present in multiple calendars. These belong in a linked “Can't find the event?” reference, not the main recipe. [S2, selection]
10. **Missing bullets can be configuration, not lost metadata.** `gcal.description: off` hides private reasons/prose too, while root, clock, and buffer directives still apply. Private prose is exempt from Google's copied-description line cap. [S3; S4, `note_prose_is_exempt_from_the_cap_and_off_hides_bullets`]

## Visual treatment and publication checks

Use one worked example consistently: the same title, date, route, meeting, and reasons in picker, text, preview, and result. The rail answers one question: **“Which time did I reserve?”** Show solid meeting time and hatched buffer wings in a future screenshot, with explicit start/end labels and the text equivalents **Meeting** and **Occupied**. The draft's text rail is an intentionally schematic, portable fallback; it is not a screenshot or measured scale.

Once the Mac phase has a real render fixture, place one cropped editor/preview image next to or immediately after the five-line recipe. Suggested alt text: “Breakfast from 10:00 to 12:00, with 30 minutes to drive there and 15 minutes to drive home; occupied time is 09:30–12:15.” Preserve legibility in light and dark themes, narrow layouts, and without color. Use existing task-fence styling only after confirming it represents the relevant event metadata accurately. No generated application screenshot is needed. [S2, Mac preview; S6]

Before publishing, verify the final CLI help and a fake-calendar preview/save/show/clear cycle; check one recurring override, one unanswered invitation, one missing daily note, an off-writer save, and a preserved manual edit. Confirm the shipped Mac chord and Return/Shift+Return/Clear behavior. Derive any output image from the verified fixture. Add the page to the guide index and navigation, cross-link the contract, and run the required `just docs-check`. These are publication checks, not verification already performed by this research.

This investigation inspected source and existing tests but did **not** execute the Rust suite, invoke unfinished note commands, mutate a real vault, or change Google Calendar. No swarm peer reports, transcripts, or findings were consulted. Only this research deliverable is being added.

## Evidence register

- **S1 — Audited epic:** `sase bead read bob-cli-ji -r …`, including status, children, and accepted reviewer choices. [Epic page](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-ji/README.md). Status is an observation at inspection, not a claim about subsequent landings.
- **S2 — Approved design:** `plan:202611/private_gcal_event_notes.md`, read through `sase artifact read`; especially “Command shape,” “Selecting the event,” “Normalization,” “Validation,” “Preview, save, clear,” “Ownership in the row,” and the records/Mac phases. Branch choices come from S1.
- **S3 — Current contracts:** [Private event notes](https://github.com/bobs-org/bob-cli/blob/7ff24c8241b1fefbed57906f5486367e3f86e14d/docs/gcal-notes.md), [Bob Gcal](https://github.com/bobs-org/bob-cli/blob/7ff24c8241b1fefbed57906f5486367e3f86e14d/docs/gcal.md). Read locally at the pinned SHA; the latter's older “description you cannot edit” known limit remains transitional and must not override the new engine contract.
- **S4 — Existing integration evidence:** [tests/gcal_notes.rs](https://github.com/bobs-org/bob-cli/blob/7ff24c8241b1fefbed57906f5486367e3f86e14d/tests/gcal_notes.rs). Test assertions were inspected, not run.
- **S5 — Implementation:** [model.rs](https://github.com/bobs-org/bob-cli/blob/7ff24c8241b1fefbed57906f5486367e3f86e14d/src/native/gcal/model.rs), [render.rs](https://github.com/bobs-org/bob-cli/blob/7ff24c8241b1fefbed57906f5486367e3f86e14d/src/native/gcal/render.rs), [cli.rs](https://github.com/bobs-org/bob-cli/blob/7ff24c8241b1fefbed57906f5486367e3f86e14d/src/native/gcal/cli.rs), plus journal/description/planner source inspected locally.
- **S6 — Documentation conventions:** audited `docs.md` memory; [how-to template](https://github.com/bobs-org/bob-cli/blob/7ff24c8241b1fefbed57906f5486367e3f86e14d/docs/_templates/how-to.md), [lint budgets](https://github.com/bobs-org/bob-cli/blob/7ff24c8241b1fefbed57906f5486367e3f86e14d/tools/docs/bob_docs/lint.py), [task fence](https://github.com/bobs-org/bob-cli/blob/7ff24c8241b1fefbed57906f5486367e3f86e14d/tools/docs/bob_docs/fences.py), and `mkdocs.yml`.
- **S7 — Mac baseline:** linked `bob-mac-capture` checkout, opened through `sase repo open`; `AGENTS.md`, documentation filenames, source search, and HEAD `af604c6d9e05ec6440bfce5fa15ced97e388035c`. The requested Event note surface is specified by S2; it was absent from this inspected baseline.
