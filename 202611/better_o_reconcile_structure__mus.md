# Better `o` / `Ctrl+Shift+O` and all-ops respect for task-block structure (`^better-o`, `^all-ops-reconcile-tasks`)

**Researcher:** mus · **Date:** 2026-11-25 · **Swarm suffix:** `__mus`
**Input:** `~/bob/bob.md` `^better-o` (`bob__better-o`, depends on `bob__micro-tasks`) and `^all-ops-reconcile-tasks` (starts after `^better-o`); epics `bob-cli-on` (closed 2026-11-23), `bob-cli-pq` (closed 2026-11-23), `bob-cli-ph` (open); live `bob-cli` source (`src/native/task_block_layout*.rs`, `src/native/task_tidy/`, `src/native/task_status_hooks/`, `docs/task-requirements.md` §3), live `bob-plugins` source (`plugins/task-status-cycler/src/010-core.js`, `140-plugin-vim.js`, `150-plugin-commands.js`, `110-plugin-lifecycle.js`); vault `~/bob/.obsidian/hotkeys.json`; decisions `task-reqs-are-met-with-their-task`, `task-deps-are-depends-on-links`.
**Peer reports:** not consulted (per swarm instructions).

## TL;DR and recommended solution

**Do both tasks, but re-scope them.** The direction is right and matches the already-accepted writer-rule contract (`docs/task-requirements.md` §3: "Order is a writer rule plus an explicit `bob task tidy`. It is never a validity rule and never a silent reorder."). The current phrasing is too broad to build ("all keymaps and capture panel operations", "so `reconcile` updates files much less often") and the `o` requirement as written will split task blocks if built literally.

Recommended:

1. **Fix `o` + `Ctrl+Shift+O` first as the pilot** (`^better-o`), behind the exact `task_block_layout` slot contract, with sibling-vs-child semantics fixed and the first-req `NOTES` scoop included. This is the only new user-visible behavior.
2. **Reframe `^all-ops-reconcile-tasks` as "every Bob writer inserts into the right zone; hand edits are never reshuffled"** — an enumerated writer inventory with shared-vector twins, not a blanket "respect reconcile structure". Keep `bob task reconcile` focused on status/derivation; do **not** teach it to tidy. Measure success with `bob task tidy --dry-run` cleanliness plus a `reconcile` managed-link-zone dirty count, not with "reconcile writes less" alone.
3. **Do managed-link writers first** (`DEPENDS ON`, `BLOCKS`, `LINKS`/`LINKED FROM`, `[dependsOn::]`/`[id::]` R1–R10), then req writers, then notes/`NOTES`/drawer writers, then logs. Capture-panel writes are already mostly compliant (they go through the Rust writers); the gap is almost entirely Obsidian keymaps.

Details, evidence, and the critique follow.

## 1. What the two tasks actually ask for

From `~/bob/bob.md` (2026-11-25 read):

- `^better-o` (Next, `[*]`, `id:: bob__better-o`, `dependsOn:: bob__micro-tasks`):
  - "See epic bob-cli-on and (wip) bob-cli-pq for context."
  - "`o` should create new task below current one when task headline is selected!"
  - "Both should respect the task sub-bullet ordering (links < reqs < drawers < logs)! A task with one or more reqs should list notes in an explicit notes drawer (see bob-cli-ph for recent changes to drawers which are ongoing — so you might want to leave notes on that bead)."
- `^all-ops-reconcile-tasks` (open `[ ]`, created 2026-11-25, `LINKS: starts after ^better-o`):
  - "Make all Obsidian keymaps and capture panel operations respect `bob task reconcile` structure!"
  - "The goal is to make it so the `bob task reconcile` command needs to update files much less often since tasks are already left in a good state (after my morning GTD review, for example)."

Dependencies: `^better-o` depends on `^micro-tasks` (`bob__micro-tasks`, closed 2026-11-23, "Require that task sub-bullets be prefixed with `TASK:`/`ALSO:`?!" — the req-model precursor, superseded by `bob-cli-on`'s req implementation). `^all-ops-reconcile-tasks` is explicitly sequenced after `^better-o`.

Related closed work: `bob-cli-on` ("Task requirements (reqs)", 17 phases, closed 2026-11-23) shipped `src/native/task_block_layout.rs`, `src/native/task_block_layout/edit.rs`, `tidy.rs`, `writers.rs`, `src/native/task_tidy/command.rs`, `src/native/task_reqs.rs`, and the first-req scoop; `bob-cli-pq` (criterion diamond, closed 2026-11-23) changed only rendering, not layout. Open and interacting: `bob-cli-ph` ("True-case drawers: bold headers that keep their real names", with `ph.4`, `ph.5`, `ph.6`, `ph.7`, `ph.8`, `ph.10`, `ph.11`) is actively renaming `NOTES` casing and drawer recognition — any `NOTES`-drawer work must track it.

## 2. Current behavior (evidence)

### 2.1 Canonical structure already exists — in Rust only

`src/native/task_block_layout.rs` (module doc, lines 1–35) is the one place that answers "where does a new child of kind K go?":

1. **Cancel Log** — first wherever a Cancel Log exists.
2. **Managed links** — `DEPENDS ON`, `BLOCKS`, `SUB-PROJECTS`, `LINKS`, `LINKED FROM`.
3. **Reqs** — each req moves with its whole subtree.
4. **Authored** — loose notes and nested `#task` subtasks, authored order.
5. **Drawers** — `NOTES` first, then others in authored order.
6. **Logs** — `SCHEDULE`, `WORK`, `ROTTEN`, existing relative order.

Key rules (`docs/task-requirements.md` §3–§3.4):

- `insertion_offset(contents, task, kind)` returns the slot (line index, byte offset, indentation) per `ChildKind` (`cancel-log`, `managed-link`, `req`, `authored`, `drawer`, `notes-drawer`, `log`). `note_home()` answers `loose` vs `notes` vs `new-notes`.
- `layout_violations` reports `out-of-zone`, `notes-not-first`, `note-outside-notes`.
- `plan_tidy()` is the pure per-open-task repair; `bob task tidy [ROUTE...]` (`src/native/task_tidy/mod.rs`, `command.rs`) is the explicit on-request repair. "Nothing else ever reorders a block: no writer, no `bob task reconcile`, and no background pass." (§3.4).
- Writers named: `drop_req`, `restore_req`, `toggle_note_req` (Ctrl+]), `insert_reqs`, `canonicalize_new_req_block`, `ensure_drawer`, plus link writers (`blocks_insert_slot`, `relation_insert_slot`, Depends-On first-child-except-after-Cancel-Log) and log appenders.
- `NOTES` rule: req-owning task keeps notes in `NOTES` (or `## Notes` section on a `^prj` owner, Title Case when created, column-zero bullets); `notes_drawer_birth = with_first_note`; first-req scoop files loose direct notes in the same write; later Bob-written notes file there; zero-req tasks keep today's tail slot and may interleave notes/drawers.
- Shared RL/RW vectors in `tests/fixtures/task_reqs/` are copied byte-for-byte by the Obsidian twin (module doc line 33–34). The twin covers req recognition/rendering — I found no JS twin for `insertion_offset` / `note_home` / `plan_tidy`.

### 2.2 What `o` and `Ctrl+Shift+O` do today (Obsidian)

- Vim `o` is native CodeMirror Vim open-line-below (insert mode on a new line). It knows nothing about tasks.
- `Ctrl+Shift+O` is `task-status-cycler:open-child-bullet-line-below` (`~/bob/.obsidian/hotkeys.json`; registered in `plugins/task-status-cycler/src/110-plugin-lifecycle.js:43-48` with `editorCheckCallback → handleOpenChildBulletLineCommand(checking, editor, view, "below")` in `150-plugin-commands.js:165-185`). The capture-phase fallback in `150-plugin-commands.js:282-304` matches exactly `Ctrl+Shift+o` and returns `"below"` (no shifted "above" variant). `open-child-bullet-line-above` exists as a command but has no hotkey.
- Both funnel to `handleVimOpenChildBulletLineBelow/Above(cm)` (`140-plugin-vim.js:825-880`), which uses `getChildBulletOpenLinePrefix(lineText)` (`010-core.js:116-118`): `${getLineIndentation(lineText)}${CHILD_BULLET_INDENT_UNIT}- ` — always a plain `- ` bullet one Tab-indent deeper, never continuing a task, never consulting zones, drawers, reqs, or `NOTES`. It inserts at `cursor.line` EOL (`replaceRange("\n" + childPrefix, {line, ch: lineText.length})`), so on a task headline it creates a first child bullet, not a sibling task, and on any task child it appends at cursor rather than at the zone-correct slot.

So today both gestures are structure-blind by design (the comment at `010-core.js:111-115` says so explicitly).

### 2.3 What `bob task reconcile` actually rewrites (why the goal is misframed)

`src/native/task_status_hooks/mod.rs:38` (`COMMAND_NAME = "bob task reconcile"`), `build_cli()` long_about (lines 87–120), plus `sync.rs`, `reconcile.rs`, `settle.rs`, `coalesce.rs`, `structure.rs`, `compose.rs`:

- Ledger-driven lane sync (Next `[*]` / In Progress `[/]` from open Pomodoro entries; never lowers; unlink never lowers; daily-note Next reset unless recent).
- Depends-On R1–R10 reconciliation (`DEPENDS ON` line ↔ `[dependsOn::]` / `[id::]` fields; `reconcile/fields.rs:28` uses `projects::edits::task_metadata_insertion_offset`), Blocked `[?]` derivation (open `dependsOn`, future `scheduled`, project `^prj` cascade with `#prj_is_blocked`, `[unblocked::]` recovery writes).
- Managed projections that never add/remove task lines (`sync.rs:658,688` comments): `BLOCKS`, `LINKED FROM`.
- Pomodoro coalescing (`coalesce.rs`), consumption (`structure::apply_blocked_consumption`), close settle.

What it explicitly does **not** do: zone reordering. `docs/task-requirements.md` §3.4: "Nothing else ever reorders a block: no writer, no `bob task reconcile`, and no background pass." `grep` for `plan_tidy|insertion_offset|note_home|layout_violation` under `src/native/task_status_hooks/` returns nothing (only the unrelated `reconcile/fields.rs` metadata-offset hit). Structure drift is `bob task tidy`'s job.

Consequence: making notes/drawers/reqs zone-correct will make `bob task tidy` report less, not `bob task reconcile`. Only managed-link-zone correctness (Depends-On placement, `BLOCKS`/`LINKS`/`LINKED FROM` placement, `[dependsOn::]`/`[id::]` canonicalization) reduces `reconcile` writes. The task's success metric needs to name both.

### 2.4 Capture-panel operations are already mostly compliant

`bob capture`, `bob capture --pull-in`, successor/offer cards, `task_move`, `task_split`, `task_merge`, and Mac draft flows go through the Rust writers (`task_block_layout::writers`, `capture/*`, `task_complete/*`), which already call `insertion_offset`/`note_home` and run the first-req scoop (capture §3.3: "Capture uses `insert_reqs` … all requirement groups are inserted in one write before its notes are planned, so the first-req scoop sees only loose notes already on the task"). The residual capture risk is preview-vs-apply skew (capture dry-run previews the canonical requirement block vs authored order — cf. open bead `bob-cli-po`) and the `^prj` `## Notes` home, not zone ignorance. The gap is Obsidian keymaps that bypass Rust entirely (in-editor `replaceRange` writes).

## 3. Critique — is this a good idea?

**Yes, directionally. No, not as written.**

Strengths:

- It extends the accepted contract instead of inventing a new one. Writer-rule + explicit tidy (never validity, never silent reorder, never hand-edit reshuffle) is already decided and already has `plan_tidy` idempotence ("a second run reports nothing") and one-commit guarded apply. Pushing the same rule into Obsidian editors is the obvious next step.
- The pilot (`^better-o`) is well-chosen: `o`/`Ctrl+Shift+O` are high-frequency, low-stakes insertions where zone errors compound daily (a child note landed after the logs, a req landed after `NOTES`, a loose note on a req-owning task that should have been filed).
- The `NOTES`-drawer clause correctly anticipates the req-owning-task invariant; without it every `o` on a req-owning task reintroduces `note-outside-notes` violations that only `tidy` can fix.

Problems with the plan as written:

1. **"All ops" is unbuildable.** No inventory exists. "All Obsidian keymaps and capture panel operations" spans at least: task-status-cycler (cycle, toggles, `open-child-bullet`, Pomodoro toggle, counted cycle), bob-navigation-hotkeys (move `Ctrl+Shift+M`, split `Ctrl+Shift+T`, Task Card stages incl. Depends-on/`⇧B`/Blocks/`⇧L`, relation pickers, successor offers, fresh/stamp gestures `Alt+F`/`Ctrl+Alt+F`, `Ctrl+Enter` close, `Alt+N` lane ops, Pomodoro move/rename), bob-ledger-tools (freshness footer, ready/plan writes, relation/block chips), bob-project-tasks, capture-complete/successor/pull-in cards, and every Mac draft/preview path. A blanket requirement guarantees partial compliance and untestable "done". It must become an enumerated writer inventory with per-op before/after vectors.
2. **The success metric measures the wrong command.** As §2.3 shows, `reconcile` does not tidy. If the team builds exactly what is asked and then measures `reconcile` write volume after a GTD review, they will conclude it failed even when every insertion is zone-perfect — because `reconcile` will still write lane/Blocked/Depends-On/unblocked/coalesce updates, which are its job. The metric must split: (a) `tidy --dry-run` cleanliness (structure), (b) `reconcile --dry-run` managed-link/field cleanliness (structure-adjacent), (c) full `reconcile` write volume (status, out of scope for this work).
3. **`o` as specified splits task blocks.** "Create new task below current one when task headline is selected" read literally means insert a sibling task line immediately after the headline line — inside the task's own child block. The correct sibling slot is after the whole task block (`bullet_block_end` / `block_last_line`), not `cursor.line + 1`. Similarly "both should respect ordering" is ambiguous between (i) new-child insertion slot and (ii) new-sibling placement relative to zones. Both need the slot table, but they are different slots (`authored`/`req`/`drawer` child slot vs next-sibling-of-task slot that preserves the parent zone).
4. **`Ctrl+Shift+O` semantics need a decision, not just compliance.** Today it is "plain child bullet, always". The request implies it should become context-aware (task → task-aware child? req → req? drawer → drawer row? log → refuse?). Without a per-context table it will either surprise (suddenly creates tasks) or stay useless (still plain `- ` but zone-placed — which zone? `authored`? `NOTES`?). The vim `o` vs `O` (below/above) asymmetry also needs preserving: there is currently no shifted "above" hotkey, and `getChildBulletKeydownDirection` hardcodes `"below"`.
5. **Hand-edit freedom is load-bearing.** The contract says hand edits are never reshuffled and `tidy` is on-request. An "all ops respect structure" push can easily slide into live-reordering or caret-jumping normalization. Every Obsidian writer must stay a single-undo, caret-preserving, previewed write that inserts into the right zone but never moves existing siblings.
6. **`bob-cli-ph` collision.** True-case drawers change the bytes every writer emits (`NOTES` vs `Notes`, `ensure_drawer`, catalog casing, `## Notes` vs `## NOTES`). Building `NOTES`-drawer logic in Obsidian against the old ALL-CAPS bytes will be redone by `ph.7`/`ph.8`. The task already flags this ("you might want to leave notes on that bead") — I would make it a hard sequencing gate, not a suggestion.

## 4. Alternatives considered

- **A. Teach `reconcile` to tidy (rejected).** Tempting given the task's framing ("so reconcile updates less"), but it violates the explicit §3.4 guarantee, makes a status command rewrite notes/drawers silently, and destroys the "hand edits are never reshuffled" promise. Keep `reconcile` and `tidy` separate; let `reconcile` report tidy-dirty counts without fixing them if a combined "morning review leaves clean" signal is wanted.
- **B. Silent live normalization on every keystroke (rejected).** Would minimize drift maximally but breaks undo, caret, and the writer-rule contract; also untestable across the/vim/IME surface. Zone-correct insertion only.
- **C. One shared JS insertion library with vector parity (recommended, see §5).** Port `insertion_offset` + `note_home` + `getChildBulletOpenLinePrefix`-replacement to the existing twin pattern (RL/RW vectors model), with the same `CHILD_BULLET_INDENT_UNIT`/dominant-indent fallback and `^prj` `## Notes` home. Every Obsidian writer calls it; Rust remains the oracle for vectors. This is more work up front than patching two keymaps, but patching two keymaps without the library guarantees the next ten keymaps reintroduce the same bugs.
- **D. Do only `^better-o`, defer the inventory (viable fallback).** If capacity is tight, ship the pilot with the library (§5.1–§5.2) and convert `^all-ops-reconcile-tasks` into a tracked inventory bead (one child per writer family) rather than a single "all ops" change. The pilot already proves the pattern; the inventory then lands incrementally with per-op vectors.

## 5. Adjustments to the requirements (what I would change)

1. **Rename the goal.** "Every Bob writer inserts into the right zone; hand edits are never reshuffled; `tidy --dry-run` is clean after the morning review." Keep "`reconcile` writes less" only for the managed-link subset, measured separately.
2. **Require an op inventory before code.** Enumerate every in-scope keymap/card/capture op with its current write path (Rust writer vs in-editor `replaceRange`), its `ChildKind`, and whether it must run the first-req scoop. Suggested families: (i) managed links (Depends-On, BLOCKS, LINKS/LINKED FROM, `[dependsOn::]`/`[id::]`); (ii) reqs (`insert_reqs`, `toggle_note_req`, carry, drop/restore placement); (iii) notes/`NOTES`/drawers (incl. `^prj` section home); (iv) logs (SCHEDULE/WORK/ROTTEN append); (v) sibling-task creation (`o`); (vi) child-bullet creation (`Ctrl+Shift+O`). Out of scope until inventoried: Pomodoro section edits, non-task bullets, tag-mark rendering.
3. **Pin `o` vs `Ctrl+Shift+O` semantics explicitly:**
   - `o` (vim normal mode, task headline selected): new **sibling** `#task` below the whole task block (after `block_last_line`), same indent, with fresh `[fresh::]`/lane stamp per freshness contract, caret on the new headline, insert mode. On a non-task line: preserve today's vim `o` exactly.
   - `Ctrl+Shift+O`: new **child** in the zone-correct slot per `insertion_offset`: on a task → `authored` slot if no reqs else `NOTES` drawer (creating it only when the note lands, `with_first_note`); on a req → nested req vs note per `toggle_note_req`/`insert_reqs` rules (do not silently create reqs — plain note child unless the context is unambiguously a req flow); inside a drawer → same drawer; on a log/managed line → refuse or fall back to the enclosing task's `authored`/`NOTES` slot (never insert into a log or managed line). Preserve the "no shifted above" asymmetry or add an explicit `Ctrl+Shift+Alt+O`-above only after the below path is proven.
4. **Sequence on `bob-cli-ph`.** No Obsidian `NOTES`/drawer writer lands before `ph.6`/`ph.7`/`ph.8` (resolver + Obsidian rendering/typing + bold writers) or it will be rewritten. Leave the note the task already suggests, and add the bead as a formal blocker.
5. **Require per-op vectors + one-undo + caret tests.** Each writer gets before/after vectors in the shared style (`tests/fixtures/task_reqs/` pattern), real-Obsidian headless coverage for `o`/`Ctrl+Shift+O` (the repo already has `obsidian-task-reqs-e2e.cjs`, `obsidian-req-close-card-e2e.cjs` patterns to copy), and explicit caret/cursor assertions.
6. **Add observability, not automation.** `tidy --dry-run` summary after the morning review; optional `reconcile --dry-run` managed-link-dirty count. No auto-tidy in `reconcile`, tick, or save hooks.

## 6. Recommended solution (phased)

**Phase 0 — inventory + gates (small, unblocks everything).** Produce the writer inventory (§5.2), confirm the `o`/sibling vs `Ctrl+Shift+O`/child table with Bryan (one question, since it changes a daily-driver vim muscle), and record `bob-cli-ph` as a blocker for drawer bytes. No code.

**Phase 1 — shared insertion library (the actual fix).** Port `insertion_offset` + `note_home` (+ `block_last_line`/`bullet_block_end` sibling computation) to the JS twin with shared vectors byte-identical to Rust. Include: `ChildKind` slots, dominant-indent fallback, `NOTES`-first-among-drawers, `^prj` `## Notes` home (Title Case create, existing-spelling match, column-zero bullets, dedent by child indent unit), blank-line-with-child travel, never-after-trailing-blanks. Vectors cover: empty task, links-only, reqs+notes (scoop), `NOTES`-first violation, `^prj` home, zero-req interleave preservation.

**Phase 2 — pilot the two keymaps (`^better-o`).** Rewire `handleVimOpenChildBulletLineBelow/Above` + `getChildBulletOpenLinePrefix` call sites to the library; implement sibling-`o` vs child-`Ctrl+Shift+O` per §5.3 with first-req scoop in the same undo and `NOTES` created only when a note lands. Keep non-task `o` byte-identical to vim. Ship with vectors + headless Obsidian tests + caret tests.

**Phase 3 — managed links first (`^all-ops…` part 1, the only part that reduces `reconcile` writes).** Audit/fix Depends-On, BLOCKS, LINKS/LINKED FROM writers to `managed-link` slots (first-child-except-after-Cancel-Log for Depends-On, zone-append for others) and R1–R10 canonical form, so `reconcile` stops healing placement. This is where the "reconcile updates less" win actually lives.

**Phase 4 — remaining writers in zone order.** Reqs → notes/`NOTES`/drawers (after `ph`) → logs. Each family lands with vectors; hand edits stay untouched; `tidy` remains the backstop and the cleanliness metric.

**Explicit non-goals:** no `reconcile` structural repair; no live reordering; no auto-tidy on save/tick; no `Ctrl+Shift+O`-creates-reqs magic; no ALL-CAPS drawer bytes in new code.

## 7. Risks and open questions

- Vim-muscle risk: redefining `o` on task lines may annoy more than it helps if the sibling slot misfires on nested tasks. Mitigate with the block-end computation plus an immediate `u`-is-one-undo guarantee.
- `^prj` home complexity (section vs drawer, dedent, spelling match) is the most bug-prone slot; isolate it behind `note_home` vectors before any keymap uses it.
- Mac draft parity: the Mac editor shows real `[ ]` bytes as teal chips (`docs/task-requirements.md` §4 Mac clause); any slot change must keep the Mac preview/typing vectors (`CaptureRequirementMark*`, `CapturePullIn*`) green — coordinate per the `mac-capture-is-a-thin-client` decision.
- Metric gaming: "fewer `reconcile` writes" will also drop when vault activity drops. Report dirty-task/note counts from dry runs, not raw write bytes.

## 8. Sources checked

- `~/bob/bob.md` `^better-o`, `^all-ops-reconcile-tasks`, `^micro-tasks`, `^micro-tasks-cleanup`, `^tasks-parent-projects`.
- `sase bead read bob-cli-on`, `bob-cli-pq` (both CLOSED); `sase bead list` (open `bob-cli-ph`, `bob-cli-pl`, `bob-cli-po`, `bob-cli-pt`, `bob-cli-pu` follow-ups).
- `src/native/task_block_layout.rs`, `task_block_layout/{edit,tidy,writers}.rs`, `src/native/task_tidy/{mod,command}.rs`, `src/native/task_status_hooks/{mod,sync,reconcile/*,structure.rs,settle.rs,coalesce.rs}`, `docs/task-requirements.md` §3–§4.
- `sase/repos/linked/bob-plugins/plugins/task-status-cycler/src/{010-core,110-plugin-lifecycle,140-plugin-vim,150-plugin-commands}.js`, `~/bob/.obsidian/hotkeys.json`.
- `sase memory read decisions:task-reqs-are-met-with-their-task decisions:task-deps-are-depends-on-links`.
