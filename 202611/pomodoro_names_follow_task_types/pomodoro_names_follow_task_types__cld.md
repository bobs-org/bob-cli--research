# Keeping task types and Pomodoro names in agreement

> Researcher **cld** · 2026-11-05 · request: make every task's effective type match a
> type of the Pomodoro whose Task Link points at it; `bob task reconcile` repairs drift
> by adding or removing types on Pomodoro lines; fix the keymaps that cause drift;
> custom Pomodoro names are probably the exception.

## TL;DR

- **Bob already defines this invariant.** It calls it *agreement* (D5 in
  `docs/task-types.md`, "Routing: agreement, landing, placement, relocation"). Since
  2026-11-02, landing a link **merges** the task's type into the destination name
  instead of retyping the task. Today, though, drift is *flagged and never silently
  repaired*. That is a deliberate earlier policy, and your request reverses it. The
  reversal needs a new decision record.
- **The real gap is not the half you described.** Vault replay (§2) shows the
  "task type is missing from the Pomodoro name" half (I1) is nearly solved since
  Nov 2: two one-snapshot episodes in three days, at least one of them a 20-second gap
  between a two-file gesture's writes. The half that still leaks is **unsupported
  types**: names keep types that no remaining link has (I2). In Rust, `merged::shed` has
  exactly one caller, Pomodoro close. In the plugins, none of the link-removal paths
  shed. Your merged-in task `^task-reconcile-removes-types` is exactly this problem.
- **The direction is right: the Pomodoro follows the task.** Three reasons:
  - The task's type is durable, deliberately chosen data.
  - An open Pomodoro name is a transient plan label.
  - Rewriting only today's open entries is cheap, local, and reversible. Retyping tasks
    instead would spread sticky `[type::]` exceptions across the vault.
- **My main adjustments** are in §5:
  - Repair **open** entries only.
  - Removal counts *worked* (struck) links as support, and never fires when the entry
    has no typed link or has an unresolvable link.
  - MEET entries are report-only.
  - Your custom-name exception **already exists** as the *container* rule; it needs no
    new mechanism.
  - Typing a name for a **brand-new** entry should retype the task, not merge.
  - The **close** should add worked types, not just narrow. Stats freezes at close, so
    that matters more than anything reconcile does mid-session.
- **Recommended solution** (§8): write one pure rule, `agree_entry(name, links) → name`,
  with Rust and JS mirrors and shared vectors. Apply it in four places:
  1. A new reconcile pass over all open entries: the safety net.
  2. The close: "settle" replaces "narrow".
  3. One ledger-write choke point per writer family (capture's staged planner; the
     plugins' prune, move, and relocation helpers), applied to the entries each gesture
     touched. This replaces patching about 25 gestures one by one.
  4. Fixes for a handful of specific bugs, including a **regression since 2026-11-02**:
     renaming an entry in Obsidian no longer retypes its tasks.

---

## 1. What exists today

| Piece | Where | What it does |
| --- | --- | --- |
| Agreement predicate | `src/native/pomodoro_themes/routing.rs:70` `agrees`; JS mirror `bob-ledger-tools/src/279-plugin-task-type-routing.js` `typeAgrees` | True if the entry is a container, the task has no type, or the task's key equals any component key, labels included. |
| Type vs. label | `routing.rs:35` `type_components` | You have `types:` configured (BUILD, CHORE, FIX, MEET, PLAN, READ, WRITE) and `plan.default_type: CHORE`. So every open task has a type, and any non-vocabulary component is a **label**. A name with no type components is a **container**. |
| Landing (R2) | `routing.rs:120` `land` | A link landing in a non-container, non-MEET entry of another type appends ` + T` to the entry and writes no task field. Alt+Enter, and MEET destinations, take the retype path instead. |
| Relocation (D8) | `routing.rs:418` `relocate`; `relocation_apply.rs` | When a task's type changes, its live link moves, or its entry is renamed. There is **no MEET guard** and **no shed of the source entry**. |
| Close naming (R6) | `capture_pomodoro_close/names.rs:93`; JS `170-plugin-pomodoro.js:766-767` | The closed entry is narrowed to its worked types. The continuation sheds types that had links before but no carried link after. Single-type entries never rename. |
| Shed on move (R7) | `merged.rs` `shed` | Documented, but the **only** Rust caller is close (`names.rs:93`). In JS, only Ctrl+Shift+M bullet moves call it (`651:280`), and only when every source link resolves. |
| Drift lint | `src/native/plan_budget/mod.rs:337` `with_type_mismatch_lints` | One `type_mismatch` per disagreeing live link, in `bob plan` only. Covers I1 only. Has no tests. |
| Drift mark | `bob-ledger-tools/src/137-ledger-type-marks.js`, runtime `268-plugin-ledger-type-marks.js:272` | Puts `#TYPE` before a disagreeing link. **It skips inherited types**, so it only sees tasks with an explicit `[type::]`. That is about 20 of 649 open `#task` lines in the vault today (~3%). Nothing shows I2. |
| Policy | `docs/task-types.md` (Agreement bullet); glossary `task-type` | "Drift that no gesture caused … is flagged and never silently repaired." The earlier research rejected "silent auto-repair of drift" because "after a hand edit, Bob can't know which side was meant" (`research:202610/task_types_from_pomodoro_themes/…__final.md`, R12). The same doc lists reconcile as a *never-writer of type fields*. |
| Reconcile | `src/native/task_status_hooks/sync.rs` `sync_task_statuses` | Dedupes links, removes canceled ones, strikes and relocates completed ones, deletes empty entries, settles off-clock events, derives statuses, and consumes blocked links. Never looks at types. Runs every 15 minutes on the MacBook. |

Two invariants are tangled together in the request. Naming them makes the design easier
to reason about:

- **I1 (coverage):** every live link's task type is a type component of its open entry.
  Containers and MEET are exempt.
- **I2 (support):** every type component of an open entry is the type of at least one
  link in it. The doc already states this intent ("after any merge, split, move, or
  close, a name says which kinds of work its Task Links hold"), but nothing enforces it.

## 2. How often drift actually happens

I replayed every vault git snapshot of each daily note. For each open entry I computed
I1 and I2. Types came from `bob types suggest` against today's vault, and daily-note
tasks were parsed in-snapshot (the script was a throwaway in `/tmp`).

| Window | Snapshots | With I1 drift | With I2 drift | I1 episodes | I2 episodes |
| --- | --- | --- | --- | --- | --- |
| Oct 25 – Nov 2 (types rolling out; merge landing shipped Nov 2) | 610 | 203 (33%) | 160 (26%) | 19 | 15 |
| Nov 3 – Nov 5 (merge landing live) | 187 | 3 (1.6%) | 4 (2.1%) | 2 | 2 |

What the post-Nov-2 episodes were:

- **Nov 5, 06:04, I1, not real drift.** A Task Card retype wrote `[type:: FIX]` to
  `sase.md`. Vault sync committed that file before relocation renamed the planned
  `— BUILD` continuation to `— FIX` 20 seconds later. This is the two-file write
  window, not a gap in the rule.
- **Nov 4, 06:24 → 12:03, I2, real drift.** A new entry `— FIX + BUILD` was created for
  `sase#^harden-github-outages`, which had no field and so inherited BUILD from
  `sase → dev`. A typed Pomodoro name of FIX merged with the inherited BUILD. At 06:30
  you set `[type:: FIX]`, and BUILD then sat on the entry unsupported for about
  5.5 hours. This is the "typed new-entry name" flaw in A5 below.
- The `^task-reconcile-removes-types` note ("removes any task types from the Pomodoro
  line that were not actually used") shows you hit the I2 case directly.

Caveats:

- Types for non-daily tasks are today's types, so retypes made after a snapshot can
  look like drift. The Nov 5 case is one example.
- Pre-Nov-2 numbers mostly predate the merge landing.
- Snapshots are vault-sync commits, minutes apart, so short windows are under-sampled.

**Takeaway:** the gestures already keep I1 reasonably well. The structural leak is I2,
plus a few I1 holes that are rare but real (§3). That changes the weighting: the
reconcile pass's most frequent job will be *removal*, so removal semantics need the
most care.

## 3. Where drift comes from (gesture audit)

This is condensed from a read-only audit of bob-cli, bob-navigation-hotkeys,
block-id-prompt, task-status-cycler, and bob-ledger-tools. Items marked ✔ I verified
myself in code; the rest come from the audit with file references.

### I2 leaks (unsupported type left behind): structural and frequent

| Writer | Path | Notes |
| --- | --- | --- |
| Every nav "prune" path: Alt+N release, future schedule, Alt+P / Ctrl+Enter roll, cancel and decay Drop, blocked consume (Ctrl+Shift+B), relation cancel label, project subtree cascade | `bob-navigation-hotkeys/src/160-pomodoro-reorder.js:568` `planDeferredPomodoroLinkCleanup` | Deletes emptied entries but never sheds. One fix covers the whole family. |
| block-id-prompt unlink, delete selected link, duplicate prune on insert | `060-link-cleanup-and-deletion.js:604`, `075-pomodoro-link-targets.js:712` | No shed. |
| Successor take-back (reopen the same day) | `task-status-cycler/src/136-plugin-successor-receipt.js:287` | Never reverts a merged-in type. |
| Task Card `t`, Use default, Ctrl+D; capture `#<type>` on an existing task; task move and inbox route | `316-task-card-type-relocation.js:179`; `relocation_apply.rs:54`; `655:25-167` | Relocation never sheds the **source** entry. `relocate` also returns `Unchanged` whenever the new type is already in the name, so `BUILD + FIX` with links {A:BUILD, B:FIX}, after retyping B to BUILD, keeps FIX with no link. |
| Capture `@r+id!` unlink, `=~K` drop, Ensure Next move, `bob task cancel`, `&`/`*` consumption, `bob task complete` | `capture_task_toggle/links.rs:441`, `capture_pomodoro_start.rs:615`, `ensure_next.rs:199`, `task_cancel/prune.rs:59`, … | No shed. ✔ `merged::shed` has a single production caller (`names.rs:93`). |
| Reconcile's own removals (dedupe, canceled links, blocked consumption) | `task_status_hooks/structure.rs`, `sync.rs` | No shed. |
| Typed name for a **new** entry (block-id-prompt link picker, capture glued `#NAME` / `=name`) | ✔ `block-id-prompt/src/078-pomodoro-theme-write.js:377` `pomodoroTargetWithKeepTypeMerge` | Creates `NAME + T` holding only a T link, so NAME is unsupported from the start. This is the Nov 4 case. |
| Ctrl+Shift+M `=` (same name) and `=NAME` peel | `651:303-311`, `160:303-325` | The new entry copies the whole source name; the peel skips shed. |
| Close continuation | `merged.rs` `shed` | Keeps "components that never had a link", and keeps the base when every type drops. That conflicts with I2 by design. |

### I1 holes (link under a name that lacks its type): rare but real

| Writer | Path | Notes |
| --- | --- | --- |
| **Regression:** renaming an entry in Obsidian (Ctrl+Shift+M on the entry line, typed name or Recent row) | ✔ `bob-navigation-hotkeys/src/650-plugin-move-commit.js:140` passes `{}` to `pomodoroBulletMoveTypePlanRows`. Since `71ae1cb` (2026-11-02, "merge Pomodoro task types by default") that means `planLanding(retype:false)`. Its `merge` outcomes are then dropped at `651:67`. | Before `71ae1cb`, `{}` meant `planRetype`, the D6 "naming retypes its tasks" contract. Now FIX → BUILD leaves FIX tasks under BUILD, and the toast says "keeps FIX". `gestureRetypeRenamePlanForTask` (`650:38`) is dead code. |
| Whole-entry move (Ctrl+Shift+M on an entry line, Enter on another entry) | `650:96-106` | Children move into the destination with no merge. Ctrl+X does merge. |
| Ctrl+X absorbing a container or unnamed entry into a typed survivor | `150:747` | The absorbed links' types are never added. |
| Capture "link into running" (`^r:id=x…`, `@r:id=x…`, `<text> @r:id=x`) | `capture/pomodoro_close.rs:2205` `link_existing_task_into_running` | Never calls `land`. |
| Capture named landing, silent skip | `capture/task_theme.rs:831-860` `stage_merge_rename` | Uses the first `#^id]]` line anywhere in the note. If that is a closed session or prose above `## Pomodoros`, the merge silently doesn't happen. |
| Moves that change *inherited* types without relocation | capture `>`, inbox route, project move-in (`batch_move.rs:33`); subtasks moved with a root (`655:55`, `task_move/command.rs`); `parent:` change Ctrl+Shift+- (`682:206`); project reversal (`665:413`); project promotion picks (`667:720`) | D8 runs only for the moved root, and only in some writers. |
| Successor into a shed continuation | `task-status-cycler/src/085e-successor-project-verdict.js:89` | Agreement is checked against the name *before* the close shed. |
| `bob types rename CHORE→X` | `pomodoro_themes/rename.rs` | Never rewrites `plan.default_type`, so default-typed tasks stay CHORE under `— X`. |
| Hand edits, `task_type:` / config edits, sync merges | — | Cannot be fixed at the source. This is what the reconcile fallback is for. |

Other notes from the audit:

- No plugin triggers reconcile. The only bob-side drift signal is `bob plan`'s lint,
  and the Obsidian plan block (computed in JS) doesn't show it.
- `relocate` can rename `— MEET` or grow it to `MEET + BUILD`. ✔ No `is_meet_name`
  check in `routing.rs:418-493`.
- Two places in `docs/task-types.md` disagree with the code. Lines ~815 and ~838 still
  say `ref today -p/-P` and named capture *retype*; both now merge.

## 4. Critique: is this a good idea?

**Yes, with a narrower definition of "remove" and two other enforcement points.**

Why enforce it at all:

- Pomodoro names feed Stats ("time by type"), the theme budget (`max_themes`), the Mac
  agenda, the menu-bar indicator, and capture's `=type` selectors. An I1 violation that
  survives to close puts real minutes under the wrong type for good. An I2 violation
  inflates composites (`PLAN + FIX + BUILD`), confuses selectors and the budget, and
  misleads at a glance.
- The system already promises agreement. Enforcing a promised invariant is cheaper than
  maintaining a lint nobody can act on. The lint has zero tests, and the Obsidian mark
  is blind to 97% of tasks.

Why "the Pomodoro follows the task" is the right repair direction:

1. **Provenance.** A task's type comes from a deliberate field, the reading rule, or a
   structural note default. An open entry's name was often produced by Bob itself
   (placement, merge, continuation), so it is the weaker signal.
2. **Blast radius.** Renaming open entries touches one file, today's daily note. Undo is
   one git revert, and closed history is untouched. Retyping tasks would write sticky
   `[type::]` exceptions into area and project notes. Those persist after the session
   and pollute the "fields are exceptions" model (PT13).
3. **Consistency.** R2 already chose this direction for every gesture: Enter merges,
   only Alt+Enter retypes. Reconcile doing the same means a gesture's output is already
   a fixed point of the repair.
4. **The old objection is answered by policy.** "Bob can't know which side a hand edit
   meant" is true. Choosing a fixed side is legitimate as long as gestures exist for the
   other side (D6 rename, Task Card `t`, Alt+Enter) and the choice is documented. You are
   making that choice.

The costs, stated plainly:

- **Hand renames get reverted.** If you type `— BUILD` over `— FIX` in the editor,
  reconcile turns it back into `— FIX` within about 15 minutes (add FIX, drop the
  unsupported BUILD). The only rename that retypes tasks is the gesture, and that
  gesture is currently broken (§3 regression). It must be fixed first.
- **Mid-session renames of the running entry.** These are visible in the menu bar and
  tmux. They are harmless (the timespan never changes), and they match what the close
  would have produced.
- **Unattended writes.** Reconcile already rewrites the daily note behind an open
  editor, through its snapshot and preimage guard, so this adds no new class of risk.
  It does add surprise, so the report must say what changed.

What I would do differently from the literal request:

- **"Remove unused types" needs a careful definition.** "Not actually used" should mean
  *no link of that type, struck or not*. Otherwise finishing the last FIX task halfway
  through a running `BUILD + FIX` session strips FIX before the close can credit it.
- **The close is the most valuable place to enforce, not reconcile.** Reconcile runs
  every 15 minutes, but Stats freezes at close. Today's close only *narrows*: it never
  adds a worked type that is missing, and it leaves single-type entries alone. A
  `— FIX` session that worked only a BUILD link therefore closes as FIX forever.
- **Fix gestures at choke points, not one by one.** The audit found more than 25
  writers. Most are removals that all lack the same post-step. Adding one
  "normalize touched entries" call to each writer family's shared helper is more robust
  than editing each gesture's local logic, and new gestures get it for free.

## 5. Adjustments to the requirements (proposed; each is a deliberate change)

- **A1. Open entries only.** Closed entries are history: they are what Stats and the
  `🍅` record say happened, like frozen `[t::]` / `[off::]` keys. A task retyped next
  week must not rewrite last week's sessions. *(Your wording, "a pomodoro that contains
  a task link", would otherwise include closed ones.)*
- **A2. Removal counts worked links as support, and is conservative.** A type component
  is removed only if all of the following hold:
  - the entry has at least one typed link;
  - no link in the entry has that type, counting struck or completed links as well as
    open ones;
  - no link in the entry is unresolvable.

  An entry whose only children are prose keeps its name, since that is planned intent.
- **A3. MEET is report-only.** An entry named MEET is owned by `bob gcal sync` and is
  never renamed. A non-MEET task under MEET keeps the `type_mismatch` lint. This
  happened once in the replay (`prepare-meeting-dan`, Oct 29). `relocate` also needs a
  MEET guard.
- **A4. The custom-name exception already exists; don't add another.** With `types:`
  configured, a custom name like `SASE V18` is all labels, which makes it a container.
  It holds any task and is never touched. Mixed names (`BOB + BUILD`) keep their labels
  exactly, and only the type components follow the rules. Unnamed `()` entries are
  containers too. This gives you the exception you were reaching for, defined by a rule
  that already ships in Rust and JS.
- **A5. Typing a type name for a brand-new entry retypes the task (D6), not merge.**
  R2's merge default protects the *other* tasks already in a destination. When a gesture
  creates the entry for this one link, there are none. A merge then yields `NAME + T`,
  and A2 would immediately drop the name you just typed. Reading the typed name as
  "this work is NAME" honors the keystrokes; that is the Nov 4 case. Enter into an
  *existing* entry keeps merging.
- **A6. Close settles instead of narrowing.** The closed name becomes its labels plus
  exactly the types of its worked links: existing order first, newly worked types
  appended in link order. This adds missing types and also applies to single-type
  entries. If there are no worked typed links, the name stays unchanged; MEET,
  containers, and unnamed entries never change. The continuation follows A2 instead of
  R6's "components that never had a link stay".
- **A7. Drift must be visible before reconcile fixes it.** The Obsidian mark should
  include inherited types, and should flag unsupported components on the entry line.
  Reconcile's output should list every rename, so an unattended revert of a hand edit
  is discoverable in the log and git.
- **A8. "Fix the keymaps" means "make every gesture's output a fixed point of the
  reconcile rule".** That is the testable definition: for every gesture vector,
  `agree_entry(output) == output`.

## 6. The rule: `agree_entry`

Signature: `agree_entry(name, links, sources) → name'`. It is pure, idempotent, and
lives next to `land` and `shed` in `routing.rs` and `merged.rs`, with a JS mirror in
`279-plugin-task-type-routing.js` and a new `agree_entry` section in
`tests/fixtures/pomodoro_themes/vectors.json`. That vector file is already
byte-for-byte shared with bob-plugins.

**Inputs.**

- `links` holds the entry's **direct, link-only child bullets**, using the same
  definition as the lint, the mark, and `relocation_apply::entry_child_links`. Links
  nested under prose are content.
- Each link is one of:
  - `Live`: unstruck, to an open task, with its effective type.
  - `Worked`: struck or `🍅`, to a completed task. Its type is the field, else the
    inherited suggestion computed as if the task were open. Close naming already
    resolves completed tasks' types this way through `placement_for_task`.
  - `Unknown`: unresolved, ambiguous, or no type.

**Steps.**

1. If the entry is closed, unnamed, `(unnamed)`, or a container, leave it unchanged.
2. If the entry is MEET, leave it unchanged and report each `Live` non-MEET link.
3. **Add (I1).** Collect the keys of `Live` links that are not among the entry's
   components, in link order with duplicates removed. These are the types to append.
4. **Support (I2).** The supported keys are the keys of all `Live` and `Worked` links.
   If at least one key is supported and there are no `Unknown` links, every type
   component whose key is not supported is dropped. Labels always stay.
5. **Order.** If exactly one type is dropped and exactly one is added, substitute in
   place, as `replace_type_components` already does. Otherwise drop first, then append
   in catalog spelling.

**Guarantee.** The supported keys are always a subset of the result's components, so a
non-empty supported set never yields a typeless name. The function is a fixed point of
itself.

| Before | Links | After | Why |
| --- | --- | --- | --- |
| `— FIX` | BUILD live | `— BUILD` | one-for-one substitution |
| `— BUILD` | BUILD, FIX live | `— BUILD + FIX` | add (same as R2 merge) |
| `— FIX + BUILD` | FIX live | `— FIX` | the Nov 4 case |
| `— BUILD + FIX` (running) | BUILD live, FIX struck | unchanged | worked link supports FIX |
| `— BUILD + FIX` | BUILD live, one unresolved | unchanged | Unknown blocks removal |
| `— BOB + FIX` | BUILD live | `— BOB + BUILD` | labels kept |
| `— SASE V18`, `— LATER`, `()` | anything | unchanged | container (A4) |
| `— MEET` | WRITE live | unchanged + lint | A3 |
| `— BUILD` | prose only | unchanged | no typed link (A2) |
| `[x] … — FIX` | BUILD | unchanged | closed (A1); fixed at close time by A6 |

The existing helpers become special cases. R2 merge is step 3 for one link. Shed is
step 4 with before and after sets. Relocation's rename branches are step 5. Over time,
writers can call `agree_entry` on the post-edit entry instead of computing each case
themselves.

## 7. Where it plugs in

### 7.1 Reconcile pass (the fallback)

- **Slot.** Run the pass after blocked-link consumption and before
  `apply_guarded_outputs`. It reads the final composed daily text
  (`compose.outputs[daily]`, falling back to the normalized daily text, the same lookup
  as `sync.rs` ~1377). By then:
  - links are deduped, canceled ones removed, completed ones struck or relocated,
    blocked ones consumed;
  - empty entries are already deleted.

  Renaming never empties an entry, so no further empty-entry pass is needed.
- **Data.** Reconcile already resolves references to `{path, block_id}` and holds file
  scans. It already builds a `HomeResolver` (~`sync.rs:533`), and `suggest_for_task`
  works as-is for open tasks. Use `Catalog::load_without_areas` for speed, as
  `successors.rs` does. Take task lines from the in-memory scans, not from disk.
- **Writes.** Entry-name tails only, never task fields. That honors the existing "reconcile
  never writes type fields" rule.
- **Output.** Add a `type_agreement[]` array to `SyncResult`. Each item carries
  `{entry_line, before, after, added[], removed[], reason}`, plus an `unrepaired[]` list
  for MEET or unknown cases. Add a human section such as
  `≈ renamed — FIX + BUILD → — FIX (BUILD has no link)`, with "would rename" under
  `--dry-run`. Include it in `change_count`.
- **Lint.** `bob plan` keeps `type_mismatch` for what reconcile cannot repair (MEET,
  unknown links) and gains a `type_unsupported` lint. Both lints need tests.

### 7.2 Close (A6)

Replace `narrow_closed` with `settle_closed`: worked types, appended if missing, with no
single-type exemption. The continuation runs `agree_entry` with carried links as `Live`.
This is a shared vector change, so both mirrors move together: Rust
`capture_pomodoro_close/names.rs`, JS `task-status-cycler/src/170-plugin-pomodoro.js`
and `060-pomodoro.js`. The successor bug in `085e` falls out once successors read the
post-close name.

### 7.3 Gesture choke points (A8)

Normalize only the entries a gesture touched: those whose link set or name changed, or
which hold a link to a task the gesture retyped or moved between notes. Unrelated
entries stay unchanged, and undo and preview stay scoped.

| Writer family | Choke point | Covers |
| --- | --- | --- |
| `bob capture` (zsh and the Mac app) | One final stage in `CaptureBatchPlanner` over the staged daily snapshot, before commit. Report renames in capture JSON so the Mac preview shows them. | Every capture form, including `=x` link-into-running, `>` moves, inbox route, project move-in, `#<type>`, and Ensure Next |
| Other bob writers of today's note: `task cancel`, `complete`, `move`, `merge`, `ref today` | A shared `ledger_agree_touched(contents, touched)` helper | Cancel and complete prunes, D8 source shedding, merge slot reuse |
| bob-navigation-hotkeys | `planDeferredPomodoroLinkCleanup`, the 651 bullet-move commit, the 650 entry move, the 316 relocation apply | The whole prune family, moves, Task Card retype |
| block-id-prompt | `060` link cleanup, `078` theme write | Unlink, delete, duplicate prune, link-to-today |
| task-status-cycler | Close (7.2), successor take-back | Mid-session strikes are already fine (worked links support) |

The JS side needs effective types for the links in touched entries, including
inherited ones. `taskTagIdentityForLine` already computes them for the mark.

### 7.4 Specific bug fixes (independent of the rule)

1. **Rename regression:** in `650-plugin-move-commit.js:140`, pass
   `{ typeMode: "retype" }` (or call the dead `gestureRetypeRenamePlanForTask`), and fix
   the preview copy at `200a:427`. *Ship first: it is tiny, and it is the only gesture
   that makes the entry master, which the "hand renames revert" cost depends on.*
2. **New-entry typed name retypes (A5):** `078:377` (`kind === "new"`) and capture's
   named creation path.
3. `stage_merge_rename` must look up the link under `## Pomodoros` open entries, and
   warn instead of returning `Ok(None)` silently.
4. Add the `relocate` MEET guard.
5. D8 for moved subtasks, `parent:` changes, and project reversal and promotion. The
   choke point covers the ledger side once these writers report the type changes.
6. `bob types rename` should warn when the renamed type is `plan.default_type`.
7. Fix the two `docs/task-types.md` passages that still say "retype" where the code
   merges.

## 8. Recommended solution

**Adopt the request with adjustments A1–A8: the Pomodoro follows the task.** Use one
pure rule (`agree_entry`), enforced at close (as settle), at each writer family's choke
point, and vault-wide by `bob task reconcile` as the safety net.

Phased so that each step is shippable and measurable:

1. **Phase 0, a bug fix (bob-plugins):** restore D6 retype on Obsidian entry renames
   (§7.4 item 1).
2. **Phase 1, rule and safety net (bob-cli + vectors):**
   - add `agree_entry` with Rust and JS mirrors and `vectors.json` cases (including
     idempotence);
   - add the reconcile pass with `type_agreement[]` output and dry-run;
   - add the `type_unsupported` lint plus tests for both lints;
   - add the `relocate` MEET guard.

   Run `bob task reconcile --dry-run` for a day to see the repair rate, then let the
   15-minute job apply it.
3. **Phase 2, close settles (A6):** shared vector change across `names.rs` and
   task-status-cycler.
4. **Phase 3, choke points (A8) and A5:** capture's final stage first (it covers the Mac
   app and every capture form), then nav's prune and move helpers, then block-id-prompt.
   Acceptance: every gesture vector's output is a fixed point of `agree_entry`, and the
   reconcile rename count trends toward zero. Reconcile renames that do appear point at
   a leaking gesture through the git commit that preceded them.
5. **Phase 4, visibility (A7):** the ledger mark covers inherited types and unsupported
   components.

**Records and docs to change.** These must go through `/sase_memory_write` when
implemented:

- A new decision, for example **"Open Pomodoro Names Follow Their Task Links"**. It
  supersedes the "drift is flagged and never silently repaired" rule (D5/R12) and
  partly supersedes R6's single-type and "never had a link" exemptions.
- Updates to the glossary strands `task-type` and `merged-pomodoro`.
- Updates to `docs/task-types.md` (Agreement, Merged Pomodoros) and
  `docs/task-status-hooks.md` (the new pass).

### Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Keep report-only (status quo + I2 lint) | Rejected. The lint appears only in `bob plan` output, the mark sees 3% of tasks, and you asked for repair. |
| Reconcile retypes tasks to match the Pomodoro | Rejected. It writes sticky fields vault-wide, inverts R2, and makes a transient plan overwrite durable data. |
| Reconcile moves disagreeing links to an agreeing entry (`place(T)`) instead of renaming | Rejected for the fallback. Moving a link you placed by hand is more surprising than renaming, and it breaks "this was worked in this session". It stays right for explicit Task Card retypes (D8). |
| Derive open names from links at read time (store only labels) | Rejected. Selectors, placement, empty planned placeholders, the Mac agenda, and the menu bar all key off stored names, and it reopens `decisions:pomodoro-theme-is-one-component`. |
| Live in-editor normalizer (ledger-tools rewrites on every edit) | Rejected. It would fight you while you type a name. Visibility (A7) plus the 15-minute fallback is enough. |
| Patch each of the ~25 gestures individually | Rejected as the main strategy. Use choke points; patch only real logic bugs (§7.4). |
| A separate `bob types agree` command | Not needed. Reconcile is already the scheduled whole-ledger reconciler, and its dry-run gives the same preview. |

### Open questions for Bryan

1. Is it acceptable that a typed-over entry name reverts within about 15 minutes, given
   the rename gesture is the supported way (after Phase 0)?
2. For a non-MEET task under MEET: lint only (recommended), or retype it to MEET the way
   R2 landing does?
3. Should a MEET-typed Event Task linked under a work entry grow it to `BUILD + MEET`
   (current R2 behavior)? That counts the session's minutes toward MEET in Stats.
4. Do you agree single-type closes may rename (A6)? For example, a `— FIX` session that
   only worked a BUILD task closes as `— BUILD`.
