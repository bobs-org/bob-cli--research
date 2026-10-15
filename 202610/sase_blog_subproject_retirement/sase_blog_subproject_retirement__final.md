# Retiring `sase_blog_0`: one blog post, one project

Consolidated report · 2026-10-15 · merges the cdx, cld, grk, and gem reports with the lead's own
re-verification against the live vault, bob-cli docs/source, and bob-plugins source. Nothing in
the vault was changed.

## Bottom line

1. **Yes, merge `sase_blog_0` into `sase_blog`.** The split was premature. It modeled a series
   that has gone from ten planned posts (June) to six (the 2026-06-07 series research) to one
   (now). Today the two projects describe one outcome twice. The child's `^prj` finishes exactly
   when the parent's does, so the hierarchy only adds cost: two `^prj` lines, two capture routes
   (`@sase_blog`, `@sase_blog_0`), two PROJECTS-tier review rows, and two Requirements lists.
2. **Changing the completion criterion matters more than collapsing the note.** `sase_blog`'s
   `^prj` says "Publish the full sase.sh blog series!", which is no longer the goal. The child's
   "Post first blog post to https://sase.sh!" is already technically true: a Fable-drafted post
   has been live at `sase.sh/blog/posts/structured-agentic-software-engineering/` since
   2026-07-08. The real finish line is your own post, in your own voice, live on sase.sh.
3. **Use Ctrl+Shift+M (move tasks to note).** Do not use reverse conversion, an Obsidian rename
   of the child, or a hand-rebuilt note. One counted move takes all six open tasks into
   `sase_blog`. It rewrites the 20 block links in 11 files and remaps `[id::]`/`[dependsOn::]`.
   Each of the other approaches either refuses, nests the work under a wrapper task, or leaves
   stale ids that block later moves.
4. **Delete the child file, and rename its archive to `done/sase_blog_done.md` in Obsidian.**
   This leaves one project, one archive, and no `sase_blog_0` stem in pickers. Keeping a
   cancelled `sase_blog_0` (cld's preference) is a valid fallback; see §6.
5. **The merge will not write the post.** The real bottleneck is writing:
   - The child's 2026-08-24 date passed with "Today is the day!"
   - "Gather a list of references" has rolled 8 times since 08-25.
   - Proofreading and writer's-block tasks were cancelled.

   Timebox the mechanics to one Pomodoro and pair them with a short triage pass.
6. **Precondition:** athena's vault-sync is wedged (bead **bob-cli-81**, filed by cld today).
   Do the merge in Obsidian on the Mac, and run the `bob` CLI steps there too.

## 1. What the vault shows (re-verified ~15:45)

| Note | Role today | Facts that matter for the merge |
|---|---|---|
| `sase_blog.md` | Project, parent `[[sase]]` | `^prj` "Publish the full sase.sh blog series!". Generated `🧩 Sub-projects: [[sase_blog_0]]`. Open tasks: "Re-frame blog post as a 'goodbye' to SASE?!" and `[*]` `^no-more-0-prj`. Four closed tasks, Requirements, Screenshots, no `done_tasks`. Line 28 has a typo link `[[șase_blog_0]]`. |
| `sase_blog_0.md` | Project, parent `[[sase_blog]]` | `^prj` with past `[scheduled:: 2026-08-24]`. **Six open residents** (below). Requirements (~25 bullets, Jul–Oct). Contents (a quote, "See [[why_sase]]"). Outline with a bare `^outline` and a "Future Blog Posts" sub-list. `done_tasks: [[done/sase_blog_0_done]]`. |
| `sase_blog_contents.md` | **The real draft**, created 15:10 today, parent `[[sase_blog]]`, no `type` | Already reworks `why_sase`'s lede and the Contents "tinkering" quote. Has a leftover `status: wip`. |
| `why_sase.md` | August draft stub, parent `sase_blog_0` | Superseded by `sase_blog_contents.md`. |
| `sase_blog_0_legacy_notes.md` | Self-described "Obsolete notes", parent `sase_blog_0` | History only. |
| `done/sase_blog_0_done.md` | Archive: **11** closed tasks, parent `sase_blog_0` | 14 inbound block links (daily notes, the databricks ref embed, and 2 internal). Ids do not collide with `sase_blog`'s. |
| `sase_post_blog.md` | Sibling project under `sase` | "Plan features to launch after [[sase_blog]] post!" Separate outcome; keep it separate. |
| `job_2026.md` `^sase-blog` | `[?]` "Release [[sase_blog]] post!" | Depends on `job_2026_apply_29#^prj`. A third representation of the finish line. |

The six open residents of `sase_blog_0`:

| Task | State | Constraint to preserve |
|---|---|---|
| `#ref` SASE paper (the live July post) `^ref-structured-agentic-software-engineering` | Ready | none |
| `#ref` launch-post introduction research `^ref-sase-launch-post-introduction` | In Progress | `[id:: sase_blog_0__…]`, BLOCKS `^intro-proposal` |
| `#ref` launch-post outline research `^ref-sase-launch-post-outline` | In Progress | same |
| Launch agent to create `~/bob/zk/` notes `^zk` | Blocked | scheduled 2026-10-17 |
| Gather a list of references (no block id) | Blocked | scheduled 2026-10-16; 8 rolls |
| Review outline/intro and launch another swarm `^intro-proposal` | Blocked | Depends-On the two in-progress refs |

Inbound references a merge must keep working:

- **20 block links into `sase_blog_0#^…` across 11 files:** 17 Pomodoro Task Links in daily notes
  from 10-07 to 10-15 (two under today's open 15:05 BLOG Pomodoro), plus 3 managed `![[…]]` embeds
  in ref notes. All of them target tasks that move, so Ctrl+Shift+M rewrites them all.
- **Seven `parent:` fields:** `why_sase`, `sase_blog_0_legacy_notes`, the archive, and four ref
  notes. One of those ref notes, `ref/chat/databricks_omnigent_job_fit`, is job-search material
  filed under the blog.
- **Five prose `[[sase_blog_0]]` links in closed or historical text:**
  - `sase_blog` `^no-more-0-prj` and `^plan-blog-post`;
  - `sase_blog_blockers` `^prj`;
  - the archive's `^outline` task;
  - the legacy note.

  Two `lib/chat/*.md` sidecars also contain plain-text `parent: sase_blog_0`.
- **Already broken:** four `[[sase_blog#^outline]]` Pomodoro links in `2026/20260619.md`. They
  logged work on the task "Decide on the blog posts' outline", which is now archived at
  `done/sase_blog_0_done#^outline`.

## 2. Critique: is this a good idea?

**Yes.** Your diagnosis is right, and a general rule explains why: **a sub-project earns its keep
only when its outcome can finish while the parent stays open.**
- With a series, "post #0 published" could finish while the series stayed open, so the June
  split was reasonable.
- With one post, finishing the child finishes the parent. The parent becomes an empty shell
  whose only content is a pointer to its child.

The sub-project machinery buys nothing here:
- Neither `^prj` has Depends-On links.
- The child's date is past, so the sub-project blocking cascade never fires.
- The generated Sub-projects line and `#hide` coupling are noise.
- If a second post becomes real, Ctrl+Alt+Shift+N ("Create project note from task") splits it
  out in one gesture. There is no reason to keep scaffolding "just in case".

**Where the request overreaches.** "Manage *everything* from `sase_blog`" should mean every task
and every planning artifact, not the prose. Splitting by kind (a project note for management, a
draft note for writing) is a good split; splitting by hypothetical future deliverable was the bad
one. You already made the right cut today by starting `sase_blog_contents.md`. A long draft
inside a project note would fight `## Tasks`, status grouping, and reconcile.

**The pattern to watch.** The over-structuring reflex is still in the backlog:
- `^zk` says "Create tasks in a new project note file for each proposed `~/bob/zk/` note". That
  would recreate this problem at a larger scale.
- `^intro-proposal` ends in "launch another research swarm".
- A `sase_blog_1` project note was created and deleted at 15:09–15:10 today, just before
  `sase_blog_contents.md` appeared. It may simply have been a first try at the draft note; the
  evidence is ambiguous.

The merge is worth doing, but it is cleanup. Treat it as a cleanup step, not as progress on the
post.

**Would I take a different approach?** Same goal, with three differences from the request as
written:
- rewrite the completion criterion, not just the note layout;
- keep the draft separate;
- end with a triage pass so only live work lands in the merged project.

I would not reverse-convert the child, rename it over the parent, keep `_0` and cancel the
parent, or fold `sase_post_blog` in. §5 explains why each one loses.

## 3. Where the reports disagreed, and how I resolved it

| Issue | Positions | Resolution (with evidence) |
|---|---|---|
| **Delete or tombstone the child** | cld: cancel it as an emptied tombstone, because that leaves zero dangling links and follows the closed-project convention. cdx, grk, gem: delete it. | **Delete.** You asked to *get rid of* it. A tombstone keeps the stem in the quick switcher, in `bob projects list`, and as `~~[[sase_blog_0]]~~ ❌` on the Sub-projects ledger (`docs/projects.md` sync rules). With the archive renamed (next row), deletion costs only a parent edit on the archive plus five optional plain-text edits to historical prose. The tombstone stays the fallback if you want zero unresolved links. |
| **Rename the archive or keep its name** | gem, and cld's delete variant: rename to `done/sase_blog_done.md`. cdx, grk: keep the name and reparent. | **Rename, in Obsidian.** The archive path is derived from the source stem (`src/native/collect_done/transform.rs` `archive_relative_path`). Archiving starts at 10 closed tasks (`collect_done/mod.rs` `DEFAULT_THRESHOLD`). So keeping the old name *guarantees* a second archive later, while a renamed file is appended to. Verified: `done/sase_blog_done.md` does not exist, archive ids do not collide with `sase_blog` ids, and `.obsidian/app.json` has `alwaysUpdateLinks: true`, so the 14 inbound links update. Do not rename it from a shell. |
| **`[id::]` values** | grk: leave the `sase_blog_0__…` ids; "the prefix is cosmetic". cld: the move rewrites them. | **cld is right; leave it to the gesture.** `prepareTaskMoveBlockIdentities` (`240-cancel-and-lanes.js`) rewrites each moved id to `<dest>__<block>`, maps old to new for `[dependsOn::]` vault-wide, and *refuses* a task whose id is neither canonical nor the bare block id. Hand-copied tasks with stale ids are a trap for any later move. |
| **How to move the work** | gem: hand-build the new `sase_blog.md` and hand-edit today's daily links. Others: Ctrl+Shift+M. | **Ctrl+Shift+M.** gem's plan fixes 2 of the 17 daily-note Task Links. The other 15 (10-07 to 10-14) would break, along with the `[id::]`/`dependsOn` consistency. |
| **Aliases as a redirect** | gem: add `aliases` and `project_name_aliases: ["sase_blog_0"]`. | **Reject.** Obsidian aliases are display and suggestion names, so `[[sase_blog_0#^x]]` does not resolve through them. `project_name_aliases` affects only `bob capture-targets` and `bob ref create -P`, and is shadowed while any note with that stem exists (`docs/projects.md` §External Names). It would also keep advertising the stem in capture completion ("aka sase_blog_0"), which defeats the purpose. |
| **A ship date on `^prj`** | grk: "If you want a ship date, pick a future one on this line." | **Wrong, and harmful.** A future inline date on `^prj` Blocks and tags `#prj_is_blocked` on **every** open resident, and drops their Task Links from today's Pomodoros (`decisions:projects-block-from-prj-line`). Put a date on a specific task, never on `^prj`, unless you want the whole project parked. |
| **The 06-19 `[[sase_blog#^outline]]` links** | cld: moving the bare `^outline` anchor back into `sase_blog` heals them. | **That only half-fixes them.** They would resolve to the Outline section. They were Task Links logging work on the outline-decision task, which now lives at `done/sase_blog_0_done#^outline`. Retarget them there before the archive rename, and Obsidian then carries them along. |
| **When to triage** | cld: cancel dropped tasks inside the child *before* moving, so history stays with the tombstone. cdx: migrate everything intact, then prune. | **Move everything, then triage in `sase_blog` in the same sitting.** With deletion, rows cancelled inside the child would leave with the file. Cancelled rows in `sase_blog` go to Done & Canceled and later to the (renamed) archive. Keeping mechanics and editorial pruning in separate steps also keeps the merge reviewable (cdx). |
| **`^prj` wording** | cdx: "Publish the SASE article at https://sase.sh". cld: "…rewritten in my own voice (same URL) and announced". grk: "Post the launch essay…". gem: "Publish the sase.sh blog post". | Use a criterion that is **not already true** (the July post is live) and is **framing-neutral** (the "goodbye" question is open): *"My SASE post, in my own voice, is live on https://sase.sh!"* Add "and announced" only if announcing is part of done (open question 1). |
| **Small factual slips** | gem: 11 archived tasks; cld: 13. gem: broken links would make "`bob plan` lane derivation fail"; "35 active projects". | 11 is correct. The `bob plan` claim is overstated: broken Task Links stop resolving, but nothing showed that lane derivation fails. The project count was not verified and does not matter. |

All four reports agree, and the source confirms, that **reverse conversion is the wrong tool**:
- `convertProjectNoteToTask` refuses a project with child notes (seven here).
- It refuses one with non-`#^prj` backlinks (daily notes and ref embeds here).
- It refuses non-list body content (the status-chip line, `See [[why_sase]].`, the bare
  `^outline`).
- Even if forced, it would nest all six tasks under a wrapper task in `sase_blog` whose block id
  would be `^0`, which is already used by the broccoli bullet. That is a sub-project in disguise,
  and the "full series" `^prj` would remain.

## 4. Requirement adjustments (explicitly flagged)

- **ADJ-1: "Everything from `sase_blog`" means tasks and planning, not prose.** All tasks, the
  `^prj`, Requirements, Outline, Screenshots, and later-post ideas live in `sase_blog.md`. The
  article lives in `sase_blog_contents.md`. `why_sase.md` is marked superseded.
- **ADJ-2: Rewrite the completion criterion.** Replace "full series" with the single-post
  outcome above, and keep `sase_blog`'s `^prj` identity.
  - Do not carry the child's 2026-08-24 date; it is past, so it is only noise.
  - Do not add a future date to `^prj` (§3).
  - Drop the child's `^prj` rather than restoring it as a second "publish" task.
- **ADJ-3: Delete the child, and rename its archive.** One project and one archive. Convert the
  five historical prose `[[sase_blog_0]]` links to plain text. In Obsidian, clicking an
  unresolved link creates an empty `sase_blog_0.md`.
- **ADJ-4 (new): Triage right after the move. These are your calls; recommendations below.**
  - **`^zk`:** cancel it, or rewrite it so zettel are ordinary notes, never project notes. It has
    rolled since 08-25. Its sibling "Flesh out…" was cancelled as "the same as the ^zk task".
    Architecture principles are parked as later-post material anyway.
  - **"Gather a list of references":** cancel it, folding its `harness_for_rsi` REF into
    Requirements. It has rolled 8 times, and citations are part of the `^intro-proposal` review.
  - **Keep** the two In Progress `#ref` reads, the July-post `#ref` (your rewrite baseline), and
    `^intro-proposal`. When you reach `^intro-proposal`, consider whether its next step is
    writing rather than "another research swarm".
- **ADJ-5 (optional; serves your "everything" requirement): Give the release a single owner.**
  Ctrl+Shift+M `job_2026` `^sase-blog` ("Release [[sase_blog]] post!") into `sase_blog`.
  - Its Depends-On `job_2026_apply_29#^prj` travels with it. As an ordinary task it blocks only
    itself, never the whole project.
  - Keep it in `job_2026` instead if you want it in the job-search view.
- **ADJ-6: No `sase_blog_1` placeholder.** Move "Future Blog Posts" to a `## Later Posts`
  section. Promote an idea to a project only when it passes the sub-project test in §2.
- **ADJ-7: Leave `sase_post_blog` as a separate project.**
  - It is post-launch product work, not writing.
  - Out of scope but worth knowing: its residents depend on `done/sase_done#^post-blog-prj`,
    which was completed 10-13, so the "after the post" gate is no longer enforced.
  - If you want the gate back, put one Depends-On `[[sase_blog#^prj]]` on its `^prj`. That
    blocks *all* its residents, so move any real bug fix out first.
- **ADJ-8: Tidy-ups.**
  - Fix the `[[șase_blog_0]]` typo.
  - Reparent the databricks job-fit ref to `job_2026`.
  - Drop `status: wip` from `sase_blog_contents.md`.
  - Optionally strip the inherited past `[scheduled:: 2026-08-24]` stamps on moved tasks; they
    are harmless.

## 5. Options compared

| Option | Verdict |
|---|---|
| **A. Fold down with Ctrl+Shift+M, then delete the child and rename the archive** | **Recommended.** One project, one archive, and no leftover stem. Costs about 25 minutes. |
| B. Fold down, then tombstone (cancel the child's `^prj`, keep the file) | **Fallback.** Leaves no unresolved links and keeps history beside the file. Leaves a struck ledger row (you can hand-delete it, which prunes it permanently) and the stem in pickers. |
| C. Reverse conversion (Ctrl+Alt+Shift+N on the child's `^prj`) | **Reject.** It refuses on children, backlinks, and body shape; if forced, it nests the work under `^0`. |
| D. Rename `sase_blog_0` over `sase_blog` | **Reject.** `[[sase_blog#^prj]]` links would silently retarget, and stale `[id::]`/`dependsOn` values would remain. `sase.md`, `sase_post_blog`, and `job_2026` already point at `sase_blog`. |
| E. Keep `_0`, cancel the parent | **Reject.** It keeps a "#0" name for a one-post project, against your stated preference. |
| F. Hand-build the merged note (gem) | **Reject.** It misses 15 Task Links and the id remapping. |
| G. Aliases as a redirect | **Reject.** They resolve neither block links nor note links (§3). |

## 6. Recommended solution: runbook (about 25 minutes, Obsidian on the Mac)

**0. Preconditions.**
- Ideally get bob-cli-81 fixed first. athena has failed every ~20 s since 05:38, its git is
  mid-merge with `UU bob.md`/`cash.md`, and `~/bob/_conflicts/` holds ~3,390 copies.
- Otherwise do everything on the Mac, CLI steps included, and accept that athena's local copies
  of touched daily notes may be quarantined. The Mac's version wins in place.
- Make sure no agent is editing these notes.

**1. Rewrite `sase_blog`'s `^prj`**, keeping `#hide` and `^prj`, and fix the `ș` typo:

```markdown
- [ ] #task #prj My SASE post, in my own voice, is live on https://sase.sh! [created::2026-06-11] #hide ^prj
```

**2. Move the six tasks.** In `sase_blog_0.md`, put the cursor on the first resident
(`^ref-structured-agentic-software-engineering`), press `5`, then Ctrl+Shift+M, and pick
`sase_blog`.
- The count skips `^prj` and carries subtrees.
- Block ids do not collide (verified).
- The links, embeds, `[id::]`, and `dependsOn` are all rewritten; you edit none of them by hand.
- Optional (ADJ-5): repeat the move for `job_2026` `^sase-blog`.

**3. Move the sections by hand.**
- Append the child's Requirements bullets under `sase_blog`'s Requirements. Both lists are
  chronological.
- Replace the Contents section with `Draft: [[sase_blog_contents]]`. The "tinkering" quote is
  already in the draft.
- Move the Outline, and turn "Future Blog Posts" into `## Later Posts`. The bare `^outline`
  anchor has no inbound links, so keep it or drop it.

**4. Reparent the satellites.**
- Set `parent: "[[sase_blog]]"` on `why_sase.md` (add "Superseded by [[sase_blog_contents]]"),
  on `sase_blog_0_legacy_notes.md`, and on the archive.
- Set the databricks ref to `[[job_2026]]`.
- Leave the three blog ref notes alone. Ref sync re-renders `parent` from the task's residence
  (`docs/highlights-ref-sync.md`). Until it runs, `bob ref doctor` reports `parent_mismatch`.

**5. Retarget the four `2026/20260619.md` links** from `[[sase_blog#^outline]]` to
`[[done/sase_blog_0_done#^outline]]`.

**6. Rename the archive *in Obsidian*** to `done/sase_blog_done.md`. Obsidian rewrites its 14
inbound links and the step-5 links. Then add `done_tasks: "[[done/sase_blog_done]]"` to
`sase_blog.md`.

**7. Plain-text the five historical prose links** to `sase_blog_0`: in `sase_blog`
(`^no-more-0-prj`, `^plan-blog-post`), `sase_blog_blockers` `^prj`, the archive's `^outline`
task, and the legacy note. Leave the `lib/chat` sidecars alone.

**8. Delete `sase_blog_0.md`** from Obsidian, so it goes to the trash, and git keeps its
history. By now it holds only `^prj` and emptied sections.

**9. Reconcile** (on the Mac):

```bash
bob projects sync --dry-run   && bob projects sync
bob task reconcile --dry-run  && bob task reconcile
```

Expected results:
- `sase_blog`'s Sub-projects line is gone. If it lingers, hand-delete it; the line is
  machine-owned and nothing regenerates it without a child.
- `^intro-proposal` is still Blocked on the two refs, now `sase_blog__…`.
- `^zk` and "Gather references" are still Blocked on their dates.
- No `#prj_is_blocked` tags appear.

Review any unrelated proposed changes in the dry runs before applying.

**10. Verify.**

```bash
cd ~/bob
grep -rn 'sase_blog_0#\^\|sase_blog_0__\|sase_blog_0_done' --include='*.md' . | grep -v '^./_conflicts'   # expect nothing
grep -rn '\[\[sase_blog_0' --include='*.md' . | grep -v '^./_conflicts'                                    # expect nothing
bob projects list | grep sase_blog        # sase_blog wip; no sase_blog_0
bob capture-targets | grep sase_blog      # no @sase_blog_0 route
bob ref doctor                            # clean after the next ref sync
```

Also open today's 15:05 BLOG Pomodoro and confirm its links now point at `sase_blog#^…`.

**11. Triage (ADJ-4)** using the Task Card cancel with a Cancel Log reason. **12. Close
`^no-more-0-prj`.**

**Fallback (tombstone, if you would rather have zero unresolved links):** skip steps 6–8. Cancel
the child's emptied `^prj` with the log entry "Merged into [[sase_blog]]: one post, one project."
Keep the archive's name and `done_tasks` on the tombstone, and hand-delete the struck ledger row
if it bothers you.

**Target shape of `sase_blog.md`:**

```markdown
---
parent: "[[sase]]"
type: "[[project]]"
status: wip
done_tasks: "[[done/sase_blog_done]]"
---
- [ ] #task #prj My SASE post, in my own voice, is live on https://sase.sh! #hide ^prj

## Tasks
- [ ] #task Re-frame blog post as a "goodbye" to SASE?!
- [ ] #task #ref …structured_agentic_software_engineering… ^ref-structured-agentic-software-engineering
### Next & In Progress
- [/] #task #ref …sase_launch_post_introduction… [id:: sase_blog__ref-sase-launch-post-introduction] …
- [/] #task #ref …sase_launch_post_outline…      [id:: sase_blog__ref-sase-launch-post-outline] …
### Blocked
- [?] #task Review … ^intro-proposal          (Depends-On the two refs)
- [?] #task Release the post! ^sase-blog      (only with ADJ-5; Depends-On job_2026_apply_29#^prj)
### Done & Canceled
…
## Requirements        (June bullets, then the child's Jul–Oct bullets)
## Screenshots
## Contents            (Draft: [[sase_blog_contents]])
## Outline
## Later Posts         (former "Future Blog Posts"; promote only when real)
```

## 7. Open questions for Bryan

1. Is "announced" part of done, or just "live"? Is the new post an in-place rewrite of the July
   URL (the 10-07 outline research's recommendation), or a new post, with the 15-minute install
   post moved to Getting Started (the June outline note)? Either way the `^prj` wording above
   holds; only the announcement half changes.
2. Should the job-gated release task move into `sase_blog` (ADJ-5), or stay in the job-search
   view?
3. Cancel or rewrite `^zk` and "Gather a list of references" (ADJ-4)?
4. Do you still want `sase_post_blog` gated on the post (ADJ-7)?

## Evidence

- **Vault, read-only, re-verified by the lead on 2026-10-15:**
  - `sase_blog.md`, `sase_blog_0.md`, `sase_blog_contents.md`, `why_sase.md`,
    `sase_blog_0_legacy_notes.md`, `done/sase_blog_0_done.md`, `sase_post_blog.md`;
    `job_2026.md:24`;
  - `ref/blogs/structured_agentic_software_engineering.md` (`source_url`, `published`
    2026-07-08);
  - a vault-wide `sase_blog_0` grep, `2026/20260619.md`, and `2026/20261015.md`;
  - `.obsidian/app.json`; git commits `b018ccd4` / `5a08a730` (`sase_blog_1`);
  - `bob vault-sync status --json`.
- **bob-cli:**
  - `docs/projects.md` (sync rules, Sub-projects ledger, External Names);
  - `docs/highlights-ref-sync.md` (ref `parent` from residence); `docs/ref.md`
    (`parent_mismatch`);
  - `src/native/collect_done/transform.rs` (`archive_relative_path`), `collect_done/mod.rs`
    (`DEFAULT_THRESHOLD = 10`).
- **bob-plugins `bob-navigation-hotkeys`:**
  - `240-cancel-and-lanes.js` (`discoverMovableObsidianTaskTargets`,
    `prepareTaskMoveBlockIdentities`);
  - `250-task-move.js` (link rewriting, per cld and cdx);
  - `665-plugin-project-conversion.js` (reverse-conversion preflights, per cld, cdx, and grk).
- **Memory:**
  - `obsidian.md`;
  - `decisions:projects-block-from-prj-line`, `decisions:subprojects-inherit-project-blocking`,
    `decisions:unblocked-tasks-are-offered`;
  - glossary: Project Note, Project Task, Task Link, and Task Dependency Link.
- **Bead:** `bob-cli-81` (athena vault-sync loop).
- **Researcher reports in this directory:** `__cdx` (acceptance criteria, archive-path
  derivation), `__cld` (link counts, tooling line references, the sync bug, the July live post),
  `__grk` (reverse-conversion failure modes, the `^zk` over-structuring risk), and `__gem` (the
  project-vs-manuscript split, today's Pomodoro inventory).
