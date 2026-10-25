# Deliberate rereads and safe reference rebuilds

Independent research by **cdx**, 2026-10-25. Repository examined: `bob-cli` at `a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1`. This report is based on the implementation, its tests and behavior contracts, audited project memory, primary API documentation, and an isolated parser experiment. No other report or findings from this swarm were consulted. This is design research; no product code or live vault data was changed.

**Assessment.** This is a useful feature. A second reading deserves a separate place for new observations, and a bad import deserves a recoverable rebuild. I would implement both, but make their meanings distinct: **reread creates another reading; overwrite rebuilds one selected reference while retaining its reading-task identity**. The dangerous part is not the flag. It is preserving the links, PDF state, extracted tasks, and history around a reference when its contents change.

The most consequential discovery is that `-f/--force` already exists. It is a boolean with a narrower meaning. Changing bare `-f` to mean reread is a deliberate compatibility break, not an additive option.

**What the repository does today.**

| Area | Observed behavior | Design consequence |
| --- | --- | --- |
| CLI | `create::command` declares boolean `-f/--force`, described as overwriting an existing target PDF. Both the single-target and collection paths read it with `get_flag`. | Replace the boolean throughout; changing only clap will break callers. [S1] |
| URL duplicates | Before fetching, `sources.rs` reads scalar/list `source_url` and legacy `url` in ref notes and intake markers. A PDF-backed note refuses even with force. | Preserve early duplicate errors and shared URL normalization. Return all matches instead of the first one. [S2] |
| Legacy refs | A matching note without `source_pdf` warns and permits a fresh capture. | “All duplicate refs require force” changes this intentional exception too. [S2, S3] |
| Names and IDs | Default targets walk `stem`, `stem_2`, … through 999. Occupancy includes notes, PDFs, sidecars, and case-insensitive reference IDs across types. Recorded IDs follow final stems. | Add a separate `__vN` reading allocator; retain `_N` for unrelated filename collisions. Extend occupancy to the whole bundle. [S3, S4] |
| Local material | Local PDF/Markdown collision identity is a normalized title at candidate paths, not a vault-wide content identity. Already marked PDFs and local library/intake PDFs have additional refusals. | A same-title hit cannot authorize destructive replacement. Do not promise that every copy of a local file is detected. [S3, S5] |
| Collections | Any overlapping URL refuses; exact queued sets can be overwritten with force. Partial overlap still refuses. | A URL match can refer to one chapter of a larger packet. Never replace that packet because one member matches. [S6] |
| Audio | `--listen` on a duplicate can attach audio to the existing capture before normal creation. Force also influences companion collision checks. | Explicit reread/overwrite must take precedence over automatic attach, and must not become permission to overwrite unrelated audio. [S1, S3] |
| Birth | The PDF is installed before `finish_create_intake`; intake then takes `bob_sync.lock → scan.lock`, pre-syncs where applicable, files the bundle, creates/adopts the task, and commits scoped paths. Unsafe intake can remain queued. | Existing birth helpers are useful, but their queue fallback is unsuitable for a destructive replacement. [S7] |
| Reading task | Modern reading tasks live in an area/project/inbox or archive, not simply inside the ref note. Allocation accounts for existing and archived block IDs. | Deleting a ref note does not delete or reset its reading task. [S8] |
| Index | Multiple PDF-backed notes with a shared identity receive `duplicate_identity`. Lookup favors non-superseded, more advanced readings, then path. | Intentional rereads need explicit provenance and index support; the current “primary” is not a safe overwrite target. [S9] |
| Annotation links | Highlight IDs and follow-up identities depend on source paths and annotation content; annotations can also contain sections and image assets. | Preserve the complete bundle and account for inbound annotation links, not just the Markdown file. [S10] |

There is an especially easy archive trap: `ref_library` skips hidden directories and `*.assets`, but `collect_ref_note_sources` recursively visits directories other than `.git`. Putting an old ref note in `ref/.history/` or `ref/foo.assets/` does **not** by itself keep it out of import deduplication. Generic task discovery is another independent walker. Archive exclusion must be an explicit, tested invariant. [S2, S9, S11]

**Critique and changes I recommend to the requirements.**

1. **Replace “delete, then recreate” with “stage, snapshot, then replace.”** The observable outcome is a fresh reference with history. Deletion must never be the first irreversible step. Download, render, narration, disk-space, or synchronization failures must leave the old reference usable.
2. **Make overwrite preserve the selected reading task and state.** Keep its block ID, location, checkbox, dates, dependency links, and work history. A rebuild repairs the current reading. Starting again belongs to reread. If overwrite should also restart the task, that is a separate product decision with reopening/archival consequences; do not inherit the CLI's default `status=ready` accidentally.
3. **Archive the complete current note and its dependencies.** A Markdown-only log loses useful meaning when its page links point at a newly rendered PDF and its images disappear. Keep saved PDF bytes, sidecars/textbundles, image assets, and companion audio as needed to interpret the old notes. Git history is additional recovery, not the user-facing annotation log.
4. **Require an exact selection when overwrite is ambiguous.** Add `-e/--existing <REF>` as a selector, accepting an exact note path or unambiguous recorded ID. It does not replace TARGET, which still supplies the material to render. Never select the first, newest, most-read, or lexicographically smallest match for destruction.
5. **Treat `__vN` as a reading number, not a source edition.** The number is allocated from 2 upward. It says nothing about arXiv version numbers or changed website content. Reserve numbers still referenced by history or a pending operation, even if a live file has disappeared; this is a clarification of “available.”
6. **Preserve the existing vault-note snapshot workflow by default.** Repeated snapshots of a changing vault note already have dated names and earlier-snapshot reporting. Do not suddenly reject all snapshots because they share `source_note`. Explicit forced modes can select an earlier snapshot, but ordinary snapshot creation retains its current behavior. This is a scoped exception to the broad duplicate requirement.
7. **Use an unambiguous optional-value spelling in the preferred interface:** `--force[=MODE]`, with bare `-f`/`--force` meaning reread. I recommend requiring `=` for explicit modes (`--force=overwrite`, `-f=reread`), rather than silently making bare force depend on argument order. This is a syntax adjustment to the requested space-separated form, justified by the experiment below. If accepting `--force overwrite` is non-negotiable, use the documented alternative below rather than pretending clap resolves the ambiguity.
8. **Launch overwrite conservatively.** Require a managed reference, safe annotation state, immediate transaction execution, and a verified archive. Do not turn it into an unqualified permission to bypass PDF coordination, sync conflicts, unrelated path collisions, or ambiguous task state. Reread can use the normal queued birth flow; overwrite should refuse when it cannot complete safely.

I would keep the requested mode names for familiarity, while help and results describe overwrite as “archive and rebuild.” A separate `bob ref reread` and `bob ref rebuild` could eventually be more expressive, but adding two commands now would create another interface migration without removing the hard storage work. Reopening the existing reading task is a cheaper alternative when all that is needed is another pass over the same annotations; it does not satisfy the requested separation of observations.

**The CLI contract, including the parser tradeoff.**

Recommended examples:

```sh
bob ref create https://example.com/essay -P work
bob ref create https://example.com/essay -P work -f
bob ref create https://example.com/essay -P work --force=reread
bob ref create https://example.com/essay --force=overwrite
bob ref create https://example.com/essay --force=overwrite \
  --existing ref/blogs/essay__v2.md --dry-run
```

A selected existing reference supplies a default parent for a forced duplicate operation; explicit `-P` may choose the new reading's parent in reread mode. Overwrite keeps the current task's actual residence. An incompatible parent/name/type/status override should fail before work in the first implementation, rather than quietly turn overwrite into a move, rename, or task reopening operation. Title/author/published overrides may change fresh source metadata and must appear in the preview.

Suggested help text:

```text
-e, --existing <REF>    Select the existing reference for a forced duplicate operation
-f, --force[=<MODE>]    Allow a duplicate source: reread creates a separate reading;
                       overwrite archives and rebuilds the selected reference
                       [bare flag: reread] [values: overwrite, reread]
```

Without the option, a known duplicate exits nonzero before fetching, prints its title and vault-relative path, and offers two clear actions:

```text
error: This source is already in your library.
  Attention Is All You Need — ref/papers/attention_is_all_you_need.md

Start a new reading:  bob ref create <source> --force=reread
Archive and rebuild: bob ref create <source> --force=overwrite
Preview either action with --dry-run.
```

Actual diagnostics should include all matches and supply shell-safe arguments where concrete commands are rendered. Remove the current suggestion to delete the note to recapture: it is incomplete advice for a bundle with a PDF, task, and sidecars.

I compiled a standalone program against **clap 4.6.7**, the version in this checkout's `Cargo.lock`. It used a repeatable positional TARGET and a `force` argument with `num_args(0..=1)`, `default_missing_value("reread")`, and a two-value parser. It ran in disposable workspace scratch, without invoking Bob or contacting a source URL.

| Input after the program name | Optional value, no equals requirement | With `require_equals(true)` |
| --- | --- | --- |
| `URL` | force absent | force absent |
| `URL --force` | reread | reread |
| `--force URL` | `InvalidValue`: URL consumed as mode | reread; URL remains TARGET |
| `URL --force overwrite` | overwrite | reread; `overwrite` becomes a second TARGET |
| `--force=overwrite URL` | overwrite | overwrite |
| `URL -f reread` | reread | reread; extra TARGET `reread` |
| `--force -- URL` | reread | reread |
| `URL --force overwite` | `InvalidValue` | reread; extra TARGET `overwite` |
| `URL -f=overwrite` | overwrite | overwrite |

These are observed parser results, not inferred Bob behavior. The current multi-target validator requires URLs, so an equals-only design also needs a focused diagnostic for misplaced mode tokens instead of a confusing collection error. Do not advertise the spaced form if it is not consumed as a mode.

Clap documents optional missing values together with zero-or-one arity and an equals requirement to remove positional ambiguity. The relevant primary API documentation was available for 4.6.6; the lockfile's 4.6.7 behavior was established by the experiment above. [Clap Arg documentation](https://docs.rs/clap/4.6.6/clap/struct.Arg.html#method.default_missing_value)

If the original spaced syntax must remain exactly as requested, standard clap without `require_equals` supports `TARGET --force overwrite`, `TARGET --force`, and `--force -- TARGET`. Document that bare force belongs after TARGET or before another option/`--`, and explicitly test the failing `--force TARGET` case. A custom lookahead that consumes only the two recognized mode words can support more placements, but then misspelled modes become positional inputs and option-value/alias handling needs its own parser contract. I would not introduce that custom preprocessing for this feature.

Store the result as `DuplicatePolicy::{Reject, Reread, Overwrite}`, with absence mapping to Reject. Do **not** use `default_value("reread")`, which would enable duplicates when no flag was supplied. Reject repeated force options and invalid attached values as usage errors. Keep short aliases, alphabetical help ordering, and hidden historical command aliases consistent.

**Define duplicate identity before writing anything.**

Keep the existing URL equivalence rules: tracking parameters/fragments are removed; syntactic URL keys, arXiv equivalences, and list-valued metadata participate. Do not broaden equivalence based on similar titles, redirects that have not been observed, or guessed URL transformations. Preserve the actual source URL(s); do not append fake query strings merely to defeat deduplication. [S2, S12]

Replace first-hit lookup with a typed result containing sorted, deduplicated matches, source keys, match evidence, whether each match is a ref/intake item, and its complete source set. Distinguish these questions:

- Does this input overlap any known reference?
- Does it describe the same complete reading unit?
- Which exact existing reference, if any, has the user selected for replacement?
- Which output paths and IDs are occupied, independently of source identity?

For overwrite, exact source-set equality matters. Given existing packet `{A, B}`, input `A` must not replace the packet. Given existing `{A}` and `{B}`, input `{A, B}` must not delete either or merge them by accident. The set comparison can ignore URL order for identity; the new document still follows argument order, and a reordered rebuild must be reported. In the first version, refuse forced operations on partial collection overlap with a message listing the overlapping members and explaining that packet restructuring is outside the operation. This is a deliberate limit on “allow duplicates,” preserving a clear reading-unit boundary.

After rereads exist, the same complete source set may legitimately have several refs. Reread can allocate another member when those matches form one verified reading family. Overwrite must demand `--existing` if more than one active reference matches. Even when one row is “primary” in `find`, that is presentation order, not destructive authority. Unrelated or malformed existing duplicates need explicit selection and must remain diagnosed.

For local PDFs/Markdown, retain existing conservative collision refusals, but label title-based evidence honestly. Require `--existing` before overwriting a title-only candidate. A matching stem/title is not proof that two documents are the same work. A later content-hash index could improve byte-identical detection, but a rendered/stamped PDF's hash is not the original source's hash, and content changes are often intentional. Do not expand this feature into universal local-file identity tracking. Vault-note snapshots retain their special behavior stated above.

**The mode matrix I would ship.**

| Situation | No force | Reread / bare force | Overwrite |
| --- | --- | --- | --- |
| No known duplicate | Normal create | Normal create, without artificial `__v2` | Refuse: nothing to rebuild; omit force for normal creation |
| One exact managed ref | Useful duplicate error | New reading bundle | Snapshot and rebuild that ref |
| Several readings of one verified source unit | List existing refs and refuse | Next available family number | Require `--existing` |
| Only a legacy PDF-less ref matches | Duplicate error for explicit `ref create` | New managed reading, leave legacy bytes intact | Initially refuse; legacy migration is not a rebuild |
| Exact queued intake item, no ref note yet | Already-queued error | New independent queued/born reading | Snapshot the queued bundle, replace that selected intake item, then ingest safely |
| Partial packet overlap | Refuse with member list | Refuse in initial scope | Refuse; never infer multiple deletions |
| Unrelated path or ID collision | Normal collision allocation/refusal | Skip occupied version number | Refuse; force is scoped to the selected ref |
| Already marked PDF as input | Existing attach/sync guidance | Require a clean original or supported source URL | Same; never call stamping a reset of annotations |
| `--listen` on a known source | Preserve existing attach behavior | Narrate the new reading | Narrate staged replacement, archive old audio |
| Unsafe immediate ingest | Existing queue behavior | May queue a new uniquely allocated bundle | No replacement; fail with a specific retry action |

The no-match overwrite refusal is another intentional requirement clarification: an operator asking to rebuild an existing object should learn when it was not found. For legacy refs, tightening explicit CLI creation is consistent with the user's request but must not silently change automatic capture/job/gkeep producers. Those producers should keep their existing default duplicate/attach/legacy policies unless their contracts are changed separately. [S13]

For duplicate forced operations, initially disallow `--output` and `--name` from overriding the selected/allotted identity. This avoids silently suffixing an explicitly exact output path or accidentally replacing an unrelated file. Ordinary fresh creation retains both options. `--existing` narrows selection; it does not waive source-set mismatch or path safety checks. Do not reinterpret an existing `ref/*.md` TARGET as an existing-reference selector: today Markdown is source material to render.

**Reread: one new reading, one new bundle.**

Use the original reference's current stem as the family base when first establishing a family. Record provenance on the new reading: an exact `reread_of` link to the designated base reference and a numeric `reading_number`. Existing notes need not be rewritten to acquire provenance. Subsequent rereads follow the recorded base, not the latest filename. Thus rereading `essay__v2` normally produces `essay__v3`, never `essay__v2__v2`. Do not strip an apparent version suffix from arbitrary old filenames without provenance: `protocol__v2` might be a legitimate original title.

These fields need a declared schema and transport through queued birth. A practical implementation is declared provenance fields in the PDF marker and note, with appropriate sync handling; another is a typed persisted birth intent. They cannot be undeclared ad hoc fields that disappear during scan or generate unknown-field warnings. Prefer the marker route if it fits the existing projection model cleanly. Keep history-list metadata out of PDF marker conflict resolution. A base rename must update provenance links through the supported rename machinery. Cycles, missing bases, or a disagreement between family metadata and source sets must fail closed for automatic family selection.

For each integer N beginning at 2, build the entire candidate `base__vN` bundle and ask whether it is available. Check all reference-type directories and configured roots, with case-insensitive ID and filename collision protection for cross-platform use. Reserve at least:

- Note and PDF paths; Markdown and textbundle sidecars.
- Image/asset directories, companion audio, and any persisted pending operation reservation.
- Recorded reference IDs throughout `ref/`, and version identities still retained by a history manifest.

Use the same final stem as the recorded ID, including on local forced rereads that would otherwise omit an ID without `-i`. Allocate a fresh reading-task block ID with the existing task allocator, rather than copying the previous task's ID. Create fresh sync metadata and annotation state. Leave the original note, task, and annotation contents alone. A new reading starts ready by default, subject to existing explicit creation-status semantics; it does not inherit another reading's Today links, dependencies, or completion dates.

`essay__v2` occupied plus `essay__v4` occupied means choose `essay__v3`. A naked unrelated `essay_2` does not mean “reading 2.” A base whose stem is already 80 characters needs a deterministic suffix-aware truncation policy or a clear naming error; silently truncating two candidates into the same path is unacceptable. Never silently revert to the ordinary `_N` allocator once the user requested reread.

Keep the literary title unchanged in frontmatter. Present “Reading 2” beside it in reports, list rows, and the note's small provenance line. Filename syntax should not become title clutter. `ref find` should return all readings with their paths, numbers, and states; do not silently change its existing primary-ranking contract as part of this work. `ref list` should retain all non-superseded readings appropriate to its filters. Suppress `duplicate_identity` only for a validated intentional family, not merely because filenames look versioned. Legacy supersession also needs to recognize an intentional reread relationship so a retained older reading is not hidden by the generic PDF-backed rule.

Fetch/render the source again for each reading; show the capture date. That may yield a newer document from a mutable URL. An arXiv `__v2` reading number is independent of arXiv's own edition. Reusing an old PDF while deleting its annotations is not a safe generic substitute: the current PDF route stamps without removing other annotations. [S5]

**Overwrite: preserve history as part of the reference.**

Keep the selected active note path, recorded ID, PDF destination, and reading-task identity. Preserve a valid original `created` date; record a rebuild timestamp separately. Regenerate source metadata and the note body from the fresh material, restore the managed reading-task embed, and add the cumulative annotation-history links. Move old free-form note content into history as requested; do not quietly carry all old prose into the freshly rebuilt note.

For an existing reference with an invalid or mismatched ID/stem, refuse with the existing repair guidance before overwrite instead of combining identity repair and reconstruction. Preserve an id-less historical object as id-less unless a separately documented upgrade is needed. Snapshot unknown frontmatter rather than throwing it away; the preview must make clear that arbitrary old metadata and prose will live in history, while the active note contains the new template and preserved structural identity.

I recommend a visible, vault-synced history root **outside `ref/`, `lib/`, and `xlib/`**, for example:

```text
ref_history/
  20261025T143012Z-<unique-operation-id>/
    annotations.md       readable, inert historical view
    original.md.txt      exact original note bytes
    original.pdf         saved PDF bytes, when one existed
    sidecar/             exported Markdown/textbundle, if present
    assets/              assets needed by historical annotations
    audio/               prior companion audio, when relevant
    manifest.json        paths, hashes, source identity, task locator, prior history
```

The operation ID prevents timestamp collisions and does not depend on a mutable reference stem. The archive's `parent` links to the active reference, satisfying vault note conventions. Its title is readable, such as “Attention Is All You Need — annotations saved 25 Oct 2026.” The manifest records UTC time and original paths; display dates can follow the vault's conventions. Copy rather than hard-link mutable files. The source note snapshot is byte-for-byte exact, including frontmatter and previous history links.

Why two note representations? A raw archived `.md` can reintroduce active checkboxes, `#task` tags, reading-task embeds, and legacy status records. The `.md.txt` file is the authoritative lossless snapshot. `annotations.md` is a generated reading view: ordinary prose/quotes remain readable; tasks become inert checkbox glyphs with no active task tags/IDs; task embeds become static locators; highlight/section anchors remain for links; metadata is archive metadata rather than `type: [[ref]]`. Preserve source block anchors needed by annotation links, while avoiding registration of duplicate task identity. Retarget PDF links and assets to the archived bundle. Test this renderer on manual sections, code fences, image annotations, sections, and continuation highlights. Do not use a regex that accidentally rewrites quoted code.

Explicitly exclude `ref_history` from task/capture/ref maintenance walkers and any client task scanning that needs it. The inert view provides defense even for generic Obsidian task queries; location exclusion alone is insufficient. Archives are readable history, never live refs or fresh task sources. Keep archive files out of mutation rewrites; raw bytes and manifest hashes must remain stable. `doctor` may validate them without repairing their contents.

The active note gets a compact block outside the regenerated Highlights region:

```markdown
## Previous annotations

- [[ref_history/20261025T143012Z-…/annotations|25 Oct 2026 · 18 highlights]]
- [[ref_history/20260904T091500Z-…/annotations|4 Sep 2026 · 9 highlights]]
```

Store the list in one typed, command-managed field and render the block from it. Do not parse arbitrary prose to recover history. Each overwrite carries forward the entire existing list plus the new entry, deduplicated by stable archive identity. Do not require traversing a chain of old notes to find earlier readings. Preserve pre-existing valid links, including unresolved ones with a warning; silently dropping an old entry because it cannot currently be opened violates the requirement. Never overwrite an old archive, auto-prune it, or hide it under a gitignored path. Verify Git tracking rules and size constraints before replacing the active bundle.

**Links and extracted work are part of the transaction.**

A plain link to `ref/papers/essay` should still open the rebuilt current reference. A link to `essay#^h-…`, an annotation section, or another removed fragment should reach the frozen historical content. Plan selective inbound fragment rewrites to `annotations.md`, preserving anchors and aliases. Include routed follow-up task backlinks and links from `done/` and prior daily notes, not just active top-level notes. Existing rename-link scanning offers reusable parsing, but its whole-bundle substitution is not sufficient for the distinction between current-note links and historical fragments. [S10, S14]

Keep extracted tasks' state, IDs, and `[h::]` history. Do not delete/recreate them from the archive or reimport old tasks on the next scan. Tasks remain actionable in their existing locations; the archive contains a historical rendering, not another live copy. Avoid resetting annotation-dedup bookkeeping blindly where it would recreate routed work. Rebuild success includes a second sync proving that the old sidecar and processed tasks do not repopulate the new reference.

Arbitrary user-created headings/block IDs need the same accounting as generated `^h-`/`^s-` anchors. Where a link is ambiguous or cannot be safely represented, refuse overwrite with the affected paths instead of claiming links were preserved. Known vault links can be rewritten; copied external `obsidian://`/Highlights deep links cannot all be discovered. State that limit in the command contract. The history view must link to the archived PDF, because the same page number in a fresh render may mean something different.

**Reliability: a small transaction, not a sequence of hopeful writes.**

The existing code has useful components: scoped Git commits, locked intake, preimage checks, atomic copies, rename rollback, and coordinated marker writes. They do not collectively make arbitrary multi-file replacement crash-atomic. In particular, the current `atomic_write` helper renames a temporary file but does not have the same explicit file/directory flushing as `atomic_copy`. An overwrite implementation needs durable snapshot and journal primitives rather than assuming every helper already offers crash recovery. [S7, S14, S15]

Use these phases:

1. **Resolve and preflight.** Classify the source, collect every match, resolve selection, reject incompatible options, identify the full old bundle/task/links, and plan the destination. Dry run stops before persistent staging, history allocation, locks that mutate state, or vault writes. Duplicate-rebuild previews should use known metadata without fetching; disclose that a later render may fail or change metadata. Other existing dry-run routes currently may fetch, which should remain documented rather than misrepresented as offline. [S3]
2. **Prepare privately.** Download/render a clean candidate and optional narration into private staging. Validate pages, marker round-trip, source identity, companion sizes, and usable output before modifying the old reference. A failed preparation leaves the active bundle untouched.
3. **Lock and revalidate.** Take the established `bob_sync.lock → scan.lock` order, pre-sync, rebuild the source/occupancy index, and verify the selected note, PDF, task, sidecars, assets, and touched link files against their planned hashes. Do not hold broad vault locks throughout a minutes-long web render. Replan a new reread's free suffix under lock; abort an overwrite if its selected preimage has changed.
4. **Secure the saved PDF state.** Use the accepted per-PDF coordination policy around the whole protected operation; do not select `.forReplacing` because the product calls this overwrite. Recheck bytes after any coordinated save. Changed/uncertain annotation state means no replacement and a specific sync/retry message.
5. **Publish the immutable snapshot and intent.** Exclusively create the archive, copy and flush its files, verify checksums, then persist a journal listing operation ID, before/after hashes, affected paths, and phase. Refuse if the archive is incomplete, untracked by vault Git rules, or would violate size constraints.
6. **Install and verify.** Replace the active PDF/note, remove or relocate stale sidecars/audio from active discovery, apply history and selective link rewrites, and preserve the task. Use expected-preimage checks and same-filesystem staged replacements. Verify identity, links, history, task count, clean sync planning, and absence of duplicate task import. Keep all touched path preimages for rollback.
7. **Commit and report.** Create one scoped commit containing the new active bundle, history, and needed link changes. On failure before the commit, restore before-images only where current bytes match this operation's after-images. Never overwrite a concurrent editor's changes during rollback. If rollback cannot finish, keep the journal, refuse further mutation of that reference, and show exact recovery paths. After a successful local commit, a push failure is “rebuilt; push pending,” not an instruction to run overwrite again.

After process death, a subsequent command must recognize an incomplete intent before normal scan/create can consume a half-replaced bundle. Recovery must either finish that same operation or restore it without minting another history snapshot or reading. A completed invocation followed by a fresh explicit reread is intentionally another reading; only recovery of the same intent is idempotent. A generic job retry must not inadvertently turn one requested reread into several.

Rust documents that ordinary `fs::rename` can replace an existing destination and cannot cross mount points; a prior existence check is not a no-overwrite guarantee. Exclusive creation and the project's no-replace primitive are appropriate for history and reread allocation. These filesystem primitives protect individual publications; the transaction journal supplies the multi-file recovery design. [Rust rename](https://doc.rust-lang.org/std/fs/fn.rename.html), [Rust File::create_new](https://doc.rust-lang.org/stable/std/fs/struct.File.html#method.create_new)

**Cross-host and open-editor limits must be explicit.** Local locks do not serialize two machines, and pre-sync cannot prove the Mac has no unsaved annotations. The accepted project policy makes the Mac the annotation-sync owner and uses bounded `.forMerging` coordination there. That policy was validated for marker updates; whole-PDF replacement still needs its own real-Highlights acceptance exercise. Do not assert that a Linux overwrite is safe merely because its local hash did not change. [M3, M4]

For the first release, permit library-PDF overwrite only on the annotation-owning Mac with a verified per-PDF safety check; require the saved PDF and note to be in a clean supported sync state. If coordination saves changed bytes, stop and require an annotation sync before retrying rather than archive a misleading stale projection. Reread remains available on other creating hosts. Expanding destructive overwrite across hosts requires either a positive owner/quiescence protocol or centralized execution; adding a remote queue with an unbound “overwrite later” instruction would be unsafe. This temporary restriction is a cost of reliable overwrite, not a new restriction on ordinary ingest-at-birth.

Even reread allocation across machines can race on the same smallest N. Retain pre-sync, collision detection, and no-clobber publication; on a remote conflict preserve both results and report it, never silently replace. If collision-free distributed numbering becomes a requirement, reserve through one authoritative writer. Do not introduce a distributed lock system merely to make this first feature look universal.

**Implementation seams and a sensible delivery order.**

| Slice | Likely files/components | Completion condition |
| --- | --- | --- |
| Source resolution and policy | `sources.rs`, `collection.rs`, `create.rs`, `clip.rs`, `stamp.rs` | Typed all-match result; policy separate from path-overwrite permission; route parity |
| Reread identity | `stamp.rs`, `pdf_target.rs`, `companion.rs`, marker/projection fields, `ref_tasks` | Whole bundle allocated once; queued ingest retains provenance; task is independent |
| Library presentation | `ref_library/row.rs`, `mod.rs`, `find.rs`, `resolve.rs`, output | Intentional families visible, accidental duplicates still diagnosed |
| History | New focused history planner/renderer, shared scan exclusions | Exact raw bytes plus usable inert archive; cumulative links survive repeated overwrite |
| Transaction | `intake.rs`-style session, `io.rs`, existing rename transaction patterns, marker coordinator | Durable intent, before-image recovery, preimage refusal, one scoped commit |
| Link/task preservation | `rename/links.rs` parser reuse, `ref_tasks`, annotation task pipeline | Old anchors reach history; no task loss, reopening, duplication, or stale reimport |
| Interfaces and docs | clap definition, completion, help fixtures, `docs/highlights-create.md`, `docs/ref.md`, sync contract, generated CLI reference | Accurate mode and option-interaction contract, aliases behave identically |

Start with the resolver and reread path, because it is additive in stored content and exposes family/index assumptions early. Build the history format and transaction executor next; release overwrite only when preservation and failure tests pass. Keep the API as a planned complete design, but do not advertise an overwrite mode that only snapshots Markdown and hopes the next scan behaves.

The source inspection covers bob-cli; I did not inspect the linked plugin or Mac Capture repositories. Before implementation lands, audit their CLI invocations and rendering of reference rows, multiple source matches, and archive exclusions through their authorized linked workspaces. No new app parsing of capture grammar or direct app vault writes is needed. Automatic producers should continue to use their explicit existing policy rather than inherit the new bare-force default.

Mark the eventual CLI contract change with a breaking Conventional Commit subject, as required by the release-train policy. Do not manually edit Cargo.toml's package version or CHANGELOG.md. Audit scripts/tests that previously used bare force to overwrite intake/output/audio, regenerate help/reference docs, and run the documented documentation gate. Preserving old and new semantics for the same bare flag is impossible; acknowledge the migration rather than invent a context-dependent default. [M5]

**Acceptance tests that matter.**

- Parser matrix: absent option, bare short/long forms, both modes, attached spelling, typos, empty/repeated values, before/after TARGET, `--`, multi-URL targets, historical aliases, completion, and mode-specific help. If the spaced contract is chosen, exercise its positional limitation explicitly.
- Duplicate refusal before any fetch, browser, render, narration, or mutation; URL spellings, arXiv editions, list-valued `url`/`source_url`, legacy-only hits, multiple readings, and partial packet overlap.
- Suffix gaps, unrelated `_2`, naturally version-shaped base names, renamed roots, missing/cyclic lineage, case variants, ID-only collisions across types, sidecar/audio/assets-only occupants, long stems, pending reservations, and contention. Check actual final ID and task block ID, not just the success string.
- Two successive overwrites preserve byte-identical original note snapshots and all prior history links. Include manual YAML, CRLF, comments, code fences, annotations with images/sections/continuations, old audio, and pre-existing history entries.
- Active, Next, Pending, blocked, completed, archived, and ambiguous reading tasks. Overwrite must not silently reopen or duplicate them; reread creates an independent task. Existing dependencies, daily links, and dates retain their meaning.
- Historical fragments and routed follow-ups resolve into frozen history; plain note links still resolve to the active note. Archives never become library rows, captured duplicates, task candidates, new annotation tasks, or mutated scan targets.
- Fault injection after render, archive-file copy, journal flush, every install/rewrite boundary, verification, commit, and push; kill/restart recovery; disk-full, permission, read-only filesystem, unsafe/symlinked destination, and concurrent edits. Verify that each failure leaves an intact old or committed new state, or an explicit recoverable held transaction.
- A second `ref sync`/scan after each successful mode is clean or makes only the documented fresh changes. It must not resurrect the prior sidecar's annotations, reset provenance/history, or duplicate extracted work.
- macOS acceptance with unsaved Highlights annotations, an open PDF, coordination timeout, changed marker, sidecar lag, and subsequent editor save. Cross-host collision exercise with a bare Git remote and independent vault clones. Do not substitute Linux-only fakes for this acceptance.

Only the isolated clap experiment was executed for this research. Existing source tests were inspected as evidence of current contracts; no claim is made that the proposed transaction or archive format has been implemented or end-to-end tested.

**Evidence map.** Source links below pin the examined commit; all repository content was read from the authorized local checkout. External API links were consulted on 2026-10-25. The audited memory decisions are project policy, while the new schema, transaction, UI, and scope choices above are recommendations.

| Ref | Evidence |
| --- | --- |
| S1 | [create CLI, options, dispatch, listen interception](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/highlights_ref/create.rs#L323) |
| S2 | [source collection and duplicate policy](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/highlights_ref/sources.rs#L92) |
| S3 | [create behavior contract: dedupe, output, listen, intake](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/docs/highlights-create.md#dedupe) |
| S4 | [default collision allocator and exact-output checks](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/highlights_ref/stamp.rs#L272) |
| S5 | [local/marked PDF refusals and stamp behavior](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/highlights_ref/pdf_target.rs#L387) |
| S6 | [collection overlap rules](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/highlights_ref/collection.rs#L1125) |
| S7 | [locked intake, queue results, and scoped write sequence](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/highlights_ref/intake.rs) |
| S8 | [reading-task collision allocation](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/ref_tasks/insert.rs#L68), [sync preimage validation and execution](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/highlights_ref/sync.rs#L1902) |
| S9 | [index membership and duplicate/supersession behavior](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/ref_library/mod.rs#L781), [primary ranking](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/ref_library/resolve.rs#L78) |
| S10 | [annotation identity, assets, follow-ups, and v2 task contract](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/docs/highlights-ref-sync.md) |
| S11 | [task file walk](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/capture_dependency_tasks.rs#L205), [ref-task walk](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/ref_tasks/walk.rs) |
| S12 | [URL normalization](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/highlights_ref/clip_url.rs) |
| S13 | [automatic ingest's fixed defaults and pre-/under-lock dedupe](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/highlights_ref/ingest.rs#L604) |
| S14 | [rename locking and transaction/rollback](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/highlights_ref/rename/plan.rs#L183), [inbound-link parser](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/highlights_ref/rename/links.rs) |
| S15 | [atomic write/copy primitives](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/highlights_ref/io.rs#L173), [PDF write coordinator integration](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/src/native/highlights_ref/marker_write.rs) |
| S16 | Existing behavioral assertions: [create](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/tests/cli/highlights/create.rs), [URL routing](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/tests/cli/highlights/url_routing.rs), [ingest](https://github.com/bobs-org/bob-cli/blob/a8ef17181eaaa6b1ab31773fc55eaf79a8d0eff1/tests/cli/highlights/ingest.rs) |
| M1 | Audited memory: `decisions:reference-ids-follow-file-stems` — reference ID follows stem; task block ID does not |
| M2 | Audited memory: `decisions:reference-renames-keep-identity` — bundle/link scope, with the ID rule superseded by M1 |
| M3 | Audited memory: `decisions:references-are-ingested-at-birth` — lock order, scoped commit, local queue, Mac annotation owner |
| M4 | Audited memory: `decisions:open-pdf-writes-are-coordinated` — bounded `.forMerging`, holds, no destructive coordination fallback |
| M5 | Audited memory: `decisions:bob-cli-releases-ride-a-daily-train`, `cli_rules.md`, `docs.md` — breaking-change notation, aliases/help, documentation gates |
| M6 | Audited memory: `obsidian.md`, `glossary:reference-note`, `glossary:reference-task` — parent convention, gitignored roots, reference/task vocabulary |

**Recommended solution.** Implement a typed duplicate policy with bare force defaulting to reread, a provenance-backed `__vN` allocator, and an explicit existing-reference selector for ambiguous or weakly identified replacements. Prefer attached explicit mode values to eliminate positional ambiguity. Reread creates a fresh bundle and independent reading task; overwrite stages fresh material, preserves the selected task and structural identity, snapshots the full old bundle into visible inert history, preserves every previous history link, and publishes through a recoverable transaction. Ship overwrite only after annotation safety, link preservation, crash recovery, and a clean subsequent scan are demonstrated. The feature is worth building; the annotation archive and transaction are the feature's core, not cleanup to add after the flag works.
