# `bob bank import -D`: clearing imported downloads from Downloads, safely, from command mode

**Date:** 2026-11-19 · **Researcher:** cld · **Evidence:** bob-cli at `e7aa392d` (`src/native/bank/{cli,import_run,import_plan,source,journal}.rs`,
`src/native/catalog/table.rs`, `src/runner.rs`, `docs/bank.md`, `docs/guides/acknowledge-bank-transactions.md`),
bob-plugins (`plugins/bob-command-mode/src/{060-runner,070-outcomes,175-args-vim}.js`,
`plugins/bob-ledger-tools/src/241m-plugin-bank-cards.js`), a live probe of the installed `bob 0.5.0`, and the
web sources listed at the end.

## TL;DR

- **Yes, build it.** The guide already tells you to run `bob bank import ~/Downloads/*.qfx && rm ~/Downloads/*.qfx`,
  because the QFX contains your full account number. `-D` moves that cleanup into bob. bob is the only component that
  knows which files it recorded, and the move fixes a small race in the `&&` idiom.
- **But the command you want to type does not work in command mode today, even without `-D`.** Command mode runs
  `bob` directly, without a shell, so `~/Downloads/*.qfx` reaches bob as a literal string. I ran the probe: bob reports
  `~/Downloads/*.qfx: could not read source: No such file or directory`, exit 2. **Adjustment 1 (required):** bob
  expands `~` and glob patterns in `bank import` FILE operands itself. It uses an operand as a literal path first, so
  shell behavior stays the same.
- **Adjustment 2 (recommended): `-D` moves files to the Trash** rather than unlinking them. "Delete" on the Mac means
  Move to Trash. Nothing else in bob destroys data permanently. The Trash still covers the privacy goal, because the
  file is gone from Downloads.
- **Adjustment 3: define "successful" precisely and check each file before removing it.** A file is moved to the
  Trash only if all of these hold:
  - The whole batch is recorded. That means it committed, or it was an identical replay that needed no commit. A
    post-sync failure still counts as recorded.
  - That file's SHA-256 appears in a `bank.import` journal event for its account.
  - The bytes on disk are still the bytes bob parsed.

  A refused or failed import keeps every file, and the output says so.
- **Adjustment 4: check up front that each file can be removed.** Before writing anything, bob confirms each file is a
  regular file outside the vault. That makes "deleted iff imported" hold in both directions, apart from a genuine I/O
  error at the very end. If that happens, bob prints a warning and exits 0. Re-running the import is a no-op that
  retries the cleanup.
- **Keep the spelling you asked for: `-D, --delete`.** `-D` already means `--day` in `bank ack|ensure|report`, but
  misuse fails safe: `bank import -D yesterday` reads `yesterday` as a FILE and refuses the batch.
- **The polished result:** one line, `🗑 Moved to the Trash from ~/Downloads: Checking1.qfx`. The command-mode preview
  shows `🗑 Would move…` first. Phase 2 makes the bank card's "Weekly import" line a one-click command-mode preview of
  `bank import -D ~/Downloads/*.qfx`.

## 1. What exists today

| Fact | Where | Why it matters for `-D` |
| --- | --- | --- |
| Every source is read and parsed **before** the lock or pre-sync. One malformed member refuses the whole batch, with no vault, journal, Git, or sync change. | `import_run::prepare_sources`, `docs/bank.md` § Import | The batch is already all-or-nothing, so `-D` can never delete a non-bank file. A stray PDF in the glob refuses the batch, and nothing is touched. |
| A successful apply is **one** guarded transaction: month rows plus journal, one scoped `bank: import N rows (alias)` commit. | `apply_with_restore`, `planned_txn` | "All imports succeeded" is one boolean, `report.failure.is_none()`, not N per-file verdicts. |
| An identical replay produces **no commit and no journal event**: `No changes; no import commit.` | `is_new_evidence`, docs § Journal | A replay is still a success: the file's evidence is already recorded. `-D` must clean it up. This is the common case of a re-download such as `Checking1 (1).qfx`. |
| A post-sync failure **keeps the local commit** and shows only a warning. | docs § Commit, preview, and replay | The data is durable in the local commit. That counts as success. |
| Every `bank.import` event stores `file_sha256` for the account. Bank IDs are hashed, description digits are masked, and raw paths are never written to the journal. | `source::parse_export` (`sha256_hex(bytes)`), `journal::ImportEvent` | This gives a per-file proof that the vault recorded these exact bytes. It also means deletions must **not** be journaled, because that would put host paths in the vault. |
| The guide's Monday ritual is `bob bank import ~/Downloads/*.qfx && rm ~/Downloads/*.qfx`: "the QFX holds the full account number, and `&&` never deletes after a refused import." | `docs/guides/acknowledge-bank-transactions.md` §1 | The stated purpose is privacy hygiene. `-D` codifies this documented ritual rather than inventing a new one. |
| Command mode **spawns `bob` with no shell** (`child_process.spawn(path, args, {cwd: vaultBase})`). Its tokenizer handles quotes and escapes only, with no `~` and no globbing. | `060-runner.js:294`, `175-args-vim.js` `cmTokenizeBobArgv` | **The requested invocation is broken today.** The probe is below. |
| The `bank-import` catalog row is `preview-first` with preview `["--dry-run"]`, and FILE is a repeatable `text` slot. | `catalog/table.rs` `bank-import` | In command mode, Enter runs `bank import --dry-run -D …` and Ctrl+Enter applies it. The dry run must show what would be removed. |
| Exit 0 renders as "completed", with the **last stdout line** as the toast summary. Catalog `exit_codes` hints can map a code to `attention`, but no row uses them yet. | `070-outcomes.js` | This shapes where cleanup warnings go (§4.6). |
| The bank queue card footer reads `Weekly import: bob bank import ~/Downloads/*.qfx`. bob-ledger-tools already opens command-mode previews through `api.commandMode.preview` (keep inbox). | `241m-plugin-bank-cards.js:604`, `295-keep-inbox-actions.js:457` | This is a ready-made spot for a one-click "Weekly import" (Phase 2). |
| `-D` is unused in `bank import` (`-a -b -d -F -f -h`). Elsewhere `-D` always takes a value: `--day` in 7 commands (including `bank ack/ensure/report`) and `--drawer` in 2 (`capture`, `task merge`). | `grep short('D')` | Cross-sibling inconsistency is minor and fails safe (§2). |

**The probe** (installed `bob 0.5.0`, scratch `BOB_DIR`, dry run). This is exactly what command mode would send:

```text
$ bob bank import -d '~/Downloads/*.qfx'
✗ bob bank import: ~/Downloads/*.qfx: could not read source: No such file or directory (os error 2)
  fix the source file and retry
exit=2
```

## 2. Critique: is this a good idea?

**Mostly yes. It is small, fits the existing design, and closes real gaps:**

1. **It codifies an existing, documented ritual.** You already delete these files on purpose, for a privacy reason.
   The open question was only who runs the delete, and whether it can be done from Obsidian.
2. **The `&& rm` idiom has a race and a reach problem that `-D` fixes.** `rm ~/Downloads/*.qfx` re-globs *after* the
   import. A second account's download that finishes during the import is deleted without ever being imported. `rm`
   also deletes by name. `-D` removes exactly the files it parsed, and only if their bytes are unchanged. This is the
   same rule as `rsync --remove-source-files`: remove only files that were transferred, and only quiescent ones.
3. **It is the established UX pattern for importers.** Examples: rsync's `--remove-source-files`, tar's
   `--remove-files`, zip `-m`, and Image Capture's "Delete after import". Beancount's `bean-file` *moves* imported
   downloads into an archive rather than deleting them (see §5).
4. **The all-or-nothing batch is the main safety feature, and bob already has it.** Because a single unparseable file
   refuses the whole batch, `-D ~/Downloads/*` cannot delete your tax PDF. It can only ever touch files bob parsed as
   bank exports.

**Where the plan as stated falls short:**

- **It does not work in the place you want to use it** (§1 probe). `-D` alone would ship a flag that command mode
  cannot use. Expanding operands is the actual enabling change. `-D` is the small part.
- **"Deleted" vs "trashed".** Unlinking would be bob's only irreversible destruction of user data. Every vault write is
  a revertible commit, and every bank refusal leaves things unchanged. A mistaken `-a`, or deciding you wanted the
  export for taxes, should be recoverable from the Trash.
- **"Iff all imports were successful" needs a precise definition.** A no-op replay must count as success, a
  post-sync failure must count as success, and dry runs must never delete. A single exit-code check is also weaker
  than a check of each file against the journal (§4.3).
- **Naming.** `-D` means `--day` in three `bank` siblings. I keep it anyway: it is the mnemonic you asked for, it is
  boolean here, and misuse fails safe. `bank import -D yesterday` refuses because it cannot read `yesterday` as a
  FILE, so nothing is written or deleted.

## 3. Adjustments to the requirements

| # | Adjustment | Status | Why |
| --- | --- | --- | --- |
| A1 | **bob expands `~` and glob patterns in `bank import` FILE operands.** A literal path is used first. | **Required** | Without it, `bank import -D ~/Downloads/*.qfx` cannot work in command mode (no shell). |
| A2 | **`-D` moves files to the OS Trash** (macOS Trash, freedesktop Trash on Linux) instead of unlinking. It never falls back to unlinking. | Recommended | Reversible. Matches Finder's meaning of "Delete". Still removes the account number from Downloads. Flipping to unlink later changes only the last step. |
| A3 | "Successful" means **the whole batch is recorded**: committed, *or* an identical replay with no commit. A post-sync failure counts. A dry run never deletes. | Clarification | The vault holds the evidence in all three cases. |
| A4 | **Each file is checked before removal:** its SHA-256 is in a `bank.import` event for its account (any host), *and* its on-disk identity and bytes are unchanged since bob read them. | Recommended | Removal rests on proof the vault recorded those bytes, not on an exit code. Protects against a file replaced mid-run. |
| A5 | **Pre-write check of each file:** every `-D` file must be a regular file (not a symlink or directory) outside the vault. Otherwise the batch is refused input, exit 2, before any write. | Recommended | Keeps the "iff" true in the other direction too: a successful import never leaves a file behind for a reason that was knowable beforehand. |
| A6 | `-D` **requires FILE**. A pattern set that expands to nothing is refused input, exit 2, with a teaching message. | Recommended | A typo such as `~/Download/*.qfx` should fail loudly, not "succeed". This matches the existing "no FILE is refused" rule. |
| A7 | A removal that fails *after* a successful import gives a **warning and exit 0**. The file is kept, and a re-run is a no-op that retries the removal. | Recommended | The exit code keeps meaning "what happened to the vault". The cleanup heals itself. |

## 4. Design

### 4.1 CLI surface

```text
bob bank import [FILE...] [-a ALIAS] [-b DIR] [-D] [-d] [-F] [-f human|json]
```

Options stay alphabetical, with uppercase before lowercase as in `-F`/`-f` today:

```text
Options:
  -a, --account <ALIAS>  Choose a configured importable account
  -b, --bob-dir <DIR>    Bob vault root; defaults to BOB_DIR or ~/bob
  -D, --delete           Move each FILE to the Trash once the whole batch is recorded
  -d, --dry-run          Preview diffs without writing
  -F, --force            Restore journaled transactions whose rows are missing
  -f, --format <FORMAT>  Output format: human or json [default: human] [possible values: human, json]
  -h, --help             Show help

Examples:
  bob bank import -D ~/Downloads/*.qfx
  bob bank import -d ~/Downloads/checking.qfx
  bob bank import -a checking -f json ~/Downloads/export.csv
  bob bank import -F
```

Sentence to add to `long_about`: *"FILE accepts `~` and glob patterns (`~/Downloads/*.qfx`), so callers without a
shell, such as command mode, can pass them. `-D` moves every FILE to the Trash only after the whole batch is
recorded, and only when the file is unchanged since bob read it. A refused or failed import keeps every file."*

clap: `Arg::new("delete").long("delete").short('D').action(SetTrue).requires("files")`.

### 4.2 Operand expansion (A1)

For each FILE operand, in order:

1. **If the operand exists as a path, use it literally.** This covers shell-expanded arguments and a file literally
   named `statement [1].qfx`, so shell users see no change.
2. Otherwise, expand a leading `~` or `~/` with the existing `bob_env::expand_tilde`. bob already does this for
   `ref create -o`, `attachments`, and audio paths.
3. If the result contains `*`, `?`, or `[`, glob it:
   - Regular files only.
   - A leading `.` must be matched literally.
   - Results are sorted, which keeps the planner's input-file order deterministic.
   - I suggest case-insensitive matching, so `*.qfx` also matches a bank's `*.QFX`. That is a deliberate,
     domain-specific choice and should be documented.

   Use the `glob` crate (rust-lang, no dependencies) or a final-path-component matcher built on `regex`, which bob
   already depends on.
4. A pattern that matches nothing contributes nothing. If **every** operand is empty, the run is refused with
   `bank_import_no_matches`: `no files match ~/Downloads/*.qfx`, hint `download a QFX/OFX export first, or check the
   pattern`. Exit 2.
5. Duplicate canonical paths are kept for the planner, which already handles repeats, but are removed **once**.

Put this in a small shared helper (for example `native::host_paths::expand_operands`). Command mode's lack of a shell
affects every host-file operand (`attachments import PATH`, `ref create FILE`, and so on), so those can adopt the
helper later. Expanding in bob rather than in the plugin matters for one more reason: **command mode stores the argv
it ran**, for RECENT, sequences, and replays. Plugin-side expansion would store last week's filenames, which `-D` has
since deleted. With bob-side expansion the stored argv keeps `~/Downloads/*.qfx`, so every replay re-expands it.

### 4.3 Lifecycle and the "iff" rule (A3–A5)

1. **Expand** operands (§4.2).
2. **Read and parse** every source, as today. Also capture each file's `(dev, inode, len, mtime)` from the open
   handle, and keep the original `PathBuf`, because `label` is lossy for non-UTF-8 paths.
3. **Check removability** (only with `-D`). Each file must be a regular file and must not canonicalize to a path
   inside the vault. A violation refuses with exit 2 (`bank_import_delete_unsupported`) before the lock, sync, or
   any write.
4. **Dry run:** plan as today, and attach `would_trash` for every file. Nothing is removed.
5. **Apply:** the unchanged transaction lifecycle (lock, pre-sync, plan, commit, post-sync).
6. **If `report.failure.is_none()`:** load the journal once and reuse it for `refresh_accounts`. Then, for each
   unique file:
   - Confirm a `bank.import` event exists with `account == resolved alias` and `file_sha256 == digest`.
   - Confirm `lstat` still matches the captured identity and a re-hash still equals the digest.
   - Then move the file to the Trash.

   Any file that fails these checks is **kept**, with a reason. The rsync manual's warning about non-quiescent files
   is what this step guards against.
7. **On any failure:** every file is kept, with reason `import_failed`.

| Outcome | Files | Exit |
| --- | --- | --- |
| Usage error; no FILE with `-D`; no matches | untouched | 2 |
| Unreadable or malformed source; account/plan refusal; `-D` removability refusal; ignored journal | all kept | 2 |
| Lock or pre-sync failure; pre-commit failure with rollback | all kept | 1 / 2 (as today) |
| Dry run | all kept, listed as "would move" | 0 |
| Committed, post-sync OK | trashed | 0 |
| Committed, **post-sync failed** | trashed (sync warning as today) | 0 |
| **Identical replay** (no commit) | trashed | 0 |
| Committed, but a file changed after the read, has no receipt, or the Trash failed | that file kept, with a warning | 0 |

Deletions are **not** journaled. Raw paths are banned from journal payloads, and a host-local file operation is not
vault history. The commit subject does not change.

### 4.4 Trash, not unlink (A2)

- **macOS:** `-[NSFileManager trashItemAtURL:resultingItemURL:error:]`. bob already links `objc2-foundation` on
  macOS for `NSFileCoordinator`, so this is one more feature flag (`NSFileManager`) and roughly 30 lines.
  - The alternative is the `trash` crate's Finder/AppleScript method. It supports Finder's **Put Back**, but it is
    slower and needs Automation permission. A child process of Obsidian would trigger an "Obsidian wants to control
    Finder" prompt.
  - Apple's API does not record the original location, so Put Back is unavailable (rdar://41878624). The file is
    still in the Trash and can be dragged back. That is an acceptable trade for no prompts.
- **Linux:** the freedesktop Trash spec (`$XDG_DATA_HOME/Trash/{files,info}`). Either use the `trash` crate (v5),
  configured for NsFileManager on macOS if its objc2 version unifies with bob's, or write about 80 lines in-house.
- **Never fall back to `unlink`.** If the Trash refuses (for example a volume without a Trash), keep the file and warn.
- **Test seam:** a hidden environment override for the Trash directory (in the style of `BOB_NOW`), so integration
  tests never touch the real Trash.
- **Privacy note for the docs:** the file stays on disk until the Trash is emptied. Finder can empty it automatically
  after 30 days (Settings → Advanced).

### 4.5 Human output

These mock-ups are abridged. Blocks above the new lines are unchanged.

The new line sits **after `Sync:`** because it is the last side effect, and before warnings, the 🔁 subscription
line, and `Next:`. The 🗑 matches the existing 🔁 and 🏦 emoji. When all files share a directory, it is printed once,
`~`-abbreviated.

**Monday, from command mode (apply):**

```text
/Users/bryan/Downloads/Checking1.qfx · checking · 2026-11-05–2026-11-19
  New 9 · matched 23 · seen 41 · ambiguous 0 · before start 0
  Out $1,204.33 · In +$2,500.00
  Ledger balance $12,345.67 on 2026-11-19
Accounts:
  WF Checking · ✓ balanced · through 2026-11-19
Affected: .bob/bank/mac.jsonl, bank/2026-11.md
Committed bank: import 9 rows (checking) (1a2b3c4)
Sync: pre ok, post ok
🗑 Moved to the Trash from ~/Downloads: Checking1.qfx
Next: file the 9 waiting rows in bank/2026-11.md — ]b walks them oldest first, Ctrl+Enter files each (or bob bank to list them).
```

**Command-mode preview (`--dry-run`, Enter):**

```text
Dry run — nothing written
…
🗑 Would move to the Trash from ~/Downloads: Checking1.qfx, Checking1 (1).qfx
```

**Re-download already recorded (replay):**

```text
No changes; no import commit.
🗑 Moved to the Trash from ~/Downloads: Checking1 (1).qfx
```

**Refused batch.** The new third line answers "did it delete my files?":

```text
✗ bob bank import: /Users/bryan/Downloads/Savings.qfx: no configured savings account
  add the account to bank.md, or pass -a ALIAS
  Kept 2 files — -D moves nothing until the whole batch imports.
```

**A file that cannot be removed after a successful import** (exit 0):

```text
🗑 Moved to the Trash from ~/Downloads: Checking1.qfx
warning: kept Checking1 (1).qfx — it changed after bob read it; run the import again to record and remove it
```

The kept files could also be appended to the 🗑 line (`· kept 1`), so the pager shows the problem without reading
past it. Output keeps honoring `NO_COLOR` and pipes. The emoji is plain text, and the dim style applies to the hint
lines only.

An optional improvement on the same path: macOS TCC can deny Obsidian (and therefore bob) access to Downloads. In that
case reads fail with `Operation not permitted (os error 1)`, and today's hint, "fix the source file", is wrong. A
macOS EPERM hint would read: `macOS blocked access to Downloads — allow Obsidian in System Settings → Privacy &
Security → Files and Folders`.

### 4.6 JSON (additive, `schema_version` stays 1)

```json
"delete": {
  "requested": true,
  "method": "trash",
  "files": [
    { "path": "/Users/bryan/Downloads/Checking1.qfx",     "status": "trashed", "reason": null },
    { "path": "/Users/bryan/Downloads/Checking1 (1).qfx", "status": "kept",    "reason": "changed_since_read" }
  ]
}
```

- `status` is one of `would_trash`, `trashed`, `kept`.
- `reason` is one of `import_failed`, `changed_since_read`, `not_recorded`, `trash_failed`.
- Without `-D`, the value is `"delete": null`.
- `ok` and `exit_code` keep describing the import.

Because the change is additive, it is not a `!` contract break under the daily release train.

### 4.7 Command mode and the bank card

- No plugin change is *required*. Once bob expands operands, typing `bank import -D ~/Downloads/*.qfx` previews on
  Enter and applies on Ctrl+Enter. The RECENT row then replays the **pattern** every Monday.
- Phase 2 (bob-plugins, bob-ledger-tools):
  - Change the bank card footer to `Weekly import: bob bank import -D ~/Downloads/*.qfx`.
  - Make the line a button that calls
    `api.commandMode.preview(["bank", "import", "-D", "~/Downloads/*.qfx"])`, the same path the keep-inbox actions
    use.
  - Result: one click opens a preview with the 🗑 "would move" line, and Ctrl+Enter applies it.
  - The existing test regex `/Weekly import: bob bank import/` still matches.
- Optionally, add `delete` and `downloads` to the `bank-import` catalog keywords.

### 4.8 Docs and decisions

- **`docs/bank.md`:**
  - Synopsis line.
  - A short "Removing imported downloads (`-D`)" subsection under Import: the rule from §4.3, Trash semantics, no
    journaling, and operand expansion.
  - Exit-code bullets.
  - The JSON field.
- **Guide:** replace `bob bank import ~/Downloads/*.qfx && rm ~/Downloads/*.qfx` with `bob bank import -D
  ~/Downloads/*.qfx`. Keep the account-number rationale and mention command mode.
- **Generated reference:** run `just docs-gen` and `just docs-check`, per the docs memory.
- **Decision records, via `/sase_memory_write`.** Two durable policies should be recorded:
  - *"bob expands `~` and globs in host-file operands, literal-first, because command mode has no shell."*
  - *"Imported bank downloads go to the Trash only after the journal holds their digest."*
- **Side finding:** the guide's sample import output (`🏦 Import · WF Checking · …`, `9 new (waiting) · 23 matched your
  rows`) no longer matches what `print_human` prints (`<file> · <account> · <range>`, `New 9 · matched 23 · …`). Fix
  it while editing that section.

## 5. Alternatives considered

| Alternative | Verdict | Reason |
| --- | --- | --- |
| `-D` that unlinks (as asked) | Viable runner-up | Same design. Only §4.4 changes. Simpler to test, but irreversible. Choose it if you want strict `rm` parity. |
| Keep the shell idiom `… && rm ~/Downloads/*.qfx` | Reject | Impossible in command mode (no shell, and `rm` is not bob). Re-globbing can delete a file that arrived mid-import. |
| Plugin-side `~`/glob expansion in command mode | Reject (for now) | Stored argv would contain expanded, since-deleted names, which breaks RECENT, sequences, and replays. Every caller (`api.commandMode`, sequences) would need it, and it would put shell semantics in JS for every command. |
| Archive raw QFX into the vault (the `bean-file` model) | Reject | `docs/bank.md` promises account and routing numbers are "never stored", and the QFX carries `ACCTID`. The journal and rows already keep everything bob needs, and `-F` restores from them. |
| Archive to a bob-owned host directory (`~/.local/state/bob-cli/bank/imported/`) | Reject | A home-made trash that is harder to find and needs its own retention policy. The OS Trash already does this well. |
| Configured inbox: `bank.md` `import.from: ~/Downloads/*.qfx` plus a bare `bank import` | Later, maybe | A vault-synced file would hold host-local paths, and it changes the "no FILE is refused" contract. A catalog alias row or the Phase 2 card button gives the same one-gesture result with no contract change. |
| Folder watch (launchd `WatchPaths`) that auto-imports | Reject | Skips the `preview-first` review on a committed money write. |
| Delete by default, with `--keep` | Reject | Destructive defaults surprise people. Deletion should be opt-in. |

## 6. Risks and open questions

- **Preview/apply drift:** the glob re-expands at apply time. A file that appears between Enter and Ctrl+Enter is
  imported and trashed without having been previewed. It is still fully parsed and recorded before removal, so I
  accept this.
- **Case-insensitive globbing** is a choice that differs from shell behavior. I recommend it (some banks emit `.QFX`),
  but you might prefer strict shell parity.
- **Exit code for cleanup failures.** I chose exit 0 with a warning. If you want command mode to show these runs in
  amber, a dedicated code mapped through a catalog `exit_codes` hint to `attention` would be the first use of that
  mechanism. That is probably overkill for a rare event.
- **Linux headless hosts:** trashed QFX files accumulate in `~/.local/share/Trash` until emptied. The guide runs this
  on the Mac, so the risk is low.
- **Put Back on macOS:** unavailable through `NSFileManager` (Apple bug), but the file can be dragged back.

## 7. Implementation sketch (one bob-cli change plus a small follow-up in bob-plugins)

1. `native::host_paths::expand_operands`: `~` plus glob, literal-first, sorted. Unit tests for literal-exists,
   tilde, sorting, hidden files, no-match, and non-UTF-8 paths.
2. `native::host_trash::move_to_trash`: macOS through `NSFileManager`, Linux through the freedesktop Trash, plus the
   hidden test-directory override.
3. `bank/cli.rs`:
   - Add `delete_arg()`, placed alphabetically.
   - Update `long_about` and the examples.
   - `execute_import` expands operands, checks removability, and calls `import_run::remove_sources` after
     success or a dry run.
4. `bank/import_run.rs`:
   - `PreparedSource { path, identity }`.
   - `ImportReport.delete: Option<DeleteReport>`.
   - The JSON field, the human line, and the "Kept N files" failure line.
   - Receipt check against the reloaded journal.
5. Tests, in the existing `import_run` test module style:
   - Success trashes the file.
   - Replay trashes the file with no commit.
   - Parse refusal, identity conflict, lock refusal, and ignored journal all keep every file.
   - Post-sync failure trashes the file.
   - Bytes changed after the read keep the file and exit 0.
   - Dry run lists `would_trash` and leaves the file untouched.
   - Symlink, directory, or vault-internal path refuses with exit 2.
   - Duplicate operands are trashed once.
   - A literal `~/Downloads/*.qfx` with a temp `HOME` works, simulating command mode.
   - The JSON contract snapshot.
6. Docs: `docs/bank.md`, the guide (including the stale-sample fix), `just docs-gen`, `just docs-check`, and the two
   decision records.
7. Follow-up in bob-plugins: the bank card footer text and button, then `npm run build`, `npm test`, and
   `bob plugins sync`.

The commit is `feat(bank): …` and non-breaking. Leave `Cargo.toml` and `CHANGELOG.md` alone; the release train owns
them.

## 8. Recommended solution

Ship **`bob bank import -D, --delete`** with these properties:

1. **It works where you asked for it.** bob expands `~` and glob patterns in FILE operands, using any operand that
   exists literally as-is. `bank import -D ~/Downloads/*.qfx` then runs from command mode exactly as from a shell, and
   its RECENT entry replays the pattern every week.
2. **It removes only what the vault provably holds.** A file is removed only when all of these hold:
   - The whole batch was recorded: committed, an identical replay, or committed with a failed post-sync.
   - The file's SHA-256 is in a `bank.import` journal event for its account.
   - The file is byte-for-byte unchanged since bob read it.

   Any refusal or failure keeps every file and says `Kept N files`. A dry run lists what *would* be moved.
3. **It is reversible.** Files go to the **Trash** (NSFileManager on macOS, the freedesktop Trash on Linux). bob never
   falls back to unlinking.
4. **It checks removability before writing.** Only regular files outside the vault are eligible, and anything else is
   refused with exit 2 before any write. A cleanup error after a successful import is a warning with exit 0, and
   re-running heals it.
5. **The output is one line.** `🗑 Moved to the Trash from ~/Downloads: Checking1.qfx` (or `Would move…` in the
   preview). JSON gains an additive `delete` object. Deletions are never journaled.
6. **Then the card button.** Make the bank card's "Weekly import" line a one-click command-mode preview of
   `bank import -D ~/Downloads/*.qfx`. Update the guide to replace `&& rm`, and record the two decisions.

If you'd rather match the guide's `rm` exactly, swap step 3 for unlink. Everything else in the design stays the same,
and the proof-of-record check still applies.

## Sources

- [trash crate 5.2.6, macOS module source (Finder vs NsFileManager, Put Back)](https://docs.rs/crate/trash/5.2.6/source/src/macos/mod.rs)
- [Apple rdar://41878624, "Put Back" doesn't work with programmatically trashed files](https://openradar.appspot.com/41878624)
- [rsync `--remove-source-files` man text, quoted (removes only transferred files; quiescent-files warning)](https://wiki.neonvagabond.xyz/content/unix.stackexchange.com_en_all_2024-05/a/371149)
- [rsync man page](https://www.mankier.com/1/rsync)
- [bean-file(1), Beancount: move downloaded files into a documents archive](https://manpages.ubuntu.com/manpages/noble/man1/bean-file.1.html)
- [Beancount: Importing External Data](https://beancount.github.io/docs/importing_external_data/)
