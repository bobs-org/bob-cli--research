# `*` in capture: "this task blocks that one" — research, critique, and recommendation

*Researcher: cld · 2026-10-14 · bob-cli `e7e98d2`, bob-mac-capture `origin/master`*

## TL;DR

- **Do it.** The best moment to record a dependency is when you discover a
  blocker, usually while you are working on the blocked task. Today that
  takes a two-item draft with a block ID you invent yourself, and it cannot
  target tasks in nested notes at all. `*` fixes both, and adds no new data
  model.
- **Most of it already exists.** `New task *note:id` is exactly "add `New
  task` to `note#^id`'s Depends-On line". The Rust planner that does this for
  `&` on an existing task (`plan_existing_task_dependencies`) works in either
  direction if you swap the roles. It already handles the Depends-On line,
  `[?]`, `^prj` side effects, consumption, prerequisite promotion, the BLOCKS
  mirror, and cycle checks.
- **Your third requirement is already a system invariant, not new
  behavior.** A Blocked task keeps no live Task Link under today's open
  Pomodoros. The `&` writer consumes those links "together with any emptied
  entry", and `bob task reconcile` does the same within 15 minutes anyway
  (`docs/task-dependencies.md` §5, §13.5). `*` should reuse that path rather
  than get its own rule.
  - I confirmed in a throwaway vault that this path **deletes a running
    timed Pomodoro** without saying so. The JSON has no `pomodoro_blocks`
    entry, and human output only says `removed 1 live Pomodoro link(s)`.
  - The deletion behavior can stay. The reporting has to be fixed before
    `*` ships, because for `*` this is the common case, not an edge case.
- **The sigil `*` is fine, with guards.** None of 3,618 vault task lines has
  a token that starts with `*`, and Obsidian note names cannot contain `*`.
  - It needs Markdown-emphasis guards that `&` never needed: `*urgent*`,
    `**bold**`, and `* bullet` must stay literal. Today all of these are
    plain text, and copying the `&` lexer rules as-is would break them.
  - `?` is the runner-up. It matches the target's resulting `[?]` status.
- **Adjustments I recommend** (details in §5): build requirement 3 by reuse
  and report it loudly; order the writes so `New @inbox:id *T` hands the
  slot to the new task and keeps the session alive; never let a new task be
  born `[/]`; allow existing-task owners and `&`+`*` in one item; allow
  nested-note targets, refuse closed or archived ones; always mint the new
  task's ID; use distinct wire names on the Mac side.

---

## 1. What exists today (verified)

### 1.1 `&` grammar and execution

- `&note:block-id` means the captured task, or an explicit `@route+id` /
  bare `@route:id` owner, **depends on** `note#^block-id`
  (`docs/capture.md` "Adding prerequisites with '&'", ~line 1151).
- The lexer lives in `src/native/capture_language/dependencies.rs`:
  - `scan_line_dependencies` (:240) and `extract_line_dependencies` (:491).
  - The sigil scanner core is already generic: `scan_modifier_with_sigil`
    (:292), `scan_quoted_modifier`, `scan_block_id`, and the validators all
    take the sigil byte. `!` already reuses them.
  - Several places hard-code `&`: the line scan (:248), the bare-`&` check
    (:519-528), the `\&` unescape (:588, :684, :851), and every diagnostic
    string.
- Ownership resolves in `resolve_execution_ownership` (:922). It returns
  `NewTask` for task-creating kinds and `ExistingTask` for `@route+id` and
  bare `@route:id`.
- Execution goes through the staged batch planner (`src/native/capture/plan.rs`):
  - A new-task dependent goes to `plan_new_task_dependencies`
    (`dependencies.rs`:2606), which runs before the task is inserted.
  - An existing dependent goes to `plan_existing_task_dependencies`
    (`dependencies.rs`:2102-2589), which runs after the item inserts any
    prose.
  - The second function is the one `*` needs. It resolves and dedupes
    prerequisites and refuses closed dependents (:2136). It applies the
    `^prj` guards, merges into the managed line or inserts it, and writes
    `[id::]`/`[dependsOn::]`/`[fresh::]`. It then flips the dependent to
    `[?]`, blocks and tags residents, calls `consume_live_links`, promotes
    open prerequisites to the dependent's pre-capture lane (`plan_promotions`),
    and stages the prerequisite's `🧱 **BLOCKS:**` line.

### 1.2 Consumption is the existing contract

- `docs/task-dependencies.md` §5 says: "An add that leaves the dependent
  `[?]` also consumes the dependent's own live links in today's open
  Pomodoros, together with any emptied entry."
- §13.5 adds three rules:
  - It only touches live (unstruck) links under **today's open**
    Pomodoros. Closed entries and `🍅` history are never touched.
  - A link-only bullet is removed **with its subtree**.
  - "the existing empty-Pomodoro rule runs; it may delete a running timed
    entry (accepted; matches cancel)."
- The decision record `projects-block-from-prj-line` lists "Consumption may
  delete a running timed Pomodoro" as an accepted cost.
- Implementation: `consume_live_links` (`src/native/capture/project_deps.rs`:266-317)
  removes the exact string `[[{route}#^{id}]]`, then runs
  `plan_empty_pomodoro_removals` (`task_status_hooks/pomodoro.rs`:287).
  - That function deletes every entry with no child line at all, not only
    the one just emptied.
  - Reconcile runs the same removal on every pass (`task_status_hooks/sync.rs`:426),
    so a childless Pomodoro never survives long anyway.

**Experiment (throwaway vault under `/tmp`, real `bob` binary).**

Setup:
- `job.md` holds `- [/] #task Do cleanup tasks! ^cleanup`.
- `bob.md` holds `- [ ] #task Ask Kelly for references! ^ask-kelly`.
- Today's daily note has a closed JOB entry with `🍅 [[job#^cleanup]]`, a
  **running** `(**1010-1035** [t:: 25m]) — JOB` whose only child is
  `[[job#^cleanup]]`, and a placeholder BLOG entry.

Then I ran `bob capture '&bob:ask-kelly @job+cleanup'`. This is today's
two-existing-tasks spelling of what `Ask Kelly *job:cleanup` would do:

- `cleanup` became `[?]` and gained `⛓️ **DEPENDS ON:** [[bob#^ask-kelly]]`.
- `ask-kelly` gained `🧱 **BLOCKS:** [[job#^cleanup]]` and was **raised from
  `[ ]` to `[/]`**, the dependent's lane, under §5's promotion rule.
- The running JOB Pomodoro was **deleted outright**. The closed `🍅` entry
  was untouched.
- Human output: `bob capture: warning: removed 1 live Pomodoro link(s) to
  newly Blocked task(s)`. Nothing said a running session was deleted.
- `--dry-run -f json` had no `pomodoro_blocks` key. A second case, where
  the emptied entry was a future placeholder, also had none. The only clue
  was `plan_budget.themes` falling from 2 to 1.
- The same gap shows on the real vault (dry run): `&bob:star-block-capture
  @job_2026_apply_20+do-cleanup-tasks` would delete today's running
  `1010-1035 — JOB` session, and the output only says
  `removed 1 live Pomodoro link(s)`.

### 1.3 The round trip already works

After the block above, `bob capture --dry-run '!bob:ask-kelly'` prints:

```
[dry-run] ok would complete [/] → [x] Ask Kelly for references!  bob.md ^ask-kelly
  Hand-offs
  offer 1  unblocked [?] → [ ] Do cleanup tasks!  job.md ^cleanup · not pulled in
  -p 1 · -p all
```

So "block T on N, do N, close N, get offered T again" is already built.
The pieces are Successor Offers (`decisions:unblocked-tasks-are-offered`)
plus the `[unblocked::]` tickler (`decisions:unblocked-tasks-resurface-as-ticklers`).
`*` only needs to create the edge.

### 1.4 `*` can be written today, clumsily

```
Ask Kelly for references @inbox^ask-kelly

&inbox:ask-kelly @job+cleanup
```

Later items see earlier staged edits, so this works atomically today. It
has three problems:

- You have to invent a block ID.
- You type the new task's location twice.
- It only works when the blocked task lives in a root note. `@route` cannot
  contain `/`, per `is_route_token` (`markers.rs`:220).

`*` is therefore mostly sugar over an already-defined meaning. That lowers
the semantic risk, and the equivalence makes a good conformance test (§6.7).

### 1.5 Related work and vault facts

- **bob-cli-3p** (READY, large) is the Obsidian twin: a "Reverse Blocks…
  stage for editing a task's dependents". It also writes the dependents'
  Depends-On lines. `*` and 3p should share one contract section (§6.6).
- The glossary says BLOCKS lines are generated and "never read back, so
  dependencies are edited only on the dependent." `*` keeps that invariant
  if, and only if, it writes **T's Depends-On line** and lets the BLOCKS
  line on the new task be generated as usual.
- Vault today:
  - 57 Depends-On lines and 17 BLOCKS lines.
  - 401 open `[?]` tasks, mostly from schedules.
  - 0 of 3,618 `#task` lines contain a whitespace-delimited token that
    starts with `*`. Only 28 contain `*` at all, mostly inside code spans or
    the `[*]` checkbox.
- The feature's own vault task is `bob.md ^star-block-capture`.

---

## 2. Is this a good idea?

**Yes.** Six reasons:

1. **It captures the dependency at the moment it is discovered.** "I can't
   do T until N" usually occurs to you while T is open or running. The
   forward `&` makes you name N first, so N must already exist.
2. **It adds no new model.** The edge still lives only on the dependent's
   Depends-On line; BLOCKS stays generated. Every engine (reconcile, chips,
   nav, the Mac app) already understands the result.
3. **Downstream is already built.** Consumption, commitment transfer,
   BLOCKS, hand-off offers on close, and ticklers on recovery all exist.
4. **It follows the thin-client rule** (`decisions:mac-capture-is-a-thin-client`).
   All semantics live in bob; the Mac app only presents them.
5. **It is strictly more expressive than the two-item workaround,** because
   it reaches tasks in nested notes.
6. **The usage signal is real.** The vault already has 57 Depends-On lines,
   and the October commit log shows the dependency gestures reworked several
   times (project blocking, capture drops, BLOCKS mirrors, successor
   offers).

**Costs and risks to accept with open eyes:**

- **Grammar budget.** Capture already overloads `@ ^ : / + & ! = # % ~`.
  `*` already means Next (`[*]`) and park (`=x*`). In Bob, `*` reads as
  "make Next", while `*T` makes T *leave* Next. One post-hoc mnemonic does
  work: the commitment transfer hands T's star to the new task. Still, the
  overload is real.
- **A capture becomes destructive by default.** It edits a task you did not
  create, and it may remove Task Links, their subtrees (notes you typed under
  the link in the running session), and the running session itself.
  - On a `^prj` target it blocks the whole project: every resident flips to
    `[?]`, gains `#prj_is_blocked`, and loses its links.
  - The preview must make this blast radius obvious. Today it does not even
    for `&`.
- **The block is soft.** Under `decisions:capture-link-drops-blocking-deps`,
  a later capture link gesture on T (`^job:cleanup`, `@job+cleanup!`, …)
  drops N from T's Depends-On line and links T. I think that is right (the
  preview shows the drop), but expect `*` to be undone by reflex re-linking.
- **Lanes don't survive Blocked.** If T was Next or Pending, blocking it
  costs that lane for good. When N closes, T recovers to Ready with an
  `[unblocked::]` tickler and a hand-off offer, not to Next. That is the
  established design (`decisions:task-lanes-are-sticky`); just know `*` makes
  it happen more often.
- **Two implementations on two release trains.** Mac work is gated by macOS
  CI, and `bob` and the app are installed separately (§7.4).

**Would I take a different approach?** No, but I considered these:

| Alternative | Verdict |
| --- | --- |
| Keep the two-item draft (§1.4) | Zero work. Too slow at the moment it matters, and impossible for nested notes. |
| Modify `&` instead of adding a sigil (`&>note:id`, `&^note:id`) | One picker, but awkward to type and parse, and it reads worse than a sibling sigil. |
| A direction toggle inside the Mac `&` picker only | Bob is the grammar authority, so the draft still needs a textual reverse form. Good later as a convenience (§7.5) on top of `*`. |
| Obsidian-only reverse stage (bob-cli-3p) | Complementary. It does not cover Mac capture, which is where blockers get jotted. |

---

## 3. Proposed semantics

### 3.1 Definition

```
<item owning task O> *note:id   ≡   add O to note#^id's Depends-On line
```

- **O, the owner,** is whatever `&` would treat as the dependent: a newly
  captured task, or an explicit existing `@route+id` or bare `@route:id`.
- **T, the target,** is the existing task at `note#^id`. It becomes the
  dependent.
- The edge is written on T. Every downstream effect is the same as an `&`
  add with T as the dependent (§5 / §13 of `docs/task-dependencies.md`).

### 3.2 Examples

| Draft | Reading |
| --- | --- |
| `Ask Kelly for references *job:cleanup` | New inbox task N. `job#^cleanup` now depends on N, is `[?]`, and loses its live links today. N rises to at least Next (capped, §5 A4). |
| `Ask Kelly @inbox:ask-kelly *job:cleanup` | Same, plus N is linked into the current Pomodoro **before** T's link is consumed. N takes T's place and the running session survives (§5 A3). |
| `Ask Kelly *job:cleanup *job:send-batch` | N blocks both tasks, in typed order. |
| `Call registrar &school:transcript *job:apply-x` | N waits on the transcript and blocks the application: an "insert between". The cycle check covers `apply-x ⇝ transcript`. |
| `*job:cleanup @bob+ask-kelly` | Existing `ask-kelly` blocks `cleanup`. Same as `&bob:ask-kelly @job+cleanup`; mode `task_dependency`. |
| `*projects/house/kitchen:order-cabinets` | Allowed target in a nested note, which `&`'s owner spelling cannot reach. |
| `*cash:prj` (a `^prj`) | Blocks the project: `^prj` plus every resident goes `[?]` and tagged, and their links are consumed. Refused if N routes inside that project or a descendant. |
| `*job:cleanup` with no task text | Incomplete: needs `dependency_target` ("add task text or `@note+task-id`"). |
| `Fix *urgent* bug`, `Read **Dune**`, `* Buy milk`, `5 * 3`, `R*D` | Literal text (§4.2 guards). |
| `Ask Kelly \*job:cleanup` | Literal `*job:cleanup` (only the `\` is consumed). |

### 3.3 Order of operations inside one item

These run in the shared staged batch. Nothing is written until the whole
draft plans.

1. Resolve and validate every `*` target (§3.4).
2. Plan the owner's own `&` prerequisites, if any (today's
   `plan_new_task_dependencies`). N may be born `[?]`.
3. Insert N, minting its block ID (§5 A8). If N was spelled `@route:id` and
   is not Blocked, stage its Task Link now.
4. For each `*` target, in typed order, call
   `plan_existing_task_dependencies(dependent = T, deps = [N])`. That call:
   - merges the Depends-On line and fields, and stamps T fresh;
   - flips T to `[?]` (and handles `^prj` residents and the tag);
   - consumes T's live links, then removes now-childless entries. Because
     step 3 already staged N's link, a session holding N's new link
     survives;
   - promotes N to T's pre-capture lane, capped at Next (§5 A4). If N is
     itself Blocked, the walk continues through it to N's prerequisites;
   - stages N's BLOCKS line, one entry per target.
5. Report: one `dependency_updates[]` entry per touched dependent, plus
   consumed links and removed Pomodoro entries (§6.5).

### 3.4 Target guards (refuse with an actionable error; nothing is written)

- The target must be an **open** task. Done or Cancelled already refuse
  ("dependencies cannot reopen a completed task", `dependencies.rs`:2136).
  The picker should exclude these rows, not merely disable them.
- Refuse a target in `done/` (archive), the previous daily note (never
  written, §4.1), `_templates`/`_generated`/`_conflicts`, fenced or
  blockquoted lines (DP29), or a note with more than one accepted Depends-On
  line or a malformed one (R10). Today only the closed-status check exists
  on the dependent side.
- Refuse the owner itself, a duplicate (O is already on T's line: report
  `already_present`, write nothing), and a new cycle (O ⇝ T already; shared
  `reject_new_cycles`).
- If T is a `^prj` and O lives in that project's note or any descendant,
  refuse (`refuse_internal_prj_targets`). That edge is a guaranteed
  deadlock, since residents are blocked by their own project.
- Combination rules are the same as `&`: session operators, section
  bullets, project-note constructions, `!` completions, and suffixed owners
  (`#name`, `=…`, `!`) reject `*` with a targeted diagnostic. One extra:
  `@route:id=x… *T` is rejected, because closing and blocking in one item is
  incoherent.

---

## 4. The sigil

### 4.1 Collisions found (probed with `bob capture-parse`)

Today these are all plain task text, and must stay that way: `* Buy milk`,
`*urgent* call mom`, `call mom *now*`, `Buy **bold** milk`, `Buy milk *`.

Copying `&`'s rules as-is would break them:

- A leading bare `*` would open the picker.
- `*urgent*` and `*now*` in a marker run would scan as `Partial` and block
  submit with "selection is incomplete".
- `*foo*:bar` would scan as complete with note `foo*`, because
  `validate_note` currently accepts `*`.
- `=x did stuff *` would turn a close into an error.

Existing `*` uses are each isolated:

- `=x*…` / `=*…` park lists only appear inside `=` tokens
  (`close_selection.rs`).
- `* ` is a bullet marker on continuation lines only, and needs a following
  space (`draft.rs`:501/538).
- `[*]` is a checkbox status, never typed in drafts.

There is no Markdown-emphasis protection anywhere today. The only precedent
is the `==highlight==` guard in the `=` lexer (`item.rs`:1111-1127).

### 4.2 Guard rules (add as lexer vectors)

`*` is a directive only when **all** of these hold:

1. It starts a whitespace token, in a leading or trailing marker position,
   exactly like `&`.
2. The next byte is not whitespace and not `*`. So `**bold**`, `* bullet`,
   and `5 * 3` stay literal.
3. The rest of the token contains no `*`. So `*urgent*` stays literal. This
   is safe because note names cannot contain `*`, so `validate_note` should
   reject `*` in the note component for both sigils.
4. A **bare** `*` opens the picker only as the **last** token of a line,
   never as the parent's first token. That protects pasted `* item`
   bullets.
5. `\*` escapes, exactly as `\&` does.

Accepted residue: a trailing word such as `Support *nix` scans as a partial
`*nix` and blocks submit with the teaching error. Users can write `\*nix`.
The vault has no such tokens.

**Shell note:** `*` is a zsh glob (`&` backgrounds a job), so the CLI already
requires single-quoting. Keep the existing docs advice.

### 4.3 Alternatives

| Sigil | For | Against |
| --- | --- | --- |
| **`*`** (requested) | Next to `&` on the keyboard (⇧7/⇧8) and visually paired. Zero vault collisions. Not a legal note-name character. | Means Next (`[*]`) and park (`=x*`) elsewhere in Bob. Needs the emphasis guards above. |
| `?` | Mnemonic for the target's result: it becomes `[?]` Blocked. Unused in the capture lexer. Zero token-start collisions (questions attach `?` to a word). | Far from `&`. Reads like "help" or "query". |
| `>` | Arrow semantics ("this → that"). | Blockquote and comparison noise (`>30`). Has no counterpart to `&`. |
| `\|` | "Wall" ↔ 🧱. | Wikilink aliases and tables. Hard to read in proportional fonts. |
| `$`, `~` | — | `$` is money (2 vault hits trailing). `~` is paths and drop lists (9 trailing hits). |

**Recommendation: keep `*`.** Adjacency and the clean vault data win, and
the guards are cheap. If the `[*]` overload bothers you, pick `?`. Decide
before Phase 1, because the Mac span names and fixtures bake the choice in.

---

## 5. Requirement adjustments (explicitly called out)

| # | Your requirement | Adjustment | Why |
| --- | --- | --- | --- |
| **A1** | "remove that task link (and the Pomodoro iff it becomes empty)" | **Reuse the existing consumption path; do not write `*`-specific logic.** Clarify the scope: only *today's open* Pomodoros; closed entries and `🍅` history are kept; "empty" means **no child lines at all**, so a note bullet keeps the entry. A link bullet's own subtree goes with it. | It is already the invariant (§5/§13.5), and reconcile would do it within 15 minutes regardless. A second rule would drift. |
| **A2** | (implicit) | **Report it.** Emit removed entries in `pomodoro_blocks` and a structured `consumed_links[]`. Human output names the session and says "running" when it is (e.g. `removed Task Link from JOB 10:10–10:35 (running) · deleted the empty Pomodoro`). Fix this for `&` too. | Today a running session vanishes behind a one-line warning (§1.2). For `*` this is the main effect, and the Mac preview is the only safety net. |
| **A3** | (new) | **Order "link new task, then consume"** so `New @inbox:id *T` puts N in the current Pomodoro and keeps the session alive. Document it as the "take its place" idiom. **No auto-linking by default.** | Covers "do the blocker now" without a new rule, and keeps "Unblocked tasks are offered, never auto-linked" intact. Many blockers are waits ("Wait for Joe's review"), which you would not want linked. |
| **A4** | (implicit) | **Cap the new task's commitment transfer at Next `[*]`.** A task created by `*` is never born `[/]`, even when T was Pending. | `[/]` is set by `=x` work; a never-worked task in PENDING is misleading. This is a small parameter on `plan_promotions`. Strict `&` parity is the alternative (§8 Q1). |
| **A5** | "the new task blocks…" | **Also allow existing-task owners** (`*T @route+id`), and **allow `&` and `*` on one item.** | Same ownership rule as `&`, so no special-case diagnostic. `&`+`*` gives "insert between" for free, with the cycle check already there. |
| **A6** | "the specified task" | **Targets must be open; nested notes allowed; refuse archive, previous-daily, and template targets.** | `*` reaches notes `@route` cannot. Blocking a closed task is meaningless. The previous daily note is never written. |
| **A7** | (implicit) | **`^prj` targets allowed** (blocks the project), with the blast radius in the preview; refuse when N routes inside that project or a descendant. | Same as `&` on `^prj` (§13.10). The internal guard prevents a deadlock. |
| **A8** | (implicit) | **Always mint N's block ID** (or use the typed `^id`/`:id`), even with `dependencies.blocks_lines: false`. | T's Depends-On line needs `[[inbox#^id]]`. `&` mints only for BLOCKS (`dependencies.rs`:2676-2708). |
| **A9** | (implicit) | **Markdown-safe lexing** (§4.2). | `&` never needed it; `*` does. |
| **A10** | (implicit) | **Picker pool and ranking for `*`:** open tasks only. Rank tasks with a live Task Link in today's open Pomodoros first (running entry first), then In Progress, Next, same-note, and the rest. | The dominant use is "the thing I'm on is blocked". Closed rows are useless here, unlike `&`, which keeps history findable. |
| **A11** | (keep) | Leave the **soft-block interaction** alone: a later capture link of T drops N under `capture-link-drops-blocking-deps`. Make sure the drop preview names N. | Consistent with an accepted decision; reopening it is out of scope. |

---

## 6. bob-cli implementation plan

### 6.1 Lexer and parse

- **Generalize, don't fork.** Turn the `&`-specific spots in
  `dependencies.rs` into a two-sigil scan with a `ModifierDirection {
  DependsOn, Blocks }`:
  - the line scan at :248;
  - the bare check at :519-528;
  - the unescape at :588/:684/:851;
  - the messages at :868-913 and in `editor_parse.rs` :607-627.
- Add the §4.2 guards behind `direction == Blocks`, plus the
  `validate_note` `*` rejection for both sigils.
- Keep the two directions in **separate lists** on `ParsedItem` /
  `DependencyEntry` (`dependencies` and `blocked_tasks`). Do not add a
  direction field to the existing list: every current consumer reads
  `dependencies[]` as "prerequisites".
- `dependency_target` stays the item's task owner for both lists (document
  this). Ownership reuses `resolve_execution_ownership`, including `@@`
  inheritance (`finish_inherited_dependency_target`).
- **Wire names.** Use new, distinct ones everywhere:
  - spans `blocked_task_sigil`, `blocked_task_note`, `blocked_task_block_id`;
  - need `blocked_task` (picker still open);
  - per-item parse array `blocked_tasks[{raw, note, block_id, quoted, range}]`.

  Reuse need `dependency_target` (no owner named) and mode
  `task_dependency` (existing-owner edge-only items). Do not name anything
  `task_blocks`; that is already the batch preview field.
- **Fix while there:** `@cash &foo:bar Buy milk` captures the literal body
  `&foo:bar Buy milk`, because the leading run does not skip a leading
  `@route`. `&foo:bar @cash Buy milk` works. `docs/capture.md` promises
  "either order". `*` would inherit this bug.

### 6.2 Completion

- Add context `blocked_task` in `capture_complete/engine.rs` (beside the
  `task_dependency` arm at :238-262).
- Candidates come from `capture_dependency_tasks::discover`, filtered to
  open tasks, ranked as in A10.
- Rows reuse the `task_dependency` row shape. The guard field is
  `already_blocked` (O is already on T's Depends-On line; for an existing O,
  read T's line). Add `disabled_reason` for self, would-cycle (existing O
  only), `^prj` internal, and duplicate IDs.
- Echo `query` and `owner` the same way.

### 6.3 `bob capture-task-id`

Add an additive `blocks_replacement` (`*note:id`, quoted as needed) beside
`dependency_replacement`, `complete_replacement`, and `parent_replacement`
(`capture_task_id.rs`:320-340). No new option is needed, which respects
`cli_rules` (the `capture-*` protocol may only grow additively).

### 6.4 Execution

- Add a `plan_blocked_targets` step in `plan.rs` after new-task insertion
  (and in the dependency-only path for existing owners, next to
  `plan_dependency_only_item`). It calls `plan_existing_task_dependencies`
  once per target with roles swapped.
- The shared function needs four changes:
  1. **Address the dependent by vault path, not route.** Nested notes were
     unreachable before.
  2. **Consume by link identity, not exact string.** `consume_live_links`
     matches `[[{route}#^{id}]]` literally. A nested target linked in the
     ledger as `[[kitchen#^order-cabinets]]` (basename form) would be
     missed, and the stale link would sit there until reconcile. Resolve
     ledger links through the shared resolver instead.
  3. **Dependent-side guards** from §3.4.
  4. **Promotion cap** (A4) when the prerequisite was created in this item.
- Re-locate N by block ID after each target's write.
  `locate_new_task_ref` (:2844) matches exact text, which goes stale once
  N's line gains `[id::]` or a promoted status.
- One BLOCKS line on N lists every target, via `stage_blocks_delta`. The
  kill switch skips only the BLOCKS mirror; the Depends-On edge still lands.

### 6.5 Output (additive, schema v1)

- `dependency_updates[]`: one `DependencyUpdateJson` per touched dependent
  (N for `&`, each T for `*`). Keep the singular `dependency_update` as
  today for compatibility.
  - The existing shape already describes `*` accurately: `dependent_*` = T,
    `prerequisites` = [N]. Old Mac builds render "Add dependency to
    '<T>' … Waiting on 1 · Blocked", which is correct.
- `consumed_links[]`: `{pomodoro, pomodoro_line, running, link, task}`.
  Emptied entries go into `pomodoro_blocks` as `removed` (A2).
- `minted_block_id` for N. Leave `minted_dependent_block_id` alone, since
  its name is wrong for `*`.
- Human output, for example:

  ```
  ✓ Ask Kelly for references!  mac_inbox.md ^ask-kelly-for-references   [*] Next
    🧱 blocks "Do cleanup tasks!"  job.md ^cleanup  [/] → [?] Blocked
    − removed its Task Link from JOB 10:10–10:35 (running) · deleted the empty Pomodoro
  ```

### 6.6 Docs and contract (land first, per thin-client rule)

- **`docs/capture.md`:**
  - grammar-table rows;
  - a new "Blocking existing tasks with '*'" section after the `&` section
    (examples, guards, ownership, order of operations, JSON);
  - collision rows (`*urgent*`, `**bold**`, `* item`, `\*`).
- **`docs/task-dependencies.md`:**
  - a short §5 bullet "Adding a dependency from the prerequisite side",
    shared with bob-cli-3p's Reverse Blocks stage;
  - "capture `&`/`*`" in the §2.4 writer column and the §14.7 writers
    table;
  - a vector table (e.g. `ST1…`) mirroring the PDG/DW/BW style.
- **Decision record.** Add one via `/sase_memory_write`, for example
  "Capture `*` adds the new task to the target's Depends-On line". Record
  the sigil choice and rejected alternatives, consume-by-reuse, the Next
  cap, and the "link then consume" ordering.

### 6.7 Tests

Mirror the `&` suites:
- `tests/cli/capture/parse_dependency.rs` (28 tests);
- `tests/cli/capture/complete_dependency.rs` (11);
- `tests/cli/capture/blocks.rs` (6);
- the lexer unit tests.

Must-have vectors:
- the emphasis guards;
- **equivalence**: `N *T` and the two-item draft (§1.4) produce
  byte-identical vault diffs, apart from the minted ID;
- running-session deletion is reported;
- `N @inbox:id *T` keeps the session;
- a nested-note target with a basename ledger link is consumed;
- a `^prj` target blocks, tags, and consumes residents;
- an internal `^prj` target is refused;
- the `&`+`*` cycle is refused;
- a closed, archived, or previous-daily target is refused;
- dry-run equals the live run;
- a second run is a no-op.

---

## 7. Bob Mac Capture plan

### 7.1 Today's coupling (summary)

- The app never sniffs `&` in the draft text. It routes on bob's span kinds,
  `needs`, and `context`.
- But the `&` picker's wording, trigger byte, and routing are spread over
  about 60 sites. Main files:
  - `CapturePickerSource.dependency` (`CapturePickerPresentation.swift`,
    19 switch arms, trigger byte `38`);
  - `DependencyPickerPresentation.swift` (`leadingSigil: "&"`,
    `insertionPrefix: "&"`, "Choose a prerequisite", "will block the
    dependent");
  - `CapturePanelModel.swift`:
    - `context == "task_dependency"` (2474, 3195);
    - Backspace sigil `38` (4095);
    - hard-coded needs and span sets in `shouldRequestCompletion`
      (6646-6692);
    - the Add-ID flow, which needs `dependency_replacement` (5001-5270).
- Decoding is tolerant except `dependency_update` and `link_guard` (plain
  `try`). Parse, complete, and task-id require `schema_version == 1`, so
  everything must stay additive.

### 7.2 Why distinct wire names (not "reuse `task_dependency` + a direction field")

- Reusing would look cheaper: highlighting, triggering, and insertion would
  just work.
- But an older app running against a newer bob would then route a `*`
  picker through the `&` Add-ID flow. That flow splices
  `dependency_replacement` (`&note:id`), **silently reversing the edge**.
- With distinct names an older app degrades safely:
  - neutral color, no picker;
  - a fully typed `*note:id` still captures correctly through
    `bob capture`;
  - the generic `task_blocks` / `pomodoro_blocks` cards still preview the
    edits.

### 7.3 Recommended Mac change set (one phase, about S–M)

- **Shared picker, parameterized by direction.** Add `direction` to the
  dependency picker source, or a `.blockedTask` case backed by the same
  `DependencyPickerPresentation`. Vary the sigil, insertion prefix, and
  copy:
  - "Blocks", "Choose a task to block";
  - "Becomes Blocked until this is done";
  - "space adds another *".
- Route `context == "blocked_task"` to the shared handler.
- Add need `blocked_task` to `pickerNeed` and `shouldRequestCompletion`.
  Add the three span kinds to the trigger set and the palette, using the
  same colors as `dependency_*`.
- Backspace on an empty filter must accept `42` (`*`) as well as `38`.
- Add-ID flow: use `blocks_replacement`. If it is missing, show the
  existing "This Bob is too old…" message.
- Preview:
  - iterate `dependency_updates[]` (fall back to the singular field);
  - show the consumed-links summary and the running-session callout as a
    destructive (red) line;
  - removed entries already render red once bob emits them in
    `pomodoro_blocks`.
- Fixtures: extend `fake-bob` and add fixtures mirroring the seven
  `task-dependency-*.json`. Tests mirror `DependencyPickerPresentationTests`
  (19) and `CaptureDependencyPanelTests` (11).
- Watch item: a lone `*` at the end of a continuation line is treated as a
  placeholder bullet for Tab/Shift-Tab (`CapturePanelController.swift`:188-199,
  1052-1084). Bob's guard 4 makes that same bare `*` a picker trigger, so
  check Tab precedence with the reopen chip (`CaptureKeyCommandRouter.swift`:204).

### 7.4 Version skew

- **New app + old bob:** old bob reads `*job:cleanup` as literal task text.
  The live preview shows it in the body, so the user sees the problem before
  submitting. This is not destructive.
- **Old app + new bob:** safe degradation (§7.2).
- No `--version` gate is needed.

### 7.5 Later nicety (not v1)

A picker key that flips the active token between `&` and `*`. The app must
ask bob for the rewrite (`capture-rewrite`), not edit the sigil itself, so
the grammar stays in bob.

---

## 8. Open questions for Bryan

1. **Q1 — lane cap (A4).** Should a new `*` task top out at Next, or match
   T's lane exactly (Pending → `[/]`), as `&` does today? I recommend the
   Next cap.
2. **Q2 — default route.** Should N default to T's note instead of
   `mac_inbox`? I recommend **no**: the inbox stays the triage point, and
   `@route` is one token away.
3. **Q3 — running-session deletion.** Accept it (the current system-wide
   rule, now visible), or reopen it system-wide? One option would close the
   running session at "now" and keep T's link as `🍅` history. Any change
   must also land in reconcile, not only in `*`. I recommend accepting it
   for v1 and relying on A2 + A3.
4. **Q4 — sigil.** `*` (recommended) or `?`?

---

## 9. Pre-existing issues found (affect `*`; worth fixing first)

Issues 1 and 2 are filed as task beads **bob-cli-7l** and **bob-cli-7m**.

1. **Consumption is invisible in output (bob-cli-7l).**
   - Root cause: `PomodoroBlockRef::removed` is documented to "never report
     the entry itself" (`pomodoro_blocks.rs`:93-102).
   - What happens: `&` consumption that removes a link and empties an entry
     (even the running timed one) emits no `pomodoro_blocks`. Human output
     only says `removed N live Pomodoro link(s) to newly Blocked task(s)`.
   - Reproduced in a throwaway vault, with both a running entry and a
     placeholder entry.
   - Why it is odd: `consume_live_links` does compute `pomodoro_refs`, and
     `plan_dependency_only_item` passes them on, but none reach the output.
2. **The leading `@route` breaks a following `&` (bob-cli-7m).**
   `@cash &foo:bar Buy milk` silently captures the body `&foo:bar Buy milk`.
   The leading-run loop in `extract_line_dependencies` stops at the first
   token that is not a modifier, and unlike the trailing run it never skips
   `@…` tokens.
3. **Consumption matches links as exact strings** (`[[route#^id]]`). Harmless
   today, because `&` dependents are always root routes. It becomes a bug
   once `*` targets nested notes.

---

## 10. Recommended solution

Ship `*` as **the reverse of `&`, implemented as `&` with the roles
swapped**:

1. **Contract first.** Write the `docs/capture.md` section and the
   `docs/task-dependencies.md` additions (§6.6), with lexer, execution, and
   equivalence vectors. Add a decision record covering the sigil, the
   ordering, the cap, and consume-by-reuse. Fix issues 9.1–9.3 in the same
   epic, before or alongside.
2. **bob-cli parse and complete.**
   - Generalize the `&` lexer to two directions, with the Markdown guards
     of §4.2.
   - Use distinct wire names: `blocked_task*` spans, the `blocked_task`
     need and context, and the `blocked_tasks[]` parse array.
   - Rank the picker with open tasks only and today's linked tasks first.
   - Add `blocks_replacement` to `capture-task-id`.
3. **bob-cli execution.** After inserting the new task (and its own link,
   if `:id`), call `plan_existing_task_dependencies` once per target with
   dependent = target and prerequisite = the new task. This gives for free:
   - the Depends-On edge on the target, `[?]`, `^prj` blocking and tags;
   - **consumption of the target's links under today's open Pomodoros,
     including deleting entries left with no children**: your requirement,
     via the existing rule;
   - commitment transfer to the new task (capped at Next), and the BLOCKS
     mirror on the new task.

   Extend that function with path-addressed dependents, identity-based
   consumption, dependent-side guards, and structured reporting of consumed
   links and removed Pomodoros. Mint the new task's ID unconditionally.
   Allow existing-task owners and `&`+`*` together.
4. **Bob Mac Capture.**
   - One shared dependency picker parameterized by direction, keyed off the
     new `blocked_task` context and need.
   - Fix the Backspace sigil check and use the new Add-ID replacement.
   - Preview cards for `dependency_updates[]`, consumed links, and a red
     running-session callout.
   - Older apps degrade safely, because no `dependency_*` name is reused.
5. **Leave alone:** no auto-linking of the new task (use `@route:id` to
   take the slot), the soft-block drop on later link gestures, and the
   system-wide consumption rule.

Effort: bob-cli about M (lexer and guards M, planner reuse S–M, picker S–M,
output and docs M); Mac about S–M. Suggested epic phases: contract →
cli-parse/complete → cli-exec/output → mac → decision/memory. bob-cli-3p's
reverse Blocks stage can later implement the same §5 "prerequisite side"
contract on the Obsidian side.
