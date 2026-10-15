# `bob ref rename` and a Refs-panel rename key

Researcher: cld · 2026-10-15 · Scope: bob-cli (`bob ref`), Bob Mac Capture (Refs
panel), Bob vault (`~/bob`), bob-plugins (read-only check).

## TL;DR

- **Build the CLI, but treat it as a safety tool.** Renaming a reference by hand, or
  with Obsidian's rename, is actively harmful today. I reproduced this in a scratch
  vault:
  - An Obsidian-style rename of the note alone makes the next scan **recreate the old
    note and insert a second reading task** (`^ref-…-2`).
  - A bare `mv` orphans the reading task (`open_ref_without_task`).
  - Renaming an annotated reference **re-keys every `^h-` highlight** and tombstones
    the old ones.

  A command that owns these invariants is worth having, even though it will be used
  rarely.
- **Usage will be rare. Fix the namer too.** Of 426 modern ref notes, 1 has an
  opaque stem (this gist) and 3 have generic ones (`README`, `AGENTS`, `demo`). The gist
  got a hex filename because `stem_from_url` takes the last URL path segment and has no
  guard against opaque IDs. The multi-URL collection namer already has that guard. Fixing
  the single-URL namer stops new cases from appearing; the rename command repairs the
  existing ones.
- **What a correct rename means (verified).** Move every same-stem file, rewrite the
  inbound links, update `source_pdf`, and **keep** the frontmatter `id` and the
  `^ref-<slug>` block ID. Then `bob ref sync --dry-run` plans **no work at all**
  (`note_action: none`, reading task unchanged, no diagnostics), and `bob ref find
  <old-id>` still resolves.
- **Requirement adjustments** (justified below):
  1. "Rename" means **the file stem**, not the title, and the reference stays in the
     same type directory.
  2. `id` and `^ref-…` stay as they are.
  3. v1 **refuses references that have highlights**. All four current candidates have
     zero. Re-keying highlights comes in v2.
  4. The command commits once, under the sync and scan locks.
  5. The panel key is **⌘E**, plus a ⌘K "Rename…" item. A bare letter, Return, or ⌘R
     won't work.
  6. The namer fix ships in the same epic.
- **Recommended order:**
  1. bob-cli: fix the namer, then add `bob ref rename` with dry-run, JSON output,
     verify, and commit.
  2. Bob Mac Capture: a ⌘E rename card that calls `bob ref rename -f json`.
  3. Optionally, later: re-key highlights so annotated references can be renamed.

---

## 1. The motivating case, precisely

| Thing | Value |
| --- | --- |
| Ref note | `ref/blogs/442a6bf555914893e9891c11519de94f.md` |
| PDF | `lib/blogs/442a6bf555914893e9891c11519de94f.pdf` (210 KB). There is no sidecar, audio, or `.assets`. |
| Frontmatter | `id: 442a6bf…` (equal to the stem), `title: karpathy/llm-wiki.md`, `author: "262588213843476"` (junk), `source_url: https://gist.github.com/karpathy/442a6bf…`, `source_pdf: lib/blogs/442a6bf….pdf` |
| PDF marker | `status, parent: sase, title, id, source_url, author, published, captured` (from `bob ref marker`). **The marker holds no path.** |
| Reading task | `sase.md:29` `- [ ] #task #ref [[ref/blogs/442a6bf…\|karpathy/llm-wiki.md]] [created::2026-10-15] ^ref-442a6bf…` |
| Embed in note | `![[sase#^ref-442a6bf…]]`, which contains no stem |
| Annotations / follow-ups | 0 / 0 (`bob ref show … -f json`) |
| Inbound links | Only `sase.md:29` |
| Origin | One vault-sync commit from the MacBook, `de14c11a` 2026-10-15 13:54. It was most likely `bob ref create <URL>`, because `gist.github.com` falls under the default `github.com` routing exclusion, so a bare-URL capture would have stayed a task (inference). |

**Why it got a hex name.** Both URL routes use the same stem order:

- `bob ref create`: `-N`, then `stem_from_url`, then `snake_case(title)`, then
  `<host>_<date>` (`src/native/highlights_ref/clip.rs:351-363`).
- Background ingest: the same order (`ingest.rs:1040-1049`).

`stem_from_url` walks the path segments from the end (`clip_url.rs:250-260`).
`stem_from_segment` (`clip_url.rs:262-294`) skips only empty segments, segments of two
characters or fewer, all-digit segments, dates, and a small word list (`index`, `post`,
`blog`, …). A 32-character hex gist ID passes all of those checks and becomes the stem.
The multi-URL namer already guards against this case. `collection_name.rs:17` says:
*"A false refusal only asks for an explicit name; a false positive becomes a durable
filename and link."* It trims `is_hex_id_word` words at `:541-558`, but the single-URL
path never got the same rule. The title and author are also poor, which is a separate
gist-metadata quality issue.

## 2. Everything a reference's name is tied to

### 2.1 Things that depend on the stem (must change on rename)

| Item | Where | Notes |
| --- | --- | --- |
| Ref note path `ref/<t>/<stem>.md` | `io.rs:4-47` (`ref_note_path`) | **The scan pairs a PDF with its note purely by path.** It does not use `source_pdf`, `id`, or the sha. |
| Library PDF `lib/<t>/<stem>.pdf` | git-tracked (`lib/` is 613/613 tracked) | Highlights.app displays this filename, which is why a bad stem is visible. |
| Highlights sidecar `lib/<t>/<stem>.md` or `.textbundle/` | `sidecar.rs:88-115` | Written by Highlights.app and found by the PDF's name. |
| Audio `lib/<t>/<stem>.{mp3,m4a,ogg,opus}` | `audio.rs:20-41` | Bound by sitting beside the PDF. The note carries `audio: "[[lib/…mp3]]"` plus a one-time `![[…mp3]]` player embed, which sync stops touching after creation (`audio.rs:111-159`). |
| Image assets `ref/<t>/<stem>.assets/h-<id>.<ext>` | `sidecar.rs:586-605` | Only `gastown_readme` has any. |
| Frontmatter `source_pdf`, `highlights_sidecar`, `audio` | `model.rs:893-1000` | `source_pdf` self-heals on sync, but a stale value plans a note write (see §3, B and C). |
| Inbound wikilinks | vault-wide | `[[ref/<t>/<stem>\|Title]]` (reading tasks, live and in `done/`), `[[ref/…#^ref]]` / `![[…]]` (Pomodoro Task Links, old schema), `[[ref/…#^h-…\|🔖]]` (follow-ups), bare `[[<stem>]]` (about 41 such links to 30 ref notes), and `[[lib/<t>/<stem>.pdf]]` (the v1 `^ref` line inside old-schema notes). |
| **Highlight block IDs `^h-…`** | `sidecar_render.rs:115-147` | `annotation_block_id` hashes **`source_pdf_value(pdf)`**, the PDF *path*, together with kind, page, ordinal, and text. Renaming the PDF therefore changes every highlight ID. |
| Follow-up `[h:: <digest>]` | `annotation_tasks.rs:227-242` | Hashes the **note path** and the `^h-` ID. |
| Listen card ▶ Play URI | `create.rs:2159-2203` | `obsidian://…file=lib%2F<t>%2F<stem>.mp3` is baked into the PDFs of Markdown-rendered references only. A rename can't fix it short of re-rendering. |

### 2.2 Things that do NOT depend on the stem (keep them)

| Handle | Why keeping it is right |
| --- | --- |
| Frontmatter `id` (exposed as `marker_id`) | Docs call it "the stable handle used by reference clients" (`ref_library/row.rs:15-16`, `docs/ref.md:225,253,503`). `ref find`/`show` match a stem **or** an `id` (`ref_library/resolve.rs:204-240`), so `bob ref find 442a6bf…` keeps working after a rename (verified). It is already allowed to differ from the stem: of 426 notes, 343 match, 77 have no id, and 6 differ. |
| Reading-task block `^ref-<slug>` | It is derived from the stem only when the task is created (`ref_tasks/line.rs:148-198`). After that it is read from the line, never recomputed. Pomodoro Task Links, Depends-On links, and `[dependsOn:: sase__ref-…]` all point at it. Rewriting it would be pure risk, and 4 existing `^ref-*` IDs already don't match their stems. |
| URL / arXiv / DOI identity keys | Come from `source_url`/`url`, not the path. |
| The PDF marker | Holds no path (`marker.rs:~250-265` rejects pipeline keys), so a rename needs no PDF write. |

## 3. Experiments (scratch vault, real binary, real files)

I copied the real note, PDF, and `sase.md`, and later one annotated reference, into a
throwaway git repo under `/tmp`. In each case I renamed the reference a different way,
committed, and ran the current `bob ref sync --dry-run` / `scan` against it with
`BOB_DIR` pointed at the scratch repo.

| # | What was done | Result |
| --- | --- | --- |
| A | **Full rename:** `git mv` of the note and PDF, rewrite of the `sase.md:29` link, update of `source_pdf`, commit | `sync_reason: marker and frontmatter match the stored hash` · `reading_task: unchanged sase.md ^ref-442a6bf…` · `note_action: none` · `pdf_marker_action: none`. `ref show`: new path, same `marker_id`, task located, `diagnostics: []`. `ref find 442a6bf…` → the renamed note. Git records both files as renames (`R100` for the PDF). **This shows that the design needs no sync-engine changes.** |
| B | **Bare `mv`**, committed, with no link rewrite | `reading_task: none (missing)` and `open_ref_without_task: open v2 note has no reading task; restore it from git or set status: abandoned`. The stale `source_pdf` plans a note update. |
| C | **Uncommitted** full rename | A writing scan succeeds *only if it plans no write to the renamed note*. With a stale `source_pdf` it refuses: `refusing to modify dirty vault files: ?? ref/blogs/karpathy_llm_wiki.md`. **The command must therefore update frontmatter itself and commit.** |
| D | **Obsidian-style rename** (note only, link updated, PDF left in place), committed | The next scan reports `would create note` for the old stem (`sync_reason: initial sync`) **and** `reading_task: insert sase.md ^ref-442a6bf…-2`. The result is a duplicate note plus a duplicate reading task. |
| E | **Full rename of an annotated reference** (`introducing_omnigent…`, 8 highlights, with sidecar) | The dry run reports `note_action: update`. The real sync then mints 8 new `^h-` IDs and tombstones the 8 old ones under `### Removed highlights`, leaving 16 IDs in the note. Inbound `#^h-` links would point at tombstones. |

Two consequences follow:

- **D rules out "just use Obsidian's rename".** That rename is bob-navigation-hotkeys'
  `rename-current-file` on ⌃⇧6 (`bob-plugins/plugins/bob-navigation-hotkeys/src/670-plugin-project-files.js:474-510`).
  The vault does have `alwaysUpdateLinks: true`, but that is not enough.
- **E is why v1 refuses annotated references** (§5, R3) until highlight re-keying exists.

The vault already shows the link-rot risk from out-of-band renames: commit `d8305f99`
moved `ref/paper/` → `ref/papers/`, and `job_update_cv.md:20` still links
`[[ref/paper/BryanBugyi_CV_extended_v2|…]]`.

## 4. Critique: is this a good idea?

**For the CLI: yes.** The vault's reference identity is spread across paths, hashes, and
links, and only bob understands all of them. §3 shows that every simpler route damages
the vault: duplicate notes, duplicate reading tasks, orphaned tasks, scans that refuse
to run, or tombstoned highlights. A rename verb under `bob ref` also fits the CLI rules
(`cli_rules.md`): `bob ref` is the reference-library noun, and its Library section
already holds writers (`migrate-tasks`, `migrate-zorg`).

**Caveats I would push back on:**

1. **Frequency is low, so the namer fix gives more leverage than the panel.**
   - The vault has 1,030 ref notes: 426 modern and 604 legacy (`ref/ai`, `ref/zorg`).
   - Exactly 1 modern note has a truly opaque stem (this gist) and 3 have generic ones
     (`ref/chat/README.md`, `AGENTS.md`, `demo.md`). All four have 0 annotations and 0
     follow-ups (checked with `bob ref show`).
   - Without the namer fix, every future gist (or similar ID-in-URL page) recreates the
     problem. The fix is about 20 lines and a few tests.
2. **The panel key is the expensive half.**
   - The Refs panel has no text input except search.
   - Its key monitor swallows every key while a card is open (`RefsPanel.swift:334-341`).
   - Selection, open history, and the inspector cache are all keyed by note path
     (`RefsModel.swift:255`, `RefsStores.swift:133-146`, `RefsInspectorLoader.swift:631`).
   - Swift changes must be compiled on the Mac (repo `AGENTS.md`).

   It is still worth doing: Highlights shows the filename, so the panel is where Bryan
   notices a bad name. But it should come after the CLI, and it is not urgent for four
   notes.
3. **"Rename" is ambiguous.** The panel rows show **titles**; Highlights, Finder, and
   Obsidian links show the **stem**. This gist has a bad stem *and* a poor title
   (`karpathy/llm-wiki.md`). Retitling is a different operation: it is a synced marker
   field, so it needs a PDF marker write plus hash/base updates. A path already exists
   for it: edit the frontmatter `title`, then run
   `bob ref sync <pdf> -p frontmatter -w`. v1 should not merge the two operations.
4. **Thin-client compliance holds.** The app would only collect a string and run
   `bob ref rename`, exactly like ⌘S runs `bob ref scan -w`. That matches
   `decisions:mac-capture-is-a-thin-client`: bob validates the name, detects
   collisions, and does every write.

**Alternatives I considered and rejected:**

| Alternative | Why not |
| --- | --- |
| Obsidian `rename-current-file` (⌃⇧6) | Experiment D: duplicate note plus duplicate reading task, and it doesn't move the `lib/` siblings or `.assets`. |
| Manual `git mv` recipe | Works (experiment A), but it is easy to get wrong (B, C, E). Fine as a one-off today (Appendix A); not a workflow. |
| Re-create with `bob ref create -N` and delete the old reference | Loses the reading-task history, `created`, Pomodoro links, and annotations. Two notes share an identity until the old one is deleted. |
| Change the title only, never the stem | Doesn't fix what Bryan sees in Highlights or Finder, or in links. |
| Make `^h-` IDs path-independent with a "seed" frontmatter field (e.g. `highlights_id_source`) | It works, but it puts a permanent indirection into the hot sync path for a rarely used feature, and it needs schema, doctor, and marker-exclusion updates. Re-keying inside the rename command (§6.6) keeps the complexity in one place. |
| Have bob suggest a name (for example from the title) to prefill the panel | Nice, but it needs a JSON field and naming heuristics for a handful of uses. Prefilling the current stem is enough. |
| Allow changing the type directory (`blogs` → `papers`) | A real need (see the CV link rot), and the same machinery would support it. Leave it out of v1 and keep `-t/--type` as a natural later option. |

## 5. Requirement adjustments (clearly called out)

- **R1 — Rename the stem, within the same type directory, for modern PDF-backed
  references only.**
  - Legacy `ref/ai` and `ref/zorg` notes have no PDF pairing, so Obsidian's rename is
    safe for them. The command should refuse them with that hint.
  - Intake-only (`xlib/`) PDFs aren't in the library yet; refuse those too.
  - The panel only lists rows with a safe `source_pdf` (`RefsModel.swift:350-415`), so
    the two sides line up.
- **R2 — Keep `id` and `^ref-<slug>` unchanged** (§2.2, verified in experiment A). After
  the rename, `id` no longer equals the stem; that is already normal.
- **R3 — v1 refuses references with highlight state.** Refuse when any of these is
  present: a `^h-` block (live or tombstoned) in the managed region, a
  `ref/<t>/<stem>.assets/` directory, or an inbound `#^h-` link. Use error code
  `has_highlights`, with a hint that re-keying is not supported yet.
  - This covers 100% of today's candidates.
  - Misnames are usually noticed at triage, before any annotating. Opening the PDF in
    Highlights is the moment the filename shows.
  - Reopen it (§6.6) the first time an annotated reference needs a rename.
- **R4 — Refuse unless the reference is in sync.** Before renaming, a dry-run sync of
  the current PDF must plan nothing. Otherwise fail with `not_in_sync` and the hint
  "run `bob ref scan` first". This is what makes the post-rename "no work planned"
  check a meaningful verification.
- **R5 — Make it one revertible commit, run under `bob_sync.lock` and the scan writer
  lock, with pre- and post-sync.** `-o/--offline` skips the syncs. Experiment C shows
  why it must commit. `sase.md` is a hot file, and the pre-sync narrows the window in
  which a vault-sync conflict could revert the link rewrite.
- **R6 — Validate names strictly.**
  - Use the same rule as `create -N` (`clip_url::validate_name`:
    `[A-Za-z0-9][A-Za-z0-9_.-]*`, dropping a trailing `.pdf`).
  - The new stem must not be occupied for this type (`stamp.rs:230`
    `default_stem_occupants`, plus `.assets` and audio).
  - **No `.md` file anywhere in the vault may already have that basename.** This is the
    migrate-zorg collision rule (`docs/ref.md:369-375`), and it protects bare `[[stem]]`
    links and Obsidian's shortest-path links.
  - Refuse a rename to the same name, or one that changes only letter case (risky on
    case-insensitive APFS).
- **R7 — Panel key: ⌘E, plus a ⌘K "Rename…" item, plus a README row.** Bare letters
  type into search, Return opens, ⌘R refreshes, and ⌃⇧⌘R is the global dev hotkey.
- **R8 — Ship the namer fix (§8) in the same epic,** so the cause is fixed along with
  the symptom.

## 6. Design: `bob ref rename` (bob-cli)

### 6.1 Surface

```text
bob ref rename [OPTIONS] <REF> <NAME>

Rename a reference's files and update every link to it

Arguments:
  <REF>   Reference to rename: note path, stem, id, URL, arXiv ID, DOI, or exact title
  <NAME>  New file stem; a trailing .pdf is ignored ([A-Za-z0-9][A-Za-z0-9_.-]*)

Options:
  -b, --bob-dir <PATH>   Bob vault root; defaults to BOB_DIR or ~/bob
  -d, --dry-run          Print the plan without moving, rewriting, committing, or syncing
  -f, --format <FORMAT>  Output format [default: human] [possible values: human, json]
  -l, --lib-dir <PATH>   Highlights PDF library; defaults to BOB_HIGHLIGHTS_LIB_DIR or lib
  -o, --offline          Skip the vault sync before and after the commit
  -r, --ref-dir <PATH>   Reference note directory; defaults to BOB_HIGHLIGHTS_REF_DIR or ref
  -x, --xlib-dir <PATH>  Highlights intake directory (checked for name collisions)
  -h, --help             Print help

Keeps the frontmatter id and the reading task's ^ref block ID, so Task Links,
dependencies, and `bob ref find <old id>` keep working.

Examples:
  bob ref rename 442a6bf555914893e9891c11519de94f karpathy_llm_wiki -d
  bob ref rename ref/chat/README.md research_prototype_cdx
```

- **Writes by default, with `-d` to preview.** This matches the targeted verbs (`create`,
  `sync`, `scan`), not the bulk `migrate-*` verbs that are dry-run by default with
  `-w`. A rename is one item, explicitly requested, and the panel needs a one-shot call.
- **Placement in help.** Put it in the `Library` section, alphabetically between
  `migrate-zorg` and `show`. Update the group's about line to "Find, list, read, and
  rename…".
- **Docs.** Add a row to the "Choose a command" table in `docs/ref.md` and a
  `## bob ref rename` section modelled on the migrate sections.

### 6.2 Resolution and refusals (all checked before anything is written)

| Code (exit 1) | When |
| --- | --- |
| `unknown_reference` / `ambiguous_reference` | Resolve the same way as `ref show`, reusing the same candidates/hints. |
| `legacy_reference` / `intake_reference` | R1. |
| `invalid_name`, `same_name` | R6. Include the snake_case of the input in the hint ("try `llm_wiki`"). |
| `name_taken` | R6: occupant in the type directory, or the basename exists elsewhere in the vault. Name the file. |
| `has_highlights` | R3. |
| `not_in_sync` | R4. |
| `dirty_paths` | Any path the plan will touch differs from `HEAD`. This is the migrate-tasks rule. |
| `lock_busy` / `scan_busy` / `sync_failed` | Lock or sync failure. A failed pre-sync aborts with an `--offline` hint. |
| `verify_failed` | §6.4 step 7. Everything is restored first. |

Usage errors exit 2. In JSON mode every failure is the standard envelope
`{"ok":false,"schema_version":1,"command":"ref rename","error":{code,message,hint}}`
on stdout (`docs/ref.md:525-537`).

### 6.3 The plan

1. **Moves.** For each item that exists, move old → new: the note, the PDF, the sidecar
   (`.md` or `.textbundle/`), the audio (all four extensions), and `.assets/` (v2 only).
   Use no-clobber renames.
2. **Rewrite inbound links** across every vault `.md` file, with the
   `migrate_tasks/rewrite.rs` exclusions (`is_excluded` at `:10`: `lib/`, `xlib/`,
   hidden, `_generated`, `_templates`, `_conflicts`, conflict copies), but **including
   `done/` and the daily notes.** Forms to rewrite:
   - `[[ref/<t>/<old>]]`, plus the variants with `|alias`, `#^…`, and `!` embeds;
   - bare `[[<old>…]]` *only when it resolves to this note*, using the locator's
     unique-stem rule (`walk.rs:114-130`);
   - `[[lib/<t>/<old>.pdf]]`, `[[lib/<t>/<old>.mp3]]`, `![[…mp3]]`;
   - Markdown links `](ref/<t>/<old>.md)`.

   Keep aliases verbatim. `preview_rewrites` / `apply_rewrites_to_contents`
   (`rewrite.rs:95, 301`) are the closest existing machinery to generalize.
3. **Update the note's own frontmatter:** `source_pdf`, `highlights_sidecar`, and
   `audio`. Leave `id`, `title`, the marker hash/base, and the `^ref` embed untouched.
   The PDF bytes are not modified.

### 6.4 Write flow (mirrors `migrate-tasks --write`, `migrate_tasks/write.rs:104-450`)

1. **Take `bob_sync.lock`** with the 60 s budget (`ob::acquire_lock_waiting`,
   `ob.rs:241`), **then the scan writer lock** (`acquire_scan_writer_lock`,
   `scan_json.rs:125`). Scan never takes `bob_sync.lock` and vault-sync never runs a
   scan, so this order cannot deadlock. Both waits are bounded anyway.
2. Require a git worktree (`ob::detect_git_worktree`, `ob.rs:278`).
3. Pre-sync unless `-o` (`vault_sync::run_cycle_with_existing_lock_report`).
4. **Re-plan from disk under the locks** and run every refusal in §6.2 again.
5. Snapshot the before-images of every file to be rewritten (`write.rs:43`).
6. Rename the files, rewrite the links and frontmatter.
7. **Verify** two things, and on any failure restore every move and before-image,
   then exit 1 with `verify_failed`:
   - **Idempotence:** run the sync planner for the new PDF in dry-run mode. It must
     report the equivalents of `note_action: none`, `pdf_marker_action: none`, and
     `reading_task: unchanged`. Experiment A shows this holds for a correct rename, and
     experiment E shows it catches highlight re-keying.
   - **Index:** rebuild the ref index. The new path must yield a row with the same
     `marker_id`, a located `task` whose `(path, block_id)` is unchanged, and no new
     diagnostics (`open_ref_without_task`, `orphan_ref_task`, `duplicate_identity`). No
     row may remain at the old path.
8. **Commit exactly the touched paths** (old and new) with `ob::commit_paths`
   (`ob.rs:299`; `git add` stages a removal for a deleted tracked path). Subject:
   `bob ref rename: <old-stem> → <new-stem>`. Git shows the PDF as a rename.
9. Post-sync unless `-o`.

### 6.5 Output

- **Human output:** a short plan/result summary — the moves (`note`, `pdf`, `sidecar`,
  …), "updated N links in M files", the kept handles (`id 442a6bf…`,
  `^ref-442a6bf…`), and `committed <sha> <subject>`.
- **JSON output.** Additive under `REF_SCHEMA_VERSION` 1:

```json
{"ok":true,"schema_version":1,"command":"ref rename","mode":"write",
 "from":{"path":"ref/blogs/442a6bf….md","stem":"442a6bf…"},
 "to":{"path":"ref/blogs/karpathy_llm_wiki.md","stem":"karpathy_llm_wiki"},
 "moves":[{"kind":"note","from":"ref/blogs/442a6bf….md","to":"ref/blogs/karpathy_llm_wiki.md"},
          {"kind":"pdf","from":"lib/blogs/442a6bf….pdf","to":"lib/blogs/karpathy_llm_wiki.pdf"}],
 "links":{"rewritten":1,"files":["sase.md"]},
 "kept":{"marker_id":"442a6bf…","task_block_id":"ref-442a6bf…"},
 "ref":{ "...": "full index row of the renamed note, as in ref show" },
 "commit":{"sha":"…","subject":"bob ref rename: 442a6bf… → karpathy_llm_wiki","paths":["…"]},
 "sync":{"pre":"ok","post":"ok"}}
```

With `-d`, the output has `mode:"dry_run"` and `commit:null`.

### 6.6 v2: renaming annotated references (re-key, not seed)

All of this stays inside the rename command, with no change to the sync path:

1. Parse the sidecar of the reference being renamed. For each live annotation, compute
   `annotation_block_id(old_pdf, a)` → `annotation_block_id(new_pdf, a)`. For images,
   use `image_annotation_block_id` with the image sha. This gives a map
   `{^h-old → ^h-new}`.
2. Apply the map:
   - rewrite the block anchors in the managed region;
   - rename the asset files `h-old.ext` → `h-new.ext`, moving `.assets/` and updating
     the embeds;
   - rewrite `#^h-old` fragments in links that target this note;
   - recompute `[h:: …]` digests for (old note path, old ID) → (new note path, new ID)
     (`annotation_tasks.rs:227-242`).
3. Leave tombstoned IDs alone. They can't be recomputed, and they stay tombstones.
4. The §6.4 idempotence check proves the re-key: experiment E would then show
   `note_action: none`.

Estimate: about 200–300 lines plus fixtures. Do it when the first annotated rename is
actually wanted.

### 6.7 Tests (bob-cli)

- Fixture vaults covering:
  - experiment A (expect a no-op sync and a located task);
  - bare-stem inbound links, including the ambiguous case;
  - `done/` and daily-note Task Links;
  - audio and sidecar moves;
  - every refusal code;
  - `--dry-run` writing nothing;
  - rollback when verification fails (inject a failure);
  - JSON envelope snapshots;
  - commit subject and paths;
  - `ref find <old id>` still resolving.
- For v2: experiment E becomes a no-op.

## 7. Design: Refs panel rename (Bob Mac Capture)

### 7.1 Key and discoverability

- **⌘E** maps to `.beginRename` in `RefsKeyRouter.command` (`RefsKeyRouter.swift:65-184`).
  ⌘E is unused in both routers. The capture editor binds only ⌃E, which still works
  inside the rename field because native text editing passes through.
  - **Rejected keys:**
    - bare `r` or ⌥R: they type into search, and tests assert pass-through
      (`RefsKeyRouterTests.swift:181-184, 213-217`);
    - Return: opens the PDF;
    - ⌘R: refresh;
    - F2: needs `fn` on MacBook keyboards.
  - **Acceptable alternative:** ⌘⇧R, if Bryan prefers the R mnemonic. A slip between it
    and ⌘R is harmless because rename only opens a prompt.
- **⌘K menu:** add `Rename…  ⌘E` (`RefsActionsMenu.swift:45-96`), next to the other
  per-row actions.
- **Footer:** add `⌘E Rename` only to the widest hint variant (`RefsFooter.swift:51-58`).
  Rename is rare, so it doesn't need to crowd the narrow variants.
- **README:** add a row to the Bob Refs key table (`README.md:1369-1386`) and a short
  "Renaming a reference" paragraph that names `bob ref rename`.

### 7.2 Prompt UI

- **Copy the Capture prompt pattern rather than inventing one.** The pieces are the
  Name Pomodoro card (`CapturePanelView.swift:1293-1384`), the `PomodoroNameField`
  focus-request sequence (`PomodoroNameField.swift:8-127`), and the
  `isolatedPromptCommand` key routing (`CaptureKeyCommandRouter.swift:425-452`):
  - Return submits; Esc and ⌃[ cancel.
  - Tab, arrows, and ⌃N/⌃P are consumed.
  - Every other key edits the field natively.
- **Card layout.** Show the card where the Copy card renders (the inspector column, or
  in place of the list on narrow panels; `RefsPanelView.swift:146-170`). Its contents:
  - the title (read-only);
  - a **File name** field prefilled with the current stem and fully selected;
  - a fixed `.pdf` suffix label;
  - a caption: "Also renames the note and updates links. Keeps the reading task."
- **Key handling.** `RefsPanel.processKeyEvent` needs a rename branch ahead of the
  router, like the Copy-card branch at `:334-341`, except that it passes text-editing
  keys through. `RefsKeyContext` gains `isRenaming`. Rename sits first in the Esc order
  (`RefsPanelModel.swift:499-519`).
  - Focus: `repairFilterFocusIfNeeded` only reclaims focus when the first responder is
    nil or the content view (`RefsPanel.swift:396-411`), so a second field is safe.
  - IME composition checks must look at the rename field, not just search.
- **Errors appear inline under the field,** using bob's `error.message` and `hint`. The
  field stays editable for another attempt.

### 7.3 Process call and result handling

- **The call.** Add `RefsFetching.rename(notePath:name:)`, which runs
  `ref rename -f json -- <note path> <name>`.
  - Pass the note path, `RefItem.id`, so resolution is exact.
  - Decode with `decodeReport` (`BobProcessClient.swift:600-659`), which reads stdout
    whatever the exit code, so `{"ok":false}` envelopes come through.
  - Use a dedicated **non-cancelling write lane** (as scan does) with a **120 s**
    timeout, because the pre- and post-sync run inside the call.
  - Put the report type and decoding in `RefsCore` so they are tested on Linux.
- **On success:**
  - Force a fresh listing that **selects `to.path`**. This mirrors
    `buildFreshListingForScan`, which selects the created path
    (`RefsPanelModel.swift:1158-1185`). Without it, the watcher refresh dims the old row
    as "No longer in your library" (`RefsPanelModel.swift:634-646`) and the new row
    appears only after a re-rank.
  - Rewrite open-history entries from → to. `RefsStores` only has load, append, and
    reset (`:215-252`), so add a small `rename(from:to:)`; otherwise frecency is lost.
  - Drop the inspector cache entry for the old ID.
  - Footer status: "Renamed → karpathy_llm_wiki.pdf · 1 link updated". Post a VoiceOver
    announcement.
  - If the panel was hidden meanwhile, post a notification, as scan does.
- **Older bob.** An unknown subcommand exits 2. Map that to "This bob can't rename
  references yet — update bob", the same way scan's exit-2 branch is handled
  (`RefsLibrary.swift:610-633`).
- **Tests:**
  - add a `ref rename` branch to `Tests/Fixtures/fake-bob` (any other `ref` subcommand
    currently exits 64, `:4936-4938`);
  - update the exact-match tests `RefsKeyRouterTests`, `RefsInspectorTests` (⌘K
    sections), and `RefsFooterTests`;
  - add `RefsFetchingTests` for argv and lane, and `RefsPanelModelTests` for: selects
    the new path, inline error, older bob, and hidden-panel completion.
  - The macOS targets build only on the Mac or in CI (`AGENTS.md`).

### 7.4 Risk specific to the panel: the PDF is likely open in Highlights

Return opens the selected PDF in Highlights, and Highlights stays frontmost while the
panel is up (`README.md:1435-1442`). So the PDF being renamed is often an open document.

- bob's `rename(2)` is not an `NSFileCoordinator`-coordinated move, so Highlights'
  `NSDocument`/`NSFilePresenter` is never told about it. I found no authoritative
  statement of what `NSDocument` does after an *uncoordinated* move.
- The plausible bad outcome is that a later autosave, or a Highlights sidecar
  auto-export, recreates `lib/<t>/<old>.pdf` or `<old>.md`. The next scan would then
  create a duplicate note (experiment D shape), and `duplicate_identity` would flag it.
- **Make this an explicit acceptance test on the Mac** before shipping the panel phase:
  1. Open the PDF in Highlights.
  2. Rename it from the panel.
  3. Add a highlight in Highlights.
  4. Check whether anything appears at the old path.
- If it does, the cheapest mitigation is for the panel to reopen the renamed PDF in
  Highlights after success, or to show a hint to close it first. This is an open
  question, not a known bug.

## 8. Root-cause fix: opaque URL segments (bob-cli, small)

**The rule.** In `stem_from_url` / `stem_from_segment` (`clip_url.rs:250-294`):

1. Strip trailing opaque-ID words from the chosen segment. Reuse
   `collection_name::is_hex_id_word`, moved into `clip_url.rs`, and also cover UUIDs.
2. If the segment is *entirely* opaque, return `None` so that `snake_case(title)` is
   used. Do not continue walking to earlier segments, because those are usually
   usernames or orgs (`karpathy`).

**Expected results:**

- The gist becomes `karpathy_llm_wiki_md`. Optionally, also strip a trailing
  file-extension word (`md`, `txt`) from title-derived stems.
- Medium-style `my-post-title-1a2b3c4d5e6f` becomes `my_post_title`.

**Scope.** Both `clip.rs` (create) and `ingest.rs` (background) pick this up. Existing
stems never change, and identity (dedupe) is URL-based, so nothing else moves.

**Separate follow-up.** Gist metadata extraction produced `author: "262588213843476"` and
the title `karpathy/llm-wiki.md`. A host-specific cleanup could use the URL owner as the
author and the gist filename, minus its extension, as the title. This is an independent
bug and not part of this feature.

## 9. Other risks and open questions

- **Vault-sync conflicts.** If another machine edits `sase.md` concurrently and the
  conflict policy keeps the remote copy, the link rewrite is lost. The reading task then
  points at a path that no longer exists, and `bob ref doctor` reports
  `open_ref_without_task`. Pre-sync makes this unlikely; `doctor` makes it visible. A
  rerun of `bob ref rename` can't fix it, because the old name is gone. A
  `bob ref doctor` hint, or a later `bob ref relink`, could.
- **Obsidian has the note open during the rename.** Obsidian sees a delete plus a create,
  not a rename. A pending editor save could recreate the old file. This is low risk
  because Obsidian closes views of deleted files, but it belongs in the manual test.
- **`refs.base` sorts by `file.ctime`.** A rename pulled through git gives the note a new
  ctime on other machines, so it reorders in that Base view. Cosmetic.
- **The Listen card ▶ Play URI** baked into Markdown-rendered PDFs goes stale. Either
  refuse to rename such PDFs or warn; most references aren't Markdown-rendered.
- **Untracked siblings** (`.m4a`/`.ogg`/`.opus` audio, `.textbundle/*.markdown`) move
  locally only. Other machines never had them, so nothing is lost.
- **Decision record.** Once accepted, add a `decisions:` record along the lines of "A
  reference rename moves the stem; `id` and `^ref` stay", via `/sase_memory_write`. The
  invariant is exactly the kind of thing someone later "fixes" by renaming the block ID
  too.

## 10. Recommended solution

1. **bob-cli, phase 1: namer fix (§8).** Tests for the gist, Medium-style, and UUID
   segments, with title fallback. Small and independent; ship it first.
2. **bob-cli, phase 2: `bob ref rename` v1 (§6).**
   - Stem rename within the type directory, for modern PDF-backed references.
   - Moves the note, PDF, sidecar, and audio, and rewrites inbound links vault-wide,
     including `done/`, daily notes, and bare stems.
   - Updates `source_pdf`, `highlights_sidecar`, and `audio`. Keeps `id` and
     `^ref-<slug>`.
   - Refuses annotated, out-of-sync, dirty, legacy, or colliding references with typed
     error codes.
   - Runs under `bob_sync.lock` and then `scan.lock`, with pre-sync, re-plan, write, and
     a **verify step that requires a no-op dry-run sync plus a clean index row**.
     Rollback on failure. One commit `bob ref rename: <old> → <new>`, then post-sync.
   - Human output plus a JSON envelope (`schema_version` 1, additive). Help in the
     Library section; docs in `docs/ref.md`.
3. **Bob Mac Capture, phase 3 (§7).**
   - ⌘E and the ⌘K "Rename…" item open an inline rename card prefilled with the current
     stem. Return runs `bob ref rename -f json -- <note path> <name>` in a non-cancelling
     120 s lane.
   - On success, select the new path and migrate open history. On failure, show bob's
     message and hint inline. An older bob gets an "update bob" message.
   - Include the Highlights-open acceptance test (§7.4).
4. **Phase 4, when first needed:** highlight re-keying (§6.6), so annotated references
   can be renamed, proven by the same idempotence check.
5. **For the gist today:** either wait for phase 2 (`bob ref rename 442a6bf…
   karpathy_llm_wiki`), or use the verified manual recipe in Appendix A.

---

## Appendix A — one-off manual fix for the gist (verified in a scratch vault)

Run this on a Linux host (GNU `sed`). On macOS use `sed -i ''`. Close the PDF in
Highlights first.

```bash
O=442a6bf555914893e9891c11519de94f; N=karpathy_llm_wiki
bob vault-sync                         # start from a fresh tree
cd ~/bob
git mv lib/blogs/$O.pdf lib/blogs/$N.pdf
git mv ref/blogs/$O.md  ref/blogs/$N.md
sed -i "s#\[\[ref/blogs/$O|#[[ref/blogs/$N|#" sase.md
sed -i "s#^source_pdf: lib/blogs/$O.pdf#source_pdf: lib/blogs/$N.pdf#" ref/blogs/$N.md
bob ref sync -d lib/blogs/$N.pdf       # expect: reading_task: unchanged … note_action: none
git commit -m "ref: rename $O -> $N" -- lib/blogs/$O.pdf lib/blogs/$N.pdf ref/blogs/$O.md ref/blogs/$N.md sase.md
bob vault-sync
```

Do not run `git commit -a`, because vault-sync owns other dirty files. Keep `id:` and
`^ref-442a6bf…` as they are. Changing the title from `karpathy/llm-wiki.md` is a
separate step: edit `title:` in the note, then run
`bob ref sync lib/blogs/$N.pdf -p frontmatter -w`.

## Appendix B — evidence index

- **bob-cli code:**
  - naming: `highlights_ref/clip.rs:351-363`, `ingest.rs:1040-1049`,
    `clip_url.rs:230-294`, `collection_name.rs:17,541-558`;
  - pairing and paths: `io.rs:4-47,77-92`;
  - highlight IDs and digests: `sidecar_render.rs:115-147`, `annotation_tasks.rs:227-242`;
  - dirty guard: `guard.rs:206-225`;
  - scan lock: `scan_json.rs:119-165`;
  - write-flow helpers: `ob.rs:241,278,299`, `ref_library/migrate_tasks/write.rs:104-450`,
    `migrate_tasks/rewrite.rs:10,95,301`;
  - collision check: `stamp.rs:83,230`;
  - resolution: `ref_library/resolve.rs:204-240`.
- **Docs:** `docs/ref.md` (identity :114-141, show :228-303, migrate-zorg collisions
  :369-375, JSON/errors :480-537), `docs/highlights-ref-sync.md` (`--write-pdf` and
  `--prefer` :600-629).
- **Bob Mac Capture:** `Sources/BobMacCapture/Refs/RefsKeyRouter.swift:65-184`,
  `RefsPanel.swift:299-347,396-411`,
  `RefsPanelModel.swift:499-519,634-646,1158-1185`,
  `Sources/RefsCore/RefsModel.swift:255,350-415`, `RefsFetching.swift:26-62`,
  `RefsStores.swift:133-252`, `CaptureCore/BobProcessClient.swift:25-28,600-659`,
  `CaptureKeyCommandRouter.swift:425-452`, `README.md:1196-1202,1369-1386`, `AGENTS.md`.
- **bob-plugins:**
  - `bob-navigation-hotkeys/src/670-plugin-project-files.js:474-510`
    (`rename-current-file`, ⌃⇧6);
  - `block-id-prompt` (`rename-selected-block-id`), a precedent for vault-wide
    block-link rewrites;
  - no plugin depends on ref stems or ids.
- **Vault facts:**
  - `.obsidian/app.json` sets `alwaysUpdateLinks: true`;
  - 1,030 ref notes: 426 modern, 604 legacy;
  - 76 ref notes have highlights;
  - `id` equals the stem in 343 of 426;
  - `lib/` is fully git-tracked;
  - the stale link at `job_update_cv.md:20` comes from commit `d8305f99`.
- **Scratch-vault experiments A–E (§3):** run with the workspace's debug `bob` build
  against copies of the real files.
- **External:**
  - [Apple: NSFileCoordinator item(at:didMoveTo:)](https://developer.apple.com/documentation/foundation/nsfilecoordinator/item(at:didmoveto:).md)
    — only coordinated moves notify file presenters.
  - [NSFilePresenter.h (10.8 SDK)](https://jenkins.heirloomcomputing.com/downloads/MacOSX10.8.sdk/System/Library/Frameworks/Foundation.framework/Headers/NSFilePresenter.h)
    — NSDocument is a file presenter.
  - [Cocoa-dev: path vs inode on moved files](https://lists.apple.com/archives/Cocoa-dev/2006/Jul/msg01768.html).
  - [MPU forum: Highlights sidecar Markdown export beside the PDF](https://talk.macpowerusers.com/t/batch-process-annotations-from-pdfs-out-to-obsidian/24470).
  - [Highlights on the App Store](https://apps.apple.com/app/id1498912833) — export
    formats.
