# Compact task dependency links and a vault-wide dependency picker

Researcher: **cdx** (`research.3f.cdx`)  
Date: 2026-10-02  
Scope: independent design research; no implementation or vault migration performed.

## Direction

This is a good change. Embedded task trees make a prerequisite list expensive to scan and can make a dependency look like a task owned by its parent. A compact row of named links expresses the relationship more clearly. The key condition is that the redesign must preserve the dependency engine, rather than merely remove exclamation marks.

I recommend **one explicitly labeled child row of ordinary, aliased block links**, edited through **Ctrl+Shift+P → Dependencies**, with a persistent picker that fuzzy-searches tasks throughout the vault. Keep Tasks-compatible `id` and `dependsOn` metadata as the semantic authority. Make the row its synchronized, navigable presentation, and ultimately derive task-chain promotion from the same metadata graph. Treat styling, selection, identity, and reconciliation as parts of the feature.

Two adjustments are particularly important: allow the single Markdown row to wrap visually, and preserve the existing meaning of dependencies as prerequisites to actionability, without introducing a hard prohibition against completing the parent manually.

## What the current implementation actually does

I inspected the current bob-cli workspace and independently opened bob-plugins through `sase repo open`. I also opened the upstream Tasks and official Obsidian developer-documentation repositories through that audited workflow. I did not consult any peer report, peer transcript, or peer findings. Sources and revisions are listed near the end.

| Finding | Evidence | Design consequence |
| --- | --- | --- |
| Dependency presentation and dependency status currently use different representations. | bob-cli `dependency_edges()` scans sole transcluded direct-child block links; `task_dependency_states()` reads Tasks IDs. [L1], [L2] | A format-only change would preserve Blocked status but break prerequisite rank propagation. |
| A task can be Blocked for dependencies, a future schedule, or both. | `docs/task-status-hooks.md`, “Derived Blocked Status”; audited `decisions:task-lanes-are-sticky`. [L3], [M1] | Removing the final dependency must not blindly set the task to Ready. |
| Ctrl+Shift+P already has dependency selection, but its candidates are local to one document. | `showLocalTaskValueStage()` calls `createBulletPropertyLocalTaskItems(this.getEditorContent(), …)`. [L4] | Add a whole-vault inventory; widening a link formatter is insufficient. |
| The current dependency picker excludes closed tasks from candidate generation. | `getOpenLocalTasks()`. [L4] | Existing completed, canceled, missing, or hidden dependencies need a separate management list so removal stays easy. |
| Dependency editing through an ordinary Task Link is currently suppressed. | `createLinkPickerPropertyItems()` hides `dependsOn`; the modal refuses that stage in link mode. [L4] | Supporting the selected task from a link requires an explicit new target-resolution path. |
| The older compact row is recognized as legacy, but new formatting emits one embed per dependency. | `DEPENDENCY_NAVIGATION_BULLET_RE`, `formatDependencyNavigationBulletWithMarker()`. [L4] | Reuse the existing managed-child conventions, but replace the limited legacy parser. |
| Generic unlinking deliberately refuses dependency embeds. | block-id-prompt `isDependencyTransclusionLink()`. [L5] | Plain dependency links need the same semantic protection, or unlinking will leave stale metadata. |
| Task closing already distinguishes plain links from embeds. | task-status-cycler behavior and README: plain links close the root; embeds can close a transcluded tree. [L6] | Normal dependency links reduce accidental tree-wide completion, but this behavior change must be explicit. |
| Moves and archiving already repair block links and dependency IDs together. | bob-cli collect-done link repair; navigation task-move identity rewriting. [L7], [L4] | The new row should use ordinary repairable block links and participate in existing move contracts. |

The compact form has history: bob-plugins commit `982ac8b6e884a3ee04142c1b812a1b079746075c` changed managed links into individual transcluded bullets on 2026-07-11. Its commit message documents synchronization and migration, but does not establish a usability rationale. I would not infer that the old compact layout was rejected on design grounds. [L8]

### Small executable checks

I loaded bob-navigation-hotkeys' exported helpers with the same minimal Obsidian/CodeMirror stubs used by its Node tests. These read-only assertions passed:

```text
tryDependencyId("projects/Alpha.md", "review")
  → projects__Alpha__review
tryDependencyId("projects/My Project.md", "review")
  → null
tryDependencyId("a/b.md", "review")
  → a__b__review
tryDependencyId("a__b.md", "review")
  → a__b__review
legacy compact row with [[#^a]] and [[#^b]]
  → recognized
legacy compact row with cross-note aliased links only
  → not recognized
```

The current path scheme has both a character restriction and a flattening collision. This is stronger evidence than an inferred risk. Also, existing recognition of a compact row does **not** mean the desired cross-vault, aliased version already works. [L4]

I did not scan Bryan's live vault, measure its size, test a new UI in Obsidian, or run a migration. Performance goals and presentation below are proposals, not measured results.

## Critique and explicit requirement adjustments

**Keep dependency management small and directional.** A dependency should mean “this task needs that prerequisite resolved.” Avoid using it to express a related note, a nice-to-have sequence, a project hierarchy, or a task merely worth doing earlier. Those weaker relationships belong in ordinary prose links. Overusing hard dependencies creates a backlog that looks blocked even when useful work is possible.

**Keep all dependencies as an AND relation.** A waits for every listed open prerequisite. Do not introduce alternatives, lag times, percentages, or a graph canvas in this change. These add ambiguity to a feature whose main purpose is faster selection and clearer reading.

| Requested idea | Proposed refinement | Why |
| --- | --- | --- |
| All dependency links on a single line | One physical Markdown child row; permit natural visual wrapping | A strict unwrapped row is unreadable with long titles, narrow panes, or many dependencies. |
| Dependencies must be completed before A is unblocked | Preserve the existing Tasks status contract: open prerequisite statuses block; terminal statuses cease blocking | Cancellation currently ceases to block. Requiring only Done would be a separate workflow change. |
| Easy adding/removing | Existing dependencies stay visible independently of eligibility for new additions | A completed task must not disappear from the removal UI. |
| Ctrl+Shift+P support | Retain the current property picker; label the row “Dependencies” and search it with “dep”, “dependsOn”, and “blocked by” | Users should choose a relationship rather than understand a storage field. |
| Entire-vault fuzzy search | Search the full eligible task inventory immediately; locality only affects ranking | Do not require choosing a note first or discovering a hidden “search everywhere” mode. |
| Any area/project note file | Repair the ID restrictions/collisions, or openly limit the initial release | The existing encoder cannot meet an unrestricted “any note” promise. Renaming users' notes is not an acceptable workaround. |
| Beautiful compact links | Store readable aliases and add restrained state styling, hover preview, and an edit affordance | Bare `[[note#^opaque-id]]` links save space but lose the task description previously supplied by the embed. |

An additional boundary: **unblocked does not mean automatically completed, and dependency metadata is not a completion lock**. Keep explicit parent completion available. A notice about outstanding prerequisites could be considered later, but changing every task-completion gesture into an enforcement mechanism is outside this redesign.

## The proposed Markdown contract

Use the existing managed-child vocabulary, with ordinary block links and human-readable display aliases:

```markdown
- [?] #task Ship release [dependsOn:: dev__write-tests, projects__Release__review] ^ship
  - 🔗 **DEPENDS ON:** [[dev#^write-tests|Write tests]] · [[projects/Release#^review|Review release]]
  - 🛠️ **WORK LOG**
    - *2026-10-02* — Drafted the release checklist
```

The example's IDs use the current legacy format to show compatibility; a new identity codec discussed below need not change existing valid IDs. The full paths live in the targets, while the aliases supply the compact labels. Obsidian supports aliased block links and native hover previews. [E1]

This stays readable with the enhancement disabled:

```text
☐ Ship release
  🔗 DEPENDS ON: Write tests · Review release
```

### Recognition and serialization

Define a task dep link by **its relationship context**, not by a new URI scheme or by every plain link beneath a task.

- Exactly one canonical dependency row belongs directly to its task. Nested rows belong to their own nearest task; logs and examples never donate edges to a parent.
- Only ordinary wiki block links in that row are dependency-link tokens. Note links and heading links are invalid dependency targets.
- Serialize new cross-note links with vault-relative paths without `.md`; serialize same-note targets as `[[#^id|Title]]`. Resolve and deduplicate using the actual note path plus block ID, never alias text, basename alone, or block ID alone.
- Accept existing safe list markers/indentation; preserve line endings and final-newline state. Canonical output uses the marker/indent of the row it replaces, or the established task-child indentation for a new row.
- Accept the prior `DEPENDS ON`/`DEPENDENCIES` labels and separators as migration input. Write one canonical label and separator. Emoji helps identification visually but must not be the only machine discriminator.
- Tokenize block links first, then validate the surrounding row grammar. Do not split the row on commas, bullets, or middle dots that may occur inside aliases.
- Preserve the user's dependency order. Append newly added dependencies in selection order; removing and re-adding moves an item to the end. Do not reorder the list every time a target's status changes.
- Preserve safe user aliases. Newly created aliases use a concise cleaned task title. Resolve current titles dynamically for preview and tooltips; avoid vault-wide rewrites whenever a title changes.
- Escape or normalize structural characters/newlines when generating aliases. Do not copy arbitrary task Markdown into raw HTML. Put rich text in a safe renderer or text nodes.
- Adding the first dependency creates the row. Removing the final dependency removes the row and empty `dependsOn` field. No persistent “none” row is needed.
- Preserve unrelated child bullets. A row with attached authored descendants or mixed content is a migration conflict, not disposable formatting.

I prefer the established **DEPENDS ON** label over a new **BLOCKED BY** marker. A retained dependency can be satisfied, so “Blocked by” would misdescribe the full relationship list. The rendered status summary can still say “1 remaining” or “2 unresolved.”

## The dependency picker

### Default flow

1. Select task A and press Ctrl+Shift+P.
2. Choose **Dependencies**. Open a modal titled **Dependencies for Ship release** with the source note beneath the title.
3. Present current dependencies at the top with remove buttons. Focus a search field whose placeholder is **Search tasks across your vault…**.
4. Fuzzy-search task descriptions and paths. Display each result on two lines: task title, then note path and task status. Show an explicit checked state for relationships already selected.
5. Toggle additions/removals without closing the modal. Maintain a draft set while the user searches for more tasks.
6. **Apply** commits the set; **Cancel** discards the draft. Reopen on the same task with the existing set selected.

A schematic view:

```text
Dependencies for Ship release
projects/Release

DEPENDENCIES                                      2 selected
[ Write tests           dev                  × ]
[ Review release        projects/Release     × ]

Search tasks across your vault…  sec review

  ☐ Security review
    projects/Security · Ready

  ☑ Review release
    projects/Release · Next

↑↓ move    Enter toggle    Ctrl+Enter apply    Esc cancel
                                  [Cancel] [Apply 2 changes]
```

This is a staged multi-selection editor. Explicit Apply/Cancel behavior avoids a modal that looks cancelable but writes every intermediate click. Show the same draft changes in the selected list and search results; removal must not require re-finding an item.

### Keyboard and pointer behavior

| Action | Behavior |
| --- | --- |
| Up/Down or existing Ctrl+N/P picker navigation | Move the result highlight |
| Enter | Toggle the highlighted relationship; keep the modal and search query open |
| Ctrl+Enter | Apply the draft and close |
| Escape | Cancel without changing task text or allocating IDs |
| Click a result/check control | Toggle it |
| Click a selected item's remove button | Stage removal |
| Activate a separate preview/open control | Preview the exact target without changing the draft |

Do not bind an unmodified Space in the search input to selection; users need spaces in queries. Include visible Apply/Cancel buttons and accessible labels instead of relying only on shortcuts. Expose **Manage task dependencies** as an independently callable command, without assigning a conflicting default hotkey.

The current dependency picker is desktop-only; this report does not claim otherwise. Pointer controls and wrapping keep a later mobile entry point feasible, but mobile support should be a deliberate acceptance requirement if desired.

### Candidate and removal rules

New candidates include all recognized open Tasks tasks, including Blocked tasks, across active vault Markdown notes. Area/project tasks are the central use case, but folder location alone must not determine eligibility. Honor the Tasks global filter and configured status registry rather than assuming every checkbox is a task or every non-space symbol is terminal.

Exclude the source task and code-fenced examples. Do not index task-looking examples under templates or conflict copies as ordinary candidates. Default new additions can omit `#hide` tasks, with a clearly visible **Include hidden tasks** option. Existing hidden dependencies remain removable. Archives are not default new-candidate pools, but existing archived targets still resolve for display and history.

Pin existing dependencies even when Done, Cancelled, hidden, missing, archived, or ambiguous. Show their status and full path. A missing target becomes an unresolved entry keyed by the stored ID; its remove control still works. Keep the distinction between a terminal target and a broken reference visible.

At an empty query, show current relationships followed by useful nearby candidates; at a nonempty query, score the whole eligible vault inventory. Use title match quality first and note path matches second, with deterministic tie-breaking and a modest locality boost. Highlight matching characters. Equal task titles must remain distinguishable by path and status.

For counted Ctrl+Shift+P, retain the existing union/intersection distinction: an item can be on all selected sources, some, or none. Use explicit **Add to all**/**Remove from all** actions for mixed selections, validate every resulting edge, and display the source count. Single-task editing should land first; batch support should follow without changing the default interaction.

### What “currently selected task” means

- On the task line: edit that task.
- On its managed dependency row: edit the owning task, even when the caret is within one of the links. This prevents editing the prerequisite's dependencies by accident.
- On an ordinary dedicated Task Link elsewhere: optionally edit the uniquely resolved linked task, with its title/path clearly named. This expands the existing link-session behavior intentionally.
- On prose containing multiple links, a selection spanning different tasks, or ambiguous buffers: refuse the ambiguous action with a short explanation. Do not guess.

A small edit button at the end of the enhanced row can open the same editor. It should appear on hover/focus and stay keyboard-accessible. Removing a prerequisite is a relationship operation; completing it remains an explicit task operation.

## A restrained visual design

Use a muted chain icon and a small label, with shallow rounded link chips, comfortable gaps, and ordinary theme typography. An unresolved relationship gets a warning icon and text; a resolved open prerequisite gets a quiet open-state indicator; a Done target gets a check and muted text. Distinguish Cancelled from Done rather than representing both as successful completion. Use color as reinforcement, never as the sole state signal.

A derived summary such as **1 remaining · 1 done** is useful, but should not be written into Markdown. If a target cannot resolve, say **1 unresolved**, not **all dependencies complete**. Preserve all stored links even when finished; soft wrapping and muted terminal chips are preferable to deleting history automatically. A later “hide satisfied” presentation preference can collapse satisfied chips without deleting relationships, but it is not necessary for the first release.

Use native link behavior wherever possible: opening the correct block, modifier navigation, context menus, and hover preview. Render the concise alias by default; show the current full task text and path on preview. Native links already solve much of the beauty problem. [E1]

Implement enhancement through a Markdown postprocessor for Reading view and a CodeMirror 6 extension for Live Preview. These are separate render surfaces; styling Reading-view HTML does not implement an editor widget. Keep Source mode plain and expose real syntax when the caret edits the row. Do not blanket-hide link syntax with CSS or turn the entire row into one opaque replacement widget. [E2]

A useful first visual milestone is the readable aliased Markdown row and polished picker; a release claiming enhanced chips should validate both Reading view and Live Preview. Screen-reader labels, visible focus, high contrast, light/dark themes, narrow panes, and reduced motion deserve equal attention to decorative polish.

## Keep one semantic graph

### Authority and synchronization

Keep `id`/`dependsOn` values compatible with Tasks. Do **not** write wikilinks inside `dependsOn`; its values are task IDs. Replacing the existing dependency backend with link parsing would require replacing Tasks queries, completion recovery, move repair, and several plugin consumers. It is a poor trade for this feature. [L2], [E3]

The row and metadata are two persisted representations, so merely calling one a projection does not eliminate drift. Define ownership and conflict handling explicitly:

1. Semantic readers consume Tasks metadata. The row supplies navigation, display labels, and order.
2. Applying a picker draft computes target-ID changes, the parent's metadata, and its row from one validated dependency set.
3. A supported direct edit of the managed row in Obsidian can be treated as edit input: validate the new target set, update metadata, then format the row in the same operation. Do not interpret ordinary child links or prose as dependencies.
4. A supported metadata edit through Tasks can regenerate the managed row from the resulting IDs. Additions/removals reconcile; aliases and order should be preserved where possible.
5. When the loaded document already has conflicting representations and the responsible edit is unknown, preserve both and show **Dependency list needs repair**. Offer **Use linked tasks** and **Use stored dependencies**, previewing the effect. Do not silently union the sets or overwrite one.
6. CLI status hooks must never infer removal because a visible row is absent, especially while the plugin is disabled or a user is editing. They continue reading metadata and report disagreement where detected.

A blank row deliberately cleared during a supported edit is different from an absent row in an imported note. Event origin, a last validated snapshot, and operation boundaries matter. Handle IME composition and partially typed wikilinks without interpreting every keystroke as a complete set replacement.

If bidirectional live editing is too large for v1, ship picker editing plus an explicit **Synchronize dependency row** action and visible mismatch feedback. Document that manual row edits require synchronization. That is a justified scope reduction; silently displaying an edited row as authoritative while retaining different metadata is not.

### Rank propagation and state recovery

The long-term graph for prerequisite traversal should resolve `dependsOn` IDs to task records, then to canonical note-path/block identities. Use that graph for rank propagation as well as blocker explanations. A link's embed flag must no longer carry scheduling semantics. [L1], [L2]

During transition, accept legacy sole embeds so pre-migration notes keep working. New compact rows can supply traversal edges only where they agree with the stored IDs; surface mismatches. Once migrated, stop using embed presence as a semantic switch. Moving promotion to metadata also makes metadata-only dependencies participate; this is an explicit behavior broadening that needs regression coverage and rollout review.

Preserve existing sticky-lane rules, strongest-rank merging, cycle-safe traversal, direct-only Today membership, and future schedules. Adding a dependency may block the parent. Removing one preserves other blocker reasons; only when none remain should existing recovery logic decide Ready, Next, or In Progress. No hidden previous-lane field is introduced. [L3], [M1]

Do not add stronger “only Done satisfies” rules in the picker while retaining Tasks-compatible cancellation semantics in the backend. For existing missing IDs, retain the documented Tasks behavior that they do not themselves block, but show unresolved health feedback prominently. Changing that to fail-closed Blocked would require a coordinated query/status-policy change, and should be decided separately. [L2], [E4]

### Safety of gestures

Extend block-id-prompt's dependency-context guard to ordinary links on the managed row. Ctrl+Shift+Enter should route to dependency management or explain that relationships are edited there; it must not erase a chip while leaving `dependsOn` intact. [L5]

Ctrl+Enter on a selected ordinary dep link can retain the ordinary Task Link root-completion behavior; it should never recursively complete a prerequisite tree because the link was formerly an embed. A parent completion still completes the parent by the normal rules. Update legacy `!` handling so it cannot toggle a managed row's representation and thereby toggle the dependency relation accidentally. Keep legacy singleton behavior as a migration adapter; route new row management through the picker. [L4], [L6]

### Cycles

Reject a proposed A → B edge if B already reaches A, and reject self-dependencies. Check the resulting batch graph, not each proposed edge against only the old graph. Show a readable cycle path such as **Ship release → Review release → Ship release**. Existing cycles are surfaced for repair; do not delete them automatically. Always allow removals that reduce a bad graph, including removal of an unresolved relationship.

## Vault inventory, identity, and reliable writes

### Search inventory

Build an in-memory index from `vault.getMarkdownFiles()`, taking unsaved open buffers as the current content. Reuse the existing open-buffer snapshot discipline used by interactive recovery. A path whose open views disagree is an ambiguity to resolve, not a reason to choose the last buffer visited. [L4], [E5]

Use create/modify/delete/rename/editor-change events to refresh affected records, with bounded debounce and cancellation. A result carries file identity, current path, block ID when present, source-line evidence, cleaned title, status type, IDs, dependency IDs, and a content/version fingerprint. File-plus-line alone is not durable identity. Tasks lacking block IDs remain searchable and use a provisional snapshot identity until Apply.

Keep filtering in memory while typing. Do not rescan every vault file on every keystroke. The public Obsidian fuzzy-search APIs can supply scores and matched positions, but their own documentation cautions about large candidate sets. Prepare the query once, retain the top results, and render a bounded result window. If measurements require it, score in cancellable chunks or a worker; never discard distant notes just to meet latency. [E6]

Suggested targets, to be tested on the actual vault: warm-search p95 below 50 ms at 10,000 task records, immediate keyboard response while cold indexing proceeds, and at most roughly 50–100 mounted result rows. These are acceptance goals, not claimed benchmarks.

### IDs: meet the “any note” requirement honestly

The current encoder flattens slash-separated paths with `__` and allows only Tasks-safe characters. My helper checks confirmed that spaces fail and `a/b.md` collides with `a__b.md`. [L4], [L7]

Do not create a relation when the chosen identity resolves to more than one task. A full-path wikilink prevents navigation ambiguity but does **not** repair a colliding Tasks ID.

For unrestricted filename support, introduce a versioned, injective ASCII codec. One concrete option for newly allocated IDs is:

```text
bob-v2-<hex of UTF-8 normalized vault-relative Markdown path>-<block-id>
```

Hex preserves spaces and Unicode without violating Tasks' ID alphabet, and encoding the whole path avoids slash/underscore collisions. The resulting IDs may be long, which is acceptable because the user sees aliases. Preserve valid existing identities until a targeted repair or move; do not mass-migrate IDs just to obtain a shorter row. Check the full vault for collisions, including authored IDs that happen to resemble the new namespace.

This change must be shared by JavaScript identity normalizers, move/rename handling, Rust archive repair, and any ID derivation helper. Older normalizers must not “correct” a v2 ID back into the broken legacy format. Use cross-language fixtures. An alternate opaque stable-ID scheme could also work, but would change Bob's present path-based identity convention more substantially; I favor the narrow codec fix for this feature.

If the team defers the codec, explicitly label v1 as supporting the current representable note paths and refuse unsupported targets visibly. That limitation falls short of the unrestricted requirement and must not be hidden by advertising “whole-vault search.”

### Applying changes

Collect and validate the entire draft before writing. Resolve current source and targets, verify they still refer to the selected tasks, validate status/IDs/cycles, and only then plan edits. Prompt for missing block IDs at Apply using the existing suggested-ID convention; no target IDs should be written merely because the user highlighted a search result. Preserve the existing prompt with a sensible suggested value and Enter acceptance rather than forcing users to type every ID. Automatic acceptance could be a later explicit preference.

Same-note changes to target IDs, parent fields, and the row should be one editor transaction. Open target notes must be edited through their buffers. For closed notes use guarded `Vault.process()` writes; its atomicity is per note, not across a group of notes. [L4], [E5]

For cross-note additions, prepare and validate target identity edits first, then commit the parent's metadata and row together. If target preparation fails, leave the parent unchanged. If parent commit fails afterward, an unused target ID is tolerable; a displayed dependency pointing at an unprepared target is not. Revalidate after asynchronous prompts and reads. Do not write stale full-file snapshots over newer buffers.

Promise one undo operation for the parent edit, not a fictitious vault-wide undo transaction. Undo may leave harmless allocated target IDs; a compensation step may remove only an ID that is provably unchanged and unused. Serialize conflicting dependency operations, and report partial preparation accurately rather than claiming full success.

## Implementation and migration sequence

This is a proposed work sequence, not an approved implementation plan or an instruction to migrate the live vault during research.

1. **Specify the contract and identity policy.** Define row grammar, status semantics, conflict handling, selection ownership, and whether unrestricted paths are a release requirement. Create shared fixtures before changing writers.
2. **Introduce the dependency model and index.** Centralize task resolution and dependency-set planning in bob-navigation-hotkeys, with a versioned public API for other plugins where needed. Do not import another deployed plugin's private `main.js` helpers. Rust readers use equivalent fixtures, not runtime plugin imports.
3. **Make all readers compatible.** Teach row-context guards and display parsers about cross-note aliases, keep legacy embeds working, and add agreement-checked traversal for compact rows. Land the coordinated identity changes before emitting v2 IDs.
4. **Deliver the picker and compact writer.** Single-task editing, current-dependency removal, staged multi-selection, full-vault fuzzy results, safe block-ID prompts, and guarded Apply are the core release. Add controlled direct row editing/explicit sync and immediate recovery feedback.
5. **Add visual enhancement.** Reading view and Live Preview share the row model; state summaries remain derived. Validate native link behavior and source-mode editing.
6. **Preview migration.** Extend or replace the existing dry-run-first dependency migration utility. Inspect sole direct-child embeds and legacy compact rows, compare them with metadata, and produce an exact diff plus unresolved/ambiguous/cyclic/mismatched counts. Do not rerun the existing utility unchanged: its formatter still emits embeds. [L4]
7. **Migrate only supported cases.** Convert agreement-confirmed dependencies to one row, preserve finished relationships and aliases, and leave authored descendants, ambiguous IDs, conflicting sets, and unresolvable references for explicit repair. A legacy embed lacking metadata may currently affect promotion without blocking; importing it as `dependsOn` changes behavior and requires an explicitly reviewed migration action.
8. **Verify idempotence and graph behavior.** A second migration should make no changes. Dry-run hooks before/after must show equivalent edges/ranks/blockers for migrated agreement-confirmed relationships. Preserve fenced examples, task blocks, logs, indentation, CRLF, and trailing newline state.
9. **Converge traversal and publish the glossary.** Once readers and writers agree, move promotion to the resolved metadata graph; review the intentional metadata-only behavior broadening. Add the glossary strand and update Task Link wording with the implementation, then run `sase memory init`. If an immutable decision record needs superseding, create a successor and mark the old record under the established policy rather than rewriting its accepted claim.
10. **Deploy through the source repository.** Modify bob-plugins in its linked checkout, then deploy with `bob plugins sync`. Changes made directly in the vault's plugin folders will be overwritten. [M2]

A successful pilot should answer whether dependencies are faster to edit and easier to read, not merely whether the new syntax can be parsed. Try adding prerequisites from two different projects, removing one completed target, following a link to its block, and editing while another note has unsaved changes. Compare the number of interactions and mistakes with today's picker.

## Acceptance checks worth implementing

| Area | Important cases |
| --- | --- |
| Ownership | Parent task; its dependency row; nested tasks; ordinary Task Link; ambiguous multiline selection |
| Parser | Same-note and full-path links; aliases; duplicate basenames; identical block IDs in different notes; separator inside alias; fences; mixed-content rows |
| UI | Add several tasks without reopening; remove terminal/missing/hidden target; fuzzy title/path query; equal titles; visible focus; cancel leaves bytes unchanged |
| Graph | AND blockers; multiple parents; chains; self-edge; new cycle; existing cycle removal; batch-created cycle; strongest-rank promotion |
| Status | Remaining open dependency; final dependency removed but future schedule remains; custom terminal status; canceled target; no hidden previous lane |
| Identity | Space/Unicode paths; slash/`__` collision; duplicate block IDs; authored ID collision; rename; task move; archived Done target; cross-language codec agreement |
| Mutation | Target changes during prompt; unsaved source/target; conflicting open buffers; target failure; parent failure; per-note undo; concurrent operations |
| Migration | Legacy labeled row; legacy embeds with agreeing metadata; embed without metadata; authored child subtree; no overwrite; idempotence; CRLF and final-newline preservation |
| Gestures/rendering | Ctrl+Shift+Enter cannot desynchronize; plain-link root completion; legacy `!`; Reading view/Live Preview/Source mode; native hover/navigation; narrow pane |
| Performance | Actual-vault measurement; large synthetic inventory; cancellable cold indexing; warm search; bounded rendered results |

These tests should exercise behavior and failure cases, rather than merely assert the new formatter's exact output. Existing suites provide useful starting points: navigation hotkeys, task-status-cycler, block-id-prompt, dependency-identity migration, Rust hook structure/sync, collect-done link repair, and task-query parity. [L4]–[L7]

## Proposed glossary memory entry

Add `sase/memory/glossary/task-dependency-link.md` when the contract ships. The following is proposed definition text, not a claim that the feature is already implemented:

> **Task Dependency Link**  
> aka **task dep link**, **dependency task link**
>
> A non-transcluded [[glossary:task-link]] in a task's direct-child **DEPENDS ON** row, identifying one of that task's prerequisites. Several task dep links share one Markdown row, which may wrap visually. Their targets may live anywhere in the active vault. Task dep links provide navigation and a readable view of the task's synchronized Tasks `dependsOn` metadata; an ordinary task link elsewhere does not establish a dependency. All open prerequisites must cease blocking before the task is unblocked, and a future schedule may still keep it Blocked. Edit the relationship set with Ctrl+Shift+P → Dependencies.

Keep syntax details, picker key tables, repair procedures, and identity codec details in product documentation, not the glossary. Update the existing Task Link strand to point to this subtype and remove its now-obsolete sentence defining sole transcluded task children as the dependency convention. Keep the distinct Pomodoro-link meaning intact.

I invoked `sase_memory_write` for this user-requested proposed memory change. I did not change canonical memory during research; doing so would teach future agents a feature that has not been implemented.

## Sources and limits

### Local product evidence

All following files were read from the authorized local checkouts. Public permalinks are supplied for review; no repository source files were fetched through the web tool.

- **[L1]** bob-cli revision `81b45eb9a1a653b9a217625603fb60919abfca7a`: [`src/native/task_status_hooks/references.rs`](https://github.com/bobs-org/bob-cli/blob/81b45eb9a1a653b9a217625603fb60919abfca7a/src/native/task_status_hooks/references.rs#L307), especially `dependency_edges()` and `sole_transcluded_block_reference()`.
- **[L2]** Same revision: [`src/native/task_status_hooks/sync.rs`](https://github.com/bobs-org/bob-cli/blob/81b45eb9a1a653b9a217625603fb60919abfca7a/src/native/task_status_hooks/sync.rs#L678), and `src/native/dataview/tasks/task.rs`, Tasks metadata parsing.
- **[L3]** Same revision: [`docs/task-status-hooks.md`](https://github.com/bobs-org/bob-cli/blob/81b45eb9a1a653b9a217625603fb60919abfca7a/docs/task-status-hooks.md), and `docs/plan.md`, including direct Task Link Today membership.
- **[L4]** bob-plugins revision `ede89d39e45464dac7d66c71dff4a4003eebda64`: [`plugins/bob-navigation-hotkeys/main.js`](https://github.com/bobs-org/bob-plugins/blob/ede89d39e45464dac7d66c71dff4a4003eebda64/plugins/bob-navigation-hotkeys/main.js), especially lines 241–268 (legacy grammar), 1253–1340 (target identity), 1433 onward (formatter), 3391 onward (managed-row collection), 3569 onward (sync plan), 4468 onward (ID encoder), 8179 onward (buffer-aware recovery snapshot), 15380 onward (link-mode suppression), 20000 onward (local candidates), 22248 onward (local picker stage), 25413 onward (`!` synchronization), and 31400 onward (local dependency write). Also `scripts/migrate-dependency-bullets.mjs` and `scripts/test-navigation-hotkeys.cjs`.
- **[L5]** Same revision: [`plugins/block-id-prompt/main.js`](https://github.com/bobs-org/bob-plugins/blob/ede89d39e45464dac7d66c71dff4a4003eebda64/plugins/block-id-prompt/main.js#L2876), dependency-link guard and task-link picker.
- **[L6]** Same revision: [`plugins/task-status-cycler/main.js`](https://github.com/bobs-org/bob-plugins/blob/ede89d39e45464dac7d66c71dff4a4003eebda64/plugins/task-status-cycler/main.js), dependency recovery/normalization; `README.md` command behavior.
- **[L7]** bob-cli revision above: [`src/native/collect_done/link_repair.rs`](https://github.com/bobs-org/bob-cli/blob/81b45eb9a1a653b9a217625603fb60919abfca7a/src/native/collect_done/link_repair.rs), `transform.rs`, and `tests/unit.rs` (including unsupported-space-path coverage).
- **[L8]** bob-plugins [`982ac8b6e884a3ee04142c1b812a1b079746075c`](https://github.com/bobs-org/bob-plugins/commit/982ac8b6e884a3ee04142c1b812a1b079746075c), commit message inspected locally.
- **[M1]** Audited memory: `glossary:task-link`, `decisions:task-status-is-derived`, and `decisions:task-lanes-are-sticky`, read with `sase memory read`.
- **[M2]** Audited `obsidian.md` memory and linked bob-plugins `AGENTS.md`, including source-repository deployment and single git-based vault sync.

### Upstream primary sources

- **[E1]** [Obsidian Internal links](https://obsidian.md/help/links): native block links, aliases, full vault-relative targets, and hover previews. Browser-verified.
- **[E2]** Official developer docs revision `c56c7e770ba25dd0ea392aacf4588f9425970d36`: [Editor extensions](https://github.com/obsidianmd/obsidian-developer-docs/blob/c56c7e770ba25dd0ea392aacf4588f9425970d36/en/Plugins/Editor/Editor%20extensions.md) and [Markdown post processing](https://github.com/obsidianmd/obsidian-developer-docs/blob/c56c7e770ba25dd0ea392aacf4588f9425970d36/en/Plugins/Editor/Markdown%20post%20processing.md), read locally.
- **[E3]** Tasks revision `692e965ecbaad197221fae9ddff13f5c5fa6ece6`: [Task Dependencies](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/692e965ecbaad197221fae9ddff13f5c5fa6ece6/docs/Getting%20Started/Task%20Dependencies.md), read locally; [official dependency filters](https://publish.obsidian.md/tasks/Queries/Filters), browser-verified. Supports ID alphabet, dependency direction, and status semantics.
- **[E4]** Same Tasks revision: [`Task.isBlocked()`](https://github.com/obsidian-tasks-group/obsidian-tasks/blob/692e965ecbaad197221fae9ddff13f5c5fa6ece6/src/Task/Task.ts#L559), read locally; confirms missing IDs do not themselves block.
- **[E5]** [Obsidian Vault API guide](https://docs.obsidian.md/Plugins/Vault), browser-verified and checked against the official local docs; explains vault enumeration, cached reads, and per-file `process()` semantics.
- **[E6]** Official developer-docs revision above: [Modals](https://github.com/obsidianmd/obsidian-developer-docs/blob/c56c7e770ba25dd0ea392aacf4588f9425970d36/en/Plugins/User%20interface/Modals.md) and [`prepareFuzzySearch`](https://github.com/obsidianmd/obsidian-developer-docs/blob/c56c7e770ba25dd0ea392aacf4588f9425970d36/en/Reference/TypeScript%20API/prepareFuzzySearch.md), read locally. Use these public primitives or their scores inside the existing custom picker shell; a plain FuzzySuggestModal alone does not provide staged multi-selection.

Some multiword Obsidian Publish URLs did not resolve correctly through the browser tool; those details were verified from official repositories instead. No claim about Bryan's installed Tasks/Obsidian version, actual vault scale, or performance follows from upstream HEAD alone. Recommended behavior is distinguished throughout from current-source findings.

## Recommended solution

Build **Ctrl+Shift+P → Dependencies** as a staged, vault-wide fuzzy multi-selector with existing relationships always removable. Write **one direct-child `🔗 **DEPENDS ON:**` row of ordinary aliased block links**, allow visual wrapping, and enhance it with restrained state-aware links and native previews. Preserve **Tasks-compatible metadata as the semantic authority**, and converge blocker calculation and prerequisite promotion on its resolved graph.

Ship the readable row and reliable picker first, with explicit synchronization/repair behavior. Include the identity-codec fix if “any area/project note file” is unrestricted; otherwise disclose the narrower first release. Roll out reader compatibility before migration, preserve relationships and authored content, and publish the new **Task Dependency Link / task dep link** glossary strand when the contract is implemented. This delivers the requested simplicity and beauty while protecting status derivation, cross-note identity, history, and the rest of Bob's task workflow.
