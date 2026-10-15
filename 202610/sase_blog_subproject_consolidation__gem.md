# SASE Blog Subproject Consolidation: Retiring `sase_blog_0` in Favor of `sase_blog`

**Author:** researcher gem (`research.4k.gem`)  
**Date:** 2026-10-15  
**Target Directory:** `sase/repos/research/202610/`  
**Status:** Complete Independent Analysis

---

## 1. Executive Summary

Bryan's proposal to eliminate the `sase_blog_0` sub-project and consolidate all task, reference, and outline management into the parent `sase_blog` project note is **strongly recommended**.

The original separation in June 2026 was predicated on an assumption that SASE would be introduced via an open-ended multi-part blog series (where `sase_blog` was the series umbrella and `sase_blog_0` was installment zero). In mid-October 2026, the strategic reality has fundamentally shifted: Bryan is now drafting a single, comprehensive retrospective and launch essay—potentially framed as a "goodbye" or lessons-learned reflection on SASE's evolution ("motion isn't progress," cutting prompt debt and AI slop). 

Under this reality, maintaining a two-level project hierarchy ($N = 1$) introduces pure organizational overhead:
1. It inflates Bob's active project roster (currently at 35 active projects).
2. It distorts Bob GTD lifecycle mechanics by keeping `sase_blog`'s completion criteria permanently hidden behind subproject cascade blocking (`decisions:subprojects-inherit-project-blocking`).
3. It creates capture routing ambiguity (`@sase_blog` vs `@sase_blog_0`).
4. It scatters related tasks, requirements, quotes, and outlines across five disparate notes (`sase_blog.md`, `sase_blog_0.md`, `sase_blog_contents.md`, `why_sase.md`, and `sase_blog_0_legacy_notes.md`).

However, a naive merge or deletion will break several critical dependencies in Bryan's live vault:
- **Active Pomodoro Ledger Links:** Bryan's daily note for today (`2026/20261015.md`) currently contains active, in-flight Pomodoro links directly targeting block IDs inside `sase_blog_0.md`.
- **Reference Library Embeds:** Four notes under `ref/` declare `parent: "[[sase_blog_0]]"` and embed specific `sase_blog_0` task block IDs.
- **Done Task Archives:** `done/sase_blog_0_done.md` holds 11 archived tasks and block IDs referenced by external notes.

This report provides a thorough critique of the plan, recommends six essential adjustments to prevent vault breakage and maintain separation between project management and manuscript drafting, and presents an end-to-end migration blueprint.

---

## 2. Forensic Analysis of Current Vault State

### 2.1 The Origin and Intent of the Split
In June 2026, Bryan created `sase_blog.md` under parent `[[sase]]` with completion task:
`- [ ] #task #prj Publish the full sase.sh blog series! [created::2026-06-11] #hide ^prj`

Shortly thereafter (commit on 2026-06-25), Bryan checked off `- [x] #task Convert [[sase_blog_0]] into a project! ^create-prj-0` and created `sase_blog_0.md` with:
`- [ ] #task #prj Post first blog post to https://sase.sh! [created::2026-06-25] #hide [scheduled:: 2026-08-24] ^prj`

The outline in `sase_blog_0.md` (lines 124–135) reveals the original rationale: Post 0 was merely the launch overview, while subsequent posts were planned for Beads/SDD, Memory, Mobile/AXE, Evals, ChangeSpec, and Pluggable Architecture. 

### 2.2 The October 2026 Reality Shift
Over the last four months, SASE underwent explosive growth (reaching 15,756 commits and over 2 million lines of code). On 2026-10-15, Bryan began drafting `sase_blog_contents.md` with a drastically different tone:
> *"Building sase is my attempt to take back some control from this thing that seemed like it was coming for a core part of my identity... Today its repo holds 15,756 commits and over two million lines of Python... motion isn't progress... This post is about the parts that stuck."*

Simultaneously, Bryan added:
- In `sase_blog.md`: `- [ ] #task Re-frame blog post as a "goodbye” to SASE?! [created::2026-10-15]`
- In `sase_blog.md`: `- [*] #task Get rid of [[sase_blog_0]] in favor of [[sase_blog]]! [created::2026-10-14] ^no-more-0-prj`

The blog is no longer an open-ended multi-volume publication campaign. It is a single, definitive essay.

### 2.3 Exhaustive Inventory of Related Files and Linkages

Across the entire vault (`~/bob`), `sase_blog_0` appears in exactly the following locations:

| File Path | Nature of Reference | Risk If Naively Deleted |
|:---|:---|:---|
| `~/bob/2026/20261015.md` (Lines 69–70) | Active Pomodoro ledger links: `[[sase_blog_0#^ref-sase-launch-post-introduction]]`, `[[sase_blog_0#^ref-sase-launch-post-outline]]` | **HIGH**: Breaks today's live Pomodoro ledger; causes `bob plan` lane derivation errors. |
| `~/bob/sase_blog.md` (Lines 9, 18, 22) | `🧩 **Sub-projects:** [[sase_blog_0]]`, active task `^no-more-0-prj`, and historical canceled task `^plan-blog-post` | Medium: Machine-owned Sub-projects line will leave stale strike markers if not handled properly. |
| `~/bob/ref/chat/sase_launch_post_introduction.md` | `parent: "[[sase_blog_0]]"`, transcludes `![[sase_blog_0#^ref-sase-launch-post-introduction]]` | **HIGH**: Breaks reading task transclusion and parent note association in `bob ref doctor`. |
| `~/bob/ref/chat/sase_launch_post_outline.md` | `parent: "[[sase_blog_0]]"`, transcludes `![[sase_blog_0#^ref-sase-launch-post-outline]]` | **HIGH**: Breaks reading task transclusion and parent note association in `bob ref doctor`. |
| `~/bob/ref/blogs/structured_agentic_software_engineering.md` | `parent: "[[sase_blog_0]]"`, transcludes `![[sase_blog_0#^ref-structured-agentic-software-engineering]]` | **HIGH**: Breaks reading task transclusion and parent note association in `bob ref doctor`. |
| `~/bob/ref/chat/databricks_omnigent_job_fit.md` | `parent: "[[sase_blog_0]]"`, transcludes `![[done/sase_blog_0_done#^ref-databricks-omnigent-job-fit]]` | **HIGH**: Breaks archived task embed link. |
| `~/bob/done/sase_blog_0_done.md` | `parent: "[[sase_blog_0]]"`, contains 11 done/canceled tasks | Medium: Archive note orphaned if parent is deleted without re-parenting. |
| `~/bob/why_sase.md` | `parent: "[[sase_blog_0.md\|sase_blog_0]]"` | Low: Prose fragment parent pointer orphaned. |
| `~/bob/sase_blog_0_legacy_notes.md` | `parent: "[[sase_blog_0.md\|sase_blog_0]]"`, notes from June | Low: Legacy notes parent pointer orphaned. |
| `~/bob/sase_blog_blockers.md` | Historical canceled task mentioning `[[sase_blog_0]]` | None: Static prose in a canceled project. |
| `~/bob/sase_post_blog.md` | Project for post-launch features; already links to `[[sase_blog]]` (parent `[[sase]]`) | None: Already points to `sase_blog`! |

---

## 3. Critique of the Proposed Plan

### 3.1 Is Getting Rid of `sase_blog_0` a Good Idea?
**Yes.** The consolidation is architecturally sound and psychologically necessary:

1. **Elimination of Phantom Hierarchy:**
   In GTD and software engineering alike, hierarchy must earn its keep. A sub-project is justified only when a parent project contains multiple concurrent or sequential sub-outcomes that require independent scheduling, distinct completion criteria (`^prj`), or separate task lanes. When the parent project's only active sub-project is the blog post itself, the parent becomes a vacuous shell whose only job is to point to its child.
2. **Harmonizing with Bob GTD Mechanics:**
   Under Bob's project architecture (`docs/projects.md` and `decisions:subprojects-inherit-project-blocking`):
   - An open sub-project forces `#hide` onto the parent's `^prj` task line. `sase_blog`'s completion task cannot surface on the dashboard until `sase_blog_0` is closed.
   - When `sase_blog_0`'s `^prj` is eventually completed, Bob's trigger (c) pull-in offer (`docs/task-dependencies.md` §12.10) surfaces `sase_blog`'s `^prj` as Next. Bryan would then have to immediately close `sase_blog` in an awkward two-step ritual for what was always one accomplishment.
   - Active project count: Bob currently tracks 35 active projects. Merging removes an unnecessary row from `bob projects list`.
3. **Capture and Query Efficiency:**
   In daily use, typing `bob capture ... @sase_blog` versus `@sase_blog_0` introduces micro-friction. Writers should not have to deliberate over which note owns an idea for the same deliverable.
4. **Resolution of Prompt Debt & Mental Alignment:**
   In `sase_blog_0.md`, Bryan noted categories of AI slop: *"Unnecessary backward compatibility; Features that I no longer use or never used; Duplication of functionality and logic."* Keeping `sase_blog_0` when the multi-post series has been abandoned is a classic manifestation of "organizational backward compatibility." Retiring it aligns the tools with the actual mindset.

### 3.2 Evaluation of Alternative Approaches

#### Alternative A: Keep `sase_blog_0` and Delete `sase_blog`
- **Concept:** Promote `sase_blog_0.md` to the top level under `[[sase]]` and delete `sase_blog.md`.
- **Verdict: REJECTED.** The zero-indexed name `sase_blog_0` is an unnatural artifact. It implies the existence of `sase_blog_1`. `sase_blog` is the natural, canonical topic stem. Furthermore, external projects like `sase_post_blog.md` already refer to `[[sase_blog]]`, not `sase_blog_0`.

#### Alternative B: Complete or Cancel `sase_blog_0` in Place Without Merging
- **Concept:** Mark `sase_blog_0`'s `^prj` as canceled `[-]`, leave the file as a terminal project, and copy open tasks to `sase_blog`.
- **Verdict: REJECTED.** Leaving `sase_blog_0.md` in the vault root keeps a ghost file. Under `docs/projects.md`, `sase_blog`'s Sub-projects line would retain `~~[[sase_blog_0]]~~ ❌`, maintaining visible clutter. Moving all content and deleting the file (relying on Git history for archival) is much cleaner.

#### Alternative C: Demote `sase_blog_0` to an Ordinary Non-Project Note
- **Concept:** Remove `type: [[project]]` from `sase_blog_0.md` and keep it as a scratchpad.
- **Verdict: REJECTED.** We already have `sase_blog_contents.md` (the draft) and `why_sase.md` (early notes). Keeping `sase_blog_0` as a third prose file prolongs fragmentation.

---

## 4. Adjustments to Requirements

Bryan's initial prompt was simple: *"I would like to get rid of that sub-project and start managing everything from the sase_blog project note."*

To execute this without breaking the Bob vault or degrading the writing workflow, the following **six adjustments** must be incorporated:

### Adjustment 1: Explicitly Separate Project Management from Manuscript Drafting
- **Issue:** `sase_blog_0.md` suffered from role confusion: it contained GTD tasks, schedule logs, reference embeds, an extensive outline, quotes, and rough draft paragraphs.
- **Adjustment:** Formally delineate two distinct artifacts:
  1. `sase_blog.md`: The **GTD Project Note**. It owns metadata (`parent: "[[sase]]"`), the `^prj` lifecycle task, active tasks, reference reading tasks, requirements/guidelines, and a link to the outline anchor.
  2. `sase_blog_contents.md`: The **Manuscript Note**. Created on 2026-10-15, it contains the actual essay prose and narrative flow. It should NOT be cluttered with GTD checkboxes or priority decay logs.

### Adjustment 2: Protect Active Pomodoro Ledger Links in Today's Daily Note
- **Issue:** `2026/20261015.md` contains active links to `sase_blog_0` block IDs under today's open Pomodoro (`1505-1530 BLOG`):
  ```markdown
  - [ ] (**1505-1530** [t:: 25m]) — BLOG
  	- [[sase_blog_0#^ref-sase-launch-post-introduction]]
  	- [[sase_blog_0#^ref-sase-launch-post-outline]]
  	- [[sase_blog#^no-more-0-prj]]
  ```
- **Adjustment:** When tasks are moved from `sase_blog_0.md` into `sase_blog.md`, the block IDs must be preserved identically (`^ref-sase-launch-post-introduction`, `^ref-sase-launch-post-outline`), and lines 69–70 of `2026/20261015.md` must be updated immediately to point to `sase_blog#...`. Otherwise, `bob plan` will report broken links and lane derivation will fail.

### Adjustment 3: Synchronize Reference Library Embeds and Frontmatter
- **Issue:** In Bob's reference system (`docs/ref.md`), reference notes in `ref/` embed parent task block IDs and declare `parent: "[[sase_blog_0]]"`.
- **Adjustment:** Update the frontmatter `parent:` and embed wikilinks in:
  - `ref/blogs/structured_agentic_software_engineering.md`
  - `ref/chat/sase_launch_post_introduction.md`
  - `ref/chat/sase_launch_post_outline.md`
  - `ref/chat/databricks_omnigent_job_fit.md`
  Afterward, verify with `bob ref doctor`.

### Adjustment 4: Configure Aliases for Backward Compatibility
- **Issue:** External links, shell habits, or muscle memory may still target `sase_blog_0`.
- **Adjustment:** Add both Obsidian and Bob aliases to `sase_blog.md`:
  ```yaml
  aliases: ["sase_blog_0"]
  project_name_aliases: ["sase_blog_0"]
  ```
  `project_name_aliases` ensures that `bob capture ... @sase_blog_0` and `bob ref create -P sase_blog_0` seamlessly route to `sase_blog.md`.

### Adjustment 5: Consolidate the Done Archive
- **Issue:** `sase_blog_0` has an archive file `done/sase_blog_0_done.md` with 11 completed tasks. `sase_blog.md` currently has 4 done tasks inlined and no `done_tasks:` property.
- **Adjustment:** Rename `done/sase_blog_0_done.md` to `done/sase_blog_done.md`, update its frontmatter to `parent: "[[sase_blog]]"`, configure `done_tasks: "[[done/sase_blog_done]]"` in `sase_blog.md`, and move `sase_blog`'s inline done tasks into it during the next `bob task archive` run.

### Adjustment 6: Preserve Boundary with `sase_post_blog.md`
- **Issue:** There is a third related project, `sase_post_blog.md` ("Plan features to launch after [[sase_blog]] post!").
- **Adjustment:** Confirm that `sase_post_blog.md` is NOT part of this consolidation. It is a sibling software project under `[[sase]]` for post-launch features. It already links to `[[sase_blog]]` and requires no modification.

---

## 5. Recommended Solution: Step-by-Step Blueprint

### Phase 1: Prepare the Consolidated `sase_blog.md`
Construct `~/bob/sase_blog.md` to house all active tasks, reference tasks, consolidated requirements, and the outline:

```markdown
---
parent: "[[sase]]"
type: "[[project]]"
status: wip
aliases: ["sase_blog_0"]
project_name_aliases: ["sase_blog_0"]
done_tasks: "[[done/sase_blog_done]]"
---
- [ ] #task #prj Publish the sase.sh blog post! [fresh:: 2026-10-15] [created::2026-06-11] #hide ^prj

## Tasks
[`⚪ 3 open`](#Tasks) · [`🔵 2 next/wip`](#Tasks#Next%20&%20In%20Progress) · [`🔴 3 blocked`](#Tasks#Blocked) · [`🟢 5 done/canceled`](#Tasks#Done%20&%20Canceled)

- [ ] #task Re-frame blog post as a "goodbye” to SASE?! [created::2026-10-15]
- [ ] #task #ref [[ref/blogs/structured_agentic_software_engineering|SASE: Structured Agentic Software Engineering¶]] [fresh:: 2026-10-15] [created::2026-10-14] ^ref-structured-agentic-software-engineering

### Next & In Progress

- [/] #task #ref [[ref/chat/sase_launch_post_introduction|The First Paragraphs of the First SASE Blog Post]] [fresh:: 2026-10-08] [id:: sase_blog__ref-sase-launch-post-introduction] [created::2026-10-07] ^ref-sase-launch-post-introduction
	- 🧱 **BLOCKS:** [[#^intro-proposal]]
- [/] #task #ref [[ref/chat/sase_launch_post_outline|The First SASE Blog Post: A Recommended Outline]] [fresh:: 2026-10-08] [id:: sase_blog__ref-sase-launch-post-outline] [created::2026-10-07] ^ref-sase-launch-post-outline
	- 🧱 **BLOCKS:** [[#^intro-proposal]]

### Blocked

- [?] #task Launch agent to create ~/bob/zk/ notes for blog post! [fresh:: 2026-10-13] [created::2026-08-16] [priority:: high] [scheduled:: 2026-10-17] ^zk
	- Have this agent go through all existing blog notes.
	- Create tasks in a new project note file for each proposed ~/bob/zk/ note.
	- Add a great sase_blog.base file that you link to from this project note file.
	- Create key architecture principles as ~/bob/zk/ zettel! [created::2026-09-07]
	- 🗓️ **SCHEDULE LOG**
		- *2026-08-25 → 2026-10-17* — 🎲 P0 → P1 · in **4** (2–7) days
- [?] #task Gather a list of references for blog post! [fresh:: 2026-10-12] [created::2026-07-28] [priority:: high] [scheduled:: 2026-10-16]
	- REF: [[lib/blogs/harness_for_rsi|harness_for_rsi]]
	- 🗓️ **SCHEDULE LOG**
		- *2026-10-12 → 2026-10-16* — 🎲 P1 roll · in **4** (2–7) days
		- *2026-10-10 → 2026-10-12* — 🎲 P1 · in **2** (2–7) days
- [?] #task Review [[lib/chat/sase_launch_post_outline]] and [[lib/chat/sase_launch_post_introduction]] + launch another research swarm to act on notes and perform another round of polishing! [fresh:: 2026-10-08] [created::2026-10-07] [dependsOn:: sase_blog__ref-sase-launch-post-introduction, sase_blog__ref-sase-launch-post-outline] ^intro-proposal
	- ⛓️ **DEPENDS ON:** [[#^ref-sase-launch-post-introduction]] • [[#^ref-sase-launch-post-outline]]

### Done & Canceled

- [x] #task Get rid of [[sase_blog_0]] in favor of [[sase_blog]]! [created::2026-10-14] [completion:: 2026-10-15] ^no-more-0-prj
- [-] #task Plan first blog post ([[sase_blog]] -> [[sase_blog_0]])! [created:: 2026-06-05] [cancelled:: 2026-06-13] ^plan-blog-post
- [x] #task Move some [[sase]] tasks to [[sase_blog]]! [created:: 2026-06-07] [completion:: 2026-06-07]
- [x] #task Do a WisprFlow brain-dump on what the first blog post should contain! [created:: 2026-06-11] [completion:: 2026-06-14]
- [x] #task Convert [[șase_blog_0]] into a project! [created::2026-06-24] [completion:: 2026-06-25] ^create-prj-0

## Drafts & Content
- Main Draft: [[sase_blog_contents]]
- Early Notes & Quotes: [[why_sase]]
- Obsolete Early Outlines: [[sase_blog_0_legacy_notes]]

## Requirements & Ideas
- **Core Narrative:**
  - Sase does not claim optimal performance, but optimal experience! [created::2026-07-16]
  - Motion isn't progress: sase grew from a 98-line script to 15,756 commits.
  - Break down gastown differences (beads vs rigs, no mayor).
  - List of limitations; agents tab buggiest part of TUI.
  - Mention loop engineering and graph engineering.
  - If building from scratch today, implement skills as procedural memory.
- **AI Slop & Prompt Debt:**
  - Unnecessary backward compatibility.
  - Features no longer used or never used.
  - Duplication of functionality and logic.
  - Accumulated degradation in alignment ("prompt debt").
- **Media & Visuals:**
  - Use custom halo and devil emojis / stick figure art!
  - Screenshots: Claude outage retries (`~/tmp/screenshots/20260616_140429.png`), `%wait` utility, questions/retries/tales (`~/tmp/screenshots/20260624_074728.png`).

## Outline
^outline
- **Introduction:** Boris method -> tmux_ai_window -> auto-approve plans -> wait / fork. Timeline of SE transformation.
- **Overview:** From `gai` (98-line LangGraph) to 2M LoC. Motion vs. progress.
- **XPrompts:** Editor tooling (sase-nvim LSP vs PIW), Directives, Alternations, Workflows (Multi-Prompt & YAML), `#fork`.
- **ACE:** Focus on Agent Tab, Families, Hoods, PRs tab, Notifications.
- **AXE:** Touch on sase-telegram and mobile supervising.
- **Retrospective / Lessons:** What stuck, what failed, prompt debt, and the future.
```

### Phase 2: Consolidate Archive and Done Tasks
1. Rename `~/bob/done/sase_blog_0_done.md` to `~/bob/done/sase_blog_done.md`.
2. In `~/bob/done/sase_blog_done.md`:
   - Change line 2 to: `parent: "[[sase_blog]]"`.
   - Update internal block references if any.
3. In `~/bob/ref/chat/databricks_omnigent_job_fit.md`:
   - Update transclusion line 20 from `![[done/sase_blog_0_done#^ref-databricks-omnigent-job-fit]]` to `![[done/sase_blog_done#^ref-databricks-omnigent-job-fit]]`.
   - Update `parent:` to `[[sase_blog]]` (or `[[job_2026]]`).

### Phase 3: Update Reference Notes in `ref/`
Update the three active reading references:
1. `ref/blogs/structured_agentic_software_engineering.md`:
   - Set `parent: "[[sase_blog]]"`
   - Set embed: `![[sase_blog#^ref-structured-agentic-software-engineering]]`
2. `ref/chat/sase_launch_post_introduction.md`:
   - Set `parent: "[[sase_blog]]"`
   - Set embed: `![[sase_blog#^ref-sase-launch-post-introduction]]`
3. `ref/chat/sase_launch_post_outline.md`:
   - Set `parent: "[[sase_blog]]"`
   - Set embed: `![[sase_blog#^ref-sase-launch-post-outline]]`

### Phase 4: Update Today's Daily Note (`2026/20261015.md`)
Update lines 69–71 in `~/bob/2026/20261015.md`:
```markdown
- [ ] (**1505-1530** [t:: 25m]) — BLOG
	- [[sase_blog#^ref-sase-launch-post-introduction]]
	- [[sase_blog#^ref-sase-launch-post-outline]]
	- [[sase_blog#^no-more-0-prj]]
```

### Phase 5: Update Supporting Draft Notes
1. `~/bob/why_sase.md`:
   - Set `parent: "[[sase_blog]]"`
2. `~/bob/sase_blog_0_legacy_notes.md`:
   - Set `parent: "[[sase_blog]]"`
3. `~/bob/sase_blog_contents.md`:
   - Verify `parent: "[[sase_blog]]"` (already in place).

### Phase 6: Retire `sase_blog_0.md`
Remove `~/bob/sase_blog_0.md` from the vault:
```bash
git -C ~/bob rm sase_blog_0.md
```
Because `aliases: ["sase_blog_0"]` and `project_name_aliases: ["sase_blog_0"]` are defined in `sase_blog.md`, any residual links or capture targets automatically resolve to `sase_blog.md`. Deleting the physical file ensures Obsidian does not resolve links to a stale file.

### Phase 7: Verification Protocol
Run Bob's standard test suite against the live vault:
```bash
# 1. Verify project list: sase_blog_0 should be gone; sase_blog active with 1 ^prj
bob projects list

# 2. Preview and apply project sync (reconciles hide tags and removes subprojects marker)
bob projects sync --dry-run
bob projects sync

# 3. Check today's plan budget and lanes (verifies no broken ledger links)
bob plan

# 4. Verify reference library integrity
bob ref doctor

# 5. Reconcile task dependencies
bob task reconcile --dry-run
```

---

## 6. Conclusion and Next Steps

Consolidating `sase_blog_0` into `sase_blog` is an overdue correction of premature structure. It eliminates a ghost project, removes cascade blocking friction, consolidates five fragmented notes into a clean "Project Note vs. Manuscript" dichotomy, and matches the reality of Bryan's writing focus.

By following the phased blueprint above, Bryan can complete this refactor cleanly during a single Pomodoro without risking broken ledger links, orphaned reference tasks, or corrupted dependency graphs.
