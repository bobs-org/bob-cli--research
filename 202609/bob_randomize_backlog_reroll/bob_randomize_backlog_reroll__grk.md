# `bob randomize`: re-roll due prioritized tasks

Researcher: `grk` (independent swarm report).  
Question: how should Bob implement a command that re-schedules every currently due prioritized task onto a random date in that task's configured priority window, in one Git commit, without fighting `bob vault-sync`?

## Verdict

The feature is a good idea. It is the vault-wide version of a gesture Bob already has for one task and for a counted editor batch: keep the existing `[priority:: …]` field, roll a new `[scheduled:: YYYY-MM-DD]` inside that level's `min_days`–`max_days` window, and record a machine-written `🗓️ **SCHEDULE LOG**` entry.

The original sketch is too thin in three places: selection (which tasks count as "due prioritized"), mutation side effects (Blocked status, Schedule Log shape, active-work exclusions), and Git (how a dedicated commit coexists with the 15-second `vault-sync` watcher). The recommended command is a native `bob randomize` that reuses the existing roll math, writes under the shared maintenance lock, and sandwiches the rewrite between two in-process `vault-sync` cycles so the randomize commit is one scoped commit and `vault-sync` is the only code that `git add -A`s, merges, and pushes.

Do not put this on the nightly cron. It is a deliberate triage dump, not maintenance.

## What already exists

Bob already encodes "priority means a random future date, not now." A task with no `priority` field is implicit P0: do it now, no roll. `~/.config/bob/config.yml` is the single source of windows:

| Label | Inline value | Inclusive window |
| ----- | ------------ | ---------------- |
| P1    | `high`       | 2–7 days         |
| P2    | `medium`     | 8–30 days        |
| P3    | `low`        | 31–90 days       |
| P4    | `lowest`     | 91–365 days      |

There is no `p:0`. `highest` is a legal Obsidian Tasks name and is unused in the live vault.

Three writers already roll or rewrite `scheduled` dates:

1. **`bob capture … p:<N>`** loads that config, calls `PriorityLevel::roll_offset`, writes `[priority::<value>]` plus `[scheduled::YYYY-MM-DD]`, and appends a brand-new Schedule Log whose reason is always a `P0 → <to>` transition. Seed mixing is `item_roll_seed(base, item_index)`; `BOB_PRIORITY_ROLL_SEED` pins a dry-run to the live write. The Rust planner in `src/native/capture_schedule_log.rs` is byte-for-byte aligned with the Obsidian picker for new tasks.

2. **Obsidian `Ctrl+Shift+P`** (`bob-navigation-hotkeys`) is the richer writer. Choosing a priority level rolls a date and writes immediately. On a task that already has a configured priority, the `scheduled` stage pins a "random in N–M days" suggestion; `Ctrl+R` re-rolls it. Counted `N<Ctrl+Shift+P>` applies one priority to N consecutive tasks with an independent roll per task. Automatic rolls prepend a Schedule Log entry when a marker exists, or append a new marker as the last direct child when it does not. A roll that lands on the date the task already has writes nothing. Giving a task a strictly future `scheduled` date also marks it Blocked and removes its live links from today's open Pomodoros.

3. **`bob task-status-hooks`** does not roll dates. It is the reconciler that turns a strictly future `[scheduled::]` into Blocked `[?]` (and unblocks when the date is due). Live runs take the same `bob_sync.lock` as `vault-sync`, snapshot inputs, and refuse to overwrite a vault that changed underfoot.

Schedule Log reason text is already a closed vocabulary. The two machine-roll forms that matter here:

| Gesture | Reason |
| ------- | ------ |
| Priority re-picked, level unchanged | `🎲 P2 · in **17** (8–30) days` |
| Pinned roll chosen in the `scheduled` stage | `🎲 P2 roll · in **17** (8–30) days` |

`bob randomize` is the second gesture: the priority does not change; only the date is re-rolled. Capture's current `priority_roll_reason()` helper emits the first form (and the `P0 → P4` form for new captures). It needs a `source: "scheduled"` sibling that inserts the `roll` suffix. Using `*` emphasis, em dash `—`, en dash `–` in the window, middle dot `·`, and the die emoji `🎲` — matching `capture_schedule_log.rs` / the picker, not the `_` emphasis that `capture_task_toggle.rs` uses for 🍅 pull-forward.

Git already has two bulk-mutation patterns:

| Command | Lock | What it commits | Push |
| ------- | ---- | --------------- | ---- |
| `bob capture` | no | nothing; watcher `git add -A`s later | via watcher |
| `bob task-status-hooks` | yes, held through writes | nothing; watcher `git add -A`s later | via watcher |
| `bob move-done-tasks` | no when standalone | scoped `git add -- <touched>` + `git commit -- <touched>` | yes, naive `git push` |
| `bob nightly` | yes, held for the whole sequence | `vault-sync`, then scoped move-done commit, then `vault-sync` | `vault-sync` does fetch/merge/retry push |
| `bob vault-sync` | yes (`acquire_lock_quiet_if_held`; exit 0 if contended) | `git add -A` of the entire worktree, message `vault(<host>): N files - …` | fetch, merge with remote-wins into `_conflicts/`, bounded push retries |

The 15-second watcher on athena/apollo (`bob-vault-sync.service`) and the Mac LaunchAgent both run `bob vault-sync -q`. A writer that does not hold `bob_sync.lock` can be committed mid-rewrite. A writer that `git add -A`s will mix unrelated Obsidian edits into its commit. `move-done-tasks` already documents that dirty bytes in a touched file ride along in its scoped commit.

## Live vault evidence (2026-09-28)

Native `bob query --tasks` against `~/bob`, with the vault's global filter `#task` and global query `path does not include _conflicts`:

| Population | Count | Notes |
| ---------- | ----: | ----- |
| Open, explicit priority, `scheduled` today or earlier | **224** | the command's default target |
| of which P1 `high` | 87 | window 2–7 days |
| of which P2 `medium` | 132 | window 8–30 days |
| of which P3 `low` | 5 | window 31–90 days |
| of which P4 `lowest` | 0 | none currently due |
| Ready `[ ]` | 222 | |
| In Progress `[/]` | 1 | `sase_clean.md` `^work-all-beads` |
| Next `[*]` | 1 | `sase.md` `^bulk-gate-cmds` |
| Blocked `[?]` | 0 | due dates are not a Blocked reason |
| Distinct files | 28 | `sase.md` alone holds 130 |
| Tasks with a block id | 54 | 170 have none |
| `^prj` lifecycle tasks | 0 | |
| Oldest due date | 2026-08-22 | about five weeks overdue |
| Open, explicit priority, `scheduled` after today | 53 | already Blocked; leave them |
| Open, no priority (P0), `scheduled` today or earlier | 40 | the work this command is meant to protect |
| Open, `priority:: highest` | 0 | |

A default run today would rewrite on the order of 28 notes and prepend 224 Schedule Log entries. `sase.md` is the hot file. The picker cannot do this: counted `N<Ctrl+Shift+P>` is cursor-relative and the pinned roll only appears when every counted task shares one priority.

## Critique of the original plan

The goal is right. The mechanism (per-task roll from `config.yml` by that task's priority) is right. Several details in the sketch would ship a command that either hits the wrong tasks, leaves them in the today view, or races the watcher.

**"Currently due" is `scheduled`, not Tasks `due`.** Bob does not use a `due` field for this workflow. Selection is: open `#task`, a recognized configured `priority` value, exactly one valid `[scheduled:: YYYY-MM-DD]`, that date `<=` today (`BOB_NOW`). `priority is not none` is the Tasks spelling; `priority is above none` would drop P3/P4 because Tasks numbers `low`/`lowest` *below* implicit none.

**P0 must stay out.** Implicit P0 is "no priority field." The 40 due P0-with-a-date tasks are the pile the user wants to focus on. Randomizing them would fight the design.

**Active work must stay out.** The one In Progress and one Next match in the live set are tasks the user is already touching. Re-rolling them would also require Pomodoro-link cleanup the picker does when a date becomes strictly future. Default skip, with an explicit opt-in.

**A date rewrite without Blocked is incomplete.** After a successful roll every target date is strictly future (every configured `min_days` is `>= 2`). Ready `[ ]` tasks with a future `scheduled` still appear in Ready/Next navigation until `task-status-hooks` runs (15 minutes on the Mac, nightly-only on athena unless invoked by hand). The picker's write marks Blocked in the same edit. Randomize should too. Otherwise the command fails its stated purpose for up to a hooks cycle.

**Schedule Log is not optional for a machine roll.** The picker creates a log on an automatic roll when the task has none, and prepends when it has one. Newest entry on top. Skip the write only when the rolled date equals the current date (cannot happen for due tasks under today's windows; still implement the guard). Do not use the 🤷 empty-reason fallback; this command never prompts.

**`randomize` as a name is slightly vague, and still the right public spelling.** It sorts between `query` and `task-status-hooks`, matches the user's vocabulary, and the help `about` can carry the precision. A hidden alias `roll-due-tasks` is optional sugar, not a second implementation.

**Discovery should not shell out to `bob query`.** A Tasks JSON dump of this population was ~30s and hundreds of KB, and it does not give byte offsets. Walk notes the way `task-status-hooks` / `note_tasks` already do, parse trailing Dataview fields with the same recognizer (`high|medium|low|lowest` plus a calendar `scheduled`), and plan every file in memory before touching disk.

**Project `^prj` frontmatter is a trap for v1.** The picker routes `^prj` scheduled writes through project frontmatter and then propagates. The live due set contains zero `^prj` matches. Skip `^prj` with a warning rather than inventing a second scheduler in the first cut.

**This is a human triage command.** Wiring it into `bob nightly` would keep kicking unread P1s every morning. Leave it off the cron.

## Requirement adjustments

These change the original request. Each is intentional.

1. **Keep the public name `bob randomize`.** About text: re-roll due prioritized tasks onto random dates in their configured windows. Optional hidden alias `roll-due-tasks`.

2. **Selection is open `#task` lines with a configured priority value and a single valid `scheduled` date `<=` today.** Exclude done, canceled, missing/invalid/ambiguous `scheduled`, unrecognized priority values, `^prj`, and files the existing vault walkers already skip (`.git`, `.obsidian`, `_conflicts`, `_generated`, `_templates`, and `done/`).

3. **Skip In Progress `[/]` and Next `[*]` by default.** Report them. `--include-active` opts in and then must also strip today's open Pomodoro links for those tasks, matching the picker.

4. **Do not change `priority`.** Look up the window by the inline value (`high` → P1), not by assuming P1 is always index 1. Add `PriorityProperty::level_by_value`.

5. **Write three things per task, in one in-memory file plan:** replace only the date token inside the existing `[scheduled:: …]` field (preserve the task's bracket/spacing); prepend or create a Schedule Log whose reason is `🎲 <label> roll · in **<n>** (<min>–<max>) days`; if the new date is strictly future, set the checkbox to Blocked `[?]`.

6. **On-demand only.** Not a nightly step.

7. **Git: one scoped randomize commit, produced under the shared lock, with `vault-sync` owning add-all / merge / push.** Details in the next section.

8. **Default is live write after a printed summary.** `-n/--dry-run` prints the same summary and per-task plan without lock, writes, or Git. No interactive confirmation prompt (automation-hostile, unlike Bob's other writers). `-j/--json` for the machine-readable plan/result. `-p/--priority P2` (repeatable) limits to listed labels. `BOB_PRIORITY_ROLL_SEED` pins rolls the same way capture does; mix the base seed with path + line so tasks stay independent and a dry-run matches apply.

9. **Honor `BOB_NOW` / `DATE` / `BOB_DIR` / `BOB_CONFIG_FILE`.** Same clock and config as `p:<N>`.

## Git and `vault-sync`

The conflict to avoid is not "two commits exist." It is (a) the watcher committing a half-written `sase.md`, (b) `git add -A` mixing randomize rewrites with unrelated dirty notes into one `vault(<host>):` commit, and (c) randomize implementing its own fetch/merge/push that disagrees with `vault-sync`'s remote-wins policy.

Recommended live sequence, modeled on `bob nightly` and using the existing `vault_sync::run_cycle_with_existing_lock`:

1. Acquire `bob_sync.lock`. On contention, fail the same way nightly does (print, exit 0) or retry like `task-status-hooks` if we take that retry controller. Do not spawn a child `bob vault-sync`; the child cannot take a lock the parent holds.
2. In-process `vault-sync` cycle. This commits any *pre-existing* dirty work under the normal `vault(<host>):` message, fetches, merges, and pushes. The randomize plan then starts from a published tree.
3. Re-read notes, plan every rewrite against those bytes, apply with a guarded snapshot/compare (the `task-status-hooks` writer is the template: quiet period on hot files, refuse if a note changed underfoot, stage replacements as temps, recover originals).
4. `git add -- <touched paths>` and `git commit -- <touched paths>` with a dedicated message, for example `bob randomize: re-roll 224 due prioritized tasks`. This is the single commit the user asked for. It must not `git add -A`.
5. In-process `vault-sync` again. The randomize paths are already committed, so add-all is a no-op unless the editor dirtied something else during the run (that dirt becomes a *second*, vault-sync-authored commit, which is correct). Fetch / merge / retry-push publishes the randomize commit.
6. Drop the lock.

`--dry-run` stops before step 1. `--no-git` (or a non-worktree vault, matching `move-done-tasks`) performs the writes and skips steps 2, 4, and 5; the next watcher cycle will `git add -A` those files. Prefer Git-on by default so the randomize commit stays attributed.

Do not copy standalone `move-done-tasks` here. It stages scoped paths and pushes, but it does not take the lock, so the 15-second watcher can interleave. Nightly only gets that right because *nightly* holds the lock around it.

Cross-machine races remain: the lock is per host. A 130-task rewrite of `sase.md` while the Mac has that note open can still lose to `vault-sync`'s remote-wins merge and land in `_conflicts/`. Mitigation is operational (run on the machine that has Obsidian, after a quiet save) plus the local guarded writer. Do not invent a second conflict policy.

Dirty bytes in a file randomize *will* touch, if they survive step 2 (they should not, because step 2 commits them), would otherwise ride along in the randomize commit the same way `move-done-tasks` documents. The sandwich exists so that does not happen.

## Implementation shape

Native command, not a plugin and not a shell script.

- Register `NativeCommand::Randomize` and a `randomize` row in `runner.rs`'s alphabetized `SUBCOMMANDS` table (`about`: "Re-roll due prioritized tasks onto random dates").
- New module `src/native/randomize.rs` for CLI, selection, summary, Git sandwich.
- Small extensions, not a second copy of the roll:
  - `PriorityProperty::level_by_value(&str)`
  - `capture_schedule_log::priority_date_roll_reason(label, days, min, max)` → `🎲 P2 roll · in **17** (8–30) days`
  - a planner that, given one task line + children, returns the updated line, optional Blocked status, and Schedule Log insert (prepend under existing marker or append marker+entry as last direct child). Reuse `first_direct_managed_log_start`, indent helpers, and `entry_text(Some(from), to, reason)`.
  - replace the date *inside* the existing scheduled field; do not reshuffle `[created::]` / `[priority::]` / `[id::]`.
- File discovery: the same excluded-directory walker `task-status-hooks` uses. Do not parse `done/` archives.
- Per-task seed: `mix64(base ^ path_hash ^ line_index)` so two tasks never share a roll, and `BOB_PRIORITY_ROLL_SEED` makes `-n` match the live run.
- After marking Blocked, leave further status reconciliation to `task-status-hooks` (dependency Blocked, grouping). Do not reimplement that command.
- Help: `-h/--help` excellent; every public long option has a short alias; options alphabetized; colored summary (counts by P-level, files, skipped reasons).

Suggested flags:

| Flag | Role |
| ---- | ---- |
| `-n, --dry-run` | plan only |
| `-j, --json` | machine-readable plan/result |
| `-p, --priority <LABEL>` | repeatable filter (`P2`, `P3`, …) |
| `-q, --quiet` | summary without per-task lines |
| `-A, --include-active` | include Next / In Progress |
| `-G, --no-git` | write without the vault-sync sandwich |

Exit 0 on a successful no-op (nothing due). Exit 2 on usage/config errors. Exit 1 on I/O, lock I/O, or a partial apply.

## Alternatives considered

**Obsidian command only.** The picker already rolls and already batch-edits consecutive tasks. It cannot select "every due prioritized task in the vault," it cannot coordinate Git with the watcher, and it requires the desktop app focused on the right notes. A later plugin command that shells out to `bob randomize` is a fine follow-up, not the first implementation.

**Leave Git to the watcher.** Simplest writer, same as `capture`. The resulting commit message is `vault(<host>): 28 files - sase.md, …` and any other dirty notes from the last 15 seconds share that commit. That fails the "single commit of *this* command's changes" requirement.

**Scoped commit + naive `git push`, no lock.** This is `move-done-tasks` standalone. It produces a dedicated commit and then loses races with the watcher and with a newer remote.

**Call `git add -A` inside randomize with a custom message.** Dedicated message, mixed contents. Worse than letting `vault-sync` own add-all.

**Re-pick each task's priority (write `🎲 P2 · …` or even `P0 → P2`).** That implies a priority change that did not happen. The scheduled-stage `roll` reason is the honest one.

**Spread P1s across a wider window than config.** Tempting given 87 due P1s into a 6-day window (~14/day). The windows are the product. If the clump is painful, change `config.yml`, do not special-case this command.

**Also randomize due P0s that happen to have a `scheduled` date.** 40 live matches. That would hide the work this command exists to surface.

## Recommended solution

Ship a native `bob randomize` that:

1. Selects open `#task` lines with a configured priority and a single `scheduled` date on or before today, skipping P0, done/canceled, `^prj`, In Progress, Next, and the usual excluded directories.
2. For each selected task, independently rolls a new date in *that* level's inclusive window from `~/.config/bob/config.yml`, using the existing `roll_offset` / `BOB_PRIORITY_ROLL_SEED` machinery.
3. In one in-memory plan per file, replaces the scheduled date, writes a `🎲 <label> roll · in **<n>** (<min>–<max>) days` Schedule Log entry (create or prepend), and marks Blocked when the new date is strictly future.
4. Holds `bob_sync.lock`, runs in-process `vault-sync`, applies the guarded writes, makes **one scoped Git commit of the touched paths**, runs in-process `vault-sync` again, then drops the lock.
5. Stays off nightly. Offers `--dry-run`, `--json`, and `--priority` on day one.

That is the smallest design that matches the existing priority-roll product, actually clears the today view, and produces one attributable commit the watcher will not swallow or split.

## Test plan (for whoever implements)

- Config: lookup by value; unknown `priority:: highest` skipped; missing config file errors the same way `p:<N>` does.
- Roll: pinned `BOB_PRIORITY_ROLL_SEED` makes `-n` match apply; two tasks in one file get different offsets; every offset stays inside `[min_days, max_days]`; `min_days == max_days` is constant.
- Selection fixtures: due P1/P2 included; future P2 skipped; P0 with a past date skipped; done skipped; two `[scheduled::]` fields skipped; In Progress skipped unless `-A`.
- Bytes: Schedule Log reason/codepoints match a picker fixture for `source: "scheduled"`; existing log prepends newest-first; missing log is created as last direct child; scheduled-field spacing around `::` is preserved.
- Status: Ready due P2 becomes `[?]` after a future roll.
- Git: under a fake worktree + lock, dry-run is clean; live run produces exactly one randomize commit whose paths equal the rewritten notes; a pre-dirty unrelated file is committed by the first `vault-sync` cycle, not by the randomize commit; contended lock does not write.
- Help: `randomize` appears in top-level `--help` in alphabetical order; `-h` lists short aliases.

## Sources

- `~/.config/bob/config.yml` (deployed windows and the P0 comment)
- `src/native/config.rs` (`PriorityLevel::roll_offset`, `roll_seed`, config parse)
- `src/native/capture.rs` / `docs/capture.md` (`p:<N>` contract)
- `src/native/capture_schedule_log.rs` (picker-matching log bytes)
- `src/native/capture_task_toggle.rs` (prepend-into-existing-log pattern; `_` emphasis is the other plugin)
- `src/native/vault_sync.rs`, `docs/vault-git-sync.md`, `src/native/nightly.rs`, `src/native/ob.rs`
- `src/native/collect_done.rs` / README "Move done tasks" (scoped commit, lock gap)
- `src/native/task_status_hooks.rs` / `task_status_hooks_write.rs` / `docs/task-status-hooks.md`
- `sase/repos/external/gh/bobs-org/bob-plugins/plugins/bob-navigation-hotkeys/main.js` (`planScheduleLogEntry`, `buildPriorityRollScheduleLog`, `planCountedBulletPropertyBatch`, `source: "scheduled"`)
- `docs/projects.md` "Schedule-log reason prompt" table
- Live `bob query --tasks` on 2026-09-28 (224 / 53 / 40 counts above)
