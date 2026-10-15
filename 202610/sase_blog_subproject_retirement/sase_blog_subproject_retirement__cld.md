---
title: "Folding sase_blog_0 back into sase_blog: critique and recommended merge"
researcher: cld
date: 2026-10-15
scope: Bob vault project structure for the sase.sh blog (sase_blog.md, sase_blog_0.md and satellites)
---

# Folding `sase_blog_0` back into `sase_blog`: critique and recommended merge

## Bottom line

1. **Yes, merge. The split was premature.** `sase_blog_0` was split out on 2026-06-25 to
   be post #0 of a series. The series has since shrunk from ten posts (June) to six
   (the 2026-06-07 research) to "probably one" (now). The hierarchy now models a plan you
   no longer have, and it costs something:
   - two `^prj` lines, plus a third "release" task in `job_2026`, for one outcome;
   - two separate `## Requirements` lists that research agents had to reconcile;
   - four links already broken by the original split.
2. **Use the purpose-built gesture, not a rename or the reverse conversion.**
   - One counted **Ctrl+Shift+M** (`5` then Ctrl+Shift+M on the first task) moves all six
     open tasks into `sase_blog`.
   - It rewrites the 20 block links in 11 files, the 2 `[id::]` fields and the 1
     `[dependsOn::]`.
   - The reverse "project note → task" conversion refuses this note, and would rebuild a
     sub-project inside a task anyway.
   - An Obsidian rename leaves stale `[id::]` values that later block task moves.
3. **Adjustment: cancel `sase_blog_0` as an emptied tombstone instead of deleting it.**
   Closed projects stay as notes everywhere else in the vault (for example
   `sase_blog_blockers` ❌). A tombstone leaves zero dangling links and keeps
   `done/sase_blog_0_done.md` (13 closed tasks, 14 inbound links) attached to its real
   history. Deleting is workable, but it adds about 10 manual link edits for no
   functional gain.
4. **Adjustment: rewrite `sase_blog`'s `^prj`.** "Publish the full sase.sh blog series!"
   is no longer the goal. The child's "Post first blog post to https://sase.sh!" is also
   ambiguous: per the 2026-10-07 outline research, a post has been live at
   `sase.sh/blog/posts/structured-agentic-software-engineering/` since 2026-07-08. The
   real finish line is an in-place rewrite in your own voice, then announcing it.
5. **Adjustment: "everything in `sase_blog`" should mean all tasks and planning, not the
   prose.** Keep the draft in `sase_blog_contents.md`, which you created at 15:10 today.
   Splitting by *kind* (draft vs. task management) is a good split. Splitting by
   *hypothetical future deliverable* was the bad one.
6. **Timebox it to one Pomodoro and use it as a triage pass.**
   - The project has been stalled since the missed 2026-08-24 date. "Gather a list of
     references" has rolled 8 times since 08-25.
   - Two proofreading tasks and the writer's-block research were cancelled.
   - Restructuring notes will not fix that. Cancel what you're dropping *before* moving,
     so only live work lands in `sase_blog`.
7. **Precondition (unrelated but urgent):** athena's vault-sync has been failing every
   ~20 s since 05:39 today and has left about 3,300 conflict copies in `~/bob/_conflicts/`.
   I filed it as **bob-cli-81** (§8). Do the merge on the Mac. It is safe for the Mac's
   content, but athena will quarantine its own edits to the touched daily notes until
   that bug is fixed.

---

## 1. What exists today (verified 2026-10-15 ~15:30)

### The two project notes

| | `sase_blog.md` (parent) | `sase_blog_0.md` (child) |
|---|---|---|
| `parent:` | `[[sase]]` | `[[sase_blog]]` |
| `^prj` | "Publish the full sase.sh blog series!" (open, `#hide`) | "Post first blog post to https://sase.sh!" `[scheduled:: 2026-08-24]`. Schedule Log: "*2026-08-24* — Today is the day!" |
| Open tasks | 2: `[*]` "Get rid of [[sase_blog_0]] in favor of [[sase_blog]]!" `^no-more-0-prj`, and `[ ]` "Re-frame blog post as a 'goodbye' to SASE?!" | 6: 1 Ready `#ref` (the captured *live* July post), 2 In Progress `#ref` (the 10-07 outline and introduction research), 3 Blocked (`^zk`, "Gather a list of references", `^intro-proposal`, which depends on the two `#ref` reads) |
| Closed tasks | 4, in place | 13, archived in `done/sase_blog_0_done.md` (`done_tasks:` frontmatter) |
| Non-task sections | `## Requirements` (June ideas), `## Screenshots` | `## Requirements` (Jul–Oct ideas, about 25 bullets), `## Contents`, `## Outline` with `^outline` (including a "Future Blog Posts" sub-list) |
| Size | 54 lines | 140 lines |

`bob projects list` shows `sase_blog wip 3 open / 2 shown` and
`sase_blog_0 wip 7 open / 3 shown`. Both counts include `^prj`.

### Satellites

- **Children of `sase_blog_0`** (via `parent:`):
  - `why_sase.md`: the August draft, 12 lines, described as "The contents of the first
    sase.sh blog post."
  - `sase_blog_0_legacy_notes.md`: the obsolete 10-section outline.
  - `done/sase_blog_0_done.md`.
  - Four ref notes: `ref/blogs/structured_agentic_software_engineering`,
    `ref/chat/sase_launch_post_outline`, `ref/chat/sase_launch_post_introduction`, and
    `ref/chat/databricks_omnigent_job_fit`. The last is a *job-search* ref that ended up
    under the blog.
- **Children of `sase_blog`:** `sase_blog_0`, and `sase_blog_contents.md`.
  - `sase_blog_contents.md` was created today from the project template, then stripped of
    `type`, `template`, `^prj` and the task stub. It keeps a leftover `status: wip`.
  - It now holds the real intro draft, and you were editing it while I researched.
  - Git shows you also created and immediately deleted a `sase_blog_1.md` project at
    15:09–15:10. The series instinct is still firing.

### Inbound references a merge must keep working

- **20 block links into `sase_blog_0#^…` across 11 files:**
  - 17 Pomodoro Task Links in daily notes from 2026-10-07 to 10-15, including two under
    today's Pomodoros;
  - 3 managed `![[…]]` embeds in the ref notes.
  - Every one of them targets a task that moves, so Ctrl+Shift+M rewrites them all.
- **14 links into `done/sase_blog_0_done#^…`:** daily notes plus the databricks ref
  embed. These are unaffected as long as the done file is not renamed.
- **Note-level `[[sase_blog_0]]` links:**
  - `parent:` in the 7 satellites;
  - prose in closed tasks (`sase_blog` `^plan-blog-post` and `^no-more-0-prj`,
    `sase_blog_blockers` `^prj`, done-file `^outline`);
  - plain text `parent: sase_blog_0` in two `lib/chat/*.md` sidecars.
- **Already-broken links:**
  - Four `[[sase_blog#^outline]]` links in `2026/20260619.md` broke when the outline
    moved into the child on 06-25. Moving `## Outline` (with `^outline`) back into
    `sase_blog` heals them.
  - `sase_blog.md:28` links `[[șase_blog_0]]` with a Romanian `ș`. It is a typo and an
    unresolved link.

### Cross-project relations that touch the blog's finish line

- `job_2026.md`: `[?] Release [[sase_blog]] post!` `^sase-blog`, with Depends-On
  `[[job_2026_apply_29#^prj]]`. The release is deliberately gated behind the
  29-application push.
- `sase_post_blog.md` ("Plan features to launch after [[sase_blog]] post!"):
  - Every task has Depends-On `[[done/sase_done#^post-blog-prj]]`. That task is "Create
    new [[sase_post_blog]] project note…", with child "Only bug fixes and blog posts until
    then".
  - It was **completed 2026-10-13**, so the "after the blog post" gate it was meant to
    express no longer blocks anything. The four unscheduled tasks show Ready.

### Signs the bottleneck is writing, not structure

- The child `^prj` date passed on 2026-08-24 ("Today is the day!").
- "Gather a list of references" has 8 Schedule Log rolls since 08-25.
- `^zk` has been rolling since 08-25.
- Cancelled in the done file:
  - "Proofread blog post!" (twice);
  - "Read research on how to get past writers block!";
  - "Describe demo video and infographic…" and "Flesh out… for each outline section"
    (the latter cancelled as "the same as the ^zk task").
- The real next action, `^intro-proposal` (review the 10-07 outline and intro research,
  then polish), is blocked only on reading those two reports, which are In Progress.

## 2. Is this a good idea?

**Yes.** Your diagnosis is right, and the case is stronger than "there will only be one
post":

1. **The hierarchy encodes a plan you abandoned.** `sase_blog` = series, `sase_blog_0` =
   post #0. The 2026-06-07 series-structure research already recommended "six promoted
   posts, not a ten-part serial". The 10-07 outline research's "Parked for later posts"
   list then turned the remaining series into "pointer at most" material. With one post,
   the parent's `^prj` describes nothing you're doing.
2. **The split is already costing you.**
   - There are three representations of "ship the post": parent `^prj`, child `^prj`,
     and `job_2026` `^sase-blog`.
   - Ideas land in whichever note was open. The 10-07 outline research had to read
     "`sase_blog.md` (series requirements)" and the child's list separately to build one
     outline.
   - The original split broke four links that are still broken.
3. **The sub-project machinery buys nothing here.**
   - Neither `^prj` has Depends-On links. The child's date is past.
   - The things a sub-project gives you are inherited blocking (via `parent:`), the
     generated `🧩 Sub-projects:` ledger, and `#hide` coupling between parent and child.
     All of them are inert or noise for one deliverable.
4. **The merge is cheap and reversible.** If a second post ever becomes real, "Create
   project note from task" (Ctrl+Alt+Shift+N) spins a task out into a new project note.
   It carries the date and Depends-On line, and turns ALL-CAPS child bullets into
   sections (`docs/projects.md:296-…`). Re-splitting later costs one gesture, so there is
   no reason to keep the scaffolding "just in case".

**What it won't do: get the post written.** Treat the merge as a 25-minute cleanup with
a triage pass (ADJ-4), not as progress on the post.

**Counter-arguments I considered and rejected:**

- **"I might write post #2."** Keep a `## Later Posts` section; the existing "Future
  Blog Posts" sub-list and the research's parked list already serve that role. Promote it
  to a project when it has its own completion criteria and its own tasks.
- **"`sase_blog_0` holds the history (done file, refs, daily links)."** That's an
  argument for *how* to dissolve it (tombstone, ADJ-1), not against dissolving it.
- **Per-note Ready cap** (default 5 per note). After the merge, `sase_blog`'s Ready lane
  is about 2 tasks, so the cap is not an issue.

## 3. What the tooling actually does

I read the bob-plugins source and the bob-cli docs and code.

### Ctrl+Shift+M, "Move tasks to note" (bob-navigation-hotkeys)

- **Links and fields:**
  - It reads every Markdown file in the vault before planning
    (`655-plugin-inbox-route.js:50-78`).
  - It rewrites `[[src#^id]]`, `![[src#^id]]` and `](src#^id)` links that point at moved
    blocks, in every file, skipping fenced code (`250-task-move.js:1-68`).
  - It rebases same-note `[[#^x]]` links in both the source and the moved block
    (`250-task-move.js:18-28`).
- **Identity:**
  - It rewrites each moved task's `[id::]` to `<dest>__<block>`, then applies the
    old-to-new id map to `[dependsOn::]` vault-wide (`240-cancel-and-lanes.js:838-901`).
  - It **refuses** a task whose `[id::]` is neither the old canonical id nor the bare
    block id (`240-cancel-and-lanes.js:878-883`). That makes stale ids a landmine for any
    approach other than this gesture.
- **Writes:** it writes the destination, then other files, then the source, with
  rollback. Moved tasks are appended to the end of the destination's `## Tasks`.
- **Selection:**
  - A count prefix selects the cursor's task plus N more `#task` lines *below it*. The
    scan crosses headings, skips `^prj`, and carries subtrees
    (`240-cancel-and-lanes.js:209-264`).
  - It does not move headings or non-task bullets. `^prj` can never be moved.
- **Block-id collisions** are refused, never renamed. I checked:
  - moved ids: `ref-structured-agentic-software-engineering`,
    `ref-sase-launch-post-introduction`, `ref-sase-launch-post-outline`, `zk`,
    `intro-proposal`;
  - `sase_blog` ids: `prj`, `no-more-0-prj`, `plan-blog-post`, `create-prj-0`.
  - **There are no collisions.** `^outline` and `^0`, which move by hand, also don't
    collide.
- **`#ref` tasks need nothing special.** The managed embed in each ref note is rewritten
  like any other link. The ref note's `parent:` is re-rendered from the task's residence
  on the next ref sync (`docs/highlights-ref-sync.md:1173-1176`). Until then, ref
  diagnostics report `parent_mismatch` (`docs/ref.md:521-528`).

### Reverse conversion: Ctrl+Alt+Shift+N on a `^prj` line

This is `convertProjectNoteToTask` in `665-plugin-project-conversion.js`. It is unsuitable
here:

- **It refuses this note** for two reasons:
  - when the project has child notes: "Project has N child notes; move them before
    converting" (`:529-535`). `sase_blog_0` has seven.
  - when any note other than the parent links to it (`:751-759`). Daily notes and ref
    embeds do.
- **Even if it ran:**
  - It would nest all six tasks under one umbrella task in `sase_blog`. That is a
    sub-project in disguise, which is what you're trying to get rid of.
  - It only repoints `#^prj` links and leaves `[id:: sase_blog_0__…]` values stale.
  - It ignores the done file.
  - It has an open bug where it leaves BLOCKS lines pointing at the trashed project
    (bob-cli-7i).

### Obsidian rename

`alwaysUpdateLinks: true` is set in `.obsidian/app.json`, so a rename updates note-level
links and frontmatter wikilinks. It does **not** touch `[id::]` or `[dependsOn::]` values.
Ids are "never rewritten" except by the move gesture
(`docs/task-dependencies.md:116-123`).

### `bob projects sync`

- **The Sub-projects ledger:** a deleted child drops off the generated line. A cancelled
  child renders `~~[[sase_blog_0]]~~ ❌` (`docs/projects.md:238-251`). Hand-deleting a
  closed entry prunes it permanently (`:282`).
- **`status:` frontmatter:** `[-]` on `^prj` sets `status: canceled` (`:153`).

### `bob task archive`

- The done file path comes from the source path: `done/<stem>_done.md`
  (`src/native/collect_done/transform.rs:84-107`).
- Archiving only happens at 10 or more closed tasks (`collect_done/mod.rs:40`). When the
  done file already exists, it appends to it with block-id dedup and ensures the
  `done_tasks:` frontmatter (`collect_done/plan.rs:261-292`).
- Done files are never scanned as sources, so nothing ever merges two done files.

## 4. Options compared

| Option | What it is | Manual edits | Dangling links afterwards | Verdict |
|---|---|---|---|---|
| **A. Fold down + delete** | Move tasks and sections into `sase_blog`, re-parent satellites, delete `sase_blog_0.md`, rename the done file to `done/sase_blog_done.md` | About 20: the B steps plus about 10 link and parent fixes, the done-file rename and re-parent, and `done_tasks:` | Historical prose links unless hand-edited | Acceptable. Tidier file list, more work, history slightly mangled. |
| **B. Fold down + tombstone** (recommended) | Same moves, then cancel the emptied `sase_blog_0` `^prj` with a Cancel Log pointing to `sase_blog` | About 10 | **None** | **Best.** Follows the vault's closed-project convention; the done file and the databricks ref stay coherent. |
| C. Promote the child by renaming it | Move `sase_blog`'s bits into `sase_blog_0`, delete `sase_blog`, rename `sase_blog_0` to `sase_blog` | Fewer link edits (Obsidian does them) | `[[sase_blog#^prj]]` links in `2026/20260614.md` silently retarget the child's `^prj`. 2 stale `[id::]` and 1 stale `[dependsOn::]` would make later moves refuse. Every `[[sase_blog]]` link dangles until the rename completes. | Reject: too clever, and leaves landmines. |
| D. Reverse conversion | Ctrl+Alt+Shift+N on the child `^prj` | n/a | n/a | Reject: it refuses here, and it would produce an umbrella task. |
| E. Keep `_0`, cancel the parent | Move `sase_blog`'s 2 open tasks down, re-parent `sase_blog_0` to `sase` | Fewest | `job_2026`, `sase_post_blog` and `sase.md` point at `sase_blog` | Reject: the cheapest option, but it keeps a "#0" name for a one-post project and contradicts your stated preference. |

## 5. Adjustments to your requirements (explicitly flagged)

- **ADJ-1 (changes "get rid of"): tombstone, don't delete.**
  - After the move, `sase_blog_0.md` is just its `^prj`, marked `[-]`, with a Cancel Log
    line: "Merged into [[sase_blog]]: one post, one project."
  - It drops out of every active view: terminal projects are inert to sync, the dash and
    the review walk.
  - The only visible trace is the ledger entry `~~[[sase_blog_0]]~~ ❌` on `sase_blog`'s
    `^prj`. You can hand-delete it if it bothers you.
  - If you still want the file gone, use the delete addendum in §6.
- **ADJ-2: rewrite the `^prj` completion criterion.** "Full series" is obsolete, and
  "Post first blog post" is technically already true (the July post is live). Suggested
  wording, framing-neutral so it survives the open "goodbye?" question:
  `- [ ] #task #prj The sase.sh launch post is rewritten in my own voice (same URL) and announced! #hide ^prj`.
  Don't carry the child's 2026-08-24 date. A past date only adds noise, and a *future*
  date on `^prj` would block every task in the note
  (`decisions:projects-block-from-prj-line`).
- **ADJ-3 (narrows "manage everything from `sase_blog`"):** all tasks and planning live
  in `sase_blog`, and the prose lives in `sase_blog_contents.md`.
  - `why_sase.md` is the superseded August draft. Re-parent it to `sase_blog` and mark it
    superseded.
  - Optionally fold its 12 lines into the legacy-notes note and retire it.
  - Replace `## Contents`' "See [[why_sase]]" with "Draft: [[sase_blog_contents]]".
- **ADJ-4 (new): triage before moving, and cancel in place.** Anything you drop should be
  cancelled *inside* `sase_blog_0` so it stays with the tombstone's history. Only live
  work moves. My recommendation, which is your call:
  - **`^zk`** ("Launch agent to create ~/bob/zk/ notes…, add a sase_blog.base…"):
    cancel, or move to `sase_post_blog`/`sase_ideas`. It is meta-structure, the outline
    research parks the architecture principles as later-post material, and it has rolled
    since 08-25.
  - **"Gather a list of references"**: cancel with the reason "covered by the 10-07
    outline research's sources and the Requirements bullet 'lots of good citations'". It
    has rolled 8 times.
  - **Keep:** the two In Progress `#ref` reads, `^intro-proposal` (the real next action),
    and the Ready `#ref` for the live July post (your rewrite baseline).
- **ADJ-5 (optional): give "release" one owner.** `job_2026` `^sase-blog` ("Release
  [[sase_blog]] post!", gated on `job_2026_apply_29#^prj`) duplicates the blog's own
  finish line.
  - **My lean:** Ctrl+Shift+M it into `sase_blog` as the project's last task. Its
    Depends-On link travels with it, and `job_2026_apply_29`'s BLOCKS line is rewritten
    automatically. The task advances the blog's outcome, and the job gate is still
    expressed as a dependency.
  - **Keep it in `job_2026`** if you want it in the job-search view. Either way, model the
    relationship with dependency links, not `parent:`.
- **ADJ-6 (observation, optional): `sase_post_blog`'s gate stopped working on 10-13.**
  - **The problem:** its tasks depend on a completed task, so "only bug fixes and blog
    posts until then" is no longer enforced.
  - **The fix if you still want the gate:** put one Depends-On `[[sase_blog#^prj]]` on
    `sase_post_blog`'s `^prj`, and drop the per-task links.
  - **Side effects:** every resident becomes Blocked and tagged `#prj_is_blocked`, and
    their Task Links leave today's Pomodoros. Move any genuine bug fix, such as "Fix remote
    machines!", out first.
- **ADJ-7 (minor tidy-ups):**
  - re-parent `ref/chat/databricks_omnigent_job_fit` to `job_2026`;
  - fix the `[[șase_blog_0]]` typo;
  - remove the leftover `status: wip` from `sase_blog_contents.md`;
  - optionally strip the inherited `[scheduled:: 2026-08-24]` stamps on moved tasks.
    They're past dates, so harmless.

## 6. Recommended solution: runbook (about 25 minutes, in Obsidian on the Mac)

0. **Preconditions.**
   - Ideally, get bob-cli-81 fixed or athena's stuck merge cleared first.
   - Otherwise, accept that athena will quarantine its local copies of
     `2026/20261014.md` and `2026/20261015.md`. The remote (Mac) version wins in place,
     so nothing on the Mac is lost.
   - Don't run the merge while an agent is editing these notes.
1. **Rewrite `sase_blog`'s `^prj`** (ADJ-2) and fix the `ș` typo.
2. **Triage in place in `sase_blog_0`** (ADJ-4): cancel the tasks you're dropping, with a
   Cancel Log reason (Task Card, then `x`).
3. **Move the live tasks.** Put the cursor on the first remaining open task and use
   `N` then Ctrl+Shift+M, where N = remaining tasks − 1 (for example `5` for all six),
   then choose `sase_blog`. Optionally do the same for `job_2026` `^sase-blog` (ADJ-5).
4. **Move the sections by hand.**
   - Append the child's `## Requirements` bullets under `sase_blog`'s `## Requirements`.
     Both are chronological, so June-then-Jul–Oct order is preserved.
   - Move `## Outline` *including the `^outline` line*. This heals the four 06-19 links.
     Rename its "Future Blog Posts" sub-list to a `## Later Posts` section if you like.
   - Move `## Contents`, with the ADJ-3 pointer change.
5. **Re-parent the satellites.** Set `parent: "[[sase_blog]]"` in `why_sase.md` and
   `sase_blog_0_legacy_notes.md`. Leave the ref notes to ref sync (only the databricks
   one per ADJ-7).
6. **Create the tombstone.** `sase_blog_0.md` should now hold only frontmatter, `^prj`,
   and the rows you cancelled in step 2. Cancel `^prj` with "Merged into [[sase_blog]]:
   one post, one project." Its Schedule Log can stay where it is, because history stays
   with the tombstone.
7. **Reconcile:** run `bob projects sync -d`, then `bob projects sync`, then
   `bob task reconcile -d`, then `bob task reconcile`. Expected results:
   - `sase_blog_0` → `status: canceled`;
   - ledger shows `~~[[sase_blog_0]]~~ ❌`;
   - `^intro-proposal` stays Blocked on the two `#ref` reads, now `sase_blog__…`.
8. **Verify:**
   - `grep -rn 'sase_blog_0#\^' ~/bob --include='*.md' | grep -v _conflicts` → nothing
     (done-file links use `done/sase_blog_0_done#^` and are expected);
   - `grep -rn 'sase_blog_0__' ~/bob --include='*.md'` → nothing;
   - `bob projects list` → `sase_blog wip`, `sase_blog_0 canceled`;
   - the 06-19 `[[sase_blog#^outline]]` links resolve in Obsidian;
   - after the next `bob ref scan`, the three moved refs show `parent: "[[sase_blog]]"`.
9. **Close `^no-more-0-prj`.** Today's Pomodoro link to it becomes a struck reference.

**Delete-variant addendum** (only if you overrule ADJ-1), after step 5:

1. Rename `done/sase_blog_0_done.md` to `done/sase_blog_done.md` *in Obsidian*, so its
   14 inbound links update and future archives land there.
2. Set its `parent:` to `[[sase_blog]]`, and add `done_tasks: "[[done/sase_blog_done]]"`
   to `sase_blog`.
3. Re-parent the databricks ref.
4. Replace the remaining prose `[[sase_blog_0]]` links with plain text, or leave them as
   history.
5. Delete `sase_blog_0.md`, then run step 7. The ledger line disappears.

**Target shape of `sase_blog.md` afterwards:**

```markdown
---
parent: "[[sase]]"
type: "[[project]]"
status: wip
---
- [ ] #task #prj The sase.sh launch post is rewritten in my own voice (same URL) and announced! #hide ^prj
	- 🧩 **Sub-projects:** ~~[[sase_blog_0]]~~ ❌        ← generated; prune by hand if unwanted

## Tasks
- [ ] #task Re-frame blog post as a "goodbye" to SASE?! …
- [ ] #task #ref [[ref/blogs/structured_agentic_software_engineering|…]] … ^ref-structured-agentic-software-engineering
### Next & In Progress
- [/] #task #ref …sase_launch_post_introduction… [id:: sase_blog__ref-sase-launch-post-introduction] …
- [/] #task #ref …sase_launch_post_outline…      [id:: sase_blog__ref-sase-launch-post-outline] …
### Blocked
- [?] #task Review … + launch another research swarm … [dependsOn:: sase_blog__ref-…, sase_blog__ref-…] ^intro-proposal
- [?] #task Release the post! ^sase-blog   ← only with ADJ-5 (Depends-On job_2026_apply_29#^prj)
### Done & Canceled
…

## Requirements      ← parent's June bullets, then the child's Jul–Oct bullets
## Screenshots
## Contents          ← "Draft: [[sase_blog_contents]]" + the motivation quote
## Outline
^outline
…
## Later Posts       ← former "Future Blog Posts"; promote to a project only when real
```

## 7. Open questions for Bryan

1. Is the "goodbye to SASE" reframe decided? It changes the wording of `^prj` and maybe
   the "announced" half of it.
2. Does "release" mean "the rewritten post is live" or "announced on LinkedIn and
   elsewhere"? This decides ADJ-5.
3. Do you still want `sase_post_blog` gated on the blog (ADJ-6)?

## 8. Out of scope but urgent: athena vault-sync is wedged (bob-cli-81)

- **What happens:** `bob vault-sync status --json` on athena shows `last_success_at`
  05:38:35 today, while `last_attempt_at` keeps advancing about every 20 s. The journal
  logs the same error every cycle since 05:39:31:
  `git failed: The following paths are ignored by one of your .gitignore files: _conflicts/.bob/stats/review/…jsonl`.
- **Root cause:**
  - `resolve_conflicts` copies a conflicted `.bob/stats/review/*.jsonl` to a path that
    mirrors its directories under `_conflicts/` (`conflict_copy_path`,
    `src/native/vault_sync.rs`).
  - The vault `.gitignore` is `*` plus a root-anchored `!/.bob/stats/**/*.jsonl`, so the
    copy stays ignored (`git check-ignore -v` → `.gitignore:3:*`).
  - `git add` then fails and the cycle repeats.
- **Impact:**
  - `.git/MERGE_HEAD` is present, with `UU bob.md` and `UU cash.md`.
  - About 3,300 quarantine copies have accumulated: 1,642 each of `bob.athena-*.md` and
    `cash.athena-*.md`, plus about 1,659 jsonl copies.
  - athena-side edits (nightly, archive) cannot sync.
- **Filed as a `bug` task bead, size medium, status ready,** linked as related to
  bob-cli-49 (conflict notifications fire on the same path). Cleaning up the quarantined
  copies is your call. I did not touch them.

## Sources

**Vault (read-only):**

- notes: `sase_blog.md`, `sase_blog_0.md`, `done/sase_blog_0_done.md`, `why_sase.md`,
  `sase_blog_0_legacy_notes.md`, `sase_blog_contents.md`, `sase_blog_blockers.md`,
  `sase_post_blog.md`, `job_2026.md`, `job_2026_apply_29.md`, `sase.md` header,
  `done/sase_done.md:1382-1387`;
- ref notes under `ref/`;
- `git log -p` for 2026-10-14/15 (the `sase_blog_1` create/delete and the
  `sase_blog_contents` creation);
- `.obsidian/app.json`.

**Prior research (vault PDFs):**

- `lib/chat/sase_blog_series_structure_consolidated.pdf` (2026-06-07: "six promoted
  posts, not a ten-part serial");
- `lib/chat/sase_launch_post_outline.pdf` (2026-10-07: "in-place rewrite of a live post";
  "Parked for later posts").

**bob-plugins** (`plugins/bob-navigation-hotkeys/src/`):

- `250-task-move.js:1-68`;
- `240-cancel-and-lanes.js:205-264, 838-901`;
- `655-plugin-inbox-route.js:50-78`;
- `665-plugin-project-conversion.js:529-535, 751-759`.

**bob-cli:**

- `docs/projects.md:153, 238-251, 282, 296-310`;
- `docs/task-dependencies.md:116-123`;
- `docs/highlights-ref-sync.md:1173-1176`;
- `docs/ref.md:521-528`;
- `src/native/collect_done/{mod.rs:40, plan.rs:261-292, transform.rs:84-107}`;
- `src/native/vault_sync.rs:742-960`;
- `bob projects list` output;
- memory: `obsidian.md`, and glossary `project-note`, `project-task`, `area-note`,
  `task-link`, `task-dependency-link`.

**Decisions:**

- `projects-block-from-prj-line`;
- `subprojects-inherit-project-blocking`;
- `task-deps-are-depends-on-links`;
- `note-ready-cap-counts-the-lane`.
