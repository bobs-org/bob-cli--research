# `bob randomize`: bulk re-rolling due prioritized tasks (research, critique, recommendation)

Researcher: `cld` · Date: 2026-09-28 · Repo: `bob-cli` (HEAD `ec31329`)

## TL;DR

- **The idea is sound.** It is the vault-native version of Todoist's bulk
  "Reschedule" for overdue tasks and the FSRS Helper's "Postpone" for Anki
  backlogs. It is also a gentler, reversible form of "to-do list bankruptcy."
  Most of the building blocks already exist in bob-cli: the priority config
  parser and roll function, Schedule Log formatting, the guarded multi-file
  writer, the pure status-grouping transform, the shared maintenance lock, and
  the vault-sync cycle.
- **Measured on the live vault today:** 224 open, due, prioritized tasks
  across 28 notes. 130 of them are in `sase.md`. All 224 are in area/project
  notes and all 224 already have a `🗓️ **SCHEDULE LOG**`. The median task is
  13 days overdue and the worst is 37.
- **Changing only the dates is not enough for "one commit."** A future date
  makes `bob task-status-hooks` flip each task to Blocked `[?]` and physically
  move it into the note's `### Blocked` group. If randomize only rewrites dates,
  the Mac's 15-minute hooks cron makes a second, much larger commit. That
  commit also breaks a clean `git revert` of the randomize commit. The command
  should therefore set the Blocked status, add the Schedule Log entry, and
  regroup each note it touches, all in memory, then write each note once.
- **To stay compatible with `vault-sync`,** run the whole operation the way
  `bob nightly` does. Take the shared lock, run a vault-sync cycle, write,
  make one scoped commit, then run another vault-sync cycle, all while holding
  the lock. Never `git push` directly the way `move-done-tasks` does, and never
  amend or rebase.
- **The P1 window is the biggest issue with the plan itself.** About 85 P1
  tasks re-rolled into a 2–7 day window come back at about 20 per day from
  Sep 30 to Oct 5, whether the dates are uniform or load-balanced. Randomizing
  cannot create capacity. I recommend one extra flag, `-u/--until DATE`: it
  clears prioritized tasks scheduled through `DATE` and rolls their windows
  from `DATE`. With no flag it behaves exactly as you specified.
- **Recommended v1:** a new native `bob randomize` with `--dry-run`,
  `--until`, `--seed`, `--offline` and (optionally) `--level`/`--format`. It
  excludes Next, In Progress, terminal statuses, `^prj`, and tasks linked from
  today's open Pomodoros. It writes picker-parity Schedule Log entries and
  makes a single scoped `bob randomize: N tasks in M notes` commit between two
  locked vault-sync cycles. Load-aware balancing and priority demotion are
  phase-2 options.

---

## 1. What already exists (grounding)

### 1.1 Priority config and rolls

- `~/.config/bob/config.yml` defines one `values: priority` property that
  `schedules: scheduled`, with four levels:

  | Label | Stored value | Window (days from base) |
  | --- | --- | --- |
  | P1 | `high` | 2–7 |
  | P2 | `medium` | 8–30 |
  | P3 | `low` | 31–90 |
  | P4 | `lowest` | 91–365 |

  A task with no `priority` field is implicitly P0. The config comment warns
  that stored values must stay Tasks priority names, because Tasks parses
  trailing fields right to left and stops at the first one it doesn't know.
- `src/native/config.rs` already parses and validates this.
  `load_priority_property`, `PriorityProperty::level(n)` and
  `PriorityLevel::{label,value,min_days,max_days}` exist.
  `PriorityLevel::roll_offset(seed)` (line 139) is an inclusive splitmix64 roll.
  `roll_seed()` (line 154) honors `BOB_PRIORITY_ROLL_SEED`, which makes tests
  deterministic. `capture.rs:1639` `item_roll_seed` derives an independent seed
  per item. What's missing is a reverse lookup from a stored value to its level
  (`high` → P1), which is trivial to add.
- `bob capture … p:<N>` writes the priority, rolls a date and writes a Schedule
  Log. `capture_schedule_log.rs` holds the byte-for-byte picker constants and
  `priority_roll_reason` / `entry_text`.

### 1.2 The Obsidian picker already does a per-note "counted" bulk roll

In `bob-plugins` (`plugins/bob-navigation-hotkeys/main.js`), `N<Ctrl+Shift+P>`
applies a priority to N tasks and rolls **an independent date per task**
(`rollByLine`, around line 19420). In one guarded editor transaction it:

1. upserts `priority` and `scheduled`,
2. flips every future-scheduled task to Blocked
   (`blockObsidianTaskCheckboxStatus`, around line 14820),
3. writes a Schedule Log entry per task with a 🎲 reason,
4. prunes the deferred tasks' links from today's open Pomodoros.

Reason formats (`formatPriorityRollScheduleReason`, around line 1851):

- priority change: `🎲 P1 → P2 · in **20** (8–30) days`
- same-level re-roll (the pinned "roll" suggestion; `Ctrl+R` re-rolls it):
  `🎲 P2 roll · in **12** (8–30) days`

That second form is already in your vault, for example in `bob.md`:

```markdown
- [ ] #task Start marking references with `stale` status after 1w of no activity! [created::2026-08-13] [priority:: medium] [scheduled:: 2026-09-13]
	- 🗓️ **SCHEDULE LOG**
		- *2026-09-01 → 2026-09-13* — 🎲 P2 roll · in **12** (8–30) days
		- *2026-08-17 → 2026-09-01* — 🎲 P1 → P2 · in **15** (8–30) days
```

Entries are newest-first. A new entry goes directly under an existing marker,
reusing the first entry's indent. Otherwise a marker and entry are appended as
the task's last direct child (`planScheduleLogEntry`, around line 1690). An
automatic entry is skipped when the date didn't change. **`bob randomize` is
really a vault-wide, headless version of the picker's counted "roll".** It
should keep that semantics and output byte-compatible.

Note: two emphasis styles are live. The picker uses `*…*`; the
`block-id-prompt` pull-forward uses `_…_`. That divergence is documented in
`capture_task_toggle.rs:33`. Randomize should use the picker's `*`
(`capture_schedule_log::entry_text`).

### 1.3 What a future date triggers: `task-status-hooks`

From `docs/task-status-hooks.md`:

- **Blocked is derived.** A valid `[scheduled:: D]` with `D` after today turns
  `[ ]`, `[*]` or `[/]` into `[?]`.
- **Status grouping.** In `[[area]]`/`[[project]]` notes, the command moves
  root task blocks out of the Ready intake into generated `### Next & In
  Progress`, `### Blocked`, `### Done & Canceled` child headings and
  regenerates a status-count badge row.
- On the Mac this runs from cron every 15 minutes (`:10/:25/:40/:55`) with
  `--retry-timeout 120`.
- The grouping step is a **pure function**:
  `task_status_groups::transform(contents, &classification)`
  (`task_status_groups.rs:344`). Its caller builds the classification from
  Tasks settings (`task_group_classification`) and checks eligibility with
  `task_grouping_eligible`. Both are private to `task_status_hooks.rs` today.

### 1.4 Multi-file writing: the guarded writer

`task_status_hooks_write.rs` already provides:

- `capture_required` / `planned_write` / `apply_plan`,
- a 2-second quiet period before structural rewrites,
- a full byte-and-inode preflight re-check before the first replace, with a
  `vault_changed` abort,
- staged temp files and atomic renames,
- a recovery manifest of originals and proposed bytes under
  `$XDG_STATE_HOME/bob-cli/task-status-hooks/<vault-hash>/<run-id>/`,
- partial-apply reporting.

This is exactly the safety net a 28-note rewrite needs. Its message prefix and
`STATE_SUBDIR` are hard-coded to task-status-hooks, which is a small
generalization.

### 1.5 Git: `vault-sync`, `nightly`, `move-done-tasks`

- **Shared lock.** `ob::try_acquire_lock` is a per-host `flock` on
  `bob_sync.lock`. `vault-sync run` exits 0 silently when the lock is held;
  hooks retry.
- **One vault-sync cycle** (`vault_sync.rs:253`) does:
  1. recover any interrupted merge,
  2. `git add -A .` (line 284),
  3. commit with a `vault(<host>): N files - …` message, or `--message`,
  4. `fetch` only when `ls-remote` differs,
  5. fast-forward, or a **real merge** (no rebase),
  6. on conflict, **remote wins in place** and the local version is copied to
     `_conflicts/` and logged,
  7. push with up to 3 non-fast-forward retries,
  8. write the status record.
- **`nightly`** (`nightly.rs:68`) is the only caller that composes steps
  under a single lock hold: vault-sync, then `move-done-tasks`, then
  vault-sync, using `run_cycle_with_existing_lock`.
- **`move-done-tasks`** makes a scoped commit
  (`git add -- paths` + `git commit -m … -- paths`) and then runs a **raw
  `git push`** (`collect_done.rs:597-686`). Run on its own, it **takes no
  lock and never fetches or merges**, so a push is rejected whenever the Mac
  has pushed first. It only behaves well inside `nightly`. Randomize should
  not copy this pattern.
- **Traffic in practice.** The Mac pushes constantly: about 180 `vault(…)`
  commits in the last 3 days, mostly 1–2 files each. athena and apollo run an
  inotify watcher (15-second timeout, short debounce). The Mac LaunchAgent
  syncs every 15 seconds.

### 1.6 Adjacent systems checked (no problem found)

- **`projects sync`** raises an ordinary task's date only when it is *earlier*
  than the project's frontmatter `scheduled`. Randomize only moves dates
  later, so the two never fight.
- **`^prj` surfacing** uses the open non-hidden count, which includes `[?]`.
  Deferring every task in a project therefore does **not** un-hide its `^prj`
  on the dash, so there's no hidden follow-up commit.
- **`^prj` lifecycle tasks** keep their schedule in frontmatter, not inline, so
  they are naturally out of scope. `sase_bug_bash`'s `^prj` has a priority but
  no inline `scheduled`.

---

## 2. The live vault today (2026-09-28, measured)

| Metric | Value |
| --- | --- |
| Open tasks with `scheduled ≤ today` **and** `priority` | **224** (222 Ready `[ ]`, 1 Next `[*]`, 1 In Progress `[/]`) |
| By level (all 224) | 87 high (P1) · 132 medium (P2) · 5 low (P3) · 0 lowest |
| By level (222 Ready) | 85 P1 · 132 P2 · 5 P3 |
| Notes touched | 28. Top: `sase.md` 130, `cash.md` 14, `bob.md` 12, `dev.md` 8, `sase_art.md` 8, `love.md` 8 |
| Note types | 190 in `[[project]]` notes, 34 in `[[area]]` notes, so **all 224 are groupable** |
| Already carrying a `🗓️ SCHEDULE LOG` | 224 / 224 |
| With a block ID | 54 (2 appear linked from today's daily note) |
| Overdue | min 0, median 13, max 37 days |
| Due P0 (no priority), untouched by design | 40 |
| **Done/canceled** tasks that still have due dates and priorities | 15. These must **not** be touched |
| Field spelling variants | `[priority:: low]` / `[priority::high]`, `[scheduled:: 2026-09-13]` / `[scheduled::2026-09-12]` |

Context for `sase.md`: its `## Tasks` Ready intake is about 680 lines. Once
those 130 tasks become Blocked, grouping moves them under `### Blocked`. That
is a large structural diff to the note you edit most, and it happens whether
randomize or the Mac's hooks cron does the regrouping.

---

## 3. Critique: is this a good idea?

### 3.1 Yes, and why rewriting dates beats a "focus view"

A read-only alternative would be a dashboard filter or a "P0 focus mode" that
just hides prioritized tasks. That would mean no writes and no git churn, but I
would not do it:

- `scheduled` is the vault's source of truth for "when should I see this."
  Blocked derivation, status grouping, dash queries and `projects list`'s
  `SHOWN` all key off it. A view-only filter leaves 200+ tasks Ready and overdue
  in every project intake. The pile keeps growing, and when focus mode ends
  you're back to a wall.
- The re-roll already has a well-defined, logged meaning in your system (🎲
  entries). The command just applies it in bulk.
- Prior art converges on the same move. Todoist offers a one-tap "Reschedule"
  for overdue tasks, plus Smart Schedule suggestions. Anki's FSRS Helper
  "Postpone" reschedules a backlog to minimize deviation. The "to-do
  bankruptcy" literature recommends clearing the slate instead of staring at an
  impossible list. Randomize is bankruptcy that keeps the tasks and tells you
  when they'll come back.

### 3.2 Real concerns

1. **Randomizing doesn't create capacity, and P1 shows it.** 85 P1 tasks in a
   6-day window (Sep 30 – Oct 5) is about 14 per day on average. Simulated
   against the vault's existing future load:

   | Placement | Mean worst day (next 30 d) | 95th-percentile worst day | Days with ≥10 tasks |
   | --- | --- | --- | --- |
   | Uniform independent rolls (as specified) | 25 | 29 | about 9 |
   | Load-aware (least-loaded day in the task's window, random tie-break) | 20 | – | about 7 |

   Load-aware placement flattens the P2 stretch (Oct 6–28) to a steady 6–7 per
   day, where uniform rolls produce a lumpy 2–12. It cannot fix the P1 wall:
   days 2–7 sit at about 19–20 either way. With the stated use case ("focus on
   P0 for days or weeks"), the P1s come back *during* the focus period. Either
   roll from a later base date (§4, A4) or accept that 85 P1s is a triage
   problem (demote or cancel) rather than a scheduling problem.
2. **Zombie tasks.** Repeated bulk rolls can hide the same task forever. The
   Schedule Log is the remedy: give randomize its own reason text so bulk
   deferrals can be counted later (for example, "rolled by randomize 3 or more
   times, so cancel or demote").
3. **A large multi-file write in a vault that is being edited on another
   machine.** With 28 notes, including the one you edit most, the risks are:
   (a) racing an Obsidian save on the same host, and (b) a git conflict with a
   Mac push. For (b), vault-sync's policy keeps the remote version and moves
   *all* of randomize's changes to that note into `_conflicts/`. Nothing is
   lost, but the result is a partial randomize. Mitigations are in §6.
4. **Status and grouping side effects are larger than the date edits.** See
   §1.3 and §2. Any "single commit" goal has to account for them.
5. **Tasks you are actively working on.** Next, In Progress, and tasks linked
   under today's open Pomodoros express "today." Randomizing them would fight
   the ledger, since the picker also has to prune Pomodoro links when it defers
   one. Exclude them.

### 3.3 Is "a single commit" the right goal?

Yes, but the reason matters more than the count. One commit makes the
operation **atomic in history**:

- other machines never pull a half-randomized vault,
- `git show` gives a readable audit,
- `git revert` is a real undo.

That undo only works cleanly if the commit **also contains the status flip and
regroup**. Otherwise the Mac's hooks cron moves the changed lines into
`### Blocked` in a later `vault(kellys-mbp)` commit, and reverting the
randomize commit then conflicts. So "single commit" really means **one commit
containing the complete, settled result for every touched note.**

---

## 4. Requirement adjustments (explicitly called out)

| # | Adjustment | Why |
| --- | --- | --- |
| **A1** | Candidates = **open Ready `[ ]` or Blocked `[?]`** `#task` tasks (per the Tasks global filter) with exactly one valid `scheduled ≤ cutoff` and a `priority` whose value maps to a configured level. **Exclude** Next `[*]`, In Progress `[/]`, done/canceled/unknown statuses, `^prj` lifecycle tasks, tasks linked under **today's open Pomodoros**, fenced code, and the hooks walker's excluded directories (`done/`, `_conflicts/`, `_templates/`, `_generated/`, dot-dirs). | Keeps "today's work" intact. Matches the picker and hooks semantics. 15 done/canceled tasks carry due dates today. |
| **A2** | **Skip and warn** (never guess) on multiple `scheduled` fields, invalid dates, or a priority value not in the config (e.g. `highest`). | Same policy as `projects sync` and `capture_task_toggle`. |
| **A3** | Each re-rolled task **also becomes Blocked `[?]`** when its new date is in the future, and each touched area/project note is **regrouped** with `task_status_groups::transform`. All of this is composed in memory and written once per note. | Makes the single commit complete and revertible. The picker already flips to Blocked. The next hooks run then has nothing to do on those notes. |
| **A4** | Add **`-u, --until DATE`** (also accepts `+N` days). Randomize prioritized tasks scheduled **on or before `DATE`** and roll each window **from `DATE`**. Default `DATE` = today, which gives exactly your specified behavior. | Directly serves "focus on P0 for N days." `--until +14` means nothing prioritized resurfaces for 2 weeks, and afterwards tasks come back spread by priority. Also sweeps tasks that would have come due during the focus period. |
| **A5** | Write a **Schedule Log entry per task** in picker format, with a distinct head, e.g. `*2026-09-13 → 2026-10-19* — 🎲 P2 randomize · in **21** (8–30) days`. With `--until`: `… · **17** (8–30) days after 2026-10-12`. Create the marker when it's missing, as the picker's automatic path does. | Auditability, zombie detection, parity with 🎲 rolls. `SCHEDULE_LOG_ENTRY_RE` accepts any reason text. |
| **A6** | **Git contract:** take the lock, run vault-sync, plan and write, make one scoped commit, run vault-sync again, all under a single lock hold. Never amend, rebase, force, or push directly. | See §6. |
| **A7** | Add `-d/--dry-run` (plan, calendar histogram, no lock, no writes) and `-s/--seed N` (reproducible rolls). | 200+ edits deserve a preview. A seed makes "what you previewed is what you get." |
| **A8** | Consider naming it **`bob reroll`**. | The vault already calls this a "roll" (🎲, `Ctrl+R` re-roll, `P2 roll`). Your call; everything below says `randomize`. |

Deferred to phase 2 (not v1): load-aware balancing (`--balance`), priority
demotion (`--demote`, logging `P1 → P2`), and a "rolled N times" report.

---

## 5. Per-task edit design

**Minimal, merge-friendly line edits.** Replace only the date inside the
existing `scheduled` field, keeping its spacing (`[scheduled::X]` vs
`[scheduled:: X]`) and bracket or paren form. Don't canonicalize the rest of
the line. Per task, the diff is then:

1. one changed task line (date, plus `[ ]`→`[?]`),
2. one inserted Schedule Log line directly under the existing marker.

Grouping then moves the whole root block into `### Blocked`. That move is
unavoidable (hooks would do it anyway) and happens in the same write.

Reusable pieces:

- **Scheduled field.** `capture_task_toggle.rs:1396` `scheduled_field_matches`
  (bracket and paren forms, counts duplicates) and `parse_strict_calendar_date`.
- **Task scan.** `note_tasks::scan` / `read_settings`: status type, block ID,
  block end, line digest, Tasks global filter, fence awareness.
- **Status flip.** `capture_task_toggle.rs:1360` `set_task_line_status`.
- **Schedule Log insertion.** `capture.rs:6233`
  `first_direct_managed_log_start`, `capture.rs:6199`
  `first_child_indentation`, and the insert pattern in `plan_task_next`
  (`capture_task_toggle.rs:70`). Randomize additionally needs the
  create-marker branch (append `\t- 🗓️ **SCHEDULE LOG**` plus entry as the
  last direct child), which is `capture_schedule_log::plan` generalized.
- **Grouping and guards.** `task_status_groups::transform`, plus hooks'
  `task_group_classification`, `task_grouping_eligible`,
  `validate_blocked_status` (fail before any write if the Tasks registry lacks
  a compatible `?` Blocked status), and `markdown_files`. Make these
  `pub(crate)` or move them to a shared module.
- **Open-Pomodoro links.** `capture_active_tasks` /
  `pomodoro::pomodoros_section_range` to find block links under today's open
  entries and exclude those tasks.

**Order within one note:** for each candidate from the bottom up (so byte
offsets stay valid), edit the date, flip the status, and insert the log entry.
Then run `transform()` once on the result.

**Line endings:** preserve CRLF/LF. The helpers above already do.

**Seeds.** Derive each task's seed from the stable identity of that task, not
from its enumeration index. For example:
`mix64(seed ^ hash(relative_path) ^ hash(line_digest))`. Then a dry-run and a
later real run with the same `--seed` produce identical dates for every
unchanged task, even if the pre-run pull added tasks elsewhere. The `mix64 %
span` modulo bias is negligible for spans of 365 or less.

---

## 6. Committing without fighting `vault-sync`

### 6.1 Options compared

| Option | How | Single commit? | Safe with vault-sync? | Verdict |
| --- | --- | --- | --- | --- |
| **O1. Write files and let background sync commit** | No git code | **No.** The inotify watcher (athena/apollo) or the 15-second LaunchAgent (Mac) can fire between note 5 and note 6 and push a half-randomized vault. Holding the lock fixes the split, but you still get a generic `vault(host)` message that sweeps in unrelated dirty files. | Mostly | Reject |
| **O2. `move-done-tasks` style** | `git add -- paths; git commit -- paths; git push` | Yes | **No.** No lock when run standalone, no fetch or merge, so a raw push is rejected whenever the Mac pushed first. `commit -- paths` also silently includes unrelated unstaged edits in those files. | Reject |
| **O3. Write, then one vault-sync cycle with `--message`** | Reuse `RunOptions.message` | Yes | Yes | Close second. Its `git add -A .` sweeps in anything else that became dirty. |
| **O4. Locked sync → write → scoped commit → sync** | `nightly`-style composition under one lock hold | **Yes**, and scoped to exactly the notes randomize wrote | **Yes.** Reuses vault-sync's recovery, merge, conflict and push-retry logic. | **Recommend** |

### 6.2 O4 step by step

1. **Acquire `bob_sync.lock`** with a bounded wait (about 30 seconds) and a
   visible "waiting for vault-sync…" message. Unlike `vault-sync`, an
   interactive command must never exit 0 silently when the lock is held.
   While randomize holds the lock, the background watcher, LaunchAgent,
   `nightly` and hooks runs on this host back off.
2. **Pre-sync:** `vault_sync::run_cycle_with_existing_lock`. This commits any
   pre-existing dirty edits as an ordinary `vault(host)` commit, pulls the
   latest Mac edits, and pushes. It leaves the tree clean at the remote tip, so
   randomize plans against the freshest state and its commit contains only its
   own changes. If it fails (offline, unhandled conflict), **abort before any
   write** unless `--offline` was given.
3. **Plan** (pure function) and print the plan.
4. **Apply** through the guarded writer: 2-second quiet period, byte-identity
   preflight, recovery copies, atomic renames. A `vault_changed` abort (you
   saved a note in Obsidian mid-run) should retry the plan once, then fail
   with no writes.
5. **Scoped commit:** `git add -- <applied paths>`, then `git commit -F - --
   <applied paths>` with a message like:

   ```text
   bob randomize: 222 tasks in 28 notes (P1 85, P2 132, P3 5)

   until: 2026-09-28 · seed: 0x5f3a9c…
   sase.md: 130
   cash.md: 14
   …
   ```

6. **Post-sync:** run `run_cycle_with_existing_lock` again for fetch, merge
   (a merge commit only if the remote moved), push retries, and the status
   record. Refactor it to return a small `CycleReport` (conflicts, pushed or
   not, SHAs) instead of a bare `i32`, so randomize can report precisely.
7. Release the lock.

The resulting history on master is: optional `vault(host)` pre-commit, then
**one** `bob randomize` commit, then an optional merge commit. The last two
are exactly what vault-sync produces today, and the randomize edits live in
one commit.

### 6.3 Failure modes and why they're benign

- **Cross-machine conflict.** The race window is only the few seconds between
  the pre-sync fetch and the post-sync push. If the Mac pushes an edit adjacent
  to a randomized line in that window, vault-sync keeps the remote note and
  moves randomize's version to `_conflicts/`. Randomize must print a loud
  warning naming the notes.

  **Re-running `bob randomize` converges.** Those tasks are still due, so the
  second run re-rolls exactly the missed ones. Randomize is idempotent (after a
  run nothing is due and prioritized), and its edits have no cross-note
  coupling. Both properties matter here.
- **Partial apply** (I/O error after some renames). Each applied note is
  self-consistent, so commit the applied subset, report the remainder, keep
  the recovery manifest, and tell the user to re-run.
- **Push failure** after a successful commit: the commit stays local and the
  background vault-sync pushes it later. Exit 1 with "committed <sha> locally;
  push will retry."
- **Non-git vault:** skip the commit with a warning, as `move-done-tasks` does.

**Operational guidance for the docs:** prefer running it on the machine where
you edit (the Mac). Local races there are *detected* by the guarded writer,
whereas remote races are only *resolved* by vault-sync quarantining a note.
Close or avoid typing in `sase.md` while it runs; as the hooks docs already
note, an unsaved Obsidian buffer isn't observable.

**Undo:** `git -C ~/bob revert <randomize-sha> && bob vault-sync`. This is
clean as long as later edits haven't touched those lines. The guarded writer's
recovery manifest also keeps the originals.

---

## 7. Why not the alternatives?

- **Implement it as an Obsidian command in `bob-plugins`.** It would have
  perfect editor-race safety, but only on the Mac with Obsidian open. It can't
  guarantee one commit (the 15-second LaunchAgent can split it) and it
  duplicates vault-wide scanning that bob-cli already owns. The picker's
  counted roll already covers the in-editor, per-note case.
- **Run `task-status-hooks` in-process after the date edits,** instead of only
  its grouping transform. It needs a refactor to accept an existing lock, and
  it would drag unrelated changes (Next clears, Pomodoro cleanup, daily-note
  edits) into the randomize commit. It also refuses to run without today's
  daily note. Composing only `transform()` on the notes randomize touches
  gives the same final bytes for those notes with none of that coupling.
- **Rely on hooks for the Blocked flip and grouping.** This produces the
  second commit and the revert problem described in §3.3.

---

## 8. Recommended solution

### 8.1 CLI

```text
bob randomize [-d|--dry-run] [-f|--format human|json] [-l|--level LABEL]... [-o|--offline] [-s|--seed N] [-u|--until DATE|+N]
```

Options are sorted alphabetically and every long option has a short alias,
per `cli_rules.md`.

| Option | Behavior |
| --- | --- |
| `-d, --dry-run` | Scan, plan, and print the full plan plus a per-day load histogram. No lock, no sync, no writes. Prints the seed. |
| `-f, --format human\|json` | Optional. JSON is useful for tests and for any future Mac Capture or plugin integration. |
| `-l, --level LABEL` | Optional and repeatable (`-l P2 -l P3`). Restricts to those levels, which is handy for leaving P1s to hand triage. |
| `-o, --offline` | Skip both vault-sync cycles but still make the scoped commit. For offline laptops and tests. |
| `-s, --seed N` | Deterministic rolls. Falls back to `BOB_PRIORITY_ROLL_SEED`, then time and PID via `config::roll_seed`. |
| `-u, --until DATE\|+N` | Cutoff and roll base. Default: today, honoring `BOB_NOW`. Must be today or later. |

Environment: `BOB_DIR`, `BOB_CONFIG_FILE`/`XDG_CONFIG_HOME`, `BOB_NOW`,
`BOB_DAY_FILE` (for today's ledger), `BOB_PRIORITY_ROLL_SEED`,
`BOB_VAULT_SYNC_LOCK_FILE`, `BOB_VAULT_SYNC_STATE_FILE`, `NO_COLOR`.

Exit codes: `0` success or nothing to do, `1` failure (including a partial
apply or a push failure after commit), `2` usage error.

### 8.2 Output (human, colored)

```text
bob randomize · Mon 2026-09-28 · ~/bob
  until 2026-09-28 · seed 0x5f3a9c…
  due prioritized: 224 · skipped: 1 next, 1 in-progress, 2 in today's Pomodoros · 0 ambiguous
  P1 high     85 → 2026-09-30 … 2026-10-05
  P2 medium  132 → 2026-10-06 … 2026-10-28
  P3 low       5 → 2026-10-29 … 2026-12-27
  load (next 30d): ▇▇█▇▇▇▂▂▁▂▂▂▂…   peak 26 on Fri 2026-10-02
  notes: sase.md 130 · cash.md 14 · bob.md 12 · … (28)
git
  pre-sync   ok  (origin/master 1a2b3c4)
  commit     4e5f6a7  bob randomize: 222 tasks in 28 notes (P1 85, P2 132, P3 5)
  post-sync  ok  pushed
```

The peak-day line makes the P1 wall visible *before* you commit.

### 8.3 Module plan

- **`src/native/randomize.rs` (new):** clap CLI in the same style as
  `vault_sync.rs`; `plan(vault_snapshot, config, until, seed) -> Plan`
  (pure); a printer; orchestration (lock → sync → apply → commit → sync).
- **`config.rs`:** `PriorityProperty::level_for_value(&str) -> Option<(n,
  &PriorityLevel)>` (trimmed, case-insensitive). Make the missing-config error
  command-neutral (today it says "p:<N> needs …").
- **Shared task-field helpers:** lift `scheduled_field_matches`,
  `parse_strict_calendar_date` and Schedule Log insertion (existing marker, or
  create marker) out of `capture_task_toggle.rs`/`capture.rs` into
  `capture_schedule_log.rs` or a new `task_fields.rs`. Add a
  `randomize_reason(label, rolled, min, max, base)` formatter next to
  `priority_roll_reason`.
- **`task_status_hooks.rs`:** expose `markdown_files`,
  `task_group_classification`, `task_grouping_eligible` and
  `validate_blocked_status` as `pub(crate)`.
- **`task_status_hooks_write.rs`:** parameterize the command name in messages
  and the recovery `STATE_SUBDIR` (e.g. `randomize/`). Otherwise reuse as is.
- **`vault_sync.rs`:** add
  `run_cycle_with_existing_lock_report(opts) -> CycleReport` (conflicts,
  pushed, SHAs, error). Keep the `i32` wrapper for `nightly`.
- **`ob.rs`:** add `acquire_lock_waiting(timeout)` for interactive commands.
- **`runner.rs`:** register `randomize` between `query` and
  `task-status-hooks` (the table is alphabetical and guarded by a test). Add
  it to the top-level help examples.
- **Docs:** a README command-table row and section, plus a new
  `docs/randomize.md` contract. Cross-link from `docs/projects.md` ("Priority
  property and scheduled rolls") and `docs/vault-git-sync.md`.

### 8.4 Tests

**Unit tests** on the pure planner:

- spacing, bracket and paren variants preserved; CRLF preserved
- skips: multiple `scheduled`, invalid date, unknown priority, `[*]`, `[/]`,
  `[x]`, `[-]`, `^prj`, fenced code, excluded directories, today's
  open-Pomodoro links
- Schedule Log: prepended under an existing marker using the entry indent;
  marker created when missing
- reason format byte-exact, including `--until`
- `[ ]`→`[?]`; a rolled date equal to the old date gets no log entry
  (`min_days: 0`)
- grouping moves the block to `### Blocked` and refreshes the badge row
- same seed gives the same dates even after unrelated tasks are added
- date math across month, year and leap boundaries

**Integration tests** in `tests/cli.rs`, reusing the existing bare-remote
fixtures from the `vault_sync_*` tests:

- exactly one new `bob randomize:` commit, clean tree, pushed
- a pre-existing unrelated dirty file lands in a *separate* `vault(host)`
  commit
- a remote-ahead, non-overlapping edit merges cleanly
- a same-line remote edit produces a conflict copy, a loud warning and a
  non-zero exit, and a re-run converges
- lock held: bounded wait, then a clear failure
- `--dry-run`: no lock, no writes, no commits
- `--offline`: commit without push
- a non-git vault gets a warning and no commit
- **after randomize, `bob task-status-hooks --dry-run` reports no changes for
  the touched notes.** This is the key parity test.

### 8.5 Phasing

1. **Phase 1 (v1):** everything in §8.1–8.4 with uniform independent rolls
   (exact picker and `p:<N>` parity).
2. **Phase 2:**
   - `-b/--balance`: load-aware placement, using the existing future load
     from the same scan (see the §3.2 numbers; about 30 lines of logic).
   - `--demote`: shift the level down one step and log `P1 → P2`.
   - A report of tasks with 3 or more `randomize` entries, to catch zombies.
   - Optionally an Obsidian command in `bob-navigation-hotkeys` that shells
     out to `bob randomize --dry-run --format json` for an in-editor preview.

---

## 9. Open questions for you

1. Should Next or In Progress tasks ever be included (e.g. behind a flag)? I
   recommend always excluding them.
2. Reason head: a distinct `randomize` (my recommendation, for auditability)
   or the existing `roll` (identical to the picker's pinned re-roll)?
3. Do you want `--until` to accept `+N` in addition to ISO dates? It's
   friendlier for the "focus for two weeks" case.
4. Is the P1 wall acceptable in practice (P1 does mean "this week"), or should
   phase 2's `--balance` or `--demote` land in v1?
5. Name: `randomize` or `reroll`?

---

## Sources

External:

- [Todoist "Reschedule" and Smart Schedule for overdue tasks (MacStories)](https://www.macstories.net/news/todoist-launches-smart-schedule-an-ai-based-feature-to-reschedule-overdue-tasks/)
- [The Ultimate Guide to Using Todoist (Doist, Medium)](https://medium.com/ten-timezones/the-ultimate-guide-to-using-todoist-f8237f1f75ed)
- [FSRS Helper README: Postpone, Load Balance, Easy Days](https://github.com/open-spaced-repetition/fsrs4anki-helper/blob/main/README.md)
- [FSRS Helper on AnkiWeb](https://ankiweb.net/shared/info/759844606)
- [Anki Load Balancer guide (willpeachMD)](https://willpeachmd.com/anki-load-balancer)
- [I Declare To-Do List Bankruptcy (Todoist)](https://www.todoist.com/inspiration/todo-list-bankruptcy)
- [How declaring to-do list bankruptcy made me more productive (Fast Company)](https://www.fastcompany.com/90383750/how-to-manage-an-overflowing-to-do-list)

Internal (read for this report):

- `bob-cli`:
  - `src/native/{config.rs, capture.rs, capture_schedule_log.rs, capture_task_toggle.rs, collect_done.rs, nightly.rs, ob.rs, projects.rs, task_status_groups.rs, task_status_hooks.rs, task_status_hooks_write.rs, vault_sync.rs, note_tasks.rs}`
  - `src/runner.rs`
  - `README.md`
  - `docs/{task-status-hooks.md, projects.md, vault-git-sync.md}`
- `bob-plugins`: `plugins/bob-navigation-hotkeys/main.js`, the Schedule Log
  planner and the counted priority transaction
- `~/.config/bob/config.yml` (deployed config)
- Live vault `~/bob`: read-only scans for the counts in §2 and the simulation
  in §3.2; git log for the commit cadence
