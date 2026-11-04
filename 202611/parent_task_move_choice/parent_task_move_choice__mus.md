# `^^` deferred parent-task picker for sealed project-note capture

Research report. Researcher: mus. Date: 2026-11-04.

## 1. What was asked

Bryan wants a new `^^` capture syntax for use with the `@foo[^:]bar@`
sealed project-note form (the form whose child pull-in the bob-cli-gl epic
just shipped). When `^^` is the entire contents of a capture bullet, the
user should be prompted — after submitting the capture — to select one or
more tasks from the parent project (`foo.md`). The selected tasks are then
added as `^id` / `:id` move bullets, exactly as if the gl-epic syntax had
been typed directly. The post-submit prompt should take inspiration from
the successor (Pull-In) prompt, except each row needs three states:
unpicked (the default), `^` (move plain), and `:` (move, make Next, and
link). The brief asks for lead design that is intuitive, reliable, and
beautiful, plus a critique and a recommended solution.

## 2. Current system (verified in tree this session)

### 2.1 The gl epic: explicit bare-`^id` / `:id` move bullets

`docs/capture.md` §"Moving parent tasks in" (verified by reading the file)
defines the shipped behavior: in a sealed project-note item, a first-level
bullet holding only `^<id>` moves that open top-level task from the parent
note into the new note's `## Tasks` intake in draft order; `:id` does the
same, plus raises it to Next and links it as `@<new>:<id>` would. A lone
`^` / `:` is an unfinished move: the editor opens a move picker
(`capture-parse` needs `project_task_move`) and `bob capture` refuses it
with `` `- ^` needs a task from foo.md; pick one or delete the bullet ``.
Move bullets are bare-only (any trailing text, marker, checkbox, or nested
bullet is a `move_bullet_*` teaching error), share a namespace with
authored IDs in the item, resolve against the parent note only, travel
through the `task move` planner (identity, history, and links preserved;
no fresh stamp), and commit atomically with the rest of the batch. The
move-bullet lexer (`src/native/capture_language/move_bullet.rs`,
`scan_move_bullet`) is claimed from the raw line before trailing-ID
stripping, so `bob capture` (`item.rs`) and `capture-parse`
(`editor_parse.rs`) agree byte-for-byte, and moved rows are excluded from
`@route:id@` successor offers.

### 2.2 `^^` today is inert task text

Verified with the freshly built debug binary
(`$CARGO_TARGET_DIR/debug/bob`):

- `capture-parse` on `Finish packet @cash^goog-exit@\n- ^^` reports
  `grammar: 10`, `mode: "project_note"`, `needs: []`, no spans on the
  bullet, `sub_bullets: ["^^"]`. It would capture a new task literally
  named `^^`.
- `capture-parse` on the same draft with `- ^` reports `mode:
  "incomplete"`, `needs: ["project_task_move"]`, marker plus
  `interactive_placeholder` spans, and
  `sub_bullet_moves: [{sigil: "^", block_id: null}]`.
- `capture-complete --cursor` anywhere inside `^^` returns `context:
  null` with no candidates.
- Code cause: `scan_move_bullet` on body `^^` sees sigil `^`, remainder
  `^`, whose first byte is not ASCII alphanumeric, and returns `None`
  (not move-shaped); `lex_project_task_id("^^")` likewise returns `None`
  (first char after sigil is not alnum), so the bullet falls through to
  the new-task path. `docs/capture.md` and `tokens.rs` both confirm `^^`
  stays ordinary prose at item start.

Consequences: claiming exactly `- ^^` (first-level bullet, sealed
project-note item, nothing else on the line) as a picker placeholder
breaks no working draft — nobody means a task named `^^` — and the claim
is narrow: parent lines, nested lines, non-project items, and escaped
`- \^^` keep today's meaning.

### 2.3 The successor Pull-In protocol is the prompt to copy

`docs/task-dependencies.md` §§12.5, 12.6, 12.14 (verified by reading):

- Offers ride one numbered, keyed protocol across every surface:
  `unblocked[]`/`successors[]`/`keep_moving[]` rows with
  `offer {key, n, group, selected, destination}`, grouped into
  `pull_in.groups[]` with Bob-authored copy, folded not-offered counts,
  and a top-level `pull_in {supported, offer_count, choice,
  picked_count}`.
- CLI selection is `-p/--pull-in` (`all`, `none`, or comma list of offer
  numbers and/or keys); unknown/stale picks are teaching errors that
  write nothing. Hidden `--require-pull-in-choice` turns an unanswered
  offer set into a write-free `pull_in_choice_required` refusal. Without
  it, an unanswered run reports offers and writes nothing relevant.
- Presentation is preview-first: dry-run/human output lists numbered
  `offer N` rows under group headers with a `-p 1,2 · -p all` hint; Bob
  Mac Capture adds an in-panel multi-select choice step on Return, then
  submits one atomic `bob capture --pull-in`. Esc returns to the draft
  with nothing written; ⇧↩ submits with none. Copy rules (§12.6) mandate
  existing glyphs and colour tokens only, at most 3 notice rows, and
  group headers (`Hand-offs`, `Project ‹note›`, `Pull from ‹N›`).

### 2.4 Note pull (bob-cli-gj) is the closest working precedent

The in-progress gj epic (`sase bead read bob-cli-gj`) makes a lone
`@route` item open the same Pull-In choice over that note's eligible
residents (Pending/Next/Ready, decided `lanes = open_lanes`), with
nothing preselected, `--require-pull-in-choice` refusal, and a
`nothing_to_pull_in` refusal carrying fold counts when the note has
nothing to offer (decided `empty_pull = refuse`). A `^^` placeholder is
gj's shape transposed inside a project-note item: an explicit request
for "some of that note's tasks, chosen after I see them," rather than
inline-authored IDs.

### 2.5 Per-row destinations are explicitly out of scope

Bead bob-cli-7j (READY, verified) proposes per-row destination overrides
for `--pull-in` and Mac, deferred from the Successor Offers epic. `^^`
picks must therefore use existing placement: `^` picks land unlinked in
draft order; `:` picks link exactly as explicit `- :id` moves do (under
`#pomodoro` or the task's effective type). Destination retargeting stays
a 7j follow-up.

## 3. Critique: is this a good idea?

Yes — with adjustments. The core insight is right, and the request names
the right model (successor prompt) and the right hard part (tri-state).

**Why it earns its place.**

- **It completes gl instead of competing with it.** The gl inline picker
  (`- ^` → candidates) serves editors; the CLI has no inline step, and
  even in an editor you often know you want "two or three of cash's tasks"
  before you know their IDs. `^^` is the blind-capture half of gl: defer
  the choice to a moment when the candidates are visible.
- **The spelling is well chosen.** `^^` reads as "more than one `^` / fill
  me in," is trivial to type, has no grammar meaning anywhere today
  (§2.2), and — claimed narrowly as the whole bullet body — is
  unambiguous. Lone `^` already means "pick one now"; `^^` meaning "pick
  several later" is a teachable pair.
- **It reuses the two best-tested paths in capture.** Expansion is into
  literal gl move bullets (write path unchanged, atomicity and guards for
  free); selection rides the §§12.5/12.14 Pull-In protocol (numbering,
  picks, refusal, Mac card, folds for free). No third task-copy path, no
  second transaction, no Swift grammar fork — the thin-client decision
  (`decisions:mac-capture-is-a-thin-client`) stays intact.

**Risks, in order of importance.**

1. **Two pickers for one pool.** Inline `- ^` (one ID, before submit) vs
   deferred `- ^^` (several, after submit) overlap. Without crisp copy
   and docs, users will not know which to reach for. The rule must be one
   sentence: "`^` when you know the task, `^^` when you want to browse."
2. **Tri-state selection grammar.** `-p` today is select-or-not. Adding
   per-row `^`-vs-`:` without turning picks into line noise is the design
   crux; §4.5 proposes a two-character prefix that mirrors the authored
   bullets.
3. **The whole batch waits.** An unanswered `^^` must hold the new note,
   the new tasks, and the daily links — not just the moves — because
   placement order and parent-last write ordering only exist inside one
   atomic batch. A user who expected "create now, move later" will be
   surprised; the preview must show what *will* be created so the hold
   reads as pending, not broken.
4. **Offer-space collision.** `^^` candidates live beside `@foo:bar@`
   successor offers and explicit `- :id` links in one number space. Moved
   rows must stay out of the offer set (gl rule) and picked rows must
   count once (as moves that also link, like explicit `:` moves already
   do via `project_note.task_links`).
5. **Placeholder proliferation.** If `^^` also gains `::`, `^^:`, suffix
   sigils, or text/markdown companions, every combination needs
   semantics. One placeholder spelling, bare-only, with per-row sigil
   choice in the picker — nothing else.

**Rejected alternatives and why.**

- **Defer the existing lone `^` instead of adding `^^`.** Breaks the
  editor inline flow gl just shipped and removes the "pick one now" fast
  path. `^^` keeps both speeds.
- **A `::` placeholder for link-default picks.** Two placeholders double
  the grammar for a choice the picker already expresses per row. Refuse
  `::` with a teaching error pointing at `^^`.
- **Post-submit moves as a second capture/transaction.** Splits atomicity
  (new note without its tasks, parent edited later), duplicates write
  ordering, and invites partial failure. Expansion-before-planning keeps
  one batch.
- **Manual composition (`bob capture-tasks -r foo`, then paste IDs).**
  Already possible and worth documenting, but it is the thing `^^`
  beautifies away; it is the fallback, not the design.
- **Fuzzy auto-pull ("take tasks matching these words").** Violates the
  settled-heads-up rule (`decisions:similar-tasks-are-a-settled-heads-up`):
  Return must never commit something the user did not explicitly choose.
- **Copy instead of move.** Same rejection as gl: splits `[id::]`
  identity, link repair, and freshness history. Move only.

## 4. Adjustments (what I would change)

1. **Claim exactly `- ^^`, bare-only, first-level, sealed project-note
   items only.** Any other token on the line, any nesting, checkbox,
   drawer, marker, or non-project item keeps today's behavior with the
   existing or a mirrored teaching error. One item holds at most one
   `^^` (a second is a duplicate teaching error — two placeholders would
   offer the same pool twice); several items may each hold one, each
   scoped to its own parent, numbered jointly in draft order.
2. **Do not add a `::` placeholder.** `^^` is the only deferred spelling.
   `- ::` refuses with: `` `::` is not a picker; write `^^` and choose `^` or `:` per task ``.
3. **Expand picks into literal move bullets, then run the gl path
   unchanged.** A `^` pick becomes `- ^id` at the placeholder's slot; a
   `:` pick becomes `- :id`. Guards (movable root, `^prj`, closed/nested,
   blocked-birth, dependency deadlock, duplicates, collisions), parent-last
   write order, link repair, dry-run equality, and `moved_from` reporting
   all come for free because the planner cannot tell a picked bullet from
   a typed one.
4. **Unanswered `^^` holds the whole batch — on every surface.**
   Without picks, `bob capture` reports the candidates as offers and
   writes nothing (gj precedent); with `--require-pull-in-choice` it
   fails `pull_in_choice_required`. The Mac preview shows the new note's
   authored tasks as provisional plus the candidate group, so "nothing
   written yet" is visible, not mysterious.
5. **Tri-state picks via a sigil prefix on `-p` tokens.** Each pick token
   accepts an optional `^`/`:` prefix mirroring the authored bullets:
   `-p ^1,:2,3` moves 1 plain, moves+links 2, moves 3 plain (bare =
   `^`). `:all` moves+links everything; `all` moves everything plain;
   a sigil on `none` is a teaching error. Prefix position is unambiguous
   (no key, number, `all`, or `none` starts with `^`/`:`; block IDs never
   contain `:` so suffixes would be the ambiguous side). The dry-run hint
   teaches it: `-p ^1,:2 · -p :all · bare is ^`.
6. **One shared number space.** `^^` candidates and successor offers
   number together in draft order (existing `number_draft_offers`
   machinery extended, not forked). A `:` pick appears in
   `project_note.task_links` exactly like an explicit `- :id` move, and
   clients must not double-count it — same rule gl already documents.
7. **Empty parent refuses like note pull.** No movable tasks under `^^`
   with any `-p` value (or none) → write-free refusal naming the parent,
   its open count, and the fold reason (gj's `empty_pull = refuse`
   precedent; suggest code `nothing_to_move_pick`). Never silently
   create the note and drop the placeholder.
8. **Editor behavior: complete inline, defer at submit.** `capture-parse`
   reports `^^` as incomplete needing a new `project_task_pick` need
   (distinct from `project_task_move` so clients route to the tri-state
   card, not the single-select picker). `capture-complete` inside `^^`
   returns the existing `project_task_move` rows so typing filters the
   parent's tasks; accepting one inserts a `- ^id` sibling after the
   `^^` line and keeps `^^` for more (gl's shift-return chain pattern).
   Any `^^` surviving at submit triggers the §12.14 choice step. CLI and
   editor thus share one rule: surviving `^^` means "ask me."
9. **Copy follows §§12.5–12.6 exactly.** New group header `Move from
   ‹parent›` (📥 glyph family reads "pull in," but moves are not links —
   use the existing move wording `moved`/`would move` from gl, never
   `linked` for `^` picks). `:` picks use the link vocabulary they
   already use as explicit moves. No new glyphs, no new hex, 3-row notice
   cap, 48-char truncation — the §12.6 rules verbatim.
10. **Grammar 10 → 11, additive JSON only.** `capture-parse` gains `^^`
    spans/needs; results gain an additive candidate group/trigger (suggest
    trigger `parent_pick`, group `project_move`) riding `pull_in`. No
    `schema_version` change; mark `!` only if the contract breaks
    additive compatibility (it should not). Ship on the daily train
    (`decisions:bob-cli-releases-ride-a-daily-train`).

## 5. Recommended solution

**Grammar (bob-cli, `docs/capture.md` first).** Under both seals, a
first-level `- ^^` bullet with no other text is a deferred parent-task
pick. It composes with explicit moves (`- ^a`, `- :b`) and new tasks in
the same item; the placeholder occupies its draft slot and expands there.
Duplicates (`^^` twice in one item), text/markers/checkboxes/nesting
around it, `::`, and non-project placements refuse with mirrored
`move_bullet_*`-style codes. Bump the capture grammar to 11.

**Planning order (reuse, do not fork).** Parse → render new note (new
tasks only) → resolve explicit moves (gl path) → collect `^^` candidates
from the parent snapshot minus already-moved/explicitly-named/duplicate
IDs → stage picks as expanded move bullets → move planner (parent-last,
link repair, collision rename) → link explicit `:` and `:`-picks →
successor-offer pass (new rows only; picked/moved rows excluded) →
inbox-route detection → guarded all-or-nothing commit (new note, parent,
daily note, repaired link notes). Any refusal or `NoteChanged` race
writes nothing. Dry-run previews the provisional new note, the candidate
group with folds, and the `-p ^1,:2` hint; its JSON equals the real
result apart from `dry_run`.

**Completion.** After `- ` inside a sealed project-note item, `^^` is
completable as today is for `^`, returning `project_task_move` rows
(document order on empty query, `@route+` ranking on typed text, ID-less
rows with suggestions, ineligible rows disabled with reasons). Accepting
inserts a sibling `- ^id` and retains `^^`. This is additive: no new
context string for the row source, one new `needs` value for the
placeholder itself.

**CLI.** `-p [^|:]N|key` per §4.5; `all`/`none` unchanged plus `:all`.
Unanswered `^^` → offers reported, nothing written (exit 0 with the
"nothing moved in · choose with -p ^1,:2 or -p :all" line); plus
`--require-pull-in-choice` → `pull_in_choice_required`. Stale/unknown
picks and sigil-on-`none` are teaching errors. `nothing_to_move_pick`
when the parent has nothing movable.

**Mac presentation (beautiful).** One candidate group, "Move from
`foo`," with status chips and type annotations (recognition, as gl
requires). Space cycles each row ∅ → `^` → `:` → ∅ (default ∅); ⌘A
fills `^`; ⇧⌘A fills `:`; footer tallies `2 move · 1 move+link`; Return
submits via the extended `--pull-in`; Esc returns to the draft; ⇧↩
submits none. The dry-run preview shows provisional new-note tasks above
the group so the pending batch is legible. Presentation only — Bob owns
the grammar and the write.

**Docs and tests.** `docs/capture.md` gains a "Defer the pick with `^^`"
section under "Moving parent tasks in" (the one-sentence `^`-vs-`^^`
rule, tri-state table, hold-the-batch statement, `-p` prefix grammar);
`docs/completion.md` and `task-dependencies.md` §§12.5/12.14/12.20 gain
the group, trigger, codes, and copy rows. Tests mirror gl's MV/MC
vectors: bare-`^^` acceptance, slot-order expansion, `^`/`:`/∅ per-row
semantics, one-per-item refusal, `::`/text/marker/nested/escaped errors,
per-item scoping across multi-item drafts, unknown/closed/`^prj`/
nested/duplicate/collision refusals, blocked-birth and deadlock wiring,
empty-parent refusal, atomicity on parent-change races, dry-run JSON
equality, `-p` prefix parsing (including `:all` and sigil-on-`none`),
shared numbering with offers, and Mac-observed transcripts for `^^`
with and without a project-note seal.

In one sentence: keep the proposal's `^^` placeholder and post-submit
timing, give it exactly one bare spelling whose picks expand into the
shipped gl move bullets inside the single atomic batch, select rows
through the existing Pull-In protocol extended only by a `^`/`:` token
prefix, and let Bob's rows teach the parent's tasks so the Mac renders a
tri-state card with Space-cycle selection and unpicked-by-default rows.
