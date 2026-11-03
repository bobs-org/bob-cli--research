# Move, merge, and split tasks: `>` capture, "merged into", and Ctrl+Shift+T

*Researcher: cld · 2026-11-03 · scope: bob-cli, bob-plugins, Bob Mac Capture*

## TL;DR

Bryan's request adds the two task "refactorings" Bob is missing. Bob can already
**move** a task (`bob task move`, Ctrl+Shift+M, capture move bullets). It cannot
**merge** a task into another task (fold it in as notes), and it cannot **split**
a bullet out into a new task. In code-refactoring terms these are *Move*,
*Inline*, and *Extract*. Treated as one family, they get a small, consistent
grammar.

The plan is a good one. The `>` syntax fits capture's "`@` says where" rule,
"merged into" fits the relation label-effect pattern that already ships three
times (cancel, complete, successor), and mentions are the right back-pointer for
split. I would build it with these principles and adjustments:

1. **The destination decides the shape.** `@a+x @b+y > @c` *moves* tasks (a note
   holds tasks). `> @c+z` and `> @c+z#drawer` *merge* them (a task holds notes).
   One arrow, two verbs, and the destination token you already know how to type
   decides which one runs.
2. **A merge never deletes; it cuts and retires.** The source's authored children
   move into the target under one title bullet, with link repair from the
   task-move engine. The source line stays as a one-line cancelled tombstone that
   carries `🪢 LINKS: merged into [[target]]`. Its dependents now wait on the
   target, and its live Task Link today goes to the target.
3. **`> @c#drawer` without a task means the project's `^prj` drawer** (an H2
   section). It is refused on area notes, which have no task to merge into.
   *(Adjustment: the request would have converted and moved the tasks with no
   tombstone.)*
4. **"merged into" becomes a new label effect**, `relations.merge_labels`
   (default `[merged into]`). Committing it through Ctrl+Shift+L or capture `~`/`~~`
   performs exactly the merge `>` performs. The inverse display `merged from`
   already exists in `NAMED_PAIRS`.
5. **Ctrl+Shift+T splits bullets in place, in one editor transaction.** New
   sibling tasks are created right below the source task. The bullets are replaced
   by `- ✂️ Split out: [[#^a|A]] • [[#^b|B]]`, whose status rings update live. The
   **new** tasks get the `💬 mentions` back-pointers, not the old one. *(This
   corrects the request's wording.)* Drawer entries are splittable too.
6. **CLI:** `bob task move <TASK>… --to <NOTE>` (multi-source),
   `bob task merge <TASK>… --into <TASK[#drawer]>`, and
   `bob task split <TASK> (-m TEXT | -n N | -D DRAWER)…`. `>` is the capture
   spelling of the first two.
7. **One engine per operation.** Merge lives only in Rust: capture, the CLI, and
   the Obsidian merge label all call it, and nav shells out to
   `bob task merge -o -f json`. Split is twinned. Rust serves the CLI, JS serves
   the same-note editor transaction, and shared vectors pin the bytes.
8. **Sequencing:** ship split first (no grammar change), then the merge engine with
   the label and CLI, then `>` after the multi-target `grammar` phase
   (`bob-cli-gm`) lands.

Watch-outs: Ctrl+Shift+T is Obsidian's default **Undo close tab** on Linux. An
unquoted `bob capture @a+x > @c` is a shell redirect that also runs Ensure Next
on `^x`. The grammar revision must be coordinated with the in-flight epics.

---

## 1. What exists today (grounding)

| Area | Today | Source |
| --- | --- | --- |
| CLI move | `bob task move <SOURCE> <DEST> (-b ID \| -m TEXT)…` takes **one** source note and moves only open, top-level, non-`^prj` tasks. The destination must be an area or a `wip`/`waiting` project and the task lands at the end of `## Tasks` intake. Links, `[id::]`, and `[dependsOn::]` are repaired vault-wide (including `done/` and daily notes). The command takes a lock, pre-syncs, makes one git commit, and supports `--dry-run`. | `docs/task-move.md`, `src/native/task_move/plan.rs` (`plan_task_move(snapshot, MoveRequest{source, dest, selectors, allow_closed})`) |
| Obsidian move | `N<Ctrl+Shift+M>` moves the current task plus N more to a picked note, focuses the destination, and never advances the `]s` walk. The JS planner is `planTaskMoveAcrossFiles`, which rewrites links across files. | bob-plugins `250-task-move.js`, decision `task-move-never-advances-the-walk` |
| Capture move | Only inside a *new project-note* item: `- ^id` / `- :id` move a task from the **parent** note. `- ^route:id` is **reserved** with `move_bullet_cross_note` ("moving from another note is not supported yet"). | `docs/capture.md` "Moving parent tasks in" |
| Notes under tasks | `@route+id <note>` files a note. A note-less `@route+id` + bullets files several notes, where ALL-CAPS bullets with children merge into drawers. `@route+id#drawer` uses exact key matching and creates the drawer on demand. On a `^prj` task the drawers are the note's `##` sections, and a missing one is created in Title Case. | `docs/capture.md` "Sub-bullets under existing tasks"; decision `capture-bullets-mirror-the-task-block` |
| Section bullets | `@note#Prefix` writes a plain bullet under a heading. It uses prefix and slug matching, falls back to the zeroth section, and **never creates** the heading. | `docs/capture.md` "Section bullets" |
| Relation label effects | `relations.cancel_labels` (Bryan: `duplicate of`, `superseded by`), `complete_labels` (`implemented by`, `verified by`), and `successor_labels` map to `enum LabelEffect {Cancel, Complete, Successor}`, one effect per label. They fire once, at commit, through explicit gestures (capture `~`/`~~`, Task Card `l`/`⇧L`, counted batches), never through reconcile, rename, or hand edits. | `docs/task-relations.md` §§17–20, `src/native/config/relations.rs` |
| "merged into" | Bryan's chezmoi config already has `# - merged into` commented out under `cancel_labels`. `inverse.rs` `NAMED_PAIRS` already has `("merged into", "merged from")` **and** `("split from", "split into")`. The vault has 0 uses today; `superseded by` (15) and `implemented by` (33) are well used. | `~/.config/bob/config.yml`, `bob relations list -a` |
| Mentions | If S's own text (title, notes, logs) contains a block link to task T, then T's generated LINKED FROM line gains `[[S]] (💬 mentions)`, and S gets a silent `^id` if it needs one. Links on Depends-On, BLOCKS, LINKS, and LINKED FROM lines never count. | `docs/task-relations.md` §19 |
| Link rings | bob-ledger-tools draws a live status ring before **every** rendered block link to a `#task`, so `[[#^a\|Alias]]` shows ◯/◉/✓ as the task progresses. | `docs/task-link-marks.md` |
| Split vocabulary | "Split"/"merge" already name **Pomodoro** operations: Ctrl+S splits a merged Pomodoro by type through a Tab-mark picker, and capture has "Splitting/Merging Pomodoros". | nav `652-pomodoro-split.js`, `docs/capture.md` |
| In-flight grammar | `bob-cli-gm` (capture_multi_target, status wip) makes a run of adjacent `@route+id` markers fan a line out to every task. Its `split_edges = refuse` answer turns `@a+x note @b+y` into an error. Move bullets already document `grammar: 8`. | plans `202611/capture_multi_target.md` |
| Keymaps | nav defaults: Ctrl+Shift+M (move), Ctrl+Shift+L / Ctrl+Shift+Alt+L (Links / Linked from), Ctrl+Shift+B / Ctrl+Shift+Alt+B, Ctrl+Shift+P, Alt+F, Ctrl+Alt+F/J/K. Bryan's `hotkeys.json` binds Alt+T and Ctrl+L but **does not override Ctrl+Shift+T**. | nav `490-plugin-lifecycle.js`, `~/bob/.obsidian/hotkeys.json` |

Two facts shape the design more than any others:

- **The move engine already repairs links for blocks that change files.** A merge
  that relocates the source's children is "a move of children" plus a cancel, so
  most of the hard machinery already exists.
- **Label effects are already the way relations do things.** A fourth effect fits
  without new concepts. A *dedicated* merge gesture would be a second way of saying
  the same thing.

## 2. Framing: three refactorings of a task outline

| Refactoring | Bob operation | What changes identity | Back-pointer |
| --- | --- | --- | --- |
| **Move** | task → another note's task list | nothing (same `^id`, links repaired) | none needed |
| **Merge** (inline) | task → notes inside another task | the source **retires** (cancelled tombstone) | `🪢 LINKS: merged into [[T]]` on S, so T's LINKED FROM shows *merged from* |
| **Split** (extract) | note bullet(s) → new task(s) | new tasks are **born** | the `✂️ Split out:` line in S's text, so the new tasks show *💬 mentioned in S* |

This table answers "is this a coherent feature?": yes, these are the three
operations of an outline editor whose nodes are tasks and notes. It also answers
"what must be reliable?": identity. Moving keeps identity, merging retires it,
and splitting mints it. Every link, dependency, Task Link, and mention must still
resolve afterwards.

## 3. Critique of the request

### What is right

- **The `>` operator is mnemonic and free.** No capture grammar rule uses `>` today
  (checked in `src/native/capture_language/`). It reads like "put these there", and
  it sits outside the already crowded sigil set (`@ # % & * ~ ! : ^ + = $ s:`).
- **Building on multi-target runs is the right reuse.** The `bob-cli-gm` run
  recognizer is exactly the "source list" `>` needs. Better still, after that epic,
  `@a+x > @c+z` is a *refused* shape (`split_capture_targets`: target markers at
  both edges). The merge spelling therefore claims a line that is otherwise an
  error and breaks nothing. Only `@a+x > @c` (a bare-note trailing token) changes
  meaning: it used to file the note text "> @c" under `^x`.
- **Not deleting merged sources is essential.** Links from Pomodoro history,
  dependencies, relations, and mentions all point at the source. A tombstone keeps
  every one of them resolvable.
- **Merge as a relation label is consistent** with how Bryan already retires tasks
  (`superseded by` cancels; `implemented by` completes).
- **Mentions are the right back-pointer for split.** They need no new relation,
  no new managed line, and no new gesture, and the status rings make the forward
  pointer live.

### What needs adjusting (and why)

- **`@c#drawer` names something that does not exist for most notes.** A drawer is
  an ALL-CAPS child of a *task*. For a plain note, `@c#X` already means a
  **section bullet** under a heading, with prefix matching and no creation. The
  coherent reading is the project's `^prj`: Bob already treats a project note's
  `##` sections as `^prj`'s drawers, creating missing ones in Title Case. Area
  notes have no `^prj`, so there is no task for "merged into" to point at.
- **"Converted to notes and moved" (no task) and "merged" (task) should not have
  different source fates.** If `> @c#drawer` deleted the source, every inbound link
  would dangle or land on a non-task bullet. Daily-note Task Links would then point
  at a plain bullet, which breaks ledger semantics. Making `> @c#drawer` a merge
  into `^prj` gives one fate for every task → notes conversion.
- **Merge needs explicit rules for dependencies, today's plan, and nested tasks.**
  "Auto-cancel" alone does the wrong thing to dependents. Cancel's recovery engine
  would *unblock* tasks that were waiting on work that is now inside T and still
  not done.
- **The mentions land on the new tasks, not the old one.** The inline links live in
  the old task's text, so the *targets* (the new tasks) get
  `[[old]] (💬 mentions)`. The old task's forward view is the ✂️ line itself,
  with live rings.
- **Ctrl+Shift+T collides with Obsidian's default "Undo close tab"**
  (Ctrl/Cmd+Shift+T). nav binds `Ctrl`, not `Mod`, so the collision happens on
  athena and apollo (Linux), not on the Mac. It is fixable in one line of
  `hotkeys.json`.
- **`>` is a shell redirect.** `bob capture @inbox+x > @db` writes stdout to a
  file named `@db`. It also *runs* `bob capture @inbox+x`, which is "Ensure Next and
  relocate its link": a silent side effect. This is why the CLI needs real verbs
  (`--to`, `--into`) and the docs must always quote.

### Would I take a different approach?

At the architecture level, no. I would sharpen three things:

1. **State the rule once, as "the destination decides the shape",** and drive
   capture, the CLI, and (later) the Ctrl+Shift+M drill-down from it.
2. **Implement merge exactly once, in Rust,** and have Obsidian call it. Merge is a
   multi-note graph rewrite (T, S, dependents, the daily note, link repair), and a
   JS twin would double the hardest code in the feature. Split is the reverse case:
   one note, one editor transaction, undo matters, so it gets a JS implementation
   with shared byte vectors.
3. **Ship split first.** It is the highest-frequency gesture (FUTURE WORK and loose
   notes become tasks every day), needs no grammar change, and has the smallest
   blast radius.

## 4. Requirement adjustments (explicit callouts)

| # | Request said | I recommend | Why |
| --- | --- | --- | --- |
| **A1** | `@a+x > @c#drawer` converts tasks to notes in "that drawer" | `> @c#drawer` ≡ `> @c+prj#drawer`: merge into the project note's `^prj` drawer (an H2 section, created in Title Case). On an area note, refuse with `merge_needs_task`. | Drawers belong to tasks, and only project notes have a note-level task. This reuses the shipped `^prj`-section drawer resolver unchanged. |
| **A2** | Converted tasks are "moved" (gone from the source) | Every task → notes conversion is a **merge**: the source is cancelled with `merged into` | Keeps every inbound link valid, gives one source fate, and `bob task archive` sweeps tombstones into `done/` nightly. |
| **A3** | "Should not delete the source tasks" | The source **line** stays as a cancelled tombstone. Its **authored children are cut** into T (with link repair). Managed lines (logs, LINKS, Depends-On) stay on S. | Content lives in one place (no stale duplicate drawers), history stays where it was written, and nothing is lost: T is written before S. |
| **A4** | (unstated) | S's **dependents re-point to T**. S's own **prerequisites are not transferred**; they are reported with a hint. | Cancel would wrongly unblock dependents, since the work is not done, just relocated. Transferring prerequisites would silently block T. |
| **A5** | (unstated) | S's live Task Link under today's **open** Pomodoros is **handed to T** if T has none and can hold one. Otherwise it is pruned. Closed Pomodoros keep history. | The plan slot follows the work, matching how a move keeps its link. *Open question Q1.* |
| **A6** | "old tasks … given linked-from mentions" | The **new** tasks get `[[old]] (💬 mentions)`. The old task carries the visible `✂️ Split out:` line with live rings. | That is how §19 mentions are defined: the text holder is the source. |
| **A7** | "merged into" configurable | New `relations.merge_labels`, default `[merged into]`. The first entry is the label that `>` and `bob task merge` write. Extra entries are synonyms. `[]` disables only the *label trigger*. | Unlike cancel and complete, merge has a first-class operator that must always write *some* label. |
| **A8** | Ctrl+Shift+T | Keep it, and add `"workspace:undo-close-pane": []` (or a rebind) to the vault's `hotkeys.json` | It is the default "Undo close tab" on Linux. Without the override the two commands compete. |
| **A9** | Split "into new tasks" (placement unstated) | New tasks are inserted **directly below the source task's block**, in bullet order, and the cursor lands on the first. Compose with `N<Ctrl+Shift+M>` to send them elsewhere. | One note gives one transaction and one undo. Composition beats a destination picker in the hot path. |
| **A10** | "top-level bullets" | First-level plain notes **and drawer entries** (e.g. `FUTURE WORK` items) | Drawer entries are where most would-be tasks live. |
| **A11** | (`>` scope) | v1 `>` lines take **no** other markers (`s:`, `$`, `#type`, `%c`, `&*~`, `!`) and **no** child bullets. `@a+x#drawer` on the *left* is reserved. | Keeps the operator crisp and errors local. The reservation leaves room for the §11 extension. |
| **A12** | (unstated refusals) | Refuse closed, recurring, `^prj`, and open-subtask-bearing sources, closed or archived targets, and targets inside the source | Each of these has no unsurprising meaning. Teaching errors name the fix. |

## 5. Capture: the `>` line

### 5.1 Recognition

A **`>` line** is one physical parent line of exactly this shape, after
whitespace tokenization:

```text
<source run> ">" <destination>
<source run>  := one or more adjacent @route+block-id markers   (the bob-cli-gm run)
<destination> := @route | @route#drawer | @route+id | @route+id#drawer
```

- **Claiming rule.** A parent line whose leading run is immediately followed by a
  standalone `>` token is a `>` line. It is claimed *before* the multi-target
  fan-out and the `split_edges` check. A malformed tail is then a **teaching
  error**, never silently filed as a note: `@a+x > @c oops` →
  `move_destination_text`.
- **Escape.** `@a+x \> quoted` keeps today's meaning (a note starting with `>`).
  The draft-rewrite tests should cover it.
- **Not a `>` line:** a `>` anywhere else (`Called Bob > 3 times @a+x`), a
  line-initial `> quote`, and a `>` inside inline code. All keep their meaning.
- **Forced destinations** (`-r`, `--task`, `--drawer`) keep `@…` literal, exactly
  as today.
- **Sources** must be `+` markers. `@a:x`, `^a:x`, and `@a^x` on the left get
  `move_source_marker` ("name tasks to move with @route+id"). Duplicates reuse
  `duplicate_capture_target`. Per-member `#drawer` and `!` are refused (`#drawer`
  is reserved, see §11).

### 5.2 What the destination means

| Destination | Operation | Sources become | Uses engine |
| --- | --- | --- | --- |
| `@c` | **Move** to `c.md`'s `## Tasks` intake | the same tasks (IDs and children intact) | `plan_task_move` once per source note, in typed order, on staged snapshots |
| `@c+z` | **Merge** into `^z` at its plain-child anchor | one title bullet each, carrying their children | new `plan_task_merge` |
| `@c+z#drawer` | **Merge** into `^z`'s drawer (exact key, created on demand, near-duplicate refusal, `#"QUOTED"` forces) | same, inside the drawer | `plan_task_merge` + existing drawer resolver |
| `@c#drawer` (c is a project note) | **Merge** into `^prj`'s drawer: an H2 section, created in Title Case | same | identical to `@c+prj#drawer` |
| `@c#drawer` (c is not a project) | refused: `merge_needs_task` | — | — |

Move keeps every `bob task move` rule: an area or `wip`/`waiting` project
destination, top-level open non-`^prj` sources, link repair, and freshness stamps
like Ctrl+Shift+M. It adds the A9 rule from capture move bullets: a
non-Blocked task cannot move into a Blocked-at-birth or Blocked project. A
source that already lives in `c.md` is refused (`move_same_note`) rather than
silently skipped.

### 5.3 Editor assist (`capture-parse`, `capture-complete`, `capture-rewrite`)

| Draft (cursor `\|`) | Assist |
| --- | --- |
| `@inbox+bench >\|` / `@inbox+bench > \|` | incomplete; `needs: ["move_destination"]`. The completion offers the **same list Ctrl+Shift+M shows** (`list_task_move_destinations`: areas and open projects, inboxes excluded), with a `+` drill-in hint |
| `… > @d\|` | routes |
| `… > @db+\|` | that note's open tasks (`@route+` ranking), each row labelled `⤵ merge into` |
| `… > @db+upgrade#\|` | that task's drawers in document order, then catalog recents, then a create row (the existing drawer menu) |
| `… > @proj#\|` (project note) | `^prj`'s `##` sections as drawers |
| `@inbox+\| > @db` | open tasks of `inbox` (the source picker, filtered to movable rows for move and mergeable rows for merge) |

`capture-parse` reports `mode: "task_move" | "task_merge"`, spans `move_source`
(per member), `move_arrow`, and `move_destination` (with the existing `drawer`
sub-span), plus an additive object:

```json
"move": {
  "operation": "merge",
  "sources": [{"start": 0, "end": 12, "route": "inbox", "block_id": "bench"}],
  "arrow": {"start": 13, "end": 14},
  "destination": {"start": 15, "end": 39, "route": "db", "block_id": "upgrade", "drawer": "future-work"}
}
```

Bob Mac Capture already renders spans by kind and stays a thin client. The only
optional Mac change is a footer verb (**Move** / **Merge**) and SF Symbols
`arrow.right` / `arrow.triangle.merge`. Until then the footer falls back to
**Capture**.

### 5.4 Output (human, dry-run, JSON)

Human output names the task, says the verb, and states each consequence:

```text
→ would move 2 tasks to db.md · ## Tasks
  ◯ Benchmark logical replication   inbox.md:14 → db.md:42
  ◉ Test pg_dump restore            work.md:88  → db.md:43
  would repair 6 links in 3 notes
```

```text
⤵ merged 2 tasks into “Upgrade Postgres to 17” (db.md) · FUTURE WORK
  ⊘ “Benchmark logical replication” · Next → Cancelled · 3 notes · its link → “Upgrade Postgres to 17”
  ⊘ “Test pg_dump restore” · Ready → Cancelled · 1 note
  ⛓ “Cut over prod” now waits on “Upgrade Postgres to 17”
  ⚠ “Benchmark logical replication” waited on “Provision staging box”; “Upgrade Postgres to 17” does not · add &infra:staging to keep waiting
```

JSON (additive, `schema_version` unchanged): `moves[]` reuses the
`bob task move` `MoveRecord` shape. `merges[]` is
`{source:{path,line,block_id,text}, target:{path,line,block_id,text,drawer?},
label, previous_status, previous_status_name, folded_lines,
link:"handed_off"|"pruned"|"none", dependents_repointed[], prerequisites_left[],
repaired_files[], message}`. A dry run equals the real result except for
`dry_run`, as for move bullets (MV1).

### 5.5 Refusals (codes and copy)

| Code | Message (illustrative) |
| --- | --- |
| `move_destination_text` | `a > line takes one destination; put the note on its own item` |
| `move_line_marker` | `a moved or merged task keeps its own schedule, priority, and type; remove s:2` |
| `move_line_children` | `> moves whole tasks; file notes with a separate @db+upgrade item` |
| `move_source_marker` | `` name tasks to move with @route+id; `@inbox:bench` would link it `` |
| `move_source_drawer` | `` moving a drawer's entries is reserved; split them with Ctrl+Shift+T or bob task split `` |
| `merge_needs_task` | `` areas have no ^prj to merge into; pick a task (@home+<id>#ideas) or move with > @home `` |
| `merge_into_itself` | `` ^bench cannot merge into itself `` |
| `merge_target_inside_source` | `` ^upgrade is nested under ^bench; merge ^bench somewhere else or move ^upgrade out first `` |
| `merge_target_closed` | `` “Upgrade Postgres to 17” is Done; reopen it or merge into an open task `` |
| `merge_source_closed` | `` “Benchmark…” is already Cancelled; only open tasks merge `` |
| `merge_source_recurring` | `` “Water plants” repeats; cancel it with Obsidian Tasks first `` (cancel's copy) |
| `merge_source_project` | `` ^prj is a project's own task; merge its tasks, or promote/reverse the project `` |
| `merge_source_open_subtasks` | `` “Benchmark…” has 2 open subtasks; move or close ^tune first `` |
| `merge_dependency_cycle` | `` “Cut over prod” would wait on “Upgrade…”, which already waits on it `` |

## 6. Merge semantics (the one rule)

> **Merging S into T** writes T first: S's description becomes one note bullet at
> T's anchor (or drawer), and S's authored children are nested beneath it with
> links repaired. Bob then re-points S's dependents to T, hands S's live Task Link
> today to T, and writes S last: S is cancelled with `🪢 LINKS: merged into [[T]]`.

### 6.1 What happens to each thing

| Thing | Fate | Reason |
| --- | --- | --- |
| S's task line | `[-]` + `[cancelled:: today]`; `^id` kept | It becomes the tombstone, and every link to S still resolves |
| S's description | becomes the title bullet in T, stripped of checkbox, `#task`, inline fields, and `^id` (Bob's existing description extractor) | Provenance by title, with no extra links (avoids a reverse mention) |
| S's authored children (notes, drawers, closed nested tasks) | **cut** under the title bullet, relative indentation kept. Block IDs inside move with link repair (the `plan_task_move` fragment repair) | One home for the content, and anchors keep resolving |
| S's open nested tasks | refuse (`merge_source_open_subtasks`) | Turning a live task into a note would destroy it |
| S's Schedule / Work / Rotten / Cancel logs | stay on S. An existing `❌ CANCEL LOG` gets `*date* — 🪢 merged into [[T]]` prepended (cancel CL4) | They are S's history |
| S's LINKS (outgoing relations) | stay on S, plus the new `merged into` entry | Relations are history (§2) |
| S's Depends-On (S's prerequisites) | stay on S as history; **not** copied to T; reported in `prerequisites_left[]` with an `&` hint | Copying would silently block T |
| Tasks that depend on S | their Depends-On link is **re-pointed to T** (dedupe; `Y == T` drops the edge and may recover T; a cycle refuses) | They were waiting on that work, and it is not done |
| Relations, mentions, and history links pointing at S | untouched | The tombstone's `merged into` chip forwards the reader |
| S's live link under today's **open** Pomodoros | rewritten in place to T if T has none and is linkable (lane rules as for any existing-task link); otherwise pruned exactly like cancel CL4 | The plan slot follows the work |
| S's links under closed Pomodoros and other days | untouched | They record what was worked on then |
| T's status, schedule, and priority | unchanged (except the lane rise a hand-off link causes under `task-lanes-are-sticky`) | Minimal side effects |
| T's LINKED FROM | gains `[[S]] (merged into)`, which displays as **merged from** | Existing inverse pair |

Idempotence: re-running a merge whose `merged into` edge already exists is
`Unchanged` and writes nothing (as for cancel labels). Reconcile stability:
`merge → bob task reconcile` must be a no-op. Make this a conformance vector.

### 6.2 Worked example

Before (`inbox.md`; derived `[id::]`/`[dependsOn::]` fields omitted):

```markdown
- [*] #task Benchmark logical replication [created::2026-10-28] ^bench
  - Try pgbench at 10k TPS
  - REQUIREMENTS
    - staging box with 64 GB
  - 🗓️ **SCHEDULE LOG**
    - *2026-10-30* — moved to Friday
- [?] #task Cut over prod [created::2026-10-28] ^cutover
  - ⛓️ **DEPENDS ON:** [[#^bench]]
```

`db.md`:

```markdown
- [ ] #task Upgrade Postgres to 17 [created::2026-10-20] ^upgrade
  - FUTURE WORK
    - Try logical replication
```

Today's daily note has `- [[inbox#^bench]]` under an open `BUILD` Pomodoro.

Capture: `@inbox+bench > @db+upgrade#future-work`

After, `db.md`:

```markdown
- [*] #task Upgrade Postgres to 17 [created::2026-10-20] ^upgrade
  - 🪢 **LINKED FROM:** [[inbox#^bench]] (merged into)
  - FUTURE WORK
    - Try logical replication
    - Benchmark logical replication
      - Try pgbench at 10k TPS
      - REQUIREMENTS
        - staging box with 64 GB
```

`inbox.md`:

```markdown
- [-] #task Benchmark logical replication [created::2026-10-28] [cancelled:: 2026-11-03] ^bench
  - 🪢 **LINKS:** merged into [[db#^upgrade]]
  - 🗓️ **SCHEDULE LOG**
    - *2026-10-30* — moved to Friday
- [?] #task Cut over prod [created::2026-10-28] ^cutover
  - ⛓️ **DEPENDS ON:** [[db#^upgrade]]
```

The daily note's `BUILD` child becomes `- [[db#^upgrade]]`, and "Upgrade
Postgres" rises to Next because it is now linked. Nightly `bob task archive`
moves the tombstone into `done/` and repairs `db.md`'s mirror link.

### 6.3 The `merged into` label effect (`relations.merge_labels`)

```yaml
relations:
  cancel_labels: [duplicate of, superseded by]   # remove "# - merged into" from here
  complete_labels: [implemented by, verified by]
  # Committing a link with one of these labels merges the task the label is
  # phrased from into the target ("S merged into T"): S's notes move under T,
  # S's dependents wait on T, and S is cancelled. The first entry is the label
  # `>` and `bob task merge` write. Empty disables only the label trigger.
  merge_labels: [merged into]
```

- `LabelEffect::Merge` joins Cancel, Complete, and Successor, and the
  one-effect-per-label overlap rule now covers four lists.
- **Fires on exactly the cancel-label gestures (CL1):** capture `~` / `~~`, the
  Links and Linked-from stages, and counted or marked batches. It **never** fires
  on reconcile, `bob relations rename` (which warns as in CL5), hand edits, or
  relabeling *away*. Relabeling *into* a merge label on an already-cancelled S
  only writes the link.
- **Directions:** `@inbox+bench ~db:upgrade|"merged into"` ≡
  `@inbox+bench > @db+upgrade`.
  `Unify DB upgrade work ~~inbox:bench|"merged into" ~~inbox:pg17|"merged into"`
  creates an umbrella task and folds both old tasks into it. `New task ~old:id|"merged into"`
  is refused with `relation_merges_new_task` (it would be born merged), with a
  `~~` hint mirroring cancel's `new_task` verdict.
- **Indication** (follows CL6: verb plus glyph, calm, never color alone): the row
  meta and `relations list` show `⤵ merges` / `⤵ merges source`. The consequence
  strip reads `⤵ Merges “S” into “T” · moves 3 notes · cancels “S” · its
  Pomodoro link goes to “T” · 1 dependent now waits on “T”`, the Return hint is
  `↵ link & merge`, and the batch banner is `⤵ Merges {N} tasks — ↵ again to
  confirm`. A hand-edit hint reads `⤵ “merged into” merges only from the Links
  stage or capture · this task stays open`.
- **Contracts:** `capture-complete` relation-label rows gain
  `merges_source: true`, and the response gains `relation_merge: {source, target,
  verdict, message, consequences}` (resolving two tasks only, never scanning the
  vault). `capture-parse` label spans gain `merges_source`. Committed
  `relation_updates[]` rows gain `merge_effect`. `bob relations list` adds
  `merges_source` and a header `· N merge`.
- **Drawer from Ctrl+Shift+L (v1.1 nicety):** when the label is a merge label, the
  confirm strip shows `into “T” · notes` and `Tab` cycles T's drawers, ending with
  `+ new`. v1 always lands at the plain-child anchor.

## 7. Split: Ctrl+Shift+T

### 7.1 Where it works

| Cursor | Ctrl+Shift+T |
| --- | --- |
| Anywhere in a **first-level plain note** of a task (including its nested lines) | split that note (and its subtree) into one new task |
| Anywhere in a **drawer entry** (`FUTURE WORK` → item) | split that entry |
| `N<Ctrl+Shift+T>` | it plus the next N sibling splittable bullets (managed lines skipped), matching `N<Ctrl+Shift+M>` |
| Visual selection | every first-level note or drawer entry the selection touches |
| The **task line** or a **drawer title** | picker titled `Split “Upgrade Postgres to 17”`: rows are splittable bullets (a drawer title preselects its entries). `Tab` marks, `Enter` splits the marked rows (else the highlighted one), `Esc` cancels. Footer `↵ split · ⇥ mark · esc`. This mirrors the Split-Pomodoro picker |
| LINKS, LINKED FROM, Depends-On, BLOCKS, any log, a Pomodoro line, or prose outside a task | notice, no edit (`Depends-On is managed — nothing to split`) |

### 7.2 What it writes (one note, one transaction, one undo)

Before:

```markdown
- [ ] #task Upgrade Postgres to 17 [created::2026-10-20] ^upgrade
  - Ping Alice about the cutover window
  - Write the rollback runbook
    - include pg_dump timing
  - FUTURE WORK
    - Try logical replication
```

`1<Ctrl+Shift+T>` on "Ping Alice…":

```markdown
- [ ] #task Upgrade Postgres to 17 [created::2026-10-20] ^upgrade
  - ✂️ Split out: [[#^ping-alice-cutover|Ping Alice about the cutover window]] • [[#^write-rollback-runbook|Write the rollback runbook]]
  - FUTURE WORK
    - Try logical replication
- [ ] #task Ping Alice about the cutover window [created::2026-11-03] ^ping-alice-cutover
  - 🪢 **LINKED FROM:** [[#^upgrade]] (💬 mentions)
- [ ] #task Write the rollback runbook [created::2026-11-03] ^write-rollback-runbook
  - 🪢 **LINKED FROM:** [[#^upgrade]] (💬 mentions)
  - include pg_dump timing
```

Rules:

- **New task line:** `- [ ] #task <bullet text> [created::today] ^<id>`. This is
  exactly what a capture-created task in that note gets, so it enters the NEW
  review tier like any new task. An existing `[created::]` on the bullet is kept,
  since the idea is older than the split. An existing `^anchor` on the bullet
  **becomes** the task ID, so links to it now resolve to a task. Otherwise the ID
  is minted with `mint_block_id` against the note's used IDs. S's explicit
  `[type::]` is copied, because the work was S's kind. Priority, schedule, and
  freshness are not copied.
- **Children travel unchanged.** An ALL-CAPS child with notes naturally becomes a
  drawer of the new task.
- **Placement:** directly after S's whole block, at S's indentation, in bullet
  order. In a project with reconcile's status-group headings, reconcile regroups
  later.
- **Replacement line:** each *contiguous run* of split bullets is replaced, at the
  run's first position, by one prose bullet:
  `- ✂️ Split out: [[#^a|Title A]] • [[#^b|Title B]]`. The bullet separator
  matches LINKS lines (` • `). Aliases are the new title, sanitized (`|`, `]]`,
  and `#` escaped) and cut at a word boundary to 60 characters with `…`.
  Non-contiguous picks produce one line per run, so S's note order survives. A
  split drawer entry is replaced *inside* the drawer, so the drawer is never
  emptied (drawers are non-empty by construction).
- **Mentions:** the nav courtesy write puts `[[S]] (💬 mentions)` on each new
  task's LINKED FROM line and mints S's `^id` if it lacks one, in the same
  transaction. Reconcile would converge anyway. Links that were inside a split
  bullet now live in the new task, so their targets' mentions move from S to N on
  the next write (reconcile authority).
- **Status rings:** bob-ledger-tools' task-link marks render ◯ → ◉ → ✓ in front of
  each alias, so the ✂️ line is a live mini-checklist with no new renderer.
- **Cursor and jumps:** land on the first new task; `Ctrl+O` returns to the ✂️
  line. Like Ctrl+Shift+M, the split never answers or advances the `]s` walk.
- **Notice:** `✂ Split 2 notes into tasks · ◯ Ping Alice about the cutover window
  · ◯ Write the rollback runbook`.
- **Later (not v1):** `Alt+Enter` in the picker could mean "split as
  prerequisites" (S depends on each new task, using the existing Depends-On writer
  and its Blocked and prune effects).

Why mentions and not a `split from` relation: the ✂️ line already *is* the
forward pointer, and mentions already give the backward one. A relation would
add a LINKS line to every new task and a second LINKED FROM entry on S for the
same fact. The `split from` / `split into` inverse pair stays available for a
hand-authored relation.

### 7.3 The hotkey

Register `{modifiers: ["Ctrl","Shift"], key: "T"}` as the default for
`bob-navigation-hotkeys:split-bullets-into-tasks` ("Split bullets into tasks").
Add to the vault's `hotkeys.json`:

```json
"workspace:undo-close-pane": []
```

Alternatively, rebind Undo close tab to `Ctrl+Alt+T`. Obsidian's built-in
binding is Ctrl/Cmd+Shift+T
([forum](https://forum.obsidian.md/t/ctrl-z-should-also-undo-close-pane/9712)).
nav binds the literal `Ctrl`, so only the Linux hosts collide. If Bryan would
rather not touch core bindings, the fallback is context-overloading Ctrl+S, which
already means "split this Pomodoro" on Pomodoro lines. I prefer T: it pairs with
M (move), it is what Bryan asked for, and it does not overload save.

## 8. Command line

The CLI rules apply: `bob task <verb>` is for vault-wide task-line rewrites, every
long option gets a short alias, options are alphabetical, and nothing nests under
`bob capture`.

```text
bob task move  [OPTIONS] <SOURCE> <DEST> (-b ID | -m TEXT)...   # unchanged
bob task move  [OPTIONS] <TASK>... -T, --to <NOTE>                # new: any notes → one note
bob task merge [OPTIONS] <TASK>... -i, --into <TASK[#DRAWER] | PROJECT#DRAWER>
bob task split [OPTIONS] <TASK> (-D DRAWER | -m TEXT | -n N)...

TASK      note:block-id (also accepts note#^block-id and [[note#^block-id]])
-d, --dry-run                Plan and print only
-D, --drawer TITLE           (split) every entry of this drawer
-f, --format human|json      Default: human
-m, --match TEXT             (split) first-level note or drawer entry containing TEXT; repeatable
-n, --nth N                  (split) Nth splittable bullet, 1-based; repeatable
-o, --offline                Skip both sync cycles; commit locally
-r, --retry-timeout SECONDS  Lock wait and re-plan budget; default 60, 0 fails fast
```

- `--to` switches `bob task move` into multi-source mode. Every positional is
  then a `note:id`. Moving a single source with `-b/-m` still works, and no
  existing spelling changes. `--to db:upgrade` (a task ref) is refused with
  ``to fold tasks into db:upgrade, use: bob task merge … --into db:upgrade``.
  The CLI keeps move and merge as **distinct verbs** because a shell has no live
  preview, and a merge cancels.
- `bob task split db:upgrade` with no selector is a usage error that **lists**
  the numbered splittable bullets (as an ambiguous stem lists its candidates):

  ```text
  error: choose bullets to split with -n, -m, or -D
    1  Ping Alice about the cutover window
    2  Write the rollback runbook  (+1)
    3  FUTURE WORK › Try logical replication
  ```
- All three verbs use the `bob task move` contract: the lock, pre-sync, a
  guarded staged write (destination first, source last), one scoped git commit
  (`bob task merge: 2 → db#^upgrade`), post-sync, `--dry-run` parity, schema-1
  JSON with `ok`, `dry_run`, records, `applied_paths[]`, `deferred_paths[]`,
  `git`, and `error`, and exit codes 2 for usage and 1 for operational errors.
- Docs and help always quote capture examples and say why:
  `bob capture '@inbox+bench > @db'   # quote it: > is a shell redirect`.

## 9. Architecture and reliability

```text
                    ┌───────────────────── Rust (authoritative) ─────────────────────┐
 capture `>` ───────┤ plan_task_move (existing, now called per source note)          │
 capture `~|merged` ┤ plan_task_merge  ── fold plan · cancel (task_cancel) ·         │
 bob task merge ────┤                    dependent re-point · ledger hand-off ·      │
 nav merge label ───┤                    fragment link repair (task_move)            │
   (via `bob task merge -o -f json`)                                                 │
 bob task split ────┤ plan_task_split  ── pure single-note transform  ◄── vectors ──┐ │
                    └──────────────────────────────────────────────────────────────┼─┘
 nav Ctrl+Shift+T ──── JS planSplitBullets (editor transaction, undo) ◄────────────┘
```

- **Merge has one engine.** `plan_task_merge(snapshot, MergeRequest{sources,
  target, drawer}) -> MergePlan{postimages, merges, repaired_files, …}` is pure
  over a `VaultSnapshot`, like `plan_task_move`. Capture runs it inside
  `CaptureBatchPlanner` (staged and preimage-checked, all or nothing). `bob task
  merge` runs it inside the task-move command shell (lock, guarded writer,
  recovery directory, commit). **nav's Links stage branches on
  `LabelEffect::Merge`:** it saves the affected buffers, renders the consequence
  strip from `bob task merge --dry-run -f json`, and commits with
  `bob task merge -o -f json`. This follows the ledger-tools precedent of running
  `bob relations rename` for multi-note writes. Costs: desktop only (mobile shows
  `⤵ merging needs the desktop app` and writes nothing), and undo is a
  `git revert` of one commit instead of Ctrl+Z. Both are acceptable for a heavy,
  infrequent, multi-note operation.
- **Write order is "copy, then retire".** T is written first, then dependents'
  notes, then the daily note, then S. Any partial failure leaves S open and
  intact, which is recoverable and visible, never lossy. Capture's batch gets
  this order for free from the topological "destination before source" rule.
- **Split is twinned.** It is one note and one transaction, undo matters, and the
  transform is pure text, so the twin is cheap.
  `tests/fixtures/task_split/vectors.json` (bob-cli authoritative, copied
  byte-for-byte into bob-plugins, as for `task_cancel/vectors.json`) pins the
  bytes.
- **Required invariants (property tests):** after any operation, every block link
  that resolved before still resolves to the same logical thing (a moved task, a
  tombstone, or a relocated anchor); `reconcile` is a no-op; a dry run equals the
  real result except `dry_run`; and re-running is `Unchanged`.

## 10. Conformance vectors (starter set)

| ID | Case | Expected |
| --- | --- | --- |
| GV1 | `@inbox+a @work+b > @db` | two `moves[]`, both in `db.md` intake in typed order; links repaired |
| GV2 | `@a+x > @c` before and after `bob-cli-gm` | before: grammar break documented (was note "> @c"); after: move |
| GV3 | `@a+x > @c+z` | merge (formerly `split_capture_targets` after gm, never a note) |
| GV4 | `@a+x > @c oops`, `@a+x > @c s:2`, `>` line plus bullets | `move_destination_text`, `move_line_marker`, `move_line_children` |
| GV5 | `@a+x \> quoted`, `Called Bob > 3 times @a+x` | unchanged note behavior |
| GV6 | `@a+x >` / `> @c+` / `> @c+z#` | incomplete with `move_destination` / `block_id` / `drawer` |
| GV7 | `@home+x > @home#ideas` (area) | `merge_needs_task` |
| GV8 | `@a+x > @proj#future-work` with no such section | `## Future Work` created; S folded; `[[proj#^prj]]` relation |
| MG1 | §6.2 example | bytes exactly as shown; daily link handed off; dependent re-pointed |
| MG2 | T already linked today | S's link pruned, not duplicated |
| MG3 | T Blocked | S's link pruned; dependents now wait on Blocked T |
| MG4 | T depends on S | edge dropped; T recovers with `[unblocked::]` if that was its last prerequisite |
| MG5 | dependent Y, and T depends on Y | `merge_dependency_cycle`; vault byte-identical |
| MG6 | S has `^anchor` on a note line, linked from a daily note | anchor moves to T's note; link repaired |
| MG7 | S has an open nested subtask | `merge_source_open_subtasks` |
| MG8 | two sources into one T | two title bullets in typed order; one LINKED FROM line, canonical sort |
| MG9 | re-run MG1 | `Unchanged`; zero writes |
| MG10 | `merged into` in both `cancel_labels` and `merge_labels` | overlap warning; no effect |
| MG11 | merge then `bob task reconcile` | no-op |
| MG12 | merge then `bob task archive` | tombstone in `done/`; T's mirror path repaired |
| SP1 | §7.2 example | bytes exactly as shown; one undo restores the original |
| SP2 | split bullets 1 and 3 of 3 | two ✂️ lines, one per run; bullet 2 stays between them |
| SP3 | split the only entry of `FUTURE WORK` | drawer keeps the ✂️ line |
| SP4 | bullet already has `^anchor`, linked elsewhere | task ID equals the anchor; inbound links now resolve to a task |
| SP5 | bullet text with `\|`, `]]`, `#` | alias escaped; mention still detected |
| SP6 | cursor on Depends-On / LINKS / log / Pomodoro | notice, no edit |
| SP7 | S lacks `^id` | S minted in the same transaction; mentions written |

## 11. Optional extension: the full "destination decides" matrix

If Bryan likes the principle, the reserved left-hand `@a+x#drawer` completes it.
A drawer is a list of *notes*, so the source kind is notes rather than tasks:

| Source ↓ / Destination → | note `@c` (holds tasks) | task `@c+z[#d]` (holds notes) |
| --- | --- | --- |
| tasks `@a+x` | **move** (v1) | **merge** (v1) |
| drawer entries `@a+x#d` | **split** into `c.md`'s tasks (leaves ✂️ line in `^x`) | **move notes** between drawers |

This would give split a capture spelling, so the Mac can split without Obsidian.
It also gives a natural home for `> @c+z#tasks` ("nest as subtasks", since
`TASKS` is already a reserved drawer key). I would **reserve** the forms in v1
(`move_source_drawer`) and decide after a few weeks of v1 use.

## 12. Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Hard-delete sources on `> @c#drawer` (as requested) | Rejected: dangling links, broken ledger semantics, two source fates |
| Merge *copies* S's notes and leaves S whole | Rejected: duplicate drawers and stale content until archive, and doubled mentions. Cut plus tombstone is just as safe with T-first ordering. |
| Merge flattens S's drawers into T's same-named drawers | Rejected: loses provenance and trips near-duplicate drawer guards. One title bullet is predictable. |
| Transfer S's prerequisites to T | Rejected: silently blocks T and prunes its links. Report and hint instead. |
| Plain cancel semantics for dependents (unblock them) | Rejected: unblocks work whose prerequisite is not done |
| Separate merge sigil (`>>`, `=>`, `->`, `→`, `into`) | Rejected: one arrow plus the destination kind is simpler. Every `>` variant has the same shell issue, `→` is hard to type, and `into` collides with prose. |
| Dedicated merge keymap instead of the label effect | Not needed: the label path covers Obsidian, and Ctrl+Shift+M drill-down (Tab into a note's tasks, then Enter to merge) is a good v2 complement that mirrors `>` |
| `split from` relation for split | Rejected: redundant with ✂️ line plus mentions |
| JS twin for merge (house pattern for cancel/complete) | Rejected for merge only: multi-note graph rewrite, so one engine wins on reliability |
| New split tasks via a destination picker | Deferred: same-note split plus `N<Ctrl+Shift+M>` composes, keeps one undo |
| No capture syntax, CLI and Obsidian only | Rejected: the Mac is the fast surface, and `@` completion makes task refs cheap |

## 13. Sequencing and coordination

1. **Phase S (split), independent, ship first.** Rust `plan_task_split` plus
   `bob task split` and its vectors, then the nav Ctrl+Shift+T gesture, picker,
   and `hotkeys.json` entry, then `docs/task-split.md` and bob-plugins docs.
2. **Phase M (merge engine).** `plan_task_merge`, `relations.merge_labels` and
   `LabelEffect::Merge`, the capture `~`/`~~` merge path (alongside
   `relations_cancel.rs`), `bob task merge`, contract doc
   `docs/task-merge.md` (vectors MG*), and the chezmoi config edit.
3. **Phase G (grammar), after `bob-cli-gm`'s `grammar` phase lands.** `>`
   recognition in both resolvers, `capture-parse`/`complete`/`rewrite`, execution
   through phases S and M engines plus `plan_task_move`, `bob task move --to`, and
   a grammar bump. Take one more than the highest revision either code or docs
   claim at that time; move bullets already say 8, and gm takes the next.
   Commit as `feat(capture)!:`.
4. **Phase N (nav merge label).** Links-stage branch to `bob task merge`, the
   consequence strip, and mobile refusal.
5. **Optional:** Mac footer verbs and symbols; Ctrl+Shift+M drill-down; §11
   matrix; cross-note `- ^route:id` move bullets (trivial once `--to` exists);
   "split as prerequisites".

After acceptance, record decisions (via `/sase_memory_write`): "A merge cancels
and folds, never deletes", "The destination decides the shape", and "Split
leaves a ✂️ line; mentions are the back-pointer". Add glossary strands for
**Task Merge** and **Task Split**, and disambiguate them from *Merged
Pomodoro* and Pomodoro split.

## 14. Open questions for Bryan

- **Q1. Today's plan on merge:** should S's live Task Link be **handed to T**
  (my default), or pruned like a cancel? With hand-off, a Ready T rises to Next.
- **Q2. Area notes:** refuse `> @area#heading` (my default), or allow a
  "file as plain bullets" mode whose tombstone gets a Cancel Log line
  `filed under [[area#Heading]]` instead of a relation?
- **Q3. Tombstone body:** cut S's notes (my default), or keep a copy on S as a
  frozen snapshot until archive?
- **Q4. Split placement:** directly below S (my default), or at the end of the
  note's `## Tasks` intake?
- **Q5. Hotkey:** clear Obsidian's Ctrl+Shift+T "Undo close tab" (my default),
  or use Ctrl+S in task context?

## 15. Recommended solution

Build **Move / Merge / Split** as one family under one principle: **the
destination decides the shape.** A note holds tasks, so `>` to a note moves. A
task holds notes, so `>` to a task merges.

- **Capture:** `@a+x @b+y > DEST` on one line, recognized right after the
  `bob-cli-gm` source run and claimed before fan-out.
  - `> @c` moves through the existing `plan_task_move`, once per source note.
  - `> @c+z` and `> @c+z#drawer` merge.
  - `> @proj#drawer` merges into `^prj`'s H2-section drawer, created on demand.
  - `> @area#…` is refused with a teaching error.
  - A `>` line takes no other markers and no children. Completion, parse, and
    rewrite reuse the `@route`, `+id`, and `#drawer` assists, and `> |` opens
    Ctrl+Shift+M's destination list. This is one grammar bump, after gm.
- **Merge = cut and retire.**
  - T is written first: S's description becomes one note bullet, with S's
    authored children nested beneath it and their anchors link-repaired.
  - Dependents of S re-point to T. S's prerequisites are reported, not
    transferred.
  - S's open-Pomodoro link today goes to T (Q1).
  - S is written last: cancelled, keeping its `^id`, its logs, and
    `🪢 LINKS: merged into [[T]]`. T's mirror reads *merged from*.
  - Refusals cover closed, recurring, `^prj`, open-subtask sources, closed
    targets, nesting, and cycles. Re-runs are idempotent.
- **`relations.merge_labels: [merged into]`** is a fourth label effect. It fires
  on the same explicit gestures as cancel labels (capture `~`/`~~`, Ctrl+Shift+L,
  Ctrl+Shift+Alt+L, batches) and runs the same Rust merge engine. nav shells out
  to `bob task merge -o -f json` for the preview and the commit.
- **Ctrl+Shift+T splits** first-level notes and drawer entries (cursor, count,
  visual selection, or a Tab-mark picker on the task line or drawer title).
  - New tasks are inserted directly below the source, born as capture-created
    tasks, with existing anchors reused as IDs.
  - Each contiguous run is replaced by `- ✂️ Split out: [[#^id|Title]] • …`,
    whose status rings update live.
  - The new tasks get `💬 mentions` back-pointers, all in one same-note editor
    transaction with one undo.
  - Clear Obsidian's Ctrl+Shift+T "Undo close tab" in `hotkeys.json`.
- **CLI:**
  - `bob task move <TASK>… --to <NOTE>` (multi-source; the old form unchanged).
  - `bob task merge <TASK>… --into <TASK[#DRAWER]|PROJECT#DRAWER>`.
  - `bob task split <TASK> (-n|-m|-D)…`, which lists candidates when no selector
    is given.
  - All three share the task-move lock, commit, dry-run, and JSON contract.
    Examples always quote `>`.
- **Order:** split, then the merge engine with the label and CLI, then the `>`
  grammar, then the nav merge label. Optional follow-ups are the §11 matrix,
  Ctrl+Shift+M drill-down, and Mac verbs.

Sources:
- [Obsidian forum: Ctrl-Z should also undo close pane (Ctrl/Cmd+Shift+T default)](https://forum.obsidian.md/t/ctrl-z-should-also-undo-close-pane/9712)
- [Obsidian forum: Undo Close Window ("Undo Close Tab" exists)](https://forum.obsidian.md/t/undo-close-window/66981)
