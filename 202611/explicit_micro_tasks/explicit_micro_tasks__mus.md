# Explicit Micro Tasks: Marker, Capture, Successors, and Merge

Researcher: mus · 2026-11-20
Scope: decide how Bob should make "micro tasks" explicit, reliable, and beautiful.
Out of scope (noted where it matters): converting an arbitrarily complex project
into an equivalent single task.

## TL;DR recommendation

Make micro tasks explicit with a single safe glyph marker, not `#task`, `TASK:`,
or stored `##` runs. Concretely:

- **Store one `›` (U+203A) as the micro-task prefix** at the start of a plain
  bullet body: `- › Confirm the rollout owner`. Depth is never stored; the
  renderer repeats the glyph by nesting depth (`›`, `››`, `›››`), so moves and
  re-indents cannot desync the count.
- **Default note-less `@route+id` capture notes into an explicit `NOTES`
  drawer**; drawers stay drawers; only `›`-marked bullets are micro tasks.
  Existing vault bullets migrate lazily (no mass rewrite) with a one-time
  reconcile + split/convert tooling, not a flag day.
- **Capture ergonomics: `..` expands to `› ` at bullet start only, plus a
  `Ctrl+G T` leader toggle** that adds/removes exactly one leading `› ` on the
  current bullet. Both go through the existing `capture-parse` / dry-run /
  commit resolver so preview and commit cannot disagree.
- **Successors reuse the existing successor-offer contract** (one picker per
  gesture, nothing preselected, `hand_off` group + additive `micro_task` field).
  Top-level (`›`) micros become closed-by-default successor rows; deeper micros
  ride along as non-actionable context. Open / pull-in / cancel reuse the same
  picker keys where possible instead of minting `Ctrl+X` / `Ctrl+Shift+X` /
  `Space` / `Tab` collisions.
- **Merges create one `›` micro bullet** (title + copied children, no live
  anchors), never a drawer, never a full task.
- **Glossary term: Micro Task.** Draft provided in §9.

The rest of this report justifies each choice, critiques the prompt's first
draft, and lists the adjustments I would make before implementation.

## 1. What exists today

### 1.1 Task children: authored notes vs drawers vs managed lines

Bob's shared classifier (`src/native/task_children.rs`,
`classify_task_child` / `classify_direct_children`) divides a task's direct
children into: `Authored`, `Drawer { title }`, managed links (`DependsOn`,
`Blocks`, `Links`, `LinkedFrom`), managed logs (`Schedule`, `Work`, `Rotten`,
`Cancel`), and `NestedTask { open }` (a `- [ ]` / `- [x]` child detected by
the task scanner with the note's settings).

A drawer is a direct non-checkbox ALL-CAPS child bullet with nested notes
(`src/native/capture_drawers.rs`, `is_drawer_title` / `parse_drawer_title`,
glossary `task-drawer`). Capture never creates an empty drawer; a childless
ALL-CAPS bullet stays a plain note. Managed lines and `TASKS` are never
drawers (`reserved_drawer_keys`). Fenced blocks nested in a list item are
excluded from children by the fenced-line scan.

What the prompt calls a "micro task" is today simply the `Authored` bucket
(plus, in practice, unchecked nested `- [ ]` rows, which are `NestedTask`s).
There is no marker, no `NOTES` drawer requirement, and no distinction between
"a note that is really a small unit of work" and "a note that is prose."

Capture's authored-sub-bullet grammar (`docs/capture.md`, "Authored
sub-bullets") allows exactly two levels under the parent line: first-level
items at column zero, nested items prefixed by exactly two ASCII spaces. Every
first-level bullet under a task today is one note (with its nested bullets as
its children) unless it is a drawer title / drawer shortcut. A note-less
`@route+id` followed by bullets files each as its own note, with drawer
bullets merging into the target's drawers (decision
`capture-bullets-mirror-the-task-block`).

### 1.2 Promotion (task → project) and reversal

Promotion (`docs/projects.md`, "Promotion successors";
bob-plugins `110-project-seed.js` `buildProjectSeedFromChildBullets`) converts
a task's child bullets into a seeded project note: qualifying children become
task lines, drawer titles become `##` sections, managed logs travel
separately, and anything lossy aborts with "Child bullets could not be
converted; nothing was promoted." The offer rows enumerate the seeded
project's open `#task` lines at any depth except `^prj`. Reversal restores
drawers from H2 sections.

The gap the prompt identifies is real: because plain notes and "would-be
tasks" are indistinguishable today, promotion must guess. An explicit micro
marker removes the guess: `›` bullets become tasks, plain notes stay notes,
drawers stay sections. This is the strongest argument for the feature.

### 1.3 Split is the closest existing inverse

`docs/task-split.md` already promotes bullets that "grew into real work" into
tasks: first-level authored notes, drawer entries, and H2 section bullets are
splittable; `#task` lines, stubs, drawer titles, managed lines, Pomodoro
lines, and checked checkboxes are not. The new task is
`- [ ] #task <text> [created:: today] ^<id>` (minted or reusing a trailing
`^anchor`), children travel byte-for-byte, and the source becomes a
`- [[#^id|Alias]]` stub plus a `LINKED FROM (💬 mentions)` line.

Any micro-task design should reuse split's writer shape (ID minting, alias
rules, mention line, placement after `P`'s block / `## Tasks` intake for daily
notes) rather than invent a second task-birth path. The successor-open path
(§6) is effectively "split on demand," and should call the same planner.

### 1.4 Successors today

Successors are computed at gesture time and never stored (glossary
`task-successor`, `successor-offer`; decision `unblocked-tasks-are-offered`;
`docs/task-dependencies.md` §12). Managed Done gestures offer direct
dependents (`hand_off`), open residents of a recovered project (`project`),
project-finished pull-ins, keep-moving offers, and successor-label relations
(`starts after`). One picker per gesture, nothing preselected, no cap; only
picked rows link (raised to Next, stamped fresh unless the task was created by
the same capture). Capture never prompts: callers pass explicit `-p`
selection; the Mac shows an in-panel choice.

Micro-task successors are a new successor *source*, not a new successor
*mechanism*. The prompt's per-row verdicts (open / pull-in / cancel /
non-actionable) map cleanly onto the existing picker + verdict-copy
infrastructure (`relation_successor` vectors, `successorPicker*` helpers)
with one new group/field, which is much cheaper than a parallel panel with
four new global keymaps.

### 1.5 Merge today

`docs/task-merge.md` folds sources into a container (task, drawer, H2
section). The source's description becomes one plain title bullet; authored
children copy beneath it with live `^id` anchors and live `[id::]` stripped
outside inline/fenced code; managed children stay on the source; open nested
tasks refuse the merge (`merge_source_open_subtasks`); dependents re-point;
the source is cancelled with `🪢 LINKS: merged into [[T]]`. Capture `<` (merge
into the task the line creates) and `>` (merge into an existing destination)
share the pure planner `plan_task_merge` in `src/native/task_merge/`.

A merge-sourced micro task therefore cannot be "just add the marker." It must
also apply the copy/strip rules, the open-nested-task refusal, and the
cancel-with-backlink, or merges will silently fork live anchors.

## 2. Is this a good idea? Critique

**Yes, with adjustments.** The core insight is sound:

1. The implicit rule ("any non-drawer sub-bullet is a would-be task")
   conflates prose notes with work items, forcing promotion to guess and
   reviewers to re-derive intent at close time.
2. Making the work-items explicit gives promotion, split, close review, and
   merge one shared vocabulary, and unlocks the stated future goal (project ⇄
   task round-trip) without committing to it now.
3. Tying micro review to the close gesture directly serves the stated goal:
   "make sure I've really completed all of the work a task commits to."

But the prompt's first draft has five weaknesses I would fix:

1. **Marker choice optimizes for familiarity over safety.** Both `#task` and
   `TASK:` collide with load-bearing grammar (see §3). Familiarity is not
   worth a tag-pane flood or a drawer-grammar exception.
2. **Storing depth (`##`, `###`) duplicates indentation.** Indentation already
   encodes depth; a stored count rots on every move/re-indent and needs a
   repair pass. Render depth, don't store it.
3. **Four new keymaps overstate the need.** `Ctrl+X` is Cut, `Space`/`Tab`
   already answer walk rows, and `Ctrl+Shift+X` sits beside the cancel
   gesture. A new modal-local key layer for one row type is a memorability
   and conflict burden. Reuse the successor picker first.
4. **`NOTES`-by-default is a vault-wide behavior change.** Thousands of
   existing plain notes would logically move. That needs lazy migration, not
   a rewrite, plus a clear story for hand-written notes that never pass
   through capture.
5. **Micro semantics are under-specified.** Can a micro carry priority,
   schedule, deps, types, block IDs? (I say no — see §5.) What does closing a
   parent with open nested micros mean? What does "closed by default" write
   to the file, if anything? The report below pins these down.

## 3. The marker: requirements and candidates

### 3.1 Requirements

Any marker must: (a) survive CommonMark + Obsidian + Tasks-plugin reads
without becoming something else; (b) not create an Obsidian tag, heading,
blockquote, checkbox, or drawer; (c) be typable without IME and togglable from
the capture panel and the editor; (d) nest cleanly; (e) be greppable; (f) not
require escaping in ordinary prose; (g) render concisely at any depth.

### 3.2 Why not `#task`

- It mints a real `#task` tag on every micro bullet: tag-pane noise, tag
  search pollution, and tag-autocomplete churn on every keystroke.
- `#` at a first-level bullet start already means "drawer shortcut" in capture
  (`- #future-work` → `- FUTURE WORK`, decision
  `capture-bullets-mirror-the-task-block`). A `- #task …` bullet is therefore
  either a drawer shortcut for a drawer literally named `TASK` (bad) or a
  grammar exception at the most sensitive position (worse).
- The escaper (`src/native/task_text_escape.rs`, `escape_hash_task_token`)
  deliberately neutralizes whitespace-delimited `#task` in notes so prose
  stays inert. Reintroducing bare `#task` as meaningful reopens the ambiguity
  that function closed.
- Nested `#task` inside a bullet body already risks Tasks-plugin / Dataview
  pickup as a task row; promoting that to the *intended* reading makes every
  hand-typed `#task` veto harder.

### 3.3 Why not `TASK:`

- `TASK:` matches the drawer title grammar (lead `A-Z`, rest allows `:`
  as the final character: `OPTIONS:` qualifies). A `TASK:` bullet with nested
  notes would parse as a drawer, not a micro — the exact opposite of intent —
  unless the drawer predicate gains a carve-out for one English word. That
  carve-out would then forbid a legitimate drawer named `TASK:` forever and
  complicate every drawer call site (`is_drawer_title`, catalog, slug match).
- It shouts. A task with six micros becomes six shouting lines; drawers
  already shout, and they denote structure, not work.
- Prefix readability is worse than suffix/marker readability at scan time
  because the eye must skip the same token on every row.

### 3.4 Why not store `##` / `###`

- `##` at a bullet body start reads as a Markdown heading fragment. Inside a
  list item it stays literal text, but every Markdown-aware tool (Obsidian
  outline, exports, PDF render catalog in decision
  `code-copy-reads-render-time-catalog`, third-party linters) sees heading
  syntax in a non-heading position.
- `#`-runs already mean "tag depth" (`#a/b`) and "heading depth" (`## H2`) in
  the same vault. A third meaning ("micro depth") forces every reader to use
  position context to disambiguate.
- Stored depth duplicates the indent that already encodes depth. Any
  outdent/indent/reorder (move gestures, `task-move`, manual edits) silently
  desyncs the stored count from the true depth until something repairs it.

### 3.5 Recommended: one stored `›`, depth rendered by repetition

Store exactly one marker per micro bullet, always in the same position
(bullet-body start, after the list marker and checkbox test):

```markdown
- [ ] #task Fix the leak [created:: 2026-11-20] ^abc123
	- › Confirm the rollout owner
		- › Send the owner the final date
	- Attach the final checklist
	- NOTES
		- the checklist PDF lives here
```

Readers render the marker repeated by micro-nesting depth (1 → `›`,
2 → `››`, 3 → `›››`), followed by a fixed space. Writers accept 1+ `›`
(plus ASCII fallback `>` — see below) and normalize to one stored `›` where
depth is recomputed from indentation. Display repetition is a pure function of
tree depth, so moves never rot.

Why `›` (U+203A, single right-pointing angle quotation mark):

- No Markdown, tag, heading, quote, checkbox, drawer, or field meaning
  anywhere in Bob's grammars or CommonMark. `is_drawer_title` rejects it at
  lead (not `A-Z`/`0-9`), so no drawer collision by construction.
- One codepoint, narrow, visually quiet; repetition (`›››`) stays compact and
  scans as depth without shouting. It reads as "sub-point of the above,"
  which is exactly the semantics.
- Typable via the `..` alias (two dots visually suggest the angle) and via
  toggle; nobody must find it in an IME. ASCII `>` is the accepted fallback
  input that normalizes to `›` on commit (mirrors the existing slug/literal
  drawer normalization pattern).
- Greppable (`rg '›'`), distinctive in diffs, and outside the
  `escape_task_text` / `escape_note_inline` hazard sets, so no escaper changes
  leak into prose. Only the micro-aware bullet renderer touches it.

Alternatives considered and rejected: `→` (wider, arrow implies direction /
assignment; also used in prose "a → b"); `▸`/`•` (bullet-like; `•` collides
with list-marker normalization); `- [>]` (custom checkbox status: Tasks
plugin may index it as a task with an unknown status, which defeats "not a
task until promoted," and checkbox semantics invite "checking the micro"
directly instead of via the successor flow); trailing markers (`… ›`, `:›`)
(suffixes hide at line end under wrapping and conflict with the trailing-edge
type/field position).

**Adjustment called out:** this replaces the prompt's `TASK:` / `#task` /
stored-`##` proposals with stored-`›` + rendered repetition. The `..` alias
idea is kept; its expansion target changes from `- #task ` to `- › `.

## 4. NOTES drawer default and capture routing

**Agree with the direction; adjust the rollout.** The rule should be:

- Under a task, every direct child is exactly one of: managed line/log,
  nested task (`- [ ]`, unchanged), drawer title, `›` micro, or `NOTES`
  entry.
- Capture's note-less `@route+id` (and `@route+id#drawer`) keeps its current
  file-each-bullet behavior, but plain bullets land in an explicit `NOTES`
  drawer (created on demand at the plain-child anchor, like any missing
  drawer) unless they are drawer bullets, `›` micros, or explicitly routed
  with a `#drawer` suffix. In other words, capture starts writing the
  `NOTES` title that today is implicit.
- `@foo+bar` (sub-bullet capture) with no drawer and no `›` marker nests the
  new line as a `NOTES` entry under the target task. With a `#drawer` suffix
  it lands in that drawer (unchanged). With a leading `›` (typed or via
  `..`) it lands as a micro at the appropriate level. A drawer shortcut at
  that position stays refused (`drawer_bullet_position`), unchanged.
- Hand-written plain notes do **not** move on read. `NOTES` is a write-time
  default plus a reconcile affordance, not a read-time reinterpretation.
  Reads treat a bare plain child as a `NOTES` entry logically (so old notes
  behave sanely) but do not rewrite the file until the next capture/split/
  reconcile write touches that block. This avoids a vault-wide rewrite and
  matches how drawer creation already works (created on demand, never
  retroactively).

Migration consequences: existing tasks with dozens of bare plain notes will
show a logical `NOTES` grouping with no file churn; the first write materializes
one `NOTES` title. Promotion, split, and the successor scan must all use the
same logical grouping so pre- and post-migration blocks behave identically.
Vectors must cover: note-less multi-note capture with mixed drawer / micro /
plain bullets; `@id#drawer` explicit routing; childless ALL-CAPS staying a
plain note (still *not* a drawer, still *not* auto-moved into `NOTES` as a
title — it becomes a `NOTES` entry); reserved names still refused.

## 5. Semantics: what a micro is (and is not)

Pin these before implementation; each is an adjustment that narrows the prompt
where it was silent:

1. **A micro is a plain bullet with a marker, not a task.** It carries no
   checkbox, no `#task`, no `created`, no block ID, no fields (`priority`,
   `scheduled`, `dependsOn`, `type`), and no Task Link. Anything needing those
   should be a real nested task (`- [ ]`) or be split first. This keeps the
   Tasks plugin, Dataview, freshness, lanes, and Blocked derivation untouched:
   micros are invisible to all of them until promoted/split/opened.
2. **Nesting is allowed; status flows downward.** A `››` micro's fate follows
   its parent `›`: opening the parent promotes the whole subtree (children
   become the new task's micros/notes, preserving relative depth minus one);
   cancelling the parent cancels the subtree. Non-top micros are never
   individually actionable in the successor picker — they render as indented
   context under their top-level `›`, exactly as the prompt suggests.
3. **Drawers and micros are orthogonal.** A micro never *is* a drawer and never
   lives *as* a drawer title. Micros can live inside a drawer (a drawer entry
   that starts with `› ` is a micro in that drawer) and drawers can live under
   a micro's subtree as ordinary structure — but promotion maps them
   separately: micros → tasks, drawers → H2 sections, plain notes → notes
   under the appropriate section/task.
4. **Identity is positional until promotion.** Micros have no block IDs, so
   moves/edits are positional like notes today. Opening/splitting mints IDs at
   promotion time (reusing a trailing `^anchor` when present, per split
   rules). No ID maintenance burden for unpromoted micros.
5. **Closing the parent never auto-closes real tasks.** Only micros listed as
   successors are offered; nested `- [ ]` tasks under the closing task keep
   today's behavior (and today's `merge_source_open_subtasks`-style refusals
   where they apply). A micro that was already struck (`~~…~~`) is complete
   history, not a successor.

## 6. Successor flow (close-time review)

### 6.1 What the prompt gets right

Closed-by-default top-level micros with an explicit per-row decision (open /
pull-in / cancel) directly serve "make sure I finished everything." Showing
deeper micros as non-actionable context is correct — their fate follows the
parent, and offering them individually would let the picker build
inconsistent trees.

### 6.2 Adjustments: reuse the picker, avoid four new global keys

The prompt proposes `Ctrl+X` (open), `Space`/`Tab` (check/pull-in),
`Ctrl+Shift+X` (cancel) on a successor panel. Three problems:

- `Ctrl+X` is Cut everywhere, including Obsidian modals; stealing it in one
  panel (even scoped) teaches a conflict that bites as soon as focus slips.
  `Space`/`Tab` already answer walk rows and move focus; overloading them in a
  second-modal context is a mis-press factory.
- The existing successor picker already solves "one gesture, N candidates,
  explicit choice, nothing preselected" with KEYS/NUMBER + PICK semantics,
  audit-tested vectors, Mac in-panel support, and capture `-p` parity. A
  parallel panel duplicates all of that for one row source.
- "Closed by default" needs a file-encoding answer: today successors write
  nothing until picked. If unpicked micros must visibly "stay closed," that
  implies a write on close (strike the micro? stamp something?). The prompt
  both says successors "are closed by default" and that cancel "strikes out
  after closing the parent" — those two writes need one coherent rule (below).

Recommended instead:

- Micro successors enter the **existing successor picker** as one new group
  (e.g. `micro_tasks`, additive `micro_task: true` field on the row, same
  KEYS/numbering/PICK wire as `hand_off`). Title the group so its default is
  legible: unchecked = stays closed history; checked-with-open = split to
  task; checked-with-pull-in = split + link today.
- Row verdicts reuse picker-local keys (numbers/letters + explicit Open /
  Pull in / Cancel actions already present in the verdict-copy
  infrastructure), not global `Ctrl+X` chords. If Obsidian-side chords are
  still wanted, scope them to the modal and prefer unclaimed leaders (the
  `Ctrl+G` leader family already exists in Mac Capture; an Obsidian-side
  equivalent beats stealing Cut).
- Semantics per top-level `›` row:
  - **Leave unchecked (default):** parent closes; the micro bullet is struck
    (`~~› text~~`, children struck with it positionally) as closed history.
    No new task, no link. This makes "closed by default" a real file state.
  - **Open:** split the micro into a new open task in the same note (same
    writer as `task split`: minted ID, children re-based, stub
    `- [[#^id|Alias]]` left in place, `LINKED FROM (💬 mentions)` added). The
    stub in the closed parent is struck to show it was not finished there,
    with the link as provenance — matching the prompt's "crossed out with a
    link to the parent," but with the link direction fixed: the closed parent
    holds a struck stub *to the new task*, and the new task holds the
    `LINKED FROM [[parent-task]]` mention (split's existing shape). Do not
    write both a forward link and a backward link with different text; reuse
    split exactly.
  - **Pull in (open + link today):** Open as above, then link the new task
    under today's daily file (same write as a picked successor: raised to
    Next, stamped fresh, block ID ensured). Only offered when the new task
    can hold a link (open, not Blocked); otherwise muted with the reason,
    like any successor row.
  - **Cancel:** parent closes; the micro is struck without any completion
    implication and, unlike the default-close strike, carries an explicit
    cancel marker (reuse the Cancel Log convention or a `~~` + `(cancelled)`?
    — decide in design; do not invent a third strike flavor). The distinction
    default-close vs cancel must be exactly one bit in the file, documented in
    the glossary, or drop the distinction and keep one "not completed" state.
    I recommend keeping both but encoding cancel as struck micro + parent
    Cancel Log entry, reusing existing log machinery instead of new inline
    syntax.

Non-top micros render indented under their top row, muted, with no keys —
as the prompt says. Their bytes follow the parent's verdict (struck with it,
or moved with it on open).

### 6.3 What "check with Space/Tab" becomes

Under this mapping there is no separate "check the successor" step: pull-in
*is* "open + link today" in one picker action. That removes the two-step
(open, then check) the prompt describes, which could strand opened-but-never-
pulled tasks. If the two-step is truly wanted, the opened task is just an
ordinary new task afterward — it can be pulled with any existing pull-in path
— and the picker does not need `Space`/`Tab` at all.

## 7. Capture ergonomics: `..` and the toggle

Keep both ideas, with tightened scope:

- **`..` alias:** expand `..` to `› ` only at an authored bullet-body start
  (after `- ` / `  - `), never mid-line, never on the parent line, never
  inside code. `- ..` → `- › `; `  - ..` → `  - › `. Mid-line `..` (ranges,
  prose, `..` path components in dependency parsing) must not expand — the
  alias is positional, like the existing `- #` drawer shortcut and the
  `/`→`#` notebook alias. `bob capture-parse` reports the expansion in preview
  so dry-run and commit agree, and undo is one keystroke (the toggle below).
- **`Ctrl+G T` toggle:** the `Ctrl+G` leader already exists (today: `U`
  toggles line case; `Esc`/`Ctrl+[`/second `Ctrl+G` cancels). Adding `T`
  ("toggle micro") fits the family: on a bullet row it adds `› ` when absent
  and removes one leading `› ` when present; on a parent line it beeps (micros
  are children, never the task line itself). Multi-line selection applies one
  direction to every touched bullet, mirroring the `U` behavior. It acts on
  the native text view so undo/IME/accessibility behave, and Bob's live parse
  re-reads the result as authority — same contract as the case toggle.
- Both surfaces must share one resolver (menu, `capture-parse`, dry-run,
  commit), per the bullet-drawer precedent (`capture-bullets-mirror`): a row
  is valid only when committing its literal bytes reaches the row's intent.

## 8. Merge creates a micro

Agree, with the "but there is more work" called out explicitly:

- Merging source `S` into target `T` (or drawer/section container) creates
  one new top-level `›` micro in the container: title bullet
  `- › <S description>` (via `clean_description`, no backlink — same
  provenance rule as today), `S`'s authored children copied beneath it with
  relative structure, live anchors/fields stripped outside code (same
  strip rules as `task-merge.md` §2), same-note link naming, fences
  byte-preserved.
- Preconditions carry over: open nested tasks in `S` refuse
  (`merge_source_open_subtasks`); managed children stay on `S`; dependents
  re-point; `S` is cancelled with `merged into [[T]]`; prerequisites warn.
  The only delta from today's merge is the title bullet gains `› ` and the
  group lands at the container's plain-child anchor (or drawer/section
  insertion point) rather than as a plain note.
- Vectors must cover multi-source merges (one `›` group per source, typed
  order), drawer/section containers (micro inside the drawer/section, not
  promotion to task), and the `prerequisites_left` / `successors_orphaned`
  reports (unchanged shape).

## 9. Glossary term (draft)

> **Micro Task** (aka micro)
>
> A plain sub-bullet of a task explicitly marked as a unit of work with a
> leading `›` (`- › Confirm the owner`). A micro is not a task: it has no
> checkbox, `#task`, `created` stamp, block ID, or fields, so it never
> appears in lanes, the walk, or queries until it is promoted. Micros nest;
> a nested micro's fate follows its top-level parent. Drawers hold structure
> (`REQUIREMENTS`), micros hold work; `NOTES` holds everything else.
> Promoting a task turns each top-level micro into a task and each drawer
> into an H2 section. Closing a task offers each top-level micro as a
> successor (open, pull in, or leave closed); split turns any micro into a
> task on demand. Merging a task into another task files it as a micro.
> Capture types a micro with `..` or `Ctrl+G T`. See `docs/capture.md`,
> `docs/task-split.md`, `docs/task-merge.md`, and
> `decisions:capture-bullets-mirror-the-task-block`.

## 10. Open questions for the designer (Bryan)

1. Should a micro inside a drawer promote to a task in that drawer's future H2
   section, or to the note's `## Tasks` intake? (I assume the former on
   promotion, the latter on split-from-daily — confirm.)
2. Keep both default-close strike and explicit-cancel strike, or collapse to
   one "not completed" state? I lean keep-both-encoded-as-strike-vs-strike+
   Cancel-Log-entry, but a single state is defensible and simpler.
3. Is ASCII `>` an acceptable input fallback for `›`, or should input require
   the alias/toggle (strict `›`-only)? I recommend accepting `>` and
   normalizing, but strict-only is a smaller grammar change.
4. Should `›` micros be offered on *every* close (Done + Cancel + park), or
   only on Done? I recommend Done + park (both leave the plan), not Cancel
   (cancel already explains incompleteness), but the picker contract supports
   either.

## 11. Suggested implementation shape (not a plan)

Grammar + renderer first (`›` lex/parse/normalize, repetition-by-depth
render, drawer-predicate exclusion proof, escaper non-interference), then
capture routing (`NOTES` default + `..` + toggle behind one resolver),
then promotion/split reuse, then successor-group + merge-title-bullet, then
vectors/docs/glossary, with `just check` + `just docs-check` gates. Each stage
keeps preview/commit agreement (dry-run equals commit modulo `dry_run`) and
adds vectors before behavior, following the `task-merge` / `task-split`
contract-first pattern.

---

### Sources consulted (independent)

- `src/native/task_children.rs` (child classifier), `src/native/capture_drawers.rs`
  (`is_drawer_title`, reserved keys, insertion geometry), `src/native/task_text_escape.rs`
  (`#task` neutralization), `src/native/task_merge/` + `docs/task-merge.md`,
  `docs/task-split.md`, `docs/capture.md` (authored sub-bullets, drawer grammar,
  close classification), `docs/projects.md` (promotion successors),
  `docs/task-dependencies.md` §11–12 (successor offers), `docs/reference/mac-capture/keyboard.md`
  (`Ctrl+G` leader), bob-plugins `110-project-seed.js` / `212-project-conversion.js` /
  `667-plugin-project-promotion.js` (seed conversion), sase memory
  `cli_rules.md`, `docs.md`, glossary `task-drawer` / `task-link` /
  `task-dependency-link` / `task-successor` / `successor-offer`, decisions
  `capture-bullets-mirror-the-task-block`, `capture-sigils-say-where-what-how`,
  `task-deps-are-depends-on-links`, `unblocked-tasks-are-offered`.
- Deliberately not consulted: the parallel swarm reports (`__cdx`, `__cld`,
  `__grk`, `__gem`); filename presence only was used to avoid overwrite.
