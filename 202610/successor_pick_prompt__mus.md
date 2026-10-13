# From auto-link to explicit pick: prompting for successor links on close

> **Research query:** Instead of automatically adding successor task links when a
> close unblocks tasks, prompt Bryan to pick which unblocked tasks to pull in —
> via new panel(s) in Obsidian (and a separate solution for bob-mac-capture if
> needed); drop the at-most-5 cap; include all open tasks of a newly-unblocked
> project; and apply the same to project/parent-project pull-ins. Is this a good
> idea, what would I change, and what is the recommended implementation?
> Researcher: mus. Single-turn independent report; no peer reports consulted.

## Bottom line

**Yes, build it — with five adjustments.** The plan is sound at its core: the
current auto-link has a real gap (it can *recover* project members but never
*link* them, which is exactly the `^bar` surprise below), and the 5-successor
breaker (`MAX_SUCCESSORS_PER_GESTURE`, `src/native/task_complete/successors.rs:54`)
is a magic number that silently links *nothing* precisely when the most work
unblocked. Replacing silent automation with one explicit pick preserves momentum
while removing both defects.

My recommended shape, in one sentence:

> When a close leaves anything worth pulling into today, one panel lists the
> would-be auto-links pre-checked plus every pullable project member unchecked;
> Enter accepts, Esc links nothing, the close itself always stands.

The five adjustments (each justified in §3):

1. **Scope the project-member offer** to visible, unplanned, unscheduled,
   own-blockers-clear residents — not literally "all open tasks".
2. **Pre-check only today's auto-set** (fully-unblocked direct dependents +
   pull-in `^prj`); members start unchecked behind a select-all toggle.
3. **One panel with sections, not multiple panels** — in both Obsidian and
   the Mac app.
4. **Yes, the Mac app needs its own solution** (verified below): a checkbox
   section in the close card plus a new additive `bob capture` selection flag.
   No grammar parsing on the Mac side — it stays a thin client.
5. **CLI batch stays auto by default** with additive opt-out/pick flags; only
   interactive clients prompt. Hooks, reconcile, and non-TTY capture never
   block on a question.

## 1. How the current behavior actually works (verified)

Two engines implement one rule (`docs/task-dependencies.md` §12, "one
definition, two engines"):

- **Rust** (`src/native/task_complete/successors.rs`, `project_close.rs`,
  `project_pull_in.rs`) for `bob capture` closes.
- **JS** (`plugins/task-status-cycler/src/085-successor-plan.js`,
  `086-successor-ids.js`, `087-successor-place.js`, `088-project-blocking.js`,
  `089-successor-project.js`, `135-plugin-successors.js`,
  `136-plugin-successor-receipt.js`, `137-plugin-successor-project.js`) for
  Obsidian Ctrl+Enter-family closes.

The rule today, condensed:

- **Candidates** are open direct dependents of the closed set C whose
  `[dependsOn::]` names a closed task's `[id::]` (with an O(1) `[id::]` gate
  that skips the whole lookup for the ~96% of tasks without one).
- Each candidate is classified: fully-unblocked → **SUCCESSOR** (linked into
  the predecessor's slot, raised to Next); otherwise recovered-only with a
  `not_linked` reason (`already_planned`, `not_planned_today`, `hidden`,
  `project_task`, `project_member`, `breaker`, `disabled`) or left
  `still_blocked` (`waits_on`, `scheduled`, `project`).
- **BREAKER: more than 5 successors in one gesture → link none**
  (`successors.rs:795`; JS mirror at `087-successor-place.js:348-350`,
  notice copy "not linked · more than 5").
- **Project members are recover-only by design** (`project_close.rs:6`:
  "recover-only, never successor-linked, outside the successor breaker").
  When a `^prj` recovers, residents lose `#prj_is_blocked` and recover with
  `Recover("project_member")` — they never get links.
- **Project pull-in** (§12.10) links the `^prj` itself only when the close
  *empties* the project: trigger (a) closed the last task, (b) the `^prj`
  was itself the dependent, or (c) a sub-project's `^prj` closed and the
  parent emptied. Pull-ins skip the breaker.
- Reporting already carries everything a picker needs: `unblocked[]` rows
  with `note_path`, `block_id`, `text`, status transition,
  `unblocked_by[]`, `link` placement (or `not_linked` + `trigger` +
  `hide_removed`), and `still_blocked[]` rows (`src/native/capture/output.rs`
  ~L200, L567–628). Dry-run emits the same rows as "would link".
- Master off-switch `plan.link_unblocked` (default true,
  `src/native/config/plan.rs:15,30`) disables linking/minting only;
  recovery still runs. Undo is Alt+N per link plus a same-day in-memory
  receipt that takes back links on predecessor reopen (§12.9).
- Test coverage is deep: `successor_tests.rs` (1390 lines),
  `project_pull_in_tests.rs` (1537 lines), PP conformance vectors (§12.11),
  Mac fixtures including `task-complete-breaker.json`.

## 2. Diagnosis: why closing `^bar` linked nothing

Reproduced from the live vault (read-only):

- `~/bob/sase.md:1236`: `- [x] #task bar boom bam … [id:: sase__bar] … ^bar`
  (now closed).
- `~/bob/sase_foo.md` is a project note whose `^prj`
  (`foo bar baz`, line 10) has `[dependsOn:: sase__bar]` and `#hide`. Its two
  resident tasks ("Some subtask", "Some other subtask") carry **no**
  `[dependsOn::]` of their own.

Closing `^bar` therefore did exactly what the spec says and nothing the user
wanted:

1. The `^prj` was this close's only dependent candidate. Its last blocker was
   removed, but the project was **not empty** (two open residents), so no
   pull-in — step 4: recover-only, `not_linked: project_task`.
2. PROJECT RECOVERY then recovered the two residents (`project_member`):
   `#prj_is_blocked` stripped, rank derived — **never linked, by design**.
3. The residents were never direct dependents of `^bar` (no dep edge), so
   they were never even link candidates.

Nothing is broken; the design just has no path from "project unblocked" to
"residents on today". The proposed panel is precisely the missing path — and
this repro dictates its most important scoping rule: the residents that
mattered here were **not dependents of the closed task at all**. A panel fed
only by "unblocked dependents" would still have shown an empty list for this
exact gesture. The member section must be sourced from *project recovery*,
not from the dependent-candidate list.

## 3. Critique and requirement adjustments

**Is prompting a good idea? Yes** — for three reasons. First, a link is a
*sticky commitment* (raises to Next; only Alt+N releases), so the current
silent auto-link spends lane capital on Bryan's behalf, and the breaker
spends *nothing* exactly when the payoff is biggest — both failure modes
vanish when a human checks boxes. Second, the member gap above is unfixable
inside auto-link without reintroducing silent mass-linking (a 30-task project
unblocking would flood today); explicit selection is the only honest way to
offer residents. Third, the data is already computed: the dry plan exists in
both engines before anything is written, so a prompt costs no new vault
reads and no new discovery — it is a filter on verdicts, not a new lookup.

**Would I take a different approach?** I considered three alternatives and
rejected each:

- *Keep auto-link, just add members to it.* Rejected: unbounded silent
  Next-lane writes on project unblock; the exact surprise the sticky-lane
  decision (`task-lanes-are-sticky`) warns against.
- *Keep auto-link, just raise/remove the cap.* Rejected: removes the only
  guardrail without adding consent; blind-Enter on a big unblock is worse
  than today's breaker.
- *Post-close notice with one-click "link all" instead of a pre-commit
  panel.* Rejected: links would already be written (or not), so the notice
  is either redundant or a second gesture; pre-commit selection keeps one
  write path, one receipt, one undo story. The existing Unblocked card
  (`bob-navigation-hotkeys/src/285-unblocked-notice.js`, pure render, no
  buttons) stays as the confirmation surface, not the decision surface.

Adjustments I am making to the request as stated (called out explicitly):

1. **"All open tasks of the project" → qualifying residents only.** The
   panel must never offer: still-blocked residents (linking Blocked tasks
   violates §12/§13.5 consumption and Pomodoro-root promotion would drag
   their other prerequisites to Next — a silent second automation);
   `#hide` carriers (fighting `bob projects sync`'s hide predicate, which
   would re-hide within 15 minutes while the link stayed); already-planned
   tasks (duplicates); scheduled-future tasks (future work on today); and
   anchorless tasks (`not_planned_today` — no slot exists to offer).
   Excluded rows appear as one muted context line with counts, not as
   checkboxes. The `^bar` repro still works: both subtasks were recovered,
   visible, unplanned, unscheduled.
2. **"One or more new panels" → one panel with sections.** Multiple popups
   per close (directs, then members, then pull-ins) would train Esc-mashing.
   One modal: §A "Unblocked" (pre-checked), §B "Project members" (unchecked
   + select-all + filter), pull-in `^prj` rows inside §A (they are today's
   auto-set). The trigger-(c) parent pull-in lands in §A the same way —
   this covers the "project/parent-project pull-ins" bullet with no special
   casing: pull-ins go through the panel rather than auto-linking.
3. **Defaults preserve today's behavior on Enter.** Pre-checked = exactly
   what auto-link would have linked (SUCCESSOR verdicts + pull-ins).
   Members unchecked: they are the new, surprising surface with sticky cost,
   and the breaker is gone, so blind acceptance must stay bounded. A
   "select all" toggle plus the search filter (copy the existing
   `DemotionSectionPickerModal` pattern at
   `task-status-cycler/src/100-editor-and-modal.js:379`) keeps the repro
   case to Tab–Space–Space–Enter.
4. **The cap removal is safe only with (2)+(3).** Deleting the breaker is
   then a pure win: explicit picks need no cardinality guard. But note the
   consequence for *auto* contexts (below): breaker deletion means auto mode
   links unboundedly. Accept and document; the kill switch remains.
5. **"Via any supported method" → all close gestures prompt, but only when
   the offer set is non-empty.** Zero-candidate closes (the vast majority)
   behave byte-identically to today — this bounds prompt fatigue precisely.
   Included: Ctrl+Enter on link/task-line/Pomodoro-line, nav walk
   Ctrl+Enter, all capture closes (`=x` variants, `=!`, `!note:id`), and —
   reluctantly — Alt+]/[ cycling into Done, for uniformity. The Alt+]/[
   case is the one place I would accept a carve-out (mid-cycle modal is
   jarring); if it annoys in practice, exempt lane-cycling and leave its
   auto behavior, rather than adding per-gesture config. Cancel, reopen,
   `=*` parks, and reconcile never prompt (they never link).

## 4. Recommended solution

### 4.1 Shared semantics (both engines, implemented once per engine)

- **Offer set.** `(SUCCESSOR verdicts ∪ pull-in ^prj rows)` ∪
  `qualifying residents of every project this gesture unblocked`
  (visible, unplanned, unscheduled, no own remaining blockers — sourced
  from PROJECT RECOVERY, §2). Everything else the planner already
  classifies stays off the ballot and becomes one muted context line
  ("+2 still blocked · 1 hidden · 1 already planned").
- **Selection parameter.** The planner takes a pick set keyed by
  `(note_path, block_id)`; picked rows link exactly as today (same
  anchors §12.3, same ORDER, same Next-raising, same minting);
  unpicked rows recover with a new `not_linked` reason (propose
  `deselected`, added to the nav reason map and Mac captions). Recovery —
  including `[unblocked::]` WRITE semantics — is unchanged: skipping a
  successor loses nothing but the link, and morning review still surfaces
  it as a tickler.
- **Delete the breaker** in both engines, its notice copy, its PP-adjacent
  tests, and the Mac `task-complete-breaker.json` fixture path. Unpicked
  rows are consent, not breakage.
- **Two-engine parity.** JS and Rust implement identical offer/default/
  selection rules with shared conformance vectors in the style of the PP
  table (§12.11): selection matrix (pick-all / pick-none / pick-subset /
  pick-stale-key), member sourcing (§2 repro as a vector), breaker-gone
  unbounded auto. The engines have drifted before (canonical-id match);
  do not add a third behavior by accident.
- **Config.** Add `plan.successor_prompt` (default true) alongside
  `link_unblocked`: false in either client disables the panel (false
  `link_unblocked` = no linking at all, as today). No per-gesture, no
  per-task, no remembered picks — stored preferences would be inference
  automation wearing a trench coat.

### 4.2 Obsidian: one modal, plan → ask → apply

- New `SuccessorPickerModal` beside `DemotionSectionPickerModal`, reusing
  its search + row + keyboard idioms. Sections §A/§B per §3.2; each row
  shows transition (`[?] → [*]`), text, locator, destination capsule
  (`→ FIX`), and minted-ID caption where applicable. Buttons:
  "Link N selected" (Enter) / "Link none" (Esc). **Esc links nothing but
  the close stands** — no rollback machinery; document it on the panel.
- Hook point is the existing plan/apply split: `buildSuccessorPool` →
  prompt → `applySuccessorNoteEdits` / `applySuccessorDailyInsertions`
  (`135-plugin-successors.js:193,354,494`). The close flow is already
  async (`finalizeClosedTasks`, `160-plugin-completion.js`), so awaiting a
  modal needs no restructuring.
- **Walk interplay** (`answering-advances-the-walk`): the walk advances
  once, after the panel commits (including link-none) — never before, so
  a dismissed panel cannot strand or double-advance the walk. Gesture
  lock covers double-Enter.
- **Undo unchanged.** Picked links join the existing same-day receipt
  (reopen takes back untouched links; pull-in `^prj` line restore already
  handles status + `#hide`). Deselected recoveries need no undo.
- **Batch closes** (multi-item drafts, Pomodoro closes): plan the whole
  batch dry, show ONE combined panel grouped by predecessor, apply once.
  Pomodoro-close successors keep closing-target placement (§12.3).

### 4.3 Mac app: yes, a custom solution is needed (verified)

Three facts force it: (1) the panel previews via `bob … --dry-run`
  (`BobProcessClient.swift:189-190`; preview at
  `CapturePanelModel.swift:1478`, submit at `:1439`) and renders successor
  rows read-only through `CaptureSuccessorPresentation` — there is **no
  multi-select-submit control** anywhere; the existing
  `CapturePickerPresentation` pickers are single-select draft-fill, a
  different interaction with nowhere to submit a set. (2) The prompt must
  precede submit while the panel is alive; the post-submit macOS
  notification (`NotificationService.swift`) can only confirm, never ask.
  (3) bob auto-links server-side, so any selection needs a protocol input
  both clients share.

The thin-client decision (`mac-capture-is-a-thin-client`) survives intact:

- bob computes candidates (dry-run rows already carry them); the Mac only
  renders checkboxes and returns picks. No grammar parsing on the Mac.
- One new card section on close previews with ≥1 offerable row: checkboxes
  mirroring the §A-pre-checked / §B-unchecked defaults, bound to the
  dry-run `unblocked[]` keys.
- One additive capture-protocol flag (CLI rules: never a subcommand under
  `bob capture`; long option + short alias; protocol grows additively):
  e.g. `bob capture --successors <keys>` / `-S`, plus `--no-successors`
  for link-none, where keys are the dry-run row identities. Default
  (no flag) = today's auto behavior, so older Mac binaries and scripts
  keep working byte-identically.
- Staleness rule: bob re-plans at submit and matches picks by
  `(note_path, block_id)` → fallback `(note_path, preview line)` →
  unmatched picks ignored with a warning line. The window is seconds in
  the same panel; do not build plan tokens.

### 4.4 CLI batch: auto by default, explicit when asked

`bob capture` is piped into scripts and hooks — it must never block on a
question. Default stays auto (minus breaker, per §3.4); the new flags give
explicit control (`--no-successors`, `--successors …`). No TTY interactive
picker in v1: Obsidian + Mac cover interactive use, and a third prompt
implementation is where parity goes to die. Document the fallback chain:
prompt where a human is present, auto where none is, off where configured.

## 5. Risks, edge cases, rollout

- **Prompt fatigue** is the top risk. Contained by: prompt iff offer set
  non-empty (most closes unaffected); Enter = today's behavior; Esc =
  link-none in one keystroke. If fatigue appears anyway, the dial is the
  §B default (unchecked → hidden-behind-toggle), not the panel's
  existence.
- **Blind-Enter mass linking** (breaker gone). Contained by members
  defaulting unchecked; the auto-set is exactly what today links anyway.
- **Hidden `^prj` of a non-emptied project** (the `^bar` case: `^prj` still
  `#hide`). Do NOT offer it: un-hiding-to-link fights sync. It stays a
  context line. Only pull-in (empty-project) `^prj` rows un-hide and link,
  as today.
- **`[unblocked::]` interplay.** Members landing Next via picks skip the
  stamp (UB4, consistent with successors); deselected members landing
  Ready get it and resurface as ticklers — the safety net that makes
  "link none" cheap.
- **Scheduled-future and still-blocked rows** are never offered, even if
  the user asks "why isn't X listed" — the muted context line answers it.
- **Performance.** No new reads on any path: the prompt filters already-
  planned verdicts; the `[id::]` gate is untouched; Mac adds zero
  subprocesses (one flag on the existing submit). The known capture
  overhead (~50× over the thin-client premise, prior research) is
  orthogonal — do not bundle that fix here.
- **Rollout order.** (1) Engine selection parameter + `deselected` reason
  + breaker deletion + conformance vectors, Rust and JS in lockstep with
  §12 rewritten. (2) Obsidian modal + walk/receipt wiring. (3) CLI flags.
  (4) Mac section + submit. Each phase ships with the previous default
  (auto) intact so no phase needs a flag day; flip `successor_prompt`
  default last, per client.

## 6. Recommended solution (condensed)

Build the explicit-pick panel with adjustments §3.1–§3.5: one sectioned
panel per close gesture with the auto-set pre-checked and qualifying
project members unchecked; Esc links nothing and the close stands;
breaker deleted; pull-in `^prj`s (including trigger-(c) parents) go
through the same panel; Mac gets a checkbox card section plus an additive
`--successors`/`--no-successors` capture flag; CLI batch stays auto;
prompt only when the offer set is non-empty; anchors, recovery, undo, and
the kill switch otherwise unchanged. The `^bar` repro then offers exactly
the two `sase_foo.md` subtasks — the behavior Bryan expected, now as an
explicit choice instead of silent automation.
