# Obsidian split controls: preserve the tab, make the destination visible

Independent research by **cdx**, 2026-11-15. Prepared for the five-researcher swarm. No peer report, peer transcript, or peer findings were consulted. This is design research, not a completed implementation or a runtime compatibility certification.

**Recommendation:** build a small, one-action window-control mode inside `bob-navigation-hotkeys`. Use `Ctrl+W` as its prefix, `h/l` for directional focus, `H/L` for moving the active tab between groups, and a compact, immediately visible hint that describes the actual result. Preserve the existing leaf and its editor state when moving. An empty source group should disappear through Obsidian's layout lifecycle. Validate that move primitive in the real application before building the polished interaction.

The idea is good: it addresses a repeated spatial operation with a coherent vocabulary. The highest risks are ambiguous semantics and destructive shortcuts disguised as harmless rearrangement. A keyboard binding alone does not solve those risks.

**What the screenshot establishes.** The supplied `~/tmp/screenshots/20261115_171818.png` shows one desktop window with two side-by-side content groups. The left group has multiple tabs, including pinned tabs; `sase_blog` is active there. The right group displays `sase_blog_contents`. The left editor has a visible caret, and the status area indicates Vim normal mode. The example is therefore about moving focus between groups and moving one tab out of a group, not moving an entire operating-system window or relocating all tabs in a column.

Obsidian's terminology supports this distinction: a tab belongs to a tab group; groups can be split, and tabs can be moved between them. A pop-out window is a different container. Use “split” in the compact interface where it is intuitive, but define it as a content tab group in the documentation. [Obsidian Tabs](https://obsidian.md/help/tabs), [Obsidian Workspace](https://obsidian.md/help/workspace).

**The requirements need these explicit adjustments.**

| Original wording or implicit assumption | Recommended clarification | Why |
| --- | --- | --- |
| Both `h` and `l` navigate to “the other” split | `h` focuses left; `l` focuses right; neither wraps. Add `w` for next split, which means “other” with two groups. | Direction should remain trustworthy at boundaries and with three groups. |
| Move the current “window” | Move exactly the active tab/leaf, keeping focus on it. | Moving the whole tab group would unexpectedly carry the pinned tabs in the screenshot. |
| Create the split when necessary | Create an adjacent group only when no destination exists on that side and another tab remains in the source. | Moving the only tab out of the only group cannot produce two useful groups without inventing another tab. |
| Destroy a split | Remove only the source group that becomes empty after a successful move. | This must not close other tabs, delete files, or reset the workspace. |
| Vim-like uppercase commands | `H/L` mean join an adjacent group, or create one when needed—not Vim's exact move-to-extreme-screen-edge semantics. | Joining and collapsing are the user's requested behavior. Document the intentional difference. |
| Unspecified key scope | Default to Vim normal mode and supported non-text content surfaces; preserve text-input and insert-mode behavior. Provide palette commands independently. | `Ctrl+W` has existing editing/close meanings, especially outside macOS Vim normal mode. |
| “Various keys” | Start with `h l H L w v` and cancellation. Defer close, close-others, resize, and four-direction layout mutation. | A small vocabulary is easier to learn, verify, and present beautifully. |

Vim provides useful muscle memory, but its windows are not Obsidian's tab groups. Its lowercase commands move focus spatially; uppercase `H/L` place a window at the far edge; `w` cycles. Borrow the distinction between focus and movement while being honest about the different uppercase behavior. [Vim window reference](https://vimhelp.org/windows.txt.html#window-move-cursor), [Vim window movement](https://vimhelp.org/windows.txt.html#window-moving).

These are recommendations, not inferred user approvals for a later implementation. In particular, the normal-mode scope and boundary behavior should be visible in the proposed feature contract.

**The command contract should be small and exact.** Here `H` and `L` mean Shift+h and Shift+l after the prefix. The prefix uses physical Control on macOS too, never a platform-dependent `Mod` alias.

| Sequence | Palette command / label | Result |
| --- | --- | --- |
| `Ctrl+W h` | Focus split left | Activate the selected tab in the nearest eligible group to the left. |
| `Ctrl+W l` | Focus split right | Symmetric right operation. |
| `Ctrl+W H` | Move tab to left split | Append the same tab to the left destination, or extract it into a newly created left group. Focus follows it. |
| `Ctrl+W L` | Move tab to right split | Symmetric right operation. |
| `Ctrl+W w` | Next split | Cycle groups in stable visual order, wrapping. With two groups this toggles. `Ctrl+W Ctrl+W` is an alias. |
| `Ctrl+W v` | Duplicate tab in new right split | Explicitly create another view. Allow only view types with verified duplication support; preserve the original. |
| `Escape` or `Ctrl+[` while pending | Cancel | Dismiss without changing focus, content, or layout. |

The move operations append after the destination's existing tabs, preserving their relative order. Keep the source tab's pin state. Two tabs displaying the same file remain distinct: never deduplicate by file path. Focus operations activate the tab already selected in the destination group, rather than its first Markdown tab or a globally recent file.

Do not repurpose Bob's existing `move-tab-left` and `move-tab-right` command IDs: they currently reorder tabs inside one group. Add unambiguous IDs such as `focus-split-left` and `move-tab-to-split-left`. Existing bindings should retain their meaning. The current registrations are in [490-plugin-lifecycle.js](https://github.com/bobs-org/bob-plugins/blob/63ff1654a8ffc52c6c1419479a7e3bb17d08f012/plugins/bob-navigation-hotkeys/src/490-plugin-lifecycle.js#L462), and the same-group implementation is in [630-plugin-vim-link-and-leaves.js](https://github.com/bobs-org/bob-plugins/blob/63ff1654a8ffc52c6c1419479a7e3bb17d08f012/plugins/bob-navigation-hotkeys/src/630-plugin-vim-link-and-leaves.js#L362).

The important outcomes can be specified without implementation jargon. An asterisk marks the active tab:

```text
One group:
  [ A  B* ]          L → [ A ] | [ B* ]
  [ A  B* ]          H → [ B* ] | [ A ]

Two groups, move into the existing neighbor:
  [ A  B* ] | [ C ]  L → [ A ] | [ C  B* ]

Move the final tab out of its group:
  [ A* ] | [ C  B ]  L → [ C  B  A* ]
  The empty left group disappears; all three tabs survive.

Only one tab exists:
  [ A* ]             L → unchanged
  Hint: “Nothing to leave here · v duplicates into a new split.”
  [ A* ]             v → [ A ] | [ A* (new view) ]
```

This also works with more than two columns: move into the adjacent eligible group, never leap to the far edge. Do not impose a hidden two-column maximum. At an outer edge, extracting one tab from a multi-tab group can create another column. Extracting the sole tab of that edge group is a no-op. Repeated uppercase movement therefore does not generate a trail of empty groups.

Within mixed layouts, left/right should select a group on that side with vertical overlap; prefer the smallest horizontal gap, then the greatest vertical overlap, then stable layout order. If no such group exists, focus is unavailable. Movement may split the source group locally if it contains another tab; it must not flatten the rest of the workspace. This tie-breaking policy is a proposed product choice, not an Obsidian guarantee. Test T-shaped and uneven layouts so “left” is reproducible.

**The hint should explain consequences while leaving the documents visible.** I recommend one nonmodal card anchored below the active group's tab bar. Render it on the next paint after `Ctrl+W`; do not require a hold or make a fast typist wait for an animation. Approximately 380–440 CSS pixels wide, clamped to the group width with small margins, is a starting point to validate at different zoom levels.

An illustrative state, with the right-hand singleton focused:

```text
┌────────────────────────────────────────────────┐
│ Splits                                 Ctrl W  │
│ [ Left · 3 tabs ]      [ Right · 1 tab · here ] │
│                                                │
│ h  Focus left          l  Focus right — edge    │
│ H  Move left           L  Move right — edge    │
│    closes this split                           │
│                                                │
│ w  Next split          v  Duplicate right       │
│ Esc  Cancel            Shift moves the tab      │
└────────────────────────────────────────────────┘
```

Unavailable rows remain visible with a readable reason. For a multi-tab source at the right edge, the `L` row changes to “New right split”; for an existing neighbor it reads “Move right”; for a last-tab transfer it adds “closes this split.” These labels come from the same action planner that executes the command. The hint must never promise one operation while the handler performs another.

Use the existing theme's background, border, radius, shadow, and accent variables. Give keycaps consistent alignment; use small directional icons as supplements to text. A miniature layout row can show group counts and the current group without copying long note titles. On wide layouts, show the immediate neighbors and “3 of 5” instead of shrinking every group into unreadability. Use one accent for the current group, not task-status colors, which already carry meaning in Bob.

Keep document focus and caret unchanged while the card is pending. Do not dim the whole app or turn the prefix into a searchable command palette. A subtle destination-header outline after navigation is enough; successful focus changes need no toast. A move can produce one brief receipt, for example “Moved to left split · right split closed.” Respect reduced motion and use no animated document travel. Escape dismisses immediately.

The card needs an announced status description, readable disabled reasons, non-color state cues, and native theme/high-contrast testing. Expose every action in the command palette for accessibility and remapping. If rows are clickable, clicking a row must execute the captured action rather than whichever tab becomes active from the click. A click outside cancels and continues its ordinary interaction. This is an interaction sketch; no pixel-perfect mockup or accessibility test was performed during this research.

Bob already has a compact Copy card with row availability, key labels, live status, and document-aware rendering. Its visual treatment is a better starting point than introducing a new visual language. Reuse those conventions, not its focus-stealing modal lifecycle. [Copy card implementation](https://github.com/bobs-org/bob-plugins/blob/63ff1654a8ffc52c6c1419479a7e3bb17d08f012/plugins/bob-navigation-hotkeys/src/103-copy-card-modal.js).

**Keyboard ownership is part of correctness.** A prefix controller should have one pending action state per document and one owner for each event. Capture `Ctrl+W` before CodeMirror or Obsidian handles it only when the focus context is eligible. Once captured, neither event should reach Vim's command parser or a native close-tab handler.

On the screenshot's Mac, Control and Command are different keys. Preserve `Cmd+W`. On Windows/Linux, claiming `Ctrl+W` replaces a familiar close-tab action in eligible contexts; make that visible in help. In Vim insert mode, preserve the existing editing behavior. Do not claim the prefix in search inputs, rename fields, task cards, Command Mode, other modals, composition, or embedded web content. A non-Vim text editor should initially keep its existing binding; the palette actions still work. Canvas text editing is an input context even if the enclosing view is supported.

Recognize the suffix with Control released or still held. Distinguish Shift explicitly so Caps Lock alone cannot turn a focus action into a tab move. Ignore pure modifier events. Reject Alt/Meta variants. Suppress auto-repeat for the prefix and layout mutations. Resolve Vim state from the focused editor; a global “last reported mode” can be stale after switching leaves. Do not arm during an unfinished Vim operator or count; counts are outside this first version.

The pending state should not silently expire while the user is reading. Exit after one successful action, Escape/Ctrl+[, outside click, focus transfer, modal opening, document blur, layout invalidation, or plugin unload. An unrecognized printable suffix is consumed and explained in the card; it must not leak into the note as an edit or Vim command. An unrelated modified shortcut can cancel the prefix and retain its normal dispatch. Handle `event.isComposing` and composition start by cancelling rather than capturing text.

Capture the source leaf and document when the prefix opens. Revalidate them before execution. If the user changes the layout while the hint is open, dismiss it with a short “Layout changed; try again” message instead of moving a different tab. Keyboard focus moving to another window must never redirect the operation to that window's globally active leaf.

Existing Bob code documents why a palette binding alone is insufficient: CodeMirror Vim swallows certain chords before Obsidian's dispatcher. Bob already uses guarded capture handlers and event deduplication. Its Vim adapter can also be replaced during vimrc reload. Use these lessons, while avoiding two independent handlers for the same prefix. [Input handling](https://github.com/bobs-org/bob-plugins/blob/63ff1654a8ffc52c6c1419479a7e3bb17d08f012/plugins/bob-navigation-hotkeys/src/610-plugin-jumps-and-counted-keys.js#L378), [Vim registration](https://github.com/bobs-org/bob-plugins/blob/63ff1654a8ffc52c6c1419479a7e3bb17d08f012/plugins/bob-navigation-hotkeys/src/620-plugin-dash-and-vim-jumps.js#L258).

The upstream Vimrc Support plugin can map a full `<C-w>...` sequence to an Obsidian command, but that alone does not supply this context-aware prefix hint or non-editor behavior. Its README even uses `<C-w>h` for a split example, illustrating why the deployed vimrc needs a conflict audit rather than assumptions. I inspected upstream source, not Bryan's live vimrc or hotkeys file. [Vimrc Support mapping example](https://github.com/esm7/obsidian-vimrc-support/blob/1ff5d97afcf3161f202aa460697233d550f6aa3f/README.md#L55).

**The central implementation risk is moving a leaf without replacing it.** The inspected official API declaration, package version 1.14.4 at commit `879c936660fcc45c90ee28ea6b4ef7068006477c`, provides:

| Public surface | Suitable use | Important limit |
| --- | --- | --- |
| `WorkspaceLeaf.parent`, `getRoot()`, `getContainer()` | Identify group and owning workspace container | Do not confuse a sidebar with the central content area. |
| `setActiveLeaf(leaf, {focus: true})` | Focus the selected destination tab | Must target the source document's group. |
| `createLeafBySplit(leaf, direction, before)` | Create a left/right adjacent group using a placeholder leaf | Creates a new leaf; does not move the existing one. |
| `duplicateLeaf(...)` | Implement explicit duplication | A duplicate is not the original editor instance. |
| `getViewState()`, `getEphemeralState()` | Observe or restore supported state when appropriate | These declarations do not promise serialization of undo history or arbitrary plugin state. |
| `detach()` | Close a leaf | Do not call it on the moving source tab. |
| `requestSaveLayout` | Request persistence after layout mutation | Saving a layout does not prove an in-memory move preserved state. |

The public declaration does not expose a general move-leaf-between-groups operation. Its `createLeafInParent` signature also names `WorkspaceSplit`, while desktop leaf parents are documented as `WorkspaceTabs`; runtime conventions should not be mistaken for a clean public move contract. [Official API declarations](https://github.com/obsidianmd/obsidian-api/blob/879c936660fcc45c90ee28ea6b4ef7068006477c/obsidian.d.ts#L10763), [Leaf declarations](https://github.com/obsidianmd/obsidian-api/blob/879c936660fcc45c90ee28ea6b4ef7068006477c/obsidian.d.ts#L11206).

The community-maintained unofficial declarations for public 1.14.4 identify `WorkspaceItem.setParent`, `WorkspaceParent.insertChild/removeChild`, `WorkspaceTabs.currentTab/selectTab`, and `Workspace.splitLeaf`. These are plausible implementation seams, explicitly unofficial. The declarations establish names and signatures, not the correct call order, lifecycle effects, or losslessness on Bryan's installed version. Notably, `currentTab` is an index, not a leaf. [WorkspaceItem](https://github.com/Fevol/obsidian-typings/blob/9bd1c773d7312bc3a7cc28606548e8439d23be99/src/obsidian/augmentations/WorkspaceItem.d.ts#L158), [WorkspaceParent](https://github.com/Fevol/obsidian-typings/blob/9bd1c773d7312bc3a7cc28606548e8439d23be99/src/obsidian/augmentations/WorkspaceParent.d.ts), [WorkspaceTabs](https://github.com/Fevol/obsidian-typings/blob/9bd1c773d7312bc3a7cc28606548e8439d23be99/src/obsidian/augmentations/WorkspaceTabs.d.ts).

Therefore the first implementation step should be a bounded feasibility experiment in an isolated scratch vault: identify the current native drag/drop or equivalent relocation path, then prove that the same leaf, view, and Markdown editor objects survive both a move and last-tab collapse. Do not invent an internal `moveLeaf` method or assume a method's existence proves its behavior.

A public-API-only recreate-and-close approach is tempting but fails the desired quality bar. Tab Shifter's inspected implementation gathers Markdown leaves, uses iteration order as group order, wraps at edges, creates a destination leaf, detaches the original, and opens its file again. Its source contains sidebar and initial-left-split TODOs. That is useful prior art for the problem, but not the implementation to adopt for this requirement. [Tab Shifter source](https://github.com/jsrozner/obsidian-tab-shifter/blob/23fe91464c2cbd42cd1137e16455a1229eb7a762/src/plugins/TabShifterPlugin.ts), [Documented caveats](https://github.com/jsrozner/obsidian-tab-shifter/blob/23fe91464c2cbd42cd1137e16455a1229eb7a762/README.md).

Likewise, Bob's existing duplicate-tab and same-group array/DOM reordering helpers should not be stretched into cross-group movement. Bob already has a leaf-switch guard addressing save/reload clobbering when changing files, further reason not to turn layout movement into file reopening. [Existing leaf helpers](https://github.com/bobs-org/bob-plugins/blob/63ff1654a8ffc52c6c1419479a7e3bb17d08f012/plugins/bob-navigation-hotkeys/src/630-plugin-vim-link-and-leaves.js), [Leaf-switch guard](https://github.com/bobs-org/bob-plugins/blob/63ff1654a8ffc52c6c1419479a7e3bb17d08f012/plugins/bob-navigation-hotkeys/src/475-leaf-switch-guard.js).

**A contained architecture keeps that risk manageable.**

1. A pure planner takes a snapshot of source identity, eligible groups, selected leaves, geometry, tab order, and supported capabilities. It returns an action, destination, creation/collapse flags, availability reason, and hint copy. Preview and execution use this same plan.
2. A workspace adapter isolates internal access. Enumerate central content leaves of every supported view type, group by parent identity, and restrict to the current document/container. Exclude sidebars, hover editors, other windows, hidden groups, and zero-size geometry. Use live group rectangles for spatial navigation, not the order returned by `getLeavesOfType("markdown")`.
3. A prefix controller owns event handling and cancellation. The hint renders the plan without moving focus. Palette commands call the same planner/executor without needing the prefix.
4. A move executor serializes operations, checks the captured source is still active/attached, and revalidates the topology immediately before mutation. It calls the proven relocation primitive once, lets native layout normalization remove an empty source, restores focus, requests layout persistence, and verifies invariants.
5. An explicit capability boundary disables unavailable moves with a useful explanation. Focus can remain available when movement is unsupported. Do not silently substitute reopening a file, rebuilding the entire layout through `changeLayout`, or raw DOM dragging.

If creating a destination requires a placeholder leaf, remove only that known placeholder after the original tab is successfully installed. Preserve other tabs, group order, and existing width ratios where possible. Split only the source allocation for a new group; do not equalize the whole workspace on every command.

Capture enough operation-local evidence to diagnose and, where proven safe, reverse a failed move. A generic whole-layout rollback is not safe: it can replace live views and overwrite unrelated layout changes. If the layout changes during a transaction, preserve all live leaves and report the failure rather than attempting a broad reconstruction. Test the partial-failure paths before claiming recovery guarantees.

The invariant is stronger than “the same file is still open”: the original leaf occurs exactly once; its pin state and view identity survive; other leaf identities and relative tab order are unchanged; total content-leaf count is unchanged for a move; no temporary empty group remains; and actual keyboard focus lands on the moved view. Markdown undo/redo, selections, cursor, folds, scroll, and navigation history must survive in real-app tests. PDF page/zoom and Canvas viewport state need their own checks. Generic third-party views require an explicit tested-support policy, not an unconditional promise.

Keep this work in the plugin repository. The bob CLI should not become a process bridge for an operation on the current UI layout. Add source fragments through `src/fragments.json`, maintain the repository's fragment-size rule, generate `main.js`, and use its normal build/docs/test/deployment workflow. No CLI grammar, vault-note schema, or cross-repository capture contract change is required by this design.

**Alternatives are useful, but none fully satisfies the request.**

| Approach | Benefit | Reason not to choose it as the complete solution |
| --- | --- | --- |
| Native commands plus vimrc mappings | Smallest configuration change; useful for a prototype | Does not itself deliver the consequence hint, controlled merging, or verified state-preserving moves. Native command IDs and behavior still need runtime inspection. |
| Install Tab Shifter | Already addresses cross-group tab movement | The inspected implementation reopens files, assumes iteration order, and has the limitations above. |
| Install Pane Relief | Broader history, tab ordering, maximizing, and window tools | Larger behavior/default-hotkey footprint; its inspected tab placement code works within the current parent, not this exact join/create/collapse contract. |
| New standalone Bob window plugin | Independent lifecycle and settings | Duplicates navigation, focus, Vim integration, and card styling unless there is a broader future workspace product. |
| Extend Bob Navigation Hotkeys with isolated modules | Fits existing ownership and permits one exact behavior contract | Requires maintaining a small internal-API adapter and real-app regression coverage. Recommended. |

Pane Relief remains useful comparative evidence: its README explicitly warns about its many preconfigured shortcuts, and its code demonstrates why group-scoped tab reordering differs from spatial group movement. It is not a drop-in match for the requested interaction. [Pane Relief README](https://github.com/pjeby/pane-relief/blob/646034ad2af6256fe8764e51668b588359185702/README.md), [Placement implementation](https://github.com/pjeby/pane-relief/blob/646034ad2af6256fe8764e51668b588359185702/src/pane-relief.ts#L184).

I would defer `q/c` close commands, `o` close-others, swaps, group-wide moves, `J/K` layout moves, numeric counts, and resize keys. They introduce separate scope and reversibility questions. If resizing later proves valuable, `=` for equal widths is a better first addition than a collection of incremental resize bindings, but it should be an explicit action rather than a side effect of moving.

**Validation should focus on contracts that mocks cannot prove.**

| Area | Required evidence before release |
| --- | --- |
| Spatial behavior | One group, screenshot-like two groups, three groups, uneven widths, nested/T-shaped layouts; no wrapping for `h/l/H/L`; deterministic selected destination. |
| Identity and content | Same leaf/view/editor before and after move; undo/redo round trip; unsaved editing, selection, folds, scroll, pin state, two views of the same note, navigation history. |
| Create/collapse | Extract a tab in both directions; merge the last tab in both directions; no orphan placeholders or accidental close; no-op for lone-tab extraction. |
| Input | Vim normal/insert/visual, pending operators/counts, Vim disabled, Reading view, actual text fields, modals, composition, Caps Lock, held Control, repeat keys, invalid suffix, Escape, outside click, blur. |
| Windows and view types | Sidebars containing Markdown, pop-outs, hidden/stacked tabs, PDF, Canvas, empty tabs, unsupported plugin views; never cross documents accidentally. |
| Races and lifecycle | Target closed while hint is open; rapid invocations; drag or workspace switch during pending state; reload/unload/re-enable; no duplicate handlers or stale hint. |
| Persistence | Save and reload the scratch workspace; verify layout, selected tab, pins, and tab order. |
| Appearance/accessibility | Light/dark themes, zoom and narrow groups, high contrast, reduced motion, announced status, clear disabled reasons; screenshots of create/join/collapse hint states. |
| OS-specific behavior | Real macOS Control versus Command; Windows/Linux close-tab conflict; existing configured shortcuts remain reachable outside the claimed context. |

The repository already has isolated real-Obsidian UI harnesses. Its startup smoke script explicitly creates a scratch vault/profile and does not open the live vault; the Copy card harness is another concrete model for UI assertions. Extend that infrastructure rather than experimenting on Bryan's active workspace. Unit-test the planner and prefix state machine, then use actual key events in the app to verify dispatch and identity. The normal repository build, unit, inventory, and docs checks remain necessary for implementation. [Startup smoke harness](https://github.com/bobs-org/bob-plugins/blob/63ff1654a8ffc52c6c1419479a7e3bb17d08f012/scripts/obsidian-startup-smoke.cjs), [Copy card UI harness](https://github.com/bobs-org/bob-plugins/blob/63ff1654a8ffc52c6c1419479a7e3bb17d08f012/scripts/obsidian-copy-card-e2e.cjs).

**Evidence limits and delivery order matter.** This investigation inspected the supplied screenshot, Bob plugin source at `63ff1654a8ffc52c6c1419479a7e3bb17d08f012`, official API declarations, unofficial declarations pinned to public 1.14.4, the upstream Vimrc Support source, Tab Shifter, Pane Relief, and primary product/Vim documentation. Repository files were read from audited SASE checkouts. No production plugin, live vault configuration, or workspace layout was changed. No runtime relocation experiment or new test suite was executed. The declaration package version is not evidence of Bryan's installed Obsidian version.

The remaining implementation questions are concrete: which native relocation primitive preserves editor identity on the supported builds; whether it automatically collapses the last-tab source; how it handles stacked groups; and which bindings already claim the prefix in Bryan's deployed configuration. Resolve those first. Then build the shared planner and palette commands, add the prefix and consequence hint, and finish with the real-app/platform acceptance matrix. If lossless relocation cannot be established, ship only the independently verified focus/duplicate subset as explicitly incomplete functionality, or keep the feature unshipped; do not present a lossy move as satisfying the requested contract.

**Recommended solution:** proceed with the feature as a narrowly scoped extension of `bob-navigation-hotkeys`: directional `h/l`, adjacent-tab transfer with `H/L`, `w` for the other/next split, and `v` for deliberate duplication. Make the hint immediate, compact, theme-native, and precise about create/join/collapse consequences. The decisive release condition is that moving a tab preserves the actual tab and its state. That yields the requested intuitive interaction and attractive presentation without sacrificing trust in the editor.
