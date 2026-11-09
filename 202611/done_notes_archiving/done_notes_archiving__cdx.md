# Done notes in Bob: preserve the files, strengthen the lifecycle

Independent research by **cdx**, 2026-11-09.

**Recommendation:** keep the per-source Markdown archives for now. The useful change is to make completion, archival, history browsing, and restoration distinct, dependable operations. Fix the archive writer and link semantics first; then make old work easy to find and restore. A wholesale migration to yearly files, one file per task, or a database would add substantial compatibility work without fixing the defects found here.

## Scope and evidence

I independently reviewed bob-cli at `7fe12b33e46db7429e5d7e95d91afe57103e13f0` and the linked bob-plugins checkout at `5e5e33b60f008c95fcd14b2ecbc2d71a9c30dfcd`, and consulted primary product documentation. I did not consult the other swarm researchers or their reports, transcripts, or findings.

I ran **13 isolated CLI invocations** covering parsing, links, rename behavior, locking, a concurrent edit, and a partial-write retry. The executable was the installed `bob 0.5.0`, SHA-256 `9ea06eafdcd0847c875b94056117a49615a2f42a7835a515f3b94dbf76d22052`. Its source revision was not exposed by `--version`; the inspected checkout independently contains the corresponding code paths. These are executable reproductions corroborated by source inspection, not a claim that I built and tested that exact checkout SHA.

All probes used disposable vaults inside this workspace, isolated from Git commits/pushes. No personal-vault content was inspected or modified, no production code was changed, and no full repository test suite was run. Consequently, the report establishes reproducible defects and design gaps, **not their frequency or existing damage in Bryan's vault**. The report is the findings record for the lead's triage; it does not launch implementation work.

## 1. What Bob actually does today

The convention is slightly richer than `done/<name>_done.md`: the source directory is mirrored. For example, `projects/launch.md` maps to `done/projects/launch_done.md`.

The collector:

- Scans eligible Markdown files, excluding `done` directories and the shared excluded directories.
- Recognizes `[x]`, `[X]`, and `[-]` lines containing `#task` and takes their indented descendants/continuations.
- Uses a **per-source count threshold, default 10**. Once a source reaches it, all collectible blocks move. This does not mean “retain the latest ten,” “archive after ten days,” or “archive ten tasks.” Below-threshold notes can retain their closed tasks indefinitely.
- Adds a source property such as `done_tasks: "[[done/projects/launch_done]]"`; the archive gets `parent: "[[projects/launch]]"` and `type: "[[done]]"`.
- Appends blocks to the archive, renames colliding block IDs with suffixes, and repairs many incoming wikilinks, embeds, simple Markdown block links, and dependency metadata.
- Can repair stale links to previously archived blocks when the conventional source/archive relationship and unique ID still establish the destination.
- Writes each archive before its source, then separate link-repair files. Each file replacement uses a temporary file and rename. A Git vault then gets a touched-path commit and push. `nightly` wraps the archive step in its shared maintenance lock and sync sequence; standalone `task archive` does not acquire that lock itself.

Sources: [collector and command](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/collect_done/mod.rs#L93), [planner](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/collect_done/plan.rs#L229), [path mapping and extraction](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/collect_done/transform.rs#L84), [archive metadata](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/collect_done/archive.rs#L107), [nightly](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/nightly.rs#L79).

This is worth preserving. It keeps human-readable history associated with its project/area, preserves authored child notes, and already handles much of the difficult cross-vault reference repair. The tests cover thresholds, cancellation, nested content, metadata repair, ID collisions, dependency fields, and idempotent ordinary link healing. The gaps below should extend that foundation rather than replace it wholesale. [Existing archive tests](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/collect_done/tests/plan.rs).

## 2. Reproduced reliability problems

Severity below reflects potential consequence, not measured incidence. All ordinary fixtures ran `bob task archive -t 1` against an isolated `BOB_DIR`.

| Finding | Reproduction and observed result | Consequence / confidence |
| --- | --- | --- |
| **Concurrent edits can be overwritten** | A controlled Git-probe shim appended `Concurrent editor text` to the source after planning and before writes. Archiving exited 0 and the added text disappeared. | High priority, reproduced. The writer installs planned strings without checking current source bytes. |
| **A partial write can duplicate a task on retry** | Force source temporary-file creation to fail after the archive is installed. First run exits 1 with the task in both source and archive. Remove the fault and rerun: archive now contains the same task as `^x` and `^x-1`. | High priority, reproduced. ID collision handling disguises a replay as a new historical task. |
| **Standalone archive ignores the shared lock** | Hold an exclusive lock on the file named by `BOB_VAULT_SYNC_LOCK_FILE`, then invoke archive. It still writes and exits 0. | High priority, reproduced. Nightly's outer lock is useful, but does not protect standalone invocations or nonparticipating editor writes. |
| **Examples become real archived tasks** | Put `- [x] Example #task ^sample` inside a fenced Markdown example, or between Obsidian `%%` comment delimiters. The collector removes the line and appends it as a live task in the archive. | High priority, reproduced in both contexts. The original note is altered and historical task counts can be polluted. |
| **An open task can disappear into history with its closed parent** | Close a parent `#task` while leaving its indented child `- [ ] Still needed #task ^c` open. Both move into `done/`. | High priority, reproduced. Active-task consumers that exclude archives can lose sight of the child. Plain, untagged checklist children need a different policy. |
| **A moved local link can silently target the wrong task** | Existing archive contains `Old ^x`; source contains closed `New ^x` with child link `[[#^x]]`. New becomes `^x-1`, but its child link remains `[[#^x]]`. | High priority, reproduced. The link now resolves to Old. This is worse than an obvious missing target. |
| **Local links are not consistently rebased** | An ID-less closed task contains `[[#^keep]]`, with `^keep` staying in the source. The link is copied unchanged. Separately, `[[#Evidence]]` is copied even though the heading stays in the source. | Reproduced. The ID-less case skips repair because there are no moved-block targets; heading links are outside the block-only repair. |
| **Source renaming can split its history** | `renamed.md` already points through `done_tasks` to `done/old_done.md`, whose `parent` is correctly `[[renamed]]`. Archive a new task: Bob creates `done/renamed_done.md` and replaces `done_tasks` with the new path. | Reproduced. Old content remains, but the primary archive pointer no longer reaches it. An old `[[renamed#^old]]` link was not healed either. |
| **Link repair has inconsistent Markdown and resolver rules** | `[[work#^p]]` is repaired but `[[WORK#^p]]` is left alone. Conversely, literal examples of `[[work#^p]]` inside inline code and fences are rewritten. | Reproduced. Case-sensitive archive resolution differs from the shared mover; literal examples are changed as though they were active links. |

### Why these happen

The archive path is an older, independent implementation. `transform_markdown` has no fence/comment/frontmatter context state; the task-block rule follows indentation without checking whether a descendant is still an actionable task. `repair_links_in_note` explicitly calls the shared repair routine with `skip_code = false`, while archive discovery uses its own case-sensitive `NoteIndex`. Local moved links are processed after relocation, losing the distinction between an old archive resident and an incoming block with the same original ID. [Extraction](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/collect_done/transform.rs#L137), [repair and early return](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/collect_done/link_repair.rs#L132), [archive-specific repair settings](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/collect_done/link_repair.rs#L483).

Per-file atomic replacement protects against a torn individual file; it does not make the multi-file move atomic. `apply_file_plan` writes archive then source without a read-set check or durable operation receipt. `run_collection` returns immediately on the first write failure, before the later Git commit. Git history is therefore helpful after successful operations, but does not solve the reproduced pre-commit failure. [Apply order](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/collect_done/plan.rs#L195), [file replacement](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/collect_done/archive.rs#L295), [Git finishing](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/collect_done/git.rs#L90).

By contrast, the task-move path already supplies shared locking, bounded retry, snapshots, guarded writes, recovery manifests, dry runs, and explicit partial-apply reporting. Reuse the underlying machinery and strengthen recovery for archive operations; do not promise that adopting it makes filesystem writes one indivisible transaction. [Task-move contract](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/docs/task-move.md), [guarded writer](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/task_status_hooks_write/apply.rs#L27).

### Additional gaps established by inspection

**Restore is not a complete archive lifecycle operation.** The public `bob task move` rejects both closed selections and either endpoint under `done/`. The plugin's transcluded reopen path changes the resolved task's status at its existing file and restores references; that path does not move an archived block back to its source. I did not execute Obsidian, so this is a code-level concern requiring an integration test, not an observed UI incident. Simply changing an archived checkbox to open is insufficient if the scanners still exclude the file. [Move refusals](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/docs/task-move.md), [plugin reopen](https://github.com/bobs-org/bob-plugins/blob/5e5e33b60f008c95fcd14b2ecbc2d71a9c30dfcd/plugins/task-status-cycler/src/160-plugin-completion.js#L691).

**Archive membership and source resolution are distributed assumptions.** The collector skips any directory component named `done`, whereas `task_dependencies::is_archive_path` checks the first component. Stats maps source paths by removing `done/` and `_done`; reference-task residence reads archive `parent`. These differ on noncanonical layouts and renamed sources. A new layout must not be introduced in the writer alone. [Archive classification](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/task_dependencies/mod.rs#L287), [stats attribution](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/stats/index.rs#L489), [reference residence](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/ref_tasks/walk.rs#L570).

**Custom statuses deserve parity tests.** Archive eligibility hardcodes three checkbox symbols, while `note_tasks` already exposes configured status types. I did not reproduce a real-vault status mismatch. Validate configured DONE/CANCELLED statuses and exclude NON_TASK explicitly; do not assume every Tasks `done` result is a Bob task eligible for movement. [Shared task model](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/note_tasks.rs#L24).

**History lacks structural context.** The append contains the task block, not its original heading or parent-task breadcrumb. Moving a completed child away from an open parent can leave an indented item with no explanatory parent in the archive. Existing tests explicitly preserve that indentation. The policy should retain enough context to understand and restore it. [Nested-child test](https://github.com/bobs-org/bob-cli/blob/7fe12b33e46db7429e5d7e95d91afe57103e13f0/src/native/collect_done/tests/unit.rs#L201).

## 3. What other systems suggest

These are useful patterns, not recommendations to migrate Bob to another product. The product facts come from official documentation retrieved for this report; the Bob implications are my inferences.

| System | Relevant documented behavior | Lesson for Bob |
| --- | --- | --- |
| **Org mode** | Supports moving a subtree to a per-file archive, including configurable destinations. Records original file, outline path, and archive time. Its bulk eligibility check can look for open TODO descendants. Also supports an in-place ARCHIVE tag that hides a subtree from normal agenda views. | Per-note archives are a well-established design. Preserve provenance, check unfinished descendants, and separate hiding from physical movement. [Moving subtrees](https://orgmode.org/manual/Moving-subtrees.html), [internal archiving](https://orgmode.org/manual/Internal-archiving.html). |
| **Things** | Completed items are accessible through Logbook search; “Continue Search” widens the search to notes, checklists, and logged items. A Logged Projects view exposes completed projects. | Offer a deliberate history search and project history view, without making ordinary action pickers noisy. The main affordance is retrieval, not a clever filename. [Quick Find documentation](https://culturedcode.com/things/support/articles/2803584/). |
| **Todoist** | Completed tasks can be shown inside their original project and uncompleted there. Project archival is separate: it removes a project from the active list and supports restoration with its data preserved. Recurring completion history has separate restrictions. | Distinguish completing a task, archiving its storage, and closing a project. Make undo/reopen visible and explain recurrence-specific limits. [Completed tasks](https://www.todoist.com/help/todoist/features/view-completed-tasks-in-todoist-J19h2s), [projects](https://www.todoist.com/help/todoist/features/introduction-to-projects-TLTjNftLM). |
| **Taskwarrior** | A completed task leaves the working set and loses its short numeric ID, but remains addressable by permanent UUID. Reopening uses that identity. | Keep active indexes small while keeping history addressable. Stable identity is a long-term architectural direction, not a reason to immediately replace Bob's path/block links. [IDs](https://taskwarrior.org/docs/ids/), [reopening FAQ](https://taskwarrior.org/support/faq/). |
| **Obsidian Tasks** | Queries filter by status type and completion date, and group results by file or heading. `done` includes DONE, CANCELLED, and NON_TASK. | A virtual history view can combine archived and not-yet-archived rows without physically regrouping files. Keep cancellation distinct from successful completion. [Filters](https://publish.obsidian.md/tasks/Queries/Filters), [grouping](https://publish.obsidian.md/tasks/Queries/Grouping). |

The strongest common idea is **a small working set plus accessible history with retained context**. Neither a yearly filename nor a new storage engine is necessary to provide that experience.

## 4. Choosing the storage model

| Option | Benefit | Cost in Bob | Judgment |
| --- | --- | --- | --- |
| Keep per-source `done/..._done.md` | Familiar, portable, local context; minimizes migration | Requires safe moves and unified source resolution | **Keep now.** |
| Keep everything in its original note, hide closed work | Stable locations and full outline context | Source files and editor payloads grow; all active consumers must filter consistently | Useful as a presentation technique and possibly for already-dated daily notes; not the universal default yet. |
| One global/yearly archive | Easy chronological browsing and bounded yearly files | Loses simple per-source parent; adds shared write hotspot; changes stats/ref/dependency assumptions | Build chronological views instead. |
| Per-source yearly shards | Caps individual file growth, retains source grouping | Needs one-to-many archive binding, discovery, migration, and updated readers | Consider only after measured file-size or latency problems. |
| One Markdown note per task | A durable task location can simplify task identity | File-count growth, different capture/task-drawer model, extensive plugin migration | Disproportionate to this request. |
| Database/event-log source of truth | Stronger transactional and temporal modeling | Competes with editable Markdown and cross-host Git workflow | Do not adopt for this work. A rebuildable local index or operation journal is different and can help. |

No live-vault size or latency data was gathered. There is no evidence here that a sharding project would improve Bryan's experience more than fixing the current writer and adding history navigation.

## 5. A better lifecycle on the existing files

### Safe archive and explicit source binding

Use a shared archive resolver across the collector, stats, reference residence, related-task search, dependencies, and plugins. Prefer a validated existing source `done_tasks` link with a matching archive `parent`; use the conventional filename only as the creation default and a legacy fallback. Reject contradictory or multiply claimed bindings rather than overwriting ownership metadata. A source rename should retain its existing archive binding; renaming the archive filename for tidiness can be a separate, previewed operation.

Do not create a second archive automatically when a valid differently named one is already bound. If multiple old archives exist, expose all of them in the diagnostic/history view first. Any consolidation must account for duplicate anchors and repair inbound references in one guarded operation. Keep old data until the move and reference audit are verified.

For moved content, resolve links against the **original block's source context** before allocating destination IDs. Preserve local links to co-moved blocks, qualify links to targets that stayed behind, and leave genuine references to old archive residents alone. Handle heading links and explicitly relative attachment links as well as block links. Obsidian distinguishes same-note headings from headings in another note, so the `[[#Evidence]]` reproduction has a clear semantic failure. [Obsidian link semantics](https://obsidian.md/help/links).

Use the shared task parser and Markdown context handling. An automatic run should hold a closed parent that still contains an open, actionable `#task` descendant and name that child in its report. Preserve ordinary unchecked checklist bullets as authored notes; the existing fixture intentionally moves an untagged checkbox with its parent. Do not silently complete, cancel, or discard those children.

### A History view that answers real questions

Add a history surface reachable from an area/project and from global search. It should combine closed tasks still in the source with archived tasks, identify their logical source, and offer:

- Text search across task titles and child notes; source/project and date filters.
- Separate completed and canceled outcomes; undated rows explicitly marked unknown.
- Newest-first presentation without rewriting the archive into a new sort order.
- “Open task,” “Open source,” and “Restore” actions with the relevant work/cancel/schedule notes visible.

This answers “How did I solve this last time?”, “What did I finish for this project?”, and “Where did that task go?” Existing stats already includes archived rows, and relation picking already exposes some archived targets; the new surface should reuse those readers rather than imply history is currently absent everywhere. Avoid inventing a second definition of “done this week.”

A read-only CLI report should be top-level under the project's CLI membership rule, for example a proposed `bob history`; a task-line mutation belongs under `bob task`. These are proposed names, not available commands.

### Restore without losing the past

Offer a dedicated restore operation, tentatively `bob task restore`, and route archive reopen gestures through it. Preview the source destination and refuse an invalid/missing destination until the user chooses an eligible note. Move the whole selected block, repair inbound references and projected dependency IDs, and then apply the existing reopen semantics. Respect current prerequisites, project blocking, and lane rules; do not automatically put the restored task into today's Pomodoros.

Keep old Work/Cancel/Rotten/Schedule Log prose. Preserve recorded Pomodoro time and notes. Archive movement itself should not alter completion dates, freshness, or review streaks. Reopening is a separate explicit gesture and must define how its existing completion/cancellation fields are retired. Existing stats treats a reopened task as no longer Done; preserve that contract in this change rather than quietly introducing an event-counting metric.

For recurring occurrences, reading tasks, merged-task tombstones, and a project's `^prj`, initially require explicit supported handling or a clear refusal. “Restore old occurrence” must not create a second recurrence; “restore merged task” must not silently undo or duplicate the target's merged notes. A separate “create follow-up from this” action could be useful later, but should create a new identity rather than masquerade as restoration.

### Predictable retention

After reliability and retrieval land, replace the count cliff with an understandable policy. My starting proposal is **keep the last seven calendar days of closed work in the source, archive older closed work nightly**, plus a scoped “archive now” action. Seven days is a suggested usability default, not a researched optimum; keep it configurable and preview its impact before rollout.

Use actual completion/cancellation dates, never archive time or filesystem mtime as a substitute. Missing or invalid close dates stay visible in diagnostics and can be explicitly archived without fabricating a completion date. Preserve existing `--threshold` behavior for compatibility; introduce the new nightly policy explicitly rather than changing the meaning of its argument.

Canonical daily notes deserve separate evaluation: they are already partitioned by date, and retaining their Event Tasks/`^gtd` may preserve daily context with little per-file growth. Do not change that policy incidentally in the first safety patch; validate ledger, checklist, stats, and reference behavior first.

## 6. Verification and rollout

Before any real-vault migration, build a **read-only archive audit** reporting source/archive binding conflicts, orphan archives, duplicate block IDs, open actionable tasks under `done/`, unresolved local links, and missing/invalid close dates. Include file/block locations, severity, and counts; do not repair ambiguous duplicates by guessing which copy is authoritative.

The regression suite should establish:

1. Fences, inline code, comments, frontmatter, and non-task checklist examples are not selected or rewritten as live tasks.
2. A closed parent with an open tagged descendant is held; ordinary child prose/checklists remain intact.
3. Link targets retain identity across collision suffixes, case variants, co-moved blocks, ID-less parents, stayed targets, headings, embeds, and explicit relative paths.
4. A stale source, archive, or link-only file stops/replans safely; standalone archive honors the maintenance lock.
5. Failure at every replacement boundary leaves a usable recovery record. Retrying does not silently duplicate content; recovery resumes or refuses from recorded state rather than replaying selection.
6. Rename and restore preserve logical source, reference residence, dependency resolution, and stats totals. A second no-change run is byte-identical.
7. Git commit failure and push failure are reported separately from local write success; later recovery/sync does not replay archival.

Stage the rollout: fix pure parsing/link defects with fixtures; adopt guarded writes and recovery; run an audit/preview; repair only unambiguous legacy metadata; then add History/Restore and change retention. Archive files remain ordinary Markdown. They are not absolutely immutable: existing supported link repairs and relation-label renames legitimately update history.

### Reproducing the two write failures safely

The following minimal harness captures the fault mechanism used in this investigation. It creates only temporary fixture files, substitutes a Git probe that never commits or pushes, and removes the fixtures afterwards. Run from a disposable workspace with `bob` installed. It tests an installed binary, so record its version/hash separately.

```python
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

binary = shutil.which("bob")
assert binary, "bob must be installed"
with tempfile.TemporaryDirectory(prefix=".archive-repro-", dir=".") as tmp:
    root = pathlib.Path(tmp).resolve()
    bindir = root / "bin"
    bindir.mkdir()
    fake_git = bindir / "git"
    fake_git.write_text(
        "#!" + sys.executable + "\n"
        "import os, pathlib\n"
        "v = pathlib.Path(os.environ['BOB_DIR'])\n"
        "if os.environ.get('ARCHIVE_REPRO') == 'change':\n"
        " p = v / 'work.md'\n"
        " p.write_text(p.read_text() + 'Concurrent editor text\\n')\n"
        "elif os.environ.get('ARCHIVE_REPRO') == 'fail':\n"
        " (v / ('.work.md.' + str(os.getppid()) + '.tmp')).mkdir()\n"
        "raise SystemExit(1)\n"
    )
    fake_git.chmod(0o755)
    for mode in ("change", "fail"):
        vault = root / mode
        vault.mkdir()
        (vault / "work.md").write_text("- [x] Done #task ^x\n")
        env = dict(os.environ)
        env.update(
            BOB_DIR=str(vault),
            GIT_DIR=str(root / "missing.git"),
            PATH=str(bindir) + os.pathsep + os.environ["PATH"],
            ARCHIVE_REPRO=mode,
        )
        def run():
            result = subprocess.run(
                [binary, "task", "archive", "-t", "1"],
                env=env, capture_output=True, text=True, timeout=15,
            )
            print(mode, result.returncode, result.stderr)
            for path in sorted(vault.rglob("*.md")):
                print(path.relative_to(vault), repr(path.read_text()))
        run()
        if mode == "fail":
            for path in vault.glob(".work.md.*.tmp"):
                path.rmdir()
            env["ARCHIVE_REPRO"] = "none"
            run()
```

Observed: `change` exited 0 and lost the injected text; `fail` exited 1 with both copies present; its retry exited 0 and produced `^x` plus `^x-1` in the archive. These demonstrate stale-write and retry behavior, not a claim about the likelihood of a real disk failure.

## 7. Recommended changes to consider, in priority order

1. **Fix archive safety first.** Reuse shared Markdown/task parsing and guarded write infrastructure; honor the standalone lock; preserve/recover partial operations; hold open tagged descendants. Add the reproduced cases before broad refactoring. This is the highest-value work because it prevents loss, hidden work, and duplicate history.
2. **Repair link semantics and unify archive binding.** Resolve outgoing links before relocation, handle ID collisions correctly, skip literal code, and honor a valid existing `done_tasks`/`parent` relationship across source renames. Update all readers together; keep current filenames as defaults.
3. **Add preview and a read-only archive health report.** Expose exact task moves, ID changes, link repairs, exclusions, and recovery state. Audit existing archives before offering targeted repairs; do not infer historical damage from these fixtures alone.
4. **Make History and Restore first-class actions.** Combine source-resident and archived closed tasks in one searchable per-project/global view, and make archived reopening return the task to an eligible active note with its references intact.
5. **Then adopt predictable age-based retention.** Trial seven days, configurable, with explicit archive-now and an unknown-date policy. Keep completion, cancellation, archival time, and reopening distinct. Evaluate dated daily notes separately.
6. **Defer storage migration.** Do not rename every `_done.md`, create a universal archive, add UUIDs across the task system, or shard by year as part of this effort. Revisit sharding only after measuring a concrete scale problem and after the shared archive resolver removes filename dependence.
