# Google Calendar descriptions as useful, editable Event Task notes

Independent research by **cdx**, 2026-11-02. Scope: design research for `bob gcal sync`; no implementation or live-vault mutation. No other report or findings from this research swarm were consulted.

**Recommendation:** copy each new Event Task's cleaned description once, into plain nested bullets under one **CALENDAR DESCRIPTION** drawer. Include the same import when a context row becomes an Event Task. After that write, the bullets belong to Bryan: edits and deletions persist. Preserve useful structure and links, remove only recognized directive lines, and keep the existing calendar badge as the route to the current Google event.

This is a good idea as an editable meeting brief. It is a much larger and less predictable feature if “sync” also means continuously reconciling imported prose. The distinction should be explicit before implementation.

## What the current system already provides

The inspected bob-cli checkout was `311b15142f23f3fcbdfaed97db8ce17a692e5880`. I also inspected drawer-related source in bob-plugins at `89dae58a7d136e4a9a1bb79156212ecd926e706a` through an audited linked-repo open.

| Verified finding | Design consequence | Evidence |
| --- | --- | --- |
| The Google field mask already requests `description`. `RawEvent` deserializes it, extracts directives, and discards the remaining text. | No extra Google request, OAuth scope, or external service is needed. Preserve a normalized description alongside the existing event fields. | [Transport][transport], [event model][model] |
| Directive lines can contain routes, off-clock aliases, and buffers together. They are recognized only if every whitespace/comma-delimited token is a directive. | Do not remove matching-looking tokens from ordinary prose. Reuse the current line classifier and precedence. | [Directive implementation][directives], [shared fixtures][vectors] |
| Child bullets are explicitly user-owned and never reconciled. Rows and links are proposed once; removed rows are tombstoned. | Import-at-birth fits the current ownership model. Updating an existing description subtree needs a separate, explicit policy. | [Ownership and lifecycle documentation][ownership]; audited `decisions:bob-gcal-is-read-only-and-proposes-once` |
| Tasks are created both by insertion and by a Maybe-to-Yes context upgrade. | Cover both creation paths. Merely changing the task-row renderer is insufficient. | [Planner][planner], [context upgrade][upgrade] |
| Time changes move the whole indented child block with its task. | Properly indented description bullets will travel with the meeting. | [Block movement][reslot] |
| Sync plans first, writes through the existing preimage-checked writer, then appends journal records. Recovery adopts a matching unjournaled row rather than inserting another. | Create the row and description in the same note write; never append description text in a second pass. | [Writer][writer], [adoption path][planner] |
| Bob already recognizes nonempty ALL-CAPS child bullets as task drawers. | A single source drawer uses an existing convention and keeps imported context separate from personal notes. | [Drawer scanner][drawers]; audited `glossary:task-drawer`; [plugin conversion contract][plugin-drawers] |
| The JSON contract excludes descriptions and attendees. Human dry-run prints a note diff. | Keep description text out of normal reports, JSON, and journal records; the intentional human diff will reveal the text being copied. | [Output contract][json-contract], [report printing][reporting] |

The audited calendar decisions also preserve daily-note residence, root attribution, phase-based MEET filing, and read-only access to Google. This proposal changes none of those behaviors. New descriptions are content under the existing task, not a new kind of task or a new daily-note section.

## Critique and deliberate requirement adjustments

The practical benefit is strong: preparation instructions, agendas, and useful links become available exactly where the meeting is planned and annotated. A source-specific drawer gives those details a home without changing the one-line event overview.

The main costs are copied boilerplate, stale snapshots, and retaining invitation content in vault Git history. These are consequences of the requested copy, not reasons to reject it. The design should avoid adding more costs through aggressive summarization, hidden filtering, or automatic merging.

I recommend these explicit refinements:

| Original ambiguity | Recommended requirement | Why |
| --- | --- | --- |
| “Sub-bullets” might mean an undifferentiated set of immediate children. | Put imported bullets under one direct child named `CALENDAR DESCRIPTION`, even for a one-line description. | Consistent provenance, one fold target, and a clean place beside personal notes. This adds one level of indentation. |
| “Sync descriptions” could imply continuing updates. | Copy on Event Task creation only, including context-to-task upgrades. | Preserves the current promise about children and avoids a silent merge policy. |
| Exclude special syntax. | Exclude whole lines recognized by the current directive grammar; preserve mixed prose. | A sentence containing `@job`, `+15`, or `#offclock` is not necessarily metadata. |
| Convert arbitrary provider formatting. | Preserve meaning, list hierarchy, emphasis, and safe links in a small Markdown subset. | A readable note matters more than reproducing fonts, tables, or embedded widgets. |
| Import descriptions into corresponding events. | Apply only to events classified as Event Tasks. Do not expand context/omitted-event inclusion. | Keeps existing calendar filtering and the Events overview stable. |
| Existing tasks might acquire the feature retroactively. | No automatic backfill of existing or adopted tasks. | An absent subtree can mean Bryan removed it; the journal cannot prove otherwise. |
| All source content fits. | Bound conversion work and make any size fallback visible. Never silently truncate an agenda. | Reliability should not depend on an invitation's size or nesting. |

The release-day consequence deserves emphasis: **already-created rows will not suddenly gain descriptions.** New rows and successful context upgrades will. Do not advise deleting an existing row to force reimport: Bob deliberately tombstones removed rows. If Bryan wants an initial backfill, treat that as a separately scoped, previewed operation, not an implicit first-run migration.

I would choose a different approach only if the actual goal is “always show the organizer's latest agenda.” In that case, use a separately managed description subtree with its own ownership state, not ordinary meeting-note children. The alternatives below explain the additional obligations.

## The proposed experience

Suppose the description contains this HTML:

```html
<p>@job -15 +10</p>
<p>Please read the <a href="https://example.com/brief">design brief</a>.</p>
<p><strong>Agenda</strong></p>
<ul>
  <li>Decide the launch date</li>
  <li>Review dependencies
    <ul><li>Confirm the support handoff</li></ul>
  </li>
</ul>
<p>Bring questions for @alex; allow +15 minutes for discussion.</p>
```

The resulting task would look like this in Markdown. The event URL is illustrative; the task row still comes from Bob's current renderer.

```markdown
- [*] #task **1000-1030** Launch review [📅](https://calendar.google.com/event?eid=example "Open in Google Calendar") [buffer:: -15m +10m] [root:: job] [type:: MEET] ^launch-review
  - CALENDAR DESCRIPTION
    - Please read the [design brief](https://example.com/brief).
    - **Agenda**
      - Decide the launch date
      - Review dependencies
        - Confirm the support handoff
    - Bring questions for @alex; allow +15 minutes for discussion.
```

The last sentence stays intact. It does not satisfy the directive-line rule. The first paragraph disappears from the copied prose because Bob already consumes it as directives. Whether `[type:: MEET]` appears continues to depend on the existing type logic.

Personal notes can then sit beside the source material:

```markdown
  - CALENDAR DESCRIPTION
    - Please read the [design brief](https://example.com/brief).
  - NOTES
    - We agreed to move the launch to Thursday.
```

Bob should not manufacture the `NOTES` drawer; this example shows what Bryan can add. The source drawer has no checkbox, extra `#task`, copied block ID, new timestamp, or second calendar link. Its title is plain ALL-CAPS, matching the existing drawer grammar rather than depending on a decorative emoji or special plugin.

Obsidian supports folding indented lists. That makes a drawer a natural disclosure control, but Markdown does not encode “start collapsed,” and a CLI should not overwrite the editor's fold state. This design promises a foldable block, not forced collapse. [Obsidian folding documentation](https://obsidian.md/help/folding)

For an empty, whitespace-only, or directive-only description, render nothing: no empty drawer and no “No description” filler. For a long but ordinary invitation, keep the meaningful content in the drawer; do not insert summaries or move it to another note automatically.

## Conversion rules: readable structure without importing behavior

Google documents `description` as optional text that can contain HTML. There is no separate description MIME-type field in the event resource. Conversion must therefore handle plain text, HTML fragments, and imperfect mixed input. This conclusion follows from the API contract; it is not evidence about the distribution of Bryan's actual invitations. [Google Calendar Events resource](https://developers.google.com/workspace/calendar/api/v3/reference/events)

Use a typed intermediate representation rather than “HTML to Markdown, then prefix every line.” For example:

```text
DescriptionDocument
  logical lines with source identity and directive disposition
  paragraphs / list items / headings
  inline text / emphasis / links / inline code
```

The representation is an implementation suggestion, not a new external contract. It makes source structure and literal text distinguishable before Bob syntax is emitted.

| Source | Proposed output |
| --- | --- |
| Plain nonempty lines | One plain bullet per explicit line; trim line edges and normalize CRLF. Do not hard-wrap to terminal width. |
| Plain `-`, `*`, or `+` list marker followed by a space | Consume one marker and render a normal bullet. Preserve recoverable indentation; avoid `- - item`. |
| Plain numbered items or HTML ordered lists | Keep ordinal information as escaped text, e.g. `- 1\. Check the cable`; preserve order and nesting. Do not turn numbered instructions into tasks. |
| HTML paragraphs and `<br>` | Preserve meaningful paragraph/line boundaries as bullets; combine adjacent text and inline nodes without inventing separators. |
| HTML unordered and nested lists | Preserve hierarchy beneath the drawer, with one canonical bullet marker. |
| Headings | Render a bold label bullet. Nest an immediately following list under that label; do not invent labels for unlabeled material. |
| Bold and italic | Preserve lightweight emphasis, emitting markup only from recognized structure. Ignore font, color, size, and positioning. |
| Links | Preserve label and destination. Permit `https`, `http`, `mailto`, and validated `tel` destinations; resolve neither relative URLs nor arbitrary schemes automatically. |
| Bare URLs | Preserve them as links after validating the destination; do not fetch them. |
| Checkboxes in descriptions | Render visible inert text such as `- \[ ] Send the deck`. Do not create tasks or change task counts. |
| Images | Preserve useful alt text and, if safe, an ordinary link to the image. Never emit an image embed or download media. |
| Tables | Flatten rows to readable bullets, preferably `Header: value` when headers are unambiguous. Do not create a Markdown table inside the task. |
| Code or preformatted text | Preserve the literal text and explicit lines without treating it as Bob commands. Do not emit executable/query fences. |
| Comments, script/style contents, embedded frames | Omit non-content/active material. Preserve surrounding visible text; never execute HTML or make asset requests. |
| Blank blocks or blocks emptied by directive removal | Omit them. |

Plain-text Markdown-like emphasis and links require an explicit policy: support a restricted inline parser for ordinary links and emphasis, but treat wikilinks, embeds, raw HTML commands, Dataview syntax, and task metadata as literal source data. This is not a license to pass the whole source through as trusted Markdown. The same escaping rules must apply to HTML text nodes and plain text.

Retain phone numbers, passcodes, repeated contact instructions, and provider boilerplate in the first release. They may look noisy but can be the only viable way to join a meeting. Do not deduplicate links against the row's join badge, strip text after a provider-specific separator, remove “unsubscribe” sections, or use an LLM to decide what matters. A foldable source drawer solves most of the visual problem without guessing.

### Directive exclusion must share the real grammar

Current parsing first normalizes HTML boundaries at `br`, `p`, `div`, and `li`, strips other tags, and decodes supported entities. It then splits each line on whitespace and commas. A line qualifies only if every token is a recognized route, off-clock alias, or buffer. The first route and first value for each buffer side win. These are verified implementation facts, not proposed syntax. [Parser][directives], [fixtures][vectors]

The content converter should consume the parser's classification, rather than independently searching for strings to delete. Ideally, a single analyzed-description result returns both the existing directive values and the surviving content blocks. Preserve source-line identity through this step; deleting every occurrence of a matching string could erase identical prose elsewhere.

| Description text | Directive behavior and copied content |
| --- | --- |
| `@job -30 +15` on its own line | Parse directives; omit the whole line. |
| `@job, #OFF-CLOCK, −30m` | Same rule; preserve current aliases, case handling, and comma behavior. |
| `Ask @job about +15 minutes` | Preserve the whole sentence; it is not a directive line. |
| `Dial +1 555-1212` | Preserve the phone instruction. |
| `-1234 +15` | Preserve the line: the invalid four-digit token makes the whole line non-directive under today's rules. |
| `@job @body -30 -15` | Omit the directive line even though later valid directives lose precedence. Do not leak ignored duplicates into the note. |
| `@missing` alone | Treat as directive syntax, omit it from prose, and retain the existing root-resolution warning/fallback. Do not make removal depend on a successful route lookup. |
| `<b>@job</b><br>Bring shoes` | Consume the route line, copy `Bring shoes`. |
| A literal `-30` line | Today it is a buffer directive. This feature must not silently reinterpret that ambiguity as prose. |

A robust HTML parser will handle some input differently from today's small tag-stripper. **Do not allow that refactor to silently reroute meetings or alter buffers.** Keep the existing directive result authoritative until a shared compatibility projection passes the current fixtures and added cases for HTML boundaries, split inline nodes, entities, and malformed fragments. Rich-content block boundaries and directive logical-line boundaries need not be identical; an HTML heading should not accidentally create new directive scope.

For an ambiguous malformed fragment where content cannot be aligned confidently to consumed directive lines, preserve uncertain visible text and report a conversion fallback rather than deleting a guessed range. Metadata still follows the established parser. Making malformed-input behavior more regular can be a separately reviewed grammar change; it is not required to copy ordinary descriptions correctly.

### Escaping is about Bob semantics as well as Markdown

The shared task text escaper already protects `#task`, inline field separators, comment markers, and trailing block IDs, but deliberately leaves other markup intact. It is a useful component, not a complete description sanitizer. Apply escaping to text nodes; do not corrupt the converter's deliberately generated Markdown or link destinations. [Shared escaper][escaper]

One concrete interaction makes this important: `row_untouched` scans the entire task block for the literal 🍅 character and treats its presence as work history. An invitation saying “🍅 Pomodoro workshop” could therefore prevent a later automatic cancellation if copied verbatim. [Lifecycle predicate][untouched]

For this feature, neutralize such reserved symbols in imported text at the source-byte level while preserving their rendered appearance—for example, render a literal tomato as `&#127813;`. A backslash or code span is insufficient when the consuming code uses substring matching. Verify this against the actual task and lifecycle scanners, not just visual Markdown rendering. The wrapper drawer alone does not provide isolation.

The output must also prevent imported `%%` comments, `[[#^id]]` task links, `![[embeds]]`, `[root:: ...]` fields, checkbox starts, trailing `^ids`, and managed-log-looking content from becoming workflow structure. Escaped or entity-encoded literal text may look slightly noisier in Source mode; use that cost where needed to preserve the meaning and avoid changing task state.

## Ownership and lifecycle: a small, complete contract

**Once the initial write succeeds, description bullets are ordinary user-owned notes.** They need no continually checked content hash, hidden marker pair, or field identifying an owned byte range.

| Situation | Recommended behavior |
| --- | --- |
| New eligible task with content | Insert row, drawer, and content in the same note write and file its existing MEET link normally. |
| New task with empty/directive-only content | Insert only the ordinary task row and link. |
| Existing Maybe context becomes a task | Import the current description once at the successful upgrade; preserve any existing children in place. Add the source drawer after existing child content, using the prevailing indent. |
| Upgrade already has a direct `CALENDAR DESCRIPTION` drawer | Preserve it and skip automatic import with a concise notice. Do not merge into or append a second same-named drawer whose ownership is unknown. |
| Ordinary rerun | Never append, replace, reorder, or deduplicate description children. The Events stamp can still change under today's existing rules. |
| Bryan edits, renames, moves, or deletes the source drawer | Keep the edit. No reconstruction or ownership guessing. |
| Google later edits, removes, or first adds a description | Leave the task's children unchanged. The calendar badge opens the latest source. No repeated “conflict” warning for an intentionally immutable snapshot. |
| A previously existing Event Task has no description | Leave it alone. Absence is not evidence that import was missed. |
| Crash recovery adopts an unjournaled task | Adopt its identity and preserve all children. Do not append descriptions during adoption. |
| Meeting time changes within the day | Move the existing task plus its entire child block through the existing re-slot logic. |
| Meeting is cancelled/declined/moved to another day | Keep current row lifecycle behavior, including the Cancel Log and preservation of child notes. Do not erase copied context. A genuinely new task on another day gets its own snapshot. |
| Recurring event has another occurrence | Copy that occurrence's description at its own birth; never key description ownership by title or series root. |
| Context or omitted event | Do not import descriptions unless it later qualifies for task creation. |

Google's recurrence model distinguishes instance IDs from the shared series `iCalUID`. Bob already keys its journal by calendar/event identity and day; reuse that model rather than inventing description identity. [Google Events identity fields](https://developers.google.com/workspace/calendar/api/v3/reference/events)

Creation-only import knowingly misses late agendas. A task synced tomorrow can carry today's agenda snapshot even if the organizer changes it before tomorrow's meeting. A task born with an empty description will remain empty. The documentation should state this plainly:

> Descriptions are copied once when Bob creates an Event Task. Edit or delete those bullets freely. Open the calendar badge for the current Google description.

That is proposed product copy, not an existing guarantee about imported descriptions.

## Implementation shape and specific traps

This is a bounded importer feature. It should remain in bob-cli; ordinary Markdown and existing drawers should not require a new macOS app contract or a plugin feature to ship.

1. Add a focused `gcal/description.rs` module for directive classification integration, HTML/plain-text conversion, inline escaping, limits, and deterministic bullet rendering. Its pure input is the provider description; its output is normalized content plus conversion diagnostics and the existing directive result.
2. Carry the normalized description privately through `GcalEvent` and `PlannedOccurrence`. Do not add it to public JSON models or journal payloads. If a raw string is retained temporarily, release it after normalization and avoid logging it through `Debug` output.
3. Keep `render_task_row` a **one-line** renderer. Add a creation-block renderer returning a vector of physical lines: parent row, optional drawer, descendants.
4. On new task insertion, use `WorkingNote::insert_block`. On context upgrade, replace the parent line, then splice description lines at the chosen child-block boundary without overwriting existing children. Recompute indices needed by later planning passes.
5. Keep ordinary `apply_span_updates` and crash adoption out of the description write path. Because the row already records creation, no description-specific journal schema is necessary for this ownership policy.
6. Feed conversion warnings into existing reporting, retaining `-q` behavior. Document the creation-only rule, the drawer shape, the lack of backfill, and the human dry-run privacy implication.

**Do not append `\n` plus bullets to the string returned by `render_task_row`.** `WorkingNote.lines` is explicitly a vector with one physical line per element. `insert_row` inserts one vector element; context upgrade assigns one element. A multiline string there might serialize into plausible Markdown while breaking row scans, subsequent insertions, reslotting, and final Pomodoro line numbers during that same plan. This is directly visible in the current planner. [WorkingNote insertion methods][working-note], [upgrade][upgrade]

Use the note's established indentation where available, drawing on existing child-indentation helpers. Keep every content line nested within the task; never allow a source heading, fence, or unindented continuation to escape into the daily note. For new blocks, two spaces per level is the illustrative default above, subject to the repo's existing indentation helper.

**Do not bolt description writes onto the end of sync.** A later second write introduces a crash state with a row but no description and invites attempts to “repair” intentional deletions. One staged note mutation gives recovery a simple rule: an existing row is complete from the importer's perspective, and adoption never adds content. The journal is still written afterward, so this is crash-tolerant rather than an atomic note-plus-journal transaction. [Sync write order][writer]

### Parser dependency choice

The current normalizer is appropriate to its small directive-extraction job, but it drops anchor destinations and does not represent nested lists. It is not a sufficient rich-description converter. [Current normalizer][directives]

Prefer an HTML5 fragment parser with a small Bob-specific renderer. `html5ever` exposes fragment parsing; the HTML standard defines recovery behavior for malformed HTML. The attraction is predictable parsing, not a browser engine or a full sanitizer stack. Evaluate its DOM support and dependency cost against this repository before selecting exact versions. [html5ever API](https://docs.rs/html5ever/latest/html5ever/), [HTML parsing standard](https://html.spec.whatwg.org/multipage/parsing.html)

`html2md` already offers HTML-to-Markdown conversion and custom handlers, but its general output vocabulary is broader than this task's allowed subset. `html2text` provides text-oriented rendering and width-based wrapping, which is useful for terminals but undesirable as the default storage format for stable notes. Either could supply parts of a prototype; neither should define the product contract by default. These are assessments of documented interfaces, not benchmark results. [html2md documentation](https://docs.rs/html2md/latest/html2md/), [html2text documentation](https://docs.rs/html2text/latest/html2text/)

A hand-written sequence of tag substitutions is the least attractive option: it loses links and nesting immediately, and handling quoted `>` characters, entities, malformed fragments, and script contents gradually recreates a parser.

### Limits and failure behavior

Choose explicit parser/output limits and test them. Reasonable starting values for evaluation are 64 KiB of input, 32 KiB of rendered content, 200 emitted items, and eight content nesting levels. These are proposed engineering limits, **not Google limits or values measured from Bryan's calendar**.

If a limit would be exceeded, omit the description copy for that occurrence, keep the event task, add a small nonempty source drawer with `Description was not copied because it is too large; open the calendar badge.`, and emit an actionable warning. Do not silently copy the beginning and discard the only dial-in number at the end. Do not keep retrying or append a second fallback on later syncs.

Recoverable HTML problems should preserve visible text in safe bullets where possible. A malformed event envelope or incomplete calendar snapshot must still retain the existing all-or-nothing sync failure behavior. Description rendering degradation is different from uncertainty about which events exist.

The deliberate persistence change is that selected description content will now live in the daily note and vault Git history. Keep the source confined to that intended destination: no raw provider HTML snapshots, no descriptions in JSON/status/journal records, and no content in routine warnings. Human `sync -d` is an explicit preview of the resulting note and necessarily includes copied text. The existing JSON dry-run report does not print the human diff; preserve that distinction. [Report printing][reporting]

## Alternatives and when they win

| Approach | Advantages | Costs | Verdict |
| --- | --- | --- | --- |
| Keep only the calendar badge | Always opens the live source; no copied clutter. | Context switching; no local editable brief or offline copy. | Does not satisfy the useful part of this request. |
| Direct child bullets copied once | Smallest visible structure and implementation. | Source and personal notes mingle; long descriptions dominate; no source-only fold. | Acceptable, but less clear than one drawer. |
| One source drawer copied once | Existing idiom, clear provenance, safe ownership, simple recovery. | Snapshots get stale; one extra nesting level; no backfill. | Recommended first release. |
| One managed drawer that follows Google until locally edited | Fresher agendas while preserving a personal edit. | Must track ownership, deletion, migration, conflicts, and missing journal state. Header text alone is not identity. | Worth doing only if live descriptions are an explicit requirement. |
| Per-bullet three-way merge | Could update unrelated organizer changes around personal edits. | No stable IDs for source bullets; reorder/split/duplicate cases are ambiguous; difficult undo and explanations. | Reject for this feature. |
| Separate generated reference note or hover-only view | Keeps daily notes short; can show long rich content. | Extra artifact/client machinery and a detour from the task; harder editing/residence model. | Reserve for a demonstrated long-document use case. |
| AI-generated summary and extracted action items | Short output. | Can omit essential instructions, invent tasks, vary between runs, or expose private descriptions to another service. | Reject as the default importer. |

If live descriptions are selected instead, the minimum defensible design is an independently tracked source subtree: record a last-emitted canonical hash, compare the current subtree before any replacement, detach permanently on local edits or deletion, and keep personal siblings outside the managed region. Empty-source state, missing-baseline state, and user-deleted state must be distinct. Description conflicts must not block root/time updates. Unknown ownership after a crash or migration must preserve the vault and avoid reimport. Completed/started meeting policy must also be explicit so historical notes do not drift. This is a meaningful extension of the current children ownership contract; it should not be smuggled in as a formatting change.

I would not add this second mode, a refresh command, an import history log, or per-event suppression syntax to the first release. The snapshot behavior is valuable on its own and gives a clean basis for judging whether stale agendas are a real problem.

## Acceptance criteria and research limits

The existing tests use a fake gog executable and temporary vaults, so the feature can be exercised without touching Google. Build on those integration fixtures rather than testing only string conversion. [Sync tests][sync-tests], [lifecycle tests][lifecycle-tests]

| Area | Essential cases and expected result |
| --- | --- |
| Creation | New future, running, and past tasks get one source drawer when nonempty; existing phase/status/link behavior stays correct. |
| Upgrade | Maybe-to-Yes imports once; preexisting children survive; a conflicting source drawer is preserved. |
| Parser | Plain text, HTML paragraphs, `br`, nested lists, ordered lists, entities, Unicode, inline links, malformed fragments, and angle-bracket prose. |
| Directives | All existing shared vectors remain valid; removed lines exactly match recognized grammar; mixed sentences and phone numbers survive. |
| Workflow isolation | Imported checkboxes, `#task`, fields, block IDs, comments, embeds, managed-log-like text, and 🍅 do not create tasks, links, or work history. |
| Idempotence | Same-minute rerun adds no rows, descriptions, or journal records. At a later minute, only the existing stamp behavior changes absent other events. |
| User ownership | Edit/delete/rename the source drawer, then rerun with changed Google descriptions; local bytes remain unchanged. |
| Source changes | Empty-to-nonempty, edited, and deleted Google descriptions never backfill or replace existing task children. |
| Placement | Multiple new meetings around existing rows with nested children; no row inserted inside another task; final MEET line indices are correct. |
| Lifecycle | Reslot carries the full block; cancellation preserves source/personal children; imported symbols do not falsely mark a task worked. |
| Recovery | Note write succeeds but row-journal append fails; next run adopts without duplicating content. Existing unjournaled rows are never used as backfill targets. |
| Concurrent edit | Preimage mismatch triggers the existing replan path; user children survive and descriptions appear once. |
| Output/privacy | Human dry-run shows the exact source drawer and writes nothing; JSON, ordinary logs, status, and journal omit description text. |
| Bounds | Size/item/depth limits produce one visible fallback without preventing the rest of a complete day's events from syncing. |
| Visual review | Inspect one-line, normal agenda, long invitation, and malformed-input output in Obsidian Source mode, Live Preview, and Reading view. Check folds, links, indentation, and separation from personal notes. |

This report is based on source and fixture inspection, audited project memory, and primary external documentation. It does not claim a working converter, passing feature tests, measured parser performance, or verified Obsidian screenshots. I did not inspect Bryan's private event descriptions. In particular, the proposed size limits and choice of a consistent drawer over direct bullets remain design judgments that should be evaluated with representative synthetic fixtures and, if desired, examples Bryan explicitly provides.

The most important implementation uncertainties are HTML/directive compatibility on malformed mixed input and whether the sanitized output remains inert to all relevant Bob scanners. Both belong in the acceptance gate; neither is resolved merely by picking an HTML library.

## Evidence index

Project sources below are pinned to inspected commits. These links identify the code read locally; no external repository files were fetched through the web.

- bob-cli: `311b15142f23f3fcbdfaed97db8ce17a692e5880`.
- bob-plugins: `89dae58a7d136e4a9a1bb79156212ecd926e706a`.
- Audited memory: `sase_artifacts.md`, `obsidian.md`, `decisions:bob-gcal-is-read-only-and-proposes-once`, `decisions:gcal-root-follows-google-until-edited`, `decisions:calendar-events-are-daily-note-event-tasks`, `decisions:synced-meetings-link-by-phase`, `glossary:event-task`, and `glossary:task-drawer` with their automatically included dependencies.
- Primary external sources: Google Calendar Events resource; Obsidian formatting/folding documentation; html5ever, html2md, and html2text API documentation; WHATWG HTML parsing standard. External claims and library assessments are linked inline.

[transport]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/src/native/gcal/gog.rs#L314
[model]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/src/native/gcal/model.rs#L79
[directives]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/src/native/gcal/model.rs#L262
[vectors]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/tests/fixtures/event_buffer/vectors.json
[ownership]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/docs/gcal.md#who-owns-each-part-of-a-row
[planner]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/src/native/gcal/plan.rs#L273
[upgrade]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/src/native/gcal/plan.rs#L836
[reslot]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/src/native/gcal/plan.rs#L759
[writer]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/src/native/gcal/sync.rs#L230
[drawers]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/src/native/capture_drawers.rs
[plugin-drawers]: https://github.com/bobs-org/bob-plugins/blob/89dae58a7d136e4a9a1bb79156212ecd926e706a/plugins/bob-navigation-hotkeys/src/100-yank-and-paths.js#L903
[json-contract]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/docs/gcal.md#json-output
[reporting]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/src/native/gcal/sync.rs#L1135
[escaper]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/src/native/task_text_escape.rs
[untouched]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/src/native/gcal/lifecycle.rs#L318
[working-note]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/src/native/gcal/plan.rs#L1210
[sync-tests]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/tests/gcal_sync.rs
[lifecycle-tests]: https://github.com/bobs-org/bob-cli/blob/311b15142f23f3fcbdfaed97db8ce17a692e5880/tests/gcal_lifecycle.rs

## Recommended solution

Ship **a creation-time description snapshot in one `CALENDAR DESCRIPTION` drawer**, containing safe, readable ordinary bullets. Preserve links and useful structure, exclude only lines consumed by the existing directive grammar, import on both task creation paths, and make all resulting children user-owned immediately. Insert a real block through the existing planner and staged writer. Keep existing tasks, adopted rows, and later edits untouched; keep provider text out of JSON and journals.

This gives Bryan meeting context at the point of use, a calm one-row overview with a foldable source drawer, and an ownership rule he can trust. Accept stale snapshots explicitly. If always-current agendas prove necessary, design a separately owned source subtree as a later product decision rather than expanding this importer into an implicit prose synchronizer.
