# Video embeds in task captures, viewed with `Z`

Research into adding video-file support to task captures (`%c`) and the Obsidian
`Z` viewer, modeled on the existing image pipeline. Request: if
`~/tmp/screencasts/20261116_155943.mp4` is on the clipboard, `%c` in a task
capture should embed that video as a sub-bullet of the new task, and `Z` should
play it.

Verdict up front: **yes, build it, as an embed (`![[…]]`) with a new `vid/`
vault directory, a new `video` attachment kind, a 100 MB size cap, and a
transport-style `Z` viewer.** Details and justification below.

## 1. How images work today (the model to copy)

Three halves, in two repos. Everything video needs already exists once; the work
is a second media type threaded through the same seams.

### 1.1 Capture: clipboard path → copied file → embed sub-bullet

`docs/capture.md` ("Clipboard", ~line 1330) is the contract. The Rust side is
`src/native/capture_clip/`:

- `clipboard.rs` reads the live clipboard (5 s deadline, 16 MiB stdout cap,
  `CLIPBOARD_TIMEOUT` / `CLIPBOARD_STDOUT_CAP`). `%c<N>` history comes from
  Alfred/Clipy stores or `capture.clipboard_history_command`.
- `plan.rs:plan_entry` classifies every clipboard line with
  `files.rs:classify_path_candidate` (handles quotes, `file://`, `~/`,
  percent-decoding). If **all** non-empty lines are existing files, they become
  attachments (max `MAX_ATTACHMENT_COUNT = 10`); otherwise text/list/snippet
  rules apply.
- `files.rs:plan_attachments` reads each file, SHA-256-hashes it,
  `attachment_kind()` sorts it by extension into `Image` vs `File`,
  `sanitize_file_name` cleans the name, and `choose_attachment_destination`
  reuses byte-identical files or appends an 8-char hash suffix on conflict.
  Images land in `img/`, everything else in `file/`.
- `files.rs:attachment_reference` renders the sub-bullet:
  `![[img/x.png|400]]` for images, `[[file/x.pdf]]` for files.
  `IMAGE_EMBED_WIDTH = 400`; `IMAGE_EXTENSIONS` is 12 entries:
  `avif, bmp, gif, heic, ico, jpeg, jpg, png, svg, tif, tiff, webp`.
- `persist.rs` writes new files atomically; on note-write failure
  `cleanup_created` removes them, so a capture never leaves orphaned copies.
- `--dry-run` plans identically but creates nothing; this is also what Bob Mac
  Capture renders as its live preview (thin-client contract,
  `decisions:mac-capture-is-a-thin-client`).

Consequence for the request: today an `.mp4` clipboard already "works" — as a
`file/` **link** (`[[file/20261116_155943.mp4]]`), not an embed. Nobody has to
invent plumbing; the missing piece is purely "video is a third kind that
embeds."

`bob attachments import` (`src/native/attachments/cli.rs`) reuses the exact same
`classify_path_candidate → plan_attachments` path with fresh reservations and
never edits notes. Its JSON reports each attachment as
`{source, display, saved, kind, reused, embed, sha256}` with `kind` serialized
`"image"` / `"file"` (`model.rs:AttachmentKind`, `cli.rs` ~line 353). Any new
kind appears in this JSON and in `docs/reference/json-outputs.md`.

### 1.2 Origin journal: path → embed → path

`docs/attachments.md` is the contract every implementation cites. One
`attachment.import` event per copied file goes to
`.bob/attachments/<host>.jsonl` (`via: "capture"` from `%c`,
`via: "zoom"` from the viewer), recording `{source, display, saved, sha256}`.
`bob attachments origin` resolves vault path → original path with
`present / missing / changed / elsewhere / external` states, so `y` (copy
original) and `r` (restore link to original) keep round-tripping. The journal
is extension-agnostic — video needs no journal change, only correct `saved`
paths flowing through it.

### 1.3 The `Z` viewer (bob-plugins, not bob-cli)

`Z` is a Vim mapping (`obsidian_vimrc.md`) over the "Zoom image on cursor
line" command; the plugin assigns no default. Contract:
`plugins/bob-navigation-hotkeys/docs/image-zoom.md`. Implementation:

- Resolver — `plugins/bob-navigation-hotkeys/src/679-plugin-image-zoom.js`:
  finds wiki/markdown refs on the cursor line (skipping code spans/fences),
  picks containing → next → previous, resolves via `metadataCache`.
  `IMAGE_ZOOM_EXTENSIONS` is a JS `Set` of **8**: `png, jpg, jpeg, gif, webp,
  svg, bmp, avif`.
- Path import — `679a-image-zoom-path.js:findImagePathBullet`: a bullet whose
  whole content is one `~/`, `/`, or `file://` path with an image extension is
  imported via `bob attachments import` (ledger-tools API,
  `plugins/bob-ledger-tools/src/173-plugin-attachments-api.js`), the bullet is
  rewritten to the returned `embed` string in one undoable edit, and the viewer
  opens with an "Imported" pill. Non-image extensions throw `Not an image:
  <path>` — this is the exact error an `.mp4` path bullet produces today.
  `importImagePathOnLine` additionally refuses unless
  `attachment.kind === "image"`.
- Viewer — `207-image-zoom-modal.js:ImageZoomModal`: an `<img>` modal with
  zoom/pan, `1` for 1:1, `0` for fit, `y` copy-origin, `r` restore-source,
  `Esc`/`q`/`Z` close. Origin line, pill toasts, focus restore — all
  media-agnostic and reusable as-is.

### 1.4 A discrepancy to fix along the way

The Rust list (12 extensions) and the JS list (8) already disagree: `heic`,
`ico`, `tif`, `tiff` capture-import fine but `Z` refuses to open them. Any
video change must update **both** lists, and should add a comment in each
pointing at the other. I would fix the existing four-extension gap in the same
pass (one-line, well-tested) rather than let a third list drift further.

## 2. What Obsidian does with video (corroborated)

Per the official Obsidian help page "Accepted file formats" (via web search):
Obsidian recognizes video files **`mkv`, `mov`, `mp4`, `ogv`, `webm`**, with
playback depending on device codecs (Electron/Chromium: H.264, VP9, HEVC and
AV1 generally play; iPhone HDR/Dolby Vision plays its HDR base layer). The
embed syntax is `![[video.mp4]]`, which renders an inline HTML5 `<video>`
player with native controls — the exact analogue of `![[image.png]]`. Two
consequences:

- **No width suffix.** `![[img/x.png|400]]` sizing is image (and PDF) syntax;
  there is no documented `![[video.mp4|400]]` equivalent. Emit the bare embed
  and let the player be responsive (constrain with viewer/plugin CSS if a
  task-bullet player overflows, not with a suffix the renderer may ignore or
  misparse). The implementer should still verify `|width` behavior on a sandbox
  vault once, since undocumented support would be the more beautiful option —
  but the design must not depend on it.
- **Extension set.** I recommend
  `mp4, mov, webm, ogv, mkv, m4v`: the five official formats plus `m4v`
  (Apple's screencast-adjacent container, same codecs as mp4). Deliberately
  **exclude `avi`**: Chromium support is unreliable and files are huge; `.avi`
  clipboards keep today's `file/`-link behavior. `gif` stays an image
  (Obsidian already animates it inline).

## 3. Critique: is this a good idea, and what would I change?

**Yes — with three hazards the requirements as stated don't mention.**

1. **Vault/git bloat is the dominant risk.** Images are kilobytes; screencasts
   are tens to hundreds of megabytes. Every embedded video permanently enters
   `~/bob` git history and re-syncs to all Tailnet hosts plus mobile. Worse, a
   single >100 MB file makes GitHub reject the **entire push**, wedging
   `vault-sync` for everything until the file is excavated from history — a
   much nastier failure than a failed capture. This alone justifies a size cap
   (§4.1) and a docs warning. Git-LFS for videos is the eventual answer but is
   explicitly a non-goal for v1.
2. **Whole-file reads don't scale to video.** `plan_attachments` does
   `fs::read` (full bytes into memory) twice over in effect (hash + persist),
   and `plan_history` fans that across entries. A 200 MB screencast will not
   OOM a modern Mac, but it is rude inside a keystroke-adjacent capture path
   with a 5 s clipboard deadline on the *read* side and no bound on the *copy*
   side. Cap + streaming hash/copy (or at minimum a `metadata().len()`
   pre-check before the read).
3. **It is a three-repo change wearing a one-repo costume.** The `%c` grammar
   and Mac Capture preview degrade gracefully (the app renders `lines` text),
   but `bob attachments import -f json` gains a `kind: "video"` value, and
   `173-plugin-attachments-api.js` currently treats any
   `kind !== "image"` as `Not an image`. If Mac Capture switches exhaustively
   on `kind`, an uncoordinated bob-cli release breaks it. Gate the bob-cli side
   on the app's handling (repo instructions: watch the exact-SHA macOS run /
   `scripts/dev/macos-ci-check`), and ship the plugins viewer change against
   the new bob.

### Adjustments to the requirements (all justified above)

- **Embed, don't link.** The request implies it ("embedded in the new task");
  make it explicit: `![[vid/20261116_155943.mp4]]` as a sub-bullet, mirroring
  `![[…|400]]` minus the width suffix.
- **New `vid/` directory, not `img/`.** `img/` already lies a little
  (`docs/reference/vault-format.md` calls `file/` "saved clipboard snippets"
  while it holds all non-image attachments). A dedicated `vid/` keeps future
  image tooling (thumbnails, contact sheets) from tripping over videos, reads
  beautifully in raw Markdown, and costs one `create_dir_all` plus doc lines.
  The journal, dedupe, and hash-suffix machinery is directory-agnostic.
- **Explicit non-goals:** audio files (different player UX, marginal value —
  stay `file/`-linked); video galleries / counted-`NZ` viewer behavior
  (images already scope these out); mobile viewer work; transcoding,
  thumbnails, or poster frames; YouTube/stream URLs (the ref-job queue owns
  URLs; pasting one stays prose-a-link as today).
- **No new config knobs.** Hard constants (extension sets, 400px stays
  image-only, size cap) keep `capture.clipboard_history*` and friends
  untouched. If Bryan later wants `.avi` or a bigger cap, that is a one-line
  follow-up, not a setting to design now.

## 4. Recommended solution

### 4.1 bob-cli (`capture_clip` + `attachments`)

- Add `AttachmentKind::Video` (`model.rs`, serde `"video"`) with
  `VIDEO_EXTENSIONS = ["mp4", "mov", "webm", "ogv", "mkv", "m4v"]`
  (case-insensitive, same helper shape as `attachment_kind` in `files.rs`).
- `plan_attachments`: `Video → "vid/"` directory;
  `attachment_reference` renders `![[<saved>]]` with **no** width suffix.
- Size guard in `plan_attachments` (covers `%c`, `%c<N>`, and `bob
  attachments import` in one place): `metadata().len()` pre-check, refuse over
  100 MB with an actionable message naming the file and the limit
  ("video exceeds the 100 MB vault limit; trim it or link it from outside the
  vault"). 100 MB aligns with GitHub's hard push limit — the failure this
  prevents is a wedged `vault-sync`. Prefer streaming the copy + incremental
  hash while there; at minimum do the pre-check so a 2 GB screen recording
  fails fast instead of after two full reads.
- `attachments/cli.rs` kind mapping gains `Video => "video"`; help text
  ("Copy image and file paths…", "Absolute image or file path…") becomes
  "image, video, and file paths". JSON shape is otherwise unchanged —
  additive, no `!` release marker, but call out the `.mov`/`.mp4` behavior
  change (link → embed) in release notes since existing users may have
  `.mov` muscle memory.
- Nothing else changes: 10-attachment cap, dedupe/hash-suffix, atomic
  write + `cleanup_created` rollback, origin journal (`via: "capture"` /
  `"zoom"` flow untouched), `--dry-run` parity, history fan-out per entry.
- Docs in the same change (`just docs-check` gate): `docs/attachments.md`
  (contract: third kind, `vid/`, no width suffix, size cap),
  `docs/capture.md` clipboard section (video line next to the image line),
  `docs/reference/cli/attachments.md` (regenerate help),
  `docs/reference/json-outputs.md` (`kind` gains `video`),
  `docs/reference/vault-format.md` (`vid/` tree entry).

### 4.2 bob-plugins (viewer + import)

- `679-plugin-image-zoom.js`: add `VIDEO_ZOOM_EXTENSIONS`; candidate rule
  becomes image-or-video (keep the containing → next → previous pick and the
  code-span/fence skips verbatim). Fix the §1.4 gap (add `heic, ico, tif,
  tiff` to the JS image set) in the same pass.
- `679a-image-zoom-path.js:findImagePathBullet`: accept video extensions;
  reword the throw to `Not an image or video: <path>` (update the asserting
  tests). `importImagePathOnLine` accepts `kind === "video"` (pill:
  `Imported to vid/x.mp4 · r to undo`; `Linked existing …` on reuse).
- `207-image-zoom-modal.js`: branch the media element — `<video controls
  playsinline preload="metadata">` for video, existing `<img>` otherwise.
  Transport keys: `Space`/`k` play-pause, `←`/`→` ∓5 s (`Shift` ∓30 s),
  `f` fullscreen; `0`/`1` fit/1:1 become no-ops for video (document, don't
  repurpose). Keep identical: title, origin line + suffixes, `y`
  copy-original, `r` restore-to-display-path (round-trips `Z`/`r` exactly like
  images), `Esc`/`q`/`Z` close, focus restore, Reading-view notice.
  **No autoplay** — reliable across desktop plugin hosts, and respectful in a
  note full of players.
- Reading view needs nothing: Obsidian renders `![[vid/x.mp4]]` as a player
  natively. If embedded players overflow narrow task bullets, add one
  `max-width: 100%` rule to the plugin stylesheet rather than touching note
  content.
- Docs: `docs/image-zoom.md` gains the video half (or a short sibling page
  linked both ways); update the "out of scope" list (galleries, `NZ`,
  mobile) to say videos share it.

### 4.3 Tests and rollout

- Rust: `capture_clip/tests.rs` — `.mp4` single path → `![[vid/…]]` line;
  uppercase `.MP4` + `file://` + quoted variants; mixed image+video batch
  (one `img/`, one `vid/`); video over cap refuses naming the limit;
  `%c3`-style history with one video entry; `attachments import` JSON shows
  `"kind":"video"`. Existing image/file assertions must pass untouched.
- Plugin: mirror the existing `test-navigation-image-zoom-*.cjs` scripts for
  video resolver + path-bullet + modal transport; update `Not an image`
  assertions.
- Manual: `%c` capture of the exact example path, dry-run preview in Mac
  Capture, `Z` open/play/seek/close, `y` copies `~/tmp/screencasts/…`,
  `r` restores, Reading-view player renders, vault-sync pushes cleanly.
- Order: bob-cli (+ docs) → train release → bob-plugins viewer against the
  new bob → Mac Capture CI gate to confirm the new `kind` value renders.
  Agents must not edit `Cargo.toml` version or `CHANGELOG.md`
  (`decisions:bob-cli-releases-ride-a-daily-train`).

### 4.4 Open questions for Bryan (recommendations included)

1. **`vid/` vs `img/` for storage?** Recommend `vid/` (§3) — cleaner and
   forward-compatible; `img/` would ship one day sooner.
2. **100 MB cap?** Recommend yes, aligned with GitHub's push limit; short
   screencasts are 5–30 MB, so day-to-day captures never notice it.
3. **Audio explicitly out of scope?** Recommend yes — `.mp3`/`.m4a` stay
  `file/`-linked until video proves the pattern.
