---
title: "Done notes: how Bob archives closed tasks, what is broken, and what to change"
researcher: cld
date: 2026-11-09
scope: bob task archive (src/native/collect_done), done/<path>/<stem>_done.md archives, every reader of done/, the live ~/bob vault, and a survey of archive designs in other task systems
---

# Done notes: how Bob archives closed tasks, what is broken, and what to change

## TL;DR

The `done/<path>/<stem>_done.md` layout is the right *shape*. It is the same
per-source sibling archive Org mode ships as its default (the Org manual's own
example is literally `#+ARCHIVE: %s_done::`). Bob's identity model is
`(note path, block id)`, every project reserves `^prj`, and about 20 readers
already depend on the source-to-archive pairing. A central log would break all
three. **Keep the per-source archive.**

The *policy and the plumbing* around it are where the problems are.

1. **Two hierarchy bugs that can silently lose or mislabel tasks.**
   - **Open subtasks get archived.** A closed root is moved together with every
     indented line under it, including open `#task` subtasks. Bob's own close
     gesture leaves open subtasks under a closed root on purpose (SV5), so this
     can really happen. Once archived, those subtasks drop out of every lane.
   - **Closed children are detached.** A closed child of an open parent is cut
     out and appended to the archive with its indentation intact. In the archive
     it then nests under whatever block was archived just before it.
2. **Renaming a source orphans its archive.** The archiver pairs notes by
   filename, but the real link is in frontmatter. The live vault already has
   one orphan: `done/2026/20260528_day_done.md`.
3. **Daily notes can be archived.** They are eligible sources, and only the
   count threshold protects them today. A day with 10 or more closed `#task`
   rows (Event Tasks count) would have its Events section moved to `done/`,
   and `bob gcal` would then tombstone those rows as "removed by you".
4. **The count threshold makes visibility depend on how busy a note is.**
   `bob.md` is flushed every night. Meanwhile 104 quieter notes hold 469 closed
   rows below the threshold, 289 of them closed more than 30 days ago. Every
   other system I surveyed uses age (or a manual or immediate trigger). None
   counts rows per file.
5. **Reliability gaps.** A standalone `bob task archive` takes no lock and has
   no stale-file check, rollback, dry-run or JSON output. Newer writers get all
   of these from the shared `vault_rewrite` transaction. In addition, the
   question "is this path inside `done/`?" is answered by about 26 separate
   predicates that follow at least four different rules.
6. **Nothing can be restored.** A task reopened inside `done/` disappears from
   every lane, and `bob task move` refuses `done/` notes.

**My recommendation, in order:**

1. Make block selection hierarchy-safe.
2. Limit archiving to area, project and inbox notes.
3. Pair source and archive through frontmatter, and keep the archive filename
   in step when the source is renamed.
4. Define one shared `is_done_archive` contract for Rust and the plugins.
5. Replace the count threshold with an age window (default: closed 7 or more
   days ago).
6. Move the command onto the `vault_rewrite` transaction and add
   `--dry-run` / `--format json`.
7. Optionally: group archive entries under month headings, add restore support,
   and add a source-side "archived" affordance.

Full list, sizes and acceptance vectors are in [§7](#7-recommended-changes).

---

## 1. How done notes work today

### 1.1 The mover (`bob task archive`, formerly `collect-done` / `move-done-tasks`)

| Aspect | Current behavior | Where |
| --- | --- | --- |
| Trigger | `bob nightly` on athena at 03:30. It runs vault-sync, then `task archive`, then articles, period notes and vault-sync, all while holding `bob_sync.lock` | `src/native/nightly.rs:37-39,176` |
| Selection | Every `[x]` / `[X]` / `[-]` list item carrying `#task`, **at any indent**, together with all deeper-indented lines (its "block") | `collect_done/transform.rs` `collectible_task_line`, `task_block_end` |
| Gate | A note is processed only if it holds ≥ `threshold` closed blocks (default **10**). Once it qualifies, **every** closed block moves, including ones closed today | `plan.rs` `moves_tasks = transform.task_count >= threshold`; `mod.rs` `DEFAULT_THRESHOLD = 10` |
| Sources | Every `.md` file except `done/` and the always-excluded names (`.bob`, `.git`, `.obsidian`, `_conflicts`, `_generated`, `_templates`). **Daily notes, period notes, `ref/` and `mail/` notes are all eligible.** Other dot-dirs (e.g. `.sase/`) are walked | `transform.rs` `should_skip_directory`; `src/native.rs:3-10` |
| Destination | `done/<source dir>/<stem>_done.md`, derived from the source **filename** | `transform.rs` `archive_relative_path` |
| Pairing metadata | The source gets `done_tasks: "[[done/…_done]]"`. The archive gets `parent: "[[source]]"` and `type: "[[done]]"` | `archive.rs` |
| Append | Blocks are appended to the end of the archive in source order, byte for byte (no dedent, no date heading, no context) | `archive.rs` `append_archive_blocks` |
| Block IDs | A colliding moved ID is renamed `^id-1`, `^id-2`, … | `archive.rs` `deduplicate_archive_append_block_ids` |
| Link repair | Every vault note (`done/` included) gets wiki, embed, Markdown and `[id::]`/`[dependsOn::]` links rewritten from `src#^id` to `done/src_done#^id`. Pathless `[[#^x]]` links inside moved blocks whose target stayed behind gain the source path. Repair is also **self-healing**: every run re-derives targets from all existing archives | `link_repair.rs` `archived_block_targets`, `overlay_current_run_block_targets` |
| Writes | Per file: write the archive, then the source, each with tmp+rename. No lock (when run standalone), no before-image or stale check, no rollback | `plan.rs` `apply_file_plan`; `archive.rs` `atomic_write` |
| Git | `git add -- paths`, `git commit -m "bob task archive YYYY-MM-DD" -- paths`, `git push` | `git.rs` |
| CLI | Only `-t/--threshold N`. No `--dry-run`, no JSON, no per-note scope | `mod.rs` |

### 1.2 The in-source staging area

`bob task reconcile` groups area and project `Tasks` sections into generated
`Next & In Progress`, `Blocked` and **`Done & Canceled`** headings, and adds a
badge row (`🟢 N done/canceled`) (`docs/task-status-hooks.md` §Status
Grouping). So a closed task first lands in the source note's `Done & Canceled`
group and later leaves it for `done/`. Today the timing of that second step is
set by the count threshold.

### 1.3 Readers of `done/`

`done/` is read-only history that a lot of code consults:

- stats (`stats/index.rs` maps archive rows back to the source by filename);
- period reviews ("either the original or the `done/` archive spelling
  resolves to one task identity", `docs/periods.md:388`);
- Pomodoro homes (walk the archive's `parent:`);
- task dependencies (a narrow exact-`done/…` read; such links "never block");
- relations (`done/` sources are read-only);
- capture "similar tasks" corpus;
- successors (exclude `done/`);
- ref-task locator;
- vault task-loss guard (includes `done/`);
- and several plugin models.

Most lane computations (reconcile, plan, Ready, Next, projects) **skip
`done/` entirely**.

---

## 2. What the live vault shows (2026-11-09, `~/bob`)

| Fact | Value |
| --- | --- |
| Archive notes | 31 (`done/*.md` plus `done/2026/20260528_day_done.md`) |
| Archived closed rows | 3,116 |
| Largest archives | `sase_done.md` 1,755 lines · `bob_done.md` 1,333 · `gtd_daily_done.md` 1,103 (the daily GTD checklist alone adds ~7 lines/day) |
| Archive commits | 109. Daily for busy notes: `bob.md` lost 47–123 lines on each of the 11-04/06/07/09 runs |
| Files touched per run | 16–37 across the five latest runs (19 on 11-09). Besides source and archive, each run rewrites Pomodoro Task Links in recent daily notes (`[[bob#^x]]` → `[[done/bob_done#^x]]`), period notes, and `ref/chat/*.md` embeds |
| Closed rows lingering below threshold | **469 rows in 104 non-daily source notes; 289 closed > 30 days ago** (oldest from June) |
| Terminal project notes at vault root | 55 (`^prj` closed), next to 45 open ones |
| Orphan archives | **1**: `done/2026/20260528_day_done.md`. Its source was renamed `2026/20260528_day.md` → `2026/20260528.md` on 2026-06-08. Both frontmatter links still agree, but the filename rule does not |
| `-N`-suffixed IDs in `done/` | 42, some from collision renames (e.g. `^https-keep-google-com-2-1`) |
| Archive chronology | 44 of 524 adjacent root rows in `bob_done.md` are out of completion-date order |
| Closed archived rows with no completion/cancel date | 15 |
| Open `#task` rows inside `done/` | 0 so far (open plain checklist items under done tasks do exist, by design) |
| Closed `#task` rows per daily note, last 40 days | max 4 (so the threshold currently protects daily notes) |

---

## 3. Bugs and sharp edges

Severity reflects the worst plausible outcome, not how often it happens.

### B1 — Open subtasks are archived with their closed root (High, latent but reachable)

**Mechanism.** `task_block_end` takes every deeper-indented line and never
looks at its content. The fixture `tests/fixtures/collect_done/nested_blocks.md`
shows an open child (`- [ ] Keep nested active task with parent`) moving into
the archive.

**Why it is reachable.** Bob's close gesture keeps open subtasks open under a
closed root on purpose:

> SV5: "Only the root closes; children stay byte-identical … `· its 1 open
> subtask stays open`" (`docs/task-dependencies.md:3738`)

**Impact.** That open `#task` ends up in `done/`, which reconcile, plan,
Ready, Next, freshness and projects never scan. It never surfaces again. It is
not reported as a loss either: the vault-loss guard counts the block ID as
still present because it scans `done/`.

### B2 — A closed child of an open parent is detached and re-parented in the archive (Medium)

**Mechanism.** The unit test `completed_child_moves_without_collecting_active_parent`
asserts that the archive receives `"  - [x] done child #task\n"`, still
indented. Appended after the previous archived root, that line becomes that
root's **subtask** in Markdown, Obsidian Tasks and Dataview.

**Impact.** The child is misattributed to an unrelated parent, and the open
parent loses the record of its finished step. For comparison, the Obsidian
Archiver plugin dedents archived subtasks to top level, and Linear refuses to
archive while the parent is open (§5).

### B3 — Source renames orphan the archive (Medium; one live instance)

**Mechanism.** The pairing is computed by filename in three places:
`archive_relative_path`, `source_relative_path_from_archive`, and
stats/periods identity. The authoritative links, `done_tasks:` and `parent:`,
are written but never read for pairing. (Pomodoro homes do read `parent:`, so
Bob is inconsistent with itself here.) When a source is renamed (the period
migration renamed `*_day.md` daily notes), Obsidian updates both frontmatter
links, but the filename rule now points at a note that does not exist.

**Live effects for `done/2026/20260528_day_done.md`:**

- stats attribute its 21 rows to the nonexistent `2026/20260528_day.md`;
- the period-review identity equivalence and the self-healing link repair skip
  it (`archived_block_targets` requires the derived source to exist).

**Next-run hazard.** If the renamed source ever qualifies again, the mover
creates a **second** archive, `done/2026/20260528_done.md`, and repoints
`done_tasks:` to it. That leaves two archives for one source, and the old one
is linked only by its own `parent:`.

### B4 — Daily notes (and other record notes) are eligible sources (Medium, latent)

**Mechanism.** No type check exists. Event Tasks are `#task` rows in the
daily note, and since `ended-synced-meetings-are-born-done` they are often
born `[x]`. The GTD checklist used to live in daily notes too, which is how
`20260528_day` got archived (21 closed rows).

**Impact on a day with ≥ 10 closed `#task` rows:**

- the Events section moves to `done/2026/YYYYMMDD_done.md`;
- `bob gcal sync` treats journaled rows whose line is gone as "deleted or moved
  away: tombstoned once" (`docs/gcal.md:628`), so the day's events read
  `removed_by_you`;
- the day stops being a self-contained record.

Period notes, `ref/`, `mail/` and record notes have the same exposure.

### B5 — Count threshold gives inconsistent, surprising visibility (Medium, UX)

**What happens.** In a busy note, a task you closed at 23:00 is gone by 03:30.
In a quiet project note, closed rows sit in `Done & Canceled` for months (289
rows older than 30 days). The `Done & Canceled` group swings between empty and
up to 9 rows, depending on activity rather than recency.

**What it costs.** Two things become hard to see: what changed this week in a
busy note, and whether a quiet finished project is really clean. The 55
terminal project notes still carry their unarchived tails.

### B6 — Not transactional; standalone runs are unlocked (Medium, reliability)

**What is missing.** `bob task archive` run by hand (outside `nightly`):

- never takes `bob_sync.lock`;
- reads every note up front, plans for the whole vault, then writes with no
  stale check;
- writes the archive **before** the source.

**Failure modes.**

- *Lost update.* A capture, reconcile, gcal sync or Obsidian edit landing
  between plan and write is overwritten.
- *Duplicated blocks.* If the source write fails after the archive write
  succeeds, the blocks exist in both notes. The next run archives them again,
  under `-1` IDs.

**The shared fix already exists.** `vault_rewrite::run` already provides
lock + stale check + rollback + verify + a single commit for renames. There is
also no `--dry-run` to preview a run, which matters more once the policy
changes.

### B7 — Many different answers to "is this under `done/`?" (Low today, a correctness trap)

**Rust: about 20 predicates, three rules.**

- *First component only:* `task_dependencies::is_archive_path`,
  `task_complete/successors.rs`, `pomodoro_themes/migrate.rs`,
  `task_status_hooks/references.rs`.
- *Any component:* `projects/surface.rs`, `relation_labels/{reverse,rename}.rs`,
  `task_complete/keep_moving.rs`, `capture_complete/{successor,candidates}.rs`,
  the archiver's own walker.
- *Any ancestor directory:* `capture/dependencies.rs`.

**Plugins: about 6 more.**

- `/^done\//i`, which is **case-insensitive**;
- `split("/")[0] === "done"`;
- `.some(segment === "done")`;
- a directory-list rule that also skips dot-dirs.

**Consequence.** A folder such as `projects/done/` would be skipped by the
archiver and by surfaces, yet treated as live by dependencies, and the reverse
in other places. Separately, the archiver walks dot-dirs (`.sase/`) that
reconcile skips. Every new feature adds another copy of the rule.

### B8 — Lost context and odd ordering in the archive (Low, UX)

**What is lost.** Archived blocks lose:

- their authored topic heading (`### Backend`), which reconcile carefully
  preserves in the source;
- for B2-style children, their parent;
- the date they were archived.

**Ordering.** Rows are ordered by archive run and source position, not by
completion (44/524 inversions in `bob_done.md`), and the archives grow without
bound. Stats and period reviews compensate, but reading `bob_done.md` by hand
is a long scroll.

### B9 — No restore path (Low frequency, high annoyance)

**Two failure points.**

- `bob task move` refuses any note under `done/` (`docs/task-move.md:80`).
- A task unchecked inside `done/` drops out of every lane and is never
  reported.

**Manual repair.** If you cut it back by hand, `[[done/…#^id]]` links do not
follow. Reconcile's R3 heal rule only covers dependency links; ledger Task
Links, relations and embeds would dangle. I inferred this from the code
paths; I did not test it end to end.

### B10 — Block-ID renames on collision (Low)

`^id` → `^id-1` keeps Markdown links correct, because link repair rewrites
them. References outside vault Markdown are not rewritten, for example IDs
pasted into research reports, beads or chats. This is mostly harmless today
and is listed for completeness.

---

## 4. Why the per-source archive itself is fine

- **It is the mainstream plain-text design.** Org's default archive location
  is "a file in the same directory as the current file, with the name derived
  by appending `_archive`", configurable per file, e.g. `#+ARCHIVE: %s_done::`.
  The Obsidian Archiver plugin offers `{{sourceFileName}}`-based archive paths.
- **Bob's identity model needs per-source scoping.** Dependency identity is
  `(path, block id)`, and every project note owns a `^prj`. In a central
  `done.txt`-style log, all archived `^prj` rows would collide and be renamed
  `^prj-1…`. That would break `is_project_task_id` and similar checks.
- **Locality is valuable.** "What did I finish on *this* project?" is answered
  by one note, and the `done_tasks:` property gives one-click navigation.
- **The link-repair machinery is already built and self-healing.** Replacing
  it would discard a lot of tested work (≈4.7k lines, ~70 tests).

**Alternatives I considered and rejected:**

| Option | Verdict |
| --- | --- |
| Keep everything in place and hide it (Things' Logbook view, Org's ARCHIVE tag, Taskwarrior status) | Rejected. Source notes like `bob.md` would carry thousands of closed rows, and every Obsidian Tasks and Bob scan would pay for them. Bob's reconcile grouping already *is* the "hide in place" stage for recent rows |
| Archive sibling inside the note (Org `C-c C-x A`, Archiver's `# Archived` heading) | Same growth problem. It is effectively today's `Done & Canceled` group |
| Central date-sharded log (todo.txt `done.txt`, journal-per-month) | Rejected for primary storage (identity collisions, loss of per-project locality). A chronological view is better built as a stats/Dataview *query* over `done/`, or as month headings inside each archive (R7) |
| Per-source archive (today) | **Keep**, fixing policy and plumbing |

---

## 5. How other systems handle done items

| System | When items leave | Where they go | Context recorded | Hierarchy rule | Restore |
| --- | --- | --- | --- | --- | --- |
| **Org mode** | Manual per subtree. `C-u C-c C-x C-s` offers child subtrees "with no open TODO entries"; `C-u C-u` offers those whose timestamp "is in the past" | `%s_archive` sibling file (manual example `%s_done::`), or an `Archive` sibling heading, or an in-place `:ARCHIVE:` tag that hides the entry | "the file from where the entry came, its outline path, the archiving time etc." (the `ARCHIVE_*` properties, set by `org-archive-save-context-info`) | Offers only subtrees with no open TODOs (prefix-arg form) | Context properties make refiling back possible |
| **Obsidian Archiver** (ivan-lednev) | Manual commands, rule-driven | Same file under `# Archived`, or a separate file whose path can use `{{sourceFileName}}`, `{{date}}`, `{{obsidianTasksCompletedDate}}` | `{{heading}}`, `{{headingChain}}`, "append stuff before archiving", date trees | The nested mode archives completed subtasks **dedented to top level**, leaving the open parent | Manual |
| **TaskPaper** | Manual "Archive @done Items" | An `Archive:` project at the bottom of the same file | Optional `@project(Name)` tag naming the origin project | Moves @done items with their children; users asked for "only items whose ancestors are also done" | Manual |
| **todo.txt** | On `do` (auto-archive on by default) or `archive` | One global `done.txt` | Only `x YYYY-MM-DD` | Flat format, none | Manual |
| **Things / Nirvana / Bonobo** ("Logbook") | Setting: immediately · after an hour · after a day · manually/never (Nirvana, Bonobo verified; Things' Immediately/Daily/Manually from memory, unverified) | A Logbook *view*; items keep their project/area (from memory) | Full item | n/a | Uncheck the item |
| **OmniFocus** | Manual "Archive Old Items…": items "completed before that date, or dropped items that haven't been changed since that date" | A separate, non-syncing archive file | Full item, with project | Item level | "drag and drop them into the desired location in your main database" |
| **Linear** | Automatic after a team-configured period of inactivity once closed (1–12 months per docs; 6 months was the old default) | Team archive, loaded on demand | Full issue | **Skips** when "the parent issue is not closed", "sub-issues are not all closed", or "there has been recent activity" | Restore from the team archive |
| **Taskwarrior** | `gc` moves completed and deleted tasks out of the working set (`pending.data` → `completed.data` in the file era) | Same database, outside the working set | Full task (UUID identity) | n/a | Modify status back |

### Lessons for Bob

1. **Age, not count.** Every automatic or semi-automatic trigger I found is
   time-based: a date cutoff (OmniFocus), an inactivity period (Linear), a
   past timestamp (Org), or immediately / after a day (Logbook apps). None
   gates on "N closed items in this file".
2. **Hierarchy guards are standard.** Both Linear and Org's bulk form refuse
   to archive a subtree with open descendants, and Linear also waits for the
   parent. Where a tool does archive a lone subtask (Archiver), it dedents it.
3. **Record where it came from.** Org's outline path, TaskPaper's
   `@project(...)` and Archiver's `{{headingChain}}` all exist because an
   archived item without context reads poorly later.
4. **Restore is first-class.** Every app-based system has a one-step way back.
5. **Projects archive as units.** Linear archives a project once all of its
   issues are archived. Bob has no project-level archive (55 terminal project
   notes remain at the vault root).

---

## 6. Design principles I would adopt

1. **Archive by age, inside a hierarchy-safe unit.** Move a closed root only
   when it is old enough and nothing beneath it is still open.
2. **Archive only notes whose job is to hold work** (area, project, inbox).
   Daily, period, reference, mail and record notes are records; never empty
   them.
3. **One pairing authority.** The frontmatter links are the source of truth.
   The filename convention is a derived invariant that Bob keeps true, not a
   guess.
4. **One path contract.** Define once what "under `done/`" means, and give
   Rust and the plugins shared test vectors.
5. **Same safety bar as every other vault rewriter:** lock, stale check,
   rollback, verify, one commit, and a dry-run.
6. **Reversible.** Reopening or restoring is a supported gesture, never a
   silent disappearance.

---

## 7. Recommended changes

Sizes: S ≈ ≤ 1 day, M ≈ 1–3 days, L ≈ multi-phase.

### R1 — Hierarchy-safe selection (fixes B1, B2) · S–M · do first

Select **archivable roots** instead of every closed line:

- A closed `#task` block is archivable only if **no ancestor list item is an
  open `#task`**. Closed children of open parents stay in place and leave
  later with their parent (Linear's rule). No dedent hacks; the parent keeps
  its history.
- An archivable block is **held** if its subtree contains any open `#task`
  (any non-`x/X/-` status). Report it as
  `held: N open subtasks (^parent)` in human and JSON output.
- Plain checklist items (no `#task`) inside the block keep moving with it, as
  today.
- Update `nested_blocks*.md` and `completed_child_moves_without_collecting_active_parent`.
  That test asserts the B2 behavior and should flip.

### R2 — Explicit source eligibility (fixes B4) · S

Only archive notes whose type is area, project or inbox, plus untyped plain
notes. Never archive:

- canonical daily notes (`YYYY/YYYYMMDD.md`);
- period notes;
- `ref/`, `mail/` and record-type notes;
- anything under a dot-directory.

Reuse the classifier that reconcile's Status Grouping already applies, so that
the notes which get a `Done & Canceled` group are exactly the notes that feed
`done/`.

### R3 — Frontmatter pairing plus rename-following (fixes B3) · M

1. Add one resolver, for example `archive_pair::for_source(path)` and
   `for_archive(path)`. It uses `done_tasks:` / `parent:` when they resolve and
   agree, and falls back to the filename rule otherwise. Point stats, periods,
   link repair, task-status-hooks archive reads and the plugin dependency
   identity at it.
2. When a resolved pair's archive path differs from the canonical
   `done/<new path>_done.md`, **rename the archive** (git mv) and rewrite
   `[[done/old_done#^id]]` links with the existing repair machinery inside a
   `vault_rewrite` transaction. Do this as an archive or nightly step. This
   keeps the filename bijection that ~20 readers rely on.
3. Add an orphan/duplicate check (`archive_orphan`, `archive_duplicate`) to
   `bob vault-sync doctor` or the nightly summary.
4. One-time fix: `done/2026/20260528_day_done.md` → `done/2026/20260528_done.md`,
   and update `done_tasks:`.

### R4 — One `done/` path contract (fixes B7) · S

- **Rust.** Add a single `is_done_archive(rel: &Path) -> bool`: the first
  normal component equals `done` exactly (case-sensitive, matching how the
  archive is written). Replace the ~20 local copies.
- **Walker.** Make the archiver's walker reuse the reconcile walker's skip
  rules (all dot-dirs).
- **Plugins.** Use one exported helper. Pin both sides with a shared
  `fixtures/done_paths/vectors.json`, following the existing cross-language
  vector pattern (`task_wikilinks`, `pomodoro_themes`). Example rows:
  `done/x_done.md` → true, `projects/done/x.md` → false, `Done/x.md` → false,
  `done.md` → false.

### R5 — Replace the count threshold with an age window (fixes B5) · M · behavior change, needs a decision record

**Rule.** A root is eligible when its close date (`[completion::]`, else
`[cancelled::]`) is at least **`archive.keep_days`** days before today
(**default 7**; `0` archives everything closed, like today's busy-note
behavior). Rows with no close date are eligible and counted in the report
(15 such rows exist in `done/` today).

**CLI.** Add `-k/--keep-days N`. Keep `-t/--threshold N` working as an
optional *additional* minimum batch per note (default 1, i.e. off), because
the CLI rules forbid removing options.

**Effect.**

- `Done & Canceled` reliably shows the last week of wins in every note, which
  lines up with the weekly period review.
- Quiet notes stop accumulating months-old rows (the 289 above drain on the
  first run).
- Busy notes stop losing yesterday's work overnight.

**Alternative.** Archive everything closed before the start of the current
ISO week. That batches link rewrites to once a week, but the cutoff swings
between 0 and 6 days. I prefer the rolling window for predictability.

**Process.** Record the change as a new decisions strand
(e.g. `done-archive-is-age-gated`) through `/sase_memory_write`.

### R6 — Put the archive on the shared transaction; add preview (fixes B6) · M

- Run `bob task archive` through `vault_rewrite::run`. That gives:
  - `bob_sync.lock` with a bounded wait, so standalone runs are safe;
  - before-image stale checks (`stale_note`);
  - atomic writes with rollback;
  - a verify hook: every moved block ID resolves exactly once, and no open
    `#task` lives in `done/`;
  - one commit and post-sync.
- Write the **source before the archive**, or rely on rollback, so a crash can
  never leave duplicates.
- Add `-n/--dry-run` and `-f/--format human|json`. JSON should list moves,
  holds (R1), skips by reason (R2), renames (R3) and link-repair counts.
  `nightly` keeps human output.

### R7 — Readable archives: month headings + origin context (fixes B8) · S–M · optional but recommended

- Insert each appended root under `## YYYY-MM` (its close month), creating the
  heading if needed and keeping headings in order. Within a month, append in
  close-date order. This is Org's date tree, made coarse. It caps how far you
  scroll and makes "what did I ship in October" a heading jump.
- When the root sat under an authored topic heading in the source, prefix it
  with a `### <topic>` sub-heading in that month section. Use headings, not a
  new task field, so task-line bytes stay untouched.
- Block IDs and link targets do not change, so link repair is unaffected.
  Existing archives can stay flat (only new appends are grouped) or be
  regrouped once by a migration.

### R8 — Restore and reopen safety (fixes B9) · M

1. **Detect.** Have reconcile or vault-sync report any open `#task` row inside
   `done/` as `open_task_in_archive`. Combined with R1, this should never
   happen unless you reopen something by hand.
2. **Restore.** Add `bob task unarchive <done/…#^id>`, or let `bob task move`
   accept a `done/` source for open rows only. It should move the block back
   into the source's intake (via `parent:`) and reverse the link repair for
   that ID.
3. **Optionally,** auto-restore reopened rows during the nightly run.

### R9 — Source-side affordance · S · optional

Give the source note one obvious way into its history. Options:

- a plugin command "Open done archive" (follows `done_tasks:`);
- a `📦 N archived` chip on the reconcile badge row.

The chip changes a fixed four-chip grammar that the plugins parse, so treat it
as a contract change. The command is cheaper.

### R10 — Project-level archiving · L · defer, decide first

The 55 terminal project notes could follow Linear's model: once a project is
terminal and all its rows are archived for `keep_days`, move the note itself
out of the root. This collides with several existing contracts:

- basename-link resolution ("basename links do not search `done/`");
- capture routes;
- Pomodoro homes;
- the `done/<stem>_done.md` pairing.

It deserves its own research and decision. A cheap interim step is to check
whether Obsidian's "Excluded files" for terminal projects, or `bob projects`
filtering, already gives enough relief. Verify Dataview/Tasks behavior with
excluded files before relying on it.

### Suggested sequencing

| Phase | Contents | Why first |
| --- | --- | --- |
| 1 | R1, R2, R4, plus the one-time orphan fix | Removes the silent-loss and record-corruption risks; small and mostly local to `collect_done/` |
| 2 | R6 (transaction, dry-run, JSON) | Gives a safe preview before the policy change lands |
| 3 | R5 (age window), with a decision record | Visible behavior change; preview it with `--dry-run` on the live vault first |
| 4 | R3 (pairing + rename-following), R7 (month headings) | Reliability and readability |
| 5 | R8, R9; R10 only after its own decision | Restore and UX polish |

### Acceptance vectors (for the implementing agent)

| ID | Given | Expect |
| --- | --- | --- |
| DA1 | `- [x] P #task` with child `- [ ] C #task` | P held (`open subtask`); nothing moves |
| DA2 | `- [ ] P #task` with child `- [x] C #task` closed 30 days ago | Nothing moves; C stays under P |
| DA3 | Closed P (old) with closed child C and plain `- [ ] note` checklist | P+C+note move together |
| DA4 | Daily note `2026/20261103.md` with 12 old closed Event Tasks | Not a source; untouched; gcal list unchanged |
| DA5 | Area note with rows closed 3 and 10 days ago, `keep_days = 7` | Only the 10-day row moves |
| DA6 | Closed row with no completion date | Moves; counted under `undated` |
| DA7 | Source renamed `a.md` → `b.md`; `done/a_done.md` has `parent: [[b]]` | Archive renamed to `done/b_done.md`; `done_tasks:` and inbound `[[done/a_done#^x]]` links rewritten; no second archive |
| DA8 | `projects/done/x.md` holds old closed rows | Treated as a normal source by every path predicate (Rust + plugin vectors agree) |
| DA9 | Source edited between plan and write | `stale_note`; nothing written; exit non-zero |
| DA10 | `--dry-run --format json` | Same plan as a live run; no writes, no lock wait, no commit |
| DA11 | Open `#task` inside `done/` | Reported `open_task_in_archive`; `unarchive` returns it to the source with links repaired |
| DA12 | Two moved rows close in Oct and Nov | Appended under `## 2026-10` and `## 2026-11` respectively; IDs unchanged |

---

## 8. Things I did not verify

- Things 3's exact Logbook option labels (support site returned 403). The
  "immediately / after a day / manually" pattern is verified for Nirvana and
  Bonobo Actions.
- Org's exact `ARCHIVE_*` property names. The manual text confirms file,
  outline path and archive time without naming them; the names come from
  `org-archive.el` mirrors.
- Linear's 1–12-month range comes from a search summary of their docs; the
  fetched page lists the skip conditions but not the range.
- B9's dangling-link claim for non-dependency links after a manual restore is
  inferred from the code, not reproduced.
- B1 and B2 are confirmed from code and fixtures. Neither has occurred in the
  live vault yet.

## Sources

**Bob code and docs (this workspace):**

- `src/native/collect_done/{mod,plan,transform,archive,link_repair,git}.rs`;
  `tests/fixtures/collect_done/nested_blocks*.md`
- `src/native/nightly.rs`, `src/native/vault_rewrite/mod.rs`,
  `src/native/stats/index.rs`, `src/native/task_dependencies/mod.rs`
- `docs/task-status-hooks.md` (Status Grouping), `docs/task-dependencies.md`
  (SV5, DR19), `docs/gcal.md`, `docs/task-move.md`, `docs/periods.md`,
  `docs/reference/vault-format.md`

**Bob plugins:** bob-plugins `130-fences-and-status.js`,
`080-dependency-identity.js`, `290-local-task-items.js`,
`085d-successor-relation-merge.js`, `031-task-wikilink-rules.js`.

**Live vault:** `~/bob` (`done/`, the `git log` of archive commits,
`2026/20260528.md`).

**External:**

- [Org manual — Moving a tree to an archive file](https://orgmode.org/manual/Moving-subtrees.html)
- [Org manual — Internal archiving](https://orgmode.org/manual/Internal-archiving.html)
- [org-archive.el (mirror)](https://code.delx.au/gnu-emacs/blob/e983096bb6a50fdae6625cb363642bcd74ec39c5:/lisp/org/org-archive.el)
- [Fuco1 — archive subtrees under the same hierarchy](https://fuco1.github.io/2017-04-20-Archive-subtrees-under-the-same-hierarchy-as-original-in-the-archive-files.html)
- Obsidian Archiver (ivan-lednev/obsidian-task-archiver) README, read from a
  local checkout; [plugin page](https://community.obsidian.md/plugins/obsidian-task-archiver)
- [obsidian-task-collector](https://github.com/ebullient/obsidian-task-collector)
- [Linear — Delete and archive issues](https://linear.app/docs/delete-archive-issues)
- [Linear changelog — auto-close and auto-archive](https://linear.app/changelog/2020-08-19-auto-close-and-auto-archive)
- [Linear changelog — auto-archive cycles and projects](https://linear.app/changelog/2021-04-15-auto-archive-cycles-and-projects-and-deleting-issues)
- [OmniFocus — Archiving and Backup](https://support.omnigroup.com/documentation/omnifocus/mac/2.7/en/archiving-and-backup/)
- [OmniFocus 3 Reference Manual](https://support.omnigroup.com/documentation/omnifocus/mac/3.12/en/omnifocus-extended/)
- [Omni forum — archiving actions in live projects](https://discourse.omnigroup.com/t/archiving-actions-in-projects-that-are-still-live/71515)
- [TaskPaper — Archiving](https://support.hogbaysoftware.com/t/archiving/2694)
- [TaskPaper — Archiving to include project name](https://support.hogbaysoftware.com/t/archiving-to-include-project-name/1185)
- [TaskPaper — Selective archiving](https://support.hogbaysoftware.com/t/selective-archiving/1455)
- [todo.txt-cli usage](https://www.github.com/todotxt/todo.txt-cli/wiki/Usage)
- [todo-txt(1)](https://dyn.manpages.debian.org/testing/todotxt-cli/todo-txt.1)
- [seanh — todo.txt](https://wombatech.pages.dev/service/https://www.seanh.cc/2022/11/04/todo.txt)
- [Nirvana — Logbook](https://www.nirvanahq.com/help/how-to/logbook)
- [Bonobo Actions — changing action behavior](https://bonobolabs.com/support/actions/changing-action-behavior/)
- [Taskwarrior terminology](https://taskwarrior.org/docs/terminology/)
- [Taskwarrior IDs](https://taskwarrior.org/docs/ids/)
- [TaskChampion docs](https://gothenburgbitfactory.github.io/taskchampion/using-task-command.html)
