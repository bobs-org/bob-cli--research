# Architecture, Comparative Analysis, and Redesign Proposals for Bob Done Notes

**Author:** researcher `gem` (5-researcher swarm)  
**Date:** 2026-11-09  
**Status:** Completed Research  
**Target Repository:** `bob-cli` / `bob` Obsidian Vault  

---

## 1. Executive Summary

In Bryan's Personal Knowledge Management (PKM) and task-management ecosystem (**Bob**), completed and canceled tasks are periodically moved from active notes into paired archive notes located under `done/<name>_done.md` (e.g., `sase.md` $\rightarrow$ `done/sase_done.md`). This process is executed primarily by the `bob task archive` command (historically known as `collect-done`) during automated nightly maintenance (`bob nightly`).

While this mechanism successfully keeps high-traffic active notes lean and prevents the review walk (`]s` / `[s`) from being slowed down by hundreds of completed checklist items, an in-depth audit of the `bob-cli` codebase, the linked `bob-plugins`, and the live `~/bob` vault reveals several **concrete correctness bugs, fragile architectural assumptions, and ergonomic friction points**:

1. **Active Child Tasks Eaten by Done Parents (Zombie Task Bug):** The collection parser (`task_block_end`) treats any indented block beneath a completed parent as part of that parent's payload. If an active, uncompleted task (`- [ ]`) is nested under a completed parent (`- [x]`), it is swept into `done/`, where it vanishes from review walks, daily schedules, and active task hooks forever.
2. **Brittle Path Stripping on Note Rename/Move:** The system identifies a source note for an archive note by naive string stripping (`strip_prefix("done")` and `strip_suffix("_done")`). If a source note is renamed or reorganized in Obsidian, the archive's `parent:` frontmatter desynchronizes from this filename derivation rule. The archive planner then silently skips the archive, fails to repair links, and eventually spawns a second, split archive file.
3. **Sub-Threshold Stagnation in Finite Projects:** The hardcoded default threshold of 10 completed tasks (`--threshold 10`) works well for long-running area notes, but completely fails finite project notes. A completed project with 4 tasks never hits the threshold during `bob nightly`; its completed tasks sit in `projects/` indefinitely unless manually archived with a custom threshold flag.
4. **Strict One-Way Valve (No Unarchive/Restore Path):** `bob task move` contains an explicit refusal check forbidding any task movement where the source or destination is under `done/`. If a task is archived prematurely or accidentally, there is no CLI command to restore it; the user must manually perform delicate Markdown surgery across files.
5. **Contextual & Chronological Collapse in Archives:** Archived tasks are dumped at the end of `_done.md` as an undifferentiated, flat list. The original section hierarchy (milestones, drawers) is erased, and tasks without an explicit `[completion:: ...]` stamp lose all historical chronology.
6. **Double Identity & Link Churn:** Rewriting wikilinks from `[[note#^id]]` to `[[done/note_done#^id]]` triggers massive Git commit diffs across notes and daily ledgers. Furthermore, downstream reporting tools (such as `bob periods brief`, recorded in bead `bob-cli-gs`) have suffered critical bugs when reconciling time attribution across dual source/archive identities.

By examining established archiving paradigms across **Emacs Org-mode**, the **Obsidian community ecosystem**, **Things 3**, **Todo.txt**, and the **GTD/PARA methodology**, this report evaluates alternative architectures: in-place section folding, centralized periodic logbooks, and whole-container lifecycle transitions.

We conclude with a **three-phase actionable recommendation plan**:
- **Phase 1 (Immediate Safety & Correctness):** Guard `task_block_end` against capturing open tasks, make archive resolution resilient to file renames via frontmatter metadata, auto-flush terminal projects with a zero threshold, and add `bob task restore`.
- **Phase 2 (Ergonomics & Structure):** Introduce date-partitioned section headers in `_done.md` (`## Archived YYYY-MM-DD`), automatically reconcile status chips after archiving, and introduce first-class whole-project archiving (`bob project archive`).
- **Phase 3 (Strategic Consolidation):** Implement transparent identity resolution across CLI tools so links remain valid regardless of whether an anchor is active or archived.

---

## 2. Current Architecture & Mechanics of Done Notes in Bob

### 2.1 File Placement, Naming, and Frontmatter Coupling

When `bob task archive` decides to archive completed tasks from a source note, it maps the source path to an archive path using the following deterministic rule (implemented in `src/native/collect_done/transform.rs:archive_relative_path`):

```
source:  <parent_dirs>/<stem>.md
archive: done/<parent_dirs>/<stem>_done.md
```

For example:
- `bob.md` $\rightarrow$ `done/bob_done.md`
- `projects/Shared.md` $\rightarrow$ `done/projects/Shared_done.md`

#### Why the Redundant `_done` Suffix Exists
A common question is: *Why `done/<stem>_done.md` instead of simply `done/<stem>.md`?*  
In Obsidian, wikilinks without a directory path (e.g., `[[bob]]`) resolve across the entire vault by file stem. If Bob placed the archive at `done/bob.md`, Obsidian would see two files named `bob.md` in the vault. Any unpathed link `[[bob]]` would become ambiguous, triggering Obsidian warnings and potentially causing link-resolution ambiguity in Dataview queries (such as the Dataview warnings observed live in Bryan's vault: `warning: ambiguous Dataview link target "foo"; matched 7 notes`).  
Adding the `_done` suffix ensures that the filename stem itself remains unique, preserving `[[bob]]` as an unambiguous reference to the active note.

#### Frontmatter Bi-Directional Linking
The archiving process links the source and archive notes through YAML frontmatter (implemented in `src/native/collect_done/archive.rs`):
- **Source Note:** Receives `done_tasks: "[[done/<stem>_done]]"`.
- **Archive Note:** Receives `parent: "[[<stem>]]"` and `type: "[[done]]"`.

```yaml
# Source Note Frontmatter
---
done_tasks: "[[done/projects/Shared_done]]"
---

# Archive Note Frontmatter
---
parent: "[[projects/Shared]]"
type: "[[done]]"
---
```

### 2.2 The Collection & Migration Engine (`collect_done`)

The archive pipeline runs in `src/native/collect_done/`:
1. **Threshold Filtering:** `build_collection_plan(vault, threshold)` scans all Markdown files (excluding `done/`, `.git/`, `.obsidian/`, `.bob/`, `_templates/`, `_generated/`, and `_conflicts/`). A note is only scheduled for task extraction if the count of completed (`[x]`, `[X]`) or canceled (`[-]`) tasks tagged with `#task` meets or exceeds `threshold` (default: 10).
2. **Extraction:** `transform_markdown` strips eligible task blocks from the source text and prepares an `archive_append` payload.
3. **Block ID Deduplication:** If an archived task carries a trailing block anchor (e.g., `^my-task`), `collect_done` checks whether that anchor already exists in the destination `_done.md`. If a collision occurs, it renames the incoming anchor to `^my-task-1` (or next available integer suffix) and records a translation mapping.
4. **Link & Dependency Rewriting:**
   - Every file in the vault (including `done/` notes and daily notes) is scanned for inbound references to moved block IDs.
   - Wikilinks like `[[source#^my-task]]` and embeds `![[source#^my-task]]` are rewritten to `[[done/source_done#^my-task]]`.
   - Dataview task fields `[id:: source__my-task]` and `[dependsOn:: source__my-task]` are updated to `done__source_done__my-task`.
   - Pathless internal links in the archived task that refer to blocks remaining in the source note are qualified to `[[source#^other-block]]`.
5. **Git Staging & Commit:** In `src/native/collect_done/git.rs`, the modified source notes, created/updated archive notes, and repaired link-bearing notes are staged and committed with `bob task archive YYYY-MM-DD`.

### 2.3 The Role of `done/` in the Broader Ecosystem

The `done/` folder acts as an **exclusion zone** across Bob's subsystems:
- **Task Status Hooks (`task_status_hooks`):** Skips `done/` during active task reconciliation. It never tracks open tasks in `done/`, nor does it update status chips for archive notes. It makes only one narrow read-only exception: resolving explicit `[[done/...#^id]]` targets as closed history for prerequisite dependency checks (`resolve_archive_target`).
- **Review Walk (`bob review` / `]s` / `[s`):** The GTD review walk traverses only active notes; `done/` is entirely invisible.
- **Task Move (`bob task move`):** Explicitly blocks moving tasks into or out of `done/`.
- **Capture (`bob capture`):** Forbids blocking an archived task with `*`, relating an archived task with `LINKS`, or targeting an archived note for task intake.
- **Query & Reporting (`bob query`):** DQL queries must explicitly exclude `-"done"` or check `type != "[[done]]"` to avoid polluting project and task reports.
- **Stats Indexing (`stats/index.rs`):** Unlike most commands, `stats` *does* scan `done/` to compute lifetime throughput and completion velocity, mapping archived tasks back to their source notes via `source_relative_path_from_archive`.

### 2.4 Empirical Evidence from Bryan's Vault

Querying Bryan's production Bob vault (`~/bob`) reveals how done notes behave in real-world usage:
- **Total Archive Notes:** Exactly **31 notes** reside in `done/`.
- **Task Distribution:** A small number of long-running "Area" and "Inbox" notes account for the overwhelming majority of archived tasks:
  - `done/gtd_daily_done.md`: **1,084 tasks**
  - `done/sase_done.md`: **831 tasks**
  - `done/bob_done.md`: **536 tasks**
  - `done/mac_inbox_done.md`: **135 tasks**
  - `done/gkeep_inbox_done.md`: **82 tasks**
  - `done/dev_done.md`: **54 tasks**
  - `done/needs_attn_tasks_done.md`: **39 tasks**
  - `done/job_done.md`: **32 tasks**
- **Legacy Artifacts:** Several notes in year directories (e.g., `2025/20250308_done.md`) carry frontmatter indicating they were generated during migration from Bryan's earlier Emacs Org-based system (`zorg_source: 20250308_done.zo`), proving a decade-long continuity of the "done file" mental model.

---

## 3. Comprehensive Audit of Existing Bugs, Edge Cases, and Fragilities

A rigorous line-by-line inspection of the Rust source code reveals several critical failure modes in the current implementation.

### 3.1 Bug 1: Active Child Tasks Eaten by Done Parent (Zombie Task Bug)

**Location:** `src/native/collect_done/transform.rs:task_block_end`  
**Severity:** High (Silent Data Ingestion & State Corruption)

#### Mechanism
When `collect_done` identifies a completed task line (e.g., `- [x] Parent epic #task`), it determines the extent of the task's block by calling `task_block_end(&lines, index, task_line.indent)`:

```rust
pub(crate) fn task_block_end(
    lines: &[&str],
    start: usize,
    task_indent: usize,
) -> usize {
    let mut index = start + 1;
    let mut include_end = start + 1;
    let mut pending_blank = false;

    while index < lines.len() {
        let (content, _) = split_line_ending(lines[index]);
        if content.trim().is_empty() {
            pending_blank = true;
            index += 1;
            continue;
        }

        if leading_indent_len(content) > task_indent {
            pending_blank = false;
            index += 1;
            include_end = index;
            continue;
        }

        break;
    }
    // ...
    include_end
}
```

Notice that `task_block_end` treats **any line indented deeper than the parent task line** as part of the parent's block. It does not check whether any of those indented lines contain uncompleted checklist items (`- [ ]`).

In `tests/fixtures/collect_done/nested_blocks.md`, this behavior is even codified as an accepted test case:
```markdown
- [x] Ship scanner #task
  - [ ] Keep nested active task with parent
  Plain continuation for the done task
  - [-] Canceled nested task also moves #task
```
The test verifies that line 4 (`- [ ] Keep nested active task with parent`) is stripped from the source note and appended into the `_done.md` file!

#### Consequence
In actual use, if a user checks off a parent item while child sub-tasks or follow-up checkboxes remain open, `bob task archive` **rips the open child tasks out of the active note and moves them into `done/`**.  
Because all active task scanning (review walks, `task_status_hooks`, agenda views) skips `done/`, those open sub-tasks become **permanent zombie tasks**. They are never scheduled, never displayed in `bob capture` agendas, and never brought up during review. The user will believe the task was lost or deleted.

---

### 3.2 Bug 2: Note Rename/Move Desynchronization & Archive Fragmentation

**Location:** `src/native/collect_done/link_repair.rs:source_relative_path_from_archive`  
**Severity:** Medium-High (Silent Archival Failure & Archive Duplication)

#### Mechanism
In `link_repair.rs`, the system attempts to determine which source note corresponds to an archive note:

```rust
pub(crate) fn source_relative_path_from_archive(
    archive_relative_path: &Path,
) -> Option<PathBuf> {
    let archive_note_path =
        archive_relative_path.strip_prefix(Path::new("done")).ok()?;
    let source_stem = archive_note_path
        .file_stem()
        .and_then(OsStr::to_str)?
        .strip_suffix("_done")?;
    let mut source_relative_path =
        archive_note_path.with_file_name(format!("{source_stem}.md"));
    // ...
    Some(source_relative_path)
}
```

Notice that this derivation is **strictly string-based**:
1. Remove `done/` from the path.
2. Remove `_done` from the file stem.

Next, in `link_repair.rs:archived_block_targets`:
```rust
if !archive_parent_matches_source(
    &archive_contents,
    archive_relative_path,
    &source_relative_path,
    &note_index,
) {
    continue;
}
```
`archive_parent_matches_source` checks whether the `parent: "[[...]]"` frontmatter in `archive_relative_path` resolves to the newly computed `source_relative_path`.

#### The Failure Sequence
1. Suppose a project note exists at `projects/Alpha.md`. It hits the threshold, and `done/projects/Alpha_done.md` is created with `parent: "[[projects/Alpha]]"`.
2. The user renames `projects/Alpha.md` to `projects/Bravo.md` in Obsidian.
3. Obsidian's link updater updates the frontmatter of `done/projects/Alpha_done.md` to `parent: "[[projects/Bravo]]"`. However, Obsidian **does not** automatically rename the file `done/projects/Alpha_done.md` to `done/projects/Bravo_done.md` (Obsidian only renames the target file and inbound links, not associated peer files).
4. The next time `bob task archive` runs:
   - It examines `done/projects/Alpha_done.md`.
   - `source_relative_path_from_archive` derives `projects/Alpha.md`.
   - But `projects/Alpha.md` no longer exists!
   - Even if `projects/Alpha.md` still existed, `archive_parent_matches_source` checks if `parent` (`[[projects/Bravo]]`) resolves to `projects/Alpha.md`. They do not match!
   - Result: `archived_block_targets` **silently ignores** `done/projects/Alpha_done.md`.
   - Link self-healing and anchor tracking for all historical tasks in `Alpha_done.md` are completely disabled.
   - When `projects/Bravo.md` eventually accumulates 10 completed tasks, `collect_done` creates a **brand-new file** `done/projects/Bravo_done.md`.
5. The project's completion history is now permanently fragmented across two disconnected files: `Alpha_done.md` and `Bravo_done.md`.

---

### 3.3 Bug 3: Sub-Threshold Stagnation in Finite Projects

**Location:** `src/native/collect_done/plan.rs:build_collection_plan`  
**Severity:** Medium (Ergonomic Degradation & Clutter Accumulation)

#### Mechanism
`DEFAULT_THRESHOLD` is set to `10`:
```rust
let moves_tasks = transform.task_count >= threshold;
```
For ongoing area hubs (`sase.md`, `bob.md`), 10 completed tasks accumulate every few days, so `nightly` regularly sweeps them clean.

However, many GTD projects in Bob are finite, short-lived initiatives containing 3 to 7 tasks total. When the user finishes the last task and checks off the project root (`- [x] #task #prj Finalize release ^prj`), the project becomes **terminal** (`TargetProjectStatus::Done`).  
Because total completed tasks ($5 < 10$) are below the threshold, **`bob nightly` never touches the note**. The completed tasks sit in `projects/Release.md` indefinitely.  
If the user wants to clear them, they must remember to manually open a terminal and run `bob task archive -t 1`.

---

### 3.4 Bug 4: Strict One-Way Valve (No Unarchive / Restore Pathway)

**Location:** `src/native/task_move/plan.rs:500-506`  
**Severity:** Medium (Workflow Inflexibility & Operational Danger)

In `src/native/task_move/plan.rs`:
```rust
Self::ArchivePath { path, role } => {
    write!(
        formatter,
        "{role} {} is under done/ and cannot be used",
        path.display()
    )
}
```
If a task was marked done by mistake, or if an open task was swallowed by Bug 3.1 and archived, the user might attempt:
```bash
bob task move done/sase_done.md sase.md ^accidental-task
```
`task_move` **hard-refuses with an error**: `source done/sase_done.md is under done/ and cannot be used`.  
There is no `bob task unarchive` or `bob task restore` command. The user has to manually copy the task line out of `_done.md`, paste it into the active note, manually remove it from `_done.md`, and manually inspect links to ensure anchors did not break.

---

### 3.5 Bug 5: Stale Visual Counters & Grouping Artifacts on Manual Run

**Location:** `src/native/collect_done/plan.rs` vs `src/native/task_status_groups/`  
**Severity:** Low-Medium (UI Desynchronization)

In Bob, active task sections feature visual status chips:
```markdown
## Tasks
[`⚪ 1 open`](#Tasks) · [`🔵 0 next/wip`](#Tasks#Next) · [`🔴 0 blocked`](#Tasks#Blocked) · [`🟢 12 done/canceled`](#Tasks#Done)
```
When `bob task archive` is executed standalone (outside of `bob nightly`), it extracts the 12 completed tasks from `### Done & Canceled`.  
However, `collect_done` **does not update or recompute the status chips**. The heading continues to display `🟢 12 done/canceled` even though the section below it is now completely empty!  
The counters only become accurate when `bob task-status-hooks` is triggered later.

---

### 3.6 Bug 6: Destruction of Context, Hierarchy, and Temporal Provenance

When tasks are moved into `_done.md`, they are simply concatenated to the end of the file:
```rust
pub(super) fn append_archive_blocks(
    contents: &mut String,
    archive_append: &str,
) {
    if archive_append.is_empty() {
        return;
    }
    if !contents.is_empty() && !contents.ends_with('\n') {
        contents.push('\n');
    }
    contents.push_str(archive_append);
}
```
#### What is lost:
1. **Section Provenance:** If the task was under `### Q3 Milestones > #### Backend API`, that heading structure is completely discarded. The task is appended as a naked bullet.
2. **Indented Child Incoherence:** As seen in `collect_done/transform.rs:completed_child_moves_without_collecting_active_parent`, if a child task completes while its parent is active, the child is moved with its original indentation (`  - [x] child task`). In `_done.md`, this appears as an orphan indented bullet with no parent list item above it.
3. **Temporal Grouping:** Unless the task was stamped with an explicit `[completion:: YYYY-MM-DD]` inline field, there is no delimiter indicating *when* the task was archived. Tasks completed in January 2024 sit adjacent to tasks completed in November 2026 with no separator.

---

### 3.7 Bug 7: The "Double Identity" Tax and Vault-Wide Link Churn

**Recorded Evidence:** Bead `bob-cli-gs` (`periods brief ignores done/ archive paths: archived tasks lose linked minutes and print dead source-note links`).

When a task moves to `done/`, its canonical link target changes:
```
[[sase#^refactor-db]]  ───►  [[done/sase_done#^refactor-db]]
```
This forces `collect_done` to rewrite every daily note, project note, and index referencing that task across the entire Git history.

#### The Bead `bob-cli-gs` Post-Mortem
During weekly period reviews (`bob periods brief`), the brief generator calculated time attribution by matching Pomodoro session links against task identities.  
Because Pomodoro links in older daily notes had been rewritten to `done/sase_done#^...`, but `periods brief` only normalized against the original `sase.md` source path, **archived tasks were credited with 0 minutes of work**. Consequently, major completed accomplishments were excluded from weekly summaries, and dead links were emitted for targets that had been moved.

Having **two distinct file targets** for the same logical task introduces an ongoing cognitive and algorithmic tax across the entire codebase.

---

## 4. Comparative Analysis: How Other Systems Handle Completed Tasks

To evaluate whether there is a better way to approach this problem, we examine how other leading personal productivity and knowledge management systems handle task completion and archiving.

```
┌──────────────────┬──────────────────────┬──────────────────────┬──────────────────────┐
│ System / Tool    │ Archival Location    │ Mechanism            │ Link & Anchor Impact │
├──────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ Bob (Current)    │ done/<stem>_done.md  │ Batch regex CLI      │ Rewrites all links   │
│                  │ (mirror 1:1 files)   │ (threshold: 10)      │ to done/..._done     │
├──────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ Emacs Org-Mode   │ 1. In-file subtree   │ Interactive keystroke│ No link breaks       │
│                  │ 2. Dedicated file    │ or batch lisp        │ (IDs stay intact     │
│                  │ 3. Central datetree  │                      │ via Org-ID)          │
├──────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ Obsidian Plugins │ ## Archive section   │ Automated in-editor  │ Zero link breaks     │
│ (Task Archiver)  │ at bottom of note    │ command on demand    │ (same file URI)      │
├──────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ Things 3         │ Dedicated "Logbook"  │ Immediate or nightly │ Internal database ID │
│                  │ (grouped by date)    │ logbook sweep        │ remains invariant    │
├──────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ Todo.txt         │ Single done.txt      │ `todo.sh archive`    │ N/A (plain text      │
│                  │ (central flat log)   │ CLI command          │ line-based format)   │
├──────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ PARA Framework   │ archive/projects/    │ Whole-container file │ Entire file moves;   │
│ (Tiago Forte)    │ (entire note moves)  │ move when complete   │ Obsidian updates refs│
└──────────────────┴──────────────────────┴──────────────────────┴──────────────────────┘
```

### 4.1 Emacs Org-Mode (`org-archive`)

Org-mode is the direct conceptual ancestor of Bryan's Bob workflow (as evidenced by the `zorg` converter notes in the vault). Org-mode offers three distinct archiving strategies:

1. **In-File Archive Subtree (`:ARCHIVE:` tag):**  
   Pressing `C-c C-x C-a` moves the completed headline to a special `* Archive` headline at the bottom of the *same* file and tags it with `:ARCHIVE:`.  
   *Key Advantages:*
   - **Zero Link Breakage:** The headline retains its internal `:ID:` property. Any link `[[id:uuid]]` or `[[file.org::*Heading]]` remains valid without rewriting.
   - **Folding:** Headlines tagged `:ARCHIVE:` are collapsed by default and excluded from agenda searches, eliminating visual and computational clutter.
2. **Sibling File Archive (`%s_archive::`):**  
   Moves the headline to a sibling file named `filename.org_archive`.
3. **Date-Tree Archive:**  
   Moves completed items into a central `archive.org` file filed under a calendar hierarchy: `* 2026 > ** 2026-11 November > *** 2026-11-09 Monday`.  
   *Key Innovation:* Org-mode automatically annotates archived subtrees with properties recording their origin:
   ```org
   :PROPERTIES:
   :ARCHIVE_TIME: 2026-11-09 Mon 14:30
   :ARCHIVE_FILE: ~/org/projects/website.org
   :ARCHIVE_CATEGORY: website
   :ARCHIVE_TODO: DONE
   :END:
   ```

### 4.2 The Obsidian Community Ecosystem (Task Archiver / Archiver)

In the broader Obsidian community, managing completed tasks is typically handled by plugins like **Task Archiver** (by Ivan Lednev) or **Archiver**:
- **Same-File Archiving:** By default, completed tasks are moved beneath an `## Archive` heading at the end of the active note.
- **Date Partitioning:** Users can configure headings like `## Archive > ### 2026-W45 > #### 2026-11-09`.
- **Preservation of Heading Context:** If an option is toggled, the plugin mirrors the original section hierarchy under the archive heading, ensuring that a task completed under `## Milestones > ### API` is placed under `## Archive > ### Milestones > #### API`.
- **Alternative Destination (Daily Note):** Some users configure the archiver to move completed tasks directly into today's Daily Note under a `### Completed Today` section, creating a live diary of accomplishments without creating any extra files.

### 4.3 Things 3 (Cultured Code)

Things 3 uses a highly regarded two-tier archiving mental model:
1. **The Logbook:** Tasks marked done remain visible in their active project for the remainder of the day (marked with a clean checkmark). At midnight (or upon pressing "Log Completed Tasks"), completed tasks are swept into the **Logbook**.
2. **Temporal Grouping:** The Logbook is organized strictly by completion date:
   - *Today*
   - *Yesterday*
   - *November 7, 2026*
3. **Project Completion vs. Area Maintenance:**
   - **Areas** (e.g., Work, Personal, Finances) are permanent containers. Tasks in areas are logged to the Logbook individually.
   - **Projects** (e.g., "Launch Marketing Campaign") have an explicit completion state. When the project itself is completed, the **entire project container** moves to the Logbook as a single completed entity.

### 4.4 The PARA Method (Tiago Forte)

In the PARA methodology (Projects, Areas, Resources, Archives), containers transition through lifecycle states:
- **Projects:** Have a deadline and a specific definition of done.
- When a project is finished, the user **does not extract tasks from the note**. Instead, the user moves the entire file:
  ```
  projects/Redesign.md  ──►  archive/projects/Redesign.md
  ```
- **Why this is superior for projects:** Extracting completed tasks from an active project note until the project note is an empty husk with 0 tasks is unnatural. A completed project *is* an archive note. Moving the entire note preserves every note, image, diagram, and completed task in its original contextual layout.

---

## 5. Architectural Evaluation & Trade-offs for Bob

Based on this comparative landscape, we evaluate three potential design paths for Bob:

```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│ Design Option                         │ Key Trade-offs                        │
├───────────────────────────────────────┼───────────────────────────────────────┤
│ Option A: Refined Status Quo          │ (+) Zero migration cost; familiar     │
│ (Fix 1:1 done/<stem>_done.md)         │ (-) 31+ extra files; link churn stays │
├───────────────────────────────────────┼───────────────────────────────────────┤
│ Option B: In-Place Archiving          │ (+) Zero link breakage; no file bloat │
│ (## Archive at EOF of source note)    │ (-) Large files grow over multi-years │
├───────────────────────────────────────┼───────────────────────────────────────┤
│ Option C: Hybrid PARA Architecture    │ (+) Natural fit: Projects move whole; │
│ (Whole-Note Projects + Area Archives) │     Areas archive tasks; clean vault  │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

### Option A: Refined Status Quo (1:1 `done/<stem>_done.md` with Critical Bug Fixes)
- **Concept:** Retain the existing `done/<stem>_done.md` file structure, but fix the parsing bugs (`task_block_end`), repair rename tracking via frontmatter, add date headings to `_done.md`, and introduce `bob task restore`.
- **Pros:**
  - 100% backward compatible with existing vault scripts, `stats` indexing, and Dataview queries.
  - Requires no schema changes or massive vault migrations.
  - Keeps active notes small and fast to parse.
- **Cons:**
  - Continues vault file proliferation (one archive note per source note).
  - Continues to rewrite links and cause Git diff churn.

### Option B: In-Place Archiving (`## Archive` within the Same Note)
- **Concept:** Completely eliminate the `done/` directory for individual notes. When `bob task archive` runs, it moves completed tasks to an `## Archive` section at the very bottom of the source file, collapsed under a markdown callout (e.g., `> [!archive]- Completed Tasks`).
- **Pros:**
  - **Permanent Link Stability:** Block anchors never change note paths! `[[sase#^task-1]]` remains valid forever. Zero link rewriting across daily notes.
  - **File Count Halved:** Eliminates 31+ redundant `_done.md` files from the vault.
  - **Full Context Preserved:** Historical tasks remain directly adjacent to the project/area they belong to.
- **Cons:**
  - Active notes for long-running areas (like `sase.md` or `gtd_daily.md`) would grow by thousands of lines (e.g., `gtd_daily.md` would gain 1,084 lines), increasing file read/write latency.
  - Requires updating all regexes and scanners in `bob-cli` to ignore tasks under `## Archive`.

### Option C: The Hybrid PARA Architecture (Recommended Strategic Direction)
- **Concept:** Recognize that **Projects** and **Areas** have fundamentally different lifecycles:
  1. **Finite Projects (`type: "[[project]]"`):**
     - Tasks remain in the project note while the project is active.
     - When the project completes (`- [x] #prj`), the **entire note** moves:
       `projects/MyProject.md` $\rightarrow$ `archive/projects/MyProject.md`.
     - Tasks are never stripped out into a separate `_done.md` file.
  2. **Perpetual Areas & Inboxes (`type: "[[area]]"`, daily notes, inboxes):**
     - Areas never complete, so they do require task offloading.
     - They offload either to `done/<area>_done.md` (with structured date headings) or to a unified monthly archive logbook (e.g., `done/2026/2026-11_archive.md`).
- **Pros:**
  - Solves the sub-threshold problem completely: projects are never shredded into disjoint pieces.
  - Aligns with modern PKM standards (PARA).
  - Drastically limits file proliferation to only the handful of perpetual hubs that truly need it.

---

## 6. Recommended Set of Changes

We recommend a pragmatic, phased roadmap that solves immediate safety bugs first, improves day-to-day ergonomics second, and provides an optional long-term architectural consolidation.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Phase 1: High-Priority Safety & Correctness Fixes (Immediate)                │
├──────────────────────────────────────────────────────────────────────────────┤
│ 1. Guard task_block_end against swallowing open child tasks (- [ ])          │
│ 2. Fix rename fragility: resolve archives via frontmatter (parent/done_tasks)│
│ 3. Add zero-threshold auto-flushing for terminal projects                    │
│ 4. Support unarchiving via `bob task restore` / allow `task move` from done/ │
│ 5. Automatically reconcile status chips immediately after task archive runs  │
├──────────────────────────────────────────────────────────────────────────────┤
│ Phase 2: Structural & Ergonomic Improvements (Short-to-Medium Term)          │
├──────────────────────────────────────────────────────────────────────────────┤
│ 1. Insert date-partitioned headings in _done.md (## Archived YYYY-MM-DD)     │
│ 2. First-class whole-project archiving (`bob project archive <name>`)        │
│ 3. Configurable per-note archive thresholds                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│ Phase 3: Architectural Long-Term Vision (Strategic)                          │
├──────────────────────────────────────────────────────────────────────────────┤
│ 1. Unified link aliasing (canonicalizing task IDs across active & archive)   │
│ 2. Time-partitioned monthly logbooks for high-volume inboxes                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Immediate Safety & Correctness Fixes

#### 1. Guard `task_block_end` Against Swallowing Open Child Tasks
- **Action:** In `src/native/collect_done/transform.rs:task_block_end`, inspect every line in the indented block. If any line matches an open checklist item (`- [ ]`, `- [/]`, `- [?]`), **halt the block extraction immediately** before that line, or refuse to collect the parent task until all child tasks are resolved.
- **Benefit:** Completely eliminates the "zombie task" bug where active subtasks are invisibly moved into `done/`.

#### 2. Robust Frontmatter-Aware Archive Resolution
- **Action:** Update `src/native/collect_done/link_repair.rs:archived_block_targets` and `source_relative_path_from_archive`. Instead of relying solely on string manipulation (`strip_prefix("done")` and `strip_suffix("_done")`), read the archive's `parent: "[[...]]"` frontmatter and verify whether the referenced parent note points back via `done_tasks: "[[...]]"`.
- **Benefit:** If a user renames `projects/Alpha.md` to `projects/Bravo.md`, the system will follow the bi-directional frontmatter links, update the archive's filename accordingly (or bind to the renamed source), and prevent archive file duplication.

#### 3. Zero-Threshold Auto-Flushing for Terminal Projects
- **Action:** In `build_collection_plan`, check if a note is a terminal project (i.e. contains a completed `- [x] #task #prj` line, matching `TargetProjectStatus::Done`). For terminal projects, override `threshold` to `0` (or `1`).
- **Benefit:** When a project is finished, its remaining completed tasks are swept into the archive during the next `bob nightly`, leaving no lingering completed tasks behind in `projects/`.

#### 4. Add `bob task restore` (Unarchive Support)
- **Action:** Lift the strict refusal in `src/native/task_move/plan.rs:500` (`ArchivePath` error). Allow `bob task move` to accept a source under `done/` as long as the destination is an active note. Implement `bob task restore <block-id>` as a dedicated convenience command.
- **Benefit:** Gives Bryan an immediate, safe mechanism to recover accidentally archived tasks, complete with automated reverse link repair.

#### 5. Auto-Reconcile Status Chips Post-Archive
- **Action:** At the end of `collect_done::run_collection`, invoke the status-group reconciler on all touched source notes before committing git changes.
- **Benefit:** Eliminates stale `🟢 N done/canceled` counter chips when `bob task archive` is executed standalone.

---

### Phase 2: Structural & Ergonomic Improvements

#### 1. Date-Partitioned Headings in Archive Notes
- **Action:** In `src/native/collect_done/archive.rs:append_archive_blocks`, format the append payload with a date heading corresponding to the archive date:
  ```markdown
  ## Archived 2026-11-09

  - [x] Refactor database connector #task [completion:: 2026-11-08]
  - [-] Deprecated legacy API #task
  ```
- **Benefit:** Transforms `_done.md` from an unstructured bullet soup into a clear, chronological logbook that is pleasant to browse in Obsidian and easy to navigate with outline tools.

#### 2. First-Class Whole-Project Archiving (`bob project archive`)
- **Action:** Add a subcommand `bob project archive <name>`:
  1. Validates that the project is terminal (`^prj` is checked).
  2. Moves the entire file: `projects/<name>.md` $\rightarrow$ `archive/projects/<name>.md` (or `done/projects/<name>.md`).
  3. If an existing `done/projects/<name>_done.md` exists, merges its historical tasks into the project note's `## Archive` section and deletes the separate `_done.md` file.
  4. Updates Obsidian links across the vault to point to the archived project note.
- **Benefit:** Restores integrity to completed projects, reducing vault clutter and eliminating the unnatural separation of a finished project into two files.

#### 3. Configurable Per-Note Archive Thresholds
- **Action:** Allow notes to specify `archive_threshold: N` (or `archive_threshold: off`) in their YAML frontmatter, overriding the CLI default.
- **Benefit:** High-volume notes (`gtd_daily.md`) can set a threshold of 20, while small milestone trackers can set a threshold of 3.

---

### Phase 3: Architectural Long-Term Vision

#### 1. Canonical Link Target Aliasing
- **Action:** Update the link-resolver infrastructure across `bob-cli` and `bob-plugins` (e.g. `NoteIndex` and `vault_links`) so that `[[note#^task-id]]` and `[[done/note_done#^task-id]]` are recognized as **symmetric aliases for the same task identity**.
- **Benefit:** Downstream review tools (`bob periods brief`), stats calculators, and habit trackers can resolve task minutes and completions regardless of which file currently holds the text, eliminating bugs like `bob-cli-gs` forever.

#### 2. Centralized Monthly Archive for Inboxes
- **Action:** For generic intake notes (`mac_inbox.md`, `gkeep_inbox.md`), route completed tasks into a shared monthly archive `done/inbox/YYYY-MM_done.md` rather than maintaining permanent, multi-thousand-line monolithic inbox archives.

---

## 7. Conclusion

Bryan's current `done/<name>_done.md` system provides essential offloading for active notes, but its implementation has accumulated several brittle assumptions: silent over-collection of child tasks, fragile string-based file path derivation, hardcoded threshold traps for small projects, and lack of restore tooling.

By executing **Phase 1** (fixing `task_block_end`, resilient frontmatter resolution, terminal project auto-flushing, and unarchive support), Bob's done notes can be made **100% bug-free and reliable** without disrupting any existing vault structures. Subsequent adoption of **Phase 2** (date headings and whole-project lifecycle archiving) will make completed task management significantly more **intuitive, structured, and pleasant to use**.
