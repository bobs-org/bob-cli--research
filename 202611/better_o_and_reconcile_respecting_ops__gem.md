# Research: `^better-o` and `^all-ops-reconcile-tasks`

**Date:** 2026-11-25  
**Scope:** `bob-cli` (`HEAD 5ab392a1`), `bob-plugins` (`HEAD 876782fe`), `bob-mac-capture` (`HEAD 284417d7`), and 7 days of live vault history in `~/bob` (2026-11-18 to 2026-11-25).  
**Related tasks in `~/bob/bob.md`:**
- `^better-o`: Better `o` and `<ctrl+shift+o>` in Obsidian (`bob.md:82-87`, context: closed `bob-cli-on`, closed `bob-cli-pq`, in-progress `bob-cli-ph`).
- `^all-ops-reconcile-tasks`: Make all Obsidian keymaps and capture panel operations respect `bob task reconcile` structure (`bob.md:66-68`, linked as `starts after [[#^better-o]]`).

---

## 1. Executive Summary & Verdict

### Is this a good idea?

**Yes — both tasks target real, measurable friction, not cosmetic polish.** However, inspecting the codebases and 7 days of live vault git history (`~/bob`) reveals that **both task descriptions hide important traps**, and implementing them literally as worded would create UX regressions in Obsidian while missing two concrete bugs that together cause ~15% of all reconcile churn.

| Task | Verdict | Core Finding |
| --- | --- | --- |
| **`^better-o`** | **Strong yes (bug fix + ergonomics), with 5 UX/scope adjustments** | Current `o` literally **slices a task's children off** onto a malformed `- [ ] ` bullet (missing `#task` and `[created::]`), and `Ctrl+Shift+O` inserts raw child bullets **above** `Cancel Log`, `Managed Links`, and `Reqs`, violating `task_block_layout`. However, jumping straight into `**Notes**` on req-owning tasks creates a discoverability/ergonomics gap for adding new reqs or new drawers, and `o` inside `### Blocked` / `### Next & In Progress` / `### Done & Canceled` (or on `^prj`) needs explicit rules. It also directly overlaps in-progress **`bob-cli-ph.7`** (`obsidian-drawers`). |
| **`^all-ops-reconcile-tasks`** | **Right goal, wrong abstraction if taken literally — narrow & split** | In 7 days of real vault history (208 reconcile commits, 529 `.md` file rewrites), **75.2% of all file rewrites** (and **87.3% of non-midnight-wake rewrites**) come from just **three concrete causes**: (1) intra-note `task_status_groups` + badge counts (**60.5% purely grouping/badges; 86.8% touch badges**), (2) Obsidian Tasks recurring-task spawns leaving `[ ]` instead of `[?]` (**100% of `[ ]`→`[?]` flips**), and (3) a **live cross-note editor-reuse bug in `bob-navigation-hotkeys`** (`fireDependencyHandEditMirror`) writing bogus `LINKED FROM (💬 mentions)` entries (**9.3%**). Interactive writers should NOT duplicate vault-wide/time-driven reconcile; they should own **single-note `task_status_groups` + `task_block_layout` + recurring-spawn `[?]` + bug fixes**, using a **two-tier Obsidian regrouping UX policy** so tasks never teleport out from under a user mid-keystroke. |

### What I would do differently from the current plan

1. **Decouple the structural layers cleanly.** Separate:
   - **Layer A — Intra-task block layout** (`task_block_layout`, enforced by `bob task tidy`): already has a byte-identical JS twin in `bob-plugins`; live vault has **0 / 598 open tasks** out of order. `^better-o` + bug `bob-cli-pn` close the last gaps.
   - **Layer B — Intra-note status grouping & badge rows** (`task_status_groups`, enforced by `bob task reconcile` / `reroll` / `archive`): **the #1 source of reconcile churn (86.8% of rewritten files)**, yet **zero** Obsidian plugins and **none** of `bob capture` / `task move` / `task split` / `task merge` call it today.
   - **Layer C — Vault-wide & time-driven reconcile** (`bob task reconcile`): midnight `[?]`→`[ ]` + `[unblocked::]` wakes, `#prj_is_blocked` cascades, cross-vault hand-edit healing, and Pomodoro ledger coalescing. Keep Layer C exclusively in `bob task reconcile`.
2. **Do not make `^all-ops-reconcile-tasks` wait on `^better-o` / `bob-cli-ph`.** The `starts after [[#^better-o]]` link unnecessarily serializes three huge, completely orthogonal wins: (a) fixing the live `fireDependencyHandEditMirror` mention-corruption bug, (b) adding a single-choke-point `task_status_groups::transform` post-pass to `bob capture` (`CaptureBatchPlanner`) + `task move`/`split`/`merge`, and (c) shipping the Rust-pinned `task-status-groups-twin.js` in `bob-plugins`. Only `^better-o` itself needs to sequence with `bob-cli-ph.7`.
3. **Do not eagerly teleport tasks in Obsidian on every single status-cycle tap.** Use a **two-tier Obsidian regrouping policy**: atomic immediate regrouping on discrete commits (`]s` review answers, modal commits, moves, link writes, `Ctrl+Shift+]`, `o` task creation) vs. **cycle-settled regrouping** (~500 ms idle or immediate flush on cursor-leave / note-leave / command) for rapid multi-tap `Alt+]` / `Alt+[` cycling, plus a post-Tasks settle pass for `Ctrl+Enter` recurring tasks.

---

## 2. Empirical Baseline: Where `bob task reconcile` Churn Actually Comes From

Before designing any solution, I ran two live vault diagnostics and analyzed 7 full days of git history in `~/bob` (2026-11-18 through 2026-11-25: 1,865 commits total).

### 2.1 Live Vault Structural Health

- **`bob task tidy --bob-dir ~/bob`:** `✓ task blocks are tidy: 598 open tasks in 5817 notes scanned, 0 tidied`. Intra-task layout drift (`task_block_layout`) is **zero** in steady state because `bob-cli` and `bob-plugins` already share the Rust-pinned `task-block-layout-twin.js`.
- **`bob task reconcile --dry-run --bob-dir ~/bob`:** `already in sync, no changes` (reconcile runs every 15 minutes via `bob tick`, `src/native/tick/catalog.rs:162`).

### 2.2 7-Day Reconcile Commit Autopsy (`~/bob`, Nov 18–25, 2026)

Across **208 reconcile commits**, `bob task reconcile` rewrote **529 `.md` files** (~30 commits / ~75 file rewrites per day). Canceling identical moved lines within each per-file diff isolates the *true* cause of every single file rewrite:

| Category (non-mutually-exclusive per file) | File Rewrites (of 529) | Share | Owned By |
| --- | ---: | ---: | --- |
| `badge_row` updated (`⚪ · 🔵 · 🔴 · 🟢`) | 459 | **86.8%** | `task_status_groups` (Layer B) |
| `task_relocated_between_groups` (`Done`/`Next`/`Blocked`/`Intake`) | 253 | **47.8%** | `task_status_groups` (Layer B) |
| `group_heading` added/removed (`### Next & In Progress`, etc.) | 52 | **9.8%** | `task_status_groups` (Layer B) |
| `true_midnight_schedule_wake` (`[?]` → `[ ]`, date arrived) | 73 | **13.8%** | Legitimate scheduled reconcile (Layer C) |
| `true_linked_from_mention_changed` (stripping bogus mentions!) | 49 | **9.3%** | **Live bug in `bob-navigation-hotkeys`** |
| `other_non_task_edit` (daily Pomodoro ledger maintenance, etc.) | 46 | **8.7%** | Pomodoro ledger / daily notes (Layer C) |
| `true_recurring_spawn_to_blocked` (`[ ]` → `[?]` on spawned chores) | 30 | **5.7%** | **Obsidian Tasks `Ctrl+Enter` gap** |
| `true_dependsOn_field_projected` / `BLOCKS` / `id` / `LINKS` | 24 (combined) | **4.5%** | Hand-edited dependency/link healing (Layer C) |

Cumulative attribution of **complete** file rewrites (files that reconcile would **not have touched at all**):

| If interactive writers fix... | Eliminated File Rewrites | % of All 529 | % of Non-Midnight-Wake (456) |
| --- | ---: | ---: | ---: |
| 1. Intra-note `task_status_groups` + badges only | **320** | **60.5%** | **70.2%** |
| 2. `+` Recurring-task spawn `[ ]` → `[?]` fixup (98/98 `[ ]`→`[?]` flips) | **350** | **66.2%** | **76.8%** |
| 3. `+` Live `fireDependencyHandEditMirror` mention-bug fix | **398** | **75.2%** | **87.3%** |

Concrete morning-review evidence from today (2026-11-25):
- Commits `595284a2d` (06:10), `fb3d0a357` (06:17), `718fc075f` (06:26), `06b983090`, and `a71c47f89` rewrote **26+ files** after Bryan's morning review almost exclusively to relocate `[x]`/`[-]`/`[?]`/`[*]` tasks into their status groups, update badge counts, flip recurring chores in `gtd_daily.md`, and strip bogus cross-note mentions.
- Even adding the `^all-ops-reconcile-tasks` task itself triggered commit `10def3566` solely to increment `⚪ 5 open` → `⚪ 6 open` in `bob.md`.

### 2.3 Two Live Bugs Discovered in the Audit

#### Bug 1 (High-impact): Cross-note editor-reuse corruption in `fireDependencyHandEditMirror`

In `bob-plugins/plugins/bob-navigation-hotkeys/src/600-plugin-dependency-mirror.js:906-966`:

1. Editing a task during `]s` morning review schedules a debounced timer holding `snapshot = { editor, parentPath, oldContent, ... }`.
2. When `]s` auto-advances to the next note in the **same `MarkdownView`**, Obsidian reuses the same `editor` object for the newly opened file.
3. When `fireDependencyHandEditMirror(snapshot)` fires, it **never checks whether the view owning `snapshot.editor` still displays `snapshot.parentPath`**. It passes `snapshot.editor` (now holding Note B's text!) with `snapshot.parentPath` (Note A's path!) into `mirrorDependencyHandEdit` and `mirrorMentionHandEdit`.
4. `mirrorMentionHandEdit` scans Note B's wikilink mentions and attributes them to Note A, writing **phantom `LINKED FROM` mentions** into target notes — e.g., `[[sase#^ranked-task-links]] (💬 mentions)` and `[[dev#^foo]] (💬 mentions)` in `bob.md`, `[[bob#^email-dan-eod]] (💬 mentions)` in `job.md`, and `[[bob#^wait-for-load]] (💬 mentions)` in `sase.md` (observed directly in commits `435132736` → `fb3d0a357` and `718fc075f`).
5. Worse, the `finally` block (`600-plugin-dependency-mirror.js:960-965`) executes `this.dependencyMirrorByPath.set(snapshot.parentPath, snapshot.editor.getValue())`, **poisoning Note A's cached baseline with Note B's contents** for subsequent edits.

**Fix:** Capture the owning `MarkdownView` (or resolve `viewForEditor`) and abort if `view.file?.path !== snapshot.parentPath`; additionally, flush or cancel `pendingDependencyMirror` on `active-leaf-change` / `file-open` before the editor swaps buffers.

#### Bug 2 (Medium-impact): Obsidian Tasks `Ctrl+Enter` spawns recurring tasks as `[ ]` despite future `[scheduled::]`

In `bob-plugins/plugins/task-status-cycler/src/180-plugin-editor-edits.js:368-399`, `applyTasksCommandAndMaybeStamp` delegates `#task` completion to Obsidian Tasks (`tasks:set-status-symbol-to-x`). When completing a recurring chore (especially `gtd_daily.md` PRE/POST items), Obsidian Tasks spawns the next occurrence with `- [ ] #task ... [scheduled:: tomorrow]`, even though Bob's invariant requires `[?]` for any open task with a future `[scheduled::]` date. Across 7 days, **98 of 98 (100%)** `[ ]` → `[?]` flips by `bob task reconcile` were recurring-task spawns!

**Fix:** Immediately after `applyTasksCommandAndMaybeStamp` returns with `lineDelta > 0`, inspect the newly inserted line(s) adjacent to `taskStatus.line`; if a spawned recurring `#task` has status `[ ]` and a `[scheduled:: YYYY-MM-DD]` strictly greater than today (using local date), flip its checkbox `[ ]` → `[?]` in place before finalizing/regrouping.

*(Also noted in the vault diff: two commits `58b7dceff` and `145d87deb` showed `- [ ] #task 🧱 **BLOCKS:** [[#^v1-draft]] [created::2026-11-22]` — a `BLOCKS:` child line accidentally promoted into a `#task`, likely via `Ctrl+Shift+]` on a managed link line. Worth adding a managed-line refusal guard to `Ctrl+Shift+]` promotion alongside `^better-o`!)*

---

## 3. Critique of Requirements & Proposed Adjustments

Below are every modification I recommend to the requirements in `bob.md`, called out explicitly.

| # | Target | Original Requirement / Assumption | Problem Found | Recommended Adjustment |
| --- | --- | --- | --- | --- |
| **A1** | `^all-ops-reconcile-tasks` | *"Make all Obsidian keymaps and capture panel operations respect `bob task reconcile` structure"* | Conflates 3 distinct layers (intra-task `task_block_layout`, intra-note `task_status_groups`, vault-wide/time-driven reconcile). Re-implementing midnight wakes, `#prj_is_blocked` cascades, or Pomodoro coalescing in Obsidian would add huge complexity for <5% remaining churn. | **Redefine scope explicitly as 4 deliverables:** (1) intra-note `task_status_groups` + badge counts in all `bob-cli` task writers (`capture`, `move`, `split`, `merge`, `gmail`, `ref`, `gkeep`) and Obsidian plugins; (2) intra-task `task_block_layout` parity (`^better-o` + `bob-cli-pn`); (3) recurring-spawn `[ ]`→`[?]` fixup; (4) `fireDependencyHandEditMirror` cross-note race fix. Keep time-based/cross-vault rules in `bob task reconcile`. |
| **A2** | `^all-ops-reconcile-tasks` | Implicit assumption that every Obsidian keymap regroups immediately in place | Immediate regrouping on `Alt+]` / `Alt+[` teleports the task 50–200 lines down into `### Next & In Progress` or `### Blocked` on the *first* tap — breaking rapid double-tap cycling (`[ ]`→`[*]`→`[/]`), mis-tap recovery, and visual continuity. | **Adopt a two-tier Obsidian regrouping policy:** immediate atomic regrouping on discrete commits (`]s` review answers, Task Card / Decay Card / `Alt+P`, `Ctrl+Shift+M`, `Ctrl+Shift+Enter`, `Ctrl+Shift+]`, `Alt+N`, `Alt+X`, `o` new task) vs. **cycle-settled regrouping** (~500 ms debounce + immediate flush on cursor-leave / note-leave / next command) for `Alt+]` / `Alt+[`. |
| **A3** | `^all-ops-reconcile-tasks` | `starts after [[#^better-o]]` | Blocks high-ROI, zero-conflict `bob-cli` and bugfix work behind `^better-o` and in-progress `bob-cli-ph`. | **Split the dependency:** Keep `^better-o` sequenced after `bob-cli-ph.7`, and run the independent tracks (`fireDependencyHandEditMirror` bugfix, `bob capture` / CLI `task_status_groups` pass, and the `task-status-groups-twin.js` library) **in parallel or ahead of `^better-o`**. |
| **A4** | `^better-o` | *"`o` should create new task below current one when task headline is selected!"* | Three edge cases break this if implemented literally: (1) pressing `o` on a task inside `### Blocked`, `### Next & In Progress`, or `### Done & Canceled` would drop a brand-new `[ ] #task` inside the wrong status group; (2) pressing `o` on `^prj` above `# Title` would create an orphan task above the H1; (3) hitting `<Esc>` without typing leaves a ghost `- [ ] #task  [created::YYYY-MM-DD]` and increments `⚪ open`. | **Refine `o` semantics:** (1) On a `#task` headline in intake (or ungrouped note), insert after the current task's **entire subtree** as `- [ ] #task | [created::YYYY-MM-DD]` and increment the badge row atomically; (2) on a `#task` inside a status group (`Next & In Progress` / `Blocked` / `Done & Canceled`), place the new `[ ] #task` at the **end of the containing section's intake** (recording a `<C-o>` jump); (3) on `^prj`, jump to `## Tasks` intake (or refuse with a clear notice); (4) prune empty task scaffold on insert-exit without typing (and restore badge count). Also define **`O`** (open above) symmetrically. |
| **A5** | `^better-o` | *"Both should respect `links < reqs < drawers < logs`! A task with one or more reqs should list notes in an explicit notes drawer"* | Two UX tensions: (1) Once `Ctrl+Shift+O` on a req-owning task jumps into `**Notes**` (2 tabs deep), there is no one-keystroke path from the task headline to add a **new req** or a **new custom drawer**; (2) on a zero-req task that already has drawers, `Ctrl+Shift+O` lands at `tail` (after drawers), and if Bryan then types `- [` (`199a-req-typing.js` expands to `- [ ] `), the new req lands **after drawers** (violating `reqs < drawers`!) and leaves existing loose notes un-scooped! | **Resolve both cleanly:** (1) On a req-owning task, `Ctrl+Shift+O` enters/creates `**Notes**`, while **`o` on any existing req** inserts a sibling `- [ ] ` req after that req's subtree (respecting `links < reqs`), and **`ph.7`'s Toggle Drawer** or typing `- **Title**` / `*` after `o` on a drawer header adds a sibling drawer; (2) upgrade `199a-req-typing.js` (or `o`/`Ctrl+Shift+O` insert-exit) so expanding `- [` on a direct child of a task re-slots the new req into the reqs zone (`links < reqs < drawers`) and scoops any loose authored notes into `**Notes**` when the task transitions from 0 → 1 req; (3) auto-prune a freshly materialized empty `**Notes**` drawer if Bryan exits insert mode without typing. |
| **A6** | `^better-o` | *"see `bob-cli-ph` for recent changes to drawers which are ongoing--so you might want to leave notes on that bead"* | `bob-cli-ph.7` (`obsidian-drawers`, currently `IN_PROGRESS`) is modifying `task-status-cycler`'s drawer helpers, `- **Notes**` constant, `*` → `**|**` assist, and Smart Enter right now. | **Leave a coordination note on `bob-cli-ph`** (exact text in Section 6.3) asking `ph.7` to keep `taskBlockEnsureNotesDrawer` and `taskBlockInsertSlot` exported as reusable pure planners in `task-block-layout-twin.js` (returning `{ content, cursorLine, cursorCh, createdNotesDrawer }`) and confirming `Ctrl+Shift+O` will compose cleanly with `ph.7`'s `*` assist and Smart Enter. |
| **A7** | `^all-ops-reconcile-tasks` | Missing CLI gaps (`bob task move`, `split`, `merge`, `bob-cli-pn`, `gmail`, `ref`, `gkeep`) | Even after fixing Obsidian and `bob capture`, standalone `bob task move`, `bob task split` (including open bug `bob-cli-pn` where plain Task Split puts `LINKED FROM` after moved children), `bob task merge`, `bob gmail sync`, `bob ref create`, and `bob gkeep pull` still leave ungrouped tasks / stale badges. | **Include all `bob-cli` task mutators + `bob-cli-pn`** in the shared Rust post-write grouping helper. |

---

## 4. Detailed Design for Part 1: `^better-o`

### 4.1 What Is Broken Today

In `bob-plugins/plugins/task-status-cycler/src/010-core.js:96-118` and `140-plugin-vim.js:768-880`:

- `handleVimOpenLineBelow` (`o`): inserts `\n${indent}- [ ] ` at `cursor.line + 1` (ignoring children, `#task`, `[created::]`, task zones, and status groups).
  - **Bug 1 (Subtree slicing):** Pressing `o` on a task headline that has `DEPENDS ON:`, reqs, drawers, notes, or logs inserts `- [ ] ` *between* the headline and its children, silently stealing the entire subtree onto the new empty bullet!
  - **Bug 2 (Malformed task):** Emits `- [ ] ` instead of `- [ ] #task  [created::YYYY-MM-DD]` (unlike `Ctrl+Shift+]` in `030-task-toggles.js:251-320`).
  - **Bug 3 (Managed-line & drawer slicing):** Pressing `o` on a req with sub-notes, a drawer header, or a managed link/log header slices its children off or emits a bare `- ` inside a forbidden zone.
- `handleVimOpenChildBulletLineBelow` (`Ctrl+Shift+O`): inserts `\n${indent}\t- ` at `cursor.line + 1`.
  - **Bug 4 (Zone violation):** Always lands *above* `Cancel Log`, `Managed Links`, and `Reqs`, violating `Cancel Log < Managed Links < Reqs < Authored < Drawers < Logs`.
  - **Bug 5 (Req-owner invariant violation):** On a task with ≥1 reqs, inserts a loose note outside `**Notes**` instead of entering/creating `**Notes**`.
- Also note: `handleVimOpenLineAbove` (`O`, `140-plugin-vim.js:797-823`) and `handleVimOpenChildBulletLineAbove` (`Ctrl+Shift+O` variant if bound, `140-plugin-vim.js:854-880`) have the exact same raw-prefix logic and should be audited alongside `o` and `Ctrl+Shift+O`.

### 4.2 Reuse What Already Exists

`task-status-cycler` **already ships** the Rust-pinned `task_block_layout` JS twin (`196-task-block-layout-twin.js`, copied identically in `bob-navigation-hotkeys/src/696-task-block-layout-twin.js`) and `task-reqs-twin.js` (`195-task-reqs-twin.js`) and `task-drawers-twin.js` (`193a-task-drawers-twin.js`)!

Specifically, `task_block_layout` already defines:
- Full task-block parsing (`taskBlockParse`): 6 zones in exact canonical order:
  1. `cancel_log` (`CANCEL LOG` / `**Cancel Log**`)
  2. `managed_link` (`DEPENDS ON`, `BLOCKS`, `SUB-PROJECTS`, `LINKS`, `LINKED FROM`)
  3. `req` (requirement checkboxes)
  4. `authored` (loose notes, nested `#task`)
  5. `drawer` (named drawers; `Notes` / `NOTES` first on req-owners)
  6. `managed_log` (`SCHEDULE LOG`, `WORK LOG`, `ROTTEN LOG`)
- Zero-req tasks allow `authored` and `drawer` to interleave (rank 3), with new loose notes landing at **`tail`** (after the last authored/drawer child, immediately before the first managed log).
- Req-owning tasks (≥1 reqs) route notes into **`**Notes**`** (currently `NOTES`, transitioning to bold `- **Notes**` in `bob-cli-ph.4`/`ph.7`; on `^prj`, notes go to H2 `## Notes`).
- `taskBlockInsertNote` / `taskBlockEnsureNotesDrawer` already compute exact insertion lines using the same rules as `bob capture` and `bob task tidy`.

### 4.3 Complete Cursor-Context Decision Matrix (`o`, `O`, `Ctrl+Shift+O`)

Every edit below is computed by a **pure planner function** in `task-status-cycler` (testable without Obsidian, just like `055-obsidian-task-toggle-ranges.js` and `196-task-block-layout-twin.js`) and applied in **one atomic CM6 transaction** (so `u` undoes everything cleanly).

| # | Cursor Context | `o` (Open Below) | `O` (Open Above) | `Ctrl+Shift+O` (Open Child Below) |
| --- | --- | --- | --- | --- |
| **1** | **Root `#task` headline** in `## Tasks` intake (or ungrouped note) | Skip entire task subtree (including all links, reqs, drawers, logs). Insert `- [ ] #task  [created::YYYY-MM-DD]` at `subtreeEnd + 1`, cursor between `#task ` and ` [created::...]`, enter Insert mode. If note is grouping-eligible, increment `⚪ open` badge in the same transaction. | Insert `- [ ] #task  [created::YYYY-MM-DD]` immediately **above** this task headline (still in intake), cursor after `#task `, increment `⚪ open` badge atomically. | **If 0 reqs:** insert `\t- ` at canonical `tail` slot (after links/authored/drawers, before first managed log). **If ≥1 reqs:** if `**Notes**` drawer exists, insert `\t\t- ` at end of `**Notes**` children; if not, materialize `\t- **Notes**` in the canonical first-drawer slot (immediately after last req) + `\t\t- ` child, cursor on the child, and arm empty-drawer auto-prune (see §4.4). |
| **2** | **Root `#task` headline** inside `### Next & In Progress`, `### Blocked`, or `### Done & Canceled` | **Do NOT insert `[ ] #task` inside the status group.** Record a `<C-o>` jump, insert `- [ ] #task  [created::YYYY-MM-DD]` at the **end of the containing section's intake** (right above the first status group heading), increment `⚪ open` atomically, move cursor there, enter Insert mode. *(Subtle notice only if jumped off-screen.)* | Same as `o` for status-group tasks (a brand-new `[ ] #task` belongs in intake, never inside `### Blocked` or `### Done & Canceled`). Record `<C-o>` jump; insert at top/end of intake (recommend end of intake for consistency). | **Identical to #1** — opens child inside this task's canonical slot (`tail` or `**Notes**`), keeping the task right where it is in its status group. |
| **3** | **`^prj` headline** (project task at top of project note, above `# Title`) | Jump into `## Tasks` intake (end of intake, creating `- [ ] #task  [created::YYYY-MM-DD]` + badge update, recording `<C-o>` jump), since sibling root tasks never sit above `# Title`. | Plain fallback (or refuse with notice — nothing belongs above `^prj` except frontmatter). | Per `docs/task-drawers.md` & `decisions:capture-bullets-mirror-the-task-block`, `^prj` notes live under H2 `## Notes`, NOT a child `**Notes**` drawer! If `^prj` has ≥1 reqs, jump/append `- ` under `## Notes` (or create `## Notes` if absent); if 0 reqs, insert `\t- ` at canonical `tail` slot (before logs) or under `## Notes` (follow `task_block_layout` `^prj` rules!). |
| **4** | **Nested `#task`** (child task inside a parent task) | Skip nested task's own subtree; insert sibling nested `- [ ] #task  [created::YYYY-MM-DD]` at the same indent inside the parent's `authored` zone (before drawers/logs). | Insert sibling nested `- [ ] #task  [created::YYYY-MM-DD]` immediately above this nested task at same indent. | Same zone-aware child insertion scoped to the **nested** task's own block (`tail` if 0 reqs, `**Notes**` if ≥1 reqs). |
| **5** | **Requirement line** (`- [ ] ...` / `- [x] ...` direct child of a task) | Skip this req's entire subtree (any sub-notes or sub-reqs); insert a sibling `- [ ] ` at the same indent immediately after it (stays cleanly inside the `reqs` zone!). | Insert sibling `- [ ] ` immediately above this req at same indent (stays in `reqs` zone, never above `Managed Links`!). | Insert a plain child note (`indent + \t- `) at the end of this req's existing children (a note attached to this specific req). |
| **6** | **Managed link line** (`DEPENDS ON`, `BLOCKS`, `SUB-PROJECTS`, `LINKS`, `LINKED FROM`, `CANCEL LOG`) | **Do NOT insert a raw `- ` inside the managed-link zone.** Treat as advancing to the owning task's canonical child-insert slot (equivalent to `Ctrl+Shift+O` on the owning task: `tail` on 0-req tasks, `**Notes**` on req-owning tasks — or if the user wants a req, they can trigger req creation). | Refuse / step out of managed-link zone (never insert authored bullets above `CANCEL LOG` or between `DEPENDS ON` and `BLOCKS`). | Same as `o` (managed link lines never take user child bullets — redirect to the owning task's canonical note slot!). |
| **7** | **Drawer header** (`- **Notes**`, `- **Spec**`, legacy `- NOTES`, etc.) | **Two defensible behaviors — pick explicitly:** **Recommended:** skip the drawer's entire subtree and insert a sibling bullet at drawer indent (`\t- `) **inside the drawer zone** (before managed logs), ready for `ph.7`'s `*` → `**|**` assist to name a new drawer! *(Alternative: open first child inside the drawer — wait, that's what `Ctrl+Shift+O` and `ph.7`'s Smart Enter on `- **Title**|` ALREADY do! Keeping `o` = sibling after subtree and `Ctrl+Shift+O` = child inside drawer makes `o` vs `Ctrl+Shift+O` 100% orthogonal!)* | Insert sibling bullet at drawer indent immediately above this drawer (after reqs, inside drawer zone — never above `Reqs` or `Managed Links`). | Append `\t\t- ` at the **end** of this drawer's children (after its existing child bullets, not slicing them off!). |
| **8** | **Child note inside a drawer** | Skip this bullet's own nested children; insert sibling `- ` at same indent inside the drawer. | Insert sibling `- ` immediately above this bullet at same indent. | Skip nothing (or insert after existing grandchildren at `indent + \t- `): insert child bullet at `indent + \t- ` after this bullet's existing children. |
| **9** | **Loose authored note** on a task | Skip this bullet's own subtree; if owning task has 0 reqs, insert sibling `- ` after subtree (before logs). If owning task somehow has ≥1 reqs (transient untidy state), insert into `**Notes**`. | Insert sibling `- ` above (stays after `Links`/`Reqs`). | Insert child bullet (`indent + \t- `) at end of this bullet's existing children. |
| **10** | **Managed log header / log entry** (`SCHEDULE LOG`, `WORK LOG`, `ROTTEN LOG`) | Logs are Bob-managed and sit last (`zone 6`). Pressing `o` on a log header or entry should **NOT** append a stray bullet inside the log! Either redirect to the owning task's canonical note slot (`tail` / `**Notes**`), or insert a new sibling `#task` after the owning task's subtree? **Recommend:** redirect to the owning task's canonical note slot (`tail` / `**Notes**`) if on the log header, or fall back to plain `o` outside task blocks; never write inside managed logs. | Same safety guard — never insert inside managed logs. | Redirect to owning task's canonical note slot (never add manual child bullets under `SCHEDULE LOG` / `WORK LOG` / `ROTTEN LOG`). |
| **11** | **Pomodoro row / Task Link** under `## Pomodoros` | Existing Pomodoro behavior (never emit `#task [created::]`; on a Pomodoro heading line, keep current `- ` or plain continuation; on a Task Link bullet, insert sibling `- ` at same indent). | Same — preserve existing Pomodoro ledger behavior. | Insert child `- ` one indent deeper after existing children of this Pomodoro/Task Link (so notes under a Task Link work without slicing). |
| **12** | **Bank row** | Preserve bank-row guard (never emit `#task` or `[created::]`; plain `- [ ] ` or bank format). | Same. | Plain child bullet after existing children. |
| **13** | **Plain bullet / prose / frontmatter / fenced code block** | Existing `getOpenLineBelowPrefix` behavior (for a plain bullet with children, skipping its children is also much nicer, or preserve standard Vim `o` on plain prose/fences/frontmatter). | Existing `O` behavior. | Existing `getChildBulletOpenLinePrefix` behavior (after existing children if on a bullet). |

### 4.4 Solving the Three Hardest `^better-o` Edge Cases

#### Edge Case 1: How do you quickly add a *req* or a *new drawer* on a task?

This is the single biggest UX subtlety in `^better-o`:
- **Adding a 2nd/3rd req to a req-owning task:** Works seamlessly via **`o` on an existing req** (Matrix row #5), which skips the req's sub-notes and inserts `- [ ] ` right inside the `reqs` zone!
- **Adding a 2nd/3rd drawer to a task:** Works seamlessly via **`o` on a drawer header** (Matrix row #7), which skips the drawer's children and inserts `\t- ` right inside the `drawer` zone, where `bob-cli-ph.7`'s `*` → `**|**` typing assist lets you immediately type `*Spec` → `- **Spec**` + Enter!
- **Adding the *1st* req to a zero-req task that ALREADY has drawers (CRITICAL GAP):**
  1. Task currently has `DEPENDS ON:`, `- **Spec**`, and `SCHEDULE LOG`.
  2. Cursor is on the task headline. User presses `Ctrl+Shift+O`. Because the task has 0 reqs, `Ctrl+Shift+O` lands at `tail` — **after `- **Spec**`** and before `SCHEDULE LOG`.
  3. User types `[ ` to start a req. `199a-req-typing.js` expands `- [ ` → `- [ ] ` **in place** — leaving the brand-new req **after `- **Spec**`**, violating `reqs < drawers`! And if the task also had loose authored notes above `- **Spec**`, they are now loose notes on a req-owning task, violating `with_first_note`!
  - **Recommended solution:** Enhance `199a-req-typing.js` (`cyclerReqTypingExpansion`) so that when `- [ ` expands to `- [ ] ` on a **direct child line of a `#task`**, if that line sits *after* any authored note or drawer in the same task block, the expansion transaction **simultaneously**:
    1. Moves the newly expanded `- [ ] |` line into the canonical end-of-`reqs` slot (right after `Managed Links` / existing reqs, before authored/drawers),
    2. Scoops any existing loose authored notes of that task into `- **Notes**` (using `taskBlockTidy` / `taskBlockEnsureNotesDrawer`),
    3. Keeps the cursor at `- [ ] |` inside the moved line, with `isolateHistory` so one `u` undoes cleanly!
  - *(Fallback if Bryan wants to keep `199a-req-typing.js` minimal in v1: expose a dedicated command / chord like "Add Requirement to Task" — or `Ctrl+Shift+R` — that opens `- [ ] |` directly in the `reqs` zone and scoops loose notes. Doing it inside `199a-req-typing.js` is strictly better because you never have to remember a new keybinding!)*

#### Edge Case 2: Empty `**Notes**` drawer (or empty `#task`) if the user presses `<Esc>` immediately

- Suppose Bryan presses `Ctrl+Shift+O` on a req-owning task with no `**Notes**` drawer yet. The plugin inserts:
  ```markdown
  	- **Notes**
  		- |
  ```
- Suppose Bryan changes his mind and immediately presses `<Esc>` without typing anything.
- Per `docs/task-drawers.md` (`notes_drawer_birth = with_first_note`), `**Notes**` should only exist once there is a note inside it; leaving an empty `- **Notes**\n\t\t- ` is noise (and similarly, pressing `o` then immediate `<Esc>` would leave a blank `- [ ] #task  [created::2026-11-25]` and a bogus `+1` on `⚪ open`!).
- **Recommended solution:** Track a tiny ephemeral **open-scaffold guard** on the editor (like `armField` in `199a-req-typing.js`):
  - Armed only by our `o` / `O` / `Ctrl+Shift+O` transaction, recording `{ kind: "new-task" | "created-notes-drawer", expectedLines, preStateBadge? }`.
  - Disarmed on any non-whitespace character typed on the inserted line.
  - If Vim exits Insert mode (`vim-mode-change` to `normal`) or focus blurs while the inserted line is still strictly empty (`- [ ] #task  [created::YYYY-MM-DD]` or `\t\t- `), automatically prune the empty scaffold (and revert the `+1` badge increment if `"new-task"`) in a clean transaction!

#### Edge Case 3: Exact `[created::YYYY-MM-DD]` byte format and cursor placement

- Verified in `task-status-cycler/src/030-task-toggles.js:251`: Bob's canonical format is `[created::YYYY-MM-DD]` (no space after `::`), matching `~/bob/bob.md`.
- Insert exact line:
  ```markdown
  - [ ] #task  [created::2026-11-25]
  ```
  with **one** space after `#task` and **one** space before `[created::...]`, and place cursor at `ch = indent.length + "- [ ] #task ".length` (immediately before the space preceding `[created::...]`).
- When Bryan types `Fix parser`, the line becomes `- [ ] #task Fix parser [created::2026-11-25]` — exact canonical single-space formatting, zero trailing-space cleanup needed!

---

## 5. Detailed Design for Part 2: `^all-ops-reconcile-tasks`

### 5.1 Architectural Choice: Pure Rust-Pinned JS Twin + Centralized `bob-cli` Post-Pass

Three architectures were evaluated for keeping Obsidian and `bob capture` in sync with `task_status_groups`:

| Option | How It Works | Pros | Cons | Verdict |
| --- | --- | --- | --- | --- |
| **Option A (Recommended): Rust-pinned JS twin (`task-status-groups-twin.js`) in `bob-plugins` + centralized `bob-cli` post-pass** | Mirror `src/native/task_status_groups/` (~750 LOC core logic; pure Markdown-in → Markdown-out) as a JS twin copied across the 3 editing plugins, pinned by a shared `SG` test-vector suite exported from Rust (exact same pattern already used for `task-block-layout-twin.js`, `task-drawers-twin.js`, `task-reqs-twin.js`, `req-close-twin.js`, `mail-close-model-twin.js`). In `bob-cli`, add one post-pass in `CaptureBatchPlanner` plus a shared helper in `task move/split/merge/gmail/ref/gkeep`. | **0 ms latency** (<1 ms in-memory); **atomic single CM6 transaction** (native `u` / `Ctrl+Z` undo!); **zero editor-vs-disk races**; works on mobile/offline; matches `bob-plugins`'s proven twin architecture. | Adds one more Rust-pinned JS twin (~500–700 LOC) to maintain alongside the 8 twins already in `bob-plugins`. (Mitigated completely by `SG` parity vectors + copy-parity tests.) | **WINNER** |
| **Option B: Subprocess call to `bob task group <file>` from Obsidian** | Plugins flush editor to disk and shell out to `bob`. | Zero JS duplication. | 30–100 ms lag per keystroke; races with unsaved CM6 buffers; breaks native Undo stack; fails on iOS/Android Obsidian; requires spawning processes from inside `]s` review walks. | Reject |
| **Option C: Faster `bob tick` / vault file-watcher daemon** | Let a background daemon run `bob task reconcile` 1–2 s after every file save. | Zero plugin code. | External disk rewrites stomp active Obsidian buffers & cursor positions; creates extra git commit churn; still doesn't fix `bob capture` dry-run previews or `⌃↩ Open` jump lines. | Reject |

Why `task_status_groups` is an **ideal** candidate for a Rust-pinned JS twin:
- Look at `src/native/task_status_groups/mod.rs:1-4`: *"Pure Markdown transform that groups Tasks-section task blocks by status. This module does not read the filesystem, mutate task statuses, resolve links, or write files."*
- Its inputs are literally just `(markdownText, { globalFilter: "#task", statusTypes })` plus the 10-line eligibility check (`grouping_eligible_note`: frontmatter `[[area]]` or `[[project]]`, not a `YYYY/YYYYMMDD.md` daily note, not today's daily note — `src/native/task_status_hooks/compose.rs:228-243`).
- Its output is `{ contents, changed, groupedSections, warnings }`, and it already preserves non-task prose and safely skips malformed/ambiguous sections (`GroupingSkipCode`, 10 guards) without ever corrupting authored text.
- Better yet, we can extend the JS twin (or a thin wrapper around it) to also return **exact line-mapping** (`mapLine(oldLine) -> newLine`) using the moved block ranges — so Obsidian can follow the cursor accurately or remap `]s` walk positions in O(1)!

### 5.2 Complete Operation-by-Operation Audit

#### A. Obsidian Plugins (`bob-plugins`)

| Plugin & Operation | Hotkey / Trigger | Currently Respects `task_block_layout`? | Currently Respects `task_status_groups`? | Required Change & Grouping Tier |
| --- | --- | --- | --- | --- |
| **`task-status-cycler`**: Open below / above / child | `o`, `O`, `Ctrl+Shift+O` | **No** (slices subtrees, inserts above links/reqs) | **No** | **`^better-o`** rewrite + **Tier 1** atomic badge increment when inserting a new `#task` in an eligible note. |
| **`task-status-cycler`**: Req typing assist | `- [` + space | **Partial** (expands in place; out-of-zone if drawers exist) | N/A (sub-bullet) | Upgrade `199a-req-typing.js` to re-slot into `reqs` zone + scoop loose notes on 0→1 req transition. |
| **`task-status-cycler`**: Complete / reopen task | `Ctrl+Enter` | Yes (via `finalizeClosedTasks`) | **No** | Add **post-Tasks recurring-spawn `[ ]`→`[?]` fixup** + **Tier 1** regroup on `]s` walk / transcluded target / direct close (single follow-up settle after Obsidian Tasks finishes; record `<C-o>` jump on in-note close). |
| **`task-status-cycler`**: Cycle status fwd/back (single & counted) | `Alt+]`, `Alt+[` | Yes | **No** | **Tier 2 (Cycle-settled):** ~500 ms debounce while cursor stays on the task line; immediate flush on cursor-leave, note-leave, or another Bob command. Follows cursor if cursor is still on the moved task. |
| **`task-status-cycler`**: Promote / demote `#task` | `Ctrl+Shift+]` | Yes | **No** (moves to `## Tasks` / demotes, never updates badge or groups) | **Tier 1** atomic regroup in the same move/replace transaction + refuse promoting managed link/log lines (`BLOCKS:`, `DEPENDS ON:`, etc.). |
| **`task-status-cycler`**: Req checkbox toggle | `Ctrl+Enter` / `Alt+]` on req | Yes | N/A | None needed (req status never changes parent task's status bucket). |
| **`bob-navigation-hotkeys`**: Task Card / Priority Roll / Schedule | `Alt+P` (`390-picker-roll-write.js`) | Yes | **No** (sets `[?]` + `[scheduled::]`, leaves task in intake!) | **Tier 1** atomic regroup in `applyEditorContentTransaction` (and in `vault.modify` for link-session target notes!). |
| **`bob-navigation-hotkeys`**: Release Next/WIP → Ready | `Alt+N` (`240-cancel-and-lanes.js`) | Yes | **No** (flips `[*]`/`[/]`→`[ ]`, leaves task inside `### Next & In Progress`!) | **Tier 1** atomic regroup in the same transaction (moves task back to intake, drops empty `### Next & In Progress`, updates badges). |
| **`bob-navigation-hotkeys`**: Cancel task | `Alt+X` (`240-cancel-and-lanes.js`) | Yes | **No** (flips to `[-]`, leaves task in intake!) | **Tier 1** atomic regroup in the same transaction (moves task to `### Done & Canceled`, updates badges). |
| **`bob-navigation-hotkeys`**: Keep / Decay Card (step/cancel/stay) | `Alt+F`, `Ctrl+Alt+F` (`548-decay-card-writers.js`) | Yes | **No** (Step WIP→Next→Ready→Scheduled/Cancel changes status, never regroups!) | **Tier 1** atomic regroup in `applyFreshnessDecayCardLinePlan` and `setBulletPriorityValue`. |
| **`bob-navigation-hotkeys`**: Move task across notes | `Ctrl+Shift+M` (`250-task-move.js`) | Yes | **No** (neither source nor destination regroups!) | **Tier 1** atomic regroup on **both** source note and destination note in the same move commit. |
| **`bob-navigation-hotkeys`**: Split task | Task Split (`256-task-split-plan.js`) | **Bug (`bob-cli-pn`)** — plain split puts `LINKED FROM` after children | **No** | Fix `bob-cli-pn` (place `LINKED FROM` via `taskBlockInsertManagedLink`) + **Tier 1** atomic regroup on source/destination notes. |
| **`bob-navigation-hotkeys`**: Hand-edit dep/mention mirror | Debounced edit (`600-plugin-dependency-mirror.js`) | Yes | **No** (and **LIVE BUG**!) | **Fix active-file guard + leaf-change flush** (`600-plugin-dependency-mirror.js:913-965`) + **Tier 1** regroup if mirror flips a dependent task `[ ]`↔`[?]`. |
| **`block-id-prompt`**: Link task into Pomodoro | `Ctrl+Shift+Enter` (`140-plugin-target-plans-and-rewrites.js`) | Yes | **No** (raises `[ ]`→`[*]` in target note, leaves it in intake!) | **Tier 1** atomic regroup on target note inside `planTargetTaskUpdate` (when raising `[ ]`→`[*]`, moving into `### Next & In Progress` and updating badges!). |
| **`bob-ledger-tools`**: Pomodoro close (`=x`, etc.) | Ledger commands | Yes | Delegates or edits daily note + target notes | Any target-note status mutation (`[*]`→`[/]` or `[x]`) runs **Tier 1** regroup on eligible target notes. |

#### B. `bob-cli` & Capture Panel (`bob capture` + `bob-mac-capture`)

| Entry Point | Currently Respects `task_block_layout`? | Currently Respects `task_status_groups`? | Required Change |
| --- | --- | --- | --- |
| **`bob capture`** (ALL capture gestures: `-`, `=`, `=x`, `=c`, `=r`, `=m`, `=t`, `*`, `<<`, `>>`, `!`, `~`, `^`, inbox routing, offer verdicts, req carry/drop) | **Yes** (`task_block_layout` writers used everywhere) | **No** (`capture/sections.rs` only *avoids clobbering* badges/headings) | **Single centralized post-pass** in `src/native/capture/plan.rs:1155-1169` (see §5.4). |
| **`bob-mac-capture`** (macOS Capture Panel) | Thin client of `bob capture` | Thin client of `bob capture` | **Zero Swift write-path changes!** Verify dry-run preview & `⌃↩ Open` jump line remapping (see §5.4). |
| **`bob task move`** (`src/native/task_move/command.rs`) | Yes | **No** | Run `task_status_groups::transform` on eligible modified source & destination notes before staging write. |
| **`bob task split`** (`src/native/task_split/`) | **Bug `bob-cli-pn`** | **No** | Fix `bob-cli-pn` + run `task_status_groups::transform` on eligible modified notes. |
| **`bob task merge`** (`src/native/task_merge/command.rs`) | Yes | **No** | Run `task_status_groups::transform` on eligible modified source & destination notes. |
| **`bob gmail sync`**, **`bob ref create`**, **`bob gkeep pull`** | Yes | **No** | Call the same shared `group_if_eligible(bob_dir, day_file, rel_path, contents, settings)` helper on any modified area/project note. |
| **`bob task reroll`**, **`bob task archive`**, **`bob task reconcile`** | Yes | **Yes** (already wired!) | No change needed (already canonical!). |

### 5.3 Deep Dive on the Obsidian Two-Tier Regrouping UX Policy

The hardest UX question in `^all-ops-reconcile-tasks` is: **what happens to Bryan's eyes and cursor in Obsidian when a task changes status?**

Consider two very different moments:

1. **Moment 1 — Morning GTD Review (`]s`) or discrete modal commits (`Alt+P`, `Alt+N`, `Alt+X`, `Ctrl+Shift+M`, `Ctrl+Shift+Enter`, Decay Card):**
   - On a `]s` landing, answering immediately advances the walk to the next due task anyway (`decisions:answering-advances-the-walk`). Regrouping the answered note atomically inside the write transaction is **100% invisible** — zero cursor jump, zero visual stutter, and the note is left completely clean on disk!
   - Outside the walk, when you open `Alt+P` to schedule a task for next month, or hit `Alt+X` to cancel it, or `Ctrl+Shift+M` to move it, or `Alt+N` to release it from Next back to Ready, you have made a **final disposition**. Having the task glide cleanly into `### Blocked` / `### Done & Canceled` / intake (with the cursor staying at the next task in place — or following with a `<C-o>` jump recorded on `Alt+N`) feels deliberate and predictable, and **one `u` / `Ctrl+Z` undoes both the status change and the move**.

2. **Moment 2 — Rapid in-editor status cycling (`Alt+]` / `Alt+[`):**
   - Suppose Bryan is sitting in `bob.md` on a `[ ]` task and wants to mark it In Progress (`[/]`). He taps `Alt+]` twice quickly (`[ ]` → `[*]` → `[/]`). Or he hits `Alt+]` by accident and immediately hits `Alt+[` to revert.
   - If the first `Alt+]` immediately teleports the task 120 lines down into `### Next & In Progress`, either:
     - the cursor stays at line 15 (so the second `Alt+]` mutates the *wrong* task!!), OR
     - the viewport violently scrolls 120 lines mid-double-tap, and a quick `Alt+[` teleports it 120 lines *back* up!
   - **Solution (Tier 2 — Cycle-Settled Regrouping):**
     - `Alt+]` / `Alt+[` updates the checkbox byte immediately on the current line (instant visual feedback, zero scroll shock).
     - It arms a lightweight **per-editor settle timer (~500 ms)** scoped to `(filePath, blockIdOrLineFingerprint)`.
     - If Bryan taps `Alt+]` again within 500 ms, the timer resets — zero teleporting mid-cycle!
     - As soon as **any** of these happens: (a) 500 ms elapses with no further cycle tap, (b) cursor moves off that task line, (c) another Bob hotkey runs, or (d) `active-leaf-change` / `file-open` / blur fires — the settle runs `taskStatusGroupsTransform` in one clean CM6 edit (guarded by `view.file?.path === expectedPath` so it can NEVER repeat the `fireDependencyHandEditMirror` bug!).
     - If the cursor was still on the cycled task when the timer fired, follow the task to its new line (recording a `<C-o>` jump); if the cursor already moved elsewhere, remap the cursor to stay on whatever line Bryan moved to!
     - *(Note: If Bryan's `]s` review walk or `Ctrl+Enter` closes a task, that uses Tier 1 immediately, never waiting on a timer.)*

3. **Moment 3 — `Ctrl+Enter` via Obsidian Tasks plugin:**
   - Obsidian Tasks rewrites the line synchronously when invoked via `this.tryExecuteTasksCommand(commandId)` (`180-plugin-editor-edits.js:377`), possibly inserting a recurring next occurrence (`lineDelta > 0`).
   - Immediately after `applyTasksCommandAndMaybeStamp` returns (and before `continueReviewWalkSilently`), run one atomic settle step:
     1. If `lineDelta > 0`, scan the newly spawned line(s); if a spawned recurring `#task` has `[ ]` and `[scheduled:: YYYY-MM-DD]` > today, flip `[ ]` → `[?]`.
     2. Run `taskStatusGroupsTransform` on the editor if `groupingEligibleNote(activePath, content)`.
     3. Position cursor: if `]s` walk is advancing, walk takes over immediately; otherwise, if a recurring occurrence was spawned, place cursor on the spawned occurrence (or next intake task); if closed non-recurring task, stay on the next task at the vacated intake position (recording `<C-o>` jump).

### 5.4 Deep Dive on `bob capture` + Bob Mac Capture Integration

`src/native/capture/plan.rs` has an **exceptionally clean single choke point** at lines 1155–1169:

```rust
plan_mention_mirrors(...)?;
let type_agreement = apply_type_agreement(...);
// >>> INSERT HERE: apply_task_status_groups_post_pass(...) <<<
let final_day = planner.peek_text(&day_file);
let pomodoro_blocks = block_tracker.finish_with_successor_reasons(...);
let task_blocks = task_tracker.finish(&planner);
let section_blocks = section_tracker.finish(&planner);
```

Why placing `apply_task_status_groups_post_pass` right here is ideal:
1. **100% coverage of all capture gestures in one place:** Every capture syntax (`-`, `=`, `=x`, `=c`, `=r`, `=m`, `=t`, `*`, `<<`, `>>`, `!`, `~`, `^`, inbox routes, offer verdicts, req carry/drop, mention mirrors) has already written its staged bytes into `planner` — and BOTH `--dry-run` and real commits execute `plan_capture_batch`, so preview and commit stay byte-identical!
2. **Zero extra disk I/O:** Only iterate over files already loaded and mutated in `planner` (`original != current`) that satisfy `grouping_eligible_note(relative_path, path, &current, &day_file)`. Unmodified notes are never read or touched.
3. **Three subtle details to handle cleanly in this post-pass:**
   - **`task_tracker` forwarding:** Snapshot pre-grouping text of each grouped file and call `task_tracker.track_item(&planner, &pre_group, Vec::new())` right after updating `planner`. Because `TaskBlockTracker` already re-anchors tracked blocks by `block_id` and Myers line mapping (`src/native/capture/task_blocks.rs:132-160`), `task_blocks` JSON (used by Bob Mac Capture's live task-block diff preview) will automatically report the final post-grouping line numbers with **zero spurious badge-row noise**!
   - **`items[i].result.line` remapping (important for `⌃↩ Open` in Bob Mac Capture!):** When a capture item adds a new task to intake or moves/closes a task, `planned.result.line` was recorded *before* grouping. Use Myers mapping (or `task_status_groups::TransformOutput` line mapping) to forward `item.result.line` for any item whose target path was grouped, so hitting `⌃↩ Open` in Bob Mac Capture jumps to the exact post-grouping line!
   - **Pre-existing drift in a note during dry-run preview:** Suppose a note was *not* yet grouped before a capture (e.g., an external hand-edit left 3 old tasks ungrouped). Running full-note `task_status_groups::transform` during `bob capture` will tidy those 3 tasks along with the captured item — which is actually desirable (leaves the note 100% reconciled!), and because `task_blocks` only renders the tracked task block (not the whole `## Tasks` section), Bob Mac Capture's preview stays completely clean and focused. Only `section_blocks` (used exclusively for `task_merge` into a non-task section, `task_blocks.rs:974-985`) renders a whole H2 section, and status groups only live under `## Tasks`, so there is no preview noise there either!
4. **Bob Mac Capture (`bob-mac-capture`) impact:** Per `decisions:mac-capture-is-a-thin-client`, `bob-mac-capture` shells out to `bob capture` for both preview and submit and never parses or mutates vault Markdown itself. **Zero Swift changes are required** for vault writes; only add one integration test confirming `⌃↩ Open` lands on the post-grouping line after a capture that closes (`=x`), cancels (`=c`), blocks (`*`), or creates (`-`) a task in an area/project note.

---

## 6. Recommended Implementation Plan & Sequencing

### 6.1 Phased Roadmap (De-serialized for Fastest ROI)

Rather than blocking everything behind `bob-cli-ph` → `^better-o` → `^all-ops-reconcile-tasks`, execute in **five focused, independently shippable phases** (Phases 0–2 can start **immediately**, in parallel with `bob-cli-ph`):

#### Phase 0 — Immediate Bugfix: `fireDependencyHandEditMirror` Active-File Guard (`bob-plugins`, S)
- **Files:** `bob-plugins/plugins/bob-navigation-hotkeys/src/600-plugin-dependency-mirror.js` + regression test.
- **Changes:** Verify `viewForEditor(snapshot.editor)?.file?.path === snapshot.parentPath` before running `mirrorDependencyHandEdit` / `mirrorMentionHandEdit` or updating `dependencyMirrorByPath`; cancel/flush pending timer on `active-leaf-change` / `file-open`.
- **Impact:** Immediately eliminates **~9.3% (~49/week)** of reconcile file rewrites and stops phantom `LINKED FROM (💬 mentions)` corruption during `]s` morning review.

#### Phase 1 — `bob-cli` Centralized Grouping Pass + `bob-cli-pn` (`bob-cli`, M)
- **Changes:**
  1. Extract a shared helper `task_status_hooks::group_if_eligible(bob_dir, day_file, path, contents, settings)` (reusing existing `grouping_eligible_note` + `task_status_groups::transform`).
  2. Wire `apply_task_status_groups_post_pass` into `src/native/capture/plan.rs` (after `apply_type_agreement`, before `task_tracker.finish`), forwarding `task_tracker` and `items[i].result.line`.
  3. Wire `group_if_eligible` into `bob task move`, `bob task split` (fixing **`bob-cli-pn`** at the same time), `bob task merge`, `bob gmail sync`, `bob ref create`, and `bob gkeep pull`.
  4. Export a deterministic **`SG` (Status Groups) Rust test-vector generator** (mirroring the existing `RL`/`RW` vectors for `task_block_layout`) to pin the upcoming JS twin.
- **Impact:** Every Capture Panel (`bob-mac-capture`) and CLI operation leaves notes 100% reconciled.

#### Phase 2 — Rust-Pinned `task-status-groups-twin.js` + Obsidian Reconcile Parity (`bob-plugins`, L)
- **Changes:**
  1. Build `task-status-groups-twin.js` (pure Markdown transform + `groupingEligibleNote` + `mapLine` line-tracker), pinned byte-for-byte against Rust `SG` vectors, with copy-parity checks across `task-status-cycler`, `bob-navigation-hotkeys`, and `block-id-prompt`.
  2. Add the **recurring-spawn `[ ]` → `[?]` post-Tasks fixup** in `task-status-cycler/src/180-plugin-editor-edits.js` (eliminating 100% of recurring-spawn reconcile flips).
  3. Wire **Tier 1** atomic regrouping into:
     - `task-status-cycler`: `Ctrl+Enter` (post-Tasks settle), `Ctrl+Shift+]` (plus managed-link promotion refusal), transcluded completion.
     - `bob-navigation-hotkeys`: `Alt+P` / Task Card (`390`), `Alt+N` / `Alt+X` (`240`), Decay Card / `Alt+F` / `Ctrl+Alt+F` (`548`), `Ctrl+Shift+M` (`250`), Task Split (`256`, including `bob-cli-pn` JS side), hand-edit dependency mirror (`600`).
     - `block-id-prompt`: `Ctrl+Shift+Enter` (`140-plugin-target-plans-and-rewrites.js`) when raising target `[ ]` → `[*]`.
  4. Wire **Tier 2** cycle-settled regrouping (~500 ms debounce + cursor-leave/note-leave flush) into `task-status-cycler` `Alt+]` / `Alt+[` (single & counted ranges).
- **Impact:** Together with Phases 0–1, drops `bob task reconcile` file rewrites by **~75–85%** (from ~529/week / ~75/day down to ~75–95/week / ~11–14/day — almost exclusively legitimate midnight schedule wakes and daily Pomodoro ledger settlement).

#### Phase 3 — `^better-o` Implementation (Sequenced Immediately After `bob-cli-ph.7`, `bob-plugins`, M)
- **Why after `bob-cli-ph.7`:** `ph.7` (`obsidian-drawers`, currently `IN_PROGRESS`) owns `task-status-cycler`'s transition from `NOTES` to `- **Notes**`, `*` → `**|**` drawer typing assist, and Smart Enter on drawer headers. Landing `^better-o` right after `ph.7` avoids merge conflicts and guarantees `Ctrl+Shift+O` uses `- **Notes**` natively from day one.
- **Changes:**
  1. Replace naive `handleVimOpenLineBelow` (`o`), `handleVimOpenLineAbove` (`O`), and `handleVimOpenChildBulletLineBelow` (`Ctrl+Shift+O`) with a pure planner implementing the Section 4.3 decision matrix on top of `task-block-layout-twin.js` + `task-status-groups-twin.js`.
  2. Add the empty-scaffold auto-prune guard (for empty `<Esc>` after `o` new-task or `Ctrl+Shift+O` newly created `- **Notes**`).
  3. Upgrade `199a-req-typing.js` so typing `- [` on a direct child of a task below existing drawers/notes atomically re-slots the new req into the `reqs` zone and scoops loose notes into `- **Notes**`.

#### Phase 4 — Post-Rollout Verification (`~/bob`, XS)
- Run Bryan's normal morning review + daytime editing + Mac Capture workflow for 3–5 days, then re-run the reconcile git-log audit to confirm remaining reconcile commits are strictly time-driven wakes, Pomodoro ledger cleanup, and rare manual raw-Markdown edits.

### 6.2 Projected Impact on Reconcile Churn

| Metric (7-day rolling window in `~/bob`) | Current Baseline | Projected After Phases 0–3 | Reduction |
| --- | ---: | ---: | ---: |
| Reconcile `.md` file rewrites / week | **529** (~75/day) | **~85–110** (~12–16/day) | **~80–84%** |
| Status-group / badge-only rewrites | 320 (60.5%) | **~0–5** (raw hand-edits only) | **~99%** |
| Recurring-task `[ ]`→`[?]` flips | 30 files / 98 tasks | **0** | **100%** |
| Bogus cross-note `LINKED FROM` mention strips | 49 files (9.3%) | **0** | **100%** |
| Intra-task `bob task tidy` drift | 0 / 598 | **0 / 598** (preserved under `o` & split) | Maintained |
| Remaining legitimate work (midnight wakes + Pomodoro ledger) | ~119 files | **~85–110 files** | Intentionally stays in `reconcile` |

### 6.3 Suggested Note to Leave on In-Progress Bead `bob-cli-ph`

Per `^better-o`'s note (*"see `bob-cli-ph` for recent changes to drawers which are ongoing--so you might want to leave notes on that bead"*), here is the concrete coordination note to attach to `bob-cli-ph` (specifically relevant to `bob-cli-ph.7` `obsidian-drawers`):

> **Coordination note for upcoming `^better-o` (`o` / `O` / `Ctrl+Shift+O` in `task-status-cycler`):**
> 1. Please keep the `task-block-layout-twin.js` note-insertion / `- **Notes**` creation planner (`taskBlockEnsureNotesDrawer` / `taskBlockInsertNote`) cleanly callable as a pure function returning the inserted line/ch and whether it newly materialized `- **Notes**`, so `Ctrl+Shift+O` on a req-owning task can reuse it directly and auto-prune the drawer if the user exits insert mode without typing.
> 2. Please ensure `ph.7`'s `*` → `**|**` drawer typing assist works immediately on a freshly opened sibling bullet at drawer indent (which `^better-o`'s `o` on an existing drawer header will emit).
> 3. Keep `ph.7`'s Smart Enter on `- **Title**|` focused on opening a child inside the drawer; `^better-o` will make `Ctrl+Shift+O` on a drawer header append a child at the end of that drawer's children and `o` on a drawer header open a sibling after the drawer's subtree, so all three gestures remain cleanly orthogonal.
> 4. `^better-o` will sequence right after `bob-cli-ph.7` closes to avoid colliding on `task-status-cycler` drawer helpers and typing extensions.
