# Saved capture templates: automatic memory with a recoverable pop

**Researcher:** cdx · **Date:** 2026-10-16 · **Status:** independent design recommendation, not an implementation.

## Assessment

This is a good feature. A template is expensive enough to compose that using it successfully should make it available next time without another saving gesture. The existing capture panel already has the grammar, previews, placeholder colors, and keyboard habits needed to make reuse feel natural.

I recommend a **bob-owned, vault-scoped template collection with automatic deduplication and a recoverable pop in the Mac app**. Keep the requested Control-T entry point. Selecting an entry takes it out of the app's available list while its draft is active, but retains the last saved definition on disk. A successful capture updates that same entry and returns it to the top. Cancellation returns the saved original. Provide an explicit Edit → Save flow for modifications that should not create captures.

The adjustment to literal pop is deliberate: selecting a reusable asset must not destroy its only durable copy. Implementing actual deletion and then attempting to repair every cancellation and crash would introduce more complexity than the feature warrants.

## Scope and evidence

I independently reviewed the shared input, the audited `bob-cli-7w` epic and its approved plan, and current sources in both repositories. I did not inspect another researcher's report, transcript, summary, or findings.

Source snapshots reviewed:

- **bob-cli:** `a041abdb1bb2f19f7f69d304922c12c7005e1765`.
- **bob-mac-capture:** `94a4e589b12d45fec7d10347d0bc6931623bf568`.
- **Shared design context:** `bead:bob-cli-7w` and `plan:202610/bulk_capture_templates.md`, read through SASE's audited commands. Saved templates were explicitly outside that epic's scope.
- **Project rules:** audited reads of CLI rules, artifact rules, Capture/Bulk Capture glossary entries, and the decision that the Mac app is a thin client of bob.

Key local evidence:

| Reference | Source | Finding |
| --- | --- | --- |
| B1 | [bob-cli capture documentation][B1], especially “Bulk templates” | A template is one parent item plus authored child bullets; the first blank line ends its definition. Later nonblank physical lines are input rows. |
| B2 | [Template language implementation][B2] | `TemplateAnalysis` already distinguishes header, definition byte range, fields, rows, and issues. Expansion is pure and separate from vault access. |
| B3 | [Capture orchestration][B3] and [commit writer][B4] | Real capture commits only after planning; dry run skips commit. The writer stages files, checks preimages, replaces files individually, and attempts rollback on ordinary failures. |
| M1 | [Canceled draft model][M1] and [disk store][M2] | Stash entries retain complete drafts; duplicates are allowed; default capacity is 10, maximum 36. Restoring removes an entry. Disk storage is app-owned JSON in Application Support. |
| M2 | [Capture panel model][M3], approximately lines 1900–2050 | Stash opens only with an empty draft. Restoration loads the editor, then removes the stash entry. Escape retains the active draft; Control-C stashes and clears it. |
| M3 | [Key router][M4] and [stash picker view][M5] | Stash has its own routing context, arrows/Control-N/Control-P/Return, character accelerators, five visible rows, and a prominent Delete All footer. Control-T has no explicit app binding today. |
| M4 | [Process client][M6], [wire models][M7], and [README][M8] | The app runs bob for parsing, completion, preview, and one final capture. Protocol additions are decoded tolerantly. Continuous preview uses `--dry-run --no-clip`. |

This was source and design research. There was no built `target/debug/bob` in this checkout, so I did not run a live capture probe, compile Swift, measure latency, or run implementation tests. The test matrix below is proposed acceptance work, not claimed verification.

## What should be persisted?

Persist the **reusable definition**, not the successful capture draft and not its expansion. For example:

```text
@@template:
Apply to {0}! @job^apply-{1}
- **URL**: {2}

Acme acme https://example.com/careers/acme
```

The saved body is:

```text
Apply to {0}! @job^apply-{1}
- **URL**: {2}
```

Selecting it reconstructs the directive and blank separator, with the caret on the first empty input row. No previous company, URL, or block ID is supplied as sample data. Keeping old rows would turn reuse into an accidental replay hazard. The canceled-draft stash remains the place for retaining a complete unfinished draft. [B1][B2][M1]

Save every successful **real** invocation with an explicit `@@template:` declaration, including a one-row template. Increment use count once per invocation, not once per expanded row. Deduplicate by reusable content and reusable invocation defaults, within the selected vault. Repeating the same template with different rows touches its recency instead of creating another entry.

Do not infer a template from ordinary text containing braces. Do not save on parse, completion, selection, preview, `--dry-run`, `--expand`, failed validation, or a failed capture. The existing promise that `capture -E` does not access the vault or perform capture side effects should remain intact. [B1][B2][B3]

### A CLI detail that is easy to miss

Saving the body alone is insufficient for every supported CLI invocation. `CaptureRequest` also carries explicit route, section, task target, task section, and reference-routing overrides. A template captured with `--route work` can otherwise be restored into the inbox. The existing request structure makes these inputs explicit. [B9]

Store reusable invocation defaults alongside the body, including the `--no-ref` policy when supplied. Include these defaults in equivalence checks. Do not persist a priority random seed, current date, pull-in selections, or other execution-specific inputs.

The backend must return a typed invocation context on retrieval; the process client applies its allowlisted options. Never store an arbitrary shell command. Show a default destination or policy in the detail preview so it is visible to the user. A saved line/digest task reference can become stale: preserve its guard and require normal revalidation on reuse rather than silently retargeting it. For the common app-created template, this context is empty because the body contains its markers.

## Critique of literal stash semantics

The stash is a collection of pending work. Its entry moves back into the editor because that is where the unfinished work now lives. A template is a reusable definition. Its next use is usually a new set of rows, and it remains valuable even if today's use is abandoned.

Literal removal at selection creates several problems:

1. Selecting a template and then discarding the draft deletes the template without a Delete gesture.
2. A crash after selection can lose it before Control-C has a chance to write a stash entry. Retaining a draft in memory is insufficient.
3. Control-C moves the entire draft into a separate, bounded stash; overflow or capacity zero can then remove the only copy.
4. A failed capture leaves the reusable template unavailable until the active draft is resolved.
5. Making a small permanent correction requires submitting real rows unless there is a separate Save action.

These are consequences of the lifecycle, not claims of a newly reproduced defect in the existing stash. Its current behavior and store APIs demonstrate why copying it wholesale would inherit the wrong tradeoffs. [M1][M2][M3]

| Approach | Advantage | Cost | Judgment |
| --- | --- | --- | --- |
| Literal durable delete on selection | Exact stash analogy; very small happy path | Loss on abandonment; needs a recovery protocol to become safe | Reject |
| Persistent library; use always copies | Simple, familiar reusable-snippet model | Changes the requested visible pop behavior | Good alternative if the pop requirement is dropped |
| Recoverable pop; suppress selected row locally while retaining its saved record | Preserves the requested interaction; no crash-loss window from selection | Needs an origin ID and explicit lifecycle rules | **Recommended** |
| Durable global checkout/lease system | Coordinates ownership across clients and machines | Sessions, liveness, stale leases, and recovery UI for a personal picker | Unnecessary in v1 |

The recommended “pop” is presentation state, not a second persistent collection. Another CLI process may still list the saved record while the app uses it. That is intentional; templates do not require exclusive ownership. There is no timeout that guesses whether Bryan still owns a draft.

## Requirements I would adjust

These changes should be visible in the eventual implementation decision:

| Requested or implied behavior | Proposed adjustment | Why |
| --- | --- | --- |
| Pop the template when selected | Hide it from available rows for the active app draft; retain the saved original until replacement succeeds | Cancellation and crashes must not destroy reusable work |
| Re-add only when a capture is submitted | Re-add the updated definition after successful capture; also allow explicit Save in Edit mode | Correcting a template should not require manufacturing a task |
| Similar to stash | Reuse geometry, focus restoration, navigation, and restrained materials; use deduplication and search instead of duplicate draft history | Similar appearance can coexist with correct template semantics |
| Copy stash retention | Keep definitions until explicit deletion; no silent 10-entry or 36-entry eviction | User-edited reusable assets should not disappear because newer ones were used |
| New Control-T mapping | Reserve it in the main capture workflow; preserve native text editing in auxiliary fields and isolated prompts | Control-T already transposes characters on macOS |
| “Used” could include preview | Define use as successful real capture | Live previews are frequent and speculative |
| Automatic saving applies to all draft text | Save definition and invocation defaults only | Avoid replaying rows and preserve CLI behavior |

Control-T's existing native behavior is documented in [Apple's keyboard shortcuts](https://support.apple.com/en-la/102650): it swaps adjacent characters around the insertion point. Keep the requested shortcut, but document the override and test its boundaries. Do not describe it as globally unbound.

## The interaction I would ship

### Opening and choosing

Expose a quiet **Templates · ⌃T** action beside the existing stash affordance. It opens in the capture panel, not a separate management window. A fresh installation should show an instructive empty state: “Templates appear here after you capture with `@@template:`.” No modal announcement follows the first automatic save.

```text
Templates                                      ⌃T
Search templates…

▧ Apply to {0}!                          3 fields
  @job · URL child                       used today

▧ Follow up with {0}                     1 field
  @people                               used yesterday

                     Edit…                 Use ↵
```

The title is a derived summary of the parent line, or an optional user-supplied name after editing. Details show the actual body, child bullets, and any invocation defaults. Do not use `@@template:` as every row's preview title; the stash's first-nonblank-line helper would produce exactly that unhelpful result for full template drafts. [M1]

Use recent successful use as the primary ordering, with a stable ID as a tie breaker. Browsing, selecting, and changing the filter do not change recency. Search should match title, literal body text, routes, and visible defaults. A clear “Search templates…” scope follows [Apple's search field guidance](https://developer.apple.com/design/human-interface-guidelines/search-fields).

Navigation uses arrows, Control-N/Control-P, Return, and click. Typing filters the list. **Do not copy the stash's unmodified letter/number accelerators into a search field**: ordinary typing must not unexpectedly activate a template. Return or double-click uses a row; a single click selects it for inspection. Ignore repeated activation key events.

When the main draft is nonempty, opening the collection is safe for browsing and editing. Disable Use with an inline explanation, “Capture or stash the current draft to use a template.” Do not replace, append to, or automatically stash the current draft. Preserve its exact text, selection, and undo state while the library is open. This improves discoverability over the stash's current empty-draft-only entry gate without introducing a destructive replacement decision. [M2]

### Loading a reusable draft

With an empty draft, Use asks bob for the current record, then installs bob's returned draft and caret offset as one editor operation. Only after installation succeeds does the app mark that ID as unavailable locally. Keep the origin ID and revision with the active draft.

The loaded draft contains the unchanged template body and an empty rows region. It should immediately show the existing calm missing-row guidance. Get can return parse metadata from bob so immediate Control-J already inserts a plain newline, without waiting for a later parse or teaching Swift how to recognize template syntax. The existing placeholder hues remain the visual connection between definition and rows. [B2][M4][M8]

### Lifecycle of the recoverable pop

| Event | Draft | Saved record / availability |
| --- | --- | --- |
| Select template | Load fresh rows region; remember ID/revision | Original stays on disk; row hidden locally |
| Escape/hide panel | Retain draft and origin in the running app | Row remains locally checked out |
| Parse/preview/capture fails | Preserve draft and origin | Original unchanged; no use-count increment |
| Successful template capture | Clear captured draft | Upsert updated definition under the origin; clear local checkout; move to top |
| Explicit Save in template editor | Save definition without capturing rows | Update same record; make it available |
| Control-C | Existing stash stores the complete draft | Release local checkout; original template becomes available |
| Explicit Discard | Discard the draft | Release local checkout; original template becomes available |
| Quit/crash/relaunch | Follow existing active-draft retention guarantees | Original is still on disk and available; no stale lease cleanup needed |
| User removes the declaration and captures ordinary text | Capture normally | Release checkout; retain original template unchanged |

Control-C intentionally ends the template-origin association: a subsequently restored stash entry is an ordinary draft copy. If edited and captured, it participates in content deduplication as a fresh use. This avoids extending the stash file schema or making a later stash restore silently overwrite a saved template. The UI should say “Draft stashed; template kept.” This is a small, explicit difference from editing the active checked-out draft.

If template text is replaced wholesale, undo restores the document, not a durable template deletion. Reassess origin validity when the document stops being a template; do not let a stale origin attach to unrelated later text.

### Editing and deleting

Edit opens a clearly labeled definition editor inside the same panel. It has a name, the template body, visible default context if present, **Cancel**, and **Save**. It contains no old input rows and no live capture action. Return inserts a newline; Command-S saves; capture submission shortcuts cannot produce vault mutations in this mode.

Validation belongs to bob. Factor definition validation out of row expansion rather than fabricating dummy values or ignoring arbitrary errors by message text. It checks the one-item structure, authored children, placeholder syntax and dense numbering, and known literal restrictions. Row-dependent meaning and live destination validity are checked again by normal preview/capture. Saving a definition must not require a successful sample capture.

Cancel leaves the saved record unchanged. A successful edit preserves stable identity and creation time; updated time changes, while last-used time does not. An optional name is metadata, not an identity or a grammar extension. Duplicate content can be surfaced in the editor with an explicit merge/keep choice; never silently discard a user-supplied name while deduplicating.

Put per-entry Delete in an overflow/context menu, with an immediate Undo action. If it cannot be undone, confirm it. Keep Delete All out of the picker footer: it does not deserve the most prominent permanent action in a reusable collection. This follows [Apple's guidance on undo](https://developer.apple.com/design/human-interface-guidelines/undo-and-redo) and [avoiding alerts for routine undoable actions](https://developer.apple.com/design/human-interface-guidelines/alerts). A later bulk clear can live in Settings with confirmation.

### Visual treatment

Reuse the panel's width, anchored position, materials, corner treatment, and five-row scrolling viewport. Keep search and action controls fixed while rows scroll. The body preview should show at most two lines per result, with full detail for the selected entry; long definitions must not stretch the entire panel.

Use the existing template symbol family, adaptive system colors, a quiet selected-row fill, secondary metadata, and the current `{N}` slot palette. Keep field labels in addition to color so color is never the only identifier. In the selected detail, `{0}`, `{1}`, and `{2}` retain the same hues used in the editor. No gradient banner, celebration, large recency badges, or competing collection dashboard is needed.

Provide VoiceOver labels for title, field count, child count, defaults, and selected state; maintain keyboard focus on return; respect increased contrast and reduced motion. A short crossfade may connect list selection to the draft, but the panel should not jump vertically. “Beautiful” here means a calm transition from finding a known tool to entering fresh values.

## Ownership, storage, and protocol

### One semantic owner

bob should own extraction, validation, storage, deduplication, and mutation. The Mac app owns presentation and the local checkout association. The existing stash's app-owned location is not a precedent for making CLI template usage invisible to the app. An app-only store would miss direct CLI captures and require Swift to understand where template rows begin, contrary to the established ownership boundary. [B2][M4]

Add a sibling noun group, **`bob capture-templates`**, whose members manage stored reusable definitions: `list`, `get`, `validate`, `save`, and `delete`. The spelling is proposed, not an existing API. Do not add `bob capture templates`: capture's free-text grammar would consume it. The audited CLI rules explicitly require frozen `capture-*` protocol siblings and prohibit nesting under `capture`.

Suggested contract shape:

| Operation | Contract |
| --- | --- |
| `list` | Read-only summaries, revisions, scoped collection revision, stable ordering, capabilities, and query filtering |
| `get ID` | Current body/defaults plus bob-produced reusable draft, UTF-8 caret offset, and parse metadata |
| `validate` | Read-only definition diagnostics; no row execution and no sample values |
| `save` | Typed stdin request with optional ID and expected revision; validates then atomically writes |
| `delete ID` | Expected-revision guard; returns enough record data for an explicit undo save |

Use versioned JSON for the new endpoints. A bare group can default to flag-only read-only list; sort help members/options and give public long options short aliases according to repository rules. No arbitrary shell fragments cross the protocol.

Real capture already receives the original raw draft. Extract its reusable definition from bob's existing `TemplateAnalysis.block.range`; do not parse capture output text or derive a reusable body from the expansion. [B2][B9]

For a checked-out app draft, add an **advertised internal origin argument** carrying the record ID and expected revision to the single final `bob capture` invocation. The backend replaces that record as part of successful capture. Do not make the app run a separate save after receiving capture success: a quit or process failure between those two calls would break the guarantee. Fresh CLI use has no origin and deduplicates by content. Preserve existing capture JSON fields; add optional saved-template metadata, not a breaking replacement for `template`.

### Persistence location and record shape

Use local durable user data, with per-vault namespacing. My preferred initial path is:

```text
$XDG_DATA_HOME/bob-cli/capture-templates/<vault-key>/templates.json
# default base: ~/.local/share
```

The vault key is derived from bob's resolved canonical vault root, not the app's working directory or a display name. Store the resolved root in collection metadata for diagnostics. Symlink aliases of the same vault should resolve to the same collection. Moving a vault changes its namespace in v1; expose export/import or deliberate reassociation rather than pretending a path hash is a durable vault UUID. This is a known limitation, not seamless migration.

I prefer data to cache or state because these entries become editable assets. The [XDG specification](https://specifications.freedesktop.org/basedir/latest/) distinguishes user data from disposable cache and less portable action history. bob's current `bob_cli_state_dir()` is useful precedent for path resolution, but adding a data-home helper is justified here. Honor an absolute `XDG_DATA_HOME`; document the fallback and ensure app-launched bob receives the same environment as other bob operations. The app never computes or directly opens this path. [B10]

Example persisted record, with illustrative identifiers and timestamps:

```json
{
  "id": "opaque-stable-id",
  "revision": 4,
  "name": "Job applications",
  "body": "Apply to {0}! @job^apply-{1}\n- **URL**: {2}",
  "invocation_defaults": {},
  "created_at": "2026-10-16T08:00:00Z",
  "updated_at": "2026-10-16T08:10:00Z",
  "last_used_at": "2026-10-16T08:10:00Z",
  "use_count": 3
}
```

Wrap records in a versioned collection document. Derive field count and the search summary using bob; avoid making cached derived values another source of truth. A digest can accelerate equivalence checks, but compare canonical content too. Normalize line endings and outer framing only. Preserve authored whitespace, child indentation, braces, quotes, and literal text; do not collapse whitespace or resolve dates while saving.

One locked JSON document is adequate for this expected scale and easy to inspect/export. Keep all saved entries; scroll and search instead of silently evicting. Bound record/input sizes and return an explicit capacity error at a documented generous safety ceiling, rather than overwriting older assets. Local-only persistence is the initial scope; neither vault sync nor cross-machine availability is implied.

SQLite is a reasonable future choice for much larger collections or extensive history. It does not make ordinary vault Markdown changes part of the same transaction just because the template store is transactional. SQLite's [atomic commit documentation](https://www.sqlite.org/atomiccommit.html) describes transactions over its own database files; the vault remains external. There is no reason to introduce it solely for a small picker.

## Reliability boundaries and failure behavior

### Make the acknowledged save part of the final capture operation

Choose a strict, coherent default: if a real template capture reports success, its reusable definition has also been installed in the collection. Do not report a generic capture failure after vault writes have committed merely because a later best-effort save failed; users may retry and create duplicate captures.

The smallest implementation consistent with the existing code is to prepare the template-store update as a **private participant in the existing staged-file commit**:

1. Perform ordinary parsing and planning first. Failure leaves the collection untouched.
2. For a real template capture, acquire a collection lock, read the latest document, check origin revision if supplied, and build one upsert. Do not lock during typing, browsing, or preview.
3. Stage the collection's new bytes alongside the already planned vault writes, and replace the collection after the vault participants. If an ordinary write fails, use the existing rollback path for all participants and report any rollback failures accurately.
4. Return capture success only after the store replacement succeeds. Update local checkout state from that success response.

Keep library participants separate from note-facing preview/result models: the JSON file must never appear as a capture target, a task diff, an Open Note destination, or a vault link. A new library directory may be created for real writes, but list/get/validate/preview must not create persistent files.

The existing writer already takes backups and syncs temporary file contents, but it is **not a crash-atomic transaction across multiple files**. Its comments also explicitly disclaim fully serialized cross-process vault writes. Extending it preserves its ordinary-error rollback model; it does not turn several renames into a power-loss transaction. State this limitation in implementation docs. A killed process between replacements can still leave an uncertain outcome. Do not automatically resubmit captures after timeouts or ambiguous transport errors. [B3][B4]

A full durable capture journal would be a separate hardening project if stronger crash consistency is required. It is unnecessary to solve loss caused by selection: the recoverable pop retains the original without one.

### Store safeguards

- Lock a stable sibling lock file, not the document inode that gets replaced. Read-modify-write, revision checks, deduplication, and manual deletion all share this lock. Use bounded waiting and actionable busy errors.
- Write a same-directory temporary file, flush it, atomically replace the document, and sync the parent directory where supported. Set private permissions on temporary files and backups before content is written: directory 0700, files 0600. The generic capture writer needs an explicit private-file policy for a newly created store; copying existing target permissions alone is insufficient. [B4]
- Check schema versions. A malformed or newer unsupported collection is an error, not an empty collection to overwrite. Preserve it, offer export/recovery, and avoid the stash store's automatic reset behavior for valuable definitions. [M2]
- Maintain one recoverable previous valid collection snapshot for accidental corruption; document that explicit privacy erasure must remove backup copies too. A normal per-item Delete remains undoable as described above.
- A new non-origin invocation reuses an equivalent record instead of adding another. An origin update preserves identity/name and uses its revision. If an explicit edit creates a duplicate with another named record, expose the duplicate decision instead of silently discarding metadata.
- If another process edits/deletes a checked-out record, refuse an origin overwrite **before** vault writes. Preserve the draft and offer refresh or Save as Copy. Retry only the explicit library operation after resolving the conflict; never retry the capture automatically.
- If the checked-out draft is converted to ordinary capture text, do not consult or mutate the template store. The original definition remains recoverable.

Strict persistence means an unreadable/full library can block template captures, although ordinary captures remain unaffected. That is a real coupling cost. Provide an explicit setting to disable automatic retention when necessary; never silently bypass saving while claiming the normal guarantee. Do not interpret “disable saving” as permission to delete the collection. Clear/erase is a separate user action.

### Compatibility

New bob plus an older app should save definitions automatically and preserve all existing capture output fields. A new app plus old bob should keep ordinary capture available and show “Saved templates require an updated bob” for this feature. Probe the new read-only endpoint/capabilities; do not infer support solely from a version string or repeatedly discover an unsupported mutation after capture.

Only pass origin arguments when advertised. An unknown/malformed optional presentation field can degrade to ordinary rendering; an unsupported library schema or unverifiable origin must not silently discard saved records. Keep the process client's existing timeouts, cancellation, and dedicated preview/submit lanes. Invalidate cached collection data and active origin when the selected bob binary or vault changes. [M4][M6][M7]

## What implementation should prove

The most valuable tests exercise lifecycle and failure cases, rather than merely repeating JSON field assignments:

| Area | Required evidence |
| --- | --- |
| Automatic memory | Successful direct CLI capture and app capture save exactly once; one row and many rows behave identically; changed rows reuse the definition. |
| Purity | Parse, complete, get, validate, expand, dry-run, and failed capture do not change collection bytes or create the collection path. |
| Extraction | Child bullets, CRLF, Unicode, quotes, escaped braces, and preserved authored whitespace; previous rows never enter a saved definition or list preview. |
| Invocation context | Restoring explicit route/section/task/default policies preserves behavior; stale task references refuse safely; execution-specific inputs are absent. |
| Safe pop | Selection hides a row locally without changing disk; Discard, Control-C, ordinary-text conversion, and process restart preserve the original. Failed load never checks it out. |
| Update identity | A checked-out edited definition replaces the origin once on success; name survives; explicit Save needs no capture rows. |
| Concurrency | Two CLI saves do not lose entries; revision conflicts/deleted origins are detected before vault mutation; matching content deduplicates. |
| Fault injection | Unwritable directory, failed temporary write, failed collection replacement, and rollback failure produce truthful outcomes. No acknowledged success omits the save. |
| Corruption | Truncated file and future schema remain untouched; recovery snapshot is usable; no silent start-empty overwrite. |
| Interaction | Nonempty draft is preserved; search typing cannot activate rows; Return/arrow navigation works; Escape restores focus; repeating an activation cannot double-submit. |
| Immediate load | Bob-produced caret is at the first row; calm missing-row state appears immediately; Control-J cannot insert a dash during delayed analysis. |
| Compatibility | Old bob/new app and new bob/old app; missing optional JSON fields; no unsupported origin flag is sent. |
| Visual/accessibility | Light/dark, high contrast, long body, empty/no-results/loading/error, five-row scroll, stable panel position, VoiceOver, and color-independent field identification. |

For an implementation, run bob-cli's required checks, then the Mac repository's mandated portable checks and real macOS compile/typecheck workflow. Its `AGENTS.md` explicitly says never to land uncompiled Swift; portable checks alone do not compile the app targets. This report makes no claim that those future checks have run.

## Recommended solution

Build automatic saved templates, with bob owning a versioned per-vault collection of reusable definitions and invocation defaults. Save once per successful real template capture, deduplicate repeated uses, and keep rows out of the collection. Control-T should reveal a compact searchable picker using the capture panel's existing materials and placeholder colors.

Honor the requested pop as a **recoverable local checkout**: the selected row disappears from available choices while its draft is active, its saved original remains durable, and a successful capture updates that record through the same final bob call. Cancellation returns the original. Add a clear Edit → Save path for permanent changes without creating tasks, and an undoable per-template Delete.

Do not copy the stash's destructive disk removal, duplicate entries, bounded eviction, letter accelerators, or prominent Delete All action. This preserves the speed of the stash interaction while giving reusable templates the persistence and care they need.

[B1]: https://github.com/bobs-org/bob-cli/blob/a041abdb1bb2f19f7f69d304922c12c7005e1765/docs/capture.md#bulk-templates
[B2]: https://github.com/bobs-org/bob-cli/blob/a041abdb1bb2f19f7f69d304922c12c7005e1765/src/native/capture_language/template.rs
[B3]: https://github.com/bobs-org/bob-cli/blob/a041abdb1bb2f19f7f69d304922c12c7005e1765/src/native/capture/mod.rs
[B4]: https://github.com/bobs-org/bob-cli/blob/a041abdb1bb2f19f7f69d304922c12c7005e1765/src/native/capture/commit.rs
[B9]: https://github.com/bobs-org/bob-cli/blob/a041abdb1bb2f19f7f69d304922c12c7005e1765/src/native/capture/cli.rs
[B10]: https://github.com/bobs-org/bob-cli/blob/a041abdb1bb2f19f7f69d304922c12c7005e1765/src/native/env.rs
[M1]: https://github.com/bobs-org/bob-mac-capture/blob/94a4e589b12d45fec7d10347d0bc6931623bf568/Sources/BobMacCapture/CanceledDraftStash.swift
[M2]: https://github.com/bobs-org/bob-mac-capture/blob/94a4e589b12d45fec7d10347d0bc6931623bf568/Sources/CaptureCore/CanceledDraftStashStore.swift
[M3]: https://github.com/bobs-org/bob-mac-capture/blob/94a4e589b12d45fec7d10347d0bc6931623bf568/Sources/BobMacCapture/CapturePanelModel.swift
[M4]: https://github.com/bobs-org/bob-mac-capture/blob/94a4e589b12d45fec7d10347d0bc6931623bf568/Sources/BobMacCapture/CaptureKeyCommandRouter.swift
[M5]: https://github.com/bobs-org/bob-mac-capture/blob/94a4e589b12d45fec7d10347d0bc6931623bf568/Sources/BobMacCapture/CapturePanelView.swift
[M6]: https://github.com/bobs-org/bob-mac-capture/blob/94a4e589b12d45fec7d10347d0bc6931623bf568/Sources/CaptureCore/BobProcessClient.swift
[M7]: https://github.com/bobs-org/bob-mac-capture/blob/94a4e589b12d45fec7d10347d0bc6931623bf568/Sources/CaptureCore/CaptureModels.swift
[M8]: https://github.com/bobs-org/bob-mac-capture/blob/94a4e589b12d45fec7d10347d0bc6931623bf568/README.md
