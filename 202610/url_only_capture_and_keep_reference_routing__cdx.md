# URL-only capture and Google Keep reference routing

Independent research by **cdx**, 2026-10-07.

The feature is a good idea if a bare URL means “save this external material to my reference intake.” It should reuse the implementation behind `bob ref create`, retain an explicit way to capture a URL as a task, and distinguish successful intake from a reference note that has reached the vault. The difficult parts are batch publication, live-preview latency, duplicate handling, and Google Keep's archive boundary—not recognizing an `https://` prefix.

My recommendation is a shared, typed Rust reference-import service, called by both capture and Keep, with an offline preview path. Preserve capture's existing aggregate-success and rollback contract. For Keep, import eligible URLs into the existing intake and leave them pending until an identifiable reference note is available and the existing durability/commit checks have succeeded. Do not run a whole-library scan from capture or Keep pull.

## Evidence and scope

I inspected bob-cli at `6d2911ce416ad2898f5791ea2e602eb4c40aed54`, and the linked bob-mac-capture checkout at `4344a542133f9a87046aad498be13b71905de6bc`. I read the requested closed epics using `sase bead read`, and read the relevant CLI, artifact, Obsidian, and thin-client memory through audited `sase memory read` commands. I did not consult any report, transcript, or findings from the other researchers in this swarm.

The principal evidence is:

| ID | Source | What it establishes |
| --- | --- | --- |
| C1 | [Capture contract](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/docs/capture.md), especially “Multi-item capture” and “Input, stdin, and JSON output” | Blank-line batch grammar, whole-batch rollback, stable output fields, aggregate Mac submission |
| C2 | [Capture entry point](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/capture/mod.rs), [planner](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/capture/plan.rs), [writer](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/capture/commit.rs) | Parse/plan/commit separation, staged text files, optimistic preimage checks, rollback ownership |
| C3 | [Draft splitting](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/capture_language/draft.rs), [item parser](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/capture_language/item.rs), [editor parser](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/capture_language/editor_parse.rs) | One authority for grammar, meaningful physical lines and source ranges, global destination handling |
| C4 | [Reference creation guide](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/docs/highlights-create.md), [create implementation](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/highlights_ref/create.rs), [target classifier](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/highlights_ref/target.rs) | URL/PDF/arXiv/article dispatch, default types, intake rather than immediate ref-note creation, private print-heavy implementation |
| C5 | [URL validation](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/highlights_ref/clip_url.rs), [source dedupe](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/highlights_ref/sources.rs), [reference identity guide](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/docs/ref.md) | Existing canonical URL identity, queued-PDF dedupe, special legacy-note behavior |
| C6 | [Keep guide](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/docs/gkeep.md), [pull transaction](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/gkeep/pull.rs), [classification](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/gkeep/plan.rs) | Verified write and scoped commit before content-guarded archive, partial per-note success, pinned/shared selection rules |
| C7 | [Keep model](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/gkeep/model.rs), [ledger/journal](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/gkeep/ledger.rs), [Python adapter](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/scripts/gkeep_adapter.py) | Separate title/text/checklist/attachment fields, exact content fingerprints, archive guard excludes attachment metadata |
| C8 | [Mac subprocess client](https://github.com/bobs-org/bob-mac-capture/blob/4344a542133f9a87046aad498be13b71905de6bc/Sources/CaptureCore/BobProcessClient.swift), [models](https://github.com/bobs-org/bob-mac-capture/blob/4344a542133f9a87046aad498be13b71905de6bc/Sources/CaptureCore/CaptureModels.swift), [panel model](https://github.com/bobs-org/bob-mac-capture/blob/4344a542133f9a87046aad498be13b71905de6bc/Sources/BobMacCapture/CapturePanelModel.swift) | 20-second timeout, live dry runs, 50-ms analysis debounce, additive decoding, draft cleared only on overall success |
| C9 | [Vault sync and intake bridge](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/docs/vault-git-sync.md#highlights-bridge), [scan implementation](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/highlights_ref/sync.rs) | `xlib/` excluded from Git sync; existing server-to-Mac transfer and periodic scan; scan covers the library and runs hooks |
| C10 | [PDF installer](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/highlights_ref/marker.rs), [file writer](https://github.com/bobs-org/bob-cli/blob/6d2911ce416ad2898f5791ea2e602eb4c40aed54/src/native/highlights_ref/io.rs) | Atomic rename helpers do not themselves call `sync_all`; atomic publication and crash durability are different claims |

Epic `bob-cli-4s` added the multi-target create implementation and `--listen`; `bob-cli-4w` made `bob ref` canonical, retained the old command aliases, and allowed a fresh capture when a URL appears only in a legacy note without a Highlights PDF. Their closed-bead descriptions and landing notes corroborate C4–C5. This research preserves those choices.

I also checked the [WHATWG URL parser](https://url.spec.whatwg.org/#concept-basic-url-parser) and [RFC 3986 character grammar](https://www.rfc-editor.org/rfc/rfc3986.html#appendix-A). These support the narrow input rules below, rather than another URL-normalization implementation.

### Small read-only confirmations

I used the installed `/home/bryan/.cargo/bin/bob` for `capture-parse` and dry runs against a temporary empty vault. Its build provenance was not independently matched to the checkout; the observations agree with the inspected source.

- A bare `https://example.com/article?x=1&y=2#section` parses as `mode: "task"`, with no URL-specific spans or diagnostics.
- Two adjacent URL lines produce an `invalid_child_line` diagnostic for line 2. Two blank-line-separated URLs produce two task items.
- A bare URL dry run reports `kind: "task"`, `relative_target: "mac_inbox.md"`, and a rendered `#task` line.
- An explicitly routed URL still reports a task. The temporary vault remained empty after both dry runs.

I did not fetch real articles, run a real Keep pull, mutate the live vault, implement the feature, or run the full test suite. The findings below are design conclusions from current source/contracts, not a claim that the proposed behavior has been tested.

## 1. Critique of the product idea

A bare URL often describes reference material, not an action. Turning it into an inbox task creates triage work before the actual capture. Routing the URL directly into the existing reference pipeline removes that extra step and makes the Mac panel and mobile Keep capture useful entry points to the same library.

The assumption has limits. A repository, product page, issue, map, video, authenticated page, or expiring link may not be capturable by the article/PDF pipeline. Some URLs are intended as reminders. Therefore the rule should be narrowly “an otherwise unmodified public HTTP(S) URL requests reference intake,” with explicit task routing taking precedence. A failed import should retain the source, explain the failure, and allow a deliberate task capture. Silently replacing the failed import with a successful inbox task would conceal which operation actually happened.

The other semantic issue is completion: `bob ref create` creates a stamped PDF in intake. It does **not** immediately create the reference Markdown note. The interface should say “Saved to reference intake” and “Already captured,” rather than promising a note that does not yet exist. The existing transfer/scan bridge remains responsible for materializing the note. [C4, C9]

Automatic narration is outside this request. Do not add `--listen` implicitly: it changes cost, duration, dependencies, and retry behavior substantially. Keep the existing type/default/status/parent rules of reference creation.

## 2. Proposed requirements and explicit adjustments

These are my proposed clarifications, not existing behavior.

| Requirement | Proposed interpretation or adjustment | Reason |
| --- | --- | --- |
| “URL is the only capture input” | Determine this from the raw capture item, before consuming route, schedule, priority, clipboard, or dependency modifiers. | A URL left after stripping modifiers is not the user's entire original input. |
| Supported URL | A complete HTTP(S) URL, without internal whitespace/control characters, accepted by the shared reference validator. | Reuses the existing public-URL policy and identity. |
| URL task escape | Explicit local routing, forced destination options, clipboard capture, or a global destination declaration preserves ordinary capture semantics. | Explicit user intent should override inference. |
| Bulk URLs | Support both the existing blank-line-separated item grammar and a draft consisting entirely of one bare URL per nonblank physical line. | A pasted URL list should not require editing in blank rows. **This adjacent-line convenience is an additive grammar adjustment.** |
| Mixed capture | Support a bare URL item alongside ordinary items separated by the normal blank-line grammar. | Avoid making bulk behavior depend on whether another item happens to be a task. **This is a justified extension beyond the narrowest whole-draft reading.** |
| Preview | `capture-parse` and capture dry run identify/reference-plan URLs without fetching or rendering them. | Live previews must remain cheap and local. **This differs intentionally from `ref create --dry-run`, which can fetch/extract.** |
| Duplicate URL | A provable existing modern capture is successful reuse for capture/Keep, with a typed result. | Makes retries and repeat Keep pulls usable. Direct `ref create` can retain its current refusal behavior. |
| Keep URL-only | Inspect title, text, kind, checklist items, and attachments separately; never infer purity from the rendered task text. | Preserves non-URL content. |
| Keep completion | An intake-only result is pending, not an archivable reference. Archive after a verified reference note and the existing commit policy. | Preserves the purpose of Keep's current archive safeguard despite the gitignored intake. **This deferred-archive rule is the main recommended workflow adjustment.** |
| Failure | Keep the Mac draft and affected Keep source notes; report actionable per-URL errors. | The source remains the recovery path. |

For a draft-wide `@@route`, I recommend treating every otherwise ordinary URL as explicitly destined for that route. This avoids silently changing an established “send this whole draft to this note” instruction. A naked URL without such a declaration becomes a reference item. Document this exception prominently.

No new subcommand under `bob capture` is appropriate: that command consumes free text and the project's CLI policy freezes the sibling `capture-*` protocol names. Existing `--route` is sufficient for an escape hatch; a new mode flag is unnecessary for the first release.

## 3. Recognition rules and examples

Use a pure classifier with three outcomes: ordinary capture, reference candidate, and claimed-but-invalid reference URL. Do not make successful parsing by `url::Url` alone the entire classifier.

The WHATWG parser removes internal ASCII tabs/newlines as part of parsing. A generic parser can therefore accept input that did not represent one complete URL in the capture grammar. Reject internal whitespace before invoking the shared validator. Preserve percent-encoded content; do not decode it to discover capture markers. [WHATWG URL parser](https://url.spec.whatwg.org/#concept-basic-url-parser)

Characters such as `&`, `=`, `+`, parentheses, `@`, and `#` are meaningful URI characters/components. Do not trim guessed punctuation or interpret marker-looking substrings inside a URL. Trim surrounding whitespace only; Markdown links, angle-bracket wrappers, bullet prefixes, and prose stay ordinary capture in the first release. [RFC 3986](https://www.rfc-editor.org/rfc/rfc3986.html#appendix-A)

| Capture input | Recommended behavior |
| --- | --- |
| `https://example.com/article` | Reference import |
| `HTTPS://example.com/article?x=1&y=2#section` | Reference import using the shared cleaner; original URL remains available in the result |
| `https://arxiv.org/html/1706.03762v2` | Existing arXiv route and dedupe identity |
| `https://example.com/download?id=123` | Existing fetch/content-type route; do not guess PDF/article from the suffix |
| `Read https://example.com/article` | Ordinary task |
| `https://example.com/article @books` | Ordinary routed task |
| `@mac_inbox https://example.com/article` | Explicit task capture, even when the URL alone would fail import |
| `https://example.com/article s:2` | Ordinary scheduled task |
| URL plus authored child bullets | Existing task/bullet grammar; no automatic reference import |
| `--route mac_inbox -- https://example.com/article` | Ordinary forced-route task |
| `@@books` plus URLs | Ordinary task routing under the global destination |
| One URL per line, with no other content | Ordered reference batch |
| Blank-line-separated task and bare URL | Mixed batch, with the same aggregate commit rule |
| Two URLs separated only by a space | Do not guess boundaries; ordinary text under existing grammar |
| `[title](https://example.com/article)` | Ordinary text; wrapper support can be added explicitly later |
| Bare `https://localhost/...` or a URL with userinfo | Reference-validation error under existing policy; never attempt a fetch |
| Bare malformed `https://...` input | A reference diagnostic/error, not a junk task created after failed validation |

Apply the special adjacent-line splitting only when the **entire draft** is an eligible URL list. Otherwise retain current authored-child and blank-line rules. Put the decision in shared draft splitting so parse, rewrite, preview, submit, source ranges, and completion see the same items. [C3]

## 4. Reuse the reference implementation through a typed service

Calling `bob ref create` as a shell command from each entry point is tempting, but is a poor permanent abstraction.

Today `create::run` accepts Clap matches, builds private `CreateOptions`, invokes private `create_pdf`, prints human output, and returns an exit code. The article engine also prints directly. There is no uniform structured creation outcome ready for capture JSON. A direct call to the current implementation would pollute capture/Keep stdout; a subprocess wrapper would still need to infer paths, errors, and duplicate state from human text. [C4]

There is also a concrete flag trap: `capture -f` selects output format, while `ref create -f` means **force overwrite**. Never forward capture's arguments wholesale to create.

Extract an internal boundary along these lines; names are illustrative:

```rust
classify_reference_input(raw, explicit_capture_intent) -> ReferenceIntent
preview_reference(config, validated_url) -> ReferencePreview
prepare_reference(config, validated_url, options, reuse_policy)
    -> PreparedReferenceOrExisting
publish_prepared_reference(prepared, publication_context) -> ReferenceOutcome
```

The shared core owns URL cleaning, arXiv identity, HTTP routing, clipping, marker generation, filename selection, collisions, defaults, and dedupe. Each CLI wrapper owns its human/JSON rendering. A reference result should identify original/cleaned URLs, canonical key, source kind, actual PDF/optional note paths, marker identity, warnings, and lifecycle/outcome (`created`, `reused`, `queued`, `ready`).

Refactor the routes incrementally. `ref create` should continue calling the same shared core and preserve its established human report and duplicate-refusal contract. Capture and Keep select an **ensure-existing-or-create** policy, rather than changing every caller's behavior.

Do not preflight with `ref find` and treat any match as reuse. Library title scoring can return candidates, and an exact legacy URL match without a PDF deliberately remains recapturable after epic 4w. Use the exact identity and capture-state logic from `sources.rs`, then verify the resource required by the caller. A note merely carrying a `source_pdf` string is not sufficient evidence that its PDF is accessible and intact when making Keep archive decisions. [C5]

Keep configuration construction independent of Clap: a constructor accepting the effective vault root and reference path configuration must preserve `BOB_HIGHLIGHTS_*` overrides. A capture or Keep request using `--bob-dir` must never accidentally import into the default live vault.

## 5. Batch behavior: preserve the existing contract

Capture currently plans every item before writing and rolls back the batch if an ordinary planning/write step fails. Calling create for item 1 and then failing item 2 would change that contract: the Mac would retain the full draft even though item 1 had already published a PDF. Duplicate reuse helps retries, but does not make that batch atomic. [C1–C2, C8]

I recommend preserving the current operational rollback semantics:

1. Parse and validate every ordinary/reference item before network work.
2. Deduplicate canonical URL identities within the batch. Preserve a result for each input item, but prepare the physical resource once.
3. Fetch/render/stamp unique reference items into owned scratch storage, without publishing into intake.
4. Keep ordinary task/note changes staged. Reserve reference destinations across the whole batch, including different URLs deriving the same stem.
5. Before publication, recheck disk preimages, URL dedupe, and target/sidecar collisions against current state.
6. Publish prepared binary files and ordinary text changes under one rollback-aware coordinator. A reused resource has no write and must never enter the cleanup set.
7. Return success only after every requested item has committed or been validly reused.

“Atomic” here means the existing best-effort rollback promise on handled failures, not a claim of an ACID transaction across many files, a Git commit, and remote websites. A hard kill/power loss can interrupt a multi-file commit. Reference preparation must make cleanup ownership explicit, and publication must not overwrite user or concurrent-process output. Locking/collision rechecks and filesystem synchronization need deliberate implementation; existing capture preimage checks explicitly do not fully serialize other processes. [C2, C10]

Start sequentially for network work. Browser rendering is expensive, and parallel URLs complicate duplicate and stem reservations. Add bounded concurrency later only if measured bulk latency warrants it.

An alternative is explicit per-URL partial success with retained failed inputs. That is cheaper to implement, but requires changing capture's contract, adding partial-failure JSON, and teaching the Mac not to resubmit already-written ordinary tasks. I would not choose that as an incidental side effect of this feature. If implementation effort forces a narrower first release, ship URL-only atomic batches first and reject mixed reference/task batches before any write; call that temporary scope restriction out explicitly.

## 6. Offline previews and an additive JSON contract

Do **not** implement capture preview by delegating to `ref create --dry-run`. Its generic URL route fetches before distinguishing PDF from article, and its article dry run calls the clip adapter before printing a plan. That is acceptable for an explicit deep reference preview but unsuitable for the Mac's live capture dry runs. The Mac analyses edits after a 50-ms debounce. [C4, C8]

The capture preview should state only what is locally knowable:

- This item requests reference intake.
- The original/cleaned URL and canonical identity.
- Known arXiv classification, or generic “PDF/article determined on import.”
- Existing modern/reference/intake state when cheaply available.
- A destination category, not a fabricated exact filename or title.
- Syntax/validation errors and relevant existing-resource warnings.

The standalone create dry run can retain its current behavior. Clarify in docs that capture's dry run is a routing plan and may leave network-derived metadata unknown.

Add a `reference` object and a new string `kind: "reference"` to capture results, retaining the required top-level fields and existing `captures` array conventions. Avoid fake task markup in `task_line`; use an empty value with the new payload providing presentation. Preview target strings may be empty when unresolved. The updated Mac must never open an empty or guessed target path. Preserve the existing parse endpoint's schema version with additive URL mode/spans/payload fields.

`bob capture` itself currently has **no** `schema_version`, unlike `capture-parse` and gkeep output. Its Swift decoder has a dedicated path for this. Do not casually introduce a different mandatory success envelope. Direct creation JSON would be useful independently, but it is not required to deliver this feature once creation returns typed internal outcomes. [C1, C8]

Only the outer command should emit the final JSON document on stdout. Shared reference code returns data; progress/diagnostics go through a controlled stderr/event channel. Errors should retain stable codes and interrupt status rather than being flattened into an arbitrary exit 1.

## 7. Bob Mac Capture changes

The accepted thin-client decision applies directly: Swift must not identify URLs and spawn separate create processes. It should submit one aggregate capture request and render Bob's classification/outcome.

Required Mac work includes:

- Optional reference payload decoding using `decodeIfPresent`, and graceful handling of unknown string kinds.
- A reference preview with URL, known state, and “title/type resolved on import,” rather than a task preview.
- Longer bounded submission timing for reference operations. The present 20-second default was explicitly designed for offline local commands; the reference fetcher and clip adapter have 300-second stage limits. Keep parse/completion/live-preview bounds unchanged. A single global timeout increase would hide local-command regressions. [C4, C8]
- A Bob-supplied execution profile or item-count/budget field from local planning, so Swift can select a finite submission budget without implementing URL grammar. Define both per-stage and total-batch budgets; 300 seconds alone is not a safe whole-operation bound because classification and article capture are separate stages.
- Clear importing/cancel/error states, draft retained on failure or timeout, and no automatic resubmission.
- Cancellation that reaches the relevant child process tree and respects the publication boundary. Today the client calls `Process.terminate()` on Bob; that alone does not establish cancellation semantics for newly introduced curl/browser descendants.
- Correct Return and Command-Return behavior. Existing opening uses Obsidian note URLs derived from every `capture.target`; an intake PDF must have an explicitly defined open action. Prefer the ref note when one exists and a file URL for a newly saved PDF. Do not fabricate a note path or open every source webpage by default.
- Notifications/accessibility strings that distinguish intake saved, existing capture reused, and reference note available.

An older Bob can continue returning an ordinary task, and the app must present that actual behavior. An older app may decode a new string kind but cannot necessarily present it correctly. Roll out Bob and the app together, and test both compatibility directions rather than equating successful decoding with a complete UX.

## 8. Keep eligibility: avoid dropping note content

Keep notes contain distinct `title`, `text`, `items`, and `attachments`; `KeepNote.url` is the link to the **Keep note**, not the submitted article. Classify the raw content before `render_note`. [C6–C7]

For the first release I recommend:

| Keep content | Action |
| --- | --- |
| Empty title, body consists of one supported bare URL | Reference import |
| Title consists of the one URL, empty body | Reference import |
| Title/body contain only the same bare URL repeated | May coalesce to one import while retaining both originals in provenance; make this a documented rule |
| Nonempty prose title and URL-only body | Existing inbox capture; do not discard or reinterpret the title |
| URL body plus explanatory prose | Existing inbox capture |
| Any checklist/list note | Existing inbox capture, even when an item is a URL |
| Any image/drawing/audio/other attachment | Existing inbox capture |
| Empty/archived/pinned/shared note | Existing selection/skip rules first; URL routing does not override them |

A shared mobile-browser note can plausibly include a descriptive title, so the strict rule may route fewer notes than Bryan expects. That is a product question, not grounds to assume the title is machine-generated. The current adapter supplies no provenance that distinguishes an automatic title from Bryan's annotation.

A later, explicit extension could allow “one URL body plus title,” preserving the title and Keep source metadata separately. Using it as `--title` would deliberately override extracted reference metadata; that is not automatically the right choice. I recommend the strict rule initially and documenting this limit.

Bulk capture in the Mac/CLI is required. Multiple URLs in a single Keep note are not explicitly requested; keep them on the existing inbox path initially. If added later, require all fields to meet the purity rule, import all URLs, and archive the original note only after **all** imports are eligible for archive. Never archive it because one URL succeeded.

Normalize only harmless surrounding whitespace for recognition, while preserving the exact original `KeepContent` fingerprint and archive expectation. Do not render/re-hash a normalized substitute. Keep creation timestamps and the Keep deep link should remain available in provenance/reporting, even when no task is written.

## 9. Keep durability, pending state, and retry behavior

Keep's current protection is substantial: atomically write and fsync a task block, re-read and parse-verify it, commit when required, then submit an exact content-guarded archive request. The task's hidden `(Keep id, fingerprint)` marker survives movement through the vault; the local fsynced journal is a backstop. An `exit 0` from a different command is not equivalent evidence. [C6–C7]

Reference intake also has an existing lifecycle:

```text
URL -> ref-create -> local xlib PDF
                       |
             existing server-to-Mac bridge
                       |
              ref scan -> lib PDF + ref note
```

The guide documents a 15-minute Mac scan job and server intake transfer via `bob_xlib_pull`. `xlib/` is intentionally gitignored. Existing create uses an atomic PDF rename, but its installer does not itself call `sync_all`. The PDF can be successfully created while no Git-synced note or PDF exists yet. [C9–C10]

My recommended Keep behavior is:

1. Classify selected notes into task writes, reference imports, already-imported references, and skips.
2. Prepare/fetch reference work without holding `bob_sync.lock` across a network/browser stage. Keep the per-host pull lock for the operation. Reacquire the vault lock for fresh validation and final local publication/commit.
3. On successful create or verified reuse of an intake PDF, report `reference_pending`/`archive: deferred`. Do not insert anything into `gkeep_inbox.md`; leave the original note in Keep Home.
4. Reuse the existing intake/bridge/scan machinery. Do not run `ref scan` here: the current scan command scans the configured library, moves intake, and can run a network pre-scan hook. It is not a targeted single-reference transaction. [C9]
5. On a later pull, if the exact URL identity resolves to a usable modern ref note and its required PDF, verify that state and apply the normal scoped Git commit policy to the archivable resource paths as needed. Then archive with the current exact original-content guard.
6. A render failure, unavailable existing resource, validation failure, or ambiguous/incomplete capture keeps the note unarchived and reports a failure/pending reason. A commit failure archives none of the notes whose completion depends on that commit, matching the current safeguard.

Pending should be an explicit successful deferral, not repeated red error output. A pull that successfully imports a URL but defers archive should exit 0 with counts for queued references; a genuinely failed import still contributes to exit 1. Preserve existing setup/usage exit codes.

There is a tradeoff: the note remains visible in Keep until the scan and a subsequent pull, rather than disappearing immediately. I prefer this to silently weakening Keep's established completion guarantee. Keep Archive is recoverable, but that is an emergency backstop, not a reason to claim reference material is already in the synced library.

### Dedupe and persistence

Reuse exact reference source identity for both queued and ready resources, including the special legacy-only recapture rule. Do not treat “already captured” error text as a success. A typed queued result and a typed ready result have different archive eligibility.

Extend the existing journal additively with reference-specific events and locators as needed. A queued event must **not** be treated as an old `Written` task event, because the planner currently interprets that as authority for archive-only behavior. Journal evidence can accelerate lookup; ready-resource verification remains the gate. Keep the old task-marker/journal path unchanged.

On the same host, the existing queued-PDF source index prevents repeated creation. Across hosts, gitignored intake is temporarily invisible: another host can prepare a duplicate before the ref note is synced. This is a real limitation of reusing the current intake model. It affects wasted work, not source loss, under deferred archiving. Retain the existing preference for duplicates over data loss. If preventing cross-host duplicate rendering is a hard requirement, add a Git-synced import receipt/ownership record with explicit pending/ready semantics; that is extra scope, not something a local journal solves.

Do not store a Markdown receipt at the PDF's same-stem `.md` path: that is reserved for Highlights sidecars and is explicitly guarded against. Do not put the only import evidence inside `xlib/`, since it is not Git-synced. If receipts are added, use a separately managed metadata location with explicit readers, retention, synchronization, and provenance; never infer durable cross-host state from a disappearing intake path alone. [C4–C5, C9]

### Notes edited during import

The adapter's current archive guard compares `title`, `text`, and `items`; attachment metadata is not included in that content object. For a URL import whose purity depended on **no attachments**, add an optional archive precondition that the live note still has no attachments. Otherwise a newly attached image can coexist with an unchanged content fingerprint and be omitted from the imported reference. This is a narrowly scoped extension to the archive protocol, not a change to the existing asynchronous-OCR fingerprint rule. [C7]

Keep edits remain guarded: a URL changed to prose during fetch stays in Keep; a subsequent pull captures its current non-URL content normally. Do not write an inbox task as an implicit error fallback for a note that qualified for reference import.

### URL-only pulls must not depend on the task inbox

Today `pull` requires the configured target file before it classifies notes, and it reads its indentation even when no task write may be necessary. Move target-note existence/indentation checks to the task-write branch. A pull containing only eligible URLs should succeed or report reference-specific problems even if `gkeep_inbox.md` is absent. Keep the current missing-target behavior when a task write actually needs that file. [C6]

## 10. Alternatives and implementation sequence

| Approach | Benefit | Cost/problem | Assessment |
| --- | --- | --- | --- |
| Shell/subprocess create once per URL | Small initial patch; reuse public command | Human-output parsing, nested stdout, broken batch semantics, duplicate-error ambiguity, repeated setup | Useful only as a throwaway experiment |
| Shared typed synchronous import core | One semantic implementation, reliable outcomes, staging and tests | Requires a real refactor of print-heavy create/article paths | **Recommended** |
| Durable job queue for all URL captures | Fast/offline capture and resilient worker retries | New state machine, worker ownership, scheduling, cancellation, monitoring, and accepted-vs-completed UX | Consider only if measured synchronous submit latency is unacceptable |
| Create then scan the entire library from pull | Ref notes appear sooner | Unrelated mutations, hooks/transfers, collision/dirty-note failures, lock scope, long duration | Reject |
| Archive Keep immediately after create exit 0 | Quick drain of Keep Home | Intake-only and non-fsynced publication differ from current archive guarantee | Reject as the default |
| Immediate archive after verified local intake plus a synced receipt | Faster drain with explicit provenance/recovery | A documented weaker guarantee; new receipt lifecycle, cross-host visibility, transfer diagnostics | Viable opt-in design if immediate archive matters more than the existing guarantee |

An implementation sequence that isolates the hard contracts is:

1. Extract typed URL preparation/outcomes and printing from reference creation; preserve existing create behavior and exact dedupe rules.
2. Add the shared raw-input classifier, URL parse mode/ranges, offline preview, and effective-vault configuration path.
3. Add reference preparation/publication to capture's batch coordinator; implement blank-line mixed batches and the all-URL adjacent-line convenience.
4. Add Mac payload/presentation, submission budgets/cancellation, correct target opening, and compatibility tests.
5. Add Keep eligibility, reference pending/ready actions, typed journal/reporting, conditional inbox validation, and archive attachment preconditions. Keep ordinary task transactions and selection rules intact.
6. Verify a real article, a direct PDF URL, and an arXiv URL through CLI, Mac, and a selected Keep note; verify eventual bridge/scan/second-pull archive behavior.

This is a coordinated feature across three entry points, not a URL regex patch. If scope must be reduced, narrow mixed-batch or Keep-title support openly; do not remove failure/durability safeguards to make the patch appear small.

## 11. Acceptance tests that matter

The existing test seams include capture grammar/batch tests, `tests/cli/highlights/create.rs`, `tests/gkeep_pull.rs` with a fake adapter, and Mac core/panel subprocess tests. Build on those rather than depending on live websites/Keep for routine CI. [C2, C4, C6, C8]

Essential cases:

- Pure URL, surrounding whitespace, uppercase scheme, CRLF, query punctuation, encoded characters, arXiv variants, malformed/userinfo/private targets, routed URLs, global destinations, scheduled URLs, prose, and authored children.
- URL lists with and without blank rows, repeated canonical URLs, mixed task/reference batches, and two different URLs deriving one output stem.
- Parse and live dry run with fake curl/clip executables that fail if invoked: proves previews are offline rather than merely asserting `dry_run: true`.
- Failure on reference item 2 leaves item 1's published resource and all ordinary batch edits absent; reused preexisting resources survive cleanup. Include disk-race/collision and interrupt tests.
- Capture/Keep JSON contains exactly one object; nested create reports never leak to stdout. `--bob-dir` and configured reference directories remain isolated.
- Keep URL body versus URL title, descriptive title, checklist, attachments, pinned/shared selection, changed content, attachment added during import, render/verify/commit/archive failure, and missing task inbox in a URL-only pull.
- First Keep pull creates one queued PDF, writes no inbox task, leaves the source pending; second same-host pull reuses it; after scan a later pull archives without creating another PDF.
- Existing modern capture reuses successfully; a legacy-only URL note still gets a fresh capture; a stale `source_pdf` pointer does not authorize archive.
- URL imports still honor `--no-archive`, `--no-commit`, dry run, limit ordering, and quiet/JSON behavior. Document any new `deferred` archive status additively.
- Mac local endpoints retain their short timeouts; slow reference submissions do not expire at 20 seconds; timeout/cancel retains the draft and leaves a reconcilable outcome. Return hides only after aggregate success; Command-Return uses the declared note/file target.
- A real bridge transfer demonstrates that a moved intake PDF is not interpreted as a vanished/failed capture and that the ready ref survives vault sync.

## Recommended solution

Implement bare HTTP(S) URLs as a first-class reference capture intent in **bob-cli**, using the same typed URL-import implementation as `bob ref create`. Let explicit capture destinations/modifiers preserve ordinary capture, keep the Mac a thin client, and make capture parsing/live dry runs completely offline. Support bulk URLs through the established batch model, with additive one-URL-per-line convenience and rollback-aware publication; do not invoke the human CLI once per item.

For **Google Keep**, start with genuinely URL-only note content and no attachments/checklist/prose title. Import into the existing intake, show a distinct pending-reference result, and leave the source unarchived until the current bridge/scan produces a usable ref note and the normal verification/commit/archive guard succeeds. Preserve exact Keep content and add the no-new-attachments archive precondition for this route. The absence of `gkeep_inbox.md` must not block URL-only pulls.

This achieves the user's routing goal without a second URL engine or a new background queue. The deliberate adjustments are offline/inexact previews, explicit ordinary-capture precedence, typed duplicate success, adjacent-line and mixed-batch support, and deferred Keep archiving. If Bryan wants Keep to disappear immediately on import, select the verified-intake-plus-synced-receipt alternative explicitly and document its weaker completion guarantee; do not make it an accidental consequence of calling create.
