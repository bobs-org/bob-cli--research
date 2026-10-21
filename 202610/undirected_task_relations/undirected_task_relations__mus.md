# Undirected task relations: design research (`mus`)

Research date: 2026-10-21. Context: proposal to make any link relation
without a description an undirected relation, showing `links` instead of
`links to` / `links from`; relations with a description become directed
(glossary updates for directed/undirected); `~~` only makes sense with a
description. Goal: intuitive, reliable, beautiful.

## TL;DR and recommended solution

Yes, build the *presentation* of this idea, but do **not** build it as a
second storage system. The proposal's instinct is right: most unlabeled
edges mean "see also / related to", which users think of as symmetric,
and the current `links to` / `linked from` chrome over-explains them.

But tying directedness to label presence at the *storage* layer is the
wrong mechanism. Recommend instead:

- **Storage stays exactly as today**: one directed edge `(S, T, label)`,
  authored on S's `🪢 **LINKS:**` line, projected onto T's generated
  `🪢 **LINKED FROM:**` line. Owner `S` is fixed at creation and never
  changes when a label is added, changed, or cleared.
- **Presentation becomes direction-aware**: unlabeled edges render under
  a single `links` group on both ends; labeled edges keep the directed
  `links to` / `linked from` rendering with pills, arrows, and inverse
  phrasing. No vault rewrite, no reconcile migration, no identity change.
- **Vocabulary fix**: the proposal says "description" — the codebase and
  every doc says "label" (`RelationEntry.label`,
  `normalize_relation_label`, `|label`, `existing_label`,
  `labelSuggestions`). Adopt **label** everywhere; do not introduce
  "description" as a synonym.
- **`~~` without a label is refused**, not silently aliased to `~`. Two
  spellings for one act is unteachable; a teaching error naming `~` is
  intuitive and preserves a single owner.
- **Disk line names never change** (`LINKS` / `LINKED FROM` stay). Only
  human-facing group titles, chips, picker help, shell groups descriptions,
  human output verbs, and docs change.

Details and per-surface wording in §7. Vectors to add in §8.

## 1. Current state (what the proposal builds on)

All citations verified against this checkout on 2026-10-21.

**Contract.** `docs/task-relations.md` is the single contract every
implementation cites. Vocabulary (§1): a task relation is "a directed,
optionally labelled, inert edge from source S to target T", stored as one
entry on S's LINKS line. `LINKS` is the authored direct-child line
(`🪢 **LINKS:**`); `LINKED FROM` is the generated mirror
(`🪢 **LINKED FROM:**`) owned by reconcile, never read back as input.
Relationship modifiers (§1, §8) are capture's umbrella for `&`, `*`, `~`
(links to), `~~` (linked from); JSON names (`picker.relationship`,
`dependency_target`, `relationship_needs_text`, mode `task_dependency`)
keep their spelling and cover all four.

**Rust.** `src/native/task_relations/` owns the model:

- `mod.rs`: `KNOT_EMOJI` (`🪢`), `LINKS_LABEL`, `LINKS_TO_LABEL`,
  `LINKED_FROM_LABEL`, `BACKLINKS_LABEL`, `RELATION_SEPARATOR` (` • `),
  `RelationEntry { target, block_id, label, embedded, struck, aliased }`,
  `LinksLine` / `LinkedFromLine` verdicts (`Accepted`, `Empty`,
  `Malformed`, `NotALine`).
- `parse.rs`: `parse_links_line`, `parse_linked_from_line`,
  `links_children_of`, `linked_from_children_of`. Header tolerance (§3.4):
  missing glyph or `🔗`, authored `LINKS`/`LINKS TO`, mirror
  `LINKED FROM`/`BACKLINKS`, separators `•`/`·`/`,`/whitespace. Entry
  labels live before each LINKS link; mirror labels in `(…)` after each
  LINKED FROM link. Alias becomes label only when no label precedes it.
- `label.rs`: `normalize_relation_label` (trim, collapse whitespace, strip
  one trailing `:`, 1–40 chars), `parse_relation_label` (reader side, any
  length), `MAX_LABEL_CHARS = 40`, forbidden `[ ] ( ) " \\ | • * ~` plus
  controls, no leading `·`/`,`. `relation_label_quoted_form` gives the
  `|label` / `|"multi word"` capture spelling.
- `format.rs`: `format_links_line` (authored order, `label link` joined by
  ` • `), `format_linked_from_line` (canonical BK21 sort via
  `cmp_blocks_links`), `relation_insert_slot` / `links_insert_slot` /
  `linked_from_insert_slot` (§4 slots: LINKS after Cancel Log / Depends-On
  / BLOCKS / Sub-projects, else first child; LINKED FROM right after
  LINKS).
- `plan.rs`: `plan_links_edit` (`LinksEdit { add, remove, relabel }`,
  `LinksLinePlan::Noop/Malformed/InvalidLabel/Edits`), `plan_linked_from_line`,
  `linked_from_desired_after_delta`. New entries append; relabels stay in
  place; same-label re-add is a no-op; removing the last entry deletes the
  line; duplicate lines merge (first label wins).
- `tests.rs`: LK1–LK20 / LW vectors pin every parse/planner case.

**Capture.** `src/native/capture_language/relations.rs` scans `~` / `~~`
modifiers (`RelationRef { raw, direction, note, block_id, label, … }`,
`RelationDirection::To/From` in `editor_model.rs`, `scan_line_relations`,
strike guard `~~old~~`, `~~~` invalid, `\~` escape, `[[…]]`/backtick
protection). `src/native/capture/relations.rs` (`plan_relation_writes`,
`RelationOwner`, `resolve_relation_target`, `refuse_duplicate_labels`)
stages S's LINKS edit plus courtesy LINKED FROM writes in one batch via
the cli-core delta planner. `src/native/capture/relations_mirror.rs`
handles the mirror. `src/native/capture/output.rs` (`format_relation_update`)
prints `🪢 links to "T" · label   path ^id`, `🪢 "S" now links here · label`,
`🪢 relabeled`, `🪢 unchanged`, with `would …` dry-run forms.

**Reconcile.** `src/native/task_status_hooks/relations.rs`
(`reconcile_relation_lines`, right after `reconcile_blocks_lines`,
`load_relation_archives`, `RelationsOutcome`) derives
`mirror(T) = sort_canonical({ (S, label) })` over writable T (§6). Never
edits LINKS; mints missing source ids silently (`mint_block_id`, no
`[id::]`); respects read-only `done/` and the previous daily note;
byte-prefilters for `LINKED FROM`/`BACKLINKS`; honors
`relations.linked_from_lines: false` (removes mirrors, mints nothing —
`src/native/config/relations.rs`, default `true`).

**Completion / pickers.** `src/native/capture_complete/` (`model.rs`,
`candidates.rs`, `render.rs`, `shell.rs`, `cli.rs`, `engine.rs`, tests in
`tests/relations.rs`, `tests/output.rs`, `tests/pomodoros.rs`): contexts
`relation_to` / `relation_from` / `relation_label`, shell groups
`"links to"` / `"linked from"` (`shell.rs:446-450`), candidate fields
`already_linked`, `existing_label`, `also_prerequisite`,
`disabled_reason`. `capture-parse` spans `relation_sigil`,
`relation_note`, `relation_block_id`, `relation_label_separator`,
`relation_label`; `relations[]` with `direction: "to"|"from"`;
`relation_grammar: 1` whenever the draft contains `~`.

**Chips (contract §10, vectors LC1–LC14).** Live relation index
(`api.relationIndex` v1 in bob-ledger-tools: forward + reverse maps, one
generation, `outgoing`/`incoming`/`labelSuggestions`), never the stored
mirror. Anatomy reuses `bob-dep-row`/`bob-dep-chip`; colour carries status,
never direction. Labels are muted small-caps pills on the arrow side:
LINKS `‹label› → (chip)`; LINKED FROM `‹inverse› (chip)` for the five
known inverses (`merged into→merged from`, `duplicate of→duplicated by`,
`follow-up of→followed up by`, `superseded by→supersedes`,
`split from→split into`), else `(chip) · ‹label› → this`. Unlabelled rows
wrap between chips; labelled rows one entry per visual row. Today LC1 is
`🪢 links to → (○ T)` even when unlabelled — the exact string the proposal
wants to change.

**Docs / glossary.** `docs/guides/link-related-tasks.md` ("Choose a
direction": `~` vs `~~`), `docs/capture.md#linking-tasks` (meaning,
guards, targets, refusals, inertness, human output), 
`docs/reference/capture-syntax.md` (`#tilde-link`, `#tilde-tilde-link`,
`#tilde-existing`, `#tilde-drop`), `docs/reference/vault-format.md`
(directed-relations example), `docs/reference/glossary.md#task-relation`
("A directed, optionally labelled, inert link … Add one with Capture `~` /
`~~` or the Task Card `l` / `⇧L`"), and memory strand `glossary:relation`
(same text plus linked references to Capture, Pomodoro, Task Link,
freshness). Prior neutral research `task_relation_labels.md` and
`task_relation_links.md` (+ `.diagrams.md`) document the shipped labelled
flow; one shipped guide example is already wrong (unquoted multi-word
`|follow-up of` never parses — LP7 requires `|"follow-up of"`).

## 2. Critique of the plan as written

**2a. "Show `links` instead of `links to` / `links from` for unlabeled" —
right instinct, underspecified surface.** Today direction words appear in
at least seven places: Task Card row titles (`Links to` / `Linked from`,
LG9), chips (`🪢 links to → (○ T)`, LC1), capture-complete groups
(`links to` / `linked from`), shell completion groups (same),
capture human output (`🪢 links to …` / `🪢 … now links here …`),
`capture-parse`/`capture` JSON (`direction: "to"|"from"`), and docs prose.
"Just show `links`" needs a per-surface table (§7): which strings change,
which stay because they describe *storage* (sigil direction) rather than
*presentation*. Changing JSON `direction` would break Mac Capture and
every picker for zero user gain — don't. Changing chip titles and human
verbs is the actual beauty win.

**2b. "Any relation with a description becomes directed" — good default,
bad trigger.** Empirically the heuristic matches use: bare links are
almost always symmetric "see also / related", while `follow-up of`,
`merged into`, `split from` are inherently directional. But making the
*presence* of a label flip the ontological kind is magic with sharp edges:
adding one word (`|see`) to an undirected edge would teleport its chips
from `links` to `links to` + `linked from`, change its Task Card section,
and reveal a direction the author never chose. Clearing a label does the
reverse. Users will experience this as instability ("I only added a word,
why did the other task's section change?"). The fix (§7): keep owner `S`
immutable; labeling only changes *rendering*, never storage or identity.
Document the transition explicitly: "labels reveal direction; removing a
label hides it".

**2c. "Use `description`" — reject the word, keep `label`.** Every layer
says label: `RelationEntry.label`, `normalize_relation_label`,
`parse_relation_label`, `relation_label`, `existing_label`,
`labelSuggestions`, `MAX_LABEL_CHARS`, all docs (§3.2 "Labels"), all chips
("pill"), all pickers ("relation card / relation field"). Introducing
"description" bifurcates search (`grep description` vs `grep label`),
help text, JSON, and the glossary. If the proposal truly means a second
free-text field distinct from the label, reject that too: no design in
`docs/task-relations.md` has room for two texts, the `(label)` mirror
syntax fits one, and two texts would double the inverse-table problem.
One text, called a label, phrased `S — ‹label› → T`.

**2d. "`~~` only makes sense with a description" — correct conclusion,
wrong remedy if it means silent aliasing.** The parenthetical "(otherwise,
it is the same as linking to a task directly using `~`)" reads as
"make unlabeled `~~` behave like `~`". Do not. Silent aliasing leaves two
spellings for one act, two picker paths to one owner, and an ambiguous
record: an unlabeled edge created via `~~` remembers the *wrong* owner
(the named task, not the captured task), so a later label reveals the
opposite direction from what `~` would have. The intuitive behavior is a
refusal with a teaching error at parse and at execution, in the picker,
and in the Linked-from stage: "`~~` names the other task as the source,
so it needs a label that reads from its side — use `~note:id` for an
unlabeled link, or add `|\"label\"`". This matches existing teaching-error
style (`operator_relation_error`, `relation_target`/`relation_label`
needs, `~~old~~` strike guard, `x~~1` "use one `~` list").

**2e. Is this a good idea at all? Yes — with the scope above.** Without
it, every "related to" pays for direction chrome (arrows, pills,
`linked from` sections, inverse lookups) that carries no information, and
newcomers reasonably ask "which direction should a see-also go?" The
proposal removes a real decision. But it must not become a second edge
system: no new line names, no dual storage, no new config key, no JSON
break, no mirror rewrite. The beauty is in *removing* chrome for the
common unlabeled case, not in adding machinery.

## 3. What "undirected" can mean (and which meaning to ship)

Three readings, one recommendation.

**A. Display-undirected, storage-directed (recommend).** Edge identity
stays `(S, T)` with `S` = authoring task (§5 "Edge identity is (S, T)").
`format_links_line` / `format_linked_from_line`, `plan_links_edit`,
`reconcile_relation_lines`, slot rules (§4), canonical sort (LK20/BK21),
and `mirror(T)` (§6) are untouched. What changes is only grouping and
wording: unlabeled outgoing + unlabeled incoming render together as
`links`; labeled edges render as `links to` / `linked from`. Deletion is
already symmetric in affordance (`removeLink(S, T)` from either end's ×,
§10 controls) even though storage is single-owner. Pros: zero vault
churn (reconcile is a no-op on disk — LR11 holds), no new failure modes,
no dual-write transactions, JS twins only regroup. Cons: markdown still
shows `LINKS` vs `LINKED FROM` for unlabeled edges — a deliberate,
documented leak ("line names are storage names; chips are the
presentation"). This matches the existing rule that chips render the live
index, never the mirror (§10, LC8, guarantee §13.4).

**B. True symmetric storage (reject).** Both tasks hold a `LINKS` entry
for one undirected edge (or a new `LINKS:` header without direction), no
mirror for undirected. Requires: canonical owner election for hand-added
pairs, dual-write transactions with rollback across notes (today cross-note
is S-commits-then-best-effort-follow-up, §8 — doubling it doubles the
"· 🪢 LINKED FROM not updated" class), dedup of `A→B + B→A` into one,
delete-from-either-removes-both semantics, `done/` + previous-daily
read-only handling on both sides, mint-on-both-sides rules, kill-switch
reinterpretation, and a vault-wide backfill that touches every existing
unlabeled edge (breaking LR11, the 2 s quiet interval, snapshots, and
`--dry-run` previews). It also breaks the "single source" guarantee
(§13.1: delete every mirror, one reconcile rebuilds byte-identical) by
creating two sources. Beauty on disk is not worth this reliability cost.

**C. Reciprocal auto-creation (reject).** Creating `A ~ B` unlabeled
writes both `A→B` and `B→A` directed edges. Same costs as B plus
permanent duplication: every unlabeled link costs two entries, two
mirrors, two index rows; relabeling one leaves a ghost twin; `plan_links_edit`
duplicate handling (first wins, LW9) fights the design. No.

Ship A. If disk beauty later demands it, revisit only after A has proven
the grouping — never as the first step.

## 4. Reliability hazards the design must close

**Identity and reciprocals.** Today `A→B` and `B→A` are independent and
cycles allowed (§5). Under A this stays true on disk, but display must
decide. Cases:

- Unlabeled `A→B` only: both ends show one `links` chip. ✓
- Unlabeled `A→B` + unlabeled `B→A` (user explicitly linked both ways):
  display must dedupe to one chip per unordered pair (else the same
  neighbor appears twice under one `links` row — ugly and confusing).
  × on the deduped chip removes *both* directed edges (else a ghost
  remains and the chip never clears). Reconcile keeps both on disk;
  only the live index dedupes. Warn nothing; this is not malformed.
- Labeled `A —follow-up of→ B` + labeled `B —follow-up of→ A`: keep two
  rows (LR19). Different meanings, different pills. No dedupe.
- Mixed `A→B` unlabeled + `B —see→ A` labeled: show `B` under `links`
  *and* under the directed section with its pill. Two edges, two truths.
  Tooltip must disambiguate ("links · also linked from with `see`").
  Rare; correctness beats brevity.

**Label transitions.** `plan_links_edit` relabels in place (§4, LW4).
Under A, relabeling `None → Some("see")` moves the chip from `links` to
`links to` on S and from `links` to `linked from` on T, with no storage
move and no new mint. Clearing `Some → None` does the reverse. Both are
`relabeled`, never `added`/`removed`. Human output must say
`🪢 relabeled …` (not `links to` → `links` as two events). The Task Card
CURRENT-row `⇧↵` relabel path (LG4) and capture rerun path (LX3) inherit
this. Docs must state the owner never flips: the direction revealed is
always the original authoring direction.

**Migration: none on disk.** Under A there is deliberately no backfill.
Existing unlabeled edges (LK1 `[[#^a]]`, LK2's bare second entry) keep
their bytes; only chips regroup. Reconcile on a pre-change vault must be
byte-identical on disk (extend LR11 with an explicit undirected-display
no-op case). This is the headline reliability property to test: check out
an old vault, run new `bob task reconcile`, `git diff` must be empty.

**`~~` guards.** `~~` targets must be editable (same refusal set as `*`:
daily notes, `done/`, `_templates`, `_generated`, `_conflicts`,
dot-directories, fenced code — `docs/capture.md#linking-tasks` "Targets").
That rule stays for labeled `~~`. Unlabeled `~~` never reaches it: it is
refused earlier with the teaching error from §2d, in `scan_relation_at` /
`plan_relation_writes` (`resolve_relation_target`,
`refuse_from_target_path`), in `capture-parse` (new need, not
`relation_target`), and in the Linked-from stage (empty label + `↵`
refused; must type a label or switch to Links stage). `~~` with a label
to an archived/previous-daily target keeps today's behavior (LINKS write
succeeds, mirror skipped with `mirror_skipped: archived_target |
previous_daily_target`, LX1/LX5).

**Read-only, malformed, id-less, self/non-task.** All unchanged and apply
equally to undirected: self refused, non-task refused with teaching
error, id-less target offers `＋ id` (nav `showBlockIdStage`, capture
`requires_block_id` / `capture-task-id` replacements), archived target
allowed with live-only chips (§10, LG6), malformed LINKS refuses authored
writes ("its LINKS line is malformed", LW10/LX9), malformed mirror skips
with warning (LX10), duplicate block-id sources never listed (LR23/BR5),
deleted-T stays with `unresolved_relation_link` + `⚠ ^id not found`
(LC4), deleted-S's mirrors cleaned next run. Inertness (§2, LR18/LX13)
holds: grouping changes never block, promote, consume, stamp, schedule,
count as Pomodoro Task Links, advance `]s`, or route inbox.

**Kill switch.** `relations.linked_from_lines: false` already removes
every mirror losslessly and mints nothing (§12). Under A it keeps doing
exactly that — for labeled and unlabeled alike. No new key (no
`undirected_*`, no `links_lines`). Invalid values still warn and behave
as `true` (LR17).

**Index/API.** `api.relationIndex` v1 (`version`, `generation`,
`ready()`, `outgoing`, `incoming`, `labelSuggestions`, `onChange`, §11)
must stay compatible for Mac Capture (thin-client decision). Add additive
helpers, never renames: `linked(path, blockId)` (deduped unordered union
of unlabeled out+in — the `links` row source) and optionally
`directedOut`/`directedIn` (labeled subsets). `labelSuggestions` unchanged
(case-insensitive dedupe, count order). Startup prefilter
(`🪢`/`**LINKS`/`**LINKED FROM`/`**BACKLINKS`), chunked
generation-guarded scan including `done/` read-only, per-file reparse on
`metadataCache.changed`, vault `delete`/`rename` handling, and unsaved
editor overlay (§11) all unchanged.

## 5. Intuitiveness: teaching model in one paragraph

"Links are symmetric unless you give them a reason not to be. Type
`~note:id` to link two tasks — both sides show it under `links`. Add
`|\"follow-up of\"` (or any label) to say *how* they connect, phrased from
the task whose LINKS line you wrote: `S — label → T`. Labeled links show
direction (`links to` here, `linked from` there, with the inverse wording
where Bob knows it). `~~note:id|\"label\"` writes the label from the other
task's side. `~~` without a label has no side to read from, so Bob asks
for `~` instead."

Every refusal, placeholder, and doc example should be checkable against
that paragraph. In particular: the Links stage (`l` / `Ctrl+Shift+L`)
accepts empty labels (creates `links`); the Linked-from stage (`⇧L`)
requires a label (empty `↵` teaches "describe it from S's side, or press
`l` to link from here instead"); the relation card's live sentence
(`S — label → T`, already in the Mac Capture card per prior research)
shows an unlabeled preview as `S — links — T` with no arrow.

## 6. Beauty: per-surface wording (the actual "just show `links`" table)

Keep storage words where they name the sigil/owner; change presentation
words where they face the user. Bold = change.

| Surface | Today | Recommended |
| --- | --- | --- |
| Task Card chips, unlabeled out+in | two rows: `links to → chips`, `linked from chips` (LC1) | **one row `🪢 links` with inline chips, no arrow, no pill, wrap between chips**; merge unlabeled out+in, BK21 sort, dedupe unordered pairs |
| Task Card chips, labeled | `‹label› → chip` / inverse or `(chip) · label → this` | unchanged (still `links to` / `linked from` sections) |
| Task Card row titles | `Links to` (`l`), `Linked from` (`⇧L`) | keep stage names (they name the owner), but **empty-label `⇧L` submit teaches**; optionally retitle to `Link…` / `Link here…` only if Obsidian strings allow without breaking `api.relations?.version` gating |
| Capture human output, unlabeled `~` add | `🪢 links to "T"   path ^id` | **`🪢 links "T"   path ^id`** / dry-run **`🪢 would link "T"`** |
| Capture human output, labeled `~`/`~~` | `🪢 links to … · label` / `🪢 "S" now links here · label` | unchanged (direction + `· label` stays) |
| Capture human output, relabel/unlabeled transitions | `🪢 relabeled` | unchanged; **never render a label add/clear as add+remove** |
| `capture-complete` groups / shell groups | `links to` / `linked from` | **keep** (they describe the sigil, not the chip); update group descriptions to note unlabeled results show under `links` |
| `capture-parse` / `capture` JSON | `direction: "to"\|"from"`, `relation_to`/`relation_from`, `relation_to_replacement` / `relation_from_replacement` | **unchanged** (Mac Capture thin client reads these; presentation regroups client-side) |
| Mixed row tooltips | `No longer links here · refreshes on the next reconcile`, `⚠ ^id not found` | keep; **add `links · also linked from with \`see\``** for the mixed-dup case (§4) |
| Collapse, dimming, toggles | `✓×N`, dimmed `✓`, `↗ note`, `toggle-dependency-chips` covers both rows | unchanged; **`links` row participates in the same toggle and collapse** (3+ closed → `✓×N`) |
| Docs prose | "directed, optionally labelled" everywhere | "a relation is symmetric (`links`) unless it carries a label, when it is directed (`links to` / `linked from`)" with the §5 paragraph verbatim |

Why no arrow for `links`: arrows promise direction. The current LC1
`links to → (○ T)` for an unlabeled edge is the precise over-chrome to
delete. Neutral row accent stays neutral; colour still carries status
only (§10). Line height still never changes (LC10).

## 7. Recommended solution (buildable spec)

**Glossary (memory + `docs/reference/glossary.md#task-relation`).**
Replace "A directed, optionally labelled, inert link …" with three
entries (keep aliases `relation`, `LINKS line`, `LINKED FROM line` on the
generic term only):

- *Task relation (relation)*: an inert, optionally labelled link between
  two tasks, authored once on one task's `🪢 **LINKS:**` line and mirrored
  on the other's generated `🪢 **LINKED FROM:**` line. Never blocks,
  counts as a Pomodoro Task Link, or changes status/schedule/priority/
  freshness. Add with `~` / `~~` or `l` / `⇧L`.
- *Undirected relation*: a relation with no label. Both ends show it
  under `links`. Stored once (owner = authoring task); labeling later
  reveals that owner as the direction.
- *Directed relation*: a relation with a label, phrased `S — ‹label› → T`
  from the source's side. Shown as `links to` here and `linked from`
  there (known labels use the inverse table; stored text never changes).

**Contract (`docs/task-relations.md`).** §1 vocabulary above; §3 grammar
unchanged (no new header — `LINKS TO` stays a tolerated non-canonical
input per LK4, never a new canonical form); §4 slots/order unchanged;
§5 add "owner is immutable across relabel"; §6 add "unlabeled edges in
`mirror(T)` render under `links`"; §8 add unlabeled-`~~` refusal to the
writer table; §10 replace LC1 with the `links` row and add the
dedupe/mixed-tooltip rules; §12 outputs unchanged except human verbs;
§15 add LU vectors (§8). State explicitly: disk names don't change.

**Capture grammar (`capture_language/relations.rs`,
`capture_language/editor_model.rs`, `capture_parse.rs`,
`reference/capture-syntax.md`, `capture.md#linking-tasks`).**
`~note:id` (no `|label`) creates undirected (stored `To`, shown `links`).
`~note:id|"label"` creates directed. `~~note:id|"label"` creates directed
from the named task. Bare `~~note:id` / `~~note:id|` / trailing-pipe forms
are a new teaching need (suggest `relation_label_required_for_from`,
message naming `~` + `|"label"`); execution refuses before staging
(`plan_relation_writes` → `resolve_relation_target`), vault byte-identical
(LX9 class). Quoting rules unchanged (`|"multi word"`, LP7). Strike,
escape, digit, `/`, mid-line, operator guards unchanged (LP3–LP5, LP10,
LP11, LP13–LP16).

**Writers (`capture/relations.rs`, `capture/relations_mirror.rs`,
`task_relations/plan.rs`, `task_status_hooks/relations.rs`).** No planner
or reconcile logic change except threading the new refusal. `Linked-from`
stage and `removeLink` semantics unchanged; dedupe of reciprocal
unlabeled pairs happens only in the live index/chip layer, never in
`plan_linked_from_line` or `reconcile_relation_lines`.

**Chips/index (bob-ledger-tools `api.relationIndex`, nav chips,
`task-status-cycler`, `block-id-prompt`).** Implement `linked()` as the
`links` row source (unlabeled out ∪ unlabeled in, unordered-dedupe, BK21
sort); keep `outgoing`/`incoming` for the directed rows filtered to
labeled edges. No new palette/badges; no `frees`/`waiting on` analogues.

**Docs/help/completion.** Update `guides/link-related-tasks.md` ("Choose
a direction" → "Link, then optionally describe"; fix the two unquoted
multi-word examples to `|"follow-up of"` / `|"related to"` while there),
`reference/vault-format.md` (add one unlabeled `links` example beside the
directed one), `reference/capture-syntax.md` (`#tilde-link` gains the
undirected sentence; `#tilde-tilde-link` gains the label-required box),
`capture.md` human-output example (`🪢 links …` for unlabeled), CLI
`--help` for `capture-parse` (drop the stale "refuses any item with
relations" line flagged in prior research), shell completion descriptions,
Mac Capture relation-card copy (`S — links — T` preview), and Obsidian
`plugins/task-relations.md` stage copy. No `mkdocs.yml` or config change;
implementer must still read `docs.md` + `cli_rules.md` memories before
touching those files (not done in this research turn).

## 8. Conformance vectors to add (LU — undirected display)

Extend `docs/task-relations.md` §15; mirror in
`src/native/task_relations/tests.rs`, `tests/cli/capture/relations.rs`,
`tests/cli/task_status_hooks/relations.rs`,
`src/native/capture_complete/tests/relations.rs`, and the JS twins'
copied tables:

- LU1: `A ~ B` unlabeled → S LINKS `[[B]]`, T mirror `[[A]]` on disk;
  both chips show one `links` row, no arrow, BK21 order.
- LU2: labeled `A —see→ B` → `links to` / `linked from` unchanged,
  pill + arrow/inverse path unchanged.
- LU3: bare `~~note:id` (and `~~note:id|` / `|"unterminated`) refused
  with the label-required teaching error; vault byte-identical; picker
  shows the same message (not `relation_target`).
- LU4: relabel `None → "see"` moves chips `links → links to/linked from`
  with owner preserved; `relabeled` in human + JSON; no new mint.
- LU5: clear `Some → None` moves chips back to `links`; same guarantees.
- LU6: reciprocal unlabeled `A→B + B→A` dedupes to one `links` chip per
  unordered pair; × removes both; disk keeps both until removed.
- LU7: mixed unlabeled + labeled between same pair shows in both rows
  with the disambiguating tooltip.
- LU8: old-vault reconcile no-op — pre-change vault with unlabeled edges
  reconciles byte-identical on disk; only chip grouping changes.
- LU9: kill-switch `false` removes mirrors for unlabeled too, mints
  nothing; re-enabling rebuilds them (LR16 class).
- LU10: human verbs — unlabeled add prints `🪢 links` /
  `🪢 would link`; labeled keeps `links to` / `now links here`; JSON
  `direction` unchanged.

## 9. Alternatives considered and rejected

- *Explicit undirected sigil* (`~=`, `~<>`, `~|`): explicit but adds a
  fifth relationship modifier to an already crowded sigil (`~` already
  fights drop-lists, strike, `~/path`, `~5m`), needs shell-quoting notes,
  picker/completion/shell/JSON updates, and teaches two ways to link.
  Label-absence already carries the signal for free.
- *New canonical `LINKS:` header for undirected*: renames storage,
  forces a vault-wide rewrite and reader-tolerance fork (LK4/LK17 grow),
  breaks every engine's closed-registry scanner, and gains nothing the
  chip row doesn't already give.
- *Forbid unlabeled entirely (always require a label)*: maximally
  explicit, but taxes the common "see also" case and contradicts the
  shipped LK1/LK2/LC1 vectors where unlabeled is first-class.
- *Infer direction from label semantics* (e.g. `follow-up of` implies
  arrow): brittle NLP in a deterministic contract; the inverse table is
  already display-only and case-insensitive — keep inference there, never
  in storage.
- *Silent `~~`→`~` alias*: see §2d — two spellings, wrong-owner time bomb.

## 10. Risks and open questions for the lead

1. Disk/display split: power users reading raw markdown will still see
   `LINKED FROM` for `links`. Accept with a one-line doc note, or is raw
   beauty worth a storage migration later? This research says accept.
2. Task Card stage retitles (`Link…` vs `Links to…`): string churn in
   Obsidian + `api.relations?.version` gating needs a plugin-side call.
   Keep owner-based names unless the plugin owner agrees.
3. Reciprocal-unlabeled ×-removes-both: confirm Bryan wants the deduped
   chip to be destructive to both edges (alternative: × removes one,
   chip stays until both gone — safer but sticky).
4. `labelSuggestions` for the Linked-from stage will now bias toward
   labels (since empty is refused there) — check suggestion ordering
   still helps rather than nags.

## Sources

- `docs/task-relations.md` §§1–15 (contract, vectors LK/LW/LR/LX/LP/LG/LC)
- `src/native/task_relations/{mod,parse,format,plan,label,tests}.rs`
- `src/native/capture_language/{relations,editor_model,tokens,completion}.rs`
- `src/native/capture/{relations,relations_mirror,output,plan,cli}.rs`
- `src/native/capture_complete/{model,candidates,render,shell,cli,engine}.rs`
  + `tests/relations.rs`
- `src/native/task_status_hooks/relations.rs`, `src/native/config/relations.rs`
- `docs/capture.md#linking-tasks`, `docs/reference/capture-syntax.md`,
  `docs/reference/vault-format.md`, `docs/reference/glossary.md#task-relation`,
  `docs/guides/link-related-tasks.md`
- Memory: `sase memory read glossary:relation -r "Need relation vocabulary
  for undirected/directed design research"` (Task Relation + linked
  Capture/Pomodoro/Task Link/freshness strands)
- Prior neutral research: `202610/task_relation_labels.md`,
  `202610/task_relation_links/task_relation_links.md` +
  `.diagrams.md` (peer-suffixed `__cdx/__cld/__grk/__gem` reports from any
  swarm deliberately not opened)
