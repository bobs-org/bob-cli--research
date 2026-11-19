# `bob bank import --delete`: delete QFX sources after successful import

Research report — researcher `mus` (independent swarm member).
Requested feature: add `-D|--delete` to `bob bank import` so
`bank import -D ~/Downloads/*.qfx` from Bob Command Mode deletes the
imported QFX files iff all imports succeeded. This report researches the
current implementation, critiques the plan, proposes requirement
adjustments, and ends with a recommended solution.

## TL;DR

Yes, build it — but **do not spell it `-D`**. Ship `--delete` with a
non-confusable short flag (recommended: `-X`), permanent
`fs::remove_file` deletion gated strictly on `ImportReport.failure.is_none()`
*after* the scoped vault commit verifies, never on dry-run, never on any
refusal or runtime failure. Report deletions additively in human and JSON
output, keep exit 0 on import success even if a delete later fails (surface
as warnings + JSON fields), and update `docs/bank.md` plus generated CLI
reference via `just docs-gen`. The `-D` short is the one part of the request
to change: in the `bank` family `-D` already means `--day`, and `-D` next to
`-d` (`--dry-run`, the exact opposite safety semantics) is a one-shift-key
footgun.

## 1. What was asked

- New option on `bob bank import`, spelled `-D|--delete`.
- Invocation from Obsidian via Bob Command Mode, e.g.
  `bank import -D ~/Downloads/*.qfx`.
- Semantics: when specified, delete the QFX files that were imported,
  iff all imports were successful.
- Researcher is explicitly asked to lead the design ("intuitive, reliable,
  beautiful"), critique the plan, adjust requirements with callouts, and end
  with a recommended solution.

## 2. How `bob bank import` works today

All paths below verified in the `bob-cli_20` workspace checkout.

### 2.1 CLI definition

- Dispatch: `src/native.rs:276` maps `NativeCommand::BankImport` to
  `bank::cli::run_import(args)`.
- Definition: `build_cli_import()` in
  `src/native/bank/cli.rs:227-257`. Current flags, alphabetical in help:
  `-a/--account`, `-b/--bob-dir`, `-d/--dry-run`, `-F/--force`
  (`--force` is the long for "restore journaled transactions whose rows are
  missing", `restore_missing_arg()` at `cli.rs:477-483`),
  `-f/--format`, `-h/--help`, plus repeatable `[FILE]` positional
  (`Arg::new("files")`, `num_args(0..)`).
- Help texts (`cli.rs:228-236`): "Plans the whole batch before writing.
  Existing rows are matched only by account, exact signed cents, and the
  documented posted-date window; new rows and the private bank journal commit
  together. `-F` deliberately restores journaled transactions whose rows were
  deleted. An ignored journal destination is refused before rows are
  installed. Refused input exits 2; runtime failures exit 1."
- Runner-level help mirrors this in `src/runner.rs:387-429`, including the
  `BANK_AFTER_HELP` example `bob bank import ~/Downloads/*.qfx`.
- Generated reference: `docs/reference/cli/bank.md:192-231` (from
  `just docs-gen` + clap help). Contract: `docs/bank.md` Import section
  (~`docs/bank.md:356+`, usage line
  `bob bank import [FILE...] [-a ALIAS] [-d] [-F]`).

### 2.2 Execution path

`execute_import()` (`cli.rs:525-597`):

1. `vault_from()` expands `~` via `bob_env::expand_tilde` (`cli.rs:501-507`;
   `src/native/env.rs:452`). Note: tilde is expanded by bob; `*` glob
   expansion is done by the invoking shell, not by bob.
2. Empty `files` + no `-F` → `missing_files_failure()` → exit 2
   (`import_run.rs:292-298`, checked in `cli.rs:538-550`).
3. `prepare_sources(&paths)` (`import_run.rs:302-319`): `fs::read` each path,
   then `source::parse_export(&label, &bytes, order)`. A malformed member
   refuses the **whole batch** before any vault/lock/sync change. No dedupe
   of duplicate argv entries observed.
4. Dry-run → `dry_run_with_restore()` (pure planner only: no directories, no
   Git/sync, no lock). Real → `apply_with_restore()` (shared maintenance
   lock + sync lifecycle via `host_catalog::run_locked`, `import_run.rs:761-836`).
5. `plan_import()` (`import_run.rs:322-546`): snapshot scan, config parse,
   journal load, `resolve_account`, `import_plan::plan_batch`, read-deps,
   staged month files + journal appends + verify images.
6. `refresh_accounts()` on success (`import_run.rs:549-584`), then human or
   JSON print, then `report.exit_code()`.

### 2.3 Success / failure contract

- `ImportReport` (`import_run.rs:40-52`): `{dry_run, today, config, accounts,
  plan, commit, sync_pre, sync_post, warnings, failure}`.
- `exit_code()` (`import_run.rs:74-81`): `None → 0`; `bank_import_*` or
  `stale_note → 2`; anything else → 1. Refused input exits 2, runtime
  failures exit 1 — matches the clap long_about.
- `to_json()` (`import_run.rs:83-176`): `schema_version: 1`, `ok`,
  `dry_run`, `changed`, `restored`/`restored_rows`, `changes`, `findings`,
  `commit`, `sync: {pre, post}`, `warnings`, `files[]`, `rows[]`,
  `subscriptions: {linked, candidates, price_changes}`, plus `error` when
  failed. Additive evolution is the norm (see test
  `json_contract_has_additive_import_summary_and_exact_dry_run_diff`,
  `import_run.rs:2021+`, which asserts new keys don't break old ones).
- Human output (`print_human`, `import_run.rs:867-999`): per-file block
  (`file · account · range`, `New/matched/seen/ambiguous/before_start`,
  `Out/In`, optional `Ledger balance`), `Accounts:`, restore details,
  findings, `Affected:`, then commit/sync or diffs, warnings, subscription
  summary, and a `Next:` line (`walk_next_line`, `import_run.rs:1061+`).
- Commit subject (`planned_txn`, `import_run.rs:633-685`):
  `bank: import N rows (<alias>)`, multi-alias list, or
  `bank: import restore N rows (...)` / `bank: import N rows, restore M (...)`.
  `N` counts new waiting rows, never matches or journal events.

### 2.4 Adjacent facts that constrain the design

- **Command Mode policy.** `bank-import` is `Policy::PreviewFirst` with
  preview `["--dry-run"]` (`src/native/catalog/table.rs:1350-1359`,
  `DRY_RUN` const at `table.rs:135`). Writers without a preview require
  `Ctrl+Enter` / Run-button confirmation
  (`docs/reference/plugins/bob-command-mode.md`). Completion kind for the
  `files` positional is `Kind::Files(None)`
  (`src/native/completion/kinds.rs:577-582`), so Obsidian can pick files;
  whether it glob-expands `*.qfx` is unconfirmed — see §6.5. Either way the
  safety story (preview shows diffs, confirm card, 60 s budget) already
  exists and the delete flag must plug into it, not bypass it.
- **`-D` already means `--day`.** `day_arg()` (`cli.rs:432-440`),
  `day_arg_default_today()` (`cli.rs:441-449`), and `day_arg_optional()`
  (`cli.rs:451-458`) all use `-D/--day` for `bank report`, `bank ensure`,
  and `bank ack` respectively. `bank import` is the only `bank` write command
  where `-D` is currently free — but family consistency matters for muscle
  memory in Command Mode.
- **CLI rules (memory `cli_rules.md`, read 2026-11-19):** `-h|--help`
  excellent; options sorted alphabetically; **every public long gets a
  short**; beautiful colored output; never rename/remove commands (hidden
  aliases instead). Docs routing (memory `docs.md`): new CLI flag →
  `just docs-gen` + clap help; behavior change → contract/reference plus
  only the guide steps made incorrect.
- **No in-repo delete precedent for import sources.** `grep` for
  `--delete/--trash/remove_file` in `src/native/bank/` finds only prose
  ("rows were deleted", "deleted rows stay deleted"); `fs::remove_file` is
  used for temp/scratch cleanup elsewhere, never for user data. `bob
  attachments import` *copies* files in and never deletes the origin.
  `capture-templates delete` (`src/runner.rs:1420`, `src/native.rs:296`) is a
  vault-object delete, not a filesystem-source delete. So this is a new
  pattern: vault-transaction success gating an outside-the-vault side effect.
- **Idempotency already exists.** Seen transactions (journaled key or row ID
  present) are never rewritten; identical replay creates no new events and no
  commit ("replay produces no scoped import commit", `docs/bank.md:585`).
  Deleting an already-imported file is therefore safe *because* the journal
  is the source of truth — re-downloading the same export later is a no-op.
  This is the strongest argument the feature is safe at all.

## 3. Is this a good idea?

Yes, with the adjustments in §4. Assessment:

**Why it's worth doing.**

1. The requested workflow is real and currently awkward: download QFX →
   switch to Obsidian → run import → switch to Finder/shell → delete exports.
   From Command Mode there is no `&& rm` (the shell trick doesn't exist in
   the sheet), so without the flag the last step stays manual. A single
   success-gated cleanup completes the loop where the user actually is.
2. Bank exports are sensitive PII sitting in `~/Downloads`. Prompt deletion
   shrinks the exposure window. This is hygiene, not just tidiness.
3. The success gate is implementable precisely because import is already
   all-or-nothing at the vault layer (whole-batch refusal, guarded txn,
   verify-before-commit). "Iff all imports were successful" maps cleanly to
   `failure.is_none()` after `apply_with_restore` returns.

**Why the naive version would be bad.**

1. Coupling an irreversible outside-the-vault side effect to a vault commit
   is the core risk. The vault write can roll back; `rm` cannot. Order and
   failure reporting must reflect that asymmetry (§5.4).
2. Silent data loss is one typo away if the flag is `-D`: `-d` previews,
   `-D` deletes — opposite meanings one shift-key apart, in a command whose
   other subcommands use `-D` for `--day`. This alone justifies respelling.
3. Trash-vs-delete, glob-vs-literal, dry-run, restore-only (`-F` with no
   files), partial-delete, and post-sync-failure semantics all need answers
   before code, or the "beautiful" part won't survive first contact with a
   real `~/Downloads`.

**Would I take a different approach?** Considered and rejected:

| Alternative | Verdict |
|---|---|
| Shell `bob bank import *.qfx && rm *.qfx` / alias / function | Fine outside Obsidian, and worth documenting as the no-flag equivalent. But it doesn't work from Command Mode (no shell chaining), it re-expands the glob (race: new files landing between import and `rm` get deleted unimported), and the gate is "exit 0" without distinguishing import-failure kinds. Keep as documented alternative, not the solution. |
| Separate `bob bank clean-downloads` / Hazel / launchd sweeper | Decouples nicely but loses the atomic gate: a sweeper can't know *this* import succeeded, and age-based sweeping deletes unimported files. Reject as primary; fine as a user-local extra. |
| Move to Trash instead of delete | Recoverable, but cross-platform Trash is a new dependency (macOS `NSFileManager` vs Linux `gio trash` vs `trash-cli`), Trash still holds PII, and `~/Downloads` Trash semantics surprise CLI users. Reject for v1; optionally revisit as a future `--trash` if Bryan wants a safety net (see §5.3). |
| Archive into the vault (attach QFX to month note) | Preserves evidence but stores PII + duplicates in Git, contradicting the journal's deliberate "raw paths, files, and bank identifiers are never journal payloads" rule (`docs/bank.md:535+`). Reject. |
| Import-then-always-delete (no flag; or default-on) | Violates least surprise for a financial importer; breaks re-runnable demos/tests and anyone who keeps exports. The flag must stay opt-in. Reject. |

So: add the flag, opt-in, success-gated, permanent delete, with the
respelling and semantics below.

## 4. Requirement adjustments (all called out)

1. **Respell `-D|--delete` → `--delete` with short `-X` (not `-D`).**
   Justification: (a) `-D/--day` is taken across `bank report/ensure/ack`
   (`cli.rs:432-458`); reusing `-D` for delete in one sibling breaks family
   consistency and Command Mode muscle memory. (b) `-d` vs `-D` visual
   confusability with opposite safety polarity (preview vs destroy).
   `-X` is free in `import` (`-a,-b,-d,-F,-f,-h` taken), mnemonic
   (✕/cross-out = delete in UIs), and alphabetically sortable per CLI rules.
   If Bryan insists on typing `-D`, add it only as a permanent hidden alias
   — but the recommendation is to **not** add `-D` at all, so the confusing
   spelling never gets baked in (CLI rules make aliases permanent).
2. **Define "all imports were successful" as `failure.is_none()` (exit 0),
   warnings included.** Counts like `ambiguous`, `before_start`, `matched`,
   `seen`, zero-new replays, and warning findings do **not** block deletion.
   Dry-run (`-d`) **never** deletes even with `--delete`. Any
   `bank_import_*` refusal (exit 2) or runtime failure (exit 1) deletes
   nothing. `-F` restore-only with no `FILE`s has nothing to delete and
   trivially succeeds.
3. **Delete permanently with `fs::remove_file`, not Trash.** Justification:
   no new platform dependency, predictable headless behavior, PII actually
   leaves `~/Downloads`, and journal idempotency makes replay safe. Call out
   the tradeoff (unrecoverable) and mitigate via opt-in + preview + explicit
   output (§5.6), not via Trash.
4. **Delete only the exact source paths bob read, after commit+verify,
   best-effort.** Not the glob pattern, not directories, not stdin. Dedupe
   repeated argv entries; skip non-regular files with a warning rather than
   aborting the (already committed) import. A per-file delete failure warns
   but does not rewrite import history or change the import's exit code
   (§5.4).
5. **Post-sync failure still deletes.** `apply_with_restore` reports sync via
   `sync_pre/sync_post` + `post_sync_warning` with `failure: None`; the local
   commit is durable ("Post-sync failure keeps the local commit",
   `docs/bank.md`). Deletion keys off commit durability, not network sync.
6. **Scope to `bank import` files only.** No recursive directory deletes, no
   vault deletes, no `-F`-implies-delete. The flag is orthogonal to `-F` and
   `-a`; combinations compose (`-a` + `--delete`, `-F` + files + `--delete`).

## 5. Design

### 5.1 Flag shape

```text
-X, --delete
        Delete each source file after a successful import
```

- Long `--delete` (as requested); short `-X` (adjustment #1).
- Alphabetical placement in clap help: after `--dry-run`/`-d`, before
  `--force`/`-F`? Clap orders by the builder call order in this codebase
  (see `build_cli_import`: files, account, bob-dir, dry-run, restore-missing,
  format, help — help output itself is alphabetical by long name). Follow the
  existing file's convention and verify with `--help` that the rendered order
  is `account, bob-dir, delete, dry-run, force, format, help`.
- Help `long_about` gains one sentence: "With `--delete`, each source file
  is permanently deleted after the import commits; nothing is deleted on
  preview, refusal, or failure." `after_help` gains an example:
  `bob bank import --delete ~/Downloads/*.qfx`.
- Catalog (`src/native/catalog/table.rs:1350-1359`): no schema change needed
  (no `slots`/`extra_args` for flags); optionally add `delete/cleanup` to the
  keyword list for discoverability. Preview stays `Some(DRY_RUN)` — preview
  must show the would-delete set without deleting.

### 5.2 What counts as "successful"

Delete iff **all** hold:

- `!dry_run` (preview never deletes — even though `dry_run_with_restore`
  returns `failure: None` on a clean plan).
- `report.failure.is_none()` from `apply_with_restore` (exit 0 path in
  `execute_import`, `cli.rs:577-586`), including the all-seen replay
  (`changed: false`, "No changes; no import commit") — deleting an
  already-journaled duplicate export is the *point*.
- The scoped commit (when there were changes) verified and landed
  (`PlannedTxn.verify`, `import_run.rs:668-681`).

Delete in **none** of these: source read/parse refusal, `plan_import`
refusal (`bank_import_*`, `stale_note`), journal-ignored refusal
(`bank_import_journal_ignored`), lock/runtime failure (exit 1), or
`missing_files_failure` (nothing to delete anyway).

### 5.3 Delete vs trash vs archive

Permanent delete (`std::fs::remove_file`) is recommended for v1:

- PII leaves the disk; Trash would retain it.
- Zero new dependencies; identical behavior on athena/apollo/mac (bob runs
  wherever Command Mode invokes it).
- Predictable in scripts and `just` gates.

Cost: unrecoverable. Mitigations (instead of Trash): explicit opt-in flag,
PreviewFirst flow in Command Mode shows the file list before anything is
destroyed, dry-run prints `Would delete N files:` without touching them,
human output names every deleted file, JSON records `deleted[]` for audit.
Re-import safety comes from the journal, not from Trash.

Future escape hatch (not v1): `--trash` using OS Trash when available. Don't
ship both spellings now — two destroy flags is the opposite of intuitive.

### 5.4 Ordering, atomicity, and delete-failure policy

Required order in `execute_import` (real path only):

1. `prepare_sources` → `apply_with_restore` (locked plan → commit → verify).
2. If `report.failure.is_some()`: return immediately, delete nothing.
3. Else delete each *unique, tilde-expanded* source path that was actually
   read (the `paths: Vec<PathBuf>` built in `execute_import`,
   `cli.rs:533-536`, after `vault_from` expansion — not the raw glob).
4. Collect `deleted: Vec<String>` and `delete_errors: Vec<{file, message}>`.
   Continue past individual failures (best-effort: one unreadable-still-locked
   file must not mask the others).
5. Attach to the report; print; exit with the **import's** code.

Delete failures therefore never flip a successful import to exit 1/2 and
never roll back the commit (impossible anyway — the commit is durable by
then). They surface as:

- Human: `Deleted 2 files:` + names, then `warning: could not delete <file>:
  <message>` per failure (via `report.warnings`, same channel as
  `refresh_accounts` warnings, `import_run.rs:559-583`).
- JSON: additive `deleted: [<label>...]` and
  `delete_errors: [{file, message}...]` (or `delete_failed`), with
  `ok: true` preserved. Additive keys keep the
  `json_contract_has_additive_import_summary` test philosophy intact.

Rationale for exit-0-on-delete-failure: the import *was* successful, and
conflating cleanup trouble with money-movement failure would teach scripts
(and Bryan) to distrust the exit code. The warnings + JSON fields are the
durable signal; a follow-up `rm` completes cleanup.

Edge: post-sync warning + success → still delete (adjustment #5). The money
and journal are committed locally; holding PII in Downloads because the
network hiccuped is worse.

### 5.5 Glob, tilde, duplicates, and weird paths

- `~/Downloads/*.qfx` from a shell: the shell expands the glob; bob sees N
  concrete paths. From Command Mode, expansion behavior is unverified (open
  question §6.5): if the sheet passes the literal `*.qfx`, `prepare_sources`
  fails the read (`could not read source`) → whole batch refused, nothing
  deleted. That's the safe direction; document it and verify before release
  whether users must pick files via completion (`Kind::Files`, §2.4) or type
  them one by one.
- Tilde: already expanded (`cli.rs:505`, `env.rs:452`) — delete the expanded
  path, and report the user-typed `label` (`PreparedSource.label`,
  `import_run.rs:35-38`) so output matches what Bryan typed.
- Duplicates (same file twice via overlapping globs): `prepare_sources`
  reads twice today; deletion must dedupe (delete once, report once). Note
  as an implementation detail: dedupe on canonicalized-expanded path, but
  report labels.
- Never delete: directories (a `FILE` arg pointing at a dir fails parse
  first — keep it that way and additionally guard `is_file()` before
  unlink), stdin/`-` (no stdin source exists for import; keep it so), files
  outside the argv list, or anything when `-F`-only was used.
- Symlinks: `fs::remove_file` unlinks the link, not the target — acceptable
  and standard; no special-casing needed beyond documenting it.
- Permissions/locks (file open in another app, read-only Downloads):
  per-file warning path (§5.4), not a batch failure.

### 5.6 "Beautiful": output contract

Human (real run, success + `--delete`):

```text
checking.qfx · checking · 2026-11-01–2026-11-14
  New 12 · matched 2 · seen 0 · ambiguous 0 · before start 0
  Out $… · In $…
Accounts:
  checking · ✓ balanced · through 2026-11-14
Affected: bank/2026-11.md, .bob/bank/<host>.jsonl
Committed bank: import 12 rows (checking) (<sha>)
Sync: pre …, post …
Deleted 1 file: ~/Downloads/checking.qfx
Next: file the 12 waiting rows in bank/2026-11.md — …
```

- Dry-run + `--delete`: after the diffs,
  `Would delete N files: <labels>` (and never delete). This is what the
  Command Mode preview shows, satisfying PreviewFirst honestly.
- Refusal/failure + `--delete`: existing `✗ bob bank import: <message>` +
  hint; add `Nothing deleted.` only if it fits the house style — otherwise
  silence is fine since nothing was promised.
- Color via existing `Styler::detect()` (`NO_COLOR`/pipe respected,
  `import_run.rs:868`); deletion lines reuse the normal (non-red) channel —
  green/check only if the file already uses that idiom for success lines.
- JSON: `deleted: ["~/Downloads/checking.qfx"]`,
  `delete_errors: []`, plus `would_delete` on dry-run if cheap. All additive;
  `ok`/`exit_code` semantics unchanged.

### 5.7 Docs, completion, and gates

- `docs/bank.md` Import section: one paragraph + example
  (`--delete` semantics, gate, dry-run behavior, trash non-goal). Usage line
  becomes `bob bank import [FILE...] [-a ALIAS] [-b DIR] [-d] [--delete] [-F]
  [-f human|json]` (keep the existing bracket style).
- `just docs-gen` regenerates `docs/reference/cli/bank.md`; `just docs-check`
  is the gate (memory `docs.md`). The catalog table's `bank-import` keywords
  may gain `delete/cleanup` — cheap discoverability in Command Mode.
- Tests (new, in `src/native/bank/import_run.rs` + `cli.rs` level):
  1. success + `--delete` removes files and reports them (tempdir QFX pair);
  2. refusal (bad second file, `prepare_sources` whole-batch refusal per
     `import_run.rs:1668` test pattern) deletes nothing;
  3. dry-run + `--delete` deletes nothing but reports would-delete;
  4. delete-failure (read-only dir / missing file raced away) keeps exit 0
     with warning + JSON field;
  5. replay (all-seen, no commit) + `--delete` still deletes;
  6. `-F`-only + `--delete` with no files succeeds and deletes nothing;
  7. `-D` is rejected as unknown (documents the respelling) — or, if a
     hidden `-D` alias is ever added, a test pinning it.
- No `AGENTS.md`/memory changes needed (behavior owned by `docs/bank.md` +
  decision record only if this becomes a standing rule — it doesn't need one).

## 6. Open questions and risks to close before implementation

1. **Short flag ratification.** `-X` is recommended; alternatives `-R`, `-E`,
   or long-only (against CLI rules) are worse. One-line confirmation from
   Bryan settles it. (If he truly wants `-D`, ship `-X|--delete` canonical
   with `-D` as a hidden alias — but prefer not to.)
2. **Command Mode glob behavior.** Verify whether the sheet expands
   `~/Downloads/*.qfx` or requires per-file completion picks. The design is
   safe either way (literal glob → clean refusal), but the docs example and
   the "beautiful" claim depend on the answer.
3. **Multi-file partial semantics.** "Iff all imports were successful" is
   batch-atomic today (one `BatchPlan`, one commit), so there is no
   commit-half-the-files state at the vault layer. Confirm the implementer
   keeps it that way: no per-file commits to enable per-file deletion.
4. **Journal-ignored + `--delete`.** `bank_import_journal_ignored` refuses
   before rows install (`import_run.rs:793-813`) — correctly deletes nothing.
   Keep that check before any unlink; add a test.
5. **Sandboxing on macOS.** If Obsidian's spawned `bob` ever runs sandboxed,
   `remove_file(~/Downloads/…)` may deny where vault writes succeed. The
   per-file warning path covers it, but a real Mac smoke test from Command
   Mode (not just `cargo test`) is required.

## 7. Recommended solution

Ship an opt-in, success-gated, permanent-delete flag on `bob bank import`:

- **Spelling:** `-X, --delete` (adjustment: not `-D`; §4.1). Usage:
  `bob bank import --delete ~/Downloads/*.qfx`.
- **Semantics:** after `apply_with_restore` returns `failure: None` on a
  non-dry-run, `execute_import` unlinks each unique expanded source path via
  `fs::remove_file`, best-effort, regular-files only. Any failure beforehand
  (source/parse refusal, plan refusal, journal-ignored, lock/runtime error)
  or any dry-run deletes nothing.
- **Reporting:** human `Deleted N files:` (+ per-file delete warnings),
  dry-run `Would delete N files:`, JSON additive `deleted[]` /
  `delete_errors[]`; import exit code unchanged (delete trouble warns, never
  flips success to failure); post-sync-warning success still deletes.
- **Plumbing:** `delete_arg()` in `cli.rs` (alphabetical, documented), flag
  threaded through `execute_import` → `apply_with_restore`/
  `dry_run_with_restore` signatures (or handled post-report in
  `execute_import` only — prefer the latter to keep `plan_import` pure);
  `ImportReport` gains deletion fields; `print_human` + `to_json` extended;
  `long_about`/`after_help` + `docs/bank.md` + `just docs-gen`; catalog
  keywords optionally extended; tests per §5.7.
- **Non-goals for v1:** no Trash mode, no default-on, no recursive/dir
  deletes, no archive-to-vault, no `-D` spelling.

This keeps the feature exactly where Bryan asked for it (one Command Mode
command that finishes the job), makes the dangerous part explicit and
auditable, and leaves the one requested spelling that would cause real
confusion (`-D`) on the cutting-room floor with reasons recorded above.

## 8. Sources consulted

- `src/native/bank/cli.rs` (`build_cli_import`, `execute_import`,
  `day_arg*`, `restore_missing_arg`, `dry_run_arg`).
- `src/native/bank/import_run.rs` (`ImportReport`, `exit_code`, `to_json`,
  `prepare_sources`, `plan_import`, `planned_txn`, `dry_run_with_restore`,
  `apply_with_restore`, `refresh_accounts`, `print_human`, `walk_next_line`,
  JSON contract test).
- `src/native/bank/import_plan.rs` (batch atomicity; `deleted_rows_stay_deleted`
  behavior).
- `src/native/catalog/table.rs` (`bank-import` row, `Policy::PreviewFirst`,
  `DRY_RUN`).
- `src/native/completion/kinds.rs` (`bank import` `files: Kind::Files`).
- `src/native.rs:276`, `src/runner.rs:387-429` (routing + `BANK_AFTER_HELP`).
- `docs/bank.md` (Import, Sources, Journal, Commit/preview/replay).
- `docs/reference/cli/bank.md:192-231`,
  `docs/reference/plugins/bob-command-mode.md` (PreviewFirst/confirm flow).
- Memory: `cli_rules.md`, `docs.md`, `sase_artifacts.md` via
  `sase memory read … -r "Researching -D/--delete option…"`.
