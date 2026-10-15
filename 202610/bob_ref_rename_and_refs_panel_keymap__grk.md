# `bob ref rename` and a Bob Refs keymap

Researcher: grk
Date: 2026-10-15
Scope: bob-cli `bob ref` surface, Highlights identity, Bob Mac Capture Refs panel
Motivating file: `lib/blogs/442a6bf555914893e9891c11519de94f.pdf`

## Verdict

Add `bob ref rename`. It is the right tool for this job. Pair it with a Bob Refs rename card (⌘⇧R plus a ⌘K item) that is a thin client of that command.

Do not treat this as a display-title edit, a Finder/Obsidian rename, or a recapture. The thing Bryan wants to change is the **library stem**: the PDF basename, the note basename, the marker `id`, the v2 reading-task block id, and every vault wikilink that points at those.

The plan as stated is directionally right and slightly under-specified. The adjustments below are the difference between a safe one-shot gesture and a command that desyncs Highlights, Today, and the next `bob ref scan`.

## The motivating example, measured

`bob ref find 442a6bf555914893e9891c11519de94f -f json` resolves as `in_library` / `match_kind: stem`. Live metadata:

| Field | Value |
| --- | --- |
| Note | `ref/blogs/442a6bf555914893e9891c11519de94f.md` |
| PDF | `lib/blogs/442a6bf555914893e9891c11519de94f.pdf` (210 KiB, git-tracked) |
| Title | `karpathy/llm-wiki.md` |
| URL | `https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f` |
| Marker `id` | `442a6bf555914893e9891c11519de94f` |
| Parent task | `sase.md` line `- [ ] #task #ref [[ref/blogs/442a6bf555914893e9891c11519de94f\|karpathy/llm-wiki.md]] [created::2026-10-15] ^ref-442a6bf555914893e9891c11519de94f` |
| Embed | `![[sase#^ref-442a6bf555914893e9891c11519de94f]]` |
| State | queued / ready, captured 2026-10-15, no audio, no sidecar, empty Highlights region |
| Git | note and PDF are tracked; `xlib/` is gitignored and this file has already left intake |

The stem is the GitHub gist id. `bob ref create` for a web article prefers `stem_from_url` over the extracted title (`src/native/highlights_ref/clip.rs`). For `gist.github.com/<user>/<32-hex>`, the last path segment wins `stem_from_segment`, and a 32-character hex string is a legal `--name` (`[A-Za-z0-9][A-Za-z0-9_.-]*`). The title `karpathy/llm-wiki.md` is already human; the PDF name is not.

This is rare, not systemic. A walk of `~/bob/lib/**/*.pdf` (425 PDFs) found **one** 32-hex stem, **zero** UUID stems, and **one** gist note. A rename command is still justified: the next gist clip will misspell itself the same way, and a manual fix has to touch too many identity surfaces at once.

A sensible new stem for this row is `karpathy_llm_wiki` (title, strip `.md`, `snake_case`). Leave the title alone unless Bryan asks.

## Critique of the stated plan

The request is: add `bob ref rename`, and a Bob Refs keymap that renames the selected reference.

That split is the correct architecture. Bob Mac Capture is a thin client of `bob` (`decisions:mac-capture-is-a-thin-client`; Refs README: the panel never parses frontmatter or writes the vault; ⌘S already shells out to `bob ref scan -w -f json`). A keymap that `mv`s files from Swift would violate that contract and would miss marker, task, and link rewrites.

What the plan under-states:

1. **Rename is a stem/identity operation, not a title operation.** The panel already shows `title`. Finder, Highlights, marker id `I` on the Copy card, the v2 `^ref-<stem>` block id, and `source_pdf` all key on the stem. Renaming “the reference” without moving the PDF leaves the complaint intact.

2. **The Mac surface is a card, not a bare key bound to a subprocess.** ⌘Y already taught this lesson: a keymap that needs input opens an in-panel card, intercepts keys, and sits first on the Esc ladder. Rename needs a text field, a preview of the plan, and Return to commit. A keymap that fires `bob ref rename` with no editor is unusable.

3. **PDF marker write-back is mandatory.** Scan’s `-w/--write-pdfs` is opt-in because most scans only rewrite notes. Rename changes `id` in the page-1 marker. Skipping that write leaves `bob ref marker` and the next scan looking at a stale identity. Docs already warn: keep Highlights and Obsidian idle during PDF writes.

4. **Highlight block ids hash the PDF path.** `annotation_block_id` / `image_annotation_block_id` SHA-256 `source_pdf_value(config, pdf)` plus payload (`sidecar_render.rs`). A stem change plus the next 15-minute `bob ref scan` would mint new `^h-…` ids and tombstone the old ones, breaking annotation-task links. The motivating row has `annotation_count: 0`, so it is safe today; a highlighted book is not.

5. **Today joins on `(task.path, task.block_id)`.** The Refs panel and `bob plan` identify the reading task that way. Changing `^ref-442a6bf…` without rewriting Task Links under today’s Pomodoros drops the row out of Today.

6. **Git tracks the library PDF.** This is an ordinary Git rename of `lib/…pdf` and `ref/…md`, plus edits to the parent note (and any other inbound links). `bob ref scan` already treats a tracked synced PDF as a Git rename. Do not invent a migrate-style auto-commit for a one-row gesture.

Those are design constraints, not reasons to reject the feature.

## Requirement adjustments (explicit)

These change the request. Each is justified.

### A. Stem rename is the feature; title is optional

**Adjustment:** `bob ref rename <REF> <NEW>` changes the stem. `--title/-T` is optional and updates frontmatter `title`, the H1, the marker `title`, and the v2 task’s display alias. Default: leave title unchanged.

The user named the PDF. The title is already `karpathy/llm-wiki.md`. Coupling them would surprise on every later rename that is only fixing a hash.

### B. Stay inside the same `ref_type` directory

**Adjustment:** this command does not refile `blogs` → `papers`. A type change is a different verb (`mv` / `refile`) with different Highlights-library and scan-path consequences.

### C. v1 refuses annotated refs and present sidecars

**Adjustment:** until highlight ids are stable across path changes, `rename` refuses when `annotation_count > 0` or a same-stem `.md` / `.textbundle` sidecar sits beside the PDF. Error code `has_annotations` (or `has_sidecar`) with a hint to wait for the follow-up.

This ships the gist case immediately and avoids silent tombstones. Lifting the gate is a follow-up, not a v1 blocker.

### D. Always write the PDF marker; `--write-pdf` is not a flag

**Adjustment:** a successful rename always stamps the new `id` (and title if requested) into the page-1 marker. There is no opt-out. Dry-run reports `marker_write: true` without touching bytes.

This diverges from `scan -w`. Identity lives in the marker; an optional write would be a footgun.

### E. Live by default, `--dry-run/-d` to plan

**Adjustment:** match `bob ref create` and `bob capture-pomodoro-name`, not `migrate-tasks` / `migrate-zorg`. A selected-row gesture that is dry-run-until-`--write` fights the Mac card (which would have to pass a hidden `--write` on Return). Migrations are bulk and reversible via one commit; this is one row and vault-sync will pick it up.

### F. Do not auto-commit

**Adjustment:** take `ref/scan.lock`, do not take `bob_sync.lock`, do not `git commit`. Same family as `ref scan` / `ref create`. `migrate-*` commit because they are bulk imports that must be one revert. A one-row rename should show up as a Git rename + parent-note edit for the next `vault-sync`.

### G. Mac UX is a rename card, not only a keymap

**Adjustment:** ⌘⇧R and a ⌘K “Rename…” item open the same in-panel card. The footer stays as it is (it is already dense; tests pin the exact hint string). Rename is rare; Copy is frequent, which is why ⌘Y is in the footer.

### H. Prefill the stem from the title, do not require Bryan to invent `snake_case` from scratch

**Adjustment:** the card prefills `validate_name(snake_case(strip_extension(title)))`. For this row that is `karpathy_llm_wiki`. The CLI still requires an explicit `NEW`.

### I. Companion: stop minting gist-hash stems

**Adjustment, separate small change:** `stem_from_url` should skip 32-character hex segments (and, on `gist.github.com`, skip them in favor of the extracted title). That does not replace rename; it stops the next gist from landing in the same hole.

Call this out as companion work, same epic or a follow-up bead, not a substitute.

## Alternatives considered

| Approach | Why it loses |
| --- | --- |
| Title-only / `aliases` | Panel title is already fine. Finder, Highlights, Copy-card `I`, and the PDF path stay hashed. |
| Obsidian rename + manual `mv` of the PDF | Misses marker `id`, v2 `^ref-<stem>`, `source_pdf`, audio, sidecars, assets, Today links. Easy to desync scan (note path is `pdf_relative_path` with `.md`). |
| Recapture with `bob ref create <URL> -N karpathy_llm_wiki` | Dedupes on the gist URL and refuses, or `--force` overwrites intake and births a second reading task. Loses the existing `^ref-…` line. |
| Mac app `FileManager.moveItem` | Violates the thin-client rule; cannot stamp the marker or rewrite `sase.md`. |
| `bob ref sync` after a hand rename | Sync maps `lib/<type>/<stem>.pdf` → `ref/<type>/<stem>.md`. A PDF moved without the note looks like a new ref; the old note becomes an orphan. |
| Dry-run-default migrate-style command | Wrong shape for a one-row UI gesture. |

Prevention-only (fix gist stems, no rename) would leave this PDF misnamed forever. Do both.

## Identity graph a rename must keep coherent

`scan` derives the note path from the PDF path (`ref_note_path` in `io.rs`): `lib/<ref_type>/<stem>.pdf` ↔ `ref/<ref_type>/<stem>.md`. `id` is the stem. v2 birth allocates `^ref-<stem>` (`docs/highlights-ref-sync.md`). The panel’s `RefItem.id` is the **note path**, because PDF stems can repeat.

For the gist row, a rename to `karpathy_llm_wiki` must update:

1. `lib/blogs/442a6bf….pdf` → `lib/blogs/karpathy_llm_wiki.pdf` (git rename)
2. `ref/blogs/442a6bf….md` → `ref/blogs/karpathy_llm_wiki.md` (git rename)
3. Frontmatter `id`, `source_pdf`, `highlights_marker_base` / hash
4. Page-1 marker `id` (mandatory PDF write)
5. Same-stem audio, Markdown sidecar, TextBundle, `*.assets/` (none here; still in the planner)
6. v2 task line on `sase.md`: wikilink target and `^ref-…` block id
7. Managed embed in the ref note: `![[sase#^ref-…]]`
8. Vault-wide wikilinks to the old note path, old PDF path, old assets, and old task block (`[[sase#^ref-442a6bf…]]` under Pomodoros, annotation tasks, daily notes)
9. v1 notes: the in-note `[[lib/…/<stem>.pdf]]` tracker line

URL identity keys stay put. `find` by gist URL still hits. `find` by old stem misses unless the old stem is kept as an `aliases` entry.

**Recommended default:** append the old stem to `aliases` (`--no-alias/-A` to skip; every public long option needs a short alias). Path-based `[[ref/blogs/old]]` links still need a rewrite; the alias only covers `[[old]]` when that stem is unique.

## Recommended CLI

Place the verb in the **Library** help group, alphabetically between `migrate-zorg` and `show`:

```
Library:
  find, list, migrate-tasks, migrate-zorg, rename, show
```

That matches `cli_rules.md` (alphabetical within a section; nest under a noun with a membership rule: `bob ref <verb>` already means library + Highlights pipeline). Do not put it under `bob capture` (frozen) or `bob task` (vault-wide task-line rewrites only).

```text
bob ref rename <REF> <NEW>
              [-A|--no-alias] [-b|--bob-dir DIR] [-d|--dry-run]
              [-f|--format human|json] [-l|--lib-dir PATH]
              [-r|--ref-dir PATH] [-T|--title TITLE]
```

- `<REF>` reuses `ref show` exact resolution (vault path, stem, id, URL, arXiv, DOI, exact title). Ambiguous / unknown → same `ambiguous_reference` / `unknown_reference` envelopes as show.
- `<NEW>` runs `validate_name` (strip one trailing `.pdf`, `[A-Za-z0-9][A-Za-z0-9_.-]*`). Refuse `/`, spaces, a different `ref_type` prefix, and a no-op that only changes case when the destination collides case-insensitively with a *different* file. `NEW == old stem` is a successful no-op.
- Collision: refuse, do not auto-suffix. Create’s `<stem>_2` walk is for *minting* names. Rename is an explicit choice.
- `-d/--dry-run`: plan, take no lock, write nothing.
- `-f json`: one compact stdout line, `schema_version: 1`, `command: "ref rename"`. Human mode is colored, scannable, lists every planned move and every rewritten link.
- Shared dir flags stay identical to the other `bob ref` verbs.

Writer protocol, in order:

1. Resolve and plan (destinations, sidecar/audio/assets, inbound-link grep, v1 vs v2).
2. Refuse `has_annotations` / `has_sidecar` (v1 gate), `name_taken`, `dirty_target`, `missing_pdf`, `intake_only` (v1 is library notes only).
3. Acquire the same `ref/scan.lock` as `bob ref scan` (wait/stderr/`scan_busy`). Dry-run skips the lock.
4. Git dirty preflight on every path that will change, same family as scan (tracked PDF + note + parent note). Unrelated dirty files elsewhere do not block.
5. Stamp the new marker to a temp PDF; verify round-trip.
6. Move PDF, companions, assets; write the new note; rewrite inbound links with a wikilink parser that skips fenced code and inline code; delete the old note.
7. Rebuild the index: `NEW` is `in_library`, old path is gone, task `(path, block_id)` matches the new stem, `source_pdf` points at the new file.
8. On mid-run failure, print what landed and what did not. There is no multi-file transaction (v2 sync already documents this). Rerunning a partial rename must be safe: if the new stem exists and the old is gone, report `already_renamed`; if both exist, refuse.

JSON success sketch:

```json
{
  "ok": true,
  "schema_version": 1,
  "command": "ref rename",
  "generated_at": "2026-10-15T18:00:00",
  "mode": "write",
  "ref": { "...index row at the new path..." },
  "from": {
    "stem": "442a6bf555914893e9891c11519de94f",
    "note": "ref/blogs/442a6bf555914893e9891c11519de94f.md",
    "pdf": "lib/blogs/442a6bf555914893e9891c11519de94f.pdf",
    "task": {"path": "sase.md", "block_id": "ref-442a6bf555914893e9891c11519de94f"}
  },
  "to": {
    "stem": "karpathy_llm_wiki",
    "note": "ref/blogs/karpathy_llm_wiki.md",
    "pdf": "lib/blogs/karpathy_llm_wiki.pdf",
    "task": {"path": "sase.md", "block_id": "ref-karpathy_llm_wiki"}
  },
  "moves": [{"from": "...", "to": "...", "kind": "pdf|note|audio|sidecar|assets"}],
  "rewrites": [{"path": "sase.md", "count": 1}],
  "alias_added": "442a6bf555914893e9891c11519de94f",
  "marker_write": true,
  "title_changed": false
}
```

Failure envelope matches find/show: `ok: false`, `error.code/message/hint`, exit 1; usage errors exit 2.

Tests live under `tests/cli/ref_library/rename.rs` (library resolver, collisions, aliases, v2 task rewrite) and `tests/cli/highlights/` for marker write + companion moves. Reuse the scratch-vault fixtures already used by scan/create.

Docs: `docs/ref.md` choose-a-command table, `docs/highlights-ref-sync.md` identity paragraph, `docs/getting-started.md` “what commands change” row (`ref rename` writes notes and PDFs; `--dry-run` does not), README command list, clap after-help examples.

## Recommended Mac panel

Bob Refs already has the right shapes:

- **Write lane:** `BobRefsFetcher.scan()` uses `decodeReport`, lane `refs-scan`, 300 s, `cancelsPreviousInLane: false`. Rename is one PDF, so a `refs-rename` lane with a **60 s** timeout is enough (default process timeout is 20 s; a marker rewrite on a large book can exceed that).
- **Overlay:** Copy card swallows the key monitor while open (`RefsPanel` returns `nil` from the monitor when `copyCard != nil`). Rename does the same, and is mutually exclusive with the copy card.
- **Esc ladder:** rename card → copy card → banner → query → scope → close.
- **Selection:** `RefItem.id` is the note path. After a successful rename, refresh the snapshot (same post-pass as scan: list + Today) and reselect `to.note`. Rewrite `refs-open-log.json` paths so Recently opened does not drop the row.
- **Watcher:** the panel already watches `<vault>/ref` and `<vault>/lib`. Defer watcher refresh while rename runs, then one refresh, matching scan.

Keymap:

| Gesture | Action |
| --- | --- |
| ⌘⇧R | Open rename card for the selected row |
| ⌘K → Rename… | Same card |
| Return | Commit (`bob ref rename <path> <stem> -f json`) |
| Esc | Dismiss card |

⌘⇧R does not collide with ⌘R (refresh) or the global Refs hotkey (⌃⇧⌘O). Do not steal a printable `r` (search always owns printables). Do not use Return-to-rename (Return opens Highlights).

Card contents:

1. Kind tile + current title
2. Stem field, prefilled, validated live with the same `validate_name` rules (reject in the UI before spawning `bob`)
3. Preview lines: PDF, note, task id
4. Optional “also set title” disclosure (off by default) → passes `-T`
5. Quiet hint: close the PDF in Highlights if it is open
6. Footer: `↩ Rename  esc Cancel`

On success: HUD “Renamed to karpathy_llm_wiki”, keep the panel up, selection on the new row. On `has_annotations`: banner with the CLI hint, card stays open. On `name_taken`: inline field error.

Swift work: `RefsCommand.showRenameCard`, `RefsAction.rename`, `RefsKeyRouter` for ⌘⇧R, `BobRefsFetcher.rename(path:new:title:)`, `RefsRenameResponse: SchemaVersioned` with `expectedSchema: 1`, decode unknown fields loosely like scan. Tests: key router, actions menu sections, footer *unchanged*, card prefills, selection follows `to.note`.

Compile Mac sources on a Swift host (`just portable-check` is not enough for `Sources/BobMacCapture*`). Coordinate the JSON contract across bob-cli and bob-mac-capture; land CLI first so the app can decode a real binary.

## Follow-ups (not v1)

1. **Highlight-id stability.** Keep existing `^h-…` ids when PDF `sha256` + annotation payload match and only the path changed. That lifts the v1 annotation gate and also makes a hand-moved PDF safe. Do **not** switch the hasher to content-hash in one shot: that would churn every id in the library on the next scan.
2. **Gist/hash stem minting.** Skip 32-hex URL segments; fall through to title `snake_case`.
3. **Intake rename.** `xlib/` files with no note yet. Different resolver (`find -i`), no v2 task.
4. **Refile / type change.** `blogs` → `papers` is not rename.
5. **Retitle-only.** A later `bob ref retitle` if marker+frontmatter+H1+task alias should move without files. Not needed for the gist.

## Is this a good idea?

Yes. I would implement it, with the adjustments above.

The feature is small in frequency and large in surface area. That is exactly when a single `bob` writer plus a thin Mac card beats ad-hoc `mv`. The gist row is a complete, currently-safe v1 fixture: tracked PDF + note, one inbound task line, empty Highlights body, obvious target stem.

I would not ship a keymap that shells out without a card, a title-only command, or a v1 that rewrites highlighted books before ids are stable.

## Recommended solution (implementation order)

1. **bob-cli:** `bob ref rename` as specified (Library group, live default, mandatory marker write, v1 annotation/sidecar refusal, scan lock, no commit, JSON schema 1, alias-by-default). Tests on a scratch vault that clones this gist shape, plus collision, no-op, dirty-target, and v2 task-rewrite cases.
2. **Docs + completion:** clap registration is enough for `bob ref <TAB>`; update `docs/ref.md`, `docs/highlights-ref-sync.md`, `docs/getting-started.md`.
3. **bob-mac-capture:** rename card, ⌘⇧R, ⌘K item, `refs-rename` lane, post-rename refresh and reselect. Do not change the footer.
4. **Companion PR (same stack or immediately after):** gist/hex stem skip in `stem_from_url` / clip finalization.
5. **Follow-up:** highlight-id stability, then lift the annotation gate.

Worked command for the motivating file, after landing:

```bash
bob ref rename 442a6bf555914893e9891c11519de94f karpathy_llm_wiki -d -f json
bob ref rename 442a6bf555914893e9891c11519de94f karpathy_llm_wiki
```

From Bob Refs: select the row, ⌘⇧R, accept the prefilled `karpathy_llm_wiki`, Return.
