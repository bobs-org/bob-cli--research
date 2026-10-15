# Collapse `sase_blog_0` into `sase_blog`

Researcher: `grk`. Independent report. Do not treat this as the swarm synthesis.

- **Question:** Bryan split `sase_blog_0` out of `sase_blog` as a numbered sub-project for the first post of a series. He now expects only one post, wants the sub-project gone, and wants every remaining blog task managed from `sase_blog`. Is that a good idea, and what is the safest way to do it?
- **Evidence:** live vault notes `~/bob/sase_blog.md`, `sase_blog_0.md`, `sase_blog_contents.md`, `why_sase.md`, `sase_blog_0_legacy_notes.md`, `sase_blog_blockers.md`, `sase_post_blog.md`, `sase.md`, `done/sase_blog_0_done.md`, and the seven notes whose `parent:` points at `sase_blog_0`; `bob projects list` / `bob capture-targets`; Dataview children and inlinks; vault-wide `sase_blog_0` mentions; bob-cli `docs/projects.md` (sync, Sub-projects line, reverse conversion); `docs/task-dependencies.md` §§12.10–13 (cascade, move, conversion); `docs/capture.md` (project-note `+` grammar); `docs/dataview.md` (`[id::]` identity); `docs/task-status-hooks.md`; bob-plugins `bob-navigation-hotkeys` `convertProjectNoteToTask` / `buildTaskBlockFromProjectNote` / `splitProjectNoteForReversal` / `collectProjectNoteBacklinkClassification`; decisions `projects-block-from-prj-line`, `subprojects-inherit-project-blocking`, `task-deps-are-depends-on-links`, `unblocked-tasks-are-offered`, `note-ready-cap-counts-the-lane`; glossary Project Note / Project Task / Area Note / Task Link / Task Dependency Link.
- **Date of evidence:** 2026-10-15. Nothing was implemented or migrated.

## Bottom line

Yes: retire the `sase_blog_0` **project**. Keep `sase_blog` as the one writing project under `sase`.

No: do not press Ctrl+Alt+Shift+N on `sase_blog_0`'s `^prj` and expect a clean merge. Reverse conversion is the official un-split, and it is the wrong tool for this note. It would refuse on child notes, on vault-wide basename links, and on non-list body (status-grouping chips, `^outline`, `See [[why_sase]].`). If those gates were cleared by hand, it would still restore the child's work as **nested children of one wrapper task** whose block id would be `^0`, while leaving `sase_blog`'s `^prj` as "Publish the full sase.sh blog series!" That is more nesting, not less.

**Recommended solution:** a flat merge.

1. Rewrite `sase_blog`'s `^prj` to the child's completion criteria: *Post the launch essay to https://sase.sh*.
2. Ctrl+Shift+M each ordinary open task from `sase_blog_0` onto `sase_blog` as a sibling under `## Tasks`.
3. Merge Requirements / Outline into `sase_blog` as **sections**, not as a restored wrapper task. Keep the prose draft in `sase_blog_contents.md`.
4. Reparent the seven child notes from `sase_blog_0` to `sase_blog`. Point `done_tasks` at the existing archive (rename it).
5. Empty then trash `sase_blog_0`. Do not cancel it and leave a `~~[[sase_blog_0]]~~ ❌` ledger row.
6. `bob projects sync` then `bob task reconcile`.
7. Leave `sase_post_blog` alone. That is the correct remaining split: product work after the post, not "post 0 of a series."

## Is this a good idea?

### What is right in the request

The numbered child is series scaffolding for a series that is not happening.

- `sase_blog` `^prj` still says **Publish the full sase.sh blog series!** and its only Sub-projects row is `[[sase_blog_0]]`. `sase_blog_0` `^prj` says **Post first blog post to https://sase.sh!** Those two lines are one outcome described twice, with a fake fan-out of 1.
- `bob projects list` shows `sase_blog` (3 open / 2 shown) and `sase_blog_0` (7 open / 3 shown). Capture lists both as `@sase_blog` and `@sase_blog_0`. The `]s` PROJECTS tier walks both `^prj` lines. Sub-project blocking (`decisions:subprojects-inherit-project-blocking`) adds a cascade hop that currently carries no reason: neither `^prj` is Blocked by an open Depends-On or a future date (the child's `[scheduled:: 2026-08-24]` is past).
- The conversion that created the child is still on the parent as a completed task: `Convert [[sase_blog_0]] into a project!` `^create-prj-0` (2026-06-25). The cancelled precursor is `Plan first blog post ([[sase_blog]] -> [[sase_blog_0]])`. The live Next task `Get rid of [[sase_blog_0]] in favor of [[sase_blog]]!` `^no-more-0-prj` is Bryan reversing that conversion on purpose.
- `sase.md` already lists `sase_blog` (not `sase_blog_0`) on its Sub-projects line, next to `sase_post_blog`. The parent name is the durable one. The `_0` suffix is the overcomplication.
- A 15-minute install post already exists at `https://sase.sh/blog/posts/structured-agentic-software-engineering/` (ref note parented to `sase_blog_0`, captured 2026-10-14). The child's outline already says to move that post to Getting Started and drop the series page. That is a single launch essay plus a getting-started page, not a numbered series.

One project note as the task hub is the design `docs/projects.md` and the glossary already describe: a Project Note holds the `^prj` completion criteria and the ordinary `#task` lines that make it true. A sub-project is for a **second finite outcome** with its own residents, not for "the first item of a list of one."

### Where the request as written overfits

"Get rid of that sub-project and start managing **everything** from the `sase_blog` project note" can be read as stuffing the article, the outline, the zettel, and the refs into one file. That is the same instinct that created `sase_blog_0`: every related note becomes a project.

The overcomplication is the **project type and the parent/child cascade**, not the existence of helper notes.

Today the writing already lives in several non-project files:

| Note | Role | Parent today |
| --- | --- | --- |
| `sase_blog.md` | Series project; meta-tasks; a Requirements dump | `sase` |
| `sase_blog_0.md` | Launch-post project; the real open work; Outline; a second Requirements dump | `sase_blog` |
| `sase_blog_contents.md` | Polished draft prose, created 2026-10-15 | `sase_blog` |
| `why_sase.md` | Earlier stub of the same opening paragraph | `sase_blog_0` |
| `sase_blog_0_legacy_notes.md` | Explicitly obsolete outline | `sase_blog_0` |
| Four `ref/` notes + `done/sase_blog_0_done.md` | Reading tasks and the archive | `sase_blog_0` |

Two project notes, two drafts of the same lede, two Requirements lists, and an "obsolete notes" file is the mess. Collapsing the **projects** and keeping **one draft child** (`sase_blog_contents.md`) is the cut that matches how Bob actually works.

### Would I take a different approach?

I would still kill the sub-project. I would not:

- Reverse-convert `sase_blog_0` back into a task on `sase_blog` (see next section).
- Rename `sase_blog_0` → `sase_blog` and delete the parent. `sase.md` already points at `sase_blog`; `sase_post_blog` already says "after [[sase_blog]] post"; capture already has `@sase_blog`. The `_0` name is what should die.
- Demote `sase_blog_0` to a non-project note and leave the file around. The stem stays in every picker and every backlink.
- Fold `sase_post_blog` in. Those seven tasks depend on `done/sase_done#^post-blog-prj`. They are product work that waits on the post, not writing work.
- Touch `sase_blog_blockers` (already `status: canceled`).
- Wait for a second post "just in case." `Ctrl+Alt+Shift+N` and capture `@sase_blog^id+` exist for the day a second finite outcome actually appears. An empty series parent is what created this.

I would treat the "Re-frame blog post as a goodbye to SASE?!" task as **content**, not as a merge step. It can stay a Ready row on `sase_blog` after the collapse.

## Why reverse conversion is the wrong tool

`docs/projects.md` and `bob-navigation-hotkeys` `convertProjectNoteToTask` (same chord as create-project-from-task, on a `^prj` line) are the documented un-split. For a freshly converted, still-tidy project they are excellent. `sase_blog_0` fails every gate that exists to protect that gesture.

### It refuses before it writes

From `convertProjectNoteToTask` and `splitProjectNoteForReversal`:

1. **Child notes.** "Project has N child notes; move them before converting." Seven notes have `parent: "[[sase_blog_0]]"` (or the piped equivalent): `why_sase.md`, `sase_blog_0_legacy_notes.md`, `done/sase_blog_0_done.md`, `ref/blogs/structured_agentic_software_engineering.md`, `ref/chat/sase_launch_post_introduction.md`, `ref/chat/sase_launch_post_outline.md`, `ref/chat/databricks_omnigent_job_fit.md`.
2. **Basename backlinks that are not `#^prj`.** `collectProjectNoteBacklinkClassification` treats any backlink original other than a `#^prj` rewrite as `otherPaths`, and the gesture refuses: *N notes link to "sase_blog_0"; update them before converting*. Live hits include daily Pomodoro Task Links (`[[sase_blog_0#^ref-sase-launch-post-introduction]]` on 2026-10-07 through 2026-10-15), ref-note embeds `![[sase_blog_0#^…]]`, the parent's Sub-projects line, and prose mentions on `sase_blog` and `sase_blog_blockers`.
3. **Non-list body.** Reversal only accepts `^prj` plus `##` sections whose bodies are list items. `sase_blog_0` has:
   - the machine-owned status-grouping chip line under `## Tasks`;
   - a paragraph `See [[why_sase]].` under `## Contents`;
   - a bare `^outline` block id under `## Outline`.
   Any one of those returns *content that is not a list item* / *content outside the ^prj task and its sections* and changes nothing.

### If the gates were forced, the shape would still be wrong

`buildTaskBlockFromProjectNote` emits **one** restored task whose description is the child's `^prj` text, then **indents every ordinary task and every section under it**. The restored block id is `getProjectReversalBlockId("sase_blog_0", "sase_blog")` → suffix `0` → `^0`. The broccoli Requirements bullet already carries `^0`. The parent `^prj` would remain "full series." The result on `sase_blog` would be:

```markdown
- [ ] #task #prj Publish the full sase.sh blog series! ^prj
- [ ] #task Post first blog post to https://sase.sh! ^0
    - [/] #task #ref …introduction
    - [/] #task #ref …outline
    - [?] #task Launch agent to create ~/bob/zk/ notes…
    - REQUIREMENTS
    - CONTENTS
    - OUTLINE
```

That is a sub-project reconstructed as a nested task tree. Bryan asked to **manage** the work from `sase_blog`, which in this vault means first-class residents under `## Tasks`, lanes, the Ready cap, capture `@sase_blog:id`, and Ctrl+Shift+P. Nested children of `^0` do not get that.

Ctrl+Shift+M is the gesture that produces sibling residents, rewrites block links vault-wide, stamps freshness, and respects `#prj_is_blocked` (`docs/task-dependencies.md` §8 table, §13.10).

## Current inventory (2026-10-15)

### `sase_blog` (keep; rewrite `^prj`)

Open:

- `[ ]` `^prj` — Publish the full sase.sh blog series! `#hide`, fresh today, Sub-projects: `[[sase_blog_0]]`
- `[ ]` Re-frame blog post as a "goodbye" to SASE?! (created today)
- `[*]` Get rid of `[[sase_blog_0]]` in favor of `[[sase_blog]]!` `^no-more-0-prj`

Closed: the plan/convert/move tasks that created the split. A Requirements section of quotes, screenshot paths, and slop categories. No `done_tasks`. No `ready_cap` override (default 5).

### `sase_blog_0` (retire as a project)

Open:

- `[ ]` `^prj` — Post first blog post to https://sase.sh! `#hide`, `[scheduled:: 2026-08-24]` (past; schedule log "Today is the day!")
- `[ ]` `#ref` structured agentic software engineering paper `^ref-structured-agentic-software-engineering`
- `[/]` `#ref` launch-post introduction `^ref-sase-launch-post-introduction`, `[id:: sase_blog_0__ref-sase-launch-post-introduction]`
- `[/]` `#ref` launch-post outline `^ref-sase-launch-post-outline`, `[id:: sase_blog_0__ref-sase-launch-post-outline]`
- `[?]` zk-note agent `^zk`, P1, `[scheduled:: 2026-10-17]`
- `[?]` Gather references, P1, `[scheduled:: 2026-10-16]`
- `[?]` intro-proposal `^intro-proposal`, Depends-On the two in-progress refs

`done_tasks: "[[done/sase_blog_0_done]]"`. Archive already holds the outline/fable/why-sase/zettel work from June–October. Leave those rows in `done/`; do not resurrect them.

The Depends-On graph on `^intro-proposal` is the only live edge. Matching is by `[id::]` value (`docs/dataview.md`; R1 / DW15 keep an existing id). After a move the `sase_blog_0__` prefix is cosmetic. Do not rewrite it unless a collision appears.

### Keep as a child of `sase`, not of the blog

`sase_post_blog`: "Plan features to launch after [[sase_blog]] post!" Four open + three blocked tasks, all (but one) depending on `done/sase_done#^post-blog-prj`. This is the post-launch product bucket. Collapsing it into the writing project would mix "ship the essay" with "fix remote machines / research_swarm / image toolset."

## Requirement adjustments

Call-outs the lead should adopt or explicitly reject.

| ID | Your requirement | Adjustment | Why |
| --- | --- | --- | --- |
| **ADJ-1** | Get rid of the `sase_blog_0` sub-project | **Yes. Retire it as a project.** Trash the file after a flat merge. Do not cancel-and-keep a struck Sub-projects ledger row. | A canceled child stays on the parent's generated line as `~~[[sase_blog_0]]~~ ❌` (`docs/projects.md` sync rules). The stem remains a capture/search hit. |
| **ADJ-2** | Manage **everything** from the `sase_blog` project note | Manage **tasks, `^prj`, Requirements, and Outline** from `sase_blog`. Keep the article body in `sase_blog_contents.md` as a non-project child. | Project notes are a task surface (lanes, cap, grouping, capture). A 2k-word draft in the same file fights `## Tasks`. The draft already lives there as of today. |
| **ADJ-3** | (Implied) reverse the June conversion with the same chord | **Do not reverse-convert.** Ctrl+Shift+M open tasks; copy sections; reparent; trash. | Reverse conversion nests work under `^0`, refuses on this note's children/backlinks/body, and leaves the series `^prj` in place. |
| **ADJ-4** | (Unstated) keep "Publish the full series" as `^prj` | **Replace** `sase_blog` `^prj` text with the child's: *Post the launch essay to https://sase.sh*. Drop the child's `^prj` rather than restoring it as a second task. Carry the schedule log only if you want the 2026-08-24 miss as history; do not copy that past date forward as a live project date. | Two completion criteria for one outcome is how the split started. The 15-minute post is Getting Started, not episode 0 of a series. |
| **ADJ-5** | (Unstated) future posts | **Do not reserve `sase_blog_1`.** If a second post becomes a real finite outcome, convert it then with Ctrl+Alt+Shift+N or capture `+`. Until then, leftover series ideas stay as Outline / Requirements bullets. | The child's Outline still lists Beads, Memory, Mobile, Evals, ChangeSpec, Architecture as "Future Blog Posts." That is a backlog, not a project tree. |
| **ADJ-6** | (Unstated) `sase_post_blog` | **Leave it.** | Already the post-launch product project, linked from `sase` and blocked on `^post-blog-prj`. Mixing it in re-creates a mega-note. |
| **ADJ-7** | (Unstated) drafts `why_sase` vs `sase_blog_contents` | **One draft: `sase_blog_contents.md`.** Reparent `why_sase` and fold or archive it. Reparent `sase_blog_0_legacy_notes.md` as history or delete it; it already says it is obsolete. | Same lede, three files. Today's contents note is the one that reads like a post. |
| **ADJ-8** | (Unstated) archive file | Set `sase_blog` `done_tasks:` to the existing archive. Rename `done/sase_blog_0_done.md` → `done/sase_blog_done.md` if you want the stem gone; otherwise keep the filename and only change `parent:`. | `sase_blog` currently has no archive pointer. New completes would otherwise have nowhere canonical to go. Daily notes already link into `done/sase_blog_0_done#^…`; a rename needs those links updated or a stub. **Prefer reparent-without-rename** unless the stem itself bothers you in search. |
| **ADJ-9** | The `^zk` task's "new project note file for each proposed zk note" | When that task runs, file zettel as **ordinary child notes** of `sase_blog` (or `~/bob/zk/` with `parent: [[sase_blog]]`), not as new `type: [[project]]` notes. A `.base` file is fine; it is not a project. | That bullet is how this over-split would reproduce itself. A zettel is not a finite project. |
| **ADJ-10** | (Unstated) Ready cap | No override. Default 5 is enough. | After merge the Ready lane is small: goodbye + maybe the paper ref. Next/Pending/Blocked/scheduled rows do not count toward the cap (`decisions:note-ready-cap-counts-the-lane`). |
| **ADJ-11** | (Unstated) `[id:: sase_blog_0__…]` | Leave the existing ids. | Vault-wide identity is the field value, not the path. Reconcile does not rewrite a valid existing id (DW15). Cosmetic cleanup is optional and easy to get wrong on `dependsOn`. |
| **ADJ-12** | "Re-frame as a goodbye" | Keep it as an ordinary task on `sase_blog`. Do not block the merge on a content decision. | Structure vs. voice. The collapse is justified either way. |

## Recommended procedure

Do this in Obsidian on the Mac so Ctrl+Shift+M rewrites live Task Links (today's daily still points at `sase_blog_0#^ref-sase-launch-post-introduction` and `#^ref-sase-launch-post-outline`). Run CLI sync after, not instead.

### 0. Preconditions

- No other editor holding unsaved buffers on these notes.
- `bob vault-sync status` clean enough that a later sync will not fight `_conflicts/`.
- Accept ADJ-4 (rewrite `^prj`) before moving work, so the destination project's completion criteria already name the post.

### 1. Rewrite the surviving `^prj`

On `sase_blog`:

```markdown
- [ ] #task #prj Post the launch essay to https://sase.sh! #hide ^prj
```

Drop "full series." Do not add `[scheduled:: 2026-08-24]`. If you want a ship date, pick a **future** one on this line (Task Card schedule); a past date does not block and only confuses the log.

### 2. Reparent children first

Change `parent:` on the seven notes from `sase_blog_0` to `sase_blog`. Reverse conversion is not in play, but the same child-note rule is why you do this before deleting the file: those notes must not dangle, and ref embeds that still say `![[sase_blog_0#^…]]` will be rewritten in step 3 when the tasks move.

Also set `sase_blog` frontmatter `done_tasks: "[[done/sase_blog_0_done]]"` (or the renamed path, ADJ-8).

### 3. Move ordinary open tasks

From `sase_blog_0` `## Tasks`, Ctrl+Shift+M each of:

- `^ref-structured-agentic-software-engineering`
- `^ref-sase-launch-post-introduction`
- `^ref-sase-launch-post-outline`
- `^zk`
- Gather references (no block id; mint one on move if prompted)
- `^intro-proposal`

Do **not** move `^prj`. Destination: `sase_blog`. They land as siblings, keep lanes (`[/]` and `[*]` are sticky), keep Depends-On, and have their `[[sase_blog_0#^id]]` links rewritten vault-wide. Parent `sase_blog` is not Blocked, so they should not pick up `#prj_is_blocked`.

Close `^no-more-0-prj` only after the file is actually gone.

### 4. Merge sections by hand

Copy `## Requirements` and `## Outline` from `sase_blog_0` onto `sase_blog`, de-duplicating against the parent's existing Requirements. Convert the Outline's bare `^outline` into a list item or drop the block id (it already lives on the archived `done/sase_blog_0_done#^outline` task). Point Contents at `[[sase_blog_contents]]` instead of inlining the draft. Fold `why_sase` into that draft or leave it as a historical child.

### 5. Retire the child project file

Once `sase_blog_0.md` has no open `#task` lines other than `^prj` and no unique sections you still need:

- Delete / trash the file (Obsidian trash + vault git keep history).
- Or, if you want a CLI-visible close: check `^prj` first, `bob projects sync` (parent Sub-projects becomes `~~[[sase_blog_0]]~~ ✅`), then delete the file and sync again so the closed child is pruned. Checking it also arms §12.10 trigger (c): closing the last open child may **offer** `sase_blog`'s `^prj` as a successor. Pick it only if you want the lifecycle task in today's Next; the offer is not auto-linked (`decisions:unblocked-tasks-are-offered`).

Do not leave a canceled `sase_blog_0` project sitting under `sase_blog`.

### 6. Reconcile

```bash
bob projects sync --dry-run
bob projects sync
bob task reconcile --dry-run
bob task reconcile
```

Expect: `sase_blog` Sub-projects line removed; `#hide` on `sase_blog` `^prj` still present (it still has open residents); grouping chips rewritten; intro-proposal still Blocked on the two refs; zk / gather-refs still Blocked on their future dates; no `#prj_is_blocked` on the moved rows.

### 7. Capture and review

From then on, new writing work is `@sase_blog`. The PROJECTS walk has one tracker. A later second post is a new conversion, not a reserved `_1`.

## Risks and leftovers

- **Daily-note history.** Closed Pomodoro links to `done/sase_blog_0_done#^…` can stay. Open links to `sase_blog_0#^…` must move in step 3; if any survive, they 404 after trash. Grep `sase_blog_0` after the merge and fix stragglers (blockers `^prj` prose, lib/chat YAML `parent: sase_blog_0`, review jsonl keys — jsonl is stats, leave it).
- **Ref embeds.** Three open refs and one paper ref embed `![[sase_blog_0#^…]]`. Ctrl+Shift+M is supposed to rewrite those with the task. Verify each ref note after the move.
- **Past project date copies.** Several child tasks still carry `[scheduled:: 2026-08-24]`. Past dates do not Block. They are noise. Optional cleanup with Task Card; not required for the merge.
- **Block id `^0`.** Lives on a Requirements bullet in the child. After a section copy it is a note-anchor, not a task. Do not also mint a restored task `^0`.
- **Quiet period.** `bob task reconcile` waits two seconds of mtime quiet on notes it structurally groups. Save, wait, then run it.
- **Ready cap / CROWDED.** Unlikely after this merge. If zk later dumps five new Ready rows into `sase_blog`, split, sequence, or defer by hand; do not raise `ready_cap` preemptively.
- **Inherited blocking from `sase`.** Flattening removes one cascade hop. `sase_blog` still inherits from `sase`. If `sase`'s `^prj` ever blocks, every blog resident blocks. That is already true of the parent today.

## Recommended solution

Collapse the **project relationship**, not the whole writing system, into `sase_blog`.

**Do:**

- One project: `sase_blog`, parent `sase`, `^prj` = post the launch essay.
- Ordinary open tasks live there as siblings (Ctrl+Shift+M).
- One draft child: `sase_blog_contents.md`.
- One archive: `done/sase_blog_0_done.md` reparented (rename optional).
- `sase_post_blog` stays the post-launch product project.
- Create a new sub-project only when a second post is a real finite outcome.

**Do not:**

- Reverse-convert `sase_blog_0` with Ctrl+Alt+Shift+N.
- Keep an empty series parent "for later posts."
- Put the article body in the project note.
- Fold `sase_post_blog` in.
- Spawn per-zettel project notes when `^zk` runs.

That is the smallest change that matches the vault as it exists on 2026-10-15 and the project/task contracts already shipped. The June split was reasonable when the `^prj` still said "series" and a `_0` implied a `_1`. With one post, it is a second `^prj`, a second capture route, a second PROJECTS walk row, and a cascade that never fires. Flatten it; keep the draft note; stop there.
