# `bob randomize`: re-scheduling due prioritized tasks — research & recommendation

**Researcher:** mus (`__mus`) — independent swarm report
**Date:** 2026-09-28
**Question:** best way to implement a new `bob randomize` command that re-schedules all
currently-due scheduled+prioritized Obsidian tasks to per-task random dates, in one
commit that does not fight `bob vault-sync`. Plus a critique of the plan itself.

## TL;DR recommendation

Build `bob randomize` as a **native Rust command** (same pattern as `bob move-done-tasks` /
`bob task-status-hooks`), which:

1. Scans vault Markdown for **open `#task` lines** with exactly one valid task-level
   `[scheduled:: YYYY-MM-DD]` (or `(scheduled:: …)`) whose date is **≤ today**, plus a
   recognized `[priority:: <value>]` field.
2. Re-rolls each task's `scheduled` date **independently** from `~/.config/bob/config.yml`
   priority levels (`min_days`/`max_days`, anchored at today), reusing the existing
   `PriorityLevel::roll_offset` / `roll_seed` machinery.
3. Rewrites only the `scheduled` field value **in place** (preserving bracket-vs-paren
   style), optionally appending a `SCHEDULE LOG` entry.
4. Holds the shared `ob` maintenance lock, writes all files, then makes **one
   path-scoped commit** (`git add -- <touched-paths>` + `git commit -m …`) and
   **does not push** — leaving fetch/merge/push to `vault-sync`. Supports `--dry-run`.
5. Ships with `--seed`, `--bob-dir`, `--dry-run`/`--format`, `-h/--help`, `BOB_NOW` /
   `BOB_PRIORITY_ROLL_SEED` overrides, JSON output, and parity-style tests.

Do **not** implement this as a shell script, do not `git add -A`, and do not push from
the command itself. Details and justification below.

---

## 1. What the codebase already gives us (reuse, don't reinvent)

### 1.1 Priority config and random-roll semantics already exist

`src/native/config.rs` owns the whole priority model:

- `~/.config/bob/config.yml` (overridable via `BOB_CONFIG_FILE` / `XDG_CONFIG_HOME`)
  declares a `priority` property with `schedules: scheduled` and `levels:` each carrying
  `label` (picker text, e.g. `P1`), `value` (what lands in the note, e.g. `high`), and an
  inclusive `[min_days, max_days]` window. The deployed config is (config.rs tests +
  live `~/.config/bob/config.yml` agree):
  - P1 `high` → 2–7 days; P2 `medium` → 8–30; P3 `low` → 31–90; P4 `lowest` → 91–365.
- `PriorityLevel::roll_offset(seed)` rolls inclusively within the window using a
  splitmix64 finalizer (`mix64`); `roll_seed()` honors `BOB_PRIORITY_ROLL_SEED` or falls
  back to `nanos ^ mix64(pid)`.
- `bob capture` (`src/native/capture.rs`: `resolve_priority`, `item_roll_seed`,
  `scheduled_date_string`) already implements "pick `p:<N>`, roll a random
  `[scheduled:: today+offset]`" with **per-item seed derivation**
  (`item_roll_seed(base, index)`) so multi-task captures don't all land on the same date.
  `randomize` should reuse `roll_offset` and a per-task seed derivation, not invent a new RNG.

Key consequence for the request's wording: the config range is keyed off the note's
**`priority` *value*** (`high`/`medium`/`low`/`lowest`), not the `P<N>` label, and a task
with **no priority field is implicitly P0** ("do it now, no roll" per the config
comment). The request's "priority property" therefore means "has a recognized
`[priority:: …]` field" — i.e. P1–P4 — and P0 tasks (no priority) are out of scope by
construction. The report's §3 proposes making this explicit in `--help`.

### 1.2 Task-line field syntax and status semantics are subtle — copy the strict parsers

Three modules encode edge cases `randomize` must not regress:

- **Field forms:** `task_status_hooks.rs` (`parse_task_date`, metadata scan) and
  `capture_task_toggle.rs` (`scheduled_field_matches`) accept **both**
  `[scheduled:: DATE]` and `(scheduled:: DATE)` anywhere on the task line, and treat
  zero / duplicate / malformed fields as *not a usable date*. `randomize` must only touch
  lines with **exactly one syntactically valid** scheduled field.
- **Project frontmatter is not task metadata:** `task_status_hooks.rs` explicitly ignores
  project `scheduled:` frontmatter; `projects.rs` manages `^prj` + frontmatter scheduling
  separately. `randomize` must only rewrite **task-level inline** scheduled fields, never
  project frontmatter.
- **Blocked/future semantics:** `task_status_hooks.rs` marks tasks with task-level
  scheduled **later than the daily anchor** as Blocked `[?]`; a schedule on/before the
  anchor is "not future". The daily anchor comes from the current daily ledger filename
  (`daily_anchor_date`), falling back to `BOB_NOW` / `Local::now` (`env::current_datetime`,
  `src/native/env.rs`). `randomize` should anchor "due" (≤ today) the same way: prefer the
  daily anchor when available, else `BOB_NOW`-overridable today. In practice both are the
  calendar date; tests should pin `BOB_NOW`.
- **Value vocabulary matters:** the config comment warns that Obsidian Tasks parsers read
  trailing inline fields right-to-left and stop at the first unrecognized one, so priority
  `value` must stay in `{highest, high, medium, low, lowest}`. `randomize` must match the
  note's priority value against configured level values and **skip unknown values** rather
  than guessing a window.

### 1.3 Two established "batch mutate the vault" patterns — pick the right half of each

| Concern | `move-done-tasks` (`collect_done.rs`) | `task-status-hooks` (+ `…_write.rs`) | What `randomize` should take |
|---|---|---|---|
| Scan → plan → apply | Plan struct, per-file contents, then write | Snapshot read-set, stage to tempfiles, guarded replace | Plan-first (dry-run preview, single commit set) |
| Locking | No lock in `run_collection` itself (relies on `nightly` holding it) | `ob::try_acquire_lock` + retry w/ backoff, quiet-period + recovery copies | Acquire the shared `ob` lock like `vault-sync`/`nightly` do |
| Git | Path-scoped `git add -- <touched>` → `git commit -m "bob move-done-tasks YYYY-MM-DD"` → `git push` | No commit at all (leaves changes for `vault-sync`) | Path-scoped single commit, **no push** (see §4) |
| Output | Human sectioned stdout | `--dry-run`, `--format human|json`, `--bob-dir`, `--retry-timeout` | Same flags (minus retry-timeout unless guarded writes are reused) |

### 1.4 How `vault-sync` actually works (why the "single commit" ask is safe)

`src/native/vault_sync.rs` (`run_cycle_inner`):

1. Verifies the worktree, recovers interrupted merge/rebase/cherry-pick.
2. `git status --porcelain`, size-preflights, then **`git add -A .`** (sweeps everything).
3. Commits staged changes with a generated message (or `--message` override), then
   fetch → reconcile `origin/master` (fast-forward or merge, with conflict-copy
   resolution) → push with up-to-3 retries on non-fast-forward.
4. `nightly.rs` runs `vault-sync` → `move-done-tasks` → `vault-sync`, all under one
   shared `ob` lock (`ob.rs`: `try_lock_exclusive` on `${XDG_RUNTIME_DIR:-/tmp}/bob_sync.lock`).

Implications: a prior path-scoped commit from `randomize` is just ancestry by the time
`vault-sync` runs — `git add -A` finds only remaining dirt, the merge path handles
remote drift, and there is no "commit conflict" concept in Git. The only real hazards
are (a) running concurrently with `vault-sync`/`nightly` (solved by the shared lock),
(b) sweeping unrelated dirty files into the randomize commit (solved by path-scoped
`git add --`, never `-A`), and (c) pushing from both commands (solved by letting only
`vault-sync` push).

---

## 2. Critique: is this a good idea?

**Yes, with guardrails.** The underlying pain is real: after days/weeks without triage,
dozens of stale P1–P4 tasks sit *due* (scheduled ≤ today), burying the P0 "do it now"
set. Bulk-deferring the tail so today reflects reality is a legitimate triage operation,
and keying the deferral window off the already-configured per-priority ranges is the
right default — it preserves the user's stated intent that P1s resurface in days while
P4s disappear for months.

Weaknesses of the plan as stated, and how to fix each:

1. **"Random date" is under-specified and naïve uniform-per-task has a pile-up problem.**
   Independent uniform draws over e.g. 2–7 days *will* stack several tasks on the same
   day. That matches capture's existing behavior, so it's acceptable and explainable,
   but don't oversell "spread". If even spreading is later wanted, it needs a
   capacity-aware scheduler (bin-packing by day), which is a different feature. Keep
   independent rolls for v1; document the pile-up property. (§3 adjustment A)
2. **Destructive rewrite destroys the overdue signal.** Today, "scheduled 3 weeks ago"
   tells you something ("I have ignored this for 3 weeks"). After a bulk roll, every
   task looks freshly scheduled. Mitigations: (a) append a `SCHEDULE LOG` child bullet
   recording the old date + reason (the codebase already has `capture_schedule_log.rs`
   and `capture_task_toggle.rs` patterns for this); (b) `--dry-run` preview; (c) the
   single commit message + `git log` as an audit trail. Recommend (a)+(b) with the log
   line opt-out-able. (§3 adjustment B)
3. **"All due + prioritized" will surprise on scope.** Vault-wide rewrites hit daily
   notes, area/project notes, and Tasks sections that `task-status-hooks` grouping owns.
   Blindly rewriting scheduled dates inside generated-group regions, done/cancelled
   tasks, `^prj` lines, or tasks with `dependsOn`/pomodoro links could fight other
   automation. Scope v1 to **open, non-`^prj`, parsable single-scheduled + recognized
   priority** tasks and skip everything else loudly (counts in output). (§3 adjustment C)
4. **Single commit is right; "commit" vs "push" needs a decision.** The request says
   "commit … using a single commit" and "doesn't conflict with vault-sync". The correct
   split is: `randomize` commits (path-scoped, one commit), `vault-sync` pushes. Having
   `randomize` also push duplicates `collect_done`'s behavior but races `vault-sync`'s
   fetch/merge/retry loop and doubles failure modes. Recommend commit-without-push as the
   default, with no `--push` flag in v1. (§4)
5. **Scheduling future-dated tasks would be a bug, not a feature.** Rolling a task that is
   already future-dated forward again is never what "catch up after neglect" means, and
   re-rolling tasks due *today* is the stated goal, so the predicate must be
   `scheduled ≤ today`, strictly. Malformed/multiple/unknown-priority cases skip.

### Alternatives considered (and why not)

- **Do it as `bob query` + manual edits / Dataview script:** read-only and familiar, but
  no guarded writes, no lock, no single commit, no tests. Wrong layer.
- **Fold into `nightly`:** tempting (it already brackets maintenance with vault-sync),
  but the user wants an *on-demand* triage lever, and automatic bulk rescheduling would
  silently destroy due-date signals every night. Keep it explicit and manual.
- **Even-spread scheduler / priority-queue fill:** better calendar hygiene, but needs
  per-day capacity policy the user hasn't expressed; defer to a later `--spread` option.
- **Shell-script command:** the repo's direction is native Rust (runner table +
  `NativeCommand`); shell loses config parsing, date math, lock plumbing, and testability.

---

## 3. Adjusted requirements (proposed contract for `bob randomize`)

Keep the request's intent; tighten these clauses (each is a deliberate adjustment,
flagged as such):

- **(A) Eligibility predicate (adjusted: narrower than "has scheduled + priority").**
  A task is eligible iff ALL hold:
  1. It is a Markdown checkbox task line counted by the Tasks globalFilter (`- [ ]`,
     `- [?]`, `- [*]`, etc. — open statuses only; never `[x]`/`[X]` done, `[-]` cancelled,
     or non-task bullets).
  2. It carries **exactly one** syntactically valid task-level inline `scheduled` field
     (`[scheduled:: YYYY-MM-DD]` or `(scheduled:: …)`), calendar-valid, with date **≤
     today** (daily anchor; `BOB_NOW`-overridable).
  3. It carries a `[priority:: <value>]` whose value matches a configured level's `value`
     (covers `high`/`medium`/`low`/`lowest`; also `highest` if a level ever uses it).
     Unknown values, missing priority (P0), multiple priority fields → skip with counts.
  4. It is not a `^prj` project-marker line and `randomize` never touches project
     frontmatter `scheduled:`.
  5. File is not in always-excluded dirs (`.git`, `.obsidian`, `_conflicts`,
     `_generated`, `_templates`) or done archives; daily notes ARE included (that is
     where stale due tasks live) but generated group headings created by
     `task-status-hooks` are left structurally alone (only the field value changes).
- **(B) Date computation (adjusted: anchor + per-task seed made explicit).**
  `new_date = today + roll_offset(level, seed_task)` where `roll_offset` is the existing
  inclusive `PriorityLevel::roll_offset`, and `seed_task` derives per task
  (e.g. `mix64(base_seed ^ stable_task_hash)` over file-relative-path + line digest,
  in the spirit of capture's `item_roll_seed`) so reruns with the same seed are stable
  yet tasks don't collide. Base seed: `BOB_PRIORITY_ROLL_SEED` if set else `roll_seed()`.
  Add `--seed <u64>` to force determinism (implies `BOB_PRIORITY_ROLL_SEED`).
- **(C) Write shape (adjusted: minimal in-place edit + audit log).**
  Replace only the scheduled field's date token, preserving `[]`-vs-`()` style and
  surrounding whitespace. Do not reorder fields, do not touch priority/created/id/block-id.
  Append (or extend) a `SCHEDULE LOG`-style child entry noting
  `old-date → new-date (bob randomize YYYY-MM-DD)` unless `--no-log` is passed. If the
  codebase's canonical schedule-log format (see `capture_schedule_log.rs`) can be reused,
  reuse it verbatim.
- **(D) Commit discipline (adjusted: commit yes, push no).**
  After applying all file writes: `git add -- <touched paths>`, commit **once** with
  `bob randomize YYYY-MM-DD (<n> tasks)` (allow `--message` override mirroring
  `vault-sync run -m`), then stop. No push, no fetch, no merge. If nothing changed, print
  "no eligible tasks; nothing to commit" and exit 0 without touching Git. If the vault is
  not a Git worktree or Git is missing, still write files and warn (mirroring
  `collect_done`'s `GitState::Skipped`).
- **(E) Concurrency (adjusted: explicit lock requirement).**
  Acquire the shared `ob` maintenance lock for the whole scan→write→commit window so a
  concurrent `vault-sync` / `nightly` / `task-status-hooks` run cannot interleave. Fail
  fast (exit 0 with "another run is active" like `vault-sync run`, or nonzero — match
  `vault-sync`'s convention) when contended; no retry loop in v1.
- **(F) Observability (adjusted: dry-run + machine output are required, not optional).**
  `--dry-run` (no writes, no commit), `--format human|json`, `--bob-dir`, `-h/--help`,
  honoring `BOB_DIR`, `BOB_NOW`, `BOB_CONFIG_FILE`, `BOB_PRIORITY_ROLL_SEED`, `NO_COLOR`.
  Human output lists per-file `old → new` lines plus skip-count breakdown
  (future / no-priority / unknown-priority / malformed-or-duplicate / done-or-cancelled /
  excluded-path); JSON emits the same machine-readably. Exit codes: `0` success/no-op,
  `1` runtime failure, `2` CLI usage error (repo convention).

Out of scope for v1 (say so in `--help`/docs): even-spread scheduling, P0 handling,
house-wide `--only-priority P2,P3` filtering (cheap to add later; skip to keep the
surface minimal — though see §5 option), touching `dependsOn`/pomodoro-linked tasks
differently (currently: treated like any eligible task), and any `nightly` integration.

---

## 4. Vault-sync interaction: why one path-scoped commit + no push cannot conflict

- **No concurrent-mutation hazard:** the shared `ob` lock serializes `randomize` against
  `vault-sync` and `nightly`. `randomize` must take it (unlike `collect_done`, which
  leans on `nightly`'s lock when run wrapped but is itself racy standalone — do not copy
  that weakness).
- **No over-commit hazard:** `git add -- <touched>` stages exactly the files `randomize`
  rewrote. `vault-sync`'s later `git add -A` only sees *other* dirt plus the already
  committed randomize commit — Git commits are snapshots, so two sequential commits never
  "conflict"; worst case a later `vault-sync` merge resolves remote drift with its
  existing conflict-copy machinery.
- **No push race:** exactly one writer pushes (`vault-sync`). `randomize` never fetches,
  merges, or pushes, so it cannot hit non-fast-forward retries or leave
  `MERGE_HEAD`/rebase state behind. Recommended doc line: *"Run `bob vault-sync` (or
  `bob nightly`) after `bob randomize` to publish."*
- **Auditability:** one commit with a stable message (`bob randomize YYYY-MM-DD (N
  tasks)`) makes revert (`git revert`) and review (`git show --stat`) trivial — strictly
  better than per-file commits.

---

## 5. Recommended implementation sketch

1. **CLI plumbing** (follow `sase/memory/cli_rules.md` before adding the subcommand):
   register `randomize` in `src/runner.rs` `SUBCOMMANDS` (alphabetical) +
   `src/native.rs` `NativeCommand::Randomize` + dispatch, mirroring `move-done-tasks`.
2. **New module** `src/native/randomize.rs`: arg parsing (`--dry-run`, `--format`,
   `--bob-dir`, `--seed`, `--message`, `--no-log`), vault scan reusing
   `task_status_hooks`/`markdown` line-walk helpers (not project-sync paths), config load
   via `config::load_priority_property`, date math via `chrono`, seed via
   `config::roll_seed` + per-task derivation, in-place field rewrite, schedule-log append.
3. **Apply + commit:** hold `ob` lock → write files → `touched_git_paths`-style set →
   `git add --` → `git diff --cached --quiet` gate → single `git commit -m …` (borrow
   `collect_done.rs: prepare_git/finish_git/commit_git_paths` shape, minus push).
4. **Tests:** unit (predicate matrix: future/due/malformed/duplicate/unknown-priority/P0/
   `^prj`/frontmatter untouched; roll bounds per level; seed determinism), fixture-vault
   integration (`BOB_DIR` tempdir + `BOB_NOW` pin: due P2 moves into 8–30d window, future
   untouched, single commit, dry-run clean), and a lock-contention test. Update `README`
   command list + `just install-smoke` help probe.
5. **Docs/UX:** `--help` states the predicate, the pile-up property, the commit-no-push
   contract, and the "run vault-sync to publish" next step.

Estimated shape: ~400–700 lines Rust + tests; no config-format change; no new
dependencies (`chrono`/`regex` already present).

---

## 6. Risks & open questions for the lead

- Per-day pile-ups (see §2.1) — acceptable for v1?
- `SCHEDULE LOG` append default-on vs opt-in — default-on recommended for auditability.
- Whether a later `--only-priority` / `--spread` / `--push` flag set is desired — recommend
  against all three in v1 to keep the contract tight.
- Daily-anchor vs `Local::now` "today": recommend anchor-with-fallback (§3B) for
  consistency with Blocked-status semantics; confirm with a vault fixture test.

*Independent assessment by mus; no peer reports consulted.*
