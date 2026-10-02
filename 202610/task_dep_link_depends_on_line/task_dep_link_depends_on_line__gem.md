# Research Report: Single-Line Task Dependency Links in Obsidian

**Author:** researcher gem (`research.3f.gem`)  
**Date:** 2026-10-02  
**Target:** `bob-cli`, `bob-plugins` (`bob-navigation-hotkeys`, `task-status-cycler`), and Obsidian Vault  
**Artifact Ref:** `research:202610/single_line_task_dependency_links__gem.md`  

---

## Executive Summary

This research investigates the redesign of Obsidian task dependency tracking across the Bob ecosystem. Specifically, it addresses transitioning away from per-dependency transcluded sub-bullets (`- ![[note#^id]]`) toward a unified, single-line presentation using standard task links, backed by a vault-wide task picker integrated into the `<ctrl+shift+p>` hotkey flow.

### Key Conclusions & Recommendations
1. **The move away from transcluded links is strongly justified.** The July 2026 experiment with transcluded sub-bullets introduced severe layout degradation in Obsidian Live Preview (clunky embedded cards, viewport jumping, broken strikethrough styling) and disrupted Vim-mode navigation. Normal wikilinks (`[[note#^id|alias]]`) restore visual cleanliness, support inline strikethrough (`~~[[...]]~~`) on completion, and preserve fast editor performance.
2. **Single-line consolidated representation is the optimal format.** Consolidating dependencies onto a single managed child bullet (`- 🔗 **DEPENDS ON:** [[target#^id|Title]] • [[target2#^id2|Title 2]]`) keeps complex tasks vertically compact (2 lines total) while maintaining clean visual distinction from arbitrary notes or subtasks.
3. **The Dual-Layer Architecture must be preserved.** The machine-readable inline field `[dependsOn:: id1, id2]` on the parent task line must remain the semantic source of truth for Obsidian Tasks, Dataview queries, and `bob task-status-hooks` derived blocked status. The single-line child bullet serves as the human-facing navigation, hover-preview, and Pomodoro graph-traversal layer.
4. **`<ctrl+shift+p>` should be expanded from local-only to vault-wide Area & Project search.** Currently, `BulletPropertyPickerModal` for `dependsOn` only scans open tasks in the active buffer. Expanding this stage to fuzzy-search across all notes carrying `type: [[area]]` or `type: [[project]]` solves the user's primary workflow friction. With in-memory metadata caching, vault-wide search remains sub-10ms fast.
5. **New Glossary Term:** A new strand, `task_dependency_link.md`, should be added to the SASE `glossary` memory web, and `glossary:task-link` should be updated to retire its legacy reference to transcluded task links.

---

## 1. Historical Evolution & Why Transclusions Failed

### 1.1 The Pre-July 2026 Baseline
Prior to July 2026, `bob-navigation-hotkeys` managed dependencies using a single child bullet with multiple block links separated by bullet dots (`•`):
```markdown
- [ ] #task Launch project beta [dependsOn:: api, frontend] ^launch
  - 🔗 **DEPENDS ON:** [[#^api]] • [[#^frontend]]
```
At that time, links were primarily intra-file or hand-authored, and the label had just migrated from `**DEPENDENCIES:**` to `**DEPENDS ON:**` (commit `b57a0bc`, `d33c4a6`).

### 1.2 The July 2026 Transclusion Experiment
In July 2026, plan `plan:202607/transcluded_task_deps.md` (implemented in commit `982ac8b`) migrated the vault from the single `DEPENDS ON` bullet to individual transcluded sub-bullets:
```markdown
- [ ] #task Launch project beta [dependsOn:: api, frontend] ^launch
  - ![[#^api]]
  - ![[#^frontend]]
```
The intention was to render the full text and checkbox of each prerequisite task directly beneath the dependent task without having to click or navigate.

### 1.3 Real-World Failure Modes of Transclusions
In day-to-day use, this model revealed major friction points:

1. **Visual Sprawl & Heavy Card Layouts in Live Preview:**  
   Obsidian renders block transclusions (`![[...#^...]]`) as heavy embedded widgets with outer borders, padding, and distinct background cards. A task with four dependencies expanded into a towering, multi-card hierarchy that broke the visual rhythm of clean GTD checklists.
2. **Interactive Ambiguity & Checkbox Quirks:**  
   In Obsidian Live Preview, the embedded task card renders an active checkbox. However, interacting with embedded checkboxes from within another note often fails to invoke the proper status hooks, task-status cyclers, or date stamps because the event context is the embed wrapper, not the source file.
3. **Broken Strikethrough for Terminal / Completed Dependencies:**  
   Markdown strikethrough (`~~...~~`) does not work on embedded widgets. When a transcluded dependency was completed, it could not be struck out cleanly (`~~![[...]]~~` is invalid or renders as broken text). `bob-navigation-hotkeys` had to resort to an awkward hybrid where struck items had their exclamation marks stripped (`~~[[...]]~~`), causing inconsistent rendering between live and completed dependencies.
4. **Vim Navigation and Viewport Hopping:**  
   Because CodeMirror 6 embeds are asynchronous DOM widgets, navigating across transcluded bullets in Vim normal mode caused cursor position snapping, line-height miscalculations, and viewport jumping (necessitating patches `30ae7b9` and `5337f45`).
5. **Pollution of Dataview / Tasks Queries:**  
   Transcluded task lines are often picked up twice by simple Dataview queries (once in the source note, and once inside the embedding note's AST), requiring complex query filters.

**Conclusion:** Moving back to normal (non-transcluded) task links eliminates all four engine-level bugs while drastically improving UI performance and readability.

---

## 2. Critique of the Proposed Plan

### 2.1 Is This a Good Idea?
**Yes, unequivocally.** The plan addresses genuine ergonomic pain points while aligning with the strengths of Obsidian's link graph and Bob's established interface grammar.

| Proposal Aspect | Evaluation | Verdict |
| :--- | :--- | :--- |
| **Drop transcluded task links** | Eliminates visual bloat, Vim jumping, and strikethrough rendering bugs. | **Strongly Endorsed** |
| **Single-line consolidated list** | Restores compact 2-line footprint per dependent task; highly scannable. | **Strongly Endorsed** |
| **`<ctrl+shift+p>` vault-wide search** | Eliminates tedious manual block-ID lookups and cross-file copying. | **Strongly Endorsed** |
| **New Glossary Web term** | Codifies "Task Dependency Link" as distinct from generic Task Links. | **Strongly Endorsed** |

### 2.2 Critical Nuances & Adjustments

While the user's direction is sound, several critical technical adjustments are necessary to prevent regressions:

#### Adjustment 1: Wikilink Aliases Are Mandatory for Aesthetics
If a single-line bullet contains bare links like `[[Projects/Apollo#^api]] • [[Areas/Finance#^tax]]`, Obsidian renders them as:
`Projects/Apollo > ^api • Areas/Finance > ^tax`
This is technical and visually jarring.  
**Required Adjustment:** When the `<ctrl+shift+p>` picker writes a task link, it must automatically append a clean display alias derived from the target task's text:
`[[Projects/Apollo#^api|Deliver Backend API]] • [[Areas/Finance#^tax|File Q3 Taxes]]`  
In Obsidian Live Preview and Reading View, this renders cleanly as clickable text pills:
**Deliver Backend API** • **File Q3 Taxes**. Hovering over any link opens the core Obsidian Page Preview popover showing the complete live task in its original context.

#### Adjustment 2: Maintain Dual State (`[dependsOn:: ...]` + `DEPENDS ON:` bullet)
One might wonder: *can we drop `[dependsOn:: ...]` entirely and parse only the `DEPENDS ON:` bullet?*  
**No.**  
- The Obsidian Tasks plugin strictly parses inline Dataview fields (`[dependsOn:: id]`) to evaluate task dependencies and block statuses in standard Tasks queries.
- `bob task-status-hooks` relies on `[dependsOn:: id]` for its fast, vault-wide indexed blocker check.
- `[dependsOn:: ...]` remains the machine semantic record; the child bullet is the human navigation and link-graph layer. The plugin must maintain strict bidirectional synchronization between them.

#### Adjustment 3: Scoped Vault Search (Areas & Projects, Not Everything)
Searching *every* markdown file in a vault on every keystroke in `<ctrl+shift+p>` can lead to UI stutter, especially if the vault contains thousands of archived notes, daily logs, or reference documents.  
**Required Adjustment:** Scope default task search to active Area and Project notes (`type: [[area]]` or `type: [[project]]`), plus the active file. Completed tasks (`[x]`, `[-]`) and archived tasks in `done/` should be filtered out from candidate selection by default.

---

## 3. Recommended Visual Design & Syntax

### 3.1 The Canonical Markdown Representation

The recommended format builds directly upon Bob's established managed-bullet design language (matching `🗓️ **SCHEDULE LOG:**` and `⏱️ **WORK LOG:**`):

```markdown
- [?] #task Ship bob-cli v2.0 [dependsOn:: Apollo__api, ux-review] ^ship-cli
  - 🔗 **DEPENDS ON:** [[Projects/Apollo#^api|Deliver Backend API]] • [[#^ux-review|Conduct UX Review]]
```

#### Syntax Breakdown
1. **Indentation:** Exactly mirrors the parent task's indentation plus one tab (or local space convention, e.g. 2 spaces or 4 spaces).
2. **List Marker:** Standard list bullet `- ` matching the note's prevailing style.
3. **Emoji & Label Anchor:** `🔗 **DEPENDS ON:** `
   - The link emoji (`🔗`) provides an immediate visual cue in both source mode and live preview.
   - Bold uppercase `**DEPENDS ON:**` matches the exact conventions of `🗓️ **SCHEDULE LOG:**` and `⏱️ **WORK LOG:**`.
4. **Target Links:**
   - **Cross-file target:** `[[Path/Note#^block-id|Clean Task Title]]`
   - **Same-file target:** `[[#^block-id|Clean Task Title]]`
5. **Link Delimiter:** ` • ` (bullet with surrounding single spaces).
6. **Alias Sanitation:** The target task's text is stripped of tags (`#task`), existing property brackets (`[scheduled:: ...]`, `[priority:: ...]`), block IDs (`^...`), and truncated to a sensible length (maximum 40 characters followed by `…` if longer) to avoid unwieldy lines.

### 3.2 Visual Lifecycle: Active, Partial, and Resolved Dependencies

#### State 1: All Dependencies Open (Parent is Blocked `[?]`)
```markdown
- [?] #task Deploy landing page [dependsOn:: copy, graphics] ^landing
  - 🔗 **DEPENDS ON:** [[#^copy|Finalize sales copy]] • [[Projects/Design#^graphics|Export hero SVG]]
```

#### State 2: Partial Completion (One Prerequisite Done)
When a dependency task is completed, its link in the child bullet is struck through (`~~...~~`):
```markdown
- [?] #task Deploy landing page [dependsOn:: graphics] ^landing
  - 🔗 **DEPENDS ON:** ~~[[#^copy|Finalize sales copy]]~~ • [[Projects/Design#^graphics|Export hero SVG]]
```
*Visual Effect in Obsidian:* The completed dependency link renders with a clean strikethrough line over the link text, providing immediate situational awareness that sales copy is done while graphics remain pending.

#### State 3: All Dependencies Resolved (Parent Unblocked to Ready `[ ]`)
When the final dependency is completed, `task-status-cycler` and `bob task-status-hooks` unblock the parent task. The child bullet either displays all struck links or is cleanly retired upon vault cleanup:
```markdown
- [ ] #task Deploy landing page ^landing
  - 🔗 **DEPENDS ON:** ~~[[#^copy|Finalize sales copy]]~~ • ~~[[Projects/Design#^graphics|Export hero SVG]]~~
```

---

## 4. Interaction Design: `<ctrl+shift+p>` with Vault-Wide Search

### 4.1 Entry Point & Property Stage
1. User positions the cursor on any task line and presses `<ctrl+shift+p>`.
2. The property modal opens showing standard properties (`scheduled`, `priority`, `dependsOn`, `lane`, `cancel`).
3. User selects `dependsOn` (or types `dep` and presses Enter).

### 4.2 The Vault-Wide Task Selection Stage
The picker transitions into the task dependency selection stage:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 🔗 dependsOn                                                          │
│ [ Filter tasks across vault (type task or project)...                ] │
├────────────────────────────────────────────────────────────────────────┤
│ Showing 3 of 42 open tasks across 8 notes                              │
├────────────────────────────────────────────────────────────────────────┤
│  ✓  Deliver Backend API                                  [x] LINKED    │
│     Projects/Apollo.md · line 42 · ^api                                │
│                                                                        │
│  ○  Conduct UX Review                                   ↵ ADD LINK     │
│     Projects/Apollo.md · line 58 · (needs block ID)                    │
│                                                                        │
│  ○  Export hero SVG                                     ↵ ADD LINK     │
│     Projects/Design.md · line 19 · ^graphics                           │
│                                                                        │
│  ○  Order server hardware                               ↵ ADD LINK     │
│     Areas/Infra.md · line 84 · ^hardware                               │
├────────────────────────────────────────────────────────────────────────┤
│ ⇥ Mark batch   ↵ Apply   esc Cancel   ↑/↓ Navigate                     │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Key UX Capabilities
1. **Fuzzy Search Across Both Content and Note Name:**
   - Query: `apollo api` → instantly matches `Deliver Backend API` in `Projects/Apollo.md`.
   - Query: `infra hard` → instantly matches `Order server hardware` in `Areas/Infra.md`.
2. **Current Dependencies Pinned at Top:**
   - Any task already present in the parent's `[dependsOn:: ...]` field is displayed at the top with a checked icon (`✓`) and a `[x] LINKED` badge.
   - Selecting an already-linked item unlinks it (removes from `[dependsOn::]` and removes from the bullet).
3. **Multi-Selection (Batch Marking with Tab):**
   - Pressing `Tab` marks/unmarks items without closing the modal.
   - Pressing `Enter` with multiple marked items applies all additions and removals in a single atomic transaction.
4. **Automated Target Block-ID Generation:**
   - If a selected target task does not have a trailing `^block-id`, the modal seamlessly prompts for or auto-assigns an intuitive slug based on the task description (e.g. `^conduct-ux-review`), updates the remote target file using `app.vault.process`, and completes the link without requiring the user to open the target note.

---

## 5. Glossary Web Term Specification

A new memory strand should be created at `sase/memory/glossary/task_dependency_link.md`:

```markdown
# Task Dependency Link

*Requested · project*

aka task dep link, dependency task link

A normal (non-transcluded) block link to an Obsidian task (`[[note#^block-id]]` or `[[#^block-id]]`, formatted with an optional display alias `|alias`) used to record that the target task is a prerequisite dependency of the containing or parent task.

Task dependency links are listed together on a single managed child bullet formatted as `- 🔗 **DEPENDS ON:** [[...]] • [[...]]` beneath the dependent task, synchronized with the machine-readable `[dependsOn:: ...]` inline metadata on the parent task. Completed dependencies are formatted with strikethrough as `~~[[...]]~~`.

When a task is linked under today's open Pomodoros, `bob task-status-hooks` traverses its task dependency links to promote those prerequisites to Next (`[*]`). Removing all dependency links removes the child bullet and clears the `[dependsOn:: ...]` metadata.
```

### Updates to Related Terms
- **`glossary:task-link`:** Remove the sentence:
  *"As another special case, transcluded task links that are the only contents of a sub-bullet on another Obsidian task are treated as sub-tasks (i.e. dependencies) of that task."*
  Replace with a reference to `[[glossary:task-dependency-link]]`.

---

## 6. Technical Implementation Architecture

### 6.1 `bob-plugins` (`plugins/bob-navigation-hotkeys/main.js`)

1. **Regex & Bullet Constants:**
   Replace the transclusion-based regex with the single-line parser:
   ```javascript
   const DEPENDENCY_NAVIGATION_LABEL = "DEPENDS ON";
   const DEPENDENCY_NAVIGATION_EMOJI = "🔗";
   const DEPENDENCY_NAVIGATION_SEPARATOR = " • ";

   const DEPENDENCY_NAVIGATION_BULLET_RE = new RegExp(
     `^(?<indent>\\s*(?:>\\s*)*)(?<marker>(?:[-*+]|\\d+[.)]))[ \\t]+` +
     `(?<emoji>${DEPENDENCY_NAVIGATION_EMOJI}[ \\t]+)?\\*\\*${DEPENDENCY_NAVIGATION_LABEL}:\\*\\*` +
     `[ \\t]+(?<linkSpan>.*)$`
   );

   const DEPENDENCY_LINK_RE = /(?<strike>~~)?\[\[(?<note>[^\]|#]*?)#\^(?<blockId>[A-Za-z0-9-]+)(?:\|(?<alias>[^\]\n]*))?\]\]\k<strike>?/g;
   ```

2. **Vault-Wide Task Indexing (`VaultTaskIndex`):**
   Implement an in-memory index of tasks residing in Area and Project notes:
   ```javascript
   function getOpenVaultTasks(app) {
     const files = app.vault.getMarkdownFiles().filter(file => {
       const cache = app.metadataCache.getFileCache(file);
       const type = cache?.frontmatter?.type;
       return type === "[[area]]" || type === "[[project]]";
     });
     // Extract open tasks from each file, caching by file path and mtime
     ...
   }
   ```

3. **Link Synchronization Plan (`planDependencyNavigationBulletSync`):**
   - Computes target additions, removals, and strikethroughs.
   - Generates the single consolidated bullet string using `formatDependencyNavigationBullet(targets, indent)`.
   - Replaces the existing line if a `DEPENDS ON:` bullet already exists; inserts beneath the parent task if none exists; deletes the line if all dependencies are removed.

### 6.2 `bob-plugins` (`plugins/task-status-cycler/main.js`)

When a task status is cycled to Done (`[x]`) or Cancelled (`[-]`):
- `recoverBlockedDependentsNow` already unblocks dependent tasks.
- Add hook to update the parent's `🔗 **DEPENDS ON:**` bullet to wrap the completed task's link in `~~...~~`.

### 6.3 `bob-cli` (`src/native/task_status_hooks/references.rs` & `sync.rs`)

1. **Update `dependency_edges` Parser:**
   In `src/native/task_status_hooks/references.rs`, replace `sole_transcluded_block_reference` with a parser that reads the single-line `DEPENDS ON:` bullet:
   ```rust
   pub(super) fn dependency_bullet_references(line: &str) -> Vec<RawReference> {
       // Check if line matches `- 🔗 **DEPENDS ON:** ...`
       // Extract all non-struck [[note#^block_id|alias]] wikilinks
       // Return Vec<RawReference> for active dependency edges
   }
   ```
2. **Struck Link Exclusion:**
   Ensure links wrapped in `~~...~~` are ignored when constructing `dependency_edges` so that completed prerequisites do not falsely seed Next promotions.
3. **Backward Compatibility:**
   During migration, allow `dependency_edges` to accept both the single-line format and legacy `![[...]]` bullets.

---

## 7. Migration Plan for Existing Vault Data

An automated migration script (`scripts/migrate-task-dependency-links.mjs` in `bob-plugins`) should execute the following idempotent steps:
1. Scan all markdown files in the vault (`~/bob/`).
2. Identify tasks carrying `[dependsOn:: ...]` that currently have child sub-bullets with `![[...#^...]]`.
3. Resolve each dependency target to obtain its clean title for the alias.
4. Replace the multiple transcluded child bullets with one consolidated `  - 🔗 **DEPENDS ON:** [[...|...]] • ...` bullet.
5. If the target task is already done (`[x]`), format with strikethrough: `~~[[...|...]]~~`.
6. Run with `--dry-run` first, inspect diffs, and then apply with `--write`.

---

## 8. Summary of Benefits

1. **Aesthetic Excellence:** Clean, scannable, single-line presentation that harmonizes with Bob's existing log bullets (`🗓️`, `⏱️`).
2. **Editor Performance:** Eliminates heavy Live Preview embeds and eliminates Vim normal-mode navigation glitches.
3. **Workflow Friction Removed:** Vault-wide Area and Project fuzzy searching directly inside `<ctrl+shift+p>` makes cross-project dependency linking effortless.
4. **Reliable Tooling Integration:** Preserves strict compatibility with Obsidian Tasks, Dataview, `task-status-hooks`, and `task-status-cycler`.
