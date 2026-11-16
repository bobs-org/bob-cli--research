**Video task captures and a unified `Z` media viewer — independent cdx research**

Researcher: cdx. Date: 2026-11-16. Scope: design research, not implementation. I independently inspected bob-cli, bob-plugins, Bob Mac Capture, project decisions, and primary external documentation. I did not consult any other report, transcript, summary, or researcher from this swarm.

**Recommendation: build this feature as an extension of Bob’s attachment workflow.** `%c` should import a local video and write a normal Obsidian embed as one child bullet; `Z` on that child should open a paused video player in the existing image viewer’s visual language. This is a good fit for short demonstrations of bugs, UI behavior, and procedures. The important work is preserving capture reliability and making viewing effortless. Merely adding `.mp4` to an extension list would miss memory usage, preview latency, codec failures, and vault synchronization.

For the supplied example, assuming that the source exists on the machine running `bob` and fits the proposed size policy:

```text
Clipboard: ~/tmp/screencasts/20261116_155943.mp4
Capture:   Investigate the capture panel flicker %c
```

The relevant output should be:

```markdown
- [ ] #task Investigate the capture panel flicker
    - ![[file/20261116_155943.mp4]]
```

This example omits ordinary task metadata and uses illustrative indentation. Production output must preserve the current target-note indentation rules. Put the cursor on the video child and press `Z`; press Space to play; press `Z` or `q` to return to the same editor position. The original recording stays intact.

I recommend retaining `file/` for videos. That is where Bob already saves them, so existing copies, references, and origin records continue to work. A new `vid/` directory is reasonable aesthetically, but it buys little functionality and creates another storage convention. If Bryan strongly prefers it, choose it explicitly for new imports and continue resolving old `file/` links; do not migrate existing attachments as part of this feature.

**The existing implementation provides most of the right semantics.** The following are findings from source, rather than guesses about the product:

| Area | What exists today | Implication for video |
| --- | --- | --- |
| Clipboard classification | Absolute paths, `~/`, quoted paths, angle wrappers, and percent-decoded `file://` paths become attachments. Other clipboard shapes retain text/snippet behavior. | Keep `%c`; do not invent `%v` or parse arbitrary prose for filenames. |
| File representation | `AttachmentKind` has only `Image` and `File`. Images become `![[img/name.png\|400]]`; other files become `[[file/name.ext]]`. | The example MP4 already takes the copy path, but gets a plain link. Add a video classification and embed representation. |
| Copies and collisions | Names are sanitized. The planner reuses matching bytes at a candidate destination and uses an eight-character SHA-256 suffix for conflicting content. | Preserve these rules. This is destination-based reuse, not a global content-addressed deduplication service. |
| Transaction behavior | Planning precedes writes; installation refuses overwrite races; created files are cleaned up on ordinary failure. Dry-run creates no files/directories. | A video is part of the same capture transaction, not a second asynchronous attachment upload. |
| Provenance | The journal records original path, display path, host, saved path, and content hash. `y` copies the origin; `r` restores a link to its original path while retaining the vault copy. | Reuse the existing origin journal and gestures. Video needs no separate provenance format. |
| Target selection | `Z` recognizes links and embeds on the current editor line, skips code, and chooses containing reference, then next, then previous. | Extend this ordered candidate list to images plus videos. Do not search a task’s descendants or open a gallery implicitly. |
| Key binding | The registered command ID is `zoom-image-on-line`; the vault Vim mapping invokes it. The plugin does not bind `Z` itself. | Preserve the command ID as a compatibility entry point; change its visible name to “View image or video on cursor line.” |
| Path-to-embed loop | `Z` on a path-only image bullet invokes `bob attachments import`, replaces only that span in one editor transaction, then opens the viewer. | Add the same path-only behavior for videos, including stale-editor checks and import-in-flight protection. |
| Mac decoding | `CaptureAttachmentOutput.kind` is a `String`. Presentation treats `image` specially and other kinds as files; thumbnails are loaded only for images. | The inspected app can decode `video` without an enum crash, but needs presentation work to say “video” and show an appropriate tile. |
| Vault transport | The vault uses Git sync; its ignore policy starts by excluding everything and selectively re-includes content. | New video support must include checking the actual vault allowlist and verifying an off-host copy. Copy success alone is insufficient. |

Sources: [capture planner][c1], [attachment model][c2], [planning and reservations][c3], [persistence][c4], [attachment contract][c6], [target resolver][p1], [command registration][p5], [path import][p3], [Mac models][m1], [Mac presentation][m2], and [vault sync coverage][c7].

**Three less obvious findings should shape implementation.** First, `plan_attachments` currently calls `fs::read` for every source, keeps bytes in `PlannedFile.contents`, and copies those buffers into reservations/plans. Existing-candidate comparisons also read whole files. The dry-run path uses this planner. The Mac app launches an authorized clipboard dry-run after accepted edits and refreshes when the clipboard counter changes. Consequently, a large recording can create repeated substantial allocations and reads while typing; “dry-run” does not mean “cheap.” This is a source-derived risk, not a measured memory benchmark. [Planner][c1], [plan cloning][c3], [Mac preview lifecycle][m4].

Second, origin lookup reads and hashes the vault file and can read/hash its original source. Opening a video should not wait for this work. The current image viewer already passes an origin promise into the modal, which is the correct pattern to retain. Streaming the importer alone would leave this second whole-file memory path behind. [Origin resolution][c5], [viewer opening][p1].

Third, both the Mac subprocess client and the plugin attachment API use a 20-second default command timeout. An unbounded import or conversion can exceed that deadline after some side effects have occurred. A larger timeout is not a substitute for bounded work, and a timeout must not be described as proof that nothing was written. [Mac process client][m5], [attachment API][p6], [plugin timeout constant][p7].

**Standard Obsidian embeds are the right durable representation.** Obsidian documents `.mkv`, `.mov`, `.mp4`, `.ogv`, and `.webm` as video formats and explicitly notes that playback depends on device codecs. Its normal embedding mechanism is `!` before an internal link. Use that format so the note remains meaningful with the custom viewer disabled. [Accepted formats][w1], [embedding files][w2].

Write bare `![[file/name.mp4]]` initially. The official embed documentation specifically explains size hints for images; it does not establish that an image-style `|400` hint works identically for videos. Verify the installed Obsidian behavior before promising such syntax. Keep sizing in presentation if necessary, and never write custom HTML, plugin-only media tokens, or an accompanying poster link into each task merely to make the viewer work. Native Reading/Live Preview playback should remain available without the `Z` extension.

| Proposed recognition | Behavior |
| --- | --- |
| `.mp4`, `.webm`, `.mov`, `.mkv`, `.ogv`, case-insensitive | Import as `video`, preserve original bytes, emit a native embed, attempt playback through Obsidian’s Chromium runtime. |
| H.264 video in MP4, with AAC audio when audio exists | Preferred interoperability target for screencasts; validate on the actual supported desktops. |
| HEVC/H.265, AV1, unusual audio tracks, or unusual MOV/MKV content | Import remains useful, but playback is runtime-dependent. Provide an explicit external-player escape hatch. |
| `.m4v`, `.avi`, `.wmv`, and other unlisted containers | Keep current generic-file behavior initially. Expand only after actual Obsidian compatibility tests. |
| Remote video URLs, YouTube links, raw clipboard movie bytes | Outside this first release; do not infer downloads or uploads from `%c`. Existing text/URL handling remains authoritative. |

Container recognition and successful decoding are different promises. A `.mp4` name alone does not identify its codec. MDN describes MP4/H.264/AAC as broadly supported, but browser documentation does not prove the exact codec bundle in Bryan’s installed Obsidian. Extension-based classification is enough to preserve the existing import model; mandatory `ffprobe` or transcoding in every capture is unnecessary. [Media processing concepts][w3], [video codec guide][w4]. Audio-only WebM is an edge case because Obsidian lists WebM under both audio and video: the viewer should tolerate zero video dimensions and still expose playback controls rather than crash or spin forever.

**The viewing experience should feel like the image viewer, with controls appropriate to time-based media.** Reuse its dark scrim, restrained typography, filename, origin line, small shortcut chips, and transient copy/import feedback. Center one video, preserve aspect ratio, and reserve real vertical space for header and controls. Keep controls clear of the picture and avoid cropping code or UI at the edges of a screencast. Portrait video and small windows need explicit layout tests.

A schematic of the intended layout, not a pixel specification:

```text
20261116_155943.mp4                                 Close
~/tmp/screencasts/20261116_155943.mp4

             ┌─────────────────────────────┐
             │                             │
             │        recording frame      │
             │                             │
             └─────────────────────────────┘
             native play / timeline / volume / fullscreen

Space Play   ←/→ Seek   f Fullscreen   y Copy source   r Restore
```

Use an actual `<video controls playsinline preload="metadata">`, with no `autoplay` or `loop`. These are browser media facilities, not a reason to implement a custom decoding stack. `preload` is a hint, and metadata loading does not guarantee an immediately available first-frame poster. Start with a calm placeholder, use a decoded frame when available, and do not require a generated poster to open the video. [HTML video element][w5].

The best first release styles the surrounding shell and uses native transport controls. This retains a working timeline, volume, and pointer interaction without recreating all their accessibility behavior. A bespoke scrubber, animated filmstrip, waveform, and speed wheel would add substantial state and testing for little capture value. Native controls may vary across Obsidian runtimes; visual review on the target Mac is part of acceptance.

| Input in video viewer | Recommended behavior |
| --- | --- |
| `Z`, `q`/`Q`, `Ctrl+[` | Close, stop playback, restore editor focus/selection/scroll. |
| `Esc` | Leave native fullscreen first; otherwise close the viewer. |
| Space | Play/pause. No automatic sound when opening. |
| Left/Right, optionally `h`/`l` | Seek −/+5 seconds; Shift seeks −/+30 seconds. Clamp to available duration. |
| `m` | Toggle mute. |
| `f` | Request/exit fullscreen where the runtime supports it. Keep native fullscreen control as a fallback. |
| `y` | Copy the recorded source display path; use the existing vault-path fallback only when no origin exists. |
| `r` | Restore just the selected embed/link to the original path if the origin is valid, in one undoable edit. Keep the vault copy. |
| Backdrop click | Close only on the actual backdrop, never on video, controls, title, origin, or footer. |

Keep image keyboard behavior unchanged. Do not copy its wheel zoom, drag-to-pan, `0`/`1`, and `h/j/k/l` transforms blindly onto a playing `<video>`: that can move or intercept the native controls. Fit plus fullscreen is a sufficient initial viewing contract. Paused-frame 1:1 zoom is a valuable later addition for small code in recordings, but it needs a deliberately separate transform layer so controls remain usable. This is a deliberate reduction from image-viewer feature parity.

Keyboard handlers must respect focused native controls and interactive elements so Space and arrows do not execute twice. Preserve composition/modifier guards, suppress toggle repeats, and avoid allowing the opening `Z` event to close the modal immediately. Keep a visible focusable Close button, a named dialog, logical Tab order, readable contrast, and reduced-motion behavior. Do not assume native controls alone make the entire modal accessible.

**Failure handling is part of the design.** A missing vault file should say which file is missing; a failed decode should say “This video couldn’t play here,” not confidently diagnose an unsupported codec when corruption or an incomplete recording is also possible. Offer “Open in default app” and “Copy vault path” on failure. The external-app action must use the resolved vault file and a structured local-file API; do not hand a shell an interpolated path and do not automatically launch another app.

Handle the promise returned by `video.play()` and represent actual playing/paused/error state. Ignore late async results after close. On close or plugin unload, mark the session closed, pause, remove the source, reset the media element with `load()`, and detach listeners; remove `<source>` children too if used. Any generated object URLs must be revoked, though the normal implementation should use Obsidian resource URLs directly rather than reading video bytes into a Blob. [Play promise][w6], [media reset][w7]. The existing resolver already uses `vault.getResourcePath` for vault files; preserve that route. [Resolver][p1].

Playback and origin lookup should proceed independently. Show “Looking up source…” while provenance resolves, then reuse the image viewer’s present/missing/changed/elsewhere states. A provenance failure must not prevent playback. A failed lookup must not be mislabeled “no origin.” Revalidate editor identity and selected span before `r`; for large files, rechecking source eligibility at the explicit restore gesture is preferable to trusting arbitrarily old state. Never delete the vault copy, including when an import succeeded but the editor changed before the rewrite. [Origin UI and restore][p4], [path import race guard][p3], [origin contract][c6].

**Reliability work should precede a broad video rollout.** Extend the shared planner used by `%c` and `bob attachments import`, not two parallel implementations. Introduce `AttachmentKind::Video`, keep videos in `file/`, and generate their embeds in `attachment_reference`. Preserve image output, ordering, collision suffixes, multi-target reuse, history order, and existing note-less `%c` filing rules. Counted clipboard history applies its ten-path ceiling per entry, so a per-entry limit alone is not a sufficient total work bound. [Capture contract][c8].

Replace in-memory attachment payloads with source descriptors and bounded streaming operations; small generated snippets can remain in memory. A concrete approach is:

1. Normalize/classify each path and inspect its metadata. Apply per-file and whole-invocation video byte limits before reading contents. Deduplicate repeated source work within the invocation without removing repeated output bullets.
2. Stream SHA-256 during planning, record a source fingerprint, and compare existing candidate destinations with bounded reads. Preserve the exact naming/reuse policy. Verify source metadata before and after the read to catch a recording still being written.
3. Keep dry-run side-effect-free and use the same destination decisions. Dry-run may stream bytes; it must not create temporary video copies or start conversion jobs.
4. For a real commit, stream a source into a uniquely created temporary destination while hashing. Verify the result against the planned hash and source identity, then use the existing no-overwrite installation semantics. A source changed between planning and copying aborts the capture; never install mixed bytes under the old digest.
5. Revalidate reused destinations at commit, preserve existing note conflict checks, and remove only files created by this invocation on ordinary rollback. Preserve the existing distinction: capture origin-journal append failure is a warning after successful note commit, whereas standalone import rolls back created files if journal append fails.
6. Convert origin hashing to streaming too. Open the player before that lookup finishes. Source/hash caches, if later introduced, need source identity, size, modification metadata, and journal invalidation; cached preview data never authorizes an unchecked commit.

This changes storage internals, not capture grammar. Preserve the current transaction contract; do not claim it becomes universally crash-atomic across notes, media, and journals. Investigate interruption/timeout behavior with fault injection. The current in-memory planner effectively snapshots bytes; replacing it with paths without hash verification would weaken correctness. [Current persistence][c4], [current provenance semantics][c6].

Streaming fixes memory amplification but still performs I/O. Do not call it a complete solution to repeated preview work. Benchmark a typical recording and the upper size bound with the existing debounce/cancellation behavior before shipping. Proposed targets, not measurements: keep UI typing responsive throughout; aim for an accepted typical-video preview within 500 ms after debounce and a maximum-size local preview within two seconds. Measure on the Mac, including a cold file cache. If this misses badly, reduce the initial bound or separately design a reusable preview cache in Bob; do not silently substitute speculative filenames for the current exact dry-run result or move destination planning into Swift.

**Set an explicit initial size policy because this vault is Git-backed.** GitHub warns above 50 MiB and blocks regular Git files above 100 MiB. That makes unrestricted screencast importing a concrete sync risk. [GitHub file limits][w8]. I recommend a provisional 95 MiB maximum per new video and a 256 MiB aggregate budget for distinct video payloads across one capture/import invocation, including clipboard history. These are product defaults proposed here, not existing limits. The per-file margin is intentional; the aggregate bound limits total I/O and lock duration. Apply the same rules through `%c` and path import.

Show the file size before submission when available. A refusal should explain the actual size and limit and leave the whole capture unwritten; it must not silently turn an oversized video into a link to a temporary source. Suggest choosing a shorter/smaller export. Do not add repeated confirmation dialogs or a hidden automatic conversion. If Bryan’s ordinary recordings regularly exceed the bound, this should reopen the storage design before implementation: explicit optimized copies or a separately engineered large-attachment store may then be justified.

A per-file limit does not prevent aggregate repository growth: hundreds of small recordings still accumulate in Git history. No automatic cleanup belongs in this first release, since attachments can have several inbound links and history is durable. Verify the actual vault `.gitignore`/`.gitattributes` and cross-host transfer for each promised extension, including uppercase filenames; adjust the vault policy through its established workflow if necessary. I inspected the documented allowlist strategy, not the live vault rules, so I am not asserting that any particular video extension is currently ignored. Do not activate Obsidian Sync as a second transport or introduce Git LFS implicitly.

**Mac Capture should remain a thin client.** The inspected Swift model accepts a new `video` string, but its summary currently counts non-images as generic files. Add a proper video count, a compact film/play tile, destination, and size if Bob provides it. Optional `size_bytes` can be added for video attachments without changing required image fields; older clients must continue decoding and newer clients must tolerate its absence. Avoid showing an invented duration before metadata exists. A poster thumbnail is useful later, but should be cancellable, cached presentation derived from a Bob-reported source, never a second clipboard reader or import planner. An icon with clear filename/size is an acceptable initial fallback. [Mac models][m1], [presentation][m2], [current thumbnail view][m3].

This follows the audited project decisions that Bob Mac Capture delegates grammar, previews, and mutation to Bob, and that capture bullets mirror the resulting task block. Keep one capture invocation per draft. The feature does not require changing `%c` tokenization, adding a directive, or relaxing contexts that currently forbid `%c`.

**There are several tempting alternatives I would decline for this scope.**

| Alternative | Assessment |
| --- | --- |
| Only change `%c` to emit an embed and rely on native playback | Useful first slice, but incomplete: it does not deliver `Z`, original-path gestures, or large-file reliability. |
| Put videos into the image extension set and reuse `ImageZoomModal` unchanged | Wrong renderer and event model. Reuse the resolver/provenance/shell where appropriate; keep video lifecycle and playback controls separate. |
| Always launch QuickTime/VLC from `Z` | Good fallback; poor default because it interrupts the editor workflow and loses the integrated origin/restore experience. |
| Link directly to `~/tmp/screencasts/...` | Fragile after cleanup and across hosts. The durable vault copy is central to the request. |
| Convert every video to MP4 or GIF during capture | Adds latency, dependencies, quality loss, and timeout/origin questions. GIF also discards audio and is a poor substitute for ordinary video transport controls. |
| Require a general gallery/media plugin | Adds another source of key bindings and behavior without solving Bob’s transactional import and origin contracts. No such dependency is needed for one local video. |
| Add transcripts, searchable video notes, timestamp links, galleries, resume history, and automatic posters now | Potentially useful later; these are separate product features and would delay the requested capture/view loop. |

The feature is valuable precisely when a short video explains something text cannot. It is less attractive as a way to file long recordings or replace a useful textual task description. Keep the human-written task title meaningful; the attachment supplies evidence, not the task’s only explanation.

**The deliberate requirements adjustments are therefore explicit:** preserve `file/`; support local files rather than remote video fetching; keep `Z` scoped to the current line; open paused; distinguish recognized containers from guaranteed codecs; enforce provisional byte limits; postpone automatic transcoding, custom timelines, and paused-frame zoom; and require sync and performance checks alongside playback checks. None changes the requested `%c` → child embed → `Z` interaction.

**Implementation should proceed in a few independently verifiable slices.** Start with a small real-runtime spike that renders a native embed, resolves its Obsidian resource URL, and exercises a local MP4 in a modal on the target Mac. Verify seek, audio, fullscreen exit, and closing while loading. This settles the runtime questions that source inspection cannot answer.

Next, implement the Rust video classification/rendering and bounded streaming path with import/capture regression coverage. Add plugin media dispatch while preserving `zoom-image-on-line`, the four existing link forms, current-line ordering, and path-only import. A small shared media context plus separate image/video bodies is preferable to a large universal media framework. Then update Mac presentation, documentation, and vault coverage. Keep old image key behavior and old video links working throughout.

For compatibility, test new Bob with the current Mac decoder, new Mac with old Bob, and plugin behavior with old Bob’s `kind: file` / plain-link video output. The plugin must not claim it received a video embed when the server returned a plain link. Existing `[[file/old.mp4]]` links should still open as videos under `Z` without requiring note migration. The inspected Swift consumer is tolerant, but do not infer that every JSON consumer treats new enum values as additive; audit them and mark an actual contract break according to the project’s release policy. Bob CLI still ships through its daily release train, with no hand-edited version or changelog.

| Validation area | Essential cases |
| --- | --- |
| Import/capture | Exact example; quoted/spaced/Unicode paths; `file://`; uppercase extension; existing identical destination; different-content collision; repeated source across tasks/history; mixed image/video/PDF clipboard; direct child and drawer targets. |
| Transaction safety | Source changes/grows between plan and save; destination appears concurrently; reused destination changes; later batch item fails; note conflict; disk-full copy; origin journal failure with the two existing semantics; process interruption; no overwrite and no deleted pre-existing files. |
| Dry-run/performance | No files, directories, journal events, or conversions; stable predicted destination; bounded peak memory with several videos; repeated previews during editing; obsolete subprocess cancellation; full invocation byte budget. |
| Resolver | Both embeds and plain links in wiki/Markdown syntax; aliases/size hints; mixed image/video ordering; code spans/fences; missing file; path-only import; stale editor and duplicate `Z`; correct source-note-relative resolution. |
| Viewer | Silent and audible MP4; WebM; representative MOV/HEVC and MKV successes or useful failures; corrupt/truncated/zero-byte files; audio-only WebM; portrait/4K/variable-frame-rate media; native control focus; fullscreen; repeat keys; close before metadata/play/origin results; unload; no continuing sound. |
| Provenance | Present/missing/changed/elsewhere/no-origin/lookup-failed states; `y`; `r` range correctness and one-step undo; same-size source modification; origin lookup cannot delay video opening. |
| Compatibility and deployment | Native embed with custom viewer disabled; existing image tests; mixed client versions; actual Git trackability and byte-identical off-host copy; plugin build/docs checks and deployment workflow; compiled Mac targets and exact-SHA macOS CI if Swift changes. |

DOM-mocked tests cannot establish codec support or visual quality. Add a small synthetic, non-sensitive media fixture set for runtime checks and keep large performance fixtures generated outside Git. Record the Obsidian/Electron version, OS, and codec for each playback result. No screenshot or desktop playback verification was performed during this research.

**Evidence boundaries.** The inspected repository snapshots were bob-cli `0510aaf0e997ca97c10919ec21214b362a1b8c12`, bob-plugins `daceef0e0c6dfab253353bcb166bab5add273e7f`, and bob-mac-capture `0f43014477912ab037e30d66cbe4a651ef1296c1`. Code citations below are pinned to those snapshots. External documentation was consulted on 2026-11-16. I did not open or probe the example recording, inspect the live vault’s ignore rules, run a desktop player, benchmark the proposed streaming design, or implement changes. Accordingly, source behavior is established by inspection; codec, appearance, timing, and sync acceptance remain concrete implementation gates, not completed tests.

**Recommended solution.** Implement native video embeds through the existing shared attachment importer, with videos retained under `file/`, explicit size bounds, streamed hashing/copying, and the current provenance and transaction rules. Extend the existing `Z` command into a current-line media dispatcher that preserves image behavior and opens local videos paused in a restrained modal with native controls, the same `y`/`r` loop, reliable teardown, and an explicit external-player fallback. Deliver the complete small-recording workflow first, including Mac presentation and real sync/runtime verification. This meets the request without turning capture into a media-processing system, and leaves a sound foundation for later paused-frame zoom or opt-in optimized copies.

[c1]: https://github.com/bobs-org/bob-cli/blob/0510aaf0e997ca97c10919ec21214b362a1b8c12/src/native/capture_clip/files.rs
[c2]: https://github.com/bobs-org/bob-cli/blob/0510aaf0e997ca97c10919ec21214b362a1b8c12/src/native/capture_clip/model.rs
[c3]: https://github.com/bobs-org/bob-cli/blob/0510aaf0e997ca97c10919ec21214b362a1b8c12/src/native/capture_clip/plan.rs
[c4]: https://github.com/bobs-org/bob-cli/blob/0510aaf0e997ca97c10919ec21214b362a1b8c12/src/native/capture_clip/persist.rs
[c5]: https://github.com/bobs-org/bob-cli/blob/0510aaf0e997ca97c10919ec21214b362a1b8c12/src/native/attachments/origin.rs
[c6]: https://github.com/bobs-org/bob-cli/blob/0510aaf0e997ca97c10919ec21214b362a1b8c12/docs/attachments.md
[c7]: https://github.com/bobs-org/bob-cli/blob/0510aaf0e997ca97c10919ec21214b362a1b8c12/docs/vault-git-sync.md
[c8]: https://github.com/bobs-org/bob-cli/blob/0510aaf0e997ca97c10919ec21214b362a1b8c12/docs/capture.md
[p1]: https://github.com/bobs-org/bob-plugins/blob/daceef0e0c6dfab253353bcb166bab5add273e7f/plugins/bob-navigation-hotkeys/src/679-plugin-image-zoom.js
[p3]: https://github.com/bobs-org/bob-plugins/blob/daceef0e0c6dfab253353bcb166bab5add273e7f/plugins/bob-navigation-hotkeys/src/679a-image-zoom-path.js
[p4]: https://github.com/bobs-org/bob-plugins/blob/daceef0e0c6dfab253353bcb166bab5add273e7f/plugins/bob-navigation-hotkeys/src/207a-image-zoom-origin.js
[p5]: https://github.com/bobs-org/bob-plugins/blob/daceef0e0c6dfab253353bcb166bab5add273e7f/plugins/bob-navigation-hotkeys/src/490-plugin-lifecycle.js
[p6]: https://github.com/bobs-org/bob-plugins/blob/daceef0e0c6dfab253353bcb166bab5add273e7f/plugins/bob-ledger-tools/src/173-plugin-attachments-api.js
[p7]: https://github.com/bobs-org/bob-plugins/blob/daceef0e0c6dfab253353bcb166bab5add273e7f/plugins/bob-ledger-tools/src/236-plugin-stats-data.js
[m1]: https://github.com/bobs-org/bob-mac-capture/blob/0f43014477912ab037e30d66cbe4a651ef1296c1/Sources/CaptureCore/CaptureModels.swift
[m2]: https://github.com/bobs-org/bob-mac-capture/blob/0f43014477912ab037e30d66cbe4a651ef1296c1/Sources/CaptureCore/CaptureClipPresentation.swift
[m3]: https://github.com/bobs-org/bob-mac-capture/blob/0f43014477912ab037e30d66cbe4a651ef1296c1/Sources/BobMacCapture/ClipCardView.swift
[m4]: https://github.com/bobs-org/bob-mac-capture/blob/0f43014477912ab037e30d66cbe4a651ef1296c1/Sources/BobMacCapture/CapturePanelModel.swift
[m5]: https://github.com/bobs-org/bob-mac-capture/blob/0f43014477912ab037e30d66cbe4a651ef1296c1/Sources/CaptureCore/BobProcessClient.swift
[w1]: https://obsidian.md/help/file-formats
[w2]: https://obsidian.md/help/embeds
[w3]: https://developer.mozilla.org/en-US/docs/Web/API/WebCodecs_API/Video_processing_concepts
[w4]: https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Video_codecs
[w5]: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/video
[w6]: https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/play
[w7]: https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/load
[w8]: https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github
