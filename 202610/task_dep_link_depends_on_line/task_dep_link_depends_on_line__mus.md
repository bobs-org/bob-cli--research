# Task dependency links: from transcluded sub-bullets to single-line normal links

Research report — researcher `mus`. Independent investigation; no peer reports consulted.

## 0. TL;DR

The request is a good idea and is **~80% built already**. `bob-navigation-hotkeys`
already implements almost exactly what is asked: a managed single-line child bullet

```
  - 🔗 **DEPENDS ON:** [[#^a]] • [[#^b]]
```

using **normal (non-transcluded) block links**, plus picker add/remove rows with fuzzy
matching, plus a one-shot migration command, plus dual-write sync with the
`[dependsOn:: …]` parent-line field. The missing piece — and the real work of this
feature — is on the **bob-cli side**: `task-status-hooks` still derives promotion
edges *only* from sole transcluded block references (`sole_transcluded_block_reference`
in `src/native/task_status_hooks/references.rs`). If the user stops writing transclusions
before the hooks learn the new bullet, dependency promotion silently breaks. Recommend:
adopt the plugin's `DEPENDS ON` bullet as the canonical **task dep link** format, teach
the hooks to read it as edges (treating it identically to a transclusion), keep
`[dependsOn:: task-id]` as the machine source of truth for `Blocked [?]` (Tasks-plugin
compatible), finish the picker UX, migrate, then deprecate transclusion edges. With two
adjustments (keep transclusion parsing as a deprecated fallback; do not abandon the
`dependsOn` field), approve the plan.

## 1. How dependencies work today (verified in this checkout)

There are **two parallel mechanisms**, and any redesign must preserve both effects:

### 1a. Transcluded block-link sub-bullets → status *promotion* propagation

- A task with a block id (`^block-id`) that has child bullets, each of which is a *sole
  transcluded block reference* (`- ![[Note#^dep]]`, no alias, valid block-id charset),
  gains dependency edges (`dependency_edges()`, `references.rs:307`).
- `desired_statuses()` (`references.rs:409`) propagates the strongest effective parent
  status down those edges: Ready `[ ]` → Next `[*]` → In Progress `[/]`. Propagation
  never lowers a status, and unlinking never changes a lane (consistent with the
  `task-lanes-are-sticky` decision: only Alt+N / the lane row releases Next→Ready;
  Blocked stays derived).
- Glossary `task-link.md` currently documents exactly this: "transcluded task links that
  are the only contents of a sub-bullet on another Obsidian task are treated as sub-tasks
  (i.e. dependencies) of that task."

### 1b. `[dependsOn:: task-id]` inline metadata → `Blocked [?]` derivation

- Separately, `task_dependency_states()` (`sync.rs:678`) resolves each task's
  `[dependsOn:: …]` ids against the vault-wide `[id:: …]` identity map. Any open
  dependency → `Transition::MarkBlocked`; cleared → unblock path (`sync.rs:505–600`).
- This is Obsidian-Tasks-plugin-native semantics (the plugin itself understands
  `dependsOn`/`id`, `isBlocked`/`isBlocking`, ⛔ emoji; bob-cli's Dataview layer parses
  and renders them too — see `src/native/dataview/tasks/`).
- **Identity mismatch to note:** (1a) keys on *block ids* (`^block-id` + note path);
  (1b) keys on *task ids* (`[id:: …]`). They are two different namespaces that today
  happen to be correlated by convention, not by construction.

## 2. What bob-plugins already implements (linked repo, v1.50.0)

All line references are to `plugins/bob-navigation-hotkeys/main.js` in the linked
`bob-plugins` checkout:

- **Canonical single-line format** (lines ~241–270): a managed child bullet
  `  - 🔗 **DEPENDS ON:** [[#^a]] • [[#^b]]` — normal links (no `!`), ` • ` separator,
  bold label + link emoji. Legacy `DEPENDENCIES` label and emoji-less bullets are
  recognized and normalized in place. This is *precisely* the "single line, visually
  appealing, normal task links" the request asks for. It already exists.
- **Legacy transclusion recognition + migration**: `DEPENDENCY_TRANSCLUSION_BULLET_RE`,
  `parseDependencyTransclusionBulletDetails`, and a dedicated
  `consolidate-dependency-navigation-links` editor command (registered ~line 25200)
  rewrite a note's dependency transclusions into the managed shape.
- **Dual-write with `[dependsOn::]`**: the picker/toggle flows call
  `applyLocalTaskDependencyListEdits(lines[parentLine], "dependsOn", …)` and stamp
  the target's `[id:: …]` (see `applyDependencyToggle`-style flow ~lines 12340–12420:
  adding a transclusion writes the canonical `dependsOn` id; removing one removes it;
  adding also promotes the target checkbox and blocks the parent — mirroring hooks
  semantics at edit time).
- **Picker UX**: `BulletPropertyPickerModal` (`set-bullet-property` command — the
  picker the Ctrl+Shift+P-era docs refer to; note the command itself declares no
  hardcoded hotkey, so Ctrl+Shift+P is Bryan's user binding worth confirming in
  `.obsidian/hotkeys.json`) already has dependency rows, counted-session support,
  `pendingCountedDependency` state, "alreadyLinked → depends linked" rendering, and a
  task picker whose dependency candidate list is intentionally restricted to open tasks
  (~line 8262) with `fuzzyMatchesText` filtering used across all picker modals.
  `dependsOn` rows are deliberately hidden in Task-Link mode ("remote tasks are edited
  through their own notes" — the sticky-lanes-era invariant that a link bullet edits the
  *linked* task, ~line 15393).

So the editor half of the request — format, single line, emoji/label styling, add/remove
via the existing picker, fuzzy matching — is designed, shipped, and iterated. The request
is less "design a new feature" than "finish and ratify a migration already in flight."

## 3. Critique of the plan

**Is it a good idea? Yes, with two adjustments.**

Arguments for:

1. **Readability.** One `DEPENDS ON` line replaces N child bullets; project notes with
   fan-in (many tasks blocked on one migration/decision task) collapse dramatically.
2. **Render cost.** Every `![[…]]` embed is live-rendered by Obsidian. N embeds per
   parent across a vault of hundreds of tasks is measurable editor overhead; plain links
   are inert text.
3. **Edit ergonomics.** A single link-span is one undo unit and one line to parse; N
   transclusion bullets invite partial-delete skew (parent thinks dep removed, hooks
   still see an edge, or vice versa).
4. **Consistency with sticky lanes.** The decision record already treats links as
   lane-affecting inputs; a managed single writer (the picker) reduces the chance of
   hand-authored skew.

Risks / objections (and why none is fatal):

1. **Loss of at-a-glance dep status.** A transclusion shows the dependency's text and
   checkbox live; a `[[#^a]]` link shows only the id until hovered. *Mitigation:* the
   parent's own derived status (`?`/`[*]`/`[/]`) already summarizes "blocked or not";
   the Tasks plugin and `bob plan` can surface dep titles in Blocked views. Do not try to
   recover inline status text — that recreates the embed cost.
2. **The `!` also meant "sub-task" visually.** Some users nest to show hierarchy.
   Dependencies are not subtasks, so flattening is semantically *more* honest; genuine
   subtasks keep normal indented `- [ ]` children (untouched by this change).
3. **Silent promotion loss during migration (the big one).** Today the hooks *only*
   understand transclusions. Any parent converted to nav-bullet-only loses its promotion
   edges on the next hooks run until bob-cli learns the format. The migration must be
   ordered: ship hooks support → run it in dual-read mode → migrate notes → deprecate.
4. **Cross-note links.** The nav regex already supports `[[Note#^id]]`; hooks-side
   resolution must reuse `NoteIndex::resolve` exactly as `dependency_edges` does
   (same-note empty target + vault-wide same-name disambiguation + unresolved-reporting),
   or cross-note deps will resolve differently in the two layers.

**Adjustment A (required): keep transclusion parsing as a deprecated fallback.** Do not
remove `sole_transcluded_block_reference` from `dependency_edges`. Instead, union both
sources: transclusion bullets ∪ `DEPENDS ON` link-spans. Rationale: vault history,
daily-note archives, and other devices' caches will contain transclusions for months;
a flag-day parser change would flip lanes on old notes. Log a per-run count of
transclusion edges seen (existing `unresolved`/change reporting plumbing can carry it)
so deprecation progress is observable, then remove no earlier than one release after the
migration command reports zero remaining.

**Adjustment B (required): keep `[dependsOn:: …]` as the blocking source of truth; the
nav bullet is the human layer.** Do not let the nav bullet *replace* `dependsOn` for
`Blocked` derivation. Reasons: (i) Tasks-plugin compatibility — `dependsOn` renders in
Tasks queries, Dataview, and any future tooling; a plugin-proprietary bullet does not;
(ii) identity namespaces differ (block-id vs task-id) and `dependsOn` is what the
unblock path already keys on; (iii) the plugin already dual-writes both, so no new edit
path is needed — just declare the contract: *picker keeps them in sync; hooks read
edges from the nav bullet (promotion) and blocking from `dependsOn` (Blocked); skew
between them is reported, with `dependsOn` winning for Blocked and the union winning
for promotion.* This matches the existing `managedIds`/`managedTargetKeys` reconciliation
logic in `collectDependencyNavigationTargets`-style code (~line 3430).

Smaller adjustments:

- **Do not put dep links on the parent task line itself.** Inline `[[#^x]]` spans inside
  the task text would leak into Tasks-plugin description, search text, and `bob plan`
  rendering. The single *child* bullet is the right scope: one extra line, machine-owned
  shape, human-readable label.
- **Scope the picker candidate list deliberately.** "Fuzzy search across the entire
  vault" should mean *all open `#task` lines vault-wide* (current behavior per ~line
  8262), excluding done/cancelled/non-task, with an explicit opt-in (typed prefix or
  toggle) to include closed tasks for historical/record deps. Unrestricted includes
  invite depending on completed tasks, which is almost always a mistake and would
  needlessly mark parents Blocked-then-unblocked.
- **Ctrl+Shift+P scope check.** That picker already hosts lane-toggle, refresh, cancel,
  priority, and date rows. Add two rows, not a new modal: `Add dependency…` (vault-wide
  fuzzy task search → append link + dual-write `dependsOn`) and per-link `Remove`
  affordance (cursor-on-link removes that link; cursor-on-parent offers checklist of
  current deps). Reuse `FilteredPickerModal` + `fuzzyMatchesText`; no new fuzzy engine.

## 4. Recommended solution

1. **Format (adopt as-is from the plugin).** Canonical task-dep-link bullet:
   `  - 🔗 **DEPENDS ON:** [[target#^block]] • [[#^other]]`, one child bullet per parent
   task, links in insertion order, deduped by (note, block) key. Same-note links use the
   empty-target `[[#^…]]` form. Normative regex already exists
   (`DEPENDENCY_NAVIGATION_BULLET_RE`); port it to Rust, don't redesign it.
2. **bob-cli hooks (the actual work).**
   - Extend `dependency_edges()` to also collect link targets from `DEPENDS ON`
     bullets (same indent/parent-item scoping, same fenced-code exclusion, same
     `NoteIndex::resolve`, same missing/duplicate reporting). Union with transclusion
     edges.
   - Keep `task_dependency_states()` (`dependsOn` → Blocked) unchanged; add a
     skew diagnostic when nav-links and `dependsOn` disagree (informational only).
   - Tests: mirror the existing `structure.rs` transclusion tests for the nav shape;
     add a mixed parent (transclusion + nav) test; add a cross-note nav test.
3. **Picker (small delta).** Two rows in the existing bullet-property picker as above;
   both dual-write nav bullet + `dependsOn` + target `[id::]` (existing helpers already
   do this — wire, don't rewrite). Keep the open-tasks-only default with a closed-task
   opt-in.
4. **Migration.** `consolidate-dependency-navigation-links` (exists) becomes the
   supported path; run it per-noteVault-wide after the hooks release lands; hooks emit a
   transclusion-edge count so stragglers are visible. No flag day.
5. **Glossary.** Add memory-web term `task-dep-link` ("task dependency link"): *a normal
   (non-transcluded) block link inside a task's managed `DEPENDS ON` child bullet,
   naming a task that must complete before the parent unblocks; the human layer over the
   `[dependsOn::]` machine field.* Update `task-link.md`'s transclusion-dependency note
   to point at it (via `/sase_memory_write` procedure, not a direct edit).
6. **Docs.** One short section in `docs/task-status-hooks.md` showing the bullet,
   the dual-write contract, and the skew-wins rules (`dependsOn` wins Blocked; union
   wins promotion).

## 5. Open questions for the lead (not blockers)

- Should `bob plan` / Blocked views expand dep-link titles inline (recovering some of
  the transclusion readability without the embed cost)? Cheap at render time, worth a
  follow-up bead.
- Should self-dependency and duplicate-id handling differ between the two layers, or
  stay exactly as today (`[dependsOn:: self]` fixtures exist; nav-span self-links
  should get the same treatment — likely ignore-with-warning)?
- Confirm Ctrl+Shift+P is bound to `set-bullet-property` in the live vault
  (`.obsidian/hotkeys.json`) rather than assuming it; the code declares no default
  hotkey for that command.

## 6. Evidence index (all paths verified this session)

- `src/native/task_status_hooks/references.rs:307–383` — `dependency_edges`,
  transclusion-only edge discovery.
- `src/native/task_status_hooks/references.rs:494–516` —
  `sole_transcluded_block_reference`.
- `src/native/task_status_hooks/sync.rs:678–715` — `task_dependency_states`
  (`dependsOn` → open/unresolved).
- `src/native/task_status_hooks/sync.rs:404–600` — edges→promotion vs
  `dependsOn`→Blocked split.
- `src/native/task_status_hooks/mod.rs:82–104` — documented contract.
- `sase/memory/glossary/task-link.md` — current transclusion-dependency definition.
- `sase/memory/decisions/task-lanes-are-sticky.md` — lane/Blocked invariants.
- `tests/fixtures/tasks_parity/vault/Tasks/Dependencies.md` — `dependsOn` fixtures.
- bob-plugins `bob-navigation-hotkeys/main.js` v1.50.0: `~241–270` format+regexes;
  `~3430` managed-id reconciliation; `~12340–12420` dual-write toggle;
  `~15393` link-mode `dependsOn` hiding; `~20181` picker modal; `~28851` picker entry;
  `~8262` open-tasks-only filter; `consolidate-dependency-navigation-links` command.
