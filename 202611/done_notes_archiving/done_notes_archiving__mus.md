# Done notes in bob-cli: how `done/<name>_done.md` works today, how other systems do it, and what to change

Research report — vault archiving (`bob task archive` / nightly collection).
Code read at workspace HEAD; no peer reports consulted.

## TL;DR

Keep the per-source `done/<path>/<stem>_done.md` mirror. It is the right
shape for an Obsidian vault with path-qualified links and dependency ids.
Do not switch to a single global `done.txt`, same-note `## Archive`
sections, or deletion.

Fix reliability and intuitiveness around it:

1. Add a time gate (grace period) alongside the count threshold, and stop
   writing frontmatter-only commits.
2. Handle renames/orphans, cap archive growth, and give the command the
   same safety UX as `merge`/`move` (`--dry-run`, scoping, lock/sync parity).
3. Align the "what counts as done" predicate with the rest of the vault,
   guarantee linkable identities, and exclude `done/` from default views.

Details and rationale below. All paths are repo-relative unless noted.

## 1. What bob does today (observed, with sources)

### 1.1 Command and schedule

- Command: `bob task archive`, implemented in
  `src/native/collect_done/mod.rs` (`COMMAND_NAME = "bob task archive"`,
  `DEFAULT_THRESHOLD = 10`, `run_collection()`).
- Help (`help_text()` / `docs/reference/cli/task.md`): "Move done and
  canceled Bob task blocks into archive notes, link sources, repair archive
  metadata, and repair Obsidian links to moved block ids."
- Only option is `-t/--threshold N`: "minimum completed/canceled task
  count per source note". No `--dry-run`, `--note`, `--since`,
  `--offline`, or lock/retry flags — unlike `merge`/`move`, which have
  `--dry-run`, locks, guarded writes, scoped commits, and vault sync.
- Nightly runs it with the default threshold:
  `src/native/nightly.rs` → `run_collect_done_step()` calls
  `collect_done::run_collection(DEFAULT_THRESHOLD, ...)`, between
  `vault-sync` runs. Standalone `run()` wraps the planner directly with
  no pre/post sync.

### 1.2 Archive layout: one mirror file per source

- `transform.rs::archive_relative_path()`: stem + `"_done.md"` under
  `done/`, preserving the source subdirectory:
  `work.md → done/work_done.md`,
  `projects/foo.md → done/projects/foo_done.md`,
  `2026/20261020.md → done/2026/20261020_done.md`.
- Reverse map: `link_repair.rs::source_relative_path_from_archive()`
  strips the leading `done/` component and the trailing `_done` stem
  suffix. `archive_parent_matches_source()` gates history repair on the
  archive's `parent:` frontmatter resolving (via `NoteIndex`) to that
  source.
- `docs/reference/vault-format.md` directory tree lists `done/` as
  "bob task archive", required "Created by archive", override "none".

### 1.3 Linkage frontmatter

- Source side: `archive.rs::ensure_source_done_tasks_frontmatter()` writes
  `done_tasks: "[[done/...]]"` (constant `DONE_TASKS_KEY`). Created even
  when the note has no frontmatter.
- Archive side: `archive_frontmatter()` / `ensure_archive_frontmatter()`
  write `parent: "[[source]]"` (function
  `archive_parent_frontmatter_line()`) plus `ARCHIVE_TYPE_LINE =
  "type: \"[[done]]\""`, preserving existing frontmatter keys.
- Consumers: `ref_tasks/insert.rs` prefers the note's own `done_tasks`
  link when allocating ref-task archives; `ref_library/migrate_tasks/plan.rs::archive_rel_for()`
  parses a `done_tasks:` line for the destination archive, falling back to
  `done/{stem}_done.md` only for single-component destinations
  (returns `None` for nested dests without an explicit link).

### 1.4 What gets moved

- `transform.rs::transform_markdown()` scans each source line; only
  `collectible_task_line()` matches move: list marker + `[x] | [X] | [-]`
  + `#task` tag (checked by `has_task_tag()`). The whole block goes:
  `task_block_end()` takes the task line plus all deeper-indented
  following lines (blank-line handling included), appended verbatim to
  `archive_append`; the source keeps everything else.
- `plan.rs::build_collection_plan()`: `moves_tasks = task_count >=
  threshold`. If false, no blocks move. But if the archive file already
  exists, the planner still rewrites source `done_tasks` and archive
  `parent`/`type` metadata (`moves_tasks || archive_exists`), and emits a
  `FilePlan` when either metadata flag is set — i.e. frontmatter-only
  plans commit with zero moved tasks.
- `markdown_files()` uses `collect_markdown_files(..., include_done =
  false)`, and `should_skip_directory()` skips any `done` component plus
  `is_always_excluded_note_directory_name()`. So collection never sources
  from `done/`. Link repair uses the sibling walker with `include_done =
  true` (`link_repair_markdown_files()`).

### 1.5 Identity preservation and link repair

- Trailing `^block-id` anchors are the identity mechanism
  (`trailing_block_id_in_line()`, `block_id_occurrences_in_text()` —
  caret must be whitespace-separated, `[A-Za-z0-9-]` only).
- `archive.rs::deduplicate_archive_append_block_ids()` renames collisions
  against the existing archive to `{id}-{N}` via `next_available_block_id()`,
  tracking `moved_block_id_final_ids`, `moved_block_final_ids`,
  `ambiguous_moved_block_ids` (same id twice in one run is ambiguous and
  skipped for repair).
- `link_repair.rs::apply_link_repairs_to_plan()` + `moved_block_targets()`
  (`archived_block_targets()` for history + `overlay_current_run_block_targets()`
  for this run) rewrite Obsidian links and `[id::]/[dependsOn::]` dependency
  metadata (`DEPENDENCY_FIELD_RE`, `repair_links_in_note_with()`,
  `repair_dependency_metadata()`), including the
  `archive_stayed_block_ids()` pathless-link pass. Reporting counts link
  repairs and dependency-metadata repairs separately.
- Dependency ids embed the note path:
  `task_dependencies::dependency_id()` / `vault_relative_link_target_with_kind(path,
  "archive"|"source")`. Archive targets always keep the explicit
  vault-relative path (`format.rs`: "Basename links do not search `done/`,
  so archive targets always ..."), because `done/` is excluded from
  basename resolution.

### 1.6 Who treats `done/` as history

- `stats/index.rs`: `excluded_directory()` skips only dot-dirs and
  `_conflicts | _generated | _templates` — `done/` is deliberately
  included (test
  `excluded_directories_are_skipped_and_done_is_included` asserts
  `done/tasks_done.md` is indexed). Stats therefore sees archive rows;
  `source_relative_path_from_archive()` is used to attribute archive
  children back to sources (index.rs ~504, ~571).
- `projects/surface.rs::is_done_path()`: any `done` component at any depth
  is an archived path (mirrors sync exclusion).
- `task_complete/keep_moving.rs::in_done_archive()` and
  `task_complete/successors.rs::in_done_archive()`: leaf-project checks
  and successor candidates exclude `done/`.
- `task_status_hooks/parse.rs` skips `done` notes; `reconcile.rs` loads
  `done/` targets on demand as "closed history" and keeps explicit
  `done/` paths in archive links.
- `pomodoro_homes` tests show `done/sase_blog_done.md` resolving with
  `type: [[done]]` + `parent: [[sase_blog]]` frontmatter; homes treat
  `done/` as non-home.
- `vault_clobber.rs` excludes `done/sase_done.md` from clobber scans.

## 2. Failure modes and papercuts in the current design

Ranked by user-visible pain, each grounded in the code above.

### 2.1 Count threshold without a time gate leaves the vault half-archived

`threshold = 10` per source note per run means a note with 9 done tasks
never archives, while a note with 10 archives all of them at once —
including tasks finished minutes ago. There is no "age" or "completed
date" input to `build_collection_plan()` at all. Consequences:

- Small area/project notes accumulate done rows forever; large notes get
  bulk yanked, including yesterday's context Bryan may still want in
  place.
- Mixed state is the norm: some notes clean, some cluttered, with no
  per-note control. Users cannot express "archive my daily notes
  aggressively but leave `work.md` alone" except by running manual
  `--threshold` values vault-wide.
- The help text ("minimum completed/canceled task count per source note")
  does not say per-run vs cumulative, nor that the whole block set moves
  once crossed.

### 2.2 Frontmatter-only plans cause commit churn

`plan.rs` lines ~284–351: when `task_count == 0` but the archive exists,
source/archive metadata is still normalized and a `FilePlan` is emitted
if either `*_metadata_updated` flag flips. Combined with nightly
auto-commit (`git.rs`: stage `git add -- touched_paths`, commit
`"bob task archive YYYY-MM-DD"`, `git push`), a quote-style drift or a
manually edited `parent:` line produces a nightly commit that moves zero
tasks. `mod.rs` even reports "source done_tasks updates" and "archive
metadata repairs" as first-class counts. Bryan pays a commit + push +
Obsidian sync cycle for cosmetic normalization.

### 2.3 Rename / move of a source orphans its archive silently

The source↔archive binding is purely conventional (path + `_done` suffix
+ `parent:` string). If Bryan renames `projects/foo.md`:

- `source_relative_path_from_archive()` still points at the old path;
  `archive_parent_matches_source()` fails (target no longer resolves or
  resolves elsewhere), so `archived_block_targets()` skips that archive
  entirely — past moves lose repair coverage with no per-archive warning,
  only aggregate counts.
- The next collection creates a *new* `done/projects/renamed_done.md`
  while the old archive sits orphaned. Nothing re-homes (`parent:` is
  rewritten only for archives in the current plan's file set), merges, or
  tombstones the orphan.
- Same hazard for case-only renames and directory moves, which are common
  during project reshuffles. `dependency_id()` includes the path, so every
  moved block's dependency identity changes too.

### 2.4 One unbounded file per source

`archive_contents()` is pure append (`append_archive_blocks()`); there is
no rotation, date sharding, size cap, or compaction. `work_done.md` grows
forever; search, Dataview, and the Tasks plugin all pay for it on every
query (stats explicitly indexes `done/`). Conversely daily notes each get
their own tiny archive (`done/2026/20261020_done.md`), so the tree fills
with hundreds of 1–3-task files. Neither extreme is browsable.

### 2.5 The "done" predicate disagrees with the rest of the system

- Archiver moves only `[x]/[X]/[-]` + `#task`.
- `task_status_hooks` and stats understand configurable `done_statuses`
  and custom DONE kinds (cf. stats test
  `task_parser_honors_custom_done_non_task_fences_and_date_diagnostics`,
  hooks `done_and_canceled` counts). A task the hooks consider done but
  the archiver does not (e.g. a custom cancel glyph without `[-]`, or a
  done row that lost its `#task` tag in editing) stays in the source
  forever; conversely `[-]` cancels archive even when hooks treat the row
  differently.
- Plain `- [x]` without `#task` never moves — probably correct, but it
  surprises users who check a box in Obsidian and expect nightly cleanup.

### 2.6 Identity gaps: id-less tasks and ambiguous ids

- Tasks without trailing `^id` move fine but leave no repair target
  (`moved_block_ids` only covers anchored blocks). Later `move`/`merge`,
  dependency links, and `task_complete` offers cannot address them.
- Duplicate ids in one run become `ambiguous_moved_block_ids` and are
  removed from repair targets (`overlay_current_run_block_targets()`).
  Safe, but the source note keeps no marker that its links were left
  dangling — the user learns only from aggregate stdout counts.

### 2.7 No preview, no scope, no lock

`merge`/`move` have `--dry-run`, typed locators, `--offline`,
retry/lock budgets, and print the same plan they would execute. Archive
has none: it scans the whole vault, writes, commits, and pushes. There is
no way to ask "what would you move?", "just this note", or "don't push".
`atomic_write()` (temp-file + rename) is solid per file, but there is no
maintenance-lock coordination with concurrent Obsidian/plugin writes
across the multi-file plan — a partial external edit between scan and
`apply_file_plan()` is silently overwritten (last-writer-wins per file).

### 2.8 `done/` competes in search, graph, and metrics by default

Because stats indexes `done/` and the files are ordinary Markdown under
the vault root, Dataview/Tasks queries, backlinks, graph view, and
`bob query` all see history unless each query filters it out. The
`type: [[done]]` marker exists but nothing in the observed docs tells
users the canonical `WHERE type != [[done]]` / `path !startswith done/`
exclusion, and `bob query`'s default paths include archives. Double
counting completed work in period stats is one missed filter away.

### 2.9 Minor: nested-ref archive fallback, line-ending/frontmatter churn

- `archive_rel_for()` (migrate_tasks) returns `None` for nested
  destinations without an explicit `done_tasks:` line — single-component
  roots get `done/{stem}_done.md`, nested notes get no archive. Inconsistent
  with the archiver, which mirrors subdirectories.
- `preferred_line_ending()`, quote style (`"[[...]]"` vs `[[...]]`),
  and `parent:` vs `done_tasks:` key placement rewrites can flip a whole
  frontmatter block for one key change. Harmless but noisy in diffs.

## 3. How other systems handle "done"

| System | Where done lives | Mechanism | Lesson for bob |
|---|---|---|---|
| `todo.sh` / Todo.txt | Single global `done.txt`; `archive` moves all `x …` lines | One append-only log, chronological, grep-friendly; `do` optionally auto-archives | Simple + predictable; loses per-note context and path-qualified identity — wrong for an Obsidian vault |
| Taskwarrior | `pending.data` vs `completed.data` (immutable history DB) | Completed never edited; reports filter by status; retention/undo via IDs | Treat history as immutable; never rewrite archive rows except repair — bob already close |
| Obsidian Task Archive plugin | Same-note `## Archive` section *or* separate note; moves task + sub-items; finished sub-task of open task moves alone (toggle) | Keeps context local; per-note opt-in; no threshold | Same-note section avoids file explosion for small notes; bad for bob's vault-wide link repair + stats |
| Obsidian Archiver / Packrat | Separate archive file, optional replace-before-archive, `%%done_log%%` append | Explicit user gesture, previewable | Gestures beat nightly surprises; preview matters |
| Obsidian Tasks `on completion` | Per-task actions on check (add date, move — "separate completed archive" is a requested action) | At-close-time handling keeps "just finished" visible until *you* move it | Time/age gate > count gate |
| GTD Board plugin / Starter-Kit rules | Auto-move to archive folder N days after Done (configurable, default off); "7 days after Done" grace | Grace period keeps recent wins visible, then files them | Direct model for bob's missing time gate |
| Todoist / Things / Reminders | Done stays in place, hidden by filter, `completedAt` timestamp; Completed smart list / Activity log | No move at all; views, not files | For small vaults, filtering beats moving; bob moves because notes would bloat — keep move, add filter parity |
| Notion | Same database, `Done` view / filtered archive view | View, not move | Same lesson: make excluding `done/` a one-liner everywhere |
| Logseq | `DONE` stays in journal/page; queries add `not done` | In-place + query filter | Same |

Key takeaway: file-per-source archiving (bob) is the outlier, but it is
the right outlier for Obsidian — same-note sections break vault-wide
`[[note#^id]]` repair and per-note `parent:` attribution, and a single
global log breaks `dependency_id()` path qualification and per-project
browsing. What bob should borrow is not the *location* but the
*policy*: grace periods, previews, per-note opt-out, and filter-first
presentation.

## 4. Recommended changes

Ordered by value/effort. Each is scoped so it can ship alone.

### R1. Add a grace period; keep the threshold as a size backstop

- Add `--older-than <duration>` (e.g. `7d`) and/or `--grace-days N` to
  `bob task archive`; nightly configures a default (suggest 7 days).
  Only blocks whose close/cancel date is older than the cutoff move;
  threshold remains as "but never leave more than N done blocks in a
  source".
- Requires reading completion dates (`[completion:: …]` / ledger close
  dates where available); tasks with no parseable close date use the
  current behavior (move when threshold crossed) and are counted
  separately in stdout so the bias is visible.
- Why Bryan will feel it: recently finished work stays where he left it
  for the weekly review, then files itself. This is the single biggest
  intuitiveness win and matches the GTD-Board/Starter-Kit convention he
  already lives near.

### R2. Stop committing when nothing moved

- Split "repair/normalize frontmatter" from "move tasks". Default:
  only write + commit files with `task_count > 0` or link-repair counts;
  put pure `done_tasks`/`parent`/`type` normalization behind
  `--repair-metadata` (nightly can run it weekly, not daily).
- Alternatively fold metadata repair into the existing link-repair pass
  so one commit covers both, and skip the commit when the tree is clean
  (already partially done via `git_has_staged_changes()` — extend the
  "no vault changes" early exit to cover metadata-only plans unless the
  flag is passed).
- Kills the nightly cosmetic commit + push + Obsidian reindex.

### R3. Give archive the `merge`/`move` safety UX

- `--dry-run` (print the same `moves:` plan without writing/committing),
  `--note <path>` / `--only <glob>` scoping, and `--offline` (commit
  without push). Reuse the maintenance lock + vault-sync bracketing that
  `merge`/`move` already use.
- Rationale: archive is the only vault-rewriting `bob task` command
  without a preview. Bryan should be able to answer "what would nightly
  do?" before it pushes.

### R4. Survive renames: re-home orphans explicitly

- On each run, detect archives whose `parent:` no longer resolves to an
  existing source (or resolves elsewhere): report them as
  `orphaned archives: N` with paths, and add `--rehome` (update `parent:`
  to the rename target when unambiguous, e.g. via git similarity or an
  explicit `--from/--to`) plus docs for the manual case. Never silently
  create a second archive alongside an orphan.
- Smaller companion fix: make `archive_rel_for()` (migrate_tasks) mirror
  subdirectories like the archiver does, instead of `None` for nested
  dests — or document that nested ref-task dests require an explicit
  `done_tasks:` line.

### R5. Cap archive growth (rotate, don't accumulate)

- Pick one: (a) yearly sharding per heavy source
  (`done/work_2026_done.md`, or `done/work/2026_done.md`), keeping
  `done_tasks:` as a list/link to the current shard; or (b) a size cap
  with `…_2_done.md` overflow. Daily-note archives (`done/2026/*_done.md`)
  should consolidate monthly or roll into the existing period tree
  instead of one file per day.
- Keep `parent:` + `type: [[done]]` on every shard so existing
  `source_relative_path_from_archive()` + `archive_parent_matches_source()`
  logic keeps working (extend the stem parser to strip date/sequence
  suffixes).
- Motivation: bounded file sizes for search/Dataview/Tasks, browsable
  history ("what did I finish in Q3?") for free.

### R6. Align "counts as done" with hooks/stats and guarantee identities

- Derive `collectible_task_line()`'s close-glyph set from the same
  `done_statuses` config the hooks use, instead of hardcoded
  `[x]/[X]/[-]`; document the `#task`-required rule in the command help
  (it is currently invisible).
- On move, assign a fresh `^id` to done blocks that lack one (respecting
  `next_available_block_id()` uniqueness) so every archived block stays
  addressable for later `move`/`merge`/dependency repair. Alternatively
  leave id-less blocks in place and count them as `unmoved: no block id`
  — either is better than today's silent unlinkable move.
- Surface `ambiguous_moved_block_ids` per file in stdout (not just a
  total), so Bryan knows which note needs manual dedup.

### R7. Make `done/` disappear from default views

- Publish the canonical exclusion once, in `vault-format.md` +
  `bob query`/`dataview.md` + Tasks-plugin docs: filter `type != [[done]]`
  / path not under `done/`. Add a `bob query` convenience (e.g. exclude
  archives by default with `--include-archives` opt-in) and confirm
  period/stats rollups attribute archive rows to sources without
  double-counting.
- Consider Obsidian-side affordances already in the tree: keep `done/`
  out of graph/backlink-heavy flows via the existing `type: [[done]]`
  marker rather than moving the directory — moving it (e.g. `.archive/`)
  would break every stored `[[done/…]]` link and the `is_done_path()`
  convention across `projects`, `successors`, `keep_moving`, and hooks.

### R8. Small UX/docs wins (cheap, do anytime)

- Per-note opt-out: honor `archive: off` (or `done_tasks: off`) in source
  frontmatter — daily scratch, dashboards, and inbox triage notes should
  never spawn archives.
- Document the contract: threshold semantics, `#task`-required,
  block-id dedup `-N` renaming, `done_tasks`↔`parent` pairing, and the
  "rename orphans" behavior, in `docs/reference/cli/task.md` (generated
  from `--help`, so fix `help_text()` first) and `vault-format.md`.
- Undo note: archive commits are ordinary git commits
  (`"bob task archive YYYY-MM-DD"`); document `git revert` / per-file
  restore as the undo path until/unless a `--undo` is built.

## 5. What I would NOT do

- **Single global `done.txt` / `done.md`.** Destroys per-note `parent:`
  attribution, path-qualified `dependency_id()`s, and per-project
  browsing; every stored `[[done/<stem>_done#^id]]` link breaks.
- **Same-note `## Archive` sections.** Keeps small notes tidy but bloats
  the exact notes archive exists to slim, and confuses lane/ready scans
  that must then filter sections instead of paths.
- **Auto-delete after N days.** Taskwarrior-style retention fits a DB,
  not a notes vault where the archive *is* the lab notebook. Rotate,
  don't delete.
- **Moving `done/` elsewhere (hidden dir, `.archive/`).** Breaks stored
  links, `is_done_path()` / `is_archive_path()` conventions, and the
  `done/` basename-exclusion rule in link formatting — cost without
  benefit once R7's filters exist.

## 6. Suggested sequencing

1. R1 (grace period) + R2 (no cosmetic commits) — biggest daily-feel win,
   small blast radius.
2. R3 (dry-run/scope/offline) + R8 opt-out flag — safety before broader
   rollout.
3. R4 (orphan re-homing) + R6 (predicate + ids) — correctness.
4. R5 (rotation) + R7 (default exclusions) — scale and presentation.

## Appendix: key code pointers

- Planner/executor: `src/native/collect_done/mod.rs`
  (`run_collection`, `COMMAND_NAME`, `DEFAULT_THRESHOLD`),
  `src/native/collect_done/plan.rs` (`build_collection_plan`,
  `FilePlan`, `CollectionPlan`),
  `src/native/collect_done/transform.rs` (`transform_markdown`,
  `collectible_task_line`, `task_block_end`, `archive_relative_path`,
  `has_task_tag`),
  `src/native/collect_done/archive.rs` (`ensure_source_done_tasks_frontmatter`,
  `ensure_archive_frontmatter`, `deduplicate_archive_append_block_ids`,
  `next_available_block_id`, `atomic_write`),
  `src/native/collect_done/link_repair.rs`
  (`apply_link_repairs_to_plan`, `moved_block_targets`,
  `source_relative_path_from_archive`, `archive_parent_target`),
  `src/native/collect_done/git.rs` (`prepare_git`, `finish_git`,
  `collect_done_commit_message`).
- Schedule: `src/native/nightly.rs` (`run_collect_done_step`).
- History-aware readers: `src/native/stats/index.rs`
  (`excluded_directory`, archive attribution via
  `source_relative_path_from_archive`),
  `src/native/projects/surface.rs` (`is_done_path`),
  `src/native/task_complete/{successors,keep_moving}.rs`
  (`in_done_archive`), `src/native/task_status_hooks/{parse,reconcile}.rs`.
- Archive-link producers/consumers: `src/native/ref_tasks/insert.rs`,
  `src/native/ref_library/migrate_tasks/plan.rs::archive_rel_for`.
- User docs: `docs/reference/cli/task.md` (`bob task archive`),
  `docs/reference/vault-format.md` (directory tree, `done/` row).
- Tests: `src/native/collect_done/tests/{unit,plan}.rs`
  (threshold parsing, dedup `-N` renaming, `done_tasks` frontmatter cases).

## Methods

Read the archiver end to end (`collect_done/*`, nightly wiring, all
`done/`-aware readers), sampled its unit/plan tests and the vault-format
/ CLI docs, and compared against Todo.txt (`todo.sh archive` →
`done.txt`), Taskwarrior (`pending.data`/`completed.data`), the Obsidian
Task Archive / Archiver / Tasks-on-completion / Packrat / GTD Board
patterns, and the filter-in-place models (Todoist, Things, Reminders,
Notion, Logseq).
