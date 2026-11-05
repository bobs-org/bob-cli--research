# `%c` clipboard history: wrong-provider diagnosis and a reliability design

Independent research by **cdx**, 2026-11-05. No other report, transcript, or findings from this research swarm were consulted.

## Decision in brief

**Keep `%c`; fix provider selection and the read/preview contract. On the inspected Mac, use an explicitly selected Alfred history adapter. Do not build another always-on clipboard manager as the initial solution.**

The user's suspicion is strongly supported by direct evidence. Bob reads the current clipboard through `pbpaste`, but its default macOS history source is a hard-coded Clipy SQLite database. During this investigation, Alfred was running and its database was current; Clipy was installed but not running, and its newest history entry was from October 20. This produces exactly the reported shape: a correct first item followed by unrelated old items.

Changing that one path is insufficient for the broader reliability goal. Provider identity, ordering semantics, bounded reads, representation handling, and preview-to-submit consistency need explicit contracts. The most useful reliability guarantee is **the requested, displayed content or a clear refusal before any write**, rather than filling a requested count from whatever history happens to be readable.

## 1. What was inspected and what is established

Research used repository code, read-only Mac metadata, synthetic isolated dry runs, and primary documentation. It did not start or stop clipboard managers, change configuration, copy sentinel text into the user's clipboard, modify the vault, or inspect personal clipboard payloads. Database queries returned schemas, counts, types, timestamps, and journal mode only.

Repository snapshots:

| Repository | Examined commit |
| --- | --- |
| bob-cli | `7e437418e958a12ed999053c425003eb9831eb52` |
| bob-mac-capture | `d2068037673b8e7681c88fce6afa2ffda079131c` |
| Clipy upstream | `d90477deb381e130e43f2b9a36ae6b9b8ce7e096` |

Clipy upstream is a separately checked-out source snapshot, not proof that every behavior in that snapshot is present in the installed application.

### Direct Mac observations

The `mac` SSH target was reachable. At approximately 09:04–09:12 America/New_York on November 5:

| Observation | Result | Meaning |
| --- | --- | --- |
| macOS | 26.5, build 25F71 | Actual inspected platform |
| Installed `bob` | 0.4.0 | Its help advertises the same Clipy default as the examined source |
| Alfred | 5.8.1, build 2349; running | An active alternative history manager exists |
| Clipy | 1.4.0; installed, no matching running process | Installation alone does not establish active recording |
| Clipy DB | `~/Library/Application Support/com.clipy-app.Clipy/sqlite.db`; 10,000 history rows | A substantial but old database remains readable |
| Clipy newest `updateAt` | `1792516869` = **2026-10-20 13:21:09 EDT** | More than two weeks behind the investigation |
| Clipy DB/WAL modification | October 20, including the WAL | Staleness was not inferred from the main DB modification time alone |
| Alfred DB | `~/Library/Application Support/Alfred/Databases/clipboard.alfdb`; modified **2026-11-05 09:03:04 EST** | Recent history activity |
| Alfred rows | 8,337; all `dataType = 0`; payload storage type `text` | Text is sufficient for an initial adapter on this observed dataset |
| Alfred newest `ts` | `815580184` | Interpreted as Apple's 2001 epoch, matches 2026-11-05 09:03:04 EST |
| Alfred journal mode | `delete` | Do not assume every clipboard database uses WAL |
| Recent Alfred timestamp ties | Two tied timestamp groups among the latest 100 rows | A timestamp-only sort has a real ambiguity on this machine |
| Launch environment overrides | `launchctl getenv BOB_CLIPBOARD_CMD` and `BOB_CLIPBOARD_HISTORY_CMD` both empty | No launchd override was observed; this does not prove the running app's entire effective environment |

The Alfred epoch interpretation is an inference corroborated by the modification time, not a published Alfred schema guarantee. Apple's documented reference epoch is January 1, 2001 UTC. Treat the conversion as adapter knowledge that needs a fixture, not as an assumption shared by all providers. [Apple: Dates](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/DatesAndTimes/Articles/dtDates.html)

**Confidence:** high that Bob's default history provider is wrong for the observed active setup. This is not an end-to-end proof of the user's original capture: the effective environment of that particular request and its payload were not examined. A controlled acceptance test after implementation should close that remaining gap.

### The code path explains the symptom

`read_clipboard_history(N)` reads the live clipboard first. For N greater than one, it then reads `BOB_CLIPBOARD_HISTORY_CMD`, when set, or Clipy's database on macOS. It normalizes the history strings, removes the first history string equal to the live value wherever it occurs, then prepends the live value and takes N−1 candidates. There is no active-manager check, last-observation check, or provider provenance in the result. [Bob clipboard reader](https://github.com/bobs-org/bob-cli/blob/7e437418e958a12ed999053c425003eb9831eb52/src/native/capture_clip/clipboard.rs#L15)

Therefore a valid old Clipy database is worse than a missing one: it can produce a successful capture with the wrong historical context. `%c` and `%c1` bypass history, which explains why their success says little about `%c3`.

**Terminology correction:** the suffix is a **count**, not an index. `%c3` currently means three values in total, with the live clipboard first; it does not mean “the third previous clip.” Preserve this syntax and make the wording consistent. [Existing contract](https://github.com/bobs-org/bob-cli/blob/7e437418e958a12ed999053c425003eb9831eb52/docs/capture.md#clipboard)

## 2. Reliability problems beyond the provider mismatch

### Stored representations can be mistaken for separate content

Bob's Clipy decoder appends every supported asset's decoded value, then joins them with newlines. A clip offering the same content as UTF-8 text and a URL can therefore become duplicated or mixed content. That combined string may also fail to match the live value, defeating the merge's equality check. [Bob Clipy decoder](https://github.com/bobs-org/bob-cli/blob/7e437418e958a12ed999053c425003eb9831eb52/src/native/capture_clip/clipy.rs#L140)

This is distinct from reading multiple history entries: a single copy can contain several items, and each item can offer several representations. Clipy's examined source explicitly does not preserve original pasteboard-item boundaries; its replay reconstructs groups by occurrence of each type. Consequently, simply grouping Bob's rows by the asset `index` would not recover original item identity. A maintained Clipy adapter needs provider-specific representation selection and must admit cases the schema cannot faithfully reconstruct. [Clipy content model](https://github.com/Clipy/Clipy/blob/d90477deb381e130e43f2b9a36ae6b9b8ce7e096/Clipy/Sources/Models/PasteboardContent.swift#L76)

### Deterministic order is not necessarily actual copy order

Bob sorts Clipy by `updateAt DESC, id DESC`. Clipy's examined writer uses integer Unix seconds; IDs can be content hashes or UUIDs, depending on settings. ID order breaks ties consistently but does not establish which of two same-second copies happened first. Recopy/deduplication settings also mean a manager's history need not be a log of every copy event. [Bob query](https://github.com/bobs-org/bob-cli/blob/7e437418e958a12ed999053c425003eb9831eb52/src/native/capture_clip/clipy.rs#L27), [Clipy writer](https://github.com/Clipy/Clipy/blob/d90477deb381e130e43f2b9a36ae6b9b8ce7e096/Clipy/Sources/Services/ClipService.swift#L206)

Alfred's inspected timestamps also have ties. A `rowid` tiebreaker is useful for repeatability within a snapshot, but it is not evidence of subsecond recopy order and is not a durable identity across database rebuilding. Do not promise “the last N copy keystrokes” from these databases.

### Read boundaries and merge rules are under-specified

The live clipboard and history are read at separate times. The clipboard can change between them; a manager can record asynchronously. Bob's Clipy reader first collects IDs and then fetches assets without an explicit transaction covering both stages. A concurrent clear or update can make the assembled result inconsistent or fail.

Text equality is not event identity. Removing an interior matching string can erase an older repeat, while a representation difference can leave a duplicate of the current item. A new provider should expose enough identity, timestamp, and ordering metadata to make this policy testable. Where it cannot, document the limitation instead of manufacturing precision.

Bob also decodes and normalizes all requested candidates before determining which N−1 historical values are needed. An invalid surplus candidate can thus abort a capture even when sufficient valid *selected* entries exist. Fix selection versus validation ordering without silently skipping an invalid entry that really occupies a requested position.

### A successful preview does not bind submission

The Mac app already renders clip cards and authorizes live clipboard previews only when Bob's accepted parse reports a clip directive. It polls `NSPasteboard.general.changeCount` while the relevant panel is visible. These are good foundations.

However, preview and submit are separate `bob capture` subprocesses; submit asks to read the clipboard again. There is no expected clipboard-snapshot argument in the examined client interface. A copy, history update, deletion, or provider lag between those calls can change what is written. Polling catches some changes but does not bind a preview to its eventual write; a database-only change may not move the system pasteboard counter. [Mac client](https://github.com/bobs-org/bob-mac-capture/blob/d2068037673b8e7681c88fce6afa2ffda079131c/Sources/CaptureCore/BobProcessClient.swift#L723), [Mac submission](https://github.com/bobs-org/bob-mac-capture/blob/d2068037673b8e7681c88fce6afa2ffda079131c/Sources/BobMacCapture/CapturePanelModel.swift#L2998)

Within one Bob invocation, clipboard memoization currently covers fanout targets of an item, not all ordinary capture items in the draft. Take one resolved clipboard snapshot for the whole invocation so two `%c` items cannot read different values mid-batch. [Bob planner](https://github.com/bobs-org/bob-cli/blob/7e437418e958a12ed999053c425003eb9831eb52/src/native/capture/plan.rs#L902)

### Failures need to be bounded and identifiable

Custom providers are launched with `Command::output()` without a local deadline or stdout-size bound. The command strings are split on whitespace, so quoted paths or arguments containing spaces are not represented properly. The Mac client has a broader process timeout, but a CLI invocation needs its own bounds and child cleanup. The current generic clipboard errors also do not expose stable provider-specific error codes. These are smaller engineering fixes with direct reliability value.

Keep the existing all-or-nothing behavior: insufficient history, a selected unsupported item, or an attachment-planning failure must leave the vault untouched. Existing tests already exercise several of these cases; extend that coverage rather than replacing it with weaker “best effort” success. [Current failure tests](https://github.com/bobs-org/bob-cli/blob/7e437418e958a12ed999053c425003eb9831eb52/tests/cli/capture/clip.rs#L505)

### Executed reproductions

The installed Linux `bob 0.4.0` was run with synthetic executable providers, an isolated empty vault and config, and `--dry-run --format json`. Temporary files were cleaned up; no files appeared in that vault. These tests exercise shared selection behavior, not the native macOS SQLite reader.

| Synthetic inputs | Observed result | What it demonstrates |
| --- | --- | --- |
| Live `CURRENT`; history `[OLD_FROM_STOPPED_MANAGER, EVEN_OLDER]`; `%c3` | Exit 0, all three values rendered | Stale history is accepted as long as it is valid text |
| Live `CURRENT`; history `[OLDER, ""]`; `%c2` | Exit 1, “history entry 2: clipboard is empty” | An unneeded tail candidate can reject the request |
| Live `CURRENT`; history `["CURRENT\nCURRENT", OLDER]`; `%c2` | Exit 0, three rendered `CURRENT` bullets across two entries | A combined representation can evade equality matching and crowd out the desired older item |

The third case simulates the output of the identified decoder behavior. It does not claim that the user's actual clipboard contained duplicate representations.

## 3. Is the proposed direction a good idea?

Yes: counted clipboard capture is a useful low-friction way to collect a small cluster of related text and links. But “make it resilient regardless of root cause” is too broad to be an acceptance criterion. Reliability here should mean predictable provenance and content, not more fallback paths.

The following are **recommended requirement adjustments**, not existing behavior:

1. **Name the source.** `%c` reads current contents; counted capture adds entries from one configured history provider. Report that provider in the clip preview and diagnostics. Never mix multiple managers' databases or silently switch after a provider failure.
2. **Define history as saved entries.** Guarantee the provider's ordered, saved history, with documented deduplication and tie behavior. Do not imply recovery of every copy event. Keep `%cN` as a total count.
3. **Require exact selected content or refusal.** No silent shortening, stale fallback, replacement of an unsupported selected entry with an older one, or commit of different content than the reviewed preview.
4. **Scope the first Alfred adapter to text.** URLs and file paths represented as ordinary text can retain Bob's existing classification. Native image/file representations need separate validated codecs. Refuse a selected unsupported type rather than silently changing position semantics. All inspected Alfred rows were text, so this solves the observed need without pretending to cover all history types.
5. **Keep `%c` independent.** A missing, stopped, or incompatible history manager must not break the current-only path.
6. **Bound resource use.** Set and document count, payload, and execution limits. A starting product proposal is 50 requested entries, a short provider deadline, and an aggregate byte cap; validate actual workflows before fixing these values. This is a deliberate limit change, not an existing promise.
7. **Retain existing privacy choices.** Read the chosen manager's already-retained history, do not recover excluded/deleted entries, and keep clip contents out of diagnostics. Do not create an additional permanent history store as a side effect of reliability work.

Alfred already supports retention, application exclusions, maximum-size exclusions, and concealed-data handling. A stopped or quiet history is not automatically corruption, and an intentionally excluded current value may be absent from history. Age and process liveness should be evidence shown to the user, not a blanket “older than X is invalid” rule. [Alfred clipboard settings](https://www.alfredapp.com/help/features/clipboard/)

## 4. Implementation options

| Option | Advantages | Costs and limitations | Assessment |
| --- | --- | --- | --- |
| Restart Clipy and leave Bob unchanged | Minimal code work | Changes the user's manager setup; retains selection, decoding and preview issues | A temporary diagnostic/workaround only if the user actually wants Clipy |
| Explicit Alfred SQLite adapter in Bob | Fits the observed Mac; small local reads; no extra recorder or UI automation | Private schema, manager-defined history, ordering ties; needs fixtures and capability checks | **Best first implementation for this setup** |
| Alfred workflow exporting history via documented placeholders | Uses Alfred's own history expansion and avoids database decoding | Requires a workflow and invocation/reply protocol; arbitrary counts and atomic snapshots need validation | Good alternative if the private-schema maintenance cost proves unacceptable |
| New Bob-owned recorder | Own schema, sequence numbers, retention, identities | Always-running lifecycle, sleep/login/restart handling, privacy exclusions, storage cleanup; starts with no past history; polling can miss rapid changes | Revisit only for an explicit stronger event-history requirement |
| Switch to another clipboard manager | May supply a supported API | User migration and a new operational dependency; still needs Bob snapshot semantics | Not justified by this incident |
| Use current macOS pasteboard APIs alone | Native access to current items and change counter | Current multi-item contents are not a chronological history API | Useful for current-read consistency, not historical recovery |

### Why a private Alfred adapter is reasonable, but not magically stable

Alfred staff have published a read-only SQLite workflow using `clipboard.alfdb`, selecting text rows with `dataType = 0` and sorting by `ts`. They explicitly characterize direct database access as a workaround rather than a supported API. The observed schema matches that approach. This makes an isolated, tested compatibility adapter credible; it does not justify spreading Alfred SQL throughout the planner. [Alfred staff implementation](https://www.alfredforum.com/topic/18061-accessing-clipboard-history-inside-a-workflow/)

Alfred also documents `{clipboard:x}` history placeholders and external workflow triggers. Those give a supported route to ask Alfred to resolve history, but the documented trigger is an invocation interface, not a synchronous history-list return API. A bridge would need safe framing, request IDs, cancellation, a bounded reply path, and no temporary overwrite of the user's clipboard. Do not interpolate clipboard text directly into shell source or hand-built JSON. A small proof of concept should establish exact count limits, ordering, and concurrent-copy behavior before preferring this route. [History placeholders](https://www.alfredapp.com/help/features/clipboard/accessing-clipboard-history/), [External triggers](https://www.alfredapp.com/help/workflows/triggers/external/)

Raycast's documented API supports clipboard history offsets from 0 through 5, which is a useful bounded capability but not a drop-in arbitrary-count provider. There is no reason to adopt Raycast just to repair an integration on an Alfred machine. [Raycast Clipboard API](https://developers.raycast.com/api-reference/clipboard)

Do not claim modern macOS has no clipboard history: Apple documents Spotlight history. The AppKit API examined here exposes the items currently held by the pasteboard, and its change counter tracks ownership changes. I did not find a documented general-purpose API for enumerating Spotlight's historical entries; that is a research limitation, not proof none can exist. Do not reverse-engineer another private store for this fix. [Apple Spotlight history](https://support.apple.com/en-ie/guide/mac-help/mchl40d5b86b/27/mac/27), [AppKit items](https://developer.apple.com/documentation/appkit/nspasteboard/pasteboarditems), [AppKit change count](https://developer.apple.com/documentation/appkit/nspasteboard/changecount)

## 5. Recommended design

### Provider resolution stays in Bob

Introduce a small internal provider boundary that returns structured entries and capability/health information. A useful conceptual record has provider identity and version, ordered entry IDs where available, timestamps with known precision, supported content types, and an ordering-quality indicator. These are proposed fields, not an existing wire schema.

Keep the legacy command override working. Add normal configuration for selecting Alfred, Clipy, a custom command, or no history. An explicitly configured command or provider takes precedence; a provider failure never activates another provider. If automatic discovery is retained, it should suggest or select only an unambiguous supported active provider and refuse ambiguity. A leftover database is not enough to win discovery. On this machine the intended choice is Alfred.

Avoid a permanent UI confirmation on every capture. Show a compact source label and useful errors; require setup only when source selection is ambiguous or unavailable. Ensure the GUI and shell resolve the same Bob configuration, rather than relying on shell startup exports that a launched app may not inherit.

Add a metadata-only diagnostic surface through the project's existing conventions. It should report effective provider, why selected, app/version/liveness, database location, schema compatibility, supported types, newest timestamp, and error state. Never dump history contents, full command environment, or secret-bearing stdout/stderr by default.

### Acquire one bounded snapshot, then select and plan

Resolve the largest clipboard count requested by the draft once and reuse its prefixes for the draft's clipboard items. Keep the fanout sharing already present. Bind the snapshot to the resolved provider/configuration and the capture request.

For a database provider, open through SQLite read-only and hold a short read transaction across the entire selected-entry read. Use a bounded busy timeout; retry only transient lock/race conditions, with a total deadline. Do not copy just a live `.db` file, mark a changing database immutable, change its journal mode, run migrations, or checkpoint someone else's database. SQLite's transaction and WAL rules explain why reads must include the real database state and why transactions should be short. [SQLite isolation](https://www.sqlite.org/isolation.html), [SQLite WAL](https://www.sqlite.org/wal.html)

Bracket the live/history acquisition with the macOS pasteboard generation counter where available. If it changes during acquisition, discard and retry a small bounded number of times. This handles concurrent current-clipboard changes; it does **not** prove that the manager has finished recording or has not excluded the item. A read-only historical database cannot establish that causal fact by itself.

Keep live first for compatibility. Remove a redundant history item only according to a documented provider policy. For a legacy string-only provider, prefer suppressing a matching head rather than searching arbitrarily deep for equal text; call out the behavior change and preserve historical repeats. For providers that deduplicate by content and may update asynchronously, use stable metadata where available and admit ambiguity. If an exact association cannot be established, show the resolved selection and rely on the preview binding rather than claim event identity.

Determine the selected candidate positions before decoding surplus candidates, while validating every selected entry. No selected entry may disappear silently. At most one preferred textual representation should stand for a logical text item; actual multi-file lists remain lists. A retained Clipy adapter needs explicit tests for its flattened schema and should refuse ambiguous unsupported structures instead of concatenating all flavors.

### Bind preview and submission without building a history store

Prefer an **expected selection fingerprint** over a new durable cache of clipboard payloads:

1. Bob resolves one selection for preview and returns an opaque fingerprint covering provider/config identity, requested counts, ordered normalized content, and relevant attachment bytes or identity checks.
2. The Mac app displays Bob's result and returns that expectation when submitting the unchanged draft.
3. Bob acquires one new selection. If the content or provider differs, it refuses before writes with a stable “clipboard changed; review updated preview” result. The app retains the draft and refreshes the preview.
4. If the expectation matches, Bob plans and commits using that same acquired selection, never reading the clipboard again later in the command.

The expectation should concern the selected content, not unrelated database rows or timestamps alone. An unrelated old-row deletion should not block a matching selection. A file attachment changing underneath the same path must not slip past validation. This design offers reviewed-content consistency without retaining another history archive; the cost is an occasional refresh when the clipboard changes at an inconvenient moment.

A CLI call without a supplied preview expectation can still capture the current snapshot once. Keep that intentional difference explicit. Do not silently auto-submit after a mismatch: that would negate review.

New JSON fields should be additive, and Mac decoders must tolerate their absence. Negotiate capability before sending new options. Keep grammar, provider selection, content classification and planning in bob-cli; Swift renders results and manages presentation. This follows the accepted `decisions:mac-capture-is-a-thin-client` memory reviewed for this investigation.

### Command providers remain an escape hatch

Preserve the existing newest-first JSON-array command protocol for compatibility, but label its weaker metadata guarantees. An eventual versioned structured response can add provenance and IDs without making that a prerequisite for the Alfred fix.

Support an argv array in new configuration rather than introducing shell evaluation. Bound execution, stdout bytes, count, and payload size; terminate and reap timed-out child processes, including appropriate process-group cleanup. Map failures to actionable classes such as unavailable provider, unsupported schema/type, insufficient entries, timeout, read race, and preview mismatch.

## 6. Delivery and acceptance criteria

This is a proposed implementation sequence, not changes performed by this research turn.

**First deliverable: correct source and visible failure.** Add the provider boundary, explicit Alfred selection, metadata diagnostics, short transactional reads and schema/type checks. Preserve `%c` and existing atomic-write behavior. Add source provenance to counted previews. Retain Clipy as an explicit supported option only to the extent its decoder is validated.

**Second deliverable: consistent selection.** Acquire once per invocation; fix surplus-candidate validation; define duplicate and tie handling; fix Clipy representation handling if it remains supported. Add bounded custom-command execution. Benchmark real Mac reads rather than guessing acceptable latency.

**Third deliverable: preview guarantee.** Add fingerprint capability to Bob and the Mac client, keep drafts on mismatch, and verify changed attachments. Build and test the actual macOS targets in CI; portable tests cannot establish AppKit integration behavior.

| Acceptance case | Required behavior |
| --- | --- |
| `%c` with no history manager | Current-only capture continues to work |
| Alfred running; stale Clipy DB remains | Explicit Alfred is used; Clipy never supplies fallback entries |
| Configured manager unavailable or schema changed | Clear provider-specific refusal before writes |
| Multiple active supported managers | Explicit configuration or an ambiguity error, never nondeterministic choice |
| Controlled copies `A`, `B`, `C` | `%c3` resolves `C`, `B`, `A` under the documented saved-entry policy |
| Rapid same-second copies and recopies | Deterministic display; no unsupported promise of exact event order |
| Current value omitted by provider exclusions | Documented live-plus-saved-history behavior; no attempt to resurrect excluded history |
| URL plus text representations; multiple files | One logical value per entry; no duplicated flavor content |
| Unsupported selected clip, too few entries, deleted attachment | Whole capture refuses; no vault or attachment writes |
| Invalid candidate beyond selected positions | Does not invalidate a complete valid selection |
| Two clip directives in one draft | Both use the same acquired snapshot/prefixes |
| Copy or history edit after preview | Submission rejects a different selection and preserves the draft |
| Unrelated history edit after preview | Matching selected content remains usable |
| Locked DB, truncated JSON, oversized output, hung child | Bounded, typed failure; no orphan provider process |
| Read-only database with WAL and concurrent clear | Coherent snapshot or explicit bounded failure |
| Terminal versus launched Mac app | Same effective provider configuration and content policy |

Run the live sentinel-copy acceptance exercise intentionally on the Mac during implementation, because it changes the system clipboard and histories. This research did not perform that mutation. Fixtures should include the observed Alfred schema and timestamp ties, synthetic native Clipy assets, and repeatable read-race hooks; they should not include personal clipboard contents.

## 7. Remaining uncertainties

- The exact environment and payload of the user's original failed request were not examined. Installed help, active-manager metadata and default source behavior make the diagnosis strong, but do not substitute for the final controlled reproduction.
- Alfred's database format is not a stable public contract. Text schema support is directly corroborated; native images, file lists, recopy behavior, and exact same-second UI ordering need targeted validation.
- A manager can be running while recording is paused or filtering a source app. No single process check, database age threshold or content comparison proves completeness.
- A provider API or database may have already discarded intermediate events. Bob cannot recover them by improving its read logic. If exact copy-event order is essential, the requirements need an explicit recording mechanism and its associated lifecycle work.
- The proposed time/count/size limits and latency goals need measured calibration. This report does not claim performance measurements it did not take.

## Recommended solution

**Implement an explicitly configured, read-only Alfred text-history adapter in bob-cli, backed by one provider boundary, visible provenance, bounded snapshot reads and exact-count refusal. Preserve `%c` as current-only and `%cN` as live plus saved history. Bind Mac previews to the selected content at submission, with a changed-content refusal and draft retention.**

This directly addresses the strongly evidenced wrong-manager failure and the independent correctness gaps without asking the user to run a second recorder. Keep a supported Alfred workflow bridge as the next alternative if private-schema maintenance becomes costly. Build Bob-owned history only if the user explicitly needs guarantees that Alfred's retained history cannot supply.
