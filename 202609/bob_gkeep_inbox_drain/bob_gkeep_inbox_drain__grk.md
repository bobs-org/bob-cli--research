# `bob gkeep`: drain Google Keep home into Obsidian tasks

- **Researcher:** grk
- **Date:** 2026-09-28
- **Question:** How should `bob gkeep` migrate Keep home notes into `~/bob/gkeep_inbox.md`, archive them only after a verified write, and list both sides — and is that the right product at all?

## Headline

**Yes, build this.** Keep is already the phone-capture inbox; the vault already expects a `bob gkeep` command; the current overflow path is a Google Doc dump. The official Google Keep API cannot do the job. Implement a native Rust `bob gkeep` that talks to the existing `keep-cli` (gkeepapi) adapter, writes Bob `#task` lines into `gkeep_inbox.md`, then archives in Keep only after a parse-back of those Keep IDs.

Name the mutating verb **`pull`** (daily inbox drain), keep **`migrate` as an alias**, and treat **`list`** as the read-only companion. Do not merge into `mac_inbox.md`. Do not put this on `bob nightly` until pull has been used by hand.

## Verdict

This is a good idea for this vault. It is the missing automation of a ritual that already exists on paper.

Evidence already in the vault:

- `gkeep_inbox.md` is a stub whose body says *“The tasks below are pulled in by the `bob gkeep` command.”* That sentence was written during the zorg→Obsidian conversion (`generated_from_zorg: true`, source `~/org/gkeep_inbox.zo`, 2026-02-14). The command name is a pre-existing contract, not a new product fantasy.
- `legacy_gkeep_notes.md` still carries a daily `@FRESHNESS` reminder to clear the Keep inbox.
- `gkeep_gdocs_inbox_dump.md` is a live `wip` project whose `^prj` task is *“Empty this Google Keep inbox dump.”* Overflow today is: copy Keep → a new Google Doc → triage later. That is the pain `bob gkeep pull` should retire.
- `mac_inbox.md` is the Mac/Hammerspoon capture sink. Phone capture and Mac capture already have different provenance; they should keep different notes.

The original request is the right *product* (one-way drain, archive after success, list both sides). Several *requirements* should change so the command is a daily GTD drain rather than a one-shot importer. Those adjustments are called out in [Justified requirement changes](#justified-requirement-changes).

---

## What `#home` actually is

[keep.google.com/#home](https://keep.google.com/#home) is Keep’s **Notes** view: every note that is not archived and not in trash. Pinned notes sit in a Pinned band at the top; everything else is Others. Labels, Reminders, and Archive are different hashes (`#label/…`, `#reminders`, `#archive`).

gkeepapi encodes the same states as `archived`, `trashed`, `pinned`, plus a URL of the form `https://keep.google.com/u/0/#NOTE/<id>` or `#LIST/<id>` (`node.TopLevelNode.url` in kiwiz/gkeepapi 0.17.1).

So “inbox items I can see at `#home`” means:

```text
archived == false AND trashed == false
```

That set includes **pinned** notes. Pinning is Keep’s way of leaving reference material on the home screen (phone numbers, a packing list, a recipe). Draining *all* of `#home` will archive those too. Honor the user’s URL as the default *scope definition*, and add a safety default: skip pinned notes unless `--include-pinned` is set. That is the one place this research disagrees with a literal reading of the request.

---

## Keep access: the official API is a dead end

### Official Workspace Keep API (`keep.googleapis.com/v1`)

Google’s own docs, last updated 2026-09-03, describe an **enterprise-only** REST API for CASB-style admin tools, authorized with **domain-wide delegation** ([Keep API overview](https://developers.google.com/workspace/keep/api/guides)). Google’s issue tracker marked consumer OAuth as *Won’t Fix (Intended Behavior)*: the `keep` / `keep.readonly` scopes work through domain-wide delegation for enterprise apps, not a personal Gmail desktop client ([issuetracker 210500028](https://issuetracker.google.com/210500028)).

Even if this account were Workspace Enterprise, the API cannot satisfy the archive requirement:

| Capability the command needs | Official v1 |
| --- | --- |
| List notes | `GET /v1/notes`; filter fields are `createTime`, `updateTime`, `trashTime`, `trashed` only |
| Distinguish home vs archive | **No.** The `Note` resource has `trashed` / `trashTime`. There is no `archived` field and no archive filter |
| Update title/body | **No.** Methods are `create`, `get`, `list`, `delete` |
| Archive a note | **No.** `delete` “removes the resource immediately and cannot be undone” |
| Pinned, labels, color, collaborators as first-class fields | **No** on the published `Note` resource |
| Attachments | `GET /v1/{name=notes/*/attachments/*}` download only |

The user’s “archive in Google Keep once we are sure the migration was successful” is **impossible** on `keep.googleapis.com`. Trash/delete is the only mutation besides create, and delete is permanent.

### Unofficial mobile API (what actually works)

[kiwiz/gkeepapi](https://github.com/kiwiz/gkeepapi) 0.17.1 (PyPI 2026-01-05) talks to the private Android Keep API:

- Endpoint: `https://www.googleapis.com/notes/v1/` (`KeepAPI.API_URL`)
- Auth: a **master token** via `gpsoauth`, then OAuth scopes `memento` + `reminders`
- Inbox query: `keep.find(archived=False, trashed=False)`
- Archive: `note.archived = True` then `keep.sync()` (sets `isArchived` on the node and marks it dirty)
- Lists, indentation, labels, colors, pin, collaborators, image/audio blob metadata, and `getMediaLink()` are all present
- Reminders exist as a separate API; `_sync_reminders()` is currently commented out in `Keep.sync()`, so reminder data is **not** trustworthy in 0.17.1
- Full note tree is pulled on `authenticate()`; `dump()` / `restore()` exist specifically because that first sync is slow

This is an unofficial protocol. Google can break it. Every Keep CLI in the wild (keep-it-markdown’s `-m` “move to archive after export”, KeepSydian, gkeep.nvim — the last of which the author retired because of API pain) is on this same library. There is no supported consumer alternative that can archive.

### Google Takeout + Obsidian Importer

The [official Obsidian Keep import](https://obsidian.md/help/import/google-keep) is a one-shot Takeout zip → Markdown notes. It cannot archive, is hours-to-days latent, flattens checklists, and drops reminders. Fine for a historical dump. Useless as a daily inbox drain.

### Browser automation of keep.google.com

Possible, ugly, session-cookie fragile, and a worse reliability story than gkeepapi. Reject.

---

## What already exists on this machine

This is the load-bearing local finding: **Keep access is already implemented.**

`~/bin/keep-cli` is a `pybash ~/lib/keep_cli` wrapper. `~/lib/keep_cli/main.py` is a careful gkeepapi 0.17.1 client with:

| Subcommand | Role |
| --- | --- |
| `auth status` / `set-token` / `exchange` / `logout` | Master token in the `keep-cli` keyring (or `KEEP_CLI_MASTER_TOKEN`) |
| `inbox` (alias `ls`) | Non-archived, non-trashed notes; `--json` |
| `show`, `find`, `items` | Read a note / search / list checklist items |
| `backup` | JSONL dump (inbox, or `--all`) |
| `archive` / `unarchive` / `trash` / `restore` | Mutations with `--dry-run` and `--json` |
| `edit`, `check`, `uncheck`, `item-edit`, `item-delete` | Content edits |

JSON note records already carry `id`, `type` (`note` \| `list`), `title`, `text`, `items[]` (with `checked`, `indented`, `parent_item_id`), `archived`, `trashed`, `pinned`, `color`, `url`, and timestamps.

Auth is **not currently configured** in this environment (`keep-cli auth status` → `email: null`, `token_available: false`). First-run setup is part of the product, not an afterthought.

bob-cli itself has **no HTTP client** (`Cargo.toml` is clap / chrono / serde / regex / rquickjs / lopdf). Native commands are Rust. External tools are already a documented runtime-dependency pattern (`git`, `pandoc`, clipboard helpers, `obsidian` CLI). Shelling out to `keep-cli --json` fits that pattern. Reimplementing `gpsoauth` + the notes/v1 changes protocol in Rust does not.

`gkeep_inbox.md` today:

```markdown
---
generated_from_zorg: true
parent: "[[inbox]]"
...
---
- See [[legacy_gkeep_notes]] ...
- The tasks below are pulled in by the `bob gkeep` command.

## Tasks
```

It is **not** a capture target. `bob capture-targets` pins `mac_inbox` as the only Inbox and then lists area/project notes; `gkeep_inbox.md` has no `type: [[area]]` frontmatter, so it does not appear. After this command exists, that note should become a real area, on the same footing as `mac_inbox.md`, so `bob capture-tasks --route gkeep_inbox` and task-status grouping work.

Bob task shape, from `capture::format_task_line`:

```text
- [ ] #task <body> [created::YYYY-MM-DD]
```

Scheduled captures use `[?]`. Block IDs are `[A-Za-z0-9-]+` (`collect_done::is_block_id_byte`). Writes already go through `collect_done::atomic_write` (temp file + rename). `## Tasks` is the preferred insertion point. That is the renderer `bob gkeep pull` should reuse, not re-spell.

`bob-cli` CLI conventions from `sase/memory/cli_rules.md`: excellent `-h|--help`, alphabetically sorted public subcommands/options, a short alias on every public long option, colored output when it helps.

---

## Critique of the original plan

The request as written:

1. A `bob gkeep` command.
2. A subcommand that migrates all `#home` items into `~/bob/gkeep_inbox.md` as Obsidian tasks.
3. Archive in Keep after a successful migration.
4. A subcommand that lists Keep and/or the vault file.

What is right:

- Destination file is already the vault’s chosen sink. Do not invent a third inbox.
- Archive-after-success is the correct GTD empty-the-inbox move. Leaving copies in Keep guarantees double-processing.
- Listing both sides is the way a human trusts the drain before and after.

What is weak or unsafe if taken literally:

- **“Migrate” sounds one-shot.** This is a daily drain, like processing email. A command named `migrate` will be run once, feared, and then the GDoc overflow will come back. The verb should be `pull` (or `drain`). Keep `migrate` as an alias so the original wording still works.
- **“All `#home` items” includes pinned reference notes.** Archiving those is data loss of a different kind: they disappear from the phone home screen. Default: skip pinned; print them in the plan as `skipped:pinned`.
- **No idempotency story.** A crash after vault write and before archive, or a partial archive, will duplicate tasks on the next run unless every written task carries a stable Keep ID. This is mandatory, not optional.
- **“Successful migration” is underspecified.** A non-zero `fs::write` is not success. Success is: atomic replace of `gkeep_inbox.md`, parse-back finds every planned Keep ID as an open `#task`, *then* archive those IDs. Archive failures after that point are recoverable because the next pull sees the IDs already in the vault and skips them.
- **“List all items in Google Keep” is unbounded.** Listing archived + trash is a debug tool, not the daily view. Default list scope for Keep should match pull scope (home). `--keep-scope archived|trash|all` can exist for forensics.
- **No mapping for lists, images, collaborators, reminders.** A Keep list of 12 items dumped as one blob of text is worse than a parent task with child bullets. Shared notes must not be archived without an explicit flag. Reminders are not currently synced by gkeepapi.
- **No auth product.** Master tokens are password-equivalent. bob-cli should not grow its own token store; it should fail with a pointer at `keep-cli auth` (or a thin `bob gkeep auth` wrapper).
- **Putting this inside bob-cli as Python, or putting Keep protocol in Rust, both fight the repo.** Native Rust owns vault mutation. `keep-cli` already owns Keep. That split is the design.
- **Nightly auto-pull** would surprise: a phone note captured at 11pm would vanish from Keep before morning triage. Keep pull interactive (or a later opt-in hook), not `bob nightly`.

Would I take a different approach than “new bob subcommand + vault file + archive”? Only in the small: I would still land tasks in `gkeep_inbox.md`, still archive, still list both sides — I would not two-way-sync (KeepSydian), would not import Takeout zips, would not dump into `mac_inbox.md`, and would not make each Keep note its own Markdown file.

---

## Justified requirement changes

Call these out as deliberate deltas from the request.

| # | Original | Change | Why |
| --- | --- | --- | --- |
| 1 | Unnamed “migrate” subcommand | **`bob gkeep pull`**, with **`migrate` as a hidden/visible alias** | Daily verb. The vault stub already says “pulled in.” |
| 2 | All `#home` notes | `#home` = unarchived + untrashed; **skip pinned unless `--include-pinned`** | Pinned notes are usually reference, not inbox. |
| 3 | Archive after “successful migration” | **Verify-then-archive protocol** below, per note, idempotent on Keep ID | Partial failure must not duplicate or lose. |
| 4 | List “all Google Keep” and/or vault | **`list --source keep\|vault\|all`** (default `all`); Keep side defaults to home | Matches the drain; `--keep-scope` for the rest. |
| 5 | Implied green-field Keep client | **Keep I/O through existing `keep-cli --json`** | Auth, inbox, archive, dry-run, list JSON already exist. |
| 6 | (unspecified) task shape | **One Keep note → one Bob `#task`**; list items become child bullets | Matches `bob capture` rendering and Tasks-plugin grouping. |
| 7 | (unspecified) identity | Stable **`^gk-<keep-id>`** block ID; Keep URL as a child bullet | Block IDs are `[A-Za-z0-9-]+`. Do **not** invent a `[keep_id::]` inline field: Obsidian Tasks parses trailing fields right-to-left and stops at the first unknown name, which would hide `[created::]` / `[scheduled::]`. |
| 8 | (unspecified) `gkeep_inbox.md` schema | Promote to an **area** note (`type: [[area]]`, `id: gkeep_inbox`, `done_tasks`) like `mac_inbox.md` | Makes `capture-tasks` / status hooks / `move-done-tasks` work. Still not the default capture route. |
| 9 | (unspecified) nightly | **Do not add to `bob nightly` in v1** | Drain is a conscious inbox-emptying step. |
| 10 | (unspecified) media | Import text always; **download images into `img/gkeep/` when `getMediaLink` works**; if media fails, leave the Keep note un-archived unless `--allow-missing-media` | Archive-after-success includes “the bits we care about are in the vault.” |
| 11 | (unspecified) sharing | **Do not archive collaborator notes** unless `--archive-shared` | Archiving a shared card changes someone else’s Keep. |
| 12 | (unspecified) volume | **`--limit N`** and **`--dry-run` / `-d` on pull** | Overflow days should process a handful, matching the existing “5 a day” overflow notes. |

---

## Recommended CLI

Follow `bob projects` / `bob highlights`: nested clap, `subcommand_required(true)`, `arg_required_else_help(true)`, sorted subcommands, every public long option has a short alias, `--format human|json` (`-f`) on read commands, `--dry-run` (`-d`) on writers, `--bob-dir` (`-b`) everywhere a vault path is used, `NO_COLOR` respected via existing `Styler`.

```text
bob gkeep
bob gkeep --help

bob gkeep auth status
bob gkeep auth set-token
bob gkeep auth exchange --oauth-token TOKEN
bob gkeep auth logout

bob gkeep list
bob gkeep list --source keep
bob gkeep list --source vault
bob gkeep list --source all          # default
bob gkeep list --keep-scope home     # default for Keep side
bob gkeep list --keep-scope archived
bob gkeep list --keep-scope all
bob gkeep list --format json

bob gkeep pull
bob gkeep pull --dry-run
bob gkeep pull --limit 5
bob gkeep pull --include-pinned
bob gkeep pull --archive-shared
bob gkeep pull --allow-missing-media
bob gkeep pull --no-archive          # write vault only; for first-run trust
bob gkeep migrate                    # alias of pull
```

Human `list` should be a colored two-pane or two-section table, not a dump:

```text
Keep home (7)                          Vault gkeep_inbox.md (12 open)
ID           PIN  TYPE  TITLE          STATUS  BLOCK          TITLE
1a2b3c4d5e6f      note  Buy milk       [ ]     gk-1a2b3c4d5e  Buy milk
9f8e7d6c5b4a  *   list  Packing        [ ]     gk-9f8e7d6c5b  Packing
…                                      [x]     gk-00aa11bb    Old imported

  3 Keep notes have no vault task
  1 vault task has no matching Keep home note (already archived or deleted)
```

`pull --dry-run` prints a **plan**, never writes:

```text
pull plan  keep home → gkeep_inbox.md

  write     1a2b3c4d5e6f  note  Buy milk
  write     9f8e7d6c5b4a  list  Packing (4 items)
  skip      deadbeef0001  already in vault as ^gk-deadbeef0001
  skip      cafe00000002  pinned (pass --include-pinned)
  skip      face00000003  shared with other@gmail.com

  would write 2 tasks, archive 2 notes, skip 3
```

On success, `Styler::success_prefix` (`ok` / `[dry-run] ok`) plus counts. Failures name the Keep ID, the vault path, and the step (`write`, `verify`, `archive`).

`auth *` is a thin passthrough to `keep-cli auth *` so the user never has to know two tools, and so bob-cli never holds a master token.

---

## Reliability protocol for `pull`

This is the heart of the design. Archive is a Keep mutation; the vault is the system of record. Order:

1. **Preflight.** `keep-cli auth status --json`. Missing email/token → exit 2 with the exact `keep-cli auth set-token` (or `bob gkeep auth set-token`) invocation. Missing `keep-cli` on `PATH` → exit 2 naming the runtime dependency.
2. **Snapshot Keep.** `keep-cli inbox --json` (and optionally `keep-cli backup -o <xdg-state>/bob/gkeep/last-inbox.jsonl` so a bad archive is reconstructable). Prefer a gkeepapi `dump()` cache under `XDG_CACHE_HOME/keep-cli/` so the second pull of the day is not a full-tree sync — this is a small keep-cli enhancement, worth doing as part of the same effort.
3. **Snapshot vault.** Read `gkeep_inbox.md` (create from a template if missing). Parse existing `^gk-…` block IDs and open-task set via the existing `note_tasks` scanner.
4. **Plan.** For each home note: skip if `^gk-<id>` already present; skip pinned/shared according to flags; skip empty notes with a warning; else stage a task block.
5. **`--dry-run` stops here.** No file writes, no Keep mutations.
6. **Write vault atomically.** Reuse `collect_done::atomic_write`. Insert new task blocks under `## Tasks` in Keep updated-time order (newest last or newest first — pick newest last so the file reads like `bob capture`). Preserve any human text above `## Tasks`.
7. **Verify.** Re-read the file. Every staged Keep ID must parse as an open `#task` with that block ID and a non-empty description. If verification fails, **do not archive anything**. Leave the file as written only if it is well-formed; otherwise restore the previous bytes from the in-memory snapshot (the temp-rename already makes a torn write impossible; a logic bug in rendering is the remaining risk).
8. **Archive per verified ID.** `keep-cli archive <id>` one at a time (or a future `keep-cli archive --batch` that still reports per-id). Collect successes and failures. A mid-loop Keep error prints the remaining IDs and exits 1. Those remaining IDs are already in the vault, so the next `pull` skips them (`skip: already in vault`) and can offer `bob gkeep pull --archive-only` later if we want a retry-without-rewrite path. v1 can retry archive of already-imported home notes as part of the normal pull: if the ID is in the vault **and** still on Keep home, archive it. That closes the crash window without a third subcommand.
9. **Report.** Written, archived, skipped, failed. JSON shape mirrors other bob commands: top-level counts plus an ordered `items` array.

`--no-archive` is the trust-building first run: write the vault, leave Keep untouched, `list --source all` to compare, then a second pull archives the already-imported IDs (step 8’s retry path).

Do not hold the vault Git lock across Keep network calls. Do use the same note-write discipline capture uses (in-memory snapshot, one atomic replace).

---

## Task mapping (what “beautiful” means in the file)

Keep **text note** titled “Buy milk”, body empty:

```markdown
- [ ] #task Buy milk #gkeep [created::2026-09-20] ^gk-1a2b3c4d5e6f
  - https://keep.google.com/u/0/#NOTE/1a2b3c4d5e6f
```

Keep **text note** with a body:

```markdown
- [ ] #task Call the dentist #gkeep [created::2026-09-18] ^gk-aa11bb22cc33
  - Ask about the crown appointment next month
  - Bring insurance card
  - https://keep.google.com/u/0/#NOTE/aa11bb22cc33
```

Keep **list** “Packing”:

```markdown
- [ ] #task Packing #gkeep [created::2026-09-12] ^gk-9f8e7d6c5b4a
  - [ ] Passport
  - [ ] Charger
    - [ ] USB-C brick
  - [x] Earplugs
  - https://keep.google.com/u/0/#LIST/9f8e7d6c5b4a
```

Rules:

- Title wins as the task body; if the title is empty, use the first non-empty line of text / first unchecked item; if still empty, skip with `skip:empty`.
- `#gkeep` marks provenance for Dataview / Tasks queries without a new inline field.
- `[created::]` uses the **Keep created date**, not pull time. That is honest provenance and matches how capture stamps Mac inbox tasks.
- Keep list checkboxes become child checkbox bullets (not `#task` children). Nested `indented` items nest one level, which gkeepapi already exposes. Keep only allows one indent level; Bob can preserve that.
- Labels on the Keep note, if any, become additional `#tags` after sanitizing to Bob’s tag charset. Unknown/unsafe characters drop with a warning.
- Color is ignored. It is not a Bob task property.
- Images: `![](img/gkeep/<keep-id>-<n>.jpg)` as a child, files written beside the note write. Drawings/audio: same if `getMediaLink` returns; otherwise a child bullet `media: <type> (not downloaded)` and the note stays on Keep home.
- Reminders: because gkeepapi does not sync them, print `warning: reminders are not imported` once per pull if we detect annotation remnants, and do **not** invent `[scheduled::]` from incomplete data.

`gkeep_inbox.md` frontmatter after promotion:

```yaml
---
parent: "[[inbox]]"
type: "[[area]]"
id: gkeep_inbox
aliases: []
tags: [gkeep]
done_tasks: "[[done/gkeep_inbox_done]]"
---
```

Keep the human intro lines (legacy pointer, “pulled in by `bob gkeep`”). Let `bob task-status-hooks` grow the usual Next / Blocked / Done groups once this is an area with a Tasks section — same as `gkeep_gdocs_inbox_dump.md` already does.

---

## Architecture

```text
┌─────────────────────────────────────────────┐
│ bob gkeep          native Rust in bob-cli   │
│  clap, Styler, note_tasks, atomic_write,    │
│  capture task renderer, --format json       │
└──────────────┬──────────────────────────────┘
               │ subprocess, JSON contract
               ▼
┌─────────────────────────────────────────────┐
│ keep-cli           ~/lib/keep_cli (Python)  │
│  gkeepapi 0.17.1 + gpsoauth + keyring       │
│  inbox --json / archive / auth / backup     │
└──────────────┬──────────────────────────────┘
               │ unofficial notes/v1
               ▼
         Google Keep (home / archive)
```

**Rust owns:** CLI UX, vault schema, idempotency, verify-then-archive sequencing, colored list, tests against fixture JSON + temp vaults.

**keep-cli owns:** master-token auth, Keep protocol, archive mutation, JSON serialization of notes.

Contract to freeze (keep-cli already almost matches):

```json
{
  "id": "1a2b3c4d5e6f",
  "type": "note",
  "title": "Buy milk",
  "text": "",
  "items": [],
  "archived": false,
  "trashed": false,
  "deleted": false,
  "pinned": false,
  "color": "DEFAULT",
  "url": "https://keep.google.com/u/0/#NOTE/1a2b3c4d5e6f",
  "timestamps": { "created": "2026-09-20T12:00:00Z", "updated": "..." }
}
```

Small keep-cli upgrades worth bundling:

1. Persist `Keep.dump()` under `XDG_CACHE_HOME` so `inbox` is not a full resync every call.
2. Optional `keep-cli archive --json --batch-ids -` reading IDs from stdin, still reporting per-id success. Bob can live without this (loop is fine for inbox-sized N).
3. Include `collaborators` and `labels` in `--json` (today’s summary omits them; pull needs them for skip rules and tags).

Do **not** vendor gkeepapi into bob-cli. Do **not** add reqwest. Document `keep-cli` under README “Runtime dependencies.”

Tests: fixture a fake `BOB_GKEEP_CLI` helper that speaks the JSON contract. Never hit live Keep in CI. Vault tests follow `tests/cli.rs` capture-inbox patterns.

---

## Alternatives considered

| Option | Verdict |
| --- | --- |
| Official Keep API in Rust | Cannot archive, cannot see home vs archive, enterprise-only. Reject. |
| Reimplement notes/v1 in Rust | Months of auth/protocol pain, no HTTP stack in bob-cli today, duplicates keep-cli. Reject. |
| Call gkeepapi from an embedded Python script in bob-cli | Fights “native Rust by default”; keep-cli is already the script. Reject as a second copy. |
| `keep-cli pull` that writes the vault itself | Splits Bob task rendering out of bob-cli; two writers of `#task` lines will drift. Keep-cli stays Keep-only. |
| Obsidian KeepSydian / Importer plugins | KeepSydian is two-way sync with a supporter paywall; Importer is Takeout. Neither is a `bob` command, neither verify-then-archives into this file’s task schema. Reject as the implementation. |
| Dump into `mac_inbox.md` | Mixes phone and Mac capture. The vault already split them. Reject. |
| One Markdown file per Keep note | Explodes the vault root; fights `move-done-tasks` and the existing `gkeep_inbox.md` contract. Reject. |
| Two-way sync | Conflicts with “archive after success.” Keep is the capture surface; Obsidian is the system of record. One-way drain. |
| `bob nightly` step | Too surprising. Offer a documented optional hook later. |
| keep-it-markdown `-m` | Closest prior art (export then archive) but writes one file per note into an `mdfiles/` folder, not Bob `#task` lines. Use as a behavior reference, not as a dependency. |

---

## Is this a good idea?

Yes. The alternative — Keep as a forever-inbox, plus a Google Doc overflow, plus a freshness nag — is already failing in this vault (`gkeep_gdocs_inbox_dump` is `wip`). Automating the drain is the correct GTD move: capture stays frictionless on the phone; processing happens in Obsidian with the rest of Bob’s task machinery.

The idea is *only* good if archive is gated on a parse-verified vault write and if pinned/shared/media notes are not silently eaten. A naive “download everything on `#home` and flip archived=true” will eventually delete a pinned reference note from the phone home screen and duplicate it in the vault on the next crash. The protocol above is what makes the product trustworthy.

Risks to accept with eyes open:

- **Unofficial API.** gkeepapi 0.17.1 is maintained (releases Nov 2025 and Jan 2026) and still has open auth issues (`LoginException: Unknown` / `BadAuthentication`). A Google-side change can break pull until gkeepapi catches up. Mitigation: `keep-cli backup` before archive; `--no-archive` / `--dry-run`; never delete, only archive.
- **Master tokens are powerful.** Store them only in the OS keyring via keep-cli. Never log them. Never put them in the vault.
- **Full-tree sync latency.** First authenticate can be slow on a large Keep account. Cache dump/restore.
- **Reminders and blobs.** Incomplete in gkeepapi. Prefer leaving those notes on Keep home over a lossy archive.

---

## Recommended solution

Ship **`bob gkeep`** as a nested native command in bob-cli, modeled on `bob projects` / `bob highlights`.

1. **Transport:** subprocess to existing `keep-cli --json`. Freeze and slightly extend that JSON. Do not use `keep.googleapis.com`.
2. **Read path:** `bob gkeep list` shows Keep home and/or `gkeep_inbox.md` open tasks in a colored table, JSON available. Default `--source all`.
3. **Write path:** `bob gkeep pull` (alias `migrate`) plans, atomically writes Bob `#task` lines under `gkeep_inbox.md`’s `## Tasks`, parse-verifies `^gk-<keep-id>` identities, then archives each verified note with `keep-cli archive`. `--dry-run` is write-safe. `--limit` caps a run. Pinned and shared notes are skipped by default.
4. **Vault:** promote `gkeep_inbox.md` to an area note; reuse `format_task_line` / `atomic_write` / `note_tasks`; `#gkeep` tag; Keep created date; list items as children; Keep URL child; images under `img/gkeep/`.
5. **Auth:** `bob gkeep auth …` wraps `keep-cli auth …`. Document the one-time master-token exchange.
6. **Ops:** runtime dependency on `keep-cli`; keep-cli cache dump; optional JSONL backup under XDG state before archive; no nightly hook in v1.
7. **Tests:** fake keep-cli, temp vault, golden task blocks, crash-between-write-and-archive replay proving idempotent archive-on-retry.

That is the smallest design that is intuitive (`pull` / `list` / `auth`), reliable (verify-then-archive, idempotent IDs), and beautiful (colored plan and two-pane list, Bob-native task lines, excellent `--help`).

### Implementation order

1. Freeze keep-cli JSON (collaborators, labels, cache). Auth must work on the real account before any vault writer is merged.
2. `bob gkeep list --source keep|vault|all` against that JSON and `gkeep_inbox.md` (read-only, shippable on its own).
3. `bob gkeep pull --dry-run` plan renderer, including skip reasons.
4. Vault writer + parse-back tests.
5. Archive step + retry-already-imported path.
6. Area-note frontmatter migration for `gkeep_inbox.md`, docs, README runtime-deps, `cli_rules` help polish.

Step 2 is immediately useful: it replaces opening keep.google.com and the vault side-by-side. Ship it first.

---

## Sources

- Local vault: `~/bob/gkeep_inbox.md`, `legacy_gkeep_notes.md`, `gkeep_gdocs_inbox_dump.md`, `mac_inbox.md`, `inbox.md`; `~/org/gkeep_inbox.zo`
- Local Keep client: `~/lib/keep_cli/main.py`, `~/lib/keep_cli/requirements.txt`, `~/bin/keep-cli`
- bob-cli: `src/runner.rs`, `src/native.rs`, `src/native/capture.rs` (`format_task_line`, `INBOX_FILE`), `src/native/capture_targets.rs`, `src/native/projects.rs`, `src/native/highlights_ref/mod.rs`, `src/native/collect_done.rs` (`atomic_write`, `is_block_id_byte`), `src/native/nightly.rs`, `src/native/style.rs`, `Cargo.toml`, `README.md` runtime dependencies, `sase/memory/cli_rules.md`
- gkeepapi 0.17.1 source (opened as `gh:kiwiz/gkeepapi`): `src/gkeepapi/__init__.py` (`API_URL`, `find`, `authenticate`, `sync`, `_sync_notes`), `src/gkeepapi/node.py` (`archived`, `url`)
- [Google Keep API overview](https://developers.google.com/workspace/keep/api/guides) (2026-09-03)
- [REST notes resource](https://developers.google.com/workspace/keep/api/reference/rest/v1/notes) — methods `create|delete|get|list` only
- [notes.list](https://developers.google.com/workspace/keep/api/reference/rest/v1/notes/list) — filter fields `createTime`, `updateTime`, `trashTime`, `trashed`
- [Issue 210500028](https://issuetracker.google.com/210500028) — consumer OAuth won’t-fix
- [gkeepapi docs](https://gkeepapi.readthedocs.io/en/latest/)
- [keep-it-markdown](https://github.com/djsudduth/keep-it-markdown) `-m` archive-after-export
- [Obsidian import from Google Keep](https://obsidian.md/help/import/google-keep)
- [KeepSydian](https://github.com/lc0rp/KeepSydian) two-way plugin (rejected as the implementation)
