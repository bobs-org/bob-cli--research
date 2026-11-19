# Research: `bob bank import -D|--delete` and Running `~/Downloads/*.qfx` from Bob Command Mode

**Question:** How should we design and implement a `-D|--delete` option on `bob bank import` so `bank import -D ~/Downloads/*.qfx` can be run from Obsidian's **Bob Command Mode** cleanly, reliably, and safely—and how should the plan itself be critiqued or refined?

---

## Executive Summary

The underlying workflow goal is strongly justified: `docs/guides/acknowledge-bank-transactions.md` currently prescribes running `bob bank import ~/Downloads/*.qfx && rm ~/Downloads/*.qfx` in a terminal because Wells Fargo QFX exports contain raw account identifiers (`<ACCTID>` / `<BANKID>`). Replacing `&& rm` with a built-in `-D|--delete` flag removes the need to drop out of Obsidian into a terminal and prevents leftover financial exports from lingering in `~/Downloads`.

**However, implementing `-D|--delete` alone will not let `bank import -D ~/Downloads/*.qfx` work in Bob Command Mode.** Inspecting both `bob-cli` and `bob-plugins` reveals a foundational gap:

1. **Command Mode spawns `bob` directly with no shell** (`bob-command-mode/src/060-runner.js`), passing `"~/Downloads/*.qfx"` as a single literal word in `argv`.
2. **`bob bank import` does neither tilde (`~`) expansion nor glob (`*.qfx`) expansion** (`src/native/bank/cli.rs`, `import_run.rs`), unlike `bob attachments import` (which calls `bob_env::expand_tilde`) or `bob gcal/gmail login` (which scan `~/Downloads`).
3. **Several cross-repo seams already exist half-wired or mismatched**: `bank-import` is `Policy::PreviewFirst` in `bob __catalog`, `bob-ledger-tools` already listens for `invalidates: ["bank"]` even though `src/native/catalog/table.rs` does not emit `"bank"` yet, and `bob __complete` emits `!files` which Command Mode maps to *vault notes* rather than host filesystem files.

**Recommended solution:** Implement path + glob resolution *inside* `bob bank import` (exact-path-first, sorted, deduplicated, zero-match refusal), add `-D|--delete` with pre-delete SHA-256 TOCTOU verification and non-destructive `-d/--dry-run` preview listing, keep deletion strictly post-commit without rolling back committed vault data on unlink errors, and pair it with catalog/adapter polish (`invalidates: &["bank"]`, `cmAdapterBankImport`, and optional Command Mode host-file completion).

---

## 1. Current Codebase Reality

### 1.1 `bob bank import` (`bob-cli`)

`bob bank import` (`src/native/bank/cli.rs`, `import_run.rs`, `import_plan.rs`, `source.rs`) is already built around a strict whole-batch transactional pipeline:

1. **CLI parsing (`build_cli_import`, `execute_import` in `src/native/bank/cli.rs`)**:
   - Options today are `-a/--account`, `-b/--bob-dir`, `-d/--dry-run`, `-F/--force`, `-f/--format`, `-h/--help`.
   - `--bob-dir` passes through `bob_env::expand_tilde(&path)`, whereas positional `[FILE]...` entries are converted via `PathBuf::from` without `expand_tilde` or glob expansion.
   - Omitting `[FILE]...` without `-F` fails early via `missing_files_failure()` (code `bank_import_missing_files`, exit `2`).
2. **Pre-lock parsing (`prepare_sources` in `src/native/bank/import_run.rs`)**:
   - Reads and parses every file (`source::parse_export`) *before* acquiring `bob_sync.lock`, running Git, or syncing.
   - Computes `file_digest = sha256_hex(bytes)` (`src/native/bank/source.rs`).
   - Supports QFX/OFX (`SourceKind::Ofx`) and Wells Fargo 5-column CSV (`SourceKind::Csv`). Empty valid OFX statements are accepted as balance/coverage evidence.
   - Any I/O or parse failure refuses the entire batch with exit `2` (`bank_import_source`).
3. **Planning & Guarded Apply (`plan_import`, `apply_with_restore` in `import_run.rs`; `run_locked` in `src/native/host_catalog/txn.rs`)**:
   - Under `bob_sync.lock`, `run_locked` verifies vault identity, checks Git worktree status, runs pre-sync, plans fresh against the synced snapshot (`plan_batch`), verifies `.bob/bank/<host>.jsonl` is not `.gitignore`d, writes staged month files, appends journal events, verifies byte post-images, and creates one scoped commit (`bank: import N rows (<alias>)`).
   - Identical replays (`new_evidence: false`, no edits, no events) return `commit: None` and skip post-sync with exit `0`.
   - **Important `sync_post` nuance:** If `apply_and_commit` succeeds locally and post-sync fails, `run_locked` keeps the local commit, sets `sync_post: "failed"`, adds a `warnings` entry, and returns `Ok(...)` (`failure: None`, exit `0`), tested in `post_sync_failure_keeps_the_local_commit_and_journal`.
4. **Account status & human/JSON output (`refresh_accounts`, `print_human`, `ImportReport::to_json`)**:
   - Exit codes (`ImportReport::exit_code`): `0` on success (including `sync_post == "failed"`), `2` on `bank_import_*` refusals or `stale_note`, `1` on runtime/lock/sync/verify failures.
   - `print_human` currently uses `Styler` minimally (`✗` red error, dim hint, dim dry-run banner); most of the summary is plain uncolored text, unlike `bob attachments import` (`src/native/attachments/cli.rs`) or `bob bank list` (`src/native/bank/output.rs`).

### 1.2 Bob Command Mode & Ledger Tools (`bob-plugins`)

Inspecting `bob-plugins/plugins/bob-command-mode/` and `bob-plugins/plugins/bob-ledger-tools/` exposes how `bank import -D ~/Downloads/*.qfx` will behave inside Obsidian:

- **Catalog entry (`src/native/catalog/table.rs`):** `bank-import` is configured as:
  - `effect: Effect::Writes`, `presentation: Presentation::Action`, `policy: Policy::PreviewFirst`, `preview: Some(&["--dry-run"])`, `budget_secs: 60`.
  - `fixed: &[]` (human output, not `-f json`, so previews and logs render nicely in the pager with `CLICOLOR_FORCE=1`).
  - `adapter: None`, `invalidates: &[]`.
- **No-shell execution (`060-runner.js`, `175-args-vim.js`):**
  - `cmTokenizeBobArgv` splits `bank import -D ~/Downloads/*.qfx` into `["bank", "import", "-D", "~/Downloads/*.qfx"]`.
  - `spawnRun` executes `child_process.spawn(bobPath, spawnArgs, { cwd: vaultBase, detached: true, ... })` with `shell: false`. No `~` or `*` expansion occurs.
- **Preview-first flow (`170-sheet.js`):**
  - Pressing `Enter` on a typed `bank import -D ~/Downloads/*.qfx` row runs `bob bank import --dry-run -D ~/Downloads/*.qfx` and opens the output pager (`Import bank transactions · preview`) with an **Apply ⌃↵** button.
  - Pressing `Ctrl+Enter` runs the command directly (`skipGuards`), bypassing preview.
- **`RECENT` persistence (`160-sheet-rank.js`, `050-run-store.js`):**
  - The sheet keeps the last 4 distinct runs in `RECENT`. Because `bank-import` is `PreviewFirst`, re-activating an applied `RECENT` row with `Enter` still triggers `--dry-run` preview before applying.
- **Cache invalidation gap (`table.rs` vs `283-plugin-command-mode-refresh.js`):**
  - `bob-ledger-tools` *already* handles `tag === "bank"` on `bob-command-mode:run-finished` by calling `this.apiBankInvalidate("command-mode")`, refreshing Bank Badges, Bank Period Charts, Bank Cards, and `]b` walk state.
  - Yet `KNOWN_INVALIDATES` in `src/native/catalog/table.rs` omits `"bank"`, and `bank-import` has `invalidates: &[]`.
- **Argument-mode completion mismatch (`175-args-vim.js`, `src/native/completion/kinds.rs`):**
  - `kinds.rs` sets `["bank", "import"]` `files` to `Kind::Files(None)` (`!files`), whereas sibling multi-format entries like `ref create` use `Kind::Files(Some("*.md *.pdf"))`.
  - Worse, `cmParseBobCompletion` in `175-args-vim.js` handles `!files` by calling `cmVaultPathCandidates(app)`—offering *vault notes* rather than host filesystem paths (`~/Downloads/*.qfx`)—and `cmGlobToRegExp` compiles multi-pattern globs like `"*.qfx *.ofx *.csv"` as a single literal pattern rather than splitting on whitespace like `bob.bash`.

---

## 2. Critique of the Original Plan

### Is this a good idea?

**Yes, as a capability; no, as a literal one-flag-only change.**

Why the core idea is strong:
- Eliminates `&& rm ~/Downloads/*.qfx` from the weekly manual ritual (`docs/guides/acknowledge-bank-transactions.md`), which is impossible to express in Command Mode's shell-free runner.
- Protects account numbers (`<ACCTID>` in QFX files) without forcing users to open a terminal just to run `rm`.
- Keeps `RECENT` in Command Mode reusable across weeks *if* the glob `~/Downloads/*.qfx` stays unexpanded in the recorded `argv` and is resolved at runtime by `bob`.

Where the naive plan breaks or needs sharpening:
1. **Literal `~/Downloads/*.qfx` fails immediately in Command Mode** unless `bob` (or a client wrapper) expands `~` and globs.
2. **Short flag `-D` has a mild semantic clash within `bob bank`:** `ack`, `ensure`, and `report` all use `-D, --day`, while `import` uses `-d, --dry-run`, `-f, --format`, `-F, --force`. On `import` specifically, `--day` makes no sense and lowercase `-d` is already taken by `--dry-run`, so `-D, --delete` follows `import`'s existing `-f`/`-F` case-pairing pattern and `bob`'s mandatory short-alias rule (`sase/memory/cli_rules.md`), matching `-D, --drawer` alongside `-d, --dry-run` on `capture` and `task merge`. Keeping `-D, --delete` is justified, though the asymmetry within `bob bank` should be documented clearly.
3. **"QFX files" is unnecessarily narrow:** `bob bank import` imports `.qfx`, `.ofx`, and Wells Fargo `.csv` identically. Only deleting `.qfx` while silently leaving `.ofx` or `.csv` behind in a `-D` batch violates least surprise.
4. **"iff all imports were successful" leaves 5 ambiguous boundary cases** (dry-run, already-seen replays, empty statements, post-sync failure vs local commit, and mid-run file modification or unlink failure) that must be nailed down explicitly before implementation.

---

## 3. Justified Adjustments to the Requirements

| # | Original Requirement / Assumption | Proposed Adjustment | Justification |
|---|---|---|---|
| **R1** | Pass `~/Downloads/*.qfx` from Command Mode assuming it works like a shell | **Expand `~` and globs (`*`, `?`, `[...]`) inside `bob bank import`** (exact-path-first, lexicographically sorted, canonicalized/deduped; exit 2 if 0 matches). | Command Mode spawns `bob` without a shell. Expanding in `bob` (not in JS) keeps non-path commands safe, works in scripts/LaunchAgents/bash/zsh alike, and keeps `~/Downloads/*.qfx` reusable in Command Mode `RECENT`. |
| **R2** | "the **QFX** files that are imported should be deleted" | **Delete all imported source files** passed to the batch (**QFX, OFX, and CSV**), not only `.qfx` extensions. | `bob bank import` accepts QFX, OFX, and Wells Fargo CSV uniformly (`docs/bank.md`). Leaving `.ofx` or `.csv` undeleted under `--delete` would be surprising. |
| **R3** | Implicit behavior when `FILE` is omitted or glob matches nothing | **Refuse with exit `2` when `-D` is passed with zero `FILE`s** (even with `-F`), **and when any glob matches zero files.** | Prevents silent false-success (`exit 0`) when the user runs `bob bank import -D -F` by mistake or when `~/Downloads/*.qfx` is empty / mis-typed. |
| **R4** | Unclear whether unchanged (`seen`) files count as "imported" | **Delete every validated source file when the batch exits `0`—including `seen` replays and valid empty statements.** | An idempotent replay of an already-journaled QFX succeeds (`ok: true`, exit `0`); leaving already-imported QFX files in `~/Downloads` defeats the cleanup goal. |
| **R5** | Interaction with `-d/--dry-run` and Command Mode `PreviewFirst` | **`-d -D` NEVER deletes files; it prints and returns the exact planned deletion list.** | `bank-import` is `Policy::PreviewFirst` in Command Mode: pressing `Enter` *always* runs `--dry-run` first. Showing `"Will delete after import"` in preview makes the `Ctrl+Enter` apply step transparent and safe. |
| **R6** | Unclear deletion mechanism (Trash vs `unlink`) and race safety | **Permanently unlink (`fs::remove_file`) after verifying each file's SHA-256 still matches `PreparedSource`'s digest.** | Moving to `~/.Trash` retains unencrypted `<ACCTID>` account numbers on disk (defeating the `&& rm` privacy rationale in `acknowledge-bank-transactions.md`). Pre-delete digest verification guards against deleting a file overwritten mid-import. |
| **R7** | Unclear handling of `sync_post` failure and `remove_file` failure | **Delete when the local commit succeeded even if `sync_post` warns; never roll back a committed import if `remove_file` fails—report per-file failures and exit `1` (`bank_import_delete_failed`).** | Once `apply_and_commit` succeeds, transactions are durable in Git and the journal. If cleanup fails afterward, exiting `1` (instead of `0` with a hidden warning) prevents Command Mode from dismissing a green `✓ Completed` toast while sensitive QFX files remain on disk. |

---

## 4. Alternative Approaches Considered

### Approach A: Minimal `-D|--delete` in `bob` only (no tilde/glob resolution)
- **Pros:** ~50 lines of Rust; zero path-matching complexity.
- **Cons:** Completely broken for the user's primary target (`bank import -D ~/Downloads/*.qfx` in Obsidian Command Mode).
- **Verdict:** **Reject.**

### Approach B: Expand `~` and globs in `bob-command-mode` (`bob-plugins`)
- **Pros:** Could theoretically apply to multiple commands.
- **Cons:**
  1. Violates Command Mode's architecture (`docs/command-catalog.md`: binary is source of truth; no shell semantics).
  2. Unsafe for non-path commands (`bob query "*foo*"`, `bob capture "buy 2*3 ~/note"`, `bob ref find`) because Command Mode does not know which args are host file globs vs text.
  3. Expanding `~/Downloads/*.qfx` before `spawnRun` persists concrete deleted paths (e.g. `Checking_2026-11-19.qfx`) in `RECENT`, breaking next week's one-click `RECENT` rerun.
- **Verdict:** **Reject.**

### Approach C: Implicit `~/Downloads` discovery (`--downloads` flag or dedicated catalog preset)
- **Pros:** Zero typing on first use (`Import Downloads QFX & delete`); eligible for Command Palette if args are absent.
- **Cons:**
  1. Overloading bare `bob bank import` to scan `~/Downloads` breaks `missing_files_is_refused_input` (`exit 2`, `docs/bank.md`).
  2. Implicitly scanning and deleting files the user did not name—even outside `~/Downloads/*.qfx`—is less transparent than explicit `~/Downloads/*.qfx` (which matches every doc example in `docs/bank.md`, `output.rs`, and `bob-ledger-tools`).
- **Verdict:** **Defer / keep optional.** Solve `bank import -D ~/Downloads/*.qfx` cleanly first; a future `bank-import-downloads` catalog row with `fixed: ["-D", "~/Downloads/*.qfx"]` (under `Policy::PreviewFirst`) can trivially layer on top if desired without changing CLI semantics.

### Approach D: Recommended Solution (`bob`-owned path/glob resolution + `-D|--delete` + Command Mode integration)
- Solves the exact user prompt end-to-end, respects both `bob-cli` and `bob-command-mode` boundaries, preserves `RECENT` reusability, and improves both terminal and Obsidian UX.

---

## 5. Recommended Solution Design

### 5.1 CLI Contract (`src/native/bank/cli.rs`)

Add `-D, --delete` to `build_cli_import()` in alphabetical long-option order (between `-b, --bob-dir` and `-d, --dry-run`, matching `tests/cli/help_options.rs` conventions):

```rust
fn delete_arg() -> Arg {
    Arg::new("delete")
        .long("delete")
        .short('D')
        .action(ArgAction::SetTrue)
        .help("Delete imported source files after a successful import")
}
```

- Update `build_cli_import().long_about(...)` and `.after_help(...)` to document:
  - `-D, --delete` deletes every source file after a successful apply (or confirmed already-seen replay).
  - `-d, --dry-run` previews which files would be deleted without modifying or deleting any files.
  - Refused or failed batches never delete any source files.
  - Add example: `bob bank import -D ~/Downloads/*.qfx`.
- Guard in `execute_import`: if `paths.is_empty()` when `delete` is true (even if `-F` is set), refuse with exit `2` (`bank_import_missing_files` or `"pass at least one FILE with -D/--delete"`).

### 5.2 Tilde & Glob Resolution (`src/native/bank/source_paths.rs` or `import_run.rs`)

Resolve `[FILE]...` before `prepare_sources`:

```rust
pub(crate) struct ResolvedSourcePath {
    /// Human-friendly display label (e.g. `~/Downloads/Checking1.qfx` via
    /// `attachments::journal::display_for_source` or shared `env` helper).
    pub(crate) label: String,
    /// Path to read and (if `-D` succeeds) verify + remove.
    pub(crate) path: PathBuf,
    /// Canonical identity for batch-wide deduplication.
    pub(crate) canonical: PathBuf,
}
```

Resolution algorithm for each raw `OsString` argument:
1. **Tilde expansion:** `let expanded = bob_env::expand_tilde(Path::new(raw));`
2. **Exact-path-first check:** Call `fs::symlink_metadata(&expanded)`:
   - If present and a directory: return `SourceError` (exit `2`: `"is a directory; pass QFX, OFX, or CSV files"`).
   - If present (file or symlink): accept literally—even if the filename contains `[`, `?`, or `*`!
   - If `NotFound`:
     - If `expanded` contains unescaped glob metacharacters (`*`, `?`, `[`): expand the pattern against the filesystem:
       - Support `*`, `?`, `[abc]`/`[!abc]`/`[a-z]` per path component; skip hidden entries (leading `.`) unless the pattern component starts with `.` (matching standard POSIX globbing).
       - Skip directories; include regular files (and symlinks to regular files).
       - Sort matches deterministically (lexicographically by path).
       - If 0 matches: return `SourceError` (exit `2`: `"no files matched {display}"`, hint `"Download a QFX, OFX, or CSV export and retry."`).
     - Otherwise: let `fs::read` fail with `SourceError` (exit `2`: `"could not read source: No such file or directory"`).
3. **Deduplicate across the batch:** Key by `fs::canonicalize(&path)` (falling back to normalized `path` if canonicalization fails), preserving first-seen order. This ensures `bob bank import -D ~/Downloads/*.qfx ~/Downloads/Checking1.qfx` neither double-parses nor fails deleting the second reference.

*Implementation choice — zero-dep matcher vs `glob` crate:* `Cargo.toml` currently has no `glob` dependency. Either adding `glob = "0.3"` (well-tested, standard, ~1 file) or writing a small ~90-line path-component globber in `src/native/bank/` works; `glob = "0.3"` avoids edge-case bugs in bracket classes and `**` if desired, while a focused component matcher avoids adding a new crate dependency for a feature whose core cases are `dir/*.qfx`. Either way, keep the resolver behind one small pure helper so `bob attachments import` can share it later if desired.

### 5.3 Execution & Reliability Lifecycle

```mermaid
flowchart TD
    A["1. Resolve & Deduplicate FILEs (~, globs)"] -->|0 matches / dir / -D without FILE| ERR2["Exit 2 · Nothing written or deleted"]
    A -->|Resolved paths| B["2. prepare_sources (read, parse, SHA-256 digest)"]
    B -->|Parse / I/O error| ERR2
    B -->|Dry run (-d)| PRE["Plan on snapshot · List 'Will delete' · Exit 0/2 · NO delete"]
    B -->|Apply| C["3. run_locked: lock -> worktree -> pre-sync -> plan_batch -> .gitignore -> write & commit -> post-sync"]
    C -->|Any TxnFailure (lock, sync_pre, conflict, stale_note, verify, commit)| ERR12["Exit 1/2 · Print 'No source files were deleted.'"]
    C -->|Ok (including sync_post failed warning)| D{"-D/--delete set?"}
    D -->|No| OK0["Exit 0"]
    D -->|Yes| E["4. For each unique source: verify SHA-256 == PreparedSource.digest, then fs::remove_file"]
    E -->|All deleted| OK0
    E -->|Any changed or unlink failed| DELERR["Keep commit intact · Report per-file status · Exit 1 (bank_import_delete_failed)"]
```

**Key safety properties:**
- **No partial import on bad glob:** If `~/Downloads/*` accidentally matches `notes.txt` alongside `Checking1.qfx`, `prepare_sources` rejects `notes.txt` in Step 2 before lock/sync/write/delete—neither vault nor Downloads changes.
- **No TOCTOU data loss:** `PreparedSource` stores `file_digest = statement.file_digest.clone()`. Before calling `fs::remove_file`, Step 4 re-reads the file and compares `sha256_hex(&current_bytes) == expected_digest` (failing that file with `"file changed on disk after import; left untouched"` if they differ).
- **Symlink honesty:** If an explicit path is a symlink to a file, `fs::remove_file` removes only the symlink (not its target); checking `symlink_metadata` vs `canonicalize` cleanly supports both without unexpected target deletion, and deduplication uses `(parent_dir, file_name)` or canonical path carefully so two symlinks to different places vs two spellings of one path behave predictably.
- **No rollback of committed data:** Step 4 runs strictly *after* `run_locked` returns `Ok`. A failed unlink never touches Git or `.bob/bank/<host>.jsonl`.

### 5.4 Beautiful Human Output & Additive JSON Contract

#### Human output (`src/native/bank/import_run.rs::print_human`)

Keep non-`-D` runs byte-identical if desired (or lightly polish with `Styler`), and make `-D` output immediately scannable in both terminal and Obsidian Command Mode's ANSI-themed pager:

1. **Dry run (`-d -D`):**
   ```text
   Dry run — nothing written
   ~/Downloads/Checking1.qfx · checking · 2026-11-01–2026-11-14
     New 9 · matched 23 · seen 41 · ambiguous 0 · before start 4
     Out $1,204.33 · In +$2,500.00
     Ledger balance $12,345.67 on 2026-11-14
   Accounts:
     WF Checking · ✓ balanced · through 2026-11-14
   Affected: .bob/bank/athena.jsonl, bank/2026-11.md
   <unified diffs>
   Will delete after import (1 file):
     - ~/Downloads/Checking1.qfx
   Next: file the 9 waiting rows in bank/2026-11.md — ]b walks them oldest first, Ctrl+Enter files each (or bob bank to list them).
   ```
   - Style `"Will delete after import (N files):"` with `styler.yellow(...)` so it stands out clearly on the preview screen before the user presses `Ctrl+Enter`.
   - If a file had `new_evidence == false` and all transactions `seen`, append dim `" (already imported)"` next to its path so the user knows why an unchanged import will still clean up the file.

2. **Successful Apply (`-D`):**
   - For 1 file: `✓ Deleted ~/Downloads/Checking1.qfx` (`✓` in `styler.green`, path clean).
   - For multiple files:
     ```text
     Deleted 2 source files:
       ✓ ~/Downloads/Checking1.qfx
       ✓ ~/Downloads/Savings1.qfx
     ```
   - Use `~/` home-shortened display labels (sharing `display_for_source` semantics from `src/native/attachments/journal.rs`) so `/Users/bryan/Downloads/...` stays readable.

3. **Import Failed / Refused with `-D`:**
   - Append one dim stderr line after the error + hint:
     `  No source files were deleted.`

4. **Import Committed, Deletion Partially Failed (`bank_import_delete_failed`, exit `1`):**
   - Print the full commit + sync summary on stdout *and* list each deletion outcome (`✓ ...` green for deleted, `✗ ...: <reason>` red for remaining files), then emit stderr:
     `✗ bob bank import: committed import, but failed to delete 1 source file`
     `  Remove the remaining file(s) manually; they may contain your account number.`

#### Additive JSON (`schema_version: 1`)

Add to `ImportReport::to_json()`:
```json
{
  "delete": true,
  "deletions": [
    {
      "file": "~/Downloads/Checking1.qfx",
      "path": "/Users/bryan/Downloads/Checking1.qfx",
      "status": "planned | deleted | failed",
      "error": null
    }
  ]
}
```
When `-D` is omitted: `"delete": false, "deletions": []`. When deletion fails after commit, keep `"ok": false`, `"commit": { ... }`, `"files": [ ... ]`, `"deletions": [ ... ]`, and `"error": { "code": "bank_import_delete_failed", "message": "...", "hint": "..." }`, returning exit `1`. (Note: file paths do not reveal bank account numbers or transaction identifiers, preserving the journal/diagnostics privacy contract in `docs/bank.md`.)

### 5.5 Obsidian Command Mode & Ledger Tools Integration (`bob-cli` + `bob-plugins`)

1. **Catalog refresh & adapter (`src/native/catalog/table.rs`):**
   - Add `"bank"` to `KNOWN_INVALIDATES` in `src/native/catalog/table.rs`.
   - Set `invalidates: &["bank"]` on `bank-import` (and consider doing the same for `bank-ack` and `bank-ensure`). This immediately lights up `bob-ledger-tools`'s existing `refreshBankForCommandModeRun()` listener in `283-plugin-command-mode-refresh.js`.
   - Set `adapter: Some("bank-import")` on `bank-import`.
2. **Outcome adapter (`bob-plugins/plugins/bob-command-mode/src/130-adapters.js`):**
   Add `cmAdapterBankImport(run, text)`:
   - **Post-sync failed (`Sync:.*post failed`)**: classify as `outcome: "attention"` (instead of hiding it behind a 5 s green toast!) with summary e.g. `"Imported 9 rows · post-sync failed (run vault-sync)"`.
   - **Deletion failed (`exitCode === 1` + `failed to delete`)**: `outcome: "failed"` (sticky toast until dismissed) summarizing both the committed rows and the remaining file(s).
   - **Zero-match glob (`no files matched`)**: `outcome: "attention"` (`"No files matched ~/Downloads/*.qfx"`), calmer amber card instead of red error.
   - **Success (`exitCode === 0`)**: parse counts + deleted count into a crisp toast, e.g. `"Imported 9 rows (23 matched) · deleted 2 files"` or `"Bank already up to date · deleted 1 file"`, plus an `"Open bank/YYYY-MM.md"` action button (`open-vault-note`) when the output names a bank month note.
3. **Completion improvements (`src/native/completion/kinds.rs` + `bob-command-mode/src/175-args-vim.js`):**
   - Update `kinds.rs` for `&["bank", "import"]` `arg: "files"` from `Kind::Files(None)` to `Kind::Files(Some("*.qfx *.ofx *.csv"))` so zsh/bash Tab completion filters bank exports.
   - *(Recommended Command Mode enhancement)*: Fix `175-args-vim.js` (`cmParseBobCompletion` / `cmGlobToRegExp`) so `!files` does not falsely list Obsidian vault Markdown files when the user is in `bank import` argument mode or typing a host path (`~/`, `/`, `./`). Offering local filesystem completions (and e.g. `~/Downloads/*.qfx` when matching `.qfx` files exist in `~/Downloads`) makes `bank import` -> `Tab` in Command Mode genuinely usable.
4. **Docs & UI hints:**
   - Update `docs/bank.md`, `docs/reference/cli/bank.md` (`just docs-gen`), `docs/guides/acknowledge-bank-transactions.md`, `src/native/bank/output.rs`, and `bob-ledger-tools/src/241m-plugin-bank-cards.js` to show `bob bank import -D ~/Downloads/*.qfx` where `&& rm` or `bob bank import` was shown.

---

## 6. Verification Plan

If implemented, verify across both repositories:
1. **`bob-cli` unit & CLI integration tests (`src/native/bank/import_run.rs`, `src/native/bank/tests.rs`, `tests/cli/bank.rs`, `tests/cli/help_options.rs`, `tests/cli/catalog.rs`, `tests/cli/docs_reference.rs`):**
   - Help option ordering (`-a`, `-b`, `-D`, `-d`, `-F`, `-f`, `-h`) and `-D` without `FILE` (including `-D -F`) exiting `2`.
   - Tilde + glob expansion (`~/Downloads/*.qfx`), exact-path-first with literal `[1]` filenames, directory rejection, deduplication across overlapping patterns, zero-match glob exiting `2` before lock/sync.
   - `-d -D` dry-run never deletes files and lists planned deletions in human + JSON output.
   - Failed parse / identity conflict / lock busy / `.gitignore` refusal / `stale_note` deletes zero files and prints `"No source files were deleted."`.
   - Successful single-file, multi-file, mixed QFX/CSV, `seen`-replay, and `sync_post == "failed"` imports delete all verified files.
   - TOCTOU digest mismatch refuses deletion of the modified file without rolling back the commit; unlink failure (`chmod` read-only parent dir) leaves commit intact, deletes other files, reports per-file status, and exits `1` with `bank_import_delete_failed`.
   - `just check` passes cleanly.
2. **`bob-plugins` tests (`scripts/test-command-mode-*.cjs`, `scripts/test-ledger-tools-command-mode-refresh.cjs`):**
   - Test `cmAdapterBankImport` outcomes (clean import + delete, `sync_post` failed -> `attention`, zero-match -> `attention`, partial delete failure -> sticky `failed`).
   - Test `invalidates: ["bank"]` triggers `apiBankInvalidate`.
   - `npm test` and `npm run validate` pass, followed by `bob plugins sync`.
