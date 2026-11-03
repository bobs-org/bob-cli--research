# Pull existing tasks into a new project note with a bare `^id` bullet

Research report for the `@foo[:^]bar@` child pull-in proposal.
Researcher: mus. Date: 2026-11-03.

## 1. What was asked

Bryan wants capture to create a project note with `@foo[:^]bar@` and then
pull child tasks out of the parent project (`~/bob/foo.md`) into the new
note. The proposed mechanism: a `^some-id` reference on a bullet line by
itself (no other text) moves the `^some-id` task from the parent file into
the new project note. Pressing `^` after `- ` when the `@foo[:^]bar@` form
appears anywhere in the draft must trigger good completion in bob-mac-capture.
The brief asks for lead design that is intuitive, reliable, and beautiful,
plus a critique and a recommended solution.

## 2. Current system (verified in tree)

### 2.1 Two seals, two bullet kinds

`docs/capture.md` (glance table and §§ on project notes) defines two seals:

- `@route^block-id@` creates `<route>_<block_id>.md` with no links and no
  offers. The `^prj` line is never linked and the daily note is untouched.
- `@route:block-id@` creates the identical note, then **offers** its open
  task rows as successors of the new `^prj` (same pull-in protocol as a
  managed Done gesture). Explicit ` :<id>` bullets still link; nothing else
  links until picked with `-p/--pull-in`. See
  [Offer a new project's tasks](#offer-a-new-projects-tasks) and the
  `glossary:task-successor` strand ("Creating a project note with capture's
  `@route:id@` likewise makes the new note's open tasks successors of its
  `^prj` task").

Task bullets inside the new note already split on the trailing sigil:

- `- <task> :<task-id>` names the task, makes it Next (`[*]`, or `[?]` when
  scheduled), and links `[[<stem>#^<task-id>]]` into the placed Pomodoro.
- `- <task> ^<task-id>` names it only (`- [ ] #task … ^<task-id>`).

This `:` = link vs `^` = name-only split runs through the whole grammar
(`@route:id` links, `@route^id` names; `^route:id` links, `:` links, `^`
names). Any pull syntax must preserve it.

### 2.2 A bare `^id` bullet is free real estate

`src/native/capture_language/project_tasks.rs::ProjectTaskPass::check_child`
is the single shared rule for execution (`item.rs`) and editor
(`editor_parse.rs`) parsers. A `Valid` ID on a first-level bullet with an
empty body hits `empty_project_task_body_error` ("capture line N names a
task but has no task text"). A `Lone` `:`/`^` is the unfinished-ID prompt.
So `- ^some-id` with nothing else is **always an error today** — repurposing
it as a pull can never break a working draft. That is the proposal's
strongest property, and the reason the sigil choice is sound.

The same file shows the surrounding guardrails a pull must reuse: `prj`
reserved in any case, charset rule (`A-Z a-z 0-9 -`), duplicate detection
across the item in source order, misplaced-parent and misplaced-nested
errors, and the `:`-with-checkbox refusal.

### 2.3 Completion already opens on `^` — but only for new IDs

`bob capture-complete --help` (and `src/native/capture_complete/cli.rs`)
documents `project_task_block_id`: a trailing ` :id`/` ^id` on a
first-level bullet of a project-note item, also on task-list bullets and
nested lines under project-note tasks. It returns empty candidates plus an
additive `block_id` object (intent `new`, stem, sigil range, owner body,
used IDs including `prj`, suggestions) and a `splice` that lands the
accepted ID on the owner line. `src/native/capture_language/completion.rs`
(`project_task_block_id_detail`) builds the used list from sibling bullets.

The Mac side (`bob-mac-capture`, opened via `sase repo open`) is a thin
client per `decisions:mac-capture-is-a-thin-client`: it runs
`capture-complete`, renders candidates, and applies `block_id.splice`
(`Sources/CaptureCore/CaptureBlockIDSplice.swift`,
`Sources/CaptureCore/BlockIDRules.swift`). `CapturePanelModel.swift`
(`handleBlockIDCompletion`, `isUsableBlockIDCompletion`, `blockIDSource`)
routes `project_task_block_id` into the Block ID picker with
`scope == .projectTask` and intent `new`, auto-opening only when the edit
wrote the separator byte. So "press `^` after `- `" already reaches Bob;
what is missing is **parent-task candidates**. No Mac grammar fork is
allowed — Bob must send them.

### 2.4 The move engine already exists, and inbox routing proves moves can live inside capture

`docs/task-move.md` (`bob task move SOURCE DEST -b/-m`) moves top-level open
`#task` blocks, preserving status, priority, schedule, freshness/keeps,
tags, and children; repairing `[id::]`/`[dependsOn::]` and vault-wide links
(wikilinks, embeds, aliases, pathless links); renaming on collision with a
report. It refuses closed, nested, non-task, and `^prj` selections, plus a
task that depends on the destination's `^prj` and a blocked destination
that only accepts `[?]` tasks (`src/native/task_move/plan.rs`).

`docs/capture.md` ("Routing inbox tasks out") proves a move stage can run
inside `bob capture`: after every item plus the successor post-pass, before
trackers finish, answered candidates move through the same engine, with
`inbox_route` JSON, `-i/--inbox-route` answers, `keep`, stale/refused
handling, and atomicity (stale pick writes nothing). A project-child pull is
the same shape with a different trigger (authored bullet, not a detected
candidate).

### 2.5 Successor offers are the wrong vehicle for this

The `@route:id@` offer flow (`successors[]`, `pull_in`, `-p`, `--require-pull-in-choice`)
is for **new** tasks choosing links. A pull is a **move** of an existing
block: identity, history, and links travel. Conflating the two would
double-report pulled rows as both moves and offers. The glossary
`task-successor` strand confirms the distinction: picked existing tasks get
stamped fresh; tasks the capture itself creates never are. Pulled tasks must
follow the move rule (preserve, no fresh stamp), not the pick rule.

## 3. Critique: is this a good idea?

Yes — with adjustments. The core insight is right:

- **Intuitive.** The draft reads like the note it writes
  (`decisions:capture-bullets-mirror-the-task-block`). `- ^ship-it` under
  the new project reads as "this task lives here now", with no route
  repetition and no new sigil to learn.
- **Reliable.** Because the bare form is an error today, there is no legacy
  ambiguity: `- Draft memo ^x` stays a new task, `- ^x` alone becomes a
  pull. Resolution is deterministic (parent note lookup, not vault-wide
  search).
- **Economical.** It reuses the move engine, the guarded-write/rollback
  discipline, and the thin-client completion contract instead of inventing a
  third task-copy path alongside `task move` and Ctrl+Shift+M.

The risks, in order of importance:

1. **Asymmetry.** The proposal specifies only `^id`. Users will try `:id`
   (the link form) and hit a confusing error. The `:`/`^` split is the most
   consistent rule in the grammar; a pull that only speaks `^` breaks it.
2. **Discoverability.** A bare `^id` looks like a typo (an ID with no task).
   Without completion that names the parent's tasks with text, status, and
   type, nobody will find it. The `^`-after-`- ` requirement is therefore
   load-bearing, not polish.
3. **Scope creep in the bullet.** If a pull bullet also accepts `s:`/`$`,
   checkboxes, drawers, or nested lines, every combination needs semantics
   (edit-then-move? move-then-edit?). The beautiful version is bare-only.
4. **Third-note writes.** Project-note capture today writes two files (new
   note + daily note). A pull adds the parent note plus vault-wide link
   repairs. That is strictly more failure surface (parent changed on disk,
   ID collision, dependency deadlock, blocked destination). It must reuse
   capture's all-or-nothing staging, not append a second transaction.
5. **Dependency and blocking semantics.** Pulling a prerequisite out from
   under dependents, or into a future-scheduled (blocked) new project, must
   not silently unblock or strand work. The `task move` + `projects-block`
   refusals already answer this, but they must be wired into the pull path,
   not re-decided.

Rejected alternatives and why:

- **`- [[foo#^id]]` / `- !foo:id` / `- ^foo:id` (explicit route per bullet).**
  Verbose, repeats the parent on every line, and breaks the draft-mirrors-
  block rule. Useful only if pulls ever span multiple parents in one item —
  they should not (see §4.2).
- **Vault-wide `^id` search (any note).** Ambiguous (`^fix` exists in five
  notes), surprising, and uncompletable. Parent-scoped lookup is the only
  predictable scope.
- **Copy instead of move.** Leaves a duplicate behind and splits `[id::]`
  identity, link repair, and freshness history. The vault already has one
  copy primitive with repair (`task move`); a second is pure cost.
- **Auto-pull by fuzzy text match ("Similar tasks" band).** Good for
  discovery, wrong for commitment: capture's Similar-tasks band is
  explicitly a settled heads-up where Return never changes anything
  (`decisions:similar-tasks-are-a-settled-heads-up`). Pulls must stay
  explicit keystrokes.

## 4. Adjustments (what I would change)

1. **Support both `- ^id` and `- :id` pulls, with the existing meaning.**
   `^id` moves the block as-is (no auto-link, mirroring `^` name-only);
   `:id` moves it, raises it to Next, and links it (mirroring `:` link),
   including the `:`-checkbox refusal. Document the pair together; the
   prompt's `^`-only form becomes the common case, not the only form.
2. **Scope pulls to first-level bullets of project-note items only.**
   Parent line, nested lines, non-project items, and task-list (`+`) items
   keep their existing errors. One item pulls from exactly one parent: the
   route of that item's `@foo^bar@`/`@foo:bar@` seal. Multiple project-note
   items in one draft each pull from their own parent.
3. **Resolve against the parent note only, and refuse loudly.**
   Missing parent note, ambiguous route, unknown `^id` (with close-match
   suggestion, mirroring `capture-tasks` errors), closed/nested/`^prj`
   source, duplicate pull of the same ID in one draft, and collision with a
   new-bullet ID in the same draft are all teaching errors that write
   nothing. Never fall back to vault-wide search and never mint a new task
   from a bare bullet.
4. **Move the whole block through the `task move` planner; do not re-render
   it as a new task.** Status, `[created::]`, priority, schedule,
   `[fresh::]`/`[keeps::]`/`[unblocked::]`, tags, Depends-On/BLOCKS/LINKS,
   drawers-as-children, and nested children travel. No fresh stamp (move
   rule, not pick rule). On block-ID collision in the new note, rename with
   the move engine's next-free suffix and report it; `prj` stays reserved.
5. **Keep pull bullets bare.** No `s:`/`$`/`%`/checkbox/drawer/nested lines
   on a pull bullet — refuse with a one-line teaching error. Schedule,
   priority, and rewording happen before or after capture, not inside the
   pull token. This is what keeps the grammar teachable.
6. **Apply the existing move guards unchanged.**
   Refuse pulling a task that depends on the new note's `^prj` (deadlock),
   pulling into a future-scheduled new project unless the pulled task is
   `[?]` (blocked-destination rule), and pulling the parent's `^prj`
   itself. Leave BLOCKS/status reconciliation to `bob task reconcile`;
   repair ledger links to the new note path (move rule) rather than
   striking them.
7. **Exclude pulled rows from `@foo:bar@` successor offers.**
   Offers cover new open rows only; pulled rows are moves, already placed.
   Explicit ` :new-id` bullets and `-p` picks compose unchanged.
8. **Make completion the teacher, additively.**
   Keep the `project_task_block_id` context (no new context string, no
   fork) and add pull candidates + `intent`/candidate-kind fields with
   `decodeIfPresent` semantics, so older Mac builds ignore what they do
   not understand and the `schema_version` bump stays additive. The picker
   shows one "Pull from `foo.md`" group (task text, status, type — the
   recognition the brief asks for) plus diagnostics with `disabled_reason`
   for ineligible rows (closed, `^prj`, nested, already-pulled, duplicate);
   no "New ID" rows on a bare bullet because a bare bullet cannot mint.
   Shell completion mirrors the same grouping; `grammar: 5` marks the
   change.

## 5. Recommended solution

**Grammar (bob-cli, `docs/capture.md` first).** Under both seals,
a first-level `- ^id` bullet with no other text pulls that open top-level
task block from the item's parent note into the new note's `## Tasks`
intake (end of intake, same placement as `task move`); `- :id` pulls,
raises to Next, and links it under the placed Pomodoro. Either form with
any other token on the line is the existing new-task or error path —
only the truly bare bullet pulls. Duplicates (two pulls of one ID, or a
pull colliding with a `- text ^id` new bullet) refuse; nested/parent-line
IDs keep their misplaced errors. Bump the capture grammar to 5; the
release rides the daily train with no manual version edit
(`decisions:bob-cli-releases-ride-a-daily-train`), and the changelog marks
`!` only if the JSON contract breaks beyond additive fields.

**Planning order (reuse, do not fork).** Parse → render new note (new tasks
only) → resolve pulls against the parent snapshot → stage parent removal +
new-note insertion through the `task move` planner (identity repair
included) → link explicit ` :` and `:id`-pull links → successor-offer pass
(new rows only) → inbox-route detection → guarded all-or-nothing commit
(new note, parent, daily note, repaired link notes). Any refusal or
`NoteChanged` race writes nothing. Dry-run previews the parent strike, the
new-note insert, ledger repairs, and renames in today's vocabulary
(`ledger`-style lines + `pulled_tasks[]` JSON next to `task_links[]`).

**Completion (the `^` requirement).** After `- ` inside a project-note item,
a typed `^`/`:` opens `project_task_block_id` scoped to that item's parent:
query filters the parent's eligible open tasks (text, ID, status/type),
each row carrying text + status + type so the choice is recognizable;
ineligible rows appear disabled with the commit's own reason; acceptance
inserts the bare sigil+ID via the existing `splice`. Other items keep
today's new-ID behavior. Because Bob owns the grammar, the Mac change is
presentation only: render the pull group, apply the splice, and preview via
`capture --dry-run` exactly as today. No Swift grammar, no second
implementation.

**Mac presentation (beautiful).** One picker group, "Pull from `foo`",
with status chips and type annotations; the inserted `- ^id` stays
human-readable in the draft. Dry-run preview shows the task leaving the
parent (struck row) and landing in the new note's task list; pulled rows
get their own "Pulled in" section above "Offers" in the Pull-In card so a
move is never mistaken for an offer. Errors read as teaching copy naming
the parent and the close match (`no task ^x in foo.md — did you mean
^y?; list with bob capture-tasks -r foo.md`).

**Docs and tests.** `docs/capture.md` gains a "Pull tasks from the parent
project" section with the `:`/`^` pair, the bare-only rule, the guard
table, and the atomicity statement; `docs/completion.md` documents the
extended `project_task_block_id` pull group. Tests mirror the existing
vectors: empty-body acceptance, both sigils, per-item scoping, unknown/
closed/`^prj`/nested/duplicate/collision-rename, dependency-deadlock and
blocked-destination refusals, atomicity on parent-change races, dry-run
JSON shape, and Mac-observed completion transcripts for `- ^` with and
without a project-note seal in the draft.

In one sentence: keep the proposal's bare-`^id` mechanism, add its missing
`:` twin, move whole blocks through the existing move engine inside
capture's single transaction, and let Bob's completion teach the parent's
tasks so the Mac only has to render them.
