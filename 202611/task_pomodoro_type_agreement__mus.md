# Task–Pomodoro type agreement: enforcement research

Researcher: mus. Vault/codebase read 2026-11-05 against
`bob-cli_32` HEAD (`01cb7b5c`). This report answers: should
`bob task reconcile` become the fallback writer that keeps every live
Task Link's task type inside its Pomodoro's type set, should the
keymaps that can break the invariant be fixed first, and how should
custom Pomodoro names be treated.

## 1. The invariant, stated precisely

The codebase already defines the proposed constraint as **agreement
(D5)** in `src/native/pomodoro_themes/routing.rs`:

- `type_components(name, sources)` (`routing.rs:35`) classifies each
  `+`-separated component of a Pomodoro `— NAME` tail as a *type
  component* or a *label*. With a configured `types:` vocabulary, only
  members are type components; without one, every component except
  inventory labels is (`routing.rs:55-66`).
- `agrees(task_key, entry_name, sources)` (`routing.rs:73`) returns
  true when the task has no effective type, the entry is a
  **container** (no type components), or the task key equals a
  component key of the entry.
- A task's **effective type** is the PT13 cascade in
  `src/native/pomodoro_themes/suggest.rs` (`suggest_for_task`): field
  `[type:: X]` / `(type::)` first, then reading-task rule
  (`plan.reading_type`, default `READ`), then the residence-chain note
  default (`task_type:` / legacy `theme:`, `off` stops the walk), then
  `plan.default_type`, else none. Field parse/repair lives in
  `src/native/task_theme.rs` (`parse_task_theme`, `set_task_theme`,
  `clear_task_theme`).
- The read-only tripwire already exists:
  `with_type_mismatch_lints` in `src/native/plan_budget/mod.rs:337`
  emits one `type_mismatch` lint per disagreeing live link
  (`LINT_TYPE_MISMATCH`, `mod.rs:43`), and
  `docs/task-types.md:861-870` plus `docs/plan.md:113` specify a
  ledger mark in Obsidian alongside the lint. Drift from hand edits,
  frontmatter/config edits, and sync merges is today **flagged and
  never silently repaired**.

So the proposal is not a new invariant; it is a decision about
**who repairs drift, in which direction, and how loudly**.

## 2. What already preserves agreement (do not re-fix)

A large writer matrix already exists. Any plan should treat these as
done and regression-test them, not redesign them:

| Gesture | Preserving mechanism | Where |
| --- | --- | --- |
| Bare capture placement | D7 `place`: running-exact → first-open-exact → first-containing → create `— T`; typeless falls back to legacy implicit | `routing.rs:250-…` (`PlaceInput`/`PlaceOutcome`), `docs/task-types.md:694-727` |
| Landing in a named Pomodoro | R2 merge: task keeps type, destination gains `+ T`; MEET and explicit-retype paths take Set/Clear instead | `routing::land` (`routing.rs:120`), `src/native/capture/task_theme.rs:683` ("links merge by default, never retype") |
| `#<type>` marker on new/existing task | Field table (§1.7) sets X first, then lands/merges; existing-link retype reuses D8 relocation | `capture/task_theme.rs:175` (`apply_type_marker`), `:340` (`apply_type_marker_to_existing`), `:1114` (`merge_named_destination`), `:1176` (`relocate_for_retype`) |
| `bob task move` across notes | D8 `apply_to_day_contents` when inherited type changes and field is `None`; explicit-field tasks keep type so no relocation is needed | `src/native/task_move/command.rs:1090-1176`, `src/native/pomodoro_themes/relocation_apply.rs:50`, `docs/task-move.md:1-18` |
| Obsidian Ctrl+Shift+M | Enter merges missing types into destination, Alt+Enter retypes to destination type, Tab cycles composite choice; emptied merged source sheds (R7) | `docs/reference/plugins/bob-navigation-hotkeys.md:202-206` |
| `^^` picker (block-id-prompt) | Enter merges missing type without touching field; Alt+Enter retypes (`[type:: X]` write/clear); Tab cycles composite | `docs/reference/plugins/block-id-prompt.md:49-63` |
| Pomodoro rename / `bob capture-pomodoro-name` | D6 retype of linked tasks (`retype: true`), containers/meet/consistent untouched; task-card rename preview counts linked-type changes | `src/native/capture_pomodoro_name.rs:500-676`, `routing::land` with `retype: true` |
| Close (Ctrl+Enter / `x`) | R6 `narrow_closed` + `shed`: closed narrows to worked types, continuation sheds uncarried types; base/labels/MEET/single-type preserved | `src/native/capture_pomodoro_close/names.rs:51`, `docs/task-types.md:957-966` |
| Move-out shed / split / merge entries | R7 shed-on-move, R4 split-by-type, R5 survivor-union merge; MEET never renamed/merged/split | `docs/task-types.md:912-969`, nav-hotkeys `Ctrl+S`/`Ctrl+X` sections |
| Successor offers | Default placement via `place(T)`; explicit retarget applies retype rule; unpicked/stale writes nothing | `docs/reference/plugins/task-status-cycler.md:174-179` |
| Task Card Type stage | Writes `[type::]` then D8-relocates the live link (`running_retype = absorb`); backlog tasks gain no link; partial failure leaves `type_mismatch` visible | `docs/reference/plugins/task-card.md:100-119` |
| Schedule/dependency writes | Future schedule *removes* live links; Depends-On add removes dependent's live links; removal cannot create disagreement | nav-hotkeys `Ctrl+Shift+P` section |

Two apparent contradictions found while reading, worth pinning before
implementation: `docs/task-types.md:689-692` lists "typed `^^`,
move, … reconcile … remain never-writers", yet the `^^` picker doc
and `task_theme.rs` show Enter-merge writes to the *destination name*.
The consistent reading is "never-writers of *task fields*" (merge
writes the Pomodoro tail, not `[type::]`), but the sentence as written
will mislead an implementer. Likewise `docs/task-types.md:842-843`
says "named capture `#NAME` / `=name` forms still call `land` with
`retype: true` until the capture merge phase" — so named captures
today *retype the task* where the end-state design says *merge the
destination*. That is arguably breaker #1 (see §3.1).

## 3. Where disagreement actually comes from

### 3.1. Gestures that write disagreement today

1. **Named capture retype path.** `routing.rs:9`, `139-146`,
   `837-839` in `docs/task-types.md`: `#NAME`/`=name` pass
   `retype: true`, so linking a `FIX` task into `— BUILD` rewrites the
   task to `BUILD` instead of merging the entry to `BUILD + FIX`.
   This is the one capture keymap whose default contradicts the
   stated end state ("merge, don't retype, unless the gesture asked
   to retype"). Fixing it is the highest-value keymap change.
2. **Hand-inserted Task Links.** A hand-typed `[[note#^id]]` bullet
   under a Pomodoro bypasses `land` entirely. No plugin can
   intercept free text; this class is unfixable at the keymap layer
   and is the honest case for a fallback.
3. **Task Card gaps, if any.** The task-card doc claims D8 relocation
   on type edits, but `docs/task-types.md:843` still says "Task Card
   integration remains later work". If the plugin-side D8 step has
   shipped, verify it; if not, the Type stage / Use-default / Ctrl+D
   rows in the table at `docs/task-types.md:847-852` are the spec,
   not the behavior. Either way, treat Task Card as *verify-first*.
4. **Pomodoro entry hand-renames.** The rename picker retypes (D6),
   but editing the `— NAME` tail as plain text does not. Same for
   hand-merging two entry blocks or hand-splitting one.
5. **Close with drifted/untyped work.**
   `names.rs:210-225`: links whose type is not a component of the
   entry leave the name unchanged ("drift … leaves the name
   unchanged"). The close is agreement-neutral, so pre-existing drift
   survives closes indefinitely.

### 3.2. Non-gestures that change one side silently

These dominate in practice and no keymap fix can reach them:

- Editing `[type::]` / `(type::)` / legacy `[theme::]` as text.
- Editing area/project `task_type:` / `theme:` defaults, `parent:`
  chains, or `[root::]` overrides (changes inherited types vault-wide).
- Editing `plan.default_type`, `plan.reading_type`, or the `types:`
  vocabulary itself. A vocabulary change is the worst case: it flips
  components between *type* and *label* (and containers into typed
  entries or vice versa) with zero link/task edits, producing mass
  disagreement in one config keystroke.
- Sync merges (`_conflicts/`, concurrent appends) and template edits.
- `bob types rename`/`split` deliberately do not rewrite all sides:
  rename rewrites tails + defaults + fields together (good), but
  split "never rewrites defaults or fields" (`docs/task-types.md:746`)
  and reports `split_leaves_task_themes` leftovers — a known,
  counted disagreement source.

### 3.3. Structural unsatisfiability: one task, many entries

A task has exactly one effective type but may hold live links under
several open Pomodoros (duplicates aside, e.g. queued + planned, or
two entries created before dedup runs). No per-entry rename can
satisfy `agrees()` for two entries with disjoint type sets
simultaneously. Today reconcile already breaks this tie by ownership:
"the first open Pomodoro in file order keeps ownership and every
conflicting physical line beneath later open Pomodoros is removed"
(`task_status_hooks/mod.rs` long-about, `docs/task-status-hooks.md`
duplicate-removal section). A type-fixing reconcile must run **after**
that dedup and operate on the surviving lineup, or it will grow names
to satisfy links that dedup is about to delete. Order of passes is a
hard requirement, not an optimization.

## 4. Critique of the plan as stated

**The direction is right; the default is wrong.** Agreement-at-write
(§2 already does most of it, §3.1 needs finishing) plus a loud
read-only signal (lint + ledger mark, already shipped) is the correct
architecture. Making `bob task reconcile` a silent Pomodoro-renaming
writer by default has five concrete hazards:

1. **Name bloat and flap.** Reconcile runs unattended (nightly,
   pre-sync). Auto-appending `+ T` for every drifted link turns typos,
   transient inherited-type states (a half-edited frontmatter chain),
   and vocab experiments into ledger renames that other surfaces
   (Mac client, ledger-tools pills, stats, `capture-pomodoros`
   refs) render live. Removing types is worse: a shed that fires
   while a link is momentarily unlinked (schedule pull-forward,
   take-back windows, mid-batch states) deletes a component the next
   run re-adds. Add-only flaps less than add-and-shed, but still
   flaps.
2. **Wrong side of the fix.** The proposal always edits the Pomodoro
   line, never the task. When the task carries an explicit
   `[type:: FIX]` under `— BUILD`, the field is the deliberate
   statement and the entry may be the mistake (wrong picker row,
   hand-inserted link). The codebase's own landing philosophy agrees
   the task usually wins (R2 merges the entry), but D6 exists precisely
   because sometimes the entry wins (deliberate rename retypes the
   task). A fallback that can only grow entries cannot express "the
   link is in the wrong entry" — yet `Ctrl+Shift+M to move` (the
   lint's own advice, `plan_budget/mod.rs:388-389`) is exactly that
   fix. Reconcile-as-renamer will cement misplaced links by renaming
   the entry around them.
3. **Deliberate names are not edge cases.** `LATER` (container),
   `BOB + BUILD` (label + type), `MEET` (calendar-owned), single-type
   entries a user keeps single on purpose, and genuinely custom names
   (`SNACK` ad-hoc with its warning) each need different treatment.
   The "custom names are rare" premise understates this: containers
   and labels are load-bearing routing targets (LATER holds anything;
   `place` skips containers deliberately), and MEET must never be
   renamed. A renamer needs a per-class policy, not a blanket
   exception.
4. **Scope creep on a lane/dependency command.** Reconcile's contract
   (its `long_about`, `docs/task-status-hooks.md`) is statuses,
   dependencies, retirement, and structural cleanup — all idempotent
   and lane-safe. Type renaming touches the close/split/merge/selector
   semantics (base type, exact-match routing, R6 inputs) and the
   `capture-pomodoros` refs/tests. A bug here corrupts today's ledger
   names, not just statuses. Gating matters.
5. **Redundancy with the shipped signal.** The lint + mark + Task
   Card retype path already closes the loop for attended drift: user
   sees `BUILD task under FIX … Ctrl+Shift+M to move or Ctrl+Shift+P
   t to retype` and fixes the *right* side. An unattended renamer
   competes with that loop and can hide the very signal that lets the
   user choose move-vs-retype.

**Verdict: good idea as an opt-in repairer, bad idea as a silent
default.** The plan's shape (fallback + keymap fixes + custom-name
care) is correct; its aggressiveness is not.

## 5. Adjustments to the requirements

1. **Reconcile must be add-skeptical, not add-and-shed.** Default to
   *report-only*; add an explicit writer (`--fix-types`, JSON
   `fix_types` summary) that **adds missing components only**, never
   removes. Shedding is a separate, louder decision (it destroys a
   routing target other links may want) and should stay in the
   gestures that own shedding semantics (close R6, move-out R7,
   split R4, explicit rename).
2. **Fix the entry side only when the entry is already typed.**
   Never auto-grow containers (`LATER`), MEET, unnamed/`(unnamed)`,
   or single-label names into typed entries. Custom/ad-hoc names:
   warn (`theme_not_configured` family) and skip, exactly as
   `docs/task-types.md:859-860` prescribes ("tasks here keep their
   own types"). Single-type entries: appending a second type changes
   base/exact-match routing — allow only under `--fix-types` and
   report prominently.
3. **Fix the task side instead when the field is explicit and the
   link looks misplaced — or rather, don't fix at all.** Distinguish
   *task says X, entry lacks X* (entry-grow candidate) from *task says
   X, entry is a deliberate single type Y* (probably a misplaced
   link: lint, don't rename). Heuristic: grow only merged entries and
   multi-link entries; for single-type-entry disagreements, keep the
   lint. This preserves the user's ability to mean "this link is
   wrong".
4. **Close the named-capture retype gap first** (§3.1.1). Until
   `#NAME`/`=name` merge by default, reconcile will fight the
   capture path weekly.
5. **Order passes explicitly**: dedup/conflicting-link removal →
   canceled/consumed-link removal → type agreement → empty-entry
   cleanup, with a rescan between structural rewrites (the existing
   pattern in `docs/task-status-hooks.md:266-276`). Type-fixing
   before dedup renames entries around doomed links.
6. **Typeless, closed, and unresolvable links are out of scope.**
   Typeless tasks agree everywhere; closed Pomodoros are history
   (never rename); unresolvable/ambiguous links cannot yield a type
   (warn through existing channels, don't touch names).
7. **Multi-link tasks: relocate, don't duplicate-grow.** If one task's
   live links span entries, prefer D8 relocation of the stray link to
   `place(X)` over growing every entry to contain X. Growing N
   entries to satisfy one task is how `BUILD + FIX + READ + …`
   monster names are born.
8. **Vocabulary changes need a confirmation gate.** A `types:`
   edit that reclassifies in-use components should surface as a
   dedicated warning (reclassify report), not as hundreds of silent
   renames or lints. At minimum, reconcile must refuse to bulk-grow
   entries when the catalog fingerprint is newer than the last full
   sweep (reuse the PT3 cache-fingerprint idea).

## 6. Recommended solution

**Phase 0 — verify, don't build.** Confirm whether Task Card D8
relocation and `^^` Enter-merge are shipped behavior or spec text
(§2 table vs. `docs/task-types.md:689-692,843`). Reconcile the two
contradictory sentences in `docs/task-types.md` first; an
implementer will otherwise build against the wrong contract.

**Phase 1 — keymap fixes (before any reconcile writer).**

- (a) Migrate named capture `#NAME`/`=name` from `retype: true` to
  merge-by-default, reserving retype for an explicit marker (the
  `Alt+Enter`/selector/tab-pick path). This is the single largest
  disagreement source under the user's control.
- (b) Audit successor explicit-retarget and ref-today `-p`/`-P`
  (D6) paths for count-preview parity with the rename picker.
- (c) Keep hand-edit and vocab-edit drift as lint+mark (already
  shipped); do not attempt interception.

**Phase 2 — reconcile as opt-in repairer.**

- Add `bob task reconcile --fix-types` (default off; dry-run
  previews it like every other reconcile mutation). Output additive
  JSON (`type_fixes: [{block_id, route, from, to, kind}]`), human
  lines mirroring the `type_mismatch` lint text plus the applied
  rename.
- Algorithm per surviving live link (post-dedup), typeless/closed/
  container/MEET/unresolvable skipped:
  1. Compute effective type via `suggest_for_task` (one shared
     `HomeResolver`, as `with_type_mismatch_lints` does).
  2. If `agrees()`, do nothing.
  3. Else if the entry already has ≥1 type component and the task
     type is known/configured (or history-known when unconfigured),
     append `+ T` in catalog spelling once (dedup by key, labels
     untouched, order preserved) — i.e. reuse the R2-merge spelling
     rule, not a fresh rename scheme.
  4. Else (container, custom, MEET, single-type deliberate,
     unknown): leave the bytes alone, keep the lint.
  5. Never shed/remove components in this pass; never create entries;
     never write `[type::]` fields; never stamp freshness, change
     lanes, consume dependency guards, or advance the walk (the
     existing "type-only edits are inert" rule,
     `docs/task-types.md:869-870`).
- Idempotence proof obligation: second run over the fixed vault
  reports zero `type_fixes` (same bar as dependency fields,
  `docs/task-status-hooks.md:393,453`). Add vector tests in the
  `routing.rs`/`relocation_apply.rs` style plus golden ledger tests:
  merged-entry grow, container skip, MEET skip, typeless skip,
  closed-entry skip, multi-link relocate-vs-grow, vocab-flip
  no-bulk-rename, dedup-before-grow ordering.

**Phase 3 — promote to default only with evidence.** Enable
`--fix-types` by default only after N weeks of opt-in logs show
(add-only) fixes converging without flap (fix count → 0 and stays
0) and no monster-name complaints. Keep a `--no-fix-types` escape
and keep shedding forever manual. Custom Pomodoro names need no
further exception under this design: they fall in the
warn-and-skip class alongside containers, which is a smaller,
safer carve-out than "don't break anything custom" and matches the
already-documented ad-hoc-name rule.

## 7. Open questions for Bryan

1. For an explicit-field task (`[type:: FIX]`) linked under a
   deliberate single-type entry (`— BUILD`): is that ever correct in
   your vault, or is it always a misplaced link? (Recommendation
   assumes misplaced → lint, not rename.)
2. Should `--fix-types` grow single-type entries into merged ones, or
   only grow already-merged entries? (Recommendation: merged only at
   first; single-type growth is the riskiest rename.)
3. Is the named-capture `#NAME`/`=name` retype→merge migration
   acceptable, or do you rely on retype-by-naming anywhere?
