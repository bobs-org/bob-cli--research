# Highlights podcast intake: source parity and a reference-first design

Researcher: cdx  
Date: 2026-10-06  
Scope: independent implementation research and critique; no application, vault, feed, or configuration changes. No other report or transcript from this research swarm was consulted.

## Decision

This is a good feature, provided its central invariant is **a reference note exists before Bob starts anything that can publish audio**. Treat `--listen` as an explicit request to create a listening edition of the same reference material, with a configurable subprocess supplying the audio service.

A literal “add a boolean, then run `sase-listen render TARGET -e full`” implementation would miss several important requirements:

- Today `create` writes a PDF, and a later `scan` writes the ref note.
- `-e full` is rejected for Markdown and artifact sources.
- A successful auto-publish render can still leave publication queued or skipped.
- `clip` already imports many PDF URLs, but its detection differs from sase-listen and it has no arXiv paper resolution.
- Importing an already annotated PDF requires different marker placement from stamping a freshly rendered PDF.
- Running the current command again after an audio failure can hit its own URL/PDF collision checks.

The solution should fix those seams, reuse the existing PDF and note machinery, and keep feed hosting, speech synthesis, and credentials outside Bob.

## What the repositories actually do

The research used these source snapshots, opened through `sase repo open`:

| Repository | Snapshot | Relevant evidence |
| --- | --- | --- |
| bob-cli | `c2aec5703ce28e437881b1ce4633e9a8e706e5c0` | create, clip, shared stamping, note sync, config, intake documentation |
| sase-listen | `f8154ad0708141e6cb7c674c1130015f262a8a2a` | source dispatch, PDF fetch, arXiv resolution, edition writing, publication, CLI progress |
| chezmoi | `8efdb68cc562a0f111b8f26b5fef36ae32ad858c` | Bob config, sase-listen feed config, Mac intake script |

Code behavior takes precedence over a broad command description. The online sase-listen documentation was unavailable through the web tool; its documentation and implementation were read from the audited checkout instead.

### Bob already has most of the document plumbing

`src/native/highlights_ref/create.rs` accepts an existing Markdown file, renders with pandoc, stamps a marker, and atomically installs the PDF. Its ordinary default is `xlib/chat/<stem>.pdf`. It does not write the ref note. The note comes from `scan` or `sync`. Existing companion-audio discovery and copying are separate behavior: explicit audio, an episode ID in input frontmatter, or a sibling narration-script hash can bind an already existing MP3. That is useful reuse, but it is not podcast creation. [B1, B2]

`clip.rs` handles URLs, provenance, naming, URL dedupe, and article metadata. The pinned adapter already probes for direct PDF responses, downloads their original bytes instead of printing HTML, and returns `kind: pdf`. Rust then reads the PDF Info title as a fallback and runs the shared marker installer. Therefore “support PDF URLs” is partly present under `clip`; it should become a shared source capability, not another independent downloader bolted onto `create`. [B3, B4]

The existing paths are valuable. `pdf_path_metadata` maps both `xlib/<type>/<stem>.pdf` and `lib/<type>/<stem>.pdf` to the same `ref/<type>/<stem>.md`. A note can therefore be created before intake moves the PDF without introducing a second note identity. The source PDF path and managed task/audio links must still follow that move correctly. [B5]

The Mac bridge matters: athena and apollo queue PDFs in gitignored `xlib/`; the Mac drains those queues and scans them. The documented fallback is a 15-minute cron run. Waiting for that bridge before creating the ref note would leave a period in which the phone could have a published episode without a reference record. [B6]

### Actual sase-listen target parity is broader than URLs

The current `render` source categories are:

| Input | Current sase-listen behavior | Proposed Bob behavior |
| --- | --- | --- |
| Markdown file | Normalize Markdown or use an authored narration script | Preserve current Markdown rendering and audio-discovery behavior |
| Narration-script Markdown | Recognize `narration: 1` frontmatter | Accept as Markdown; listener renders the authored script |
| Local PDF | Identify by suffix or PDF magic, extract locally, cache by content hash | Import a managed copy; preserve the caller’s source file |
| HTTP(S) HTML article | Fetch, extract, cache, generate an edition | Reuse Bob’s browser capture and print template |
| HTTP(S) PDF | Recognize MIME and appropriate PDF magic; extract the PDF | Download/import that PDF rather than regenerate its pages |
| arXiv paper URL | Convert supported paper URL forms to a canonical PDF URL | Resolve before document fetching, naming, and dedupe |
| `kind:path` artifact reference | Audited `sase artifact read`, then Markdown/script handling | Resolve through an optional configured artifact reader; render the returned Markdown |

Existing local paths should win over artifact syntax, and URLs must be recognized before treating a colon as an artifact delimiter. Broad parity should mean these documented source categories; copying incidental acceptance of arbitrary local text formats is unnecessary. No bare `arxiv:2602.16844` shorthand is implemented upstream; do not advertise it as parity. [L1, L2]

### “Full” does not mean a full transcription

URL/PDF `full` is an AI-written adaptation with a 2,400-word budget. It covers major sections in order, but is not a word-for-word reading. `verbatim` uses deterministic normalization, which also omits material such as code, tables, mathematics, references, and some PDF furniture. Describe the default as “Full AI adaptation” in any audio provenance shown on the note. Listening or publication must not automatically mark the source’s `^ref` task as read. [L3]

More critically, `load_source` rejects `edition in {"brief", "full"}` for sources that are neither URLs nor local PDFs. The rejection occurs before artifact reading or ordinary Markdown handling. A universal configured command ending in `-e full` would break Bob’s existing Markdown use case. [L2]

### Publication and output need explicit contracts

`render` uses `feed.auto_publish` for article/research kinds, while ordinary documents need explicit publication. Auto-publication can warn and return a successful render with `published: false`; a remote failure can additionally set `publish_queued: true`. Explicit `--publish` raises a failure when publication fails, while retaining the completed library episode and remote outbox behavior. [L4]

Bryan’s chezmoi-managed sase-listen config already sets `feed.host: apollo` and `auto_publish: true`. Its token is obtained through a command. This feature should reuse that setup; Bob does not need feed configuration, token storage, XML generation, SSH publishing, or a new AntennaPod subscription. The actual Bob source config is `home/dot_config/bob/config.yml`, deployed to the XDG Bob config path, rather than a config inside the vault. Bob supports `BOB_CONFIG_FILE` and `XDG_CONFIG_HOME` overrides. [C1, C2, B7]

The listener has an existing live stage checklist and plain non-TTY output. `--json` suppresses that display. Its stdout also contains the finished summary and its stderr contains progress/errors. Inherit both streams directly, flush Bob’s preceding output, and let the child see the real terminal. Do not buffer the process, truncate its output, prefix every line, or nest a second progress animation around it. [L5]

Publishing to RSS does not guarantee immediate arrival on the phone. AntennaPod refreshes feeds on a configurable schedule, with a documented default of 12 hours. Bob should say “published; refresh the feed in AntennaPod,” not “downloaded to your phone.” [A1]

## Critique and justified requirement adjustments

The idea is sound because it makes capturing the source and preparing an audio edition one deliberate action. It also gives a natural place to preserve source provenance and track reading independently of delivery format. The main risk is treating audio synthesis and publishing as if they were another atomic local file write.

I recommend these explicit adjustments:

1. **Create the ref note synchronously for `--listen`.** A queued PDF alone does not satisfy the tracking goal. Keep ordinary non-listening intake behavior compatible, but do not start the listener until the note has been written.
2. **Use `-e full` only for URL/PDF sources.** Markdown and artifact inputs use their existing script/normalization semantics. If Bryan later wants AI adaptation of Markdown too, that needs a separately designed provider capability.
3. **Make publication explicit in the configured sase-listen adapter.** Use `--publish`; avoid equating “render succeeded” with “episode is on the subscribed feed.”
4. **Preserve PDFs’ pages, not their exact bytes.** Adding Bob’s Highlights marker and the reference backlink changes PDF bytes. Do it to an imported copy; do not reflow the paper or overwrite the original local file.
5. **Retain the captured PDF and note if audio fails.** Report partial completion and a useful retry path. A remote publication cannot be safely undone as part of a local rollback.
6. **Do not make `--listen` automatically replicate every new MP3 into vault Git.** Feed publication fulfills the requested phone-listening workflow. Existing `--audio`/discovery keeps working; a new companion can be an optional adapter result. At 64 kb/s and 150 spoken words/minute, a 2,400-word edition is roughly 7.7 MB, so automatic archival is a meaningful storage policy, not a free detail.
7. **Define “always tracked” within this entry point.** Direct calls to sase-listen, Telegram audio, or another generator can bypass Bob. Reconciliation of all historical or independently created episodes would be a separate feature.
8. **Include artifact references if “same targets” is literal.** They are part of the upstream contract. An implementation restricted to files and URLs should be described as a scoped first release, not complete parity.

The optional flag is the right initial approach. I would not make all captures generate audio automatically: full adaptations can incur writer and synthesis costs and take time. A future provider-independent “listen to an existing reference” action is attractive, but it need not block this feature.

## Proposed command and configuration

Use:

~~~sh
bob highlights create <TARGET> -L
bob highlights create https://arxiv.org/abs/2602.16844v2 --listen
bob highlights create https://example.org/paper.pdf --listen
bob highlights create paper.pdf --listen
bob highlights create report.md --listen
~~~

`-l` already means `--lib-dir`, so use `-L` for `--listen`. Keep help options alphabetical and provide the project-required short aliases for any additional public options. Explain that listening creates the ref note immediately, that the configured command publishes audio, and that PDF files are imported without regenerating their pages.

Broaden `create` into the convenient public source entry point. Keep `clip` as a documented URL-focused command using the same implementation; do not remove it or independently evolve two URL/PDF pipelines. Reuse its metadata override arguments where they are useful on `create`, especially title and filename controls.

Proposed chezmoi change:

~~~yaml
highlights:
  pre_scan_hook: PATH="$HOME/bin:$PATH" bob_xlib_pull
  listen_command:
    - "~/bin/bob_highlights_listen"
    - "{target}"
~~~

Add `home/bin/executable_bob_highlights_listen` in chezmoi. This small provider adapter owns the sase-listen flags; Bob only knows a configured argv and a source context.

The configuration contract should be deliberately small:

- A nonempty argv array; no implicit shell evaluation.
- `{target}` substitutes one complete argument. URLs containing `&`, spaces in paths, and hostile punctuation remain literal arguments.
- Expand a leading `~` on the executable path explicitly. Preserve the caller’s working directory, and canonicalize local source paths before invocation.
- Missing/empty configuration is an actionable error when `--listen` is requested, with no implicit sase-listen fallback. Ordinary create/clip calls do not require the listener.
- Validate unknown placeholders and malformed config before expensive work.
- Pass provider-neutral environment context: target kind, original/canonical source identity, captured source-file path when available, ref-note path, and an optional result-file path. Names and enum values must be documented and versioned.
- Exit zero means the requested listening operation completed; nonzero means Bob reports partial completion. Cancellation stays distinguishable from an ordinary error.

For the configured adapter, the effective URL/PDF invocation is:

~~~sh
sase-listen render <canonical-target> -e full --publish
~~~

When Bob has the actual captured PDF/HTML bytes, the adapter should also use the provider’s `--html <captured-source>` option. It accepts saved PDFs as well as HTML. Canonicalize arXiv *before* doing this: upstream intentionally skips its arXiv rewriting when `--html` is supplied. This preserves the URL’s source identity while using the same captured material, rather than independently fetching a newer or differently gated page. [L6]

For Markdown and artifacts, omit `-e full`. The adapter must preserve the renderer’s stdout, stderr, and exit behavior. It should be a thin argv builder, not a parser of the rendered human summary.

This wrapper is worthwhile because the provider already has type-dependent flags. A direct argv such as `["sase-listen", "render", "{target}", "-e", "full", "--publish"]` is appropriate only for a URL/PDF-only command, not for the universal `create` target contract.

Artifact resolution needs its own optional reader seam if Bob supports that source category. A configured argv equivalent to `sase artifact read TARGET "bob highlights create"` can return audited Markdown to a scratch file. Keep this dependency dormant for ordinary files and URLs; do not resolve sidecar paths by scanning the filesystem. Prefer a stable artifact identity over the scratch filename in provenance.

## Source resolution and PDF import

Introduce a shared `ResolvedSource`/capture plan holding source kind, original target, canonical identity, actual captured bytes/path, title metadata, and proposed document identity. The PDF renderer/importer and listener both consume it.

Dispatch in this order: HTTP(S) URL; an existing local path; artifact reference; an explicit unsupported/missing-source error. Do not classify remote PDFs by a `.pdf` suffix alone.

### PDF URLs

Match upstream’s useful recognition cases: `application/pdf`, `application/x-pdf`, and octet-stream/missing content type with PDF magic. Its sniff checks the first 1,024 bytes for `%PDF-`. Validate the downloaded document before installing it. Bob’s current adapter only checks for `application/pdf`, so full parity needs an enhancement. Preserve Bob’s current public-network restrictions and redirect checks rather than copying weaker incidental upstream URL acceptance. [B4, L7]

Do not require pandoc or LaTeX for PDF imports. Ideally direct PDF acquisition should avoid needing a browser too; share the safe fetch/validation component with clip and retain the browser route for HTML. Respect existing limits: Bob’s capture ceiling relates to vault sync’s 95 MiB refusal, while the current listener accepts at most 64 MiB and 400 pages with no OCR. A PDF can be successfully captured even if the audio step later cannot extract it. Explain that as partial completion, not unsupported document intake. [B6, L3, L7]

Use PDF Info metadata and explicit overrides. Unknown author/publication metadata should be omitted instead of guessed. A PDF title is better than a URL slug when available.

### arXiv

Port the small pure URL recognizer into Bob’s source layer, with attribution/licensing appropriate to the upstream MIT code, rather than importing or shelling out to sase-listen to resolve targets. Match its fixtures:

- Exact hosts `arxiv.org`, `www.arxiv.org`, `export.arxiv.org`.
- `/abs/<id>`, `/html/<id>`, `/pdf/<id>`; optional `.pdf` only on the PDF form.
- Old-style IDs such as `hep-th/9901001` and `math.GT/0309136v2`; new-style IDs with four or five digits after the dot.
- Retain explicit `vN`; ignore query/fragment for paper resolution.
- Canonical acquisition URL `https://arxiv.org/pdf/<id>`.
- No fallback from a failed paper PDF fetch to the abstract page. [L8]

Dedupe all those URL forms by the canonical paper identity before launching an expensive listener. Use a stable ID-based filename, such as `arxiv_2602_16844v2.pdf`, and the actual title for display. Do not let a metadata/title correction create a second paper identity.

An unversioned identifier is not an immutable edition: arXiv documents that it displays the most recent version. Preserve a resolved version if available and record a source content hash; otherwise retain the captured snapshot and hash without inventing a version. Use the captured snapshot for audio so “same paper” means the material Bob actually archived. [A2]

Suggested defaults are `chat` for Markdown, `blogs` for HTML, and `papers` for PDF/arXiv inputs, with `--ref-type` overriding them. `papers` is a proposed new default, not an established vault taxonomy claim; books or other PDFs can select their existing type explicitly.

### Highlights markers and PDF backlinks

The import path must be annotation-aware. Today `embed_marker` appends a new text annotation, while `read_pdf_marker` returns the first standalone page-one text annotation. For a PDF that already contains such a note, the new Bob marker would not be selected. Ensure the Bob marker becomes the first eligible annotation while preserving existing annotations and their ordering otherwise. If an existing Bob marker is recognized, reuse/update it under the normal collision rules rather than silently producing competing markers. Do not heuristically overwrite an arbitrary existing annotation. [B8]

The inspected shared stamper creates a `/Text` marker; it does not itself create a URI backlink to the generated ref note. Existing Markdown listen-card links target companion audio. The requested “ref note linked from the PDF” therefore needs an explicit acceptance check and shared implementation, not an assumption that the marker already provides it. Use the stable ref-note path in an Obsidian URI, encoded with existing URI helpers. Test a real link annotation/marker interaction in Highlights and another reader; avoid inserting a cover page or drawing over the paper’s text. [B1, B8]

## Execution, recovery, and the intake bridge

Recommended order:

1. Validate flags, resolve config/executable, identify the source, and preflight known document/note collisions.
2. Acquire or render the source to scratch storage and finish metadata/path planning.
3. Install the managed, marker-stamped PDF and create/update this one ref note using the existing note planner, dirty-note checks, and atomic writer.
4. Record a listening attempt on that reference before starting the subprocess.
5. Run the configured listener synchronously with inherited streams.
6. Record success/failure/cancellation and any structured result, print a compact final receipt, and return a truthful exit status.

Do not shell out to global `bob highlights scan` for step 3. It runs the pull hook and touches unrelated queued/library PDFs; unrelated failures could block or confuse this capture. Extract the existing scoped note/sync operation into a callable internal function.

I prefer preserving the current intake bridge. Keep the captured PDF in `xlib/` when that is the planned output, but write its stable `ref/<type>/<stem>.md` immediately. Then make intake transition explicitly update the Bob-managed `^ref` PDF link and any companion embed when the document moves to `lib/`. Apply this only when the old link matches the previously recorded source; preserve authored checkboxes and unrelated body content. The note’s source path should truthfully reflect the current location. Test the transition, including a note transferred through vault Git before its PDF is pulled.

This permits a short interval in which a second device has the note but not the queued PDF. The original source URL remains usable, and the command should clearly label the PDF as queued. That is preferable to silently changing default output locations or awaiting the Mac before generating audio. If immediate PDF availability on every device is a hard requirement, choose scoped promotion into `lib/` and explicitly redesign the bridge; do not hide that behavior change inside a flag.

Honor `--output` exactly and preserve external-output support. A PDF outside managed directories should get its explicitly scoped note and retain the existing “scan will not discover it” explanation; do not invent a library move.

### Failure states must remain reviewable

| Failure point | What remains | Behavior |
| --- | --- | --- |
| Invalid config/flags or known collision | No new capture | Error before starting the listener |
| Acquisition/render/marker failure | No installed partial PDF; no podcast | Clean scratch work and report the cause |
| Note write fails after PDF install | Captured PDF; no listener launch | Report exact retained PDF and repair/retry path |
| Synthesis fails | PDF and ref note | Nonzero, record attempt failure, show complete provider output |
| Explicit publication fails | PDF/ref and possibly completed provider episode/outbox | Nonzero; retain all evidence, use provider publication retry |
| Ctrl-C after capture | PDF/ref and any provider cache | Record interrupted/unknown attempt; propagate cancellation |
| Process dies after publication but before receipt | Ref exists; outcome may be unknown locally | Require reconciliation/explicit retry, never claim exactly-once publication |

Do not erase successful capture merely because the optional listening step failed. Likewise, do not promise a distributed transaction between vault files and an RSS server.

A repeated `create TARGET --listen` must reuse the previously captured source/reference when it can verify the same identity. It should skip a recorded completed listening operation by default and resume a known failed one. Maintain current duplicate-ref refusal for ordinary capture and current protections against overwriting annotated library PDFs. Never repurpose Bob’s `--force` as permission to pass sase-listen `--force`, which bypasses structural lint.

Keep listening state separate from reference lifecycle status and separate from the existing scalar `audio` companion field. A small managed `listen` record can store attempt state, provider/episode identity when supplied, and edition provenance. Exclude it from PDF-marker property synchronization. Use a short per-reference lock to claim an attempt; avoid holding the vault-wide maintenance lock throughout network synthesis. Merge the final result into managed fields without overwriting edits made during rendering.

Full terminal output and machine receipts are compatible, but not through the provider’s current `--json` mode. The current renderer has no independent result-file switch. A generic optional `BOB_HIGHLIGHTS_LISTEN_RESULT_FILE` contract can accept an atomic, versioned JSON receipt from an adapter; adding `--result-file` upstream while retaining normal progress would make the sase-listen adapter clean. Treat that as a clearly scoped enhancement, not an existing capability. Do not parse Rich output, guess the newest manifest, use `publish --latest`, or scan every episode to infer which concurrent render belongs to this reference. In an initial hook-only implementation, store the attempt/exit result and let the explicit-publication adapter establish success; structured episode metadata can follow.

## A restrained, beautiful experience

Bob should provide a clear frame, then give the terminal to the listener:

~~~text
✓ Captured “Paper title”
  PDF        xlib/papers/arxiv_2602_16844v2.pdf · queued for library intake
  Reference  ref/papers/arxiv_2602_16844v2.md
  Source     https://arxiv.org/pdf/2602.16844v2

♫ Preparing listening edition…
[the configured command’s complete native output]

✓ Reference saved · listening command completed
~~~

For failure, retain the same receipt and say “Reference saved; listening failed,” followed by the concrete retry action. Do not print an unqualified green “done” after a queued or failed publication. Without a structured receipt, avoid claiming a specific episode ID or duration in Bob’s own summary.

The note should remain a reference note with its existing PDF task and managed Highlights region. Add only a small “Listen” detail/card when useful: full adaptation versus authored reading, provider episode identity if available, and an optional portable playback link or companion embed. Do not store the secret feed token in frontmatter, PDF links, or logs. Source provenance and the reference backlink matter more than a large new audio dashboard.

`--dry-run --listen` prints the planned PDF/note paths and safely displayed argv. It must not invoke sase-listen’s `--dry-run`: upstream can write an AI script and incur writer usage even in that mode. Existing Bob URL dry-run acquisition can retain its documented behavior, but it must not generate audio, publish, or persist ref/attempt state. [L3]

## Implementation slices and acceptance evidence

This is a feature spanning bob-cli and chezmoi; the optional machine-receipt enhancement adds a small sase-listen change.

1. Factor shared source/path planning from create/clip; add local-PDF, arXiv, artifact-resolution, and PDF-response parity.
2. Fix annotation-aware import, and validate the PDF-to-ref backlink.
3. Add scoped eager note creation and explicit intake link migration.
4. Add `--listen/-L`, typed argv configuration, full stream inheritance, cancellation, and reference-specific retry state.
5. Add the chezmoi config/adapter, docs/help/completion, and diagnostics. Apply chezmoi through its required deployment workflow during implementation.
6. Add structured receipts only if the first release promises episode metadata or stronger automated resume behavior; never silently simulate them with log parsing.

Meaningful acceptance tests should cover:

- Current Markdown create output and include-ID/audio behavior remain compatible without `--listen`.
- Fake listener argv with spaces, Unicode, quotes, `&`, and shell metacharacters is literal; malformed config/missing executable fails before launch.
- Both stdout and stderr pass through in full on success and failure; TTY/NO_COLOR behavior and Ctrl-C work.
- The fake listener can assert that the correctly typed/parented ref note already exists at process start.
- URL PDF recognition covers extensionless responses, aliases/octets/magic, redirects, invalid bodies, and size limits. No pandoc call for imports.
- Local original PDF is unchanged; the managed copy preserves page count, text, links, annotations, and outline.
- arXiv aliases, old IDs, versions, lookalike hosts, and failed PDF fetch/no abstract fallback match upstream fixtures.
- An existing standalone page-one text annotation never displaces the new Bob marker.
- Intake moves update only managed source links; subsequent scan is a no-op and human note edits survive.
- Capture failure never invokes audio; audio/publication failure retains the ref; rerun creates neither a second note nor an unnecessary PDF.
- `--listen` does not imply “read,” does not disable `--no-audio`’s existing discovery semantics, and does not forward Bob’s `--force` to provider lint bypass.
- Dry-run never invokes the listener or writes attempt state.

Research verification performed: a standard-library-only probe of the checked-out arXiv module verified five canonicalizing inputs and five rejecting inputs, including new/old/versioned IDs, host lookalikes, and the unsupported bare shorthand. No paid render, feed mutation, vault capture, deployment, or implementation test suite was run. Remaining live validation should be one article and one versioned arXiv paper in a scratch vault/feed, followed by manual Highlights backlink and AntennaPod refresh checks.

## Evidence references

All GitHub file links below point to source snapshots inspected locally, rather than web-fetched repository contents.

- **B1:** [Bob create implementation](https://github.com/bobs-org/bob-cli/blob/c2aec5703ce28e437881b1ce4633e9a8e706e5c0/src/native/highlights_ref/create.rs), particularly command construction, `create_pdf`, and audio URI generation.
- **B2:** [Highlights workflow and companion-audio contract](https://github.com/bobs-org/bob-cli/blob/c2aec5703ce28e437881b1ce4633e9a8e706e5c0/docs/highlights-ref-sync.md).
- **B3:** [Bob clip implementation](https://github.com/bobs-org/bob-cli/blob/c2aec5703ce28e437881b1ce4633e9a8e706e5c0/src/native/highlights_ref/clip.rs), especially direct-PDF metadata fallback and shared install.
- **B4:** [Pinned capture adapter](https://github.com/bobs-org/bob-cli/blob/c2aec5703ce28e437881b1ce4633e9a8e706e5c0/scripts/web_clip/web_clip_adapter.py), `_probe_pdf`, `_is_pdf_response`, `_download_remote_pdf`.
- **B5:** [Path metadata](https://github.com/bobs-org/bob-cli/blob/c2aec5703ce28e437881b1ce4633e9a8e706e5c0/src/native/highlights_ref/io.rs), [note generation](https://github.com/bobs-org/bob-cli/blob/c2aec5703ce28e437881b1ce4633e9a8e706e5c0/src/native/highlights_ref/note.rs), [scoped sync and scan](https://github.com/bobs-org/bob-cli/blob/c2aec5703ce28e437881b1ce4633e9a8e706e5c0/src/native/highlights_ref/sync.rs).
- **B6:** [Vault Git sync and Highlights bridge runbook](https://github.com/bobs-org/bob-cli/blob/c2aec5703ce28e437881b1ce4633e9a8e706e5c0/docs/vault-git-sync.md), “Highlights bridge.”
- **B7:** [Bob XDG config and Highlights schema](https://github.com/bobs-org/bob-cli/blob/c2aec5703ce28e437881b1ce4633e9a8e706e5c0/src/native/config/mod.rs).
- **B8:** [Shared marker installer](https://github.com/bobs-org/bob-cli/blob/c2aec5703ce28e437881b1ce4633e9a8e706e5c0/src/native/highlights_ref/stamp.rs), `embed_marker` and `stamp_and_install`; [marker reader](https://github.com/bobs-org/bob-cli/blob/c2aec5703ce28e437881b1ce4633e9a8e706e5c0/src/native/highlights_ref/marker.rs), `read_pdf_marker`.
- **L1:** [sase-listen render arguments](https://github.com/sase-org/sase-listen/blob/f8154ad0708141e6cb7c674c1130015f262a8a2a/src/sase_listen/cli/render.py) and [CLI contract](https://github.com/sase-org/sase-listen/blob/f8154ad0708141e6cb7c674c1130015f262a8a2a/docs/cli.md).
- **L2:** [Source dispatch and edition rejection](https://github.com/sase-org/sase-listen/blob/f8154ad0708141e6cb7c674c1130015f262a8a2a/src/sase_listen/pipeline.py#L475), `looks_like_ref`, `looks_like_pdf_file`, `read_artifact_ref`, and `load_source`.
- **L3:** [Article/PDF extraction and edition documentation](https://github.com/sase-org/sase-listen/blob/f8154ad0708141e6cb7c674c1130015f262a8a2a/docs/web-articles.md); [writer’s 600/2,400-word budgets](https://github.com/sase-org/sase-listen/blob/f8154ad0708141e6cb7c674c1130015f262a8a2a/src/sase_listen/writer/author.py).
- **L4:** [Publication rules and failure handling](https://github.com/sase-org/sase-listen/blob/f8154ad0708141e6cb7c674c1130015f262a8a2a/src/sase_listen/pipeline.py#L2394); [multi-machine outbox contract](https://github.com/sase-org/sase-listen/blob/f8154ad0708141e6cb7c674c1130015f262a8a2a/docs/multi-machine.md).
- **L5:** [Progress/JSON contract](https://github.com/sase-org/sase-listen/blob/f8154ad0708141e6cb7c674c1130015f262a8a2a/docs/cli.md) and `cli/render.py` in L1.
- **L6:** [Source acquisition, saved HTML/PDF, and canonical cache identity](https://github.com/sase-org/sase-listen/blob/f8154ad0708141e6cb7c674c1130015f262a8a2a/src/sase_listen/web/store.py#L205).
- **L7:** [MIME/magic validation and byte limits](https://github.com/sase-org/sase-listen/blob/f8154ad0708141e6cb7c674c1130015f262a8a2a/src/sase_listen/web/fetch.py).
- **L8:** [arXiv recognizer](https://github.com/sase-org/sase-listen/blob/f8154ad0708141e6cb7c674c1130015f262a8a2a/src/sase_listen/web/arxiv.py) and [parity fixtures](https://github.com/sase-org/sase-listen/blob/f8154ad0708141e6cb7c674c1130015f262a8a2a/tests/test_arxiv.py).
- **C1:** chezmoi snapshot above: `home/dot_config/bob/config.yml:49` and `home/bin/executable_bob_xlib_pull`.
- **C2:** same chezmoi snapshot: `home/dot_config/sase-listen/config.yml:11`, feed host and auto-publish fields only; no credential values were needed.
- **A1:** [AntennaPod: refreshing podcasts](https://antennapod.org/documentation/automation/refreshing-podcasts), accessed 2026-10-06.
- **A2:** [arXiv: version availability](https://info.arxiv.org/help/versions.html), accessed 2026-10-06.

## Recommended solution

Implement **reference-first `bob highlights create TARGET --listen/-L`** with a shared source resolver for Markdown, local PDFs, HTML/PDF URLs, arXiv paper URLs, and configured artifact reading. Preserve original PDF pages in a managed stamped copy, fix existing-annotation marker ordering, and provide a verified PDF backlink to the stable ref note.

Keep Bob’s intake bridge, but create the ref note immediately for listening requests and explicitly migrate its managed source links during later intake. Only then run a configured argv hook with complete inherited output. Put the sase-listen-specific adapter in chezmoi, use full adaptation for URL/PDF sources, omit that flag for Markdown/artifacts, and request publication explicitly.

Retain the reference on any audio failure, support verified reuse/retry without replacing annotated PDFs, and keep audio delivery state separate from reading status. Start with this small configurable integration; add a structured result-file contract when episode metadata or stronger automated resumption is required. This delivers the requested one-command workflow while keeping Bob responsible for the reference and the chosen audio tool responsible for the episode.
