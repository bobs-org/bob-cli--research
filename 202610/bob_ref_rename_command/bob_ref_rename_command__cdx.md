# Reference renaming in bob-cli and Bob Mac Capture

Researcher: **cdx** · 2026-10-15 · Independent implementation research

## Decision in brief

**Add `bob ref rename`, with a Refs-panel action, but define it as renaming the managed reference’s file bundle while preserving its identity.** A raw filesystem rename is unsafe in the current pipeline. The PDF basename determines the reference-note path, and both PDF and note paths participate in generated annotation/task identities. Those dependencies must be handled before exposing a convenient keyboard gesture.

For the requested example, a reasonable explicit new stem is `karpathy_llm_wiki`. Keep the existing display title `karpathy/llm-wiki.md`, source URL, source `id`, reading-task block ID, dates, and annotation IDs. Add **Rename Reference Files…** to the actions menu and use **Command-Shift-R** to open a small filename editor. Keep title editing separate in the initial release.

This is a useful repair feature. I would pair it with a small, separately testable improvement to future import naming for opaque URL slugs, so renaming does not become routine cleanup. I would not turn this into a general reference-metadata editor or a new universal identity architecture.

## Scope and evidence

I independently inspected bob-cli at `9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a` and bob-mac-capture at `9f58448a035b3592c2d7e5dbd5a3d0abf0a9f111`. I did not locate or consult the other swarm reports or their findings. Product code and the live vault were not changed. Evidence consists of checked-out source, project memory read through its audited command, official documentation, read-only reference queries, and one disposable synthetic-vault experiment.

The source links below are permalinks to those inspected commits. Proposed behavior is identified as a recommendation; it does not describe a command already implemented.

### What the supplied PDF actually is

A read-only lookup, `bob ref find 442a6bf555914893e9891c11519de94f -i -f json`, resolved exactly one library entry:

| Property | Observed value |
| --- | --- |
| Display title | `karpathy/llm-wiki.md` |
| PDF | `lib/blogs/442a6bf555914893e9891c11519de94f.pdf` |
| Note | `ref/blogs/442a6bf555914893e9891c11519de94f.md` |
| Source URL | `https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f` |
| Frontmatter / PDF marker `id` | `442a6bf555914893e9891c11519de94f` |
| Reading state | queued / ready |
| Reading task | `sase.md#^ref-442a6bf555914893e9891c11519de94f` |
| Current annotation count / audio | 0 / absent |

`bob ref show ref/blogs/442a6bf555914893e9891c11519de94f.md -N -f json` and read-only `bob ref marker` confirmed this. Thus the hash is a real source identifier, rather than random corrupt data. It is a poor human filename, while the title is already informative. **Renaming must not replace every occurrence of that hash:** doing so would corrupt the gist URL and the existing source ID.

A bare `bob ref show 442a6bf555914893e9891c11519de94f.pdf` failed, whereas the stem and full vault-relative paths work. The resolver treats `.pdf` inputs as paths and compares them to the full `source_pdf`. Use the selected row’s exact note path in the app; document full PDF paths in CLI examples instead of relying on PDF basename lookup. This follows the existing [reference resolution code](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/src/native/ref_library/resolve.rs#L141).

## Why the feature is more than `rename(old, new)`

### 1. The scanner locates notes by PDF path, not marker ID

`pdf_path_metadata` maps `lib/<relative>.pdf` to `ref/<relative>.md`. `plan_pdf_sync` computes that destination and reads it before locating the reading task. It does not search for an existing note with the same marker ID. Moving only the PDF can therefore make scan create another note while leaving the original behind. Moving only the note can make scan recreate the old note. Moving both keeps the mirror convention, but does not address the remaining dependencies. See [path mapping](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/src/native/highlights_ref/io.rs#L4) and [scan planning](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/src/native/highlights_ref/sync.rs#L255).

Recommendation: preserve that convention for this feature. Rename the mirrored note together with the PDF. Teaching scan to find arbitrarily named notes by ID is a substantially different architecture, with missing/duplicate IDs and fallback selection to solve.

### 2. Annotation IDs currently depend on the PDF filename

`annotation_block_id` hashes the vault-relative PDF path, annotation kind, page, ordinal, and normalized text. Image IDs likewise include the PDF path. Consequently a renamed PDF gives unchanged annotations new `h-…` IDs. Rendering then regards the old IDs as removed and writes tombstones. [The code](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/src/native/highlights_ref/sidecar_render.rs#L115) and [documented block-ID contract](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/docs/highlights-ref-sync.md#L1136) agree.

I reproduced this with the installed `bob` in a temporary vault inside this workspace, isolated from Git discovery and using a temporary state directory. The fixture had one marked PDF, one plain Markdown sidecar, one reading task, and one unchanged quote. After the first scan I renamed the PDF, sidecar, and reference note with ordinary filesystem moves, then scanned again:

```text
first scan:                  created 1, failures 0
original quote ID:           h-ffe0f9128268
scan after bundle rename:    updated 1, failures 0
new quote ID:                h-574710efb948
old quote ID:                retained under Removed highlights
parent reading task target:  still ref/blogs/old_hash
```

The fixture was removed afterward. This confirms path-induced annotation churn and an unrepaired reading-task link. It does not establish the exact lifecycle outcome for every reading status or plugin state. The first experimental attempt was refused by the normal dirty-target guard because its temporary vault inherited the enclosing Git worktree; the successful experiment deliberately tested the supported non-worktree scan path.

### 3. Extracted task IDs also depend on paths

The durable processed-task digest includes the reference-note path, annotation block ID, and normalized task identity. Existing `[h:: …]` markers are intended to survive task edits, completion, and archiving. Text-based fallbacks may suppress some duplicates, but cannot safely substitute for keeping the original digest: edited or archived tasks can depend on their stored ID. See [digest construction](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/src/native/highlights_ref/annotation_tasks.rs#L213) and [the task contract](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/docs/highlights-ref-sync.md#L1117).

Preserve existing reading-task block IDs too. The ugly `ref-442a…` address is already a link target; improving its appearance is not worth rewriting ledger and dependency links.

### 4. A reference has several related files and addresses

| Member or address | Required treatment |
| --- | --- |
| Library PDF | Move to the requested stem within the same directory |
| Mirrored reference note | Move with it; preserve user text and frontmatter formatting where possible |
| `<stem>.md` sidecar | Move if present; do not confuse it with the note under `ref/` |
| `<stem>.textbundle/` | Move the complete bundle if present; preserve relative asset paths |
| Plain-sidecar image assets | Resolve their actual relative paths; do not invent an asset directory convention |
| `ref/.../<stem>.assets/` | Move if present and update live embeds; preserve contained annotation IDs |
| `.mp3`, `.m4a`, `.ogg`, `.opus` companions | Plan every associated same-stem companion; update note audio metadata and embeds |
| `source_pdf`, `highlights_sidecar`, `audio` | Update current location values without changing identity/provenance |
| Incoming note/PDF/asset links | Rewrite target addresses, including block/page fragments, preserving aliases |
| Reading task and annotation follow-up backlinks | Rewrite note target only; retain checkbox state, properties, IDs, residence, children, dates |
| App history and caches | Remap the old note path to the new path and invalidate stale detail data |

Sidecar lookup prefers `<stem>.md` over `<stem>.textbundle`; image assets are resolved relative to the sidecar text file; copied images live under the note’s `.assets` directory. The audio field is derived from same-stem companions. These are existing [sidecar](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/src/native/highlights_ref/sidecar.rs#L75), [asset](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/src/native/highlights_ref/sidecar.rs#L491), and [pipeline metadata](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/src/native/highlights_ref/note.rs#L5) contracts. If both sidecar forms exist, inventory both so a stale export is not left behind to mislead a later scan.

An additional corner case deserves an explicit test: a generated listen-card PDF may embed an `obsidian://open` URI containing its audio filename. Merely moving audio fixes the note’s player but breaks that PDF button. The [audio-link contract](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/docs/highlights-ref-sync.md#L265) makes this observable. Either migrate that exact URI without rerendering the document, including the PDF in the backed-up write set, or refuse that case until supported. Do not silently declare success with a broken button. Preserve PDF bytes in the ordinary case; never rerender an annotated PDF to rename it.

Highlights’ official documentation describes path-based `highlights://…#page=…` links. Sidecar page links may therefore require exact old-PDF address updates too; the behavior of a currently open document and its next sidecar save must be validated on a Mac. [Highlights release notes](https://highlightsapp.net/changelog/mac/)

### 5. Obsidian cannot be assumed to repair an external rename

Obsidian documents automatic internal-link updating, plus both wikilinks and Markdown links, fragments, and aliases. That is a useful behavior reference, not proof that a headless filesystem operation will repair the vault. The CLI should own its link updates and work with Obsidian closed. [Obsidian internal links](https://help.obsidian.md/links)

## Critique and alternatives

| Approach | Benefit | Cost / judgment |
| --- | --- | --- |
| Edit only `title` | Small, improves display names without moving files | Does not fix the explicitly requested PDF filename; title is already readable in this example |
| Rename in Finder or implement a file-only wrapper | Very small implementation | Breaks scan addressing and related links/identities; reject |
| Ask Obsidian to rename files | Can reuse its link handling | Requires a running app and still does not preserve bob’s hash inputs, sidecars, or app state; unsuitable as the command’s authority |
| Rename only PDF and keep stable note path, changing scan to follow IDs | Avoids incoming note-link churn | Replaces the current mirrored-path contract and needs duplicate/missing-ID rules; consider only as a separate architectural decision |
| Rename the managed bundle and preserve existing identity inputs | Meets the stated need within the current layout | Moderate backend work; recommended |
| Migrate all references to immutable UUIDs or a central manifest first | Strong general identity model | Excessive prerequisite for occasional renaming; legacy IDs, copies, sync, and migrations widen the project substantially |
| Improve naming during create | Avoids many future repairs | Complements rename; cannot repair existing files by itself |

The proposal is good if renaming is occasional corrective maintenance. It becomes a poor investment if the design assumes it is only a key binding plus a filesystem call, or bundles a general metadata editor, folder relocation, and library-wide identity migration into the first version.

## Explicit adjustments to the requirements

1. **“Rename reference” means rename the managed file bundle.** The initial command changes the filename stem, not the title, source ID, reference type, or parent. Label the app action **Rename Reference Files…** so that meaning is visible.
2. **Preserve historical identity even when it looks ugly.** Keep marker/frontmatter `id`, reading-task block IDs, annotation IDs, processed-task IDs, URLs, capture/creation/finish dates, and research provenance. No global hash replacement.
3. **Preserving scan behavior is an acceptance requirement.** A subsequent scan must not create a new reference/reading task or tombstone unchanged annotations because of the rename.
4. **Limit the first release to indexed PDF references inside managed `lib/`, with the expected mirrored note.** Refuse missing PDFs, unsupported external locations, ambiguous ownership, incomplete intake, and unsafe links before writing. An intake-only reference is not selectable in today’s panel anyway. Scanning it first provides the normal route.
5. **Add preview and structured results.** `-d/--dry-run` and `-f/--format human|json` are essential for a coordinated multi-file operation and the thin Mac client. Normal invocation applies the explicit rename; no redundant confirmation flag is needed.
6. **Keep a scoped recovery record.** Multi-file moves are not atomic together. Preflight refusals must write nothing; interruption after mutation needs recoverable state rather than an undocumented half-rename.
7. **Include an actions-menu entry as well as a keymap.** Preserve current shortcuts and provide a discoverable route.
8. **Improve opaque import names separately.** This reduces the recurring source of the problem but is not a substitute for fixing existing files.

No requirement to edit SASE memory is implied by this research.

## Proposed CLI contract

```bash
# Preview using an exact current note path.
bob ref rename ref/blogs/442a6bf555914893e9891c11519de94f.md karpathy_llm_wiki -d

# Apply the filename change.
bob ref rename ref/blogs/442a6bf555914893e9891c11519de94f.md karpathy_llm_wiki

# Equivalent full PDF selector; useful outside the app.
bob ref rename lib/blogs/442a6bf555914893e9891c11519de94f.pdf karpathy_llm_wiki

# Machine-readable preview.
bob ref rename ref/blogs/442a6bf555914893e9891c11519de94f.md karpathy_llm_wiki -d -f json
```

Reuse `ref show`’s exact resolution and ambiguity diagnostics. Titles may be accepted only under those exact-resolution rules; never select a fuzzy candidate for mutation. After resolving an exact path, verify the note/PDF association and marker consistency rather than selecting an alternate source-URL match behind the user’s back. Marker IDs are not globally unique by assumption: the app already tracks their share counts.

Accept a filename **stem**, with the existing create-name character policy (`[A-Za-z0-9][A-Za-z0-9_.-]*`) as a sensible first release. Reuse its optional `.pdf` suffix stripping for CLI convenience, clearly documented. Show `.pdf` as a fixed suffix in the UI. Reject paths, separators, hidden names, empty names, control characters, and overlong destination components. Construct targets by appending each member’s extension to the validated stem, being careful not to accidentally replace a dotted stem’s final component with `Path::with_extension`.

An exact unchanged name is a successful no-op. Handle case-only changes deliberately on case-insensitive Mac filesystems, with a collision-checked temporary hop; alternatively refuse them clearly in the first release. Preflight destination collisions case-insensitively as well as checking the actual filesystem. Never overwrite or silently append `_2` to an explicit requested name. Check companion, note, assets, and pending `xlib/` occupants too. A pending old-name companion should be handled deliberately or cause an actionable “scan intake first” refusal.

Use existing path overrides where applicable: `-b/--bob-dir`, `-l/--lib-dir`, `-r/--ref-dir`, and `-x/--xlib-dir`. Add the verb alphabetically in the Library help group. Keep options sorted, provide short aliases for public long options, and update help fixtures/completion/docs under the project CLI rules. No `--force`, folder-moving option, bulk mode, or automatic title editing in v1.

The JSON response should be a versioned, one-line envelope on stdout. Include `ok`, `schema_version`, `command`, `mode`, `changed`, an operation ID, unchanged marker ID when present, old/new note/PDF paths, ordered file moves, rewritten-file/link counts, warnings, and structured error/recovery details. Human output should summarize those same changes. Errors such as `ambiguous_reference`, `unsupported_reference`, `destination_exists`, `dirty_targets`, `reference_changed`, `rename_busy`, and `recovery_required` should be distinguishable. A no-op should be explicit. Keep progress and lock-wait messages on stderr.

Do not make the app discover what happened by interpreting prose or guessing names. A successful result must explicitly map old note path to new note path.

## Backend design and safety boundaries

### Preserve old identity inputs with a small compatibility mechanism

Before the first rename, record a note-local, pipeline-owned identity-origin record containing the **exact values currently used to hash the PDF path and note path**. Subsequent annotation and processed-task hashing should use those immutable origin values; actual file reads, output destinations, and emitted links should use current paths. On later renames keep the original record unchanged.

This can be one structured pipeline field with two components; the final spelling should follow existing field conventions. Add it to the pipeline exclusions so it is preserved by note rendering, rejected as a PDF marker property, omitted from marker hashes/base, and never sent into the PDF’s user metadata. Generic path rewriting must not rewrite those historical values.

This preserves existing `h-…` and `[h:: …]` values without trying to reverse SHA-256 or rewriting every historical task. References without the new field retain the old algorithm exactly. New references need no bulk migration. Preserve the field even on a first rename with no annotations, so future annotations use a stable identity context. Test malformed origin data as an error, rather than silently falling back and churning IDs.

Using the current marker ID directly for every hash would change the hashes of previously annotated references. It is also nullable and can be shared. A general future identity redesign remains possible, but it is not needed to make this operation safe.

### Plan once, revalidate, then execute the complete change set

Build a dedicated rename planner/executor in bob-cli, reusing path configuration, exact reference resolution, existing link parsing/resolution, and write guards. It should inventory the whole bundle, all affected vault links, known local URI links, and before-images. Preserve arbitrary note text; do not reconstruct the note from a fresh scan template. Keep synced title/status fields and marker snapshots untouched for a filename-only operation.

Rewrite resolved **link targets**, not arbitrary strings. Cover generated and authored wikilinks/embeds, aliases, note `.md` spellings, block/heading/page fragments, Markdown links and reference definitions, percent-encoded paths, and same-document relative links affected by an asset move. Preserve custom display text. Resolve short links against the pre-rename vault index so duplicate stems do not cause unrelated files to be rewritten. A newly ambiguous short link must become an unambiguous path or cause refusal.

Existing `vault_links::NoteIndex` helps resolve note targets, and capture’s link scanner understands code/escaped wikilinks, but neither is a complete attachment-renaming engine. Do not claim otherwise. Extend a focused shared utility with fixtures for the supported forms. Skip code examples and raw source URLs. Preserve historical provenance such as `research`, `research_ref`, `source_url`, and the new identity origins. Include ordinary archive notes when they contain live links: scan’s prohibition on lifecycle edits to `done/` should not be misread as permission to leave broken historical backlinks. This operation changes addresses, not archived task state.

For formats outside the parser’s supported contract, detect relevant old-address references and either support them or refuse with named files. In particular, inventory Canvas/other structured vault links if present; do not silently promise universal Obsidian link repair. External documents and previously copied links outside the vault cannot be comprehensively found. State that boundary in command help; aliases are lookup aids, not transparent filesystem redirects.

For PDF narration URIs, implement narrow destination replacement and verify that annotations, marker contents, page count, and relevant document structure survive. Rehash `source_pdf_sha256` if bytes change. If that cannot be made reliable in the initial release, fail preflight for affected PDFs with a specific explanation; this does not block the supplied audio-free example.

### Coordinate writers and recover interrupted changes

Writing scans currently hold `ref/scan.lock`; `sync_pdf` does not take that lock. Vault sync uses a separate maintenance lock. A brand-new rename-only lock would leave important races open. See [scan locking](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/src/native/highlights_ref/scan_json.rs#L119), [sync entry points](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/src/native/highlights_ref/sync.rs#L7), and [maintenance locking](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/src/native/ob.rs#L144).

Make rename participate in the scan writer exclusion and maintenance exclusion, and bring overlapping single-PDF writers into the same coordination contract. Establish and test one lock ordering across all paths that acquire both locks. Account for scan’s external pre-scan hook before holding locks in a new arrangement: a hook that invokes another maintenance operation must not create a deadlock. Existing scan helpers called by rename should not reacquire a lock already held. Do not run a full scan or its network hook as an incidental rename side effect.

Re-read the source association and every planned source/rewrite target under lock. Refuse unsafe containment, symlinks escaping managed roots, unreadable members, ownership ambiguity, changed files, and affected dirty Git targets. Do not require the entire vault to be clean just because unrelated work exists. Use before-image comparisons to catch an editor saving after planning. These local locks cannot stop unsaved edits in Highlights/Obsidian or coordinate another host directly; test normal vault-sync convergence and make the active-document behavior explicit.

Use a small durable operation journal in bob’s state directory, holding the intended mapping, preconditions, phases, and recoverable before-images. Stage rewritten files and use no-clobber moves; the existing generic `atomic_write`/`atomic_copy` helpers use overwrite-capable renames and are not sufficient destination protection on their own. Ordinary detected failures should roll back only bytes/paths still owned by this operation. Do not overwrite a user’s divergent edit during rollback. An interrupted operation should be completed or safely recovered under the same locks before a new overlapping rename proceeds, with named recovery files if human intervention is needed.

A single filesystem rename is atomic; the whole reference transformation is not. A memory-only rollback is insufficient when the subprocess is killed or times out. Make retries idempotent through the operation record, and return enough information to distinguish applied changes from preflight failure. Do not automatically retry a mutating subprocess after a lost response without checking its outcome.

Follow the normal reference pipeline’s lack of automatic reconciliation; do not add a Git pull/push or whole-vault commit to the interactive gesture. `bob vault-sync` remains responsible for normal persistence/sync. Keep the journal and backups until the operation has a verified final state.

## Mac app integration

The existing architecture is well suited to this: a `RefsFetching` protocol owns direct `bob` subprocess calls; `RefsLibrary` owns refresh and scanning; `RefsPanelModel` handles selection/actions; the controller routes keys and presents UI. Keep all vault mutation and naming semantics in bob-cli, consistent with the accepted thin-client decision.

Add a rename endpoint/client response alongside [RefsFetching](https://github.com/bobs-org/bob-mac-capture/blob/9f58448a035b3592c2d7e5dbd5a3d0abf0a9f111/Sources/RefsCore/RefsFetching.swift#L8), then a bounded rename state in the library/model. Use a dedicated `refs-rename` lane with replacement cancellation disabled. The app’s existing `decodeReport` path can decode structured failures even when the subprocess exits nonzero. Set a timeout that accommodates the backend’s bounded lock wait; a timeout must lead to reconciliation/recovery, not a blind second mutation.

Recommended interaction:

1. **⌘⇧R**, or **⌘K → Rename Reference Files…**, opens an in-panel editor for the selected reference. Show its current filename and readable title; select the stem. A title-derived suggestion is optional, never an automatic commit.
2. Keep the extension fixed. Use ordinary text editing/IME behavior. Return submits, Escape cancels. While this editor is active, bypass normal list shortcuts and the controller’s automatic search-field focus repair.
3. Show the proposed PDF/note destinations and a concise “related files and links will be updated” explanation. A backend dry-run can supply a preview; apply must revalidate it. One Rename submission is enough; do not add a second generic confirmation.
4. Keep the draft and selection on validation failure. During mutation disable repeated rename/scan submissions. Hiding the panel must not cancel the library-owned operation; completion/error can be presented on the next show.
5. After success, apply the returned old→new note-path mapping, refresh library/Today data, and invalidate inspector/copy caches. Keep the same logical reference selected. Migrate open-history events and relevant path-keyed signals without changing their timestamps. Preserve query and scope.

This last point is essential: [`RefItem.id` is the note path](https://github.com/bobs-org/bob-mac-capture/blob/9f58448a035b3592c2d7e5dbd5a3d0abf0a9f111/Sources/RefsCore/RefsModel.swift#L255), and [frozen listings preserve disappeared IDs as unavailable](https://github.com/bobs-org/bob-mac-capture/blob/9f58448a035b3592c2d7e5dbd5a3d0abf0a9f111/Sources/RefsCore/RefsRanking.swift#L298). An ordinary watcher refresh would otherwise leave the selected old row unavailable and lose history association. Remap the selected row in its current listing position, rather than reranking it away. If the old filename query no longer matches, keep that renamed row visible until the user edits the query or explicitly refreshes, then use normal ranking.

⌘R already refreshes and ⌘S already scans. Plain Return/Tab opens the selected PDF. Although Finder uses Return to rename, adopting that convention here would break this panel’s established quick-open behavior. ⌘⇧R is unused in the inspected Refs router and fits the action; retain all current bindings. See [existing routing](https://github.com/bobs-org/bob-mac-capture/blob/9f58448a035b3592c2d7e5dbd5a3d0abf0a9f111/Sources/BobMacCapture/Refs/RefsKeyRouter.swift#L63) and [Apple’s Finder rename behavior](https://support.apple.com/guide/mac-help/rename-files-folders-and-disks-on-mac-mchlp1144/mac).

An in-panel editor also avoids the nonactivating panel hiding when an external dialog takes key status. If a sheet is used, explicitly suspend resign-key hiding and restore field focus. The current actions-menu controller already has a small version of that suspension.

Handle independently installed app/CLI versions: add a capability indication if the existing capability interface supports it, or recognize the unsupported-command response and explain that bob must be updated. Do not let an old binary’s plain usage text become a misleading JSON decode error. Keep new response fields additive with tolerant decoding while rejecting unsupported schema versions. Do not change all app identity keys to marker IDs just for rename; nullable/shared marker IDs make that unsafe.

## Improve future imports, without widening the initial repair

The current web route chooses an explicit name, then a URL-derived stem, then an extracted-title-derived stem. The URL stem validator accepts a long hexadecimal slug. That directly explains why this gist’s hash beats its available title. See [web naming precedence](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/src/native/highlights_ref/clip.rs#L338) and [slug validation](https://github.com/bobs-org/bob-cli/blob/9bdb0bd9eadbb0382f06f5815ebc51019e94ae9a/src/native/highlights_ref/clip_url.rs#L250).

A narrow improvement is to classify clearly opaque URL segments—such as a gist’s hex ID or a UUID—and prefer a validated extracted title for the human filename when available. Keep URL-based deduplication and source provenance. Keep explicit `--name` authoritative. Start with known forms rather than a loose “looks random” heuristic that rejects legitimate technical identifiers; preserve current behavior when the title is absent or unusable. Use the existing collision planner. Separately consider whether the title’s `karpathy/` prefix should be retained in its slug to reduce collisions.

This can be a second small change after the rename safety work or an independent improvement. It must not silently rename existing references during scan.

## Implementation boundaries and validation

I would deliver three reviewable pieces: (1) identity preservation with backward-compatible scan behavior, (2) backend rename planning/execution/recovery and CLI contract, (3) app transport, editor, and selection/history handling. The opaque-slug import improvement is a separate small change. Exact duration needs implementation work; this is not a one-evening keymap patch if annotated references are supported correctly.

Tests should protect outcomes, especially the following:

- Rename an opaque-ID reference; its URL and source ID still resolve to one row; next scan does not create another note or reading task.
- Rename an annotated reference, including images, comments, extracted tasks, edited/archived processed tasks, and existing tombstones; unchanged IDs remain unchanged across at least two renames and scans.
- Cover v1 in-note trackers and v2 reading tasks, including closed/archived reading-task backlinks; preserve statuses, task IDs, child lines, user text, and dates.
- Move plain sidecar, TextBundle, copied assets, each audio extension, and any actual relative assets. Verify live note/PDF/Markdown/URI links, fragments, aliases, encoding, duplicate short stems, and code examples.
- Verify an embedded audio URI is migrated safely or refused before mutation. Verify no accidental PDF rerender and marker/annotation preservation.
- Exercise destination collisions for every member, case-only changes, dotted names, path traversal/symlink escape, missing members, malformed origin metadata, dirty affected targets, changed-after-preview files, and no-op requests.
- Inject failures between each move/write and kill the process mid-operation. Recover without data loss or overwriting divergent edits. Repeat a completed request safely.
- Run concurrent scan/sync/rename and a vault-sync boundary to check exclusion and lock ordering, including hooks and timeouts.
- App tests: key routing, menu discoverability, editor focus/IME/Escape/Return, duplicate-submission suppression, hide during operation, unsupported CLI, structured failure, lost response, watcher interleavings, retained selection/query, history remapping, and inspector cache invalidation.

For later implementation, follow the Mac repo’s compile requirement: run `just portable-check`; on hosts without Swift use an appropriate Swift host. Changes to macOS app targets require a scratch-copy build on a Mac (`bundle.sh` and `just typecheck-tests`), plus CI tests. Portable checks alone do not compile the AppKit UI. Research here changed no Swift and performed no Mac compilation. The remaining empirical uncertainty is how an actively open Highlights document follows the rename and regenerates its sidecars; resolve that with a manual annotated-PDF check before enabling the gesture broadly.

## Recommended solution

**Proceed with `bob ref rename REF NAME` as a managed bundle operation, exposed through Rename Reference Files… on ⌘⇧R.** Rename the PDF, mirrored note, and associated files; rewrite supported live links; preserve source IDs, reading-task addresses, annotation/task identity, dates, and user content. Add an immutable note-local origin for the legacy path-based hashes so a later scan remains stable. Provide dry-run/JSON results, refuse collisions and unsupported cases before writing, and retain a durable recovery journal for interruption.

Keep v1 focused on filename changes for indexed managed PDFs. Title editing, folder moves, bulk renaming, and universal UUID migration can wait. For the supplied reference, `karpathy_llm_wiki.pdf` and `ref/blogs/karpathy_llm_wiki.md` are sensible proposed names while the source ID remains `442a6bf555914893e9891c11519de94f`. Improve future opaque-slug import naming separately. This meets the actual repair need without sacrificing the reference’s existing links and history.
