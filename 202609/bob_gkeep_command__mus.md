# `bob gkeep`: design research — Keep inbox → Obsidian tasks

Researcher: **mus** · 2026-09-28 · swarm report (`__mus`)

Goal: help decide the best way to implement a new `bob gkeep` command that
(1) migrates Google Keep inbox items (the `#home` view at
https://keep.google.com/#home) into Obsidian tasks in `~/bob/gkeep_inbox.md`,
(2) archives migrated items in Keep once migration is verified, and
(3) lists items in Keep and/or in `gkeep_inbox.md` — intuitively, reliably,
and beautifully.

## 1. Starting context in this repo and vault

Facts observed directly in the workspace and vault (not assumptions):

- `bob-cli` is a Rust CLI (`clap` 4.5). Top-level commands are declared in a
  sorted table in `src/runner.rs`; each native command parses its own args
  with `clap` (see `src/native/vault_sync.rs`, `src/native/dataview.rs`).
  A new `bob gkeep` would follow this established pattern: one table entry
  plus a `src/native/gkeep*.rs` module with subcommands.
- House CLI conventions that apply to any new command:
  - `sase/memory/cli_rules.md`: excellent `-h|--help`, sorted options, every
    public long option gets a short alias, colored output where it aids
    readability. Existing code has a `Styler` helper (`src/native/style.rs`)
    that respects `NO_COLOR`/TTY — reuse it.
  - Existing flags to mirror: `--bob-dir/-b` (defaults to `BOB_DIR` or
    `~/bob`, see `src/native/env.rs`), `--format/-f` (`human` default +
    `json` for scripting, as in `capture-tasks` and `query`), `--dry-run/-n`
    (as in `vault-sync run`), `--json/-j` status output (as in
    `vault-sync status`).
  - Good structural models: `bob vault-sync` (`run` + `status` subcommands,
    lock-protected cycle, state JSON under
    `${XDG_STATE_HOME:-~/.local/state}/bob-cli/`) and `bob highlights`
    (`scan` preview vs `sync` mutate, plus a `doctor` prerequisites command).
    `gkeep` wants exactly this trio: preview, mutate, diagnose.
- `~/bob/gkeep_inbox.md` exists today and already anticipates this feature.
  Its body (after frontmatter) is currently:
  `- See [[legacy_gkeep_notes]] for old notes …`
  `- The tasks below are pulled in by the 'bob gkeep' command.`
  `## Tasks` (empty). Frontmatter says `generated_from_zorg: true` with a
  `zorg_source` pointer — so this file was previously produced from
  `~/org/gkeep_inbox.zo` by a `convert_zorg_core.py` pipeline, and there is a
  `~/bob/legacy_gkeep_notes.md` holding pre-zorg notes plus a `@FRESHNESS`
  reminder habit. Implication: the vault already treats this file as
  **machine-appended, human-triaged** — the new command should preserve that
  contract (append under `## Tasks`, never rewrite the header/prose).
- Task-format infrastructure already exists: `src/native/note_tasks.rs`
  parses `- [ ]` tasks with digests/refs, and `bob capture-tasks --route …`
  lists open tasks per note. `gkeep list --source vault` should reuse that
  parser rather than inventing a second task reader.

## 2. The hard truth: there is no usable official Keep API for this

This dominates the design. Findings from current external sources:

1. **Official Google Keep API is Workspace-enterprise-only.** It requires a
   paid Workspace account with domain-wide delegation by an admin and does
   not work for personal `@gmail.com` accounts. Unless the vault owner has a
   Workspace account holding these Keep notes (unlikely for a personal
   inbox), the official REST API is a dead end. Do not design around it as
   the primary path; at most, leave room for it as a future optional backend.
2. **The only "live inbox" path is the unofficial `gkeepapi` Python library**
   (kiwiz/gkeepapi), which speaks Keep's private sync protocol. It supports
   exactly what the requirements need: `find(pinned/archived/trashed)` for
   the `#home` inbox view and `archive()` for the archive-back step.
   Costs and risks:
   - Authentication is through `gpsoauth` master tokens, not standard OAuth.
     Multiple 2025 reports describe `BadAuthentication` failures and Google
     deprecating app-password flows for this endpoint; setup is a fiddly
     one-time browser/token exchange, and Google can break the private
     protocol at any time. This is the fragile point of the whole feature —
     not the markdown rendering.
   - Upstream maintenance is questionable (stale `kiwiz/gkeepapi`, community
     forks/MCP wrappers carrying fixes). Pinning to one commit/hash and
     isolating it behind a helper is mandatory.
   - `bob-cli` is Rust with a small dependency list; there is **no
     maintained Rust crate** for the Keep sync protocol. The realistic
     integration is shelling out to a Python helper (e.g. `uvx` or a
     vendored venv), which is a new runtime dependency and a new failure
     mode for a CLI that is otherwise self-contained and offline.
   - Credentials (master token) must live somewhere safe: OS keychain
     preferred, else a `0600` file under `XDG_STATE_HOME/bob-cli/`, never in
     the vault repo.
3. **Google Takeout export is the stable, sanctioned path** — one JSON file
   per note with `title`, `textContent`, `listContent` (checkbox items),
   `labels`, `color`, `isArchived`/`isTrashed`, and
   `createdTimestampUsec`/`userEditedTimestampUsec`, plus attachments.
   Prior community migrations (Keep→Obsidian) standardize on it. Limits: it
   is manual (request at takeout.google.com, wait minutes–hours), a
   point-in-time snapshot (not the "live #home view"), and one-way (it
   cannot list live state nor archive notes back). It satisfies
   *migration* but not *list-live* nor *archive-back*.
4. Rejected: the "select-all → Copy to Google Docs → process" community
   workaround is manual and lossy — not automatable, not a CLI backend.

## 3. Critique of the plan as stated

**Is it a good idea? Yes — with the archive step treated as the dangerous
part, not an afterthought.** A single capture inbox (`gkeep_inbox.md`) that
is machine-filled and human-triaged matches the existing vault habit
(`@FRESHNESS` reminder, `## Tasks` section, `capture-tasks` listing). Killing
Keep↔Obsidian double-entry is genuinely valuable. But several requirements
need tightening before implementation:

1. **"All of my current Google Keep inbox items" is ambiguous.** The `#home`
   view mixes: plain notes, checklists, pinned notes, notes with reminders,
   labeled notes, notes with images/audio, archived-but-untrashed notes.
   Specify: default = non-pinned, non-archived, non-trashed (mirrors
   `gkeepapi`'s `find` filters); add `--include-pinned`,
   `--include-archived`, `--label` filters. Decide: do completed checklist
   items migrate as `- [x]` or get dropped? (Recommend: migrate as checked
   tasks — preserves information, triager can delete.)
2. **"Archived once we are sure the migration was successful" is the
   riskiest sentence in the request.** "Sure" must be defined in code as a
   two-phase commit: (a) append tasks, (b) re-read and re-parse the file
   with the repo's own `note_tasks` parser and confirm every migrated Keep
   ID is present, (c) write a manifest (Keep IDs ↔ task digests ↔ timestamps)
   to the state dir, (d) only then call archive, (e) report per-note
   archive results. Never archive from the in-memory render — archive from
   the verified file contents.
3. **One command listing two different systems ("Keep and/or vault") risks
   confusion.** Keep it, but make the source explicit every time:
   `--source keep|vault|both` (default `both` for humans, with clear section
   headers; `json` output namespaces `keep:` vs `vault:`). Reuse the
   `note_tasks` parser for the vault side so "list vault" and "list Keep"
   share task semantics.
4. **Idempotency is a requirement, not a nice-to-have.** Re-running migrate
   must not duplicate tasks. Embed the Keep note ID in each migrated task
   (e.g. an inline field like `[keep_id::abc123]` plus a stable block ID
   such as `^keep-<short-hash>`) and scan for existing IDs before appending.
5. **The beauty requirement is real but bounded.** In this codebase "beautiful"
   means: sorted options, great `--help` with examples, colored human output
   via `Styler`, quiet-by-default mutations with a one-line `ok …` summary,
   and `--format json` for scripting — not a TUI. Aim at
   `vault-sync`/`highlights` polish, not a new interaction paradigm.
6. **Biggest unspoken cost: auth UX.** The token setup, storage, rotation,
   and `doctor` diagnostics will be more code and more support burden than
   the migration logic. Budget for it explicitly.

## 4. Adjustments to the requirements (proposed, sign-off needed)

- A1. Split the command into four subcommands: `list`, `migrate`, `import`
  (Takeout fallback), `doctor` — instead of one migrate + one list.
- A2. Make archiving **opt-in per run** (`--archive`), not automatic:
  first run migrates and prints a review checklist; second run with
  `--archive` verifies and archives. The request's "archive once sure"
  becomes a two-step habit instead of a flag-day auto-archive.
- A3. Default `migrate` to `--dry-run` preview when stdout is a TTY? No —
  stay consistent with `vault-sync` (`--dry-run/-n` opt-in). Instead, require
  verification to pass before `--archive` is honored, and always write the
  manifest regardless.
- A4. Add a machine contract from day one: `--format json` on `list` and
  `migrate`, stable exit codes (0 ok, 1 error, 2 usage), manifest JSON in
  the state dir. The macOS capture frontend and future agents will thank us.
- A5. Attachments (images/audio) are out of scope for v1: migrate a
  placeholder child line (`[attachment: photo.jpg — see Keep note <id>]`)
  and warn; do not attempt binary download in v1.

## 5. Recommended solution

**Architecture: native Rust `bob gkeep` frontend, pluggable Keep source,
Takeout-first delivery, live sync as an isolated opt-in helper.**

- `bob gkeep list [--source keep|vault|both] [--include-archived]
  [--include-pinned] [--label T] [--format human|json]`
  Read-only. Vault side reuses `note_tasks`; Keep side calls the helper.
  Human output groups pinned → inbox, colored via `Styler`, with counts.
- `bob gkeep migrate [--dry-run/-n] [--archive] [--no-archive]
  [--limit N] [--label T] [--format human|json]`
  Two-phase: fetch → render → idempotency scan → append under `## Tasks`
  (creating the section if missing, never touching header prose) → re-parse
  and verify → write manifest to
  `~/.local/state/bob-cli/gkeep-manifests/<timestamp>.json` → archive only
  with `--archive` and only the verified set → print `ok N tasks →
  gkeep_inbox.md, M archived` (or `[dry-run] ok …` preview). Archiving is
  never the default.
- `bob gkeep import --from <Takeout/Keep dir> [--dry-run] [--archive-never]`
  Same render/append/verify pipeline, source = Takeout JSON. This is the
  **v1 shippable core**: zero credentials, zero new runtime deps, works
  even if Google breaks the private protocol tomorrow.
- `bob gkeep doctor`
  Checks: helper present (`python3`/`uvx`, pinned `gkeepapi`), token
  reachable (keychain/state file, `0600`), vault file writable, Takeout dir
  parseable. Exit non-zero with actionable hints. Model on
  `highlights doctor`.

**Keep-note → Obsidian-task mapping (v1):**

| Keep field | Obsidian rendering |
|---|---|
| title (if any) | bold prefix on the parent task line |
| `textContent` newlines | child bullet lines under the parent task |
| `listContent` items | `- [ ]` / `- [x]` children preserving check state |
| labels | `#tags` appended |
| reminder | `tick::YYYY-MM-DD` inline field |
| Keep note ID | `[keep_id::<id>]` inline field + `^keep-<shorthash>` block ID (idempotency keys) |
| color | dropped (or `keep_color::` field — vault owner's call) |
| attachments | placeholder child line + warning count |

**Live-sync helper (v2, opt-in):** a small vendored Python script invoked by
the Rust command (`keep.find(archived=False, trashed=False)` for list,
`note.archive()` after verification for migrate). Pin the `gkeepapi` commit,
document the master-token setup in `doctor` output and `--help`, store the
token in the OS keychain with a state-dir fallback. If auth rots (the known
2025 `BadAuthentication` class of failures), `doctor` says so plainly and
`import` keeps working — the feature degrades to Takeout instead of dying.

**Reliability checklist:** idempotency scan before every append; verify by
re-parsing the written file (not memory); manifest every run; `--limit`
for safe first runs; existing `note_tasks` digest refs for stable identity;
unit tests on mapping + idempotency with fixture Takeout JSON and fixture
helper JSON; integration tests against a temp `BOB_DIR`.

**Delivery order:** (1) `list --source vault` + `import` + render pipeline
(no credentials, immediately useful for the existing Takeout backlog);
(2) `migrate --archive` + manifest + verification; (3) live helper + `list
--source keep` + `doctor`. Each phase is independently shippable and demoable.

## 6. Bottom line

Build it — but build it as **Takeout import first, live Keep sync second,
archive-behind-verification always**. The requested three behaviors are all
implementable, yet only the unofficial protocol delivers "live list" and
"archive back," and that protocol is the fragile, credential-hungry part.
The phased design above gives a useful, beautiful, reliable tool at every
step and never lets a Keep API hiccup lose or duplicate a task.

*Sources consulted: workspace sources (`src/runner.rs`, `src/native/`,
`~/bob/gkeep_inbox.md`, `~/bob/legacy_gkeep_notes.md`, house CLI rules);
public docs and community reports on the Keep API's Workspace-only scope,
`gkeepapi`/`gpsoauth` auth behavior, and Takeout JSON format (see §2). No
peer swarm reports were consulted.*
