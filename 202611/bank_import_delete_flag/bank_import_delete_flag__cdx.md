# Bank import deletion: a batch guarantee with an honest cleanup boundary

Researcher: **cdx** · 2026-11-19

## Recommendation in brief

Add `-D, --delete`, default off. It is a useful improvement to the download → import → review ritual, and the existing whole-batch importer is a good foundation. The feature should mean **import this complete set, then permanently remove these same source files only when the import is safely complete**.

It should not be implemented as a loop that imports and deletes one file at a time, or as a Command Mode shell wrapper. The requested command also needs native path expansion: today `bank import -D ~/Downloads/*.qfx` would encounter both an unsupported flag and, after adding that flag alone, an unexpanded pathname.

My recommended design has four parts:

1. Resolve and snapshot the source set in bob, including `~/` and bounded file globs.
2. Keep the current whole-batch import and scoped Git commit.
3. Make deletion a separate, guarded post-import phase with explicit results.
4. Preserve Command Mode's preview/apply experience while binding Apply to the previewed source set and bytes.

The important requirement adjustment is that successful imports **permit** deletion; they cannot guarantee it. Permissions, concurrent changes, interruption, and sync failures can require retaining sources after the import has succeeded. Those outcomes must be visible and retryable.

## Evidence and scope

This is independent research. I did not consult the other swarm researchers' reports, transcripts, or findings. No implementation changes, live bank imports, or source-file deletions were performed.

I inspected bob-cli at `e7aa392d688ea250ada1a6d732e3f27ed0e67c9c` and the linked bob-plugins checkout at `febfc6bacd3ef9895aa1a0c24bff3781ecbb95de`. References below use those revisions rather than moving branches. I also read the project's CLI rules, documentation rules, artifact instructions, and Command Mode/bank glossary through the audited memory reader.

Small executable probes supplemented source inspection:

- The installed `bob 0.5.0`, invoked directly through Python with `bank import -d -f json`, rejected both a literal absolute `*.qfx` argument and literal `~/Downloads/*.qfx` with exit 2 and `bank_import_source: could not read source`. A temporary matching file remained present; the temporary vault path was never created. This verifies installed behavior; its exact build SHA was not established.
- The linked plugin's existing test harness tokenized the user's command as `["bank", "import", "-D", "~/Downloads/*.qfx"]`. Quoting a path containing spaces likewise preserved the tilde and wildcard as characters.
- I inspected existing regression tests, including malformed-input refusal, identical replay, scoped commits, rollback, and post-sync failure. I did not run the full Rust suite or a real Obsidian application session.

### What the current implementation guarantees

| Finding | Evidence | Design consequence |
| --- | --- | --- |
| Import accepts multiple FILE arguments and `-d`, `-F`, `-a`, and `-f`. `-D` is available on this leaf. | [CLI builder](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/src/native/bank/cli.rs#L227) | Add a normal flag; retain lowercase `-d` for dry run. Other bank leaves use `-D` for day, so clear leaf help matters. |
| FILE values become `PathBuf`s unchanged, then `fs::read` reads them directly. Only the vault argument is tilde-expanded here. | [CLI orchestration](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/src/native/bank/cli.rs#L525), [source preparation](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/src/native/bank/import_run.rs#L300) | Native input resolution is necessary for the exact requested workflow. |
| All sources parse before entering maintenance; account resolution and planning use the whole batch. | [Import contract](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/docs/bank.md#L354), [planner](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/src/native/bank/import_plan.rs#L1) | Preserve this boundary. One malformed member must retain every input. |
| Rows and journal appends are installed, verified, and committed together; failures have guarded rollback. | [Transaction implementation](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/src/native/host_catalog/txn.rs#L767) | Delete only after this succeeds; never put external source deletion into its rollback set. |
| A complete replay is successful without a new commit. | [Replay test](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/src/native/bank/import_run.rs#L1676) | Neither `changed` nor `commit.is_some()` is a sufficient deletion predicate. |
| Post-sync failure leaves a local commit and returns success with a warning. | [Lifecycle](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/src/native/host_catalog/txn.rs#L1008), [explicit regression test](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/src/native/bank/import_run.rs#L1612) | Checking only `failure.is_none()` or exit 0 would delete even after failed sync. Choose this policy deliberately. |
| Some journal corruption and identity contradictions surface as warnings rather than refusal. | [Planner findings](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/src/native/bank/import_plan.rs#L416) | Success is not synonymous with trustworthy archival evidence. Classify deletion blockers explicitly. |
| `PreparedSource` retains a human label and parsed statement; the parsed statement includes a digest, but no deletion identity. | [PreparedSource](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/src/native/bank/import_run.rs#L33), [ParsedStatement](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/src/native/bank/source.rs#L93) | Add an operational path and captured file identity; never delete using the lossy display label. |

### What Command Mode changes

The plugin strips shell-style quotes but does not expand the shell language. It launches bob directly with the vault as its working directory. The CLI, not the plugin, owns the command catalog and write policy. Bank import is already `preview-first` with `--dry-run` preview arguments. See the [tokenizer](https://github.com/bobs-org/bob-plugins/blob/febfc6bacd3ef9895aa1a0c24bff3781ecbb95de/plugins/bob-command-mode/src/175-args-vim.js#L3), [spawn call](https://github.com/bobs-org/bob-plugins/blob/febfc6bacd3ef9895aa1a0c24bff3781ecbb95de/plugins/bob-command-mode/src/060-runner.js#L294), and [catalog row](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/src/native/catalog/table.rs#L1349).

Apply currently reruns the original argv, plus optional adapter carry. If native globbing is added without a source guard, a file downloaded after preview could be imported and deleted without appearing in the preview. Replaced contents at the same filename pose the same problem. This is a new consequence of making the source operation destructive, even though fresh replanning already exists for vault writes. See [preview handling](https://github.com/bobs-org/bob-plugins/blob/febfc6bacd3ef9895aa1a0c24bff3781ecbb95de/plugins/bob-command-mode/src/170-sheet.js#L545) and [Apply](https://github.com/bobs-org/bob-plugins/blob/febfc6bacd3ef9895aa1a0c24bff3781ecbb95de/plugins/bob-command-mode/src/170-sheet.js#L750).

## Is deletion a good idea?

Yes, as an explicit option. A Downloads folder full of already-consumed exports creates recurring work and uncertainty. The importer already records file digests, identities, coverage, and balance evidence, and its replay behavior makes retries practical.

There are two costs to acknowledge:

- The journal is a normalized record, not an archive of the original QFX. Account/routing numbers are deliberately discarded, and raw bytes are not retained by this import path. Successful import does not make the original export recoverable. `-F` can restore journaled rows; it cannot restore the QFX file. Keep deletion opt-in and document this distinction. [Source contract](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/docs/bank.md#L373)
- A vault transaction and external Downloads files do not share an atomic commit. Calling several filesystem removal operations cannot make the whole cleanup atomic. Rust's [`remove_file`](https://doc.rust-lang.org/std/fs/fn.remove_file.html) can fail for missing files, permissions, or directory inputs. Unix [`unlink`](https://man7.org/linux/man-pages/man2/unlink.2.html) removes one directory entry, with permissions determined partly by its parent directory. Therefore readable input is not proof of deletability.

I would keep `--delete` as permanent removal of the selected source paths, explicitly described in help. I would not silently copy raw financial exports into a hidden archive. Moving to system Trash is a credible alternative if recoverability is Bryan's main preference, but it has different semantics and platform behavior; it should be called `--trash` if chosen. An archive/move feature can be separate later. None is necessary to deliver this request well.

I would also avoid `import ... && rm ...` as the product solution: it has no native Command Mode support, can expand the pattern twice, lacks file-identity checks, and cannot distinguish the current post-sync-warning success case.

## Proposed behavioral contract

### Adjustments and clarifications to the request

These are intentional design choices, not claims that they were already requested:

1. **Support every supported import format**, not only `.qfx`: QFX, OFX, and the supported CSV profile. The command detects content, so extension-based deletion would be surprising. Every successfully processed input in a mixed batch follows the same policy.
2. **Interpret “iff” as a safety gate plus an attempted cleanup.** No source is removed before the whole batch succeeds. A successful batch may still retain files when cleanup is unsafe or impossible. Report this as incomplete cleanup, not as a rolled-back import.
3. **Retain sources on failed post-sync.** Local data is safe, but the run did not complete its normal durability workflow. For `-D` only, return exit 1 with `import_ok: true` and cleanup withheld. Ordinary imports keep their existing success-with-warning behavior. A successful no-op with pre-sync success and post-sync intentionally skipped remains eligible.
4. **Refuse destructive import when evidence integrity is uncertain.** Initially block `-D` on malformed journal lines, journal contradictions, and duplicate bank IDs; preserve ordinary non-destructive import behavior. Refuse before installing new rows once the planner identifies these findings. Cosmetic/category/subscription warnings, an account balance delta, and normal matching ambiguity do not automatically block deletion.
5. **Bind Command Mode Apply to previewed sources.** A changed source set, replaced file, or changed source bytes requires a new preview. Explicit “run now” remains a deliberate bypass of preview, not of import or cleanup safety checks.
6. **Reject source symlinks and special files for destructive imports**, and reject sources inside the vault for `-D`. This keeps deletion out of Bob's own notes, journals, and Git lifecycle. Existing non-delete import behavior need not change. This is a conservative scope restriction, not a filesystem necessity.

These additions favor retaining an extra download over removing a file whose consumption is uncertain. They do not require a second confirmation dialog: the option and existing preview/apply gesture provide the user intent.

### Define successful processing, not “new rows”

A valid file succeeds when all of its records are accounted for under the existing importer rules and its required evidence is safely recorded. New rows, matched typed rows, already-seen transactions, and intentionally journaled `before_start` transactions can all satisfy that condition. Valid empty OFX statements can supply coverage or balance evidence and also count as success. A valid all-seen file must be deletable; otherwise the most common retry after interruption could never clean up.

Matching ambiguity currently writes a new waiting row rather than dropping a transaction. It is not itself a failed import. Conversely, a malformed source, unresolved account, identity conflict refusal, failed write/verification/commit, or uncertain evidence blocks all deletion. Source and import counts must remain distinct; ambiguous is a qualifier, not another disjoint transaction bucket to sum blindly.

### Outcomes

| Situation | Import effect | Source effect | Exit |
| --- | --- | --- | --- |
| No `-D` | Existing behavior | Retain all | Existing behavior |
| `-D -d` | Preview only | Show exact planned removals; remove none | 0 on valid preview |
| Valid batch, commit and sync succeed | Whole batch recorded | Remove snapshotted unchanged sources | 0 if cleanup completes |
| All records already present, valid evidence, successful pre-sync | No new commit required | Remove unchanged sources | 0 if cleanup completes |
| Any source is invalid, unreadable, or resolves to no match | Refuse before maintenance | Retain all | 2 |
| Evidence-integrity refusal or stale preview guard | Refuse before import writes | Retain all | 2 |
| Pre-sync, lock, write, verification, or commit fails | Existing failure/rollback semantics | Retain all | Existing 1/2 classification |
| Post-sync fails after local commit | Preserve successful local import | Retain all | 1 for `-D` |
| Any source changed before cleanup preflight | Preserve successful import | Remove none | 1 |
| Removal fails after earlier removals | Preserve successful import | Report removed, failed, and unattempted paths | 1 |
| Process dies after commit, before/during cleanup | Import remains; cleanup may be incomplete | Remaining files remain | Interrupted; retry remaining files |

For `-D -F` with no FILE arguments, refuse with a clear “deletion requires source files” message; plain `-F` keeps its existing source-free restore behavior. With FILE arguments, `-D -F` is valid, and deletion waits for the combined import/restore operation.

## Native source resolution

Keep this local to `bank import`; do not turn all Command Mode arguments into a shell.

- Expand only a leading `~/` using Bob's home-directory helper. Relative paths remain relative to the process working directory, which is the vault in Command Mode. Document that explicitly.
- Try a supplied path literally first. This preserves existing files whose names contain `[` or `*`, including paths a real shell has already expanded.
- Otherwise expand supported file patterns. For v1, ordinary `*`, `?`, and character classes within path segments are enough. Exclude recursive `**`, brace expansion, environment substitution, command substitution, pipelines, and `~otheruser`. No hidden-file matching unless explicitly named.
- Preserve the user's positional order. Sort each pattern's expansion deterministically; do not globally sort the entire batch, because input-file order is part of existing import ordering.
- Refuse an invalid pattern, any enumeration error, and each unmatched pattern even if other inputs matched. Never silently import/delete a partial selection because traversal errors were filtered away.
- Resolve once per invocation. Deduplicate repeated references to the same directory entry, preserving first appearance. Distinct files containing identical bytes remain distinct cleanup targets. Distinct explicitly selected hard-link names may both be removed; do not collapse them solely by inode.
- Preserve paths as `PathBuf`/`OsString` through IO. Display escaping is separate. Literal non-UTF-8 paths can retain existing support; if the chosen glob API requires UTF-8, refuse unsupported patterns rather than using lossy conversion.

A maintained glob library is reasonable. [`glob_with`](https://docs.rs/glob/latest/glob/fn.glob_with.html) supports relative/absolute patterns, reports invalid patterns, and yields alphabetically ordered paths. Configure and test the intended grammar; do not assume library defaults equal the desired policy. The current Cargo manifest has no direct glob dependency. A custom shell parser would be disproportionate.

Command Mode strips quote provenance before bob receives argv. Therefore quoting a wildcard protects spaces but cannot mean “disable Bob's pattern expansion.” The literal-existing-path rule handles normal literal names; document this small distinction instead of claiming full shell compatibility.

## Guarded cleanup implementation

Keep parsing/planning pure and add a small bank-specific source/cleanup layer. The operational object should contain the absolute source path, display path, parsed digest, file identity, and necessary metadata. On supported Unix hosts, capture device/inode identity from the opened file, not just `mtime` and size. Read through that handle, reject non-regular files for `-D`, and check metadata around the read. Avoid following a leaf symlink; avoid blocking indefinitely on a FIFO substituted between inspection and open.

The sequence should be:

```text
resolve inputs → capture source identities/bytes → parse every input
    → validate optional preview source fingerprint
    → maintenance lock + pre-sync → fresh whole-batch plan
    → check deletion eligibility → install + verify + scoped commit
    → post-sync → validate every source again → remove captured paths
    → report import outcome and cleanup outcome separately
```

All final source checks happen before the first removal. Compare identity and a fresh content digest to what was actually parsed. If any input is missing, replaced, changed, unreadable, or has become a symlink, retain every still-present source. Do not re-expand the wildcard at deletion time.

Then check each entry immediately before its removal. On the first unexpected removal failure, stop, retain the rest, and report exact counts and paths. If an entry disappeared concurrently, report it as absent, not “deleted by bob”; conservatively finish with an incomplete-cleanup result rather than hiding the race. Never undo committed bank rows because external cleanup failed.

Prefer directory-handle-relative operations where practical, so a parent-path replacement cannot redirect a deletion. On Unix, `unlinkat` can operate relative to an opened directory. It still does not provide atomic “unlink only if this inode matches” semantics. A final metadata/hash check followed by unlink narrows ordinary races; it does not eliminate an adversarial swap or concurrent in-place write in that interval. State this limit honestly. A hostile-directory guarantee would require a separate claim/quarantine and recovery design, with its own observable renames and failure modes; it is not justified for this personal Downloads workflow.

Keep cleanup outside `PlannedTxn.files`, appends, and rollback. Ideally retain the maintenance lifecycle through the eligibility decision and cleanup using a narrowly scoped post-success hook, returning a cleanup result alongside the successful import result. Do not make a callback error discard the commit context or trigger vault rollback. The vault lock coordinates Bob processes; it does not lock Downloads against browsers or other programs.

For no-op imports, explicitly validate the evidence used to declare them successful before authorizing deletion. `apply_and_commit` currently returns early for a no-op before validating dependencies. A non-destructive replay can tolerate that boundary more easily than a destructive one. Avoid inventing empty commits just to make `commit.is_some()` true.

Crash behavior remains simple: before commit, no source removals; after commit, retrying remaining inputs is safe through transaction identity deduplication. Do not add automatic background deletion, permanent cleanup manifests, or a new raw-export journal just for this option. Removal is a normal filesystem unlink, not secure erasure or proof that backups/hard links contain no copy.

## Make preview mean something

I recommend a stateless **expected-source fingerprint**, carried only when applying a preview. Compute it from a versioned, unambiguous encoding of the ordered resolved paths, file identities, content digests, vault identity, and import-affecting arguments (`account`, restore, deletion). At apply time, resolve/read again and compare before entering maintenance. New matches, removed matches, or changed contents produce “Sources changed; preview again.” No source list is inferred from a diff or human output.

This fingerprint binds source selection and bytes, not the entire vault transaction. The existing importer still replans the synced vault. Document that distinction rather than promising exact replay of every previewed row after intervening vault edits.

There is already a suitable host-local machine channel: `BOB_RUN_RECEIPT`. The [runner currently writes an atomic receipt](https://github.com/bobs-org/bob-cli/blob/e7aa392d688ea250ada1a6d732e3f27ed0e67c9c/src/runner.rs#L1497) with exit code and finish time; the plugin's [receipt reader](https://github.com/bobs-org/bob-plugins/blob/febfc6bacd3ef9895aa1a0c24bff3781ecbb95de/plugins/bob-command-mode/src/050-run-store.js#L110) accepts additive fields. Add typed bank-import preview metadata there and expose the same fingerprint in JSON output. A narrow `bank-import` adapter can convert validated metadata into an internal `--expected-sources` argument, reusing the existing adapter carry mechanism. Keep normal human output readable; do not print an opaque token as a user-facing step.

This is a proposed protocol extension, not an existing capability. The runner must pass receipt metadata through both normal completion and reload/adoption classification, persist the carry, and treat a missing/malformed fingerprint as unavailable Apply. [Existing task-reroll carry](https://github.com/bobs-org/bob-plugins/blob/febfc6bacd3ef9895aa1a0c24bff3781ecbb95de/plugins/bob-command-mode/src/130-adapters.js#L130) is a useful implementation precedent.

Handle all ways to execute the command:

- Preview Apply, including the toast action and reload recovery, must pass the expected fingerprint.
- A fresh Ctrl+Enter “run now” explicitly accepts the current source set but still uses all batch and cleanup checks.
- Rerunning a completed command or resuming a sequence must not accidentally reuse a stale preview fingerprint. A fresh destructive rerun should return to preview unless the user explicitly chooses the existing run-now/sequence confirmation path.
- An older plugin must not silently apply an unguarded destructive preview. A concrete compatibility approach is to require either the expected fingerprint or an internal explicit-current-source marker for real `-D` invocations using the Command Mode receipt channel. Updated run-now and confirmed-sequence paths supply that marker; old clients receive an upgrade/preview message. Scope and document that client contract before shipping it.

This coordinated plugin work is the largest addition to a naive one-flag implementation. It is justified because the user explicitly wants an Obsidian preview-driven workflow. No changes to the Mac Capture application are indicated by this feature.

## Output that is calm, clear, and attractive

Keep the existing per-file rows, counts, diffs, and review hint. Add a short cleanup summary with enough contrast to notice the destructive choice, not a new modal ritual. Show all source basenames in a compact list; use full paths when ambiguous and in diagnostics. Preserve complete machine-readable paths in JSON.

A preview could lead with:

```text
Bank import · 3 files
42 new · 8 already recorded

After a successful import, permanently delete these 3 source files:
  checking.qfx
  savings.qfx
  card.qfx

Dry run — nothing written or deleted
```

Success:

```text
Imported 3 files · 42 new · 8 already recorded
Deleted 3 source files
```

Successful no-op cleanup:

```text
All transactions already recorded · no new import commit
Deleted 3 source files
```

Incomplete cleanup:

```text
Import saved · source cleanup incomplete
Deleted 2 of 3 files
Kept ~/Downloads/card.qfx — permission denied
Fix the permission, then import the remaining file again with -D.
```

Post-sync hold:

```text
Import saved locally · sync failed
Kept all 3 source files
Run bob vault-sync, then retry import with -D.
```

Use the existing Styler: green for completed work, amber for retained sources needing attention, red for refusal/errors. Meaning must survive `NO_COLOR`, pipes, and the Command Mode pager. Finish with the useful bank review hint on success; on incomplete cleanup, prioritize the retention/retry summary so the generic last-line outcome cannot misleadingly suggest everything completed. A typed adapter should distinguish “import failed” from “import saved; cleanup incomplete.”

Extend schema 1 additively. Suggested fields are `import_ok` and `cleanup` containing `requested`, `status`, counts, and per-source outcomes (`planned`, `deleted`, `retained`, `failed`, `not_attempted`, `absent`) plus stable reason codes. Retain existing `changed` as the vault-plan meaning: an all-seen cleanup can legitimately have `changed: false` and deleted sources. On cleanup failure, top-level `ok: false` and exit 1 describe the entire requested operation while `import_ok: true`, existing commit details, and the complete import summary show what succeeded. Use a cleanup-specific error code, not the existing `bank_import_*` prefix that currently maps all such failures to exit 2.

Do not log raw bank content or account/routing numbers in new metadata. File paths already appear in import output; keep source fingerprints and richer path metadata host-local rather than adding them to the vault journal.

## Implementation scope and validation

The narrow source changes are in `bank/cli.rs`, `bank/import_run.rs`, and a focused source-resolution/cleanup module. Preserve `import_plan.rs` as a planner, with explicit deletion-eligibility classification around its findings. A small lifecycle integration may be needed to retain successful context through cleanup. Extend the catalog, receipt output, and Command Mode adapter/carry paths together for preview binding.

Update the clap help and examples, the import contract in `docs/bank.md`, the Command Mode guide, generated CLI reference, and the catalog/receipt protocol documentation. Keep options alphabetized (`account`, `bob-dir`, `delete`, `dry-run`, `force`, `format`, `help`). Generate docs with `just docs-gen`; verify with `just docs-check`. Do not manually edit generated CLI reference or release version/changelog. Plugin implementation must follow its fragment build/test workflow and deployment instructions.

The most valuable tests assert behavior and preserved files, not helper call order:

| Area | Required cases |
| --- | --- |
| Flag compatibility | `-D` and `--delete`; default retention; `-D -d` preserves every byte; existing `-d` and `-F`; source-free `-D -F` refusal |
| Batch guarantee | Several files succeed; final file malformed; unresolved account; duplicate-identity conflict; write/verify/commit failure; no source deleted on any batch failure |
| Valid success variants | All-seen replay; zero-new matched files; before-start-only file; valid empty OFX statement; mixed QFX/OFX/CSV; overlapping duplicate content |
| Resolution | Raw `~/Downloads/*.qfx` argv without a shell; paths with spaces; literal bracket names; unmatched pattern alongside a matched file; traversal error; deterministic ordering; repeated same path |
| File safety | Symlink and FIFO refusal before read/delete; vault-resident source refusal; same-size same-mtime replacement with different inode; in-place byte changes; disappearing file; parent-path replacement |
| Lifecycle | Post-sync failure preserves local commit and all sources; successful no-op with skipped post-sync still cleans up; integrity warnings block only destructive mode; ordinary warnings remain nonfatal |
| Cleanup failure | Fault-injected failure on second unlink; first removed, remaining preserved, import committed, structured partial result, exit 1; safe retry of remaining files |
| Preview and UI | New glob match after preview; changed source bytes; expected guard survives Apply/toast/reload; missing guard fails closed; explicit run-now works; fresh rerun does not reuse stale guard; coherent human/JSON outcomes |
| Interruption | Kill after commit and before cleanup; interrupt mid-cleanup; retry imports remaining files without duplicate rows |

Use temporary exports and temporary syncable vaults with local remotes, following existing tests. Inject cleanup failures deterministically instead of relying only on chmod tests that behave differently as root. Run focused bank/lifecycle/plugin tests and required repository checks; exercise the actual typed command through the Command Mode harness with a temporary HOME/Downloads fixture supplied by the test environment. A real desktop smoke test should verify preview legibility and Apply feedback after those tests pass.

## Recommended solution

**Ship `-D, --delete` as an explicit, guarded cleanup phase after a complete batch import, with native bank-input globbing and source-bound Command Mode Apply.** Treat already-recorded inputs as successful; never infer success from “new rows” or the presence of a fresh commit. Retain all sources on failed imports, failed sync, stale source snapshots, or unreliable journal evidence. Report partial deletion honestly and preserve the successful import for retry.

Keep the everyday interaction small: type `bank import -D ~/Downloads/*.qfx`, review a compact preview that names the files, apply once, and see a clear import-and-cleanup result. The complexity belongs in source identity checks and failure handling; the user should experience one dependable completion of the download ritual.
