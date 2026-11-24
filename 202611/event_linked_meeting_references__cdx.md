# Meeting notes that belong to the meeting

Independent research and design recommendation · researcher **cdx** · 2026-11-24

## Decision in brief

**Build this. Make it an event-centered filing and editing experience, with AI helping produce a useful brief.** The important result is a trustworthy reference that is easy to find again from the meeting and its area/project. Generating another summary alone will not deliver that result.

My recommendation is **Add meeting notes… → inspect one editable preview → Save & link**. Start from an Event Task whenever possible, inherit its valid `[root::]`, retain the exact imported source, and put a concise, editable brief in a normal ref note. Keep proposed follow-up tasks separate from saving the note. Begin with files and pasted text; add Wispr's official read-only MCP adapter after the core flow works.

For the supplied example, use `[[job]]`, link the exact `[[2026/20261123#^bryan-bugyi-derrick]]` occurrence, and title the reference **Yogi — Intro with Derrick Blakely · 2026-11-23**. The source is an already synthesized set of notes, not a verbatim transcript. This distinction must remain visible.

This is research, not an implementation or a production import. I inspected the supplied source, queried the live vault read-only, inspected relevant code and documentation, and checked current primary product documentation. I did not create the live reference, change the event, or consult any other report or researcher in this swarm.

## What the actual example establishes

The input `/home/bryan/tmp/bryan_derrick_meet_notes.txt` has 78 lines and 3,246 bytes. Its SHA-256 is `648521d3fe519f3e5c643ae9b5f905b41b96c234fd91eaa73289e2a81665bdfa`. It contains a lead summary, topical sections, and a final next step. There are no timestamped utterances or speaker turns. Calling this “imported meeting notes” is supported by its shape; identifying it specifically as an unedited Wispr-generated summary would require information the file does not contain.

The user supplies the Wispr provenance. The document says that the next interview stages are an AI-enabled coding exercise and an onsite, and that Derrick will email Bryan next steps. The body describes the exercise as an hour to 75 minutes; its opening says 75 minutes. It also contains the uncertain name “BOLI” and calls Bryan's project “Sassy.” These are excellent quality fixtures: a helpful system must not confidently replace either name, erase the duration range, or turn a possible future contribution into an accepted assignment.

A targeted `bob query` against the requested daily note returned:

| Property | Observed value |
| --- | --- |
| Event title | Bryan Bugyi and Derrick Blakely |
| Daily note | `2026/20261123.md` |
| Block ID | `bryan-bugyi-derrick` |
| Meeting span | `1500-1530` |
| Current task mark | `x`, completed |
| Root | `job` |
| Calendar provenance | Google Calendar event link is present |

The printed local span is evidence of the scheduled meeting, not the length of the recording or proof of attendance. The source contains no recording duration. The feature should obtain the timezone from Bob's configured/event context rather than the importing machine's UTC clock.

A second targeted query confirmed `job.md` is an area, and `job_2026.md` is a project beneath it. The existing references `yogi_derrick_question_playbook` and `yogi_senior_swe_product_intro_call_prep` are both filed under `job`. This corroborates the event's explicit root. It does **not** authorize inventing a Yogi project or moving existing notes. Offer `job_2026` as an ordinary destination choice; default to `job`.

I also tested the current installed binary (`bob 0.6.0`) with a read-only invocation:

```sh
bob ref create /home/bryan/tmp/bryan_derrick_meet_notes.txt -P job -t meetings -d
```

It exits 1: the target must be Markdown, PDF, or an HTTP(S) URL. Thus “just run ref create on the transcript” does not handle even this first input today.

## Is the idea worth building?

Yes. Bob already supplies the scarce context: a specific meeting occurrence, time attribution, area/project hierarchy, task navigation, and a reference library. Wispr supplies capture. Joining these produces a useful memory of a meeting without making the user choose filenames, remember link syntax, or reconstruct context weeks later.

The strongest use cases are interviews, substantive one-to-ones, customer calls, design discussions, and research conversations. Their useful output is usually a short brief plus evidence and next steps. Routine status calls do not automatically deserve another permanent note. Make creation deliberate and fast; do not import every calendar event by default.

There are four traps:

1. **Summary laundering.** A fluent second summary can make the first summary's mistakes look verified. Preserve source kind, uncertainty, and an inspectable source location.
2. **Administrative work disguised as automation.** Opening an extra reading task for every attended meeting can create more review work than the feature saves.
3. **Task ownership mistakes.** “Derrick will email Bryan” is Derrick's commitment. “Bryan might lead a migration” is an opportunity. Neither is automatically a task Bryan has accepted.
4. **A weak join behind a polished UI.** Matching a recurring meeting by title or displaying success before the ref exists makes the feature unreliable precisely when users stop checking it.

I would change the emphasis from “automatically transcribe meetings into refs” to **“turn selected meeting material into an excellent, correctly filed meeting reference.”** Bob should accept already good notes without forcing another model pass.

## What current products suggest

These are design precedents and documented capabilities, not comparative usability measurements.

| Primary source | Relevant finding | Implication for Bob |
| --- | --- | --- |
| [Wispr: sharing meeting notes](https://docs.wisprflow.ai/articles/5073796184-sharing-meeting-notes-from-notetaker-beta) | Whole-meeting Markdown export can include title, attendees, personal notes, summary, and timestamped transcript. Desktop transcript-only copy omits timestamps. | Support whole exports, summaries, and bare transcripts as distinct input shapes. Do not require timestamps or a particular clipboard format. |
| [Wispr: editor](https://docs.wisprflow.ai/articles/9406970664-meeting-notes-and-the-editor-in-notetaker-beta) | Personal notes, generated summary, and transcript are separate views. | Retain the distinction between the author's thinking, imported evidence, and generated prose. |
| [Wispr: remote MCP](https://docs.wisprflow.ai/articles/9551372685-connect-an-mcp-client-to-wispr-flow-remote-mcp-server) | Official access is read-only and covers meetings, notes, transcripts, and calendar associations. Authorization is account-wide. Long transcripts arrive in portions; search is not transcript full-text search. | A direct adapter is feasible later. It must fetch complete selected content, expose partial/unavailable sources, and retain file/paste fallback. Do not scrape app storage. |
| [Notion: AI meeting notes](https://www.notion.com/help/ai-meeting-notes) | Calendar-linked notes, meeting-specific summary instructions, and transcript citations coexist. Citations can reveal a snippet or jump to its source line. | Start from the event and make evidence available beside the brief, without forcing everyone into a raw-transcript view. |
| [Granola: product overview](https://docs.granola.ai/help-center/getting-started/granola-101) | A calendar event can create a meeting note; ad hoc notes also exist; templates shape the output. | The event is a useful entry point, but imported material must still work when metadata is absent. Use a restrained structure, not a large template picker. |

The HAX guidance treats initial expectations, ordinary interaction, errors, and evolving use as parts of one design. Bob's source labels, editable previews, recoverable failures, and preserved user edits are my application of that guidance, rather than features proven specifically by it. [Microsoft HAX Toolkit](https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/).

The useful competitive feature is not recording more audio. It is making the next useful action and the original context easy to retrieve.

## Proposed user experience

### Start at the event

Add **Add meeting notes…** to the Event Task's contextual actions and expose a named Obsidian command that works on the event itself or a Task Link resolving to it. Completed events must remain eligible; this example is already closed. Use **Open meeting notes** once a reference is attached, with **Add source…** in its secondary menu.

The initial complete release should ship the Bob backend plus the Obsidian entry point and sheet. That is the shortest path from an actual Event Task to an editable ref. A native Mac sheet can use the same contract later; its existing Event notes picker and Refs presentation offer useful components. Do not ship only a CLI and call the UX complete.

When entered without an event, show a recent-events picker with date, time, title, and root. Search historical dates as well as recent events. The first candidate is a suggestion, never an invisible write target. Prefer explicit identity from an integration over fuzzy title matching. If no event exists, keep the material as a draft until the user selects or creates the appropriate event through the existing workflow; a meeting import should not invent a calendar task.

### One sheet, progressive disclosure

The sheet has three clear regions: meeting identity, editable note, and destination/save controls. Start with a paste area and **Choose file…**. Pasting is an intentional action; opening the sheet must not silently consume the clipboard. Accept UTF-8 `.txt` and `.md`, and make malformed encoding, empty inputs, and oversized inputs explicit.

A classified summary opens immediately as editable notes with **Polish with AI** available. A transcript offers **Draft notes**. A whole export selects its existing summary as the starting brief and retains the other components as source. Classification is a suggested, editable label: **Notes**, **Transcript**, or **Full export**. For this input, Notes is the correct default.

The same sheet then shows a preview like this:

```text
Meeting notes                                           Source ▸
Yogi — Intro with Derrick Blakely
Mon 23 Nov · 15:00–15:30                 Linked event ↗

File under  [ Job ▾ ]                   From this event

Brief
Introductory interview covering Yogi's AI product work,
engineering practices, and the remaining interview stages.

Next steps
Derrick will email next steps. No date recorded.          [1]
Coding exercise: about 60–75 minutes, AI tools allowed.   [2]

Needs checking
The quality tool's name was captured as “BOLI.”           [3]

[ Edit notes ]     [ Polish with AI ]      [ More ▾ ]

Reviewed reference · no reading reminder
Cancel                                  [ Save & link ]
```

This is a layout specification, not a screenshot of implemented behavior. Source markers resolve to source paragraphs here; they must not imply transcript timestamps. The complete note can be longer than this first screen.

Keep the destination visible during editing. Explain its initial value with “From this event.” An explicit override changes reference filing only. Changing the event's root changes time attribution and remains a separate existing action. Do not write an override back into Google or learn a recurring-series rule from it.

### Save should be one clear commitment

**Save & link** publishes the reviewed brief, source, reading record, and reciprocal links. A persistent result says **Saved in Job · Linked to 23 Nov meeting**, with **Open notes** and a guarded undo action. A new ref opens at its brief, not an empty Highlights section or the first page of its source PDF.

The advanced reading choice is **Review later**. Default **Reviewed reference** is appropriate after the user has reviewed this brief and chosen to save it; it is not inferred from the event's completed mark. Review later creates the ordinary ready reading task. An AI-generated draft does not create a task while waiting for review.

A standard modern ref still requires one reading record. Saving a reviewed reference therefore creates a closed `#task #ref` record in the chosen parent, with its completion date equal to the review/import date. The meeting date is separate metadata. This is a compatibility tradeoff: it avoids an open backlog item but may add a Done/reading record to current statistics. Evaluate that behavior explicitly; do not silently exclude these tasks from metrics or backdate completion to the meeting. If users reject that cost, a taskless reference lifecycle is a separate design change, not a hidden exception in this importer.

Suggested actions appear as prose in the brief. A later explicit **Create task…** action can preview owner, destination, date, and duplicate candidates through Bob's existing capture machinery. In the first release, ordinary capture is enough. Saving a note never creates a bundle of inferred tasks or a Gmail reply watch.

### Make it beautiful by making the useful content dominant

Use the existing Bob card typography, spacing, and destination hue. One modest page glyph is enough. Avoid an AI sparkle beside every paragraph, dense status badges, and a large drop zone after the source has loaded. Let the event title, date, and content lead.

Use a comfortable reading measure, approximately 60–75 characters, with generous separation between a two-sentence brief, key points, next steps, and uncertainties. Only show populated sections. Use quiet numbered source markers; an amber label belongs on a specific unresolved claim, not on the entire document. Destination color must have a text label.

At wide sizes, Source opens a side-by-side inspector. At narrow sizes, it becomes a secondary pane and restores the editor's scroll position when closed. Citation activation should select the exact excerpt and allow returning to the same position. Use semantic headings, screen-reader labels, visible focus, dark/light themes, and reduced-motion behavior.

Enter inserts a newline in text; an explicit Save shortcut can be Cmd/Ctrl+Enter. Escape backs out one layer and preserves the local draft; `q` outside text controls and Ctrl+[ follow the same dispatch as required by Bob's panel convention. Never assign `q` to a new action. AI generation is cancellable, and reopening the sheet restores the draft. The UI shows stages such as Drafting, Ready to review, Saving, and Saved locally—never a fictional percentage.

## The actual reference I would produce

Proposed basename: `yogi_derrick_intro_20261123`, under `ref/meetings/`. Collision allocation still belongs to Bob; the importer must first look for an existing reference attached to this occurrence rather than suffixing on every retry.

The human content below is a worked example, grounded only in the supplied material. It intentionally avoids bringing current email state or outside company facts into a historical meeting record.

> **Yogi — Intro with Derrick Blakely · 2026-11-23**
>
> **Meeting:** [[2026/20261123#^bryan-bugyi-derrick|Bryan Bugyi and Derrick Blakely]] · 15:00–15:30  
> **Filed under:** [[job]]  
> **Source:** Imported Wispr meeting notes; no verbatim transcript supplied.
>
> ### Brief
>
> The introductory interview covered Yogi's AI product work, Bryan's engineering background, and how the team is adapting its development process around AI. The supplied notes describe the conversation positively and list an AI-enabled coding exercise and an onsite as the remaining interview stages.
>
> ### What matters for the role
>
> - Derrick described user-facing AI work including chat, agents, and vector search. Yogi's agents examine customer-feedback data on a schedule and aim to surface novel, consequential, actionable issues.
> - The discussion emphasized product value beyond running a general-purpose model: scale, persistence, auditability, enrichment, and an opinionated user experience.
> - Potential work included broader configurable agents, recurring reports, improved social-data experiences, and a possible migration from Prefect to Temporal. The notes say that migration had not started; they do not record an assignment to Bryan.
> - Bryan wants a team actively developing an AI-centered software process. The notes describe substantial Claude Code use at Yogi and review focused on production-bound changes.
>
> ### Interview process and next steps
>
> - Derrick said he would email next steps. No deadline is recorded.
> - The next coding exercise involves building a data-processing app with AI tools. The source describes roughly 60–75 minutes; the opening summary says 75 minutes. Confirm the precise format from the invitation.
> - An onsite follows the coding stage. No date is recorded here.
>
> ### Questions to clarify
>
> - Exact name of the code-quality tool, captured as “BOLI.”
> - Scope and ownership of the possible Prefect-to-Temporal migration.
> - Exact coding-round duration and evaluation criteria.
>
> ### Source details
>
> Open the preserved imported notes for the full company examples, Bryan's background, and the description of his project. The input calls that project “Sassy”; any correction should be recorded as Bryan's correction, with the imported source retained.

In the implementation, source markers should attach to these claims and jump to the relevant original section. A source reference here means “supported by these imported notes,” not “verified against the audio.” Questions inferred as useful follow-ups must be visibly identified as questions, not assertions that someone raised them in the meeting.

The event gains one ordinary child link, placed below the Google-owned description block:

```markdown
  - Meeting notes: [[ref/meetings/yogi_derrick_intro_20261123|Yogi — Intro with Derrick]]
```

The ref gains a `meeting_event` wikilink pointing at the exact block, plus machine-readable provenance described below. It retains the normal managed reading-task embed below the H1. The brief belongs in the author-owned body **outside** the managed Highlights region. The event's mark, clock span, root, buffers, calendar links, and Pomodoro history remain as they were.

## Storage and architecture: extend refs without rebuilding them

### Reuse the library, with an editable front door

A captured conversation already fits Bob's Reference Note definition. A `ref_type: meetings` folder provides a useful category without inventing a second note type. Modern reference parentage must continue to come from the reading task's residence; the meeting pointer is provenance, not a competing parent field.

For the first release, **reuse the existing PDF-backed ref pipeline for the preserved source**, while opening the editable Markdown brief by default from the event. The PDF is a readable snapshot of the imported source, not a second editable copy of the polished brief. Users should not need to understand Pandoc, choose a PDF path, or run a scan. This keeps Highlights, source retention, reading tasks, and reference lookup usable with modest extensions.

A text-native, PDF-optional ref is a reasonable long-term direction, but it is a broader change today: Bob Refs describes itself as PDF-backed and opens PDFs by default; source catalogs and reference birth are coupled to rendering. Do not introduce a legacy-shaped trackerless note as a shortcut. Reconsider text-native birth if a measured prototype shows source-PDF creation dominates latency or reliability. A renderer failure must preserve the draft and explain retry; it must not silently create a different ref format.

The new `meetings` kind would initially decode as `.other(raw:)` in the current Mac client. Add its proper label/icon and test filtering before advertising complete Mac support. Do not globally change Enter to open Markdown for all existing references; the event's notes link opens the brief, and the source remains separately available.

### Preserve three different things

| Layer | Ownership and behavior |
| --- | --- |
| Imported bytes | Immutable snapshot of the `.txt`, `.md`, or fetched payload. Preserve bytes, source kind, origin, full digest, capture time, and completeness. |
| Render input and source PDF | Deterministic presentation of that import. Retain the exact Markdown used for rendering through the existing write-once `source_markdown` store. |
| Reviewed brief | Ordinary editable ref-note body. Initialize once; subsequent scan, import, or AI generation must not overwrite the user's prose. |

The raw file and render input may differ: adding headings, escaping dangerous syntax, or formatting speaker turns changes bytes. `source_markdown` alone therefore does not establish byte-for-byte preservation of the original `.txt`. Extend the source store with an explicitly digested original attachment and manifest, or use a sibling content-addressed meeting-input store. Choose one implementation and test its Git allowlists, doctor checks, and retention. Do not keep the only source under `~/tmp`, an unsynced job directory, or `xlib/`.

Metadata should include `meeting_event`, meeting date/time/zone as observed, provider identity when known, source kind and digest, generator/model and prompt version when applicable, and review time. Proposed fields are new contract work, not existing supported options. Avoid placing machine-specific absolute paths or participant email addresses into a readable title. A filename is provenance, never a deduplication key.

For real transcripts, source anchors can address turns and supplied timestamps. For this input, they address paragraph/line ranges tied to the full source digest. AI output should refer to those ranges structurally; Bob validates they exist and that displayed excerpts match. This validates citation location, not semantic entailment, so human review still matters.

### Identity and linking

Use two distinct identities:

- **Local address:** vault-relative note path and block ID. An unqualified `^bryan-bugyi-derrick` is insufficient, particularly for repeated titles on different days.
- **Provider occurrence:** the canonical calendar ID and event ID already represented by Bob's gcal occurrence/journal. Store provider/account context where needed; never use `primary` as a durable calendar identifier. For handwritten events, retain a local identity without requiring Google access.

Recurring-event title, meeting URL, and series ID alone cannot identify one occurrence. Google documents `originalStartTime` as identifying an instance within its series even after rescheduling; Bob already exposes `calendar_id` and `event_id`, with original-start data on events. Reuse that mapping and test rescheduled occurrences. [Google Calendar event resource](https://developers.google.com/workspace/calendar/api/v3/reference/events), [recurring-event guide](https://developers.google.com/workspace/calendar/api/guides/recurringevents).

Default to one canonical meeting reference per occurrence, with multiple source attachments when an export is enriched or corrected. Same occurrence + same source digest returns the existing ref. Same occurrence + new content offers **Add source / update draft**, never silent replacement. Different occurrences with identical input raise a visible reuse warning rather than silently collapsing them. Ref IDs follow filenames under the existing rule; stable occurrence provenance must therefore survive a ref rename independently of the display ID.

The event link is an ordinary inert note link, not a Depends-On entry, task relation, Task Requirement, or Pomodoro Task Link. Keep it outside the hashed Google description window. A later root change must not silently refile an edited reference; offer a destination change explicitly. A missing event leaves a readable ref with a repairable link, not an orphan to delete. A missing ref leaves a diagnosable link, not permission to regenerate content from memory.

Private **Event notes** (`bob gcal note`) are a different feature: directive-bearing logistics projected into a Google-owned description window. They can affect root, buffers, and acknowledgement. Its journal also bounds canonical note text to 2,048 bytes; this source is already larger. Do not overload that field with meeting minutes, or offer series-wide meeting minutes by default.

### Model boundary

Bob owns event resolution, parent validation, source parsing, source identity, link rendering, plan validation, and writes. A generator receives only the selected source, verified event metadata, relevant route labels, and optional instructions. It returns a structured draft with summary sections, evidence spans, uncertainty markers, and proposed actions. It does not receive shell or vault-writing authority.

Treat source text as data even when it says to run commands, change tasks, or ignore instructions. Render imported material inertly: do not execute embedded Dataview, HTML, command chips, capture sigils, or remote images. Known user-authored wikilinks in the reviewed brief can be created by Bob from validated identities. Source content cannot create those identities.

Allow the generator to be replaced. An existing agent can supply a reviewed draft through the same contract, and the UI can use a configured model provider. I did not establish an existing general meeting-summary runtime in Bob, so provider integration, cancellation, timeout, cost controls, and configuration must be budgeted explicitly. Use an ordinary structured model call, not a new autonomous agent framework. Source-only formatting must remain possible without a model.

For long inputs, partition by source turns or sections with stable offsets, generate section evidence, and assemble a final brief with coverage checks. Never silently truncate and label it complete. No network retrieval or additional vault traversal is required to summarize the supplied meeting.

### Publication and recovery are the hard part

Current `highlights_ref/intake.rs` offers typed `Ingested`, `Queued`, and `Incomplete` outcomes. The command can exit successfully with a queued PDF. `reading_execute.rs` explicitly says its write sequence is **not a multi-file transaction** and recovers by adopting an existing reading task on rerun. Do not wrap today's create command and append an event bullet afterward while calling the whole operation atomic.

Introduce a durable operation envelope covering source installation, ref birth with brief, reading record, and event backlink. Generate and render before taking vault locks. At publication, follow the existing `bob_sync.lock → scan.lock` order, pre-sync, resolve again, and verify the preview's event, destination, and source fingerprints. If material context changed, retain the draft and refresh the review; do not silently choose a new meeting.

A filesystem cannot atomically rename several independent notes at once. The implementation needs guarded writes plus a durable recovery record, deterministic operation identity, and idempotent adoption/repair. A detected failure can roll back unchanged outputs or leave an explicitly repairable pending state. A process crash must be recoverable without rerunning AI and generating a second reference. Do not hold vault locks through model requests.

Return clear states such as `draft`, `ready`, `saving`, `linked`, `saved_locally_sync_pending`, `needs_review`, and `repair_required`. Names are illustrative. Only `linked` or a precisely described local-success result is allowed to dismiss the sheet as saved. A queued render must not leave a dangling event link. A network push failure after complete local writes should retain the work and say sync is pending.

Use the local duplicate guard under locks and provider/source provenance to detect cross-host duplicates. Local locking does not guarantee global exactly-once creation: two hosts can pull the same revision and race. Concurrent conflicting births need a tested reconciliation or explicit repair state, never silent last-writer-wins loss of a reviewed brief. Do not claim this is solved by a content hash alone.

A reversal operates on the receipt's exact written spans and hashes. If the user has edited the new note or event since saving, stop destructive reversal and offer **Unlink**; do not blindly revert entire parent or daily files. Source history stays preserved unless the user explicitly requests its deletion.

## Interface and implementation boundaries

The public noun should remain `ref`, whose membership is reference material. Add a meeting-oriented producer, provisionally **`bob ref meeting`**, backed by prepare/draft/publish/status operations for clients. This is a proposed command, not one to run today. The exact option grammar needs a small contract review: new public long flags require short aliases, help/completions must follow Bob's ordering conventions, and a bare group must not mutate.

The protocol should accept a file or stdin, explicit event identity, optional destination override, source kind, and optionally a supplied draft. It should return schema-versioned JSON with resolved identities, the destination reason, planned paths, conflicts, and an operation token. A dry run must remain genuinely read-only and must not contact an AI provider. Producing an AI draft is an explicit separate operation; publication must not invoke generation again.

The frontend passes argv/input directly to Bob and renders its result. It does not parse capture grammar, infer calendar identity, write Markdown, or call the model independently. Do not add a magic capture sigil for this feature. Existing capture already has a large grammar, and this is a document workflow with source inspection and review.

The most relevant implementation seams are:

| Area | Reuse or extend |
| --- | --- |
| Source intake | `highlights_ref/create.rs`, `source_store.rs`, and `intake.rs`; new text-input normalization and original-byte retention |
| Reference birth | `reading_plan.rs`, `reading_execute.rs`, note rendering; initialize reviewed prose and event provenance in the same recoverable operation |
| Parent validation | Shared `parent_notes` resolver; prefer the valid event root, refuse an invalid/terminal destination with a chooser |
| Event identity and placement | `gcal/model.rs`, `journal.rs`, `bullet_block.rs`; do not add a second description-ownership rule |
| Ref lookup and presentation | `ref_library/show.rs`, rename/link handling, `RefsCore/RefsModel.swift`; expose meeting provenance and brief without confusing it with source PDF content |
| Obsidian entry point | Task Card / named command, resolving through existing Task Link behavior; accessible editor and source pane |
| Later Mac frontend | Existing process client, event identity views, Refs styling and selection patterns; additive JSON decoding |

Prefer a narrow producer module with shared planning helpers over embedding the whole workflow into the already large `create.rs`. Reuse existing format and identity rules but do not pretend the current intake API already carries all the state needed for meeting publication.

## Explicit adjustments to the requested requirements

| Adjustment | Reason |
| --- | --- |
| Accept imported notes, transcripts, and whole exports | The first input is summary-shaped, and Wispr exports have different fidelity. |
| Make AI optional for already useful notes | Avoid a redundant transformation and preserve an offline filing path. |
| Default to the event's valid root, with a visible override | This example has an authoritative `job` route; title-based project inference is weaker. |
| Preserve the original and its source kind | A beautiful brief must remain auditable and must not acquire invented transcript authority. |
| Publish a reviewed ref without an open reading reminder by default | Avoid turning every saved meeting into backlog; retain the existing modern ref record and expose Review later. |
| Keep task extraction out of automatic save | Ownership, deadlines, duplicates, and real-world changes need separate deliberate choices. |
| Start with selected imports; add direct Wispr access later | File/paste covers the actual case and isolates durable filing from account-specific connector behavior. |
| Treat meeting refs separately from private calendar Event notes | The latter has directive, acknowledgement, scope, and size semantics unsuitable for minutes. |
| Keep a source PDF for compatibility in v1 | Text-native birth is broader than this feature; the editable brief remains the primary event-facing experience. |

These are design recommendations, not approved changes to existing architecture decisions.

## Acceptance criteria and evidence still needed

A prototype should make the supplied case executable end to end, then use a small fixture set. The hard checks are behavioral, not tests mirroring rendering code.

| Scenario | Required result |
| --- | --- |
| Supplied `.txt` and explicit block | Destination `job`; source classified as notes; exact reciprocal links; event remains completed with unchanged timing/root. |
| Same upload twice or lost success response | Same ref and reading record, one event link; no new model call required to recover. |
| Two same-title meetings; recurring and moved instances | User/context selects the exact occurrence; identity survives reschedule; no series-wide attachment. |
| Root removed or project closed after preview | Preserve draft and require a new valid destination; no quiet inbox fallback on publication. |
| Existing manual event children and later gcal sync | Notes link and manual text survive; description ownership and calendar behaviour remain unchanged. |
| Ref rename, reading-task move/archive, and event relocation | Ref stays findable; managed embed and parent follow existing rules; provenance/link repair remains unambiguous. |
| Failure after every write stage, busy locks, push failure | Recover or accurately report the state; no false success, lost source, duplicated task, or blind overwrite. |
| Two hosts publish concurrently | Duplicate/conflict detection yields an explicit, recoverable outcome. |
| Source contains prompt injection, capture sigils, or active Markdown | Source displays as evidence and creates no commands, tasks, embeds, or network side effects. |
| Corrected export / additional transcript | New immutable source revision; edited brief preserved; replacement shown as a diff for review. |
| “BOLI,” “Sassy,” 60–75 minutes, Derrick's email | No silent correction, false exactness, assigned Bryan task, invented deadline, or invented timestamp. |
| Cancel generation; reopen editor; source/model unavailable | Draft preserved, cancellation bounded, and file/paste/source-only mode still available. |
| Light/dark, narrow layout, keyboard and screen reader | All key actions usable; evidence and destination readable without color dependence. |

Evaluate note quality against a human rubric: useful brief, correct commitments, retained uncertainty, no unsupported facts, navigable evidence, and low correction effort. Count incorrectly created tasks separately from missed optional suggestions; both can be hidden by an attractive overall summary score.

Provisional UX goals—not measured results—are one launch, one paste/drop, and one Save after review for an unambiguous event, with no mandatory filename or project typing. Record time to first editable content, time to durable link, manual corrections, destination overrides, and repeat-import outcomes. Source-PDF rendering and Git sync are likely latency contributors; measure them before adding caches or a daemon.

Still unverified: an authenticated Wispr MCP end-to-end import, actual model quality/latency, rendered UI usability, cross-host publication, and whether the closed reference record's effect on statistics is acceptable. No code change or test suite execution was required for this research. The `.txt` dry-run rejection and live-vault metadata are directly observed; the proposed UX and publication protocol have not been implemented.

## Evidence ledger

Local source inspections used these revisions:

- **bob-cli:** `8d82c621b25d1595ec8a495c30f6087fbc87f524`. `docs/ref.md`, `docs/highlights-create.md`, `docs/highlights-ref-sync.md`, `docs/ref-jobs.md`, `docs/gcal.md`, `docs/gcal-notes.md`; `src/native/highlights_ref/{source_store,intake,reading_plan,reading_execute,note}.rs`; `src/native/ref_tasks/line.rs`; `src/native/gcal/{model,journal,bullet_block}.rs`; `src/native/ref_library/show.rs`.
- **bob-plugins:** `3824ce558a08174d74addcc6f14687303dfd635a`. `docs/task-card.md`, `docs/calendar-events.md`, `plugins/bob-ledger-tools/src/291-plugin-gcal-events.js`.
- **bob-mac-capture:** `0b441d3b9c9f5d29fd05967160126a6fba12ca44`. `docs/refs.md`, `Sources/RefsCore/RefsModel.swift`, `Sources/BobMacCapture/GcalNoteEditorView.swift`, and `Sources/BobMacCapture/Refs/RefsInspectorView.swift`.
- **Vault evidence:** read-only `bob query` for the exact November 23 task and area/project/reference metadata. No direct scan of unrelated notes and no mail-body reads were used. The attempted repository alias `bob` was not configured; vault data was obtained through the supported query skill.
- **Input:** the user-supplied file and digest above. Its company and interview claims are attributed to that file, not externally verified facts.
- **Audited memory:** `obsidian.md`, `cli_rules.md`; glossary definitions of Event Task, Reference Note, Reference Task, Area Note, Project Note, and Task Link; decisions covering source preservation, ingest at birth, ref IDs, private event notes, thin clients, and panel closing keys.
- **External primary documentation:** linked beside its claims above; checked 2026-11-24. Wispr's current docs establish available capabilities, not that this account is authorized or that an integration has been tested. No peer research was read or obtained indirectly.

## Recommended solution

Ship **event-centered meeting references**: select the exact Event Task, paste or choose the source, review a concise editable brief with evidence, and **Save & link** into the event's area/project. For this first case, save a reviewed meeting ref under `job`, attach it to `2026/20261123#^bryan-bugyi-derrick`, preserve the supplied notes as summary-level evidence, and leave task creation to an explicit later action.

Use the current reference library and source-PDF machinery behind the scenes, add original-byte retention and a recoverable publication envelope, and make the brief—not PDF handling—the user-facing experience. Implement the Bob contract and a polished Obsidian flow first; native Mac convenience and Wispr MCP can follow without changing the underlying identity or storage model. This delivers the useful feature while keeping the first release focused on the hardest and most valuable promise: **the right notes, in the right place, attached to the right meeting, without losing what the user wrote.**
