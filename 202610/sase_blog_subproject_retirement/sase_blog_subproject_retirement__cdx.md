# Consolidating SASE blog planning into one project

Researcher: cdx  
Date: 2026-10-15  
Scope: independent research and recommendation; no vault content was changed. No other swarm researcher's report, transcript, summary, or findings were consulted.

## Assessment

Consolidating `sase_blog_0` into `sase_blog` is a good idea for the work currently represented in the vault. The parent and child now describe essentially the same publication outcome at different levels of specificity. Maintaining two project lifecycles adds routing, review, and linking work without an evident second deliverable.

The more important correction is to change the parent's completion criteria. Its current promise is a **full blog series**. Removing the child while retaining that promise would simplify the files but preserve the original scope problem. Make the parent represent publishing the one SASE article that Bryan currently intends to write; additional posts can remain possibilities.

I would perform a deliberate merge, preserving task identities and supporting notes. I would not use the project-to-task conversion shortcut as the primary approach, mark an unpublished article complete, or combine every related document into a single Markdown file.

## What the live vault shows

Read-only `bob query` inspections returned the following. Line numbers below are one-based; native query results are zero-based. Observations are a working snapshot, not a guarantee that the vault will remain unchanged before implementation.

| Note | Current role | Relevant state |
| --- | --- | --- |
| `sase_blog.md` | Active project, parent `[[sase]]` | `^prj`: “Publish the full sase.sh blog series!”; generated Sub-projects line names `sase_blog_0` |
| `sase_blog_0.md` | Active project, parent `[[sase_blog]]` | `^prj`: “Post first blog post to https://sase.sh!”; inline schedule `2026-08-24` and a Schedule Log |
| `why_sase.md` | Supporting note, parent `[[sase_blog_0]]` | Description identifies it as the contents of the first blog post; linked from the child's Contents section |
| `sase_blog_0_legacy_notes.md` | Supporting note, parent `[[sase_blog_0]]` | Preserve and reparent; its body was not assessed |
| `done/sase_blog_0_done.md` | Existing archive, parent `[[sase_blog_0]]` | Referenced by the child's `done_tasks` property and historical daily notes |
| `sase_blog_contents.md` | Note already parented to `[[sase_blog]]`, with no project type in the returned metadata | Another possible content location; metadata alone does not establish whether it replaces or complements `why_sase` |
| `sase_post_blog.md` | Separate active project, parent `[[sase]]` | Outcome concerns features to launch after the post; it is a sibling, not the child being removed |

The parent has two open ordinary tasks: deciding whether to reframe the article as a “goodbye,” and the already-Next task to remove the child (`^no-more-0-prj`). Its other material includes Requirements, Screenshots, and historical completed/canceled tasks.

The child contains **six open resident tasks in addition to its lifecycle task**: three ordinary tasks and three reference tasks. These should all be accounted for, even if frontmatter counters present a different summary.

| Resident task | Block ID | Current state / constraint |
| --- | --- | --- |
| Structured Agentic Software Engineering reference | `ref-structured-agentic-software-engineering` | Ready |
| First paragraphs reference | `ref-sase-launch-post-introduction` | In Progress |
| Recommended outline reference | `ref-sase-launch-post-outline` | In Progress |
| Launch an agent to create Zettelkasten notes | `zk` | Blocked; scheduled `2026-10-17` |
| Gather blog references | No trailing block ID returned | Blocked; scheduled `2026-10-16` |
| Review the introduction/outline and run another polishing swarm | `intro-proposal` | Blocked by the two introduction/outline reference tasks |

The child's `^intro-proposal` Depends-On line points to the two local reference-task blocks. Those references have generated BLOCKS mirrors. Their old `2026-08-24` schedules are past dates on the research date; the two future ordinary-task schedules remain meaningful blockers. Removing the project boundary must not erase either kind of real constraint.

This is also a context merge. The child has substantial Requirements, Contents, and Outline material, including embedded images, quotes, examples, and ideas for future posts. The parent has its own overlapping writing notes. Moving only the three ordinary tasks would omit much of the useful work.

The incoming-link query reported **17 distinct notes** linking to the child. Seven have `parent` set to it:

- `why_sase.md`
- `sase_blog_0_legacy_notes.md`
- `done/sase_blog_0_done.md`
- `ref/blogs/structured_agentic_software_engineering.md`
- `ref/chat/sase_launch_post_introduction.md`
- `ref/chat/sase_launch_post_outline.md`
- `ref/chat/databricks_omnigent_job_fit.md`

Daily notes from October 7–15 include task links to `^intro-proposal` and/or the two reference tasks. Today's daily note also links to those references. The canceled `sase_blog_blockers` project mentions the child in its completion description. This establishes that deleting the child without repairing references would break useful navigation and task identity. It does not establish an exhaustive list of every textual mention or every possible link syntax.

## Critique of the proposed simplification

**The core idea is sound.** A project boundary earns its cost when it represents an independently managed outcome: a second committed article, a separate release, or work with its own lifecycle. “All blog work” and “the only planned blog post” currently overlap too much. Reintroducing a second project later is possible if a second post becomes a concrete commitment; it is unnecessary to retain the hierarchy as insurance.

**One project does not require one document.** The draft, reference notes, images, and historical archive serve different purposes. The useful simplification is one place to find and manage publication work. Flattening those documents into the project would enlarge the note and create more link repairs without reducing project overhead further. Keep the existing draft linked from the project; establish which existing content note is authoritative before consolidating prose. Do not create a third draft location merely to complete this merge.

**The source material suggests a scope problem beyond note count.** The child's outline still includes “Future Blog Posts,” while many Requirements are questions or optional presentation ideas. There is also a task whose instructions would create a new project note for proposed Zettelkasten work, and another calls for another research/polishing swarm. Those may be valuable, but they can reproduce the same coordination overhead and delay publication if treated as prerequisites by default. Preserve them during migration, then explicitly decide which work is required for this article. Do not automatically cancel them or remove their dependencies.

**The “goodbye” framing remains an editorial decision.** The merge can proceed without deciding whether the article is an introduction, retrospective, or goodbye. A provisional publication outcome is sufficient. Do not have the migration silently settle the voice, argument, or title.

**Avoid another infrastructure project to solve this one.** There is no evidence here that Bob needs a generalized project-merge command, a new plugin, a new taxonomy, or a new note hierarchy. A small, reviewable migration using existing task-move behavior and a precise link map fits the scale of the problem.

## Alternatives considered

| Approach | Benefit | Cost / limitation | Judgment |
| --- | --- | --- | --- |
| Keep parent and child | No migration | Retains two lifecycle tasks and routing choices for one publication | Poor fit for current intent |
| Convert child to a normal task in parent | Existing supported reversal preserves a task tree | Creates another publication task beneath the parent's publication lifecycle; current children and backlinks block the shortcut | Useful for other cases, not preferred here |
| Merge tasks/context into parent and retire child | One publication outcome, one active project, familiar destination name | Requires identity, link, and parent-field repair | Recommended |
| Keep an inactive child as a historical/redirect note | Can provide a temporary landing page for residual references | Retains an extra file; a plain redirect does not make old block links resolve to moved tasks | Temporary fallback only |
| Rename the child to replace the parent | Keeps the larger body intact | Still must merge parent history and resolve the destination-name conflict and two `^prj` identities | No clear advantage |

### Why the built-in reversal is not a one-step solution

The project contract documents Ctrl+Alt+Shift+N on `^prj` as conversion back to a task in the parent's Tasks section. It retains a root task, carries supported section lists beneath it, repoints inbound `#^prj` links, and trashes the project note after successful writes. [C1]

The actual plugin code adds decisive preconditions: it refuses a project with child notes, refuses backlinks other than permitted `^prj` links, rejects duplicate destination block IDs, and rejects unsupported content shapes. Current child-note parent links alone are enough to make this shortcut unsuitable without preparation. Non-lifecycle task links are another obstacle. [C2]

Even after all that preparation, reversal would leave a normal “publish first post” task beneath a project whose new outcome should be “publish the post.” That intermediate task would need further consolidation. Directly moving residents and mapping the two equivalent lifecycle identities avoids that detour.

## Explicit adjustments to the requirements

1. **Interpret “everything from `sase_blog`” as one management home.** Supporting draft, reference, legacy, and archive notes may remain separate and should be reachable from that home.
2. **Replace the series-level outcome with a single-publication outcome.** For example, “Publish the SASE article at https://sase.sh.” Keep the existing `sase_blog#^prj` identity. Additional posts remain uncommitted ideas.
3. **Retire the redundant lifecycle without claiming publication happened.** Map the child's equivalent `^prj` references to the surviving lifecycle. Do not check or cancel the publication task simply because the merge is finished. The separate `^no-more-0-prj` task can be completed once the actual migration passes review.
4. **Make preservation part of acceptance.** Preserve all six resident tasks, their subtrees, constraints, reference relationships, logs, and incoming navigation. An absence of `sase_blog_0` from the project list is insufficient by itself.
5. **Keep the old archive filename unless a separate need justifies renaming it.** Reparent it and link it from the surviving project. Historical filenames need not match current project boundaries.
6. **Separate the mechanical merge from editorial pruning.** Review speculative requirements, future-post ideas, Zettelkasten preparation, and further research afterward. That review may shorten the publication path, but it should not become an unbounded prerequisite to the merge.

## Suggested migration and acceptance checks

This is an execution recommendation, not a claim that these operations have been performed.

### 1. Record the current state and the identity map

Use the current vault editing workflow to establish a recoverable checkpoint and inspect sync state. Re-query before writing: the research reads were not an atomic vault snapshot, and some queries intermittently encountered missing files during indexing. Do not infer that an incomplete query means no references exist.

Build an explicit mapping:

| Existing identity | Destination |
| --- | --- |
| `sase_blog_0#^prj` | `sase_blog#^prj` |
| `sase_blog_0#^zk` | `sase_blog#^zk`, subject to collision check |
| `sase_blog_0#^intro-proposal` | `sase_blog#^intro-proposal`, subject to collision check |
| Each of the three reference-task block links | Same block ID in `sase_blog`, subject to collision check |
| Child note-level links and child `parent` values | `sase_blog`, or a more specific preserved section when appropriate |
| `done/sase_blog_0_done#^…` | Unchanged when the archive remains at its existing path |

Also inventory heading links and non-task block anchors before combining sections. Keep one destination block ID per task and exactly one lifecycle block `^prj`; the two lifecycle lines cannot simply be pasted together.

### 2. Move tasks with their children and link repairs

Use Bob's supported Ctrl+Shift+M task moves for the six resident tasks, or an equivalent carefully staged migration if implementation must be headless. The supported move planner rebases same-note block links, rewrites references and path-derived dependency IDs across files, rejects destination-ID collisions, and handles project-blocking effects. It also stamps freshness on moved open tasks, so a freshness update can be an expected migration effect. [C3]

Preserve the two In Progress reference tasks, the two future schedules, and the `intro-proposal` dependency relationship. A task move is not authorization to make scheduled work Ready, add ledger links, or promote all remaining work. Keep the task without a block ID intact; assign one through supported tooling only if the implementation needs a stable identity.

### 3. Combine context without duplicating the publication task

Update the parent's outcome and preserve its `^prj`. Transfer the child's lifecycle log and relevant completion context. Its past `2026-08-24` date is historical context, not a reason to invent a new deadline or reset the resident tasks' schedules.

Combine overlapping Requirements and Outline material, preserving content and anchors before optional deduplication. Keep a Contents link to the chosen existing draft and preserve Screenshots. A compact History link to the existing archive is sufficient. Reuse the existing sections rather than introducing another management scheme.

Reparent the seven identified child notes to the surviving project, reviewing whether each still belongs there. In particular, preserve the job-fit reference during the mechanical merge rather than opportunistically reorganizing unrelated research.

### 4. Repair references, retire the child, and reconcile

Update actual link destinations, including today's and historical daily-note task links. Preserve session timestamps and work-log text. Distinguish the exact child-note path from the archive path; blanket replacement of the string `sase_blog_0` would also change archive names and other intentional historical text.

Once all moved content and links are accounted for, retire the child as an active project and trash its obsolete note. Do this before expecting project sync to remove the generated Sub-projects entry; leaving a live child with the same parent would make it reappear. A temporary non-project compatibility note is reasonable only if some references cannot yet be safely repaired, and must be called out as unfinished cleanup. It cannot substitute for repairing block links.

Preview project and dependency reconciliation:

```bash
bob projects sync --dry-run
bob task reconcile --dry-run --retry-timeout 0
```

These previews cover the vault, so inspect unrelated proposed effects before applying their corresponding live commands. They derive generated links, dependency mirrors, blocking, and task grouping; they do not perform a semantic project merge for you. [C1, C4]

### 5. Preserve archive behavior deliberately

Keep `done/sase_blog_0_done.md`, change its parent to `[[sase_blog]]`, and expose it through a normal History link. Keep its existing task block IDs and historical incoming links.

Do **not** assume that putting `done_tasks: [[done/sase_blog_0_done]]` on the parent will redirect future archival. The current archive planner derives the destination from the source path: tasks archived from `sase_blog.md` go to `done/sase_blog_done.md`, and the command maintains `done_tasks` for that derived destination. [C5] Inspect whether that canonical destination already exists before implementation; this research did not establish its absence conclusively. A legacy archive plus the normal future archive is acceptable. Merging archives is optional extra work, not necessary to simplify active planning.

### Acceptance criteria

- `sase_blog` is the sole active project for writing/publishing this article; `sase_post_blog` remains a separate sibling project for its existing purpose.
- The surviving project has exactly one `^prj`, with a single-article completion criterion and no false completion event.
- All six former child residents are present once, with notes/logs preserved; the existing parent tasks remain accounted for. The merge task is completed only after verification.
- The two reference prerequisites still block `intro-proposal`; future schedules still block the two scheduled tasks.
- Today's task links and sampled historical task links resolve to the same tasks at their new locations. Reference notes still point to their moved reading tasks where applicable.
- All seven identified child-note parent links are repaired; the old archive remains reachable and its block links resolve.
- Heading and note-level links to the retired file have been repaired. A link audit reports no unexplained references to a deleted child, while legitimate archive references and historical prose remain intact.
- Capture routes and project views offer the surviving project without an active `sase_blog_0` project; reconciliation previews reveal no unexplained blocker or ledger changes.

## Evidence and limits

The primary evidence was the live vault queried through the audited `bob_query` skill, alongside current project contracts and plugin source opened through `sase repo`. Supporting-note metadata was inspected, but draft prose, legacy-note bodies, and reference annotations were not evaluated. This report therefore recommends preserving those documents and resolving the draft-location ambiguity before changing prose. It does not claim a complete editorial assessment or a complete backlink audit.

Representative reproducible queries:

```bash
bob query --format json --query 'TABLE WITHOUT ID file.path AS File, file.frontmatter AS Metadata, file.inlinks AS Incoming, file.outlinks AS Outgoing FROM "sase_blog.md" OR "sase_blog_0.md" OR "why_sase.md" OR "done/sase_blog_0_done.md"'

bob query --format json --query 'TABLE WITHOUT ID file.path AS File, item.line AS Line, item.text AS Text, item.status AS State, item.blockId AS Block, item.scheduled AS Scheduled, item.section AS Section FROM "sase_blog.md" OR "sase_blog_0.md" FLATTEN file.lists AS item'

bob query --format json --query 'TABLE WITHOUT ID file.path AS File, type AS Kind, parent AS Parent FROM [[sase_blog_0]]'
```

Local source references, inspected at bob-cli revision `dad02a2f6e308ca8492759a967e17658d140f6b4` and bob-plugins revision `841119ed0e3b59204d737263c7913f23ad040441`:

- **C1:** [Project contract](../../../../docs/projects.md), especially Project Notes, The `^prj` Task, Sync Rules, and project reversal.
- **C2:** [Project conversion implementation](../../linked/bob-plugins/plugins/bob-navigation-hotkeys/src/665-plugin-project-conversion.js), `convertProjectNoteToTask`, including child-note and backlink preflights; [reversal parser](../../linked/bob-plugins/plugins/bob-navigation-hotkeys/src/210-rename-and-line-context.js), `splitProjectNoteForReversal` and `buildTaskBlockFromProjectNote`.
- **C3:** [Task move planner](../../linked/bob-plugins/plugins/bob-navigation-hotkeys/src/250-task-move.js), `rewriteTaskMoveReferences` and `planTaskMoveAcrossFiles`.
- **C4:** [Dependency contract](../../../../docs/task-dependencies.md), especially project blocking, move behavior, and managed Depends-On/BLOCKS lines; current `bob task reconcile --help`.
- **C5:** [Archive path derivation](../../../../src/native/collect_done/transform.rs), `archive_relative_path`; [archive planner](../../../../src/native/collect_done/plan.rs), `build_collection_plan`.

Audited memory reads covered Obsidian vault conventions, project/task/link terminology, project blocking inheritance, dependency source-of-truth rules, and artifact registration. No peer report or unrelated prior research report was used.

Obsidian's official documentation independently confirms that note renaming can update links and that block references include both a note destination and a block ID. That supports treating this as an identity-preserving merge rather than relying on deletion or a file rename alone. [Internal links](https://obsidian.md/help/links)

Aliases provide alternate note names; the documented alias insertion produces a link to the canonical file with alternate display text. An alias is not a documented per-block migration mechanism, and it should not be used as the sole repair for moved task links. Bob's `project_name_aliases` is a separate routing feature. [Obsidian aliases](https://obsidian.md/help/aliases), [Bob external names](../../../../docs/projects.md#external-names-project_name_aliases)

## Recommended solution

Merge the six resident tasks and useful planning context from `sase_blog_0` into `sase_blog`, retain the parent's `^prj`, and change its outcome to publishing one SASE article. Reparent supporting notes, repair task and note links, keep the existing draft and archive as linked documents, then retire the child project after verification. Preserve the current constraints during that move; afterward, trim optional research and future-post preparation to the minimum needed to publish. This removes the redundant project without replacing it with another layer of process.
