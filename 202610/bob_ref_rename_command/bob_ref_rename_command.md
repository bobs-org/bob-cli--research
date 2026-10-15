# `bob ref rename` and a Bob Refs rename key: consolidated report

> **Research query:** Should a new `bob ref rename` command, with a matching keymap in the
> bob-mac-capture app's ref panel, be added to rename the currently selected reference (for
> example the misnamed `442a6bf555914893e9891c11519de94f.pdf`), and what is the best way to
> implement it? Critique the plan, say whether a different approach would be better, call out any
> justified adjustments to the requirements, and end with a recommended solution.

![Infographic "Rename the files. Keep the identity.": build bob ref rename as a safety tool that moves the PDF, note, sidecar, and audio together from 442a6bf….pdf to karpathy_llm_wiki.pdf, updating file paths, inbound links, and path metadata while keeping the reference id, reading-task block ID, title, source URL, and PDF bytes unchanged; why a plain rename fails (note-only rename, file-move-only, annotated PDF); fixing the URL namer first (1 opaque hex stem in about 425 PDFs); a narrow, safe v1; one coordinated change under the vault-sync and scan locks with verify, rollback, and one scoped commit; the Mac Refs rename card on ⌘⇧R or ⌘K → Rename…; and the rollout namer fix, CLI v1, Obsidian guard, Mac card, gated on a Highlights-open test](bob_ref_rename_command_infographic.png)

## Bottom line

**Build it, but as a safety tool rather than a convenience key.** Today, renaming a reference by
hand is actively harmful. Every simpler route was reproduced in a scratch vault and damaged the
library (see [why a raw rename is unsafe](#why-a-raw-rename-is-unsafe)). One bob-owned verb that
keeps every invariant is worth having, even though it will be used rarely.

Three changes to the request, explained in [the critique](#critique-of-the-plan) and the
[requirement adjustments](#requirement-adjustments):

1. **"Rename" means the file stem.** The stem is the PDF basename, the note basename, and their
   companions. It does not mean the title, and it does not mean the identity: the frontmatter `id`
   and the `^ref-…` reading-task block ID **stay as they are**.
2. **Fix the namer first.** The hex filename comes from a
   [one-function gap in `stem_from_url`](#root-cause-fix-for-opaque-url-segments). Without that
   fix, every future gist recreates the problem.
3. **v1 refuses annotated references.** Renaming the PDF currently re-keys every `^h-` highlight
   ID. The gist has no highlights, and neither does any other current rename candidate.

**Recommended shape:**

- [`bob ref rename <REF> <NAME>`](#recommended-cli-design) in the `bob ref` Library group. It runs
  under `bob_sync.lock` and the scan lock, makes one scoped commit, and accepts `-d/--dry-run`,
  `-f json`, and `-o/--offline`.
- A Bob Refs **⌘⇧R** rename card, plus a **⌘K → Rename…** item, as a
  [thin client](#recommended-mac-panel-design) of that command.
- **A guard on Obsidian's rename-current-file command for managed ref notes.** None of the four
  reports proposed this, and it closes
  [the most likely way this damage happens today](#reproductions).

For [the motivating file](#the-motivating-reference):
`bob ref rename 442a6bf555914893e9891c11519de94f karpathy_llm_wiki`.

## Recommended solution

One epic, landed in this order (bob-cli first, so the app decodes a real binary):

1. **bob-cli: namer fix** ([root-cause fix](#root-cause-fix-for-opaque-url-segments)). About 20
   lines plus tests. It is independent and stops new hex stems.
2. **bob-cli: `bob ref rename` v1** ([CLI design](#recommended-cli-design)). It does the
   following:
   - renames the stem of a modern, PDF-backed, unannotated reference in place;
   - moves the note, PDF, sidecar, and audio;
   - rewrites inbound links vault-wide, including `done/`, daily notes, and bare stems;
   - updates `source_pdf`, `highlights_sidecar`, and `audio`;
   - **keeps `id` and `^ref-…`, with no PDF write**;
   - refuses with typed codes;
   - runs under `bob_sync.lock` and then the scan lock, with pre-sync, re-plan, write, **verify (a
     no-op dry-run sync plus a clean index row)** with rollback, one scoped commit, and post-sync;
   - offers `-d`, `-f json`, and `-o`. Docs and help go in the Library group.
3. **bob-plugins: guard `rename-current-file`** for managed ref notes. Show a notice pointing at
   `bob ref rename`, then run `bob plugins sync`.
4. **bob-mac-capture: the ⌘⇧R / ⌘K rename card** ([panel design](#recommended-mac-panel-design))
   as a thin client. On success it selects `to.path` and migrates history. It is gated on the
   [Highlights-open acceptance test](#risks-and-open-questions).
5. **Later, when first needed:** annotated renames through the identity-origin field
   ([v2 design](#renaming-annotated-references-in-v2)), then folder refiling, retitling
   (`--title` or `bob ref retitle`), and a bob-provided name suggestion for the card.

### Renaming the gist today

**For the gist today**, wait for step 2 and run:

```bash
bob ref rename 442a6bf555914893e9891c11519de94f karpathy_llm_wiki -d
bob ref rename 442a6bf555914893e9891c11519de94f karpathy_llm_wiki
```

You can also apply the [one-off manual fix below](#verified-one-off-manual-fix) now. Fix the title
separately if you want: set `title: llm-wiki` in the note, then run
`bob ref sync lib/blogs/karpathy_llm_wiki.pdf -p frontmatter -w`.

### Verified one-off manual fix

From cld's [experiment A](#reproductions). Close the PDF in Highlights first. On macOS, use
`sed -i ''`.

```bash
O=442a6bf555914893e9891c11519de94f; N=karpathy_llm_wiki
bob vault-sync && cd ~/bob
git mv lib/blogs/$O.pdf lib/blogs/$N.pdf
git mv ref/blogs/$O.md  ref/blogs/$N.md
sed -i "s#\[\[ref/blogs/$O|#[[ref/blogs/$N|#" sase.md
sed -i "s#^source_pdf: lib/blogs/$O.pdf#source_pdf: lib/blogs/$N.pdf#" ref/blogs/$N.md
bob ref sync -d lib/blogs/$N.pdf   # expect: reading_task unchanged, note_action none
git commit -m "ref: rename $O -> $N" -- lib/blogs/$O.pdf lib/blogs/$N.pdf \
  ref/blogs/$O.md ref/blogs/$N.md sase.md
bob vault-sync
```

- Do not touch `id:` or `^ref-442a6bf…`.
- Do not use `git commit -a`, because vault-sync owns other dirty files.

## Critique of the plan

**Is it a good idea? Yes, for the CLI.** Only bob understands the
[coupled state](#how-identity-is-coupled), and every alternative damages the vault:

- **Finder or `mv`:** Experiment B: an orphaned task and a stale `source_pdf`.
- **Obsidian ⌃⇧6 rename:** Experiment D: a duplicate note plus a duplicate reading task. It also
  does not move `lib/` siblings.
- **Recapture with `bob ref create <URL> -N new`:** Refused by URL dedupe. Forcing it loses the
  reading-task history, `created`, and links.
- **Title-only edit:** Does not fix what Highlights, Finder, and links show.
- **A Mac app `FileManager.moveItem`:** Violates the thin-client decision and cannot rewrite
  `sase.md`.
- **Make IDs path-independent library-wide first, using UUIDs or content hashes:** Churns every
  existing `^h-` on the next scan. Too large a prerequisite for a rare operation.

**What I would do differently from the request as stated:**

1. **Lead with prevention.** One opaque stem in roughly 425 PDFs means the namer fix (about 20
   lines) has more leverage than the panel. Without it, every gist clip reproduces the problem.
2. **Treat the panel as the expensive, second half.** Bob Refs has no text input besides search.
   Its key monitor swallows keys while a card is open (`RefsPanel.swift:324-341`). Selection, open
   history, and inspector caches are keyed by note path (`RefItem.id`). Swift must also be compiled
   on the Mac. The panel is still worth building, because Highlights shows the filename and Bryan
   is in the panel when he notices a bad name.
3. **Close the Obsidian hole.** The vault's own rename hotkey corrupts ref notes
   ([experiment D](#reproductions)). A small bob-plugins guard should refuse, with a notice, when
   the active file is a managed ref note: under `ref/` and with a `source_pdf`. The notice should
   point at `bob ref rename`. The guard is cheap and protects the path Bryan is most likely to
   reach for.
4. **Keep v1 narrow:** same type directory, a PDF-backed library reference, no highlights. Folder
   refiling (`blogs` → `papers`; the vault already has link rot from commit `d8305f99`),
   retitling, bulk renames, and intake (`xlib/`) renames are separate later verbs or options.

## Requirement adjustments

Each adjustment below is called out explicitly.

- **R1 — Scope.**
  - Rename the **stem** of a modern, PDF-backed library reference, within its existing `ref_type`
    directory.
  - Refuse legacy notes (`ref/ai`, `ref/zorg`). They have no PDF pairing, so Obsidian's rename is
    safe for them; say so in the hint.
  - Refuse intake-only `xlib/` PDFs. Bob Refs lists only rows with a safe `source_pdf`, so the CLI
    and panel scopes line up.
- **R2 — Preserve identity.** Keep `id`, `^ref-<slug>`, `source_url`, the dates, and the marker
  hash/base. Make no PDF byte changes.
- **R3 — v1 refuses highlight state** (`has_highlights`). Refuse if any of these exist:
  - a `^h-` block, live or tombstoned, in the managed region;
  - a `.assets/` directory;
  - a `[h:: …]` follow-up citing the note;
  - an inbound `#^h-` link.

  A sidecar alone is **not** a refusal; it moves with the bundle. That is more precise than grk's
  "any sidecar".
- **R4 — Refuse a listen-card URI.** Refuse when the PDF has an `obsidian://` link annotation
  naming its audio file (`listen_card_link`). Moving the audio and rewriting `audio:` and the
  player embed is fine; rewriting the PDF is not.
- **R5 — Preconditions.**
  - The reference must be in sync: a dry-run sync of the current PDF plans nothing. Otherwise
    refuse with `not_in_sync` and the hint "run `bob ref scan`".
  - Every touched path must be clean against `HEAD`; otherwise refuse with `dirty_paths`.
- **R6 — Names.**
  - Use `validate_name`, ignoring a trailing `.pdf`.
  - Collisions are refused (`name_taken`), never auto-suffixed. Check the new stem against every
    bundle member, case-insensitively, plus `xlib/`. Also check it against **any `.md` with that
    basename anywhere in the vault**, which protects bare `[[stem]]` links. This is the
    `migrate-zorg` rule.
  - Renaming to the same name is a successful no-op. Refuse case-only changes in v1, because APFS
    is case-insensitive.
- **R7 — One scoped commit.**
  - Run under `bob_sync.lock` (60 s budget) and then `ref/scan.lock`, with a pre-sync and a
    post-sync.
  - `-o/--offline` commits locally without syncing.
  - Commit subject: `bob ref rename: <old> → <new>`.
- **R8 — Live by default, `-d/--dry-run` to preview.** This matches `create`, `sync`, and
  `reroll`, not the dry-run-by-default `migrate-*` verbs. Everyone agreed.
- **R9 — The panel gesture is a card,** opened by ⌘⇧R or ⌘K → Rename…, not a bare key.
- **R10 — Ship the [namer fix](#root-cause-fix-for-opaque-url-segments) in the same epic,
  first.**
- **R11 — Add the Obsidian rename guard (bob-plugins) in the same epic.**

## The motivating reference

Verified live, read-only.

- **Note:** `ref/blogs/442a6bf555914893e9891c11519de94f.md`
- **PDF:** `lib/blogs/442a6bf555914893e9891c11519de94f.pdf` (git-tracked). There is no sidecar,
  audio, or `.assets/`.
- **Title:** `karpathy/llm-wiki.md` (readable, but carries a stray `.md`)
- **Source URL:** `https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f`
- **Frontmatter / marker `id`:** `442a6bf555914893e9891c11519de94f`
- **Reading task:** `sase.md`:
  `- [ ] #task #ref [[ref/blogs/442a6bf…|karpathy/llm-wiki.md]] [created::2026-10-15] ^ref-442a6bf…`
- **Inbound links:** Only `sase.md` and the note's own `![[sase#^ref-442a6bf…]]` embed. No
  daily-note Task Links (checked with grep).
- **State:** Queued / Ready. 0 annotations, 0 follow-ups.

The hash is the gist's real ID, not junk. **A rename must therefore not replace every occurrence of
the hash.** Doing so would corrupt `source_url`, which is the URL dedupe key (cdx).

**How it happened.** `bob ref create` picks a stem in this order: `-N`, then `stem_from_url`, then
`snake_case(title)`, then `<host>_<date>` (`src/native/highlights_ref/clip.rs:351-363`). Background
ingest uses the same order (`ingest.rs:1040-1041`). `stem_from_segment` skips only empty segments,
segments of two characters or fewer, all-digit segments, dates, and a small word list
(`clip_url.rs:262-294`). A 32-character hex ID passes all of those checks.

**How common it is.** All the reports agree it is rare:

- grk found 1 hex stem among about 425 PDFs.
- cld found, among 426 modern notes, 1 opaque stem and 3 generic ones (`README`, `AGENTS`,
  `demo`). All four have 0 annotations.

## Why a raw rename is unsafe

Consensus across the reports, verified.

### How identity is coupled

The reference's identity is spread across paths, hashes, and links:

- **Scan pairs PDF ↔ note purely by path: `lib/<t>/<s>.pdf` ↔ `ref/<t>/<s>.md`**
  - *Evidence:* `io.rs:4-47` (`ref_note_path`, `pdf_path_metadata`)
  - *Consequence of a naive rename:* Moving one side makes scan create a fresh note, and a second
    reading task, for the other side.
- **Highlight IDs hash the vault-relative PDF path** (plus kind, page, ordinal, and text; images
  use the image sha)
  - *Evidence:* `sidecar_render.rs:115-147`, through `source_pdf_value` →
    `vault_relative_path_value` (`io.rs:77-92`)
  - *Consequence of a naive rename:* Every `^h-` changes. The old ones are tombstoned under
    "Removed highlights", so inbound `#^h-` links point at tombstones.
- **Follow-up `[h:: …]` digests hash the note path** plus the `^h-` ID
  - *Evidence:* `annotation_tasks.rs:227-242`
  - *Consequence of a naive rename:* Processed-task identity churns, and duplicate follow-ups
    become possible.
- **Reading-task link targets the note path**
  - *Evidence:* `sase.md` line
  - *Consequence of a naive rename:* A bare `mv` orphans the task (`open_ref_without_task`).
- **Bundle members are found by sitting beside the PDF:** sidecar `.md`/`.textbundle/`, audio
  (`mp3`/`m4a`/`ogg`/`opus`), and `ref/<t>/<s>.assets/`
  - *Evidence:* `sidecar.rs:75-115,491`, `audio.rs:20-41`
  - *Consequence of a naive rename:* These members are silently left behind.
- **Listen-card ▶ Play URI** baked into Markdown-rendered PDFs
  - *Evidence:* `create.rs:2159-2203`
  - *Consequence of a naive rename:* Moving the audio breaks the button unless the PDF is
    rewritten.

### Reproductions

cld used scratch vaults with the real binary and copies of the real files; cdx ran an independent
repro that confirmed E.

- **A. Full rename: move note and PDF, rewrite the `sase.md` link, update `source_pdf`, keep `id`
  and `^ref`:** `bob ref sync -d` plans **no work at all** (`note_action: none`,
  `reading_task: unchanged`, `pdf_marker_action: none`). `ref find <old id>` still resolves. **This
  design needs no sync-engine changes.**
- **B. Bare `mv`:** The reading task goes missing (`open_ref_without_task`), and the stale
  `source_pdf` plans a write.
- **C. Full rename left uncommitted, with stale frontmatter:** The writing scan refuses:
  `refusing to modify dirty vault files`.
- **D. Obsidian-style rename of the note only:** The next scan recreates the old note **and**
  inserts `^ref-…-2`, a duplicate reading task.
- **E. Full rename of an annotated reference (8 highlights):** 8 new `^h-` IDs are minted and 8 are
  tombstoned (16 in the note).

**D is the most important result in practice.** The vault's Obsidian rename command
(`bob-navigation-hotkeys` `rename-current-file`, `670-plugin-project-files.js:474-510`) calls
`fileManager.renameFile` with no ref-note guard. It is the most likely way this damage happens
today, and `alwaysUpdateLinks: true` does not prevent it.

## Recommended CLI design

This design is for bob-cli.

### Command surface

```text
bob ref rename [OPTIONS] <REF> <NAME>

Rename a reference's files and update every link to it

Arguments:
  <REF>   Reference: note path, stem, id, URL, arXiv ID, DOI, or exact title
  <NAME>  New file stem; a trailing .pdf is ignored ([A-Za-z0-9][A-Za-z0-9_.-]*)

Options:
  -b, --bob-dir <PATH>   Bob vault root; defaults to BOB_DIR or ~/bob
  -d, --dry-run          Print the plan without moving, rewriting, committing, or syncing
  -f, --format <FORMAT>  Output format [default: human] [possible values: human, json]
  -l, --lib-dir <PATH>   Highlights PDF library; defaults to BOB_HIGHLIGHTS_LIB_DIR or lib
  -o, --offline          Commit locally; skip the vault sync before and after
  -r, --ref-dir <PATH>   Reference note directory; defaults to BOB_HIGHLIGHTS_REF_DIR or ref
  -x, --xlib-dir <PATH>  Highlights intake directory (checked for name collisions)
  -h, --help             Print help

Keeps the frontmatter id and the reading task's ^ref block ID, so Today, Task Links,
dependencies, and `bob ref find <old id>` keep working. Links outside the vault
(browser bookmarks, copied URIs) cannot be updated.

Examples:
  bob ref rename 442a6bf555914893e9891c11519de94f karpathy_llm_wiki -d
  bob ref rename ref/chat/README.md research_prototype_cdx
```

**CLI-rule compliance:**

- Place the verb in **Library**, alphabetically between `migrate-zorg` and `show`, and update the
  group's about line to "Find, list, read, and rename…".
- Every long option has a short alias, and options are sorted.
- Add the clap registration, which gives completion for free, and an entry in the `docs/ref.md`
  "Choose a command" table plus a `## bob ref rename` section.

Resolution reuses `ref show`'s exact resolver (`ref_library/resolve.rs`) and returns its
`unknown_reference` / `ambiguous_reference` envelopes. It must never mutate a fuzzy match. The app
always passes the exact note path. Note that a bare `<hash>.pdf` basename does not resolve today
(cdx), so examples use stems or full paths.

### Rename plan

The plan is computed in full before anything is written.

1. **Moves**, using no-clobber renames, for whichever of these exist:
   - the note;
   - the PDF;
   - the sidecar (`.md` and/or `.textbundle/`; inventory both so a stale export is not left
     behind);
   - the audio (all four extensions).

   v1 has no `.assets/`, because [R3](#requirement-adjustments) refuses it.
2. **Inbound link rewrites** across vault `.md` files:
   - Use the `migrate_tasks/rewrite.rs` exclusions (`lib/`, `xlib/`, hidden, `_generated`,
     `_templates`, `_conflicts`, conflict copies), but **include `done/` and daily notes**.
   - Forms to rewrite:
     - `[[ref/<t>/<old>]]`, plus its `|alias`, `#…`, and `!` embed variants;
     - bare `[[<old>]]`, only when it resolves to this note (the unique-stem rule; reuse
       `stem_counts`);
     - `[[lib/<t>/<old>.pdf]]` (the v1 `^ref` tracker line);
     - links to `.mp3` and other audio companions;
     - Markdown links `](ref/<t>/<old>.md)`.
   - Rewrite targets, not strings. Keep aliases verbatim, and skip code spans and fences.
   - `preview_rewrites` / `apply_rewrites_to_contents` (`rewrite.rs:95,301`) and
     `resolve_link_target` are the closest machinery to generalize.
3. **Own frontmatter:** update `source_pdf`, `highlights_sidecar`, and `audio`, and the player
   embed if present. Leave `id`, `title`, the marker hash/base, the `^ref` embed, and all other
   user text untouched; never re-render the note from a template.

### Write flow

The write flow mirrors `migrate-tasks --write` and `task reroll`.

1. Take `bob_sync.lock` (`ob::acquire_lock_waiting`, 60 s), then the scan writer lock
   (`acquire_scan_writer_lock`).
   - Scan never takes `bob_sync.lock`, and the configured pre-scan hook is `bob_xlib_pull`, not
     vault-sync. This order therefore does not invert anything, and both waits are bounded.
   - Do not run the pre-scan hook or a full scan as a side effect.
2. Require a git worktree (`ob::detect_git_worktree`). Then pre-sync
   (`vault_sync::run_cycle_with_existing_lock_report`) unless `-o`. If the pre-sync fails, abort
   with the hint "re-run with --offline".
3. **Re-plan from disk under the locks** and re-run every refusal.
4. Snapshot the before-image of every file to be rewritten. Move the files, then rewrite the links
   and frontmatter.
5. **Verify; on any failure, restore all moves and before-images and exit with `verify_failed`.**
   - **Idempotence:** a dry-run sync of the new PDF plans `note_action: none`,
     `pdf_marker_action: none`, and `reading_task: unchanged`. Experiment A shows this holds for a
     correct rename; experiment E shows it would catch highlight churn.
   - **Index:** the new path yields a row with the same `marker_id`, a located task with the same
     `(path, block_id)`, and no new `open_ref_without_task`, `orphan_ref_task`, or
     `duplicate_identity` diagnostics. No row remains at the old path.
6. Commit **exactly the touched paths**, old and new, with `ob::commit_paths`. Git records the PDF
   as a rename. Then post-sync unless `-o`.
7. **Re-runs:** if the new stem exists and the old one is gone, report `already_renamed` (exit 0,
   `changed: false`). If both exist, refuse.

### Error codes

Errors exit 1 with the standard
`{"ok":false,"schema_version":1,"command":"ref rename","error":{code,message,hint}}` envelope on
stdout; usage errors exit 2. The codes, by category:

- **Resolution:** `unknown_reference`, `ambiguous_reference`
- **Scope:** `legacy_reference`, `intake_reference`
- **Name:** `invalid_name`, `name_taken`
- **Highlight state:** `has_highlights`, `listen_card_link`
- **Preconditions:** `not_in_sync`, `dirty_paths`
- **Locks and sync:** `lock_busy`, `scan_busy`, `sync_failed`
- **Outcome:** `verify_failed`, `already_renamed`

For `invalid_name`, include a snake-cased suggestion in the hint.

### JSON output

The JSON is additive, with `schema_version: 1`.

```json
{"ok":true,"schema_version":1,"command":"ref rename","mode":"write","changed":true,
 "from":{"path":"ref/blogs/442a6bf….md","pdf":"lib/blogs/442a6bf….pdf","stem":"442a6bf…"},
 "to":{"path":"ref/blogs/karpathy_llm_wiki.md","pdf":"lib/blogs/karpathy_llm_wiki.pdf","stem":"karpathy_llm_wiki"},
 "moves":[{"kind":"note","from":"…","to":"…"},{"kind":"pdf","from":"…","to":"…"}],
 "links":{"rewritten":1,"files":["sase.md"]},
 "kept":{"marker_id":"442a6bf…","task":{"path":"sase.md","block_id":"ref-442a6bf…"}},
 "ref":{"…":"full index row at the new path, as in ref show"},
 "commit":{"sha":"…","subject":"bob ref rename: 442a6bf… → karpathy_llm_wiki"},
 "sync":{"pre":"ok","post":"ok"},"warnings":[]}
```

With `-d`, the output has `mode: "dry_run"` and `commit: null`. The explicit `from.path` →
`to.path` mapping is what the app uses to remap selection and history; it must never have to infer
what happened.

### CLI tests

- **Fixture vaults:**
  - the gist shape, where experiment A becomes a test: the sync is a no-op, the task is located,
    and `find <old id>` still resolves;
  - bare-stem links, including the ambiguous case;
  - links in `done/` and daily notes;
  - sidecar and audio moves;
  - dotted stems (avoid `Path::with_extension` clobbering a dotted stem's final component);
  - every refusal code;
  - `-d` writing nothing;
  - injected verification failure followed by rollback;
  - the commit's paths and subject;
  - `already_renamed`;
  - JSON snapshots.
- **Help fixtures** for the Library group.

### Renaming annotated references in v2

When the first annotated rename is actually wanted, adopt **cdx's identity-origin field** rather
than cld's re-key. Add one pipeline-owned frontmatter field, e.g.
`highlights_id_origin: {pdf: <path at first rename>, note: <path>}`, written by the first rename of
a reference that has highlight state.

- `annotation_block_id`, `image_annotation_block_id`, and `annotation_task_source_digest` hash the
  origin values when present, and current paths otherwise. References without the field keep
  today's algorithm byte-for-byte, so nothing migrates.
- Add the field to the marker-sync exclusion list and to note-render preservation, and exclude it
  from generic path rewriting.
- Malformed values are an error, never a silent fallback.

**Why this beats re-keying.** Re-keying must rewrite anchors in the managed region, asset
filenames, inbound `#^h-` fragments vault-wide, and `[h:: …]` digests on task lines, including
archived ones in `done/`. Tombstoned IDs still cannot be recomputed. The origin field changes no
existing bytes beyond one frontmatter line. It survives repeated renames, and the
[write-flow idempotence check](#write-flow) proves it works. Its cost is one optional lookup in the
hash path, plus documentation, so that nobody later "fixes" the mismatch.

grk's content-matching ("reuse IDs when sha and payload match") would put fuzzy matching into every
scan; reject it.

## Root-cause fix for opaque URL segments

A small bob-cli change; ship it first.

Change **`stem_from_url`**, not `stem_from_segment`, because the collection namer imports
`stem_from_segment`:

1. Strip trailing opaque words from the chosen segment. Reuse `collection_name::is_hex_id_word`
   (`collection_name.rs:552-558`: at least 6 characters, at least one digit, lowercase hex), moved
   into a shared spot, and add UUIDs.
2. If the **last non-skipped segment is entirely opaque, return `None`.** Do not keep walking to
   earlier segments, which are usually owners or orgs (`karpathy`). That lets `snake_case(title)`
   win.
3. Optionally strip a trailing file-extension word (`md`, `txt`) from title-derived stems. The gist
   would then become `karpathy_llm_wiki` rather than `karpathy_llm_wiki_md`.

**Tests:**

- `gist.github.com/<user>/<32-hex>` falls back to the title.
- Medium-style `my-post-title-1a2b3c4d5e6f` becomes `my_post_title`.
- A UUID segment falls back to the title.
- An explicit `-N` still wins, and an absent title falls back to `<host>_<date>`.

Existing stems never change, and dedupe stays URL-based. The gist's bad title and author
(`author: "262588213843476"`) are a separate host-metadata bug (cld); file it separately rather
than fold it in.

## Recommended Mac panel design

This design is for bob-mac-capture.

### Keys and discoverability

- In `RefsKeyRouter.command`, `case KeyCode.r`: `.command` → `.refresh` (unchanged);
  `[.command, .shift]` → `.showRenameCard`.
- Do not use these keys:
  - bare or ⌥ letters, which type into search (and tests assert that);
  - Return or Tab, which open Highlights;
  - F2, which needs `fn` on MacBooks.
- Add **Rename…  ⌘⇧R** to the ⌘K menu (`RefsActionsMenu.swift`) next to the per-row actions.
- Add a README key-table row. Leave the footer unchanged: rename is rare, and footer tests pin the
  exact strings.

### Rename card

Shown where the Copy card renders; mutually exclusive with it.

- Contents:
  - the title, read-only;
  - a **File name** field prefilled with the current stem, fully selected;
  - a fixed `.pdf` suffix;
  - the caption "Also renames the note and updates links. Keeps the reading task.";
  - a quiet "close the PDF in Highlights first" hint.
- Key handling:
  - Return submits; Esc and ⌃[ cancel.
  - Every other key edits the field natively. Copy the Name-Pomodoro prompt pattern
    (`PomodoroNameField`, `isolatedPromptCommand`).
  - Add an `isRenaming` branch in `RefsPanel.processKeyEvent` ahead of the router, like the
    Copy-card branch, but passing text-editing keys through. Put rename first on the Esc ladder.
  - IME checks look at the rename field.
- Errors render inline from bob's `message`/`hint`, and the draft stays editable.

### Process call

- Add `RefsFetching.rename(notePath:name:)`, which runs
  `ref rename -f json -- <note path> <name>`.
- Decode with `decodeReport`, which reads stdout whatever the exit code.
- Use a dedicated non-cancelling `refs-rename` lane with a **120 s** timeout, which covers the lock
  wait plus two sync cycles.
- Put the report type in `RefsCore` so it is tested on Linux. Use `decodeIfPresent` for new fields
  and reject other `schema_version`s.
- Disable resubmission while a rename runs. Hiding the panel must not cancel it; post completion as
  a notification, as scan does.
- Defer watcher refreshes during the call, then refresh once.

### On success

- Build a fresh listing that **selects `to.path`**, mirroring `buildFreshListingForScan`.
  Otherwise the watcher refresh dims the old row as "No longer in your library".
- Migrate open history (add `RefsStores.rename(from:to:)`, keeping timestamps) and drop the
  inspector-cache entry for the old ID.
- Show the footer status "Renamed → karpathy_llm_wiki.pdf · 1 link updated" and post a VoiceOver
  announcement.
- Do not re-key app identity to marker IDs. They are nullable and can be shared.

### Older bob

An unknown subcommand exits 2. Show "This bob can't rename references yet — update bob", the same
way scan's exit-2 branch is handled.

### Panel tests

- Add a `ref rename` branch to `Tests/Fixtures/fake-bob`.
- Cover:
  - key-router, ⌘K-section, and unchanged-footer tests;
  - the card's prefill and focus;
  - argv and lane;
  - selection following `to.path`;
  - inline errors;
  - older bob;
  - completion while the panel is hidden.
- The macOS targets build only on a Mac or in CI; `just portable-check` is not enough (repo
  `AGENTS.md`).

## Risks and open questions

- **Highlights has the PDF open** (the main unknown). Return opens the selected PDF in Highlights,
  so the file being renamed is often open.
  - A plain `rename(2)` is not an `NSFileCoordinator` move, so Highlights' `NSDocument` may never
    learn of it. A later autosave or sidecar export could then recreate `<old>.pdf` or `<old>.md`,
    and the next scan would duplicate the note.
  - **Manual acceptance test on the Mac before enabling the key:** open the PDF, rename it from the
    panel, add a highlight, and check the old path.
  - If the old path reappears, the cheapest mitigations are for the card to require closing the
    document, or to reopen the renamed PDF after success.
  - Because `id` is preserved, `bob ref doctor` would flag the resulting `duplicate_identity`.
- **Vault-sync conflicts on `sase.md`.** Under the "remote wins" policy, a concurrent remote edit to
  the same line can drop the link rewrite. Pre-sync narrows the window, and `doctor` reports
  `open_ref_without_task`. A later `bob ref relink` or doctor hint could repair it. This is the same
  exposure as any `sase.md` edit.
- **External links** (browser bookmarks, copied `obsidian://` or `highlights://` URIs) cannot be
  found. State this in `--help`.
- **Cosmetic effects:** `refs.base` sorts by `file.ctime`, so the note reorders on other hosts.
  Untracked audio formats move locally only.
- **Decision record, once accepted.** "A reference rename moves the stem; `id` and `^ref` stay."
  This invariant is exactly the kind of thing someone later "fixes", so record it with
  `/sase_memory_write`. This report proposes the record but does not write it.

## Where the reports disagreed and how I resolved it

- **Change `id` and `^ref-<stem>`?**
  - *Positions:* Keep both: cdx, cld. Change both, with a mandatory PDF marker write and an alias:
    grk. Change the block ID by default, with `--keep-block-id`: gem.
  - *Resolution:* **Keep both.** No diagnostic couples `id` to the stem. I counted 344 notes where
    they match and 6 where they already differ (`row.rs:15` calls `id` "the stable handle used by
    reference clients"). The marker holds no path; pipeline path fields are excluded from marker
    sync (`bob ref marker` output). Keeping `id` therefore means **no PDF write**, which is what you
    want when the PDF may be open in Highlights. Today, Task Links, and Depends-On all join on
    `(task.path, block_id)` (grk's own point), so keeping the block ID leaves them untouched.
    [Experiment A](#reproductions) shows a no-op sync. A preserved marker `id` also lets
    `bob ref doctor` flag `duplicate_identity` if Highlights later recreates the old file. Changing
    the IDs buys only cosmetics, at the cost of the riskiest rewrites.
- **Annotated references in v1?**
  - *Positions:* Support them through an identity-origin field: cdx. Refuse them: cld, grk. Not
    addressed: gem.
  - *Resolution:* **Refuse in v1** (`has_highlights`). This covers 100% of current candidates, and
    misnames are noticed at triage, before any annotating. **For v2, prefer cdx's origin field**
    over cld's in-command re-key or grk's content matching
    ([v2 design](#renaming-annotated-references-in-v2)).
- **Commit and locks?**
  - *Positions:* `bob_sync.lock` + scan lock, pre/post sync, one commit: cld. Durable journal, no
    commit: cdx. Scan lock only, no commit: grk. "Atomic transaction" plus `--force`: gem.
  - *Resolution:* **cld's model**, because it is the established pattern for vault-wide multi-file
    rewrites. `bob task reroll` "publishes the whole change as a single scoped commit between two
    vault-sync cycles under the shared maintenance lock" (`randomize.rs:1-7`), and `migrate-tasks`
    / `migrate-zorg` do the same with `ob::commit_paths` and `--offline`. Without `bob_sync.lock`, a
    periodic vault-sync can commit a half-moved state; another host's scan would then birth a
    duplicate note and task (experiment D shape). The commit also gives a single revert point and
    avoids the dirty-guard refusals from experiment C.
- **Crash safety**
  - *Positions:* Durable operation journal: cdx. In-memory before-images + verify/rollback: cld.
    Report partial state + `already_renamed`: grk.
  - *Resolution:* **Before-images + verify + rollback, plus idempotent re-run detection.** The
    mutating window is sub-second, between the slow pre-sync and the commit. A durable journal is
    deferred until a real failure shows it is needed.
- **Panel key**
  - *Positions:* ⌘⇧R: cdx, grk, gem. ⌘E: cld.
  - *Resolution:* **⌘⇧R.** I verified both keys are unbound in `RefsKeyRouter.swift`. ⌃⇧⌘R is
    only the dev build's *global* hotkey (`HotKeyRegistry.swift:9-13`), so there is no conflict.
    The R mnemonic wins, and a slip to ⌘R (refresh) is harmless. ⌘E is the fallback.
- **Title editing in the same command?**
  - *Positions:* Out of scope: cdx, cld. Optional `-T`/`-t`: grk, gem.
  - *Resolution:* **Out of v1.** The title is a marker-synced field, so retitling *does* need a PDF
    write. A path already exists: edit `title:` in the note, then run
    `bob ref sync <pdf> -p frontmatter -w` (`-p/--prefer` and `-w/--write-pdf` are verified in
    `--help`).
- **Prefill in the card**
  - *Positions:* Current stem: cld. Title-derived slug computed in Swift: grk, gem.
  - *Resolution:* **Current stem, fully selected, in v1**, so typing replaces it. Any title-derived
    suggestion must come from bob, as a JSON field, not from Swift heuristics
    (`decisions:mac-capture-is-a-thin-client`).
- **Namer fix**
  - *Positions:* All four agree it is needed.
  - *Resolution:* **gem's patch is wrong.** Adding the hex check to `stem_from_segment` makes
    `stem_from_url`'s reverse walk (`clip_url.rs:252-259`) fall back to the previous segment, so
    the stem becomes `karpathy` instead of being derived from the title. `stem_from_segment` is
    also shared with the collection namer (`collection_name.rs:10-13`). Use cld's rule in
    `stem_from_url` instead ([root-cause fix](#root-cause-fix-for-opaque-url-segments)).
- **Name rules and flags**
  - *Positions:* `validate_name` `[A-Za-z0-9][A-Za-z0-9_.-]*`: cdx, cld, grk. `[a-zA-Z0-9_-]`,
    `-F` for format, `-f/--force` for a dirty tree: gem.
  - *Resolution:* **Reuse `validate_name`** (`clip_url.rs:230-246`). Keep `-f/--format`, as every
    `bob ref` verb does. Do not add `--force`: a dirty *touched* path is a refusal, while unrelated
    dirt is ignored.

### Claims not verified

Claims I could not verify and that the recommendation does not rely on:

- gem: Highlights writes "(conflict).pdf" autosave copies.
- grk: a 20 s default timeout could be exceeded by a marker rewrite. This is moot, because there is
  no marker rewrite.
- How Highlights' open `NSDocument` behaves after an uncoordinated `rename(2)`. All reports flag
  this as unknown (see [risks and open questions](#risks-and-open-questions)).

## Sources and method

Lead researcher · 2026-10-15 · Merges the independent reports
[`__cdx`](bob_ref_rename_command__cdx.md), [`__cld`](bob_ref_rename_command__cld.md),
[`__grk`](bob_ref_rename_command__grk.md), and [`__gem`](bob_ref_rename_command__gem.md) with my
own verification against bob-cli `9bdb0bd9`, bob-mac-capture `9f58448a`, bob-plugins, and the live
vault (read-only).

### Evidence index

- **bob-cli `9bdb0bd9`:**
  - pairing and paths: `highlights_ref/io.rs:4-47,77-92`;
  - IDs: `sidecar_render.rs:115-147`, `annotation_tasks.rs:213-242`;
  - naming: `clip.rs:351-363`, `ingest.rs:1040-1041`, `clip_url.rs:230-294`,
    `collection_name.rs:10-25,541-558`, `pdf_target.rs:57-76`;
  - locks: `scan_json.rs:125,196`, `sync.rs:47`, `ob.rs:241,278,299`;
  - write pattern: `randomize.rs:1-7,637-657`, `ref_library/migrate_tasks/write.rs:104-400`,
    `migrate_tasks/rewrite.rs:10,95,257,301`;
  - stable-handle docs: `ref_library/row.rs:15-16`.
- **bob-mac-capture `9f58448a`:** `Refs/RefsKeyRouter.swift:65-184`, `HotKeyRegistry.swift:9-25`,
  `Refs/RefsPanel.swift:324-341`, `RefsCore/RefsFetching.swift:16-60`.
- **bob-plugins:** `bob-navigation-hotkeys/src/670-plugin-project-files.js:474-510`,
  `490-plugin-lifecycle.js:238`.
- **Live vault (read-only):**
  - `bob ref show 442a6bf…`;
  - `bob ref marker` (pipeline fields excluded from marker sync; the marker has no path);
  - a grep for inbound links (only `sase.md` and the note itself);
  - the frontmatter `id` vs stem count (344 match, 6 differ);
  - config `pre_scan_hook: bob_xlib_pull`.
- **Memory:** `cli_rules.md`, `decisions:mac-capture-is-a-thin-client`, `obsidian.md`.
- **Experiments:** cld's A–E (scratch vaults with the real binary), and cdx's independent repro of
  E in a synthetic vault.
- **External:**
  - [Obsidian internal links](https://help.obsidian.md/links);
  - [Apple `NSFileCoordinator` `item(at:didMoveTo:)`](https://developer.apple.com/documentation/foundation/nsfilecoordinator/item(at:didmoveto:)):
    only coordinated moves notify file presenters;
  - [Highlights changelog](https://highlightsapp.net/changelog/mac/): path-based `highlights://`
    links.
