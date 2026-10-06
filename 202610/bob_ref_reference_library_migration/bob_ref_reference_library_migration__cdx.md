# Migrating `bob highlights` to `bob ref`: a reference catalogue for people and agents

Researcher: **cdx** · Date: **2026-10-06**

## Assessment

**This is a good idea if `bob ref` becomes a small, reliable view of the existing reference collection.** The name describes the material rather than the application that imports it, and the vault already contains most of the information needed. Preserve the Highlights pipeline and add read-only catalogue and annotation commands around it.

The important work is not the rename. It is exposing trustworthy reading-state evidence, matching old and new source identities, and making missing information explicit. A command that merely lists `status: read` would omit substantial historical material; one that assumes highlights imply completion would mislead recommendation agents.

My recommendation is a native, Markdown-first catalogue with `list`, `search`, `show`, `annotations`, and `stats`, plus all six existing commands. Keep `highlights` as a permanent hidden alias. Start without a new database, embeddings, PDF-dependent queries, or another reading-state field. Add durable completion history and reference mutation only as separate, deliberate extensions.

## Investigation and evidence boundaries

I independently inspected bob-cli at `ce54258121bd567344f603311a4792299cd05185`, bob-plugins at `9e69a9d4242f30732755aeae2cf6c45c00e5aa75`, the audited project/home memories for CLI rules, Obsidian, artifacts, reference notes/tasks, and current task-lane/review decisions. I queried the actual vault through the read-only `bob_query` skill and `bob query` native engine. The installed executable reports `bob 0.1.0`; that version alone does not establish its exact build commit.

I consulted official Highlights and Zotero documentation. I did not consult this swarm's other reports, transcripts, summaries, or researchers. No implementation or vault mutation was performed. The counts below are observations of the local vault during this investigation, not a synchronized census of every machine or a comprehensive account of everything Bryan has ever read. No live MacBook export/write-back validation was performed.

Source links are collected in the evidence section and cited throughout. Repository links are pinned to the inspected commits.

## What already exists

`bob highlights` currently has **clip, create, doctor, marker, scan, and sync**. `clip` captures a URL to a PDF, `create` renders Markdown to a PDF, `scan` handles intake and recursive synchronization, `sync` processes one PDF, `marker` inspects PDF metadata, and `doctor` checks prerequisites. There is no dedicated catalogue or structured annotation-query command in this group. [B1, B2]

The pipeline is already more than an annotation exporter:

- Library PDFs live under `lib/`; intake lives under `xlib/`; generated notes live under `ref/`, retaining nested library-relative paths.
- Notes carry `type: "[[ref]]"`, path-derived `ref_type`, source/provenance metadata, and a reading tracker ending in the exact block ID `^ref`.
- The tracker maps `[ ] → ready`, `[*] → next`, `[/] → wip`, `[x]`/`[X] → read`, and `[-] → abandoned`. Deprecated `unread` and `done` inputs normalize to `ready` and `read`. `legacy` is also supported.
- Marker and note metadata use a stored base/hash for reconciliation. The tracker contributes a status signal; conflicting independent status edits are rejected.
- Generated annotations live between `<!-- highlights:begin -->` and `<!-- highlights:end -->`. Content outside that region is preserved. Quotes, comments, standalone notes, image selections, and removed-annotation tombstones have distinguishable renderings and existing `^h-...` anchors.
- Annotation-derived follow-up tasks are independent of the source-level reading task. Completing a follow-up task does not mean the reference is finished. [B1, B3–B6]

**Clarification to the request:** Highlights itself autosaves a same-name Markdown/TextBundle sidecar beside the PDF. Bob imports that content into the separate reference note under `ref/`. Highlights warns that it overwrites external edits to its sidecar. Therefore, read Bob's reference notes for the new catalogue and annotation commands; leave sidecars owned by Highlights. [Official Highlights sidecar documentation](https://highlightsapp.net/how-to/mac/sidecar-files/), [B1]

There is also an important current limitation: a note-side lifecycle change that requires PDF marker write-back makes a writing sync refuse without `--write-pdf`/`--write-pdfs`. The refusal occurs before sidecar rendering. Consequently, checking a reading task can leave the frontmatter and imported annotations behind until synchronization succeeds. A read API must report the live note's evidence without calling the writer or treating the last import as live MacBook state. [B3]

## What the actual collection looks like

The following census uses `FROM "ref"`, rather than widening membership to every note whose `type` links to `ref`.

| Current frontmatter status | Notes |
| --- | ---: |
| `read` | 285 |
| `legacy` | 282 |
| `abandoned` | 17 |
| `next` | 5 |
| `ready` | 1 |
| `wip` | 0 |
| **Total** | **590** |

The `^ref` task-mark census found 308 tasks: 285 `[x]`, 17 `[-]`, five `[*]`, and one `[ ]`. Its distribution agrees with the non-legacy frontmatter totals; aggregate agreement alone is not proof of row-by-row consistency.

| `ref_type` frontmatter | Notes |
| --- | ---: |
| `chat` | 286 |
| `docs` | 11 |
| `blogs` | 6 |
| `papers` | 5 |
| Missing | 282 |

The 282 legacy notes preserve these older values:

| `legacy_status` | Notes |
| --- | ---: |
| `unread` | 144 |
| `collect_fleeting_notes` | 92 |
| `read` | 25 |
| `review_fleeting_notes` | 13 |
| `abandoned` | 4 |
| `review_lit_notes` | 4 |

Additional observations:

- **283** notes have a non-null `url`; only **two** have a non-null `source_url`. These counts do not establish the union or validity of every URL. Two sampled legacy `url` values were ordinary source article URLs.
- **123** notes have non-null `highlights_count`: **115** positive counts and **eight** zero counts. **467** lack that field. Missing counts do not prove a lack of annotations or authored notes.
- A type-based query found **13 additional notes outside `ref/`**, all root-level reference index notes such as `ai_ref.md`, `obsidian_ref.md`, and `sase_ref.md`, with no status. Automatically including every `type: [[ref]]` would include these indexes as though they were individual readings.

These observations materially change the design. URL compatibility and legacy-state evidence matter immediately. Type filtering cannot assume every old item has a `ref_type`. Captured chats should remain accessible, but agents seeking articles and papers need an explicit filter or profile so chats do not dominate results.

The queries emitted pre-existing ambiguous-link warnings. Grouped JSON additionally warned that group rows have no source-note path; its numeric table remained available. I used scalar status/URL/count results and task block IDs for the census, not ambiguous wikilink destinations. Failed or unsupported metadata introspection was not used as evidence.

Reproducible DQL is included below.

## Critique and adjustments to the requirements

### 1. Separate inventory, engagement, and completion

A reference being present establishes that it is tracked. A Ready/Next tracker establishes its current queue position. A WIP tracker establishes the current workflow lane. A completed tracker establishes an explicit completion signal. Highlights establish recorded engagement with passages; they do not establish that the entire source was read.

Current task policy makes Next and Pending sticky. In particular, `[/]` can persist while work waits; it should not be advertised as proof Bryan is reading the source right now. Preserve `wip` as the stored value and describe the lane accurately. Do not introduce a competing field named `reading_status` just to translate the checkbox vocabulary. [M1, B7]

**Adjustment:** expose current status, status provenance, annotations, and explicit completion evidence separately. If agents want an “engaged” view, compute it from observable signals and return the reasons. Do not store a new automatic “partially read” status.

### 2. “Already read” is not identical to “currently completed”

The existing contract permits reopening `[x]` to `[ ]` or `[/]`. That removes current completion, but does not erase the fact that the reference was previously read. The present lifecycle is a current-state model, not a durable reading history. Neither note creation time, file modification time, `captured`, nor `highlights_synced_at` is a completion date. [B1, B6]

**Adjustment:** distinguish `current_status` from `read_before`. Return `read_before: true` when there is explicit evidence: current `read`, an explicit retained completion record, or `legacy_status: read`. Return `null` when history is unknown. Do not return `false` merely because a reference is Ready, Next, abandoned, or absent from the vault.

For legacy notes, expose the original value and the exact evidence. The 25 `legacy_status: read` notes contain useful historical completion evidence even though their current lifecycle remains `legacy`. Do not silently turn the 92 note-collection and 17 note-review states into `read`; their workflow names are suggestive, but this investigation does not establish their completion semantics.

Persistent history is a worthwhile later addition: for example, a note-local completion-evidence flag and known completion dates preserved across reopening, written through an explicit completion workflow. Coordinate that with Obsidian completion gestures and synchronization. Do not backdate historical completions from filesystem timestamps. A read-only first release can expose existing evidence; it cannot guarantee retention of every future completion/reopen event.

### 3. Keep all references, including sources without PDFs

The collection already contains URL references and legacy notes. A read API should not require a PDF, marker, managed Highlights region, or `^ref` task just to list them.

**Adjustment:** define the default catalogue as ordinary reference Markdown notes under the configured reference-note root, including legacy records. Exclude hidden directories, conflict copies, templates, asset directories, and sidecar containers. Validate `type`, status, and identity fields, but do not expand membership solely by `type: [[ref]]`. Missing or invalid metadata becomes a visible diagnostic.

Keep missing `ref_type` as unknown. Path components or parent indexes can be displayed as organizational hints; they are not proven media types. A curated article/paper view may need reviewed classification of old items rather than assuming that everything in an AI folder is a paper.

### 4. Identity matching matters more than recommendation machinery

A recommendation agent needs to know whether a candidate is already tracked or read, including URL spelling variants and older `url` fields. A second implementation of recommendation ranking is unnecessary.

**Adjustment:** normalize metadata into a common read model while preserving raw fields:

- Read both `source_url` and `url`. Prefer the documented modern field for display, but retain both as aliases when they differ and flag disagreement.
- Match exact URLs and existing clip-compatible normalization before considering title similarities. Preserve meaningful URL parameters; do not invent redirects or publisher/preprint equivalence.
- Support explicit DOI/arXiv identifiers when present. Grouping versions or treating a PDF URL as equivalent to its landing page requires actual identifier evidence or a declared alias.
- Use exact vault-relative note paths as unambiguous locators. Existing `id` is often a basename and is not guaranteed globally unique.
- Do not use the annotated PDF's SHA-256 as the work's identity: annotation/marker writes can change the bytes.
- Return multiple matches and match reasons. A title match is a candidate, not proof that Bryan read the same work.

The current clip code already contains URL cleaning/dedupe logic, but its note scan reads `source_url`, not old `url`. Reuse and test that identity logic for the new reader; changing capture refusal behavior should be an explicit separate change. [B8]

Do not derive a reference's identity from every DOI or URL mentioned inside its annotations. A cited paper in a quote is not necessarily the paper represented by the note.

### 5. Treat catalogue and annotation results as snapshots

A query on Linux can reliably read synchronized Markdown without the Highlights app. It cannot prove there are no unsaved annotations on the Mac. `highlights_synced_at` describes an import, not necessarily the last successful scan or the source's current state. A missing sidecar currently preserves an existing imported region. [B1, B6]

**Adjustment:** return snapshot provenance and availability, with PDF/sidecar validation explicitly unperformed during ordinary queries. A zero imported count means an empty recorded snapshot; an absent count means unknown. Age alone does not prove a snapshot is stale.

`clip` and `create` also write intake PDFs before a reference note exists. A note-only catalogue can miss newly queued intake. Declare `coverage.intake: not_checked` by default. Use existing `doctor`/`marker` for explicit intake inspection; if immediate queue visibility becomes necessary, add an opt-in intake query using the existing intake marker reader. Do not make all catalogue queries traverse PDFs. Intake availability can differ by machine because `xlib/` is outside vault Git sync coverage. [B1, B8, M1]

### 6. Preserve compatibility and avoid a simultaneous data migration

Project CLI rules require permanent hidden aliases, no deprecation output, canonical command names in help/diagnostics, alphabetical options/subcommands, and a short alias for every public long option. This rules out removing `bob highlights` or warning on every scheduled invocation. [M1]

**Adjustment:** make `bob ref` canonical and redirect `bob highlights` to the identical handler. Keep the existing `highlights:` configuration, `BOB_HIGHLIGHTS_*` variables, hook guard, managed-region delimiters, provenance keys, block IDs, and automation labels. They describe an integration and remain valid. Namespace migration does not require renaming stored fields or every LaunchAgent.

I would keep bare `bob ref` showing help in the first release, matching the existing group's shape. A later bare default to the read-only `list` member is allowed by policy, but should be implemented deliberately rather than accidentally falling into `scan` or another writer.

## Proposed command surface

All commands are members of one noun: **operations on Bob's reference collection and its intake/import pipeline**. Put the canonical group in the Vault help section, reflecting its broader role. Preserve these paths with their existing arguments and behavior:

```text
bob ref clip URL
bob ref create MARKDOWN
bob ref doctor
bob ref marker PDF
bob ref scan
bob ref sync PDF
```

Add:

| Command | Purpose |
| --- | --- |
| `bob ref list` | Filter and enumerate references, including legacy/unknown state |
| `bob ref search QUERY` | Search metadata by default; opt into notes/annotations; exact source-URL lookup |
| `bob ref show REFERENCE` | Inspect one record, provenance, diagnostics, and optionally the original note |
| `bob ref annotations REFERENCE` | Retrieve imported quotations, Bryan's comments, standalone notes, and image references |
| `bob ref stats` | Counts by state/type and metadata/annotation coverage |

Representative usage; these are **proposed commands**, not currently installed commands:

```bash
bob ref list -s read -f json
bob ref list -s ready,next,wip -f markdown
bob ref list -s legacy -f json
bob ref list -t blogs,papers -a -f json
bob ref search 'agent memory' -f json
bob ref search -u 'https://example.org/article' -f json
bob ref search 'retrieval' -i annotations -f json
bob ref show ref/papers/example.md -f json
bob ref show ref/papers/example.md -R
bob ref annotations ref/papers/example.md -n -f markdown
bob ref stats -f json
```

Use `-f/--format` for `table|markdown|json`; `-s/--status`, `-t/--ref-type`, `-u/--url`, `-i/--in`, `-n/--notes-only`, `-R/--raw`, and `-a/--all` are illustrative short/long pairs. Existing `-b/--bob-dir` and `-r/--ref-dir` retain their meanings; therefore raw cannot reuse `-r`. Give any additional limit/sort/topic flags short aliases too. URL-only search accepts an omitted text query. `--raw` prints the exact note and is incompatible with structured formatting options.

Use the same filters and record normalizer across commands. Status filtering targets effective current status and supports `legacy` plus explicit `unknown`/`conflict` query categories, without adding those categories to stored PDF status values. Repeated/comma-separated filters should have a documented OR rule within each field and AND between fields. Search content modes distinguish metadata, authored notes, imported annotations, and all; task plumbing should not contaminate authored-note search by default.

Resolve a full note path first, then a unique explicit `id` or basename. Ambiguity is an error with candidate paths; never silently select the first stem match. Human display can be compact and colored. JSON must contain no ANSI escapes, prose prefixes, or mixed diagnostic lines on stdout.

Choose a documented default result limit, for example 50, consistently across formats. Always include `matched`, `returned`, `truncated`, and scope in structured results; provide `--all` for complete enumeration. Never let a recommendation agent mistake a page of results for the whole library. A later batch match interface is useful if repeated URL lookups become expensive, but is not necessary for the first coherent release.

### Record and response contracts

A versioned JSON envelope should identify its schema, local generation time, scope, and completeness. A compact catalogue item might look like this illustrative example:

```json
{
  "schema_version": 1,
  "coverage": {"corpus": "reference_notes", "intake": "not_checked"},
  "matched": 1,
  "returned": 1,
  "truncated": false,
  "items": [{
    "reference_path": "ref/papers/example.md",
    "id": "example",
    "title": "Example Paper",
    "ref_type": "papers",
    "source_urls": ["https://example.org/paper"],
    "source_pdf": "lib/papers/example.pdf",
    "current_status": "read",
    "status_evidence": {"source": "ref_task", "mark": "x"},
    "frontmatter_status": "read",
    "legacy_status": null,
    "read_before": true,
    "completion_date": null,
    "annotation_snapshot": {
      "imported_count": 4,
      "synced_at": null,
      "source_verified": false
    },
    "diagnostics": []
  }]
}
```

Keep quote/comment bodies out of list responses by default; fetch details for selected records. `null` communicates missing evidence rather than a guessed value. Include match provenance on search results and explicit history provenance when `read_before` comes from legacy metadata.

For status normalization, reuse the existing lifecycle mapping and conflict principles:

1. Validate one genuine `^ref` tracker, its supported mark, `#task`, and PDF link. Legacy omission of `#ref`/`#hide` remains accepted. Ignore fenced examples when identifying a real tracker; malformed or multiple trackers produce diagnostics.
2. If tracker and frontmatter agree, report that state.
3. If the tracker differs while frontmatter still matches the stored base, report the tracker state with pending reconciliation. Reading does not require PDF access or write-back.
4. If note-local evidence proves independently conflicting edits against the base, report conflict rather than manufacture a settled state. Return the underlying signals. Do not claim that the PDF marker was checked.
5. Without a tracker, normalize valid frontmatter status; otherwise report legacy/unknown as appropriate. Never require a generated PDF task on a URL-only legacy note.

This reader should not call the full `plan_pdf_sync` path: that path opens the PDF and enforces marker reconciliation requirements irrelevant to a local catalogue. [B3–B5]

## Annotation retrieval design

**Read the imported managed region in `ref/`, rather than reparsing live sidecars or opening PDFs.** This is the representation that reaches headless agents through vault synchronization and already has citation anchors. Keep exact raw-note retrieval as a fallback for old/unrecognized formats.

The typed annotation record should carry:

- Reference-note path and source PDF path if known.
- Existing `h-...` anchor and a resolvable `[[ref/...#^h-...]]` citation target.
- Kind: text highlight, standalone note, image selection, or removed annotation.
- Page label exactly as recorded; a page number only when confidently recoverable.
- Separate quote text, user comment, standalone note text, and asset path.
- Snapshot provenance and parsing diagnostics.

`annotations --notes-only` should return comments and standalone notes, retaining enough quote/page context to interpret them. It must not present all quoted article prose as Bryan's own position. Image annotations can return their asset and comment without OCR; image-only content should not vanish because it has no searchable text.

Exclude removed-annotation tombstones from normal searches and counts; offer `-D/--removed` for historical inspection. Their block IDs remain valid historical targets, but tombstones are not live annotations. Keep `-r` reserved for `--ref-dir`.

The existing text anchor hash includes PDF path, kind, page label, ordinal on that page, and normalized text. Comment-only edits preserve the anchor; text changes, path changes, or ordering changes can affect it. Image anchors depend on PDF path and image bytes. Reuse these IDs without claiming they are immutable annotation identities. The pipeline preserves removed anchors as tombstones. [B6]

A practical parser can recognize Bob's known generated callout contract and retained historical formats. For unknown markup, return raw content with `structured_annotations_available: false`, rather than silently discarding it or claiming zero annotations. Do not change generated formatting solely to make the new reader easier to write. Annotation retrieval is read-only and must never import follow-up tasks or rerender notes.

## Architecture and alternatives

### Recommended implementation structure

Add a small Rust catalogue module, for example `native/ref_catalogue`, containing directory discovery, read-only full-YAML metadata parsing, reference records, status evidence, annotation parsing, filtering, and output. Compose its subcommands with the existing Highlights command builder.

Reuse lifecycle/marker vocabulary and URL identity utilities through a narrow `pub(crate)` boundary; avoid copying status tables into unrelated parsers. Existing Highlights frontmatter parsing is tailored to line-preserving marker projection, whereas Dataview already uses `serde_yaml` for general YAML. A reader must support multiline/list metadata such as authors/topics without rewriting the writer. Share appropriate metadata/Markdown primitives rather than invoking DQL subprocesses internally. [B4, B5, B8, B10]

Initially read only the configured reference tree. With 590 notes, a simple scan is a reasonable starting hypothesis, but measure latency with cold and warm caches before claiming a performance target. Existing native DQL builds an index of the whole vault before source selection and emitted unrelated link warnings during this research; wrapping it would inherit those costs and diagnostics. [B10]

If repeated queries justify caching, use an untracked, rebuildable local cache keyed by parser/schema version and file identity/content changes. Markdown remains authoritative. SQLite FTS or semantic retrieval can follow measured need; neither belongs in the initial migration merely because the consumer is an agent.

### Alternatives considered

| Approach | Strength | Why I would or would not choose it |
| --- | --- | --- |
| Saved `bob query` DQL and shell snippets | Available immediately; no new domain code | Good interim solution; lacks a stable reading-evidence, identity, and annotation contract |
| Native `bob ref` over existing notes | Fits Bob, works headlessly, preserves workflows | **Preferred:** small domain layer, with deliberate ambiguity and snapshot handling |
| Dedicated database as the source of truth | Flexible querying and history | Adds synchronization/migration burden and competes with task/frontmatter/PDF state |
| Zotero as the main reference manager | Rich source management, tags, linked annotation notes | Reasonable if bibliographies/citation workflows become dominant; larger migration than this use case needs |
| Embeddings/vector store first | Semantic discovery | Does not establish exact source identity or reading completion; requires maintenance and evaluation |

Zotero documents colored tags for “to read” organization and annotations inserted into notes with page links/citations. Its built-in reader stores annotations in its database unless exported into a PDF. It is a credible alternative for scholarly reference management, but moving to it now would introduce another ownership/synchronization boundary into an already working Highlights/Bob workflow. That conclusion is my inference from the documented capabilities and the current local architecture. [Zotero collections and tags](https://www.zotero.org/support/collections_and_tags), [Zotero PDF reader](https://www.zotero.org/support/pdf_reader)

### Mutations should be a separate phase

A future `track` or `set-status` command is useful, but substantially more involved than read-side enumeration. It must preserve required parents, update the visible tracker and note status coherently, respect task-lane policy, and handle PDF marker reconciliation without writing PDFs implicitly.

URL-only stubs also interact with current clip dedupe: a tracked `source_url` is already enough for clip to refuse capture. Adding `track` without an adoption path would prevent later PDF capture of the same item. An explicit adoption/attachment operation would need to preserve authored prose and establish the managed-region contract. Resolve that before shipping URL-stub creation, rather than quietly redefining `clip` or `create`. [B8, M1]

## Delivery sequence and validation

This is a suggested implementation sequence, not an implementation performed by this report.

1. **Namespace compatibility.** Register `ref` as the sole canonical root; add `highlights → ref` to `runner::ALIASES`; update `COMMAND_NAME`, help text, completion descriptors/kinds, docs, and canonical examples. Keep the internal `NativeCommand::Highlights` name if that avoids unrelated churn. Do not mount the same native command twice: runner tests enforce one canonical path. [B2, B9]
2. **Read model and inventory.** Add note-scoped membership, old/new URL handling, status evidence/conflicts, legacy history evidence, filters, versioned JSON, `list`, `show`, `search`, and `stats`. Ship clear coverage limits before claiming comprehensive reading history.
3. **Imported annotation interface.** Add `annotations`, comments-only retrieval, metadata/content search scopes, existing anchor citations, image records, tombstone exclusion, and raw fallbacks. These steps together satisfy the first release's useful agent workflow.
4. **Optional history and mutation improvements.** Preserve completion evidence across reopening; consider intake visibility, batch candidate lookup, URL tracking/adoption, and completion dates. Evaluate an annotation-only import mode if lifecycle write-back refusals regularly block annotation freshness. Any such mode must preserve the existing `sync`/`scan` behavior by default and remain an explicit operation.

Necessary implementation checks:

- Compare old and canonical invocations for all six legacy members: stdout, stderr, exit status, and resulting files must match under a fixed test clock. Include help/error paths and the existing parent `--no-hooks` behavior. No deprecation text.
- Verify canonical help/completion paths, hidden-alias acceptance, alphabetical ordering, short aliases, completion providers, and the existing runner command-tree invariants.
- Use mixed-corpus fixtures: generated PDFs, URL-only legacy notes, missing type/status, root index notes outside the corpus, multiline metadata, duplicate stems/IDs, conflicting URL fields, and malformed YAML/trackers.
- Test every lifecycle mark and aliases, unsynchronized tracker edits, proven conflicts, reopening, and retained legacy `read` evidence. Ready must never automatically mean “never read.”
- Test comments versus quotes, standalone notes, images, historical formats, removed blocks, unchanged anchors, and raw fallback. Counts exclude tombstones and agree with retrieved live records.
- Verify queries perform no writes, spawn no hooks, access no PDFs, and need neither Obsidian nor pandoc/browser/Highlights. Structured output stays valid JSON even with diagnostics; malformed records are reported rather than silently lost. Fatal root/read errors exit nonzero; no-match results are valid empty results with explicit scope.
- Measure scanning before choosing caching. Validate annotation snapshots against real Highlights-exported Mac files before promising format completeness. Existing fixtures are explicitly synthetic. [B11]

An agent-facing acceptance exercise should include: an already-completed paper, a legacy paper with explicit old completion, a queued source, a title near-match, an unknown-history source, and a recently clipped intake-only source. Correctly distinguish these cases and show why each was classified. That is a more useful gate than merely testing that a table contains rows.

## Reproducible vault queries

Run with `bob query -f markdown -q '<DQL>'`, or use `-f json` for structured output. These were read-only observations of the default local vault.

```dataview
TABLE WITHOUT ID key AS Status, length(rows) AS Count
FROM "ref"
GROUP BY status
SORT key ASC
```

```dataview
TABLE WITHOUT ID key AS Type, length(rows) AS Count
FROM "ref"
GROUP BY ref_type
SORT key ASC
```

```dataview
TABLE WITHOUT ID key AS Legacy, length(rows) AS Count
FROM "ref"
WHERE status = "legacy"
GROUP BY legacy_status
SORT key ASC
```

```dataview
TABLE WITHOUT ID key AS Mark, length(rows) AS Count
FROM "ref"
FLATTEN file.tasks AS t
WHERE t.blockId = "ref"
GROUP BY t.status
SORT key ASC
```

For URL/count coverage, replace the grouping expression with `(url != null)`, `(source_url != null)`, or `(highlights_count != null)`. For positive imported counts, add `WHERE highlights_count != null` and group by `(highlights_count > 0)`. To audit type-only scope expansion:

```dataview
TABLE WITHOUT ID file.path AS Path, status AS Status
WHERE type = [[ref]] AND !startswith(file.path, "ref/")
SORT file.path ASC
```

## Evidence references

- **B1 — Existing pipeline and note contract:** [Highlights reference sync documentation](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/docs/highlights-ref-sync.md), particularly synced properties, generated body, task lifecycle, and scheduled scan; [web clip contract](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/docs/highlights-clip.md).
- **B2 — Existing command surface:** [Highlights CLI builder](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/highlights_ref/cli.rs#L19-L53), [native dispatch](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native.rs).
- **B3 — Planning and write-back refusal:** [sync planning](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/highlights_ref/sync.rs#L233-L325).
- **B4 — Lifecycle recognition and conflict signals:** [tracker parser and status contribution](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/highlights_ref/annotation_tasks.rs#L576-L790), [status types](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/highlights_ref/model.rs#L94-L195).
- **B5 — Existing projection/frontmatter model:** [three-way projection resolution](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/highlights_ref/projection.rs), [line-preserving frontmatter parser](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/highlights_ref/frontmatter.rs).
- **B6 — Annotation representation, IDs, counts, and provenance:** [sidecar rendering](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/highlights_ref/sidecar_render.rs#L4-L195), [note metadata and body](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/highlights_ref/note.rs#L4-L108).
- **B7 — Current plugin reference membership:** [reference collection predicate](https://github.com/bobs-org/bob-plugins/blob/9e69a9d4242f30732755aeae2cf6c45c00e5aa75/plugins/bob-ledger-tools/src/340-dashboard-views-and-plan-block.js#L170-L201). Its active-reference view is intentionally narrower than the proposed all-state catalogue.
- **B8 — URL identity and intake dedupe:** [URL cleaning/key rules](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/highlights_ref/clip_url.rs#L43-L112), [recorded source discovery and refusal](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/highlights_ref/clip.rs#L485-L652).
- **B9 — Command rename/completion integration:** [root alias table and dispatcher](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/runner.rs), [completion tree](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/completion/tree.rs), [completion argument kinds](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/completion/kinds.rs).
- **B10 — Native query/index architecture:** [whole-vault index and YAML parsing](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/dataview/index.rs), [discovery exclusions](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/dataview/sources.rs#L99-L141), [existing dependencies](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/Cargo.toml).
- **B11 — Existing test scope:** [synthetic Highlights fixtures](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/tests/fixtures/highlights_ref/README.md), [lifecycle integration tests](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/tests/cli/highlights/tasks.rs), [status unit tests](https://github.com/bobs-org/bob-cli/blob/ce54258121bd567344f603311a4792299cd05185/src/native/highlights_ref/tests/status.rs).
- **M1 — Audited local memory:** `sase memory read obsidian.md cli_rules.md sase_artifacts.md glossary:reference-note glossary:reference-task decisions:task-lanes-are-sticky decisions:review-walk-is-tiered -r 'Research bob ref read-state design, annotation provenance, CLI compatibility, and durable report registration'`. These supply the required parent, sync/intake limits, permanent hidden-alias rule, reference terminology, and current lane semantics.
- **External primary sources:** [Highlights sidecar ownership and autosave](https://highlightsapp.net/how-to/mac/sidecar-files/), [Highlights TextBundle export](https://highlightsapp.net/how-to/mac/export-pdf-annotations-as-textbundle/), [Highlights annotation view](https://highlightsapp.net/how-to/mac/view-all-pdf-annotations/), [Zotero collections/tags](https://www.zotero.org/support/collections_and_tags), [Zotero annotation notes and storage](https://www.zotero.org/support/pdf_reader). Consulted 2026-10-06; external product behavior may change.

## Recommended solution

**Build `bob ref` as the canonical, native reference catalogue over the existing Markdown notes, retaining the complete Highlights pipeline behind a permanent hidden `bob highlights` alias.** Add `list`, `search`, `show`, `annotations`, and `stats` with a versioned JSON contract, explicit coverage, conservative URL matching across `url` and `source_url`, and existing annotation citations.

Use the established reading tracker and note status for current state; preserve explicit legacy completion evidence and return unknown history honestly. Treat quotations, comments, and completion as separate evidence. Make ordinary reads work from synchronized Markdown alone, and keep intake/PDF reconciliation explicit.

Ship this useful read-side interface first. Then, if Bryan needs reliable “ever finished, even after reopening” history or agent-authored tracking, extend the completion and adoption workflows deliberately. The data census makes that second phase valuable, but it does not justify delaying a small catalogue behind a new reference manager or retrieval system.
