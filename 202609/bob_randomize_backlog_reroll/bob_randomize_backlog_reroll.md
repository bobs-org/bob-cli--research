# `bob randomize`: bulk re-roll of due prioritized tasks (consolidated report)

Lead researcher consolidation · 2026-09-28 · `bob-cli` at `ec31329`

Sources: five independent reports ([cdx](bob_randomize_backlog_reroll__cdx.md),
[cld](bob_randomize_backlog_reroll__cld.md), [grk](bob_randomize_backlog_reroll__grk.md),
[mus](bob_randomize_backlog_reroll__mus.md), [gem](bob_randomize_backlog_reroll__gem.md)).
I also re-checked the disputed points against `bob-cli` source, the `bob-plugins` picker,
and read-only scans of the live `~/bob` vault and its git log.

## TL;DR

- **Build it. It's a good idea.** `bob randomize` is the vault-wide, headless version of
  a gesture Bob already has: the Obsidian picker's same-level 🎲 "roll" (317 such
  Schedule Log entries in the vault today). All five reports agree, and so do I. Most of
  the parts already exist: priority windows and seeded rolls (`config.rs`), Schedule Log
  formatting (`capture_schedule_log.rs`), the guarded multi-file writer
  (`task_status_hooks_write.rs`), the pure grouping transform (`task_status_groups.rs`),
  the shared maintenance lock (`ob.rs`), and the in-process vault-sync cycle
  (`vault_sync::run_cycle_with_existing_lock`, used by `nightly`).
- **Today it would touch 224 tasks in 28 notes.** That's 87 P1, 132 P2, 5 P3 and 0 P4;
  130 of the tasks are in `sase.md`. Every one of them already has a
  `🗓️ **SCHEDULE LOG**`. None has a `due` date or recurrence, and none sits in a daily
  note. Two are active (1 Next, 1 In Progress).
- **Changing only the dates is not enough.** A future `scheduled` date makes
  `task-status-hooks` flip the task to Blocked `[?]` and move its block into the note's
  `### Blocked` group. On the Mac that happens within 15 minutes, as a second commit
  touching all 28 notes. That second commit also stops `git revert` of the randomize
  commit from applying cleanly. So randomize should set the status, add a log entry, and
  regroup, all in memory, then write each note once.
- **Git design:** do what `bob nightly` does. Take the lock, run vault-sync, write the
  edits, make **one scoped commit** of only the files randomize wrote, run vault-sync
  again, then release the lock. vault-sync stays the only code that runs `git add -A`,
  merges, or pushes.
- **The biggest weakness of the plan is P1.** Randomizing doesn't free up any time. The
  85 Ready P1s re-rolled into the 2–7 day window come back at about 19–20 tasks a day
  from Sep 30 to Oct 5 (existing load plus the re-rolls). That lands inside the "focus on
  P0 for days or weeks" period this command is meant to protect. I recommend one extra
  optional flag, `-u/--until DATE|+N`: it clears prioritized tasks scheduled through
  `DATE` and rolls their windows from `DATE`. Without the flag the command does exactly
  what you asked for.

## 1. What exists today (verified)

| Need | Existing piece | Gap |
| --- | --- | --- |
| Priority windows | `config.rs`: `load_priority_property`, `PriorityLevel::roll_offset` (inclusive splitmix64, l.139), `roll_seed` (honors `BOB_PRIORITY_ROLL_SEED`, l.154) | Lookup is by ordinal only (`level(n)`, l.97). Add a value-to-level lookup (`high`→P1) and a check that values are unique. The missing-config error says "p:<N> needs…"; make it command-neutral. |
| Per-item seeds | `capture.rs:1639` `item_roll_seed(base, index)` (private) | Derive from task identity instead of index (§4, row 11). |
| Scheduled field parsing | `capture_task_toggle.rs:1396` `scheduled_field_matches` (bracket and paren forms, counts duplicates), `:1417` `parse_strict_calendar_date` (both private) | Lift into a shared task-field module; don't write a fourth parser. |
| Task scan | `note_tasks::scan` / `read_settings`: Tasks statuses, global filter `#task`, frontmatter and fence skipping, block extents, line digest | Does not keep property byte spans; add them. |
| Status flip | `capture_task_toggle.rs:1360` `set_task_line_status` (pub(crate)) | — |
| Schedule Log | `capture_schedule_log.rs`: `MARKER_TEXT`, `entry_text`, `priority_roll_reason`, `plan` (byte-matched to the picker) | Needs a same-level roll reason and an "insert under existing marker or create marker" planner. |
| Grouping | `task_status_groups::transform` (pub(crate), l.344) | `task_group_classification` (l.3457), `task_grouping_eligible` (l.3470), `validate_blocked_status` (l.1963) and `markdown_files` (l.2473) are private to `task_status_hooks.rs`. |
| Guarded writes | `task_status_hooks_write.rs`: `capture_required`, `planned_write`, `apply_plan`. Provides a 2 s quiet period, byte and inode preflight, staged temp files plus atomic renames, a recovery manifest, and partial-apply reporting. `apply_plan` does **not** take the lock; the caller does (hooks l.974). | `TOOL`/`STATE_SUBDIR` are hard-coded to `task-status-hooks`; parameterize them. |
| Lock | `ob::try_acquire_lock` / `acquire_lock` (`flock` on `bob_sync.lock`; `acquire_lock` returns exit **0** when the lock is contended) | An interactive command needs a bounded wait, not a silent exit 0. |
| Git | `vault_sync::run_cycle_with_existing_lock(&ChildEnv) -> i32` (l.189). It uses `RunOptions::default()` (no message, not quiet). The cycle recovers any interrupted merge, runs `add -A .`, commits, fetches if the remote changed, fast-forwards or merges, keeps the **remote** copy on conflict and puts the local copy in `_conflicts/`, then pushes with up to 3 retries. | Add a variant that returns a report (conflicts, pushed, SHAs) so randomize can print exact results. |

The live vault today (my scan; it matches the cld and grk counts):

| Metric | Value |
| --- | --- |
| Open `#task`, one valid `scheduled` ≤ today, one `priority` | **224** in 28 notes (222 Ready, 1 Next `[*]`, 1 In Progress `[/]`) |
| By level | 87 P1 `high` · 132 P2 `medium` · 5 P3 `low` · 0 P4 `lowest` |
| Hot notes | `sase.md` 130 (Ready intake is lines 17–694; `### Blocked` group at l.846) · `cash.md` 14 · `bob.md` 12 |
| Already has a Schedule Log | 224 / 224 |
| Has `due`/📅, `repeat`/🔁, or nested under another task | 0 / 0 / 0 |
| Due P0 (no priority), which this command must leave alone | 40 |
| Existing load in the P1 window (Sep 30 – Oct 5) | 32 tasks, about 5 per day |
| Commits in the vault over the last 3 days | 189, all but one from the Mac's vault-sync (`vault(kellys-*)`) |
| 🎲 reasons in Schedule Logs | 344 `Px → Py` · 317 `Px roll` · 6 bare `Px` |

## 2. Critique: is this a good idea?

**Yes.** Rewriting `scheduled` is better than a read-only "P0 focus view". `scheduled` is
what the vault uses to decide when you see a task. Blocked status, grouping, dashboards
and `projects list` all read it. A view filter would leave 200+ tasks overdue in every
project intake, and they would still be there when you stopped filtering. Other tools
converge on the same move: Todoist's bulk "Reschedule overdue", FSRS Helper's "Postpone"
for Anki backlogs, and "to-do list bankruptcy". Randomize is bankruptcy that keeps the
tasks and tells you when each one comes back. Because it's seeded and logged, you can
also audit and reproduce every roll.

Real concerns, most important first:

1. **It doesn't free up any time, and P1 shows it most.** P1 means "2–7 days". Re-rolling
   85 overdue P1s puts about 14 tasks a day on top of the existing ~5 during exactly the
   period you wanted for P0 work (cld simulated a 95th-percentile peak of about 29 in a
   single day). Load-aware placement flattens P2 but can't fix a 6-day window. Also,
   87 overdue P1s is a warning in itself: either the P1 window is too short for how many
   tasks you actually get through, or many of these are really P2s. Randomize should put
   that pile-up in front of you (a histogram in the dry-run) rather than hide it.
2. **Tasks can be deferred forever, and you lose the "how overdue" signal.** "Scheduled 5
   weeks ago" tells you something. After a bulk roll every task looks freshly scheduled,
   and running it repeatedly can hide the same task indefinitely. The Schedule Log fixes
   both. Give bulk rolls their own reason text so you can later count "deferred in bulk 3
   or more times without review, so cancel or demote".
3. **The side effects are bigger than the date edits.** The Blocked flip plus moving the
   block into `### Blocked` turns 224 one-line edits into a structural rewrite of 28
   notes, including the one you edit most. Hooks would make the same move anyway, so the
   only question is which commit it lands in (§5).
4. **Work you're doing today must not move.** Next, In Progress, and tasks linked under
   today's open Pomodoros mean "today". Rolling them would fight the ledger (the picker
   has to prune Pomodoro links when it defers a task).
5. **Races with other machines.** The lock only covers one host. If the Mac pushes an
   overlapping edit in the few seconds between the two syncs, vault-sync's policy keeps
   the Mac's copy of that note and moves randomize's version to `_conflicts/`. Nothing is
   lost, and re-running converges because the missed tasks are still due.
6. **`scheduled` isn't always a soft date.** If a task also has a real `due` date or a
   recurrence rule, re-rolling `scheduled` can push it past its deadline or shift its
   recurrence. No candidate has either today, so skipping them costs nothing now and
   protects you later.

**Would I take a different approach?** Not a different mechanism: a native, seeded bulk
roll through the existing primitives is right. My changes are (a) settle status and
grouping in the same commit, (b) exclude active work, (c) add `--until` so the command
serves the "focus for N days" use case directly, and (d) show the resulting load before
anything is written. Keep it **manual only**: every report rejects putting it on
`nightly`, because silent nightly deferral would erase the overdue signal without you
ever looking.

## 3. Requirement adjustments (explicitly called out)

| # | Adjustment | Why |
| --- | --- | --- |
| R1 | **Candidates:** open Ready `[ ]` or Blocked `[?]` `#task` lines (Tasks global filter) with exactly one strictly valid inline `scheduled` ≤ cutoff and exactly one `priority` whose value matches a configured level. | "Prioritized" means a configured priority value; P0 (no field) is left alone by construction. Only task-level inline fields count; project frontmatter never does. |
| R2 | **Exclude** Next `[*]`, In Progress `[/]`, tasks block-linked under today's open Pomodoros, done/canceled/unknown statuses, `^prj` lifecycle lines, fenced/frontmatter content, and the standard walker exclusions (`done/`, dot-dirs, `_conflicts`, `_generated`, `_templates`). | They represent today's work or aren't tasks. 15 done/canceled tasks in the vault still have due dates and priorities. |
| R3 | **Skip with a warning (never guess)** on duplicate `scheduled`/`priority` fields, invalid dates, unknown priority values, or a task that also has a `due` date or recurrence. Print `path:line` and a count for each reason. Config problems (missing file, duplicate level values, no compatible `?` Blocked status) are **fatal before any write**. | Matches the `projects sync` and toggle policy. One bad line shouldn't block triage of 224 tasks, and printed counts keep "all" honest. |
| R4 | **One in-memory postimage per note:** replace only the date bytes (keep bracket/paren style and spacing), set `[?]` when the new date is after today, prepend a Schedule Log entry (create the marker if it's missing, as the picker does), then run `task_status_groups::transform` once on eligible area/project notes. | This makes the single commit complete and revertible, and leaves hooks nothing to do on those notes. |
| R5 | **Reason text:** picker grammar with its own head: `*2026-09-13 → 2026-10-19* — 🎲 P2 randomize · in **21** (8–30) days`. With `--until`: `… · **17** (8–30) days after 2026-10-12`. | You can tell bulk, unreviewed rolls apart from reviewed `roll`s. The picker's `SCHEDULE_LOG_ENTRY_RE` accepts any reason text. |
| R6 | **Git:** lock → vault-sync → write → one scoped commit → vault-sync, all under one lock hold. Never amend, rebase, force-push, run `add -A` itself, or push directly. | See §5. |
| R7 | **Preview and reproducibility are required:** `--dry-run` (no lock, no writes, no Git), `--seed`, JSON output, and a per-day load histogram. | 200+ edits deserve a preview. With a seed, what you preview is what you get. |
| R8 | **Optional `-u/--until DATE\|+N`** (default today) sets both the cutoff and the date the windows are rolled from. | Directly serves "focus on P0 for N days". It moves where the windows start without changing their width. |
| R9 | **On demand only**, never from `nightly` or cron. | It's a deliberate triage action, not maintenance. |

## 4. Where the reports disagreed, and my resolution

| # | Topic | Positions | Resolution |
| --- | --- | --- | --- |
| 1 | Next / In Progress | cdx and mus include them ("all" means all); cld, grk and gem exclude them | **Exclude** (R2). Setting `[?]` on them wipes out the active state. There are only 2 live, and they're reported as skipped. No `--include-active` in v1. |
| 2 | Tasks linked from today's Pomodoros | cld and gem exclude them; the others don't mention it | **Exclude.** Simpler than the picker's link pruning, and it keeps the commit off the daily note. |
| 3 | Malformed metadata | cdx: abort before any write; the others: skip and warn | **Skip and warn** for task-level problems; **fatal** for config-level problems (R3). |
| 4 | Create a Schedule Log when missing? | cdx: only update existing logs; mus: optional (`--no-log`); cld, grk and gem: create or prepend | **Create or prepend** (the picker's automatic-roll behavior). It doesn't matter today (224/224 already have logs). No `--no-log`. |
| 5 | Reason head | cdx `🎲 P2 · …` (the re-pick form, which implies a priority change); grk and gem `🎲 P2 roll · …`; cld a distinct `randomize` head | **Distinct `randomize` head** (R5). If you prefer exact picker parity, `roll` is the fallback. Open question Q2. |
| 6 | Git workflow | mus: scoped commit, no sync, no push; gem: scoped commit then one sync; cdx: sync, write, then a second sync with a custom message; cld and grk: sync, scoped commit, sync | **cld/grk sandwich.** cdx's version needs a new message-taking entry point, and the second sync's `add -A` would pull concurrent Obsidian saves to *other* notes into the randomize commit. mus's version plans against a possibly stale tree and carries pre-existing edits to touched notes into the commit. mus's version survives as the `--offline` fallback. |
| 7 | Regroup in the same write | cld: yes; grk: leave it to hooks; the others: flip status only | **Yes** (R4). Verified: `sase.md` has managed groups; hooks runs only from the Mac cron (`:10/:25/:40/:55`) and would make a second commit touching all 28 notes. The cost is exposing four private helpers. |
| 8 | Lock contention | mus and grk: exit (0) like vault-sync or nightly; cld: bounded wait | **Bounded wait** using hooks' retry controller (about 30 s, with a visible "waiting for vault-sync…" message), then exit 1. vault-sync holds the lock for seconds at a time, and an interactive command that silently exits 0 is misleading. |
| 9 | `--until` | cld proposes it; grk says "the windows are the product, don't special-case" | **Adopt** (R8). It shifts where the window starts and never widens it, so grk's objection (against wider windows) doesn't apply. Default behavior is unchanged. |
| 10 | Level filter | cld `-l/--level`; grk and gem `-p/--priority`; mus defers it | **Adopt `-l/--level LABEL` (repeatable).** It's cheap, and "leave P1s for hand triage" is the other good answer to the P1 pile-up. |
| 11 | Per-task seed | grk and gem: path + line index; cdx, cld and mus: path + line digest | **Identity-based:** `mix64(base ^ h(rel_path) ^ h(line_digest) ^ dup_ordinal)`. The pre-sync can shift line numbers between a dry-run and the real run; the ordinal keeps identical lines distinct. |
| 12 | What "today" is | mus: the daily-ledger anchor; the others: `BOB_NOW` / local date | Use the **same effective day as hooks**: the `BOB_DAY_FILE` date if it's set, otherwise `bob_env::current_datetime()`. They're the same unless `BOB_DAY_FILE` overrides it (`default_day_file` is derived from `current_datetime`). |
| 13 | Push | mus: never push; everyone else: push through vault-sync | **Push through the post-sync.** `--offline` skips both syncs and leaves only a local commit. |

## 5. Committing without fighting `vault-sync`

What "conflicting with vault-sync" would actually look like: (a) the 15-second
watcher/LaunchAgent commits a half-written set of notes; (b) an `add -A` mixes your
unrelated edits into the randomize commit; (c) randomize runs its own
fetch/merge/push with a policy that differs from vault-sync's. The sequence below rules
out all three:

```text
acquire bob_sync.lock (bounded wait)          ← watcher, LaunchAgent, nightly, hooks back off
  pre-sync:  run_cycle_with_existing_lock     ← commits existing edits as vault(host), pulls, pushes
             (fail → abort, nothing written; hint --offline)
  plan:      rescan, build complete plan (pure)
  apply:     guarded writer (quiet period, byte preflight, recovery copies, atomic renames)
             (vault_changed → re-plan once, then fail with no writes)
  commit:    git add -- <applied> ; git commit -F - -- <applied>
  post-sync: run_cycle_with_existing_lock     ← add -A (normally a no-op), fetch/merge, push retry
release lock
```

Commit message:

```text
bob randomize: 222 tasks in 28 notes (P1 85, P2 132, P3 5)

until 2026-09-28 · seed 0x5f3a9c…
sase.md 130 · cash.md 14 · bob.md 12 · …
```

After a run, master has, in order: an optional `vault(host)` commit from the pre-sync,
exactly **one** `bob randomize` commit, and an optional merge commit if the remote moved.
Each of these is something vault-sync already produces.

Failure behavior:

- **Pre-sync fails** (offline, unhandled conflict): abort before writing anything and
  exit 1.
- **Partial apply** (I/O error after some renames): commit the notes that were written
  (each is self-consistent), report the rest along with the recovery directory, and exit
  1. Re-running converges.
- **Post-sync conflict:** vault-sync keeps the remote copy of the note and quarantines
  randomize's version. Print a loud warning naming the notes and exit 1. Re-running picks
  up the tasks that were missed.
- **Push fails after the commit:** "committed `<sha>` locally; background vault-sync will
  publish". Exit 1. Never roll back good local edits because the network failed.
- **Not a git vault:** write the notes, warn, and skip Git (as `move-done-tasks` does).

To undo: `git -C ~/bob revert <sha> && bob vault-sync`. This is clean because status and
grouping are inside the same commit. The recovery manifest also keeps the original files.

Where to run it: any host works. The Mac, where you edit (nearly all recent commits come
from it), is best, because the guarded writer can *detect* local races there. Races with
another machine can only be *resolved* afterwards, by quarantining the note. Avoid typing
in `sase.md` during the ~5-second write window.

## 6. Recommended solution

### 6.1 CLI

```text
bob randomize [-b|--bob-dir PATH] [-d|--dry-run] [-f|--format human|json]
              [-l|--level LABEL]... [-o|--offline] [-r|--retry-timeout SECS]
              [-s|--seed N] [-u|--until DATE|+N]
```

Options are alphabetized and every option has a short alias (`cli_rules`). The letters
follow the `task-status-hooks` conventions (`-b`, `-d`, `-f`, `-r`).

| Option | Behavior |
| --- | --- |
| `-b, --bob-dir` | Vault root; defaults to `BOB_DIR` or `~/bob`. |
| `-d, --dry-run` | Scan, plan, and print the full plan, skip reasons, seed, and a per-day load histogram. No lock, sync, writes, recovery directory, or status file. |
| `-f, --format` | `human` (colored) or `json` (same data, stable field names). |
| `-l, --level` | Repeatable. Only re-roll these labels, e.g. `-l P2 -l P3`. |
| `-o, --offline` | Skip both vault-sync cycles but still make the scoped local commit. |
| `-r, --retry-timeout` | Bounded wait for the lock (default about 30 s). |
| `-s, --seed` | Base seed. Falls back to `BOB_PRIORITY_ROLL_SEED`, then `config::roll_seed()`. Always printed. |
| `-u, --until` | Cutoff and roll base, as a date or `+N` days. Defaults to today; must be today or later. |

Environment variables honored: `BOB_DIR`, `BOB_NOW`, `BOB_DAY_FILE`, `BOB_CONFIG_FILE`,
`XDG_CONFIG_HOME`, `BOB_PRIORITY_ROLL_SEED`, `BOB_VAULT_SYNC_LOCK_FILE`,
`BOB_VAULT_SYNC_STATE_FILE`, `NO_COLOR`.

Exit codes: 0 on success or nothing to do; 1 on runtime, partial-apply, conflict, or push
failure; 2 on a usage error.

Human output (sketch):

```text
bob randomize · Mon 2026-09-28 · ~/bob · until 2026-09-28 · seed 0x5f3a9c…
  eligible 222 · skipped: 1 next, 1 in-progress, 0 in today's Pomodoros, 0 ambiguous
  P1 high     85 → 2026-09-30 … 2026-10-05
  P2 medium  132 → 2026-10-06 … 2026-10-28
  P3 low       5 → 2026-10-29 … 2026-12-27
  load (next 30d): ▇▇█▇▇▇▂▂▁▂▂▂…   peak 26 on Fri 2026-10-02
  notes: sase.md 130 · cash.md 14 · bob.md 12 · … (28)
git: pre-sync ok · commit 4e5f6a7 · post-sync ok, pushed
```

### 6.2 Module plan

1. **`src/native/randomize.rs` (new).** Holds the clap CLI, a pure
   `plan(snapshot, config, cutoff, base, seed, filters) -> Plan`, the printers, and the
   orchestration (lock → sync → apply → commit → sync). Register
   `NativeCommand::Randomize` and add an alphabetized `randomize` row in `runner.rs`
   (between `query` and `task-status-hooks`) plus a top-level help example.
2. **`config.rs`.** Add `PriorityProperty::level_for_value(&str)`, validate that level
   values are unique, make errors command-neutral, and make the per-item seed helper
   public.
3. **Shared task fields.** Move `scheduled_field_matches` and
   `parse_strict_calendar_date` into a shared module and generalize them to any inline
   property with byte spans. Detect `due`/📅 and `repeat`/🔁 for the skip rule.
4. **Schedule Log.** Add `randomize_reason(label, days, min, max, base)` next to
   `priority_roll_reason`. Add a planner that prepends under an existing marker (reusing
   `first_direct_managed_log_start` and `first_child_indentation`) or appends the marker
   and entry as the task's last direct child.
5. **Hooks helpers.** Make `markdown_files`, `task_group_classification`,
   `task_grouping_eligible` and `validate_blocked_status` `pub(crate)`, or move them into
   a shared module. Reuse the hooks `retry_loop` for lock and `vault_changed` retries.
6. **Guarded writer.** Parameterize `TOOL` and `STATE_SUBDIR` (recovery goes under
   `$XDG_STATE_HOME/bob-cli/randomize/…`). Leave hooks' behavior and tests unchanged.
7. **`vault_sync.rs`.** Add `run_cycle_with_existing_lock_report(quiet) -> CycleReport`
   (conflicts, pushed, SHAs, error). Keep the `i32` wrapper for `nightly`.
8. **Docs.** Add a README row and section and a new `docs/randomize.md`. Cross-link from
   `docs/projects.md` (priority rolls; add the new reason row) and
   `docs/vault-git-sync.md`.

Within each note, edit candidates bottom-up so byte offsets stay valid (date, then status,
then log entry), then run `transform()` once. Preserve CRLF/LF line endings. If a roll
lands on the task's current date (only possible with `min_days: 0`), write no log entry
and don't set Blocked.

### 6.3 Tests

- **Planner units.** Bracket, paren and spacing variants are preserved, and so is CRLF.
  Every skip reason in R2/R3 has a case. Log entries are byte-exact, with both
  prepend-to-existing and create-marker cases. `[ ]`→`[?]` only when the new date is in
  the future. `min == max` and `min_days: 0` windows work. Date math is right across
  month, year and leap boundaries. The same seed gives the same dates after unrelated
  tasks are added. `--until` changes both cutoff and base. `--level` filters.
- **Grouping parity (the key test).** After randomize, `bob task-status-hooks --dry-run`
  reports no randomize-caused changes in the touched notes.
- **Git integration** (reusing the `vault_sync_*` bare-remote fixtures in
  `tests/cli.rs`). Exactly one `bob randomize:` commit, whose paths equal the rewritten
  notes, and it gets pushed. A pre-existing dirty unrelated file lands in a separate
  `vault(host)` commit. A non-overlapping remote change merges cleanly. A same-note
  remote change gives a conflict copy, a warning and exit 1, and a re-run converges.
  `--offline` commits without pushing. `--dry-run` leaves no trace. A held lock means a
  bounded wait, then failure with no writes. A non-git vault gets a warning.
- **Guarded-writer paths.** An editor save between planning and replacement triggers a
  re-plan and then fails cleanly. Partial apply is reported with its recovery directory.
- **CLI.** Help ordering, short aliases, JSON schema, exit codes.

### 6.4 Phasing

- **v1:** everything above, with independent uniform rolls (the same distribution as the
  picker and `p:<N>`).
- **v2 candidates:** `--balance` (put each task on the least-loaded day in its window;
  cld measured the worst day in the next 30 days dropping from about 25 to 20);
  `--demote` (drop one level and log `P1 → P2`); a "rolled by randomize N or more times"
  report; and an Obsidian command in `bob-navigation-hotkeys` that shows
  `bob randomize --dry-run --format json` as a preview.

## 7. Open questions for you

1. Should the reason head be `randomize` (recommended, so bulk rolls can be counted
   later) or `roll` (exact picker parity)?
2. Is P1 coming back within a week acceptable, or should `--until`/`--level` be your
   default habit? Should `--balance`/`--demote` be in v1?
3. Should Next and In Progress ever be included behind a flag? (I recommend never.)
4. Name: keep `randomize` (it's your word, and it sorts cleanly), or `reroll` (the
   vault's own 🎲 term)?
