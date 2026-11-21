# Nested task reqs and the REQUIREMENTS → NOTES migration

Research and recommendation, 2026-11-21.

**I recommend both changes, and recommend keeping the name “task requirement,” shortened to “task req” or “req.”** Nesting is a substantial revision to the proposed implementation, especially capture, branch operations, and close-card selection. It does not require replacing the design's lifecycle or storage model. Renaming existing `REQUIREMENTS` drawers to `NOTES` is a smaller, safer migration than converting their contents into reqs.

The useful distinction is: **a req describes part of one task's committed scope; it has no independent completion lifecycle.** A nested req refines that scope. If it needs its own completion, schedule, priority, or work tracking, carry it into a real task.

This report assesses the [consolidated design](task_reqs_design/task_reqs_design__final.md), particularly §§3, 4.1, 5.1–5.7, and 7. Bryan's latest request replaces its single-level restriction and clarifies its ambiguous migration language. Recommendations below are proposed design amendments, not claims that these behaviors already ship. No application code, vault contents, tracking beads, or accepted memory records were changed.

**What survives, and what changes**

| Part of the original design | Recommended disposition | Size of change |
| --- | --- | --- |
| Checkbox storage without `#task`; hashes are presentation | Keep; derive glyph depth from the requirement tree | Small |
| Pending reqs become met with their owning task; Bob does not write req completion | Keep, with explicit ancestor-drop rules | Medium |
| Single-level recognizer and `req_nested` refusal | Replace with recursive recognition and structural boundaries | Large |
| Capture's two-level authored grammar | Extend for nested reqs and their notes; preserve other route contracts | Large |
| Carry via Task Split | Keep the engine; extend selection, ownership rebasing, and overlap handling | Large |
| Requirements group on the existing successor card | Keep; add hierarchy, subtree effects, and conflict handling | Large |
| Req → task → project conversion family | Keep; promote one requirement level at a time | Medium to large |
| First-req `NOTES` creation and loose-note scoop | Keep at the real task boundary; avoid recursive drawer proliferation | Small |
| “Convert or retire” existing `REQUIREMENTS` drawers | Replace with explicit, content-preserving rename/merge into `NOTES` | Small to medium |
| Reader/writer hardening, capability gates, shared vectors | Keep and test at every supported depth | Broader coverage |

The original eight delivery areas still make sense. Their phase count understates the added work: phases 1, 2, 3, 5, 6, and 7 all need meaningful amendments. I would re-estimate those areas before scheduling implementation. The evidence does not support a credible percentage or person-day estimate; this is source inspection, not an implementation spike.

**Why retain nesting**

Nesting lets a broad requirement contain its specific obligations without flattening away context or creating separate scheduled work. For example:

```text
- [ ] #task Ship the exporter ^export
    - [ ] Handles supported inputs
        - [ ] Handles Windows files
            - [ ] Preserves CRLF
            - Fixture: windows.csv
        - [ ] Handles empty input
    - NOTES
        - Morgan reported the original issue.
```

The requirement marks render as `⌗⌗`, `⌗⌗⌗`, and `⌗⌗⌗⌗` at successive requirement depths. The fixture bullet remains a note. There is still one task until an explicit carry or promotion creates another.

This is useful structure at a real cost: branch-level actions are more complicated than row-level actions, and a long close-time audit is easier to rubber-stamp. I would accept that cost because Bryan explicitly wants nested scope, while keeping independent lanes, dates, progress percentages, and completion out of reqs. Hierarchy alone does not require those features.

Org's checkbox lists demonstrate that lightweight nested items can stay outside the global TODO list. Its automatic parent-checkbox progress is a different semantic choice and should not be imported into Bob. This is an analogy for lightweight hierarchy, not evidence that Bob users want early ticking. [Org manual](https://orgmode.org/manual/Checkboxes.html).

“Keep support” should not be read as “turn an existing feature back on.” The original report describes nesting in the canceled proposal, whereas the inspected current code still has no requirement child kind and capture still models only two authored depths. There is reusable subtree machinery, but no verified, shipped nested-req implementation to retain unchanged. [C1], [C2]

**The minimum complete nesting contract**

**Ownership must distinguish the structural parent from the owning task.** A req is a non-`#task` checkbox whose immediate list parent is either a real task or another recognized req. Following that chain must reach one real task. Every req in that chain shares that task's completion lifecycle. A genuine nested `#task` starts its own ownership boundary; it is not a req merely because it is indented.

A plain note, drawer, managed log, quote, fence, notebook body, or Pomodoro row interrupts req recognition. Thus a copied checklist under `NOTES`, or under a plain note attached to a req, stays ordinary content. Do not implement “any checkbox somewhere below a task is a req.” That would greatly expand accidental conversions compared with the original proposal.

Source indentation establishes structure. Hashes do not: keep checkbox bytes and render depth-specific marks. Literal `###` and `####` have Markdown heading semantics; CommonMark defines ATX headings for one through six hashes. Keeping the glyph separate also avoids an artificial six-heading limit on req nesting. [CommonMark §4.2](https://spec.commonmark.org/0.31.2/#atx-headings).

There should be no arbitrary single-level or two-level product restriction. An implementation may need a documented safety bound for pathological depth, but must refuse explicitly rather than flatten or discard content. Store numeric depth/parent relationships or an equivalent tree; extending a `First | Nested` enum with one more case merely postpones the same problem.

**Derived completion remains the right default.** Nesting should not introduce parent-req progress or a second completion cascade. Pending reqs become met when the owning real task is done, and moot when it is cancelled. Reopening the task makes its live scope pending again. The original proposal's decision to accept legacy/manual `[x]` is a compatibility exception, not permission for a Bob gesture to tick a req early. A manually checked intermediate req must not complete its descendants while the real task is open.

Dropping a branch needs an additional rule: mark its root `[-]`, preserve its descendants, and derive that its otherwise-active descendants are excluded by the dropped ancestor. Do not call those descendants met when the task closes. Restore the branch root and its previously active descendants return, while an explicitly dropped child stays dropped and a carried child stays carried. This preserves history without writing a cancellation mark and reason on every descendant.

| Operation | Recommended subtree behavior |
| --- | --- |
| Close/reopen the real task | Derive state for all active reqs at every depth; no req-completion writes |
| Drop a req branch | Drop its root; show the number of descendants excluded with it; preserve child bytes and explicit outcomes |
| Restore a dropped branch | Restore root scope; retain independently dropped/carried descendants |
| Carry a req branch | Create one task from the selected req and move its entire subtree; descendants become reqs of the new task |
| Carry only a nested leaf | Leave the outer req in place with a carried stub at the leaf's original position |
| Toggle req back to note | For a leaf, ordinary toggle; for a branch, refuse unless an explicit preview accounts for all descendant reqs |

Carrying does not add a dependency to the old task. A parent requirement whose child was dropped or carried now represents its remaining committed scope. If that result is misleading, revise the parent's text or explicitly add a dependency to the carried task; do not secretly make nesting a dependency graph.

**Notes stay with the object they explain.** Keep the original task-level order: managed links, req subtrees, drawers (`NOTES` first), logs, with the existing cancellation-log exception. Sorting moves whole subtrees. At the req level, retain authored child order and attached notes; do not create a `NOTES` drawer under every req. The task's first-req scoop moves only loose notes belonging directly to that task, never notes belonging to nested reqs.

When a req becomes a task through carry or promotion, its directly attached prose becomes that new task's notes. If the new task has child reqs, apply the same task-level `NOTES` rule there. This is an ownership transition that the original flat design did not need to specify.

**The close card needs branch semantics, not just indentation.** Show pending reqs in document order with parent context, depth, and expand/collapse behavior. A collapsed branch must expose the number of pending descendants and any staged exceptions. Default remains Met; task-offer “mark all” continues to exclude req rows. Counts should describe scope, such as “6 reqs in 2 branches,” rather than imply six independently completed tasks.

Ancestor and descendant selections can overlap. Carrying an ancestor already carries its descendant; independently carrying both must not produce two copies. Dropping an ancestor while staging a carry underneath it is also a conflict. For the first version, I recommend refusing overlapping structural choices with a clear explanation, rather than inferring action order or silently clearing a staged choice. Disjoint branch actions can commit together. After carrying an entire branch, the user can further split it from its new task.

Replace the flat proposal's text-hash-based row identity with a snapshot-bound identity that includes the structural path/parent and occurrence, optionally using an existing anchor. Validate the relevant subtree and owner preimages at commit. Duplicate “Handles errors” rows under different branches, or an indent change while a card is open, must never redirect a verdict. Permanent IDs on every req are unnecessary for this.

Ctrl+J stays navigation-only and lands after all writes. If a pinned descendant moves because its ancestor is carried, resolve its new location from the move map. A pin must neither create a second task nor change the verdict. This follows the existing jump decision, rather than reopening it.

The original report also contains an existing Esc ambiguity: its Obsidian card is post-close, but its acceptance prose says Esc writes nothing “anywhere.” A revised document should say that Esc discards staged req edits while the already-completed owner remains done; the Mac's pre-write card returns to the draft. Nesting does not itself require changing card timing. Whichever timing is retained, enumerate the req group from the pre-close snapshot so derived Met does not make the audit disappear.

**Promotion should move the boundary by one level**

Promote the outermost reqs to project tasks and keep their descendants as reqs of those new tasks. For example:

```text
Before: one task                  After promotion: project task plus task rows

Ship exporter                     ## Tasks
  req: Handles inputs             - [ ] #task Handles inputs
    req: Handles Windows files        - [ ] Handles Windows files
      req: Preserves CRLF                 - [ ] Preserves CRLF
  req: Documents flags            - [ ] #task Documents flags
```

Flattening all descendants into independent project tasks would discard the distinction Bryan is asking the name to preserve. Keeping only the roots and converting descendants into prose would discard req semantics. One-level promotion preserves both structure and the ability to promote or carry a branch later.

Retain the original mappings for dropped roots, carried stubs, task-level prose, drawers, and logs, but add fixtures for descendants and owner-dependent state. In particular, moving a branch out of a done owner must not silently reinterpret historically met descendants as newly pending. The converter should preserve the explicit/history states it can represent and refuse ambiguous cases; closed/history conversion is not solved merely by indentation.

The later project-to-task conversion should also be reconsidered: a task with only reqs and attached notes can potentially demote to a req branch. Having child reqs alone need not force it to remain a separate task, as the flat design assumed. Independent schedules, dependencies, links, and history still require the existing carried-task fallback or a refusal. This broadens representability; it is not a promise that every project can round-trip losslessly.

Nesting removes one structural objection to merge-writes-a-req, but does not resolve whether “merge” means duplicate work or additional scope. I recommend keeping that feature deferred.

**What the code inspection changes in the estimate**

| Original delivery area | Verified constraint and resulting amendment |
| --- | --- |
| 1. Core contract and hardening | `TaskChildKind` has no req variant, and `classify_direct_children` intentionally excludes grandchildren. Keep direct-child callers intact and add a requirement-tree view for recursive consumers. Scheduling and embedded close hazards identified in the original report remain present and must be guarded at all depths. [C1][C4] |
| 2. Capture | `AuthoredDepth` is exactly `First | Nested`; `classify_authored_line` accepts column zero or exactly two spaces. Grouping helpers rely on that binary distinction. A third requirement level, and notes under a second-level req, require real grammar work. Generalize representation while admitting deeper structure only in the appropriate contexts; do not accidentally change notebook, record, close-log, or drawer capture semantics. [C2] |
| 3. Close engine | Task Split already preserves/rebases descendants and repairs moved anchors, but its candidate collector selects direct task children and drawer entries. Arbitrary nested req extraction needs new candidate resolution, a root-owner context, and non-overlapping selections. The current split stub is a plain link; the proposed `[>]` req stub remains new work. [C3] |
| 4. Rendering | Depth marks are comparatively small work; recognizing ancestors across folds, viewport boundaries, and Reading view requires shared fixtures. Existing checkbox/freshness readers are broad and still need guards. Expose semantic labels such as “requirement, level 3, of Ship exporter,” not spoken hash strings. [C5] |
| 5. Obsidian gestures and card | Every eligibility guard must recognize the full req chain; insertion, indentation, note conversion, drop/restore, carry, duplicate labels, and pinned descendants need tree-aware behavior. Existing real nested tasks retain their own semantics. |
| 6. Mac | `bulletIndentationEdit` only moves between zero and two spaces; continuation and paste-placeholder helpers also encode those depths. Extend Tab/Shift-Tab, Return, paste, marker expansion, atomic deletion, and undo coverage. Bob should return semantic depth/parent and eligibility data; Swift remains a presentation/editing client. [C6] |
| 7. Promotion | `buildProjectSeedFromChildBullets` already collects descendants, but treats every eligible non-drawer direct bullet as a task. Keep the original notes-versus-work correction, then apply the one-level conversion rule and destination note normalization. [C7] |
| 8. Migration | Replace inferred drawer-content conversion with structured rename/merge. Expand scope from the original “live drawers” wording to all existing drawers, including closed/archive content and the project-section drawer representation. [C8] |

The original claim that the capture drawer decision is not reopened no longer holds: `decisions:capture-bullets-mirror-the-task-block` explicitly names third-level authored bullets as a condition for reconsideration. Its central principle—capture mirrors the task block—still fits the requested design. The thin-client and navigation-only jump decisions remain applicable without change.

The inspected capture grammar revision is still 28. If these changes ship together, they can share the proposed next grammar revision and successor capability revision; nesting does not inherently require an extra release cycle. Pin the actual revisions at implementation time. Old-client default Met is safe only after the reader/writer guards are in place; it does not make broad legacy checkbox writers harmless. The Mac changes still require compilation and exact-commit macOS CI under that repository's rules.

**Migrate every REQUIREMENTS drawer to NOTES, preserving content**

I recommend interpreting “all existing drawers” to include open, done, and cancelled tasks, including archived tasks, plus eligible project `## Requirements` sections that Bob exposes as drawers of `^prj`. This last category follows the current drawer API, not a generic heading-replacement rule. Ordinary `Requirements` headings in other note types, quoted examples, fences, and body prose are outside that category. Report malformed or ambiguous candidates rather than silently claiming a complete migration.

The migration should do the following:

1. Inventory recognized drawer keys matching `REQUIREMENTS`, using Bob's normalization. Report open/closed/archive/project-section counts, existing `NOTES` collisions, duplicate headings, and affected links. The original report's “one live drawer” is historical evidence, not an inventory of this broader scope; I did not rescan the vault in this research.
2. Rename a lone task drawer to `NOTES`, or a project drawer section to `## Notes`, preserving its entire body, nested structure, anchors, checklist bytes, logs, and ordering.
3. When a `NOTES` drawer already exists under the same owner, consolidate into one. Recommended deterministic rule: use the earliest participating container's position, label it `NOTES`, and concatenate bodies in original container order. Preserve repeated content rather than guessing that duplicates can be deleted. Ambiguous cases receive an explicit preview.
4. Repair links to renamed project heading anchors, including embeds and Markdown links where resolvable. When consolidation would make heading identity ambiguous, require explicit resolution instead of leaving broken references. Block anchors inside bodies must remain stable.
5. Refresh the derived drawer catalog and update active saved templates/examples/routes that would recreate `#requirements`. A transitional alias is optional and should be explicit and bounded; it is not a reason to maintain two canonical drawer names indefinitely.
6. Apply one previewed transaction with stale-file/dirty-buffer protection and a recoverable preimage. Re-run inventory and migration: no recognized legacy drawers should remain unresolved, and a second migration should produce no changes. Any excluded or unresolved cases must be listed before calling “all” complete.

Crucially, **do not turn a drawer's bullets into reqs as part of this rename**. The drawer name says how prose was filed, not that every bullet is mandatory scope. Existing ordinary checkbox lists inside a migrated `NOTES` drawer also stay ordinary checkbox lists. Bryan can explicitly mark and move particular statements into the req tree later.

This migration applies even to tasks with zero reqs. It is separate from the original first-req scoop, which leaves other zero-req loose notes alone. It should not be hidden inside a general tidy or reconciliation pass. `NOTES` also remains compatible with any later cosmetic change away from ALL-CAPS drawer titles; that separate UI choice need not delay the semantic migration.

**Why “task req” is still the best name**

| Name | What it communicates | Recommendation |
| --- | --- | --- |
| Task requirement / task req | Scope whose satisfaction belongs to the task; concise once learned | Use the full form in help and teaching text, “req” in compact UI |
| Subtask | A task with an independently actionable lifecycle; already a Bob contract term | Avoid for this feature |
| Step / checklist item | Something the user expects to tick while working | Avoid while early completion is forbidden |
| Acceptance criterion | A condition of success, but less natural for action-shaped obligations | Useful explanatory wording, not the primary name |
| Completion requirement | More explicit, but longer and potentially suggests a hard close gate | Possible teaching phrase, not necessary as the canonical term |

The abbreviation alone will not teach the distinction. Pair it with consistent copy: **“Part of this task's scope. Met when the task closes. Drop it or make it a task.”** For nested rows, name the owning task. Hide the interactive checkbox in managed views and guard completion gestures at every depth; a renamed noun cannot compensate for a control that still looks and behaves like an independently tickable subtask.

Renaming `REQUIREMENTS` drawers to `NOTES` strengthens this vocabulary: “req” now identifies an explicit scope item, while the drawer holds contextual material. The cost is a small amount of learned terminology and less specific drawer labeling. Those costs are preferable to two different things both called requirements. I would adopt the name and migration together, while preserving drawer content exactly.

**Evidence needed before calling the amended feature complete**

| Scenario | Required result |
| --- | --- |
| Three-plus req levels, notes between branches, mixed source indentation | Same ownership and depth in Rust, Obsidian, capture preview, and Mac; malformed ancestry refuses rather than flattens |
| Checklist under a note, drawer, fence, or quoted/imported text | Never acquires req semantics accidentally |
| Done, cancel, and reopen via managed and unmanaged paths | All active descendants derive the correct state; no early completion write |
| Drop/restore outer branch containing dropped and carried children | Descendant history survives; no descendant falsely reads as met |
| Carry outer branch versus carry one leaf | Exactly one task per selected disjoint branch; notes/anchors travel; root ownership changes correctly |
| Select ancestor and descendant for carry/drop together | Conflict is visible before writes; no duplicate, lost, or silently ignored scope |
| Reorder or reindent duplicate-labelled rows while card is open | Stale selection refuses; no verdict moves to another branch |
| Pin descendant then carry its ancestor | One final jump to the correct moved location, preserving walk behavior |
| Promote task with nested reqs and mixed notes | Only outer reqs become tasks; descendants retain req identity and notes stay attached |
| Rename with existing NOTES, archive content, heading links, and repeated bodies | Content preserved, links accounted for, second run empty, no guessed req conversion |
| Walk, lanes, Today, statistics, schedule propagation, and task close scanners | Only real tasks receive task-level behavior regardless of req depth |

The recommendation is therefore to amend the existing design before implementation, retaining its storage, lifecycle, and conversion family. The substantive new decisions are branch ownership, drop/carry conflicts, and one-level promotion. The migration should be made explicit and lossless. None of this warrants restoring the canceled proposal's independent ticking or unrelated authoring shortcuts.

**Evidence and limits**

The original design was read through `sase artifact read`. Code claims above were independently inspected in local checkouts opened through `sase repo open`: bob-cli at `020ad4e6207f81fd9c633db21c48e1b8efdf3bba`, bob-plugins at `4e0ff78b1534e62a55e86f8c94632bc76f3cc84b`, and bob-mac-capture at `f11262242cd253bf32f07a5a2fa25c94efb0f1fc`. Research checkout base: `9a1c29dd12062ffa28e53ddd5599e49c700dd8e5`. This was a design/code review; no implementation tests, live-vault migration, or fresh bead-status verification were performed. The original report's vault and canceled-epic observations remain attributed to that report.

Audited memory reads covered Task Drawer, Capture Bullets Mirror The Task Block, A Jump Successor Lands Last And Parks The Walk, and Bob Mac Capture Is A Thin Client Of bob. The source links below identify the inspected revisions; they were not used to bypass local repository access.

- [C1: task child classifier][C1], especially `TaskChildKind` and `classify_direct_children`.
- [C2: authored depth model][C2], plus [`draft.rs` lines 938–995](https://github.com/bobs-org/bob-cli/blob/020ad4e6207f81fd9c633db21c48e1b8efdf3bba/src/native/capture_language/draft.rs#L938) and [`first_level_groups`](https://github.com/bobs-org/bob-cli/blob/020ad4e6207f81fd9c633db21c48e1b8efdf3bba/src/native/capture_language/drawer_bullet.rs#L373).
- [C3: split planner][C3], including `collect_candidates`, child rebasing, moved-anchor repair, and `choose_placement`.
- [C4: project schedule writer][C4], plus [`parse_task_line`](https://github.com/bobs-org/bob-cli/blob/020ad4e6207f81fd9c633db21c48e1b8efdf3bba/src/native/projects/scan.rs#L1319) and [`finish_close_node`](https://github.com/bobs-org/bob-cli/blob/020ad4e6207f81fd9c633db21c48e1b8efdf3bba/src/native/task_complete/tree.rs#L641).
- [C5: checkbox cycler regex][C5], plus [`freshnessTaskStatus`](https://github.com/bobs-org/bob-plugins/blob/4e0ff78b1534e62a55e86f8c94632bc76f3cc84b/plugins/bob-ledger-tools/src/080-freshness-placement.js#L153).
- [C6: Mac indentation helper][C6], plus [`PlainTextPaste.parsePlaceholderLine`](https://github.com/bobs-org/bob-mac-capture/blob/f11262242cd253bf32f07a5a2fa25c94efb0f1fc/Sources/BobMacCapture/PlainTextPaste.swift#L85).
- [C7: project seed builder][C7].
- [C8: drawer classifier and project-section representation][C8], particularly `project_h2_drawers` at line 581, `drawers` at line 1317, and `drawer_key` at line 75.

[C1]: https://github.com/bobs-org/bob-cli/blob/020ad4e6207f81fd9c633db21c48e1b8efdf3bba/src/native/task_children.rs
[C2]: https://github.com/bobs-org/bob-cli/blob/020ad4e6207f81fd9c633db21c48e1b8efdf3bba/src/native/capture_language/model.rs#L908
[C3]: https://github.com/bobs-org/bob-cli/blob/020ad4e6207f81fd9c633db21c48e1b8efdf3bba/src/native/task_split/plan.rs
[C4]: https://github.com/bobs-org/bob-cli/blob/020ad4e6207f81fd9c633db21c48e1b8efdf3bba/src/native/projects/edits.rs#L73
[C5]: https://github.com/bobs-org/bob-plugins/blob/4e0ff78b1534e62a55e86f8c94632bc76f3cc84b/plugins/task-status-cycler/src/010-core.js#L13
[C6]: https://github.com/bobs-org/bob-mac-capture/blob/f11262242cd253bf32f07a5a2fa25c94efb0f1fc/Sources/BobMacCapture/CapturePanelController.swift#L1512
[C7]: https://github.com/bobs-org/bob-plugins/blob/4e0ff78b1534e62a55e86f8c94632bc76f3cc84b/plugins/bob-navigation-hotkeys/src/110-project-seed.js
[C8]: https://github.com/bobs-org/bob-cli/blob/020ad4e6207f81fd9c633db21c48e1b8efdf3bba/src/native/capture_drawers.rs
