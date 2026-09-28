# Engineering Research Report: `bob randomize` Subcommand Architecture, Safety, and Design Critique

**Researcher**: `gem` (Independent Swarm Evaluation)  
**Date**: September 28, 2026  
**Status**: Completed Research & Proposal  
**Artifact ID**: `research:202609/bob_randomize_command_design_and_critique__gem.md`

---

## 1. Executive Summary & Problem Framing

### 1.1 The Operational Context
In Bryan's personal productivity and task management architecture (`bob-cli` and the Bob Obsidian vault), tasks are tracked as Markdown checklist items annotated with Dataview-style inline properties (e.g., `[priority:: high]`, `[scheduled:: 2026-09-10]`, `^block-id`). The system enforces a strict priority and scheduling taxonomy defined in `~/.config/bob/config.yml`:

- **Implicit P0 (Do It Now / Unrolled)**: Any task lacking an explicit `[priority:: ...]` field is implicitly **P0**. P0 tasks represent top-tier, non-negotiable commitments that demand immediate attention and are never randomly deferred.
- **Explicit Lower Priorities (<P0)**: Tasks carrying explicit priority levels represent lower-urgency work distributed across configured time horizons:
  - **P1 (`high`)**: 2 to 7 days
  - **P2 (`medium`)**: 8 to 30 days
  - **P3 (`low`)**: 31 to 90 days
  - **P4 (`lowest`)**: 91 to 365 days

When tasks reach their scheduled date (`scheduled <= today`), Bob's status hooks (`bob task-status-hooks`) unblock them, transitioning them from Blocked (`[?]`) to Ready (`[ ]`). 

### 1.2 The User Request
When several days or weeks pass without active backlog maintenance, dozens or hundreds of previously scheduled lower-priority tasks inevitably become due or overdue. This creates a "task flood" where low-priority backlog clutter obscures active P0 initiatives.

The user proposes a new native CLI subcommand, `bob randomize`, to:
1. Identify all currently due, scheduled, and prioritized tasks (`scheduled <= today` AND `priority` is present).
2. Reschedule each matching task independently using a random date drawn from its priority level's configured day range in `~/.config/bob/config.yml`.
3. Commit all resulting file modifications in a single atomic Git commit.
4. Ensure the operation does not interfere or conflict with automated vault synchronization (`bob vault-sync`).

### 1.3 High-Level Evaluation
The proposal addresses a real and recurring cognitive bottleneck ("task review paralysis"). However, a naive implementation poses significant operational risks:
- Risk of rescheduling active, in-progress, or Pomodoro-linked tasks.
- Inconsistencies with Bob's Schedule Log audit convention (`🗓️ **SCHEDULE LOG**`).
- Checkbox status misalignment (leaving future-scheduled tasks marked Ready `[ ]` instead of Blocked `[?]`).
- Race conditions or Git index corruption if executed concurrently with `bob vault-sync`.
- Sweeping unrelated working-tree modifications into the Git commit if staging is not strictly bounded to touched paths.

This report evaluates the plan, critiques its trade-offs, refines the behavioral specification, solves the Git and `vault-sync` concurrency constraints, and presents a concrete architectural design adhering to all SASE and Bob CLI rules.

---

## 2. In-Depth Critique of the Plan

### 2.1 The Value Thesis: Why This Command Is Justified
1. **Defending P0 Focus (Cognitive Bandwidth Preservation)**:  
   When a user returns after an absence, facing 80 overdue tasks produces severe decision fatigue. Because P0 tasks carry no priority property and are meant for immediate execution, batch-deferring all `<P0` tasks instantly restores focus to P0 work without requiring manual evaluation of each individual item.
2. **Aligning with Existing Config Philosophy**:  
   The day windows in `~/.config/bob/config.yml` were specifically designed to space out lower-priority work across realistic horizons (e.g., P2 tasks across a month; P4 across a year). Batch rescheduling is the logical extension of the single-task picker roll implemented in `bob-navigation-hotkeys` (`Ctrl+Shift+P`).
3. **Preventing "Task Bankruptcy" Abandonment**:  
   Without an automated bulk-deferral mechanism, users overwhelmed by hundreds of red overdue badges often stop maintaining their task system entirely. `bob randomize` functions as an operational safety valve.

### 2.2 Critical Risks, Weaknesses, and Failure Modes

#### A. The "Infinite Deferral" / Starvation Trap
- **The Issue**: Continually kicking overdue tasks into the future without reviewing them can turn the backlog into a permanent digital landfill. A P2 task rolled 5 times over 5 months has effectively been abandoned without a deliberate decision to cancel or delete it.
- **Mitigation / Adjustment**:  
  - The tool should output a transparent summary table by priority level and note origin.
  - Retain the full Schedule Log trail on each task so the number of previous rolls is immediately visible in Obsidian (`*<old> → <new>* — 🎲 P2 roll...`).
  - Consider adding a `--max-rolls <N>` flag in future iterations to flag chronically deferred tasks for explicit deletion or cancellation.

#### B. The Risk of Yanking In-Progress or Committed Tasks
- **The Issue**: Suppose Bryan returned yesterday and pulled one P1 task into today's active Pomodoro or marked it In Progress (`[/]`) or Next (`[*]`). If `bob randomize` naively selects all tasks where `scheduled <= today`, it would snatch that active task out of his workflow and reschedule it for next week.
- **Adjustment**:  
  - **Eligibility must strictly exclude**:
    1. Tasks with status `[/]` (In Progress) or `[*]` (Next).
    2. Completed tasks (`[x]`, `[X]`) and cancelled tasks (`[-]`).
    3. Tasks referenced as children under open or completed Pomodoro entries in today's daily ledger (`default_day_file`).
  - Only truly unstarted tasks (`[ ]` Ready and `[?]` Blocked) should be candidates for randomization.

#### C. Inadvertent Date Clustering
- **The Issue**: Uniform independent pseudo-random sampling across small windows (e.g., P1 with 2–7 days) can naturally cluster multiple tasks onto the exact same day. If 10 P1 tasks are randomized, statistics dictate that 3 or 4 will likely collide on the same date.
- **Evaluation**: While true load-balancing (bin-packing across calendar days) is possible, keeping independent sampling maintains simplicity and matches the behavior of the Obsidian plugin picker. The variance across P2 (22 days), P3 (60 days), and P4 (275 days) makes heavy clustering unlikely for lower tiers. Independent rolling per task should be preserved.

#### D. The "Dirty Vault" Git Staging Hazard
- **The Issue**: If the implementation stages changes using `git add -A .` or `git add <vault>`, and Bryan has unsaved or half-edited notes elsewhere in his vault, those unrelated files will be swept into the `randomize` commit.
- **Adjustment**:  
  - `bob randomize` **must only stage the exact list of files it modified** (`git add -- <touched_path1> <touched_path2> ...`).
  - Staging must never use global worktree wildcards.

---

## 3. Detailed Requirements & Technical Adjustments

### 3.1 Task Eligibility Rules
A checklist line in a Markdown file qualifies for `bob randomize` if and only if all of the following conditions hold:

| Criterion | Rule | Justification |
| :--- | :--- | :--- |
| **Note Scope** | In a markdown file (`.md`) within the vault, excluding hidden directories, `_conflicts/`, `_generated/`, `_templates/`, and `.obsidian/`. | Uses `bob-cli`'s canonical `is_always_excluded_note_directory_name`. |
| **Status Symbol** | Checkbox is open: `[ ]` (Ready) or `[?]` (Blocked). | Tasks marked `[*]`, `[/]`, `[x]`, `[X]`, `[-]` are active or finished. |
| **Global Filter** | Line contains the Tasks global filter (if configured in Tasks settings, e.g. `#task`). | Conforms to Obsidian Tasks plugin indexing rules. |
| **Priority Property** | Line contains `[priority:: <val>]` or `(priority:: <val>)` matching a configured level in `config.yml`. | Tasks lacking priority are implicit P0 and must not be touched. |
| **Scheduled Property** | Line contains `[scheduled:: <date>]` or `(scheduled:: <date>)` with a valid `YYYY-MM-DD` date where `<date> <= today`. | Future-scheduled tasks are already deferred; tasks without `scheduled` are unpinned. |
| **Active Pomodoro Link** | Task is not transcluded or block-linked under an open Pomodoro bullet in today's daily note. | Prevents rescheduling work currently being performed. |

### 3.2 Date Calculation & PRNG Specification
- **Base Date (`today`)**: Derived from `bob_env::current_datetime()` (which honors `BOB_NOW` and `DATE` environment variables for reproducible CLI testing).
- **Day Offset**: For a task with priority level $L$, where $L$ defines `[min_days, max_days]`:
  $$\text{span} = \text{max\_days} - \text{min\_days} + 1$$
  $$\text{offset} = \text{min\_days} + (\text{mix64}(\text{seed}) \pmod{\text{span}})$$
- **New Date**:
  $$\text{new\_scheduled} = \text{today} + \text{Duration::days}(\text{offset})$$
- **Seed Management**:
  - `seed` advances per task by mixing the base seed with the task's block ID or file path + line index, ensuring each task gets an independent roll even in tight batch loops.
  - The CLI must accept an optional `--seed <U64>` flag (and honor `BOB_PRIORITY_ROLL_SEED`) for 100% deterministic test fixtures and dry-run parity.

### 3.3 Schedule Log Entry Formatting
In Bryan's vault, automated rolls append to the task's `🗓️ **SCHEDULE LOG**` child bullet. Investigation of actual vault files (`sase_memory.md`, `dev.md`) reveals the exact live format:

```markdown
- [ ] #task Migrate `/sase_git_commit` to `/sase_stitch`! [created::2026-08-20] [priority:: high] [scheduled:: 2026-09-10] ^commit-to-stitch
	- 🗓️ **SCHEDULE LOG**
		- *2026-09-07 → 2026-09-10* — 🎲 P1 roll · in **2** (2–7) days
		- *2026-08-31 → 2026-09-07* — 🎲 P1 roll · in **7** (2–7) days
```

To maintain byte-level parity with `capture_schedule_log.rs` and `bob-navigation-hotkeys/main.js`:
1. **Entry Shape**:
   ```
   *<old_date> → <new_date>* — 🎲 <label> roll · in **<offset>** (<min_days>–<max_days>) days
   ```
2. **Placement**:
   - New Schedule Log entries are **prepended** at the top of the existing Schedule Log entry list (directly below the `🗓️ **SCHEDULE LOG**` marker).
   - If the task does not have an existing `🗓️ **SCHEDULE LOG**` bullet, `bob randomize` should create the marker bullet indented as a child of the task, followed by the entry bullet indented as a grandchild.
   - Indentation style (tabs vs spaces) must match the existing file's indentation convention (or inherit the task's child indentation).

### 3.4 Checkbox Status Transition: `[ ]` $\rightarrow$ `[?]`
In Bob's system architecture (`src/native/task_status_hooks.rs`):
> *"Tasks whose task-level [scheduled:: YYYY-MM-DD] date is later than the effective daily anchor, are marked Blocked [?], overriding Ready, Next, and In Progress."*

When `bob randomize` rolls a task's scheduled date from today/past into the future:
- If the task was Ready (`[ ]`), leaving it as `[ ]` creates a temporary semantic contradiction: the note says Ready, but the date is in the future.
- When `bob task-status-hooks` subsequently runs, it will immediately rewrite that task from `[ ]` to `[?]`.
- **Recommendation**: `bob randomize` should directly update the task's checkbox status to `[?]` (Blocked) in the same pass. This avoids intermediate file churn and immediately reflects the task's blocked status across Obsidian Dataview and Tasks views.

---

## 4. Git Transaction Safety & `bob vault-sync` Harmonization

The user's prompt emphasizes:
> *"If possible, we should try to commit the file changes made by this command using a single commit. Make sure that our single commit doesn't cause issues with / conflict with the `bob vault-sync` command."*

### 4.1 How `bob vault-sync` Operates
An analysis of `src/native/vault_sync.rs` and `src/native/ob.rs` shows how vault synchronization works:
1. **Mutual Exclusion Lock**:
   `vault-sync` calls `ob::acquire_lock_quiet_if_held()`, which opens `BOB_VAULT_SYNC_LOCK_FILE` (`/tmp/bob_sync.lock` or `$XDG_RUNTIME_DIR/bob_sync.lock`) and acquires an exclusive `fs2::FileExt::try_lock_exclusive()`. If held by another process, `vault-sync` immediately exits with code 0 (quietly yielding).
2. **Cycle Flow**:
   - Verifies the Git worktree.
   - Aborts any interrupted merge/rebase (`MERGE_HEAD`).
   - Checks `git status --porcelain=v1 -z -uall`.
   - Stages all changes: `git add -A .`.
   - Commits staged changes if any: `git commit -F -` with message `vault(<host>): <N> files...`.
   - Fetches `origin/master`.
   - Merges or fast-forwards `origin/master`.
   - Quarantines unresolvable conflicts to `_conflicts/`.
   - Pushes local `HEAD:master` to `origin` with up to 3 retries.
   - Updates `~/.local/state/bob-cli/vault-sync.json`.

### 4.2 Potential Conflicts and Failure Scenarios

| Scenario | Risk | Solution in `bob randomize` |
| :--- | :--- | :--- |
| **Concurrent Execution** | `vault-sync` runs via timer while `randomize` is half-way through modifying notes on disk. | `bob randomize` **must acquire `ob::acquire_lock()`** before reading/modifying files. If `vault-sync` triggers, it will see the lock held and exit cleanly. |
| **Git Index Lock Collision** | Both processes attempt to stage or commit at the same moment, causing `.git/index.lock` failures. | Prevented completely by holding the exclusive maintenance file lock throughout `randomize`. |
| **Staging Contamination** | `randomize` executes `git add -A .` while the user has unrelated dirty files. | `randomize` **must only stage its touched file paths**: `git add -- <paths...>`. |
| **Diverged History / Push Rejection** | `randomize` commits and pushes directly using raw `git push`, but remote master has new commits from another device. | Instead of a raw `git push`, `randomize` should use the established sync pipeline: either invoke `vault_sync::run_cycle_with_existing_lock` or follow the fetch-merge-push protocol. |

### 4.3 Recommended Git Workflow for `bob randomize`

```
┌────────────────────────────────────────────────────────┐
│ 1. Acquire Maintenance Lock (ob::acquire_lock())       │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 2. Preflight Working Tree & Remote Sync                │
│    - Ensure no unresolved MERGE_HEAD in vault          │
│    - Optional: Fetch origin/master                     │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 3. Scan & Plan Modifications                           │
│    - Read config.yml & vault notes                     │
│    - Find qualifying tasks; compute new dates & logs   │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 4. Apply Changes to Disk                               │
│    - Atomic write per modified file                    │
│    - Track exact list of modified PathBufs             │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 5. Stage Touched Files ONLY                            │
│    - git -C <vault> add -- <touched_files...>          │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 6. Create Dedicated Single Git Commit                  │
│    - git -C <vault> commit -m "<structured_message>"   │
│      -- <touched_files...>                             │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 7. Reconcile & Push via Vault-Sync Logic               │
│    - Call vault_sync::run_cycle_with_existing_lock()   │
│    - Handles push retries, remote merges, status JSON  │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 8. Release Lock & Report Summary to User               │
└────────────────────────────────────────────────────────┘
```

#### Commit Message Format
To keep vault history legible, `bob randomize` should use a structured commit message:
```text
randomize: reschedule 42 overdue tasks across 8 notes

- P1 (high): 6 tasks (2–7 days)
- P2 (medium): 18 tasks (8–30 days)
- P3 (low): 14 tasks (31–90 days)
- P4 (lowest): 4 tasks (91–365 days)
```

---

## 5. Subcommand CLI Design & Interface Contract

Adhering strictly to `cli_rules.md`:
- Alphabetically sorted subcommands and options.
- Short alias for every public option.
- Full, clean `-h|--help` output.
- Colored output using `Styler` when stdout is a TTY.

### 5.1 CLI Syntax

```text
Usage: bob randomize [OPTIONS]

Re-schedule currently due prioritized Obsidian tasks using randomized dates.

Options:
  -b, --bob-dir <PATH>         Bob vault root; defaults to BOB_DIR or ~/bob
  -c, --commit                 Commit and push modified notes via Git [default: true]
  -n, --dry-run                Report planned changes without modifying files or Git
  -f, --format <FORMAT>        Output format: human or json [default: human]
  -m, --message <MSG>          Override default Git commit message
      --no-commit              Write file changes without creating a Git commit
      --no-log                 Update scheduled dates without writing Schedule Log entries
      --no-push                Commit changes locally without pushing to remote
  -p, --priority <LEVELS>      Comma-separated priority levels to randomize (e.g. P1,P2,P3,P4)
                               [default: all configured <P0 levels]
  -q, --quiet                  Suppress per-task progress; only report summary and errors
  -s, --seed <U64>             PRNG seed for reproducible date rolling (overrides BOB_PRIORITY_ROLL_SEED)

Examples:
  bob randomize --dry-run
  bob randomize
  bob randomize --priority P3,P4
  bob randomize --format json
  bob randomize --no-commit
```

### 5.2 Dry-Run Output Example
Running `bob randomize --dry-run` produces an immediate, high-fidelity report:

```text
bob randomize: planning task rescheduling (dry-run)
vault: /home/bryan/bob
today: 2026-09-28

  P1 (high · 2–7d):
    sase_memory.md:18
      "Migrate `/sase_git_commit` to `/sase_stitch`!"
      scheduled: 2026-09-10 -> 2026-10-02 (+4d)
      status: [ ] -> [?]

  P2 (medium · 8–30d):
    dev.md:26
      "Change your phone screen protector!"
      scheduled: 2026-09-12 -> 2026-10-18 (+20d)
      status: [ ] -> [?]

Summary:
  Would reschedule 24 tasks across 6 notes (P1: 4, P2: 12, P3: 6, P4: 2).
  Would write 1 Git commit: "randomize: reschedule 24 overdue tasks across 6 notes".
  Dry-run complete; no files modified.
```

---

## 6. Architecture & Implementation Plan

### 6.1 Codebase Integration Points

1. **`src/native/randomize.rs` (New Module)**:
   - Implements the complete subcommand logic:
     - `pub(crate) fn run(args: Vec<OsString>) -> i32`
     - Vault scanning via `fs::read_dir`, excluding `is_always_excluded_note_directory_name`.
     - Task parsing using regex matching for `[priority:: <val>]` and `[scheduled:: <val>]`.
     - Priority mapping via `config::load_priority_property(&config_path())`.
     - Schedule Log generation via `capture_schedule_log`.
     - Line replacement with line-ending preservation (`\r\n` vs `\n`).
     - Atomic file writes.
     - Git staging, commit creation, and sync delegation.
2. **`src/native.rs`**:
   - Register `mod randomize;`.
   - Add `Randomize` to `enum NativeCommand`.
   - Dispatch `NativeCommand::Randomize => randomize::run(args)`.
3. **`src/runner.rs`**:
   - Insert `Subcommand` entry into `SUBCOMMANDS` array in strict alphabetical order:
     ```rust
     Subcommand {
         name: "randomize",
         script_command: None,
         about: "Re-schedule currently due prioritized tasks with random dates",
         native_command: NativeCommand::Randomize,
     },
     ```
     (Placed between `"projects"` and `"query"`).
4. **`src/native/vault_sync.rs`**:
   - Reuse `run_cycle_with_existing_lock(&child_env)` to cleanly reconcile and push after `randomize` creates its commit.

### 6.2 Task Parsing & Line Rewriting Engine
Rather than loading the heavy Tasks JavaScript sandbox (which is only needed for dynamic dataviewjs queries and can time out on large vaults), `randomize` should use native Rust string/regex parsing.

```rust
pub(crate) struct QualifyingTask {
    pub(crate) file_path: PathBuf,
    pub(crate) line_index: usize,
    pub(crate) raw_line: String,
    pub(crate) description: String,
    pub(crate) current_status: char,
    pub(crate) priority_level: PriorityLevel,
    pub(crate) current_scheduled: NaiveDate,
    pub(crate) new_scheduled: NaiveDate,
    pub(crate) rolled_days: u64,
    pub(crate) block_id: Option<String>,
}
```

For each modified note:
1. Parse lines into `Vec<String>`.
2. Locate qualifying tasks and their child block boundaries (`child_block_end_line`).
3. Replace `[scheduled:: <old>]` with `[scheduled:: <new>]` on the task line.
4. Replace `[ ]` with `[?]` if transitioning to Blocked.
5. If Schedule Log writing is enabled:
   - Check if `🗓️ **SCHEDULE LOG**` bullet exists among children.
   - If present: prepend the new log entry bullet directly after the marker line.
   - If absent: insert `\t- 🗓️ **SCHEDULE LOG**` and `\t\t- *<old> → <new>* — ...`.
6. Write the updated content back to disk using atomic temporary-file renaming.

### 6.3 Verification & Safety Measures
- **Pre-execution Vault Lock**: Protect against concurrent cron or manual `vault-sync` executions.
- **Pre-execution Git Worktree Check**: Ensure `git rev-parse --is-inside-work-tree` succeeds and no unmerged rebase/merge states exist.
- **Preserve Unrelated Files**: Only stage touched files (`git add -- <paths>`).
- **Comprehensive Unit & Parity Tests**:
  - Test task regex against all vault variations (`[priority:: high]`, `[priority::low]`, `(priority:: high)`).
  - Test CRLF and LF preservation.
  - Test Schedule Log insertion when marker exists vs missing.
  - Test PRNG determinism with explicit `--seed`.
  - Test `--dry-run` guarantees zero disk or Git mutations.

---

## 7. Comparative Assessment of Alternatives

| Approach | Description | Pros | Cons | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Option 1: Native CLI `bob randomize` (Proposed & Refined)** | Standalone native Rust CLI command with lock acquisition, precise staging, and optional push. | Fast; atomic; scriptable; fully integrated with Bob config and Git sync; safe dry-run mode. | Requires running a CLI command from terminal. | **Recommended Solution** |
| **Option 2: Obsidian Plugin Keymap (`bob-navigation-hotkeys`)** | Add a hotkey in Obsidian (e.g. `Ctrl+Alt+R`) to trigger bulk randomization inside the editor. | Convenient while working inside the GUI. | Obsidian JavaScript environment is single-threaded; large vaults freeze UI during bulk updates; Git commit/sync coordination is prone to desktop sync races. | Not recommended for batch vault mutations. |
| **Option 3: Automatic Nightly Rescheduling (`bob nightly`)** | Automatically randomize overdue `<P0` tasks during the nightly cron run without user interaction. | Hands-off; backlog never builds up. | Disastrous loss of agency: tasks change dates without user awareness or consent; impossible to tell if a task was intentionally deferred or silently postponed. | Strongly rejected. |
| **Option 4: Interactive Triage CLI (`bob randomize --interactive`)** | Step through each overdue task in terminal, prompting `[r]andomize / [k]eep / [d]one / [c]ancel`. | Fine-grained control over individual tasks. | Slow and tedious for 80+ overdue tasks; defeats the primary goal of rapid cognitive unblocking. | Good potential follow-up mode, but secondary to batch mode. |

---

## 8. Final Recommendation & Implementation Roadmap

### Recommendation Summary
Implement **`bob randomize`** as a native Rust CLI subcommand within `bob-cli` following the refined specification:

1. **Scope & Semantics**: Target only open, unstarted tasks (`[ ]` and `[?]`) with explicit priority (`high`, `medium`, `low`, `lowest`) and overdue schedule (`scheduled <= today`). Leave P0, active, in-progress, and Pomodoro-linked tasks untouched.
2. **Date Math**: Use `~/.config/bob/config.yml` priority windows and Bob's `mix64` PRNG with support for deterministic seeds.
3. **Auditability**: Prepend canonical `🗓️ **SCHEDULE LOG**` entries with `🎲 <label> roll` reasons.
4. **Status Consistency**: Transition rescheduled tasks to Blocked (`[?]`) to match Bob's invariant that future-scheduled tasks are blocked.
5. **Git Safety**: Hold `ob::acquire_lock()`, stage only touched paths, create a single descriptive commit, and push through `vault_sync::run_cycle_with_existing_lock`.

### Phased Roadmap

- **Phase 1 (Core Engine & Config Parser)**:
  - Add `src/native/randomize.rs`.
  - Implement task line parser, priority matching, date rolling, and unit tests.
- **Phase 2 (File Mutation & Schedule Log Integration)**:
  - Implement Schedule Log marker detection, entry formatting, and CRLF-safe file rewriting.
  - Implement `--dry-run` preview and JSON output formatting.
- **Phase 3 (Git Transaction & Lock Integration)**:
  - Integrate `ob::acquire_lock()`.
  - Implement touched-path staging (`git add -- <paths>`).
  - Wire single atomic commit creation and delegate push to `vault_sync`.
- **Phase 4 (CLI Wiring & Integration Tests)**:
  - Register `bob randomize` in `SUBCOMMANDS` table in `src/runner.rs`.
  - Add end-to-end integration tests in `tests/cli.rs` covering `--dry-run`, real execution, and Git commit verification.
