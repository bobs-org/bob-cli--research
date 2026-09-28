# Research: `bob randomize` for due prioritized tasks

Date: 2026-09-28  
Researcher: cdx  
Code reviewed: `bob-cli` at `ec3132963f89`

## Executive summary

This is a good feature if it is treated as an explicit backlog-triage operation rather
than ordinary scheduling. The repository already has almost all of the hard pieces:
priority windows and seeded rolls, Tasks-plugin status classification, Markdown-aware
task scanning, guarded multi-file replacement, a shared vault-maintenance lock, and a
Git reconciler that handles remote races and conflicts. The safest implementation is to
compose/refactor those pieces. A new ad-hoc regex walker followed by `git add -A && git
commit` would recreate solved problems and would be the wrong design.

My recommended behavior is:

1. Under the shared maintenance lock, first run the existing vault-sync reconcile core
   so the command plans against current remote state and begins from a clean worktree.
2. Load the priority configuration once, scan active Markdown notes, and select only
   recognized nonterminal tasks having exactly one valid task-level `scheduled` field
   whose date is `<= today` and exactly one priority field whose value maps uniquely to
   a configured priority level.
3. Give each selected task its own deterministic derived roll from one run seed, with
   each configured `[min_days, max_days]` interpreted inclusively relative to today.
4. Plan all edits before writing. Replace only the schedule value bytes, preserve the
   field delimiter/spacing/line ending, and change the checkbox to Blocked (`[?]`) when
   the new date is future. If the task already owns a direct-child Schedule Log, prepend
   an old-date-to-new-date roll entry; do not create hundreds of new log sections.
5. Apply the batch through a generalized version of the existing guarded writer. Then
   invoke vault-sync's existing-lock core again with a descriptive commit message. This
   creates one content commit for the randomization and lets the canonical reconciler
   handle fetch/merge/push and push races.

Ship `--dry-run`, `--format json`, and `--seed`; honor `BOB_NOW`,
`BOB_CONFIG_FILE`, and `BOB_PRIORITY_ROLL_SEED`. Strictly abort before writing on
ambiguous/malformed candidate metadata or unmapped priority values rather than silently
leaving part of the backlog behind.

## What already exists

### Priority configuration and randomness

`src/native/config.rs` already models a priority property and its levels, validates
nonnegative inclusive `min_days`/`max_days`, implements `PriorityLevel::roll_offset`,
resolves the standard config path, and honors `BOB_PRIORITY_ROLL_SEED` (roughly lines
11-182 and 243-406). The currently documented deployment is:

| Label | Stored value | Inclusive day window |
| --- | --- | ---: |
| P1 | `high` | 2-7 |
| P2 | `medium` | 8-30 |
| P3 | `low` | 31-90 |
| P4 | `lowest` | 91-365 |

The docs explicitly define a task without a priority field as implicit P0 and say there
is no `p:0` (`docs/capture.md`, around lines 237-281). That aligns well with the stated
goal: selecting tasks with a priority field naturally leaves P0 tasks alone.

Two small additions are needed. `PriorityProperty` can currently look up only by ordinal
(`level(number)`), while existing tasks store the configured `value`; add lookup by
value. Also validate that stored values are unique, because a duplicate makes reverse
mapping ambiguous. Load and validate the file once per command, not once per task.

For batches, `capture.rs` already derives per-item seeds from one base seed rather than
reusing the same seed (`item_roll_seed`, around line 1639). `randomize` should share a
public version of that helper. Deriving from the base seed plus a stable task identity
(vault-relative path plus original line digest) is better than scan index alone: adding
an unrelated earlier file will not reshuffle every later task in a seeded run.

### Task and Markdown semantics

`src/native/note_tasks.rs` provides a useful shared model. It reads the Obsidian Tasks
settings, classifies open versus terminal statuses, skips strict YAML frontmatter and
fenced code, retains line/block extents, and uses a line digest for stale-safe identity
(notably lines 15-38, 88-157, and 192-265). `TaskStatusType::is_open` includes TODO,
In Progress, and On Hold while excluding Done, Cancelled, and Non-Task
(`src/native/task_status_hooks.rs`, around lines 481-521).

There are nevertheless multiple field parsers with different policies:

- `task_status_hooks.rs` parses trailing Dataview properties and hard-codes the five
  standard priority values (around lines 2513-2635).
- `capture_task_toggle.rs` recognizes bracket and parenthesis schedule fields anywhere
  on the physical task line and deliberately refuses ambiguous duplicate schedules
  (around lines 1379-1446).
- `note_tasks.rs` removes generic bracket fields from displayed descriptions but does
  not retain property names, values, or byte spans.

Do not add a fourth incompatible parser. Extract a small reusable inline-property
scanner that returns delimiter, key, trimmed value, and byte spans. Extend the shared
task scan (or layer a randomize planner on its `NoteTask` line identities) so it gains
the safety of frontmatter/fence exclusion and the exact spans needed for byte-preserving
replacement.

The vault walk should be sorted and should use the established exclusions: `done`,
dot-directories, `.git`, `.obsidian`, `_conflicts`, `_generated`, and `_templates`.
`task_status_hooks.rs` and `collect_done.rs` already demonstrate that traversal policy
(around `task_status_hooks.rs:2473-2512` and `collect_done.rs:2096-2160`). Project-level
frontmatter such as `scheduled: ...` is not task-level metadata and must remain out of
scope.

### Status and schedule-log consistency

`task-status-hooks` considers a task scheduled later than the effective day to be
derived-Blocked, overriding Ready, Next, or In Progress; today and earlier are not
future (`src/native/task_status_hooks.rs`, around lines 1302-1388 and 1510-1530). Merely
changing the date would leave the note temporarily inconsistent until another hook run.
The batch should therefore set an eligible task to `[?]` when its newly rolled date is
strictly future, using a shared validation/helper for the configured Blocked status.
When a configured window allows day zero and the roll is today, do not force Blocked.

Schedule history is intentional in this project. `capture_schedule_log.rs` contains
byte-compatible reason and entry formatting, while task-toggle logic prepends a history
entry only when a direct-child Schedule Log already exists. Follow that low-noise
precedent: for a P2 task, for example, record `old -> new` with a reason like
`🎲 P2 · in **N** (8–30) days`, using the repository's actual Unicode formatter. Do not create
a Schedule Log section on every old task. This preserves existing audit trails without
turning a cleanup command into a large structural rewrite.

### Safe multi-file writes

The strongest reusable implementation is `src/native/task_status_hooks_write.rs`,
introduced specifically to protect live vault notes from concurrent editor saves. It:

- captures file identity and bytes;
- acquires the same maintenance lock as vault-sync;
- detects scan-set or content changes between planning and replacement;
- stages unique same-directory temporary files and preserves mode/xattrs;
- writes recovery originals/proposed copies and a manifest; and
- stops safely with explicit applied/deferred paths if a later replacement cannot be
  completed.

The relevant entry points are around lines 417-537 and the preflight/staging/apply path
around lines 600-850 and 1028-1310. It is currently branded and parameterized for
`task-status-hooks` (`TOOL`, state directory, temp prefix, and messages), so the right
move is to extract a generic guarded note-batch module with a tool identifier, then keep
thin command adapters. Copying only `fs::write` or capture's simpler batch writer would
lose the concurrency protections that this repository recently added on purpose.

The SASE/Bob lock coordinates Bob commands, not Obsidian itself, so guarded snapshots
remain necessary even while the lock is held.

## Git and vault-sync integration

`vault-sync` is now the canonical full-vault Git reconciliation path. It acquires the
shared lock, stages the worktree, commits, fetches/reconciles `origin/master`, retries
non-fast-forward pushes, quarantines conflicts, and records status
(`src/native/vault_sync.rs`, especially lines 181-219, 256-325, and 1019-1070).
`ob::try_acquire_lock` supplies the shared exclusive lock and honors
`BOB_VAULT_SYNC_LOCK_FILE` (`src/native/ob.rs`, around lines 123-211). The removal of the
old bulk-commit command in commit `4051bf5` reinforces that new commands should not grow
another independent full-vault Git workflow.

I recommend a lock-held reconcile/mutate/reconcile sequence, analogous to `bob nightly`:

```text
acquire shared maintenance lock
  -> vault-sync using existing lock (clean/publish/fetch/reconcile)
  -> rescan and build complete randomize plan
  -> guarded batch write
  -> vault-sync using existing lock and a randomize commit message
release lock
```

Expose an internal vault-sync entry point that accepts the existing-lock run options,
including a commit message such as:

```text
bob randomize 2026-09-28: 47 tasks in 12 files
```

Why this is preferable:

- The leading sync prevents randomizing stale task lines and sharply narrows the remote
  conflict window.
- The leading sync also commits pre-existing loose vault edits separately, so the
  trailing commit normally contains only this batch.
- The shared lock prevents the 15-second background vault-sync job from entering during
  either note replacement or Git operations.
- The trailing sync owns remote races, merge recovery, conflict quarantine, status
  reporting, and push retry. No duplicated `git fetch/merge/push` policy is needed.
- All randomize file changes are produced before the trailing sync, so they enter one
  content commit. A later reconcile merge may add a merge commit, but does not split the
  randomization itself.

There is no perfect transaction across an editor, many filesystem replacements, Git,
and a network remote. If the trailing sync fails after the files were safely written,
report a nonzero "changes applied, publication pending" result and leave them for the
next vault-sync; do not roll back valid note edits merely because the network failed. If
the leading sync fails, abort before changing any task. If guarded application detects
a concurrent edit, report recovery/applied/deferred paths and do not start the trailing
sync until the state is understood.

A scoped `git commit -- <touched paths>` is a possible alternative and is used by
`move-done-tasks`, but it would require new reconciliation/push coordination and risks
semantic drift from vault-sync. Given the requested compatibility, the two vault-sync
calls are the cleaner default. After a successful leading sync, broad staging in the
trailing sync should be narrowly scoped in practice; guarded scanning further prevents
concurrent Markdown saves from being silently folded in.

## Proposed command contract

```text
bob randomize [--dry-run] [--format human|json] [--seed N]
```

Defaults and eligibility:

- Vault: `BOB_DIR` / `~/bob`.
- Effective day: `bob_env::current_datetime().date()`, thereby honoring `BOB_NOW` and
  legacy `DATE` exactly like the rest of Bob.
- Config: the existing `BOB_CONFIG_FILE` / XDG / `~/.config/bob/config.yml` chain.
- Eligible: a recognized open Tasks task in the active vault scan with exactly one
  valid inline schedule `<= today`, exactly one configured priority property, and a
  priority value mapping to exactly one configured level.
- Ineligible: implicit P0 (no priority property), future tasks, terminal/non-task or
  unrecognized statuses, project frontmatter, fenced examples, generated/conflict
  trees, and `done/` archives.
- Roll: one inclusive priority window relative to today per task. A task can roll the
  same date it already has; count that as eligible but unchanged and do not manufacture
  a content edit.
- Seed: `--seed` takes precedence; otherwise honor `BOB_PRIORITY_ROLL_SEED`; otherwise
  generate one seed for the run and print/return it. JSON must include it.
- Real runs reconcile before and after the batch. `--dry-run` performs no file, Git,
  network, state-file, or recovery-directory writes; it previews the current local
  checkout. A seeded preview can be reapplied exactly if the vault snapshot is unchanged.

Human output should summarize effective date and seed, scanned/eligible/changed task and
file counts, counts per priority level, per-task `path:line old -> new`, skipped no-op
rolls, and commit/push outcome. JSON should expose the same data with stable field names.

Errors should be fail-before-write for duplicate schedule/priority fields, invalid dates
on otherwise candidate-looking prioritized tasks, unknown priority values, duplicate
configured values, date overflow, invalid config, missing Blocked status when one is
needed, or unreadable/non-UTF-8 candidate files. Silently skipping these cases would
make "all" false while giving the user false confidence.

## Critique and requirement adjustments

The idea is useful, but random dates are triage, not prioritization. They reduce the
visual pressure of an overdue pile and guarantee periodic resurfacing, but they also
erase the semantic meaning of a schedule if that field sometimes means a genuine
deadline. Repeated reruns can indefinitely defer tasks, and independent uniform rolls
can create clusters. The original creation date, priority, Schedule Log (where already
present), Git commit, and reported seed provide enough auditability to make that risk
acceptable for a personal backlog.

I would keep the requested independent random rolls rather than replace them with even
spacing, because the configured windows already express the policy and the seed makes a
batch explainable/reproducible. If clustering becomes annoying, a later optional
"balanced" strategy could shuffle tasks then distribute them across each level's days;
it should not silently change the initial contract.

I recommend making these adjustments explicit:

1. **"All tasks" means open task-level items only.** Completed/cancelled tasks and note
   frontmatter do not participate.
2. **P0 remains implicit and untouched.** Presence of a recognized configured priority
   value is the exact lower-priority predicate.
3. **Ambiguity is fatal, not skippable.** The command should either truthfully process
   the whole eligible set or make the data problem visible before writing.
4. **Status is reconciled in the same batch.** A newly future task becomes Blocked so
   note state immediately matches existing hook semantics.
5. **Existing logs are updated, new log sections are not mass-created.** Git plus command
   output is the batch-level audit trail.
6. **A run seed is first-class.** This improves testing, dry-run usefulness, incident
   diagnosis, and user trust without weakening independent per-task rolls.
7. **Git/network failure semantics are explicit.** Pre-sync failure means no mutation;
   post-sync failure means the safe local mutation remains pending publication.

I would not default to excluding Next or In-Progress tasks: the request specifically
defines lower priority by presence of the priority property, and silently preserving
some such tasks would violate "all." If that proves too aggressive, add explicit future
filters (`--exclude-status`, `--priority`) rather than changing the base behavior.

## Implementation outline

1. Add `Randomize` to `NativeCommand`, add alphabetically sorted `randomize` registration
   in `runner.rs`, create `src/native/randomize.rs`, and document it in top-level help,
   README, and a focused command doc.
2. Extend `config.rs` with unique value validation, reverse lookup, and a reusable
   per-item seed derivation helper.
3. Extract a shared inline Dataview-property scanner and reuse the existing note-task
   status/settings model. Do byte-range replacements in descending order per file.
4. Generalize `task_status_hooks_write.rs` into a command-parameterized guarded note
   batch module; keep the current hook behavior/tests intact.
5. Extract/share the Blocked-status validation and the "existing Schedule Log entry"
   insertion helper. Compose schedule, status, and optional log edits into one postimage
   per file before guarded application.
6. Add an existing-lock vault-sync entry point accepting a custom message, and run the
   leading/trailing cycles described above. Do not shell out to `bob vault-sync` while
   holding the same lock.

## Test plan

At minimum, unit/integration tests should cover:

- due yesterday/today selected; tomorrow unchanged; missing priority/P0 unchanged;
- every configured level stays inside inclusive bounds, including fixed and day-zero
  windows, with independent deterministic results from a fixed seed;
- arbitrary configured stored values and property name; unknown/duplicate values fail;
- completed, cancelled, non-task, unrecognized, frontmatter, fenced, `done/`, hidden,
  generated, and conflict-copy content remains unchanged;
- bracket and parenthesis properties, whitespace preservation, CRLF/no-final-newline,
  multiple candidate lines in one file, malformed dates, and duplicate fields;
- status changes only for newly future eligible tasks and validates the Blocked status;
- existing Schedule Log gets one correctly formatted old-to-new entry; absent log stays
  absent; multiple tasks' insertion offsets do not interfere;
- dry-run and JSON make no writes and expose seed/plan; a fixed seed yields exact parity
  between preview and apply on an unchanged snapshot;
- lock contention, an editor save between scan/stage/replace, scan-set changes, staged
  write failure, partial apply, and recovery evidence;
- leading sync remote-only changes, pre-existing local dirty files, one descriptive
  randomize commit, push races, post-sync failure, and background vault-sync contention;
- top-level help ordering and native-only dispatch.

## Recommended solution

Implement `bob randomize` as a strict, seeded, plan-then-apply vault transaction built
from existing Bob primitives: shared task/property parsing, configured priority reverse
lookup, guarded multi-file writes, the shared maintenance lock, and leading/trailing
vault-sync reconciliation. Reschedule every eligible nonterminal prioritized task from
today, immediately mark future rolls Blocked, append history only to Schedule Logs that
already exist, and publish the batch in one descriptive commit through vault-sync.
Provide `--dry-run`, JSON, and an explicit seed from day one. This delivers the requested
one-command backlog reset while preserving determinism, auditability, editor safety,
and compatibility with the continuously running vault-sync process.
